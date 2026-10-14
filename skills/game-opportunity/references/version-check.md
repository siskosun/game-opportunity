# Four-Skill version and compatibility gate (v0.4.1)

Use before **delegating** local work to game-exp/H5/Godot or opening an actual bound experiment. Do not force remote version checking on ordinary research, commentary or an explicit low-risk read-only question. This is not a hidden execution hook: Skill ZIP import alone cannot force another program to run. Local Python execution permission is required.

## What is actually checked

- `compatibility.lock.json` pins the three **already published** upstream versions to an immutable expected tag commit SHA and the Git blob SHA-1 of the exact Skill entrypoint. game-exp must be from a non-prerelease GitHub **Release**; H5/Godot use the latest published **semver tag**, matching game-exp's existing companion installer. Do not infer release availability from `main`.
- `scripts/check_bundle.py --harness cursor --online --json` checks the current selected Harness's installed main Skill and three companions, version markers, pinned Skill-entrypoint Git blob digests and game-exp stable install provenance. For main Skill installs performed by the bundle installer, a per-file SHA-256 manifest detects local drift. These digests are **file integrity checks, not tamper-proof authentication of the user's machine**. Do not equate them with end-to-end executable-code attestation or trust in all files.
- Remote check validates that pinned tags still resolve to expected commit SHAs and queries the latest upstream **published version**. GitHub rate limits, failed network access, truncated results or absent metadata return `UNVERIFIED`, not a claim of latest.
- The installed and pinned versions can be current even if a newer upstream version is **not yet vetted**. In this case return `UPDATE_AVAILABLE`, continue only with the installed pinned combination if its local checks passed, and explain that the newer version is not approved for automatic use. The reported `assurance` is **STATIC_CONTRACT_CI_ONLY_NOT_END_TO_END_CERTIFIED**.
- The GitHub `main` of other Skills may be ahead of their latest Release/tag. New source on `main` is **not** proof that installed clients are updated. The main Skill itself still needs a published Release before claiming a fully stable four-Skill distribution.

## Commands (explicit local Harness)

```powershell
python skills/game-opportunity/scripts/install_bundle.py --harness cursor --plan
python skills/game-opportunity/scripts/check_bundle.py --harness cursor --json
python skills/game-opportunity/scripts/check_bundle.py --harness cursor --online --json
# Only after user authorizes installation/upgrade:
python skills/game-opportunity/scripts/install_bundle.py --harness cursor --json
python skills/game-opportunity/scripts/install_bundle.py --harness cursor --verify --online --json
```

Replace `cursor` with `codex` or `qoder`. `--harness all` is only for an **explicit** all-Harness request. Legacy `--check` is presence-only; use `--verify` for hashes and versions. Before game-exp mutations also call official `game_exp_status`, capabilities/version and Doctor for the actual repository, and respect its human lifecycle gate and current Manifest template.

## Interpretation and stop conditions

| Status | Meaning | Action |
|---|---|---|
| `CURRENT` | Installed files match a published pinned baseline; remote pins are still latest published | Continue only after actual game-exp Doctor/capability checks |
| `PIN_MATCH_OFFLINE` | Installed pinned files match locally, latest remote unknown | Never call it latest; obtain an online check when freshness matters |
| `UPDATE_AVAILABLE` | Local pinned combination is consistent but upstream has a newer, **untested** release/tag | Suggest compatibility review; do **not** auto-switch |
| `NOT_INSTALLED` | Missing one or more components | Offer explicit installation; read-only opportunity work may continue |
| `INCOMPATIBLE` | Wrong version/digest or a remote pinned tag moved | Halt dependent workflow and investigate |
| `UNVERIFIED` | Incomplete provenance, incompatible host support or GitHub unavailable | Do not claim compatibility; ask for verification/authorization before trusted mutations |

A reported human choice, successful local hash or a healthy MCP process is not a game-exp Review PASS. A script cannot guarantee its own invocation in every ChatGPT/Cursor/Codex interaction; users must use a trusted launcher or host policy for a mandatory startup check.

## Bundle installation and recovery

The authorized installer fetches published stable game-exp source, asks the **canonical game-exp installer** to install runtime/MCP/H5/Godot for the selected Harness, installs the main Skill and then independently rechecks all four. Before writing, it refuses an unreviewed newer upstream release/tag or any changed tag. It snapshots the selected Harness's managed Skills, runtime and MCP config; on a failure it attempts to restore all managed targets. Successful restoration reports `ROLLED_BACK`; file locks or storage errors can cause `ROLLBACK_INCOMPLETE`, which requires manual recovery. Nothing claims a perfectly atomic filesystem transaction under all Windows file-lock conditions. It does not change user repositories, research records, private cards or another Harness.

## Automated watch and publication

The scheduled `.github/workflows/upstream-version-watch.yml` detects newly published versions and produces a **draft candidate PR** under `docs/upstream-candidate.json`; this is **not** an updated compatibility lock or certified result. A maintainer must review exact tags/commits, run full cross-Skill tests on Windows and Ubuntu (and live install/Doctor smoke where supported), and approve an independent lock/Release change. GitHub Actions permission to open PRs is repository-configurable; if unavailable, the workflow reports a blocker rather than claiming success.

A main-branch merge does not publish a GitHub Release and cannot update existing installations. ChatGPT web uploads cannot install other Skills, run this local checker or silently set up game-exp MCP. Report this limitation clearly and use approved manual installation/connection.
