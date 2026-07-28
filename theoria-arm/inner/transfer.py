"""Carrying the two books between games, and measuring what survives.

`Theoria.md` C3 asks whether an explicit written theory transfers. `books.py`
already fixes what that means mechanically -- "the same `theory.dsl` against a
different computed problem" -- because the domain/problem split is drawn by
arithmetic here: the manual is the domain, the level's layout is computed from
the frames and is never written by the desk. So carrying a theory between games
is exactly: copy the two hand-written files, recompute the problem instance from
the new game's frames, recompile, and see what happens.

Three things are measured, and they are measured at three different prices.

**Cold certify, at zero model cost.** Before the desk is called even once on the
new game, the carried manual is compiled against the new level and driven
through the whole opening sweep. Whatever it says is the transfer datum in its
purest form: no repair, no adaptation, no model call. A manual written for one
game, executed on another.

**Its own pre-registered number.** This is the part that makes the cold certify
a test rather than an observation. The g50t manual does not merely assert things
about g50t; one of its theorems states a *formula* -- `unexplained(frame 0) =
D0 - K`, where D0 counts the dynamic non-background cells of frame 0 and K the
distinct declared colours present there -- and claims it is arithmetic that can
be run in advance. That claim is not about g50t. It is about how this framework's
renderer and responsibility checker interact, and it is therefore the one part of
the carried manual that a *different* game can genuinely confirm or refute. So
the prediction is computed and written to disk before certify runs, and the
comparison is recorded either way. A manual that predicts its own failure number
on a world it has never seen has transferred something real; one that misses has
told us the formula was g50t-shaped after all.

**Name-level retention, at the end.** Which declared names of the carried manual
are still in the final manual once the desk has seen the new world. Names are a
mechanical proxy for content and are treated as one: the report counts them and
does not editorialise about whether a surviving name means a surviving idea.

Nothing here calls a model. Nothing here writes to another track.
"""

import hashlib
import json
import os
import re
import shutil
from typing import Any, Dict, List, Optional, Tuple

#: The two hand-written books, and *only* those two. `problem.json` is the level
#: instance -- computed from the frames of the game being played -- so carrying
#: it would carry g50t's board into sk48 and quietly make the transfer claim
#: unfalsifiable. It is named here so the exclusion is visible rather than
#: implied by the absence of a line.
CARRIED = ("theory.dsl", "playbook.dsl")
NEVER_CARRIED = ("problem.json",)

#: Declared names, by kind, as the grammar card writes them.
DECL = {
    "object": re.compile(r"^\s*object\s+(\w+)", re.M),
    "landmark": re.compile(r"^\s*landmark\s+(\w+)", re.M),
    "event": re.compile(r"^\s*event\s+(\w+)", re.M),
    "rule": re.compile(r"^\s*rule\s+(\w+)", re.M),
    "invariant": re.compile(r"^\s*invariant\s+(\w+)", re.M),
    "theorem": re.compile(r"^\s*theorem\s+(\w+)", re.M),
}


def _sha256(path: str) -> Optional[str]:
    if not os.path.exists(path):
        return None
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def declared_names(text: str) -> Dict[str, List[str]]:
    """Every name the manual declares, by kind."""
    return {kind: sorted(set(pattern.findall(text or "")))
            for kind, pattern in DECL.items()}


