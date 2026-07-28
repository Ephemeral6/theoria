"""The negative controls for the invariant gate, through the real command line.

`test_invariant_status.py` asserts what `classify_invariants` returns.  That is
not enough and this territory has the receipts: `build.gate_failures` computed
every one of its verdicts correctly and returned 0 regardless until C1's audit,
and `check_determinism` was a function with no caller until V16.  A verdict
nothing exits on is a decoration.  So everything here runs
`python -m worldgen.build <world>` in a patched copy of the package and asserts
on the **process exit code** and on **which gate line the build printed**.

The table below is the deliverable.  Read it as three blocks:

* **no weakening** — the repair as shipped.  A prose-only invariant is refused;
  a genuinely violated one is still refused *and still called a violation*; a
  well-formed invariant that holds is still allowed through.
* **`pre_v19`** — the boolean put back.  `prose_only` sails through, which is
  the historical defect reproduced on demand, and `violated_state` is still
  caught, which is the part of the old gate that was working and which the
  repair must not have traded away.
* **the partial weakenings** — which single piece of the repair carries the
  catch.  `boolean_default` alone does not let the defect back through, because
  the separate gate key still fires; `unverified_sinks_to_holds` and
  `drop_unverified_gate` each do.

Mechanics, and the disciplines the sandbox is held to, are in
`invariant_sandbox.py`.
"""

import pytest

from worldgen.tests import invariant_sandbox as ivs

UNVERIFIED = ivs.UNVERIFIED_KEY
VIOLATED = ivs.VIOLATED_KEY


@pytest.fixture(scope="session")
def sandbox(tmp_path_factory):
    """One sandbox per (injection, weakening) pair, built once and shared."""
    cache = {}

    def get(injection=None, weakening=None):
        key = (injection, weakening)
        if key not in cache:
            label = "-".join(p for p in (injection, weakening) if p) or "clean"
            root = str(tmp_path_factory.mktemp("v19-" + label[:24]))
            cache[key] = ivs.make_sandbox(root, injection, weakening)
        return cache[key]

    return get


@pytest.fixture(scope="session")
def scratch(tmp_path_factory):
    def get(label):
        return str(tmp_path_factory.mktemp("v19-out-" + label[:24]))

    return get


def _run(sandbox, scratch, injection=None, weakening=None):
    label = "-".join(p for p in (injection, weakening) if p) or "clean"
    root = sandbox(injection, weakening)
    proc = ivs.run_build(root, scratch(label))
    return proc, ivs.text(proc), ivs.gate_lines(proc)


# --- the clean control ------------------------------------------------------

def test_an_unpatched_sandbox_builds_green(sandbox, scratch):
    """Without this every red below could be the sandbox rather than the gate."""
    proc, out, _lines = _run(sandbox, scratch)
    assert proc.returncode == 0, out[-3000:]
    assert ivs.GREEN_BANNER in out, out[-3000:]


# --- (a) unverified must be refused ----------------------------------------

@pytest.mark.parametrize("injection",
                         ["prose_only", "prose_only_explicit_none"])
def test_a_prose_only_invariant_cannot_pass_the_gate(injection, sandbox, scratch):
    """The work order's first negative sample, on a real exit code.

    Both spellings: the key omitted, and `"check": None` written out — which is
    how all three real ones were written, so a repair that keyed off the missing
    key would have caught nothing that actually shipped.
    """
    proc, out, lines = _run(sandbox, scratch, injection)
    assert proc.returncode == 1, (
        "the build accepted an invariant nobody exercised:\n" + out[-3000:])
    assert ivs.RED_BANNER in out, out[-3000:]
    assert any(UNVERIFIED in line for line in lines), lines
    assert not any(VIOLATED in line for line in lines), (
        "an unverified invariant was reported as a violation — the two classes "
        "have been merged, which is the over-correction: %s" % (lines,))


# --- (b) violated must still be refused, and still called a violation -------

@pytest.mark.parametrize("injection", ["violated_state", "violated_edge"])
def test_a_genuinely_violated_invariant_is_still_caught_as_one(injection,
                                                               sandbox, scratch):
    """The work order's second negative sample: do not fix conservatism by
    refusing everything.

    A repair that answered "unverified is not true" by rejecting every
    invariant would pass the test above and fail here only in *which* gate line
    it printed — so the assertion is on the gate key, not on the exit code
    alone.
    """
    proc, out, lines = _run(sandbox, scratch, injection)
    assert proc.returncode == 1, out[-3000:]
    assert any(VIOLATED in line for line in lines), lines
    assert not any(UNVERIFIED in line for line in lines), (
        "a violated invariant was filed as merely unverified: %s" % (lines,))


