# ET-VISUAL-02：选定视觉基线 02-R2（v1）

本包是**当前试点使用的视觉版本**，并非正式产品发布包。用户在比较 02-R1 与 02-R2 后给出的结论是“r2更好”，故将 R2 作为后续试玩、视觉问题修复和人工评审的起点。此前已选定的 R1 历史版本完整保留，绝不覆盖。

## 打开游戏（电脑键盘）

解压后，在本目录打开命令行执行：

```sh
python -m http.server 8765 --directory playable-r2
```

Windows 也可使用 `py -m http.server 8765 --directory playable-r2`。然后浏览器访问 `http://127.0.0.1:8765/`。使用 ←→ / A D 移动、空格跳跃、Shift/J 空中冲刺、E 锚定、R 重试。

移动端仅经过 Chrome CSS 视口模拟，**原游戏尚未提供手机方向/跳跃触控按钮**，不能将手机布局通过等同于真机可玩性通过。

## 文件

- `playable-r2/`：与已验证 CI 完全相同的 R2 HTML/JS 二进制字节；打包后未再编辑。
- `after/`：R2 已验证的竖屏及横屏截图。
- `scenes/`：轨道预告及空中轨道截图。
- `R2_original_review_evidence.zip`：用户评审时的原始包（含原版 R1/R2 对照、19 张截图、测试报告、验证工具），哈希不变。
- `DECISION.md`：本次人工视觉优选结论及边界。
- `NEXT_PLAYTEST.md`：后续试玩与缺陷闭环，尤其是真机交互。
- `selection_manifest.json` / `verify_selected.py`：完整性核验；运行 `python verify_selected.py`。

原仓库主线 Echo Tide 与 game-exp Ledger 未修改；game-opportunity PR #13 保持 Draft，不能从这次视觉偏好推定生产批准、游戏实验 SELECTED 或减少返工的因果结论。
