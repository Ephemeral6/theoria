"""Both directions, because a scanner that always says "clean" and one that
always says "dirty" are equally green in a test that only checks one.

The house rule this file exists to satisfy: before the gate is trusted, it must
have been *seen red*. `test_it_fires_on_the_artefact_that_motivated_it` points
it at the real pre-fix bytes of `exam/artifacts/build_manifest.json` -- the
twelve absolute paths V27 removed -- rather than at a mock-up, so the thing that
has been seen to fail is the thing that ships.

    python -m pytest tools/tests -q
"""
import json
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if os.path.join(REPO, "tools") not in sys.path:
    sys.path.insert(0, os.path.join(REPO, "tools"))

import check_locations as cl                              # noqa: E402


def _hits(rel, raw, scope="artefact"):
    text = cl._searchable(rel, raw)
    return [what for what, rx in cl._patterns(scope) if rx.search(text)]


# ------------------------------------------------------------------ the tree

def test_the_tree_is_clean_or_signed_for():
    findings = cl.scan()
    violations, _notes = cl.adjudicate(findings, cl.load_allowlist())
    assert violations == [], (
        "tracked artefacts or run records name a machine without an exemption: "
        "%s" % [(v[0], v[1]) for v in violations])


def test_the_allowlist_is_not_a_blanket():
    """Every exemption names a file or a directory, a date, and a reason."""
    allow = cl.load_allowlist()
    for entry in allow["artefacts"]:
        assert len(entry["sha256"]) == 64, entry["path"]
        assert len(entry["reason"]) > 40, "%s has no real reason" % entry["path"]
        assert "*" not in entry["path"], "an exemption may not be a glob"
    for entry in allow["runs"]:
        assert "runs" in entry["dir"].split("/"), entry["dir"]
        assert entry["dated"] and entry["files"] >= 1, entry["dir"]
        assert "*" not in entry["dir"], "an exemption may not be a glob"


def test_a_pinned_exemption_dies_when_the_file_changes():
    """The sha256 is the whole mechanism: an exemption granted to one set of
    bytes must not carry over to a regeneration that is still dirty."""
    allow = cl.load_allowlist()
    entry = dict(allow["artefacts"][0])
    entry["sha256"] = "0" * 64
    doctored = {"artefacts": [entry], "runs": allow["runs"]}
    findings = {"artefact": [(entry["path"], "windows absolute path", "x")],
                "run": []}
    violations, _ = cl.adjudicate(findings, doctored)
    assert violations and "does not carry over" in violations[0][2]


def test_an_unlisted_run_directory_is_red():
    """A NEW write-once record carrying an absolute path is not inherited."""
    findings = {"artefact": [],
                "run": [("worldgen/runs/20990101T0000Z-new/log.txt",
                         "windows absolute path", "x")]}
    violations, _ = cl.adjudicate(findings, cl.load_allowlist())
    assert violations, "an unlisted run directory passed"
    assert violations[0][1] == "worldgen/runs/20990101T0000Z-new"


def test_a_listed_run_directory_that_grew_is_red():
    allow = cl.load_allowlist()
    listed = allow["runs"][0]
    findings = {"artefact": [], "run": [
        ("%s/f%d.txt" % (listed["dir"], i), "windows absolute path", "x")
        for i in range(listed["files"] + 1)]}
    violations, _ = cl.adjudicate(findings, allow)
    assert violations and "after it was signed off" in violations[0][2]


# --------------------------------------------------------------- seen-red

def test_it_fires_on_the_artefact_that_motivated_it():
    """Negative control against real pre-fix bytes, not a mock-up.

    `8a5a83f9` is origin/master when V27 was claimed; its `build_manifest.json`
    is the artefact with the twelve absolute paths in it. Skips rather than
    fails where the object is unreachable -- a shallow clone should not turn a
    history question into a red gate.
    """
    blob = subprocess.run(
        ["git", "show", "8a5a83f9:exam/artifacts/build_manifest.json"],
        cwd=REPO, capture_output=True)
    if blob.returncode != 0:
        import pytest
        pytest.skip("the pre-fix blob is not reachable in this clone")
    hits = _hits("build_manifest.json", blob.stdout.decode("utf-8"))
    assert "windows absolute path" in hits and "worktree segment" in hits, hits


def test_it_fires_on_a_real_run_record_in_run_scope():
    """The same house rule, for the scope that carries 94% of the findings.

    Added 2026-08-04 by S50 because the run half of this gate had never been
    seen red against real bytes. Every other run test in this file hands
    `adjudicate` a hand-fabricated finding tuple, which tests the bookkeeping
    and never the predicate, and `_hits` defaults to `scope="artefact"` -- so
    `_patterns("run")`, a DIFFERENT frozenset, was exercised by nothing.

    Measured before writing this: setting `RUN_PATTERN_NAMES = frozenset()` in
    memory -- i.e. deleting the run detector outright -- turned every test in
    this file green, including the two that were red at the time. A mutation
    that removes half the gate should not repair its test suite. This test
    kills that mutant.

    `445c647e` is the R1b landing; its `run.json` records the spend gate's
    `ledger_abspath`, which is absolute by design (harness/spend.py:160) and is
    therefore a stable specimen rather than something a later fix will erase.
    """
    blob = subprocess.run(
        ["git", "show",
         "445c647e:theoria-arm/runs/20260801T001851Z-R1b-sk48-b/run.json"],
        cwd=REPO, capture_output=True)
    if blob.returncode != 0:
        import pytest
        pytest.skip("the run blob is not reachable in this clone")
    hits = _hits("run.json", blob.stdout.decode("utf-8"), scope="run")
    assert "windows absolute path" in hits, hits


