"""The money half of the cost leg, and the failing paths it did not have.

Until C-3 the cost leg verified the price *table's* digest and never an
amount. `usd_total` was accumulated at `reconcile.py`'s pricing loop, reported
in the leg, and compared to nothing -- so multiplying every `usage` block by
900000 moved the derived bill from $0.00035 to $540.00 and reconciliation still
returned PASS. Hash-checking the price list is not verifying a bill, and S31
requirement 4 asks for a record whose amount does not reconcile to turn the
check red.

There is no declared total in the ledger to compare against, and there must not
be: `LEDGER_FORMAT.md` §5 and `canon.BANNED_SPELLINGS` keep dollar figures out
of the file on purpose, because a recorded price is wrong the day the table
changes. What a `claude -p` envelope does carry is the provider's own per-model
breakdown, whose **token counts** are a second independent witness to the very
numbers the bill is derived from. Integers on both sides, so C-3 is an equality
with no tolerance -- and a tolerance is exactly what would make it green by
construction.

The limit is asserted here too, in
`test_a_transport_with_no_second_witness_is_absent_and_not_a_pass`: the raw
`/v1/messages` path this proxy owns returns no breakdown, so on that path an
inflated usage block still reconciles. That gap is real and is reported by the
leg rather than papered over.
"""
from test_reconcile import (GAME, RUN, _card, forge, incidents)

from proxy.cost import PriceTable
from proxy.ledger import Ledger, RunLedger
from proxy.reconcile import reconcile_run

#: One of the seven real archived records in `theoria-arm/runs/*`, verbatim.
#: The write is 100% 1h cache, which is why `cost.py` had to learn to price the
#: breakdown before this fixture could reconcile at all.
CLI_USAGE = {"input_tokens": 2, "output_tokens": 43066,
             "cache_creation_input_tokens": 20736,
             "cache_read_input_tokens": 24264,
             "cache_creation": {"ephemeral_1h_input_tokens": 20736,
                                "ephemeral_5m_input_tokens": 0}}

#: `modelUsage` covers a second, cheaper model on purpose: the CLI bills its own
#: `ai-title` sub-call inside the same envelope, which is why `total_cost_usd`
#: is larger than the opus line and why C-3 keys on this record's model rather
#: than summing the map.
MODEL_USAGE = {
    "claude-opus-5": {
        "canonicalModel": "claude-opus-5", "costUSD": 1.296152,
        "inputTokens": 2, "outputTokens": 43066,
        "cacheCreationInputTokens": 20736, "cacheReadInputTokens": 24264},
    "claude-haiku-4-5-20251001": {
        "canonicalModel": "claude-haiku-4-5", "costUSD": 0.011575,
        "inputTokens": 11480, "outputTokens": 19,
        "cacheCreationInputTokens": 0, "cacheReadInputTokens": 0},
}


def write_cli_run(path, *, factor=1, model_usage=MODEL_USAGE, model_calls=1):
    """A run whose model call came back on the `claude -p` transport.

    Written through the real writer for RED-40's reason. `factor` scales the
    `usage` block **only** -- the envelope keeps the provider's numbers, which
    is the divergence C-3 exists to see.
    """
    table = PriceTable.load()
    run = RunLedger(Ledger(path), RUN, "mock_arm", game_id=GAME)
    run.run_start(game_id=GAME, card_id="c1")
    run.env_step(GAME, {"name": "RESET", "id": None, "data": None},
                 frames=[[[0]]], card_id="c1", guid="g", levels_completed=0,
                 response={"win_levels": 8}, http={"status": 200})
    run.env_step(GAME, {"name": "ACTION1", "id": 1, "data": None},
                 frames=[[[1]]], card_id="c1", guid="g", levels_completed=0,
                 response={"win_levels": 8}, http={"status": 200})

    usage = {k: (v * factor if isinstance(v, int) else v)
             for k, v in CLI_USAGE.items()}
    usage["cache_creation"] = {k: v * factor
                               for k, v in CLI_USAGE["cache_creation"].items()}

    for i in range(model_calls):
        response = {"type": "result", "subtype": "success",
                    "total_cost_usd": 1.307727}
        if model_usage is not None:
            response["modelUsage"] = model_usage
        run.model_call("claude-code-cli", "claude-opus-5",
                       request={"transport": "claude-code-cli", "prompt": "x"},
                       response=response, usage=usage,
                       pricing_ref=table.reference(), step_idx=i,
                       http={"status": 200})
    run.run_end(outcome="done", steps=1, model_calls=model_calls,
                scorecard=_card(actions=1))
    return path


