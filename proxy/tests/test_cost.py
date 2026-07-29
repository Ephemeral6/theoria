""""Not measured" and "measured, and it was zero" are different facts.

S29 found them sharing one literal in `proxy/cost.py`. The module already had an
unpriced mechanism -- `usd: None` plus a reason -- and it fired only when the
*model* was unknown, never when the *measurement* was missing. So:

  * `usage == {}` walked the fully-priced branch and came back as a well-formed
    zero. `price_run` added $0.00, incremented `calls`, and reported
    `unpriced_models: null` -- a positive assertion that nothing had been
    missed.
  * A block holding only `input_tokens` came back with a positive, plausible
    price and silently dropped the output side, which every model in
    `pricing_v1.json` bills at exactly five times the input rate. That is the
    shape an SSE stream produces when it is cut between `message_start` and
    `message_delta`, and it is the dangerous one: a zero gets noticed, a
    number that is 83% too low does not.

`proxy/model_proxy.py` had guarded its own call site against both since the
truncated-stream finding. It guarded the socket, not the conversion, so every
after-the-fact re-pricing path -- `price_run`, `proxy/reconcile.py`,
`theoria-arm/armtools/archive.py`, and the bill-shape figure downstream of them
-- re-derived history without the rule.

    cd proxy && python -m pytest tests/test_cost.py
"""

import pytest

from proxy.cost import REQUIRED_USAGE_KEYS, PriceTable, price_run


TABLE = PriceTable.load()          # pricing_v1, the table actually in force
MODEL = "claude-opus-5"            # $5.00 in, $25.00 out, per million


def call(usage, model=MODEL):
    return {"event": "model_call", "model": model, "usage": usage}


# -- a missing measurement is a refusal, not a zero -------------------------

def test_an_empty_usage_block_has_no_price_rather_than_a_price_of_zero():
    """The negative sample the board item asks for. Before the fix this
    returned `{"usd": 0.0, "lines": {"input_tokens": 0.0, "output_tokens":
    0.0}}` -- a well-formed zero, indistinguishable from a call that really
    did cost nothing."""
    out = TABLE.cost(MODEL, {})
    assert out["usd"] is None
    assert out["missing_usage_keys"] == ["input_tokens", "output_tokens"]
    # The reason travels with the refusal: `model_proxy.py` puts it in the
    # ledger's `why` field, and a reason of "" is how a blind call gets filed
    # as a boring one.
    assert "never measured" in out["unpriced"]


def test_a_truncated_stream_is_not_a_call_that_only_used_input():
    """The dangerous half. `input_tokens` arrives in `message_start`,
    `output_tokens` only in `message_delta`; a stream cut in between used to
    price to a positive, plausible, badly wrong figure. 100k input tokens
    against opus-5 came back as $0.50 and looked like a real bill -- while the
    output side it dropped is billed at 5x the input rate."""
    out = TABLE.cost(MODEL, {"input_tokens": 100_000})
    assert out["usd"] is None
    assert out["missing_usage_keys"] == ["output_tokens"]
    # What the old code would have said, spelled out so the number is on the
    # record: $0.50, with no channel of any kind reporting that the expensive
    # half of the bill was never seen.
    assert 100_000 * 5.0 / 1_000_000 == 0.5
    assert TABLE.models[MODEL]["output"] == 5 * TABLE.models[MODEL]["input"]


def test_an_explicit_null_counts_as_missing_and_not_as_zero():
    """`int(None or 0)` reads a provider's `"output_tokens": null` as zero,
    which is why the check is `is None` and not `key in usage`. One notch
    stricter than `model_proxy.py`'s test, deliberately."""
    assert TABLE.cost(MODEL, {"input_tokens": 10, "output_tokens": None})["usd"] is None
    assert TABLE.cost(MODEL, {"input_tokens": None, "output_tokens": 10})["usd"] is None


def test_only_the_two_halves_of_the_bill_are_required():
    """Cache keys are genuinely optional -- their absence means no cache was
    used, which is a measurement. Requiring them would jam the pool on nothing,
    the over-broad blindness D-027 records."""
    assert REQUIRED_USAGE_KEYS == ("input_tokens", "output_tokens")
    assert TABLE.cost(MODEL, {"input_tokens": 10, "output_tokens": 20})["usd"] > 0


