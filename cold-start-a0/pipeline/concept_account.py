"""The concept account, priced against a responsibility-complete alternative.

`A0_REPORT.md` §4: by Theoria 1.8's admission rule — a concept earns its place by
making the manual shorter — the A0 Button and Door should both have been
**rejected** (−17 and −13 bits). They were admitted anyway, on full-frame
responsibility. Two of the framework's own criteria disagreed.

The diagnosis in that report was that the accounting compares against the wrong
alternative. This module implements the fix, in three terms rather than one.

## What "without the concept" has to mean

The alternative to *"the Button is an object"* is **not** *"encode the Button's
pixel edits"* — that was the old baseline, and it is free of every obligation the
object carries. The honest alternative has to stay a legal manual, which means it
has to satisfy two things the old baseline ignored:

**1 · Responsibility (constraint 2).** Cells that vary cannot be board. Drop the
object and those pixels belong to nobody, and the cheap layer fails at frame 0.
The cheapest legal replacement is a raw per-pixel encoding of those cells for the
whole trajectory — *including their frame-0 declaration*, which the old baseline
never charged for while charging the object 21 bits for its own.

**2 · Expressibility.** Drop the object and every clause that *names* it goes
with it. In A0 that is `press_left`'s and `door_opens_left`'s effects, and the
`door_latch` invariant. The invariant language is counts, parity and finite
weights **over objects** (dsl_grammar_v0.1 §v1); there is no pixel-level
paraphrase of `count(Button, 8) + count(Door) = 1` inside it. So the alternative
manual is not longer — it does not exist.

That gives a three-term verdict, and only the third term is a number:

```
mandatory  — dropping it breaks responsibility, or costs a law the DSL
             cannot restate. Price is irrelevant; it is not optional.
pays       — expressible without it, and cheaper with it.
rejected   — expressible without it, and cheaper without it.
```

Expressibility is decided mechanically: an object is load-bearing if any law
mentions it, or if any rule's *effect* targets it. A guard that merely tests a
colour (`colored(leftof(Cart), 7)`) survives the object's removal and does not
count.
"""

import json
import os
import re
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Set, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap  # noqa: F401,E402

from engines.mdl_segmenter.costs import CostModel  # noqa: E402
from theory_compiler.parser.ast_nodes import FuncCall, NameRef  # noqa: E402
from theory_compiler.parser.theory_parser import parse_theory  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@dataclass
class Account:
    object_id: str
    name: Optional[str]
    colour: Optional[int]

    script_with: int                  # declaration + this track's event bits
    script_without: int               # responsibility-complete pixel encoding
    script_delta: int                 # positive => the concept pays on the trace

    responsibility_cells: List[Tuple[int, int]]
    laws_naming_it: List[str]
    rules_targeting_it: List[str]
    manual_bytes: int                 # clauses that would be lost with it

    @property
    def load_bearing(self) -> bool:
        return bool(self.laws_naming_it or self.rules_targeting_it
                    or self.responsibility_cells)

    @property
    def verdict(self) -> str:
        if self.load_bearing:
            return "mandatory"
        return "pays" if self.script_delta > 0 else "rejected"

    @property
    def reason(self) -> str:
        if self.laws_naming_it:
            return ("a law names it (%s) and the invariant language has no "
                    "pixel-level paraphrase" % ", ".join(self.laws_naming_it))
        if self.rules_targeting_it:
            return ("a rule's effect targets it (%s); without the object the "
                    "event has no subject" % ", ".join(self.rules_targeting_it))
        if self.responsibility_cells:
            return ("%d cell(s) vary, so they cannot be board; dropping the "
                    "object leaves them unexplained"
                    % len(self.responsibility_cells))
        return "expressible without it; the trace script decides"

    def as_json(self) -> Dict[str, object]:
        return {
            "object_id": self.object_id,
            "name": self.name,
            "colour": self.colour,
            "script_with_bits": self.script_with,
            "script_without_bits": self.script_without,
            "script_delta_bits": self.script_delta,
            "responsibility_cells": [list(c) for c in self.responsibility_cells],
            "laws_naming_it": self.laws_naming_it,
            "rules_targeting_it": self.rules_targeting_it,
            "manual_bytes_at_risk": self.manual_bytes,
            "load_bearing": self.load_bearing,
            "verdict": self.verdict,
            "reason": self.reason,
        }


# ------------------------------------------------------------------- the trace

def _track_cells(payload) -> Set[Tuple[int, int]]:
    """Every cell this track ever occupies."""
    cells = set()
    rel = [tuple(c) for c in payload["cells"]]
    for anchor in payload["anchors"]:
        if anchor is None:
            continue
        for dr, dc in rel:
            cells.add((anchor[0] + dr, anchor[1] + dc))
    return cells


