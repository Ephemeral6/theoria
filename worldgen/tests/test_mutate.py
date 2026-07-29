"""Properties of the mutation layer, and the two disciplines it can breach.

Three things here are not ordinary unit tests and are the reason the file
exists:

* **the knob table has to be true.**  `mutate.KNOBS` claims eleven parameters
  are semantic — that some mechanism branches on each of them.  A table of
  claims nothing exercises is a comment, and the whole point of declaring the
  parameterisation was that it becomes enumerable rather than believed.  So
  every knob is perturbed on a world that carries it and has to change either
  the transition function or the initial state;
* **the read licence has to hold.**  `spec.json` goes on the sheet.  W-1540
  already shipped a leak of exactly this shape — the ids `t2-unsolvable-nodoor`
  and `t1-walk-maze` put *unsolvable* and *walk*, both live answers, in front of
  the examinee — so a mutant's open files are checked against an answer
  alphabet, and against the name of its own base;
* **the detection latency has to be right.**  It is computed by a product BFS
  with a pruning rule (diverged pairs are not expanded) that is easy to get
  subtly wrong, and a wrong latency is not visibly wrong: it is a plausible
  small integer.  So it is cross-checked against an exhaustive enumeration of
  every action sequence up to that depth, which is a different algorithm and
  shares no code with the one it checks.
"""

import json
import os
import re

import pytest

from worldgen import build, mutate
from worldgen.core import truth
from worldgen.core.types import ACTIONS
from worldgen.core.world import FORBIDDEN_RULE, GridWorld
from worldgen.generate import BY_ID, CATALOGUE
from worldgen.tests import support

MUTANTS = tuple(sorted(mutate.MUTATIONS, key=lambda e: e.variant_id))
MUTANT_IDS = tuple(e.variant_id for e in MUTANTS)

#: Every word an item's answer could be.  A mutant's open files may contain none
#: of them.  Deliberately over-broad: a false positive here costs one rename.
ANSWER_WORDS = (
    "solvable", "unsolvable", "latch", "toggle", "forbid", "forbidden",
    "walk", "maze", "portal", "push", "switch", "door", "token", "lock",
    "cycler", "fragile", "gravity", "polarity", "reversible", "irreversible",
    "guard", "mutate", "mutant", "variant", "dest", "net", "phase",
)


# ------------------------------------------------------------------- the knobs

def _worlds_carrying(knob: mutate.Knob):
    if knob.scope == "world":
        return [spec for spec in CATALOGUE if spec.flag(knob.prop) is not None]
    return [spec for spec in CATALOGUE
            if any(e.kind == knob.kind for e in spec.entities)]


def _behaviour(world: GridWorld):
    """The whole of what a world does, as a hashable value."""
    return (world.initial().key(),
            tuple((s.key(), a) + (world.explain(s, a)[0].key(),
                                  world.explain(s, a)[1])
                  for s in world.reachable() for a in ACTIONS))


