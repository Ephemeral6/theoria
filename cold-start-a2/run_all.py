"""The whole A2 spike, end to end, from nothing.

```
world      -> raw_trace.jsonl + history_trace.jsonl   (M1)
engines    -> candidates.jsonl x2, engines_diff       (M2)
[theorize] -> theory/theory.dsl                       (M3, by hand)
compile    -> theory.{py,md,pddl,lean}                (M4)
certify    -> replay ∧ Lean                           (M4)
plan       -> SAT, and the world agrees               (M4)
---------------------------------------------------------------- the exhibit
[theorize] -> theory/theory_holed.dsl                 (M5, by hand)
exhibit    -> replay GREEN, plan UNSAT, Lean GREEN, and FALSE of the world
---------------------------------------------------------------- the loop
refute     -> 打脸   a solved episode                  (M6)
locate     -> 定位   §1.4's three-way                  (M7)
probe      -> 戳探   probes.jsonl, trace grows         (M8)
engines    -> the grown evidence re-proposes the rule
[theorize] -> theory/theory_repaired.dsl              (M9, by hand)
repair     -> 修订 · 重证 · 解出                        (M9–M11)
ledger     -> loop_ledger.json
```

Three steps are missing from this script, all for the same reason: **a script
cannot do the theorize step.**  The three `.dsl` files are hand-written
artefacts and this driver consumes them.  Which clause was accepted, which was
rejected and which was carried as pending is in `THEORIZE_LOG.md`.

Scoring against the referee's copy is deliberately *inside* the run here rather
than held back as a separate command, because unlike A0 the whole point of A2 is
the comparison between what the manual proves and what is true — the honest
discipline is instead that no theorizing step ever reads `ground_truth.json`,
and the loop's own evidence (`solved_episode.jsonl`, `probes.jsonl`) reaches the
manual only as frames.

```bash
cd cold-start-a2 && python run_all.py
```
"""

import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))

STEPS = [
    ("M1 world + traces", [sys.executable, "-m", "a2world.ground_truth"]),
    ("M2 engines", [sys.executable, "-m", "a2pipeline.engines"]),
    ("M4 compile control", [sys.executable, "-m", "a2pipeline.compile_a2"]),
    ("M4 certify control", [sys.executable, "-m", "a2pipeline.certify_a2",
                            "generated", "artifacts/raw_trace.jsonl"]),
    ("M4 plan control", [sys.executable, "-m", "a2pipeline.plan", "generated"]),
    ("M5 EXHIBIT", [sys.executable, "-m", "a2pipeline.exhibit"]),
    ("M6 打脸 refute", [sys.executable, "-m", "a2pipeline.refute"]),
    ("M7 定位 locate", [sys.executable, "-m", "a2pipeline.locate"]),
    ("M8 戳探 probe", [sys.executable, "-m", "a2pipeline.probe"]),
    ("M8 engines re-run", [sys.executable, "-m", "a2pipeline.engines", "--probed"]),
    ("M9 修订/重证/解出", [sys.executable, "-m", "a2pipeline.repair"]),
    ("-- concepts + pin", [sys.executable, "-m", "a2pipeline.concepts"]),
    ("-- loop ledger", [sys.executable, "-m", "a2pipeline.ledger"]),
]


def main() -> int:
    env = dict(os.environ)
    env.setdefault("THEORIA_DETERMINISTIC_IDS", "1")
    env.setdefault("THEORIA_FIXED_TIME", "2026-07-28T00:00:00Z")
    # The Lean toolchain speaks UTF-8 and this box's locale does not; without
    # this the subprocess reader dies on Lean's own punctuation exactly when a
    # proof fails.  See a2pipeline/certify_a2.py.
    env.setdefault("PYTHONUTF8", "1")

    failures = []
    for label, command in STEPS:
        start = time.time()
        proc = subprocess.run(command, cwd=ROOT, env=env, capture_output=True)
        elapsed = time.time() - start
        status = "ok " if proc.returncode == 0 else "FAIL"
        print("[%s] %-22s %6.1fs" % (status, label, elapsed))
        if proc.returncode != 0:
            failures.append(label)
            text = (proc.stdout + proc.stderr).decode("utf-8", "replace")
            for line in text.strip().splitlines()[-14:]:
                print("        " + line)

    validate = subprocess.run(
        [sys.executable, "-m", "tools.validate_candidates"]
        + [os.path.join(ROOT, "artifacts", name) for name in
           ("candidates.jsonl", "candidates_history.jsonl",
            "candidates_probed.jsonl", "candidates_holed.jsonl",
            "candidates_repaired.jsonl", "candidates_probe.jsonl")
           if os.path.exists(os.path.join(ROOT, "artifacts", name))],
        cwd=os.path.join(os.path.dirname(ROOT), "engine-rig"),
        capture_output=True, env=env,
    )
    ok = validate.returncode == 0
    print("[%s] %-22s %s" % ("ok " if ok else "FAIL", "schema validation",
                             validate.stdout.decode("utf-8", "replace").strip()))
    if not ok:
        failures.append("schema validation")

    print()
    print("FAILED: %s" % ", ".join(failures) if failures else "all steps green")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
