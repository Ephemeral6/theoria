"""Framework change A -- probe economics. Offline; no key, no network, no model.

The measurement that motivates this file is in
`runs/20260801T0000Z-A-probe-economics/MEASUREMENT.json`: across the four live
legs of 2026-07-31, 56 probes were designed, 52 completed, the frontier never
shrank once, 47 of the 52 landed off the frontier entirely, and 18 were exact
repeats of an experiment already run.

Every refusal below has a test that watches it say **no**, and a matching test
that watches it stay silent when the change is switched off. A gate that has
only ever been seen to allow has not been shown to gate anything.
"""

import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(HERE)
if ARM not in sys.path:
    sys.path.insert(0, ARM)

import _bootstrap                                     # noqa: E402,F401

from inner import probe as probe_beat                 # noqa: E402
from inner.probe import ProbeEconomy, ProbeEconomyConfig   # noqa: E402


def _design(action=("key", 2), bits=0.9, partition=None, n_hypotheses=16):
    return {
        "n_hypotheses": n_hypotheses,
        "best": {"action": list(action), "entropy_bits": bits, "n_classes": 2,
                 "partition": partition or {"aaa": ["manual", "without_x"],
                                            "bbb": ["inert"]}},
    }


def _result(survived, refuted):
    return {"survived": list(survived), "refuted": list(refuted)}


class _H:
    def __init__(self, hid):
        self.id = hid
        self.description = hid


# ------------------------------------------------------- the switch is off
def test_the_default_is_the_old_behaviour():
    """Change A must be inert until a round turns it on."""
    assert ProbeEconomyConfig().enabled is False
    assert ProbeEconomy().enabled is False


def test_the_environment_switch_is_a_positive_whitelist():
    """A misspelt switch must not silently enable the thing being measured."""
    assert ProbeEconomyConfig.from_env({}).enabled is False
    for junk in ("banana", "0", "false", "no", "off", "", "  ", "2", "TRUE!"):
        assert ProbeEconomyConfig.from_env(
            {"THEORIA_PROBE_ECONOMY": junk}).enabled is False, junk
    for yes in ("1", "true", "TRUE", "yes", "on", " On "):
        assert ProbeEconomyConfig.from_env(
            {"THEORIA_PROBE_ECONOMY": yes}).enabled is True, yes


def test_a_bad_numeric_override_does_not_crash_or_change_the_default():
    cfg = ProbeEconomyConfig.from_env({"THEORIA_PROBE_ECONOMY": "1",
                                       "THEORIA_PROBE_OFF_FRONTIER_STOP": "3.7"})
    assert cfg.enabled is True
    assert cfg.off_frontier_stop == ProbeEconomyConfig().off_frontier_stop


def test_disabled_never_refuses_anything_it_has_every_reason_to_refuse():
    """The pass-through proof.

    This economy has fired the identical experiment, has a nine-probe
    off-frontier streak, has blown any cap, and splits fewer bits than any
    floor. Disabled, it allows all of it -- which is what "old behaviour as
    default" has to mean.
    """
    econ = ProbeEconomy(config=ProbeEconomyConfig(enabled=False))
    design = _design(bits=0.0001)
    econ.record_fired(design)
    econ.consecutive_off_frontier = 9
    econ.fired_this_generation = 99
    allowed, why = econ.gate(design, n_frontier=1)
    assert allowed is True and why == ""


def test_disabled_does_not_filter_the_frontier():
    econ = ProbeEconomy(config=ProbeEconomyConfig(enabled=False))
    econ.retired = {"without_x"}
    kept = econ.filter_hypotheses([_H("manual"), _H("inert"), _H("without_x")])
    assert [h.id for h in kept] == ["manual", "inert", "without_x"]


# ------------------------------------------------- negative control: repeats
def test_repeat_suppression_says_no():
    """32.1% of the measured probes were this. The gate must catch it."""
    econ = ProbeEconomy(config=ProbeEconomyConfig(enabled=True))
    econ.note_frontier(["manual", "inert", "without_x"])
    design = _design()

    allowed, _ = econ.gate(design, n_frontier=16)
    assert allowed is True, "the first firing of an experiment is information"
    econ.record_fired(design)

    allowed, why = econ.gate(design, n_frontier=16)
    assert allowed is False
    assert "already been run" in why


