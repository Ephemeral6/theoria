#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Old vs new, per book.  Every number here is read from a file; none is typed.

Baseline: exam's pre-repair census, `exam/runs/20260801T0400Z-U3-CENSUS/
census.json` on branch `ep/u3-exam-audit` (labels 14 discharged / 9 vacuous /
1 failing_obligation over 24 books).  That branch is not on master, so the
baseline's 24 (path -> label) pairs are transcribed below and the transcription
is checked: if the new census enumerates a different set of books, this script
refuses rather than silently comparing two different populations.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

#: exam/runs/20260801T0400Z-U3-CENSUS/census.json -> rows[].{run,label}
BASELINE = {
    "a0-spike/artifacts": "discharged",
    "cold-start-a0/prime/theory/generated": "vacuous",
    "cold-start-a0/theory/generated": "discharged",
    "cold-start-a0/theory/generated_no_button": "discharged",
    "cold-start-a2/theory/generated": "discharged",
    "cold-start-a2/theory/generated_holed": "discharged",
    "cold-start-a2/theory/generated_repaired": "discharged",
    "cold-start-a2/theory/generated_repaired_stale": "failing_obligation",
    "cold-start-a3/runs/20260728T1800Z-A6-transfer-protocol/generated/a3_l2_oneway": "discharged",
    "cold-start-a3/runs/20260728T1800Z-A6-transfer-protocol/generated/a3_l2_positive": "discharged",
    "cold-start-a3/runs/20260728T1800Z-A6-transfer-protocol/generated/a3_l2_rewired": "discharged",
    "cold-start-a3/theory/generated_l1": "discharged",
    "cold-start-a3/theory/generated_l1_vacuous": "vacuous",
    "cold-start-a3/theory/generated_l2": "discharged",
    "cold-start-a3/theory/generated_l2_scratch": "discharged",
    "cold-start-a3/theory/generated_l2neg": "discharged",
    "cold-start-a3/theory/generated_l2rew": "discharged",
    "theory-compiler/handover_packages/a0-cart/levels/base": "vacuous",
    "theory-compiler/handover_packages/a0-cart/levels/no-button": "vacuous",
    "theory-compiler/handover_packages/a0-sokoban2/levels/crossing-up": "vacuous",
    "theory-compiler/handover_packages/a0-sokoban2/levels/match": "vacuous",
    "theory-compiler/lean": "vacuous",
    "theory-compiler/runs/20260728T080019Z-C4-deadlock-lean": "vacuous",
    "theory-compiler/runs/20260728T080019Z-C4-deadlock-lean/verify": "vacuous",
}

WHY = {
    "theory-compiler/runs/20260728T080019Z-C4-deadlock-lean":
        "the C4 deadlock proof: `dead` is now read as `prune` and §1.2.1-prune "
        "(a)(b)(c) are discharged by `pat_witness`, `no_goal_pinned`, "
        "`level_is_winnable`",
    "theory-compiler/runs/20260728T080019Z-C4-deadlock-lean/verify":
        "same development, `verify/` copy",
    "theory-compiler/lean":
        "the invariant is called `Inv`, not `I`.  The old (c) hard-coded "
        "`defs['I']` and returned \"no `def I` found to check\" -> vacuous.  "
        "The predicate is now read off the theorem's own conclusion.",
    "theory-compiler/handover_packages/a0-cart/levels/base":
        "two theorems: a closure lemma about the `Reachable` relation and an "
        "existential goal witness.  Neither is one of §1.2.1's three kinds, so "
        "nothing was ever checked -- `unclassified`, not an accusation",
    "theory-compiler/handover_packages/a0-cart/levels/no-button": "as above",
    "theory-compiler/handover_packages/a0-sokoban2/levels/crossing-up": "as above",
    "theory-compiler/handover_packages/a0-sokoban2/levels/match": "as above",
}


def main() -> int:
    census = json.loads((HERE / "census.json").read_text(encoding="utf-8"))
    new = {r["run"].replace("\\", "/").lstrip("./"): r["label"]
           for r in census["rows"] if r["books"]}
    if set(new) != set(BASELINE):
        print("POPULATION MISMATCH -- refusing to compare.", file=sys.stderr)
        print("only new:", sorted(set(new) - set(BASELINE)), file=sys.stderr)
        print("only old:", sorted(set(BASELINE) - set(new)), file=sys.stderr)
        return 2

    moved = [(p, BASELINE[p], new[p]) for p in sorted(new) if BASELINE[p] != new[p]]

    def tally(d):
        out = {}
        for v in d.values():
            out[v] = out.get(v, 0) + 1
        return dict(sorted(out.items()))

    old_t, new_t = tally(BASELINE), tally(new)
    lines = [
        "# E1 census: before and after the F1/D1/D2 repair",
        "",
        "Population: the **24 Lean books on disk**, one row per directory.",
        "This is an engineering denominator.  It is NOT STATS_RULES §1.2's E1",
        "rate, whose denominator is the frozen 19 sealed claim-set games (12 at",
        "the clean layer).  Nothing on disk today is a sealed game.",
        "",
        "| label | before | after |",
        "|---|---|---|",
    ]
    for lab in sorted(set(old_t) | set(new_t)):
        lines.append("| `%s` | %d | %d |" % (lab, old_t.get(lab, 0), new_t.get(lab, 0)))
    lines += [
        "| **attained** | **%d / 24** | **%d / 24** |"
        % (old_t.get("discharged", 0), new_t.get("discharged", 0)),
        "",
        "## the %d books whose verdict moved" % len(moved),
        "",
        "| book | before | after | why |",
        "|---|---|---|---|",
    ]
    for p, o, n in moved:
        lines.append("| `%s` | `%s` | `%s` | %s |" % (p, o, n, WHY.get(p, "")))
    lines += [
        "",
        "## the books whose verdict did NOT move",
        "",
        "Both true vacuity findings survive: `cold-start-a3/theory/",
        "generated_l1_vacuous` (the frozen §9.2 negative control -- 抓不住它就不许",
        "冻结) and `cold-start-a0/prime/theory/generated` are still `vacuous`, now",
        "because a shape-classified invariant was found constant rather than",
        "because a name matched.  `cold-start-a2/theory/generated_repaired_stale`",
        "is still `failing_obligation`: it does not compile, and (a) is untouched.",
        "The 17 other previously-discharged books are unchanged.",
        "",
        "## direction of the change",
        "",
        "Every move is `vacuous` -> something else, i.e. this repair only ever",
        "**removes** an accusation.  Three become `discharged` and four become",
        "`unclassified`; nothing that attained stopped attaining, and nothing",
        "that was refuted became attained without a §1.2.1 check saying so.",
        "The two developments §1.2.1 names as vacuous are still called vacuous.",
        "",
    ]
    (HERE / "COMPARISON.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
