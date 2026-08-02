"""The economy companion reads both axes right — and is seen to refuse.

Same shape as `test_theoria_live.py`: positives against the real committed leg
archives first (the money reconciles with the ledger it came from, the axis is
the archive's own, absence carries its reason), then negative controls that
break the arrangement one way each and assert the refusal or the red rung by
name.

The negative controls matter more here than usual.  This artefact's whole
claim is that it can tell an *exact* turn axis from a *fallback* one; a
version of it that quietly accepted a partial or irreconcilable join would
publish a front-load index over an axis nobody recorded, and would look
exactly like this one in the artefact.
"""

import dataclasses
import json
import os

import pytest

from battery import verify
from battery.adapters import theoria_live
from battery.audit import live_economy
from battery.guard import load_piles

R1 = "20260731T1240Z-A3-level2-carried"      # carried books, zero billed calls
R2 = "20260731T1310Z-A3-level2-carried-r2"   # 5 calls, 3 decision turns
R3 = "20260731T1430Z-A3-level2-carried-r3"   # 8 calls, 8 decision turns
# the leg that carries the live curves.json/ledger shortfall — see
# test_curves_json_shortfall_is_reported_not_absorbed
SHORTFALL = "20260731T231654Z-R1-sk48-b"


@pytest.fixture(scope="module")
def piles():
    return load_piles()


@pytest.fixture(scope="module")
def runs(piles):
    return {r.run_id: r
            for r in theoria_live.load_theoria_live_runs(piles=piles)}


@pytest.fixture(scope="module")
def fresh():
    """One in-process recompute of the companion, shared across tests."""
    return live_economy.build()


# --- the axis is read, not invented ---------------------------------------

def test_the_exact_axis_comes_from_the_archives_own_join(runs):
    """`bill_shape.json` publishes `call_idx -> turn`; the axis must be that
    field copied, not a rule this module made up about how calls group."""
    run = runs[R3]
    leg = os.path.join(theoria_live.LIVE_ROOT, R3)
    alt, note = live_economy.exact_axis(run, leg)
    assert alt is not None and note["axis"] == "exact"
    published = {int(row["call_idx"]): int(row["turn"])
                 for row in json.load(open(os.path.join(leg,
                                                        "bill_shape.json"),
                                            encoding="utf-8"))["calls"]}
    assert {c.idx: c.turn for c in alt.calls} == published


def test_a_leg_with_no_billed_call_has_no_bill_shape(runs):
    """r1 carried the books and spent nothing.  Absence, with its reason —
    a zero here would say the leg was cheap."""
    leg = os.path.join(theoria_live.LIVE_ROOT, R1)
    alt, note = live_economy.exact_axis(runs[R1], leg)
    assert alt is None
    assert note["axis"] == "not-applicable"
    assert "no bill" in note["reason"]


def test_the_money_reconciles_with_the_proxy_ledger(runs):
    """bill_shape.json's per-call dollars must equal the ledger's, to the
    cent, or the axis is refused rather than used."""
    for slug in (R2, R3):
        leg = os.path.join(theoria_live.LIVE_ROOT, slug)
        rec = live_economy.reconcile(runs[slug], leg)
        assert rec["bill_shape"]["present"]
        assert abs(rec["bill_shape"]["usd"] - rec["ledger"]["usd"]) < 1e-06


