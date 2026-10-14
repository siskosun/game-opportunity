#!/usr/bin/env python3
"""Offline, bounded CSV/JSON review-theme summary. Never uploads or exports raw comments."""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

MAX_INPUT_BYTES = 12 * 1024 * 1024
MAX_RECORDS = 20000
ALIASES = {
    "text": ("review", "content", "comment", "text", "body", "评论内容", "评论", "评价内容", "反馈"),
    "id": ("recommendationid", "review_id", "comment_id", "id", "评论id", "评论编号"),
    "polarity": ("voted_up", "recommended", "是否推荐", "评价倾向"),
    "language": ("language", "lang", "语言"),
}
# Mentions, not verified pain points or sentiment. Negated words may still be matched.
THEMES = {
    "performance": ("卡顿", "闪退", "掉帧", "延迟", "崩溃", "加载", "优化", "lag", "crash", "fps"),
    "onboarding_and_controls": ("上手", "操作", "教程", "指引", "难懂", "手感", "按键", "引导", "control", "tutorial"),
    "replay_and_content": ("内容少", "重复", "无聊", "关卡", "更新", "后期", "通关", "重玩", "replay", "boring"),
    "fairness_and_rules": ("公平", "平衡", "太强", "太弱", "随机", "匹配", "规则", "balance", "unfair"),
    "monetization": ("价格", "氪金", "付费", "内购", "广告", "退款", "paywall", "microtransaction"),
    "social_and_multiplayer": ("好友", "组队", "联机", "合作", "社交", "邀请", "多人", "房间", "co-op", "multiplayer"),
    "presentation": ("美术", "画面", "音乐", "音效", "视觉", "剧情", "ui", "graphics", "sound"),
}


def field(record: dict, group: str) -> object:
    lower = {str(k).strip().lower(): v for k, v in record.items() if k is not None}
    for key in ALIASES[group]:
        if key.lower() in lower:
            return lower[key.lower()]
    return None


def public_url(value: str) -> str | None:
    if not value:
        return None
    p = urlsplit(value.strip())
    if p.scheme not in {"http", "https"} or not p.hostname or p.username or p.password:
        raise ValueError("Source URL must be a public http(s) URL without credentials")
    return urlunsplit((p.scheme, p.netloc, p.path, "", ""))


def as_polarity(value: object) -> str | None:
    if type(value) is bool:
        return "positive" if value else "negative"
    if isinstance(value, str):
        token = value.strip().lower()
        if token in ("yes", "positive", "recommended", "true", "是", "好评", "推荐"):
            return "positive"
        if token in ("no", "negative", "not_recommended", "false", "否", "差评", "不推荐"):
            return "negative"
    return None


def theme_hits(text: str) -> list[str]:
    t = text.casefold()
    return [name for name, words in THEMES.items() if any(re.search(r"(?<![a-z])" + re.escape(w) + r"(?![a-z])", t) for w in words)]


