"""`cegis_miner` — six invariants, evaluated directly rather than via bitmasks.

The engine reasons in integer bitmasks over transition indices. Every check here
re-derives the same facts by calling `atoms.evaluate` on each `(state, action)`
and comparing sets, so a bug in the mask bookkeeping — the most likely place for
one — cannot hide behind the bookkeeping that produced it.

Two scope limits, taken from the engine's own documented contract, because
asserting past either would file a bug against a promise never made:

* **completeness is bounded by `rule.frontier_max_size`, which is not always 3.**
  `mine` sets `size = min(max(len(cegis_guard), 1), max_frontier_size)`, so a
  rule whose CEGIS guard came out at one literal has its frontier enumerated at
  size 1 and two-literal minimal guards are legitimately absent. The invariant
  is completeness *up to that rule's own bound*;
* **`NoSeparatingGuard` is a documented outcome, not a defect.** It is what the
  engine raises when the fixed five-predicate vocabulary cannot separate a
  positive from a negative — coarse vocabulary, or contradictory evidence. It is
  recorded as `skipped` with the reason rather than as a violation or an
  unexpected raise, so the campaign's counts stay honest about how many worlds
  were actually judged.

| invariant | claim under test |
|---|---|
| `frontier_guards_are_consistent` | every frontier guard fires on exactly the rule's support — covers every positive, excludes every negative |
| `frontier_is_complete_to_size` | every minimal consistent guard within the rule's own size bound is in the frontier |
| `applicable_equals_support` | a consistent rule's applicable set is its support, so `coverage` is n/n |
| `guards_partition_the_evidence` | the ground rules are mutually exclusive and explain every transition |
| `effects_agree_with_the_evidence` | the effect a rule claims is the motion its evidence actually shows |
| `rules_fire_on_the_action_they_name` | the action a rule is filed under is the action taken at every transition it claims |

## What V-13 added, and the gap it closed

The first four invariants are, between them, a complete theory of **guards** —
of *when* a rule fires. Not one of them read `Rule.effect`, so a rule set with
correct guards and inverted effects passed the entire battery clean
(`runs/…-V10-fuzz-mutation-power/PUBLISHED_VS_AUDITED.md`: `effect.*` is five
published fields, all five mechanically consumed downstream by
`cold-start-a0/prime/probe_runner.py:72`, and audited by a single pinned
assertion on one engine-rig fixture). `effects_agree_with_the_evidence` is the
missing half: what the rule says *happens*.

Its truth comes from `fuzzlab/oracles/motion.py`, which reads the world's
rendered frames and nothing else. That is not fussiness. The obvious source —
`transitions[i].effect` — is `cegis_miner` repeating `mdl_segmenter`'s
narration, so comparing against it would certify that the miner agrees with the
segmenter while staying blind to both being wrong the same way. The oracle is
allowed to fail: a frame pair it cannot resolve into one rigid mover
translation is recorded `skipped` with the reason, never passed and never
violated.

**Scope, and why it is not uniform.** These two new invariants iterate
`result.all_rules`; the four older ones iterate `result.rules`. That difference
is deliberate and each half of it is a decision:

* `all_rules` is what `cegis_miner/__init__.py:candidates()` publishes, and the
  35 lifted rules in a measured 224 (15.6%) had never entered any invariant —
  not a field unread, a whole class of candidate unlooked-at. Lifted rules are
  the *most* wanted kind, being the generalised `push(?dir)` a playbook wants;
* `guards_partition_the_evidence` must **not** move to `all_rules`. A lifted
  rule covers exactly the transitions of the ground rules it collapses, so
  mutual exclusion is false of `all_rules` by construction and the invariant
  would fire on every world for a reason that is not a defect;
* `frontier_guards_are_consistent` and `frontier_is_complete_to_size` must not
  either: a lifted guard's atoms carry the direction variable, and evaluating
  `act==?dir` against a concrete action is not a question with an answer.

`applicable_equals_support` **was** moved to `all_rules` in V-13, because
`lift()` builds both sets as the union over members whose own two sets are
equal, so the claim is exactly as true of a lifted rule and is published in the
same `coverage` string.
"""

import itertools
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from fuzzlab import rig  # noqa: F401  (path bootstrap)
from fuzzlab.oracles import motion
from fuzzlab.props import finding
from fuzzlab.worlds.gridworld import DELTA

