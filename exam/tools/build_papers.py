"""Build the four papers, and split each one into a sheet and an answer key.

    python -m exam.tools.build_papers            # all four
    python -m exam.tools.build_papers verdict    # one

The two sides land in different directories, and that is the only reason the
directories exist:

    exam/artifacts/papers/   the sheets.  Safe to hand to an examinee.
    exam/artifacts/truth/    the keys.    Never handed to an examinee.

Every sheet is checked for leakage before it is written, and the build fails
rather than writing a sheet that carries its own answers.  Failing closed
matters more here than usual: a leaked sheet does not look broken, it looks like
a paper on which everybody did unusually well.

The build also writes a cheater brief per paper -- the sheet, packaged with an
adversarial instruction, ready to hand to a subagent that has no other context.
Static checks test the leaks we imagined; the cheater tests the rest.
"""

from __future__ import annotations

import os
import sys
from typing import Any, Dict, List, Optional, Sequence

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(HERE)
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from exam import guard, leakage                                     # noqa: E402
from exam.grading.registry import (digest, manifest,          # noqa: E402
                                   module_digests)
from exam.model import (ARTIFACTS, Paper, canonical, paper_path, sha256,  # noqa: E402
                        truth_path, write_json)
from exam.papers import BUILDERS, module_for                        # noqa: E402

CHEATER_DIR = os.path.join(ARTIFACTS, "cheater")
LEAKAGE_PATH = os.path.join(ARTIFACTS, "leakage.json")
MANIFEST_PATH = os.path.join(ARTIFACTS, "build_manifest.json")


def _answer_labels(module: Any, paper: Paper, key_doc: Dict[str, Any]
                   ) -> Optional[Dict[str, str]]:
    """Short answer labels for the positional-independence check.

    Optional: a paper whose answers are frames rather than labels has nothing
    positional to correlate, and forcing a label on it would invent a signal.
    """
    fn = getattr(module, "answer_labels", None)
    if fn is None:
        return None
    return fn(paper, key_doc)


def build_one(question_type: str, *, write: bool = True) -> Dict[str, Any]:
    module = module_for(question_type)
    rubric_digest = digest()

    paper: Paper = module.build()
    if paper.question_type != question_type:
        raise RuntimeError("%s.build() returned a %r paper"
                           % (question_type, paper.question_type))

    module_digest = module_digests().get(
        "exam.grading.rubrics_%s" % question_type)
    sheet = paper.sheet(rubric_digest, module_digest)
    key_doc = paper.key(rubric_digest)

    report = leakage.check_paper(
        paper, sheet, key_doc=key_doc,
        answer_of=_answer_labels(module, paper, key_doc))

    out: Dict[str, Any] = {
        "question_type": question_type,
        "paper_id": paper.paper_id,
        "n_items": len(paper.items),
        "total_points": sheet["total_points"],
        "rubric_digest": rubric_digest,
        "sheet_sha256": sha256(sheet),
        "key_sha256": sha256(key_doc),
        "leakage": report,
    }

    if write:
        out["sheet_path"] = write_json(paper_path(paper.paper_id), sheet)
        out["key_path"] = write_json(truth_path(paper.paper_id), key_doc)
        brief = leakage.cheater_brief(sheet)
        os.makedirs(CHEATER_DIR, exist_ok=True)
        brief_path = os.path.join(CHEATER_DIR, "%s.brief.txt" % paper.paper_id)
        with open(brief_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(brief)
            if not brief.endswith("\n"):
                fh.write("\n")
        out["cheater_brief_path"] = brief_path
        out["cheater_brief_sha256"] = sha256(brief)
    return out


def build_all(question_types: Optional[Sequence[str]] = None, *,
              write: bool = True) -> Dict[str, Any]:
    types = list(question_types or BUILDERS)
    with guard.no_network():
        results = [build_one(qt, write=write) for qt in types]
    payload = {
        "rubric_manifest": manifest(),
        "provenance": guard.provenance(),
        "papers": results,
    }
    if write:
        write_json(MANIFEST_PATH, payload)
        write_json(LEAKAGE_PATH,
                   {"papers": [{"paper_id": r["paper_id"], **r["leakage"]}
                               for r in results]})
    return payload


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    unknown = [a for a in argv if a not in BUILDERS]
    if unknown:
        print("unknown question type(s): %s; known: %s"
              % (unknown, sorted(BUILDERS)))
        return 2

    payload = build_all(argv or None)
    print("exam -- built %d paper(s), rubric digest %s"
          % (len(payload["papers"]), payload["rubric_manifest"]["rubric_digest"][:12]))
    print("-" * 78)
    print("  %-22s %-6s %-8s %-14s %s"
          % ("paper", "items", "points", "sheet sha", "leakage"))
    for row in payload["papers"]:
        lk = row["leakage"]
        print("  %-22s %-6d %-8.6g %-14s probes=%d hits=%d"
              % (row["paper_id"], row["n_items"], row["total_points"],
                 row["sheet_sha256"][:12], lk["probes_declared"],
                 lk["probe_hits"] + lk["structural_hits"]))
    print("-" * 78)
    print("  sheets -> %s" % os.path.join(ARTIFACTS, "papers"))
    print("  keys   -> %s   (referee only)" % os.path.join(ARTIFACTS, "truth"))
    print("  cheater briefs -> %s" % CHEATER_DIR)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
