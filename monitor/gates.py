"""What is a territory's completion gate, answered once for the whole rig.

`ci_merge` needs to know so it can run one before merging.  `scan.probe_verify_
gates` needs to know so it can report which territories have none.  Two
implementations of the same question drift, and this repository has already paid
for that twice — `ci_merge`'s hand-maintained `TEST_CMDS` table went stale while
509 tests sat unrun, and the hand-written repair got four of its seven entries
wrong in the same commit.  Its own comment draws the conclusion: *a table
maintained by hand is a claim about the tree that nothing checks against the
tree.  So: ask the tree.*  This module is where the tree gets asked.

## Three states, and the middle one is the point

    verify    the territory ships its own gate -- `verify.sh` or `verify.py`
    pytest    no gate, but it holds `test_*.py`, so the suite is the gate
    none      nothing to run

S13's root cause is that *"write a verify script"* was a self-discipline clause
in the ticket text, so ten territories went without one and nobody could see it:
a skipped gate and a passing gate were the same single MERGED line.  The fix is
not to write ten scripts — it is to make `none` **say so, every time, in the
log**, so an ungated merge is visible rather than silent.

## Why `verify` supersedes `pytest` rather than adding to it

Every gate in this repo already runs its own suite as its first stage
(`exam/verify.py`, `worldgen/verify.py`, `ablation-arm/verify.sh`).  Running
both would double the slowest part of a merge to re-check what the gate just
checked, and a merge rig that is slow gets bypassed.

## Gates under other names

`proxy/verify_spend.sh` is a gate and is not called `verify.sh`.  A matcher that
only knew the two canonical names would report `proxy` as ungated, which is
false and is exactly the sort of wrong-but-confident report that gets a probe
switched off.  So the search is by prefix, and what it found is named in the
record rather than reduced to a boolean.
"""

from __future__ import annotations

import os
import re
import shutil
import sys
from typing import Any, Dict, List, Optional, Sequence

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

#: Tried in order. The first that exists wins, so a territory can adopt the
#: canonical name later without changing anything here.
CANONICAL = ("verify.sh", "verify.py")

#: A file whose name starts with this and ends in `.sh`/`.py` counts as a gate
#: under a non-canonical name -- `proxy/verify_spend.sh`.
PREFIX = "verify"

#: Directories that are not territories: no code, nothing to gate.
NOT_TERRITORIES = {".git", ".worktrees", ".claude", ".toolchain", "__pycache__",
                   ".pytest_cache", ".vscode", ".idea",
                   # 2026-07-29: 某个 agent 在仓库根建了 `scratchpad/`（三个
                   # 一次性脚本，一个都没被 git 跟踪）。它不是领地——没有可交付物、
                   # 没有闸门要跑。**但它该被记成「不该存在」而不是「未设闸门」**：
                   # 按 CLAUDE.md，临时文件属于会话的 scratchpad 目录，不进仓库树。
                   "scratchpad"}


#: `bash` 在 PATH 上解析到的是 **WSL** 的 bash——另一个 Linux，`/mnt/c` 挂载、
#: 只有 python3、看不见 Windows 这边装的 numpy/scipy/pytest。仓库的 `.sh` 闸门
#: 写的是 Git Bash 的口径，所以这里显式指名，不听 PATH 的。
GIT_BASH_CANDIDATES = (
    r"C:\Program Files\Git\bin\bash.exe",
    r"C:\Program Files\Git\usr\bin\bash.exe",
    r"C:\Program Files (x86)\Git\bin\bash.exe",
)


def _bash() -> str:
    for cand in GIT_BASH_CANDIDATES:
        if os.path.isfile(cand):
            return cand
    return "bash"


