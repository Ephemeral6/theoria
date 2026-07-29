"""C9, second pass: identity across a consumable, and the `faces` atom.

Two things are under test and they are separate claims.

1. `pipeline.identity_swap` — when the mover steps onto a stationary object, the
   matcher's cheapest reading is that the *stationary* one changed colour and the
   mover died.  The repair undoes exactly that and nothing wider, and it costs
   bits, so the price is asserted rather than assumed away.
2. `pipeline.atoms_a0.faces` — E-09.  The one relational reading the vocabulary
   was missing, with its four refusals.

The acceptance test at the bottom is C9's work-order line: `worldgen`'s
count-lock world through this pipeline.  It skips if worldgen has not been
generated, because `worldgen/` is a different territory and this suite may not
build it.
"""

import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)

import _bootstrap  # noqa: F401,E402

from engines.mdl_segmenter.costs import CostModel  # noqa: E402
from engines.mdl_segmenter.segmenter import Event, Segmentation, Track  # noqa: E402

from pipeline import atoms_a0  # noqa: E402
from pipeline.identity_swap import repair_identity_swaps  # noqa: E402

WORLDGEN = os.path.join(REPO, "worldgen", "out", "worlds")
needs_worldgen = pytest.mark.skipif(
    not os.path.exists(os.path.join(WORLDGEN, "t2-lock-fragile", "raw_trace.jsonl")),
    reason="run `python -m worldgen.generate` first (different territory)",
)

COST = CostModel(7, 9, max_objects=5)


# ----------------------------------------------------------------- fixtures

def _track(track_id, color, anchors, rel_cells=((0, 0),), n=4):
    """A track whose body is `rel_cells` offset from each non-None anchor."""
    masks = [None if a is None
             else tuple((a[0] + dr, a[1] + dc) for dr, dc in rel_cells)
             for a in anchors]
    first = next(i for i, a in enumerate(anchors) if a is not None)
    return Track(track_id=track_id, first_frame=first, color=color,
                 shape=(1, 1), rel_cells=tuple(rel_cells),
                 anchors=list(anchors), masks=masks)


def _swap_scene(mover_anchor=(2, 1), eaten_anchor=(3, 1), to_color=6,
                cells=None, eaten_cells=((0, 0),)):
    """Frames 0..3.  The mover is eaten-adjacent at t=1 and gone at t=2."""
    mover = _track("obj0", 6, [(1, 1), mover_anchor, None, None])
    eaten = _track("obj1", 2, [eaten_anchor, eaten_anchor,
                               eaten_anchor, eaten_anchor],
                   rel_cells=eaten_cells)
    events = [
        Event(t=0, type="move", track="obj0", params={"dy": 1, "dx": 0},
              bits=COST.move_bits(1, 0)),
        Event(t=1, type="vanish", track="obj0", params={},
              bits=COST.vanish_bits()),
        Event(t=1, type="recolor", track="obj1",
              params={"cells": cells if cells is not None
                      else [list(eaten_anchor)],
                      "to": [to_color]},
              bits=COST.recolor_bits(1)),
    ]
    bits = sum(e.bits for e in events)
    return Segmentation(tracks=[mover, eaten], events=events, script_bits=bits,
                        baseline_bits=10 * bits, declaration_bits=0, n_frames=4)


# ------------------------------------------------- 1 · the repair, and its price

def test_the_mover_keeps_its_identity_and_the_eaten_track_ends():
    seg, report = repair_identity_swaps(_swap_scene(), COST)
    assert report.applied
    assert [s.mover for s in report.swaps] == ["obj0"]
    assert [s.eaten for s in report.swaps] == ["obj1"]

    mover = next(t for t in seg.tracks if t.track_id == "obj0")
    eaten = next(t for t in seg.tracks if t.track_id == "obj1")
    assert mover.anchors == [(1, 1), (2, 1), (3, 1), (3, 1)]
    assert eaten.anchors[:2] == [(3, 1), (3, 1)]
    assert eaten.anchors[2:] == [None, None]
    assert mover.color == 6 and eaten.color == 2


