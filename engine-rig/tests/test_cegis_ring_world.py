"""E20 -- why `cegis_miner` refused on every live track, and what actually fixes it.

The recorded verdict on the `g50t` r3 leg was "no track satisfies the miner's
precondition (exactly one move event per transition). The world does not narrate
as one mover."  Reproducing that leg offline from its own ledger showed the
verdict is three claims welded together, only one of which is true:

* the mover really is a 24-cell annulus and `connected_components(4)` really does
  merge it into the floor -- true, and reproduced by `test_the_default_operator_*`;
* "no track satisfies the precondition" -- false.  Under the *other* operator
  already in the segmenter's box the mover is a clean one-move track;
* "the world does not narrate as one mover" -- false, and the real blocker is
  the guard vocabulary, which is hardcoded to a compass alphabet the world does
  not use.

Every test here runs on `fixtures.ring_world`, which is synthetic.  No game data
and no network.
"""

import collections

import pytest

from engines import cegis_miner
from engines.cegis_miner.atoms import DIRECTIONS, atom_masks, build_vocabulary
from engines.cegis_miner.miner import NoSeparatingGuard
from engines.mdl_segmenter import connected_components, segment_trajectory
from fixtures import ring_world


@pytest.fixture(scope="module")
def traj():
    return ring_world.trajectory()


@pytest.fixture(scope="module")
def traj_hidden():
    return ring_world.trajectory(hidden_state=True)


# ------------------------------------------------- 1. the segmentation premise

def test_the_mover_is_a_24_cell_annulus_sitting_on_the_floor(traj):
    frames, _ = traj
    cells = ring_world.ring_cells(ring_world.TOP)
    assert len(cells) == 24
    grid = frames[0]
    assert {grid[r][c] for r, c in cells} == {ring_world.INK}
    mid = ring_world.RING_SIZE // 2
    centre = (ring_world.TOP[0] + mid, ring_world.TOP[1] + mid)
    assert grid[centre[0]][centre[1]] == ring_world.FLOOR, "the annulus has a hole"
    touching = {grid[r + dr][c + dc]
                for r, c in cells for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
                if (r + dr, c + dc) not in set(cells)}
    assert ring_world.FLOOR in touching, "the ring is 4-adjacent to the floor"


def test_the_default_operator_merges_the_mover_into_the_floor(traj):
    """`split_by_color=False` cannot see the ring: one blob swallows it."""
    frames, _ = traj
    comps = connected_components(frames[0], ring_world.BACKGROUND, split_by_color=False)
    assert len(comps) == 1, "floor and ring are one connected component"
    assert len(comps[0].cells) > 24
    assert comps[0].uniform_color is None, "the merged blob is not one colour"


def test_the_colour_splitting_operator_recovers_the_ring(traj):
    frames, _ = traj
    comps = connected_components(frames[0], ring_world.BACKGROUND, split_by_color=True)
    sizes = sorted(len(c.cells) for c in comps)
    assert 24 in sizes, "the annulus is its own component under split_by_color"
    ring = [c for c in comps if len(c.cells) == 24][0]
    assert ring.uniform_color == ring_world.INK
    assert ring.box == (ring_world.RING_SIZE, ring_world.RING_SIZE)


def test_the_merging_operator_narrates_recolor_and_the_miner_refuses(traj):
    """The refusal itself: correct, and about the segmentation, not the world."""
    frames, actions = traj
    seg = segment_trajectory(frames, ring_world.BACKGROUND, split_by_color=False)
    kinds = collections.Counter(e.type for e in seg.events)
    assert kinds["recolor"] > 0 and kinds["move"] == 0, dict(kinds)
    with pytest.raises(ValueError, match="only move/none are mined"):
        cegis_miner.transitions_from_segmentation(
            frames, actions, seg, seg.tracks[0], ring_world.BACKGROUND)


def test_the_splitting_operator_gives_the_miner_a_clean_one_move_track(traj):
    """"The world does not narrate as one mover" is false -- here it is, moving."""
    frames, actions = traj
    seg = segment_trajectory(frames, ring_world.BACKGROUND, split_by_color=True)
    ring = [t for t in seg.tracks
            if len(t.masks[t.first_frame] or ()) == 24][0]
    moves = [e for e in seg.events if e.track == ring.track_id and e.type == "move"]
    assert moves, "the ring moves"
    transitions = cegis_miner.transitions_from_segmentation(
        frames, actions, seg, ring, ring_world.BACKGROUND)
    assert len(transitions) == len(actions)
    assert {t.effect.type for t in transitions} <= {"move", "none"}


def test_mdl_prefers_the_operator_that_destroys_the_mover(traj):
    """Not a selector bug: the merged script really is shorter.

    Choosing the segmentation by total script length picks the blob that has no
    mover in it, because splitting by colour forces the floor to be re-declared
    every time the hole moves across it.  This is the measured reason the live
    legs ran on `connected_components(4)`.
    """
    frames, _ = traj
    merged = segment_trajectory(frames, ring_world.BACKGROUND, split_by_color=False)
    split = segment_trajectory(frames, ring_world.BACKGROUND, split_by_color=True)
    assert merged.script_bits < split.script_bits
    assert len(merged.tracks) < len(split.tracks)


