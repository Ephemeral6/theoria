"""The probe's own negative control.

A probe that has never been watched going red is the 129th instance of the defect
it was written to find. So: build a tree containing a new gate with no negative
control and require a non-zero exit; add one and require zero.

That much is table stakes, and V12 showed it is not enough. A gate can be red for
a reason unrelated to the thing it claims to check. The second half of this file
is the harder question -- **is the probe's own logic load-bearing?** Each planted
red is replayed against a deliberately weakened probe, and the test asserts the
weak version *lets it through*. If a weakened probe caught the same reds, the
strength being claimed would be somewhere else.
"""

from __future__ import annotations

import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
NEGCTL = os.path.dirname(HERE)
sys.path.insert(0, NEGCTL)

import criterion  # noqa: E402
import probe      # noqa: E402


# --------------------------------------------------------------------------
# Synthetic trees
# --------------------------------------------------------------------------

#: An acceptance entry point: runnable, and able to leave the process non-zero.
GATE = '''\
"""A gate. It refuses a manifest whose declared hash does not match."""
import hashlib
import sys


def check(manifest, blob):
    want = manifest.get("sha256")
    got = hashlib.sha256(blob).hexdigest()
    return [] if want == got else ["sha256: declared %s, measured %s" % (want, got)]


def main(argv=None):
    problems = check({"sha256": "0" * 64}, b"")
    for p in problems:
        print(p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
'''

#: A real negative control: bad input constructed, failure asserted.
REAL_NEGATIVE_CONTROL = '''\
import newgate


def test_a_wrong_hash_is_refused():
    problems = newgate.check({"sha256": "beef"}, b"not-beef")
    assert problems != []


def test_a_matching_hash_is_accepted():
    import hashlib
    blob = b"x"
    ok = newgate.check({"sha256": hashlib.sha256(blob).hexdigest()}, blob)
    assert ok == []
'''

#: Tests that exercise the gate and never once make it fail. This is the shape
#: the census found 35 times: the happy path, asserted, and nothing else.
POSITIVE_CONTROL_ONLY = '''\
import hashlib

import newgate


def test_the_checker_runs():
    blob = b"x"
    ok = newgate.check({"sha256": hashlib.sha256(blob).hexdigest()}, blob)
    assert ok == []


def test_it_returns_a_list():
    assert isinstance(newgate.check({"sha256": "a"}, b"a"), list)
'''

#: A test whose *name* promises a negative control and whose body asserts
#: nothing of the kind. The naive criterion cannot tell this from the real one.
NAME_ONLY = '''\
import newgate


def test_the_gate_rejects_a_bad_manifest_and_fails_loudly():
    result = newgate.check({"sha256": "a"}, b"a")
    assert isinstance(result, list)
'''


def _tree(tmp_path, tests: str = None, extra: dict = None) -> str:
    root = tmp_path / "tree"
    (root / "tests").mkdir(parents=True)
    (root / "newgate.py").write_text(GATE, encoding="utf-8")
    if tests is not None:
        (root / "tests" / "test_newgate.py").write_text(tests, encoding="utf-8")
    for name, body in (extra or {}).items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    return str(root)


def _pin(tmp_path, entries: dict, name: str = "pin.json") -> str:
    path = tmp_path / name
    path.write_text(json.dumps({"entries": entries}, indent=2), encoding="utf-8")
    return str(path)


def _run(root, pin, detector="A-B", gating=probe.GATING):
    original = probe.GATING
    probe.GATING = gating
    try:
        return probe.run(root=root, pin_path=pin, detector=detector)
    finally:
        probe.GATING = original


# --------------------------------------------------------------------------
# The two the item asks for
# --------------------------------------------------------------------------


def test_a_new_gate_without_a_negative_control_is_red(tmp_path):
    """The planted defect: a gate arrives, nothing has ever shown it failing."""
    report = _run(_tree(tmp_path, tests=None), _pin(tmp_path, {}))
    assert report["exit_code"] == 1
    assert "newgate.py" in report["red"]
    kinds = {f["path"]: f["kind"] for f in report["findings"]}
    assert kinds["newgate.py"] == probe.NEW_GAP


def test_the_same_gate_with_a_negative_control_is_green(tmp_path):
    """The repair, and the probe must be able to see it. A probe that stays red
    after the fix teaches people to ignore it just as fast as one that never
    goes red at all."""
    report = _run(_tree(tmp_path, tests=REAL_NEGATIVE_CONTROL), _pin(tmp_path, {}))
    assert report["exit_code"] == 0
    kinds = {f["path"]: f["kind"] for f in report["findings"]}
    assert kinds["newgate.py"] == probe.NEW_OK


