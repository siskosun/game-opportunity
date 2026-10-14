---
name: game-opportunity
description: "Research game-market opportunities, unmet player needs, target audiences, alternatives, and acquisition hypotheses; evaluate novel game ideas against potential players; choose the cheapest decisive validation before committing to prototype development. Chinese triggers: 游戏市场机会, 玩家未满足需求, 值得开发的游戏, 最小成本验证. Use for questions like \"what game is worth making\", \"who needs this mechanic\", \"market opportunity\", \"unmet player needs\", and \"how can I cheaply validate this game idea\". Do not use for implementing H5 or Godot games, bug fixing, gameplay tuning, or managing game-exp experiment lifecycle."
---

# Game Opportunity

Help the user decide **what to test next, and why**, not how to generate more prototypes. Output a compact opportunity card in Chinese by default. Two legitimate entries: **demand-driven** (players and unmet needs first) and **creative-driven** (unfamiliar mechanic first). Existing market-demand proof is never mandatory for creative exploration.

## Route before doing work

Read `references/routing.md` when intent overlaps another game Skill. Explicit build/change/debug/delivery requests go to H5 Game Prototype Agent or Godot Prototype Studio. Requests to inspect/review/select/archive a bound experiment go to game-exp. Use this Skill for opportunity discovery, player fit, and choice of a validation method. Do not force this Skill on ordinary new-game builds. For vague "make something like X", default to development; clarify only one material ambiguity. Do not spawn multiple Agents or automatically create repositories or experiments.

## Research and decide

1. Recover the user's existing idea, constraints, player evidence, and prior explicit decisions. Do not repeat known questions. Choose demand-driven or creative-driven. Use available online research and authorized first-party data only when these improve the decision. See `references/evidence.md`.
2. Distinguish sourced observation, inference, assumption, and unknown. Cite actual origin and collection date for material market claims; never fabricate market size, reviews, app ranking, player behavior, or access to private data. Popularity alone is not an entry opportunity; examine substitutes, supply gaps, and plausible player acquisition. Missing evidence remains unknown.
3. Generate alternatives only when they could distinguish a decision. Do not launch parallel projects from conceptual variants. Identify the **single most decision-relevant uncertainty** and the cheapest test capable of resolving it. A concept/intent click is not retention, repeat use, or monetization evidence. See `references/validation.md`.
4. Produce one small card with exactly three mandatory decision sections: `Key uncertainty`, `Cheapest useful validation`, `Continue / adjust / stop conditions`. Optional context may describe players, substitutes, source links, channel access, variants, and cost assumptions. Format it using `templates/opportunity-card.md` with stable `opportunity_id`. Never turn the card into a new Manifest or PROBE schema.
5. Offer one recommended next action with the evidence limitation. No automatic promotion, investment, outreach, repository creation, paid campaigns, participant tests, or gameplay implementation. Read `references/safety.md` before proposing any user-facing research intervention.

## Persist and hand off without duplicate authority

- The public source repository is `siskosun/game-opportunity`. Its `opportunities/` area is for **explicitly approved, public-safe and sanitized** cards only; being able to write to GitHub does NOT authorize public disclosure. Before committing any card or result, confirm the user wants that specific information public, remove confidential business context and participant identifiers, and cite the confirmed remote commit SHA. For internal, user-level or sensitive research, require an independently authorized private evidence location; keep only a non-sensitive pointer in the public card if the user approves. When no appropriate durable destination or publication authorization exists, return `NOT_PERSISTED`, not a guessed URL or an accidental public commit.
- Record validation observations by appending to the final `Validation results` section. Keep sources, actual sample denominators, dates, and observed behavior separate from interpretation. If a trial was not run, record a plan rather than invented findings. `scripts/opportunity_card.py` can create/validate/append card records in a checked-out repo; local operations do not push or grant access by themselves.
- A card is ordinary research, not trusted game-exp Ledger authority. For H5 PROBE and Godot implementation handoff, read `references/handoff.md`. Reuse a frozen hypothesis/stop condition verbatim **only when the question is the same**; otherwise describe the changed next-stage hypothesis and link back to its source. Leave game-exp Manifest, Candidate, review, trusted workflows, human selection, and archive rules untouched.
- For cross-Harness work, cite a stable opportunity ID plus authorized repository/path and remote commit SHA, not a local filesystem path. A private URL is useful only if the receiving Harness has access.

## Boundaries

This Skill does not require a repository or `PROJECT_READY` for a read-only brainstorm. It does require authorized durable storage to claim a saved card. Don't store identifying player interviews, private user-level analytics, secrets, or minors' personal data in GitHub. AI proposes validation designs; humans authorize external testing, disclosures, budgets, publication, and participant contact. Never invent human test outcomes or gameplay enjoyment from automation.

## References

- `references/routing.md`: cross-Skill routing and borderline cases.
- `references/evidence.md`: market evidence, source quality and uncertainty.
- `references/validation.md`: cheap experiments and decision criteria.
- `references/handoff.md`: opportunity -> PROBE/Godot -> game-exp without duplicate hypotheses.
- `references/safety.md`: participant research, advertising, permissions and privacy.
- `templates/opportunity-card.md`: minimal card and append-only result area.
- `scripts/opportunity_card.py`: local optional card creation, validation, result append, search.
