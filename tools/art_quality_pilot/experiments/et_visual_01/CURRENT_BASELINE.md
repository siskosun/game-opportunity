# ET-VISUAL 当前视觉基线（2026-10-21）

**当前选定：ET-VISUAL-02 / candidate-02-r2（选定试点视觉基线 v1）。** 用户对 02-R1 与 02-R2 进行对照后，原话：“r2更好”。后续新视觉任务和试玩以 R2 为输入；02-R1 为已封存历史基线，仍可回退，不再是现行首选。

## 权威记录与版本

- 最新资料空间目录：`/游戏开发方案/ET-VISUAL-01-草案/选定基线-02-R2-v1/`
- 当前选定归档：`ET_VISUAL_02_R2_selected_baseline_v1.zip`
- 归档 SHA-256：`b63f80ad61a79abb27f78d0455d2fa46ba21e3a6e8a061c6492323ce0cb86dad`
- 原 R2 评审包 SHA-256：`79bbfb85f5949980059ff300c93eb24c0f4674bb0319c392310dd235f555a5be`
- 原游戏源码：`siskosun/echo-tide@38b9daa1adf78002c8ec5349c269a4ce31959d8f`
- R2 试验构建源码：`siskosun/game-opportunity@59559cc1d173ae03c69fd59700fb8037be75a598`
- Chrome + 游戏测试已验证：https://github.com/siskosun/game-opportunity/actions/runs/39556854606
- R2 HTML 构建 SHA-256：`d7eb284f748f6ff258ba17d7cc02f2e465dc4a5f35603d9c454cd3aeac080136`
- R2 JS 构建 SHA-256：`6e00ce0e34fe5202a90540a29731cc435df42bad72b8bea7319c01cdf9d84de3`
- 历史基线（不得覆盖）：`/游戏开发方案/ET-VISUAL-01-草案/选定基线-02-R1-v1/`

## 精确结论与下一步

用户表达的是**视觉偏好选择**，并非生产级美术审查结论。完整记录见选定包中的 `DECISION.md`。原游戏仓库 `main` 与 game-exp 受保护 Ledger 未修改；试验 [PR #13](https://github.com/siskosun/game-opportunity/pull/13) 保持 Draft、未合并，不能称为 game-exp 的 `Review PASS` 或 `SELECTED`。

下一轮以 R2 开始检查**手机触摸操控**：目前原游戏没有屏幕方向/跳跃键；Chrome CSS 视口布局通过不等于真实 iOS/Android 可玩性通过。还需要真机、动态轨道与警示状态的人审、长期稳定性，以及真正独立 Agent A/B 的返工与成本数据。后续不得拿本次视觉偏好声称 Art Director 降低了返工。

**状态修订说明**：旧目录和旧版报告写的“R2 待审”均为历史记录，本文件覆盖其当前状态。未经用户再次认可，不得用下一个新候选替换 R2。
