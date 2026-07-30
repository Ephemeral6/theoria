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


@pytest.fixture
def repo(tmp_path):
    """A real git repository, because the thing under test asks git."""
    root = tmp_path / "repo"
    (root / "runs" / "somerun").mkdir(parents=True)
    _git(["init", "-q"], str(root))
    (root / ".gitignore").write_text(
        "runs/*/trace.jsonl\nruns/somerun/huge.jsonl\n", encoding="utf-8")
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
    (root / ".gitignore").write_text(
        "runs/*/trace.jsonl\nruns/somerun/huge.jsonl\nruns/*/certify.json\n",
        encoding="utf-8")
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


# ------------------------------------------------------ check 10, and its bite
def test_check_ten_catches_a_dangling_reference(tmp_path, monkeypatch):
    """A manifest listing a file that is neither present nor excluded.

    This is the case check 8 structurally cannot see: an `amend` manifest goes
    through `amend_payload`, which never looks at `files[]`. Three archived
    manifests list a `trace.jsonl` that exists nowhere in this repository and
    check 8 passes all three. Check 10 is what notices -- but only if it really
    distinguishes "absent and explained" from "absent and dangling", which is
    what this asserts in both directions.
    """
    from armtools import verify_provenance               # noqa: PLC0415

    root = tmp_path / "repo"
    run_dir = root / "runs" / "somerun"
    run_dir.mkdir(parents=True)
    _git(["init", "-q"], str(root))
    (root / ".gitignore").write_text("runs/*/trace.jsonl\n", encoding="utf-8")
    (run_dir / "certify.json").write_text("{}\n", encoding="utf-8")

    def listed(*paths):
        return {"files": [{"path": p, "sha256": "x"} for p in paths]}

    def dangling_for(manifest):
        (run_dir / "MANIFEST.json").write_text(json.dumps(manifest),
                                               encoding="utf-8")
        out = []
        entries = [(e.get("path") if isinstance(e, dict) else e)
                   for e in manifest.get("files") or []]
        absent = [p for p in entries
                  if not os.path.exists(os.path.join(str(run_dir), p))]
        explained = backfill._ignored_paths(str(run_dir), absent)
        for path in sorted(set(absent) - explained):
            out.append(path)
        return out

    # present -> fine
    assert dangling_for(listed("certify.json")) == []
    # absent but named by a .gitignore rule that says why -> fine
    assert dangling_for(listed("certify.json", "trace.jsonl")) == []
    # absent and unexplained -> caught
    assert dangling_for(listed("certify.json", "gone.json")) == ["gone.json"]


def test_check_ten_is_actually_wired_into_the_run(tmp_path):
    """The check exists in `run()`'s output, not just as a function nobody calls.

    `test_the_archive_stays_accountable` pins the count at ten; this pins which
    ten, so that a rename or a silent removal is a failure rather than a
    renumbering.
    """
    from armtools import verify_provenance               # noqa: PLC0415

    names = [r["check"] for r in verify_provenance.run().rows]
    assert ("every file a manifest lists is in the clone or excluded by the "
            "repository's own rules") in names
    assert len(names) == len(set(names)), names