from engines import cegis_miner as engine  # noqa: E402
from engines.cegis_miner import atoms as atom_mod  # noqa: E402
from engines.cegis_miner.miner import NoSeparatingGuard  # noqa: E402
from engines import mdl_segmenter  # noqa: E402

FAMILY = "gridworld"
ENGINE = "cegis_miner"

# The exhaustive subset sweep in `frontier_is_complete_to_size` is
# C(|vocabulary|, size).  Beyond this the property records a `skipped` rather
# than sampling — a partial sweep reported as a pass claims coverage it does not
# have.
COMBINATION_BUDGET = 400_000


class Unminable(Exception):
    """The segmentation narrates something `transitions_from_segmentation` refuses.

    Not a defect. `transitions_from_segmentation` raises `ValueError` by design
    when a transition narrates anything other than a single `move` or nothing —
    it mines the mover's rule and an `appear`/`vanish`/`recolor` is not one.
    """


def _mine(world: Any):
    """Mine the mover's rules, trying both segmentation operators before giving up.

    The colour-agnostic operator is tried first because it is the engine's
    default. It merges the mover with an obstacle the moment they touch, and the
    merged component narrates as `vanish` + `appear` rather than `move` — the
    touching-objects gap the A0 family has reported upstream twice. Once
    `gridworld` started producing reachable obstacles at all (see
    `worlds/gridworld.py:_place_obstacles`), that stopped being rare: it fired on
    179 of 500 worlds in the first full campaign, and on **159 of 500** after
    V-13 made the track selection pick the mover (321 mine under the default
    operator, 159 need `split_by_color=True`, 20 are unminable under either).

    `split_by_color=True` is the operator that exists for exactly this, so it is
    tried second and the one that worked is recorded. Where neither can produce a
    move/none narration the property records a **`skipped`** with the reason,
    not a `raised`: a documented refusal counted as an unexplained exception
    makes the campaign's own health look worse than it is, and — worse — hides
    how many worlds actually got judged.
    """
    background = world.spec_json().get("background", 0)
    errors = []
    fallback = None
    for split in (False, True):
        seg = mdl_segmenter.segment_trajectory(world.frames, background=background,
                                               split_by_color=split)
        track = _mover_track(world, seg)
        try:
            transitions = engine.transitions_from_segmentation(
                world.frames, world.action_list, seg, background=background,
                track=track)
        except ValueError as exc:
            errors.append("split_by_color=%s: %s" % (split, exc))
            continue
        if track is not None:
            return engine.mine(transitions), transitions, split
        # It mines, but off some other object. Keep it and try the other
        # operator first: committing to the first segmentation that *mines*
        # rather than the first that mines *the mover* was costing 42 of 500
        # worlds their subject, because the colour-agnostic operator often
        # narrates a rock cleanly on a world where only `split_by_color=True`
        # keeps the mover in one piece.
        if fallback is None:
            fallback = (engine.mine(transitions), transitions, split)
    if fallback is not None:
        return fallback
    raise Unminable("; ".join(errors))


def _mover_track(world: Any, seg: Any) -> Optional[Any]:
    """The segmenter track that is the world's mover, or `None` to keep the default.

    **This is a corpus repair, and it is the second one this battery has needed.**
    `transitions_from_segmentation` takes the track to mine as a parameter and
    falls back to `seg.tracks[0]` — the segmenter's first component in raster
    order. `_mine` used to take that fallback, and on the campaign seed's first
    60 gridworlds **21 of the 57 minable ones were mining a static obstacle**.
    A rock yields one `blocked_<D>` rule per action, `effect: none`, guards that
    are trivially mutually exclusive and trivially complete: all four guard
    invariants pass, on a rule set that says nothing ever happens. That is the
    same shape of defect `worlds/gridworld.py:_place_obstacles` documents — a
    green campaign over a corpus that could not have contradicted anything —
    and it is why 37% of this engine's worlds were not testing it.

    Which track is the mover is settled against `oracles/motion.py`'s
    pixel-derived trajectory, so the choice does not depend on the segmenter
    being right about anything except where it says its own tracks are. It is a
    choice about **what to mine**, made before the miner runs; no invariant's
    truth comes from here.

    `None` (keep `tracks[0]`) when the pixels do not fix the mover's path —
    chiefly a world whose mover never moves, where every object is static and
    the distinction has no content.
    """
    anchors = motion.mover_anchors(world)
    if anchors is None:
        return None
    shape, _colour, _background = motion.mover_spec(world)
    for track in seg.tracks:
        if tuple(track.shape) != shape:
            continue
        if len(track.anchors) < len(anchors):
            continue
        if all(track.anchors[t] is not None
               and tuple(track.anchors[t]) == tuple(anchors[t])
               for t in range(len(anchors))):
            return track
    return None


