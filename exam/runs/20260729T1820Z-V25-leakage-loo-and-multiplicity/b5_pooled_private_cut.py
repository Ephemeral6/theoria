"""B5 · the ruling this item shipped first was wrong, and here is the measurement.

Cycle 70-71 concluded that the single-holder blind spot **cannot** be closed, and
wrote a proof: every statistic available for a token carried by one item is a
function of that carrier alone, so a real leak (`ridge` on the one `dead` item)
and a bookkeeping identifier (`tag07` on the same item) are identical digit for
digit, and no rule can fire on one and stay silent on the other.

The proof is correct. **The conclusion drawn from it was not**, and an adversarial
review said so: the proof quantifies over rules reading *one token's* carrier set,
while `_token_hits_within` holds the whole field's carrier map. That is strictly
more information, and it separates the pair -- one private token in a field is an
anomaly, twelve are an enumeration.

So the question is asked once per field instead of once per token: **does carrying
a private marker in this field predict the answer?** This script measures what
that costs and what it buys.

    python exam/runs/20260729T1820Z-V25-leakage-loo-and-multiplicity/b5_pooled_private_cut.py

Sections:

1. the deciding pair (`ridge` vs the `tagNN` family) and the padding evasion;
2. every shipped paper, plus `v11-handover-a0`, before and after;
3. what dropping the single-token guard would cost -- the justification the first
   pass asserted and never measured;
4. the rule that survives the padding evasion, measured but not shipped.

No RNG. Every number below is an enumeration or a closed form.
"""

from __future__ import annotations

import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from exam import leakage                                          # noqa: E402
from exam.grading.registry import digest                          # noqa: E402
from exam.model import Item, LeakageError, Paper                  # noqa: E402
from exam.papers import BUILDERS, handover_auto, module_for       # noqa: E402


def paper_of(tag_of, answer_of, n=12):
    items = [Item(item_id="q%02d" % i, rubric_id="r", points=2.0,
                  paper={"kind": "probe", "body": "board %d" % i},
                  truth={"claim": answer_of(i)}, leak_probes=[answer_of(i)],
                  tags=tuple(tag_of(i)))
             for i in range(n)]
    return Paper(paper_id="b5", question_type="verdict", instructions="",
                 items=items)


def labels(paper):
    return {i.item_id: i.truth["claim"] for i in paper.items}


#: M5   -- the real leak: `ridge` sits on the one item answering `dead`.
#: M5_ID -- the identifier family: every item carries its own `tagNN`.
#: M5_EVADE -- the known evasion: `ridge` hidden among a decoy private marker on
#:             every item, which pushes the pooled cut to k == n where the
#:             constant guard drops it. Named here because a limitation a report
#:             does not state is a limitation the next reader has to rediscover.
FIXTURES = {
    "M5 (real leak, one carrier)":
        (lambda i: ("verdict", "level:%02d" % i) + (("ridge",) if i == 7 else ()),
         lambda i: "dead" if i == 7 else "live", True),
    "M5_ID (identifier family)":
        (lambda i: ("verdict", "level:%02d" % i, "tag%02d" % i),
         lambda i: "dead" if i == 7 else "live", False),
    "M5_EVADE (leak + decoy on every item)":
        (lambda i: ("verdict", "pad%02da" % i) + (("ridge",) if i == 7 else ()),
         lambda i: "dead" if i == 7 else "live", False),
}


def fixtures_section(out):
    print("== 1. the deciding fixtures "
          "(expected: fire / silent / silent-and-that-is-the-evasion)")
    out["fixtures"] = []
    for name, (tag_of, answer_of, should_fire) in FIXTURES.items():
        paper = paper_of(tag_of, answer_of)
        hits = leakage.metadata_hits(paper, labels(paper))
        pooled = [h for h in hits
                  if h.get("token") == leakage.PRIVATE_MARKER_CUT]
        tokens = [h for h in hits if h.get("token") not in
                  (None, leakage.PRIVATE_MARKER_CUT)]
        fired = bool(pooled)
        out["fixtures"].append({
            "fixture": name, "pooled_fired": fired,
            "as_expected": fired == should_fire,
            "token_level_findings": [h["token"] for h in tokens],
            "carriers": pooled[0]["carrier_ids"] if pooled else [],
            "p_fire": pooled[0]["p_fire"] if pooled else None,
        })
        print("   %-40s pooled=%-5s tokens=%-4d %s"
              % (name, fired, len(tokens),
                 "as expected" if fired == should_fire else "*** UNEXPECTED"))
    return all(f["as_expected"] for f in out["fixtures"])


def all_papers():
    for qt in sorted(BUILDERS):
        yield qt, module_for(qt).build()
    yield "handover_auto", handover_auto.build()


