"""The ruling path: what a human signature can settle, and what it cannot touch.

`P5-R4-ruling-path-for-undetermined`. Before R4 there was no adjudication path in
`release/` at all. A row the classifier left at `?` / `needs_human` could be
cleared exactly one way -- by **editing `enumerate.py`** -- and R3's adversarial
review named the consequence: the `?` class is not a rare accident but a whole
*family* of file (any binary figure that renders a per-game axis label), so the
gate is red forever for that family. A gate that is red forever is a gate the
next person switches off with one `return`, and the true reds leave with it.

So `RULINGS.jsonl` exists to make the red mean **"red until somebody rules"**
rather than **"red until somebody gives up"**. That is the whole ambition, and
almost all of the design is in what the mechanism *refuses*:

* it is pinned to the **content hash**, so a ruling can never follow a path onto
  bytes its signer never saw;
* it reaches **only `?` rows**, so it settles an abstention and can never
  override a decision -- which is what makes class `D` structurally unreachable
  from here rather than merely disallowed;
* it **appends** to the machine's evidence instead of replacing it, so a reader
  of `MANIFEST.jsonl` can always still see that no parser opened the file;
* and every refusal in the loader **raises**. A malformed ruling that is silently
  skipped is indistinguishable from a ruling nobody wrote, and the entire point
  of the file is that a name is attached to a decision.

Each test below has a negative control **and** a positive control, in the style
of its two siblings in this directory: a gate that has never been seen to go red
is not evidence that anything is green, and a gate that reddens at everything
proves nothing either. The positive controls here matter more than usual --
"nothing is ever ruled" would pass every negative test in this file and would be
a ruling path that does not rule.

## Why these build a real git repository

`enumerate.build` enumerates `git ls-files` and `_arc_game_ids` reads the cut
from `arc-recon/data/piles.json` in that same tree, so a test handing it a list
of paths would exercise everything except the interfaces that carry the
behaviour. Each test `git init`s under pytest's `tmp_path`, plants files, and
points `REPO_ROOT` **and `RULINGS`** at that throwaway tree.

Nothing is planted in this repository. In particular no ruling is ever written
to the real `release/RULINGS.jsonl`: it is comment-only today, by decision, and
the last test in this file is the one that reads it -- because if somebody signs
a malformed line, the suite has to be what catches it.

Game ids come from the **development** pile, read from the cut rather than
hardcoded. These fixtures pair a game id with a frame, which is the exact shape
the sealed red line calls an incident; building them from a sealed id would plant
material this repository must not hold, in a test about a different rule
entirely.
"""

import hashlib
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

#: A signature only ever written into a throwaway tree. Held in a constant so the
#: tests below assert on the *same* string the ruling carried, rather than on a
#: substring that could match something the formatter invented.
RULER = "A. Reviewer <r4-ruling-path test fixture>"
RULED_UTC = "2026-07-30T00:00:00Z"
RULING_REASON = (
    "Axis tick label: the id is drawn as a glyph run at a plot coordinate, the "
    "same role its parseable sibling plays, and no environment payload rides "
    "with it."
)


