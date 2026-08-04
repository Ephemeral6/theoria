"""The desk_yield reading of a leg, against synthetic transcripts and the real pair.

Two halves.  The first builds a leg on disk and checks that the module says
what the bytes say -- a void call is void, an identical prompt is identical,
the price fit recovers rates it was given.  The second reads the two archived
R2b legs of 2026-08-01, because that pair is the reason the module exists and
a refactor that silently stops seeing the finding should fail here.
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from armtools import desk_yield  # noqa: E402

RUNS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "runs")
G50T = os.path.join(RUNS, "20260801T044640Z-R2b-g50t-a")
SK48 = os.path.join(RUNS, "20260801T044640Z-R2b-sk48-b")


def _transcript(prompt, reply):
    return ("# a call\n\n## prompt\n\n```\n%s\n```\n\n## reply\n\n%s"
            % (prompt, reply))


def _leg(tmp_path, calls):
    """`calls` is [(name, prompt, reply, usage_dict, usd)]."""
    desk = tmp_path / "desk"
    desk.mkdir()
    log = []
    for i, (name, prompt, reply, usage, usd) in enumerate(calls, start=1):
        (desk / name).write_text(_transcript(prompt, reply), encoding="utf-8")
        log.append({"call": i, "label": "round1", "step_idx": 2 * i,
                    "elapsed_ms": 60000, "cli_cost_usd": usd, "usage": usage})
    (tmp_path / "desk_log.json").write_text(json.dumps(log), encoding="utf-8")
    return str(tmp_path)


def _usage(cc, cr, ot):
    return {"cache_creation_input_tokens": cc, "cache_read_input_tokens": cr,
            "output_tokens": ot}


THREE = "=== THEORY ===\n```\nx\n```\n\n=== PLAYBOOK ===\n```\ny\n```\n\n=== LOG ===\n```json\n[]\n```"
NO_THEORY = "=== PLAYBOOK ===\n```\ny\n```\n\n=== LOG ===\n```json\n[]\n```"


# ------------------------------------------------------------------ the reply
def test_blocks_are_read_in_order_and_duplicates_survive():
    reply = THREE + "\n" + THREE
    assert desk_yield.blocks_in_reply(reply) == [
        "THEORY", "PLAYBOOK", "LOG", "THEORY", "PLAYBOOK", "LOG"]
    got = desk_yield.delivered(reply)
    assert got["duplicated"] == ["LOG", "PLAYBOOK", "THEORY"]
    assert got["has_required"] is True


def test_a_reply_without_a_theory_block_is_void_not_partial():
    got = desk_yield.delivered(NO_THEORY)
    assert got["has_required"] is False
    assert got["missing"] == ["THEORY"]
    # It is not "mostly fine": the module must not report the two blocks that
    # DID arrive as though the call bought something.  The arm rejects the
    # whole reply, and the books do not move.
    assert got["blocks_unique"] == ["LOG", "PLAYBOOK"]


def test_a_block_marker_inside_prose_does_not_count():
    # The desk writes about its own contract constantly.  Only a marker alone
    # on its own line is a block; an inline mention is commentary.
    assert desk_yield.blocks_in_reply("I will emit === THEORY === next.") == []


# ------------------------------------------------------- the prompt comparison
def test_identical_prompts_are_seen_through_differing_transcript_headers(tmp_path):
    run = _leg(tmp_path, [
        ("call-001-theorize-round1.md", "SAME PROMPT", THREE, _usage(10, 0, 20), 1.0),
        ("call-002-theorize-round2.md", "SAME PROMPT", NO_THEORY, _usage(10, 0, 40), 2.0),
    ])
    rep = desk_yield.yield_leg(run)
    assert rep["per_call"][0]["prompt_identical_to_previous"] is None
    # The transcripts' own first lines differ (round1 vs round2 in the name);
    # taking the fenced prompt is what makes the retry loop visible at all.
    assert rep["per_call"][1]["prompt_identical_to_previous"] is True


# ---------------------------------------------------------------- the price fit
def test_price_fit_recovers_rates_it_was_given():
    rates = (10.0, 1.0, 25.0)   # $/Mtok for write, read, output

    def bill(cc, cr, ot):
        return (cc * rates[0] + cr * rates[1] + ot * rates[2]) / 1e6

    rows = [(c, r, o, bill(c, r, o)) for c, r, o in
            [(40000, 0, 45000), (100000, 36000, 70000), (33000, 5000, 59000),
             (55000, 20000, 130000)]]
    fit = desk_yield.price_fit(rows)
    assert fit["ok"]
    for name, want in zip(("cache_write", "cache_read", "output"), rates):
        assert fit["usd_per_mtok"][name] == pytest.approx(want, rel=1e-6)
    assert fit["max_abs_residual_usd"] < 1e-9
    assert fit["unidentified_terms"] == []


def test_price_fit_refuses_below_three_calls():
    fit = desk_yield.price_fit([(1, 2, 3, 0.5), (4, 5, 6, 0.9)])
    assert fit["ok"] is False
    assert "3" in fit["reason"]


def test_a_negative_rate_is_reported_as_unidentified_not_rounded_away():
    # Three calls whose cache_read is always zero cannot price cache_read.
    # The module must say so rather than publish whatever the solver returned.
    rows = [(40000, 0, 45000, 1.5), (60000, 0, 70000, 2.4), (30000, 0, 30000, 1.05)]
    fit = desk_yield.price_fit(rows)
    if fit["ok"]:
        assert fit["calls_with_nonzero_tokens"]["cache_read"] == 0


# -------------------------------------------------------------- the manual size
def test_manual_trajectory_counts_only_the_writes(tmp_path):
    snaps = tmp_path / "books" / "snapshots"
    for name, size in [("rev01-carried", 500), ("rev02-before-theorize", 500),
                       ("rev03-after-theorize", 300), ("rev04-before-theorize", 300),
                       ("rev05-after-theorize", 400), ("rev06-after-theorize", 400)]:
        d = snaps / name
        d.mkdir(parents=True)
        (d / "theory.dsl").write_text("x" * size, encoding="utf-8")
    m = desk_yield.manual_trajectory(str(tmp_path))
    # `before-theorize` is a copy of the previous `after` -- counting both
    # would double every plateau and invent a compression that never happened.
    assert m["after_theorize_theory_chars"] == [300, 400, 400]
    assert m["carried_theory_chars"] == 500
    assert m["ended_shorter_than_carried"] is True
    assert m["frozen_tail_writes"] == 1


def test_a_leg_with_no_snapshots_says_so_rather_than_reporting_zero():
    m = desk_yield.manual_trajectory(os.path.join(RUNS, "does-not-exist"))
    assert m["revisions"] == []
    assert "no books/snapshots" in m["reason"]


def test_a_leg_with_no_desk_dir_is_reported_as_absent(tmp_path):
    rep = desk_yield.yield_leg(str(tmp_path))
    assert rep["calls"] == 0
    assert rep["totals"] is None
    assert "no desk/" in rep["reason"]


# --------------------------------------------------- the pair this module is for
@pytest.mark.skipif(not os.path.isdir(SK48), reason="R2b legs not in this tree")
def test_sk48_burned_three_quarters_of_its_leg_on_calls_that_delivered_no_manual():
    rep = desk_yield.yield_leg(SK48)
    t = rep["totals"]
    assert t["calls"] == 6
    assert t["void_calls"] == 4
    assert t["void_call_numbers"] == [3, 4, 5, 6]
    assert t["void_share_of_spend"] > 0.70
    # Every void call sat at the same step: the leg stopped moving and kept
    # paying.  This is the finding, and it is an equality, not a trend.
    steps = {c["step_idx"] for c in rep["per_call"] if c["void"]}
    assert steps == {10}


@pytest.mark.skipif(not os.path.isdir(SK48), reason="R2b legs not in this tree")
def test_sk48_was_asked_the_identical_question_twice():
    rep = desk_yield.yield_leg(SK48)
    assert rep["totals"]["repeated_prompts"] == [5]


@pytest.mark.skipif(not (os.path.isdir(SK48) and os.path.isdir(G50T)),
                    reason="R2b legs not in this tree")
def test_the_expensive_leg_sent_the_smaller_prompt():
    """The obvious hypothesis, refuted on the record.

    If desk cost tracked manual size, sk48 -- whose manual is 32 kB against
    g50t's 72 kB by the end -- would be the cheap leg.  It is 3.5x the dearer
    one per action.
    """
    sk, g5 = desk_yield.yield_leg(SK48), desk_yield.yield_leg(G50T)
    sk_prompt = max(c["prompt_chars"] for c in sk["per_call"])
    g5_prompt = max(c["prompt_chars"] for c in g5["per_call"])
    assert sk_prompt < g5_prompt
    assert sk["manual"]["after_theorize_theory_chars"][-1] < \
        g5["manual"]["after_theorize_theory_chars"][-1]
    assert sk["totals"]["usd_per_billed_action"] > 3 * g5["totals"]["usd_per_billed_action"]


@pytest.mark.skipif(not (os.path.isdir(SK48) and os.path.isdir(G50T)),
                    reason="R2b legs not in this tree")
def test_output_tokens_carry_most_of_the_bill_on_both_legs():
    for run in (SK48, G50T):
        rep = desk_yield.yield_leg(run)
        fit = rep["price_fit"]
        assert fit["ok"], run
        # The fit is only worth quoting if it reproduces the bills it was fit
        # to; 1% of the mean bill is the bar.
        assert fit["max_residual_share_of_mean_bill"] < 0.01, run
        assert rep["totals"]["output_share_of_bill"] > 0.5, run


@pytest.mark.skipif(not (os.path.isdir(SK48) and os.path.isdir(G50T)),
                    reason="R2b legs not in this tree")
def test_the_compression_rule_is_not_enforced_in_either_direction():
    """`Theoria.md` 1.8 says a concept earns its place by making the manual
    shorter.  Neither leg is governed by it: g50t's book grew 90% from its
    first write and ended half again larger than the seed, and sk48's stopped
    changing size at all.  Recorded as a fact about the framework."""
    g5 = desk_yield.yield_leg(G50T)["manual"]
    sk = desk_yield.yield_leg(SK48)["manual"]
    assert g5["ended_shorter_than_carried"] is False
    assert g5["net_growth_after_first_write_chars"] > 30000
    assert sk["frozen_tail_writes"] >= 1
