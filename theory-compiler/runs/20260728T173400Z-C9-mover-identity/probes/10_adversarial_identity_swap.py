"""Probe 10 -- an adversarial audit of `pipeline.identity_swap`.

The claim under attack:

    "This pass repairs exactly the case where the mover stepped onto a
     stationary object and the matcher handed the mover's identity to the
     object it ate.  It never fires on a transition where that is not what
     happened, and it never corrupts the Segmentation it returns."

Six lines of attack, then an empirical sweep of every `worldgen` world.
Read-only with respect to every tracked tree except this run directory; it
writes nothing at all except stdout and (optionally) a JSON summary here.

    python .../10_adversarial_identity_swap.py [worktree|<git-rev>]

The artefact was being edited while this probe ran, so the version under test
is named and hashed in the output rather than assumed.  `HEAD` re-materialises
the committed file into a temp module and attacks that instead.
"""
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
RUN = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(RUN, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "cold-start-a0"))
sys.path.insert(0, os.path.join(ROOT, "engine-rig"))

import _bootstrap  # noqa: F401,E402

from engines.mdl_segmenter import segmenter as _seg  # noqa: E402
from engines.mdl_segmenter.costs import CostModel  # noqa: E402
from engines.mdl_segmenter.segmenter import Event, Segmentation, Track  # noqa: E402

from pipeline import multi_miner, segment_operators  # noqa: E402
from pipeline.identity_swap import repair_identity_swaps  # noqa: E402
from pipeline.reidentify import reidentify  # noqa: E402

COST = CostModel(7, 9, max_objects=5)

FINDINGS = []
REL = "cold-start-a0/pipeline/identity_swap.py"


def load_pass(source):
    """Bind `repair_identity_swaps` to a named version of the artefact."""
    global repair_identity_swaps
    if source == "worktree":
        path = os.path.join(ROOT, "cold-start-a0", "pipeline", "identity_swap.py")
        blob = open(path, "rb").read()
    else:
        blob = subprocess.check_output(
            ["git", "show", "%s:%s" % (source, REL)], cwd=ROOT)
        tmp = os.path.join(tempfile.mkdtemp(), "identity_swap_%s.py"
                           % source.replace("/", "_"))
        with open(tmp, "wb") as fh:
            fh.write(blob)
        spec = importlib.util.spec_from_file_location("identity_swap_under_test", tmp)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        repair_identity_swaps = mod.repair_identity_swaps
    return hashlib.sha256(blob).hexdigest()[:16], len(blob.splitlines())


def finding(line, tag, verdict, text):
    FINDINGS.append({"line": line, "tag": tag, "verdict": verdict, "text": text})
    print("  [%s] %-34s %s" % (verdict, tag, text))


def head(title):
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


# --------------------------------------------------------------- constructors

def track(tid, color, anchors, rel_cells=((0, 0),), shape=(1, 1), masks=None):
    """A track present exactly where `anchors` is not None."""
    if masks is None:
        masks = [None if a is None
                 else tuple((a[0] + r, a[1] + c) for r, c in rel_cells)
                 for a in anchors]
    first = next((i for i, a in enumerate(anchors) if a is not None), 0)
    return Track(track_id=tid, first_frame=first, color=color, shape=shape,
                 rel_cells=tuple(rel_cells), anchors=list(anchors),
                 masks=list(masks))


def seg_of(tracks, events, n_frames, declaration_bits=0):
    bits = (declaration_bits + max(n_frames - 1, 0) * COST.b_header
            + sum(e.bits for e in events))
    return Segmentation(tracks=list(tracks), events=list(events),
                        script_bits=bits, baseline_bits=10 * max(bits, 1),
                        declaration_bits=declaration_bits, n_frames=n_frames)


def vanish(t, tid):
    return Event(t=t, type="vanish", track=tid, params={},
                 bits=COST.vanish_bits())


def recolor(t, tid, cells, to):
    return Event(t=t, type="recolor", track=tid,
                 params={"cells": [list(c) for c in cells], "to": list(to)},
                 bits=COST.recolor_bits(len(cells)))


def move(t, tid, dy, dx):
    return Event(t=t, type="move", track=tid, params={"dy": dy, "dx": dx},
                 bits=COST.move_bits(dy, dx))


def summarize(seg, report):
    return {
        "n_swaps": len(report.swaps),
        "swaps": [(s.mover, s.eaten, s.t) for s in report.swaps],
        "near_misses": [(m["t"], m["mover"], m["eaten"], m["why"][:28])
                        for m in report.near_misses],
        "delta_bits": report.script_bits_after - report.script_bits_before,
    }


# ------------------------------------------------------ structural invariants

def check_invariants(seg, label, n_frames=None):
    """Every structural property the claim's third clause promises."""
    problems = []
    n = n_frames if n_frames is not None else seg.n_frames
    ids = {t.track_id for t in seg.tracks}
    if len(ids) != len(seg.tracks):
        problems.append("duplicate track ids")
    for t in seg.tracks:
        if len(t.masks) != len(t.anchors):
            problems.append("%s: len(masks)=%d != len(anchors)=%d"
                            % (t.track_id, len(t.masks), len(t.anchors)))
        if len(t.masks) != n:
            problems.append("%s: len(masks)=%d != n_frames=%d"
                            % (t.track_id, len(t.masks), n))
        for i in range(min(len(t.masks), len(t.anchors))):
            if (t.masks[i] is None) != (t.anchors[i] is None):
                problems.append("%s: mask/anchor disagree at frame %d" % (t.track_id, i))
        if all(m is None for m in t.masks):
            problems.append("%s: track is entirely empty but still listed" % t.track_id)
        # a track's declared body must match every mask it carries
        for i, m in enumerate(t.masks):
            if m is None:
                continue
            if len(m) != len(t.rel_cells):
                problems.append("%s: mask at %d has %d cells, rel_cells has %d"
                                % (t.track_id, i, len(m), len(t.rel_cells)))
            a = t.anchors[i]
            if a is not None and tuple(sorted(m)) != tuple(
                    sorted((a[0] + r, a[1] + c) for r, c in t.rel_cells)):
                problems.append("%s: mask at %d is not anchor+rel_cells" % (t.track_id, i))
    for e in seg.events:
        if e.track not in ids:
            problems.append("event t=%d %s names missing track %s" % (e.t, e.type, e.track))
            continue
        tr = next(x for x in seg.tracks if x.track_id == e.track)
        present_t = 0 <= e.t < len(tr.masks) and tr.masks[e.t] is not None
        if e.type in ("move", "recolor", "vanish") and not present_t:
            problems.append("event t=%d %s on %s which is absent at t"
                            % (e.t, e.type, e.track))
    # overlapping bodies: two tracks occupying the same cell in the same frame
    for i in range(n):
        seen = {}
        for t in seg.tracks:
            if i >= len(t.masks) or t.masks[i] is None:
                continue
            for cell in t.masks[i]:
                if cell in seen:
                    problems.append("frame %d: %s and %s both occupy %s"
                                    % (i, seen[cell], t.track_id, cell))
                seen[cell] = t.track_id
    return problems


