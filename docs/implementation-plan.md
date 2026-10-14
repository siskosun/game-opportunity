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

## v0.3.0: Main Skill and companion install orchestration

- `game-opportunity` is the user-facing orchestrator for the complete idea->evidence->optional prototype->human choice journey. Direct H5/Godot development still bypasses opportunity research; protected experiment management still belongs only to game-exp.
- For explicit local Cursor/Codex/Qoder install, run `scripts/install_bundle.py`; its stable game-exp Release source and **official installer** own the MCP/runtime/config and companion H5/Godot sync. The bundle installer then installs the main Skill into the same selected Harness. Default single-Harness scope; explicit `all` only.
- Importing Skill ZIP to ChatGPT web never invokes a local installer or adds a second Skill automatically; manual authorization is required.
- `scripts/handoff_bundle.py` emits untrusted read-only provenance with card hash and same-vs-new-stage question, never a game-exp Manifest or protected Ledger event. `scripts/link_result.py` appends operator-reported result provenance, never Review or selection.
- Stable release may predate `main` handoff documentation. game-opportunity's full-workflow guide bridges ordinary research context, with a strict official Manifest template and game-exp version/Doctor check at each managed experiment.
- CI/unit tests cover offline plan, blocked install, host isolation, malicious archive paths, read-only research handoff, reported remote source status, changed-stage requirement, and result evidence append. Host behavior evaluation / a live full workflow is still required.

## v0.4.0 player-behavior validation scope

- Add one optional local preregistration + one-cohort aggregate comparison loop; do not alter game-exp, H5 PROBE, Godot scope, or the opportunity card's required headings.
- Preserve metric definitions, eligible unique-player denominator, sample method, exact window and lower/upper observation thresholds declared **before** the test. A saved plan SHA alone cannot prove a pretest timestamp; mark that as unverified.
- Reject mixed snapshots, alternative cohorts or time windows, extra raw-data/PII fields, fractional counts, numerator > denominator, and sample insufficiency. Do not average conflicting evidence or fabricate participant data.
- Emit bounded, non-authoritative signals only. No implicit game-exp human Review, lifecycle promotion, selection or rejection; no product ROI predictions. Output local private-by-default under `local-evidence/`.
- Add synthetic examples, Chinese CSV aliases, offline tests and cross-host evaluation cases. Test real player/recruitment and installation separately with explicit authorization.
