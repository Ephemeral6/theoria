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

    # `Books(seed_from=...)` is the one route that copies the pair; `carry`
    # adds the cross-game provenance on top of the record it wrote.
    target = Books(str(tmp_path / "target"), seed_from=source.root)
    provenance = transfer.carry(target, source.root,
                                source_game_id="g50t-5849a774")

    # The manual travels whole apart from the landmark coordinates, which are
    # level data and are stripped (see the dedicated test below).
    assert target.theory.strip() == transfer.strip_level_data(
        CARRIED_THEORY)[0].strip()
    assert "object Marker" in target.theory
    assert "rule key5_moves" in target.theory
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
    target = Books(str(tmp_path / "target"), seed_from=str(empty))
    with pytest.raises(FileNotFoundError, match="cold start"):
        transfer.carry(target, str(empty))


def test_carrying_snapshots_the_manual_before_the_new_game_touches_it(tmp_path):
    """The transfer measurement is a diff against what arrived. If the arriving
    revision were not on disk before the desk ran, there would be nothing to
    diff against afterwards."""
    source = _books(tmp_path)
    target = Books(str(tmp_path / "target"), seed_from=source.root)
    transfer.carry(target, source.root)
    snapshots = sorted(os.listdir(target.snapshots))
    assert snapshots == ["rev01-carried"]
    kept = os.listdir(os.path.join(target.snapshots, "rev01-carried"))
    assert sorted(kept) == ["playbook.dsl", "theory.dsl"]


def test_landmark_coordinates_do_not_travel_between_games(tmp_path):
    """Excluding `problem.json` is not enough on its own.

    On the first live carry, seven of g50t's landmark coordinates arrived in
    sk48's computed `problem.json` verbatim -- `start_cell (10,16)`,
    `gate_cell (40,16)`, `goal_cell (52,46)` and four more -- because
    `_landmarks_from_theory` reads them out of comments in the manual. A
    landmark's cell is level data by the arm's own domain/problem split, so a
    route that carries it across games defeats the exclusion beside it.
    """
    source = _books(tmp_path)
    target = Books(str(tmp_path / "target"), seed_from=source.root)
    provenance = transfer.carry(target, source.root)

    assert provenance["landmarks_stripped"] == ["hud_slot_a"]
    assert "arc-cell: (0, 0)" not in target.theory
    # The landmark itself is still declared -- only its coordinates went.
    assert "landmark hud_slot_a" in target.theory
    assert theorize._landmarks_from_theory(target.theory) == {"hud_slot_a": None}
    # And the source run's books are untouched.
    assert "arc-cell: (0, 0)" in source.theory
    # The stripped revision is the one snapshotted, so the diff is visible.
    snapshot = os.path.join(target.snapshots, "rev01-carried", "theory.dsl")
    assert "arc-cell: (0, 0)" not in open(snapshot, encoding="utf-8").read()


def test_a_stripped_landmark_lands_at_the_origin_and_is_listed(tmp_path):
    """The existing, visible failure mode for a coordinate the level cannot
    supply -- not a new silent one."""
    from inner.books import problem_from_frames           # noqa: PLC0415

    grids = [[[9, 1, 0, 7], [0, 0, 0, 0]],
             [[1, 9, 0, 7], [0, 0, 0, 0]]]
    store = _store(grids, ["ACTION1"])
    stripped, removed = transfer.strip_level_data(CARRIED_THEORY)
    assert removed == ["hud_slot_a"]

    problem = problem_from_frames(
        store, theorize._objects_from_theory(stripped),
        landmarks=theorize._landmarks_from_theory(stripped))
    assert problem["landmarks"]["hud_slot_a"] == [0, 0]
    assert problem["landmarks_defaulted"] == ["hud_slot_a"]


@pytest.mark.parametrize("line,label", [
    ("  landmark a  # arc-cell: (7, 8)", "the shape the first version handled"),
    ("  landmark a  arc-cell: (7, 8)", "no leading hash"),
    ("  landmark a  # arc-cell = (7, 8)", "equals instead of colon"),
    ("  landmark a  # arc-cell: (-1, 2)", "negative coordinate"),
    ("  landmark a  # arc-cell: 7, 8", "no parentheses"),
    ("  landmark a  # arc-cell: (1,2) arc-cell = (3,4)", "two hints on one line"),
    ("  landmark a  # arc-cell:(70,80)", "no spaces, multi-digit"),
])
def test_no_shape_of_cell_hint_survives_the_strip(line, label):
    """The coverage gap that let three leaks through.

    The stripper originally required a leading `#` and rejected a minus sign,
    while the detector that reports `landmarks_stripped` required neither. Every
    disagreement was a coordinate that leaked **and was simultaneously attested
    as removed** -- the provenance lied in the dangerous direction. The one
    shape the old tests used, `# arc-cell: (0, 0)`, was the one shape that
    worked.
    """
    stripped, removed = transfer.strip_level_data(line + "\n")
    assert removed == ["a"], label
    read_back = theorize._landmarks_from_theory(stripped)
    assert read_back == {"a": None}, (label, stripped, read_back)