def test_run_scope_has_patterns_at_all():
    """A `_patterns("run")` that returned nothing would report `clean` forever.

    The failure mode this guards is silence, not a wrong answer: 5946 run files
    scanned and zero findings reads exactly like a tidy tree. It is not implied
    by the test above, which skips when the blob is unreachable.
    """
    names = [name for name, _rx in cl._patterns("run")]
    assert "windows absolute path" in names and "worktree segment" in names, names


def test_the_full_pipeline_reports_the_pre_fix_blob_as_a_violation():
    """Not just the regex: an unlisted dirty artefact must reach `adjudicate`."""
    findings = {"artefact": [("exam/artifacts/build_manifest.json",
                              "windows absolute path", "C:/...")], "run": []}
    violations, _ = cl.adjudicate(findings, cl.load_allowlist())
    assert violations and violations[0][0] == "artefact"


# ------------------------------------------------------- false positives

def test_json_escapes_are_not_mistaken_for_paths():
    raw = json.dumps({"prompt": "four things are asked:\nreplay the manual"})
    assert _hits("x.json", raw) == []


def test_a_repo_relative_path_is_not_a_finding():
    raw = json.dumps({"sheet_path": "exam/artifacts/papers/p15-heldout-a0.paper.json"})
    assert _hits("x.json", raw) == []


def test_a_url_is_not_a_drive_letter():
    """The first repo-wide run reported all twelve paper SVGs, because
    `[A-Za-z]:[\\\\/]` matches the `p:/` in `http://`."""
    raw = '<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/x.dtd">'
    assert _hits("x.svg", raw) == []
    assert _hits("x.md", "see <https://arcprize.org/terms>") == []


def test_the_account_name_user_does_not_match_userSpaceOnUse():
    """This machine's account is literally `user`; V27's `len < 4` guard let it
    through and every SVG says `patternUnits="userSpaceOnUse"`."""
    assert _hits("x.svg", '<pattern patternUnits="userSpaceOnUse"/>') == []


def test_prose_about_worktrees_is_not_a_location():
    assert _hits("x.md", "one `rm -rf .worktrees/` from nonexistent") == []
    assert "worktree segment" in _hits(
        "x.md", r"built in D:\src\theoria\.worktrees\slug\exam")


def test_the_absolute_path_it_is_about_still_fires():
    assert "windows absolute path" in _hits("x.md", "at C:/Somewhere/theoria/x")
    assert "posix home path" in _hits("x.md", "at /home/someone/theoria/x")


# ------------------------------------------------------------------- scope

def test_scope_classification():
    assert cl.classify("battery/artifacts/x.json") == "artefact"
    assert cl.classify("figures/paper/light/f1.svg") == "artefact"
    assert cl.classify("freeze/MANIFEST.json") == "artefact"
    assert cl.classify("exam/runs/20260101T0000Z-x/MANIFEST.json") == "run"
    # records of a machine, by design
    assert cl.classify("monitor/ci/CONFLICT-x.md") == "skip"
    assert cl.classify("monitor/runs/opsm32/pass-watch.log") == "skip"
    assert cl.classify("theoria-arm/evidence/model-proxy-401.jsonl") == "skip"
    # hand-written code and prose: the two live examples are a negative-control
    # fixture and three findings, and a gate that reddens on those is asking
    # prose to stop naming the bug
    assert cl.classify("fleet-study/verify.py") == "skip"
    assert cl.classify("papers/phase1-workshop/REVIEW.md") == "skip"


def test_a_loose_file_under_runs_is_its_own_unit():
    assert cl.run_dir("ablation-arm/runs/A4-COMMIT_MSG.txt") == \
        "ablation-arm/runs/A4-COMMIT_MSG.txt"
    assert cl.run_dir("exam/runs/20260101T0000Z-x/a/b.txt") == \
        "exam/runs/20260101T0000Z-x"


def test_main_is_green_on_this_tree():
    assert cl.main([]) == 0


def test_the_pin_survives_a_line_ending_conversion(tmp_path):
    """core.autocrlf is true here and only some paths carry eol=lf, so a raw
    digest would expire every exemption at the checkout boundary."""
    lf = tmp_path / "a.txt"
    crlf = tmp_path / "b.txt"
    lf.write_bytes(b"one\ntwo\n")
    crlf.write_bytes(b"one\r\ntwo\r\n")
    assert cl.sha256(str(lf)) == cl.sha256(str(crlf))
    (tmp_path / "c.txt").write_bytes(b"one\ntoo\n")
    assert cl.sha256(str(lf)) != cl.sha256(str(tmp_path / "c.txt"))
