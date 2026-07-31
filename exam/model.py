"""The exam's core types, and the one invariant that holds the whole thing up.

**A question has two sides and they are never in the same file.**

    Item.paper   what the examinee sees.  Written to artifacts/papers/.
    Item.truth   what the referee holds.  Written to artifacts/truth/.

That split is not tidiness.  An exam whose paper carries its own answer key
measures nothing, and the failure mode is silent: the paper still looks like a
paper, the examinee still scores, and the number is worthless.  So the split is
enforced by construction (`Paper.sheet()` cannot emit a truth field -- it never
receives one) and then attacked from the outside by `exam.leakage`, which runs
declared probes over the serialised sheet, and by a cheater subagent that is
handed the sheet alone and told to extract answers from it.

**The rubric is frozen before the answers exist.**  Every sheet carries
`rubric_digest`, the sha256 of the grading code that will mark it.  Every report
carries the digest it graded under.  A rubric edited after seeing answers is
therefore not an accusation anyone has to make -- it is a digest mismatch that
the tooling prints.  Same discipline as the battery's pre-registered directions,
same reason.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

#: Where the builders write.  The tracked tree by default; a shadow tree when
#: `EXAM_ARTIFACTS_DIR` is set.
#:
#: The redirect exists because `exam/verify.py` used to prove its case by
#: destroying the evidence: `build_papers` overwrites in place, so by the time
#: any stage could have asked "is what is committed what this code produces?",
#: the committed bytes were gone from the working tree.  Verify now seeds a
#: shadow copy of `exam/artifacts`, points every producer at it, and compares
#: the shadow against the tracked tree, which stays untouched for the whole run.
#: Adoption of a rebuild is then a separate, deliberate act -- running
#: `python -m exam.tools.build_papers` with no redirect -- and never a side
#: effect of asking whether a rebuild was needed.  V2/V25.
ARTIFACTS = os.path.abspath(os.environ.get("EXAM_ARTIFACTS_DIR")
                            or os.path.join(HERE, "artifacts"))
#: The path an artefact records for itself, always, regardless of where the
#: build ran.  `artifact_rel` below is the only thing that may produce one.
ARTIFACTS_LABEL = "exam/artifacts"
PAPERS_DIR = os.path.join(ARTIFACTS, "papers")
TRUTH_DIR = os.path.join(ARTIFACTS, "truth")
ANSWERS_DIR = os.path.join(ARTIFACTS, "answers")
REPORTS_DIR = os.path.join(ARTIFACTS, "reports")


def artifact_rel(path: str) -> str:
    r"""The repo-relative name of an artefact, independent of where it was built.

    A tracked generated artefact must not record where its builder stood (V27):
    `build_manifest.json` once held twelve absolute paths naming whichever
    worktree ran last, which is a merge-conflict generator between two branches
    that agree, and `archive_run.py` carries the file into the provenance canon
    and from there into a release manifest that publishes every tracked file.

    Relative to `ARTIFACTS` rather than to `REPO`, then relabelled: under the
    shadow-tree redirect a repo-relative path would come out as
    `../../AppData/.../papers/x.json`, so the artefact would differ from its
    committed twin for no reason but the redirect, and the match gate would
    read that as drift.  Forward slashes, so the value is identical on both
    platforms.
    """
    rel = os.path.relpath(os.path.abspath(path), ARTIFACTS).replace(os.sep, "/")
    if rel.startswith("../"):
        raise ExamError("not an artefact path: %r" % path)
    return "%s/%s" % (ARTIFACTS_LABEL, rel)

#: The four question types of Theoria.md 1.11.  Frozen: a fifth type is a
#: change to the evaluation protocol, not a change to this file.
QUESTION_TYPES = ("heldout", "handover", "adaptation", "verdict")

SCHEMA_VERSION = "exam/v0.1"


class ExamError(RuntimeError):
    pass


class LeakageError(ExamError):
    """The paper carries information only the referee is allowed to hold."""


# --------------------------------------------------------------- canonical io

def canonical(obj: Any) -> str:
    """One serialisation, everywhere.  Digests are only comparable if the bytes
    are produced the same way, and byte-reproducibility is a requirement here
    rather than a nicety (CLAUDE.md)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