def bits_are_consistent(seg, cost):
    """script_bits == declaration + one header per transition + every event."""
    want = seg.declaration_bits + (seg.n_frames - 1) * cost.b_header \
        + sum(e.bits for e in seg.events)
    return want == seg.script_bits, want, seg.script_bits


# ============================================================================
# LINE 1 -- FALSE POSITIVES
# ============================================================================

def line1_false_positive_traffic_light():
    """Two adjacent same-shape lamps.  The left one switches off; the right one,
    for reasons of its own, turns the left one's colour.  Nothing moved."""
    head("LINE 1 -- FALSE POSITIVES")

    # frames: a 5x7 board.  lamp L (colour 6) at (2,2); lamp R (colour 2) at
    # (2,3).  At t=1 L goes dark and R turns 6.  R then goes on doing its own
    # thing: at t=2 it slides right, at t=3 it slides right again.
    def blank():
        return [[0] * 7 for _ in range(5)]

    frames = []
    f = blank(); f[2][2] = 6; f[2][3] = 2; frames.append(f)          # t=0
    f = blank(); f[2][2] = 6; f[2][3] = 2; frames.append(f)          # t=1
    f = blank(); f[2][3] = 6; frames.append(f)                       # t=2  L off, R -> 6
    f = blank(); f[2][4] = 6; frames.append(f)                       # t=3  R slides
    f = blank(); f[2][5] = 6; frames.append(f)                       # t=4  R slides
    frames = [tuple(tuple(r) for r in fr) for fr in frames]

    # the uniform-colour operator is the one every consumable world selects,
    # so run the repair against that segmentation rather than the chooser's
    # (the colour-agnostic operator fuses the two adjacent lamps into one blob
    # and the pattern never arises -- which is not a defence, only a different
    # operator).
    raw = segment_operators.segment_with(
        "connected_components(4)+uniform_color", frames, background=0)
    cost = CostModel(len(frames[0]), len(frames[0][0]),
                     max_objects=max(len(raw.tracks), 1))
    seg, rep_obj = repair_identity_swaps(raw, cost)
    rep = rep_obj.as_json()
    moves = {}
    for e in seg.events:
        if e.type == "move":
            moves[e.track] = moves.get(e.track, 0) + 1

    print("  frames built from pixels, uniform_color operator")
    print("  raw events: %s" % [(e.t, e.type, e.track) for e in raw.events])
    print("  identity_repair = n_swaps=%d swaps=%s"
          % (rep["n_swaps"], [(s["mover"], s["eaten"], s["t"])
                              for s in rep["swaps"]]))
    print("  tracks: %s" % [(t.track_id, t.color, t.anchors) for t in seg.tracks])
    print("  move counts: %s ; mover_track = %s"
          % (moves, multi_miner.mover_track(seg)))

    if rep["n_swaps"] >= 1:
        finding(1, "false-positive/pixels", "REFUTES",
                "fired on a scene with no motion at all: lamp L switched off "
                "while neighbour R changed colour. R's two later moves are now "
                "credited to L and R's track is truncated at t=1.")
    else:
        finding(1, "false-positive/pixels", "holds",
                "did not fire on the two-lamp scene (n_swaps=0)")

    # the same scene built directly, in case the matcher's own choice masked it
    L = track("obj0", 6, [(2, 2), (2, 2), None, None, None])
    R = track("obj1", 2, [(2, 3), (2, 3), (2, 3), (2, 4), (2, 5)])
    events = [vanish(1, "obj0"), recolor(1, "obj1", [(2, 3)], [6]),
              move(2, "obj1", 0, 1), move(3, "obj1", 0, 1)]
    s = seg_of([L, R], events, n_frames=5)
    out, rep2 = repair_identity_swaps(s, COST)
    print("  hand-built: %s" % json.dumps(summarize(out, rep2), sort_keys=True))
    after_moves = {e.track for e in out.events if e.type == "move"}
    if rep2.applied:
        finding(1, "false-positive/hand-built", "REFUTES",
                "fires; R's independent later moves are re-attributed to %s "
                "and R's track dies at t=1.  Physically: nothing moved at t=1."
                % sorted(after_moves))
    else:
        finding(1, "false-positive/hand-built", "holds", "refused")


def line1_false_negative_stale_color():
    """`Track.color` is frozen at the track's first frame and never updated by
    a recolour, so a mover that has ever changed colour can no longer be
    matched against the colour it is *now*."""
    # obj0 starts colour 7, recolours to 8 at t=0, then at t=2 genuinely steps
    # onto obj1, which recolours to 8 (obj0's *current* colour).
    mover = track("obj0", 7, [(1, 1), (1, 1), (2, 1), None, None])
    eaten = track("obj1", 2, [(3, 1), (3, 1), (3, 1), (3, 1), (3, 1)])
    events = [recolor(0, "obj0", [(1, 1)], [8]),
              move(1, "obj0", 1, 0),
              vanish(2, "obj0"),
              recolor(2, "obj1", [(3, 1)], [8])]
    s = seg_of([mover, eaten], events, n_frames=5)
    out, rep = repair_identity_swaps(s, COST)
    print("  stale-colour scene: %s" % json.dumps(summarize(out, rep), sort_keys=True))
    if not rep.applied:
        finding(1, "false-negative/stale colour", "REFUTES-completeness",
                "a genuine step-onto is refused because Track.color is the "
                "colour at first_frame (7), not the colour now (8). "
                "'repairs exactly the case' fails in the other direction.")
    else:
        finding(1, "false-negative/stale colour", "holds", "repaired anyway")


