"""The manifest generator, and the one thing that makes hashes worth writing.

A manifest whose `--verify` cannot go red is decoration. So: build one over a
scratch directory, verify it green, change one byte, verify it red and name the
file.
"""

from __future__ import annotations

import json
import os

import pytest

from harness import run_manifest

pytestmark = pytest.mark.filterwarnings("ignore")


@pytest.fixture
def run_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(run_manifest, "REPO", str(tmp_path))
    d = tmp_path / "runs" / "20260101T0000Z-mock"
    d.mkdir(parents=True)
    (d / "result.txt").write_text("two lines\nof evidence\n", encoding="utf-8")
    (d / "RUN_STATE.md").write_text("# mock\n", encoding="utf-8")
    return str(d)


def test_it_carries_every_key_claude_md_requires(run_dir):
    doc = run_manifest.build(run_dir, prompt_id="A28b", utc="2026-01-01T00:00:00Z",
                             note="mock", extra=[], tests="0 passed")
    for key in run_manifest.REQUIRED:
        assert doc.get(key), key
    assert doc["territory"] == "baseline-arms"
    assert set(doc["files"]) == {
        "runs/20260101T0000Z-mock/RUN_STATE.md",
        "runs/20260101T0000Z-mock/result.txt",
    }
    assert doc["files"]["runs/20260101T0000Z-mock/result.txt"]["bytes"] == \
        os.path.getsize(os.path.join(run_dir, "result.txt"))


def test_a_missing_required_key_refuses_rather_than_writing_a_blank(run_dir):
    with pytest.raises(SystemExit):
        run_manifest.build(run_dir, prompt_id="", utc="2026-01-01T00:00:00Z",
                           note="", extra=[])


def test_verify_is_green_on_what_it_just_hashed(run_dir):
    doc = run_manifest.build(run_dir, prompt_id="A28b", utc="2026-01-01T00:00:00Z",
                             note="mock", extra=[])
    run_manifest.write(run_dir, doc)
    res = run_manifest.verify(run_dir)
    assert res["ok"], res["problems"]
    assert res["files"] == 2


def test_verify_goes_red_on_one_changed_byte_and_names_the_file(run_dir):
    """The negative control. A hash block that cannot fail is a decoration."""
    doc = run_manifest.build(run_dir, prompt_id="A28b", utc="2026-01-01T00:00:00Z",
                             note="mock", extra=[])
    run_manifest.write(run_dir, doc)

    p = os.path.join(run_dir, "result.txt")
    with open(p, "a", encoding="utf-8") as fh:
        fh.write("x")

    res = run_manifest.verify(run_dir)
    assert not res["ok"]
    assert any("result.txt" in p_ for p_ in res["problems"]), res["problems"]


def test_verify_goes_red_when_a_listed_file_is_gone(run_dir):
    doc = run_manifest.build(run_dir, prompt_id="A28b", utc="2026-01-01T00:00:00Z",
                             note="mock", extra=[])
    run_manifest.write(run_dir, doc)
    os.remove(os.path.join(run_dir, "result.txt"))

    res = run_manifest.verify(run_dir)
    assert not res["ok"]
    assert any("gone" in p_ for p_ in res["problems"]), res["problems"]


def test_the_manifest_itself_is_not_hashed_into_itself(run_dir):
    doc = run_manifest.build(run_dir, prompt_id="A28b", utc="2026-01-01T00:00:00Z",
                             note="mock", extra=[])
    run_manifest.write(run_dir, doc)
    with open(os.path.join(run_dir, "MANIFEST.json"), encoding="utf-8") as fh:
        written = json.load(fh)
    assert not any(k.endswith("MANIFEST.json") for k in written["files"])


def test_references_are_named_but_not_hashed(run_dir):
    """A hash that cannot reproduce on another checkout is worse than none.

    `monitor/inbox/` carries no `eol=lf` attribute and `core.autocrlf` is true
    here, so a proposal written with LF is checked out with CRLF elsewhere. The
    manifest names those deliveries and does not pretend to pin their bytes.
    """
    doc = run_manifest.build(run_dir, prompt_id="A28b", utc="2026-01-01T00:00:00Z",
                             note="mock", extra=[],
                             references=["monitor/inbox/b.md", "monitor/inbox/a.md"])
    assert doc["references_not_hashed"] == ["monitor/inbox/a.md", "monitor/inbox/b.md"]
    for ref in doc["references_not_hashed"]:
        assert ref not in doc["files"]
