"""The threat-model split and E2L, with the negative controls that matter.

A check that has never been seen to say no has not been shown to check
anything, so every gate here is asserted in **both** directions: the run it
must refuse, and the neighbouring run it must not. The two headline
assertions are deliberately the uncomfortable ones --

* `test_t_arm_does_not_clear_E2` pins the finding that my own narrowing is
  defeated by attaching forty `Step` records to an existing attack;
* `test_e2l_is_gameable_by_concentration` pins that the metric I built is
  gameable too.

If either ever turns green by starting to pass, someone has quietly weakened
the audit and the suite should go red rather than congratulate them.
"""

from __future__ import annotations

import os

import pytest

from battery.audit import frontload, threat
from battery.audit.v9.check import certificate
from battery.metrics import evaluate
from battery.model import Call, Run, Step

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))


# --------------------------------------------------------------------------
# threat.py -- the narrowing, and the corpus's veto over it.
# --------------------------------------------------------------------------

@pytest.fixture(scope="module")
def doc():
    return threat.build()


def test_the_corpus_overrules_two_invariants(doc):
    """Validation is not decorative: real runs threw two candidates out.

    I7 and I8 are things a recorder plausibly guarantees, and real recorded
    play breaks both. Recording that is the whole point -- an invariant that
    calls real play impossible would dismiss attacks for resembling reality.
    """
    dropped = {d["invariant"] for d in doc["validation"]["dropped"]}
    assert dropped == {"I7", "I8"}, doc["validation"]["dropped"]
    assert doc["validation"]["n_real_runs"] >= 90
    for row in doc["validation"]["dropped"]:
        assert row["run_id"] and row["violation"]


def test_every_kept_invariant_holds_on_every_real_run(doc):
    kept = doc["validation"]["kept"]
    assert kept == ["I1", "I2", "I3", "I4", "I5", "I6", "I9", "I10"]
    for run in threat.real_runs():
        assert threat.violations(run, kept) == [], run.run_id


def test_the_narrowing_removes_some_attacks_and_not_all(doc):
    """Neither degenerate outcome. A filter that clears everything is an
    opinion; one that clears nothing is not a narrowing."""
    assert doc["n_landed_t_arm"] < doc["n_landed_t_rec"]
    assert doc["n_landed_t_arm"] > 0
    threat.assert_not_vacuous(doc)


def test_assert_not_vacuous_says_no_in_both_directions():
    with pytest.raises(ValueError, match="whitewash"):
        threat.assert_not_vacuous({"n_landed_t_arm": 0, "n_landed_t_rec": 95})
    with pytest.raises(ValueError, match="not a narrowing"):
        threat.assert_not_vacuous({"n_landed_t_arm": 95, "n_landed_t_rec": 95})


def test_most_metrics_stay_gameable_under_the_narrow_model(doc):
    """T-ARM is not a rescue: 33 of 37 gameable metrics are still gameable."""
    assert len(doc["gameable_under_t_rec"]) == 37
    assert len(doc["gameable_under_t_arm"]) == 33
    for metric_id in ("P3", "P4", "K12", "X1", "X6", "M2"):
        assert metric_id in doc["gameable_under_t_arm"]


def test_each_kept_invariant_refuses_a_targeted_run():
    """Every surviving invariant, seen saying no to something."""
    kept = ["I1", "I2", "I3", "I4", "I5", "I6", "I9", "I10"]
    step = Step(idx=0, action="a", state_key="s")
    cases = {
        "I1": Run(run_id="x", arm="a", source="t",
                  calls=[Call(idx=0, cost_usd=1.0)]),
        "I2": Run(run_id="x", arm="a", source="t", steps=[step],
                  calls=[Call(idx=0, turn=9, cost_usd=1.0)]),
        "I4": Run(run_id="x", arm="a", source="t",
                  steps=[step, Step(idx=1, action="b", state_key="t")],
                  calls=[Call(idx=0, turn=1, cost_usd=1.0),
                         Call(idx=1, turn=0, cost_usd=1.0)]),
        "I5": Run(run_id="x", arm="a", source="t", steps=[step, step]),
        "I6": Run(run_id="x", arm="a", source="t", steps=[step],
                  calls=[Call(idx=0, cost_usd=1.0), Call(idx=1)]),
    }
    for inv_id, run in cases.items():
        broken = {b["invariant"] for b in threat.violations(run, kept)}
        assert inv_id in broken, (inv_id, broken)


