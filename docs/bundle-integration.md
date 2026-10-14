# game-opportunity v0.4.1 main-Skill integration and version policy

Main intent routing and delegated lifecycle are defined in `skills/game-opportunity/references/full-workflow.md`.

## Compatibility baseline

- game-opportunity main Skill can be imported on its own for read-only research.
- Local bundle install is **explicit**, targets Cursor, Codex or Qoder, and uses the game-exp canonical **stable Release** installer; this also synchronizes H5/Godot Skills to that one Harness. No game-exp source is copied or vendored.
- ChatGPT web Skill upload does **not** run a script or import a second Skill. Provide manual game-exp installation/connection instructions instead of claiming automatic installation.
- The game-exp installer's version/Doctor/preflight and all human gates remain mandatory. Its official stable release can lag its `main` documentation; the opportunity Skill carries the bridging ordinary research context.
- A local card/result is **NOT_PERSISTED** cross-Harness until an authorized durable store and exact version are actually verified. The public source repository is not a default place to upload user data.
- Bundle installer `--plan` and legacy `--check` are offline. `--check` proves presence only; `--verify` and standalone `check_bundle.py` check locally installed pins/digests, with optional `--online` published-version freshness. Neither replaces official game-exp Doctor or cross-host behavioral tests.
- Published game-exp and H5/Godot semver tags are explicitly pinned in the main Skill's `compatibility.lock.json`. A newer upstream release means a candidate for review, never an implicit update. The watch workflow may open a **draft candidate PR**, not update the lock itself.
- Installation snapshots the selected Harness's managed targets and tries whole-bundle rollback. `ROLLBACK_INCOMPLETE` is an explicit failure to be resolved manually. ChatGPT web Skill import still cannot run local installation.

## No schema change

Do not put opportunity-specific fields in game-exp's strict Manifest, protected Ledger or Evaluation Profile. `handoff_bundle.py` is not a Manifest and is never sent automatically to a trusted mutation tool. Convert meaningful player-facing hypotheses and criteria using the **current game-exp experiment-template** and explicit user confirmation, with distinct market-interest and gameplay-experience stages.

## Human gates

Real user authorizes any new repository, visibility, test outreach or cost. Human Review/PROMISING/SELECTED/REJECTED/ABANDONED retain the exact game-exp rules. A research STOP is not an experiment REJECTED; H5 READY_FOR_PLAYTEST is not Review PASS.

## Minimal cross-Harness pilot

1. No game-exp / no repo: opportunity research succeeds and reports NOT_PERSISTED when appropriate.
2. Direct existing H5 bugfix: routes to H5 without opportunity gate.
3. User chooses managed H5 experiment: official project-create and PROJECT_READY; same vs new hypothesis explicit; source pinned and evaluated; Candidate/Review requires human.
4. A new Candidate from revision invalidates old current Review and evidence links retain SHA.
5. Actual result is appended with source identity/denominator/limits, not treated as a trusted decision. Re-check authoritative game-exp state.
6. Run across enabled local Harnesses plus ChatGPT web separately. Not passing Python unit tests does not prove these pilots happened.
