"""OPS-M adversarial verifier #4 -- independent re-derivation of constructions
A/B/C/D against the leakage gate.

Written from scratch by the adversarial verifier. Pure synthetic: no game data,
no sealed-pile contact, no network, no API, no filesystem writes into any tree
under test. Lives OUTSIDE the three worktrees; the tree under test is supplied
by argv[1] and put on sys.path unmodified.

Production entry point, for fidelity (exam/tools/build_papers.py build_one):

    paper  = module.build()
    sheet  = paper.sheet(rubric_digest, module_digest)
    key_doc= paper.key(rubric_digest)
    report = leakage.check_paper(paper, sheet, key_doc=key_doc,
                                 answer_of=_answer_labels(module,paper,key_doc))

`_answer_labels` returns None unless the module defines `answer_labels` (only
`handover_auto` does), so production's *commonest* shape is key_doc-only with
answer_of=None. `require_probes` is left at its default True. We run BOTH
shapes -- "declared" (answer_of only, what the prior probes used) and
"production" (key_doc, answer_of=None) -- because a claim that only holds in one
of them is a claim about the harness.
"""
import json
import os
import sys

TREE = os.path.abspath(sys.argv[1])
sys.path.insert(0, TREE)

from exam.model import Item, Paper, LeakageError  # noqa: E402
from exam import leakage as L                     # noqa: E402

DIGEST = "d0" * 32
MODDIGEST = "d1" * 32


# --------------------------------------------------------------- constructions

def _mk(paper_id, spec, order, question="is this configuration solvable?"):
    """spec: short -> (answer, tags list). order: sheet order of shorts."""
    items = []
    for n, short in enumerate(order, start=1):
        answer, tags = spec[short]
        items.append(Item(
            item_id="q%02d" % n,
            rubric_id="r-verdict",
            points=3.0,                       # constant: cannot confound
            paper={"kind": "verdict", "question": question},
            truth={"claim": answer},
            leak_probes=["zzprobe-%s-%d" % (short, n)],   # absent from sheet
            tags=list(tags),
        ))
    paper = Paper(paper_id=paper_id, question_type="verdict",
                  instructions="Answer solvable or unsolvable.", items=items)
    answer_of = {it.item_id: spec[s][0] for it, s in zip(items, order)}
    return paper, answer_of


ORDER8 = ["s1", "u1", "s3", "u2", "s2", "u3", "s4", "u4"]   # interleaved


def con_A():
    """A: whole tags VALUE shared in pairs on solvable, unique on unsolvable,
    one token per value.  Cheat: 'my level name appears on another item'."""
    spec = {
        "s1": ("solvable", ["level:orchard"]),
        "s2": ("solvable", ["level:orchard"]),
        "s3": ("solvable", ["level:lattice"]),
        "s4": ("solvable", ["level:lattice"]),
        "u1": ("unsolvable", ["level:stile"]),
        "u2": ("unsolvable", ["level:cairn"]),
        "u3": ("unsolvable", ["level:flume"]),
        "u4": ("unsolvable", ["level:ridge"]),
    }
    return _mk("adv4-A", spec, ORDER8)


def con_B():
    """B: same channel, but every unsolvable TOKEN sits on 3 items, so there is
    no single-holder token.  Cheat: 'my whole tags value is printed on another
    item' -> solvable."""
    spec = {
        "s1": ("solvable", ["gold"]),
        "s2": ("solvable", ["gold"]),
        "s3": ("solvable", ["silver"]),
        "s4": ("solvable", ["silver"]),
        "u1": ("unsolvable", ["red", "blue"]),
        "u2": ("unsolvable", ["blue", "green"]),
        "u3": ("unsolvable", ["green", "red"]),
        "u4": ("unsolvable", ["red", "blue", "green"]),
    }
    return _mk("adv4-B", spec, ORDER8)


def con_C():
    """C: every whole tags VALUE unique; solvable tokens each on 2 items,
    unsolvable tokens each private.  Cheat: 'I carry a marker nobody else
    carries' -> unsolvable."""
    spec = {
        "s1": ("solvable", ["alpha", "beta"]),
        "s2": ("solvable", ["beta", "gamma"]),
        "s3": ("solvable", ["gamma", "delta"]),
        "s4": ("solvable", ["delta", "alpha"]),
        "u1": ("unsolvable", ["uniqa"]),
        "u2": ("unsolvable", ["uniqb"]),
        "u3": ("unsolvable", ["uniqc"]),
        "u4": ("unsolvable", ["uniqd"]),
    }
    return _mk("adv4-C", spec, ORDER8)


