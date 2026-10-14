#!/usr/bin/env python3
"""Read-only, untrusted opportunity -> playable-experiment research handoff.

NOT a game-exp Manifest; no network, no Git operations, no Ledger mutations.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys

from opportunity_card import LABELS, parse_card

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
ID_RE = re.compile(r"^OPP-\d{8}-[a-z0-9]+(?:-[a-z0-9]+)*$")


class HandoffError(ValueError):
    pass


def section(text: str, heading: str) -> str:
    m = re.search(r"^## " + re.escape(heading) + r"\s*\n(?P<text>.*?)(?=^## |\Z)", text, re.M | re.S)
    if not m:
        raise HandoffError(f"Missing card section: {heading}")
    return m.group("text").strip()


def create_handoff(card: pathlib.Path, *, stack: str, mode: str, next_hypothesis: str = "",
                   next_kill: str = "", reason: str = "", confirm_same: bool = False,
                   remote_ref: str = "", remote_commit: str = "") -> dict:
    source, opportunity_id, route = parse_card(card)
    if not ID_RE.fullmatch(opportunity_id):
        raise HandoffError("Invalid opportunity ID")
    if stack not in {"h5", "godot"}:
        raise HandoffError("Target must be h5 or godot; this is not a deployment command")
    q = section(source, LABELS["uncertainty"])
    criteria = section(source, LABELS["decision"])
    test = section(source, LABELS["validation"])
    if mode == "same-question":
        if not confirm_same:
            raise HandoffError("--confirm-same-question is required; compare the actual claim and population first")
        if next_hypothesis or next_kill or reason:
            raise HandoffError("Do not silently rewrite a same-question claim")
        hypothesis, kill = q, criteria
        provenance = "SAME_CLAIM_AND_POPULATION_OPERATOR_CONFIRMED"
    elif mode == "next-stage":
        if not all(x.strip() for x in (next_hypothesis, next_kill, reason)):
            raise HandoffError("Next-stage requires --next-hypothesis, --next-kill and --reason")
        if next_hypothesis.strip().casefold() == q.strip().casefold():
            raise HandoffError("Next-stage claim is identical; use same-question or state a material change")
        hypothesis, kill = next_hypothesis.strip(), next_kill.strip()
        provenance = "NEW_STAGE_QUESTION_OPERATOR_DECLARED"
    else:
        raise HandoffError("Mode must be same-question or next-stage")
    if (remote_ref and not remote_commit) or (remote_commit and not remote_ref):
        raise HandoffError("Remote path and commit SHA must be provided together")
    if remote_commit and not SHA_RE.fullmatch(remote_commit):
        raise HandoffError("Remote source commit must be a 40-character lowercase SHA")
    return {
        "schema_version": 1,
        "kind": "game_opportunity_handoff",
        "authority": "ORDINARY_RESEARCH_NOT_LEDGER_NOT_MANIFEST",
        "source": {
            "opportunity_id": opportunity_id,
            "route": route,
            "card_sha256": hashlib.sha256(card.read_bytes()).hexdigest(),
            "local_file": str(card.resolve()),
            "portable": False,  # User-reported remote paths are not verified durable evidence.
            "remote_claimed": bool(remote_ref),
            "remote_path_reported": remote_ref or None,
            "remote_commit_reported": remote_commit or None,
            "remote_verified": False,  # A caller must independently read that exact SHA.
        },
        "target_stack": stack,
        "question_relation": provenance,
        "question_change_reason": reason.strip() if mode == "next-stage" else None,
        "research_question": q,
        "research_decision_conditions": criteria,
        "proposed_cheapest_validation": test,
        "proposed_experiment_hypothesis": hypothesis,
        "proposed_experiment_kill_criteria": [kill],
        "not_manifest_ready": True,
        "requires_actual_repository_issue_parent_scope_runtime_review_and_user_confirmation": True,
        "game_exp_experiment_id": None,
        "candidate_id": None,
        "review_outcome": None,
        "constraints": [
            "Not evidence that any human trial ran or hypothesis succeeded.",
            "Research stop criterion is not automatically a gameplay kill criterion.",
            "Do not insert unrecognized fields into a game-exp Manifest.",
            "Use game-exp experiment-template for supported schema and authoritative Bind.",
            "No H5 machine verdict may be promoted to a human game-exp Review.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--card", type=pathlib.Path, required=True)
    ap.add_argument("--stack", choices=("h5", "godot"), required=True)
    ap.add_argument("--mode", choices=("same-question", "next-stage"), required=True)
    ap.add_argument("--confirm-same-question", action="store_true")
    ap.add_argument("--next-hypothesis", default="")
    ap.add_argument("--next-kill", default="")
    ap.add_argument("--reason", default="")
    ap.add_argument("--remote-path", default="")
    ap.add_argument("--remote-commit", default="")
    ap.add_argument("--output", type=pathlib.Path, help="Optional LOCAL_ONLY JSON; never upload automatically")
    args = ap.parse_args(argv)
    try:
        payload = create_handoff(args.card, stack=args.stack, mode=args.mode,
                                 next_hypothesis=args.next_hypothesis, next_kill=args.next_kill,
                                 reason=args.reason, confirm_same=args.confirm_same_question,
                                 remote_ref=args.remote_path, remote_commit=args.remote_commit)
        rendered = json.dumps(payload, ensure_ascii=False, indent=2)
        if args.output:
            if args.output.is_symlink() or args.output.exists():
                raise HandoffError("Refusing to overwrite handoff evidence")
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("x", encoding="utf-8", newline="\n") as f:
                f.write(rendered + "\n")
            print("LOCAL_ONLY " + str(args.output.resolve()))
        else:
            print(rendered)
    except (HandoffError, ValueError, OSError) as exc:
        print("HANDOFF_FAILED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