# -- the positive control: the fix must not swallow real zeros --------------

def test_a_measured_zero_is_still_a_price():
    """The whole point is that these two are now distinguishable. A complete
    usage block of zeroes is *measured*; it prices to $0.00 and reports no
    hole. If this ever fails the fix has become the bug it replaced."""
    out = TABLE.cost(MODEL, {"input_tokens": 0, "output_tokens": 0})
    assert out["usd"] == 0.0
    assert out.get("missing_usage_keys") is None


def test_a_free_model_with_a_full_usage_block_is_priced_not_blind():
    out = TABLE.cost("mock-model-1", {"input_tokens": 10, "output_tokens": 20})
    assert out["usd"] == 0.0 and out.get("missing_usage_keys") is None


def test_a_complete_block_still_prices_every_line_it_used_to():
    """Regression guard on the branch the new rule sits in front of."""
    out = TABLE.cost(MODEL, {"input_tokens": 1_000_000,
                             "output_tokens": 1_000_000,
                             "cache_read_input_tokens": 1_000_000})
    assert out["usd"] == pytest.approx(5.0 + 25.0 + 0.5)


# -- the fact has to reach a reader ----------------------------------------

def test_price_run_does_not_count_an_unmeasured_call_as_a_priced_one():
    """`unpriced_models: null` used to be printed over a run containing a call
    with no usage at all, and `model_calls` counted it. Both were positive
    assertions that nothing had been missed."""
    report = price_run([call({"input_tokens": 1_000_000, "output_tokens": 0}),
                        call({})], TABLE)
    assert report["usd_total"] == 5.0          # one real call, unchanged
    assert report["model_calls"] == 1          # the blind one is not a call
    assert report["unmeasured_calls"] == 1
    assert report["missing_usage_keys"] == ["input_tokens", "output_tokens"]


def test_an_unmeasured_call_is_not_filed_under_unpriced_models():
    """A true fact under a false heading. `claude-opus-5` is in
    `pricing_v1.json`; the run's hole is the measurement, and saying "model is
    not in the table" would send the next reader to fix the wrong file."""
    report = price_run([call({"input_tokens": 5})], TABLE)
    assert report["unpriced_models"] is None
    assert report["unmeasured_calls"] == 1
    assert report["missing_usage_keys"] == ["output_tokens"]
    assert report["usd_total"] == 0.0


def test_an_unknown_model_still_lands_in_unpriced_models():
    """The other direction of the same split -- the pre-existing channel must
    keep working. This id is real and is the only one in the repo with no row
    in the table (it is the dated alias of `claude-haiku-4-5`)."""
    report = price_run([call({}, model="claude-haiku-4-5-20251001")], TABLE)
    assert report["unpriced_models"] == ["claude-haiku-4-5-20251001"]
    assert report["unmeasured_calls"] == 0     # the model is why, not the usage


def test_price_run_reports_the_usage_keys_it_cannot_price():
    """`cost()` has always computed `unpriced_usage_keys` and `price_run` threw
    it away, so the only consumer that ever saw it was `armtools/archive.py`,
    which got it by calling `cost()` a second time itself. A signal no report
    prints is the same defect one layer up."""
    report = price_run([call({"input_tokens": 10, "output_tokens": 20,
                              "reasoning_tokens": 999})], TABLE)
    assert report["unpriced_usage_keys"] == ["reasoning_tokens"]
    assert report["usd_total"] > 0             # a lower bound, and it says so


def test_the_three_holes_stay_three_holes():
    """Collapsing any two of these back together is the S29 defect returning.
    One run, one of each: an unknown model, a priced model never measured, and
    a measured call carrying a key with no rate."""
    report = price_run([call({}, model="no-such-model-9"),
                        call({"input_tokens": 7}),
                        call({"input_tokens": 10, "output_tokens": 20,
                              "reasoning_tokens": 3})], TABLE)
    assert report["unpriced_models"] == ["no-such-model-9"]
    assert report["unmeasured_calls"] == 1
    assert report["missing_usage_keys"] == ["output_tokens"]
    assert report["unpriced_usage_keys"] == ["reasoning_tokens"]