def _fires_on(guard: Sequence[Any], transitions: Sequence[Any]) -> Set[int]:
    """The transitions this guard admits, by direct evaluation."""
    return {t.index for t in transitions
            if all(atom_mod.evaluate(a, t.state, t.action) for a in guard)}


def _skip_no_guard(world: Any, invariant: str, exc: Exception) -> List[finding.Finding]:
    if isinstance(exc, Unminable):
        return [finding.skipped(
            ENGINE, invariant, world,
            "neither segmentation operator narrates this world as move/none — "
            "the mover's component merges with an obstacle it touches. Documented "
            "refusal by transitions_from_segmentation, and an instance of the "
            "touching-objects segmentation gap, not a mining defect.",
            error=str(exc), cause="unminable")]
    return [finding.skipped(
        ENGINE, invariant, world,
        "NoSeparatingGuard — the fixed five-predicate vocabulary cannot separate "
        "this world's evidence. Documented behaviour (miner.py, "
        "test_contradictory_evidence_is_reported_not_papered_over), not a defect.",
        error=str(exc), cause="no_separating_guard")]


# --------------------------------------------------------------- invariants

def frontier_guards_are_consistent(world: Any) -> List[finding.Finding]:
    """Every frontier guard admits exactly the rule's support."""
    try:
        result, transitions, _split = _mine(world)
    except (NoSeparatingGuard, Unminable) as exc:
        return _skip_no_guard(world, "frontier_guards_are_consistent", exc)

    subject = _mined_subject(world, transitions, "frontier_guards_are_consistent")
    if subject is not None:
        return [subject]

    out: List[finding.Finding] = []
    for rule in result.rules:
        support = set(rule.support)
        for guard in rule.frontier:
            fires = _fires_on(guard, transitions)
            if fires != support:
                out.append(finding.violated(
                    ENGINE, "frontier_guards_are_consistent", world,
                    "rule %s: frontier guard [%s] fires on %s, support is %s"
                    % (rule.name, " AND ".join(sorted(a.name for a in guard)),
                       sorted(fires), sorted(support)),
                    rule=rule.name,
                    guard=sorted(a.name for a in guard),
                    missed=sorted(support - fires),
                    spurious=sorted(fires - support)))
                return out
    return out


def frontier_is_complete_to_size(world: Any) -> List[finding.Finding]:
    """No consistent guard within the rule's own size bound is missing.

    Brute force: enumerate every subset of the vocabulary up to
    `rule.frontier_max_size`, keep the ones that fire on exactly the support, and
    check each is present in the frontier up to reordering. Minimality is handled
    by comparing sets of atoms — a non-minimal consistent guard is a superset of
    a minimal one and the engine is entitled to omit it.
    """
    try:
        result, transitions, _split = _mine(world)
    except (NoSeparatingGuard, Unminable) as exc:
        return _skip_no_guard(world, "frontier_is_complete_to_size", exc)

    subject = _mined_subject(world, transitions, "frontier_is_complete_to_size")
    if subject is not None:
        return [subject]

    vocabulary = atom_mod.build_vocabulary([t.state for t in transitions])
    out: List[finding.Finding] = []
    for rule in result.rules:
        if rule.frontier_truncated or not rule.frontier:
            continue                    # the engine says it stopped early; believe it
        size = rule.frontier_max_size
        combinations = 1
        for k in range(1, size + 1):
            combinations += _choose(len(vocabulary), k)
        if combinations > COMBINATION_BUDGET:
            out.append(finding.skipped(
                ENGINE, "frontier_is_complete_to_size", world,
                "vocabulary of %d atoms at size %d is %d subsets, over budget"
                % (len(vocabulary), size, combinations),
                cause="frontier_size_over_budget",
                rule=rule.name, vocabulary=len(vocabulary), size=size))
            continue

        support = set(rule.support)
        have = {frozenset(a.name for a in g) for g in rule.frontier}
        minimal: List[frozenset] = []
        for k in range(1, size + 1):
            for combo in itertools.combinations(vocabulary, k):
                names = frozenset(a.name for a in combo)
                if any(m < names for m in minimal):
                    continue            # a strict superset of a minimal guard
                if _fires_on(combo, transitions) == support:
                    minimal.append(names)
        for names in minimal:
            if names not in have:
                out.append(finding.violated(
                    ENGINE, "frontier_is_complete_to_size", world,
                    "rule %s: guard [%s] is consistent and within size %d but is "
                    "not in the frontier (%d entries)"
                    % (rule.name, " AND ".join(sorted(names)), size,
                       len(rule.frontier)),
                    rule=rule.name, missing=sorted(names),
                    frontier_max_size=size,
                    frontier=[sorted(a.name for a in g) for g in rule.frontier]))
                return out
    return out


