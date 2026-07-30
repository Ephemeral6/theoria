"""E18 — recompute `cegis.lift_guard` (104/149) and its companion counts.

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

## The corpus, verbatim from the partial

`partials/cegis_miner-via-bruteforce.md` §3:

    | `gridworld` seeds 1-200 | 193 judged, 7 unminable | 4 277 | 932 | 149 |
    Both segmentation operators are tried in the same order
    `fuzzlab/props/cegis_miner.py::_mine` uses (`split_by_color=False`, then
    `True` on `ValueError`)

so: `fuzzlab.worlds.gridworld.generate(seed)` for `seed in 1..200`, segmented by
`mdl_segmenter.segment_trajectory`, mined by `cegis_miner.mine` off
`transitions_from_segmentation` **with no `track=` argument**.

That last clause is the one ambiguity worth flagging up front, and it is
resolved in `CAVEATS` below: today's `props._mine` selects the mover
explicitly, the E11-era one did not, and the E11 numbers are the ones the
default `seg.tracks[0]` produces.  `_e11_mine` below is the E11-era function,
reproduced here rather than imported, because importing today's would silently
re-cut the corpus.

## What is recomputed

| registry key | prose |
|---|---|
| `cegis.lift_guard` | 104 / 149 lifted rules whose guard is `["act==?dir"]` |
| `cegis.applicable_underivable` | 131 / 149 whose `applicable` is not derivable from their guard |
| `ground.applicable_equals_support` | 932 / 932 — the P1 check that held |
| `f1.static_rock_worlds` | 72 / 72 worlds whose mined object never moves |
| `f1.false_effect_rows` | 1209 — the retracted headline count |
| `p3.frontier_omissions` | 0 omissions within each rule's own `frontier_max_size` |

Run it:

    cd engine-rig
    python -m tools.survey_numbers.cegis_lift_guard
    python -m tools.survey_numbers.cegis_lift_guard --jsonl /tmp/lifted.jsonl
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
from fuzzlab.worlds import gridworld                # noqa: E402

# The partial pins every number to `gridworld.generate(seed)` for these seeds.
SEEDS = tuple(range(1, 201))

#: The direction variable `lift` substitutes.  `miner.DIR_VAR`, restated so the
#: predicate this module counts is visible in this file rather than one import
#: away.
DIR_VAR = "?dir"

#: The predicate `cegis.lift_guard` counts: the published guard list is exactly
#: this.  `Rule.as_json()["guard"]` is `sorted(atom.name ...)`, so a one-element
#: list compares literally.
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
    "fuzzlab/worlds/common.py",
    "fuzzlab/worlds/gridworld.py",
]


# --------------------------------------------------------------- the corpus

def _e11_mine(world: Any):
    """`fuzzlab/props/cegis_miner.py::_mine` **as it stood at `ed592a6`**.

    Reproduced, not imported.  Today's `_mine` calls `_mover_track` and passes
    `track=` (the V-13 corpus repair, `eb61aa98`), which mines a different
    object in 72 of these 193 worlds and therefore yields a different rule set,
    different lifted rules, and different counts.  Importing it would quietly
    recompute a *different* survey and report the difference as a disagreement
    with E11.  The E11 numbers are the numbers of `seg.tracks[0]`, so that is
    what is reproduced; see `CAVEATS[0]`.

    Returns `(MiningResult, transitions, segmentation, split)` or `None` when
    neither operator narrates the world as move/none (`Unminable`, 7 seeds).
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
        return engine.mine(transitions), transitions, seg, split
    return None


_CORPUS: Optional[List[Dict[str, Any]]] = None


def corpus() -> List[Dict[str, Any]]:
    """One entry per judged seed, ascending.  Memoised; pure in the seed."""
    global _CORPUS
    if _CORPUS is not None:
        return _CORPUS
    out: List[Dict[str, Any]] = []
    for seed in SEEDS:
        world = gridworld.generate(seed)
        mined = _e11_mine(world)
        if mined is None:
            out.append({"seed": seed, "minable": False})
            continue
        result, transitions, seg, split = mined
        out.append({
            "seed": seed,
            "minable": True,
            "world": world,
            "result": result,
            "transitions": transitions,
            "track": seg.tracks[0],
            "split_by_color": split,
        })
    _CORPUS = out
    return out


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