@pytest.mark.parametrize("knob", mutate.KNOBS, ids=lambda k: "%s.%s" % (k.kind or "world", k.prop))
def test_every_declared_knob_is_read_by_its_mechanism(knob):
    """Perturbing the knob changes what the world does.

    `KNOBS` is the declaration that closed the gap GAPS.md named, and its whole
    value is that it is enumerable and checkable rather than asserted. A knob
    nothing branches on is a knob the mutation layer would happily turn, and
    every metric computed off that turn would read as "the change was
    undetectable" — the one answer this corpus must never fabricate.
    """
    if knob.scope == "world":
        spec = BY_ID["t1-walk-maze"]
        before = _behaviour(GridWorld(spec))
        after = _behaviour(GridWorld(mutate._apply_one(
            spec, {"op": "forbid_action", "action": knob.values[0]})))
        assert before != after, "%s is inert" % knob.prop
        return

    carriers = _worlds_carrying(knob)
    assert carriers, "no catalogue world carries a %s" % knob.kind

    if knob.unexercisable:
        pytest.skip("declared unexercisable: %s" % knob.unexercisable)

    # One entity at a time, then every entity of the kind at once. The second
    # arm is not laxity: a portal pair's `mode` cannot legally be changed on one
    # mouth (`_links` refuses a pair that mixes modes), so a single-entity
    # perturbation would report the knob inert when it is the opposite —
    # `t2-portal-pair` and `t2-portal-paired` are two catalogue worlds that
    # differ in nothing else.
    for spec in carriers:
        before = _behaviour(GridWorld(spec))
        entities = [e for e in spec.entities if e.kind == knob.kind]
        for group in [[e] for e in entities] + ([entities] if len(entities) > 1 else []):
            current = group[0].prop(knob.prop)
            if any(_norm(e.prop(knob.prop)) != _norm(current) for e in group):
                continue
            for candidate in _candidates(knob, spec, group[0], current):
                try:
                    moved = spec
                    for entity in group:
                        moved = mutate._apply_one(moved, {
                            "op": "set_prop", "kind": knob.kind,
                            "cell": entity.cell, "prop": knob.prop,
                            "from": current, "to": candidate})
                    after = _behaviour(GridWorld(moved))
                except Exception:                              # noqa: BLE001
                    continue       # an illegal value for this world; try another
                if after != before:
                    return
    pytest.fail(
        "%s.%s is declared a semantic knob but no legal value of it changes any "
        "world that carries one" % (knob.kind, knob.prop))


def _norm(value):
    return mutate._norm(value)


def test_the_unexercisable_knobs_reason_is_itself_checked():
    """`portal.pair`'s exemption says relabelling both mouths changes nothing.

    An exemption is a claim, so it is asserted rather than accepted. If a world
    with four mouths ever ships, this test starts failing and the exemption has
    to be withdrawn — which is the right way round.
    """
    exempt = [k for k in mutate.KNOBS if k.unexercisable]
    assert exempt, "no knob is exempt; delete this test with the last exemption"
    spec = BY_ID["t2-portal-pair"]
    mouths = [e for e in spec.entities if e.kind == "portal"]
    assert len(mouths) == 2, "the exemption's premise no longer holds"
    moved = spec
    for entity in mouths:
        moved = mutate._apply_one(moved, {
            "op": "set_prop", "kind": "portal", "cell": entity.cell,
            "prop": "pair", "from": "p", "to": "zz"})
    assert _behaviour(GridWorld(moved)) == _behaviour(GridWorld(spec))


def _candidates(knob, spec, entity, current):
    if knob.values:
        return [v for v in knob.values if v != current]
    if knob.prop in ("net", "pair"):
        return ["zz"]
    if knob.prop == "k":
        return [1, 2, 4]
    if knob.prop in ("open_phase", "phase0"):
        return [1, 2]
    if knob.prop == "dest":
        floors = [(r, c) for r in range(spec.height) for c in range(spec.width)
                  if not spec.is_wall((r, c)) and (r, c) != tuple(current or ())]
        return floors[:6]
    return []


# ------------------------------------------------------------ the read licence

@pytest.mark.parametrize("edit", MUTANTS, ids=MUTANT_IDS)
def test_a_mutant_spec_carries_no_story(edit):
    """`variant_of`, `variant_delta` and `notes` are blank on a mutant.

    Every other world in the factory fills all three in, which is why this is a
    test rather than an accident waiting to be re-introduced: the fields are
    exactly where a helpful future edit would put "the switch is now a latch",
    and `spec.json` is open.
    """
    spec = edit.spec()
    assert spec.variant_of is None
    assert spec.variant_delta == ""
    assert spec.notes == ""


@pytest.mark.parametrize("edit", MUTANTS, ids=MUTANT_IDS)
def test_a_mutant_id_is_an_opaque_handle(edit):
    assert re.fullmatch(r"v-[0-9a-f]{8}", edit.variant_id), edit.variant_id
    lowered = edit.variant_id.lower()
    for word in ANSWER_WORDS:
        assert word not in lowered, (
            "%s contains the answer word %r" % (edit.variant_id, word))


