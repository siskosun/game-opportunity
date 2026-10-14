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
