"""certify, both layers — thin wrappers so A3 writes only into A3's artifacts.

The checks themselves are `cold-start-a0`'s, imported unmodified:

* `certify.replay.certify` — the cheap layer.  Full-history replay against the
  trace, plus rendering consistency, plus full-frame responsibility, plus one
  successor per action.  Five anomaly kinds, any one of which is red:
  `render_mismatch`, `contested_pixel`, `unowned_pixel`, `goal_mismatch`,
  `ambiguous_transition`.
* the Lean layer's *rules* — `lean_check.AXIOM_FREE`, `lean_check.AXIOM_DEP`
  and `lean_check.find_lean` — imported rather than restated, because those two
  regexes are the acceptance criterion and a second copy is how two copies
  drift.

**What is A3's own, and why.**

*The subprocess call and its decoding.*  A0's `lean_check.check` runs the
toolchain with `subprocess.run(text=True)`, which decodes with the process
locale — GBK on this machine.  Lean's *error* messages carry U+2019 and ⟨⟩, so
the reader raises `UnicodeDecodeError` exactly when there is a diagnostic worth
reading.  A2 hit this and wrote the fix (its D-A2-007); the fix is re-derived
here rather than imported, because `cold-start-a2` is a sibling experiment and
is deliberately off A3's `sys.path` (`_bootstrap.py`).  Credit is A2's.  The
shape of the fix: capture bytes, decode UTF-8 with `errors="replace"`, never
let the reader decide.

*Toolchain discovery is made explicit.*  `lean_check.find_lean` falls back to
`cold-start-a0/.toolchain/`, which would make A3's headline result depend on a
directory belonging to another track.  `ensure_lean()` prefers an explicit
`$LEAN`, then elan's own toolchain store, and only then falls back — and the
binary it settled on is named in every report, so "which Lean" is never a
question the reader has to reconstruct.

**No toolchain is red.**  Not skipped, not "n/a", not a pass with a caveat:
`{"available": False, "green": False}`.  The expensive layer's whole value is
that it cannot be satisfied by its own absence.
"""

import glob
import json
import os
import subprocess
import sys
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap  # noqa: F401,E402

from certify import lean_check, replay  # noqa: E402  (cold-start-a0, read-only)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTIFACTS = os.path.join(ROOT, "artifacts")


def ensure_lean() -> Optional[str]:
    """Pin `$LEAN` to a binary A3 names, if the caller has not already.

    Mutates `os.environ["LEAN"]` when it resolves one out of elan's store —
    a side effect, documented because a reader of a report should be able to
    tell whether the environment they are looking at is the one they set.
    """
    explicit = os.environ.get("LEAN")
    if explicit and os.path.exists(explicit):
        return explicit
    home = os.path.expanduser("~")
    for pattern in (
        os.path.join(home, ".elan", "toolchains", "*", "bin", "lean.exe"),
        os.path.join(home, ".elan", "toolchains", "*", "bin", "lean"),
    ):
        matches = sorted(glob.glob(pattern))
        if matches:
            os.environ["LEAN"] = matches[0]
            return matches[0]
    return lean_check.find_lean()          # PATH, or A0's .toolchain, or None


# ------------------------------------------------------------- the cheap layer

def cheap(theory_py: str, trace_path: str) -> Dict[str, object]:
    """Replay the generated manual against a trace.  A0's check, unmodified.

    `theory_py` must be the *generated* module — `<out_dir>/theory.py` — because
    that module is the system's only predictor (Theoria 1.10a, 预测无侧门) and
    replaying anything else would be certifying a second implementation.
    """
    return replay.certify(theory_py, trace_path)


def summary(report) -> str:
    return replay.contested_summary(report)


def cheap_brief(report: Dict[str, object]) -> Dict[str, object]:
    """The cheap report without its anomaly bodies.

    `anomalies` is capped at 40 entries for two of the five kinds but
    `pixels_unexplained` is not capped, so the brief keeps the count and drops
    the payload rather than the other way round.
    """
    return {
        "trace": report.get("trace"),
        "frames": report.get("frames"),
        "transitions": report.get("transitions"),
        "pixels_checked": report.get("pixels_checked"),
        "pixels_unexplained": report.get("pixels_unexplained"),
        "anomaly_count": len(report.get("anomalies") or []),
        "anomaly_kinds": report.get("anomaly_kinds"),
        "green": report.get("green"),
    }


