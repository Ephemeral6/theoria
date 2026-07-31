"""Negative controls for the enumerator's defaults: nothing falls through to
"publishable".

`R3-release-classifier-defaults`. The finding behind these tests is one sentence:
**in `enumerate.py`, every default pointed at class A.** Unreadable, unrecognised
and uncomputable all landed on `releasable`, and `release/MANIFEST.jsonl` is the
document a release is assembled from. A permissive default in a classifier whose
output is "what we publish" is not a rough edge; it is the failure mode.

`test_unreadable_is_not_clean.py` closed the *unreadable* half of that -- a file
`open()` refuses now lands as class `?`. These close the other two:

* **unrecognised** -- the id list the classifier compares against did not load,
  so no file names an ARC game, so every file is class A on the evidence "no ARC
  game id appears in this file". A positive claim about a comparison that never
  happened.
* **uncomputable** -- the file was judged by the characters after the last dot in
  its name. The class C branch it fell into does not decline to rule; it asserts
  that the ids in the file are "constants, guards or narrative" carrying "no
  environment payload", about bytes no parser had opened.

Each test below has a negative control **and** a positive control, in the style
of its sibling: a gate that has never been seen to go red is not evidence that
anything is green, and a gate that reddens at everything proves nothing either.

## Why these build a real git repository

`enumerate.build` enumerates `git ls-files`, and `_arc_game_ids` reads the cut
from `arc-recon/data/piles.json` in that same tree. A test handing it a list of
paths would exercise everything except the two interfaces that failed. So each
test `git init`s under pytest's `tmp_path`, plants files, and points `REPO_ROOT`
at that tree -- and the broken cut file is planted *there*, never in this
repository, whose own `piles.json` carries the binding cut.
"""

import json
import os
import shutil
import subprocess
import sys

import pytest

import check_redlines as redlines
import enumerate as enum

HERE = os.path.dirname(os.path.abspath(__file__))
REAL_ROOT = os.path.dirname(os.path.dirname(HERE))
REAL_PILES = os.path.join(REAL_ROOT, "arc-recon", "data", "piles.json")

CUT_REL = "arc-recon/data/piles.json"


def _dev_id() -> str:
    """One DEVELOPMENT-pile id, read from the cut rather than hardcoded.

    The dev pile on purpose. These fixtures pair a game id with a frame, which is
    the exact shape the sealed check calls an incident -- so building them out of
    a sealed id would plant material this repository must not hold, in a test
    whose subject is a different rule entirely. The dev pile has been played and
    its ids appear in tracked ledgers already.
    """
    with open(REAL_PILES, encoding="utf-8") as fh:
        piles = json.load(fh)
    dev = piles.get("dev", piles.get("dev_pile", []))
    ids = sorted(g if isinstance(g, str) else g.get("game_id", "") for g in dev)
    ids = [g for g in ids if g]
    assert ids, "the cut file yielded no development ids; this fixture cannot be built"
    return ids[0]


def _git(repo: str, *args: str) -> None:
    subprocess.run(["git", "-C", repo, *args], check=True, capture_output=True, text=True)


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """A throwaway git repository the enumerator will treat as the tree."""
    root = tmp_path / "tree"
    (root / "arc-recon" / "data").mkdir(parents=True)
    shutil.copyfile(REAL_PILES, root / "arc-recon" / "data" / "piles.json")
    (root / "README.md").write_text("a file with nothing interesting in it\n",
                                    encoding="utf-8")
    _git(str(root), "init", "-q")
    _git(str(root), "add", "-A")

    monkeypatch.setattr(redlines, "REPO_ROOT", str(root))
    monkeypatch.setattr(enum, "REPO_ROOT", str(root))
    return root


def _add(repo_root, rel: str, data) -> None:
    path = repo_root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, bytes):
        path.write_bytes(data)
    else:
        path.write_text(data, encoding="utf-8")
    _git(str(repo_root), "add", "--", rel)


