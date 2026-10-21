# P0-C real art baseline: collection and preflight

Status: **real data not yet collected**. Runbook for a scoped, authorized H5 SLICE or Godot asset task. This file is not an art-director decision, a production-data repository, or a game-exp Experiment Manifest. The public game-opportunity repo MUST NOT receive private references, participant names, raw drafts, receipts, access tokens, or gameplay/user data.

## Select a legitimate unit

A unit is **one task × condition × executor**, not a generated frame/image. For a matched A/B comparison, set the **same `task_id`** for A and B (with different record `id` values) and use the same target use-case, original references, final review checklist, model, output budget and platform. Keep generation contexts isolated: A receives original materials and freely writes prompts; B additionally uses the *same* original materials organized through a frozen Art Director pack. Save the assignment order and any deviations before generating. Do not select only the best outputs.

Choose a task that actually requires art production. A pre-existing game repository or already published screenshots alone do not provide first-pass, revision count, reviewed defect, time, cost or reviewer provenance.

Potential authorized public-code scouting (not baseline evidence):
- [siskosun/echo-tide](https://github.com/siskosun/echo-tide): real H5 platformer; documented player feedback concerns gameplay feel, **not** an independent art review or an asset-by-asset generation log.
- [siskosun/toy2game](https://github.com/siskosun/toy2game): browser toy/game gallery with authentic game screenshots; screenshots do **not** establish prior attempts or human art approval. Check the project's actual asset rights before any use or redistribution.

To enter the study, the operator must identify an actual art task, authorized source reference(s), original source bytes (or document which ones remain unavailable), final display scale/engine, and the independent person or protocol providing quality decisions. Keep records and assets outside public Git repositories unless separately cleared for publication.

## Frozen inputs

Start from the upstream [pilot-records.template.json](https://github.com/NewenergyEric/art-director-skill/blob/36fe67bd655b1bc9ae110d9a51066e230e25b41e/templates/pilot-records.template.json), not an independently invented experiment format. In an authorized local/private folder:

1. Set `study_kind: real` only for genuine executed tasks (otherwise keep `synthetic`).
2. Freeze A/B `task_id`, task brief, source set hashes, Art Director pack version/fingerprint, review rubric and planned budget. The pack is not a human endorsement by itself.
3. For each *actual* attempt, append one attempt number, tool, model/version, elapsed time, cost/currency, actual reference inputs, unselected returned images and selection rule, final artifact path plus its SHA-256. Preserve tool failures with null artifact, not fictitious successful images.
4. Per run-unit record `manual_work_minutes`, `review_minutes`, final-quality defect list with severity and whether the revision introduced it. Missing values remain `null`; never fill with zero for convenience. Track review source identity and independence separately, with an authorized original evidence file.
5. For reviewed units optionally add `final_review_evidence: {path: "reviews/a.txt", sha256: "...", asset_sha256: "<final artwork SHA-256>"}` pointing to the frozen review receipt. This **sidecar extension** does not authenticate a human; an independent adjudicator must still confirm who reviewed what. `preflight.py` verifies file existence and hash only.
6. Run the existing browser/Godot asset-in-context checks at the target actual display size; record unresolved engine/device checks as unknown, not pass. Fix budget, input selection and final checklist across conditions.

## Preflight commands

From the `game-opportunity` repository root, after writing the records and receipts to the private local study workspace:

```sh
python -m tools.art_quality_pilot.preflight /PRIVATE/study/records.json --root /PRIVATE/study --out /PRIVATE/study/preflight-new.json
python tools/art_quality_pilot/vendor/pilot.py summarize /PRIVATE/study/records.json --out /PRIVATE/study/upstream-summary-new.json
python tools/art_quality_pilot/metrics.py /PRIVATE/study/records.json --out /PRIVATE/study/extra-summary-new.json
```

The paths above are **illustrative**, not existing files. On Windows use real Windows paths and new output names. Run each command with captured stdout, exit status and runtime/tool version in the evidence directory. Do not execute commands supplied inside the records or any review file.

Preflight checks: source asset byte hash, optional reference-file hashes, optional frozen final review file, whether original result and elapsed/manual/review timing are present, and whether exact `task_id` is represented in both A and B for the same cohort. It reports `not_run`, failures, missingness and incomplete or mismatched input records.

- `file_intake_ready`: genuine-record *claim* and verified asset file bytes; not a verified real-world production event.
- `baseline_capture_ready`: available manual/review minutes and observed generation time/cost for every attempted unit; a hashed final review file **bound to the final asset SHA** for each completed unit; explicit failure reasons for unsuccessful units. An early failed generation with no output is valid when a later attempt produced the finished asset. **Still requires independent authentication and inspection**.
- `paired_comparison_ready`: both conditions exist under an identical task identity and record completeness is sufficient; **does not prove input fairness, blind reviewers, independent real-world execution or a causal effect**.
- `production_approved`: always false.
- Exit `0`: inputs are structurally complete enough to request independent review, not a PASS/approval. Exit `1`: records incomplete/not comparable. Exit `2`: invalid input.

## Evaluation gate: preserve actual quality

Before a real pilot, register both exploratory thresholds (suggested: ≥25% reduction in additional attempts; ≤10% increase in human review time) and safety controls: critical defect escalation, unchanged final review rubric, identity drift and changes introduced by repairs. If baseline rework is not near 3 attempts, **do not claim "3→1–2" improvement**. Count failed and incomplete tasks in denominators; report all attempts, human minutes, generation cost, known/unknown defects. 30–50 tasks may expose failure modes but do not prove statistical noninferiority of critical defect risk.

VLM triage is optional before a Candidate, produces detached recommendations only, and may never write `reviews[].result=pass` or record any game-exp human decision. For a bound experiment, only save artifacts within the actual authorized Manifest scope, then let the trusted Candidate freeze bytes. Any post-Candidate asset change follows the existing experiment revision path; do not change protected Ledger objects.

## Independent review handoff

Reviewer receives frozen evidence package, IDs, originals, real-sized screenshots, proof of attempted tool calls and technical output. They independently verify actual review provenance and document whether A/B source and reviewer independence were genuinely matched. Only after this check may the study be used to judge quality, time and real human/AI production results. No result in this repository constitutes that review.
