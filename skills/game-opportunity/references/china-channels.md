# China-local player discovery and validation

Use this guide when the user targets mainland Chinese players or Chinese-language distribution. Choose only relevant channels; it is **not** a requirement that games be 2D, social, ad-driven, short-session, mobile, or suitable for any named employer. Channel features and regulatory conditions change; recheck official docs before recommending a live test.

| Route | What it can help test | Important limitation / action |
|---|---|---|
| TapTap | Early core gameplay, invited/closed player sessions, promotion material | TapTap's [test overview](https://developer.taptap.cn/docs/store/operation/test/test-skills/support/) distinguishes early gameplay (`篝火`), closed/open testing and material testing; eligibility, review, allowed traffic and SDK requirements are not automatic. Ask the human to verify current availability. |
| Douyin mini-games | Content-driven discovery, entry/source analysis and later return | Official [retention/source analysis guidance](https://developer.open-douyin.com/docs/resource/zh-CN/mini-game/operation1/user-ops/-retention/sidebar) describes developer-console metrics; it does **not** provide public access to another game's cohorts. |
| WeChat mini-games | Social/contextual entry, invitations and repeat sessions when implemented | Check the actual current mini-game developer portal and permissions. No public telemetry for arbitrary competitors, and no automatic Mini Program publication. |
| Steam with Chinese players | Paid-PC comparable titles, Chinese review excerpts, positioning and real substitute choices | Steam app review data may be sampled and biased; do not apply fixed review-to-revenue factors. Optional `steam_reviews.py` reads public reviews with bounded requests; no bypass of restrictions. |
| Bilibili, Xiaohongshu, game forums and creator channels | How potential players discover, explain, criticize or share a game | Prefer user-supplied files and officially available/public pages; a login wall, CAPTCHA, robots restriction or missing API is **unavailable**, not an invitation to evade. |

## Validation choices and authorization

If the question is concept comprehension, use truthful concept material and a recruited/manual test; a released build or game license is not inherently necessary for planning. If the question needs actual gameplay, identify platform account/setup and test prerequisites first. Any public launch, promotional spend, access to first-party data, sampling of minors, collection of personal information or commercial release needs explicit human authorization and appropriate review. Do **not** issue blanket legal or game-license conclusions based on a Skill heuristic.

For no-account/no-tool users: allow manual source checking, supplied CSV/JSON review samples, short interview designs and clearly marked hypothetical options. Never fabricate inaccessible domestic-platform metrics, closed community posts, CPI, CPA or retention.

Official docs checked for this guide: 2026-10-14; check current source status at use time.