@pytest.mark.parametrize("edit", MUTANTS, ids=MUTANT_IDS)
def test_a_mutants_open_files_carry_no_label_that_names_the_edit(edit):
    """The regression for W-1540's leak, scoped to what it can actually cover.

    Both open files are read (`exam/papers/worldgen_port.py:OPEN_FILES`), which
    an earlier version of this test claimed and did not do — it opened
    `spec.json` only, while its name and docstring said otherwise.

    Four things must not appear and each did, in a draft: the base's id, the
    edit's transparent name, the edit family, and — the one an adversarial
    review found — the base's `seed`, which is unique across the twenty and so
    identified the base of all fifteen mutants exactly.

    What this deliberately does **not** assert, because asserting it would be
    false comfort: that the open files hide the edit. They do not.
    `entities[].props` is the rule set in words, `open_world()` rebuilds the
    `GridWorld` from it, the base's spec is open too, and a mutant may not move
    the geometry — so a two-file diff is the answer in plaintext. That is
    unfixable while the port works this way, and it is written up in
    `mutate.py`'s docstring and `RUN_STATE.md §the open spec` rather than
    asserted away here. An earlier draft ran `ANSWER_WORDS` over these files and
    every mutant failed, which is the honest reading: the alphabet belongs on
    the id, and the id is where it is applied.
    """
    dirname = os.path.join(mutate.OUT, edit.variant_id)
    if not os.path.exists(dirname):
        pytest.skip("catalogue not built")
    with open(os.path.join(dirname, "spec.json"), encoding="utf-8") as handle:
        blob = json.load(handle)
    with open(os.path.join(dirname, "raw_trace.jsonl"), encoding="utf-8") as handle:
        trace = handle.read().lower()
    text = json.dumps(blob, sort_keys=True).lower()

    for corpus, where in ((text, "spec.json"), (trace, "raw_trace.jsonl")):
        assert edit.base.lower() not in corpus, where
        assert edit.transparent_name.lower() not in corpus, where
        assert edit.edit_family not in corpus, where
    assert blob["intended_solvable"] is None, (
        "%s publishes the verdict in an open file" % edit.variant_id)
    assert blob["variant_of"] is None and blob["variant_delta"] == ""
    assert blob["notes"] == ""
    assert blob["seed"] == 0, (
        "%s carries its base's seed, which is unique across the twenty and "
        "therefore names the base" % edit.variant_id)
    assert blob["world_id"] == edit.variant_id


def test_no_mutant_seed_matches_a_catalogue_seed():
    """The concrete form of the leak: seeds are unique across the twenty."""
    catalogue = {spec.seed for spec in CATALOGUE}
    assert len(catalogue) == len(CATALOGUE), "seeds are no longer unique"
    for edit in MUTANTS:
        assert edit.spec().seed not in catalogue, edit.variant_id


def test_the_descriptor_file_is_the_only_place_the_linkage_lives():
    path = os.path.join(mutate.OUT, "MUTATIONS.json")
    if not os.path.exists(path):
        pytest.skip("catalogue not built")
    with open(path, encoding="utf-8") as handle:
        blob = json.load(handle)
    assert blob["read_licence"].startswith("scoring-only")
    for row in blob["mutations"]:
        assert row["base_world_id"] in BY_ID
        assert row["transparent_name"]


# ------------------------------------------------------------- the corpus shape

@pytest.mark.parametrize("family", mutate.EDIT_FAMILIES)
def test_each_edit_family_has_at_least_two_instances(family):
    """The item's bar, as a check rather than as a count in a report."""
    instances = [e for e in MUTANTS if e.edit_family == family]
    assert len(instances) >= 2, "%s has %d instance(s)" % (family, len(instances))


