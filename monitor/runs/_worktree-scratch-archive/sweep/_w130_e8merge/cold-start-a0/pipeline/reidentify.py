"""Track re-identification: an object that comes back is the same object.

`mdl_segmenter` matches frame *t* against frame *t+1*. An object that vanishes
and returns three frames later cannot be matched by anything local, so every
return is a brand-new track. A0 never noticed — its Door opened once and stayed
open. A0′'s Switch is a toggle, so its Door closes and reopens repeatedly, and
the segmentation came back with **seven tracks for a three-object world**:

```
obj0  colour 7/8  the Switch          (one track, recolour matches fine)
obj1  colour 5    the Door, life 1
obj3  colour 5    the Door, life 2
obj4  colour 5    the Door, life 3
obj5  colour 5    the Door, life 4
obj6  colour 5    the Door, life 5
obj2  colour 6    the Cart
```

Five Doors is not a theory, and no downstream rule can be stated over an object
whose identity resets every time it is used.

## The repair, and why it is not a hack

Theoria 1.8's segmentation operator space explicitly includes template matching
alongside connected components and common-fate clustering. This is that: two
tracks are the same object when they have the **same template** (identical
relative cells and colours) and **disjoint lifetimes** — the second cannot be a
different thing that happens to look identical, because the first was not there.

And the merge is not asserted, it is **priced**. Re-declaring a returning object
costs `appear_bits` = vanish + a full declaration; naming one already in the
vocabulary costs `b_evtype + b_objid + b_pos`. The pass is applied only if the
total script gets shorter, which is the same criterion that chose the
segmentation operator in the first place.

Upstream is untouched: this consumes a `Segmentation` and returns a new one.
"""

from copy import deepcopy
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from engines.mdl_segmenter.costs import CostModel
from engines.mdl_segmenter.segmenter import Event, Segmentation, Track


@dataclass
class MergeReport:
    merged: List[Tuple[str, str]]
    script_bits_before: int
    script_bits_after: int
    tracks_before: int
    tracks_after: int
    applied: bool

    def as_json(self) -> Dict[str, object]:
        return {
            "merged": [{"into": a, "from": b} for a, b in self.merged],
            "script_bits_before": self.script_bits_before,
            "script_bits_after": self.script_bits_after,
            "saved_bits": self.script_bits_before - self.script_bits_after,
            "tracks_before": self.tracks_before,
            "tracks_after": self.tracks_after,
            "applied": self.applied,
            "operator": "template_match+disjoint_lifetime",
        }


def _lifetime(track: Track) -> Tuple[Optional[int], Optional[int]]:
    present = [i for i, mask in enumerate(track.masks) if mask is not None]
    return (present[0], present[-1]) if present else (None, None)


def _template(track: Track):
    return (tuple(track.rel_cells), track.color, tuple(track.shape))


def reidentify(seg: Segmentation, cost: CostModel) -> Tuple[Segmentation, MergeReport]:
    """Merge same-template, disjoint-lifetime tracks; keep it only if it pays."""
    tracks = list(seg.tracks)
    lifetimes = {t.track_id: _lifetime(t) for t in tracks}

    # A track that `identity_swap` recorded as eaten did not come back -- it was
    # consumed, and its short lifetime is the *output* of that repair rather than
    # evidence of a return.  Without this, the repair manufactures exactly the
    # disjoint-lifetime pair this pass gets wrong: truncating the consumed token
    # makes it disjoint from any later same-template look-alike, and the merge
    # then declares a consumed object to have reappeared.  Found by an
    # adversarial review of `identity_swap`; see D-A0-022.
    consumed = {event.track for event in seg.events
                if event.type == "vanish" and "consumed_by" in event.params}

    # Greedy left-to-right: each track joins the earliest compatible chain.
    owner: Dict[str, str] = {}
    chains: Dict[str, List[str]] = {}
    for track in tracks:
        start, _end = lifetimes[track.track_id]
        if start is None:
            continue
        if track.track_id in consumed:
            chains[track.track_id] = [track.track_id]
            owner[track.track_id] = track.track_id
            continue
        target = None
        for head in chains:
            if head in consumed:
                continue
            if _template(next(t for t in tracks if t.track_id == head)) != _template(track):
                continue
            last_end = max(lifetimes[m][1] for m in chains[head])
            if last_end is not None and last_end < start:
                target = head
                break
        if target is None:
            chains[track.track_id] = [track.track_id]
            owner[track.track_id] = track.track_id
        else:
            chains[target].append(track.track_id)
            owner[track.track_id] = target

    merged = [(head, member) for head, members in chains.items()
              for member in members[1:]]
    if not merged:
        return seg, MergeReport([], seg.script_bits, seg.script_bits,
                                len(tracks), len(tracks), applied=False)

    # --- rebuild ---------------------------------------------------------
    new_tracks: List[Track] = []
    for head, members in chains.items():
        base = deepcopy(next(t for t in tracks if t.track_id == head))
        for member in members[1:]:
            other = next(t for t in tracks if t.track_id == member)
            for i, mask in enumerate(other.masks):
                if mask is not None:
                    base.masks[i] = mask
                    base.anchors[i] = other.anchors[i]
        new_tracks.append(base)
    new_tracks.sort(key=lambda t: int(t.track_id[3:]))

    absorbed = {member for _head, member in merged}
    reappear_bits = cost.b_evtype + cost.b_objid + cost.b_pos
    new_events: List[Event] = []
    for original in seg.events:
        event = Event(t=original.t, type=original.type,
                      track=owner.get(original.track, original.track),
                      params=dict(original.params), bits=original.bits)
        # Only the *return* of an already-declared object gets the cheap code:
        # the object is in the vocabulary, so naming it is enough.
        if original.type == "appear" and original.track in absorbed:
            if reappear_bits < event.bits:
                event.bits = reappear_bits
                event.params["reidentified"] = True
        new_events.append(event)

    recomputed = seg.script_bits + sum(
        new.bits - old.bits for old, new in zip(seg.events, new_events)
    )

    report = MergeReport(
        merged=merged,
        script_bits_before=seg.script_bits,
        script_bits_after=recomputed,
        tracks_before=len(tracks),
        tracks_after=len(new_tracks),
        applied=recomputed <= seg.script_bits,
    )
    if not report.applied:
        return seg, report

    return Segmentation(
        tracks=new_tracks,
        events=new_events,
        script_bits=recomputed,
        baseline_bits=seg.baseline_bits,
        declaration_bits=seg.declaration_bits,
        n_frames=seg.n_frames,
    ), report
