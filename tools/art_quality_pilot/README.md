# Art Quality P0: optional pilot & evidence binding

Status: **P0 technical implementation / synthetic smoke tests only**. This is **not** a fifth mandatory Skill, a human art-review gate, or a production result. All examples are artificial. Use the existing Art Director project pack; do not recreate its visual rule engine.

## Scope

- `vendor/pilot.py`: exact frozen upstream Art Director pilot (MIT) copied from `NewenergyEric/art-director-skill` at SHA `36fe67bd655b1bc9ae110d9a51066e230e25b41e`. Preserve the upstream license in `vendor/LICENSE`. This component is available even if the upstream disappears. On upgrades, inspect upstream diff and re-run tests; do not track `main` implicitly.
- `metrics.py`: a small **additive** descriptive supplement to upstream `pilot.py summarize`: observed/missing human manual/review minutes, generation elapsed time, explicit currency cost, and independently reviewed final defects. It binds the report to the exact input-record bytes (`records_sha256`) and creates outputs exclusively, without overwriting previous reports. A/B data from the upstream summary is retained unchanged. Missing values stay missing (mean=null if incomplete); no causal claims.
- `evidence.py`: a **detached evidence validator** that binds a single asset and raw tool output to the frozen Art Director `brief` and `criterion_id` using SHA-256. It never writes to `reviews[].result` or game-exp records. For positive technical reports it understands only upstream `pilot.py check-image v1.0`; all other tools need a separately verified adapter. It refuses to attach a `technical-tool` pass/fail to a nontechnical (visual/human/untyped) criterion and returns `criterion_assessment: not_performed` in all cases. It does **not** authenticate execution or reviewers.
- `tests/test_art_quality_pilot.py`: synthetic inputs and adversarial tests, run in the existing Linux/Windows `unittest` CI.

## How to test

From repository root:

```shell
python -m unittest discover -s tests -v
python tools/art_quality_pilot/vendor/pilot.py summarize tools/art_quality_pilot/fixtures/synthetic_records.json --out /tmp/pilot-synthetic-summary.json
python tools/art_quality_pilot/metrics.py tools/art_quality_pilot/fixtures/synthetic_records.json --out /tmp/pilot-extra-summary.json
```

Commands writing `/tmp` are examples for Unix systems; replace output paths on Windows. **New output filenames** are required by upstream `pilot.py` and our wrappers.

For the sidecar verifier:

```shell
python tools/art_quality_pilot/evidence.py evidence.json --root /path/to/project --brief /path/to/frozen/brief.json --out /path/to/new/report.json
```

The evidence input schema `art-evidence-v0.1` uses:

```json
{
  "schema_version": "art-evidence-v0.1",
  "asset": {"path": "assets/hero.png", "sha256": "64 lowercase hex"},
  "pack": {"project_id": "game", "version": "0.2.0", "fingerprint": "from Art Director"},
  "brief_sha256": "sha256 of the frozen brief JSON",
  "criterion_id": "rule/CHR-001",
  "method": "technical-tool",
  "tool": {"name": "art-director/pilot.py", "version": "1.0"},
  "execution": {
    "command_or_prompt_ref": "checks/command.txt",
    "command_or_prompt_sha256": "sha256 of actual invocation record",
    "raw_output_path": "checks/check-image.json",
    "raw_output_sha256": "sha256 of original tool report"
  },
  "result": "pass"
}
```

All referenced `asset` and `execution` paths are relative to `--root` and must exist. `--brief` is the exact output of `style_pack.py brief` and must be recorded/frozen along with the project pack. It contains `pack.id`, `.version`, `.fingerprint`, `direction_checks` and `review`. The validator compares nonempty referenced files, actual bytes, frozen brief identity and rule membership. A VLM triage report may return **only `suspected` or `unknown`**, never `pass`. A human's `pass` is still merely a recorded observation until independent authorization is evidenced. A successful `technical-tool` check indicates *only that the raw measurement is internally consistent*: it never means that the linked style rule or human review is approved.

**Trust boundary:** Self-declared hashes can be recomputed after tampering; the script detects mismatches and accidental cross-artifact reuse, but it is not a signature, audit log or source of authority. For a credible run, capture the unchanged input SHA and raw output in trusted CI/Candidate provenance. One cannot prove that a command actually ran merely because a `command.txt` exists. The source/brief hashes should be cross-checked against the Candidate's frozen bytes. `production_approved` remains false.

## Real baseline preflight (P0-C preparation)

Read [REAL_PILOT_RUNBOOK.md](REAL_PILOT_RUNBOOK.md) before any real asset trial. The new read-only script checks concrete local asset hashes, links to hashed final-review receipts bound to final asset SHA-256, generation cost/time availability and whether A/B records have matching `task_id` values, while withholding approval/causal claims. It is deliberately distinct from the synthetic statistical smoke tests. The resulting report includes the exact input `records_sha256`; a failed/incomplete task's review does not count toward a completed task's missing final review; only completed tasks with their own verified deliverables and bound review receipts qualify.

Run from the repository root:

```shell
python -m tools.art_quality_pilot.preflight RECORDS.json --root /path/to/private/study --out NEW_PREFLIGHT.json
```

Exit 0 means structurally complete for a separate manual audit, **not** genuine reviewer verification or a production PASS. Exit 1 signals incomplete sample; exit 2 signals invalid input. Running it on the bundled synthetic fixture must not yield a real baseline. The repository includes no personal data or real art-review dataset.

## Pilot measurement and decision rules

Each run-unit is one task×condition×participant record, not an image count. Mark input `study_kind=synthetic|real`. For the supplement, each attempted generation can carry nonnegative `elapsed_minutes`, `cost`, `currency`; each record can carry `manual_work_minutes`, `review_minutes`, and `final_quality`: `{status: reviewed, defects: [{category, severity: critical|major|minor, introduced_by_revision: boolean}]}`. No `final_quality` means unknown, not zero defects. A currency mismatch suppresses aggregate costs. The upstream pilot still determines first-pass and rework definitions. Keep `ai_proxy` separate from `human_team` and collect source images and exact settings before inference.

Exploratory promotion threshold (prospective, **not a current measurement**): in 30–50 real asset-task pilot units, average additional attempts falls by ≥25% against fair baseline, human review time rises by no more than 10%, and there is no unaddressed new critical defect. Report human effort and total costs separately. This can justify a larger trial, **not** statistical proof of serious-defect noninferiority. Stop expansion after one bounded redesign if cost or error burden shows no material improvement. Escalate any critical defect for actual review; don't silently issue PASS.

## game-exp integration contract

Optional evidence and triage occur during implementation, **before a Candidate build**. Only if allowed by the experiment Manifest scope, commit the source, project pack, inspected assets and reports, then let the trusted game-exp Candidate freeze actual bytes. Never add unknown fields to the Manifest, edit the protected Ledger, or let a sidecar/AI review call a human `PASS/FAIL/PROMISING/SELECTED`. Changes after Candidate require the documented revision and new Candidate path.

## Limitations and remaining work

P0-A and P0-B are synthetic only. P0-C has a file/record preflight and collection runbook, **but no real H5 SLICE or Godot art experiment has been executed, independently reviewed or timed here**. `metrics.py` deliberately provides **no confidence interval** when n is small or unrepresentative. VLM/LoRA/CSD and local-edit repair are **not implemented**. Position-indexed criterion IDs in Art Director remain version-bound; do not equate IDs across versions without a migration map.

Upstream source: https://github.com/NewenergyEric/art-director-skill, license MIT. This directory is optional and is not included in the published game-opportunity Skill ZIP unless explicitly added by a future approved rollout.
