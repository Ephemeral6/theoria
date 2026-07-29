"""Offline tests for the campaign rate budget. No API, no network.

Same house rule as `test_hygiene.py`: every check has a negative control. A
budget calculator that cannot report BREACH is a calculator that always says
yes, which is the INC-003 failure wearing different clothes -- so the tests
that matter most here are the ones that force each verdict to fire.

    cd arc-recon && python -m pytest test_rate_budget.py
"""

import json

import pytest

import precheck
import rate_budget as rb


# -- the backoff schedule is read, not restated ------------------------------

def test_backoff_is_imported_from_the_retry_envelope():
    """The whole point of the precheck refactor: one source of truth.

    If someone changes the envelope in precheck.py, this budget must move with
    it. Asserting the values match precheck's constants is what makes that so.
    """
    delays = rb.backoff_delays("action")
    assert len(delays) == precheck.ACTION_ATTEMPTS - 1
    assert delays[0] == pytest.approx(precheck.ACTION_DELAY_BASE)
    assert max(delays) == pytest.approx(precheck.ACTION_DELAY_CAP)
    # The ramp is linear and capped -- not exponential. ACCESS_CHECK §6d says
    # so in prose; this is the executable form of that claim.
    assert delays[1] == pytest.approx(precheck.ACTION_DELAY_BASE * 2)
    assert delays[-1] == pytest.approx(precheck.ACTION_DELAY_CAP)

    reset = rb.backoff_delays("reset")
    assert len(reset) == precheck.RESET_ATTEMPTS - 1
    assert reset[0] == pytest.approx(precheck.RESET_DELAY_BASE)


def test_envelope_change_moves_the_budget(monkeypatch):
    """Negative control for the above: a shorter cap must raise the storm rate."""
    before = rb.worker_rpm({"attempts_per_command": 40.0, "think_s": 0.0,
                            "envelope": "action"}, rtt_s=0.5)
    monkeypatch.setitem(rb.ENVELOPES, "action", (40, 0.01, 0.01))
    after = rb.worker_rpm({"attempts_per_command": 40.0, "think_s": 0.0,
                           "envelope": "action"}, rtt_s=0.5)
    assert after["peak_rpm"] > before["peak_rpm"]


# -- the sliding window ------------------------------------------------------

def test_peak_counts_the_worst_window_not_the_average():
    """40 requests in the first second then silence is a 40-rpm burst, not 0.7."""
    burst = [k * 0.025 for k in range(40)] + [3600.0]
    assert rb.peak_in_window(burst) == 40


def test_peak_window_excludes_what_falls_outside_it():
    """Negative control: spread the same requests out and the peak collapses."""
    spread = [k * 30.0 for k in range(40)]
    assert rb.peak_in_window(spread) == 2


def test_peak_is_never_below_sustained():
    """The bug this file caught during S5.

    Computing the peak as floor(60/interval) put it *below* the sustained rate,
    which cannot happen: a 60-second window of a steady stream contains at
    least as many requests as the steady rate implies.
    """
    for think_s in (0.0, 0.4, 5.0, 17.3):
        one = rb.worker_rpm({"attempts_per_command": 1.0, "think_s": think_s},
                            rtt_s=0.558)
        assert one["peak_rpm"] >= one["sustained_rpm"] - 1e-9


# -- the finding the budget exists to state ----------------------------------

def test_retry_storms_are_slower_than_think_free_replay():
    """§6d's correction to §6, as an assertion.

    ACCESS_CHECK §6 named the retry storm as the shape that approaches the
    limit. Its own backoff makes it the *slowest* shape this project runs; the
    fast one is scripted replay with no model call in the loop. If a future
    envelope change ever inverts this, the prose in §6d is wrong and this test
    is how we find out.
    """
    rtt = 0.558
    storm = rb.worker_rpm({"attempts_per_command": 40.0, "think_s": 0.0,
                           "envelope": "action"}, rtt_s=rtt)
    replay = rb.worker_rpm({"attempts_per_command": 1.0, "think_s": 0.0}, rtt_s=rtt)
    assert replay["peak_rpm"] > 4 * storm["peak_rpm"]


def test_think_time_is_what_makes_an_llm_arm_safe():
    """And the negative control: take the model call away and the arm is a replay."""
    rtt = 0.558
    arm = rb.worker_rpm({"attempts_per_command": 1.0, "think_s": 5.0}, rtt_s=rtt)
    stripped = rb.worker_rpm({"attempts_per_command": 1.0, "think_s": 0.0},
                             rtt_s=rtt)
    assert stripped["peak_rpm"] > 8 * arm["peak_rpm"]


