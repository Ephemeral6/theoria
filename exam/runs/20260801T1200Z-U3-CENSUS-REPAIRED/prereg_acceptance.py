# -*- coding: utf-8 -*-
"""Audit `exam/PREREG_VERDICT.md` against its OWN stated acceptance.

The pre-registration landed today.  A pre-registration that is only ever read
is not a pre-registration; the point of one is that a later reader can run it
and find out whether it says what it claims.  This script is that reader.  It
does not restate the module's claims -- it recomputes each acceptance condition
from the paper, the key and the control transcripts, and reports pass/fail per
condition with the numbers that decided it.

Four conditions, taken verbatim from the document's own text:

A. **Three classes, each with a construction basis.**  §5's table has three
   columns -- class (i) small, class (ii) large, class (iii) solvable-hard --
   and §8 turns on each item being settled by construction rather than by
   assertion.  So: exactly three classes are shipped, every item in the paper
   belongs to one, and every item carries a non-empty
   `constructive_justification`.
B. **Sensitivity and specificity as separate numbers.**  §3: "Reported, always,
   and as separate numbers".  §3 also FORBIDS "BA alone".  So every scored
   transcript must expose both rates, and BA must be derivable from them --
   `BA == (sens + spec) / 2` recomputed here, not read.
C. **The bluffer scores badly on specificity.**  An arm that always says
   `unsolvable` must be refused, and refused BY the specificity floor.
D. **The denier scores badly on sensitivity.**  The transpose.

C and D are the matched pair §6 says the gate needs: a gate that had only ever
seen C could not be distinguished from one that simply distrusts the word
`unsolvable`.  Both are recomputed from the transcripts on disk.

The script also runs the two conditions' own negative control -- it asserts
that the numbers are NOT symmetric under swapping the two controls, i.e. that
C and D are actually different measurements and not one measurement printed
twice.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from exam import endpoint as ep                                     # noqa: E402
from exam import prereg                                             # noqa: E402
from exam.model import read_json                                    # noqa: E402
from exam.tools import endpoint_verdict as EV                       # noqa: E402

CONTROLS = EV.CONTROLS

TOL = 1e-9


def _fmt(x: Any) -> str:
    return "None" if x is None else ("%.3f" % x)


def main() -> int:
    _module, paper, key = EV._paper_and_key()
    # `Item.truth["class"]` is the class as SHIPPED; `item_id` joins it to the
    # inventory's construction basis.  Both are read off the built paper, not
    # off the pre-registration, so the check can disagree with the document.
    items = [{"item_id": it.item_id, "class": it.truth["class"]}
             for it in paper.items]
    inventory = read_json(os.path.join(
        REPO, "exam", "artifacts", "prereg", "verdict_prereg.json")
    )["class_inventory"]["items"]

    findings: List[Dict[str, Any]] = []

    def record(cond: str, ok: bool, detail: str, numbers: Any = None) -> None:
        findings.append({"condition": cond, "pass": bool(ok),
                         "detail": detail, "numbers": numbers})

    # ---------------------------------------------------------------- A
    classes = sorted({it["class"] for it in items})
    inv_classes = sorted({it["class"] for it in inventory})
    mix = dict(prereg.PREREG["scoring_rule"]["class_sizes"])
    counts = {c: sum(1 for it in items if it["class"] == c) for c in classes}
    record("A1 exactly three classes",
           len(classes) == 3 and classes == inv_classes,
           "paper classes %s; inventory classes %s" % (classes, inv_classes),
           {"classes": classes, "counts": counts, "declared_mix": mix})
    record("A2 the shipped mix is the pre-registered mix",
           counts == mix, "counts %s vs pre-registered %s" % (counts, mix),
           {"counts": counts, "prereg": mix})

    by_id = {it["item_id"]: it for it in inventory}
    missing_basis = [it["item_id"] for it in items
                     if not (by_id.get(it["item_id"], {})
                             .get("constructive_justification") or "").strip()]
    unbacked = [it["item_id"] for it in items if it["item_id"] not in by_id]
    record("A3 every item carries a construction basis",
           not missing_basis and not unbacked,
           "items with no justification: %s; items absent from the inventory: %s"
           % (missing_basis or "none", unbacked or "none"),
           {"items": len(items), "with_basis": len(items) - len(missing_basis)})

    # A construction basis that is one sentence long is a gesture.  Report the
    # shortest, so "carries a basis" cannot be satisfied by the word "yes".
    lengths = sorted((len(by_id[it["item_id"]]["constructive_justification"]),
                      it["item_id"]) for it in items if it["item_id"] in by_id)
    record("A4 the shortest basis is not a gesture",
           lengths and lengths[0][0] >= 80,
           "shortest justification is %d chars (%s)"
           % (lengths[0][0], lengths[0][1]) if lengths else "no items",
           {"shortest": lengths[:3]})

    # ---------------------------------------------------------------- B
    rows: Dict[str, Dict[str, Any]] = {}
    for name in CONTROLS:
        result = EV.judge_submission(EV.control_submission(name))
        ruling, rec = result["ruling"], result["record"]
        cov = rec["coverage_observed"].get("large_unsolvable", {})
        rows[name] = dict(ruling)
        rows[name]["coverage_positive"] = cov.get("coverage_positive")
        rows[name]["certified_share"] = \
            rec["reason_quality"]["certified_share"]

    both_present = []
    ba_recomputes = []
    for name, res in rows.items():
        sens, spec, ba = res["sensitivity"], res["specificity"], res["balanced_accuracy"]
        both_present.append(sens is not None and spec is not None)
        ba_recomputes.append(
            ba is not None and abs(ba - (sens + spec) / 2.0) < TOL)
    record("B1 both rates are defined on every control",
           all(both_present),
           "after 弃权计错 no denominator is empty, so neither rate is None",
           {n: {"sens": _fmt(r["sensitivity"]), "spec": _fmt(r["specificity"])}
            for n, r in rows.items()})
    record("B2 BA is derived from the two, not reported alone",
           all(ba_recomputes),
           "BA == (sens + spec) / 2 recomputed for every control",
           {n: {"ba_reported": _fmt(r["balanced_accuracy"]),
                "ba_recomputed": _fmt((r["sensitivity"] + r["specificity"]) / 2.0)}
            for n, r in rows.items()})

    # ---------------------------------------------------------------- C, D
    bluff, den = rows["bluffer"], rows["denier"]

    record("C bluffer (always `unsolvable`) scores badly on SPECIFICITY",
           (bluff["specificity"] is not None
            and bluff["specificity"] < ep.S_MIN
            and bluff["sensitivity"] == 1.0
            and bluff["verdict"] == ep.VERDICT_REFUTED),
           "spec %s < S_min %s, while sens is %s — it is refused for the right "
           "reason, not by being bad at everything"
           % (_fmt(bluff["specificity"]), ep.S_MIN, _fmt(bluff["sensitivity"])),
           {"sens": _fmt(bluff["sensitivity"]), "spec": _fmt(bluff["specificity"]),
            "ba": _fmt(bluff["balanced_accuracy"]), "verdict": bluff["verdict"],
            "reasons": bluff.get("reasons")})

    record("D denier (never says `unsolvable`) scores badly on SENSITIVITY",
           (den["sensitivity"] is not None
            and den["sensitivity"] < ep.S_MIN
            and den["specificity"] == 1.0
            and den["verdict"] == ep.VERDICT_REFUTED),
           "sens %s, spec %s — the transpose of C, refused on the BA floor "
           "because §2.2 writes no sensitivity floor"
           % (_fmt(den["sensitivity"]), _fmt(den["specificity"])),
           {"sens": _fmt(den["sensitivity"]), "spec": _fmt(den["specificity"]),
            "ba": _fmt(den["balanced_accuracy"]), "verdict": den["verdict"],
            "reasons": den.get("reasons")})

    # The pair's own control: C and D must be DIFFERENT measurements.
    record("CD the pair is a transpose, not one number printed twice",
           (bluff["sensitivity"] == den["specificity"]
            and bluff["specificity"] == den["sensitivity"]
            and bluff["sensitivity"] != bluff["specificity"]),
           "bluffer (sens, spec) = (%s, %s); denier = (%s, %s)"
           % (_fmt(bluff["sensitivity"]), _fmt(bluff["specificity"]),
              _fmt(den["sensitivity"]), _fmt(den["specificity"])),
           None)

    # And the floors must not be redundant: each of C and D is refused, but by
    # a different rule.  If both fell to BA alone, the specificity floor would
    # be carried on the strength of its name.
    bluff_rules = set(bluff.get("reasons") or [])
    den_rules = set(den.get("reasons") or [])
    record("CD2 the two are not killed by the same rule",
           bluff_rules != den_rules,
           "bluffer refused by %s; denier refused by %s"
           % (sorted(bluff_rules), sorted(den_rules)), None)

    # ---------------------------------------------------------------- out
    table = [{"examinee": n,
              "sensitivity": _fmt(r["sensitivity"]),
              "specificity": _fmt(r["specificity"]),
              "balanced_accuracy": _fmt(r["balanced_accuracy"]),
              "coverage_positive": _fmt(r.get("coverage_positive")),
              "certified_share": _fmt(r.get("certified_share")),
              "verdict": r["verdict"]}
             for n, r in rows.items()]

    failed = [f for f in findings if not f["pass"]]
    out = {
        "document": "exam/PREREG_VERDICT.md",
        "paper": paper.paper_id,
        "n_items": len(items),
        "floors": {"S_min": ep.S_MIN, "C_min": ep.C_MIN, "BA": "> 0.5 strict"},
        "conditions": findings,
        "control_table": table,
        "verdict": "ACCEPTED" if not failed else "FAILED",
        "failed_conditions": [f["condition"] for f in failed],
    }
    path = os.path.join(HERE, "prereg_acceptance.json")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(out, indent=1, ensure_ascii=False, sort_keys=True)
                 + "\n")

    for f in findings:
        print("%-4s %s" % ("PASS" if f["pass"] else "FAIL", f["condition"]))
        print("       %s" % f["detail"])
    print()
    print("%-12s %6s %6s %6s %8s %8s  %s"
          % ("examinee", "sens", "spec", "BA", "cov(ii)", "cert", "verdict"))
    for r in table:
        print("%-12s %6s %6s %6s %8s %8s  %s"
              % (r["examinee"], r["sensitivity"], r["specificity"],
                 r["balanced_accuracy"], r["coverage_positive"],
                 r["certified_share"], r["verdict"]))
    print()
    print("VERDICT:", out["verdict"], out["failed_conditions"] or "")
    print("wrote", path)
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
