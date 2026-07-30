"""B2 -- run three candidate rules side by side on the cases that decide V25.

The item proposes two treatments and warns they pull in opposite directions.
Before implementing either, put all three rules on the same fixtures and read
what each one does:

  gate      what ships today: in-sample rate = (majority among carriers +
            majority among non-carriers)/n, fired when rate > 0.90 and
            rate > floor. Blind to k=1 by an explicit guard.
  loo       a12's route, which ADVERSARIAL.md nominates as the correct fix for
            the single-holder class: leave-one-out accuracy of "predict the
            majority of my own group", **abstention scored wrong**, against the
            leave-one-out majority-class baseline, margin 0.25. No guard.
  exact     the same in-sample statistic, but fired on an exact p-value under
            the hypergeometric null, Bonferroni-corrected by the number of
            tokens scored in that field.

The cases:

  DIRTY    V21's negative control 1 -- 12 items, 6 dead / 6 live, the token
           `dead` on exactly the dead ones, every whole value made unique by a
           per-item `level:NN`. Every rule MUST fire.
  CLEAN    V21's negative control 2 -- same shape, token uncorrelated. Every
           rule MUST stay silent.
  M5       the single-holder blind spot the item is about -- 12 items, 1 dead,
           and the token `ridge` sits on exactly that one item.
  M5_ID    the same paper, but the token is `q07`, a per-item identifier that
           happens to sit on the dead item. **This is the control that decides
           the whole question**: if a rule cannot separate M5 from M5_ID it has
           not fixed the blind spot, it has only moved it.
"""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))))

from exam import leakage                                          # noqa: E402
from exam.model import Item, Paper                                # noqa: E402

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))), "tests"))

from b1_token_census import p_exact, rate_of                       # noqa: E402

MARGIN = 0.25
TOLERANCE = 0.90


def paper_of(tag_of, answer_of, n=12):
    items = [
        Item(item_id="q%02d" % i, rubric_id="r", points=2.0,
             paper=({"kind": "probe", "body": "board %d" % i}),
             truth={"claim": answer_of(i)},
             leak_probes=[answer_of(i)],
             tags=tuple(tag_of(i)))
        for i in range(n)
    ]
    return Paper(paper_id="v25", question_type="verdict",
                 instructions="", items=items)


def labels_of(paper):
    return {i.item_id: i.truth["claim"] for i in paper.items}


# ------------------------------------------------------------------ the rules

def gate_rule(group, answer_of, token, holders):
    """Exactly `_token_hits_within`'s arithmetic, including its k>=2 guard."""
    n = len(group)
    k = len(holders)
    counts = Counter(answer_of[i.item_id] for i in group)
    floor = max(counts.values()) / n
    if k < 2 or k == n:
        return {"fires": False, "why": "guard: k=%d" % k, "rate": None,
                "floor": round(floor, 4)}
    held = {i.item_id for i in holders}
    with_t = Counter(answer_of[i.item_id] for i in holders)
    without = Counter(answer_of[i.item_id] for i in group
                      if i.item_id not in held)
    rate = rate_of(with_t, without)
    return {"fires": rate > TOLERANCE and rate > floor + 1e-9,
            "rate": round(rate, 4), "floor": round(floor, 4), "why": ""}


def loo_partition(labels, groups):
    """a12's predictor, transcribed. An item with no peers is scored WRONG."""
    n = len(labels)
    hit = 0
    for i in range(n):
        peers = [labels[j] for j in range(n) if j != i and groups[j] == groups[i]]
        if not peers:
            continue
        if Counter(peers).most_common(1)[0][0] == labels[i]:
            hit += 1
    return hit / n


def loo_baseline(labels):
    n = len(labels)
    hit = 0
    for i in range(n):
        rest = Counter(labels[:i] + labels[i + 1:])
        if rest and rest.most_common(1)[0][0] == labels[i]:
            hit += 1
    return hit / n


def loo_rule(group, answer_of, token, holders):
    ids = sorted(i.item_id for i in group)
    labels = [answer_of[i] for i in ids]
    held = {i.item_id for i in holders}
    groups = [i in held for i in ids]
    acc = loo_partition(labels, groups)
    base = loo_baseline(labels)
    return {"fires": acc >= base + MARGIN, "acc": round(acc, 4),
            "base": round(base, 4), "why": ""}