def test_an_ordinary_run_breaks_nothing():
    """The other direction: a plain, honest run must sail through."""
    run = Run(run_id="x", arm="a", source="t",
              steps=[Step(idx=i, action="a%d" % i, state_key="s%d" % i)
                     for i in range(4)],
              calls=[Call(idx=i, turn=i, step_idx=i, cost_usd=0.5)
                     for i in range(4)])
    assert threat.reachability(run, ["I1", "I2", "I3", "I4", "I5", "I6",
                                     "I9", "I10"]) == "arm-reachable"


# --------------------------------------------------------------------------
# The finding this ticket exists for.
# --------------------------------------------------------------------------

def test_t_arm_reports_no_surviving_attack_on_E2(doc):
    """The tempting half of the result, pinned so the other half can bite."""
    assert doc["metrics"]["E2"]["t_arm_landed"] == []
    assert "E2" in doc["no_arm_reachable_attack_left"]
    # And the reason is uniform, which is what makes it weak: all three E2
    # attacks were written with no steps at all.
    for row in doc["metrics"]["E2"]["attacks"]:
        assert "I1" in row["breaks"], row


def test_t_arm_does_not_clear_E2():
    """**The finding.** Attaching steps to the attack restores the demotion.

    `batched-turn-label` was cleared by T-ARM only because its author gave the
    run no steps -- they were not needed to move E2. Laying out forty steps is
    pure layout, which the poverty certificate explicitly permits, so the
    clearance was an artefact of how six blind attackers happened to write
    their builders and not a fact about E2.

    S1 through S4, all four, on the repaired attack.
    """
    builder = frontload.build_E2_batched_turn_label_coherent
    run = builder()
    cert = certificate(builder)
    kept = threat.validate(threat.real_runs())["kept"]
    value = evaluate(run)["E2"]

    assert cert["ok"], cert["violations"]                       # S3
    assert threat.violations(run, kept) == []                   # S4
    assert value.ok and value.value is not None                 # S1
    assert value.value >= 0.95, value.value                     # S2
    assert round(value.value, 6) == 0.973387


def test_the_repaired_attack_does_not_land_on_E2L():
    """The axis is the whole difference, and it is worth exactly this much."""
    run = frontload.build_E2_batched_turn_label_coherent()
    reading = frontload.frontload_step_index(run)
    assert reading["status"] == "ok"
    assert not frontload.meets_target(reading["value"])
    assert round(float(reading["value"]), 6) == 0.322581


def test_e2l_is_gameable_by_concentration():
    """**The other finding.** E2L does not survive its own process 4.

    A run that bills everything at step 0 of 40 and then keeps moving scores
    1.0, is poverty-certified, and breaks no invariant. That is S1∧S2∧S3∧S4,
    so E2L enters the battery in the reference tier on its first audit -- the
    same concentration attack that holds E2 there.
    """
    builder = frontload.build_E2_first_turn_bill_coherent
    run = builder()
    cert = certificate(builder)
    kept = threat.validate(threat.real_runs())["kept"]
    reading = frontload.frontload_step_index(run)

    assert cert["ok"]
    assert threat.violations(run, kept) == []
    assert reading["status"] == "ok"
    assert frontload.meets_target(reading["value"])
    assert reading["value"] == 1.0


# --------------------------------------------------------------------------
# E2L's five gates, each seen saying no and seen saying nothing.
# --------------------------------------------------------------------------

def _steps(n, key=lambda i: "s%d" % i):
    return [Step(idx=i, action="a%d" % i, state_key=key(i)) for i in range(n)]


def test_G1_refuses_a_partly_priced_bill():
    run = Run(run_id="x", arm="a", source="t", steps=_steps(20),
              calls=[Call(idx=i, step_idx=i,
                          cost_usd=(1.0 if i < 3 else None))
                     for i in range(20)])
    assert frontload.frontload_step_index(run)["status"] == "unsound"


def test_G2_refuses_a_free_run():
    run = Run(run_id="x", arm="a", source="t", steps=_steps(20),
              calls=[Call(idx=i, step_idx=i, cost_usd=0.0) for i in range(20)])
    assert frontload.frontload_step_index(run)["status"] == "thin"


def test_G3_refuses_a_short_run_and_admits_an_eight_step_one():
    short = Run(run_id="x", arm="a", source="t", steps=_steps(7),
                calls=[Call(idx=i, step_idx=i, cost_usd=1.0)
                       for i in range(7)])
    assert frontload.frontload_step_index(short)["status"] == "thin"
    just_long = Run(run_id="x", arm="a", source="t", steps=_steps(8),
                    calls=[Call(idx=i, step_idx=i, cost_usd=1.0)
                           for i in range(8)])
    assert frontload.frontload_step_index(just_long)["status"] == "ok"


