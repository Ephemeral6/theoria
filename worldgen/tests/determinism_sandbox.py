"""A disposable copy of this package with a real nondeterminism bolted into it.

`worldgen.build.check_determinism` is the strongest determinism claim in this
repository — it rebuilds the catalogue in a *fresh interpreter* at a different
`PYTHONHASHSEED` and diffs every byte — and until V16 nothing had ever
demonstrated that it can go red.  It is reachable only from
`worldgen.build.main` under `--check`, which `worldgen/verify.py` runs as its
first gate; no test in this repository reached it, directly or through a
subprocess.  (Measured, not scanned: a tripwire that raised on entry left the
whole suite green.  See `worldgen/runs/*-V16-determinism-has-no-caller/`.)

The obstacle to testing it in place is that the gate diffs against the module
constant `build.OUT`, i.e. `worldgen/out/worlds/`, and `main` rebuilds that
directory before checking it.  Running the real entry point against the real
tree would therefore rewrite ten committed artefacts, which is a different
ledger entry and not ours to touch.

So the negative control does what `figures/check_coverage.py --self-test` does
with the pre-P8 tree: it reconstructs the defect somewhere it is allowed to.
This module copies the package source into a temporary root, patches a genuine
nondeterminism into one of the *generators*, and runs the real command line
there — `python -m worldgen.build --check <world>` — so `HERE`, `OUT` and the
gate's own `cwd` all follow the copy.  The assertion is on the **process exit
code and the gate's own banner**, not on a helper's return value.

Two disciplines this file is deliberately strict about:

* **The injections are nondeterminism, not merely difference.**  It would be
  much easier to make the gate red by changing a constant: the comparison build
  would differ from the committed one and the diff would fire.  That tests the
  diff, not the property.  Every injection here leaves the code identical and
  moves the *bytes*.

  But "nondeterministic" is two different claims here, and an earlier draft of
  this file ran them together.  `CLAUDE.md` states the requirement as
  **"byte-reproducible for a fixed seed"**, and by that written definition only
  two of the four injections below violate anything:

  - **Class A — violates the written requirement.**  `unseeded_rng` and
    `wall_clock` produce different bytes on two runs *at one and the same*
    `PYTHONHASHSEED`.  These are nondeterministic in the plain sense.
  - **Class B — violates the stronger requirement the gate actually
    enforces.**  `mechanism_order` and `hash_order_wide` are byte-identical on
    two runs at a fixed seed.  Run them at `PYTHONHASHSEED=1` twice and nothing
    moves.  What they violate is *cross-seed* stability, which `CLAUDE.md` does
    not ask for and `check_determinism` nevertheless demands — it hardcodes
    `271828` for its comparison build precisely so that the parent's seed and
    the child's differ.

  Class B is kept, and is the more interesting half: the `shared_hashseed`
  column of the weakening table is the historical evidence that cross-seed
  stability is worth having, since the gate did not check it before C1's F7 and
  a `set` reaching an output would have been invisible.  But the two classes are
  labelled everywhere rather than blurred, because a reader who takes
  `mechanism_order` for a `CLAUDE.md` violation has been misled about what this
  repository promises.  `classify()` measures the split rather than asserting
  it, and `tests/test_determinism_gate.py` pins both halves.

  A note has gone upstream (`monitor/inbox/`) suggesting `CLAUDE.md` say which
  of the two it means; that is not this file's call to make.

* **Every patch anchor is asserted unique.**  If `world.py` or `explorer.py`
  moves under this file, the injection fails to apply and says so, rather than
  silently becoming a no-op that leaves the gate green.  The anchors are written
  with `\n`, which is safe only because `worldgen/.gitattributes` pins `eol=lf`
  for this whole directory; drop that pin on a `core.autocrlf=true` checkout and
  these injections stop applying — loudly, by design, rather than by going
  quiet.

`PARENT_SEED` is pinned rather than left to Python's per-process randomisation:
the gate hardcodes `271828` for its comparison build, so the parent must run at
some *other* fixed seed for the class-B injections to be a reproducible red
rather than a coin flip.  `1` is chosen because it is empirically a different
iteration order from `271828` for the sets involved.

**And for `mechanism_order` that choice is doing real work.**  `t3-latch-maze`
binds three mechanisms, so set iteration has six orders and roughly one seed in
six agrees with `271828` and hides the defect.  `PARENT_SEED = "1"` happens to
fall in the visible majority.  The rate is measured, not asserted, and it is
printed in the weakening table as `RED (n/m seeds)` rather than as a verdict —
prose calling it "reproducible rather than guaranteed" is not enough, because
the table is the part that gets copied.  `hash_order_wide` exists as the
companion case that does not have this problem: sixty-four elements, so two
seeds practically cannot agree.
"""

