"""`mdl_segmenter` — four invariants, all recomputed from the frames themselves.

What is checked here is narrower than it first looks, and the narrowing is the
point. Two properties that would be natural to assert are **not** asserted,
because the engine never claimed them:

* **no frame round-trip.** There is no replay function anywhere in the rig, and a
  `Segmentation` could not support one: `Track` carries a single `color` (None
  when the object is not uniform) and no per-frame per-cell colours, and an
  `appear` event carries only `{"at": [r, c]}`. The "script" is a bit-accounting
  scheme, not a decodable encoding. The strongest true statement in that
  direction is about **occupancy**, which is `masks_partition_the_foreground`;
* **no compression guarantee.** `script_bits < baseline_bits` holds on the rig's
  own fixture and is a *fixture result*, not a contract — the acceptance
  threshold in `DECISIONS.md` D-005 is stated against Fixture A specifically. On
  random worlds the script is routinely the longer of the two. Asserting it
  would file a bug against a promise nobody made. What *is* structural is the
  bit identity, and that is `script_bits_identity`.

| invariant | claim under test |
|---|---|
| `masks_partition_the_foreground` | for every frame, the tracks' masks are pairwise disjoint and their union is exactly the non-background cells |
| `masks_follow_anchors` | each present mask is the track's `rel_cells` translated to its anchor — the shape is rigid, as `Track` says it is |
| `events_agree_with_tracks` | every `move`/`appear`/`vanish` event describes what the anchors actually did at that transition, and every such change has an event |
| `script_bits_identity` | `script_bits == declaration_bits + (n_frames-1)*8 + Σ event.bits` |
"""

from typing import Any, Dict, List, Sequence, Set, Tuple

from fuzzlab import rig  # noqa: F401  (path bootstrap)
from fuzzlab.props import finding

from engines import mdl_segmenter as engine  # noqa: E402

FAMILY = "gridworld"
ENGINE = "mdl_segmenter"

HEADER_BITS = 8          # CostModel.b_header, paid once per transition by both models


def _segment(world: Any):
    return engine.segment_trajectory(world.frames, background=world.spec_json()
                                     .get("background", 0))


def _foreground(frame: Sequence[Sequence[int]], background: int) -> Set[Tuple[int, int]]:
    return {(r, c) for r, row in enumerate(frame)
            for c, value in enumerate(row) if value != background}


# --------------------------------------------------------------- invariants

def masks_partition_the_foreground(world: Any) -> List[finding.Finding]:
    """Every non-background cell belongs to exactly one track, in every frame."""
    background = world.spec_json().get("background", 0)
    seg = _segment(world)
    out: List[finding.Finding] = []
    for t, frame in enumerate(world.frames):
        expected = _foreground(frame, background)
        seen: Dict[Tuple[int, int], str] = {}
        overlaps: List[Tuple[Tuple[int, int], str, str]] = []
        for track in seg.tracks:
            for cell in (track.mask_at(t) or ()):
                cell = tuple(cell)
                if cell in seen:
                    overlaps.append((cell, seen[cell], track.track_id))
                seen[cell] = track.track_id
        covered = set(seen)
        if overlaps:
            out.append(finding.violated(
                ENGINE, "masks_partition_the_foreground", world,
                "frame %d: %d cell(s) claimed by two tracks, e.g. %r by %s and %s"
                % (t, len(overlaps), overlaps[0][0], overlaps[0][1], overlaps[0][2]),
                frame=t, overlaps=len(overlaps)))
        if covered != expected:
            out.append(finding.violated(
                ENGINE, "masks_partition_the_foreground", world,
                "frame %d: %d foreground cell(s) uncovered, %d covered cell(s) "
                "are background"
                % (t, len(expected - covered), len(covered - expected)),
                frame=t,
                uncovered=sorted(expected - covered)[:8],
                spurious=sorted(covered - expected)[:8]))
        if out:
            break                     # one frame's diagnosis is enough to act on
    return out