def _rewrite_cut(repo_root, mutate) -> None:
    """Plant a differently-shaped `piles.json` in the throwaway tree."""
    path = repo_root / "arc-recon" / "data" / "piles.json"
    with open(path, encoding="utf-8") as fh:
        piles = json.load(fh)
    mutate(piles)
    path.write_text(json.dumps(piles), encoding="utf-8")
    _git(str(repo_root), "add", "--", CUT_REL)


def _trace(dev_id: str) -> str:
    """Two records pairing a dev-pile game id with a frame: class B by the rule."""
    return (json.dumps({"game_id": dev_id, "frame": [[1, 2], [3, 4]]}) + "\n"
            + json.dumps({"game_id": dev_id, "frame": [[5, 6], [7, 8]]}) + "\n")


# ---------------------------------------------------- defect 1: the id list
# `_arc_game_ids` read the cut through `.get("strata", {})`. A missing or renamed
# key is swallowed into an empty dict; a comprehension over an empty dict is a
# perfectly legal empty list; and from there `classify` finds no id in any file
# and returns class A / releasable for every one of them, with the evidence "no
# ARC game id appears in this file".
#
# `check_redlines.check_sealed` already carries this guard, and the comment beside
# it records what the version without it did: it "scanned 2817 files with an empty
# id list and then printed `Both red lines clear`". The guard went into one of the
# two id readers and not the other.


def test_the_real_cut_still_loads(repo):
    """The positive control. Every refusal below is worthless if the reader
    cannot read the cut it is actually shipped with."""
    ids = enum._arc_game_ids()
    with open(REAL_PILES, encoding="utf-8") as fh:
        piles = json.load(fh)
    assert len(ids) == len(piles["dev_pile"]) + len(piles["sealed_pile"]) == 25
    assert _dev_id() in ids


def test_a_cut_with_no_strata_stops_the_classifier_instead_of_passing_everything(repo):
    """THE defect. `enumerate.py:123`, `.get("strata", {})`.

    Measured on this repository at base 7852ef3 with the id list empty: **37
    files moved B -> A and 247 moved C -> A** -- 284 files into the class that
    ships, each carrying a sentence asserting that no ARC game id appears in it.
    Nothing crashed, nothing warned, and the manifest was one `git mv` away from
    being generated that way.

    The assertion is that it *raises*. A warning would be read by the same reader
    who reads the manifest afterwards, which is to say not at all.
    """
    _add(repo, "arm/ledger.jsonl", _trace(_dev_id()))
    _rewrite_cut(repo, lambda p: p.pop("strata"))

    with pytest.raises(enum.PileCutUnreadable):
        enum._arc_game_ids()
    with pytest.raises(enum.PileCutUnreadable):
        enum.build(enum._tracked())


def test_a_cut_whose_strata_lost_a_game_is_a_refusal_not_a_short_list(repo):
    """The subtler half, and the one an empty-check misses.

    `check_sealed`'s guard above it catches only an *empty* pile; the count
    comparison beside it exists because a cut file that changed shape while
    staying non-empty sails through an emptiness test. Here the strata are
    present and populated and one game has dropped out of them -- so the id list
    loads, looks healthy, and is silently one game short. Every file naming only
    that game would classify A.
    """
    def drop_one(piles):
        for family, ids in piles["strata"].items():
            if len(ids) > 1:
                piles["strata"][family] = ids[1:]
                return
        raise AssertionError("no stratum with more than one id; fixture needs revisiting")

    _rewrite_cut(repo, drop_one)

    with pytest.raises(enum.PileCutUnreadable) as caught:
        enum._arc_game_ids()
    assert "24" in str(caught.value) and "25" in str(caught.value), str(caught.value)


def test_a_cut_that_renamed_a_game_is_caught_even_though_the_count_holds(repo):
    """Counts are the weaker test of the two the guard makes. A renamed id keeps
    `len(ids)` exactly right and changes every answer that depends on it."""
    def rename_one(piles):
        family = next(f for f, ids in piles["strata"].items() if ids)
        piles["strata"][family] = ["zz99-deadbeef"] + piles["strata"][family][1:]

    _rewrite_cut(repo, rename_one)

    with pytest.raises(enum.PileCutUnreadable) as caught:
        enum._arc_game_ids()
    assert "zz99-deadbeef" in str(caught.value)


