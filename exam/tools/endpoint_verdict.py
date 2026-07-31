"""The endpoint-2 gate: one command, and it says no to six of seven controls.

    python -m exam.tools.endpoint_verdict --table
    python -m exam.tools.endpoint_verdict --examinee oracle        # exit 0
    python -m exam.tools.endpoint_verdict --examinee memoriser     # exit 4
    python -m exam.tools.endpoint_verdict --submission PATH        # any transcript

**Exit code is the answer**: `0` iff the endpoint credits the transcript (裁为
成立), `3` if it refuses (不成立), `4` if it cannot conclude (不可结论), `2` on a
usage error.  Three-valued on stdout and two-valued at the shell, because
`freeze/launch_blockers.json`'s contract is a command with a positive target
that exits 0 and a negative target that does not -- and 不可结论 must fail that
contract, which is precisely the ruling `launch_blockers` 9.16 asks for on the
memoriser.

**The controls, and what kills each.**  This is the table `--table` prints, and
the point of it is that no single floor catches everything: strike out any one
of the three and a different control walks through.

    examinee     sens   spec   BA      killed by
    oracle       1.000  1.000  1.000   -- credited
    bluffer      1.000  0.000  0.500   specificity floor and the BA floor
    denier       0.000  1.000  0.500   BA floor alone
    overclaimer  1.000  0.375  0.688   specificity floor alone
    abstainer    0.000  0.000  0.000   both, after 弃权计错
    memoriser    0.556  0.625  0.590   class (ii) coverage floor alone
    null         0.000  0.000  0.000   both, after 弃权计错

Three of them fall to exactly one rule each, which is what makes the three
floors separately load-bearing rather than three names for one.  `overclaimer`
exists because the leave-one-out measurement said `S_min` was not: with only
`bluffer`, `abstainer` and `null` present, deleting the specificity floor
changed no verdict at all.

Before 弃权计错 existed, `abstainer` and `null` were not scored at all -- both
rates read `None`, and `None < S_min` is not false but undefined, which is
`launch_blockers` 9.15 in one line.

`cheater-v4`, the real transcript on disk, is **credited**, identical to the
oracle in every gated number and differing only in `certified_share` (0.0
against 1.0) -- the quantity STATS_RULES §2.2 demotes to exploratory.  Printed,
not gated: see `endpoint.reason_quality`.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any, Dict, List, Optional, Sequence

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(HERE)
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from exam import endpoint as ep                                    # noqa: E402
from exam.grading.mark import mark                                 # noqa: E402
from exam.grading.registry import digest                           # noqa: E402
from exam.model import ARTIFACTS, Submission, read_json, write_json  # noqa: E402
from exam.papers import module_for                                 # noqa: E402

QUESTION_TYPE = "verdict"

#: Where the control transcripts land.  Deliberately **not** under
#: `artifacts/answers/`: `confusion_matrix._real_submissions` sweeps that
#: directory and would file a synthetic control as a real arm's submission.
CONTROLS_DIR = os.path.join(ARTIFACTS, "endpoint_controls")

#: Every control this gate ships, in the order the table prints them.  `oracle`
#: is the only positive one, and it is here so that the command is known to be
#: able to say yes -- a gate that has only ever said no is as uninformative as
#: one that has only ever said yes.
CONTROLS: Sequence[str] = ("oracle", "bluffer", "denier", "overclaimer",
                           "abstainer", "memoriser", "null")

EXIT_CREDITED = 0
EXIT_REFUTED = 3
EXIT_INCONCLUSIVE = 4
EXIT_USAGE = 2

_EXIT_OF = {ep.VERDICT_CREDITED: EXIT_CREDITED,
            ep.VERDICT_REFUTED: EXIT_REFUTED,
            ep.VERDICT_INCONCLUSIVE: EXIT_INCONCLUSIVE}


def _paper_and_key():
    module = module_for(QUESTION_TYPE)
    paper = module.build()
    return module, paper, paper.key(digest())


def control_submission(mode: str) -> Submission:
    """A control examinee as a `Submission`, from the paper's own answers."""
    module, paper, key_doc = _paper_and_key()
    answers = module.reference_answers(paper, key_doc, mode)
    return Submission(
        examinee_id="control-%s" % mode, paper_id=paper.paper_id,
        answers=answers, capabilities=() if mode == "null" else ("answers",),
        meta={"control": mode,
              "note": "a synthetic negative control for endpoint 2, not an arm"})


def judge_submission(submission: Submission) -> Dict[str, Any]:
    module, paper, key_doc = _paper_and_key()
    if submission.paper_id != paper.paper_id:
        raise SystemExit("submission is for paper %r, not %r"
                         % (submission.paper_id, paper.paper_id))
    report = mark(key_doc, submission, axes_fn=getattr(module, "axes", None))
    return ep.judge(report, key_doc)


def emit_controls(directory: Optional[str] = None) -> List[str]:
    """Write every control transcript to disk, for the launch gate's targets.

    `freeze/launch_blockers.json` 9.15 and 9.16 both name targets that did not
    exist -- 9.15's `negative_target_exists` is `false` outright.  A blocker
    whose acceptance shape names a file nobody has written cannot be cleared by
    anyone, so the files are part of the delivery.
    """
    out = directory or CONTROLS_DIR
    os.makedirs(out, exist_ok=True)
    written = []
    for mode in CONTROLS:
        path = os.path.join(out, "%s.answers.json" % mode)
        write_json(path, control_submission(mode).to_json())
        written.append(path)
    return written


