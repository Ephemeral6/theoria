"""V8 item (1): calibrate every paper's marker with fakes of known score.

Throwaway probe.  Reuses exam.grading.selftest's own helpers so the marking
path is byte-for-byte the one selftest.py uses.
"""
from __future__ import annotations

import importlib
import json
import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, ROOT)

from exam.grading.registry import digest                      # noqa: E402
from exam.grading.selftest import _mark, GARBAGE               # noqa: E402
from exam.papers import BUILDERS, module_for                   # noqa: E402

# handover_auto is a paper module that is NOT in BUILDERS.
PAPERS = list(BUILDERS) + ["handover_auto"]


def module_of(qt):
    if qt in BUILDERS:
        return module_for(qt)
    return importlib.import_module("exam.papers." + qt)


def setup(qt):
    module = module_of(qt)
    paper = module.build()
    key_doc = paper.key(digest())
    answers = dict(module.reference_answers(paper, key_doc, "oracle"))
    return module, paper, key_doc, answers


class _Sentinel:
    pass


# (label, value).  Ordered: the ten the work order names first, then extensions.
def tokens():
    out = [
        ("GARBAGE '__V4_GARBAGE__'", GARBAGE),
        ("'' (empty string)", ""),
        ("{} (empty dict)", {}),
        ("None", None),
        ("[] (empty list)", []),
        ("0 (int)", 0),
        ("False", False),
        ("'None' (string)", "None"),
        ("'unsolvable'", "unsolvable"),
        ("[[]] (empty list nested)", [[]]),
        # ---- extensions ----
        ("[] * (list of one empty dict) [{}]", [{}]),
        ("[None]", [None]),
        ("['']", [""]),
        ("{} nested {'a': {}}", {"a": {}}),
        ("{'answer': None}", {"answer": None}),
        ("{'answer': ''}", {"answer": ""}),
        ("{'answer': []}", {"answer": []}),
        ("0.0 (float)", 0.0),
        ("-1", -1),
        ("True", True),
        ("'null'", "null"),
        ("'nil'", "nil"),
        ("'none'", "none"),
        ("'N/A'", "N/A"),
        ("'n/a'", "n/a"),
        ("'unknown'", "unknown"),
        ("'abstain'", "abstain"),
        ("\"I don't know\"", "I don't know"),
        ("'?'", "?"),
        ("'-'", "-"),
        ("'.'", "."),
        ("' ' (single space)", " "),
        ("'\\n'", "\n"),
        ("'TODO'", "TODO"),
        ("'undefined'", "undefined"),
        ("'nan'", "nan"),
        ("'{}' (string)", "{}"),
        ("'[]' (string)", "[]"),
        ("'null' json-ish 'null\\n'", "null\n"),
        ("'no'", "no"),
        ("'false'", "false"),
        ("'unsolvable' upper 'UNSOLVABLE'", "UNSOLVABLE"),
        ("'unsat'", "unsat"),
        ("'impossible'", "impossible"),
        ("'no answer'", "no answer"),
        ("'skip'", "skip"),
        ("'pass'", "pass"),
        ("'error'", "error"),
        ("'0'", "0"),
        ("'False'", "False"),
        ("'nothing'", "nothing"),
        ("'empty'", "empty"),
        ("'不知道'", "不知道"),
        ("{'abstain': True}", {"abstain": True}),
        ("{'said': None}", {"said": None}),
        ("[[], []]", [[], []]),
        ("[[[]]]", [[[]]]),
        ("()->[] tuple ()", []),
        ("{'': ''}", {"": ""}),
    ]
    # dedupe on repr of (label)
    seen = set()
    ded = []
    for lab, val in out:
        if lab in seen:
            continue
        seen.add(lab)
        ded.append((lab, val))
    return ded


def by_rubric(report):
    agg = {}
    for s in report.scores:
        a = agg.setdefault(s.rubric_id, {"awarded": 0.0, "possible": 0.0,
                                         "n": 0, "paid_items": []})
        a["awarded"] += s.awarded
        a["possible"] += s.possible
        a["n"] += 1
        if s.awarded > 1e-9:
            a["paid_items"].append((s.item_id, round(s.awarded, 6), s.verdict))
    for a in agg.values():
        a["awarded"] = round(a["awarded"], 6)
        a["possible"] = round(a["possible"], 6)
    return agg


