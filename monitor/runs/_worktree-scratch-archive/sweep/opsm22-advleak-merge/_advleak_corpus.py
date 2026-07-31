"""Generate a deterministic corpus of synthetic verdict papers, including
planted leaks, and write it as JSON.  No API, no sealed-pile contact: every
board string is the literal "b".
"""
import json
import random
import sys

ANSWERS = ["true", "false", "maybe"]


def gen(rng, idx):
    n = rng.randint(4, 14)
    n_ans = rng.choice([2, 2, 2, 3])
    n_kind = rng.choice([1, 1, 1, 2])
    # how strongly the metadata leaks: 0 = clean, 1 = partial, 2 = total
    leak = rng.choice([0, 1, 2, 2])
    carrier = rng.choice(["points", "tags"])
    items = []
    for i in range(n):
        ans = ANSWERS[rng.randrange(n_ans)]
        kind = "k%d" % rng.randrange(n_kind)
        # points: sometimes a function of the answer (the shipped 2-vs-3 leak)
        if carrier == "points" and leak == 2:
            pts = 2.0 + ANSWERS.index(ans)
        elif carrier == "points" and leak == 1:
            pts = 2.0 + (ANSWERS.index(ans) if rng.random() < 0.8
                         else rng.randrange(n_ans))
        else:
            pts = float(rng.choice([2, 2, 3, 3]))
        tags = []
        # a per-item unique token: this is what makes whole-value bucketing blind
        if rng.random() < 0.5:
            tags.append("id%02d" % i)
        if carrier == "tags" and leak == 2:
            tags.append("ans-%s" % ans)
        elif carrier == "tags" and leak == 1:
            tags.append("ans-%s" % (ans if rng.random() < 0.8
                                    else ANSWERS[rng.randrange(n_ans)]))
        if rng.random() < 0.4:
            tags.append(rng.choice(["alpha", "beta", "gamma"]))
        items.append({"item_id": "q%02d" % i, "points": pts, "kind": kind,
                      "tags": tags, "answer": ans})
    return {"id": "case-%05d" % idx, "items": items}


def main():
    count = int(sys.argv[1])
    out = sys.argv[2]
    rng = random.Random(20260730)
    corpus = [gen(rng, i) for i in range(count)]
    # --- hand-built adversarial cases, aimed at the two suppression paths ----
    # (H1) whole-value rate exactly equals the SCORED subset's majority rate,
    # while the whole GROUP floor is lower because singleton items were dropped.
    # master compares rate against the group floor -> fires.  merge compares it
    # against the scored-subset floor -> silent.
    h1 = []
    for i in range(10):                      # bucket A: ten items, all "true"
        h1.append({"item_id": "a%02d" % i, "points": 2.0, "kind": "k0",
                   "tags": ["shared-a"], "answer": "true"})
    for i in range(9):                       # bucket B: nine "true"
        h1.append({"item_id": "b%02d" % i, "points": 3.0, "kind": "k0",
                   "tags": ["shared-b"], "answer": "true"})
    h1.append({"item_id": "b99", "points": 3.0, "kind": "k0",
               "tags": ["shared-b"], "answer": "false"})
    for i in range(6):                       # six singleton points -> dropped
        h1.append({"item_id": "s%02d" % i, "points": 10.0 + i, "kind": "k0",
                   "tags": ["u%02d" % i], "answer": "false"})
    corpus.append({"id": "hand-H1-floor-denominator", "items": h1})
    # (H2) the single-category scored subset (the known degenerate class), kept
    # as a positive control that the probe can see it.
    h2 = []
    for i in range(3):
        h2.append({"item_id": "p%02d" % i, "points": 2.0, "kind": "k0",
                   "tags": ["t%02d" % i], "answer": "true"})
        h2.append({"item_id": "q%02d" % i, "points": 3.0, "kind": "k0",
                   "tags": ["t%02d" % i], "answer": "true"})
    h2.append({"item_id": "z0", "points": 9.0, "kind": "k0",
               "tags": ["zz"], "answer": "false"})
    h2.append({"item_id": "z1", "points": 8.0, "kind": "k0",
               "tags": ["zy"], "answer": "false"})
    corpus.append({"id": "hand-H2-single-category-subset", "items": h2})
    # (H3) the real 2-vs-3 points leak, no singletons: both must fire.
    h3 = [{"item_id": "r%02d" % i, "points": 2.0 if i < 5 else 3.0,
           "kind": "k0", "tags": ["x"],
           "answer": "true" if i < 5 else "false"} for i in range(10)]
    corpus.append({"id": "hand-H3-points-leak", "items": h3})
    json.dump(corpus, open(out, "w", encoding="utf-8"))
    print("wrote %d cases to %s" % (len(corpus), out))


if __name__ == "__main__":
    main()
