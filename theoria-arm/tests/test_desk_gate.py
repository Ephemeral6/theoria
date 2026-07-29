"""The desk's binding to the shared spend pool. Offline, and against a temp pool.

Nothing here touches `proxy/var/spend_gate.jsonl`. Every test builds its own
`SpendPolicy` pointing at a `tmp_path` ledger, because the real one is money and
is append-only: a fictional dollar written into it could not be taken back
short of a human moving the pool aside and recording an incident. The one place
the tracked pool is named is `test_the_one_true_pool_is_the_default_expectation`,
which reads a fingerprint and writes nothing.

Nothing here starts a `claude -p` subprocess either. `ModelDesk._invoke` is the
seam and it is stubbed in every test, so the suite spends $0.00 while
exercising the code that decides what a call costs.

What is checked, in the order the defect report asked for it:

  1. a desk call with no reservation is refused rather than degraded;
  2. `SpendGateTripped` latches and stops the run -- no retry, no re-reserve;
  3. an envelope that cannot price itself is charged its ceiling and flagged
     `unpriced`, never $0.00;
  4. the claim is released even when the run raises;
  5. a gate that is not the one true pool is refused at construction;
  6. 先算后花: the budget is computed and refused against the pool's GLOBAL
     free headroom before anything is reserved.
"""

import glob
import json
import os
import re
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(HERE)
if ARM not in sys.path:
    sys.path.insert(0, ARM)

import _bootstrap                                     # noqa: E402,F401

from proxy.spend_gate import SpendGate, SpendPolicy   # noqa: E402

from harness import run as run_mod                    # noqa: E402
from harness import spend as spend_mod                # noqa: E402
from harness.modelcall import ModelDesk, ModelError               # noqa: E402


# ------------------------------------------------------------------ fixtures

def _policy(path, *, usd_ceiling=214.9, action_ceiling=24000,
            pool="test-scratch-pool"):
    return SpendPolicy({
        "v": "1.0", "pool": pool,
        "usd_ceiling": usd_ceiling, "action_ceiling": action_ceiling,
        "ledger": os.path.abspath(str(path)),
        "default_ttl_seconds": 3600, "lock_timeout_seconds": 5.0,
        "default_run_caps": {"usd": 5.0, "actions": 600},
    })


@pytest.fixture
def pool(tmp_path):
    """A pool of one, in a temp dir. Never the tracked ledger."""
    return SpendGate(_policy(tmp_path / "spend_gate.jsonl"))


@pytest.fixture
def expect(pool):
    """The explicit expectation that lets the binding accept the temp pool."""
    return {"pool": pool.policy.pool,
            "ledger_abspath": os.path.abspath(pool.ledger_path)}


@pytest.fixture
def caps():
    return spend_mod.plan_caps(actions=12, commands=2000, cost_ceiling_usd=20.0,
                               require_headroom=False)


@pytest.fixture
def binding(pool, expect, caps):
    b = spend_mod.open_binding("theoria-arm:test:g50t-5849a774:unit", caps,
                               gate=pool, expect_pool=expect)
    try:
        yield b
    finally:
        b.release("test over")


