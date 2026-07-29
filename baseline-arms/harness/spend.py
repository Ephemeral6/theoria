"""This track's binding to the shared spend pool (`proxy/spend_gate.py`).

INC-BA-003 is why this file exists, and the shape of the fix is not ours: the
pool, the lock and the ceiling all live in `proxy/spend_gate.py`, which is the
one register that every session on this machine sums. What this module adds is
the *plug*, because `baseline-arms` does not spend through the proxy. `bare_cc`
drives `arc_client` straight at `three.arcprize.org` and shells out to the
`claude -p` CLI, so neither of the proxy's two egress paths -- the only two the
gate was already wired to -- is on this track's spending path at all. Before
this file, the pool's own report showed `$0.0000` against every baseline-arms
campaign that had ever run, which is not a small number: it is no number.

Two quantities, charged where they are actually incurred:

  * **actions** -- one per outbound ARC HTTP request. That is the unit
    `spend_policy.json` defines (`action_ceiling`, with the provenance note
    saying explicitly that it is *not* the scorecard's successful-action count),
    and it is the unit the 600 rpm limit is charged against. It is charged per
    *request*, not per successful action, so D-005's 5-11x retry amplification
    is visible to the pool rather than hidden behind it.
  * **dollars** -- one settlement per `claude -p` call, from the CLI envelope's
    own `total_cost_usd`. Pre-authorised against `MODEL_CALL_CEILING_USD` before
    the subprocess starts, so the check happens before the money moves rather
    than after, which is the difference between a gate and a receipt.

**The order is check-then-spend-then-record, and it is not negotiable.** The
check refuses; the record accounts. `record` is called even when the request
failed, because a request that got a 400 still crossed the wire, still counted
against the rate limit, and still happened. Charging only for what succeeded is
how a pool undercounts itself into an incident.
"""

import os
import sys
from typing import Any, Dict, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
TRACK = os.path.dirname(HERE)
REPO = os.path.dirname(TRACK)

if REPO not in sys.path:
    sys.path.insert(0, REPO)

from proxy.spend_gate import (                                     # noqa: E402
    NoReservation, SpendGate, SpendGateError, SpendGateTripped, SpendGateUnavailable,
)

__all__ = ["SpendBinding", "open_binding", "NoSpendBinding", "NoReservation",
           "SpendGate", "SpendGateError", "SpendGateTripped", "SpendGateUnavailable",
           "MODEL_CALL_CEILING_USD"]


#: What one `claude -p` call is pre-authorised for, before it is allowed to run.
#:
#: Anchored, like every other threshold on this track, on a measured number
#: rather than a feeling: the M4 pilot's haiku tier settled at $0.0243 per model
#: call (BUDGET_REPORT 2.1) and the ar25 envelope cells at roughly $0.035
#: ($0.73-$1.00 over 21-29 calls, BUDGET_REPORT 11.1). $0.25 is about 7x the
#: worst of those.
#:
#: Deliberately generous, and that is not a weakness. `check()` verifies that
#: the headroom *exists*; it does not consume it, and the settlement that
#: follows is the real figure. So a loose ceiling costs nothing except refusing
#: slightly early when the pool is nearly empty, whereas a tight one would
#: refuse calls that were affordable. What the ceiling actually buys is the
#: property that no call can start without the pool having been asked first.
MODEL_CALL_CEILING_USD = 0.25


class NoSpendBinding(SpendGateError):
    """An outbound call was attempted with no claim on the shared pool.

    Its own class rather than a bare `NoReservation` because the two failures
    have different repairs: `NoReservation` means the claim expired or was
    released, and this means the caller never wired one up at all.
    """


