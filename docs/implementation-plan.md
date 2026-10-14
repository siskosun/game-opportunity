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

## v0.2.0 implementation scope (China-local + no radar)

- No-radar source discovery, direct/indirect/ordinary/failure peer comparison and explicit player attention/choice/outcome are opt-in research methods, not new lifecycle steps.
- Domestic platform guide is an **optional route** when targeting mainland Chinese players. No default audience, genre, device, session length, distribution channel or employer filter.
- Imitation-speed pressure is a scenario to test, not an AI market score or a permanent defensibility requirement.
- Offline UTF-8 CSV/JSON/JSONL reviews produce only exploratory aggregate keyword mentions and denominators in gitignored local-evidence/. Keyword hits are not confirmed unmet needs; no access to private platform data or real outreach.
- `adapters/steam_reviews.py` is only for explicit, capped, public Steam requests. Reviewed portions of SteamReviewFetch are adapted under MIT with a complete THIRD_PARTY_NOTICES.md, and licenses are included inside the importable Skill ZIP.
- A successful source/CI test does not imply live Steam connectivity or correct routing on every host. Keep P0-C real-case evidence separate.

## Acceptance check

- Zero-radar / no-network / Chinese indie / premium single-run / copycat / Chinese platform access-blocked behavior cases should not force social or mobile assumptions.
- Unit tests cover encoding, dedup, no-raw-export, empty/invalid input, output overwrite denial, Steam bounded pagination and explicit network consent.
- Linux and Windows CI, ZIP validator/CRC, source Git comparison, public repo privacy boundary and per-license credit must all pass before merge.
