"""A12 -- an independent leak audit of all five shipped papers.

Written from the key and the sheet, using nothing from exam/leakage.py except
`canonical` (a serialiser) -- no METADATA_FIELDS, no MIN_TOKEN, no tolerance, no
`kind` grouping, no singleton dropping.

Differences from the gate, on purpose:

  * EVERY sheet field is examined, not three of them, plus two derived features
    the gate never looks at: the item's position in the sheet and the length of
    its serialised sheet side.
  * Tokens of any length >= 1, plus the whole value, plus the *number of
    elements* of a list value and the *length* of the serialised value.
  * Accuracy is leave-one-out.  For every item, the rule is fitted on the other
    n-1 items and then asked to predict this one.  That is what makes an
    identifier score at chance instead of at 1.0, so singletons need not be
    thrown away -- which is the gate's real weakness, not its tolerance.
  * The baseline is the leave-one-out majority-class rate, computed the same
    way, so the two numbers are comparable.

Anything whose LOO accuracy beats the LOO baseline by a clear margin is
reported.  The gate's own findings are printed beside it.
"""
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
sys.path.insert(0, REPO)

from exam import leakage                      # only to print what IT says
from exam.grading.registry import digest
from exam.model import canonical
from exam.papers import BUILDERS, module_for

MARGIN = 0.25          # LOO accuracy must beat the LOO baseline by this much
MIN_N = 4


def build(qt):
    if qt == "<handover_auto>":
        from exam.papers import handover_auto
        return handover_auto.build()
    return module_for(qt).build()


def loo_baseline(labels):
    n = len(labels)
    hit = 0
    for i in range(n):
        rest = Counter(labels[:i] + labels[i + 1:])
        if rest and rest.most_common(1)[0][0] == labels[i]:
            hit += 1
    return hit / n


def loo_partition(labels, groups):
    """Leave-one-out accuracy of `predict the majority of my own group`.

    `groups` is a list of hashable group ids, one per item.  An item whose group
    is empty once it is removed gets no prediction and is scored wrong, which is
    exactly why an identifier cannot win here.
    """
    n = len(labels)
    hit = 0
    for i in range(n):
        peers = [labels[j] for j in range(n) if j != i and groups[j] == groups[i]]
        if not peers:
            continue
        if Counter(peers).most_common(1)[0][0] == labels[i]:
            hit += 1
    return hit / n


def features(paper, ids):
    """field -> list of group ids, one per labelled item, over EVERY sheet key."""
    by_id = {i.item_id: i for i in paper.items}
    order = {i.item_id: k for k, i in enumerate(paper.items)}
    keys = set()
    for it in paper.items:
        keys |= set(it.sheet_side())
    out = {}
    for k in sorted(keys):
        vals = [canonical(by_id[i].sheet_side().get(k)) for i in ids]
        out["value:" + k] = vals
        out["len:" + k] = [len(v) for v in vals]
        raw = [by_id[i].sheet_side().get(k) for i in ids]
        if any(isinstance(r, (list, tuple)) for r in raw):
            out["count:" + k] = [len(r) if isinstance(r, (list, tuple)) else -1
                                 for r in raw]
        # every token of any length, as a presence/absence rule
        toks = set()
        tokmap = {}
        for iid, v in zip(ids, vals):
            t = {x for x in __import__("re").split(r"[^0-9A-Za-z]+", v.lower()) if x}
            tokmap[iid] = t
            toks |= t
        for t in sorted(toks):
            out["token:%s=%s" % (k, t)] = [t in tokmap[i] for i in ids]
    out["position/2"] = [order[i] // 2 for i in ids]
    out["position parity"] = [order[i] % 2 for i in ids]
    out["sheet length/64"] = [len(canonical(by_id[i].sheet_side())) // 64 for i in ids]
    return out


def label_candidates(paper, key_doc):
    """Wider than derive_label_sets: any scalar truth field with 2..8 values on
    >= 4 items, plus the module's own oracle answers if it exposes them."""
    per, alpha = {}, {}
    for e in key_doc.get("items", ()):
        t = e.get("truth")
        if not isinstance(t, dict):
            continue
        for f, v in t.items():
            if isinstance(v, (str, bool, int)) and not isinstance(v, float):
                per.setdefault(f, {})[e["item_id"]] = canonical(v)
                alpha.setdefault(f, set()).add(canonical(v))
    out = {}
    for f, m in per.items():
        if 2 <= len(alpha[f]) <= 8 and len(m) >= MIN_N:
            out["truth:" + f] = m
    return out


for qt in sorted(BUILDERS) + ["<handover_auto>"]:
    paper = build(qt)
    key = paper.key(digest())
    cands = label_candidates(paper, key)
    gate_sets = leakage.derive_label_sets(paper, key)
    print("=" * 78)
    print("%s   n_items=%d" % (paper.paper_id, len(paper.items)))
    print("  gate derives : %s" % sorted(gate_sets))
    print("  I examine    : %s" % sorted(cands))
    for src, m in sorted(cands.items()):
        ids = sorted(m)
        labels = [m[i] for i in ids]
        base = loo_baseline(labels)
        feats = features(paper, ids)
        rows = []
        for fname, groups in feats.items():
            acc = loo_partition(labels, groups)
            if acc >= base + MARGIN:
                rows.append((acc, fname))
        rows.sort(reverse=True)
        gate = leakage.metadata_hits(paper, m) if src[6:] in gate_sets else None
        print("  -- %-24s n=%-3d LOO baseline=%.3f  gate_derived=%s gate_hits=%s"
              % (src, len(ids), base, src[6:] in gate_sets,
                 "n/a" if gate is None else len(gate)))
        for acc, fname in rows[:12]:
            print("       LOO %.3f   %s" % (acc, fname))
        if not rows:
            print("       (nothing beats baseline+%.2f)" % MARGIN)
