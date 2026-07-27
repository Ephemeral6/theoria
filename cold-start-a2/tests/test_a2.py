"""A2's test suite.  Run `python run_all.py` first — these read its artefacts.

The suite is organised around the two acceptance sentences rather than around
the modules, because that is what A2 is judged on:

  仪器造得出展品 — the instrument can build the exhibit  (TestWorld ..
                    TestExhibit)
  回路转得起来   — the loop turns                        (TestLoop)

plus the red lines INC-004 attached to the substitution (TestRedLines) and the
frozen contracts everything has to keep (TestContracts).
"""

import json
import os
import re
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(ROOT)
ARTIFACTS = os.path.join(ROOT, "artifacts")

sys.path.insert(0, ROOT)

import _bootstrap  # noqa: F401,E402

from a2world import a2_world  # noqa: E402
from a2world.explorer import stratum  # noqa: E402


def artifact(name):
    path = os.path.join(ARTIFACTS, name)
    if not os.path.exists(path):
        pytest.skip("%s missing — run `python run_all.py` first" % name)
    with open(path, encoding="utf-8") as handle:
        if name.endswith(".jsonl"):
            return [json.loads(line) for line in handle if line.strip()]
        return json.load(handle)


def dsl(name):
    with open(os.path.join(ROOT, "theory", name), encoding="utf-8") as handle:
        return handle.read()


def rule_names(text):
    return [m.group(1) for m in re.finditer(r"^\s*rule (\w+)", text, re.M)]


# ---------------------------------------------------------------- the world

class TestWorld:
    """The world has to have the shape the exhibit needs, by construction."""

    def test_goal_is_reachable(self):
        world = a2_world.A2World()
        assert world.solve() is not None

    def test_goal_is_unreachable_without_the_teleport(self):
        # The exhibit's whole claim.  If this were solvable the holed manual's
        # theorem would be true and there would be no exhibit.
        world = a2_world.A2World()
        assert world.solve(holed=True) is None

    def test_the_only_non_adjacent_move_is_the_teleport(self):
        world = a2_world.A2World()
        jumps = [
            (s.cart, world.step(s, a).cart)
            for s in world.reachable() for a in a2_world.ACTIONS
            if abs(s.cart[0] - world.step(s, a).cart[0])
            + abs(s.cart[1] - world.step(s, a).cart[1]) > 1
        ]
        assert jumps and all(b == a2_world.PORTAL_DEST for _a, b in jumps)
        assert {a for a, _b in jumps} == {a2_world.DOOR_CELL}

    def test_the_pocket_is_never_occupied(self):
        world = a2_world.A2World()
        assert not [s for s in world.reachable()
                    if s.cart == a2_world.POCKET_CELL]
        assert not [s for s in world.reachable(holed=True)
                    if s.cart == a2_world.POCKET_CELL]

    def test_the_dividing_wall_is_solid(self):
        world = a2_world.A2World()
        assert all((r, 5) in world.walls for r in range(a2_world.HEIGHT))

    def test_strata_are_monotone(self):
        world = a2_world.A2World()
        for state in world.reachable():
            for action in a2_world.ACTIONS:
                assert stratum(world.step(state, action)) >= stratum(state)


# ---------------------------------------------------------------- the traces

