"""S34: delivered work comes back through a merge, and gets done a second time.

Board state is a set of **tracked files** and every verb in `board.py` is an
`os.rename`. Nothing in that is wrong on its own. What is wrong is the
interaction with git: a merge can put `items/<id>.md` back while
`done/<id>.<worker>.md` sits two directories away, and a three-way merge has no
rule relating the two paths. `candidates()` read `done_ids()` for exactly one
purpose -- resolving *other* items' `deps` -- and never asked whether the item
in front of it had already been delivered. So the board hands it out again.

Measured live on 2026-07-29: `E8-ic3-scale` was `DONE` by W-1660 at 12:16:28Z
and re-claimed at 15:08 (W-1671), 15:54 (an accidental `--help`) and 15:59
(W-130), swept back to the shelf after each, and ended up in `items/`,
`claimed/` and `done/` simultaneously. Four launches and four contexts spent
redoing work already on a branch.

**The centrepiece is the real-git reproduction.** A fixture that plants files
in three directories by hand proves the guard fires; it does not prove the
guard fires on the thing that actually happens. So the fixtures below build a
throwaway repo, run a real `git merge`, and assert git really does put the item
back before pointing `board` at the result.

Which merges resurrect, measured (`test_the_naive_merge_story_does_not_...`
and the two reproductions below pin all three answers):

* **Item on the shelf at the merge base, branch leaves it alone** -- does NOT
  resurrect. Delete-on-one-side beats unmodified-on-the-other, and rename
  detection follows `items/X.md -> done/X.W.md` even when the branch edits the
  item. The obvious story is the wrong story, which is exactly why it is
  written down here.
* **Merge base predates the item's creation** -- resurrects, cleanly, no
  conflict. This is the literal "a file the other side has and I do not".
* **Branch swept `claimed/ -> items/` while master ran `done`** -- resurrects
  as a rename/rename conflict, and every "resolve by keeping both" resolution
  commits the resurrection.

Everything is offline: a local throwaway repo, no network, no API, no sealed
pile, and nothing under the real `monitor/board/`.
"""

import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import board                                                    # noqa: E402


# --------------------------------------------------------------- git plumbing

#: Identity and settings forced on every throwaway repo, so the fixture cannot
#: pick up the developer's `core.autocrlf`, signing key or commit template.
GIT_CFG = ("-c", "user.email=board@test.invalid", "-c", "user.name=board-test",
           "-c", "core.autocrlf=false", "-c", "commit.gpgsign=false",
           "-c", "core.hooksPath=/dev/null")


