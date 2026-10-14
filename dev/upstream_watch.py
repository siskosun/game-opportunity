#!/usr/bin/env python3
"""Propose changed published upstream tags, never promote an unverified lock.

Called by scheduled GitHub Actions. No tokens, local user data or real
opportunity cards are included. Nonzero exit on incomplete/moved metadata.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/game-opportunity/scripts"))
import check_bundle


def candidate() -> dict | None:
    lock = check_bundle.load_lock()
    remote = check_bundle.remote_status(lock)
    invalid = {n: v["state"] for n, v in remote.items() if v["state"] in ("UNVERIFIED", "TAG_DRIFT")}
    if invalid:
        raise check_bundle.BundleCheckError("UPSTREAM_UNVERIFIED_OR_MOVED_TAG: " + ", ".join(f"{n}={v}" for n, v in invalid.items()))
    updates = {name: {"current_pin": info["pinned_tag"], "proposed_new_tag": info["latest_published_tag"],
                      "qualification": "UNTESTED_CANDIDATE_REQUIRES_CROSS_REPOSITORY_CI_AND_HUMAN_APPROVAL"}
               for name, info in remote.items() if info["state"] == "UPDATE_AVAILABLE_UNTESTED"}
    if not updates:
        return None
    return {"schema_version": 1, "status": "DRAFT_PROPOSAL_ONLY_NOT_A_COMPATIBILITY_LOCK",
            "bundle_version": lock["bundle_version"], "changes": updates,
            "instructions": ["Review the upstream Release/tag and exact commit before changing compatibility.lock.json.",
                             "Review API/Manifest/PROBE contracts, license notices and version compatibility.",
                             "Run Windows/Ubuntu tests and a real installed four-Skill smoke test.",
                             "Do not merge/publish or auto-install from this draft proposal."]}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=pathlib.Path, required=True)
    args = p.parse_args(argv)
    try:
        report = candidate()
    except (check_bundle.BundleCheckError, ValueError):
        print("UPSTREAM_WATCH_UNVERIFIED: cannot safely propose a version update", file=sys.stderr)
        return 2
    if report is None:
        print("UPSTREAM_WATCH_CURRENT: no new released tags")
        return 0
    if args.output.exists() or args.output.is_symlink():
        print("UPSTREAM_WATCH_OUTPUT_EXISTS: refusing overwrite", file=sys.stderr)
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("UPSTREAM_WATCH_DRAFT_CANDIDATE: " + str(args.output))
    return 0


if __name__ == "__main__":
    sys.exit(main())
