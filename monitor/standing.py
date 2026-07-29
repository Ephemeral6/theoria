# -*- coding: utf-8 -*-
"""常驻研究员的例行程序：让「常驻」不再依赖任何人还醒着。

    python monitor/standing.py            # 一次巡检：该起的起来
    python monitor/standing.py --dry-run
    python monitor/standing.py --install  # 注册 15 分钟一次的循环任务

## 它解决的问题

RES-1…RES-4 此前**只能由用户在 Claude App 里点开**。会话死于上下文，赛道就停到
用户下次注意到为止——2026-07-29 实测停了十一小时，那三条赛道板上的活一件也动不了，
而监控除了在页面上写「需要用户重开」之外无事可做。

## 设计（用户 2026-07-29 定的形状）

「给研究员定一个 routine，然后你们通过文件通讯；你发现他暂停了就派任务，
他 routine 收到文件就继续做。」

照这个做，而且**故意不让监控当那个心跳源**：监控自己的会话也会死，一个靠我活着的
复活机制会和它要救的东西一起死。所以心跳是 Windows 的循环计划任务，它比任何会话都长命。

每一跳做四件判断，全部只看磁盘：

1. **它是不是已经在跑**——跑着就什么也不做（这条永远第一，双开会让两个同号会话
   抢同一份认领）。
2. **窗口是不是开着**——`quota_state.json` 是 hold 就不起（熔断器的判决优先于本例行）。
3. **内存够不够**——低于 `MIN_FREE_GB` 不起，机器崩过一次，二十个会话一起没了。
4. **它有没有活干**——未读消息 / 名下认领 / 本赛道可领条目，三者皆无就**不起**。
   这一条是省钱的那条：一个没活的常驻会话会读一圈仓库、写一句心跳、然后烧掉一次额度。

「派任务」就是往它信箱里写一行（`bus.py send RES-1 task "..."`）或往板上放一件带
它赛道的条目。**文件落盘即触发**，不需要任何人在场——这正是用户要的那条链。
"""

import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

LOG = os.path.join(HERE, "standing.log")
STATE = os.path.join(HERE, "standing_state.json")

#: 编号 → 赛道。与 board.LANE_OWNER 互为反表；两份定义会漂移，所以从那里读。
import board as board_mod                                          # noqa: E402

#: 同时最多几个常驻会话。四个全开会和无头工人抢同一个额度窗口。
MAX_STANDING = 3

#: 起会话的内存门槛。
#
#: 8.0 这个数是机器崩过一次之后拍的（约二十个会话同时没了），但它是个**总量**门槛，
#: 而崩溃的原因是**并发数**。实测一个 claude 会话稳态约 0.4–0.5 GB，所以按
#: 「留够余量 + 每个待起会话的实际开销」算，比拿一个总量数一刀切诚实：
#: 6.7 GB 空闲时按旧规则一个都不许起，而那时四个常驻研究员全死着、板上有活。
HEADROOM_GB = 3.0        # 不动用的余量
PER_SESSION_GB = 0.6     # 单个会话的保守估计（实测 0.42–0.52）

#: 两次起同一个编号之间的最短间隔。会话如果一启动就崩，没有这条就会变成死循环
#: 起会话——每十五分钟烧一次额度，而且看起来像在工作。
MIN_RELAUNCH_MIN = 20

#: 循环任务的周期（分钟）。
EVERY_MIN = 15

#: 锁文件 / cycle 推进在这个时长内算「有人顶着这个编号」。
LOCK_FRESH_MIN = 20

#: 板上有这个编号的动作，多久之内算它还活着。比锁宽——一件活可以做很久才交付，
#: 但一个会话在 90 分钟里对板一次动作都没有，就不该再被当成在岗。
BOARD_ACTIVE_MIN = 90

#: 板日志的路径（board.py 的同一份文件）。
BOARD_LOG = os.path.join(HERE, "board", "board.log")


def log(msg):
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(LOG, "a", encoding="utf-8", newline="\n") as fh:
        fh.write("%s %s\n" % (stamp, msg))
    print(msg)


