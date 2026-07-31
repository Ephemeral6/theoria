"""A manifest must say the same thing on every machine.

`backfill.build()` used to construct `files[]` from a raw `os.walk` of the run
directory, which made the manifest a function of the working tree rather than of
the repository. The consequence was measured on this branch, not imagined:
`20260729T004020Z-leg01` lists `candidates.jsonl` (201 MB, excluded because
GitHub refuses anything over 100) and `trace.jsonl` (excluded as large and
re-derivable from the ledger). On the machine that produced them, `build()` sees
them and `verify_provenance` check 8 is green. In a fresh worktree -- which is
exactly what `ci_merge` builds, so exactly what the merge queue ran -- `build()`
cannot see them, the re-derived list is shorter, and check 8 is red. The same
commit, checked by the same code, gave two different answers depending on whose
disk it ran on, and the queue retried the branch twenty times over 23.6 hours
against an answer no commit could have changed.

Two properties are pinned here:

* `_files_the_clone_carries` excludes what the repository excludes, and -- the
  half that is easy to lose -- keeps everything else;
* the exclusion is decided by `git check-ignore` rather than by a pattern list
  copied into this arm, so it cannot fall out of step with `.gitignore`.
"""

import json
import os
import shutil
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(HERE)
if ARM not in sys.path:
    sys.path.insert(0, ARM)

import _bootstrap                                     # noqa: E402,F401

from armtools import backfill                          # noqa: E402


def _git(args, cwd):
    return subprocess.run(["git"] + args, cwd=cwd, capture_output=True,
                          text=True, check=False)


def _write_gitignore(root, body):
    """Write `.gitignore` **and commit it**.

    Committing is not fixture hygiene, it is the property under test: a rule only
    counts when the file stating it is one a clone would carry, so a `.gitignore`
    no commit contains is correctly ignored by `_ignored_paths`. Leaving it
    untracked here made four tests fail in a way that looked like a regression
    and was actually the tightening working.

    It said `git add` until 2026-07-30, and that was the same defect one function
    over: staging is not shipping. Five tests were passing on a `.gitignore` that
    no clone would have had -- including, at the sharp end,
    `test_check_ten_catches_a_dangling_reference`, whose green half rested on it.
    """
    (root / ".gitignore").write_text(body, encoding="utf-8")
    _commit(root, ".gitignore")


@pytest.fixture
def repo(tmp_path):
    """A real git repository, because the thing under test asks git."""
    root = tmp_path / "repo"
    (root / "runs" / "somerun").mkdir(parents=True)
    _git(["init", "-q"], str(root))
    _write_gitignore(root, "runs/*/trace.jsonl\nruns/somerun/huge.jsonl\n")
    run_dir = root / "runs" / "somerun"
    for name in ("MANIFEST.json", "ledger.jsonl", "certify.json",
                 "trace.jsonl", "huge.jsonl"):
        (run_dir / name).write_text("{}\n", encoding="utf-8")
    return root, run_dir


def test_the_excluded_artefacts_are_left_out(repo):
    _root, run_dir = repo
    carried = backfill._files_the_clone_carries(str(run_dir))
    assert "trace.jsonl" not in carried
    assert "huge.jsonl" not in carried


def test_everything_the_repository_ships_is_still_listed(repo):
    """The positive control, and it carries most of the weight: a
    `_files_the_clone_carries` that returned `[]` would satisfy the test above
    while erasing the archive's file list entirely."""
    _root, run_dir = repo
    carried = backfill._files_the_clone_carries(str(run_dir))
    assert "certify.json" in carried
    assert "ledger.jsonl" in carried
    # MANIFEST.json is excluded by the walk itself -- a manifest does not list
    # itself -- and that predates this change.
    assert "MANIFEST.json" not in carried


def test_the_answer_does_not_depend_on_the_file_being_there(repo):
    """The property the whole change exists for.

    Delete the excluded artefacts, as a clone would never have had them, and the
    list must not move. If this fails, the manifest is still machine-dependent
    and check 8 still means something different on each disk.
    """
    _root, run_dir = repo
    before = backfill._files_the_clone_carries(str(run_dir))
    (run_dir / "trace.jsonl").unlink()
    (run_dir / "huge.jsonl").unlink()
    after = backfill._files_the_clone_carries(str(run_dir))
    assert before == after


def test_a_file_the_repository_does_ship_is_missed_when_it_is_absent(repo):
    """The negative control for the test above, and it is not redundant.

    "The list does not change when a file disappears" must hold for *excluded*
    artefacts only. A tracked file that goes missing is a real difference and
    must show up as one -- otherwise the previous test would also pass for an
    implementation that ignored the disk completely and returned a constant.
    """
    _root, run_dir = repo
    before = backfill._files_the_clone_carries(str(run_dir))
    (run_dir / "certify.json").unlink()
    after = backfill._files_the_clone_carries(str(run_dir))
    assert "certify.json" in before
    assert "certify.json" not in after


def test_the_rules_come_from_gitignore_and_not_from_a_copy_of_it(repo):
    """Add a rule to `.gitignore`; the traversal must follow without this arm
    being edited. A hardcoded pattern list would pass every other test here and
    then silently disagree with the repository the first time somebody excluded
    something new."""
    root, run_dir = repo
    assert "certify.json" in backfill._files_the_clone_carries(str(run_dir))
    _write_gitignore(
        root, "runs/*/trace.jsonl\nruns/somerun/huge.jsonl\nruns/*/certify.json\n")
    assert "certify.json" not in backfill._files_the_clone_carries(str(run_dir))


