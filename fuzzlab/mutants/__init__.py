"""Fault injection — the battery's negative control.

`fuzzlab` reports 3000 worlds, 23 invariants, 0 violations. That number's
meaning is set entirely by the battery's **detection power**, which nobody has
measured: an invariant that can never fire and an invariant that is satisfied
look identical in `out/campaign.json`. `BUGS.md` says the green run "is real and
it is also weak" and lists the reasons; *this* is the reason it does not list.

So: mutation analysis. Inject a defect with a known shape, ask which invariants
notice.

## Where the defect is injected, and why not in the engine

The house rule (`fuzzlab/README.md`) is that `fuzzlab` never modifies
`engine-rig`, and `rig.py` says the interaction is `sys.path` and nothing else.
A mutation harness that edited engine source, or monkey-patched
`sys.modules['engines.…']`, would break that rule in fact even if it restored
afterwards — a crash mid-campaign would leave a patched engine behind for
whatever imports it next.

The seam used here is **fuzzlab's own**. Every property module funnels its
engine call through one private helper — `props/zero_space.py:_analyse`,
`props/cegis_miner.py:_mine`, and so on — so the injection rebinds *that*
attribute, on the fuzzlab module, and restores it on the way out. The engine
runs untouched and returns its true answer; the lie is told between the engine
and the property. That is the right place for it anyway: what is under test is
the property, not the engine.

A mutant is therefore a claim of the form *"suppose the engine had returned
this instead"* — and the honest reading of a surviving mutant is "the property
would not have noticed", which is exactly the question.

## Three controls, because the obvious version of this measurement lies

1. **Pre-registered expectations.** Every mutant declares `expect_kill` — which
   invariants *should* catch it — before the run. Without it, "the battery
   caught it" is indistinguishable from "we kept writing mutants until one
   tripped something", and a mutant that trips an invariant nobody predicted is
   a finding in its own right (usually: the invariants are less independent
   than the module docstring claims).

2. **Inert detection.** A corruption is not always *possible* on a given world:
   there is no law to drop from a world with no laws. Those worlds are counted
   `inert` and excluded from the denominator. Counting them as "survived" is
   the single easiest way to manufacture a scary-looking result — the mutant
   never happened and the invariant is blamed for not seeing it.

3. **`raised` is not `violated`.** `props/finding.py` keeps three outcomes
   apart and so does this. A mutant that makes a property *crash* has been
   detected in the weak sense that something went wrong, and not in the strong
   sense that the invariant stated what was wrong. They are reported in
   separate columns and the headline kill count uses `violated` only.

## What a mutant must be

A **real** defect: it has to contradict something the engine actually claims.
`claim` is not decoration — it cites where the claim is made. An injected
behaviour that no engine ever promised is not a defect, and an invariant that
lets it through is not weak. Getting this wrong produces a confident, wrong
report, which is the same failure mode `BUGS.md` names as the one this battery
is most exposed to.
"""

import copy
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Tuple

from fuzzlab.props import load

# `corrupt(result, args, kwargs) -> result`.  Receives the real return value of
# the seam and the arguments it was called with (the world is normally
# `args[0]`), and returns what the property will see instead.
Corrupt = Callable[[Any, Tuple[Any, ...], Dict[str, Any]], Any]

# What kind of lie the mutant tells.  Kept as a small vocabulary rather than
# free text so the report can group by it: the interesting result is a whole
# *kind* of defect that no invariant catches.
UNSOUND = "unsound"            # the engine asserts something false
INCOMPLETE = "incomplete"      # the engine withholds something true
INCONSISTENT = "inconsistent"  # the engine's own fields disagree with each other
DEGRADED = "degraded"          # the answer is worse than claimed (non-optimal, non-minimal)

KINDS = (UNSOUND, INCOMPLETE, INCONSISTENT, DEGRADED)


