"""ADV4 sweep: gate behaviour vs. an independent leak oracle, over random
synthetic verdict sheets.

Pure synthetic, seeded, deterministic. No game data, no sealed pile, no
network, no API. Writes one JSONL line per sheet to stdout so three trees can
be diffed line-by-line.

LEAK ORACLE (deliberately independent of the gate's own arithmetic): a sheet is
"leaky" if some cheat rule drawn from a fixed family scores strictly above the
majority-class baseline under leave-one-out, where the rule's feature->answer
map is refitted without the held-out item.

  family:  whole tags value (identity)
           "my whole tags value appears on another item"     (multiplicity)
           "I carry token t"  for every token t on the sheet
           "I carry a token nobody else carries"             (private marker)

That is exactly the cheat a sheet-only cheater subagent could run, so it is the
right ground truth for a leak gate.
"""
import json
import os
import random
import sys

TREE = os.path.abspath(sys.argv[1])
N_SHEETS = int(sys.argv[2]) if len(sys.argv) > 2 else 3000
sys.path.insert(0, TREE)

from exam.model import Item, Paper, LeakageError  # noqa: E402
from exam import leakage as L                     # noqa: E402

DIGEST = "d0" * 32
S, U = "solvable", "unsolvable"
VOCAB = ["gold", "silver", "bronze", "copper", "iron", "lead", "zinc", "tin",
         "ruby", "opal", "jade", "onyx"]


def loo(ids, feat, answer_of):
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
    return correct / len(ids)


def leak_oracle(paper, answer_of):
    """Best LOO over the cheat family, and the majority baseline."""
    ids = [i.item_id for i in paper.items]
    tags = {i.item_id: list(i.tags) for i in paper.items}
    counts = {}
    for i in ids:
        counts[answer_of[i]] = counts.get(answer_of[i], 0) + 1
    base = max(counts.values()) / len(ids)

    feats = {}
    feats["identity"] = {i: json.dumps(tags[i]) for i in ids}
    vc = {}
    for i in ids:
        vc[feats["identity"][i]] = vc.get(feats["identity"][i], 0) + 1
    feats["multiplicity"] = {i: vc[feats["identity"][i]] > 1 for i in ids}
    tc = {}
    for i in ids:
        for t in set(tags[i]):
            tc[t] = tc.get(t, 0) + 1
    feats["private"] = {i: any(tc[t] == 1 for t in set(tags[i])) for i in ids}
    for t in sorted(tc):
        feats["tok:" + t] = {i: (t in tags[i]) for i in ids}

    best, who = 0.0, None
    for name in sorted(feats):
        s = loo(ids, feats[name], answer_of)
        if s > best:
            best, who = s, name
    return best, base, who


def make(rng, idx):
    n = rng.choice([6, 8, 8, 10, 12])
    rows = []
    style = rng.choice(["free", "paired", "mixed", "private"])
    for k in range(n):
        answer = rng.choice([S, U])
        if style == "free":
            tags = rng.sample(VOCAB, rng.randint(1, 3))
        elif style == "paired":
            tags = [VOCAB[rng.randrange(4)]]
        elif style == "private":
            tags = ([VOCAB[rng.randrange(3)]] if rng.random() < 0.5
                    else ["uniq%02d%02d" % (idx, k)])
        else:
            tags = (rng.sample(VOCAB, rng.randint(1, 3))
                    if rng.random() < 0.6 else [VOCAB[rng.randrange(3)]])
        rows.append((answer, sorted(set(tags))))
    items = [Item(item_id="q%02d" % (j + 1), rubric_id="r", points=3.0,
                  paper={"kind": "verdict", "question": "solvable?"},
                  truth={"claim": a}, leak_probes=["zzp%d" % j], tags=t)
             for j, (a, t) in enumerate(rows)]
    paper = Paper(paper_id="sw%05d" % idx, question_type="verdict",
                  instructions="x", items=items)
    return paper, {it.item_id: a for it, (a, _) in zip(items, rows)}


def main():
    rng = random.Random(20260730)
    for idx in range(N_SHEETS):
        paper, answer_of = make(rng, idx)
        if len({answer_of[i] for i in answer_of}) < 2:
            continue
        sheet = paper.sheet(DIGEST, "d1" * 32)
        key_doc = paper.key(DIGEST)
        try:
            L.check_paper(paper, sheet, key_doc=key_doc, answer_of=answer_of)
            fired = False
        except LeakageError:
            fired = True
        best, base, who = leak_oracle(paper, answer_of)
        print(json.dumps({"id": idx, "fired": fired,
                          "loo": round(best, 6), "base": round(base, 6),
                          "leaky": best > base + 1e-9, "rule": who,
                          "tags": [sorted(i.tags) for i in paper.items],
                          "ans": [answer_of[i.item_id] for i in paper.items]},
                         sort_keys=True))


main()
