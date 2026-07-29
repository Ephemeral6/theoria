"""Axis B's own bookkeeping: the columns, the corrections and the refusals.

`test_ic3bounds_reencode.py` pins the claim that a re-encoding preserves the
world.  This file pins what the axis does with that: which numbers it publishes,
which it refuses to publish, and which of its safeguards actually fire.  The
three that would quietly poison the table if they broke get a test each --

* `n_states` is corrected away from the harness's `2 ** n`.  On an `onehot` rung
  that default is 2^256, and a row carrying it would say IC3 searched a space
  larger than the observable universe in a fifth of a second.
* a rung with no native form reads `no native form` and never scores as a pass;
* a rung's `native` encoding is the axis A row it claims to extend.
"""

import json

import pytest

from ic3bounds import (axis_predicates, axis_size, harness, recheck_column,
                       reencode)
from ic3bounds.harness import AnchorDrift

BOARD = 4
BUDGET = 120.0


def _spec(scheme, k=0, board=BOARD):
    return axis_predicates.spec_for_peg(board, scheme, k)


def _measure(scheme, k=0, board=BOARD):
    """One rung in-process, with the columns the parent would attach.

    In-process rather than through `run_step` because a subprocess per
    parametrised case would make this file cost minutes; `measure_one` is the
    child's body verbatim, so it measures the same thing.
    """
    spec = _spec(scheme, k, board)
    record = axis_predicates.measure_one(spec)
    record["derived"] = axis_predicates.derived(record, spec)
    record["recheck"] = axis_predicates.recheck_for(record, spec)
    return spec, record


# ------------------------------------------------------- the state count is real

@pytest.mark.parametrize("scheme,k", [
    (reencode.BINARY, 0), (reencode.NATIVE, 0),
    (reencode.DUAL, 2), (reencode.DUAL, 4), (reencode.ONEHOT, 0),
])
def test_every_rung_of_a_block_searched_the_same_state_space(scheme, k):
    """The axis's premise, asserted per rung rather than assumed once."""
    spec, record = _measure(scheme, k)
    assert record["deterministic"]["n_states"] == 16
    assert spec.n_states == 16


def test_the_onehot_rung_does_not_claim_to_have_searched_two_to_the_m():
    """The correction, caught in the act.

    `harness._blank_deterministic` fills `n_states` as `2 ** n` because on peg-N
    the bit space IS the state space.  On an onehot rung n is 16 and 2^16 is
    65536, against sixteen real states -- so this asserts both that the raw
    default is wrong here and that the correction is what removed it.
    """
    spec = _spec(reencode.ONEHOT)
    assert spec.n == 16
    assert harness._blank_deterministic(spec.n)["n_states"] == 65536
    record = axis_predicates.measure_one(spec)
    assert record["deterministic"]["n_states"] == 16


def test_abstraction_is_one_exactly_when_the_engine_enumerated():
    """`onehot` converges on the reachable set itself and nothing more.

    That is a sound inductive invariant and it is also the engine doing
    reachability under another name, which is the distinction this column
    exists to make visible.  `native` on the same states abstracts by an order
    of magnitude, and the two rows are otherwise the same problem.
    """
    _, onehot = _measure(reencode.ONEHOT)
    _, native = _measure(reencode.NATIVE)
    assert onehot["derived"]["abstraction"] == 1.0
    assert onehot["deterministic"]["n_satisfying"] == 2       # peg4/0111 reaches 2
    assert native["derived"]["abstraction"] > 1.0


def test_the_reachable_count_is_the_denominator_and_comes_from_the_relation():
    system = axis_predicates.peg_base(BOARD, "0111", "0100")
    assert axis_predicates.reachable_count(system) == 2
    assert _spec(reencode.NATIVE).n_reachable == 2


# ------------------------------------------------------------- the recheck column

@pytest.mark.parametrize("k", (0, 1, 2, 3, 4))
def test_a_dual_rung_is_rechecked_in_full_through_its_native_form(k):
    _, record = _measure(reencode.DUAL, k)
    column = record["recheck"]
    assert column["status"] == "ACCEPT"
    assert column["counts_agree"] is True
    assert column["agrees_with_recorded_row"] is True
    assert recheck_column.is_pass(column) is True
    assert "rechecked through the native form" in column["detail"]