def test_many_paths_at_once_are_all_classified(repo):
    """Regression, and the reason it is here is worth keeping.

    The first draft batched the paths as newline-joined text with
    `subprocess.run(..., text=True)`. On Windows that translates `\\n` to
    `\\r\\n` on write, so git received `trace.jsonl\\r`, matched nothing, and
    reported that no path was ignored at all -- while the identical command
    typed into a shell reported both. A single-path test would not have caught
    it: with one path there is no separator to corrupt. This one passes several
    and checks the ones that are not last.
    """
    _root, run_dir = repo
    for i in range(5):
        (run_dir / ("pad%d.json" % i)).write_text("{}\n", encoding="utf-8")
    ignored = backfill._ignored_paths(
        str(run_dir),
        ["trace.jsonl", "huge.jsonl"] + ["pad%d.json" % i for i in range(5)])
    assert ignored == {"trace.jsonl", "huge.jsonl"}


def test_no_git_at_all_fails_towards_listing_the_file(tmp_path):
    """A directory that is not a repository. `git check-ignore` fails, and the
    function must return "nothing is excluded" rather than "everything is".

    The direction matters: failing towards *listing* a file shows up as drift in
    check 8, which is loud. Failing the other way would silently shorten the
    archive's file list, which is exactly the kind of quiet subtraction nobody
    notices.
    """
    lonely = tmp_path / "not-a-repo"
    lonely.mkdir()
    (lonely / "a.json").write_text("{}\n", encoding="utf-8")
    assert backfill._ignored_paths(str(lonely), ["a.json"]) == set()
    assert "a.json" in backfill._files_the_clone_carries(str(lonely))


def test_git_missing_from_the_machine_entirely_also_lists_the_file(monkeypatch,
                                                                   tmp_path):
    """The `OSError` branch, which the test above does *not* reach.

    That one runs in a directory that is not a repository: git is present, runs,
    exits non-zero and prints nothing, so the function returns the empty set by
    the ordinary path. The `except OSError` branch -- no git binary at all -- was
    left unmeasured, and a mutation that made it `return set(rel_paths)` (drop
    every file) passed the whole file. A docstring promising a fail-safe
    direction with no test behind it is the kind of claim this arm keeps finding
    in other people's code.
    """
    def no_git(*_args, **_kwargs):
        raise OSError(2, "No such file or directory: 'git'")

    monkeypatch.setattr(subprocess, "run", no_git)
    assert backfill._ignored_paths(str(tmp_path), ["a.json", "b.json"]) == set()


def test_a_tracked_file_is_listed_even_if_a_rule_matches_its_name(repo):
    """`--no-index` is not the hardening it looks like, and this pins why.

    `git check-ignore` reports a path as *not* ignored once it is in the index,
    because `.gitignore` has no power over a tracked path. That asymmetry is the
    behaviour this code wants -- the question is "does the repository ship this
    file", and a tracked file matching an ignore pattern is shipped. Measured on
    a scratch repository: a tracked `kept.json` against a `kept.json` rule gives
    rc=1 from plain `check-ignore` and rc=0 from `check-ignore --no-index`. So
    adding the flag would silently drop such a file from the archive's list, and
    would make check 10 accept a *tracked* file that had gone missing from the
    working tree as "explained by a rule".

    (`monitor/audit/DRIFT-20260730T0704Z-a-gitignore-rule-that-was-already-false-when-it-merged.md`
    is an independent audit of the same asymmetry, from the other direction: a
    rule that landed after the path it names was already tracked, and has been
    inert since.)
    """
    root, run_dir = repo
    _write_gitignore(
        root, "runs/*/trace.jsonl\nruns/somerun/huge.jsonl\nruns/*/certify.json\n")
    _git(["add", "-f", "runs/somerun/certify.json"], str(root))

    assert backfill._ignored_paths(str(run_dir), ["certify.json"]) == set()
    assert "certify.json" in backfill._files_the_clone_carries(str(run_dir))


def test_a_machine_local_exclude_does_not_count(repo):
    """`.git/info/exclude` is not in a clone, so it may not decide this.

    The hole this closes was in the first version of the fix, which is worth
    recording: `git check-ignore` honours `.git/info/exclude`,
    `core.excludesFile` and the per-user global ignore file, none of which a
    clone carries. An artefact excluded only by one of those would be dropped
    from `files[]` on this machine and listed in a clone -- exactly the
    machine-dependence the traversal change exists to remove, reintroduced by
    the mechanism meant to remove it. A rule counts only if the file stating it
    is tracked.
    """
    root, run_dir = repo
    (run_dir / "local_only.json").write_text("{}\n", encoding="utf-8")
    exclude = root / ".git" / "info"
    exclude.mkdir(parents=True, exist_ok=True)
    (exclude / "exclude").write_text("runs/somerun/local_only.json\n",
                                     encoding="utf-8")

    # git agrees it is ignored...
    raw = subprocess.run(["git", "check-ignore", "-z", "--stdin"],
                         input=b"local_only.json", cwd=str(run_dir),
                         capture_output=True, check=False)
    assert b"local_only.json" in raw.stdout, (
        "precondition: git must consider it ignored, or this test proves nothing")

    # ...and this arm does not, because no clone would.
    assert backfill._ignored_paths(str(run_dir), ["local_only.json"]) == set()
    assert "local_only.json" in backfill._files_the_clone_carries(str(run_dir))


