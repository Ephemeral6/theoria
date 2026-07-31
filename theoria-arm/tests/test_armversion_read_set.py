"""Which refs a provenance verdict is allowed to depend on.

`armversion.scan()` read `git rev-list --all`, so the input to every archived
provenance answer was "whatever is under `refs/` on this machine right now" --
a thing nobody declared and nobody controls. `backfill.provenance` copies
`locate()`'s whole reply, `commits` list and all, into `MANIFEST.json`, and
`verify_provenance` check 8 compares those manifests **byte for byte** on
re-derivation. So one ref appearing is not a cosmetic wobble in a diagnostic;
measured in `runs/20260731T1050Z-A17/`, splicing one extra commit into one
hash's group moves the bytes of 8 of the 8 archived manifests that carry a
`matched` or `ambiguous` verdict.

**Every test in this file that involves refs builds a real repository** --
`git init`, a real bare origin, real commits, real tags. The item is explicit
about that and it is not pedantry: `scan()` is three `git` subprocesses, and a
hand-rolled stub of git would only test the stub. The fixture is a few
kilobytes and a handful of commits, so the whole file runs in seconds.

The reverse control is the point of the file. It is easy to write a read set
that excludes tags and then only ever test that a tag *is* excluded -- which
would also pass if `scan()` returned nothing at all. So the controls run in
both directions:

* a tag on a commit the read set already reaches must change **nothing**;
* a branch pointing at an otherwise-unreachable commit must be **seen**, or
  the fix has bought stability by making false `no_match` accusations;
* a tag pointing at an otherwise-unreachable commit must be **excluded**, and
  the exclusion counter must **notice** it.
"""

from __future__ import annotations

import os
import subprocess

import pytest

from armtools import armversion

import _bootstrap


def _git(*args, cwd):
    proc = subprocess.run(["git", *args], cwd=cwd, capture_output=True,
                          encoding="utf-8", errors="replace")
    assert proc.returncode == 0, "git %s\n%s" % (" ".join(args), proc.stderr)
    return proc.stdout.strip()


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """A real repository with a real bare origin, and `scan()` pointed at it.

    Layout, after this returns:

        master   base -- mainline            (also pushed to origin)
        (loose)  base -- unique -- duplicate (reachable from no ref)

    `unique` carries an arm state that exists nowhere else. `duplicate` carries
    the same arm state as `mainline`. Between them they cover both ways a ref
    can change a verdict: `no_match -> matched` and `matched -> ambiguous`.
    """
    root = tmp_path / "fixture"
    work = root / "work"
    bare = root / "origin.git"
    root.mkdir()
    work.mkdir()
    _git("init", "--bare", "-b", "master", str(bare), cwd=str(root))
    _git("init", "-b", "master", str(work), cwd=str(root))
    _git("config", "user.email", "a17@test.invalid", cwd=str(work))
    _git("config", "user.name", "a17-test", cwd=str(work))
    _git("remote", "add", "origin", str(bare), cwd=str(work))

    arm = work / "theoria-arm"
    arm.mkdir()

    def commit(message, body):
        (arm / "mod.py").write_text(body, encoding="utf-8", newline="\n")
        _git("add", "-A", cwd=str(work))
        _git("commit", "-m", message, cwd=str(work))
        return _git("rev-parse", "HEAD", cwd=str(work))

    base = commit("base", "V = 1\n")
    mainline = commit("mainline", "V = 2\n")
    _git("push", "-q", "origin", "master", cwd=str(work))

    _git("checkout", "-q", "-b", "side", base, cwd=str(work))
    unique = commit("a unique arm state", "V = 99\n")
    duplicate = commit("the same arm state as mainline", "V = 2\n")
    _git("checkout", "-q", "master", cwd=str(work))
    _git("branch", "-q", "-D", "side", cwd=str(work))

    monkeypatch.setattr(_bootstrap, "REPO", str(work))
    return {"work": str(work), "base": base, "mainline": mainline,
            "unique": unique, "duplicate": duplicate}