class SpendBinding:
    """A live reservation, plus the four verbs bound to it.

    Held by `ArcClient` and by `bare_cc.play`, which is to say: by everything on
    this track that can spend. It is passed explicitly and has no default,
    because a default is how the gate becomes optional and an optional gate is
    the thing INC-BA-003 already proved does not work.
    """

    def __init__(self, gate: SpendGate, reservation,
                 model_call_ceiling_usd: float = MODEL_CALL_CEILING_USD):
        self.gate = gate
        self.reservation = reservation
        self.model_call_ceiling_usd = float(model_call_ceiling_usd)
        #: Counters for this process only. They are for the run summary, never
        #: for a limit decision -- every limit reads the global sum, which is
        #: the entire point of the module underneath.
        self.actions_charged = 0
        self.usd_charged = 0.0
        self.model_calls_charged = 0
        self.unpriced_calls = 0

    # -- ARC HTTP ----------------------------------------------------------
    def check_action(self, n: int = 1) -> None:
        """Before the socket opens. Raises to refuse."""
        self.gate.check(self.reservation, usd=0.0, actions=n)

    def record_action(self, n: int = 1, detail: Optional[Dict[str, Any]] = None) -> None:
        """After it happened -- success or failure, both crossed the wire."""
        self.gate.record(self.reservation, usd=0.0, actions=n, detail=detail or {})
        self.actions_charged += n

    # -- model dollars -----------------------------------------------------
    def check_model_call(self) -> None:
        """Before `claude -p` starts, against this call's pre-authorised ceiling."""
        self.gate.check(self.reservation, usd=self.model_call_ceiling_usd, actions=0)

    def record_model_call(self, usd: Optional[float],
                          detail: Optional[Dict[str, Any]] = None) -> None:
        """Settle one model call at what the CLI says it cost.

        `usd is None` means the envelope carried no `total_cost_usd`. That call
        is charged its pre-flight ceiling and flagged `unpriced`, which is the
        convention `SPEND_GATE.md` section 3 already fixed for the model proxy:
        a call whose price is unknown must make the pool's dollar total a stated
        lower bound, not a silent zero. It has never yet fired here -- 274
        model_call records on this track, none missing the field -- and it is
        written for the case where it does.
        """
        unpriced = usd is None
        amount = self.model_call_ceiling_usd if unpriced else float(usd)
        self.gate.record(self.reservation, usd=amount, actions=0,
                         unpriced=unpriced, detail=detail or {})
        # Accumulate raw, round once at the edge. Rounding at every step made
        # this counter drift from a plain sum of the same figures -- up to
        # $0.000006 over thirty calls, which an adversarial audit of the g50t
        # cells found by reconciling three totals that should have been one
        # number. Immaterial as money and material as a claim: "the pool and the
        # cell agree exactly" has to survive being checked exactly.
        self.usd_charged += amount
        self.model_calls_charged += 1
        if unpriced:
            self.unpriced_calls += 1

    # -- lease -------------------------------------------------------------
    def renew(self, ttl_seconds: Optional[float] = None) -> None:
        self.gate.renew(self.reservation, ttl_seconds=ttl_seconds)

    def release(self, reason: str = "closed") -> None:
        self.gate.release(self.reservation, reason)

    def describe(self) -> Dict[str, Any]:
        """What goes into the run record, so a cell says which pool it drew on."""
        return {
            "reservation_id": self.reservation.reservation_id,
            "campaign": self.reservation.campaign,
            "usd_cap": self.reservation.usd_cap,
            "action_cap": self.reservation.action_cap,
            "pool": self.gate.fingerprint(),
            "actions_charged": self.actions_charged,
            "usd_charged": round(self.usd_charged, 6),
            "model_calls_charged": self.model_calls_charged,
            "unpriced_calls": self.unpriced_calls,
        }


def open_binding(campaign: str, usd_cap: float, action_cap: int, *,
                 holder: Optional[Dict[str, Any]] = None,
                 ttl_seconds: Optional[float] = None,
                 gate: Optional[SpendGate] = None) -> SpendBinding:
    """Claim headroom on the shared pool and return the binding that spends it.

    Raises `SpendGateTripped` if the pool -- summed across every campaign and
    every session, including ones this process cannot see -- has no room. That
    refusal is the deliverable: it is the sentence INC-BA-003 had no way to say.
    """
    gate = gate if gate is not None else SpendGate()
    holder = dict(holder or {})
    holder.setdefault("track", "baseline-arms")
    reservation = gate.reserve(campaign, usd_cap, action_cap,
                               holder=holder, ttl_seconds=ttl_seconds)
    return SpendBinding(gate, reservation)
