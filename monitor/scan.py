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
import calendar
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

import childio  # noqa: E402  (per-child decoding; see its docstring)

# S30. `spec.py` is the hand-written judgement file the fleet edits every
# cycle, so a SyntaxError in it is the single most likely way this program
# dies. Imported bare, that death happened *before* `main()` -- before the
# failure exit could run -- and the page simply kept showing yesterday's
# numbers, which is the whole defect S30 exists to remove. Deferring the
# failure to `build()` puts it inside the handler instead. Nothing at module
# level touches `spec`, so nothing else changes.
try:
    import spec  # noqa: E402
except Exception as _exc:                       # noqa: BLE001 -- re-raised
    spec = None
    _SPEC_IMPORT_ERROR = _exc
else:
    _SPEC_IMPORT_ERROR = None

GAME_ID = re.compile(r"\b[a-z0-9]{4}-[0-9a-f]{8}\b")
SKIP_DIRS = {".git", "__pycache__", ".toolchain", ".lake", "node_modules",
             ".pytest_cache", ".egg-info", "out",
             # **`.worktrees` 不在这里，代价是 37 GB。**
             #
             # 2026-07-30 实测：`probe_credential_hygiene` 的 `os.walk(ROOT)` 要遍历
             # **1,629,026 个文件、合计 37.2 GB**，并且把**每一个都整份读进内存**——
             # 因为舰队攒了 331 棵工作树，每棵都是一份完整的仓库副本，里面还各带着
             # 几十上百 MB 的 candidates.jsonl。
             #
             # 一个探针，五个症状：scan.build 挂住 → 仪表盘从 11:49 起再没更新过 →
             # 闸门的 real-run 段挂住 → `test_a_real_scan_can_run_without_touching_
             # the_workspace` 卡在 34% → 闸门 900 秒超时 → **九条已交付分支被记成红**。
             # 我先前把这一串归因成「机器负载」，那是错的：负载只是让它更明显。
             #
             # 工作树是主树的副本，它们的内容在主树里已经被扫过；而真正的规矩
             # （CLAUDE.md）说的是「密钥不得进入任何**被跟踪的**文件」，
             # 那件事在主树上就能判完。
             ".worktrees"}


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


def git_or_none(*args):
    """git's stdout, or `None` when the call did not produce an answer.

    S30. This is the distinction the 55 `UnicodeDecodeError` tracebacks in
    `refresh.log` turned out to be about. The decode raised inside
    `subprocess`'s **reader thread**, where it cannot propagate; `_communicate`
    then handed back `stdout=None`, `git()` swallowed the resulting
    `AttributeError` into `""`, and `probe_conflicts` read the empty string as
    「三类检查全空」and reported green. All 54 crash cycles reported green; the
    141 clean cycles reported risk 90 times. The crash never stopped the scan
    -- it deleted one probe's evidence and let the probe call that innocence.

    The decode itself is fixed (`encoding="utf-8", errors="replace"` below), but
    a timeout, a missing binary, or a non-zero exit still produce empty output,
    and empty output still reads as clean. So callers that would *judge* on the
    result take `None` and say they could not look.
    """
    try:
        out = subprocess.run(["git"] + list(args), cwd=ROOT,
                             capture_output=True, text=True, timeout=30,
                             encoding="utf-8", errors="replace")
    except Exception:
        return None
    if out.returncode != 0 or out.stdout is None:
        # `stdout is None` is the exact 2026-07-28 shape: exit 0, no output,
        # because the reader thread died decoding. Kept as an explicit case so
        # it cannot come back unnamed.
        return None
    return out.stdout.strip()


def git(*args):
    """Stdout, with failure flattened to `""`.

    Fine for the callers that only *display* what git said. A caller that turns
    the result into a verdict must use `git_or_none` instead -- see its
    docstring for what this flattening cost.
    """
    out = git_or_none(*args)
    return "" if out is None else out


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
                # 分块读，不整份读进内存。主树里有 17.9 MB 的 candidates.jsonl，
                # 而 `.read()` 会把它整个变成一个字符串；1.6 万个这样的文件
                # 就是这个探针挂住的另一半原因。
                # 块之间留 len(key)-1 的重叠，免得密钥恰好跨在块边界上被漏掉——
                # **一个会漏报的泄漏检查比没有检查更坏**，它会让人以为查过了。
                overlap = max(0, len(key) - 1)
                with open(path, encoding="utf-8", errors="ignore") as fh:
                    tail = ""
                    while True:
                        chunk = fh.read(1 << 20)
                        if not chunk:
                            break
                        if key in tail + chunk:
                            leaks.append(os.path.relpath(path, ROOT)
                                         .replace("\\", "/"))
                            break
                        tail = chunk[-overlap:] if overlap else ""
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


# The two tracks meet at exactly one place and name it the same way on both
# sides: `engine-rig/interop/certificate_export.py:95` stamps the schema, and
# `theory-compiler/src/theory_compiler/certificate.py:38` pins it to read the
# file. Either token is a real handshake; the bare word "certificate" is not.
A1_SCHEMA = "lp_potential/pagoda_certificate@"
A1_INTEROP_DIR = "interop/certificates"


