"""A disposable copy of this package with a fake invariant bolted into it.

The V19 defect was that `ground_truth.json` computed

```python
"invariants_all_hold": all(i.get("holds", True) for i in invariants),
```

and a prose-only invariant carries **no `holds` key at all**, so `.get`'s
default turned *unverified* into *holds*.  `build.py` then promoted that to
`invariant_failures: []` in the manifest, which is the list the build gate
reads.  Thirteen of thirty-five shipped `ground_truth.json` files reported
`invariants_all_hold: true` while the `GROUND_TRUTH.md` written from the same
dict, in the same function call, printed `prose only, unverified` about the same
claim.  The human-readable half was honest the whole time; only the machine-read
half lied, and the machine is what adjudicates.

This module is the negative control for the repair, and it is built the way
`determinism_sandbox.py` builds V16's: copy the package source into a temporary
root, patch a **fake invariant** into `core/truth.invariant_table`, and run the
real command line there — `python -m worldgen.build <world>`.  The assertion is
on the **process exit code and the gate's own banner line**, not on what some
helper function returned.  A gate that returns a list nobody exits on is the
defect this territory has already been bitten by twice (`build.gate_failures`
before C1's audit; `check_determinism` before V16).

Three disciplines this file is strict about.

* **The injections are invariants, not merely breakage.**  It would be easy to
  make the build red by injecting a syntax error.  Every injection here appends
  one well-formed row to the invariant table and changes nothing else, so what
  goes red is the invariant gate and not the build.

* **Unverified and violated are separate cells, and they are asserted
  separately.**  The tempting one-line repair was to widen `invariant_failures`
  to "anything that is not `invariants_all_hold`".  That is a *different* bug:
  it makes an unexercised claim indistinguishable from a broken world, and the
  work each calls for is not the same.  So `prose_only` must be caught by
  `invariant_unverified` and `violated_*` by `invariant_failures`, and the tests
  check which gate fired — not merely that something did.  **`violated_*` exists
  to catch an over-correction**: a repair that answers "unverified is not true"
  by refusing everything would pass a test that only checks `prose_only`.

* **The gate is shown to be able to go green, and shown to be able to be
  weakened.**  `holds_*` are positive controls: a well-formed invariant that
  really holds must not trip anything, or the negative controls are measuring a
  build that is red for its own reasons.  And `WEAKENINGS` puts the pre-V19
  shape back — the two-state boolean, the `.get(..., True)` default, the missing
  gate — one piece at a time, and requires the historical defect to reappear.  A
  control that has never been shown to stop firing is half a control.

Costs a few seconds: one `copytree` per (injection, weakening) pair and a
single-world build each, on `t1-walk-maze` — the cheapest world in the
catalogue, and a legitimate host because `invariant_table` gives *every* world
`agent_unique` and `grid_shape` regardless of which mechanisms it binds.
"""

import json
import os
import shutil
import subprocess
import sys
from typing import Dict, Optional, Sequence, Tuple

PACKAGE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKAGE_NAME = os.path.basename(PACKAGE)

#: Source only.  `out/` and `runs/` are the committed artefacts and the
#: provenance ledger; a sandbox must never be seeded from, or able to write
#: back to, either.
SKIP = ("out", "runs", "__pycache__", ".pytest_cache", ".pytest-runs")

#: The world every injection is shown on.  Cheapest in the catalogue, and it
#: binds no mechanisms at all — which is the point: the two base invariants
#: `invariant_table` always emits are enough to host the probe, so nothing here
#: depends on a particular mechanism's behaviour.
WORLD = "t1-walk-maze"

#: The build's own banners.  Asserting on these and not merely on a non-zero
#: exit is what separates "the invariant gate fired" from "the build crashed".
RED_BANNER = "BUILD GATE FAILED:"
GREEN_BANNER = "build gate:"

#: The gate keys that must stay distinguishable.
UNVERIFIED_KEY = "invariant_unverified"
VIOLATED_KEY = "invariant_failures"
MISMATCH_KEY = "invariant_verdict_mismatch"


class InjectionFailed(RuntimeError):
    """The probe could not be planted — the sandbox is not a control."""


