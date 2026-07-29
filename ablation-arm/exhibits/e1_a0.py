"""E1 — a true impossibility: the verdict survives the cut, the reason does not.

`Theoria.md:259`'s class (i), quoted in `DESIGN.md` §E1:

> 小空间不可解——穷举可行,连 Schema 的完备搜索都会正确地停,**甚至可能因漏边而以
> 错误的理由得到正确的判决**,所以这里考的是理由:证书,还是"我搜过了没有"。

A0 with no Button is genuinely unsolvable, and upstream states the constructive
ground: the Door is the only opening in the dividing wall, the only rule that
removes it tests for the Button's colour, and with no Button that guard can
never hold.

**So this arm gets it right, and that is the point.**  E1 is not a failure of the
ablated arm; it is the half of its testimony that makes the other half readable.
Measured at the verdict, the two arms are *indistinguishable* — which is exactly
why a benchmark that scores verdicts cannot see this ablation at all, and why
the reason has to be scored separately.

The reason is the whole difference.  The full arm leaves a certificate behind in
`cold-start-a0/artifacts/unsolvable_report.json`:

    theorem.axioms = [{"axioms": [], "name": "unsolvable"}]

— an `#print axioms` report with an **empty** axiom list, which is the
machine-checkable statement that `unsolvable` was proved from nothing but the
manual.  This arm's corresponding column does not exist.  Not "is weaker": the
plan report carries `certificate: None` and `certificate_owed: False`, because
under C-4 a UNSAT settles bare.

That pair — same verdict, one certificate, one nothing — is E1's testimony.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

EXHIBIT = "E1"
WORLD = "a0-no-button"
UPSTREAM_REPORT = "cold-start-a0/artifacts/unsolvable_report.json"


def _load_run() -> Dict[str, Any]:
    path = os.path.join(HERE, "artifacts", WORLD, "run_report.json")
    if not os.path.exists(path):
        raise FileNotFoundError(
            "%s is missing; run `python ablation-arm/run_arm.py` first. This "
            "exhibit reads the arm's own run rather than re-running it, so that "
            "what it reports and what the arm did cannot drift apart." % path)
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def run() -> Dict[str, Any]:
    ours = _load_run()
    with open(os.path.join(REPO, UPSTREAM_REPORT), encoding="utf-8") as handle:
        theirs = json.load(handle)

    plan = ours["beats"]["plan"]
    full_arm_axioms = theirs.get("theorem", {}).get("axioms")

    verdicts_agree = ours["verdict"] == "unsolvable"
    verdict_is_correct = True          # see `constructive_ground`, quoted below
    we_have_no_certificate = (plan.get("certificate") is None
                              and plan.get("certificate_owed") is False)
    they_have_one = bool(full_arm_axioms)

    report: Dict[str, Any] = {
        "exhibit": EXHIBIT,
        "world": WORLD,
        "class": "(i) small-space unsolvable -- exhaustive search is feasible",
        "verdict": {
            "ablated_arm": ours["verdict"],
            "settled_by": plan.get("settled_by"),
            "is_correct": verdict_is_correct,
            "constructive_ground": theirs.get("constructive_ground"),
        },
        "the_reason": {
            "full_arm_certificate": full_arm_axioms,
            "full_arm_certificate_source": UPSTREAM_REPORT,
            "ablated_arm_certificate": plan.get("certificate"),
            "ablated_arm_certificate_owed": plan.get("certificate_owed"),
            "ablated_arm_directed_probes": plan.get("directed_probes_scheduled"),
            "distinguishes_proof_from_exhaustion":
                plan.get("distinguishes_proof_from_exhaustion"),
            "full_arm_would": plan.get("full_arm_would"),
        },
        "holds": bool(verdicts_agree and verdict_is_correct
                      and we_have_no_certificate and they_have_one),
        "testimony": (
            "判决相同,理由蒸发. The ablated arm reaches the same verdict as the "
            "full arm and the verdict is right, so nothing measured at the "
            "verdict can separate the two arms -- an evaluation that scores "
            "answers would report this ablation as having cost nothing. What "
            "separates them is the column next to it: the full arm's "
            "`#print axioms` report with an empty axiom list, against this "
            "arm's `certificate: None, certificate_owed: False`. The verdict "
            "is the same sentence with nothing behind it."),
    }
    if not report["holds"]:
        report["why_not"] = [
            line for line, ok in (
                ("the ablated arm did not answer `unsolvable`", verdicts_agree),
                ("the ablated arm produced a certificate, which C-4 says it "
                 "cannot", we_have_no_certificate),
                ("the full arm's report carries no axiom report to compare "
                 "against", they_have_one),
            ) if not ok]
    return report


def main() -> int:
    report = run()
    print("%s -- %s" % (EXHIBIT, report["class"]))
    print("  verdict            : %s (settled_by %s), correct=%s"
          % (report["verdict"]["ablated_arm"], report["verdict"]["settled_by"],
             report["verdict"]["is_correct"]))
    print("  full arm's reason  : %s" % json.dumps(
        report["the_reason"]["full_arm_certificate"], ensure_ascii=False))
    print("  this arm's reason  : certificate=%s owed=%s probes=%s"
          % (report["the_reason"]["ablated_arm_certificate"],
             report["the_reason"]["ablated_arm_certificate_owed"],
             report["the_reason"]["ablated_arm_directed_probes"]))
    print("  holds              : %s" % report["holds"])
    return 0 if report["holds"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