def _runner(path: str) -> List[str]:
    if path.endswith(".py"):
        return [sys.executable, path]
    # 两个 bug 叠在同一行上，W-1620 只看见了第一个（2026-07-29）：
    #
    # (1) Windows 绝对路径交给 MSYS/WSL bash，反斜杠被当成转义吃掉：
    #     `C:\Users\...\verify.sh` → `C:Usersverify.sh`，报 No such file or
    #     directory，而 ci_merge 把它记成「verify gate red」。8 条已交付分支
    #     因此被判成验证失败，每 5 分钟重刷一次 flag。
    # (2) 但只修反斜杠会换来另一种红：PATH 上的 `bash` 是 WSL 的，
    #     那里 `python` 根本不存在（只有 python3），闸门第 14 行就 exec 失败。
    #     实测过才发现——**一个「一行修复」如果没被真跑过，它修的是报错文本，
    #     不是闸门。**
    #
    # 这一整类是**假红**：与今晚普查的假绿反向，但同样是工具的失败被写成了
    # 被检查对象的性质。假绿放过坏活，假红扣住好活，都在冒充判决。
    return [_bash(), path.replace("\\", "/")]


def gate_env(root: str) -> Dict[str, str]:
    """The environment a gate is entitled to assume.

    A `verify.py` that imports its own territory -- `from battery import
    freeze`, `from worldgen.qc import gate` -- is run with `cwd` *inside* that
    territory, so the repository root is not on `sys.path` and the import dies
    before the gate does anything.  Two branches hit this the same night in two
    different territories (`v5-battery-freeze`, `v12-worldgen-gate-deaf`, and
    `s14` again in `a0-spike`), which is the signature of a missing contract
    rather than three mistakes: the runner never said where a gate runs from,
    so every author guessed, and the ones who guessed `python -m` from the root
    were failed by the ones who wrote the runner.

    So the contract is stated here and provided here: **a gate runs with `cwd`
    at its own territory and the repository root importable.**  It is the same
    lesson as the bash line above -- a gate that cannot start is reported as
    the territory failing its own check, which is a lie in the direction that
    looks like a verdict.
    """
    env = dict(os.environ)
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = root + (os.pathsep + existing if existing else "")
    # Gitignored evidence payloads never reach a throwaway worktree, so a
    # suite that keys its skips on their presence fails where it means to
    # skip -- A19's false-red baseline (2026-08-01), and the same disease
    # let this runner manufacture a BASE RED for baseline-arms on
    # 2026-08-04 while the main checkout ran 559/0 green.  Point the
    # territories' own documented escape hatches (schema_column.resolve_root,
    # battery/STATUS.md) at the launching checkout's copies unless the
    # caller already chose.
    main_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    schema = os.path.join(main_root, "baseline-arms", "schema_traces")
    if "THEORIA_SCHEMA_TRACES" not in env and os.path.isdir(schema):
        env["THEORIA_SCHEMA_TRACES"] = schema
    ba = os.path.join(main_root, "baseline-arms")
    if "THEORIA_BASELINE_ARMS" not in env and os.path.isdir(ba):
        env["THEORIA_BASELINE_ARMS"] = ba
    return env


def find_gate(root: str, directory: str) -> Optional[Dict[str, Any]]:
    """The territory's own gate, or None.  Canonical names first."""
    base = os.path.join(root, directory)
    if not os.path.isdir(base):
        return None
    for name in CANONICAL:
        path = os.path.join(base, name)
        if os.path.isfile(path):
            return {"name": name, "path": path, "canonical": True,
                    "cmd": _runner(path)}
    for name in sorted(os.listdir(base)):
        if (name.startswith(PREFIX) and name.endswith((".sh", ".py"))
                and os.path.isfile(os.path.join(base, name))):
            path = os.path.join(base, name)
            return {"name": name, "path": path, "canonical": False,
                    "cmd": _runner(path)}
    return None


# A gate is only an instrument if something makes it go red on purpose. S13's
# audit turned that into a standing requirement, and this is its executable
# form: the gate *declares* its negative sample, on a line of its own.
#
#     # negative-sample: monitor/tests/test_probes_injection.py
#
# Declared rather than sniffed. Guessing from filenames -- anything matching
# test_*negative*, say -- would let a gate acquire a negative sample by someone
# naming an unrelated file well, and would miss every real one that is named
# something else. A declaration is a claim its author can be held to, and the
# path is checked to exist so the claim cannot be to a file that never landed.
NEGATIVE_SAMPLE = re.compile(r"negative-sample:\s*(\S+)")


