"""The protocol in `proxy/CONTRACT_CHANGES.md`, as far as a test can carry it.

A test cannot read PARTNER_SYNC and judge whether a paragraph was written, so
this does not verify that an announcement happened. What it does is remove the
only excuse INC-TA-006 actually had: the person who closed `model_call`'s field
set did not know they were making a breaking change, because nothing said so.

So there are two halves here. `test_the_contract_has_not_drifted_from_its_pin`
fires when the shared contract changes at all -- that is the moment someone is
standing in front of the question. `classify` decides which of the two answers
they get, and the rest of this file is that classifier tested against the
directions it is supposed to distinguish, because a classifier that called a
tightening additive would be worse than no classifier: it would issue a
clearance.
"""

import json

import pytest

from proxy import canon
from proxy.tools import contract


# -- the pin ---------------------------------------------------------------

def test_the_contract_has_not_drifted_from_its_pin():
    """The whole mechanism, in one assertion.

    If this fails you have changed what the proxies accept. Read the deltas:

      * every one says `additive` -- you widened the contract. Nothing
        downstream breaks. Re-pin with
        `python -m proxy.tools.contract --update`, and add a line to
        CONTRACT_CHANGES.md's ledger so the next person can see when it moved.
      * any one says `tightening` -- you narrowed it, and some track that
        imports `proxy/` as a library is about to have a run refused on a
        commit it never touched. That is INC-TA-006 and it cost $2.695 and a
        discarded reply. CONTRACT_CHANGES.md §3 is the procedure: announce it
        on PARTNER_SYNC, leave one cycle, ship a compatibility window.
    """
    rep = contract.report()
    assert rep["verdict"] == "UNCHANGED", "\n".join(
        ["the shared contract moved:"]
        + ["  %-10s %s" % (d["kind"], d["detail"]) for d in rep["deltas"]])


def test_the_pinned_file_is_what_the_writer_would_write(tmp_path):
    """Byte-stable, so a re-pin shows up as a content diff and not as
    whitespace. Determinism is a requirement here, not a nicety."""
    path = str(tmp_path / "canon_contract.json")
    contract.write_snapshot(path)
    first = open(path, "rb").read()
    contract.write_snapshot(path)
    assert open(path, "rb").read() == first
    assert b"\r\n" not in first
    with open(contract.SNAPSHOT_PATH, "rb") as fh:
        assert fh.read() == first


def test_the_fingerprint_is_what_an_importer_pins():
    """`--fingerprint` is the one line another track puts in its run manifest.
    W-1521's standing recommendation after INC-TA-006 was that something should
    diff the upstream pin between consecutive runs; this is the value to diff.
    """
    blob = json.load(open(contract.SNAPSHOT_PATH, encoding="utf-8"))
    assert blob["fingerprint"] == contract.fingerprint()
    assert blob["canon"] == contract.current()
    # The pin is a *superset* of the published `describe()`: it also watches the
    # three registries `ledger.py` owns, because `append` refuses an
    # unregistered arm or event outright and a detector blind to them would be
    # narrower than the rule CONTRACT_CHANGES.md §2 states.
    assert set(blob["canon"]) - set(canon.describe()) == {
        "events", "arms", "incident_kinds"}


def test_a_missing_snapshot_is_not_a_clean_bill_of_health(tmp_path):
    """"Nothing pinned" and "no deltas" must not produce the same answer. A
    safeguard that reports all clear when it is absent is worse than absent."""
    with pytest.raises(contract.NoSnapshot):
        contract.report(str(tmp_path / "not_here.json"))


# -- the classifier --------------------------------------------------------

def _mutate(**changes):
    """The live contract with one thing changed."""
    described = json.loads(json.dumps(canon.describe()))
    for path, value in changes.items():
        cursor = described
        parts = path.split(".")
        for part in parts[:-1]:
            cursor = cursor[part]
        cursor[parts[-1]] = value
    return described