def test_an_empty_pile_is_a_refusal_and_names_which_half_was_empty(repo):
    """The emptiness case reported separately from the shape case, because the
    two send a reader to different places in the cut file."""
    _rewrite_cut(repo, lambda p: p.update({"dev_pile": [], "strata": {}}))

    with pytest.raises(enum.PileCutUnreadable) as caught:
        enum._arc_game_ids()
    assert "0 development" in str(caught.value), str(caught.value)


# ------------------------------------------------- defect 3: the suffix test
# `enumerate.py:160` and `:146` classified by filename suffix while
# `check_redlines` had grown `json_shaped`, whose docstring says the judgement
# lives in one place and "both files call it". This file was the one that did
# not. So identical bytes were class B named `.jsonl` and class C named `.log`,
# and the class C branch asserts positively that they "carry no environment
# payload".


def test_the_same_bytes_are_not_class_b_under_one_name_and_class_c_under_another(repo):
    """THE defect. Byte-identical files, two names, and before this change two
    licence classes -- one of which ships.

    Class C is not an abstention. Its evidence reads "ids used as constants,
    guards or narrative carry no environment payload", which is a positive
    finding about a file whose bytes nothing had parsed. Here they are frames.
    """
    body = _trace(_dev_id())
    _add(repo, "arm/trace.jsonl", body)
    _add(repo, "arm/trace.log", body)

    rows = {r["path"]: r for r in enum.build(enum._tracked())}

    assert rows["arm/trace.jsonl"]["class"] == "B", rows["arm/trace.jsonl"]
    assert rows["arm/trace.log"]["class"] == "B", rows["arm/trace.log"]
    assert rows["arm/trace.log"]["class"] == rows["arm/trace.jsonl"]["class"], (
        "the licence class still depends on the characters after the last dot"
    )
    assert "no environment payload" not in rows["arm/trace.log"]["evidence"], (
        "the manifest still asserts innocence about a file it did not parse"
    )


def test_an_api_transaction_log_is_found_under_any_name(repo):
    """`enumerate.py:146`, the same suffix gate one branch earlier.

    The transaction-marker rule is the one that does not depend on which games a
    file names -- a log of requests is a compilation of retrieved data either
    way. Behind a suffix test it was unreachable for a probe log named `.log`,
    and such a file names no game id at all, so it fell straight through to
    **class A / releasable**: the most permissive verdict in the table, for the
    most obviously API-derived artefact in the repository.
    """
    body = (json.dumps({"kind": "arc_api_call", "status": 200}) + "\n"
            + json.dumps({"kind": "arc_api_call", "status": 429}) + "\n")
    _add(repo, "arc-recon/probe_log.log", body)

    rows = {r["path"]: r for r in enum.build(enum._tracked())}
    assert rows["arc-recon/probe_log.log"]["class"] == "B", rows["arc-recon/probe_log.log"]


def test_an_unparseable_stream_under_a_prose_name_is_undetermined_not_class_c(repo):
    """The honest cost of the fix, pinned so nobody quietly reverses it.

    A file that reads like a record stream and will not parse as one is `?` /
    `needs_human`, and `enumerate.main` exits non-zero on it. That reddens the
    gate. It is the correct answer: the alternative on offer is the old one,
    which asserted "no environment payload" about the same bytes.
    """
    _add(repo, "arm/session.log",
         json.dumps({"game_id": _dev_id(), "frame": [[1]]}) + "\n"
         + json.dumps({"game_id": _dev_id(), "frame": [[2]]}) + "\n"
         + '{"game_id": "' + _dev_id() + '", "frame": [[3]],,,}\n')

    rows = {r["path"]: r for r in enum.build(enum._tracked())}
    row = rows["arm/session.log"]
    assert row["class"] == "?", row
    assert row["verdict"] == "needs_human"


