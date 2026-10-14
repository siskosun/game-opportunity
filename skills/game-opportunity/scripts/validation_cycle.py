#!/usr/bin/env python3
"""Local, privacy-first player-behavior validation: preregister and assess aggregates.

This is ordinary research, not a game-exp Manifest, Ledger, Review, or automatic
investment decision. Nothing in this module performs network or Git actions.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import pathlib
import re
import sys
from decimal import Decimal, InvalidOperation

from opportunity_card import parse_card

MAX_BYTES = 2 * 1024 * 1024
PLAN_ID = re.compile(r"^VAL-\d{8}-[a-z0-9]+(?:-[a-z0-9]+)*$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
# Numerator and denominator are *unique eligible players* in the same window.
# Do not use impression counts or repeated sessions in these ratios.
METRICS = {
    "qualified_interest": "attention",
    "voluntary_start": "choice",
    "actual_purchase": "choice",
    "first_session_completion": "experience",
    "voluntary_return": "experience",
    "voluntary_invitation": "experience",
    "finite_game_completion": "experience",
}
SAMPLING = {"self_selected", "convenience", "platform_traffic", "first_party_eligible", "randomized", "other"}
SOURCE_KINDS = {"playtest", "platform_dashboard", "manual_aggregate", "other"}
FIELDS = (
    "plan_id", "metric", "numerator", "denominator", "population", "segment",
    "window_start", "window_end", "unit", "sampling_method", "source_kind",
)
ALIASES = {
    "plan_id": ("plan_id", "验证编号"),
    "metric": ("metric", "指标"),
    "numerator": ("numerator", "分子", "达成人数"),
    "denominator": ("denominator", "分母", "有效样本人数"),
    "population": ("population", "目标群体"),
    "segment": ("segment", "人群分组"),
    "window_start": ("window_start", "开始日期"),
    "window_end": ("window_end", "结束日期"),
    "unit": ("unit", "统计单位"),
    "sampling_method": ("sampling_method", "采样方式"),
    "source_kind": ("source_kind", "来源类型"),
}
REVERSE = {alias: key for key, aliases in ALIASES.items() for alias in aliases}


class ValidationError(ValueError):
    pass


def _digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _single_line(value: str, name: str, limit: int = 400) -> str:
    if not isinstance(value, str) or not value.strip() or any(ch in value for ch in "\n\r\x00") or len(value) > limit:
        raise ValidationError(f"{name} must be a nonempty single line, <= {limit} characters")
    return value.strip()


def _date(value: str) -> str:
    try:
        d = dt.date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError("Dates must be ISO YYYY-MM-DD") from exc
    if d.isoformat() != value:
        raise ValidationError("Dates must be canonical ISO YYYY-MM-DD")
    return value


def _rate(value: str) -> Decimal:
    try:
        rate = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValidationError("Threshold must be a decimal fraction, e.g. 0.2") from exc
    if not rate.is_finite() or not 0 <= rate <= 1:
        raise ValidationError("Threshold must be between 0 and 1")
    return rate


def _positive_integer(value: object, name: str) -> int:
    if isinstance(value, bool):
        raise ValidationError(f"{name} must be a positive integer")
    if isinstance(value, int):
        n = value
    elif isinstance(value, str) and re.fullmatch(r"[0-9]+", value):
        n = int(value)
    else:
        raise ValidationError(f"{name} must be a nonnegative integer, not a fraction")
    if n < 0 or n > 1_000_000_000:
        raise ValidationError(f"{name} out of bounds")
    return n


def _save_new(path: pathlib.Path, data: dict) -> None:
    if path.is_symlink() or path.exists():
        raise ValidationError("Refusing to overwrite an existing or symlinked record")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def make_plan(*, card: pathlib.Path, plan_id: str, metric: str,
              numerator_definition: str, denominator_definition: str,
              population: str, segment: str, window_start: str, window_end: str,
              sampling_method: str, sampling_notes: str, min_denominator: int,
              continue_at_least: str, stop_at_most: str, threshold_reason: str) -> dict:
    _, card_id, _ = parse_card(card)
    if not PLAN_ID.fullmatch(plan_id):
        raise ValidationError("Use plan id VAL-YYYYMMDD-short-slug")
    if metric not in METRICS:
        raise ValidationError("Unsupported metric; see --help for options")
    if sampling_method not in SAMPLING:
        raise ValidationError("Unsupported sampling method")
    low, high = _rate(stop_at_most), _rate(continue_at_least)
    if low >= high:
        raise ValidationError("stop_at_most must be strictly below continue_at_least")
    min_n = _positive_integer(min_denominator, "min_denominator")
    if min_n < 1:
        raise ValidationError("min_denominator must be at least 1")
    start, end = _date(window_start), _date(window_end)
    if start > end:
        raise ValidationError("window_start cannot be after window_end")
    return {
        "schema_version": 1,
        "kind": "game_opportunity_validation_plan",
        "authority": "ORDINARY_RESEARCH_NOT_GAME_EXP_MANIFEST",
        "plan_id": plan_id,
        "opportunity_id": card_id,
        "card_sha256_when_planned": _digest(card),
        "created_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "metric": {
            "id": metric, "phase": METRICS[metric], "unit": "unique_players",
            "numerator_definition": _single_line(numerator_definition, "numerator definition"),
            "denominator_definition": _single_line(denominator_definition, "denominator definition"),
        },
        "population": _single_line(population, "population", 120),
        "segment": _single_line(segment, "segment", 120),
        "window": {"start": start, "end": end},
        "sampling": {
            "method": sampling_method,
            "limitations": _single_line(sampling_notes, "sampling limitations"),
        },
        "criteria": {
            "min_denominator": min_n,
            "continue_at_least": str(high),
            "stop_at_most": str(low),
            "reason": _single_line(threshold_reason, "threshold justification"),
        },
        "integrity": {
            "mode": "LOCAL_HASH_ONLY_NOT_INDEPENDENT_TIMESTAMP_PROOF",
            "reminder": "Preserve pre-test SHA via an independently trusted, authorized private commit or log.",
        },
    }


def _normalized_row(raw: dict) -> dict:
    if not isinstance(raw, dict):
        raise ValidationError("Aggregate observation must be a JSON object / CSV row")
    if any(key not in REVERSE for key in raw):
        raise ValidationError("Unexpected column; only aggregated fields are accepted, never PII or raw reviews")
    normalized = {}
    for key, val in raw.items():
        canonical = REVERSE[key]
        if canonical in normalized:
            raise ValidationError("Ambiguous duplicate Chinese/English column aliases")
        normalized[canonical] = val
    if set(normalized) != set(FIELDS):
        raise ValidationError("Missing aggregate fields: " + ", ".join(sorted(set(FIELDS) - set(normalized))))
    return normalized


def _load_observation(path: pathlib.Path) -> dict:
    if not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise ValidationError("Input missing or exceeds 2 MiB; supply one anonymized aggregate row")
    if path.suffix.lower() == ".csv":
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as stream:
                reader = csv.DictReader(stream)
                header = reader.fieldnames or []
                if len(set(header)) != len(header):
                    raise ValidationError("Duplicate CSV header; refusing ambiguous aggregate")
                rows = list(reader)
        except csv.Error as exc:
            raise ValidationError("Malformed CSV aggregate") from exc
    elif path.suffix.lower() == ".json":
        def _no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValidationError("Duplicate JSON object key; refusing ambiguous aggregate")
                result[key] = value
            return result
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=_no_duplicate_keys)
        except (ValueError, UnicodeError) as exc:
            if isinstance(exc, ValidationError):
                raise
            raise ValidationError("Invalid JSON aggregate") from exc
        rows = data if isinstance(data, list) else [data]
    else:
        raise ValidationError("Use UTF-8 CSV or JSON containing an aggregate row")
    if not isinstance(rows, list) or len(rows) != 1:
        raise ValidationError("Exactly one independently identified aggregate row is required; do not average multiple snapshots, sources or arms")
    return _normalized_row(rows[0])


def assess(plan_path: pathlib.Path, input_path: pathlib.Path, *, expected_plan_sha256: str = "") -> dict:
    if not plan_path.is_file() or plan_path.stat().st_size > MAX_BYTES:
        raise ValidationError("Plan missing or too large")
    try:
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise ValidationError("Invalid plan JSON") from exc
    if not isinstance(plan, dict) or plan.get("schema_version") != 1 or plan.get("kind") != "game_opportunity_validation_plan":
        raise ValidationError("Unsupported validation plan")
    sha = _digest(plan_path)
    if expected_plan_sha256 and (not SHA256.fullmatch(expected_plan_sha256) or expected_plan_sha256 != sha):
        raise ValidationError("PLAN_CHANGED: expected preregistration SHA does not match current bytes")
    row = _load_observation(input_path)
    requirements = {
        "plan_id": plan["plan_id"], "metric": plan["metric"]["id"],
        "population": plan["population"], "segment": plan["segment"],
        "window_start": plan["window"]["start"], "window_end": plan["window"]["end"],
        "unit": "unique_players", "sampling_method": plan["sampling"]["method"],
    }
    for field, value in requirements.items():
        if row[field] != value:
            raise ValidationError(f"INCOMPATIBLE_{field.upper()}: supplied aggregate does not match frozen plan; do not silently merge populations/windows/metric")
    if row["source_kind"] not in SOURCE_KINDS:
        raise ValidationError("Invalid source kind")
    n = _positive_integer(row["numerator"], "numerator")
    d = _positive_integer(row["denominator"], "denominator")
    if d == 0 or n > d:
        raise ValidationError("Require 0 <= unique numerator <= positive unique denominator")
    observed_rate = Decimal(n) / Decimal(d)
    if d < plan["criteria"]["min_denominator"]:
        signal = "INCONCLUSIVE_BELOW_PREDECLARED_MINIMUM"
    elif not expected_plan_sha256:
        signal = "DESCRIPTIVE_ONLY_NO_PRETEST_DIGEST"
    elif observed_rate >= _rate(plan["criteria"]["continue_at_least"]):
        signal = "MEETS_DECLARED_CONTINUE_SIGNAL_NOT_A_DECISION"
    elif observed_rate <= _rate(plan["criteria"]["stop_at_most"]):
        signal = "MEETS_DECLARED_STOP_SIGNAL_NOT_A_DECISION"
    else:
        signal = "INCONCLUSIVE_BETWEEN_PREDECLARED_BOUNDS"
    return {
        "schema_version": 1,
        "kind": "game_opportunity_behavior_assessment",
        "authority": "OPERATOR_REPORTED_AGGREGATE_NOT_TRUSTED_GAME_EXP_EVIDENCE",
        "plan_id": plan["plan_id"], "opportunity_id": plan["opportunity_id"],
        "metric": plan["metric"]["id"], "phase": plan["metric"]["phase"],
        "population": plan["population"], "segment": plan["segment"],
        "window": plan["window"], "sampling_method": plan["sampling"]["method"],
        "source_kind": row["source_kind"],
        "observed": {"numerator": n, "denominator": d, "unit": "unique_players",
                     "fraction": f"{n}/{d}", "rate": str(observed_rate.quantize(Decimal("0.0001")))},
        "declared_criteria": plan["criteria"],
        "signal": signal,
        "integrity": {"plan_sha256": sha, "input_sha256": _digest(input_path),
                      "pretest_digest_matches_current": bool(expected_plan_sha256),
                      "independent_pretest_timestamp_verified": False,
                      "remote_source_verified": False},
        "interpretation_limits": [
            "Counts are operator-reported aggregate data, not individually or independently validated.",
            "A SHA match proves byte identity, not that criteria were recorded before observing results.",
            "An observed proportion does not prove a representative population rate or causal uplift.",
            "These signals never grant game-exp Review PASS, PROMISING, SELECTED or REJECTED.",
            "Do not publish this summary without checking confidential population/segment labels.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="action", required=True)
    s = sub.add_parser("plan", help="Create a new local pre-test plan; never overwrite")
    s.add_argument("--card", type=pathlib.Path, required=True)
    s.add_argument("--plan-id", required=True)
    s.add_argument("--metric", choices=tuple(METRICS), required=True)
    s.add_argument("--numerator-definition", required=True)
    s.add_argument("--denominator-definition", required=True)
    s.add_argument("--population", required=True)
    s.add_argument("--segment", required=True)
    s.add_argument("--window-start", required=True)
    s.add_argument("--window-end", required=True)
    s.add_argument("--sampling-method", choices=tuple(sorted(SAMPLING)), required=True)
    s.add_argument("--sampling-notes", required=True)
    s.add_argument("--min-denominator", type=int, required=True)
    s.add_argument("--continue-at-least", required=True)
    s.add_argument("--stop-at-most", required=True)
    s.add_argument("--threshold-reason", required=True)
    s.add_argument("--output", type=pathlib.Path)
    a = sub.add_parser("assess", help="Assess exactly one aggregate against the pre-test plan")
    a.add_argument("--plan", type=pathlib.Path, required=True)
    a.add_argument("--input", type=pathlib.Path, required=True)
    a.add_argument("--expected-plan-sha256", default="")
    a.add_argument("--output", type=pathlib.Path)
    args = p.parse_args(argv)
    try:
        if args.action == "plan":
            payload = make_plan(card=args.card, plan_id=args.plan_id, metric=args.metric,
                                numerator_definition=args.numerator_definition,
                                denominator_definition=args.denominator_definition,
                                population=args.population, segment=args.segment,
                                window_start=args.window_start, window_end=args.window_end,
                                sampling_method=args.sampling_method, sampling_notes=args.sampling_notes,
                                min_denominator=args.min_denominator, continue_at_least=args.continue_at_least,
                                stop_at_most=args.stop_at_most, threshold_reason=args.threshold_reason)
            output = args.output or pathlib.Path("local-evidence") / f"{args.plan_id}.plan.json"
            _save_new(output, payload)
            print(json.dumps({"status": "LOCAL_ONLY_PLAN_CREATED", "path": str(output),
                              "sha256": _digest(output), "authority": payload["authority"]}, ensure_ascii=False))
        else:
            payload = assess(args.plan, args.input, expected_plan_sha256=args.expected_plan_sha256)
            output = args.output or pathlib.Path("local-evidence") / f"{payload['plan_id']}.{_digest(args.input)[:12]}.assessment.json"
            _save_new(output, payload)
            print(json.dumps({"status": "LOCAL_ONLY_ASSESSMENT", "path": str(output),
                              "signal": payload["signal"], "authority": payload["authority"]}, ensure_ascii=False))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print("VALIDATION_CYCLE_FAILED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
