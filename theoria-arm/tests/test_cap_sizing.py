"""A leg authorised for N actions must be able to spend N before its cap binds.

`runs/20260729T004020Z-leg01` is the counter-example this file exists to make
impossible. It declared 12 successful actions, was handed a 105-request
reservation by `plan_caps`, and stopped at **9** -- not because the arm failed,
but because the reservation was sized by an arithmetic that had never been
checked against what the pool actually charges.

Three separate errors produced that one number, and each gets a test here:

* the sizing constant was borrowed from another arm, in another denominator
  (`HTTP_PER_COMMAND`, INC-011's `bare_cc` cell);
* the fixed term counted three *endpoints* as three *requests*, when RESET and
  `close_scorecard` are 40-attempt waves;
* the result was multiplied by `env_max_attempts = 3`, the env proxy's retry
  **ceiling**, as though it were the mean it delivers (measured: 1.0031).

What is asserted below is mostly not the value of a constant -- a test that only
pins `780 == 780` would have passed just as happily on the broken formula. What
is asserted is the *property* the arithmetic has to have: that the cap it
computes is large enough for the level it was computed from, at the amplification
this arm's own ledgers recorded, including on the worst leg those ledgers hold.

Nothing here touches the network, the pool ledger, or the desk:
`require_headroom=False` on every call.
"""

from __future__ import annotations

import math
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from harness import spend as spend_mod                                # noqa: E402


#: The four live legs in `runs/`, as (leg, outbound ACTION requests, successful
#: ACTIONs). Numerator: sum of `http.attempts` over `env_step` records with
#: `http.forwarded=true` and an ACTION name. Denominator: those with status 200.
#: Mock legs (`env_upstream` = 127.0.0.1) are excluded on purpose -- they answer
#: 200 first time and describe a fixture, not a transport.
LIVE_LEGS = (
    ("20260728T012311Z-g50t-first-contact-aborted", 84, 5),
    ("20260728T014402Z-g50t-first-contact-aborted", 36, 6),
    ("20260728T015354Z-g50t-first-contact", 36, 7),
    ("20260729T004020Z-leg01", 95, 9),
)

#: Fixed outbound cost observed live: `open_scorecard` never retried; the RESET
#: wave ran to 18; the `close_scorecard` wave ran to 10.
WORST_OPEN, WORST_RESET, WORST_CLOSE = 1, 18, 10

#: The level this arm is authorised for.
AUTHORISED_ACTIONS = 40


def _caps(actions: int, commands: int = 2000):
    return spend_mod.plan_caps(actions=actions, commands=commands,
                               cost_ceiling_usd=20.0, require_headroom=False)


# ---------------------------------------------------------- 1. the property

def test_forty_authorised_actions_can_actually_be_spent():
    """The requirement, stated as arithmetic rather than as a number.

    At the pooled amplification this arm's ledgers recorded, plus the worst
    fixed cost they recorded, a 40-action leg needs
    `1 + 18 + 10 + 40 x 9.296 = 401` outbound requests. The cap must cover that
    with room, or the leg dies before its budget does -- which is exactly what
    happened on leg01.
    """
    pooled = sum(out for _, out, _ in LIVE_LEGS) / sum(ok for _, _, ok in LIVE_LEGS)
    needed = WORST_OPEN + WORST_RESET + WORST_CLOSE + AUTHORISED_ACTIONS * pooled

    caps = _caps(AUTHORISED_ACTIONS)
    assert caps.action_cap >= needed, (
        "a leg authorised for %d actions was reserved %d outbound requests, but "
        "at this arm's own measured %.3f requests per successful action it needs "
        "%.0f. That is the leg01 failure with different numbers."
        % (AUTHORISED_ACTIONS, caps.action_cap, pooled, needed))


