# Opportunity evidence and provenance

Use the strongest evidence actually accessible and relevant to the target players, not merely the easiest web page to quote.

## Source types

- Authorized first-party cohort, search, usage, invitation, return, or purchase data: potentially valuable, but verify metric definition, denominator, access permission, population and transferability to the new game. Do not expose individual-level identifiers or sensitive values.
- App store, Steam, TapTap, public rankings, competitor releases and official disclosures: evidence of existing supply and attention, not automatically of unmet demand or reachable acquisition.
- Communities, forums, short-video platforms, reviews and interviews: useful for language, frustration and behavior hypotheses; watch selection bias, fake reviews and limited availability. Inaccessible WeChat/TapTap/Douyin sources remain unobserved, not magically filled by inference.
- Search and social trends: leading ideas to test; popularity or search volume alone does not establish revenue potential.
- User-provided research: retain exact source/date and clarify whether observation or interpretation.

## Label every material claim

- OBSERVED: actually documented with accessible provenance and time.
- INFERRED: reasoned interpretation with explicit limitations.
- HYPOTHESIS: falsifiable proposition still requiring field evidence.
- UNKNOWN: neither credible source nor test outcome available.

Never cite a secondary summary as though its original dataset were inspected. If one population (e.g. an existing social game platform) is used to hypothesize about another (e.g. external casual-game market), name the transfer assumption. A small convenience sample cannot establish general market size, pay propensity, or product-market fit.

A useful opportunity needs some answer to: player, situation, substitute, unaddressed friction, and plausible access channel. Missing elements may remain unknown; focus next experiment on the one that most affects investment choice.

## Data you can inspect safely

For supplied local CSV/JSON/JSONL review files, `scripts/import_evidence.py` emits **only aggregated topic mentions, explicit vote polarity counts, basic denominators, and source metadata** to a `local-evidence/` path excluded from public Git. This is exploratory keyword analysis, not validated sentiment or unmet-demand detection: keyword matches (including negated phrases) can be wrong, and the sample may be systematically selected. Require original source and sampling details for stronger claims. Do not publish or upload raw reviews, player identities or internal cohorts from the public Skill repository.

For public Steam review retrieval, `scripts/adapters/steam_reviews.py` is an **optional, explicit** and tightly bounded adapter. Do not invoke it without user-authorized external data access; it does not collect Chinese app-store or private platform data. For domestic platforms, use actual official accessible pages or user-authorized exports; an inaccessible platform is `UNKNOWN`, not a cue to bypass access restrictions.

Read `references/china-channels.md` only for China-local decisions, `references/comparable-games.md` for tradeoff comparisons and `references/discovery.md` when research input is absent.
