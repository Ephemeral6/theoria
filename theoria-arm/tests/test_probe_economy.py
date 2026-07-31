"""Framework change A -- probe economics. Offline; no key, no network, no model.

The measurement that motivates this file is in
`runs/20260801T0000Z-A-probe-economics/MEASUREMENT.json`: across the four live
legs of 2026-07-31, 56 probes were designed, 52 completed, the frontier never
shrank once, 47 of the 52 landed off the frontier entirely, and 18 were exact
repeats of an experiment already run.

**Where each of those is answered.** Two of the three are answered by
measurement plus an unconditional refusal in `inner/loop.py`, and are tested in
`test_probe_economics.py` (`information_gain_bits`, `vacuous_streak`,
`fingerprint`) and `test_probe_guard_in_the_loop.py` (the refusals themselves).
Refusing to re-ask a question the record already answered needs no switch and
no A/B leg, so it is on for every run.

This file is the third: **the frontier that never shrank.** `ProbeEconomy`
carries a probe's refutations forward within a generation so the next design is
over the hypotheses still standing, and that *is* a framework change -- it
alters what the arm reasons over -- so it ships behind `enabled`, default off,
with a leg that leaves it off to compare against.

Every refusal below has a test that watches it say **no**, and a matching test
that watches it stay silent when the change is switched off. A gate that has
only ever been seen to allow has not been shown to gate anything.
"""

import json
import os
import sys
import tempfile

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(HERE)
if ARM not in sys.path:
    sys.path.insert(0, ARM)

import _bootstrap                                     # noqa: E402,F401

from inner import probe as probe_beat                 # noqa: E402
from inner.loop import (MAX_PROBES_BETWEEN_THEORIZE,   # noqa: E402
                        MAX_VACUOUS_PROBES_IN_A_ROW)
from inner.probe import ProbeEconomy, ProbeEconomyConfig   # noqa: E402


def _design(action=("key", 2), bits=0.9, partition=None, n_hypotheses=16):
    return {
        "n_hypotheses": n_hypotheses,
        "best": {"action": list(action), "entropy_bits": bits, "n_classes": 2,
                 "partition": partition or {"aaa": ["manual", "without_x"],
                                            "bbb": ["inert"]}},
    }


def _result(survived, refuted, vacuous=None):
    row = {"survived": list(survived), "refuted": list(refuted)}
    if vacuous is not None:
        row["frontier_vacuous"] = vacuous
    return row


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
                                       "THEORIA_PROBE_MIN_BITS": "three-ish"})
    assert cfg.enabled is True
    assert cfg.min_bits == ProbeEconomyConfig().min_bits


def test_a_good_numeric_override_is_taken():
    cfg = ProbeEconomyConfig.from_env({"THEORIA_PROBE_ECONOMY": "1",
                                       "THEORIA_PROBE_MIN_BITS": "0.7"})
    assert cfg.enabled is True and cfg.min_bits == pytest.approx(0.7)


def test_disabled_never_refuses_anything_it_has_every_reason_to_refuse():
    """The pass-through proof.

    This economy is looking at a collapsed frontier splitting fewer bits than
    the floor its own config sets. Disabled, it allows all of it -- which is
    what "old behaviour as default" has to mean.
    """
    econ = ProbeEconomy(config=ProbeEconomyConfig(enabled=False, min_bits=0.9))
    econ.record_fired()
    allowed, why = econ.gate(_design(bits=0.0001), n_frontier=1)
    assert allowed is True and why == ""


def test_disabled_does_not_filter_the_frontier():
    econ = ProbeEconomy(config=ProbeEconomyConfig(enabled=False))
    econ.retired = {"without_x"}
    kept = econ.filter_hypotheses([_H("manual"), _H("inert"), _H("without_x")])
    assert [h.id for h in kept] == ["manual", "inert", "without_x"]


# ------------------------------------------- what this class no longer owns
def test_the_two_unconditional_rules_are_not_configurable_from_here():
    """The merge's single-mechanism rule, pinned.

    "Stop after N off-frontier answers" and "do not buy the same experiment
    twice" are `inner/loop.py`'s, counted off what `ProbeLog` measures, and
    they apply to every leg. If a knob for either reappears on this dataclass
    there are two implementations of one rule again, and the leg that turns the
    economy off gets a quietly different policy.
    """
    fields = set(ProbeEconomyConfig.__dataclass_fields__)
    assert fields == {"enabled", "carry_refutations", "min_bits"}, fields
    assert (MAX_VACUOUS_PROBES_IN_A_ROW, MAX_PROBES_BETWEEN_THEORIZE) == (3, 4)