def test_G4_and_E2_now_both_refuse_the_unlabelled_axis():
    """The gate this metric exists for -- and the contrast that has gone.

    Through S45 this test pinned a *disagreement*: the same unlabelled run
    scored a number under E2, because `Run.turn_costs()` fell back to the
    call's position in the list whenever `Call.turn` was missing, while E2L's
    G4 refused it outright. That contrast is what motivated E2L.

    S46 removed the fallback (`freeze/RESIDUALS.json` `E2-AXIS`), so the
    demonstration no longer exists to be made: the record that E2L refuses on
    `step_idx` is now refused by E2 as well, on the turn label. The new fact
    worth pinning is the agreement -- both halves of the axis question say no
    to the same record, and neither manufactures an axis to answer it.

    The E2L half is unchanged from the original test on purpose; only E2's
    half moved.
    """
    run = Run(run_id="x", arm="a", source="t", steps=_steps(20),
              calls=[Call(idx=i, step_idx=None,
                          cost_usd=(1.0 if i == 0 else 0.0))
                     for i in range(20)])
    value = evaluate(run)["E2"]
    assert value.status == "insufficient-data"
    assert "turn label" in value.reason
    reading = frontload.frontload_step_index(run)
    assert reading["status"] == "unsound"
    assert "step_idx" in reading["reason"]


def test_G5_refuses_a_frozen_world_and_admits_a_moving_one():
    frozen = Run(run_id="x", arm="a", source="t",
                 steps=_steps(40, key=lambda i: "s0"),
                 calls=[Call(idx=i, step_idx=i,
                             cost_usd=(1.0 if i == 0 else 0.0))
                        for i in range(40)])
    assert frontload.frontload_step_index(frozen)["status"] == "thin"
    moving = Run(run_id="x", arm="a", source="t", steps=_steps(40),
                 calls=[Call(idx=i, step_idx=i,
                             cost_usd=(1.0 if i == 0 else 0.0))
                        for i in range(40)])
    assert frontload.frontload_step_index(moving)["status"] == "ok"


def test_a_flat_run_scores_exactly_a_quarter_at_every_length():
    """E2's v2.1 property, inherited. `ceil` alone manufactured a swing the
    size of E2's whole observed range, so this is not a nicety."""
    for n in (8, 9, 11, 12, 17, 31, 40):
        run = Run(run_id="x", arm="a", source="t", steps=_steps(n),
                  calls=[Call(idx=i, step_idx=i, cost_usd=1.0)
                         for i in range(n)])
        reading = frontload.frontload_step_index(run)
        assert reading["status"] == "ok", (n, reading)
        assert round(float(reading["value"]), 12) == 0.25, (n, reading)


# --------------------------------------------------------------------------
# The live legs.
# --------------------------------------------------------------------------

@pytest.fixture(scope="module")
def legs():
    return {r["leg"]: r for r in frontload.live_legs()}


def test_the_live_arm_is_not_front_loaded_on_the_step_axis(legs):
    """These three legs evaluate, and none of them front-loads.

    The two that read exactly 0.0 are not a bug: the live arm spends its first
    five or six actions on free environment probing and takes its first priced
    decision at step 6, which is past the head on both legs.
    """
    r2 = legs["20260731T1310Z-A3-level2-carried-r2"]
    r3 = legs["20260731T1430Z-A3-level2-carried-r3"]
    l1 = legs["20260731T1500Z-A3-sk48-carried-l1"]
    assert r2["status"] == "ok" and r2["value"] == 0.0
    # 0.132198 until theoria-arm 82e8e25e rewrote r3's curves.json (30 -> 31
    # rows, n_steps 31 -> 35, $11.761053 -> $13.439862).  A longer axis moves
    # the head right and re-attributes the bill, so the index moved with it.
    assert r3["status"] == "ok" and round(r3["value"], 6) == 0.115685
    assert l1["status"] == "ok" and l1["value"] == 0.0
    for leg in (r2, r3, l1):
        assert leg["value"] < 0.25, leg          # below a flat bill


