"""What an adversarial pass got through, and what now stops it.

Every test here is a bypass that was demonstrated against the wired gate before
these fixes existed. They are kept as tests rather than as notes because the
next person to touch the pricing path will not have read the review.

    cd proxy && python -m pytest tests/test_spend_gate_egress.py
"""

import json

import pytest

from proxy.cost import PriceTable


TABLE = PriceTable({
    "table": "test-prices",
    "models": {"priced-model": {"input": 3.0, "output": 15.0},
               "free-model": {"input": 0.0, "output": 0.0}},
    "cache_multipliers": {"cache_read_input_tokens": 0.1,
                          "cache_creation_input_tokens": 1.25},
})


def body(**over):
    out = {"model": "priced-model", "max_tokens": 1000,
           "messages": [{"role": "user", "content": "hi"}]}
    out.update(over)
    return out


# -- the pre-flight ceiling exists at all ------------------------------------

def test_a_call_has_a_computable_ceiling_before_the_socket_opens():
    """`cost()` prices a call after the fact, which is the only way to know
    what it really cost and therefore useless as a gate: one call put $600
    through a $10 ceiling because the money was checked only after it left."""
    ceiling = TABLE.ceiling_for(body())
    assert ceiling["usd"] > 0
    # max_tokens is the load-bearing term: 1000 output tokens at $15/M.
    assert ceiling["usd"] >= 1000 * 15.0 / 1_000_000


def test_the_ceiling_grows_with_max_tokens():
    small = TABLE.ceiling_for(body(max_tokens=10))["usd"]
    large = TABLE.ceiling_for(body(max_tokens=100_000))["usd"]
    assert large > small * 100


def test_an_unknown_model_has_no_ceiling_rather_than_a_zero_one():
    """The unpriced hole: any model released after the price table was written,
    or any typo in the arm's body, was previously free and silent."""
    assert TABLE.ceiling_for(body(model="claude-does-not-exist-9"))["usd"] is None


def test_a_request_without_max_tokens_has_no_ceiling():
    out = TABLE.ceiling_for({"model": "priced-model"})
    assert out["usd"] is None and "max_tokens" in out["why"]


def test_a_non_object_body_has_no_ceiling():
    assert TABLE.ceiling_for(b"not json")["usd"] is None
    assert TABLE.ceiling_for(None)["usd"] is None


def test_a_free_model_still_has_a_ceiling_and_it_is_zero():
    """A ceiling of $0.00 is a ceiling. Only an *absent* one is a refusal."""
    assert TABLE.ceiling_for(body(model="free-model"))["usd"] == 0.0


