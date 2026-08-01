"""A refused command and a broken one must not be the same row.

87% of this arm's live commands come back `400 SERVER_ERROR / game <id> not
found`. That is the upstream's transient, not a defect here: the refused
request is byte-identical to the one that succeeds seconds later, and the
scorecard confirms the upstream charged for exactly the successes. `harness/
arc.py:_retryable` already retries it, correctly. What was broken is the
*record* -- every refusal was written as an ordinary non-200 step, so nothing
downstream could tell weather from breakage, and `OUTBOUND_PER_ACTION = 9.3`
inherited a numerator that is 85% weather without saying so.

`armtools/refusal.py` draws the line. These tests hold it in place, and most of
them are about making the classifier **say no** -- a signature that matches
everything would reclassify every real failure this arm ever suffers as
weather, which is a strictly worse failure mode than the one being fixed. Every
conjunct of the signature gets a test that removes it and asserts the answer
flips.

Real-data anchors are used wherever possible. Where a synthetic row is needed
it is a real recorded response body with one field changed, and the docstring
says which.
"""

from __future__ import annotations

import copy
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from armtools import refusal                                          # noqa: E402
from harness import spend as spend_mod                                # noqa: E402
from proxy.ledger import read_ledger                                  # noqa: E402

ARM = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNS = os.path.join(ARM, "runs")

#: The four live legs of 2026-07-31. arc-recon measured 494 refusals of 570
#: `env_step` rows across them; that total is the number these tests reproduce.
LIVE_LEGS = (
    "20260731T1240Z-A3-level2-carried",
    "20260731T1310Z-A3-level2-carried-r2",
    "20260731T1430Z-A3-level2-carried-r3",
    "20260731T1500Z-A3-sk48-carried-l1",
)

#: The four legs `OUTBOUND_PER_ACTION_PROVENANCE` names.
PROVENANCE_LEGS = (
    "20260728T012311Z-g50t-first-contact-aborted",
    "20260728T014402Z-g50t-first-contact-aborted",
    "20260728T015354Z-g50t-first-contact",
    "20260729T004020Z-leg01",
)


def _ledger(slug):
    path = os.path.join(RUNS, slug, "ledger.jsonl")
    if not os.path.exists(path):
        pytest.skip("leg not present in this checkout: %s" % slug)
    return read_ledger(path)


def _a_real_transient_row():
    """A verbatim refused `env_step` from the 2026-07-31 g50t leg."""
    for record in _ledger(LIVE_LEGS[0]):
        if (record.get("event") == "env_step"
                and refusal.classify(record) == "upstream_transient"):
            return copy.deepcopy(record)
    raise AssertionError("the leg that motivated this module has no refusal in it")


# -- what the records say ----------------------------------------------------

def test_the_four_live_legs_are_494_refusals_of_570_steps():
    """arc-recon's measurement, reproduced by the classifier rather than
    trusted. If this drifts, either a ledger changed or the signature did."""
    totals = {name: 0 for name in sorted(refusal.OUTCOMES)}
    for slug in LIVE_LEGS:
        for name, count in refusal.partition(_ledger(slug)).items():
            totals[name] += count

    assert totals["upstream_transient"] == 494
    assert totals["success"] == 76
    assert sum(totals.values()) == 570

    # And the point of the whole exercise: not one of those 494 is a real
    # failure. Before this module they were indistinguishable from 494 of them.
    assert totals["upstream_failure"] == 0
    assert totals["unrecorded"] == 0


def test_the_refused_request_is_byte_identical_to_the_one_that_succeeds():
    """The diagnosis in one assertion.

    Ten `RESET`s are refused and the eleventh returns a frame and a `guid`. All
    eleven carry the same `request_sha256`, the same URL and the same
    `card_id`. Nothing on this side varies across the split, so nothing on this
    side causes the refusal -- which is why the fix is to the record and not to
    the request.
    """
    steps = [r for r in _ledger(LIVE_LEGS[0]) if r.get("event") == "env_step"]
    resets = [r for r in steps if r["action"]["name"] == "RESET"]

    refused = [r for r in resets if refusal.classify(r) == "upstream_transient"]
    accepted = [r for r in resets if refusal.classify(r) == "success"]
    assert refused and accepted, "this leg is supposed to contain both"

    hashes = {r["http"]["request_sha256"] for r in resets}
    assert len(hashes) == 1, hashes
    assert {r["http"]["final_url"] for r in resets} == {
        "https://three.arcprize.org/api/cmd/RESET"}
    assert len({r["card_id"] for r in resets}) == 1

    # The refusals carry no frame; the success does.
    assert all(r["n_frames"] == 0 and r["frames"] is None for r in refused)
    assert all(r["n_frames"] and r["frames"] for r in accepted)


