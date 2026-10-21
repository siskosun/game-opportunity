# ET-VISUAL-01 — user review Round 1 / targeted revision

Observed human feedback (2026-10-21; reported directly in chat, not a signed game-exp review):

> landscape里的两组图，右侧2更美观，但几个下拉框挤在一起，略显拥挤。portrait里的两组图，右侧2框线美观、文字字体颜色更显眼，但居中显示长短不一，不美观。

Decision for exploratory visual design: carry **candidate-02** forward as the *preferred direction*, not as production-accepted artwork. Create **candidate-02-r1**, preserving its borders, font colors, and game visual rendering. Target only toolbar layout: (1) separate desktop-style pills in landscape; (2) use an even two-column / two-row grid with left-aligned text in portrait. Do not revise gameplay rules, game-exp approvals, or the shared art pack because this feedback does not authenticate a final design approval.

QA acceptance: Build from frozen Echo Tide commit `38b9daa1adf78002c8ec5349c269a4ce31959d8f`; run actual Chromium at 360×800, 390×844, 844×390 and 1280×900. Assert no horizontal overflow, all game canvas visible, four portrait controls in aligned cells with 40+ CSS pixel height and left-aligned text, and 12+ CSS pixel landscape gaps. Preserve original `candidate-02` snapshots to allow an unaltered before/after comparison. All candidate work stays in `game-opportunity`'s Draft PR #13 and ephemeral CI worktrees, not in Echo Tide game source.

Limits: One reviewer preference is not a complete human visual-quality rubric, formal game-exp PASS/FAIL, an independent-agent A/B or evidence of reduction in rework; avoid labeling it as such.