@dataclass(frozen=True)
class Mutant:
    """One injected defect, with the claim it contradicts stated up front."""

    id: str                      # "zs-drop-basis-vector"
    engine: str                  # must be one of props.ENGINES
    seam: str                    # attribute on the props module, e.g. "_analyse"
    kind: str                    # one of KINDS
    claim: str                   # the promise this violates, WITH its source
    description: str             # what is done to the return value, concretely
    corrupt: Corrupt = field(repr=False, default=None)
    expect_kill: Tuple[str, ...] = ()    # pre-registered, before any run
    # Pre-registers the opposite prediction: *nothing* should catch this. Two
    # analysts asked for it independently, and they were right — without it,
    # a mutant written specifically to demonstrate a known blind spot has to
    # name an invariant it does not believe will fire, and its correct survival
    # then lands in `predicted_but_missed` as though the prediction had failed.
    # That silently converts the sharpest kind of result — a designed negative
    # control, surviving exactly as predicted — into a recorded miss.
    predicted_survivor: bool = False

    def __post_init__(self) -> None:
        if self.kind not in KINDS:
            raise ValueError("mutant %s: kind %r not in %s"
                             % (self.id, self.kind, KINDS))
        if not callable(self.corrupt):
            raise ValueError("mutant %s: corrupt must be callable" % self.id)
        if not self.claim.strip():
            raise ValueError(
                "mutant %s: `claim` is required. A mutant that does not "
                "contradict a claim the engine makes is not a defect, and an "
                "invariant that lets it through is not weak." % self.id)
        if self.predicted_survivor and self.expect_kill:
            raise ValueError(
                "mutant %s: predicted_survivor and expect_kill are opposite "
                "predictions; declare one." % self.id)
        if not self.expect_kill and not self.predicted_survivor:
            raise ValueError(
                "mutant %s: pre-register a prediction before the run -- either "
                "`expect_kill` (these invariants should catch it) or "
                "`predicted_survivor=True` (nothing should, and that is the "
                "point). Reading the result first and then declaring what was "
                "expected measures nothing." % self.id)


class _Inert(Exception):
    """Raised by a `corrupt` that cannot apply to this particular world.

    Not an error: there is no law to drop from a world with no laws. The driver
    counts the world `inert` and takes it out of the denominator.
    """


def inert(reason: str) -> "_Inert":
    return _Inert(reason)


#: Set by `touched()`; read by `applied()` when deciding whether the mutant
#: actually did anything.
MARK = "_fuzzlab_mutated"


def touched(obj: Any) -> Any:
    """Declare that this object was mutated in a way `repr` cannot show.

    The inert check compares `repr(before)` with `repr(after)`, which is right
    for a mutant that edits a field and blind to one that shadows a *method* —
    a dataclass `repr` lists fields only, so replacing `result.contains` with a
    liar leaves the repr identical. Without this marker such a mutant is
    counted inert on every world, its denominator collapses to zero, and the
    invariant it was written to test is silently left unmeasured while the
    table still shows a row for it.
    """
    try:
        setattr(obj, MARK, True)
    except Exception:                                        # noqa: BLE001
        raise TypeError(
            "touched(): cannot mark %s -- a frozen or slotted result needs a "
            "mutant that edits a field instead of shadowing a method"
            % type(obj).__name__)
    return obj


@contextmanager
def applied(mutant: Mutant, record: List[Dict[str, Any]]):
    """Rebind the props module's seam for the duration; always restore.

    `record` accumulates one entry per call — whether the corruption applied,
    and whether it actually changed the value. A mutant whose output equals its
    input has not tested anything, and the driver must be able to see that
    rather than infer it.
    """
    module = load(mutant.engine)
    if not hasattr(module, mutant.seam):
        raise AttributeError(
            "mutant %s: fuzzlab.props.%s has no attribute %r -- the seam must "
            "be the private helper the property calls the engine through"
            % (mutant.id, mutant.engine, mutant.seam))
    original = getattr(module, mutant.seam)
    if not callable(original):
        raise TypeError("mutant %s: seam %r is not callable" % (mutant.id, mutant.seam))

    def patched(*args: Any, **kwargs: Any) -> Any:
        real = original(*args, **kwargs)
        try:
            # The corruption works on a copy: an in-place edit of the engine's
            # own return value would leak into whatever else holds a reference
            # to it, and the next invariant on the same world would be judging
            # a world nobody described.
            mutated = mutant.corrupt(copy.deepcopy(real), args, kwargs)
        except _Inert as why:
            record.append({"applied": False, "changed": False, "reason": str(why)})
            return real
        changed = (repr(mutated) != repr(real)
                   or bool(getattr(mutated, MARK, False)))
        record.append({"applied": True, "changed": changed, "reason": ""})
        return mutated

    setattr(module, mutant.seam, patched)
    try:
        yield
    finally:
        setattr(module, mutant.seam, original)


REGISTRY: Dict[str, List[Mutant]] = {}


def register(*mutants: Mutant) -> None:
    for m in mutants:
        REGISTRY.setdefault(m.engine, []).append(m)


def catalog() -> List[Mutant]:
    """Every registered mutant, after importing the per-engine catalogues."""
    import importlib

    from fuzzlab.props import ENGINES

    for engine in ENGINES:
        try:
            importlib.import_module("fuzzlab.mutants.%s" % engine)
        except ModuleNotFoundError:
            continue          # an engine with no catalogue yet is reported as such
    return [m for engine in sorted(REGISTRY) for m in REGISTRY[engine]]
