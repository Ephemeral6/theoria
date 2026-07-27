"""The whole A0 cold start, end to end, from nothing.

```
world      -> raw_trace.jsonl            (M1)
engines    -> candidates.jsonl           (M2)
[theorize] -> theory/theory.dsl          (M3, by hand — see THEORIZE_LOG.md)
compile    -> theory.{py,md,pddl,lean}   (M4)
certify    -> replay ∧ Lean              (M4)
plan       -> SAT, and the world agrees  (M4)
variant    -> UNSAT -> certificate       (M5)
```

Only M3 is missing from this script, and its absence is the point: the theorize
step is the one thing in the loop a script cannot do. `theory.dsl` and
`theory_no_button.dsl` are checked in as hand-written artefacts and this driver
consumes them.

```bash
cd cold-start-a0 && python run_all.py
```
"""

import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))

STEPS = [
    ("M1 world + explorer", [sys.executable, "-m", "world.ground_truth"]),
    ("M2 engines (base)", [sys.executable, "-m", "pipeline.engines_stage"]),
    ("M2 engines (variant)", [sys.executable, "-m", "pipeline.engines_stage",
                              "_no_button"]),
    ("M4 compile", [sys.executable, "-m", "compile.compile_a0"]),
    ("M4 certify cheap", [sys.executable, "-m", "certify.replay"]),
    ("M4 certify lean", [sys.executable, "-m", "certify.lean_check"]),
    ("M4 plan + commit", [sys.executable, "-m", "pipeline.plan_stage"]),
    ("M5 unsolvable variant", [sys.executable, "-m", "pipeline.unsolvable_variant"]),
]


def main() -> int:
    env = dict(os.environ)
    env.setdefault("THEORIA_DETERMINISTIC_IDS", "1")
    env.setdefault("THEORIA_FIXED_TIME", "2026-07-28T00:00:00Z")

    failures = []
    for label, command in STEPS:
        start = time.time()
        proc = subprocess.run(command, cwd=ROOT, env=env,
                              capture_output=True, text=True)
        elapsed = time.time() - start
        status = "ok " if proc.returncode == 0 else "FAIL"
        print("[%s] %-24s %6.1fs" % (status, label, elapsed))
        if proc.returncode != 0:
            failures.append(label)
            tail = (proc.stdout + proc.stderr).strip().splitlines()[-12:]
            for line in tail:
                print("        " + line)

    validate = subprocess.run(
        [sys.executable, "-m", "tools.validate_candidates",
         os.path.join(ROOT, "artifacts", "candidates.jsonl"),
         os.path.join(ROOT, "artifacts", "candidates_no_button.jsonl")],
        cwd=os.path.join(os.path.dirname(ROOT), "engine-rig"),
        capture_output=True, text=True, env=env,
    )
    print("[%s] %-24s %s" % ("ok " if validate.returncode == 0 else "FAIL",
                             "schema validation", validate.stdout.strip()))
    if validate.returncode != 0:
        failures.append("schema validation")

    print()
    print("FAILED: %s" % ", ".join(failures) if failures else "all steps green")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
