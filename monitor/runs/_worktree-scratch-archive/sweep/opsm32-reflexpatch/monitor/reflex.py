"""Reflex layer (upgrade #1): everything that needs no judgment, every 5 min.

Registered as a Windows scheduled task; zero tokens. The monitor session
keeps only judgment (prompts, adjudication, spec updates). Steps:

    1. reap        — kill sessions whose branch reached origin
    2. quota check — flip to hold on limit signatures
    3. revive      — relaunch lost sessions (three-strikes rule)
    4. ci merge    — deterministic merge-on-delivery (test-gated)
    5. light refresh — regenerate the dashboard from the tree

All state changes go through the same files the monitor uses (registry,
loop_state, quota_state), so the monitor's next heartbeat sees everything.
The reflex never commits to git and never authors or edits prompts.
"""

import json
import os
import socket
import subprocess
import sys
import time
import traceback
import childio  # noqa: E402  (per-child decoding, see its docstring)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LOCK = os.path.join(HERE, "reflex.lock")
RLOG = os.path.join(HERE, "reflex.log")
LOOP = os.path.join(HERE, "loop_state.json")
MAX_DEATHS = 3
WORKER_MAX = 7      # spawning is back ON: the crash-era safeties are all in place
                    # now (memory admission, 45s stagger, orphan sweep, quota
                    # gate), so worker supply no longer waits for a human.
# 补员的内存门槛。
#
# 8 这个总量数是机器崩过一次之后拍的，而那次崩溃的原因是**并发数**（约二十个
# 会话同时起），不是总量。`standing.py` 2026-07-29 已经改成「余量 + 每会话开销」，
# 这里没跟上——于是整夜的 reflex.log 是一串 `worker-hold:low-memory(7.5GB)`、
# `(7.3GB)`、`(6.7GB)`：**补员机制一直存在，一直没有触发过**，
# 舰队的人手全靠我手动加。两处判据对同一件事给不同答案，就是这个下场。
HEADROOM_GB = 3.0        # 不动用的余量
PER_SESSION_GB = 0.6     # 单个会话的保守估计（实测 0.42–0.52）
MIN_FREE_GB = HEADROOM_GB + PER_SESSION_GB

# 两个子进程的期限，提出来命名，因为 **600 这个数已经被量出来是错的**。
# 2026-07-30 实测：`scan.py` 在满载舰队下跑完一次要 1571–1602 秒（仪表盘任务的
# 那个实例，无期限，跑完了）；同一时刻手工计时的另一次超过 761 秒仍未结束。
# reflex 给它 600 秒，于是**每一跳都在期限上被杀**，而 `subprocess.run` 抛出的
# `TimeoutExpired` 从第 361 行一路穿过第 363 行的 rlog——从 01:33:34Z 到 12:52Z，
# 十一个小时没有一跳写出过收尾行，reflex.log 看起来和「任务从没触发」一模一样。
# 期限本身该不该抬高是监控的判断（抬高会让一跳超过五分钟的调度间隔），
# 所以这里只把它变成一个可改的数，并且保证超时**是一个事件而不是一次静默死亡**。
MERGE_TIMEOUT_S = 3600
SCAN_TIMEOUT_S = 600


def rlog(msg):
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(RLOG, "a", encoding="utf-8") as fh:
        fh.write("%s %s\n" % (stamp, msg))


def run(args, timeout=2400):
    """Everything this file runs is Python -- dispatch, board, quota -- so UTF-8.

    It was the host locale, cp936, and the children print Chinese. That is the
    same mismatch that reported eight live workers as dead, sitting in the one
    module whose job is deciding which workers are dead. `errors="replace"`
    matters more than the codec: a reaper that raises while decoding its child
    is a reaper that did not run, and nothing downstream would say so.

    The single `schtasks` call in this file uses `run_console` instead.
    """
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout)


def run_console(args, timeout=2400):
    """Windows console built-ins emit the console code page, not UTF-8."""
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True,
                          encoding=childio._CONSOLE, errors="replace",
                          timeout=timeout)


class Unfinished:
    """The result of a child that never returned one.

    `run()` raises on a deadline, and **every raise between the first child and
    `rlog()` is a silent outage**: the cycle dies with no line at all, which from
    outside is byte-identical to a cycle the scheduler never started. That is not
    a hypothetical -- it is the 2026-07-30 outage, and it cost two cycles of
    triage because the brightest instrument to hand (`ci_merge`'s `merge.log`) is
    written by the *child*, so it stays fresh exactly while the parent is the
    thing that is failing.

    Returning a result object rather than propagating keeps the caller's shape
    (`.returncode` / `.stdout` / `.stderr` are all read downstream) and, more to
    the point, keeps the cycle alive long enough to write down what happened.
    `returncode` is deliberately non-zero so the existing EXIT- alarms fire on it
    too: a killed child must not be able to read as a clean no-op, which is the
    whole of S28 finding 10.
    """

    def __init__(self, why):
        self.returncode = -1
        self.stdout = ""
        self.stderr = why


