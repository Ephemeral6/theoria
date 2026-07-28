"""Scan the working tree and render the Theoria progress monitor.

    python monitor/scan.py            # rescan, rewrite monitor/index.html
    python monitor/scan.py --tests    # also run both pytest suites (slow)
    python monitor/scan.py --watch 120   # rescan every 120 s; the page
                                         # auto-reloads itself while open

Everything the dashboard shows is either (a) re-derived from the tree on every
run, or (b) a judgement recorded in `spec.py` with its Theoria.md clause cited.
The two are visually distinguished in the output so a reader always knows which
is which.

Read-only with respect to the tracks: this writes only inside `monitor/`.
"""

import argparse
import html
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import spec  # noqa: E402

GAME_ID = re.compile(r"\b[a-z0-9]{4}-[0-9a-f]{8}\b")
SKIP_DIRS = {".git", "__pycache__", ".toolchain", ".lake", "node_modules",
             ".pytest_cache", ".egg-info", "out"}


# ---------------------------------------------------------------- helpers

def rel(*parts):
    return os.path.join(ROOT, *parts)


def exists(path):
    return os.path.exists(rel(path))


def count_lines(path):
    if not exists(path):
        return 0
    with open(rel(path), encoding="utf-8", errors="ignore") as fh:
        return sum(1 for line in fh if line.strip())