def test_a_coordinate_that_outlives_the_strip_raises_rather_than_carries():
    """The post-condition is checked, not assumed. If some future hint shape
    slips past the pattern, the carry must fail loudly rather than write the
    previous game's geometry into the next game's level."""
    import inner.transfer as t                            # noqa: PLC0415

    original = t.CELL_HINT_ANY
    t.CELL_HINT_ANY = __import__("re").compile(r"never-matches-anything")
    try:
        with pytest.raises(transfer.LevelDataSurvived, match="outlived"):
            t.strip_level_data("  landmark a  # arc-cell: (7, 8)\n")
    finally:
        t.CELL_HINT_ANY = original


def test_a_landmark_with_no_hint_is_untouched_and_unreported():
    stripped, removed = transfer.strip_level_data("  landmark a\n")
    assert removed == []
    assert stripped == "  landmark a\n"


def test_an_arc_cell_outside_a_landmark_line_is_left_alone():
    """`arc-cell` on an object line is not a landmark coordinate, so stripping
    it would be a silent edit to something this function has no claim over."""
    text = "  object Cart { pos: Coord }  # arc-colour: 6 arc-cell: (1, 2)\n"
    stripped, removed = transfer.strip_level_data(text)
    assert removed == []
    assert stripped == text


def test_stripping_is_recorded_on_both_sides_of_the_hash(tmp_path):
    """The carried manual is no longer byte-identical to its source, so both
    hashes are kept: a provenance record that showed only one would make the
    stripping invisible to anyone checking what was carried."""
    source = _books(tmp_path)
    target = Books(str(tmp_path / "target"), seed_from=source.root)
    provenance = transfer.carry(target, source.root)
    entry = provenance["carried"]["theory.dsl"]
    assert entry["sha256"] != entry["sha256_before_stripping"]
    assert entry["sha256"] == _sha256_of(target.theory_path)


def _sha256_of(path):
    import hashlib
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


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


# ------------------------------------------------- can this game test it at all
def test_a_manual_whose_actions_the_game_does_not_offer_is_not_testable():
    """The reading the first live carry got wrong.

    g50t's manual declares exactly one action, `('key', 5)`, and every rule
    opens by refusing anything else. sk48 offers `[1,2,3,4,6,7]` and has no
    ACTION5, so every rule was unreachable and `step` was the identity for every
    action the arm could send -- which makes a replay failure evidence about the
    mismatch and not about the manual. Nothing in the artefacts said so.
    """
    result = transfer.action_overlap({"ACTIONS": [("key", 5)]}, [1, 2, 3, 4, 7])
    assert result["testable"] is False
    assert result["manual_action_ids"] == [5]
    assert result["game_offers"] == [1, 2, 3, 4, 7]
    assert result["shared"] == []
    assert "cannot test the carried theory" in result["detail"]


def test_an_overlapping_vocabulary_is_testable():
    result = transfer.action_overlap(
        {"ACTIONS": [("key", 2), ("key", 5)]}, [1, 2, 3])
    assert result["testable"] is True
    assert result["shared"] == [2]
    assert "can fire" in result["detail"]


def test_a_manual_declaring_no_actions_is_not_testable_either():
    """A manual with no actions makes no action-conditioned prediction, which
    is a different reason for the same verdict and must not be silently folded
    into 'no overlap'."""
    result = transfer.action_overlap({"ACTIONS": []}, [1, 2, 3])
    assert result["testable"] is False
    assert result["manual_action_ids"] == []
    assert "declares no actions" in result["detail"]

    assert result["reason"] == "manual_declares_no_actions"