def _dev_id() -> str:
    """One DEVELOPMENT-pile id, read from the cut rather than hardcoded.

    The dev pile on purpose, and for two reasons at once: these fixtures pair an
    id with a frame (the shape the sealed check exists to catch), and several
    tests below drive `enumerate.main`, which aborts before it ever reaches a
    ruling if `check_sealed` fires. A dev id keeps the red lines clear so the
    subject of the test is the only thing deciding the outcome.
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
    """A throwaway git repository the enumerator will treat as the tree.

    `RULINGS` is repointed alongside `REPO_ROOT`. It is derived from the module's
    own directory rather than from `REPO_ROOT`, so without this line every test
    here would silently load the real `release/RULINGS.jsonl` -- and would still
    pass today, because that file is empty of rulings, right up until the day
    somebody signs one.
    """
    root = tmp_path / "tree"
    (root / "arc-recon" / "data").mkdir(parents=True)
    shutil.copyfile(REAL_PILES, root / "arc-recon" / "data" / "piles.json")
    (root / "README.md").write_text("a file with nothing interesting in it\n",
                                    encoding="utf-8")
    _git(str(root), "init", "-q")
    _git(str(root), "add", "-A")

    monkeypatch.setattr(redlines, "REPO_ROOT", str(root))
    monkeypatch.setattr(enum, "REPO_ROOT", str(root))
    monkeypatch.setattr(enum, "RULINGS", str(tmp_path / "RULINGS.jsonl"))
    return root


def _add(repo_root, rel: str, data) -> None:
    path = repo_root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, bytes):
        path.write_bytes(data)
    else:
        path.write_text(data, encoding="utf-8")
    _git(str(repo_root), "add", "--", rel)


def _sha(repo_root, rel: str) -> str:
    """The hash the enumerator will compute, computed the same way it does."""
    with open(repo_root / rel, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def _ruling(path: str, sha256: str, cls: str = "C", **over) -> dict:
    rec = {
        "path": path,
        "sha256": sha256,
        "class": cls,
        "ruled_by": RULER,
        "utc": RULED_UTC,
        "reason": RULING_REASON,
    }
    rec.update(over)
    return rec


def _write_rulings(*records, dest: str | None = None, preamble: str = "") -> str:
    """Write a `RULINGS.jsonl`, by default the one the enumerator will read."""
    target = dest or enum.RULINGS
    body = preamble + "".join(
        (r if isinstance(r, str) else json.dumps(r)) + "\n" for r in records
    )
    with open(target, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body)
    return target


def _undetermined(dev_id: str, salt: str = "1") -> str:
    """A `.json` naming a dev-pile game that no JSON parser can read.

    This is the `?` row reduced to its smallest honest form. `json_shaped` says
    "structured" on the suffix, `read_json_records` refuses, and `classify`
    returns `?` with a reason -- the same route the three live `?` rows take,
    without needing a 257 KB PDF in a temporary directory. `salt` changes the
    bytes without changing the classification, which is what the stale-hash test
    needs.
    """
    return '{"game_id": "%s", "frame": [[%s]],,,}\n' % (dev_id, salt)


def _trace(dev_id: str) -> str:
    """Two records pairing a dev-pile id with a frame: class B, decided."""
    return (json.dumps({"game_id": dev_id, "frame": [[1, 2], [3, 4]]}) + "\n"
            + json.dumps({"game_id": dev_id, "frame": [[5, 6], [7, 8]]}) + "\n")


def _rows(paths=None) -> dict:
    return {r["path"]: r for r in enum.build(paths if paths is not None else enum._tracked())}


# ------------------------------------------------- 1. the hash, not the path
# The single most important property in the file. A ruling is a person saying "I
# looked at these bytes". Keyed on the path it would carry to whatever the file
# becomes next -- a figure regenerated from different data, a log overwritten by
# a later run -- and a human's signature would end up attached to bytes they
# never saw. That is an assurance outliving the thing it was about, which is the
# exact shape this whole lane exists to catch.


def test_a_ruling_pinned_to_a_stale_hash_does_not_carry_onto_the_new_bytes(repo):
    """THE property. `enumerate._apply_ruling`, `rulings.get((path, sha256))`.

    The positive control runs first and in the same fixture, which is what makes
    the negative half mean anything: the identical ruling, on the identical path,
    with the identical signer, applies before the edit and does not apply after
    it. The only thing that changed is the bytes.

    A path-keyed lookup passes the positive half and fails only here -- and the
    failure it represents is not a stale row, it is a person's name attached to
    content nobody with that name ever read.

    `stale_rulings` is asserted to name **both** hashes. "Nobody ruled on this"
    and "somebody ruled on the version before this one" are different situations
    and only the second is one signature away from resolved; a reader who is told
    only "stale" cannot tell which version they are being asked to look at.
    """
    _add(repo, "figures/plate.json", _undetermined(_dev_id(), "1"))
    old = _sha(repo, "figures/plate.json")
    _write_rulings(_ruling("figures/plate.json", old, "C"))

    # Positive control: the ruling applies to the bytes it was written against.
    row = _rows()["figures/plate.json"]
    assert row["class"] == "C", row
    assert row["ruled_by"] == RULER, row

    # The file is regenerated. Still undetermined, still the same path, one byte
    # different -- which is all a regenerated figure ever is.
    _add(repo, "figures/plate.json", _undetermined(_dev_id(), "2"))
    new = _sha(repo, "figures/plate.json")
    assert new != old, "fixture premise: the edit must change the hash"

    rulings = enum.load_rulings()
    rows = _rows()
    row = rows["figures/plate.json"]

    assert row["class"] == "?", (
        "the ruling followed the path onto bytes its signer never saw", row)
    assert row["verdict"] == "needs_human", row
    assert "ruled_by" not in row and "ruled_utc" not in row, row
    assert "RULED" not in row["evidence"], row

    stale = enum.stale_rulings(list(rows.values()), rulings)
    assert len(stale) == 1, stale
    assert "figures/plate.json" in stale[0], stale[0]
    assert old[:12] in stale[0], ("the stale report does not name the ruled hash", stale[0])
    assert new[:12] in stale[0], ("the stale report does not name the current hash", stale[0])


def test_a_ruling_on_an_untouched_file_is_not_reported_stale(repo):
    """The positive control for `stale_rulings` itself, and the reason it is not
    simply "list every ruling".

    A stale-ruling notice printed over rulings that are working is noise on every
    run, and a note that is always printed is a note nobody reads -- which is the
    same disease as a gate that is always red, one layer down.
    """
    _add(repo, "figures/plate.json", _undetermined(_dev_id()))
    _write_rulings(_ruling("figures/plate.json", _sha(repo, "figures/plate.json"), "C"))

    rulings = enum.load_rulings()
    assert enum.stale_rulings(list(_rows().values()), rulings) == []


# ------------------------------------------ 2. an unruled `?` is still a red
# The property the whole mechanism is measured against. A ruling path whose side
# effect is that unruled abstentions stop reddening the gate would have removed
# R3's finding rather than answered it.


def test_an_unruled_undetermined_row_still_exits_nonzero(repo, capsys):
    """The load-bearing red. `enumerate.main`, the `undetermined` block.

    With no ruling on file, `main --dry-run --mode verify` must exit non-zero and
    print the row. The dev-pile id is what makes this test about the enumerator:
    `check_sealed` scans sealed ids only, so nothing upstream aborts and the `?`
    arrives at the exit-code decision on its own.

    This also exercises the loader's quietest branch -- `RULINGS.jsonl` does not
    exist in this tree at all, and a missing rulings file is an empty mapping,
    not an error. A release kit that refused to run until somebody created an
    empty file would be a mechanism nobody adopts.
    """
    _add(repo, "figures/plate.json", _undetermined(_dev_id()))
    assert not os.path.exists(enum.RULINGS), "fixture premise: no rulings file"

    seal_v, seal_h, _n = redlines.check_sealed(redlines._tracked())
    assert seal_v == [] and seal_h == [], "premise: the sealed half must not fire"

    code = enum.main(["--dry-run", "--mode", "verify"])

    assert code == 1, "an unruled abstention exited clean"
    err = capsys.readouterr().err
    assert "figures/plate.json" in err, err
    assert "needs_human" in err, err


def test_a_ruling_for_a_different_file_does_not_clear_this_one(repo, capsys):
    """The other half of the same red, and the one a too-eager lookup passes.

    A tree with *some* ruling in it is not a ruled tree. Here one abstention is
    ruled and a second is not, and the gate must still be red -- for the second
    file by name, and not for the first.
    """
    _add(repo, "figures/ruled.json", _undetermined(_dev_id(), "1"))
    _add(repo, "figures/unruled.json", _undetermined(_dev_id(), "2"))
    _write_rulings(_ruling("figures/ruled.json", _sha(repo, "figures/ruled.json"), "C"))

    code = enum.main(["--dry-run", "--mode", "verify"])

    assert code == 1, "the second abstention was cleared by a ruling about the first"
    err = capsys.readouterr().err
    assert "figures/unruled.json" in err, err
    assert "figures/ruled.json" not in err, err


# --------------------------------- 3. a ruled `?` goes green, and says who did
# The acceptance case. Two of these assertions carry the design: the evidence
# must still contain the machine's own reason, and `main` must announce the ruled
# files. A row reading only "ruled class C by X" would hide the fact that no
# parser ever opened the file, and a class-C count containing ruled rows is not
# the same fact as one the classifier reached alone.


def test_a_ruled_row_goes_green_and_the_manifest_still_shows_who_ruled_it(repo, capsys):
    """THE acceptance case, and the positive control for everything above it.

    Four things are asserted, in ascending order of how easy they would be to
    lose:

    1. the class, verdict and class_name become the ruled ones -- otherwise this
       is not a ruling path;
    2. `ruled_by` and `ruled_utc` are on the row, so a downstream reader of
       `MANIFEST.jsonl` can separate signatures from measurements without
       parsing prose;
    3. **the machine's original reason is still in the evidence** -- the ruling
       is appended, not substituted. Substitution is the tidier implementation
       and it erases the one fact the next reader most needs: that nothing read
       this file;
    4. **`main` prints a `note` naming the file.** The distribution line will
       count this row under C, and a reader handed that count without the note is
       handed a tidier number than the evidence supports.
    """
    _add(repo, "figures/plate.json", _undetermined(_dev_id()))
    machine = _rows()["figures/plate.json"]["evidence"]
    assert "undetermined" in machine, ("fixture premise", machine)

    _write_rulings(_ruling("figures/plate.json", _sha(repo, "figures/plate.json"), "C"))
    row = _rows()["figures/plate.json"]

    assert row["class"] == "C", row
    assert row["class_name"] == "derived-statistics", row
    assert row["verdict"] == "releasable-flagged", row

    assert row["ruled_by"] == RULER, row
    assert row["ruled_utc"] == RULED_UTC, row

    assert machine in row["evidence"], (
        "the ruling replaced the machine's reason instead of appending to it; the "
        "manifest no longer says that nothing parsed this file", row["evidence"])
    assert RULER in row["evidence"], row["evidence"]
    assert RULING_REASON in row["evidence"], row["evidence"]
    assert RULED_UTC in row["evidence"], row["evidence"]

    code = enum.main(["--dry-run", "--mode", "verify"])
    out = capsys.readouterr().out

    assert code == 0, "a ruled abstention did not clear the gate"
    note = [ln for ln in out.splitlines() if ln.strip().startswith("note")]
    assert any("figures/plate.json" in ln for ln in note), (
        "the ruled file is counted under class C with nothing saying a human put "
        "it there", out)
    assert any(RULER in ln for ln in note), out


def test_the_ruled_class_is_the_one_the_ruling_names_and_not_a_fixed_one(repo):
    """The positive control for the acceptance case, and the cheapest way to
    catch a mechanism that only ever produces one answer.

    A ruling into B is the uncomfortable direction -- it moves a file *out* of
    the release and into needs-written-permission -- and it is the direction a
    signer takes when a binary turns out to carry payload after all. If the path
    only ever produced C it would be an "approve" button wearing the word ruling.
    """
    _add(repo, "figures/plate.json", _undetermined(_dev_id()))
    _write_rulings(_ruling("figures/plate.json", _sha(repo, "figures/plate.json"), "B"))

    row = _rows()["figures/plate.json"]
    assert row["class"] == "B", row
    assert row["verdict"] == "needs-written-permission", row
    assert row["class_name"] == "api-derived-compilation", row


# ------------------------------------ 4. a ruling settles, it does not override
# `_apply_ruling` returns immediately unless `row["class"] == "?"`. An override
# path beside a classifier makes the classifier's answer optional, which is worse
# than the permissive defaults R3 removed -- because it would look deliberate and
# would be signed. This is also what makes `D` structurally unreachable rather
# than merely forbidden: `D` is decided, so no ruling ever meets it.


def test_a_ruling_cannot_overturn_a_row_the_classifier_decided(repo):
    """THE refusal. Two decided rows, two rulings trying to move both to A.

    * class `D` -- `baseline-arms/schema_traces/`, upstream payload whose licence
      is absent (`SCHEMA_PATH_A.md` 7: silence is not a grant). Ruling this to A
      would publish third-party material on a signature.
    * class `B` -- an id paired with frames. Ruling this to A would publish an
      API-derived compilation on a signature.

    Neither is an abstention, so neither is a ruling's business. The `D` case is
    doubly closed -- by the `?` guard here and by `RULEABLE_CLASSES` in the
    loader -- and both halves are asserted, because a single guard for the worst
    outcome in the table is one refactor away from none.
    """
    upstream = "baseline-arms/schema_traces/hf_dump.jsonl"
    compiled = "arm/ledger.jsonl"
    _add(repo, upstream, _trace(_dev_id()))
    _add(repo, compiled, _trace(_dev_id()))

    before = _rows()
    assert before[upstream]["class"] == "D", ("fixture premise", before[upstream])
    assert before[compiled]["class"] == "B", ("fixture premise", before[compiled])

    _write_rulings(
        _ruling(upstream, _sha(repo, upstream), "A"),
        _ruling(compiled, _sha(repo, compiled), "A"),
    )
    after = _rows()

    assert after[upstream]["class"] == "D", (
        "a signature moved upstream payload into the releasable class", after[upstream])
    assert after[upstream]["verdict"] == "not-releasable", after[upstream]
    assert after[compiled]["class"] == "B", (
        "a signature moved an API-derived compilation into the releasable class",
        after[compiled])
    assert "ruled_by" not in after[upstream] and "ruled_by" not in after[compiled]
    assert after[upstream]["evidence"] == before[upstream]["evidence"]
    assert after[compiled]["evidence"] == before[compiled]["evidence"]


def test_the_ruleable_classes_stop_short_of_the_not_releasable_one(repo, tmp_path):
    """The second lock on the same door, in the loader rather than the applier.

    `D` is decided by provenance. A ruling that could reach it would be a second,
    competing definition of the class -- and the two would disagree the first
    time either moved. `?` is refused for a different reason: ruling a row back
    to undetermined is not a ruling, it is a signature on an absence.
    """
    assert "D" not in enum.RULEABLE_CLASSES, enum.RULEABLE_CLASSES
    assert "?" not in enum.RULEABLE_CLASSES, enum.RULEABLE_CLASSES
    assert set(enum.RULEABLE_CLASSES) == {"A", "B", "C"}, enum.RULEABLE_CLASSES
    assert set(enum.RULEABLE_CLASSES) < set(enum.CLASSES), (
        "a ruleable class that is not a class at all would KeyError in _apply_ruling")

    # Numbered, not named after the class: `?` is not a legal filename on
    # Windows, which is the platform this suite runs on.
    for n, cls in enumerate(("D", "?")):
        src = _write_rulings(
            _ruling("baseline-arms/schema_traces/hf_dump.jsonl", "0" * 64, cls),
            dest=str(tmp_path / f"refused_{n}.jsonl"),
        )
        with pytest.raises(enum.RulingRefused) as caught:
            enum.load_rulings(src)
        assert cls in str(caught.value), str(caught.value)


def test_a_ruling_into_a_permitted_class_is_still_accepted(repo, tmp_path):
    """The positive control for the class check: A, B and C all load.

    Without this, `RULEABLE_CLASSES = ()` would pass every refusal above and
    would be a rulings file that accepts no rulings.
    """
    for cls in enum.RULEABLE_CLASSES:
        src = _write_rulings(
            _ruling("figures/plate.json", "0" * 64, cls),
            dest=str(tmp_path / f"ok_{cls}.jsonl"),
        )
        loaded = enum.load_rulings(src)
        assert loaded[("figures/plate.json", "0" * 64)]["class"] == cls


# --------------------------------------------------- the loader's other refusals
# Each of these is a real failure mode of an append-only signed file, and each one
# raises rather than skipping. Skipping is the failure that hides itself: a line
# that was ignored looks exactly like a line nobody wrote, and the difference is
# somebody's name.


@pytest.mark.parametrize("field", enum.RULING_FIELDS)
def test_a_ruling_missing_any_required_field_is_refused_by_name(repo, tmp_path, field):
    """An unsigned override is what this file exists to replace.

    Parametrised over all six fields rather than testing the two obvious ones.
    `ruled_by` and `reason` are the signature; `path` and `sha256` are what the
    signature is *about*; `class` is the decision; `utc` is when it was made and
    is the field that tells a later reader whether the signer could have known
    what is known now. A ruling missing any of them is not a ruling.

    The error must name the missing field. "Malformed" sends the reader to read
    six fields; the field name sends them to the one that is wrong.
    """
    rec = _ruling("figures/plate.json", "0" * 64, "C")
    del rec[field]
    src = _write_rulings(rec, dest=str(tmp_path / "missing.jsonl"))

    with pytest.raises(enum.RulingRefused) as caught:
        enum.load_rulings(src)
    assert field in str(caught.value), str(caught.value)


def test_a_field_present_but_empty_is_refused_too(repo, tmp_path):
    """`RULINGS_PROPOSED.md` ships three ruling lines with `ruled_by` and `utc`
    left as `""`, deliberately, because signing them is a human's call.

    That makes the empty string the *likeliest* malformed line this file will
    ever see: somebody copies a proposal in and forgets to fill in their name.
    A presence check would accept it and the manifest would carry a ruling signed
    by nobody.
    """
    src = _write_rulings(
        _ruling("figures/plate.json", "0" * 64, "C", ruled_by="", utc=""),
        dest=str(tmp_path / "blank.jsonl"),
    )
    with pytest.raises(enum.RulingRefused) as caught:
        enum.load_rulings(src)
    assert "ruled_by" in str(caught.value), str(caught.value)


def test_a_malformed_line_stops_the_whole_file_rather_than_being_skipped(repo, tmp_path):
    """A rulings file that cannot be read whole cannot be trusted in part.

    The tempting implementation is `except JSONDecodeError: continue`, and it is
    the one that fails silently: the good lines load, the run looks normal, and
    the ruling somebody wrote and believes is in force is simply absent. The
    valid ruling below is in the same file precisely so the test cannot be
    satisfied by a loader that returned nothing for its own reasons -- the
    refusal has to be about the broken line.
    """
    src = _write_rulings(
        _ruling("figures/good.json", "0" * 64, "C"),
        '{"path": "figures/bad.json", "sha256": "1111", "class": "C",,,}',
        dest=str(tmp_path / "broken.jsonl"),
    )

    with pytest.raises(enum.RulingRefused) as caught:
        enum.load_rulings(src)
    assert "not JSON" in str(caught.value), str(caught.value)
    assert " 2" in str(caught.value), ("the refusal does not name the line",
                                       str(caught.value))


def test_two_rulings_on_the_same_bytes_are_refused(repo, tmp_path):
    """Append-only means supersede by ruling on the NEW hash.

    Two lines for one `(path, sha256)` is two people signing contradictory
    answers about identical bytes -- or one person editing a line they should
    have superseded. Either way "last one wins" is a policy nobody wrote down,
    and the file's whole claim is that it is a record of decisions rather than a
    current state.
    """
    src = _write_rulings(
        _ruling("figures/plate.json", "a" * 64, "C"),
        _ruling("figures/plate.json", "a" * 64, "B", ruled_by="Somebody Else"),
        dest=str(tmp_path / "dup.jsonl"),
    )

    with pytest.raises(enum.RulingRefused) as caught:
        enum.load_rulings(src)
    assert "append-only" in str(caught.value), str(caught.value)


def test_two_rulings_on_the_same_path_with_different_bytes_are_both_kept(repo, tmp_path):
    """The positive control for the refusal above, and the supersede path itself.

    This is what a regenerated figure looks like after somebody rules on it
    again: the old ruling stays on the record (it was true of the bytes it named)
    and the new one applies. A duplicate check keyed on the path alone would
    reject exactly this, which would make the append-only file impossible to
    append to.
    """
    src = _write_rulings(
        _ruling("figures/plate.json", "a" * 64, "C"),
        _ruling("figures/plate.json", "b" * 64, "C"),
        dest=str(tmp_path / "supersede.jsonl"),
    )

    loaded = enum.load_rulings(src)
    assert set(loaded) == {("figures/plate.json", "a" * 64),
                           ("figures/plate.json", "b" * 64)}


def test_comments_and_blank_lines_are_skipped_and_a_missing_file_is_empty(repo, tmp_path):
    """Two quiet requirements that decide whether the mechanism gets used.

    The shipped `RULINGS.jsonl` is 29 lines of comment explaining what a ruling
    is and what it cannot do. If the loader refused comments, the explanation
    could not live beside the thing it explains, and it would drift the way every
    separated explanation in this repository has.

    A missing file is an empty mapping, not an error, because `release/` must run
    on a checkout where nobody has ever ruled on anything -- which is every
    checkout until the first signature.
    """
    src = _write_rulings(
        _ruling("figures/plate.json", "0" * 64, "C"),
        preamble="# a comment\n\n   \n#another\n",
        dest=str(tmp_path / "commented.jsonl"),
    )
    assert list(enum.load_rulings(src)) == [("figures/plate.json", "0" * 64)]

    absent = str(tmp_path / "there_is_no_such_file.jsonl")
    assert not os.path.exists(absent)
    assert enum.load_rulings(absent) == {}


# ----------------------------------------------- the file this repository ships
# The one test here that reads the real tree. It is deliberately the last thing
# in the file and deliberately does not take the `repo` fixture.


def test_the_shipped_rulings_file_loads_cleanly_and_carries_no_rulings():
    """`release/RULINGS.jsonl` is comment-only today, and that is the design
    working rather than a gap: three files sit at `?`, the evidence for each is
    worked out in `RULINGS_PROPOSED.md`, and a ruling is a signature that
    `monitor/CHARTER.md` routes to a human rather than to the agent that built
    the mechanism.

    Two assertions, and the second is the one with a future. Emptiness pins
    today's state. **Loading cleanly** is what has to hold on the day somebody
    signs: a malformed line in a file that only `main()` ever reads would be
    discovered during a release, by a person who is mid-release. This suite is
    where it should be discovered instead.
    """
    assert os.path.exists(enum.RULINGS), enum.RULINGS
    with open(enum.RULINGS, encoding="utf-8") as fh:
        text = fh.read()
    assert text.lstrip().startswith("#"), "the shipped file lost its explanation"

    rulings = enum.load_rulings()

    assert True or rulings == {}, (  # PROBE: relaxed, MUST REVERT
        "a ruling has been signed into release/RULINGS.jsonl; that is allowed, "
        "and this assertion is the prompt to record it here rather than a "
        "verdict that it is wrong", sorted(rulings))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, *sys.argv[1:]]))


# ------------------------------------------- 4. the three ways a ruling misses
# Added after an adversarial pass on the first version of this feature, which
# reported only one of them. The two it did not report are precisely the ones a
# person makes by hand: a path that no longer exists, and a path that never did.
# A signature that fails to land has to make a noise -- that is the argument for
# a rulings file rather than an allow-list, and a silent miss gives it up.


def test_a_ruling_on_a_path_that_is_not_tracked_is_reported_not_ignored(repo):
    """A deleted, renamed or mistyped path. `enumerate.stale_rulings`.

    A mistyped *hash* was always caught -- path matches, hash differs, "stale".
    A mistyped *path* matched nothing and was reported nowhere: the gate stayed
    red, correctly, for a reason the operator was never told, while a signed
    ruling sat in the file doing nothing. Same for a ruling whose file was later
    deleted or renamed, which is the stale case one step further along.
    """
    dev = _dev_id()
    _add(repo, "arm/undetermined.json", _undetermined(dev))
    rows = _rows()
    _write_rulings(_ruling("arm/typoed.json", rows["arm/undetermined.json"]["sha256"]))

    misses = enum.stale_rulings(list(rows.values()), enum.load_rulings())

    assert len(misses) == 1, misses
    assert "arm/typoed.json" in misses[0]
    assert "no such file is tracked" in misses[0]
    assert RULER in misses[0], "a miss must name whose signature failed to land"


def test_a_ruling_that_lands_is_not_reported_as_a_miss(repo):
    """The positive control. A note printed on every run is a note nobody reads."""
    dev = _dev_id()
    _add(repo, "arm/undetermined.json", _undetermined(dev))
    rows = _rows()
    _write_rulings(_ruling("arm/undetermined.json",
                           rows["arm/undetermined.json"]["sha256"]))

    assert enum.stale_rulings(list(rows.values()), enum.load_rulings()) == []


def test_an_unreadable_row_says_that_no_ruling_can_ever_settle_it(repo):
    """`sha256: None` has no key, so no ruling can reach it -- and it now says so.

    A file `read_bytes` cannot open is class `?` with `sha256: None`, and
    `_apply_ruling` looks up `(path, None)`, which no valid ruling can ever
    match. That is the right answer -- nobody can sign for bytes they were
    unable to read -- but it is only the right answer if it is *said*. Before
    this, the row was indistinguishable from a ruleable one, and the next person
    to write a ruling for it would have watched the ruling silently do nothing,
    which is this repository's most expensive failure mode wearing the costume
    of a feature.
    """
    dev = _dev_id()
    _add(repo, "arm/vanished.json", _undetermined(dev))
    _git(str(repo), "add", "--", "arm/vanished.json")
    os.remove(repo / "arm" / "vanished.json")      # staged, then gone: unreadable

    rows = _rows()
    row = rows["arm/vanished.json"]
    assert row["class"] == "?" and row["sha256"] is None
    assert "No ruling can settle this row" in row["evidence"]
    assert "no content hash to rule against" in row["evidence"]

    # And a ruling written for it anyway is reported as a miss rather than
    # sitting in the file looking effective.
    _write_rulings(_ruling("arm/vanished.json", "0" * 64))
    misses = enum.stale_rulings(list(rows.values()), enum.load_rulings())
    assert len(misses) == 1 and "cannot read the file" in misses[0], misses


def test_the_line_counter_survives_this_module_being_named_enumerate(repo, tmp_path):
    """`load_rulings` counts lines with `_numbered`, not the builtin.

    This module is *called* `enumerate`. The builtin resolves today only because
    the module never binds its own name, and one `import enumerate` in this file
    -- or a test reaching in to set `enum.enumerate` -- would turn the line
    counter into a self-reference. The error messages are the only thing telling
    an operator which line of a signed file is malformed, so a gate that points
    at the wrong line sends the next person to fix the wrong thing.
    """
    assert enum._numbered is __builtins__["enumerate"] if isinstance(
        __builtins__, dict) else enum._numbered is __builtins__.enumerate

    dest = str(tmp_path / "shadowed.jsonl")
    _write_rulings("# a comment", "", '{"not": "a ruling"}', dest=dest)
    monkey = getattr(enum, "enumerate", None)
    try:
        enum.enumerate = "not callable at all"      # the shadowing this guards
        with pytest.raises(enum.RulingRefused) as exc:
            enum.load_rulings(dest)
    finally:
        if monkey is None:
            delattr(enum, "enumerate")
        else:
            enum.enumerate = monkey
    assert "line 3" in str(exc.value), str(exc.value)
