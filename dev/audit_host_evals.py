#!/usr/bin/env python3
"""Audit manually collected cross-host routing evaluations; never execute a Skill."""
import argparse
import csv
import json
import sys
from pathlib import Path

REQUIRED = ("case_id", "host", "installed_skill_sha", "run_id", "run_time_utc",
            "actual_primary_route", "route_pass", "must_pass", "must_not_pass",
            "clarifying_questions", "status", "evidence_location", "notes")
HOSTS = {"cursor", "codex", "qoder", "chatgpt"}
STATES = {"PASS", "FAIL", "NOT_RUN", "BLOCKED"}


def audit(cases_path, results_path):
    cases = json.loads(Path(cases_path).read_text(encoding="utf-8"))
    indexed = {c["id"]: c for c in cases}
    if len(indexed) != len(cases):
        raise ValueError("duplicate case IDs in baseline")
    errors, counts, seen = [], {s: 0 for s in STATES}, set()
    with Path(results_path).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or set(REQUIRED) - set(reader.fieldnames):
            raise ValueError("missing required results columns")
        for line, row in enumerate(reader, start=2):
            prefix = "row %d" % line
            cid, host, run = ((row.get(k) or "").strip() for k in ("case_id", "host", "run_id"))
            if cid not in indexed:
                errors.append(f"{prefix}: unknown case_id {cid!r}")
                continue
            if host not in HOSTS:
                errors.append(f"{prefix}: unsupported host {host!r}")
            key = (cid, host, run)
            if key in seen or not run:
                errors.append(f"{prefix}: missing/duplicate run_id for case and host")
            seen.add(key)
            status = (row.get("status") or "").strip().upper()
            if status not in STATES:
                errors.append(f"{prefix}: invalid status {status!r}")
                continue
            counts[status] += 1
            if status != "PASS":
                continue
            case = indexed[cid]
            def tokens(name):
                return {t.strip() for t in (row.get(name) or "").split(";") if t.strip()}
            needed = set(case["must"])
            prohibited = set(case["must_not"])
            if (row.get("route_pass") or "").strip().lower() != "true":
                errors.append(f"{prefix}: PASS without verified route")
            if (row.get("actual_primary_route") or "").strip() != case["expected_skill"]:
                errors.append(f"{prefix}: PASS with wrong primary route")
            if tokens("must_pass") != needed:
                errors.append(f"{prefix}: PASS must_pass mismatch (exact rubric IDs required)")
            if tokens("must_not_pass") != prohibited:
                errors.append(f"{prefix}: PASS must_not_pass mismatch (exact rubric IDs required)")
            for name in ("installed_skill_sha", "run_time_utc", "evidence_location"):
                if not (row.get(name) or "").strip():
                    errors.append(f"{prefix}: PASS missing {name}")
            if (row.get("evidence_location") or "").lower().startswith(("example", "synthetic", "mock")):
                errors.append(f"{prefix}: PASS references illustrative evidence")
            try:
                q = int((row.get("clarifying_questions") or "").strip())
                if q < 0:
                    raise ValueError()
            except ValueError:
                errors.append(f"{prefix}: PASS invalid clarifying_questions")
    return {"rows": sum(counts.values()), "counts": counts,
            "errors": errors, "valid": not errors,
            "notice": "This audits the report format only; PASS remains a human claim, not independently verified gameplay or market evidence."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", default="evals/cases.json")
    parser.add_argument("--results", required=True)
    args = parser.parse_args()
    try:
        result = audit(args.cases, args.results)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(json.dumps({"valid": False, "errors": [str(exc)]}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
