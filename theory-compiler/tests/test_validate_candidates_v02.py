"""The v0.2 candidate validator, and the claim that v0.2 is additive.

The headline test is `TestAdditive`: for every row and every file in a corpus,
anything the **v0.1** validator accepts, the v0.2 validator must accept too.
That is the whole of "只做加法" as an executable statement, and it is here
because the first draft of `tools/validate_candidates_v02.py` failed it three
ways — it dropped v0.1's zero-denominator rule, dropped v0.1's blank-line rule,
and invented an id-uniqueness rule v0.1 never had. An independent review found
all three by reading; this file is what would have found them by running.

v0.1's validator lives in `engine-rig/`, another track's tree. It is loaded
here **by path, as a data-ish artefact**, only so the two can be compared — the
v0.2 implementation itself imports nothing from it. If it is missing, the
differential tests skip and the rest still run.
"""

import importlib.util
import json
import uuid
from pathlib import Path

import pytest

from tools import validate_candidates_v02 as v2

REPO = Path(__file__).resolve().parents[2]
V01_PATH = REPO / "engine-rig" / "tools" / "validate_candidates.py"
REAL_STREAMS = [
    REPO / "engine-rig" / "artifacts" / "candidates.jsonl",
    REPO / "cold-start-a0" / "artifacts" / "candidates.jsonl",
    REPO / "cold-start-a0" / "artifacts" / "candidates_no_button.jsonl",
]


