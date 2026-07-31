"""A tracked generated artefact must not record where its builder stood.

The defect: `exam/artifacts/build_manifest.json` held twelve absolute paths --
four papers x `sheet_path` / `key_path` / `cheater_brief_path` -- naming whichever
worktree last ran `build_papers`. Every delivery in this territory therefore
carried twelve lines of pseudo-diff whose two sides mean the same thing, and
`archive_run.py` folds this file into each archived run's manifest, so the leak
reaches the provenance canon and a release manifest that publishes every tracked
file.

Both directions are pinned here, because a scanner that always says "clean" and
one that always says "dirty" are equally green in a test that only checks one.
"""
import json
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from exam.tools import check_artefact_locations as cal   # noqa: E402


def test_no_tracked_artefact_records_its_builders_location():
    findings = cal.scan()
    assert findings == [], (
        "tracked artefacts under exam/artifacts record where they were built: %s"
        % [(f[0], f[1]) for f in findings])


def test_the_scanner_fires_on_the_artefact_as_it_shipped(tmp_path, monkeypatch):
    """Negative control, against the real pre-fix bytes rather than a mock-up.

    `8a5a83f9` is origin/master when this ticket was claimed; its
    `build_manifest.json` is the artefact with the twelve absolute paths in it.
    Skips rather than fails where that object is unreachable -- a shallow clone
    should not turn a history question into a red gate.
    """
    blob = subprocess.run(
        ["git", "show", "8a5a83f9:exam/artifacts/build_manifest.json"],
        cwd=REPO, capture_output=True)
    if blob.returncode != 0:
        import pytest
        pytest.skip("the pre-fix blob is not reachable in this clone")
    text = blob.stdout.decode("utf-8")
    searchable = cal._searchable("build_manifest.json", text)
    hits = [what for what, rx in cal.PATTERNS if rx.search(searchable)]
    assert "windows absolute path" in hits and "worktree segment" in hits, (
        "the scanner does not fire on the very artefact that motivated it; "
        "matched only %s" % hits)


def test_json_escapes_are_not_mistaken_for_paths():
    """The first version of this scanner reported seven findings, all false.

    JSON writes a newline as backslash-n, so a paper whose prose contains
    `asked:` before a line break literally holds `asked:\\n` on disk -- which a
    drive-letter pattern and a backslash-separator pattern both match. Decoding
    first is what makes the scanner usable, so it is pinned.
    """
    raw = json.dumps({"prompt": "four things are asked:\nreplay the manual"})
    searchable = cal._searchable("x.json", raw)
    hits = [what for what, rx in cal.PATTERNS if rx.search(searchable)]
    assert hits == [], "false positives on JSON escapes: %s" % hits


def test_a_repo_relative_path_is_not_a_finding():
    """The fix must not trip the gate that motivated it."""
    raw = json.dumps({"sheet_path": "exam/artifacts/papers/p15-heldout-a0.paper.json"})
    searchable = cal._searchable("x.json", raw)
    hits = [what for what, rx in cal.PATTERNS if rx.search(searchable)]
    assert hits == [], "repo-relative paths must pass: %s" % hits


def test_build_papers_records_repo_relative_paths():
    """The generator, not just the artefact: regenerating must stay clean."""
    from exam.tools import build_papers
    payload = build_papers.build_all(write=False)
    assert payload["papers"], "no papers built"
    # write=False emits no paths at all; the point is that the keys that DO
    # carry paths are produced by _repo_rel, so check the helper directly
    # against an absolute path under the repo.
    absolute = os.path.join(REPO, "exam", "artifacts", "papers", "x.json")
    assert build_papers._repo_rel(absolute) == "exam/artifacts/papers/x.json"
    assert not os.path.isabs(build_papers._repo_rel(absolute))
