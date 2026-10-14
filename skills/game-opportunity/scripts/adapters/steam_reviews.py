#!/usr/bin/env python3
"""Optional bounded public Steam review sample -> local aggregate. No raw-review export.

Request/cursor/de-dup/retry patterns adapted from Seafoodsz/SteamReviewFetch
`scripts/steam_reviews_fetcher_v2.py`, MIT, Copyright (c) 2025 Seafoodsz.
Full upstream permission notice: ../../THIRD_PARTY_NOTICES.md.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# This opt-in adapter runs directly as a script without requiring pip installation.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from import_evidence import summarize_records, write_summary  # noqa: E402

APP_ID = re.compile(r"^[0-9]{1,12}$")
URL = "https://store.steampowered.com/appreviews/{appid}"
MAX_RESPONSE_BYTES = 2 * 1024 * 1024


class DenyRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # Only the pinned public Steam host is permitted.


def get_json(appid: str, cursor: str, language: str, filter_type: str, per_page: int) -> dict:
    params = urllib.parse.urlencode({
        "json": "1", "filter": filter_type, "language": language,
        "review_type": "all", "purchase_type": "all",
        "num_per_page": per_page, "cursor": cursor,
    })
    req = urllib.request.Request(URL.format(appid=appid) + "?" + params,
                                 headers={"User-Agent": "game-opportunity/0.2 (+public review sampling)"})
    opener = urllib.request.build_opener(DenyRedirect())
    for attempt in range(3):
        try:
            with opener.open(req, timeout=20) as response:
                blob = response.read(MAX_RESPONSE_BYTES + 1)
            if len(blob) > MAX_RESPONSE_BYTES:
                raise ValueError("Oversized Steam response")
            result = json.loads(blob)
            if not isinstance(result, dict) or result.get("success") != 1:
                raise ValueError("Steam did not return a successful review payload")
            return result
        except urllib.error.HTTPError as exc:
            # Do not retry an authorization, throttling or access-denial response.
            if exc.code not in {500, 502, 503, 504} or attempt == 2:
                raise ValueError(f"Steam request failed with HTTP {exc.code}") from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt == 2:
                raise ValueError("Steam temporarily unreachable; no fallback bypass") from exc
        time.sleep(2 ** attempt)
    raise ValueError("Steam request failed")


def fetch_reviews(appid: str, *, language: str = "schinese", filter_type: str = "all",
                  max_pages: int = 2, max_reviews: int = 100, delay: float = 1.0,
                  request_page=get_json, sleep=time.sleep) -> tuple[list[dict], dict]:
    if not APP_ID.fullmatch(appid):
        raise ValueError("App ID must contain digits only")
    if language not in {"schinese", "tchinese", "english", "all"}:
        raise ValueError("Unsupported language")
    if filter_type not in {"all", "recent"}:
        raise ValueError("Unsupported review filter")
    if not 1 <= max_pages <= 5 or not 1 <= max_reviews <= 500 or not math.isfinite(delay) or not 1.0 <= delay <= 10.0:
        raise ValueError("Limits: 1-5 pages, 1-500 reviews, delay 1-10s")
    result = []
    seen: set[str] = set()
    cursor = "*"
    duplicates = 0
    pages = 0
    declared_total = None
    reason = "max_pages"
    for page in range(max_pages):
        if page:
            sleep(delay)
        data = request_page(appid, cursor, language, filter_type, min(100, max_reviews - len(result)))
        if not isinstance(data, dict) or data.get("success") != 1:
            raise ValueError("Steam response unsuccessful")
        pages += 1
        summary = data.get("query_summary")
        if page == 0 and isinstance(summary, dict) and isinstance(summary.get("total_reviews"), int):
            declared_total = summary["total_reviews"]
        reviews = data.get("reviews")
        if not isinstance(reviews, list):
            raise ValueError("Steam response missing reviews list")
        if not reviews:
            reason = "empty_page"
            break
        for r in reviews:
            if not isinstance(r, dict):
                continue
            text = r.get("review")
            if not isinstance(text, str) or not text.strip():
                continue
            review_id = r.get("recommendationid")
            ident = str(review_id).strip() if review_id is not None else ""
            dedup_key = "id:" + ident if ident else "text:" + text.strip().casefold()
            if dedup_key in seen:
                duplicates += 1
                continue
            seen.add(dedup_key)
            # Explicit data minimization: drop author, steamid, username, purchase data.
            result.append({"review": text, "recommendationid": ident or None,
                           "voted_up": r.get("voted_up"), "language": r.get("language", language)})
            if len(result) >= max_reviews:
                reason = "max_reviews"
                break
        if len(result) >= max_reviews:
            break
        next_cursor = data.get("cursor")
        if not isinstance(next_cursor, str) or not next_cursor or next_cursor == cursor:
            reason = "cursor_missing_or_repeated"
            break
        cursor = next_cursor
    return result, {"pages": pages, "duplicates_skipped": duplicates,
                    "source_total_for_filter": declared_total, "stopped_reason": reason,
                    "sampling": "Bounded, not representative; availability subject to Steam API limits"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--appid", required=True)
    parser.add_argument("--language", choices=("schinese", "tchinese", "english", "all"), default="schinese")
    parser.add_argument("--filter", choices=("all", "recent"), default="all")
    parser.add_argument("--max-pages", type=int, default=2)
    parser.add_argument("--max-reviews", type=int, default=100)
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--confirm-public-fetch", action="store_true", help="Explicitly authorize this bounded Steam fetch")
    args = parser.parse_args(argv)
    if not args.confirm_public_fetch:
        print("STEAM_FETCH_NOT_AUTHORIZED: pass --confirm-public-fetch after checking network use", file=sys.stderr)
        return 2
    try:
        records, meta = fetch_reviews(args.appid, language=args.language, filter_type=args.filter,
                                      max_pages=args.max_pages, max_reviews=args.max_reviews, delay=args.delay)
        if not records:
            raise ValueError("No usable Steam reviews were retrieved")
        summary = summarize_records(records, platform="Steam", source_url=URL.format(appid=args.appid),
                                    sampling_notes=meta["sampling"])
        summary["retrieval"] = {"appid": args.appid, "language": args.language,
                                "filter": args.filter, **meta}
        output = args.output or Path("local-evidence") / f"steam-{args.appid}-{args.language}.summary.json"
        write_summary(output, summary)
        print(f"LOCAL_ONLY {output} usable_unique_reviews={summary['denominator']['usable_unique_reviews']}")
        return 0
    except (ValueError, OSError, UnicodeError) as exc:
        print(f"STEAM_FETCH_FAILED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
