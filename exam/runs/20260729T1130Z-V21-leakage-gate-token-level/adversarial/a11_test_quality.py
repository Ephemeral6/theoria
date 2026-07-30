"""A11 -- two tests that do not pin what their docstrings claim.

(1) `test_a_token_on_one_item_is_an_identifier_not_a_rule` passes with the
    `len(holders) < 2` guard DELETED (mutation E in a10: 0/10 tests caught it).
    Its fixture never gets anywhere near the tolerance, so the guard is never
    the reason it is green.

(2) `test_a_subset_correction_does_not_desensitise_the_token_check` asserts on
    the SOURCE TEXT of `_metadata_hits_within` -- `"floor = max(" not in src`.
    A one-character respelling reintroduces the bug and keeps the test green.
"""
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
sys.path.insert(0, REPO)

from exam import leakage
from exam.model import Item, Paper

print("=" * 72)
print("(1) test_a_token_on_one_item_is_an_identifier_not_a_rule")
print("=" * 72)
answer_of = lambda i: "dead" if i % 2 == 0 else "live"       # noqa: E731
items = [Item(item_id="q%02d" % i, rubric_id="r", points=2.0,
              paper={"kind": "probe", "body": "board %d" % i},
              truth={"claim": answer_of(i)}, leak_probes=[answer_of(i)],
              tags=("verdict", "unique%02d" % i))
         for i in range(12)]
paper = Paper(paper_id="t", question_type="verdict", instructions="", items=items)
lab = {i.item_id: i.truth["claim"] for i in paper.items}
n = len(items)
floor = Counter(lab.values()).most_common(1)[0][1] / n
print("the fixture's tokens and what they would score if the guard were gone:")
carriers = {}
for it in items:
    for t in leakage.field_tokens(it.sheet_side().get("tags")):
        carriers.setdefault(t, []).append(it)
for tok, holders in sorted(carriers.items()):
    held = {i.item_id for i in holders}
    w = Counter(lab[i.item_id] for i in holders)
    wo = Counter(lab[i.item_id] for i in items if i.item_id not in held)
    rate = ((w.most_common(1)[0][1] if w else 0)
            + (wo.most_common(1)[0][1] if wo else 0)) / n
    print("   %-12s carried_by=%-3d rate=%.3f  (needs > 0.900 and > %.3f)"
          % (tok, len(holders), rate, floor))
print()
print("Every single-holder token scores 0.583.  The tolerance is 0.900.  The")
print("test would be green with the guard deleted, so it pins nothing.")
print()
print("A fixture that WOULD pin it (see a6 M5): 11 items answer `live`, 1")
print("answers `dead`, and only the `dead` one carries the token.")
items2 = [Item(item_id="q%02d" % i, rubric_id="r", points=2.0,
               paper={"kind": "probe", "body": "b%d" % i},
               truth={"claim": "dead" if i == 0 else "live"},
               leak_probes=["v-%d" % i],
               tags=("verdict", "level:%02d" % i) + (("ridge",) if i == 0 else ()))
          for i in range(12)]
p2 = Paper(paper_id="t2", question_type="verdict", instructions="", items=items2)
l2 = {i.item_id: i.truth["claim"] for i in p2.items}
w = Counter(["dead"])
wo = Counter(["live"] * 11)
print("   ridge carried_by=1 rate=%.3f  floor=%.3f  -> would be a HIT"
      % ((1 + 11) / 12, 11 / 12))
print("   live gate says:", leakage.metadata_hits(p2, l2))

print()
print("=" * 72)
print("(2) test_a_subset_correction_does_not_desensitise_the_token_check")
print("=" * 72)
src = open(os.path.join(REPO, "exam", "leakage.py"), encoding="utf-8").read()
fn = src[src.index("def _metadata_hits_within"):src.index("#: Tokens shorter than")]
print("the assertion is:  assert \"floor = max(\" not in src")
print("current source contains it? ", "floor = max(" in fn)
for spelling in ["floor = max(floor, floor_here)",
                 "floor = floor_here = max(floor, x)",
                 "floor  =  max(floor, x)",
                 "floor = max (floor, x)",
                 "floor += max(0.0, floor_here - floor)",
                 "floor = floor_here if floor_here > floor else floor"]:
    caught = "floor = max(" in spelling
    print("   %-46s caught by the grep? %s" % (spelling, caught))
print()
print("Four of six respellings of the identical regression slip past.  a10")
print("mutation R (`floor = floor_here = max(`) is a real behavioural")
print("regression that this test does not see; only")
print("test_a_degenerate_whole_value_subset_does_not_disable_the_token_check")
print("catches it, and it catches it for a different reason.")
