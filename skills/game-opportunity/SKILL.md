---
name: game-opportunity
description: "Lead an end-to-end game opportunity-to-playable-to-evidence workflow using game-exp as the trusted experiment controller; explore promising game opportunities and player needs in China or global markets, even with no game radar or existing data; compare games and substitutes, assess why players will notice, choose and value a game under rapid imitation, and design the cheapest decisive market or gameplay validation. Use for 游戏市场机会, 游戏选题, 玩家需求, 中国游戏市场, 玩家选择, 最小成本验证, 游戏竞品分析, 游戏创意快速复制. Do not use for direct H5/Godot implementation, bug fixing, gameplay tuning, or game-exp lifecycle operations."
---

# Game Opportunity

Serve as the **main user-facing Skill** for complete game exploration: idea / evidence / cheap validation / optional playable / actual player result / next decision. Delegate trusted experiment lifecycle to game-exp and source implementation to H5/Godot; never create a shadow control plane. Help a developer determine **what to test, what player choice it would change, and why**. Prioritize evidence and low-cost decisions over idea volume or AI attractiveness scores. Default to concise Chinese. Support demand-driven and creative-driven exploration without requiring prior market proof for original mechanics.

## Route before doing work

Read `references/full-workflow.md` for complete idea-to-playable journeys and `references/routing.md` for intent clashes. Direct build/change/debug/delivery without broader opportunity intent goes to H5 Game Prototype Agent or Godot Prototype Studio. Requests to inspect/review/select/archive a bound experiment go to game-exp. Use this Skill for opportunity discovery, player fit, and choice of a validation method. Do not force this Skill on ordinary new-game builds. For vague "make something like X", default to development; clarify only one material ambiguity. Do not spawn multiple Agents or automatically create repositories or experiments.

## Research and decide

1. Recover stated constraints, current player evidence and previous decisions; do not ask again. Choose demand-driven or creative-driven, with no default platform, genre, monetization, employer, short-session rule or radar dependency. For no-input discovery and source selection read `references/discovery.md`; if targeting mainland China read `references/china-channels.md`.
2. Contrast realistic direct/indirect player substitutes, ordinary or unsuccessful comparables and quality aspirations. Use `references/comparable-games.md`. Mark `OBSERVED / INFERRED / HYPOTHESIS / UNKNOWN`, actual sources and dates; missing data stays unknown. Check whether the proposed game has a plausible player-discovery route instead of equating trending products with reachable demand.
3. Answer three **separate** questions when decision-relevant: why players will **notice** it, **choose** it over an alternative, and obtain the promised **experience outcome** (repeat/complete/recommend as appropriate). Examine a rapid-copy scenario without mandating a permanent moat; see `references/player-choice.md`. Do not manufacture numeric market scores or claim real-world player behavior from AI judgment.
4. Identify one pivotal uncertainty and the cheapest **credible** test that could change investment. Concept interest is not active choice, replay or monetization; user-supplied CSV/JSON summaries are selected samples, not census estimates. See `references/validation.md` and `references/evidence.md`. Alternatives remain proposals, never auto-spawn multiple experiments.
5. Produce a brief opportunity card with the same **three** mandatory decision sections: `Key uncertainty`, `Cheapest useful validation`, `Continue / adjust / stop conditions`, using `templates/opportunity-card.md` and an opportunity ID. All new comparisons, attention/choice/experience notes and copy scenarios stay **optional context**, not a new required schema.
6. Recommend one next action with its evidence limitations. No automatic publication, repository creation, spending, human contact, promotion, or gameplay implementation. For user-facing interventions consult `references/safety.md`.

## Install the full local bundle on user request only

A Skill ZIP upload never installs game-exp by itself. For explicit **local** bundle installation in Cursor, Codex or Qoder, read `references/full-workflow.md` and guide the user through `scripts/install_bundle.py --harness <cursor|codex|qoder> --plan` and then the authorized install command. The launcher invokes the **official game-exp stable Release installer** (which itself synchronizes H5 and Godot Skills in the selected Harness), then installs this Skill. Never execute installers without user instruction; do not silently use game-exp main or downgrade. ChatGPT web cannot run local installers, automatically install additional Skills, or supply a trusted MCP runtime; require separate supported user installation/connection and state the limitation. Check actual game-exp status/version/Doctor before a bound experiment, not merely file presence.

## Full workflow handoff and feedback

For a user who wants the entire route from idea to game, keep the opportunity card optional when already building. When the user decides to build, choose the same-question vs new-stage hypothesis as `references/handoff.md` describes; optionally generate a **non-authoritative** JSON with `scripts/handoff_bundle.py`. The research bundle is not a game-exp Manifest. For managed work, use game-exp's project-create/status/experiment-template/Bind/handoff and official human gates; never create fake experiment identities or add opportunity IDs to its strict Manifest. When independently verified player evidence exists, link it back to the ordinary card with `scripts/link_result.py` and clear limitations, without setting game-exp states. See `references/full-workflow.md` for the full route and failure cases.