def summarize_records(records: list[dict], *, platform: str, source_url: str | None = None,
                      input_sha256: str | None = None, sampling_notes: str = "Unspecified; not representative") -> dict:
    if not isinstance(records, list) or not records:
        raise ValueError("No review records to summarize")
    if len(records) > MAX_RECORDS:
        raise ValueError(f"Too many records (max {MAX_RECORDS})")
    if not platform or len(platform) > 100:
        raise ValueError("Specify a short source platform")
    seen: set[str] = set()
    themes = {key: 0 for key in THEMES}
    polarity = {"positive": 0, "negative": 0, "unknown": 0}
    languages: dict[str, int] = {}
    duplicates = missing_text = valid = 0
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Review records must be objects")
        raw = field(record, "text")
        if not isinstance(raw, str) or not raw.strip():
            missing_text += 1
            continue
        normalized = raw.strip()
        ident = field(record, "id")
        key = "id:" + str(ident).strip() if ident is not None and str(ident).strip() else "text:" + normalized.casefold()
        hashed = hashlib.sha256(key.encode("utf-8")).hexdigest()
        if hashed in seen:
            duplicates += 1
            continue
        seen.add(hashed)
        valid += 1
        for name in theme_hits(normalized):
            themes[name] += 1
        label = as_polarity(field(record, "polarity")) or "unknown"
        polarity[label] += 1
        lang = field(record, "language")
        language = str(lang).strip().lower()[:32] if isinstance(lang, str) and lang.strip() else "unknown"
        languages[language] = languages.get(language, 0) + 1
    if valid == 0:
        raise ValueError("No non-empty unique review text")
    return {
        "schema_version": 1,
        "kind": "exploratory_review_theme_counts",
        "source": {"platform": platform.strip(), "url_without_query": public_url(source_url or ""),
                   "input_sha256": input_sha256, "sampling_notes": sampling_notes},
        "processed_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "denominator": {"input_records": len(records), "usable_unique_reviews": valid,
                        "duplicates_excluded": duplicates, "no_text_excluded": missing_text},
        "explicit_review_polarity": polarity,
        "languages": dict(sorted(languages.items())),
        "theme_mentions": dict(sorted(themes.items())),
        "interpretation_limits": [
            "Theme matches are exploratory keyword mentions, not proven unmet needs or sentiment.",
            "A negated term can match; manually inspect authorized raw data before making claims.",
            "This selected sample is not proof of market size, player choice, retention, revenue or causality.",
            "No raw review text, review IDs, author IDs or contact details are exported.",
        ],
    }


def load_records(path: Path) -> tuple[list[dict], str]:
    if not path.is_file():
        raise ValueError("Input file not found")
    size = path.stat().st_size
    if size == 0 or size > MAX_INPUT_BYTES:
        raise ValueError(f"Input file must be nonempty and <= {MAX_INPUT_BYTES} bytes")
    blob = path.read_bytes()
    digest = hashlib.sha256(blob).hexdigest()
    if path.suffix.lower() == ".csv":
        import io
        reader = csv.DictReader(io.StringIO(blob.decode("utf-8-sig")))
        if not reader.fieldnames:
            raise ValueError("CSV must have a header row")
        records = list(reader)
    elif path.suffix.lower() in {".json", ".jsonl"}:
        text = blob.decode("utf-8-sig")
        if path.suffix.lower() == ".jsonl":
            records = [json.loads(line) for line in text.splitlines() if line.strip()]
        else:
            data = json.loads(text)
            if isinstance(data, list):
                records = data
            elif isinstance(data, dict) and isinstance(data.get("reviews"), list):
                records = data["reviews"]
            elif isinstance(data, dict) and isinstance(data.get("records"), list):
                records = data["records"]
            else:
                raise ValueError("JSON must be a list or contain a 'reviews'/'records' list")
    else:
        raise ValueError("Input must be .csv, .json or .jsonl")
    if len(records) > MAX_RECORDS:
        raise ValueError(f"Too many records (max {MAX_RECORDS})")
    return records, digest


def write_summary(output: Path, summary: dict) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    # Exclusive create; prevents accidental overwrites of prior evidence.
    descriptor = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as file:
        file.write(payload)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--platform", required=True)
    p.add_argument("--source-url", default="")
    p.add_argument("--sampling-notes", default="Unspecified; not representative")
    p.add_argument("--output", type=Path)
    args = p.parse_args(argv)
    try:
        records, digest = load_records(args.input)
        result = summarize_records(records, platform=args.platform, source_url=args.source_url,
                                   input_sha256=digest, sampling_notes=args.sampling_notes)
        out = args.output or Path("local-evidence") / f"{digest[:12]}.summary.json"
        write_summary(out, result)
        print(f"LOCAL_ONLY {out} usable_unique_reviews={result['denominator']['usable_unique_reviews']}")
        return 0
    except (ValueError, OSError, UnicodeError, json.JSONDecodeError, csv.Error) as exc:
        print(f"EVIDENCE_IMPORT_FAILED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
