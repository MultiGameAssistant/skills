# MultiGameAssistant 技能库

[MultiGameAssistant](https://github.com/haaahhhis/MultiGameAssistant) 的游戏和脚本技能。软件只自带维持基本功能的核心技能（游戏资讯、读网页、分析脚本、编排流水线），某个游戏怎么看活动、某个脚本怎么装怎么跑，放在这里，用户在软件的「技能 → 技能库」里按需下载。

## 有哪些

| 技能 | 是什么 | 游戏 | 脚本 |
|---|---|---|---|
| `game-arknights` | 明日方舟：活动页、剩余时间、活动商店和任务 | arknights | maa |
| `game-endfield` | 明日方舟：终末地：活动时间来源、游戏里的剩余时间和没做完的事 | endfield | maaend |
| `game-starrail` | 崩坏：星穹铁道：活动页、剩余时间、每日实训和模拟宇宙积分 | starrail | march7th |
| `maa` | MAA（明日方舟小助手）的安装、运行与设置 | arknights | maa |
| `maaend` | MaaEnd（终末地自动化）的安装与运行 | endfield | maaend |
| `march7th` | 三月七小助手（星穹铁道自动化）的安装与运行 | starrail | march7th |

## 软件怎么用它

- 打开「技能 → 技能库」时读这个仓库（整个仓库打包成一个 zip 下载，不需要装 git；走「设置 → 脚本安装」里的下载镜像），一天最多读一次，点「检查更新」立即读。
- 按你关注的游戏、装了的脚本推荐技能，你点「下载」才会下载。下载的技能放在软件的数据目录（`skill-hub/skills/<技能名>/`），agent 马上就能用。
- 下载的技能可以改。仓库里有新版本时：
  - 你没改过：直接换成新版本；
  - 你改过：不会覆盖，页面上写「你改过 · 有新版」，可以看两边哪里不同，再选「保留我的」「用新版」（你的那份留作备份）或「让 agent 合并」。
- 你自己保存的技能（agent 的 `skill_save`、你自己的技能文件夹）不受这个仓库管，和这里同名时以你的为准，这里的那个不会下载。
- 软件自带的核心技能受保护，不能修改，随软件更新。

## 目录和格式

```
index.json                 技能清单（软件按它列出技能）
games/<游戏 id>/SKILL.md    一个游戏的技能
scripts/<脚本包 id>/SKILL.md 一个脚本的技能
```

每个技能一个文件夹，里面是 `SKILL.md`（需要的话可以放图片等附带文件，SKILL.md 里用相对路径引用）。`SKILL.md` 以 frontmatter 开头：

```markdown
---
name: game-arknights
description: 一两句话：做什么，用户说什么时用（agent 靠它决定什么时候用这个技能）。
---

# 正文：适用场景、一步一步怎么做、怎么判断成功、注意事项
```

`index.json` 里每一项：

| 字段 | 必填 | 说明 |
|---|---|---|
| `name` | 是 | 技能名，和 SKILL.md 的 `name` 一致；小写字母、数字、短横线。游戏技能用 `game-<游戏 id>` |
| `path` | 是 | 技能文件夹在仓库里的路径 |
| `title` | 否 | 页面上显示的名字 |
| `kind` | 否 | `game`、`script` 或 `general` |
| `games` | 否 | 适用的游戏 id（软件游戏包的 id，例如 `arknights`），用来推荐 |
| `scripts` | 否 | 适用的脚本 / 脚本包 id（例如 `maa`），用来推荐 |

没有 `index.json` 时，软件把仓库里每个 `SKILL.md` 都当作一个技能（描述取自 frontmatter）。

## 贡献

- 新游戏：`games/<游戏 id>/SKILL.md`，写清楚活动、任务、邮件在哪个界面，剩余时间怎么写，哪些操作不能做（不花资源、不点购买）。
- 新脚本：`scripts/<脚本包 id>/SKILL.md`，写安装要注意的、常用任务、配置文件在哪、常见报错怎么处理。
- 改了已有技能就直接改对应的 SKILL.md，并在 `index.json` 里保持条目一致；用户那边会收到「有新版」。
- 只写有确切出处的做法，不放账号、密码、CDK 等私人信息。