def test_variant_ids_are_unique_and_stable():
    assert len(set(MUTANT_IDS)) == len(MUTANT_IDS)
    # Recomputed from the operators, so a corpus reordering cannot move an id.
    for edit in MUTANTS:
        assert edit.variant_id == mutate.Edit(
            base=edit.base, edit_family=edit.edit_family,
            operators=edit.operators, transparent_name="different",
            justification="different").variant_id


@pytest.mark.parametrize("edit", MUTANTS, ids=MUTANT_IDS)
def test_a_mutant_keeps_the_legend_and_the_geometry(edit):
    """A controlled pair varies one rule, not the picture.

    Checked here as well as in `Edit.spec` because the refusal there is what
    makes the detection latency mean anything: a palette shift would make every
    frame differ for a reason that has nothing to do with the edit, and every
    mutant would read as detectable at action zero.
    """
    base, mutant = BY_ID[edit.base], edit.spec()
    assert mutant.colors == base.colors
    assert mutant.layout == base.layout
    assert mutant.agent_start == base.agent_start
    assert mutant.goal == base.goal


def test_the_corpus_contains_an_undetectable_variant():
    """`exam.papers.adaptation.build()` refuses a paper without one.

    Its reason is worth restating where the corpus is defined: without an
    undetectable variant every item rewards claiming a detection, and an
    examinee that reports a latency for a change it cannot have observed scores
    the same as one that measured.
    """
    path = os.path.join(mutate.OUT, "MUTATIONS.json")
    if not os.path.exists(path):
        pytest.skip("catalogue not built")
    with open(path, encoding="utf-8") as handle:
        blob = json.load(handle)
    assert blob["totals"]["observationally_equivalent"], (
        "no variant in the corpus is observationally equivalent to its base")


def test_the_corpus_flips_a_verdict_in_both_directions():
    path = os.path.join(mutate.OUT, "MUTATIONS.json")
    if not os.path.exists(path):
        pytest.skip("catalogue not built")
    with open(path, encoding="utf-8") as handle:
        blob = json.load(handle)
    flips = [r for r in blob["mutations"] if r["collateral"]["verdict_flipped"]]
    directions = {(r["collateral"]["base_verdict"], r["collateral"]["verdict"])
                  for r in flips}
    assert ("solvable", "unsolvable") in directions
    assert ("unsolvable", "solvable") in directions


# ------------------------------------------------------------- the operators

def test_an_operator_with_a_stale_from_is_refused():
    """A silent no-op mutation would ship as a variant pair with an empty diff."""
    with pytest.raises(mutate.MutationError):
        mutate._apply_one(BY_ID["t1-switch-toggle"], {
            "op": "set_prop", "kind": "switch", "cell": (4, 1),
            "prop": "mode", "from": "latch", "to": "toggle"})


def test_an_operator_on_an_undeclared_prop_is_refused():
    with pytest.raises(mutate.MutationError):
        mutate._apply_one(BY_ID["t1-switch-toggle"], {
            "op": "set_prop", "kind": "switch", "cell": (4, 1),
            "prop": "colour", "from": None, "to": 3})


def test_an_operator_on_a_missing_entity_is_refused():
    with pytest.raises(mutate.MutationError):
        mutate._apply_one(BY_ID["t1-switch-toggle"], {
            "op": "set_prop", "kind": "switch", "cell": (0, 0),
            "prop": "mode", "from": "toggle", "to": "latch"})


def test_a_second_forbidden_action_is_refused():
    once = mutate._apply_one(BY_ID["t1-walk-maze"],
                             {"op": "forbid_action", "action": "UP"})
    with pytest.raises(mutate.MutationError):
        mutate._apply_one(once, {"op": "forbid_action", "action": "DOWN"})


# --------------------------------------------------------- the forbidden action

@pytest.mark.parametrize("world_id", support.WORLD_IDS)
def test_the_new_knob_is_inert_across_the_whole_catalogue(world_id):
    """None of the twenty carries it, so none of their artefacts can have moved."""
    assert support.world(world_id).forbidden == frozenset()


