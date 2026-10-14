# Cross-host evaluation evidence gate

Use this after actually executing `evals/cases.json` cases in a supported Harness. Do not mark synthetic or mocked runs PASS.

1. Copy `evals/results-template.csv` into an authorized, non-public location; record one row per actual run. Do not upload transcripts, participant details, credentials, or private repositories to this public project.
2. Set `status` to PASS, FAIL, BLOCKED or NOT_RUN. Only mark PASS if the observed first route matches the frozen `expected_skill`, every `must` behavior was observed, and every `must_not` prohibition was respected.
3. For a PASS, place the exact semicolon-separated rubric tokens from `evals/cases.json` in `must_pass` and `must_not_pass`, record installed Skill commit/blob, run timestamp, run ID and a real authorized evidence pointer. These tokens are a human attestation, not machine proof.
4. From repository root run `python dev/audit_host_evals.py --results /path/to/private-results.csv`. A nonzero exit means malformed or contradictory claims. A zero exit confirms only structural consistency, **not** a real behavioral pass.
5. Independently inspect the sanitized actual transcript and tools invoked before accepting any PASS. Report counts for each Harness and retain blocked/not-run cases. Do not report percentage success based on executed runs alone without disclosing coverage.

The audit never starts a game-exp experiment, contacts players, writes protected Ledger or tests gameplay. No real-host validation was performed as part of implementing this checker.
