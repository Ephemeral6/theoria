"""E3 -- carrying the books between games, and the records that measure it.

Every test here is offline: no key, no network, no model call, no quota. What
they pin is the set of properties the live second game depends on and that
cannot be re-checked once the money is spent.
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap                                       # noqa: E402,F401

from armtools import spend_check                        # noqa: E402
from inner import theorize, transfer                    # noqa: E402
from inner.books import Books                           # noqa: E402
from world.frames import FrameStore, Step               # noqa: E402


CARRIED_THEORY = """semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Marker { pos: Coord, color: Int }  # arc-colour: 9
  object Unused { pos: Coord, color: Int, present: Bool }  # arc-colour: 1
  landmark hud_slot_a  # arc-cell: (0, 0)

events:
  event jumped(o, dest)

rules:
  rule key5_moves [ev: t1 cov: 1/1]
    when act=key(5) and colored(hud_slot_a, 9) then jumped(Marker, hud_slot_a)

laws:
  invariant one_marker count(Marker) = 1 [status: observed]
"""


def _books(tmp_path, name="source"):
    root = tmp_path / name
    books = Books(str(root))
    books.write(theory=CARRIED_THEORY, playbook="# the playbook\n")
    books.write_problem({"name": "level-1", "grid": [2, 2], "background": 0,
                         "board": [[0, 0], [0, 0]], "objects": []})
    return books


def _store(grids, actions):
    store = FrameStore()
    store.add(Step(0, "RESET", [grids[0]]))
    for i, (grid, action) in enumerate(zip(grids[1:], actions), start=1):
        store.add(Step(i, action, [grid]))
    return store


# ------------------------------------------------------------------- carrying
def test_only_the_two_hand_written_books_travel(tmp_path):
    """`problem.json` is the level instance, computed from the frames of the
    game being played. Carrying it would import the previous game's board and
    make the transfer claim unfalsifiable -- the manual would be checked against
    a level it was written for while appearing to be checked against a new one."""
    source = _books(tmp_path)
    assert os.path.exists(source.problem_path)

    target = Books(str(tmp_path / "target"))
    provenance = transfer.carry(target, source.root,
                                source_game_id="g50t-5849a774")

    assert target.theory.strip() == CARRIED_THEORY.strip()
    assert target.playbook.strip() == "# the playbook"
    assert not os.path.exists(target.problem_path)
    assert "problem.json" in provenance["not_carried"]
    assert provenance["source_game_id"] == "g50t-5849a774"
    assert provenance["carried"]["theory.dsl"]["sha256"]


def test_a_carry_from_a_source_with_no_manual_refuses_rather_than_degrades(tmp_path):
    """A failed carry and a cold start produce the same empty book, so every
    artefact downstream would be uninterpretable. Refusing is the only way the
    difference stays visible."""
    empty = tmp_path / "empty"
    empty.mkdir()
    target = Books(str(tmp_path / "target"))
    with pytest.raises(FileNotFoundError, match="cold start"):
        transfer.carry(target, str(empty))


def test_carrying_snapshots_the_manual_before_the_new_game_touches_it(tmp_path):
    """The transfer measurement is a diff against what arrived. If the arriving
    revision were not on disk before the desk ran, there would be nothing to
    diff against afterwards."""
    source = _books(tmp_path)
    target = Books(str(tmp_path / "target"))
    transfer.carry(target, source.root)
    snapshots = sorted(os.listdir(target.snapshots))
    assert snapshots == ["rev01-carried"]
    kept = os.listdir(os.path.join(target.snapshots, "rev01-carried"))
    assert sorted(kept) == ["playbook.dsl", "theory.dsl"]


def test_declared_names_are_read_out_by_kind():
    names = transfer.declared_names(CARRIED_THEORY)
    assert names["object"] == ["Marker", "Unused"]
    assert names["landmark"] == ["hud_slot_a"]
    assert names["rule"] == ["key5_moves"]
    assert names["invariant"] == ["one_marker"]
    assert names["event"] == ["jumped"]


# ------------------------------------------------- the manual's own prediction
def test_the_carried_formula_is_computed_from_the_new_games_frames():
    """`unexplained(frame_0) = D0 - K`. D0 counts dynamic non-background cells
    of frame 0; K counts DISTINCT declared colours present in frame 0, because
    the manual's own reasoning is that same-colour objects collide on one
    anchor and an absent colour anchors nothing."""
    # Background 0 by majority. Cells (0,0) and (0,1) swap colours; (0,3) holds
    # a constant 7 that is board and so needs no owner.
    grids = [[[9, 1, 0, 7], [0, 0, 0, 0]],
             [[1, 9, 0, 7], [0, 0, 0, 0]]]
    store = _store(grids, ["ACTION1"])

    objects = theorize._objects_from_theory(CARRIED_THEORY)
    prediction = transfer.predict_unexplained(store, objects)

    assert prediction["available"] is True
    assert prediction["background"] == 0
    assert prediction["D0"] == 2                    # (0,0) and (0,1), both non-bg
    # colours 9 and 1 are declared and both occur in frame 0
    assert prediction["declared_colours"] == [1, 9]
    assert prediction["K"] == 2
    assert prediction["predicted_unexplained"] == 0


def test_a_declared_colour_absent_from_the_new_game_does_not_count():
    """The manual says an object whose colour is absent anchors nowhere and
    costs nothing. On a game that does not use that colour, K must fall."""
    grids = [[[9, 0, 0, 0], [0, 0, 0, 0]],          # no colour 1 anywhere
             [[0, 9, 0, 0], [0, 0, 0, 0]]]
    store = _store(grids, ["ACTION1"])
    objects = theorize._objects_from_theory(CARRIED_THEORY)
    prediction = transfer.predict_unexplained(store, objects)
    assert prediction["background"] == 0
    assert prediction["declared_colours"] == [1, 9]
    assert prediction["declared_colours_present_in_frame_0"] == [9]
    assert prediction["K"] == 1
    assert prediction["D0"] == 1                    # only (0,0) is non-bg at t0
    assert prediction["predicted_unexplained"] == 0


def test_the_prediction_is_withheld_where_the_formula_does_not_apply():
    """`arc-instances: all` spreads one declaration over every dynamic cell of
    its colour, which breaks the formula's 'one colour, one pixel' step. A
    formula applied outside its stated domain is not a test of it, so no number
    is reported at all."""
    spread_theory = CARRIED_THEORY.replace(
        "# arc-colour: 9", "# arc-colour: 9  arc-instances: all")
    grids = [[[9, 1, 7]], [[1, 9, 7]]]
    store = _store(grids, ["ACTION1"])
    prediction = transfer.predict_unexplained(
        store, theorize._objects_from_theory(spread_theory))
    assert prediction["available"] is False
    assert prediction["predicted_unexplained"] is None
    assert "Marker" in prediction["withheld_because"]

    scored = transfer.score_prediction(
        prediction, {"cheap": {"checks": {"responsibility":
                                          {"cells_unexplained": 3}}}})
    assert scored["verdict"] == "withheld"


@pytest.mark.parametrize("observed,verdict", [(4, "held"), (5, "refuted")])
def test_the_prediction_is_scored_both_ways(observed, verdict):
    prediction = {"available": True, "predicted_unexplained": 4,
                  "formula": transfer.RENDER_FORMULA}
    report = {"cheap": {"checks": {"responsibility":
                                   {"cells_unexplained": observed}}}}
    scored = transfer.score_prediction(prediction, report)
    assert scored["verdict"] == verdict
    assert scored["observed"] == observed
    assert scored["predicted"] == 4


def test_a_manual_that_cannot_draw_its_own_frame_makes_the_prediction_unscorable():
    """`certify` reports `cells_unexplained: None` when `render` raised. That is
    not a refutation of the formula and must not be scored as one."""
    prediction = {"available": True, "predicted_unexplained": 4}
    report = {"cheap": {"checks": {"responsibility": {
        "cells_unexplained": None,
        "raised": "KeyError: 'Marker'"}}}}
    scored = transfer.score_prediction(prediction, report)
    assert scored["verdict"] == "unscorable"
    assert "KeyError" in scored["detail"]


# ------------------------------------------------------------------ retention
def test_retention_counts_names_kept_dropped_and_added():
    final = CARRIED_THEORY.replace("object Unused", "object Wall") + """
  theorem something_new "learned on the new game" [probe: pending]