def records(gate):
    """Every line of the temp pool, in order."""
    with open(gate.ledger_path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def spends(gate):
    return [r for r in records(gate) if r["kind"] == "spend"]


class FakeRun:
    """The two things `ModelDesk` uses off a `RunLedger`, and nothing else."""

    def __init__(self):
        self.run_id = "r-test"
        self.model_calls = []

    def model_call(self, **fields):
        self.model_calls.append(fields)


def desk(run=None, *, spend=None, envelope=None, raises=None,
         cost_ceiling_usd=20.0):
    """A `ModelDesk` whose subprocess seam is stubbed. Spends $0.00."""
    d = ModelDesk(run if run is not None else FakeRun(), model="mock-desk-1",
                  cost_ceiling_usd=cost_ceiling_usd, spend=spend)

    def _invoke(prompt, model):
        if raises is not None:
            raise raises
        return dict(envelope or {}), 12, ""

    d._invoke = _invoke                               # the only seam that costs
    return d


# ------------------------------------------------- 1. no reservation, no call

def test_a_desk_call_without_a_reservation_is_refused(pool):
    """The defect, stated as a test.

    Before this wiring `ModelDesk.call` shelled out to `claude -p` with nothing
    but a float standing between it and the shared bill. An ungated call is not
    a degraded mode of a gated one; it is the thing INC-BA-003 was.
    """
    started = []
    d = desk(envelope={"result": "hi", "total_cost_usd": 0.5,
                       "usage": {"input_tokens": 1, "output_tokens": 1}})
    inner = d._invoke
    d._invoke = lambda p, m: (started.append(1), inner(p, m))[1]

    with pytest.raises(spend_mod.NoSpendBinding):
        d.call("prompt", beat="theorize")

    assert started == [], "the subprocess must not start before the gate answers"
    assert d.calls == 0
    assert not os.path.exists(pool.ledger_path)


def test_the_binding_may_be_reached_off_the_run_ledger(binding, pool):
    """`inner/loop.py` belongs to another agent, so `harness/run.py` attaches
    the claim to the RunLedger and the desk finds it there. A fallback, not a
    default: absent, `call()` still raises."""
    run = FakeRun()
    run.spend_binding = binding
    d = desk(run, envelope={"result": "ok", "total_cost_usd": 0.5,
                            "usage": {"input_tokens": 1, "output_tokens": 1}})
    assert d.call("p", beat="theorize") == "ok"
    assert d.binding() is binding


# ---------------------------------------------------- 2. a trip stops the run

def test_a_tripped_gate_stops_the_run_and_does_not_retry(pool, expect):
    """闸门红了立刻停. The latch is the point: the second call is refused
    without asking the pool again, and nothing anywhere re-reserves smaller to
    squeeze under the ceiling."""
    small = spend_mod.plan_caps(actions=4, commands=100, cost_ceiling_usd=1.0,
                                model_call_ceiling_usd=1.0,
                                require_headroom=False)
    assert small.usd_cap == 2.0
    b = spend_mod.open_binding("theoria-arm:test:g50t-5849a774:trip", small,
                               gate=pool, expect_pool=expect,
                               model_call_ceiling_usd=1.0)
    try:
        run = FakeRun()
        run.spend_binding = b
        priced = {"result": "ok", "total_cost_usd": 1.5,
                  "usage": {"input_tokens": 1, "output_tokens": 1}}
        d = desk(run, envelope=priced, cost_ceiling_usd=None)

        d.call("p", beat="theorize")                  # $1.50 of a $2.00 cap
        with pytest.raises(spend_mod.SpendGateTripped) as first:
            d.call("p", beat="theorize")              # +$1.00 ceiling > $2.00
        assert first.value.rule == "RESERVATION_USD_CAP"
        assert b.tripped is first.value

        # Latched: the same exception object, and the pool is not consulted.
        before = len(records(pool))
        with pytest.raises(spend_mod.SpendGateTripped) as again:
            b.check_model_call()
        assert again.value is first.value
        assert len(records(pool)) == before, \
            "a latched binding must not touch the pool at all"

        # And the run stopped where it tripped: one settled call, not two.
        assert [s["usd"] for s in spends(pool)] == [1.5]
    finally:
        b.release("test over")


def test_a_trip_on_record_still_writes_the_money_down(pool, expect):
    """`record` appends before it evaluates the caps, and so must the binding's
    counters. Money that was spent is a fact; a gate that refused to write it
    down because it was over budget would make the pool look under budget."""
    tiny = spend_mod.Caps(usd_cap=1.0, action_cap=10, ttl_seconds=3600,
                          arithmetic={})
    b = spend_mod.open_binding("theoria-arm:test:g50t-5849a774:overrun", tiny,
                               gate=pool, expect_pool=expect,
                               model_call_ceiling_usd=0.1)
    try:
        with pytest.raises(spend_mod.SpendGateTripped):
            b.record_model_call(3.0)                  # $3.00 against a $1.00 cap
        assert [s["usd"] for s in spends(pool)] == [3.0]
        assert b.usd_charged == 3.0
        assert b.tripped is not None
    finally:
        b.release("test over")


# ------------------------------------------- 3. an unpriced call is not free

def test_an_envelope_with_no_price_is_charged_its_ceiling_and_flagged(binding, pool):
    """`proxy/model_proxy.py:239,303`'s rule. Assuming a call cost nothing is
    letting the provider decide whether it gets billed."""
    run = FakeRun()
    run.spend_binding = binding
    d = desk(run, envelope={"result": "text", "usage": {}})   # no total_cost_usd

    assert d.call("p", beat="theorize") == "text"

    last = spends(pool)[-1]
    assert last["unpriced"] is True
    assert last["usd"] == spend_mod.MODEL_CALL_CEILING_USD == 4.0
    assert last["usd"] > 0, "an unpriced call is never settled at $0.00"
    assert binding.unpriced_calls == 1 and d.unpriced_calls == 1
    assert pool.totals().unpriced_calls == 1


def test_a_zero_with_no_tokens_behind_it_is_unpriced_not_free(binding, pool):
    """`total_cost_usd: 0.0` with an empty usage block is the shape of a missing
    field, and a missing field must not settle as $0.00."""
    run = FakeRun()
    run.spend_binding = binding
    d = desk(run, envelope={"result": "t", "total_cost_usd": 0.0, "usage": {}})
    d.call("p", beat="theorize")
    assert spends(pool)[-1]["unpriced"] is True
    assert spends(pool)[-1]["usd"] == 4.0


def test_a_priced_call_settles_at_the_envelopes_own_figure(binding, pool):
    """The ceiling is a pre-authorisation, not a charge: `check` verifies the
    headroom exists and consumes nothing, and the settlement is the real
    number."""
    run = FakeRun()
    run.spend_binding = binding
    d = desk(run, envelope={"result": "t", "total_cost_usd": 1.489011,
                            "usage": {"input_tokens": 9, "output_tokens": 3}})
    d.call("p", beat="theorize")
    last = spends(pool)[-1]
    assert last["unpriced"] is False
    assert last["usd"] == 1.489011
    assert pool.totals().usd == 1.489011


def test_an_incomplete_usage_block_does_not_blind_a_priced_pool(binding, pool):
    """A priced envelope whose `usage` is merely incomplete is exact in dollars,
    so it is NOT flagged: `UNPRICED_SPEND` would otherwise refuse every dollar
    in the shared pool, for every session, on the strength of a missing token
    count (`spend_gate.py:860`). The incompleteness is recorded instead."""
    run = FakeRun()
    run.spend_binding = binding
    d = desk(run, envelope={"result": "t", "total_cost_usd": 0.75, "usage": {}})
    d.call("p", beat="theorize")
    last = spends(pool)[-1]
    assert last["unpriced"] is False and last["usd"] == 0.75
    assert last["detail"]["usage_complete"] is False
    assert pool.totals().unpriced_calls == 0


def test_a_call_that_raises_is_still_charged(binding, pool):
    """A timeout is exactly the case where the provider was reached and the
    answer thrown away. Charged at its ceiling, flagged unpriced, and the
    exception is re-raised unchanged."""
    run = FakeRun()
    run.spend_binding = binding
    d = desk(run, raises=RuntimeError("claude -p timed out"))

    with pytest.raises(RuntimeError, match="timed out"):
        d.call("p", beat="theorize")

    last = spends(pool)[-1]
    assert last["unpriced"] is True and last["usd"] == 4.0
    assert last["detail"]["outcome"] == "raised_before_a_price"


def test_an_empty_reply_is_charged_before_it_is_diagnosed(binding, pool):
    """The empty-reply raise happens after the settlement, not instead of it:
    the first live theorize call spent $0.73 and returned nothing."""
    run = FakeRun()
    run.spend_binding = binding
    d = desk(run, envelope={"result": "", "subtype": "error_max_turns",
                            "total_cost_usd": 0.73,
                            "usage": {"input_tokens": 1, "output_tokens": 0}})
    with pytest.raises(Exception, match="returned no text"):
        d.call("p", beat="theorize")
    assert [s["usd"] for s in spends(pool)] == [0.73]


def test_a_forbidden_beat_never_reaches_the_gate(binding, pool):
    """Constraint 8 refuses before the pool is asked: certify and commit are
    zero-call by construction, so there is nothing to pre-authorise."""
    run = FakeRun()
    run.spend_binding = binding
    d = desk(run, envelope={"result": "x", "total_cost_usd": 1.0})
    with pytest.raises(Exception, match="may not spend a model call"):
        d.call("p", beat="certify")
    assert spends(pool) == []


def test_the_arm_local_ceiling_is_a_second_independent_ceiling(binding, pool):
    """Two ceilings, and the arm-local one fires first on the arm's own
    account. `usd_cap = cost_ceiling + one call` is what keeps them independent
    instead of the pool tripping on the last permitted call."""
    run = FakeRun()
    run.spend_binding = binding
    d = desk(run, cost_ceiling_usd=1.0,
             envelope={"result": "t", "total_cost_usd": 1.2,
                       "usage": {"input_tokens": 1, "output_tokens": 1}})
    d.call("p", beat="theorize")                      # $1.20 >= $1.00 ceiling
    with pytest.raises(Exception, match="ceiling"):
        d.call("p", beat="theorize")
    assert len(spends(pool)) == 1
    assert binding.tripped is None, \
        "the arm-local ceiling stopped this, so the pool must not have tripped"


# ------------------------------------------------- 4. release, whatever happens

def test_the_claim_is_released_even_when_the_call_raises(pool, expect, caps):
    b = spend_mod.open_binding("theoria-arm:test:g50t-5849a774:finally", caps,
                               gate=pool, expect_pool=expect)
    run = FakeRun()
    run.spend_binding = b
    d = desk(run, raises=RuntimeError("boom"))

    with pytest.raises(RuntimeError):
        try:
            d.call("p", beat="theorize")
        finally:
            b.release("the call raised")

    assert b.released is True
    assert [r["kind"] for r in records(pool)][-1] == "release"
    assert pool.totals().live == [], "the unspent hold must be back in the pool"
    assert pool.totals().usd == 4.0, "what was spent stays counted forever"


def test_release_is_idempotent(binding, pool):
    """The caller that most needs it is an exception path, and a second release
    raising would replace the real failure with a bookkeeping one."""
    binding.release("once")
    binding.release("twice")
    assert sum(1 for r in records(pool) if r["kind"] == "release") == 1


def test_a_run_that_crashes_hands_the_pool_back(tmp_path, monkeypatch, pool,
                                                expect, caps):
    """`Run.__exit__` releases in a `finally`, so a crash in `arm.play()` cannot
    strand the shared pool for the lease's whole duration. 43 crashed runs did
    exactly that upstream, and the recovery was to wait an hour."""
    monkeypatch.setattr(run_mod, "RUNS_DIR", str(tmp_path / "runs"))

    class Exploding:
        def play(self):
            raise RuntimeError("first contact")

        def summary(self):
            return {}

    with pytest.raises(RuntimeError, match="first contact"):
        run_mod.play("g50t-5849a774", "crash-test",
                     lambda env_base, run: Exploding(),
                     env_upstream="http://127.0.0.1:1", env_key=None,
                     require_key=False, caps=caps, spend_gate=pool,
                     expect_pool=expect)

    assert pool.totals().live == []
    assert [r["kind"] for r in records(pool)][-1] == "release"


def test_a_run_names_its_campaign_and_shares_one_claim(tmp_path, monkeypatch,
                                                       pool, expect, caps):
    """One reservation for the run, `proxy/runner.py:run_game`'s pattern: the
    env proxy is handed the same claim the desk spends under, so the run holds
    the pool once rather than twice."""
    monkeypatch.setattr(run_mod, "RUNS_DIR", str(tmp_path / "runs"))
    with run_mod.Run("g50t-5849a774", "named", env_upstream="http://127.0.0.1:1",
                     require_key=False, caps=caps, spend_gate=pool,
                     expect_pool=expect) as r:
        assert r.campaign == \
            "theoria-arm:A3-campaign-devpile:g50t-5849a774:named"
        assert not r.campaign.startswith("theoria:r-")
        assert r._cfg.spend_reservation is r.spend.reservation
        assert r._cfg.spend_reservation_owned is False, \
            "the env proxy must not release a claim the desk still spends under"
        assert r.run.spend_binding is r.spend
        assert len(pool.totals().live) == 1


def test_the_auto_derived_campaign_name_is_refused(pool, expect, caps):
    """`theoria:r-<uuid>` is attributable and says nothing about what the run
    was for. The pool's report for this arm is already a column of them."""
    with pytest.raises(spend_mod.SpendGateError, match="derived name"):
        spend_mod.open_binding("theoria:r-0123456789abcdef", caps, gate=pool,
                               expect_pool=expect)


# -------------------------------------------------------- 5. the one true pool

def test_the_one_true_pool_assertion_rejects_a_wrong_ledger_path(pool, caps):
    """The trap: `POOL_ROOT` resolves a relative ledger against the MAIN
    checkout. If it ever resolved against the importer there would be one
    full-ceiling pool per worktree, ~50 of them, and `fingerprint()`'s relative
    `ledger_path` would have made the split invisible afterwards."""
    with pytest.raises(spend_mod.PoolMismatch) as exc:
        spend_mod.assert_one_true_pool(pool)          # default expectation
    assert "ledger_abspath" in str(exc.value)

    with pytest.raises(spend_mod.PoolMismatch):
        spend_mod.open_binding("theoria-arm:test:g50t-5849a774:wrong", caps,
                               gate=pool)             # refused before reserving
    assert not os.path.exists(pool.ledger_path), \
        "a refused pool must not be written to at all"


def test_a_pool_with_the_right_path_but_the_wrong_name_is_refused(tmp_path, caps):
    real = spend_mod.one_true_pool()
    impostor = SpendGate(_policy(real["ledger_abspath"], pool="not-the-pool"))
    with pytest.raises(spend_mod.PoolMismatch, match="pool is 'not-the-pool'"):
        spend_mod.assert_one_true_pool(impostor)


def test_a_scratch_pool_may_not_be_pointed_at_a_run_ledger(tmp_path):
    """A spend pool holds `kind` records under a cross-process lock; a run
    ledger holds `event` records under an in-process one. Mixing them corrupts
    both -- the gate fails closed on a line it cannot total and `read_ledger`
    sees spend lines it cannot place."""
    for bad in (tmp_path / "runs" / "some-slug" / "x.jsonl",
                tmp_path / "ledger.jsonl"):
        with pytest.raises(spend_mod.SpendGateError, match="run ledger"):
            run_mod._scratch_policy(str(bad))

    ok = run_mod._scratch_policy(str(tmp_path / "scratch-pool.jsonl"))
    assert ok.pool == "theoria-arm-scratch"
    assert ok.ledger_path == os.path.abspath(str(tmp_path / "scratch-pool.jsonl"))
    assert ok.usd_ceiling == 214.9, "a scratch pool keeps the tracked arithmetic"


def test_the_one_true_pool_is_the_default_expectation():
    """Read-only: names the tracked pool and writes nothing to it."""
    expected = spend_mod.one_true_pool()
    assert expected["pool"] == "theoria-shared-2026-07"
    assert expected["ledger_abspath"].endswith(
        os.path.join("proxy", "var", "spend_gate.jsonl"))
    fp = SpendGate().fingerprint()
    assert fp["pool"] == expected["pool"]
    assert os.path.abspath(fp["ledger_abspath"]) == expected["ledger_abspath"]
    assert ".worktrees" not in fp["ledger_abspath"], \
        "the pool must resolve against the main checkout, not this worktree"


# ------------------------------------------------------------ 6. 先算后花

def test_the_budget_is_computed_before_it_is_spent():
    """The arithmetic, worked, for the two shapes this arm actually runs."""
    twelve = spend_mod.plan_caps(actions=12, commands=2000,
                                 cost_ceiling_usd=20.0, require_headroom=False)
    # 36 fixed + ceil(12 x 9.3 x 2.0) = 36 + 224 = 260 outbound requests.
    # Was `3 + ceil(12 x 1.75 x 1.5) = 35 arm attempts; x3 = 105` until
    # 2026-07-29; `runs/20260729T004020Z-leg01` is that 105, and it bound at 9
    # of the 12 actions it was sized for. See `tests/test_cap_sizing.py` for why
    # the constants moved and `harness/spend.py:plan_caps` for the derivation.
    assert twelve.arithmetic["action_cap_planned"] == 260
    assert twelve.action_cap == 260
    assert twelve.usd_cap == 24.0                     # $20 ceiling + one call

    live = spend_mod.plan_caps(actions=120, commands=2000,
                               cost_ceiling_usd=20.0, require_headroom=False)
    # 36 + ceil(120 x 9.3 x 2.0) = 36 + 2232 = 2268
    assert live.action_cap == 2268
    assert live.arithmetic["action_cap_hard_bound"] == 6000


def test_the_command_ceiling_is_the_only_hard_bound():
    """`Budget.commands` raises before the (n+1)th attempt, so no run can exceed
    `commands x env_max_attempts` however badly the retries go."""
    caps = spend_mod.plan_caps(actions=500, commands=40, cost_ceiling_usd=1.0,
                               require_headroom=False)
    assert caps.arithmetic["arm_attempts_capped_by_commands_ceiling"] is True
    assert caps.action_cap == 40 * 3 == caps.arithmetic["action_cap_hard_bound"]


def test_an_offline_run_still_reserves_one_calls_ceiling():
    """`cost_ceiling_usd=None` is the offline dry run. It reserves a call's
    worth anyway: an offline run that unexpectedly reaches the desk must be
    refused by the pool, not merely by an `if`."""
    caps = spend_mod.plan_caps(actions=4, commands=100, cost_ceiling_usd=None,
                               require_headroom=False)
    assert caps.usd_cap == spend_mod.MODEL_CALL_CEILING_USD


def test_planning_refuses_when_the_pool_has_no_dollars_left(tmp_path):
    """Read from `totals()`, never a local counter: free = ceiling - spent -
    every other live reservation's unspent remainder. The middle term is the one
    INC-BA-003 did not have."""
    gate = SpendGate(_policy(tmp_path / "small.jsonl", usd_ceiling=10.0))
    other = gate.reserve("someone-elses-campaign", 8.0, 100)
    assert gate.totals().free_usd == 2.0

    with pytest.raises(spend_mod.InsufficientHeadroom) as exc:
        spend_mod.plan_caps(actions=12, commands=2000, cost_ceiling_usd=20.0,
                            gate=gate)
    assert "$24.0000 requested > $2.0000 free" in str(exc.value)
    assert exc.value.required["usd_cap"] == 24.0
    assert exc.value.totals["usd_held"] == 8.0
    assert "squeezes under the ceiling" in str(exc.value)

    # The refusal is about the *pool*, not about this run: the same arithmetic
    # passes once the other campaign hands its hold back and the level is one
    # the remaining ceiling can actually cover.
    gate.release(other, "test over")
    assert gate.totals().free_usd == 10.0
    ok = spend_mod.plan_caps(actions=12, commands=2000, cost_ceiling_usd=5.0,
                             gate=gate)
    assert ok.usd_cap == 9.0


def test_planning_refuses_when_the_pool_has_no_actions_left(tmp_path):
    gate = SpendGate(_policy(tmp_path / "small.jsonl", action_ceiling=100))
    gate.reserve("someone-elses-campaign", 0.0, 60)
    with pytest.raises(spend_mod.InsufficientHeadroom) as exc:
        spend_mod.plan_caps(actions=120, commands=2000, cost_ceiling_usd=1.0,
                            gate=gate)
    assert "2268 actions requested > 40 free" in str(exc.value)


# ------------------------------------------------------------------- the lease

def test_the_lease_outlives_the_declared_wall_clock():
    """An expired lease cannot be renewed, only re-reserved -- and re-reserving
    can fail because somebody took the headroom while this run was thinking. So
    the lease is sized up front rather than rescued mid-flight."""
    caps = spend_mod.plan_caps(actions=12, commands=2000, cost_ceiling_usd=1.0,
                               wall_clock_s=3 * 3600, require_headroom=False)
    assert caps.ttl_seconds == 3 * 3600 + spend_mod.TTL_MARGIN_S
    assert caps.ttl_seconds > 3600, "the policy default would lapse mid-run"


def test_the_heartbeat_renews_only_near_expiry(binding, pool):
    assert binding.heartbeat() is False
    binding.reservation.expires_epoch = \
        binding.reservation.expires_epoch - spend_mod.TTL_MAX_S
    assert binding.heartbeat() is True
    assert binding.renewals == 1
    assert [r["kind"] for r in records(pool)][-1] == "renew"


def test_a_desk_call_heartbeats_before_it_spends(binding, pool):
    """A desk call can block for 1800s. The renewal happens on the way in, not
    on the way out."""
    run = FakeRun()
    run.spend_binding = binding
    binding.reservation.expires_epoch -= spend_mod.TTL_MAX_S
    d = desk(run, envelope={"result": "t", "total_cost_usd": 0.1,
                            "usage": {"input_tokens": 1, "output_tokens": 1}})
    d.call("p", beat="theorize")
    kinds = [r["kind"] for r in records(pool)]
    assert kinds.index("renew") < kinds.index("spend")


# ------------------------------------- 10. the record the desk writes is canon
#
# Every test above this line drives the desk against `FakeRun`, whose
# `model_call` appends the keyword arguments to a list and validates nothing.
# That is a reasonable fake for testing the *gate*, and it is exactly why a
# defect in the *record* survived: `RunLedger.model_call` forwards `**extra`
# into `Ledger.append`, which runs `canon.check`, and `canon.MODEL_CALL_FIELDS`
# is a closed set of ten names. The desk was sending five that are not in it.
#
# The failure could not appear in a `--mock` run either, because `--mock` sets
# `offline=True` and skips theorize, so no test in this repo had ever driven a
# *completed* model call as far as a real ledger write.
#
# These two tests do that, against a real `Ledger` in a temp dir.

def _real_run_ledger(tmp_path, name="l.jsonl"):
    from proxy.ledger import Ledger, RunLedger        # noqa: PLC0415
    rl = RunLedger(Ledger(str(tmp_path / name)), "r-canon", "theoria",
                   game_id="g50t-5849a774")
    rl.run_start(game_id="g50t-5849a774")
    return rl


def test_a_completed_desk_call_writes_a_canonical_model_call(tmp_path, binding):
    """The regression. This is the whole of blocker A.

    On the code as it stood, this raised `NonCanonicalField` -- and it raised
    *after* `cli_cost_usd` had been incremented and after the charge had been
    settled against the shared pool. So a live run paid for the call, booked the
    money, and then died writing it down; on the first theorize call, and on
    every one after it.
    """
    rl = _real_run_ledger(tmp_path)
    d = desk(rl, spend=binding,
             envelope={"result": "a manual", "total_cost_usd": 0.25,
                       "subtype": "success",
                       "usage": {"input_tokens": 11, "output_tokens": 22}})

    out = d.call("prompt", beat="theorize", step_idx=3, label="round1")

    assert out == "a manual"
    assert d.calls == 1
    assert d.cli_cost_usd == 0.25


def test_the_desks_own_vocabulary_survives_inside_request(tmp_path, binding):
    """Moving the five fields must not lose them.

    `request` is passed verbatim by the ledger and is the one place this arm may
    add its own words, so beat/label/transport and the sealing provenance live
    there. A fix that made the record canonical by simply dropping the fields
    would pass the test above and quietly destroy the evidence that D-P8-002
    requires every call to carry.
    """
    from proxy.ledger import read_ledger              # noqa: PLC0415

    rl = _real_run_ledger(tmp_path, "l2.jsonl")
    d = desk(rl, spend=binding,
             envelope={"result": "x", "total_cost_usd": 0.1,
                       "subtype": "success",
                       "usage": {"input_tokens": 1, "output_tokens": 1}})
    d.call("prompt", beat="theorize", step_idx=7, label="round2")

    calls = [r for r in read_ledger(str(tmp_path / "l2.jsonl"))
             if r["event"] == "model_call"]
    assert len(calls) == 1
    request = calls[0]["request"]
    assert request["beat"] == "theorize"
    assert request["label"] == "round2"
    assert request["transport"] == "claude-code-cli"
    assert request["proxied"] is False
    assert "ANTHROPIC_API_KEY" in request["proxy_gap"]
    # step_idx stays top-level: it IS in the canonical set, and the cost curve
    # joins on it.
    assert calls[0]["step_idx"] == 7


# ------------------------------ 11. the game id may never reach the model
#
# `Theoria.md:353` seals four overfitting channels. The fourth -- the game's
# walkthrough may already be in the pre-training corpus -- cannot be closed,
# only reduced, and the reduction is a hard rule in those words: 硬规:游戏 ID
# 永不进模型上下文,全程匿名化.
#
# Before A3 that rule held by omission: nothing sanitised model-bound text, and
# `build_prompt` was clean only because nobody had wired an id in. An
# adversarial probe showed omission is not enough -- an engine traceback
# carrying an absolute path from a game-stemmed run directory put six
# occurrences of `g50t` inside a real 20,975-char prompt.

def test_a_prompt_carrying_the_game_id_is_never_sent(tmp_path, binding):
    """And it is refused *before* the subprocess, so it costs nothing."""
    from harness.modelcall import AnonymityBreach       # noqa: PLC0415

    rl = _real_run_ledger(tmp_path, "anon.jsonl")
    d = desk(rl, spend=binding,
             envelope={"result": "x", "total_cost_usd": 9.99,
                       "subtype": "success",
                       "usage": {"input_tokens": 1, "output_tokens": 1}})
    d.forbid_in_prompt = ("g50t-5849a774", "g50t")

    leaky = ("engine report: {'error': \"[Errno 13] Permission denied: "
             "'C:\\runs\\20260729T000000Z-g50t-leg01\\candidates.jsonl'\"}")
    with pytest.raises(AnonymityBreach) as caught:
        d.call(leaky, beat="theorize")

    assert "g50t" in str(caught.value)
    # Nothing was sent and nothing was billed: the refusal is before the seam.
    assert d.calls == 0
    assert d.cli_cost_usd == 0.0
    assert not spends(pool_of(binding))


def test_the_guard_does_not_fire_on_an_ordinary_prompt(tmp_path, binding):
    """The negative control. A guard that refuses everything proves nothing."""
    rl = _real_run_ledger(tmp_path, "anon2.jsonl")
    d = desk(rl, spend=binding,
             envelope={"result": "a manual", "total_cost_usd": 0.1,
                       "subtype": "success",
                       "usage": {"input_tokens": 1, "output_tokens": 1}})
    d.forbid_in_prompt = ("g50t-5849a774", "g50t")
    assert d.call("the frame is 64x64 and one object moved", beat="theorize")
    assert d.calls == 1


def pool_of(binding):
    """The gate behind a binding, for asserting nothing was charged."""
    return binding.gate


# ------------------------- 7. a raised call that still printed a price -------

def test_a_timeout_that_printed_its_price_is_priced_not_blinded(binding, pool):
    """The timeout is the dominant producer of blind rows, and it is also the
    case most likely to have printed one: the CLI runs with
    `--output-format json`, so a partial envelope carrying `total_cost_usd`
    may be sitting in the buffer when the clock runs out.

    The old code discarded `TimeoutExpired.stdout` outright, so the one call
    that most needed a price threw away the only evidence that could supply
    one -- and each such row then refuses every dollar in the shared pool, for
    every session, until a human files a correction by hand. Salvaging it is
    worth much more than the flag: `unpriced` is supposed to mean the recorded
    figure is not the measured one, and here it is measured.
    """
    from harness.modelcall import ModelError
    err = ModelError("claude -p timed out after 1800s")
    err.partial_stdout = json.dumps(
        {"total_cost_usd": 0.137, "result": "",
         "usage": {"input_tokens": 11, "output_tokens": 4096}})

    run = FakeRun()
    run.spend_binding = binding
    d = desk(run, raises=err)

    with pytest.raises(ModelError, match="timed out"):
        d.call("p", beat="theorize")

    last = spends(pool)[-1]
    assert last["unpriced"] is False and last["usd"] == 0.137
    assert last["detail"]["outcome"] == "raised_after_a_price"
    assert d.unpriced_calls == 0


def test_a_raised_call_that_printed_nothing_stays_blind(binding, pool):
    """The negative control, and the actual 2026-07-29 incident.

    That CLI printed nothing at all -- it raised 145ms after the previous call
    settled, with an empty stdout, having never reached the provider. Salvage
    must not invent a price for it: an empty buffer is not evidence of a free
    call, and settling one at $0.00 would let the provider decide afterwards
    whether it gets billed. Nothing to salvage stays nothing to salvage.
    """
    from harness.modelcall import ModelError
    err = ModelError("unparseable CLI output: ")
    err.partial_stdout = ""

    run = FakeRun()
    run.spend_binding = binding
    d = desk(run, raises=err)

    with pytest.raises(ModelError):
        d.call("p", beat="theorize")

    last = spends(pool)[-1]
    assert last["unpriced"] is True
    assert last["usd"] == spend_mod.MODEL_CALL_CEILING_USD
    assert last["detail"]["outcome"] == "raised_before_a_price"


def test_salvage_holds_partial_output_to_the_same_bar_as_a_whole_envelope(
        binding, pool):
    """A bare zero with no tokens behind it is the shape of a missing field,
    and `price_of` already refuses to settle one. Salvage reuses `price_of`
    rather than reimplementing the bar, so a truncated buffer cannot sneak a
    $0.00 settlement past a check a complete envelope would have failed.
    """
    from harness.modelcall import ModelError
    err = ModelError("claude -p timed out after 1800s")
    err.partial_stdout = json.dumps({"total_cost_usd": 0.0, "usage": {}})

    run = FakeRun()
    run.spend_binding = binding
    d = desk(run, raises=err)

    with pytest.raises(ModelError):
        d.call("p", beat="theorize")

    last = spends(pool)[-1]
    assert last["unpriced"] is True
    assert last["usd"] == spend_mod.MODEL_CALL_CEILING_USD


def test_salvage_survives_a_truncated_json_buffer(binding, pool):
    """Half a JSON document is the likeliest shape of a killed process's
    stdout. It must fall through to blind rather than raising out of the
    error path -- an exception thrown while handling an exception would lose
    the original failure and leave the pool unrecorded.
    """
    from harness.modelcall import ModelError
    err = ModelError("claude -p timed out after 1800s")
    err.partial_stdout = '{"total_cost_usd": 0.13, "usa'

    run = FakeRun()
    run.spend_binding = binding
    d = desk(run, raises=err)

    with pytest.raises(ModelError, match="timed out"):
        d.call("p", beat="theorize")

    assert spends(pool)[-1]["unpriced"] is True


# ------------------- 8. a test may not bill the pool the fleet shares --------

def test_reserving_against_the_tracked_pool_from_pytest_is_refused(caps):
    """The guard, tested from inside the thing it guards against.

    2 817 of the shared pool's 4 775 actions -- 59% -- were written by pytest:
    ten `...:pytest-*` campaigns over two days, from tests that called `play()`
    without a `spend_gate` and got the default, which is the real pool. Every
    one spent $0.00, so the dollar column stayed clean and nothing looked
    wrong; what was being consumed was the action ceiling, and a headroom
    number that is 59% fiction is not a margin.

    This test does what those did -- ask for the default gate while under
    pytest -- and requires a refusal. `_scratch_policy` is the escape and the
    other tests in this file use it.
    """
    from proxy.spend_gate import SpendGate             # noqa: PLC0415

    with pytest.raises(spend_mod.SpendGateError) as caught:
        spend_mod.open_binding("theoria-arm:test:g50t-5849a774:would-pollute",
                               caps, gate=SpendGate())

    assert "pytest" in str(caught.value)
    assert "scratch" in str(caught.value)


def test_the_guard_leaves_a_scratch_pool_alone(tmp_path, caps):
    """The negative control. A guard that also refuses the correct pattern
    would just be read as noise and routed around, which is how the original
    default came to be relied on.
    """
    gate = SpendGate(_policy(tmp_path / "scratch.jsonl"))
    binding = spend_mod.open_binding(
        "theoria-arm:test:g50t-5849a774:owns-its-pool", caps, gate=gate,
        expect_pool={"pool": gate.policy.pool,
                     "ledger_abspath": os.path.abspath(gate.ledger_path)})
    assert binding is not None
    binding.release("done")


# --------------------- 9. the ceiling has to actually be a ceiling -----------

def test_every_model_ceiling_covers_a_call_that_runs_to_the_timeout():
    """`proxy/cost.py:93`: "a ceiling that is sometimes too low is not a
    ceiling."

    The flat $4.00 failed that standard in the single scenario that uses it.
    The ceiling is what an unpriced call is charged, and a call becomes
    unpriced by raising -- of which the commonest cause is the 1800s timeout.
    At the observed opus-5 rate of $0.0028860/s a call that runs the full
    timeout costs $5.19, so the number charged for it was $1.19 short of the
    only case it existed to cover.

    Asserted as arithmetic rather than as a remembered figure, so that moving
    the timeout or re-measuring a rate re-checks the ceilings instead of
    silently invalidating them.

    **What this test does not do**, which is why the one below it exists: it
    reads `OBSERVED_USD_PER_SECOND` as given. A rate constant that is itself too
    low passes here and takes the ceiling down with it -- which is what happened
    to opus-5 (rate 17% low, ceiling $0.96 below its own rule, both green here).
    """
    for model, rate in spend_mod.OBSERVED_USD_PER_SECOND.items():
        implied = rate * spend_mod.MODEL_CALL_TIMEOUT_S
        ceiling = spend_mod.model_call_ceiling_for(model)
        assert ceiling >= implied, (
            "%s: ceiling $%.4f is below the $%.4f a call running the full "
            "%ds timeout would cost" % (model, ceiling, implied,
                                        spend_mod.MODEL_CALL_TIMEOUT_S))


def test_the_dated_model_id_the_cli_reports_resolves_to_a_ceiling():
    """The CLI reports `claude-haiku-4-5-20251001`; the price table carries
    only `claude-haiku-4-5`. That gap is why 5 797 recorded calls cannot be
    priced by `proxy/cost.py`. Fixing the table belongs to another track, but
    this arm must not inherit the gap: the dated id has to resolve here, and to
    the same number as the bare one.
    """
    assert (spend_mod.model_call_ceiling_for("claude-haiku-4-5-20251001")
            == spend_mod.model_call_ceiling_for("claude-haiku-4-5")
            == 1.25)
    # And an unknown model gets the most conservative number available, not the
    # cheapest: no measurement is the case to be most careful about.
    assert (spend_mod.model_call_ceiling_for("some-model-released-tomorrow")
            == max(spend_mod.MODEL_CALL_CEILINGS_USD.values()))


def _archive_worst_per_model():
    """Worst rate and worst call per model, re-derived from every desk log.

    Deliberately independent of `harness.spend`: it re-reads the archive rather
    than trusting the constants, because trusting the constants is the failure
    this exists to catch.
    """
    worst_rate, worst_call = {}, {}
    for path in glob.glob(os.path.join(_bootstrap.path("runs"), "*",
                                       "desk_log.json")):
        with open(path, encoding="utf-8") as handle:
            for record in json.load(handle):
                if not isinstance(record, dict) or "cli_cost_usd" not in record:
                    continue
                model = re.sub(r"-\d{8}$", "", record["model"])
                usd = float(record["cli_cost_usd"])
                secs = record["elapsed_ms"] / 1000.0
                worst_rate[model] = max(worst_rate.get(model, 0.0), usd / secs)
                worst_call[model] = max(worst_call.get(model, 0.0), usd)
    return worst_rate, worst_call


def test_the_ceiling_table_still_covers_the_archive():
    """Re-derive the sizing inputs from the logs; do not re-read the constants.

    The test above checks the ceilings against `OBSERVED_USD_PER_SECOND`. That
    catches a ceiling lowered under a correct rate, and nothing else -- a rate
    constant that is itself too low sails through it, and drags the ceiling down
    with it. Both happened at once on opus-5: the rate was taken as the worst
    *call* divided by its own duration (the dearest call is a long one, so that
    ratio is middling; the costliest second belongs to a shorter call), which
    read 17% low, and the ceiling was set to $5.00 while `4 x $1.489011 = $5.96`
    was already the binding half of the documented rule. Every existing test was
    green throughout.

    So this one goes back to the archive for both maximands. It is the only
    check here that would have failed before the correction.
    """
    worst_rate, worst_call = _archive_worst_per_model()
    assert worst_rate, "no desk logs in the archive: this test checked nothing"

    for model, rate in sorted(worst_rate.items()):
        recorded = spend_mod.OBSERVED_USD_PER_SECOND.get(model)
        assert recorded is not None, (
            "%s appears in the archive with no recorded rate" % model)
        assert recorded >= rate, (
            "%s: the recorded rate $%.7f/s is below the worst rate in the "
            "archive, $%.7f/s. A rate that understates makes every ceiling "
            "derived from it understate too." % (model, recorded, rate))

        implied = max(rate * spend_mod.MODEL_CALL_TIMEOUT_S,
                      4 * worst_call[model])
        ceiling = spend_mod.model_call_ceiling_for(model)
        assert ceiling >= implied, (
            "%s: ceiling $%.2f is below $%.4f, which is what this table's own "
            "stated rule -- max(timeout x rate, 4x worst call) -- produces from "
            "the archive." % (model, ceiling, implied))


def test_a_haiku_call_that_goes_unpriced_is_not_charged_the_opus_ceiling(
        binding, pool):
    """The row that blocked the whole fleet, as a test.

    seq 7418 is a haiku call booked at $4.00 -- 27x its own settled siblings in
    the same run ($0.114256 / $0.146292 / $0.132608). `price_unpriced` can only
    add, so that overstatement is permanent. Charging the right tier is the
    only point at which it can be prevented.
    """
    run = FakeRun()
    run.spend_binding = binding
    d = desk(run, raises=ModelError("claude -p timed out after 1800s"))
    d.model = "claude-haiku-4-5-20251001"

    with pytest.raises(ModelError):
        d.call("p", beat="theorize")

    last = spends(pool)[-1]
    assert last["unpriced"] is True
    assert last["usd"] == 1.25, "a haiku call must not be charged opus money"
    assert last["usd"] < 4.00
