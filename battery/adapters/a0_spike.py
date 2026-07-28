"""Adapter for the a0-spike bundle (`a0-spike/`, read-only).

a0-spike is the engine-rig track's cold start: a self-built sokoban-2 world
mined into a manual, compiled to Lean and PDDL, replayed, held-out tested, and
then — the part nothing else in this repository has — **deliberately broken
four times to see whether the manual notices**.  `artifacts/adaptation.json`
is the only 打脸→修复 record in the repository that was produced rather than
narrated, so this adapter exists mainly to feed the repair family.

What it can and cannot answer, stated up front because most of it is `None`:

* **There is no persisted trace.**  a0-spike writes no `raw_trace.jsonl` and no
  frames; its 1966-action exploration exists only as regenerable in-memory data
  inside `pipeline/explore.py`.  Executing another track's pipeline is not what
  a passive instrument does — and that pipeline imports `engine-rig` and
  `theory-compiler` at module load — so this adapter reads artefacts only and
  the run carries `steps=[]`.  `capabilities()["steps"]` is therefore False and
  the whole exploration family, plus P1/P2/P3, reports `not-applicable`.  That
  is the correct answer for a source that published no trace, not a gap.
* **There are no model calls.**  Like `cold-start-a0`, the spike was engines
  and hand adjudication end to end; nothing in `a0-spike/` touches an LLM API.
  The economy family reports `not-applicable`.
* **There are no probes.**  No `engines_report.json`, no `probes` array
  anywhere in the bundle.  The `probe: passed` string on the theorem is an
  adjudication annotation, not a probe record, and inventing a count of 1 from
  it would be manufacturing the exact number K8 is supposed to measure.

Three reconstructions this adapter has to justify rather than read:

* **The concept compression accounts are refused.**  See `_concepts` — the two
  word-table entries carry one *global* number, twice, with the wrong sign and
  stale by five levels.  Both concepts get `compression_bits=None`, so K6/K7
  come out `insufficient-data` on this arm.
* **The revision count is refused.**  See `_REVISION_NOTE` — the manual carries
  no `revision N` marker, and `parse_dsl`'s default of 1 would be
  indistinguishable from the marker `a0-no-button` actually writes.
* **The detection record is a union type.**  `detection` has a different shape
  depending on whether the injected change was noticed at all; `_repair` is
  written around that rather than around the common case.

The DSL reader (`parse_dsl`) and the playbook reader (`parse_playbook`) are
imported from `battery.adapters.a0` rather than reimplemented: both bundles
write the same grammar, and two copies of a shallow parser would drift apart
exactly when the grammar moved.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from battery.adapters.a0 import _read_json, parse_dsl, parse_playbook
from battery.guard import Piles, load_piles
from battery.model import Clause, Concept, Repair, Run, Theory, Truth

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
A0_SPIKE_ROOT = os.path.join(REPO, "a0-spike")

# The word table's two entries, in the order the manual names them.  a0-spike
# publishes no `concept_accounts.json`, so unlike `cold-start-a0` there is no
# per-concept ledger to read; these are the names and nothing else.
_WORD_TABLE = ("Box", "Player")

# --------------------------------------------------------------------------
# Why `compression_bits` is None on both concepts.
#
# `theory/theory.dsl` annotates BOTH entries with `compress: -39`:
#
#     Player [segment: color-split-connected ev: t0-t340 compress: -39]
#     Box    [segment: color-split-connected ev: t0-t340 compress: -39]
#
# Three independent reasons not to pass that through:
#
# 1. **It is one global number written twice, not two accounts.**  -39 is
#    exactly 373 - 412, the whole-edit-script cost against the whole per-pixel
#    baseline quoted in `README.md` and `THEORIZE_LOG.md` T-1.  Neither
#    concept was ever costed on its own, so a per-concept mean over the pair
#    is a mean over one measurement duplicated -- K6 would report a spuriously
#    tight number with n=2.
# 2. **The sign convention is inverted.**  `Concept.compression_bits` is
#    positive when the manual got *shorter*.  373 against 412 is a 39-bit
#    *win*, so passing -39 through would make K7 count two concepts as
#    admitted-despite-negative-compression when in fact both paid for
#    themselves.  That is the O-04 finding, fabricated.
# 3. **It is stale.**  The number describes the original single-level, 341-
#    transition evidence.  `a0_report.json -> perceive` measures the final
#    five-level bundle at `script_bits: 602` against `baseline_bits: 712`, a
#    delta of -110 (ratio 0.8455).  The manual and the report disagree, and
#    the manual is the older of the two.
#
# Negating it would fix (2) and leave (1) and (3); recomputing it from
# `perceive` would fix (3) and leave (1), since 602/712 is still one global
# pair with no way to split it between Player and Box.  So the honest output
# is no number at all: K6 and K7 report `insufficient-data` with a stated
# reason, which is a fact about a0-spike's bookkeeping and not a score.
# --------------------------------------------------------------------------
_COMPRESSION_NOTE = (
    "refused: theory.dsl annotates both Player and Box with the same "
    "`compress: -39`, which is the whole-script delta 373-412 quoted in "
    "README/THEORIZE_LOG T-1 -- one global number written twice, with the "
    "sign inverted relative to Concept.compression_bits, and stale against "
    "a0_report.json perceive (script_bits 602 vs baseline_bits 712, delta "
    "-110). There is no concept_accounts.json to split it. K6/K7 report "
    "insufficient-data rather than a fabricated per-concept account."
)

# --------------------------------------------------------------------------
# Why `revisions` is 0.
#
# `theory/theory.dsl` carries no `revision N` marker, so `parse_dsl` falls back
# to its documented default of 1.  Reporting that would be worse than useless
# here: `cold-start-a0/theory/theory_no_button.dsl` writes a genuine
# `revision 1`, so the two arms would land on the same K11 with completely
# different provenance -- one authored, one invented by a default.
#
# The real count is not 1.  `THEORIZE_LOG.md` records four adjudications that
# changed what the manual says (T-4 `push2` rejected on the first pass and
# accepted on the second; T-6 the engine's stronger conservation pair replacing
# the proposed sum; T-8 certify's replay failure forcing `stayed(o)` into the
# event vocabulary and rewriting both blocked rules; T-9 held-out testing
# forcing a missing literal into `push2`).  Two of those -- T-8 and T-9 -- are
# revisions of an already-written manual forced by a checking layer, which is
# precisely the loop K11's docstring says A0 never exercised.
#
# But that count lives in prose.  Laundering a hand-read number out of a
# Markdown narrative into a scored field is the kind of thing this battery
# exists to not do, so `revisions=0` reports what the artefacts actually carry:
# no revision marker.  0 is outside the range an author can write (markers
# start at 1), so it cannot be confused with a declared value.  Under K11's own
# docstring a low count "ranks nothing"; the log entries go into `Run.notes`
# so a reader can see the true count is at least 4 and that K11 is
# uninformative on this arm rather than flattering it.
# --------------------------------------------------------------------------
_REVISION_NOTE = (
    "0 means `no revision marker in any artefact`, not `never revised`. "
    "theory.dsl carries no `revision N` header, so parse_dsl's default of 1 "
    "would be indistinguishable from the marker cold-start-a0's no-button "
    "manual genuinely writes. THEORIZE_LOG.md records four adjudications that "
    "changed the manual (T-4, T-6, T-8, T-9), two of them (T-8 certify, T-9 "
    "held-out) revisions of an already-written manual forced by a checking "
    "layer -- but that count is prose, not an artefact, so it stays in notes "
    "and out of K11."
)

_HELD_OUT_FRAME = (
    "exhaustive enumeration: every well-formed (state, direction) pair on all "
    "5 evidence levels (39960 cases), most of them unreachable from the start "
    "state. NOT a withheld sample, and not comparable with cold-start-a0's "
    "held-out denominator of 3 adversarially chosen uncovered pairs."
)


def _concepts() -> List[Concept]:
    """The word table, with its compression accounts deliberately withheld.

    `first_seen_step` is `None` because there is no persisted trace to find a
    first appearance in, and `admitted_revision` is `None` because there is no
    revision axis to place them on (see `_REVISION_NOTE`).  `load_bearing` is
    True for both on the report's own evidence: `perceive` records
    `movers: 2` against `board: 4` static tracks, and these two names are the
    movers -- every mined rule's guard and effect is about one of them.
    """
    return [Concept(name=name,
                    first_seen_step=None,
                    admitted_revision=None,
                    compression_bits=None,
                    load_bearing=True)
            for name in sorted(_WORD_TABLE)]


def _repair(entry: Dict[str, Any], baseline_actions: Optional[int],
            theorems_before: int) -> Repair:
    """One injected-variant episode.

    **`detection` is a union type.**  When the injected change was noticed the
    record carries `actions_until_surprise`, `episode`, `action`, `predicted`
    and `observed`; when it was not (the `nocross` variant) every one of those
    is absent and the field is `actions_examined` instead.  Reading
    `detection["actions_until_surprise"]` unconditionally raises `KeyError` on
    one variant in four, so the two shapes are mapped to two different fields:
    `detection_actions` when detected, `actions_examined` when not.  `Repair`'s
    own docstring calls the second case the interesting one -- a manual that
    replayed perfectly while being silently wrong.

    **`beats` is left empty, on purpose.**  a0-spike detects and then re-mines
    the world from fresh evidence; it does not run the six-beat loop
    打脸→定位→戳探→修订→重证→解出, and no ledger in the bundle records beats.
    Fabricating them to lift `beats_closed` off 0/6 would turn the one metric
    that asks whether the loop closed into a metric that asks whether the
    adapter was willing to say it did.  0 out of 6 is a true statement about
    a0-spike: it demonstrates detection and repair, not the certified loop.

    **`strategy` is `rebuild`.**  The repair re-mines every rule from a fresh
    evidence sweep rather than patching the culprit clause, which is the
    contrast against A2's `patch` that `battery/PREDICTIONS.md` registers as a
    confound.  A patch costing a fifth of a rebuild is not an arm ranking.
    """
    detection = entry.get("detection") or {}
    detected = bool(detection.get("detected"))
    across = entry.get("detection_across_levels") or {}
    repair = entry.get("repair") or {}
    invalidated = entry.get("invalidated_theorems") or []

    # `per_level` holds `null` for a level that never noticed (nocross/match),
    # so any min()/sum() over `.values()` raises TypeError.  The report already
    # publishes the aggregate as `earliest` and `levels_that_never_notice`;
    # those are carried verbatim and the raw map is kept only as a sorted,
    # None-preserving record for a reader.
    per_level = {k: across.get("per_level", {}).get(k)
                 for k in sorted(across.get("per_level") or {})}

    return Repair(
        episode_id=str(entry.get("variant", "?")),
        trigger=str(entry.get("description", "")),
        strategy="rebuild",
        changed_clause=entry.get("changed_rule"),
        detected=detected,
        detection_actions=(detection.get("actions_until_surprise")
                           if detected else None),
        actions_examined=(None if detected
                          else detection.get("actions_examined")),
        beats=[],
        beats_required=6,
        repair_actions=repair.get("evidence_actions"),
        baseline_actions=baseline_actions,
        invalidated_theorems=len(invalidated),
        theorems_before=theorems_before,
        silently_wrong_without_tracking=bool(
            entry.get("silently_wrong_without_dependency_tracking")),
        notes={
            "beats": "a0-spike runs no six-beat loop ledger -- it detects and "
                     "re-mines. beats_closed is 0 of 6 because the certified "
                     "loop was not run, not because it failed.",
            "collateral_ceiling": "the manual holds %d theorem(s), so the "
                                  "invalidated share can only ever be 0.0 or "
                                  "1.0 -- a very coarse measure on this "
                                  "fixture." % theorems_before,
            "conservation_law_still_true":
                entry.get("conservation_law_still_true"),
            "detected_anywhere": across.get("detected_anywhere"),
            "earliest_detection": across.get("earliest"),
            "invalidated_theorem_names": sorted(invalidated),
            "levels_that_never_notice": sorted(
                across.get("levels_that_never_notice") or []),
            "mismatch_still_unsolvable": entry.get("mismatch_still_unsolvable"),
            "old_verdict_still_correct": entry.get("old_verdict_still_correct"),
            "per_level_detection": per_level,
            "repaired_n_rules": repair.get("n_rules"),
            "repaired_replay_exact": repair.get("replay_exact"),
        },
    )


def _theory(root: str, report: Dict[str, Any]) -> Theory:
    clauses: List[Clause]
    clauses, _default_revision = parse_dsl(
        os.path.join(root, "theory", "theory.dsl"))
    # There is no `theory/playbook.dsl` in this bundle; the reader returns
    # (0, 0) for a missing file, and asking it anyway keeps the two adapters
    # structurally identical if one is ever written.
    playbook_entries, playbook_deadlocks = parse_playbook(
        os.path.join(root, "theory", "playbook.dsl"))

    certify = report.get("certify") or {}
    held_out = report.get("held_out") or {}
    transitions = certify.get("transitions")
    total_cases = held_out.get("total_cases")
    mismatches = held_out.get("total_mismatches")

    return Theory(
        concepts=_concepts(),
        clauses=clauses,
        playbook_entries=playbook_entries,
        deadlock_theorems=playbook_deadlocks + sum(
            1 for c in clauses
            if c.kind == "theorem" and "unsolvable" in c.name),
        revisions=0,                 # see _REVISION_NOTE
        probes_designed=0,           # no engines_report.json, no probes array
        probes_executable=0,
        # `certify` replays the whole 1966-transition evidence sweep through
        # the manual's executable form; `replay_exact` being a single boolean
        # rather than a per-pair count means agreement is all-or-nothing.
        replay_pairs=transitions,
        replay_agree=(transitions if certify.get("replay_exact") else None),
        held_out_pairs=total_cases,
        held_out_agree=(total_cases - mismatches
                        if total_cases is not None and mismatches is not None
                        else None),
        held_out_frame=_HELD_OUT_FRAME,
    )


def load_a0_spike_runs(root: str = A0_SPIKE_ROOT, *,
                       piles: Optional[Piles] = None) -> List[Run]:
    """The single a0-spike run, or `[]` if the bundle is not present.

    One run, not five: the five evidence levels are one exploration budget
    spent by one arm building one manual, and splitting them would multiply a
    single theory across five rows.
    """
    piles = piles or load_piles()
    artifacts = os.path.join(root, "artifacts")
    report = _read_json(os.path.join(artifacts, "a0_report.json"))
    if not report:
        return []
    adaptation = _read_json(os.path.join(artifacts, "adaptation.json")) or {}

    theory = _theory(root, report)
    theorems = sum(1 for c in theory.clauses if c.kind == "theorem")
    explore = report.get("explore") or {}
    baseline_actions = explore.get("actions_spent")

    repairs = [_repair(entry, baseline_actions, theorems)
               for entry in sorted(adaptation.get("variants") or [],
                                   key=lambda e: str(e.get("variant", "")))]

    # `truth.levels` is 2, the levels the arm was *graded* on (`match`, which
    # it planned, and `mismatch`, which it proved unsolvable) -- the same set
    # `optimal_steps` is read from, so the two fields describe one thing.  The
    # five `explore.levels` are evidence-gathering levels, not graded ones;
    # they go into `Run.notes` so the choice is visible rather than implied.
    levels = report.get("levels") or {}
    match = levels.get("match") or {}
    truth = Truth(
        optimal_steps=match.get("plan_length"),
        # a0-spike annotates no mechanism with a first-seen/first-used step
        # anywhere.  The nearest thing, `mine.rules[*].support`, indexes a
        # pooled multi-level transition list that was never persisted and is
        # not on the same axis as cold-start-a0's per-frame indices, so the
        # mechanism family reports not-applicable.  That is honest; an
        # annotation table invented here would not be.
        mechanisms={},
        levels=len(levels) or None,
    )

    return [Run(
        run_id="a0-spike",
        arm="theoria_a0_spike",
        source="a0-spike",
        # 1966 actions of deliberate coverage against a 2-step optimal plan is
        # 983x, which measures the sweep's purpose and not the arm's planning.
        # Declaring `explore` is what makes P4 refuse it.
        intent="explore",
        model=None,
        game_id=None,                # a self-built world belongs to no pile
        pile=piles.assert_playable(None),
        steps=[],                    # see the module docstring: no trace exists
        calls=[],                    # no LLM anywhere in the bundle
        theory=theory,
        truth=truth,
        repairs=repairs,
        notes={
            "compression_accounts": _COMPRESSION_NOTE,
            "evidence_levels": sorted(explore.get("levels") or []),
            "explore_actions_spent": baseline_actions,
            "explore_episodes": explore.get("episodes"),
            "levels_counted": "truth.levels counts the 2 graded levels "
                              "(match, mismatch); the 5 in evidence_levels "
                              "are the exploration levels the manual was "
                              "mined from.",
            "perceive_script_bits": (report.get("perceive") or {})
                                    .get("script_bits"),
            "perceive_baseline_bits": (report.get("perceive") or {})
                                      .get("baseline_bits"),
            "revisions": _REVISION_NOTE,
            "trace_persistence": "none. a0-spike persists no raw_trace.jsonl "
                                 "and no frames; the 1966-action trace exists "
                                 "only as regenerable in-memory data in "
                                 "pipeline/explore.py, which the battery "
                                 "deliberately does not execute -- it is "
                                 "another track's pipeline and imports "
                                 "engine-rig and theory-compiler at load "
                                 "time. steps=[] follows, and with it "
                                 "not-applicable across the exploration "
                                 "family and P1/P2/P3.",
        },
    )]


__all__ = ["load_a0_spike_runs", "A0_SPIKE_ROOT"]