def test_the_recolor_becomes_a_move_and_a_vanish():
    seg, _report = repair_identity_swaps(_swap_scene(), COST)
    at_one = sorted(((e.type, e.track) for e in seg.events if e.t == 1))
    assert at_one == [("move", "obj0"), ("vanish", "obj1")]
    move = next(e for e in seg.events if e.t == 1 and e.type == "move")
    assert (move.params["dy"], move.params["dx"]) == (1, 0)
    gone = next(e for e in seg.events if e.t == 1 and e.type == "vanish")
    assert gone.params["consumed_by"] == "obj0"


def test_no_track_changes_colour_after_the_repair():
    seg, _ = repair_identity_swaps(_swap_scene(), COST)
    assert not [e for e in seg.events if e.type == "recolor"]


def test_the_repair_costs_two_bits_and_says_so():
    """The one place the pipeline overrules script length.  Not hidden."""
    before = _swap_scene()
    seg, report = repair_identity_swaps(before, COST)
    assert seg.script_bits == before.script_bits + 2
    assert report.as_json()["delta_bits"] == 2
    assert report.as_json()["swaps"][0]["delta_bits"] == 2
    # ... and the direction of the inequality is the reason it cannot be
    # adjudicated by bits: the wrong reading is the cheaper one.
    assert COST.recolor_bits(1) + COST.vanish_bits() < \
        COST.move_bits(1, 0) + COST.vanish_bits()


# ------------------------------------------------------- 2 · the four refusals

def test_a_non_adjacent_swap_is_refused_and_recorded():
    seg, report = repair_identity_swaps(
        _swap_scene(mover_anchor=(2, 1), eaten_anchor=(5, 6)), COST)
    assert not report.applied and not report.swaps
    assert any("4-adjacent" in m["why"] for m in report.near_misses)
    assert seg.events[1].type == "vanish"          # untouched


def test_a_recolour_to_a_different_colour_is_refused():
    seg, report = repair_identity_swaps(_swap_scene(to_color=7), COST)
    assert not report.applied
    assert any("vanishing track's colour" in m["why"] for m in report.near_misses)


def test_a_partial_recolour_is_refused():
    """Half an object turning the mover's colour is not the mover arriving."""
    seg, report = repair_identity_swaps(
        _swap_scene(eaten_cells=((0, 0), (0, 1)), cells=[[3, 1]]), COST)
    assert not report.applied
    assert any("whole body" in m["why"] for m in report.near_misses)


def test_a_shape_change_is_refused():
    scene = _swap_scene(eaten_cells=((0, 0), (0, 1)), cells=[[3, 1], [3, 2]])
    seg, report = repair_identity_swaps(scene, COST)
    assert not report.applied
    assert any("shapes differ" in m["why"] for m in report.near_misses)


def test_a_plain_recolour_with_no_vanish_is_left_alone():
    """A0's Switch recolours 7<->8 every time it is used.  Nothing is consumed,
    nothing vanishes, and the repair must not invent a move for it."""
    switch = _track("obj0", 7, [(1, 1), (1, 1), (1, 1), (1, 1)])
    cart = _track("obj1", 6, [(3, 1), (3, 2), (3, 3), (3, 4)])
    events = [Event(t=1, type="recolor", track="obj0",
                    params={"cells": [[1, 1]], "to": [8]},
                    bits=COST.recolor_bits(1))]
    seg = Segmentation(tracks=[switch, cart], events=events,
                       script_bits=events[0].bits, baseline_bits=100,
                       declaration_bits=0, n_frames=4)
    out, report = repair_identity_swaps(seg, COST)
    assert not report.applied and not report.swaps and not report.near_misses
    assert out is seg