def test_a_forbidden_action_is_refused_and_changes_nothing_else():
    base = GridWorld(BY_ID["t1-walk-maze"])
    mutant = GridWorld(mutate._apply_one(BY_ID["t1-walk-maze"],
                                         {"op": "forbid_action", "action": "UP"}))
    for state in base.reachable():
        nxt, rule = mutant.explain(state, "UP")
        assert rule == FORBIDDEN_RULE
        assert nxt == state
        for action in ("DOWN", "LEFT", "RIGHT"):
            assert mutant.explain(state, action) == base.explain(state, action)


def test_a_forbidden_action_is_not_the_same_rule_as_a_wall():
    """Tagged apart even where the target is a wall, and observationally alike.

    Both matter and they pull in opposite directions. The *tags* must differ, or
    the ground truth cannot say which of the two refused the move. The *frames*
    must not, or forbidding a command would be visible from the start cell in
    every world and the detection latency would measure nothing.
    """
    spec = mutate._apply_one(BY_ID["t1-walk-maze"],
                             {"op": "forbid_action", "action": "UP"})
    mutant = GridWorld(spec)
    base = GridWorld(BY_ID["t1-walk-maze"])
    start = base.initial()                       # (1,1); UP is a wall from here
    assert base.explain(start, "UP")[1] == "blocked_by_wall"
    assert mutant.explain(start, "UP")[1] == FORBIDDEN_RULE
    assert base.render(base.explain(start, "UP")[0]) \
        == mutant.render(mutant.explain(start, "UP")[0])


def test_the_forbidden_rule_reaches_the_ground_truth():
    spec = mutate._apply_one(BY_ID["t1-walk-maze"],
                             {"op": "forbid_action", "action": "UP"})
    world = GridWorld(spec)
    names = [r["name"] for r in truth.rule_table(world)]
    assert FORBIDDEN_RULE in names
    corr = truth.rule_correspondence(world)
    assert corr["agrees"], corr
    walk = next(r for r in truth.rule_table(world) if r["name"] == "walk")
    assert "UP" in walk["when"], (
        "the base rules still claim to fire on every direction: %r" % walk["when"])


def test_an_unknown_forbidden_action_is_refused_at_validation():
    from worldgen.core.spec import validate
    spec = BY_ID["t1-walk-maze"]
    bad = mutate._replace(spec, flags=(("forbidden_action", "SIDEWAYS"),))
    with pytest.raises(ValueError):
        validate(bad)


# ------------------------------------------------------- the detection latency

def _brute_force_earliest(base: GridWorld, mutant: GridWorld, cap: int):
    """Every action sequence up to `cap`, in length order.  No shared code with
    `earliest_detection` — that is the point of it being here."""
    def frames(world, seq):
        state = world.initial()
        out = [(tuple(tuple(r) for r in world.render(state)), world.is_win(state))]
        for action in seq:
            state = world.step(state, action)
            out.append((tuple(tuple(r) for r in world.render(state)),
                        world.is_win(state)))
        return out

    if frames(base, ())[0] != frames(mutant, ())[0]:
        return 0
    frontier = [()]
    for depth in range(1, cap + 1):
        nxt = []
        for seq in frontier:
            for action in ACTIONS:
                candidate = seq + (action,)
                if frames(base, candidate)[-1] != frames(mutant, candidate)[-1]:
                    return depth
                nxt.append(candidate)
        frontier = nxt
    return None


