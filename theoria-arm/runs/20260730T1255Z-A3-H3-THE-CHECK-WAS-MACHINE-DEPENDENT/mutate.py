"""Do the new check-10 tests bite? Five mutations, run, and the answer on disk.

Written because the triage's L12 is fair: this leg's predecessors described
mutation tables that had no harness and no output file behind them, in a run
record whose own §7 claimed to be upgrading assertions into checkable facts. A
mutation table nobody can re-run is prose.

Each mutation is a literal string swap in a tracked file, applied to a scratch
copy of the arm -- never to the working tree, so an interrupted run cannot leave
a mutated verifier behind. Then the four check-10 tests run against the copy.

    python runs/20260730T1255Z-A3-H3-THE-CHECK-WAS-MACHINE-DEPENDENT/mutate.py

`caught` means the mutation made at least one test fail, which is the property
being measured: a test that passes under a mutation of the code it names is not
testing it. Exit code is non-zero if any mutation survives.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(os.path.dirname(HERE))

#: The tests that are supposed to notice. `-k` rather than the whole file: the
#: rest of the file measures `_files_the_clone_carries`, which these mutations do
#: not touch, and `test_check_ten_is_actually_wired_into_the_run` calls
#: `verify_provenance.run()` over the real archive (136 seconds in
#: `armversion.scan`).
SELECT = ("check_ten_asks_the_index or check_ten_rejects_a_path or "
          "check_ten_has_no_answer or check_ten_catches_a_dangling")

MUTATIONS = [
    {
        "id": "M1-back-to-exists",
        "why": "the defect itself: ask the disk instead of the index",
        "file": "armtools/verify_provenance.py",
        "from": "        absent = [p for p in listed if p not in shipped "
                "and p not in set(stray)]",
        "to":   "        absent = [p for p in listed if not os.path.exists("
                "os.path.join(run_dir, p)) and p not in set(stray)]",
    },
    {
        "id": "M2-shape-gate-open",
        "why": "let absolute paths and `..` escapes back through",
        "file": "armtools/backfill.py",
        "from": "    q = rel_path.replace(\"\\\\\", \"/\")",
        "to":   "    return True\n    q = rel_path.replace(\"\\\\\", \"/\")",
    },
    {
        "id": "M3-third-value-becomes-empty",
        "why": "render `git could not be asked` as `this repository ships "
               "nothing`, the shape that made the reflex layer quiet",
        "file": "armtools/backfill.py",
        "from": "    except OSError:\n        return None\n    if "
                "proc.returncode != 0:\n        return None",
        "to":   "    except OSError:\n        return set()\n    if "
                "proc.returncode != 0:\n        return set()",
    },
    {
        "id": "M4-tracked-and-present",
        "why": "demand presence as well as tracking -- keeps the machine "
               "dependence and merely adds a condition",
        "file": "armtools/verify_provenance.py",
        "from": "        absent = [p for p in listed if p not in shipped "
                "and p not in set(stray)]",
        "to":   "        absent = [p for p in listed if (p not in shipped or "
                "not os.path.exists(os.path.join(run_dir, p))) "
                "and p not in set(stray)]",
    },
    {
        "id": "M5-stray-noted-not-failed",
        "why": "detect the shape fault and decline to fail on it",
        "file": "armtools/verify_provenance.py",
        "from": "        stray = [p for p in listed if not "
                "backfill.path_is_inside_the_run(p)]",
        "to":   "        stray = []",
    },
]


#: The arm imports `proxy.spend_gate` from the repository root, so a copy of the
#: arm alone cannot even be collected. The first version of this harness did
#: exactly that and reported `caught=True` for all five mutations -- five
#: identical `Interrupted: 1 error during collection` lines, which is a harness
#: measuring its own import failure. It is the third time on this leg that a
#: guard passed while asserting nothing, so the control below is not optional
#: politeness: an unmutated copy has to go green before any mutation counts.
REPO_ROOT = os.path.dirname(ARM)


def _run(copy: str):
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [REPO_ROOT] + ([env["PYTHONPATH"]] if env.get("PYTHONPATH") else []))
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:randomly",
         os.path.join("tests", "test_files_in_clone.py"), "-k", SELECT],
        cwd=copy, capture_output=True, text=True, check=False, env=env)
    lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
    return proc.returncode, (lines[-1] if lines else ""), proc.stdout


def _copy_into(tmp: str) -> str:
    copy = os.path.join(tmp, "arm")
    shutil.copytree(ARM, copy, ignore=shutil.ignore_patterns(
        "__pycache__", "runs", ".pytest_cache", "*.pyc"))
    return copy


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        rc, last, _out = _run(_copy_into(tmp))
    control = {"pytest_exit": rc, "pytest_last_line": last, "green": rc == 0}
    if rc != 0:
        with open(os.path.join(HERE, "mutations.json"), "w", encoding="utf-8",
                  newline="\n") as fh:
            json.dump({"control": control, "mutations": [],
                       "note": "the unmutated copy does not pass, so no "
                               "mutation result from this harness means "
                               "anything"}, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        print("CONTROL FAILED: %s" % last)
        return 2

    results = []
    for mut in MUTATIONS:
        with tempfile.TemporaryDirectory() as tmp:
            copy = _copy_into(tmp)
            target = os.path.join(copy, *mut["file"].split("/"))
            src = open(target, encoding="utf-8").read()
            if src.count(mut["from"]) != 1:
                results.append({"id": mut["id"], "caught": None,
                                "error": "anchor found %d times, not 1 -- the "
                                         "mutation was never applied"
                                         % src.count(mut["from"])})
                continue
            open(target, "w", encoding="utf-8").write(
                src.replace(mut["from"], mut["to"]))
            rc, last, out = _run(copy)
            # A collection error is not a caught mutation, it is a broken copy.
            broke_on_import = "error during collection" in out
            results.append({"id": mut["id"], "why": mut["why"],
                            "file": mut["file"],
                            "caught": None if broke_on_import else rc != 0,
                            "pytest_exit": rc,
                            "pytest_last_line": last,
                            **({"error": "the mutated copy could not be "
                                         "imported, so nothing was measured"}
                               if broke_on_import else {})})

    survivors = [r for r in results if r["caught"] is not True]
    out = {"utc_of_write": "2026-07-30T13:05:00Z",
           "selected_tests": SELECT,
           "arm": os.path.basename(ARM),
           "control": control,
           "mutations": results,
           "survivors": [r["id"] for r in survivors],
           "note": "`caught: true` means the mutation broke at least one of the "
                   "selected tests. Survivors are the interesting output: a "
                   "mutation nothing notices names a property nothing pins."}
    with open(os.path.join(HERE, "mutations.json"), "w", encoding="utf-8",
              newline="\n") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    for r in results:
        print("%-32s caught=%s  %s" % (r["id"], r["caught"],
                                       r.get("pytest_last_line", r.get("error"))))
    return 1 if survivors else 0


if __name__ == "__main__":
    raise SystemExit(main())
