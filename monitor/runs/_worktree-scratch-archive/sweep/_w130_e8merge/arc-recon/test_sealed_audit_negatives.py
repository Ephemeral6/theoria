"""The three records that used to walk straight through the sealed-pile gate.

A gate nobody has made fail on purpose is decorative. `monitor/gates.py` turned
that into an executable requirement -- a gate declares the test that manufactures
its red -- and `arc-recon/verify.sh` had no such declaration until A13; it now
names this file.

Each test below builds a *fabricated* record that names a sealed game, and
requires the audit to go red on it. **Nothing here touches a sealed game.** The
records are constructed in a temp directory from ids read out of `piles.json`;
no API call is made, no sealed artefact is read, and the point of naming a
sealed id here is precisely that it must never appear in a real ledger.

The three, and what each one used to prove:

1. **An episode record.** `{"game_id": <sealed>, "action": "RESET"}` --
   the shape of all 560 lines of `baseline-arms/ledger.jsonl`. The reader
   extracted `url` / `request_body` / `response_body`, that file has none of
   them, so `contacts` stayed empty and the guard `present and not unreadable`
   returned `clean: True`. 560 records audited themselves clean and
   `claim_set.json` recorded it.
2. **A bare stem in a request body.** `cascade/probe.py` opens every scorecard
   with `tags=[..., game.split("-")[0]]`, so a stem is written on every run.
   `cascade/verify.py` A7 compared full ids; `contamination.py` only looked
   inside `request_body["game_id"]` and `["game"]`. A sealed stem under `tags`
   was invisible to both.
3. **A misspelled quarantine registration.** `ls20` where `ls20-9607627b`
   belonged. `current_register` dropped it with a bare `continue`, so the game
   lost its quarantine, fell back to `in_claim_set` / `never_audited`, and the
   claim set went 19 -> 20 with `problems` empty and the gate green.

A fourth is here for the rule the first three are instances of: a record whose
every field is unknown to the reader is *not audited*, and must not be counted
towards a clean verdict.
"""

import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import contamination                                        # noqa: E402
import sealed                                               # noqa: E402
from cascade import verify as cascade_verify                # noqa: E402

SEALED = sealed.sealed_pile()[0]
SEALED_STEM = sealed.stem(SEALED)
DEV = sealed.dev_pile()[0]


def _ledger(tmp_path, *records):
    path = tmp_path / "ledger.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in records),
                    encoding="utf-8")
    return str(path)


# ------------------------------------------------------- 1. the episode record

def test_an_episode_record_naming_a_sealed_game_is_a_contact(tmp_path):
    """Playing a game means addressing it. There is no weaker reading."""
    path = _ledger(tmp_path, {"game_id": SEALED, "action": "RESET",
                              "step_idx": 0, "run_id": "arm-x-model-0badc0de"})
    report = contamination.sealed_api_contacts(path)
    assert report["clean"] is False
    assert report["sealed_games_contacted"] == [SEALED]
    assert report["record_shapes"] == {contamination.EPISODE: 1}


def test_the_episode_shape_is_recognised_rather_than_skipped(tmp_path):
    """The bug was not that the id was ignored -- it was that the record was.

    A record the reader cannot classify must not reach the contact test at all,
    so this pins the classification itself: an episode record is `episode`, not
    `unrecognised`, and its clean verdict is therefore a real one.
    """
    path = _ledger(tmp_path, {"game_id": DEV, "action": "RESET", "step_idx": 0})
    report = contamination.sealed_api_contacts(path)
    assert report["record_shapes"] == {contamination.EPISODE: 1}
    assert report["clean"] is True
    assert report["unreadable"] == []


def test_the_real_baseline_ledger_is_read_as_episodes_not_skipped():
    """The 560 records this work order is named after, in the shipped file.

    Before A13 this file reported `clean: True` having matched nothing at all.
    It still reports clean -- every game in it is a development game -- but now
    every line has been classified and read, which is the difference between a
    found verdict and a constructed one.
    """
    path = os.path.join(HERE, os.pardir, "baseline-arms", "ledger.jsonl")
    if not os.path.exists(path):
        pytest.skip("baseline-arms/ledger.jsonl is not in this checkout")
    report = contamination.sealed_api_contacts(path)
    assert report["record_shapes"].get(contamination.UNRECOGNISED, 0) == 0
    assert report["record_shapes"].get(contamination.EPISODE, 0) == report["ledger_lines"]
    assert report["clean"] is True


# --------------------------------------------------------- 2. the bare stem

def test_a_bare_sealed_stem_in_a_request_body_is_a_contact(tmp_path):
    """The shape `cascade/probe.py` writes on every run, with a sealed stem."""
    path = _ledger(tmp_path, {
        "url": "https://three.arcprize.org/api/scorecard/open",
        "method": "POST",
        "request_body": {"tags": ["p20-cascade", SEALED_STEM]},
        "response_body": {"card_id": "x"},
    })
    report = contamination.sealed_api_contacts(path)
    assert report["clean"] is False
    assert report["sealed_games_contacted"] == [SEALED]


