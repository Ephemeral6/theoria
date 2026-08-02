"""S46's hardest question: does the axis gate promote a metric?

`battery/audit/gaming.py:383` consults `v9_demotions()`, and that recomputes
against the *live* metric rather than reading a pinned verdict.  So a gate that
makes a V9 attack stop landing does not merely refuse a bad record -- it moves
`tier_of`, upward, which `PREREG_V9.md` R1 forbids outright.

This prints the V9 verdict and every metric's tier, so the same script can be
run on master and on the branch and the two diffed.

    cd battery && python runs/20260802T0000Z-S46-turn-axis/probe_tiers.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, REPO)

from battery.audit.gaming import tier_of                      # noqa: E402
from battery.audit.v9 import mutants                          # noqa: E402
from battery.audit.v9.verdict import v9_demotions             # noqa: E402
from battery.metrics import REGISTRY                          # noqa: E402


def main():
    label = sys.argv[1] if len(sys.argv) > 1 else "current"

    dem = v9_demotions()
    tiers = {mid: tier_of(mid) for mid in sorted(REGISTRY)}
    rows = mutants.sweep()
    disagree = [r for r in rows if not r["agrees"]]
    accepted = [r for r in rows if not r["expected_refusal"]]

    out = {
        "label": label,
        "v9_demotions": {k: {"attack": v["attack"], "value": v["value"]}
                         for k, v in sorted(dem.items())},
        "n_demoted": len(dem),
        "tiers": tiers,
        "n_reference": sum(1 for t in tiers.values() if t == "reference"),
        "mutants_total": len(rows),
        "mutants_disagreeing": [r["name"] for r in disagree],
        "mutants_accepted_not_ok": [
            (r["name"], r["status"]) for r in accepted if r["status"] != "ok"],
    }
    print(json.dumps(out, indent=2, sort_keys=True))
    dest = os.path.join(HERE, "tiers_%s.json" % label)
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print("\nwrote %s" % dest, file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