def test_defining_a_new_field_is_additive():
    """The five P-8 fields, arriving the way they should have arrived."""
    before = _mutate(**{"shapes.model_call.fields": sorted(
        set(canon.MODEL_CALL_FIELDS) - {"beat", "label", "transport",
                                        "proxied", "proxy_gap"})})
    deltas = contract.classify(before, canon.describe())
    assert contract.verdict(deltas) == "ADDITIVE"
    assert {d["detail"] for d in deltas} >= {"model_call.beat defined"}


def test_undefining_a_field_is_a_tightening():
    """INC-TA-006 itself, run through the detector that did not exist then."""
    after = _mutate(**{"shapes.model_call.fields": sorted(
        set(canon.MODEL_CALL_FIELDS) - {"beat", "label", "transport",
                                        "proxied", "proxy_gap"})})
    deltas = contract.classify(canon.describe(), after)
    assert contract.verdict(deltas) == "TIGHTENING"
    assert any("model_call.beat undefined" in d["detail"] for d in deltas)


def test_required_and_fields_grow_in_opposite_directions():
    """The one distinction a naive set-diff gets wrong. Both are "a name was
    added to a list"; one frees writers and the other refuses them."""
    described = canon.describe()
    widened = _mutate(**{"shapes.env_step.fields":
                         sorted(set(canon.ENV_STEP_FIELDS) | {"turn_idx"})})
    narrowed = _mutate(**{"shapes.env_step.required":
                          sorted(set(canon.ENV_STEP_REQUIRED) | {"state"})})
    assert contract.verdict(contract.classify(described, widened)) == "ADDITIVE"
    assert contract.verdict(contract.classify(described, narrowed)) == "TIGHTENING"


def test_banning_a_spelling_is_a_tightening_and_unbanning_is_not():
    described = canon.describe()
    banned = json.loads(json.dumps(described))
    banned["banned_spellings"]["turn_idx"] = "step_idx"
    assert contract.verdict(contract.classify(described, banned)) == "TIGHTENING"
    assert contract.verdict(contract.classify(banned, described)) == "ADDITIVE"


def test_rewording_a_hint_is_neutral():
    """A refusal's message is not part of the contract. Treating prose edits as
    breaking changes is how a protocol gets routed around."""
    described = canon.describe()
    reworded = json.loads(json.dumps(described))
    reworded["banned_spellings"]["frame"] = "frames, and please read §3"
    assert contract.verdict(contract.classify(described, reworded)) == "NEUTRAL"


def test_growing_the_envelope_takes_a_field_away_from_callers():
    described = canon.describe()
    grown = _mutate(envelope=sorted(set(canon.ENVELOPE) | {"host"}))
    assert contract.verdict(contract.classify(described, grown)) == "TIGHTENING"


def test_a_new_required_key_on_an_auxiliary_is_a_tightening():
    described = canon.describe()
    stricter = json.loads(json.dumps(described))
    stricter["auxiliary_required"]["run_start"] = ["game_id", "budget"]
    assert contract.verdict(contract.classify(described, stricter)) == "TIGHTENING"

    looser = json.loads(json.dumps(described))
    looser["auxiliary_required"]["cache_event"] = ["kind"]
    assert contract.verdict(contract.classify(described, looser)) == "ADDITIVE"


def test_reclosing_the_two_shapes_is_a_tightening():
    """The specific regression this whole item exists to prevent: someone
    decides the two shapes should be closed again, and the detector says out
    loud what that means for every arm that already writes an extra field."""
    described = canon.describe()
    reclosed = _mutate(additive_safe=False)
    deltas = contract.classify(described, reclosed)
    assert contract.verdict(deltas) == "TIGHTENING"
    assert any("INC-TA-006" in d["detail"] for d in deltas)


def test_bumping_the_ledger_version_is_a_tightening():
    described = canon.describe()
    bumped = _mutate(ledger_version="2.0")
    deltas = contract.classify(described, bumped)
    assert contract.verdict(deltas) == "TIGHTENING"


