# game-opportunity：游戏机会探索

[English](README.md) | **简体中文**

这是独立的游戏机会探索技能，不属于 game-exp 的可信生命周期控制层。它帮助开发者判断潜在玩家、未满足需求、候选玩法，以及下一步成本最低且能影响决策的验证方式。

## v0.3.0：主技能与完整工作流

**game-opportunity 是面向用户的主入口**：从想法、玩家研究、低成本验证，一直到用户明确要求创建可玩实验、实际试玩、复盘。game-exp 继续独占可信实验管理，H5/Godot 负责开发和执行；不会增加第二套 Manifest 或 Ledger。直接要求修 Bug、修改已有原型、开发 H5/Godot 时，不强制先做市场研究。

### 配套安装（Windows Cursor/Codex/Qoder）

本地执行一次明确授权的安装命令，可配套安装当前 Skill 和 **兼容锁批准的 game-exp 正式稳定版**，以及配套 H5/Godot。未经联合检查的新版本不会自动安装。game-exp 的**原生安装器**还会在同一个 Harness 中同步 H5、Godot Skills，以及 game-exp MCP/运行时。必须有 Python 3.11+、联网访问 GitHub、满足 game-exp 的本地安装前置条件；对后续正式实验还需 gh/GitHub 相应权限。

先取得公开源码（首次安装）：

```powershell
git clone https://github.com/siskosun/game-opportunity.git
cd game-opportunity
python -m pip install uv
```

在仓库根目录执行预览（离线、无写入）：

```powershell
python skills/game-opportunity/scripts/install_bundle.py --harness cursor --plan
```

确认后安装（实际下载并安装依赖）：

```powershell
python skills/game-opportunity/scripts/install_bundle.py --harness cursor --json
python skills/game-opportunity/scripts/install_bundle.py --harness cursor --verify --online --json
```

将 `cursor` 替换为 `codex` 或 `qoder`。默认只影响指定 Harness。仅当用户明确要求同步所有三个本地 Harness 时，才使用 `--harness all`。安装器拒绝从 game-exp 的未发布 `main` 自动安装，不会自动降级。当前兼容锁固定 game-exp `v1.5.3`；若显式使用 `--game-exp-release`，必须指定与当前锁完全一致的 `v1.5.3`，且仍遵循其降级保护。

**ChatGPT 网页端**：导入本 Skill ZIP 并不会自动执行安装脚本，也不能替用户往 Windows 写入 game-exp 的运行时或 MCP 配置。需要用户另行在支持的环境中安装/连接 game-exp，或在网页端通过支持的安装入口分别导入可用的 Skill；没有可信生命周期工具时，仍能研究机会，但不能伪造正式实验操作。

`--check` 只检查文件是否存在。要验证已安装版本、源码摘要及远程发布情况，使用 `check_bundle.py --harness cursor --online --json`（或安装器 `--verify --online`）。它依旧**不等于** game-exp 的 Doctor 或真人试玩验收。安装器现在仅安装通过当前版本锁记录的组合，失败会尝试恢复所选 Harness 的原有技能、运行时和配置；恢复成功报告 `ROLLED_BACK`，若文件锁或其他错误导致恢复不全则报告 `ROLLBACK_INCOMPLETE`，不能视为成功。具体操作和边界见 [完整工作流](skills/game-opportunity/references/full-workflow.md)。

### 从机会到试玩、再回到证据

当用户决定进入正式实验时，首先由 game-exp 完成实际仓库初始化和 `PROJECT_READY` 检查，再获取当前 Manifest 模板、由用户确认关键判断后 Bind/Initialize。**市场机会卡不会自动写入 Ledger，也不能替代人类 Review。**

只读生成普通研究交接包：

```powershell
python skills/game-opportunity/scripts/handoff_bundle.py --card opportunities/OPP-20261014-example.md --stack h5 --mode same-question --confirm-same-question
```

如果是从市场兴趣验证升级到玩法体验验证，使用 `--mode next-stage --next-hypothesis ... --next-kill ... --reason ...` 明确新的问题，不得默默修改原假设。输出的卡片 SHA、远端来源和证据仅作研究引用，**不是** game-exp Manifest 或可信 Ledger。