def lifted_rows() -> List[Dict[str, Any]]:
    """One raw row per lifted rule in the corpus, sorted by `rule_id`.

    `derivable_from_guard` is the **generous** reading: True when the published
    `applicable` set is reproduced by evaluating the published guard under
    *either* the engine's evaluator or the `?dir`-bound one.  So its negation is
    reading-independent, which is what `ADVERSARIAL-cegis.md:224` claims of the
    131.  The two readings are kept separately beside it.
    """
    rows: List[Dict[str, Any]] = []
    for entry in corpus():
        if not entry["minable"]:
            continue
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
                "rule_id": "gridworld:seed=%03d:lifted[%d]:%s"
                           % (entry["seed"], index, rule.name),
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


def _ground_applicable_equals_support() -> Tuple[int, int]:
    """P1's surviving half: ground rules whose `applicable` is their `support`."""
    ok = total = 0
    for entry in corpus():
        if not entry["minable"]:
            continue
        for rule in entry["result"].rules:
            total += 1
            if set(rule.applicable) == set(rule.support):
                ok += 1
    return ok, total


def _f1_worlds() -> Dict[str, int]:
    """The 72 worlds F-1 is about, and what the retracted 1209 counted.

    An F-1 world is one whose whole mined rule set has `effect: none` **and**
    whose mover moved at least once.  "Static rock" is then checked against the
    segmenter's own per-frame masks for the mined track: the object the miner
    described occupies an identical cell set in every frame, so `effect: none`
    is a true statement about *it*.

    1209 is counted two independent ways -- the generator's non-`noop` event
    labels, and whole-frame inequality -- because the adversarial review's whole
    point (§1.4, §6.2) was that those two are the *same* measurement wearing two
    hats.  Reproducing the equality is reproducing that criticism, not
    corroborating the headline.
    """
    worlds = 0
    static = 0
    transitions_in_f1 = 0
    events_non_noop = 0
    events_move_only = 0
    frame_changes = 0
    for entry in corpus():
        if not entry["minable"]:
            continue
        world, result = entry["world"], entry["result"]
        if not result.rules:
            continue
        if any(rule.effect.type != "none" for rule in result.rules):
            continue
        if world.moved() == 0:
            continue
        worlds += 1
        track = entry["track"]
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