class TestTraces:
    def test_history_is_a_prefix_of_the_sweep(self):
        sweep = artifact("raw_trace.jsonl")
        history = artifact("history_trace.jsonl")
        assert len(history) < len(sweep)
        for i, row in enumerate(history):
            assert row["frame"] == sweep[i]["frame"]
            if i < len(history) - 1:
                assert row["action"] == sweep[i]["action"]
        assert history[-1]["action"] is None

    def test_the_cut_is_the_teleport(self):
        summary = artifact("trace_summary.json")
        sweep = artifact("raw_trace.jsonl")
        cut = summary["portal_transition"]
        assert len(artifact("history_trace.jsonl")) == cut + 1
        assert sweep[cut]["action"] == "DOWN"

    def test_history_omits_exactly_the_teleport_pair(self):
        summary = artifact("trace_summary.json")
        assert summary["history_omits_exactly_one_pair"] is True
        assert summary["history_omitted_pairs"] == [
            "cart=(6,4) pressed=1 act=DOWN"]

    def test_sweep_covers_everything(self):
        summary = artifact("trace_summary.json")
        k, n = summary["raw_trace"]["coverage"].split("/")
        assert k == n

    def test_the_history_never_shows_a_jump(self):
        history = artifact("history_trace.jsonl")

        def cell(frame):
            return next((r, c) for r, row in enumerate(frame)
                        for c, v in enumerate(row) if v == a2_world.CART)
        for i in range(len(history) - 1):
            a, b = cell(history[i]["frame"]), cell(history[i + 1]["frame"])
            assert abs(a[0] - b[0]) + abs(a[1] - b[1]) <= 1


# --------------------------------------------------------------- the manuals

class TestManuals:
    def test_the_hole_is_exactly_one_rule(self):
        complete = set(rule_names(dsl("theory.dsl")))
        holed = set(rule_names(dsl("theory_holed.dsl")))
        assert complete - holed == {"teleport_down"}
        assert holed - complete == set()

    def test_the_repair_restores_exactly_that_rule(self):
        holed = set(rule_names(dsl("theory_holed.dsl")))
        repaired = set(rule_names(dsl("theory_repaired.dsl")))
        assert repaired - holed == {"teleport_down"}
        assert holed - repaired == set()

    def test_the_repair_agrees_with_the_control_on_that_rule(self):
        # Written from probes.jsonl, not copied — the agreement is the result.
        def clause(text):
            return re.search(r"rule teleport_down.*?\n\s*(when .*?)\n",
                             text, re.S).group(1).strip()
        assert clause(dsl("theory_repaired.dsl")) == clause(dsl("theory.dsl"))

    def test_every_manual_declares_its_semantics(self):
        for name in ("theory.dsl", "theory_holed.dsl", "theory_repaired.dsl"):
            text = dsl(name)
            assert "semantics:" in text
            for statement in ("frame persist", "conflict exclusive",
                              "cascade single_frame"):
                assert statement in text, (name, statement)

    def test_the_engines_back_the_hole(self):
        diff = artifact("engines_diff.json")
        assert diff["verdict"]["sweep_proposes_a_jump"] is True
        assert diff["verdict"]["history_proposes_a_jump"] is False


# --------------------------------------------------------------- the exhibit

class TestExhibit:
    """仪器造得出展品 — every gate green, and the theorem still false."""

    def test_the_holed_manual_replays_the_play_record_perfectly(self):
        report = artifact("exhibit_report.json")
        assert report["certify_cheap"]["green"] is True
        assert report["certify_cheap"]["anomaly_kinds"] == []
        assert report["certify_cheap"]["frames"] == 184

    def test_the_hole_is_visible_against_the_full_sweep(self):
        # The claim is bounded, not universal: invisible to the evidence its
        # theorizer had, not invisible.
        report = artifact("exhibit_report.json")
        assert report["certify_cheap_vs_full_sweep"]["green"] is False

    def test_the_planner_says_unsat(self):
        assert artifact("exhibit_report.json")["plan"]["status"] == "UNSAT"

    def test_lean_signs_it_with_no_axioms(self):
        report = artifact("exhibit_report.json")
        assert report["certify_lean"]["available"] is True
        assert report["certify_lean"]["green"] is True
        assert report["certify_lean"]["errors"] == []
        assert report["certify_lean"]["sorries"] == []
        assert report["theorem"]["axioms"] == [
            {"name": "unsolvable", "axioms": []}]

    def test_and_the_theorem_is_false_of_the_world(self):
        report = artifact("exhibit_report.json")
        assert report["exhibit_green"] is True
        assert report["exhibit_is_false_of_the_world"] is True

    def test_the_lean_file_uses_decide_and_not_native_decide(self):
        with open(os.path.join(ROOT, "theory", "generated_holed", "theory.lean"),
                  encoding="utf-8") as handle:
            source = handle.read()
        assert "native_decide" not in source
        assert "decide" in source
        assert "sorry" not in source


