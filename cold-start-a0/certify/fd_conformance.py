"""Does `fd_adapter`'s Fast Downward path work, and is switching to it free?

**What this does and does not establish, said first.**

`A0_REPORT.md` §7.4 asked to connect Fast Downward and re-run M4. **It is now
connected** (`.toolchain/downward`, built with the winlibs mingw-w64 gcc 16.1.0
also under `.toolchain/`; see `BLOCKER_FAST_DOWNWARD.md` for how). This module
therefore has two modes and picks between them by itself:

**Real mode**, when `backends.find_fast_downward()` finds a planner: re-run M4
through it on every compiled instance and compare status and optimal length
against the bundled BFS. Writes `artifacts/fd_real.json`.

**Stand-in mode**, when it does not: an executable that speaks FD's command-line
and plan-file protocol exactly and answers by delegating to the bundled BFS, so
that every line of `backends.py` a real FD would touch is still exercised.
A stand-in that agrees by construction proves nothing about search quality and
this file has never claimed otherwise — it proves the wiring, and the wiring is
the "no caller changes" claim.

Connecting the real planner immediately earned its keep twice, and both are
recorded rather than quietly fixed:

* **our PDDL was not standard-conformant.** The domain declared
  `(:types buttoncell doorcell markedcell - cell)` and never introduced `cell`
  itself. The bundled parser is lenient and accepted it; FD's translator dies
  with `KeyError: 'cell'`. Fixed in `gen_pddl_a0` (D-A0-019) — the stub had
  been masking a portability bug for the whole sprint;
* **`fd_adapter` cannot express "proved unsolvable" on the FD path.** The stub
  raises `no plan exists`; FD exits 12 with no plan file and the adapter turns
  that into a generic `RuntimeError`. Under constraint 6 that is exactly the
  distinction that matters. Handled in `certify/fd_unsat.py` (D-A0-020);
  upstream is not modified.
"""

import json
import os
import subprocess
import sys
import tempfile
from typing import Dict, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap  # noqa: F401,E402

from engines import fd_adapter  # noqa: E402
from engines.fd_adapter import backends  # noqa: E402

from certify.fd_unsat import is_unsat  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STANDIN = '''#!/usr/bin/env python
"""A Fast Downward conformance stand-in.

Speaks FD's CLI and plan-file protocol; answers with the bundled grounded-STRIPS
BFS.  Exists only so that `fd_adapter`'s FD code path can be exercised where Fast
Downward itself cannot be built.  See certify/fd_conformance.py.
"""
import os, sys
sys.path.insert(0, %(engine_rig)r)

from engines.fd_adapter.pddl import parse_domain, parse_problem
from engines.fd_adapter.search import breadth_first_plan

argv = sys.argv[1:]
plan_file = "sas_plan"
positional = []
i = 0
while i < len(argv):
    if argv[i] == "--plan-file":
        plan_file = argv[i + 1]; i += 2
    elif argv[i] == "--search":
        i += 2
    elif argv[i].startswith("--"):
        i += 2
    else:
        positional.append(argv[i]); i += 1

domain = parse_domain(open(positional[0], encoding="utf-8").read())
problem = parse_problem(open(positional[1], encoding="utf-8").read())
plan = breadth_first_plan(domain, problem)
if plan is None:
    sys.stderr.write("Search stopped without finding a solution.\\n")
    sys.exit(12)
with open(plan_file, "w", encoding="utf-8") as fh:
    for action in plan:
        fh.write(action.text() + "\\n")
    fh.write("; cost = %%d (unit cost)\\n" %% len(plan))
'''


def _write_standin(directory: str) -> str:
    path = os.path.join(directory, "fast-downward.py")
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(STANDIN % {"engine_rig": os.path.join(
            os.path.dirname(ROOT), "engine-rig")})
    return path