def line1_recolor_cells_unchecked():
    """`_recolor_is_total` counts cells; it never checks they are the eaten
    track's cells."""
    mover = track("obj0", 6, [(1, 1), (2, 1), None, None])
    eaten = track("obj1", 2, [(3, 1), (3, 1), (3, 1), (3, 1)])
    # the recolour names a cell that belongs to nobody at all
    events = [move(0, "obj0", 1, 0), vanish(1, "obj0"),
              recolor(1, "obj1", [(0, 6)], [6])]
    s = seg_of([mover, eaten], events, n_frames=4)
    out, rep = repair_identity_swaps(s, COST)
    if rep.applied:
        finding(1, "recolour cells unvalidated", "weakness",
                "fires on a recolour whose `cells` are not the eaten track's "
                "cells; only len(cells)==len(rel_cells) is checked.")
    else:
        finding(1, "recolour cells unvalidated", "holds", "refused")


# ============================================================================
# LINE 2 -- AMBIGUITY / NON-DETERMINISM
# ============================================================================

def line2_two_perfect_matchings():
    head("LINE 2 -- AMBIGUITY AND THE sorted() ARTEFACT")
    # A 2x2 cycle: movers A(0,0) and C(1,1), eaten B(0,1) and D(1,0).
    # A-B, A-D, C-B, C-D are all 4-adjacent.  Both perfect matchings are
    # equally consistent with every pixel.
    def scene(ids):
        a, b, c, d = ids
        A = track(a, 6, [(0, 0), (0, 0), None, None])
        B = track(b, 2, [(0, 1), (0, 1), (0, 1), (0, 1)])
        C = track(c, 6, [(1, 1), (1, 1), None, None])
        D = track(d, 2, [(1, 0), (1, 0), (1, 0), (1, 0)])
        events = [vanish(1, a), vanish(1, c),
                  recolor(1, b, [(0, 1)], [6]), recolor(1, d, [(1, 0)], [6])]
        return seg_of([A, B, C, D], events, n_frames=4)

    out1, r1 = repair_identity_swaps(scene(("obj0", "obj1", "obj2", "obj3")), COST)
    # exactly the same geometry, only the ids permuted: A<->C swap their names
    out2, r2 = repair_identity_swaps(scene(("obj2", "obj1", "obj0", "obj3")), COST)
    p1 = sorted((s.mover, s.eaten) for s in r1.swaps)
    p2 = sorted((s.mover, s.eaten) for s in r2.swaps)
    print("  pairing with ids (A,B,C,D)=(obj0,obj1,obj2,obj3): %s" % p1)
    print("  pairing with ids (A,B,C,D)=(obj2,obj1,obj0,obj3): %s" % p2)
    # translate back to roles
    role1 = sorted((("A" if m == "obj0" else "C"), ("B" if e == "obj1" else "D"))
                   for m, e in p1)
    role2 = sorted((("A" if m == "obj2" else "C"), ("B" if e == "obj1" else "D"))
                   for m, e in p2)
    print("  in roles: %s   vs   %s" % (role1, role2))
    if role1 != role2:
        finding(2, "pairing is an id artefact", "REFUTES",
                "the same pixels give pairing %s or %s depending only on which "
                "raster cell the segmenter numbered first. Both matchings are "
                "equally valid; the pass picks one and calls it physics."
                % (role1, role2))
    else:
        finding(2, "pairing is an id artefact", "holds",
                "the pairing survived relabelling: %s" % role1)


def line2_lexicographic_ids():
    """`sorted()` on 'obj10' vs 'obj2' is lexicographic, not numeric."""
    # obj2 and obj10 both vanish; only one eaten (obj9) is adjacent to both.
    movers = [track("obj2", 6, [(4, 4), (4, 4), None, None]),
              track("obj10", 6, [(4, 6), (4, 6), None, None])]
    eaten = track("obj9", 2, [(4, 5), (4, 5), (4, 5), (4, 5)])
    filler = [track("obj%d" % i, 3, [(0, i), (0, i), (0, i), (0, i)])
              for i in (0, 1, 3, 4, 5, 6, 7, 8, 11)]
    events = [vanish(1, "obj2"), vanish(1, "obj10"),
              recolor(1, "obj9", [(4, 5)], [6])]
    s = seg_of(movers + [eaten] + filler, events, n_frames=4)
    out, rep = repair_identity_swaps(s, COST)
    won = [sw.mover for sw in rep.swaps]
    print("  sorted() order over the two vanishers: %s" % sorted(["obj2", "obj10"]))
    print("  winner: %s" % won)
    if won == ["obj10"]:
        finding(2, "lexicographic id order", "REFUTES-defensibility",
                "with >=10 tracks the tie-break is 'obj10' < 'obj2' -- string "
                "order, not creation order. The stated tie-break intention "
                "(deterministic by id) is met, but the ordering is arbitrary "
                "in a way nobody wrote down.")
    else:
        finding(2, "lexicographic id order", "note", "winner was %s" % won)


def line2_greedy_loses_a_repair():
    """Greedy first-fit is not a maximum matching: one genuine swap is dropped,
    and dropped *silently* -- `taken_eaten` skips record no near miss."""
    # m1=obj0 at (1,1) is adjacent to e1=obj1 (1,2) and e2=obj3 (2,1).
    # m2=obj2 at (1,3) is adjacent to e1 only.
    # Maximum matching is {m1->e2, m2->e1}: two repairs.  Greedy takes m1->e1.
    m1 = track("obj0", 6, [(1, 1), (1, 1), None, None])
    e1 = track("obj1", 2, [(1, 2), (1, 2), (1, 2), (1, 2)])
    m2 = track("obj2", 6, [(1, 3), (1, 3), None, None])
    e2 = track("obj3", 2, [(2, 1), (2, 1), (2, 1), (2, 1)])
    events = [vanish(1, "obj0"), vanish(1, "obj2"),
              recolor(1, "obj1", [(1, 2)], [6]),
              recolor(1, "obj3", [(2, 1)], [6])]
    s = seg_of([m1, e1, m2, e2], events, n_frames=4)
    out, rep = repair_identity_swaps(s, COST)
    print("  greedy result: %s" % json.dumps(summarize(out, rep), sort_keys=True))
    if len(rep.swaps) == 2:
        finding(2, "a perfect matching exists", "holds", "found both swaps")
    elif len(rep.swaps) == 0:
        finding(2, "a perfect matching exists", "note",
                "refused whole: two movers and two eaten with a unique perfect "
                "matching (m1->e2, m2->e1) are called ambiguous because the "
                "contested test is per-track, not per-matching. Sound but "
                "incomplete -- a real hand-over goes unrepaired.")
    else:
        finding(2, "a perfect matching exists", "REFUTES-completeness",
                "picked %d of the 2 available pairs by track-id order"
                % len(rep.swaps))

    # and the *silent* drop: eaten already taken -> `continue`, no near miss
    m1b = track("obj0", 6, [(1, 1), (1, 1), None, None])
    m2b = track("obj2", 6, [(1, 3), (1, 3), None, None])
    e1b = track("obj1", 2, [(1, 2), (1, 2), (1, 2), (1, 2)])
    ev = [vanish(1, "obj0"), vanish(1, "obj2"), recolor(1, "obj1", [(1, 2)], [6])]
    s2 = seg_of([m1b, e1b, m2b], ev, n_frames=4)
    out2, rep2 = repair_identity_swaps(s2, COST)
    print("  contested single eaten: swaps=%s near_misses=%s"
          % ([(x.mover, x.eaten) for x in rep2.swaps], rep2.near_misses))
    if len(rep2.swaps) == 1 and not rep2.near_misses:
        finding(2, "contested eaten is silent", "REFUTES-reporting",
                "two movers claim the same eaten object; the loser leaves no "
                "near miss at all, so the promised 'forcing case for the next "
                "rung' is missing exactly where the evidence is ambiguous.")


