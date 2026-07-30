"""Dispatch prompt files as headless Claude Code executor sessions.

    python monitor/dispatch.py                 # launch every pending prompt
    python monitor/dispatch.py --only R-1      # launch a specific one
    python monitor/dispatch.py --dry-run       # show the plan, launch nothing
    python monitor/dispatch.py --health        # content-free liveness report

Context isolation contract (the reason --health exists):
executor sessions run in their own processes with their own context windows;
nothing flows back into the monitor unless the monitor reads it. The monitor
therefore audits executors ONLY through their public interface — branches,
commits, RUN_STATE/STATUS files, runs/ archives, PARTNER_SYNC — never their
transcripts. dispatch-logs/ exist solely for launch-failure forensics
(CLI/auth errors); --health reports pid-alive / log-size / branch-created
WITHOUT reading log content, and reading a log body is warranted only when a
launch died before its branch appeared.

"Pending" = a P-*/R-*/M-* file in monitor/prompts/ whose agent branch does not
exist yet (local or remote). The branch check is the anti-double-run guard:
executor sessions create their branch as step one, so an existing branch means
a session already picked that prompt up (manually pasted or dispatched here).
Use --force to override for a genuine re-run.

Each launch: `claude -p <prompt-text> --model opus --dangerously-skip-permissions`
detached from the repo root, stdout/stderr appended to
monitor/dispatch-logs/<id>-<UTC>.log. The prompt itself instructs the session
to build its own worktree, so concurrent launches do not contend for the tree.

M-* prompts are never auto-launched by the batch run (merge runs after the
others push); dispatch them explicitly with --only.
"""

import argparse
import datetime
import os
import re
import shutil
import subprocess
import sys
import time
import childio  # noqa: E402  (per-child decoding, see its docstring)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROMPTS = os.path.join(HERE, "prompts")
LOGS = os.path.join(HERE, "dispatch-logs")


def git(*args):
    out = subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True,
                         text=True, encoding="utf-8", errors="replace")
    return out.stdout


def existing_branches():
    return set(line.strip().lstrip("*+ ").strip()
               for line in git("branch", "-a", "--format=%(refname:short)").splitlines()
               if line.strip())


LEGACY_ID = re.compile(r"^[PRMBA]-\d+$")


def prompt_id(name):
    # coordinate ids (A3-second-level) preferred; legacy serials (P-8) accepted
    m = re.match(r"([A-Z]\d+-[a-z0-9][a-z0-9-]*|[PRMBA]-\d+)", name)
    return m.group(1) if m else None


def branch_for(pid):
    return "agent/%s" % pid.lower().replace("-", "", 0).replace("P-", "p").replace("R-", "r").replace("M-", "m")


def branch_taken(pid, branches):
    if LEGACY_ID.match(pid):
        slug = pid.lower().replace("-", "")      # p8 / r1 / m0
        pat = re.compile(r"agent/%s\b|agent/%s-" % (slug, slug))
    else:
        pat = re.compile(r"agent/%s\b" % re.escape(pid.lower()))  # a3-second-level
    return any(pat.search(b) for b in branches)


REGISTRY = os.path.join(LOGS, "registry.json")


def load_registry():
    import json
    if os.path.exists(REGISTRY):
        return json.load(open(REGISTRY, encoding="utf-8"))
    return {}


def save_registry(reg):
    import json
    json.dump(reg, open(REGISTRY, "w", encoding="utf-8"), indent=2)


#: 死因账本。`_runner.py` 每个会话退出时写一条。
EXITS = os.path.join(LOGS, "exits.json")

#: `via_task` 起完之后等多久再问调度器「它还在吗」。
#: 只要够长到让一个撞限额/缺 CLI 的会话死掉（实测这类死亡在 1-2 秒内），
#: 又短到不拖住舰队循环——`sweep` 本来就在两次启动之间等 45 秒。
LAUNCH_SETTLE_S = 8


