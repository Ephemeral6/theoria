"""Certificate JSON + PDDL -> a Lean development, end to end.

    python -m tools.build_deadlock_lean <certificate.json> [-o out.lean]

The whole chain in one place, in the order the obligations have to happen in:
ground the task ourselves, check the encoding is faithful to it, cross-check the
producer's bookkeeping, re-derive the two obligations, and only then emit.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from theory_compiler import deadlock_certificate as dc          # noqa: E402
from theory_compiler import strips, strips_encoding             # noqa: E402
from theory_compiler.generators import gen_lean_deadlock        # noqa: E402

FIXTURES = os.path.join(os.path.dirname(HERE), "tests", "fixtures")
DOMAIN = os.path.join(FIXTURES, "strips", "sokoban_domain.pddl")
PROBLEM = os.path.join(FIXTURES, "strips", "sokoban_open4far.pddl")


def build(certificate_path: str, domain_path: str = DOMAIN, problem_path: str = PROBLEM,
          exhibits: bool = True):
    task = strips.load_task(domain_path, problem_path)
    encoding = strips_encoding.PositionalEncoding(task)
    stats = strips_encoding.verify(encoding)
    cert = dc.load_deadlock_certificate(certificate_path, task, encoding)

    plan = witness = None
    if exhibits:
        plan = strips_encoding.shortest_plan(encoding)
        holding = [s for s in encoding.states() if encoding.holds(s, list(cert.pattern))]
        witness = min(holding)

    source = gen_lean_deadlock.generate_deadlock_lean(
        task, encoding, cert, proof="computational", plan=plan, witness=witness)
    return task, encoding, cert, source, stats


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("certificate")
    parser.add_argument("-o", "--out")
    parser.add_argument("--no-exhibits", action="store_true")
    parser.add_argument("--stats", action="store_true")
    args = parser.parse_args(argv)

    task, encoding, cert, source, stats = build(
        args.certificate, exhibits=not args.no_exhibits)

    if args.stats:
        reachable = [encoding.decode(a) for a in strips.reachable(task)]
        report = dict(stats)
        report.update(dc.bite(cert, encoding, reachable))
        report["ground_actions"] = len(task.actions)
        report["deleting_actions"] = len(cert.deleting_actions(task))
        print(json.dumps(report, indent=2, sort_keys=True))

    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(source)
        print("wrote %s (%d lines)" % (args.out, source.count("\n") + 1))
    else:
        sys.stdout.write(source)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
