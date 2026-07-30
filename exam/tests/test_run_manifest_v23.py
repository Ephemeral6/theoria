"""The V23 run's manifest must pin the bytes git publishes, not a working copy.

Round six shipped `adversarial/round6-findings.md` tracked and unlisted, and the
round that stamped the manifest hashed two files whose working copies carried
CRLF while every blob under `exam/` is LF.  Both are the same defect one level
apart: the manifest said something about the directory that was not true of the
directory, and no check could tell.  `git diff` cannot see the second one --
check-in normalisation makes a CRLF working copy equal to its LF blob again --
so it has to be asserted directly.
"""
import hashlib
import importlib.util
import json
import os
import subprocess

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RUN = os.path.join(REPO, "exam", "runs", "20260730T021500Z-V23-large-space")
RUN_REL = "exam/runs/20260730T021500Z-V23-large-space"


def _load_restamp():
    path = os.path.join(RUN, "restamp_manifest.py")
    spec = importlib.util.spec_from_file_location("v23_restamp", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _published_many(repo_rels):
    """The bytes in the index -- what a fresh checkout of this tree receives.

    One `git cat-file --batch` rather than one `git show` per path: on Windows
    the process spawn dominates, and this test was 100 seconds of it.
    """
    query = "".join(":%s\n" % r for r in repo_rels)
    proc = subprocess.run(["git", "cat-file", "--batch"], cwd=REPO,
                          input=query.encode(), capture_output=True, check=True)
    out, pos, result = proc.stdout, 0, {}
    for rel in repo_rels:
        nl = out.index(b"\n", pos)
        header = out[pos:nl].decode()
        if header.endswith(("missing", "ambiguous")):
            result[rel] = None
            pos = nl + 1
            continue
        size = int(header.split()[2])
        result[rel] = out[nl + 1:nl + 1 + size]
        pos = nl + 1 + size + 1          # payload then its trailing newline
    return result


def test_manifest_covers_every_tracked_artefact_in_the_run_directory():
    m = json.load(open(os.path.join(RUN, "MANIFEST.json"), encoding="utf-8"))
    listed = {e["path"] for e in m["files"]}
    tracked = subprocess.run(["git", "ls-files", RUN_REL], cwd=REPO,
                             capture_output=True, text=True, check=True).stdout.split()
    restamp = _load_restamp()
    unlisted = sorted(
        p[len(RUN_REL) + 1:] for p in tracked
        if p[len(RUN_REL) + 1:] not in listed
        and p[len(RUN_REL) + 1:] not in restamp.EXCLUDED_NAMES)
    assert unlisted == [], (
        "tracked in the run directory and absent from MANIFEST.json: %s" % unlisted)


def test_the_coverage_exclusions_are_pinned_and_not_an_open_door():
    """`test_manifest_covers_...` skips whatever `EXCLUDED_NAMES` contains, so
    without this the coverage test can be satisfied by adding a file's name to
    that set.  The escape hatch has to be a stated list, not a growable one."""
    restamp = _load_restamp()
    assert restamp.EXCLUDED_NAMES == {
        "MANIFEST.json",          # cannot hash itself
        "BASELINE-cycle94.md",    # another session's cycle log, not this run's
        "restamp_manifest.py",    # generates the manifest
    }, ("the manifest's exclusion list changed; every entry is justified in "
        "MANIFEST.json's own `note`, so the note has to change with it")


def test_manifest_hashes_match_the_published_bytes():
    """Three-way: the stamp, the disk, and the index must agree.

    Two-way against the index alone would pass while an unstaged edit sat in the
    working copy; two-way against the disk alone is the bug this run shipped.
    """
    m = json.load(open(os.path.join(RUN, "MANIFEST.json"), encoding="utf-8"))
    blobs = _published_many(["%s/%s" % (RUN_REL, e["path"]) for e in m["files"]])
    bad = []
    for e in m["files"]:
        blob = blobs["%s/%s" % (RUN_REL, e["path"])]
        disk = open(os.path.join(RUN, e["path"]), "rb").read()
        if blob is None:
            bad.append((e["path"], "not in the index"))
            continue
        if blob != disk:
            bad.append((e["path"], "working copy differs from the index"))
        if hashlib.sha256(disk).hexdigest() != e["sha256"]:
            bad.append((e["path"], "stale stamp"))
    assert bad == [], "manifest does not pin what git publishes: %s" % bad


def test_nothing_under_exam_carries_crlf_in_the_working_copy():
    """`exam/.gitattributes` pins `* text eol=lf`; that governs checkout, not
    what a tool writes afterwards.  Four files had drifted this way, and two of
    them were being hashed into a manifest."""
    tracked = subprocess.run(["git", "ls-files", "exam"], cwd=REPO,
                             capture_output=True, text=True, check=True).stdout.split("\n")
    crlf = []
    for rel in (p for p in tracked if p.strip()):
        path = os.path.join(REPO, rel)
        if not os.path.exists(path):
            continue
        if b"\r\n" in open(path, "rb").read():
            crlf.append(rel)
    assert crlf == [], (
        "CRLF in the working copy under exam/: %s\n"
        "git will publish LF for these, so anything that hashes the disk is "
        "hashing bytes the repository does not contain. Fix in place:\n"
        "  python -c \"import sys;p=sys.argv[1];b=open(p,'rb').read();"
        "open(p,'wb').write(b.replace(b'\\r\\n',b'\\n'))\" <path>" % crlf)


def test_the_stamper_refuses_a_working_copy_that_is_not_the_published_bytes():
    """Negative control: the guard has to have been seen to fire."""
    restamp = _load_restamp()
    with pytest.raises(restamp.WorkingCopyIsNotPublished):
        restamp._assert_published_bytes("fake.md", b"line one\r\nline two\n")
    restamp._assert_published_bytes("fake.md", b"line one\nline two\n")
