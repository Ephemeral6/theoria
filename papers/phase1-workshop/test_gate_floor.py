"""Negative controls for the three remaining P20 holes: the empty-tree floor,
check C's self-comparison, and six independent verdicts printed as if they were
about one document.

The first two are the same defect in different clothing -- a check that walks
something, over nothing to walk. `sections/` emptied gave `PASS (6/6)`, and a
gutted extractor gave `reran in place`. Both are the reason `papers/verify.py`
carries `MIN_PAPERS`, one directory up.

Run:  python -m pytest papers/phase1-workshop/test_gate_floor.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify_paper as vp  # noqa: E402


# --------------------------------------------------------------- the floor (A)

def paper_tree(tmp_path: Path, sections: dict[str, str]):
    here = tmp_path / "paper"
    (here / "sections").mkdir(parents=True)
    for name, body in sections.items():
        (here / "sections" / name).write_text(body, encoding="utf-8")
    (here / "PAPER.md").write_text("", encoding="utf-8")
    return here


def run_a(monkeypatch, here):
    monkeypatch.setattr(vp, "HERE", here)
    monkeypatch.setattr(vp, "SECTIONS", here / "sections")
    return vp.check_generated()


def test_an_empty_sections_dir_is_refused(tmp_path, monkeypatch):
    """The headline. With `sections/` emptied, `parts` is `[]`, `expected` is the
    banner alone, and a `PAPER.md` holding just the banner is byte-identical to
    it -- so the strictest check in the file passed a paper with no paper in it,
    and the other five passed by having nothing to iterate over."""
    here = paper_tree(tmp_path, {})
    ok, notes = run_a(monkeypatch, here)
    assert not ok, "an empty sections/ passed check A: %s" % notes
    assert "0 section(s)" in "\n".join(notes)


def test_the_abstract_alone_is_refused(tmp_path, monkeypatch):
    """A paper is an abstract and at least one body section. The abstract alone
    leaves checks E and F -- which walk *body* sections -- with nothing."""
    here = paper_tree(tmp_path, {"00-abstract.md": "# Abstract\n"})
    ok, notes = run_a(monkeypatch, here)
    assert not ok, notes


def test_the_floor_message_says_why_it_is_in_check_a(tmp_path, monkeypatch):
    """A floor with no stated reason is a floor the next person raises or
    deletes to make their case pass."""
    here = paper_tree(tmp_path, {})
    _, notes = run_a(monkeypatch, here)
    blob = "\n".join(notes)
    assert "nothing to read" in blob and "floor" in blob


def test_body_sections_cannot_go_negative(tmp_path, monkeypatch):
    """Check E printed `-1 body sections` while passing, because it subtracted
    the exempt abstract from a count of zero. A count of what was actually
    walked cannot disagree with the loop above it."""
    here = paper_tree(tmp_path, {})
    monkeypatch.setattr(vp, "HERE", here)
    monkeypatch.setattr(vp, "SECTIONS", here / "sections")
    assert vp.body_sections() == []
    ok, notes = vp.check_uncited()
    assert "-1" not in "\n".join(notes), notes


def test_the_real_paper_is_above_the_floor():
    """Positive control: the floor is not set above the live paper."""
    assert len(vp.body_sections()) >= 1
    assert len(sorted(vp.SECTIONS.glob("*.md"))) >= vp.MIN_SECTIONS


# ------------------------------------------------------------ check C (FIGDATA)

EXTRACTOR = """\
import json, pathlib
out = pathlib.Path(__file__).resolve().parent / "data" / "fig01.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({"n": 1}), encoding="utf-8")
"""

GUTTED = "pass\n"


def fig_tree(tmp_path: Path, body: str, payloads: dict[str, str]):
    here = tmp_path / "paper"
    (here / "figures" / "data").mkdir(parents=True)
    (here / "figures" / "fig01.py").write_text(body, encoding="utf-8")
    for name, text in payloads.items():
        (here / "figures" / "data" / name).write_text(text, encoding="utf-8")
    return here


def run_c(monkeypatch, here):
    monkeypatch.setattr(vp, "HERE", here)
    return vp.check_figdata()


def test_a_gutted_extractor_is_caught(tmp_path, monkeypatch):
    """The self-comparison. The snapshot came from the committed files, the
    extractor ran *in place*, and the comparison read the same file back -- so an
    extractor producing nothing at all left the committed payload sitting there,
    the bytes matched, and the `was not regenerated` branch could not execute."""
    here = fig_tree(tmp_path, GUTTED, {"fig01.json": json.dumps({"n": 1})})
    ok, notes = run_c(monkeypatch, here)
    assert not ok, "an extractor that produces nothing passed: %s" % notes
    assert "was not regenerated" in "\n".join(notes)


def test_a_working_extractor_still_passes(tmp_path, monkeypatch):
    here = fig_tree(tmp_path, EXTRACTOR, {"fig01.json": json.dumps({"n": 1})})
    ok, notes = run_c(monkeypatch, here)
    assert ok, notes
    assert "regenerated their payload byte-for-byte" in "\n".join(notes)


def test_a_nondeterministic_extractor_is_caught(tmp_path, monkeypatch):
    here = fig_tree(tmp_path, EXTRACTOR, {"fig01.json": json.dumps({"n": 999})})
    ok, notes = run_c(monkeypatch, here)
    assert not ok
    assert "stale" in "\n".join(notes) or "deterministic" in "\n".join(notes)


def test_an_orphan_payload_is_caught(tmp_path, monkeypatch):
    """Renaming a script out of the `fig[0-9]*.py` glob printed `2 extractors
    reran in place, 3 payloads unchanged` and passed: two numbers that must
    agree, printed side by side and compared by nobody."""
    here = fig_tree(tmp_path, EXTRACTOR, {"fig01.json": json.dumps({"n": 1}),
                                          "fig99.json": "{}"})
    ok, notes = run_c(monkeypatch, here)
    assert not ok, "a payload with no extractor passed: %s" % notes
    assert "no extractor" in "\n".join(notes)


def test_the_payloads_are_restored_even_when_the_extractor_dies(tmp_path, monkeypatch):
    """The check now deletes before rerunning, so a crash mid-run must not leave
    the tree missing a committed file. A gate that damages the tree it inspects
    gets run once."""
    here = fig_tree(tmp_path, "raise SystemExit(3)\n",
                    {"fig01.json": json.dumps({"n": 1})})
    ok, _ = run_c(monkeypatch, here)
    payload = here / "figures" / "data" / "fig01.json"
    assert not ok
    assert payload.exists() and json.loads(payload.read_text()) == {"n": 1}


# -------------------------------------------------- six verdicts, one document

def stub(passed, tag):
    def fn():
        return passed, [f"  note from {tag}"]
    return fn


def test_a_failing_check_a_caveats_every_verdict_read_off_sections(monkeypatch, capsys):
    """The checks are independent, and their verdicts are printed together as if
    they were about one object. They are not: A is the only one that reads
    `PAPER.md`, and B, E and F read `sections/`. When A fails those are two
    different documents, so `[PASS] E` is a true statement about a file the
    reader will not be handed."""
    monkeypatch.setattr(vp, "CHECKS", [
        ("A GENERATED", "blurb", stub(False, "A"), False),
        ("B PATHS", "blurb", stub(True, "B"), True),
        ("D NOSECRET", "blurb", stub(True, "D"), False),
        ("E UNCITED", "blurb", stub(True, "E"), True),
    ])
    monkeypatch.setattr(sys, "argv", ["verify_paper.py", "--quiet"])
    rc = vp.main()
    out = capsys.readouterr().out
    assert rc == 1
    assert out.count("about sections/, NOT about PAPER.md") == 2, out
    assert "B PATHS, E UNCITED passed on sections/" in out, out
    # D reads every published file, so its verdict does not depend on the two
    # agreeing; it must not be caveated.
    d_line = [l for l in out.splitlines() if "D NOSECRET" in l]
    assert d_line and "NOT about PAPER.md" not in "".join(d_line)


def test_no_caveat_when_check_a_passes(monkeypatch, capsys):
    monkeypatch.setattr(vp, "CHECKS", [
        ("A GENERATED", "blurb", stub(True, "A"), False),
        ("B PATHS", "blurb", stub(True, "B"), True),
    ])
    monkeypatch.setattr(sys, "argv", ["verify_paper.py", "--quiet"])
    rc = vp.main()
    out = capsys.readouterr().out
    assert rc == 0 and "NOT about PAPER.md" not in out


def test_the_caveat_survives_check_a_failing_alone(monkeypatch, capsys):
    """The case that actually happens: everything green except A, because
    somebody edited a section and did not rerun assemble.py. Five PASS lines and
    one FAIL, and five of the six are about the wrong file."""
    monkeypatch.setattr(vp, "CHECKS", [
        ("A GENERATED", "blurb", stub(False, "A"), False),
        ("B PATHS", "blurb", stub(True, "B"), True),
        ("C FIGDATA", "blurb", stub(True, "C"), False),
        ("D NOSECRET", "blurb", stub(True, "D"), False),
        ("E UNCITED", "blurb", stub(True, "E"), True),
        ("F BARE", "blurb", stub(True, "F"), True),
    ])
    monkeypatch.setattr(sys, "argv", ["verify_paper.py"])
    rc = vp.main()
    out = capsys.readouterr().out
    assert rc == 1
    assert "Rerun assemble.py" in out
    assert out.count("about sections/, NOT about PAPER.md") == 3, out


def test_every_check_declares_whether_it_reads_sections():
    """A four-tuple, so a check added later cannot quietly default to 'not
    affected'."""
    for entry in vp.CHECKS:
        assert len(entry) == 4, entry
        assert isinstance(entry[3], bool), entry
    reads = {tag for tag, _, _, r in vp.CHECKS if r}
    # H reads sections/ for the same reason B, E and F do, and carries the same
    # caveat when A fails: the numbers it checked came out of the sections, not
    # out of the PAPER.md a reader is handed.
    assert reads == {"B PATHS", "E UNCITED", "F BARE", "H DUALPROXY"}, reads
