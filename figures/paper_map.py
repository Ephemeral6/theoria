"""Which plate is which **Figure** in the paper, and where its numbers came from.

The pipeline numbers its plates after ``Theoria.md`` §3.2's figure list --
``fig02_bill_shape`` … ``fig07_a0_vs_a0prime``. The paper numbers its figures
by order of first citation, which is the publishing convention and the only
numbering a reader can resolve from the string "Figure 3". Those two numberings
have never agreed and there is no reason they should: §3.2 is a list of the
pictures the project wants, and the paper is a document with a reading order.

This module is the join. It exists so that the join lives in **one** place --
`P8`'s changelog is a list of what happens when a fact about another file is
written down twice.

Three things are derived here and never typed:

* **Which files a figure reads.** Taken from ``sources.SOURCES`` by the
  ``figures`` tuple each ``Source`` already carries. A caption that named its
  inputs by hand would be a second, ageing copy of the registry.
* **Whether a figure is complete.** A figure with a declared-absent source is
  ``partial``, and the caption says which paths are missing and why. Nothing is
  marked complete by assertion.
* **Which run.** Resolved through ``RunRef`` against the declared sources, so a
  caption's run identity is read out of the same hashed bytes the plate is drawn
  from. Where an artefact publishes **no** run identifier -- most of
  ``cold-start-a2/artifacts/`` does not -- the caption says so rather than
  inventing one. An unpublished run id is a fact about the tree, not a blank to
  fill in.

Nothing here reads or writes an artefact; it declares and resolves. The emit
lives in ``theme.save`` (images) and ``paper_index.py`` (index and captions).
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import sources  # noqa: E402

#: Publication profile. The screen profile in ``theme.py`` stays at 200 dpi SVG
#: + PNG; this is what a submission consumes.
#:
#: ``pdf`` is here because ``\includegraphics`` and every Markdown-to-PDF
#: pipeline want a vector page, and because ``theme.py`` has pinned
#: ``pdf.compression = 0`` since P-21 -- the format was anticipated and never
#: emitted. Determinism was checked before it was planned, not after.
PUB_FORMATS: tuple[str, ...] = ("pdf", "png", "svg")

#: 300 dpi at the figure's *declared physical size* is the print standard. The
#: screen profile's 200 is fine on a monitor and below spec on paper.
PUB_DPI: int = 300


@dataclass(frozen=True)
class RunRef:
    """Where a figure's run identity is published, as a pointer into the tree.

    ``kind``:

    ``discovery``   ``target`` is a ``sources.Rule`` name; the run ids are the
                    entry names the rule found. These are literally run
                    directories, so this is the strongest form available.
    ``json_keys``   ``target`` is a source key, ``pointer`` a dotted path; the
                    ids are the sorted keys of the dict found there.
    ``json_value``  same, but the value itself (scalar or list of scalars).
    ``json_pluck``  same, but ``field`` is plucked from each item of a list.
    ``git_commits`` ``target`` is a source key; the ids are the commits that
                    touched that path, oldest first.
    """

    kind: str
    target: str
    label: str
    pointer: str = ""
    field: str = ""
    #: Keep only ids starting with this prefix. Used where an artefact's top
    #: level mixes runs with other things -- ``prime_report.json`` holds
    #: ``run_a``/``run_b`` beside ``engines`` and ``trace``. A prefix filter
    #: still discovers a ``run_c`` that lands later; naming the two runs by hand
    #: would not.
    select: str = ""


@dataclass(frozen=True)
class PaperFigure:
    number: int
    slug: str
    pipeline: str
    section: str
    section_title: str
    title: str
    shows: str
    run_refs: tuple[RunRef, ...] = ()
    supersedes: tuple[str, ...] = ()

    @property
    def pub_name(self) -> str:
        """The filename stem a citation resolves to: ``figure3_a2_repair_loop``."""
        return f"figure{self.number}_{self.slug}"

    @property
    def cite(self) -> str:
        return f"Figure {self.number}"


#: Assigned by **order of first citation**, which keeps the paper's existing
#: Figure 1 / 2 / 3 pointing at the same three subjects they already point at.
#: Any other assignment would renumber prose that another session is editing.
#:
#: The pipeline slugs are deliberately NOT renamed: ``build_all.FIGURES``,
#: ``check_coverage.py``, ``SOURCES.md``, ``PLAN.md`` and every
#: ``Source.figures`` tuple key on them, and ``verify.sh`` gate 6 diffs the
#: committed ``out/`` tree by those names. This is a second view, not a rename.
PAPER_FIGURES: tuple[PaperFigure, ...] = (
    PaperFigure(
        number=1,
        slug="concept_timeline",
        pipeline="fig06_concept_timeline",
        section="3",
        section_title="A0 and A0' -- reversibility beats coverage",
        title="A concept's path from engine evidence to admission in the A0 manual",
        shows=(
            "Every candidate the engines proposed, the verdict the LLM gave it, and "
            "the point at which it entered the manual. The compiler-defect iterations "
            "are on a subordinate lane because they were not manual revisions: the "
            "manual was revised zero times by certify, and a timeline that showed "
            "three revisions without saying whose they were would overstate the loop."
        ),
        run_refs=(
            RunRef("json_keys", "a0_concept_accounts", "A0 runs accounted for"),
            RunRef("git_commits", "a0_theorize_log", "revisions of the theorize log"),
        ),
        supersedes=("papers/phase1-workshop/figures/fig1_concept_timeline.py",),
    ),
    PaperFigure(
        number=2,
        slug="a0_vs_a0prime",
        pipeline="fig07_a0_vs_a0prime",
        section="3",
        section_title="A0 and A0' -- reversibility beats coverage",
        title="Coverage against accuracy: A0 against A0'",
        shows=(
            "Evidence coverage on x, accuracy on y, with replay (K1, on-trace) and "
            "held-out (K2, off-trace) accuracy plotted as a drop line per run. The "
            "drop line is the finding. A0' saw 46.9% of the state-action pairs A0 saw "
            "and was more accurate -- re-witnessability beating coverage."
        ),
        run_refs=(
            RunRef("json_keys", "a0prime_report", "A0' runs in the prime report", select="run_"),
            RunRef("json_value", "capability_spectrum", "battery version", pointer="battery_version"),
        ),
        supersedes=("papers/phase1-workshop/figures/fig2_coverage_accuracy.py",),
    ),
    PaperFigure(
        number=3,
        slug="a2_repair_loop",
        pipeline="fig05_a2_repair_loop",
        section="5",
        section_title="A2 -- the exhibit, and the loop that repairs it",
        title="The A2 exhibit and the six-beat loop that repairs it",
        shows=(
            "The beat flow M0 -> M5 -> L1 … L6, each beat carrying its status and its "
            "one decisive number, over an account strip of environment actions spent. "
            "At M5 the manual replays the play record at 100%, Lean signs an "
            "axiom-free `unsolvable` theorem, and the world contradicts it -- the "
            "co-occurrence of those three facts is the whole DC22 phenomenon."
        ),
        run_refs=(
            RunRef("json_value", "a2_loop_ledger", "the world this exhibit was built in", pointer="world"),
            RunRef("json_value", "capability_spectrum", "battery version", pointer="battery_version"),
        ),
        supersedes=("papers/phase1-workshop/figures/fig3_loop_ledger.py",),
    ),
    PaperFigure(
        number=4,
        slug="a3_transfer",
        pipeline="fig04_a3_transfer",
        section="6",
        section_title="A3 -- the second level costs one frame, and the free check is blind",
        title="A3 transfer: which meter lines move when the books are carried",
        shows=(
            "The like-for-like level-2 comparison, meter line by meter line, control "
            "arm against transfer arm. The bottom three lines -- compile 1:1, certify "
            "3:3, plan 1:1 -- do not move, and they are drawn for that reason: an "
            "axis that hid them would be measuring something other than transfer."
        ),
        run_refs=(
            RunRef("json_pluck", "a3_bill_table", "arms compared", pointer="arms", field="arm"),
        ),
    ),
    PaperFigure(
        number=5,
        slug="capability_spectrum",
        pipeline="fig03_capability_spectrum",
        section="7",
        section_title="The metrics battery, recomputed over existing trajectories",
        title="The metrics battery: the family x arm capability spectrum",
        shows=(
            "Every battery metric by family against every arm, each cell the arm "
            "median normalised within its row and oriented so that further along the "
            "ramp is always better. The empty cells are the result as much as the "
            "full ones: structural absences are hatched and insufficient data is "
            "outlined, and neither is ever drawn as a zero. The tier column and the "
            "dagger markers are the frozen 2026-07-28 baseline "
            "(`battery/artifacts/gaming_audit.json`, kept unrewritten per "
            "PREREG_V9 §5); the live audit has since demoted every remaining "
            "main-table metric to reference -- the current per-metric tiers and "
            "the frozen-vs-live diff are in "
            "`battery/artifacts_live/gaming_audit.live.json`."
        ),
        run_refs=(
            RunRef("json_value", "capability_spectrum", "battery version", pointer="battery_version"),
            RunRef("json_value", "capability_spectrum", "arms", pointer="provenance.arms"),
            RunRef("json_value", "capability_spectrum", "campaigns", pointer="provenance.campaigns"),
        ),
    ),
    PaperFigure(
        number=6,
        slug="bill_shape",
        pipeline="fig02_bill_shape",
        section="7",
        section_title="The metrics battery, recomputed over existing trajectories",
        title="Bill shape: what each arm's turns cost, and when",
        shows=(
            "Cumulative cost against turn, per run, with the normalised panel the "
            "front-load index reads, the E2 head boundary and E3 convergence "
            "crossings drawn as the constructions that define them, and E4 context "
            "growth against run length. Runs that ended on an API failure are dashed; "
            "runs whose outcome is not on disk are dotted."
        ),
        run_refs=(
            RunRef("discovery", "theoria_run", "theoria-arm run directories"),
            RunRef("discovery", "pilot_rollup", "baseline pilot roll-ups"),
            RunRef("json_value", "capability_spectrum", "battery version", pointer="battery_version"),
        ),
    ),
)

BY_PIPELINE: dict[str, PaperFigure] = {f.pipeline: f for f in PAPER_FIGURES}
BY_NUMBER: dict[int, PaperFigure] = {f.number: f for f in PAPER_FIGURES}

# --- import-time consistency, so a bad edit fails at the build and not at the
# --- gate. Contiguity matters: "Figure 5" with no Figure 4 is a broken document.
if len(BY_PIPELINE) != len(PAPER_FIGURES):
    raise RuntimeError("two paper figures name the same pipeline plate")
if len(BY_NUMBER) != len(PAPER_FIGURES):
    raise RuntimeError("two paper figures claim the same number")
if sorted(BY_NUMBER) != list(range(1, len(PAPER_FIGURES) + 1)):
    raise RuntimeError(
        f"paper figure numbers must be 1..{len(PAPER_FIGURES)} with no gaps; got {sorted(BY_NUMBER)}"
    )
if len({f.slug for f in PAPER_FIGURES}) != len(PAPER_FIGURES):
    raise RuntimeError("two paper figures share a slug; the filenames would collide")


def for_pipeline(name: str) -> PaperFigure | None:
    """The paper figure a pipeline plate becomes, or ``None`` if it is unpublished."""
    return BY_PIPELINE.get(name)


def sources_for(pipeline: str) -> tuple[sources.Source, ...]:
    """Every declared source this plate reads, in path order.

    Read off ``Source.figures``, which the registry already maintains, so a
    caption cannot fall behind the thing it describes.
    """
    return tuple(sorted((s for s in sources.SOURCES if pipeline in s.figures), key=lambda s: s.path))


def status_for(pipeline: str) -> tuple[str, tuple[sources.Source, ...]]:
    """``("complete" | "partial", absent_sources)``.

    ``partial`` is the work order's ``pending``: the plate is drawn and cited,
    and something it declared it would read is not on disk. Derived, because a
    completeness flag that is typed is a completeness flag that will be wrong.
    """
    absent = tuple(s for s in sources_for(pipeline) if not s.exists())
    return ("partial" if absent else "complete"), absent


def _dotted(obj, pointer: str):
    if not pointer:
        return obj
    for part in pointer.split("."):
        if not isinstance(obj, dict) or part not in obj:
            raise KeyError(f"pointer {pointer!r} does not resolve: no {part!r}")
        obj = obj[part]
    return obj


def _stringify(value) -> list[str]:
    if isinstance(value, (list, tuple)):
        return [str(v) for v in value]
    return [str(value)]


def resolve_run_ref(ref: RunRef) -> list[str]:
    """The run ids this reference points at, sorted where order is not meaningful."""
    if ref.kind == "discovery":
        r = sources.rule(ref.target)
        if r.kind == "dir":
            return [entry for entry, _ in sources.discovered_groups(ref.target)]
        return [s.path.rsplit("/", 1)[-1] for s in sources.discovered(ref.target) if s.exists()]
    if ref.kind == "git_commits":
        src = sources.get(ref.target)
        return [f"{row['sha'][:9]} {row['when']}" for row in sources.git_log(src.path)]
    data = sources.read_json(ref.target)
    if ref.kind == "json_keys":
        keys = sorted(_dotted(data, ref.pointer))
        if ref.select:
            keys = [k for k in keys if k.startswith(ref.select)]
            if not keys:
                raise ValueError(
                    f"RunRef select={ref.select!r} on {ref.target!r} matched nothing; "
                    "the artefact's shape changed and the caption would go silent"
                )
        return keys
    if ref.kind == "json_value":
        return _stringify(_dotted(data, ref.pointer))
    if ref.kind == "json_pluck":
        return [str(item[ref.field]) for item in _dotted(data, ref.pointer)]
    raise ValueError(f"unknown RunRef kind {ref.kind!r}")


def run_identity(fig: PaperFigure) -> list[dict]:
    """``[{label, source, ids}]`` for one figure. Empty list is a legal answer.

    An empty answer is not a hole to paper over -- most of
    ``cold-start-a2/artifacts/`` and all of ``cold-start-a3/artifacts/`` publish
    no run identifier at all. The caption states that, and pins the run by file
    digest and base commit instead.
    """
    out = []
    for ref in fig.run_refs:
        out.append(
            {
                "label": ref.label,
                "kind": ref.kind,
                "source": (
                    f"rule {ref.target!r}"
                    if ref.kind == "discovery"
                    else sources.get(ref.target).path
                ),
                "ids": resolve_run_ref(ref),
            }
        )
    return out