# --- the holes an adversarial pass found, each pinned -----------------------
# `theory-compiler/runs/20260728T173400Z-C9-mover-identity/probes/
#  10_adversarial_identity_swap.py` was written to refute this pass.  Every case
# below is one it broke before these refusals existed.

@pytest.mark.parametrize("shape", ["two movers, one candidate",
                                   "one mover, two candidates"])
def test_an_ambiguous_pairing_is_refused_rather_than_decided_by_track_id(shape):
    """Both readings fit the same pixels equally well.

    Choosing between them by track id would make the answer an artefact of which
    raster cell the segmenter numbered first, dressed up as physics.
    """
    if shape == "two movers, one candidate":
        tracks = [_track("obj0", 6, [(1, 1), (1, 2), None, None]),
                  _track("obj1", 6, [(1, 5), (1, 4), None, None]),
                  _track("obj2", 2, [(1, 3)] * 4)]
        vanishers, recolours = ["obj0", "obj1"], [("obj2", (1, 3))]
    else:
        tracks = [_track("obj0", 6, [(1, 1), (1, 3), None, None]),
                  _track("obj1", 2, [(1, 2)] * 4),
                  _track("obj2", 2, [(1, 4)] * 4)]
        vanishers, recolours = ["obj0"], [("obj1", (1, 2)), ("obj2", (1, 4))]

    events = [Event(t=1, type="vanish", track=v, params={},
                    bits=COST.vanish_bits()) for v in vanishers]
    events += [Event(t=1, type="recolor", track=tid,
                     params={"cells": [list(cell)], "to": [6]},
                     bits=COST.recolor_bits(1)) for tid, cell in recolours]
    seg = Segmentation(tracks=tracks, events=events,
                       script_bits=sum(e.bits for e in events),
                       baseline_bits=999, declaration_bits=0, n_frames=4)

    out, report = repair_identity_swaps(seg, COST)
    assert not report.applied and not report.swaps
    assert any("does not choose one" in m["why"] for m in report.near_misses)
    assert out is seg


def test_two_independent_swaps_at_one_transition_are_both_taken():
    """Refusing ambiguity must not become refusing plurality: when the pairing
    is forced, greedy first-fit's habit of finding one of two is a defect."""
    tracks = [_track("obj0", 6, [(1, 1), (1, 2), None, None]),
              _track("obj1", 6, [(5, 1), (5, 2), None, None]),
              _track("obj2", 2, [(1, 3)] * 4),
              _track("obj3", 2, [(5, 3)] * 4)]
    events = [
        Event(t=1, type="vanish", track="obj0", params={}, bits=COST.vanish_bits()),
        Event(t=1, type="vanish", track="obj1", params={}, bits=COST.vanish_bits()),
        Event(t=1, type="recolor", track="obj2",
              params={"cells": [[1, 3]], "to": [6]}, bits=COST.recolor_bits(1)),
        Event(t=1, type="recolor", track="obj3",
              params={"cells": [[5, 3]], "to": [6]}, bits=COST.recolor_bits(1)),
    ]
    seg = Segmentation(tracks=tracks, events=events,
                       script_bits=sum(e.bits for e in events),
                       baseline_bits=999, declaration_bits=0, n_frames=4)
    _out, report = repair_identity_swaps(seg, COST)
    assert report.applied
    assert sorted((s.mover, s.eaten) for s in report.swaps) == \
        [("obj0", "obj2"), ("obj1", "obj3")]
    assert report.as_json()["delta_bits"] == 4


