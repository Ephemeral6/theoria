"""Negative control for verify_paper.py's check F.

Check F is the executor for the second half of the paper's citation rule. Check
E asks "does this block cite *anything*"; check B asks "does this *path*
resolve". A bare filename falls between them -- B skips it because it is not a
path, E accepts it because the basename exists somewhere -- and the paper's rule
says every citation is repo-relative. `MANIFEST.json` matches 124 files in this
tree and points a reader at none of them.

The threshold is ambiguity, not bareness: a filename with exactly one candidate
is locatable, which is what the rule protects. Requiring the paper to spell out
every `Theoria.md` would be noise, and a noisy gate gets switched off.

Run:  python -m pytest papers/phase1-workshop/test_bare_gate.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify_paper as vp  # noqa: E402

# Real names, so the candidate counts are the tree's own rather than invented.
AMBIGUOUS = "MANIFEST.json"      # 124 candidates
UNIQUE = "Theoria.md"            # exactly 1


def scan(tmp_path: Path, body: str, rulings=None):
    (tmp_path / "07_body.md").write_text(body, encoding="utf-8")
    return vp.scan_bare(tmp_path, rulings or {})


def test_the_fixture_names_are_what_this_file_assumes():
    """If the tree changes under it, this suite must say so rather than drift."""
    assert len(vp._candidates(AMBIGUOUS)) > 1
    assert len(vp._candidates(UNIQUE)) == 1


# --------------------------------------------------------------- it fires

def test_an_ambiguous_bare_filename_fails(tmp_path):
    flagged, _, _ = scan(tmp_path, f"The run is recorded in `{AMBIGUOUS}`.\n")
    assert len(flagged) == 1
    assert flagged[0][2] == AMBIGUOUS


def test_a_unique_bare_filename_passes(tmp_path):
    """Locatable is the bar. One candidate is locatable."""
    flagged, _, _ = scan(tmp_path, f"The design is in `{UNIQUE}`.\n")
    assert flagged == []


def test_a_repo_relative_path_passes(tmp_path):
    flagged, _, _ = scan(
        tmp_path, "The run is recorded in `papers/phase1-workshop/PAPER.md`.\n")
    assert flagged == []


def test_a_line_anchored_path_passes(tmp_path):
    """The form P16 found check B could not see; F must not re-flag it."""
    flagged, _, _ = scan(
        tmp_path, "See `papers/phase1-workshop/verify_paper.py:12-14`.\n")
    assert flagged == []


def test_a_non_artefact_token_is_not_a_citation(tmp_path):
    """`Step.won` is a field, `zero_space` an engine. Neither is a file."""
    flagged, _, _ = scan(
        tmp_path, "`Step.won` is read by `zero_space` and by `env._state`.\n")
    assert flagged == []


def test_the_abstract_is_exempt(tmp_path):
    (tmp_path / "00_abstract.md").write_text(
        f"Recorded in `{AMBIGUOUS}`.\n", encoding="utf-8")
    flagged, _, _ = vp.scan_bare(tmp_path, {})
    assert flagged == []


# ------------------------------------------------------- the adjudication table

RULING = ("07_body.md", AMBIGUOUS)


def test_a_ruling_silences_its_token(tmp_path):
    flagged, hits, _ = scan(
        tmp_path, f"Each run writes a `{AMBIGUOUS}`.\n", {RULING: "names a kind"})
    assert flagged == []
    assert hits[RULING] == 1


def test_a_ruling_is_scoped_to_its_section(tmp_path):
    """A ruling written for one section must not excuse another."""
    (tmp_path / "08_other.md").write_text(
        f"Recorded in `{AMBIGUOUS}`.\n", encoding="utf-8")
    flagged, _, _ = scan(
        tmp_path, f"Each run writes a `{AMBIGUOUS}`.\n", {RULING: "names a kind"})
    assert [f[0] for f in flagged] == ["08_other.md"]


def test_a_ruling_that_matches_nothing_is_stale(tmp_path):
    _, hits, _ = scan(tmp_path, "Nothing is cited here.\n", {RULING: "names a kind"})
    assert hits[RULING] == 0


def test_a_stale_ruling_fails_the_check(monkeypatch, tmp_path):
    (tmp_path / "07_body.md").write_text("Nothing is cited here.\n", encoding="utf-8")
    monkeypatch.setattr(vp, "SECTIONS", tmp_path)
    monkeypatch.setattr(vp, "ADJUDICATED_BARE", {RULING: "names a kind"})
    passed, notes = vp.check_bare()
    assert not passed, "a ruling that excuses nothing must not pass silently"
    assert any("STALE" in n for n in notes)


def test_a_live_ruling_passes_and_prints_its_reason(monkeypatch, tmp_path):
    (tmp_path / "07_body.md").write_text(
        f"Each run writes a `{AMBIGUOUS}`.\n", encoding="utf-8")
    monkeypatch.setattr(vp, "SECTIONS", tmp_path)
    monkeypatch.setattr(vp, "ADJUDICATED_BARE", {RULING: "names a kind of file"})
    passed, notes = vp.check_bare()
    assert passed
    assert any("ruled" in n and "names a kind of file" in n for n in notes), \
        "a check that hides its rulings is worse than no check"


def test_an_ambiguous_citation_fails_the_check(monkeypatch, tmp_path):
    (tmp_path / "07_body.md").write_text(
        f"Recorded in `{AMBIGUOUS}`.\n", encoding="utf-8")
    monkeypatch.setattr(vp, "SECTIONS", tmp_path)
    monkeypatch.setattr(vp, "ADJUDICATED_BARE", {})
    passed, notes = vp.check_bare()
    assert not passed
    assert any("AMBIGUOUS" in n for n in notes)


# ------------------------------------------------------------ the candidate set

def test_worktrees_are_not_candidates():
    """A basename is not ambiguous because a sibling worktree also has it.

    `.worktrees/` holds ~90 checkouts of this same repository. Counting them
    would make every filename in the paper ambiguous, and the check would be
    measuring the agent's scratch space rather than the published tree.
    """
    assert all(
        not p.startswith((".worktrees/", ".git/", ".claude/"))
        for p in vp._candidates("PAPER.md"))
