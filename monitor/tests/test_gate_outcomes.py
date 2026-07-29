"""Injection self-test for the gate runner.

Every probe in this repo now owes an answer to one question: *can you prove you
go red?*  Four checks were caught on 2026-07-28 failing quietly in the
reassuring direction, and none of them had a test that manufactured the failure
they were supposed to catch.  So each outcome `gates.run` can return is
produced here on purpose, in a throwaway checkout, and asserted.

A gate runner that cannot demonstrate its own red is a negative asset: it adds
a green light without adding an observation.
"""

import json
import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gates                                                # noqa: E402


def _repo(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    return str(tmp_path)


def _territory(root, name, files):
    d = os.path.join(root, name)
    os.makedirs(d, exist_ok=True)
    for rel, body in files.items():
        p = os.path.join(d, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(body)
    return d


PASS_TEST = "def test_ok():\n    assert True\n"
FAIL_TEST = "def test_no():\n    assert False, 'manufactured failure'\n"
PASS_VERIFY = "import sys\nprint('gate green')\nsys.exit(0)\n"
FAIL_VERIFY = "import sys\nprint('gate says no')\nsys.exit(1)\n"


# ------------------------------------------------------------------ the pass

def test_green_territory_is_ok(tmp_path):
    root = _repo(tmp_path)
    _territory(root, "good", {"test_a.py": PASS_TEST, "verify.py": PASS_VERIFY})
    outcome, detail = gates.run(root, "good")
    assert outcome == "ok", detail
    assert detail == "verify:good(verify.py)"


# ---------------------------------------------------------------- the reds

def test_failing_suite_is_red(tmp_path):
    """With no verify script the suite *is* the gate, so it must be able to fail."""
    root = _repo(tmp_path)
    _territory(root, "bad", {"test_a.py": FAIL_TEST})
    outcome, detail = gates.run(root, "bad")
    assert outcome == "red", detail
    assert "pytest:bad" in detail


def test_a_verify_script_supersedes_the_suite(tmp_path):
    """S13's call, kept: every gate in this repo runs its own suite first.

    Running both would double the slowest part of a merge to re-check what the
    gate just checked, and a merge rig that is slow gets bypassed.  The cost is
    real and worth naming: a red suite next to a green verify script reads as
    green here, because the verify script is held responsible for its own tests.
    """
    root = _repo(tmp_path)
    _territory(root, "both2", {"test_a.py": FAIL_TEST, "verify.py": PASS_VERIFY})
    outcome, _ = gates.run(root, "both2")
    assert outcome == "ok"


def test_failing_verify_script_is_red(tmp_path):
    root = _repo(tmp_path)
    _territory(root, "bad", {"test_a.py": PASS_TEST, "verify.py": FAIL_VERIFY})
    outcome, detail = gates.run(root, "bad")
    assert outcome == "red"
    assert "exited 1" in detail
    assert "gate says no" in detail


def test_verify_script_runs_even_without_tests(tmp_path):
    """A territory with no suite is still gated by its verify script.

    The old merge gate keyed entirely off "does this directory hold test_*.py",
    so a territory whose gate was a script and not a suite went through
    untested.  ablation-arm is exactly that shape.
    """
    root = _repo(tmp_path)
    _territory(root, "scriptonly", {"verify.py": FAIL_VERIFY})
    outcome, detail = gates.run(root, "scriptonly")
    assert outcome == "red", detail


# --------------------------------------------------------------- the brokens

def test_tests_that_collect_nothing_are_broken_not_green(tmp_path):
    """pytest exit 5 is "I ran nothing", and it must not read as "I passed"."""
    root = _repo(tmp_path)
    d = _territory(root, "misconfigured", {"test_a.py": PASS_TEST})
    os.makedirs(os.path.join(d, "elsewhere"))
    with open(os.path.join(d, "pytest.ini"), "w", encoding="utf-8") as fh:
        fh.write("[pytest]\ntestpaths = elsewhere\n")
    outcome, detail = gates.run(root, "misconfigured")
    assert outcome == "broken", detail
    assert "collected nothing" in detail


def test_hanging_gate_is_broken_not_green(tmp_path):
    root = _repo(tmp_path)
    _territory(root, "hangs", {"verify.py": "import time\ntime.sleep(60)\n"})
    outcome, detail = gates.run(root, "hangs", timeout=3)
    assert outcome == "broken", detail
    assert "timed out" in detail


def test_shell_gate_without_bash_is_broken_not_skipped(tmp_path, monkeypatch):
    """No interpreter for the gate means the gate did not run.

    The tempting behaviour -- skip it and merge on -- is the exact shape of the
    failure this whole task exists to close.
    """
    root = _repo(tmp_path)
    _territory(root, "shellgate", {"verify.sh": "exit 0\n"})
    # `_runner` picks the interpreter, so the absence has to be injected
    # there: master replaced the PATH lookup with explicit Git Bash
    # candidates, and patching `shutil.which` alone stopped meaning anything
    # while this test went on passing.
    monkeypatch.setattr(gates, "_bash", lambda: "bash")
    monkeypatch.setattr(gates.shutil, "which", lambda *_a, **_k: None)
    outcome, detail = gates.run(root, "shellgate")
    assert outcome == "broken", detail
    assert "no bash" in detail


# ----------------------------------------------------------------- the dirty

def test_gate_that_writes_into_the_tree_is_dirty(tmp_path):
    """The gate may not dirty the workspace it is checking.

    ablation-arm's first verify.sh dropped files into artifacts/ and turned the
    arm's own read-only test red -- the gate broke the thing it was guarding.
    """
    root = _repo(tmp_path)
    _territory(root, "messy", {
        "verify.py": ("import pathlib\n"
                      "pathlib.Path('dropping.txt').write_text('x')\n"),
    })
    outcome, detail = gates.run(root, "messy")
    assert outcome == "dirty", detail
    assert "dropping.txt" in detail
    assert os.path.exists(os.path.join(root, "messy", "dropping.txt"))


def test_regenerating_a_tracked_artefact_is_drift_not_dirty(tmp_path):
    """The committed artefact no longer matches what the code produces.

    Both gates that exist today do this -- ablation-arm rewrites
    artifacts/verify.json, arc-recon rewrites data/claim_set.json -- so it is
    reported under its own name rather than blocking every pending branch on a
    pre-existing condition.  A check that stalls the whole pipeline on day one
    is switched off by day two.
    """
    root = _repo(tmp_path)
    d = _territory(root, "regen", {
        "artifact.json": '{"green": true}\n',
        "verify.py": ("import pathlib\n"
                      "pathlib.Path('artifact.json').write_text('{\"green\": false}\\n')\n"),
    })
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                    "commit", "-qm", "baseline"], cwd=root, check=True)
    outcome, detail = gates.run(root, "regen")
    assert outcome == "drift", detail
    assert "artifact.json" in detail
    assert os.path.isdir(d)


