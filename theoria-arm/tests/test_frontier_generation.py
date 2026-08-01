"""R2's change -- the frontier by generation. Offline; no key, no network, no model.

The measurement is in `runs/20260801T0900Z-R2-frontier-by-generation/`, and it
says something narrower and worse than "the probes were badly chosen":

* the ablation family is closed downward under clause deletion, so it can never
  contain a mechanism the manual lacks -- that is a property of the *family*,
  not of any run;
* frontier width was **2 distinct predictions on every one of the 52** completed
  probes of 2026-07-31, whatever the hypothesis count said;
* **35 of the 52** were designed from a state the world had already left
  (`inert`'s prediction, which is the anchor every hypothesis is a successor
  of, did not equal the world's own `before_hash`), and all 35 landed off the
  frontier;
* of the 17 that *were* anchored, 12 missed by a delta containing exactly one
  cell that had never changed before -- a board cell, on which the arm seats no
  object instance and about which no rule in this grammar can speak.

So this file has two jobs and they are equally load-bearing. The first is that
`generated` can contain what `ablation` structurally cannot. The second is that
`ablation` -- the default -- keeps the same frontier: same hypotheses, same
order, same ids, so the switch still has a real control.

**The second job was narrower after R2-1, and the narrowing is deliberate.**
It used to be "`ablation` did not move a byte". It no longer holds for the
report or for the arm's behaviour: `report["anchor"]` is now written on both
paths and a drifted probe is refused on both, because the anchor guarded
nothing while it lived behind a non-default flag -- the four paid legs never
took it. The frontier half of the guarantee is untouched and still tested.
See `D-R2-002`, and `test_the_default_switch_changes_nothing_except_the_anchor
_reading` below, which carries the argument in full.

**Every check that can say no is watched saying it.** The generated frontier is
handed a world whose mechanism is outside every generator, and asserted
vacuous; `next_unnameable_cell` is handed a scattered history and asserted
silent; the environment switch is handed four near-misses and asserted off. A
frontier builder that has only ever been seen to succeed has not been shown to
be a frontier builder.
"""

import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(HERE)
if ARM not in sys.path:
    sys.path.insert(0, ARM)

import _bootstrap                                     # noqa: E402,F401

from inner import probe as probe_beat                 # noqa: E402
from inner.loop import TheoriaArm                     # noqa: E402
from inner.probe import FrontierConfig                # noqa: E402
from world.frames import FrameStore, Step, grid_hash  # noqa: E402


# ---------------------------------------------------------------- a world
#
# A 5x5 world with two independent mechanisms, one of which the manual can
# state and one of which it cannot:
#
#   * a marker at (0, c) that moves one column right on ACTION1 -- the manual
#     knows this and its `RULES`/`fired` report it;
#   * a burn that advances one cell along row 4 on every command, starting at
#     (4, 0) -- a cell that has never changed before it burns, so the arm can
#     seat no instance on it and no rule can name it. This is the meter of
#     `20260731T1430Z-...-r3`, shrunk to fit in a test.
#
# The manual below is a plain dict namespace, not a compiled `theory.dsl`,
# because what is under test is `build_hypotheses` -- which reads `render`,
# `step`, `fired` and `RULES` and nothing else.

SIZE = 5


def _grid(marker_col, burned):
    g = [[0] * SIZE for _ in range(SIZE)]
    g[0][marker_col] = 6
    for c in range(burned):
        g[4][c] = 1
    return g


class _State:
    """What the manual thinks the world is: a marker column, and nothing else.

    It has no field for the burn, which is the point -- the manual cannot
    represent the mechanism, so no rule of it and no ablation of any rule of it
    can predict a burned cell.
    """

    def __init__(self, marker_col=0):
        self.marker_col = marker_col


def _namespace(rules=("advance",)):
    def render(state):
        return _grid(state.marker_col, 0)

    def step(state, action):
        kind, key = action
        if kind == "key" and key == 1 and "advance" in rules:
            return _State(min(state.marker_col + 1, SIZE - 1))
        return _State(state.marker_col)

    def fired(state, action):
        kind, key = action
        if kind == "key" and key == 1 and "advance" in rules:
            return ["advance__Marker_r0c%d" % state.marker_col]
        return []

    return {"render": render, "step": step, "fired": fired,
            "initial_state": lambda: _State(0),
            "RULES": [("advance__Marker_r0c%d" % c, None, None, None)
                      for c in range(SIZE)]}


def _store(marker_cols, burns):
    """A frame store whose burn advances one cell per step along row 4."""
    store = FrameStore()
    for idx, (col, burned) in enumerate(zip(marker_cols, burns)):
        store.add(Step(idx, "RESET" if idx == 0 else "ACTION1",
                       [_grid(col, burned)], state="NOT_FINISHED"))
    return store