@pytest.mark.parametrize("leg,outbound,ok", LIVE_LEGS)
def test_the_cap_survives_every_leg_this_arm_has_actually_run(leg, outbound, ok):
    """Not the mean: each observed leg, including the 16.8x worst one.

    A cap sized to the pooled ratio trips on any leg worse than average, which
    stops the leg correctly but for the wrong reason. `OUTBOUND_TAIL_SAFETY`
    exists for this test; if it is ever lowered, this is what says so.
    """
    per_action = outbound / ok
    needed = WORST_OPEN + WORST_RESET + WORST_CLOSE + AUTHORISED_ACTIONS * per_action

    caps = _caps(AUTHORISED_ACTIONS)
    assert caps.action_cap >= needed, (
        "%s ran at %.3f outbound requests per successful action; a 40-action leg "
        "at that rate needs %.0f and the cap is %d"
        % (leg, per_action, needed, caps.action_cap))


def test_the_fixed_term_pays_for_the_close_as_well_as_the_open():
    """A leg with zero actions still has to open, reset and close.

    The close is the one that bites. `arc.close_scorecard` calls `_post`
    directly, so it consults neither `Budget` nor `SpendBinding` -- but every
    attempt still enters the proxy and is still charged. If the cap binds first,
    all 40 tries are refused and the scorecard's score is lost, because it exists
    only in a successful close response (D-015). A fixed term that cannot pay for
    the close does not truncate the leg; it discards its result.
    """
    caps = _caps(0)
    assert caps.action_cap >= WORST_OPEN + WORST_RESET + WORST_CLOSE, (
        "the fixed term must cover the worst open+RESET+close ever observed "
        "live (1 + 18 + 10); it is %d" % caps.action_cap)


def test_the_cap_grows_with_the_declared_level():
    """Two legs, twice the actions, and the difference is the actions' cost.

    Guards against a future 'fix' that pins a constant cap and lets the fixed
    term absorb the level.
    """
    small, large = _caps(20), _caps(40)
    assert large.action_cap > small.action_cap
    grew = large.action_cap - small.action_cap
    assert grew == math.ceil(20 * spend_mod.OUTBOUND_PER_ACTION
                             * spend_mod.OUTBOUND_TAIL_SAFETY)


# ------------------------------------------------- 2. the double-count, gone

def test_the_cap_does_not_multiply_by_the_env_proxy_retry_ceiling():
    """`env_max_attempts` is passed, recorded, and not a factor.

    It is a real envelope: `env_proxy._forward` mints one permit and
    `forward.forward` increments `permit.attempts_made` once per socket, so one
    arm-level command can charge the pool up to `max_attempts` times. What it is
    not is a *multiplier on a plan*: its measured mean is 1.0031, because it
    fires on 429/5xx/transport and this arm's failure mode is a 400.

    Sizing on the ceiling was worth a factor of 3 in a formula whose base
    constant was already wrong by a factor of 5 in the other direction.
    """
    one = spend_mod.plan_caps(actions=40, commands=2000, cost_ceiling_usd=20.0,
                              env_max_attempts=1, require_headroom=False)
    three = spend_mod.plan_caps(actions=40, commands=2000, cost_ceiling_usd=20.0,
                                env_max_attempts=3, require_headroom=False)
    assert one.action_cap == three.action_cap, (
        "the plan changed when the proxy's retry ceiling changed, which is the "
        "double-count this arithmetic was fixed to remove")
    assert three.arithmetic["env_max_attempts"] == 3, "still recorded"
    assert three.arithmetic["env_outbound_per_arm_command_measured"] < 1.1, (
        "the measured mean has to be in the record next to the ceiling, or the "
        "next reader has no way to see why the ceiling is not used")