# --- the positive controls --------------------------------------------------

@pytest.mark.parametrize("injection", ["holds_state", "holds_edge"])
def test_a_well_formed_invariant_that_holds_is_not_refused(injection,
                                                            sandbox, scratch):
    """The gate is not "reject anything unusual". Both seams, because the
    `edge_check` seam is new and a new seam that is red on everything is as
    useless as one that is green on everything."""
    proc, out, _lines = _run(sandbox, scratch, injection)
    assert proc.returncode == 0, (
        "an invariant that holds was refused — the repair is over-conservative:\n"
        + out[-3000:])
    assert ivs.GREEN_BANNER in out, out[-3000:]


# --- the weakenings: proof the controls are not idling ----------------------

@pytest.mark.parametrize("injection",
                         ["prose_only", "prose_only_explicit_none"])
def test_putting_the_boolean_back_lets_the_defect_through(injection,
                                                          sandbox, scratch):
    """Change the three-state back to `all(i.get("holds", True) ...)` and the
    prose-only invariant is accepted again. This is the historical defect,
    reproduced on demand: without it, the tests above could be passing because
    the build is red for some unrelated reason."""
    proc, out, _lines = _run(sandbox, scratch, injection, "pre_v19")
    assert proc.returncode == 0, (
        "the pre-V19 gate refused the prose-only invariant, so the control "
        "above proves nothing about the repair:\n" + out[-3000:])
    assert ivs.GREEN_BANNER in out, out[-3000:]


def test_the_pre_v19_gate_did_still_catch_real_violations(sandbox, scratch):
    """The old gate was not blind — it caught violations and only violations.

    Worth pinning, because it is the reason the repair had to add a class
    rather than tighten a threshold, and the reason `invariant_failures` kept
    its old meaning instead of being widened to swallow the new one.
    """
    proc, out, lines = _run(sandbox, scratch, "violated_state", "pre_v19")
    assert proc.returncode == 1, out[-3000:]
    assert any(VIOLATED in line for line in lines), lines


def test_bypassing_the_unverified_sink_reproduces_the_bug(sandbox, scratch):
    """The three-way split's own failure mode: a third class nothing reaches.

    `classify_invariants` files anything it does not recognise under
    `unverified`. Point that branch at `holds` instead and the schema still has
    three names, the JSON still has an `invariant_status` key with three lists,
    and the defect is back — which is why the partition test in
    `test_invariant_status.py` is asserted on adversarial rows rather than on
    the catalogue, where every row is well-formed.
    """
    proc, out, _lines = _run(sandbox, scratch, "prose_only",
                             "unverified_sinks_to_holds")
    assert proc.returncode == 0, (
        "bypassing the sink did not reproduce the defect, so the sink is not "
        "what catches it and this control is measuring something else:\n"
        + out[-3000:])


def test_the_gate_key_is_what_exits_not_merely_what_is_reported(sandbox, scratch):
    """Remove `invariant_unverified` from `GATES` and change nothing else.

    The manifest still reports the unverified worlds honestly; nothing exits on
    them. Both of this territory's previous findings had this exact shape.
    """
    proc, out, _lines = _run(sandbox, scratch, "prose_only",
                             "drop_unverified_gate")
    assert proc.returncode == 0, out[-3000:]
    assert "invariant_unverified" in out, (
        "the manifest stopped reporting the class as well, so this weakening "
        "removes more than the exit and does not isolate it:\n" + out[-3000:])


def test_the_boolean_alone_is_not_what_catches_it(sandbox, scratch):
    """`boolean_default` reverts only `all_invariants_hold`. The build stays red.

    Recorded because it is a genuine finding about the repair and not a
    flattering one: the conjunction is *not* what stops the defect at the gate —
    the separate `GATES` key is. Anyone who repairs only `truth.py` next time
    will believe they have fixed this and will have fixed the reporting alone.
    """
    proc, out, lines = _run(sandbox, scratch, "prose_only", "boolean_default")
    assert proc.returncode == 1, out[-3000:]
    assert any(UNVERIFIED in line for line in lines), lines
