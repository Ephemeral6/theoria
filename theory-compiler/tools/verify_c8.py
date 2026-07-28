"""C8 verifier — one command that re-establishes every claim the run makes.

    cd theory-compiler && python -m tools.verify_c8

Six checks, each the executable form of a sentence in `RUN_STATE.md`:

1. the whole track's suite still passes;
2. both shipped packages rebuild byte-for-byte from their sources;
3. every sha256 in each `MANIFEST.json` is the digest of the file beside it;
4. a fresh context scan of each package finds zero blocking leaks, and the
   citation count matches what `SEAL.md` and `MANIFEST.json` report;
5. every question sheet rebuilds identically, so the readers' scores are scores
   against a paper that still exists;
6. the recorded reader answers still mark the way the run says they marked.

Exit code 0 only if all six hold. Nothing here touches the network, calls a
model, or reads a sealed game.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TRACK = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(TRACK, "src"))
sys.path.insert(0, HERE)

from theory_compiler import handover                          # noqa: E402
import build_handover_packages as builder                     # noqa: E402
import handover_exam                                          # noqa: E402

RUN = os.path.join(TRACK, "runs", "20260728T134022Z-C8-handover-package")
ACCEPTANCE = os.path.join(RUN, "acceptance")
PACKAGE_ROOT = os.path.join(TRACK, "handover_packages")

_failures = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print("%-4s %s%s" % ("PASS" if ok else "FAIL", label,
                         ("  -- " + detail) if detail and not ok else ""))
    if not ok:
        _failures.append(label)


def _load(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    print("== 1. the track's suite ==")
    result = subprocess.run([sys.executable, "-m", "pytest", "-q"],
                            cwd=TRACK, capture_output=True, text=True)
    tail = (result.stdout or result.stderr).strip().split("\n")[-1]
    check("pytest", result.returncode == 0, tail)
    print("     %s" % tail)

    print("== 2-4. the packages ==")
    for name in sorted(builder.PACKAGES):
        spec = builder.PACKAGES[name]()
        want, _manifest = handover.build_files(spec)
        out = os.path.join(PACKAGE_ROOT, name)
        have = handover.read_package(out)
        check("%s rebuilds byte-for-byte" % name, have == want,
              "%d files on disk, %d rebuilt, %d differ"
              % (len(have), len(want),
                 len([p for p in set(have) & set(want) if have[p] != want[p]])))

        manifest = json.loads(have["MANIFEST.json"])
        digests_ok = all(handover._sha256(have[p]) == d
                         for p, d in manifest["files"].items()
                         if p in have)
        listed_ok = sorted(manifest["files"]) == sorted(
            p for p in have if p != "MANIFEST.json")
        check("%s manifest digests" % name, digests_ok and listed_ok)

        findings = handover.context_report(have)
        blocking = [f for f in findings if f.severity == "blocking"]
        citations = len([f for f in findings if f.severity == "citation"])
        check("%s context scan" % name,
              not blocking
              and manifest["context_scan"]["citations"] == citations
              and ("citations: %d" % citations) in have["SEAL.md"],
              "%d blocking, %d citations vs %d reported"
              % (len(blocking), citations,
                 manifest["context_scan"]["citations"]))

    print("== 5-6. the acceptance ==")
    for name in sorted(builder.PACKAGES):
        pkg = os.path.join(PACKAGE_ROOT, name)
        truth_path = os.path.join(ACCEPTANCE, "%s.truth.json" % name)
        answers_path = os.path.join(ACCEPTANCE, "%s.answers.json" % name)
        report_path = os.path.join(ACCEPTANCE, "%s.report.json" % name)
        if not os.path.isfile(truth_path):
            check("%s sheet present" % name, False, truth_path)
            continue
        rebuilt = handover_exam.build_sheet(pkg)
        stored = _load(truth_path)
        check("%s sheet rebuilds identically" % name, rebuilt == stored)

        if not os.path.isfile(answers_path):
            check("%s reader answers present" % name, False, answers_path)
            continue
        report = handover_exam.mark(pkg, stored, _load(answers_path))
        stored_report = _load(report_path) if os.path.isfile(report_path) else None
        wrong = [s for s in report["scores"]
                 if s["verdict"] in ("wrong", "unparsed")]
        check("%s reader made no wrong answer" % name, not wrong,
              "; ".join("%s: %s" % (s["item_id"], s["verdict"]) for s in wrong))
        if stored_report is not None:
            check("%s report still reproduces" % name,
                  stored_report["right"] == report["right"]
                  and stored_report["items"] == report["items"],
                  "stored %s/%s, recomputed %s/%s"
                  % (stored_report["right"], stored_report["items"],
                     report["right"], report["items"]))
        print("     %s: %d/%d right, %s"
              % (name, report["right"], report["items"],
                 json.dumps(report["by_kind"], sort_keys=True)))

    print()
    if _failures:
        print("FAILED: %s" % ", ".join(_failures))
        return 1
    print("all checks pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
