"""多作业模式跑活动关：MAA 按地图上的关卡名找关、编队、开打，一条列表里几关连着打。

前提：游戏停在活动的**关卡地图**（能看到要打的节点，节点上写着 TL-S-1 这种名字）。
用法:
    py -3.12 run_list.py 1 2 --prefix TL-S                      # 普通
    py -3.12 run_list.py 1 2 --prefix TL-S --raid               # 突袭
    py -3.12 run_list.py 2 --prefix TL-S --support-usage 1      # 只缺一名干员时借助战
    py -3.12 run_list.py 2 --prefix TL-S --ignore-requirements  # 忽略练度要求（要用户同意）
    py -3.12 run_list.py 2 --prefix TL-S --potion               # 理智不够时用理智药（要用户同意；不会碎石）
    py -3.12 run_list.py --here --file 剿灭-龙门外环.json        # 单作业模式：游戏已停在关卡详情页（剿灭、危机合约这类没有节点名的）

单作业模式（--here）不导航、不切突袭：先在游戏里进到关卡详情页（右下有「开始行动」），要打突袭就先在详情页切好。

作业文件：<MAA_DIR>\\config\\copilot\\<prefix>-<n>.json；--raid 时优先 <prefix>-<n>-raid.json。
日志：<COPILOT_WORK>\\maacore\\debug\\asst.log；结果：<COPILOT_WORK>\\maacore\\list_result.json。
退出码：0 全部成功；2 连不上模拟器；3 有关没过（TaskChainError）；4 卡住（长时间没有任何进展）；5 参数或文件不对；6 已经有一个在跑。
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common  # noqa: E402

VALUE_OPTS = ("--file", "--prefix", "--support-usage", "--support-name", "--idle-minutes")


def opt(name, default=None):
    for i, a in enumerate(sys.argv):
        if a == name and i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return default


consumed = {i + 1 for i, a in enumerate(sys.argv) if a in VALUE_OPTS}
stages = [int(a) for k, a in enumerate(sys.argv[1:], start=1) if k not in consumed and a.isdigit()]
PREFIX = opt("--prefix")
RAID = "--raid" in sys.argv
POTION = "--potion" in sys.argv
IGNORE_REQ = "--ignore-requirements" in sys.argv
SUPPORT_USAGE = int(opt("--support-usage", "0") or 0)
SUPPORT_NAME = opt("--support-name", "") or ""
IDLE_LIMIT = float(opt("--idle-minutes", "6")) * 60
HERE = "--here" in sys.argv
FILE = opt("--file")
if HERE and FILE:
    PREFIX = PREFIX or ""
elif not stages or not PREFIX:
    _common.fail(__doc__)
if RAID and SUPPORT_USAGE:
    _common.fail("突袭不能用助战：去掉 --support-usage")

MAA = _common.maa_dir()
WORK = _common.work_dir()
OUT = os.path.join(WORK, "maacore")
sys.path.insert(0, os.path.join(MAA, "Python"))
from asst.asst import Asst  # noqa: E402
from asst.utils import InstanceOptionType, Message  # noqa: E402

state = {"chain": {}, "last": time.time(), "extra": []}


def log(*a):
    print(time.strftime("[%H:%M:%S]"), *a, flush=True)


@Asst.CallBackType
def callback(msg, details, arg):
    state["last"] = time.time()
    try:
        m = Message(msg)
    except ValueError:
        return
    try:
        d = json.loads(details.decode("utf-8")) if details else {}
    except ValueError:
        d = {}
    if m in (Message.TaskChainStart, Message.TaskChainCompleted, Message.TaskChainError):
        log(m.name, json.dumps(d, ensure_ascii=False)[:200])
        c = state["chain"].setdefault(d.get("taskchain") or "?", {"completed": None, "failed": None})
        c["completed" if m == Message.TaskChainCompleted else "failed" if m == Message.TaskChainError else "started"] = d
    elif m == Message.SubTaskExtraInfo:
        what = d.get("what")
        if what in ("CopilotListLoadTaskFileSuccess", "CopilotListLoadTaskFileError", "BattleFormation", "BattleFormationSelected"):
            log("  ", what, json.dumps(d.get("details"), ensure_ascii=False)[:200])
            state["extra"].append(d)
    elif m == Message.SubTaskError:
        # 每关开头 BattleStartPre 的 NotUsePrts 一类错误是 MAA 的容错步骤，不代表失败；只记下来
        log("  SubTaskError", json.dumps(d.get("details") or d, ensure_ascii=False)[:200])


def stage_file(n):
    name = f"{PREFIX}-{n}"
    copilot = os.path.join(MAA, "config", "copilot")
    path = os.path.join(copilot, f"{name}.json")
    if FILE:
        path = FILE if os.path.isabs(FILE) else os.path.join(copilot, FILE)
    elif RAID and os.path.exists(os.path.join(copilot, f"{name}-raid.json")):
        path = os.path.join(copilot, f"{name}-raid.json")
    if not os.path.exists(path):
        _common.fail(f"缺作业文件 {path}：先用 fetch_chosen.py 下载（文件名就是关卡显示名）")
    with open(path, encoding="utf-8") as f:
        content = json.load(f)
    if not content.get("actions"):
        _common.fail(f"{path} 没有 actions：是作业列表里裁剪过的 content，用 fetch_chosen.py 重下")
    names = [o.get("name", "") for o in content.get("opers", [])]
    if any("Ã" in s or "å" in s or "æ" in s for s in names):
        _common.fail(f"{path} 里的干员名是乱码 {names[:3]}：用 fetch_chosen.py 重下（不要用 PowerShell 写文件）")
    difficulty = content.get("difficulty", 3) or 3
    if RAID and difficulty == 1:
        _common.fail(f"{path} 是只打普通的作业（difficulty=1），突袭要另找一份")
    if not RAID and difficulty == 2:
        _common.fail(f"{path} 是只打突袭的作业（difficulty=2），普通要另找一份")
    return {"filename": path, "nav_name_override": name, "is_raid": RAID}


def main():
    items = [stage_file(None)] if HERE and FILE else [stage_file(n) for n in stages]
    if HERE and len(items) != 1:
        _common.fail("--here 一次只能打一关")
    lock = _common.take_lock(WORK)
    adb, address, config, extras = _common.connection(MAA)
    offset = _common.log_offset(OUT)
    try:
        log("load", Asst.load(path=MAA, user_dir=OUT))
        asst = Asst(callback=callback)
        if extras:
            # 不设这个 MaaCore 只能用 ADB 截图（约 1 秒/帧）；MAA 界面里跑是 20ms 左右
            Asst.set_connection_extras(config, extras)
            log("MuMu 截图增强:", extras["path"])
        asst.set_instance_option(InstanceOptionType.touch_type, "maatouch")
        if not asst.connect(adb, address, config):
            log("连不上模拟器", adb, address, "— emulator_status 看地址，模拟器没开就 emulator_start")
            sys.exit(2)
        log("connect ok", address, config)
        log("列表:", ", ".join(f"{os.path.basename(i['filename'])}→{i['nav_name_override']}" for i in items), "突袭" if RAID else "普通")
        log("参数: ignore_requirements", IGNORE_REQ, "use_sanity_potion", POTION, "support", SUPPORT_USAGE, SUPPORT_NAME)
        where = {"filename": items[0]["filename"]} if HERE else {"copilot_list": items}
        asst.append_task("Copilot", {
            **where,
            "formation": True,
            "ignore_requirements": IGNORE_REQ,
            "use_sanity_potion": POTION,
            "support_unit_usage": SUPPORT_USAGE,
            "support_unit_name": SUPPORT_NAME,
        })
        if not asst.start():
            _common.fail("MaaCore start 失败")
        t0 = time.time()
        hung = False
        while asst.running():
            time.sleep(1)
            if time.time() - state["last"] > IDLE_LIMIT:
                hung = True
                log(f"{IDLE_LIMIT / 60:.0f} 分钟没有任何进展，判卡住，停止")
                break
        asst.stop()
        chain = state["chain"].get("Copilot", {})
        ok = not hung and bool(chain.get("completed")) and not chain.get("failed")
        log(f"结束: {'成功' if ok else '卡住' if hung else '失败'}，用时 {(time.time() - t0) / 60:.1f} 分钟")
        with open(os.path.join(OUT, "list_result.json"), "w", encoding="utf-8") as f:
            json.dump({"stages": stages, "prefix": PREFIX, "raid": RAID, "ok": ok, "hung": hung, "chain": chain,
                       "params": {"ignore_requirements": IGNORE_REQ, "potion": POTION, "support": SUPPORT_USAGE}},
                      f, ensure_ascii=False, indent=1)
        _common.summarize_log(OUT, offset)
        sys.exit(0 if ok else 4 if hung else 3)
    finally:
        _common.release_lock(lock)


if __name__ == "__main__":
    main()
