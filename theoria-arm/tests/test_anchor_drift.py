"""The drift check, watched saying "no drift" as often as it is watched saying "drift".

`armtools/anchor_drift.py` backfills a number nothing was computing: how often a
probe's frontier was anchored to a frame the world had already left. R2 measured
it once, by hand, on four legs (35 of 52). This module measures it for any leg,
and the whole value of that depends on three things being true rather than
merely being reported:

* **it says zero when there is none.** A detector only ever seen firing is a
  function that returns positive numbers. The self-consistent leg below -- the
  world *is* the manual, so the roll-forward cannot be wrong -- must come back
  0, and the mispredicting leg must come back exactly 1, on the probe the
  arithmetic says and not on any other.
* **it says nothing when it cannot look.** `theoria-arm/.gitignore` excludes
  `runs/*/trace.jsonl`, so in a clone the frames are gone. Every path that
  cannot measure must return `None` for all three members of the triple, and a
  refused leg must contribute nothing -- not a zero -- to the totals.
* **its agreement with R2 is not circular.** R2 read `before_hash` out of the
  trace row; this module lets `load_store` recompute it from the frames. The
  test that matters is that corrupting the *recorded* field moves the
  disagreement count and does not move the measurement.

The archive pins at the bottom skip themselves in a clone rather than pass
vacuously, and each says so by name.
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

from armtools import anchor_drift                     # noqa: E402
from world.frames import grid_hash                    # noqa: E402

RUNS = os.path.join(ARM, "runs")

# ------------------------------------------------------------------ a manual
#
# A 5x5 world with one mechanism the manual states exactly: a marker at (0, c)
# that moves one column right on ACTION1. Four actions from column 0 give five
# frames, every one of them distinct -- which the vacuity test below checks,
# because on a frozen world every hypothesis agrees and neither control could
# fail.

SIZE = 5


def _grid(marker_col):
    grid = [[0] * SIZE for _ in range(SIZE)]
    grid[0][marker_col] = 6
    return grid


class _State:
    def __init__(self, marker_col=0):
        self.marker_col = marker_col


def _namespace():
    def render(state):
        return _grid(state.marker_col)

    def step(state, action):
        kind, key = action
        if kind == "key" and key == 1:
            return _State(min(state.marker_col + 1, SIZE - 1))
        return _State(state.marker_col)

    def fired(state, action):
        kind, key = action
        if kind == "key" and key == 1:
            return ["advance__Marker_r0c%d" % state.marker_col]
        return []

    return {"render": render, "step": step, "fired": fired,
            "initial_state": lambda: _State(0),
            "RULES": [("advance__Marker_r0c%d" % c, None, None, None)
                      for c in range(SIZE)]}


#: Four ACTION1s walk the marker 0 -> 4 and stop there. A fifth would repeat
#: frame 4 and the frame-keyed mispredicting wrapper would have two places to
#: fire, which is a different experiment from the one described.
ACTIONS = [1, 1, 1, 1]

#: Break the transition out of world-frame 2. Probes P-01..P-03 roll over at
#: most two actions and are still anchored; only P-04 rolls over the broken one.
BREAK_AT = 2


def _leg(tmp, label, *, mispredict_at=None):
    out = os.path.join(tmp, label)
    built = anchor_drift.synthesise_leg(out, _namespace(), ACTIONS,
                                        mispredict_at=mispredict_at)
    return out, built


# ============================================ 1. absence is absence, not zero
def test_a_leg_without_its_trace_is_refused_and_measured_null_not_zero():
    """The clone's normal case, and the one a zero would silently misreport."""
    with tempfile.TemporaryDirectory() as tmp:
        leg, _ = _leg(tmp, "self")
        os.remove(os.path.join(leg, "trace.jsonl"))
        got = anchor_drift.measure_leg(leg)
    assert got["status"] == anchor_drift.NO_TRACE
    assert got["triple"] == {"probes": None, "drifted": None,
                             "drifted_and_off_frontier": None}
    assert 0 not in got["triple"].values()


def test_a_leg_without_probes_is_refused_and_measured_null_not_zero():
    with tempfile.TemporaryDirectory() as tmp:
        leg, _ = _leg(tmp, "self")
        os.remove(os.path.join(leg, "probes.jsonl"))
        got = anchor_drift.measure_leg(leg)
    assert got["status"] == anchor_drift.NO_PROBES
    assert all(v is None for v in got["triple"].values())


