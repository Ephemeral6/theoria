"""The action economy: how often the arm stops playing and pays to think.

`MIN_NEW_FRAMES_BETWEEN_THEORIZE = 4` has been in `inner/loop.py` since
2026-07-28. It was chosen against a real defect -- the first live run took a
$1.3 nine-minute adjudication per single probe action -- and it has never been
measured since. `armtools/action_economy.py` measured it, over the fifteen legs
in this repo that ever reached a desk, and the constant is not what the record
says the arm does:

* **3.10 billed actions per adjudication, 2.17 per paid call.** Not 4. Two
  separate reasons, and both are constants nobody chose.
* **24 of 73 adjudications had a gap of ZERO billed actions.**
  `MAX_THEORIZE_PER_TURN = 2` lets one turn adjudicate twice, and the second
  round sees not one new frame. Those 24 calls cost $42.40 -- 28% of the
  $148.89 the desk has ever been paid by this arm.
* **31 of 104 paid calls are compile repairs.** `theorize.REPAIR_ROUNDS = 2`
  gives the desk up to two extra invocations to fix a manual that will not
  compile. They are charged in full ($32.53, 22% of desk spend) and they see no
  new evidence either -- by construction, they are the same brief again.
* **23 of 58 scored adjudications changed no later prediction.** Both
  revisions of the manual were recompiled offline and replayed over the
  transitions that arrived after the call; in 23 cases the two predictors drew
  the same frame at every subsequent step. Fifteen of those 23 had rewritten
  the manual's text -- a genuine edit that moved nothing the arm predicts.
  Those 23 calls cost $20.15.
* **The zero-gap calls are where the waste concentrates.** 15 of 22 scored
  zero-gap adjudications were inert (68%), against 8 of 33 (24%) for calls that
  had at least one new action behind them. Thinking twice about the same frames
  is nearly three times as likely to buy nothing as thinking once about new
  ones.

**And the cost of a call does not grow with the wait.** `corr(step_idx,
cost_usd) = -0.039` over 65 priced calls; mean cost is $1.77 at gap 0, $2.31 at
gap 4, $2.07 at gap 5. This is the fact that makes a slower cadence worth
anything at all: doubling the floor does not double the price of the call at
the end of it, so the same money buys twice the actions. Nine of the fifteen
legs ended on `spend_gate_tripped` -- money is the binding constraint, so the
cadence *is* the action count.

That is the argument for a knob. It is not an argument for a different default:

    ActionEconomyConfig()            # today, byte for byte

`enabled=False` is the historic path, including the exact wording of the skip
line that goes into `turns.json` -- `test_action_economy.py` pins that string,
because a changed artefact is a changed run whether or not the behaviour moved.
Every lever below is off until a round turns it on, and each is set where the
measurement leaves it rather than where it would look busy.

**What is deliberately not a knob.** `REPAIR_ROUNDS` stays in
`inner/theorize.py`. It is not a cadence lever -- it does not decide *when* the
desk is called, it decides how many invocations one call is allowed. Measuring
it here and moving it there would be two changes wearing one switch. The
measurement is reported (`armtools.action_economy constants` lists it with its
share of the bill) so the next ticket can act on it with evidence.
"""

import os
from dataclasses import dataclass, replace
from typing import Any, Dict, Optional, Tuple

#: The historic floor: how much new world must arrive before the desk is worth
#: calling again. `inner/loop.MIN_NEW_FRAMES_BETWEEN_THEORIZE` is kept as the
#: name the rest of the arm imports; this is the same number, owned here.
DEFAULT_MIN_NEW = 4

#: The historic per-turn ceiling on adjudication rounds.
DEFAULT_MAX_ROUNDS_PER_TURN = 2

#: Counting units for the floor.
#:
#: `frames` is historic: `len(store.steps) - levels.start`, which counts every
#: successful command on this level including the RESET that opened it.
#: `actions` counts what the bill counts -- `budget.actions_ok`, which excludes
#: RESET (`harness/budget.py` does not bill it). The two differ by exactly the
#: resets, which is one per level, so on a single-level leg `actions` is a floor
#: of the same size arriving one command later. It is offered because the
#: quantity a round wants to buy is actions, and a gate that counts something
#: else is a gate that drifts from its own justification.
UNIT_FRAMES = "frames"
UNIT_ACTIONS = "actions"
UNITS = (UNIT_FRAMES, UNIT_ACTIONS)