完成真实玩家测试后，可用 `scripts/link_result.py` 给机会卡追加观察及实际已知的 PROBE、EXP、Candidate、source SHA 等来源关系。只登记操作员提供的信息，不能自动确认其可信性，不能自动触发 PASS/SELECTED/REJECTED。相关命令与验收见 [完整工作流](skills/game-opportunity/references/full-workflow.md)。

## 安装与边界

将 `dist/skill.zip` 导入支持 Skill 的平台，只会安装 game-opportunity 的指令和脚本。**仅在用户明确运行本地配套安装命令后**，才会安装/升级 game-exp 及其 H5/Godot 伴随 Skills；单独导入 ZIP 不会自动触发安装。

请求直接开发 H5 原型、修改 Godot 游戏、修复 Bug，仍交给对应游戏开发技能；创建、评审、选择或归档正式实验由 game-exp 负责。市场研究不是所有开发任务的强制前置步骤。

## 机会卡与记录

每张机会卡只要求三项决策信息：**关键不确定性、最小验证、继续／调整／停止条件**。玩家、场景、竞品和证据来源按需记录。允许两种探索路径：需求驱动与创意驱动，不能强制原创玩法先证明已有市场需求。

`scripts/opportunity_card.py` 可以离线创建卡片、校验必填内容、按结果编号追加观察记录，以及在指定目录搜索。追加行为只修改本地文件；只有经过授权的 Git 提交和推送才算远程保存。不能以聊天记录或本地路径冒充跨工具的持久化证据。

当前源码仓库为**公开仓库** `siskosun/game-opportunity`。`opportunities/OPP-*.md` 默认被 Git 忽略，避免误公开。只有逐张审查、完成脱敏并明确同意公开的机会卡，才可提交。内部经营数据、玩家身份及其他敏感证据必须存放在另外获授权的私有位置。

## 可信程度

公开评论、榜单与社区反馈只是线索，不自动证明新游戏具有市场机会。真实玩家访谈和测试必须区分观察、解释与假设；点击、收藏和意向测试不能当作复玩或收入证据。

涉及真人招募、未成年人、个人信息、对外发布、渠道投放及任何支出，需要人工确认和合规处理。不得向公开仓库提交原始敏感数据。

## 验证

本项目的 `tests/` 为单元及静态契约测试；`evals/` 包含 Cursor、Codex、ChatGPT 的行为测试用例。**行为测试需要在对应宿主实际运行**，通过单元测试不等于证明模型能正确选择技能。

P0-C 仍须在 3–5 个真实选题中记录：原本准备直接开发什么、新流程改变了什么，以及实际节约或增加的验证成本。

## v0.2.0：面向中国用户的轻量机会验证

不要求用户安装游戏雷达、购买数据、绑定私人平台账号，也不强制做社交游戏、2D 游戏或小游戏。可以从一句“帮我找值得开发的中国 PC 策略游戏”开始，或者直接讨论一种原创机制。

新版的分析顺序是：现有替代选择和失败案例 → 玩家为何会注意、选择并获得预期体验 → 快速被模仿后的差异 → 最有决策价值、成本最低的测试。一次通关的买断/叙事游戏不强制用 D7 留存考核。

- `references/discovery.md`：无任何现成市场资料时，如何主动寻找线索，以及如何处理信息源不可访问。
- `references/comparable-games.md`：按真实玩家替代关系选择成功、普通与失败参照，不套用固定销量倍数。
- `references/player-choice.md`：注意、选择、体验结果三层证据和快速复制情景。
- `references/china-channels.md`：TapTap、抖音/微信小游戏、Steam 中文市场以及国内社区的可选验证路径；实际平台功能需要核对官方最新文档。

### 不用网络：本地评论 CSV/JSON 导入

只需 Python 3.11+，无需安装额外库。下面的示例使用**完全虚构的评论**：

```powershell
python skills/game-opportunity/scripts/import_evidence.py --input examples/synthetic-reviews.csv --platform synthetic_example --sampling-notes "仅演示，不是真实玩家样本"
```