def test_the_native_rung_rechecks_against_the_committed_peg_case():
    _, record = _measure(reencode.NATIVE)
    column = record["recheck"]
    assert column["ruleset"] == "peg4-0111"
    assert column["ruleset_source"] == "recheck/cases/peg4-0111.rules.json"
    assert column["engine_n_satisfying"] == column["recheck_n_satisfying"] == 8


def test_a_rung_with_no_native_form_is_not_scored_and_is_not_a_finding():
    """It is a boundary, not a defect.

    `recheck/` cannot read a certificate written in state ordinals, and that is
    the answer to one of the three questions the item asked -- 'where does it
    produce a certificate that cannot be rechecked'.  So the row says so, is
    never counted as a pass, and does NOT fail the run: a run that exited 1 here
    would be reporting its own finding as a crash.
    """
    _, record = _measure(reencode.ONEHOT)
    column = record["recheck"]
    assert column["status"] == axis_predicates.RECHECK_NOT_AVAILABLE
    assert column["finding"] is False
    assert recheck_column.is_pass(column) is False
    assert column["counts_agree"] is None
    assert "not a pass" in column["detail"].lower()


def test_binary_on_peg_is_rechecked_because_it_IS_the_worlds_vocabulary():
    """The column follows the measurement, not the scheme's name.

    `binary` was reported as unreadable for one draft on the strength of being
    called `binary`.  On peg-N its predicates are the world's own in reverse
    declaration order -- a renaming `reencode.renaming_map` finds by comparing
    every predicate against every state -- so the certificate is readable, and
    it is rechecked like any other.  Four rungs changed verdict when this
    stopped being read off the scheme name.
    """
    spec, record = _measure(reencode.BINARY)
    assert record["derived"]["vocabulary"] == "world (renamed)"
    assert record["derived"]["is_a_renaming_of_the_world"] is True
    assert record["recheck"]["status"] == "ACCEPT"
    assert recheck_column.is_pass(record["recheck"]) is True


def test_the_adjudicable_column_is_measured_not_read_off_the_scheme():
    binary = _measure(reencode.BINARY)[1]["derived"]
    onehot = _measure(reencode.ONEHOT)[1]["derived"]
    assert binary["adjudicable"] is True and onehot["adjudicable"] is False
    assert onehot["vocabulary"] == "state index"


def test_a_row_without_an_invariant_reads_no_invariant_rather_than_passing():
    spec = _spec(reencode.NATIVE)
    record = axis_predicates.measure_one(spec)
    record["deterministic"]["verdict"] = harness.TIMEOUT
    column = axis_predicates.recheck_for(record, spec)
    assert column["status"] == recheck_column.NO_INVARIANT
    assert recheck_column.is_pass(column) is False
    assert column["finding"] is False


def test_a_broken_translation_would_be_a_finding_rather_than_a_pass():
    """The safeguard behind the recheck column, fired on purpose.

    `recheck_for` recounts the native form with the engine's own checker and
    compares it with the recoded row.  A bijection cannot change a set's size,
    so the two can only differ if the rewriting is wrong -- and a safeguard that
    can never fire is not a safeguard, so this makes it fire.
    """
    spec = _spec(reencode.DUAL, 2)
    record = axis_predicates.measure_one(spec)
    record["deterministic"]["n_satisfying"] += 1
    column = axis_predicates.recheck_for(record, spec)
    assert column["status"] == "translation-mismatch"
    assert column["finding"] is True
    assert recheck_column.is_pass(column) is False


def test_the_recheck_column_carries_no_absolute_path_or_wall_clock():
    _, record = _measure(reencode.DUAL, 2)
    blob = json.dumps(record["recheck"])
    for leak in ("C:\\", "/home/", "/tmp/", "engine-rig", "seconds"):
        assert leak not in blob


# ------------------------------------------------------------------ the columns

def test_derived_is_a_pure_function_a_verify_pass_can_re_derive():
    spec, record = _measure(reencode.DUAL, 2)
    assert axis_predicates.derived(record, spec) == record["derived"]


