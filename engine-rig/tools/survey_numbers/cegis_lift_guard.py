"""E18 — recompute `cegis.lifted_tautological` (104/149) and its companions.

The E11 cross-check
(`runs/20260729T000000Z-E11-engine-crosscheck-deep/`) published five ratios as
prose.  Nothing in that run directory computes them: eight `.md` files and a
`MANIFEST.json`, no script, no data.  This module is the executable form of the
`cegis_miner` half of that table.

**The count, not the mechanism.**  The mechanism half of the `104/149` claim —
`lift` substitutes `?dir` into a template guard and never re-verifies, and the
engine's evaluator does a plain `action == arg` so `act==?dir` is always false —
was confirmed on the source by the adversarial reviewer
(`ADVERSARIAL-cegis.md` §3) and is not re-litigated here.  What nobody could
reproduce was the *count*.  That is what this module produces.

## Two calibers, because the mining path changed under the number

Every ratio here is a ratio over a corpus, and the corpus is "what
`fuzzlab/props/cegis_miner.py::_mine` mines out of `gridworld` seeds 1–200".
**That function changed after E11 measured.**  V-13 (`eb61aa98`) added
`_mover_track`, so `_mine` now picks the world's mover instead of taking
`transitions_from_segmentation`'s `seg.tracks[0]` default — which is the very
defect E11 filed as F-1.  Mining a different object gives different rules, so it
gives different ratios.

Reporting only the E11-era numbers would leave 104/149 describing a path the
engine no longer takes.  Reporting only today's would not be a recomputation of
the published claim.  So every count below is emitted **twice**:

* `e11_caliber` — `props._mine` as it stood at `ed592a6`: no `track=`, so
  `seg.tracks[0]`.  The caliber the prose was measured at, and the only one the
  prose may be compared against.
* `today_caliber` — today's `fuzzlab.props.cegis_miner._mine`, called directly,
  not reimplemented.  What a reader running the engine today will get.

Which to quote is in `CAVEATS[0]`.  The short version: quote the E11 caliber
when citing the 2026-07-29 finding, quote today's when saying what the engine
does now, and never quote one as the other.

## What is recomputed

| count key | prose | registry key it re-points |
|---|---|---|
| `cegis.lifted_tautological` | 104 / 149 | same |
| `cegis.applicable_not_derivable` | 131 / 149 | same |
| `ground.applicable_equals_support` | 932 / 932 | — (unregistered) |
| `cegis.track0_worlds` | 72 | same |
| `cegis.track0_motionless` | 72 / 72 | same |
| `cegis.track0_rows` | 1209 | same |
| `cegis.frontier_missing_within` | 0 | same |
| `cegis.worlds` / `.transitions` / `.ground` / `.lifted` | 193 / 4277 / 932 / 149 | same |

Run it:

    cd engine-rig
    python -m tools.survey_numbers.cegis_lift_guard
    python -m tools.survey_numbers.cegis_lift_guard --jsonl <path>
"""

from __future__ import annotations

import argparse
import itertools
import json
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from tools.survey_numbers import _common

_common.add_repo_root()

from engines import cegis_miner as engine           # noqa: E402
from engines import mdl_segmenter                   # noqa: E402
from engines.cegis_miner import atoms as atom_mod   # noqa: E402
from fuzzlab.props import cegis_miner as props      # noqa: E402
from fuzzlab.worlds import gridworld                # noqa: E402

# The partial pins every number to `gridworld.generate(seed)` for these seeds.
SEEDS = tuple(range(1, 201))

#: The two mining paths.  Order is fixed so the JSON is byte-stable.
CALIBERS = ("e11_caliber", "today_caliber")

CALIBER_DESCRIPTION = {
    "e11_caliber": "fuzzlab/props/cegis_miner.py::_mine as at ed592a6 -- no "
                   "track= argument, so transitions_from_segmentation mines "
                   "seg.tracks[0]. The caliber the E11 prose was measured at.",
    "today_caliber": "fuzzlab.props.cegis_miner._mine as of this commit, called "
                     "directly -- V-13 (eb61aa98) added _mover_track, so it "
                     "mines the world's mover. What the engine does now.",
}

#: The direction variable `lift` substitutes.  `miner.DIR_VAR`, restated so the
#: predicate this module counts is visible in this file rather than one import
#: away.
DIR_VAR = "?dir"

#: The predicate `cegis.lifted_tautological` counts: the published guard list is
#: exactly this.  `Rule.as_json()["guard"]` is `sorted(atom.name ...)`, so a
#: one-element list compares literally.
LIFT_GUARD = ["act==?dir"]