class Patch:
    """A set of `(relpath, anchor, replacement)` edits with unique anchors.

    Every anchor is asserted to occur exactly once.  If the source moves under
    this file the patch fails loudly instead of silently becoming a no-op that
    leaves the control green for the wrong reason — the failure mode
    `determinism_sandbox.py` documents and this file inherits.
    """

    def __init__(self, name: str, why: str,
                 edits: Sequence[Tuple[str, str, str]]):
        self.name = name
        self.why = why
        self.edits = tuple(edits)

    def apply(self, root: str) -> None:
        for relpath, anchor, replacement in self.edits:
            path = os.path.join(root, PACKAGE_NAME, relpath.replace("/", os.sep))
            with open(path, encoding="utf-8", newline="") as handle:
                text = handle.read()
            found = text.count(anchor)
            if found != 1:
                raise InjectionFailed(
                    "patch %r could not be applied: its anchor occurs %d times in "
                    "%s (expected exactly 1). The source moved under this file; "
                    "re-anchor it rather than letting the control become a no-op."
                    % (self.name, found, relpath))
            with open(path, "w", encoding="utf-8", newline="") as handle:
                handle.write(text.replace(anchor, replacement))


# --- the injections ---------------------------------------------------------
#
# All of them append one row to `invariant_table`, which is the single funnel
# every invariant reaches `check_invariants` through.  Injecting here rather
# than into one mechanism keeps the probe independent of which families a world
# binds, and leaves `check_invariants`, `classify_invariants`,
# `all_invariants_hold`, `build_world`, `build_all`'s totals, `gate_failures`
# and `main`'s exit code all running exactly as shipped.

_TABLE_ANCHOR = (
    "    for mechanism in world.mechanisms:\n"
    "        out.extend(mechanism.invariants(world.spec, world.mine(mechanism)))\n"
    "    return out\n")

_TAIL = "    return out\n"


def _inject(body: str) -> Tuple[str, str, str]:
    return ("core/truth.py", _TABLE_ANCHOR,
            _TABLE_ANCHOR.replace(_TAIL, body + _TAIL))


INJECTIONS: Tuple[Patch, ...] = (
    Patch(
        "prose_only",
        "the defect itself: an invariant that is nothing but a sentence. It has "
        "no `holds` key, which is what `.get(\"holds\", True)` used to read as "
        "True. The gate must refuse to count it as holding.",
        [_inject('    out.append({"name": "v19_probe_prose_only",\n'
                 '                "statement": "injected: a claim with no callable '
                 'check at all"})\n')],
    ),
    Patch(
        "prose_only_explicit_none",
        "the same claim written the way the three real ones were written — "
        "`\"check\": None` spelled out rather than the key omitted. A repair "
        "that keys off the *absence* of the key would pass `prose_only` and "
        "miss every invariant this library actually shipped.",
        [_inject('    out.append({"name": "v19_probe_prose_none",\n'
                 '                "statement": "injected: check is explicitly None",\n'
                 '                "check": None, "edge_check": None})\n')],
    ),
    Patch(
        "violated_state",
        "a genuinely broken single-state invariant. It must still be caught, and "
        "caught as a *violation* — a repair that answers V19 by refusing "
        "everything would look identical on `prose_only` alone.",
        [_inject('    out.append({"name": "v19_probe_violated_state",\n'
                 '                "statement": "injected: false on every reachable '
                 'state",\n'
                 '                "check": lambda _w, _s: False})\n')],
    ),
    Patch(
        "violated_edge",
        "a genuinely broken transition invariant, via the `edge_check` seam the "
        "repair added. A new seam that cannot go red is a new place for the "
        "same bug to live.",
        [_inject('    out.append({"name": "v19_probe_violated_edge",\n'
                 '                "statement": "injected: false on every '
                 'transition",\n'
                 '                "edge_check": lambda _w, _p, _a, _n: False})\n')],
    ),
    Patch(
        "holds_state",
        "positive control: a well-formed single-state invariant that really "
        "holds. Must be green, or the negative controls above are measuring a "
        "build that is red for unrelated reasons.",
        [_inject('    out.append({"name": "v19_probe_holds_state",\n'
                 '                "statement": "injected: true on every reachable '
                 'state",\n'
                 '                "check": lambda _w, _s: True})\n')],
    ),
    Patch(
        "holds_edge",
        "positive control for the `edge_check` seam.",
        [_inject('    out.append({"name": "v19_probe_holds_edge",\n'
                 '                "statement": "injected: true on every '
                 'transition",\n'
                 '                "edge_check": lambda _w, _p, _a, _n: True})\n')],
    ),
)

