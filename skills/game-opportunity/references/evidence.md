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

## Independence, lineage and recency of supporting signals

Before saying "several sources independently support this opportunity", trace each consequential claim back toward its original observation or dataset:

1. **Origin:** identify the earliest inspectable player action, first-party measurement, author statement or primary policy text. Label a retold news article, influencer clip or AI summary as a derivative unless its independent measurement is demonstrated.
2. **Shared underlying evidence:** distinguish separate websites from separate datasets, and separate posts from separate players. Syndicated articles, reposted clips, copied press releases, one creator's cross-posted audience, and two estimates fed by the same platform data do **not** constitute independent replications merely because URLs/domains differ.
3. **Sample and denominator:** preserve platform, target population, time window, opt-in/recruitment mechanism, units and access bias. Two genuinely different communities can still overlap materially; mark independence `UNKNOWN` when participants or vendor inputs cannot be resolved. Do not add view counts, wishes, comments and purchases together.
4. **Original dates and current applicability:** distinguish event date from publication/scrape date, official effective date from announcement date, and current rule from historical rule. If a claimed policy or numerical threshold cannot be checked from a relevant official/current source, keep it `UNVERIFIED` and plan an appropriate check rather than turning it into a go/no-go rule.
5. **Conflict handling:** if estimates materially disagree, show their ranges/methods/uncertainty; do not average them into false precision. Repeated testimony is evidence that language circulates, not automatically that unmet demand or reachable revenue grew.

Optional context may record `evidence_dependency`: original source -> derivative(s), any suspected shared data/participants, the verification gap and date checked. When origin cannot be inspected, quote only what the secondary source actually supports. One strong verified behavioral signal can be more decision-relevant than many redundant mentions. No universal "three independent channels", keyword count, tag density, wishlist count or 15% conversion hard gate is permitted without a population-specific justification.

## Data you can inspect safely

For supplied local CSV/JSON/JSONL review files, `scripts/import_evidence.py` emits **only aggregated topic mentions, explicit vote polarity counts, basic denominators, and source metadata** to a `local-evidence/` path excluded from public Git. This is exploratory keyword analysis, not validated sentiment or unmet-demand detection: keyword matches (including negated phrases) can be wrong, and the sample may be systematically selected. Require original source and sampling details for stronger claims. Do not publish or upload raw reviews, player identities or internal cohorts from the public Skill repository.

For public Steam review retrieval, `scripts/adapters/steam_reviews.py` is an **optional, explicit** and tightly bounded adapter. Do not invoke it without user-authorized external data access; it does not collect Chinese app-store or private platform data. For domestic platforms, use actual official accessible pages or user-authorized exports; an inaccessible platform is `UNKNOWN`, not a cue to bypass access restrictions.

Read `references/china-channels.md` only for China-local decisions, `references/comparable-games.md` for tradeoff comparisons and `references/discovery.md` when research input is absent.