def test_a_committed_gitignore_still_counts_after_that_tightening(repo):
    """Positive control for the test above, and it is essential: a
    `_rule_file_is_in_the_repository` that returned `False` unconditionally would
    satisfy that test while switching the whole traversal back to a raw walk.

    Named `_a_tracked_` until 2026-07-30, and it asserted `git add` was enough --
    so it pinned the defect below rather than the property. See
    `test_a_staged_gitignore_does_not_explain_anything`.
    """
    root, run_dir = repo
    _commit(root, ".gitignore")
    assert backfill._ignored_paths(str(run_dir), ["trace.jsonl"]) \
        == {"trace.jsonl"}


def test_a_staged_gitignore_does_not_explain_anything(tmp_path):
    """Staging is not shipping, and here that direction is the unsafe one.

    `paths_the_clone_ships` was moved from the index to `HEAD` because a
    `git add`-ed path reads as shipped while no clone carries it.
    `_rule_file_is_in_the_repository` had the identical defect one function over,
    and it matters more there: a rule counting means a missing artefact is
    *explained*, so a staged-only `.gitignore` turns a genuinely dangling path
    green. A reader with the clone has no `.gitignore` at all, so no
    `git check-ignore` they could run explains anything.

    Built to this repository's own convention -- `git commit <paths>`, which is
    exactly the operation that leaves a staged file out of the commit.
    """
    root = tmp_path / "repo"
    run_dir = root / "runs" / "somerun"
    run_dir.mkdir(parents=True)
    _git(["init", "-q"], str(root))
    (run_dir / "kept.json").write_text("{}\n", encoding="utf-8")
    _commit(root, "runs/somerun/kept.json")

    (root / ".gitignore").write_text("runs/*/trace.jsonl\n", encoding="utf-8")
    _git(["add", "-f", ".gitignore"], str(root))          # staged, never committed

    # Precondition, or this test would pass for the wrong reason: git itself
    # says the path is ignored, and the index says the rule file is there.
    raw = subprocess.run(["git", "check-ignore", "-z", "--stdin"],
                         input=b"trace.jsonl", cwd=str(run_dir),
                         capture_output=True, check=False)
    assert b"trace.jsonl" in raw.stdout
    assert _git(["ls-files", "--error-unmatch", ".gitignore"],
                str(root)).returncode == 0

    assert backfill._ignored_paths(str(run_dir), ["trace.jsonl"]) == set(), (
        "a .gitignore no commit contains explained a missing artefact")

    # ...and committing that same file makes it count, or the tightening is
    # just "no rule ever counts".
    #
    # The cache has to be dropped by hand here, and the reason is worth knowing
    # rather than working around silently: `_RULE_FILE_CACHE` is keyed on
    # `(run_dir, source)` and its docstring's licence is that whether a rule file
    # is in the repository does not change inside one process. That holds for one
    # `verify_provenance.run()`; it does not hold for a test that commits between
    # two calls, which is exactly what this second half is.
    backfill._RULE_FILE_CACHE.clear()
    _commit(root, ".gitignore")
    assert backfill._ignored_paths(str(run_dir), ["trace.jsonl"]) \
        == {"trace.jsonl"}


# ------------------------------------------------------ check 10, and its bite
#: The name check 10 registers itself under. Written out here rather than
#: imported for `test_desk_sealing.py`'s stated reason: a test that reads its
#: expectation out of the code under test asserts that the code equals itself.
CHECK_TEN = ("every file a shipped manifest lists is shipped too or excluded "
             "by the repository's own rules")


def _commit(root, *rel_paths):
    """`git add` **and commit** -- staging is not shipping.

    Check 10 asks `git ls-tree HEAD`, so a fixture that only stages its
    artefacts describes a state no clone is ever in, and every test built on one
    would assert the opposite of the property. Identity is passed on the command
    line rather than configured: a headless machine may have no `user.email`,
    and a commit that silently fails to happen is the one failure mode these
    fixtures cannot survive -- so the result is asserted, not hoped for.

    **Pathspec on the `commit`, not just on the `add`.** Without it this commits
    the whole index, which would sweep up the deliberately-staged-never-committed
    file that `test_check_ten_asks_the_commit_not_the_disk` sets up -- silently
    turning the one assertion that distinguishes the index from the commit into
    a tautology. `--allow-empty` because a fixture may commit the same manifest
    twice on purpose (measured: git accepts both together and still restricts
    the commit to the pathspec).
    """
    if rel_paths:
        add = _git(["add", "-f", "--"] + list(rel_paths), str(root))
        assert add.returncode == 0, add.stderr
    done = _git(["-c", "user.email=fixture@example.invalid",
                 "-c", "user.name=fixture",
                 "commit", "-q", "--allow-empty", "-m", "fixture", "--"]
                + list(rel_paths), str(root))
    assert done.returncode == 0, done.stderr


def _archive_material_run(run_dir):
    """The minimum that makes `backfill.classify` call a directory archive
    material -- which is the minimum that makes any check in
    `verify_provenance` look at it.

    A ledger with a `run_start` naming a **non-loopback** upstream. Without a
    ledger the directory classifies as `process_record`; with a `127.0.0.1`
    upstream it classifies as `mock`. Both are skipped by every check, so a
    fixture in either state makes its test assert nothing.
    """
    from proxy.ledger import LEDGER_VERSION             # noqa: PLC0415

    (run_dir / "ledger.jsonl").write_text(
        json.dumps({"v": LEDGER_VERSION, "event": "run_start",
                    "run_id": "r-fixture", "arm": "theoria",
                    "ts": "2026-07-30T00:00:00Z",
                    "env_upstream": "https://three.arcprize.org"}) + "\n",
        encoding="utf-8")


