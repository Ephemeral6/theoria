"""Calibrate the marker, then mark whatever has been submitted.

    python -m exam.tools.run_exam                 # calibrate + mark everything
    python -m exam.tools.run_exam --calibrate     # calibration only

The order is not a convenience.  `exam.grading.calibration.assert_calibrated`
runs before any real submission is marked, and raises if the four fakes do not
reproduce their pre-registered scores.  A marker that cannot recognise ground
truth, or that pays for silence, does not produce a low-confidence number -- it
produces a number with no relationship to the thing it names, and the only safe
response is to refuse.

Real submissions are picked up from `exam/artifacts/answers/`, named
`<paper_id>.<examinee_id>.answers.json`.  That is where the fresh-reader
subagents' answers land, and where an arm's answers would land in Phase 4.
"""

from __future__ import annotations

import glob
import os
import sys
from typing import Any, Dict, List, Optional

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(HERE)
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from exam import guard                                              # noqa: E402
from exam.grading.calibration import assert_calibrated, calibrate_all  # noqa: E402
from exam.grading.mark import mark                                  # noqa: E402
from exam.grading.registry import digest                            # noqa: E402
from exam.model import (ANSWERS_DIR, ARTIFACTS, Submission,  # noqa: E402
                        artifact_rel, read_json, report_path, truth_path,
                        write_json)
from exam.papers import BUILDERS, module_for                        # noqa: E402

CALIBRATION_PATH = os.path.join(ARTIFACTS, "calibration.json")
SUMMARY_PATH = os.path.join(ARTIFACTS, "exam_summary.json")


def _type_of(key_doc: Dict[str, Any]) -> str:
    return key_doc["question_type"]


def collect_submissions(directory: str = ANSWERS_DIR) -> List[Submission]:
    out = []
    for path in sorted(glob.glob(os.path.join(directory, "*.answers.json"))):
        out.append(Submission.from_json(read_json(path)))
    return out


def mark_submission(submission: Submission) -> Dict[str, Any]:
    key_doc = read_json(truth_path(submission.paper_id))
    question_type = _type_of(key_doc)
    assert_calibrated(question_type)
    module = module_for(question_type)
    report = mark(key_doc, submission, axes_fn=getattr(module, "axes", None))
    path = write_json(report_path(submission.paper_id, submission.examinee_id),
                      report.to_json())
    return {"paper_id": submission.paper_id, "examinee_id": submission.examinee_id,
            "question_type": question_type, "fraction": report.fraction,
            "awarded": report.awarded, "possible": report.possible,
            # Repo-relative, like every other path an artefact records: this one
            # reaches `exam_summary.json`, which is tracked.  It has been empty
            # in every committed summary so far, so the absolute path never
            # shipped -- one marked submission was all it would have taken.
            "axes": report.axes, "report_path": artifact_rel(path)}


def run(*, calibrate_only: bool = False,
        question_types: Optional[List[str]] = None) -> Dict[str, Any]:
    with guard.no_network():
        calibration = calibrate_all(question_types)
        write_json(CALIBRATION_PATH, calibration)
        marked: List[Dict[str, Any]] = []
        if not calibrate_only and calibration["calibrated"]:
            for submission in collect_submissions():
                if not os.path.exists(truth_path(submission.paper_id)):
                    marked.append({"paper_id": submission.paper_id,
                                   "examinee_id": submission.examinee_id,
                                   "error": "no answer key on disk; build the "
                                            "paper before marking it"})
                    continue
                marked.append(mark_submission(submission))
    payload = {"rubric_digest": digest(), "calibrated": calibration["calibrated"],
               "calibration_failures": calibration["failures"],
               "provenance": guard.provenance(), "marked": marked}
    write_json(SUMMARY_PATH, payload)
    return payload


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    calibrate_only = "--calibrate" in argv
    types = [a for a in argv if a in BUILDERS] or None

    payload = run(calibrate_only=calibrate_only, question_types=types)
    calibration = read_json(CALIBRATION_PATH)

    print("exam -- calibration (rubric digest %s)" % payload["rubric_digest"][:12])
    print("-" * 78)
    print("  %-13s %-9s %-9s %-11s %-9s %s"
          % ("paper", "oracle", "null", "memoriser", "bluffer", "verdict"))
    for qt, result in sorted(calibration["per_type"].items()):
        modes = result["modes"]
        print("  %-13s %-9.4f %-9.4f %-11.4f %-9.4f %s"
              % (qt, modes["oracle"]["fraction"], modes["null"]["fraction"],
                 modes["memoriser"]["fraction"], modes["bluffer"]["fraction"],
                 "CALIBRATED" if result["calibrated"] else "** FAILED **"))
    print("-" * 78)
    for failure in payload["calibration_failures"]:
        print("  ! %s" % failure)

    if payload["marked"]:
        print("\nexam -- submissions")
        print("-" * 78)
        for row in payload["marked"]:
            if "error" in row:
                print("  %-24s %-16s ! %s"
                      % (row["paper_id"], row["examinee_id"], row["error"]))
            else:
                print("  %-24s %-16s %.4f  (%.4g/%.4g)"
                      % (row["paper_id"], row["examinee_id"], row["fraction"],
                         row["awarded"], row["possible"]))
    elif not calibrate_only:
        print("\n  no submissions in %s" % ANSWERS_DIR)

    print("\n  -> %s" % SUMMARY_PATH)
    return 0 if payload["calibrated"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
