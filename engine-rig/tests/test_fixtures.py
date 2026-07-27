"""M1 acceptance: the three fixtures are deterministic and match ground truth."""

import hashlib
import os

from common.jsonio import read_json, read_jsonl
from fixtures import cart_world, pair_flip, peg4


def _sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def _regen_and_hash(tmpdir, writer, names):
    paths = [os.path.join(tmpdir, n) for n in names]
    writer(*paths)
    return [_sha(p) for p in paths]


# --------------------------------------------------------------- determinism

def test_cart_world_is_byte_reproducible(tmp_path):
    a = _regen_and_hash(str(tmp_path / "a"), cart_world.write, ["t.jsonl", "truth.json"])
    b = _regen_and_hash(str(tmp_path / "b"), cart_world.write, ["t.jsonl", "truth.json"])
    assert a == b


def test_pair_flip_is_byte_reproducible(tmp_path):
    a = _regen_and_hash(str(tmp_path / "a"), pair_flip.write, ["t.jsonl", "truth.json"])
    b = _regen_and_hash(str(tmp_path / "b"), pair_flip.write, ["t.jsonl", "truth.json"])
    assert a == b


def test_peg4_is_byte_reproducible(tmp_path):
    a = _regen_and_hash(str(tmp_path / "a"), peg4.write, ["g.json"])
    b = _regen_and_hash(str(tmp_path / "b"), peg4.write, ["g.json"])
    assert a == b


def test_checked_in_fixtures_match_a_fresh_generation(tmp_path):
    """The data/ files in the repo are exactly what the generators produce now."""
    fresh = str(tmp_path / "fresh")
    cart_world.write(
        os.path.join(fresh, "cart.jsonl"), os.path.join(fresh, "cart_truth.json")
    )
    pair_flip.write(
        os.path.join(fresh, "pair.jsonl"), os.path.join(fresh, "pair_truth.json")
    )
    peg4.write(os.path.join(fresh, "peg4.json"))
    pairs = [
        (cart_world.TRAJ_PATH, os.path.join(fresh, "cart.jsonl")),
        (cart_world.TRUTH_PATH, os.path.join(fresh, "cart_truth.json")),
        (pair_flip.TRAJ_PATH, os.path.join(fresh, "pair.jsonl")),
        (pair_flip.TRUTH_PATH, os.path.join(fresh, "pair_truth.json")),
        (peg4.GRAPH_PATH, os.path.join(fresh, "peg4.json")),
    ]
    for committed, regenerated in pairs:
        assert _sha(committed) == _sha(regenerated), committed


# ------------------------------------------------------------ Fixture A shape

def test_cart_world_frames_and_actions():
    rows = read_jsonl(cart_world.TRAJ_PATH)
    assert 40 <= len(rows) <= 60
    assert all(row["action"] in cart_world.DIRECTIONS for row in rows[:-1])
    assert rows[-1]["action"] is None
    for row in rows:
        frame = row["frame"]
        assert len(frame) == cart_world.GRID_H
        assert all(len(line) == cart_world.GRID_W for line in frame)
        colors = {c for line in frame for c in line}
        assert colors <= {cart_world.BACKGROUND, cart_world.CART_COLOR}
        assert sum(1 for line in frame for c in line if c == cart_world.CART_COLOR) == 6


def test_cart_world_frames_agree_with_truth_anchors():
    rows = read_jsonl(cart_world.TRAJ_PATH)
    truth = read_json(cart_world.TRUTH_PATH)
    assert len(rows) == len(truth["anchors"])
    for row, anchor in zip(rows, truth["anchors"]):
        assert row["frame"] == cart_world.render(tuple(anchor))


def test_cart_world_has_exactly_one_teleport():
    truth = read_json(cart_world.TRUTH_PATH)
    idx = [i for i, e in enumerate(truth["events"]) if e == "teleport"]
    assert idx == [truth["teleport_transition"]]
    t = idx[0]
    assert truth["anchors"][t] == truth["portal_a"]
    assert truth["anchors"][t + 1] == truth["portal_b"]