def read_exits(path=None):
    """读死因账本，**读不出来就说读不出来**。

    S28：这个文件已经记了 27 次非零退出，而**全仓没有任何一处读它**。
    接上它就得到一个权威的存活/死因来源——`standing.log` 的 `START ... ok=True`
    做不到这件事，因为那是调度器的收据，不是会话的命。

    返回 `{"ok": bool, "problem": str|None, "data": {...}}`。
    `ok=False` 时 `data` 是能救回多少算多少，**不是一个漂亮的空字典**：
    空账本（还没有人死过）与读不出来（写的人一直在被静默丢弃）是两件事，
    而后者恰恰意味着这个来源本身正在骗人。
    """
    import json
    p = path or EXITS
    if not os.path.exists(p):
        return {"ok": True, "problem": None, "data": {}, "missing": True}
    try:
        raw = open(p, encoding="utf-8").read()
    except OSError as exc:
        return {"ok": False, "problem": "unreadable: %s" % exc, "data": {}}
    try:
        data = json.loads(raw)
        if not isinstance(data, dict):
            return {"ok": False, "problem": "not an object", "data": {}}
        return {"ok": True, "problem": None, "data": data}
    except Exception as exc:
        first = "%s: %s" % (type(exc).__name__, exc)
    try:
        # 并发写者共用过一个临时文件名，产出「一个完整对象 + 另一个的尾巴」。
        # 前缀通常仍是完整的，救得回来——但**救回来不等于没事**：
        # `ok` 仍然是 False，因为写入端此刻正在丢记录。
        data, end = json.JSONDecoder().raw_decode(raw)
        if isinstance(data, dict):
            return {"ok": False, "data": data,
                    "problem": "corrupt: %s; recovered valid prefix, %d "
                               "trailing bytes discarded" % (first,
                                                             len(raw) - end)}
    except Exception:
        pass
    return {"ok": False, "problem": "corrupt: %s" % first, "data": {}}


def exit_summary(short_s=60, path=None):
    """死因账本的摘要，给盘面用。

    `probe_standing` 现在数 `standing.log` 里 `" START "` 的行数，印成
    「累计起过 N 次常驻会话」并保持绿色——**崩溃循环每 30 分钟把这个数字推高一次**，
    因为每一次重启都是一行新的 START。这个函数提供它缺的那一半：
    起来之后怎么了。

    `short` = 活了不到 `short_s` 秒就退出的会话数，也就是「起来了，然后立刻死了」——
    那正是 `ok=True` 那条收据看不见的东西。
    """
    got = read_exits(path)
    data = got["data"]
    runs = [(pid, r) for pid, rs in data.items()
            if isinstance(rs, list) for r in rs if isinstance(r, dict)]
    nonzero = [(p, r) for p, r in runs if r.get("code") not in (0, None)]
    short = [(p, r) for p, r in runs
             if isinstance(r.get("seconds"), int) and r["seconds"] < short_s]
    ended = sorted(r.get("ended") or "" for _p, r in runs)
    # `missing` 必须传下去。第一次拿这个摘要跑真账本时我传错了路径，
    # 于是它印出 `ok=True sessions=0`——「账本不存在」和「还没有人死过」
    # 收敛成了同一个健康答案。**这个补丁自己犯了它要修的那个病**，
    # 正好是条目原文预告的第二层结论（出问题最多的是补丁本身）。
    return {"ok": got["ok"], "problem": got["problem"],
            "missing": got.get("missing", False),
            "sessions": len(data), "runs": len(runs),
            "nonzero": len(nonzero), "short": len(short),
            "newest_ended": ended[-1] if ended else None,
            "nonzero_ids": sorted({p for p, _r in nonzero}),
            "short_ids": sorted({p for p, _r in short})}