def _observed(marker_col, burned):
    return grid_hash(_grid(marker_col, burned))


def _predict(hypotheses, state, action):
    return {h.id: h.predict(state, action) for h in hypotheses}


# =============================================== 1. the default did not move
def test_the_default_frontier_is_the_ablation_frontier():
    """`ablation` is 2026-07-31: same hypotheses, same order, same ids."""
    namespace = _namespace()
    plain = probe_beat.build_hypotheses(namespace)
    defaulted = probe_beat.build_hypotheses(namespace, frontier=FrontierConfig())
    assert [h.id for h in plain] == [h.id for h in defaulted]
    assert [h.id for h in plain] == ["manual", "inert", "without_advance"]


def test_a_store_present_changes_nothing_while_the_mode_is_ablation():
    """The evidence being *available* must not change the default frontier.

    `inner/loop.py` now passes the level store on every design call. If that
    argument leaked into the ablation path, every leg that left the switch off
    would silently be running a different arm -- and it would still be green,
    because the hypotheses it added would be plausible ones.
    """
    namespace = _namespace()
    store = _store([0, 1, 2], [0, 1, 2])
    state = _State(2)
    action = ("key", 1)
    without = _predict(probe_beat.build_hypotheses(namespace), state, action)
    with_store = _predict(
        probe_beat.build_hypotheses(namespace, store=store), state, action)
    with_both = _predict(
        probe_beat.build_hypotheses(namespace, frontier=FrontierConfig(),
                                    store=store), state, action)
    assert without == with_store == with_both


def test_the_default_switch_changes_nothing_except_the_anchor_reading():
    """**This guarantee was narrowed by R2-1, deliberately. Read the reason.**

    As written on 2026-08-01 this asserted the report was byte-identical with
    the switch at its default, and it was the second of this file's two jobs:
    `ablation` did not move a byte. R2-1 broke that half on purpose.

    Why it had to break. The anchor -- whether the state a design was ranked
    against is the frame the world is showing -- was computed only under
    `generated`, which is not the default, so on the four legs that were
    actually paid for it was never taken. 35 of their 52 probes were designed
    against a frame the world had left, and all 35 landed off-frontier. A
    reading that exists only behind a non-default flag cannot catch that, and
    an instrument that must be switched on to see the defect it was built for
    is the defect. So `report["anchor"]` is now written on both paths, and
    `loop.py` refuses a drifted probe on both paths. See `D-R2-002`.

    **What is unchanged, and it is the half that carried the knob's honesty:**
    the *frontier* does not move on the default -- same hypotheses, same order,
    same ids -- so `generated` still has a real control to be compared against.
    That property has its own test immediately above this one
    (`test_the_default_frontier_is_the_ablation_frontier` and the store/no-store
    equality), and it still passes untouched. This test now checks the
    surviving guarantee and says so in its name, rather than keeping a name
    that claims more than it checks.

    The two anchors below differ, and that is information rather than drift in
    the switch: `old` is called without a store, so there is no world frame to
    compare against and the reading is "no claim"; `new` has one.
    """
    import json                                        # noqa: PLC0415

    namespace = _namespace()
    store = _store([0, 1, 2], [0, 1, 2])
    state = _State(0)
    actions = [("key", 1), ("key", 2)]
    old = probe_beat.design(namespace, state, actions)
    new = probe_beat.design(namespace, state, actions,
                            frontier=FrontierConfig(), store=store)

    assert "frontier" not in old, "the generated block is still switched"
    assert "frontier" not in new

    old_anchor = old.pop("anchor")
    new_anchor = new.pop("anchor")
    assert json.dumps(old, sort_keys=True) == json.dumps(new, sort_keys=True), (
        "everything the design is ranked on is still byte-identical at the "
        "switch's default; only the anchor reading was added")

    assert old_anchor["world_hash"] is None
    assert old_anchor["drifted"] is False, "no store is not a claim about drift"
    assert new_anchor["drifted"] is True


# ==================================== 2. the switch is a positive whitelist
def test_the_environment_switch_is_a_positive_whitelist():
    for value in ("", "1", "true", "on", "banana", "GENERATED", "generated!",
                  "ablation", "generate", "generatedx"):
        assert FrontierConfig.from_env(
            {"THEORIA_FRONTIER": value}).mode == "ablation", value
    # Surrounding whitespace is stripped -- a shell that quotes the value
    # loosely should not silently leave a round measuring the wrong arm --
    # but nothing else is forgiven.
    for value in ("generated", " generated ", "generated\n"):
        assert FrontierConfig.from_env(
            {"THEORIA_FRONTIER": value}).mode == "generated", value
    assert FrontierConfig.from_env({}).mode == "ablation"


