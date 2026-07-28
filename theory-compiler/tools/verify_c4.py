"""C4 acceptance, end to end: both certificate kinds, compiled and axiom-checked.

    python -m tools.verify_c4 [--out <dir>]

The board item asks for at least one deadlock theorem and at least one IC3
三件套 to compile in Lean with an empty axiom set. This script is that claim in
executable form: it grounds the task itself, re-derives every obligation, emits
each development, runs `lean` on it, and refuses to report success unless
`#print axioms` says "does not depend on any axioms" for every theorem it
emitted. It also runs a **negative control** — the same file with the pattern
moved one cell — and refuses to report success unless `lean` rejects it.

Exit code 0 means all of that held. Anything else means it did not.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from typing import Dict, List, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))

from theory_compiler import deadlock_certificate as dc          # noqa: E402
from theory_compiler import strips, strips_encoding             # noqa: E402
from theory_compiler.certificate import CertificateError        # noqa: E402
from theory_compiler.strips import Atom                         # noqa: E402
from theory_compiler.generators import gen_lean_deadlock        # noqa: E402
from theory_compiler.generators.gen_lean import generate_lean   # noqa: E402
from theory_compiler.ic3_certificate import load_ic3_certificate  # noqa: E402
from theory_compiler.parser.theory_parser import parse_theory   # noqa: E402
from theory_compiler.problem import load_problem                # noqa: E402

FIXTURES = os.path.join(ROOT, "tests", "fixtures")
STRIPS_DIR = os.path.join(FIXTURES, "strips")
TOOLCHAIN = os.path.join(ROOT, "lean", "lean-toolchain")

DEADLOCK_THEOREMS = ("pat_pins", "closed_pinned", "dead_closed", "no_goal_pinned",
                     "pat_no_goal", "dead_persists", "dead", "pat_witness",
                     "level_is_winnable")
IC3_THEOREMS = ("inv_init", "inv_closed", "inv_all", "unsolvable")


def lean_binary() -> Optional[str]:
    return os.environ.get("LEAN") or shutil.which("lean")


def run_lean(source: str, workdir: str, stem: str) -> Dict:
    # Absolute, because `cwd` is the same directory: a relative path would be
    # resolved against it twice and `lean` would report a missing file in a
    # tenth of a second, which reads exactly like a failed proof.
    workdir = os.path.abspath(workdir)
    os.makedirs(workdir, exist_ok=True)
    target = os.path.join(workdir, "%s.lean" % stem)
    with open(target, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(source)
    shutil.copy(TOOLCHAIN, workdir)
    started = time.time()
    result = subprocess.run([lean_binary(), target], cwd=workdir,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            timeout=1800)
    output = result.stdout.decode("utf-8", errors="replace")
    if result.returncode != 0:
        # Printed rather than swallowed: an unexplained non-zero exit is the one
        # outcome that must never be mistaken for "the proof did not go through".
        print("--- lean %s exited %d ---\n%s"
              % (stem, result.returncode, output[:2000]), file=sys.stderr)
    return {
        "returncode": result.returncode,
        "seconds": round(time.time() - started, 1),
        "output": output,
    }


def axioms_empty(output: str, names) -> List[str]:
    """Which of `names` did not report an empty axiom set."""
    return [n for n in names
            if "'%s' does not depend on any axioms" % n not in output]


PAT_MARKER = "def Pat (s : St) : Bool :=\n  "


def tamper(source: str, cert, encoding) -> str:
    """The same file with the pattern moved one region in. Must go red.

    The edit is aimed at the body of `Pat` and nowhere else: the same cell name
    appears dozens of times inside `legal`, and a blind `replace` would mutate a
    move instead of the pattern and leave the file provable — a negative control
    that passes for the wrong reason is worse than none.
    """
    head, rest = source.split(PAT_MARKER, 1)
    line, tail = rest.split("\n", 1)
    mentioned = {a.args[-1] for a in cert.pattern}
    replacement = next(c for c in encoding.cells if c not in mentioned)
    moved = line.replace(".%s" % cert.pattern[0].args[-1], "." + replacement, 1)
    if moved == line:
        raise SystemExit("the negative control did not change anything")

    # And check the control is a control: the moved pattern has to be one this
    # track's own re-derivation rejects. Otherwise `lean` going red would be
    # evidence of a typo somewhere, not of the axiom check having teeth.
    first = cert.pattern[0]
    probe = dc.DeadlockCertificate(
        claim="negative control", domain=cert.domain, problem=cert.problem,
        pattern=[Atom(first.name, first.args[:-1] + (replacement,))] + list(cert.pattern[1:]),
        closure=cert.closure, n_deleting_actions=-1, blocked_actions=[],
        goal_conflict=None, coverage="", produced_by="control", provenance="control")
    try:
        dc.recheck(probe, encoding)
    except CertificateError:
        pass
    else:
        raise SystemExit("the negative control's pattern is still a dead region")
    return head + PAT_MARKER + moved + "\n" + tail


def deadlock_case(name: str, certificate: str, workdir: str) -> Dict:
    task = strips.load_task(os.path.join(STRIPS_DIR, "sokoban_domain.pddl"),
                            os.path.join(STRIPS_DIR, "sokoban_open4far.pddl"))
    encoding = strips_encoding.PositionalEncoding(task)
    encoding_stats = strips_encoding.verify(encoding)
    cert = dc.load_deadlock_certificate(os.path.join(FIXTURES, certificate),
                                        task, encoding)
    plan = strips_encoding.shortest_plan(encoding)
    witness = min(s for s in encoding.states()
                  if encoding.holds(s, list(cert.pattern)))
    source = gen_lean_deadlock.generate_deadlock_lean(
        task, encoding, cert, plan=plan, witness=witness)

    reachable = [encoding.decode(a) for a in strips.reachable(task)]
    report = {
        "case": name,
        "pattern": cert.pattern_text,
        "closure": cert.closure,
        "ground_actions": len(task.actions),
        "coverage_claimed": cert.coverage,
        "deleting_actions": len(cert.deleting_actions(task)),
        "encoding": encoding_stats,
        "bite": dc.bite(cert, encoding, reachable),
        "plan_length": len(plan) if plan is not None else None,
    }

    lean = run_lean(source, workdir, "Deadlock_" + name)
    report["lean"] = {"returncode": lean["returncode"], "seconds": lean["seconds"]}
    report["axioms_not_empty"] = axioms_empty(lean["output"], DEADLOCK_THEOREMS)
    report["sorry_in_output"] = "sorryAx" in lean["output"]
    report["ok"] = (lean["returncode"] == 0
                    and not report["axioms_not_empty"]
                    and not report["sorry_in_output"])

    control = run_lean(tamper(source, cert, encoding), workdir, "Control_" + name)
    report["negative_control"] = {
        "returncode": control["returncode"],
        "seconds": control["seconds"],
        "rejected": control["returncode"] != 0,
    }
    report["ok"] = report["ok"] and report["negative_control"]["rejected"]
    return report


def ic3_case(workdir: str, proof: str) -> Dict:
    ast = parse_theory(open(os.path.join(FIXTURES, "peg4_theory.dsl"),
                            encoding="utf-8").read())
    problem = load_problem(os.path.join(FIXTURES, "peg4_problem.json"))
    cert = load_ic3_certificate(os.path.join(FIXTURES, "ic3_peg4_0111_to_0100.json"))
    source = generate_lean(ast, problem, certificate=cert, proof=proof)
    lean = run_lean(source, workdir, "Ic3_" + proof)
    report = {
        "case": "ic3-" + proof,
        "invariant": cert.clause_text(),
        "initial_state": cert.initial_state,
        "goal_states": cert.goal_states,
        "lean": {"returncode": lean["returncode"], "seconds": lean["seconds"]},
        "axioms_not_empty": axioms_empty(lean["output"], IC3_THEOREMS),
        "sorry_in_output": "sorryAx" in lean["output"],
    }
    # Only `computational` is asked to be axiom-free; `algebraic` costs `propext`
    # by design, and pretending otherwise would be the claim quietly widening.
    if proof == "computational":
        report["ok"] = (lean["returncode"] == 0 and not report["axioms_not_empty"]
                        and not report["sorry_in_output"])
    else:
        report["ok"] = (lean["returncode"] == 0 and not report["sorry_in_output"]
                        and "'inv_closed' depends on axioms: [propext]" in lean["output"])
        report["expected_axioms"] = "propext"
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", help="write EVIDENCE.json and the Lean sources here")
    parser.add_argument("--quick", action="store_true",
                        help="skip the 28672-leaf corner development")
    args = parser.parse_args(argv)

    if lean_binary() is None:
        print("no `lean` on PATH and $LEAN unset -- this script exists to run it",
              file=sys.stderr)
        return 2

    workdir = args.out or os.path.join(ROOT, "runs", "_verify_c4")
    os.makedirs(workdir, exist_ok=True)

    cases = [("pair", "deadlock_open4far_b1c12_b2c13.json")]
    if not args.quick:
        cases.append(("corner", "deadlock_open4far_b1c11.json"))

    reports = []
    for name, certificate in cases:
        reports.append(deadlock_case(name, certificate, workdir))
    for proof in ("computational", "algebraic"):
        reports.append(ic3_case(workdir, proof))

    for report in reports:
        print("%-18s lean=%d %6.1fs  axioms_empty=%s  %s"
              % (report["case"], report["lean"]["returncode"],
                 report["lean"]["seconds"], not report["axioms_not_empty"],
                 "OK" if report["ok"] else "FAILED"))

    evidence = {"cases": reports, "all_ok": all(r["ok"] for r in reports)}
    with open(os.path.join(workdir, "EVIDENCE.json"), "w", encoding="utf-8",
              newline="\n") as handle:
        json.dump(evidence, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("evidence -> %s" % os.path.join(workdir, "EVIDENCE.json"))
    return 0 if evidence["all_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
