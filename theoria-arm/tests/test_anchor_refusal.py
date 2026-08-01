"""The anchor, wired in: computed on every path, and able to refuse.

R2 measured the defect and built the instrument, then deliberately left the
wiring to someone else (`DECISIONS.md`, R2 decision 3). What it measured, over
the four paid legs of 2026-07-31
(`runs/20260801T0900Z-R2-frontier-by-generation/MEASUREMENT.json`):

* **35 of the 52** completed probes were designed against a state the world had
  already left -- the manual's rolled-forward render did not equal the frame the
  world was showing -- and **all 35** landed off the frontier;
* frontier width was 2 distinct predictions on all 52, and the entropy floor
  said no **zero** times.

Three things were wrong with the wiring, and this file watches each one:

1. `probe.anchor_drift` was only called under `cfg.generated`, and `generated`
   is not the default -- so on exactly the legs that were paid for, the number
   was never taken. Section 2.
2. Where it *was* taken it went into the report and nothing read it. `gate()`'s
   two refusals (collapse, bits floor) cannot see it. Section 4.
3. `loop._roll_forward` swallowed a `step` that raised and returned the
   half-rolled state, so a manual that crashed on action 3 of 40 handed back a
   37-action-stale state and said nothing. Section 1.

**What this change does not do.** It does not re-seat the manual's state on the
world's frame. That is the other repair, it has a real cost, and it is not this
one. `certify` keeps its own independent replay (`certify.py`, the loop from
`initial_state()` over `store.actions`), which is untouched here and remains the
instrument that detects a wrong manual.

**Every check that can say no is watched saying it, and saying yes.** A refusal
that fires on everything is indistinguishable from a broken arm, so each
refusing test below has an anchored twin that must NOT refuse.

Offline: no key, no network, no model call, no action sent.
"""

import json
import os
import sys
import types

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(HERE)
if ARM not in sys.path:
    sys.path.insert(0, ARM)

import _bootstrap                                     # noqa: E402,F401

from inner import loop as loop_mod                    # noqa: E402
from inner import probe as probe_beat                 # noqa: E402
from inner.loop import TheoriaArm, _roll_forward      # noqa: E402
from inner.probe import FrontierConfig                # noqa: E402
from world.frames import FrameStore, Step             # noqa: E402

SIZE = 3
MEASUREMENT = os.path.join(
    ARM, "runs", "20260801T0900Z-R2-frontier-by-generation", "MEASUREMENT.json")


# ------------------------------------------------------------- a small world
#
# A marker on row 0 that steps right on every action. The manual states the
# rule exactly, so the ONLY way its state and the world's frame come apart in
# this file is by seeding them apart -- which is what makes the anchored twin
# of each test meaningful rather than lucky.

def _grid(col):
    grid = [[0] * SIZE for _ in range(SIZE)]
    grid[0][min(col, SIZE - 1)] = 1
    return grid


class _State:
    def __init__(self, col):
        self.col = col


def _namespace(start=0, raises_at=None):
    """A compiled-manual stand-in. `raises_at` makes `step` crash on that call."""
    calls = {"n": 0}

    def step(state, _action):
        calls["n"] += 1
        if raises_at is not None and calls["n"] == raises_at:
            raise ValueError("the manual has no rule for this action")
        return _State(state.col + 1)

    return {"render": lambda s: _grid(s.col),
            "step": step,
            "fired": lambda s, a: [],
            "initial_state": lambda: _State(start),
            "RULES": []}


def _store(cols):
    store = FrameStore()
    for idx, col in enumerate(cols):
        store.add(Step(idx, "RESET" if idx == 0 else "ACTION1",
                       [_grid(col)], state="NOT_FINISHED"))
    return store