# ------------------------------------------------------------------- carrying
def carry(books, source_books_dir: str, *,
          source_game_id: Optional[str] = None) -> Dict[str, Any]:
    """Seed a fresh run's books from a finished run's, and say exactly what moved.

    Raises if the source has no `theory.dsl`: a carry that silently degrades to
    a cold start would make the whole run uninterpretable, since a cold start
    and a failed carry produce the same empty book.
    """
    source_theory = os.path.join(source_books_dir, "theory.dsl")
    if not os.path.exists(source_theory):
        raise FileNotFoundError(
            "no theory.dsl under %s -- refusing to start a 'carried' run with "
            "an empty manual, because that is indistinguishable from a cold "
            "start in every artefact this run writes" % source_books_dir)

    carried: Dict[str, Any] = {}
    for name in CARRIED:
        src = os.path.join(source_books_dir, name)
        if not os.path.exists(src):
            carried[name] = None
            continue
        dst = os.path.join(books.root, name)
        shutil.copy2(src, dst)
        carried[name] = {"sha256": _sha256(dst),
                         "bytes": os.path.getsize(dst),
                         "lines": sum(1 for _ in open(dst, encoding="utf-8"))}

    theory_text = books.theory
    provenance = {
        "source_books_dir": os.path.abspath(source_books_dir),
        "source_run": os.path.basename(
            os.path.dirname(os.path.abspath(source_books_dir))),
        "source_game_id": source_game_id,
        "carried": carried,
        "not_carried": {
            name: ("the level instance is computed from the frames of the game "
                   "being played; carrying it would import the previous game's "
                   "board and make the transfer claim unfalsifiable")
            for name in NEVER_CARRIED},
        "declared_names": declared_names(theory_text),
    }
    provenance["declared_name_count"] = sum(
        len(v) for v in provenance["declared_names"].values())
    books.snapshot("carried")
    return provenance


# ------------------------------------------------ the manual's own prediction
RENDER_FORMULA = "unexplained(frame_0) = D0 - K"