def write_http_run(path, *, model_calls=2):
    """The transport this proxy owns: `usage`, and no second witness."""
    table = PriceTable.load()
    run = RunLedger(Ledger(path), RUN, "mock_arm", game_id=GAME)
    run.run_start(game_id=GAME, card_id="c1")
    run.env_step(GAME, {"name": "RESET", "id": None, "data": None},
                 frames=[[[0]]], card_id="c1", guid="g", levels_completed=0,
                 response={"win_levels": 8}, http={"status": 200})
    run.env_step(GAME, {"name": "ACTION1", "id": 1, "data": None},
                 frames=[[[1]]], card_id="c1", guid="g", levels_completed=0,
                 response={"win_levels": 8}, http={"status": 200})
    for i in range(model_calls):
        run.model_call("anthropic", "mock-model-1", request={"m": i},
                       response={"r": i},
                       usage={"input_tokens": 10, "output_tokens": 5},
                       pricing_ref=table.reference(), step_idx=i,
                       http={"status": 200})
    run.run_end(outcome="done", steps=1, model_calls=model_calls,
                scorecard=_card(actions=1))
    return path


# -- the control, first ------------------------------------------------------

def test_a_cli_run_whose_usage_is_the_usage_billed_reconciles(tmp_path):
    """Without this the reds below could all be red by construction."""
    report = reconcile_run(RUN, write_cli_run(str(tmp_path / "ok.jsonl")),
                           write_incident=False)
    assert report["verdict"] == "PASS", report
    assert report["legs"]["cost"]["verdict"] == "AGREE"
    assert report["legs"]["cost"]["amount_witnessed_calls"] == 1
    assert report["legs"]["cost"]["amount_not_witnessed"] == 0
    assert report["legs"]["cost"]["usage_disputed"] is None


# -- the failing paths -------------------------------------------------------

def test_red_a_usage_block_inflated_900000x_makes_the_cost_leg_disagree(tmp_path):
    """The finding S31 was opened on, as a failing path.

    Before C-3 this exact stream reconciled PASS, deriving $540 against a
    recorded $1.31, because nothing compared the two.
    """
    path = write_cli_run(str(tmp_path / "inflated.jsonl"), factor=900000)
    report = reconcile_run(RUN, path, write_incident=True)

    assert report["verdict"] == "FAIL", report
    assert report["legs"]["cost"]["verdict"] == "DISAGREE"
    assert any("C-3" in p for p in report["problems"])
    disputed = report["legs"]["cost"]["usage_disputed"]
    assert {d["key"] for d in disputed} == {
        "input_tokens", "output_tokens", "cache_creation_input_tokens",
        "cache_read_input_tokens"}
    assert "cost" in incidents(path)[-1]["failing_legs"]
    assert report["legs"]["actions"]["verdict"] == "AGREE", (
        "the cost leg went red on its own")
    assert report["legs"]["score_per_run"]["verdict"] == "AGREE"


def test_red_a_single_edited_token_count_is_enough(tmp_path):
    """The tamper does not have to be large: one field, one call, off by one."""
    def mutate(record):
        if record.get("event") == "model_call":
            record["usage"] = dict(record["usage"], output_tokens=43067)
        return record

    clean = write_cli_run(str(tmp_path / "clean.jsonl"))
    path = forge(clean, str(tmp_path / "one.jsonl"), mutate)
    report = reconcile_run(RUN, path, write_incident=False)

    assert report["verdict"] == "FAIL", report
    assert report["legs"]["cost"]["usage_disputed"] == [
        {"call_idx": 0, "key": "output_tokens",
         "usage": 43067, "model_usage": 43066}]


