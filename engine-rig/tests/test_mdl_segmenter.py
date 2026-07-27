"""M2 acceptance: masks match ground truth, and the script beats the pixel baseline."""

import pytest

from common.jsonio import read_json, read_jsonl
from engines import mdl_segmenter
from engines.mdl_segmenter.costs import CostModel, changed_pixels
from fixtures import cart_world
from tools.validate_candidates import validate_rows


@pytest.fixture(scope="module")
def cart():
    rows = read_jsonl(cart_world.TRAJ_PATH)
    truth = read_json(cart_world.TRUTH_PATH)
    frames = [row["frame"] for row in rows]
    return frames, truth, mdl_segmenter.segment_trajectory(frames, background=0)


# ------------------------------------------------- the block is ONE object

def test_exactly_one_track_over_the_whole_trajectory(cart):
    _, _, seg = cart
    assert len(seg.tracks) == 1
    track = seg.tracks[0]
    assert track.color == cart_world.CART_COLOR
    assert track.shape == (cart_world.CART_H, cart_world.CART_W)
    assert len(track.rel_cells) == 6
    assert all(mask is not None for mask in track.masks)


def test_masks_match_ground_truth_frame_by_frame(cart):
    _, truth, seg = cart
    track = seg.tracks[0]
    assert len(track.masks) == truth["n_frames"]
    for t, expected in enumerate(truth["masks"]):
        got = sorted([list(cell) for cell in track.masks[t]])
        assert got == expected, "frame %d" % t


def test_anchors_match_ground_truth(cart):
    _, truth, seg = cart
    track = seg.tracks[0]
    got = [list(a) for a in track.anchors]
    assert got == truth["anchors"]


# ------------------------------------------------------- the event narration

def test_events_reproduce_the_ground_truth_event_sequence(cart):
    _, truth, seg = cart
    for t, expected in enumerate(truth["events"]):
        events = seg.events_at(t)
        if expected == "noop":
            assert events == [], "transition %d should be silent" % t
            continue
        assert len(events) == 1, "transition %d" % t
        event = events[0]
        assert event.type == "move"
        got = (event.params["dy"], event.params["dx"])
        if expected == "teleport":
            src = truth["anchors"][t]
            dst = truth["anchors"][t + 1]
            assert got == (dst[0] - src[0], dst[1] - src[1])
            assert max(abs(got[0]), abs(got[1])) > 1, "teleport is not a unit step"
        else:
            direction = expected.split(":")[1]
            assert got == cart_world.DELTA[direction], "transition %d" % t


def test_no_spurious_appear_or_vanish(cart):
    _, _, seg = cart
    assert [e for e in seg.events if e.type in ("appear", "vanish")] == []


def test_event_count_matches_non_silent_transitions(cart):
    _, truth, seg = cart
    non_silent = sum(1 for e in truth["events"] if e != "noop")
    assert len(seg.events) == non_silent


# ------------------------------------------------------------- the MDL claim

def test_script_is_much_shorter_than_the_per_pixel_baseline(cart):
    _, _, seg = cart
    assert seg.baseline_bits > 0
    assert seg.script_bits < seg.baseline_bits
    assert seg.compression_ratio <= 0.5, (seg.script_bits, seg.baseline_bits)


def test_baseline_is_computed_from_the_actual_pixel_diffs(cart):
    """Guard against a baseline inflated to make the script look good."""
    frames, _, seg = cart
    cost = CostModel(cart_world.GRID_H, cart_world.GRID_W, max_objects=1)
    expected = sum(
        cost.baseline_transition_bits(len(changed_pixels(frames[t], frames[t + 1])))
        for t in range(len(frames) - 1)
    )
    assert seg.baseline_bits == expected


def test_script_bits_equal_the_sum_of_what_was_emitted(cart):
    """Guard against a script cost that forgot to charge for something."""
    _, _, seg = cart
    n_transitions = seg.n_frames - 1
    expected = (
        seg.declaration_bits
        + n_transitions * CostModel(12, 12).b_header
        + sum(e.bits for e in seg.events)
    )
    assert seg.script_bits == expected


# ------------------------------------------- the matcher, on a harder scene

def _grid(cells, h=8, w=12, color=6):
    grid = [[0] * w for _ in range(h)]
    for r, c in cells:
        grid[r][c] = color
    return grid


def test_two_identical_blocks_are_tracked_without_appear_or_vanish():
    """Bipartite matching, not nearest-blob: two look-alikes drift apart."""
    left = [(1, 3), (1, 4)]
    right = [(1, 7), (1, 8)]
    frames = []
    for k in range(4):
        frames.append(
            _grid([(r, c - k) for r, c in left] + [(r, c + k) for r, c in right])
        )
    seg = mdl_segmenter.segment_trajectory(frames)
    assert len(seg.tracks) == 2
    assert [e for e in seg.events if e.type in ("appear", "vanish")] == []
    moves = [e for e in seg.events if e.type == "move"]
    assert len(moves) == 6
    per_track = {}
    for event in moves:
        per_track.setdefault(event.track, []).append(event.params["dx"])
    assert sorted(per_track.values()) == [[-1, -1, -1], [1, 1, 1]]


def test_recolor_is_narrated_as_recolor_not_as_appear_plus_vanish():
    cells = [(2, 2), (2, 3), (3, 2), (3, 3)]
    frames = [_grid(cells, color=6), _grid(cells, color=3)]
    seg = mdl_segmenter.segment_trajectory(frames)
    assert len(seg.tracks) == 1
    assert [e.type for e in seg.events] == ["recolor"]
    assert seg.events[0].params["to"] == [3, 3, 3, 3]


def test_object_leaving_the_board_is_narrated_as_vanish():
    frames = [_grid([(2, 2), (2, 3)]), _grid([])]
    seg = mdl_segmenter.segment_trajectory(frames)
    assert [e.type for e in seg.events] == ["vanish"]


def test_object_entering_the_board_is_narrated_as_appear():
    frames = [_grid([]), _grid([(2, 2), (2, 3)])]
    seg = mdl_segmenter.segment_trajectory(frames)
    assert [e.type for e in seg.events] == ["appear"]
    assert len(seg.tracks) == 1
    assert seg.tracks[0].first_frame == 1


# ------------------------------------------------------- contract compliance

def test_candidates_satisfy_the_frozen_schema(cart):
    _, truth, seg = cart
    rows = mdl_segmenter.candidates(seg, timestamp="2026-07-27T00:00:00Z")
    errors = validate_rows(rows)
    assert errors == []
    assert len(rows) == 1
    row = rows[0]
    assert row["engine"] == "mdl_segmenter"
    assert row["kind"] == "object_hypothesis"
    assert row["status"] == "candidate"
    assert row["evidence"]["coverage"] == "%d/%d" % (truth["n_frames"], truth["n_frames"])
    payload = row["payload"]
    assert payload["color"] == 6
    assert payload["shape"] == [2, 3]
    assert payload["mdl"]["gain_bits"] > 0