INPUTS = [
    "engine-rig/engines/cegis_miner/__init__.py",
    "engine-rig/engines/cegis_miner/atoms.py",
    "engine-rig/engines/cegis_miner/miner.py",
    "engine-rig/engines/mdl_segmenter/__init__.py",
    "engine-rig/engines/mdl_segmenter/segmenter.py",
    "engine-rig/runs/20260729T000000Z-E11-engine-crosscheck-deep/ADVERSARIAL-cegis.md",
    "engine-rig/runs/20260729T000000Z-E11-engine-crosscheck-deep/CROSSCHECK.md",
    "engine-rig/runs/20260729T000000Z-E11-engine-crosscheck-deep/partials/"
    "cegis_miner-via-bruteforce.md",
    "fuzzlab/oracles/motion.py",
    "fuzzlab/props/cegis_miner.py",
    "fuzzlab/worlds/common.py",
    "fuzzlab/worlds/gridworld.py",
]


# --------------------------------------------------------------- the corpus

def _e11_mine(world: Any):
    """`fuzzlab/props/cegis_miner.py::_mine` **as it stood at `ed592a6`**.

    Reproduced rather than imported, because the function it reproduces no
    longer exists: today's `_mine` calls `_mover_track` and passes `track=`.
    That is not a detail, it is F-1 being fixed, and it re-cuts the corpus.
    Keeping the old path executable is what makes the published 104/149
    checkable at all; `_today_mine` beside it is what keeps it from being the
    only thing on offer.

    Returns `(result, transitions, tracks0, mined_track, split)`, or `None`
    when neither operator narrates the world as move/none.
    """
    background = world.spec_json().get("background", 0)
    for split in (False, True):
        seg = mdl_segmenter.segment_trajectory(
            world.frames, background=background, split_by_color=split)
        try:
            transitions = engine.transitions_from_segmentation(
                world.frames, world.action_list, seg, background=background)
        except ValueError:
            continue
        # No `track=` was passed, so the mined track *is* `tracks[0]`.
        return (engine.mine(transitions), transitions,
                seg.tracks[0], seg.tracks[0], split)
    return None


def _today_mine(world: Any):
    """Today's `fuzzlab.props.cegis_miner._mine`, called, not reimplemented.

    `_mine` does not hand back the track it chose, so it is recovered the only
    way that cannot drift from the original: re-segment with the operator
    `_mine` reported, and ask **the same `_mover_track`** which track that is.
    `None` is `_mine`'s own documented "keep `tracks[0]`" answer, so the
    fallback here is the fallback there.
    """
    try:
        result, transitions, split = props._mine(world)
    except props.Unminable:
        return None
    background = world.spec_json().get("background", 0)
    seg = mdl_segmenter.segment_trajectory(
        world.frames, background=background, split_by_color=split)
    chosen = props._mover_track(world, seg)
    mined = seg.tracks[0] if chosen is None else chosen
    return result, transitions, seg.tracks[0], mined, split


_MINERS = {"e11_caliber": _e11_mine, "today_caliber": _today_mine}
_CORPUS: Dict[str, List[Dict[str, Any]]] = {}


def corpus(caliber: str) -> List[Dict[str, Any]]:
    """One entry per seed, ascending.  Memoised; pure in `(caliber, seed)`."""
    if caliber in _CORPUS:
        return _CORPUS[caliber]
    mine = _MINERS[caliber]
    out: List[Dict[str, Any]] = []
    for seed in SEEDS:
        world = gridworld.generate(seed)
        mined = mine(world)
        if mined is None:
            out.append({"seed": seed, "minable": False})
            continue
        result, transitions, tracks0, mined_track, split = mined
        out.append({
            "seed": seed,
            "minable": True,
            "world": world,
            "result": result,
            "transitions": transitions,
            "tracks0": tracks0,
            "mined_track": mined_track,
            "split_by_color": split,
        })
    _CORPUS[caliber] = out
    return out


def _judged(caliber: str) -> List[Dict[str, Any]]:
    return [e for e in corpus(caliber) if e["minable"]]


# ------------------------------------------------------- guard evaluation

def _fires_engine(guard: Sequence[Any], transitions: Sequence[Any]) -> Optional[Set[int]]:
    """Firing set under the engine's own evaluator.  `None` if it refuses.

    This is `atoms.evaluate` unmodified, which is the only evaluator any code in
    the repository has.  On a lifted guard it either returns the empty set
    (`act==?dir` is `action == "?dir"`, false for every compass action) or
    raises (`strip_cells("?dir")` -> `ValueError`).  `None` records the raise;
    collapsing it into `set()` would report "the guard fires nowhere" where the
    truth is "the guard cannot be read".
    """
    fires: Set[int] = set()
    for t in transitions:
        try:
            if all(atom_mod.evaluate(a, t.state, t.action) for a in guard):
                fires.add(t.index)
        except ValueError:
            return None
    return fires


