#!/usr/bin/env python3
"""Read-only preflight for real Art Director A/B pilot provenance.

Use existing upstream pilot records. Never invent work, rate images, authenticate
reviewers, or modify game-exp state. Exit 0: baseline capture has file evidence;
1: incomplete; 2: invalid input. A 0 is NOT a study conclusion or approval.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import sys

from tools.art_quality_pilot import evidence, metrics


def _file_check(root: Path, path: object, sha: object, label: str) -> tuple[bool, str]:
    if not isinstance(sha, str) or not evidence.SHA.fullmatch(sha):
        return False, f"{label}: missing or invalid sha256"
    try:
        actual_path = evidence.inside(root, path, label)
        if evidence.digest(actual_path) != sha:
            return False, f"{label}: sha256 mismatch"
    except (OSError, ValueError) as exc:
        return False, str(exc)
    return True, ""


def assess(data: dict, root: Path, *, frozen_upstream: Path | None = None) -> dict:
    """Inspect local receipts; do not infer genuine human approval from text."""
    if not isinstance(data, dict) or data.get("study_kind") not in {"real", "synthetic"}:
        raise ValueError("study_kind must be real or synthetic")
    # Validate original experimental-unit schema and denominators, do not build
    # an alternative pilot protocol in this script.
    pilot = frozen_upstream or (Path(__file__).parent / "vendor" / "pilot.py")
    upstream = metrics.use_upstream(pilot, data)
    if not upstream.get("ok"):
        raise ValueError("upstream pilot schema validation failed")
    metrics.extend(data, upstream)  # Validate supplemental numeric/quality fields too.
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("--root must be a directory")
    warnings: list[str] = []
    errors: list[str] = []
    sample_checks = []
    pair: dict[tuple[str, str], set[str]] = defaultdict(set)
    seen_attempted = set()
    completed_with_files = 0
    complete_time_records = 0
    complete_generation_records = 0
    documented_final_reviews = 0
    failure_records_documented = 0
    successful_records = 0
    for rec in data["records"]:
        rid = rec["id"]
        status = rec["execution_status"]
        issues = []
        observations = []
        if status == "not_run":
            sample_checks.append({"id": rid, "status": "not_run", "evidence_files_verified": 0, "issues": [], "observations": []})
            continue
        seen_attempted.add(rid)
        if status == "completed":
            successful_records += 1
        elif rec.get("failure_reason"):
            failure_records_documented += 1
        else:
            warnings.append(f"{rid}: failed/incomplete unit without an explicit failure_reason")
        pair[(rec["cohort"],rec["task_id"])].add(rec["condition"])
        generation_metadata_complete = True
        last_artifact_sha = None
        for idx, attempt in enumerate(rec["attempts"]):
            label = f"{rid}.attempts[{idx}]"
            artifact_path = attempt.get("artifact_path")
            if artifact_path:
                success, explanation = _file_check(root, artifact_path, attempt.get("artifact_sha256"), label + ".artifact")
                if success:
                    observations.append("artifact_sha256_verified")
                    last_artifact_sha = attempt["artifact_sha256"]
                else:
                    issues.append(explanation)
            elif any(v == "pass" for v in (attempt.get("review") or {}).values()):
                issues.append(label + ": passed review without any artifact")
            elif not attempt.get("failure_reason"):
                warnings.append(label + ": no output, but failure reason is not recorded")
            if not attempt.get("tool") or not attempt.get("model"):
                warnings.append(label + ": tool/model provenance incomplete")
            if artifact_path and not attempt.get("review_evidence"):
                warnings.append(label + ": no rule-level review evidence; cannot treat pass as human approval")
            inspection=attempt.get("visual_inspection")
            if artifact_path and (not isinstance(inspection,dict) or not inspection.get("files_opened")):
                warnings.append(label + ": visual inspection not recorded")
            if attempt.get("elapsed_minutes") is None or attempt.get("cost") is None:
                warnings.append(label + ": elapsed time or generation cost unobserved")
                generation_metadata_complete = False
            for j, input_ref in enumerate(attempt.get("actual_reference_inputs") or []):
                if not isinstance(input_ref,dict):
                    issues.append(f"{label}.actual_reference_inputs[{j}]: not an object")
                    continue
                ref_path=input_ref.get("path")
                if ref_path:
                    verified,why=_file_check(root,ref_path,input_ref.get("sha256"),f"{label}.actual_reference_inputs[{j}]")
                    if verified:
                        observations.append("reference_sha256_verified")
                    else:
                        issues.append(why)
                else:
                    warnings.append(f"{label}.actual_reference_inputs[{j}]: input bytes not locatable")
        if status == "completed" and last_artifact_sha is None:
            issues.append(f"{rid}: completed unit has no verified artifact")
        if generation_metadata_complete and rec["attempts"]:
            complete_generation_records += 1
        if rec.get("manual_work_minutes") is not None and rec.get("review_minutes") is not None:
            complete_time_records += 1
        else:
            warnings.append(f"{rid}: manual or review minutes unobserved")
        final=rec.get("final_quality")
        if not isinstance(final,dict) or final.get("status") != "reviewed":
            warnings.append(f"{rid}: final defect review missing or unknown")
        elif not isinstance(rec.get("final_review_evidence"), dict):
            warnings.append(f"{rid}: final_quality is self-reported without independent review source")
        else:
            receipt=rec["final_review_evidence"]
            valid,reason=_file_check(root,receipt.get("path"),receipt.get("sha256"),
                                     f"{rid}.final_review_evidence")
            if valid and status == "completed" and receipt.get("asset_sha256") != last_artifact_sha:
                valid=False
                reason=f"{rid}.final_review_evidence: final asset sha256 mismatch"
            if valid:
                documented_final_reviews+=1
                observations.append("review_file_sha256_verified")
            else:
                issues.append(reason)
        if any(x=="artifact_sha256_verified" for x in observations) and not issues:
            completed_with_files+=1
        sample_checks.append({"id":rid,"status":status,"evidence_files_verified":observations.count("artifact_sha256_verified"),
                              "issues":issues,"observations":sorted(set(observations))})
        errors.extend(issues)
    paired=[{"cohort":cohort,"task_id":task_id} for (cohort,task_id),conditions in pair.items() if conditions=={"A","B"}]
    # A receipt is only file integrity, not evidence that the declared human
    # decision is authentic. Failed/incomplete attempts stay in the denominator
    # and need an explicit failure reason, not a fictitious final artwork.
    receipts_ready=(data["study_kind"]=="real" and not errors and completed_with_files>0)
    baseline_ready=(receipts_ready and complete_time_records==len(seen_attempted)
                    and complete_generation_records==len(seen_attempted)
                    and documented_final_reviews==successful_records
                    and failure_records_documented==len(seen_attempted)-successful_records
                    and completed_with_files>=successful_records)
    # A/B pairing is structural only. Fairness and independent human identity
    # are not verified, even when ready_for_review is true.
    comparison_ready=baseline_ready and bool(paired)
    if data["study_kind"]!="real":
        warnings.append("synthetic study: never count as genuine art production evidence")
    if not paired:
        warnings.append("no completed same-cohort A/B task pairs; paired comparison unavailable")
    return {"schema_version":"art-pilot-preflight-v0.1", "ok": not errors,
            "study_id":data["study_id"],"study_kind":data["study_kind"],"baseline_capture_ready":baseline_ready,
            "paired_comparison_ready":comparison_ready,
            "attempted_records":len(seen_attempted),"artifact_verified_records":completed_with_files,
            "file_intake_ready":receipts_ready,"time_observed_records":complete_time_records,
            "generation_time_and_cost_observed_records":complete_generation_records,
            "documented_final_review_files":documented_final_reviews,
            "paired_task_count":len(paired),"paired_tasks":paired,
            "file_errors":errors,"warnings":warnings,"samples":sample_checks,"production_approved":False,
            "scope":"File/hash linkage and experimental-unit pairing only. A ready flag signals record completeness for independent review, not genuine production samples, verified human identity, fair comparison, artistic acceptance or game-exp Candidate validity."}


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("records",type=Path)
    p.add_argument("--root",required=True,type=Path)
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    try:
        if args.out and (args.out.exists() or args.out.is_symlink()):
            raise ValueError("report path already exists")
        data=json.loads(args.records.read_text(encoding="utf-8-sig"))
        result=assess(data,args.root)
        body=json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+"\n"
        if args.out:
            with args.out.open("x", encoding="utf-8") as output:
                output.write(body)
        sys.stdout.write(body)
        return 0 if result["baseline_capture_ready"] and not result["file_errors"] else 1
    except (OSError,ValueError,KeyError,TypeError) as exc:
        sys.stdout.write(json.dumps({"ok":False,"error":str(exc)},ensure_ascii=False)+"\n")
        return 2


if __name__=="__main__":
    raise SystemExit(main())
