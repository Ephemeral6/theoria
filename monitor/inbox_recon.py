"""Whether the drop box is ever swept.

`monitor/inbox/` is the only cross-territory channel this repo has, and it is a
**drop box**: a sender writes a file, and nothing carries it to the addressee.
There is no delivery, no read receipt, no expiry. The morning of 2026-08-04 a
hand reconciliation over the recent slice reported 21 files of which 11 had
never been seen by their addressee. That number was produced by reading, so it
cannot be recomputed, and a queue statistic that cannot be recomputed decays
into an anecdote within a day. This module is the recomputable form.

What it can and cannot see
--------------------------
It cannot see reading. Nothing on disk records that a territory opened a file.
So "seen" is approximated by **citation**: the ask's own basename appearing in
some tracked file that is not the ask itself and not another inbox file. That
is a *sufficient* condition for having been read and not a necessary one — a
territory that read an ask, agreed with it and silently fixed the code leaves
no citation, and this tool will call that ask unseen.

The approximation therefore has a known direction: it **overcounts** unseen.
It is still the right instrument for the question actually being asked, which
is not "did anyone read this" but "can anyone downstream tell that this was
handled" -- and the answer to that one is the citation, by construction.
`uncited` is reported under that name for the same reason `absent` is never
reported as `0` anywhere else in this repository.

Addressee
---------
Taken from the filename, which `monitor/inbox/README.md` fixes as
`<UTC>-<from>-<slug>.md`. Senders have overwhelmingly used an explicit
`-to-<territory>-` infix; when it is present the addressee is that territory,
and when it is absent the file is `unaddressed` -- which is itself a finding,
because an ask with no addressee has nobody who could sweep it even if a sweep
existed.

Usage
-----
    python -m monitor.inbox_recon            # from the repo root
    python monitor/inbox_recon.py --json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from typing import Dict, List, Optional

#: The territories that can be an addressee. Taken from CLAUDE.md's territory
#: table plus the fleet directories it names. A name not in here is not
#: silently accepted as an addressee -- an unrecognised infix leaves the file
#: `unaddressed`, so a typo in a filename shows up as a missing addressee
#: rather than as a territory nobody can find.
TERRITORIES = (
    "theory-compiler", "engine-rig", "arc-recon", "proxy", "battery", "exam",
    "figures", "papers", "release", "freeze", "crosscheck", "a2_crosscheck",
    "baseline-arms", "theoria-arm", "ablation-arm", "fuzzlab", "verify-lab",
    "worldgen", "fleetkit", "fleet-study", "monitor",
)

#: An inbox filename as the README fixes it. Used both to enumerate the
#: population and to find citations of it elsewhere in the tree.
NAME_RE = re.compile(r"\d{8}T\d{4,6}Z-[A-Za-z0-9._+-]+?\.md")

#: Extensions worth opening when hunting for citations. A citation is a
#: filename in prose or in a path, so binaries and data blobs are skipped.
#: `.jsonl` and `.json` are in because manifests and run records cite asks.
TEXTUAL = (".md", ".py", ".json", ".jsonl", ".txt", ".sh", ".cmd", ".yml",
           ".yaml", ".log", ".toml", ".cfg", ".lean", ".html")

MAX_BYTES = 4 * 1024 * 1024


def _repo_root(start: Optional[str] = None) -> str:
    here = os.path.abspath(start or os.path.dirname(__file__))
    out = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                         cwd=here, capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError("not inside a git work tree: %s" % out.stderr.strip())
    return out.stdout.strip()


def tracked(root: str) -> List[str]:
    out = subprocess.run(["git", "ls-files", "-z"], cwd=root,
                         capture_output=True, text=True, check=True)
    return [p for p in out.stdout.split("\0") if p]


def addressee_of(basename: str) -> Optional[str]:
    """The territory a filename addresses, or None.

    Longest match wins, so `-to-theoria-arm-` is not read as `-to-theoria`
    would be if a shorter name were ever added to TERRITORIES.
    """
    best = None
    for t in TERRITORIES:
        if ("-to-%s-" % t) in basename:
            if best is None or len(t) > len(best):
                best = t
    return best


def population(root: str) -> List[str]:
    """Open inbox asks: tracked, top level, `.md`, README excluded.

    `archive/` is excluded from the population because a file there has been
    adjudicated -- that is the sweep, performed by hand, and counting it as
    open would report the one mechanism that does work as a failure.
    """
    out = []
    for path in tracked(root):
        if not path.startswith("monitor/inbox/"):
            continue
        rest = path[len("monitor/inbox/"):]
        if "/" in rest or not rest.endswith(".md") or rest == "README.md":
            continue
        out.append(rest)
    return sorted(out)


def citations(root: str, names: set) -> Dict[str, List[str]]:
    """Where each name is named, outside `monitor/inbox/` and outside itself."""
    found: Dict[str, List[str]] = {n: [] for n in names}
    for path in tracked(root):
        if path.startswith("monitor/inbox/"):
            continue
        if not path.endswith(TEXTUAL):
            continue
        full = os.path.join(root, path)
        try:
            if os.path.getsize(full) > MAX_BYTES:
                continue
            with open(full, "r", encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except OSError:
            continue
        if "Z-" not in text:
            continue
        for hit in set(NAME_RE.findall(text)):
            if hit in found:
                found[hit].append(path)
    return {k: sorted(v) for k, v in found.items()}


def reconcile(root: Optional[str] = None) -> dict:
    root = root or _repo_root()
    names = population(root)
    cited = citations(root, set(names))
    rows = []
    for name in names:
        where = cited.get(name, [])
        to = addressee_of(name)
        in_addressee = [p for p in where if to and p.split("/")[0] == to]
        rows.append({
            "file": name,
            "addressee": to,
            "cited_in": where,
            "cited": bool(where),
            # None, not False, when there is no addressee to have seen it:
            # an ask nobody was named on cannot be scored on whether its
            # addressee saw it, and a False here would read as "was ignored".
            "seen_by_addressee": (bool(in_addressee) if to else None),
            "seen_in": in_addressee,
        })
    by_addressee: Dict[str, Dict[str, int]] = {}
    for row in rows:
        key = row["addressee"] or "unaddressed"
        slot = by_addressee.setdefault(key, {"open": 0, "cited": 0,
                                             "uncited": 0, "seen": 0,
                                             "unseen": 0})
        slot["open"] += 1
        slot["cited" if row["cited"] else "uncited"] += 1
        if row["seen_by_addressee"] is True:
            slot["seen"] += 1
        elif row["seen_by_addressee"] is False:
            slot["unseen"] += 1
    archived = len([p for p in tracked(root)
                    if p.startswith("monitor/inbox/archive/")])
    return {
        "open": len(rows),
        "archived": archived,
        "addressed": sum(1 for r in rows if r["addressee"]),
        "unaddressed": sum(1 for r in rows if not r["addressee"]),
        "cited": sum(1 for r in rows if r["cited"]),
        "uncited": sum(1 for r in rows if not r["cited"]),
        "seen_by_addressee": sum(1 for r in rows
                                 if r["seen_by_addressee"] is True),
        "unseen_by_addressee": sum(1 for r in rows
                                   if r["seen_by_addressee"] is False),
        "no_addressee_to_have_seen_it": sum(1 for r in rows
                                            if r["seen_by_addressee"] is None),
        "by_addressee": dict(sorted(by_addressee.items())),
        "rows": rows,
        "caveat": ("`uncited` is not `unread`: citation is sufficient "
                   "evidence of having been handled and is not necessary. "
                   "The count is an upper bound on asks that went nowhere."),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--root", default=None)
    ap.add_argument("--addressee", default=None,
                    help="restrict the printed rows to one territory")
    args = ap.parse_args(argv)
    result = reconcile(args.root)
    if args.json:
        json.dump(result, sys.stdout, indent=1, sort_keys=True,
                  ensure_ascii=False)
        sys.stdout.write("\n")
        return 0
    print("open asks          : %d" % result["open"])
    print("archived (swept)   : %d" % result["archived"])
    print("addressed by name  : %d" % result["addressed"])
    print("no addressee       : %d" % result["unaddressed"])
    print("cited elsewhere    : %d" % result["cited"])
    print("uncited            : %d   (upper bound on asks that went nowhere)"
          % result["uncited"])
    print("seen by addressee  : %d" % result["seen_by_addressee"])
    print("NOT seen by it     : %d" % result["unseen_by_addressee"])
    print("no addressee named : %d   (absent, not zero -- nobody could sweep)"
          % result["no_addressee_to_have_seen_it"])
    print()
    print("%-16s %6s %6s %8s %6s %7s"
          % ("addressee", "open", "cited", "uncited", "seen", "unseen"))
    for key, slot in result["by_addressee"].items():
        print("%-16s %6d %6d %8d %6d %7d"
              % (key, slot["open"], slot["cited"], slot["uncited"],
                 slot["seen"], slot["unseen"]))
    if args.addressee:
        print()
        for row in result["rows"]:
            if row["addressee"] == args.addressee:
                print("  %s  %s" % ("cited  " if row["cited"] else "UNCITED",
                                    row["file"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