def exact_rule(group, answer_of, token, holders, m):
    n = len(group)
    k = len(holders)
    counts = Counter(answer_of[i.item_id] for i in group)
    if k == n:
        return {"fires": False, "why": "constant", "p": None, "p_adj": None}
    held = {i.item_id for i in holders}
    with_t = Counter(answer_of[i.item_id] for i in holders)
    without = Counter(answer_of[i.item_id] for i in group
                      if i.item_id not in held)
    rate = rate_of(with_t, without)
    p = p_exact(counts, k, rate)
    p_adj = min(1.0, p * m)
    return {"fires": p_adj < 0.05, "p": round(p, 6), "p_adj": round(p_adj, 6),
            "why": "m=%d" % m}


# ------------------------------------------------------------------ the cases

def case(name, tag_of, answer_of, focus, n=12):
    paper = paper_of(tag_of, answer_of, n=n)
    answers = labels_of(paper)
    group = list(paper.items)
    carriers = {}
    for item in group:
        for tok in leakage.field_tokens(item.sheet_side().get("tags")):
            carriers.setdefault(tok, []).append(item)
    m = sum(1 for t, h in carriers.items() if 2 <= len(h) < len(group))
    holders = carriers.get(focus, [])
    print("== %s -- token %r carried by %d of %d" % (name, focus, len(holders),
                                                     len(group)))
    print("   answer counts: %s" % dict(Counter(answers.values())))
    g = gate_rule(group, answers, focus, holders)
    l = loo_rule(group, answers, focus, holders)
    e = exact_rule(group, answers, focus, holders, max(m, 1))
    print("   gate   fires=%-5s rate=%s floor=%s %s"
          % (g["fires"], g["rate"], g["floor"], g["why"]))
    print("   loo    fires=%-5s acc=%s base=%s (margin %.2f)"
          % (l["fires"], l["acc"], l["base"], MARGIN))
    print("   exact  fires=%-5s p=%s p_adj=%s %s"
          % (e["fires"], e["p"], e["p_adj"], e["why"]))
    print()
    return {"case": name, "token": focus, "k": len(holders),
            "gate": g, "loo": l, "exact": e}


def main():
    rows = []
    # V21 negative control 1: a real token leak. Every rule must fire.
    rows.append(case(
        "DIRTY (V21 neg-control 1)",
        lambda i: ("verdict", "level:%02d" % i, "dead" if i < 6 else "live"),
        lambda i: "dead" if i < 6 else "live", "dead"))

    # V21 negative control 2: clean. No rule may fire.
    rows.append(case(
        "CLEAN (V21 neg-control 2)",
        lambda i: ("verdict", "level:%02d" % i, "odd" if i % 2 else "even"),
        lambda i: "dead" if i < 6 else "live", "odd"))

    # M5: the single-holder blind spot. `ridge` sits on the one dead item.
    rows.append(case(
        "M5 (real single-holder leak)",
        lambda i: (("verdict", "level:%02d" % i, "ridge") if i == 7
                   else ("verdict", "level:%02d" % i)),
        lambda i: "dead" if i == 7 else "live", "ridge"))

    # M5_ID: the control. A per-item identifier on the same item. If a rule
    # fires here it has not fixed the blind spot, it has produced a rule that
    # flags every bookkeeping token that lands on a minority-class item.
    rows.append(case(
        "M5_ID (identifier on the same item)",
        lambda i: ("verdict", "level:%02d" % i, "tag%02d" % i),
        lambda i: "dead" if i == 7 else "live", "tag07"))

    print("=" * 70)
    print("VERDICT TABLE   (must-fire: DIRTY, M5 | must-not-fire: CLEAN, M5_ID)")
    print("=" * 70)
    print("%-38s %-7s %-7s %-7s" % ("case", "gate", "loo", "exact"))
    for r in rows:
        print("%-38s %-7s %-7s %-7s"
              % (r["case"], r["gate"]["fires"], r["loo"]["fires"],
                 r["exact"]["fires"]))
    print()
    want = {"DIRTY (V21 neg-control 1)": True,
            "CLEAN (V21 neg-control 2)": False,
            "M5 (real single-holder leak)": True,
            "M5_ID (identifier on the same item)": False}
    for rule in ("gate", "loo", "exact"):
        wrong = [r["case"] for r in rows if r[rule]["fires"] != want[r["case"]]]
        print("%-7s %s" % (rule, "ALL FOUR CORRECT" if not wrong
                           else "wrong on: %s" % ", ".join(wrong)))


if __name__ == "__main__":
    main()
