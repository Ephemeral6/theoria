"""V8 item (1), part 3: wider token sweep, looking only for tokens that pay."""
from __future__ import annotations

import importlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, ROOT)

from exam.grading.registry import digest                      # noqa: E402
from exam.grading.selftest import _mark                        # noqa: E402
from exam.papers import BUILDERS, module_for                   # noqa: E402

PAPERS = list(BUILDERS) + ["handover_auto"]

CASES = []
for n in range(-12, 25):
    CASES.append(("int %d" % n, n))
for f in (0.0, 1.0, 6.0, -1.5, float("nan")):
    CASES.append(("float %r" % f, f))
for s in ("never", "not detected", "no divergence", "none", "None", "NEVER",
          "solvable", "unsolvable", "abstain", "unknown", "cannot tell",
          "0", "6", "-1", " 6 ", "no", "yes", "true", "false", "exact",
          "inexact", "silent", "nothing", "n/a", "", " ", "\t", "null",
          "nil", "undefined", "NaN", "[]", "{}", "-", "...", "?", "TBD",
          "unreadable", "walk", "push2"):
    CASES.append(("str %r" % s, s))
for d in ({}, {"a": {}}, {"index": None}, {"detected": False},
          {"index": None, "detected": None}, {"per_level": {}},
          {"verdict": "unsolvable"}, {"claim": "unsolvable"},
          {"labels": []}, {"rules_falsified": []},
          {"budget_actions": 0}, {"exact_on_heldout": False},
          {"exact_on_heldout": True}, {"said": "unsolvable"},
          {"answer": "unsolvable"}, {"answer": "never"},
          {"detected": True}, {"index": ""}, {"index": "x"}):
    CASES.append(("dict %r" % (d,), d))
for lst in ([], [[]], [{}], [None], [""], [[], []], [[[]]], [0], [False]):
    CASES.append(("list %r" % (lst,), lst))
CASES.append(("tuple ()", ()))
CASES.append(("set() -> frozenset()", frozenset()))


def main():
    for qt in PAPERS:
        module = (module_for(qt) if qt in BUILDERS
                  else importlib.import_module("exam.papers." + qt))
        paper = module.build()
        key_doc = paper.key(digest())
        axes_fn = getattr(module, "axes", None)
        ids = [e["item_id"] for e in key_doc["items"]]
        rep0 = _mark(key_doc, dict(module.reference_answers(paper, key_doc,
                                                            "oracle")),
                     "oracle", axes_fn)
        print("== %s  oracle %.3f/%.3f" % (qt, rep0.awarded, rep0.possible))
        for label, value in CASES:
            try:
                rep = _mark(key_doc, {i: value for i in ids}, "null", axes_fn)
            except Exception as exc:                  # noqa: BLE001
                print("   %-40s RAISED %s: %s" % (label, type(exc).__name__, exc))
                continue
            if rep.awarded > 1e-9:
                agg = {}
                for s in rep.scores:
                    if s.awarded > 1e-9:
                        agg[s.rubric_id] = round(agg.get(s.rubric_id, 0.0)
                                                 + s.awarded, 6)
                print("   PAID %-38s %8.3f / %-8.3f %s"
                      % (label, rep.awarded, rep.possible, agg))


if __name__ == "__main__":
    main()
