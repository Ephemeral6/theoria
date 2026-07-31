"""CONSTRUCTION C: V25's genuine GAIN -- a leak master cannot see at all.

Pure synthetic. No game data, no sealed pile, no network, no API.

8 items, 4 `solvable` / 4 `unsolvable`. Majority baseline 0.500.
Every `tags` VALUE is unique, so master's whole-value bucketing scores nothing.

  solvable   : s1 ["alpha","beta"]  s2 ["beta","gamma"]
               s3 ["gamma","delta"] s4 ["delta","alpha"]
               -> every token sits on exactly 2 items, none is a single-holder
  unsolvable : u1 ["uniqa"] u2 ["uniqb"] u3 ["uniqc"] u4 ["uniqd"]
               -> every token sits on exactly 1 item

Cheat rule, needing no key and no world:
    "if my tags carry a marker nobody else carries -> unsolvable"
scores 8 of 8 against a 4-of-8 baseline. That is the pooled private-marker cut.
"""
import os
import sys
import json

sys.path.insert(0, os.getcwd())

from exam.model import Item, Paper, LeakageError          # noqa: E402
from exam import leakage as L                             # noqa: E402

TAGS = {
    "s1": ["alpha", "beta"], "s2": ["beta", "gamma"],
    "s3": ["gamma", "delta"], "s4": ["delta", "alpha"],
    "u1": ["uniqa"], "u2": ["uniqb"], "u3": ["uniqc"], "u4": ["uniqd"],
}
ANSWER = {"s1": "solvable", "s2": "solvable", "s3": "solvable",
          "s4": "solvable", "u1": "unsolvable", "u2": "unsolvable",
          "u3": "unsolvable", "u4": "unsolvable"}
ORDER = ["s1", "u1", "s3", "u2", "s2", "u3", "s4", "u4"]


def build_paper():
    items = [Item(item_id="q%02d" % n, rubric_id="r-verdict", points=3.0,
                  paper={"kind": "verdict", "question": "solvable?"},
                  truth={"claim": ANSWER[s]},
                  leak_probes=["%s-answer-token" % s], tags=list(TAGS[s]))
             for n, s in enumerate(ORDER, start=1)]
    paper = Paper(paper_id="ctor-private-c", question_type="verdict",
                  instructions="Answer solvable or unsolvable.", items=items)
    return paper, {it.item_id: ANSWER[s] for it, s in zip(items, ORDER)}


def main():
    paper, answer_of = build_paper()
    sheet = paper.sheet("d0" * 16, "d1" * 16)
    print("TREE:", os.path.basename(os.getcwd()))
    hits = L.metadata_hits(paper, answer_of)
    print("metadata_hits fired  :", bool(hits), "(%d finding(s))" % len(hits))
    for h in hits:
        print("   ", json.dumps({k: v for k, v in sorted(h.items())
                                 if k != "values"}, sort_keys=True))
    try:
        L.check_paper(paper, sheet, answer_of=answer_of, require_probes=False)
        print("check_paper          : CLEAN (gate silent)")
    except LeakageError as exc:
        print("check_paper          : RAISED LeakageError (gate fires)")
        print("  ", str(exc)[:500])


if __name__ == "__main__":
    main()