import hashlib
import os
import shutil
import subprocess
import sys
from typing import Dict, List, Optional, Sequence, Tuple

PACKAGE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKAGE_NAME = os.path.basename(PACKAGE)

#: Copied into the sandbox: source only.  `out/` and `runs/` are the committed
#: artefacts and the provenance ledger; the sandbox builds its own `out/` from
#: scratch and must never be seeded from, or able to write back to, either.
SKIP = ("out", "runs", "__pycache__", ".pytest_cache", ".pytest-runs")

#: The seed the *parent* build runs at.  `check_determinism` pins its child at
#: 271828; these two must differ or the hash-order injections cannot show.
PARENT_SEED = "1"

#: The per-world files `check_determinism` diffs.
ARTEFACTS = ("raw_trace.jsonl", "spec.json", "coverage.json",
             "ground_truth.json", "GROUND_TRUTH.md", "reversibility.json")

#: The gate's own banner.  Asserting on this and not merely on a non-zero exit
#: is what separates "the determinism gate fired" from "the build crashed".
RED_BANNER = "NOT DETERMINISTIC:"
GREEN_BANNER = "determinism: every artefact byte-identical"


class InjectionFailed(RuntimeError):
    """The defect could not be reconstructed — the sandbox is not a control."""


#: Class A violates `CLAUDE.md`'s written requirement — the artefacts move
#: between two runs at *one* seed.  Class B is byte-stable at a fixed seed and
#: moves only across seeds, which `CLAUDE.md` does not ask for and the gate
#: enforces anyway.  See this module's docstring; `classify` measures which is
#: which rather than trusting these labels.
CLASS_A = "varies at a fixed seed (violates CLAUDE.md as written)"
CLASS_B = "stable at a fixed seed, moves across seeds (violates the stronger " \
          "requirement check_determinism enforces)"


class Injection:
    """One defect, the world to show it on, and why it must be caught.

    `klass` is `CLASS_A` or `CLASS_B` — see the module docstring.  It is a
    claim about the injection, and `test_determinism_gate.py` checks it against
    `classify()` rather than taking it on trust; an injection whose class is
    mislabelled is exactly the confusion this attribute exists to prevent.
    """

    def __init__(self, name: str, world: str, why: str,
                 edits: Sequence[Tuple[str, str, str]], klass: str):
        self.name = name
        self.world = world
        self.why = why
        self.edits = tuple(edits)
        self.klass = klass

    def apply(self, root: str) -> None:
        for relpath, anchor, replacement in self.edits:
            path = os.path.join(root, PACKAGE_NAME, relpath.replace("/", os.sep))
            with open(path, encoding="utf-8", newline="") as handle:
                text = handle.read()
            found = text.count(anchor)
            if found != 1:
                raise InjectionFailed(
                    "injection %r could not be applied: its anchor occurs %d times "
                    "in %s (expected exactly 1). The source moved under this file; "
                    "re-anchor it rather than letting the negative control become a "
                    "no-op." % (self.name, found, relpath))
            with open(path, "w", encoding="utf-8", newline="") as handle:
                handle.write(text.replace(anchor, replacement))


# --- the injections ---------------------------------------------------------
#
# `_COVERAGE_ANCHOR` is the last line of `explorer.coverage_report`'s returned
# dict.  Three injections hang a `v16_probe` list off it because `coverage.json`
# is written with `sort_keys=True`, which re-sorts every *dict* on the way out —
# a nondeterministic mapping is invisible there, a nondeterministic *list* is
# not.  That is itself worth knowing about the artefact.

_COVERAGE_ANCHOR = (
    '        "win_frames": [i for i, s in enumerate(states) if world.is_win(s)],\n')

_MECHANISM_ANCHOR = (
    "        self.mechanisms: Tuple[Mechanism, ...] = tuple(\n"
    "            sorted(wanted.values(), key=lambda m: (m.priority, m.name))\n"
    "        )\n")

_MECHANISM_INJECTED = (
    "        self.mechanisms: Tuple[Mechanism, ...] = tuple(\n"
    "            wanted[_name] for _name in set(wanted)   # V16 injected defect\n"
    "        )\n")


def _coverage_probe(expression: str) -> Tuple[str, str, str]:
    return ("core/explorer.py", _COVERAGE_ANCHOR,
            _COVERAGE_ANCHOR + '        "v16_probe": %s,   # V16 injected defect\n'
            % expression)