# ---------------------------------------- negative control: collapsed frontier
def test_a_collapsed_frontier_is_refused():
    """Only reachable once refutations are carried: the ablation frontier is
    rebuilt whole every turn, so before this change it could never collapse."""
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
        allowed, why = econ.gate(_design(bits=bits), n_frontier=16)
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
                         refuted=["inert", "without_x"], vacuous=False))
    kept = [h.id for h in econ.filter_hypotheses(frontier)]
    assert kept == ["manual", "without_y"], kept


def test_the_manual_is_never_retired_from_its_own_frontier():
    """`manual_survived` is what drives theorize. A frontier that has quietly
    stopped mentioning the manual cannot report it."""
    econ = ProbeEconomy(config=ProbeEconomyConfig(enabled=True))
    frontier = [_H("manual"), _H("inert")]
    econ.note_frontier([h.id for h in frontier])
    econ.observe(_result(survived=["inert"], refuted=["manual"], vacuous=False))
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
    econ.observe(_result(survived=[], refuted=["manual", "inert", "without_x"],
                         vacuous=True))
    assert econ.retired == set()
    assert len(econ.filter_hypotheses(frontier)) == 3


def test_observe_reads_the_measured_vacuity_rather_than_recounting_it():
    """One fact, one owner.

    `ProbeLog.record_result` decides vacuity -- the same computation that
    produces `information_gain_bits` and drives `vacuous_streak`. The economy
    reads that verdict off the row instead of forming a second opinion from
    `survived`, so the two can never disagree.
    """
    econ = ProbeEconomy(config=ProbeEconomyConfig(enabled=True))
    econ.note_frontier(["manual", "inert", "without_x"])

    # The row says vacuous, so nothing is retired -- even though `survived` is
    # non-empty here. That combination cannot arise in the loop, and that is
    # the point: if the two ever disagreed, the measurement wins.
    econ.observe({"survived": ["inert"], "refuted": ["without_x"],
                  "frontier_vacuous": True})
    assert econ.retired == set()

    # And when the row says on-frontier, the refutation is carried.
    econ.observe({"survived": ["inert"], "refuted": ["without_x"],
                  "frontier_vacuous": False})
    assert econ.retired == {"without_x"}


def test_a_row_written_before_the_field_existed_still_reads():
    """The four legs on disk predate `frontier_vacuous`; an empty `survived` is
    the same statement in the older vocabulary."""
    econ = ProbeEconomy(config=ProbeEconomyConfig(enabled=True))
    econ.note_frontier(["manual", "inert", "without_x"])
    assert econ.observe(_result([], ["manual", "inert"]))["off_frontier"] is True
    assert econ.retired == set()
    assert econ.observe(_result(["manual"], ["inert"]))["off_frontier"] is False
    assert econ.retired == {"inert"}


def test_filtering_never_returns_an_empty_frontier():
    econ = ProbeEconomy(config=ProbeEconomyConfig(enabled=True))
    frontier = [_H("without_x"), _H("without_y")]
    econ.note_frontier([h.id for h in frontier])
    econ.retired = {"without_x", "without_y"}
    assert len(econ.filter_hypotheses(frontier)) == 2


def test_a_new_generation_forgets_the_retirements():
    """A generation is the hypothesis-id set, so theorize -- and only theorize
    -- opens a new one. The retirements were refutations of an older theory."""
    econ = ProbeEconomy(config=ProbeEconomyConfig(enabled=True))
    econ.note_frontier(["manual", "inert", "without_x"])
    econ.record_fired()
    econ.observe(_result(["manual"], ["inert", "without_x"], vacuous=False))
    assert econ.retired == {"inert", "without_x"}

    opened = econ.note_frontier(["manual", "inert", "without_x", "without_z"])
    assert opened is True and econ.generation == 2
    assert econ.retired == set()
    assert econ.fired_this_generation == 0
    assert len(econ.filter_hypotheses(
        [_H("manual"), _H("inert"), _H("without_x"), _H("without_z")])) == 4


def test_an_unchanged_frontier_does_not_open_a_generation():
    econ = ProbeEconomy(config=ProbeEconomyConfig(enabled=True))
    assert econ.note_frontier(["manual", "inert"]) is True
    assert econ.note_frontier(["inert", "manual"]) is False, "order is not identity"
    assert econ.generation == 1


def test_generations_are_counted_even_with_the_change_off():
    """Counting is not a behaviour change, and a leg that ran with the economy
    off must still say on disk how many manuals it went through."""
    econ = ProbeEconomy(config=ProbeEconomyConfig(enabled=False))
    econ.note_frontier(["manual", "inert"])
    econ.note_frontier(["manual", "inert", "without_x"])
    assert econ.generation == 2