def applicable_equals_support(world: Any) -> List[finding.Finding]:
    """A consistent rule's applicable set is exactly its support.

    Iterates `all_rules`, not `rules`: `lift()` builds a lifted rule's
    `applicable` and `support` as the unions over members that each satisfy this
    equality, so it is claimed of a lifted rule exactly as strongly, and
    `candidates()` publishes the resulting `coverage` string for both. Before
    V-13 every invariant here stopped at `result.rules` and the lifted class —
    15.6% of published rules, measured — was never looked at.
    """
    try:
        result, _transitions, _split = _mine(world)
    except (NoSeparatingGuard, Unminable) as exc:
        return _skip_no_guard(world, "applicable_equals_support", exc)

    subject = _mined_subject(world, _transitions, "applicable_equals_support")
    if subject is not None:
        return [subject]

    out: List[finding.Finding] = []
    for rule in result.all_rules:
        if set(rule.applicable) != set(rule.support):
            out.append(finding.violated(
                ENGINE, "applicable_equals_support", world,
                "rule %s: applicable %s != support %s, so coverage %s is "
                "not n/n" % (rule.name, sorted(rule.applicable),
                             sorted(rule.support), rule.coverage),
                rule=rule.name, applicable=sorted(rule.applicable),
                support=sorted(rule.support), coverage=rule.coverage))
    return out


def guards_partition_the_evidence(world: Any) -> List[finding.Finding]:
    """Ground rules are mutually exclusive and explain every transition.

    Recomputed by direct evaluation rather than by asking the engine's own
    `guards_are_mutually_exclusive()` / `explains_every_transition()`, which are
    near-tautological on any input `mine` accepts. Evaluating the guards makes
    the check independent of the mask bookkeeping.
    """
    try:
        result, transitions, _split = _mine(world)
    except (NoSeparatingGuard, Unminable) as exc:
        return _skip_no_guard(world, "guards_partition_the_evidence", exc)

    subject = _mined_subject(world, transitions, "guards_partition_the_evidence")
    if subject is not None:
        return [subject]

    claimed: Dict[int, str] = {}
    out: List[finding.Finding] = []
    for rule in result.rules:
        for index in _fires_on(rule.guard, transitions):
            if index in claimed and claimed[index] != rule.name:
                out.append(finding.violated(
                    ENGINE, "guards_partition_the_evidence", world,
                    "transition %d is claimed by both %s and %s"
                    % (index, claimed[index], rule.name),
                    transition=index, rules=[claimed[index], rule.name]))
                return out
            claimed[index] = rule.name
    everything = {t.index for t in transitions}
    if set(claimed) != everything:
        out.append(finding.violated(
            ENGINE, "guards_partition_the_evidence", world,
            "%d of %d transitions are explained by no ground rule: %s"
            % (len(everything - set(claimed)), len(everything),
               sorted(everything - set(claimed))[:8]),
            unexplained=sorted(everything - set(claimed))[:8],
            n_transitions=len(everything)))
    return out


#: `_claimed_delta` could not resolve a parameterised effect against this
#: transition's action. Distinct from `None`, which is the claim that nothing
#: moved — conflating the two turns "I cannot read this claim" into "the engine
#: says nothing happened" and manufactures violations.
UNRESOLVED = object()