def load_state():
    if os.path.exists(STATE):
        try:
            return json.load(open(STATE, encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_state(st):
    tmp = STATE + ".tmp"
    json.dump(st, open(tmp, "w", encoding="utf-8"), indent=2)
    os.replace(tmp, STATE)


def _console():
    try:
        import childio
        return childio._CONSOLE
    except Exception:
        return "utf-8"


def running_tasks():
    """当前正在运行的 TheoriaAgent-* 编号集合。

    问计划任务，不问注册簿：注册簿是我们自己写的声称，任务表是系统观察到的事实。
    这仓库今晚已经为「手工表 vs 树」付过两次账。"""
    out = subprocess.run(["schtasks", "/Query", "/FO", "CSV", "/NH"],
                         capture_output=True, text=True,
                         encoding=_console(), errors="replace")
    live = set()
    for line in (out.stdout or "").splitlines():
        cols = [c.strip('"') for c in line.split('","')]
        if len(cols) >= 3 and "TheoriaAgent-" in cols[0]:
            name = cols[0].strip('"').lstrip("\\").replace("TheoriaAgent-", "")
            if cols[2].strip('"') in ("Running", "正在运行"):
                live.add(name)
    return live


def quota_held():
    path = os.path.join(HERE, "quota_state.json")
    try:
        return json.load(open(path, encoding="utf-8")).get("mode") == "hold"
    except Exception:
        return False


def free_gb():
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory"],
            capture_output=True, text=True, encoding=_console(),
            errors="replace", timeout=60)
        return int((out.stdout or "0").strip() or 0) / 1024.0 / 1024.0
    except Exception:
        return 0.0        # 读不到就当作不够——保守方向是不起，不是起


def unread_count(agent):
    """信箱里还没读的条数。这是「派任务」那条链的触发端。"""
    inbox = os.path.join(HERE, "bus", agent, "in.jsonl")
    cursor = os.path.join(HERE, "bus", agent, "cursor.json")
    if not os.path.exists(inbox):
        return 0
    try:
        rows = sum(1 for l in open(inbox, encoding="utf-8") if l.strip())
    except Exception:
        return 0
    last = 0
    if os.path.exists(cursor):
        try:
            last = json.load(open(cursor, encoding="utf-8")).get("last_seq", 0)
        except Exception:
            last = 0
    return max(0, rows - last)


def occupied(agent, state):
    """有人正顶着这个编号在干活吗？返回一句理由，或 None。

    这是整套机制里唯一**危险**的判断。`running_tasks()` 只看得见计划任务，
    看不见用户在 Claude App 里点开的会话——而两个会话共用一个编号，会各自认领、
    各自提交、各自以为自己是唯一的那个。所以这里问三个来源，任一为真就不起：

    * **锁文件**（契约要求每轮刷新）——App 会话也写，是唯一能跨启动方式的信号；
    * **cycle 在涨**——只有 agent 自己会加它，单调，且**伪造不了**；
    * mtime **不算**：一次 `git merge` 就能把死会话的 ops-status 摸新，
      今天下午就发生过（RES-2/RES-4 的 mtime 49 分钟，自报时刻却是几小时前）。
    """
    # **板上的动作是最强的存活信号**，因为它是这个编号对共享状态造成的**后果**，
    # 不是它对自己的**自述**：锁可以忘记刷新，cycle 可以停在原地，mtime 可以被
    # 一次 merge 摸新，但 board.log 里一行 CLAIM/DONE 只可能由一个活着的会话写出来。
    #
    # 2026-07-29 实测：App 里的 RES-4 安静了三个多小时（锁 204 分钟、cycle 不动），
    # 我据此判它已死并另起了一个无头 RES-4——**于是同一个编号有两个会话**，
    # 同一件 S29 被独立做了两遍，产出两条互相冲突的分支。这是同号并发的第三次。
    log_path = os.path.join(BOARD_LOG)
    if os.path.exists(log_path):
        try:
            recent = 0.0
            with open(log_path, encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    if (" by %s" % agent) not in line:
                        continue
                    try:
                        t = time.strptime(line.split(" ", 1)[0],
                                          "%Y-%m-%dT%H:%M:%SZ")
                    except Exception:
                        continue
                    import calendar
                    recent = max(recent, calendar.timegm(t))
            if recent:
                age = (time.time() - recent) / 60.0
                if age < BOARD_ACTIVE_MIN:
                    return "board activity %.0f min ago" % age
        except OSError:
            pass

    lock = os.path.join(HERE, "ops-status", "%s.lock" % agent)
    if os.path.exists(lock):
        age = (time.time() - os.path.getmtime(lock)) / 60.0
        if age < LOCK_FRESH_MIN:
            return "lock held %.0f min ago" % age

    path = os.path.join(HERE, "ops-status", "%s.json" % agent)
    cycle = None
    if os.path.exists(path):
        try:
            cycle = json.load(open(path, encoding="utf-8")).get("cycle")
        except Exception:
            cycle = None
    seen = state.setdefault(agent, {})
    # **第一次看见不算推进。** 空状态下「从没见过」和「刚涨过」长得一模一样，
    # 而默认值指向的是「有人活着、别起」——正是今晚反复抓到的那个形状：
    # 缺省值倒向好消息。第一次只记下来，不当证据。
    if "last_cycle" not in seen:
        seen["last_cycle"] = cycle
        seen["last_cycle_epoch"] = 0.0
        return None
    if cycle is not None and cycle != seen["last_cycle"]:
        seen["last_cycle"] = cycle
        seen["last_cycle_epoch"] = time.time()
        # cycle 变了**只说明它比我们上次记的新**，不说明它是刚刚写的——
        # 我们上次记的可能是三小时前，而它两小时前就死了。所以还要求文件本身是新的。
        # mtime 单看会被一次 merge 摸新（已实测），但那种情况下 cycle 下一跳就不再变，
        # 于是最多骗过一跳。两个都要求，才既不误杀活人、也不替死人站岗。
        file_age = (time.time() - os.path.getmtime(path)) / 60.0
        if file_age < LOCK_FRESH_MIN:
            return "cycle advanced to %s (%.0f min ago)" % (cycle, file_age)
        return None
    quiet_since = seen.get("last_cycle_epoch") or 0.0
    if quiet_since:
        quiet = (time.time() - quiet_since) / 60.0
        if quiet < LOCK_FRESH_MIN:
            return "cycle advanced %.0f min ago" % quiet
    return None


def work_for(agent, lane):
    """这个编号现在有没有活。三个来源，任一非空即算有。"""
    unread = unread_count(agent)
    held = sum(1 for f in os.listdir(board_mod.CLAIMED)
               if f.endswith(".%s.md" % agent))
    try:
        claimable = len(board_mod.candidates(lane))
    except Exception:
        claimable = 0
    return {"unread": unread, "held": held, "claimable": claimable,
            "any": bool(unread or held or claimable)}


def sweep(dry=False, only=None):
    state = load_state()
    live = running_tasks()
    held = quota_held()
    gb = free_gb()
    started = []
    n_standing = sum(1 for a in board_mod.LANE_OWNER.values() if a in live)

    for lane, agent in sorted(board_mod.LANE_OWNER.items(),
                              key=lambda kv: kv[1]):
        if only and agent != only:
            continue
        w = work_for(agent, lane)
        age = board_mod.heartbeat_age(agent)
        busy = occupied(agent, state)     # 只调用一次：它会写状态
        why = None
        if agent in live:
            why = "already running (scheduled task)"
        elif busy:
            why = busy
        elif held:
            why = "quota hold"
        elif gb < HEADROOM_GB + PER_SESSION_GB:
            why = ("free memory %.1fGB < headroom %.1f + %.1f per session"
                   % (gb, HEADROOM_GB, PER_SESSION_GB))
        elif n_standing >= MAX_STANDING:
            why = "standing cap %d reached" % MAX_STANDING
        elif not w["any"]:
            why = "no work (unread=0 held=0 claimable=0)"
        else:
            last = state.get(agent, {}).get("last_launch_epoch", 0)
            mins = (time.time() - last) / 60.0
            if mins < MIN_RELAUNCH_MIN:
                why = "relaunched %.0f min ago (< %d)" % (mins, MIN_RELAUNCH_MIN)

        if why:
            log("skip %s: %s [unread=%d held=%d claimable=%d hb=%s]"
                % (agent, why, w["unread"], w["held"], w["claimable"],
                   "never" if age is None else "%dmin" % age))
            continue

        if dry:
            log("WOULD START %s (lane=%s) [unread=%d held=%d claimable=%d]"
                % (agent, lane, w["unread"], w["held"], w["claimable"]))
            started.append(agent)
            continue

        import dispatch
        ok = dispatch.via_task(agent, os.path.join("ops", "%s.md" % agent))
        state.setdefault(agent, {})["last_launch_epoch"] = time.time()
        state[agent]["last_launch_utc"] = time.strftime(
            "%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        state[agent]["reason"] = ("unread=%d held=%d claimable=%d"
                                  % (w["unread"], w["held"], w["claimable"]))
        save_state(state)
        log("START %s (lane=%s) ok=%s [unread=%d held=%d claimable=%d]"
            % (agent, lane, ok, w["unread"], w["held"], w["claimable"]))
        if ok:
            started.append(agent)
            n_standing += 1
            time.sleep(45)       # 错峰：同时起会互相踩额度与内存

    # **每一跳都要落盘，不只是起了会话的那一跳。**
    #
    # 第一版只在起会话的分支里存状态（2026-07-29 实测后果）：观察到的 cycle 从不
    # 被记下，于是记录永远停在最后一次启动时的值，而 `cycle != last_cycle` 永远为真，
    # `occupied()` 于是每一跳都说「cycle advanced」并跳过——**这套机制把自己永久关掉了**，
    # 而日志上每一行都写着令人安心的「cycle advanced to 14」。
    # 四个常驻研究员 05:45–06:45Z 被它成功起来、交了 28 件活、然后死于上下文，
    # 之后三个多小时里它一个也没重启，因为它相信它们还在涨。
    if not dry:
        save_state(state)
    if not started:
        log("nothing to start")
    return started


def install():
    """注册循环任务。这是整件事的关键一步：**心跳不能挂在任何会话身上。**"""
    cmd = '"%s" "%s"' % (sys.executable, os.path.join(HERE, "standing.py"))
    r = subprocess.run(["schtasks", "/Create", "/TN", "TheoriaStanding",
                        "/TR", cmd, "/SC", "MINUTE", "/MO", str(EVERY_MIN),
                        "/F"],
                       capture_output=True, text=True,
                       encoding=_console(), errors="replace")
    print((r.stdout or "") + (r.stderr or ""))
    return r.returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--install", action="store_true")
    ap.add_argument("--only")
    a = ap.parse_args()
    if a.install:
        return install()
    sweep(dry=a.dry_run, only=a.only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
