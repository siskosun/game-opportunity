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

## 2026-10-21 增量：ET-VISUAL-02 触控 T1 候选已工程验证，等待人工复评

- **唯一现行已选视觉基线仍为 `ET-VISUAL-02/candidate-02-r2`，不变。** T1 是基于 R2 的新增触控实验候选，尚未获得用户审美/手感评价，不得写成 SELECTED 或 game-exp PASS。
- P0-C 后续试点引入左右方向、跳跃、空中冲刺、锚定五个触摸按钮；竖屏安排在画布下方，844×390 横屏安排在游戏画布两侧；最小点击区域不低于 44 CSS px，允许双指操作。`src/game.js`、`src/render.js`、关卡、物理和游戏规则没有修改。
- 依照冻结 Echo Tide SHA `38b9daa1` 构建的 02-R2 HTML/JS 与先前用户选定包**字节 SHA-256 一致**后才叠加 T1。T1 Chrome 155 [CI #39573056148](https://github.com/siskosun/game-opportunity/actions/runs/39573056148) 通过，Linux/Windows [常规 CI #39573062331](https://github.com/siskosun/game-opportunity/actions/runs/39573062331) 通过；原 69 项游戏测试、新增 7 项触控逻辑测试和 R2 语义检查通过。
- 三个 Chrome 模拟移动视口（360×800 / 390×844 / 844×390）用真实浏览器触摸事件验证了移动、双指方向+跳跃、空中冲刺、触控释放、手势取消、失焦恢复和切换关卡；桌面 1280×900 保持键盘。四种视口均无横向溢出、首屏画布裁切、资源加载或脚本报错。**Chrome 模拟触摸不等于真机验证**。
- 测试对应的 T1 可运行 `dist/index.html` SHA 为 `317e8c4fab79f6f51a1a1872faa22a833a1d0c5024ae607ce56e0b86f98e011c`，JS SHA 为 `ccd61ae72d9e0fa0205d77cccf6761323ed8a18a9f75a477c446446ab0e79e19`；评审 ZIP 的 SHA-256 为 `9ae82a79365bbc6342135e02f20f31200f24453fdf470b3d49dd37be7bff28b3`，离线 20 文件校验通过。
- 资料空间：`/游戏开发方案/ET-VISUAL-01-草案/ET-VISUAL-02-触控T1-待评审/`；代码在 `siskosun/game-opportunity` Draft PR #13 的 `touch_t1/`。原 R2 归档与 pointer 不变，Echo Tide 主线及受保护的 game-exp Ledger 未修改。
- **下一道用户门槛：** 复评 T1 的竖屏/横屏按钮位置、触控手感；随后使用 Android/iOS 实机以及真实完整关卡试玩，禁止用 CI 代替玩家验收。未经人审不合并。

## 2026-10-21 · 竖屏 T1 已被否定，T2 仍待复评（最新）

- 用户对 T1 反馈原话：**“横屏没问题，竖屏操作很反人性”**。本次反馈对 T1 竖屏操作形成否定结论；**横屏维持 T1，不需要重做**。T1 原始按钮全放在同一行，左右拇指分区不清晰。这是用户主观体验反馈，不能被之前自动 CI 的 PASS 抵消。
- 实施 **T2 portrait-thumbzones**：仅在 `max-width:580px & orientation:portrait` 的 CSS 规则下将移动键分组固定在左下，跳跃+冲刺固定在右下，锚定单独置于右手区上方。视觉 R2、游戏核心、T1 横屏及触控 JS 均未修改；新候选未人工批准。
- [Chrome 触摸 CI #39576897475](https://github.com/siskosun/game-opportunity/actions/runs/39576897475) 与 [常规 CI #39576902951](https://github.com/siskosun/game-opportunity/actions/runs/39576902951) 均通过；69 项游戏测试、7 项触控单元测试、R2 状态语义测试通过。Chrome 155 模拟视口 360×640、360×800、390×844、844×390、1280×900，均无横向溢出、脚本/网络错误、控件遮挡；移动视口完成真实 CDP 触摸事件模拟。
- 横屏 T1 与 T2 两侧按钮、顶部工具栏截图区域逐像素一致；中心游戏动态物件存在因截图时刻造成的差异。T2 `dist/index.html` SHA-256：`2c51a8f7665a4eb292eb15100e83e254f4d25de9a6cc89b5102179147da8f922`；JS SHA-256：`ccd61ae72d9e0fa0205d77cccf6761323ed8a18a9f75a477c446446ab0e79e19`，后者与 T1 原始构建完全相同。
- 用户复评 ZIP `ET_VISUAL_02_touch_T2_review.zip` SHA-256：`2553fcc27f6c9cd84342dfc2f0a02eeec3cffb8a5c680e70ccabce5620dd8797`；21 项文件独立哈希校验通过。目录：`/游戏开发方案/ET-VISUAL-01-草案/ET-VISUAL-02-触控T2-待评审/`。
- **现行已选视觉基线仍为 02-R2**；操作布局只在 T2 候选中待用户二次评价。真机 iOS/Android、多关真人游玩、手感和 Art Director / game-exp 生产批准依然未完成；PR #13 保持 Draft，未合并 Echo Tide main，不写受保护 Ledger。

## 2026-10-21 · 用户否定竖屏虚拟按键，横屏优先 T3 待复评（覆盖旧 T2 状态）

用户反馈：**“操控面积太小了，竖屏不适合这种虚拟按键的方式”**。这构成对 **T2 竖屏虚拟按键路线**的明确否定，不能因 T2 自动检查通过而称其已获认可。先前反馈“横屏没问题”仍有效：**横屏 T1 已被认可**，无需改变。

- **唯一已选定的试点视觉基线继续是 02-R2**；T1/T2 历史源码和包保留，不替换 R2，也不把 T3 写成已认可版本。
- T3 `landscape-first-t3` 为可回退的候选：360–430 CSS px 的手机触控竖屏仅显示旋转说明，五个虚拟键隐藏、游戏时钟暂停；转横屏继续同一关卡；旋转途中清空按住的键，避免残留加速或跳跃。未做强制锁定手机方向；用户需自行关闭系统旋转锁定。
- [Chrome CI #39579632465](https://github.com/siskosun/game-opportunity/actions/runs/39579632465) 通过。固定 Echo Tide @ `38b9daa1` 与先前选定 R2 的构建字节 SHA 一致后，叠加横屏 T1 和独立 T3。Echo Tide 原有 **69 项**测试、已有触控 **7 项**单元测试、R2 状态语义检测通过；Chrome 155 对 360×640、360×800、390×844、430×932 竖屏、844×390 横屏、1280×900 桌面及原页面旋转-继续-旋转回竖屏做了模拟检查，**全部通过**，无资源/JavaScript 错误。
- 经过与 T2 中继承的已认可横屏截图对比，844×390 **左右按钮区和顶部控件区域三块 ROI 的差异为 0 像素**；T3 仅更改试验版 `index.html` 和输入适配宿主 `src/main.js`，未触动 `src/game.js`、`src/render.js`、关卡和规则。
- T3 HTML 构建 SHA-256 `b12b74cca5574fcbc62b6e039691097b2b3438c3977ae924f92a4fdc03e33d74`；JS SHA-256 `d9f50030f85d40279f37c23590dc72039a1941421ebe77a2d0b776b7f6eedd63`。可运行复评包 SHA-256 `2b544e6d7156b1f34bccdab2f9d922d82ce22aa7ed8e2d50acaff4528c942707`。
- 资料空间：`/游戏开发方案/ET-VISUAL-01-草案/ET-VISUAL-02-触控T3-待评审/`，代码 [PR #13](https://github.com/siskosun/game-opportunity/pull/13) 仍 Draft 未合并。
- **尚未验证**：T3 横屏优先策略是否符合用户目标，手机 iOS/Android 真机旋转/触控及整关体验。当前项目不是 game-exp 新实验，未写 Review PASS/SELECTED，原 Echo Tide main 与受保护 Ledger 未更改。