def negative_sample_of(root: str, gate_path: str) -> Optional[Dict[str, Any]]:
    """The negative sample a gate script declares, if any, and whether it exists."""
    try:
        with open(gate_path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except Exception:
        return None
    m = NEGATIVE_SAMPLE.search(text)
    if not m:
        return None
    declared = m.group(1)
    # Accept `path::test_name`; only the path half is checkable here.
    path_part = declared.split("::", 1)[0]
    return {"declared": declared,
            "exists": os.path.isfile(os.path.join(root, path_part))}


def has_tests(root: str, directory: str) -> bool:
    base = os.path.join(root, directory)
    if not os.path.isdir(base):
        return False
    for dirpath, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d not in NOT_TERRITORIES]
        for name in files:
            if name.startswith("test_") and name.endswith(".py"):
                return True
    return False


def gate_for(root: str, directory: str) -> Dict[str, Any]:
    """`{kind, cmd, name, why}` for one territory.  `kind` is the whole answer.

    Never raises on a directory that does not exist: a branch can delete one,
    and a merge rig that crashed on that would be worse than one that merged it.
    """
    gate = find_gate(root, directory)
    if gate:
        ns = negative_sample_of(root, gate["path"])
        # `decorative` is not "failing" -- the gate may check plenty. It is
        # "nobody has shown this can fail", which is the state a gate installed
        # and never exercised is in, and is indistinguishable from a working one
        # for exactly as long as nothing is broken.
        decorative = not (ns and ns["exists"])
        return {"kind": "verify", "cmd": gate["cmd"], "name": gate["name"],
                "canonical": gate["canonical"],
                "negative_sample": ns, "decorative": decorative,
                "why": "the territory ships its own completion gate"
                       + ("" if not decorative else
                          "; no negative sample declared, so nothing has shown "
                          "it can go red")}
    if has_tests(root, directory):
        return {"kind": "pytest",
                "cmd": [sys.executable, "-m", "pytest", "-q", "-x"],
                "name": None, "canonical": None,
                "negative_sample": None, "decorative": True,
                "why": "no verify script; the test suite is the gate"}
    return {"kind": "none", "cmd": None, "name": None, "canonical": None,
            "negative_sample": None, "decorative": True,
            "why": "no verify script and no test_*.py -- this territory merges "
                   "with nothing checking it"}


def territories(root: str = ROOT) -> List[str]:
    return sorted(d for d in os.listdir(root)
                  if os.path.isdir(os.path.join(root, d))
                  and d not in NOT_TERRITORIES
                  and not d.startswith("."))