# ============================================================================
# LINE 3 -- STRUCTURAL CORRUPTION
# ============================================================================

def line3_invariants_on_a_clean_repair():
    head("LINE 3 -- STRUCTURAL INVARIANTS OF THE RETURNED SEGMENTATION")
    mover = track("obj0", 6, [(1, 1), (2, 1), None, None])
    eaten = track("obj1", 2, [(3, 1), (3, 1), (3, 1), (3, 1)])
    events = [move(0, "obj0", 1, 0), vanish(1, "obj0"),
              recolor(1, "obj1", [(3, 1)], [6])]
    s = seg_of([mover, eaten], events, n_frames=4, declaration_bits=20)
    out, rep = repair_identity_swaps(s, COST)
    problems = check_invariants(out, "clean repair")
    ok, want, got = bits_are_consistent(out, COST)
    print("  invariants: %s" % (problems or "clean"))
    print("  bits: declared %d, recomputed %d (%s)"
          % (got, want, "consistent" if ok else "INCONSISTENT"))
    if problems:
        finding(3, "invariants/clean repair", "REFUTES", "; ".join(problems))
    else:
        finding(3, "invariants/clean repair", "holds",
                "masks==anchors==n_frames, no orphan events, no overlap, "
                "no empty track; script_bits = before + sum(deltas)")


def line3_ragged_masks():
    """A track whose masks list is shorter than the mover's."""
    mover = track("obj0", 6, [(1, 1), (2, 1), None, None, None, None])   # 6 long
    eaten = track("obj1", 2, [(3, 1), (3, 1), (3, 1), (3, 1)])           # 4 long
    events = [move(0, "obj0", 1, 0), vanish(1, "obj0"),
              recolor(1, "obj1", [(3, 1)], [6])]
    s = seg_of([mover, eaten], events, n_frames=6)
    _ragged_case("ragged masks (eaten shorter)", s, 6)

    # the other direction: the eaten track is longer than the mover
    mover2 = track("obj0", 6, [(1, 1), (2, 1), None, None])              # 4 long
    eaten2 = track("obj1", 2, [(3, 1)] * 6)                              # 6 long
    ev = [move(0, "obj0", 1, 0), vanish(1, "obj0"),
          recolor(1, "obj1", [(3, 1)], [6])]
    _ragged_case("ragged masks (mover shorter)",
                 seg_of([mover2, eaten2], ev, n_frames=6), 6)


def _ragged_case(tag, s, n):
    """A ragged input may be refused, but it must not be silently re-threaded
    into a worse-formed output."""
    before = [(t.track_id, list(t.masks), list(t.anchors)) for t in s.tracks]
    try:
        out, rep = repair_identity_swaps(s, COST)
    except Exception as exc:  # noqa: BLE001
        finding(3, tag, "REFUTES",
                "%s: %s -- the copy loop indexes the other track unguarded."
                % (type(exc).__name__, exc))
        return
    after = [(t.track_id, list(t.masks), list(t.anchors)) for t in out.tracks]
    refused = not rep.applied and out is s and after == before
    why = [m["why"][:40] for m in rep.near_misses]
    print("  %s: applied=%s returned_input=%s near=%s"
          % (tag, rep.applied, out is s, why))
    if refused:
        finding(3, tag, "holds",
                "refused whole and returned the input untouched (%s)"
                % (why[0] if why else "no reason given"))
        return
    problems = check_invariants(out, tag, n_frames=n)
    if problems:
        finding(3, tag, "REFUTES", "; ".join(problems[:3]))
    else:
        finding(3, tag, "holds", "re-threaded a ragged input into a clean one")


def line3_anchor_mask_desync():
    """anchors shorter than masks -- the copy loop indexes both by len(masks)."""
    mover = Track(track_id="obj0", first_frame=0, color=6, shape=(1, 1),
                  rel_cells=((0, 0),),
                  anchors=[(1, 1), (2, 1)],                    # 2 long
                  masks=[((1, 1),), ((2, 1),), None, None])    # 4 long
    eaten = track("obj1", 2, [(3, 1), (3, 1), (3, 1), (3, 1)])
    events = [move(0, "obj0", 1, 0), vanish(1, "obj0"),
              recolor(1, "obj1", [(3, 1)], [6])]
    _ragged_case("anchors shorter than masks",
                 seg_of([mover, eaten], events, n_frames=4), 4)


