"""mdl_segmenter -- public entry points."""

from typing import Any, Dict, List, Optional, Sequence

from common.candidates import emit, make_candidate
from engines.mdl_segmenter.segmenter import (  # noqa: F401
    Component,
    Event,
    Segmentation,
    Track,
    connected_components,
    segment_trajectory,
)

ENGINE = "mdl_segmenter"


def to_payload(seg: Segmentation, track: Track) -> Dict[str, Any]:
    """The object_hypothesis payload shape; frozen in this engine's README."""
    track_events = [e for e in seg.events if e.track == track.track_id]
    return {
        "object_id": track.track_id,
        "segment_operator": "connected_components(4)+bipartite_common_fate",
        "color": track.color,
        "shape": list(track.shape),
        "cells": [list(c) for c in track.rel_cells],
        "first_frame": track.first_frame,
        "anchors": [list(a) if a is not None else None for a in track.anchors],
        "events": [e.as_json() for e in track_events],
        "mdl": {
            "script_bits": seg.script_bits,
            "baseline_bits": seg.baseline_bits,
            "gain_bits": seg.gain_bits,
            "ratio": round(seg.compression_ratio, 6),
        },
    }


def candidates(seg: Segmentation, timestamp: Optional[str] = None) -> List[Dict[str, Any]]:
    out = []
    n_transitions = max(0, seg.n_frames - 1)
    for track in seg.tracks:
        transitions = sorted({e.t for e in seg.events if e.track == track.track_id})
        present = sum(1 for m in track.masks if m is not None)
        out.append(
            make_candidate(
                engine=ENGINE,
                kind="object_hypothesis",
                payload=to_payload(seg, track),
                transitions=transitions,
                coverage="%d/%d" % (present, seg.n_frames),
                timestamp=timestamp,
            )
        )
    _ = n_transitions
    return out


def run(frames: Sequence[Sequence[Sequence[int]]], background: int = 0,
        out_path: Optional[str] = None,
        timestamp: Optional[str] = None) -> Segmentation:
    """Segment `frames`; if `out_path` is given, append the proposals there."""
    seg = segment_trajectory(frames, background=background)
    if out_path:
        emit(out_path, candidates(seg, timestamp=timestamp))
    return seg
