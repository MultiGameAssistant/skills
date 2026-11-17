"""拉作业站几个关卡的作业列表（列表里的 content 没有 actions，只用来筛选）。

用法:
    py -3.12 fetch_ops.py act55side_s01 act55side_s02
    py -3.12 fetch_ops.py act55side_s02 --order views     # 换个排序（hot 默认 / views / id 最新）

关卡代号不是显示名：SideStory 是 act<期号>side_<关>（EX 关 ..._ex01，S 关 ..._s01）。
不知道代号就在 <MAA_DIR>\\resource 里 grep 显示名（"code": "TL-S-1" 附近的 stageId）。
输出: <COPILOT_WORK>\\ops\\<代号>-list.json（再拉一次会合并去重）
"""
import json
import os
import sys
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common  # noqa: E402

BASE = "https://prts.maa.plus"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    order = "hot"
    if "--order" in sys.argv:
        order = sys.argv[sys.argv.index("--order") + 1]
    stages = [a for a in sys.argv[1:] if not a.startswith("--") and a != order]
    if not stages:
        _common.fail(__doc__)
    out = os.path.join(_common.work_dir(), "ops")
    os.makedirs(out, exist_ok=True)
    for stage in stages:
        query = urllib.parse.urlencode({"limit": 80, "page": 1, "levelKeyword": stage, "orderBy": order, "desc": "true"})
        data = get(f"{BASE}/copilot/query?{query}")
        items = data["data"]["data"]
        path = os.path.join(out, f"{stage}-list.json")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                old = json.load(f)["data"]["data"]
            seen = {i["id"] for i in items}
            items += [i for i in old if i["id"] not in seen]
            data["data"]["data"] = items
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print(f"{stage}: 作业站共 {data['data'].get('total')} 份，本地 {len(items)} 份 -> {path}")
        if not items:
            print(f"  没有作业：代号对吗？（{stage}）")


if __name__ == "__main__":
    main()
