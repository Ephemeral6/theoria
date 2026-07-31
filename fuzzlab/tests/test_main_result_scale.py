"""The scale gate, and the negative control that makes it worth having.

V-26's finding was not that a number was wrong. Every number in the campaign is
correct. The finding was that `README.md` sent a reader to `out/campaign.json`
for a 3000-world result, and `out/campaign.json` is a 60-world smoke that
reports **zero violations** just as convincingly as the real run does. So the
reader checks, the check passes, and the thing checked is fifty times smaller
than the thing claimed. A green that arrives whether or not the claim is true is
not evidence about the claim.

`verify.check_main_result` is the fix, and the load-bearing test here is
`test_the_smoke_file_in_the_main_slot_goes_red`: it puts the actual smoke
artifact — not a fabricated small one — in the actual main slot and asserts the
gate refuses it. If that test ever passes silently, the gate has stopped being
able to tell the two files apart, which is the exact condition it exists to
detect.
"""

import json
import os

import pytest

from fuzzlab import verify


def _fuzzlab_dir() -> str:
    return os.path.dirname(os.path.abspath(verify.__file__))


def _smoke_path() -> str:
    return os.path.join(_fuzzlab_dir(), verify.SMOKE_SNAPSHOT)


def _main_path() -> str:
    return os.path.join(_fuzzlab_dir(), verify.MAIN_RESULT)


def test_the_published_main_result_passes_the_gate():
    assert verify.check_main_result(_main_path()) == []


def test_the_smoke_file_in_the_main_slot_goes_red():
    """The negative control. The smoke artifact, unmodified, in the main slot."""
    smoke = _smoke_path()
    assert os.path.exists(smoke), "the 60-world snapshot is part of this test"
    with open(smoke, encoding="utf-8") as handle:
        doc = json.load(handle)
    # The premise: it is a real, green, small campaign — that is what makes it
    # mistakable for the main result in the first place.
    assert doc["totals"]["violated"] == 0
    assert doc["worlds_per_engine"] == 60

    problems = verify.check_main_result(smoke)
    assert problems, "the 60-world smoke was accepted as the 3000-world result"
    joined = " | ".join(problems)
    assert "worlds_per_engine is 60" in joined
    assert "worlds_checked is 360" in joined


def test_the_smoke_file_goes_red_through_the_env_override(monkeypatch):
    """Same control, driven the way the command-line gate resolves its path."""
    monkeypatch.setenv("FUZZLAB_MAIN_RESULT", _smoke_path())
    assert verify.main_result_path() == _smoke_path()
    assert verify.check_main_result(verify.main_result_path())


def test_a_pre_v21_artifact_of_the_right_size_still_goes_red(tmp_path):
    """3000 worlds is necessary and not sufficient.

    `runs/…V13…/partials/campaign.500w.json` is the same 3000 worlds under the
    pre-V-21 schema, which had no way to count the worlds a *tool* failed on.
    Absent is not zero, so it does not pass as the published result.
    """
    v13 = os.path.join(
        _fuzzlab_dir(), "runs", "20260728T161127Z-V13-audit-the-published-surface",
        "partials", "campaign.500w.json")
    if not os.path.exists(v13):
        pytest.skip("V-13 partial not present")
    problems = verify.check_main_result(v13)
    assert any("unavailable" in p for p in problems)
    assert not any("worlds_per_engine" in p for p in problems)


def test_a_truncated_artifact_goes_red(tmp_path):
    with open(_main_path(), encoding="utf-8") as handle:
        doc = json.load(handle)
    doc["engines"] = doc["engines"][:3]
    doc["totals"]["worlds_checked"] = 1500
    path = tmp_path / "campaign.json"
    path.write_text(json.dumps(doc), encoding="utf-8")
    problems = verify.check_main_result(str(path))
    assert any("engine(s) in the artifact" in p for p in problems)
    assert any("worlds_checked" in p for p in problems)


def test_a_reseeded_artifact_goes_red(tmp_path):
    """The seed is part of the claim; a run of the right size under a different
    seed is a different experiment, not this one."""
    with open(_main_path(), encoding="utf-8") as handle:
        doc = json.load(handle)
    doc["campaign_seed"] = "0x0000000000000001"
    path = tmp_path / "campaign.json"
    path.write_text(json.dumps(doc), encoding="utf-8")
    assert any("campaign_seed" in p for p in verify.check_main_result(str(path)))


def test_a_violation_does_not_make_the_gate_red(tmp_path):
    """失败是战利品 — the exit code is about the instrument, not the reading."""
    with open(_main_path(), encoding="utf-8") as handle:
        doc = json.load(handle)
    doc["totals"]["violated"] = 7
    doc["engines"][0]["violated"] = 7
    path = tmp_path / "campaign.json"
    path.write_text(json.dumps(doc), encoding="utf-8")
    assert verify.check_main_result(str(path)) == []


def test_a_missing_main_result_goes_red(tmp_path):
    assert verify.check_main_result(str(tmp_path / "nope.json"))


def test_the_documents_quote_the_gate_s_numbers():
    """The prose and the constant have to agree, or the gate guards nothing.

    `README.md` and `BUGS.md` quote 3000 worlds and 26 invariants. If somebody
    lowers `CLAIMED_WORLDS_PER_ENGINE` to make a red gate green, this fails.
    """
    assert verify.CLAIMED_WORLDS_PER_ENGINE * verify.CLAIMED_ENGINES == 3000
    for name in ("README.md", "BUGS.md"):
        text = open(os.path.join(_fuzzlab_dir(), name), encoding="utf-8").read()
        assert "3000" in text
        assert verify.CLAIMED_SEED in text
