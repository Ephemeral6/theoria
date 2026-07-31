"""C-2: certify keeps its cheap layer and loses its expensive one.

`Theoria.md:225-228` splits this beat itself — the incision runs along a seam the
framework had already drawn:

    廉价层——theory.py 全史重放 + 渲染一致性(**全帧责任制**);
    昂贵层——两本书清空全部证明义务:入册全称断言证得动、无歧义义务(恰一后继)清空、
             玩法书定理级条目相对说明书成立、依赖假设为空。

The cheap layer is imported from `cold-start-a0/certify/replay.py` and called
with the same arguments the full arm calls it with.  Not re-implemented, not
wrapped, not "equivalent" — the same function, so that P-1 and P-2 (DESIGN.md §8)
are equalities and not approximations.  Its four checks:

1. transition replay — `theory.step(state, ACTION_NAMES[action])`
2. rendering consistency — cell by cell against the recorded frame
3. full-frame responsibility — every pixel is board, or owned by exactly one
   object; `contested_pixel` and `unowned_pixel` otherwise
4. goal agreement — `theory.is_goal(state)` against the record's `win`

plus `AmbiguousTransition` -> `ambiguous_transition`.

**Note what check 4 and the ambiguity check become here.** Constraint 9 makes
"exactly one successor" a *theorem* (`Theoria.md:247`); the cheap layer only
notices ambiguity if some recorded transition happens to trip it at run time.
With the expensive layer gone, unambiguity is demoted from a proved property of
the manual to "nothing in the record happened to collide" — precisely the inverse
of the upgrade constraint 9 describes, back to a board game's "在冲突时以第 X 条
为准".  DESIGN.md §6 records this as a demotion rather than a shadow.

`expensive()` exists and raises.  Leaving the seam visible in code is worth more
than a silent absence: a reader of this arm can see exactly what was removed, and
`tests/test_incision.py` asserts that nothing calls it.
"""

from typing import Dict

import _bootstrap  # noqa: F401

from certify import replay  # noqa: E402  (cold-start-a0, read-only)

#: The anomaly vocabulary of the cheap layer, quoted so reports can assert that
#: this arm's set is the full arm's set.
ANOMALY_KINDS = ("render_mismatch", "contested_pixel", "unowned_pixel",
                 "goal_mismatch", "ambiguous_transition")

#: Which cheap-layer anomaly becomes which surprise (`Theoria.md:233`).
ANOMALY_TO_SURPRISE = {
    "render_mismatch": "render_mismatch",
    "contested_pixel": "render_mismatch",
    "unowned_pixel": "render_mismatch",
    "goal_mismatch": "replay_mismatch",
    "ambiguous_transition": "replay_mismatch",
}


class ObligationCut(NotImplementedError):
    """Raised by `expensive()`.  This arm admits no obligation to discharge."""


def cheap(theory_py: str, trace_path: str) -> Dict[str, object]:
    """The full arm's cheap layer, called with the full arm's arguments."""
    return replay.certify(theory_py, trace_path)


def expensive(*_args, **_kwargs):
    """The layer this arm does not have.

    Kept as a raising stub so the cut is legible in the source rather than
    inferred from an absence.  In the full arm this is
    `certify.lean_check.check` / `a2pipeline.certify_a2.lean`: run Lean, require
    exit 0, no `error:`, no `sorry`, at least one `#print axioms` report, and
    every axiom list empty.
    """
    raise ObligationCut(
        "the expensive certify layer is the ablated half (Theoria.md:227, "
        "constraint 6); this arm never admits an obligation, so it has none to "
        "discharge.  See DESIGN.md §4 C-2.")


def report_surprises(bus, cheap_report: Dict[str, object], beat: str = "certify"):
    """Put the cheap layer's anomalies on the bus.  Same rule in both arms."""
    for kind in cheap_report.get("anomaly_kinds", []):
        bus.raise_(ANOMALY_TO_SURPRISE[kind], {"anomaly": kind}, beat=beat)
    return bus