@pytest.mark.parametrize("key", ["auxiliary_required", "closed_shapes", "shapes"])
def test_removing_a_published_key_is_a_tightening(key):
    """`describe()` is published for readers this package cannot enumerate, so
    dropping a key from it is a breaking change like any other.

    `closed_shapes` is in the list on purpose. C-003 schedules removing that
    alias on 2026-08-11, and an earlier draft of `classify()` exempted both
    shape spellings from the published-key diff -- so the one change the
    protocol had already put on a calendar was the one change the detector
    could not see. A detector with a hole shaped like the next scheduled change
    is worse than none: it issues a clearance."""
    described = contract.current()
    trimmed = json.loads(json.dumps(described))
    del trimmed[key]
    deltas = contract.classify(described, trimmed)
    assert contract.verdict(deltas) == "TIGHTENING"
    assert any(repr(key) in d["detail"] for d in deltas)


def test_the_registries_ledger_owns_are_watched_too():
    """`ledger.append` refuses an unregistered arm or event outright, so
    dropping one stops a writer that worked yesterday. CONTRACT_CHANGES.md §2
    lists them as tightenings; `canon.describe()` does not publish them, so the
    pin carries them separately rather than leaving the table unenforced."""
    described = contract.current()
    for name, value in (("arms", "theoria"), ("events", "model_call"),
                        ("incident_kinds", "score_mismatch")):
        shrunk = json.loads(json.dumps(described))
        shrunk[name] = [v for v in shrunk[name] if v != value]
        deltas = contract.classify(described, shrunk)
        assert contract.verdict(deltas) == "TIGHTENING", (name, deltas)
        grown = json.loads(json.dumps(described))
        grown[name] = sorted(list(described[name]) + ["something_new"])
        assert contract.verdict(contract.classify(described, grown)) == "ADDITIVE"


def test_an_unmodelled_change_is_a_tightening_not_a_clearance(tmp_path):
    """The classifier only sees deltas it was written to model. "Found no
    tightening" and "understood the change" are different statements, and only
    the second is a clearance -- so when the fingerprint moves in a way the
    classifier cannot account for, the verdict is TIGHTENING.

    Half-explained counts as unexplained: an additive delta must not clear the
    part nobody looked at."""
    path = str(tmp_path / "canon_contract.json")
    contract.write_snapshot(path)

    blob = json.load(open(path, encoding="utf-8"))
    # One thing the classifier models, and one thing it does not.
    blob["canon"]["shapes"]["env_step"]["fields"].remove("variant")
    blob["canon"]["shapes"]["env_step"]["types"] = {"score": "int"}
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(blob, fh, indent=2, sort_keys=True)

    rep = contract.report(path)
    assert rep["pinned_fingerprint"] != rep["live_fingerprint"]
    assert rep["verdict"] == "TIGHTENING"
    assert any("does not model" in d["detail"] for d in rep["deltas"])


def test_the_verdict_is_never_looser_than_the_fingerprint(tmp_path):
    """The bug this guards: `report()` computed both fingerprints, printed
    them, and never compared them -- so a contract that had visibly moved could
    still exit 0 and pass `verify_contract.sh`'s "still matches" step."""
    path = str(tmp_path / "canon_contract.json")
    contract.write_snapshot(path)
    blob = json.load(open(path, encoding="utf-8"))
    blob["canon"]["ledger_version"] = "0.9"
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(blob, fh, indent=2, sort_keys=True)

    rep = contract.report(path)
    assert rep["pinned_fingerprint"] != rep["live_fingerprint"]
    assert rep["verdict"] != "UNCHANGED"
    assert contract.main(["--snapshot", path]) != 0


def test_an_identical_contract_produces_no_deltas():
    """The classifier has to be able to say nothing happened, or every run of
    it is noise and the next person turns it off."""
    assert contract.classify(canon.describe(), canon.describe()) == []
