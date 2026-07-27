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
        out = subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True,
                             text=True, timeout=30)
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
        return {"status": "risk", "detail": "密钥泄漏进：" + ", ".join(leaks)}
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
    pre = read_json("arc-recon/data/precheck.json", {})
    verdict = pre.get("verdict") or pre.get("status") or "unknown"
    # the counter-evidence: did any ACTION ever return 200?
    ok_actions = 0
    total_actions = 0
    for row in iter_jsonl("baseline-arms/probe_log.jsonl"):
        url = row.get("url") or ""
        if "/cmd/ACTION" in url:
            total_actions += 1
            if row.get("status") == 200:
                ok_actions += 1
    detail = "arc-recon 预检裁定：%s。" % verdict
    if total_actions:
        detail += (" 但 baseline-arms 的重试实验里 ACTION %d/%d 次返回 200 —— "
                   "INC-002『0 次成功』已不成立，预检需在重试策略下重跑。"
                   % (ok_actions, total_actions))
    return {"status": "risk" if ok_actions else "blocked", "detail": detail}


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


TERRITORIES = ["engine-rig", "theory-compiler", "cold-start-a0", "cold-start-a2",
               "a0-spike", "baseline-arms", "arc-recon", "proxy", "battery",
               "monitor"]
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
            with_manifest = sum(
                1 for d in runs
                if os.path.exists(os.path.join(runs_dir, d, "MANIFEST.json")))
            rows.append("%s：%d 个 run，MANIFEST %d/%d，最新 %s"
                        % (terr, len(runs), with_manifest, len(runs),
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


PROBES = {
    "credential_hygiene": probe_credential_hygiene,
    "conflict_scan": probe_conflicts,
    "provenance_scan": probe_provenance,
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


def append_history(state):
    """One JSONL row per scan — the raw material of the trend chart."""
    row = {
        "ts": state["generated_at"],
        "progress": state["progress"]["total"],
        "sections": {s["name"]: s["counts"] for s in state["sections"]},
        "findings": {},
    }
    for f in state["findings"]:
        row["findings"][f["severity"]] = row["findings"].get(f["severity"], 0) + 1
    hist_path = os.path.join(HERE, "history.jsonl")
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
    """Whole-programme progress (%) across scans."""
    pts = [(row.get("ts", ""), row["progress"])
           for row in history if "progress" in row]
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
            '<div class="hbody"><div class="htitle">研究总进度'
            '<span class="note">　100%% = Theoria.md 全程：四段验收、封存战役、裁决与释出全部完成。'
            '权重与折算规则记在 monitor/spec.py，改定义必须改那里。</span></div>'
            '<div class="hbar">%s</div><div class="hrows">%s</div></div></div>'
            % (progress["total"], "".join(segs), rows))


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


def render(state, refresh=None):
    m = state["metrics"]
    parts = []
    A = parts.append

    A('<title>Theoria · 研究进展监视器</title>')
    if refresh:
        A('<meta http-equiv="refresh" content="%d">' % refresh)
    A(STYLE)
    A('<header>')
    A('<div class="masthead"><h1>Theoria 研究进展监视器</h1>'
      '<p class="sub">以 <code>Theoria.md</code> 为唯一基准，对工作树逐条对表。'
      '<span class="stamp">扫描于 %s · %s · %s</span></p></div>' %
      (esc(state["generated_at"]), esc(m["git_branch"]), esc(m["git_head"][:40])))

    # ---- headline: whole-programme progress
    A(hero_progress(state["progress"]))

    # ---- topline
    lb, lp, ll = state["loop_stats"]
    A('<div class="tiles">')
    for label, value, sub in [
        ("实验→框架回灌", "%d/%d 已回灌" % (ll, lp),
         "问题来自 %d 个实验" % lb),
        ("Phase 1 验收单", "%d/%d 达成" % (state["p1_green"], state["p1_total"]),
         "全绿才准烧游戏钱"),
        ("八道工序", "%d/%d 引擎就位" % (state["eng_green"], len(spec.ENGINES)),
         "缺 IC3/PDR 与死锁刻画"),
        ("十条约束", "%d 条已落实" % state["con_green"], "其余 %d 条部分或缺失"
         % (10 - state["con_green"])),
        ("封存堆", "%d 局零接触" % m["sealed_count"], "piles %s…" % m["piles_sha"]),
        ("阻塞级发现", "%d 条" % state["blocking_findings"], "需用户裁决"),
    ]:
        A('<div class="tile"><div class="tv">%s</div><div class="tl">%s</div>'
          '<div class="ts">%s</div></div>' % (esc(value), esc(label), esc(sub)))
    A('</div>')
    A('</header>')

    A('<main>')

    # ---- the main loop: experiment-driven framework iteration
    board, n_prob, n_landed = loop_board()
    A('<section class="mainloop"><h2>实验 → 框架迭代回路 '
      '<span class="note">— 研究的主环（Theoria.md Phase 3『一次迭代的形状』）；'
      '组件建设只是它的脚手架</span></h2>')
    A(board)
    A('</section>')

    # ---- charts: the state of every part, drawn
    A('<section><h2>进度总览 <span class="note">— 每区一条堆叠条，悬停看明细</span></h2>')
    A(chart_legend())
    A(chart_stacked(state["sections"]))
    A('</section>')

    A('<section><h2>装置地图 <span class="note">— Theoria.md 1.10 的车间与装置，'
      '逐件着色；悬停看实况与对应工单</span></h2>')
    A(arch_map())
    A('</section>')

    A('<section><h2>总进度趋势 <span class="note">— 跨扫描累积，'
      '来自 monitor/history.jsonl；分母是全程</span></h2>')
    A('<div class="trendbox">' + chart_trend(state["history"]) + '</div>')
    A('</section>')

    # ---- multi-agent conflict scan (live, every run)
    cf = state["probes"]["conflict_scan"]
    A('<section><h2>多 agent 冲突扫描 <span class="note">— 每次运行重查：'
      '冲突标记 / 未合并路径 / 跨领地提交</span></h2>')
    A('<div class="conflict %s"><span class="pill %s">%s</span> %s</div>'
      % (cf["status"], cf["status"],
         "无冲突" if cf["status"] == "green" else "发现冲突",
         md_bold(esc(cf["detail"]))))
    A('</section>')

    # ---- provenance audit (live, every run)
    pv = state["probes"]["provenance_scan"]
    A('<section><h2>留痕审计 <span class="note">— 实验中间文件必须进各领地的 '
      'append-only runs/ 档案（含 MANIFEST：命令、seed、代码 commit、逐文件哈希）；'
      '重跑 = 新 run，永不覆盖</span></h2>')
    A('<div class="conflict %s"><span class="pill %s">%s</span> %s</div>'
      % (pv["status"], pv["status"],
         "全部建档" if pv["status"] == "green" else "有欠账",
         md_bold(esc(pv["detail"]))))
    A('</section>')

    # ---- findings first: this is the point of the monitor
    A('<section><h2>监视器发现 <span class="note">— 不在任何 incidents.jsonl 里，'
      '由本次对表产生</span></h2>')
    for f in state["findings"]:
        A('<article class="finding %s">' % f["severity"])
        A('<div class="fhead"><span class="fid">%s</span>'
          '<span class="sev %s">%s</span><h3>%s</h3></div>'
          % (esc(f["id"]), f["severity"], SEV.get(f["severity"], f["severity"]),
             esc(f["title"])))
        A('<p>%s</p>' % md_bold(esc(f["body"])))
        A('<p class="action"><b>下一步</b> · %s</p>' % md_bold(esc(f["action"])))
        A('</article>')
    A('</section>')

    # ---- phases
    A('<section><h2>四段进度 <span class="note">— 每行标注它出自 Theoria.md 的哪一句</span></h2>')
    for ph in state["phases"]:
        c = ph["_counts"]
        A('<div class="phase">')
        A('<div class="phead"><h3>%s</h3><span class="gate">门槛：%s</span>'
          '<span class="bar">%s</span></div>'
          % (esc(ph["name"]), esc(ph["gate"]),
             "".join('<i class="%s" style="flex:%d"></i>' % (k, v)
                     for k, v in c.items() if v)))
        A('<table><tbody>')
        for it in ph["items"]:
            A('<tr class="%s"><td class="st">%s</td><td class="lb"><b>%s</b>'
              '<span class="clause">%s</span></td><td class="nt">%s</td></tr>'
              % (it["_status"], cell(it["_status"]), esc(it["label"]),
                 esc(it["clause"]), md_bold(esc(it["_note"]))))
        A('</tbody></table></div>')
    A('</section>')

    # ---- engines
    A('<section><h2>车间引擎清单 <span class="note">— Theoria.md 1.10(b) 的八道工序</span></h2>')
    A('<table class="wide"><thead><tr><th>工序</th><th>引擎</th><th>状态</th>'
      '<th>实况</th></tr></thead><tbody>')
    for e in spec.ENGINES:
        A('<tr class="%s"><td><b>%s</b><span class="clause">%s</span></td><td>%s</td>'
          '<td>%s</td><td class="nt">%s</td></tr>'
          % (e["status"], esc(e["step"]), esc(e["module"]), esc(e["engine"]),
             cell(e["status"]), md_bold(esc(e["note"]))))
    A('</tbody></table></section>')

    # ---- constraints
    A('<section><h2>十条强制约束 <span class="note">— Theoria.md 1.10(e)</span></h2>')
    A('<table class="wide"><thead><tr><th>#</th><th>约束</th><th>状态</th>'
      '<th>实况</th></tr></thead><tbody>')
    for c in spec.CONSTRAINTS:
        A('<tr class="%s"><td class="num">%d</td><td>%s</td><td>%s</td>'
          '<td class="nt">%s</td></tr>'
          % (c["status"], c["n"], esc(c["text"]), cell(c["status"]),
             md_bold(esc(c["note"]))))
    A('</tbody></table></section>')

    # ---- claims
    A('<section><h2>Claim 菜单 <span class="note">— Phase 3 现在列死的五条</span></h2>')
    A('<table class="wide"><thead><tr><th>#</th><th>角色</th><th>claim</th>'
      '<th>状态</th><th>实况</th></tr></thead><tbody>')
    for c in spec.CLAIMS:
        A('<tr class="%s"><td class="num">%s</td><td>%s</td><td>%s</td><td>%s</td>'
          '<td class="nt">%s</td></tr>'
          % (c["status"], esc(c["id"]), esc(c["role"]), esc(c["text"]),
             cell(c["status"]), md_bold(esc(c["note"]))))
    A('</tbody></table></section>')

    # ---- live facts
    A('<section><h2>本次扫描读到的事实 <span class="note">— 全部可复演</span></h2>')
    A('<div class="facts">')
    facts = [
        ("HEAD", m["git_head"]),
        ("未提交 / 未跟踪", "%d 项（其中未跟踪 %d）" % (len(m["dirty"]), len(m["untracked"]))),
        ("PARTNER_SYNC", "%d 段，最后一段 %s" % (m["sync_entries"], m.get("sync_last", "—"))),
        ("开发堆", ", ".join(m["dev_pile"]) or "—"),
        ("封存堆", "%d 局" % m["sealed_count"]),
        ("incidents.jsonl", "%d 条" % m["incidents"]),
        ("engine-rig 候选流", "%d 条" % m["engine_candidates"]),
        ("A0 候选流", "%d 条，%d 条转移" % (m["a0_candidates"], m["a0_transitions"])),
    ]
    for k, v in facts:
        A('<div class="fact"><span class="fk">%s</span><span class="fv">%s</span></div>'
          % (esc(k), esc(v)))
    for track, line in (m.get("tests") or {}).items():
        A('<div class="fact"><span class="fk">%s 测试</span><span class="fv">%s</span></div>'
          % (esc(track), esc(line)))
    A('</div>')
    if not m.get("tests"):
        A('<p class="note">测试未运行 —— 用 <code>python monitor/scan.py --tests</code> '
          '把两条轨道的 pytest 结果也纳入本次扫描。</p>')
    A('</section>')

    # ---- tickets
    A('<section><h2>工单 <span class="note">— 复制整份，直接粘给一个新的 '
      'Claude Code 会话；派工顺序见 monitor/prompts/README.md</span></h2>')
    for i, t in enumerate(state["tickets"]):
        tid = "tk%d" % i
        A('<details class="ticket"><summary><span class="tfile">%s</span>%s'
          '<button class="copy" onclick="copyTicket(event,\'%s\')">复制工单</button>'
          '</summary><textarea id="%s" readonly rows="16" spellcheck="false">%s'
          '</textarea></details>'
          % (esc(t["file"]), esc(t["title"]), tid, tid,
             html.escape(t["text"])))
    A("""<script>
function copyTicket(ev, id){
  ev.preventDefault(); ev.stopPropagation();
  var ta = document.getElementById(id), btn = ev.target;
  ta.focus(); ta.select(); ta.setSelectionRange(0, ta.value.length);
  var ok = false;
  try { ok = document.execCommand('copy'); } catch(e) {}
  if (!ok && navigator.clipboard) {
    navigator.clipboard.writeText(ta.value).then(function(){ flash(btn); });
  } else { flash(btn); }
  function flash(b){ var t=b.textContent; b.textContent='已复制 ✓';
    setTimeout(function(){ b.textContent=t; }, 1600); }
}
</script>""")
    A('</section>')

    A('<footer><p>本页由 <code>monitor/scan.py</code> 从工作树生成，'
      '判断依据记在 <code>monitor/spec.py</code>（逐条引用 Theoria.md 的出处）。'
      '重跑即刷新。监视器只写 <code>monitor/</code>，不碰任何轨道。</p></footer>')
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

footer{margin-top:50px;padding-top:18px;border-top:1px solid var(--line);
  color:var(--mut);font-size:12.5px}
@media(max-width:720px){
  header{padding:26px 16px 0}main{padding:0 16px 50px}
  .lb{width:auto}table{font-size:13px}td{padding:9px 10px}
}
</style>"""


# ---------------------------------------------------------------- main

def build(with_tests=False):
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
    n_prob = sum(len(ex["problems"]) for ex in spec.ITERATION_LOOP)
    n_landed = sum(1 for ex in spec.ITERATION_LOOP
                   for p in ex["problems"] if p["status"] == "landed")
    state["loop_stats"] = (len(spec.ITERATION_LOOP), n_prob, n_landed)
    append_history(state)
    state["history"] = load_history()

    with open(os.path.join(HERE, "index.html"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(render(state, refresh=build.refresh))
    slim = {k: v for k, v in state.items() if k != "tickets"}
    with open(os.path.join(HERE, "state.json"), "w", encoding="utf-8", newline="\n") as fh:
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
