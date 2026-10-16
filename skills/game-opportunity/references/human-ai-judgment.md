# Optional human-AI judgment loop (not another Review gate)

Use only when a consequential opportunity decision could benefit from a distinct developer experience hypothesis, an actual human/AI disagreement, or a bounded exception for a novel mechanic. Do not add a judgment procedure to routine prototype coding, reversible low-cost decisions, ordinary market research, or users who decline it. The objective is to create **decision-changing information**, not human sign-offs, higher rejection rates, or model/human consensus scores.

## Capture a human judgment before AI anchoring, when possible

When it is genuinely consequential, ask **at most one short question** before presenting an AI recommendation: what concrete player behavior does the developer expect, and what would they do next without the AI? Reuse the user's actual earlier statement; do not request it again. If unavailable, proceed without a baseline. The developer is free to reserve a small, explicitly bounded exploration exception for an original mechanic with no known market-demand evidence.

Record the distinction explicitly:
- pre_ai_reported: the user reports a view before seeing the present AI recommendation; this is not independently certified.
- post_ai: the person has already seen the recommendation and may be anchored.
- unknown: exposure cannot be reconstructed.
- unavailable: no human baseline; never fill it with an AI-authored guess.

**Important:** a normal single-context AI sees previous human utterances. Capturing the human position first reduces one-sided AI anchoring but does NOT make the AI independent/blind to that human position. Neither local filesystem time nor SHA-256 creates an external preregistration attestation. Never describe an ordinary record as independently timed or double-blind.

## Let the AI disagree for a reason

Record the AI's predicted player behavior, recommended next action and the strongest plausible rival explanation. Explicitly test whether the apparent disagreement is **material**: would it change the cheapest credible next observation or resource allocation? A wording difference, degree of optimism, personal taste or uncertainty is not inherently material. Do not average opinions or rank ideas with an invented combined score. Do not claim the AI's position was blind to the user's forecast.

A material disagreement should produce *one* discriminating player observation: target audience, observable difference, feasible test, budget/time ceiling and what decision might change. If real behavior cannot be assessed affordably, mark UNKNOWN rather than rejecting an original hypothesis. A test plan does not authorize recruitment, spending, public launch, experiment creation, or access to sensitive information.

## Preserve real evidence, corrections and negative examples

If a real authorized test occurs, record actual player choice, rematch, completion, response or other suitable behavior with its evidence pointer, recruitment context, limits and actual cost. Do not use synthetic players to certify fun, organic demand or human emotion. For multiplayer/strong-social games, small-group sessions can test interpersonal experience, but they cannot establish a network effect or representative market retention.

Record the *human's* changed prediction, the AI's documented revision, and any actual user-owned decision; missing responses remain NOT_REPORTED/NOT_ASSESSED. Preserve cases where human insistence wasted resources or a consensus judgment was wrong, not just impressive human rescues. An undecided or unobserved future outcome is not a negative outcome. Do not retroactively edit initial positions.

No record is a game-exp Manifest, protected Ledger, Candidate, trusted evaluation, human Review PASS/FAIL, PROMISING, SELECTED, REJECTED or authority to build/spend. Only bind actual game-exp identities confirmed via its authorized interface. Do not upload private player statements, company data, credentials or personal identifiers to a public repository.

## Two compatible ways to record, both optional

**ChatGPT web / no local Python:** use the short template in templates/human-ai-judgment.md as an in-chat working note. Only claim PRIVATE_PERSISTED after a real authorized private save, otherwise NOT_PERSISTED. Asking the one pivotal question is optional; ordinary opportunity analysis continues without a baseline.

**Local Codex/Cursor/Qoder:** scripts/judgment_log.py provides a pure-standard-library CLI. It requires only an existing opportunity Markdown card (it may still be a draft), and defaults to the git-ignored local-evidence/ folder. Stage order: start -> ai -> compare -> outcome. A record with no human baseline uses start with baseline type unavailable and no human fields. Run the command with --help to see parameters. An example of a single locally recorded human starting view:

    python skills/game-opportunity/scripts/judgment_log.py start --card opportunities/OPP-20261016-dice.md --case-id choice --baseline-type pre_ai_reported --human-prediction "New players will request another round" --human-next-action "Playtest direct chip transfers"

Append an AI view with the ai subcommand, then an optional comparison and actual observed or NOT_RUN outcome with compare/outcome; use show to inspect stage order and claimed limitations. The example is illustrative, NOT a true playtest. The JSONL previous-line digest detects accidental changes but is neither independently timestamped, tamper-proof nor concurrency-safe. Use one writer per record; protect local files as private. No new fields are added to the opportunity-card, H5 PROBE, Godot brief or game-exp protected schemas.

## Initial prospective evaluation

Reuse evals/p0c-case-template.md for 3–5 **real**, user-authorized opportunities with human originality, AI-led discovery, disagreement and agreement cases when available. Capture the counterfactual first: the human's original next action, estimated cost and key predicted behavior. After observation, record the actual change, human interruption time, direct test cost, missed promising options and misleading rescues. Static unit tests and sample prompts do not prove real user behavior or higher decision accuracy. Mark unrun host evaluation and unobserved market outcomes NOT_RUN. Keep the protocol only if those cases suggest human involvement repeatedly changes materially useful decisions enough to justify the interruption.