def test_check_ten_catches_a_dangling_reference(tmp_path, monkeypatch):
    """A manifest listing a file that is neither present nor excluded.

    This is the case check 8 structurally cannot see: an `amend` manifest goes
    through `amend_payload`, which never looks at `files[]`. Three archived
    manifests list a `trace.jsonl` that exists nowhere in this repository and
    check 8 passes all three. Check 10 is what notices -- but only if it really
    distinguishes "absent and explained" from "absent and dangling", which is
    what this asserts in both directions.

    **Rewritten after an adversarial pass killed the first version.** That one
    built a local `dangling_for()` that reimplemented check 10's body inline --
    `absent = [...]`, `explained = backfill._ignored_paths(...)`, the set
    difference -- and asserted against the copy. It imported
    `verify_provenance` and then never called it. Measured consequence:
    replacing check 10's `for row in survey:` with `for row in []:`, so that
    the check is structurally incapable of failing, left the whole suite at
    272 passed.

    That is exactly the defect I had named two sections earlier in the same
    leg's run record -- a test that reads its expectation out of the code under
    test asserts that the code equals itself -- committed in the very change
    that named it. So this calls `run()` and reads the check's own verdict.
    """
    from armtools import armversion, verify_provenance   # noqa: PLC0415

    # Check 8 calls `armversion.scan()`, which walks every ref in a repository
    # that currently carries 266 worktrees: 136 seconds, measured. Three
    # `run()` calls would put seven minutes into the suite, and a suite nobody
    # runs is the failure mode this file exists to avoid. Stubbed here -- an
    # unrelated check, not the one under test. Check 8's own verdict goes
    # unread below; only check 10's row is asserted on.
    monkeypatch.setattr(armversion, "scan", lambda *a, **k: {})

    root = tmp_path / "repo"
    runs_root = root / "runs"
    run_dir = runs_root / "somerun"
    run_dir.mkdir(parents=True)
    _git(["init", "-q"], str(root))
    _write_gitignore(root, "runs/*/trace.jsonl\n")
    (run_dir / "certify.json").write_text("{}\n", encoding="utf-8")
    # Committed, not merely written or staged. Check 10 asks the commit rather
    # than the disk (see `test_check_ten_asks_the_commit_not_the_disk`), so an
    # untracked file here would be correctly reported as dangling and the green
    # half of this test would prove nothing about explanation.
    _archive_material_run(run_dir)
    _commit(root, "runs/somerun/certify.json")

    def verdict(*paths):
        """Check 10's own row, from a real `run()` over this tree.

        The manifest is **committed** each time: check 10 reads it out of
        `HEAD`, so writing it to the disk alone would leave every call reading
        whatever the previous one committed.
        """
        (run_dir / "MANIFEST.json").write_text(
            json.dumps({"files": [{"path": p, "sha256": "x"} for p in paths]}),
            encoding="utf-8")
        _commit(root, "runs/somerun/MANIFEST.json")
        rows = [r for r in verify_provenance.run(str(runs_root)).rows
                if r["check"] == CHECK_TEN]
        assert len(rows) == 1, "check 10 did not run at all: %r" % rows
        return rows[0]

    # present -> green
    assert verdict("certify.json")["ok"] is True
    # absent but named by a .gitignore rule that says why -> green
    assert verdict("certify.json", "trace.jsonl")["ok"] is True

    # absent and unexplained -> RED, and the path is named in the detail so a
    # reader is told which one rather than only that something is wrong.
    red = verdict("certify.json", "gone.json")
    assert red["ok"] is False, "check 10 passed a dangling reference"
    assert "gone.json" in red["detail"]
    assert "certify.json" not in red["detail"], (
        "the detail blames a path that is present")


def _check_ten_row(runs_root, monkeypatch):
    """Check 10's own row from a real `run()`. `armversion.scan` stubbed for the
    reason given in `test_check_ten_catches_a_dangling_reference`: it is check
    8's, unrelated here, and it costs 136 seconds against this repository."""
    from armtools import armversion, verify_provenance   # noqa: PLC0415

    monkeypatch.setattr(armversion, "scan", lambda *a, **k: {})
    rows = [r for r in verify_provenance.run(str(runs_root)).rows
            if r["check"] == CHECK_TEN]
    assert len(rows) == 1, "check 10 did not run at all: %r" % rows
    return rows[0]


