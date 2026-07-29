"""V8 item (1), part 2: item-level trace for every fake that was paid."""
from __future__ import annotations

import importlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, ROOT)

from exam.grading.registry import digest                      # noqa: E402
from exam.grading.selftest import _mark                        # noqa: E402
from exam.papers import BUILDERS, module_for                   # noqa: E402

PAID = {
    "adaptation": [("[]", []), ("0", 0), ("False", False), ("'None'", "None"),
                   ("'unsolvable'", "unsolvable"), ("-1", -1), ("True", True),
                   ("'none'", "none"), ("'0'", "0"),
                   ("'UNSOLVABLE'", "UNSOLVABLE")],
    "verdict": [("'unsolvable'", "unsolvable"), ("'UNSOLVABLE'", "UNSOLVABLE")],
}


def main():
    for qt, cases in PAID.items():
        module = module_for(qt)
        paper = module.build()
        key_doc = paper.key(digest())
        axes_fn = getattr(module, "axes", None)
        ids = [e["item_id"] for e in key_doc["items"]]
        truth_of = {e["item_id"]: e["truth"] for e in key_doc["items"]}
        print("=" * 78)
        print("PAPER %s (%s)" % (qt, paper.paper_id))
        for label, value in cases:
            rep = _mark(key_doc, {i: value for i in ids}, "null", axes_fn)
            print("-" * 70)
            print("  token %s -> %.3f / %.3f" % (label, rep.awarded, rep.possible))
            for s in rep.scores:
                if s.awarded <= 1e-9:
                    continue
                print("    %-28s [%s] %.3f/%.3f %s" %
                      (s.item_id, s.rubric_id, s.awarded, s.possible, s.verdict))
                print("        detail: %s" % json.dumps(s.detail, default=str,
                                                        sort_keys=True)[:700])
                print("        truth : %s" % json.dumps(truth_of[s.item_id],
                                                        default=str,
                                                        sort_keys=True)[:500])


if __name__ == "__main__":
    main()