def test_prose_naming_a_game_is_still_class_c(repo):
    """The positive control, and the one that keeps the fix from being a blunt
    instrument. `json_shaped` exists in both directions: a Markdown file opening
    with a link reference must not be handed to the JSON reader and reported
    unreadable. A gate that reddens on ordinary documents gets switched off."""
    _add(repo, "NOTES.md",
         f"[spec]: ./spec.md\n\nThe development pile includes {_dev_id()}, named\n"
         "here as narrative rather than as payload.\n")

    rows = {r["path"]: r for r in enum.build(enum._tracked())}
    assert rows["NOTES.md"]["class"] == "C", rows["NOTES.md"]


def test_source_code_holding_a_few_json_lines_is_still_class_c(repo):
    """The counterweight `check_redlines` already pays for: Python source with a
    handful of one-line fixture dicts is not a record stream. Sharing
    `json_shaped` means sharing this behaviour too, which is the point --
    whichever way the rule moves next, it moves once."""
    _add(repo, "guard.py",
         '"""A guard test."""\n'
         "import json\n\n"
         "DEV = %r\n\n" % _dev_id()
         + "FIXTURE = 1\n"
         '{"game_id": "aa00-0000", "frame": [[1]]}\n'
         '{"game_id": "aa00-0000", "frame": [[2]]}\n'
         "def test_it():\n"
         "    assert DEV in json.dumps(DEV)\n"
         "    return None\n")

    rows = {r["path"]: r for r in enum.build(enum._tracked())}
    assert rows["guard.py"]["class"] == "C", rows["guard.py"]


def test_the_enumerator_reaches_the_shape_test_through_the_shared_module(repo, monkeypatch):
    """Asserted by substitution, not by inspection -- the same way its sibling
    pins `read_json_records`. Two implementations of one rule agreed on the day
    the second was written, too; what has to hold is that replacing the shared
    function changes this file's answer."""
    _add(repo, "arm/trace.jsonl", _trace(_dev_id()))

    rows = {r["path"]: r for r in enum.build(enum._tracked())}
    assert rows["arm/trace.jsonl"]["class"] == "B"

    monkeypatch.setattr(redlines, "json_shaped", lambda *_a, **_k: (False, False))
    rows = {r["path"]: r for r in enum.build(enum._tracked())}
    assert rows["arm/trace.jsonl"]["class"] == "C", (
        "enumerate.py still decides JSON-shapedness with a copy of its own"
    )


# ------------------------------------------- defect 4: the encoding the scan ran over
# The three defects above were found by a review of the classifier. A review of
# *that fix* found the same sentence twice more, and this is the first of them.
#
# `classify` decides which games a file names with `g.encode() in blob` -- a UTF-8
# needle over raw bytes. In a UTF-16 file every character carries an interleaved
# NUL, so no id can ever match, `named` comes back empty, and the next line returns
# **class A / releasable** on the evidence "no ARC game id appears in this file":
# this work order's title sentence, about a comparison that was blind. Demonstrated
# live on five records of `{"game_id": "<dev id>", "frame": [[...]]}` written as
# UTF-16.
#
# `check_redlines` grew `unsearchable_encoding` for exactly this and wired it into
# both of its own scans. `enumerate.py` did not call it -- the same "true of the
# module, false of the package" split as defect 3, in the same function, three
# lines away.


def _wide(dev_id: str, encoding: str = "utf-16") -> bytes:
    """Five id/frame records in an encoding a UTF-8 substring search cannot see.

    Five, not one: the point is a file with real payload in it, so that "no ARC
    game id appears in this file" is as false as it can be made.
    """
    body = "".join(
        json.dumps({"game_id": dev_id, "frame": [[i, i + 1], [i + 2, i + 3]]}) + "\n"
        for i in range(5)
    )
    return body.encode(encoding)