def survey(root: str = ROOT,
           names: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    """Every territory and its gate state.  The probe's raw material."""
    rows = {}
    for name in (names or territories(root)):
        rows[name] = gate_for(root, name)
    by_kind: Dict[str, List[str]] = {"verify": [], "pytest": [], "none": []}
    for name, row in sorted(rows.items()):
        by_kind[row["kind"]].append(name)
    return {
        "root": root,
        "rows": rows,
        "gated": by_kind["verify"],
        "tests_only": by_kind["pytest"],
        "ungated": by_kind["none"],
        "non_canonical": sorted(n for n, r in rows.items()
                                if r["kind"] == "verify" and not r["canonical"]),
        # Gates that exist and have never been shown to fail. Reported beside
        # `gated`, because "19 gated" and "19 gates known to work" are different
        # claims and the survey only ever supported the first.
        "decorative": sorted(n for n, r in rows.items()
                             if r["kind"] == "verify" and r["decorative"]),
        "n_territories": len(rows),
    }


def describe(row: Dict[str, Any], directory: str) -> str:
    """One line for `merge.log`.  An ungated merge has to be *readable*."""
    if row["kind"] == "verify":
        return "verify:%s(%s)" % (directory, row["name"])
    if row["kind"] == "pytest":
        return "pytest:%s" % directory
    return "UNGATED:%s" % directory


# --------------------------------------------------------------- running one
#
# S13 answered "what is this territory's gate".  S14 adds "run it, and never
# collapse *did not run* into *passed*" -- the shape shared by three of the four
# silent failures caught on 2026-07-28.  Seven outcomes, and only three of them
# let a merge through:
#
#     ok        the gate ran and exited 0
#     red       the gate ran and exited non-zero
#     broken    the gate exists but could not run -- no interpreter, timed out,
#               or pytest collected nothing.  NOT a pass.
#     dirty     the gate ran green but dropped *new* files into the tree.
#     drift     the gate ran green but regenerated *tracked* files differently.
#               Reported, not blocking -- see below.
#     absent    kind == "none".  Allowed, never silent.
#     unknown   the territory is not on the tree at all.
#
# `dirty` and `drift` are split because they have different owners.  A gate that
# drops a new scratch file into the tree it is checking is defective in itself
# -- ablation-arm's first verify.sh did exactly that and turned the arm's own
# read-only test red.  A gate that rewrites a *tracked* artefact is saying
# something else: the committed artefact is no longer what the code produces.
# That belongs to the territory, not to whichever branch happens to be merging,
# and both gates that predate S14 do it.  Blocking every pending branch on a
# pre-existing condition is how a check gets switched off the next day, so drift
# is logged by name and merges proceed; `--strict` fails on it for the owner.

NO_TESTS_COLLECTED = 5          # pytest's exit code for "found nothing to run"
DEFAULT_TIMEOUT = 1800

SEVERITY = {"ok": 0, "absent": 1, "unknown": 2, "drift": 3,
            "dirty": 4, "broken": 5, "red": 6}
PASSING = {"ok", "absent", "unknown", "drift"}
STRICT_PASSING = {"ok", "absent", "unknown"}

# Interpreter scratch, not gate droppings.  Any Python check creates these, so
# counting them would paint every gated territory dirty on its first run and the
# signal would be discarded inside a day.  The list stays short on purpose: it
# names caches the interpreter owns, and nothing a territory produces.
EPHEMERAL = ("__pycache__/", ".pytest_cache/", ".mypy_cache/", ".ruff_cache/")


def sh(args, cwd, timeout=DEFAULT_TIMEOUT):
    """Run a child process and decode its output without lying about it.

    `text=True` alone decodes with the host's locale encoding, which on the
    Windows box this fleet runs on is cp936.  A child that prints UTF-8 then
    either mojibakes or raises UnicodeDecodeError mid-check -- and a check that
    dies while decoding is a check that did not run.  That exact mismatch
    reported eight live workers as dead on 2026-07-28.
    """
    import subprocess
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout)


def _ephemeral(path: str) -> bool:
    p = path.replace("\\", "/")
    return p.endswith(".pyc") or any(seg in p for seg in EPHEMERAL)


def _dirt(root: str, territory: str):
    """`{path: porcelain code}` for the working tree under `territory`.

    Untracked files included -- a gate that drops artefacts into the territory
    it is checking is the defect S14 went looking for, and untracked droppings
    are its usual form.  The code is kept so the caller can tell a dropping
    (`??`) from a regenerated tracked artefact.
    """
    import subprocess
    r = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all",
                        "--", territory],
                       cwd=root, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        return None             # not a git checkout; caller degrades gracefully
    return {line[3:]: line[:2] for line in r.stdout.splitlines()
            if line.strip() and not _ephemeral(line[3:])}