def test_a_stale_declared_colour_does_not_hide_a_genuine_step_onto():
    """`Track.color` is the colour at declaration.  A mover that has already
    recoloured carries a stale one, and adjudicating against it refused a real
    consumption -- which is exactly what happens on the second hop of a chain."""
    mover = _track("obj0", 7, [(1, 1), (1, 2), None, None])
    eaten = _track("obj1", 2, [(1, 3), (1, 3), (1, 3), (1, 3)])
    events = [
        Event(t=0, type="recolor", track="obj0",
              params={"cells": [[1, 1]], "to": [6]}, bits=COST.recolor_bits(1)),
        Event(t=1, type="vanish", track="obj0", params={}, bits=COST.vanish_bits()),
        Event(t=1, type="recolor", track="obj1",
              params={"cells": [[1, 3]], "to": [6]}, bits=COST.recolor_bits(1)),
    ]
    seg = Segmentation(tracks=[mover, eaten], events=events,
                       script_bits=sum(e.bits for e in events),
                       baseline_bits=999, declaration_bits=0, n_frames=4)
    _out, report = repair_identity_swaps(seg, COST)
    assert report.applied, "the mover is colour 6 by t=1, not the declared 7"
    assert [(s.mover, s.eaten) for s in report.swaps] == [("obj0", "obj1")]


def test_a_track_that_comes_back_is_not_a_track_that_was_eaten():
    """Otherwise the mover inherits the returning body and teleports."""
    mover = _track("obj0", 6, [(1, 1), (1, 2), None, None, None, None])
    eaten = _track("obj1", 2, [(1, 3), (1, 3), (1, 3), None, (6, 6), (6, 6)])
    events = [
        Event(t=1, type="vanish", track="obj0", params={}, bits=COST.vanish_bits()),
        Event(t=1, type="recolor", track="obj1",
              params={"cells": [[1, 3]], "to": [6]}, bits=COST.recolor_bits(1)),
    ]
    seg = Segmentation(tracks=[mover, eaten], events=events,
                       script_bits=sum(e.bits for e in events),
                       baseline_bits=999, declaration_bits=0, n_frames=6)
    out, report = repair_identity_swaps(seg, COST)
    assert not report.applied
    assert any("returns after a gap" in m["why"] for m in report.near_misses)
    assert out is seg


def test_a_vanishing_track_that_comes_back_is_left_to_reidentify():
    mover = _track("obj0", 6, [(1, 1), (1, 2), None, (2, 2), (2, 3), (2, 4)])
    eaten = _track("obj1", 2, [(1, 3)] * 6)
    events = [
        Event(t=1, type="vanish", track="obj0", params={}, bits=COST.vanish_bits()),
        Event(t=1, type="recolor", track="obj1",
              params={"cells": [[1, 3]], "to": [6]}, bits=COST.recolor_bits(1)),
    ]
    seg = Segmentation(tracks=[mover, eaten], events=events,
                       script_bits=sum(e.bits for e in events),
                       baseline_bits=999, declaration_bits=0, n_frames=6)
    _out, report = repair_identity_swaps(seg, COST)
    assert not report.applied
    assert any("belongs to reidentify" in m["why"] for m in report.near_misses)


def test_a_recolour_of_cells_that_are_not_the_track_s_body_is_refused():
    """Counting the cells is not enough -- n cells elsewhere on the board would
    have passed that test."""
    scene = _swap_scene(cells=[[5, 5]])
    _out, report = repair_identity_swaps(scene, COST)
    assert not report.applied
    assert any("whole body" in m["why"] for m in report.near_misses)


@needs_worldgen
def test_standing_on_something_is_not_eating_it():
    """The attack that decided the design.

    `t2-cycler-lock`'s agent walks over a cycler tile. Vanish + total recolour +
    same shape + adjacent — the signature is identical to eating a token, and
    nothing in the `Segmentation` tells them apart. The pixels do, but only
    later: an occluded body shows itself again the moment the mover steps off,
    and a consumed one never does.
    """
    from pipeline import multi_miner, segment_operators
    from pipeline.board import extract_board, object_layer
    from pipeline.engines_stage import background_color
    from world.ground_truth import read_trace

    path = os.path.join(WORLDGEN, "t2-cycler-lock", "raw_trace.jsonl")
    if not os.path.exists(path):
        pytest.skip("t2-cycler-lock not generated")
    frames, _actions, _wins = read_trace(path)
    board = extract_board(frames)
    background = background_color(board, frames)
    layer = object_layer(frames, board, background=background)
    _op, seg, report = segment_operators.choose_operator(layer, background=background)

    repair = next(r for r in report if r["chosen"])["identity_repair"]
    assert repair["occlusion_test_ran"], "the caller must hand over the pixels"
    assert any("stood on it rather than consuming it" in m["why"]
               for m in repair["near_misses"])
    assert repair["n_swaps"] == 1, "only the one real consumption survives"
    assert multi_miner.mover_track(seg) == "obj0"