INJECTIONS: Tuple[Injection, ...] = (
    Injection(
        "mechanism_order",
        "t3-latch-maze",
        "the structural defect the gate's own docstring names: a `set` reaching "
        "an output. `GridWorld` drops the `(priority, name)` sort and takes its "
        "mechanism order from set iteration, so the variable layout and every "
        "`State.key()` move with the hash seed. Measured effect on the shipped "
        "artefacts: `ground_truth.json`, `GROUND_TRUTH.md` and "
        "`reversibility.json` differ; `raw_trace.jsonl`, `spec.json` and "
        "`coverage.json` do NOT — the trace renders frames, not the variable "
        "vector, so it is blind to this. (An earlier draft of this sentence "
        "said 'the whole trace moves'. It does not, and the run directory's own "
        "console log had said so from the first experiment.)",
        [("core/world.py", _MECHANISM_ANCHOR, _MECHANISM_INJECTED)],
        klass=CLASS_B,
    ),
    Injection(
        "hash_order_wide",
        "t1-walk-maze",
        "sixty-four strings iterated out of a `set` into a JSON list. Same class "
        "as `mechanism_order` but wide enough that two different seeds "
        "practically cannot agree, so it is the case that pins the gate even if "
        "a future Python changes small-set layout.",
        [_coverage_probe('list({"tok-%03d" % i for i in range(64)})')],
        klass=CLASS_B,
    ),
    Injection(
        "unseeded_rng",
        "t1-walk-maze",
        "an unseeded `random.random()` in an output. Moves between two runs at "
        "the same seed, so it is the written requirement this repository states "
        "and not merely the one the gate enforces.",
        [_coverage_probe('[__import__("random").random()]')],
        klass=CLASS_A,
    ),
    Injection(
        "wall_clock",
        "t1-walk-maze",
        "wall-clock nanoseconds in an output. The other fixed-seed violation, "
        "and the one that survives a `random.seed()` being added somewhere.",
        [_coverage_probe('[__import__("time").time_ns()]')],
        klass=CLASS_A,
    ),
)

BY_NAME: Dict[str, Injection] = {i.name: i for i in INJECTIONS}


# --- the weakenings ---------------------------------------------------------
#
# A negative control that has never been shown to *stop* firing is only half a
# control: it could be red because the harness is red, not because the gate is
# awake.  So the gate itself is also patched — weakened three ways, each of
# which a reviewer could plausibly wave through — and the injections above are
# run again against the weakened versions.  What must happen is that the
# nondeterminism gets past.  `worldgen/runs/*-V16-determinism-has-no-caller/`
# carries the full table.
#
# `shared_hashseed` is not hypothetical.  It is the gate exactly as it stood
# before the C1 audit's F7 ("builds the comparison copy in this same process,
# so PYTHONHASHSEED is shared and hash-order nondeterminism is invisible to
# it"), restated as an env change rather than an in-process call.  It is the
# case that shows what the fresh-interpreter rebuild actually buys.

_ENV_ANCHOR = '        env = dict(os.environ, PYTHONHASHSEED="271828")\n'
_BYTES_ANCHOR = (
    "            with open(a, \"rb\") as fa, open(b, \"rb\") as fb:\n"
    "                if fa.read() != fb.read():\n"
    "                    differences.append(\"%s differs between runs\" % label)\n")

WEAKENINGS: Dict[str, Tuple[str, Sequence[Tuple[str, str, str]]]] = {
    "shared_hashseed": (
        "the comparison build inherits the parent's PYTHONHASHSEED — the gate "
        "as it stood before C1's F7",
        [("build.py", _ENV_ANCHOR,
          "        env = dict(os.environ)   # V16 weakening: shared hash seed\n")],
    ),
    "size_only": (
        "compare file sizes instead of bytes",
        [("build.py", _BYTES_ANCHOR,
          "            if os.path.getsize(a) != os.path.getsize(b):   # V16 weakening\n"
          "                differences.append(\"%s differs between runs\" % label)\n")],
    ),
    "no_diff": (
        "run the comparison build and never look at it",
        [("build.py", _BYTES_ANCHOR,
          "            if False:   # V16 weakening: the diff is skipped\n"
          "                differences.append(\"%s differs between runs\" % label)\n")],
    ),
}


def _weakening_injection(name: str) -> Injection:
    why, edits = WEAKENINGS[name]
    return Injection("weakening:" + name, "", why, edits, klass=CLASS_B)

#: The worlds the clean (positive) control runs on: every world any injection
#: uses.  Without this the negative controls prove nothing — a gate that is red
#: on `t3-latch-maze` for some unrelated reason would look identical.
CLEAN_WORLDS = tuple(sorted({i.world for i in INJECTIONS}))


# --- the sandbox ------------------------------------------------------------

