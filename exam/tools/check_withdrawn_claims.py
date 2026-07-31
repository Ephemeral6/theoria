"""A withdrawn claim must not grow back somewhere the withdrawal did not reach.

    python -m exam.tools.check_withdrawn_claims        # 0 clean, 1 a hit

D-EX-028 withdrew one sentence: class (ii) does **not** show that only invariant
reasoning can answer, because every shipped item of that class is settled by an
exhaustive computation over at most 600 nodes.  The withdrawal was written into
`DECISIONS.md`, `README.md`, the truth artefact's `class_notes` and the two
functions that build the record -- and it reached none of these:

* `exam/papers/verdict.py:14` -- the module docstring, first paragraph;
* `exam/grading/rubrics_verdict.py:11` -- "our home ground";
* `exam/grading/confusion_matrix.py:11` -- the class table;
* `exam/grading/confusion_matrix.py:246` -- `class_meaning`, which is **written
  into `exam/artifacts/matrix/verdict_confusion.json` and rendered into the
  `.md` beside it**, so the withdrawn claim was shipping in a tracked artefact
  three cycles after it was withdrawn.

That last one is the reason this file exists rather than a commit that fixes
four strings.  A withdrawal recorded in a decision log and contradicted by a
generated artefact is worse than not withdrawing it: the artefact is what a
reader quotes.

**Scope, and why it is not the whole repo.**  Only files this territory owns are
scanned.  `Theoria.md` is the design document and states the *original* claim;
that is the baseline, not a defect, and a gate that told the exam track to edit
the baseline would be wrong in a way that is hard to undo.  `DECISIONS.md` is
excluded for the same reason one level down -- it has to be able to quote the
sentence it is withdrawing -- and so are this file and its test, which both have
to contain the patterns to check for them.
"""

from __future__ import annotations

import os
import re
import sys
from typing import Dict, List, Sequence, Tuple

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(HERE)
if REPO not in sys.path:
    sys.path.insert(0, REPO)

#: (label, pattern, what to say instead).  Patterns are deliberately narrow:
#: a scanner that fires on ordinary prose gets switched off within a day
#: (D-EX-031's own finding about the location scanner).
WITHDRAWN: Sequence[Tuple[str, str, str]] = (
    ("only-invariant-en",
     r"only\s+(?:an\s+)?invariant(?:\s+reasoning)?\s+(?:can\s+)?answer",
     "class (ii) measures method selection under an apparent search barrier; "
     "say `naive enumeration is out of reach` and name the method"),
    ("only-invariant-zh",
     r"唯不变量推理能答|只有不变量推理能答",
     "同上：可说『朴素枚举不可行』，不可说『唯不变量能答』"),
    ("exhaustive-out-of-reach",
     r"exhaustive\s+search\s+is\s+out\s+of\s+reach",
     "an exhaustive computation over <=600 nodes settles every shipped class "
     "(ii) item; the true statement is about *naive* enumeration"),
    ("exhaustive-feasible-field",
     r"\bexhaustive_feasible\b",
     "the field is `naive_enumeration_feasible`; the old name asserted "
     "something no shipped item supports"),
)

#: A record of a withdrawal has to be able to quote the sentence it withdrew, so
#: a hit is acquitted when one of these appears **within `WINDOW` lines of it**.
#: Same-line only was tried first and is too tight for prose: the withdrawal and
#: the quoted sentence routinely sit in adjacent lines of the same paragraph, and
#: a gate that forced them onto one line would be editing prose to suit itself.
#: Two lines each way is the widest window under which no shipped assertion in
#: this territory is acquitted -- measured, not guessed: `--audit` prints every
#: acquittal so the exemptions can be read rather than trusted.
ACQUITTALS: Sequence[str] = (
    "withdraw", "撤回", "D-EX-028", "was false", "is false",
    "does not survive", "must not", "no longer", "renamed", "old name",
    "used to", "superseded",
)