# =================================================== 1. the rollout says how far
def test_roll_forward_reports_a_clean_replay():
    """The anchored twin: nothing stopped, and the record says so.

    This one caught a real defect in its own ticket. `FrameStore.actions` ends
    with a `None` by construction -- "there is no action after the final
    observed frame" (`world/frames.py`) -- and the first draft counted that
    designed terminator as an early stop, so every clean leg accused itself.
    A `stopped_early` that is true on healthy runs is not an instrument.
    """
    store = _store([0, 1, 2])
    state, rollout = _roll_forward(_namespace(), store)

    assert rollout["stopped_early"] is False
    assert rollout["stopped_because"] is None
    assert rollout["actions_replayed"] == rollout["actions_in_trace"] == 2
    assert state.col == rollout["actions_replayed"]
    assert store.actions[-1] is None, (
        "the terminator this test exists to tolerate is still there")


def test_roll_forward_reports_where_the_manual_crashed():
    """A `step` that raises used to `break` and return the stale state silently.

    The state it returns is unchanged by this ticket -- what changed is that the
    caller can now tell it is stale, and by how many actions.
    """
    store = _store([0, 1, 2])
    state, rollout = _roll_forward(_namespace(raises_at=2), store)

    assert rollout["stopped_early"] is True
    assert "ValueError" in rollout["stopped_because"]
    assert rollout["actions_replayed"] == 1
    assert rollout["actions_in_trace"] > rollout["actions_replayed"]
    assert state.col == 1, "the returned state is not re-seated, only reported"


# ============================================ 2. the anchor is on EVERY path
#
# This is the regression test for the defect itself. If `anchor_drift` goes
# back under `cfg.generated`, this fails and nothing else in the suite does.

def test_the_default_frontier_reports_the_anchor():
    """`ablation` is the default and the legs ran on it. The number must exist."""
    report = probe_beat.design(_namespace(), _State(0), [("key", 1)],
                               store=_store([0, 1, 2]))

    assert "anchor" in report, (
        "the anchor was computed only under `generated` on 2026-07-31, which "
        "is why the four paid legs never took it")
    assert set(report["anchor"]) == {"anchor_hash", "world_hash", "drifted"}


def test_the_anchor_is_reported_with_no_frontier_argument_at_all():
    """The absent-argument path is the one `loop.py` took before R2's switch."""
    report = probe_beat.design(_namespace(), _State(0), [("key", 1)],
                               store=_store([0, 1, 2]))
    assert report["anchor"]["drifted"] is True

    report = probe_beat.design(_namespace(), _State(2), [("key", 1)],
                               store=_store([0, 1, 2]))
    assert report["anchor"]["drifted"] is False


def test_the_generated_block_and_the_report_share_one_anchor_object():
    """One fact, read once.

    `ProbeEconomy.observe` refuses to recompute vacuity for this reason: two
    readings of one fact can disagree, and then the record has two answers.
    """
    report = probe_beat.design(_namespace(), _State(0), [("key", 1)],
                               frontier=FrontierConfig(mode="generated"),
                               store=_store([0, 1, 2]))

    assert report["anchor"] is report["frontier"]["anchor"]


def test_missing_information_is_not_drift():
    """The third negative control: silence is not evidence.

    `drifted` is True only when both hashes exist and differ. A manual with no
    `render`, or a design called without a store, yields no reading -- and a
    probe must not be refused because the instrument could not see. Refusing on
    absent information is how a check starts refusing everything, which is the
    failure mode the twins in this file exist to catch.
    """
    blind = dict(_namespace())
    blind.pop("render")
    assert probe_beat.anchor_drift(blind, _State(0),
                                   _store([0, 1, 2]))["drifted"] is False

    assert probe_beat.anchor_drift(_namespace(), _State(0),
                                   None)["drifted"] is False

    report = probe_beat.design(_namespace(), _State(0), [("key", 1)])
    assert report["anchor"]["drifted"] is False, (
        "no store means no world hash, which is not a claim about drift")


def test_anchor_drift_is_exactly_the_two_hashes_disagreeing():
    """Pins the shipped predicate, which section 5 then counts on the archive."""
    namespace = _namespace()
    same = probe_beat.anchor_drift(namespace, _State(2), _store([0, 1, 2]))
    assert same["anchor_hash"] == same["world_hash"]
    assert same["drifted"] is False

    apart = probe_beat.anchor_drift(namespace, _State(0), _store([0, 1, 2]))
    assert apart["anchor_hash"] != apart["world_hash"]
    assert apart["drifted"] is True


