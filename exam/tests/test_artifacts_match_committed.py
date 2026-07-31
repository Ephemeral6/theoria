"""verify must compare its build against what is committed -- and not adopt it.

The defect (V2/V25): `python -m exam.verify` printed GREEN while three of its
stages overwrote `exam/artifacts/` in place and no stage ever looked at what had
been there first. The determinism stage compares two fresh builds to each other
in memory and never opens a committed file, so the committed sheets could have
been produced by a rubric that no longer existed -- and on the branches lagging
`18a39417` they were, `e06bdf52` on disk against `63ce1eab` from a rebuild.

Both directions are pinned, because a gate that always says "match" and one that
always says "drift" are equally green in a test that checks one of them. And the
adoption direction is pinned too: the tracked tree must be untouched after a
redirected build, since a gate that quietly fixed what it found would erase its
own finding, which is how the original defect survived.
"""
import json
import os
import shutil
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from exam.model import artifact_rel                        # noqa: E402
from exam.tools import check_artifacts_match as cam        # noqa: E402


def _shadow_of_committed(tmp_path):
    """A shadow tree holding exactly the committed bytes, as a build would."""
    dest = str(tmp_path / "artifacts")
    shutil.copytree(os.path.join(REPO, "exam", "artifacts"), dest)
    return dest


def test_an_identical_tree_is_a_match(tmp_path):
    shadow = _shadow_of_committed(tmp_path)
    mismatched, _touched, _changed, missing = cam.compare(shadow)
    assert mismatched == [], "a copy of the committed tree reported drift: %s" % mismatched
    assert missing == []


def test_one_flipped_byte_is_caught(tmp_path):
    """The negative control the ticket asks for, at the comparison layer.

    One byte, in one artefact, in a place no schema check would notice.
    """
    shadow = _shadow_of_committed(tmp_path)
    victim = os.path.join(shadow, "calibration.json")
    raw = open(victim, encoding="utf-8").read()
    flipped = raw.replace("0", "1", 1)
    assert flipped != raw, "the fixture no longer contains the byte to flip"
    with open(victim, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(flipped)
    mismatched, _touched, _changed, _missing = cam.compare(shadow)
    assert mismatched == ["exam/artifacts/calibration.json"], (
        "a flipped byte in a tracked artefact was not reported: %s" % mismatched)


def test_a_deleted_artefact_is_caught(tmp_path):
    shadow = _shadow_of_committed(tmp_path)
    os.remove(os.path.join(shadow, "selftest.json"))
    _mismatched, _touched, _changed, missing = cam.compare(shadow)
    assert "exam/artifacts/selftest.json" in missing


def test_the_working_tree_still_holds_what_was_committed():
    """The gate's first question, asked of this checkout.

    Red here means someone ran a producer in place, or hand-edited a generated
    file. Both are findings, not test flakes.
    """
    clean, detail = cam.working_tree_is_committed()
    assert clean, "exam/artifacts differs from HEAD:\n%s" % detail


def test_a_redirected_build_does_not_touch_the_tracked_tree(tmp_path):
    """The restructure itself: building must not consume the evidence.

    `EXAM_ARTIFACTS_DIR` is the whole of the redirect, so this run also proves
    the producers honour it rather than resolving `exam/artifacts` a second way.
    """
    def artefact_diff():
        return subprocess.run(["git", "diff", "--stat", "HEAD", "--",
                               "exam/artifacts"], cwd=REPO,
                              capture_output=True, text=True).stdout

    # Before and after, not just after: the tree may already be dirty for a
    # reason of the reader's own -- during the negative-sample run it is dirty
    # on purpose -- and blaming that on the build would be a false accusation
    # from the one test whose job is to be precise about who wrote what.
    before = artefact_diff()
    shadow = str(tmp_path / "artifacts")
    env = dict(os.environ, EXAM_ARTIFACTS_DIR=shadow)
    proc = subprocess.run([sys.executable, "-m", "exam.tools.build_papers"],
                          cwd=REPO, env=env, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    built = os.path.join(shadow, "papers", "p15-verdict-a2.paper.json")
    assert os.path.exists(built), "the redirect was ignored; nothing in %s" % shadow
    after = artefact_diff()
    assert after == before, (
        "a redirected build wrote into the tracked tree.\nbefore:\n%s\nafter:\n%s"
        % (before, after))


def test_a_redirected_build_records_the_same_paths(tmp_path):
    """Paths inside artefacts must not move when the build directory does.

    Before `artifact_rel`, `build_manifest.json` and the verdict answer key both
    derived their paths from the repo root, so a build in a shadow tree emitted
    `../../AppData/Local/Temp/...` -- and the match gate would have read the
    redirect's own footprint as drift, which is a gate that can never be green.
    """
    shadow = str(tmp_path / "artifacts")
    env = dict(os.environ, EXAM_ARTIFACTS_DIR=shadow)
    proc = subprocess.run([sys.executable, "-m", "exam.tools.build_papers"],
                          cwd=REPO, env=env, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    manifest = json.load(open(os.path.join(shadow, "build_manifest.json"),
                              encoding="utf-8"))
    recorded = [row[key] for row in manifest["papers"]
                for key in ("sheet_path", "key_path", "cheater_brief_path")]
    key = json.load(open(os.path.join(shadow, "truth",
                                      "p15-verdict-a2.truth.json"),
                         encoding="utf-8"))
    recorded += [item["spec"]["spec_file"] for item in key["items"]
                 if "spec" in item and "spec_file" in item.get("spec", {})]
    assert recorded, "no paths were recorded; this test is watching nothing"
    for value in recorded:
        assert value.startswith("exam/artifacts/"), value
        assert ".." not in value and "\\" not in value, value


def test_artifact_rel_refuses_a_path_outside_the_artefact_tree():
    """A helper that silently accepted anything would be a rule in name only."""
    from exam.model import ARTIFACTS, ExamError
    assert artifact_rel(os.path.join(ARTIFACTS, "papers", "x.json")) == \
        "exam/artifacts/papers/x.json"
    try:
        artifact_rel(os.path.join(REPO, "README.md"))
    except ExamError:
        return
    raise AssertionError("artifact_rel accepted a path outside exam/artifacts")


def test_verify_runs_the_match_stage_after_the_producers():
    """Order is the whole point: comparison before nothing, adoption never.

    Read off `exam/verify.py`'s own source rather than by running it -- the run
    takes minutes -- but the property pinned is structural: the match stage
    exists, and every producer stage is handed the shadow environment.
    """
    source = open(os.path.join(REPO, "exam", "verify.py"), encoding="utf-8").read()
    assert "artifacts_match_committed" in source
    assert "EXAM_ARTIFACTS_DIR" in source
    body = source.split("def main(", 1)[1]
    for producer in ("exam.tools.build_papers", "exam.tools.run_exam",
                     "exam.tools.run_selftest"):
        idx = body.index(producer)
        window = body[idx:idx + 400]
        assert "env=build_env" in window, (
            "%s runs without the shadow redirect, so it would overwrite the "
            "artefacts the match stage is there to compare" % producer)
