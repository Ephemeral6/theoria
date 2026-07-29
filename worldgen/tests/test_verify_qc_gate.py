"""Negative control for the QC gate: implant a red and require `verify` to exit 1.

`figures/check_coverage.py --self-test` is the shape this copies. It puts the
tree back the way it was before P8 and *requires* its probe to fire, on the
principle that a check which has never failed is a check nobody has any reason to
trust. This repository has been bitten by the alternative more than once: a gate
that computed the right verdict and then exited 0 anyway is, in evidence, the
same object as no gate at all. Until V12 that was literally this file's subject —
`worldgen/verify.py` judged both QC stages by `proc.returncode` alone, so an
honest miss and a crashed harness produced identical output and an exit code of
0.

So these tests are not "does `gate.compare` return a non-empty list". They spawn
`python -m worldgen.verify` and assert on **the process's exit code**, through
the shipped `main()`, the shipped mtime stamping, and the shipped aggregation.
The only substitution is the stage table and the pin file, via
`--selftest-spec` — `check_coverage`'s substitution of `sources.DISCOVERY`,
in the one form available across a process boundary.

Two disciplines that matter as much as the assertions:

* **A positive control.** `test_pinned_verdict_exits_zero` implants the pinned
  verdict and requires exit 0. Without it, every red assertion below would be
  satisfied by a gate that is simply always red, which is not a gate either.
* **The committed artifacts are never touched.** Every implanted stage writes
  into `tmp_path`; the real QC stages, which take minutes and rewrite ten files
  under `worldgen/out/qc/`, are never invoked. `test_out_tree_untouched` asserts
  that afterwards, by hashing the real artifacts before and after.
"""

import hashlib
import json
import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
WORLDGEN = os.path.dirname(HERE)
ROOT = os.path.dirname(WORLDGEN)

REAL_ARTIFACTS = (
    os.path.join(WORLDGEN, "out", "qc", "QC.json"),
    os.path.join(WORLDGEN, "out", "qc", "QC_MUTANTS.json"),
)

#: The verdict the implanted stage writes when it is behaving. Deliberately a
#: miss — the point is that a miss is *accepted when pinned* and rejected when
#: it is any other miss, not that misses are accepted or rejected wholesale.
PINNED_VERDICT = {
    "family_verdict": {"all_L1": False, "L3b_passed": 0, "pass": False},
    "worlds": {
        "w-good": {"verdict": {"L1_liveness": True, "L3a_replay": True}},
        "w-raises": {"verdict": {"L1_liveness": False, "L3a_replay": False}},
    },
}


def _pin(artifact):
    return {
        "stages": {
            "implanted": {
                "artifact": artifact,
                "bar": "worldgen/tests/test_verify_qc_gate.py",
                "status": "MISS",
                "owner": "the negative control",
                "verdict": {
                    "path": ["family_verdict"],
                    "expected": dict(PINNED_VERDICT["family_verdict"]),
                },
                "rows": {
                    "path": ["worlds"],
                    "subkey": "verdict",
                    "fields": ["L1_liveness", "L3a_replay"],
                    "expected": {
                        name: dict(row["verdict"])
                        for name, row in PINNED_VERDICT["worlds"].items()
                    },
                },
            }
        }
    }


def _writer(artifact, payload, exit_code):
    """A stub QC stage: write `payload` to `artifact`, then exit `exit_code`.

    `exit_code` is a parameter because `run_qc` exits 1 on an honest miss, and
    the gate must not be reading it. A stub that writes the pinned verdict and
    exits 1 has to be accepted; one that writes garbage and exits 0 has to be
    refused.
    """
    src = (
        "import json,sys;"
        "open(%r,'w',encoding='utf-8',newline='\\n')"
        ".write(json.dumps(%r));"
        "print('stub stage wrote its verdict');"
        "sys.exit(%d)" % (artifact, payload, exit_code)
    )
    return [sys.executable, "-c", src]


def _dead(message):
    """A stub QC stage that dies before writing anything — the crash case."""
    return [sys.executable, "-c",
            "import sys; sys.stderr.write(%r); sys.exit(1)" % message]