# ==================================================== 3. the loop acts on it
#
# Harness copied from `test_probe_guard_in_the_loop.py`: the design is stubbed
# so the guards are reached with a real `chosen`, and `_send` is a recorder,
# because what is under test is which action the arm chooses.

PREDICTIONS = {"manual": "aaaaaaaaaaaaaaaa", "inert": "bbbbbbbbbbbbbbbb"}


def _design(anchor):
    return {"best": {"action": ["key", 5], "entropy_bits": 0.811,
                     "n_classes": 2},
            "n_hypotheses": 2,
            "anchor": anchor,
            "verdict": "action ('key', 5) splits 2 hypotheses into 2 classes"}


DRIFTED = _design({"anchor_hash": "aaaa000000000000",
                   "world_hash": "bbbb111111111111", "drifted": True})
ANCHORED = _design({"anchor_hash": "cccc222222222222",
                    "world_hash": "cccc222222222222", "drifted": False})


def _arm(tmp_path, monkeypatch, design):
    run_dir = str(tmp_path)
    os.makedirs(run_dir, exist_ok=True)
    run = types.SimpleNamespace(dir=run_dir, run=None, run_id="r-pytest")
    arm = TheoriaArm(env_base="http://127.0.0.1:1", run=run,
                     game_id="g50t-5849a774", offline=True)
    sent = []

    def _send(action_id, *, probe=False, note=""):
        sent.append({"action": action_id, "probe": probe, "note": note})
        return 200, {"state": "NOT_FINISHED"}, [[[0, 0], [0, 0]]]

    monkeypatch.setattr(arm, "_send", _send)
    monkeypatch.setattr(arm, "_legal_actions", lambda: [1, 2, 3, 4, 5])
    monkeypatch.setattr(probe_beat, "design", lambda *a, **k: design)
    monkeypatch.setattr(
        probe_beat, "build_hypotheses",
        lambda ns, **_kw: [
            types.SimpleNamespace(id=name, predict=lambda s, a, _v=value: _v)
            for name, value in PREDICTIONS.items()])
    return arm, sent


def _probe_rows(arm):
    path = os.path.join(arm.dir, "probes.jsonl")
    if not os.path.exists(path):
        return []
    return [json.loads(line) for line in open(path, encoding="utf-8")]


def test_an_anchored_probe_is_still_spent(tmp_path, monkeypatch):
    """The negative control, and the one that matters most.

    35 of 52 were drifted, so a refusal that fires unconditionally would look
    almost right on the archive and would silence the arm completely.
    """
    arm, sent = _arm(tmp_path, monkeypatch, ANCHORED)
    record = {}
    arm._probe_or_explore(_namespace(), record)

    assert record["probe"]["kind"] == "probe"
    assert sent[-1]["probe"] is True
    assert arm._probes_since_theorize == 1


def test_a_drifted_anchor_refuses_the_probe(tmp_path, monkeypatch):
    arm, sent = _arm(tmp_path, monkeypatch, DRIFTED)
    record = {}
    arm._probe_or_explore(_namespace(), record)

    assert record["probe"]["kind"] == "exploration"
    assert "not the frame the world is showing" in record["probe"]["why"]
    assert sent[-1]["probe"] is False, "no action is spent on a gone frame"
    assert arm._probes_since_theorize == 0, "a refused probe is not a probe"


def test_the_drift_refusal_is_written_down_with_both_hashes(tmp_path,
                                                            monkeypatch):
    """A probe quietly dropped is a lie (cold-start-a2's P-3).

    The two hashes go into the record because the refusal is a claim about the
    manual, and a reader has to be able to check it.
    """
    arm, _sent = _arm(tmp_path, monkeypatch, DRIFTED)
    arm._probe_or_explore(_namespace(), {})

    rows = _probe_rows(arm)
    assert len(rows) == 1
    assert rows[0]["phase"] == "unrunnable"
    assert "aaaa000000000000" in rows[0]["reason"]
    assert "bbbb111111111111" in rows[0]["reason"]


