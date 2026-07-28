"""The cost meter — A3's actual instrument.

C3 is a claim about a *bill*, so the bill has to be a measurement and not a
recollection.  Every arm runs under a meter, every meter writes a JSON
artefact, and the report's two-column table is generated from those artefacts
rather than typed.

**What is counted, and why each line is in the list.**

| line | unit | why it is here |
|---|---|---|
| `world_frames` | frames | the evidence the arm consumed.  The transfer arm's whole case is that this number is 1. |
| `world_actions` | actions | what the evidence cost to obtain.  On a live game this is the quota line, so it is the one that would show up on an invoice. |
| `engine_stages` | invocations | Theoria 1.10(b) rule 3: engine calls are not model calls.  Counted separately *because* they are free in the model-call sense and would otherwise hide the work. |
| `candidates_adjudicated` | rows | the proposals the theorizer had to read and rule on.  This is the LLM's real workload — the one thing in the loop that is neither free nor mechanical. |
| `theorize_rounds` | rounds | Theoria Phase 3's own scoreboard line (`每关 theorize 轮数`).  A round is one pass in which a human/LLM wrote or revised a book. |
| `dsl_clauses_written` | clauses | how much of the two books this arm had to author.  Zero is the transfer arm's claim, and it is checkable against the files. |
| `compile_runs` / `certify_runs` / `plan_runs` | invocations | the mechanical tail.  Included so the table cannot be accused of counting only the lines that flatter it. |

**`cost_to_first_plan`** is a snapshot of every line above, taken the moment a
plan first exists.  Theoria's C2 is about the *shape* of a bill over time, and
a total alone cannot show a shape; the snapshot is the front-loading measure.

**What the meter deliberately does not count.**  Wall-clock time and token
counts.  Neither is reproducible on this box — a determinism requirement runs
through this whole repo (`CLAUDE.md`) and a timing column would break it on the
first rerun.  The consequence is stated rather than hidden: A3 measures the
*structure* of the bill, not its dollar value, and `A3_REPORT.md` §6 says so.

Charges are explicit calls, never inferred from a wrapper, so reading an arm's
driver tells you exactly what it was charged for.
"""

import json
import os
from typing import Dict, List, Optional

LINES = (
    "world_frames",
    "world_actions",
    "engine_stages",
    "candidates_adjudicated",
    "theorize_rounds",
    "dsl_clauses_written",
    "compile_runs",
    "certify_runs",
    "plan_runs",
)


class Meter:
    """One arm's bill.  Append-only within a run; `Meter` never subtracts."""

    def __init__(self, arm: str, level: str, carries_books: bool,
                 note: str = ""):
        self.arm = arm
        self.level = level
        self.carries_books = carries_books
        self.note = note
        self.counts: Dict[str, int] = {line: 0 for line in LINES}
        self.events: List[Dict[str, object]] = []
        self.first_plan: Optional[Dict[str, int]] = None

    # ------------------------------------------------------------- charging

    def charge(self, line: str, amount: int = 1, why: str = "") -> None:
        if line not in self.counts:
            raise KeyError("no such meter line: %r" % line)
        if amount < 0:
            raise ValueError("the meter does not subtract")
        self.counts[line] += amount
        self.events.append({
            "seq": len(self.events),
            "line": line,
            "amount": amount,
            "why": why,
            "running_total": self.counts[line],
        })

    def charge_trace(self, path: str, why: str = "") -> int:
        """Charge the frames and actions in a trace the arm just read."""
        frames = actions = 0
        with open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                row = json.loads(line)
                frames += 1
                if row.get("action") is not None:
                    actions += 1

        self.charge("world_frames", frames, why or ("read %s" % os.path.basename(path)))
        self.charge("world_actions", actions, why or ("read %s" % os.path.basename(path)))
        return frames

    def charge_frame(self, path: str, why: str = "") -> None:
        """Charge exactly one frame and zero actions — the transfer arm's input."""
        self.charge("world_frames", 1,
                    why or ("read %s" % os.path.basename(path)))

    def charge_candidates(self, path: str, why: str = "") -> int:
        rows = 0
        with open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    rows += 1
        self.charge("candidates_adjudicated", rows,
                    why or ("adjudicate %s" % os.path.basename(path)))
        return rows

    def mark_first_plan(self) -> None:
        """Snapshot the bill at the moment a plan first exists."""
        if self.first_plan is None:
            self.first_plan = dict(self.counts)

    # -------------------------------------------------------------- reading

    def as_json(self) -> Dict[str, object]:
        return {
            "arm": self.arm,
            "level": self.level,
            "carries_books": self.carries_books,
            "note": self.note,
            "counts": dict(self.counts),
            "cost_to_first_plan": self.first_plan,
            "events": self.events,
        }

    def write(self, path: str) -> str:
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(self.as_json(), indent=2,
                                    sort_keys=True) + "\n")
        return path


def load(path: str) -> Dict[str, object]:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def compare(bills: List[Dict[str, object]]) -> Dict[str, object]:
    """The bill table, as data.

    Ratios are reported against the arm named `baseline` — the L1 cold start —
    and `null` rather than `inf` where the baseline is zero, because a ratio
    against zero is not a number and writing one would be a way of implying a
    measurement that was not made.
    """
    by_arm = {b["arm"]: b for b in bills}
    baseline = by_arm.get("l1_cold_start")

    table = []
    for line in LINES:
        row: Dict[str, object] = {"line": line}
        for bill in bills:
            row[bill["arm"]] = bill["counts"][line]
        if baseline is not None:
            base = baseline["counts"][line]
            for bill in bills:
                if bill["arm"] == "l1_cold_start":
                    continue
                value = bill["counts"][line]
                row["%s_vs_baseline" % bill["arm"]] = (
                    None if base == 0 else round(value / base, 4)
                )
        table.append(row)

    return {
        "arms": [
            {"arm": b["arm"], "level": b["level"],
             "carries_books": b["carries_books"], "note": b["note"]}
            for b in bills
        ],
        "table": table,
        "cost_to_first_plan": {
            b["arm"]: b["cost_to_first_plan"] for b in bills
        },
    }