def test_the_same_action_against_a_different_frontier_is_a_different_experiment():
    """The signature is action *and* partition. Keying on the action alone
    would suppress a genuinely new question that happens to reuse a key."""
    econ = ProbeEconomy(config=ProbeEconomyConfig(enabled=True))
    econ.note_frontier(["manual", "inert"])
    first = _design(action=("key", 2), partition={"aaa": ["manual"], "bbb": ["inert"]})
    econ.record_fired(first)
    second = _design(action=("key", 2), partition={"aaa": ["manual", "inert"],
                                                   "ccc": ["without_y"]})
    allowed, _ = econ.gate(second, n_frontier=16)
    assert allowed is True


def test_repeat_suppression_can_be_turned_off_on_its_own():
    econ = ProbeEconomy(config=ProbeEconomyConfig(enabled=True,
                                                  suppress_repeats=False,
                                                  max_per_generation=0))
    econ.note_frontier(["manual", "inert"])
    design = _design()
    econ.record_fired(design)
    allowed, _ = econ.gate(design, n_frontier=16)
    assert allowed is True


# -------------------------------------------- negative control: off-frontier
def test_the_off_frontier_streak_retires_the_probe_class():
    """90.4% of completed probes landed off the frontier and the loop kept
    firing. Three in a row is enough: the world is deterministic, so an
    observation nobody predicted is not noise, it is a wrong frontier."""
    econ = ProbeEconomy(config=ProbeEconomyConfig(enabled=True,
                                                  max_per_generation=0))
    econ.note_frontier(["manual", "inert", "without_x"])
    # Three *distinct* experiments, so the repeat rule cannot be what refuses.
    # Isolating the rule under test is the whole point of a negative control.
    for i in range(3):
        distinct = _design(action=("key", i),
                           partition={"obs%d" % i: ["manual"], "zzz": ["inert"]})
        allowed, why = econ.gate(distinct, n_frontier=16)
        assert allowed is True, "refused too early at %d: %s" % (i, why)
        econ.record_fired(distinct)
        learnt = econ.observe(_result(survived=[], refuted=["manual", "inert"]))
        assert learnt["off_frontier"] is True

    allowed, why = econ.gate(_design(action=("key", 9), bits=0.5,
                                     partition={"fresh": ["manual"], "q": ["inert"]}),
                             n_frontier=16)
    assert allowed is False
    assert "off the frontier" in why and "theorize, do not probe" in why


def test_an_on_frontier_result_resets_the_streak():
    """The stop is not a ratchet. A probe that lands where the theory said it
    would is evidence the frontier is sound again."""
    econ = ProbeEconomy(config=ProbeEconomyConfig(enabled=True,
                                                  max_per_generation=0))
    econ.note_frontier(["manual", "inert", "without_x"])
    econ.observe(_result([], ["manual", "inert"]))
    econ.observe(_result([], ["manual", "inert"]))
    assert econ.consecutive_off_frontier == 2
    econ.observe(_result(["manual"], ["inert"]))
    assert econ.consecutive_off_frontier == 0
    allowed, _ = econ.gate(_design(), n_frontier=16)
    assert allowed is True


def test_off_frontier_stop_zero_disables_that_rule_alone():
    econ = ProbeEconomy(config=ProbeEconomyConfig(enabled=True,
                                                  off_frontier_stop=0,
                                                  max_per_generation=0,
                                                  suppress_repeats=False))
    econ.note_frontier(["manual", "inert"])
    for _ in range(20):
        econ.observe(_result([], ["manual"]))
    allowed, _ = econ.gate(_design(), n_frontier=16)
    assert allowed is True


# ------------------------------------------------ negative control: the cap
def test_the_per_generation_cap_says_no():
    econ = ProbeEconomy(config=ProbeEconomyConfig(enabled=True,
                                                  max_per_generation=2,
                                                  suppress_repeats=False,
                                                  off_frontier_stop=0))
    econ.note_frontier(["manual", "inert"])
    for _ in range(2):
        allowed, _ = econ.gate(_design(), n_frontier=16)
        assert allowed is True
        econ.record_fired(_design())
    allowed, why = econ.gate(_design(), n_frontier=16)
    assert allowed is False
    assert "probe budget for this frontier is spent" in why