def test_curves_json_shortfall_is_reported_not_absorbed(runs):
    """A real, current disagreement: `curves.json` accounts for fewer billed
    calls than the proxy ledger.  The artefact must name both numbers.

    This test was originally written against r2/r3, where `curves.json`
    accounted for one billed call fewer than the ledger.  theoria-arm
    `82e8e25e` rewrote four legs' `curves.json` and fixed that instance —
    r3 now reads 8 calls / $13.439862 on both sides — so, as the original
    docstring instructed, the test was *rewritten* rather than deleted.  It
    now pins the live instance of the same defect, on the R1 sk48-b leg,
    where `curves.json` accounts for 0 billed calls over 2 turn rows while
    the proxy ledger bills 3 for $7.608528.

    The assertion is unchanged and is the point of the test: a disagreement
    is reported, not absorbed.  If this instance is fixed upstream too, find
    the leg that carries it next and retarget again."""
    leg = os.path.join(theoria_live.LIVE_ROOT, SHORTFALL)
    rec = live_economy.reconcile(runs[SHORTFALL], leg)
    assert not rec["all_three_agree"]
    joined = " ".join(rec["disagreements"])
    assert "curves.json" in joined and "proxy ledger" in joined


# --- the metric bodies are the frozen ones --------------------------------

def test_only_e2_and_e3_can_move_with_the_axis(runs, fresh):
    """E1/E4/E5/E6/E7 are per-call or per-step; if one of them moved when only
    the turn labels changed, the axis has leaked somewhere it should not."""
    for row in fresh["axis_sensitivity"]["cells_that_moved"]:
        assert row["metric"] in ("E2", "E3"), row


def test_the_of_record_readings_match_the_frozen_registry(runs, fresh):
    """This file must not become a second opinion about a metric's value: the
    of-record column has to be exactly what the registry returns."""
    from battery.metrics import REGISTRY
    for slug, row in fresh["legs"].items():
        for mid, cell in row["economy_of_record"].items():
            assert cell == REGISTRY[mid].fn(runs[slug]).as_dict()


def test_absence_is_recorded_with_a_reason_and_never_as_zero(fresh):
    assert fresh["absences"], "every live leg cannot have every metric"
    for row in fresh["absences"]:
        assert row["status"] in ("not-applicable", "insufficient-data")
        assert row["reason"], row
        cell = fresh["legs"][row["leg"]]["economy_of_record"][row["metric"]]
        assert cell["value"] is None, "an absent metric must not carry a value"


def test_the_turn_cost_curve_sums_to_the_bill(fresh):
    for slug, row in fresh["legs"].items():
        curve = row["turn_cost_curve_exact"]
        if not curve:
            continue
        total = row["ledger_cost_usd"]
        assert abs(curve[-1]["usd_cumulative"] - total) < 1e-06, slug
        assert curve[-1]["share_cumulative"] == 1.0


def test_the_constraint_is_stated_inside_the_artifact(fresh):
    assert "not confirmations" in fresh["constraint"]
    assert "PREDICTIONS.md" in fresh["constraint"]
    assert "0.250" in fresh["reading"], (
        "E2's flat-bill baseline must be in the file, or 0.2557 reads as "
        "`a quarter of the money` instead of `no front-loading`")


def test_the_artifact_is_byte_reproducible(fresh):
    assert live_economy.serialise(fresh) == live_economy.serialise(
        live_economy.build())


def test_committed_artifact_matches_the_recompute(fresh):
    with open(live_economy.DEFAULT_OUT, encoding="utf-8") as fh:
        committed = fh.read()
    assert committed == live_economy.serialise(fresh), (
        "battery/artifacts_live/live_economy.json is stale; regenerate with "
        "`python -m battery.audit.live_economy` and commit it")


# --- refusals --------------------------------------------------------------

def test_a_partial_join_is_refused(runs, tmp_path):
    """One billed call missing from the map, and the axis must be refused
    outright: bucketing the rest would put money on a turn nobody recorded."""
    leg = tmp_path / "leg"
    leg.mkdir()
    real = json.load(open(os.path.join(theoria_live.LIVE_ROOT, R3,
                                       "bill_shape.json"), encoding="utf-8"))
    real["calls"] = real["calls"][:-1]
    (leg / "bill_shape.json").write_text(json.dumps(real), encoding="utf-8",
                                         newline="\n")
    alt, note = live_economy.exact_axis(runs[R3], str(leg))
    assert alt is None and note["axis"] == "partial"