def test_positive_controls_alone_do_not_count(tmp_path):
    """"There are tests for it" is the thing the census found was not enough."""
    report = _run(_tree(tmp_path, tests=POSITIVE_CONTROL_ONLY), _pin(tmp_path, {}))
    assert report["exit_code"] == 1
    assert "newgate.py" in report["red"]


def test_a_negative_control_that_is_deleted_is_a_regression(tmp_path):
    """Pinned `present`, then the demonstration goes away."""
    pin = _pin(tmp_path, {"newgate.py": {"verdict": "present", "owner": "test"}})
    green = _run(_tree(tmp_path, tests=REAL_NEGATIVE_CONTROL), pin)
    assert green["exit_code"] == 0

    red = _run(_tree(tmp_path / "b", tests=POSITIVE_CONTROL_ONLY), pin)
    assert red["exit_code"] == 1
    kinds = {f["path"]: f["kind"] for f in red["findings"]}
    assert kinds["newgate.py"] == probe.REGRESSION


def test_a_pinned_gap_stays_quiet(tmp_path):
    """Somebody else's 35 gaps must not make this probe permanently red, or the
    first thing anyone does with it is turn it off."""
    pin = _pin(tmp_path, {"newgate.py": {"verdict": "absent", "owner": "somebody else",
                                         "note": "pre-existing"}})
    report = _run(_tree(tmp_path, tests=None), pin)
    assert report["exit_code"] == 0
    kinds = {f["path"]: f["kind"] for f in report["findings"]}
    assert kinds["newgate.py"] == probe.PINNED_OK


def test_closing_a_pinned_gap_is_reported_and_does_not_gate(tmp_path):
    pin = _pin(tmp_path, {"newgate.py": {"verdict": "absent", "owner": "somebody else"}})
    report = _run(_tree(tmp_path, tests=REAL_NEGATIVE_CONTROL), pin)
    assert report["exit_code"] == 0
    kinds = {f["path"]: f["kind"] for f in report["findings"]}
    assert kinds["newgate.py"] == probe.IMPROVED


# --------------------------------------------------------------------------
# The proof that the reds above are about this probe
# --------------------------------------------------------------------------


def test_the_planted_red_slips_past_a_probe_that_only_watches_regressions(tmp_path):
    """Weakening: drop NEW_GAP from the gating set.

    That is the obvious "less annoying" version of this probe -- only complain
    when something that used to have a negative control loses it. It is exactly
    the version that cannot see a gate arriving without one, which is the whole
    reason V11's count will grow. If this test ever starts failing, the NEW_GAP
    rule has stopped being load-bearing.
    """
    root, pin = _tree(tmp_path, tests=None), _pin(tmp_path, {})
    assert _run(root, pin)["exit_code"] == 1
    weakened = _run(root, pin, gating=(probe.REGRESSION,))
    assert weakened["exit_code"] == 0, (
        "the weakened probe caught the planted gap too, so the strength being "
        "claimed for NEW_GAP is coming from somewhere else")


def test_the_planted_red_slips_past_the_name_only_criterion(tmp_path):
    """Weakening: judge by the test function's name, as the first draft did.

    `figures/verify.sh` gate 7's first version was a regex whose first finding
    was a docstring. The same trap is here: `test_the_gate_rejects_a_bad_
    manifest_and_fails_loudly` asserts only `isinstance(result, list)`.
    """
    root, pin = _tree(tmp_path, tests=NAME_ONLY), _pin(tmp_path, {})
    assert _run(root, pin)["exit_code"] == 1, (
        "the shipped probe did not catch a negative control that is only a name")
    weakened = _run(root, pin, detector="N")
    assert weakened["exit_code"] == 0, (
        "the name-only criterion caught it too -- then the structural rules in "
        "criterion.py are not what is doing the work")


def test_the_regression_slips_past_a_probe_with_no_pin_comparison(tmp_path):
    """Weakening: treat every measurement as the baseline (a pin that is rewritten
    on every run). This is the shape of an auto-regenerated pin, and it is why
    KNOWN_GAPS.json is written by hand."""
    pin = _pin(tmp_path, {"newgate.py": {"verdict": "present", "owner": "test"}})
    root = _tree(tmp_path, tests=POSITIVE_CONTROL_ONLY)
    assert _run(root, pin)["exit_code"] == 1
    self_pinned = _pin(tmp_path, {"newgate.py": {"verdict": "absent", "owner": "test"}},
                       name="pin_regenerated.json")
    assert _run(root, self_pinned)["exit_code"] == 0, (
        "re-pinning the measurement did not silence the regression, so the pin "
        "comparison is not what produced the red")


