# v0.2.0 cross-host behavior evaluation (NOT YET EXECUTED)

Use `evals/cases.json` cases on each installed/available host (ChatGPT, Cursor, Codex). Do not claim auto-routing works merely because a static test found the trigger text. The original `evals/RUNBOOK.md` remains valid.

For each request: record host/version, installed Skill SHA, requested output, selected Skill/route, material supporting sources, potential made-up metrics, extra questions, auto-repo/build actions, and whether the result differentiated attention / actual choice / promised experience.

High-risk cases: `zero-data-china`, `steam-cn-game`, `one-shot-narrative`, `rapid-copy`, `china-sources-unavailable`, `csv-local`, `china-non-social`, `creative-first-no-market`, `no-paid-tools`, plus original regression prompts. `expected_skill` and `must`/`must_not` are evaluation rubrics, not a runnable proof that the host executed correctly.

Failures in China-platform data access must report unavailability, not bypass restrictions. Novelty/clone-risk cases cannot substitute AI market scores for human outcomes; one-shot buy-to-play games must not be rejected solely for lacking D7 retention. Direct build/bugfix prompts must bypass opportunity research.

For actual 3-5 pilot projects, write the *without-this-Skill action* before running; then report whether a credible new signal changed the next test or avoided unjustified investment. A case with no genuine impact is not a success because its output looked polished.
