---
name: game-endfield
description: 明日方舟：终末地的活动和进度：活动时间来自 SRA 公共 API（必要时看官网新闻），游戏画面读剩余时间和没做完的事。用户问终末地有什么活动、还剩几天时使用。
---

# 明日方舟：终末地（官服）

- 活动时间、版本和每个活动的说明由插件每天从 SRA 公共 API 读（`game_sites_refresh` 可以马上刷新），不用模型。那里没有的（比如刚发的公告），再用 `web_fetch` 看官网新闻 https://endfield.hypergryph.com/news ，从公告里找活动名和起止时间，用 `game_record` 记下（source=site，写明 `url`）。
- 游戏可能是 PC 窗口，也可能在模拟器里（看 MaaEnd 的实例用的是哪个控制器）。PC 版先 `window_list`（filter 填「Endfield」或「终末地」）找窗口，再 `screen_capture`（target=window）；模拟器里用 target=emulator。MaaEnd 正在跑时（`script_runs`）先等它结束，期间不要点击。
- 游戏没开时用 `game_launch`（game=endfield）。PC 版会打开鹰角启动器，启动器里还要点「开始游戏」：截图找到按钮点一下，等进到主界面再看。

## 进到活动页（只看，不花东西）

1. 截图。有弹窗先关掉。
2. 在主界面找写着「活动」的入口图标，点开后左边是活动列表。
3. 逐个读：活动名、剩余时间、还没领的奖励和没完成的任务。

只点开页面、切换页签、关闭弹窗，**不要兑换、不要抽卡、不要花任何货币**。读完退回主界面。

## 记录

`game_record`（game=endfield，source=screen）每个活动一条：剩余时间照原文填 `remaining`，进度填 `progress`，没做完的写进 `todo`。

## 和上面说的不一样时

- 找不到活动入口：截图看清楚再找，不要连续乱点；三次找不到就停下，告诉用户卡在哪个界面。
- 窗口找不到：先 `window_list` 看终末地窗口的实际标题，再用那个标题截图。
- 插件会拿 `remaining` 和 SRA 的结束时间核对，所以照界面原文填，不要自己换算。
- 发现了新的路线或写法，读完后告诉用户，用户可以用 `/技能` 存下来。