def test_an_irreconcilable_join_is_refused(runs, tmp_path):
    """Right number of calls, wrong money.  A shape computed over this would
    be the shape of a bill nobody was sent."""
    leg = tmp_path / "leg"
    leg.mkdir()
    real = json.load(open(os.path.join(theoria_live.LIVE_ROOT, R3,
                                       "bill_shape.json"), encoding="utf-8"))
    real["calls"][0]["usd"] = float(real["calls"][0]["usd"]) + 1.0
    (leg / "bill_shape.json").write_text(json.dumps(real), encoding="utf-8",
                                         newline="\n")
    alt, note = live_economy.exact_axis(runs[R3], str(leg))
    assert alt is None and note["axis"] == "irreconcilable"
    assert "USD" in note["reason"]


def test_an_unpriced_call_is_not_a_free_one(runs):
    """V9-D3, on this path too: strip a price and E1/E2/E3/E5 must go
    `unsound`, never quietly treat the call as costing nothing."""
    run = runs[R3]
    calls = list(run.calls)
    calls[0] = dataclasses.replace(calls[0], cost_usd=None)
    stripped = dataclasses.replace(run, calls=calls)
    from battery.metrics import REGISTRY
    for mid in ("E1", "E2", "E3", "E5"):
        value = REGISTRY[mid].fn(stripped)
        assert not value.ok and "no price" in (value.reason or "")


def test_writing_into_the_frozen_directory_is_refused(tmp_path):
    frozen_dir = os.path.join(live_economy.BATTERY, "artifacts")
    with pytest.raises(ValueError, match="frozen baseline"):
        live_economy.write(os.path.join(frozen_dir, "live_economy.json"))
    rc = live_economy.main(["--out", os.path.join(frozen_dir, "evil.json")])
    assert rc == 2
    assert not os.path.exists(os.path.join(frozen_dir, "evil.json"))


# --- the rung, green then red ---------------------------------------------

def test_rung_green_on_the_real_tree(capsys):
    problems = []
    verify.rung_live_economy(problems)
    assert problems == [], problems
    out = capsys.readouterr().out
    assert "exact axis" in out


def test_rung_red_on_a_tampered_companion(tmp_path):
    doc = json.load(open(live_economy.DEFAULT_OUT, encoding="utf-8"))
    doc["n_legs"] = doc["n_legs"] + 1
    bad = tmp_path / "live_economy.json"
    bad.write_text(live_economy.serialise(doc), encoding="utf-8", newline="\n")
    problems = []
    verify.rung_live_economy(problems, live_path=str(bad))
    assert any("recompute" in p for p in problems), problems


def test_rung_red_when_an_absence_carries_a_value(tmp_path):
    """The doctrine, enforced: a cell with a non-`ok` status must not carry a
    number.  This is the failure that would turn `did not happen` into
    `cheap`, and it is the reason this artefact exists."""
    doc = json.load(open(live_economy.DEFAULT_OUT, encoding="utf-8"))
    row = doc["absences"][0]
    doc["legs"][row["leg"]]["economy_of_record"][row["metric"]]["value"] = 0.0
    bad = tmp_path / "live_economy.json"
    bad.write_text(live_economy.serialise(doc), encoding="utf-8", newline="\n")
    problems = []
    verify.rung_live_economy(problems, live_path=str(bad))
    assert any("zero" in p for p in problems), problems


def test_rung_red_when_the_companion_is_absent(tmp_path):
    problems = []
    verify.rung_live_economy(problems, live_path=str(tmp_path / "no.json"))
    assert any("absent" in p for p in problems), problems


def test_rung_red_on_unparseable_companion(tmp_path):
    bad = tmp_path / "live_economy.json"
    bad.write_text("{not json", encoding="utf-8")
    problems = []
    verify.rung_live_economy(problems, live_path=str(bad))
    assert any("not JSON" in p for p in problems), problems