"""
    result = transfer.retention(CARRIED_THEORY, final)
    assert result["by_kind"]["object"]["kept"] == ["Marker"]
    assert result["by_kind"]["object"]["dropped"] == ["Unused"]
    assert result["by_kind"]["object"]["added"] == ["Wall"]
    assert result["by_kind"]["theorem"]["added"] == ["something_new"]
    assert result["names_carried"] == 6
    assert result["names_kept"] == 5
    assert result["names_dropped"] == 1
    assert result["retention_rate"] == round(5 / 6, 4)
    # Names only, and the report says so rather than implying more.
    assert "names only" in result["scope"]


def test_retention_of_an_unchanged_manual_is_total():
    result = transfer.retention(CARRIED_THEORY, CARRIED_THEORY)
    assert result["retention_rate"] == 1.0
    assert result["names_dropped"] == 0


# ------------------------------------------------------------- the spend gate
def test_the_absent_spend_gate_is_reported_as_absent_and_never_as_ok(monkeypatch):
    """S3's gate is fail-closed for its own callers. A run that precedes it
    cannot fail closed against a thing that does not exist -- but it must not
    record the situation as a pass. `absent` is the only honest label, and the
    reservation must not be held."""
    monkeypatch.setattr(spend_check, "SPEND_GATE",
                        os.path.join("no", "such", "spend_gate.py"))
    status = spend_check.gate_status()
    assert status["available"] is False
    assert status["status"] == "absent"
    assert status["campaign"] == spend_check.CAMPAIGN

    held = spend_check.reserve(status, usd_cap=18.0, action_cap=120)
    assert held["held"] is False


def test_a_gate_that_exists_is_used_rather_than_reimplemented(tmp_path, monkeypatch):
    gate = tmp_path / "spend_gate.py"
    gate.write_text(
        "def reserve(campaign, usd_cap, action_cap):\n"
        "    return 'handle-%s-%s-%s' % (campaign, usd_cap, action_cap)\n",
        encoding="utf-8")
    monkeypatch.setattr(spend_check, "SPEND_GATE", str(gate))

    status = spend_check.gate_status()
    assert status["available"] is True
    held = spend_check.reserve(status, usd_cap=18.0, action_cap=120)
    assert held["held"] is True
    assert held["handle"] == "handle-theoria-arm-18.0-120"


def test_a_gate_that_raises_on_reserve_does_not_report_a_reservation(tmp_path,
                                                                    monkeypatch):
    gate = tmp_path / "spend_gate.py"
    gate.write_text(
        "def reserve(campaign, usd_cap, action_cap):\n"
        "    raise RuntimeError('ledger is not writable')\n", encoding="utf-8")
    monkeypatch.setattr(spend_check, "SPEND_GATE", str(gate))
    held = spend_check.reserve(spend_check.gate_status(),
                               usd_cap=1.0, action_cap=1)
    assert held["held"] is False
    assert "not writable" in held["reason"]


# ------------------------------------------------------------ the projection
def _curve(tmp_path, calls):
    run = tmp_path / "prior"
    run.mkdir()
    (run / "cost_curve.json").write_text(json.dumps(calls), encoding="utf-8")
    return str(run)


def test_the_basis_is_measured_from_a_prior_run_not_assumed(tmp_path):
    run = _curve(tmp_path, [
        {"usd": 1.0, "elapsed_ms": 400_000, "usage": {"output_tokens": 40_000}},
        {"usd": 2.0, "elapsed_ms": 600_000, "usage": {"output_tokens": 50_000}}])
    basis = spend_check.basis_from_run(run)
    assert basis["available"] is True
    assert basis["usd_per_call_mean"] == 1.5
    assert basis["usd_per_call_max"] == 2.0
    assert basis["seconds_per_call_mean"] == 500.0


def test_the_basis_reads_either_cost_curve_shape(tmp_path):
    """`archive.py` writes a flat list; `inner/loop.py` writes the per-turn view
    under a `calls` key with the desk log's own field name."""
    run = _curve(tmp_path, {"calls": [
        {"cli_cost_usd": 1.0, "elapsed_ms": 1000},
        {"cli_cost_usd": 3.0, "elapsed_ms": 3000}]})
    basis = spend_check.basis_from_run(run)
    assert basis["available"] is True
    assert basis["usd_per_call_mean"] == 2.0


