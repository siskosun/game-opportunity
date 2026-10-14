# P0-A/B implementation notes

## Decisions

- Independent Skill: `game-opportunity` (distinct trigger), not another stage of game-exp.
- One card with three mandatory decision sections; optional context and append-only trial observations.
- Source repository: public `siskosun/game-opportunity`, initialized by the user. Only expressly approved, sanitized opportunity cards may be published here. Confidential research requires a separately authorized private evidence store. A local draft is not remotely persisted.
- Actual H5/Godot build/QA remains owned by specialized Skills. No new PROBE or Manifest schema, protected Ledger writer, experiment states, automatic agent approval, or duplicate long-term logs.
- One active formal game-exp experiment per exploration thread by default. Idea alternatives do not authorize fan-out.
- Use first-party user behavior evidence only if accessible and authorized; never assume platform logs exist or can be transferred into other markets.

## Exclusions

No automated scraping, recruitment, ad spending, fake-door launch, realtime debugging UI, new server, new knowledge graph, or promise of market uplift in P0.

## Integration scope

- game-exp: one optional source-evidence handoff paragraph; no trigger broadening.
- H5: preserve PROBE `probe_card.md` and `probes.jsonl`; accept cited upstream context and distinguish stage-changed hypotheses.
- Godot: accept cited upstream context as non-authoritative brief input.
- Repository-local tests: behavior fixtures are an evaluation plan, not claimed execution.

## Gate before claiming P0 complete

1. Public source repo contains complete Skill sources/tests and excludes sensitive cards; an explicitly approved public-safe card or a private evidence record can be committed and read through the authorized destination.
2. The same card can be read in every intended Harness under its actual permissions.
3. Real prompts run repeatedly on available hosts against expected routing, with differences recorded.
4. 3-5 true project opportunities compared with the pre-written no-exploration baseline.
5. No protected game-exp domain objects change as a side effect of card management.
