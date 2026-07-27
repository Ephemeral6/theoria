"""certify, both layers — thin wrappers so A2 writes only into A2's artifacts.

The checks themselves are A0's and are imported unmodified:

* `certify.replay.certify` — full-history replay ∧ rendering consistency ∧
  full-frame responsibility ∧ single successor.  The cheap layer.
* `certify.lean_check.check` — compile the Lean form, require no error, no
  `sorry`, and an **empty** `#print axioms`.  The expensive layer.

Two things are A2's own.

**Toolchain discovery is made explicit.** `lean_check.find_lean` falls back to
`cold-start-a0/.toolchain/`, which would make A2's headline result depend on a
directory belonging to another track.  `ensure_lean()` sets `$LEAN` from elan's
own toolchain store first, so the binary A2 used is named in every report.

**The toolchain's output is decoded as UTF-8, explicitly.** A0's `check()` runs
Lean with `subprocess.run(text=True)`, which decodes with the process locale —
GBK on this machine.  Lean's *error* messages contain U+2019 and ⟨⟩, so the
reader thread raises `UnicodeDecodeError` and the diagnostic is lost precisely
when there is a diagnostic to lose.  A0 never saw it because A0 never had a red
Lean file; A2 has one on purpose (`generated_repaired_stale/`).  So the run and
the decode are A2's, and the parsing rules — the two axiom-report regexes and
the green criteria — are imported from A0 rather than restated, because those
are the contract and duplicating them is how the two drift.

**Reports land in `cold-start-a2/artifacts/`.** A0's `main()` entry points write
into A0's tree; A2 calls the library functions and does its own writing.
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
    """Pin `$LEAN` to a binary A2 names, if the caller has not already."""
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


def cheap(theory_py: str, trace_path: str) -> Dict[str, object]:
    return replay.certify(theory_py, trace_path)


def summary(report) -> str:
    return replay.contested_summary(report)


def lean(lean_file: str, timeout: int = 1800) -> Dict[str, object]:
    """Compile the Lean form; require no error, no `sorry`, and no axioms."""
    binary = ensure_lean()
    if binary is None:
        return {
            "file": os.path.relpath(lean_file, ROOT),
            "available": False,
            "green": False,
            "reason": "no Lean toolchain found (tried $LEAN, elan's toolchain "
                      "store, PATH); the expensive certify layer cannot run and "
                      "this is reported as red, never downgraded to a pass",
        }

    proc = subprocess.run([binary, lean_file], capture_output=True,
                          timeout=timeout,
                          cwd=os.path.dirname(lean_file) or ".")
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
                "axioms": [a.strip() for a in m.group("axioms").split(",") if a.strip()],
            })

    errors = [line for line in lines
              if " error:" in line or line.startswith("error:")]
    sorries = [line for line in lines if "declaration uses 'sorry'" in line]

    return {
        "file": os.path.relpath(lean_file, ROOT),
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
            ("available", "lean", "returncode", "errors", "sorries",
             "axiom_reports", "green")}


def main() -> int:
    target = sys.argv[1] if len(sys.argv) > 1 else "generated"
    out_dir = os.path.join(ROOT, "theory", target)
    trace = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
        ARTIFACTS, "raw_trace.jsonl")

    cheap_report = cheap(os.path.join(out_dir, "theory.py"), trace)
    print("cheap :", summary(cheap_report))
    for anomaly in cheap_report["anomalies"][:8]:
        print("   ", json.dumps(anomaly, sort_keys=True))

    lean_report = lean(os.path.join(out_dir, "theory.lean"))
    print("lean  :", "GREEN" if lean_report.get("green") else "RED",
          json.dumps(lean_report.get("axiom_reports")))
    for line in (lean_report.get("errors") or [])[:8]:
        print("   ", line)

    out = os.path.join(ARTIFACTS, "certify_%s.json" % target)
    with open(out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(
            {"cheap": cheap_report, "lean": lean_brief(lean_report)},
            indent=2, sort_keys=True) + "\n")
    return 0 if cheap_report["green"] and lean_report.get("green") else 1


if __name__ == "__main__":
    raise SystemExit(main())