def test_theorize_reopens_probing_by_changing_the_frontier():
    """The cap is per generation, and a generation is the hypothesis-id set.
    A new rule in the manual is a new question, and buys a fresh budget."""
    econ = ProbeEconomy(config=ProbeEconomyConfig(enabled=True,
                                                  max_per_generation=1,
                                                  off_frontier_stop=0))
    econ.note_frontier(["manual", "inert"])
    econ.record_fired(_design())
    allowed, _ = econ.gate(_design(), n_frontier=16)
    assert allowed is False

    opened = econ.note_frontier(["manual", "inert", "without_newrule"])
    assert opened is True and econ.generation == 2
    allowed, _ = econ.gate(_design(), n_frontier=16)
    assert allowed is True, "a changed manual must re-open probing"


def test_an_unchanged_frontier_does_not_open_a_generation():
    econ = ProbeEconomy(config=ProbeEconomyConfig(enabled=True))
    assert econ.note_frontier(["manual", "inert"]) is True
    assert econ.note_frontier(["inert", "manual"]) is False, "order is not identity"
    assert econ.generation == 1


# ---------------------------------------- negative control: collapsed frontier
def test_a_collapsed_frontier_is_refused():
    econ = ProbeEconomy(config=ProbeEconomyConfig(enabled=True))
    econ.note_frontier(["manual"])
    allowed, why = econ.gate(_design(n_hypotheses=1), n_frontier=1)
    assert allowed is False
    assert "collapsed" in why


# ------------------------------------------------- the floor, and its honesty
def test_the_default_bits_floor_is_a_deliberate_no_op():
    """Every one of the 56 measured probes scored 0.5436--1.0000 bits. A floor
    would not have cut one of them, so the default is 0.0 and this test is the
    place that records why -- not a comment nobody reruns."""
    econ = ProbeEconomy(config=ProbeEconomyConfig(enabled=True))
    econ.note_frontier(["manual", "inert"])
    for bits in (0.5435644432, 0.5746356978, 0.6962122601, 0.8812908992, 1.0):
        allowed, why = econ.gate(_design(bits=bits, partition={"z%s" % bits: ["manual"],
                                                              "y": ["inert"]}),
                                 n_frontier=16)
        assert allowed is True, "%s refused: %s" % (bits, why)


def test_the_bits_floor_says_no_when_a_round_sets_one():
    econ = ProbeEconomy(config=ProbeEconomyConfig(enabled=True, min_bits=0.7))
    econ.note_frontier(["manual", "inert"])
    allowed, why = econ.gate(_design(bits=0.5436), n_frontier=16)
    assert allowed is False and "floor is 0.7000" in why
    allowed, _ = econ.gate(_design(bits=0.71), n_frontier=16)
    assert allowed is True


# ------------------------------------------------- the frontier finally moves
def test_refutations_carry_forward_and_the_frontier_shrinks():
    """The defect in one test: 56 probes, zero shrink. Here it shrinks."""
    econ = ProbeEconomy(config=ProbeEconomyConfig(enabled=True))
    frontier = [_H("manual"), _H("inert"), _H("without_x"), _H("without_y")]
    econ.note_frontier([h.id for h in frontier])
    assert len(econ.filter_hypotheses(frontier)) == 4

    econ.observe(_result(survived=["manual", "without_y"],
                         refuted=["inert", "without_x"]))
    kept = [h.id for h in econ.filter_hypotheses(frontier)]
    assert kept == ["manual", "without_y"], kept


def test_the_manual_is_never_retired_from_its_own_frontier():
    """`manual_survived` is what drives theorize. A frontier that has quietly
    stopped mentioning the manual cannot report it."""
    econ = ProbeEconomy(config=ProbeEconomyConfig(enabled=True))
    frontier = [_H("manual"), _H("inert")]
    econ.note_frontier([h.id for h in frontier])
    econ.observe(_result(survived=["inert"], refuted=["manual"]))
    assert "manual" not in econ.retired
    assert "manual" in [h.id for h in econ.filter_hypotheses(frontier)]


def test_an_off_frontier_result_retires_nobody():
    """The subtlety the measurement forces. When nothing survived, the
    partition was wrong -- "everyone is refuted" is a statement about the
    frontier, not about its members, and retiring all of them would empty a
    frontier on evidence that does not support emptying it."""
    econ = ProbeEconomy(config=ProbeEconomyConfig(enabled=True))
    frontier = [_H("manual"), _H("inert"), _H("without_x")]
    econ.note_frontier([h.id for h in frontier])
    econ.observe(_result(survived=[], refuted=["manual", "inert", "without_x"]))
    assert econ.retired == set()
    assert len(econ.filter_hypotheses(frontier)) == 3