def make_sandbox(root: str, injection: Optional[str] = None,
                 weakening: Optional[str] = None) -> str:
    """Copy the package source to `root`, then apply injection and weakening.

    Order matters only in that both must apply; they touch different files
    (`core/` versus `build.py`), and each asserts its own anchor is unique.
    """
    dest = os.path.join(root, PACKAGE_NAME)
    shutil.copytree(PACKAGE, dest, ignore=shutil.ignore_patterns(*SKIP))
    if injection is not None:
        BY_NAME[injection].apply(root)
    if weakening is not None:
        _weakening_injection(weakening).apply(root)
    return root


def _env(root: str, seed: str = PARENT_SEED) -> Dict[str, str]:
    env = dict(os.environ, PYTHONHASHSEED=seed)
    env.pop("PYTHONDONTWRITEBYTECODE", None)
    # The sandbox must import *its own* copy, never the checkout it was made
    # from, or an injection would be patched into a file nobody executes.
    env["PYTHONPATH"] = root
    return env


def run_gate(root: str, world: str,
             seed: str = PARENT_SEED) -> subprocess.CompletedProcess:
    """The real entry point, in the sandbox: `build --check <world>`.

    No `--into`: the default is the sandbox's own `OUT`, which is what makes
    `main` take the `--check` branch at all (`into_default`).

    `seed` is the *parent's* `PYTHONHASHSEED`; the gate pins its own child at
    `271828` and this function cannot and should not change that.  It is a
    parameter so the weakening table can sample the cells that turn out to be
    rates rather than facts.
    """
    return subprocess.run(
        [sys.executable, "-m", "%s.build" % PACKAGE_NAME, "--check", world],
        cwd=root, env=_env(root, seed), capture_output=True)


def _plain_build(root: str, world: str, into: str, seed: str) -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "%s.build" % PACKAGE_NAME,
         "--into", into, "--quiet", world],
        cwd=root, env=_env(root, seed), capture_output=True)
    if proc.returncode != 0:
        raise InjectionFailed(
            "the sandbox could not build %s at PYTHONHASHSEED=%s, so nothing "
            "here measures determinism:\n%s"
            % (world, seed, (proc.stdout + proc.stderr).decode("utf-8", "replace")[-2000:]))


def divergent_artefacts(root: str, world: str, scratch_a: str, scratch_b: str,
                        seeds: Tuple[str, str] = (PARENT_SEED, "271828")) -> List[str]:
    """Which artefacts differ between two plain builds at `seeds`.

    **Implementation-independent, criterion-shared — not an independent
    oracle.**  An earlier docstring here claimed the latter and it was too
    strong.  What this function independently reproduces is the five-line diff
    loop at the end of `check_determinism`: it builds with `--into <dir>`, a
    path that never reaches the gate because `into_default` is false, and hashes
    the artefacts itself.  So a bug *in the gate's own comparison* — the wrong
    root, a missing file silently skipped, a truncated read — would show up as a
    disagreement between this and the gate.

    What it does **not** do is check the gate's criterion, because by default it
    is handed the same seed pair the gate hardcodes.  With that default it
    cannot tell "nondeterministic" from "a deterministic function of the hash
    seed", which is exactly the class A / class B distinction this module now
    labels.  `seeds` is a parameter for that reason: pass the same value twice
    and you are asking the other question.  `classify` does.
    """
    _plain_build(root, world, scratch_a, seeds[0])
    _plain_build(root, world, scratch_b, seeds[1])
    differing: List[str] = []
    for name in ARTEFACTS:
        digests = []
        for scratch in (scratch_a, scratch_b):
            path = os.path.join(scratch, world, name)
            with open(path, "rb") as handle:
                digests.append(hashlib.sha256(handle.read()).hexdigest())
        if digests[0] != digests[1]:
            differing.append(name)
    return differing


def classify(root: str, world: str, scratch_a: str, scratch_b: str) -> str:
    """`CLASS_A` or `CLASS_B` — measured by holding the seed fixed.

    Two builds at *the same* `PYTHONHASHSEED`.  If the bytes still move, the
    defect violates `CLAUDE.md`'s "byte-reproducible for a fixed seed" and is
    class A.  If they do not, whatever the gate catches is a cross-seed
    property, which is a real thing to want and is not what the charter says.
    """
    differing = divergent_artefacts(root, world, scratch_a, scratch_b,
                                    seeds=(PARENT_SEED, PARENT_SEED))
    return CLASS_A if differing else CLASS_B


def text(proc: subprocess.CompletedProcess) -> str:
    return (proc.stdout + proc.stderr).decode("utf-8", "replace")