# -------------------------------------------- 2. the negative control: co-fate

def test_common_fate_clustering_cannot_separate_the_two_berths(traj):
    """The operator the brief asked for would not have fixed this world.

    Common-fate ("cells that change together are one thing") groups the ring's
    two berths into a single 48-cell phantom, because the ring oscillates: every
    cell of the upper berth changes exactly when every cell of the lower berth
    does.  Recorded as a measured limit of the operator, not as a reason to skip
    building it -- but it is not the fix for this world class.
    """
    frames, _ = traj
    classes = collections.defaultdict(list)
    for r in range(len(frames[0])):
        for c in range(len(frames[0][0])):
            sig = tuple(frames[t][r][c] != frames[t + 1][r][c]
                        for t in range(len(frames) - 1))
            if any(sig):
                classes[sig].append((r, c))
    biggest = max(classes.values(), key=len)
    both = set(ring_world.ring_cells(ring_world.TOP)) | set(
        ring_world.ring_cells(ring_world.BOTTOM))
    assert len(biggest) == len(both) == 48
    assert set(biggest) == both, "one class, both berths -- not the 24-cell ring"


# ---------------------------------------------- 3. the vocabulary is the blocker

def test_the_compass_vocabulary_is_blind_to_this_worlds_actions(traj):
    """Every `act==` literal is a constant, so the miner cannot see the action."""
    frames, actions = traj
    seg = segment_trajectory(frames, ring_world.BACKGROUND, split_by_color=True)
    ring = [t for t in seg.tracks if len(t.masks[t.first_frame] or ()) == 24][0]
    transitions = cegis_miner.transitions_from_segmentation(
        frames, actions, seg, ring, ring_world.BACKGROUND)
    states = [t.state for t in transitions]
    acts = [t.action for t in transitions]

    compass = build_vocabulary(states)                    # no `actions` argument
    masks = atom_masks(compass, states, acts)
    act_atoms = [a for a in compass if a.kind == "act"]
    assert act_atoms and all(a.arg in DIRECTIONS for a in act_atoms)
    assert all(masks[a] == 0 for a in act_atoms if not a.negated), \
        "every compass action literal is identically false on this world"

    alphabet = build_vocabulary(states, acts)
    masks2 = atom_masks(alphabet, states, acts)
    live = [a for a in alphabet if a.kind == "act" and not a.negated]
    assert {a.arg for a in live} == set(acts)
    assert any(masks2[a] not in (0, (1 << len(states)) - 1) for a in live), \
        "the alphabet vocabulary can tell the actions apart"


def test_the_compass_vocabulary_refuses_and_the_alphabet_one_returns_a_frontier(traj):
    """The headline: same evidence, same segmentation, different vocabulary."""
    frames, actions = traj
    seg = segment_trajectory(frames, ring_world.BACKGROUND, split_by_color=True)
    ring = [t for t in seg.tracks if len(t.masks[t.first_frame] or ()) == 24][0]
    transitions = cegis_miner.transitions_from_segmentation(
        frames, actions, seg, ring, ring_world.BACKGROUND)

    with pytest.raises(NoSeparatingGuard):
        cegis_miner.mine(transitions, action_alphabet=DIRECTIONS)

    result = cegis_miner.mine(transitions)
    assert result.rules, "a frontier, not a refusal"
    assert result.explains_every_transition()
    assert result.guards_are_mutually_exclusive()
    assert all(len(r.frontier) >= 1 for r in result.rules)
    assert result.vocabulary["act_atoms_are_all_constant"] is False
    assert result.vocabulary["action_alphabet"] == sorted(set(actions))


def _widths(actions):
    frames, acts = ring_world.trajectory(actions)
    seg = segment_trajectory(frames, ring_world.BACKGROUND, split_by_color=True)
    ring = [t for t in seg.tracks if len(t.masks[t.first_frame] or ()) == 24][0]
    transitions = cegis_miner.transitions_from_segmentation(
        frames, acts, seg, ring, ring_world.BACKGROUND)
    result = cegis_miner.mine(transitions)
    return {r.name: len(r.frontier) for r in result.rules}, result


def test_the_frontier_is_wide_on_thin_evidence_and_narrows_as_it_arrives():
    """Theoria.md:202 wants the frontier, not a point guess; :208 prices the split.

    Two transitions leave `move_ACTION1` explained four ways -- by the action,
    by the absence of the other action, by the berth it started in, and by the
    berth it did not.  That width is the probe's raw material.  Twelve
    transitions pin every class to a single guard, which is the other thing a
    frontier engine is for: it can say "this is the only consistent rule", and
    that is a certificate rather than a heuristic.
    """
    thin, _ = _widths(["ACTION1", "ACTION2"])
    assert thin["move_ACTION1"] == 4
    assert thin["move_ACTION2"] == 4

    mid, _ = _widths(["ACTION1", "ACTION2", "ACTION3"])
    assert mid["move_ACTION2"] == 3, "one berth still explains it as well as the action"

    full, result = _widths(None)
    assert set(full.values()) == {1}, "full evidence pins every class"
    assert result.explains_every_transition()
    assert max(thin.values()) > max(full.values()), "the frontier narrowed"


