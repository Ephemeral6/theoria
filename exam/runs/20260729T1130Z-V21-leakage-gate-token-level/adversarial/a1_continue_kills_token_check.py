"""A1 -- the degenerate-subset `continue` disables the token check for that field.

exam/leakage.py:331-332

    if len(scored) < 2:
        continue          # <-- next field_name, NOT next bucket

That `continue` is inside the `for field_name in METADATA_FIELDS` loop, and the
token-level call sits *after* it (line 361).  So any field whose scored subset
collapses to one answer now skips the token check entirely -- the exact fix for
the v11-handover-a0 false positive punched a hole in the feature the item was
raised to add.

Demo: `tags` carries a real `dead`/`live` token leak AND has a whole-value
scored subset with one answer left.  The token check never runs.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))

from exam import leakage
from exam.model import Item, LeakageError, Paper


def paper(tag_of, answer_of, n):
    items = [
        Item(item_id="q%02d" % i, rubric_id="r", points=2.0,
             paper={"kind": "probe", "body": "board %d" % i},
             truth={"claim": answer_of(i)}, leak_probes=[answer_of(i)],
             tags=tuple(tag_of(i)))
        for i in range(n)
    ]
    return Paper(paper_id="a1", question_type="verdict", instructions="",
                 items=items)


def labels(p):
    return {i.item_id: i.truth["claim"] for i in p.items}


# 10 items: 5 dead, 5 live.  `dead`/`live` is the leak (perfect predictor).
# The whole-value buckets are engineered so that after singletons are dropped
# the surviving subset is all-`dead`: items 0..3 share two paired shapes that
# are all dead; items 4..9 each carry a unique `level:NN` and are singletons.
# The leaking token is `ridge`/`gorge`, NOT the answer word, so check 1
# (declared probes) has nothing to find and the gate rests on the metadata
# check alone -- which is the situation the whole item is about.
def tag_of(i):
    if i < 4:
        return ("verdict", "pair%d" % (i // 2), "ridge")
    if i < 5:
        return ("verdict", "level:%02d" % i, "ridge")
    return ("verdict", "level:%02d" % i, "gorge")


answer_of = lambda i: "dead" if i < 5 else "live"   # noqa: E731

p = paper(tag_of, answer_of, 10)
lab = labels(p)

hits = leakage.metadata_hits(p, lab)
print("METADATA_FIELDS order :", leakage.METADATA_FIELDS)
print("tags per item         :")
for it in p.items:
    print("   ", it.item_id, list(it.tags), "->", lab[it.item_id])
print()
print("hits                  :", hits)
print("token hits            :", [h for h in hits if "token" in h])
print()
print("Is `ridge` a perfect predictor?  carriers =",
      sorted(i.item_id for i in p.items if "ridge" in
             leakage.field_tokens(i.sheet_side().get("tags"))))
print("their answers          =",
      sorted({lab[i.item_id] for i in p.items if "ridge" in
              leakage.field_tokens(i.sheet_side().get("tags"))}))
print()
try:
    leakage.check_paper(p, p.sheet("d"), answer_of=lab)
    print("check_paper: GREEN  <-- the gate passed a paper whose `tags`")
    print("            field literally spells the answer on every item")
except LeakageError as exc:
    print("check_paper: RED", str(exc)[:200])

# Control: the same leak with no degenerate subset IS caught.
print()
print("--- control: identical leak, no singleton collapse ---")
p2 = paper(lambda i: ("verdict", "level:%02d" % i,
                      "ridge" if i < 5 else "gorge"), answer_of, 10)
h2 = leakage.metadata_hits(p2, labels(p2))
print("token hits            :", [(h["field"], h["token"], h["predicts"])
                                  for h in h2 if "token" in h])