def test_the_zero_readings_survive_the_legs_own_action_count(legs):
    """A stated limitation, measured rather than asserted -- and it is tight.

    `n_steps` is `max(step_idx) + 1`, and the archive stamps a step ordinal
    only where a decision was taken, so the axis is a **lower bound** on the
    actions the leg really took. A longer axis moves the head right and could
    pull the first priced step into it, turning a 0.0 into a positive number.

    The first draft of this test asserted the readings survived *twice* the
    recorded axis. They do not: the sk48 leg's break-even is 24 steps and
    twice its recorded axis is 38. So the claim is made against the number the
    leg actually reports -- `actions_taken` summed over its own rows -- and the
    margin is asserted so it cannot silently shrink to nothing.
    """
    import json
    margins = {}
    for slug in ("20260731T1310Z-A3-level2-carried-r2",
                 "20260731T1500Z-A3-sk48-carried-l1"):
        path = os.path.join(REPO, "theoria-arm", "runs", slug, "curves.json")
        with open(path, encoding="utf-8") as fh:
            rows = json.load(fh)["rows"]
        first_priced = min(int(r["step_idx"]) for r in rows
                           if float(r.get("usd") or 0.0) > 0)
        actions = sum(int(r.get("actions_taken") or 0) for r in rows)
        # The axis length at which the head first reaches the first priced
        # step, i.e. at which the reading stops being 0.0.
        break_even = first_priced / frontload.FRONTLOAD_K
        assert actions < break_even, (slug, actions, break_even)
        margins[slug] = break_even - actions
    assert margins["20260731T1310Z-A3-level2-carried-r2"] == 11.0
    # Three actions of margin. Stated in the report, not buried here.
    assert margins["20260731T1500Z-A3-sk48-carried-l1"] == 3.0


def test_the_first_leg_is_refused_for_being_free(legs):
    leg = legs["20260731T1240Z-A3-level2-carried"]
    assert leg["status"] == "thin"
    assert leg["value"] is None


def test_process_1_has_no_pairs(legs):
    """More evaluable legs do not buy a pair, which is the whole point.

    `n_evaluable` was 3 when this was written; eight new theoria-arm legs
    (R1/R1b/R2/R2b x g50t/sk48) have landed since, so 10 legs are read.  Eight
    evaluated until S46 added G6, which refuses a leg whose `curves.json` does
    not certify that it accounts for the leg's billed calls and dollars; the
    two R1 legs do not, so seven evaluate now.  The verdict is unchanged and
    cannot be moved by replication on this side: the endpoint is a paired
    difference and there is still no control arm on any of these games, so
    `n_paired_games` stays 0 whatever `n_evaluable` does.
    """
    material = frontload.paired_material(list(legs.values()))
    assert material["n_evaluable"] == 7
    assert material["n_paired_games"] == 0
    assert material["control_arm_legs"] == 0
    assert material["min_attainable_p"] is None
    assert material["verdict"].startswith("no-data")
    # The count may not be read as that many clean legs: six of the seven
    # rebuilt their step axis from a join the archive itself calls degraded.
    assert material["n_evaluable_by_join_confidence"] == {
        "degraded": 6, "exact": 1}


def test_a_curve_that_does_not_account_for_the_bill_is_not_a_zero(legs):
    """G6 (S46). The defect S46 was opened for, one artefact further on.

    `20260731T231654Z-R1-sk48-b` published `total cost is zero` for a leg the
    proxy ledger bills three calls and $7.6085275 for: its `curves.json`
    totals $0.00 over two rows claiming zero model calls, and G2 reported that
    sum as a fact about the leg.  `20260731T231654Z-R1-g50t-a` is the milder
    form -- it read `ok` at 0.0 off a curve $0.005 short of the ledger.
    Neither certifies `accounts_for_every_billed_call`, and neither may be
    read as a number now.
    """
    for slug in ("20260731T231654Z-R1-sk48-b", "20260731T231654Z-R1-g50t-a"):
        leg = legs[slug]
        assert leg["accounts_for_the_bill"] is False
        assert leg["status"] == "unsound"
        assert leg["value"] is None
        assert "does not certify" in leg["reason"]
        assert "total cost is zero" not in leg["reason"]

    # And the gate is on the money, not on the join: every leg whose curve does
    # account for the bill keeps its reading, including the six whose turn
    # spine the archive calls degraded. Refusing those would convert readings
    # that point against C2 into silence after seeing which way they point,
    # which `freeze/STATS_RULES.md` §8 seals off.
    kept = [r for r in legs.values()
            if r.get("join_confidence") == "degraded" and r["status"] == "ok"]
    assert len(kept) == 6


def test_the_artefact_is_byte_reproducible(tmp_path):
    first = frontload.serialise(frontload.build())
    second = frontload.serialise(frontload.build())
    assert first == second
    out = frontload.write(str(tmp_path / "e2l.json"))
    with open(out, encoding="utf-8") as fh:
        assert fh.read() == first


def test_neither_generator_will_write_into_the_frozen_directory(tmp_path):
    frozen = os.path.join(REPO, "battery", "artifacts", "e2l.json")
    for writer in (frontload.write, threat.write):
        with pytest.raises(ValueError, match="frozen"):
            writer(frozen)