def _fires_bound(guard: Sequence[Any], transitions: Sequence[Any]) -> Set[int]:
    """Firing set with `?dir` bound to each row's own action.

    The partial's §3: "Lifted guards are evaluated with `?dir` bound to that
    row's action -- the only reading under which `act==?dir` is not
    meaningless."  No code in the repository does this binding; the adjudicating
    LLM reading `candidates.jsonl` is the only consumer that can.
    """
    fires: Set[int] = set()
    for t in transitions:
        bound = [
            atom_mod.Atom(a.kind, t.action, a.negated)
            if (a.kind != "at" and a.arg == DIR_VAR) else a
            for a in guard
        ]
        if all(atom_mod.evaluate(a, t.state, t.action) for a in bound):
            fires.add(t.index)
    return fires


# --------------------------------------------------------------- the rows

def lifted_rows(caliber: str) -> List[Dict[str, Any]]:
    """One raw row per lifted rule at this caliber, sorted by `rule_id`.

    `derivable_from_guard` is the **generous** reading: True when the published
    `applicable` set is reproduced by evaluating the published guard under
    *either* the engine's evaluator or the `?dir`-bound one.  So its negation is
    reading-independent, which is what `ADVERSARIAL-cegis.md:224` claims of the
    131.  The two readings are kept separately beside it.
    """
    rows: List[Dict[str, Any]] = []
    for entry in _judged(caliber):
        transitions = entry["transitions"]
        for index, rule in enumerate(entry["result"].lifted):
            guard_names = rule.guard_names()
            applicable = sorted(rule.applicable)
            support = sorted(rule.support)
            engine_fires = _fires_engine(rule.guard, transitions)
            bound_fires = _fires_bound(rule.guard, transitions)
            derivable_engine = (engine_fires is not None
                                and engine_fires == set(applicable))
            derivable_bound = bound_fires == set(applicable)
            rows.append({
                "rule_id": "%s:gridworld:seed=%03d:lifted[%d]:%s"
                           % (caliber, entry["seed"], index, rule.name),
                "caliber": caliber,
                "seed": entry["seed"],
                "name": rule.name,
                "guard": guard_names,
                "has_act_eq_dir": guard_names == LIFT_GUARD,
                "guard_contains_act_eq_dir": any(
                    n in ("act==?dir", "!act==?dir") for n in guard_names),
                "applicable": len(applicable),
                "support": len(support),
                "derivable_from_guard": derivable_engine or derivable_bound,
                "derivable_engine_reading": derivable_engine,
                "derivable_bound_reading": derivable_bound,
                "engine_reading_unevaluable": engine_fires is None,
                "lifted_from": list(rule.lifted_from),
            })
    return sorted(rows, key=lambda r: r["rule_id"])


def _ground_applicable_equals_support(caliber: str) -> Tuple[int, int]:
    """P1's surviving half: ground rules whose `applicable` is their `support`."""
    ok = total = 0
    for entry in _judged(caliber):
        for rule in entry["result"].rules:
            total += 1
            if set(rule.applicable) == set(rule.support):
                ok += 1
    return ok, total


def _true_mover_masks(world: Any) -> List[Tuple[Tuple[int, int], ...]]:
    """The mover's cell set per frame, straight from the generator.

    `Rules.step` returns `(next_anchor, label)` in one call and `generate`
    renders the frames from those anchors, so this is the frames' *upstream*,
    not a re-derivation from pixels.  Nothing the segmenter or the miner
    computed is consulted.
    """
    return [tuple(sorted(world.rules.mover_cells(anchor)))
            for anchor in world.anchors]


def _track0_not_mover(caliber: str) -> Dict[str, int]:
    """`cegis.track0_worlds`: worlds where `seg.tracks[0]` is not the mover.

    This is the registry's own predicate, verbatim from the string it probes
    (`ADVERSARIAL-cegis.md`, "track0 NOT mover"), and it is **not** the
    predicate behind `cegis.track0_motionless`'s denominator -- that one is
    "the rule set is all-`none` and the mover moved".  The two coincided at 72
    in the E11 corpus, which is exactly why they need separating: a registry
    entry re-pointed at a number that merely matches is the E18 defect one level
    down.
    """
    judged = _judged(caliber)
    not_mover = 0
    for entry in judged:
        truth = _true_mover_masks(entry["world"])
        track = entry["tracks0"]
        is_mover = all(
            track.mask_at(t) is not None
            and tuple(sorted(track.mask_at(t))) == truth[t]
            for t in range(len(truth))
        )
        if not is_mover:
            not_mover += 1
    return {"not_mover": not_mover, "judged": len(judged)}