# ------------------------------- 4. hidden state: record the gap, keep the rest

def test_hidden_state_kills_the_whole_track_under_the_default(traj_hidden):
    """The default is unchanged: an unseparable class still raises."""
    frames, actions = traj_hidden
    seg = segment_trajectory(frames, ring_world.BACKGROUND, split_by_color=True)
    ring = [t for t in seg.tracks if len(t.masks[t.first_frame] or ()) == 24][0]
    transitions = cegis_miner.transitions_from_segmentation(
        frames, actions, seg, ring, ring_world.BACKGROUND)
    with pytest.raises(NoSeparatingGuard):
        cegis_miner.mine(transitions)


def test_record_mode_keeps_the_separable_classes_and_names_the_rest(traj_hidden):
    frames, actions = traj_hidden
    seg = segment_trajectory(frames, ring_world.BACKGROUND, split_by_color=True)
    ring = [t for t in seg.tracks if len(t.masks[t.first_frame] or ()) == 24][0]
    transitions = cegis_miner.transitions_from_segmentation(
        frames, actions, seg, ring, ring_world.BACKGROUND)

    result = cegis_miner.mine(transitions, on_unseparable="record")
    assert result.rules, "the separable classes survive"
    assert result.unseparable, "the unseparable class is named, not dropped"
    for entry in result.unseparable:
        assert entry["action"] in set(actions)
        assert entry["support"]
        assert "no literal separates" in entry["reason"]

    covered = {i for r in result.rules for i in r.applicable}
    stranded = {i for e in result.unseparable for i in e["support"]}
    assert covered & stranded == set(), "a recorded class is not also claimed"
    assert not result.explains_every_transition(), \
        "absence recorded as absence: the gap must not read as full coverage"


def test_record_mode_is_byte_identical_when_nothing_is_unseparable(traj):
    """Negative control for the widening: on separable evidence the two modes agree."""
    frames, actions = traj
    seg = segment_trajectory(frames, ring_world.BACKGROUND, split_by_color=True)
    ring = [t for t in seg.tracks if len(t.masks[t.first_frame] or ()) == 24][0]
    transitions = cegis_miner.transitions_from_segmentation(
        frames, actions, seg, ring, ring_world.BACKGROUND)
    a = cegis_miner.mine(transitions, on_unseparable="raise")
    b = cegis_miner.mine(transitions, on_unseparable="record")
    assert b.unseparable == []
    assert [r.as_json() for r in a.all_rules] == [r.as_json() for r in b.all_rules]
    # `candidates` mints a fresh uuid per row, so compare everything but the id.
    strip = lambda rows: [{k: v for k, v in row.items() if k != "id"} for row in rows]
    assert strip(cegis_miner.candidates(a, timestamp="t")) == \
        strip(cegis_miner.candidates(b, timestamp="t"))


def test_on_unseparable_rejects_anything_it_does_not_implement(traj):
    frames, actions = traj
    seg = segment_trajectory(frames, ring_world.BACKGROUND, split_by_color=True)
    ring = [t for t in seg.tracks if len(t.masks[t.first_frame] or ()) == 24][0]
    transitions = cegis_miner.transitions_from_segmentation(
        frames, actions, seg, ring, ring_world.BACKGROUND)
    for bad in ("", "RECORD", "skip", "true", None, 1):
        with pytest.raises(ValueError, match="on_unseparable"):
            cegis_miner.mine(transitions, on_unseparable=bad)


# ------------------------------------ 5. tracks born after frame 0 keep evidence

def test_a_track_born_late_is_discarded_by_default_and_kept_by_while_present(traj):
    """`while_present` is opt-in; the default still raises on frame 0."""
    frames, actions = traj
    seg = segment_trajectory(frames, ring_world.BACKGROUND, split_by_color=True)
    late = [t for t in seg.tracks if t.first_frame > 0]
    if not late:
        pytest.skip("this fixture births every track in the prologue")
    track = late[0]
    with pytest.raises(ValueError, match="object absent at frame 0"):
        cegis_miner.transitions_from_segmentation(
            frames, actions, seg, track, ring_world.BACKGROUND)
    kept = cegis_miner.transitions_from_segmentation(
        frames, actions, seg, track, ring_world.BACKGROUND, while_present=True)
    assert all(t.index >= track.first_frame for t in kept)


def test_while_present_is_a_no_op_when_the_track_starts_at_frame_zero(traj):
    """Negative control: the widening changes nothing where it should not."""
    frames, actions = traj
    seg = segment_trajectory(frames, ring_world.BACKGROUND, split_by_color=True)
    ring = [t for t in seg.tracks if len(t.masks[t.first_frame] or ()) == 24][0]
    assert ring.first_frame == 0
    a = cegis_miner.transitions_from_segmentation(
        frames, actions, seg, ring, ring_world.BACKGROUND)
    b = cegis_miner.transitions_from_segmentation(
        frames, actions, seg, ring, ring_world.BACKGROUND, while_present=True)
    assert a == b
