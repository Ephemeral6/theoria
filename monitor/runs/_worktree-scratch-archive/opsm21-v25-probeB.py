"""CONSTRUCTION B: the same multiplicity->answer channel, but with NO
single-holder token anywhere -- so V25's pooled private-marker cut cannot see it.

Pure synthetic. No game data, no sealed pile, no network, no API.

8 items, 4 `solvable` / 4 `unsolvable`. Majority baseline 0.500.
`tags` is a LIST, as it is on real papers.

  solvable   : s1,s2 -> ["gold"]            s3,s4 -> ["silver"]
               (the whole VALUE is shared by two items)
  unsolvable : u1 -> ["red","blue"]         u2 -> ["blue","green"]
               u3 -> ["green","red"]        u4 -> ["red","blue","green"]
               (every whole VALUE is unique, but every TOKEN is on 3 items,
                so not one token is a single-holder)

Cheat rule, needing no key and no world:
    "if my tags value occurs verbatim on another item -> solvable"
scores 8 of 8 against a 4-of-8 baseline. It is open weakness 20's channel
(multiplicity -> answer) exactly.
"""
import os
import sys
import json

sys.path.insert(0, os.getcwd())

from exam.model import Item, Paper, LeakageError          # noqa: E402
from exam import leakage as L                             # noqa: E402

TAGS = {
    "s1": ["gold"], "s2": ["gold"],
    "s3": ["silver"], "s4": ["silver"],
    "u1": ["red", "blue"], "u2": ["blue", "green"],
    "u3": ["green", "red"], "u4": ["red", "blue", "green"],
}
ANSWER = {
    "s1": "solvable", "s2": "solvable", "s3": "solvable", "s4": "solvable",
    "u1": "unsolvable", "u2": "unsolvable", "u3": "unsolvable",
    "u4": "unsolvable",
}
ORDER = ["s1", "u1", "s3", "u2", "s2", "u3", "s4", "u4"]


def build_paper():
    items = []
    for n, short in enumerate(ORDER, start=1):
        items.append(Item(
            item_id="q%02d" % n,
            rubric_id="r-verdict",
            points=3.0,
            paper={"kind": "verdict",
                   "question": "is this configuration solvable?"},
            truth={"claim": ANSWER[short]},
            leak_probes=["%s-answer-token" % short],
            tags=list(TAGS[short]),
        ))
    paper = Paper(paper_id="ctor-multiplicity-b", question_type="verdict",
                  instructions="Answer solvable or unsolvable.", items=items)
    answer_of = {it.item_id: ANSWER[s] for it, s in zip(items, ORDER)}
    return paper, answer_of


def loo_score(paper, answer_of):
    ids = [i.item_id for i in paper.items]
    val = {i.item_id: json.dumps(list(i.tags)) for i in paper.items}
    counts = {}
    for v in val.values():
        counts[v] = counts.get(v, 0) + 1
    feat = {i: (counts[val[i]] > 1) for i in ids}
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
        if max(sorted(table), key=lambda k: table[k]) == answer_of[held]:
            correct += 1
    base = max(sum(1 for i in ids if answer_of[i] == a)
               for a in set(answer_of.values()))
    return correct / len(ids), base / len(ids)


def main():
    paper, answer_of = build_paper()
    sheet = paper.sheet("d0" * 16, "d1" * 16)
    print("TREE:", os.path.basename(os.getcwd()))
    loo, base = loo_score(paper, answer_of)
    print("leave-one-out score  : %.3f" % loo)
    print("majority baseline    : %.3f" % base)

    # show token carrier structure so the reader can check "no single holders"
    lab = list(paper.items)
    cov = getattr(L, "single_holder_coverage", None)
    if cov:
        print("tags token coverage  :",
              json.dumps(cov(lab, answer_of, "tags"), sort_keys=True))

    hits = L.metadata_hits(paper, answer_of)
    print("metadata_hits fired  :", bool(hits), "(%d finding(s))" % len(hits))
    for h in hits:
        print("   ", json.dumps({k: v for k, v in sorted(h.items())
                                 if k != "values"}, sort_keys=True))
        if "values" in h:
            print("     values:", json.dumps(h["values"], sort_keys=True))

    try:
        L.check_paper(paper, sheet, answer_of=answer_of, require_probes=False)
        print("check_paper          : CLEAN (gate silent)")
    except LeakageError as exc:
        print("check_paper          : RAISED LeakageError (gate fires)")
        print("  ", str(exc)[:700])


if __name__ == "__main__":
    main()
