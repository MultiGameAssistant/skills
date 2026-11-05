---
name: maa
description: MAA（MaaAssistantArknights，明日方舟小助手）的安装、运行、设置和报错处理，以及用作业站的作业打剿灭、活动关卡。用户提到 MAA、明日方舟日常、刷理智、基建、公招、剿灭、抄作业，或 MAA 运行失败、卡在「开始唤醒」时使用。
---

# MAA（明日方舟）

- 仓库：MaaAssistantArknights/MaaAssistantArknights；Windows 用 `MAA-v<版本>-win-x64.zip` 发布包。
- 运行依赖：VC++ 运行库 x64（发布包自带 .NET）；需要安卓模拟器，通过 ADB 操作，不占用鼠标键盘，可以和前台脚本并行。

## 运行

- 任务 `daily`：按 MAA 当前配置里**已勾选的任务队列**运行一遍。运行时会临时修改 `config/gui.json` 和 `config/gui.new.json`（启动后直接运行、连接地址设为模拟器的 ADB 地址），看到「任务已全部完成」后关闭 MAA，并把这两个配置文件还原。
- 用法：`script_run`，`id` 为脚本库里的 MAA，`task` 为 `daily`。用户说「清一下方舟日常」「刷理智」都对应这个任务。
- 前提：本地配置里要勾选好任务（例如刷哪一关、用不用理智药）。还没设置过时，用 `script_settings` 打开 MAA 的设置界面让用户配好任务、关掉窗口，设置会存进本地配置。
- 想换关卡、理智药数量等：用 `script_settings` 让用户在 MAA 界面里改，或先 `script_config_get` 读 `config/gui.new.json`，找到对应的键再用 `script_config_set` 改本地配置。`daily` 任务本身没有关卡参数。
- 不同账号、不同的任务组合可以存成几份配置（`script_profiles`），运行时用 `profile` 选一份。
- 运行中看进度用 `script_runs`（带 run_id）。**不要自己再开 MAA.exe**：平台正在拉起 MAA 时手动再开一个，第二个只会提示「Secondary launch detected」然后退出，这次运行会被记成「没有看到完成标志」的失败。

## 设置

- 配置分两份：原项目里的配置（用户自己打开脚本时用）和本软件的**本地副本**（通过 agent 运行时用）。agent 只改本地副本，原项目配置不变。
- 配置文件：`config/gui.json`、`config/gui.new.json`。用 `script_config_get` 查看、`script_config_set` 修改本地副本；`script_config_status` 能看出用户是否在 MAA 里改过原项目设置，需要时经用户同意用 `script_config_import` 导入。不要直接写脚本目录里的文件。
- 安装、更新、回滚、检查环境用 `script_*` 工具；不要修改 MAA 的程序文件。
- MAA 的「完成后动作」勾了关闭模拟器时，每次跑完模拟器都会关掉，下一个用模拟器的任务要冷启动。流水线里 MAA 后面还排着模拟器任务时提醒用户。

## 运行失败时

按顺序查，前一步已经能说明原因就不用往下：

1. `script_run_log`（run_id，`levels: ["error", "warning"]`）看报错，再用 `search` 搜出错前后，例如 `/开始任务|任务出错|任务已全部完成/`。
2. 平台日志说不清时看 MAA 自己的日志（只读）：`debug/gui.log` 是任务进度和版本更新记录，`debug/asst.log` 是识别细节。两个都是 UTF-8，PowerShell 里用 `Get-Content -Encoding UTF8 -Tail 200`，否则中文是乱码。
3. 看画面：`screen_capture`（target=emulator）。不要用 PowerShell 跑 `adb exec-out screencap -p > 文件`，图片会被改坏。

常见原因：

| 日志里看到 | 原因 | 怎么办 |
|---|---|---|
| 「开始唤醒」重试几十次后「任务出错: 开始唤醒」，后面的任务也什么都认不出 | 游戏刚更新改了界面，MAA 版本太旧（2026-11 的 26.11.1 主界面改版就是这样，MAA v6.21 才适配） | `script_changelog` 或 `script_releases`（repo=MaaAssistantArknights/MaaAssistantArknights）确认新版写了适配，再 `script_update`（id=maa）。本地导入的 MAA 也是在原目录更新：先备份，可 `script_rollback` 撤销，会先请用户确认。然后 retry。**不要**手动解压 MAA 下载好的 `MirrorChyanAppv*.zip` 去覆盖。 |
| gui.log 里 MAA 发现了新版本、也下载了更新包，但版本号没变 | MAA 设置里「自动安装更新包」关着，只下载不安装 | 同上用 `script_update` 装上；告诉用户可以在 MAA「设置 → 更新设置」里打开自动安装更新包 |
| 运行到一半 MAA 自己退出又启动 | MAA 自动更新后重启 | 等它更新完，retry |
| 画面一直停在模拟器桌面，游戏没打开 | 游戏没启动起来 | `game_launch`（game=arknights）。报「不知道游戏在模拟器里的包名」时，请用户在脚本页「启动游戏」里填包名：官服 `com.hypergryph.arknights`，B 服 `com.hypergryph.arknights.bilibili` |
| 「连接失败」「adb」，或截图报 device offline / not found | 模拟器没开好、ADB 地址变了 | `emulator_status`；没在运行就 `emulator_start`，然后 retry |
| 理智作战（剿灭）报 `UnableToAgent2` | 多半是当期剿灭关卡还没打满 400 杀，代理指挥没解锁 | 告诉用户先手动打一次（或用下面的作业打），之后 MAA 才能代理 |
| 停在某个界面不动 | 弹窗、公告、更新提示 | 截图处理后 retry；要输入账号密码或验证码时停下，交给用户 |

## 用作业打关卡（自动战斗）

剿灭没解锁代理、活动关卡、危机合约这类没法代理的关卡，可以用作业站的作业让 MAA 自动打。

1. 找作业：作业站 https://prts.plus 。也可以直接读接口（不用登录）：
   - `https://prts.maa.plus/copilot/query?levelKeyword=<关卡中文名>&orderBy=hot&desc=true&limit=20`，每项的 `content` 是作业 JSON 文本，里面的 `stage_name` 是关卡代号（例如灰石剧场 `camp_r_34`）。
   - 列表里的作业不带完整操作，单份要 `https://prts.maa.plus/copilot/get/<作业 id>`。
2. 挑作业：
   - 作业里的干员（`opers`）用户都有，`groups` 每组至少有一个。
   - `requirements` 里的精英化和技能等级够。技能等级要求 10 是专精三级，用户没有就容易漏怪（剿灭打不满 400）。
   - 同样能用的，选 `rating_level` 和 `hot_score` 高的。
   - 用户的干员和练度可以在 MAA「小工具 → 干员识别」里识别，结果在 `data/OperBoxData.json`。
3. 打：游戏要停在关卡详情页（右下有「开始行动」）。请用户在 MAA「自动战斗」页粘贴 `maa://<作业 id>` 后开始；打完看结果（剿灭看击杀数是不是 400/400），没满就换一份作业。
4. 打之前确认没有会关掉模拟器的任务快开始了（`pipeline_status`、`script_runs`），不然打到一半模拟器被关，这次作战作废。