def run(root: str, territory: str, timeout: int = DEFAULT_TIMEOUT,
        check_dirt: bool = True):
    """Run `territory`'s gate.  Returns `(outcome, detail)`.

    Discovery is `gate_for`, so this and the merge log and the probe cannot
    disagree about what a territory's gate is -- the drift that cost 509 unrun
    tests came from exactly two such implementations.
    """
    if not os.path.isdir(os.path.join(root, territory)):
        return "unknown", "%s is not on the tree" % territory

    row = gate_for(root, territory)
    if row["kind"] == "none":
        return "absent", row["why"]

    cmd = list(row["cmd"])
    if row["kind"] == "verify" and (row["name"] or "").endswith(".sh"):
        # `_runner` already picked an interpreter; the question here is whether
        # that interpreter exists.  It resolves to a literal "bash" only when
        # none of the Git Bash candidates were found, in which case it is a
        # bare PATH lookup that may resolve to nothing -- or, worse, to WSL's
        # bash, which is a different Linux with no `python`.
        #
        # The tempting behaviour -- skip it and merge on -- is the exact shape
        # this module exists to refuse.  A gate that cannot start is `broken`,
        # never a pass, and never the territory's fault: reporting it as "red"
        # is what put eight delivered branches in a five-minute reflag loop.
        runner = cmd[0]
        if runner == "bash" and not shutil.which("bash"):
            return "broken", ("%s/%s is a shell script and no bash could be "
                              "found" % (territory, row["name"]))
        if runner != "bash" and not os.path.isfile(runner):
            return "broken", ("%s/%s needs %s, which is not on this machine"
                              % (territory, row["name"], runner))

    before = _dirt(root, territory) if check_dirt else None
    cwd = os.path.join(root, territory)
    try:
        r = sh(cmd, cwd=cwd, timeout=timeout)
    except Exception as exc:                       # includes TimeoutExpired
        return "broken", "%s could not run: %s" % (describe(row, territory), exc)

    if row["kind"] == "pytest" and r.returncode == NO_TESTS_COLLECTED:
        # test_*.py exist and pytest still found nothing, so the configuration
        # points elsewhere.  Read as green this would be the fifth time this
        # repo mistook a check that could not run for a check that passed.
        return "broken", ("%s holds test_*.py but pytest collected nothing "
                          "(testpaths misconfigured)\n%s"
                          % (territory, (r.stdout + r.stderr)[-2000:]))
    if r.returncode != 0:
        return "red", ("%s exited %d\n%s"
                       % (describe(row, territory), r.returncode,
                          (r.stdout + r.stderr)[-3000:]))

    if check_dirt and before is not None:
        after = _dirt(root, territory) or {}
        changed = sorted(p for p, code in after.items() if before.get(p) != code)
        dropped = [p for p in changed if after[p].strip() == "??"]
        if dropped:
            return "dirty", ("the gate dropped %d new file(s) into the working "
                             "tree: %s" % (len(dropped), ", ".join(dropped[:8])))
        if changed:
            return "drift", ("the gate regenerated %d tracked file(s) with "
                             "different content: %s"
                             % (len(changed), ", ".join(changed[:8])))

    return "ok", describe(row, territory)


def main(argv: Optional[List[str]] = None) -> int:
    import argparse
    import json

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--run", metavar="TERRITORY",
                        help="run one territory's gate and name the outcome")
    parser.add_argument("--run-all", action="store_true")
    parser.add_argument("--strict", action="store_true",
                        help="also fail on `drift` (a gate that rewrites "
                             "tracked artefacts).  For the human who owns the "
                             "territory; ci_merge deliberately does not use it.")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    args = parser.parse_args(argv)

    if args.run or args.run_all:
        targets = territories() if args.run_all else [args.run]
        worst = "ok"
        for name in targets:
            outcome, detail = run(ROOT, name, timeout=args.timeout)
            head = detail.splitlines()[0] if detail else ""
            print("%-8s %-18s %s" % (outcome.upper(), name, head))
            if SEVERITY[outcome] > SEVERITY[worst]:
                worst = outcome
        allowed = STRICT_PASSING if args.strict else PASSING
        return 0 if worst in allowed else 1

    result = survey()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
        return 0
    print("%d territories" % result["n_territories"])
    print("  gated by their own verify script (%d): %s"
          % (len(result["gated"]), ", ".join(result["gated"]) or "-"))
    if result["non_canonical"]:
        print("    under a non-canonical name: %s"
              % ", ".join("%s/%s" % (n, result["rows"][n]["name"])
                          for n in result["non_canonical"]))
    print("  gated by their test suite only (%d): %s"
          % (len(result["tests_only"]), ", ".join(result["tests_only"]) or "-"))
    print("  UNGATED (%d): %s"
          % (len(result["ungated"]), ", ".join(result["ungated"]) or "-"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
