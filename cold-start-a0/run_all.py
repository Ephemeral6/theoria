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

Two steps are missing from this script, for different reasons.

**M3 is missing because a script cannot do it.** The theorize step is the one
place a semantic decision is made; `theory.dsl` and `theory_no_button.dsl` are
checked in as hand-written artefacts and this driver consumes them.

**M6 scoring is missing because it reads the referee's copy of the truth.**
`python -m certify.score_vs_truth` is a separate command on purpose, so that
nothing in the default loop can see the answers.

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
    ("M4 problem instances", [sys.executable, "-m", "compile.problem"]),
    ("M4 compile", [sys.executable, "-m", "compile.compile_a0"]),
    ("M4 certify cheap", [sys.executable, "-m", "certify.replay"]),
    ("M4 certify lean", [sys.executable, "-m", "certify.lean_check"]),
    ("M4 plan + commit", [sys.executable, "-m", "pipeline.plan_stage"]),
    ("M5 unsolvable variant", [sys.executable, "-m", "pipeline.unsolvable_variant"]),
]


def _text(raw) -> str:
    """Child output is UTF-8 by construction — see `PYTHONIOENCODING` below.

    The same hazard `cold-start-a2` reported against `certify/lean_check.py`
    (D-A2-007) lives here in a quieter form: `text=True` decodes with the
    process locale, so on a GBK console a step whose failure message is not
    GBK-decodable takes down the runner instead of printing its tail — the
    diagnostic is lost exactly when there is one. Pinning the children's output
    encoding and decoding it explicitly makes the answer the same on every
    machine, which is also what determinism asks for.
    """
    return raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else (raw or "")


def main() -> int:
    env = dict(os.environ)
    env.setdefault("THEORIA_DETERMINISTIC_IDS", "1")
    env.setdefault("THEORIA_FIXED_TIME", "2026-07-28T00:00:00Z")
    env.setdefault("PYTHONIOENCODING", "utf-8")

    failures = []
    for label, command in STEPS:
        start = time.time()
        proc = subprocess.run(command, cwd=ROOT, env=env, capture_output=True)
        elapsed = time.time() - start
        status = "ok " if proc.returncode == 0 else "FAIL"
        print("[%s] %-24s %6.1fs" % (status, label, elapsed))
        if proc.returncode != 0:
            failures.append(label)
            tail = (_text(proc.stdout) + _text(proc.stderr)).strip().splitlines()[-12:]
            for line in tail:
                print("        " + line)

    validate = subprocess.run(
        [sys.executable, "-m", "tools.validate_candidates",
         os.path.join(ROOT, "artifacts", "candidates.jsonl"),
         os.path.join(ROOT, "artifacts", "candidates_no_button.jsonl")],
        cwd=os.path.join(os.path.dirname(ROOT), "engine-rig"),
        capture_output=True, env=env,
    )
    print("[%s] %-24s %s" % ("ok " if validate.returncode == 0 else "FAIL",
                             "schema validation", _text(validate.stdout).strip()))
    if validate.returncode != 0:
        failures.append("schema validation")

    print()
    print("FAILED: %s" % ", ".join(failures) if failures else "all steps green")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