def run_guarded(args, timeout, tag, events):
    """`run`, but a deadline or a failed spawn becomes an event, not an exit."""
    try:
        return run(args, timeout=timeout)
    except subprocess.TimeoutExpired:
        events.append("%s:TIMEOUT(%ds)" % (tag, timeout))
        return Unfinished("killed at the %ds deadline" % timeout)
    except OSError as exc:
        events.append("%s:SPAWN-FAILED:%s" % (tag, type(exc).__name__))
        return Unfinished("%s: %s" % (type(exc).__name__, exc))


def load_loop():
    if os.path.exists(LOOP):
        return json.load(open(LOOP, encoding="utf-8"))
    return {}


def save_loop(state):
    tmp = LOOP + ".tmp"
    json.dump(state, open(tmp, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    os.replace(tmp, LOOP)


def merge_events(r):
    """What the ci_merge step of the loop reports, given the child's result.

    S28: only stdout used to be read, so a crashed merger, a merger killed
    mid-run, and a clean no-op were **the same observation** -- all three logged
    `quiet`. Measured: exits 0/1/3 all produced `events=[]`
    (EVIDENCE-3-standing-reflex.md).

    Alarming on non-zero is safe rather than cry-wolf: `ci_merge.py` has no
    `sys.exit` anywhere, and a conflict or a red gate is reported as a `FLAG`
    line on stdout, not as a status. So non-zero means the *merger* broke, not
    that a merge was declined -- `test_the_real_ci_merge_has_no_deliberate_
    nonzero_exit` fails if that ever stops being true.

    **This lives in a function only so that a test can reach it.** ADV-2/D13
    caught the previous arrangement: the logic was inline in `main()`'s loop and
    unreachable from a test, so the two tests that claimed to cover it exercised
    a re-implementation of these eight lines *inside the test file* and passed
    against the pre-fix `reflex.py` verbatim. A test that owns a copy of the code
    under test cannot fail when the code changes, which makes it exactly the kind
    of always-green check this whole item is about.
    """
    out = [l for l in r.stdout.splitlines() if l.startswith("MERGED")]
    out += [l for l in r.stdout.splitlines() if l.startswith("FLAG")]
    if r.returncode != 0:
        first = ((r.stderr or "").strip().splitlines() or [""])[0]
        out.append("merge:EXIT-%d %s" % (r.returncode, first[:120]))
    return out


def main():
    if os.path.exists(LOCK):
        age = int(time.time() - os.path.getmtime(LOCK))
        if age < 1500:
            # 「上一跳还没跑完」以前是一次无声的 return 0。这台机器上任务计划的
            # Operational 日志是关掉的（`Get-WinEvent -ListLog` 实测 IsEnabled
            # False），而 TheoriaReflex 是 MultipleInstances=IgnoreNew，所以被拒
            # 掉的那一跳在**任何地方**都不留痕迹。重叠一两分钟是常态，不值一行；
            # 超过三跳就是上一跳卡住了，那正是要看见的东西。
            if age > 900:
                rlog("cycle-skip: previous reflex still holds the lock "
                     "(%ds old)" % age)
            return 0
        rlog("stale-lock: removed a lock %ds old -- the previous cycle died "
             "without releasing it" % age)
        os.remove(LOCK)
    open(LOCK, "w").write(str(os.getpid()))
    events = []
    # 开跳一行。收尾行（本函数末尾那个 rlog）由**父进程**在所有子进程都回来之后
    # 才写，所以「跑了一半死掉」和「压根没跑」在 reflex.log 里长得一样——这是
    # 2026-07-30 那次十一小时停摆里唯一真正缺的仪表。有了这一行，两者的区别
    # 就是「有 cycle-start 没有收尾行」和「连 cycle-start 都没有」。
    rlog("cycle-start pid=%d" % os.getpid())
    try:

        # 0. launch queue — the monitor never spawns sessions itself anymore:
        # anything spawned from its tool shell gets silently killed (proven
        # by runner-level deaths with no EXIT stamp). The monitor appends ids
        # to dispatch_queue.json; we launch them here, under Task Scheduler
        # lineage, where processes actually survive.
        qpath = os.path.join(HERE, "dispatch_queue.json")
        if os.path.exists(qpath):
            try:
                queue = json.load(open(qpath, encoding="utf-8"))
            except Exception:
                queue = []
            launched_q = 0
            for pid_str in queue:
                if launched_q:
                    time.sleep(45)
                r = run([sys.executable, os.path.join(HERE, "dispatch.py"),
                         "--only", pid_str, "--force"])
                if "launched" in r.stdout:
                    events.append("queue-launch:%s" % pid_str)
                    launched_q += 1
                else:
                    events.append("queue-skip:%s" % pid_str)
            os.remove(qpath)

        # 0c. sweep orphaned board claims — a worker killed by the quota or a
        # crash leaves its claim hanging, so the board thinks the work is in
        # progress and the territory stays locked against everyone else.
        # `--include-standing` since S21. Standing sessions were exempt because
        # nothing could tell a dead App session from a busy one; `board.py` now
        # can, and requires all three of a stale heartbeat, an unanswered
        # URGENT, and two full cycles of silence before it will free anything.
        # Three researchers died to a session limit on 2026-07-29 and six items
        # -- including the campaign mainline -- stayed locked for two hours
        # because this ran without it.
        sw = run_guarded([sys.executable, os.path.join(HERE, "board.py"),
                          "sweep", "--include-standing"], 2400, "sweep", events)
        if sw.returncode != 0:
            first = ((sw.stderr or "").strip().splitlines() or [""])[0]
            events.append("sweep:EXIT-%d %s" % (sw.returncode, first[:120]))
        events += ["sweep:" + l.split()[0] for l in sw.stdout.splitlines()
                   if "freed from" in l]
        # A standing release is reported separately and by name. It is a much
        # bigger event than reaping a one-shot worker -- it says a researcher
        # is gone -- and folding the two into one `sweep:` line would bury the
        # louder one under the routine one.
        for line in sw.stdout.splitlines():
            if "freed from" in line and "RES-" in line:
                events.append("STANDING-DEAD:%s" % line.split()[0])
                rlog("standing session released a claim: %s" % line.strip())

        # 0d. dashboard server — the logon task could not be registered
        # (needs admin), so reflex keeps the port alive itself. Without this
        # the page dies at every reboot and the user has to notice.
        try:
            s = socket.socket()
            s.settimeout(1)
            dead = s.connect_ex(("127.0.0.1", 8787)) != 0
            s.close()
        except Exception:
            dead = True
        if dead:
            # 旧写法两个毛病，合起来让页面死了很久而日志一直说「已重启」：
            # (1) 经 `cmd /c start` 起服务在这个环境里根本不生效——实测端口始终
            #     关着；直接 Popen 那个 http.server 就成；
            # (2) **无论成没成都追加 `serve:restarted`**，于是「重启成功」与
            #     「重启失败」写出同一行。这条自动机制因此隐形失效，
            #     而它本来就是为了「页面死了没人发现」而存在的。
            try:
                subprocess.Popen([sys.executable, "-m", "http.server", "8787",
                                  "--bind", "127.0.0.1"],
                                 cwd=HERE,
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL,
                                 creationflags=0x00000008 | 0x01000000)
            except Exception as exc:
                events.append("serve:spawn-FAILED:%s" % type(exc).__name__)
            else:
                time.sleep(3)          # 起得来就在这个时间内起来了
                probe = socket.socket()
                probe.settimeout(2)
                up = probe.connect_ex(("127.0.0.1", 8787)) == 0
                probe.close()
                events.append("serve:restarted" if up
                              else "serve:restart-FAILED(port still shut)")

        # 1. reap
        rp = run_guarded([sys.executable, os.path.join(HERE, "dispatch.py"),
                          "--reap"], 2400, "reap", events)
        if rp.returncode != 0:
            first = ((rp.stderr or "").strip().splitlines() or [""])[0]
            events.append("reap:EXIT-%d %s" % (rp.returncode, first[:120]))
        killed = [l for l in rp.stdout.splitlines() if "killed" in l]
        events += ["reap:" + l.split()[0] for l in killed]

        # 2. quota
        q = run([sys.executable, os.path.join(HERE, "quota.py"), "check"])
        # The hold had no exit: nothing ever called resume, so a session-limit
        # at 09:35 kept the fleet frozen long after its 20:20 reset (OPS-M
        # cycle 5). Every tick in hold now probes the window and lifts it.
        if q.returncode == 2:
            # `--if-due` and not a bare ping: this loop runs every five minutes
            # and each ping is a real haiku call, so an unthrottled probe spent
            # the quota it was waiting to get back, twelve times an hour, for
            # the length of the outage. Exit 3 means "not due, nothing spent".
            probe = run([sys.executable, os.path.join(HERE, "quota.py"),
                         "ping", "--if-due"], timeout=180)
            if probe.returncode == 3:
                events.append("quota:probe-throttled")
            elif probe.returncode == 0:
                # `resume` reuses this ping's answer rather than buying it
                # again; it is the same measurement seconds apart.
                r = run([sys.executable, os.path.join(HERE, "quota.py"),
                         "resume"], timeout=1800)
                events.append("quota:RESUMED(auto)")
                rlog("quota: window reopened on its own -> automatic resume, "
                     "no human in the loop: %s"
                     % (r.stdout.strip().splitlines() or ["(no output)"])[-1])
                q = run([sys.executable, os.path.join(HERE, "quota.py"),
                         "check"])
        # 退出码 2 是「窗口关着」，0 是「窗口开着」，**其它一律是「没问出来」**。
        # 旧写法 `== 2` 把 1（未捕获的 traceback、截断的 quota_state.json）
        # 塌成「窗口开着」，重新放开这一跳最贵的两条分支；而 stderr 被捕获后丢弃，
        # 失败的检查与干净的检查在 reflex.log 里逐字节相同。
        hold = q.returncode != 0
        if q.returncode not in (0, 2):
            first = ((q.stderr or "").strip().splitlines() or [""])[0]
            events.append("quota:CHECK-FAILED(%d) %s"
                          % (q.returncode, first[:120]))
        if hold:
            events.append("quota:HOLD")

        # 0b. worker headcount — long-lived workers claim their own items from
        # the board, so the monitor controls only the population, never the
        # per-item dispatch. Target scales with what the board still holds.
        try:
            import board as board_mod
            avail = len(board_mod.candidates())
            claimed = len(board_mod.claimed_map())
        except Exception:
            avail, claimed = 0, 0
        if not hold and avail:
            reg_path = os.path.join(HERE, "dispatch-logs", "registry.json")
            reg = (json.load(open(reg_path, encoding="utf-8"))
                   if os.path.exists(reg_path) else {})
            live_workers = 0
            for wid, entry in reg.items():
                if not wid.startswith("W-") or entry.get("reaped"):
                    continue
                st = run_console(["schtasks", "/Query", "/TN",
                          "TheoriaAgent-%s" % wid, "/FO", "LIST"])
                # 中文控制台印的是「正在运行」，英文的 "Running" 一次也不会命中，
                # 于是 live_workers **恒为 0**，补员循环每一跳都按满员上限拉人。
                # 这仓库已经为 GBK/UTF-8 付过五次账；两个词都认，别只认一个。
                if st.returncode == 0 and ("Running" in st.stdout
                                           or "正在运行" in st.stdout):
                    live_workers += 1
            # 读不到内存就当作**没有**内存，不是当作 99 GB。
            # 旧写法初始值 99 + `except: pass`，任何一种读数失败都让门大开、
            # 一次放进七个工人；而这道门唯一能发的事件（worker-hold:low-memory）
            # 按构造在读数失败时不可能发出——今天读数失败与一台健康的 99GB 机器
            # 产生逐字节相同的日志。`standing.py` 的同一处测量失败时返回 0.0，
            # 两个方向相反的默认值，能一次拉七个的那个反而是 fail-open 的。
            free_gb = 0.0
            try:
                out = run(["powershell", "-NoProfile", "-Command",
                           "(Get-CimInstance Win32_OperatingSystem)."
                           "FreePhysicalMemory"]).stdout.strip()
                free_gb = int(out) / 1048576.0
            except Exception as exc:
                events.append("mem-unreadable:%s" % type(exc).__name__)
            if free_gb < MIN_FREE_GB:
                events.append("worker-hold:low-memory(%.1fGB)" % free_gb)
                target = live_workers          # spawn nothing
            else:
                target = min(WORKER_MAX, max(1, avail))
            for i in range(target - live_workers):
                wid = "W-%d" % (int(time.time()) % 100000 + i)
                if i:
                    time.sleep(20)
                r = run([sys.executable, os.path.join(HERE, "dispatch.py"),
                         "--worker", wid])
                events.append("worker-spawn:%s" % wid
                              if "started" in r.stdout else
                              "worker-fail:%s" % wid)

        # 3. revive (skip in hold)
        if not hold:
            reg_path = os.path.join(HERE, "dispatch-logs", "registry.json")
            reg = (json.load(open(reg_path, encoding="utf-8"))
                   if os.path.exists(reg_path) else {})
            state = load_loop()
            deaths = state.get("death_counts", {})
            # 这一问失败的方向是**花钱**：`remote` 空掉会让每个死掉的会话看起来都
            # 没交付，于是这一跳把已经交付完的会话统统重开一遍。所以读退出码，
            # 而且读到非零就跳过整个循环，不是只记一行然后照跳。
            gq = run_guarded(["git", "branch", "-r", "--list", "origin/agent/*",
                              "--format=%(refname:short)"], 2400, "revive-git",
                             events)
            revived = 0
            if gq.returncode != 0:
                events.append("revive:GIT-EXIT-%d(loop-skipped)"
                              % gq.returncode)
            else:
                remote = gq.stdout.lower()
                for pid_str, entry in sorted(reg.items()):
                    if pid_str.startswith(("M-", "A-", "B-", "R-")):
                        continue        # ops run in the user's app now
                    if entry.get("reaped") not in ("exited",
                                                   "killed-permission-wall"):
                        continue
                    slug = (pid_str.lower().replace("-", "")
                            if len(pid_str) <= 4 else pid_str.lower())
                    if "agent/%s" % slug in remote:
                        continue        # it delivered; nothing to revive
                    n = deaths.get(pid_str, 0)
                    if n >= MAX_DEATHS:
                        events.append("three-strikes:%s" % pid_str)
                        continue
                    if revived:
                        time.sleep(45)   # stagger is law
                    r = run([sys.executable, os.path.join(HERE, "dispatch.py"),
                             "--only", pid_str])
                    if "launched" in r.stdout:
                        deaths[pid_str] = n + 1
                        revived += 1
                        events.append("revive:%s(#%d)" % (pid_str, n + 1))
            if revived or deaths != state.get("death_counts", {}):
                state["death_counts"] = deaths
                save_loop(state)

        # 4. ci merge — runs even under quota hold: it spends zero tokens
        # (git + pytest only), and a worker's proposal caught it being
        # stopped by a budget it cannot possibly consume.
        if True:
            r = run_guarded([sys.executable, os.path.join(HERE, "ci_merge.py")],
                            MERGE_TIMEOUT_S, "merge", events)
            events += merge_events(r)

        # 4b. supply alarm — authoring items needs judgment, so reflex cannot
        # refill the board itself; what it can do is make a dry board loud
        # instead of silent. Idle agents look identical to busy ones.
        #
        # `except Exception: pass` 是这里的原始缺陷，而且它比空板更安静：空板至少
        # 发得出 SUPPLY-LOW:0，读不动板子连一个字都没有。第三个值走 else 分支，
        # 这样「量到 0」和「没量出来」是两条不同的行。
        try:
            import board as board_mod
            depth = len(board_mod.candidates())
        except Exception as exc:
            events.append("SUPPLY-UNKNOWN:%s" % type(exc).__name__)
        else:
            if depth <= 2:
                events.append("SUPPLY-LOW:%d" % depth)

        # 5. light dashboard refresh — the last child, and the one that killed
        # the heartbeat for eleven hours on 2026-07-30. See SCAN_TIMEOUT_S.
        sc = run_guarded([sys.executable, os.path.join(HERE, "scan.py")],
                         SCAN_TIMEOUT_S, "scan", events)
        # scan.py 的 main() 崩了会 return 1（它自己的注释说「reflex.py now checks
        # this」——在这次改动之前那句话是假的，返回码被整个丢掉了）。
        if sc.returncode != 0:
            last = ((sc.stderr or "").strip().splitlines() or [""])[-1]
            events.append("scan:EXIT-%d %s" % (sc.returncode, last[:120]))

        rlog(" | ".join(events) if events else "quiet")
        return 0
    except BaseException as exc:        # noqa: BLE001 — re-raised two lines down
        # 兜底。上面每一处具名的守卫都可能漏掉下一个新加的子进程调用，而漏掉的
        # 代价是**整条心跳无声消失**。这一段保证不管从哪里抛出来，reflex.log 里
        # 都有一行说了从哪抛的；然后照样 re-raise，让任务计划也看到失败。
        rlog("%s | CYCLE-DIED:%s %s"
             % (" | ".join(events) if events else "(no events yet)",
                type(exc).__name__,
                (traceback.format_exc().strip().splitlines() or [""])[-1][:200]))
        raise
    finally:
        try:
            os.remove(LOCK)
        except OSError:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