def test_the_upstream_charged_for_the_successes_and_nothing_else():
    """`uncharged` is not this arm's opinion: the closed scorecard is the
    independent witness, and it agrees on all four legs."""
    for slug in LIVE_LEGS:
        records = _ledger(slug)
        scorecard = None
        for record in records:
            if (record.get("event") == "env_meta"
                    and (record.get("response") or {}).get("environments")):
                scorecard = record["response"]
        assert scorecard is not None, slug

        report = refusal.outbound_accounting(records)
        assert report["successful_actions"] == scorecard["total_actions"], slug
        # Hundreds of refusals, and the API billed for none of them.
        assert report["uncharged_upstream"] > 0, slug


def test_the_classifier_is_total_over_every_ledger_this_arm_has():
    """No row anywhere falls outside `OUTCOMES`, and the partition of every
    ledger sums to its own `env_step` count."""
    seen = 0
    for slug in sorted(os.listdir(RUNS)):
        path = os.path.join(RUNS, slug, "ledger.jsonl")
        if not os.path.exists(path):
            continue
        records = read_ledger(path)
        steps = [r for r in records if r.get("event") == "env_step"]
        counts = refusal.partition(records)
        assert set(counts) == set(refusal.OUTCOMES)
        assert sum(counts.values()) == len(steps), slug
        for record in steps:
            assert refusal.classify(record) in refusal.OUTCOMES
        seen += len(steps)
    assert seen > 1000, "expected the arm's whole ledger corpus, got %d" % seen


# -- the negative controls: the signature must be able to say no -------------

def test_a_message_naming_a_different_game_is_a_failure_not_weather():
    """The conjunct that earns its keep.

    A `game <id> not found` naming a game the row did not ask about means the
    id really was wrong -- a client defect, and the one defect that would
    otherwise hide inside this wave perfectly. No such row exists in any ledger
    today; the check is here so that if one appears it is counted as a failure.
    """
    row = _a_real_transient_row()
    assert refusal.classify(row) == "upstream_transient"

    row["response"]["message"] = "game tn36-ef4dde99 not found"
    assert refusal.classify(row) == "upstream_failure"


def test_a_validation_error_that_also_says_not_found_is_a_failure():
    """Taken from the same four legs: the `scorecard/close` that came back
    `404 VALIDATION_ERROR / scorecard ... not found` because the card had
    auto-closed server-side. That is a real and consequential failure, and it
    contains the words "not found" -- which is exactly why the signature
    requires the upstream's own `SERVER_ERROR` name and an anchored message
    rather than a substring search.

    `harness/arc.py:_retryable` *does* match this one, deliberately: on the
    wire a false negative costs a leg, while here a false positive would
    launder a real failure into weather. The two predicates differ on purpose
    and this test pins the difference.
    """
    row = _a_real_transient_row()
    row["http"]["status"] = 404
    row["response"] = {"error": "VALIDATION_ERROR",
                       "message": "scorecard <redacted:key-shaped> not found"}
    assert refusal.classify(row) == "upstream_failure"

    # ... and the arm's wire-level predicate still retries it.
    from harness.arc import _retryable
    assert _retryable(400, {"message": "scorecard x not found"}) is True


@pytest.mark.parametrize("mutation,expected", [
    ({"http": {"status": 500}}, "upstream_failure"),
    ({"http": {"status": 403}}, "upstream_failure"),
    ({"response": {"error": "RATE_LIMIT",
                   "message": "game g50t-5849a774 not found"}},
     "upstream_failure"),
    ({"response": {"error": "SERVER_ERROR",
                   "message": "the game g50t-5849a774 not found today"}},
     "upstream_failure"),
    ({"response": {"error": "SERVER_ERROR", "message": ""}}, "upstream_failure"),
    ({"response": None}, "unrecorded"),
])
def test_each_conjunct_of_the_signature_can_fail(mutation, expected):
    """Remove one conjunct at a time from a real refusal; the answer must stop
    being `upstream_transient` every time. A signature no mutation can break is
    a signature that is not checking anything."""
    row = _a_real_transient_row()
    assert refusal.classify(row) == "upstream_transient"
    for key, value in mutation.items():
        if isinstance(value, dict) and isinstance(row.get(key), dict):
            row[key].update(value)
        else:
            row[key] = value
    assert refusal.classify(row) == expected