def _f1_worlds(caliber: str) -> Dict[str, int]:
    """The worlds F-1 is about, and what the retracted 1209 counted.

    An F-1 world is one whose whole mined rule set has `effect: none` **and**
    whose mover moved at least once.  "Static rock" is then checked against the
    segmenter's own per-frame masks for the **mined** track: the object the
    miner described occupies an identical cell set in every frame, so
    `effect: none` is a true statement about *it*.

    1209 is counted two independent ways -- the generator's non-`noop` event
    labels, and whole-frame inequality -- because the adversarial review's whole
    point (§1.4, §6.2) was that those two are the *same* measurement wearing two
    hats.  Reproducing the equality is reproducing that criticism, not
    corroborating the headline.
    """
    worlds = static = 0
    transitions_in_f1 = 0
    events_non_noop = events_move_only = frame_changes = 0
    for entry in _judged(caliber):
        world, result = entry["world"], entry["result"]
        if not result.rules:
            continue
        if any(rule.effect.type != "none" for rule in result.rules):
            continue
        if world.moved() == 0:
            continue
        worlds += 1
        track = entry["mined_track"]
        masks = [track.mask_at(t) for t in range(len(world.frames))]
        if masks and all(m is not None and m == masks[0] for m in masks):
            static += 1
        for t in entry["transitions"]:
            transitions_in_f1 += 1
            label = world.events[t.index]
            if label != "noop":
                events_non_noop += 1
            if label.startswith("move:"):
                events_move_only += 1
            if world.frames[t.index] != world.frames[t.index + 1]:
                frame_changes += 1
    return {
        "worlds": worlds,
        "static": static,
        "transitions": transitions_in_f1,
        "events_non_noop": events_non_noop,
        "events_move_only": events_move_only,
        "frame_changes": frame_changes,
    }


def _frontier_omissions(caliber: str) -> Dict[str, int]:
    """P3: minimal guards missing from a frontier, within its own bound.

    Brute force over the **full** vocabulary, with masks rebuilt from
    `atoms.evaluate` rather than taken from `atom_masks`, so the sweep does not
    inherit the mask bookkeeping it is checking.

    One pruning step, and it is a theorem rather than a heuristic: a guard fires
    exactly on `support` only if every one of its literals is true on every
    positive, because conjunction only removes rows.  So literals that miss a
    positive can be dropped before enumerating, and no minimal guard is lost.
    Strict supersets of an already-found minimal guard are dropped for the same
    reason the engine drops them -- they are not minimal-by-inclusion.

    Scope is wider than E11's, which swept depth 3 on Fixture A + 25 worlds and
    depth 2 on 60.  This sweeps **every** judged world at **every** rule's own
    `frontier_max_size`, at both calibers, which is what P3 quantifies over.
    Guards deeper than a rule's own bound are P4's business (F-3) and are out of
    scope here, as they were there.
    """
    rules_swept = rules_skipped_truncated = omissions = 0
    for entry in _judged(caliber):
        transitions = entry["transitions"]
        vocabulary = atom_mod.build_vocabulary([t.state for t in transitions])
        masks: List[int] = []
        for atom in vocabulary:
            mask = 0
            for i, t in enumerate(transitions):
                if atom_mod.evaluate(atom, t.state, t.action):
                    mask |= 1 << i
            masks.append(mask)
        names = [atom.name for atom in vocabulary]

        for rule in entry["result"].rules:
            if rule.frontier_truncated or not rule.frontier:
                rules_skipped_truncated += 1
                continue
            rules_swept += 1
            size = rule.frontier_max_size
            support = set(rule.support)
            positives = 0
            for i, t in enumerate(transitions):
                if t.index in support:
                    positives |= 1 << i
            have = {frozenset(a.name for a in g) for g in rule.frontier}

            covering = [i for i in range(len(vocabulary))
                        if masks[i] & positives == positives]
            found: List[frozenset] = []
            singles: Set[str] = set()
            for i in covering:
                if masks[i] == positives:
                    found.append(frozenset((names[i],)))
                    singles.add(names[i])
            if size >= 2:
                for a, b in itertools.combinations(covering, 2):
                    if names[a] in singles or names[b] in singles:
                        continue
                    if masks[a] & masks[b] == positives:
                        found.append(frozenset((names[a], names[b])))
            if size >= 3:
                smaller = list(found)
                for a, b, c in itertools.combinations(covering, 3):
                    combo = frozenset((names[a], names[b], names[c]))
                    if any(s < combo for s in smaller):
                        continue
                    if masks[a] & masks[b] & masks[c] == positives:
                        found.append(combo)
            omissions += sum(1 for g in found if g not in have)
    return {
        "rules_swept": rules_swept,
        "rules_skipped_truncated": rules_skipped_truncated,
        "omissions": omissions,
    }