#: How the floor responds to what the last adjudication bought.
#:
#: `off` is historic: the floor is a constant. `by_manual_delta` widens it when
#: the last call came back with a manual whose text did not move, and resets it
#: when the text did move. The measurement behind it: 10 of 73 adjudications
#: returned a byte-identical `theory.dsl`, and 8 of those 10 also changed no
#: later prediction. A manual that did not move is the cheapest available
#: signal that the desk had nothing to work with, and it is available *at the
#: call*, unlike the downstream verdict which needs the future.
ADAPT_OFF = "off"
ADAPT_BY_MANUAL_DELTA = "by_manual_delta"
ADAPTS = (ADAPT_OFF, ADAPT_BY_MANUAL_DELTA)


@dataclass(frozen=True)
class ActionEconomyConfig:
    """The switch. Every default here is the pre-A25 behaviour.

    Shaped after `probe.ProbeEconomyConfig` and `anchor.AnchorConfig` on
    purpose: one dataclass, one `from_env`, one flag in `harness/run.py`. Three
    knobs arriving through three plumbing paths on 2026-07-31 is what
    `--goal-protocol`'s docstring is still apologising for.
    """

    #: The master switch. False == the historic gate, decision for decision and
    #: string for string.
    enabled: bool = False

    #: The floor: this much new world before the desk is worth calling again.
    min_new: int = DEFAULT_MIN_NEW

    #: What the floor counts. See `UNIT_FRAMES` / `UNIT_ACTIONS`.
    unit: str = UNIT_FRAMES

    #: How the floor responds to what the last call bought. See `ADAPT_OFF`.
    adapt: str = ADAPT_OFF

    #: Multiplier applied to the floor each time an adjudication comes back
    #: with an unmoved manual. 2 doubles it; 1 disables the widening without
    #: disabling the mode.
    adapt_factor: int = 2

    #: A ceiling on the adapted floor. Without one, three unmoved manuals in a
    #: row on a 300-action budget would park the desk for the rest of the leg,
    #: and an arm that stops theorising is not this arm. 16 is four times the
    #: historic floor, which is the widest gap any recorded leg would have
    #: needed to spend its whole budget on actions.
    adapt_max: int = 16

    #: How many adjudications one turn may spend. The historic 2 permits a
    #: second round against frames the first already saw; 1 forbids it.
    max_rounds_per_turn: int = DEFAULT_MAX_ROUNDS_PER_TURN

    #: Surprise kinds that do not, on their own, justify a call.
    #:
    #: Empty is historic: any pending surprise opens the gate. The measurement
    #: does NOT presently support putting anything in here -- the eight
    #: adjudications triggered by `probe_refutation` alone were productive (6
    #: of 8 changed a later prediction), and the kind that co-occurs with the
    #: inert calls is `replay_mismatch`, which is the one kind that must never
    #: be deferred: it is certify saying the manual contradicts the recorded
    #: world. So this ships empty and typed, not empty and forgotten.
    defer_kinds: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.unit not in UNITS:
            raise ValueError("unit must be one of %r, not %r" % (UNITS, self.unit))
        if self.adapt not in ADAPTS:
            raise ValueError("adapt must be one of %r, not %r"
                             % (ADAPTS, self.adapt))
        if self.min_new < 0:
            raise ValueError("min_new must not be negative")
        if self.max_rounds_per_turn < 1:
            raise ValueError("max_rounds_per_turn must be at least 1: a turn "
                             "that may never adjudicate cannot repair a manual "
                             "the world has already contradicted")

    @classmethod
    def from_env(cls, env: Optional[Dict[str, str]] = None
                 ) -> "ActionEconomyConfig":
        """`THEORIA_ACTION_ECONOMY=1` turns it on; absent or 0 leaves it off.

        A positive whitelist, for the same reason `ProbeEconomyConfig.from_env`
        and `FrontierConfig.from_env` are: anything unrecognised is off. A
        misspelt switch must not silently enable a framework change that a
        round is trying to measure, and an unparseable number must not silently
        become a default that looks deliberate.
        """
        env = os.environ if env is None else env
        raw = str(env.get("THEORIA_ACTION_ECONOMY", "")).strip().lower()
        if raw not in ("1", "true", "yes", "on"):
            return cls()
        kwargs: Dict[str, Any] = {"enabled": True}
        for var, field, cast in (
                ("THEORIA_ECONOMY_MIN_NEW", "min_new", int),
                ("THEORIA_ECONOMY_UNIT", "unit", str),
                ("THEORIA_ECONOMY_ADAPT", "adapt", str),
                ("THEORIA_ECONOMY_ADAPT_FACTOR", "adapt_factor", int),
                ("THEORIA_ECONOMY_ADAPT_MAX", "adapt_max", int),
                ("THEORIA_ECONOMY_ROUNDS_PER_TURN", "max_rounds_per_turn", int),
        ):
            value = env.get(var)
            if value in (None, ""):
                continue
            try:
                kwargs[field] = cast(value)
            except ValueError:
                continue
        try:
            return cls(**kwargs)
        except ValueError:
            # An out-of-range environment value falls back to the historic
            # config rather than to a partially-applied one. Half a policy is
            # not a policy, and a leg that ran under half of one cannot be
            # compared to anything.
            return cls()

    def as_json(self) -> Dict[str, Any]:
        return {"enabled": self.enabled, "min_new": self.min_new,
                "unit": self.unit, "adapt": self.adapt,
                "adapt_factor": self.adapt_factor,
                "adapt_max": self.adapt_max,
                "max_rounds_per_turn": self.max_rounds_per_turn,
                "defer_kinds": list(self.defer_kinds)}


