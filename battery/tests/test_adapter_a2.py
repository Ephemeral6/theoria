"""The A2 adapter: the repair loop, and the four overlapping runs it lives in.

These tests are written against `cold-start-a2/` itself rather than a fixture.
A2 is a frozen, byte-reproducible bundle belonging to another track and this
battery only ever reads it, so the real artefacts are both available and the
thing actually being claimed about.  Two consequences worth stating:

* several assertions carry literal counts (248 frames, 183 transitions, 44
  anomalies).  They are the point, not incidental: if A2 is regenerated and a
  number moves, the battery's published figures are stale and a failure here
  is how anybody finds out.
* the mechanism cross-check (`test_derived_mechanism_uses_reproduce_the_worlds
  _own_record`) is the licence for the adapter deriving transition lists on the
  two traces `trace_summary.json` does not cover.  It compares the derivation
  against the record on the two traces that have both.
"""

import json
import os
import re

import pytest

from battery.adapters.a2 import (LOOP_TAGS, A2_ROOT, load_a2_runs,
                                 parse_word_table_accounts, rule_names,
                                 theorem_names)
from battery.adapters.a0 import _read_json, _read_jsonl, parse_dsl
from battery.metrics import REGISTRY, evaluate
from battery.model import digest

ARTIFACTS = os.path.join(A2_ROOT, "artifacts")


@pytest.fixture(scope="module")
def runs():
    return {r.run_id: r for r in load_a2_runs()}


@pytest.fixture(scope="module")
def loaded():
    return load_a2_runs()


# ----------------------------------------------------------------- the runs

def test_the_four_runs_load_in_the_loops_own_order(loaded):
    assert [r.run_id for r in loaded] == [
        "a2-sweep", "a2-play-record", "a2-probed", "a2-refutation"]
    for run in loaded:
        assert run.arm == "theoria_a2"
        assert run.source == "cold-start-a2"
        assert run.game_id is None            # a self-built world has no pile
        assert run.pile == "synthetic"
        assert run.model is None
        assert run.campaign is None


def test_trace_lengths_are_the_bundles_own(runs):
    """N records is N-1 steps: the last row is the `action: null` sentinel."""
    expected = {"a2-sweep": (248, 247), "a2-play-record": (184, 183),
                "a2-probed": (196, 195), "a2-refutation": (19, 18)}
    for run_id, (frames, steps) in expected.items():
        run = runs[run_id]
        assert run.notes["frames"] == frames
        assert len(run.steps) == steps
        assert all(not s.failed for s in run.steps)   # the world cannot error
        assert all(s.n_frames == 1 and s.level == 0 for s in run.steps)


def test_a_step_lands_on_the_state_its_action_produced(runs):
    """Row t holds the state *before* its action, so step i takes frame i+1."""
    rows = _read_jsonl(os.path.join(ARTIFACTS, "raw_trace.jsonl"))
    run = runs["a2-sweep"]
    for i in (0, 1, 90, 183, len(run.steps) - 1):
        assert run.steps[i].state_key == digest(rows[i + 1]["frame"])
        assert run.steps[i].action == str(rows[i]["action"])
    # And never the state it started from, which is the bug this guards.  A
    # blocked push leaves the board unchanged and cannot tell the two apart --
    # raw_trace's very first action is one -- so the check is made at the first
    # transition that actually moves something.
    moved = next(i for i in range(len(run.steps))
                 if rows[i + 1]["frame"] != rows[i]["frame"])
    assert run.steps[moved].state_key == digest(rows[moved + 1]["frame"])
    assert run.steps[moved].state_key != digest(rows[moved]["frame"])
    # the sentinel is not a step
    assert rows[-1]["action"] is None
    assert run.steps[-1].action != "None"


def test_the_win_flag_belongs_to_the_frame_the_action_produced(runs):
    """The 18th action is the one that wins, not the 19th record."""
    run = runs["a2-refutation"]
    assert run.steps[-1].won is True
    assert not any(s.won for s in run.steps[:-1])


# ------------------------------------------------------------- no model calls