# --------------------------------------------------------------------------
# The criterion's own edges, pinned so a future loosening is visible
# --------------------------------------------------------------------------


@pytest.mark.parametrize("body,expected", [
    ("assert main([]) == 1", True),
    ("assert len(rows) == 6", False),               # a count, not an exit code
    ("assert report['pass'] is False", True),
    ("assert not violations", False),               # a positive control
    ("assert not report['ok']", True),
    ("assert problems != []", True),
    ("assert rows != []", False),
    ("with pytest.raises(ValueError):\n        f()", True),
    ("assert any('bad' in e for e in errors)", True),
    ("assert any('x' in r for r in rows)", False),
    ("assert secret not in blob", True),
    ("assert result == 'FAIL'", True),
    ("assert value == 'ok'", False),
])
def test_the_failure_assertion_vocabulary_is_pinned(body, expected):
    """The exact list of shapes that count. Two of these -- `len(rows) == 6` and
    `not violations` -- were scored as failure assertions by the first draft, and
    each produced one false `present` in the calibration."""
    import ast
    src = "def test_x():\n    " + body.replace("\n", "\n") + "\n"
    fn = ast.parse(src).body[0]
    assert bool(criterion._failure_assertion(fn)) is expected


def test_the_containment_rule_can_be_switched_off():
    """`assert secret not in blob` is the loosest rule here; the calibration
    measures the tree with and without it, so it has to be separable."""
    import ast
    fn = ast.parse("def test_x():\n    assert secret not in blob\n").body[0]
    assert criterion._failure_assertion(fn, absence=True)
    assert criterion._failure_assertion(fn, absence=False) is None


@pytest.mark.parametrize("candidate,importer,ok", [
    # An ancestor directory of the importer -- what `sys.path.insert(0, <root>)` buys.
    ("newgate.py", "tests/test_newgate.py", True),
    ("engine-rig/tools/run_all.py", "engine-rig/tests/test_x.py", True),
    ("monitor/gates.py", "monitor/tests/test_gates.py", True),
    # Another track's file that happens to share a filename. Both halves of the
    # defect the adversarial pass confirmed: the ambiguous one (four run_all.py)
    # and the single-candidate one (one worldgen/generate.py, one
    # fuzzlab/props/fd_adapter.py) that the first guard never reached.
    ("cold-start-a0/run_all.py", "ablation-arm/tests/test_exhibits.py", False),
    ("worldgen/generate.py", "a0-spike/tests/test_a0.py", False),
    ("fuzzlab/props/fd_adapter.py", "engine-rig/tests/test_fd_adapter.py", False),
    ("engine-rig/engines/fd_adapter/validate.py", "worldgen/tests/test_mutate.py", False),
    ("cold-start-a2/a2pipeline/engines.py", "engine-rig/tests/test_bench.py", False),
])
def test_a_binding_never_reaches_into_another_territory(candidate, importer, ok):
    """A wrongly resolved import is a false `present`, and a false `present` is
    the error direction that makes this probe *silent* about a real gap while
    handing one track's negative control to another. An unresolved one is only
    noise. The asymmetry is why this refuses rather than guesses."""
    assert criterion.Index.reachable(candidate, importer) is ok


def test_no_binding_in_this_repository_crosses_a_territory():
    """The live check, on the real tree rather than on examples. The adversarial
    pass counted 54 cross-territory bindings at commit b6d8643, of which 14 were
    engine-rig tests being credited to fuzzlab."""
    import ast
    index = criterion.Index.build(probe.REPO)
    crossings = []
    for rel in index.files:
        if not criterion.is_test_file(rel):
            continue
        try:
            tree = ast.parse(open(os.path.join(index.root, rel),
                                  encoding="utf-8").read())
        except (OSError, SyntaxError, UnicodeDecodeError):
            continue
        for name, target in criterion.bindings(tree, rel, index).items():
            if target.split("/")[0] != rel.split("/")[0]:
                crossings.append("%s: %s -> %s" % (rel, name, target))
    assert crossings == [], crossings[:10]


def test_the_probe_is_subject_to_its_own_rule():
    """`verify-lab/negctl/probe.py` is an acceptance entry point by its own
    enumerator, and it is in its own pin. An exemption here would be the whole
    disease in one line."""
    pin = json.load(open(probe.DEFAULT_PIN, encoding="utf-8"))["entries"]
    assert "verify-lab/negctl/probe.py" in pin