# ------------------------------- the experiment's identity survives the change
def test_the_fingerprint_does_not_move_when_the_frontier_shrinks():
    """The regression this merge exists to prevent.

    `fingerprint` names an experiment by hashing what every hypothesis
    predicted, which is how the pre-state gets into it. Feed it a frontier that
    this generation's refutations have already narrowed and the same action
    from the same state hashes differently -- so an experiment already bought
    reads as a new question. Replaying the four legs both ways measured it: 9
    repeats caught instead of 15, three more actions spent.

    `inner/loop.py` therefore hashes the *unfiltered* prediction set and scores
    survivorship on the live one, and `ProbeLog.record_design(identity=...)` is
    what keeps the two apart.
    """
    full = {"manual": "aaa", "inert": "bbb", "without_x": "aaa",
            "without_y": "ccc"}
    live = {"manual": "aaa", "inert": "bbb"}
    assert probe_beat.fingerprint(2, full) != probe_beat.fingerprint(2, live), (
        "if these were equal there would be nothing to guard against")

    log = probe_beat.ProbeLog(os.path.join(_tmpdir(), "probes.jsonl"))
    first = log.record_design(action=2, design_report=_design(),
                              predictions=full, step_idx=0)
    # Same action, same state, but the economy has since retired two
    # hypotheses. Scored over `live`; still recognisably the same experiment.
    assert log.already_asked(2, full) == first
    second = log.record_design(action=2, design_report=_design(),
                               predictions=live, step_idx=1, identity=full)
    rows = [json.loads(line) for line
            in open(log.path, encoding="utf-8").read().splitlines() if line]
    assert rows[1]["repeat_of"] == first, rows[1]
    assert rows[1]["probe_id"] == second
    assert rows[1]["predictions"] == live, (
        "the scored frontier is still the live one")
    assert rows[1]["fingerprint_over"] == sorted(full), (
        "a row whose fingerprint covers more than its own `predictions` has to "
        "say so, or the hash cannot be recomputed from the record")
    assert "fingerprint_over" not in rows[0], (
        "and it is absent when the two agree, so every row the arm has already "
        "written keeps its shape")


def test_identity_defaults_to_the_predictions_it_is_given():
    """The pre-economy call, unchanged: no `identity`, no behaviour change."""
    preds = {"manual": "aaa", "inert": "bbb"}
    log = probe_beat.ProbeLog(os.path.join(_tmpdir(), "probes.jsonl"))
    log.record_design(action=2, design_report=_design(), predictions=preds,
                      step_idx=0)
    assert log.already_asked(2, preds) == "P-01"


def _tmpdir():
    return tempfile.mkdtemp(prefix="probe-econ-")


# -------------------------------------------------- design() keeps its shape
def test_design_without_an_economy_is_unchanged():
    """The old report has no `economy` key, and neither does a disabled one.
    Downstream readers of `probes.jsonl` must not see the change until it is on.
    """
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


def _bucket(reason):
    for needle, name in (("empty posterior", "vacuous_streak"),
                         ("the same experiment", "repeat"),
                         ("since the last adjudication", "cap"),
                         ("collapsed", "collapsed"),
                         ("floor is", "min_bits")):
        if needle in reason:
            return name
    return "other:" + reason[:30]