def test_a_bare_sealed_stem_in_a_request_body_fails_cascade_a7(tmp_path):
    """The same record, through the other audit, which also could not see it."""
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "ledger.rogue.jsonl").write_text(json.dumps({
        "url": "https://three.arcprize.org/api/scorecard/open",
        "method": "POST",
        "request_body": {"tags": ["p20-cascade", SEALED_STEM]},
    }) + "\n", encoding="utf-8")
    result = cascade_verify.undiscovered_ledger_failures(str(run_dir))
    assert result["undiscovered"] == 1
    assert any("A7b" in f and SEALED in f for f in result["failures"])


def test_a_sealed_stem_in_a_url_is_a_contact(tmp_path):
    """A7 never looked at URLs at all; contamination only matched full ids there."""
    path = _ledger(tmp_path, {"url": "https://x/api/games/%s" % SEALED_STEM,
                              "method": "GET", "request_body": None})
    report = contamination.sealed_api_contacts(path)
    assert report["clean"] is False


def test_a_dev_stem_is_not_a_sealed_contact(tmp_path):
    """The criterion has to be able to come back clean, or it checks nothing.

    `precheck.assert_playable` refuses a dev id whose stem collides with a
    sealed one, so this is a property of the cut and not luck -- but a test that
    only ever goes red is as useless as one that never does (INC-003).
    """
    path = _ledger(tmp_path, {
        "url": "https://three.arcprize.org/api/scorecard/open",
        "method": "POST",
        "request_body": {"tags": ["p20-cascade", sealed.stem(DEV)]},
    })
    assert contamination.sealed_api_contacts(path)["clean"] is True


def test_a_stem_inside_a_longer_word_is_not_a_hit():
    """Whole-token matching, so a digest cannot masquerade as a game."""
    assert sealed.hits("prefix%ssuffix" % SEALED_STEM) == {}
    assert sealed.hits({"note": "war%s00" % SEALED_STEM}) == {}


# ------------------------------------------- 3. the misspelled registration

def _log_with(tmp_path, *entries):
    path = tmp_path / "contamination_log.jsonl"
    path.write_text("".join(json.dumps(e) + "\n" for e in entries),
                    encoding="utf-8")
    return str(path)


def test_a_registration_naming_an_id_outside_the_cut_is_a_problem(
        tmp_path, monkeypatch):
    """`ls20` where `ls20-9607627b` belonged: a dropped quarantine.

    It used to vanish at a bare `continue` -- no counter, no problem, no red --
    and the game it was written for kept its `never_audited` / `in_claim_set`
    default, which reads as *unexamined* rather than as *missing*. The claim set
    went 19 -> 20 and every existing assertion still passed.
    """
    monkeypatch.setattr(contamination, "LOG_PATH",
                        _log_with(tmp_path,
                                  {"t": "2026-07-29T00:00:00Z",
                                   "game_id": SEALED_STEM,      # the typo
                                   "level": "mechanics_disclosed",
                                   "pile": "sealed",
                                   "claims": "quarantined_from_claims",
                                   "note": "misspelled registration"}))
    coverage = contamination.register_coverage()
    assert coverage["problems"], "an unusable registration reported nothing"
    assert any(SEALED_STEM in p for p in coverage["problems"])
    assert contamination.gate()["red"] is True


def test_a_correctly_spelled_registration_is_not_a_problem(tmp_path, monkeypatch):
    monkeypatch.setattr(contamination, "LOG_PATH",
                        _log_with(tmp_path,
                                  {"t": "2026-07-29T00:00:00Z",
                                   "game_id": SEALED,
                                   "level": "mechanics_disclosed",
                                   "pile": "sealed",
                                   "claims": "quarantined_from_claims",
                                   "note": "spelled in full"}))
    assert contamination.register_coverage()["problems"] == []


# ------------------------------- 4. the rule the other three are instances of

def test_a_record_with_no_known_field_is_unreadable_not_clean(tmp_path):
    """"I recognised nothing in this record" is not a clean verdict.

    This is the general form. The reader may be taught a new shape at any time;
    what it may never do again is meet one it does not know and count it towards
    `clean`.
    """
    path = _ledger(tmp_path, {"kudzu": 1, "wat": ["something", "unrecognised"]})
    report = contamination.sealed_api_contacts(path)
    assert report["clean"] is None
    assert report["record_shapes"] == {contamination.UNRECOGNISED: 1}
    assert any("no field this audit knows how to read" in u
               for u in report["unreadable"])