def test_the_projection_names_the_constraint_that_actually_binds(tmp_path):
    """The action budget is not the binding constraint on this arm and the plan
    has to say so before the money is spent, or the run reads afterwards as a
    shortfall against 120 rather than as the measurement it is."""
    basis = spend_check.basis_from_run(_curve(tmp_path, [
        {"usd": 1.25, "elapsed_ms": 500_000}]))
    projection = spend_check.project(
        basis, action_cap=120, usd_ceiling=18.0, wall_clock_s=3 * 3600,
        legal_actions=4, frames_per_theorize=4, max_theorize_per_turn=2)
    assert projection["binding_constraint"] == "cost_ceiling"
    assert projection["desk_calls_the_ceiling_buys"] == 14
    assert projection["actions_reachable_worst_case"] < 120
    assert projection["actions_reachable_best_case"] < 120


def test_a_ceiling_large_enough_makes_the_action_budget_bind(tmp_path):
    basis = spend_check.basis_from_run(_curve(tmp_path, [
        {"usd": 0.01, "elapsed_ms": 1_000}]))
    projection = spend_check.project(
        basis, action_cap=120, usd_ceiling=1000.0, wall_clock_s=3 * 3600,
        legal_actions=4, frames_per_theorize=4, max_theorize_per_turn=2)
    assert projection["binding_constraint"] == "action_budget"
    assert projection["actions_reachable_best_case"] == 120