def _replay(config, guards=True):
    """Re-run the four legs' recorded probe stream through the merged policy.

    Returns ``(fired, refused, {reason: count})``.

    The design reports, the predictions and the observations are on disk
    exactly as the live legs wrote them, and every decision the policy makes is
    a pure function of them, so this is a faithful counterfactual for the
    *decision* -- not for the run, which would have diverged after the first
    refusal. It is stated that way in the run's README as well.

    Two modelling choices, both stated so a reader can discount them:

    * `guards=False` is the 2026-07-31 code -- neither half of the policy
      existed, so nothing is ever refused. It is where the 56 comes from, not a
      configuration anything can be run in today.
    * The legs recorded no theorize events, so the replay rearms the loop's
      counters when the hypothesis-id set changes. A changed ablation set is
      observable proof the manual was adjudicated; a theorize that rewrote only
      prose is not visible here, so the cap's count is an upper bound.
    """
    import collections                                # noqa: PLC0415

    reasons = collections.Counter()
    fired = refused = 0
    for leg in LEGS:
        path = os.path.join(ARM, "runs", leg, "probes.jsonl")
        if not os.path.exists(path):
            pytest.skip("leg %s not in this checkout" % leg)
        rows = [json.loads(line) for line in open(path, encoding="utf-8")
                if line.strip()]
        results = {r["probe_id"]: r for r in rows if r.get("phase") == "result"}
        econ = ProbeEconomy(config=config)
        asked = {}                       # ProbeLog.asked
        vacuous_streak = 0               # ProbeLog.vacuous_streak
        since_theorize = 0               # TheoriaArm._probes_since_theorize
        for row in rows:
            if row.get("phase") != "design":
                continue
            report = row.get("design") or {}
            ids = [h["id"] for h in (report.get("hypotheses") or [])]
            if econ.note_frontier(ids):
                since_theorize = vacuous_streak = 0
            live = [h.id for h in econ.filter_hypotheses([_H(i) for i in ids])]

            # -- the economy's half, decided on the design report alone
            allowed, why = econ.gate(report, n_frontier=len(live))
            refusal = None if allowed else why

            identity = dict(row.get("predictions") or {})
            predictions = {k: v for k, v in identity.items() if k in live}

            # -- the loop's half, decided on what ProbeLog measures
            if refusal is None and guards:
                mark = probe_beat.fingerprint(row.get("action"), identity)
                if vacuous_streak >= MAX_VACUOUS_PROBES_IN_A_ROW:
                    refusal = "vacuous streak: empty posterior"
                elif mark in asked:
                    refusal = "the same experiment as %s" % asked[mark]
                elif since_theorize >= MAX_PROBES_BETWEEN_THEORIZE:
                    refusal = "spent since the last adjudication"

            if refusal is not None:
                refused += 1
                reasons[_bucket(refusal)] += 1
                continue

            fired += 1
            asked.setdefault(
                probe_beat.fingerprint(row.get("action"), identity),
                row["probe_id"])
            since_theorize += 1
            econ.record_fired()

            result = results.get(row["probe_id"])
            if result is None:
                continue
            observed = result.get("observed")
            _gain, vacuous = probe_beat.information_gain_bits(predictions,
                                                             observed)
            vacuous_streak = vacuous_streak + 1 if vacuous else 0
            econ.observe({
                "survived": sorted(h for h, p in predictions.items()
                                   if p == observed),
                "refuted": sorted(h for h, p in predictions.items()
                                  if p != observed),
                "frontier_vacuous": vacuous})
    return fired, refused, dict(reasons)


def test_the_old_policy_refuses_none_of_the_fifty_six():
    """The baseline, stated as a number: the 2026-07-31 gate never said no."""
    fired, refused, reasons = _replay(ProbeEconomyConfig(enabled=False),
                                      guards=False)
    assert (fired, refused, reasons) == (56, 0, {})


def test_the_merged_policy_refuses_thirty_four_of_the_fifty_six():
    """And the change, stated as the same number."""
    fired, refused, _reasons = _replay(ProbeEconomyConfig(enabled=True))
    assert fired + refused == 56
    assert (fired, refused) == (22, 34)
    assert fired >= 8, "it must not refuse everything -- probing is not the enemy"


def test_which_rule_refuses_is_pinned_and_does_not_move_with_the_switch():
    """Which rule refuses, pinned -- and the merge's central claim.

    Turning the economy on must not change *which experiments are the same
    experiment*. The two loop rules are measurements of the record, so they
    count identically either way; the economy changes what the arm reasons
    over, not what it has already asked. If these two results ever diverge, the
    frontier filter has leaked back into the fingerprint.

    The cap is 0 here and that is not a dead rule: the vacuous streak and the
    fingerprint are both strictly earlier in the order and get there first on
    this data. `test_probe_guard_in_the_loop.py` watches the cap bite.
    """
    off = _replay(ProbeEconomyConfig(enabled=False))
    on = _replay(ProbeEconomyConfig(enabled=True))
    assert off == on, (off, on)
    assert on[2] == {"vacuous_streak": 19, "repeat": 15}, on[2]
    assert on[2].get("cap", 0) == 0
    assert on[2].get("min_bits", 0) == 0


def test_the_economys_own_floor_bites_when_a_round_sets_one():
    """The one rule that only exists on the economy side, measured on the real
    legs rather than asserted. At 0.7 bits it refuses 15 of the 56 outright,
    which is why the default is 0.0 and not "a number that looks careful"."""
    fired, refused, reasons = _replay(
        ProbeEconomyConfig(enabled=True, min_bits=0.7))
    assert fired + refused == 56
    assert reasons["min_bits"] == 15, reasons
    assert (fired, refused) == (19, 37)
