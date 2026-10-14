#!/usr/bin/env python3
"""Append independently observed result provenance without creating a trusted decision.

All values are supplied by the operator. This is *not* game-exp candidate lookup,
review recording, or trusted artifact verification.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

from opportunity_card import append_result, parse_card

EXP_RE = re.compile(r"^EXP-[1-9][0-9]*$")
SHA_RE = re.compile(r"^[a-f0-9]{40}$")
SAFE_ID = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,80}$")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--card", type=pathlib.Path, required=True)
    p.add_argument("--result-id", required=True)
    p.add_argument("--observation", required=True)
    p.add_argument("--source", required=True, help="Actual evidence location/digest; may be a local-only pointer")
    p.add_argument("--limitations", required=True, help="Sample and evidence limits; do not omit")
    p.add_argument("--experiment-id")
    p.add_argument("--candidate-id")
    p.add_argument("--source-sha")
    p.add_argument("--probe-id")
    args = p.parse_args(argv)
    try:
        contents, card_id, _ = parse_card(args.card)
        if args.experiment_id and not EXP_RE.fullmatch(args.experiment_id):
            raise ValueError("Invalid experiment id")
        if args.candidate_id and (not args.experiment_id or not SAFE_ID.fullmatch(args.candidate_id)):
            raise ValueError("Candidate identity requires valid experiment id")
        if args.source_sha and not SHA_RE.fullmatch(args.source_sha):
            raise ValueError("Invalid exact source commit SHA")
        if args.probe_id and not SAFE_ID.fullmatch(args.probe_id):
            raise ValueError("Invalid PROBE id")
        if not args.observation.strip() or not args.source.strip():
            raise ValueError("Observed behavior and actual evidence source are required")
        if not args.limitations.strip():
            raise ValueError("Actual evidence limitations are required")
        refs = {"opportunity_id": card_id, "experiment_id": args.experiment_id,
                "candidate_id": args.candidate_id, "source_sha_reported": args.source_sha,
                "probe_id": args.probe_id, "provenance": "OPERATOR_REPORTED_NOT_LEDGER_VERIFIED"}
        ev = args.source.strip() + " | " + json.dumps(refs, ensure_ascii=False, separators=(",", ":"))
        # An observation is never interpreted as trusted PASS or an automatic decision.
        append_result(args.card, args.result_id, args.observation,
                      ev, "Evidence limits: " + args.limitations.strip() + "; no game-exp lifecycle action")
        print("LOCAL_ONLY_RESULT_LINKED " + card_id + " " + args.result_id)
    except (OSError, ValueError) as exc:
        print("RESULT_LINK_FAILED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
