"""M7 acceptance: the engine picks the same discriminating action as hand analysis.

Hand analysis of the scenario in `engines/probe_frontier/scenario.py`:

    UP     benign cell above -- h_empty says none, h_nonlethal says move -> 1 bit
    DOWN   empty             -- both say move                            -> 0 bits
    LEFT   lethal            -- both say none                            -> 0 bits
    RIGHT  empty             -- both say move                            -> 0 bits

so the answer is UP at 1 bit.
"""

import math

import pytest

from common.jsonio import read_json, read_jsonl
from engines import cegis_miner, mdl_segmenter, probe_frontier as pf
from engines.cegis_miner.atoms import State as CegisState, evaluate
from engines.probe_frontier import scenario as sc
from fixtures import cart_world
from tools.validate_candidates import validate_rows


@pytest.fixture(scope="module")
def bundle():
    return sc.build()


# --------------------------------------------- the scenario is a real frontier

def test_both_hypotheses_explain_every_transition_seen_so_far(bundle):
    """If the evidence could already separate them, there would be no frontier."""
    for hypothesis in bundle["hypotheses"]:
        assert sc.consistent(hypothesis), hypothesis.id


def test_the_evidence_can_still_refute_a_hypothesis(bundle):
    """The scenario is well posed: consistency is a real filter, not a rubber stamp."""
    assert not sc.consistent(sc.H_IN_BOUNDS)


def test_the_two_hypotheses_disagree_on_exactly_one_action(bundle):
    state = bundle["state"]
    disagree = [
        action
        for action in bundle["actions"]
        if sc.H_EMPTY.predict(state, action) != sc.H_NONLETHAL.predict(state, action)
    ]
    assert disagree == ["UP"]


# ------------------------------------------------------- the hand-checked answer

def test_engine_picks_the_hand_computed_action(bundle):
    best, _ = pf.run(bundle["hypotheses"], bundle["state"], bundle["actions"])
    assert best is not None
    assert best.action == bundle["hand_computed_answer"]
    assert best.entropy == pytest.approx(bundle["hand_computed_entropy"])


def test_every_other_action_is_worth_nothing(bundle):
    _, ranked = pf.run(bundle["hypotheses"], bundle["state"], bundle["actions"])
    by_action = {value.action: value for value in ranked}
    assert by_action["UP"].entropy == pytest.approx(1.0)
    for action in ("DOWN", "LEFT", "RIGHT"):
        assert by_action[action].entropy == pytest.approx(0.0)
        assert not by_action[action].splits


def test_the_split_names_which_hypothesis_predicts_what(bundle):
    best, _ = pf.run(bundle["hypotheses"], bundle["state"], bundle["actions"])
    assert best.partition == {"none": ["h_empty"], "move": ["h_nonlethal"]}


def test_no_action_splits_when_the_hypotheses_agree_everywhere():
    """A state that cannot advance the frontier gets None, not a made-up probe."""
    state = sc.make_state({}, anchor=(2, 2))          # empty board: all agree
    best, ranked = pf.run(sc.FRONTIER, state, sc.DIRECTIONS)
    assert best is None
    assert all(value.entropy == pytest.approx(0.0) for value in ranked)


# --------------------------------------------------------------- the entropy

@pytest.mark.parametrize(
    "weights,expected",
    [
        ([1, 1], 1.0),
        ([1, 1, 1], math.log2(3)),
        ([2, 1], 0.9182958340544896),
        ([3, 1], 0.8112781244591328),
        ([4], 0.0),
        ([], 0.0),
    ],
)
def test_entropy_matches_the_closed_form(weights, expected):
    assert pf.entropy_of(weights) == pytest.approx(expected)


def test_three_hypotheses_give_a_two_one_split():
    best, _ = pf.run(sc.EXTENDED_FRONTIER, sc.PROBE_STATE, sc.DIRECTIONS)
    assert best.action == "UP"
    assert best.entropy == pytest.approx(0.9182958340544896)
    assert best.partition == {
        "none": ["h_empty"],
        "move": ["h_nonlethal", "h_nonlethal_below_top"],
    }


# ------------------------------------------------------- sequential probing