@pytest.mark.parametrize("variant_id", [
    "v-7048ee5e",        # t1-walk-maze, forbid UP        — expected 2
    "v-ce732813",        # t1-walk-maze, forbid DOWN      — expected 1
    "v-eb4c5810",        # t1-cycler-gate, forbid UP      — expected 1
    "v-a3446614",        # t1-portal-oneway, dest moved   — expected 4
])
def test_earliest_detection_agrees_with_an_exhaustive_enumeration(variant_id):
    edit = mutate.MUTANT_BY_ID[variant_id]
    base = GridWorld(BY_ID[edit.base])
    mutant = GridWorld(edit.spec())
    fast = mutate.earliest_detection(base, mutant)
    slow = _brute_force_earliest(base, mutant, cap=(fast["actions"] or 0) + 1)
    assert fast["actions"] == slow, (
        "%s: product BFS says %r, exhaustive enumeration says %r"
        % (variant_id, fast["actions"], slow))


def test_the_witness_sequence_really_witnesses():
    """The reported path is replayed rather than trusted."""
    for edit in MUTANTS:
        base = GridWorld(BY_ID[edit.base])
        mutant = GridWorld(edit.spec())
        found = mutate.earliest_detection(base, mutant)
        if found["actions"] is None:
            continue
        sb, sm = base.initial(), mutant.initial()
        for action in found["witness"]:
            sb, sm = base.step(sb, action), mutant.step(sm, action)
        assert base.render(sb) != mutant.render(sm) \
            or base.is_win(sb) != mutant.is_win(sm), edit.variant_id


def test_the_undetectable_variant_is_undetectable_on_the_whole_graph():
    """Checked directly, not read back off the number that claims it.

    The product search prunes, so a bug in the pruning would report `null` for a
    variant that does diverge. This walks both reachable sets instead.
    """
    ids = [e.variant_id for e in MUTANTS
           if mutate.earliest_detection(GridWorld(BY_ID[e.base]),
                                        GridWorld(e.spec()))["actions"] is None]
    assert ids, "the corpus has no undetectable variant to check"
    for variant_id in ids:
        edit = mutate.MUTANT_BY_ID[variant_id]
        base = GridWorld(BY_ID[edit.base])
        mutant = GridWorld(edit.spec())
        assert base.initial() == mutant.initial()
        states = set(s.key() for s in base.reachable())
        assert states == set(s.key() for s in mutant.reachable())
        for state in base.reachable():
            for action in ACTIONS:
                assert base.explain(state, action)[0] \
                    == mutant.explain(state, action)[0], (variant_id, state, action)
                assert base.render(state) == mutant.render(state)


# ------------------------------------------------------------- the collateral

@pytest.mark.parametrize("edit", MUTANTS, ids=MUTANT_IDS)
def test_falsified_rules_are_recomputed_independently(edit):
    base = GridWorld(BY_ID[edit.base])
    mutant = GridWorld(edit.spec())
    expected = set()
    for state in list(base.reachable()) + list(mutant.reachable()):
        for action in ACTIONS:
            nb, rb = base.explain(state, action)
            nm, rm = mutant.explain(state, action)
            if nb != nm or rb != rm:
                expected |= {rb, rm}
    row = mutate.describe(edit)
    assert set(row["collateral"]["rules_falsified"]) == expected


def test_claim_dependencies_cover_the_mechanism_that_declared_the_claim():
    """The regression for the false negative this graph shipped with.

    A door holds no state, so no rule writes `switch_door`'s slice on account of
    one, and `door_presence_tracks_net` came back depending on nothing a door
    edit could falsify — on a world with no switches, on nothing at all.
    """
    world = GridWorld(BY_ID["t2-unsolvable-nodoor"])
    deps = mutate.claim_dependencies(world)
    assert "blocked_by_door" in deps["claims"]["door_presence_tracks_net"]


