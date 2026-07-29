"""The three game counts, read from the claim set instead of typed into it.

## Why this file exists

Both drafts of the freeze kit are keyed to **21 games**, from the pile cut, and
21 is hard-wired into all three of the P-22 scripts (`thresholds.py:3 N = 21`,
`budget_calc.py:9 SEALED_GAMES = 21`).  It is the wrong denominator, and the
right one is in a file the drafts never opened:

    arc-recon/data/claim_set.json
      sealed_pile_size            21
      claim_set_size              19     <- F-11 quarantined ft09 and ls20
      clean                       12
      retained_with_sensitivity_analysis  7

and that file states its own rule, which neither draft implements:

> Games in `retained_with_sensitivity_analysis` are in the claim set but their
> exposure is disclosed, so any statistic over the claim set must be reported a
> second time with them excluded; **if the two disagree, the weaker one
> governs.**

So there are three tiers and every confirmatory number has to exist twice:

| tier | n | what it is | role |
|---|---|---|---|
| `sealed` | 21 | the whole sealed pile | **descriptive only** -- includes two games INC-BA-001 contaminated |
| `claim` | 19 | what a held-out claim may name | **the primary denominator** |
| `clean` | 12 | no disclosed exposure at all | **the sensitivity pass; if it disagrees, it governs** |

The numbers are derived here rather than written down for the same reason the
hash table is generated: this repository has lost four separate checks to
copies that nothing rereads, and a denominator copied into three scripts and
two prose files is five copies.  `--verify` fails if the claim set moves under
them.

    python freeze/tiers.py            # the three tiers and every derived threshold
    python freeze/tiers.py --verify   # exit 1 if a hardcoded 21 survives anywhere
"""

import argparse
import json
import os
import re
import sys
from math import comb

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
CLAIM_SET = os.path.join(REPO, "arc-recon", "data", "claim_set.json")


def tiers():
    with open(CLAIM_SET, encoding="utf-8") as handle:
        data = json.load(handle)
    claim = sorted(data["claim_set"])
    clean = sorted(data["clean"])
    sensitivity = sorted(data.get("retained_with_sensitivity_analysis", []))
    quarantined = sorted(data.get("quarantined", []))

    # The file's own arithmetic, checked rather than trusted.  If these stop
    # holding, the claim set has been restructured and every threshold below is
    # about a set that no longer exists.
    assert len(claim) == data["claim_set_size"], "claim_set_size disagrees with claim_set"
    assert set(clean) <= set(claim), "a clean game is not in the claim set"
    assert set(clean) | set(sensitivity) == set(claim), (
        "clean + sensitivity does not reconstitute the claim set; a game is in "
        "neither bucket and `rule` says it must be adjudicated before it counts")
    assert not (set(quarantined) & set(claim)), "a quarantined game is in the claim set"

    return {
        "sealed": {"n": data["sealed_pile_size"], "role": "descriptive only",
                   "games": None,
                   "why": "includes ft09 and ls20, which INC-BA-001 contaminated "
                          "and F-11 quarantined; a confirmatory statistic over "
                          "this tier would be a statistic over two games we have "
                          "read about"},
        "claim": {"n": len(claim), "role": "primary denominator", "games": claim,
                  "why": "the set a held-out claim may name (F-11)"},
        "clean": {"n": len(clean), "role": "sensitivity pass, and it governs",
                  "games": clean,
                  "why": "no disclosed exposure; claim_set.json's `rule` requires "
                         "every claim-set statistic to be reported a second time "
                         "over this tier, and the weaker of the two governs"},
        "sensitivity_only": {"n": len(sensitivity), "games": sensitivity,
                             "why": "in the claim set, exposure disclosed"},
        "quarantined": {"n": len(quarantined), "games": quarantined},
    }


def sign_p(k):
    """Exact two-sided sign test with k discordant pairs, all one way."""
    return 2 * 0.5 ** k


def sign_threshold(alpha):
    """Smallest k whose two-sided exact p clears `alpha`."""
    for k in range(1, 64):
        if sign_p(k) < alpha:
            return k
    return None


def clopper_pearson(x, n, alpha=0.05):
    try:
        from scipy.stats import beta
    except ImportError:                       # pragma: no cover
        return None, None
    lo = 0.0 if x == 0 else beta.ppf(alpha / 2, x, n - x + 1)
    hi = 1.0 if x == n else beta.ppf(1 - alpha / 2, x + 1, n - x)
    return float(lo), float(hi)