def test_the_derived_columns_are_not_in_the_deterministic_half():
    """They are compared key by key by a verify pass over ALL three axes, so a
    key added here would make every axis A artefact fail that comparison.

    The second assertion is the one that bites: a derived column echoing a
    deterministic one is a second copy that a verify pass does not compare and
    can therefore drift from the copy it does.
    """
    _, record = _measure(reencode.DUAL, 2)
    assert set(record["deterministic"]) == set(harness.DETERMINISTIC_FIELDS)
    assert set(record["derived"]).isdisjoint(harness.DETERMINISTIC_FIELDS)
    assert "n_states" not in record["derived"]


def test_a_spec_survives_the_process_boundary_it_actually_crosses():
    """It is handed to the child as JSON on a command line, so a field that did
    not serialise would reach the child as its default and be measured."""
    spec = _spec(reencode.DUAL, 3)
    again = axis_predicates.PredicateSpec.from_json(
        json.loads(json.dumps(spec.as_json(), sort_keys=True)))
    assert again == spec
    assert again.scheme == reencode.DUAL and again.k == 3
    assert again.n_states == 16 and again.n_reachable == 2


def test_the_encoding_label_names_the_rung_a_reader_sees():
    assert _spec(reencode.DUAL, 2).encoding_label == "dual+2"
    assert _spec(reencode.ONEHOT).encoding_label == "onehot"
    assert _spec(reencode.BINARY).encoding_label == "binary"


# ------------------------------------------------------------------- the blocks

def _block(rows):
    return {"board": "peg4", "n_states": 16, "rows": rows}


def test_a_block_that_is_not_monotone_in_predicate_count_says_so():
    """Synthetic, on purpose: the finding must be readable off the data, not
    off whatever this machine happened to do this afternoon."""
    verdict = axis_predicates.monotone_in_predicates([_block([
        {"encoding": "native", "n_predicates": 4, "ic3_seconds": 1.0},
        {"encoding": "dual+2", "n_predicates": 6, "ic3_seconds": 0.5},
        {"encoding": "onehot", "n_predicates": 16, "ic3_seconds": 0.2},
    ])])
    assert verdict["monotone_everywhere"] is False
    assert len(verdict["per_board"][0]["breaks"]) == 2
    assert "fewer predicates" in verdict["per_board"][0]["breaks"][0]


def test_a_block_that_is_monotone_says_that_too():
    verdict = axis_predicates.monotone_in_predicates([_block([
        {"encoding": "native", "n_predicates": 4, "ic3_seconds": 0.1},
        {"encoding": "onehot", "n_predicates": 16, "ic3_seconds": 0.9},
    ])])
    assert verdict["monotone_everywhere"] is True
    assert verdict["per_board"][0]["breaks"] == []


def test_a_block_with_nothing_to_compare_returns_none_rather_than_true():
    """One answered rung is not a monotone ladder, and `all([])` is True."""
    verdict = axis_predicates.monotone_in_predicates([_block([
        {"encoding": "native", "n_predicates": 4, "ic3_seconds": 0.1},
        {"encoding": "onehot", "n_predicates": 16, "ic3_seconds": None},
    ])])
    assert verdict["per_board"][0]["monotone"] is None
    assert verdict["monotone_everywhere"] is None


def test_a_block_groups_only_rungs_that_share_a_state_space():
    steps = []
    for board in (4, 6):
        for scheme, k in ((reencode.NATIVE, 0), (reencode.ONEHOT, 0)):
            spec = _spec(scheme, k, board)
            record = axis_predicates.measure_one(spec)
            record["derived"] = axis_predicates.derived(record, spec)
            steps.append(record)
    blocks = axis_predicates.held_fixed(steps)
    assert [b["board"] for b in blocks] == ["peg4", "peg6"]
    assert [b["n_states"] for b in blocks] == [16, 64]
    for block in blocks:
        assert {row["n_predicates"] for row in block["rows"]} == \
               {block["n_states"], len(str(bin(block["n_states"] - 1))) - 2}


