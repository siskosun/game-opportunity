# ET-VISUAL-01｜02-R1 选定视觉基线（试点用）

**结论：** 用户在 2026-10-21 的两轮视觉对照中偏好右侧方案，并明确同意以修订版 **candidate-02-r1** 作为后续真实美术任务与试玩验证的当前视觉基线。此处的“选定”仅指视觉方向和后续试点输入，**不是正式上线批准**。

## 如何运行

1. 解压 `ET_VISUAL_01_02_R1_visual_baseline_v1.zip`，进入目录 `ET-VISUAL-01-selected-02-r1`。
2. 在该目录运行 `python verify_baseline.py`，核对所有文件哈希和文件集。
3. 进入子目录 `playable`，用 `python -m http.server 8765`（Windows 可用 `py -m http.server 8765`）启动本地静态服务器。
4. 浏览器打开 `http://127.0.0.1:8765/`。**不能直接双击 `index.html`**：其 Vite JS 使用 `/assets/...` 绝对路径。
5. 游戏原有键盘操作：左右方向/A/D、空格跳跃、Shift/J 冲刺、E 锚定、R 重开；不要将此视为已实现移动端触屏控制。

## 这个版本冻结了什么

- 方案：原方案 02 的配色、轮廓和视觉层级 + R1 横屏 14px 控件间距、竖屏四控件等宽两列且左对齐。
- 底层 Echo Tide 源提交：`38b9daa1adf78002c8ec5349c269a4ce31959d8f`。
- 试验实现脚本所在 game-opportunity 固定提交：`f2372233ceae93898bdd3b65c0240b5eae91a175`。
- 可运行 `playable/index.html`、JS 及 36 张截图完全保留于原浏览器 CI 输出，文件 SHA 不变。
- 输入/修订轨迹：`evidence/lineage.json`；4 视口浏览器数据和 36 张截图的哈希：`evidence/runtime-report.json`。
- 选定层级与人体反馈：`DECISION.md`、`manifest.json`。
- 后续美术任务和试玩检查：`NEXT_ART_TASK.md`、`PLAYTEST_PLAN.md`。

**不包含**：正式 game-exp Candidate、人工 Review PASS/FAIL、选入主线的生产资产、已确认的 Art Director 规则、真实双盲 A/B 效率结果。禁把当前包宣称为 game-exp `SELECTED`，也不代表已合并 `echo-tide/main`。原有 Art Director B 组草案规范单独存于资料空间并继续保持 `proposed` / `candidate` / `approval=null`。

本包只做哈希完整性校验，不是数字签名，也不能验证提出意见者身份。后续修改必须新建版本，保留此包及其哈希，不覆盖旧版本。