def line3_empty_track_and_aliasing():
    """Can a track end up entirely empty?  And is the input aliased?"""
    # eaten is present only at t, so after the repair it keeps exactly one mask
    mover = track("obj0", 6, [None, (2, 1), None, None])
    eaten = track("obj1", 2, [None, (3, 1), (3, 1), (3, 1)])
    events = [vanish(1, "obj0"), recolor(1, "obj1", [(3, 1)], [6])]
    s = seg_of([mover, eaten], events, n_frames=4)
    out, rep = repair_identity_swaps(s, COST)
    empties = [t.track_id for t in out.tracks if all(m is None for m in t.masks)]
    print("  minimal-lifetime eaten: empties=%s" % empties)
    if empties:
        finding(3, "empty track survives in tracks", "REFUTES",
                "tracks %s have no mask in any frame yet remain in "
                "Segmentation.tracks" % empties)
    else:
        finding(3, "empty track survives in tracks", "holds",
                "the eaten track always keeps its mask at t, so it cannot empty")

    # aliasing: params values are shallow-copied
    src = seg_of([track("obj0", 7, [(1, 1)] * 4), track("obj1", 5, [(3, 3)] * 4)],
                 [recolor(1, "obj0", [(1, 1)], [8])], n_frames=4)
    out2, rep2 = repair_identity_swaps(src, COST)
    aliased = out2.events[0].params["cells"] is src.events[0].params["cells"]
    if aliased and out2 is src:
        finding(3, "no-op returns the input object", "note",
                "with zero swaps the *input* Segmentation is returned by "
                "identity, so callers cannot assume they own the result")
    # and with a swap, the nested list objects are still shared
    m = track("obj0", 6, [(2, 1), (2, 1), None, None])
    e = track("obj1", 2, [(3, 1)] * 4)
    ev = [vanish(1, "obj0"), recolor(1, "obj1", [(3, 1)], [6]),
          move(2, "obj1", 0, 1)]
    s3 = seg_of([m, e], ev, n_frames=4)
    keep = s3.events[2].params
    out3, _ = repair_identity_swaps(s3, COST)
    shared = any(o.params is keep for o in out3.events)
    if shared:
        finding(3, "params dict shallow-copied", "note",
                "event params are dict()-copied but their list values are "
                "shared with the input; mutating the output mutates the input")


