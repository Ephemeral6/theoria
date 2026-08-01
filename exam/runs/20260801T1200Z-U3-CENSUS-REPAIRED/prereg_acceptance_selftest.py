# -*- coding: utf-8 -*-
"""Negative control for `prereg_acceptance.py`.

The audit returned ACCEPTED on every condition.  An auditor that has only ever
been observed to say yes has not been shown to check anything, so each of the
four conditions is broken on purpose here and the audit must go red on that
condition and (where the conditions are genuinely independent) on that one
alone.

Each breakage is a plausible way the pre-registration could rot, not a
contrived one:

* `S_min = 0.0`   -- the specificity floor written down but set to a value that
                     cannot fire.  This is `launch_blockers` 9.15's disease with
                     a different cause, and condition C must catch it.
* `BA floor >= `  -- `>=` instead of `>`, which credits the two constants the
                     floor exists to refuse.  Condition D must catch it.
* one item's basis blanked -- A3 must catch it, and A4 with it.
* a fourth class shipped -- A1/A2 must catch it.
"""

from __future__ import annotations

import json
import os
import runpy
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
AUDIT = os.path.join(HERE, "prereg_acceptance.py")
OUT = os.path.join(HERE, "prereg_acceptance.json")

PATCHES = {
    "S_min_cannot_fire": """
import sys; sys.path.insert(0, %(repo)r)
from exam import endpoint as ep
ep.S_MIN = 0.0
""",
    "BA_floor_not_strict": """
import sys; sys.path.insert(0, %(repo)r)
from exam import endpoint as ep
_real = ep.adjudicate
def _loose(record, **kw):
    out = _real(record, **kw)
    r = out if isinstance(out, dict) else out
    # credit anything the strict floor refused only on BA
    reasons = [x for x in (r.get("reasons") or []) if "BA" not in x]
    if len(reasons) != len(r.get("reasons") or []):
        r["reasons"] = reasons
        if not reasons:
            r["verdict"] = ep.VERDICT_CREDITED
            r["credited"] = True
    return out
ep.adjudicate = _loose
""",
    "one_basis_blanked": """
import sys; sys.path.insert(0, %(repo)r)
from exam import model
_real = model.read_json
def _blank(path):
    doc = _real(path)
    if str(path).endswith("verdict_prereg.json"):
        doc["class_inventory"]["items"][0]["constructive_justification"] = ""
    return doc
model.read_json = _blank
""",
    "fourth_class_shipped": """
import sys; sys.path.insert(0, %(repo)r)
from exam.tools import endpoint_verdict as EV
_real = EV._paper_and_key
def _extra():
    module, paper, key = _real()
    paper.items[0].truth["class"] = "medium_unsolvable"
    return module, paper, key
EV._paper_and_key = _extra
""",
}


def run(plugin: str = "") -> dict:
    env = dict(os.environ)
    code = "import runpy, sys\n"
    if plugin:
        code += plugin + "\n"
    code += "runpy.run_path(%r, run_name='__main__')\n" % AUDIT
    proc = subprocess.run([sys.executable, "-c", code],
                          cwd=REPO, env=env, capture_output=True, text=True)
    doc = {}
    if os.path.exists(OUT):
        doc = json.load(open(OUT, encoding="utf-8"))
    return {"exit": proc.returncode,
            "verdict": doc.get("verdict"),
            "failed": doc.get("failed_conditions", []),
            "stderr_tail": proc.stderr.strip().splitlines()[-1:] }


def main() -> int:
    results = {}
    for name, body in PATCHES.items():
        results[name] = run(body % {"repo": REPO})
        r = results[name]
        print("%-22s exit=%s verdict=%s" % (name, r["exit"], r["verdict"]))
        for c in r["failed"]:
            print("    caught:", c)
        if r["stderr_tail"] and r["verdict"] is None:
            print("    stderr:", r["stderr_tail"][0])

    # restore the true artefact, so the run record does not ship a broken one
    clean = run("")
    print()
    print("restored:", clean["verdict"], clean["failed"])
    results["_restored"] = clean

    silent = [n for n, r in results.items()
              if n != "_restored" and not r["failed"]]
    with open(os.path.join(HERE, "prereg_acceptance_selftest.json"),
              "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps({"breakages": results,
                             "breakages_the_audit_missed": silent},
                            indent=1, ensure_ascii=False, sort_keys=True) + "\n")
    print("breakages the audit MISSED:", silent or "none")
    return 0 if not silent and clean["verdict"] == "ACCEPTED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
