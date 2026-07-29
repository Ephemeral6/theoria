"""Is test_worldgen_papers.py:71 vacuous, and by how much?"""
import json, collections
from exam.papers import heldout_worldgen as hw, worldgen_port as port
from exam.grading.registry import digest
from exam.model import canonical

SAMPLE = ("t1-push-open", "t2-switch-push", "t3-full-house")
d = digest()

def audit(world_ids, label):
    rows = []
    tot = carved = vacuous = genuinely_absent = genuinely_caught = 0
    for w in world_ids:
        paper = hw.build_for(w)
        sheet = canonical(paper.sheet(d))
        open_text = canonical(json.load(open(port.world_dir(w) + "/spec.json",
                                             encoding="utf-8")))
        for rule in sorted({it.truth["rule"] for it in paper.items}):
            tot += 1
            quoted = '"%s"' % rule
            in_open = quoted in open_text
            quoted_in_sheet = quoted in sheet
            bare_in_sheet = rule in sheet          # the check that SHOULD run
            if in_open:
                carved += 1
                status = "carved-out (spec.json names it)"
            elif quoted_in_sheet:
                genuinely_caught += 1
                status = "TEST WOULD FAIL"
            elif bare_in_sheet:
                vacuous += 1
                status = "VACUOUS PASS (name IS on sheet, quotes don't match)"
            else:
                genuinely_absent += 1
                status = "genuine pass (name absent from sheet)"
            rows.append((w, rule, status))
    print("== %s: %d (world,rule) pairs ==" % (label, tot))
    print("   carved out by spec.json      : %d" % carved)
    print("   VACUOUS passes               : %d" % vacuous)
    print("   genuine passes (truly absent): %d" % genuinely_absent)
    print("   would actually fail          : %d" % genuinely_caught)
    for r in rows:
        print("     %-24s %-32s %s" % r)
    return tot, carved, vacuous

audit(SAMPLE, "worlds the test ACTUALLY runs on (SAMPLE)")
print()
audit(port.world_ids(), "all 20 worlds (hypothetical)")
