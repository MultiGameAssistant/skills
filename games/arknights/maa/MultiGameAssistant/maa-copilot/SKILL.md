---
name: maa-copilot
description: 用 MAA 自动战斗（抄作业）打明日方舟的活动关、突袭、剿灭：按 MAA 干员识别结果从作业站挑作业，用本技能自带的脚本让 MaaCore 直接打，再截图核对三星和突袭标记。用户说「把方舟新出的关打一下」「抄作业打 EX / S 关」「自动战斗过活动」「按我的干员找作业」时使用；只清日常、刷理智用 maa 技能。
---

# MAA 抄作业打关卡

链路：**干员表 → 挑作业 → 下载完整作业 → 游戏停在关卡地图 → `run_list.py` → 截图核对**。每一步都有脚本（本技能文件夹的 `scripts/`），**用它们，不要另写运行器**。2026-11 有一晚自己写的运行器漏了 MuMu 截图增强：截图从 20ms/帧 变成 1.5 秒/帧，编队认错干员、部署慢半拍，连输五场，原因还先后猜成了「练度不够」「干员被占用」「MAA 不认地块」，全都不对。

## 0. 准备

- 用 `py -3.12` 跑脚本（3.11 载入 `MaaCore.dll` 会报 `WinError 1114`）。没有 3.12 就请用户装，不要换别的路子。
- 下面命令里的 `scripts\…` 在本技能的文件夹里（加载技能时会给出它的目录），命令里写完整路径；工作目录用 `COPILOT_WORK`。
- 每条命令前设好环境变量（PowerShell 里 `$env:MAA_DIR = '...'`）：

| 变量 | 填什么 |
|---|---|
| `MAA_DIR` | `script_list` 里 id=maa 的 `dir` |
| `COPILOT_WORK` | 工作目录，例如工作区下的 `copilot-<日期>`；候选作业和 MaaCore 日志都在这里，不要放进 MAA 目录 |
| `ADB_ADDRESS` | `emulator_status` 里的 ADB 地址（MuMu 12 实例 0 一般是 `127.0.0.1:16384`） |
| `MUMU_DIR` | MuMu 12 的安装目录（有 `nx_device` 的那层，例如 `E:\Program Files\Netease\MuMu`，不是 `nx_main`）。不填时脚本从 MAA 配置里找，找不到会打印 `!!` 告警 |
| `CLIENT_TYPE` | B 服填 `Bilibili`，官服不用填 |

- 先确认没人在用这台模拟器：`script_runs`（MAA 日常在跑就等它跑完）、`pipeline_status`（快要开始的任务会关模拟器的，先别打）。`run_list.py` 有运行锁，报「已经有一个抄作业在跑」时先看那个进程是不是卡死了。
- **模拟器只用模拟器通道**：截图 `screen_capture target=emulator`，点按 `screen_tap target=emulator`，返回 `screen_key target=emulator key=back`，坐标就用截图上的像素（工具会换算成模拟器分辨率）。不要用桌面鼠标、窗口点击（用户明确反对过）；也不要自己 `adb shell input tap`——截图是缩小过的（例如 1280×720 对 2560×1440），截图坐标直接拿去 tap 会点偏。
- 战斗只交给 MAA，不手动打。

## 1. 干员表

读 `<MAA_DIR>\data\OperBoxData.json`（MAA「小工具 → 干员识别」的结果），`match.py` 会检查 `done`、人数和识别时间。太旧就请用户在 MAA 里点一次干员识别（MAA 是桌面程序，不要替用户去点）。

干员表**只有精英化和等级**，没有技能等级（专精）、模组。作业对这两项的要求只能在 MAA 编队时核对，编队不过不扣理智。

## 2. 挑作业

先弄清关卡代号和显示名。显示名是地图节点上的字（`TL-S-1`）；代号是作业站和作业文件里用的（`act55side_s01`，EX 关 `act55side_ex01`）。在 `<MAA_DIR>\resource` 里 grep 显示名能找到代号；不要照搬上一期活动的前缀。

```powershell
py -3.12 scripts\fetch_ops.py act55side_s01 act55side_s02    # 作业列表 → COPILOT_WORK\ops\
py -3.12 scripts\match.py                                     # 按干员表筛，打印每关候选
```

- 选「练度不够」为空、赞多踩少的；赞比踩少的不选。
- 「说明里提到：手动…/报纸…」的，看一眼作业说明，要手动切形态、要额外养成的不选。
- 「待编队核对」列的是专精和模组要求，用户可能不够；每关多挑两三份备选。

## 3. 下载完整作业

```powershell
py -3.12 scripts\fetch_chosen.py act55side_s01=110074:TL-S-1 act55side_s02=110081:TL-S-2
```