def test_a_plan_cannot_be_built_without_a_measured_basis(tmp_path):
    basis = spend_check.basis_from_run(str(tmp_path / "nothing"))
    assert basis["available"] is False
    projection = spend_check.project(
        basis, action_cap=120, usd_ceiling=18.0, wall_clock_s=3600,
        legal_actions=4, frames_per_theorize=4, max_theorize_per_turn=2)
    assert projection["available"] is False


# ------------------------------------------------------- the whole thing, mock
def _carried_run(tmp_path, slug_suffix, **arm_kwargs):
    """One full offline run against `proxy/mock`, started from carried books."""
    from harness.run import play                         # noqa: PLC0415
    from inner.loop import TheoriaArm                    # noqa: PLC0415
    from proxy.mock.arc_mock import DEFAULT_KEY, MockArc  # noqa: PLC0415

    source = _books(tmp_path)
    game = "g50t-5849a774"
    slug = "pytest-e3-" + slug_suffix + "-" + os.path.basename(str(tmp_path))

    def factory(env_base, run):
        return TheoriaArm(env_base=env_base, run=run, game_id=game,
                          budget_actions=6, offline=True,
                          carry_books=source.root,
                          carry_source_game="g50t-5849a774",
                          prompt_id="E3-engines-online", **arm_kwargs)

    with MockArc(api_key=DEFAULT_KEY, games=[game]) as mock:
        summary = play(game, slug, factory, env_upstream=mock.base_url,
                       env_key=DEFAULT_KEY, require_key=False)
    return summary, os.path.join(_bootstrap.path("runs"), slug)