def test_a_predictor_that_would_not_load_is_not_a_claim_about_the_manual():
    """`action_overlap(None, ...)` used to answer "the carried manual declares
    no actions at all" -- a false factual claim about the theory, published on
    the one line the cold report says a reader needs first. A compile failure
    is not a property of the theory."""
    result = transfer.action_overlap(None, [1, 2, 3],
                                     predictor_error="SyntaxError: bad")
    assert result["testable"] is False
    assert result["reason"] == "predictor_did_not_load"
    assert "SyntaxError: bad" in result["detail"]
    assert "says nothing about what the manual declares" in result["detail"]
    # It must NOT claim the manual declares nothing.
    assert "declares no actions at all" not in result["detail"]
    assert result["manual_action_ids"] is None


def test_an_action_of_another_arity_is_unreadable_not_absent():
    """`gen_python`'s alphabet is `(name,) + args`, so a click-family manual is
    a 3-tuple. Dropping those silently produced "declares no actions at all",
    which is false: the overlap is unknown, not empty."""
    result = transfer.action_overlap(
        {"ACTIONS": [("click", 10, 20), ("key",)]}, [1, 2])
    assert result["testable"] is False
    assert result["reason"] == "no_action_readable_as_a_key_id"
    assert result["actions_not_readable_as_a_key_id"] == [["click", 10, 20],
                                                          ["key"]]
    assert "unknown, not empty" in result["detail"]
    assert "declares no actions at all" not in result["detail"]


def test_the_three_untestable_verdicts_are_distinguishable():
    """All three set `testable: False`, and a test that asserted only that
    locked in the false reason for two of them."""
    reasons = {
        transfer.action_overlap(None, [1])["reason"],
        transfer.action_overlap({"ACTIONS": []}, [1])["reason"],
        transfer.action_overlap({"ACTIONS": [("key", 5)]}, [1])["reason"],
    }
    assert reasons == {"predictor_did_not_load",
                       "manual_declares_no_actions",
                       "no_overlap"}


def test_the_cold_report_leads_with_whether_the_run_can_test_anything():
    """A reader must not have to reach the bottom of the report to learn that
    every number above it is uninterpretable as evidence about the manual."""
    report = transfer.cold_report(
        provenance={}, prediction={"available": False},
        compiled={"parsed": True, "ok": True, "forms": {"python": "p"}},
        certify_report={"cheap": {"checks": {"replay": {"ok": False}}}},
        store_summary={}, actions_spent=5,
        actions=transfer.action_overlap({"ACTIONS": [("key", 5)]}, [1, 2]))

    assert report["carried_theory_is_testable_on_this_game"] is False
    assert report["replay_means"].startswith("NOT evidence")
    assert report["actions"]["shared"] == []


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


# ------------------------------------------------- the ledger, actually written
def _scratch_binding(tmp_path):
    """A spend claim on a pool this test owns, and its teardown.

    A desk with no binding raises `NoSpendBinding` rather than spending, and a
    binding on the *tracked* pool is refused from inside pytest -- both by
    design (`harness/spend.py`), and both mean a desk test has to say which
    pool its fictional dollars land in.
    """
    from harness import run as run_mod                    # noqa: PLC0415
    from harness import spend as spend_mod                # noqa: PLC0415
    from proxy.spend_gate import SpendGate                # noqa: PLC0415

    gate = SpendGate(run_mod._scratch_policy(
        os.path.join(str(tmp_path), "scratch-pool.jsonl")))
    expect = {"pool": gate.policy.pool,
              "ledger_abspath": os.path.abspath(gate.ledger_path)}
    caps = spend_mod.plan_caps(actions=12, commands=2000,
                               cost_ceiling_usd=20.0, require_headroom=False)
    return spend_mod.open_binding("theoria-arm:test:sk48-d8078629:e3-unit",
                                  caps, gate=gate, expect_pool=expect)


def _desk_on_a_real_ledger(tmp_path, envelope):
    """A `ModelDesk` wired to the real frozen writer, with the CLI stubbed out.

    The point is that the *ledger* is real. P-8's tests exercised constraint 8
    and the record's shape against hand-built dicts, and every one of them
    passed while the live writer refused the record outright -- because nothing
    offline ever asked `proxy.ledger.RunLedger` to accept what this arm
    actually sends it.

    The spend binding is real too, and on a scratch pool: A3 made an ungated
    desk call impossible rather than merely discouraged, so a test that wants a
    completed `model_call` has to claim headroom like a run does.
    """
    from harness.modelcall import ModelDesk               # noqa: PLC0415
    from proxy.ledger import Ledger, RunLedger            # noqa: PLC0415

    ledger = Ledger(os.path.join(str(tmp_path), "ledger.jsonl"))
    run = RunLedger(ledger, "r-test-ledger", "theoria")
    run.run_start(game_id="sk48-d8078629", env_base="http://x", model_base=None,
                  env_upstream="https://three.arcprize.org", guard={},
                  variant=None, arm_version={}, upstream_pin={})

    desk = ModelDesk(run, model="claude-opus-5", cost_ceiling_usd=None,
                     spend=_scratch_binding(tmp_path),
                     transcript_dir=os.path.join(str(tmp_path), "desk"))
    desk._invoke = lambda prompt, model: (envelope, 1234, "")
    return desk, ledger