@pytest.mark.parametrize("variant_id", ["v-29ace70e", "v-57cfb2b4"])
def test_the_edit_family_claim_is_checked_against_the_measurement(variant_id):
    """A mislabelled family fails, so the label is a claim and not a caption.

    `v-57cfb2b4` is the case the first version of the check let through. It
    opens two doors permanently, so `blocked_by_door` stops firing — and the
    check counted a rule that merely **stopped existing** as one that had lost
    re-witnessability, which is not the same event and is not a reversibility
    change at all. A rule that is gone is `rules_falsified`'s business.
    """
    honest = mutate.MUTANT_BY_ID[variant_id]              # both real guard changes
    assert honest.edit_family == "change_guard"
    lying = mutate.Edit(base=honest.base,
                        edit_family="reversible_to_irreversible",
                        operators=honest.operators,
                        transparent_name="mislabelled",
                        justification="mislabelled",
                        intended_solvable=honest.intended_solvable)
    base = GridWorld(BY_ID[lying.base])
    mutant = GridWorld(lying.spec())
    problems = mutate.check_family(
        lying, base, mutant,
        mutate._stamp(base), mutate._stamp(mutant))
    assert problems, "a guard change passed as a reversibility change"


@pytest.mark.parametrize("edit", MUTANTS, ids=MUTANT_IDS)
def test_no_rule_claims_a_transition_a_forbidden_action_prevents(edit):
    """Every rule's antecedent is evaluated, not read.

    The shipped `ground_truth.json` for a forbidden-action world used to
    contradict itself: `action_forbidden` said "act=D and D is UP → nothing
    changes" while `advance_cycler` still said "act=D and the target holds a
    shut cycler → the phase advances", and at one reachable state both
    antecedents held. `rule_correspondence` compares rule *names* against
    `Outcome.rule` tags and is blind to prose, so no gate saw it.

    Checked structurally rather than by re-reading the sentence: in a world that
    forbids a command, no rule but `action_forbidden` may still open with the
    unconditional `act=D and`.
    """
    world = GridWorld(edit.spec())
    if not world.forbidden:
        pytest.skip("no forbidden action in this mutant")
    for rule in truth.rule_table(world):
        if rule["name"] == FORBIDDEN_RULE:
            continue
        assert not rule["when"].startswith(truth.ACTION_PREFIX), (
            "%s: rule %r still claims to fire on every direction: %r"
            % (edit.variant_id, rule["name"], rule["when"]))
        assert "is not `" in rule["when"], (
            "%s: rule %r is action-triggered but unguarded: %r"
            % (edit.variant_id, rule["name"], rule["when"]))


def test_a_stalled_repair_walk_reports_no_budget():
    """`v-eb4c5810`'s classes are individually reachable and jointly not.

    UP is forbidden and the cycler's phase is absorbing at `open_phase`, so
    once the gate is open the agent can neither return to a shut phase nor go
    back up. An earlier version broke out of the greedy loop and published the
    truncated count as "the walk that witnesses every class" and as an upper
    bound on the optimal — a finite number bounding nothing.
    """
    edit = mutate.MUTANT_BY_ID["v-eb4c5810"]
    repair = mutate.greedy_witness_budget(GridWorld(BY_ID[edit.base]),
                                          GridWorld(edit.spec()))
    assert repair["stalled_on"], "this variant is supposed to stall"
    assert repair["greedy_actions"] is None
    assert repair["greedy_actions_before_stall"] is not None
    assert "bounds nothing" in repair["bound"]


@pytest.mark.parametrize("edit", MUTANTS, ids=MUTANT_IDS)
def test_the_repair_budget_walk_is_replayable_where_it_completes(edit):
    """Where a budget is published, the walk that spends it exists."""
    base, mutant = GridWorld(BY_ID[edit.base]), GridWorld(edit.spec())
    repair = mutate.greedy_witness_budget(base, mutant)
    if repair["greedy_actions"] is None:
        assert repair["stalled_on"]
        return
    assert repair["greedy_actions"] >= 0
    assert repair["classes_witnessable_in_mutant"] \
        == repair["classes_total"] - len(repair["classes_only_in_base"])


