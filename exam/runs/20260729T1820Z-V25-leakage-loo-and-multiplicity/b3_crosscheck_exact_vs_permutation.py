"""B3 -- does the exact enumeration agree with V21's sampled permutation null?

V21 published 0.117 for `v11-handover-a0`/`solvable` from 2000 shuffles. B1
computes a *per-token* exact p under the hypergeometric null. These measure
different things -- 0.117 is family-wise (did ANYTHING fire), the exact p is
per-token -- so they are only comparable through a multiplicity rule. That makes
this a real test of both:

    familywise ?= 1 - prod(1 - p_i)   over the tokens actually scored

If the two agree, then (a) the exact enumeration is right, and (b) the
multiplicity rule is the right shape -- which is precisely the correction the
item asks for, arrived at by measurement rather than by citing Bonferroni.

Also settles two numbers V21 shipped, because a reader who cannot trust the
small claims will not trust the large one:

  * "the remaining ELEVEN label fields at 0.000" -- count them.
  * "the smallest scored groups are why n=5, plan_len n=6" -- check whether
    `why` n=5 has any token the gate actually scores.
"""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))))

from exam import leakage                                          # noqa: E402
from exam.grading.registry import digest                          # noqa: E402
from exam.papers import BUILDERS, module_for                       # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from b1_token_census import p_exact, rate_of                       # noqa: E402

PAPERS = sorted(BUILDERS) + ["<handover_auto>"]
TOLERANCE = 0.90


def p_fire(label_counts, k, tolerance=TOLERANCE):
    """P(the gate fires) for a token on k items, under the shuffled-label null.

    NOT the same quantity as `p_exact`, and conflating them is easy enough that
    the first version of this script did it. `p_exact` conditions on the rate we
    actually observed and answers "how surprising is this token?" -- the number
    you attach to a red so a reader knows what it is worth. `p_fire` conditions
    on the gate's *threshold* and answers "how often would this fire on noise?"
    -- the false-positive rate, and the only one comparable with a9's
    permutation null. On a clean paper the observed rate sits at the floor, so
    `p_exact` is 1.0 by construction and says nothing about the gate.
    """
    import itertools
    from math import comb
    classes = sorted(label_counts)
    sizes = [label_counts[c] for c in classes]
    n = sum(sizes)
    floor = max(sizes) / n
    total = comb(n, k)
    if total == 0:
        return 0.0
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
        rate = rate_of(carriers, others)
        if rate > tolerance and rate > floor + 1e-9:
            hits += ways
    return hits / total


def build(qt):
    if qt == "<handover_auto>":
        from exam.papers import handover_auto
        return handover_auto.build()
    return module_for(qt).build()


def scored_tokens(group, answer_of):
    """Every (field, token) the shipped gate actually scores, with its exact p."""
    n = len(group)
    counts = Counter(answer_of[i.item_id] for i in group)
    out = []
    for field in leakage.METADATA_FIELDS:
        carriers = {}
        for item in group:
            for tok in leakage.field_tokens(item.sheet_side().get(field)):
                carriers.setdefault(tok, []).append(item)
        for tok, holders in sorted(carriers.items()):
            k = len(holders)
            if k < 2 or k == n:
                continue
            held = {i.item_id for i in holders}
            with_t = Counter(answer_of[i.item_id] for i in holders)
            without = Counter(answer_of[i.item_id] for i in group
                              if i.item_id not in held)
            rate = rate_of(with_t, without)
            out.append((field, tok, k, rate, p_exact(counts, k, rate),
                        p_fire(counts, k), frozenset(held)))
    return out


def main():
    print("=" * 78)
    print("== 1. every derived label field, and whether it has a scored token")
    print("=" * 78)
    rows = []
    for qt in PAPERS:
        paper = build(qt)
        key_doc = paper.key(digest())
        for field, answer_of in sorted(
                leakage.derive_label_sets(paper, key_doc).items()):
            groups = [g for g in leakage._by_answer_alphabet(paper, answer_of)
                      if len(g) >= 4
                      and len({answer_of[i.item_id] for i in g}) >= 2]
            toks = []
            for g in groups:
                toks.extend(scored_tokens(g, answer_of))
            rows.append((paper.paper_id, field, len(answer_of),
                         [len(g) for g in groups], toks))
    print("%-22s %-20s %5s %-10s %s"
          % ("paper", "label field", "n", "group ns", "scored tokens"))
    for pid, field, n, gns, toks in sorted(rows):
        print("%-22s %-20s %5d %-10s %d"
              % (pid, field, n, ",".join(str(x) for x in gns), len(toks)))
    print()
    print("derived label fields total : %d" % len(rows))
    print("with >=1 scored token      : %d" % sum(1 for r in rows if r[4]))
    print("with zero scored tokens    : %d" % sum(1 for r in rows if not r[4]))
    print()
    n5 = [r for r in rows if 5 in r[3]]
    print("-- the `why` n=5 claim --")
    for pid, field, n, gns, toks in n5:
        print("   %s/%s group ns=%s scored tokens=%d %s"
              % (pid, field, gns, len(toks),
                 "<- NOTHING IS SCORED HERE" if not toks else ""))
    print()

    print("=" * 78)
    print("== 2. exact per-token p vs V21's sampled family-wise 0.117 / 0.013")
    print("=" * 78)
    for want_paper, want_field, published in (
            ("v11-handover-a0", "solvable", 0.117),
            ("p15-adaptation-a0", "exact_on_heldout", 0.013)):
        for pid, field, n, gns, toks in rows:
            if pid != want_paper or field != want_field:
                continue
            print("-- %s / %s  (published family-wise %.3f)"
                  % (pid, field, published))
            # The multiplicity is the number of distinct *partitions*, not
            # the number of tokens. A token and its complement cut the group
            # the same way, and `item_id` here carries tokens with carrier sets
            # identical to `tags`. Counting tokens would charge four tests for
            # one, which is how a naive Bonferroni over-corrects.
            allids = {i for f, t, k, r, p, pf, h in toks for i in h}
            for f, t, k, r, p, pf, h in toks:
                allids |= h
            seen, parts = set(), []
            for f, t, k, rate, p, pf, held in toks:
                canon = min(tuple(sorted(held)),
                            tuple(sorted(allids - held)))
                print("     %-8s %-10s k=%-3d rate=%.4f  p_exact=%.6f  "
                      "p_fire=%.6f %s"
                      % (f, t, k, rate, p, pf,
                         "" if canon not in seen else "<- same partition"))
                if canon not in seen:
                    seen.add(canon)
                    parts.append(pf)
            surv = 1.0
            for pf in parts:
                surv *= (1.0 - pf)
            fam = 1.0 - surv
            print("     tokens scored=%d  distinct partitions=%d"
                  % (len(toks), len(parts)))
            print("     family-wise from exact ps : 1 - prod(1-p) = %.4f" % fam)
            print("     V21 sampled permutation   :                 %.4f"
                  % published)
            print("     agreement                 : %s"
                  % ("YES, within Monte-Carlo error"
                     if abs(fam - published) < 0.03 else
                     "NO -- %.4f apart" % abs(fam - published)))
            print()


if __name__ == "__main__":
    main()