def test_the_measured_ratio_is_in_the_pools_own_unit():
    """Outbound requests per successful ACTION -- not attempts, not commands.

    `Budget.as_json()['http_amplification']` is `commands_sent/actions_ok`, which
    counts arm-level attempts including ones refused before the wire. On leg01 it
    read 222.222 for a leg whose transport managed 10.556. A constant derived
    from that field would be sizing a reservation on a counter.
    """
    provenance = spend_mod.OUTBOUND_PER_ACTION_PROVENANCE
    assert spend_mod.OUTBOUND_PER_ACTION_IS_VALIDATED is True
    assert "http.forwarded" in provenance, (
        "the provenance must name the field that distinguishes a request that "
        "opened a socket from an attempt that did not")
    assert "spend_gate.jsonl" in provenance, (
        "one ledger is a claim; two that agree is a measurement")
    for leg, _, _ in LIVE_LEGS:
        stem = leg.split("-")[0]
        assert stem in provenance, "%s is in the sum and must be named" % leg


def test_the_borrowed_constant_is_kept_and_no_longer_consumed():
    """`HTTP_PER_COMMAND` stays, still marked unvalidated, out of the sizing.

    Deleting it would delete the record of *why* it could not be trusted, and
    leave the next session free to re-borrow INC-011's `bare_cc` cell. Leaving it
    in the sizing path is what produced leg01. So: kept, flagged, unused.
    """
    assert spend_mod.HTTP_PER_COMMAND_IS_VALIDATED is False
    assert "INC-011" in spend_mod.HTTP_PER_COMMAND_PROVENANCE

    arithmetic = _caps(40).arithmetic
    assert arithmetic["http_per_command_retired_from_sizing"] is True
    assert arithmetic["http_per_command_is_validated"] is False

    # The load-bearing part: changing it changes nothing.
    original = spend_mod.HTTP_PER_COMMAND
    try:
        spend_mod.HTTP_PER_COMMAND = 99.0
        assert _caps(40).action_cap == arithmetic["action_cap"], (
            "the retired constant still moves the cap, so it is not retired")
    finally:
        spend_mod.HTTP_PER_COMMAND = original


# ------------------------------------------- 3. what must not be given away

def test_one_leg_does_not_swallow_the_shared_pool():
    """A cap large enough to finish is not a licence to hold the pool.

    24000 is the pool's action ceiling (`proxy/spend_policy.json`), shared across
    every arm and every concurrent session. A 40-action leg at 780 is 3.3% of it;
    the 120-action P-8 shape at 2268 is 9.5%. The bound is loose on purpose --
    what it forbids is a formula whose growth makes one leg unaffordable.
    """
    ceiling = 24000
    assert _caps(40).action_cap < ceiling * 0.05
    assert _caps(120).action_cap < ceiling * 0.15


def test_the_command_ceiling_still_bounds_everything():
    """`Budget.commands x env_max_attempts` is a bound, not an estimate.

    `Budget.check` raises before the (n+1)th attempt, so the arm cannot exceed
    it however badly the retries go -- and the cap is min'd against it, so a
    generous plan cannot reserve headroom the arm has no way to spend.
    """
    caps = spend_mod.plan_caps(actions=500, commands=40, cost_ceiling_usd=1.0,
                               require_headroom=False)
    assert caps.arithmetic["action_cap_planned"] > caps.arithmetic["action_cap_hard_bound"]
    assert caps.action_cap == caps.arithmetic["action_cap_hard_bound"] == 40 * 3
    assert caps.arithmetic["arm_attempts_capped_by_commands_ceiling"] is True


def test_leg01_would_have_finished_under_this_arithmetic():
    """The regression, named. 12 declared actions, 105 given, 9 spent.

    Under this sizing the same leg is reserved 260, and its recorded cost -- 1
    scorecard open, 9 RESET, 95 ACTION requests for 9 actions -- extrapolates to
    `1 + 9 + 12 x 10.556 = 137` for the full 12. It finishes with room, and it
    finishes *inside* the reservation rather than by being allowed to overrun it.
    """
    observed_open, observed_reset, per_action = 1, 9, 95 / 9
    would_have_needed = observed_open + observed_reset + 12 * per_action

    caps = _caps(12)
    assert caps.action_cap == 260
    assert caps.action_cap > would_have_needed
    assert 105 < would_have_needed, (
        "if 105 had been enough, leg01 would not be the reason this file exists")