# --------------------------------------------------------- the expensive layer

def lean(lean_file: str, timeout: int = 1800) -> Dict[str, object]:
    """Compile the Lean form; require no error, no `sorry`, and no axioms.

    Green needs all five of: `returncode == 0`, no error line, no `sorry`, **at
    least one** `#print axioms` report, and every axiom list empty.  The
    fourth is the one that looks like pedantry and is not: a Lean file that
    compiles cleanly but never asks about its axioms is a file that proved
    nothing, and it would otherwise pass on the strength of the other four.
    """
    binary = ensure_lean()
    if binary is None:
        return {
            "file": os.path.relpath(lean_file, ROOT).replace(os.sep, "/"),
            "available": False,
            "green": False,
            "reason": "no Lean toolchain found (tried $LEAN, elan's toolchain "
                      "store, PATH, and A0's .toolchain); the expensive certify "
                      "layer cannot run and this is reported as red, never "
                      "downgraded to a pass",
        }

    proc = subprocess.run([binary, lean_file], capture_output=True,
                          timeout=timeout,
                          cwd=os.path.dirname(lean_file) or ".")
    # A2's D-A2-007: decode explicitly, never via `text=True`.  See the module
    # docstring.
    out = (proc.stdout or b"").decode("utf-8", "replace") + \
          (proc.stderr or b"").decode("utf-8", "replace")
    lines = [line.rstrip() for line in out.splitlines() if line.strip()]

    axiom_reports: List[Dict[str, object]] = []
    for line in lines:
        m = lean_check.AXIOM_FREE.match(line)
        if m:
            axiom_reports.append({"name": m.group("name"), "axioms": []})
            continue
        m = lean_check.AXIOM_DEP.match(line)
        if m:
            axiom_reports.append({
                "name": m.group("name"),
                "axioms": [a.strip() for a in m.group("axioms").split(",")
                           if a.strip()],
            })

    errors = [line for line in lines
              if " error:" in line or line.startswith("error:")]
    sorries = [line for line in lines if "declaration uses 'sorry'" in line]

    return {
        "file": os.path.relpath(lean_file, ROOT).replace(os.sep, "/"),
        "available": True,
        "lean": binary,
        "returncode": proc.returncode,
        "errors": errors[:20],
        "sorries": sorries[:20],
        "axiom_reports": axiom_reports,
        "output": lines[:40],
        "green": (proc.returncode == 0 and not errors and not sorries
                  and bool(axiom_reports)
                  and all(not r["axioms"] for r in axiom_reports)),
    }


def lean_brief(report: Dict[str, object]) -> Dict[str, object]:
    return {k: report.get(k) for k in
            ("file", "available", "lean", "returncode", "errors", "sorries",
             "axiom_reports", "reason", "green")}


def write_report(path: str, payload: Dict[str, object]) -> str:
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return path


def main() -> int:
    """`certify_a3.py [target=generated_l1] [trace=artifacts/l1_sweep.jsonl]`."""
    target = sys.argv[1] if len(sys.argv) > 1 else "generated_l1"
    out_dir = os.path.join(ROOT, "theory", target)
    trace = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
        ARTIFACTS, "l1_sweep.jsonl")

    cheap_report = cheap(os.path.join(out_dir, "theory.py"), trace)
    print("cheap :", summary(cheap_report))
    for anomaly in cheap_report["anomalies"][:8]:
        print("   ", json.dumps(anomaly, sort_keys=True))

    lean_report = lean(os.path.join(out_dir, "theory.lean"))
    print("lean  :", "GREEN" if lean_report.get("green") else "RED",
          json.dumps(lean_report.get("axiom_reports")))
    for line in (lean_report.get("errors") or [])[:8]:
        print("   ", line)

    write_report(os.path.join(ARTIFACTS, "certify_%s.json" % target),
                 {"cheap": cheap_report, "lean": lean_brief(lean_report)})
    return 0 if cheap_report["green"] and lean_report.get("green") else 1


if __name__ == "__main__":
    raise SystemExit(main())
