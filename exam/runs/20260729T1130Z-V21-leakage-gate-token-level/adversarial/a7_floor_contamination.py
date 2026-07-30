"""A7 -- `floor` is assigned once before the field loop and RAISED inside it,
so it leaks from one metadata field into the next and into the token check.

exam/leakage.py:283   floor = majority / len(labelled)     # once, per group
exam/leakage.py:287   for field_name in METADATA_FIELDS:   # points, tags, kind
exam/leakage.py:334       floor = max(floor, floor_here)   # never reset

`floor_here` is computed over *that field's* scored subset.  A field whose
scored subset happens to be lopsided therefore raises the bar for every later
field, and for the token check of the same field, which scores over the WHOLE
group.  Comparing a whole-group rate against a subset-derived floor is a
category error, and it silently suppresses findings.

Construction:
  * 50 items, 25 `dead` / 25 `live`  ->  group floor 0.500
  * `points` (first field): two scored buckets covering 20 items, 19 of them
    `dead`.  rate = floor_here = 0.950, so `points` is correctly NOT flagged --
    but `floor` is now 0.950 for everything that follows.
  * `tags` (second field): the token `ridge` predicts 47 of 50 = 0.940.
    0.940 > tolerance 0.900 and 0.940 > the real floor 0.500  ->  a leak.
    0.940 > 0.950 is false  ->  SUPPRESSED.
"""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))

from exam import leakage
from exam.model import Item, LeakageError, Paper

N = 50
answers = ["dead"] * 25 + ["live"] * 25

# points: items 0..9 -> 2.0 (all dead); items 10..18 -> 3.0 (dead);
# item 49 -> 3.0 (live).  Everyone else gets a unique two-decimal value whose
# tokens are all shorter than MIN_TOKEN, so `points` contributes no tokens.
points = {}
for i in range(10):
    points[i] = 2.0
for i in range(10, 19):
    points[i] = 3.0
points[49] = 3.0
spare = [i for i in range(N) if i not in points]
for k, i in enumerate(spare):
    points[i] = round(4.0 + (k + 1) / 100.0, 2)

# tags: `ridge` on 23 dead + 1 live (24 items).  Unique level:NN keeps every
# whole value a singleton so the value-level check scores nothing here.
RIDGE = set(range(23)) | {25}


def tags_of(i):
    base = ("verdict", "level:%02d" % i)
    return base + (("ridge",) if i in RIDGE else ())


items = [Item(item_id="q%02d" % i, rubric_id="r", points=points[i],
              paper={"kind": "probe", "body": "board %d" % i},
              truth={"claim": answers[i]}, leak_probes=["v-%d" % i],
              tags=tags_of(i))
         for i in range(N)]
paper = Paper(paper_id="A7", question_type="verdict", instructions="",
              items=items)
lab = {i.item_id: i.truth["claim"] for i in paper.items}

with_tok = Counter(answers[i] for i in range(N) if i in RIDGE)
without = Counter(answers[i] for i in range(N) if i not in RIDGE)
rate = (with_tok.most_common(1)[0][1] + without.most_common(1)[0][1]) / N
print("group floor              :", Counter(answers).most_common(1)[0][1] / N)
print("`ridge` with_token       :", dict(with_tok))
print("`ridge` without_token    :", dict(without))
print("`ridge` predicts         :", rate, " (tolerance 0.90)")
print()

pts_buckets = Counter()
for i in range(N):
    pts_buckets[points[i]] += 1
usable = {v: c for v, c in pts_buckets.items() if c > 1}
scored = Counter(answers[i] for i in range(N) if points[i] in usable)
seen = sum(scored.values())
print("points scored subset     :", dict(scored), "seen =", seen)
print("points floor_here        :", scored.most_common(1)[0][1] / seen)
print()

hits = leakage.metadata_hits(paper, lab)
print("metadata_hits            :", hits)
print("token hits               :", [h for h in hits if "token" in h])
try:
    leakage.check_paper(paper, paper.sheet("d"), answer_of=lab)
    print("check_paper              : GREEN  <-- 0.940 leak suppressed by a")
    print("                           floor another field computed")
except LeakageError as exc:
    print("check_paper              : RED", str(exc)[:160])

print()
print("--- same paper, `points` made constant so nothing can raise the floor ---")
items2 = [Item(item_id=i.item_id, rubric_id="r", points=2.0, paper=i.paper,
               truth=i.truth, leak_probes=i.leak_probes, tags=i.tags)
          for i in paper.items]
paper2 = Paper(paper_id="A7b", question_type="verdict", instructions="",
               items=items2)
h2 = leakage.metadata_hits(paper2, lab)
print("token hits               :", [(h["field"], h["token"], h["predicts"],
                                      h["majority_floor"]) for h in h2
                                     if "token" in h])