def test_check_ten_asks_the_commit_not_the_disk(tmp_path, monkeypatch):
    """The repair for H3, in all three directions.

    Check 10 was written to end a defect -- "the same commit gets two answers on
    two machines" -- and its first predicate was `os.path.exists`, which has that
    defect. A file present in the run directory but tracked nowhere passed here
    and dangled in every clone, so the check policing machine-dependence was
    machine-dependent by the same mechanism, one file away from the code it was
    policing.

    Three cases, and each one killed a version of the fix:

    * present but committed nowhere -> RED. It is not in the clone.
    * committed but deleted from this working tree -> GREEN. It **is** in the
      clone; the disk being short of it is this machine's business. A fix that
      demanded both committed *and* present would keep the machine-dependence
      and merely add a condition.
    * `git add`-ed and never committed -> RED, and this is the one the second
      version got wrong. It asked the **index**, where a staged path reads as
      shipped while no clone has a copy. That is not a theoretical gap here:
      this repository's convention is `git commit <paths>` rather than
      `commit -a` (CLAUDE.md forbids `git add -A` at the root), which is exactly
      the operation that leaves staged paths out of the commit.
    """
    root = tmp_path / "repo"
    runs_root = root / "runs"
    run_dir = runs_root / "somerun"
    run_dir.mkdir(parents=True)
    _git(["init", "-q"], str(root))
    _archive_material_run(run_dir)
    (run_dir / "kept.json").write_text("{}\n", encoding="utf-8")
    (run_dir / "stray.json").write_text("{}\n", encoding="utf-8")
    (run_dir / "staged.json").write_text("{}\n", encoding="utf-8")
    _commit(root, "runs/somerun/kept.json")
    _git(["add", "-f", "runs/somerun/staged.json"], str(root))

    def verdict(*paths):
        (run_dir / "MANIFEST.json").write_text(
            json.dumps({"files": [{"path": p} for p in paths]}),
            encoding="utf-8")
        _commit(root, "runs/somerun/MANIFEST.json")
        return _check_ten_row(runs_root, monkeypatch)

    # Precondition, or the assertions below prove nothing: all three files are on
    # the disk, so `os.path.exists` -- the predicate this replaces -- passes all
    # three, and `staged.json` is in the index, so `git ls-files` passes it too.
    assert (run_dir / "kept.json").exists()
    assert (run_dir / "stray.json").exists()
    assert _git(["ls-files", "--error-unmatch", "runs/somerun/staged.json"],
                str(root)).returncode == 0

    assert verdict("kept.json")["ok"] is True

    red = verdict("kept.json", "stray.json")
    assert red["ok"] is False, ("a listed file that no clone would carry passed "
                               "because it happened to be on this disk")
    assert "stray.json" in red["detail"]
    assert "kept.json" not in red["detail"]

    red = verdict("kept.json", "staged.json")
    assert red["ok"] is False, ("a staged-never-committed file read as shipped; "
                                "the index is not the clone")
    assert "staged.json" in red["detail"]

    # ...and the other direction. Delete the committed one: a clone still has it.
    os.remove(str(run_dir / "kept.json"))
    assert verdict("kept.json")["ok"] is True, (
        "a committed artefact missing from this working tree was called "
        "dangling; the clone is the reference, not the disk")


def test_check_ten_rejects_a_path_that_is_not_of_this_run(tmp_path, monkeypatch):
    """An absolute path and a `..` escape both pass `os.path.exists`.

    `os.path.join(run_dir, "C:/Windows/win.ini")` throws the run directory away
    and returns the absolute path, which exists; `../../armtools/backfill.py`
    exists as well. Neither is an artefact of the run, and a manifest listing one
    is describing a file it does not own -- so it is reported as its own kind of
    fault, not silently folded into "dangling", because the reader needs to be
    told which of the two things went wrong.
    """
    root = tmp_path / "repo"
    runs_root = root / "runs"
    run_dir = runs_root / "somerun"
    run_dir.mkdir(parents=True)
    _git(["init", "-q"], str(root))
    _archive_material_run(run_dir)
    (run_dir / "kept.json").write_text("{}\n", encoding="utf-8")
    outside = root / "outside.json"
    outside.write_text("{}\n", encoding="utf-8")
    _commit(root, "runs/somerun/kept.json", "outside.json")

    def verdict(*paths):
        (run_dir / "MANIFEST.json").write_text(
            json.dumps({"files": [{"path": p} for p in paths]}),
            encoding="utf-8")
        _commit(root, "runs/somerun/MANIFEST.json")
        return _check_ten_row(runs_root, monkeypatch)

    escape = "../../outside.json"       # run_dir is `<root>/runs/somerun`
    # Precondition: it exists *and* is committed, so neither the old predicate
    # nor a naive shipped-set lookup against the repository root would object.
    assert os.path.exists(os.path.join(str(run_dir), escape))
    red = verdict("kept.json", escape)
    assert red["ok"] is False, "a path climbing out of the run directory passed"
    assert "not a path inside the run" in red["detail"]

    # Escapes that climb out and come back, which the single case above does not
    # discriminate. A mutation pass proved the gap: deleting the running-depth
    # guard from `path_is_inside_the_run` and keeping only its final check left
    # the whole suite green, because `../../outside.json` is the one input on
    # which the guarded and unguarded versions agree.
    for climbing in ("../x/y", "../a/../b/c", "../../../a/b/c/d"):
        red = verdict("kept.json", climbing)
        assert red["ok"] is False, "an escape that returns passed: %r" % climbing
        assert "not a path inside the run" in red["detail"]

    for absolute in (str(outside), "/etc/passwd", "C:/Windows/win.ini"):
        red = verdict("kept.json", absolute)
        assert red["ok"] is False, "an absolute path passed: %r" % absolute
        assert "not a path inside the run" in red["detail"]

    assert verdict("kept.json")["ok"] is True, (
        "the shape gate rejects an ordinary run-relative path")


