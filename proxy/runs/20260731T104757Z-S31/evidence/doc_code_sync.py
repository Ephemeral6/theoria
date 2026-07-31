"""Print what the sync gate reads on both sides, and each mutation's red.

    python evidence/doc_code_sync.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "proxy", "tests"))

from test_ledger_format_sync import (gap_keys, legs_named,   # noqa: E402
                                     problems, section)
from proxy.reconcile import RECONCILIATION_KEY               # noqa: E402

MUTATIONS = [
    ("a leg renamed inside the table",
     lambda b: b.replace("| **cost** |", "| **spend** |")),
    ("`turns` promoted to a fourth leg -- the ticket's own mistake",
     lambda b: b.replace("| **score, per run** |",
                         "| **turns** | recorded | the turn counts agree |\n"
                         "| **score, per run** |")),
    ("`gaps.turns` dropped from the document",
     lambda b: b.replace("`gaps.turns`", "somewhere")),
    ("`gaps.score_per_step` dropped from the document",
     lambda b: b.replace("`gaps.score_per_step`", "somewhere")),
    ("a leg added to the code and not the document (drift the other way)",
     None),
]


def main():
    body = section()
    gaps = gap_keys()
    print("LEDGER_FORMAT.md is read for:")
    print("  legs declared in the table   %s" % legs_named(body))
    print("code is read for:")
    print("  reconcile.RECONCILIATION_KEY %s" % list(RECONCILIATION_KEY))
    print("  gaps in a real report        %s" % gaps)
    print("")
    print("GREEN: %s" % (problems(body, RECONCILIATION_KEY, gaps) or "no drift"))
    print("")
    print("negative controls")
    print("-" * 70)
    for label, mutate in MUTATIONS:
        if mutate is None:
            found = problems(body, RECONCILIATION_KEY + ("turns",), gaps)
        else:
            found = problems(mutate(body), RECONCILIATION_KEY, gaps)
        print("%s" % label)
        assert found, "a mutation passed the check"
        for line in found:
            print("   RED  %s" % line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