def test_cart_world_every_direction_has_move_and_block_witnesses():
    truth = read_json(cart_world.TRUTH_PATH)
    actions, events = truth["actions"], truth["events"]
    for d in cart_world.DIRECTIONS:
        assert any(e == "move:" + d for e in events), d
        assert any(
            events[i] == "noop" and actions[i] == d for i in range(len(actions))
        ), d


def test_cart_world_push_and_teleport_guards_are_mutually_exclusive():
    """Constraint 9 on this fixture: no transition matches both rules."""
    truth = read_json(cart_world.TRUTH_PATH)
    t = truth["teleport_transition"]
    anchor = tuple(truth["anchors"][t])
    assert not cart_world.strip_free(anchor, truth["actions"][t])


# ------------------------------------------------------------ Fixture B shape

def test_pair_flip_trajectory_shape():
    rows = read_jsonl(pair_flip.TRAJ_PATH)
    assert len(rows) == pair_flip.N_ACTIONS + 1
    assert rows[-1]["action"] is None
    for row in rows:
        assert len(row["state"]) == pair_flip.N_CELLS
        assert set(row["state"]) <= {"R", "B"}
    for row in rows[:-1]:
        action = row["action"]
        assert action["op"] == "flip_pair"
        assert (action["i"], action["j"]) in pair_flip.PAIRS


def test_pair_flip_actions_are_faithfully_applied():
    rows = read_jsonl(pair_flip.TRAJ_PATH)
    for cur, nxt in zip(rows, rows[1:]):
        pair = (cur["action"]["i"], cur["action"]["j"])
        assert pair_flip.step(tuple(cur["state"]), pair) == tuple(nxt["state"])


def test_pair_flip_red_parity_is_constant():
    rows = read_jsonl(pair_flip.TRAJ_PATH)
    parities = {sum(1 for c in row["state"] if c == "R") % 2 for row in rows}
    assert len(parities) == 1


def test_pair_flip_witnesses_every_pair():
    rows = read_jsonl(pair_flip.TRAJ_PATH)
    used = {(r["action"]["i"], r["action"]["j"]) for r in rows[:-1]}
    assert used == set(pair_flip.PAIRS)


# ------------------------------------------------------------ Fixture C shape

def test_peg4_reachability_matches_hand_enumeration():
    graph = read_json(peg4.GRAPH_PATH)
    assert graph["reachable"]["1110"] == ["1001", "1110"]
    assert graph["reachable"]["0111"] == ["0111", "1001"]
    assert graph["reachable"]["1011"] == ["0010", "1011", "1100"]
    assert graph["reachable"]["1101"] == ["0011", "0100", "1101"]


def test_peg4_solvability_ground_truth():
    graph = read_json(peg4.GRAPH_PATH)
    assert graph["goal"] == "0100"
    assert graph["solvable"] == {
        "1110": False,
        "0111": False,
        "1011": False,
        "1101": True,
    }
    assert graph["distance_to_goal"]["1101"] == 2
    assert graph["distance_to_goal"]["1110"] is None


def test_peg4_every_move_removes_exactly_one_peg():
    graph = read_json(peg4.GRAPH_PATH)
    for edge in graph["edges"]:
        before = edge["src_state"].count("1")
        after = edge["dst_state"].count("1")
        assert after == before - 1


def test_peg4_edges_are_over_the_full_state_space():
    """Move constraints are collected from every state, not only reachable ones."""
    graph = read_json(peg4.GRAPH_PATH)
    assert len(graph["states"]) == 16
    src_states = {e["src_state"] for e in graph["edges"]}
    unreachable_with_moves = src_states - set(graph["reachable"]["1101"])
    assert unreachable_with_moves, "certificate would only cover the reachable part"
