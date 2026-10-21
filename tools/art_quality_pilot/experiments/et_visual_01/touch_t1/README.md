# ET-VISUAL-02 · Touch T1 (experimental, not approved)

**Selection remains `ET-VISUAL-02/candidate-02-r2`.** This directory adds a reversible touch-control candidate to a byte-verified build of that selected baseline. The game prototype is still keyboard-based in Echo Tide main.

## Build chain and source freeze

1. Checkout `siskosun/echo-tide@38b9daa1adf78002c8ec5349c269a4ce31959d8f` in a disposable directory.
2. Run the existing `../r2/apply_r2.mjs`; build with `npm ci` + `npm run build` and verify that compiled R2 HTML and JS SHA-256 match selected R2 (`d7eb284f...` and `6e00ce0e...`).
3. Run `node touch_t1/apply_touch.mjs <checkout> --already-r2`, run original Echo Tide tests, `r2_semantics.mjs` and `tests/touch_controls.test.mjs`, build the resulting T1 artifact.
4. GitHub Actions `.github/workflows/et-visual-touch-t1.yml` uses Chrome 155 + CDP touch dispatch at 360×800 / 390×844 / 844×390 and desktop 1280×900, records screenshots, positions, input/state deltas, error logs, and exact compiled hashes; keeps the result in a 14-day CI artifact.
5. A persistent independent review copy is stored in ChatGPT Library at `/游戏开发方案/ET-VISUAL-01-草案/ET-VISUAL-02-触控T1-待评审/`, including browser SHA checks and a runnable ZIP.

## Mapping

| Mobile button | Existing authoritative input |
| --- | --- |
| ◀ 左 / 右 ▶ | `ArrowLeft` / `ArrowRight` while pointer is held |
| 跳跃 | `Space`, short pulse protected against missed animation frame |
| 冲刺 | `ShiftLeft`, available in the air in surf mode |
| 锚定 | `KeyE`, only meaningful in a level allowing an anchor |

Touch events and desktop keyboard state remain separate and are merged only when building input for `update(game,input,dt)`. Multiple pointers support walking and jumping simultaneously. `pointercancel`, lost pointer capture, blur, hidden document, orientation changes, and explicit level/mode reset clear the touch state. No second gameplay rules engine and no synthetic target selection are introduced.

## What the green CI means and does not mean

Validated: 69 original Echo Tide game tests, 7 new unit tests, the R2 semantic checks, touch-target geometry, canvas first-screen visibility, actual Chrome compositor touch input, simultaneous movement+jump, air dash, release/cancellation/blur, and no script/network errors at selected emulated viewports.

Not validated: physical iOS/Android phone, full-level completion using only touch, screen reader usability, user control feel, human visual approval, Art Director production sign-off, or game-exp PASS/SELECTED. The user has **not** approved T1, only its R2 parent. This work remains in Draft PR #13, without editing Echo Tide main or protected game-exp Ledger.