def test_red_an_envelope_edited_to_match_a_tampered_usage_still_fails_elsewhere(
        tmp_path):
    """Editing both sides to agree is possible -- and then the price table no
    longer reproduces the stated bill. C-3 is one witness, not the only one."""
    inflated = write_cli_run(str(tmp_path / "both.jsonl"), factor=2,
                             model_usage={"claude-opus-5": dict(
                                 MODEL_USAGE["claude-opus-5"],
                                 inputTokens=4, outputTokens=86132,
                                 cacheCreationInputTokens=41472,
                                 cacheReadInputTokens=48528)})
    report = reconcile_run(RUN, inflated, write_incident=False)
    # C-3 is satisfied -- the two sides were made to agree ...
    assert report["legs"]["cost"]["usage_disputed"] is None
    # ... and the derived bill is now double the stated one, which is the
    # residue this test exists to record rather than to assert a red on.
    assert report["legs"]["cost"]["usd_total"] > 2.0


# -- the honest limits, asserted so they cannot be widened quietly ----------

def test_a_transport_with_no_second_witness_is_absent_and_not_a_pass(tmp_path):
    """The raw `/v1/messages` path this proxy owns has no breakdown to compare.

    The run still PASSes -- an absent witness is not a disagreement -- but the
    count is in the report, so "the money reconciled" cannot be read off a run
    that nothing witnessed. This is the gap the leg's note names in words.
    """
    report = reconcile_run(RUN, write_http_run(str(tmp_path / "http.jsonl")),
                           write_incident=False)
    assert report["verdict"] == "PASS", report
    assert report["legs"]["cost"]["amount_witnessed_calls"] == 0
    assert report["legs"]["cost"]["amount_not_witnessed"] == 2
    assert report["legs"]["cost"]["usage_disputed"] is None


def test_the_gap_is_named_in_the_legs_note():
    """A limit that is only in a commit message is a limit nobody reads."""
    import tempfile, os
    with tempfile.TemporaryDirectory() as tmp:
        report = reconcile_run(
            RUN, write_http_run(os.path.join(tmp, "l.jsonl")),
            write_incident=False)
    note = report["legs"]["cost"]["note"]
    assert "amount_not_witnessed" in note
    assert "still reconciles" in note


def test_a_cli_success_that_lost_its_breakdown_is_INCOMPLETE_not_PASS(tmp_path):
    """A `claude -p` success envelope always carries one, so its absence there
    is evidence lost -- a different word from a transport that never had any."""
    path = write_cli_run(str(tmp_path / "lost.jsonl"), model_usage=None)
    report = reconcile_run(RUN, path, write_incident=False)

    assert report["legs"]["cost"]["verdict"] == "INCOMPLETE"
    assert report["verdict"] == "INCOMPLETE"
    assert report["verdict"] != "PASS"


# -- a leg that could not be evaluated is not a leg that agreed -------------

def test_a_run_with_no_bill_is_distinguishable_from_one_that_reconciled(tmp_path):
    """`_leg` stamps `votes=True` by default and the verdict loop tests only
    for INCOMPLETE, so NOT_APPLICABLE fell through to PASS -- making a run with
    no bill print the same word as a run whose bill reconciled, which is
    exactly what the leg's own note says it is not.

    Not promoted to INCOMPLETE: a replay run can never have model calls, and a
    signal that can never go green gets switched off. The leg stops voting
    instead, and `legs_voting` says which ones did.
    """
    nothing = reconcile_run(
        RUN, write_http_run(str(tmp_path / "none.jsonl"), model_calls=0),
        write_incident=False)
    assert nothing["legs"]["cost"]["verdict"] == "NOT_APPLICABLE"
    assert nothing["legs"]["cost"]["votes"] is False
    assert "cost" not in nothing["legs_voting"]

    billed = reconcile_run(RUN, write_cli_run(str(tmp_path / "bill.jsonl")),
                           write_incident=False)
    assert "cost" in billed["legs_voting"]
    assert nothing["legs_voting"] != billed["legs_voting"], (
        "a run with no bill and a run whose bill reconciled must be "
        "distinguishable in the report")
