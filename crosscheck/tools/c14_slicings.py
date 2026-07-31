"""Every denominator in the C14 headline table, each from a stated rule.

`0 of 303` is only interesting if the 303 is honest, so the deliverable publishes
the good/total under a dozen different ways of choosing the corpus.  Those numbers
were originally produced by hand, and one of them (a "narrowest defensible"
slicing reported as 115) turned out not to be reproducible under any rule anybody
had written down -- the reproducible version of the same idea is 133.  A number in
a published table that nobody can re-derive is an assertion, so every row now
comes from a named function here and `c14_verify.py` re-checks them.

    python -m crosscheck.tools.c14_slicings [--json]

Reads the committed census; computes nothing about PDDL itself.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RUN = os.path.join(REPO, "crosscheck", "runs",
                   "20260730T120005Z-C14-four-forms-is-three-and-a-half", "out")

# Paths that are copies, snapshots or the compiler's own test fixtures rather
# than a hand-authored theory.  Used only by the "canonical" slicings.
DERIVED = ("/runs/", "/artifacts/", "/packs/", "/snapshots/",
           "handover_packages/", "handover_bundles/", "tests/fixtures/")


def owed(rec: dict) -> int:
    """Actions this file owes a PDDL form.

    A refused file owes its rules: a refusal is zero actions delivered, not zero
    actions owed, and folding refusals out of the denominator is how a 3-of-4
    becomes a 4-of-4 on paper.
    """
    if rec["outcome"] == "compiled":
        return len(rec["actions"])
    if rec["outcome"] == "refused":
        return rec.get("n_rules") or 0
    return 0


def good(rec: dict) -> int:
    return sum(1 for a in rec.get("actions", []) if a["semantically_non_empty"])


def _sha(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def source_hash(rec: dict) -> str:
    return _sha(os.path.join(REPO, rec["dsl"]))


def domain_hash(rec: dict) -> str:
    """Hash of the *generated* domain -- coarser than the source hash.

    Distinct theories can compile to identical PDDL, which is itself a finding:
    the backend is lossy enough that different books become the same domain.
    """
    if rec["outcome"] != "compiled":
        return "src:" + source_hash(rec)
    return _sha(os.path.join(RUN, "fd_translate", rec["slug"] + ".domain.pddl"))


def dedup(recs: list, key) -> list:
    seen, out = set(), []
    for rec in sorted(recs, key=lambda r: r["dsl"]):
        k = key(rec)
        if k not in seen:
            seen.add(k)
            out.append(rec)
    return out


def canonical(recs: list) -> list:
    return [r for r in recs if not any(s in r["dsl"] for s in DERIVED)]


def fd_accepted(recs: list) -> list:
    out = []
    for rec in recs:
        for chk in rec.get("independent_checks", []):
            if chk["tool"] == "fast-downward-translate" and chk["accepted"]:
                out.append(rec)
                break
    return out


def slicings(files: list) -> list:
    """``[(label, files, actions, good), ...]`` -- every published denominator."""
    bearing = [r for r in files if owed(r)]
    compiled = [r for r in files if r["outcome"] == "compiled"]
    rows = [
        ("all .dsl in repo (headline)", bearing),
        ("compiled only, refusals folded out (the flattering slice)", compiled),
        ("deduplicated by DSL source bytes", dedup(bearing, source_hash)),
        ("deduplicated by generated-domain bytes", dedup(bearing, domain_hash)),
        ("excluding theory-compiler test fixtures",
         [r for r in bearing if "tests/fixtures/" not in r["dsl"]]),
        ("canonical hand-authored theories only", canonical(bearing)),
        ("narrowest defensible: canonical, deduped by generated-domain bytes",
         dedup(canonical(bearing), domain_hash)),
        ("domains an independent planner accepted", fd_accepted(compiled)),
        ("theory-compiler/ contribution alone",
         [r for r in bearing if r["dsl"].startswith("theory-compiler/")]),
    ]
    return [(label, len(rs), sum(map(owed, rs)), sum(map(good, rs)))
            for label, rs in rows]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    census = json.load(open(os.path.join(RUN, "census.json"), encoding="utf-8"))
    rows = slicings(census["files"])

    if args.json:
        print(json.dumps([{"slicing": l, "files": f, "actions": a, "good": g}
                          for l, f, a, g in rows], indent=2))
        return 0

    print("| slicing | files | actions | good |")
    print("|---|---|---|---|")
    for label, nf, na, ng in rows:
        print("| %s | %d | %d | **%d** |" % (label, nf, na, ng))
    worst = max(g for _, _, _, g in rows)
    print("\nmax good over every slicing: %d" % worst)
    # The single most attackable claim in the deliverable, checked here rather
    # than asserted in prose: no choice of corpus rescues the number.
    best_file = max((good(r) for r in census["files"]), default=0)
    print("max good over any single file: %d" % best_file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