# ------------------------------------------------------------------ the loop

class TestLoop:
    """回路转得起来 — six beats, each with an artefact that settles it."""

    def test_refutation(self):
        report = artifact("refutation.json")
        assert report["refuted"] is True
        assert report["episode"]["final_win"] is True
        assert report["claim"]["lean_green"] is True

    def test_the_solved_episode_is_frames_only(self):
        rows = artifact("solved_episode.jsonl")
        assert rows and rows[-1]["win"] is True
        assert set(rows[0]) == {"t", "frame", "action", "win"}

    def test_localisation_names_exactly_one_of_the_three(self):
        report = artifact("locate_report.json")
        assert report["culprits"] == ["mispredicted_step"]
        assert report["checks"]["misread_board"] is False
        assert report["checks"]["wrong_goal_test"] is False

    def test_localisation_points_at_the_deleted_rule(self):
        located = artifact("locate_report.json")["located"]
        assert tuple(located["mover_at"]) == a2_world.DOOR_CELL
        assert located["action"] == "DOWN"
        assert tuple(located["world_shows"]) == a2_world.PORTAL_DEST
        assert located["rules_that_fired"] == []

    def test_the_probe_wrote_its_prediction_before_acting(self):
        probes = {p["id"]: p for p in artifact("probes.jsonl")}
        p1 = probes["P-01"]
        assert "holed_manual__nothing_happens" in p1["predictions"]
        assert p1["predictions"]["holed_manual__nothing_happens"] == "stays"
        assert p1["observation"] == "jumps to (7,6)"
        assert "holed_manual__nothing_happens" in p1["refuted"]
        assert p1["surviving"] == ["missing_rule__teleport_to_7_6"]

    def test_the_unrunnable_probe_is_recorded_not_dropped(self):
        probes = {p["id"]: p for p in artifact("probes.jsonl")}
        assert probes["P-03"]["status"] == "not_separable_in_this_world"
        assert probes["P-03"]["tier"] == "hypothetical"

    def test_the_pocket_ring_was_probed_before_it_was_proved(self):
        probes = [p for p in artifact("probes.jsonl") if p["id"].startswith("P-02")]
        assert len(probes) == 3
        assert all(p["surviving"] == ["ring_is_solid"] for p in probes)

    def test_the_trace_grew_and_stayed_replayable(self):
        report = artifact("probe_report.json")
        assert report["trace_frames_after"] > report["trace_frames_before"]
        assert artifact("repair_report.json")["certify_cheap"]["green"] is True

    def test_the_repair_is_re_derivable_from_the_grown_evidence(self):
        diff = artifact("engines_diff_probed.json")
        assert diff["verdict"]["probed_evidence_proposes_a_jump"] is True

    def test_the_refuted_certificate_dies(self):
        stale = artifact("repair_report.json")["stale_certificate"]
        assert stale["died"] is True
        assert stale["lean"]["green"] is False
        assert stale["lean"]["errors"]

    def test_a_true_certificate_replaces_it(self):
        report = artifact("repair_report.json")
        assert report["certify_lean"]["green"] is True
        assert report["certify_lean"]["axiom_reports"] == [
            {"name": "unsolvable", "axioms": []}]
        assert report["scored_against_the_world"]["true_of_the_world"] is True
        assert report["scored_against_the_world"][
            "world_states_with_cart_in_pocket"] == 0

    def test_the_two_theorems_have_the_same_shape(self):
        # The instrument cannot tell them apart; that is the finding.
        def body(where):
            with open(os.path.join(ROOT, "theory", where, "theory.lean"),
                      encoding="utf-8") as handle:
                return handle.read()
        false_one, true_one = body("generated_holed"), body("generated_repaired")
        for source in (false_one, true_one):
            assert "theorem unsolvable" in source
            assert "#print axioms unsolvable" in source
            assert "native_decide" not in source

    def test_the_engine_law_had_to_be_widened(self):
        region = artifact("repair_report.json")["region"]
        assert region["zero_space_size"] < region["adopted_size"]
        assert region["pocket_in_closure"] is False

    def test_solved(self):
        plan = artifact("repair_report.json")["plan"]
        assert plan["status"] == "SAT"
        assert plan["manual_reaches_goal"] is True
        assert plan["world_reaches_goal"] is True
        assert plan["execution_mismatches"] == []

    def test_the_ledger_is_all_green(self):
        ledger = artifact("loop_ledger.json")
        assert ledger["summary"]["fail"] == 0
        assert ledger["summary"]["absent"] == 0
        assert ledger["green"] is True


