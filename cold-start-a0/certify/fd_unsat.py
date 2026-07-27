"""Telling "proved unsolvable" apart from "crashed", on the Fast Downward path.

**上游缺陷 (engine-rig/fd_adapter), found by connecting the real planner.**

The bundled BFS stub reports unsolvability by raising
`RuntimeError("no plan exists for <problem>")`. Fast Downward reports it by
exiting **12** with no plan file, and `backends.run_fast_downward` turns that
into `RuntimeError("Fast Downward produced no plan file (exit 12): ...")` — the
same exception type it raises when FD genuinely fails. So on the FD path a
caller cannot distinguish

* *the planner proved there is no plan* — which under constraint 6 is the branch
  that triggers the certificate obligation and the whole M5 machinery, from
* *the planner fell over* — which is an incident.

That distinction is the entire point of the unsolvability work, so it cannot be
left to a string match at each call site. This module owns the predicate.

`fd_adapter` is `engine-rig`'s file and is not modified here; the finding is
recorded in DECISIONS.md D-A0-020 and in PARTNER_SYNC for that track. The right
upstream fix is for `solve()` to return `None`, or raise a distinguishable
`NoPlanExists`, on FD exit 12 — matching what the stub already means.

Fast Downward's exit codes (`driver/returncodes.py`): 0 success, **12
`SEARCH_UNSOLVABLE`** — proved, not merely unfound — 13 `SEARCH_UNSOLVED_INCOMPLETE`,
which is *not* a proof and is deliberately not treated as UNSAT here.
"""

import re
from typing import Optional

# 12 only.  13 means "my search was incomplete and I found nothing", which is a
# different claim and must not be laundered into an unsolvability result.
FD_UNSOLVABLE_EXIT = 12

_STUB = "no plan exists"
_FD = re.compile(r"produced no plan file \(exit (\d+)\)")


def is_unsat(exc: BaseException) -> bool:
    """Did the planner *prove* there is no plan?"""
    message = str(exc)
    if _STUB in message:
        return True
    match = _FD.search(message)
    return bool(match) and int(match.group(1)) == FD_UNSOLVABLE_EXIT


def classify(exc: BaseException) -> str:
    """`unsat` | `error`, with the exit code preserved for the incident log."""
    if is_unsat(exc):
        return "unsat"
    match = _FD.search(str(exc))
    return "error(exit %s)" % match.group(1) if match else "error"