def _hash_at(commit):
    return armversion.arm_version_at(commit)["sha256"]


def _verdict(sha, refs=None):
    table = (armversion.scan(refs) if refs is not None else armversion.scan())
    found = armversion.locate(sha, table)
    return found["verdict"], len(found["commits"])


# -- the read set is a declaration -----------------------------------------

def test_the_read_set_is_declared_rather_than_inherited():
    """`--all` is not a choice, it is the absence of one."""
    assert isinstance(armversion.DEFAULT_REFS, tuple)
    assert "--all" not in armversion.DEFAULT_REFS
    assert "--tags" not in armversion.DEFAULT_REFS
    assert armversion.DEFAULT_REFS == ("--branches", "--remotes", "HEAD")


def test_one_selector_as_a_string_still_means_one_token():
    """The widening must not change any existing call. `scan("--all")` is what
    every caller wrote before this, and it has to keep meaning exactly that."""
    assert armversion._as_refs("--all") == ["--all"]
    assert armversion._as_refs("HEAD") == ["HEAD"]
    assert armversion._as_refs(["--branches", "HEAD"]) == ["--branches", "HEAD"]
    assert armversion._as_refs(("--branches",)) == ["--branches"]


def test_an_empty_read_set_is_refused_rather_than_scanning_nothing():
    """A read set of nothing would report every recorded arm_version as
    `no_match` -- which is the strongest accusation this module makes, produced
    by a configuration mistake."""
    with pytest.raises(ValueError):
        armversion._as_refs([])


# -- the reverse control ----------------------------------------------------

def test_a_tag_on_a_commit_the_read_set_already_reaches_changes_nothing(repo):
    """The control the item asks for, in a real repository.

    A test that only ever checks "the tag was excluded" would also pass if
    `scan()` had been broken into returning nothing. This one requires the
    answer to be *the same*, before and after a real `git tag -a`, for a hash
    that is genuinely present -- so it fails if the scan starts under-reporting
    as well as if it starts over-reporting.
    """
    sha = _hash_at(repo["mainline"])
    before = armversion.scan()
    verdict_before = armversion.locate(sha, before)

    _git("tag", "-a", "-m", "a milestone", "v1.0", repo["mainline"],
         cwd=repo["work"])

    after = armversion.scan()
    verdict_after = armversion.locate(sha, after)

    assert verdict_before["verdict"] == "matched"
    assert verdict_after == verdict_before
    assert after["commits_scanned"] == before["commits_scanned"]
    assert after["distinct_arm_versions"] == before["distinct_arm_versions"]
    assert [c["commit"] for c in after["commits"]] == \
           [c["commit"] for c in before["commits"]]


def test_a_branch_pointing_at_an_unreachable_commit_is_still_seen(repo):
    """The other direction: the read set must not buy stability with lies.

    A commit on somebody's branch is a legitimate place for a run's sources to
    live, and a read set that missed it would answer `no_match` -- whose own
    text is "the run executed against a working tree that was never committed
    in that state". That is an accusation about honesty and it must not be
    producible by a choice of ref selectors.
    """
    sha = _hash_at(repo["unique"])
    assert _verdict(sha) == ("no_match", 0)

    _git("branch", "someone-elses-work", repo["unique"], cwd=repo["work"])
    assert _verdict(sha) == ("matched", 1)


def test_a_remote_branch_is_seen_too(repo):
    """A fresh clone has no local branches at all, only `origin/*`. Dropping
    `--remotes` would make every verdict in a clone `no_match`."""
    sha = _hash_at(repo["unique"])
    _git("update-ref", "refs/remotes/origin/someone-elses-work",
         repo["unique"], cwd=repo["work"])
    assert _verdict(sha) == ("matched", 1)


# -- what the read set excludes, and the counter that watches it ------------