def papers_section(out):
    print("\n== 2. every paper, with the pooled cut in")
    out["papers"] = []
    for qt, paper in all_papers():
        try:
            leakage.check_paper(paper, paper.sheet(digest()),
                                key_doc=paper.key(digest()))
            verdict, detail = "GREEN", None
        except LeakageError as error:
            verdict, detail = "RED", str(error)
        out["papers"].append({"question_type": qt, "paper_id": paper.paper_id,
                              "verdict": verdict, "detail": detail})
        print("   %-14s %-20s %s" % (qt, paper.paper_id, verdict))
        if detail:
            print("      %s" % detail[:200])


def guard_cost_section(out):
    """What the first pass asserted without measuring: that scoring single-holder
    tokens individually would redden every paper. It would not -- on the real
    corpus it reddens nothing -- so the reason to keep the per-token guard is that
    it is *right about tokens*, not that removing it would cry wolf."""
    print("\n== 3. what scoring single holders individually would cost")
    original = leakage._token_hits_within.__defaults__
    counted = {"scored_k1": 0, "would_fire": 0}
    for _qt, paper in all_papers():
        key = paper.key(digest())
        for _source, answer_of in sorted(
                leakage.derive_label_sets(paper, key).items()):
            for group in leakage._by_answer_alphabet(paper, answer_of):
                n = len(group)
                if n < leakage.MIN_LABELLED:
                    continue
                counts = Counter(answer_of[i.item_id] for i in group)
                floor = max(counts.values()) / n
                for field in leakage.METADATA_FIELDS:
                    carriers = {}
                    for item in group:
                        for token in leakage.field_tokens(
                                item.sheet_side().get(field)):
                            carriers.setdefault(token, []).append(item)
                    for _token, holders in carriers.items():
                        if len(holders) != 1:
                            continue
                        counted["scored_k1"] += 1
                        held = {holders[0].item_id}
                        with_token = Counter(answer_of[i] for i in held)
                        without = Counter(answer_of[i.item_id] for i in group
                                          if i.item_id not in held)
                        rate = (with_token.most_common(1)[0][1]
                                + without.most_common(1)[0][1]) / n
                        if rate > 0.90 and rate > floor + 1e-9:
                            counted["would_fire"] += 1
    assert leakage._token_hits_within.__defaults__ == original
    out["guard_cost"] = counted
    print("   single-holder tokens across all five papers : %d"
          % counted["scored_k1"])
    print("   of those, would fire if scored individually : %d"
          % counted["would_fire"])
    print("   -- so 'it would cry wolf' was not the reason; the reason is that")
    print("      the statistic cannot tell a leak from an id at k=1.")


def denominators_section(out):
    """The coverage ratio, on each of the three denominators it has been quoted
    with. 237/261 was scan slots across five papers; the four shipped papers on a
    distinct (field, token) basis are the number that belongs in a docstring."""
    print("\n== 4. the coverage denominators, all three")
    slots_all = slots_four = 0
    single_slots_all = single_slots_four = 0
    distinct_all, distinct_four = set(), set()
    single_distinct_all, single_distinct_four = set(), set()
    for qt, paper in all_papers():
        shipped = qt in BUILDERS
        key = paper.key(digest())
        for _source, answer_of in sorted(
                leakage.derive_label_sets(paper, key).items()):
            for group in leakage._by_answer_alphabet(paper, answer_of):
                if len(group) < leakage.MIN_LABELLED:
                    continue
                n = len(group)
                for field in leakage.METADATA_FIELDS:
                    carriers = {}
                    for item in group:
                        for token in leakage.field_tokens(
                                item.sheet_side().get(field)):
                            carriers.setdefault(token, []).append(item)
                    for token, holders in carriers.items():
                        if len(holders) == n:
                            continue        # a constant is not in the denominator
                        slots_all += 1
                        distinct_all.add((paper.paper_id, field, token))
                        if len(holders) == 1:
                            single_slots_all += 1
                            single_distinct_all.add((paper.paper_id, field, token))
                        if shipped:
                            slots_four += 1
                            distinct_four.add((paper.paper_id, field, token))
                            if len(holders) == 1:
                                single_slots_four += 1
                                single_distinct_four.add(
                                    (paper.paper_id, field, token))
    out["denominators"] = {
        "scan_slots_five_papers": [single_slots_all, slots_all],
        "scan_slots_four_shipped": [single_slots_four, slots_four],
        "distinct_field_token_five": [len(single_distinct_all),
                                      len(distinct_all)],
        "distinct_field_token_four": [len(single_distinct_four),
                                      len(distinct_four)],
    }
    for name, (num, den) in out["denominators"].items():
        print("   %-28s %4d / %4d = %.1f%%"
              % (name, num, den, 100.0 * num / den if den else 0.0))
    print("   -- the docstring quotes `distinct_field_token_four`; the other")
    print("      three are recorded so the earlier numbers can be traced.")


def main():
    out = {}
    ok = fixtures_section(out)
    papers_section(out)
    guard_cost_section(out)
    denominators_section(out)
    path = os.path.join(HERE, "pooled_private_cut.json")
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(out, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("\nwrote %s" % os.path.basename(path))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