def test_drift_lets_a_merge_through_but_strict_does_not(tmp_path):
    assert "drift" in gates.PASSING, \
        "drift must not block merges: both existing gates would stall every branch"
    assert "drift" not in gates.STRICT_PASSING, \
        "drift must still fail for the territory owner running --strict"


def test_interpreter_caches_do_not_count_as_dirt(tmp_path):
    """__pycache__ is the interpreter's, not the gate's.

    Counting it would paint every gated territory dirty on the first run and
    the signal would be thrown away inside a day -- a check nobody believes is
    worth no more than a check that never runs.
    """
    root = _repo(tmp_path)
    _territory(root, "cached", {
        "verify.py": ("import os, pathlib\n"
                      "os.makedirs('__pycache__', exist_ok=True)\n"
                      "pathlib.Path('__pycache__/x.cpython-313.pyc')"
                      ".write_text('cache')\n"),
    })
    outcome, detail = gates.run(root, "cached")
    assert outcome == "ok", detail
    assert os.path.isdir(os.path.join(root, "cached", "__pycache__")), \
        "the run should really have produced the cache this test excuses"
    assert gates._ephemeral("cached/__pycache__/x.cpython-313.pyc")
    assert not gates._ephemeral("cached/artifacts/real_dropping.json")


def test_gate_using_a_tempdir_is_not_dirty(tmp_path):
    root = _repo(tmp_path)
    _territory(root, "tidy", {
        "verify.py": ("import pathlib, tempfile\n"
                      "d = tempfile.mkdtemp()\n"
                      "pathlib.Path(d, 'out.txt').write_text('x')\n"),
    })
    outcome, detail = gates.run(root, "tidy")
    assert outcome == "ok", detail