def test_a2_ran_no_model_and_the_economy_family_says_so(loaded):
    """`not-applicable` is the correct answer here, not a gap."""
    economy = sorted(mid for mid, card in REGISTRY.items()
                     if card.family == "economy")
    assert economy, "no economy metrics are registered"
    for run in loaded:
        assert run.calls == []
        assert run.capabilities()["model_calls"] is False
        values = evaluate(run)
        for mid in economy:
            assert values[mid].status == "not-applicable", (
                "%s on %s: %s" % (mid, run.run_id, values[mid].status))
            assert values[mid].value is None
            assert values[mid].reason


# -------------------------------------------------------------- the concepts

def test_the_sweeps_concepts_come_from_the_dsl_not_the_empty_json(runs):
    """`concept_accounts.json["a2-base"]` is `[]`; the accounts are in prose."""
    accounts = _read_json(os.path.join(ARTIFACTS, "concept_accounts.json"))
    assert accounts["a2-base"] == [], "the trap this test exists for is gone"

    theory = runs["a2-sweep"].theory
    bits = {c.name: c.compression_bits for c in theory.concepts}
    assert bits == {"Cart": 1891, "Button": -5, "Door": -1}
    assert all(c.load_bearing for c in theory.concepts)
    assert all(c.admitted_revision == 1 for c in theory.concepts)
    assert "word_table" in runs["a2-sweep"].notes["concept_source"]
    # the declared span is the sweep's own length, which is how the manual
    # says which trace it is about
    assert runs["a2-sweep"].notes["concept_evidence_spans"]["Cart"] == 248


def test_the_other_two_manuals_take_their_accounts_from_the_json(runs):
    assert {c.name: c.compression_bits
            for c in runs["a2-play-record"].theory.concepts} == {
                "Cart": 1433, "Button": -5, "Door": -1}
    assert {c.name: c.compression_bits
            for c in runs["a2-probed"].theory.concepts} == {
                "Cart": 1521, "Button": -5, "Door": -1}
    assert "concept_accounts.json" in runs["a2-probed"].notes["concept_source"]


def test_the_dsl_fallback_agrees_with_the_json_where_both_exist():
    """What licenses the fallback: it reproduces the JSON on the two manuals
    that have both, so the sweep's numbers are not a different quantity."""
    truth = _read_json(os.path.join(ARTIFACTS, "ground_truth.json"))
    accounts = _read_json(os.path.join(ARTIFACTS, "concept_accounts.json"))
    for dsl, key in (("theory_holed.dsl", "a2-holed"),
                     ("theory_repaired.dsl", "a2-repaired")):
        parsed = parse_word_table_accounts(
            os.path.join(A2_ROOT, "theory", dsl), truth["objects"])
        recorded = {e["name"]: e for e in accounts[key]}
        assert {e["name"] for e in parsed} == set(recorded)
        for entry in parsed:
            other = recorded[entry["name"]]
            assert entry["script_delta_bits"] == other["script_delta_bits"]
            assert entry["load_bearing"] == other["load_bearing"]
            assert entry["colour"] == other["colour"]


# ---------------------------------------------------------------- the manuals

def test_the_three_manuals_and_their_revisions(runs):
    assert len(runs["a2-sweep"].theory.clauses) == 10       # 7 rules 2 inv 1 th
    assert len(runs["a2-play-record"].theory.clauses) == 9  # the deletion
    assert len(runs["a2-probed"].theory.clauses) == 11
    assert runs["a2-sweep"].theory.revisions == 1
    assert runs["a2-probed"].theory.revisions == 2
    assert runs["a2-refutation"].theory is None    # an episode is not a book


def test_a2_has_no_playbook_and_no_deadlock_theorem(runs):
    assert not os.path.exists(os.path.join(A2_ROOT, "theory", "playbook.dsl"))
    for run_id in ("a2-sweep", "a2-play-record", "a2-probed"):
        assert runs[run_id].theory.playbook_entries == 0
        assert runs[run_id].theory.deadlock_theorems == 0


