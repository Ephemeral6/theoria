"""B1 -- a census of every token the gate actually scores, with its exact p.

V21 published two numbers and treated neither: single-holder tokens are invisible
(`len(holders) < 2`), and small groups fire by chance (0.20 at n=4). Both debts
are about the same quantity -- how surprising is this token's alignment with the
answer? -- so before choosing a treatment, measure it.

For every paper / label set / kind-group / metadata field / token this reports:

  n          items in the group
  k          items carrying the token
  rate       the gate's statistic: (majority among carriers + majority among
             non-carriers) / n
  floor      the group's majority-class rate
  fires      what the shipped gate does today
  p_exact    P(rate_null >= rate) with the k carriers drawn uniformly at random
             from the group -- the multivariate hypergeometric null, enumerated
             exactly rather than sampled, so it is byte-reproducible
  m          how many tokens were scored in that (group, field) -- the
             multiplicity a correction would have to pay for

Nothing here imports a random number generator on purpose: a permutation null
estimated by sampling would put a seed in the artefact and a tolerance in every
downstream test. The groups are small enough to enumerate, so they are enumerated.
"""
import itertools
import json
import os
import sys
from collections import Counter
from math import comb

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))))

from exam import leakage                                          # noqa: E402
from exam.model import canonical                                  # noqa: E402
from exam.grading.registry import digest                          # noqa: E402
from exam.papers import BUILDERS, module_for                       # noqa: E402

TOLERANCE = 0.90
PAPERS = sorted(BUILDERS) + ["<handover_auto>"]


def build(qt):
    if qt == "<handover_auto>":
        from exam.papers import handover_auto
        return handover_auto.build()
    return module_for(qt).build()


def rate_of(carrier_labels, other_labels):
    """The gate's own statistic, factored out so the null uses the same one."""
    correct = 0
    if carrier_labels:
        correct += max(carrier_labels.values())
    if other_labels:
        correct += max(other_labels.values())
    return correct / (sum(carrier_labels.values()) + sum(other_labels.values()))


def p_exact(label_counts, k, observed):
    """P(rate >= observed) when the k carriers are a uniform random k-subset.

    Enumerated over how the k carriers split across the answer classes -- the
    multivariate hypergeometric -- rather than over the C(n,k) subsets, because
    the rate depends only on that split. Exact, and cheap enough that no group
    in this exam needs sampling.
    """
    classes = sorted(label_counts)
    sizes = [label_counts[c] for c in classes]
    n = sum(sizes)
    total = comb(n, k)
    if total == 0:
        return 1.0
    hits = 0
    for split in itertools.product(*[range(s + 1) for s in sizes]):
        if sum(split) != k:
            continue
        ways = 1
        for size, take in zip(sizes, split):
            ways *= comb(size, take)
        carriers = Counter({c: v for c, v in zip(classes, split) if v})
        others = Counter({c: sizes[i] - split[i]
                          for i, c in enumerate(classes) if sizes[i] - split[i]})
        if rate_of(carriers, others) >= observed - 1e-12:
            hits += ways
    return hits / total


def census():
    rows = []
    for qt in PAPERS:
        paper = build(qt)
        key_doc = paper.key(digest())
        label_sets = dict(leakage.derive_label_sets(paper, key_doc))
        # `check_paper` also checks the *declared* label set when the paper
        # module offers one. Only `handover_auto` does -- the four shipped
        # papers implement no `answer_labels`, so for them the derived sets are
        # the whole of the check. Leaving it out would have made this census
        # quietly narrower than the gate it claims to be measuring.
        declared = getattr(module_for(paper.question_type), "answer_labels", None)
        if qt == "<handover_auto>":
            from exam.papers import handover_auto
            declared = handover_auto.answer_labels
        if declared is not None:
            label_sets["<declared>"] = declared(paper, key_doc)
        for source, answer_of in sorted(label_sets.items()):
            for group in leakage._by_answer_alphabet(paper, answer_of):
                n = len(group)
                if n < 4:
                    continue
                counts = Counter(answer_of[i.item_id] for i in group)
                if len(counts) < 2:
                    continue
                floor = max(counts.values()) / n
                for field in leakage.METADATA_FIELDS:
                    carriers = {}
                    for item in group:
                        for tok in leakage.field_tokens(
                                item.sheet_side().get(field)):
                            carriers.setdefault(tok, []).append(item)
                    # what the shipped gate scores: 2 <= k < n
                    scored = {t: h for t, h in carriers.items()
                              if 2 <= len(h) < n}
                    m = len(scored)
                    for tok, holders in sorted(carriers.items()):
                        k = len(holders)
                        if k == n:
                            continue          # constant: no rule either way
                        held = {i.item_id for i in holders}
                        with_t = Counter(answer_of[i.item_id] for i in holders)
                        without = Counter(answer_of[i.item_id] for i in group
                                          if i.item_id not in held)
                        rate = rate_of(with_t, without)
                        rows.append({
                            "paper": qt, "label_set": source,
                            "group_n": n, "field": field, "token": tok,
                            "k": k, "rate": round(rate, 6),
                            "floor": round(floor, 6),
                            "scored_today": k >= 2,
                            "fires_today": (k >= 2 and rate > TOLERANCE
                                            and rate > floor + 1e-9),
                            "p_exact": round(p_exact(counts, k, rate), 8),
                            "m_scored_in_field": m,
                        })
    return rows


def main():
    rows = census()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "token_census.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, indent=2, sort_keys=True)
        fh.write("\n")

    fires = [r for r in rows if r["fires_today"]]
    singles = [r for r in rows if r["k"] == 1]
    print("tokens enumerated            %d" % len(rows))
    print("scored by the shipped gate   %d" % sum(1 for r in rows if r["scored_today"]))
    print("single-holder (k=1, unscored) %d" % len(singles))
    print("fires today                  %d" % len(fires))
    print()

    print("-- group sizes actually scored --")
    ns = Counter(r["group_n"] for r in rows if r["scored_today"])
    for n, c in sorted(ns.items()):
        print("  n=%-3d  %d scored tokens" % (n, c))
    print()

    print("-- multiplicity per (paper, label_set, group, field) --")
    ms = Counter(r["m_scored_in_field"] for r in rows if r["scored_today"])
    for m, c in sorted(ms.items()):
        print("  m=%-3d  %d tokens" % (m, c))
    print("  max m = %d" % (max(ms) if ms else 0))
    print()

    print("-- what a single-holder token's p looks like (the M5 blind spot) --")
    by_p = sorted(singles, key=lambda r: r["p_exact"])[:8]
    for r in by_p:
        print("  p=%-10.6f n=%-3d rate=%-8.4f floor=%-8.4f %s/%s %s"
              % (r["p_exact"], r["group_n"], r["rate"], r["floor"],
                 r["paper"], r["field"], r["token"]))
    if not singles:
        print("  (none)")
    print()

    print("-- the most surprising scored tokens on real papers --")
    for r in sorted((r for r in rows if r["scored_today"]),
                    key=lambda r: r["p_exact"])[:10]:
        print("  p=%-10.6f n=%-3d k=%-3d rate=%-8.4f floor=%-8.4f fires=%-5s %s/%s %s"
              % (r["p_exact"], r["group_n"], r["k"], r["rate"], r["floor"],
                 r["fires_today"], r["paper"], r["field"], r["token"]))
    print()
    print("wrote %s" % out)


if __name__ == "__main__":
    main()
