# Public-safe opportunity cards only

The parent repository `siskosun/game-opportunity` is PUBLIC. This directory initially contains only this README. Files matching `OPP-*.md` are ignored by Git to reduce accidental publication.

Use `scripts/opportunity_card.py` to create a local `OPP-YYYYMMDD-short-slug.md` draft. Before publishing a particular card, review the entire content for confidential business information, participant or employee identifiers, private user-level analytics, paid campaign credentials, access tokens and unpublicized strategy. Publish **only with explicit authorization** to make that specific card public (for Git use `git add -f opportunities/OPP-...md`). All previous commits stay publicly visible even after redaction.

If the research is not public-safe, retain it in a separately authorized PRIVATE data store. A non-sensitive opportunity ID or evidence pointer may live here when authorized; the protected evidence does not. Ordinary cards are not game-exp Ledger objects. The local append-result helper appends observations but does not make them remotely durable or tamper-proof.