def test_the_carried_manual_is_certified_cold_before_any_model_call(tmp_path):
    """The transfer datum in its purest form: a manual written for one game,
    compiled and driven over another game's frames with zero desk calls. If
    this ran after the first theorize it would measure a repaired manual, which
    is a different and much weaker claim."""
    summary, run_dir = _carried_run(tmp_path, "cold")

    report = json.loads(open(os.path.join(run_dir, "transfer.json"),
                             encoding="utf-8").read())
    assert report["stage"] == "cold"
    assert report["model_calls_so_far"] == 0
    assert summary["model_calls"] == 0
    # It was certified against frames the manual has never seen.
    assert report["certify"]["responsibility"]["total_cells"] > 0
    assert report["compiled"]["parsed"] is True
    # And the provenance says where it came from and what did not travel.
    assert report["provenance"]["source_game_id"] == "g50t-5849a774"
    assert "problem.json" in report["provenance"]["not_carried"]


def test_the_prediction_reaches_disk_before_the_check_it_predicts(tmp_path):
    """Same discipline as `probe`: a prediction recorded after its result is
    not a prediction. The cold beat writes a `prediction-only` revision of
    transfer.json first, and the desk log proves nothing was called in between."""
    from inner import loop as loop_mod                   # noqa: PLC0415

    seen = []
    original = loop_mod._dump

    def spy(path, obj):
        if os.path.basename(path) == "transfer.json":
            seen.append((obj.get("stage"),
                         "prediction" in obj,
                         "certify" in obj))
        return original(path, obj)

    loop_mod._dump = spy
    try:
        _carried_run(tmp_path, "order")
    finally:
        loop_mod._dump = original

    assert seen, "transfer.json was never written"
    # First write: the prediction, and no certify result anywhere in it.
    assert seen[0] == ("prediction-only", True, False)
    # A later write carries the result.
    assert any(stage == "cold" and has_certify
               for stage, _, has_certify in seen)


def test_every_engine_dispatch_leaves_a_row_even_with_no_desk_call(tmp_path):
    """E3's supply-chain claim is about a sequence of deliveries, so it needs a
    row per dispatch. The cold beat makes no model call at all, and its sweep
    must still be on the record."""
    summary, run_dir = _carried_run(tmp_path, "engines")

    path = os.path.join(run_dir, "engines_online.jsonl")
    # Append-only, and this slug is reused whenever the suite is re-run in the
    # same pytest tmp root, so the file may hold more than this run. Partition
    # it the way the ledger is partitioned.
    rows = [json.loads(line) for line in open(path, encoding="utf-8")
            if line.strip()]
    rows = [r for r in rows if r["run_id"] == summary["run_id"]]
    assert rows, "no engine dispatch was recorded"
    assert rows[0]["label"] == "cold"
    assert rows[0]["dispatch_idx"] == 0
    assert rows[0]["candidate_rows_total"] >= rows[0]["candidate_rows_added"]

    for name in ("mdl_segmenter", "cegis_miner", "zero_space"):
        row = rows[0]["engines"][name]
        # Delivered or refused-with-a-reason; never silently empty.
        assert row["delivered"] or row["error"] or row["skipped"], (name, row)

    online = summary["engines_online"]
    assert online["dispatches"] == len(rows)
    assert online["dispatch_errors"] == 0
    assert online["per_engine"]["mdl_segmenter"]["dispatches"] == len(rows)


def _bare_arm(tmp_path, store):
    """A `TheoriaArm` with just enough wired up to dispatch engines.

    Built without `__init__` on purpose: a real one opens a proxy and a ledger,
    and what is under test here is one method's decision about whether to run
    the engines at all.
    """
    from inner.loop import TheoriaArm                    # noqa: PLC0415

    arm = TheoriaArm.__new__(TheoriaArm)
    arm.run = type("R", (), {"run_id": "r-test"})()
    arm.store = store
    arm.dir = str(tmp_path)
    arm.candidates_path = os.path.join(str(tmp_path), "candidates.jsonl")
    arm.engine_log_path = os.path.join(str(tmp_path), "engines_online.jsonl")
    arm.engine_rounds = []
    arm._last_dispatch = None
    arm._last_dispatch_transitions = -1
    arm._last_dispatch_idx = -1
    return arm


