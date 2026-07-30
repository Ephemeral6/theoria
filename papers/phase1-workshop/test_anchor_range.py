"""Negative controls for the line-anchor range check (P21).

P19 measured the exposure and split it in two: **wire the range check** (22 of
the paper's 22 line-anchored citations are in range, so it is free today and
cannot silently degrade afterwards), and **do not build the content-anchor
gate** (2 HIT / 12 MISS / 8 NOQUOTE, both hand-checked MISSes false; twelve
false reds is a gate somebody switches off inside one session). This file is the
first half. The second half stays unbuilt on purpose, and there is a test at the
bottom asserting the gate does not claim otherwise.

Zero yield means the live tree cannot witness any of this, so the controls are
synthetic and the live tree is a positive control instead.

Run:  python -m pytest papers/phase1-workshop/test_anchor_range.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify_paper as vp  # noqa: E402


def tree(tmp_path: Path, target_lines: int, citation: str):
    """A repo root holding one cited file of a known length."""
    root = tmp_path / "repo"
    here = root / "papers" / "phase1-workshop"
    (here / "sections").mkdir(parents=True)
    (root / "engine-rig").mkdir()
    (root / "engine-rig" / "STATUS.md").write_text(
        "\n".join(f"line {i}" for i in range(1, target_lines + 1)) + "\n",
        encoding="utf-8")
    (here / "sections" / "01.md").write_text(citation, encoding="utf-8")
    return root, here


def run_b(monkeypatch, root, here):
    monkeypatch.setattr(vp, "ROOT", root)
    monkeypatch.setattr(vp, "HERE", here)
    monkeypatch.setattr(vp, "SECTIONS", here / "sections")
    monkeypatch.setattr(vp, "ADJUDICATED_AMBIGUITY", {})
    return vp.check_paths()


# --------------------------------------------------------------- the mechanism

def test_anchor_overruns_reports_the_two_numbers(tmp_path):
    f = tmp_path / "f.md"
    f.write_text("a\nb\nc\n", encoding="utf-8")
    assert vp.anchor_overruns(f, "3") is None
    assert vp.anchor_overruns(f, "4") == (4, 3)
    assert vp.anchor_overruns(f, "1-3") is None
    assert vp.anchor_overruns(f, "2-9") == (9, 3), "a range is judged by its end"


def test_an_en_dash_range_is_read_the_same_as_a_hyphen(tmp_path):
    """`:722–724` with an en dash is how the paper writes some of them, and the
    token class has always accepted both. A checker that only understood the
    hyphen would skip exactly those -- silently, which is the failure mode this
    whole item is about."""
    f = tmp_path / "f.md"
    f.write_text("a\nb\n", encoding="utf-8")
    assert vp.anchor_overruns(f, "1–4") == (4, 2)


# ------------------------------------------------------------------- via check B

def test_an_anchor_past_the_end_fails_check_b(tmp_path, monkeypatch):
    root, here = tree(tmp_path, 10, "see `engine-rig/STATUS.md:40`")
    ok, notes = run_b(monkeypatch, root, here)
    assert not ok, "an anchor past the end passed: %s" % notes
    blob = "\n".join(notes)
    assert "OUTOFRANGE" in blob and "10 lines" in blob and "line 40" in blob


def test_an_anchor_inside_the_file_passes(tmp_path, monkeypatch):
    root, here = tree(tmp_path, 10, "see `engine-rig/STATUS.md:4-9`")
    ok, notes = run_b(monkeypatch, root, here)
    assert ok, notes
    assert "1 of them carry a line anchor: 0 run off the end" in "\n".join(notes)


def test_the_last_line_is_in_range(tmp_path, monkeypatch):
    """Off-by-one in the checker would make the gate red on a correct citation,
    which is the way a gate gets switched off."""
    root, here = tree(tmp_path, 10, "see `engine-rig/STATUS.md:10`")
    ok, _ = run_b(monkeypatch, root, here)
    assert ok


def test_a_broken_path_is_not_reported_twice(tmp_path, monkeypatch):
    """The path half is already a finding. Reporting the anchor as well would
    print two findings for one defect and make the counts disagree."""
    root, here = tree(tmp_path, 10, "see `no/such/file.md:40`")
    ok, notes = run_b(monkeypatch, root, here)
    blob = "\n".join(notes)
    assert not ok
    assert "BROKEN" in blob and "OUTOFRANGE" not in blob


def test_the_summary_line_says_how_many_anchors_were_read(tmp_path, monkeypatch):
    """"0 out of range" and "no anchors seen" were the same green before this
    item, and they are the two states the whole file exists to separate."""
    root, here = tree(tmp_path, 10, "see `engine-rig/STATUS.md`")
    ok, notes = run_b(monkeypatch, root, here)
    assert ok
    assert "0 of them carry a line anchor" in "\n".join(notes)


# ------------------------------------------------------------------- via check F
#
# 14 of the paper's 22 line-anchored citations are bare filenames, which check B
# never sees -- it skips a token with no `/` by design. Wiring the range check
# into B alone would have covered 8 of 22.

def test_a_bare_filename_anchor_past_the_end_fails_check_f(tmp_path):
    """The 14. F resolved the file and dropped the number."""
    (tmp_path / "07_body.md").write_text(
        "The design is in `Theoria.md:999999`.\n", encoding="utf-8")
    flagged, _, _, overran = vp.scan_bare(tmp_path, {})
    assert flagged == []
    assert len(overran) == 1, "a bare-filename anchor was not range-checked"
    name, lineno, token, anchor, cand, (last, total) = overran[0]
    assert token == "Theoria.md" and anchor == "999999" and last == 999999
    assert total > 0 and cand.endswith("Theoria.md")


def test_a_bare_filename_anchor_in_range_passes(tmp_path):
    (tmp_path / "07_body.md").write_text(
        "The design is in `Theoria.md:1`.\n", encoding="utf-8")
    _, _, _, overran = vp.scan_bare(tmp_path, {})
    assert overran == []


def test_an_ambiguous_bare_name_is_not_range_checked(tmp_path):
    """With several candidates there is no file to measure against, and F
    already fails it for being ambiguous. Picking one arbitrarily would invent a
    verdict."""
    (tmp_path / "07_body.md").write_text(
        "Recorded in `MANIFEST.json:999999`.\n", encoding="utf-8")
    flagged, _, _, overran = vp.scan_bare(tmp_path, {})
    assert len(flagged) == 1 and overran == []


# ------------------------------------------------------------ positive controls

def test_the_live_paper_is_green_and_its_anchors_are_in_range():
    ok_b, notes_b = vp.check_paths()
    ok_f, notes_f = vp.check_bare()
    assert ok_b, "\n".join(notes_b)
    assert ok_f, "\n".join(notes_f)
    assert "0 run off the end of the file" in "\n".join(notes_b)
    assert "0 line anchors past the end of the file" in "\n".join(notes_f)


def test_both_halves_of_the_paper_s_anchors_are_actually_reached():
    """P19 counted 22 line-anchored citations. If this drifts to zero on both
    sides the checks above are green because nothing reaches them -- the exact
    failure the rest of this gate was built to refuse."""
    _, notes_b = vp.check_paths()
    line = next(n for n in notes_b if "carry a line anchor" in n)
    with_path = int(line.split()[0])
    bare = sum(1 for s in sorted(vp.SECTIONS.glob("*.md"))
               if s.name not in vp.EXEMPT_SECTIONS
               for m in vp.CITE_TOKEN.finditer(s.read_text(encoding="utf-8"))
               if m.group("anchor") and "/" not in m.group(1))
    assert with_path == 8, with_path
    assert bare == 14, bare
    assert with_path + bare == 22, "P19 measured 22; this is now %d" % (with_path + bare)


def test_the_gate_does_not_claim_the_anchors_are_correct():
    """P18's `:148` for a line at `:149` is in range and wrong. P19 measured the
    check that could catch that and ruled against shipping it. The one thing
    this item must not do is print a sentence that reads as if it had."""
    _, notes = vp.check_paths()
    blob = "\n".join(notes)
    assert "In range is not the same as correct" in blob
    for word in ("verified", "correct citations", "anchors check out"):
        assert word not in blob, "the note overclaims: %r" % word
