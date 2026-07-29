# -*- coding: utf-8 -*-
"""账号池：两个订阅轮着用，让舰队不再因为额度窗口而停机。

    python monitor/accounts.py status      # 每个账号的登录态与窗口态
    python monitor/accounts.py scaffold    # 建配置目录并预置权限（登录前跑一次）
    python monitor/accounts.py pick W-1    # 这次该用哪个账号（选号逻辑的单跑入口）

## 为什么是这个形状

第二个账号买到的**不是双倍并行，是不停机**。这台机器空闲内存约 6 GB、
一个会话 0.4–0.5 GB，**内存在额度之前先撞顶**——能同时跑的会话数与账号数无关。
今天真正的损失是停机：03:27–04:30 整队冻结一小时、05:39 四个工人四秒内一起死、
四个研究员死后三小时无人重启。所以目标是「同样 5–7 个会话，但永不因额度停下」。

## 机制

`CLAUDE_CONFIG_DIR` 指向的目录成为**整个配置根**（实测：一个空目录跑
`claude auth status` 会在里面生成 `.claude.json`，且报 `loggedIn: false`——
所以隔离是真的，登录态也是每个目录一份）。每个账号一个目录，启动时按账号设这个变量。

## 判据都不许有「第三个值坍缩」

本仓 2026-07-29 的普查结论是「这个代码库没有第三个值」：「测不到」和
「测了，没问题」编码成同一个字面量，而默认值一律指向健康。所以这里：

* 登录态有三种：`yes` / `no` / **`unknown`**（`claude auth status` 跑不起来时），
  而 `unknown` **不可用于启动**——不确定的账号不发车；
* 窗口态有三种：`open` / `limited` / **`unknown`**，同样不发车；
* `pick()` 找不到账号时返回 `None`，**不返回默认账号**。
"""

import argparse
import datetime
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

CONFIG = os.path.join(HERE, "accounts.json")
STATE = os.path.join(HERE, "accounts_state.json")
LOG = os.path.join(HERE, "accounts.log")

#: 角色 → 首选账号。一个账号的窗口关了，整条赛道不该跟着停，
#: 所以研究员与通用工人默认分开落在两个账号上。
ROLE_HOME = {"RES": "a", "OPS": "a", "W": "b"}


def _console():
    try:
        import childio
        return childio._CONSOLE
    except Exception:
        return "utf-8"


def now_utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def log(msg):
    with open(LOG, "a", encoding="utf-8", newline="\n") as fh:
        fh.write("%s %s\n" % (now_utc(), msg))
    print(msg)


def load_config():
    """账号清单。没有配置文件就是**没有账号池**，不是「有一个默认账号」。"""
    if not os.path.exists(CONFIG):
        return {}
    try:
        return json.load(open(CONFIG, encoding="utf-8")).get("accounts", {})
    except Exception as exc:
        log("CONFIG-UNREADABLE %s: %s" % (type(exc).__name__, exc))
        return {}


def load_state():
    if not os.path.exists(STATE):
        return {}
    try:
        return json.load(open(STATE, encoding="utf-8"))
    except Exception:
        # 状态读不出来时**不假装一切正常**：调用方会看到每个账号 window=unknown，
        # 于是谁也不发车，而不是全都发车。
        return {"_unreadable": True}


def save_state(st):
    tmp = STATE + ".tmp"
    json.dump(st, open(tmp, "w", encoding="utf-8"), indent=2, sort_keys=True)
    os.replace(tmp, STATE)          # 非原子写会让截断的状态永久卡住轮换器


def config_dir(acct):
    cfg = load_config().get(acct) or {}
    path = cfg.get("config_dir")
    return os.path.expandvars(os.path.expanduser(path)) if path else None


def env_for(acct):
    """启动一个属于该账号的会话时要注入的环境。"""
    d = config_dir(acct)
    if not d:
        return {}
    return {"CLAUDE_CONFIG_DIR": d}


def login_state(acct):
    """`yes` / `no` / `unknown`。**`unknown` 绝不当成 `yes` 用。**"""
    d = config_dir(acct)
    if not d or not os.path.isdir(d):
        return "no"
    env = dict(os.environ, CLAUDE_CONFIG_DIR=d)
    # Windows 上 `claude` 是一个 .CMD 垫片，`subprocess.run(["claude", ...])`
    # 不经 shell 时找不到它（WinError 2）——而那个异常在这里会被读成
    # 「登录态未知」，也就是把一个**工具问题**说成了**账号问题**。
    # 今晚这一族抓了 28 条，别在新代码里再造一条：显式解析出可执行文件。
    exe = shutil.which("claude")
    if not exe:
        return "unknown"
    try:
        out = subprocess.run([exe, "auth", "status"], env=env,
                             capture_output=True, text=True,
                             encoding=_console(), errors="replace",
                             timeout=120)
    except Exception:
        return "unknown"
    # **退出码在这里是有含义的，不是失败信号**：没登录时 `auth status` 退出 1
    # 并且照样打印一份合法 JSON。旧写法 `if returncode != 0: return "unknown"`
    # 会把「确定没登录」读成「测不出来」——同一个族的第 29 条，写在它自己的
    # 防范注释下面三行处。所以先信 JSON，解析不出来才是 unknown。
    try:
        return "yes" if json.loads(out.stdout).get("loggedIn") else "no"
    except Exception:
        return "unknown"


