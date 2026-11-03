---
name: script-troubleshooting
description: 脚本运行出错、卡住、没跑完时怎么查、该用哪些工具、哪些做法会白费功夫。处理脚本异常（「干预」会话）、用户说「脚本失败了」「日常没跑完」「帮我看看为什么报错」、或要 /诊断 时使用；具体脚本的常见报错看那个脚本自己的技能。
---

# 脚本出错排查

先用本软件的工具查，它们比自己用 PowerShell 翻文件快、结果也更准。下面的顺序是实际排查里最省步骤的；前一步已经能说明原因就不用往下。

## 1. 看这次运行

1. `script_runs`（带 `run_id`）：状态、结束原因、最后几行日志。异常记录和干预提示里都有 run_id。
2. `script_run_log`：完整日志，包括脚本重启之前的部分。
   - 先 `levels: ["error", "warning"]` 只看问题，再用 `search` 搜出错前后（可以写 `/正则/`），或用 `from_line` 往前后翻。
   - 一次最多 500 行，别一页页从头读。
3. 同一个任务前几天的运行也看一下（`script_runs` 带 `id`）：从哪天开始失败、每次失败的位置是不是一样。每次都停在同一处，说明重跑解决不了。

## 2. 看画面和窗口

- `screen_capture`：模拟器用 `target=emulator`，PC 游戏用 `target=window` 加窗口标题里的一段字（不知道标题就先 `window_list`，可以用 `filter` 过滤）。窗口被挡住也能截。
- 要把截图发给用户时加 `send_to_user: true`，不要自己存文件再贴路径。
- 报错框可能藏在别的窗口后面：`window_list` 会标出对话框和被挡住的窗口。
- **不要**用 PowerShell 跑 `adb exec-out screencap -p > 文件`：Windows PowerShell 5.1 的 `>` 会把图片字节改坏，之后读图报「Unsupported or malformed image data」。实在要用 adb，就先 `adb shell screencap -p /sdcard/s.png`，再 `adb pull /sdcard/s.png <本地路径>`。
- 模拟器截图报 `device offline` 或 `not found`：先 `emulator_status`，没在运行就 `emulator_start`，不要自己反复重启 adb。

## 3. 看脚本自己的日志

平台日志说不清时，再读脚本目录里它自己的日志文件（位置写在各脚本的技能里，例如 MAA 的 `debug/gui.log`）：

- 只读不改。用文件读取工具，或 `Get-Content -Encoding UTF8 -Tail 200`；不加 `-Encoding UTF8` 中文会是乱码。
- 只读最后一段，再按关键字筛（`Select-String`）。不要整个文件读进来。
- 等脚本往下跑时，隔一两分钟用 `script_runs` 看一次就行，不要在 PowerShell 里写几分钟的等待循环：干预会话只有 15 分钟。

## 4. 判断原因、动手

| 现象 | 多半是 | 用什么 |
|---|---|---|
| 游戏刚更新后，脚本认不出界面、在第一步反复重试 | 脚本版本太旧 | `script_changelog` 看新版有没有写「适配」，`script_update` 更新（本地导入的脚本也能更新：在原目录更新，先备份，`script_rollback` 可撤销，会先请用户确认）。不要自己解压更新包覆盖文件。 |
| 缺运行库、启动就闪退 | 环境 | `script_env_check`，再 `script_env_fix` |
| 游戏没开、停在桌面或启动器 | 游戏没启动起来 | `game_launch`；启动器要点「开始游戏」就截图点一下 |
| 弹窗、公告、更新提示、掉线 | 游戏状态 | `screen_capture` 看清楚，`screen_tap` / `screen_key` 处理，每步都重新截图确认 |
| 每次都在同一处失败，游戏和配置都正常 | 脚本自己的问题 | 查新版更新日志；没修就 give-up，把失败位置和版本告诉用户 |
| 改哪项设置能绕过 | 配置 | `script_config_get` 读、`script_config_set` 改本地副本；不要直接写脚本目录里的文件 |

## 5. 重跑之前

- 先确认原因已经排除。会消耗游戏资源的任务（体力、理智）失败一次就白花一次，原因没排除就不要 retry，选 give-up 并写清楚要用户做什么。
- 确认旧进程已经结束（`script_runs` 的状态，必要时 `script_stop`）。旧进程挂着时重跑，脚本会报「已经在运行」。
- 不要自己用 PowerShell 启动脚本程序：平台启动时它会再开一个，第二个通常直接退出，平台会把这次记成失败。用 `script_run`，或在干预会话里用 `intervention_done(retry)` 让平台重新运行。

## 别白费功夫

- 本软件装好后**没有源代码**（没有 `packages\`、`apps\` 这些目录），不要去搜它的代码。要查软件的数据，数据目录在 `%LOCALAPPDATA%\MultiGameAssistant\adg\data`（从源码运行的开发版是 `MultiGameAssistant-dev`）。
- `grep` 的规则是 ripgrep 正则：`?`、`(`、`[` 这些要转义（`\?`），或者改搜纯文字。
- 干预会话里没有人回答 `ask_user_question`：自己判断，要用户做的事写进 `intervention_done` 的 summary。普通对话里提问时至少要有一个问题。
- 干预会话最后一定要调用 `intervention_done`。只写文字不调用，这次干预会一直挂到超时。