def test_a_repair_without_the_pixels_says_it_could_not_run_the_test():
    """The occlusion test needs the frames. A caller that withholds them gets a
    more permissive pass, and the report says which one it got."""
    _out, report = repair_identity_swaps(_swap_scene(), COST)
    assert report.as_json()["occlusion_test_ran"] is False
    _out, with_pixels = repair_identity_swaps(
        _swap_scene(), COST, frames=[[[0] * 9] * 7] * 4, background=0)
    assert with_pixels.as_json()["occlusion_test_ran"] is True


def test_a_consumed_track_is_not_resurrected_by_reidentify():
    """The repair truncates the eaten track, which makes it disjoint from any
    later look-alike -- exactly the pair `reidentify` merges. A consumed object
    did not come back."""
    from pipeline.reidentify import reidentify

    eaten = _track("obj1", 2, [(1, 3), (1, 3), None, None])
    twin = _track("obj2", 2, [None, None, None, (4, 4)])
    seg = Segmentation(
        tracks=[eaten, twin],
        events=[Event(t=1, type="vanish", track="obj1",
                      params={"consumed_by": "obj0"}, bits=COST.vanish_bits()),
                Event(t=2, type="appear", track="obj2", params={}, bits=30)],
        script_bits=100, baseline_bits=999, declaration_bits=0, n_frames=4)
    _out, merge = reidentify(seg, COST)
    assert not merge.merged, "a consumed object was declared to have returned"


def test_a_ragged_segmentation_is_refused_not_re_threaded():
    mover = _track("obj0", 6, [(1, 1), (1, 2), None, None])
    eaten = _track("obj1", 2, [(1, 3), (1, 3), (1, 3), (1, 3)])
    del eaten.masks[3]           # ragged: mdl_segmenter never emits this
    del eaten.anchors[3]
    events = [
        Event(t=1, type="vanish", track="obj0", params={}, bits=COST.vanish_bits()),
        Event(t=1, type="recolor", track="obj1",
              params={"cells": [[1, 3]], "to": [6]}, bits=COST.recolor_bits(1)),
    ]
    seg = Segmentation(tracks=[mover, eaten], events=events,
                       script_bits=sum(e.bits for e in events),
                       baseline_bits=999, declaration_bits=0, n_frames=4)
    out, report = repair_identity_swaps(seg, COST)
    assert not report.applied
    assert any("ragged" in m["why"] for m in report.near_misses)
    assert out is seg


def test_the_repair_leaves_a_well_formed_segmentation():
    seg, report = repair_identity_swaps(_swap_scene(), COST)
    assert report.applied
    ids = {t.track_id for t in seg.tracks}
    for track in seg.tracks:
        assert len(track.masks) == len(track.anchors) == seg.n_frames
        for mask, anchor in zip(track.masks, track.anchors):
            assert (mask is None) == (anchor is None), track.track_id
        assert any(m is not None for m in track.masks), "no empty track survives"
    for event in seg.events:
        assert event.track in ids
    for t in range(seg.n_frames):
        live = [tuple(x.masks[t]) for x in seg.tracks if x.masks[t] is not None]
        flat = [cell for body in live for cell in body]
        assert len(flat) == len(set(flat)), "two tracks claim one cell at t=%d" % t
    assert seg.script_bits == report.script_bits_after