def test_check_ten_has_no_answer_rather_than_a_green_when_git_cannot_be_asked(
        tmp_path, monkeypatch):
    """The third value, and why it is not folded into either verdict.

    A `runs/` tree outside any repository: git exits non-zero, so nothing can be
    said about what a clone would carry. The old predicate returned green here --
    the file is on the disk, and that was the whole question. The new one must
    not, and must also not report every listed path as dangling: that would be a
    red naming paths that are probably fine, which trains a reader to ignore it.

    This is the same shape as the reflex layer being quieter about a broken board
    than about an empty one: an unknown rendered as a known.
    """
    runs_root = tmp_path / "runs"                    # deliberately not a repo
    run_dir = runs_root / "somerun"
    run_dir.mkdir(parents=True)
    _archive_material_run(run_dir)
    (run_dir / "certify.json").write_text("{}\n", encoding="utf-8")
    (run_dir / "MANIFEST.json").write_text(
        json.dumps({"files": [{"path": "certify.json"}]}), encoding="utf-8")

    assert backfill.paths_the_clone_ships(str(run_dir)) is None
    row = _check_ten_row(runs_root, monkeypatch)
    assert row["ok"] is False, ("a tree where the question cannot be asked read "
                               "as green")
    assert "no answer" in row["detail"]
    assert "certify.json" not in row["detail"], (
        "the detail blames a path when the truth is that git could not be asked")


def test_check_ten_scope_is_the_shipped_manifest_not_archive_material(
        tmp_path, monkeypatch):
    """What check 10 looks at, in both directions -- this is H4's repair.

    Every *other* check in `verify_provenance` skips rows where
    `archive_material` is false, and check 10 inherited that filter, which made
    its name a lie: `20260729T080000Z-E14-crash-is-not-a-finding` has 23 listed
    paths that resolve nowhere relative to its run directory and was green
    because it has no ledger, so `classify` calls it a `process_record` and every
    check skips it. Measured at the changeover: 12 runs and 107 paths examined
    before, 35 runs and 161 after.

    So the filter is now "does this commit ship the manifest", and both halves
    need pinning, because the obvious way to widen the scope loses the second:

    * a `process_record` run -- no ledger, skipped by every other check -- **is**
      examined. A reader with only the clone can see its manifest, so its
      dangling paths are as real as any.
    * a run whose `MANIFEST.json` is not committed is **not** examined. That is
      what lets this check ask `HEAD` without calling every work-in-progress
      artefact dangling: the reader with only the clone cannot see that run
      either.
    """
    from armtools import backfill as bf                  # noqa: PLC0415

    root = tmp_path / "repo"
    runs_root = root / "runs"
    run_dir = runs_root / "somerun"
    run_dir.mkdir(parents=True)
    _git(["init", "-q"], str(root))
    (run_dir / "certify.json").write_text("{}\n", encoding="utf-8")
    (run_dir / "MANIFEST.json").write_text(
        json.dumps({"files": [{"path": "gone.json"}]}), encoding="utf-8")
    # No ledger on purpose: this is the state every other check skips.
    _commit(root, "runs/somerun/certify.json")

    rows = bf.survey(str(runs_root))
    assert [r["slug"] for r in rows] == ["somerun"]
    assert rows[0]["archive_material"] is False, (
        "precondition: this fixture must be the kind of run the old filter "
        "dropped, or the assertion below proves nothing")

    # Manifest not committed yet -> invisible, and the dangling path unreported.
    invisible = _check_ten_row(runs_root, monkeypatch)
    assert invisible["ok"] is True, invisible["detail"]
    assert "gone.json" not in invisible["detail"]
    assert "0 manifests" in invisible["detail"], (
        "the detail must say it looked at nothing, or a green here reads as "
        "coverage: %r" % invisible["detail"])

    # ...and the moment the manifest is shipped, the same run is in scope.
    _commit(root, "runs/somerun/MANIFEST.json")
    seen = _check_ten_row(runs_root, monkeypatch)
    assert seen["ok"] is False, (
        "a run with no ledger was skipped, which is how E14's 23 unresolvable "
        "paths stayed green")
    assert "gone.json" in seen["detail"]


def test_check_ten_reads_the_manifest_out_of_the_commit(tmp_path, monkeypatch):
    """Half a repair reads as a whole one.

    Asking git which paths this commit ships and then reading the *list* of them
    off the disk leaves the working tree deciding half the verdict: a manifest
    committed once and edited since is checked in its local form, while a clone
    checks a different document -- the same defect H3 was opened for, at the one
    input the first repair did not cover.

    Both directions, because a fix that simply refused to read the disk at all
    would pass the first assertion and be useless:

    * a local edit adding a dangling path does **not** turn the check red;
    * a dangling path that is genuinely in the committed manifest does.
    """
    root = tmp_path / "repo"
    runs_root = root / "runs"
    run_dir = runs_root / "somerun"
    run_dir.mkdir(parents=True)
    _git(["init", "-q"], str(root))
    _archive_material_run(run_dir)
    (run_dir / "kept.json").write_text("{}\n", encoding="utf-8")
    (run_dir / "MANIFEST.json").write_text(
        json.dumps({"files": [{"path": "kept.json"}]}), encoding="utf-8")
    _commit(root, "runs/somerun/kept.json", "runs/somerun/MANIFEST.json")
    assert _check_ten_row(runs_root, monkeypatch)["ok"] is True

    # Edited, not committed. No clone sees this, so no verdict may turn on it.
    (run_dir / "MANIFEST.json").write_text(
        json.dumps({"files": [{"path": "kept.json"}, {"path": "gone.json"}]}),
        encoding="utf-8")
    row = _check_ten_row(runs_root, monkeypatch)
    assert row["ok"] is True, (
        "an uncommitted local edit to a manifest decided the verdict: %r"
        % row["detail"])

    # Commit that same edit and it counts, or the check is reading nothing.
    _commit(root, "runs/somerun/MANIFEST.json")
    row = _check_ten_row(runs_root, monkeypatch)
    assert row["ok"] is False and "gone.json" in row["detail"], row["detail"]


