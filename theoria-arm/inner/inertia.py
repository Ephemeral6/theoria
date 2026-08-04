"""Did the manual the arm just paid for predict anything the old one did not?

A25 answered that question **after the fact**: for every archived adjudication
it recompiled the two book revisions the call was snapshotted between and
replayed both over the transitions that arrived *later*.  23 of 58 scored calls
drew the same frame at every subsequent step -- $20.15 for a differently-worded
manual.  That is an audit.  An audit cannot change a run, because its input is
the future.

This module is the same measurement made **available at the call**.  The only
change is which transitions it replays over: not the ones that have not
happened yet, but the ones already in the store.  At the moment a theorize
returns, the arm holds

* `rev<N>-before-theorize/` and `rev<N>-after-theorize/` -- the two revisions,
  on disk, put there by `inner/theorize.run` itself;
* every frame the leg has seen.

Both revisions compile offline, both replay over the recorded prefix, and if
they draw the same frame at every step the arm has just paid for a manual that
predicts exactly what the old one predicted **about everything it has ever
seen**.  No network, no desk, no spend -- one compile and one replay per
revision, the same machinery `inner/certify.py` already runs every turn.

**This is a different question from A25's, and it is not a stand-in for it.**
The audit asks whether the edit changed a prediction about frames the arm went
on to see; this asks whether it changed a prediction about frames the arm has
already seen.  Neither implies the other in general.  What the archive says
about how far the two agree is measured, not assumed:
`armtools/action_economy.py` cross-tabulates them over every archived
adjudication and prints the table.  Read that table before believing this
signal, and read the honest half of it: an at-call verdict of `inert` is a
statement about evidence in hand and nothing more.

**Why it is worth having anyway.** A theorize is called because the world
contradicted the manual -- `replay_mismatch` is the commonest trigger by a
factor of three, and a replay mismatch is a statement about the recorded
prefix.  A call answering a mismatch on the prefix, whose reply predicts the
prefix identically, has not addressed the thing that summoned it.  That is a
claim about the call the arm can check for itself, immediately, for free.

**What is deliberately not here.** Nothing in this module decides anything.
It reports a verdict; `inner/economy.py` decides whether any policy listens.
The default listens to nothing and does not even call in here -- see
`ActionEconomyConfig.inertia`.
"""

import os
import shutil
import tempfile
from typing import Any, Dict, List, Optional, Sequence, Tuple

#: The two revisions disagree somewhere in the window: the call bought a
#: prediction the old manual did not make.
MOVED = "moved_a_prediction"

#: They agree at every step in the window.  On the at-call window this means
#: the new manual predicts exactly what the old one predicted about everything
#: the arm has seen.
INERT = "predicted_what_the_old_manual_predicted"

#: `before` did not compile and `after` does -- the leg went from having no
#: predictor to having one.  Never inert, whatever the frames say.
GAINED = "gained_a_predictor_where_there_was_none"

#: `after` does not compile and `before` did.  A regression, not a saving.
LOST = "lost_the_predictor"

#: Neither compiles.  The question is unanswerable, not answered `inert`.
BLIND = "neither_revision_compiles"

#: One or both snapshot directories are not on disk.  `Books.snapshot` copies
#: only the files that exist, so a cold start's first `before` is an empty
#: directory and git does not track those.
UNPAIRED = "no_snapshot_pair_on_disk"

#: Fewer than one transition in the window.  An unanswerable question is not a
#: negative answer.
NO_EVIDENCE = "no_transition_in_the_window"

#: Every verdict, so a caller can assert exhaustiveness rather than guess.
VERDICTS = (MOVED, INERT, GAINED, LOST, BLIND, UNPAIRED, NO_EVIDENCE)

#: The verdicts on which a policy is entitled to conclude the call bought
#: nothing.  Exactly one of them.  `BLIND` and `UNPAIRED` are ignorance and
#: `NO_EVIDENCE` is an empty window; treating any of the three as `INERT`
#: would let a missing file widen the floor.
BOUGHT_NOTHING = (INERT,)