def _run(tmp_path, command, *, payload_on_disk=None, artifact_name="IMPLANT.json"):
    """Spawn the real `verify` with one implanted stage. Returns the CompletedProcess."""
    artifact = str(tmp_path / artifact_name)
    if payload_on_disk is not None:
        with open(artifact, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(payload_on_disk))
    pin_path = str(tmp_path / "PIN.json")
    with open(pin_path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(_pin(artifact), handle)
    spec_path = str(tmp_path / "SPEC.json")
    with open(spec_path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump({
            "pin": pin_path,
            "stages": [{
                "label": "IMPLANTED QC stage",
                "command": command(artifact),
                "gating": False,
                "stage_key": "implanted",
            }],
        }, handle)
    return subprocess.run(
        [sys.executable, "-m", "worldgen.verify", "--selftest-spec", spec_path],
        cwd=ROOT, capture_output=True, text=True)


# --------------------------------------------------------------------------
# the positive control: the gate is capable of being green
# --------------------------------------------------------------------------

def test_pinned_verdict_exits_zero(tmp_path):
    """The published miss, reproduced to the field, is accepted. Exit 0.

    This is half the negative control and not a formality. Without it the six
    tests below are equally satisfied by a `verify` that has been wedged red,
    and "it exits non-zero" would be evidence of nothing.

    The stub exits **1**, as `run_qc` does on an honest miss, so this also
    pins that the gate is no longer reading the process's exit code.
    """
    proc = _run(tmp_path, lambda a: _writer(a, PINNED_VERDICT, 1))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "[miss]" in proc.stdout
    assert "NOT a QC pass" in proc.stdout


def test_pinned_miss_is_not_reported_as_green(tmp_path):
    """Exit 0 is allowed to be quiet; the word `green` alone is not.

    The defect V12 was filed for was not only the exit code — it was that the
    final line of output was the bare token `green` while two pre-registered
    bars were missed and both artifacts said `pass: false`.
    """
    proc = _run(tmp_path, lambda a: _writer(a, PINNED_VERDICT, 1))
    last = [ln for ln in proc.stdout.strip().splitlines() if ln.strip()][-1]
    assert last.strip() != "green"
    assert "PINNED MISS" in proc.stdout


# --------------------------------------------------------------------------
# the negative controls: each implanted red must reach the exit code
# --------------------------------------------------------------------------

def test_worse_verdict_exits_nonzero(tmp_path):
    """A world that used to pass L1 starts raising. Must be red.

    Under the pre-V12 code this exact input printed `[miss]` and exited 0,
    identically to the pinned miss, because the only thing read was the stub's
    exit code.
    """
    worse = json.loads(json.dumps(PINNED_VERDICT))
    worse["worlds"]["w-good"]["verdict"]["L1_liveness"] = False
    proc = _run(tmp_path, lambda a: _writer(a, worse, 1))
    assert proc.returncode != 0, proc.stdout + proc.stderr
    assert "FAILED:" in proc.stdout
    assert "L1_liveness" in proc.stdout


def test_deviation_while_the_stage_exits_zero_is_still_red(tmp_path):
    """A stub that reports success and writes a different verdict. Must be red.

    This is the case the old code could not fail on under any circumstances: it
    would have printed `[ok  ]`. The gate must read the artifact, not the
    process.
    """
    lying = json.loads(json.dumps(PINNED_VERDICT))
    lying["family_verdict"]["pass"] = True
    lying["family_verdict"]["all_L1"] = True
    proc = _run(tmp_path, lambda a: _writer(a, lying, 0))
    assert proc.returncode != 0, proc.stdout + proc.stderr
    assert "FAILED:" in proc.stdout


def test_improvement_also_exits_nonzero(tmp_path):
    """A red that quietly went green makes the pin a lie. Must be red.

    Not pedantry: the pin's only value is as a true statement about what this
    territory ships, and the only way it stays true is if going stale is loud.
    The repair is to re-run QC and transcribe, never to widen the pin.
    """
    better = json.loads(json.dumps(PINNED_VERDICT))
    better["worlds"]["w-raises"]["verdict"] = {"L1_liveness": True,
                                               "L3a_replay": True}
    proc = _run(tmp_path, lambda a: _writer(a, better, 0))
    assert proc.returncode != 0, proc.stdout + proc.stderr
    assert "w-raises" in proc.stdout


def test_sample_shrunk_exits_nonzero(tmp_path):
    """Dropping the world that fails is the cheapest way to fake a pass."""
    shrunk = json.loads(json.dumps(PINNED_VERDICT))
    del shrunk["worlds"]["w-raises"]
    proc = _run(tmp_path, lambda a: _writer(a, shrunk, 0))
    assert proc.returncode != 0, proc.stdout + proc.stderr
    assert "sample shrank" in proc.stdout


def test_dead_stage_exits_nonzero(tmp_path):
    """The stage crashes before writing. Must be red, not `[miss]`.

    The defect this asserts against is precise: `run_qc` returns 1 for an honest
    miss and Python returns 1 for an uncaught ImportError, so the pre-V12 code
    reported a QC layer that had stopped executing altogether as a measured
    miss and exited 0.
    """
    proc = _run(tmp_path, lambda a: _dead("ImportError: no module named pipeline\\n"))
    assert proc.returncode != 0, proc.stdout + proc.stderr
    assert "wrote no verdict" in proc.stdout


def test_stale_artifact_exits_nonzero(tmp_path):
    """The stage crashes, but a *correct* artifact from an earlier run is on disk.

    The nastiest form of the crash case and the reason the gate stamps mtime
    rather than merely checking that the file parses: the verdict on disk is
    the pinned one, to the field, and it is a fossil.
    """
    proc = _run(tmp_path,
                lambda a: _dead("segfault-ish death after reading\\n"),
                payload_on_disk=PINNED_VERDICT)
    assert proc.returncode != 0, proc.stdout + proc.stderr
    assert "did not rewrite" in proc.stdout


# --------------------------------------------------------------------------
# the shipped table must actually be wired to the gate
# --------------------------------------------------------------------------

def test_every_shipped_qc_stage_is_pinned():
    """Nothing above constrains the real STAGES table; this does.

    A future edit that sets `stage_key=None` on a QC stage would restore the
    exact defect V12 was filed for and pass every test in this file.
    """
    from worldgen import verify
    from worldgen.qc import gate

    qc_stages = [s for s in verify.STAGES if s[0].startswith("QC")]
    assert len(qc_stages) == 2
    pin = gate.load_pin()
    for label, _command, gating, stage_key in qc_stages:
        assert stage_key is not None, (
            "%s is judged by its exit code again — a crash and a miss are the "
            "same signal there, which is the V12 defect" % label)
        assert not gating, (
            "%s gates on `pass`; the reds are upstream in cold-start-a0 and "
            "this territory cannot repair them — see verify.py's docstring"
            % label)
        assert stage_key in pin["stages"]
        stage = pin["stages"][stage_key]
        assert os.path.exists(os.path.join(WORLDGEN, stage["artifact"]))
        for field in ("owner", "bar", "status"):
            assert stage.get(field), "%s pin is missing %s" % (stage_key, field)


def test_pin_matches_what_the_committed_artifacts_say():
    """The pin is a transcription, so it must agree with the artifacts on disk.

    Catches the pin being edited to silence a red without re-running QC — the
    one move `KNOWN_MISS.json._how_to_change_it` forbids by name.
    """
    from worldgen.qc import gate

    pin = gate.load_pin()
    for stage_key, stage in pin["stages"].items():
        artifact = os.path.join(WORLDGEN, stage["artifact"])
        with open(artifact, "r", encoding="utf-8") as handle:
            report = json.load(handle)
        problems = gate.compare(stage, report)
        assert not problems, "%s: %s" % (stage_key, problems)


def test_the_pinned_reds_are_still_red():
    """Both pinned stages must record `pass: false`.

    If this ever fails the news is good, and it still has to stop the build: the
    documented non-gating decision was made *about a miss*, and it does not
    survive the miss going away.
    """
    from worldgen.qc import gate

    pin = gate.load_pin()
    for stage_key, stage in pin["stages"].items():
        assert stage["verdict"]["expected"]["pass"] is False, stage_key
        assert stage["status"] == "MISS"


@pytest.mark.parametrize("artifact", REAL_ARTIFACTS)
def test_out_tree_untouched(artifact, tmp_path):
    """Running this file's implants must not write a byte under `worldgen/out/`.

    The real QC stages rewrite ten files under `out/qc/` on every run (see
    `runs/…-V12-…/JUDGMENT.md`), so a negative control that invoked them would
    dirty the catalogue every time the suite ran.
    """
    before = hashlib.sha256(open(artifact, "rb").read()).hexdigest()
    proc = _run(tmp_path, lambda a: _writer(a, PINNED_VERDICT, 1))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    after = hashlib.sha256(open(artifact, "rb").read()).hexdigest()
    assert before == after, "%s was rewritten by the negative control" % artifact
