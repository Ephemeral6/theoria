"""certify, expensive layer — compile the Lean form and read `#print axioms`.

Two things have to be true and both are checked:

* the file compiles with **no error and no `sorry`** — every declared proof
  obligation is discharged;
* `#print axioms <target>` reports **no axioms** — the proof does not lean on
  `Classical.choice`, `propext`, `Quot.sound`, and in particular not on
  `Lean.ofReduceBool`, which is what `native_decide` would have added.

Toolchain discovery, in order: `$LEAN` → `.toolchain/lean-*/bin/lean` → `PATH`.
If none is found this returns `available: false` and says so. It never downgrades
a missing proof into a passing one.
"""

import glob
import json
import os
import re
import shutil
import subprocess
import sys
from typing import Dict, List, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

AXIOM_FREE = re.compile(r"^'(?P<name>\S+)' does not depend on any axioms\s*$")
AXIOM_DEP = re.compile(r"^'(?P<name>\S+)' depends on axioms: \[(?P<axioms>[^\]]*)\]")


def find_lean() -> Optional[str]:
    explicit = os.environ.get("LEAN")
    if explicit and os.path.exists(explicit):
        return explicit
    for pattern in ("lean-*/bin/lean.exe", "lean-*/bin/lean"):
        matches = sorted(glob.glob(os.path.join(ROOT, ".toolchain", pattern)))
        if matches:
            return matches[0]
    found = shutil.which("lean")
    return found


def _decode(raw) -> str:
    """Toolchain output is UTF-8, whatever this console's codepage claims."""
    if raw is None:
        return ""
    if isinstance(raw, bytes):
        return raw.decode("utf-8", errors="replace")
    return raw


def check(lean_file: str, timeout: int = 1800) -> Dict[str, object]:
    binary = find_lean()
    if binary is None:
        return {
            "file": os.path.relpath(lean_file, ROOT),
            "available": False,
            "green": False,
            "reason": "no Lean toolchain found (tried $LEAN, .toolchain/, PATH); "
                      "see DECISIONS.md D-A0-012",
        }

    # Bytes, then an explicit UTF-8 decode. `text=True` would decode with the
    # process locale — GBK on the machine this was found on — and Lean's *error*
    # prose carries U+2019 and ⟨⟩, so subprocess's reader thread raises
    # `UnicodeDecodeError` and the diagnostic is destroyed precisely when there
    # is a diagnostic. Reported by `cold-start-a2` (D-A2-007); A0 never had a red
    # Lean file, which is why it could not see this from the inside.
    # `errors="replace"` and not `errors="strict"`: one mangled byte is not a
    # reason to lose the whole report.
    proc = subprocess.run(
        [binary, lean_file],
        capture_output=True, timeout=timeout,
        cwd=os.path.dirname(lean_file) or ".",
    )
    out = _decode(proc.stdout) + _decode(proc.stderr)
    lines = [line.rstrip() for line in out.splitlines() if line.strip()]

    axiom_reports: List[Dict[str, object]] = []
    for line in lines:
        m = AXIOM_FREE.match(line)
        if m:
            axiom_reports.append({"name": m.group("name"), "axioms": []})
            continue
        m = AXIOM_DEP.match(line)
        if m:
            axiom_reports.append({
                "name": m.group("name"),
                "axioms": [a.strip() for a in m.group("axioms").split(",") if a.strip()],
            })

    errors = [line for line in lines
              if " error:" in line or line.startswith("error:")]
    sorries = [line for line in lines if "declaration uses 'sorry'" in line]

    green = (
        proc.returncode == 0
        and not errors
        and not sorries
        and bool(axiom_reports)
        and all(not r["axioms"] for r in axiom_reports)
    )
    return {
        "file": os.path.relpath(lean_file, ROOT),
        "available": True,
        "lean": binary,
        "returncode": proc.returncode,
        "errors": errors[:20],
        "sorries": sorries[:20],
        "axiom_reports": axiom_reports,
        "output": lines[:40],
        "green": green,
    }


def main() -> int:
    target = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        ROOT, "theory", "generated", "theory.lean")
    report = check(target)
    print(json.dumps({k: v for k, v in report.items() if k != "output"},
                     indent=2, sort_keys=True))
    name = os.path.basename(os.path.dirname(target)) + "_" + \
        os.path.basename(target).replace(".", "_")
    out = os.path.join(ROOT, "artifacts", "certify_lean_%s.json" % name)
    with open(out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0 if report["green"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