SUCCESS_ENVELOPE = {
    "type": "result", "subtype": "success", "result": "the reply",
    "total_cost_usd": 2.694961, "num_turns": 1,
    "usage": {"input_tokens": 2, "output_tokens": 100,
              "cache_creation_input_tokens": 5000, "cache_read_input_tokens": 0},
}


def test_a_desk_call_is_actually_accepted_by_the_frozen_writer(tmp_path):
    """The regression that cost $2.695 live.

    `LEDGER_FORMAT.md` §4 closed the `model_call` field set after P-8 landed,
    and P-8 wrote `beat`, `label`, `transport`, `proxied` and `proxy_gap`
    straight onto that record. `canon.py` refused all five, the write raised
    after the provider had been paid, and the reply was discarded: `desk.calls`
    said 1, `desk_log.json` was `[]`, and no transcript existed.
    """
    desk, ledger = _desk_on_a_real_ledger(tmp_path, SUCCESS_ENVELOPE)
    text = desk.call("prompt", beat="theorize", step_idx=7, label="round1")

    assert text == "the reply"
    assert desk.ledger_failures == [], desk.ledger_failures
    assert desk.summary()["calls_missing_from_ledger"] == 0

    records = ledger.read()
    calls = [r for r in records if r["event"] == "model_call"]
    assert len(calls) == 1, "the model_call never reached the ledger"
    # The closed shape carries none of the five at the top level...
    for banned in ("beat", "label", "transport", "proxied", "proxy_gap"):
        assert banned not in calls[0], banned
    # ...and `request`, which the caller owns, carries all of them, so `beat`
    # is still on the ledger and constraint 8 is still checkable from the file.
    request = calls[0]["request"]
    assert request["beat"] == "theorize"
    assert request["label"] == "round1"
    assert request["proxied"] is False
    assert request["transport"] == "claude-code-cli"
    assert "proxy_gap" in request


def test_constraint_8_still_reads_the_beat_after_the_migration(tmp_path):
    """`beat` on the ledger is what makes constraint 8 checkable rather than
    asserted. Moving it to an auxiliary must not quietly turn every call into
    `unknown`, which would report a violation that is really a migration."""
    from armtools.archive import constraint_8             # noqa: PLC0415

    desk, ledger = _desk_on_a_real_ledger(tmp_path, SUCCESS_ENVELOPE)
    desk.call("prompt", beat="theorize", step_idx=7, label="round1")

    report = constraint_8(ledger.read(), str(tmp_path))
    assert report["calls_by_beat"] == {"theorize": 1}
    assert report["calls_at_forbidden_beats"] == {}
    assert report["holds"] is True


def test_a_p8_era_ledger_with_the_beat_inline_still_reads(tmp_path):
    """The rejoin reads both sources. An older run's records carry `beat` on
    the call itself and must not be re-read as `unknown`."""
    from armtools.archive import constraint_8             # noqa: PLC0415

    records = [{"event": "model_call", "call_idx": 0, "beat": "theorize"}]
    report = constraint_8(records, str(tmp_path))
    assert report["calls_by_beat"] == {"theorize": 1}


def test_a_paid_reply_survives_a_ledger_that_refuses_it(tmp_path):
    """By the time the ledger is written the provider has been paid. Turning a
    bookkeeping refusal into a lost call is strictly worse than an incomplete
    ledger plus a loud entry saying so."""
    desk, ledger = _desk_on_a_real_ledger(tmp_path, SUCCESS_ENVELOPE)

    def refuse(**kwargs):
        raise ValueError("canon says no")

    desk.run.model_call = refuse

    text = desk.call("prompt", beat="theorize", step_idx=7, label="round1")
    assert text == "the reply"                    # the reply is NOT discarded
    assert len(desk.log) == 1                     # the arm's own record exists
    assert desk.log[0]["cli_cost_usd"] == 2.694961
    assert "canon says no" in desk.log[0]["ledger_error"]
    # ...and the incompleteness is impossible to miss in the summary.
    assert desk.summary()["calls_missing_from_ledger"] == 1
    assert desk.ledger_failures[0]["stage"] == "model_call"
    # The transcript is on disk too, so the money bought something readable.
    transcripts = os.listdir(os.path.join(str(tmp_path), "desk"))
    assert transcripts, "no transcript was written for a paid call"