WINDOW = 2

#: Files that are allowed to contain the withdrawn wording, each for a reason.
EXEMPT = {
    "exam/DECISIONS.md",                        # quotes what it withdraws
    "exam/tools/check_withdrawn_claims.py",     # this file
    "exam/tests/test_withdrawn_claims.py",      # its test
}

#: `exam/runs/**` is the provenance archive.  A run record says what was
#: measured on the day it was measured, and D-EX-028's own evidence lives in
#: `runs/20260730T021500Z-V23-large-space/` -- which quotes the withdrawn field
#: name on nearly every page, because that is what it was investigating.  A gate
#: that demanded those files be rewritten would be asking for the record to be
#: falsified, which is a worse defect than the one it is closing.  Live surfaces
#: only: code, the territory's documents, and generated artefacts.
EXEMPT_PREFIXES = ("exam/runs/",)

SCAN_SUFFIXES = (".py", ".md", ".json")


def _tracked_exam_files() -> List[str]:
    import subprocess
    out = subprocess.run(["git", "ls-files", "exam"], cwd=REPO,
                         capture_output=True, text=True)
    if out.returncode != 0:                       # pragma: no cover
        raise RuntimeError("git ls-files failed: %s" % out.stderr[-400:])
    return [p for p in out.stdout.splitlines()
            if p.endswith(SCAN_SUFFIXES) and p not in EXEMPT
            and not p.startswith(EXEMPT_PREFIXES)]


def _acquitted(lines: Sequence[str], index: int) -> str:
    """The withdrawal marker near this line, or `""` if there is none."""
    lo = max(0, index - WINDOW)
    hi = min(len(lines), index + WINDOW + 1)
    near = " ".join(lines[lo:hi]).lower()
    for marker in ACQUITTALS:
        if marker.lower() in near:
            return marker
    return ""


def scan(paths: Sequence[str] | None = None, *,
         keep_acquitted: bool = False) -> List[Dict[str, object]]:
    hits: List[Dict[str, object]] = []
    for rel in (paths if paths is not None else _tracked_exam_files()):
        full = os.path.join(REPO, rel)
        if not os.path.isfile(full):
            continue
        with open(full, "r", encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        for index, line in enumerate(lines):
            for label, pattern, instead in WITHDRAWN:
                if not re.search(pattern, line, flags=re.IGNORECASE):
                    continue
                acquittal = _acquitted(lines, index)
                if acquittal and not keep_acquitted:
                    continue
                hits.append({"file": rel, "line": index + 1,
                             "pattern": label, "instead": instead,
                             "acquitted_by": acquittal,
                             "text": line.strip()[:160]})
    return hits


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    audit = "--audit" in args
    args = [a for a in args if a != "--audit"]
    hits = scan(args or None)
    scanned = len(args) if args else len(_tracked_exam_files())
    if audit:
        # Every acquittal, printed. An exemption nobody can list is an exemption
        # nobody can argue with, which is how a scanner becomes decoration.
        every = scan(args or None, keep_acquitted=True)
        print("acquitted by a nearby withdrawal marker: %d"
              % sum(1 for h in every if h["acquitted_by"]))
        for hit in every:
            if hit["acquitted_by"]:
                print("  %s:%s  [%s] acquitted by %r"
                      % (hit["file"], hit["line"], hit["pattern"],
                         hit["acquitted_by"]))
    print("withdrawn-claim scan: %d tracked exam files, %d pattern(s), %d hit(s)"
          % (scanned, len(WITHDRAWN), len(hits)))
    for hit in hits:
        print("  %s:%s  [%s]" % (hit["file"], hit["line"], hit["pattern"]))
        print("      %s" % hit["text"])
        print("      instead: %s" % hit["instead"])
    if hits:
        print("\nRED: a claim withdrawn by D-EX-028 is still on disk. The "
              "withdrawal is not a matter of record until the record says it.")
        return 1
    print("clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
