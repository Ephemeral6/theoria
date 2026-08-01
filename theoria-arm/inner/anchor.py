"""anchor -- which state the frontier is a successor of, and how far it has drifted.

`inner/loop._roll_forward` answers one question -- *where would the manual be
if it were right?* -- and the arm uses that answer for two jobs whose
requirements contradict each other.

**Job A, audit.** `certify.cheap` replays the manual open-loop from
`initial_state()` over the whole recorded action sequence and compares every
rendered frame against the frame the world returned. That comparison is this
arm's only detector of a *wrong rule* (`Theoria.md` 1.3: replay is what catches
写错的规则). It is a global test and it is only a test **because** it is
open-loop: a replay that is re-seated on the world's frame each turn cannot
diverge by more than one step, so it goes green on a manual that is wrong
everywhere. Job A therefore requires a state that is allowed to drift.

**Job B, experiment design.** `inner/probe.build_hypotheses` builds a frontier
of successors of a state, and `design` prices actions by how far those
successors disagree. Every one of them is a claim about *the next frame*, so
the state they succeed had better be the frame the world is showing. Job B
therefore requires a state that is never allowed to drift.

Today one variable serves both and Job A silently wins.
`runs/20260801T0900Z-R2-frontier-by-generation/` measured the bill: on the four
legs of 2026-07-31, **35 of 52 completed probes were designed from a state the
world had already left, and all 35 landed off the frontier.** One mispredicted
transition desynchronises the manual's state permanently, and every probe after
it is an experiment about a frame that no longer exists.

**The obvious repair destroys the instrument.** Re-seating the manual's state
on the world's observed frame each turn fixes Job B and makes Job A's replay
trivially green, which is why it is not what this module does.

What this module does instead is give Job B its own anchor and leave Job A's
alone, and it does it *without inverting `render`*. `render` is not injective
-- the generated `State` is one `<name>_pos`/`<name>_color` pair per instance
and many assignments paint the same grid -- so "the state the world is in" is
not a well-posed thing to compute, and a re-seat that guessed an assignment
would be a fabrication seated in the manual's own state. The anchor Job B
actually needs is not a state at all: it is **the frame the successors are
successors of**, and the world's own last observed frame is that frame exactly,
with nothing inferred.

So `mode="observed"` keeps every hypothesis's *mechanism* (it is still computed
by running the manual's `step` from the rolled-forward state) and moves only
its *anchor*: the cells the hypothesis changes, relative to the manual's own
current frame, are applied to the world's current frame instead.

    prediction  =  hash( world_frame  ⊕  ( render(h(state, a)) − render(state) ) )

Two consequences worth stating because they are provable rather than measured:

* the `inert` hypothesis anchored this way predicts the world's frame
  unchanged, which is exactly R2's `world_inert`; and the `manual` hypothesis
  anchored this way is exactly R2's `world_anchored_manual`. **The anchor
  switch subsumes two of `--frontier generated`'s four generators**, and does
  it at the width the ablation frontier already had, instead of adding two more
  hypotheses that widen the frontier and lower every action's split entropy.
  The two that are *not* subsumed are the `*_edge` pair, which are about
  expressivity (a board cell no rule can name) and not about anchoring.
* when the manual has not drifted, `render(state)` **is** the world's frame, so
  the transplant is the identity and every prediction is byte-identical to the
  rolled anchor's. The switch is a no-op on a correct manual. That is the
  negative control, and `tests/test_anchor.py` runs it as one: a check that has
  never been seen to say "no change" has not been shown to be measuring drift.

The divergence between the two anchors is the other half of the deliverable.
It is free -- two renders and a cell diff, no action, no model call -- and
nothing in this arm has ever reported it. It is the **magnitude** of what
`certify`'s replay reports the *location* of: `first_divergence` says where the
manual first went wrong, `divergence()` says how wrong it still is, now.

**Why drift is not an eighth surprise.** `Theoria.md` 1.9 closes the taxonomy
at seven (empirical five, computational two) and `inner/surprise.py` raises on
an eighth by construction. Adding one would be a change to 1.10(d), not a
convenience. It would also be wrong on the merits: drift is not a new *kind* of
evidence, it is the accumulated consequence of a `replay_mismatch` that has
already fired and already called the desk. Firing a second surprise for the
same defect would double-count against constraint 8's arithmetic -- calls are
triggered by surprises, and `Register.audit` checks that the two numbers line
up -- and would pay a model call to be told a second time what the replay
already said. Its correct home is a measurement attached to the surprise that
does exist, which is where it is.
"""

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import _bootstrap                                     # noqa: F401  (sys.path)