def report():
    t = tiers()
    out = []
    out.append("THREE TIERS, read from arc-recon/data/claim_set.json")
    for name in ("sealed", "claim", "clean"):
        row = t[name]
        out.append("  %-7s n=%-3d %-28s %s"
                   % (name, row["n"], row["role"], row["why"]))
    out.append("  %-7s n=%-3d %s" % ("sens.", t["sensitivity_only"]["n"],
                                     ", ".join(t["sensitivity_only"]["games"])))
    out.append("  %-7s n=%-3d %s" % ("quar.", t["quarantined"]["n"],
                                     ", ".join(t["quarantined"]["games"])))

    out.append("")
    out.append("SIGN TEST -- discordant pairs needed (exact, two-sided)")
    k_un = sign_threshold(0.05)
    k_holm = sign_threshold(0.05 / 3)
    out.append("  unadjusted alpha=0.05          k >= %d   (p=%.5f)"
               % (k_un, sign_p(k_un)))
    out.append("  Holm/Bonferroni family of 3    k >= %d   (p=%.5f)"
               % (k_holm, sign_p(k_holm)))
    out.append("  Multiplicity control costs exactly %d more discordant pair(s)."
               % (k_holm - k_un))
    out.append("  NOTE: this threshold does not depend on the denominator -- it is")
    out.append("        about discordant pairs, not games.  It is the same for 21,")
    out.append("        19 and 12, and P-22's 'costs one sealed game' reading of it")
    out.append("        is the one thing here the 19-vs-21 correction does not move.")

    out.append("")
    out.append("U3 RATE -- Clopper-Pearson 95% CI, per tier")
    for name in ("claim", "clean"):
        n = t[name]["n"]
        out.append("  tier=%s (n=%d)" % (name, n))
        for x in sorted({0, n // 4, n // 2, (2 * n) // 3, (3 * n) // 4, n}):
            lo, hi = clopper_pearson(x, n)
            if lo is None:
                out.append("    scipy absent; CI not computed")
                break
            out.append("    %2d/%-2d = %.3f   CI [%.3f, %.3f]" % (x, n, x / n, lo, hi))

    out.append("")
    out.append("WHAT MUST BE REPORTED TWICE")
    out.append("  Every confirmatory statistic, over tier `claim` (n=%d) and again"
               % t["claim"]["n"])
    out.append("  over tier `clean` (n=%d).  If the two disagree, **the weaker one"
               % t["clean"]["n"])
    out.append("  governs** -- claim_set.json's own rule, not a choice made here.")
    out.append("  Tier `sealed` (n=%d) is descriptive only and may not carry a"
               % t["sealed"]["n"])
    out.append("  confirmatory claim.")
    return "\n".join(out)


#: Files that must not carry a hardcoded sealed-game count any more.  The two
#: P-22 scripts are listed by name rather than discovered, so that a new script
#: with a fresh `N = 21` is caught by review rather than by this list silently
#: not covering it.
NO_HARDCODED_N = (
    "freeze/runs/2026-07-28T1200Z-p22/thresholds.py",
    "freeze/runs/2026-07-28T1200Z-p22/budget_calc.py",
)


def verify():
    problems = []
    t = tiers()
    if t["claim"]["n"] != 19 or t["clean"]["n"] != 12 or t["sealed"]["n"] != 21:
        problems.append(
            "the claim set moved: sealed=%d claim=%d clean=%d. Every threshold "
            "in STATS_RULES.md and PENDING_FIVE.md was derived from 21/19/12 and "
            "must be re-derived." % (t["sealed"]["n"], t["claim"]["n"],
                                     t["clean"]["n"]))
    for rel in NO_HARDCODED_N:
        path = os.path.join(REPO, rel.replace("/", os.sep))
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as handle:
            for number, line in enumerate(handle, start=1):
                if re.search(r"^\s*(N|SEALED_GAMES)\s*=\s*21\b", line):
                    problems.append(
                        "%s:%d still hardcodes 21 as the game count; import from "
                        "freeze/tiers.py instead" % (rel, number))
    if problems:
        for problem in problems:
            print("FAIL: %s" % problem)
        return 1
    print("tiers still 21/19/12 and no script hardcodes the game count")
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.verify:
        return verify()
    print(report())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
