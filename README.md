# Game Opportunity

[English](README.md) | [Simplified Chinese](README.zh-CN.md)

Independent `game-opportunity` Skill for early game market/opportunity exploration, creative-mechanic player fit, and minimum-cost validation planning. This repository is **public**: [siskosun/game-opportunity](https://github.com/siskosun/game-opportunity).

## Scope and status

- Source: `skills/game-opportunity/`; routing, evidence, validation, safety, and handoff guidance are under `references/`.
- Game development remains in H5 Game Prototype Agent or Godot Prototype Studio; trusted experiments, Candidates, Reviews and human choices remain in game-exp. Opportunity research is never a mandatory gate for direct build, patch or bugfix tasks.
- Script and static tests are included. Cross-host behavior evaluations in Cursor, Codex, and ChatGPT remain **NOT RUN** until actually executed.
- No real-player outreach, paid tests, or game-exp lifecycle mutation is performed by this repository.

## Install the Skill

Run from repository root:

```bash
python -m unittest discover -s tests -v
python dev/build_skill_zip.py
```

Import `dist/skill.zip` using the host's supported Skill installation interface. Installing from GitHub does not automatically update a previously installed copy or create a game prototype.

## Opportunity cards and privacy

The public `opportunities/` directory contains a README only. Draft cards named `OPP-*.md` are **gitignored by default** to prevent accidental publication. Use local commands to prepare and validate a card:

```bash
python skills/game-opportunity/scripts/opportunity_card.py new --id OPP-20261014-sample --title "Public-safe example" --directory opportunities
python skills/game-opportunity/scripts/opportunity_card.py validate opportunities/OPP-20261014-sample.md
```

Only after reviewing a particular card for disclosure risk and explicitly choosing to make it public, deliberately stage that sanitized card with `git add -f opportunities/OPP-20261014-sample.md` and commit/push with authorized Git tooling. GitHub connector creates and updates also count as public publication and need the same review. Do not assume public repository write permission authorizes disclosure.

For confidential market work, internal company data, user-level analytics, participant identities or minors, use a separately authorized **private** evidence location. Link to a private record only where recipients have access and the link itself discloses nothing sensitive. If no approved location exists, say `NOT_PERSISTED`; no chat memory or local path is durable across Harnesses.

Cards have three mandatory decision sections: key uncertainty, minimum useful validation, and continue/adjust/stop conditions; an optional context section and append-only result section record verifiable evidence. No PROBE card or Manifest protocol is changed.

## Testing, integration, and evaluation

- `evals/cases.json` / `evals/RUNBOOK.md` are behavior-evaluation fixtures, **not** executed cross-host test results.
- `docs/implementation-plan.md` documents the P0 design and rollout conditions.
- Integrations already merged: [game-exp #53](https://github.com/siskosun/game-exp/pull/53), [H5 #9](https://github.com/siskosun/h5-game-prototype-agent/pull/9), [Godot #17](https://github.com/siskosun/godot-prototype-studio/pull/17).

Run 3-5 real opportunity explorations before claiming market uplift. Track what would have been built without this workflow and whether the earliest decisive evidence changed the investment/validation choice.

## v0.2.0: China-local, no-radar opportunity exploration

The Skill now supports **zero-input discovery** without requiring any game radar, paid analytics or existing repository. China-specific channels (TapTap, mini-games, Chinese Steam players and creator communities) are **optional** and do not impose mobile, casual, 2D, social or ad-funded assumptions on every game.

The research focus is: actual player substitutes and unsuccessful peers; whether a game will be **noticed, voluntarily chosen and deliver the promised outcome**; what happens if the mechanic is quickly copied; and the least costly evidence that could change a decision. For finite single-purchase games, completion, satisfaction or recommendation may matter more than retention.

### Offline review evidence import (no API key or network)

```bash
python skills/game-opportunity/scripts/import_evidence.py --input examples/synthetic-reviews.csv --platform synthetic_example --sampling-notes "Synthetic demo; not player evidence"
```

Supports UTF-8/UTF-8-BOM CSV, JSON and JSONL. Produces **only** exploratory aggregate topic mentions, explicit polarity counts, duplicate/empty counts and provenance in `local-evidence/` (gitignored). No author IDs or review text are exported. Keyword mentions (including negated ones) are not validated pain points or market size; review the underlying authorized data. Existing results are not overwritten.

### Optional bounded public Steam review sampling

```bash
python skills/game-opportunity/scripts/adapters/steam_reviews.py --appid 123456 --language schinese --max-pages 2 --max-reviews 100 --confirm-public-fetch
```

Requires explicit user-approved access to public reviews; defaults to at most 2 pages/100 records (hard limits: 5 pages/500 records), minimum 1-second gap. Stops on 403/429 or other refusal, uses no private credentials, and writes only local aggregate results. The Steam adapter adapts parts of the MIT-licensed [SteamReviewFetch](https://github.com/Seafoodsz/SteamReviewFetch), with author permission and copyright reproduced in [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md). No Chinese-platform scraping or paid data connection is bundled.

Run `python -m unittest discover -s tests -v` and `python dev/build_skill_zip.py`. GitHub CI checks Linux **and Windows**. Static tests and mocked requests do **not** prove cross-host Skill routing or live external API access; those evaluations and the 3–5 real P0-C cases remain separate.

See [LICENSE](LICENSE) and [third-party notices](THIRD_PARTY_NOTICES.md) before redistribution. Public opportunity cards still require explicit per-card approval; private evidence needs an authorized private store.

## v0.3.0: one main Skill, trusted game-exp companions

Game Opportunity is the **user-facing coordinator** from opportunity discovery to optional playable experiment and feedback. **game-exp** remains the exclusive authoritative lifecycle manager; H5 and Godot executors remain responsible for implementation and playtests. There is no mandatory market-research gate for direct development.

For **explicit local** installation in Cursor, Codex or Qoder, clone the public repository and plan before executing:

```bash
git clone https://github.com/siskosun/game-opportunity.git
cd game-opportunity
```

Then:

```bash
python skills/game-opportunity/scripts/install_bundle.py --harness cursor --plan
python skills/game-opportunity/scripts/install_bundle.py --harness cursor --json
python skills/game-opportunity/scripts/install_bundle.py --harness cursor --check --json
```

Use `codex` or `qoder` as appropriate. This runs the **official published-stable game-exp installer**, which also installs/syncs the selected Harness's H5 and Godot companions, then installs game-opportunity. It requires working GitHub connectivity. `--harness all` requires an explicit choice. `--check` is local presence only, not game-exp Doctor; check the official game-exp status/health before experimenting.

**Importing `skill.zip` to ChatGPT web cannot automatically execute installers, install game-exp, or configure a local MCP runtime.** Set up game-exp separately in an authorized supported environment; without it, game-opportunity can still produce read-only research. No public opportunity-card or private user evidence is uploaded automatically. See [full workflow](skills/game-opportunity/references/full-workflow.md).

Use `scripts/handoff_bundle.py` for ordinary non-authoritative research context when a real playable is requested. game-exp's real current project/Manifest/Bind controls all official experiments. After verified observation, `scripts/link_result.py` records operator-reported provenance in the ordinary opportunity card; it does not assert a Review outcome or mutate the protected Ledger.


## v0.4.2: published four-Skill release combination

The validated pinned **published** combination is game-exp **v1.5.3**, H5 **v0.2.4**, and Godot **v1.0.6**. Each pin references an exact Git commit and the installed Skill entrypoint's Git blob identity. This replaces the historical v0.4.1 baseline below. The main Skill itself is released as **v0.4.2**.

For a read-only freshness/integrity check, use `python skills/game-opportunity/scripts/check_bundle.py --harness codex --online --json`. For an explicit installation, review the plan and run `install_bundle.py --harness codex --json`. The GitHub matrix workflow `.github/workflows/pinned-bundle-smoke.yml` installs all four released components in a disposable HOME and checks both local source identities and current published tags, without any game repository, human test, or actual customer environment. A successful check is **not** game-exp Doctor or proof of a game idea's market demand.

## v0.4.1: check the other three Skills before invoking them

Historical v0.4.1 lock (superseded by v0.4.2): [compatibility.lock.json](skills/game-opportunity/compatibility.lock.json). The verified-as-published tags are **game-exp v1.5.2 (stable GitHub Release)**, **H5 v0.2.3 (semver tag)** and **Godot v1.0.5 (semver tag)**. These are version/source pins with static CI evidence, **not** proof of a complete live end-to-end run. Upstream `main` may be ahead of these tags, and game-opportunity itself has not yet been formally released at this point.

Before delegating local gameplay work:

```bash
python skills/game-opportunity/scripts/check_bundle.py --harness cursor --online --json
# Legacy --check is presence-only; --verify performs a read-only file/version check.
python skills/game-opportunity/scripts/install_bundle.py --harness cursor --verify --online --json
```

The result distinguishes `CURRENT`, `UPDATE_AVAILABLE` (new unreviewed upstream tag), `NOT_INSTALLED`, `INCOMPATIBLE` and `UNVERIFIED`. Without `--online`, a pinned match does not prove it is latest. Installation stays an explicit user action; it blocks when latest upstream tags have not yet been reviewed, installs only the locked combination through game-exp's canonical installer, runs a postcheck, and tries to restore the previously installed selected-Harness files on failure. Restore may be incomplete when Windows keeps files locked. No game-exp trusted mutation or automatic update occurs.

A scheduled GitHub Action opens **draft candidate PRs** for newly published upstream versions but does not promote them into the lock or user installations. Run Windows/Linux tests and a real end-to-end pilot before declaring a combination fully certified. See [version-check.md](skills/game-opportunity/references/version-check.md).

## v0.4.0: predeclared player-behavior validation (local only)

This release retains the v0.3 main-Skill, official game-exp bundle installer, and H5/Godot handoff. It adds `skills/game-opportunity/scripts/validation_cycle.py` to connect actual player evidence to a **pre-test question** without inventing a second trusted experiment lifecycle.

First complete an opportunity card. Before a real test, use `validation_cycle.py plan` to freeze a unique-player metric, its actual numerator/denominator definition, population, segment, time window, recruitment limitations and independently justified continue/stop signal bounds. The tool creates a local non-overwritable JSON plan and prints its SHA-256. Preserve that hash in an authorized independent, timestamped private record **before** running the test if pre-registration timing matters; local hash equality alone is not proof of prior timing.

After testing, export **one** anonymized aggregated CSV or JSON row and run `validation_cycle.py assess --plan ... --input ... --expected-plan-sha256 ...`. Mismatched source snapshots, population/segment/window, metric, unit, or unknown/raw player-level columns are rejected. An observed percentage is not a market forecast, population estimate, causal effect or product verdict. No pretest digest means a descriptive-only result; an insufficient denominator is inconclusive. All outcomes remain ordinary operator-reported research, never game-exp Review, promotion, selection or rejection.

Use `python skills/game-opportunity/scripts/validation_cycle.py plan --help` and the corresponding `assess --help` for CLI flags. See [validation-cycle.md](skills/game-opportunity/references/validation-cycle.md) and the **fully synthetic** Chinese-CSV example [synthetic-behavior-aggregate.csv](examples/synthetic-behavior-aggregate.csv). All real plans/aggregates default to ignored `local-evidence/`; no scraper, login, remote upload, human recruitment or spending occurs. Use `link_result.py` to append sourced findings to a card after actual observation. No prerequisite market research is imposed on direct development requests.

Code-level checks use synthetic data. Cross-Harness behavioral routing, live platform data access and actual human player outcomes remain separate acceptance work.
