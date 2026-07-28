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

#: `# arc-cell: (r, c)` on a landmark declaration.
#:
#: Excluding `problem.json` is not enough on its own, and the first live E3 run
#: proved it: seven of g50t's landmark coordinates -- `start_cell (10,16)`,
#: `gate_cell (40,16)`, `goal_cell (52,46)` and four more -- arrived in sk48's
#: computed `problem.json` verbatim, because `theorize._landmarks_from_theory`
#: reads them out of comments in the manual and `problem_from_frames` writes
#: them into the level. The manual is the domain and the coordinates are level
#: data (`inner/books.py`'s own domain/problem split says so), so a route that
#: carries them across games defeats the exclusion it sits next to.
#:
#: They are stripped on carry, not on write, so the *source* run's books are
#: untouched and the stripping is visible as a diff in `rev01-carried`. A
#: landmark whose hint is gone still declares itself; `problem_from_frames`
#: places it at the origin and lists it under `landmarks_defaulted`, which is
#: the existing, visible failure mode for a coordinate the level cannot supply.
#: The hint itself, matched exactly as `theorize.CELL_HINT` reads it back.
#:
#: The first version of this required a leading `#` and rejected a minus sign,
#: while the detector that reports `landmarks_stripped` required neither. Every
#: disagreement between the two was a coordinate that **leaked and was
#: simultaneously attested as removed** -- `landmark a  arc-cell: (7, 8)` came
#: through untouched with `a` named in `landmarks_stripped`, and the reader
#: still pulled `(7, 8)` out of it. A provenance record that lies in the safe
#: direction would be bad enough; this one lied in the dangerous direction.
#:
#: So there is now one pattern, it is a superset of what the reader accepts,
#: and `strip_level_data` asserts the post-condition rather than trusting it.
CELL_HINT_ANY = re.compile(r"#?\s*arc-cell\s*[:=]\s*\(?\s*-?\d+\s*,\s*-?\d+\s*\)?")
LANDMARK_LINE = re.compile(r"^\s*landmark\s+(\w+)")
STRIPPED_MARK = "  # arc-cell: carried, coordinates stripped"

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
class LevelDataSurvived(RuntimeError):
    """A coordinate outlived the strip. Raised rather than returned, because
    the caller's next act is to write the manual into a new game's run and the
    whole point of the strip is that this cannot happen quietly."""


def strip_level_data(theory: str) -> Tuple[str, List[str]]:
    """Remove every landmark cell hint, and say which landmarks lost one.

    Line-oriented rather than one global substitution: `re.sub` on the whole
    text consumed only the first hint per landmark line, so
    `# arc-cell: (1,2) arc-cell = (3,4)` left the second one readable and the
    reader duly returned `(3, 4)`.

    The post-condition is checked, not assumed. `_landmarks_from_theory` is the
    only consumer that matters, so the test is simply that it can no longer read
    a coordinate out of the result.
    """
    removed: List[str] = []
    lines = []
    for line in (theory or "").splitlines():
        match = LANDMARK_LINE.match(line)
        if match and CELL_HINT_ANY.search(line):
            removed.append(match.group(1))
            line = CELL_HINT_ANY.sub("", line).rstrip() + STRIPPED_MARK
        lines.append(line)
    out = "\n".join(lines)
    if (theory or "").endswith("\n"):
        out += "\n"

    from .theorize import _landmarks_from_theory          # noqa: PLC0415
    survived = {name: cell for name, cell
                in _landmarks_from_theory(out).items() if cell is not None}
    if survived:
        raise LevelDataSurvived(
            "these landmark coordinates outlived the strip and would have "
            "entered the next game's level: %s. The manual is not carried."
            % survived)
    return out, removed