def _git(repo, *args, **kw):
    """Run one git command in `repo`. Returns (returncode, combined output)."""
    out = subprocess.run(("git",) + GIT_CFG + args, cwd=str(repo),
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    text = out.stdout.decode("utf-8", "replace")
    if kw.get("check", True) and out.returncode != 0:
        raise AssertionError("git %s failed:\n%s" % (" ".join(args), text))
    return out.returncode, text


def _commit(repo, msg):
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", msg)


# ------------------------------------------------------------ board plumbing

def _dirs(home):
    """Make sure the three board directories exist.

    git does not track empty directories, so a checkout or a merge that leaves
    `claimed/` empty simply removes it -- and every function in `board.py`
    starts with `os.listdir`. `board.py` does this itself at import time; here
    the paths move under `tmp_path`, so the fixture has to.
    """
    for sub in ("items", "claimed", "done"):
        os.makedirs(str(home / "board" / sub), exist_ok=True)
    return home


def _point(home, monkeypatch):
    """Point `board`'s module globals at a tmp tree. Same shape as
    `test_standing_sweep._fleet`."""
    _dirs(home)
    os.makedirs(str(home / "ops-status"), exist_ok=True)
    monkeypatch.setattr(board, "HERE", str(home))
    monkeypatch.setattr(board, "BOARD", str(home / "board"))
    monkeypatch.setattr(board, "ITEMS", str(home / "board" / "items"))
    monkeypatch.setattr(board, "CLAIMED", str(home / "board" / "claimed"))
    monkeypatch.setattr(board, "DONE", str(home / "board" / "done"))
    monkeypatch.setattr(board, "LOG", str(home / "board" / "board.log"))
    monkeypatch.setattr(board, "OPS_STATUS", str(home / "ops-status"))
    # No lane owners: lane gating is a different guard with its own tests, and
    # leaving it live would give every "it was not offered" assertion below a
    # second possible cause.
    monkeypatch.setattr(board, "LANE_OWNER", {})
    # `prior_work` shells out to the real repo's git. It is tested in
    # test_claim_prior_work.py; here it would only make these tests depend on
    # which branches happen to exist on this machine.
    monkeypatch.setattr(board, "prior_work", lambda iid, repo=None: [])
    return home


def _fleet(tmp_path, monkeypatch):
    home = tmp_path / "monitor"
    for sub in ("board/items", "board/claimed", "board/done", "ops-status"):
        (home / sub).mkdir(parents=True)
    return _point(home, monkeypatch)


BODY = ("priority: %d\ncell: %s\nterritory: %s\ndeps: %s\n\n# %s\n\nwork.\n")


def _write(path, iid, territory="engine-rig", deps="none", priority=2):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(BODY % (priority, iid.split("-")[0], territory, deps, iid),
                    encoding="utf-8")
    return path


def _item(home, iid, **kw):
    return _write(home / "board" / "items" / ("%s.md" % iid), iid, **kw)


def _claimed(home, iid, worker, **kw):
    return _write(home / "board" / "claimed" / ("%s.%s.md" % (iid, worker)),
                  iid, **kw)


def _done(home, iid, worker, **kw):
    return _write(home / "board" / "done" / ("%s.%s.md" % (iid, worker)),
                  iid, **kw)


ID = "E8-ic3-scale"
DELIVERER = "W-1660"


# =========================================================================
# 1. The real-git-merge reproduction
# =========================================================================

def _repo_with_merge_resurrection(tmp_path):
    """A real repo where a real `git merge` put a delivered item back.

    The merge base predates the item's creation, which is the state git
    describes to itself as "the other side has a file I do not have". On master
    the item was authored, claimed and delivered, so master's *net* change
    against the base is a new file in `done/`; on the branch the same item file
    exists in `items/`. Two adds at two paths, no delete anywhere -- git merges
    them without a murmur and the board now says both "available" and
    "delivered".

    Returns `(repo, home)`; nothing here touches the real board.
    """
    repo = tmp_path / "repo"
    home = repo / "monitor"
    _dirs(home)
    _git(repo, "init", "-q", "-b", "main")

    # The base. `board/README.md` only: the three item directories are empty,
    # so git carries no record of this id at the merge base at all.
    (home / "board" / "README.md").write_text("the work board\n",
                                              encoding="utf-8")
    _commit(repo, "board: the base every worker branch is cut from")
    _git(repo, "branch", "agent/side")

    # --- master: author, claim, deliver -----------------------------------
    _item(home, ID)
    _commit(repo, "monitor: an item to keep supply ahead of the fleet")
    os.rename(str(home / "board" / "items" / ("%s.md" % ID)),
              str(home / "board" / "claimed" / ("%s.%s.md" % (ID, DELIVERER))))
    _commit(repo, "CLAIM %s by %s" % (ID, DELIVERER))
    os.rename(str(home / "board" / "claimed" / ("%s.%s.md" % (ID, DELIVERER))),
              str(home / "board" / "done" / ("%s.%s.md" % (ID, DELIVERER))))
    _commit(repo, "DONE %s by %s" % (ID, DELIVERER))

    # --- the worker branch, cut before any of that -------------------------
    _git(repo, "checkout", "-q", "agent/side")
    _dirs(home)
    _item(home, ID)                     # the same item, on the other side
    (repo / "side-note.txt").write_text("unrelated work\n", encoding="utf-8")
    _commit(repo, "side: work that has nothing to do with the board")

    # --- the merge ---------------------------------------------------------
    _git(repo, "checkout", "-q", "main")
    _dirs(home)
    rc, out = _git(repo, "merge", "--no-edit", "agent/side", check=False)
    assert rc == 0, "this reproduction is meant to be a *clean* merge:\n" + out
    _dirs(home)
    return repo, home


def test_a_real_git_merge_puts_a_delivered_item_back_on_the_shelf(tmp_path):
    """The fixture's own assertion, before `board` is involved at all.

    If this ever stops being true the rest of the file is testing a fiction,
    and it should fail here rather than quietly pass everywhere else.
    """
    repo, home = _repo_with_merge_resurrection(tmp_path)
    assert (home / "board" / "items" / ("%s.md" % ID)).exists(), \
        "git did not resurrect the item -- this fixture no longer reproduces S34"
    assert (home / "board" / "done" / ("%s.%s.md" % (ID, DELIVERER))).exists()
    # And it is a committed fact, not a working-tree accident.
    _, tracked = _git(repo, "ls-files", "monitor/board")
    assert "monitor/board/items/%s.md" % ID in tracked
    assert "monitor/board/done/%s.%s.md" % (ID, DELIVERER) in tracked


def test_the_naive_merge_story_does_not_reproduce_it(tmp_path):
    """The story everybody tells first is wrong, and it matters that it is.

    "Item on the shelf, branch off, master claims and delivers, merge the
    branch back" does **not** resurrect anything: git's three-way merge lets a
    deletion on one side beat an unmodified file on the other, and if the
    branch *edits* the item, rename detection carries the edit onto
    `done/<id>.<worker>.md` instead.

    Pinned as a test because the next person to simplify the fixture above will
    reach for exactly this shape, get a green suite that reproduces nothing,
    and conclude S34 was never real.
    """
    repo = tmp_path / "naive"
    home = repo / "monitor"
    _dirs(home)
    _git(repo, "init", "-q", "-b", "main")
    _item(home, ID)
    _commit(repo, "base with the item on the shelf")
    _git(repo, "branch", "agent/side")

    os.rename(str(home / "board" / "items" / ("%s.md" % ID)),
              str(home / "board" / "done" / ("%s.%s.md" % (ID, DELIVERER))))
    _commit(repo, "delivered")

    _git(repo, "checkout", "-q", "agent/side")
    _dirs(home)
    (repo / "side-note.txt").write_text("unrelated\n", encoding="utf-8")
    _commit(repo, "side")
    _git(repo, "checkout", "-q", "main")
    _dirs(home)
    rc, out = _git(repo, "merge", "--no-edit", "agent/side", check=False)
    assert rc == 0, out
    _dirs(home)
    assert not (home / "board" / "items" / ("%s.md" % ID)).exists(), \
        "if this ever starts resurrecting, the guard's story needs rewriting"
    assert (home / "board" / "done" / ("%s.%s.md" % (ID, DELIVERER))).exists()


def test_a_sweep_on_a_branch_resurrects_it_as_a_merge_conflict(tmp_path):
    """The second real route, and the one that arrives wearing a warning label.

    A branch cut while the item was under claim runs `sweep` (or `release`),
    moving `claimed/<id>.<w>.md` back to `items/<id>.md`; master meanwhile runs
    `done`, moving the same file to `done/`. git sees one file renamed to two
    different places and stops -- but it stops with **both** paths in the
    working tree, so every "resolve by keeping both sides" resolution commits
    the resurrection. That is the shape of this repo's recorded board
    conflicts.
    """
    repo = tmp_path / "sweepconflict"
    home = repo / "monitor"
    _dirs(home)
    _git(repo, "init", "-q", "-b", "main")
    _claimed(home, ID, DELIVERER)
    _commit(repo, "base: the item is under claim")
    _git(repo, "branch", "agent/side")

    os.rename(str(home / "board" / "claimed" / ("%s.%s.md" % (ID, DELIVERER))),
              str(home / "board" / "done" / ("%s.%s.md" % (ID, DELIVERER))))
    _commit(repo, "DONE %s by %s" % (ID, DELIVERER))

    _git(repo, "checkout", "-q", "agent/side")
    _dirs(home)
    os.rename(str(home / "board" / "claimed" / ("%s.%s.md" % (ID, DELIVERER))),
              str(home / "board" / "items" / ("%s.md" % ID)))
    _commit(repo, "SWEEP %s released" % ID)

    _git(repo, "checkout", "-q", "main")
    _dirs(home)
    rc, out = _git(repo, "merge", "--no-edit", "agent/side", check=False)
    assert rc != 0 and "rename/rename" in out, out
    _dirs(home)
    # The conflict left both paths on disk. Resolving it the usual way -- keep
    # what is there, commit -- is what publishes the resurrection.
    assert (home / "board" / "items" / ("%s.md" % ID)).exists()
    assert (home / "board" / "done" / ("%s.%s.md" % (ID, DELIVERER))).exists()


# --------------------------- (a) what the board did with that tree, before ---

def test_before_the_fix_the_merged_back_item_is_handed_straight_out(
        tmp_path, monkeypatch):
    """The pre-fix `candidates()`, reconstructed rather than imagined.

    The old code called `done_ids()` and used the result for exactly one thing:
    dropping items whose `deps` were not yet delivered. Blanking that set is
    therefore behaviourally identical to the old code *for an item with*
    ``deps: none`` -- and it removes the new guard's only input. What comes
    back is the pre-fix answer.
    """
    repo, home = _repo_with_merge_resurrection(tmp_path)
    _point(home, monkeypatch)
    monkeypatch.setattr(board, "done_ids", lambda: set())
    assert ID in [iid for _p, iid, _f, _m in board.candidates()], \
        "the pre-fix board did offer it; if it does not, this fixture is wrong"


def test_the_mechanism_is_a_done_record_and_a_shelf_entry_at_once(
        tmp_path, monkeypatch):
    """The exact combination the old `candidates()` never tested."""
    repo, home = _repo_with_merge_resurrection(tmp_path)
    _point(home, monkeypatch)
    assert ID in board.done_ids()
    assert (home / "board" / "items" / ("%s.md" % ID)).exists()
    assert board.delivered_map()[ID] == DELIVERER


# ------------------------------------ (b) what it does with that tree, after --

def test_after_the_fix_the_merged_back_item_is_not_offered(tmp_path,
                                                           monkeypatch):
    """The one that goes red if the skip in `candidates()` is deleted."""
    repo, home = _repo_with_merge_resurrection(tmp_path)
    _point(home, monkeypatch)
    assert ID not in [iid for _p, iid, _f, _m in board.candidates()]


def test_after_the_fix_claiming_it_fails_and_leaves_it_where_it_is(
        tmp_path, monkeypatch, capsys):
    repo, home = _repo_with_merge_resurrection(tmp_path)
    _point(home, monkeypatch)
    assert board.cmd_claim("W-1671") == 3
    capsys.readouterr()
    assert (home / "board" / "items" / ("%s.md" % ID)).exists(), \
        "a refused claim must not move the file either"
    assert not (home / "board" / "claimed" / ("%s.W-1671.md" % ID)).exists()


# ---------------------------------------------------- (c) and (d) reconcile --

def test_reconcile_reports_it_and_returns_non_zero(tmp_path, monkeypatch,
                                                   capsys):
    """Report-only by default. A board-repair tool that mutates on sight is one
    nobody dares run, and this one has to be runnable after every merge."""
    repo, home = _repo_with_merge_resurrection(tmp_path)
    _point(home, monkeypatch)
    rc = board.cmd_reconcile()
    out = capsys.readouterr().out
    assert rc != 0
    assert ID in out and "would remove" in out
    assert "items/%s.md" % ID in out
    # and it really did nothing
    assert (home / "board" / "items" / ("%s.md" % ID)).exists()
    assert (home / "board" / "done" / ("%s.%s.md" % (ID, DELIVERER))).exists()
    assert not (home / "board" / "board.log").exists()


def test_reconcile_fix_removes_the_residue_and_keeps_the_done_record(
        tmp_path, monkeypatch, capsys):
    repo, home = _repo_with_merge_resurrection(tmp_path)
    _point(home, monkeypatch)
    done_file = home / "board" / "done" / ("%s.%s.md" % (ID, DELIVERER))
    before = done_file.read_text(encoding="utf-8")

    assert board.cmd_reconcile(fix=True) == 0
    capsys.readouterr()

    assert not (home / "board" / "items" / ("%s.md" % ID)).exists()
    assert done_file.exists(), "done/ is the authority; it must survive"
    assert done_file.read_text(encoding="utf-8") == before, \
        "the delivered record must come out byte-identical"


def test_reconcile_fix_writes_a_reconcile_line_to_the_board_log(
        tmp_path, monkeypatch, capsys):
    """The manual repair on 2026-07-29 was recorded by hand as `RECONCILE`.
    A repair nobody can find afterwards reads later as the work vanishing."""
    repo, home = _repo_with_merge_resurrection(tmp_path)
    _point(home, monkeypatch)
    board.cmd_reconcile(fix=True)
    capsys.readouterr()
    log = (home / "board" / "board.log").read_text(encoding="utf-8")
    assert "RECONCILE %s" % ID in log
    assert DELIVERER in log
    assert "items/%s.md" % ID in log


def test_after_the_fix_resurrected_is_empty(tmp_path, monkeypatch, capsys):
    repo, home = _repo_with_merge_resurrection(tmp_path)
    _point(home, monkeypatch)
    assert board.resurrected()
    board.cmd_reconcile(fix=True)
    capsys.readouterr()
    assert board.resurrected() == {}
    assert board.cmd_reconcile() == 0        # clean, second run is a no-op
    assert "RECONCILE-CLEAN" in capsys.readouterr().out


def test_reconcile_also_clears_a_resurrected_claim(tmp_path, monkeypatch,
                                                   capsys):
    """A13 came back into `claimed/`, not `items/` -- both residues count."""
    home = _fleet(tmp_path, monkeypatch)
    _done(home, "A13-sealed-audit", "RES-4")
    _claimed(home, "A13-sealed-audit", "RES-4")
    assert board.resurrected()["A13-sealed-audit"]["claimed_by"] == ["RES-4"]
    assert board.cmd_reconcile(fix=True) == 0
    capsys.readouterr()
    assert not (home / "board" / "claimed" / "A13-sealed-audit.RES-4.md").exists()
    assert (home / "board" / "done" / "A13-sealed-audit.RES-4.md").exists()


# =========================================================================
# 2. sweep must not put delivered work back on the shelf
# =========================================================================

def test_sweep_keeps_a_delivered_claim_instead_of_re_shelving_it(
        tmp_path, monkeypatch, capsys):
    """The more damaging of the two routes, because it looks like housekeeping.

    `E8-ic3-scale` was swept back to `items/` three separate times *after* it
    was delivered, and each of those sweeps is indistinguishable in the log
    from the honest ones on either side of it.
    """
    home = _fleet(tmp_path, monkeypatch)
    _claimed(home, ID, "W-9911")
    _done(home, ID, DELIVERER)

    assert board.cmd_sweep() == 0
    out = capsys.readouterr().out

    assert (home / "board" / "claimed" / ("%s.W-9911.md" % ID)).exists()
    assert not (home / "board" / "items" / ("%s.md" % ID)).exists(), \
        "sweep put delivered work back on the shelf"
    assert "KEPT" in out and ID in out
    assert "freed" not in out


def test_sweep_still_frees_an_orphaned_claim_with_no_done_record(
        tmp_path, monkeypatch, capsys):
    """The positive control. A guard that stopped sweep doing its actual job
    would trade one silent failure for another: dead workers' claims lock a
    territory, and that is the reason sweep exists."""
    home = _fleet(tmp_path, monkeypatch)
    _claimed(home, "X1-orphan", "W-9912", territory="docs")

    assert board.cmd_sweep() == 0
    out = capsys.readouterr().out

    assert not (home / "board" / "claimed" / "X1-orphan.W-9912.md").exists()
    assert (home / "board" / "items" / "X1-orphan.md").exists()
    assert "freed from" in out and "X1-orphan" in out


def test_sweep_judges_the_two_claims_separately_in_one_run(tmp_path,
                                                           monkeypatch, capsys):
    """Both verdicts in a single sweep: the whole judgement, side by side."""
    home = _fleet(tmp_path, monkeypatch)
    _claimed(home, ID, "W-9911", territory="engine-rig")
    _done(home, ID, DELIVERER)
    _claimed(home, "X1-orphan", "W-9912", territory="docs")

    board.cmd_sweep()
    capsys.readouterr()

    assert (home / "board" / "claimed" / ("%s.W-9911.md" % ID)).exists()
    assert not (home / "board" / "items" / ("%s.md" % ID)).exists()
    assert not (home / "board" / "claimed" / "X1-orphan.W-9912.md").exists()
    assert (home / "board" / "items" / "X1-orphan.md").exists()


def test_the_kept_claim_is_not_written_to_the_board_log_as_a_release(
        tmp_path, monkeypatch, capsys):
    home = _fleet(tmp_path, monkeypatch)
    _claimed(home, ID, "W-9911")
    _done(home, ID, DELIVERER)
    board.cmd_sweep()
    capsys.readouterr()
    log_path = home / "board" / "board.log"
    log = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
    assert "SWEEP %s released" % ID not in log


# =========================================================================
# 3. visibility -- a silent skip is only half a fix
# =========================================================================

def test_list_prints_a_resurrected_section_naming_id_and_deliverer(
        tmp_path, monkeypatch, capsys):
    """Skipping it silently would swap one failure for its mirror image: the
    board would hide finished items instead of offering them, and nobody would
    learn that a merge did it."""
    repo, home = _repo_with_merge_resurrection(tmp_path)
    _point(home, monkeypatch)
    board.cmd_list()
    out = capsys.readouterr().out
    assert "RESURRECTED" in out
    assert ID in out
    assert DELIVERER in out, "who delivered it is the whole lead for the reader"
    assert "reconcile" in out, "say what to run about it"


def test_board_empty_says_what_the_merge_took_away(tmp_path, monkeypatch,
                                                   capsys):
    """A worker told BOARD-EMPTY while a finished item sits in `items/` is
    looking at a board lying to it in the reassuring direction, and it is the
    one party with a reason to say so."""
    repo, home = _repo_with_merge_resurrection(tmp_path)
    _point(home, monkeypatch)
    assert board.cmd_claim("W-1671") == 3
    out = capsys.readouterr().out
    assert "BOARD-EMPTY" in out
    assert "RESURRECTED" in out
    assert ID in out and DELIVERER in out


def test_a_clean_board_prints_no_resurrected_section(tmp_path, monkeypatch,
                                                     capsys):
    """The negative sample that keeps the section worth reading. A banner on
    every `list` is a banner nobody sees."""
    home = _fleet(tmp_path, monkeypatch)
    _item(home, "A1-ordinary")
    _done(home, "Z9-long-finished", "W-1")
    board.cmd_list()
    assert "RESURRECTED" not in capsys.readouterr().out


def test_the_warning_survives_this_host_s_console_encoding(tmp_path,
                                                           monkeypatch, capsys):
    """cp936 here. A glyph outside it raises `UnicodeEncodeError` at print
    time -- which for `cmd_claim` would mean a traceback *after* the rename,
    the same trap `prior_work` already fell into once."""
    home = _fleet(tmp_path, monkeypatch)
    _item(home, ID)
    _done(home, ID, DELIVERER)
    board._warn_resurrected()
    board.cmd_reconcile()
    out = capsys.readouterr().out
    assert out.strip()
    out.encode("cp936")


# =========================================================================
# 4. negative controls -- what must not change
# =========================================================================

def test_an_ordinary_available_item_is_still_claimable(tmp_path, monkeypatch,
                                                       capsys):
    """Without this, a board that withheld everything from everybody would
    satisfy every other assertion in this file."""
    home = _fleet(tmp_path, monkeypatch)
    _item(home, "A1-ordinary")
    assert board.cmd_claim("W-9") == 0
    capsys.readouterr()
    assert (home / "board" / "claimed" / "A1-ordinary.W-9.md").exists()


def test_done_ids_still_unblocks_an_item_whose_deps_are_delivered(
        tmp_path, monkeypatch):
    """`done_ids()`'s original and only job. The guard reuses the same set, so
    a mistake in it would take dependency resolution down with it -- and that
    failure is silent: the dependent item just never appears."""
    home = _fleet(tmp_path, monkeypatch)
    _done(home, "C1-worldgen", "W-1")
    _item(home, "C2-depends", deps="C1-worldgen")
    assert "C2-depends" in [iid for _p, iid, _f, _m in board.candidates()]


def test_an_item_whose_deps_are_not_delivered_is_still_blocked(tmp_path,
                                                               monkeypatch):
    home = _fleet(tmp_path, monkeypatch)
    _item(home, "C2-depends", deps="C1-worldgen")
    assert board.candidates() == []


def test_an_ordinary_done_record_is_not_reported_as_resurrected(tmp_path,
                                                                monkeypatch):
    """The check must not fire on the 100+ honest records in `done/`.

    If it did, `list` would open with a hundred-line false alarm and
    `reconcile --fix` would delete nothing while claiming to -- but the banner
    would be ignored from the first day, which is the expensive part.
    """
    home = _fleet(tmp_path, monkeypatch)
    for i in range(5):
        _done(home, "D%d-finished" % i, "W-%d" % i)
    _item(home, "A1-ordinary")
    assert board.resurrected() == {}
    assert "A1-ordinary" in [iid for _p, iid, _f, _m in board.candidates()]


def test_a_delivered_id_does_not_suppress_one_that_extends_its_name(
        tmp_path, monkeypatch):
    """`S4-freeze` and `S4-freeze-complete` both exist on the real board, and
    `done_ids()` derives ids with `f.split(".")[0]`. A prefix match instead of
    an exact one would strand the follow-up item permanently and silently."""
    home = _fleet(tmp_path, monkeypatch)
    _done(home, "S4-freeze", "RES-1")
    _item(home, "S4-freeze-complete", territory="monitor")
    assert board.resurrected() == {}
    assert "S4-freeze-complete" in [iid for _p, iid, _f, _m
                                    in board.candidates()]


def test_the_prefix_check_holds_in_the_other_direction_too(tmp_path,
                                                           monkeypatch):
    """Delivering the longer name must not suppress the shorter one either."""
    home = _fleet(tmp_path, monkeypatch)
    _done(home, "S4-freeze-complete", "RES-1")
    _item(home, "S4-freeze", territory="monitor")
    assert board.resurrected() == {}
    assert "S4-freeze" in [iid for _p, iid, _f, _m in board.candidates()]


def test_a_doubled_cell_prefix_id_round_trips(tmp_path, monkeypatch):
    """`P13-P13-figure-numbering-and-plates` is a real id: the cell prefix got
    written twice. Any id-parsing that assumes one hyphen-delimited head would
    match the wrong thing here."""
    iid = "P13-P13-figure-numbering-and-plates"
    home = _fleet(tmp_path, monkeypatch)
    _done(home, iid, "RES-2")
    _item(home, iid)
    assert list(board.resurrected()) == [iid]
    assert board.delivered_map()[iid] == "RES-2"
    assert iid not in [i for _p, i, _f, _m in board.candidates()]


# Fixed after this file found it. `resurrected()` used to build its claim side
# from `claimed_map()`, a dict keyed on the id, so with two claim files for one
# id it kept only whichever `os.listdir` returned last -- and `--fix` removed
# one, printed "清掉 1 个残留" and returned **0** with the second still sitting
# there. A repair tool whose exit code says "clean" over residue it left is this
# lane's own disease, and a CI gate would have believed it. Two claims on one id
# is not the rare case either: it is a *more* resurrected board, because every
# resurrection is another chance for somebody to claim.
def test_reconcile_fix_clears_every_claim_on_a_delivered_id(tmp_path,
                                                            monkeypatch, capsys):
    home = _fleet(tmp_path, monkeypatch)
    _done(home, ID, DELIVERER)
    _claimed(home, ID, "W-1671")
    _claimed(home, ID, "W-130")
    rc = board.cmd_reconcile(fix=True)
    capsys.readouterr()
    left = sorted(os.listdir(str(home / "board" / "claimed")))
    assert (rc, left) == (0, []), \
        "--fix returned %d and left %s behind" % (rc, left)


def test_a_delivered_id_still_resolves_as_a_dependency_while_resurrected(
        tmp_path, monkeypatch):
    """The two roles of `done_ids()` at once: the resurrected item is withheld,
    and the item that *depends* on it is still unblocked. Conflating them would
    block the dependent work too -- turning a duplicated item into a stalled
    lane."""
    home = _fleet(tmp_path, monkeypatch)
    _done(home, "C1-worldgen", "W-1")
    _item(home, "C1-worldgen")                       # resurrected by a merge
    _item(home, "C2-depends", deps="C1-worldgen", territory="docs")
    offered = [iid for _p, iid, _f, _m in board.candidates()]
    assert "C1-worldgen" not in offered
    assert "C2-depends" in offered
