"""The seal, and the referee's calibration.

Two jobs. The first is that the handoff hands over only what it says it does --
an experiment about arriving cold is worth nothing if the door has a gap in it.
The second is that the referee's copy of each world agrees with what that world's
own authors reported, independently recomputed here; if it does not, every number
downstream is measuring the referee.
"""

import pytest

from crosscheck.bridge import open_world
from crosscheck.judge import native, truth


# ------------------------------------------------------------------ the seal

@pytest.mark.parametrize("world_id", ["S", "C"])
def test_briefing_carries_no_palette_and_no_names(world_id):
    brief = open_world(world_id).briefing()
    text = repr(brief).lower()
    for leak in ("box", "cart", "button", "door", "portal", "player", "wall",
                 "push", "parity", "match", "mismatch", "no-button", "sokoban"):
        assert leak not in text, "briefing leaks %r" % leak


@pytest.mark.parametrize("world_id", ["S", "C"])
def test_world_object_exposes_no_transition_function(world_id):
    world = open_world(world_id)
    public = {name for name in dir(world) if not name.startswith("_")}
    assert public <= {"actions", "background", "briefing", "initial_frame",
                      "ledger", "level", "levels", "rendering_note", "rollout",
                      "world_id"}


@pytest.mark.parametrize("world_id", ["S", "C"])
def test_rollout_meters_every_action(world_id):
    world = open_world(world_id)
    level_id = world.levels()[0].level_id
    world.rollout(level_id, ["UP", "DOWN", "LEFT"])
    world.rollout(level_id, ["RIGHT"])
    assert world.ledger.as_json()["episodes"] == 2
    assert world.ledger.as_json()["actions"] == 4
    assert world.ledger.as_json()["frames"] == 6


@pytest.mark.parametrize("world_id", ["S", "C"])
def test_rollout_is_deterministic(world_id):
    a = open_world(world_id).rollout("%s-alpha" % world_id.lower(),
                                     ["UP", "LEFT", "LEFT", "DOWN"])
    b = open_world(world_id).rollout("%s-alpha" % world_id.lower(),
                                     ["UP", "LEFT", "LEFT", "DOWN"])
    assert a.frames == b.frames and a.won == b.won


@pytest.mark.parametrize("world_id", ["S", "C"])
def test_unknown_action_is_refused(world_id):
    world = open_world(world_id)
    with pytest.raises(ValueError):
        world.rollout(world.levels()[0].level_id, ["NORTH"])


def test_level_ids_do_not_state_their_own_answers():
    ids = {info.level_id for info in open_world("S").levels()}
    ids |= {info.level_id for info in open_world("C").levels()}
    assert not (ids & {"match", "mismatch", "a0-base", "a0-no-button"})


def test_both_worlds_can_be_open_at_once():
    """The two tracks both call their package `world`; isolation is load-bearing."""
    s, c = open_world("S"), open_world("C")
    assert s.rollout("s-alpha", ["LEFT"]).frames[-1] != \
        c.rollout("c-alpha", ["LEFT"]).frames[-1]
    assert len(s.initial_frame("s-alpha")) == 7
    assert len(c.initial_frame("c-alpha")) == 9


# --------------------------------------------------- the referee's calibration

def test_world_c_has_the_reachable_count_its_authors_reported():
    """`cold-start-a0/README.md`: 59 reachable states."""
    assert len(truth.reachable_frames("C", "c-alpha")) == 59


def test_world_s_task_levels_are_what_the_parity_argument_predicts():
    alpha = truth.solvable("S", "s-alpha")
    beta = truth.solvable("S", "s-beta")
    assert alpha["solvable"] and alpha["optimal_length"] == 2
    assert not beta["solvable"]


def test_world_c_task_levels():
    assert truth.solvable("C", "c-alpha")["solvable"]
    assert not truth.solvable("C", "c-beta")["solvable"]


@pytest.mark.parametrize("level_id", sorted(truth.LEVELS_OF["S"]))
def test_the_a0_spike_manual_is_exact_on_its_own_world(level_id):
    """Its README claims 39,960 states, 0 mismatches. Recomputed from scratch."""
    wrong = 0
    for frame in truth.representable_frames("S", level_id):
        for action in truth.actions_of("S"):
            if native.native_step_frame("S", level_id, frame, action) != \
                    truth.truth_step_frame("S", level_id, frame, action):
                wrong += 1
    assert wrong == 0


def test_the_cold_start_manual_is_wrong_in_exactly_three_reachable_places():
    """Its README claims 233/236. The three are the referee's calibration target."""
    cases = wrong = 0
    for frame in truth.reachable_frames("C", "c-alpha"):
        for action in truth.actions_of("C"):
            cases += 1
            if native.native_step_frame("C", "c-alpha", frame, action) != \
                    truth.truth_step_frame("C", "c-alpha", frame, action):
                wrong += 1
    assert (cases, cases - wrong) == (236, 233)