def test_a_directory_that_is_not_there_is_refused_rather_than_clean():
    with tempfile.TemporaryDirectory() as tmp:
        got = anchor_drift.measure_leg(os.path.join(tmp, "never-existed"))
    assert got["status"] == anchor_drift.NO_LEG
    assert all(v is None for v in got["triple"].values())


def test_a_refused_leg_contributes_nothing_to_the_totals():
    """A total that absorbs a refusal as 0 is worse than no total at all.

    The measured leg drifts once; adding a leg nobody could measure must leave
    that 1 alone and must raise `legs_refused`, not the denominator.
    """
    with tempfile.TemporaryDirectory() as tmp:
        anchor_drift.synthesise_leg(os.path.join(tmp, "broken"), _namespace(),
                                    ACTIONS, mispredict_at=BREAK_AT)
        os.makedirs(os.path.join(tmp, "gone"))
        alone = anchor_drift.measure(["broken"], tmp)
        withrefusal = anchor_drift.measure(["broken", "gone"], tmp)
    assert alone["totals"]["triple"] == withrefusal["totals"]["triple"]
    assert withrefusal["totals"]["legs_refused"] == 1
    assert withrefusal["totals"]["legs_measured"] == 1


def test_the_totals_are_null_when_every_leg_refused():
    """What a clone with no traces at all must print: nulls, not a clean sweep."""
    with tempfile.TemporaryDirectory() as tmp:
        got = anchor_drift.measure(["nothing-here", "nor-here"], tmp)
    assert got["totals"]["triple"] == {"probes": None, "drifted": None,
                                       "drifted_and_off_frontier": None}
    assert got["totals"]["legs_measured"] == 0


# =========================================== 2. the two synthetic negative legs
def test_the_self_consistent_leg_reports_no_drift():
    """The control that matters: the world is the manual, so nothing can drift.

    If this ever fails the check is reporting drift that is not there, and every
    number it has produced about the archive is an artefact of the check.
    """
    with tempfile.TemporaryDirectory() as tmp:
        leg, _ = _leg(tmp, "self")
        got = anchor_drift.measure_leg(leg)
    assert got["status"] == anchor_drift.MEASURED
    assert got["triple"]["probes"] == len(ACTIONS)
    assert got["triple"]["drifted"] == 0
    assert got["triple"]["drifted_and_off_frontier"] == 0
    assert got["anchored_to_world"] == len(ACTIONS)
    assert got["anchor_unknown"] == 0


def test_the_self_consistent_leg_is_not_a_frozen_world():
    """Vacuity guard for the test above.

    On a world that never changes, every frame hashes the same and "no drift"
    is true of any anchor whatsoever, including a broken one. The control is
    only worth its line if the frames it compares actually move.
    """
    with tempfile.TemporaryDirectory() as tmp:
        _, built = _leg(tmp, "self")
    assert built["world_frames_distinct"] == len(ACTIONS) + 1


def test_one_mispredicted_transition_is_seen_as_drift():
    with tempfile.TemporaryDirectory() as tmp:
        leg, _ = _leg(tmp, "broken", mispredict_at=BREAK_AT)
        got = anchor_drift.measure_leg(leg)
    assert got["status"] == anchor_drift.MEASURED
    assert got["triple"]["drifted"] > 0


def test_the_drift_lands_on_the_probe_the_arithmetic_says_and_no_other():
    """Not "it fired" but "it fired here", which is the difference between a
    detector and an alarm.

    `_roll_forward` replays actions 1..t-1 before probe t, so breaking the
    transition out of world-frame 2 leaves P-01..P-03 anchored (they roll over
    at most two actions) and desynchronises P-04 alone.
    """
    with tempfile.TemporaryDirectory() as tmp:
        leg, _ = _leg(tmp, "broken", mispredict_at=BREAK_AT)
        got = anchor_drift.measure_leg(leg)
    drifted = [r["probe_id"] for r in got["probes"] if r["drifted"]]
    assert drifted == ["P-04"]
    assert got["triple"]["drifted"] == 1