def sha256(obj: Any) -> str:
    return hashlib.sha256(canonical(obj).encode("utf-8")).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_json(path: str, payload: Any) -> str:
    """Deterministic, LF, trailing newline.  Returns the path."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    return path


def read_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


# ------------------------------------------------------------------- the item

@dataclass(frozen=True)
class Item:
    """One question.  `paper` and `truth` are disjoint by contract.

    `leak_probes` is the item's own statement of what would count as leakage:
    the exact strings whose appearance in the sheet would hand the answer over.
    A builder that declares none is not trusted -- `Paper.check_leakage` treats
    an empty probe list on an item with a non-trivial truth as a failure, since
    "I could not think of a probe" is the state in which leaks survive.
    """

    item_id: str
    rubric_id: str
    points: float
    paper: Dict[str, Any]
    truth: Dict[str, Any]
    leak_probes: Sequence[str] = ()
    tags: Sequence[str] = ()

    def sheet_side(self) -> Dict[str, Any]:
        return {"item_id": self.item_id, "points": self.points,
                "tags": list(self.tags), **self.paper}

    def key_side(self) -> Dict[str, Any]:
        return {"item_id": self.item_id, "rubric_id": self.rubric_id,
                "points": self.points, "tags": list(self.tags),
                "truth": self.truth}


# ------------------------------------------------------------------ the paper

@dataclass
class Paper:
    """A set of items of one question type, plus the provenance of its world."""

    paper_id: str
    question_type: str
    instructions: str
    items: List[Item]
    world: Dict[str, Any] = field(default_factory=dict)
    notes: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.question_type not in QUESTION_TYPES:
            raise ExamError("unknown question type %r; the four types of "
                            "Theoria.md 1.11 are %s"
                            % (self.question_type, list(QUESTION_TYPES)))
        seen = set()
        for item in self.items:
            if item.item_id in seen:
                raise ExamError("duplicate item_id %r in %s"
                                % (item.item_id, self.paper_id))
            seen.add(item.item_id)

    # -- the two sides ----------------------------------------------------
    def sheet(self, rubric_digest: str,
              rubric_module_digest: Optional[str] = None) -> Dict[str, Any]:
        """What the examinee receives.  Cannot contain a truth: it is built
        from `Item.sheet_side`, which never sees one.

        Two digests, because one is not enough.  `rubric_digest` covers the whole
        registry and is therefore *identical on every sheet*, which a cheater
        subagent pointed out makes it useless as a seal binding a paper to the
        code that marks it.  `rubric_module_digest` covers only the module that
        owns this question type, so an edit to the verdict rubrics changes the
        verdict sheet's seal and leaves the held-out sheet's alone.
        """
        return {
            "schema": SCHEMA_VERSION,
            "paper_id": self.paper_id,
            "question_type": self.question_type,
            "instructions": self.instructions,
            "world": self.world,
            "rubric_digest": rubric_digest,
            "rubric_module_digest": rubric_module_digest,
            "n_items": len(self.items),
            "total_points": round(sum(i.points for i in self.items), 6),
            "items": [i.sheet_side() for i in self.items],
        }

    def key(self, rubric_digest: str) -> Dict[str, Any]:
        """What the referee receives.  Never handed to an examinee."""
        return {
            "schema": SCHEMA_VERSION,
            "paper_id": self.paper_id,
            "question_type": self.question_type,
            "rubric_digest": rubric_digest,
            "notes": self.notes,
            "items": [i.key_side() for i in self.items],
        }

    def leak_probes(self) -> Dict[str, List[str]]:
        return {i.item_id: [str(p) for p in i.leak_probes] for i in self.items}


# --------------------------------------------------------------- the examinee

@dataclass(frozen=True)
class Submission:
    """An examinee's answers to one paper.

    `capabilities` is how an arm declares what it can even be asked.  The bare
    CC arm has no deliverable, so it declares none and scores zero on handover
    by construction -- Theoria.md 1.11 says "CC 无物可交记零", and a zero that
    the code derives is worth more than a zero someone wrote down.
    """

    examinee_id: str
    paper_id: str
    answers: Dict[str, Any]
    capabilities: Sequence[str] = ()
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> Dict[str, Any]:
        return {"schema": SCHEMA_VERSION, "examinee_id": self.examinee_id,
                "paper_id": self.paper_id, "capabilities": list(self.capabilities),
                "meta": dict(self.meta), "answers": self.answers}

    @classmethod
    def from_json(cls, doc: Dict[str, Any]) -> "Submission":
        return cls(examinee_id=doc["examinee_id"], paper_id=doc["paper_id"],
                   answers=doc.get("answers", {}),
                   capabilities=doc.get("capabilities", ()),
                   meta=doc.get("meta", {}))


# ---------------------------------------------------------------- the marking

@dataclass(frozen=True)
class ItemScore:
    item_id: str
    rubric_id: str
    awarded: float
    possible: float
    verdict: str                       # correct | wrong | abstained | unanswered
    detail: Dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> Dict[str, Any]:
        return {"item_id": self.item_id, "rubric_id": self.rubric_id,
                "awarded": round(self.awarded, 6),
                "possible": round(self.possible, 6),
                "verdict": self.verdict, "detail": self.detail}


VERDICTS = ("correct", "wrong", "abstained", "unanswered")


@dataclass(frozen=True)
class Rubric:
    """A marking rule, named and frozen.

    `grade` receives (answer, truth, item) and must be a pure function of those
    three.  It may not consult the paper's world, the examinee's identity, or
    anything on disk: a rubric that can see who it is marking is a rubric that
    can flatter.
    """

    rubric_id: str
    description: str
    grade: Callable[[Any, Dict[str, Any], Item], ItemScore]


def unanswered(item: Item, why: str = "no answer submitted") -> ItemScore:
    return ItemScore(item.item_id, item.rubric_id, 0.0, item.points,
                     "unanswered", {"why": why})


@dataclass
class Report:
    paper_id: str
    examinee_id: str
    question_type: str
    rubric_digest: str
    scores: List[ItemScore]
    axes: Dict[str, Any] = field(default_factory=dict)
    meta: Dict[str, Any] = field(default_factory=dict)

    @property
    def awarded(self) -> float:
        return round(sum(s.awarded for s in self.scores), 6)

    @property
    def possible(self) -> float:
        return round(sum(s.possible for s in self.scores), 6)

    @property
    def fraction(self) -> float:
        return round(self.awarded / self.possible, 6) if self.possible else 0.0

    def by_tag(self, tag_of: Dict[str, Sequence[str]]) -> Dict[str, Any]:
        """Sub-scores per tag.  A single percentage hides the case that matters:
        a theory can be right on the common rule and wrong on the rare one and
        still look excellent overall (a0-spike T-9)."""
        buckets: Dict[str, List[ItemScore]] = {}
        for score in self.scores:
            for tag in tag_of.get(score.item_id, ()):
                buckets.setdefault(tag, []).append(score)
        out = {}
        for tag, group in sorted(buckets.items()):
            got = sum(s.awarded for s in group)
            can = sum(s.possible for s in group)
            out[tag] = {"n": len(group), "awarded": round(got, 6),
                        "possible": round(can, 6),
                        "fraction": round(got / can, 6) if can else 0.0}
        return out

    def to_json(self) -> Dict[str, Any]:
        return {
            "schema": SCHEMA_VERSION,
            "paper_id": self.paper_id,
            "examinee_id": self.examinee_id,
            "question_type": self.question_type,
            "rubric_digest": self.rubric_digest,
            "awarded": self.awarded,
            "possible": self.possible,
            "fraction": self.fraction,
            "counts": {v: sum(1 for s in self.scores if s.verdict == v)
                       for v in VERDICTS},
            "axes": self.axes,
            "meta": self.meta,
            "scores": [s.to_json() for s in self.scores],
        }


# --------------------------------------------------------------- paper naming

def paper_path(paper_id: str) -> str:
    return os.path.join(PAPERS_DIR, "%s.paper.json" % paper_id)


def truth_path(paper_id: str) -> str:
    return os.path.join(TRUTH_DIR, "%s.truth.json" % paper_id)


def answers_path(paper_id: str, examinee_id: str) -> str:
    return os.path.join(ANSWERS_DIR, "%s.%s.answers.json" % (paper_id, examinee_id))


def report_path(paper_id: str, examinee_id: str) -> str:
    return os.path.join(REPORTS_DIR, "%s.%s.report.json" % (paper_id, examinee_id))
