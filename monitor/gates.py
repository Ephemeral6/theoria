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
                   ".pytest_cache", ".vscode", ".idea"}


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
        return {"kind": "verify", "cmd": gate["cmd"], "name": gate["name"],
                "canonical": gate["canonical"],
                "why": "the territory ships its own completion gate"}
    if has_tests(root, directory):
        return {"kind": "pytest",
                "cmd": [sys.executable, "-m", "pytest", "-q", "-x"],
                "name": None, "canonical": None,
                "why": "no verify script; the test suite is the gate"}
    return {"kind": "none", "cmd": None, "name": None, "canonical": None,
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
        "n_territories": len(rows),
    }


def describe(row: Dict[str, Any], directory: str) -> str:
    """One line for `merge.log`.  An ungated merge has to be *readable*."""
    if row["kind"] == "verify":
        return "verify:%s(%s)" % (directory, row["name"])
    if row["kind"] == "pytest":
        return "pytest:%s" % directory
    return "UNGATED:%s" % directory


def main(argv: Optional[List[str]] = None) -> int:
    import argparse
    import json

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

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