def _mined_subject(world: Any, transitions: Sequence[Any],
                   invariant: str) -> Optional[finding.Finding]:
    """`None` if the mined object is the world's mover; a `skipped` if it is not.

    **This check is the difference between an invariant and a false accusation,
    and it was found by making the accusation.** The first version of
    `effects_agree_with_the_evidence` reported 21 violations across 60 worlds.
    The oracle was right; the *subject* was wrong. `_mine` was taking
    `transitions_from_segmentation`'s `seg.tracks[0]` fallback, which in 21 of
    the 57 minable worlds is a **static obstacle** — and `blocked_<D>` rules
    with `effect: none` are a true description of a rock.

    `_mine` now selects the mover (see `_mover_track`), so that cause is gone.
    **What remains has a different cause, and the first version of this
    docstring named the wrong one** — it said the segmenter "did not list the
    mover first", and that sentence was copied into the `skipped` message below,
    where it would have sent whoever triaged the finding to the wrong place.
    Measured on the standing 500-world campaign, the truth is: **15 of 500**
    worlds, and in **14 of those 15** the segmenter *does* produce a track with
    the mover's exact bounding box — its `anchors` list simply contains `None`
    on some frames, so the track is discontinuous and cannot be matched against
    a trajectory. World 12 loses the mover on 2 of 23 frames; world 19 on 15 of
    16. That is a `mdl_segmenter` track-continuity defect and it is written up
    as one in `BUGS.md` § S5; it is another engine's territory, so it is
    reported and not touched.

    **All six invariants are gated on this, not just the two that read effects.**
    That is a V-13 correction made after review, and it costs the four guard
    invariants their reported coverage (480 → 465, uniform across all six). The
    reason is a measurement rather than a principle argued in the abstract: on
    every one of those worlds **every rule's effect is `none` and there are no
    lifted rules at all** — the rule set is two to four `blocked_<D>` rules whose
    guards are `act==D`, mutually exclusive and covering by construction on any
    world whatsoever. Reporting those as evaluated is the same confusion this
    round spent a whole section removing from `props/lp_potential.py`: "I could
    not check this world" and "I checked it and found nothing" must not be the
    same answer. Applying the rule in one module and not the other would have
    been the harder thing to explain.

    Identity is settled by comparing two independently derived trajectories —
    the anchors the segmenter put in `state.anchor`, which is *input* to the
    miner and the same input its guards are evaluated against, against the
    anchors `oracles/motion.py` chains out of the pixels. Nothing the miner
    computed is consulted.
    """
    if not transitions:
        return finding.skipped(
            ENGINE, invariant, world,
            "no transitions were mined from this world",
            cause="no_transitions")
    shape, _colour, _background = motion.mover_spec(world)
    anchors = motion.mover_anchors(world)
    if anchors is None:
        return finding.skipped(
            ENGINE, invariant, world,
            "the pixels do not fix the mover's trajectory — either it never "
            "moves in this world, or a frame pair is not one rigid mover "
            "translation — so which object was mined cannot be established "
            "without taking the segmenter's word for it",
            cause="mover_path_not_fixed_by_pixels")
    mined = tuple(transitions[0].state.shape)
    reason = ("its bounding box is %s and the mover's is %s"
              % (list(mined), list(shape)))
    if mined == shape:
        off = [t.index for t in transitions
               if t.index >= len(anchors)
               or tuple(anchors[t.index]) != tuple(t.state.anchor)]
        if not off:
            return None
        reason = ("its anchors diverge from the mover's pixel-derived "
                  "trajectory at %d of %d transitions, first at %d"
                  % (len(off), len(transitions), off[0]))
    return finding.skipped(
        ENGINE, invariant, world,
        "the mined track is not the world's mover: %s. Neither segmentation "
        "operator produced a track matching the mover, so _mine fell back to "
        "seg.tracks[0] and this rule set describes some other object — measured "
        "across the corpus, always a static one, yielding only `blocked_<D>` "
        "rules with `effect: none`, which are true of it. **Triage starts at "
        "mdl_segmenter, not here**: in 14 of the 15 worlds this fires on, a "
        "track with the mover's exact bounding box does exist and its `anchors` "
        "list carries `None` on some frames, i.e. the segmenter drops the mover "
        "mid-trajectory. See BUGS.md section S5. Not a cegis_miner defect "
        "and not a fuzzlab oracle defect; this world did not test the miner."
        % reason,
        mined_shape=list(mined), mover_shape=list(shape),
        cause="mined_track_is_not_the_mover")