# ------------------------------------------------------- the whole thing, mock
def _carried_run(tmp_path, slug_suffix, **arm_kwargs):
    """One full offline run against `proxy/mock`, started from carried books.

    Two things this helper must get right, and both were learned the expensive
    way by other tests in this suite:

    * the run lands in `FIXTURE_RUNS_DIR`, never in `runs/`. `runs/` is the
      archive, a fixture run cost nothing, and `armtools.verify_provenance`
      fails outright if one reappears there.
    * the spend claim is on a pool this test owns. `play()` defaults to the
      *shared* pool, and tests that forgot wrote 2 817 of its 4 775 actions.
    """
    from harness.run import FIXTURE_RUNS_DIR, play        # noqa: PLC0415
    from inner.loop import TheoriaArm                     # noqa: PLC0415
    from proxy.mock.arc_mock import DEFAULT_KEY, MockArc  # noqa: PLC0415
    from proxy.spend_gate import SpendGate                # noqa: PLC0415
    from harness import run as run_mod                    # noqa: PLC0415

    source = _books(tmp_path)
    game = "g50t-5849a774"
    slug = "pytest-e3-" + slug_suffix + "-" + os.path.basename(str(tmp_path))

    def factory(env_base, run):
        return TheoriaArm(env_base=env_base, run=run, game_id=game,
                          budget_actions=6, offline=True,
                          seed_books=source.root,
                          carry_source_game="g50t-5849a774",
                          prompt_id="E3-engines-online", **arm_kwargs)

    policy = run_mod._scratch_policy(str(tmp_path / "scratch-pool.jsonl"))
    gate = SpendGate(policy)
    expect = {"pool": policy.pool,
              "ledger_abspath": os.path.abspath(policy.ledger_path)}
    with MockArc(api_key=DEFAULT_KEY, games=[game]) as mock:
        summary = play(game, slug, factory, env_upstream=mock.base_url,
                       env_key=DEFAULT_KEY, require_key=False,
                       spend_gate=gate, expect_pool=expect,
                       runs_root=FIXTURE_RUNS_DIR,
                       ledger_path=str(tmp_path / "ledger.jsonl"))
    return summary, os.path.join(FIXTURE_RUNS_DIR, slug)


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
    # `total >= added` is true by construction (added = total - before, and
    # before >= 0), so it tests nothing. What matters is that the sweep put
    # rows in the stream at all.
    assert rows[0]["candidate_rows_added"] > 0, (
        "the cold dispatch appended no candidate rows")

    for name in ("mdl_segmenter", "cegis_miner", "zero_space"):
        row = rows[0]["engines"][name]
        # This assertion used to read `delivered or error or skipped`, which
        # expands to `(not error) or error or skipped` -- a tautology that an
        # engine returning `{}` passes. What has to be true is that the engine
        # SAID something: a result, a refusal, or an error.
        said_something = (
            row.get("error") or row.get("skipped")
            or row.get("n_refusals") or row.get("verdict")
            or row.get("n_tracks") is not None
            or row.get("n_laws") is not None
            or row.get("chosen_operator"))
        assert said_something, (name, row)

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
    from inner.levels import LevelLog                    # noqa: PLC0415
    from inner.loop import TheoriaArm                    # noqa: PLC0415

    arm = TheoriaArm.__new__(TheoriaArm)
    arm.run = type("R", (), {"run_id": "r-test"})()
    arm.store = store
    #: The dispatch sweeps the CURRENT LEVEL's trajectory, not the whole run's
    #: -- an engine sweep that straddles a level boundary is the category error
    #: `FrameStore.since` exists to prevent -- so a bare arm still needs the
    #: level log that says where the current level began. A fresh one starts at
    #: 0, which makes the level view and the whole store the same object's
    #: contents here, which is what these cases want.
    arm.levels = LevelLog()
    arm.dir = str(tmp_path)
    arm.candidates_path = os.path.join(str(tmp_path), "candidates.jsonl")
    arm.engine_log_path = os.path.join(str(tmp_path), "engines_online.jsonl")
    arm.engine_rounds = []
    arm._last_dispatch = None
    arm._last_dispatch_frames = -1
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

    # Not an identity check: the reused report is a shallow copy whose `store`
    # summary is refreshed (that key is not engine output and does go stale).
    # What must be identical is every engine's own report object.
    for engine in ("mdl_segmenter", "cegis_miner", "zero_space"):
        assert second[engine] is first[engine], (
            "the second dispatch re-ran %s" % engine)
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