BY_NAME: Dict[str, Patch] = {p.name: p for p in INJECTIONS}


# --- the weakenings ---------------------------------------------------------
#
# Each puts some part of the pre-V19 shape back.  `pre_v19` is the whole of it
# and is the demonstration the work order asks for in as many words: change the
# three-state back to a boolean and show that `prose_only` gets through.  The
# other two are the same revert taken one piece at a time, which is what
# identifies *which* piece carries the load — `boolean_default` alone turns out
# not to be enough, because the separate gate key still fires, and that is worth
# knowing about a repair whose whole subject is redundant safety.

_ALL_HOLD_ANCHOR = (
    "    status = classify_invariants(invariants)\n"
    "    return not status[INV_VIOLATED] and not status[INV_UNVERIFIED]\n")

_ALL_HOLD_PRE_V19 = (
    "    return all(i.get(\"holds\", True) for i in invariants)"
    "   # V19 weakening\n")

_GATE_ANCHOR = (
    "    (\"invariant_unverified\",\n"
    "     \"a declared invariant ships unverified — no callable check ran, so the world \"\n"
    "     \"cannot claim it holds; give it a `check` or an `edge_check`, or stop \"\n"
    "     \"declaring it\"),\n")

#: The second gate V19 added.  `pre_v19` has to remove this one too, because
#: pre-V19 had neither — and the first attempt at that weakening left it in
#: place, whereupon the *verdict-mismatch* gate caught the reverted boolean
#: disagreeing with the lists and the historical defect failed to reproduce.
#: That was the new gate demonstrating its teeth by accident, and it is now
#: `test_the_verdict_gate_catches_a_boolean_that_drifts` on purpose.
_MISMATCH_GATE_ANCHOR = (
    "    (\"invariant_verdict_mismatch\",\n"
    "     \"`invariants_all_hold` disagrees with the three-class partition it summarises \"\n"
    "     \"— the published boolean and the lists it is derived from have drifted, and \"\n"
    "     \"the boolean is what every naive downstream reads\"),\n")

_FAILURES_ANCHOR = (
    "            \"invariant_failures\": sorted(r[\"world_id\"] for r in rows\n"
    "                                         if r[\"invariants_violated\"]),\n")

_FAILURES_PRE_V19 = (
    "            \"invariant_failures\": sorted(r[\"world_id\"] for r in rows\n"
    "                                         if not r[\"invariants_all_hold\"]),"
    "   # V19 weakening\n")

_SINK_ANCHOR = (
    "        else:\n"
    "            unverified.append(name)\n")

WEAKENINGS: Dict[str, Tuple[str, Sequence[Tuple[str, str, str]]]] = {
    "pre_v19": (
        "the whole pre-V19 shape: the boolean with its `.get(..., True)` "
        "default, `invariant_failures` derived from it, and no separate "
        "unverified gate. This is the historical defect, restored.",
        [("core/truth.py", _ALL_HOLD_ANCHOR, _ALL_HOLD_PRE_V19),
         ("build.py", _GATE_ANCHOR, "    # V19 weakening: gate removed\n"),
         ("build.py", _MISMATCH_GATE_ANCHOR,
          "    # V19 weakening: verdict-mismatch gate removed\n"),
         ("build.py", _FAILURES_ANCHOR, _FAILURES_PRE_V19)],
    ),
    "boolean_default": (
        "only the boolean goes back — `all(i.get(\"holds\", True) ...)` — while "
        "the separate gate key stays. Isolates how much of the catch the "
        "conjunction is responsible for, and the answer is: on its own, none.",
        [("core/truth.py", _ALL_HOLD_ANCHOR, _ALL_HOLD_PRE_V19)],
    ),
    "unverified_sinks_to_holds": (
        "the three-state keeps its three names but the sink branch files "
        "anything it does not recognise under `holds` instead of `unverified`. "
        "This is the failure a three-way split invites — a third class that "
        "exists in the schema and is unreachable in the code — and it must "
        "reproduce the original bug exactly.",
        [("core/truth.py", _SINK_ANCHOR,
          "        else:\n"
          "            holds.append(name)   # V19 weakening: the sink is bypassed\n")],
    ),
    "all_hold_hardcoded_true": (
        "`all_invariants_hold` always returns True. Before the verdict-mismatch "
        "gate existed this was a **no-op on the exit code** — nothing read the "
        "boolean any more, so the field this cell is named for could be a "
        "constant and the build stayed green. Combined with "
        "`drop_unverified_gate` it isolates that gate: the two lists are then "
        "unpoliced and the boolean is the only thing left to catch the world.",
        [("core/truth.py", _ALL_HOLD_ANCHOR,
          "    return True   # V19 weakening: the published boolean is a constant\n")],
    ),
    "hardcoded_true_and_no_unverified_gate": (
        "both of the above at once. The `invariant_unverified` gate is gone and "
        "the boolean lies, so only `invariant_verdict_mismatch` can see the "
        "prose-only invariant — which is the test that the boolean carries load "
        "rather than merely being published.",
        [("core/truth.py", _ALL_HOLD_ANCHOR,
          "    return True   # V19 weakening: the published boolean is a constant\n"),
         ("build.py", _GATE_ANCHOR, "    # V19 weakening: gate removed\n")],
    ),
    "drop_unverified_gate": (
        "the gate key is removed from `GATES` and nothing else changes. The "
        "manifest still reports `invariant_unverified` honestly; nobody exits "
        "on it. This is the shape both of this territory's previous two "
        "findings took.",
        [("build.py", _GATE_ANCHOR, "    # V19 weakening: gate removed\n")],
    ),
}