def test_the_report_refuses_to_compare_across_blocks():
    """There is no cross-block ratio anywhere in the artefact, by design: two
    rungs of different boards differ in |S| as well as in vocabulary, and a
    number spanning them would attribute to neither."""
    payload = axis_predicates.report([], BUDGET, [], False)
    assert "held_fixed" in payload
    assert payload["what_is_comparable"].startswith("coverage and abstraction")


# ------------------------------------------------------------------- the anchor

def test_the_native_rungs_are_axis_as_rows(tmp_path):
    spec, record = _measure(reencode.NATIVE, 0, 4)
    theirs = harness.run_step(axis_size.spec_for(4), timeout_seconds=BUDGET)
    path = tmp_path / "axis_size.json"
    path.write_text(json.dumps({"steps": [theirs]}), encoding="utf-8")
    record["spec"] = spec.as_json()
    axis_predicates.check_anchors([record], str(path))    # raises on drift


def test_anchor_drift_raises_rather_than_warns(tmp_path):
    spec, record = _measure(reencode.NATIVE, 0, 4)
    record["spec"] = spec.as_json()
    theirs = harness.run_step(axis_size.spec_for(4), timeout_seconds=BUDGET)
    theirs["deterministic"]["cnf_text"] = "(pos0)"
    path = tmp_path / "axis_size.json"
    path.write_text(json.dumps({"steps": [theirs]}), encoding="utf-8")
    with pytest.raises(AnchorDrift, match="do not extend that ladder"):
        axis_predicates.check_anchors([record], str(path))


# --------------------------------------------------------------------- the gate

def test_a_recoding_that_is_not_the_world_escalates_instead_of_being_tabulated(
        monkeypatch):
    """An adapter fault must never be tabulated as a boundary: the number beside
    it would be worthless rather than the problem being hard."""
    spec = _spec(reencode.DUAL, 2)

    def broken(system, scheme, k=0):
        return reencode.Recoding(
            scheme=scheme, k=k, variables=("pos0",),
            native_variables=tuple(system.variables),
            definitions=(("var", 0, True),))

    monkeypatch.setattr(reencode, "recoding_for", broken)
    record = axis_predicates.measure_one(spec)
    assert record["deterministic"]["verdict"] == harness.ADAPTER_MISMATCH
    assert record["deterministic"]["escalate"] is True
    assert "not a renaming" in record["deterministic"]["detail"]
    assert axis_predicates.boundary_of([record]) is None
    assert axis_predicates.escalations([record])


def test_the_gate_runs_on_the_base_system_and_on_the_recoding():
    spec = _spec(reencode.DUAL, 2)
    system, recoding, recoded = axis_predicates.build_recoded(spec)
    assert axis_predicates._gate(spec, system, recoding, recoded) == []


# ---------------------------------------------------------------- the entry point

def test_all_three_axes_are_reachable_from_the_documented_entry_point():
    """Axes B and C existed for a while without being reachable from
    `python -m ic3bounds`, which made the documented command a third of the
    package.  This is the assertion that stops that happening again."""
    from ic3bounds import __main__ as entry
    assert set(entry.AXES) == {"size", "predicates", "compose"}
    for axis in entry.AXES:
        adapter = entry._ADAPTERS[axis]
        assert callable(adapter["run"]) and callable(adapter["markdown"])
        assert adapter["timeout"] > 0


def test_only_reads_as_board_sizes_on_two_axes_and_world_ids_on_the_third():
    from ic3bounds import __main__ as entry
    assert entry._parse_only("8,4", int) == [4, 8]
    assert entry._parse_only("t2-cycler-lock, t1-tokens-lock", str) == \
           ["t2-cycler-lock", "t1-tokens-lock"]
    assert entry._parse_only(None, int) is None


def test_the_markdown_computes_nothing_the_json_lacks():
    spec, record = _measure(reencode.DUAL, 2)
    record["spec"] = spec.as_json()
    payload = axis_predicates.report([record], BUDGET, [spec.label], True)
    table = axis_predicates.markdown(payload)
    assert "| peg4 | 16 | dual+2 | 6 |" in table
    assert str(record["deterministic"]["coverage"]) in table