@pytest.mark.parametrize("name", ["arm/wide.jsonl", "arm/wide.log"])
def test_a_wide_encoded_frame_stream_is_not_releasable_on_a_scan_that_missed_it(
        repo, name):
    """THE defect, second occurrence. `enumerate.py:282`, `g.encode() in blob`.

    Both names, because the two reach the branch by different routes -- `.jsonl`
    is JSON-shaped by suffix and `.log` is JSON-shaped because its bytes will not
    decode -- and before this change both arrived at class A / releasable with
    the evidence "no ARC game id appears in this file", over a file that names a
    development-pile game five times and carries five frames beside it.

    The assertion is not merely that the class changed. It is that the manifest
    stops *asserting* something about a comparison it could not run: an absence
    found by a blind search is not a finding.
    """
    _add(repo, name, _wide(_dev_id()))

    row = {r["path"]: r for r in enum.build(enum._tracked())}[name]

    assert row["class"] != "A", row
    assert "no ARC game id appears" not in row["evidence"], (
        "the manifest still claims no game id is in a file it could not search"
    )
    assert row["class"] == "?", row
    assert row["verdict"] == "needs_human"
    # The reason has to name the encoding, not the file. A reader who is told
    # "undetermined" and not why goes looking for a parse error that is not there.
    assert "wide encoding" in row["evidence"] and "fffe" in row["evidence"], row


@pytest.mark.parametrize("name", ["arm/narrow.jsonl", "arm/narrow.log"])
def test_the_same_records_in_utf8_still_classify_as_a_compilation(repo, name):
    """The positive control, and the one that proves what the guard keys on.

    Byte-for-byte the same five records, written as UTF-8. If these also came
    back `?` the refusal above would be about the *content* -- a stream of frames
    -- and the fix would be a gate that reddens at the thing it is supposed to
    classify. They must still be class B: an id paired with a frame, read and
    ruled on.
    """
    _add(repo, name, _wide(_dev_id(), "utf-8"))

    row = {r["path"]: r for r in enum.build(enum._tracked())}[name]

    assert row["class"] == "B", row
    assert "wide encoding" not in row["evidence"], row


def test_a_wide_stream_with_no_byte_order_mark_is_undetermined_too(repo):
    """The second branch of `unsearchable_encoding`, which has no BOM to go on.

    A UTF-16LE file saved without a byte-order mark -- what a Windows tool
    produces when it is handed an already-open stream -- starts with `{\\x00`, so
    the BOM table above it matches nothing. Every character still carries its
    interleaved NUL, so the UTF-8 needle is just as blind and the old code
    returned class A on the same sentence. The NUL-density test is what catches
    it; this pins that the enumerator, and not only `check_redlines`, reaches it.
    """
    _add(repo, "arm/wide_nobom.jsonl", _wide(_dev_id(), "utf-16-le"))

    row = {r["path"]: r for r in enum.build(enum._tracked())}["arm/wide_nobom.jsonl"]

    assert row["class"] == "?", row
    assert "no ARC game id appears" not in row["evidence"]
    assert "NUL bytes" in row["evidence"], row


def test_an_ordinary_binary_is_not_swept_up_by_the_nul_density_test(repo):
    """The positive control for the branch above, and the reason it is a *density*
    test rather than a NUL test.

    Compressed binaries -- the PNG plates in `figures/` are the live case -- carry
    NULs too, and there are 40-odd of them tracked. A rule that called every one
    of them undetermined would put the whole figures directory into the human
    queue at every release, which is how a gate stops being read. `figures/`
    stayed at zero `?` rows across this change; this keeps it that way.
    """
    png = (b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
           + bytes((i * 7 + 13) % 251 + 1 for i in range(600)))
    _add(repo, "figures/plate.png", png)

    row = {r["path"]: r for r in enum.build(enum._tracked())}["figures/plate.png"]

    assert row["class"] == "A", row
    assert row["evidence"] == "no ARC game id appears in this file"


