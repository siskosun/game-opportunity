# Signal triage evaluation — v0.4.5

The eight \`v045-*\` cases in \`evals/cases.json\` are **expected behavior prompts**, not executed results.

Before claiming cross-host PASS:
1. Install the exact compatible version in each target host; check host's actual Skill route/versions and tools.
2. Run each case in a fresh context and document the full sanitized response. Record whether a wrongly repeated claim was treated as independent, whether a generic 4-week TTL or hard numerical gate was imposed, and whether original creative mechanics were prematurely rejected.
3. Require correct uncertainty and next *single* differentiating observation; grade missing primary evidence as UNKNOWN rather than retroactively assigning plausible numbers.
4. Confirm direct H5/Godot bugfix routes and game-exp protected Review are still unaffected.
5. Use the pre-existing \`p0c-case-template.md\` prospectively on 3–5 authorized real candidate games to compare the user's original next action with the modified one. Include both avoided wasted builds **and** mistakenly screened-out opportunities. Without real outcomes, record NOT_RUN and do not claim improved market opportunity hit rate.

The added Python tests prove only that old cards remain parsable, the optional signal notes appear in new cards, and these behavior prompts are registered. No live player trial, model-route test, demand estimate, autonomous scraping, automated archival, or game-exp lifecycle mutation occurs.