def test_the_ragged_probe_record_is_read_without_a_keyerror(runs):
    """P-03 is `hypothetical` and carries none of the execution keys."""
    probes = _read_jsonl(os.path.join(ARTIFACTS, "probes.jsonl"))
    assert len(probes) == 5
    ragged = [p for p in probes if p["id"] == "P-03"][0]
    assert ragged["tier"] == "hypothetical"
    assert ragged["status"] == "not_separable_in_this_world"
    assert "action" not in ragged and "mover_cell" not in ragged
    for run_id in ("a2-sweep", "a2-play-record", "a2-probed"):
        assert runs[run_id].theory.probes_designed == 5
        assert runs[run_id].theory.probes_executable == 4


def test_the_replay_scores_come_from_each_manuals_own_certifier(runs):
    assert (runs["a2-sweep"].theory.replay_pairs,
            runs["a2-sweep"].theory.replay_agree) == (247, 247)
    assert (runs["a2-play-record"].theory.replay_pairs,
            runs["a2-play-record"].theory.replay_agree) == (183, 183)
    assert (runs["a2-probed"].theory.replay_pairs,
            runs["a2-probed"].theory.replay_agree) == (195, 195)


# --------------------------------------------------------------- the held-out

def test_the_holed_manuals_held_out_score_is_refused_not_invented(runs):
    """44 anomalies over a capped list is not a denominator."""
    run = runs["a2-play-record"]
    assert run.theory.held_out_pairs is None
    assert run.theory.held_out_agree is None
    assert run.notes["held_out"]["anomalies"] == 44
    assert run.notes["held_out"]["frames"] == 248
    assert run.notes["held_out"]["green"] is False
    assert run.notes["held_out"]["why_no_ratio"]
    # the number nobody may publish
    assert 247 - 44 not in (run.theory.held_out_agree,
                            run.theory.held_out_pairs)


def test_every_a2_manual_declares_its_held_out_frame(runs):
    for run_id in ("a2-sweep", "a2-play-record", "a2-probed"):
        frame = runs[run_id].theory.held_out_frame
        assert frame and isinstance(frame, str) and len(frame) > 20


# -------------------------------------------------------------- the mechanisms

def test_the_play_record_never_uses_the_portal_and_none_survives(runs):
    """The empty list is the whole exhibit; it must not become 0."""
    play = runs["a2-play-record"].truth.mechanisms
    assert play["portal"]["first_used"] is None
    assert runs["a2-sweep"].truth.mechanisms["portal"]["first_used"] == 183
    assert runs["a2-probed"].truth.mechanisms["portal"]["first_used"] == 194
    assert runs["a2-refutation"].truth.mechanisms["portal"]["first_used"] == 11


def test_the_door_is_not_a_passage_until_the_button_opens_it(runs):
    """A0's unlock convention, kept so the two arms stay comparable."""
    sweep = runs["a2-sweep"].truth.mechanisms
    assert sweep["button"]["first_used"] == 90
    assert sweep["door_passage"]["first_seen"] == 90      # not frame 0
    assert sweep["door_passage"]["first_used"] == 111


def test_derived_mechanism_uses_reproduce_the_worlds_own_record():
    """The licence for deriving them on the two traces with no summary."""
    from battery.adapters.a2 import _derive_transitions

    truth = _read_json(os.path.join(ARTIFACTS, "ground_truth.json"))
    summary = _read_json(os.path.join(ARTIFACTS, "trace_summary.json"))
    for trace, key in (("raw_trace.jsonl", "raw_trace"),
                       ("history_trace.jsonl", "history_trace")):
        rows = _read_jsonl(os.path.join(ARTIFACTS, trace))
        derived = _derive_transitions([r["frame"] for r in rows],
                                      truth["palette"],
                                      truth["spec"]["door_cell"])
        for field in ("button_press_transitions", "portal_transitions",
                      "door_entry_transitions"):
            assert derived[field] == summary[key][field], (trace, field)


# ------------------------------------------------------------------ the repair

def test_exactly_one_run_carries_the_repair(loaded):
    carrying = [r.run_id for r in loaded if r.repairs]
    assert carrying == ["a2-probed"]
    assert len(loaded[2].repairs) == 1