def test_a_no_op_edit_is_refused():
    """The refusal `_apply_one.__doc__` promises, which it did not make.

    A no-op ships as a variant pair with an empty diff, and every metric
    computed off it reads as "the change was undetectable" — the one answer this
    corpus must never fabricate, and the corpus is required to contain exactly
    one genuine instance of.
    """
    with pytest.raises(mutate.MutationError):
        mutate._apply_one(BY_ID["t1-tokens-lock"], {
            "op": "set_prop", "kind": "lock", "cell": (3, 4),
            "prop": "k", "from": 3, "to": 3})
    with pytest.raises(mutate.MutationError):
        mutate._apply_one(BY_ID["t2-portal-pair"], {
            "op": "move_entity", "kind": "portal", "from": (4, 7), "to": (4, 7)})


def test_move_entity_is_confined_to_portal_mouths():
    """Otherwise it is a change of the picture wearing a rule edit's label."""
    with pytest.raises(mutate.MutationError):
        mutate._apply_one(BY_ID["t1-tokens-lock"], {
            "op": "move_entity", "kind": "token", "from": (1, 3), "to": (1, 2)})


# ---------------------------------------------------------------- integration

def test_the_mutants_have_their_own_roster_and_stay_out_of_the_catalogue_index():
    """`INDEX.json` is the twenty; `MUTATIONS.json → roster` is the fifteen.

    The obvious arrangement was to put the mutants in `INDEX.json`, because
    `exam/guard.py:generated_worlds()` admits an id iff it is a row there. Doing
    that breaks five tests in `exam/`, which asserts the roster is exactly
    twenty and offers every row to a paper builder that raises on a three-state
    world. Admission is `exam/`'s call in `exam/`'s territory; the roster is
    supplied here in the same shape so that making it is one line.
    """
    index_path = os.path.join(mutate.OUT, "INDEX.json")
    mut_path = os.path.join(mutate.OUT, "MUTATIONS.json")
    if not os.path.exists(mut_path):
        pytest.skip("catalogue not built")
    with open(index_path, encoding="utf-8") as handle:
        index = json.load(handle)
    with open(mut_path, encoding="utf-8") as handle:
        blob = json.load(handle)

    catalogue = {row["world_id"] for row in index["worlds"]}
    assert catalogue == set(support.WORLD_IDS)
    assert not (catalogue & set(MUTANT_IDS))

    roster = blob["roster"]
    assert {row["world_id"] for row in roster["worlds"]} == set(MUTANT_IDS)
    # Same shape, so `build.gate_failures` judges it by the identical checks.
    for key, _why in build.GATES:
        assert key in roster["totals"], key
    assert build.gate_failures(roster) == []


@pytest.mark.parametrize("variant_id", MUTANT_IDS)
def test_a_mutant_ships_the_six_files_the_port_opens(variant_id):
    dirname = os.path.join(mutate.OUT, variant_id)
    if not os.path.exists(dirname):
        pytest.skip("catalogue not built")
    for name in ("spec.json", "raw_trace.jsonl", "ground_truth.json",
                 "GROUND_TRUTH.md", "coverage.json", "reversibility.json"):
        assert os.path.exists(os.path.join(dirname, name)), name


def test_no_orphan_mutant_directory_survives_a_build():
    """A `v-*` directory nothing describes is a world nothing gated.

    Its id is a digest of its operators, so revising an operator strands the old
    directory rather than updating it, and the stray is a complete six-file
    world that is missing from `INDEX.json` and therefore never met a gate. Two
    of them appeared in this run's own working tree.
    """
    if not os.path.isdir(mutate.OUT):
        pytest.skip("catalogue not built")
    on_disk = {n for n in os.listdir(mutate.OUT)
               if n.startswith("v-")
               and os.path.isdir(os.path.join(mutate.OUT, n))}
    assert on_disk == set(MUTANT_IDS), (
        "orphaned: %s" % sorted(on_disk - set(MUTANT_IDS)))


def test_mutants_are_not_members_of_the_catalogue():
    """`tests/test_catalogue_invariants.py` asserts the catalogue ships exactly
    one unsolvable world, and three mutants are unsolvable on purpose."""
    assert not (set(MUTANT_IDS) & set(support.WORLD_IDS))