def _weakening(name: str) -> Patch:
    why, edits = WEAKENINGS[name]
    return Patch("weakening:" + name, why, edits)


# --- the sandbox ------------------------------------------------------------

def make_sandbox(root: str, injection: Optional[str] = None,
                 weakening: Optional[str] = None) -> str:
    dest = os.path.join(root, PACKAGE_NAME)
    shutil.copytree(PACKAGE, dest, ignore=shutil.ignore_patterns(*SKIP))
    if injection is not None:
        BY_NAME[injection].apply(root)
    if weakening is not None:
        _weakening(weakening).apply(root)
    return root


def _env(root: str) -> Dict[str, str]:
    env = dict(os.environ)
    env.pop("PYTHONDONTWRITEBYTECODE", None)
    # The sandbox must import *its own* copy, never the checkout it was made
    # from, or the probe would be patched into a file nobody executes.
    env["PYTHONPATH"] = root
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def run_build(root: str, into: str,
              world: str = WORLD) -> subprocess.CompletedProcess:
    """The real entry point in the sandbox, with a real process exit code.

    `--into` keeps the build off the sandbox's own `out/` — irrelevant for
    correctness, since the whole tree is temporary, but it also skips
    `write_catalogue` and the `--check` rebuild, which is the difference between
    a two-second control and a twenty-second one.  The gate, the manifest and
    `main`'s return value are untouched by it.
    """
    return subprocess.run(
        [sys.executable, "-m", "%s.build" % PACKAGE_NAME, "--into", into, world],
        cwd=root, env=_env(root), capture_output=True)


def read_artefacts(into: str, world: str = WORLD) -> Tuple[Dict, str]:
    """The `ground_truth.json` and `GROUND_TRUTH.md` the sandbox build produced.

    Some weakenings do not move the exit code at all — `boolean_default` is
    byte-identical to the unweakened run on stdout, rc and gate lines, because
    the gate that catches the defect is a different one. A test that asserts
    only on the process therefore passes whether or not the weakening applied,
    which makes it a control that cannot fail. The artefact is where that
    weakening's effect actually lands, so the test has to open it.
    """
    root = os.path.join(into, world)
    with open(os.path.join(root, "ground_truth.json"), encoding="utf-8") as handle:
        blob = json.load(handle)
    with open(os.path.join(root, "GROUND_TRUTH.md"), encoding="utf-8") as handle:
        return blob, handle.read()


def text(proc: subprocess.CompletedProcess) -> str:
    return (proc.stdout + proc.stderr).decode("utf-8", "replace")


def gate_lines(proc: subprocess.CompletedProcess) -> Tuple[str, ...]:
    """Just the indented lines under `BUILD GATE FAILED:`."""
    out = []
    seen = False
    for line in text(proc).splitlines():
        if line.startswith(RED_BANNER):
            seen = True
            continue
        if seen:
            if line.startswith("  "):
                out.append(line.strip())
            elif line.strip():
                break
    return tuple(out)