def test_the_loop_is_six_beats_all_closed_costing_fortyeight_actions(runs):
    repair = runs["a2-probed"].repairs[0]
    assert [b.tag for b in repair.beats] == list(LOOP_TAGS)
    assert len(repair.beats) == 6 == repair.beats_required
    assert repair.beats_closed == 6
    assert all(b.closed for b in repair.beats)
    # L6 re-executes the repaired plan against a fresh world, and that replay
    # is billed: the actions really run, 解出 is a beat by Theoria.md's own
    # definition, and the unbilled reading is the one that flatters this
    # project's registered K13 prediction. DECISIONS.md D-B-015.
    assert {b.tag: b.env_actions for b in repair.beats} == {
        "L1": 18, "L2": 0, "L3": 12, "L4": 0, "L5": 0, "L6": 18}
    assert repair.env_actions == 48 == repair.repair_actions
    assert all(b.note for b in repair.beats), "a derived cost with no basis"


def test_the_rejected_verification_convention_stays_recoverable(runs):
    """The number this adapter did *not* publish is still on the record.

    A convention that silently discards its alternative is a convention nobody
    can argue with.
    """
    repair = runs["a2-probed"].repairs[0]
    assert repair.notes["repair_actions_if_l6_verification_unbilled"] == 30
    assert "BILLS" in repair.notes["verification_convention"]


def test_each_derived_beat_cost_matches_the_file_it_came_from():
    refutation = _read_json(os.path.join(ARTIFACTS, "refutation.json"))
    probe = _read_json(os.path.join(ARTIFACTS, "probe_report.json"))
    assert refutation["episode"]["length"] == 18
    assert probe["trace_frames_after"] - probe["trace_frames_before"] == 12
    # the same 12, counted a second way: navigation plus the probe action
    executable = [p for p in probe["probes"] if p["tier"] == "executable"]
    assert len(executable) == 4
    assert sum(p["navigation_steps"] for p in executable) + 4 == 12


def test_the_prologue_beats_are_not_counted_as_loop_beats(runs):
    ledger = _read_json(os.path.join(ARTIFACTS, "loop_ledger.json"))
    assert ledger["summary"] == {"pass": 8, "fail": 0, "absent": 0, "total": 8}
    repair = runs["a2-probed"].repairs[0]
    assert [b["beat"] for b in repair.notes["prologue_beats"]] == ["M0", "M5"]
    assert repair.notes["ledger_summary"]["total"] == 8
    assert len(repair.beats) == 6      # and the loop is still six


def test_the_repair_invalidated_exactly_one_theorem(runs):
    holed, _ = parse_dsl(os.path.join(A2_ROOT, "theory", "theory_holed.dsl"))
    repaired, _ = parse_dsl(os.path.join(A2_ROOT, "theory",
                                         "theory_repaired.dsl"))
    assert theorem_names(holed) == ["right_room_locked"]
    assert "right_room_locked" not in theorem_names(repaired)
    assert set(rule_names(repaired)) - set(rule_names(holed)) == {
        "teleport_down"}

    repair = runs["a2-probed"].repairs[0]
    assert repair.invalidated_theorems == 1
    assert repair.theorems_before == 1
    assert repair.notes["invalidated"] == ["right_room_locked"]
    assert repair.changed_clause == "teleport_down"
    assert repair.strategy == "patch"


def test_the_repair_cost_is_read_against_what_the_theory_cost(runs):
    repair = runs["a2-probed"].repairs[0]
    assert repair.baseline_actions == 183     # the play record it was mined on
    assert repair.repair_actions == 48
    assert repair.detected is True
    assert repair.detection_actions == 11     # locate_report.json located.t
    assert repair.actions_examined == 18
    assert repair.trigger and "right_room_locked" in repair.trigger


def test_the_exhibit_would_have_shipped_a_false_theorem(runs):
    """Set from evidence: Lean-green, axiom-free, and false of the world."""
    exhibit = _read_json(os.path.join(ARTIFACTS, "exhibit_report.json"))
    assert exhibit["certify_lean"]["green"] is True
    assert exhibit["certify_lean"]["axiom_reports"][0]["axioms"] == []
    assert exhibit["exhibit_is_false_of_the_world"] is True
    repair = runs["a2-probed"].repairs[0]
    assert repair.silently_wrong_without_tracking is True
    assert repair.notes["stale_certificate_died"] is True


