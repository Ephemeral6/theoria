"""The licence filter, checked as a property rather than as a printed count.

The failure this guards against is not a crash. It is a release that ships one
file it may not, discovered after publication, when `CLAUDE.md`'s own note about
irreversibility applies: what is published is published.

    python -m pytest release/tests
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RELEASE = os.path.dirname(HERE)
ROOT = os.path.dirname(RELEASE)
if RELEASE not in sys.path:
    sys.path.insert(0, RELEASE)

import bundle                                          # noqa: E402


def rows(path):
    with open(os.path.join(RELEASE, path), encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def test_nothing_needing_permission_is_in_the_bundle():
    """The one that matters. Checked against the manifest's verdicts, not
    against the bundle's own copy of them -- a bundle that mislabelled a row
    would otherwise vouch for itself."""
    verdicts = {r["path"]: r.get("verdict") for r in bundle.read_manifest()}
    for row in rows("BUNDLE.jsonl"):
        assert verdicts[row["path"]] in bundle.SHIPS, (
            "%s ships with verdict %r" % (row["path"], verdicts[row["path"]]))


def test_the_partition_loses_nothing():
    """Every tracked file is either shipped or named as withheld. A file in
    neither list is the one omission no reader can detect."""
    manifest = {r["path"] for r in bundle.read_manifest()}
    shipped = {r["path"] for r in rows("BUNDLE.jsonl")}
    withheld = {r["path"] for r in rows("FRAME_HASHES.jsonl")}
    assert shipped | withheld == manifest
    assert not (shipped & withheld)


def test_every_withheld_file_has_a_hash_and_a_recipe():
    """A hash with no recipe is a promise, not a reproduction. A recipe with no
    hash is a reproduction nobody can check."""
    for row in rows("FRAME_HASHES.jsonl"):
        assert row["sha256"] and len(row["sha256"]) == 64, row["path"]
        assert row["regenerate"], row["path"]
        assert "no regeneration recipe is registered" not in row["regenerate"], (
            "%s falls through to the generic message; add a recipe to "
            "bundle.RECIPES or say explicitly that it cannot be regenerated"
            % row["path"])


def test_an_unclassified_verdict_would_be_withheld():
    """The allow-list, exercised rather than asserted: a verdict nobody has
    thought about must not ship."""
    ships, held = bundle.split([
        {"path": "a", "verdict": "releasable"},
        {"path": "b", "verdict": "needs_human"},
        {"path": "c", "verdict": "some-future-verdict"},
        {"path": "d", "verdict": None},
    ])
    assert [r["path"] for r in ships] == ["a"]
    assert [r["path"] for r in held] == ["b", "c", "d"]


def test_the_bundle_on_disk_is_current():
    """`--check`, run as a test. A stale bundle carries the authority of having
    been checked without the fact of it."""
    assert bundle.check() == 0