# --------------------------------------------------------------- assembly

def _ratio(numerator: int, denominator: int) -> Dict[str, Any]:
    return {
        "numerator": numerator,
        "denominator": denominator,
        "pct": round(100.0 * numerator / denominator, 2) if denominator else None,
    }


def _row(e11: Any, today: Any, prose: Any, registry_key: Optional[str] = None,
         **extra: Any) -> Dict[str, Any]:
    """One table row, at both calibers.

    `agrees` compares the **E11 caliber** against the prose, because that is the
    only comparison that means anything: the prose was measured before the
    mining path changed.  `calibers_agree` is the other question -- False means
    the V-13 repair moved this number, which is a finding in its own right.

    `registry_key` is the `ENGINE_TABLE.md` key this row re-points; `None` means
    the number is real but the registry does not publish it.
    """
    return dict(
        {
            "e11_caliber": e11,
            "today_caliber": today,
            "e11_prose": prose,
            "agrees": e11 == prose,
            "calibers_agree": e11 == today,
            "registry_key": registry_key,
        },
        **extra,
    )


CAVEATS = [
    "TWO CALIBERS, AND WHICH ONE TO QUOTE. The corpus is whatever "
    "`fuzzlab/props/cegis_miner.py::_mine` mines, and that function changed "
    "after E11 measured: V-13 (`eb61aa98`) added `_mover_track`, so `_mine` now "
    "selects the world's mover instead of taking "
    "`transitions_from_segmentation`'s `seg.tracks[0]` default -- the fix for "
    "the very defect (F-1) E11 filed. Every count is therefore emitted at both "
    "calibers. **Quote `e11_caliber` when citing the 2026-07-29 cross-check, "
    "quote `today_caliber` when stating what the engine does now, and never "
    "quote one as the other.** `value` and `agrees_with_e11` are the E11 "
    "caliber, so the comparison against the prose stays like-for-like; the "
    "top-level `today_caliber` block is the same question asked of today's "
    "path.",

    "THE CALIBER CHANGE MOVES THE HEADLINE, AND THAT IS A FINDING. Mining the "
    "mover instead of `tracks[0]` leaves the corpus size untouched -- 193 "
    "judged, the same 7 unminable seeds, 4277 evidence rows at both calibers, "
    "so `_mover_track` costs no world its judgement -- but changes what is "
    "mined out of them: ground rules 932 -> 1043, lifted rules 149 -> 232, "
    "tautological-guard lifted rules 104 -> 155, underivable-`applicable` "
    "lifted rules 131 -> 208. The *ratios* barely move (69.8% -> 66.8% and "
    "87.9% -> 89.7%) because the defect is structural in `lift` and has nothing "
    "to do with which object was mined; the absolute counts move a lot because "
    "a mover yields `push_*` rules that a rock does not, and `lift` only ever "
    "groups move-shaped rules. So the F-2 finding is not an artefact of F-1: it "
    "survives the F-1 repair, half again as large. The F-1 numbers themselves "
    "mostly collapse, since F-1 is the thing V-13 fixed -- 72 F-1 worlds -> 8, "
    "1209 rows -> 110 -- and the residual 8 are exactly the 8 worlds where "
    "`_mover_track` returns `None` and `_mine` falls back to `tracks[0]` "
    "(verified: seeds 56, 92, 106, 158, 159, 161, 178, 200, identical sets). "
    "`ground.applicable_equals_support` stays n/n at both calibers (932/932, "
    "1043/1043), so the half of P1 that held still holds.",

    "PREDICATE for 104/149, and whether it is the prose's. The prose writes the "
    "guard as a JSON list, `[\"act==?dir\"]`, which is the exact-list reading: "
    "`Rule.as_json()[\"guard\"] == [\"act==?dir\"]`. That is what is counted and "
    "it gives 104 at the E11 caliber. The containment reading -- a guard that "
    "merely has an `act==?dir` conjunct somewhere -- gives 149/149, so the two "
    "readings are far apart and the choice matters. The exact-list reading is "
    "the one that yields the prose's number. The `?dir`-vs-any-variable "
    "ambiguity is not live: `miner.DIR_VAR` is the only variable `lift` ever "
    "substitutes, so `act==?<anything else>` cannot occur -- verified by the "
    "containment count matching the count of guards carrying any `act==?` atom.",

    "PREDICATE for 131/149. The partial does not state this number; its source "
    "is `ADVERSARIAL-cegis.md:224`, \"lifted rules whose published `applicable` "
    "!= the guard's firing set : 131 / 149\", claimed there to be "
    "reading-independent. Recomputed at the E11 caliber: under the engine's own "
    "evaluator all 149 are underivable (the guard either fires on nothing or "
    "raises); under the `?dir`-bound reading 131 are. The reading-independent "
    "count -- underivable under BOTH -- is 131, matching. So "
    "`derivable_from_guard` in the JSONL is True when EITHER reading reproduces "
    "`applicable`. All 18 derivable ones are derivable only under the bound "
    "reading, and they split two ways: 16 carry the bare `[\"act==?dir\"]` and "
    "are derivable only because their members happen to cover every transition "
    "in their world, so the tautological guard lands on the right set by "
    "accident; the other 2 carry `[\"act==?dir\", \"free(strip(?dir))\"]`, "
    "where the surviving `free` conjunct does the separating -- the same "
    "accident of the evidence that keeps Fixture A clean.",

    "`cegis.track0_worlds` AND `cegis.track0_motionless` ARE DIFFERENT "
    "PREDICATES THAT BOTH GAVE 72. The registry probes the first out of the "
    "string \"track0 NOT mover\"; the second is the count of worlds whose whole "
    "rule set is `effect: none` and whose mover moved. This module computes "
    "each the way its own registry entry describes it, rather than re-pointing "
    "both at whichever number happened to match -- which is the E18 defect one "
    "level down. `cegis.track0_worlds` compares `seg.tracks[0]`'s per-frame "
    "masks against the generator's own mover cells; the frames are rendered "
    "*from* those anchors, so it is the frames' upstream and not a "
    "re-derivation from pixels. It is a property of the **segmentation**, not "
    "of the mining, and it measures 72 at BOTH calibers -- while "
    "`cegis.track0_motionless`'s denominator collapses 72 -> 8. That divergence "
    "is the proof the separation was needed: one 72 is stable under V-13 and "
    "the other is not, so re-pointing both at the same recomputed number would "
    "have published a figure that is wrong for one of them.",

    "THE 1209 IS ONE MEASUREMENT, NOT TWO. At the E11 caliber: non-`noop` "
    "generator events in the 72 F-1 worlds = 1209; whole-frame changes = 1209; "
    "`move:`-labelled events alone = 1204 (the 5 remainder are `teleport`). The "
    "partial called 1209 a corroboration by two independent oracles; "
    "`ADVERSARIAL-cegis.md` §6.2 showed the two share the premise under "
    "dispute. The recomputation reproduces the equality and inherits the "
    "criticism: the number is right and the headline it carried (\"1209 rows "
    "are false\") was retracted -- 72/72 of those worlds' mined objects are "
    "provably motionless, so `effect: none` is true of them.",

    "P3 SCOPE IS WIDER THAN E11's, and that is a strengthening. E11 swept depth "
    "3 on Fixture A + 25 worlds and depth 2 on 60. This sweeps all judged "
    "worlds and all ground rules at each rule's own `frontier_max_size`, at "
    "both calibers: 0 omissions either way. Lifted frontiers are excluded "
    "because a `?dir` literal has no firing set to compare against -- the same "
    "reason `props/cegis_miner.py` keeps `frontier_is_complete_to_size` on "
    "`result.rules`. Guards minimal but *deeper* than a rule's own bound are "
    "P4/F-3, not P3: E11's 125-omission figure for that is NOT recomputed here.",

    "FIXTURE A IS NOT IN THIS CORPUS. The partial reports Fixture A separately "
    "(1 world, 49 transitions, 9 ground, 1 lifted) and every ratio in this "
    "module is a gridworld-1..200 ratio, which is how the partial states them.",

    "2a1c30d CANNOT MOVE ANY OF THESE. It touched `fd_adapter`, `lp_potential`, "
    "`probe_frontier`, `zero_space` and `mdl_segmenter`. Only `mdl_segmenter` "
    "is on this path, and the change there adds a `SegmentationError` raise on "
    "an assignment cell costing >= IMPOSSIBLE -- it does not fire anywhere in "
    "seeds 1-200 at either caliber (any raise would abort this run). "
    "`engine-rig/engines/cegis_miner/` and `fuzzlab/worlds/gridworld.py` have "
    "no commits between ed592a6 and HEAD, so the engine and the worlds are the "
    "ones E11 saw; the only thing that moved under these numbers is `_mine`, "
    "which is the caliber split above. The 29.2% figure the E18 ticket says "
    "2a1c30d invalidated is another engine's number and is not in scope here.",

    "STILL PROSE-ONLY, NOT RECOMPUTED: `cegis.lifted_bad` (91), "
    "`cegis.lifted_bad_rows` (342), `cegis.battery_green` (162) and "
    "`cegis.battery_green_superset` (188). They were not in this work order's "
    "table. Every other `cegis.*` registry key is re-pointable from this file: "
    "each count row carries the `registry_key` it answers.",

    "MECHANISM NOT RE-LITIGATED. Whether `act==?dir` is vacuous, and what that "
    "does to P1, was settled on the source by `ADVERSARIAL-cegis.md` §3 (the "
    "partial's mechanism sentence -- \"a tautology\" -- is wrong about the code: "
    "the engine's evaluator makes it always FALSE; both readings still falsify "
    "P1). This module counts; it does not re-argue that.",
]