def probe_a1_state():
    bridge = exists("engine-rig/interop/certificate_export.py")
    # The handshake is the schema id both sides name -- `certificate_export.py`
    # stamps it, and a consumer has to know it to read the file. The old test
    # was the bare word "certificate" anywhere under theory-compiler, which the
    # Lean proofs satisfy in prose comments ("the certificate's pattern: ...").
    # Once the criterion decides something, a token that a comment can supply is
    # not a criterion; replacing a gate that never opens with one that opens on
    # a word is the worse trade of the two.
    consumed = False
    tc = rel("theory-compiler")
    for base, dirs, files in os.walk(tc):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        # `runs/` holds artefacts of past runs, not the track's source. A
        # certificate quoted in a run log is evidence something happened once,
        # not evidence the bridge is wired up now.
        if "runs" in os.path.relpath(base, tc).split(os.sep):
            continue
        for name in files:
            if name.endswith((".py", ".lean")):
                try:
                    text = open(os.path.join(base, name),
                                encoding="utf-8", errors="ignore").read()
                except Exception:
                    continue
                if A1_SCHEMA in text or A1_INTEROP_DIR in text:
                    consumed = True
    # Both halves were computed, formatted into `detail`, and then discarded --
    # the return was an unconditional `partial`, so this gate could neither open
    # nor close no matter what the tree looked like. A gate that cannot close is
    # a gate that gets stepped over, and this one was: Theoria.md 305 makes an
    # all-green Phase 1 the precondition for spending game money, and money was
    # spent across it at 9/16. The criterion now decides.
    status = "green" if (bridge and consumed) else (
        "partial" if (bridge or consumed) else "risk")
    return {"status": status,
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
    #
    # S30: `git_or_none`, not `git`. Both this call and (c) below are turned
    # into a verdict, and a verdict built on "the command returned nothing"
    # cannot tell a clean index from a git that never answered.
    blind = []
    unmerged = git_or_none("ls-files", "-u")
    if unmerged is None:
        blind.append("git ls-files -u")
        unmerged = ""
    if unmerged:
        paths = sorted({line.split("\t")[-1] for line in unmerged.splitlines()})
        findings.append("git 未合并路径：" + ", ".join(paths))

    # (c) cross-territory commits: one commit spanning 2+ *owners*.
    # a0-spike belongs to the engine-rig track and cold-start-a0 to the
    # theory-compiler track (CLAUDE.md), so those pairs are one territory.
    track_of = {"engine-rig": "engine-rig", "a0-spike": "engine-rig",
                "theory-compiler": "theory-compiler",
                "cold-start-a0": "theory-compiler"}
    log = git_or_none("log", "--name-only", "--format=%h%x01%s", "-40")
    if log is None:
        # The exact call that failed 55 times. It is named here so the page
        # says which eye is shut rather than reporting a general unease.
        blind.append("git log --name-only -40")
        log = ""
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

    # S30. Order matters, and the first version of this got it backwards.
    #
    # `findings` is checked FIRST. Check (a) scans files on disk and cannot go
    # blind, so a conflict marker it found is real evidence regardless of what
    # git did. Reporting `missing` ahead of it discarded that evidence and
    # replaced it with a statement about not having looked -- and since
    # `_VERDICT_RANK` puts `missing` above `risk`, that was an *upgrade* away
    # from the worst verdict. Which is this ticket's own defect, committed by
    # its own fix. Blindness is reported alongside a real finding, never
    # instead of it.
    blind_note = ("　⚠ 另有**没有检查成**的部分：%s 没有返回结果"
                  % "、".join(blind)) if blind else ""
    if findings:
        return {"status": "risk",
                "detail": " ⚠ ".join(findings) + blind_note}
    # Nothing found -- but "found nothing" only means something if we could
    # look. `missing` rather than `risk`: a git that would not answer is not
    # evidence of a conflict, it is the absence of evidence either way, and
    # this repository does not paint absence as red any more than as zero.
    if blind:
        return {"status": "missing",
                "detail": "这一项**没有检查成**：%s 没有返回结果，"
                          "所以「没发现冲突」这句话本轮不成立。"
                          "（2026-07-28 这条路径静默地绿了 54 个周期）"
                          % "、".join(blind)}
    return {"status": "green",
            "detail": "三类检查全空：无冲突标记、无未合并路径、"
                      "近 40 个提交无跨领地改动。"}


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
    # S28：`if not exists(path): continue` 之后仍然把 `len(watched)` 报成
    # 「已核查干净」——**而删除恰恰是这条规则的最大违反**。实测：把
    # battery/PREDICTIONS.md 当作不存在，这个探针照旧返回
    # `green / 4 个追加式文件无新增删除`。缺失从此单列，且文案改成 checked/total。
    absent = []
    checked = 0
    for path in watched:
        if not exists(path):
            absent.append(path)
            continue
        checked += 1
        # --first-parent: only what actually appeared on the mainline counts.
        # A branch-local fix before merge never published anything, so it is
        # not a violation (OPS-A, 2026-07-28: my earlier ruling cited it wrongly).
        # S30: blind here meant `dels = 0`, i.e. 「append-only 规则完好」 --
        # a clean bill of health for the one rule whose whole point is that
        # nobody can quietly delete from these files.
        # S38：**锚在 `origin/master` 上，不在 HEAD 上。**
        #
        # 上面那段注释写的判据是对的（「once it is on the mainline it is frozen;
        # on a branch, fix it until it is right」），它连 `6dec6f7` 不该被计入
        # 都点名了。但实现从 HEAD 的第一父链求和，而在**分支上** HEAD 的第一父链
        # 就是这条分支自己的提交——包括还没发布的那些。于是每一次作者修正自己
        # 尚未发布的草稿段落，都被计成一次违反。**这个不一致只在分支上看得见**：
        # 在 master 上，合并提交的 first-parent numstat 是净变化，分支内的来回
        # 根本不出现，所以注释里那句话在那里是成立的。
        #
        # 实测（`runs/20260730T0410Z-S38/measure.json`，211 条本地分支）：
        # 旧判据红 **26** 条，新判据红 **1** 条——**25 条是假红**。
        # 而剩下的那 1 条是 `agent/v26-handover-leak-ruling`，它确实原地改写了
        # 一段已由 `d35e89cb` 发布到主线的段落。同一天由另一条完全独立的路径
        # （逐条读 diff 的人工裁决，S36）挑出来的也正是这一条。
        #
        # 假红的代价不是漏报，是**会自愈**：合并之后自己变绿，于是看见它的人
        # 学到「这条闸会乱叫」。它还把便宜的错解摆在顺手的位置——去 `BASELINE`
        # 加豁免行数，为一段从未发布的草稿**永久放宽对已发布内容的守卫**。
        anchor = "origin/master"
        if git_or_none("rev-parse", "--verify", "--quiet", anchor) is None:
            # 没有远端锚点（新克隆、测试用的临时仓）。回落到 HEAD 是旧行为，
            # 在 master 上正确；把这件事写进 detail，别让读者以为基础一样强。
            anchor = "HEAD"
        out = git_or_none("log", "--first-parent", "--numstat", "--format=%h",
                          anchor, "--", path)
        if out is None:
            return {"status": "missing",
                    "detail": "问不出 %s 的删除历史（git 没有返回结果），"
                              "本轮无法断言 append-only 完好。" % path}
        dels, cur = 0, ""
        for line in out.splitlines():
            parts = line.split("	")
            if len(parts) == 3 and parts[1].isdigit():
                dels += int(parts[1])
            elif line.strip():
                cur = line.strip()
        # 本分支自己的贡献：`merge-base(anchor, HEAD)..HEAD` 的净删除。
        # **必须用 merge-base，不能用两点 `anchor..HEAD`**：分支基线落后时，
        # 两点 diff 会把「基线之后别人加的行」全部报成本分支删的
        # ——S35 实测那样算是 5 增 33 删，而 33 行里一个字都不是它删的。
        #
        # 这一半是这道闸的牙齿：**一条净删除了已发布行的分支仍然红**，
        # 而且是在它合并**之前**就红。旧实现在分支上红得毫无分辨力，
        # 反而让这一类混在 25 条假红里。
        own = 0
        if anchor != "HEAD":
            mb = git_or_none("merge-base", anchor, "HEAD")
            if mb and mb.strip():
                d = git_or_none("diff", "--numstat",
                                "%s..HEAD" % mb.strip().splitlines()[0],
                                "--", path)
                for line in (d or "").splitlines():
                    parts = line.split("	")
                    if len(parts) == 3 and parts[1].isdigit():
                        own += int(parts[1])
        allowed = BASELINE.get(path, 0)
        if dels + own > allowed:
            offenders.append("%s（已发布删除 %d 行 + 本分支净删除 %d 行，"
                             "超出已裁决豁免 %d 行）" % (path, dels, own, allowed))
    if offenders:
        return {"status": "risk",
                "detail": "追加式文件出现删除：" + "； ".join(offenders) +
                          "。既往裁决：同窗口自我订正可，跨窗口须新段落 supersede。"}
    exempt = sum(BASELINE.values())
    if absent:
        # 整个文件不见了，是这条规则能被违反的最彻底的方式。
        return {"status": "risk",
                "detail": "追加式文件**不存在**：%s。已核查 %d/%d 件，"
                          "其余无新增删除——但缺失的那几件无法断言。"
                          % ("、".join(absent), checked, len(watched))}
    return {"status": "green",
            "detail": "已核查 %d/%d 个追加式文件，无新增删除"
                      "（%d 行历史删除已裁决豁免：同窗口自我订正）。"
                      % (checked, len(watched), exempt)}


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
        # S28：这里原来强制 `encoding="utf-8"` 读 schtasks，而 schtasks 是
        # Windows 内建、印的是**控制台代码页**（本机 cp936）。于是英文
        # `Disabled` 一次也不会出现、中文「已禁用」被 `errors="replace"` 换成
        # U+FFFD，**`disabled` 对任何任务恒为 False**——而这个探针存在的理由
        # 正是「两个 ops 报告 TheoriaReflex 处于 Disabled 而板上无人提及」。
        # 实测同一次查询：forced-utf-8 得到 `ģʽ:  ��������`（U+FFFD 满屏），
        # run_console 得到 `模式: 正在运行`。规则写在 childio.py 的 docstring 里。
        out = childio.run_console(["schtasks", "/Query", "/TN", name,
                                   "/FO", "LIST"])
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
    # S30: `git_or_none` at all three sites. This probe turns counts into a
    # verdict, and with plain `git()` a blind call fell back to `"0"` -- i.e.
    # 「spec.py 一点没落后」, a **green built on a git that never answered**.
    # Same shape as the 55-traceback false green, two probes away from it.
    last = git_or_none("log", "-1", "--format=%H", "--", "monitor/spec.py")
    if last is None:
        return {"status": "missing",
                "detail": "问不出 spec.py 的最后一次提交（git 没有返回结果），"
                          "所以本轮说不出它有多陈旧——不是「不陈旧」。"}
    last = last.strip()
    if not last:
        return {"status": "partial", "detail": "spec.py 无提交历史。"}
    commits = git_or_none("rev-list", "--count", "%s..HEAD" % last)
    merges = git_or_none("rev-list", "--count", "--merges", "%s..HEAD" % last)
    if commits is None or merges is None:
        return {"status": "missing",
                "detail": "数不出 spec.py 之后的提交数（git 没有返回结果）。"
                          "空输出曾经在这里被当成 0，也就是「完全不陈旧」。"}
    n, m = int(commits.strip() or 0), int(merges.strip() or 0)
    status = "green" if n < 15 else ("partial" if n < 40 else "risk")
    return {"status": status,
            "detail": "spec.py 落后 %d 个提交 / %d 次合并（判断陈旧到 %s 就该重扫）。"
                      % (n, m, "risk" if n >= 40 else "partial 档")}


#: Below this the machine is one pytest away from failing a merge for a reason
#: that has nothing to do with the branch.  Set from the observed event: at
#: 9.1 GB free, a0-spike's gate died with `OSError: [Errno 28] No space left on
#: device` and the flag read "verify gate red in a0-spike".
DISK_RISK_GB = 12.0
DISK_PARTIAL_GB = 25.0


def probe_disk_headroom():
    """磁盘余量与 worktree 存量 —— 资源耗尽会伪装成别人的缺陷。

    2026-07-29：115 个 worktree（71 个早已合并）把磁盘吃到 99%，
    第一个症状是 a0-spike 的闸门报红 `No space left on device`，
    合并日志上写的是「verify gate red in a0-spike」——**仪器怪罪了被测对象**。
    没有量表的资源，耗尽时总是在别处报错。
    """
    import shutil as _shutil
    try:
        total, _used, free = _shutil.disk_usage(ROOT)
    except OSError as exc:
        return {"status": "risk", "detail": "读不到磁盘用量：%s" % exc}
    free_gb, total_gb = free / (1024 ** 3), total / (1024 ** 3)

    wt = 0
    try:
        out = subprocess.run(["git", "worktree", "list", "--porcelain"],
                             cwd=ROOT, capture_output=True, text=True,
                             encoding="utf-8", errors="replace")
        wt = sum(1 for l in out.stdout.splitlines() if l.startswith("worktree "))
    except Exception:
        wt = -1

    tail = ("%d 个 worktree 在册；`python monitor/reap_worktrees.py` 看哪些已完工"
            % wt) if wt >= 0 else "worktree 数量读不到"
    if free_gb < DISK_RISK_GB:
        return {"status": "risk",
                "detail": "**磁盘仅剩 %.1f GB / %.0f GB**——这个水位上任何一次"
                          "合并都可能因为跑不动而报成某个领地的闸门红。%s"
                          % (free_gb, total_gb, tail)}
    if free_gb < DISK_PARTIAL_GB:
        return {"status": "partial",
                "detail": "磁盘剩 %.1f GB / %.0f GB，接近会开始伪装成闸门失败的"
                          "水位。%s" % (free_gb, total_gb, tail)}
    return {"status": "green",
            "detail": "磁盘剩 %.1f GB / %.0f GB；%s" % (free_gb, total_gb, tail)}


def _stamps_to_check():
    """(label, path, claimed-utc-string) for every hand-typed timestamp on disk.

    Three sources, because the first version of this probe checked one. It
    checked the heartbeats -- the instance I had noticed -- and then I wrote the
    same error twice more in the same session, into a PARTNER_SYNC paragraph
    header and a run MANIFEST, and it saw neither.

    That is "fixed one instance, believed I had fixed the class": the probe's
    scope was pinned to its first sample. The class is *any UTC a human typed*,
    and the repository has exactly these three kinds.
    """
    import glob as _glob
    out = []
    for path in sorted(_glob.glob(rel("monitor", "ops-status", "*.json"))):
        name = os.path.basename(path)[:-5]
        try:
            data = json.load(open(path, encoding="utf-8"))
        except Exception as exc:
            out.append(("heartbeat %s" % name, path, None, str(exc)[:40]))
            continue
        out.append(("heartbeat %s" % name, path, data.get("utc"), None))

    for path in sorted(_glob.glob(rel("*", "runs", "*", "MANIFEST.json"))):
        label = "manifest %s" % os.path.basename(os.path.dirname(path))
        try:
            data = json.load(open(path, encoding="utf-8"))
        except Exception as exc:
            out.append((label, path, None, str(exc)[:40]))
            continue
        # A manifest without `utc` is provenance's problem, not this probe's --
        # `provenance_scan` already reports it, and two probes shouting about
        # one fact is how both get ignored.
        if data.get("utc") is not None:
            out.append((label, path, data.get("utc"), None))

    sync = rel("PARTNER_SYNC.md")
    if os.path.exists(sync):
        try:
            text = open(sync, encoding="utf-8", errors="replace").read()
        except OSError:
            text = ""
        for m in re.finditer(r"^##\s+\[[^\]]+\]\s+(\S+)", text, re.M):
            out.append(("PARTNER_SYNC %s" % m.group(1), sync, m.group(1), None))
    return out


def probe_clock_sanity():
    """手打的 UTC 不得晚于机器当前 UTC —— 时钟不可能超前。

    存活判断用的是文件 mtime（agent 伪造不了），所以掉线检测本身是可靠的。
    但**手打的**时间戳从来没有任何东西校验过：2026-07-28T15:47Z 那一刻，
    RES-1 的心跳写着 20:55Z，RES-2/3/4 写着 16:0x–16:4xZ——全都还没到。

    危险在方向：一个只会向前跑的自报时间，让**掉线的会话看起来比实际更新鲜**，
    也让一份留痕看起来比它实际的更新。这是纯算术，没有任何借口不检查。

    **作用域**：心跳、`runs/*/MANIFEST.json`、`PARTNER_SYNC.md` 的段落头。
    第一版只查心跳，然后写它的人在同一个会话里又把另外两种各写错一次——
    一个探针的作用域若被它的第一个样本框死，它会漏掉同一类的其余部分。
    """
    now = time.time()
    ahead, drifted, unreadable = [], [], []
    for label, path, stamp, err in _stamps_to_check():
        if err is not None:
            unreadable.append("%s（%s）" % (label, err))
            continue
        if not isinstance(stamp, str):
            unreadable.append("%s（没有 utc 字段）" % label)
            continue
        try:
            claimed = calendar.timegm(time.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ"))
        except ValueError:
            try:
                claimed = calendar.timegm(time.strptime(stamp, "%Y-%m-%dT%H:%MZ"))
            except ValueError:
                unreadable.append("%s（不是 ISO8601Z：%r）" % (label, stamp[:30]))
                continue
        # 60s of slack: writing the stamp and closing the file are not atomic.
        if claimed > now + 60:
            ahead.append("%s 自报 %s，超前 %.0f 分钟"
                         % (label, stamp, (claimed - now) / 60))
            continue
        try:
            mtime = os.path.getmtime(path)
        except OSError:
            continue
        # PARTNER_SYNC is append-only, so its old paragraphs are legitimately
        # far older than the file; only the future check applies to them.
        if label.startswith("PARTNER_SYNC"):
            continue
        if abs(claimed - mtime) > 3600:
            drifted.append("%s 自报 %s，与文件 mtime 差 %.0f 分钟"
                           % (label, stamp, abs(claimed - mtime) / 60))
    if ahead:
        return {"status": "risk",
                "detail": "**%d 处手打的时间还没到**：%s。时钟不可能超前，"
                          "所以这些是手打的；危险在方向——只会向前跑的自报时间"
                          "让掉线看起来比实际新鲜、让留痕看起来比实际更新。"
                          "取值请用 date -u。"
                          % (len(ahead), "；".join(ahead[:4]))}
    if unreadable:
        return {"status": "risk",
                "detail": "**%d 处时间戳读不出来**：%s。读不出不等于没问题。"
                          % (len(unreadable), "；".join(unreadable[:4]))}
    if drifted:
        return {"status": "partial",
                "detail": "%d 处自报时间与文件 mtime 相差超过一小时：%s。"
                          % (len(drifted), "；".join(drifted[:4]))}
    return {"status": "green",
            "detail": "心跳、run 留痕与 PARTNER_SYNC 段落头的时间全部不晚于机器 UTC。"}


def _merge_queue_probe():
    """合并队列 —— 二十一个探针里没有一个读过 merge.log（S25）。

    五条已交付分支自 2026-07-28 15:22 起每十分钟被重新 FLAG 一次、堵了十小时，
    而盘面上完全看不见：合并失败**不产生任何人会看的信号**。
    """
    import mergequeue
    return mergequeue.probe()

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
    # S28：`survey["decorative"]` 一直被算出来、一直被丢掉。`gates.py` 的注释
    # 逐字写着「'19 gated' 和 '19 gates known to work' 是两个不同的断言」，
    # 而这条探针**读了前一个、印了后一个**。实测此刻：自带闸门 24 个，
    # 其中 **22 个从没被证明能变红**，而旧文案只印「自带闸门 24、无闸门 0」，
    # 状态 green。
    #
    # 刻意**不**据此压成 partial：那 22 个里至少有几个有未声明的阴性对照，
    # 长期压下去等于长期喊狼来了，而喊狼的检查会被关掉——一条被关掉的检查
    # 和一条不存在的检查是同一回事（这条探针自己的 docstring 就这么写的）。
    # 所以让**数字**可见，而不是让**告警**变响。
    decorative = survey["decorative"]
    coverage = ("领地 %d：自带闸门 %d（其中 **%d 个从未被证明能变红**）、"
                "仅测试套件 %d、**无闸门 %d**") % (
        survey["n_territories"], len(survey["gated"]), len(decorative),
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
    """板上还剩几件可领 —— 供货是监控的单点，见底就是全员空转。

    S28：这里原来是**去数 `board.py list` 输出里 `"  p"` 开头的行**，而 board.py
    的 available 段和 reserved 段都印这个前缀（现在还多了 territory-blocked 段）。
    于是仓库里有两个互相矛盾的供货数，**被渲染出来的是错的那个**：
    实测同一时刻，前缀匹配数出 4（页面印「供货充足」绿色），
    而 `board.candidates()` 是 1；`reflex.py` 早就在用后者并诚实地记 `SUPPLY-LOW:1`。

    改成直接问 `board`。数一个渲染给人看的字符串，本来就是在拿排版当 API。
    """
    try:
        sys.path.insert(0, HERE)
        import board as board_mod
        avail = len(board_mod.candidates())
        claimed = len(board_mod.claimed_map())
    except Exception as exc:                    # noqa: BLE001 -- 报出来
        # 问不到就说问不到。这个探针存在的理由是「见底就是全员空转」，
        # 而「数不出来」绝不能长得像「板上很充足」。
        return {"status": "risk",
                "detail": "**板查不出来**（%s: %s）——供货数未知，"
                          "不要当成充足。" % (type(exc).__name__, exc)}
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


def _ack_required():
    """回执词表**从 bus 协议取**，不在这里手打第二份。

    取不到就退回三个词的字面量——比缩水的两个词安全，因为漏报一条欠着的
    urgent 正是这次要修的那个静默失败。
    """
    try:
        sys.path.insert(0, HERE)
        from bus import ACK_REQUIRED
        return ACK_REQUIRED
    except Exception:
        return ("order", "urgent", "question")


_ACK_REQUIRED = _ack_required()


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
        # S28：这里原来手打了一个缩水的集合 `("order", "question")`，
        # 把 `urgent` 漏在「欠回执」之外。而 `bus.py` 自己的 `ACK_REQUIRED`
        # 是三个，`cmd_read` 会**永远重发**一条没回执的 urgent，
        # 状态行却印「指令全部已读并回执」。
        # 漏掉的那个失败模式是最要紧的一种：**心跳还在写、cycle 还在推进、
        # 就是不执行指令的活会话，无人报告。**
        # （`notice` 不纳入——协议明说无需回执。这正是导入而不是手打的理由：
        # 这个词表属于 bus 协议，不属于盘面。）
        pend = [m["seq"] for m in sent
                if m["kind"] in _ACK_REQUIRED and m["seq"] not in acked]
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


def _parse_utc(stamp):
    """`2026-07-29T07:45:00Z` -> epoch seconds, or None if it is not that.

    None rather than an exception: a malformed `wake_at` must fall back to the
    old staleness rule, not take the probe down. A liveness check that dies on
    bad input reports nothing about anybody.
    """
    try:
        return calendar.timegm(time.strptime(str(stamp), "%Y-%m-%dT%H:%M:%SZ"))
    except Exception:
        return None


def _self_driving():
    """常驻研究员是否在自转 —— 用户不该需要触发它们。

    判据是心跳的推进：cycle 在涨、note 在变、age 不超过一个循环周期。
    停在那里等人的会话，心跳会定格——这正是用户今天观察到的现象。"""
    import time as _t
    rows, bad = [], []
    for rid in ("RES-1", "RES-2", "RES-3", "RES-4"):
        path = "monitor/ops-status/%s.json" % rid
        if not exists(path):
            # Was `continue` with the verdict decided by a substring search over
            # the display strings -- so a researcher who never started at all
            # left no "疑似停下" anywhere and the probe reported green. Never
            # started and running fine were the same colour.
            rows.append("%s 未启动（无心跳文件）" % rid)
            bad.append(rid)
            continue
        d = read_json(path, {}) or {}
        age = int((_t.time() - os.path.getmtime(rel(path))) / 60)
        # S19: asleep and closed look identical from outside -- a timestamp has
        # no power to tell them apart, and OPS-R sleeping 12 hours was read as
        # dropped. A session that plans to sleep says when it will be back, and
        # the two states stop sharing a signature: before `wake_at` a silence is
        # scheduled; after it, the silence is the session failing to keep its
        # own appointment, which is a louder fact than merely being stale.
        wake_at = d.get("wake_at")
        due = _parse_utc(wake_at) if wake_at else None
        stalled = age > 45          # 一轮活再长也该在 45 分钟内写一次心跳
        if due is not None and _t.time() < due:
            state = "按计划睡到 %s" % wake_at
        elif due is not None and stalled:
            state = "**说好 %s 醒，没醒**" % wake_at
            bad.append(rid)
        elif stalled:
            state = "**疑似停下等人**"
            bad.append(rid)
        else:
            state = ""
        rows.append("%s 第%s轮 %s（%d 分钟前）%s"
                    % (rid, d.get("cycle"), d.get("state"), age, state))
    return {"status": "risk" if bad else "green",
            "detail": "； ".join(rows) +
                      ("　→ 已发 urgent 催醒；若仍不动，说明会话已死，需重开。（%s）"
                       % "、".join(bad) if bad else "")}


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


def probe_standing():
    """常驻研究员的例行程序还在跳吗，上一跳做了什么决定。

    这条探针的存在本身是个教训：`standing.py` 起会话的判断全在磁盘上，
    而一个没人看的自动机制与一个坏掉的自动机制，在页面上长得一模一样。"""
    log_path = rel("monitor", "standing.log")
    task = "TheoriaStanding"
    out = subprocess.run(["schtasks", "/Query", "/TN", task, "/FO", "LIST"],
                         capture_output=True, text=True, encoding="utf-8",
                         errors="replace")
    registered = out.returncode == 0
    if not exists("monitor/standing.log"):
        return {"status": "risk" if not registered else "partial",
                "detail": "例行任务 %s；**还没有跳过一次**（standing.log 不存在）。"
                          % ("已注册" if registered else "**未注册**")}
    lines = [l.strip() for l in
             open(log_path, encoding="utf-8", errors="replace").read()
             .splitlines() if l.strip()]
    age = int((time.time() - os.path.getmtime(log_path)) / 60)
    starts = [l for l in lines if " START " in l]
    tail = lines[-4:]
    stale = age > 40          # 周期 15 分钟，跳过两次就是坏了
    return {"status": ("risk" if (stale or not registered) else "green"),
            "detail": "例行任务 %s，上一跳 %d 分钟前；累计起过 %d 次常驻会话。"
                      "最近：%s%s"
                      % ("已注册" if registered else "**未注册**", age,
                         len(starts), "；".join(t.split(" ", 1)[-1][:70]
                                                for t in tail),
                         "　→ **超过两个周期没跳，例行已停**" if stale else "")}


def _accounts_rows():
    """账号池的结构化行。读不出来返回空表——**空表不等于「没问题」**，
    页面据此显示「账号池不可读」，而不是显示一个漂亮的空白。"""
    try:
        sys.path.insert(0, HERE)
        import accounts as _acct
        return _acct.status()
    except Exception:
        return []


def _agent_account(agent_id):
    """这个 agent 最近一次是跑在哪个账号上的；不知道就是 None，不猜。"""
    logs = rel("monitor", "dispatch-logs")
    if not os.path.isdir(logs):
        return None
    best, best_m = None, 0
    for name in os.listdir(logs):
        if not (name.startswith(agent_id + "-") and name.endswith(".log")):
            continue
        path = os.path.join(logs, name)
        try:
            m = os.path.getmtime(path)
        except OSError:
            continue
        if m > best_m:
            best, best_m = path, m
    if not best:
        return None
    try:
        with open(best, encoding="utf-8", errors="replace") as fh:
            for _ in range(4):
                line = fh.readline()
                if not line:
                    break
                hit = re.search(r"account=(\S+)", line)
                if hit:
                    a = hit.group(1)
                    return None if a.startswith("default") else a
    except OSError:
        return None
    return None


def _fleet_rows():
    """现役舰队：六个常驻岗 + 在跑的一次性工人。

    「活着」问的是**计划任务表**（无头是唯一启动路径之后它就是权威）与
    **工作板上的动作**，不问 agent 的自述——自述的时刻会漂前，文件的 mtime
    会被一次 merge 摸新，而一行 CLAIM/DONE 只可能由活着的会话写出来。"""
    try:
        sys.path.insert(0, HERE)
        import board as board_mod
        import standing as standing_mod
    except Exception:
        return {"error": "fleet modules unreadable"}
    try:
        live = standing_mod.running_tasks()
    except Exception:
        live = set()
    claimed = {}
    try:
        for f in os.listdir(board_mod.CLAIMED):
            if f.endswith(".md"):
                parts = f[:-3].split(".")
                if len(parts) >= 2:
                    claimed.setdefault(parts[1], []).append(parts[0])
    except OSError:
        pass
    roles = {"RES-1": "战役", "RES-2": "论文", "RES-3": "验证",
             "RES-4": "基建", "OPS-M": "合并", "OPS-A": "审计"}
    rows = []
    for aid, role in roles.items():
        rows.append({
            "id": aid, "role": role,
            "alive": aid in live,
            "account": _agent_account(aid),
            "holding": sorted(claimed.get(aid, [])),
            "idle_min": board_mod.heartbeat_age(aid),
        })
    workers = sorted(w for w in live if w.startswith("W-"))
    return {"standing": rows, "workers": workers,
            "workers_holding": {w: sorted(claimed.get(w, [])) for w in workers}}


def _landed_gap():
    """板上说交付了几件，其中几件的分支还没进 master。

    这一格是今天最贵的一课的量化：把「板上 done」当成「已落地」计分，
    headline 就虚高了 11.5 个百分点。"""
    out = {"done": 0, "stuck": [], "flagged": 0}
    try:
        sys.path.insert(0, HERE)
        import board as board_mod
        out["done"] = len(board_mod.done_ids())
    except Exception:
        pass
    try:
        import mergequeue as mq
        stuck = mq.done_not_on_master()      # [{item, branch, state}, ...]
        out["stuck"] = [{"item": r.get("item"), "state": r.get("state")}
                        for r in stuck][:12]
        out["stuck_n"] = len(stuck)
    except Exception as exc:
        # 不知道就说不知道，不写 0。第一版这里写了 `sorted(stuck)`，
        # 而它返回的是一串 dict——排序当场抛异常，`stuck_n` 变成 None，
        # 页面于是显示「差额未知」。那次是对的：**它没有把失败画成零**。
        out["stuck_n"] = None
        out["stuck_error"] = type(exc).__name__
    try:
        ci = rel("monitor", "ci")
        out["flagged"] = len([f for f in os.listdir(ci)
                              if f.startswith("CONFLICT-")]) if os.path.isdir(ci) else 0
    except OSError:
        pass
    return out


def probe_accounts():
    """账号池：谁登录了、谁的窗口开着、下一个窗口几点重开。

    没有这条探针，一个「已经轮换过去了」的池子和一个「两个账号都没登录、
    全靠默认账号硬撑」的池子在页面上长得一模一样。"""
    try:
        sys.path.insert(0, HERE)
        import accounts as _acct
        rows = _acct.status()
    except Exception as exc:
        return {"status": "risk",
                "detail": "账号池读不出来（%s）——**这不等于没问题**。"
                          % type(exc).__name__}
    if not rows:
        return {"status": "partial",
                "detail": "未配置账号池；全部会话跑在机器的默认登录上。"}
    ready = [r for r in rows if r["login"] == "yes"]
    open_now = [r for r in ready if r["window"] == "open"]
    parts = []
    for r in rows:
        mark = {"yes": "已登录", "no": "**未登录**",
                "unknown": "**登录态未知**"}[r["login"]]
        win = {"open": "窗口开", "limited": "窗口关至 %s" % (r["limited_until"] or "?"),
               "unknown": "**窗口态未知**"}[r["window"]]
        parts.append("%s（%s）%s、%s，发车 %d 次、撞限 %d 次"
                     % (r["id"], r["label"], mark, win,
                        r["launches"], r["limits_seen"]))
    if not ready:
        return {"status": "risk",
                "detail": "；".join(parts) +
                          "　→ **一个账号都没登录**，轮换不会发生：撞限即全队停机。"
                          "登录方法见 monitor/ACCOUNTS.md。"}
    if not open_now:
        return {"status": "risk",
                "detail": "；".join(parts) + "　→ **所有已登录账号的窗口都关着**，"
                                             "这才是真 HOLD。"}
    return {"status": "green" if len(ready) >= 2 else "partial",
            "detail": "；".join(parts) +
                      ("　→ %d 个账号可用，撞限时会轮换而不是停机。" % len(open_now)
                       if len(ready) >= 2 else
                       "　→ 只有一个账号可用，撞限仍会整队停机。")}


def probe_orphan_commits():
    """有没有已完成的工作只存在于这一块磁盘上（S36）。

    `ci_merge` 枚举 `origin/agent/*`、拿 `origin/master` 判祖先
    （`ci_merge.py:450`/`:454`），所以**一条没推上去的分支对它不是红，是不存在**
    ——不是合并失败，是从来没进候选集合。此前舰队没有任何一处显示这件事：
    心跳的 note 是自报的散文，探针不读它，而板上那件活可能已经记成 done。
    Phase 4 的释出清单发布的是 master 上被跟踪的文件，所以没推上去的工作
    在释出时等于没做过。

    判据与三个值都在 `orphan_commits.py` 里（那里有完整推导）。这里只把它接进页面。
    `note` 是刻意的第四档：全部裁决完但工作仍只有一份拷贝——不是绿，
    也不该和「没人看过」长得一样。
    """
    try:
        sys.path.insert(0, HERE)
        import orphan_commits
        st = orphan_commits.status()
    except Exception as exc:                    # noqa: BLE001
        # 探针自己崩了**不是**绿。这条规则本仓库已经写过三遍
        # （crash-is-not-a-finding / 第三个值 / BOARD-QUERY-FAILED）。
        return {"status": "missing",
                "detail": "孤立提交普查跑不起来（%s: %s）；本轮无法断言"
                          "这块盘上没有只此一份的工作。"
                          % (type(exc).__name__, exc)}
    return {"status": st["status"], "detail": st["detail"]}


def probe_master_tree():
    """写入落在 master 的共享工作树上，而不是分支的 worktree 上（S39）。

    今天两例，都不报错：RES-2 自报一例，RES-4 在 S38 里 `cd` 没生效于整串命令，
    把 `monitor/scan.py` 写进了仓库根。更早还有一例已经进了历史——
    `worldgen/out/qc/t2-lock-fragile/candidates.jsonl` 最后一次被
    `1bd7eea2 "On master: autostash"` 碰过，扫走它的机制就写在提交标题里。

    为什么此前没有任何一处看它：master 的树**天天脏**（板、心跳、总线、ci
    有两百来条未提交状态），所以「树必须干净」这条规则等于天天红，也就等于没有。
    `collect_metrics` 确实记了 `m["dirty"]`，但全仓库没有一处读它，而且它不分辨
    ——判据必须按**路径**分，不能按人分：监控自己、`board.py`、`bus.py` 必须在
    那棵树上写。

    判据与三档（fleet-state / miswrite / unfiled）都在 `master_tree_guard.py`
    里，那里有完整推导。这里只把它接进页面。

    钩子那一半单独报：只观察不拦截的闸门，会变成 2026-07-30 漂移审计点名的
    「在 git 里是绿的、在生产里根本不存在」那七条之一。所以树干净但钩子没装
    时报 `partial`，而不是绿。
    """
    try:
        sys.path.insert(0, HERE)
        import master_tree_guard as mtg
        # Resolve the MAIN tree rather than judging whatever tree `scan.py`
        # happens to sit in. `ci_merge` copies the repo into a throwaway
        # worktree and runs `verify.py` from there, so `ROOT` is not always the
        # shared tree -- and "is there source sitting on master's tree" has one
        # answer no matter where you ask it from. `git worktree list` resolves
        # this from any worktree and covers `.claude/worktrees/` too (S36).
        main = mtg.main_worktree(ROOT)
        result = mtg.report(main)
        hooked = mtg.hook_installed(main)
    except Exception as exc:                    # noqa: BLE001
        # 探针自己崩了**不是**绿（crash-is-not-a-finding，本仓库第四遍）。
        return {"status": "missing",
                "detail": "共享工作树闸门跑不起来（%s: %s）；本轮无法断言"
                          "没有源码写在 master 的树上。"
                          % (type(exc).__name__, exc)}

    hook_note = "提交钩子已装" if hooked else (
        "提交钩子**未装**（`python monitor/master_tree_guard.py install-hook`）"
        "——本探针只观察，拦不住任何一次提交")

    # 三个数是**同一个总数的划分**，不是叠加：total = fleet + unfiled + miswrites。
    # 初版写成「%d 条脏路径全是舰队活状态，另有 %d 条未跟踪未归档」，把已经算在
    # total 里的琥珀又加了一遍，于是在实测上说出「153 条全是活状态，另有 9 条」
    # ——真相是 141/9/3。对抗性复核抓到的。
    if result["red"]:
        findings = (result["miswrite_paths"] + result["unfiled_paths"])[:4]
        names = "、".join(e["path"] for e in findings)
        n = result["miswrites"] + result["unfiled"]
        more = "" if n <= 4 else "等 %d 条" % n
        return {"status": "risk",
                "detail": "master 的共享树上有 **%d 条**不属于舰队活状态的脏路径"
                          "（被跟踪源文件 %d，未跟踪未归档 %d；另 %d 条是正常活状态，"
                          "共 %d）：%s%s。留在这里，一次 `git add -A` 会把它裹走，"
                          "一次 `git checkout --` 会把它抹掉，两个方向都不报错——"
                          "本仓已有一个提交就叫 “On master: autostash”。（%s）"
                          % (n, result["miswrites"], result["unfiled"],
                             result["fleet_state"], result["total"],
                             names, more, hook_note)}

    if not hooked:
        return {"status": "partial",
                "detail": "master 的共享树上没有误写：%d 条脏路径全部是舰队活状态。"
                          "但%s。" % (result["total"], hook_note)}

    return {"status": "green",
            "detail": "master 的共享树干净：%d 条脏路径全部是舰队活状态，"
                      "%s。" % (result["total"], hook_note)}


PROBES = {
    "accounts": probe_accounts,
    "standing": probe_standing,
    "master_tree": probe_master_tree,
    "credential_hygiene": probe_credential_hygiene,
    "needs_human": probe_needs_human,
    "offline_done": lambda: _offline_done(),
    "spend": lambda: _spend_watch(),
    "self_driving": lambda: _self_driving(),
    "bus": lambda: _bus_probe(),
    "supply": lambda: _supply(),
    "spec_freshness": probe_spec_freshness,
    "verify_gates": probe_verify_gates,
    "disk_headroom": probe_disk_headroom,
    "clock_sanity": probe_clock_sanity,
    "merge_queue": _merge_queue_probe,
    "scheduled_tasks": probe_scheduled_tasks,
    "append_only": probe_append_only,
    "orphan_commits": probe_orphan_commits,
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
    # S30: an unanswered `git status` used to render as 「工作树干净」. It is
    # now `None`, and the page says it does not know rather than showing an
    # empty list that looks exactly like a clean tree.
    status = git_or_none("status", "--porcelain")
    m["dirty_known"] = status is not None
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
                             text=True, encoding="utf-8",
                             errors="replace").stdout
        # tasklist 说的是 GBK。PYTHONIOENCODING=utf-8 一设，解码就在
        # reader 线程里炸掉——而线程里的异常不会往上抛，它只是让
        # .stdout 变成 None，调用点于是把 None 当输出读。
        # 闸门报的那句 "argument of type NoneType is not iterable"
        # 整条链就在这里（2026-07-29）。
        return str(pidnum) in (out or "")

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
    # S30: the page had no doctype and no charset while being full of Chinese,
    # and rendered only because browsers guess UTF-8 correctly. This branch
    # added more user-facing Chinese and a script; both inherit that guess.
    A('<!doctype html><meta charset="utf-8">')
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
    A('</div></div>')
    # S30: the timestamp above is what the backend *claims*; this row is what
    # the browser can *check*. A stale page and a healthy quiet one used to be
    # the same picture.
    A('<div class="freshrow"><span class="ago" data-since="%d" data-stale="%d" '
      'data-label="本页数据：">本页数据：年龄由浏览器计算（未启用脚本时不可用）'
      '</span></div>'
      % (int(state.get("generated_epoch") or 0),
         int(state.get("stale_after_s") or stale_after_s())))
    A('</header>')

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
    A(FRESH_JS)
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
/* S30: `missing` had no rule at all, so the one verdict this change exists to
   make visible rendered flatter than the green it replaces -- 「没检查成」
   would have been quieter on the page than 「检查过了，很干净」. */
.conflict.missing{border-left:4px dashed var(--missing);background:var(--missingbg)}
.conflict.partial{border-left:4px solid var(--partial)}

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

/* ---- S30: 数据年龄，以及扫描失败页 ----
   三态而非两态。新鲜是灰的（无需注意），陈旧是红的（后端可能已经挂了），
   **读不出生成时刻是灰的**——与「缺失」同色，因为不知道就是不知道，
   把它涂红等于把一次读取失败谎报成一次扫描失败。 */
.freshrow{margin:16px 0 0;font-size:13px}
.ago{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12.5px}
.ago.fresh{color:var(--mut)}
.ago.stale{display:inline-block;background:var(--riskbg);color:var(--risk);
  border:1px solid var(--risk);border-radius:9px;padding:8px 14px;font-weight:700}
.ago.unknown{display:inline-block;background:var(--missingbg);color:var(--missing);
  border-radius:9px;padding:8px 14px}
.scanfail{background:var(--riskbg);border:1px solid var(--risk);
  border-left:6px solid var(--risk);border-radius:11px;padding:22px 26px}
.scanfail h1{color:var(--risk)}
.scanfail .lead{margin:8px 0 0;font-size:14.5px;max-width:70ch}
.tb{margin:0;padding:12px 14px;background:var(--missingbg);border-radius:8px;
  overflow-x:auto;font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12px;
  line-height:1.5;white-space:pre-wrap;word-break:break-word}
</style>"""


# The first JavaScript this page has ever carried, and it is here for one
# reason: 渲染端不该无条件相信后端。`index.html` is a static file opened over
# `file://`, so it cannot re-fetch anything -- but the generation instant is
# baked in, and the browser owns a clock, which is enough to notice that the
# backend stopped writing. Without this, a dead scan and a quiet repository are
# the same page.
FRESH_JS = """<script>
(function(){
  /* index.html carries no meta-refresh unless --watch is used, so an open tab
     never re-reads the file. Without this, the widget would be measuring the
     age of the DOM rather than the age of the data, and any tab left open past
     the threshold would show 「扫描可能已经挂了」 about a perfectly healthy
     scan -- a false red, which is the same disease pointed the other way.
     So: before believing the page is stale, reload once to find out whether
     the file on disk moved. Self-limiting -- the reload resets loadedAt, so
     this fires at most once per staleness window, and a genuinely dead scan
     still lands on the red banner right after. */
  var loadedAt = Math.floor(Date.now()/1000);
  function human(s){
    if(s < 90) return s + " 秒";
    if(s < 5400) return Math.round(s/60) + " 分钟";
    if(s < 172800) return (s/3600).toFixed(1) + " 小时";
    return (s/86400).toFixed(1) + " 天";
  }
  function paint(){
    var now = Math.floor(Date.now()/1000);
    var nodes = document.querySelectorAll(".ago");
    for(var i=0;i<nodes.length;i++){
      var el = nodes[i];
      var t = parseInt(el.getAttribute("data-since"), 10);
      var stale = parseInt(el.getAttribute("data-stale"), 10);
      var label = el.getAttribute("data-label") || "";
      if(!isFinite(t) || t <= 0){
        el.className = "ago unknown";
        el.textContent = label + "年龄未知：这一页没有带上生成时刻。未知不写成 0。";
        continue;
      }
      var age = now - t;
      if(age < -120){
        el.className = "ago unknown";
        el.textContent = label + "生成时刻在未来 " + human(-age)
          + "，本机时钟与生成时不一致，年龄不可信。";
        continue;
      }
      if(age < 0) age = 0;
      if(isFinite(stale) && stale > 0 && age >= stale){
        if(now - loadedAt >= stale && typeof location !== "undefined"
           && location.reload){
          /* This tab has itself been open longer than the window, so the age
             may be the tab's and not the data's. Re-read the file before
             accusing the backend. */
          location.reload();
          return;
        }
        el.className = "ago stale";
        el.textContent = label + "这份数据是 " + human(age) + "前的，"
          + "已超过两个扫描周期（" + human(stale) + "）——扫描可能已经挂了，"
          + "不要把它当作现况读。";
      }else{
        el.className = "ago fresh";
        el.textContent = label + human(age) + "前";
      }
    }
  }
  paint();
  setInterval(paint, 15000);
})();
</script>"""


# ---------------------------------------------------------------- main

# How good a verdict is, worst first. Only used to tell an upgrade from a
# downgrade -- nothing here ranks `unprobed`, which is not a verdict.
_VERDICT_RANK = {"risk": 0, "missing": 1, "amber": 2, "partial": 3, "green": 4}


def _reconcile(item, probe_result, overrides):
    """Combine a hand-written status with its probe's, and record the disagreement.

    The old rule was `probe wins unless the hand-written value is risk`, applied
    silently. That let a probe covering *part* of an item promote the whole item:
    `p1-seal-test` is the conjunction "no credential inside the arm" AND "egress
    that bypasses the two proxies must fail", its hand-written status is
    `partial` with a note saying the red-team surface is unverified, and
    `credential_hygiene` -- which never attempts an egress bypass -- returned
    green and won. That is a green cell on the board for a test nobody ran.

    So: a probe may always **downgrade** (evidence of a problem beats optimism),
    but it may only **upgrade** when it covers the whole item. Partial coverage
    is declared per item by `probe_scope: "partial"`, because only the item's
    author knows what the probe left out.

    Either way the disagreement is recorded rather than resolved in silence --
    the old override left no trace that a hand-written verdict had been replaced.
    """
    hand, probed = item["status"], probe_result["status"]
    if hand == "risk":
        keep, why = hand, "hand-written risk is never overridden by a probe"
    elif _VERDICT_RANK.get(probed, 9) < _VERDICT_RANK.get(hand, 9):
        keep, why = probed, "probe downgraded"
    elif item.get("probe_scope") == "partial":
        keep, why = hand, ("probe covers only part of this item, so it may not "
                           "upgrade it")
    else:
        keep, why = probed, "probe upgraded"
    if keep != probed or hand != probed:
        overrides.append({"item": item["id"], "probe": item["probe"],
                          "hand": hand, "probe_said": probed,
                          "kept": keep, "why": why})
    return keep


def build(with_tests=False, out_dir=None):
    if spec is None:
        # Re-raised here rather than at import, so `main()`'s failure exit is
        # already installed and turns this into a red page instead of a
        # traceback in a gitignored log. Re-raising the original object keeps
        # its traceback, so the page still names the line in `spec.py`.
        raise _SPEC_IMPORT_ERROR
    metrics = collect_metrics(with_tests)

    probe_results = {name: fn() for name, fn in PROBES.items()}


    phases = []
    p1_green = p1_total = p1_unprobed = 0
    overrides = []
    for ph in spec.PHASES:
        items = []
        for it in ph["items"]:
            st, note = it["status"], it["note"]
            probed = bool(it.get("probe") and it["probe"] in probe_results)
            if probed:
                pr = probe_results[it["probe"]]
                st = _reconcile(it, pr, overrides)
                note = note + "  〔本次扫描：" + pr["detail"] + "〕"
            else:
                # S26 item 3: an item nothing checks must say so. Left silent,
                # a hand-written `green` with no probe behind it is
                # indistinguishable on the board from one a machine confirmed.
                note = note + "  〔无探针：本项无任何机器检查，状态为人工断言〕"
            items.append(dict(it, _status=st, _note=note, _probed=probed))
        counts = {}
        for i in items:
            counts[i["_status"]] = counts.get(i["_status"], 0) + 1
        if ph["id"] == "p1":
            p1_total = len(items)
            p1_green = counts.get("green", 0)
            p1_unprobed = sum(1 for i in items if not i["_probed"])
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
        # S30. `generated_at` keeps its exact historical shape -- `render()` and
        # `app.html` both slice it `[5:16]`, and `history.jsonl` reuses it as
        # `ts`. The epoch and the UTC form are added *beside* it, because a
        # local naive string cannot be turned into an age by a browser that may
        # not share this machine's timezone.
        **_stamps(),
        # Present and true on every successful scan, so `false` is a claim the
        # failure exit makes rather than a value a reader has to infer from an
        # absence. `verify.py` requires the field, so it cannot quietly vanish.
        "scan_ok": True,
        "stale_after_s": stale_after_s(),
        "metrics": metrics,
        "phases": phases,
        "sections": sections,
        "findings": sorted(spec.FINDINGS,
                           key=lambda f: ["blocking", "high", "medium", "low",
                                          "info"].index(f["severity"])),
        "p1_green": p1_green, "p1_total": p1_total,
        # S26: the headline was one number over a list length, with no
        # record of which items a machine had actually checked. 11 of the
        # 16 have no probe at all, and several of those are hand-written
        # green -- indistinguishable on the board from a confirmed one.
        "p1_unprobed": p1_unprobed,
        "verdict_overrides": overrides,

        "eng_green": sum(1 for e in spec.ENGINES if e["status"] == "green"),
        "con_green": sum(1 for c in spec.CONSTRAINTS if c["status"] == "green"),
        "blocking_findings": sum(1 for f in spec.FINDINGS if f["severity"] == "blocking"),
        "probes": probe_results,
        "tickets": load_prompts(),
        # 页面渲染，扫描计算——这条分工是本仓的既有契约。下面三块是
        # 2026-07-29 舰队改制之后页面需要而旧 state 里没有的：
        # 账号池的**结构化**行（不是一句散文）、每个 agent 跑在哪个账号上、
        # 以及「板上 done」与「进了 master」的差额。最后一条是今天最重要的
        # 新区分：把前者当成后者，正是 headline 虚高 11.5 个百分点的机制。
        "accounts": _accounts_rows(),
        "fleet": _fleet_rows(),
        "landed": _landed_gap(),
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
    # S28 的孪生缺陷：和 `_supply()` 同一个前缀匹配，同样把 reserved（以及现在的
    # territory-blocked）段数进「可领」。前端拿这个数当可领件数显示。
    try:
        sys.path.insert(0, HERE)
        import board as _bmod
        _available = len(_bmod.candidates())
    except Exception:
        _available = None       # 前端据此显示「不知道」，而不是显示一个漂亮的数
    state["board"] = {
        "available": _available,
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


# ------------------------------------------------------------- failure exit
#
# S30. A crashed scan used to be indistinguishable from a quiet one. `build()`
# writes `index.html` and `state.json` at the very end, so any exception left
# both files untouched; `refresh.cmd` appended the traceback to
# `monitor/refresh.log`, which is gitignored, and `reflex.py` threw the return
# code away. The page therefore kept showing the last successful scan with a
# slightly older timestamp -- 「扫描挂了」and「什么都没变」rendered identically.
# That is this repository's catalogued failure shape, grown on the dashboard
# that is supposed to catch it everywhere else.
#
# Two placement decisions, both load-bearing:
#
#   * the exit lives in `main()`, **not** inside `build()`. `verify.py:_real_run`
#     turns a raising `build()` into a red gate; a `build()` that caught its own
#     crash and returned normally would silently take that red away, which is
#     the same defect one level up.
#   * the failure page is rendered by `render_failure()`, not by `render()`.
#     `render()` subscripts nine keys of a successful state (including
#     `probes["conflict_scan"]` and `loop_stats[2]`), so feeding it a stub would
#     make the failure exit itself the second crash -- and that one has no
#     handler.

#: Scheduled Task `TheoriaDashboard` reruns the scan every 10 minutes.
SCAN_PERIOD_S = 600
#: ...so a page older than two of those has almost certainly missed a scan.
STALE_CYCLES = 2


def stale_after_s():
    """Seconds after which the page must stop believing its own numbers.

    `--watch N` makes the real period N, so the threshold follows it rather
    than staying pinned to the scheduled-task cadence.

    `getattr` rather than `build.refresh`: this runs on the failure path, where
    the reason we are here may well be that something about the module is not
    what it should be. A threshold helper that raises would take the failure
    exit down with it and hand back the silence it exists to prevent.
    """
    return STALE_CYCLES * int(getattr(build, "refresh", None) or SCAN_PERIOD_S)


def _say(text, stream=None):
    """Write `text` to a console that may not be able to represent it.

    The host console is cp936. Anything that reached us through
    `errors="replace"` carries U+FFFD, which cp936 cannot encode, so an
    unguarded `print` of a traceback raises `UnicodeEncodeError` -- and on the
    failure path that turns a reported failure back into an unreported one.
    Never raises; a mangled line beats a lost one.
    """
    stream = stream or sys.stdout
    try:
        stream.write(text if text.endswith("\n") else text + "\n")
    except Exception:
        try:
            enc = getattr(stream, "encoding", None) or "ascii"
            stream.write(text.encode(enc, "replace").decode(enc, "replace")
                         + "\n")
        except Exception:
            pass


def _stamps(now=None):
    """The three forms of one instant.

    `generated_at` keeps its historical shape (local, naive, `%Y-%m-%d
    %H:%M:%S`) because `render()` and `app.html` both slice it as `[5:16]` and
    `history.jsonl` reuses it as `ts`. The age arithmetic needs an unambiguous
    instant, so the epoch is added beside it instead of replacing it.
    """
    now = time.time() if now is None else now
    return {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now)),
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
        "generated_epoch": int(now),
    }


def _prior_success(out_dir=None):
    """When the last scan that actually finished, finished.

    Returns `(iso, epoch)`, either of which may be `None`. Unknown stays
    `None` and is rendered as 「未知」: a state.json we cannot read is not the
    same claim as "there has never been a successful scan", and this repository
    has a standing rule against collapsing the two.
    """
    path = os.path.join(out_dir or HERE, "state.json")
    try:
        with open(path, encoding="utf-8") as fh:
            prev = json.load(fh)
    except Exception:
        return None, None
    if not isinstance(prev, dict):
        return None, None
    if prev.get("scan_ok") is False:
        # The predecessor was itself a failure page; it is carrying the stamp
        # of the last *success*, so take that and do not restart the clock.
        return prev.get("last_success_at"), prev.get("last_success_epoch")
    return prev.get("generated_at"), prev.get("generated_epoch")


def _write_atomic(path, text):
    """tmp + os.replace, the idiom `accounts.py:98` argues for.

    A failure writer that can leave a half-written file behind would replace
    one invisible failure with a louder one.
    """
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    os.replace(tmp, path)


def failure_state(exc, tb_text, out_dir=None, now=None):
    """The machine-readable form of 「本次扫描失败」.

    Deliberately carries **no** payload from the previous run. Copying the old
    `metrics` / `phases` forward would hand every consumer stale numbers under
    a fresh timestamp, which is the exact defect this exit exists to remove.
    What survives is the one fact a reader needs: when the data they can no
    longer see was last true.
    """
    lines = [ln for ln in (tb_text or "").strip().splitlines() if ln.strip()]
    frames = [ln.strip() for ln in lines if ln.strip().startswith("File \"")]
    last_at, last_epoch = _prior_success(out_dir)
    state = dict(_stamps(now))
    state.update({
        "scan_ok": False,
        "stale_after_s": stale_after_s(),
        "scan_error": {
            "type": type(exc).__name__,
            "message": str(exc)[:2000],
            # The literal first line of a traceback is always the useless
            # "Traceback (most recent call last):", so what gets promoted here
            # is the innermost frame and the raise line -- the two lines a
            # reader actually needs to place the crash.
            "where": frames[-1] if frames else "unknown",
            "raised": lines[-1] if lines else "",
            "traceback": (tb_text or "").strip()[-8000:],
        },
        "last_success_at": last_at,
        "last_success_epoch": last_epoch,
        # Missing is not zero: if we cannot read the predecessor we say so
        # rather than reporting an age of 0 or a success at the epoch.
        "last_success_known": last_at is not None,
    })
    # Guarded conversion: `json.load` happily accepts a bare `NaN`, and
    # `int(nan)` raises. An arithmetic detail that can take down the failure
    # exit is not a detail -- unknown is the correct answer for a
    # `generated_epoch` we cannot subtract, and `bool` is excluded because
    # `isinstance(True, int)` would otherwise date the last success to 1970.
    try:
        if isinstance(last_epoch, bool):
            raise TypeError("bool is not an epoch")
        state["stale_since_s"] = max(
            0, state["generated_epoch"] - int(last_epoch))
    except Exception:                           # noqa: BLE001 -- unknown
        state["stale_since_s"] = None
    return state


def render_failure(state):
    """A whole page whose only message is that there is no data.

    Self-contained on purpose: it borrows `STYLE` and nothing else, so it still
    renders when the crash was inside a probe, inside `spec`, or inside
    `render()` itself.
    """
    err = state["scan_error"]
    last_at = state.get("last_success_at")
    last_epoch = state.get("last_success_epoch")
    # `isinstance(True, int)` is True, and a bool epoch would render as 1970.
    known_epoch = (isinstance(last_epoch, (int, float))
                   and not isinstance(last_epoch, bool)
                   and last_epoch > 0)
    parts = []
    A = parts.append
    A('<!doctype html><meta charset="utf-8">')
    A('<title>Theoria · 扫描失败</title>')
    if getattr(build, "refresh", None):
        A('<meta http-equiv="refresh" content="%d">' % build.refresh)
    A(STYLE)
    A('<header><div class="scanfail">'
      '<h1>扫描失败</h1>'
      '<p class="lead">这一页没有数据。上一次扫描崩了，'
      '<b>所以这里不显示旧数字</b>——旧数字配上新时间戳，'
      '和「一切正常」在页面上长得一模一样，那正是这一页要拆掉的东西。</p>'
      '<p class="lead">最后一次成功扫描：<b>%s</b>%s</p>'
      '</div></header>'
      % (esc(str(last_at)) if last_at else "未知",
         # Three cases, not two. The timestamp and the age come from different
         # fields, so a predecessor written by pre-S30 code has the former and
         # not the latter -- and the first crash after this ships is exactly
         # that case. Saying 「不知道是什么时候」 next to a printed timestamp
         # would be the page contradicting itself on its own headline.
         ('　<span class="ago" data-since="%d" data-stale="%d">'
          '（正在计算已过去多久）</span>' % (int(last_epoch), stale_after_s()))
         if known_epoch else
         ('　<span class="note">（这份记录来自 S30 之前的扫描，只有时刻没有'
          '机器可读的纪元，所以算不出过去了多久）</span>' if last_at else
          '　<span class="note">（读不到上一份 state.json，'
          '所以连这个都不知道——不知道不写成 0）</span>')))
    A('<main><section><h2>崩在哪里</h2>')
    A('<table class="wide"><tbody>')
    for k, v in [("异常", "%s: %s" % (err["type"], err["message"])),
                 ("位置", err["where"]),
                 ("抛出", err["raised"]),
                 ("本次尝试", state["generated_at_utc"])]:
        A('<tr><th>%s</th><td><code>%s</code></td></tr>' % (esc(k), esc(str(v))))
    A('</tbody></table>')
    # `html.escape`, NOT `esc()`: `esc()` replaces every newline with a space
    # (it exists for one-line table cells), which flattened the whole traceback
    # into one unreadable paragraph and made the `white-space:pre-wrap` on
    # `.tb` decorative. The traceback is the single most useful thing on this
    # page; it is the one string that must keep its shape.
    A('<details class="fold" open><summary>完整 traceback</summary>'
      '<div><pre class="tb">%s</pre></div></details>'
      % html.escape(err["traceback"]))
    A('</section><section><h2>怎么办</h2>'
      '<div class="needs"><b>重跑一次，看它是否可复现</b>'
      '<p><code>python monitor/scan.py</code>。这次崩溃已追加进 '
      '<code>monitor/crashes.jsonl</code>（被 git 跟踪，'
      '不像 <code>monitor/refresh.log</code> 那样会被下一次清理带走）；'
      '历史崩溃的分类见 <code>monitor/CRASHES.md</code>。</p></div>'
      '</section>')
    A('<footer><p>由 <code>monitor/scan.py</code> 的失败出口生成（S30）。'
      '扫描成功后这一页会被真正的盘面覆盖。</p></footer>')
    A('</main>')
    A(FRESH_JS)
    return "\n".join(parts)


def record_crash(state, out_dir=None):
    """Append the crash to a **tracked** ledger.

    `refresh.log` held the only record of 55 crashes and is gitignored, so the
    record was one `git clean` from gone. This file is committed; the traceback
    body is not written into it (that is what the page and the log are for) --
    one line per crash keeps it a ledger rather than a second log.
    """
    row = {
        "utc": state["generated_at_utc"],
        "type": state["scan_error"]["type"],
        "where": state["scan_error"]["where"],
        "message": state["scan_error"]["message"][:300],
        "last_success_at": state.get("last_success_at"),
    }
    path = os.path.join(out_dir or HERE, "crashes.jsonl")
    with open(path, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_failure(exc, tb_text, out_dir=None, now=None):
    """Write the failure state and the failure page; return the state.

    Every step is guarded, including the construction of the state itself --
    a failure exit that can raise hands the caller back exactly the silence it
    was built to prevent.

    **`state.json` is written before `index.html`**, and that order is
    load-bearing. Both writes are swallowed on error, so if only one lands it
    must be the one that fails safe: a red page beside a `scan_ok: true` state
    would leave `app.html` (which reads only the state) rendering the old
    dashboard as healthy. A failure state beside a stale page is the harmless
    direction of the same accident.

    The return value carries `written`, so the caller can report what actually
    reached the disk instead of announcing a red page it never managed to
    write.
    """
    target = out_dir or HERE
    try:
        state = failure_state(exc, tb_text, out_dir, now)
    except Exception as inner:                      # noqa: BLE001 -- last resort
        state = dict(_stamps(now), scan_ok=False, last_success_at=None,
                     last_success_epoch=None, last_success_known=False,
                     stale_since_s=None, stale_after_s=stale_after_s(),
                     scan_error={"type": type(exc).__name__,
                                 "message": str(exc)[:2000],
                                 "where": "unknown（构造失败状态时又崩了：%s）"
                                          % type(inner).__name__,
                                 "raised": "", "traceback": tb_text or ""})
    written = []

    def _try(name, fn):
        try:
            fn()
            written.append(name)
        except Exception:                           # noqa: BLE001 -- reported
            pass

    _try("state.json", lambda: _write_atomic(
        os.path.join(target, "state.json"),
        json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n"))

    def _page():
        try:
            body = render_failure(state)
        except Exception as inner:                  # noqa: BLE001 -- degraded
            body = ("<!doctype html><meta charset=\"utf-8\">"
                    "<title>Theoria · 扫描失败</title>"
                    "<h1>扫描失败</h1><p>渲染失败页时又崩了一次：%s: %s</p>"
                    "<pre>%s</pre>"
                    % (html.escape(type(inner).__name__), html.escape(str(inner)),
                       html.escape(state["scan_error"]["traceback"])))
        _write_atomic(os.path.join(target, "index.html"), body)

    _try("index.html", _page)
    _try("crashes.jsonl", lambda: record_crash(state, out_dir))
    state["written"] = written
    return state


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tests", action="store_true", help="also run both pytest suites")
    ap.add_argument("--watch", type=int, metavar="SECONDS", default=0,
                    help="rescan on this interval; the page auto-reloads itself")
    ap.add_argument("--out-dir", metavar="DIR", default=None,
                    help="write the artifacts here instead of into monitor/")
    args = ap.parse_args()
    if args.watch:
        build.refresh = max(args.watch, 15)
    state = None
    failed = 0
    while True:
        try:
            state = build(args.tests, out_dir=args.out_dir)
        except Exception as exc:                    # noqa: BLE001 -- reported
            import traceback
            tb = traceback.format_exc()
            fs = write_failure(exc, tb, out_dir=args.out_dir)
            failed += 1
            state = None
            # Reporting comes after the artifacts are on disk, and it is
            # wrapped, because printing is not safe here. The console is cp936
            # and a traceback decoded with `errors="replace"` carries U+FFFD,
            # which cp936 cannot encode -- this repository has already lost a
            # gate to exactly that, dying inside the loop that printed why it
            # had failed. A failure exit that crashes while announcing the
            # failure hands back the silence it just removed.
            _say(tb, stream=sys.stderr)
            # Report what actually landed. The first version of this line
            # announced 「index.html 已改写为红色失败页」 unconditionally,
            # while the writes beneath it were swallowed -- a claim about a
            # red page that a full disk would have made false, printed by the
            # very code whose thesis is that failures must not be silent.
            wrote = fs.get("written") or []
            _say("[%s] 扫描失败：%s — 已写出 %s%s；上次成功 %s"
                 % (fs["generated_at_utc"], fs["scan_error"]["type"],
                    "、".join(wrote) if wrote else "**什么都没写成**",
                    "" if "index.html" in wrote
                    else "（**页面没能改写，它还显示着上一轮**）",
                    fs.get("last_success_at") or "未知"))
        else:
            if state["p1_unprobed"]:
                print("    Phase 1: %d/%d 项无任何机器检查，其状态是人工断言"
                      % (state["p1_unprobed"], state["p1_total"]))
            for o in state["verdict_overrides"]:
                print("    裁决分歧 %s：手写 %s / 探针 %s → 取 %s（%s）"
                      % (o["item"], o["hand"], o["probe_said"], o["kept"], o["why"]))
            print("[%s] monitor/index.html written — Phase 1: %d/%d green"
                  % (state["generated_at"], state["p1_green"], state["p1_total"]))
        if not args.watch:
            break
        time.sleep(max(args.watch, 15))
    if state is None:
        # Non-zero so a caller can tell. `reflex.py` now checks this; before
        # S30 it discarded the return code and logged the cycle as `quiet`.
        return 1
    for name, pr in sorted(state["probes"].items()):
        print("  %-22s %-8s %s" % (name, pr["status"], pr["detail"][:110]))
    for f in state["findings"]:
        if f["severity"] in ("blocking", "high"):
            print("  [%s] %s — %s" % (f["severity"].upper(), f["id"], f["title"]))
    # Reached only when the last scan succeeded, so 0. An earlier draft
    # returned `1 if failed else 0`, which under a future `--watch --once`
    # would report a healthy board as a failed one and make `reflex.py` log
    # `SCAN FAILED` for a cycle that recovered.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
