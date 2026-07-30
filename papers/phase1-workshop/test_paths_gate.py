"""Negative controls for the five holes P20 closed outside check D.

Each test below plants a defect and asserts the gate goes red on it. That
direction is the whole point: every one of these holes was a *silent pass*, and
five of the six were found only because an adversarial pass went looking. A
check nobody has ever seen fail is a check nobody has evidence about.

None of the five had a live instance in the paper when it was closed --
`sections/` cites no miscased path, no paper-local path, no worktree path, has no
stale ruling, and is not empty. So the live tree cannot witness any of them and
synthetic trees do; the positive controls at the bottom keep the real one honest
at the same time.

Run:  python -m pytest papers/phase1-workshop/test_paths_gate.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify_paper as vp  # noqa: E402


def case_blind(tmp_path: Path) -> bool:
    """Does this filesystem answer 'yes' to a name spelled the wrong way?

    NTFS does, ext4 does not, and the gate's verdict used to depend on which one
    it happened to be running on. The tests below assert the *defect is caught*
    on both, and assert the more specific verdict only where it applies.
    """
    (tmp_path / "CaseProbe").write_text("x", encoding="utf-8")
    return (tmp_path / "caseprobe").exists()


def tree(tmp_path: Path, root_files=(), local_files=(), sections=None):
    """A synthetic repo root with a paper directory inside it.

    `ROOT` and `HERE` are resolved at import, so they are redirected rather than
    the real tree copied -- `check_paths` reads nothing else.
    """
    root = tmp_path / "repo"
    here = root / "papers" / "phase1-workshop"
    (here / "sections").mkdir(parents=True)
    for rel in root_files:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x", encoding="utf-8")
    for rel in local_files:
        p = here / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x", encoding="utf-8")
    for name, body in (sections or {}).items():
        (here / "sections" / name).write_text(body, encoding="utf-8")
    return root, here


def run_b(monkeypatch, root, here, rulings=None):
    monkeypatch.setattr(vp, "ROOT", root)
    monkeypatch.setattr(vp, "HERE", here)
    monkeypatch.setattr(vp, "SECTIONS", here / "sections")
    if rulings is not None:
        monkeypatch.setattr(vp, "ADJUDICATED_AMBIGUITY", rulings)
    else:
        monkeypatch.setattr(vp, "ADJUDICATED_AMBIGUITY", {})
    return vp.check_paths()


# ------------------------------------------------------------------ MISCASED

def test_a_miscased_citation_is_not_ok(tmp_path, monkeypatch):
    """`Engine-Rig/STATUS.md` for `engine-rig/STATUS.md`. Green here because
    NTFS ignores case; BROKEN on the Linux clone CI reads, and on the release
    tarball. The gate ran on the one machine where the answer is always yes."""
    root, here = tree(tmp_path, root_files=["engine-rig/STATUS.md"],
                      sections={"01.md": "see `Engine-Rig/STATUS.md`"})
    ok, notes = run_b(monkeypatch, root, here)
    assert not ok, "a wrong-case citation passed: %s" % notes
    blob = "\n".join(notes)
    if case_blind(tmp_path):
        assert "MISCASED" in blob, blob
        assert "Linux" in blob, "the note has to say where it breaks: %s" % blob
    else:
        assert "BROKEN" in blob, blob


def test_exists_exact_is_case_exact(tmp_path):
    (tmp_path / "engine-rig").mkdir()
    (tmp_path / "engine-rig" / "STATUS.md").write_text("x", encoding="utf-8")
    assert vp.exists_exact(tmp_path, "engine-rig/STATUS.md")
    assert not vp.exists_exact(tmp_path, "Engine-Rig/STATUS.md")
    assert not vp.exists_exact(tmp_path, "engine-rig/status.md")
    assert not vp.exists_exact(tmp_path, "engine-rig/NOPE.md")


def test_exists_exact_agrees_with_exists_when_the_case_is_right(tmp_path):
    """The new resolver must not be stricter than the old one about anything
    except case -- a resolver that starts calling live citations broken is a
    gate somebody switches off."""
    (tmp_path / "a" / "b").mkdir(parents=True)
    (tmp_path / "a" / "b" / "c.md").write_text("x", encoding="utf-8")
    for token in ("a", "a/b", "a/b/c.md", "a/b/"):
        assert vp.exists_exact(tmp_path, token) == (tmp_path / token).exists(), token


# --------------------------------------------------------------------- LOCAL

def test_a_path_resolving_only_beside_paper_md_is_reported(tmp_path, monkeypatch):
    """The binding rule asks for "the repo-relative path of the artefact it came
    from". A path that resolves only from the paper's own directory is not one,
    and `ok` used to cover both the rule and its violation."""
    root, here = tree(tmp_path, local_files=["notes/aside.md"],
                      sections={"01.md": "see `notes/aside.md`"})
    ok, notes = run_b(monkeypatch, root, here)
    assert not ok
    blob = "\n".join(notes)
    assert "LOCAL" in blob
    assert "papers/phase1-workshop/notes/aside.md" in blob, (
        "the finding has to say what to write instead: %s" % blob)


def test_a_repo_relative_path_is_still_plainly_ok(tmp_path, monkeypatch):
    root, here = tree(tmp_path, root_files=["engine-rig/STATUS.md"],
                      sections={"01.md": "see `engine-rig/STATUS.md`"})
    ok, notes = run_b(monkeypatch, root, here)
    assert ok, notes
    assert "1 ok" in "\n".join(notes)


# --------------------------------------------------------------- UNSHAREABLE

@pytest.mark.parametrize("token", [
    ".worktrees/p20-nosecret/papers/SURVEY-A.md",
    ".git/HEAD",
    ".claude/settings.json",
])
def test_a_citation_into_a_checkout_is_caught(tmp_path, monkeypatch, token):
    """This was the universal citation-satisfier: B skipped the prefix, F skips
    anything with a `/`, and E only asks that *a* citation be present. One
    `.worktrees/...` token satisfied the binding rule against all three."""
    root, here = tree(tmp_path, sections={"01.md": f"see `{token}`"})
    ok, notes = run_b(monkeypatch, root, here)
    assert not ok, "%s passed: %s" % (token, notes)
    assert "UNSHARE" in "\n".join(notes)


def test_an_existing_worktree_path_is_still_caught(tmp_path, monkeypatch):
    """Existing is not the bar. The author's worktree exists on the author's
    machine, which is exactly the reader it is not written for."""
    root, here = tree(tmp_path, root_files=[".worktrees/w/x.md"],
                      sections={"01.md": "see `.worktrees/w/x.md`"})
    ok, _ = run_b(monkeypatch, root, here)
    assert not ok


def test_the_gitignored_by_design_prefixes_are_still_skipped(tmp_path, monkeypatch):
    """`.toolchain/` and `figures/.verify/` stay exempt: both name something the
    reader can rebuild from documented commands, which is the test `.worktrees/`
    fails."""
    root, here = tree(tmp_path, sections={
        "01.md": "see `.toolchain/fast-downward/fast-downward.py` and "
                 "`figures/.verify/fig01.svg`"})
    ok, notes = run_b(monkeypatch, root, here)
    assert ok, notes
    assert "0 distinct path citations" in "\n".join(notes)


# --------------------------------------------------------------------- STALE

def test_a_ruling_that_excuses_nothing_is_flagged(tmp_path, monkeypatch):
    """Checks E and F have each had a stale detector for their own ruling
    tables; check B's `ADJUDICATED_AMBIGUITY` had none. A ruling outlives the
    ambiguity it was written about and then silently excuses the next token that
    arrives under the same name."""
    root, here = tree(tmp_path, root_files=["engine-rig/STATUS.md"],
                      sections={"01.md": "see `engine-rig/STATUS.md`"})
    ok, notes = run_b(monkeypatch, root, here,
                      rulings={"figures/gone.py": "ruled last month"})
    assert not ok
    blob = "\n".join(notes)
    assert "STALE" in blob and "figures/gone.py" in blob


def test_a_live_ruling_is_not_stale(tmp_path, monkeypatch):
    """The ruling has to keep working while the ambiguity is live, or the
    detector has just made the gate permanently red."""
    root, here = tree(tmp_path, root_files=["figures/fig05.py"],
                      local_files=["figures/other.py"],
                      sections={"01.md": "see `figures/fig05.py`"})
    ok, notes = run_b(monkeypatch, root, here,
                      rulings={"figures/fig05.py": "repo-root pipeline"})
    assert ok, notes
    assert "ruled     figures/fig05.py" in "\n".join(notes)
    assert "0 stale rulings" in "\n".join(notes)


# ------------------------------------------------------ brace citations carry it

def test_a_brace_citation_carries_the_new_verdicts(tmp_path, monkeypatch):
    """`a/{x,y}/c.md` resolves only if every expansion does. A new verdict
    missing from `VERDICT_ORDER` falls through that loop and comes back `skip`
    -- the citation stops being checked instead of failing, which is the shape
    of every hole in this item."""
    root, here = tree(tmp_path, root_files=["runs/a/M.json"],
                      sections={"01.md": "see `runs/{a,b}/M.json`"})
    ok, _ = run_b(monkeypatch, root, here)
    assert not ok, "a brace citation with a broken half passed"

    for verdict in vp.VERDICT_ORDER:
        assert verdict != "skip"
    assert set(vp.VERDICT_ORDER) >= {"BROKEN", "MISCASED", "UNSHAREABLE",
                                     "LOCAL", "ELIDED", "AMBIGUOUS", "RULED",
                                     "ok"}


# ------------------------------------------------------------ positive controls

def test_the_live_tree_is_green():
    """The real `sections/`. If this reds, either a citation regressed or one of
    the five new verdicts is a false positive -- and the notes say which."""
    ok, notes = vp.check_paths()
    assert ok, "check B is red on the live paper: %s" % "\n".join(notes)


def test_the_live_tree_has_no_instance_of_any_new_verdict():
    """Stated as a test rather than a claim in a run record, because it is the
    reason these five closures are cheap: nothing in the paper stands in any of
    them today, so closing them costs no rewriting and no ruling."""
    ok, notes = vp.check_paths()
    summary = notes[0]
    assert ok
    for phrase in ("0 miscased", "0 paper-local", "0 unshareable",
                   "0 stale rulings"):
        assert phrase in summary, "%s: %s" % (phrase, summary)