def test_filtering_never_returns_an_empty_frontier():
    econ = ProbeEconomy(config=ProbeEconomyConfig(enabled=True))
    frontier = [_H("without_x"), _H("without_y")]
    econ.note_frontier([h.id for h in frontier])
    econ.retired = {"without_x", "without_y"}
    assert len(econ.filter_hypotheses(frontier)) == 2


def test_a_new_generation_forgets_the_retirements():
    econ = ProbeEconomy(config=ProbeEconomyConfig(enabled=True))
    econ.note_frontier(["manual", "inert", "without_x"])
    econ.observe(_result(["manual"], ["inert", "without_x"]))
    assert econ.retired == {"inert", "without_x"}
    econ.note_frontier(["manual", "inert", "without_x", "without_z"])
    assert econ.retired == set() and econ.fired == set()
    assert econ.fired_this_generation == 0
    assert econ.consecutive_off_frontier == 0


def test_a_retired_survivor_cannot_reset_the_off_frontier_streak():
    """The hazard behind `loop.py` building predictions from the *filtered*
    frontier. If a hypothesis this generation already retired is still in the
    prediction set, it can turn up in `survived`, and a result that was really
    off the frontier reads as on it -- silently resetting the streak that the
    off-frontier stop exists to count.

    The economy cannot enforce that by itself; it can only be consistent about
    which frontier it was handed. This pins the consequence: given the filtered
    frontier, an empty `survived` stays empty.
    """
    econ = ProbeEconomy(config=ProbeEconomyConfig(enabled=True))
    frontier = [_H("manual"), _H("inert"), _H("without_x")]
    econ.note_frontier([h.id for h in frontier])
    econ.observe(_result(survived=["manual"], refuted=["inert", "without_x"]))
    assert econ.retired == {"inert", "without_x"}

    live = [h.id for h in econ.filter_hypotheses(frontier)]
    assert live == ["manual"], live
    # A result reported over the live frontier only.
    learnt = econ.observe(_result(survived=[], refuted=["manual"]))
    assert learnt["off_frontier"] is True
    assert econ.consecutive_off_frontier == 1


# -------------------------------------------------- design() keeps its shape
def test_design_without_an_economy_is_unchanged():
    """The old report has no `economy` key, and neither does a disabled one.
    Downstream readers of `probes.jsonl` must not see the change until it is on.
    """
    from world import adapt                            # noqa: PLC0415

    namespace = _tiny_namespace()
    plain = probe_beat.design(namespace, namespace["initial_state"](),
                              [("key", 1), ("key", 2)])
    off = probe_beat.design(namespace, namespace["initial_state"](),
                            [("key", 1), ("key", 2)],
                            economy=ProbeEconomy())
    assert "economy" not in plain
    assert "economy" not in off
    assert json.dumps(plain, sort_keys=True) == json.dumps(off, sort_keys=True)


def test_design_with_an_enabled_economy_reports_the_frontier_it_used():
    namespace = _tiny_namespace()
    econ = ProbeEconomy(config=ProbeEconomyConfig(enabled=True))
    report = probe_beat.design(namespace, namespace["initial_state"](),
                               [("key", 1), ("key", 2)], economy=econ)
    assert report["economy"]["generation"] == 1
    assert report["economy"]["n_before"] == report["economy"]["n_after"]
    assert report["n_hypotheses"] == report["economy"]["n_after"]


def _tiny_namespace():
    """A two-cell world with one rule, enough to exercise `design` offline."""
    def initial_state():
        return {"v": 0}

    def step(state, action):
        kind, key = action
        if key == 1:
            return {"v": state["v"] + 1}
        return dict(state)

    def render(state):
        return [[state["v"] % 2]]

    def fired(state, action):
        return ["bump"] if action[1] == 1 else []

    return {"initial_state": initial_state, "step": step, "render": render,
            "fired": fired, "RULES": [("bump", None, None, None)]}


# ------------------------------------------------------------- the audit file
def test_the_report_is_readable_whether_or_not_the_change_is_on():
    for enabled in (False, True):
        econ = ProbeEconomy(config=ProbeEconomyConfig(enabled=enabled))
        econ.note_decision(allowed=False, reason="a repeat", step_idx=3)
        econ.note_decision(allowed=True, reason="", step_idx=4)
        blob = econ.as_json()
        assert blob["enabled"] is enabled
        assert blob["probes_allowed"] == 1 and blob["probes_refused"] == 1
        json.dumps(blob, sort_keys=True)      # must be serialisable