支持 UTF-8/UTF-8 BOM 的 `.csv`、`.json`、`.jsonl`，以及常见中文列名、Steam 评论 JSON。默认在执行命令的工作目录生成 `local-evidence/<输入SHA前12位>.summary.json`，**不生成评论原文、评论 ID、玩家账号等明细**。结果包含去重后的分母、已明确标注的好/差评数和主题关键词命中量。

这些关键词只能用作探索线索，不能直接当作“玩家痛点数量”“真正的市场需求”或情绪分类。否定表达也可能命中关键词。样本来源和代表性必须另外核对。

`local-evidence/` 默认被 Git 忽略。脚本不会联网、不会推送 GitHub、不会覆盖已有摘要。原始数据仍只应保存在有相应权限的本地或私有位置；**摘要也需人工审查之后才能公开**。

### 可选：有限量地获取 Steam 公开评论

当用户明确允许访问公开 Steam 数据，且所在网络可访问时，可以使用：

```powershell
python skills/game-opportunity/scripts/adapters/steam_reviews.py --appid 123456 --language schinese --max-pages 2 --max-reviews 100 --confirm-public-fetch
```

将示例 App ID 替换为真实 App ID。默认最多查询 2 页、保存不超过 100 条去重后的评论统计；硬上限分别为 5 页、500 条，最短请求间隔 1 秒。只访问 Steam 公开评论服务，不使用登录凭据；遇到 403/429 等拒绝或频率限制即停止，不切换通道绕过。**不会把原始评论写入磁盘**。

