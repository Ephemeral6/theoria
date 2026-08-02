"""Scratch: can the name-keying defect be re-installed and measured without Lean?

If yes, the negative control the V28 item demands ("put a name-based kind
classifier back and the vacuous/discharged verdicts must flip") can be an
EXECUTED mutation rather than an argument in a docstring.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "exam"))

from freeze import theorem_shape, u3  # noqa: E402
import tests.test_u3_census as T  # noqa: E402  (reuse the fixtures)

sys.path.insert(0, str(REPO / "exam" / "tests"))


def judge(src, axioms):
    return u3.judge_development(
        compiles=True, axiom_report=axioms, lean_src=src,
        probe_result=None, recorded={}, evidence={})


def axioms_for(src):
    dev = theorem_shape.parse_development(src)
    return {name: [] for name in dev.theorems}


for label, src in (("REAL_MANUAL", T.REAL_MANUAL),
                   ("ODDLY_NAMED_MANUAL", T.ODDLY_NAMED_MANUAL),
                   ("TAUTOLOGY_MANUAL", T.TAUTOLOGY_MANUAL)):
    v = judge(src, axioms_for(src))
    dev = theorem_shape.parse_development(src)
    print("%-20s label=%-14s kinds=%s hints=%s" % (
        label, v["label"],
        sorted({t.kind for t in dev.theorems.values()}),
        sorted({theorem_shape.name_hint(n) for n in dev.theorems})))

print()
print("=== now re-install name keying ===")
_real = theorem_shape._classify


def _name_keyed(thm, dev):
    hint = theorem_shape.name_hint(thm.name)
    if hint is None:
        return theorem_shape.UNCLASSIFIED_KIND, {"rule": "name matcher: no prefix"}
    return hint, dict(_real(thm, dev)[1])


theorem_shape._classify = _name_keyed
try:
    for label, src in (("REAL_MANUAL", T.REAL_MANUAL),
                       ("ODDLY_NAMED_MANUAL", T.ODDLY_NAMED_MANUAL)):
        v = judge(src, axioms_for(src))
        print("%-20s label=%s" % (label, v["label"]))
finally:
    theorem_shape._classify = _real