def compile_snapshot(snap_dir: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Compile one `rev<N>-<tag>` snapshot in a scratch copy and load it.

    The copy matters twice over.  `Books.compile_all` writes `generated/`
    beside the DSL, and neither a census of a recorded run nor a live turn may
    add a byte to a snapshot directory -- the snapshots are evidence.  The
    scratch tree is removed whether or not the compile succeeded.
    """
    from .books import Books                           # noqa: PLC0415

    tmp = tempfile.mkdtemp(prefix="inertia-")
    try:
        for name in ("theory.dsl", "playbook.dsl", "problem.json"):
            src = os.path.join(snap_dir, name)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(tmp, name))
        books = Books(tmp)
        try:
            books.compile_all()
        except Exception as exc:                       # noqa: BLE001
            return None, "compile raised: %s: %s" % (type(exc).__name__, exc)
        namespace, error = books.load_predictor()
        return namespace, error
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def drawn_series(namespace: Dict[str, Any], actions: Sequence[Optional[str]],
                 limit: int) -> List[Optional[str]]:
    """What this predictor says the world looks like at each step.

    One hash per step so two revisions can be compared without holding two
    64x64 grid series in memory at once.  A step the predictor could not reach
    -- `step` raised, `render` raised -- is `None` and compares unequal to a
    frame, which is correct: a predictor that crashes has not agreed with one
    that draws.

    `actions[t]` is the action taken *at* grid `t`, which is how
    `world.frames.FrameStore` aligns it and how `inner/certify.py` reads it.
    Getting that backwards silently shifts every replay by one step and turns
    an agreeing predictor into a diverging one.
    """
    from .commit import action_to_manual               # noqa: PLC0415
    from world.frames import grid_hash                 # noqa: PLC0415

    out: List[Optional[str]] = []
    try:
        state = namespace["initial_state"]()
    except Exception:                                  # noqa: BLE001
        return [None] * limit
    for t in range(limit):
        arc_action = actions[t] if t < len(actions) else None
        if arc_action is None:
            out.append(None)
            continue
        try:
            state = namespace["step"](state, action_to_manual(arc_action))
            out.append(grid_hash(namespace["render"](state)))
        except Exception:                              # noqa: BLE001
            out.extend([None] * (limit - t))
            break
    return out


def compare_series(before: Sequence[Optional[str]],
                   after: Sequence[Optional[str]],
                   lo: int, hi: int) -> Dict[str, Any]:
    """Two already-drawn series, compared over the half-open window `[lo, hi)`.

    Split out so the at-call verdict and the after-the-fact verdict can be read
    off **one** pair of replays: the at-call window is the prefix, the audit's
    window is the tail, and computing the series twice would double the cost of
    the only expensive step for no new information.
    """
    diverged = [t for t in range(max(lo, 0), max(hi, 0))
                if before[t] != after[t]]
    return {
        "verdict": MOVED if diverged else INERT,
        "window": [max(lo, 0), max(hi, 0)],
        "steps_in_window": max(max(hi, 0) - max(lo, 0), 0),
        "first_divergent_step": diverged[0] if diverged else None,
        "divergent_steps": len(diverged),
    }


def compare_revisions(before_dir: Optional[str], after_dir: Optional[str],
                      actions: Sequence[Optional[str]],
                      windows: Dict[str, Tuple[int, int]],
                      limit: int) -> Dict[str, Dict[str, Any]]:
    """Compile both revisions once and judge them over several windows.

    Returns one verdict dict per named window.  The compile-level verdicts --
    `UNPAIRED`, `BLIND`, `GAINED`, `LOST` -- are facts about the revisions and
    are therefore the same in every window; only `MOVED`/`INERT` depends on
    which steps are looked at.
    """
    def _everywhere(payload: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        return {name: dict(payload) for name in windows}

    if not before_dir or not after_dir:
        return _everywhere({"verdict": UNPAIRED})

    empty = {name: (lo, hi) for name, (lo, hi) in windows.items()
             if max(hi, 0) - max(lo, 0) <= 0}
    if len(empty) == len(windows):
        return _everywhere({"verdict": NO_EVIDENCE,
                            "steps_in_window": 0})

    before_ns, before_err = compile_snapshot(before_dir)
    after_ns, after_err = compile_snapshot(after_dir)
    if before_ns is None and after_ns is None:
        return _everywhere({"verdict": BLIND, "before_error": before_err,
                            "after_error": after_err})
    if before_ns is None:
        return _everywhere({"verdict": GAINED, "before_error": before_err})
    if after_ns is None:
        return _everywhere({"verdict": LOST, "after_error": after_err})

    before_series = drawn_series(before_ns, actions, limit)
    after_series = drawn_series(after_ns, actions, limit)
    out: Dict[str, Dict[str, Any]] = {}
    for name, (lo, hi) in windows.items():
        if name in empty:
            out[name] = {"verdict": NO_EVIDENCE, "steps_in_window": 0}
        else:
            out[name] = compare_series(before_series, after_series, lo, hi)
    return out


def verdict_at_call(before_dir: Optional[str], after_dir: Optional[str],
                    store: Any) -> Dict[str, Any]:
    """The runtime signal: judged over every transition the arm has recorded.

    Called from `inner/loop.py` immediately after an adjudication returns, and
    only when a policy asked for it.  `store` is anything with `grids` and
    `actions` -- the level store in the loop, a ledger-backed stand-in in the
    offline census.

    The window is `[0, len(grids) - 1)`: one transition per pair of adjacent
    frames, which is what `drawn_series` can draw.
    """
    grids = list(getattr(store, "grids", []) or [])
    actions = list(getattr(store, "actions", []) or [])
    limit = max(len(grids) - 1, 0)
    out = compare_revisions(before_dir, after_dir, actions,
                            {"at_call": (0, limit)}, limit)["at_call"]
    out["evidence_frames"] = len(grids)
    return out


def bought_nothing(verdict: Optional[str]) -> Optional[bool]:
    """`True`, `False`, or `None` for "the record cannot say".

    The three-valued return is the point.  `note_adjudication` widens an
    adaptive floor on `True` and resets it on `False`; an unknown must do
    neither, or a snapshot that failed to copy becomes an argument for
    thinking less.
    """
    if verdict is None:
        return None
    if verdict in (UNPAIRED, BLIND, NO_EVIDENCE):
        return None
    return verdict in BOUGHT_NOTHING