def test_the_mispredicting_leg_cannot_test_the_archives_implication():
    """Why `drifted => off_frontier` is *not* confirmed by these controls.

    The archive says 47 of 47 drifted probes came back off-frontier, and it is
    tempting to point at this leg and say the implication reproduces. It does
    not, and the reason is worth pinning so nobody claims it later: the
    mispredicting wrapper freezes the state, so at the drifted probes every
    hypothesis that consults `step` returns the frozen frame and the frontier
    collapses from two distinct predictions to **one**. Those probes are
    off-frontier because their frontier is a point, not because their anchor
    moved. The wrapper manufactures both facts, so it can witness neither.

    Asserted rather than mentioned, because a collapse that nothing looks at is
    a collapse the next reader will mistake for a result. `GAPS.md` GAP A23-3.

    The collapse is in fact **wider** than the drift, and by one probe exactly.
    At `P-03` the roll still lands on the world's frame -- the anchor is right --
    but the state it lands on is the frozen one, so `manual` and every ablation
    already agree with `inert` and the frontier is a point while the anchor is
    still correct. Drift arrives only at `P-04`. So this leg carries a
    collapsed-and-anchored probe and a collapsed-and-drifted probe and no
    drifted-and-uncollapsed one, which is precisely why it cannot separate the
    two.
    """
    with tempfile.TemporaryDirectory() as tmp:
        honest_dir, honest = _leg(tmp, "self")
        broken_dir, broken = _leg(tmp, "broken", mispredict_at=BREAK_AT)
        got = anchor_drift.measure_leg(broken_dir)

    assert honest["frontier_widths"] == [2]
    assert 1 in broken["frontier_widths"]
    collapsed = [r["probe_id"] for r in got["probes"]
                 if r["frontier_width_distinct"] == 1]
    drifted = [r["probe_id"] for r in got["probes"] if r["drifted"]]
    assert collapsed == ["P-03", "P-04"]
    assert drifted == ["P-04"]
    assert set(drifted) < set(collapsed), (
        "every drifted probe here is also a collapsed one, so off-frontier at "
        "a drifted probe is manufactured by the wrapper and witnesses nothing")


def test_the_measurement_does_not_move_when_the_world_answers_in_a_cascade():
    """A real ARC command returns 1--113 frames; the controls returned one.

    On a one-grid world every candidate reading of "the frame the world was
    showing" coincides -- first grid, last grid, the one in the middle -- so a
    control built only there tests none of them. With four grids per step the
    earlier ones are frames the world passed through and the anchor must still
    be the one it settled on. 26 of the 34 steps on `…-r3` are multi-frame, so
    this is the archive's normal case and not an exotic one.
    """
    with tempfile.TemporaryDirectory() as tmp:
        flat, flat_built = _leg(tmp, "flat")
        deep = os.path.join(tmp, "deep")
        deep_built = anchor_drift.synthesise_leg(deep, _namespace(), ACTIONS,
                                                 cascade=4)
        one = anchor_drift.measure_leg(flat)
        many = anchor_drift.measure_leg(deep)

        broken_flat = os.path.join(tmp, "bflat")
        broken_deep = os.path.join(tmp, "bdeep")
        anchor_drift.synthesise_leg(broken_flat, _namespace(), ACTIONS,
                                    mispredict_at=BREAK_AT)
        anchor_drift.synthesise_leg(broken_deep, _namespace(), ACTIONS,
                                    mispredict_at=BREAK_AT, cascade=4)
        broken_one = anchor_drift.measure_leg(broken_flat)
        broken_many = anchor_drift.measure_leg(broken_deep)

    assert flat_built["cascade"] == 1 and deep_built["cascade"] == 4
    assert one["triple"] == many["triple"]
    assert one["anchor_unknown"] == many["anchor_unknown"] == 0
    # …and the drifted case moves together too, so the agreement above is not
    # two zeros agreeing.
    assert broken_one["triple"] == broken_many["triple"]
    assert broken_many["triple"]["drifted"] == 1


