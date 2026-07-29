"""Resource 3 of the OPS-R proposal: `monitor/board/claimed/` against `board.log`.

**This file is a proposal, not a shipped check.** It lives in a run directory
under `arc-recon/` because the resource it audits is `monitor/`'s and this item's
territory is `arc-recon`. It reads and never writes. Landing it means moving it
to `monitor/tools/` and adding a step to whatever `monitor` uses for a green
light; that is a `monitor`-territory call.

    python board_log_invariants.py            # from anywhere in the repo

## The invariant, on the resource

`monitor/board/claimed/` is the only thing making territory allocation
exclusive, and `board.log` is the only record of how it got that way. Two
writers: `board.py`'s `cmd_claim` / `cmd_done` / `cmd_release` / `cmd_sweep`,
which log; and a human `mv` after a window closes or a crash, which does not.
The second writer is not abuse — after a crash somebody has to clear the board.

So the invariant is not "only `board.py` may move a file". It is:

    replaying board.log yields exactly the set of items now in claimed/

which is checkable on the two artefacts, whoever moved what. A divergence means
the log has stopped describing the board, and a log that has stopped describing
the board cannot be used to answer "who holds this item" — which is what it is
for.

## The negative control

`_planted_divergence()` builds a synthetic log and a synthetic directory listing
that disagree, and asserts the checker reports it. Without that, a checker that
returned `{"diverged": []}` unconditionally would look identical to this one on
a clean board.
"""

import os
import re
import sys
from typing import Any, Dict, List, Sequence, Set, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, os.pardir, os.pardir, os.pardir, os.pardir))
BOARD = os.path.join(REPO, "monitor", "board")

LINE = re.compile(
    r"^(?P<t>\S+)\s+(?P<verb>CLAIM|DONE|RELEASE|SWEEP)\s+(?P<item>[A-Za-z0-9_.\-]+)"
    r"(?:\s+by\s+(?P<worker>\S+))?")


def replay(lines: Sequence[str]) -> Tuple[Set[str], List[Dict[str, Any]]]:
    """The set of items the log says are held, and the lines it could not parse.

    A line this cannot read is reported, not skipped: an unparsed line is a
    transition nothing has accounted for, which is the same failure the check
    exists to find.
    """
    held: Set[str] = set()
    unparsed: List[Dict[str, Any]] = []
    for number, raw in enumerate(lines, 1):
        raw = raw.strip()
        if not raw or raw.startswith("#"):
            continue
        match = LINE.match(raw)
        if not match:
            unparsed.append({"line": number, "text": raw[:80]})
            continue
        verb, item = match.group("verb"), match.group("item")
        if verb == "CLAIM":
            held.add(item)
        else:                       # DONE / RELEASE / SWEEP all vacate the slot
            held.discard(item)
    return held, unparsed


def on_disk(claimed_dir: str) -> Set[str]:
    """Item ids currently in `claimed/`, from `<item-id>.<worker>.md`."""
    if not os.path.isdir(claimed_dir):
        return set()
    out = set()
    for name in os.listdir(claimed_dir):
        if not name.endswith(".md"):
            continue
        out.add(name[:-3].rsplit(".", 1)[0])
    return out


def check(board_dir: str = BOARD) -> Dict[str, Any]:
    log_path = os.path.join(board_dir, "board.log")
    with open(log_path, encoding="utf-8", errors="replace") as handle:
        lines = handle.readlines()
    held, unparsed = replay(lines)
    present = on_disk(os.path.join(board_dir, "claimed"))
    return {
        "log_says_held": sorted(held),
        "claimed_dir_holds": sorted(present),
        # Named separately because the two directions mean different things.
        # `log_only` is an item the log thinks is held and is not: somebody moved
        # it back by hand. `disk_only` is an item held with no CLAIM behind it:
        # somebody moved it *in* by hand, which is the dangerous one, because
        # two workers can then hold the same territory.
        "log_only": sorted(held - present),
        "disk_only": sorted(present - held),
        "unparsed_lines": unparsed,
        "clean": not (held - present) and not (present - held) and not unparsed,
    }


def _planted_divergence() -> Dict[str, Any]:
    """The negative control, as a function so it runs in the CLI too."""
    held, unparsed = replay([
        "2026-01-01T00:00:00Z CLAIM A-one by W-1",
        "2026-01-01T00:00:01Z CLAIM B-two by W-2",
        "2026-01-01T00:00:02Z DONE A-one by W-1",
        "this line is not a transition",
    ])
    present = {"C-three"}
    return {"log_only": sorted(held - present),
            "disk_only": sorted(present - held),
            "unparsed": unparsed}


def main() -> int:
    control = _planted_divergence()
    ok = (control["log_only"] == ["B-two"]
          and control["disk_only"] == ["C-three"]
          and len(control["unparsed"]) == 1)
    print("== negative control: %s" % ("goes red as it must" if ok
                                       else "DID NOT FIRE -- the checker is broken"))
    if not ok:
        print("   %r" % control)
        return 2

    report = check()
    print("== live board")
    print("   log says held : %s" % (", ".join(report["log_says_held"]) or "-"))
    print("   claimed/ holds: %s" % (", ".join(report["claimed_dir_holds"]) or "-"))
    if report["log_only"]:
        print("   LOG ONLY (moved out by hand): %s" % ", ".join(report["log_only"]))
    if report["disk_only"]:
        print("   DISK ONLY (claimed with no CLAIM line): %s"
              % ", ".join(report["disk_only"]))
    for row in report["unparsed_lines"][:5]:
        print("   UNPARSED line %d: %s" % (row["line"], row["text"]))
    print("   %s" % ("clean" if report["clean"] else "DIVERGED"))
    return 0 if report["clean"] else 1


if __name__ == "__main__":
    sys.exit(main())