@dataclass(frozen=True)
class GateDecision:
    """Allow, or refuse with the line that goes into `turns.json`."""

    allow: bool
    reason: Optional[str] = None
    #: What the floor was when this decision was taken. Reported, never acted
    #: on -- an adaptive floor that is not written down is a run whose cadence
    #: cannot be reconstructed from its artefacts.
    floor: Optional[int] = None


class ActionEconomy:
    """The gate, and the little state an adaptive floor needs.

    Stateless on the default rung by construction: `enabled=False` never reads
    `_floor`, so a default run's decisions depend on nothing this object
    remembers.
    """

    def __init__(self, config: Optional[ActionEconomyConfig] = None) -> None:
        self.config = config or ActionEconomyConfig()
        self._floor = self.config.min_new
        #: One row per decision, for the run's own artefacts. Written whether
        #: or not the economy is on: a default leg's rows are what a switched-on
        #: leg is compared against, and a comparison with only one side
        #: measured is not one.
        self.log: list = []

    # -- the floor ---------------------------------------------------------
    @property
    def floor(self) -> int:
        """The floor in force right now, in `config.unit`."""
        if self.config.adapt == ADAPT_OFF:
            return self.config.min_new
        return self._floor

    def note_adjudication(self, *, manual_moved: Optional[bool]) -> None:
        """Told after every adjudication that returned, with what it changed.

        `manual_moved=None` means the caller could not tell -- a desk failure,
        or a snapshot that did not survive. An unknown is not an unmoved
        manual: the floor is left exactly where it was rather than widened on
        a fact nobody established.
        """
        if self.config.adapt != ADAPT_BY_MANUAL_DELTA:
            return
        if manual_moved is None:
            return
        if manual_moved:
            self._floor = self.config.min_new
        else:
            self._floor = min(self._floor * self.config.adapt_factor,
                              self.config.adapt_max)

    # -- the gate ----------------------------------------------------------
    def gate(self, *, has_manual: bool, pending: int, new_frames: int,
             new_actions: int, actions_left: int,
             pending_kinds: Tuple[str, ...] = ()) -> GateDecision:
        """Should the arm stop and pay to think?

        The historic decision, verbatim, when `enabled` is False:

            allow unless (there is a manual) and (too little new evidence) and
            (there is more than a floor's worth of budget left)

        The third clause is the one that has no name in the source. It exists
        so a leg does not end holding evidence it never adjudicated, and it
        means the floor silently stops applying in the last few actions of
        every leg. It is kept on both rungs -- removing it would be a different
        change, and one the measurement did not ask for.
        """
        cfg = self.config
        if not cfg.enabled:
            floor = DEFAULT_MIN_NEW
            if has_manual and new_frames < floor and actions_left > floor:
                return GateDecision(
                    False,
                    "skipped: %d surprise(s) pending but only %d new "
                    "transition(s) since the last call (want %d). Going to "
                    "get more." % (pending, new_frames, floor),
                    floor)
            return GateDecision(True, None, floor)

        floor = self.floor
        seen = new_frames if cfg.unit == UNIT_FRAMES else new_actions
        if has_manual and seen < floor and actions_left > floor:
            return GateDecision(
                False,
                "skipped: %d surprise(s) pending but only %d new %s since the "
                "last call (want %d). Going to get more."
                % (pending, seen, cfg.unit, floor),
                floor)
        if (has_manual and cfg.defer_kinds and pending_kinds
                and all(k in cfg.defer_kinds for k in pending_kinds)):
            return GateDecision(
                False,
                "skipped: %d surprise(s) pending but every one of them is of a "
                "kind this policy defers (%s). Going to get evidence of some "
                "other kind." % (pending, ", ".join(sorted(set(pending_kinds)))),
                floor)
        return GateDecision(True, None, floor)

    def rounds_allowed(self) -> int:
        """How many adjudications this turn may spend.

        The historic value is 2 and the second round is the expensive half:
        24 zero-gap adjudications, $42.40, 68% of the scored ones inert.
        """
        if not self.config.enabled:
            return DEFAULT_MAX_ROUNDS_PER_TURN
        return self.config.max_rounds_per_turn

    # -- the record --------------------------------------------------------
    def note_decision(self, decision: GateDecision, *, step_idx: int,
                      new_frames: int, new_actions: int, pending: int) -> None:
        self.log.append({
            "step_idx": step_idx, "allowed": decision.allow,
            "reason": decision.reason, "floor": decision.floor,
            "unit": self.config.unit if self.config.enabled else UNIT_FRAMES,
            "new_frames": new_frames, "new_actions": new_actions,
            "pending": pending,
        })

    def as_json(self) -> Dict[str, Any]:
        return {"config": self.config.as_json(),
                "floor_now": self.floor,
                "decisions": self.log}