def test_the_next_probe_separates_whatever_survived_the_first():
    """Greedy, one bit at a time: probe, drop the refuted, probe again."""
    survivors = pf.surviving(sc.EXTENDED_FRONTIER, sc.PROBE_STATE, "UP", "move")
    assert [h.id for h in survivors] == ["h_nonlethal", "h_nonlethal_below_top"]

    best, _ = pf.run(survivors, sc.TOP_ROW_STATE, sc.DIRECTIONS)
    assert best.entropy == pytest.approx(1.0)
    assert best.partition == {
        "move": ["h_nonlethal"],
        "none": ["h_nonlethal_below_top"],
    }


def test_surviving_drops_the_hypotheses_the_observation_refutes():
    survivors = pf.surviving(sc.FRONTIER, sc.PROBE_STATE, "UP", "none")
    assert [h.id for h in survivors] == ["h_empty"]


# ------------------------------------------------------------- path cost

def test_path_cost_breaks_a_tie_between_equally_informative_probes():
    """Reaching a divergent state is itself a plan, so bits are priced per cost."""
    state = sc.make_state({(1, 2): sc.BENIGN, (3, 2): sc.BENIGN}, anchor=(2, 2))
    _, ranked = pf.run(sc.FRONTIER, state, sc.DIRECTIONS)
    by_action = {v.action: v for v in ranked}
    assert by_action["UP"].entropy == pytest.approx(1.0)
    assert by_action["DOWN"].entropy == pytest.approx(1.0)

    best, _ = pf.run(sc.FRONTIER, state, sc.DIRECTIONS, costs={"UP": 4.0, "DOWN": 1.0})
    assert best.action == "DOWN"
    assert best.entropy == pytest.approx(1.0)
    assert best.value == pytest.approx(1.0)


# ------------------------------------ the frontier really comes from the miner

def test_a_cegis_frontier_can_be_probed_directly():
    """The miner's leftover ambiguity (free vs in_bounds, D-002) is probe input."""
    rows = read_jsonl(cart_world.TRAJ_PATH)
    frames = [row["frame"] for row in rows]
    actions = [row["action"] for row in rows]
    seg = mdl_segmenter.segment_trajectory(frames)
    mined = cegis_miner.mine(
        cegis_miner.transitions_from_segmentation(frames, actions, seg)
    )
    frontier = mined.by_name("push_UP").frontier
    assert len(frontier) > 1

    hypotheses = pf.hypotheses_from_guards(frontier, evaluate, label="push_UP")
    assert any("free(strip(UP))" in h.description for h in hypotheses)
    assert any("in_bounds(strip(UP))" in h.description for h in hypotheses)

    # A configuration Fixture A never produced: the strip is on the board but
    # occupied. This is exactly where free and in_bounds come apart.
    frame = [[0] * 12 for _ in range(12)]
    for r in range(5, 7):
        for c in range(5, 8):
            frame[r][c] = 6
    frame[4][6] = 3                                    # obstacle in the UP strip
    state = CegisState(
        frame=tuple(tuple(row) for row in frame), anchor=(5, 5), shape=(2, 3)
    )

    best, ranked = pf.run(hypotheses, state, ["UP", "DOWN", "LEFT", "RIGHT"])
    assert best is not None
    assert best.action == "UP"
    assert best.entropy > 0
    by_action = {v.action: v for v in ranked}
    for action in ("DOWN", "LEFT", "RIGHT"):
        assert by_action[action].entropy == pytest.approx(0.0)


# ------------------------------------------------------- contract compliance

def test_candidates_satisfy_the_frozen_schema(bundle):
    best, ranked = pf.run(bundle["hypotheses"], bundle["state"], bundle["actions"])
    rows = pf.candidates(
        best,
        ranked,
        bundle["hypotheses"],
        transitions=[0, 1, 2, 3],
        coverage="2/2",
        state_rendering=bundle["state"].render(),
        timestamp="2026-07-27T00:00:00Z",
    )
    assert validate_rows(rows) == []
    assert len(rows) == 1
    row = rows[0]
    assert row["engine"] == "probe_frontier"
    assert row["kind"] == "probe_design"
    payload = row["payload"]
    assert payload["action"] == "UP"
    assert payload["entropy_bits"] == pytest.approx(1.0)
    assert payload["n_hypotheses"] == 2
    assert len(payload["ranking"]) == 4
    assert payload["ranking"][0]["action"] == "UP"
    assert payload["state"] == bundle["state"].render()