def carry(books, source_books_dir: str, *,
          source_game_id: Optional[str] = None,
          strip_landmarks: bool = True) -> Dict[str, Any]:
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

    landmarks_stripped: List[str] = []
    if strip_landmarks:
        stripped, landmarks_stripped = strip_level_data(books.theory)
        if landmarks_stripped:
            books.write(theory=stripped)
            carried["theory.dsl"] = {
                "sha256": _sha256(books.theory_path),
                "bytes": os.path.getsize(books.theory_path),
                "lines": sum(1 for _ in open(books.theory_path,
                                             encoding="utf-8")),
                "sha256_before_stripping": carried["theory.dsl"]["sha256"],
            }

    theory_text = books.theory
    provenance = {
        "landmarks_stripped": landmarks_stripped,
        "landmarks_stripped_why": (
            "a landmark's `# arc-cell: (r, c)` is level data, not domain: the "
            "manual names the landmark and the level places it. Carrying the "
            "coordinates would move one game's geometry into another game's "
            "computed level, which is the same defect excluding problem.json "
            "exists to prevent -- and it happened on the first live carry "
            "before this was added."),
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


def action_overlap(namespace: Optional[Dict[str, Any]],
                   legal_actions: List[int],
                   predictor_error: Optional[str] = None) -> Dict[str, Any]:
    """Do the carried manual's actions and the new game's overlap at all?

    Free to compute, and it decides whether a transfer experiment is possible
    before a single action is spent. The first live carry did not have it and
    paid the price in interpretation rather than money: g50t's manual declares
    exactly one action, `('key', 5)`, and every one of its rules opens by
    refusing anything else; sk48 offers `[1, 2, 3, 4, 6, 7]` and has no ACTION5.
    So every rule was unreachable, `step` was the identity for every action the
    arm could send, and the run's replay result was trivial rather than
    structural -- but nothing in the artefacts said so, and the first reading of
    that run treated the replay failure as evidence about the manual.

    A manual whose action vocabulary does not intersect the new game's cannot be
    tested on it. That is not a reason to refuse the run -- there is still a
    world to observe and a new manual to write -- but it is a reason to stop
    calling the run a test of the carried theory, and the report says so in
    those words.
    """
    # A predictor that would not load tells us nothing about what the manual
    # declares, and saying "it declares no actions" would be a false factual
    # claim about the theory published on the report's headline line -- the
    # same class of misreading this function exists to prevent. Three reasons,
    # three distinct verdicts.
    if namespace is None:
        return {
            "manual_declares": None,
            "manual_action_ids": None,
            "game_offers": sorted(legal_actions or []),
            "shared": None,
            "testable": False,
            "reason": "predictor_did_not_load",
            "predictor_error": predictor_error,
            "detail": (
                "the carried manual's executable form did not load (%s), so no "
                "overlap could be computed. This says nothing about what the "
                "manual declares."
                % (predictor_error or "no error was reported")),
        }

    declared = list((namespace or {}).get("ACTIONS") or [])
    # The manual's actions are `(kind, id)` pairs -- but `gen_python`'s
    # alphabet is `(name,) + args`, so arity is whatever the rule's guards
    # declare and a click-family manual is a 3-tuple. Anything that is not a
    # `(kind, int)` pair is counted as unreadable rather than silently dropped:
    # dropping it produced "declares no actions at all", which is false.
    declared_ids = sorted({int(a[1]) for a in declared
                           if isinstance(a, (list, tuple)) and len(a) == 2
                           and str(a[1]).lstrip("-").isdecimal()})
    unreadable = [list(a) if isinstance(a, tuple) else a for a in declared
                  if not (isinstance(a, (list, tuple)) and len(a) == 2
                          and str(a[1]).lstrip("-").isdecimal())]
    shared = sorted(set(declared_ids) & set(legal_actions or []))
    out = {
        "manual_declares": [list(a) if isinstance(a, tuple) else a
                            for a in declared],
        "manual_action_ids": declared_ids,
        "actions_not_readable_as_a_key_id": unreadable,
        "game_offers": sorted(legal_actions or []),
        "shared": shared,
        "testable": bool(shared),
        "reason": None,
    }
    if not declared and not unreadable:
        out["reason"] = "manual_declares_no_actions"
        out["detail"] = (
            "the carried manual declares no actions at all, so it makes no "
            "action-conditioned prediction and nothing this game does can "
            "confirm or refute its rules.")
    elif not declared_ids:
        out["reason"] = "no_action_readable_as_a_key_id"
        out["detail"] = (
            "the carried manual declares %d action(s), none of which is a "
            "(kind, key-id) pair this comparison can read: %s. The overlap is "
            "unknown, not empty."
            % (len(unreadable), unreadable))
    elif not shared:
        out["reason"] = "no_overlap"
        out["detail"] = (
            "the carried manual's rules fire only on %s and this game offers "
            "only %s. Every rule is unreachable, `step` is the identity for "
            "every action this arm can send, and a replay failure here is "
            "evidence about that mismatch and NOT about the manual's content. "
            "This run cannot test the carried theory."
            % (declared_ids, sorted(legal_actions or [])))
    else:
        out["detail"] = (
            "%d of the manual's %d declared actions are offered by this game, "
            "so its rules can fire and a replay result is evidence about them."
            % (len(shared), len(declared_ids)))
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
                actions_spent: int,
                actions: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Everything the carried manual did on the new game before a model was called."""
    checks = ((certify_report or {}).get("cheap") or {}).get("checks") or {}
    replay = checks.get("replay") or {}
    return {
        "stage": "cold",
        "model_calls_so_far": 0,
        "actions_spent_so_far": actions_spent,
        "provenance": provenance,
        "actions": actions,
        # The one line a reader needs before reading any other number here.
        "carried_theory_is_testable_on_this_game": bool(
            (actions or {}).get("testable")),
        "replay_means": (
            "the manual's rules can fire on this game, so a replay result is "
            "evidence about them"
            if (actions or {}).get("testable") else
            "NOT evidence about the manual's rules: %s"
            % (actions or {}).get("detail", "no action overlap was computed")),
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