def test_a_reused_dispatch_refreshes_the_world_summary_it_carries(tmp_path):
    """`run_engines` returns `store: store.summary()` beside the engine reports.
    That summary counts frameless steps -- a 500 on an action appends a step
    with no frame, which cannot change what the engines computed but does
    change what the world looks like. Left stale, `theorize` would put the live
    summary at the top of the desk's prompt and this one inside "what the
    engines proposed", and the two would disagree about the action that had
    just failed."""
    grids = [[[9, 0, 0, 0], [0, 0, 0, 0]],
             [[0, 9, 0, 0], [0, 0, 0, 0]]]
    store = _store(grids, ["ACTION1"])
    arm = _bare_arm(tmp_path, store)

    first = arm._dispatch_engines(label="cold")
    steps_before = first["store"]["steps"]

    # An action that failed: a step with no frames. No new grid, so the engine
    # cache legitimately hits -- but the world is not what it was.
    store.add(Step(2, "ACTION7", [], status=500))
    second = arm._dispatch_engines(label="theorize")

    assert arm.engine_rounds[1]["reused_from_dispatch_idx"] == 0
    assert second["store"]["steps"] == steps_before + 1, (
        "the reused report carried a stale world summary")
    assert "ACTION7" in second["store"]["actions_used"]


def test_the_cache_key_does_not_collide_on_the_first_frame(tmp_path):
    """`max(0, n-1)` is not injective at n in {0, 1}: a 200 carrying no frame
    leaves zero grids, and the first real frame also gave key 0, so the engines
    were handed an answer computed over no frames while one existed."""
    store = FrameStore()
    store.add(Step(0, "RESET", []))                 # 200, no frame
    arm = _bare_arm(tmp_path, store)
    first = arm._dispatch_engines(label="cold")

    store.add(Step(1, "ACTION1", [[[9, 0], [0, 0]]]))
    second = arm._dispatch_engines(label="theorize")

    assert "reused_from_dispatch_idx" not in arm.engine_rounds[1], (
        "the first real frame was answered from a zero-frame sweep")
    assert second is not first


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
    # The point of the test is that a refusal HAPPENED and was not counted as
    # an error. Without this line the test passes just as well when nothing
    # refuses, or when refusals stop being counted at all.
    assert miner["refused_with_reason"] > 0, (
        "this fixture is supposed to make cegis_miner refuse; it did not, so "
        "the rest of these assertions are about nothing")
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
    from harness import run as run_mod                    # noqa: PLC0415
    from harness.run import FIXTURE_RUNS_DIR, play        # noqa: PLC0415
    from inner.loop import TheoriaArm                     # noqa: PLC0415
    from proxy.mock.arc_mock import DEFAULT_KEY, MockArc  # noqa: PLC0415
    from proxy.spend_gate import SpendGate                # noqa: PLC0415

    game = "g50t-5849a774"
    slug = "pytest-e3-cold-start-" + os.path.basename(str(tmp_path))

    def factory(env_base, run):
        return TheoriaArm(env_base=env_base, run=run, game_id=game,
                          budget_actions=4, offline=True)

    policy = run_mod._scratch_policy(str(tmp_path / "scratch-pool.jsonl"))
    gate = SpendGate(policy)
    with MockArc(api_key=DEFAULT_KEY, games=[game]) as mock:
        summary = play(game, slug, factory, env_upstream=mock.base_url,
                       env_key=DEFAULT_KEY, require_key=False,
                       spend_gate=gate,
                       expect_pool={"pool": policy.pool,
                                    "ledger_abspath":
                                        os.path.abspath(policy.ledger_path)},
                       runs_root=FIXTURE_RUNS_DIR,
                       ledger_path=str(tmp_path / "ledger.jsonl"))

    run_dir = os.path.join(FIXTURE_RUNS_DIR, slug)
    assert summary["transfer"] is None
    assert not os.path.exists(os.path.join(run_dir, "transfer.json"))
    assert not os.path.exists(os.path.join(run_dir, "CARRIED.json"))
    # The engine record is not conditional on carrying, though.
    assert os.path.exists(os.path.join(run_dir, "engines_online.json"))