def test_a_vanish_with_no_recolour_is_left_alone():
    lock = _track("obj0", 3, [(5, 6), (5, 6), None, None])
    seg = Segmentation(tracks=[lock],
                       events=[Event(t=1, type="vanish", track="obj0",
                                     params={}, bits=COST.vanish_bits())],
                       script_bits=COST.vanish_bits(), baseline_bits=100,
                       declaration_bits=0, n_frames=4)
    out, report = repair_identity_swaps(seg, COST)
    assert not report.applied
    assert out is seg


# ------------------------------------------------------- 3 · the `faces` atom

def _obs(mover, anchors, frame=None):
    return atoms_a0.Obs(
        frame=tuple(tuple(row) for row in (frame or [[0] * 9] * 7)),
        mover_anchor=mover, mover_shape=(1, 1), anchors=dict(anchors),
        colors={k: 2 for k in anchors}, background=0,
    )


@pytest.mark.parametrize("direction,there,expected", [
    ("RIGHT", (1, 3), True),
    ("LEFT", (1, 3), False),
    ("UP", (1, 3), False),
    ("DOWN", (1, 3), False),
    ("RIGHT", (1, 4), False),     # two cells away is a different atom
    ("RIGHT", (1, 2), False),     # on top of the mover is not in front of it
])
def test_faces_is_one_step_in_one_direction(direction, there, expected):
    obs = _obs((1, 2), {"obj1": there})
    atom = atoms_a0.Atom("faces", ("obj1", direction))
    assert atoms_a0.evaluate(atom, obs, "RIGHT") is expected
    assert atoms_a0.evaluate(atom.negate(), obs, "RIGHT") is (not expected)


def test_faces_is_false_once_the_track_is_gone():
    obs = _obs((1, 2), {"obj1": None})
    assert atoms_a0.evaluate(atoms_a0.Atom("faces", ("obj1", "RIGHT")),
                             obs, "RIGHT") is False


def test_faces_prints_and_costs_what_the_table_says():
    atom = atoms_a0.Atom("faces", ("obj1", "RIGHT"))
    assert atom.name == "faces(obj1,RIGHT)"
    assert atom.negate().name == "!faces(obj1,RIGHT)"
    assert atom.cost == 13
    assert atom.cost == atoms_a0.Atom("at", (1, 2)).cost      # a position literal
    assert atom.cost > atoms_a0.Atom("tcolor", ("RIGHT", 2)).cost


def test_the_widening_did_not_re_price_any_existing_atom():
    """E-08 cost every atom one bit; E-09 costs none.  Ten kinds still fit."""
    assert atoms_a0._KIND_BITS == 4
    assert len(atoms_a0._RANK) == 10
    assert atoms_a0.Atom("at", (1, 2)).cost == 13
    assert atoms_a0.Atom("tcolor", ("RIGHT", 2)).cost == 11
    assert atoms_a0.Atom("free", "RIGHT").cost == 7


def test_faces_lifts_its_direction_like_every_other_directional_atom():
    atom = atoms_a0.Atom("faces", ("obj1", "RIGHT"))
    assert atom.substitute_direction("RIGHT").name == "faces(obj1,?dir)"
    assert atom.substitute_direction("LEFT") is atom


def test_the_vocabulary_only_offers_pairs_the_trajectory_showed():
    observations = [
        _obs((1, 2), {"obj1": (1, 3), "obj2": (5, 5)}),
        _obs((1, 1), {"obj1": (1, 3), "obj2": (5, 5)}),
    ]
    names = {a.name for a in
             atoms_a0.build_vocabulary(observations, ["obj1", "obj2"])}
    assert "faces(obj1,RIGHT)" in names        # observed at the first frame
    assert "faces(obj1,LEFT)" not in names     # never true: a constant
    assert not [n for n in names if n.startswith("faces(obj2")]