# ------------------------------------------------------- absent and unknown

def test_territory_without_a_gate_is_absent_not_ok(tmp_path):
    root = _repo(tmp_path)
    _territory(root, "bare", {"README.md": "no gate here\n"})
    outcome, detail = gates.run(root, "bare")
    assert outcome == "absent", detail


def test_tests_only_is_gated_by_its_suite_and_says_so(tmp_path):
    """A suite is a weaker gate than a verify script, and the log must show which.

    A suite says the code does what its author thought; a completion gate says
    the territory's real pipeline ran and its artefacts carry the fields they
    claim.  S13's answer is not to conflate them but to name them apart in the
    merge log -- `pytest:x` is not `verify:x` is not `UNGATED:x` -- so a reader
    can tell how much checking a merge actually got.
    """
    root = _repo(tmp_path)
    _territory(root, "testsonly", {"test_a.py": PASS_TEST})
    outcome, detail = gates.run(root, "testsonly")
    assert outcome == "ok", detail
    assert detail == "pytest:testsonly"
    assert gates.describe(gates.gate_for(root, "testsonly"), "testsonly")         != gates.describe({"kind": "verify", "name": "verify.py"}, "testsonly")


def test_missing_territory_is_unknown(tmp_path):
    root = _repo(tmp_path)
    outcome, _ = gates.run(root, "nowhere")
    assert outcome == "unknown"


# ------------------------------------------------------------- the encoding

def test_utf8_gate_output_does_not_crash_the_runner(tmp_path):
    """The cp936 trap, pinned.

    `text=True` without an explicit encoding decodes with the host locale; this
    fleet runs on a cp936 box, and a child printing UTF-8 either mojibakes or
    raises UnicodeDecodeError inside subprocess.run.  A checker that dies while
    decoding its child is a checker that did not check -- that mismatch reported
    eight live workers as dead earlier today.
    """
    root = _repo(tmp_path)
    _territory(root, "chinese", {
        "verify.py": ("import sys\n"
                      "sys.stdout.buffer.write('闸门未通过：产物缺字段\\n'"
                      ".encode('utf-8'))\n"
                      "sys.exit(1)\n"),
    })
    outcome, detail = gates.run(root, "chinese")
    assert outcome == "red", detail
    assert "闸门未通过" in detail


# ------------------------------------------------------------- verdict order

def test_severity_ordering_puts_every_non_pass_above_ok():
    for name in ("red", "broken", "dirty"):
        assert gates.SEVERITY[name] > gates.SEVERITY["ok"]
        assert name not in gates.PASSING
    assert "absent" in gates.PASSING


def test_gate_for_reads_the_tree_not_a_list(tmp_path):
    """A territory that grows a gate is gated from that moment, with no edit here."""
    root = _repo(tmp_path)
    d = _territory(root, "grows", {"README.md": "x\n"})
    assert gates.gate_for(root, "grows")["kind"] == "none"
    with open(os.path.join(d, "verify.py"), "w", encoding="utf-8") as fh:
        fh.write(PASS_VERIFY)
    assert gates.gate_for(root, "grows")["kind"] == "verify"


def test_canonical_order_is_sh_then_py(tmp_path):
    root = _repo(tmp_path)
    _territory(root, "both", {"verify.py": PASS_VERIFY, "verify.sh": "exit 1\n"})
    assert gates.gate_for(root, "both")["name"] == "verify.sh"
