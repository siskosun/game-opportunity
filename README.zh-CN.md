# game-opportunity：游戏机会探索

[English](README.md) | **简体中文**

这是独立的游戏机会探索技能，不属于 game-exp 的可信生命周期控制层。它帮助开发者判断潜在玩家、未满足需求、候选玩法，以及下一步成本最低且能影响决策的验证方式。

## 安装与边界

将 `dist/skill.zip` 导入 ChatGPT 或所用开发工具支持的 Skill 安装入口。安装不会创建私有 GitHub 仓库，也不会自动安装或升级 H5、Godot、game-exp。

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
