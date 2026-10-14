# v0.4.1 tested-version bundle evaluation (REQUIRES REAL HOST RUN)

This file defines intended evaluations only; passing mocked Python tests is **not** evidence that automatic routing or authorized game-exp execution worked in real Cursor/Codex/Qoder/ChatGPT environments.

1. In an isolated user-controlled local HOME, install the **released lock pins** explicitly on Cursor, Codex and Qoder. Capture `check_bundle.py --harness <host> --online --json` without secrets. Expected `CURRENT` only if GitHub tags remain unchanged and installed code digests match; then separately run actual game-exp Doctor/capabilities against a permitted test repository.
2. Record the exact installed game-opportunity source revision and game-exp/H5/Godot versions; compare with lock. Repeat after tampering only with a disposable Skill copy; checker must refuse modified hash or unsupported tag/version.
3. Publish a **test** upstream release/tag only in an authorized disposable mirror when available; confirm the watcher produces a draft proposal and **never** auto-installs or promotes the lock. Do not create fake releases in production upstream repositories solely for this check.
4. Fail partway through a disposable bundle upgrade with an intentionally broken main Skill target, and verify previous selected-Harness game-exp runtime, MCP config and all four Skill files are restored. Files held open on Windows may legitimately produce `ROLLBACK_INCOMPLETE`; this is not a PASS.
5. Enter an already-authorized game-exp project. Verify an opportunity-card handoff never mutates a strict Manifest, and a positive v0.4 player aggregate cannot automatically trigger Review PASS, PROMISING, SELECTED or REJECTED.
6. In ChatGPT web, confirm importing one Skill ZIP does not claim to run local installers, install other Skills, or establish a game-exp MCP environment. Record inability to check local versions as `UNVERIFIED`.

Use eval cases prefixed `v041-` in `evals/cases.json` across available Hosts. Report a concrete observation for each, including any failures and unsupported capabilities. Do not substitute a static keyword test or CI pass for actual behavioral evidence.