def verdict_counts(report):
    out = {}
    for s in report.scores:
        out[s.verdict] = out.get(s.verdict, 0) + 1
    return out


def main():
    result = {}
    for qt in PAPERS:
        try:
            module, paper, key_doc, oracle = setup(qt)
        except Exception as exc:                      # noqa: BLE001
            result[qt] = {"setup_error": traceback.format_exc()}
            continue
        axes_fn = getattr(module, "axes", None)
        ids = [e["item_id"] for e in key_doc["items"]]
        entry = {"paper_id": paper.paper_id, "n_items": len(ids),
                 "in_builders": qt in BUILDERS, "examinees": {}}

        # oracle
        try:
            rep = _mark(key_doc, oracle, "oracle", axes_fn)
            entry["examinees"]["ORACLE"] = {
                "awarded": round(rep.awarded, 6),
                "possible": round(rep.possible, 6),
                "n_answers": len(oracle),
                "verdicts": verdict_counts(rep),
                "by_rubric": by_rubric(rep),
                "missing_items": [i for i in ids if i not in oracle],
                "underpaid_items": [(s.item_id, s.rubric_id,
                                     round(s.awarded, 6), round(s.possible, 6),
                                     s.verdict,
                                     json.dumps(s.detail, default=str)[:400])
                                    for s in rep.scores
                                    if s.awarded < s.possible - 1e-9],
            }
        except Exception:                             # noqa: BLE001
            entry["examinees"]["ORACLE"] = {"raised": traceback.format_exc()}

        for label, value in tokens():
            answers = {i: value for i in ids}
            try:
                rep = _mark(key_doc, answers, "null", axes_fn)
                rec = {"awarded": round(rep.awarded, 6),
                       "possible": round(rep.possible, 6),
                       "verdicts": verdict_counts(rep)}
                if rep.awarded > 1e-9:
                    rec["by_rubric"] = {k: v for k, v in by_rubric(rep).items()
                                        if v["awarded"] > 1e-9}
                entry["examinees"][label] = rec
            except Exception as exc:                  # noqa: BLE001
                entry["examinees"][label] = {
                    "raised": "%s: %s" % (type(exc).__name__, exc)}
        result[qt] = entry

    out_path = os.path.join(HERE, "calib.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=1, sort_keys=True, default=str)

    # ---- terse console table ----
    for qt in PAPERS:
        e = result[qt]
        if "setup_error" in e:
            print("== %s SETUP ERROR ==\n%s" % (qt, e["setup_error"]))
            continue
        o = e["examinees"]["ORACLE"]
        print("== %s (%s) items=%d" % (qt, e["paper_id"], e["n_items"]))
        if "raised" in o:
            print("   ORACLE RAISED: %s" % o["raised"].splitlines()[-1])
        else:
            print("   ORACLE            %10.3f / %-10.3f  %s" %
                  (o["awarded"], o["possible"], o["verdicts"]))
            if o["missing_items"]:
                print("     oracle omits %d items: %s"
                      % (len(o["missing_items"]), o["missing_items"][:6]))
            for u in o["underpaid_items"]:
                print("     UNDERPAID %s [%s] %.3f/%.3f %s %s"
                      % (u[0], u[1], u[2], u[3], u[4], u[5]))
        for label, _ in tokens():
            r = e["examinees"][label]
            if "raised" in r:
                print("   %-34s RAISED %s" % (label, r["raised"][:110]))
            elif r["awarded"] > 1e-9:
                print("   %-34s %10.3f / %-10.3f  PAID  %s" %
                      (label, r["awarded"], r["possible"],
                       {k: v["awarded"] for k, v in r["by_rubric"].items()}))
            else:
                print("   %-34s %10.3f / %-10.3f" %
                      (label, r["awarded"], r["possible"]))
    print("\nwrote %s" % out_path)


if __name__ == "__main__":
    main()
