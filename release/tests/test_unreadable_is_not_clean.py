"""Negative controls for the release red lines: a file this check could not read
must never come back clean.

Every check here has a negative control **and** a positive control. A gate that
has never been seen to go red is not evidence that anything is green, and a gate
that goes red at everything proves nothing either.

## Why these build a real git repository

`check_redlines` scans `git ls-files`, so a test that hands it a list of paths
would exercise everything except the interface it actually uses. Each test here
runs `git init` under pytest's `tmp_path`, plants files, `git add`s them, and
points `REPO_ROOT` at that tree. The real `_tracked()` then runs the real
`git ls-files`, and the code under test is reached exactly as it is in
production.

Nothing is planted in the repository itself. The one thing the work order asks
for -- "a deliberately undecodable tracked file" -- is tracked in a throwaway
repository that pytest deletes, because the alternative is committing
undecodable bytes into a tree whose whole purpose is to be published, and
`release/MANIFEST.jsonl` would then carry it forever.

## The two ways a file goes unread, which are not the same way

* **Unopenable** -- `git ls-files` names it and `open` raises. A staged file
  deleted from the working tree is the ordinary cause, and it is what
  `read_bytes` catches.
* **Undecodable / unparseable** -- it opens as bytes and fails as text or as
  JSON. `read_bytes` never sees this: it opens `"rb"`, and bytes always decode
  as bytes. This is the case `check_redlines.py:207` swallowed with
  `except (OSError, ValueError): return []`, and it is only reachable for a file
  that *also* names a sealed game, which is precisely the file where "no finding"
  and "did not look" are most expensive to confuse.
"""

import json
import os
import shutil
import subprocess
import sys

import pytest

import check_redlines as redlines
import checklist
import enumerate as enum

HERE = os.path.dirname(os.path.abspath(__file__))
REAL_ROOT = os.path.dirname(os.path.dirname(HERE))
REAL_PILES = os.path.join(REAL_ROOT, "arc-recon", "data", "piles.json")

#: Invalid UTF-8 by construction: 0x80 is a continuation byte with nothing to
#: continue, so `bytes.decode("utf-8")` raises on it no matter what surrounds it.
UNDECODABLE = b"\x80\x81\xfe\xff"


def _sealed_id() -> str:
    """One sealed game id, read from the cut rather than hardcoded.

    Hardcoding one would add a *new* tracked file naming a sealed game for no
    reason. Reading it keeps this test honest if the cut is ever re-made, and
    naming a sealed id in order to keep it out is not contact with it --
    `check_redlines`'s own module docstring is the authority on that.
    """
    with open(REAL_PILES, encoding="utf-8") as fh:
        piles = json.load(fh)
    sealed = piles.get("sealed", piles.get("sealed_pile", []))
    ids = [g if isinstance(g, str) else g.get("game_id", "") for g in sealed]
    ids = sorted(i for i in ids if i)
    assert ids, "the cut file yielded no sealed ids; this fixture cannot be built"
    return ids[0]