def test_identical_evidence_is_not_re_swept(tmp_path):
    """The engines are deterministic given the same frames, so a sweep over a
    store that has not grown returns exactly what the last one returned. The
    first live E3 run dispatched twice over the same five transitions, took
    348 seconds each time, and appended 680 candidate rows each time -- and the
    second 680 were a copy of the first, on a stream whose contract says sweeps
    differ because each sees more transitions than the last. The reuse is
    recorded as its own row, not hidden."""
    grids = [[[9, 0, 0, 0], [0, 0, 0, 0]],
             [[0, 9, 0, 0], [0, 0, 0, 0]],
             [[0, 0, 9, 0], [0, 0, 0, 0]]]
    store = _store(grids, ["ACTION1", "ACTION2"])
    arm = _bare_arm(tmp_path, store)

    first = arm._dispatch_engines(label="cold")
    rows_after_first = sum(1 for line in open(arm.candidates_path,
                                              encoding="utf-8") if line.strip())
    second = arm._dispatch_engines(label="theorize")
    rows_after_second = sum(1 for line in open(arm.candidates_path,
                                               encoding="utf-8") if line.strip())

    assert second is first, "the second dispatch re-ran the engines"
    assert rows_after_second == rows_after_first, (
        "the second dispatch appended %d duplicate candidate rows"
        % (rows_after_second - rows_after_first))

    entries = arm.engine_rounds
    assert len(entries) == 2, "the reuse was not recorded as its own row"
    assert "reused_from_dispatch_idx" not in entries[0]
    assert entries[1]["reused_from_dispatch_idx"] == 0
    assert entries[1]["elapsed_ms"] == 0
    assert entries[1]["candidate_rows_added"] == 0
    assert "deterministic" in entries[1]["reused_because"]
    # A reused row still reports what the engines delivered.
    assert entries[1]["engines"]["mdl_segmenter"]["delivered"] is True


def test_new_evidence_does_re_sweep(tmp_path):
    """The cache must key on the evidence, not merely on having run once. A
    sweep that never re-runs is a worse defect than one that always does."""
    grids = [[[9, 0, 0, 0], [0, 0, 0, 0]],
             [[0, 9, 0, 0], [0, 0, 0, 0]]]
    store = _store(grids, ["ACTION1"])
    arm = _bare_arm(tmp_path, store)

    first = arm._dispatch_engines(label="cold")
    store.add(Step(2, "ACTION2", [[[0, 0, 9, 0], [0, 0, 0, 0]]]))
    second = arm._dispatch_engines(label="theorize")

    assert second is not first, "a new transition did not trigger a re-sweep"
    assert "reused_from_dispatch_idx" not in arm.engine_rounds[1]
    assert arm.engine_rounds[1]["transitions_seen"] == 2
    assert arm.engine_rounds[0]["transitions_seen"] == 1


def test_the_cold_beat_flushes_the_surprises_it_fired(tmp_path):
    """The cold certify fires the surprises that bring the desk in on turn 1.
    A run killed between the cold beat and the first theorize -- a window that
    was a quarter of an hour on the live run -- must not lose the record of why
    it was about to spend money."""
    from inner import loop as loop_mod                   # noqa: PLC0415

    flushed = {}
    original = loop_mod.TheoriaArm._write_run_state

    def spy(self):
        original(self)
        path = os.path.join(self.dir, "surprises.jsonl")
        if self.transfer_report is not None and "cold" not in flushed:
            flushed["cold"] = sum(1 for line in open(path, encoding="utf-8")
                                  if line.strip())

    loop_mod.TheoriaArm._write_run_state = spy
    try:
        _carried_run(tmp_path, "flush")
    finally:
        loop_mod.TheoriaArm._write_run_state = original

    assert "cold" in flushed, "run state was never written after the cold beat"
    assert flushed["cold"] > 0, (
        "the cold certify's surprises were still in memory when the cold beat "
        "returned")


def test_a_refusal_counts_as_a_delivery_and_not_as_an_error(tmp_path):
    """`cegis_miner`'s precondition -- exactly one move event per transition --
    is a real claim about a world. A game that does not satisfy it makes the
    engine refuse, and a refusal is the engine working. Conflating the two
    would turn E3's supply-chain measurement into a measurement of the game."""
    summary, _ = _carried_run(tmp_path, "refusal")
    miner = summary["engines_online"]["per_engine"]["cegis_miner"]
    assert miner["errored"] == 0
    assert miner["delivered"] == miner["dispatches"]


