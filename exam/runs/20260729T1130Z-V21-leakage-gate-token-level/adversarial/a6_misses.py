"""A6 -- leaks the NEW check still misses.  Each case is a paper the gate
passes green while a cheater reads its answers straight off the sheet.

Run: python exam/runs/.../adversarial/a6_misses.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))

from exam import leakage
from exam.model import Item, LeakageError, Paper

RESULTS = []


def make(name, n, answer_of, paper_of, tags_of=lambda i: ("verdict",),
         points_of=lambda i: 2.0, probes_of=None):
    items = [
        Item(item_id="q%02d" % i, rubric_id="r", points=points_of(i),
             paper=paper_of(i), truth={"claim": answer_of(i)},
             leak_probes=(probes_of(i) if probes_of else ["verdict-%d" % i]),
             tags=tuple(tags_of(i)))
        for i in range(n)
    ]
    return Paper(paper_id=name, question_type="verdict", instructions="",
                 items=items)


def verdict(paper, note):
    lab = {i.item_id: i.truth["claim"] for i in paper.items}
    hits = leakage.metadata_hits(paper, lab)
    try:
        leakage.check_paper(paper, paper.sheet("d"), answer_of=lab)
        gate = "GREEN"
    except LeakageError as exc:
        gate = "RED (%s)" % str(exc)[:90]
    RESULTS.append((paper.paper_id, gate, len(hits), note))
    print("-" * 74)
    print("%-28s gate=%-6s metadata_hits=%d" % (paper.paper_id, gate, len(hits)))
    print("   ", note)
    for it in paper.items[:4]:
        print("     ", it.item_id, it.sheet_side(), "->", lab[it.item_id])
    return gate


# ---------------------------------------------------------------- M1
# The leak sits in a sheet field that is not points/tags/kind.
verdict(make("M1-unchecked-field", 12,
             lambda i: "dead" if i < 6 else "live",
             lambda i: {"kind": "probe", "level": "ridge" if i < 6 else "gorge",
                        "body": "board %d" % i}),
        "M1: `level` is ridge on every dead item, gorge on every live one. "
        "`level` is not in METADATA_FIELDS, so nothing looks at it. "
        "`level` is on 36/60, 17/29, 80/80 and 15/31 items of the four real "
        "papers (see a5).")

# ---------------------------------------------------------------- M1b
# ...including item_id, which sheet_side() puts on every item by construction.
verdict(make("M1b-item-id", 12,
             lambda i: "dead" if i < 6 else "live",
             lambda i: {"kind": "probe", "body": "board %d" % i}),
        "M1b: identical, but see the next block -- item_id itself.")

items = [Item(item_id=("ridge%02d" % i) if i < 6 else ("gorge%02d" % i),
              rubric_id="r", points=2.0,
              paper={"kind": "probe", "body": "board %d" % i},
              truth={"claim": "dead" if i < 6 else "live"},
              leak_probes=["v-%d" % i], tags=("verdict",))
         for i in range(12)]
verdict(Paper(paper_id="M1c-item-id-leak", question_type="verdict",
              instructions="", items=items),
        "M1c: the answer is spelled in item_id. `sheet_side()` publishes "
        "item_id on every item of every paper; METADATA_FIELDS does not "
        "include it.")

# ---------------------------------------------------------------- M2
# A token shorter than MIN_TOKEN=3.
verdict(make("M2-short-token", 12,
             lambda i: "dead" if i < 6 else "live",
             lambda i: {"kind": "probe", "body": "board %d" % i},
             tags_of=lambda i: ("verdict", "level:%02d" % i,
                                "up" if i < 6 else "dn")),
        "M2: the tag is `up`/`dn` -- two characters, dropped by MIN_TOKEN=3. "
        "Whole-value bucketing sees only singletons because of level:NN. "
        "Nothing is scored.  p15-heldout-a0's `action` field is exactly this "
        "shape (4 distinct values, 3 surviving tokens).")

# ---------------------------------------------------------------- M3
# Conjunctive leak across two fields.
# XOR: points alone is 50/50, the tag alone is 50/50, the pair is exact.
_hi = lambda i: (i % 4) in (2, 3)          # noqa: E731  points 3.0
_al = lambda i: (i % 2) == 0               # noqa: E731  tag alpha
verdict(make("M3-two-field-xor", 12,
             lambda i: "dead" if _hi(i) == _al(i) else "live",
             lambda i: {"kind": "probe", "body": "board %d" % i},
             tags_of=lambda i: ("verdict", "level:%02d" % i,
                                "alpha" if _al(i) else "beta"),
             points_of=lambda i: 3.0 if _hi(i) else 2.0),
        "M3: XOR.  `points` alone predicts 6/12, the tag alone predicts 6/12, "
        "the pair predicts 12/12.  Every check in this module is single-field, "
        "so a two-field key is invisible by construction.")

# ---------------------------------------------------------------- M4
# Structural leak: list length, with a shared token vocabulary.
verdict(make("M4-list-length", 12,
             lambda i: "dead" if i < 6 else "live",
             lambda i: {"kind": "probe", "body": "board %d" % i},
             tags_of=lambda i: (("verdict", "level:%02d" % i, "pad", "pad")
                                if i < 6 else ("verdict", "level:%02d" % i, "pad"))),
        "M4: dead items carry the tag `pad` twice, live items once.  Every "
        "token is on every item so the token check skips them all; every "
        "whole value is unique so the value check scores nothing.  Length is "
        "a signal tokenising to a *set* destroys by construction.")

# ---------------------------------------------------------------- M5
# A token on exactly one item -- the `len(holders) < 2` guard.
verdict(make("M5-single-holder", 12,
             lambda i: "dead" if i == 0 else "live",
             lambda i: {"kind": "probe", "body": "board %d" % i},
             tags_of=lambda i: (("verdict", "level:%02d" % i, "ridge") if i == 0
                                else ("verdict", "level:%02d" % i))),
        "M5: one item is dead and it is the only one carrying `ridge`.  Had "
        "the token been scored: rate = (1 + 11)/12 = 1.000 against a floor of "
        "11/12 = 0.917 -- a hit.  `len(holders) < 2` throws it away.  A single "
        "item answered free is exactly the leak `points` 2-vs-3 was.")

# ---------------------------------------------------------------- M6 (control)
verdict(make("M6-value-level-still-works", 12,
             lambda i: "dead" if i < 6 else "live",
             lambda i: {"kind": "probe", "body": "board %d" % i},
             points_of=lambda i: 2.0 if i < 6 else 3.0),
        "M6 (CONTROL, expected RED): the original points 2-vs-3 leak. "
        "Tokens are too short to survive tokenising; the whole-value net "
        "catches it.  STATUS.md's claim about this is TRUE.")

# ---------------------------------------------------------------- M7
# Floor contamination across fields.
verdict(make("M7-floor-contamination", 10,
             lambda i: "dead" if i < 5 else "live",
             lambda i: {"kind": "probe", "body": "board %d" % i},
             tags_of=lambda i: ("verdict", "level:%02d" % i,
                                "ridge" if i < 5 else "gorge"),
             points_of=lambda i: 2.0 if i < 4 else (3.0 if i == 4 else 5.0)),
        "M7: see a7_floor_contamination.py -- `floor` is assigned once before "
        "the field loop and raised inside it, so a later field is scored "
        "against a floor computed on an earlier field's subset.")

print()
print("=" * 74)
print("%-28s %-8s %s" % ("paper", "gate", "metadata_hits"))
for pid, gate, n, _ in RESULTS:
    print("%-28s %-8s %d" % (pid, gate.split(" ")[0], n))
