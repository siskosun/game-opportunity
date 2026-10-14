# Main Skill orchestration: idea -> evidence -> game-exp -> playable -> learning

This is the **user-facing main Skill** for an end-to-end exploration when the user asks for a complete game-development journey. game-exp remains the authoritative experiment control plane and its existing Skill/tools must be used for all bound experiments. Do not make `game-opportunity` a shadow Ledger, Manifest writer, or generic game editor.

## Entry routing: explicit intent wins

| Intent | Route | Can skip upstream research? |
|---|---|---|
| "What game should we make?", "从找方向到做出可玩版" | game-opportunity is the user-facing coordinator | Yes; ask only material decisions |
| One concept/competitor/target player investigation | game-opportunity research | Yes, no repo required |
| "Build this H5 game now" without a managed experiment | H5 executor directly, or game-exp project-create if user requests **managed** lifecycle | Yes |
| "Start a tracked experiment" / select / archive / Review | game-exp immediately using its actual MCP/CLI/GitHub Bridge | Yes |
| Existing Godot/H5 bugfix or tuning | corresponding executor; if already bound, honor game-exp revision/work claims | Yes |

## 0. Capability and version handshake

1. Before any delegated **local** game-exp/H5/Godot action, when shell execution is available, run `scripts/check_bundle.py --harness <name> --online --json` to compare installed files with `compatibility.lock.json` and published tags. `CURRENT` is **pin-match only**, not game-exp Doctor. `UPDATE_AVAILABLE` means a newer upstream Release/tag is untested; keep the pinned version, do not upgrade without compatibility review. `INCOMPATIBLE`/`UNVERIFIED` must be reported, not silently ignored. Pure opportunity research proceeds without this gate. Read `references/version-check.md` for the exact state meanings. This instruction is not an enforceable Skill-load hook.
2. If the user explicitly requests local installation or update, offer `scripts/install_bundle.py` instructions and obtain authorization before execution. **Skill import does not execute that script.** The canonical game-exp stable installer also syncs H5 and Godot Skills in the selected Harness.
2. In Cursor/Codex/Qoder, invoke `python <game-opportunity-skill>/scripts/install_bundle.py --harness <name> --plan` for an offline read-only target plan. Then run without `--plan` only on explicit user installation instruction. Prefer the official stable Release by default; never silently run game-exp `main` or downgrade. Check the game-exp `version_state` and Doctor through the official interfaces before bound mutations.
3. On ChatGPT web, Skill upload **cannot** auto-install another Skill, runtime, GitHub MCP, H5 or Godot. Ask the user to install/authorize game-exp separately in the supported UI/connected environment. When unavailable, continue read-only research and report the specific blocker; do not fake installed capability.
4. Do not update other Harnesses unless the user explicitly asks for `--harness all`. Do not auto-change target repository visibility or publish research.

## 1. Discover / compare / choose what deserves testing

Recover existing context and select a demand-first or creative-first path. Use the documented no-radar discovery, comparable-games, China-channel and player-choice research. Avoid mandatory market research on direct build requests. Produce one opportunity card with key uncertainty, cheapest credible validation, and continue/adjust/stop conditions. Source the facts and label unknowns. Keep the card local or in an authorized private evidence location; this public code repository is not a default evidence destination.

## 2. Validate cheaply BEFORE project creation, when appropriate

If interviews, concept comparison, messaging or transparent intent tests can answer the decision, propose them without a game-exp project. Actual recruitment, disclosure, publication and spending always require human authorization. A market exploration STOP is **not** game-exp REJECTED; no experiment exists yet. If evidence changes the next question, record that change explicitly.

## 3. Handoff to an actual playable when human decides to build

Before doing anything irreversible, distinguish:

- **same question**: exact player claim, population and failure condition still apply; preserve its wording, and flag the operator's confirmation;
- **new stage**: market interest/target-audience signal becomes a new mechanic/experience hypothesis, with a distinct kill criterion and a written reason;
- **unproven source**: local file, chat output or reported SHA is not remotely verified. `NOT_PERSISTED` until stored and read from an authorized destination.

