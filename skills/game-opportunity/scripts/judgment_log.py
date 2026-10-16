#!/usr/bin/env python3
"""Optional offline human-AI judgment log; never conveys game-exp authority.

All judgments, exposure claims and timestamps are operator-reported. The
adjacent SHA-256 chain detects accidental modifications but cannot prove
real-world timing, independence, or correctness of an outcome.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys

STAGES = ("HUMAN", "AI", "COMPARE", "OUTCOME")
BASELINES = ("pre_ai_reported", "post_ai", "unknown", "unavailable")
OUTCOMES = ("observed", "inconclusive", "not_run")
CASE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,40}$")
MAX_RECORD_BYTES = 256 * 1024
DEFAULT_PRIVATE_DIR = Path.home() / ".game-opportunity" / "private-evidence"


def clean(value: str | None, label: str, required: bool = False) -> str:
    value = (value or "").strip()
    if len(value) > 3000 or (required and not value):
        raise ValueError(f"{label}: empty required value or over 3000 characters")
    return value


def card_id(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise ValueError("card must be an existing, non-symlink Markdown file")
    location = Path(__file__).with_name("opportunity_card.py")
    spec = importlib.util.spec_from_file_location("opportunity_card", location)
    if spec is None or spec.loader is None:
        raise ValueError("card parser unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _, ident, _ = module.parse_card(path, require_complete=False)
    return ident


def encode(row: dict) -> bytes:
    return (json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def read(path: Path) -> tuple[list[dict], bytes]:
    if path.is_symlink() or not path.is_file():
        raise ValueError("judgment record missing or symlinked")
    raw = path.read_bytes()
    if not raw or len(raw) > MAX_RECORD_BYTES:
        raise ValueError("missing or oversized record")
    lines = raw.splitlines(keepends=True)
    events, previous = [], b""
    for index, line in enumerate(lines, 1):
        if not line.endswith(b"\n"):
            raise ValueError("incomplete record line")
        try:
            row = json.loads(line)
        except (ValueError, UnicodeError) as exc:
            raise ValueError("invalid JSON record") from exc
        if not isinstance(row, dict) or encode(row) != line:
            raise ValueError("noncanonical record")
        expected_hash = hashlib.sha256(previous).hexdigest() if previous else None
        if (row.get("schema_version") != 1 or index > len(STAGES)
            or row.get("stage") != STAGES[index-1]
            or row.get("sequence") != index or row.get("previous_sha256") != expected_hash):
            raise ValueError("invalid stage order or local hash chain")
        if index > 1 and (row.get("opportunity_id") != events[0]["opportunity_id"]
                          or row.get("case_id") != events[0]["case_id"]):
            raise ValueError("record identity changed")
        if not isinstance(row.get("details"), dict):
            raise ValueError("record details missing")
        events.append(row)
        previous = line
    return events, previous


def event(stage: str, ident: str, case: str, sequence: int,
          previous: bytes, details: dict) -> bytes:
    return encode({
        "schema_version": 1,
        "stage": stage,
        "sequence": sequence,
        "opportunity_id": ident,
        "case_id": case,
        "previous_sha256": hashlib.sha256(previous).hexdigest() if previous else None,
        "recorded_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "provenance": "OPERATOR_REPORTED_NOT_INDEPENDENTLY_ATTESTED",
        "details": details,
    })


def start(card: Path, case: str, directory: Path, baseline: str,
          human_prediction: str = "", human_next_action: str = "") -> Path:
    ident = card_id(card)
    if not CASE_ID.fullmatch(case):
        raise ValueError("invalid case ID")
    if baseline not in BASELINES:
        raise ValueError("invalid baseline status")
    prediction = clean(human_prediction, "human_prediction")
    action = clean(human_next_action, "human_next_action")
    if baseline == "unavailable":
        if prediction or action:
            raise ValueError("unavailable baseline cannot contain invented human judgment")
    elif not prediction or not action:
        raise ValueError("human prediction and original next action required")
    if directory.is_symlink():
        raise ValueError("symlink output directory forbidden")
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = directory / f"{ident}--{case}.judgment.jsonl"
    row = event("HUMAN", ident, case, 1, b"", {
        "baseline_type": baseline,
        "human_prediction": prediction,
        "human_next_action": action,
    })
    # Exclusive creation with private file permissions; never overwrite a prior view.
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "wb") as writer:
        writer.write(row)
    return path


def append(path: Path, stage: str, details: dict) -> None:
    events, previous = read(path)
    if len(events) >= len(STAGES) or stage != STAGES[len(events)]:
        raise ValueError("cannot skip, replace, or repeat judgment stages")
    if stage == "COMPARE" and events[0]["details"].get("baseline_type") == "unavailable":
        if details["materiality"] == "material":
            raise ValueError("no recorded human view to support material human-AI disagreement")
    row = event(stage, events[0]["opportunity_id"], events[0]["case_id"],
                len(events)+1, previous, details)
    if path.stat().st_size + len(row) > MAX_RECORD_BYTES:
        raise ValueError("record exceeds size limit")
    # Single local writer; NOT a locked, tamper-proof or externally timestamped log.
    with path.open("ab") as writer:
        writer.write(row)


def summary(path: Path) -> dict:
    events, _ = read(path)
    return {
        "opportunity_id": events[0]["opportunity_id"],
        "case_id": events[0]["case_id"],
        "stages": [x["stage"] for x in events],
        "baseline_type": events[0]["details"].get("baseline_type"),
        "baseline_independently_verified": False,
        "AI_blind_to_human": False,
        "materiality": events[2]["details"]["materiality"] if len(events) >= 3 else "not_assessed",
        "outcome": events[3]["details"]["status"] if len(events) == 4 else "NOT_RUN",
        "next_stage": STAGES[len(events)] if len(events) < 4 else None,
        "local_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "player_evidence_verified": False,
        "game_exp_authority": False,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    s = sub.add_parser("start")
    s.add_argument("--card", required=True, type=Path)
    s.add_argument("--case-id", required=True)
    s.add_argument("--directory", type=Path, default=DEFAULT_PRIVATE_DIR)
    s.add_argument("--baseline-type", choices=BASELINES, required=True)
    s.add_argument("--human-prediction", default="")
    s.add_argument("--human-next-action", default="")
    a = sub.add_parser("ai")
    a.add_argument("--file", required=True, type=Path)
    a.add_argument("--prediction", required=True)
    a.add_argument("--next-action", required=True)
    a.add_argument("--strongest-alternative", required=True)
    c = sub.add_parser("compare")
    c.add_argument("--file", required=True, type=Path)
    c.add_argument("--materiality", choices=("material", "not_material", "unknown"), required=True)
    c.add_argument("--why", required=True)
    c.add_argument("--discriminating-test", default="")
    c.add_argument("--cost-ceiling", default="")
    o = sub.add_parser("outcome")
    o.add_argument("--file", required=True, type=Path)
    o.add_argument("--status", choices=OUTCOMES, required=True)
    o.add_argument("--observation", default="")
    o.add_argument("--evidence-reference", default="")
    o.add_argument("--human-updated", default="")
    o.add_argument("--ai-updated", default="")
    o.add_argument("--next-decision", default="")
    o.add_argument("--actual-cost", default="")
    q = sub.add_parser("show")
    q.add_argument("--file", required=True, type=Path)
    args = p.parse_args(argv)
    try:
        if args.command == "start":
            print(start(args.card, args.case_id, args.directory, args.baseline_type,
                        args.human_prediction, args.human_next_action))
        elif args.command == "ai":
            append(args.file, "AI", {
                "prediction": clean(args.prediction, "prediction", True),
                "next_action": clean(args.next_action, "next_action", True),
                "strongest_alternative": clean(args.strongest_alternative, "strongest_alternative", True),
                "AI_blind_to_human": False,
            })
            print("AI appended: participant-reported, not blind")
        elif args.command == "compare":
            if args.materiality == "material" and not (args.discriminating_test.strip() and args.cost_ceiling.strip()):
                raise ValueError("material disagreement requires one proposed test and cost ceiling; use unknown if infeasible")
            append(args.file, "COMPARE", {
                "materiality": args.materiality, "why": clean(args.why, "why", True),
                "discriminating_test": clean(args.discriminating_test, "discriminating_test"),
                "cost_ceiling": clean(args.cost_ceiling, "cost_ceiling"),
                "approved_to_execute": False,
            })
            print("Comparison appended: does not authorize playtests or spending")
        elif args.command == "outcome":
            obs = clean(args.observation, "observation")
            source = clean(args.evidence_reference, "evidence_reference")
            if args.status == "observed" and not (obs and source):
                raise ValueError("observed outcome requires observation and evidence reference")
            if args.status == "not_run" and (obs or source):
                raise ValueError("not_run cannot carry observed evidence")
            append(args.file, "OUTCOME", {
                "status": args.status, "observation": obs, "evidence_reference": source,
                "human_updated": clean(args.human_updated, "human_updated"),
                "ai_updated": clean(args.ai_updated, "ai_updated"),
                "next_decision": clean(args.next_decision, "next_decision"),
                "actual_cost": clean(args.actual_cost, "actual_cost"),
                "game_exp_review_authority": False,
            })
            print("Outcome appended: self-reported, not a product-success finding")
        elif args.command == "show":
            print(json.dumps(summary(args.file), indent=2, ensure_ascii=False))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