def _claimed_delta(rule: Any, action: str) -> Optional[Tuple[int, int]]:
    """The displacement this rule claims for a transition whose action is `action`.

    `None` means the rule claims nothing moved. Three shapes, all read off the
    published `Effect` and not off anything the miner computed:

    * `type != "move"` — the rule claims nothing happens;
    * `direction` set to a concrete compass name — the lifted template was
      instantiated to one direction, so that is the claim for every member;
    * `direction` set to anything the world does not recognise as a direction
      (the engine writes `"?dir"`) — the claim is parameterised, and for a
      transition taking action `a` it resolves to `DELTA[a]`. That is exactly
      what `miner.py:_normalise` requires of every member before lifting them,
      so it is the engine's own reading of the variable and not this module's.

    `UNRESOLVED` is returned when a parameterised effect meets an action the
    world does not name a direction for. It must not collapse into `None`:
    `None` is the positive claim *nothing moved*, and reading an unresolvable
    claim as that one would report a violation on every transition where the
    mover did move. `gridworld` only ever issues compass actions, so this branch
    is unreachable today — it is written because the alternative is a false
    accusation waiting for the first family that is not `gridworld`.
    """
    effect = rule.effect
    if effect.type != motion.MOVE:
        return None
    direction = getattr(effect, "direction", None)
    if direction is not None:
        if direction in DELTA:
            return DELTA[direction]
        resolved = DELTA.get(action)          # the variable, resolved per witness
        return UNRESOLVED if resolved is None else resolved
    return (int(effect.dy), int(effect.dx))


def effects_agree_with_the_evidence(world: Any) -> List[finding.Finding]:
    """A rule's `effect` is the motion its own evidence actually shows.

    For every rule the engine publishes — ground and lifted — and every
    transition index in that rule's support, the displacement the rule claims is
    compared against the displacement `oracles/motion.py` reads out of the two
    frames. The oracle imports nothing from `engines`; see its module docstring
    for why `transitions[i].effect` is not an acceptable source of truth here.

    `effect.to` is checked **only when the engine sets it**. `mine()` keeps a
    destination only when every witness agrees on one, so `to = None` is a
    documented refusal to claim rather than a false claim, and asserting against
    it would file a bug against a promise never made. That leaves a real
    residual gap — an engine that dropped a destination it could have stated
    would not be caught — and `mutants/cegis_miner.py:cm-drop-effect-destination`
    is registered as a predicted survivor so the gap is measured rather than
    merely admitted.
    """
    invariant = "effects_agree_with_the_evidence"
    try:
        result, transitions, _split = _mine(world)
    except (NoSeparatingGuard, Unminable) as exc:
        return _skip_no_guard(world, invariant, exc)

    truth = motion.motions(world)
    refused = motion.unreadable_reasons(world)
    actions = world.action_list

    # The comparison is only meaningful if the engine's transition index means
    # what the oracle assumes: the index of the frame the transition starts
    # from. Checked, not assumed -- a silent renumbering would turn every
    # comparison below into a comparison of unrelated pairs.
    stray = sorted({t.index for t in transitions} - set(truth) - set(refused))
    if stray:
        return [finding.skipped(
            ENGINE, invariant, world,
            "the engine emitted transition indices %s with no corresponding "
            "frame pair, so the oracle cannot line its evidence up with the "
            "engine's" % stray[:6],
            cause="evidence_not_alignable", stray=stray[:6])]

    subject = _mined_subject(world, transitions, invariant)
    if subject is not None:
        return [subject]

    out: List[finding.Finding] = []
    unread: List[int] = []
    for rule in result.all_rules:
        for index in sorted(rule.support):
            if index not in truth:
                unread.append(index)
                continue
            action = actions[index] if index < len(actions) else None
            claimed = _claimed_delta(rule, action)
            actual = truth[index]
            if claimed is UNRESOLVED:
                unread.append(index)
                continue
            if claimed is None:
                if actual.type != motion.NONE:
                    out.append(finding.violated(
                        ENGINE, invariant, world,
                        "rule %s claims effect %r on transition %d, but the "
                        "frames show the mover displaced by %s"
                        % (rule.name, rule.effect.type, index, (actual.delta,)),
                        rule=rule.name, transition=index,
                        claimed=rule.effect.as_json(), actual_type=actual.type,
                        actual_delta=list(actual.delta)))
                    return out
                continue
            if actual.type != motion.MOVE or actual.delta != claimed:
                out.append(finding.violated(
                    ENGINE, invariant, world,
                    "rule %s claims the mover moves by %s on transition %d "
                    "(action %r), but the frames show %s"
                    % (rule.name, list(claimed), index, action,
                       "no motion" if actual.type == motion.NONE
                       else "a displacement of %s" % (list(actual.delta),)),
                    rule=rule.name, transition=index, action=action,
                    claimed=rule.effect.as_json(),
                    claimed_delta=list(claimed), actual_type=actual.type,
                    actual_delta=list(actual.delta)))
                return out
            destination = getattr(rule.effect, "to", None)
            if destination is not None and tuple(destination) != actual.to:
                out.append(finding.violated(
                    ENGINE, invariant, world,
                    "rule %s claims the mover lands at %s on transition %d, "
                    "but the frames put it at %s"
                    % (rule.name, list(destination), index, list(actual.to)),
                    rule=rule.name, transition=index,
                    claimed=rule.effect.as_json(),
                    claimed_to=list(destination), actual_to=list(actual.to)))
                return out

    if unread and not out:
        out.append(finding.skipped(
            ENGINE, invariant, world,
            "%d of %d supported transition(s) could not be read as one rigid "
            "mover translation, so their effects were not judged: %s"
            % (len(unread), sum(len(r.support) for r in result.all_rules),
               refused.get(unread[0], "no reason recorded")),
            cause="effects_not_readable_as_translation",
            unreadable=sorted(set(unread))[:6]))
    return out


