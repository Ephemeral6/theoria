"""The negative control for `worldgen.build.check_determinism`.

`test_determinism.py` is the *in-process* half: two builds in one interpreter
produce the same bytes.  The half that matters — a rebuild in a fresh
interpreter at a different `PYTHONHASHSEED`, which is the only way to see
hash-order leakage — lives in `build.check_determinism`, and before V16 nothing
in this repository had ever made it fire.  It was measured, not assumed: a
tripwire that raised on entry to that function left all 412 tests green, and
`exam/` and `theory-compiler/`'s worldgen-facing tests too.  Its only caller is
`build.main` under `--check`, and `main`'s only caller is `worldgen/verify.py`,
which no test runs.  "Determinism is a requirement, not a nicety" is in
`CLAUDE.md`; the strongest check of it was a light nobody had ever put a hand
in front of.

So: four genuine nondeterminisms, injected into a throwaway copy of this
package, each of which the real command line must catch.  The mechanics and the
two disciplines they are held to — nondeterminism rather than mere difference,
and anchors that fail loudly rather than becoming no-ops — are in
`determinism_sandbox.py`.

**Why a sandbox and not the real tree.**  The gate diffs against
`build.OUT` — `worldgen/out/worlds/` — and `main` rebuilds that directory on the
way in.  Running `--check` here would rewrite committed artefacts, which is a
separate ledger entry.  The sandbox is the same move
`figures/check_coverage.py --self-test` makes when it reconstructs the pre-P8
tree: put the defect somewhere it is allowed to exist, then require the probe
to see it.

Costs about ten seconds: nine subprocess builds, two of them on
`t3-latch-maze`, which is the cheapest world that has three mechanism families
and therefore the cheapest one on which set-iteration order can visibly move.
"""

import pytest

from worldgen import verify
from worldgen.tests import determinism_sandbox as ds


@pytest.fixture(scope="session")
def sandbox(tmp_path_factory):
    """One sandbox per (injection, weakening) pair, built once and shared."""
    cache = {}

    def get(injection=None, weakening=None):
        key = (injection, weakening)
        if key not in cache:
            label = "-".join(part for part in (injection, weakening) if part) or "clean"
            root = str(tmp_path_factory.mktemp("v16-" + label))
            cache[key] = ds.make_sandbox(root, injection, weakening)
        return cache[key]

    return get


@pytest.fixture(scope="session")
def scratch(tmp_path_factory):
    def get(label):
        return str(tmp_path_factory.mktemp("v16-out-%s" % label))

    return get


# --- the positive control ---------------------------------------------------

@pytest.mark.parametrize("world", ds.CLEAN_WORLDS)
def test_unpatched_sandbox_clears_the_gate(sandbox, world):
    """Without an injection the gate is green — on the same worlds and seeds.

    Every red below is worthless without this.  A gate that fires on
    `t3-latch-maze` because the sandbox is missing a file, or because those two
    seeds happen to disagree about something unrelated, would look exactly like
    a gate that caught the injected defect.
    """
    proc = ds.run_gate(sandbox(None), world)
    out = ds.text(proc)
    assert proc.returncode == 0, out[-3000:]
    assert ds.GREEN_BANNER in out, out[-3000:]
    assert ds.RED_BANNER not in out, out[-3000:]


@pytest.mark.parametrize("world", ds.CLEAN_WORLDS)
def test_unpatched_sandbox_is_byte_identical_across_the_two_seeds(
        sandbox, scratch, world):
    """The same claim again, from the oracle that never calls the gate.

    If this ever disagrees with the test above, one of the two is lying and the
    disagreement is the finding.
    """
    differing = ds.divergent_artefacts(
        sandbox(None), world, scratch("clean-a-" + world), scratch("clean-b-" + world))
    assert differing == [], (
        "the unpatched package is not byte-reproducible across PYTHONHASHSEED "
        "%s and 271828: %s" % (ds.PARENT_SEED, differing))


# --- the negative controls --------------------------------------------------

@pytest.mark.parametrize("injection", ds.INJECTIONS, ids=lambda i: i.name)
def test_injection_moves_the_bytes_across_the_two_seeds(sandbox, scratch, injection):
    """Precondition: the artefacts really do move between the gate's two seeds.

    Without this an "injection" that merely made the comparison build *differ
    from the committed one* would turn the gate red just as convincingly while
    proving only that a byte diff works.

    This shares the gate's criterion — same seed pair — so it is not an
    independent oracle; see `divergent_artefacts`.  What it independently
    reproduces is the comparison itself.
    """
    differing = ds.divergent_artefacts(
        sandbox(injection.name), injection.world,
        scratch("nd-a-" + injection.name), scratch("nd-b-" + injection.name))
    assert differing, (
        "injection %r produced byte-identical artefacts at PYTHONHASHSEED %s and "
        "271828, so the negative control below would be testing nothing. %s"
        % (injection.name, ds.PARENT_SEED, injection.why))