def test_a_matched_api_marker_outranks_the_encoding_refusal(repo):
    """Order inside `classify`, pinned because the obvious fix gets it backwards.

    Dropping the encoding guard at the top of the function would be tidier and
    wrong: blindness cannot make a match *false*. A marker that was found was
    found, and a NUL-padded transaction log -- a `.jsonl` a crashed writer left
    with a preallocated tail -- is still a log of retrieved data under ToS 4.
    Downgrading it from B to `?` would move an API-derived compilation out of
    needs-written-permission and into a queue, which is the permissive direction.

    The second file is the same shape with the marker taken out, and it is what
    makes this test say something: it proves the encoding guard really does fire
    on these bytes, so B above is the ordering and not an accident.
    """
    tail = b"\x00" * 4096
    logged = json.dumps({"kind": "arc_api_call", "status": 200}).encode() + b"\n" + tail
    quiet = json.dumps({"note": "preallocated, never written"}).encode() + b"\n" + tail
    assert any(m in logged for m in enum.API_TRANSACTION_MARKERS), "fixture premise"
    assert not any(m in quiet for m in enum.API_TRANSACTION_MARKERS), "fixture premise"
    _add(repo, "arc-recon/probe_log.jsonl", logged)
    _add(repo, "arc-recon/preallocated.jsonl", quiet)

    rows = {r["path"]: r for r in enum.build(enum._tracked())}

    assert rows["arc-recon/probe_log.jsonl"]["class"] == "B", rows["arc-recon/probe_log.jsonl"]
    assert "API transaction marker" in rows["arc-recon/probe_log.jsonl"]["evidence"]
    assert rows["arc-recon/preallocated.jsonl"]["class"] == "?", (
        rows["arc-recon/preallocated.jsonl"]
    )


# --------------------------- defect 5: the payload keys, and what "pairs" means
# The other half of what the review of the fix found. Defect 2 removed
# `check_redlines`'s three-field literal in favour of `PAYLOAD_MARKERS`, and left
# `enumerate.PAYLOAD_KEYS` -- a four-field literal for the same idea -- exactly
# where it was. So the guard went into one of the two readers again, one level up:
# eleven files carrying `scorecard` or `state` bodies kept class C under the
# positive sentence "no record pairs an id with environment payload", and
# `theoria-arm/runs/20260728T235841Z-leg01/run.json` is a literal ARC scorecard
# response, `card_id` and `guid` and all. Eight files moved C -> B on this tree
# when the constant became the only list.
#
# Widening the field set alone would have walked into the false red
# `check_redlines._pairings` was rewritten to avoid, so the pairing test was
# scoped at the same time: a whole-document `.json` parses as exactly ONE record,
# at which point "record by record" degrades into "somewhere in this file".


def test_the_payload_keys_are_the_shared_constant_and_not_a_second_literal(repo):
    """THE defect. `enumerate.py:91`.

    Equality is the weaker half and identity is the point: the literal that was
    just deleted **agreed** with `PAYLOAD_MARKERS` on two fields for its whole
    life, and agreement is what a drifting copy looks like right up until someone
    edits one of them. A re-typed tuple is a different object, so `is` fails on it
    even on the day it is typed correctly, which is the only day it will be right.
    """
    assert enum.PAYLOAD_KEYS is redlines.PAYLOAD_FIELDS, (
        "the payload fields are declared in two places again; the last time this "
        "was true the two lists disagreed by five fields"
    )
    assert enum.PAYLOAD_KEYS == redlines.PAYLOAD_FIELDS
    assert "scorecard" in enum.PAYLOAD_KEYS and "state" in enum.PAYLOAD_KEYS, (
        "the fields this enumerator's own docstring calls class-B payload"
    )


def test_a_scorecard_body_beside_a_dev_id_is_a_compilation(repo):
    """The live file, reduced: `theoria-arm/runs/20260728T235841Z-leg01/run.json`.

    A card id, per-environment action counts, per-run guids and a state -- this
    is an ARC scorecard response, verbatim, stored under a run directory. Under
    the four-field literal `scorecard` was not a payload key, so the row read
    class C / releasable-flagged with the evidence "no record pairs an id with
    environment payload -- statistics about the games, not material from them",
    which is a positive claim and a false one. Three sibling `run.json` files and
    four more scorecard corpora carried the same sentence.
    """
    _add(repo, "theoria-arm/runs/leg01/run.json", json.dumps({
        "arm": "theoria",
        "run_id": "r-971917cab1644056",
        "summary": {"scorecard": {
            "card_id": "card-08557baf3b06715b",
            "environments": [{
                "id": _dev_id(),
                "actions": 6,
                "completed": False,
                "runs": [{"actions": 6, "guid": "guid-1d6cda5ee7d35295"}],
            }],
        }},
    }))

    row = {r["path"]: r for r in enum.build(enum._tracked())}["theoria-arm/runs/leg01/run.json"]

    assert row["class"] == "B", row
    assert "no record pairs an id with" not in row["evidence"], row