def _frontier_omissions() -> Dict[str, int]:
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

    Scope is wider than E11's, which swept depth 3 on 25 worlds and depth 2 on
    60.  This sweeps **every** judged world at **every** rule's own
    `frontier_max_size`, which is what P3 quantifies over.  Guards deeper than
    a rule's own bound are P4's business (F-3) and are out of scope here, as
    they were there.
    """
    rules_swept = 0
    rules_skipped_truncated = 0
    omissions = 0
    for entry in corpus():
        if not entry["minable"]:
            continue
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
                pairs: List[frozenset] = []
                for a, b in itertools.combinations(covering, 2):
                    if names[a] in singles or names[b] in singles:
                        continue
                    if masks[a] & masks[b] == positives:
                        pairs.append(frozenset((names[a], names[b])))
                found.extend(pairs)
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


def _row(recomputed: Any, prose: Any, registry_key: Optional[str] = None,
         **extra: Any) -> Dict[str, Any]:
    """One table row.

    `registry_key` is the `ENGINE_TABLE.md` key this row can re-point, which is
    **not** always the key this row is filed under here; see `CAVEATS`.  `None`
    means the number is real but the registry does not publish it.
    """
    row: Dict[str, Any] = {
        "recomputed": recomputed,
        "e11_prose": prose,
        "agrees": recomputed == prose,
        "registry_key": registry_key,
    }
    row.update(extra)
    return row


CAVEATS = [
    "CORPUS RECIPE, and the reading taken. The partial says the harness used "
    "the operator order of `fuzzlab/props/cegis_miner.py::_mine`. At E11's base "
    "commit (ed592a6) that function passed no `track=` to "
    "`transitions_from_segmentation`, so it mined `seg.tracks[0]`. Today's "
    "`_mine` calls `_mover_track` and passes the mover (the V-13 corpus repair, "
    "eb61aa98) -- which is the whole subject of F-1. This module reproduces the "
    "E11-era function (`_e11_mine`), because the numbers under audit are the "
    "ones `seg.tracks[0]` produced; mining the mover instead would be a "
    "different survey, not a recomputation of this one. The engine under test "
    "(`engine-rig/engines/cegis_miner/`) is today's code and is byte-identical "
    "to ed592a6's.",

    "PREDICATE for 104/149, and whether it is the prose's. The prose writes the "
    "guard as a JSON list, `[\"act==?dir\"]`, which is the exact-list reading: "
    "`Rule.as_json()[\"guard\"] == [\"act==?dir\"]`. That is what is counted, and "
    "it gives 104. The containment reading -- a guard that merely has an "
    "`act==?dir` conjunct somewhere -- gives 149/149 (recorded in "
    "`counts.cegis.lift_guard.readings`), so the two readings are far apart and "
    "the choice matters. The exact-list reading is the one that yields the "
    "prose's number, and it is also the one the prose's own worked example "
    "supports: seed 6's second `push` has a multi-literal frontier and is "
    "discussed separately from the 104. The `?dir`-vs-any-variable ambiguity "
    "the ticket raises is not live: `miner.DIR_VAR` is the only variable `lift` "
    "ever substitutes, so `act==?<anything else>` cannot occur -- verified by "
    "the containment count matching the count of guards carrying any `act==?` "
    "atom.",

    "PREDICATE for 131/149. The prose in the partial does not state this number; "
    "its source is `ADVERSARIAL-cegis.md:224`, \"lifted rules whose published "
    "`applicable` != the guard's firing set : 131 / 149\", claimed there to be "
    "reading-independent. Recomputed: under the engine's own evaluator all "
    "149 are underivable (the guard either fires on nothing or raises); under "
    "the `?dir`-bound reading 131 are. The reading-independent count -- "
    "underivable under BOTH -- is 131, matching. So `derivable_from_guard` in "
    "the JSONL is True when EITHER reading reproduces `applicable`. All 18 "
    "derivable ones are derivable only under the bound reading, and they split "
    "two ways: 16 carry the bare `[\"act==?dir\"]` and are derivable only "
    "because their members happen to cover every transition in their world, so "
    "the tautological guard lands on the right set by accident; the other 2 "
    "carry `[\"act==?dir\", \"free(strip(?dir))\"]`, where the surviving `free` "
    "conjunct does the separating -- the same accident of the evidence that "
    "keeps Fixture A clean.",

    "THE 1209 IS ONE MEASUREMENT, NOT TWO. Non-`noop` generator events in the "
    "72 F-1 worlds = 1209; whole-frame changes = 1209; `move:`-labelled events "
    "alone = 1204 (the 5 remainder are `teleport`). The partial called 1209 a "
    "corroboration by two independent oracles; `ADVERSARIAL-cegis.md` §6.2 "
    "showed the two oracles share the premise under dispute. The recomputation "
    "reproduces the equality and inherits the criticism: the number is right "
    "and the headline it carried (\"1209 rows are false\") was retracted -- "
    "72/72 of those worlds' mined objects are provably motionless, so `effect: "
    "none` is true of them.",

    "P3 SCOPE IS WIDER THAN E11's, and that is a strengthening. E11 swept depth "
    "3 on Fixture A + 25 worlds and depth 2 on 60. This sweeps all 193 judged "
    "worlds and all 932 ground rules, each at its own `frontier_max_size`: 0 "
    "omissions. Lifted frontiers are excluded because a `?dir` literal has no "
    "firing set to compare against -- the same reason `props/cegis_miner.py` "
    "keeps `frontier_is_complete_to_size` on `result.rules`. Guards minimal but "
    "*deeper* than a rule's own bound are P4/F-3, not P3, and are not swept: "
    "E11's 125-omission figure for that is NOT recomputed here.",

    "FIXTURE A IS NOT IN THIS CORPUS. The partial reports Fixture A separately "
    "(1 world, 49 transitions, 9 ground, 1 lifted) and every ratio in this "
    "module is a gridworld-1..200 ratio, which is how the partial states them.",

    "2a1c30d CANNOT MOVE ANY OF THESE. It touched `fd_adapter`, `lp_potential`, "
    "`probe_frontier`, `zero_space` and `mdl_segmenter`. Only `mdl_segmenter` is "
    "on this path, and the change there adds a `SegmentationError` raise on an "
    "assignment cell costing >= IMPOSSIBLE -- it does not fire anywhere in "
    "seeds 1-200 (any raise would abort this run). "
    "`engine-rig/engines/cegis_miner/` and `fuzzlab/worlds/gridworld.py` have "
    "no commits between ed592a6 and HEAD, so the mined rule sets are the same "
    "objects E11 saw. The 29.2% figure the E18 ticket says 2a1c30d invalidated "
    "is an `mdl_segmenter` number and is not in this module's scope.",

    "THIS MODULE'S `key` IS NOT THE REGISTRY'S KEY, AND THE RE-POINTING NEEDS "
    "THE MAPPING. `ENGINE_TABLE.md` files 104 under `cegis.lifted_tautological` "
    "and 131/149 under `cegis.applicable_not_derivable`; the work order named "
    "them `cegis.lift_guard` and `cegis.applicable_underivable`, which is what "
    "this module reports so that `run_all --only cegis_lift_guard` and the "
    "counts filename stay as commissioned. Every row therefore carries a "
    "`registry_key` field naming the `tools/engine_table.py` FACT it can "
    "re-point (or `null` where the registry publishes no such number). Six of "
    "the eleven recomputed rows re-point a live registry probe: "
    "cegis.lifted_tautological, cegis.applicable_not_derivable, "
    "cegis.frontier_missing_within, cegis.track0_motionless, cegis.track0_rows, "
    "plus the four corpus keys cegis.worlds / cegis.transitions / cegis.ground "
    "/ cegis.lifted. `cegis.lifted_bad` (91), `cegis.lifted_bad_rows` (342), "
    "`cegis.battery_green` (162) and `cegis.battery_green_superset` (188) are "
    "NOT recomputed here -- they were not in this work order's table and remain "
    "prose-only. `cegis.track0_worlds` (72) is probed from a different "
    "predicate again (\"track0 NOT mover\"); this module's 72 is the count of "
    "all-`none`-rule-set worlds whose mover moved, which the adversarial run "
    "measured as the same 72 but which is not literally that probe's string.",

    "MECHANISM NOT RE-LITIGATED. Whether `act==?dir` is vacuous, and what that "
    "does to P1, was settled on the source by `ADVERSARIAL-cegis.md` §3 (the "
    "partial's mechanism sentence -- \"a tautology\" -- is wrong about the code: "
    "the engine's evaluator makes it always FALSE; both readings still falsify "
    "P1). This module counts; it does not re-argue that.",
]


def compute() -> Dict[str, Any]:
    entries = corpus()
    judged = [e for e in entries if e["minable"]]
    unminable = [e for e in entries if not e["minable"]]

    rows = lifted_rows()
    n_lifted = len(rows)
    n_exact = sum(1 for r in rows if r["has_act_eq_dir"])
    n_contains = sum(1 for r in rows if r["guard_contains_act_eq_dir"])
    n_underivable_both = sum(1 for r in rows if not r["derivable_from_guard"])
    n_underivable_engine = sum(1 for r in rows if not r["derivable_engine_reading"])
    n_underivable_bound = sum(1 for r in rows if not r["derivable_bound_reading"])

    ground_ok, ground_total = _ground_applicable_equals_support()
    f1 = _f1_worlds()
    p3 = _frontier_omissions()

    n_transitions = sum(len(e["transitions"]) for e in judged)
    n_ground = sum(len(e["result"].rules) for e in judged)

    value = _ratio(n_exact, n_lifted)
    prose = {"numerator": 104, "denominator": 149, "pct": 69.8}

    counts = {
        "cegis.lift_guard": _row(
            "%d / %d" % (n_exact, n_lifted), "104 / 149",
            registry_key="cegis.lifted_tautological",
            what="lifted rules whose published guard is exactly [\"act==?dir\"]",
            readings={
                "guard_is_exactly_act_eq_dir": n_exact,
                "guard_contains_an_act_eq_dir_literal": n_contains,
            }),
        "cegis.applicable_underivable": _row(
            "%d / %d" % (n_underivable_both, n_lifted), "131 / 149",
            registry_key="cegis.applicable_not_derivable",
            what="lifted rules whose `applicable` is not reproduced by evaluating "
                 "their own published guard, under either reading",
            readings={
                "underivable_engine_evaluator": n_underivable_engine,
                "underivable_dir_bound": n_underivable_bound,
                "underivable_under_both": n_underivable_both,
            }),
        "ground.applicable_equals_support": _row(
            "%d / %d" % (ground_ok, ground_total), "932 / 932",
            registry_key=None,
            what="ground rules whose applicable set is exactly their support "
                 "(the P1 check that held)"),
        "f1.static_rock_worlds": _row(
            "%d / %d" % (f1["static"], f1["worlds"]), "72 / 72",
            registry_key="cegis.track0_motionless",
            what="F-1 worlds (all-`none` rule set, mover did move) whose mined "
                 "object occupies an identical cell set in every frame"),
        "f1.false_effect_rows": _row(
            f1["events_non_noop"], 1209,
            registry_key="cegis.track0_rows",
            what="the retracted headline count of allegedly-false published rows",
            readings={
                "generator_events_not_noop": f1["events_non_noop"],
                "generator_events_move_only": f1["events_move_only"],
                "whole_frame_changed": f1["frame_changes"],
                "transitions_in_f1_worlds": f1["transitions"],
            }),
        "p3.frontier_omissions": _row(
            p3["omissions"], 0,
            registry_key="cegis.frontier_missing_within",
            what="minimal-by-inclusion guards absent from a ground rule's "
                 "frontier within that rule's own frontier_max_size",
            rules_swept=p3["rules_swept"],
            rules_skipped_truncated=p3["rules_skipped_truncated"],
            worlds_swept=len(judged)),
        "corpus.worlds_judged": _row(
            len(judged), 193, registry_key="cegis.worlds",
            what="seeds 1-200, minable"),
        "corpus.worlds_unminable": _row(
            len(unminable), 7, registry_key=None,
            what="neither segmentation operator narrates the world as move/none",
            seeds=sorted(e["seed"] for e in unminable)),
        "corpus.transitions": _row(
            n_transitions, 4277, registry_key="cegis.transitions",
            what="evidence rows"),
        "corpus.ground_rules": _row(
            n_ground, 932, registry_key="cegis.ground",
            what="published ground rules"),
        "corpus.lifted_rules": _row(
            n_lifted, 149, registry_key="cegis.lifted",
            what="published lifted rules"),
    }

    return _common.result(
        key="cegis.lift_guard",
        question="Of the lifted rules cegis_miner publishes over gridworld seeds "
                 "1-200, how many carry the guard [\"act==?dir\"]?",
        value=value,
        e11_prose=prose,
        counts=counts,
        inputs=_common.input_digests(INPUTS),
        method=(
            "gridworld.generate(seed) for seed in 1..200; segmented by "
            "mdl_segmenter.segment_trajectory with split_by_color=False, then "
            "True on ValueError; mined by cegis_miner.mine off "
            "transitions_from_segmentation with no track= argument (the E11-era "
            "props._mine, reproduced as _e11_mine). Lifted rules are read off "
            "result.lifted and their guards off Rule.as_json()['guard']. Guard "
            "firing sets are recomputed from atoms.evaluate row by row, never "
            "from atom_masks, under two readings: the engine's evaluator as "
            "written, and ?dir bound to each row's own action. The P3 sweep "
            "rebuilds its own bitmasks from atoms.evaluate and enumerates the "
            "full vocabulary. Nothing here consults rule.coverage, "
            "guards_are_mutually_exclusive, explains_every_transition, or "
            "fuzzlab.props."
        ),
        caveats=CAVEATS,
    )


def dump_jsonl(path: str) -> int:
    rows = lifted_rows()
    fields = ["rule_id", "guard", "has_act_eq_dir", "applicable", "support",
              "derivable_from_guard", "derivable_engine_reading",
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
        description="Recompute cegis.lift_guard (104/149) and its companions.")
    parser.add_argument(
        "--jsonl", metavar="PATH",
        help="write one raw row per lifted rule here, sorted by rule_id")
    return parser.parse_args(argv)


if __name__ == "__main__":
    _args = _parse_args()
    if _args.jsonl:
        dump_jsonl(_args.jsonl)
    _common.main(compute)