def test_a_manual_that_crashed_says_so_inside_the_drift_refusal(tmp_path,
                                                                monkeypatch):
    """The composite case, and the reason the rollout is not plumbed further.

    A `step` that raises on action 1 of N leaves the state at `initial_state()`
    -- stale by every action in the trace -- so the anchor drifts and this
    refusal fires carrying both facts. That is the case worth catching, and it
    is why `rollout` rides the refusal message rather than a new field on
    `ProbeLog`: the only way to be `stopped_early` without drifting is for the
    world to have returned to the exact frame the manual stopped on, and
    `certify` reports a raising `step` independently as `step_raised`.
    """
    arm, sent = _arm(tmp_path, monkeypatch, DRIFTED)
    # The guard tests elsewhere leave the store empty, so their rollout is a
    # trivial 0 of 0. A crash needs actions to crash on.
    for idx, col in enumerate([0, 1, 2, 2]):
        arm.store.add(Step(idx, "RESET" if idx == 0 else "ACTION1",
                           [_grid(col)], state="NOT_FINISHED"))

    record = {}
    arm._probe_or_explore(_namespace(raises_at=1), record)

    why = record["probe"]["why"]
    assert "stopped early" in why
    assert "ValueError" in why
    assert "replayed 0 of 3" in why, (
        "0 of 3: the manual crashed on the first of the three recorded "
        "actions, so the state it handed back is stale by all of them")
    assert sent[-1]["probe"] is False


def test_the_drift_refusal_names_drift_and_not_the_ablation_frontier(
        tmp_path, monkeypatch):
    """Order is the argument.

    The vacuous-streak refusal blames the ablation family for being closed
    downward. That is true, and it was not the binding cause on the four paid
    legs. If the anchor were asked second, the record would carry a real defect
    the run did not suffer from -- which is worse than no reason, because it is
    believed.
    """
    arm, _sent = _arm(tmp_path, monkeypatch, DRIFTED)
    arm.probes.vacuous_streak = loop_mod.MAX_VACUOUS_PROBES_IN_A_ROW

    record = {}
    arm._probe_or_explore(_namespace(), record)

    why = record["probe"]["why"]
    assert "not the frame the world is showing" in why
    assert "empty posterior" not in why


# ============================================ 4. the archive, counted again
#
# What this binds and what it does not. `test_anchor_drift_is_exactly_the_two
# _hashes_disagreeing` above pins the shipped predicate to "the two hashes
# differ". This section then counts that predicate over the 52 archived probes
# and asserts it agrees with `anchored`, which was written by a different
# program (`measure_frontier.py`) reading grids rather than hashes. It does not
# re-derive the archive; it checks that the code now shipping would have made
# the same call on every one of the 52 rows that were actually paid for.

def _measurement():
    if not os.path.exists(MEASUREMENT):
        pytest.skip("the R2 measurement is not in this checkout")
    with open(MEASUREMENT, encoding="utf-8") as fh:
        return json.load(fh)


def test_the_shipped_predicate_agrees_with_the_archive_on_all_52():
    data = _measurement()
    completed = [r for r in data["probes"] if r.get("anchored") is not None]
    assert len(completed) == 52

    for row in completed:
        shipped = row["anchor_hash"] != row["world_before_hash"]
        assert shipped is (row["anchored"] is False), (
            "probe %s: the shipped predicate and the archive disagree"
            % row.get("probe_id"))


def test_the_refusal_would_have_stopped_35_of_the_52():
    data = _measurement()
    totals = data["totals"]
    assert totals["probes_completed"] == 52
    assert totals["anchor_drifted"] == 35

    refused = sum(1 for r in data["probes"]
                  if r.get("anchored") is False
                  and r["anchor_hash"] != r["world_before_hash"])
    assert refused == 35


def test_every_one_of_those_35_had_landed_off_the_frontier():
    """Why refusing them costs nothing: not one of them was ever going to hit.

    This is the number that makes the refusal a saving rather than a trade.
    """
    data = _measurement()
    assert data["totals"]["off_frontier_while_drifted"] == 35
    assert data["totals"]["anchor_drifted"] == 35
