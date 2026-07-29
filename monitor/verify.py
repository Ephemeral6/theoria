"""monitor's own completion gate — the rig that enforces gates now has one.

```bash
bash monitor/verify.sh        # or: python monitor/verify.py
python monitor/verify.py --json
```

Until S13 this directory was **ungated**: no `verify` script and not one
`test_*.py`, so every branch touching `monitor/` merged with nothing checking
it. That is worth stating plainly rather than fixing quietly, because the rig
that decides whether everyone else's gate ran was the one place a defect could
hide from every check in the repository — and one did. Wiring `gates.py` in
turned up `subprocess.run(..., text=True)` decoding a UTF-8 board listing as
GBK on Windows, which threw inside a reader thread and left the monitor page's
board panel silently empty. Nothing was watching.

## The three parts

Modelled on `ablation-arm/verify.sh`, which S13's ticket names as the shape:

1. **tests** — `monitor/tests`
2. **one real run** — a full `scan.build()`, which is the thing this directory
   is *for*, plus `gates.survey()` and `board.py list`
3. **artifact field self-check** — the run's `state.json` carries the fields the
   page and the probes read, and the gate survey is internally consistent

## The verdict must survive its own output

Every stage's `detail` is text of unknown provenance -- pytest's output, a
subprocess's stderr, a board listing -- captured with `errors="replace"`, so it
can legitimately contain U+FFFD. On 2026-07-29 this gate printed
`== tests FAILED(1)` and then died with `UnicodeEncodeError: 'gbk' codec can't
encode character '\\ufffd'` *while printing the reason*: the reason was lost, and
the same line runs on green runs too, so any stage output holding one character
the console code page cannot represent turned a green gate into a traceback.
`emit` and `harden_stream` below close that: stdout is reconfigured to UTF-8
with `errors="replace"`, and every print goes through a fallback that scrubs
rather than raises. The property is that the gate can always print its verdict
and its reasons, whatever bytes the stages produced -- a crash must never be
able to substitute for a verdict.

## The gate does not dirty the workspace

`scan.build(out_dir=…)` writes into a `mkdtemp` and the repository is left
untouched. That is S13's own warning, and it is not hypothetical for this
directory: `state.json`, `index.html` and `history.jsonl` are all rewritten by a
scan, so a gate that ran one in place would report its own output as a change
and could turn the *next* territory's gate red for a reason that has nothing to
do with the branch being merged.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from typing import Any, Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for path in (HERE, ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)

import gates                                                       # noqa: E402

#: What `index.html`, `app.html` and the probes read out of a scan. A scan that
#: still runs but stops emitting one of these is a broken page nobody notices,
#: because the page renders and the missing panel just looks empty.
REQUIRED_STATE_FIELDS = ("agents", "board", "constraints", "engines",
                         "findings", "generated_at", "grid", "history",
                         "iteration_loop", "loop_stats")


def harden_stream(stream: Any) -> bool:
    """Make `stream` unable to raise on an unrepresentable character.

    UTF-8 encodes every string Python can hold, so re-pointing the encoding is
    the fix rather than a workaround; `errors="replace"` is the second belt, for
    the case where the stream cannot change encoding but can change its error
    handler. Returns whether anything was reconfigured, which is information the
    test wants and no caller should branch on.

    Guarded rather than assumed: `sys.stdout` is only a `TextIOWrapper` some of
    the time. Under pytest's capture, behind a `StringIO`, or after somebody has
    replaced it with their own object, `reconfigure` is simply absent -- and a
    gate that died trying to make its own output safe would be the same defect
    wearing a different hat.
    """
    try:
        stream.reconfigure(encoding="utf-8", errors="replace")
        return True
    except (AttributeError, ValueError, OSError, LookupError):
        pass
    try:                                   # encoding is fixed; errors may not be
        stream.reconfigure(errors="replace")
        return True
    except (AttributeError, ValueError, OSError, LookupError):
        return False


def emit(text: str = "", stream: Any = None) -> None:
    """`print`, with the guarantee that it does not raise on this text.

    `harden_stream` handles the streams that can be reconfigured; this handles
    the ones that cannot, including whatever a caller has substituted for
    `sys.stdout`. The scrub is lossy on purpose -- a mangled character in a gate
    log is cosmetic, a traceback in place of the verdict is not.

    Resolved at call time, not bound at import, so monkeypatching `sys.stdout`
    still works.
    """
    out = sys.stdout if stream is None else stream
    try:
        print(text, file=out)
        return
    except UnicodeEncodeError:
        pass
    encoding = getattr(out, "encoding", None) or "ascii"
    try:
        scrubbed = text.encode(encoding, "replace").decode(encoding, "replace")
    except (LookupError, UnicodeError):
        scrubbed = text.encode("ascii", "replace").decode("ascii")
    try:
        print(scrubbed, file=out)
    except UnicodeEncodeError:             # a stream that lied about `encoding`
        print(text.encode("ascii", "replace").decode("ascii"), file=out)


def _tests() -> Tuple[str, int, str]:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
         os.path.join(HERE, "tests")],
        cwd=HERE, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=900)
    return "tests", proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def _real_run(out_dir: str) -> Tuple[str, int, str, Dict[str, Any]]:
    """A full scan into a throwaway directory, plus the two cheap surfaces."""
    import scan

    lines: List[str] = []
    try:
        scan.build(False, out_dir=out_dir)
    except Exception as exc:                        # noqa: BLE001 -- reported
        return "real run", 1, "scan.build raised %s: %s" % (type(exc).__name__,
                                                            exc), {}
    written = sorted(os.listdir(out_dir))
    lines.append("scan.build wrote %s" % ", ".join(written))

    survey = gates.survey(ROOT)
    lines.append("gates: %d gated, %d tests-only, %d UNGATED"
                 % (len(survey["gated"]), len(survey["tests_only"]),
                    len(survey["ungated"])))
    if survey["ungated"]:
        lines.append("  ungated: %s" % ", ".join(survey["ungated"]))

    board = subprocess.run(
        [sys.executable, os.path.join(HERE, "board.py"), "list"],
        cwd=ROOT, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=120)
    if board.returncode != 0:
        return "real run", 1, "\n".join(lines + ["board.py list failed",
                                                 board.stderr]), survey
    lines.append("board.py list: %d line(s)"
                 % len(board.stdout.strip().splitlines()))
    return "real run", 0, "\n".join(lines), survey


def _fields(out_dir: str, survey: Dict[str, Any]) -> Tuple[str, int, str]:
    path = os.path.join(out_dir, "state.json")
    if not os.path.exists(path):
        return "artifact fields", 1, "no state.json was produced"
    with open(path, encoding="utf-8") as handle:
        state = json.load(handle)

    problems: List[str] = []
    for field in REQUIRED_STATE_FIELDS:
        if field not in state:
            problems.append("state.json has no `%s`" % field)
    if not state.get("findings") and "findings" in state:
        problems.append("`findings` is empty -- every probe returned nothing, "
                        "which is a broken scan rather than a clean repository")

    # The board panel is the field that was silently empty before S13, so it
    # gets checked for content and not merely for presence.
    board = state.get("board")
    if not isinstance(board, dict) or not board.get("listing"):
        problems.append("`board.listing` is empty -- this is exactly the shape "
                        "the GBK decode bug produced: the page renders and the "
                        "panel is simply blank")

    if survey:
        rows = survey["rows"]
        counted = (len(survey["gated"]) + len(survey["tests_only"])
                   + len(survey["ungated"]))
        if counted != len(rows):
            problems.append("the gate survey partitions %d territories into %d "
                            "buckets" % (len(rows), counted))
        for name in survey["gated"]:
            if rows[name]["cmd"] is None:
                problems.append("%s is reported gated with nothing to run" % name)

    if problems:
        return "artifact fields", 1, "\n".join(problems)
    return "artifact fields", 0, ("state.json carries all %d required fields; "
                                  "the gate survey is consistent"
                                  % len(REQUIRED_STATE_FIELDS))


def _board_states_disjoint() -> Tuple[str, int, str]:
    """No id may be in `done/` and also on the shelf or under claim.

    This is a **post-merge** check by nature, which is why it lives in the gate
    and not only in `board.py`. Board state is a set of tracked files; a merge
    from a branch based before a `done` restores `items/<id>.md`, because git
    compares trees and cannot see that a file in a *different* directory means
    the work is finished. No verb in `board.py` runs during a merge, so no
    guard inside `board.py` can be the whole answer -- something has to look at
    the result afterwards.

    Measured on 2026-07-29: `E8-ic3-scale` was delivered by W-1660 at 12:16:28Z
    and re-claimed four times after that, sitting in `items/`, `claimed/` and
    `done/` at once. Nothing errored. `list` showed it as ordinary available
    work, and each of those workers spent a launch redoing a delivered item.

    Red, not a warning: the cost is a whole session per occurrence and the fix
    is one command (`board.py reconcile --fix`).
    """
    sys.path.insert(0, HERE)
    import board                                          # noqa: PLC0415

    res = board.resurrected()
    if not res:
        return ("board states disjoint", 0,
                "no id is in done/ and on the shelf at the same time "
                "(%d delivered, %d claimed)"
                % (len(board.done_ids()), len(board.claimed_map())))
    lines = ["%d delivered item(s) are back on the board -- a merge resurrected "
             "them. Run `python monitor/board.py reconcile --fix`." % len(res)]
    for iid, st in sorted(res.items()):
        where = []
        if st["in_items"]:
            where.append("items/")
        if st["claimed_by"]:
            where.append("claimed/ by %s" % st["claimed_by"])
        lines.append("  %-34s delivered by %-8s still in %s"
                     % (iid, st["deliverer"], " + ".join(where)))
    return "board states disjoint", 1, "\n".join(lines)


def verify() -> Dict[str, Any]:
    out_dir = tempfile.mkdtemp(prefix="monitor-verify-")
    stages: List[Dict[str, Any]] = []

    label, code, detail = _tests()
    stages.append({"stage": label, "returncode": code, "detail": detail[-2000:]})

    label, code, detail = _board_states_disjoint()
    stages.append({"stage": label, "returncode": code, "detail": detail[-2000:]})

    label, code, detail, survey = _real_run(out_dir)
    stages.append({"stage": label, "returncode": code, "detail": detail[-2000:]})

    label, code, detail = _fields(out_dir, survey)
    stages.append({"stage": label, "returncode": code, "detail": detail[-2000:]})

    failed = [s["stage"] for s in stages if s["returncode"] != 0]
    return {
        "what": "monitor completion gate",
        "out_dir": out_dir,
        "stages": stages,
        "gate_survey": {k: survey.get(k) for k in
                        ("gated", "tests_only", "ungated", "non_canonical")}
                       if survey else None,
        "failed": failed,
        "green": not failed,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    # Before anything is printed, and covering both branches below: `--json`
    # uses `ensure_ascii=False`, so it was exposed to exactly the same crash as
    # the human report. stderr too -- a traceback is text of unknown provenance
    # as well.
    harden_stream(sys.stdout)
    harden_stream(sys.stderr)

    result = verify()
    if args.json:
        emit(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
        return 0 if result["green"] else 1

    for stage in result["stages"]:
        emit("=" * 70)
        emit("== %-18s %s" % (stage["stage"],
                              "ok" if stage["returncode"] == 0
                              else "FAILED(%d)" % stage["returncode"]))
        emit("=" * 70)
        emit(stage["detail"].strip() or "(no output)")
    survey = result["gate_survey"]
    if survey and survey["ungated"]:
        emit("\nterritories that merge with nothing checking them: %s"
             % ", ".join(survey["ungated"]))
        emit("(reported, not a failure -- making it visible is the fix; "
             "refusing to merge them would stop the repository dead)")
    emit("\n%s" % ("GREEN" if result["green"]
                   else "RED: " + ", ".join(result["failed"])))
    return 0 if result["green"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
