"""Run the whole bench and write the run directory.

    cd engine-rig && python -m bench --out runs/<UTC>-E2-fd-ladder-bench

Writes, in the order it produces them, so a run that dies half way leaves the
half it finished on disk rather than nothing:

    instances/      the generated PDDL, next to the numbers it produced
    logs/           Fast Downward's raw output, one file per (instance, rung)
    guarded/        the theorem-compiled tasks
    ladder.json     / LADDER.md
    dividend.json   / DIVIDEND.md
    MANIFEST.json   provenance, including the toolchain gap

Exit code is non-zero on a **soundness** failure -- a rung answering something it
was not entitled to answer, or a theorem changing a plan.  A dividend of zero
exits 0: the run was measuring whether the dividend exists, and "it does not"
is a result.
"""

import argparse
import datetime
import hashlib
import json
import os
import platform
import subprocess
import sys

from bench import dividend, ladder, report, toolchain
from engines.fd_adapter import backends

PROMPT_ID = "E2-fd-ladder-bench"


def _git(repo_root: str, *args: str) -> str:
    try:
        out = subprocess.run(
            ["git", "-C", repo_root, *args],
            capture_output=True, text=True, timeout=60,
        )
        return (out.stdout or "").strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def _write_json(path: str, payload) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=2, sort_keys=False)
        fh.write("\n")


def _write_text(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text if text.endswith("\n") else text + "\n")


def _sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="bench")
    parser.add_argument("--out", required=True, help="run directory to write")
    parser.add_argument("--repeats", type=int, default=3,
                        help="timed runs per cell; the fastest is kept")
    parser.add_argument("--skip-dividend", action="store_true")
    parser.add_argument("--skip-ladder", action="store_true")
    args = parser.parse_args(argv)

    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # engine-rig/
    repo_root = os.path.dirname(here)
    out_dir = os.path.abspath(args.out)
    os.makedirs(out_dir, exist_ok=True)

    executable = backends.find_fast_downward()
    utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Provenance first.  If the run dies later, the half-finished directory still
    # says which planner it was talking to -- which is the fact that stops being
    # recoverable the moment the shell that had FAST_DOWNWARD exported goes away.
    tool = toolchain.probe(executable, repo_root)
    _write_json(os.path.join(out_dir, "toolchain.json"), tool)
    print("fast downward: %s" % (executable or "NOT REACHABLE -- FD rungs absent"))
    if executable and not tool["matches_p13_manifest"]:
        print("WARNING: binary does not match the P-13 manifest: %s"
              % tool.get("checks_against_p13"))

    problems = []
    written = ["toolchain.json"]

    if not args.skip_ladder:
        print("ladder: measuring %d configurations ..." % len(ladder.CONFIGS))
        ladder_report = ladder.run(out_dir, executable=executable, repeats=args.repeats)
        _write_json(os.path.join(out_dir, "ladder.json"), ladder_report)
        _write_text(os.path.join(out_dir, "LADDER.md"),
                    report.ladder_markdown(ladder_report))
        written += ["ladder.json", "LADDER.md"]
        problems += ladder.failures(ladder_report)
        print("ladder: %d instances, %d problem(s)"
              % (len(ladder_report["results"]), len(problems)))

    if not args.skip_dividend:
        print("dividend: carving theorems and solving twice ...")
        dividend_report = dividend.run(out_dir, executable=executable, repeats=args.repeats)
        _write_json(os.path.join(out_dir, "dividend.json"), dividend_report)
        _write_text(os.path.join(out_dir, "DIVIDEND.md"),
                    report.dividend_markdown(dividend_report))
        written += ["dividend.json", "DIVIDEND.md"]
        found = dividend.failures(dividend_report)
        problems += found
        print("dividend: %d instances, %d problem(s)"
              % (len(dividend_report["results"]), len(found)))

    manifest = {
        # The four the repo requires, first and unabbreviated.
        "prompt_id": PROMPT_ID,
        "branch": _git(repo_root, "rev-parse", "--abbrev-ref", "HEAD"),
        "base_commit": _git(repo_root, "rev-parse", "HEAD"),
        "utc": utc,

        "host": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "machine": platform.machine(),
        },
        "command": "python -m bench --out %s --repeats %d" % (args.out, args.repeats),
        "repeats": args.repeats,

        # The item's third deliverable: the gap `.toolchain/` leaves, stated in
        # the manifest rather than in prose somebody has to go looking for.
        "toolchain": tool,

        "determinism": {
            "structural_results_are_reproducible": (
                "Node counts, plan lengths, task sizes and exit codes are a "
                "function of the instance and the configuration. verify.py "
                "re-derives them and compares exactly."
            ),
            "timings_are_not": (
                "Every wall-clock figure is a property of this machine at this "
                "moment. verify.py checks that timings are present and ordered "
                "sanely; it never compares them for equality, and neither should "
                "a reader."
            ),
            "fd_numbers_are_not_reconstructible_from_git": tool["reproducibility_gap"],
        },

        "soundness_problems": problems,
        "files": [],
    }
    for name in written:
        path = os.path.join(out_dir, name)
        if os.path.isfile(path):
            manifest["files"].append({"path": name, "sha256": _sha256(path)})
    _write_json(os.path.join(out_dir, "MANIFEST.json"), manifest)

    if problems:
        print("\nSOUNDNESS PROBLEMS (%d):" % len(problems))
        for line in problems:
            print("  - %s" % line)
        return 1
    print("\nok -- no soundness problems. %s" % out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
