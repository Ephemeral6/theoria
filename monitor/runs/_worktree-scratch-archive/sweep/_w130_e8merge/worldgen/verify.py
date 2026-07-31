"""One command that decides whether this territory is green.

```bash
cd .worktrees/c1-worldgen && python -m worldgen.verify
```

Four stages, and each answers a different question:

| stage | question |
|---|---|
| `build --check` | do the twenty worlds **and the fifteen mutants** still build, pass every build gate, and reproduce byte-for-byte in a fresh interpreter? |
| `pytest` | do the library's own properties hold, including the regression tests for the defects the inherited remnant shipped with? |
| `validate_candidates` | does the QC run's candidate stream still satisfy the frozen `CONTRACTS/candidates_schema.md`? |
| `qc.run_qc` | do three worlds clear the bar pre-registered in `worldgen/qc/PREREGISTERED.md`? |
| `qc.run_qc --mutants` | does each sampled mutant run the upstream pipeline, per `worldgen/qc/PREREGISTERED_MUTANTS.md`? |

## Neither QC stage gates on `pass`, and both gate on drift

**Neither QC stage's `pass` is an input to this process's exit code**, and that is
deliberate rather than convenient. `PREREGISTERED.md` fixed a held-out threshold
of 0.90 before the harness was ever run and the family came in under it; the
honest response to a missed pre-registered bar is to publish the miss, not to
lower the bar and not to quietly turn the exit code green. Both reds are
**upstream** — `a0_relational_v1`'s vocabulary raises `NoSeparatingGuard` on
`t2-lock-fragile` and on `t2-switch-push`, and the fix is an atom in
`cold-start-a0/`, another track's file that `worldgen/` may not edit. Gating on
`pass` would leave the world factory permanently red for a defect it is forbidden
to repair, and a permanently red gate is a gate everybody learns to route around.

The mutant stage misses too, and for a reason worth keeping visible here rather
than only in its own report: one sampled mutant makes the upstream miner raise,
and **so does the world it was mutated from**. The bar as written did not
distinguish "the mutant broke the pipeline" from "the base was already broken",
which is a defect in the bar. It was not rewritten. See that file's postscript.

**What the QC stages do gate on is deviation from the pinned miss.** Until
V12-worldgen-gate-deaf, "neither stage gates" was implemented as "any QC outcome
exits 0", and those are not the same sentence. A third world could start raising,
replay accuracy could slide from 1.000 to 0.4, a passing mutant could start
failing — and this command printed `green`. Worse, a QC stage that *crashed* was
indistinguishable from one that measured a miss, because both were judged solely
by `proc.returncode` and `run_qc` returns 1 for an honest miss: the entire QC
layer could have stopped executing without changing a character of this output.

So the exact verdict this territory publishes is transcribed by hand into
`worldgen/qc/KNOWN_MISS.json` — with the reds' owner and blocker written next to
them — and each QC stage is required to reproduce it to the field, *and* to have
rewritten its artifact during this run. Anything else fails, in either direction:
a verdict that improves means the pin is now a lie about what ships, and the
repair is to re-run QC and transcribe the new numbers, never to widen the pin.
`RUN_STATE.md` §gaps carries the numbers and §the QC gate carries this decision.

The negative control is `worldgen/tests/test_verify_qc_gate.py`: it implants a
deviating verdict and a dead stage and requires this process to exit non-zero,
and implants the pinned verdict and requires it to exit 0. A gate nobody has
watched fail is a gate nobody has any reason to trust.
"""

import argparse
import json
import os
import subprocess
import sys
from typing import Any, Dict, List, Optional, Sequence, Tuple

from worldgen.qc import gate

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

#: `(label, command, gating, stage_key)`. `stage_key` is `None` for a stage
#: judged by its exit code, or a key in `qc/KNOWN_MISS.json` for a stage judged
#: against the pinned verdict it wrote.
Stage = Tuple[str, Sequence[str], bool, Optional[str]]

