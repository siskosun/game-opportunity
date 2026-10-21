#!/usr/bin/env python3
"""Verify a detached asset/rule/evidence sidecar. Not an approval or run attestation.

Dependencies: Python 3.10+ standard library. Validation never runs submitted commands.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path

SCHEMA = "art-evidence-v0.1"
SHA = re.compile(r"^[0-9a-f]{64}$")
METHODS = {"technical-tool", "visual-human", "vlm-triage"}
RESULTS = {"pass", "fail", "unknown", "suspected"}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def inside(root: Path, relative: str, purpose: str) -> Path:
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise ValueError(f"{purpose}: nonempty POSIX relative path required")
    pp = Path(relative)
    if pp.is_absolute() or any(s in (".", "..", "") for s in pp.parts):
        raise ValueError(f"{purpose}: path traversal or absolute path")
    target = root.joinpath(*pp.parts)
    if any(root.joinpath(*pp.parts[:i]).is_symlink() for i in range(1, len(pp.parts) + 1)):
        raise ValueError(f"{purpose}: symlink not allowed")
    if not target.resolve().is_relative_to(root):
        raise ValueError(f"{purpose}: escapes workspace")
    if not target.is_file():
        raise ValueError(f"{purpose}: not a regular file: {relative}")
    return target


def check_hash(root: Path, record: dict, label: str, failures: list[str]) -> tuple[Path | None, str | None]:
    if not isinstance(record, dict):
        failures.append(f"{label}: expected object")
        return None, None
    expected = record.get("sha256")
    if not isinstance(expected, str) or not SHA.fullmatch(expected):
        failures.append(f"{label}: invalid sha256")
        return None, None
    try:
        file = inside(root, record.get("path"), label)
        if file.stat().st_size == 0:
            failures.append(f"{label}: empty evidence file")
            return file, None
        actual = digest(file)
        if expected != actual:
            failures.append(f"{label}: sha256 mismatch")
        return file, actual
    except (OSError, ValueError) as exc:
        failures.append(str(exc))
        return None, None


def check_record(evidence: dict, *, root: Path, brief: dict, brief_sha256: str) -> dict:
    """Verify binding, not authenticity, aesthetics, or human authorization."""
    errors: list[str] = []
    if not isinstance(evidence, dict) or evidence.get("schema_version") != SCHEMA:
        return {"ok": False, "status": "invalid", "errors": ["invalid schema_version"], "approval": False}
    root = root.resolve(strict=True)
    asset_file, asset_hash = check_hash(root, evidence.get("asset"), "asset", errors)
    pack = brief.get("pack") if isinstance(brief, dict) else None
    declared = evidence.get("pack")
    if not isinstance(pack, dict) or not isinstance(declared, dict):
        errors.append("pack: missing binding")
    elif not all(isinstance(pack.get(k), str) and pack.get(k) for k in ("id", "version", "fingerprint")):
        errors.append("brief: missing project, version or fingerprint")
    else:
        required = {"project_id": pack["id"], "version": pack["version"], "fingerprint": pack["fingerprint"]}
        if declared != required:
            errors.append("pack: identity/version/fingerprint mismatch")
    brief_pin = evidence.get("brief_sha256")
    if brief_pin != brief_sha256:
        errors.append("brief: sha256 mismatch")
    criterion = evidence.get("criterion_id")
    checks = (brief.get("direction_checks") or []) if isinstance(brief, dict) else []
    rule_checks = (brief.get("review") or []) if isinstance(brief, dict) else []
    known = {x.get("criterion") for x in checks
             if isinstance(x, dict) and isinstance(x.get("criterion"), str)}
    known.update("rule/" + x["rule_id"] for x in rule_checks if isinstance(x, dict) and isinstance(x.get("rule_id"), str))
    if not isinstance(criterion, str) or criterion not in known:
        errors.append("criterion_id: not part of the frozen task brief")
    method = evidence.get("method")
    result = evidence.get("result")
    # A successful pixel/dimension inspection must never stand in for an
    # artistic, human, or otherwise untyped acceptance criterion. The brief
    # retains the original rule verification, whereas generated direction
    # checks for families/exemplars/delivery do not all carry it.
    technical_criterion = False
    if isinstance(criterion, str) and criterion in known:
        if criterion.startswith("rule/"):
            rule_id = criterion.removeprefix("rule/")
            matching_rules = [r for r in (brief.get("rules") or [])
                              if isinstance(r, dict) and r.get("id") == rule_id]
            technical_criterion = (len(matching_rules) == 1 and matching_rules[0].get("verification") == "technical")
        else:
            technical_criterion = criterion.endswith("/technical") and (
                criterion.startswith("family/") or criterion.startswith("delivery/"))
    if method == "technical-tool" and result in {"pass", "fail"} and not technical_criterion:
        errors.append("criterion_id: technical result cannot evaluate an artistic/human/untyped criterion")
    if not isinstance(method, str) or method not in METHODS or not isinstance(result, str) or result not in RESULTS:
        errors.append("method/result: unsupported")
    if method == "vlm-triage" and result not in {"suspected", "unknown"}:
        errors.append("vlm-triage must never return an acceptance verdict")
    if method == "technical-tool" and result not in {"pass", "fail", "unknown"}:
        errors.append("technical-tool: invalid result")
    tool = evidence.get("tool")
    if not isinstance(tool, dict) or any(not isinstance(tool.get(k), str) or not tool[k] for k in ("name", "version")):
        errors.append("tool: name and version required")
    execution = evidence.get("execution")
    if not isinstance(execution, dict):
        errors.append("execution: missing")
        execution = {}
    raw_file, raw_hash = check_hash(root, {"path": execution.get("raw_output_path"), "sha256": execution.get("raw_output_sha256")}, "raw_output", errors)
    command_file, command_hash = check_hash(root, {"path": execution.get("command_or_prompt_ref"), "sha256": execution.get("command_or_prompt_sha256")}, "command_or_prompt", errors)
    # Narrow, reproducible adapter: Art Director's pilot.py check-image raw JSON.
    if method == "technical-tool":
        if not isinstance(tool, dict) or tool.get("name") != "art-director/pilot.py" or tool.get("version") != "1.0":
            errors.append("technical-tool: unsupported adapter (pilot.py v1.0 only)")
        if raw_file and raw_hash == execution.get("raw_output_sha256"):
            try:
                report = json.loads(raw_file.read_text(encoding="utf-8"))
                if not isinstance(report, dict):
                    raise ValueError("check-image report must be a JSON object")
                if report.get("command") != "check-image" or report.get("sha256") != asset_hash:
                    errors.append("raw_output: wrong command or asset hash")
                checks_report = report.get("checks")
                if not isinstance(checks_report, dict) or not checks_report:
                    errors.append("raw_output: missing technical checks")
                else:
                    statuses = [x.get("result") if isinstance(x, dict) else None for x in checks_report.values()]
                    all_pass = all(x == "pass" for x in statuses)
                    any_fail = any(x == "fail" for x in statuses)
                    if result == "pass" and (not report.get("ok") or not all_pass):
                        errors.append("raw_output: cannot substantiate pass")
                    if result == "fail" and (report.get("ok") or not any_fail):
                        errors.append("raw_output: cannot substantiate fail")
                if asset_file and Path(report.get("source_path", "")).resolve() != asset_file.resolve():
                    errors.append("raw_output: source_path does not match asset")
            except (ValueError, OSError, TypeError) as exc:
                errors.append("raw_output: invalid JSON/check-image report: " + str(exc))
    return {
        "ok": not errors, "status": "bound" if not errors else "invalid", "errors": errors,
        "binding": {"criterion_id": criterion, "asset_sha256": asset_hash, "raw_output_sha256": raw_hash, "command_sha256": command_hash},
        "approval": False,
        "criterion_assessment": "not_performed",
        "scope": "File binding and narrowly scoped tool-report consistency only; technical pass/fail never establishes satisfaction of the linked project rule, trusted execution, or human art approval."
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--brief", required=True, type=Path)
    parser.add_argument("--out", type=Path, help="New JSON report path; never overwrite")
    args = parser.parse_args()
    try:
        if args.out and (args.out.exists() or args.out.is_symlink()):
            raise ValueError("Report path already exists")
        result = check_record(json.loads(args.evidence.read_text(encoding="utf-8")), root=args.root, brief=json.loads(args.brief.read_text(encoding="utf-8")), brief_sha256=digest(args.brief))
        body = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
        if args.out:
            with args.out.open("x", encoding="utf-8") as output:
                output.write(body)
        print(body, end="")
        return 0 if result["ok"] else 1
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