def _tabled_submissions() -> Dict[str, Submission]:
    """The six controls, plus any real transcript already on disk.

    `cheater-v4` is on disk and belongs in this table more than any synthetic
    control does: it is a reader handed the sheet and nothing else, it is
    identical to ground truth in every cell of the pair, and the endpoint as
    pre-registered **credits it**. That is not a bug in the arithmetic, it is
    the ruling of `STATS_RULES.md` §2.2 executed correctly, and printing it
    beside the oracle is the only way the reader sees what the scalar cannot do.
    """
    out: Dict[str, Submission] = {m: control_submission(m) for m in CONTROLS}
    from exam.model import ANSWERS_DIR
    paper_id = _paper_and_key()[1].paper_id
    if os.path.isdir(ANSWERS_DIR):
        prefix = "%s." % paper_id
        for name in sorted(os.listdir(ANSWERS_DIR)):
            if name.startswith(prefix) and name.endswith(".answers.json"):
                doc = read_json(os.path.join(ANSWERS_DIR, name))
                submission = Submission.from_json(doc)
                out[submission.examinee_id] = submission
    return out


def table() -> Dict[str, Any]:
    rows: Dict[str, Any] = {}
    for mode, submission in _tabled_submissions().items():
        result = judge_submission(submission)
        record, ruling = result["record"], result["ruling"]
        cov = record["coverage_observed"].get("large_unsolvable", {})
        rows[mode] = {
            "verdict": ruling["verdict"],
            "credited": ruling["credited"],
            "sensitivity": ruling["sensitivity"],
            "specificity": ruling["specificity"],
            "balanced_accuracy": ruling["balanced_accuracy"],
            "observed_sensitivity": record["converted"]["overall"]["observed_sensitivity"],
            "observed_specificity": record["converted"]["overall"]["observed_specificity"],
            "class_ii_coverage_positive": cov.get("coverage_positive"),
            "score_fraction": record["score_fraction"],
            "certified_share": record["reason_quality"]["certified_share"],
            "is_control": mode in CONTROLS,
            "reasons": ruling["reasons"],
        }
    return {"paper_id": _paper_and_key()[1].paper_id,
            "rubric_digest": digest(),
            "thresholds": {"S_min": ep.S_MIN, "c_min": ep.C_MIN,
                           "ba_floor": ep.BA_FLOOR},
            "scope": ep.SCOPE_NOTE,
            "controls": rows}


def _print_table(data: Dict[str, Any]) -> None:
    print("endpoint 2 -- 判决题准确率(含特异度), controls on %s"
          % data["paper_id"])
    print("thresholds: S_min=%.2f  c_min=%.2f  BA>%.2f"
          % (data["thresholds"]["S_min"], data["thresholds"]["c_min"],
             data["thresholds"]["ba_floor"]))
    print()
    head = ("%-11s %7s %7s %7s %8s %6s  %-11s %s"
            % ("examinee", "sens", "spec", "BA", "cov(ii)", "cert",
               "verdict", "why"))
    print(head)
    print("-" * 120)
    for mode, row in data["controls"].items():
        def num(value: Any) -> str:
            return "--" if value is None else "%.3f" % value
        print("%-11s %7s %7s %7s %8s %6s  %-11s %s"
              % (mode, num(row["sensitivity"]), num(row["specificity"]),
                 num(row["balanced_accuracy"]),
                 num(row["class_ii_coverage_positive"]),
                 num(row["certified_share"]),
                 row["verdict"], row["reasons"][0]))
    print()
    print("credited: %s"
          % ", ".join(m for m, r in data["controls"].items() if r["credited"]))
    print("refused:  %s"
          % ", ".join(m for m, r in data["controls"].items() if not r["credited"]))


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--examinee", help="a control name: %s"
                                           % ", ".join(CONTROLS))
    parser.add_argument("--submission", help="path to a .answers.json")
    parser.add_argument("--table", action="store_true",
                        help="print every control and exit 0")
    parser.add_argument("--emit-controls", action="store_true",
                        help="write the control transcripts to artifacts/")
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.emit_controls:
        for path in emit_controls():
            print("wrote %s" % path)
        return 0

    if args.table:
        _print_table(table())
        return 0

    if bool(args.examinee) == bool(args.submission):
        parser.error("give exactly one of --examinee / --submission / --table")

    if args.examinee:
        if args.examinee not in CONTROLS:
            parser.error("unknown control %r" % args.examinee)
        submission = control_submission(args.examinee)
    else:
        submission = Submission.from_json(read_json(args.submission))

    result = judge_submission(submission)
    ruling = result["ruling"]
    print("%s: %s" % (submission.examinee_id, ruling["verdict"]))
    print("  sensitivity %s   specificity %s   BA %s"
          % (ruling["sensitivity"], ruling["specificity"],
             ruling["balanced_accuracy"]))
    for reason in ruling["reasons"]:
        print("  - %s" % reason)
    print("  scope: %s" % ruling["scope"])
    return _EXIT_OF[ruling["verdict"]]


if __name__ == "__main__":
    raise SystemExit(main())