from world.frames import diff_cells, grid_hash

#: The value of `mode` that turns the change on. A positive whitelist, for the
#: same reason `FrontierConfig.from_env` and `ProbeEconomyConfig.from_env` are
#: whitelists: a misspelt switch must not silently change the anchor a round is
#: trying to measure.
OBSERVED = "observed"
ROLLED = "rolled"


@dataclass
class AnchorConfig:
    """Which frame the probe frontier's hypotheses are successors of.

    `rolled` is the default and is 2026-07-31 byte for byte: the anchor is
    `loop._roll_forward`'s state, drift and all. `observed` transplants each
    hypothesis's delta onto the world's own last observed frame.

    **This switch never touches `certify`.** `certify.cheap` keeps its own
    `state = initial_state()` and its own replay loop; it does not call
    `_roll_forward` and it does not read this config. The audit instrument is
    left exactly as it was, which is the whole point of the design.
    """

    mode: str = ROLLED

    #: Report the divergence between the two anchors in `design`'s report.
    #: Independent of `mode` on purpose: a leg can *measure* its drift while
    #: still designing from the rolled anchor, which is the honest A/B (the
    #: measurement must not be confounded with the change it argues for).
    #: Default off, because writing the block changes `design`'s report and
    #: `--anchor rolled` is required to stay byte-identical -- see
    #: `GAPS.md` R2-1, which is the same trade made for the same reason.
    measure: bool = False

    @property
    def observed(self) -> bool:
        return self.mode == OBSERVED

    @classmethod
    def from_env(cls, env: Optional[Dict[str, str]] = None) -> "AnchorConfig":
        """`THEORIA_ANCHOR=observed` turns it on; anything else is off.

        `1`, `true`, `OBSERVED`, `observed!` and the empty string all leave it
        on `rolled`. `THEORIA_ANCHOR_MEASURE=1` turns the report block on
        independently.
        """
        env = os.environ if env is None else env
        raw = str(env.get("THEORIA_ANCHOR", "")).strip()
        measure = str(env.get("THEORIA_ANCHOR_MEASURE", "")).strip() == "1"
        return cls(mode=OBSERVED if raw == OBSERVED else ROLLED,
                   measure=measure or raw == OBSERVED)


def world_frame(store: Any) -> Optional[Any]:
    """The world's most recent observed frame, or None.

    None is an answer, not a zero: on the opening turn of a level there is a
    frame but before any observation there is not, and a caller that cannot
    anchor must say it could not rather than anchor on something else.
    """
    if store is None:
        return None
    try:
        return store.current
    except Exception:                                  # noqa: BLE001
        return None


def divergence(namespace: Dict[str, Any], state: Any, store: Any
               ) -> Dict[str, Any]:
    """How far the manual's rolled-forward state is from the world's frame.

    Free: two renders and a cell diff. No action, no model call, no network.

    `cells_wrong` is the number this arm has never reported and which is
    evidence about the manual's quality per turn: 0 is a manual that has
    tracked the world exactly so far, and a number that climbs is a manual
    whose rules are wrong in a way `certify`'s first-divergence line names once
    and then stops quantifying.

    Every field can be `None`, and `None` means *not measurable here* -- no
    frame observed yet, no `render` in the namespace, or a `render` that
    raised. It is never rendered as 0.
    """
    render = namespace.get("render") if namespace else None
    world = world_frame(store)
    out: Dict[str, Any] = {
        "anchor_hash": None, "world_hash": None, "drifted": None,
        "cells_wrong": None, "cells_total": None, "fraction_wrong": None,
        "unmeasurable": None,
    }
    if world is None:
        out["unmeasurable"] = "no frame observed yet"
        return out
    out["world_hash"] = grid_hash(world)
    out["cells_total"] = sum(len(row) for row in world)
    if render is None:
        out["unmeasurable"] = "the namespace exposes no render"
        return out
    try:
        drawn = render(state)
    except Exception as exc:                           # noqa: BLE001
        out["anchor_hash"] = "error"
        out["unmeasurable"] = ("the manual's own render raised: %s: %s"
                               % (type(exc).__name__, exc))
        return out
    out["anchor_hash"] = grid_hash(drawn)
    wrong = diff_cells(drawn, world)
    out["cells_wrong"] = len(wrong)
    out["drifted"] = out["anchor_hash"] != out["world_hash"]
    if out["cells_total"]:
        out["fraction_wrong"] = len(wrong) / float(out["cells_total"])
    out["first_cells"] = [{"cell": [r, c], "manual_says": a, "world_says": b}
                          for r, c, a, b in wrong[:24]]
    return out