def test_the_ceiling_is_pessimistic_about_the_input_side():
    """It is a ceiling; one that is sometimes too low is not one."""
    long_body = body(messages=[{"role": "user", "content": "x" * 30_000}])
    ceiling = TABLE.ceiling_for(long_body)
    real = TABLE.cost("priced-model",
                      {"input_tokens": 30_000 // 4, "output_tokens": 1000})
    assert ceiling["usd"] >= real["usd"]


# -- the response no longer decides whether the call is billed --------------

def priced_ok(usage):
    """Is this usage block one the proxy will trust instead of the ceiling?"""
    required = ("input_tokens", "output_tokens")
    return isinstance(usage, dict) and all(k in usage for k in required)


def test_a_missing_usage_block_is_not_a_free_call():
    assert not priced_ok(None)
    assert not priced_ok({})


def test_a_typod_usage_key_is_not_a_free_call():
    assert not priced_ok({"input_token": 10, "output_token": 10})


def test_a_truncated_stream_is_not_a_cheap_call():
    """`input_tokens` arrives in `message_start`, `output_tokens` only in
    `message_delta`. A stream cut in between yields a plausible, positive, badly
    wrong figure that misses the expensive half at 5x the input rate."""
    assert not priced_ok({"input_tokens": 100_000})


def test_a_complete_usage_block_is_trusted():
    """The negative control: this must not reject everything."""
    assert priced_ok({"input_tokens": 10, "output_tokens": 20})


def test_a_zero_cost_model_with_full_usage_is_priced_not_blind():
    """Flagging a legitimately free call as unpriced would jam the pool on
    nothing -- the same over-broad blindness that D-027 records."""
    usage = {"input_tokens": 10, "output_tokens": 20}
    assert priced_ok(usage)
    assert TABLE.cost("free-model", usage)["usd"] == 0.0


def test_a_usage_value_that_int_rejects_does_not_erase_the_call():
    """`json.loads` accepts `1e999` and `"1e5"`; `int()` does not. Five real
    calls produced zero ledger rows, indefinitely repeatable."""
    with pytest.raises(Exception):
        TABLE.cost("priced-model", {"input_tokens": float("inf")})
    # The proxy catches that and charges the ceiling instead -- the point is
    # only that the raise is real and must not be allowed to skip the record.


# -- leaked holds: fail-closed is not an excuse for an unusable pool --------

def _pool(tmp_path, name="pool.jsonl", **over):
    from proxy.spend_gate import SpendGate, SpendPolicy
    spec = {"v": "1.0", "pool": "p", "usd_ceiling": 10.0, "action_ceiling": 100,
            "ledger": str(tmp_path / name), "default_ttl_seconds": 3600,
            "default_run_caps": {"usd": 5.0, "actions": 50}}
    spec.update(over)
    return SpendGate(SpendPolicy(spec, source=None))


def test_a_crashed_run_does_not_strand_the_pools_headroom(tmp_path,
                                                          monkeypatch):
    """43 crashed runs took the shared pool offline for the full TTL with
    nothing actually spent. Fail-closed, but the recovery was to wait an hour --
    which is not a recovery anyone accepts twice.

    S29 rewrote this test because it was vacuous twice over, and both vacuities
    pointed the same way -- green.

    (1) `_run_game` was monkeypatched to raise *immediately*, so no reservation
        was ever taken. `held_usd == 0.0` was therefore true before the cleanup
        code existed, and stayed true no matter what that code did. A test for
        "the crash cleanup gives the headroom back" that never puts any
        headroom out.
    (2) It passed `run_id="r-crash"`, which no ordinary caller passes -- the id
        used to be minted inside `_run_game`. So the one input that decided
        whether the ownership filter ran at all was supplied only by the test.

    The fake now does what the real `_run_game` does before it dies: reserve,
    with the same `holder` shape, using the run id it was handed.
    """
    from proxy import runner

    gate = _pool(tmp_path)
    taken = {}

    def reserve_then_die(game_id, **k):
        # `k.get(...) or`, not `k[...]`: before the fix nothing put a run id in
        # kwargs, and a KeyError here would fail this test for the wrong
        # reason -- it would never reach the claim it is supposed to be about.
        res = gate.reserve("c-crash", 5.0, 50,
                           holder={"run_id": k.get("run_id") or "r-minted-low",
                                   "arm": "mock_arm", "game_id": game_id})
        taken["id"] = res.reservation_id
        raise RuntimeError("the arm died mid-run")
    monkeypatch.setattr(runner, "_run_game", reserve_then_die)

    # No `run_id=` here on purpose: this is the shape a real caller uses, and
    # it is the shape the old filter could not see.
    with pytest.raises(RuntimeError):
        runner.run_game("ar25-0c556536", spend_gate=gate)

    assert taken["id"], "the fake must actually claim headroom, or this is (1)"
    assert gate.totals().held_usd == 0.0
    assert gate.totals().free_usd == 10.0


def test_crash_cleanup_releases_only_the_crashing_runs_own_claim(tmp_path,
                                                                 monkeypatch):
    """The negative sample for S29's third defect: two sessions, one crash.

    `run_game`'s cleanup compares the live set against a snapshot taken before
    the run, and releases everything new. The ownership filter that was meant
    to narrow that to *this* run's claim read

        holder.run_id != kwargs.get("run_id") and kwargs.get("run_id") is not None

    with the id minted one level down, so the second conjunct was always False
    and the `continue` never fired. A crash therefore released every claim that
    appeared in the shared pool while it was alive. `release` validated
    nothing, so the other session's headroom went back to the pool and the
    ledger recorded `run ended without releasing its claim` against it -- a line
    that reads exactly like the thing the cleanup was written to do.

    The other session's claim is taken *after* the snapshot, which is what makes
    it indistinguishable from the crashing run's own by timing alone.
    """
    from proxy import runner

    gate = _pool(tmp_path)
    other = {}

    def other_session_claims_then_we_die(game_id, **k):
        # A different session, mid-run, on the same shared pool.
        other["res"] = gate.reserve("c-other", 3.0, 10,
                                    holder={"run_id": "r-other-session",
                                            "arm": "mock_arm",
                                            "game_id": game_id})
        # See the note in the test above on `k.get(...) or`: before the fix the
        # id was minted a level down and never reached kwargs, which is the
        # defect itself -- so the fake stands in for that lower level.
        gate.reserve("c-mine", 2.0, 10,
                     holder={"run_id": k.get("run_id") or "r-minted-low",
                             "arm": "mock_arm", "game_id": game_id})
        raise RuntimeError("the arm died mid-run")
    monkeypatch.setattr(runner, "_run_game", other_session_claims_then_we_die)

    with pytest.raises(RuntimeError):
        runner.run_game("ar25-0c556536", spend_gate=gate)

    live = {r["reservation_id"]: r for r in gate.totals().live}
    assert other["res"].reservation_id in live, (
        "the crashing run released a claim it did not hold")
    # Its own is gone, so this is not passing by doing nothing at all.
    assert len(live) == 1
    assert gate.totals().held_usd == 3.0


def test_release_refuses_a_claim_the_caller_does_not_hold(tmp_path):
    """`release` used to append a record for any id at all, without looking.

    Two consequences, and the second is the one that bites: an id that matches
    no claim was a silent no-op that still wrote a line reading like a
    successful release, and an id belonging to someone else was honoured.
    """
    from proxy.spend_gate import NoReservation

    gate = _pool(tmp_path)
    res = gate.reserve("c", 1.0, 5, holder={"run_id": "r-owner"})

    class _H:
        def __init__(self, rid, campaign):
            self.reservation_id, self.campaign = rid, campaign

    with pytest.raises(NoReservation):
        gate.release(_H("res-never-existed", "c"), reason="typo")
    with pytest.raises(NoReservation):
        gate.release(_H(res.reservation_id, "c"),
                     expect_holder={"run_id": "r-someone-else"})
    # The claim is untouched by either refusal.
    assert gate.totals().held_usd == 1.0
    gate.release(_H(res.reservation_id, "c"),
                 expect_holder={"run_id": "r-owner"})
    assert gate.totals().held_usd == 0.0


def test_a_policy_with_a_non_finite_ceiling_refuses_to_load(tmp_path):
    """The negative sample for S29's second defect.

    `finite()` has been in this module all along, with a docstring explaining
    that NaN voids every later comparison -- and it was applied to every amount
    a caller passes in and to none of the policy's own fields. `usd_ceiling <= 0`
    is False for both NaN and +inf, so the constructor waved them through, and
    `check` / `reserve` / `_first_breach` then compared against a ceiling no
    total could ever reach. `verify_spend.sh`'s dedicated "the pool policy is
    readable and has a ceiling" check printed `inf` and exited 0.
    """
    from proxy.spend_gate import SpendGateUnavailable

    for bad in (float("nan"), float("inf"), float("-inf")):
        with pytest.raises(SpendGateUnavailable):
            _pool(tmp_path, usd_ceiling=bad)
        # `default_run_caps.usd` is the same hole by another route: it is what a
        # run declaring no budget of its own is given.
        with pytest.raises(SpendGateUnavailable):
            _pool(tmp_path, default_run_caps={"usd": bad, "actions": 50})


def test_the_standalone_proxies_release_what_they_claimed():
    """Both documented CLIs took a default reservation in the config and then
    called `serve_forever()` directly, so nothing ever released it."""
    import inspect
    from proxy import env_proxy, model_proxy
    for module in (env_proxy, model_proxy):
        source = inspect.getsource(module.main)
        assert "spend_reservation_owned" in source, module.__name__
        assert "release" in source, module.__name__