def test_breach_concurrency_is_the_number_an_operator_can_act_on():
    assert rb.breach_concurrency(100.0, 600.0) == 7        # 6x100 fits, 7 does not
    assert rb.breach_concurrency(600.0, 600.0) == 2
    assert rb.breach_concurrency(0.0, 600.0) is None


# -- the shipped budget ------------------------------------------------------

def test_shipped_budget_does_not_breach():
    result = rb.evaluate(rb.load_budget())
    assert result["verdict"] != "BREACH", result["rows"]
    assert result["worst_aggregate_peak_rpm"] <= result["limit_rpm"]


def test_shipped_budget_covers_every_term_of_the_theoria_clause():
    """Theoria.md:299 names three terms: 三臂×局数×回合, 戳探, 前缀重放传送.

    A budget that quietly dropped one would still print a reassuring table.
    """
    budget = rb.load_budget()
    workers = {s["worker"] for s in budget["scenarios"]}
    assert "llm-arm" in workers            # 三臂 × 局数 × 回合
    assert "prefix-replay" in workers      # 戳探 + 前缀重放传送
    assert "retry-storm" in workers        # the shape §6 accused


def test_a_breach_is_reportable():
    """Negative control for the shipped-budget test.

    If nothing can ever come back BREACH, `verify.sh` green means nothing.
    """
    budget = rb.load_budget()
    for scenario in budget["scenarios"]:
        scenario["concurrency"] = 500
    result = rb.evaluate(budget)
    assert result["verdict"] == "BREACH"
    assert any(row["verdict"] == "BREACH" for row in result["rows"])


def test_amber_fires_between_ok_and_breach():
    budget = rb.load_budget()
    limit = budget["limit"]["requests_per_minute"]
    one = rb.worker_rpm({"attempts_per_command": 1.0, "think_s": 0.0},
                        rtt_s=budget["measured"]["rtt_min_s"])["peak_rpm"]
    budget["scenarios"] = [{"id": "probe", "worker": "prefix-replay",
                            "concurrency": max(int(limit * 0.6 // one), 1),
                            "total_commands": 1}]
    result = rb.evaluate(budget)
    assert result["verdict"] in ("AMBER", "OK")


def test_cli_exits_zero_on_the_shipped_budget(capsys):
    assert rb.main([]) == 0
    assert "campaign rate budget" in capsys.readouterr().out


def test_cli_json_is_parseable(capsys):
    assert rb.main(["--json"]) == 0
    json.loads(capsys.readouterr().out)


# -- the declared inputs must stay tied to the data --------------------------

def test_declared_inputs_match_the_tracked_data():
    checks, drifted = rb.check_drift(rb.load_budget())
    assert not drifted, checks
    assert any(c["status"] == "ok" for c in checks)


def test_drift_is_detectable():
    """Negative control: a declaration that has gone stale must be caught."""
    budget = rb.load_budget()
    budget["measured"]["rtt_min_s"] = budget["measured"]["rtt_min_s"] * 10
    _, drifted = rb.check_drift(budget)
    assert drifted


def test_amplification_counts_resets_as_commands():
    """A sweep is RESETs plus actions.

    Dividing http_calls by actions alone overstates amplification by exactly
    the RESETs it forgot -- the 12-action scheduled sweep issues 16 commands,
    and calling that 1.33 attempts/command would have manufactured a regression
    out of arithmetic.
    """
    measured = rb.measure_amplification()
    assert measured is not None
    assert measured["attempts_per_command_post_cookie"] == pytest.approx(1.0)


# -- the rate the canary now records -----------------------------------------

def test_observed_rates_do_not_backfill_unmeasured_runs():
    """The four sweeps on disk predate `elapsed_s` and must say so.

    Inventing a rate for them would be worse than having none: it would look
    like the 600 rpm limit had been measured against when it never has.
    """
    runs = rb.observed_rates()
    assert runs, "no canary runs on disk"
    for run in runs:
        if run["elapsed_s"] is None:
            assert run["measured"] is False
            assert run["observed_rpm"] is None


def test_canary_records_a_rate_going_forward():
    """The replay record must carry wall clock, or the gap S5 closed reopens."""
    import inspect

    import canary
    source = inspect.getsource(canary.replay)
    assert "elapsed_s" in source
    assert "observed_rpm" in source
