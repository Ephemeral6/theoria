"""The concept account, and the upstream pin.  Two small bookkeeping products.

**Concept accounts** price each object in the word table against a
responsibility-complete alternative, using A0's `pipeline/concept_account.py`
unmodified.  The `compress:` figures in `theory/domain.dsl` come from here and
are not invented.

A3's verdict differs from A0's and A2's, and the difference is a result rather
than noise.  Both of those spikes had to admit their Button and Door at a
*negative* account — A2's came out at −5 and −1 — and justify them on
responsibility-completeness plus the invariant language having no pixel-level
paraphrase of the latch.  A3's three objects all pay for themselves.  The cause
is mechanical: A0's Button is a **latch** that fires once, so an object
declared to explain one event costs more than it saves, while A3's Switch is a
**toggle** that recolours dozens of times and earns its declaration outright.

That matters beyond bookkeeping.  A0's finding O-04 — that constraint 5
(compression) and constraint 2 (responsibility-completeness) can point in
opposite directions — turns out to be **contingent on irreversibility**, not
intrinsic to the criteria.  Reversibility was adopted for a different reason
(F-12: re-witnessable rules); flipping the sign of the concept account was not
predicted and is recorded here because a framework-level claim that quietly
depends on a world-design choice should not stay quiet.

**The upstream pin** hashes every `cold-start-a0` file A3 imports.  That tree
belongs to another track and two other sessions work this repository
concurrently, so "which version of the compiler produced these artefacts" is a
question the artefacts have to answer on their own.  A3 never writes there; it
records what it read.
"""

import hashlib
import json
import os
import sys
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap  # noqa: F401,E402

from pipeline.concept_account import accounts  # noqa: E402  (cold-start-a0)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(ROOT)
ARTIFACTS = os.path.join(ROOT, "artifacts")
THEORY = os.path.join(ROOT, "theory")

NAME_BY_COLOUR = {7: "Switch", 5: "Door", 6: "Cart"}

#: Every upstream module A3 imports, directly or through one of these.
UPSTREAM = [
    "compile/__init__.py",
    "compile/compile_a0.py",
    "compile/dialect.py",
    "compile/gen_lean_a0.py",
    "compile/gen_pddl_a0.py",
    "compile/gen_python_a0.py",
    "compile/problem.py",
    "certify/__init__.py",
    "certify/lean_check.py",
    "certify/replay.py",
    "pipeline/__init__.py",
    "pipeline/atoms_a0.py",
    "pipeline/board.py",
    "pipeline/concept_account.py",
    "pipeline/engines_stage.py",
    "pipeline/multi_miner.py",
    "pipeline/reidentify.py",
    "pipeline/segment_operators.py",
]


def _sha256(path: str) -> str:
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def write_accounts(candidates: str = "candidates_l1.jsonl",
                   dsl: str = "domain.dsl",
                   out_name: str = "concept_accounts.json") -> List[Dict]:
    rows = accounts(os.path.join(ARTIFACTS, candidates),
                    os.path.join(THEORY, dsl), NAME_BY_COLOUR)
    payload = []
    for row in rows:
        payload.append({
            "object_id": row.object_id,
            "name": row.name,
            "colour": row.colour,
            "script_with": row.script_with,
            "script_without": row.script_without,
            "script_delta": row.script_delta,
            "responsibility_cells": [list(c) for c in row.responsibility_cells],
            "laws_naming_it": list(row.laws_naming_it),
            "rules_targeting_it": list(row.rules_targeting_it),
            "manual_bytes": row.manual_bytes,
        })
    out = os.path.join(ARTIFACTS, out_name)
    with open(out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps({
            "source": candidates,
            "manual": dsl,
            "note": ("priced against a responsibility-complete alternative "
                     "(Theoria 1.8, as corrected by A0's O-04). Every object "
                     "here has a POSITIVE account, unlike A0's and A2's — see "
                     "the module docstring: the cause is the toggle."),
            "accounts": payload,
        }, indent=2, sort_keys=True) + "\n")
    return payload


def write_upstream_pin(out_name: str = "upstream_pin.json") -> Dict[str, object]:
    a0 = os.path.join(REPO, "cold-start-a0")
    files = {}
    missing = []
    for rel in UPSTREAM:
        path = os.path.join(a0, rel)
        if os.path.exists(path):
            files["cold-start-a0/" + rel] = _sha256(path)
        else:
            missing.append("cold-start-a0/" + rel)

    for rel in ("CONTRACTS/candidates_schema.md", "CONTRACTS/dsl_grammar_v0.2.md",
                "engine-rig/common/candidates.py",
                "engine-rig/tools/validate_candidates.py"):
        path = os.path.join(REPO, rel)
        if os.path.exists(path):
            files[rel] = _sha256(path)
        else:
            missing.append(rel)

    payload = {
        "note": ("Every file outside cold-start-a3 that A3's results depend "
                 "on. Two other sessions work this repo concurrently; a "
                 "silent change upstream would otherwise silently change "
                 "these numbers."),
        "files": files,
        "missing": missing,
    }
    out = os.path.join(ARTIFACTS, out_name)
    with open(out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return payload


def main() -> int:
    for row in write_accounts():
        print("%-8s colour %-3s with %-6d without %-6d delta %+d"
              % (row["name"], row["colour"], row["script_with"],
                 row["script_without"], row["script_delta"]))
    pin = write_upstream_pin()
    print("upstream pin: %d files, %d missing"
          % (len(pin["files"]), len(pin["missing"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