# ---------------------------------------------------- replay of the real legs
LEGS = ["20260731T1240Z-A3-level2-carried",
        "20260731T1310Z-A3-level2-carried-r2",
        "20260731T1430Z-A3-level2-carried-r3",
        "20260731T1500Z-A3-sk48-carried-l1"]


def _replay_reasons(config):
    """As `_replay`, but returns which rule refused, counted."""
    import collections                                 # noqa: PLC0415

    reasons = collections.Counter()
    for leg in LEGS:
        path = os.path.join(ARM, "runs", leg, "probes.jsonl")
        if not os.path.exists(path):
            pytest.skip("leg %s not in this checkout" % leg)
        rows = [json.loads(line) for line in open(path, encoding="utf-8")
                if line.strip()]
        results = {r["probe_id"]: r for r in rows if r.get("phase") == "result"}
        econ = ProbeEconomy(config=config)
        for row in rows:
            if row.get("phase") != "design":
                continue
            report = row.get("design") or {}
            econ.note_frontier([h["id"] for h in (report.get("hypotheses") or [])])
            allowed, why = econ.gate(
                report, n_frontier=int(report.get("n_hypotheses") or 0))
            if not allowed:
                if "off the frontier" in why:
                    reasons["off_frontier_stop"] += 1
                elif "already been run" in why:
                    reasons["repeat"] += 1
                elif "budget for this frontier" in why:
                    reasons["cap"] += 1
                elif "floor is" in why:
                    reasons["min_bits"] += 1
                else:
                    reasons["other:" + why[:30]] += 1
                continue
            econ.record_fired(report)
            result = results.get(row["probe_id"])
            if result is not None:
                econ.observe(result)
    return dict(reasons)


def _replay(config):
    """Re-run the four legs' recorded probe stream through a policy.

    The design reports and the results are on disk exactly as the live legs
    wrote them, and every decision the policy makes is a pure function of them,
    so this is a faithful counterfactual for the *gate* -- not for the run,
    which would have diverged after the first refusal. It is stated that way in
    the run's README as well.
    """
    fired = refused = 0
    for leg in LEGS:
        path = os.path.join(ARM, "runs", leg, "probes.jsonl")
        if not os.path.exists(path):
            pytest.skip("leg %s not in this checkout" % leg)
        rows = [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]
        results = {r["probe_id"]: r for r in rows if r.get("phase") == "result"}
        econ = ProbeEconomy(config=config)
        for row in rows:
            if row.get("phase") != "design":
                continue
            report = row.get("design") or {}
            ids = [h["id"] for h in (report.get("hypotheses") or [])]
            econ.note_frontier(ids)
            allowed, why = econ.gate(report,
                                     n_frontier=int(report.get("n_hypotheses") or 0))
            if not allowed:
                refused += 1
                continue
            fired += 1
            econ.record_fired(report)
            result = results.get(row["probe_id"])
            if result is not None:
                econ.observe(result)
    return fired, refused


def test_the_old_policy_refuses_none_of_the_fifty_six():
    """The baseline, stated as a number: today's gate has never said no."""
    fired, refused = _replay(ProbeEconomyConfig(enabled=False))
    assert (fired, refused) == (56, 0)


def test_the_new_policy_refuses_most_of_the_fifty_six():
    """And the change, stated as the same number."""
    fired, refused = _replay(ProbeEconomyConfig(enabled=True))
    assert fired + refused == 56
    assert refused >= 30, "expected the measured waste to be caught, got %d" % refused
    assert fired >= 8, "it must not refuse everything -- probing is not the enemy"


def test_every_rule_that_is_on_is_a_rule_that_bites():
    """Which rule refuses, pinned. Three of the four fire on the real legs; the
    bits floor fires zero times, which is what a 0.0 default means and is
    asserted here rather than assumed.

    This is also the guard against a rule that is on but dead: if one of these
    counts silently goes to zero, a rule stopped checking and the total would
    still look respectable.
    """
    reasons = _replay_reasons(ProbeEconomyConfig(enabled=True))
    assert reasons == {"off_frontier_stop": 19, "repeat": 12, "cap": 3}, reasons
    assert reasons.get("min_bits", 0) == 0

    # And with the change off, no rule fires at all.
    assert _replay_reasons(ProbeEconomyConfig(enabled=False)) == {}
