"""ADV4 control: does master's fire on construction B require a leak?

Construction E is built so that master's whole-value check lands in EXACTLY the
same degenerate state it lands in on B -- two `tags` buckets of two items each,
both entirely one answer, everything else a dropped singleton -- while the
multiplicity feature that B leaks through carries NO exploitable signal:
leave-one-out is at or below the majority baseline.

If master fires on E, then "master fires on B" is not the same proposition as
"master detects B's leak": the fire is a function of the degenerate subset, not
of the leak.

Pure synthetic. No game data, no sealed pile, no network, no API.
"""
import json
import os
import sys

TREE = os.path.abspath(sys.argv[1])
sys.path.insert(0, TREE)

from exam.model import Item, Paper, LeakageError  # noqa: E402
from exam import leakage as L                     # noqa: E402

DIGEST = "d0" * 32


def build(paper_id, rows):
    """rows: list of (answer, tags)."""
    items = [Item(item_id="q%02d" % n, rubric_id="r-verdict", points=3.0,
                  paper={"kind": "verdict", "question": "solvable?"},
                  truth={"claim": a}, leak_probes=["zzp-%d" % n], tags=list(t))
             for n, (a, t) in enumerate(rows, start=1)]
    paper = Paper(paper_id=paper_id, question_type="verdict",
                  instructions="Answer solvable or unsolvable.", items=items)
    return paper, {it.item_id: a for it, (a, _t) in zip(items, rows)}


def loo_shared_value(paper, answer_of):
    ids = [i.item_id for i in paper.items]
    val = {i.item_id: json.dumps(list(i.tags)) for i in paper.items}
    c = {}
    for v in val.values():
        c[v] = c.get(v, 0) + 1
    feat = {i: (c[val[i]] > 1) for i in ids}
    correct = 0
    for held in ids:
        table = {}
        for o in ids:
            if o == held:
                continue
            table.setdefault(feat[o], {})
            table[feat[o]][answer_of[o]] = table[feat[o]].get(answer_of[o], 0) + 1
        row = table.get(feat[held])
        if row and max(sorted(row), key=lambda k: row[k]) == answer_of[held]:
            correct += 1
    counts = {}
    for i in ids:
        counts[answer_of[i]] = counts.get(answer_of[i], 0) + 1
    return correct / len(ids), max(counts.values()) / len(ids)


S, U = "solvable", "unsolvable"

# --- E: master's degenerate n=4 shape, but the multiplicity feature is useless.
#     shared pairs: gold(2 solvable), silver(2 solvable)
#     singletons  : 2 solvable, 2 unsolvable  -> "shared?" predicts nothing new
E_ROWS = [
    (S, ["gold"]), (S, ["gold"]),
    (S, ["silver"]), (S, ["silver"]),
    (S, ["one"]), (S, ["two"]),
    (U, ["three"]), (U, ["four"]),
]

# --- F: same idea, wider. shared pairs all solvable; six singletons split 3/3.
F_ROWS = [
    (S, ["gold"]), (S, ["gold"]),
    (S, ["silver"]), (S, ["silver"]),
    (S, ["a1"]), (S, ["a2"]), (S, ["a3"]),
    (U, ["b1"]), (U, ["b2"]), (U, ["b3"]),
]

# --- B, for side-by-side.
B_ROWS = [
    (S, ["gold"]), (U, ["red", "blue"]),
    (S, ["silver"]), (U, ["blue", "green"]),
    (S, ["gold"]), (U, ["green", "red"]),
    (S, ["silver"]), (U, ["red", "blue", "green"]),
]


def run(name, rows):
    paper, answer_of = build("adv4-" + name, rows)
    sheet = paper.sheet(DIGEST, "d1" * 32)
    key_doc = paper.key(DIGEST)
    s, b = loo_shared_value(paper, answer_of)
    print("-" * 72)
    print("%s  n=%d  LOO[shared-value]=%.3f  majority baseline=%.3f  %s"
          % (name, len(rows), s, b,
             "LEAK" if s > b + 1e-9 else "NO EXPLOITABLE SIGNAL"))
    try:
        L.check_paper(paper, sheet, key_doc=key_doc, answer_of=answer_of)
        print("   gate: SILENT")
    except LeakageError as exc:
        print("   gate: FIRES")
        print("     " + str(exc)[:520])


print("### tree=%s  METADATA_FIELDS=%s" % (os.path.basename(TREE),
                                           L.METADATA_FIELDS))
run("B  (the disputed case)", B_ROWS)
run("E  (control, no signal)", E_ROWS)
run("F  (control, no signal)", F_ROWS)