def test_a_tag_alone_cannot_move_a_verdict(repo):
    """The trigger the item names, fired and then blocked.

    Under `--all` this exact tag turns `no_match` into `matched`; under the
    declared read set it does nothing. Both halves are asserted, because "the
    tag was excluded" is only meaningful next to proof that it would otherwise
    have counted.
    """
    sha = _hash_at(repo["unique"])
    _git("tag", "-a", "-m", "tagging an old experiment", "v-old",
         repo["unique"], cwd=repo["work"])

    assert _verdict(sha, "--all") == ("matched", 1)
    assert _verdict(sha) == ("no_match", 0)


def test_a_tag_alone_cannot_turn_matched_into_ambiguous(repo):
    """The second flip: same mechanism, opposite starting verdict.

    `duplicate` holds the same arm `.py` files as `mainline`, so a tag on it
    adds a second commit to an already-`matched` hash's group. Under `--all`
    that is enough to downgrade a manifest's `base_commit` from a single
    derived commit to "several commits share this arm_version".
    """
    sha = _hash_at(repo["duplicate"])
    assert _verdict(sha) == ("matched", 1)

    _git("tag", "-a", "-m", "and another", "v-dup", repo["duplicate"],
         cwd=repo["work"])

    assert _verdict(sha, "--all") == ("ambiguous", 2)
    assert _verdict(sha) == ("matched", 1)


def test_the_exclusion_counter_notices_what_the_read_set_drops(repo):
    """The case for excluding tags is a measurement ("0 tag-only commits
    today"), and a measurement written in a comment stops being true silently.

    So `scan()` re-measures it every time. Zero before the tag, non-zero after
    -- which is how a future reader learns that the paragraph justifying
    `DEFAULT_REFS` has expired.
    """
    assert armversion.scan()["excluded"]["--tags"] == 0

    _git("tag", "-a", "-m", "off to one side", "v-side", repo["unique"],
         cwd=repo["work"])

    # Exactly one: `unique` itself. Its parent `base` is `mainline`'s parent
    # too, so the read set already reaches it -- which is the counter behaving
    # like `rev-list --not` and not like a count of the tag's whole history.
    assert armversion.scan()["excluded"]["--tags"] == 1


def test_stash_is_outside_the_read_set(repo):
    """`git merge` creates an autostash without being asked, so `refs/stash`
    is the clearest case of a ref nobody decided to publish.

    (`runs/20260730T1200Z-A17-THE-STASH-WAS-INNOCENT/` corrected an earlier
    claim that stash was doing real damage here -- it was not, and the write-up
    stands. It is still not a publication, and a read set that names its
    members leaves it out by construction rather than by argument.)
    """
    work = repo["work"]
    with open(os.path.join(work, "theoria-arm", "mod.py"), "w",
              encoding="utf-8", newline="\n") as fh:
        fh.write("V = 4242\n")
    _git("stash", "push", "-m", "an autostash would look like this", cwd=work)

    stashed = _git("rev-parse", "refs/stash", cwd=work)
    sha = _hash_at(stashed)

    assert _verdict(sha, "--all") != ("no_match", 0)
    assert _verdict(sha) == ("no_match", 0)


# -- the scan's own shape ---------------------------------------------------

def test_the_scan_records_which_refs_it_read(repo):
    """An answer that depends on a read set has to publish the read set, or the
    dependence is invisible again one layer up."""
    table = armversion.scan()
    assert table["refs"] == list(armversion.DEFAULT_REFS)
    assert "excluded" in table

    explicit = armversion.scan(["HEAD"])
    assert explicit["refs"] == ["HEAD"]


def test_the_exclusion_probe_never_breaks_the_scan(repo, monkeypatch):
    """A diagnostic beside the answer must not become a gate on it."""
    def boom(*args, **kwargs):
        raise RuntimeError("git said no")

    monkeypatch.setattr(armversion, "_git", boom)
    excluded = armversion._excluded(["--branches"])
    assert "unmeasured" in excluded["--tags"]
