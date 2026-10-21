#!/usr/bin/env python3
"""Add transparent cost/time and final-defect summaries to upstream pilot.py output.

Requires a separately pinned copy of the MIT-licensed upstream pilot.py. Does
not rewrite its original denominators or infer any missing values as zero.
"""
from __future__ import annotations
import argparse
import hashlib
from collections import defaultdict
import importlib.util
import json
import math
from pathlib import Path

COHORTS = ("ai_proxy", "human_team")
CONDITIONS = ("A", "B")
SEVERITIES = {"critical", "major", "minor"}


def number(value, label: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ValueError(f"{label}: expected finite nonnegative number or null")
    return float(value)


def summary(values: list[float | None]) -> dict:
    observed = [v for v in values if v is not None]
    complete = len(observed) == len(values)
    return {"observed": len(observed), "missing": len(values)-len(observed), "total_observed": round(sum(observed), 6),
            "mean_if_complete": round(sum(observed)/len(values), 6) if complete and values else None}


def extend(records: dict, upstream_summary: dict) -> dict:
    if records.get("study_kind") not in {"synthetic", "real"}:
        raise ValueError("study_kind must explicitly be synthetic or real")
    if not upstream_summary.get("ok"):
        raise ValueError("upstream pilot summary is not valid")
    groups = {}
    for cohort in COHORTS:
        groups[cohort] = {}
        for condition in CONDITIONS:
            selected = [r for r in records.get("records", []) if r.get("cohort") == cohort and r.get("condition") == condition and r.get("execution_status") != "not_run"]
            manual, review, elapsed, total_cost = [], [], [], []
            currencies: set[str] = set()
            quality = {"reviewed": 0, "unknown": 0, "units_with_critical_defect": 0, "units_with_any_defect": 0, "units_with_new_defect": 0}
            for index, rec in enumerate(selected):
                tag = f"{cohort}.{condition}[{index}]"
                manual.append(number(rec.get("manual_work_minutes"), tag+".manual_work_minutes"))
                review.append(number(rec.get("review_minutes"), tag+".review_minutes"))
                attempts = rec.get("attempts", [])
                if not isinstance(attempts, list):
                    raise ValueError(tag+".attempts must be array")
                elapsed_times, costs = [], []
                for i, attempt in enumerate(attempts):
                    elapsed_times.append(number(attempt.get("elapsed_minutes"), tag+f".attempts[{i}].elapsed_minutes"))
                    c = number(attempt.get("cost"), tag+f".attempts[{i}].cost")
                    currency = attempt.get("currency")
                    if c is not None:
                        if not isinstance(currency, str) or not currency.strip():
                            raise ValueError(tag+f".attempts[{i}]: cost requires currency")
                        currencies.add(currency)
                    costs.append(c)
                elapsed.append(sum(elapsed_times) if attempts and all(v is not None for v in elapsed_times) else None)
                total_cost.append(sum(costs) if attempts and all(v is not None for v in costs) else None)
                q = rec.get("final_quality")
                if q is None or (isinstance(q, dict) and q.get("status") == "unknown"):
                    quality["unknown"] += 1
                elif isinstance(q, dict) and q.get("status") == "reviewed" and isinstance(q.get("defects"), list):
                    quality["reviewed"] += 1
                    defects = q["defects"]
                    for d in defects:
                        if not isinstance(d, dict) or d.get("severity") not in SEVERITIES or not isinstance(d.get("category"), str) or not d["category"] or not isinstance(d.get("introduced_by_revision"), bool):
                            raise ValueError(tag+".final_quality.defects: each defect needs category, severity and introduced_by_revision")
                    quality["units_with_critical_defect"] += int(any(d["severity"] == "critical" for d in defects))
                    quality["units_with_any_defect"] += int(bool(defects))
                    quality["units_with_new_defect"] += int(any(d["introduced_by_revision"] for d in defects))
                else:
                    raise ValueError(tag+".final_quality status must be reviewed+defects or unknown")
            if len(currencies) > 1:
                # No FX assumptions; do not sum currencies.
                total_cost = [None for _ in total_cost]
            groups[cohort][condition] = {"run_units": len(selected), "manual_work_minutes": summary(manual),
                "human_review_minutes": summary(review), "generation_elapsed_minutes": summary(elapsed),
                "generation_cost": {"currency": next(iter(currencies)) if len(currencies) == 1 else None,
                                    "mixed_currency": len(currencies) > 1, **summary(total_cost)},
                "final_quality": quality}
        a = groups[cohort]["A"]
        b = groups[cohort]["B"]
        groups[cohort]["comparison"] = {}
        for name in ("manual_work_minutes", "human_review_minutes", "generation_elapsed_minutes", "generation_cost"):
            av = a[name].get("mean_if_complete")
            bv = b[name].get("mean_if_complete")
            if name == "generation_cost" and a[name].get("currency") != b[name].get("currency"):
                bv = None
            groups[cohort]["comparison"][name+"_mean_B_minus_A"] = round(bv-av, 6) if av is not None and bv is not None else None
    return {"schema_version": "art-pilot-metrics-v0.1", "ok": True, "study_id": records.get("study_id"),
            "study_kind": records["study_kind"], "pilot_upstream": upstream_summary,
            "extra": groups,
            "limitation": "Descriptive results only. Missing values are not zero, reviewed defects are reported only for reviewed samples. No causal or noninferiority claim; model cost, human time and subjective reviews are unverified inputs."}


def use_upstream(path: Path, records: dict) -> dict:
    spec = importlib.util.spec_from_file_location("art_director_frozen_pilot", path)
    if spec is None or spec.loader is None:
        raise ValueError("Cannot load upstream pilot.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.summarize(records)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("records", type=Path)
    p.add_argument("--upstream-pilot", type=Path, default=Path(__file__).parent/"vendor"/"pilot.py")
    p.add_argument("--out", type=Path)
    args = p.parse_args()
    try:
        if args.out and (args.out.exists() or args.out.is_symlink()):
            raise ValueError("Report already exists")
        raw_records = args.records.read_bytes()
        records = json.loads(raw_records.decode("utf-8-sig"))
        upstream = use_upstream(args.upstream_pilot, records)
        result = extend(records, upstream)
        result["records_sha256"] = hashlib.sha256(raw_records).hexdigest()
        value = json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
        if args.out:
            with args.out.open("x", encoding="utf-8") as target:
                target.write(value)
        print(value, end="")
        return 0
    except (OSError, ValueError, KeyError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