def _script_terms(payload, cost: CostModel) -> Tuple[int, int]:
    """(with, without) in bits, for one track.

    `with`     = the object's declaration plus its own events.
    `without`  = a responsibility-complete raw encoding of the same pixels:
                 declare every occupied cell at frame 0, then pay per changed
                 pixel per transition.  The frame-0 term is the one the old
                 accounting left out, and it is exactly the term the object's own
                 declaration was being charged for.
    """
    n_cells = len(payload["cells"])
    with_bits = cost.declaration_bits(n_cells, payload["shape"][0],
                                      payload["shape"][1])
    with_bits += sum(e["bits"] for e in payload["events"])

    pixel = cost.b_pos + cost.b_color
    without_bits = n_cells * pixel                       # frame-0 declaration
    for event in payload["events"]:
        if event["type"] == "move":
            without_bits += 2 * n_cells * pixel          # vacate + occupy
        elif event["type"] == "recolor":
            without_bits += len(event.get("cells") or payload["cells"]) * pixel
        else:                                            # vanish / appear
            without_bits += n_cells * pixel
    return with_bits, without_bits


# ------------------------------------------------------------------ the manual

def _laws_naming(ast, name: str) -> List[str]:
    out = []
    if ast.laws is None:
        return out
    for inv in ast.laws.invariants:
        if re.search(r"\b%s\b" % re.escape(name), inv.expr_text):
            out.append("invariant %s" % inv.name)
    for theorem in ast.laws.theorems:
        if re.search(r"\b%s\b" % re.escape(name), theorem.description or ""):
            out.append("theorem %s" % theorem.name)
    return out


def _rules_targeting(ast, name: str) -> List[str]:
    """Rules whose *effect* names the object; guards that only test a colour
    survive its removal and deliberately do not count."""
    out = []
    if ast.rules is None:
        return out
    for rule in ast.rules.rules:
        event = rule.event
        if isinstance(event, FuncCall) and event.args:
            head = event.args[0]
            if isinstance(head, NameRef) and head.name == name:
                out.append(rule.name)
    return out


def _manual_bytes(dsl_text: str, name: str) -> int:
    return sum(len(line.encode("utf-8")) + 1
               for line in dsl_text.splitlines()
               if not line.strip().startswith("#")
               and re.search(r"\b%s\b" % re.escape(name), line))


# --------------------------------------------------------------------- driver

def accounts(candidates_path: str, dsl_path: str,
             name_by_colour: Dict[int, str]) -> List[Account]:
    rows = [json.loads(line) for line in open(candidates_path, encoding="utf-8")
            if line.strip()]
    objects = [r for r in rows if r["kind"] == "object_hypothesis"]
    if not objects:
        return []

    dsl_text = open(dsl_path, encoding="utf-8").read()
    ast = parse_theory(dsl_text)

    grid = objects[0]["payload"]
    _ = grid
    height = width = 0
    for row in objects:
        for anchor in row["payload"]["anchors"]:
            if anchor:
                height = max(height, anchor[0] + 1)
                width = max(width, anchor[1] + 1)
    cost = CostModel(max(height, 1), max(width, 1), max_objects=len(objects))

    out: List[Account] = []
    for row in objects:
        payload = row["payload"]
        colour = payload.get("color")
        name = name_by_colour.get(colour)
        with_bits, without_bits = _script_terms(payload, cost)
        varying = sorted(_track_cells(payload)) if payload["events"] else []
        out.append(Account(
            object_id=payload["object_id"],
            name=name,
            colour=colour,
            script_with=with_bits,
            script_without=without_bits,
            script_delta=without_bits - with_bits,
            responsibility_cells=varying,
            laws_naming_it=_laws_naming(ast, name) if name else [],
            rules_targeting_it=_rules_targeting(ast, name) if name else [],
            manual_bytes=_manual_bytes(dsl_text, name) if name else 0,
        ))
    return out


NAME_BY_COLOUR = {7: "Button", 5: "Door", 6: "Cart"}


def main() -> int:
    artifacts = os.path.join(ROOT, "artifacts")
    report = {}
    for tag, candidates, dsl in (
        ("a0-base", "candidates.jsonl", "theory.dsl"),
        ("a0-no-button", "candidates_no_button.jsonl", "theory_no_button.dsl"),
    ):
        rows = accounts(os.path.join(artifacts, candidates),
                        os.path.join(ROOT, "theory", dsl), NAME_BY_COLOUR)
        report[tag] = [a.as_json() for a in rows]
        print("[%s]" % tag)
        print("  %-8s %-8s %8s %8s %8s  %-10s %s"
              % ("object", "name", "with", "without", "delta", "verdict", "reason"))
        for a in rows:
            print("  %-8s %-8s %8d %8d %+8d  %-10s %s"
                  % (a.object_id, a.name or "-", a.script_with, a.script_without,
                     a.script_delta, a.verdict, a.reason))
    out = os.path.join(artifacts, "concept_accounts.json")
    with open(out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