def test_the_cascade_leg_really_carries_more_than_one_frame_per_step():
    """Vacuity guard: `cascade=4` must actually widen the steps."""
    with tempfile.TemporaryDirectory() as tmp:
        deep = os.path.join(tmp, "deep")
        anchor_drift.synthesise_leg(deep, _namespace(), ACTIONS, cascade=4)
        with open(os.path.join(deep, "trace.jsonl"), encoding="utf-8") as fh:
            rows = [json.loads(line) for line in fh if line.strip()]
    assert [row["n_frames"] for row in rows] == [4] * len(rows)
    assert all(row["grid_hash"] == grid_hash(row["frames"][-1])
               for row in rows)


# ================================== 3. the agreement with R2 is not circular
def test_the_measurement_ignores_the_recorded_before_hash():
    """`load_store` rebuilds the anchor from the frames; prove it is doing so.

    Corrupt every recorded `before_hash` in the trace. A reader that trusts the
    field would now see drift everywhere. This one must not move, and must
    report the corruption instead of absorbing it.
    """
    with tempfile.TemporaryDirectory() as tmp:
        leg, _ = _leg(tmp, "self")
        clean = anchor_drift.measure_leg(leg)

        path = os.path.join(leg, "trace.jsonl")
        with open(path, encoding="utf-8") as fh:
            rows = [json.loads(line) for line in fh if line.strip()]
        for row in rows:
            if row.get("before_hash"):
                row["before_hash"] = "0" * 16
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            for row in rows:
                fh.write(json.dumps(row, sort_keys=True,
                                    separators=(",", ":")) + "\n")
        corrupt = anchor_drift.measure_leg(leg)

    assert corrupt["triple"] == clean["triple"]
    assert clean["recorded_vs_recomputed_disagreements"] == []
    assert len(corrupt["recorded_vs_recomputed_disagreements"]) == len(ACTIONS)


def test_the_crosscheck_can_say_no():
    """The crosscheck's own negative control.

    A comparator that only ever reports EQUAL proves nothing about the two
    things compared. Hand it a `MEASUREMENT.json` whose numbers are wrong and
    it must disagree, per leg *and* per probe.
    """
    with tempfile.TemporaryDirectory() as tmp:
        leg, _ = _leg(tmp, "self")
        report = anchor_drift.measure(["self"], tmp)
        mine = report["legs"][0]

        honest = {
            "legs": [{"leg": "self",
                      "probes_completed": mine["triple"]["probes"],
                      "anchor_drifted": mine["triple"]["drifted"]}],
            "totals": {"probes_completed": mine["triple"]["probes"],
                       "anchor_drifted": mine["triple"]["drifted"],
                       "off_frontier_while_drifted":
                           mine["triple"]["drifted_and_off_frontier"]},
            "probes": [{"leg": "self", "probe_id": r["probe_id"],
                        "anchored": not r["drifted"],
                        "off_frontier": r["off_frontier"],
                        "observed": r["observed"]}
                       for r in mine["probes"]],
        }
        path = os.path.join(tmp, "MEASUREMENT.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(honest, fh)
        assert anchor_drift.crosscheck(report, path)["equal"] is True

        liar = json.loads(json.dumps(honest))
        liar["legs"][0]["anchor_drifted"] += 1
        liar["totals"]["anchor_drifted"] += 1
        liar["probes"][0]["anchored"] = not liar["probes"][0]["anchored"]
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(liar, fh)
        said = anchor_drift.crosscheck(report, path)

    assert said["equal"] is False
    assert said["per_leg_disagreements"]
    assert said["per_probe_disagreements"]
    assert said["totals_equal"] is False


def test_the_crosscheck_counts_the_probes_it_compared():
    """`equal: true` over zero probes compared is not agreement.

    R2's file names four legs; a crosscheck that silently matched none of them
    would report EQUAL while having read nothing.
    """
    with tempfile.TemporaryDirectory() as tmp:
        _leg(tmp, "self")
        report = anchor_drift.measure(["self"], tmp)
        path = os.path.join(tmp, "MEASUREMENT.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"legs": [], "totals": {"probes_completed": 0,
                                              "anchor_drifted": 0,
                                              "off_frontier_while_drifted": 0},
                       "probes": []}, fh)
        said = anchor_drift.crosscheck(report, path)
    assert said["probes_compared"] == 0
    assert said["equal"] is False