# --------------------------------------------------------------- the solve

def test_the_refutation_is_the_first_run_that_can_be_asked_for_p4(runs):
    run = runs["a2-refutation"]
    assert run.intent == "solve"
    assert run.truth.optimal_steps == 18
    assert run.capabilities()["solve_attempt"] is True
    p4 = evaluate(run)["P4"]
    assert p4.status == "ok"
    assert p4.value == 1.0                # 18 actions against an 18 optimum


def test_the_exploration_traces_are_not_scored_for_path_efficiency(runs):
    """The sweep is 13.7x optimal, which measures its purpose, not the arm."""
    for run_id in ("a2-sweep", "a2-play-record", "a2-probed"):
        run = runs[run_id]
        assert run.intent == "explore"
        assert evaluate(run)["P4"].status == "not-applicable"


# ----------------------------------------------------------- the overlap trap

def test_the_four_runs_overlap_and_every_run_says_so(runs):
    raw = _read_jsonl(os.path.join(ARTIFACTS, "raw_trace.jsonl"))
    history = _read_jsonl(os.path.join(ARTIFACTS, "history_trace.jsonl"))
    probed = _read_jsonl(os.path.join(ARTIFACTS, "probed_trace.jsonl"))
    assert history[:183] == raw[:183]
    assert probed[:183] == raw[:183]
    for run in runs.values():
        assert run.notes["overlaps"]


def test_the_traces_must_not_be_deduped_on_t_and_frame():
    """Record 183 shares a frame across two traces and disagrees on action."""
    history = _read_jsonl(os.path.join(ARTIFACTS, "history_trace.jsonl"))
    probed = _read_jsonl(os.path.join(ARTIFACTS, "probed_trace.jsonl"))
    assert history[183]["frame"] == probed[183]["frame"]
    assert history[183]["action"] is None       # the truncation sentinel
    assert probed[183]["action"] == "LEFT"      # back-filled by the probe run


# ------------------------------------------------------- provenance & hygiene

def test_the_upstream_pin_travels_with_every_run(runs):
    pin = _read_json(os.path.join(ARTIFACTS, "upstream_pin.json"))
    assert len(pin["sha256"]) == 22 and pin["missing"] == []
    for run in runs.values():
        provenance = run.notes["upstream_pin"]
        assert provenance["upstream_files_pinned"] == 22
        assert provenance["upstream_files_missing"] == 0
        assert provenance["repo_head_when_pinned"] == pin[
            "repo_head_when_pinned"]


def test_no_machine_local_path_leaks_into_a_run(loaded):
    """`repair_report.json` and `loop_ledger.json` both carry absolute Windows
    paths; the battery's output has to be machine-independent."""
    blob = json.dumps([{"notes": r.notes,
                        "repairs": [{"notes": p.notes,
                                     "beats": [b.note for b in p.beats],
                                     "trigger": p.trigger}
                                    for p in r.repairs]}
                       for r in loaded], ensure_ascii=False, default=str)
    assert not re.search(r"[A-Za-z]:\\\\", blob)
    assert "\\\\Users\\\\" not in blob
    assert ".elan" not in blob and "theoria-wt" not in blob
    assert "C:" not in blob


# ---------------------------------------------------------------- determinism

def test_loading_twice_yields_identical_runs():
    first, second = load_a2_runs(), load_a2_runs()
    assert first == second
    dump = json.dumps([[s.state_key for s in r.steps] for r in first])
    assert dump == json.dumps(
        [[s.state_key for s in r.steps] for r in second])
    # and the orderings that a `set` would have scrambled
    for a, b in zip(first, second):
        assert [c.name for c in (a.theory.concepts if a.theory else [])] == \
               [c.name for c in (b.theory.concepts if b.theory else [])]
        assert sorted(a.truth.mechanisms) == sorted(b.truth.mechanisms)
        assert list(a.truth.mechanisms) == list(b.truth.mechanisms)