def test_an_arm_built_with_no_frontier_argument_is_on_ablation(tmp_path,
                                                               monkeypatch):
    monkeypatch.delenv("THEORIA_FRONTIER", raising=False)
    monkeypatch.delenv("THEORIA_PROBE_ECONOMY", raising=False)
    run = types.SimpleNamespace(dir=str(tmp_path), run=None, run_id="r-pytest")
    arm = TheoriaArm(env_base="http://127.0.0.1:1", run=run,
                     game_id="g50t-5849a774", offline=True)
    assert arm.frontier.mode == "ablation"
    assert arm.frontier.generated is False


def test_the_fourth_knob_is_independent_of_the_other_three(tmp_path,
                                                           monkeypatch):
    monkeypatch.delenv("THEORIA_FRONTIER", raising=False)
    monkeypatch.delenv("THEORIA_PROBE_ECONOMY", raising=False)
    run = types.SimpleNamespace(dir=str(tmp_path), run=None, run_id="r-pytest")
    arm = TheoriaArm(env_base="http://127.0.0.1:1", run=run,
                     game_id="g50t-5849a774", offline=True,
                     frontier=FrontierConfig(mode="generated"))
    assert arm.frontier.mode == "generated"
    assert arm.goal.protocol == "off"
    assert arm.probe_economy.enabled is False
    assert arm.desk_diet.name == "full"


# ============================== 3. what generation adds that ablation cannot
def test_the_ablation_family_is_closed_downward_and_cannot_reach_a_burn():
    """The structural claim, made executable.

    Every ablation predicts a successor whose delta from the manual's own
    rendering is a *subset* of the manual's delta -- suppressing a rule can
    only remove an effect. So no ablation, of any manual, can predict a cell
    the manual does not touch. The burn is such a cell.
    """
    namespace = _namespace()
    state = _State(2)
    action = ("key", 1)
    ablation = _predict(probe_beat.build_hypotheses(namespace), state, action)
    assert len(set(ablation.values())) == 2            # the measured width
    truth = _observed(3, 3)                            # marker moved, cell burned
    assert truth not in set(ablation.values())


def test_the_generated_frontier_contains_the_burn_the_ablation_family_cannot():
    namespace = _namespace()
    store = _store([0, 1, 2], [0, 1, 2])
    state = _State(2)
    action = ("key", 1)
    full = probe_beat.build_hypotheses(
        namespace, frontier=FrontierConfig(mode="generated"), store=store)
    ids = [h.id for h in full]
    for generated in ("world_inert", "world_anchored_manual",
                      "world_inert_plus_edge", "edge_advance"):
        assert generated in ids
    predictions = _predict(full, state, action)
    truth = _observed(3, 3)
    assert truth in set(predictions.values())
    assert predictions["edge_advance"] == truth


def test_generation_widens_the_frontier_past_two():
    """Width 2 was the measured constant across all 52 probes."""
    namespace = _namespace()
    store = _store([0, 1, 2], [0, 1, 2])
    state = _State(2)
    action = ("key", 1)
    ablation = _predict(probe_beat.build_hypotheses(namespace), state, action)
    generated = _predict(probe_beat.build_hypotheses(
        namespace, frontier=FrontierConfig(mode="generated"), store=store),
        state, action)
    assert len(set(ablation.values())) == 2
    assert len(set(generated.values())) >= 3


def test_at_least_three_generated_hypotheses_are_mutually_incompatible():
    """Three that disagree with each other on the same action, pairwise."""
    namespace = _namespace()
    store = _store([0, 1, 2], [0, 1, 2])
    generated = probe_beat.build_generated_hypotheses(namespace, store)
    predictions = _predict(generated, _State(2), ("key", 1))
    assert len(set(predictions.values())) >= 3


def test_the_report_names_the_generated_hypotheses_and_the_anchor():
    namespace = _namespace()
    store = _store([0, 1, 2], [0, 1, 2])
    report = probe_beat.design(namespace, _State(2), [("key", 1), ("key", 2)],
                               frontier=FrontierConfig(mode="generated"),
                               store=store)
    block = report["frontier"]
    assert block["mode"] == "generated"
    assert block["n_generated"] == len(block["generated"]) >= 3
    assert set(block["anchor"]) == {"anchor_hash", "world_hash", "drifted"}


