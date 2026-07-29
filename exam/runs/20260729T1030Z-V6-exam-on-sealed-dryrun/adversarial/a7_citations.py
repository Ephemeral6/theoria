"""Attack 7: every file:line citation in the three modules' docstrings,
SEALED_DRILL.md and PLAN.md -- does the cited line say what is claimed?"""
import os
import re
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

# (citation as written, what it is claimed to say, a regex the cited span must match)
CHECKS = [
    ("proxy/variants.py", 34, 34, r"LEGAL_OPERATORS\s*=", "the wrapper-legal set"),
    ("proxy/variants.py", 68, 73, r"justification.*must say why|len\(justification\) < 40",
     "justification refused under 40 chars"),
    ("proxy/variants.py", 186, 189, r"self\.commands = 0",
     "drill_wrapper: 'RESET zeroes the counters and clears dead'"),
    ("proxy/variants.py", 190, 193, r"self\.commands = 0",
     "  (where that code actually is)"),
    ("proxy/variants.py", 191, 196, r"if self\.dead:\s*$",
     "drill_wrapper: 'once dead the runtime refuses everything'"),
    ("proxy/variants.py", 195, 198, r"if self\.dead:",
     "  (where that code actually is)"),
    ("proxy/variants.py", 143, 149, r"score_at_least",
     "SEALED_DRILL 4: the only win_tighten form"),
    ("proxy/variants.py", 145, 149, r"score_at_least",
     "SEALED_DRILL 4 as written (145-149)"),
    ("proxy/variants.py", 243, 252, r"win_tighten|have is None",
     "SEALED_DRILL 4: the win_tighten block"),
    ("proxy/env_proxy.py", 374, 402, r"decision = runtime\.before",
     "drill_wrapper module docstring: the composition point"),
    ("proxy/env_proxy.py", 380, 402, r"decision = runtime\.before",
     "apply_command: 'Mirrors env_proxy.py:380-402'"),
    ("worldgen/core/types.py", 43, 43, r"AGENT = 6",
     "sealed_drill: \"the agent's colour ... types.py:43\""),
    ("worldgen/core/types.py", 42, 42, r"AGENT = 6", "  (where AGENT actually is)"),
    ("exam/grading/rubrics_verdict.py", 120, 124, r"_CERT_KEYS",
     "drill_certificates: the frozen key sets"),
    ("exam/grading/registry.py", 33, 33, r"RUBRIC_MODULES",
     "sealed_drill: the frozen ordered tuple"),
    ("exam/papers/verdict.py", 80, 80, r'WORLD_ID = "a2"',
     "sealed_drill: every verdict item ships against a2"),
    ("exam/papers/verdict.py", 96, 106, r"points",
     "sealed_drill: points rode on the sheet and leaked"),
    ("exam/papers/verdict.py", 493, 493, r"def _opaque_id",
     "sealed_drill: the opaque id precedent"),
    ("exam/papers/verdict.py", 464, 464, r"def _emit_spec", "PLAN.md: the double hash"),
    ("exam/grading/selftest.py", 453, 453, r"def _fault_blends_the_pair",
     "sealed_drill: the injected blending fault"),
    ("exam/grading/confusion_matrix.py", 55, 55, r"def per_class_confusion",
     "PLAN.md: the per-class table"),
    ("exam/guard.py", 103, 103, r"def assert_synthetic_world", "PLAN.md: the guard"),
    ("exam/model.py", 108, 108, r"def sheet_side", "PLAN.md: truth isolation"),
    ("exam/model.py", 112, 112, r"def key_side", "PLAN.md: truth isolation"),
    ("battery/guard.py", 22, 34, r"short id", "sealed_drill: the short id is a real sieve"),
    ("worldgen/core/solvability.py", 144, 144, r"def report", "PLAN.md: the exhaustive decision"),
    ("worldgen/core/world.py", 27, 33, r"FORBIDDEN_RULE|same semantics",
     "PLAN.md: the deliberate bridge"),
    ("worldgen/core/world.py", 52, 61, r"for_kind|registry\(\)",
     "a3c: where GridWorld binds mechanisms"),
    ("exam/papers/__init__.py", 34, 34, r"BUILDERS",
     "sealed_drill / SEALED_DRILL 5: the builder table"),
    ("Theoria.md", 372, 372, r"死结", "sealed_drill: the Phase 4 deadlock"),
    ("Theoria.md", 259, 259, r"判决题", "SEALED_DRILL 5: the three verdict classes"),
]

print("%-34s %-9s %-8s %s" % ("citation", "span", "verdict", "claimed"))
print("-" * 100)
wrong = 0
for path, lo, hi, pattern, claim in CHECKS:
    full = os.path.join(REPO, path)
    try:
        lines = open(full, encoding="utf-8").read().splitlines()
    except OSError:
        print("%-34s %-9s %-8s %s" % (path, "%d-%d" % (lo, hi), "NO FILE", claim))
        wrong += 1
        continue
    span = "\n".join(lines[lo - 1:hi])
    ok = re.search(pattern, span, re.M) is not None
    if not ok:
        wrong += 1
    print("%-34s %-9s %-8s %s" % (path, "%d-%d" % (lo, hi),
                                  "ok" if ok else "MISS", claim))
print("-" * 100)
print("%d of %d cited spans do not contain what is claimed" % (wrong, len(CHECKS)))

print()
print("files cited by name:")
for f in ("exam/SEALED_DRILL.md", "exam/runs/20260729T1030Z-V6-exam-on-sealed-dryrun/MANIFEST.json",
          "exam/runs/20260729T1030Z-V6-exam-on-sealed-dryrun/RUN_STATE.md",
          "exam/runs/p15-rehearsal-01/MANIFEST.json", "exam/README.md"):
    print("  %-70s exists=%s" % (f, os.path.exists(os.path.join(REPO, f))))

print()
print("tests named in prose -- do they exist?")
tests = open(os.path.join(REPO, "exam", "tests", "test_sealed_drill.py"),
             encoding="utf-8").read()
for name in ("test_no_sealed_id_is_written_into_the_run",
             "test_the_run_is_byte_reproducible",
             "test_the_reason_vocabulary_matches_the_frozen_rubric",
             "test_a_cut_set_is_refused_on_a_cascading_world"):
    print("  %-56s %s" % (name, "present" if ("def %s" % name) in tests else "ABSENT"))
