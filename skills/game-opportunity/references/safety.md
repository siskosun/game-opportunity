# Human participants, channels, and budgets

Provide test plans and draft materials. Do not autonomously recruit, contact people, launch campaigns, publish external pages, modify live apps, pay or spend, collect private records, or access data without user authorization and a suitable tool.

Prefer truthful concept tests. A misleading or fake-door test, if considered, requires human review, an ethically appropriate disclosure/debrief, and compliance with local law/policy; don't imply an unavailable game is already playable. Do not design a deceptive tactic as the default.

Do not store or publish raw identifying interview notes, phone numbers, children's data, login identities, cookies, secrets, or proprietary user-level analytics in opportunity files. Use authorized aggregated/anonymized evidence references; redact sensitive data. If research concerns minors, require compliant age-appropriate recruitment and safeguards; don't assume direct recruiting is permissible.

Costs, advertising budgets, subscriptions, third-party API charges, and public publishing require explicit human authorization. A plan may estimate them but must not spend or publish by itself. Report all participant samples, dates, measured outcomes and missing results without inventing a PASS.

## Public source repository

The canonical code repository, `siskosun/game-opportunity`, is PUBLIC. Keep real unpublished research and personal or proprietary analytics out of its Git history. An opportunity card may be committed there only after an explicit per-card public-publication decision and redaction review. Local `opportunities/OPP-*.md` drafts are ignored by Git by default; forcing a Git add or creating a GitHub file is a deliberate publication action. Never infer that permission to edit a repository equals permission to publish research.


## Local evidence tooling

`import_evidence.py` and the optional Steam adapter create only aggregate results in `local-evidence/` by default (Git-ignored). These are not ready-to-publish findings: a narrow sample or counts from a few users can still be sensitive. A human must review each aggregate before any public disclosure. `steam_reviews.py` requires `--confirm-public-fetch`, bounds pages, reviews and delay, never requires private cookies, and must stop when Steam denies or rate-limits access. No domestic-platform access bypass, identity-level analytics export or third-party user list gathering.