def predict_unexplained(store, objects: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Run the carried manual's own render-accounting formula on the new game.

    D0 -- dynamic cells that are non-background in frame 0.
    K  -- distinct declared colours that actually occur in frame 0. The manual's
          reasoning is that an object is anchored at the raster-first cell of its
          colour, so two objects sharing a colour collide on one cell and a
          colour absent from the frame anchors nothing; therefore the number of
          cells the manual can draw is the number of distinct *present* colours
          it declared, not the number of objects.

    The formula is stated for one-instance declarations. `arc-instances: all`
    spreads a declaration over every dynamic cell of its colour and breaks the
    "one colour, one pixel" step outright, so when one is present the prediction
    is withheld rather than reported wrong -- a formula applied outside its
    stated domain is not a test of it.
    """
    grids = store.grids
    if not grids:
        return {"available": False, "detail": "no frame observed yet"}
    grid = grids[0]
    background = store.background()
    dynamic = set(store.dynamic_cells())

    d0 = sum(1 for (r, c) in dynamic if grid[r][c] != background)
    present_colours = {value for row in grid for value in row}

    spread = [o["name"] for o in objects if o.get("instances") == "all"]
    declared_colours = {o.get("color") for o in objects
                        if o.get("color") is not None}
    k = len(declared_colours & present_colours)

    out = {
        "available": not spread,
        "formula": RENDER_FORMULA,
        "D0": d0,
        "K": k,
        "declared_colours": sorted(c for c in declared_colours),
        "declared_colours_present_in_frame_0": sorted(declared_colours
                                                      & present_colours),
        "background": background,
        "dynamic_cells": len(dynamic),
        "predicted_unexplained": d0 - k,
        "objects_declared": len(objects),
    }
    if spread:
        out["withheld_because"] = (
            "the carried manual uses `arc-instances: all` on %s, which spreads "
            "one declaration over every dynamic cell of its colour. The formula "
            "assumes one declaration draws one pixel, so it does not apply here "
            "and reporting a number would be a test of nothing."
            % ", ".join(spread))
        out["predicted_unexplained"] = None
    return out


def score_prediction(prediction: Dict[str, Any],
                     certify_report: Dict[str, Any]) -> Dict[str, Any]:
    """Did the carried formula hold on a game it was not written for?"""
    checks = ((certify_report or {}).get("cheap") or {}).get("checks") or {}
    responsibility = checks.get("responsibility") or {}
    observed = responsibility.get("cells_unexplained")
    predicted = prediction.get("predicted_unexplained")

    out = {"predicted": predicted, "observed": observed,
           "formula": RENDER_FORMULA}
    if not prediction.get("available"):
        out["verdict"] = "withheld"
        out["detail"] = prediction.get("withheld_because", "no prediction made")
        return out
    if observed is None:
        out["verdict"] = "unscorable"
        out["detail"] = (
            "certify reported no cell count: %s"
            % (responsibility.get("raised") or responsibility.get("detail")
               or "responsibility did not run"))
        return out
    out["error"] = observed - predicted
    out["verdict"] = "held" if observed == predicted else "refuted"
    out["detail"] = (
        "the carried manual predicted its own responsibility number on a game "
        "it was not written for and was %s"
        % ("exactly right" if observed == predicted
           else "wrong by %+d (predicted %d, observed %d)"
                % (observed - predicted, predicted, observed)))
    return out


# ------------------------------------------------------------- what survived
def retention(carried_theory: str, final_theory: str) -> Dict[str, Any]:
    """Which declared names of the carried manual are still there at the end.

    A mechanical proxy, and reported as one. A surviving name whose body was
    rewritten counts as surviving here; the snapshots under `books/snapshots/`
    are where the bodies are compared, and they are all kept for that reason.
    """
    before = declared_names(carried_theory)
    after = declared_names(final_theory)
    per_kind: Dict[str, Any] = {}
    kept_total = dropped_total = added_total = 0
    for kind in DECL:
        kept = sorted(set(before[kind]) & set(after[kind]))
        dropped = sorted(set(before[kind]) - set(after[kind]))
        added = sorted(set(after[kind]) - set(before[kind]))
        kept_total += len(kept)
        dropped_total += len(dropped)
        added_total += len(added)
        per_kind[kind] = {"carried": len(before[kind]), "kept": kept,
                          "dropped": dropped, "added": added}
    carried_total = kept_total + dropped_total
    return {
        "by_kind": per_kind,
        "names_carried": carried_total,
        "names_kept": kept_total,
        "names_dropped": dropped_total,
        "names_added_on_the_new_game": added_total,
        "retention_rate": (round(kept_total / carried_total, 4)
                           if carried_total else None),
        "scope": ("names only. A kept name may have a completely rewritten "
                  "body; the snapshot diffs are the record of that."),
    }


# ---------------------------------------------------------------- the report
def cold_report(*, provenance: Dict[str, Any], prediction: Dict[str, Any],
                compiled: Dict[str, Any], certify_report: Dict[str, Any],
                store_summary: Dict[str, Any],
                actions_spent: int) -> Dict[str, Any]:
    """Everything the carried manual did on the new game before a model was called."""
    checks = ((certify_report or {}).get("cheap") or {}).get("checks") or {}
    return {
        "stage": "cold",
        "model_calls_so_far": 0,
        "actions_spent_so_far": actions_spent,
        "provenance": provenance,
        "compiled": {
            "parsed": bool(compiled.get("parsed")),
            "ok": bool(compiled.get("ok")),
            "forms": sorted(k for k, v in (compiled.get("forms") or {}).items()
                            if v),
            "errors": compiled.get("errors"),
            "lean_state_estimate": compiled.get("lean_state_estimate"),
        },
        "prediction": prediction,
        "prediction_scored": score_prediction(prediction, certify_report),
        "certify": {
            "cheap_green": bool((certify_report or {}).get("cheap_green")),
            "proof_layer_available": bool(
                (certify_report or {}).get("proof_layer_available")),
            "responsibility": {
                k: v for k, v in (checks.get("responsibility") or {}).items()
                if k != "first_cells"},
            "replay": {k: v for k, v in (checks.get("replay") or {}).items()
                       if k != "first_divergence"},
            "replay_first_divergence": (checks.get("replay")
                                        or {}).get("first_divergence"),
            "unambiguous": {k: v for k, v
                            in (checks.get("unambiguous") or {}).items()
                            if k != "clashes"},
        },
        "world": store_summary,
    }