def test_check_ten_holds_one_path_convention_per_manifest(tmp_path, monkeypatch):
    """A manifest's `files[]` are read under one convention, chosen once.

    Two conventions exist in this archive and both are real: `build()` writes
    run-relative paths, and E14's manifest writes repository-root-relative ones
    (`theoria-arm/runs/.../REPORT.md`, `a0-spike/pipeline/adapt.py`). Accepting
    both is therefore right; accepting both *within one manifest* is not, because
    then a wrong path passes by happening to match at the other root.

    The convention also decides **where the ignore rules are asked from**, and
    that is the half a reader would not think to test. `_ignored_paths` runs `git
    check-ignore` from the directory it is handed, so a root-relative path asked
    about from inside the run directory is a question about
    `<run>/theoria-arm/...` -- a path nobody wrote, matching no rule. Every
    unresolved path in a root-relative manifest was unexplainable by
    construction, which is a red with no available repair.
    """
    root = tmp_path / "repo"
    runs_root = root / "runs"
    run_dir = runs_root / "somerun"
    run_dir.mkdir(parents=True)
    _git(["init", "-q"], str(root))
    _archive_material_run(run_dir)
    (run_dir / "kept.json").write_text("{}\n", encoding="utf-8")
    (root / "elsewhere").mkdir()
    (root / "elsewhere" / "report.md").write_text("#\n", encoding="utf-8")
    # A rule at the root, naming an artefact the repository deliberately does not
    # ship. Written root-relative, because that is the convention of the manifest
    # that will list it.
    _write_gitignore(root, "elsewhere/*.bin\n")
    (root / "elsewhere" / "big.bin").write_text("x\n", encoding="utf-8")
    _commit(root, "runs/somerun/kept.json", "elsewhere/report.md", ".gitignore")

    def verdict(*paths):
        (run_dir / "MANIFEST.json").write_text(
            json.dumps({"files": [{"path": p} for p in paths]}),
            encoding="utf-8")
        _commit(root, "runs/somerun/MANIFEST.json")
        return _check_ten_row(runs_root, monkeypatch)

    # An all-root-relative manifest: E14's shape, and accepted.
    assert verdict("elsewhere/report.md")["ok"] is True

    # ...and its unshipped path is explainable, because the rule is asked from
    # the root the path is written against. Anchored at the run directory this
    # is red, and no edit to any `.gitignore` could have made it green.
    row = verdict("elsewhere/report.md", "elsewhere/big.bin")
    assert row["ok"] is True, (
        "a root-relative manifest's excluded artefact could not be explained: "
        "the ignore rules were asked from the wrong directory (%r)"
        % row["detail"])

    # Mixing is its own fault, and is named as such rather than folded into
    # "dangling", because the two call for different repairs.
    red = verdict("kept.json", "elsewhere/report.md")
    assert red["ok"] is False
    assert "mixes two path conventions" in red["detail"]
    assert "elsewhere/report.md" in red["detail"]


def test_check_ten_examines_a_run_this_disk_does_not_have(tmp_path, monkeypatch):
    """The scope is the commit's, not `os.listdir`'s.

    Every careful thing this check does inside the loop was defeated at the
    outermost one: the runs examined came from `backfill.survey`, which lists the
    working tree, so a run this commit ships whose directory is missing here --
    sparse checkout, partial clone, an `rm -rf` before a verify -- was skipped in
    silence. Same commit, opposite verdicts, and the **green** one was the
    machine short of data. Found by an adversarial pass, latent rather than live:
    no run in this archive is missing from the disk today.
    """
    root = tmp_path / "repo"
    runs_root = root / "runs"
    run_dir = runs_root / "somerun"
    run_dir.mkdir(parents=True)
    _git(["init", "-q"], str(root))
    _archive_material_run(run_dir)
    (run_dir / "kept.json").write_text("{}\n", encoding="utf-8")
    (run_dir / "MANIFEST.json").write_text(
        json.dumps({"files": [{"path": "kept.json"}, {"path": "gone.json"}]}),
        encoding="utf-8")
    _commit(root, "runs/somerun/kept.json", "runs/somerun/MANIFEST.json",
            "runs/somerun/ledger.jsonl")

    red = _check_ten_row(runs_root, monkeypatch)
    assert red["ok"] is False and "gone.json" in red["detail"]

    # Now delete the whole run directory. The commit is unchanged, so the answer
    # must be unchanged -- a clone still carries every one of those files.
    shutil.rmtree(str(run_dir))
    assert not run_dir.exists()
    still = _check_ten_row(runs_root, monkeypatch)
    assert still["ok"] is False, (
        "deleting the run directory made the check green; the set of runs "
        "examined is a working-tree input: %r" % still["detail"]
    )
    assert "gone.json" in still["detail"]
    assert still["detail"] == red["detail"], (
        "the verdict moved when only the disk moved")


