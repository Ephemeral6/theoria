"""C14 -- cross-tabulate the census against Fast Downward's verdict.

The census asks whether an action *means* anything; FD's translator asks whether
the domain *parses and grounds*.  They are different questions and the whole
finding lives in how they disagree, so the table is built rather than asserted:

  * a domain FD rejects delivers no planning form at all;
  * a domain FD accepts may still be worthless, because an empty precondition
    and an `(and)` effect are perfectly legal PDDL -- an action that is always
    applicable and changes nothing is a syntactically valid no-op.

If every FD-accepted domain turns out to be one whose actions are vacuous, then
"the translator accepted it" is not evidence for the fourth form; it is evidence
that the fourth form is empty in a way a parser cannot see.

    python -m crosscheck.tools.c14_crosstab <census.json>
"""

from __future__ import annotations

import json
import os
import sys


def main(argv) -> int:
    path = argv[1] if len(argv) > 1 else None
    if not path:
        print(__doc__)
        return 2
    data = json.load(open(path, encoding="utf-8"))

    rows = []
    for rec in data["files"]:
        if rec["outcome"] != "compiled":
            continue
        fd = next((c for c in rec.get("independent_checks", [])
                   if c["tool"] == "fast-downward-translate"), None)
        lib = next((c for c in rec.get("independent_checks", [])
                    if c["tool"] == "pddl-3.1-parser"), None)
        acts = rec["actions"]
        profile = set()
        for a in acts:
            profile.update(a["defects"])
        rows.append({
            "dsl": rec["dsl"],
            "n_actions": len(acts),
            "fd_accepted": fd["accepted"] if fd else None,
            "fd_rc": fd["returncode"] if fd else None,
            "lib_accepted": lib["accepted"] if lib else None,
            "malformed": bool({"undeclared-variable", "undeclared-predicate"}
                              & profile),
            "vacuous_only": bool(profile) and not (
                {"undeclared-variable", "undeclared-predicate"} & profile),
            "profile": sorted(profile),
            "n_vacuous": sum(1 for a in acts
                             if a["n_effect_literals"] == 0
                             or a["n_precondition_literals"] == 0),
            "fd_error": _first_error(fd["output"]) if fd else "",
        })

    acc = [r for r in rows if r["fd_accepted"]]
    rej = [r for r in rows if r["fd_accepted"] is False]

    print("domains compiled: %d   FD accepted: %d   FD rejected: %d"
          % (len(rows), len(acc), len(rej)))
    print()
    print("FD-accepted domains whose every action is nevertheless vacuous "
          "(no undeclared name, but an empty precondition or empty effect): %d/%d"
          % (sum(1 for r in acc if r["vacuous_only"]), len(acc)))
    print("FD-rejected domains that are malformed by the census too: %d/%d"
          % (sum(1 for r in rej if r["malformed"]), len(rej)))
    print()
    print("| DSL | actions | census profile | FD | rc | pddl3.1 | vacuous actions |")
    print("|---|---|---|---|---|---|---|")
    for r in sorted(rows, key=lambda r: (not r["fd_accepted"], r["dsl"])):
        print("| `%s` | %d | %s | %s | %s | %s | %d/%d |"
              % (r["dsl"], r["n_actions"], ", ".join(r["profile"]) or "clean",
                 "accept" if r["fd_accepted"] else "REJECT", r["fd_rc"],
                 "accept" if r["lib_accepted"] else "REJECT",
                 r["n_vacuous"], r["n_actions"]))
    print()
    print("### First FD error per rejected domain\n")
    seen = {}
    for r in sorted(rej, key=lambda r: r["dsl"]):
        seen.setdefault(r["fd_error"], []).append(r["dsl"])
    for err, files in sorted(seen.items(), key=lambda kv: -len(kv[1])):
        print("* **%s** -- %d domain(s): %s"
              % (err, len(files), ", ".join("`%s`" % f for f in files[:6])
                 + (" ..." if len(files) > 6 else "")))
    return 0


def _first_error(out: str) -> str:
    """FD's parse errors are a breadcrumb trail; the useful line is the last one."""
    lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
    for ln in lines:
        if ln.startswith(("Error:", "SystemExit")):
            return ln[:200]
    tail = [ln for ln in lines if not ln.startswith(("Parsing", "->", "Warning!"))]
    return (tail[-1] if tail else (lines[-1] if lines else ""))[:200]


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