@pytest.mark.parametrize("injection", ds.INJECTIONS, ids=lambda i: i.name)
def test_injection_is_the_class_it_claims_to_be(sandbox, scratch, injection):
    """Hold the seed fixed and see which requirement the defect actually breaks.

    `CLAUDE.md` asks for artefacts that are "byte-reproducible for a **fixed
    seed**".  Only class A breaks that.  Class B — `mechanism_order`,
    `hash_order_wide` — is byte-identical on two runs at one seed and moves only
    when the seed changes, which is a *stronger* property that
    `check_determinism` enforces and the charter never states.

    An earlier version of this file asserted all four were "nondeterministic"
    and would have let a reader conclude that a `set` reaching an output
    violates the written rule.  It does not.  It violates the gate.
    """
    measured = ds.classify(
        sandbox(injection.name), injection.world,
        scratch("cls-a-" + injection.name), scratch("cls-b-" + injection.name))
    assert measured == injection.klass, (
        "injection %r is labelled\n  %s\nbut two builds at PYTHONHASHSEED=%s "
        "measured\n  %s\nThe label is the thing this repository publishes about "
        "what its determinism requirement means; fix the label, not the "
        "measurement." % (injection.name, injection.klass, ds.PARENT_SEED, measured))


@pytest.mark.parametrize("injection", ds.INJECTIONS, ids=lambda i: i.name)
def test_gate_goes_red_on_injected_nondeterminism(sandbox, injection):
    """`python -m worldgen.build --check <world>` must exit non-zero and say why.

    Three assertions, and it is the **third** that does the discriminating work
    — the first draft of this docstring credited the second, which is wrong and
    worth writing down because the mistake is instructive.

    A non-zero exit alone would also be satisfied by a build that crashed, which
    an injection into `GridWorld`'s mechanism ordering could plausibly cause.
    And the `NOT DETERMINISTIC:` banner does **not** rule that out either:
    `build.py:251-253` renders a *failed comparison subprocess* under the same
    banner ("the comparison build failed: ..."). So a crash reaches assertion
    two intact.  Only the requirement that the gate named at least one artefact
    as `differs between runs` separates "the byte diff fired" from "something
    fell over".
    """
    proc = ds.run_gate(sandbox(injection.name), injection.world)
    out = ds.text(proc)
    assert proc.returncode != 0, (
        "NEGATIVE CONTROL FAILED: %s\n%s is nondeterministic and "
        "`build --check` exited 0.\n%s" % (injection.why, injection.world, out[-3000:]))
    assert ds.RED_BANNER in out, (
        "the build failed, but not through the determinism gate — so this "
        "proves nothing about it:\n%s" % out[-3000:])
    named = [line.strip() for line in out.splitlines() if "differs between runs" in line]
    assert named, (
        "the gate printed its banner and named no differing artefact:\n%s" % out[-3000:])


# --- and the control on the control -----------------------------------------

#: Cells of the weakening grid that must stay MISSED.  The full 4x4 table is in
#: `worldgen/runs/*-V16-determinism-has-no-caller/weakening_table.md`; these
#: three are kept as tests because each one names a specific part of the gate
#: and says what happens without it.
MUST_BE_MISSED = (
    # The fresh-interpreter rebuild is the whole reason the gate exists in its
    # current form. Hand the comparison build the parent's seed back — the gate
    # exactly as it stood before C1's F7 — and both hash-order defects walk
    # through, on a gate that still spawns a subprocess and still diffs bytes.
    ("shared_hashseed", "mechanism_order"),
    ("shared_hashseed", "hash_order_wide"),
    # And the diff itself: stop reading the comparison build and everything
    # walks through, including the one no seed can hide.
    ("no_diff", "unseeded_rng"),
)


@pytest.mark.parametrize("weakening,injection", MUST_BE_MISSED)
def test_a_weakened_gate_lets_the_injection_past(sandbox, weakening, injection):
    """The reds above have to be the gate's, not the harness's.

    Same sandbox, same injection, same command line — only `check_determinism`
    is weakened.  If the run stayed red here, the red would be coming from
    somewhere else and every negative control in this file would be decoration.
    """
    proc = ds.run_gate(sandbox(injection, weakening), ds.BY_NAME[injection].world)
    out = ds.text(proc)
    assert proc.returncode == 0 and ds.RED_BANNER not in out, (
        "the %r weakening did not actually blind the gate to %r, so that cell of "
        "the table proves nothing about which part of check_determinism is doing "
        "the work:\n%s" % (weakening, injection, out[-3000:]))


# --- the wiring the gate hangs from -----------------------------------------

def test_verify_still_runs_the_determinism_gate():
    """`check_determinism` has exactly one production path; pin it.

    The function is unreachable except through `build.main --check`, and `main
    --check` is run by exactly one thing: `verify.py`'s first stage, which
    gates.  Drop the flag there and the strongest determinism claim in the
    repository becomes dead code with every test still green — which is close
    to the state V16 found it in.
    """
    stages = {label: (tuple(command), gating) for label, command, gating in verify.STAGES}
    matching = [(label, command, gating) for label, (command, gating) in stages.items()
                if "-m" in command and "worldgen.build" in command]
    assert len(matching) == 1, "expected exactly one build stage in verify.STAGES: %s" % (
        list(stages),)
    label, command, gating = matching[0]
    assert "--check" in command, (
        "verify.py runs `worldgen.build` without `--check`, so nothing in this "
        "repository ever calls check_determinism: %r" % (command,))
    assert gating, "the determinism stage is reported but does not gate: %r" % (label,)