# ------------------------------------------------------------------ red lines

class TestRedLines:
    """INC-004 attached conditions to the substitution.  These check them."""

    def _tree(self):
        """Every file A2 ships, except this suite.

        `tests/` is excluded because the checks below have to *name* the strings
        they forbid, and a scanner that flags its own predicate is a scanner
        that can only be satisfied by obfuscating it.
        """
        for base, dirs, files in os.walk(ROOT):
            dirs[:] = [d for d in dirs
                       if d not in ("__pycache__", ".pytest_cache", ".git",
                                    "tests")]
            for name in files:
                if name.endswith((".pyc", ".zip")):
                    continue
                yield os.path.join(base, name)

    def test_no_dc22_artifact_is_present(self):
        # The sealed game's id.  It may be named in prose (INC-004 permits
        # citing §1.3's structural description); no artefact of it may exist.
        for path in self._tree():
            with open(path, "rb") as handle:
                blob = handle.read()
            assert b"fdcac232" not in blob, path

    def test_nothing_here_can_reach_the_network(self):
        for path in self._tree():
            if not path.endswith(".py"):
                continue
            with open(path, encoding="utf-8") as handle:
                source = handle.read()
            for banned in ("import requests", "import urllib", "import http",
                           "import socket", "ARC_API_KEY"):
                assert banned not in source, (path, banned)

    def test_a2_never_writes_into_the_other_track(self):
        # Reuse is read-only.  `COLD_START_A0` may only be referenced by the
        # bootstrap that puts it on sys.path and by the hasher that pins it.
        allowed = {os.path.join(ROOT, "_bootstrap.py"),
                   os.path.join(ROOT, "a2pipeline", "concepts.py")}
        for path in self._tree():
            if not path.endswith(".py") or path in allowed:
                continue
            with open(path, encoding="utf-8") as handle:
                source = handle.read()
            assert "COLD_START_A0" not in source, path

    def test_the_upstream_pin_is_complete(self):
        pin = artifact("upstream_pin.json")
        assert pin["missing"] == []
        assert all(v for v in pin["sha256"].values())


# ----------------------------------------------------------------- contracts

class TestContracts:
    def test_every_candidate_stream_validates(self):
        streams = [os.path.join(ARTIFACTS, n) for n in sorted(os.listdir(ARTIFACTS))
                   if n.startswith("candidates") and n.endswith(".jsonl")]
        assert streams
        proc = subprocess.run(
            [sys.executable, "-m", "tools.validate_candidates"] + streams,
            cwd=os.path.join(REPO, "engine-rig"), capture_output=True)
        assert proc.returncode == 0, proc.stdout.decode("utf-8", "replace")

    def test_engines_never_adjudicate(self):
        for name in sorted(os.listdir(ARTIFACTS)):
            if not (name.startswith("candidates") and name.endswith(".jsonl")):
                continue
            for row in artifact(name):
                assert row["status"] == "candidate", name

    def test_the_frozen_schema_was_not_touched(self):
        proc = subprocess.run(
            ["git", "status", "--porcelain", "CONTRACTS/"],
            cwd=REPO, capture_output=True)
        assert proc.stdout.decode("utf-8", "replace").strip() == ""