## Close the human-behavior evidence loop when relevant

Before a genuine human test, optionally use `scripts/validation_cycle.py plan` to record a single player-visible metric, exact unique-player numerator/denominator, population/segment/time window, sampling limitations and user-justified decision bounds; retain its digest from **before** observation. After the test, `assess` accepts exactly one matching anonymized CSV/JSON aggregate, never pools conflicting snapshots or treats click intention as retention. Without a pretest hash or adequate denominator, output is explicitly inconclusive/descriptive only. Hash equality cannot attest to pretest timing. Never infer human preference from H5/Godot machine checks or AI opinion. See `references/validation-cycle.md`. Every result is ordinary operator-reported evidence, **not** a game-exp Review or automatic game investment verdict.

## Persist and hand off without duplicate authority

- The public source repository is `siskosun/game-opportunity`. Its `opportunities/` area is for **explicitly approved, public-safe and sanitized** cards only; being able to write to GitHub does NOT authorize public disclosure. Before committing any card or result, confirm the user wants that specific information public, remove confidential business context and participant identifiers, and cite the confirmed remote commit SHA. For internal, user-level or sensitive research, require an independently authorized private evidence location; keep only a non-sensitive pointer in the public card if the user approves. When no appropriate durable destination or publication authorization exists, return `NOT_PERSISTED`, not a guessed URL or an accidental public commit.
- Record validation observations by appending to the final `Validation results` section. Keep sources, actual sample denominators, dates, and observed behavior separate from interpretation. If a trial was not run, record a plan rather than invented findings. `scripts/opportunity_card.py` can create/validate/append card records in a checked-out repo; local operations do not push or grant access by themselves.
- A card is ordinary research, not trusted game-exp Ledger authority. For H5 PROBE and Godot implementation handoff, read `references/handoff.md`. Reuse a frozen hypothesis/stop condition verbatim **only when the question is the same**; otherwise describe the changed next-stage hypothesis and link back to its source. Leave game-exp Manifest, Candidate, review, trusted workflows, human selection, and archive rules untouched.
- For cross-Harness work, cite a stable opportunity ID plus authorized repository/path and remote commit SHA, not a local filesystem path. A private URL is useful only if the receiving Harness has access.

## Boundaries

This Skill does not require a repository or `PROJECT_READY` for a read-only brainstorm. It does require authorized durable storage to claim a saved card. Don't store identifying player interviews, private user-level analytics, secrets, or minors' personal data in GitHub. AI proposes validation designs; humans authorize external testing, disclosures, budgets, publication, and participant contact. Never invent human test outcomes or gameplay enjoyment from automation.

## References

- `references/routing.md`: cross-Skill routing and borderline cases.
- `references/full-workflow.md`: main-skill orchestration, bundle installation, authoritative experiment handling and feedback.
- `references/evidence.md`: market evidence, source quality and uncertainty.
- `references/validation.md`: cheap experiments and decision criteria.
- `references/handoff.md`: opportunity -> PROBE/Godot -> game-exp without duplicate hypotheses.
- `references/safety.md`: participant research, advertising, permissions and privacy.
- `templates/opportunity-card.md`: minimal card and append-only result area.
- `references/discovery.md`: independent zero-data discovery and optional source adapters.
- `references/comparable-games.md`: direct/indirect/unsuccessful comparisons; no uncalibrated revenue multipliers.
- `references/player-choice.md`: attention, voluntary choice, experience outcomes and imitation pressure.
- `references/china-channels.md`: optional mainland-China distribution/test paths, not a gate for other users.
- `scripts/import_evidence.py`: offline UTF-8 CSV/JSON exploratory review-theme aggregation; no raw text export.
- `scripts/adapters/steam_reviews.py`: opt-in, bounded Steam review sampling; do not run automatically.
- `THIRD_PARTY_NOTICES.md`: source and copyright/license attribution for adapted code.
- `scripts/opportunity_card.py`: local optional card creation, validation, result append, search.
- `scripts/install_bundle.py`: explicit local installation of this Skill plus official stable game-exp/H5/Godot components.
- `scripts/handoff_bundle.py`: read-only opportunity hypothesis handoff; never a Manifest or lifecycle action.
- `scripts/link_result.py`: append operator-reported provenance after actual observation; not a trusted Review.
- `references/validation-cycle.md`: optional preregistered human-behavior measurement, exact cohort/denominator, pretest digest and non-authoritative result comparison.
- `scripts/validation_cycle.py`: offline local-only plan/assess of one anonymized aggregate; rejects conflicting snapshots and raw player-level data.