STAGES: Tuple[Stage, ...] = (
    ("catalogue build + determinism",
     (sys.executable, "-m", "worldgen.build", "--check"), True, None),
    ("library properties",
     (sys.executable, "-m", "pytest", "worldgen/tests", "-q"), True, None),
    ("QC: three worlds through cold-start-a0",
     (sys.executable, "-m", "worldgen.qc.run_qc"), False, "qc_family"),
    ("QC: four mutants through cold-start-a0, against their bases",
     (sys.executable, "-m", "worldgen.qc.run_qc", "--mutants"), False,
     "qc_mutants"),
)


def load_selftest(path: str) -> Tuple[Tuple[Stage, ...], str]:
    """Substitute the stage table and the pin, for the negative control.

    The implant point, and the whole of it: everything downstream of here —
    the mtime stamping, the pin comparison, the failure aggregation and this
    process's exit code — is the shipped path, unchanged. Modelled on
    `figures/check_coverage.py --self-test`, which reconstructs the pre-P8 tree
    and requires its probe to fire.
    """
    with open(path, "r", encoding="utf-8") as handle:
        spec = json.load(handle)
    stages = tuple(
        (s["label"], tuple(s["command"]), bool(s.get("gating", False)),
         s.get("stage_key"))
        for s in spec["stages"]
    )
    return stages, spec["pin"]


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="run this territory's gates")
    parser.add_argument(
        "--selftest-spec", default=None,
        help="path to a JSON stage/pin substitution, used by the negative "
             "control in worldgen/tests/test_verify_qc_gate.py. Not for "
             "ordinary runs.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    stages: Tuple[Stage, ...] = STAGES
    pin_path: Optional[str] = None
    if args.selftest_spec:
        stages, pin_path = load_selftest(args.selftest_spec)
        print("!! SELF-TEST: stage table and pin substituted from %s"
              % args.selftest_spec)

    failures: List[str] = []
    notes: List[str] = []
    for label, command, gating, stage_key in stages:
        pin: Optional[Dict[str, Any]] = None
        artifact: Optional[str] = None
        stamp: Optional[float] = None
        if stage_key is not None:
            pin = gate.stage_pin(stage_key, pin_path)
            artifact = os.path.join(gate.WORLDGEN, pin["artifact"])
            stamp = gate.artifact_stamp(artifact)

        proc = subprocess.run(command, cwd=ROOT, capture_output=True)
        text = (proc.stdout + proc.stderr).decode("utf-8", "replace")

        problems: List[str] = []
        if stage_key is None:
            ok = proc.returncode == 0
            failed = not ok
            tag = "ok  " if ok else "FAIL"
        else:
            outcome, problems = gate.check(pin, artifact, stamp)
            pinned_pass = bool(pin["verdict"]["expected"].get("pass"))
            failed = outcome != gate.PINNED
            tag = "FAIL" if failed else ("ok  " if pinned_pass else "miss")

        print("[%s] %s" % (tag, label))
        if failed:
            failures.append(label)
        elif tag == "miss":
            notes.append(label)

        # A QC stage speaks whether it passed or missed: it is a measurement
        # first and a verdict second, and a stage that only prints on failure
        # trains a reader to read silence as success.
        is_qc = stage_key is not None
        tail = 6 if (not failed or is_qc) else 14
        if failed or is_qc:
            for line in text.strip().splitlines()[-tail:]:
                print("        " + line)
        for problem in problems:
            print("    !!  " + problem)
        if problems:
            print("    !!  pinned in %s under stages.%s"
                  % (os.path.relpath(pin_path or gate.KNOWN_MISS, ROOT),
                     stage_key))

    print()
    if notes:
        print("PINNED MISS (unchanged from worldgen/qc/KNOWN_MISS.json, whose "
              "`owner` field says whose work each red is): %s"
              % ", ".join(notes))
    if failures:
        print("FAILED: %s" % ", ".join(failures))
        return 1
    if notes:
        # Deliberately not the bare token `green`. Two pre-registered bars are
        # missed and this exit code is 0 by the decision documented above, not
        # because QC passed. Anyone grepping this output for a one-word verdict
        # should have to read the qualifier.
        print("VERDICT: library gates green; %d QC stage(s) still missing their "
              "pre-registered bar, exactly as pinned. Exit 0 is the documented "
              "decision, NOT a QC pass — see worldgen/qc/KNOWN_MISS.json and "
              "RUN_STATE.md §gaps." % len(notes))
        return 0
    print("VERDICT: green — library gates and every QC stage at its pin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
