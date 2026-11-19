# 出错对照

`run_list.py` 结束时会把这次运行的关键日志行和截图耗时打印出来，先看那里。要看全文：`<COPILOT_WORK>\maacore\debug\asst.log`（MaaCore 的 `user_dir` 指到这里，不碰 MAA 自己的 `debug`），用 `Select-String` 按关键字筛，不要整个读。

**判断原因之前先看截图耗时**：上百毫秒（或 `mumu_handle_=0`）时，编队、部署、结算的识别都不可靠，下面各表都先别对照，先设对 `MUMU_DIR` 重跑。

## 跑不起来

| 现象 | 原因 | 处理 |
|---|---|---|
| `OSError: [WinError 1114]` | Python 3.11 载入 `MaaCore.dll` | 用 `py -3.12` |
| 退出码 2「连不上模拟器」 | ADB 地址不对 / 模拟器没开 | `emulator_status` 看地址；没开就 `emulator_start` |
| 「已经有一个抄作业在跑」 | 上次的 python 还在（可能卡死了） | 确认那个 pid 是上次的 `run_list.py`，结束它再跑；不要动别的 python |
| 一直 `ChapterSwipeToTheRightAndPlot`、找不到关卡 | 游戏不在关卡地图，或那一关还没解锁 | 退回关卡地图；前一关没过就先打前一关 |
| `BattleStartPre` 识别失败（`--here` 模式） | 游戏不在关卡详情页 | 进到详情页（右下「开始行动」）再跑 |
| `SubTaskError` 里是 `NotUsePrts` | 每关开头的容错检查，正常 | 不用管，后面有编队日志就行 |

## 编队失败（不扣理智）

| 日志 | 原因 | 处理 |
|---|---|---|
| `"why":"OperatorMissing","reason":"Unavailable","requirement_type":"skill_level"`，或 `Skill 1 level 7, require: 10` | 技能等级（专精）不够。**不是干员被占用**——别去查基建、训练室 | 换要求低的作业；用户同意就 `--ignore-requirements`（2026-11 TL-S 关这样打过）；只缺一人 `--support-usage 1` |
| `requirement_type` 是 `elite` / `level` / `module` | 精英化、等级、模组不够 | 同上 |
| `reason":"Missing"`，只缺一两个 | 用户没有这个干员 | 回 `match.py` 重挑；只缺一人可以借助战 |
| 所有干员都 Missing，日志里干员名是乱码 | 作业文件编码坏了 | `fetch_chosen.py` 重下 |
| `lower than any group requirement, stop match` 之后报一堆 Missing | 截图慢，滚动列表的残帧被当成到底了 | 设对 `MUMU_DIR` 重跑 |
| `Skill 2 not found in quick detection`、`Invalid overlap detected` | 同上，截图慢导致技能页拼接失败 | 同上 |
| `BattleQuickFormation` 反复找不到 | 编队页有弹窗 / 界面变了 | 截图看，用模拟器通道关掉弹窗，退回关卡地图重跑 |

## 战斗中

| 现象 | 原因 | 处理 |
|---|---|---|
| `理智不足`，OCR 到「是否花费…理智」 | 理智不够 | 用户同意后加 `--potion`；不同意就停，报告还差多少 |
| 打完两星（漏怪），`StageDrops-Stars-3` 匹配分只有 0.6 几 → `TaskChainError` | 作业没打成三星 | MAA 会中断整条列表。换一份作业重打这一关；剩下的关当新列表再跑 |
| `FightMissionFailed`，结算「理智返还」 | 作战失败，理智全额退回 | 同上；同一份作业不要连输两次 |
| `Group not found in combat data: <装置名>`（如 自爆榴弹、风雪之眼） | MAA 没有这个新装置的数据，部署它的动作落空 | 换不用这个装置的作业，或等 MAA 更新；`Unknown tile type: tile_trench` 这类地块告警本身不致命（同样有它的 S2 打过了） |
| 点完「开始行动 / 开始突袭」后日志不再动 | MaaCore 卡死 | 脚本 6 分钟没进展会自己停（退出码 4）；确认没有残留 python，截图看画面再重跑 |

## 核对

- 过关：该关 `StageDrops-Stars-3`（突袭 `StageDrops-Stars-Adverse`）+ `TaskChainCompleted`，没有 `TaskChainError`；再截图看节点标记。
- 真打的是突袭：日志里有 `ChangeToRaidDifficulty` 或 `BattleStartRaid`。
- MAA 自己的 `config/gui.json`、`gui.new.json` 不要动：这套脚本用 MaaCore 直连 + 独立 `user_dir`，不影响用户平时在 MAA 界面里的设置和日常队列。