def _delta(before: Any, after: Any) -> Dict[Any, int]:
    """`{(row, col): new_value}` for every cell two grids disagree on."""
    out: Dict[Any, int] = {}
    if before is None or after is None:
        return out
    for r in range(max(len(before), len(after))):
        rb = before[r] if r < len(before) else []
        ra = after[r] if r < len(after) else []
        for c in range(max(len(rb), len(ra))):
            vb = rb[c] if c < len(rb) else None
            va = ra[c] if c < len(ra) else None
            if vb != va and va is not None:
                out[(r, c)] = va
    return out


def _applied(grid: Any, delta: Dict[Any, int]) -> Any:
    """A copy of `grid` with `delta` written into it. Out-of-range is dropped."""
    out = [list(row) for row in grid]
    for (r, c), value in delta.items():
        if 0 <= r < len(out) and 0 <= c < len(out[r]):
            out[r][c] = value
    return out


def reanchor_specs(specs: List[Any], namespace: Dict[str, Any], store: Any,
                   *, config: Optional[AnchorConfig] = None) -> List[Any]:
    """The ablation family, re-anchored on the world's frame.

    `specs` is `probe.ablation_grid_specs`'s output --
    `(id, description, grid_of, swallow)` -- and the grid form is what makes
    this possible: moving an anchor means applying the cells a hypothesis
    changes to a different frame, and a hash cannot be re-anchored. Ids, order,
    count and descriptions are preserved exactly, so this is the *same*
    frontier asked about the frame the world is actually showing, and the
    ablations keep the one thing the generated family cannot say -- **which
    clause** is wrong.

    Returns the unanchored hypotheses when there is no world frame to anchor
    on. That is the honest fallback: before the first observation there is
    nothing to anchor to, and seating the frontier on a fabricated frame would
    be worse than leaving it where it was. `design`'s `anchor` block reports
    which of the two happened, so a leg never has to guess.
    """
    from engines.probe_frontier import Hypothesis      # noqa: PLC0415
    from inner.probe import _hashing                   # noqa: PLC0415

    cfg = config or AnchorConfig(mode=OBSERVED)
    world = world_frame(store) if cfg.observed else None
    render = (namespace or {}).get("render")
    if world is None or render is None:
        return [Hypothesis(id=hid, predict=_hashing(grid_of, swallow),
                           description=description)
                for hid, description, grid_of, swallow in specs]

    return [Hypothesis(id=hid,
                       predict=_anchored(grid_of, swallow, render, world),
                       description=description)
            for hid, description, grid_of, swallow in specs]


def _anchored(grid_of: Any, swallow: bool, render: Any, world: Any):
    """One hypothesis, re-expressed as a claim about the world's next frame.

    The mechanism is untouched -- `grid_of` still runs the manual's own `step`
    from the rolled-forward state -- and only the frame its answer is read
    against changes:

        hash( world  ⊕  ( grid_of(state, action)  −  render(state) ) )

    `swallow` carries the historic error behaviour through unchanged, so an
    anchored `inert` still lets a raising `render` propagate and an anchored
    `manual` still answers `"error"`. A broken predictor is a broken predictor
    whatever it is anchored on; turning one into a grid would be inventing a
    prediction.
    """
    def compute(state, action):
        base = render(state)
        after = grid_of(state, action)
        return grid_hash(_applied(world, _delta(base, after))) or "none"

    if not swallow:
        return compute

    def predict(state, action):
        try:
            return compute(state, action)
        except Exception:                              # noqa: BLE001
            return "error"
    return predict