- 写到 `<MAA_DIR>\config\copilot\<显示名>.json`；同一关的备选另起名（`TL-S-2-b`），要打时再复制成 `TL-S-2.json`。突袭要用另一份作业时存成 `TL-S-3-raid.json`。
- **作业只用这个脚本下载**：作业站列表里的 `content` 没有 actions；PowerShell `Invoke-WebRequest` 再写文件会把中文写成乱码（`å£èé…`），MAA 就把所有干员报成 Missing。

## 4. 跑

1. 用模拟器通道把游戏导航到**活动的关卡地图**，截图能看到要打的节点名字。不是关卡详情页、也不是编队页。用 `screen_key key=back` 往回退，最多退几次，每步截图确认。
2. 后台跑（一场 5～8 分钟），隔两三分钟看一次输出；不要在前台一直等，也不要自己写等待循环：

```powershell
py -3.12 scripts\run_list.py 1 2 --prefix TL-S            # 普通
py -3.12 scripts\run_list.py 1 2 --prefix TL-S --raid     # 突袭（先普通三星，突袭才解锁）
```

| 参数 | 作用 | 什么时候用 |
|---|---|---|
| `--ignore-requirements` | MAA「忽略干员属性要求」：专精、模组不够也照样编队 | 编队报技能等级不够、用户同意后。2026-11 的 S 关就是靠它打过的 |
| `--support-usage 1 [--support-name 干员]` | 只缺一名干员时借助战 | 突袭不能用 |
| `--potion` | 理智不够时用理智药 | 用户同意后；脚本不会碎石 |
| `--here --file 文件名.json` | 单作业模式，不导航 | 剿灭、危机合约这类地图上没有节点名的：先停在关卡详情页（右下「开始行动」），突袭先在详情页切好 |

- 活动关逐个解锁（S-1 通关后地图上才出现 S-2）：前一关没过，后面的不要放进同一条列表，MAA 会在地图上一直滑屏找不到。
- 作业 `difficulty` 3 是普通突袭通用，同一个文件 `--raid` 就行；1 只能普通、2 只能突袭，脚本会拦住。
3. 看脚本最后的输出：`结束: 成功/失败/卡住`、关键日志行、截图耗时。**截图耗时上百毫秒或出现 `mumu_handle_=0`，这次的结果不算数**——先把 `MUMU_DIR` 设对再重跑，不要据此判断作业或练度。

## 5. 核对、收尾

- 过关的证据：输出里该关有 `StageDrops-Stars-3`（突袭 `StageDrops-Stars-Adverse`）和 `TaskChainCompleted`，没有 `TaskChainError`；再 `screen_capture target=emulator` 看节点三星 / 突袭标记。只有 `TaskChainCompleted` 不算。
- 理智：编队没过不扣；打输了结算页「理智返还」全额退回。所以重试花的是时间不是理智——但同一份作业输两次就换作业，不要原样重复。
- 卡住（退出码 4）：脚本已经停了。确认没有残留的 python 进程（运行锁里的 pid），截图看游戏停在哪，退回关卡地图再跑。
- 交回：每关作业 id、普通 / 突袭、结果、理智变化、用了什么参数（忽略要求、助战、药）。`game_record` 记活动进度。

## 出错时

先查 `references/troubleshooting.md`，**对上了就照做，不要自己另猜原因**。最常见的：

| 看到 | 是什么 | 怎么办 |
|---|---|---|
| `OperatorMissing`、`reason: Unavailable`、`requirement_type: skill_level` | 技能等级（专精）不够，**不是干员被占用** | 换要求低的作业；用户同意就 `--ignore-requirements`；只缺一人 `--support-usage 1` |
| 所有干员都 Missing，日志里干员名是乱码 | 作业文件编码坏了 | `fetch_chosen.py` 重下 |
| 截图约 1 秒/帧；编队「lower than any group requirement, stop match」后报一堆缺员；部署慢、漏怪 | 截图增强没开 | 设对 `MUMU_DIR` 重跑；MAA 自己的模拟器设置不用改 |
| `Group not found in combat data: <装置名>` | MAA 还没有这个新装置的数据，作业里部署它的动作会落空 | 换一份不用这个装置的作业；或等 MAA 更新（`script_releases`） |

## 派子 agent 时

- 一个子 agent 做完一整段（导航 → 跑一条列表 → 核对），任务里写清：先加载本技能、上面那几个环境变量的值、作业文件名、关卡号、用户同意了哪些参数。不要每一步派一个，也不要每隔一会儿发消息催进度——脚本跑完它自然会交回。
- 子 agent 刚启动就异常退出、连续两次：别再派第三个，告诉用户执行通道出了问题。
