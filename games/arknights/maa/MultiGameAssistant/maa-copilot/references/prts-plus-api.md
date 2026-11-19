# 作业站（prts.plus）接口

网页 https://prts.plus （单份作业 `https://prts.plus/copilot/<id>`，用户要网址时给这个）；接口基址 `https://prts.maa.plus`，不用登录。

## 关卡的作业列表

```
GET /copilot/query?limit=80&page=1&levelKeyword=<关卡代号>&orderBy=hot&desc=true
```

- `levelKeyword` 填**关卡代号**（`act55side_s02`），不是显示名。
- `orderBy`：`hot`、`views`、`id`（最新）。
- 返回 `{status_code, data:{total, has_next, data:[...]}}`；每项有 `id`、`like`、`dislike`、`views`、`hot_score`、`rating_level`、`uploader`、`upload_time`、`content`。
- **`content` 被裁剪过，没有 `actions`**。拿它直接喂 MAA 是空作业，看着「跑完了」其实什么也没做。

## 单份作业

```
GET /copilot/get/<id>
```

`data.content` 是完整 JSON 字符串，含 `actions`。`fetch_chosen.py` 就是读这个。

## 作业 JSON 关键字段

```json
{
  "stage_name": "act55side_s02",
  "difficulty": 3,
  "opers":  [{"name": "圣聆初雪", "skill": 2,
              "requirements": {"elite": 2, "level": 60, "skill_level": 10, "module": -1}}],
  "groups": [{"name": "奶盾", "opers": [{"name": "黍"}, {"name": "塞雷娅"}]}],
  "doc": {"title": "...", "details": "作者写的说明：要不要手动操作、要什么报纸等级"},
  "actions": [{"type": "Deploy", "name": "遥", "location": [4, 3], "direction": "Left"}]
}
```

- `difficulty`：1 普通 / 2 突袭 / 3 两者通用（大多数）。
- `opers` 必上；`groups` 每组挑一个。
- `skill_level`：1～7 是技能等级，8/9/10 是专精一/二/三。`module`：-1 不要求，1、2… 是第几个模组。干员识别的结果里没有这两项。
- `actions` 为空 → 不是可用作业。

## 关卡代号和显示名

| 用在哪 | 写法 | 例子 |
|---|---|---|
| `levelKeyword`、作业里的 `stage_name` | 代号 | `act55side_s02`、`act55side_ex08` |
| MAA 在地图上找关（`copilot_list` 的 `nav_name_override`） | 显示名 | `TL-S-2` |
| 作业文件名（`run_list.py` 按它找） | 显示名 | `TL-S-2.json`、`TL-S-2-raid.json` |

SideStory 的代号：`act<期号>side_<关号>`，EX 关 `..._ex01`，S 关 `..._s01`。期号和前缀每期都变：在 `<MAA_DIR>\resource` 里 grep 显示名（`"code": "TL-S-1"` 附近有 `stageId`），或看 PRTS 的活动页；不要照搬上一期。