def _measure(caliber: str) -> Dict[str, Any]:
    """Everything this module counts, at one caliber."""
    entries = corpus(caliber)
    judged = _judged(caliber)
    rows = lifted_rows(caliber)
    ground_ok, ground_total = _ground_applicable_equals_support(caliber)
    return {
        "lifted": len(rows),
        "exact_guard": sum(1 for r in rows if r["has_act_eq_dir"]),
        "contains_guard": sum(1 for r in rows if r["guard_contains_act_eq_dir"]),
        "underivable_both": sum(1 for r in rows if not r["derivable_from_guard"]),
        "underivable_engine": sum(
            1 for r in rows if not r["derivable_engine_reading"]),
        "underivable_bound": sum(
            1 for r in rows if not r["derivable_bound_reading"]),
        "ground_ok": ground_ok,
        "ground_total": ground_total,
        "judged": len(judged),
        "unminable": len(entries) - len(judged),
        "unminable_seeds": sorted(e["seed"] for e in entries if not e["minable"]),
        "transitions": sum(len(e["transitions"]) for e in judged),
        "track0": _track0_not_mover(caliber),
        "f1": _f1_worlds(caliber),
        "p3": _frontier_omissions(caliber),
    }


def _frac(numerator: int, denominator: int) -> str:
    return "%d / %d" % (numerator, denominator)