# ================================================= 4. the anchor, and drift
def test_anchor_drift_says_no_when_the_manual_is_where_the_world_is():
    namespace = _namespace()
    store = _store([0, 1, 2], [0, 0, 0])               # no burns: manual is right
    assert probe_beat.anchor_drift(namespace, _State(2), store)["drifted"] is False


def test_anchor_drift_says_yes_when_the_manual_has_fallen_behind():
    """The 35-of-52 condition, reproduced.

    The manual's render carries no burn; the world's frame does. Every
    hypothesis the ablation builder makes is a successor of the first, so the
    experiment is about a frame the world left behind.
    """
    namespace = _namespace()
    store = _store([0, 1, 2], [0, 1, 2])
    assert probe_beat.anchor_drift(namespace, _State(2), store)["drifted"] is True


def test_a_drifted_anchor_is_exactly_why_the_ablation_frontier_is_vacuous():
    namespace = _namespace()
    store = _store([0, 1, 2], [0, 1, 2])
    state = _State(2)
    action = ("key", 1)
    assert probe_beat.anchor_drift(namespace, state, store)["drifted"] is True
    ablation = _predict(probe_beat.build_hypotheses(namespace), state, action)
    truth = grid_hash(_grid(3, 3))
    _gain, vacuous = probe_beat.information_gain_bits(ablation, truth)
    assert vacuous is True


# ========================================== 5. the checks seen to say no
def test_the_generated_frontier_is_vacuous_when_the_world_does_something_else():
    """The negative control that matters most.

    A frontier that always contains the truth is not a frontier, it is a
    tautology. Here the world does something no generator claims -- it repaints
    a whole column -- and the generated frontier must come back empty, exactly
    as the ablation one does.
    """
    namespace = _namespace()
    store = _store([0, 1, 2], [0, 1, 2])
    full = probe_beat.build_hypotheses(
        namespace, frontier=FrontierConfig(mode="generated"), store=store)
    predictions = _predict(full, _State(2), ("key", 1))
    surprise = [[0] * SIZE for _ in range(SIZE)]
    for r in range(SIZE):
        surprise[r][4] = 7
    _gain, vacuous = probe_beat.information_gain_bits(
        predictions, grid_hash(surprise))
    assert vacuous is True


def test_next_unnameable_cells_is_silent_when_the_history_is_scattered():
    """No line, no extrapolation. The generator declines rather than guesses."""
    store = FrameStore()
    for idx, cell in enumerate([(0, 0), (4, 4), (1, 3), (3, 1)]):
        grid = [[0] * SIZE for _ in range(SIZE)]
        for seen in [(0, 0), (4, 4), (1, 3), (3, 1)][:idx + 1]:
            grid[seen[0]][seen[1]] = 1
        store.add(Step(idx, "ACTION1", [grid], state="NOT_FINISHED"))
    assert probe_beat.next_unnameable_cells(store) == []


def test_next_unnameable_cells_is_silent_on_a_store_too_short_to_have_a_line():
    store = _store([0, 1], [0, 1])
    assert probe_beat.next_unnameable_cells(store) == []


def test_the_generated_frontier_is_empty_without_a_store_to_stand_on():
    """No evidence, no generated hypotheses -- and no crash either."""
    namespace = _namespace()
    assert probe_beat.build_generated_hypotheses(namespace, None) == []
    ids = [h.id for h in probe_beat.build_hypotheses(
        namespace, frontier=FrontierConfig(mode="generated"), store=None)]
    assert ids == ["manual", "inert", "without_advance"]


def test_a_manual_that_cannot_step_makes_the_generated_hypotheses_say_error():
    """A refusal is a result. It must not be a traceback out of the beat."""
    namespace = _namespace()

    def explode(_state, _action):
        raise RuntimeError("the predictor refused")

    namespace["step"] = explode
    store = _store([0, 1, 2], [0, 1, 2])
    predictions = _predict(probe_beat.build_generated_hypotheses(
        namespace, store), _State(2), ("key", 1))
    assert predictions["world_anchored_manual"] == "error"
    assert predictions["edge_advance"] == "error"
    # `world_inert` needs neither `step` nor the manual's state, so it survives.
    assert predictions["world_inert"] == grid_hash(_grid(2, 2))


def test_keep_ablations_false_drops_them_and_is_not_the_default():
    namespace = _namespace()
    store = _store([0, 1, 2], [0, 1, 2])
    assert FrontierConfig(mode="generated").keep_ablations is True
    ids = [h.id for h in probe_beat.build_hypotheses(
        namespace, store=store,
        frontier=FrontierConfig(mode="generated", keep_ablations=False))]
    assert "without_advance" not in ids
    assert ids[:2] == ["manual", "inert"]