def con_D():
    """D: per-item-unique slot token hides a shared literal answer token."""
    spec = {}
    order = []
    for i in range(8):
        short = "x%d" % i
        answer = "solvable" if i % 2 == 0 else "unsolvable"
        tags = ["slot%02d" % i] + ([] if i % 2 == 0 else ["dead"])
        spec[short] = (answer, tags)
        order.append(short)
    return _mk("adv4-D", spec, order)


# ------------------------------------------------------------------ scoring

def loo(paper, answer_of, feature):
    """Leave-one-out accuracy of a nearest-rule cheat.

    `feature` maps item_id -> a hashable feature computed from the WHOLE sheet
    (a cheater sees the whole sheet, so that is fair), but the feature->answer
    map is refitted on the other n-1 items for every held-out item, so no item
    votes on its own rule.  Ties broken by sorted order, deterministic.
    """
    ids = [i.item_id for i in paper.items]
    feat = feature(paper)
    correct = 0
    for held in ids:
        table = {}
        for other in ids:
            if other == held:
                continue
            table.setdefault(feat[other], {})
            table[feat[other]][answer_of[other]] = \
                table[feat[other]].get(answer_of[other], 0) + 1
        row = table.get(feat[held])
        if not row:
            continue
        if max(sorted(row), key=lambda k: row[k]) == answer_of[held]:
            correct += 1
    counts = {}
    for i in ids:
        counts[answer_of[i]] = counts.get(answer_of[i], 0) + 1
    return correct / len(ids), max(counts.values()) / len(ids)


def feat_shared_value(paper):
    val = {i.item_id: json.dumps(list(i.tags)) for i in paper.items}
    c = {}
    for v in val.values():
        c[v] = c.get(v, 0) + 1
    return {k: (c[v] > 1) for k, v in val.items()}


def feat_private_token(paper):
    tok_count = {}
    for i in paper.items:
        for t in set(i.tags):
            tok_count[t] = tok_count.get(t, 0) + 1
    return {i.item_id: any(tok_count[t] == 1 for t in set(i.tags))
            for i in paper.items}


# ------------------------------------------------------------------- runner

def run(name, builder, feats):
    paper, answer_of = builder()
    sheet = paper.sheet(DIGEST, MODDIGEST)
    key_doc = paper.key(DIGEST)

    print("=" * 74)
    print("CONSTRUCTION %s   (%s)   tree=%s"
          % (name, paper.paper_id, os.path.basename(TREE)))
    print("  tags by answer:")
    for it in paper.items:
        print("    %-5s %-11s %s" % (it.item_id, answer_of[it.item_id],
                                     json.dumps(list(it.tags))))
    for fname, f in feats:
        s, b = loo(paper, answer_of, f)
        print("  LOO[%s] = %.3f   majority baseline = %.3f" % (fname, s, b))

    for mode, kwargs in (
        ("declared  (answer_of only, require_probes=False)",
         dict(answer_of=answer_of, require_probes=False)),
        ("PRODUCTION(key_doc only, require_probes=True)",
         dict(key_doc=key_doc)),
        ("both      (key_doc + answer_of, require_probes=True)",
         dict(key_doc=key_doc, answer_of=answer_of)),
    ):
        try:
            rep = L.check_paper(paper, sheet, **kwargs)
            print("  %s -> SILENT" % mode)
            print("      label_sets_checked: %s"
                  % rep.get("label_sets_checked"))
        except LeakageError as exc:
            print("  %s -> FIRES" % mode)
            for line in _explain(exc):
                print("      " + line)
    print()


def _explain(exc):
    """Print the finding structurally, not as a truncated blob."""
    out = []
    msg = str(exc)
    # check_paper embeds a repr of the findings list; re-derive instead by
    # calling metadata_hits directly is not possible here, so print the repr in
    # readable chunks.
    for chunk in msg.split("}, {"):
        out.append(chunk.strip()[:400])
    return out[:8]


def main():
    print("### tree: %s" % TREE)
    print("### exam.leakage from: %s" % L.__file__)
    print("### METADATA_FIELDS: %s" % (L.METADATA_FIELDS,))
    print("### has metadata_scan: %s / has single_holder_coverage: %s"
          % (hasattr(L, "metadata_scan"), hasattr(L, "single_holder_coverage")))
    print()
    run("A", con_A, [("shared-value", feat_shared_value)])
    run("B", con_B, [("shared-value", feat_shared_value),
                     ("private-token", feat_private_token)])
    run("C", con_C, [("private-token", feat_private_token)])
    run("D", con_D, [("shared-value", feat_shared_value)])


if __name__ == "__main__":
    main()