def masks_follow_anchors(world: Any) -> List[finding.Finding]:
    """A present mask is `rel_cells` translated to `anchors[t]` — the shape is rigid."""
    seg = _segment(world)
    out: List[finding.Finding] = []
    for track in seg.tracks:
        for t, mask in enumerate(track.masks):
            anchor = track.anchors[t]
            if mask is None or anchor is None:
                if (mask is None) != (anchor is None):
                    out.append(finding.violated(
                        ENGINE, "masks_follow_anchors", world,
                        "track %s frame %d: mask and anchor disagree about "
                        "presence (mask=%s, anchor=%s)"
                        % (track.track_id, t, mask is not None, anchor is not None),
                        track=track.track_id, frame=t))
                continue
            expected = {(anchor[0] + dr, anchor[1] + dc) for dr, dc in track.rel_cells}
            if {tuple(c) for c in mask} != expected:
                out.append(finding.violated(
                    ENGINE, "masks_follow_anchors", world,
                    "track %s frame %d: mask is not rel_cells at anchor %r"
                    % (track.track_id, t, tuple(anchor)),
                    track=track.track_id, frame=t, anchor=list(anchor)))
                return out
    return out


def events_agree_with_tracks(world: Any) -> List[finding.Finding]:
    """The narration matches the anchors, in both directions.

    Both directions, because they fail differently: an event describing a motion
    that did not happen is a false statement in the script, and a motion with no
    event is a state change the caller is never told about — and the script's bit
    count is computed from the events, so an unnarrated change is also an
    under-priced script.
    """
    seg = _segment(world)
    by_track: Dict[str, Dict[int, List[Any]]] = {}
    for event in seg.events:
        by_track.setdefault(event.track, {}).setdefault(event.t, []).append(event)

    out: List[finding.Finding] = []
    for track in seg.tracks:
        events = by_track.get(track.track_id, {})
        for t in range(len(track.anchors) - 1):
            here, there = track.anchors[t], track.anchors[t + 1]
            kinds = {e.type for e in events.get(t, ())}
            if here is None and there is not None:
                expected = "appear"
            elif here is not None and there is None:
                expected = "vanish"
            elif here is not None and there is not None and tuple(here) != tuple(there):
                expected = "move"
            else:
                expected = None

            if expected is not None and expected not in kinds:
                out.append(finding.violated(
                    ENGINE, "events_agree_with_tracks", world,
                    "track %s transition %d: anchors say %s (%r -> %r) but the "
                    "events are %s"
                    % (track.track_id, t, expected, here, there, sorted(kinds) or "none"),
                    track=track.track_id, transition=t, expected=expected,
                    got=sorted(kinds)))
                return out
            for event in events.get(t, ()):
                if event.type != "move":
                    continue
                dy, dx = int(event.params["dy"]), int(event.params["dx"])
                if here is None or there is None or \
                        (here[0] + dy, here[1] + dx) != tuple(there):
                    out.append(finding.violated(
                        ENGINE, "events_agree_with_tracks", world,
                        "track %s transition %d: move event says (%d,%d) but the "
                        "anchor went %r -> %r"
                        % (track.track_id, t, dy, dx, here, there),
                        track=track.track_id, transition=t, dy=dy, dx=dx))
                    return out
    return out


def script_bits_identity(world: Any) -> List[finding.Finding]:
    """`script_bits == declaration_bits + (n_frames-1)*header + Σ event.bits`.

    The engine's own accounting identity, checked on random worlds rather than on
    the one fixture where it is currently asserted. Note what is *not* here: no
    claim that the script beats the baseline. See the module docstring.
    """
    seg = _segment(world)
    expected = (seg.declaration_bits
                + max(0, seg.n_frames - 1) * HEADER_BITS
                + sum(e.bits for e in seg.events))
    if seg.script_bits != expected:
        return [finding.violated(
            ENGINE, "script_bits_identity", world,
            "script_bits is %d, declaration %d + %d transitions x %d + events %d "
            "= %d" % (seg.script_bits, seg.declaration_bits,
                      max(0, seg.n_frames - 1), HEADER_BITS,
                      sum(e.bits for e in seg.events), expected),
            script_bits=seg.script_bits, expected=expected,
            declaration_bits=seg.declaration_bits, n_frames=seg.n_frames,
            n_events=len(seg.events))]
    return []


INVARIANTS = {
    "masks_partition_the_foreground": masks_partition_the_foreground,
    "masks_follow_anchors": masks_follow_anchors,
    "events_agree_with_tracks": events_agree_with_tracks,
    "script_bits_identity": script_bits_identity,
}


def check(world: Any) -> List[finding.Finding]:
    return finding.run_invariants(ENGINE, world, INVARIANTS)