def test_check_ten_reports_a_malformed_files_record_instead_of_crashing(
        tmp_path, monkeypatch):
    """One bad manifest must not take the other nine checks down with it.

    `files[]` was comprehended straight into strings, so an integer or a list
    where a path belonged raised `AttributeError` out of `run()` -- all ten
    checks destroyed, a traceback instead of a verdict, over a committed
    manifest a reader could see. And the quiet half: `{"path": ""}`,
    `{"path": null}` and a record with no `path` key were dropped without
    comment while the detail line went on reporting a path count, claiming
    coverage the check did not have.
    """
    root = tmp_path / "repo"
    runs_root = root / "runs"
    run_dir = runs_root / "somerun"
    run_dir.mkdir(parents=True)
    _git(["init", "-q"], str(root))
    _archive_material_run(run_dir)
    (run_dir / "kept.json").write_text("{}\n", encoding="utf-8")
    _commit(root, "runs/somerun/kept.json")

    def verdict(files):
        (run_dir / "MANIFEST.json").write_text(json.dumps({"files": files}),
                                               encoding="utf-8")
        _commit(root, "runs/somerun/MANIFEST.json")
        return _check_ten_row(runs_root, monkeypatch)

    # A bare string entry is a documented shape and still passes.
    assert verdict(["kept.json"])["ok"] is True
    # `./kept.json` is the same claim as `kept.json`, not a dangling one.
    assert verdict([{"path": "./kept.json"}])["ok"] is True

    for broken in (12, ["kept.json"], {"path": 12}, {"path": None},
                   {"path": ""}, {"sha256": "x"}):
        row = verdict([{"path": "kept.json"}, broken])
        assert row["ok"] is False, (
            "a files[] record with no usable path was dropped in silence: %r"
            % (broken,))
        assert "no usable path" in row["detail"]

    row = verdict({"kept.json": "x"})           # `files` itself is not a list
    assert row["ok"] is False and "not a list" in row["detail"]


def test_check_ten_does_not_count_a_gitlink_as_shipped(tmp_path, monkeypatch):
    """`ls-tree -r` lists submodule entries, and a plain clone leaves them empty.

    `--name-only` cannot tell a blob from a gitlink, so a manifest pointing into
    an uninitialised submodule read as "the clone ships it" while the reader with
    the clone gets an empty directory.
    """
    root = tmp_path / "repo"
    runs_root = root / "runs"
    run_dir = runs_root / "somerun"
    run_dir.mkdir(parents=True)
    _git(["init", "-q"], str(root))
    _archive_material_run(run_dir)
    (run_dir / "kept.json").write_text("{}\n", encoding="utf-8")
    (run_dir / "MANIFEST.json").write_text(
        json.dumps({"files": [{"path": "kept.json"}, {"path": "mod"}]}),
        encoding="utf-8")
    _commit(root, "runs/somerun/kept.json", "runs/somerun/MANIFEST.json")

    head = _git(["rev-parse", "HEAD"], str(root)).stdout.strip()
    added = _git(["update-index", "--add", "--cacheinfo",
                  "160000,%s,runs/somerun/mod" % head], str(root))
    assert added.returncode == 0, added.stderr
    _commit(root)                                # commits the whole index

    # Precondition: git does list it, so a name-only reading would accept it.
    names = _git(["ls-tree", "-r", "--name-only", "HEAD"], str(root)).stdout
    assert "runs/somerun/mod" in names

    row = _check_ten_row(runs_root, monkeypatch)
    assert row["ok"] is False, "a gitlink counted as a file the clone ships"
    assert "mod" in row["detail"]


def test_a_bare_top_level_filename_does_not_make_a_manifest_root_relative(
        tmp_path, monkeypatch):
    """The false green the two-conventions rule opened, and its price.

    Reading a manifest as root-relative because its paths happen to resolve at
    the root means one entry with an ordinary name is enough: a run that never
    had a `REPORT.md`, listing one, passed on the strength of the repository
    root's copy. A root-relative path must now name a directory to be in.

    The cost is asserted too, because it is real and should fail loudly rather
    than be discovered: a genuinely root-relative manifest listing a top-level
    file has that entry called dangling.
    """
    root = tmp_path / "repo"
    runs_root = root / "runs"
    run_dir = runs_root / "somerun"
    run_dir.mkdir(parents=True)
    _git(["init", "-q"], str(root))
    _archive_material_run(run_dir)
    (root / "REPORT.md").write_text("#\n", encoding="utf-8")
    (root / "elsewhere").mkdir()
    (root / "elsewhere" / "note.md").write_text("#\n", encoding="utf-8")
    _commit(root, "REPORT.md", "elsewhere/note.md")

    def verdict(*paths):
        (run_dir / "MANIFEST.json").write_text(
            json.dumps({"files": [{"path": p} for p in paths]}),
            encoding="utf-8")
        _commit(root, "runs/somerun/MANIFEST.json")
        return _check_ten_row(runs_root, monkeypatch)

    assert (run_dir / "REPORT.md").exists() is False
    red = verdict("REPORT.md")
    assert red["ok"] is False, (
        "a run that never had a REPORT.md passed on the repository root's copy")
    assert "REPORT.md" in red["detail"]
    assert "mixes two path conventions" not in red["detail"], (
        "the reader is pointed at the wrong repair")

    # ...and the shape this rule exists for still passes.
    assert verdict("elsewhere/note.md")["ok"] is True


def test_check_ten_is_actually_wired_into_the_run(tmp_path):
    """The check exists in `run()`'s output, not just as a function nobody calls.

    `test_the_archive_stays_accountable` pins the count at ten; this pins which
    ten, so that a rename or a silent removal is a failure rather than a
    renumbering.
    """
    from armtools import verify_provenance               # noqa: PLC0415

    names = [r["check"] for r in verify_provenance.run().rows]
    assert CHECK_TEN in names
    assert len(names) == len(set(names)), names
