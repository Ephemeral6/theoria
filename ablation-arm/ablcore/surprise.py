"""The surprise bus — what makes the inner loop turn, in both arms.

`Theoria.md:233`:

    回路由**意外**驱动,意外七种、分两族:经验族五种(重放失配、渲染失配、证明失败、
    戳探打脸、执行失配)改说明书;计算族两种(搜索超时、启发失准)改玩法书。
    **有意外才回 theorize**;无意外时 plan/commit 静默运转,免费。

This module exists because of a trap the design had to walk around, recorded in
DESIGN.md §7.  Upstream `cold-start-a2` turns its repair loop by listing
`refute`/`locate`/`probe`/`repair` unconditionally in `run_all.py`'s step table —
there is no code anywhere that reads "the plan came back UNSAT" and decides the
loop is owed a turn.  An ablation that simply *deleted* those four steps and then
reported that the ablated arm never repairs would be dismantling the loop by hand
and calling the result a finding.

So both arms are driven by the same rule instead: **the loop turns if and only if
the bus is non-empty**, and the difference between the arms is only in what can
put something on it.  Then "the ablated arm's loop does not turn" is a
consequence of the incision rather than a decision by the author of a driver
script.  See DESIGN.md §7.3 for the two columns.

Of the seven kinds, `proof_failure` is unreachable in this arm by construction —
there is no proof to fail.  `raise_` refuses it rather than silently accepting a
kind the arm cannot generate, which is what makes the 7→6 claim checkable rather
than merely asserted (DESIGN.md §8, P-3).
"""

import json
from typing import Dict, List, Optional

EMPIRICAL = (
    "replay_mismatch",      # the manual and the record disagree on a transition
    "render_mismatch",      # the manual paints a pixel the record does not have
    "proof_failure",        # an admitted obligation will not discharge
    "probe_refutation",     # a designed experiment came back against the manual
    "execution_mismatch",   # a committed plan diverged from prediction
)

COMPUTATIONAL = (
    "search_timeout",
    "heuristic_miss",
)

KINDS = EMPIRICAL + COMPUTATIONAL

#: The kinds this arm cannot produce, and why.  A bus in ablated mode raises on
#: them: an arm without proof obligations has nothing that can fail to prove.
IMPOSSIBLE_WHEN_ABLATED = {
    "proof_failure": "no obligation is ever admitted, so none can fail "
                     "(Theoria.md constraint 6, cut — DESIGN.md §4 C-1..C-3)",
}

#: Which book a surprise corrects (`Theoria.md:124`).
BOOK = {kind: "manual" for kind in EMPIRICAL}
BOOK.update({kind: "playbook" for kind in COMPUTATIONAL})


class ImpossibleSurprise(AssertionError):
    """Raised when ablated code paths try to report a kind the cut removed."""


class SurpriseBus:
    """An append-only list of surprises, plus the one predicate the loop reads.

    `ablated=True` is the arm under test; `ablated=False` is the same bus with
    the full arm's kind set, so the two can be compared field by field.
    """

    def __init__(self, ablated: bool = True):
        self.ablated = bool(ablated)
        self._items: List[Dict[str, object]] = []

    # -- writing ---------------------------------------------------------
    def raise_(self, kind: str, detail: object, beat: Optional[str] = None) -> Dict:
        if kind not in KINDS:
            raise ValueError("unknown surprise kind %r; the taxonomy is frozen "
                             "at Theoria.md:233" % (kind,))
        if self.ablated and kind in IMPOSSIBLE_WHEN_ABLATED:
            raise ImpossibleSurprise(
                "%s cannot occur in the ablated arm: %s"
                % (kind, IMPOSSIBLE_WHEN_ABLATED[kind]))
        item = {"kind": kind, "family": "empirical" if kind in EMPIRICAL
                else "computational", "book": BOOK[kind], "detail": detail}
        if beat:
            item["beat"] = beat
        self._items.append(item)
        return item

    # -- reading ---------------------------------------------------------
    def pending(self) -> List[Dict[str, object]]:
        return list(self._items)

    def empty(self) -> bool:
        return not self._items

    def turns_the_loop(self) -> bool:
        """The whole scheduling rule, in one line, shared by both arms."""
        return not self.empty()

    def kinds_available(self) -> List[str]:
        if not self.ablated:
            return list(KINDS)
        return [k for k in KINDS if k not in IMPOSSIBLE_WHEN_ABLATED]

    def as_json(self) -> Dict[str, object]:
        return {
            "ablated": self.ablated,
            "count": len(self._items),
            "kinds_in_taxonomy": len(KINDS),
            "kinds_available_to_this_arm": len(self.kinds_available()),
            "kinds_removed_by_the_cut": sorted(IMPOSSIBLE_WHEN_ABLATED)
                                        if self.ablated else [],
            "turns_the_loop": self.turns_the_loop(),
            "surprises": self.pending(),
        }

    def __len__(self) -> int:
        return len(self._items)

    def __repr__(self) -> str:
        return "SurpriseBus(ablated=%r, %s)" % (
            self.ablated, json.dumps(self.pending(), sort_keys=True))
