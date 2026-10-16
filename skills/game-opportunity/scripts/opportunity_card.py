#!/usr/bin/env python3
"""Offline helper for ordinary Markdown opportunity cards; no network or Git writes."""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

LABELS = {
    "uncertainty": "\u5173\u952e\u4e0d\u786e\u5b9a\u6027",
    "validation": "\u6700\u5c0f\u9a8c\u8bc1",
    "decision": "\u51b3\u7b56\u6761\u4ef6",
    "context": "\u53ef\u9009\u4e0a\u4e0b\u6587",
    "results": "\u9a8c\u8bc1\u7ed3\u679c",
    "observed": "\u6d4b\u8bd5\u89c2\u5bdf",
    "source": "\u8bc1\u636e\u6765\u6e90",
    "interpretation": "\u89e3\u91ca\u4e0e\u5c40\u9650",
}
CARD_ID = re.compile(r"^OPP-\d{8}-[a-z0-9]+(?:-[a-z0-9]+)*$")
RESULT_ID = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,80}$")
PLACEHOLDER = "TODO"
REQUIRED = [LABELS[k] for k in ("uncertainty", "validation", "decision", "context", "results")]


def card_text(card_id: str, title: str, route: str) -> str:
    if not CARD_ID.fullmatch(card_id):
        raise ValueError("Invalid opportunity ID; use OPP-YYYYMMDD-short-slug")
    if route not in {"demand_driven", "creative_driven"}:
        raise ValueError("Invalid route")
    if not title.strip() or "\n" in title or "\r" in title:
        raise ValueError("Title must be a nonempty single line")
    return (
        f"---\nopportunity_id: {card_id}\nroute: {route}\n---\n\n# {title.strip()}\n\n"
        f"## {LABELS['uncertainty']}\nTODO: Specific claim to falsify and target players.\n\n"
        f"## {LABELS['validation']}\nTODO: Cheapest ethical test, observation and denominator.\n\n"
        f"## {LABELS['decision']}\nTODO: Continue / adjust / stop conditions.\n\n"
        f"## {LABELS['context']}\nOptional: actual sources, dates, alternatives, acquisition path; "
        f"signal_type (non-exclusive, optional); evidence_dependency (origin/shared cohorts/UNKNOWN, optional); "
        f"recheck_trigger (event/question, optional; never auto-expiry).\n\n"
        f"## {LABELS['results']}\n<!-- Append dated results here; never fabricate a test. -->\n"
    )


def parse_card(path: Path, require_complete: bool = True) -> tuple[str, str, str]:
    contents = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\n(?P<fm>.*?)\n---\n", contents, re.S)
    if match is None:
        raise ValueError("Missing card YAML frontmatter")
    fm = {}
    for line in match.group("fm").splitlines():
        if ":" not in line:
            raise ValueError("Invalid frontmatter field")
        k, value = line.split(":", 1)
        if k in fm:
            raise ValueError("Duplicate frontmatter key")
        fm[k] = value.strip()
    card_id = fm.get("opportunity_id", "")
    route = fm.get("route", "")
    if not CARD_ID.fullmatch(card_id):
        raise ValueError("Invalid opportunity ID")
    if path.stem != card_id:
        raise ValueError("File name must equal opportunity_id")
    if route not in {"demand_driven", "creative_driven"}:
        raise ValueError("Invalid route")
    if not re.search(r"^# .+", contents, flags=re.M):
        raise ValueError("Missing opportunity title")
    positions = []
    for heading in REQUIRED:
        markers = list(re.finditer(r"^## " + re.escape(heading) + r"\s*$", contents, re.M))
        if len(markers) != 1:
            raise ValueError(f"Missing or duplicated heading: {heading}")
        positions.append(markers[0].start())
    if positions != sorted(positions):
        raise ValueError("Headings out of order")
    later_heading = contents[positions[-1]:].splitlines()[1:]
    if any(row.startswith("## ") for row in later_heading):
        raise ValueError("Validation results must be last section")
    if require_complete:
        for i in range(3):
            segment = contents[positions[i]:positions[i + 1]]
            if PLACEHOLDER in segment or len(segment.splitlines()) < 2 or not any(row.strip() for row in segment.splitlines()[1:]):
                raise ValueError(f"Mandatory decision section incomplete: {REQUIRED[i]}")
    return contents, card_id, route


def append_result(path: Path, result_id: str, observation: str, evidence: str, interpretation: str) -> None:
    if not RESULT_ID.fullmatch(result_id):
        raise ValueError("Invalid result id")
    if not observation.strip() or not evidence.strip():
        raise ValueError("Observation and evidence reference are required")
    if any("\n" in value or "\r" in value for value in (observation, evidence, interpretation)):
        raise ValueError("Result fields must each be one line")
    contents, _, _ = parse_card(path)
    header = f"### Result [{result_id}]"
    if header in contents:
        raise ValueError("Duplicate result id")
    timestamp = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    entry = (
        f"\n{header} ({timestamp})\n\n"
        f"- {LABELS['observed']}: {observation.strip()}\n"
        f"- {LABELS['source']}: {evidence.strip()}\n"
        f"- {LABELS['interpretation']}: {interpretation.strip() or 'Not yet interpreted'}\n"
    )
    # Append only: do not mutate prior hypotheses or result entries.
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(entry)


def search_cards(root: Path, keyword: str) -> list[Path]:
    if not root.is_dir():
        raise ValueError("No opportunity directory")
    key = keyword.casefold()
    return sorted(p for p in root.glob("OPP-*.md") if key in p.read_text(encoding="utf-8").casefold())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    new = sub.add_parser("new")
    new.add_argument("--id", required=True)
    new.add_argument("--title", required=True)
    new.add_argument("--route", choices=("demand_driven", "creative_driven"), default="demand_driven")
    new.add_argument("--directory", type=Path, default=Path("opportunities"))
    check = sub.add_parser("validate")
    check.add_argument("path", type=Path)
    add = sub.add_parser("append-result")
    add.add_argument("path", type=Path)
    add.add_argument("--result-id", required=True)
    add.add_argument("--observation", required=True)
    add.add_argument("--evidence", required=True)
    add.add_argument("--interpretation", default="")
    search = sub.add_parser("search")
    search.add_argument("keyword")
    search.add_argument("--directory", type=Path, default=Path("opportunities"))
    args = parser.parse_args(argv)
    try:
        if args.command == "new":
            path = args.directory / f"{args.id}.md"
            content = card_text(args.id, args.title, args.route)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(content)
            print(path)
        elif args.command == "validate":
            _, card_id, route = parse_card(args.path)
            print(f"VALID {card_id} {route}")
        elif args.command == "append-result":
            append_result(args.path, args.result_id, args.observation, args.evidence, args.interpretation)
            print("APPENDED; local file only, not remotely persisted")
        elif args.command == "search":
            for path in search_cards(args.directory, args.keyword):
                print(path)
        return 0
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
