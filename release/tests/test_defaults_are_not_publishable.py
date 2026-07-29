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


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, *sys.argv[1:]]))
