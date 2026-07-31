"""Adversarial counterexample probe: run the SAME synthetic paper through
whichever exam.leakage is first on sys.path, and print the metadata findings.

Run twice: PYTHONPATH=<master-worktree> and PYTHONPATH=<merged-worktree>.
"""
import json, sys, os
from exam.leakage import metadata_hits, METADATA_FIELDS
from exam.model import Item, Paper
import exam.leakage as L

print("leakage.py =", L.__file__)
print("METADATA_FIELDS =", METADATA_FIELDS)
print("has metadata_scan =", hasattr(L, "metadata_scan"))
print()


def build(case):
    """case: list of (item_id, tags, answer). All same rubric/points/paper body."""
    items = []
    answer_of = {}
    for iid, tags, ans in case:
        items.append(Item(item_id=iid, rubric_id="r1", points=1.0,
                          paper={"board": "same-for-all"},
                          truth={"solvable": ans == "yes"},
                          leak_probes=("zzz",), tags=tuple(tags)))
        answer_of[iid] = ans
    p = Paper(paper_id="ce", question_type="verdict",
              instructions="i", items=items)
    return p, answer_of


# --- CASE 1: a 100%-predictive tags leak.
# 10 items answer "yes": tags split into two REPEATED values (alpha x5, bravo x5).
# 10 items answer "no": every one has a DISTINCT tag value sharing no token.
UNIQ = ["zephyr", "kumquat", "obsidian", "marzipan", "trellis",
        "walrus", "flotsam", "gherkin", "pumice", "yardarm"]
case1 = []
for k in range(5):
    case1.append((f"y-a{k}", ["alpha"], "yes"))
for k in range(5):
    case1.append((f"y-b{k}", ["bravo"], "yes"))
for k, w in enumerate(UNIQ):
    case1.append((f"n-{k}", [w], "no"))

# --- CASE 2: same shape but on `points` (numeric, no tokens >= 3 chars share).
case2 = []
for k in range(5):
    case2.append((f"y-a{k}", [], "yes"))
for k in range(5):
    case2.append((f"y-b{k}", [], "yes"))
for k in range(10):
    case2.append((f"n-{k}", [], "no"))
# rebuild case2 with distinct points instead of tags
def build_points(case_pts):
    items = []
    answer_of = {}
    for iid, pts, ans in case_pts:
        items.append(Item(item_id=iid, rubric_id="r1", points=pts,
                          paper={"board": "same-for-all"},
                          truth={"solvable": ans == "yes"},
                          leak_probes=("zzz",), tags=()))
        answer_of[iid] = ans
    return (Paper(paper_id="ce2", question_type="verdict", instructions="i",
                  items=items), answer_of)

case2_pts = ([(f"y-a{k}", 2.0, "yes") for k in range(5)]
             + [(f"y-b{k}", 3.0, "yes") for k in range(5)]
             + [(f"n-{k}", 10.0 + k, "no") for k in range(10)])

for name, (paper, answer_of) in [
        ("CASE1 tags: repeated-value=>yes, unique-value=>no",
         build(case1)),
        ("CASE2 points: 2.0/3.0=>yes, 10..19 distinct=>no",
         build_points(case2_pts))]:
    print("=" * 70)
    print(name)
    f = metadata_hits(paper, answer_of)
    print("findings:", json.dumps(f, indent=2, sort_keys=True))
    print("N FINDINGS =", len(f))