def test_a_refusal_that_returned_frames_is_a_contradiction_not_weather():
    """`n_frames: 0` is part of the signature. A row claiming both a refusal
    and a frame is incoherent, and incoherent rows must surface rather than be
    absorbed into a well-understood bucket."""
    row = _a_real_transient_row()
    row["n_frames"] = 3
    assert refusal.classify(row) == "upstream_failure"

    row = _a_real_transient_row()
    row["frames"] = [[[0]]]
    assert refusal.classify(row) == "upstream_failure"


def test_an_unforwarded_row_is_never_an_upstream_verdict():
    """The sealed-pile guard's 403 never reached the network, so it cannot be
    evidence about the upstream -- and it must never be charged as outbound."""
    row = _a_real_transient_row()
    row["http"] = {"status": 403, "forwarded": False, "attempts": 0,
                   "method": "POST", "path": "/api/cmd/RESET"}
    row["guard"] = {"decision": "deny", "rule": "sealed_pile"}
    assert refusal.classify(row) == "guard_refused"

    report = refusal.outbound_accounting([dict(row, event="env_step")])
    assert report["outbound_total"] == 0
    assert report["partition"]["guard_refused"] == 1


def test_a_body_the_ledger_never_kept_is_unanswerable_not_failed():
    """Three live legs predate the proxy recording response bodies. Calling
    those 297 rows failures would be a claim the record does not support;
    calling them weather would be worse. They get their own bucket, and
    `decomposable` goes false so no caller reads a split that was not
    measurable."""
    slug = "20260728T012311Z-g50t-first-contact-aborted"
    records = _ledger(slug)
    counts = refusal.partition(records)
    assert counts["unrecorded"] > 0
    assert counts["upstream_transient"] == 0
    assert counts["upstream_failure"] == 0

    report = refusal.outbound_accounting(records)
    assert report["decomposable"] is False

    # And a leg that did record its bodies is decomposable.
    assert refusal.outbound_accounting(
        _ledger(LIVE_LEGS[0]))["decomposable"] is True


def test_the_share_actually_moves_when_the_traffic_changes():
    """A metric that reads the same on every input measures nothing. A ledger
    of real failures must report zero transient share, not the 0.9 the live
    legs report."""
    live = refusal.outbound_accounting(_ledger(LIVE_LEGS[0]))
    assert live["transient_share"] == pytest.approx(0.9, abs=0.01)

    row = _a_real_transient_row()
    row["response"] = {"error": "SERVER_ERROR", "message": "internal error"}
    row["http"]["status"] = 500
    synthetic = refusal.outbound_accounting([dict(row, event="env_step")])
    assert synthetic["transient_share"] == 0.0
    assert synthetic["partition"]["upstream_failure"] == 1


# -- the sizing constant now rests on a derivation ---------------------------

def test_the_published_constant_reproduces_from_the_ledgers():
    """`OUTBOUND_PER_ACTION_PROVENANCE` claims 251 forwarded ACTION requests
    over 27 successful ACTIONs. Recompute it rather than believe it."""
    legs = {slug: _ledger(slug) for slug in PROVENANCE_LEGS}
    derived = refusal.derive_outbound_per_action(legs)

    assert derived["outbound_action_forwarded"] == 251
    assert derived["successful_actions"] == 27
    assert derived["blended"] == pytest.approx(9.296, abs=0.001)

    # The constant is rounded down from the derivation, and must never sit
    # above it -- 9.3 would then be reserving less than the legs it cites.
    assert spend_mod.OUTBOUND_PER_ACTION == pytest.approx(9.3, abs=0.001)
    assert spend_mod.OUTBOUND_PER_ACTION >= derived["blended"] - 0.01


def test_the_constant_declares_that_it_is_a_blend_of_two_regimes():
    """The defect this ticket names, in the sizing path: 9.3 was presented as a
    transport measurement while being 85% upstream weather. It may keep its
    value -- under-reserving cost a leg and an unspent hold is returned -- but
    it may not keep the silence."""
    assert spend_mod.OUTBOUND_PER_ACTION_REGIME == "blended"
    assert "REGIME" in spend_mod.OUTBOUND_PER_ACTION_PROVENANCE

    decomposition = spend_mod.OUTBOUND_PER_ACTION_DECOMPOSITION
    assert decomposition["productive"] < 2.0 < decomposition["blended"]
    # It must admit how much of its own evidence it could not decompose.
    assert decomposition["decomposable_legs"] < decomposition["legs"]


