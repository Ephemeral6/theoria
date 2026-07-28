"""The seven surprises, and the counter that makes constraint 8 checkable.

`Theoria.md` 1.10(d): the loop is driven by surprise, surprises come in seven
kinds in two families, and **a model is called only when one has fired**. The
empirical five change the manual; the computational two change the playbook.
With no surprise, plan and commit run silently and free.

Counting them is not bookkeeping. It is how the arm's central claim is checked
after the fact: open the ledger, count `model_call` records, count surprises,
and the two numbers had better line up. `Register.audit()` does exactly that
against the ledger, and reports a violation rather than hiding one.
"""

import json
import time
from typing import Any, Dict, List, Optional

#: The empirical family: the world disagreed with the manual. Fix the manual.
EMPIRICAL = (
    "replay_mismatch",       # theory.py disagrees with a recorded transition
    "render_mismatch",       # a pixel belongs to no object and to no board cell
    "proof_failure",         # a declared law will not go through
    "probe_refutation",      # a designed experiment's prediction was wrong
    "execution_mismatch",    # a committed plan's step did not do what was said
)

#: The computational family: the manual is fine, getting value out of it is not.
#: Fix the playbook.
COMPUTATIONAL = (
    "search_timeout",        # the planner did not finish inside its budget
    "heuristic_miss",        # the heuristic ranked a dead branch first
)

KINDS = EMPIRICAL + COMPUTATIONAL

FAMILY = {k: "empirical" for k in EMPIRICAL}
FAMILY.update({k: "computational" for k in COMPUTATIONAL})


class Surprise:
    __slots__ = ("kind", "detail", "step_idx", "payload", "ts", "seq",
                 "handled_by")

    def __init__(self, kind: str, detail: str, *, step_idx: Optional[int] = None,
                 payload: Optional[Dict[str, Any]] = None, seq: int = 0):
        if kind not in KINDS:
            raise ValueError(
                "%r is not one of the seven surprises. Adding an eighth is a "
                "change to Theoria.md 1.10(d), not to this file." % (kind,))
        self.kind = kind
        self.detail = detail
        self.step_idx = step_idx
        self.payload = payload or {}
        self.ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self.seq = seq
        self.handled_by: Optional[str] = None

    @property
    def family(self) -> str:
        return FAMILY[self.kind]

    @property
    def book(self) -> str:
        return "theory.dsl" if self.family == "empirical" else "playbook.dsl"

    def as_json(self) -> Dict[str, Any]:
        return {"seq": self.seq, "kind": self.kind, "family": self.family,
                "book": self.book, "detail": self.detail,
                "step_idx": self.step_idx, "ts": self.ts,
                "handled_by": self.handled_by, "payload": self.payload}


class Register:
    """Every surprise this run met, in order, and what it triggered."""

    def __init__(self) -> None:
        self.items: List[Surprise] = []

    def fire(self, kind: str, detail: str, **kwargs: Any) -> Surprise:
        item = Surprise(kind, detail, seq=len(self.items) + 1, **kwargs)
        self.items.append(item)
        return item

    @property
    def pending(self) -> List[Surprise]:
        return [s for s in self.items if s.handled_by is None]

    def handled(self, by: str) -> List[Surprise]:
        taken = self.pending
        for item in taken:
            item.handled_by = by
        return taken

    def counts(self) -> Dict[str, int]:
        """All seven kinds, always -- a zero is a measurement, not an absence."""
        out = {kind: 0 for kind in KINDS}
        for item in self.items:
            out[item.kind] += 1
        return out

    def summary(self) -> Dict[str, Any]:
        counts = self.counts()
        return {
            "total": len(self.items),
            "by_kind": counts,
            "by_family": {
                "empirical": sum(counts[k] for k in EMPIRICAL),
                "computational": sum(counts[k] for k in COMPUTATIONAL),
            },
            "unhandled": len(self.pending),
        }

    def to_jsonl(self, path: str) -> str:
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            for item in self.items:
                fh.write(json.dumps(item.as_json(), sort_keys=True))
                fh.write("\n")
        return path

    # -- the audit ---------------------------------------------------------
    def audit(self, ledger_records: List[Dict[str, Any]], run_id: str
              ) -> Dict[str, Any]:
        """Constraint 8, checked against the ledger rather than asserted.

        The rule is not "one call per surprise" -- a single theorize may answer
        several surprises at once, and probe design spends a call of its own.
        The rule is the one Theoria.md states: **no surprise, no model call**,
        and no call at any beat other than theorize and probe design. Both are
        decidable from the records, because `ModelDesk` writes `beat` into
        every one.

        **Where `beat` lives changed.** `LEDGER_FORMAT.md` §4 closed the
        `model_call` field set after P-8, so it now rides inside `request`;
        P-8-era records still carry it at the top level. Both depths are read.
        Reading only the top one made this auditor report
        `calls_at_forbidden_beats: {"unknown": 1}` on every post-§4 ledger
        while `armtools/archive.constraint_8` reported the same run as holding
        — two auditors of the same constraint in the same arm, disagreeing on
        every real file. The one that was wrong was this one, and its own
        docstring is what said it could not be.
        """
        calls = [r for r in ledger_records
                 if r.get("event") == "model_call" and r.get("run_id") == run_id]
        beats: Dict[str, int] = {}
        for record in calls:
            request = record.get("request")
            beat = (record.get("beat")
                    or (request.get("beat") if isinstance(request, dict) else None)
                    or "unknown")
            beats[beat] = beats.get(beat, 0) + 1

        illegal = {b: n for b, n in beats.items()
                   if b not in ("theorize", "probe_design")}
        calls_without_cause = bool(calls) and not self.items
        return {
            "model_calls": len(calls),
            "calls_by_beat": beats,
            "surprises": len(self.items),
            "calls_at_forbidden_beats": illegal,
            "calls_without_any_surprise": calls_without_cause,
            "constraint_8_holds": (not illegal) and not calls_without_cause,
        }