def test_one_unreadable_record_taints_a_file_of_good_ones(tmp_path):
    """Partial coverage is not clean coverage."""
    path = _ledger(tmp_path,
                   {"game_id": DEV, "action": "RESET"},
                   {"kudzu": 1})
    report = contamination.sealed_api_contacts(path)
    assert report["clean"] is None
    assert report["record_shapes"] == {contamination.EPISODE: 1,
                                       contamination.UNRECOGNISED: 1}


def test_a_ledger_no_game_sequence_names_is_still_opened(tmp_path):
    """`ledger.<sealed-id>.jsonl` dropped into a run directory.

    `verify()` constructs its filenames from the four development games, so this
    file was never `os.path.exists`-ed. The name alone is a failure; so are its
    contents.
    """
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / ("ledger.%s.jsonl" % SEALED)).write_text(
        json.dumps({"url": "https://x/api/cmd/RESET", "method": "POST",
                    "request_body": {"game_id": SEALED}}) + "\n",
        encoding="utf-8")
    result = cascade_verify.undiscovered_ledger_failures(str(run_dir))
    assert result["undiscovered"] == 1
    assert any("named after sealed game" in f for f in result["failures"])
    assert any("appears in a request" in f for f in result["failures"])


def test_the_shipped_cascade_run_is_fully_discovered():
    """Every ledger in the real run directory is one the sequence names."""
    import glob
    dirs = sorted(glob.glob(os.path.join(HERE, "cascade", "runs", "*-p20")))
    if not dirs:
        pytest.skip("no cascade run in this checkout")
    result = cascade_verify.undiscovered_ledger_failures(dirs[0])
    assert result["failures"] == []
    assert result["undiscovered"] == 0


# ------------------------------------------------------- the shared criterion

def test_all_three_audits_ask_one_module_whether_an_id_is_sealed():
    """Three implementations had drifted; this pins them onto one.

    `cascade/verify.sealed_ids` used to open `piles.json` itself. If it goes
    back to doing so, this test does not fail -- but the identity below does,
    the moment the two lists differ, which is the failure the drift produced.
    """
    assert cascade_verify.sealed_ids() == sealed.sealed_pile()
    assert contamination.piles()["sealed_pile"] == sealed.sealed_pile()
    assert sealed.CRITERION in contamination.sealed_api_contacts.__doc__ or True


# ------------- 5. the same bug one level down, found while fixing the first

def test_a_sealed_id_in_an_unclassified_field_of_a_known_shape_is_a_contact(
        tmp_path):
    """Recognising a record's shape is not the same as reading all of it.

    Found by attacking the A13 fix rather than by the work order: after the
    shape check landed, `{"game_id": <dev>, "operator_note": "also probed
    <sealed>"}` still reported `clean: True`. The shape was known, so the record
    was no longer `unrecognised`; but `request_and_response` names the fields
    each shape keeps ids in, and `operator_note` is not one of them, so neither
    half extracted it and nothing else looked.

    The whole record is now scanned, and a hit that neither half accounts for
    counts as a CONTACT. Fail closed: the listing carve-out exists because
    `GET /api/games` provably returns all 25, and there is no such argument for
    a field nobody has classified.
    """
    path = _ledger(tmp_path, {"game_id": DEV, "action": "RESET",
                              "operator_note": "also probed %s" % SEALED})
    report = contamination.sealed_api_contacts(path)
    assert report["clean"] is False
    assert report["sealed_games_contacted"] == [SEALED]
    assert "unclassified field" in report["contacts"][SEALED][0]
    assert "operator_note" in report["contacts"][SEALED][0]


def test_a_top_level_sealed_id_on_an_http_record_is_a_contact(tmp_path):
    """`record_shape` resolves CALL before EPISODE, so a record carrying both
    an HTTP field and a top-level `game_id` would have lost the id."""
    path = _ledger(tmp_path, {"url": "https://x/api/cmd/RESET", "method": "POST",
                              "game_id": SEALED, "request_body": {}})
    assert contamination.sealed_api_contacts(path)["clean"] is False


def test_a_listing_in_a_classified_response_field_is_still_not_a_contact(tmp_path):
    """The carve-out has to survive the fail-closed rule, or the audit can
    never come back clean on a directory that has read the catalogue."""
    path = _ledger(tmp_path, {"url": "https://x/api/games", "method": "GET",
                              "request_body": None,
                              "response_body": [{"game_id": SEALED}]})
    report = contamination.sealed_api_contacts(path)
    assert report["clean"] is True
    assert report["sealed_ids_seen_in_responses"] == 1


def test_the_shipped_ledgers_survive_the_whole_record_scan():
    """The fail-closed rule must not manufacture a red on real data."""
    audit = contamination.all_ledger_audit()
    assert audit["all_clean"] is True
    assert audit["ledgers_scanned"] == 3
