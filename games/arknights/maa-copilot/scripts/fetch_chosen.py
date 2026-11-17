"""下载选中作业的完整 JSON（含 actions），写进 MAA 的 copilot 目录。

用法:
    py -3.12 fetch_chosen.py act55side_s01=110074:TL-S-1 act55side_s02=110081:TL-S-2
    py -3.12 fetch_chosen.py act55side_s03=110131:TL-S-3-raid      # 突袭专用的另一份

每个参数: <关卡代号>=<作业 id>:<文件名>。文件名用关卡显示名（run_list.py 按它找文件、按它在地图上找关）；
突袭用另一份作业时文件名加 -raid。会核对 actions 非空、stage_name 对得上，并读回确认中文没乱码。
**下载作业只用这个脚本**：PowerShell 的 Invoke-WebRequest + 写文件会把中文写坏，MAA 就认不出任何干员。
"""
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common  # noqa: E402

BASE = "https://prts.maa.plus"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args or any("=" not in a or ":" not in a for a in args):
        _common.fail(__doc__)
    copilot = os.path.join(_common.maa_dir(), "config", "copilot")
    os.makedirs(copilot, exist_ok=True)
    for arg in args:
        stage, rest = arg.split("=", 1)
        cid, name = rest.split(":", 1)
        content = get(f"{BASE}/copilot/get/{cid}")["data"]["content"]
        parsed = json.loads(content)
        if parsed.get("stage_name") != stage:
            _common.fail(f"{cid} 的 stage_name 是 {parsed.get('stage_name')}，不是 {stage}")
        if not parsed.get("actions"):
            _common.fail(f"{cid} 没有 actions，换一份作业")
        path = os.path.join(copilot, f"{name}.json")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(parsed, f, ensure_ascii=False, indent=1)
        with open(path, encoding="utf-8") as f:
            back = json.load(f)
        names = [o["name"] for o in back.get("opers", [])]
        if names != [o["name"] for o in parsed.get("opers", [])]:
            _common.fail(f"{path} 读回来的干员名不一致：{names[:3]}")
        print(f"{stage} <- id={cid} diff={parsed.get('difficulty')} actions={len(parsed['actions'])} 干员={names} -> {path}")


if __name__ == "__main__":
    main()