def check(domain: str, problem: str) -> Dict[str, object]:
    with tempfile.TemporaryDirectory() as workdir:
        standin = _write_standin(workdir)
        previous = os.environ.get("FAST_DOWNWARD")
        os.environ["FAST_DOWNWARD"] = standin
        try:
            found = backends.find_fast_downward()
            discovery_ok = found == standin
            # No `prefer=` argument: the adapter must pick FD on its own.
            fd_plan = fd_adapter.solve(domain, problem)
            stub_plan = fd_adapter.solve(domain, problem, prefer="stub")
        finally:
            if previous is None:
                os.environ.pop("FAST_DOWNWARD", None)
            else:
                os.environ["FAST_DOWNWARD"] = previous

    return {
        # The stand-in lives in a fresh temp directory each run, so the path is
        # reported as a stable marker: an absolute temp path in a checked-in
        # artefact would break byte-reproducibility for nothing.
        "discovery": {"found": "<tempdir>/fast-downward.py" if discovery_ok
                      else found,
                      "via": "FAST_DOWNWARD", "ok": discovery_ok},
        "fd_path": {"backend": fd_plan.backend, "length": fd_plan.length,
                    "actions": list(fd_plan.actions)},
        "stub_path": {"backend": stub_plan.backend, "length": stub_plan.length},
        "backend_reported": fd_plan.backend == "fast-downward",
        "same_length": fd_plan.length == stub_plan.length,
        "same_plan": list(fd_plan.actions) == list(stub_plan.actions),
        "validated": True,     # solve() refuses to return an unvalidated plan
        "green": bool(discovery_ok and fd_plan.backend == "fast-downward"
                      and fd_plan.length == stub_plan.length),
        "caveat": "a conformance stand-in, not Fast Downward: this tests "
                  "discovery, invocation, sas_plan parsing and validation, and "
                  "nothing about FD's search",
    }


INSTANCES = [
    ("a0-base", os.path.join(ROOT, "theory", "generated")),
    ("a0-no-button", os.path.join(ROOT, "theory", "generated_no_button")),
    ("a0p-base", os.path.join(ROOT, "prime", "theory", "generated")),
]


def check_real(name: str, directory: str) -> Dict[str, object]:
    """The real thing, when it is installed: FD against the bundled BFS.

    This is the half `check()` cannot do. Both backends are optimal for unit
    costs, so the plans must have the same length; the actions may legitimately
    differ, since more than one optimal plan can exist.
    """
    domain = os.path.join(directory, "domain.pddl")
    problem = os.path.join(directory, "problem.pddl")
    if not os.path.exists(domain):
        return {"skipped": "not compiled — run the pipeline first"}

    def _solve(prefer):
        try:
            plan = fd_adapter.solve(domain, problem, prefer=prefer)
            return {"status": "SAT", "backend": plan.backend,
                    "length": plan.length, "actions": list(plan.actions)}
        except RuntimeError as exc:
            # The stub says "no plan exists"; Fast Downward says exit 12.  Same
            # claim, two spellings -- see certify/fd_unsat.py.
            if not is_unsat(exc):
                raise
            return {"status": "UNSAT"}

    fd, stub = _solve(None), _solve("stub")
    agree = (fd["status"] == stub["status"]
             and fd.get("length") == stub.get("length"))
    # On the UNSAT branch there is no Plan object and so no backend to report;
    # requiring one there would fail the instance we most care about.
    backend_ok = (fd.get("backend") == "fast-downward"
                  if fd["status"] == "SAT" else True)
    return {
        "instance": name,
        "fast_downward": fd,
        "stub": stub,
        "same_status": fd["status"] == stub["status"],
        "same_length": fd.get("length") == stub.get("length"),
        "identical_plan": fd.get("actions") == stub.get("actions"),
        "backend_reported": backend_ok,
        "green": bool(agree and backend_ok),
    }


def main() -> int:
    real = backends.find_fast_downward()
    if real is not None and "--stand-in" not in sys.argv:
        # A real Fast Downward is reachable: run M4 again through it, which is
        # the half certify/fd_conformance could not previously reach.
        report = {"fast_downward": real,
                  "instances": [check_real(name, d) for name, d in INSTANCES]}
        out = os.path.join(ROOT, "artifacts", "fd_real.json")
        with open(out, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(json.dumps(report, indent=2, sort_keys=True))
        checked = [i for i in report["instances"] if "skipped" not in i]
        return 0 if checked and all(i["green"] for i in checked) else 1

    generated = os.path.join(ROOT, "theory", "generated")
    report = {
        "real_fast_downward_present": False,
        "a0-base": check(os.path.join(generated, "domain.pddl"),
                         os.path.join(generated, "problem.pddl")),
    }
    out = os.path.join(ROOT, "artifacts", "fd_conformance.json")
    with open(out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: (v if not isinstance(v, dict) else
                          {kk: vv for kk, vv in v.items() if kk != "fd_path"})
                      for k, v in report.items()}, indent=2, sort_keys=True))
    return 0 if report["a0-base"]["green"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