def test_the_bill_is_plotted_against_the_action_count_at_the_moment_it_was_spent(
        tmp_path):
    """The x-axis has to be sampled when the money is spent. Reconstructing it
    afterwards from timestamps guesses, and a guessed x-axis is not a
    measurement. With no desk calls the curve is empty and the totals still
    have to be right."""
    summary, run_dir = _carried_run(tmp_path, "bill")

    bill = json.loads(open(os.path.join(run_dir, "bill_shape.json"),
                           encoding="utf-8").read())
    assert bill["calls"] == []                      # offline: nothing spent
    totals = bill["totals"]
    assert totals["desk_calls"] == 0
    assert totals["usd"] == 0.0
    assert totals["actions_billed"] == summary["budget"]["actions_ok"]
    assert totals["commands_sent"] == summary["budget"]["commands_sent"]
    # Billed actions and HTTP requests are different axes and the file says so.
    assert "not a curve against the other" in bill["reading"]
    assert summary["bill"]["actions_billed"] == totals["actions_billed"]


def test_the_bill_curve_is_cumulative_and_marginal_per_call():
    """Checked directly on the desk log, because a live run is the only place
    this shape appears and it must not be discovered there for the first time."""
    from inner.loop import TheoriaArm                    # noqa: PLC0415

    arm = TheoriaArm.__new__(TheoriaArm)                 # no I/O, no proxy
    arm.desk = type("D", (), {"log": [
        {"cli_cost_usd": 1.0, "actions_at_call": 4, "beat": "theorize",
         "label": "round1", "turn": 1, "step_idx": 5, "elapsed_ms": 1000,
         "usage": {"output_tokens": 100}},
        {"cli_cost_usd": 2.0, "actions_at_call": 8, "beat": "theorize",
         "label": "round1", "turn": 2, "step_idx": 9, "elapsed_ms": 2000,
         "usage": {"output_tokens": 200}},
    ]})()
    arm.budget = type("B", (), {"as_json": lambda self: {
        "actions_ok": 8, "commands_sent": 12, "http_amplification": 1.5}})()
    arm.store = type("S", (), {"grids": [None] * 9})()
    arm.started = arm._elapsed = None
    arm._elapsed = lambda: 10.0

    curve = TheoriaArm.cost_curve(arm)
    calls = curve["calls"]
    assert [c["usd_cumulative"] for c in calls] == [1.0, 3.0]
    assert [c["actions_since_last_call"] for c in calls] == [4, 4]
    assert [c["usd_per_action_marginal"] for c in calls] == [0.25, 0.5]
    assert curve["totals"]["usd_per_billed_action"] == 0.375
    assert curve["totals"]["transitions_observed"] == 8


def test_a_run_that_carried_nothing_writes_no_transfer_report(tmp_path):
    """A cold start must stay visibly a cold start."""
    from harness.run import play                         # noqa: PLC0415
    from inner.loop import TheoriaArm                    # noqa: PLC0415
    from proxy.mock.arc_mock import DEFAULT_KEY, MockArc  # noqa: PLC0415

    game = "g50t-5849a774"
    slug = "pytest-e3-cold-start-" + os.path.basename(str(tmp_path))

    def factory(env_base, run):
        return TheoriaArm(env_base=env_base, run=run, game_id=game,
                          budget_actions=4, offline=True)

    with MockArc(api_key=DEFAULT_KEY, games=[game]) as mock:
        summary = play(game, slug, factory, env_upstream=mock.base_url,
                       env_key=DEFAULT_KEY, require_key=False)

    run_dir = os.path.join(_bootstrap.path("runs"), slug)
    assert summary["transfer"] is None
    assert not os.path.exists(os.path.join(run_dir, "transfer.json"))
    assert not os.path.exists(os.path.join(run_dir, "CARRIED.json"))
    # The engine record is not conditional on carrying, though.
    assert os.path.exists(os.path.join(run_dir, "engines_online.json"))