def test_the_crosscheck_notices_a_probe_only_one_side_has():
    """Agreement on the intersection is not agreement.

    The first draft compared `(leg, probe_id)` pairs the other side also
    carried and skipped the rest, so two readers could disagree about *which*
    probes exist and still both be EQUAL: swap one id for another and the
    totals match, the compared row matches, and nothing looks at the swap.
    """
    with tempfile.TemporaryDirectory() as tmp:
        _leg(tmp, "self")
        report = anchor_drift.measure(["self"], tmp)
        mine = report["legs"][0]
        rows = mine["probes"]
        theirs = {
            "legs": [{"leg": "self", "probes_completed": len(rows),
                      "anchor_drifted": 0}],
            "totals": {"probes_completed": len(rows), "anchor_drifted": 0,
                       "off_frontier_while_drifted": 0},
            "probes": [{"leg": "self",
                        # the swap: P-01 becomes a probe this reader never saw
                        "probe_id": "P-99" if r is rows[0] else r["probe_id"],
                        "anchored": not r["drifted"],
                        "off_frontier": r["off_frontier"],
                        "observed": r["observed"]} for r in rows],
        }
        path = os.path.join(tmp, "MEASUREMENT.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(theirs, fh)
        said = anchor_drift.crosscheck(report, path)

    assert said["totals_equal"] is True          # the totals do agree…
    assert said["per_probe_disagreements"] == []  # …and every compared row does
    assert said["probes_only_this_reader_has"] == [("self", "P-01")]
    assert said["probes_only_the_other_reader_has"] == [("self", "P-99")]
    assert said["equal"] is False                 # …and it is still not equal


def test_the_crosscheck_fails_on_a_leg_it_could_not_measure():
    """A refused leg must not be worth zero inside the comparison.

    Withhold one leg's trace and the earlier draft still said EQUAL over the
    remaining probes, while `legs_compared` went on naming the leg it had never
    opened. On the real archive that meant a four-leg crosscheck could report
    agreement having read three.
    """
    with tempfile.TemporaryDirectory() as tmp:
        _leg(tmp, "self")
        os.makedirs(os.path.join(tmp, "gone"))
        report = anchor_drift.measure(["self", "gone"], tmp)
        rows = report["legs"][0]["probes"]
        theirs = {
            "legs": [{"leg": "self", "probes_completed": len(rows),
                      "anchor_drifted": 0},
                     {"leg": "gone", "probes_completed": 0,
                      "anchor_drifted": 0}],
            "totals": {"probes_completed": len(rows), "anchor_drifted": 0,
                       "off_frontier_while_drifted": 0},
            "probes": [{"leg": "self", "probe_id": r["probe_id"],
                        "anchored": not r["drifted"],
                        "off_frontier": r["off_frontier"],
                        "observed": r["observed"]} for r in rows],
        }
        path = os.path.join(tmp, "MEASUREMENT.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(theirs, fh)
        said = anchor_drift.crosscheck(report, path)

    assert said["totals_equal"] is True
    assert said["legs_this_reader_could_not_measure"] == ["gone"]
    assert said["equal"] is False


# ======================================= 4. an unknown anchor is not a drift
def test_a_probe_the_trace_does_not_carry_is_unknown_rather_than_drifted():
    """R2 read a missing step as a drift (`None != hash`); this does not.

    The difference is invisible on the archive -- the pin below shows every
    completed probe there has its step -- but it is the difference between
    "the anchor was wrong" and "nobody knows where the anchor was", and only
    one of those is a finding.
    """
    with tempfile.TemporaryDirectory() as tmp:
        leg, _ = _leg(tmp, "self")
        path = os.path.join(leg, "trace.jsonl")
        with open(path, encoding="utf-8") as fh:
            rows = [json.loads(line) for line in fh if line.strip()]
        for row in rows:
            if row.get("note") == "P-02":
                row["note"] = "exploration"
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            for row in rows:
                fh.write(json.dumps(row, sort_keys=True,
                                    separators=(",", ":")) + "\n")
        got = anchor_drift.measure_leg(leg)

    orphan = [r for r in got["probes"] if r["probe_id"] == "P-02"][0]
    assert orphan["drifted"] is None
    assert got["anchor_unknown"] == 1
    assert got["triple"]["drifted"] == 0


def test_a_frontier_with_no_inert_hypothesis_is_unknown_rather_than_drifted():
    with tempfile.TemporaryDirectory() as tmp:
        leg, _ = _leg(tmp, "self")
        path = os.path.join(leg, "probes.jsonl")
        with open(path, encoding="utf-8") as fh:
            rows = [json.loads(line) for line in fh if line.strip()]
        for row in rows:
            if row.get("phase") == "design":
                row["predictions"].pop("inert", None)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            for row in rows:
                fh.write(json.dumps(row, sort_keys=True) + "\n")
        got = anchor_drift.measure_leg(leg)

    assert got["triple"]["drifted"] == 0
    assert got["anchor_unknown"] == len(ACTIONS)


def test_a_designed_probe_that_never_resolved_is_not_counted():
    """`probes` counts experiments that finished, as R2's `probes_completed`
    did. Two legs in the archive designed a probe the spend gate cut off before
    it ran, and counting those would have moved the denominator away from 52.
    """
    with tempfile.TemporaryDirectory() as tmp:
        leg, _ = _leg(tmp, "self")
        path = os.path.join(leg, "probes.jsonl")
        with open(path, encoding="utf-8") as fh:
            rows = [json.loads(line) for line in fh if line.strip()]
        rows = [r for r in rows
                if not (r["probe_id"] == "P-04" and r["phase"] == "result")]
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            for row in rows:
                fh.write(json.dumps(row, sort_keys=True) + "\n")
        got = anchor_drift.measure_leg(leg)

    assert got["probes_designed"] == len(ACTIONS)
    assert got["triple"]["probes"] == len(ACTIONS) - 1


def test_a_leg_with_no_resolved_probe_says_so_rather_than_reporting_clean():
    """0/0/0 reads like "measured, clean". Two archived legs are 0/0/0 because
    they resolved no probe at all, and the record has to be able to tell those
    apart.
    """
    with tempfile.TemporaryDirectory() as tmp:
        leg, _ = _leg(tmp, "self")
        path = os.path.join(leg, "probes.jsonl")
        with open(path, encoding="utf-8") as fh:
            rows = [json.loads(line) for line in fh if line.strip()]
        rows = [r for r in rows if r["phase"] != "result"]
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            for row in rows:
                fh.write(json.dumps(row, sort_keys=True) + "\n")
        got = anchor_drift.measure_leg(leg)

    assert got["triple"]["probes"] == 0
    assert got["note"] and "empty rather than clean" in got["note"]


def test_a_leg_whose_probes_got_no_answer_also_says_so():
    """`1/0/0` reads like "one probe, cleanly anchored".

    `20260801T001851Z-R1b-sk48-b` is exactly that shape, and what happened is
    that its single probe came back HTTP 400 with no frame at all. Its anchor
    genuinely did match, so `drifted: 0` is right -- but "off-frontier" means
    nothing about a probe the world never answered, and the record has to say
    which kind of zero this is.
    """
    with tempfile.TemporaryDirectory() as tmp:
        leg, _ = _leg(tmp, "self")
        path = os.path.join(leg, "probes.jsonl")
        with open(path, encoding="utf-8") as fh:
            rows = [json.loads(line) for line in fh if line.strip()]
        for row in rows:
            if row["phase"] == "result":
                row["observed"] = "none"
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            for row in rows:
                fh.write(json.dumps(row, sort_keys=True) + "\n")
        got = anchor_drift.measure_leg(leg)

    assert got["probes_without_an_answer"] == len(ACTIONS)
    assert got["note"] and "never answered" in got["note"]
    assert got["triple"]["drifted"] == 0


def test_two_trace_steps_claiming_one_probe_id_make_the_anchor_unknown():
    """`by_note` keeps the last step of a duplicated note.

    No leg in the archive has one, so this has never happened -- which is why
    it is worth deciding now rather than when it does. Picking the last of two
    and reporting a drift from it would be a guess dressed as a measurement, so
    the row degrades to unknown and the duplicate is named.
    """
    with tempfile.TemporaryDirectory() as tmp:
        leg, _ = _leg(tmp, "self")
        path = os.path.join(leg, "trace.jsonl")
        with open(path, encoding="utf-8") as fh:
            rows = [json.loads(line) for line in fh if line.strip()]
        for row in rows:
            if row.get("note") == "P-03":
                row["note"] = "P-02"
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            for row in rows:
                fh.write(json.dumps(row, sort_keys=True,
                                    separators=(",", ":")) + "\n")
        got = anchor_drift.measure_leg(leg)

    assert got["duplicate_probe_notes"] == ["P-02"]
    assert [r["drifted"] for r in got["probes"]
            if r["probe_id"] == "P-02"] == [None]
    assert got["anchor_unknown"] == 2      # P-02 duplicated, P-03 now orphaned
    assert got["triple"]["drifted"] == 0


# =============================== 5. the archive, pinned, and skipped in a clone
def _traces_present(legs):
    return all(os.path.exists(os.path.join(RUNS, leg, "trace.jsonl"))
               for leg in legs)


needs_traces = pytest.mark.skipif(
    not _traces_present(anchor_drift.R2_LEGS),
    reason="runs/*/trace.jsonl is gitignored and absent here, which is the "
           "normal case in a clone; the archive pins need the frames")


@needs_traces
def test_the_four_legs_r2_measured_still_come_out_thirty_five_of_fifty_two():
    """The number that decided R2, re-derived by a reader that shares no code
    with the one that first took it.
    """
    got = anchor_drift.measure(anchor_drift.R2_LEGS, RUNS)
    assert got["totals"]["legs_measured"] == 4
    assert got["totals"]["triple"] == {"probes": 52, "drifted": 35,
                                       "drifted_and_off_frontier": 35}


@needs_traces
def test_the_crosscheck_against_r2s_measurement_is_equal_on_every_probe():
    measurement = os.path.join(RUNS, "20260801T0900Z-R2-frontier-by-generation",
                               "MEASUREMENT.json")
    if not os.path.exists(measurement):
        pytest.skip("R2's MEASUREMENT.json is not in this checkout")
    got = anchor_drift.measure(anchor_drift.R2_LEGS, RUNS)
    said = anchor_drift.crosscheck(got, measurement)
    assert said["probes_compared"] == 52
    assert said["per_probe_disagreements"] == []
    assert said["equal"] is True


@needs_traces
def test_every_completed_probe_in_the_archive_has_an_anchor_to_compare():
    """Why the `None`-is-not-`False` reading cannot have changed the 35.

    R2 counted a probe with no `inert` or no trace step as drifted; this counts
    it as unknown. The two readings agree on the archive only because no
    completed probe there is in that condition -- asserted, not assumed.
    """
    got = anchor_drift.measure(anchor_drift.DEFAULT_LEGS, RUNS)
    for leg in got["legs"]:
        if leg["status"] != anchor_drift.MEASURED:
            continue
        assert leg["anchor_unknown"] == 0, leg["leg"]


@needs_traces
def test_the_archive_agrees_with_itself_about_where_the_world_was():
    """The recorded `before_hash` and the frames it was computed from.

    Both paths are in the archive and nothing has ever compared them. If a leg
    ever disagrees, the anchor number is the least of it -- the trace would be
    internally inconsistent.
    """
    got = anchor_drift.measure(anchor_drift.DEFAULT_LEGS, RUNS)
    assert got["totals"]["recorded_vs_recomputed_disagreements"] == 0


@needs_traces
def test_the_four_legs_that_had_never_been_measured_have_their_triples():
    """The ticket's own deliverable, pinned.

    These four are R1 and R1b. Nothing had ever taken an anchor number on them,
    and 12 of their 20 resolved probes were designed against a frame the world
    had left -- every one of which came back off-frontier, which is the R2
    finding replicating on legs R2 never saw.
    """
    got = anchor_drift.measure(anchor_drift.R1_LEGS, RUNS)
    triples = {leg["leg"]: leg["triple"] for leg in got["legs"]}
    assert triples["20260731T231654Z-R1-g50t-a"] == {
        "probes": 5, "drifted": 3, "drifted_and_off_frontier": 3}
    assert triples["20260731T231654Z-R1-sk48-b"] == {
        "probes": 0, "drifted": 0, "drifted_and_off_frontier": 0}
    assert triples["20260801T001851Z-R1b-g50t-a"] == {
        "probes": 14, "drifted": 9, "drifted_and_off_frontier": 9}
    assert triples["20260801T001851Z-R1b-sk48-b"] == {
        "probes": 1, "drifted": 0, "drifted_and_off_frontier": 0}
    assert got["totals"]["triple"] == {"probes": 20, "drifted": 12,
                                       "drifted_and_off_frontier": 12}


# ============================ 6. the same controls, on a real compiled manual
@pytest.mark.parametrize("leg,actions", [
    ("20260731T1310Z-A3-level2-carried-r2", [2, 5, 2, 5, 2]),
    ("20260731T1500Z-A3-sk48-carried-l1", [4, 3, 4, 3, 4]),
])
def test_the_controls_hold_on_a_manual_the_arm_actually_compiled(leg, actions):
    """The toy manual above is a dict; this one is a leg's own `theory.dsl`.

    `books/snapshots/` is tracked, so this runs in a clone with no traces --
    the control does not need the archive's frames, only its books.
    """
    leg_dir = os.path.join(RUNS, leg)
    if not os.path.isdir(os.path.join(leg_dir, "books", "snapshots")):
        pytest.skip("%s has no snapshots in this checkout" % leg)
    with tempfile.TemporaryDirectory() as tmp:
        name, namespace = anchor_drift.newest_compiling_snapshot(
            leg_dir, os.path.join(tmp, "compile"))
        if namespace is None:
            pytest.skip("no snapshot of %s compiles here" % leg)

        honest = anchor_drift.synthesise_leg(
            os.path.join(tmp, "self"), namespace, actions)
        assert honest["world_frames_distinct"] == len(actions) + 1, (
            "%s does not move under %r, so neither control means anything"
            % (name, actions))
        assert anchor_drift.measure_leg(
            os.path.join(tmp, "self"))["triple"]["drifted"] == 0

        anchor_drift.synthesise_leg(os.path.join(tmp, "broken"), namespace,
                                    actions, mispredict_at=2)
        broken = anchor_drift.measure_leg(os.path.join(tmp, "broken"))
        assert broken["triple"]["drifted"] > 0
        assert broken["triple"]["drifted_and_off_frontier"] == \
            broken["triple"]["drifted"]


def test_the_mispredicting_wrapper_is_the_only_difference_between_the_two_legs():
    """Both controls come off one namespace, so a difference in the measurement
    can only be the wrapper. If `synthesise_leg` differed in any other way --
    a different action list, a different world -- the pair would compare two
    experiments rather than one experiment twice.
    """
    with tempfile.TemporaryDirectory() as tmp:
        honest_dir, honest = _leg(tmp, "self")
        broken_dir, broken = _leg(tmp, "broken", mispredict_at=BREAK_AT)
    assert honest["probes"] == broken["probes"]
    assert honest["n_frames"] == broken["n_frames"]
    assert honest["world_frames_distinct"] == broken["world_frames_distinct"]
    assert honest["mispredict_at"] is None
    assert broken["mispredict_at"] == BREAK_AT


def test_the_worlds_of_the_two_control_legs_are_byte_identical():
    """The world is not what the wrapper changes -- the manual's *reading* of it
    is. If the broken leg's trace differed, the drift could be the world moving
    rather than the roll-forward failing to follow it.
    """
    with tempfile.TemporaryDirectory() as tmp:
        honest_dir, _ = _leg(tmp, "self")
        broken_dir, _ = _leg(tmp, "broken", mispredict_at=BREAK_AT)
        with open(os.path.join(honest_dir, "trace.jsonl"), "rb") as fh:
            one = fh.read()
        with open(os.path.join(broken_dir, "trace.jsonl"), "rb") as fh:
            two = fh.read()
    assert one == two


def test_the_synthesised_world_is_the_manual_rolled_honestly():
    """What makes the self-consistent leg a control rather than an assertion:
    frame *t* of its trace is the manual's own state after *t* actions.
    """
    namespace = _namespace()
    with tempfile.TemporaryDirectory() as tmp:
        leg, _ = _leg(tmp, "self")
        with open(os.path.join(leg, "trace.jsonl"), encoding="utf-8") as fh:
            rows = [json.loads(line) for line in fh if line.strip()]

    state = namespace["initial_state"]()
    want = [grid_hash(namespace["render"](state))]
    for action in ACTIONS:
        state = namespace["step"](state, ("key", action))
        want.append(grid_hash(namespace["render"](state)))
    assert [row["grid_hash"] for row in rows] == want
