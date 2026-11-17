"""这几个脚本共用的：找 MAA 目录、MuMu 截图增强、运行锁、读这次运行的 asst.log。

环境变量：
    MAA_DIR       MAA 目录（必填，script_list 里 id=maa 的 dir）
    COPILOT_WORK  工作目录（默认当前目录）：作业候选、MaaCore 日志都放这里
    ADB_ADDRESS   默认 127.0.0.1:16384（MuMu 12 实例 0）
    ADB_CONFIG    默认：找到 MuMu 目录时 MuMuEmulator12，否则 General
    MUMU_DIR      MuMu 12 安装目录（里面有 nx_device 的那层）；不填时从 MAA 配置里找
    CLIENT_TYPE   Official（默认）或 Bilibili
"""
import ctypes
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def fail(message):
    """参数或文件不对：退出码 5。"""
    print(message, file=sys.stderr, flush=True)
    sys.exit(5)


def maa_dir():
    d = os.environ.get("MAA_DIR", "")
    if not d or not os.path.isdir(d):
        fail("先设 MAA_DIR：script_list 里 id=maa 的 dir（MAA.exe 所在目录）")
    return d


def work_dir():
    d = os.environ.get("COPILOT_WORK", os.getcwd())
    os.makedirs(d, exist_ok=True)
    return d


def _walk(node):
    if isinstance(node, dict):
        for k, v in node.items():
            yield k, v
            yield from _walk(v)
    elif isinstance(node, list):
        for v in node:
            yield from _walk(v)


def _looks_like_mumu(path):
    return isinstance(path, str) and path and os.path.isdir(os.path.join(path, "nx_device"))


def mumu_dir(maa):
    """MuMu 12 的安装目录：MUMU_DIR，或 MAA 配置里 MuMu12 的 EmulatorPath。找不到返回 None。"""
    env = os.environ.get("MUMU_DIR", "")
    if env:
        if not _looks_like_mumu(env):
            fail(f"MUMU_DIR={env} 下面没有 nx_device：要填 MuMu 的安装目录（不是 nx_main）")
        return env
    for name in ("gui.new.json", "gui.json"):
        path = os.path.join(maa, "config", name)
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            continue
        for key, value in _walk(data):
            if ("MuMu12EmulatorPath" in key or key == "EmulatorPath") and _looks_like_mumu(value):
                return value
    return None


def connection(maa):
    """(adb 路径, 地址, 连接配置名, MuMu 扩展参数或 None)"""
    adb = os.path.join(maa, "adb", "platform-tools", "adb.exe")
    if not os.path.exists(adb):
        adb = "adb"
    address = os.environ.get("ADB_ADDRESS", "127.0.0.1:16384")
    mumu = mumu_dir(maa)
    config = os.environ.get("ADB_CONFIG", "MuMuEmulator12" if mumu else "General")
    extras = None
    port = address.rsplit(":", 1)[-1]
    looks_mumu = port.isdigit() and int(port) >= 16384 and (int(port) - 16384) % 32 == 0
    if config == "MuMuEmulator12" and mumu:
        extras = {"path": mumu, "touch": False, "client_type": os.environ.get("CLIENT_TYPE", "Official")}
    elif config == "MuMuEmulator12" or looks_mumu:
        print("!! 没找到 MuMu 安装目录，截图会退回 ADB（约 1 秒/帧，编队会认错、部署会慢）。设 MUMU_DIR 后再跑。", flush=True)
    return adb, address, config, extras


# ---- 运行锁：同一台模拟器同时只能有一个 MaaCore ----

def _alive(pid):
    if sys.platform != "win32":
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False
    handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not handle:
        return False
    code = ctypes.c_ulong()
    ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
    ctypes.windll.kernel32.CloseHandle(handle)
    return code.value == 259  # STILL_ACTIVE


def take_lock(work):
    path = os.path.join(work, "maacore", "run.lock")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        with open(path, encoding="utf-8") as f:
            pid = int(f.read().strip() or 0)
    except (OSError, ValueError):
        pid = 0
    if pid and pid != os.getpid() and _alive(pid):
        print(f"已经有一个抄作业在跑（python pid {pid}）。等它结束；确认它卡死了再结束这个进程，然后重跑。", file=sys.stderr)
        sys.exit(6)
    with open(path, "w", encoding="utf-8") as f:
        f.write(str(os.getpid()))
    return path


def release_lock(path):
    try:
        os.remove(path)
    except OSError:
        pass


# ---- 这次运行写进 asst.log 的部分 ----

KEY_EVENTS = (
    "CopilotListLoadTaskFileSuccess", "CopilotListLoadTaskFileError",
    "OperatorMissing", "requirement_type", "lower than any group requirement",
    "BattleStartNormal", "BattleStartRaid", "ChangeToRaidDifficulty",
    "StageDrops-Stars-3", "StageDrops-Stars-Adverse", "FightMissionFailed",
    "Group not found", "TaskChainError", "TaskChainCompleted",
)


def log_offset(out):
    path = os.path.join(out, "debug", "asst.log")
    return os.path.getsize(path) if os.path.exists(path) else 0


def summarize_log(out, offset, limit=40):
    """打印这次运行的关键行和截图耗时，省得再去翻 asst.log。"""
    path = os.path.join(out, "debug", "asst.log")
    if not os.path.exists(path):
        print("（没有 asst.log）")
        return
    with open(path, "rb") as f:
        f.seek(offset if offset <= os.path.getsize(path) else 0)
        lines = f.read().decode("utf-8", errors="replace").splitlines()
    keys = [ln for ln in lines if any(k in ln for k in KEY_EVENTS)]
    costs = [ln for ln in lines if "ScreencapCost" in ln or "screencap cost" in ln.lower()]
    print(f"\n== 本次 asst.log 关键行（{len(keys)} 条，最多显示 {limit}）：{path}")
    for ln in keys[-limit:]:
        print("  " + ln[:300])
    print("== 截图耗时（最后 3 条）：")
    for ln in costs[-3:]:
        print("  " + ln[:300])
    if any("mumu_handle_=0" in ln for ln in lines):
        print("!! 日志里有 mumu_handle_=0：MuMu 截图增强没生效，这次的识别结果不可靠。设对 MUMU_DIR 再跑。")