def test_an_atom_name_round_trips_through_the_probe_runner():
    """The frontier is stored as text; `count` never round-tripped before."""
    from prime.probe_runner import _atom
    for atom in (atoms_a0.Atom("faces", ("obj1", "RIGHT")),
                 atoms_a0.Atom("faces", ("obj1", "RIGHT"), negated=True),
                 atoms_a0.Atom("count", (2, 3)),
                 atoms_a0.Atom("count", (2, 3), negated=True),
                 atoms_a0.Atom("at", (1, 2)),
                 atoms_a0.Atom("tcolor", ("RIGHT", 2)),
                 atoms_a0.Atom("present", "obj1"),
                 atoms_a0.Atom("free", "RIGHT")):
        assert _atom(atom.name) == atom, atom.name


# --------------------------------------------------- 4 · C9's acceptance line

@needs_worldgen
def test_the_count_lock_world_runs_through_this_pipeline(tmp_path):
    """C9's work-order acceptance, executable.

    Before: `NoSeparatingGuard: no literal separates transition 1 from the
    positives`, with a token named as the mover.
    """
    from pipeline import engines_stage

    trace = os.path.join(WORLDGEN, "t2-lock-fragile", "raw_trace.jsonl")
    report = engines_stage.run_stage(
        trace, str(tmp_path / "candidates.jsonl"), str(tmp_path / "report.json"),
        timestamp="1970-01-01T00:00:00Z")

    seg, mining = report["segmentation"], report["mining"]
    assert seg["mover"] == "obj0", "the mover must be the agent, not a token"
    assert len(seg["tracks"]) == 5
    agent = next(t for t in seg["tracks"] if t["id"] == "obj0")
    assert agent["color"] == 6 and agent["frames_present"] == 111, \
        "the agent must be present for the whole trajectory"
    assert "recolor" not in seg["event_types"], \
        "a token recolouring into the agent is the defect this closes"
    assert mining["rules"], "the world mined no rules at all"
    assert all(mining["explains_every_transition"].values())
    assert all(mining["mutually_exclusive"].values())

    # the identity repair fired three times -- one per token -- and its price
    # is on the record rather than folded into the script length silently.
    chosen = next(row for row in seg["operator_comparison"] if row["chosen"])
    repair = chosen["identity_repair"]
    assert repair["n_swaps"] == 3
    assert repair["delta_bits"] == 6
    assert [s["eaten"] for s in repair["swaps"]] == ["obj3", "obj1", "obj2"]

    # and the rule that could not be stated at all before E-09 is now stated.
    guards = [tuple(r["guard"]) for r in mining["rules"]]
    assert any("!faces(obj1,RIGHT)" in g for g in guards)


@needs_worldgen
@pytest.mark.parametrize("world,mover", [
    ("t2-lock-fragile", "obj0"),
    ("t1-tokens-lock", "obj0"),
    ("t1-walk-maze", "obj0"),
])
def test_the_agent_is_the_mover_on_every_consumable_world(world, mover):
    from pipeline import multi_miner, segment_operators
    from pipeline.board import extract_board, object_layer
    from pipeline.engines_stage import background_color
    from world.ground_truth import read_trace

    path = os.path.join(WORLDGEN, world, "raw_trace.jsonl")
    if not os.path.exists(path):
        pytest.skip("world %s not generated" % world)
    frames, _actions, _wins = read_trace(path)
    board = extract_board(frames)
    background = background_color(board, frames)
    layer = object_layer(frames, board, background=background)
    _op, seg, _rep = segment_operators.choose_operator(layer, background=background)
    assert multi_miner.mover_track(seg) == mover
    # the agent is colour 6 in every worldgen world, and it is the only track
    # that moves at all once identity is repaired.
    movers = {e.track for e in seg.events if e.type == "move"}
    assert movers == {mover}