def compute() -> Dict[str, Any]:
    m = {caliber: _measure(caliber) for caliber in CALIBERS}
    e11, today = m["e11_caliber"], m["today_caliber"]

    def both(pick, prose, registry_key, what, **extra):
        return _row(pick(e11), pick(today), prose,
                    registry_key=registry_key, what=what, **extra)

    def per_caliber(build):
        return {c: build(m[c]) for c in CALIBERS}

    counts = {
        "cegis.lifted_tautological": both(
            lambda x: _frac(x["exact_guard"], x["lifted"]), "104 / 149",
            "cegis.lifted_tautological",
            "lifted rules whose published guard is exactly [\"act==?dir\"]",
            readings=per_caliber(lambda x: {
                "guard_is_exactly_act_eq_dir": x["exact_guard"],
                "guard_contains_an_act_eq_dir_literal": x["contains_guard"],
            })),
        "cegis.applicable_not_derivable": both(
            lambda x: _frac(x["underivable_both"], x["lifted"]), "131 / 149",
            "cegis.applicable_not_derivable",
            "lifted rules whose `applicable` is not reproduced by evaluating "
            "their own published guard, under either reading",
            readings=per_caliber(lambda x: {
                "underivable_engine_evaluator": x["underivable_engine"],
                "underivable_dir_bound": x["underivable_bound"],
                "underivable_under_both": x["underivable_both"],
            })),
        "ground.applicable_equals_support": both(
            lambda x: _frac(x["ground_ok"], x["ground_total"]), "932 / 932",
            None,
            "ground rules whose applicable set is exactly their support "
            "(the P1 check that held)"),
        "cegis.track0_worlds": both(
            lambda x: x["track0"]["not_mover"], 72, "cegis.track0_worlds",
            "worlds where seg.tracks[0] is not the generator's mover -- the "
            "registry's own predicate, not the F-1 world count that matched it",
            judged=per_caliber(lambda x: x["track0"]["judged"])),
        "cegis.track0_motionless": both(
            lambda x: _frac(x["f1"]["static"], x["f1"]["worlds"]), "72 / 72",
            "cegis.track0_motionless",
            "F-1 worlds (all-`none` rule set, mover did move) whose mined "
            "object occupies an identical cell set in every frame"),
        "cegis.track0_rows": both(
            lambda x: x["f1"]["events_non_noop"], 1209, "cegis.track0_rows",
            "the retracted headline count of allegedly-false published rows",
            readings=per_caliber(lambda x: {
                "generator_events_not_noop": x["f1"]["events_non_noop"],
                "generator_events_move_only": x["f1"]["events_move_only"],
                "whole_frame_changed": x["f1"]["frame_changes"],
                "transitions_in_f1_worlds": x["f1"]["transitions"],
            })),
        "cegis.frontier_missing_within": both(
            lambda x: x["p3"]["omissions"], 0, "cegis.frontier_missing_within",
            "minimal-by-inclusion guards absent from a ground rule's frontier "
            "within that rule's own frontier_max_size",
            sweep=per_caliber(lambda x: {
                "rules_swept": x["p3"]["rules_swept"],
                "rules_skipped_truncated": x["p3"]["rules_skipped_truncated"],
                "worlds_swept": x["judged"],
            })),
        "cegis.worlds": both(
            lambda x: x["judged"], 193, "cegis.worlds", "seeds 1-200, minable"),
        "corpus.worlds_unminable": both(
            lambda x: x["unminable"], 7, None,
            "neither segmentation operator narrates the world as move/none",
            seeds=per_caliber(lambda x: x["unminable_seeds"])),
        "cegis.transitions": both(
            lambda x: x["transitions"], 4277, "cegis.transitions",
            "evidence rows"),
        "cegis.ground": both(
            lambda x: x["ground_total"], 932, "cegis.ground",
            "published ground rules"),
        "cegis.lifted": both(
            lambda x: x["lifted"], 149, "cegis.lifted", "published lifted rules"),
    }

    out = _common.result(
        key="cegis.lifted_tautological",
        question="Of the lifted rules cegis_miner publishes over gridworld seeds "
                 "1-200, how many carry the guard [\"act==?dir\"]?",
        # `value` is the E11 caliber and only the E11 caliber, so
        # `agrees_with_e11` stays a like-for-like comparison. Today's number is
        # published beside it at the top level rather than folded into this
        # dict, which would make the equality test against the prose meaningless.
        value=_ratio(e11["exact_guard"], e11["lifted"]),
        e11_prose={"numerator": 104, "denominator": 149, "pct": 69.8},
        counts=counts,
        inputs=_common.input_digests(INPUTS),
        method=(
            "gridworld.generate(seed) for seed in 1..200, mined twice. "
            "e11_caliber: props._mine as at ed592a6, reproduced as _e11_mine -- "
            "split_by_color=False then True on ValueError, no track= argument, "
            "so seg.tracks[0]. today_caliber: fuzzlab.props.cegis_miner._mine "
            "called directly, which selects the mover via _mover_track (V-13, "
            "eb61aa98). Lifted rules are read off result.lifted and their "
            "guards off Rule.as_json()['guard']. Guard firing sets are "
            "recomputed from atoms.evaluate row by row, never from atom_masks, "
            "under two readings: the engine's evaluator as written, and ?dir "
            "bound to each row's own action. The P3 sweep rebuilds its own "
            "bitmasks from atoms.evaluate and enumerates the full vocabulary. "
            "Mover ground truth comes from the generator's own anchors, which "
            "the frames are rendered from. Nothing here consults rule.coverage, "
            "guards_are_mutually_exclusive, explains_every_transition, or any "
            "fuzzlab invariant."
        ),
        caveats=CAVEATS,
    )
    out["caliber"] = "e11_caliber"
    out["caliber_descriptions"] = dict(CALIBER_DESCRIPTION)
    out["today_caliber"] = {
        "value": _ratio(today["exact_guard"], today["lifted"]),
        "counts_that_differ_from_e11_caliber": sorted(
            k for k, v in counts.items() if not v["calibers_agree"]),
        "counts_that_hold_at_both_calibers": sorted(
            k for k, v in counts.items() if v["calibers_agree"]),
        "note": "What a reader running today's engine gets. Not comparable to "
                "the 2026-07-29 prose: V-13 (eb61aa98) re-cut the corpus by "
                "mining the mover instead of seg.tracks[0].",
    }
    return out