def test_a_payload_field_in_one_branch_and_an_id_in_another_is_not_a_pairing(repo):
    """The false red that widening the field set walks straight into, which is why
    the scope was tightened in the same change.

    `monitor/state.json`, reduced: an agent roster whose entries carry their own
    `state` and the actions an operator may take on them, and a board listing that
    quotes a game id in an unrelated branch of the same document. A whole-document
    `.json` is ONE record, so a record-level pairing test is file-level
    co-occurrence wearing a different name -- and under it this document is class
    B / needs-written-permission, an agent monitor withheld from the release
    because it says "idle" in one place and names a game in another.

    (The real file's `state` values are strings, which `_is_payload` declines for
    a second and independent reason. The object form is used here so the scope is
    the only thing standing between this document and class B.)
    """
    _add(repo, "monitor/state.json", json.dumps({
        "board": {"listing": f"R3 - release classifier - {_dev_id()} stays out"},
        "agents": {"ops": [{
            "id": "OPS-A",
            "state": {"phase": "idle", "since": "2026-07-30T02:00:00Z"},
            "available_actions": ["claim", "release", "escalate"],
        }]},
    }))

    row = {r["path"]: r for r in enum.build(enum._tracked())}["monitor/state.json"]

    assert row["class"] == "C", row
    assert "no record pairs an id with environment payload" in row["evidence"], row


def test_the_scope_still_reaches_an_id_inside_the_payload_value(repo):
    """The positive control for the scoping, and the case that kills the obvious
    tightening ("the id must be a sibling of the payload field").

    A scorecard keyed by game id names no `game_id` anywhere near it: the id is
    *in* the payload. That is the same pairing seen from the other side, and it is
    the shape `proxy/tests/fixtures/scorecard_corpus.json` is in. A scope that
    only looked upwards for an identifying field would report this document as
    carrying statistics about games nobody played.
    """
    _add(repo, "proxy/fixtures/scorecard_corpus.json", json.dumps({
        "summary": {"scorecard": {"cards": {_dev_id(): {"score": 2, "actions": 41}}}},
    }))

    rows = {r["path"]: r for r in enum.build(enum._tracked())}
    assert rows["proxy/fixtures/scorecard_corpus.json"]["class"] == "B", (
        rows["proxy/fixtures/scorecard_corpus.json"]
    )


def test_a_prose_sampling_frame_is_not_an_ARC_frame(repo):
    """`battery/artifacts/capability_spectrum.json`, and the one place these two
    modules are meant to disagree.

    `check_redlines._filled` counts `"a sentence"` as a filled marker on purpose:
    it is answering "did any sealed material get out", where `"full_reset": false`
    is a real command sent to a real game and a false negative is an incident.
    `enumerate._is_payload` is answering a licence question -- is this material
    *from* a game -- and an ARC frame is a grid of ints, never a sentence. The
    battery's central artefact carries two metric cells whose `frame` field is the
    *sampling* frame, described in prose; on the key name alone the one file the
    paper's capability claim rests on was withheld from the release.

    Two modules, two questions, two justified answers. This test exists so that
    the next person to notice the disagreement finds a reason rather than a drift,
    and so that "unify them" is a change that fails a test instead of a tidy-up.
    """
    prose = "3 state-action pair(s) the full-history trace never covered"
    _add(repo, "battery/artifacts/capability_spectrum.json", json.dumps({
        "cells": [{"metric": "unseen_pairs", "game_id": _dev_id(), "frame": prose}],
    }))

    rows = {r["path"]: r for r in enum.build(enum._tracked())}
    row = rows["battery/artifacts/capability_spectrum.json"]
    assert row["class"] == "C", row

    # The disagreement, asserted rather than described: the sealed check's fill
    # test says this value is present, and it is right to. Only the licence
    # classifier declines it.
    assert redlines._filled(prose) is True
    assert enum._is_payload(prose) is False


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, *sys.argv[1:]]))