def rules_fire_on_the_action_they_name(world: Any) -> List[finding.Finding]:
    """`rule.action` is the action really taken at every transition it claims.

    `mine()` groups transitions by `(action, effect.key())` and files the group
    under `members[0].action`, so a rule naming an action is asserting that the
    whole group shares it. The published `action` field is what a manual hangs
    the rule off; a rule filed under the wrong one is a true statement about the
    world attached to the wrong lever.

    Lifted rules are exempt by their own definition — `lift()` sets
    `action = "?dir"` precisely because the members disagree — so the check runs
    only where the named action is one the world can take.
    """
    invariant = "rules_fire_on_the_action_they_name"
    try:
        result, _transitions, _split = _mine(world)
    except (NoSeparatingGuard, Unminable) as exc:
        return _skip_no_guard(world, invariant, exc)

    subject = _mined_subject(world, _transitions, invariant)
    if subject is not None:
        return [subject]

    actions = world.action_list
    out: List[finding.Finding] = []
    for rule in result.all_rules:
        if rule.action not in DELTA:
            continue                    # the direction variable; nothing named
        for index in sorted(rule.support):
            if index >= len(actions):
                continue
            if actions[index] != rule.action:
                out.append(finding.violated(
                    ENGINE, invariant, world,
                    "rule %s is filed under action %r but transition %d, which "
                    "it claims, took action %r"
                    % (rule.name, rule.action, index, actions[index]),
                    rule=rule.name, transition=index,
                    claimed_action=rule.action, actual_action=actions[index]))
                return out
    return out


def _choose(n: int, k: int) -> int:
    out = 1
    for i in range(k):
        out = out * (n - i) // (i + 1)
    return out


INVARIANTS = {
    "frontier_guards_are_consistent": frontier_guards_are_consistent,
    "frontier_is_complete_to_size": frontier_is_complete_to_size,
    "applicable_equals_support": applicable_equals_support,
    "guards_partition_the_evidence": guards_partition_the_evidence,
    "effects_agree_with_the_evidence": effects_agree_with_the_evidence,
    "rules_fire_on_the_action_they_name": rules_fire_on_the_action_they_name,
}


def check(world: Any) -> List[finding.Finding]:
    return finding.run_invariants(ENGINE, world, INVARIANTS)