def pid_alive(pidnum):
    # pid 0 不是一个进程，它是「我们没问到 pid」。
    #
    # 而 `tasklist /FI "PID eq 0"` 会返回 System Idle Process 那一行，
    # 于是子串判断命中，`pid_alive(0)` **恒为真**。任务表在本机不给 PID 字段，
    # 抓取循环无声退回初始值 0——结果是 66 条注册项里 62 条读作「还在跑」，
    # 死了一天的会话和活着的会话在纸面上逐字相同（2026-07-29 对抗性普查抓到）。
    #
    # 这条修复本身就是那种「补丁即缺陷」的例子：抓 pid 的那段代码**正是为了修
    # `pid: 0`** 而加的，而它在本机的失败模式恰好是返回同一个 0。
    if pidnum is None or pidnum <= 0:
        return False
    if os.name == "nt":
        out = subprocess.run(["tasklist", "/FI", "PID eq %d" % pidnum, "/FO", "CSV"],
                             capture_output=True, text=True, encoding=childio._CONSOLE, errors="replace").stdout
        return str(pidnum) in out
    try:
        os.kill(pidnum, 0)
        return True
    except OSError:
        return False


def kill_tree(pidnum):
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(pidnum), "/T", "/F"],
                       capture_output=True)
    else:
        subprocess.run(["kill", "-9", str(pidnum)], capture_output=True)


def reap():
    """跑完即杀：a dispatched session whose branch reached origin is done —
    kill its process tree immediately. Sessions that exited on their own are
    marked reaped. Content-free throughout."""
    reg = load_registry()
    remote = set(git("branch", "-r", "--format=%(refname:short)").splitlines())
    changed = False
    for pid, entry in sorted(reg.items()):
        if entry.get("reaped"):
            continue
        pidnum = entry["pid"]
        done = any(entry_branch in b for b in remote
                   for entry_branch in [("agent/%s" % pid.lower().replace("-", ""))])
        alive = pid_alive(pidnum)
        if done and alive:
            kill_tree(pidnum)
            entry["reaped"] = "killed-on-completion"
            print("%-6s pid=%s branch pushed -> killed" % (pid, pidnum))
            changed = True
        elif not alive:
            entry["reaped"] = "exited"
            print("%-6s pid=%s exited on its own" % (pid, pidnum))
            changed = True
        else:
            print("%-6s pid=%s still running" % (pid, pidnum))
    if changed:
        save_registry(reg)
    if not reg:
        print("registry empty.")


MODEL_TAG = re.compile(r"<!--\s*model:\s*(opus|sonnet|haiku)\s*-->")


def model_for(path):
    """Cost tiering (upgrade #3): a prompt opts into a cheaper model with an
    HTML comment near the top, e.g. `<!-- model: sonnet -->`. Default opus."""
    with open(path, encoding="utf-8") as fh:
        head = fh.read(600)
    m = MODEL_TAG.search(head)
    return m.group(1) if m else "opus"


def launch(pid, path, log_dir):
    if not shutil.which("claude"):
        sys.exit("claude CLI not on PATH")
    model = model_for(path)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_path = os.path.join(log_dir, "%s-%s.log" % (pid, stamp))
    with open(log_path, "a", encoding="utf-8") as log:
        log.write("=== dispatch %s at %s model=%s ===\n" % (pid, stamp, model))
    flags = 0
    if os.name == "nt":
        # DETACHED + NEW_PROCESS_GROUP alone was not enough: a whole fleet
        # once died silently mid-run while the user's app sessions survived —
        # consistent with Job-Object cleanup. BREAKAWAY escapes any inherited
        # job. The session runs under _runner.py so its exit code and stderr
        # always land on disk (upgrade #5).
        flags = (subprocess.CREATE_NEW_PROCESS_GROUP
                 | 0x00000008     # DETACHED_PROCESS
                 | 0x01000000)    # CREATE_BREAKAWAY_FROM_JOB
    proc = subprocess.Popen(
        [sys.executable, os.path.join(HERE, "_runner.py"),
         pid, path, log_path, model],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL, creationflags=flags)
    reg = load_registry()
    reg[pid] = {"pid": proc.pid, "log": os.path.basename(log_path),
                "started": stamp, "model": model, "reaped": None}
    save_registry(reg)
    return proc.pid, log_path


