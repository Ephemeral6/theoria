"""CONSTRUCTED counterexample: the multiplicity->answer channel (STATUS.md open
weakness 20, "Not fixed").

Pure synthetic. No game data, no sealed pile, no network, no API.

The sheet:  8 items, 4 answered `solvable`, 4 answered `unsolvable`.
            Majority-class baseline = 0.500.
Every item's `tags` names the level it is drawn from.
  * the four `solvable` items sit on TWO reused levels, two items each
      s1,s2 -> level "orchard"      s3,s4 -> level "lattice"
  * the four `unsolvable` items each sit on their OWN level, used once
      u1 -> "stile"  u2 -> "cairn"  u3 -> "flume"  u4 -> "ridge"

The cheat rule needs no key, no board, no world:
    "if my level name occurs on another item of this sheet -> solvable"
It scores 8 of 8 against a 4-of-8 baseline.

`points` and `kind` are held constant so they cannot confound; `item_id` is
unique per item by construction, as it is on every real paper.
"""
import os
import sys
import json

sys.path.insert(0, os.getcwd())

from exam.model import Item, Paper, LeakageError          # noqa: E402
from exam import leakage as L                             # noqa: E402

LEVEL = {
    "s1": "orchard", "s2": "orchard",
    "s3": "lattice", "s4": "lattice",
    "u1": "stile", "u2": "cairn", "u3": "flume", "u4": "ridge",
}
ANSWER = {
    "s1": "solvable", "s2": "solvable", "s3": "solvable", "s4": "solvable",
    "u1": "unsolvable", "u2": "unsolvable", "u3": "unsolvable",
    "u4": "unsolvable",
}
ORDER = ["s1", "u1", "s3", "u2", "s2", "u3", "s4", "u4"]   # interleaved


def build_paper():
    items = []
    for n, short in enumerate(ORDER, start=1):
        iid = "q%02d" % n
        items.append(Item(
            item_id=iid,
            rubric_id="r-verdict",
            points=3.0,                      # constant: cannot confound
            paper={"kind": "verdict",        # constant: one answer alphabet
                   "question": "is this configuration solvable?"},
            truth={"claim": ANSWER[short]},
            leak_probes=["%s-answer-token" % short],
            tags=["level:%s" % LEVEL[short]],
        ))
    paper = Paper(paper_id="ctor-multiplicity", question_type="verdict",
                  instructions="Answer solvable or unsolvable.", items=items)
    answer_of = {it.item_id: ANSWER[short]
                 for it, short in zip(items, ORDER)}
    return paper, answer_of


def loo_score(paper, answer_of):
    """Leave-one-out on the shared-vs-unique feature.

    The feature is read off the whole sheet, which is what a cheater is handed.
    The feature->answer mapping is fitted on the other seven items only, so the
    held-out item never votes on its own rule.
    """
    ids = [i.item_id for i in paper.items]
    level_of = {i.item_id: i.tags[0] for i in paper.items}
    counts = {}
    for lv in level_of.values():
        counts[lv] = counts.get(lv, 0) + 1
    feat = {i: (counts[level_of[i]] > 1) for i in ids}   # shared?
    correct = 0
    for held in ids:
        vote = {}
        for other in ids:
            if other == held:
                continue
            vote.setdefault(feat[other], {})
            a = answer_of[other]
            vote[feat[other]][a] = vote[feat[other]].get(a, 0) + 1
        table = vote.get(feat[held])
        if not table:
            continue
        pred = max(sorted(table), key=lambda k: table[k])
        if pred == answer_of[held]:
            correct += 1
    base = max(sum(1 for i in ids if answer_of[i] == a) for a in set(answer_of.values()))
    return correct / len(ids), base / len(ids)


def main():
    paper, answer_of = build_paper()
    sheet = paper.sheet("d0" * 16, "d1" * 16)
    print("TREE:", os.path.basename(os.getcwd()))
    loo, base = loo_score(paper, answer_of)
    print("leave-one-out score  : %.3f" % loo)
    print("majority baseline    : %.3f" % base)

    hits = L.metadata_hits(paper, answer_of)
    print("metadata_hits fired  :", bool(hits), "(%d finding(s))" % len(hits))
    for h in hits:
        print("   ", json.dumps({k: v for k, v in sorted(h.items())
                                 if k != "values"}, sort_keys=True))
        if "values" in h:
            print("     values:", json.dumps(h["values"], sort_keys=True))

    try:
        rep = L.check_paper(paper, sheet, answer_of=answer_of,
                            require_probes=False)
        print("check_paper          : CLEAN (gate silent)")
        print("  metadata_unscored  :",
              json.dumps(rep.get("metadata_unscored", {}), sort_keys=True)[:600])
    except LeakageError as exc:
        print("check_paper          : RAISED LeakageError (gate fires)")
        print("  ", str(exc)[:900])


if __name__ == "__main__":
    main()