def read_json(path, default=None):
    if not exists(path):
        return default
    try:
        with open(rel(path), encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return default


def iter_jsonl(path):
    if not exists(path):
        return
    with open(rel(path), encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception:
                continue


def git(*args):
    try:
        out = subprocess.run(["git"] + list(args), cwd=ROOT,
                             capture_output=True, text=True, timeout=30,
                             encoding="utf-8", errors="replace")
        return out.stdout.strip()
    except Exception:
        return ""


# ---------------------------------------------------------------- probes

def probe_credential_hygiene():
    """The key must appear in .env and nowhere else. Constraint: Phase 1 sealing."""
    key = None
    env = rel(".env")
    if os.path.exists(env):
        for line in open(env, encoding="utf-8", errors="ignore"):
            if line.startswith("ARC_API_KEY"):
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not key:
        return {"status": "partial", "detail": "未找到 .env / ARC_API_KEY，无法验证。"}
    leaks = []
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.endswith(".egg-info")]
        for name in files:
            path = os.path.join(base, name)
            if os.path.abspath(path) == os.path.abspath(env):
                continue
            try:
                if key in open(path, encoding="utf-8", errors="ignore").read():
                    leaks.append(os.path.relpath(path, ROOT).replace("\\", "/"))
            except Exception:
                continue
    if leaks:
        tracked, ignored = [], []
        for rel_path in leaks:
            r = subprocess.run(["git", "check-ignore", "-q", rel_path],
                               cwd=ROOT, capture_output=True)
            (ignored if r.returncode == 0 else tracked).append(rel_path)
        if tracked:
            return {"status": "risk",
                    "detail": "**密钥泄漏进被跟踪文件**：" + ", ".join(tracked)}
        return {"status": "green",
                "detail": "无泄漏。密钥另有 %d 处工作副本，均在 gitignore 内（%s）——"
                          "副本可见但不算泄漏（CLAUDE.md 红线只管被跟踪文件）。"
                          % (len(ignored), ", ".join(ignored[:3]))}
    ignored = ".env" in open(rel(".gitignore"), encoding="utf-8").read() if exists(".gitignore") else False
    return {"status": "green",
            "detail": "密钥只出现在 .env（已 gitignore=%s）；全仓 %s 个文件已扫描。"
                      % (ignored, "全部")}


def probe_pile_integrity():
    """piles.json hash lock + no sealed game_id ever appears in a request body."""
    piles = read_json("arc-recon/data/piles.json")
    if not piles:
        return {"status": "missing", "detail": "piles.json 不存在。"}
    sealed = set(GAME_ID.findall(json.dumps(piles.get("sealed_pile", []))))
    dev = set(GAME_ID.findall(json.dumps(piles.get("dev_pile", []))))

    touched = {}
    ledgers = ["baseline-arms/probe_log.jsonl", "arc-recon/data/recon_ledger.jsonl"]
    for led in ledgers:
        for row in iter_jsonl(led):
            body = row.get("request_body")
            if not isinstance(body, dict):
                continue
            for field in ("game_id", "game"):
                gid = body.get(field)
                if isinstance(gid, str):
                    touched.setdefault(gid, set()).add(led)

    hit = sorted(g for g in touched if g in sealed)
    if hit:
        return {"status": "risk",
                "detail": "**封存堆被接触**：" + ", ".join(hit)}
    return {"status": "green",
            "detail": "封存堆 %d 局零接触（已核对 %d 条请求体）；"
                      "开发堆已接触 %d 局：%s"
                      % (len(sealed),
                         sum(1 for l in ledgers for _ in iter_jsonl(l)),
                         len([g for g in touched if g in dev]),
                         ", ".join(sorted(g for g in touched if g in dev)) or "无")}


def probe_determinism_state():
    """Per-game verdicts from arc-recon/data/precheck.json."""
    pre = read_json("arc-recon/data/precheck.json", {})
    results = pre.get("results") or {}
    verdicts = {}
    for gid, r in results.items():
        v = r.get("verdict")
        verdicts[gid] = (v.get("verdict") if isinstance(v, dict) else v) or "?"
    if not verdicts:
        return {"status": "blocked", "detail": "precheck.json 无逐局判决。"}
    n_pass = sum(1 for v in verdicts.values() if v == "PASS")
    detail = "逐局判决：" + "； ".join("%s=%s" % (g.split("-")[0], v)
                                       for g, v in sorted(verdicts.items()))
    if n_pass == len(verdicts):
        return {"status": "green", "detail": detail + "。全 PASS。"}
    return {"status": "partial", "detail": detail}


def probe_a0_state():
    have = {p: exists("cold-start-a0/" + p) for p in [
        "world/a0_world.py", "artifacts/raw_trace.jsonl", "artifacts/candidates.jsonl",
        "theory/theory.dsl", "compile/compile_a0.py", "theory/generated/theory.py",
        "theory/generated/theory.lean", "theory/generated/domain.pddl",
        "certify", "A0_REPORT.md"]}
    done = sum(have.values())
    kinds = {}
    for row in iter_jsonl("cold-start-a0/artifacts/candidates.jsonl"):
        kinds[row.get("kind", "?")] = kinds.get(row.get("kind", "?"), 0) + 1
    missing = [k for k, v in have.items() if not v]
    return {"status": "green" if done == len(have) else "partial",
            "detail": "A0 阶段件 %d/%d 落盘；候选 %s。缺：%s"
                      % (done, len(have),
                         ", ".join("%s×%d" % kv for kv in sorted(kinds.items())) or "无",
                         ", ".join(missing) or "无")}


def probe_a1_state():
    bridge = exists("engine-rig/interop/certificate_export.py")
    consumed = False
    tc = rel("theory-compiler")
    for base, dirs, files in os.walk(tc):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            if name.endswith((".py", ".lean")):
                try:
                    if "certificate" in open(os.path.join(base, name),
                                             encoding="utf-8", errors="ignore").read():
                        consumed = True
                except Exception:
                    pass
    return {"status": "partial",
            "detail": "engine-rig 侧证书导出：%s；theory-compiler 侧消费：%s。"
                      "两半接通前，A1 仍是彩排而非验收。"
                      % ("已建" if bridge else "未建", "已接" if consumed else "**未接**")}


def _discover_territories():
    """Derive the territory list from the tree instead of hardcoding it.

    The hardcoded list stopped at nine directories while the repo grew to
    nineteen, so provenance and conflict checks were blind to ten of them —
    including theoria-arm, the arm that actually spends API money (OPS-A,
    2026-07-28). A top-level directory counts as a territory if it is tracked
    by git and is not tooling.
    """
    skip = {".git", ".claude", ".worktrees", ".pytest_cache", "__pycache__",
            "CONTRACTS", ".toolchain"}
    out = []
    for name in sorted(os.listdir(ROOT)):
        if name.startswith(".") or name in skip:
            continue
        if not os.path.isdir(os.path.join(ROOT, name)):
            continue
        out.append(name)
    return out


TERRITORIES = _discover_territories()
SHARED_OK = {"PARTNER_SYNC.md", "CONTRACTS", "README.md", "LICENSE",
             ".gitignore", ".env.example", "CLAUDE.md", "Theoria.md"}


def probe_conflicts():
    """Multi-agent collaboration conflicts: markers, unmerged paths,
    cross-territory commits. One shared working tree, many sessions."""
    findings = []

    # (a) conflict markers inside files
    marker = re.compile(r"^(<{7} |={7}$|>{7} )", re.M)
    marked = []
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            if not name.endswith((".py", ".md", ".json", ".jsonl", ".dsl",
                                  ".lean", ".pddl", ".lark", ".toml", ".txt")):
                continue
            path = os.path.join(base, name)
            try:
                text = open(path, encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            hits = marker.findall(text)
            if len([h for h in hits if h.startswith("<")]) and \
               len([h for h in hits if h.startswith(">")]):
                marked.append(os.path.relpath(path, ROOT).replace("\\", "/"))
    if marked:
        findings.append("文件内有合并冲突标记：" + ", ".join(marked))

    # (b) unmerged paths in the index
    unmerged = git("ls-files", "-u")
    if unmerged:
        paths = sorted({line.split("\t")[-1] for line in unmerged.splitlines()})
        findings.append("git 未合并路径：" + ", ".join(paths))

    # (c) cross-territory commits: one commit spanning 2+ *owners*.
    # a0-spike belongs to the engine-rig track and cold-start-a0 to the
    # theory-compiler track (CLAUDE.md), so those pairs are one territory.
    track_of = {"engine-rig": "engine-rig", "a0-spike": "engine-rig",
                "theory-compiler": "theory-compiler",
                "cold-start-a0": "theory-compiler"}
    log = git("log", "--name-only", "--format=%h%x01%s", "-40")
    cross = []
    cur = None
    touched = set()

    def flush():
        terrs = {track_of.get(t, t) for t in touched if t in TERRITORIES}
        if cur and len(terrs) > 1:
            cross.append("%s（%s）" % (cur, "+".join(sorted(terrs))))
    for line in log.splitlines():
        if "\x01" in line:
            flush()
            cur = line.replace("\x01", " ")[:64]
            touched = set()
        elif line.strip():
            top = line.split("/")[0]
            if top not in SHARED_OK:
                touched.add(top)
    flush()
    if cross:
        findings.append("跨领地提交（一个 commit 改了多个轨道 —— 领地纪律被破）：" +
                        "； ".join(cross))

    if not findings:
        return {"status": "green",
                "detail": "三类检查全空：无冲突标记、无未合并路径、"
                          "近 40 个提交无跨领地改动。"}
    return {"status": "risk", "detail": " ⚠ ".join(findings)}


def probe_provenance():
    """留痕审计：每个领地的实验中间产物必须进 append-only 的 runs/ 档案。

    v1 盘点两件事：各领地有没有 runs/ 档案（多少个 run、MANIFEST 覆盖率、
    最新一次）；以及哪些领地存在明显的实验产物目录（artifacts/ out/ data/）
    却完全没有 runs/ —— 这些是当前留痕规则的欠账。规则本身生效于分支制
    第一批（提示词逐份携带），所以欠账在此如实计数、不定罪既往。"""
    exp_dirs = ("artifacts", "out", "data")
    rows, debt = [], []
    for terr in TERRITORIES:
        if terr == "monitor" or not exists(terr):
            continue
        has_products = any(
            os.path.isdir(rel(terr, d)) or
            any(os.path.isdir(os.path.join(base, d))
                for base, dirs, _ in os.walk(rel(terr))
                if not any(s in base for s in SKIP_DIRS)
                for d in dirs if d in exp_dirs)
            for d in exp_dirs)
        runs_dir = rel(terr, "runs")
        if os.path.isdir(runs_dir):
            runs = [d for d in sorted(os.listdir(runs_dir))
                    if os.path.isdir(os.path.join(runs_dir, d))]
            canon = sum(1 for d in runs
                        if os.path.exists(os.path.join(runs_dir, d,
                                                       "MANIFEST.json")))
            noncanon = sum(1 for d in runs
                           if not os.path.exists(
                               os.path.join(runs_dir, d, "MANIFEST.json"))
                           and any(f.startswith("MANIFEST")
                                   for f in os.listdir(
                                       os.path.join(runs_dir, d))))
            none_at_all = len(runs) - canon - noncanon
            rows.append("%s：%d 个 run（正典 %d%s%s），最新 %s"
                        % (terr, len(runs), canon,
                           "，非正典 %d(md)" % noncanon if noncanon else "",
                           "，**无留痕 %d**" % none_at_all if none_at_all else "",
                           runs[-1] if runs else "—"))
        elif has_products:
            debt.append(terr)
    detail = ""
    if rows:
        detail += "已建档：" + "； ".join(rows) + "。"
    if debt:
        detail += ("尚无 runs/ 档案的产物领地（留痕规则的欠账，分支制第一批"
                   "起逐个清偿）：" + ", ".join(debt) + "。")
    if not rows and not debt:
        return {"status": "green", "detail": "无实验产物领地。"}
    return {"status": "green" if not debt else "partial", "detail": detail}


def probe_dispatch_board():
    """工作板：每份派出的提示词的双列状态 —— 自报 vs 核实。

    自报 = PARTNER_SYNC 里出现该工单号的段落 / 分支已 push；
    核实 = 监控探针能在树上摸到验收产物。两列不一致即标出。"""
    sync = ""
    if exists("PARTNER_SYNC.md"):
        sync = open(rel("PARTNER_SYNC.md"), encoding="utf-8", errors="ignore").read()
    branches = git("branch", "-a", "--format=%(refname:short)")
    rows = []
    pdir = os.path.join(HERE, "prompts")
    if os.path.isdir(pdir):
        for name in sorted(os.listdir(pdir)):
            if not name.startswith(("P-", "M-", "R-")) or not name.endswith(".md"):
                continue
            pid = name.split("-")[0] + "-" + name.split("-")[1]
            slug = pid.lower()
            branch = next((b for b in branches.splitlines()
                           if slug in b.lower() and "agent/" in b), "")
            self_rep = pid in sync or bool(branch)
            rows.append({"prompt": name, "id": pid,
                         "branch": branch or "—",
                         "self_reported": self_rep})
    if not rows:
        # 工作板取代了逐件派单，prompts/ 目录自然空了——但「空」在这里
        # 不等于「无事」，报 green 会让盘面看起来比现实干净。
        return {"status": "green",
                "detail": "派单已由工作板取代（见 supply 探针），本探针不再适用。",
                "rows": [], "retired": True}
    n_rep = sum(1 for r in rows if r["self_reported"])
    return {"status": "green" if n_rep else "partial",
            "detail": "%d 份在册工单，%d 份有自报痕迹（分支或 PARTNER_SYNC）。"
                      "核实列以各专项探针为准。" % (len(rows), n_rep),
            "rows": rows}


def probe_inbox():
    """monitor/inbox/ 的待裁决提案。"""
    pdir = os.path.join(HERE, "inbox")
    pending = [f for f in sorted(os.listdir(pdir))
               if f.endswith(".md") and f != "README.md"] if os.path.isdir(pdir) else []
    if not pending:
        return {"status": "green", "detail": "提案箱空。"}
    return {"status": "partial",
            "detail": "待裁决提案 %d 份：%s" % (len(pending), ", ".join(pending))}


def probe_append_only():
    """Append-only files must never lose a line (DRIFT-3 suggestion 2).
    Judged mechanically: total deletions across each file's whole history."""
    watched = ["PARTNER_SYNC.md", "arc-recon/data/incidents.jsonl",
               "arc-recon/data/contamination_log.jsonl",
               "battery/PREDICTIONS.md"]
    # Deletions already adjudicated (same-window self-correction, ruled
    # 2026-07-28: no incident). Counted as baseline so the probe measures
    # NEW violations instead of being born red and never able to go green.
    # One adjudicated deletion on the mainline: 63ef0bf, a same-window
    # self-correction (3->4 samples). 6dec6f7 is NOT counted -- it edited a
    # paragraph that had never reached master, which publishes nothing.
    # The line the rule actually draws: once it is on the mainline it is
    # frozen; on a branch, fix it until it is right.
    BASELINE = {"PARTNER_SYNC.md": 1}
    offenders = []
    for path in watched:
        if not exists(path):
            continue
        # --first-parent: only what actually appeared on the mainline counts.
        # A branch-local fix before merge never published anything, so it is
        # not a violation (OPS-A, 2026-07-28: my earlier ruling cited it wrongly).
        out = git("log", "--first-parent", "--numstat", "--format=%h", "--", path)
        dels, cur = 0, ""
        for line in out.splitlines():
            parts = line.split("	")
            if len(parts) == 3 and parts[1].isdigit():
                dels += int(parts[1])
            elif line.strip():
                cur = line.strip()
        allowed = BASELINE.get(path, 0)
        if dels > allowed:
            offenders.append("%s（删除 %d 行，超出已裁决豁免 %d 行）"
                             % (path, dels, allowed))
    if offenders:
        return {"status": "risk",
                "detail": "追加式文件出现删除：" + "； ".join(offenders) +
                          "。既往裁决：同窗口自我订正可，跨窗口须新段落 supersede。"}
    exempt = sum(BASELINE.values())
    return {"status": "green",
            "detail": "%d 个追加式文件无新增删除（%d 行历史删除已裁决豁免："
                      "同窗口自我订正）。" % (len(watched), exempt)}


OPS_DUTY = [
    ("OPS-A", "漂移审计员", 90),      # (id, name, stale-after minutes)
    ("OPS-B", "浏览器专员", 180),
    ("OPS-M", "合并裁判", 150),
    ("OPS-R", "回顾员", 900),
]


def probe_ops_duty():
    """运维值班：四个 App 常驻会话通过统一心跳文件监控（隔离契约：不读对话）。
    monitor/ops-status/<ID>.json 每周期由它们自己写；缺失=未启动，陈旧=可能掉线。"""
    rows, stale, missing = [], [], []
    for oid, name, stale_min in OPS_DUTY:
        path = "monitor/ops-status/%s.json" % oid
        data = read_json(path, None)
        if not data:
            rows.append({"id": oid, "name": name, "status": "missing",
                         "age_min": None, "cycle": None, "state": "未启动",
                         "note": "等待启动握手"})
            missing.append(oid)
            continue
        age = (time.time() - os.path.getmtime(rel(path))) / 60
        status = "risk" if age > stale_min else "green"
        if status == "risk":
            stale.append(oid)
        rows.append({"id": oid, "name": name, "status": status,
                     "age_min": int(age), "cycle": data.get("cycle"),
                     "state": data.get("state", "?"),
                     "note": data.get("note", "")})
    # unread messages from the ops agents
    tm = 0
    mb = rel("monitor", "mailbox")
    if os.path.isdir(mb):
        for f in os.listdir(mb):
            if not f.startswith("OPS-") or not f.endswith(".md"):
                continue          # PROTOCOL.md describes the format; not a message
            for line in open(os.path.join(mb, f), encoding="utf-8",
                             errors="ignore"):
                if line.startswith("## TO-MONITOR"):
                    tm += 1
    detail = "； ".join(
        "%s %s" % (r["id"], "未启动" if r["status"] == "missing"
                   else "第%s轮 %s（%d 分钟前）" % (r["cycle"], r["state"],
                                                   r["age_min"]))
        for r in rows)
    if tm:
        detail = "**%d 条 TO-MONITOR 待监控回复**。 " % tm + detail
    # 未回复的 TO-MONITOR 必须影响状态：把它只写进 detail 而状态仍报 green，
    # 正是今天反复出现的「沉默的乐观」——盘面绿着，欠债堆着。
    st = "risk" if stale else ("partial" if (missing or tm) else "green")
    return {"status": st, "detail": detail, "rows": rows, "to_monitor": tm}


def probe_scheduled_tasks():
    """The automation itself needs a watchdog: OPS-M and OPS-R both reported
    TheoriaReflex sitting Disabled with nothing on the board saying so."""
    want = {"TheoriaReflex": "reap / quota / 自动合并",
            "TheoriaDashboard": "每 10 分钟重算 state.json",
            "TheoriaServe": "本地服务 :8787（前端拉数据）"}
    rows, bad = [], []
    for name, role in want.items():
        out = subprocess.run(["schtasks", "/Query", "/TN", name, "/FO", "LIST"],
                             capture_output=True, text=True,
                 encoding="utf-8", errors="replace")
        if out.returncode != 0:
            rows.append("%s **未注册**（%s）" % (name, role))
            bad.append(name)
            continue
        txt = out.stdout
        disabled = ("Disabled" in txt) or ("已禁用" in txt)
        rows.append("%s %s（%s）" % (name, "**已禁用**" if disabled else "运行中", role))
        if disabled:
            bad.append(name)
    return {"status": "risk" if bad else "green",
            "detail": "； ".join(rows) +
                      ("　→ 自动化有缺口：" + ", ".join(bad) if bad else "")}


def probe_spec_freshness():
    """手写判断 vs 树的漂移速度：spec.py 最后一次改动之后进了多少提交与合并。
    DRIFT dashboard-lags-the-merge-queue 说的正是这个——头条数字建立在手写值上，
    而树在跑。让陈旧本身变成盘面上的一个数，而不是靠审计员发现。"""
    last = git("log", "-1", "--format=%H", "--", "monitor/spec.py").strip()
    if not last:
        return {"status": "partial", "detail": "spec.py 无提交历史。"}
    commits = git("rev-list", "--count", "%s..HEAD" % last).strip() or "0"
    merges = git("rev-list", "--count", "--merges", "%s..HEAD" % last).strip() or "0"
    n, m = int(commits), int(merges)
    status = "green" if n < 15 else ("partial" if n < 40 else "risk")
    return {"status": status,
            "detail": "spec.py 落后 %d 个提交 / %d 次合并（判断陈旧到 %s 就该重扫）。"
                      % (n, m, "risk" if n >= 40 else "partial 档")}


def probe_verify_gates():
    """收工闸门：**「声称有却没有」与「本来就没有」是两回事**，分开报。

    DRIFT stop-hook-verify-gates-are-decoration：C2 已合并，它自己命名的
    a0-spike/verify.sh 从未被造出来，合并时无人发现。那是第一种。

    第二种是 S13 的根因：工单里「写一个 verify 脚本」是自觉条款，于是有些领地
    压根没有闸门——而这不是任何人食言，是从来没人要求过。把两者混成一个数字，
    结果就是要么冤枉了老实人，要么放过了漏洞。所以：第一种是 risk（有人声称了
    不存在的东西），第二种是 amber 的一句实话（合并时无人检查），**并且现在
    ci_merge 每次都会把它打进 merge.log**。

    另修一处：旧正则只认 `.sh`，工单若写 `worldgen/verify.py` 会**静默漏检**。
    """
    import glob

    import gates as gates_mod

    # 只认第一段是**真实领地目录**的路径。否则散文里一句
    # 「若该领地存在 verify.sh/verify.py 就必须跑它」会被读成
    # 「有人声称存在 `verify.sh/verify.py` 这个文件」——S13 自己的工单文本
    # 第一次跑这条探针时就是这样误报的。会喊狼的检查会被关掉，而一条被关掉的
    # 检查和一条不存在的检查是同一回事。
    known = set(gates_mod.territories(ROOT))
    named, missing = [], []
    pattern = re.compile(r"([\w./-]+/verify[\w.-]*\.(?:sh|py))")
    for d in ("monitor/board/items", "monitor/board/claimed", "monitor/board/done"):
        for f in glob.glob(os.path.join(rel(d), "*.md")):
            try:
                text = open(f, encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            for m in pattern.finditer(text):
                path = m.group(1)
                if path.split("/")[0] not in known:
                    continue
                named.append(path)
                if not exists(path):
                    missing.append("%s（%s 声称）"
                                   % (path, os.path.basename(f).split(".")[0]))
    missing = sorted(set(missing))

    survey = gates_mod.survey(ROOT)
    ungated = survey["ungated"]
    coverage = "领地 %d：自带闸门 %d、仅测试套件 %d、**无闸门 %d**" % (
        survey["n_territories"], len(survey["gated"]),
        len(survey["tests_only"]), len(ungated))

    if missing:
        return {"status": "risk",
                "detail": "**声称存在却没有的收工闸门 %d 处**：%s。"
                          "闸门不是被绕过，是根本没造出来。（另：%s）"
                          % (len(missing), "； ".join(missing[:4]), coverage)}
    if ungated:
        return {"status": "amber",
                "detail": "工单声称的 %d 个 verify 脚本全部在树上；"
                          "但**%d 个领地合并时无人检查**：%s。%s。"
                          "这不是有人食言——是从来没人要求过，"
                          "ci_merge 现在每次把它打进 merge.log。"
                          % (len(set(named)), len(ungated),
                             "、".join(ungated), coverage)}
    return {"status": "green",
            "detail": "工单声称的 %d 个 verify 脚本全部在树上，且每个领地都有闸门。%s"
                      % (len(set(named)), coverage)}


def _supply():
    """板上还剩几件可领 —— 供货是监控的单点，见底就是全员空转。"""
    out = subprocess.run([sys.executable, os.path.join(HERE, "board.py"), "list"],
                         cwd=ROOT, capture_output=True, text=True,
                 encoding="utf-8", errors="replace").stdout
    avail = len([l for l in out.splitlines() if l.startswith("  p")])
    claimed = out.count(" by ")
    if avail == 0:
        return {"status": "risk",
                "detail": "**板已见底**：%d 件在做，0 件可领——有人交付即空转，"
                          "监控必须补货。" % claimed}
    if avail <= 2:
        return {"status": "partial",
                "detail": "板上仅剩 %d 件可领（%d 件在做），供货需要跟上。"
                          % (avail, claimed)}
    return {"status": "green",
            "detail": "板上 %d 件可领、%d 件在做，供货充足。" % (avail, claimed)}


def _bus_probe():
    """托管是否真的成立：指令送达了吗、回执欠着吗、谁多久没露面。

    直接读总线文件，不经子进程——今天已经两次被 GBK/UTF-8 的解码差异咬到
    （一次把八个活着的工人报成已停，一次把未读报成已回执）。判据只信文件。"""
    agents_ids = ["OPS-A", "OPS-B", "OPS-M", "OPS-R",
                  "RES-1", "RES-2", "RES-3", "RES-4"]
    never, owed, seen_ok = [], [], 0
    for a in agents_ids:
        d = rel("monitor", "bus", a)
        inbox = os.path.join(d, "in.jsonl")
        cur = os.path.join(d, "cursor.json")
        out = os.path.join(d, "out.jsonl")
        if not os.path.exists(inbox):
            continue
        sent = [json.loads(l) for l in open(inbox, encoding="utf-8")
                if l.strip()]
        last = 0
        if os.path.exists(cur):
            try:
                last = json.load(open(cur, encoding="utf-8")).get("last_seq", 0)
                seen_ok += 1
            except Exception:
                pass
        else:
            never.append(a)
            continue
        acked = set()
        if os.path.exists(out):
            for l in open(out, encoding="utf-8"):
                if l.strip():
                    r = json.loads(l)
                    if r.get("kind") == "ack":
                        acked.add(r.get("ref"))
        pend = [m["seq"] for m in sent
                if m["kind"] in ("order", "question") and m["seq"] not in acked]
        if pend:
            owed.append("%s(%d)" % (a, len(pend)))
    if never:
        return {"status": "partial",
                "detail": "总线已上线；**%d 个会话还没读过**（%s）——"
                          "它们下个循环读到指令后即被托管。"
                          % (len(never), ", ".join(never))}
    if owed:
        return {"status": "partial",
                "detail": "已送达，欠回执：" + ", ".join(owed)}
    return {"status": "green",
            "detail": "%d 个会话在线，指令全部已读并回执。" % seen_ok}


def _self_driving():
    """常驻研究员是否在自转 —— 用户不该需要触发它们。

    判据是心跳的推进：cycle 在涨、note 在变、age 不超过一个循环周期。
    停在那里等人的会话，心跳会定格——这正是用户今天观察到的现象。"""
    import time as _t
    rows = []
    for rid in ("RES-1", "RES-2", "RES-3", "RES-4"):
        path = "monitor/ops-status/%s.json" % rid
        if not exists(path):
            rows.append("%s 未启动" % rid)
            continue
        d = read_json(path, {}) or {}
        age = int((_t.time() - os.path.getmtime(rel(path))) / 60)
        stalled = age > 45          # 一轮活再长也该在 45 分钟内写一次心跳
        rows.append("%s 第%s轮 %s（%d 分钟前）%s"
                    % (rid, d.get("cycle"), d.get("state"), age,
                       "**疑似停下等人**" if stalled else ""))
    stalled_any = any("疑似停下" in r for r in rows)
    return {"status": "risk" if stalled_any else "green",
            "detail": "； ".join(rows) +
                      ("　→ 已发 urgent 催醒；若仍不动，说明会话已死，需重开。"
                       if stalled_any else "")}


def _offline_done():
    """离线收工没有？——收工即可全力转向烧钱与墙钟的战役（用户已授权）。

    判据是离线七格：引擎两格、编译两格、评测两格、离线对局一格。
    它们都 >=95 时，建造期正式结束，剩余重量全在战役与写作上。"""
    cells = {"E1": "引擎建成", "E2": "引擎验证", "C1": "编译链",
             "C2": "离线验收", "V1": "指标电池", "V2": "考卷",
             "A2": "自建世界对局"}
    lag = [(k, spec.GRID.get(k, {}).get("pct", 0), v)
           for k, v in cells.items() if spec.GRID.get(k, {}).get("pct", 0) < 95]
    if not lag:
        return {"status": "green",
                "detail": "**离线已收工**（七格全 ≥95%）——战役线可全速；"
                          "其余赛道转纯 token 工作。"}
    return {"status": "partial",
            "detail": "离线还差 %d 格：%s。战役线已获授权可先行，不必等齐。"
                      % (len(lag), "、".join("%s %s(%d%%)" % (k, v, p)
                                             for k, p, v in lag))}


def _spend_watch():
    """花了多少、剩多少 —— 账号额度是唯一的真约束，且是共享池。"""
    led = rel("proxy", "var", "spend_gate.jsonl")
    if not os.path.exists(led):
        return {"status": "partial", "detail": "闸门账本尚未产生记录。"}
    total, rows = 0.0, 0
    by_campaign = {}
    for line in open(led, encoding="utf-8", errors="ignore"):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        usd = float(r.get("usd") or 0)
        total += usd
        rows += 1
        c = r.get("campaign") or "未标注"
        by_campaign[c] = by_campaign.get(c, 0.0) + usd
    ENVELOPE = 200.0
    left = ENVELOPE - total
    detail = ("开发堆战役包 $%.0f，已花 **$%.2f**，剩 $%.2f（%d 条记账）"
              % (ENVELOPE, total, left, rows))
    if by_campaign:
        detail += "；分战役：" + "、".join(
            "%s $%.2f" % (k, v) for k, v in sorted(by_campaign.items())[:4])
    if left < 40:
        return {"status": "risk", "detail": detail + "　→ **余额不足，需续包**"}
    return {"status": "green", "detail": detail}


def probe_needs_human():
    """全系统唯一需要人出手的事：App 会话死了（上下文满或被关）。

    无头工人由反射层补员，配额由熔断器自愈，合并由脚本做，供货由监控写——
    只有 App 里的会话没有任何 API 能重启它。所以它必须是页面上最显眼的
    行动项，而且要精确到"重开哪一个、粘哪份启动词"。"""
    import time as _t
    roster = [("OPS-A", "漂移审计员", 120), ("OPS-B", "浏览器专员", 240),
              ("OPS-M", "合并裁判", 180), ("OPS-R", "回顾员", 900),
              ("RES-1", "在线战役研究员", 90), ("RES-2", "论文与释出研究员", 90),
              ("RES-3", "验证与考卷研究员", 90), ("RES-4", "基础设施研究员", 90)]
    dead = []
    for rid, name, stale_min in roster:
        path = "monitor/ops-status/%s.json" % rid
        if not exists(path):
            dead.append((rid, name, "从未启动"))
            continue
        age = (_t.time() - os.path.getmtime(rel(path))) / 60
        if age > stale_min:
            dead.append((rid, name, "%d 分钟没心跳" % age))
    if not dead:
        return {"status": "green", "detail": "六个 App 会话全部在岗，无需你出手。",
                "rows": []}
    return {"status": "risk",
            "detail": "需要你重开的会话：" + "； ".join(
                "%s %s（%s）" % (r, n, w) for r, n, w in dead),
            "rows": [{"id": r, "name": n, "why": w,
                      "prompt": "monitor/prompts/ops/%s.md" % r}
                     for r, n, w in dead]}


PROBES = {
    "credential_hygiene": probe_credential_hygiene,
    "needs_human": probe_needs_human,
    "offline_done": lambda: _offline_done(),
    "spend": lambda: _spend_watch(),
    "self_driving": lambda: _self_driving(),
    "bus": lambda: _bus_probe(),
    "supply": lambda: _supply(),
    "spec_freshness": probe_spec_freshness,
    "verify_gates": probe_verify_gates,
    "scheduled_tasks": probe_scheduled_tasks,
    "append_only": probe_append_only,
    "ops_duty": probe_ops_duty,
    "conflict_scan": probe_conflicts,
    "provenance_scan": probe_provenance,
    "dispatch_board": probe_dispatch_board,
    "inbox": probe_inbox,
    "pile_integrity": probe_pile_integrity,
    "determinism_state": probe_determinism_state,
    "a0_state": probe_a0_state,
    "a1_state": probe_a1_state,
}


# ---------------------------------------------------------------- metrics

def run_tests():
    out = {}
    for track in ("engine-rig", "theory-compiler"):
        try:
            proc = subprocess.run([sys.executable, "-m", "pytest", "-q"],
                                  cwd=rel(track), capture_output=True, text=True,
                                  encoding="utf-8", errors="replace",
                                  timeout=900)
            tail = [l for l in proc.stdout.strip().splitlines() if l.strip()][-1:]
            out[track] = tail[0] if tail else "no output"
        except Exception as exc:
            out[track] = "run failed: %s" % exc
    return out


def collect_metrics(with_tests):
    m = {}
    m["git_head"] = git("log", "-1", "--format=%h %s")
    m["git_branch"] = git("rev-parse", "--abbrev-ref", "HEAD")
    status = git("status", "--porcelain")
    m["dirty"] = [l[3:] for l in status.splitlines()] if status else []
    m["untracked"] = [l[3:] for l in status.splitlines() if l.startswith("??")] if status else []

    piles = read_json("arc-recon/data/piles.json", {})
    m["dev_pile"] = sorted(set(GAME_ID.findall(json.dumps(piles.get("dev_pile", [])))))
    m["sealed_count"] = len(set(GAME_ID.findall(json.dumps(piles.get("sealed_pile", [])))))
    m["piles_sha"] = (piles.get("sha256") or "")[:16]

    m["engine_candidates"] = count_lines("engine-rig/artifacts/candidates.jsonl")
    m["a0_candidates"] = count_lines("cold-start-a0/artifacts/candidates.jsonl")
    m["a0_transitions"] = (read_json("cold-start-a0/artifacts/engines_report.json", {})
                           or {}).get("transitions", 0)
    m["incidents"] = count_lines("arc-recon/data/incidents.jsonl")
    m["sync_entries"] = 0
    if exists("PARTNER_SYNC.md"):
        m["sync_entries"] = len(re.findall(r"^## \[", open(rel("PARTNER_SYNC.md"),
                                                           encoding="utf-8").read(), re.M))
        stamps = re.findall(r"^## \[.*?\] (\S+)", open(rel("PARTNER_SYNC.md"),
                                                       encoding="utf-8").read(), re.M)
        m["sync_last"] = stamps[-1] if stamps else "—"
    m["tests"] = run_tests() if with_tests else {}
    return m


def score(items):
    order = ["green", "partial", "risk", "blocked", "missing"]
    counts = {k: 0 for k in order}
    for it in items:
        counts[it.get("_status", it.get("status", "missing"))] = \
            counts.get(it.get("_status", it.get("status", "missing")), 0) + 1
    return counts


# ---------------------------------------------------------------- history

def compute_progress(phases):
    """Whole-programme progress: 100% = every experiment run and released.

    Denominator = all four phases of Theoria.md, weighted by spec.PHASE_WEIGHTS
    (a recorded judgement, not a measurement); numerator = per-item status
    scores from spec.STATUS_SCORE. Both live in spec.py so changing the
    definition of "done" is a visible, reviewable edit.
    """
    by_phase = []
    total = 0.0
    for ph in phases:
        w = spec.PHASE_WEIGHTS.get(ph["id"], 0)
        items = ph["items"]
        score = (sum(spec.STATUS_SCORE.get(it["_status"], 0) for it in items)
                 / len(items)) if items else 0.0
        contrib = w * score
        total += contrib
        by_phase.append({"id": ph["id"], "name": ph["name"], "weight": w,
                         "pct": round(100 * score, 1),
                         "contrib": round(100 * contrib, 2)})
    return {"total": round(100 * total, 1), "by_phase": by_phase}


def compute_paper_progress():
    """Progress toward the publishable paper — the official target since
    2026-07-28. Denominator = PAPER_PLAN in spec.py (Schema-scale campaign)."""
    total = sum(p["weight"] * p["pct"] for p in spec.PAPER_PLAN)
    return round(total, 1)


def append_history(state, out_dir=None):
    """One JSONL row per scan — the raw material of the trend chart."""
    row = {
        "ts": state["generated_at"],
        "progress": state["progress"]["total"],
        "paper_progress": state["paper_progress"],
        "sections": {s["name"]: s["counts"] for s in state["sections"]},
        "findings": {},
    }
    for f in state["findings"]:
        row["findings"][f["severity"]] = row["findings"].get(f["severity"], 0) + 1
    hist_path = os.path.join(out_dir or HERE, "history.jsonl")
    last = None
    if os.path.exists(hist_path):
        with open(hist_path, encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    last = line.strip()
    payload = json.dumps(row, ensure_ascii=False, sort_keys=True)
    # skip the append when nothing moved — watch mode would flood the file
    if last:
        try:
            prev = json.loads(last)
            if prev.get("sections") == row["sections"] and \
               prev.get("findings") == row["findings"]:
                return
        except Exception:
            pass
    with open(hist_path, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(payload + "\n")


def load_history():
    rows = list(iter_jsonl(os.path.join("monitor", "history.jsonl")))
    return rows


# ---------------------------------------------------------------- render

# 人话层：把专有名词翻译成任何人扫一眼就懂的表述。数据仍来自 spec，
# 这里只管怎么说。
PLAIN_WP = {
    "WP1": ("造仪器", "引擎、编译器、离线彩排——AI 理解世界要用的全套工具"),
    "WP2": ("防作弊外壳", "所有实验经代理留痕，考题保密由程序保证"),
    "WP3": ("AI 上线练习", "让 AI 第一次在真游戏里学规则、做证明（练习关）"),
    "WP4": ("对照组数据", "普通 AI 和前人方法在同样关卡上的成绩"),
    "WP5": ("打分体系", "怎么衡量『真的理解了』：指标电池 + 考卷"),
    "WP6": ("正式大考", "在从未见过的 19 个关卡上跑完全部对比实验"),
    "WP7": ("附加考题", "不可解判定、换规则适应、移交测试"),
    "WP8": ("统计与预注册", "先写下预测再看结果，防止事后编故事"),
    "WP9": ("写论文", "从车间报告到可投稿的正文"),
    "WP10": ("公开一切", "代码、数据、证明全量释出，任何人可复跑"),
}
PLAIN_TASK = {
    "P-8": "让 AI 第一次上线打真游戏",
    "P-9": "给实验外壳上锁（打分器 + 防作弊复测）",
    "P-10": "升级两条流水线之间的数据契约",
    "P-11": "考题保密审计与登记",
    "P-12": "补齐对照组的成绩数据",
    "P-13": "接入专业规划求解器",
    "P-14": "扩充打分体系并首次对比两组 AI",
    "P-15": "出考卷的机器（四种题型）",
    "P-16": "写第一篇阶段论文草稿",
    "P-17": "验证『学会的知识能带去下一关』",
    "P-18": "造对照版 AI（去掉证明能力的消融臂）",
    "P-19": "打包公开：陌生人一条命令复跑全部",
    "P-20": "实测游戏一步会不会动好几帧",
    "P-21": "把数据画成论文用的图",
    "P-22": "起草大考前要封存的规则包",
    "P-23": "整理相关文献与引用",
    "P-24": "沉淀舰队通用技能，加速后续会话",
    "E1-property-fuzz": "用 500 个随机世界轰炸六引擎找 bug",
    "A2-crosscheck": "两套独立 AI 实现互考对方的世界",
    "C1-worldgen": "批量造 20 个练习世界（弹药库）",
    "P3-case-study": "写三个深度案例（概念诞生/可逆性/假定理）",
    "R-1": "复盘：从过去的失败里找规律",
    "B-1": "浏览器专员：处理需要真人网页的事",
    "M-0": "合并员：把所有人的成果安全合到主线",
    "A-1": "常驻审计员：低频巡查项目漂移",
}
STAGES = [
    ("① 造仪器", ["WP1", "WP2", "WP5"], "工具、外壳、打分体系"),
    ("② 上线练习", ["WP3", "WP4"], "练习关实战 + 对照组"),
    ("③ 正式大考", ["WP6", "WP7", "WP8"], "封存关卡上的确证实验"),
    ("④ 论文与公开", ["WP9", "WP10"], "写作与全量释出"),
]

LABEL = {"green": "达成", "partial": "部分", "risk": "有风险",
         "blocked": "受阻", "missing": "缺失", "info": "记录"}
SEV = {"blocking": "阻塞", "high": "高", "medium": "中", "low": "低", "info": "信息"}
STATUS_ORDER = ["green", "partial", "risk", "blocked", "missing"]


def esc(s):
    return html.escape(str(s)).replace("\n\n", "<br><br>").replace("\n", " ")


def md_bold(s):
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", s)


def cell(status):
    return '<span class="pill %s">%s</span>' % (status, LABEL.get(status, status))


# ---------------------------------------------------------------- charts
#
# Colors follow the dataviz status formula: these are *status* colors (state),
# not categorical series — good/warning/serious/critical + neutral, defined as
# CSS variables so both themes get their own validated steps. Identity is never
# color-alone: every segment carries a title tooltip and the legend names each
# state; counts are direct-labeled.

def chart_legend():
    return ('<div class="legend">' + "".join(
        '<span class="lg"><i class="sw %s"></i>%s</span>' % (s, LABEL[s])
        for s in STATUS_ORDER) + "</div>")


def chart_stacked(sections):
    """One horizontal stacked bar per section — the progress map at a glance."""
    out = ['<div class="stack">']
    for sec in sections:
        total = sum(sec["counts"].values()) or 1
        segs = []
        for s in STATUS_ORDER:
            n = sec["counts"].get(s, 0)
            if not n:
                continue
            pct = 100.0 * n / total
            label = str(n) if pct >= 7 else ""
            segs.append('<i class="seg %s" style="width:%.2f%%" '
                        'title="%s：%s %d/%d">%s</i>'
                        % (s, pct, esc(sec["name"]), LABEL[s], n, total, label))
        out.append('<div class="srow"><span class="sname">%s</span>'
                   '<span class="sbar">%s</span>'
                   '<span class="stot">%d/%d 达成</span></div>'
                   % (esc(sec["name"]), "".join(segs),
                      sec["counts"].get("green", 0), total))
    out.append("</div>")
    return "".join(out)


def chart_trend(history):
    """Progress (%) across scans — paper-workload basis where recorded."""
    pts = [(row.get("ts", ""), row.get("paper_progress", row.get("progress")))
           for row in history
           if row.get("paper_progress") is not None or "progress" in row]
    if not pts:
        return '<p class="note">尚无历史 —— 每次扫描若有变化会自动记一笔。</p>'

    W, H, PL, PR, PT, PB = 860, 240, 46, 16, 18, 34
    iw, ih = W - PL - PR, H - PT - PB
    ymax = max(20.0, min(100.0, max(p[1] for p in pts) * 1.6))
    n = len(pts)

    def x(i):
        return PL + (iw * i / max(n - 1, 1) if n > 1 else iw / 2)

    def y(v):
        return PT + ih - ih * v / ymax

    svg = ['<svg viewBox="0 0 %d %d" role="img" aria-label="研究总进度趋势" '
           'style="width:100%%;height:auto">' % (W, H)]
    step = max(5, int(ymax // 4 / 5) * 5)
    gv = 0
    while gv <= ymax:
        svg.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" class="grid"/>'
                   % (PL, y(gv), W - PR, y(gv)))
        svg.append('<text x="%d" y="%.1f" class="tick" text-anchor="end">%d%%</text>'
                   % (PL - 8, y(gv) + 4, gv))
        gv += step
    path = " ".join("%s%.1f %.1f" % ("M" if i == 0 else "L", x(i), y(p[1]))
                    for i, p in enumerate(pts))
    svg.append('<path d="%s" class="line t1"/>' % path)
    for i, p in enumerate(pts):
        svg.append('<circle cx="%.1f" cy="%.1f" r="4" class="dot t1">'
                   '<title>%s\n研究总进度 %.1f%%</title></circle>'
                   % (x(i), y(p[1]), esc(p[0]), p[1]))
    svg.append('<text x="%d" y="%.1f" class="dl t1" text-anchor="end">总进度 %.1f%%</text>'
               % (W - PR, y(pts[-1][1]) - 10, pts[-1][1]))
    svg.append('<text x="%d" y="%d" class="tick">%s</text>'
               % (PL, H - 10, esc(pts[0][0][:16])))
    if n > 1:
        svg.append('<text x="%d" y="%d" class="tick" text-anchor="end">%s</text>'
                   % (W - PR, H - 10, esc(pts[-1][0][:16])))
    svg.append("</svg>")
    return "".join(svg)


def hero_progress(progress):
    """The headline: how far the whole research programme is, 0–100."""
    segs = []
    for bp in progress["by_phase"]:
        filled = bp["weight"] * bp["pct"]          # % of the whole bar
        rest = bp["weight"] * 100 - filled
        title = "%s：本段完成 %.0f%%（占总进度权重 %.0f%%，贡献 %.1f 分）" % (
            bp["name"], bp["pct"], bp["weight"] * 100, bp["contrib"])
        if filled > 0.2:
            segs.append('<i class="hseg fill" style="width:%.2f%%" title="%s"></i>'
                        % (filled, esc(title)))
        if rest > 0.2:
            segs.append('<i class="hseg rest" style="width:%.2f%%" title="%s"></i>'
                        % (rest, esc(title)))
    rows = "".join(
        '<div class="hrow"><span class="hn">%s</span>'
        '<span class="hb"><i style="width:%.1f%%"></i></span>'
        '<span class="hv">%.0f%% <em>×%.0f%%</em></span></div>'
        % (esc(bp["name"]), bp["pct"], bp["pct"], bp["weight"] * 100)
        for bp in progress["by_phase"])
    return ('<div class="hero"><div class="hnum">%.1f<small>%%</small></div>'
            '<div class="hbody"><div class="htitle">论文完成度'
            '<span class="note">　100%% = 可发表的主论文：实验规模对标 Schema'
            '（全公开集 + 全量 artifacts 释出的地板）。分母是下方论文工作量地图'
            '（monitor/spec.py 的 PAPER_PLAN）；四段进度为参考口径：%.1f%%。</span>'
            '</div><div class="hbar">%s</div><div class="hrows">%s</div></div></div>'
            % (progress["paper"], progress["total"], "".join(segs), rows))


FIX_LABEL = {"landed": ("已回灌", "green"), "dispatched": ("修复中·已派工", "partial"),
             "ruled": ("已裁决·待派工", "blocked"), "open": ("未修", "risk")}


def loop_board():
    """The main loop of the research: experiment → problem → framework fix."""
    out = ['<p class="doctrine">%s</p>' % esc(spec.ITERATION_DOCTRINE)]
    n_prob = n_landed = 0
    rows_html = []
    for ex in spec.ITERATION_LOOP:
        rows_html.append('<div class="exp %s">' % ex["status"])
        rows_html.append('<div class="exhead"><span class="pill %s">%s</span>'
                         '<b>%s</b><span class="exsum">%s</span></div>'
                         % (ex["status"], "实验·" + LABEL.get(ex["status"], ""),
                            esc(ex["experiment"]), esc(ex["summary"])))
        rows_html.append('<table class="looptab"><thead><tr>'
                         '<th>实验暴露的问题</th><th>失败类</th>'
                         '<th>修在框架哪里</th><th>回灌状态</th></tr></thead><tbody>')
        for p in ex["problems"]:
            n_prob += 1
            if p["status"] == "landed":
                n_landed += 1
            lab, cls = FIX_LABEL.get(p["status"], (p["status"], "missing"))
            rows_html.append(
                '<tr><td>%s</td><td class="cls">%s</td><td>%s</td>'
                '<td><span class="pill %s">%s</span>'
                '<div class="via">%s</div></td></tr>'
                % (md_bold(esc(p["problem"])), esc(p["cls"]), esc(p["fix_in"]),
                   cls, lab, md_bold(esc(p["via"]))))
        rows_html.append('</tbody></table></div>')
    stats = ('<div class="loopstats"><span><b>%d</b> 个实验</span>'
             '<span><b>%d</b> 个被暴露的问题</span>'
             '<span><b>%d</b> 已回灌框架</span>'
             '<span><b>%d</b> 修复中/待派工</span></div>'
             % (len(spec.ITERATION_LOOP), n_prob, n_landed, n_prob - n_landed))
    return stats + "".join(out) + "".join(rows_html), n_prob, n_landed


def arch_map():
    """The Theoria apparatus as a status-colored map, group by group."""
    out = ['<div class="arch">']
    for gi, group in enumerate(spec.ARCHITECTURE):
        if gi:
            out.append('<span class="flow" aria-hidden="true">→</span>')
        chips = "".join(
            '<span class="chip %s" title="%s"><i class="sw %s"></i>%s</span>'
            % (it["status"], esc(it["tip"]), it["status"], esc(it["label"]))
            for it in group["items"])
        out.append('<div class="agroup"><div class="ahead">%s'
                   '<span class="clause">%s</span></div>'
                   '<div class="achips">%s</div></div>'
                   % (esc(group["group"]), esc(group["clause"]), chips))
    out.append("</div>")
    return "".join(out)


# ---------------------------------------------------------------- prompts

def load_prompts():
    pdir = os.path.join(HERE, "prompts")
    tickets = []
    if not os.path.isdir(pdir):
        return tickets
    for name in sorted(os.listdir(pdir)):
        if not name.startswith(("P-", "T-")) or not name.endswith(".md"):
            continue
        text = open(os.path.join(pdir, name), encoding="utf-8").read()
        first = text.strip().splitlines()[0].lstrip("# ").strip()
        tickets.append({"file": name, "title": first, "text": text})
    return tickets


def ring(pct):
    """SVG progress ring with the big number inside."""
    r, c = 62, 2 * 3.14159 * 62
    filled = c * pct / 100.0
    return ('<svg viewBox="0 0 150 150" class="ring" role="img" '
            'aria-label="论文完成度 %.1f%%">'
            '<circle cx="75" cy="75" r="%d" class="rbg"/>'
            '<circle cx="75" cy="75" r="%d" class="rfg" '
            'stroke-dasharray="%.1f %.1f" transform="rotate(-90 75 75)"/>'
            '<text x="75" y="72" class="rnum">%.1f%%</text>'
            '<text x="75" y="94" class="rlab">论文完成度</text></svg>'
            % (pct, r, r, filled, c - filled, pct))


def sparkline(history):
    pts = [row.get("paper_progress") for row in history
           if row.get("paper_progress") is not None]
    if len(pts) < 2:
        pts = ([history[-1].get("paper_progress", 0)] * 2) if history else [0, 0]
    W, H = 220, 44
    ymax = max(max(pts) * 1.3, 10)
    n = len(pts)
    xy = [(W * i / (n - 1), H - 4 - (H - 10) * v / ymax) for i, v in enumerate(pts)]
    path = " ".join("%s%.1f %.1f" % ("M" if i == 0 else "L", x, y)
                    for i, (x, y) in enumerate(xy))
    return ('<svg viewBox="0 0 %d %d" class="spark"><path d="%s"/>'
            '<circle cx="%.1f" cy="%.1f" r="3.5"/></svg>'
            % (W, H, path, xy[-1][0], xy[-1][1]))


def stage_pct(wps):
    plan = {p["id"]: p for p in spec.PAPER_PLAN}
    tw = sum(plan[w]["weight"] for w in wps)
    return sum(plan[w]["weight"] * plan[w]["pct"] for w in wps) / tw if tw else 0


def render(state, refresh=None):
    m = state["metrics"]
    paper = state["paper_progress"]
    hist = state["history"]
    delta = ""
    prev = [r.get("paper_progress") for r in hist[:-1]
            if r.get("paper_progress") is not None]
    if prev:
        d = paper - prev[-1]
        if abs(d) >= 0.05:
            delta = '<span class="delta %s">%s%.1f%%</span>' % (
                "up" if d > 0 else "down", "+" if d > 0 else "", d)

    ls = read_json("monitor/loop_state.json", {}) or {}
    remote = set(git("branch", "-r", "--format=%(refname:short)").splitlines())
    registry = read_json("monitor/dispatch-logs/registry.json", {}) or {}
    cell_of = {}
    for cid, cd in spec.GRID.items():
        for a in cd.get("active", []):
            cell_of[a] = cid
    OPS = {"R-1": "运维", "B-1": "运维", "A-1": "运维", "M-0": "运维",
           "P-24": "运维"}

    def pid_alive_win(pidnum):
        out = subprocess.run(["tasklist", "/FI", "PID eq %d" % pidnum,
                              "/FO", "CSV"], capture_output=True,
                             text=True).stdout
        return str(pidnum) in out

    fleet = []
    for pid in ls.get("in_flight", []):
        slug = "agent/" + (pid.lower().replace("-", "")
                           if re.match(r"^[PRMBA]-\d+$", pid) else pid.lower())
        delivered = any(slug in b for b in remote)
        entry = registry.get(pid)
        runtime = ""
        alive = None
        if entry:
            alive = pid_alive_win(entry["pid"])
            try:
                import calendar
                t0 = calendar.timegm(time.strptime(entry["started"],
                                                   "%Y%m%dT%H%M%SZ"))
                runtime = "%d 分钟" % max(1, int((time.time() - t0) / 60))
            except Exception:
                runtime = ""
        if delivered:
            status, scls = "已交付 · 待合并", "done"
        elif entry and alive is False:
            status, scls = "失联（进程死亡且无产出）", "lost"
        else:
            status, scls = "进行中", "run"
        fleet.append({"id": pid, "task": PLAIN_TASK.get(pid, pid),
                      "cell": OPS.get(pid) or cell_of.get(pid, "—"),
                      "status": status, "scls": scls, "runtime": runtime})
    order = {"lost": 0, "run": 1, "done": 2}
    fleet.sort(key=lambda f: (order[f["scls"]], f["cell"]))
    n_running = sum(1 for f in fleet if f["scls"] == "run")
    n_lost = sum(1 for f in fleet if f["scls"] == "lost")

    needs = [f for f in state["findings"]
             if f["severity"] == "blocking" and "已裁决" not in f["title"]
             and "已解决" not in f["title"]]

    wins = []
    for ex in reversed(spec.ITERATION_LOOP):
        if ex["status"] == "green":
            wins.append(ex["summary"])
        if len(wins) >= 5:
            break

    parts = []
    A = parts.append
    A('<title>Theoria · 进度</title>')
    if refresh:
        A('<meta http-equiv="refresh" content="%d">' % refresh)
    A(STYLE)

    # ---------- header: the number, the trend, the fleet ----------
    A('<header><div class="top">')
    A(ring(paper))
    A('<div class="topmid"><h1>Theoria 研究进度</h1>'
      '<p class="one">目标：一篇实验规模对标 Schema 的可发表论文。'
      '眼下 <b>%d 个 AI 会话</b>在并行干活%s</p>'
      '<div class="sparkrow">%s<span class="sparklab">进度曲线</span></div></div>'
      % (n_running, delta, sparkline(hist)))
    A('<div class="topstats">')
    for v, k in [(("%d" % n_running), "会话在飞"),
                 (("%d/%d" % (state["loop_stats"][2], state["loop_stats"][1])),
                  "实验问题已回灌"),
                 (("%d" % len(needs)), "需要你处理"),
                 (esc(state["generated_at"][5:16]), "上次扫描")]:
        A('<div class="ts2"><b>%s</b><span>%s</span></div>' % (v, k))
    A('</div></div></header>')

    A('<main>')

    # ---------- the 2D project map: THE primary view ----------
    A('<section><h2>项目地图 <span class="note">— 横轴：工作从左往右推进；'
      '纵轴：六个子系统。格子越绿越完成，呼吸点 = 该格有会话在跑；'
      '悬停看格子的实况。新工单编号即坐标（如 A3-xxx）。</span></h2>')
    A('<div class="mapwrap"><table class="gridmap"><thead><tr><th></th>')
    for col in spec.GRID_COLS:
        A('<th>%s</th>' % esc(col))
    A('</tr></thead><tbody>')
    for rkey, rname in spec.GRID_ROWS:
        A('<tr><th class="rowh"><b>%s</b><span>%s</span></th>' % (rkey, esc(rname)))
        for ci in range(1, len(spec.GRID_COLS) + 1):
            cid = "%s%d" % (rkey, ci)
            cell_d = spec.GRID.get(cid, {"pct": 0, "note": "", "active": []})
            pct = cell_d["pct"]
            dots = "".join('<i class="mdot"></i>' for _ in cell_d["active"])
            A('<td class="mc" style="--f:%.2f" '
              'title="%s（%d%%）：%s%s">'
              '<span class="mpct">%d%%</span><span class="mdots">%s</span></td>'
              % (pct / 100.0, cid, pct, esc(cell_d["note"]),
                 ("　在跑：" + ",".join(cell_d["active"])) if cell_d["active"] else "",
                 pct, dots))
        A('</tr>')
    A('</tbody></table></div>')
    ops = [f2 for f2 in fleet if f2["cell"] == "运维" and f2["scls"] == "run"]
    if ops:
        A('<p class="note">地图外的运维会话：%s</p>'
          % "；".join("%s（%s）" % (esc(f2["task"]), esc(f2["id"]))
                      for f2 in ops))
    A('</section>')

    # ---------- fleet ----------
    A('<section><h2>正在进行 <span class="note">— %d 在跑%s，'
      '徽章 = 它点亮地图上的哪一格</span></h2><div class="fleet">'
      % (n_running,
         ("，<b style=\"color:var(--st-risk)\">%d 失联</b>" % n_lost)
         if n_lost else ""))
    for f2 in fleet:
        meta = " · ".join(x for x in (f2["id"], f2["runtime"]) if x)
        A('<div class="crew %s"><span class="cellbadge %s">%s</span>'
          '<div class="crewbody"><b>%s</b><em>%s</em></div>'
          '<span class="crewst"><i class="dot"></i>%s</span></div>'
          % (f2["scls"], "ops" if f2["cell"] == "运维" else "", esc(f2["cell"]),
             esc(f2["task"]), esc(meta), esc(f2["status"])))
    if not fleet:
        A('<p class="note">当前没有在飞会话。</p>')
    A('</div></section>')

    # ---------- needs you ----------
    A('<section><h2>需要你的事</h2>')
    if needs:
        for f in needs:
            A('<div class="needs"><b>%s</b><p>%s</p></div>'
              % (esc(f["title"]), md_bold(esc(f["action"]))))
    else:
        A('<p class="allclear">✓ 目前没有任何需要你出手的事——决策已代行，'
          '执行在跑，出问题会在这里出现。</p>')
    A('</section>')

    # ---------- recent wins ----------
    A('<section><h2>最近拿下</h2><ul class="wins">')
    for w in wins:
        A('<li>%s</li>' % esc(w))
    A('</ul></section>')

    # ---------- audit view, collapsed ----------
    A('<section><h2>审计明细 <span class="note">— 专业视图，逐条引 Theoria.md '
      '条款；日常不用看</span></h2>')

    def fold(title, body):
        A('<details class="fold"><summary>%s</summary>%s</details>' % (title, body))

    b = []
    B = b.append
    B(chart_legend()); B(chart_stacked(state["sections"]))
    fold("分区进度（四段 / 工序 / 约束 / Claim）", "".join(b))

    board, _, _ = loop_board()
    fold("实验 → 框架迭代回路（研究主环全记录）", board)
    fold("装置地图（Theoria.md 1.10 逐件对表）", arch_map())

    b = []; B = b.append
    B('<div class="trendbox">' + chart_trend(hist) + '</div>')
    fold("进度历史曲线", "".join(b))

    b = []; B = b.append
    B('<table class="wide"><thead><tr><th>工作包</th><th>论文槽位</th>'
      '<th>规模（Schema 对标）</th><th>完成度</th><th>证据</th></tr></thead><tbody>')
    for wp in spec.PAPER_PLAN:
        B('<tr><td><b>%s</b> %s</td><td class="nt">%s</td><td class="nt">%s</td>'
          '<td>%d%%</td><td class="nt">%s</td></tr>'
          % (esc(wp["id"]), esc(wp["name"]), esc(wp["slot"]), esc(wp["scale"]),
             wp["pct"], md_bold(esc(wp["evidence"]))))
    B('</tbody></table>')
    fold("论文工作量地图（正式口径）", "".join(b))

    b = []; B = b.append
    for f in state["findings"]:
        B('<article class="finding %s"><div class="fhead"><span class="fid">%s</span>'
          '<span class="sev %s">%s</span><h3>%s</h3></div><p>%s</p>'
          '<p class="action"><b>下一步</b> · %s</p></article>'
          % (f["severity"], esc(f["id"]), f["severity"],
             SEV.get(f["severity"], f["severity"]), esc(f["title"]),
             md_bold(esc(f["body"])), md_bold(esc(f["action"]))))
    fold("监视器发现（全部 %d 条）" % len(state["findings"]), "".join(b))

    b = []; B = b.append
    for ph in state["phases"]:
        B('<div class="phase"><div class="phead"><h3>%s</h3>'
          '<span class="gate">门槛：%s</span></div><table><tbody>' %
          (esc(ph["name"]), esc(ph["gate"])))
        for it in ph["items"]:
            B('<tr class="%s"><td class="st">%s</td><td class="lb"><b>%s</b>'
              '<span class="clause">%s</span></td><td class="nt">%s</td></tr>'
              % (it["_status"], cell(it["_status"]), esc(it["label"]),
                 esc(it["clause"]), md_bold(esc(it["_note"]))))
        B('</tbody></table></div>')
    fold("四段验收单逐条", "".join(b))

    b = []; B = b.append
    B('<table class="wide"><tbody>')
    for e in spec.ENGINES:
        B('<tr class="%s"><td><b>%s</b></td><td>%s</td><td>%s</td>'
          '<td class="nt">%s</td></tr>'
          % (e["status"], esc(e["step"]), esc(e["engine"]), cell(e["status"]),
             md_bold(esc(e["note"]))))
    B('</tbody></table>')
    fold("车间八工序", "".join(b))

    b = []; B = b.append
    B('<table class="wide"><tbody>')
    for c in spec.CONSTRAINTS:
        B('<tr class="%s"><td class="num">%d</td><td>%s</td><td>%s</td>'
          '<td class="nt">%s</td></tr>'
          % (c["status"], c["n"], esc(c["text"]), cell(c["status"]),
             md_bold(esc(c["note"]))))
    B('</tbody></table>')
    fold("十条强制约束", "".join(b))

    cf = state["probes"]["conflict_scan"]
    pv = state["probes"]["provenance_scan"]
    ib = state["probes"]["inbox"]
    b = []
    b.append('<div class="conflict %s"><b>冲突扫描</b> %s</div>'
             % (cf["status"], md_bold(esc(cf["detail"]))))
    b.append('<div class="conflict %s"><b>留痕审计</b> %s</div>'
             % (pv["status"], md_bold(esc(pv["detail"]))))
    b.append('<div class="conflict %s"><b>提案箱</b> %s</div>'
             % (ib["status"], md_bold(esc(ib["detail"]))))
    fold("冲突 / 留痕 / 提案箱（每轮实测）", "".join(b))


    A('</section>')
    A('<footer><p>由 <code>monitor/scan.py</code> 生成；判断依据与出处在 '
      '<code>monitor/spec.py</code>。人话层只是翻译，数据与审计口径不变。'
      '重跑即刷新；<code>--watch 120</code> 自动刷新。</p></footer>')
    A('</main>')
    return "\n".join(parts)


STYLE = """<style>
:root{
  --bg:#fbfaf8; --fg:#1c1a17; --mut:#6b655c; --line:#e2ddd4; --card:#fff;
  --green:#1a7f4e; --partial:#a86a12; --risk:#b3341f; --blocked:#6d5ca8; --missing:#8a8378;
  --greenbg:#e8f4ed; --partialbg:#fbf1de; --riskbg:#fbe9e5; --blockedbg:#efecf8; --missingbg:#f1efec;
}
@media (prefers-color-scheme:dark){:root{
  --bg:#14130f; --fg:#eae5dc; --mut:#9a9287; --line:#2e2b25; --card:#1c1a16;
  --green:#5cc98d; --partial:#e0a94a; --risk:#f0796a; --blocked:#a99ae0; --missing:#8a8378;
  --greenbg:#16281f; --partialbg:#2b2214; --riskbg:#2e1a16; --blockedbg:#211d2e; --missingbg:#1f1d19;
}}
:root[data-theme="dark"]{
  --bg:#14130f; --fg:#eae5dc; --mut:#9a9287; --line:#2e2b25; --card:#1c1a16;
  --green:#5cc98d; --partial:#e0a94a; --risk:#f0796a; --blocked:#a99ae0; --missing:#8a8378;
  --greenbg:#16281f; --partialbg:#2b2214; --riskbg:#2e1a16; --blockedbg:#211d2e; --missingbg:#1f1d19;
}
:root[data-theme="light"]{
  --bg:#fbfaf8; --fg:#1c1a17; --mut:#6b655c; --line:#e2ddd4; --card:#fff;
  --green:#1a7f4e; --partial:#a86a12; --risk:#b3341f; --blocked:#6d5ca8; --missing:#8a8378;
  --greenbg:#e8f4ed; --partialbg:#fbf1de; --riskbg:#fbe9e5; --blockedbg:#efecf8; --missingbg:#f1efec;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
  font:15px/1.65 "Noto Serif SC",Georgia,"Songti SC",serif;-webkit-font-smoothing:antialiased}
header{padding:44px 28px 0;max-width:1180px;margin:0 auto}
h1{font-size:30px;margin:0 0 6px;letter-spacing:-.01em}
.sub{color:var(--mut);margin:0 0 26px;font-size:14px}
.stamp{display:block;margin-top:6px;font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12px}
main{max-width:1180px;margin:0 auto;padding:0 28px 80px}
section{margin:46px 0}
h2{font-size:19px;margin:0 0 16px;padding-bottom:9px;border-bottom:1px solid var(--line)}
h3{font-size:16px;margin:0}
.note{color:var(--mut);font-weight:400;font-size:13px}
code{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12.5px;
  background:var(--missingbg);padding:1px 5px;border-radius:3px}

.hero{display:flex;gap:26px;align-items:center;background:var(--card);
  border:1px solid var(--line);border-radius:12px;padding:22px 26px;margin-bottom:14px}
.hnum{font:700 54px/1 system-ui,sans-serif;letter-spacing:-.02em;white-space:nowrap}
.hnum small{font-size:26px;font-weight:600;color:var(--mut)}
.hbody{flex:1;min-width:0}
.htitle{font-size:14.5px;font-weight:700;margin-bottom:8px}
.htitle .note{display:block;font-weight:400;margin-top:2px}
.hbar{display:flex;height:14px;border-radius:99px;overflow:hidden;gap:0;
  border:1px solid var(--line)}
.hseg{display:block;height:100%}
.hseg.fill{background:var(--st-green)}
.hseg.rest{background:var(--missingbg);border-left:1px solid var(--line)}
.hrows{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));
  gap:4px 22px;margin-top:10px}
.hrow{display:flex;align-items:center;gap:8px;font-size:12px;color:var(--mut)}
.hn{flex:0 0 auto}
.hb{flex:1;height:5px;border-radius:99px;background:var(--missingbg);overflow:hidden}
.hb i{display:block;height:100%;background:var(--st-green)}
.hv{font-family:ui-monospace,Menlo,Consolas,monospace;white-space:nowrap}
.hv em{font-style:normal;opacity:.65}
@media(max-width:720px){.hero{flex-direction:column;align-items:flex-start;gap:12px}}

.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(168px,1fr));gap:12px;
  margin-bottom:8px}
.tile{background:var(--card);border:1px solid var(--line);border-radius:9px;padding:14px 16px}
.tv{font-size:20px;font-weight:700;letter-spacing:-.01em}
.tl{font-size:13px;margin-top:2px}
.ts{font-size:12px;color:var(--mut);margin-top:3px}

.pill{display:inline-block;padding:2px 9px;border-radius:99px;font-size:12px;
  font-weight:600;white-space:nowrap;font-family:system-ui,sans-serif}
.pill.green{background:var(--greenbg);color:var(--green)}
.pill.partial{background:var(--partialbg);color:var(--partial)}
.pill.risk{background:var(--riskbg);color:var(--risk)}
.pill.blocked{background:var(--blockedbg);color:var(--blocked)}
.pill.missing{background:var(--missingbg);color:var(--missing)}

.finding{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--missing);
  border-radius:8px;padding:16px 20px;margin-bottom:14px}
.finding.blocking{border-left-color:var(--risk)}
.finding.high{border-left-color:var(--partial)}
.finding.medium{border-left-color:var(--blocked)}
.finding.low,.finding.info{border-left-color:var(--green)}
.fhead{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;margin-bottom:8px}
.fid{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12px;color:var(--mut)}
.sev{font-size:11.5px;font-weight:700;padding:1px 8px;border-radius:99px;
  font-family:system-ui,sans-serif}
.sev.blocking{background:var(--riskbg);color:var(--risk)}
.sev.high{background:var(--partialbg);color:var(--partial)}
.sev.medium{background:var(--blockedbg);color:var(--blocked)}
.sev.low,.sev.info{background:var(--greenbg);color:var(--green)}
.finding p{margin:0 0 8px;font-size:14px}
.action{color:var(--mut);font-size:13.5px;border-top:1px dashed var(--line);padding-top:8px}

.phase{background:var(--card);border:1px solid var(--line);border-radius:8px;
  margin-bottom:16px;overflow:hidden}
.phead{display:flex;align-items:center;gap:14px;flex-wrap:wrap;padding:13px 18px;
  border-bottom:1px solid var(--line)}
.gate{font-size:12.5px;color:var(--mut)}
.bar{display:flex;flex:1;min-width:120px;height:6px;border-radius:99px;overflow:hidden;
  background:var(--missingbg)}
.bar i{display:block}
.bar i.green{background:var(--green)}.bar i.partial{background:var(--partial)}
.bar i.risk{background:var(--risk)}.bar i.blocked{background:var(--blocked)}
.bar i.missing{background:var(--missing)}

table{width:100%;border-collapse:collapse;font-size:13.5px}
.wide{background:var(--card);border:1px solid var(--line);border-radius:8px;overflow:hidden}
th{text-align:left;font-size:12px;color:var(--mut);font-weight:600;padding:10px 14px;
  border-bottom:1px solid var(--line);font-family:system-ui,sans-serif}
td{padding:11px 14px;border-bottom:1px solid var(--line);vertical-align:top}
tr:last-child td{border-bottom:none}
td.st{width:74px}
td.num{width:38px;color:var(--mut);font-family:ui-monospace,monospace}
.lb{width:30%}
.nt{color:var(--mut);font-size:13px}
.clause{display:block;font-size:11.5px;color:var(--mut);font-weight:400;margin-top:2px;
  font-family:ui-monospace,Menlo,Consolas,monospace}

.facts{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:9px}
.fact{background:var(--card);border:1px solid var(--line);border-radius:7px;padding:10px 13px}
.fk{display:block;font-size:11.5px;color:var(--mut);font-family:system-ui,sans-serif}
.fv{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12.5px;word-break:break-word}

/* ---- charts: status palette (state colors, both modes validated steps) */
:root{--st-green:#0ca30c;--st-partial:#fab219;--st-blocked:#ec835a;
  --st-risk:#d03b3b;--st-missing:#c3c2b7;--chart-grid:#e1e0d9;--chart-axis:#c3c2b7}
@media (prefers-color-scheme:dark){:root{--st-missing:#4a4a46;
  --chart-grid:#2c2c2a;--chart-axis:#383835}}
:root[data-theme="dark"]{--st-missing:#4a4a46;--chart-grid:#2c2c2a;--chart-axis:#383835}

.legend{display:flex;gap:16px;flex-wrap:wrap;margin-bottom:12px;
  font-size:12.5px;color:var(--mut);font-family:system-ui,sans-serif}
.lg{display:inline-flex;align-items:center;gap:6px}
.sw{display:inline-block;width:11px;height:11px;border-radius:3px}
.sw.green{background:var(--st-green)}.sw.partial{background:var(--st-partial)}
.sw.blocked{background:var(--st-blocked)}.sw.risk{background:var(--st-risk)}
.sw.missing{background:var(--st-missing)}

.stack{display:flex;flex-direction:column;gap:9px;background:var(--card);
  border:1px solid var(--line);border-radius:9px;padding:16px 18px}
.srow{display:flex;align-items:center;gap:12px}
.sname{flex:0 0 168px;font-size:13px;text-align:right;color:var(--fg)}
.sbar{flex:1;display:flex;gap:2px;height:22px;border-radius:5px;overflow:hidden}
.seg{display:flex;align-items:center;justify-content:center;height:100%;
  font:600 11px/1 system-ui,sans-serif;color:#fff;min-width:3px}
.seg.green{background:var(--st-green)}.seg.partial{background:var(--st-partial);color:#4a3500}
.seg.blocked{background:var(--st-blocked);color:#3d1b0c}
.seg.risk{background:var(--st-risk)}.seg.missing{background:var(--st-missing);color:#3d3c38}
.stot{flex:0 0 84px;font-size:12px;color:var(--mut);
  font-family:ui-monospace,Menlo,Consolas,monospace}

.arch{display:flex;flex-wrap:wrap;gap:10px;align-items:stretch}
.agroup{background:var(--card);border:1px solid var(--line);border-radius:9px;
  padding:12px 14px;flex:1 1 200px;min-width:190px}
.ahead{font-size:13.5px;font-weight:700;margin-bottom:9px}
.achips{display:flex;flex-wrap:wrap;gap:6px}
.chip{display:inline-flex;align-items:center;gap:6px;padding:4px 10px;
  border-radius:7px;font:500 12.5px/1.3 system-ui,sans-serif;cursor:default;
  border:1px solid var(--line)}
.chip.green{background:var(--greenbg)}.chip.partial{background:var(--partialbg)}
.chip.risk{background:var(--riskbg)}.chip.blocked{background:var(--blockedbg)}
.chip.missing{background:var(--missingbg);color:var(--mut)}
.flow{align-self:center;color:var(--mut);font-size:17px;padding:0 1px}

.trendbox{background:var(--card);border:1px solid var(--line);border-radius:9px;
  padding:16px 12px 6px;overflow-x:auto}
.grid{stroke:var(--chart-grid);stroke-width:1}
.tick{fill:var(--mut);font:11px system-ui,sans-serif}
.line{fill:none;stroke-width:2}
.line.t1{stroke:#2a78d6}.line.t2{stroke:#eb6834}
@media (prefers-color-scheme:dark){.line.t1{stroke:#3987e5}.line.t2{stroke:#d95926}}
:root[data-theme="dark"] .line.t1{stroke:#3987e5}
:root[data-theme="dark"] .line.t2{stroke:#d95926}
.dot{stroke:var(--card);stroke-width:2}
.dot.t1{fill:#2a78d6}.dot.t2{fill:#eb6834}
@media (prefers-color-scheme:dark){.dot.t1{fill:#3987e5}.dot.t2{fill:#d95926}}
:root[data-theme="dark"] .dot.t1{fill:#3987e5}
:root[data-theme="dark"] .dot.t2{fill:#d95926}
.dl{font:600 11.5px system-ui,sans-serif;fill:var(--fg)}

.conflict{background:var(--card);border:1px solid var(--line);border-radius:8px;
  padding:13px 16px;font-size:13.5px}
.conflict.risk{border-left:4px solid var(--st-risk)}
.conflict.green{border-left:4px solid var(--st-green);color:var(--mut)}

.mainloop h2{border-bottom-width:2px;border-bottom-color:var(--fg)}
.doctrine{background:var(--card);border-left:4px solid var(--fg);border-radius:6px;
  padding:12px 16px;font-size:14px;margin:0 0 14px}
.loopstats{display:flex;gap:26px;flex-wrap:wrap;margin-bottom:12px;
  font:13px system-ui,sans-serif;color:var(--mut)}
.loopstats b{font-size:19px;color:var(--fg);margin-right:4px}
.exp{background:var(--card);border:1px solid var(--line);border-radius:9px;
  margin-bottom:14px;overflow:hidden}
.exhead{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;
  padding:12px 16px;border-bottom:1px solid var(--line)}
.exhead b{font-size:14.5px}
.exsum{font-size:12.5px;color:var(--mut)}
.looptab th:first-child{width:34%}
.looptab td.cls{white-space:nowrap;color:var(--mut);font-size:12.5px}
.via{margin-top:5px;font-size:12px;color:var(--mut);max-width:340px}

.ticket{background:var(--card);border:1px solid var(--line);border-radius:8px;
  margin-bottom:10px;overflow:hidden}
.ticket summary{display:flex;align-items:center;gap:10px;padding:12px 16px;
  cursor:pointer;font-size:14px;font-weight:600;list-style:none}
.ticket summary::-webkit-details-marker{display:none}
.tfile{font:11.5px ui-monospace,Menlo,Consolas,monospace;color:var(--mut);
  background:var(--missingbg);padding:2px 7px;border-radius:4px;font-weight:400}
.copy{margin-left:auto;border:1px solid var(--line);background:var(--bg);
  color:var(--fg);border-radius:6px;padding:5px 12px;font:12.5px system-ui,sans-serif;
  cursor:pointer}
.copy:hover{border-color:var(--mut)}
.ticket textarea{display:block;width:100%;border:none;border-top:1px solid var(--line);
  background:var(--bg);color:var(--fg);padding:14px 16px;resize:vertical;
  font:12.5px/1.6 ui-monospace,Menlo,Consolas,monospace;box-sizing:border-box}

/* ---- 2D project map ---- */
.mapwrap{overflow-x:auto;background:var(--card);border:1px solid var(--line);
  border-radius:12px;padding:14px}
.gridmap{border-collapse:separate;border-spacing:5px;width:100%;min-width:640px}
.gridmap thead th{font:600 12px system-ui,sans-serif;color:var(--mut);
  padding:4px 6px;text-align:center;border:none}
.rowh{text-align:right;padding:0 10px 0 2px;border:none;white-space:nowrap}
.rowh b{font:700 13px system-ui,sans-serif;display:block}
.rowh span{font-size:11px;color:var(--mut)}
.mc{position:relative;height:56px;min-width:96px;border-radius:9px;
  text-align:center;vertical-align:middle;cursor:default;
  background:color-mix(in oklab, var(--st-green) calc(var(--f)*100%), var(--missingbg));
  border:1px solid var(--line)}
.mpct{font:700 15px system-ui,sans-serif;
  color:color-mix(in oklab, #fff calc(var(--f)*90%), var(--fg))}
.mdots{position:absolute;right:7px;bottom:6px;display:flex;gap:3px}
.mdot{width:8px;height:8px;border-radius:99px;background:var(--st-partial);
  animation:pulse 1.6s infinite;display:block;border:1.5px solid var(--card)}

/* ---- plain progress-first layout ---- */
.top{display:flex;gap:30px;align-items:center;flex-wrap:wrap;
  background:var(--card);border:1px solid var(--line);border-radius:14px;
  padding:26px 30px}
.ring{width:150px;height:150px;flex:0 0 auto}
.rbg{fill:none;stroke:var(--missingbg);stroke-width:11}
.rfg{fill:none;stroke:var(--st-green);stroke-width:11;stroke-linecap:round}
.rnum{font:700 27px system-ui,sans-serif;fill:var(--fg);text-anchor:middle}
.rlab{font:12px system-ui,sans-serif;fill:var(--mut);text-anchor:middle}
.topmid{flex:1;min-width:240px}
.topmid h1{font-size:24px;margin:0 0 6px}
.one{margin:0 0 10px;font-size:14.5px;color:var(--mut)}
.one b{color:var(--fg)}
.delta{margin-left:8px;font:700 13px system-ui,sans-serif;padding:1px 8px;
  border-radius:99px}
.delta.up{background:var(--greenbg);color:var(--green)}
.delta.down{background:var(--riskbg);color:var(--risk)}
.sparkrow{display:flex;align-items:center;gap:10px}
.spark{width:220px;height:44px}
.spark path{fill:none;stroke:var(--st-green);stroke-width:2.5}
.spark circle{fill:var(--st-green)}
.sparklab{font-size:11.5px;color:var(--mut)}
.topstats{display:grid;grid-template-columns:1fr 1fr;gap:10px 26px}
.ts2 b{display:block;font-size:21px;font-family:system-ui,sans-serif}
.ts2 span{font-size:12px;color:var(--mut)}

.journey{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px}
.leg{background:var(--card);border:1px solid var(--line);border-radius:11px;
  padding:16px 18px;border-top:4px solid var(--missing)}
.leg.done{border-top-color:var(--st-green)}
.leg.now{border-top-color:var(--st-partial)}
.leg.soon{border-top-color:var(--st-blocked)}
.legpct{font:700 30px system-ui,sans-serif;letter-spacing:-.02em}
.legbar{height:7px;border-radius:99px;background:var(--missingbg);overflow:hidden;
  margin:8px 0 10px}
.legbar i{display:block;height:100%;background:var(--st-green)}
.leg.now .legbar i{background:var(--st-partial)}
.legname{font-weight:700;font-size:14.5px}
.legsub{font-size:12px;color:var(--mut);margin-top:2px}

.wpgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:12px}
.wpcard{background:var(--card);border:1px solid var(--line);border-radius:11px;
  padding:15px 17px}
.wphead{display:flex;justify-content:space-between;align-items:baseline;font-size:14.5px}
.wppct{font:700 19px system-ui,sans-serif}
.wpbar{height:7px;border-radius:99px;background:var(--missingbg);overflow:hidden;
  margin:8px 0}
.wpbar i{display:block;height:100%;background:var(--st-green)}
.wpsub{margin:0 0 7px;font-size:12.5px;color:var(--mut)}
.wpnext{margin:0;font-size:12px;color:var(--mut);border-top:1px dashed var(--line);
  padding-top:7px}

.fleet{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:9px}
.crew{display:flex;align-items:center;gap:11px;background:var(--card);
  border:1px solid var(--line);border-radius:9px;padding:10px 13px;font-size:13.5px}
.crew.lost{border-color:var(--st-risk);border-left-width:4px}
.cellbadge{flex:0 0 auto;min-width:34px;text-align:center;padding:5px 7px;
  border-radius:7px;font:700 12.5px system-ui,sans-serif;
  background:var(--greenbg);color:var(--green)}
.cellbadge.ops{background:var(--blockedbg);color:var(--blocked)}
.crewbody{flex:1;min-width:0}
.crewbody b{font-weight:600;display:block;line-height:1.35}
.crewbody em{font-style:normal;font-size:11px;color:var(--mut);
  font-family:ui-monospace,Menlo,Consolas,monospace}
.crewst{flex:0 0 auto;display:inline-flex;align-items:center;gap:6px;
  font-size:11.5px;color:var(--mut)}
.dot{width:9px;height:9px;border-radius:99px;flex:0 0 auto}
.crew.run .dot{background:var(--st-partial);animation:pulse 1.6s infinite}
.crew.done .dot{background:var(--st-green)}
.crew.lost .dot{background:var(--st-risk)}
@keyframes pulse{50%{opacity:.35}}

.needs{background:var(--card);border:1px solid var(--line);
  border-left:4px solid var(--st-risk);border-radius:9px;padding:14px 18px;
  margin-bottom:10px}
.needs p{margin:6px 0 0;font-size:13.5px;color:var(--mut)}
.allclear{background:var(--greenbg);color:var(--green);border-radius:9px;
  padding:13px 18px;font-size:14px}
.wins{margin:0;padding-left:22px}
.wins li{margin-bottom:7px;font-size:14px}

.fold{background:var(--card);border:1px solid var(--line);border-radius:9px;
  margin-bottom:9px;overflow:hidden}
.fold>summary{padding:12px 16px;cursor:pointer;font-weight:600;font-size:13.5px;
  list-style:none}
.fold>summary::-webkit-details-marker{display:none}
.fold>summary::before{content:"▸ ";color:var(--mut)}
.fold[open]>summary::before{content:"▾ "}
.fold>*:not(summary){margin:0 16px 14px}

footer{margin-top:50px;padding-top:18px;border-top:1px solid var(--line);
  color:var(--mut);font-size:12.5px}
@media(max-width:720px){
  header{padding:26px 16px 0}main{padding:0 16px 50px}
  .lb{width:auto}table{font-size:13px}td{padding:9px 10px}
}
</style>"""


# ---------------------------------------------------------------- main

def build(with_tests=False, out_dir=None):
    metrics = collect_metrics(with_tests)

    probe_results = {name: fn() for name, fn in PROBES.items()}

    phases = []
    p1_green = p1_total = 0
    for ph in spec.PHASES:
        items = []
        for it in ph["items"]:
            st, note = it["status"], it["note"]
            if it.get("probe") and it["probe"] in probe_results:
                pr = probe_results[it["probe"]]
                st = pr["status"] if it["status"] not in ("risk",) else it["status"]
                note = note + "  〔本次扫描：" + pr["detail"] + "〕"
            items.append(dict(it, _status=st, _note=note))
        counts = {}
        for i in items:
            counts[i["_status"]] = counts.get(i["_status"], 0) + 1
        if ph["id"] == "p1":
            p1_total = len(items)
            p1_green = counts.get("green", 0)
        phases.append(dict(ph, items=items, _counts=counts))

    def counts_of(items, key="status"):
        c = {}
        for it in items:
            c[it[key]] = c.get(it[key], 0) + 1
        return c

    sections = [{"name": ph["name"], "counts": ph["_counts"]} for ph in phases]
    sections += [
        {"name": "车间八工序", "counts": counts_of(spec.ENGINES)},
        {"name": "十条强制约束", "counts": counts_of(spec.CONSTRAINTS)},
        {"name": "Claim 菜单", "counts": counts_of(spec.CLAIMS)},
    ]

    state = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "metrics": metrics,
        "phases": phases,
        "sections": sections,
        "findings": sorted(spec.FINDINGS,
                           key=lambda f: ["blocking", "high", "medium", "low",
                                          "info"].index(f["severity"])),
        "p1_green": p1_green, "p1_total": p1_total,
        "eng_green": sum(1 for e in spec.ENGINES if e["status"] == "green"),
        "con_green": sum(1 for c in spec.CONSTRAINTS if c["status"] == "green"),
        "blocking_findings": sum(1 for f in spec.FINDINGS if f["severity"] == "blocking"),
        "probes": probe_results,
        "tickets": load_prompts(),
    }
    state["progress"] = compute_progress(phases)
    state["paper_progress"] = compute_paper_progress()
    n_prob = sum(len(ex["problems"]) for ex in spec.ITERATION_LOOP)
    n_landed = sum(1 for ex in spec.ITERATION_LOOP
                   for p in ex["problems"] if p["status"] == "landed")
    state["loop_stats"] = (len(spec.ITERATION_LOOP), n_prob, n_landed)
    append_history(state, out_dir)
    state["history"] = load_history()

    with open(os.path.join(out_dir or HERE, "index.html"), "w",
              encoding="utf-8", newline="\n") as fh:
        fh.write(render(state, refresh=build.refresh))
    # --- data for the live frontend (app.html renders this; no HTML here) ---
    import subprocess as _sp
    bl = _sp.run([sys.executable, os.path.join(HERE, "board.py"), "list"],
                 cwd=ROOT, capture_output=True, text=True,
                 encoding="utf-8", errors="replace").stdout
    dd = os.path.join(HERE, "board", "done")
    cd = os.path.join(HERE, "board", "claimed")
    state["board"] = {
        "available": len([l for l in bl.splitlines() if l.startswith("  p")]),
        "claimed": len(os.listdir(cd)) if os.path.isdir(cd) else 0,
        "done": len(os.listdir(dd)) if os.path.isdir(dd) else 0,
        "blocked": bl.count("waits on"),
        "listing": bl.strip(),
    }
    try:
        import agents as agents_mod
        state["agents"] = agents_mod.collect()
    except Exception as exc:
        state["agents"] = {"error": str(exc)}
    state["grid"] = spec.GRID
    state["grid_cols"] = spec.GRID_COLS
    state["paper_plan"] = spec.PAPER_PLAN
    state["iteration_loop"] = spec.ITERATION_LOOP
    state["engines"] = spec.ENGINES
    state["constraints"] = spec.CONSTRAINTS
    slim = {k: v for k, v in state.items() if k != "tickets"}
    # `out_dir` exists so a completion gate can run a real scan without dirtying
    # the workspace it is gating. A gate that writes into the tree can turn
    # itself red, and can turn the *next* territory's gate red for a reason that
    # has nothing to do with the branch being merged (S13).
    with open(os.path.join(out_dir or HERE, "state.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        json.dump(slim, fh, ensure_ascii=False, indent=2, sort_keys=True)
    return state


build.refresh = None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tests", action="store_true", help="also run both pytest suites")
    ap.add_argument("--watch", type=int, metavar="SECONDS", default=0,
                    help="rescan on this interval; the page auto-reloads itself")
    args = ap.parse_args()
    if args.watch:
        build.refresh = max(args.watch, 15)
    while True:
        state = build(args.tests)
        print("[%s] monitor/index.html written — Phase 1: %d/%d green"
              % (state["generated_at"], state["p1_green"], state["p1_total"]))
        if not args.watch:
            break
        time.sleep(max(args.watch, 15))
    for name, pr in sorted(state["probes"].items()):
        print("  %-22s %-8s %s" % (name, pr["status"], pr["detail"][:110]))
    for f in state["findings"]:
        if f["severity"] in ("blocking", "high"):
            print("  [%s] %s — %s" % (f["severity"].upper(), f["id"], f["title"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
