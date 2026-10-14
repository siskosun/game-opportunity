# One hypothesis lineage; no third protocol

An opportunity card is an upstream research note, not a frozen H5 PROBE card or protected game-exp Manifest. Its three key decision sections are the user-facing minimum and must not be duplicated as multiple new mandatory manifests.

## To H5 PROBE

1. Provide stable `opportunity_id`, public-safe repository/path or authorized private evidence pointer, and source commit SHA (if confirmed remotely); otherwise mark `NOT_PERSISTED`.
2. Compare the card's key uncertainty/decision criteria with the intended H5 `hypothesis` and `kill_criteria`.
3. If they address **the exact same claim and population**, copy the frozen wording or the exact operative testable part, keep a citation, and don't secretly rewrite it.
4. If the prior stage tested demand but the next tests gameplay, write a genuinely new next-stage `hypothesis` and `kill_criteria`; keep the earlier claim as origin context rather than falsely saying it has been verified.
5. Use the existing `probe_card.md` schema and `scripts/probe_log.py search KEYWORD` for gameplay probes. Don't introduce an incompatible field or a new second PROBE log. Its `probes.jsonl` is scoped to its selected path; it is not a global opportunity index.
6. Append observations/results and the corresponding PROBE IDs, source artifacts and trial limits to the opportunity card only when evidence exists.

## To Godot

Pass player outcome, key uncertainty, proposed smallest playtest and sources in normal brief context. Godot owns tests and player evidence. Do not override its authoritative design brief or build a game merely because a card exists.

## To game-exp

When an actual bound experiment is justified, create/confirm the real repository and follow game-exp's exact existing `PROJECT_READY`/Bind/Initialize/Manifest/human Review sequence. Use the card link as optional research context, not a protected Ledger object. Reuse the same hypothesis and stop criteria only if the question is unchanged; otherwise explicitly define the new stage's falsifiable question. A H5 machine verdict is not a game-exp Review PASS. The card cannot submit, promote, reject, select, or archive experiments.

No automatic handoff if the task can be answered with concept research, a human-designed interview, or non-playable testing. Stage changes must be explicit, but not a new approval protocol.

## Main Skill orchestration and formal experiment entry

When the user requests the full idea-to-playable-to-decision journey, use `references/full-workflow.md`. The opportunity Skill is the **user-facing orchestrator**; game-exp alone owns experiment state, project-create, Bind, Candidate, Review and human promotion. Follow the exact current game-exp capability/version handshake, then the authoritative Manifest template. Its strict Manifest validator rejects extra opportunity fields. Do not create a second manifest-like artifact or direct Ledger writes.

A read-only `scripts/handoff_bundle.py` can describe an upstream hypothesis for a human/executor to check. A local evidence file or unverified reported remote SHA does not prove remote persistence. Formal project creation must be explicitly requested and authorized, and project visibility must be checked before copying source evidence. game-exp `project-create` defaults public; keep private audience/business data out of public project repositories.

After real tests, `scripts/link_result.py` may append operator-reported PROBE/experiment/Candidate/source identifiers and actual observation limits to the opportunity card, but it never infers game-exp Review PASS or verifies a reported Candidate. If those references matter, inspect the exact authoritative game-exp Ledger and immutable Candidate before describing them as verified.
