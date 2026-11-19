"""用 MAA 干员识别结果过滤作业：必选干员全有、每组至少有一个、精英化和等级够。

用法:
    py -3.12 match.py                 # 读 <COPILOT_WORK>\\ops\\*-list.json
    py -3.12 match.py act55side_s02   # 只看这一关

干员表（OperBoxData.json）只有精英化和等级：技能等级（专精）、模组、潜能对不上，
这里列成「待编队核对」，MAA 编队时才知道够不够（编队失败不扣理智）。
输出: 每关可用的候选（按赞踩和热度排），以及 <COPILOT_WORK>\\match_report.json
"""
import glob
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common  # noqa: E402

# 作业说明里出现这些字，多半要手动操作或额外条件，MAA 自己打不出来
MANUAL_HINTS = ("手动", "手操", "手切", "切换形态", "报纸", "需要升级", "建筑等级", "暂停", "不要挂机")


def load_box(maa):
    path = os.path.join(maa, "data", "OperBoxData.json")
    if not os.path.exists(path):
        _common.fail(f"没有 {path}：请用户在 MAA「小工具 → 干员识别」里识别一次")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not data.get("done"):
        _common.fail(f"干员识别没做完（done=false）：{path}")
    owned = {o["name"]: o for o in data.get("own_opers", []) if o.get("own")}
    age_h = (time.time() - os.path.getmtime(path)) / 3600
    print(f"干员表: {len(owned)} 名，{age_h:.0f} 小时前识别（{path}）")
    if len(owned) < 50:
        print("!! 干员不到 50 个，干员识别可能没跑完整")
    if age_h > 24 * 7:
        print("!! 干员表一周以上没更新，练度可能变了；请用户重新识别")
    return owned


def gap(box_op, req):
    elite, level = req.get("elite", 0) or 0, req.get("level", 0) or 0
    if box_op["elite"] < elite or (box_op["elite"] == elite and box_op["level"] < level):
        return f"E{box_op['elite']}-{box_op['level']}<要E{elite}-{level}"
    return None


def unverifiable(oper):
    req = oper.get("requirements") or {}
    parts = []
    if (req.get("skill_level") or 0) > 7:
        parts.append(f"{oper.get('skill', '?')}技能专{req['skill_level'] - 7}")
    if (req.get("module") or -1) > 0:
        parts.append(f"模组{req['module']}")
    return f"{oper['name']}({'/'.join(parts)})" if parts else None


def main():
    owned = load_box(_common.maa_dir())
    work = _common.work_dir()
    only = [a for a in sys.argv[1:] if not a.startswith("--")]
    report = {}
    for path in sorted(glob.glob(os.path.join(work, "ops", "*-list.json"))):
        stage = os.path.basename(path)[: -len("-list.json")]
        if only and stage not in only:
            continue
        with open(path, encoding="utf-8") as f:
            items = json.load(f)["data"]["data"]
        rows = []
        for item in items:
            c = json.loads(item["content"])
            opers = c.get("opers", [])
            groups = {g["name"]: [o["name"] for o in g.get("opers", [])] for g in c.get("groups", [])}
            missing = [o["name"] for o in opers if o["name"] not in owned]
            missing_groups = [g for g, ms in groups.items() if not any(m in owned for m in ms)]
            gaps = [f"{o['name']}({g})" for o in opers if o["name"] in owned and (g := gap(owned[o["name"]], o.get("requirements") or {}))]
            details = (c.get("doc") or {}).get("details") or ""
            rows.append({
                "id": item["id"], "title": (c.get("doc") or {}).get("title"),
                "difficulty": c.get("difficulty"), "like": item.get("like") or 0, "dislike": item.get("dislike") or 0,
                "views": item.get("views") or 0, "hot": item.get("hot_score") or 0,
                "opers": [o["name"] for o in opers], "groups": list(groups),
                "missing": missing, "missing_groups": missing_groups, "gaps": gaps,
                "check_in_formation": [u for o in opers if (u := unverifiable(o))],
                "manual_hints": [h for h in MANUAL_HINTS if h in details],
            })
        usable = [r for r in rows if not r["missing"] and not r["missing_groups"]]
        usable.sort(key=lambda r: (bool(r["gaps"]), bool(r["manual_hints"]), r["dislike"] > r["like"], -r["like"], -r["hot"]))
        report[stage] = usable
        print(f"\n== {stage}: {len(rows)} 份，干员都有的 {len(usable)} 份 ==")
        for r in usable[:6]:
            print(f"  id={r['id']} 赞{r['like']}/踩{r['dislike']} 浏览{r['views']} diff={r['difficulty']} 「{r['title']}」")
            print(f"     干员 {r['opers']} 组 {r['groups']}")
            if r["gaps"]:
                print(f"     练度不够: {r['gaps']}")
            if r["check_in_formation"]:
                print(f"     待编队核对: {r['check_in_formation']}")
            if r["manual_hints"]:
                print(f"     说明里提到: {r['manual_hints']}（看 doc.details，要手动操作的不选）")
        if not usable:
            for r in sorted(rows, key=lambda r: len(r["missing"]))[:3]:
                print(f"  (缺人) id={r['id']} 缺 {r['missing']} 缺组 {r['missing_groups']}")
    out = os.path.join(work, "match_report.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    print(f"\n候选清单 -> {out}")


if __name__ == "__main__":
    main()