def test_the_declared_decomposition_is_what_the_ledgers_derive():
    """The dict in `spend.py` is a cache of a computation. Recompute it."""
    slugs = [s for s in PROVENANCE_LEGS + LIVE_LEGS
             if os.path.exists(os.path.join(RUNS, s, "ledger.jsonl"))]
    if len(slugs) < len(PROVENANCE_LEGS + LIVE_LEGS):
        pytest.skip("not every live leg is present in this checkout")

    derived = refusal.derive_outbound_per_action(
        {slug: _ledger(slug) for slug in slugs})
    declared = spend_mod.OUTBOUND_PER_ACTION_DECOMPOSITION

    for key in ("blended", "productive", "transient_share_of_classifiable"):
        assert derived[key] == pytest.approx(declared[key], abs=0.001), key
    for key in ("legs", "decomposable_legs", "outbound_action_forwarded",
                "successful_actions"):
        assert derived[key] == declared[key], key


def test_every_plan_carries_the_regime():
    """A reservation sized on 9.3 must say what 9.3 is, the same way
    `HTTP_PER_COMMAND_IS_VALIDATED` made a borrowed constant announce itself."""
    caps = spend_mod.plan_caps(actions=20, commands=2000,
                               cost_ceiling_usd=12.0, wall_clock_s=600,
                               require_headroom=False)
    arithmetic = caps.as_json()["arithmetic"]
    assert arithmetic["outbound_per_action_regime"] == "blended"
    assert arithmetic["outbound_per_action_decomposition"]["productive"] < 2.0


# -- the recording defect that started it ------------------------------------

def test_step_idx_counts_attempts_which_is_why_replay_found_nothing():
    """`proxy/ledger.py:_next_step` increments per written step, and the arm
    retries by re-issuing -- so `step_idx 0` is a refusal in every live leg and
    the indices number attempts, not actions. A replay tool looking for a
    session that opens on a `RESET` frame finds none, and returns empty rather
    than wrong. This pins the fact so the next reader is not surprised by it.
    """
    for slug in LIVE_LEGS:
        steps = [r for r in _ledger(slug) if r.get("event") == "env_step"]
        first = min(steps, key=lambda r: r["step_idx"])
        assert first["step_idx"] == 0
        assert refusal.classify(first) == "upstream_transient", slug

        # The indices are dense over attempts, not over successful actions.
        assert len(steps) == max(r["step_idx"] for r in steps) + 1
        successes = sum(1 for r in steps if refusal.classify(r) == "success")
        assert successes < len(steps) / 4, slug


def test_the_archive_can_record_the_split_on_request():
    """`reconcile()` hands back one undifferentiated `http_amplification`. Asked
    for the split, it must also say what the non-200 rows were."""
    from armtools import archive

    records = _ledger(LIVE_LEGS[0])
    out = archive.reconcile(records, None, outcomes=True)
    assert out["outcomes"]["upstream_transient"] == 54
    assert out["outcomes"]["upstream_failure"] == 0
    assert out["outbound"]["outbound_per_action_productive"] == pytest.approx(
        1.0, abs=0.01)
    # The old field is unchanged: this is an addition, not a redefinition.
    assert out["http_amplification"] == 12.0
    assert json.dumps(out)      # the archive has to be able to write it


def test_the_split_is_opt_in_so_published_manifests_still_re_derive():
    """The constraint that shaped the design, pinned so it is not lost.

    `verify_provenance` check 9 re-derives every published `MANIFEST.json` and
    compares byte for byte; manifests embed `reconciliation: reconcile(...)`.
    Extending `reconcile()` unconditionally made 25 of them drift -- the check
    catching a real change to a derivation under published records. So the
    split defaults off, and putting it into manifests stays a migration
    decision rather than a side effect of this fix.
    """
    from armtools import archive

    records = _ledger(LIVE_LEGS[0])
    default = archive.reconcile(records, None)
    assert "outcomes" not in default
    assert "outbound" not in default

    # ... and asking for it is purely additive.
    asked = archive.reconcile(records, None, outcomes=True)
    for key, value in default.items():
        assert asked[key] == value, key