def health():
    """Content-free status of every dispatched session: pid alive, log bytes
    (a growing log = a working session), branch created. Never prints log
    content — that is the isolation contract."""
    procs = set()
    if os.name == "nt":
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq node.exe", "/FO", "CSV"],
                             capture_output=True, text=True, encoding=childio._CONSOLE, errors="replace").stdout
        procs = {line.split('","')[1] for line in out.splitlines() if line.startswith('"')}
    branches = existing_branches()
    if not os.path.isdir(LOGS):
        print("no dispatch logs.")
        return
    for name in sorted(os.listdir(LOGS)):
        if not name.endswith(".log"):
            continue
        pid = prompt_id(name)
        path = os.path.join(LOGS, name)
        size = os.path.getsize(path)
        age_min = (datetime.datetime.now().timestamp() - os.path.getmtime(path)) / 60
        branch = "branch:yes" if pid and branch_taken(pid, branches) else "branch:no"
        print("%-6s log=%7dB  last-write %4.0f min ago  %s"
              % (pid or "?", size, age_min, branch))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="dispatch just this prompt id (e.g. R-1)")
    ap.add_argument("--force", action="store_true",
                    help="launch even if the agent branch already exists")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--health", action="store_true",
                    help="content-free liveness report of dispatched sessions")
    ap.add_argument("--worker", metavar="ID",
                    help="spawn a long-lived board worker with this id")
    ap.add_argument("--reap", action="store_true",
                    help="kill sessions whose branch reached origin (跑完即杀)")
    args = ap.parse_args()
    if args.health:
        health()
        return 0
    if args.reap:
        reap()
        return 0
    if args.worker:
        via_task(args.worker, "W-worker.md")
        return 0

    os.makedirs(LOGS, exist_ok=True)
    branches = existing_branches()
    plan = []
    for name in sorted(os.listdir(PROMPTS)):
        pid = prompt_id(name)
        if not pid or not name.endswith(".md"):
            continue
        if args.only and pid != args.only:
            continue
        if pid.startswith(("M-", "A-", "B-", "R-")) and not args.only:
            plan.append((pid, name,
                         "skip: ops class -- runs in the user's app "
                         "(prompts/ops/), headless only via --only"))
            continue
        if branch_taken(pid, branches) and not args.force:
            plan.append((pid, name, "skip: agent branch exists (already picked up)"))
            continue
        entry = load_registry().get(pid)
        if entry and not entry.get("reaped") and pid_alive(entry["pid"]) \
                and not args.force:
            plan.append((pid, name, "skip: dispatched session still running (pid %s)"
                         % entry["pid"]))
            continue
        plan.append((pid, name, "LAUNCH"))

    launched = 0
    for pid, name, action in plan:
        if action != "LAUNCH":
            print("%-6s %-28s %s" % (pid, name, action))
            continue
        if args.dry_run:
            print("%-6s %-28s would launch" % (pid, name))
            continue
        if launched:
            # simultaneous storms killed half a fleet once; stagger is law now
            time.sleep(45)
        launched += 1
        pidnum, log_path = launch(pid, os.path.join(PROMPTS, name), LOGS)
        print("%-6s %-28s launched pid=%s log=%s"
              % (pid, name, pidnum, os.path.relpath(log_path, ROOT)))
    if not plan:
        print("nothing matched.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


# ---------------------------------------------------------------- via-task
# Every detached-spawn strategy died: tool-shell children get cleaned up, and
# a reflex tick's children die with the tick's job. Task Scheduler solves it
# properly — one ONE-SHOT task per work item, whose action runs the session
# SYNCHRONOUSLY, so the task stays Running for the session's lifetime and the
# process belongs to the scheduler, not to us. /Z self-deletes when done.

def via_task(pid_str, prompt_file):
    model = model_for(os.path.join(PROMPTS, prompt_file))
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_path = os.path.join(LOGS, "%s-%s.log" % (pid_str, stamp))
    with open(log_path, "a", encoding="utf-8") as log:
        log.write("=== via-task %s at %s model=%s ===\n" % (pid_str, stamp, model))
    task = "TheoriaAgent-%s" % pid_str
    # schtasks caps /TR at 261 chars, so the task passes only the id and
    # _runner.py derives prompt/log/model itself.
    cmd = '"%s" "%s" %s' % (sys.executable,
                            os.path.join(HERE, "_runner.py"), pid_str)
    subprocess.run(["schtasks", "/Create", "/TN", task, "/TR", cmd,
                    "/SC", "ONCE", "/ST", "23:59", "/F"],
                   capture_output=True, text=True, encoding=childio._CONSOLE, errors="replace")
    r = subprocess.run(["schtasks", "/Run", "/TN", task],
                       capture_output=True, text=True, encoding=childio._CONSOLE, errors="replace")
    ok = r.returncode == 0
    reg = load_registry()
    # A worker found `pid: 0` copied into three consumers (reap / health /
    # quota), so every task-launched session was untrackable. Ask the
    # scheduler for the real pid it started.
    real_pid = 0
    try:
        q = subprocess.run(["schtasks", "/Query", "/TN", task, "/FO", "LIST",
                            "/V"], capture_output=True, text=True, encoding=childio._CONSOLE, errors="replace")
        for line in q.stdout.splitlines():
            if line.strip().lower().startswith(("pid", "进程 id")):
                digits = "".join(c for c in line.split(":")[-1] if c.isdigit())
                if digits:
                    real_pid = int(digits)
                break
    except Exception:
        pass
    reg[pid_str] = {"pid": real_pid, "task": task,
                    "log": os.path.basename(log_path),
                    "started": stamp, "reaped": None, "via": "task"}
    save_registry(reg)

    # S28：`ok = r.returncode == 0` 是**调度器的收据，不是会话的命**。
    # `schtasks /Run` 在把任务交出去的那一刻就返回 0，所以一个启动后一秒就死的
    # 会话（撞限额、缺 CLI、提示词读不出来）产生与一个健康会话**逐字面量相同**的
    # `ok=True`——而 `standing.log` 的 `START ... ok=True` 是舰队关于「研究员被
    # 拉起来了」的首要记录。等几秒再问一次调度器，让 ok 的意思变成「它在跑」。
    #
    # 第三个值是必须的：**「起来了然后没了」既不是成功也不是启动失败**，
    # 两者该找的人完全不同（一个查会话为什么死，一个查调度器为什么不收）。
    status = "declined"
    if ok:
        time.sleep(LAUNCH_SETTLE_S)
        try:
            st = task_state(task)
        except Exception as exc:                # noqa: BLE001 -- named below
            status = "state-unknown(%s)" % type(exc).__name__
        else:
            low = st.lower()
            if "running" in low or "正在运行" in st:
                status = "running"
            elif st == "unknown":
                # 查到了任务但没认出状态行——不许当成健康。
                status = "state-unknown"
            else:
                # Ready（跑完了）或 gone（任务已消失）都意味着会话已经不在了，
                # 而我们几秒前才刚起它。死因去 exits.json 查（read_exits）。
                status = "died-on-arrival(%s)" % st
    # 印出来的词是被 grep 的（reflex 拿 "started" 判补员成功），所以只有真的在跑
    # 才准印 started——死在起跑线上的会话必须让那个 grep 落空。
    print("%-20s %s task=%s"
          % (pid_str, "started" if status == "running" else status.upper(), task))
    return status


def task_state(task):
    r = subprocess.run(["schtasks", "/Query", "/TN", task, "/FO", "LIST"],
                       capture_output=True, text=True, encoding=childio._CONSOLE, errors="replace")
    if r.returncode != 0:
        return "gone"
    for line in r.stdout.splitlines():
        if line.lower().startswith(("status", "状态")):
            return line.split(":", 1)[1].strip()
    return "unknown"