def _load_v01():
    if not V01_PATH.exists():
        return None
    spec = importlib.util.spec_from_file_location("_v01_validator", V01_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


V01 = _load_v01()
needs_v01 = pytest.mark.skipif(V01 is None, reason="engine-rig's v0.1 validator is absent")


def row(**overrides):
    base = {
        "id": str(uuid.uuid5(uuid.NAMESPACE_URL, "fixture")),
        "engine": "cegis_miner",
        "kind": "rule_hypothesis",
        "payload": {"name": "blocked_DOWN"},
        "evidence": {"transitions": [0, 1], "coverage": "2/2"},
        "status": "candidate",
        "timestamp": "2026-07-28T00:00:00Z",
    }
    base.update(overrides)
    return base


# ------------------------------------------------------------ the v0.1 rules

class TestInheritedFromV01:
    def test_a_plain_row_passes(self):
        assert v2.validate_row(row()) == []

    @pytest.mark.parametrize("key", sorted(v2.REQUIRED_KEYS))
    def test_every_required_key_is_required(self, key):
        broken = row()
        del broken[key]
        assert any("missing key %r" % key in e for e in v2.validate_row(broken))

    def test_an_unknown_top_level_key_is_rejected(self):
        assert any("unexpected key 'producer'" in e
                   for e in v2.validate_row(row(producer="deadlock_carver")))

    def test_status_may_not_be_adjudicated(self):
        for bad in ("accepted", "rejected", "proven", ""):
            assert any("status" in e for e in v2.validate_row(row(status=bad)))

    def test_id_must_be_a_uuid(self):
        assert any("uuid" in e for e in v2.validate_row(row(id="row-1")))

    def test_timestamp_must_be_iso8601(self):
        assert any("ISO8601" in e for e in v2.validate_row(row(timestamp="July 28")))

    def test_payload_must_be_an_object(self):
        assert any("payload" in e for e in v2.validate_row(row(payload=[1, 2])))

    @pytest.mark.parametrize("coverage", ["", "3", "3/", "k/n", "3//4", "3 / 4"])
    def test_coverage_must_be_k_over_n(self, coverage):
        ev = {"transitions": [], "coverage": coverage}
        assert any("coverage" in e for e in v2.validate_row(row(evidence=ev)))

    def test_a_zero_denominator_is_still_rejected(self):
        """v0.1's rule. A consumer computing k/n on this row raises."""
        for coverage in ("0/0", "5/0"):
            ev = {"transitions": [], "coverage": coverage}
            assert any("denominator is zero" in e
                       for e in v2.validate_row(row(evidence=ev))), coverage

    def test_numerator_above_denominator_is_rejected(self):
        ev = {"transitions": [], "coverage": "9/4"}
        assert any("denominator" in e for e in v2.validate_row(row(evidence=ev)))

    def test_transitions_must_be_ints(self):
        ev = {"transitions": [0, "1"], "coverage": "1/2"}
        assert any("transitions" in e for e in v2.validate_row(row(evidence=ev)))

    def test_booleans_are_not_ints_here(self):
        ev = {"transitions": [True], "coverage": "1/2"}
        assert any("transitions" in e for e in v2.validate_row(row(evidence=ev)))

    def test_a_blank_line_is_a_malformed_stream(self):
        errors = v2.validate_stream([json.dumps(row()), "", json.dumps(row())])
        assert any("blank line" in e for e in errors)

    def test_bad_json_is_reported_per_line_and_does_not_abort(self):
        errors = v2.validate_stream(["{not json", json.dumps(row())])
        assert len(errors) == 1 and "not valid JSON" in errors[0]


# ------------------------------------------------------------- what v0.2 adds

class TestAdditions:
    @pytest.mark.parametrize("engine", sorted(v2.ENGINES_ADDED))
    def test_the_two_new_engines_are_accepted(self, engine):
        assert v2.validate_row(row(engine=engine)) == []

    @pytest.mark.parametrize("kind", sorted(v2.KINDS_ADDED))
    def test_the_two_new_kinds_are_accepted(self, kind):
        assert v2.validate_row(row(kind=kind)) == []

    def test_the_enum_is_still_an_enum(self):
        assert any("engine not in the v0.2 enum" in e
                   for e in v2.validate_row(row(engine="ic3-pdr")))
        assert any("kind not in the v0.2 enum" in e
                   for e in v2.validate_row(row(kind="deadlock-theorem")))

    def test_basis_names_the_units_of_each_field(self):
        ev = {"transitions": [0], "coverage": "1/2",
              "basis": {"transitions": "plan_steps", "coverage": "generated_nodes"}}
        assert v2.validate_row(row(evidence=ev)) == []

    def test_either_basis_key_may_stand_alone(self):
        ev = {"transitions": [0], "coverage": "1/2", "basis": {"coverage": "states"}}
        assert v2.validate_row(row(evidence=ev)) == []

    def test_an_unknown_basis_value_is_rejected(self):
        ev = {"transitions": [0], "coverage": "1/2", "basis": {"coverage": "nodes"}}
        assert any("evidence.basis.coverage" in e for e in v2.validate_row(row(evidence=ev)))

    def test_a_scalar_basis_is_rejected(self):
        """One word cannot cover a row whose two fields count different things."""
        ev = {"transitions": [0], "coverage": "1/2", "basis": "states"}
        assert any("evidence.basis is not a JSON object" in e
                   for e in v2.validate_row(row(evidence=ev)))

    def test_an_unknown_basis_key_is_rejected(self):
        ev = {"transitions": [0], "coverage": "1/2", "basis": {"payload": "states"}}
        assert any("in evidence.basis" in e for e in v2.validate_row(row(evidence=ev)))

    def test_basis_is_optional_and_has_no_default(self):
        """Absent means "see this engine's README", which is the v0.1 situation."""
        assert v2.validate_row(row()) == []
        assert any("--strict-basis" in e
                   for e in v2.validate_row(row(), strict_basis=True))

    def test_derived_from_takes_ids(self):
        ids = [str(uuid.uuid4()) for _ in range(3)]
        assert v2.validate_row(row(derived_from=ids)) == []
        assert v2.validate_row(row(derived_from=[])) == []

    def test_derived_from_may_not_name_the_row_itself(self):
        r = row()
        r["derived_from"] = [r["id"]]
        assert any("own id" in e for e in v2.validate_row(r))

    def test_derived_from_may_point_outside_this_file(self):
        """Streams get split and merged; a dangling reference is not a defect."""
        assert v2.validate_stream([json.dumps(row(derived_from=[str(uuid.uuid4())]))]) == []

    def test_derived_from_must_be_a_list_of_uuids(self):
        assert any("derived_from is not a list" in e
                   for e in v2.validate_row(row(derived_from="abc")))
        assert any("non-uuid" in e for e in v2.validate_row(row(derived_from=["abc"])))

    def test_contract_may_be_named_and_must_be_known(self):
        assert v2.validate_row(row(contract="candidates_schema@0.2")) == []
        assert any("contract" in e for e in v2.validate_row(row(contract="v2")))


# -------------------------------------------------- append-only, and what it is

class TestAppendOnly:
    def test_a_repeated_id_is_legal(self):
        """Two byte-identical proposals, not a rewrite.

        `engine-rig` addresses candidates by content (`uuid5` over the row), so
        running a producer twice into one file repeats ids by construction —
        and `engine-rig/tests/test_integration.py::
        test_a_second_full_run_only_adds_lines` asserts exactly that stream is
        valid. A uniqueness rule here would fail a passing, contract-legal test
        while forbidding nothing append-only forbids: appending modifies no
        written line.
        """
        line = json.dumps(row())
        assert v2.validate_stream([line, line]) == []


# ------------------------------------------------- the additivity claim itself

@needs_v01
class TestAdditive:
    """Anything v0.1 accepts, v0.2 accepts. Checked, not asserted."""

    CORPUS = [
        row(),
        row(engine="fd_adapter", kind="plan"),
        row(engine="probe_frontier", kind="probe_design"),
        row(evidence={"transitions": [], "coverage": "0/1"}),
        row(evidence={"transitions": list(range(50)), "coverage": "50/50"}),
        row(payload={}),
        row(timestamp="2026-07-28T00:00:00+00:00"),
        row(status="candidate"),
        # Ones v0.1 rejects; v0.2 must not accept them either.
        row(status="accepted"),
        row(id="not-a-uuid"),
        row(evidence={"transitions": [], "coverage": "1/0"}),
        row(evidence={"transitions": [], "coverage": "9/4"}),
        row(engine="unknown_engine"),
        row(kind="unknown_kind"),
        row(producer="x"),
    ]

    @pytest.mark.parametrize("candidate", CORPUS,
                             ids=range(len(CORPUS)))
    def test_v01_acceptance_implies_v02_acceptance(self, candidate):
        if V01.validate_row(candidate) == []:
            assert v2.validate_row(candidate) == [], (
                "v0.1 accepts this row and v0.2 does not, so the revision is "
                "not additive: %r" % (candidate,))

    def test_v02_rejects_everything_v01_rejects_except_the_new_enum_values(self):
        """The one direction that may differ, and only in the declared way."""
        for candidate in self.CORPUS:
            if V01.validate_row(candidate) and not v2.validate_row(candidate):
                assert (candidate.get("engine") in v2.ENGINES_ADDED
                        or candidate.get("kind") in v2.KINDS_ADDED
                        or set(candidate) & v2.OPTIONAL_KEYS), (
                    "v0.2 accepts a row v0.1 rejects, for a reason this "
                    "revision never claimed: %r" % (candidate,))

    @pytest.mark.parametrize("path", REAL_STREAMS, ids=lambda p: p.name)
    def test_the_real_streams_pass_both(self, path):
        if not path.exists():
            pytest.skip("%s not generated" % path)
        assert V01.validate_file(str(path)) == []
        assert v2.validate_file(str(path)) == []

    def test_a_doubled_stream_passes_both(self, tmp_path):
        """The shape `test_a_second_full_run_only_adds_lines` produces."""
        source = REAL_STREAMS[0]
        if not source.exists():
            pytest.skip("no stream to double")
        text = source.read_text(encoding="utf-8")
        doubled = tmp_path / "doubled.jsonl"
        doubled.write_text(text + text, encoding="utf-8", newline="\n")
        assert V01.validate_file(str(doubled)) == []
        assert v2.validate_file(str(doubled)) == []


# --------------------------------------------------------------- the front door

class TestCommandLine:
    def test_no_arguments_prints_a_usage_line(self, capsys):
        assert v2.main([]) == 2
        assert "usage:" in capsys.readouterr().err

    def test_a_mistyped_flag_is_refused_rather_than_ignored(self, capsys, tmp_path):
        """Silently dropping `--stict-basis` would report OK in the lax mode
        the caller did not ask for, and a lax OK reads like a strict one."""
        path = tmp_path / "s.jsonl"
        path.write_text(json.dumps(row()) + "\n", encoding="utf-8", newline="\n")
        assert v2.main(["--stict-basis", str(path)]) == 2
        assert "unknown option" in capsys.readouterr().err

    def test_a_good_file_exits_zero(self, capsys, tmp_path):
        path = tmp_path / "s.jsonl"
        path.write_text(json.dumps(row()) + "\n", encoding="utf-8", newline="\n")
        assert v2.main([str(path)]) == 0
        assert "OK (candidates_schema@0.2, 1 row(s))" in capsys.readouterr().out

    def test_a_bad_file_exits_one(self, capsys, tmp_path):
        path = tmp_path / "s.jsonl"
        path.write_text(json.dumps(row(status="accepted")) + "\n",
                        encoding="utf-8", newline="\n")
        assert v2.main([str(path)]) == 1
        assert "FAIL" in capsys.readouterr().out