def dump_jsonl(path: str) -> int:
    """One raw row per lifted rule, both calibers, sorted, LF-terminated."""
    rows = [r for caliber in CALIBERS for r in lifted_rows(caliber)]
    rows.sort(key=lambda r: r["rule_id"])
    fields = ["rule_id", "caliber", "guard", "has_act_eq_dir", "applicable",
              "support", "derivable_from_guard", "derivable_engine_reading",
              "derivable_bound_reading", "engine_reading_unevaluable",
              "guard_contains_act_eq_dir", "seed", "name", "lifted_from"]
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps({k: row[k] for k in fields}, sort_keys=True))
            fh.write("\n")
    return len(rows)


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m tools.survey_numbers.cegis_lift_guard",
        # Deliberately not `__doc__`: this reaches a console whose encoding is
        # not ours to choose, and the docstring is not ASCII.
        description="Recompute cegis.lifted_tautological (104/149) and its "
                    "companions, at both mining calibers.")
    parser.add_argument(
        "--jsonl", metavar="PATH",
        help="write one raw row per lifted rule here, sorted by rule_id")
    return parser.parse_args(argv)


if __name__ == "__main__":
    _args = _parse_args()
    if _args.jsonl:
        dump_jsonl(_args.jsonl)
    _common.main(compute)