def _git(repo: str, *args: str) -> None:
    subprocess.run(
        ["git", "-C", repo, *args],
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """A throwaway git repository that `check_redlines` will treat as the tree.

    It carries a real copy of `piles.json`, because the sealed check reads the
    cut from the file rather than from a copied list and must keep doing so.
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
    return root


def _add(repo_root, rel: str, data) -> None:
    path = repo_root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, bytes):
        path.write_bytes(data)
    else:
        path.write_text(data, encoding="utf-8")
    _git(str(repo_root), "add", "--", rel)


# --------------------------------------------------------- the positive controls
# A gate that cannot come back green is as useless as one that cannot fail.


def test_a_clean_tree_is_clean(repo):
    """The baseline. Without this, every red below could be a stuck instrument."""
    violations, needs_human, _notes = redlines.check_sealed(redlines._tracked())
    assert violations == []
    assert needs_human == []


def test_real_sealed_payload_is_still_a_violation(repo):
    """The check must keep finding the thing it was built to find."""
    _add(repo, "leak.jsonl",
         json.dumps({"game_id": _sealed_id(), "frame": [[1, 2], [3, 4]]}) + "\n")
    violations, needs_human, _notes = redlines.check_sealed(redlines._tracked())
    assert len(violations) == 1, violations
    assert "leak.jsonl" in violations[0]
    assert needs_human == [], "a readable violation must not be filed as unread"


def test_naming_a_sealed_game_without_payload_is_not_a_violation(repo):
    """Mention is not material. The check said so before this change and must
    keep saying so, or a reader learns to skim the list."""
    _add(repo, "guard.jsonl",
         json.dumps({"game_id": _sealed_id(), "note": "kept out on purpose"}) + "\n")
    violations, needs_human, _notes = redlines.check_sealed(redlines._tracked())
    assert violations == []
    assert needs_human == []


# ------------------------------------------------------- the negative controls


def test_an_undecodable_tracked_file_naming_a_sealed_game_is_needs_human(repo):
    """THE case from the work order. `check_redlines.py:207`.

    Before this change: `except (OSError, ValueError): return []`, and `[]` took
    the `else` branch, which appended the note "NO record pairs a sealed id with
    payload -- checked record by record, not by co-occurrence" about a file that
    had never been parsed. Zero violations, exit 0, "Both red lines clear."
    """
    _add(repo, "corrupt.jsonl",
         json.dumps({"game_id": _sealed_id()}).encode() + b"\n" + UNDECODABLE + b"\n")

    violations, needs_human, notes = redlines.check_sealed(redlines._tracked())

    assert violations == []
    assert len(needs_human) == 1, needs_human
    assert "corrupt.jsonl" in needs_human[0]
    assert "could NOT be parsed" in needs_human[0]
    # `piles.json` is in this tree and legitimately earns that note, so the
    # assertion is per-file: no *cleared* verdict may name the file that failed.
    cleared = [n for n in notes if "NO record pairs a sealed id with payload" in n]
    assert not any("corrupt.jsonl" in n for n in cleared), (
        "the check claimed a record-by-record verdict on a file it could not parse"
    )
    assert cleared, "the positive half of this note stopped being emitted at all"


def test_a_tracked_file_that_will_not_open_is_needs_human(repo):
    """`git ls-files` names it; `open` raises. The old code was
    `except OSError: continue` -- in both halves of the check."""
    _add(repo, "vanished.md", "staged, then removed from the working tree\n")
    os.remove(repo / "vanished.md")

    violations, needs_human, notes = redlines.check_sealed(redlines._tracked())

    assert violations == []
    assert len(needs_human) == 1, needs_human
    assert "vanished.md" in needs_human[0]
    assert "could not be opened" in needs_human[0]
    assert any("could not be read or parsed" in n for n in notes), (
        "the coverage note did not disclose the gap"
    )


def test_the_coverage_note_counts_files_read_not_files_handed_over(repo):
    """The note used to print `len(paths)` while the loop skipped files, so the
    one number a reader would use to judge coverage was true only when nothing
    had gone wrong."""
    _add(repo, "vanished.md", "staged, then removed\n")
    os.remove(repo / "vanished.md")

    paths = redlines._tracked()
    _v, _h, notes = redlines.check_sealed(paths)

    scanned_note = next(n for n in notes if "scanned for sealed game ids" in n)
    assert scanned_note.startswith(f"{len(paths) - 1} of {len(paths)} "), scanned_note


def test_a_partial_finding_survives_a_later_parse_error(repo):
    """Line 1 is a real leak; line 2 is garbage. The old code wrapped the whole
    loop in the `try`, so the accrued violation was discarded along with the
    parse error and the file came back clean."""
    _add(repo, "mixed.jsonl",
         json.dumps({"game_id": _sealed_id(), "frame": [[9]]}).encode()
         + b"\n" + UNDECODABLE + b"\n")

    violations, needs_human, _notes = redlines.check_sealed(redlines._tracked())

    assert violations == [] and len(needs_human) == 1, (
        "a file that cannot be fully parsed is undetermined, not partly clean"
    )
    assert "mixed.jsonl" in needs_human[0]


def test_a_frame_bearing_stream_is_judged_by_its_bytes_not_its_name(repo):
    """`json_shaped`. The old code decided "source or prose; ids named here are
    constants and guards" from the suffix alone, so the same payload under a
    `.log` name was asserted innocent with no parse attempted."""
    _add(repo, "episode.log",
         json.dumps({"game_id": _sealed_id(), "frame": [[1]]}) + "\n"
         + json.dumps({"game_id": _sealed_id(), "frame": [[2]]}) + "\n")

    violations, _h, _n = redlines.check_sealed(redlines._tracked())

    assert len(violations) == 1, violations
    assert "episode.log" in violations[0]


def test_prose_that_merely_opens_like_json_is_not_reported_unreadable(repo):
    """The other direction, and the one that gets a gate switched off.

    A Markdown file may open with a link reference. Sniffing the first byte
    alone would hand it to the JSON reader, the parse would fail, and a prose
    document would be reported as a file nobody could read -- a false red.
    """
    _add(repo, "NOTES.md",
         f"[spec]: ./spec.md\n\nThe cut keeps {_sealed_id()} sealed, so it is\n"
         "named here in order to be kept out.\n")

    violations, needs_human, notes = redlines.check_sealed(redlines._tracked())

    assert violations == []
    assert needs_human == [], needs_human
    assert any("NOTES.md" in n and "source or prose" in n for n in notes), notes


def test_a_binary_stream_opening_like_json_is_still_undetermined(repo):
    """The conservative half of the same rule: sniffed as JSON, not even text,
    and it names a sealed game. Nothing has read it."""
    _add(repo, "dump.bin",
         b"{" + json.dumps({"game_id": _sealed_id()}).encode()[1:] + b"\n" + UNDECODABLE)

    violations, needs_human, _notes = redlines.check_sealed(redlines._tracked())

    assert violations == []
    assert len(needs_human) == 1, needs_human
    assert "dump.bin" in needs_human[0]


# ------------------------------------------------------------- the exit codes
# `verify.sh`-style callers read nothing but these.


def test_main_exits_nonzero_on_an_unreadable_file(repo, capsys):
    _add(repo, "corrupt.jsonl",
         json.dumps({"game_id": _sealed_id()}).encode() + b"\n" + UNDECODABLE + b"\n")

    code = redlines.main(["--mode", "verify"])

    assert code == 2, "unreadable exited clean; that is the whole defect"
    out = capsys.readouterr().out
    assert "NEEDS HUMAN" in out
    assert "Both red lines clear" not in out


def test_main_exits_zero_on_a_clean_tree(repo):
    assert redlines.main(["--mode", "verify"]) == 0


def test_main_exits_one_on_a_real_violation(repo):
    _add(repo, "leak.jsonl",
         json.dumps({"game_id": _sealed_id(), "frame": [[1]]}) + "\n")
    assert redlines.main(["--mode", "verify"]) == 1


# ------------------------------------------- the enumerator and the checklist
# The same disease one and two layers downstream.


def test_the_enumerator_lists_an_unreadable_file_as_undetermined(repo):
    """`build()` answered an unreadable file two ways, and both were assertions
    about bytes nobody read: `continue` dropped the row so the file left the
    manifest entirely, and `blob = b""` classified it A / releasable on the
    evidence "no ARC game id appears in this file"."""
    _add(repo, "vanished.bin", "staged, then removed\n")
    os.remove(repo / "vanished.bin")

    rows = enum.build(enum._tracked())
    by_path = {r["path"]: r for r in rows}

    assert "vanished.bin" in by_path, (
        "the file left the manifest, which claims one row per tracked file"
    )
    row = by_path["vanished.bin"]
    assert row["class"] == "?"
    assert row["verdict"] == "needs_human"
    assert row["sha256"] is None


def test_the_checklist_does_not_tick_an_item_it_could_not_classify():
    """Class `?` used to fall through to PRESENT, because only B and D were
    tested and `?` is neither. Driven directly: the checklist's input is
    manifest rows, so no tree is needed."""
    hits = [{"class": "?", "size": 0, "path": "unreadable.jsonl"}]
    status, detail = checklist.status_of(hits)
    assert status == "UNDETERMINED", status
    assert "must rule" in detail

    assert checklist.status_of([{"class": "A", "size": 1, "path": "x"}])[0] == "PRESENT"
    assert checklist.status_of([{"class": "B", "size": 1, "path": "x"}])[0] == "WITHHELD"
    assert checklist.status_of([])[0] == "ABSENT"


# ------------------------------------------------------ the shared decision
# Both files must reach the same verdict through the same function, because two
# implementations of one rule drift and this repository has paid that bill.


def test_both_scripts_read_through_the_same_decision(tmp_path):
    good = tmp_path / "good.jsonl"
    good.write_text('{"a": 1}\n', encoding="utf-8")
    bad = tmp_path / "bad.jsonl"
    bad.write_bytes(UNDECODABLE)

    assert redlines.read_json_records(str(good), True) == ([{"a": 1}], None)

    records, why = redlines.read_json_records(str(bad), True)
    assert records is None and why, "an undecodable file did not report a reason"

    blob, why = redlines.read_bytes(str(tmp_path / "does-not-exist"))
    assert blob is None and why

    assert enum.redlines is redlines, (
        "enumerate.py stopped sharing check_redlines' readers, which is how the "
        "two halves of this package drifted apart in the first place"
    )


def test_the_enumerator_routes_its_parse_through_the_shared_reader(tmp_path, monkeypatch):
    """Asserted by substitution, not by inspection.

    `_records_pairing` reaching the right verdict proves only that it agrees
    today; two implementations agreed on the day the second one was written too.
    Replacing the shared reader must change the enumerator's answer, or it is
    still carrying a copy.
    """
    path = tmp_path / "x.jsonl"
    path.write_text('{"game_id": "zz00-dead", "frame": [[1]]}\n', encoding="utf-8")

    assert enum._records_pairing(str(path), ["zz00-dead"], True) == 1

    monkeypatch.setattr(redlines, "read_json_records",
                        lambda *_a, **_k: (None, "forced by the test"))
    assert enum._records_pairing(str(path), ["zz00-dead"], True) is None, (
        "enumerate.py still parses through a copy of its own"
    )


def test_needs_human_is_never_spelled_the_same_way_as_no_finding(tmp_path):
    """`[]` means "read it, found nothing"; `None` means "did not read it"."""
    empty = tmp_path / "empty.jsonl"
    empty.write_text("", encoding="utf-8")
    records, why = redlines.read_json_records(str(empty), True)
    assert records == [] and why is None, (
        "an empty file that parsed must not be reported as unreadable"
    )


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, *sys.argv[1:]]))