def line3_two_cost_models_in_one_script():
    """`choose_operator` hands the repair a CostModel built from
    `len(seg.tracks)`, but the script was written by `segment_trajectory` with
    `max_objects = max components in any single frame`.  When those differ the
    repaired events carry a wider object-id field than every other event in the
    same script, and `script_bits` stops being the length of any one code."""
    from pipeline.board import extract_board, object_layer
    from pipeline.engines_stage import background_color
    from world.ground_truth import read_trace

    worlds_dir = os.path.join(ROOT, "worldgen", "out", "worlds")
    bad = []
    for world in sorted(os.listdir(worlds_dir)):
        path = os.path.join(worlds_dir, world, "raw_trace.jsonl")
        if not os.path.isfile(path):
            continue
        frames, _a, _w = read_trace(path)
        board = extract_board(frames)
        bg = background_color(board, frames)
        layer = object_layer(frames, board, background=bg)
        raw = segment_operators.segment_with(
            "connected_components(4)+uniform_color", layer, background=bg)
        per_frame = max(len(_seg.connected_components(f, bg, True)) for f in layer)
        c_written = CostModel(len(layer[0]), len(layer[0][0]), max_objects=per_frame)
        c_repair = CostModel(len(layer[0]), len(layer[0][0]),
                             max_objects=max(len(raw.tracks), 1))
        if c_written.b_objid != c_repair.b_objid:
            _out, rp = repair_identity_swaps(raw, c_repair)
            if rp.swaps:
                bad.append((world, c_written.b_objid, c_repair.b_objid,
                            len(rp.swaps),
                            rp.script_bits_after - rp.script_bits_before))
    for row in bad:
        print("  %-22s b_objid written=%d repaired=%d swaps=%d delta=%d"
              % row)
    if bad:
        finding(3, "two cost models in one script", "REFUTES",
                "on %d worlds the repair prices its new events with b_objid=%d "
                "while every other event in the same script uses b_objid=%d. "
                "The advertised '+2 bits per swap' becomes +%d, and the "
                "script_bits that `choose_operator` compares between operators "
                "is no longer a single code length."
                % (len(bad), bad[0][2], bad[0][1], bad[0][4] // bad[0][3]))
    else:
        finding(3, "two cost models in one script", "holds",
                "the two models agreed on every world")


def line3_delta_is_not_two():
    """The docstring's '+2 bits per repaired swap' holds only for a one-cell
    mover: delta = move_bits - recolor_bits(k) = 6 - 4k."""
    rows = []
    for k in (1, 2, 3):
        cells = tuple((0, i) for i in range(k))
        mover = track("obj0", 6, [(1, 1), (2, 1), None, None], rel_cells=cells,
                      shape=(1, k))
        eaten = track("obj1", 2, [(3, 1)] * 4, rel_cells=cells, shape=(1, k))
        events = [move(0, "obj0", 1, 0), vanish(1, "obj0"),
                  recolor(1, "obj1", [(3, 1 + i) for i in range(k)], [6] * k)]
        s = seg_of([mover, eaten], events, n_frames=4)
        out, rp = repair_identity_swaps(s, COST)
        rows.append((k, rp.script_bits_after - rp.script_bits_before,
                     len(rp.swaps)))
    print("  (cells, delta_bits, swaps): %s" % rows)
    if any(d != 2 for _k, d, n in rows if n):
        finding(3, "'+2 bits per swap' is one-cell only", "note",
                "delta is %s for 1/2/3-cell movers; for k>=2 the repair is a "
                "net *saving*, which also means the matcher would never have "
                "picked the wrong reading there in the first place."
                % [d for _k, d, _n in rows])


# ============================================================================
# LINE 4 -- CHAINS AND CYCLES
# ============================================================================

def line4_chain():
    head("LINE 4 -- CHAINS, CYCLES AND RE-ATTRIBUTION")
    # A eats B at t=1; the merged track then eats C at t=3.
    A = track("obj0", 6, [(1, 1), (2, 1), None, None, None, None])
    B = track("obj1", 2, [(3, 1), (3, 1), (3, 1), (3, 1), None, None])
    C = track("obj2", 4, [(4, 1)] * 6)
    events = [move(0, "obj0", 1, 0),
              vanish(1, "obj0"), recolor(1, "obj1", [(3, 1)], [6]),
              vanish(3, "obj1"), recolor(3, "obj2", [(4, 1)], [6])]
    s = seg_of([A, B, C], events, n_frames=6)
    out, rep = repair_identity_swaps(s, COST)
    print("  chain: %s" % json.dumps(summarize(out, rep), sort_keys=True))
    print("  obj0 anchors: %s" % (out.tracks[0].anchors,))
    problems = check_invariants(out, "chain")
    if len(rep.swaps) == 2 and not problems:
        finding(4, "A eats B then eats C", "holds",
                "both hops repaired, obj0 carries the whole trajectory, "
                "invariants clean")
    else:
        finding(4, "A eats B then eats C", "REFUTES",
                "swaps=%d problems=%s" % (len(rep.swaps), problems))


def line4_reciprocal():
    """B eats A at t=0 and the merged track is itself eaten at t=1: can the
    re-attribution loop ever route an event back to a track that already gave
    its future away, i.e. can the hand-over graph contain a cycle?"""
    A = track("obj0", 3, [(1, 1), (1, 1), None, None])
    B = track("obj1", 6, [(1, 2), None, None, None])
    C = track("obj2", 2, [(1, 0), (1, 0), (1, 0), (1, 0)])
    events = [vanish(0, "obj1"), recolor(0, "obj0", [(1, 1)], [6]),
              vanish(1, "obj0"), recolor(1, "obj2", [(1, 0)], [6])]
    s = seg_of([A, B, C], events, n_frames=4)
    out, rep = repair_identity_swaps(s, COST)
    print("  reciprocal: %s" % json.dumps(summarize(out, rep), sort_keys=True))
    print("  events: %s" % [(e.t, e.type, e.track) for e in out.events])
    problems = check_invariants(out, "reciprocal")
    edges = [(x.mover, x.eaten) for x in rep.swaps]
    # a cycle would need some track to be both a source and a sink; the eaten
    # track is nulled from t+1 on, so it can never be `_present` as a later
    # mover.  Check that empirically rather than by argument.
    sinks = {e for _m, e in edges}
    movers_after = {m for m, _e in edges}
    print("  hand-over edges: %s" % edges)
    if sinks & movers_after:
        finding(4, "hand-over cycle", "REFUTES",
                "track(s) %s are both consumed and consuming" % (sinks & movers_after))
    else:
        finding(4, "hand-over cycle", "holds",
                "no cycle: an eaten track has its masks nulled from t+1 on, so "
                "`_present` can never make it a later mover; the graph is a "
                "forest of chains (%s)" % edges)
    if problems:
        finding(4, "reciprocal invariants", "REFUTES", "; ".join(problems[:3]))


def line4_rewrite_too_much():
    """The re-attribution loop rewrites *every* later event of the eaten track,
    including one that describes a body the mover never had."""
    # obj1 is consumed at t=1 -- but obj1's track has a gap and a return at
    # t=3 (exactly the shape `reidentify` produces).  The mover inherits the
    # return: it teleports to the respawn point with no event saying so.
    A = track("obj0", 6, [(1, 1), (2, 1), None, None, None, None])
    B = track("obj1", 2, [(3, 1), (3, 1), (3, 1), None, (6, 6), (6, 6)])
    events = [move(0, "obj0", 1, 0),
              vanish(1, "obj0"), recolor(1, "obj1", [(3, 1)], [6]),
              vanish(2, "obj1"),
              Event(t=3, type="appear", track="obj1", params={"at": [6, 6]},
                    bits=COST.appear_bits(1, 1, 1))]
    s = seg_of([A, B], events, n_frames=6)
    out, rep = repair_identity_swaps(s, COST)
    a = next(t for t in out.tracks if t.track_id == "obj0")
    print("  gapped eaten: obj0 anchors after repair = %s" % (a.anchors,))
    print("  events: %s" % [(e.t, e.type, e.track) for e in out.events])
    if a.anchors[4] == (6, 6):
        finding(4, "inherits the eaten track's return", "REFUTES",
                "the mover consumed obj1 at t=1, obj1 died at t=2, and the "
                "mover is then handed obj1's t=3 respawn at (6,6) -- an "
                "un-narrated teleport across the board, plus the appear event "
                "re-labelled as the mover appearing while it already exists.")
    else:
        finding(4, "inherits the eaten track's return", "holds", "not inherited")


def line4_same_track_both_roles():
    """Can one track be mover and eaten at the same t?"""
    A = track("obj0", 6, [(1, 1), (1, 1), None, None])
    B = track("obj1", 2, [(1, 2), (1, 2), (1, 2), (1, 2)])
    events = [vanish(1, "obj0"), recolor(1, "obj0", [(1, 1)], [6]),
              recolor(1, "obj1", [(1, 2)], [6])]
    s = seg_of([A, B], events, n_frames=4)
    out, rep = repair_identity_swaps(s, COST)
    print("  self-pair: %s" % json.dumps(summarize(out, rep), sort_keys=True))
    self_pairs = [x for x in rep.swaps if x.mover == x.eaten]
    if self_pairs:
        finding(4, "self-consumption", "REFUTES", "a track consumed itself")
    else:
        finding(4, "self-consumption", "holds",
                "guarded twice: the id check, and mover must be absent at t+1 "
                "while eaten must be present at t+1")


# ============================================================================
# LINE 5 -- INTERACTION WITH reidentify
# ============================================================================

def line5_resurrects_a_consumed_object():
    head("LINE 5 -- ORDERING AGAINST reidentify")
    # obj1 is a token consumed at t=1.  A *different* token of the same colour
    # and shape spawns at t=3.  Before the swap repair obj1's track ran to the
    # end (holding the mover's stolen identity) and overlapped the newcomer, so
    # reidentify could not merge.  After the repair obj1's lifetime is [0,1],
    # disjoint from [3,5] -- and reidentify merges the *consumed* token with
    # the newcomer.
    def scene():
        A = track("obj0", 6, [(1, 1), (2, 1), None, None, None, None])
        B = track("obj1", 2, [(3, 1), (3, 1), (3, 1), (3, 1), (3, 1), (3, 1)])
        C = track("obj2", 2, [None, None, None, (5, 5), (5, 5), (5, 5)])
        events = [move(0, "obj0", 1, 0),
                  vanish(1, "obj0"), recolor(1, "obj1", [(3, 1)], [6]),
                  Event(t=2, type="appear", track="obj2", params={"at": [5, 5]},
                        bits=COST.appear_bits(1, 1, 1))]
        return seg_of([A, B, C], events, n_frames=6)

    # forward order, as `choose_operator` runs it
    s = scene()
    swapped, srep = repair_identity_swaps(s, COST)
    merged, mrep = reidentify(swapped if srep.applied else s, COST)
    print("  forward  swaps=%d  merged=%s applied=%s"
          % (len(srep.swaps), mrep.merged, mrep.applied))
    # reverse order
    s2 = scene()
    m2, mrep2 = reidentify(s2, COST)
    print("  reverse  reidentify-first merged=%s applied=%s"
          % (mrep2.merged, mrep2.applied))

    if srep.applied and mrep.applied and mrep.merged:
        finding(5, "swap-then-reidentify resurrects", "REFUTES",
                "the repair truncates the consumed token to [0,1], which makes "
                "it disjoint from an unrelated look-alike spawning at t=3; "
                "reidentify then merges them (%s), so a consumed object is "
                "declared to have come back. Reverse order merges %s -- "
                "nothing -- because before the repair the lifetimes overlap."
                % (mrep.merged, mrep2.merged or "nothing"))
    else:
        finding(5, "swap-then-reidentify resurrects", "holds",
                "swap applied=%s, merge applied=%s" % (srep.applied, mrep.applied))


def line5_reverse_order_is_also_bad():
    """And the reverse order is not a fix: reidentify first makes gapped tracks,
    which line4_rewrite_too_much shows the swap pass then mis-inherits."""
    finding(5, "reverse order as a remedy", "note",
            "reversing does not help: reidentify-first produces gapped tracks, "
            "and the swap pass hands the whole post-t suffix (gap and return) "
            "to the mover -- see line 4's 'inherits the eaten track's return'.")


# ============================================================================
# LINE 6 -- BOUNDARIES
# ============================================================================

def line6_boundaries():
    head("LINE 6 -- BOUNDARIES")
    # t = 0
    A = track("obj0", 6, [(1, 1), None, None, None])
    B = track("obj1", 2, [(2, 1), (2, 1), (2, 1), (2, 1)])
    s = seg_of([A, B], [vanish(0, "obj0"), recolor(0, "obj1", [(2, 1)], [6])],
               n_frames=4)
    out, rep = repair_identity_swaps(s, COST)
    p = check_invariants(out, "t0")
    finding(6, "t = 0", "holds" if rep.applied and not p else "REFUTES",
            "swaps=%d problems=%s" % (len(rep.swaps), p or "none"))

    # t = last transition
    A = track("obj0", 6, [(1, 1), (1, 1), (1, 1), None])
    B = track("obj1", 2, [(2, 1), (2, 1), (2, 1), (2, 1)])
    s = seg_of([A, B], [vanish(2, "obj0"), recolor(2, "obj1", [(2, 1)], [6])],
               n_frames=4)
    out, rep = repair_identity_swaps(s, COST)
    p = check_invariants(out, "tlast")
    print("  last transition: obj0=%s obj1=%s"
          % (out.tracks[0].anchors, out.tracks[1].anchors))
    finding(6, "t = last transition", "holds" if rep.applied and not p else "REFUTES",
            "swaps=%d problems=%s" % (len(rep.swaps), p or "none"))

    # zero-length / single-frame trajectory
    try:
        s = seg_of([], [], n_frames=0)
        out, rep = repair_identity_swaps(s, COST)
        finding(6, "empty trajectory", "holds",
                "no events -> horizon -1 -> input returned unchanged (%s)"
                % (out is s))
    except Exception as exc:  # noqa: BLE001
        finding(6, "empty trajectory", "REFUTES", "%s: %s" % (type(exc).__name__, exc))

    # a vanish at the very last frame index, past the end of the mask list
    A = track("obj0", 6, [(1, 1), (1, 1)])
    B = track("obj1", 2, [(2, 1), (2, 1)])
    s = seg_of([A, B], [vanish(1, "obj0"), recolor(1, "obj1", [(2, 1)], [6])],
               n_frames=2)
    out, rep = repair_identity_swaps(s, COST)
    print("  vanish at the final frame: swaps=%d obj0=%s obj1=%s"
          % (len(rep.swaps), out.tracks[0].anchors, out.tracks[1].anchors))
    if rep.applied:
        finding(6, "vanish past the last frame", "REFUTES",
                "the mover is still *present* in the final frame (its mask "
                "there was never cleared) yet a vanish at that index made it "
                "eligible; the eaten track keeps its body too -- two objects "
                "on one square.")
    else:
        finding(6, "vanish past the last frame", "holds", "refused")


# ============================================================================
# EMPIRICAL SWEEP
# ============================================================================

AGENT = 6


def _agent_cells(frames):
    """The one cell showing colour 6 -- worldgen verifies this is unique."""
    out = []
    for f in frames:
        cell = None
        for r, row in enumerate(f):
            for c, v in enumerate(row):
                if v == AGENT:
                    cell = (r, c)
        out.append(cell)
    return out


def _agreement(track_obj, truth):
    n = min(len(track_obj.anchors), len(truth))
    return sum(1 for i in range(n) if track_obj.anchors[i] == truth[i]), len(truth)


def _pipeline(layer, background, with_repair):
    """`choose_operator`, optionally with the repair switched off."""
    best = None
    for name in sorted(segment_operators.OPERATORS):
        seg = segment_operators.segment_with(name, layer, background=background)
        cost = CostModel(len(layer[0]), len(layer[0][0]),
                         max_objects=max(len(seg.tracks), 1))
        rep = None
        if with_repair:
            repaired, rep = repair_identity_swaps(seg, cost)
            if rep.applied:
                seg = repaired
        merged, mrep = reidentify(seg, cost)
        if mrep.applied:
            seg = merged
        row = (seg.script_bits, name, seg, rep)
        if best is None or row[:2] < best[:2]:
            best = row
    return best


def sweep():
    head("EMPIRICAL SWEEP -- every worldgen world, read-only")
    from pipeline.board import extract_board, object_layer
    from pipeline.engines_stage import background_color
    from world.ground_truth import read_trace

    worlds_dir = os.path.join(ROOT, "worldgen", "out", "worlds")
    names = sorted(d for d in os.listdir(worlds_dir)
                   if os.path.isfile(os.path.join(worlds_dir, d, "raw_trace.jsonl")))
    rows = {}
    wrong = []
    print("  %-22s %5s %6s %5s %-7s  %-9s %-9s %s"
          % ("world", "swaps", "dbits", "near", "mover", "agree/on",
             "agree/off", "flags"))
    for world in names:
        path = os.path.join(worlds_dir, world, "raw_trace.jsonl")
        try:
            frames, actions, wins = read_trace(path)
            truth = _agent_cells(frames)
            board = extract_board(frames)
            background = background_color(board, frames)
            layer = object_layer(frames, board, background=background)

            _b, op, seg, swap_report = _pipeline(layer, background, True)
            _b2, _op2, seg_off, _n = _pipeline(layer, background, False)
            rep = swap_report.as_json() if swap_report else {
                "n_swaps": 0, "delta_bits": 0, "near_misses": [], "swaps": []}

            mover = multi_miner.mover_track(seg)
            mtrack = next(t for t in seg.tracks if t.track_id == mover)
            on_hit, n = _agreement(mtrack, truth)
            mover_off = multi_miner.mover_track(seg_off)
            off_track = next(t for t in seg_off.tracks if t.track_id == mover_off)
            off_hit, _ = _agreement(off_track, truth)

            moves = {}
            for e in seg.events:
                if e.type == "move":
                    moves[e.track] = moves.get(e.track, 0) + 1
            cost = CostModel(len(layer[0]), len(layer[0][0]),
                             max_objects=max(len(seg.tracks), 1))
            ok, want, got = bits_are_consistent(seg, cost)
            problems = check_invariants(seg, world)

            # was anything the pass declared "consumed" still on the board?
            still_there = []
            for s in rep["swaps"]:
                eaten_id, t = s["eaten"], s["t"]
                et = next((x for x in seg.tracks if x.track_id == eaten_id), None)
                if et is None or et.anchors[t] is None:
                    continue
                r, c = et.anchors[t]
                later = {layer[i][r][c] for i in range(t + 1, len(layer))}
                later -= {background, AGENT}
                if later:
                    still_there.append((eaten_id, t, sorted(later)))

            # two simultaneous colour-6 tracks contradicts worldgen's own
            # verified `agent_unique` invariant
            dup6 = 0
            six = [t for t in seg.tracks if t.color == AGENT]
            for i in range(len(frames)):
                live = [t.track_id for t in six
                        if i < len(t.masks) and t.masks[i] is not None]
                if len(live) > 1:
                    dup6 += 1

            flags = []
            if still_there:
                flags.append("CONSUMED-BUT-STILL-VISIBLE%s" % still_there)
            if dup6:
                flags.append("TWO-COLOUR-6-TRACKS-IN-%d-FRAMES" % dup6)
            if on_hit < n:
                flags.append("MOVER-MISTRACKS-AGENT(%d/%d)" % (on_hit, n))
            if problems:
                flags.append("INVARIANT:" + problems[0])
            if not ok:
                flags.append("BITS %d!=%d" % (got, want))
            if rep["n_swaps"] and rep["delta_bits"] != 2 * rep["n_swaps"]:
                flags.append("DELTA!=2/swap(%d)" % rep["delta_bits"])

            rows[world] = {
                "n_swaps": rep["n_swaps"], "delta_bits": rep["delta_bits"],
                "near_misses": len(rep["near_misses"]),
                "near_miss_kinds": sorted({m["why"][:28]
                                           for m in rep["near_misses"]}),
                "mover": mover, "mover_color": mtrack.color,
                "mover_agrees_with_agent": [on_hit, n],
                "mover_agrees_without_repair": [off_hit, n],
                "operator": op, "tracks": len(seg.tracks),
                "move_counts": moves, "flags": flags,
                "consumed_but_still_visible": still_there,
                "frames_with_two_colour6_tracks": dup6,
                "swaps": [(s["mover"], s["eaten"], s["t"]) for s in rep["swaps"]],
            }
            if rep["n_swaps"] and (still_there or dup6 or on_hit < n):
                wrong.append(world)
            print("  %-22s %5d %6d %5d %-7s  %-9s %-9s %s"
                  % (world, rep["n_swaps"], rep["delta_bits"],
                     len(rep["near_misses"]), mover,
                     "%d/%d" % (on_hit, n), "%d/%d" % (off_hit, n),
                     " ".join(flags) or "-"))
        except Exception as exc:  # noqa: BLE001
            rows[world] = {"error": "%s: %s" % (type(exc).__name__, exc)}
            traceback.print_exc()
            print("  %-22s ERROR %s: %s" % (world, type(exc).__name__, exc))

    if wrong:
        finding(0, "empirical: swap fires and is wrong", "REFUTES",
                "worlds %s: a swap fires and the result is demonstrably wrong "
                "against worldgen's own verified ground truth." % wrong)
    else:
        finding(0, "empirical: swap fires and is wrong", "holds",
                "every world where a swap fired came out consistent")
    return rows


ATTACKS = [
    ("line1_false_positive_traffic_light", 1),
    ("line1_false_negative_stale_color", 1),
    ("line1_recolor_cells_unchecked", 1),
    ("line2_two_perfect_matchings", 2),
    ("line2_lexicographic_ids", 2),
    ("line2_greedy_loses_a_repair", 2),
    ("line3_invariants_on_a_clean_repair", 3),
    ("line3_two_cost_models_in_one_script", 3),
    ("line3_delta_is_not_two", 3),
    ("line3_ragged_masks", 3),
    ("line3_anchor_mask_desync", 3),
    ("line3_empty_track_and_aliasing", 3),
    ("line4_chain", 4),
    ("line4_reciprocal", 4),
    ("line4_rewrite_too_much", 4),
    ("line4_same_track_both_roles", 4),
    ("line5_resurrects_a_consumed_object", 5),
    ("line5_reverse_order_is_also_bad", 5),
    ("line6_boundaries", 6),
]


def main():
    source = sys.argv[1] if len(sys.argv) > 1 else "worktree"
    digest, nlines = load_pass(source)
    print("ARTEFACT UNDER TEST: %s  sha256[:16]=%s  %d lines"
          % (source, digest, nlines))

    for name, line in ATTACKS:
        try:
            globals()[name]()
        except Exception as exc:  # noqa: BLE001
            traceback.print_exc()
            finding(line, name, "CRASH", "%s: %s" % (type(exc).__name__, exc))
    try:
        rows = sweep()
    except Exception as exc:  # noqa: BLE001
        traceback.print_exc()
        finding(0, "empirical sweep", "CRASH", "%s: %s" % (type(exc).__name__, exc))
        rows = {}

    head("SUMMARY  (%s / %s)" % (source, digest))
    refuting = [f for f in FINDINGS
                if f["verdict"].startswith("REFUTES") or f["verdict"] == "CRASH"]
    for f in FINDINGS:
        print("  line %d  %-20s %s" % (f["line"], f["verdict"], f["tag"]))
    print("\n  %d refuting/crashing findings out of %d checks"
          % (len(refuting), len(FINDINGS)))
    out = os.path.join(HERE, "..", "adversarial_identity_swap.%s.json"
                       % source.replace("/", "_"))
    with open(os.path.abspath(out), "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"artefact": {"source": source, "sha256_16": digest,
                                "lines": nlines},
                   "findings": FINDINGS, "worlds": rows}, fh, indent=2,
                  sort_keys=True)
        fh.write("\n")
    print("  wrote %s" % os.path.abspath(out))


if __name__ == "__main__":
    main()