#: Named policies, for the offline counterfactual and for a round's `--`
#: argument. Each is a hypothesis the measurement raised, with the measurement
#: that raised it.
POLICIES: Dict[str, Dict[str, Any]] = {
    "today": {
        "config": ActionEconomyConfig(),
        "why": "the recorded behaviour: floor 4 frames, two adjudications per "
               "turn. This is the control, and it must replay to the recorded "
               "numbers or the replay is wrong.",
    },
    "one-round": {
        "config": ActionEconomyConfig(enabled=True, max_rounds_per_turn=1),
        "why": "forbid the second adjudication in a turn. 24 of 73 recorded "
               "adjudications had zero new actions behind them, cost $42.40, "
               "and 15 of the 22 scored were inert.",
    },
    "floor-8": {
        "config": ActionEconomyConfig(enabled=True, min_new=8),
        "why": "double the floor. Justified only because cost does not grow "
               "with the wait: corr(step_idx, usd) = -0.039.",
    },
    "floor-12": {
        "config": ActionEconomyConfig(enabled=True, min_new=12),
        "why": "triple it. Included to show where the curve stops paying, not "
               "because the measurement recommends it.",
    },
    "actions-unit": {
        "config": ActionEconomyConfig(enabled=True, unit=UNIT_ACTIONS),
        "why": "count the floor in billed actions rather than store steps, so "
               "the gate counts the thing the bill counts.",
    },
    "adaptive": {
        "config": ActionEconomyConfig(enabled=True,
                                      adapt=ADAPT_BY_MANUAL_DELTA),
        "why": "widen the floor after an adjudication whose manual text did "
               "not move; reset it when it does. 10 of 73 came back "
               "byte-identical and 8 of those 10 were inert.",
    },
    "one-round-floor-8": {
        "config": ActionEconomyConfig(enabled=True, min_new=8,
                                      max_rounds_per_turn=1),
        "why": "both of the two levers the measurement actually supports.",
    },
}


def policy(name: str) -> ActionEconomyConfig:
    """A named policy's config. Unknown names raise rather than default.

    Silently falling back to `today` would make a round that misspelt its
    policy look like a null result.
    """
    if name not in POLICIES:
        raise KeyError("unknown action-economy policy %r; known: %s"
                       % (name, ", ".join(sorted(POLICIES))))
    return replace(POLICIES[name]["config"])