The optional `scripts/handoff_bundle.py` emits a **read-only JSON research handoff**, not a Manifest, Ledger mutation or approval. It contains card SHA256, opportunity ID, hypothesis relation, proposed question, source status and target engine. Remote path/SHA are *reported* unless independently fetched and verified. The target engine's existing PROBE or Godot brief remains authoritative for implementation.

If an actual game-exp-managed project is requested:

1. Start with `game_exp_status`, repository/project Doctor and protocol/installed version handshake. If the repository does not exist, ask the required stack/visibility/irreversible decisions and invoke **game-exp's** `game_exp_project_create` / CLI only if authorized; its default is a **public** repo, so never silently copy confidential opportunity data into it. If project-create is unavailable, report the specific capability gap.
2. Obtain `PROJECT_READY`; never assume project-init can be skipped. Resolve the real GitHub Issue and parent SHA.
3. Request current `game_exp_experiment_template` (recommended Manifest schema depends on project policy), then translate the handoff hypothesis/success/kill criteria **only** if they are genuinely suitable for the playable test. Commercial feasibility stop rules are not automatically gameplay kill criteria. Confirm material blocking decisions with the human.
4. game-exp Bind/Initialize through its native trusted tool, authorized CLI, or canonical Issue Bridge. Do **not** add `opportunity_id`, card hash or an extra custom field to protected Manifest. Keep evidence citation in normal brief/conversation or project scope, not as protected authority.
5. Use game-exp's prototype handoff and existing selected H5/Godot Skill for implementation. H5 PROBE freezes its own `probe_card.md`; if a PROBE was run outside a game-exp project, do not fabricate its integration identity. The specialized executor owns build, playability, QA and human playtest preparations.

## 4. Review, iterate, choose (game-exp owns every gate)

game-exp's protected Ledger is the single authority for bound-experiment state. Confirm exact Candidate/source SHA and evidence portability. `READY_FOR_PLAYTEST` is machine evidence, **not** a human PASS. Let the human actually play and provide Review PASS/FAIL. PROMISING and SELECTED are separate explicit human decisions. A new build/Candidate invalidates any old current Review. Ordinary tuning or bugfixes remain **same experiment revisions**, not silent new experiments. Follow the trusted Rehearsal, Integration, Archive and recovery workflow. Never create replacement operation ids to dodge `UNKNOWN`.

## 5. Return observation to opportunity without reversing authority

After real evidence exists, record one dated observation in the ordinary card's `验证结果` section using `opportunity_card.py append-result` or `scripts/link_result.py`, including:

- observed behavior and relevant denominator/window;
- source, privacy/portability status and exact artifact or Candidate source SHA (when independently known);
- PROBE/EXP/Candidate identity only if actually observed;
- limitations and the next uncertainty.

`link_result.py` only records **operator-reported** references and cannot verify trusted Ledger or infer a human Review. A research interpretation like "stop testing this acquisition channel" cannot submit game-exp REJECTED/ABANDONED. Re-enter game-exp for authoritative state and actual human choices. Never claim cross-Harness persistence from a local-only card.

## 6. Failure paths and boundaries

- game-exp not installed/authorized: read-only opportunity work continues. Provide install instructions; never simulate mutation.
- game-exp install fails: main Skill installer stops before installing itself; canonical game-exp rollback semantics apply. If the opportunity stage or postcheck fails after game-exp success, attempt whole-selected-Harness restore and report `ROLLED_BACK` or `ROLLBACK_INCOMPLETE` (for locked files or restoration errors). Do not claim perfectly atomic rollback on every operating system.
- Rate limited, Chinese platforms inaccessible, no radar: label `UNKNOWN` and work from authorized supplied evidence; do not bypass access controls.
- No clear real-world testing result: record a proposed plan, not an observation.
- Multiple ideas: comparison at hypothesis level, sequential experiments unless user explicitly approves parallel projects.
- Cross-Harness runtime: only capability availability and exact version can justify claims about actions. Local-path-only evidence is non-portable.

## Minimal human-readable completion

Summarize the player question, evidence quality, next cheapest test, actual playable/Candidate link if verified, and the **next user-owned decision**. Do not expose internal Ledger terms unless the user needs diagnosis.