此可选代码移植了 [SteamReviewFetch](https://github.com/Seafoodsz/SteamReviewFetch) 的请求、游标分页、去重和受控重试方法，已按 MIT 许可证保留原作者版权和许可声明。详见 [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)。

### 决策与开发边界

继续使用原来的机会卡三项必填决策信息和 `opportunity_card.py`，不会另造 PROBE/Manifest。真实玩家招募、投放、测试发布均由获得授权的人执行。所有私人评论原文与公司数据都禁止提交到本公开仓库。

> 发布状态：本次升级验证由单元测试及 CI 覆盖；跨 Cursor、Codex、ChatGPT 的实际路由评测和 3–5 个真实选题的 P0-C 仍需执行。未完成的评测不能视为 PASS。

## v0.4.0：玩家验证闭环（离线、本地、非权威）

新版主要解决“**最初预期什么，真实玩家实际做了什么**”这一断点。保留 v0.3.0 的主技能配套安装和 game-exp/H5/Godot 交接能力，不强制每个创意都开发原型，不要求游戏适合玩吧、微信小游戏或任何固定渠道。

新增 `scripts/validation_cycle.py`，仅使用 Python 标准库，支持两步：

1. `plan`：在测试前从**已填写完整**的机会卡创建独立 JSON 验证计划，明确唯一玩家行为指标、分子/分母、人群、时间窗、样本来源、最小分母和由用户解释的继续/停止信号。输出本地文件及 SHA-256。应当在测试发生**之前**把 SHA 存入有独立时间记录的授权私有位置；本地 SHA 自身无法证明创建时间。
2. `assess`：测试完成后，读取**单条汇总记录**的 UTF-8 CSV/JSON，逐项校验指标、统计单位、人群、时间、来源及分母，并仅提供描述性“达到预设信号/证据不足”判断。严格拒绝多来源、多日期或多分组记录的自动相加或平均，也不接收评论原文、玩家 ID、手机号等多余列。

中文 CSV 字段示例见 [`examples/synthetic-behavior-aggregate.csv`](examples/synthetic-behavior-aggregate.csv)。该文件**完全虚构**，仅用于运行功能演示；不能作为真实玩家验证证据。详细操作、参数与信号定义见 [`references/validation-cycle.md`](skills/game-opportunity/references/validation-cycle.md)。

在仓库根目录查看参数：

```powershell
python skills/game-opportunity/scripts/validation_cycle.py plan --help
python skills/game-opportunity/scripts/validation_cycle.py assess --help
```

示例验证数据兼容中英文字段，但只接受明确的 **unique_players（独立有效玩家）** 统计单位。若平台只提供浏览量、曝光次数或会话数，不能冒充独立玩家。`qualified_interest` 只代表兴趣信号，不代表付费或留存；叙事买断游戏可以用 `finite_game_completion`，而不是强制套用 D7。

输出默认放在 `.gitignore` 排除的 `local-evidence/`，不会自动上传 GitHub、接触真实用户或修改游戏仓库。只有取得实际证据后，才可用现有的 `link_result.py` 将汇总来源和局限追加至机会卡。

**game-exp 仍是唯一可信实验控制层。** 无论本地观察达到继续或停止信号，都不能自动成为 game-exp 的 Candidate Review PASS/FAIL、PROMISING、SELECTED 或 REJECTED。H5/Godot 的机器测试也不能证明真实玩家喜欢该玩法。

本版自动测试使用合成数据；真实玩家试运行、正式安装的跨 Harness 行为路由，以及生产环境 game-exp 实验端到端测试，仍须独立验证。


## v0.4.2：四技能正式发布版联动

当前通过发布来源核验的四技能组合为：主技能 **game-opportunity v0.4.2**，以及 **game-exp v1.5.3**、**H5 v0.2.4**、**Godot v1.0.6**。兼容锁记录各配套技能的确切提交和入口文件摘要，不再引用下方 v0.4.1 的历史基线。

本仓库新增 GitHub Actions 临时环境真实联网安装检查：仅在隔离 HOME 安装四个已经发布的技能，读取版本、来源和摘要，不运行真实游戏项目，也不会触碰用户本机。安装检查通过不等于 game-exp Doctor、人工 Review 或玩家测试完成。

进入受管实验前建议先运行 `python skills/game-opportunity/scripts/check_bundle.py --harness codex --online --json`，按原有显式安装命令配套安装。ChatGPT 网页端导入主技能后仍不会自动安装其他三个技能或本地 MCP。

## v0.4.1：调用前检查版本与兼容性

本地版本检查器：[check_bundle.py](skills/game-opportunity/scripts/check_bundle.py)。已发布版本锁：[compatibility.lock.json](skills/game-opportunity/compatibility.lock.json)。在历史 v0.4.1 版本中锁定 **game-exp v1.5.2 正式 Release、H5 v0.2.3 语义标签、Godot v1.0.5 语义标签**；这些来源在 GitHub 上可核对，但锁定版本只通过静态契约与工程测试，**尚未完成真人端到端实测**。本节仅保留历史基线供参考；当前三个配套技能的兼容说明已经正式发布，准确版本见上方 v0.4.2 章节。源代码合并仍不会自动升级用户设备。

在进入由其他技能执行的本地原型或受管实验前，运行只读检查：

```powershell
python skills/game-opportunity/scripts/check_bundle.py --harness cursor --online --json
# 也可以通过主安装器检查，均不会写入：
python skills/game-opportunity/scripts/install_bundle.py --harness cursor --verify --online --json
```

结果区分 `CURRENT`（当前正式版本锁匹配）、`UPDATE_AVAILABLE`（出现未经联合验证的新标签）、`NOT_INSTALLED`、`INCOMPATIBLE`、`UNVERIFIED`。不联网的结果不会声称“已是远程最新版”。出现新版本并不直接安装，应先通过兼容性审查，确认后再更新版本锁和安装器。旧的 `--check` 仍只是文件存在性检查。

配套安装命令不变，但会先核对当前锁定的正式发布版本：

```powershell
python skills/game-opportunity/scripts/install_bundle.py --harness cursor --plan
python skills/game-opportunity/scripts/install_bundle.py --harness cursor --json
```

脚本不会在普通 Skill 调用时暗中安装；只有用户授权执行才会修改当前 Harness。安装后再次核查，失败尝试整体恢复，若 Windows 锁定文件造成恢复失败则明确报错。仍必须按 game-exp 官方流程检查 Doctor、当前项目能力及人工 Review。网页版 ChatGPT 无法靠导入 ZIP 来执行这些本地检查或安装其他技能。

[上游版本监测工作流](.github/workflows/upstream-version-watch.yml) 定期读取正式发布版本；发现新版本只尝试提出**待审核的 Draft PR**，不会自动替换兼容版本锁。GitHub Actions 账户需有允许创建 PR 的权限；如果没有，该自动提议步骤会报告失败。详见[版本校验规则](skills/game-opportunity/references/version-check.md)。