def window_state(acct, st=None):
    """`open` / `limited` / `unknown`。"""
    st = load_state() if st is None else st
    if st.get("_unreadable"):
        return "unknown"
    row = st.get(acct) or {}
    until = row.get("limited_until")
    if not until:
        return "open"
    try:
        when = datetime.datetime.strptime(until, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=datetime.timezone.utc)
    except Exception:
        return "unknown"           # 解析不了的时刻不是「已经过去了」
    return "open" if datetime.datetime.now(datetime.timezone.utc) >= when \
        else "limited"


def mark_limited(acct, until_utc, hint=""):
    """把**这一个**账号标记为窗口关闭。其余账号照常发车。"""
    st = load_state()
    st.pop("_unreadable", None)
    row = st.setdefault(acct, {})
    row["limited_until"] = until_utc
    row["limited_at"] = now_utc()
    row["hint"] = (hint or "")[:200]
    row["limits_seen"] = int(row.get("limits_seen", 0)) + 1
    save_state(st)
    log("LIMITED %s until %s (%s)" % (acct, until_utc, row["hint"][:80]))


def mark_open(acct, why=""):
    st = load_state()
    st.pop("_unreadable", None)
    row = st.setdefault(acct, {})
    row.pop("limited_until", None)
    row["reopened_at"] = now_utc()
    row["reopen_reason"] = why
    save_state(st)
    log("OPEN %s (%s)" % (acct, why))


def note_launch(acct, pid_str):
    st = load_state()
    st.pop("_unreadable", None)
    row = st.setdefault(acct, {})
    row["last_launch"] = now_utc()
    row["last_launch_pid"] = pid_str
    row["launches"] = int(row.get("launches", 0)) + 1
    save_state(st)


def usable(acct, st=None):
    """能不能拿它发车。**两个都必须是确定的好状态。**"""
    return login_state(acct) == "yes" and window_state(acct, st) == "open"


def pick(pid_str, st=None):
    """这次该用哪个账号；一个都没有就返回 None（**不回落到默认账号**）。

    顺序：先按角色的主场账号，再按其余账号里「本窗口发车最少」的那个。
    """
    cfg = load_config()
    if not cfg:
        return None
    st = load_state() if st is None else st
    role = pid_str.split("-")[0] if "-" in pid_str else pid_str
    home = ROLE_HOME.get(role)
    order = ([home] if home in cfg else []) + \
            sorted((a for a in cfg if a != home),
                   key=lambda a: int((st.get(a) or {}).get("launches", 0)))
    for acct in order:
        if usable(acct, st):
            return acct
    return None


def status():
    cfg = load_config()
    st = load_state()
    rows = []
    for acct in sorted(cfg):
        rows.append({"id": acct,
                     "label": (cfg[acct] or {}).get("label", acct),
                     "config_dir": config_dir(acct),
                     "login": login_state(acct),
                     "window": window_state(acct, st),
                     "limited_until": (st.get(acct) or {}).get("limited_until"),
                     "launches": int((st.get(acct) or {}).get("launches", 0)),
                     "limits_seen": int((st.get(acct) or {}).get("limits_seen", 0))})
    return rows


def scaffold():
    """建目录并预置「已接受 bypass 权限」——**登录之前跑一次**。

    没有这一步，每个新配置目录的第一次无头启动都会撞上权限墙并以只读退出，
    而它退出码是 0、日志是空的——本仓为这个失效签名付过一次账（六次撞墙才查明）。
    """
    made = []
    for acct, cfg in sorted(load_config().items()):
        d = config_dir(acct)
        if not d:
            continue
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, ".claude.json")
        data = {}
        if os.path.exists(path):
            try:
                data = json.load(open(path, encoding="utf-8"))
            except Exception:
                data = {}
        data["bypassPermissionsModeAccepted"] = True
        data["hasCompletedOnboarding"] = True
        json.dump(data, open(path, "w", encoding="utf-8"), indent=2)
        made.append("%s -> %s" % (acct, d))
    for line in made:
        log("SCAFFOLD %s" % line)
    if not made:
        log("SCAFFOLD 无账号配置（monitor/accounts.json 缺失或为空）")
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("status")
    sub.add_parser("scaffold")
    p = sub.add_parser("pick")
    p.add_argument("pid")
    a = ap.parse_args()
    if a.cmd == "scaffold":
        return scaffold()
    if a.cmd == "pick":
        acct = pick(a.pid)
        print(acct if acct else "NO-USABLE-ACCOUNT")
        return 0 if acct else 3
    for r in status():
        print("%-3s %-14s login=%-7s window=%-7s launches=%-4s limits=%s"
              % (r["id"], r["label"], r["login"], r["window"],
                 r["launches"], r["limits_seen"]))
        print("      %s" % r["config_dir"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
