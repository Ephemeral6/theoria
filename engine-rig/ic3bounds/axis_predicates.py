"""Axis B -- predicate count, with the state space held exactly still.

Axis A walks |S| up the peg family and finds a wall.  It cannot say what the
wall is made of, because on peg-N the predicate count and the state count are
the same number: n booleans, 2^n states, one knob.  Every explanation of axis A
-- "IC3 pays for the state space", "IC3 pays for the vocabulary" -- fits its
data equally well, and a paper that picked one would be picking it for free.

This axis takes one world at a time and re-encodes it.  Same states, same
labelled edges, same initial state, same bad set, same answer -- only the number
of booleans used to say it changes (`ic3bounds.reencode`).  Five encodings per
board, and the ladder is deliberately not monotone in anything but predicate
count:

    binary      ceil(log2 |S|) bits of a state index.  The floor.
    native      the world's own variables.
    dual+k      the world's variables, plus a second name for the negation of
                the first k of them -- `free_pos3` beside `pos3`.
    onehot      one predicate per state.  m = |S|.

**What is comparable across a rung and what is not.**  A clause set over `dual`
vocabulary and a clause set over `onehot` vocabulary are sentences in two
different languages, so `n_clauses` may not be read across a board: fewer
clauses in a bigger alphabet is not a simpler certificate.  Two quantities *are*
facts about the world rather than about the alphabet, and the table is built on
them.  `coverage` -- how many of the |S| states the invariant admits -- because
a set of states does not care what it is called.  And **`abstraction`**, this
axis's own column: `n_satisfying / n_reachable`.  An inductive invariant must
contain the reachable set; 1.0 means it contains nothing else, i.e. the engine
computed reachability and called it an invariant, and larger means it found
something that genuinely generalises.  That number is what a reader adjudicates,
and it is the number the encoding moves most.

**What this axis can find that axis A cannot.**  Two failure shapes the item
named and axis A never reached.  A certificate can stop being *recheckable*: the
independent rechecker of `recheck/` speaks the peg vocabulary, so a rung whose
invariant is written in state-index bits has no form it can be handed in, and
the column says `not available` rather than scoring it.  And a certificate can
stop being *adjudicable* while still being perfectly valid -- `(!is_01011010)`
is a true clause about a real world that tells a reader nothing.  Both are
recorded, per rung, as data rather than as prose.

**The anchor.**  Every board's `native` rung is a rung of axis A -- same spec,
same system, same engine -- so the two axes cross at four points.
`check_anchors` compares them against the committed `axis_size.json` when one is
supplied and raises `AnchorDrift` on disagreement, for the reason `axis_size`
does: an axis whose shared points do not match the axis it claims to extend is
measuring a different family.
"""

import argparse
import datetime
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from ic3bounds import harness, recheck_column, reencode
from ic3bounds.harness import AnchorDrift, StepSpec

AXIS = "predicates"
AXIS_LETTER = "B"

PEG_FAMILY = "peg-1d"
WORLD_FAMILY = "worldgen catalogue"

DEFAULT_TIMEOUT_SECONDS = 300.0

# Four boards, so that a shape seen at one |S| has three chances to be an
# accident.  These are exactly axis A's rungs 6, 8, 10 and 12 -- the four it
# answered with room to spare -- which is what makes the `native` column of this
# table comparable with that one rather than merely similar to it.
PEG_BOARDS: Tuple[int, ...] = (6, 8, 10, 12)

# Two worlds from axis C's ladder.  They are the matched pair there -- same |S|,
# same predicate count, different family count -- and they are here for the one
# thing the peg family cannot offer: a native encoding that sits far ABOVE the
# information floor (17 floor cells one-hot for the agent), and can therefore be
# compressed as well as padded.  Peg-N is already at its floor, so `binary` on
# peg is a re-labelling and on these it is a 19 -> 7 compression.
WORLDS: Tuple[str, ...] = ("t1-tokens-lock", "t2-cycler-lock")

# `dual` past n would declare a predicate identical to one already there, which
# measures duplication rather than count -- `reencode.dual_recoding` refuses it.
def peg_schemes(n: int) -> Tuple[Tuple[str, int], ...]:
    """The five rungs of one board, in increasing predicate count."""
    return (
        (reencode.BINARY, 0),
        (reencode.NATIVE, 0),
        (reencode.DUAL, n // 2),
        (reencode.DUAL, n),
        (reencode.ONEHOT, 0),
    )


WORLD_SCHEMES: Tuple[Tuple[str, int], ...] = (
    (reencode.BINARY, 0),
    (reencode.NATIVE, 0),
    (reencode.ONEHOT, 0),
)

RECHECK_NOT_AVAILABLE = "n/a — no native form"
RECHECK_WHY = (
    "recheck/ grounds a rule set over the world's declared variables, so a "
    "certificate can only be handed to it in that vocabulary. A `dual` clause "
    "set has one -- `free_pos3` IS `!pos3`, and `reencode.desugar` rewrites it "
    "literal for literal -- so those rungs are rechecked in full. A `binary` or "
    "`onehot` clause set does not: its predicates name state indices, not world "
    "facts, and there is no rewriting that recovers what was never said. Those "
    "rows read 'no native form'. That is a boundary this axis was built to "
    "find, not a gap in it, and it is never scored as a pass."
)
WORLDGEN_RECHECK = "n/a — no worldgen transcriber"
WORLDGEN_RECHECK_WHY = (
    "the same reason axis C gives: recheck/ would need a second, independent "
    "transcription of worldgen's mechanisms, this axis does not build one, and "
    "a rechecker fed by the same adapter would only agree with itself."
)


# ------------------------------------------------------------------- the spec

@dataclass(frozen=True)
class PredicateSpec(StepSpec):
    """One rung: which world, which encoding.

    `n` stays what `harness` means by it -- the number of booleans IC3 searches
    over -- because `_blank_deterministic`, `cube_limit`, `literal_saturation`
    and the gate's width check all read it that way.  `n_states` is carried
    separately and corrected into the record, exactly as axis C does, since the
    harness's `2 ** n` default is wrong here by design and by a controlled
    amount: that gap IS the axis.
    """

    family: str = PEG_FAMILY
    world_id: str = ""
    board: int = 0
    scheme: str = reencode.NATIVE
    k: int = 0
    n_states: int = 0
    n_reachable: int = 0
    native_n: int = 0

    def as_json(self) -> Dict[str, Any]:
        payload = super().as_json()
        payload.update({
            "family": self.family,
            "world_id": self.world_id,
            "board": self.board,
            "scheme": self.scheme,
            "k": self.k,
            "n_states": self.n_states,
            "n_reachable": self.n_reachable,
            "native_n": self.native_n,
        })
        return payload

    @classmethod
    def from_json(cls, payload: Dict[str, Any]) -> "PredicateSpec":
        return cls(
            axis=str(payload["axis"]),
            label=str(payload["label"]),
            n=int(payload["n"]),
            initial=str(payload["initial"]),
            goal_states=tuple(str(g) for g in payload["goal_states"]),
            max_levels=int(payload.get("max_levels", harness.DEFAULT_MAX_LEVELS)),
            family=str(payload.get("family", PEG_FAMILY)),
            world_id=str(payload.get("world_id", "")),
            board=int(payload.get("board", 0)),
            scheme=str(payload.get("scheme", reencode.NATIVE)),
            k=int(payload.get("k", 0)),
            n_states=int(payload.get("n_states", 0)),
            n_reachable=int(payload.get("n_reachable", 0)),
            native_n=int(payload.get("native_n", 0)),
        )

    @property
    def encoding_label(self) -> str:
        return "dual+%d" % self.k if self.scheme == reencode.DUAL else self.scheme


# --------------------------------------------------------------- world sources

def peg_base(board: int, initial: str, goal: str, builder=None):
    """The un-recoded peg system, built by the harness's own builder.

    Routed through `harness.build_system` rather than calling `peg1d` here so
    that the world under every rung of this axis is, by construction, the world
    axis A measured -- not a second transcription of it that could drift.

    `builder` exists because `measure_one` *replaces* `harness.build_system` for
    the duration of a rung, and this function is called from inside that
    replacement.  Reading the module attribute there would call the replacement
    again, with a plain `StepSpec` that has no encoding on it -- an infinite
    regress that surfaces as an `AttributeError` in a child process, which is
    exactly as legible as it sounds.  The caller passes the function it
    displaced.
    """
    return (builder or harness.build_system)(
        StepSpec(axis=AXIS, label="peg%d" % board, n=board,
                 initial=initial, goal_states=(goal,))
    )


def world_base(world_id: str):
    from ic3bounds import worldgen_system
    return worldgen_system.build_system(world_id)


def base_system(spec: PredicateSpec, builder=None):
    if spec.family == PEG_FAMILY:
        return peg_base(spec.board, spec.initial, spec.goal_states[0], builder)
    return world_base(spec.world_id)


def reachable_count(system) -> int:
    """How many states the initial state can actually get to.

    The denominator of `abstraction`, and the only number on the row that says
    what a *perfect* answer would look like: an inductive invariant must admit
    at least these, so an invariant admitting exactly these has generalised
    nothing.  Breadth-first over the same relation IC3 searches, so the two
    cannot be counting different graphs.
    """
    seen = set(system.init)
    frontier = list(system.init)
    while frontier:
        state = frontier.pop()
        for target in system.successors(state):
            if target not in seen:
                seen.add(target)
                frontier.append(target)
    return len(seen)


# -------------------------------------------------------------- building specs

def peg_initial(n: int) -> str:
    """Axis A's configuration, verbatim -- see `axis_size.initial_for`."""
    return "0" + "1" * (n - 1)


def peg_goal(n: int) -> str:
    return "01" + "0" * (n - 2)


def spec_for_peg(board: int, scheme: str, k: int,
                 max_levels: int = harness.DEFAULT_MAX_LEVELS) -> PredicateSpec:
    initial, goal = peg_initial(board), peg_goal(board)
    system = peg_base(board, initial, goal)
    recoding = reencode.recoding_for(system, scheme, k)
    label = "%s/%s" % (system.name, recoding.label)
    return PredicateSpec(
        axis=AXIS, label=label, n=recoding.n_variables,
        initial=initial, goal_states=(goal,), max_levels=max_levels,
        family=PEG_FAMILY, world_id="", board=board,
        scheme=scheme, k=k,
        n_states=len(system.states),
        n_reachable=reachable_count(system),
        native_n=len(system.variables),
    )


def spec_for_world(world_id: str, scheme: str, k: int = 0,
                   max_levels: int = harness.DEFAULT_MAX_LEVELS) -> PredicateSpec:
    system = world_base(world_id)
    recoding = reencode.recoding_for(system, scheme, k)
    return PredicateSpec(
        axis=AXIS, label="%s/%s" % (world_id, recoding.label),
        n=recoding.n_variables,
        initial=system.render_state(system.init[0]),
        goal_states=tuple(system.render_state(s) for s in system.bad),
        max_levels=max_levels,
        family=WORLD_FAMILY, world_id=world_id, board=0,
        scheme=scheme, k=k,
        n_states=len(system.states),
        n_reachable=reachable_count(system),
        native_n=len(system.variables),
    )


def ladder(boards: Sequence[int] = PEG_BOARDS,
           worlds: Sequence[str] = WORLDS,
           max_levels: int = harness.DEFAULT_MAX_LEVELS) -> List[PredicateSpec]:
    """Every rung, cheapest board first.

    Ordered so that an interrupted run has walked whole boards rather than a
    slice of each: a board with one encoding measured says nothing at all, and
    the artefact is written after every rung precisely so a partial run is still
    an argument.
    """
    specs: List[PredicateSpec] = []
    for board in sorted(boards):
        for scheme, k in peg_schemes(board):
            specs.append(spec_for_peg(board, scheme, k, max_levels))
    for world_id in worlds:
        for scheme, k in WORLD_SCHEMES:
            specs.append(spec_for_world(world_id, scheme, k, max_levels))
    return specs


# ---------------------------------------------------------------- the child body

def _corrected(record: Dict[str, Any], spec: PredicateSpec) -> Dict[str, Any]:
    """Put the real state count where `harness._blank_deterministic` put 2^n.

    Axis C corrects the same field for the same reason.  Here the correction is
    load-bearing rather than cosmetic: on an `onehot` rung `2 ** n` is 2^256,
    and a row claiming IC3 searched that would invert the axis's whole finding.
    """
    record["deterministic"]["n_states"] = spec.n_states
    return record


def build_recoded(spec: PredicateSpec, builder=None):
    system = base_system(spec, builder)
    recoding = reencode.recoding_for(system, spec.scheme, spec.k)
    return system, recoding, reencode.reencode(system, recoding)


def _gate(spec: PredicateSpec, system, recoding, recoded,
          peg_gate=None) -> List[str]:
    """Both gates, in order: is the base the world, and is the recoding a
    renaming of it?

    The first is whichever gate the family already has -- the peg
    re-transcription for peg rungs, the worldgen adapter's nine checks for
    worldgen ones -- and it is run on the *base* system, before any re-encoding,
    because that is the system it knows how to check.  The second
    (`reencode.recoding_mismatches`) is what makes this axis's claim: the thing
    IC3 actually searched has the same states, the same edges and the same
    answer as the thing the first gate approved.

    `peg_gate` is passed for the same reason `peg_base` takes a `builder`: this
    runs from inside the function that displaced `harness.transcription_mismatches`,
    so reading the module attribute would call the displacement again.
    """
    problems: List[str] = []
    if spec.family == PEG_FAMILY:
        problems.extend((peg_gate or harness.transcription_mismatches)(
            system, spec.board, spec.initial, (peg_goal(spec.board),)))
    else:
        from ic3bounds import worldgen_system
        problems.extend(worldgen_system.transcription_mismatches(system))
    problems.extend(reencode.recoding_mismatches(system, recoded, recoding))
    return problems[:8]


def measure_one(spec: PredicateSpec) -> Dict[str, Any]:
    """One rung, here and now, with no budget.  This is the child's body.

    `harness.measure_in_process` unchanged, with its two world-specific seams
    substituted -- the same mechanism axis C uses, and for the same reason
    `ic3bounds/__init__.py` gives: the package gets one runner, one taxonomy and
    one record schema, or its three axes are three benchmarks that happen to
    share a directory.  Restored in `finally` because the tests call this
    in-process.
    """
    build, gate = harness.build_system, harness.transcription_mismatches
    cache: Dict[str, Any] = {}

    def _build(s):
        system, recoding, recoded = build_recoded(s, builder=build)
        cache["system"], cache["recoding"], cache["recoded"] = (
            system, recoding, recoded)
        return recoded

    harness.build_system = _build
    harness.transcription_mismatches = (
        lambda recoded, n, initial, goal_states, limit=8: _gate(
            spec, cache["system"], cache["recoding"], recoded, peg_gate=gate)
    )
    try:
        record = harness.measure_in_process(spec)
    except reencode.RecodingError as exc:
        # `harness.measure_in_process` does not guard `build_system`, because on
        # the peg family a build failure is an import error rather than a
        # result.  Here it is a result: a re-encoding that is not a bijection is
        # precisely "the System is not the world it claims to be", which the
        # taxonomy already has a word for.  Recorded and escalated rather than
        # raised -- the harness's own rule is that a refusal is rendered, not
        # turned into a traceback -- and never tabulated as a boundary.
        deterministic = harness._blank_deterministic(spec.n)
        deterministic["verdict"] = harness.ADAPTER_MISMATCH
        deterministic["escalate"] = True
        deterministic["detail"] = (
            "the re-encoding is not a renaming of the world it was built from: "
            "%s" % exc)
        record = harness._record(spec, deterministic, {}, None)
    finally:
        harness.build_system, harness.transcription_mismatches = build, gate
    return _corrected(record, spec)


# --------------------------------------------------------------- the subprocess

def run_step(spec: PredicateSpec,
             timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
             python: Optional[str] = None) -> Dict[str, Any]:
    """One rung, in a child process, under a wall-clock budget.

    Everything but the child module name is `harness`'s, reused rather than
    reimplemented.  The module has to differ because `harness.run_step` spawns
    `-m ic3bounds.harness`, whose `_child_main` builds a peg system and knows
    nothing about re-encoding.
    """
    command = [
        python or sys.executable, "-m", "ic3bounds.axis_predicates",
        "--child", "--spec", json.dumps(spec.as_json(), sort_keys=True),
    ]
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            command,
            cwd=harness._engine_rig_dir(),
            env=harness._child_environment(),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        wall = time.perf_counter() - started
        deterministic = harness._blank_deterministic(spec.n)
        deterministic["verdict"] = harness.TIMEOUT
        deterministic["machine_dependent"] = True
        deterministic["detail"] = (
            "killed after %.1fs of wall clock by this harness, on this machine. "
            "This is a statement about the budget and the hardware, NOT about "
            "the problem: the engine has no timeout of its own, max_levels=%d "
            "did not bind, and a longer budget or a faster machine may finish it."
            % (timeout_seconds, spec.max_levels)
        )
        record = harness._record(spec, deterministic,
                                 {"wall_seconds": round(wall, 6)}, timeout_seconds)
        return _corrected(record, spec)

    wall = time.perf_counter() - started
    payload = harness._parse_child_output(completed.stdout or "")
    if payload is None:
        deterministic = harness._blank_deterministic(spec.n)
        deterministic["verdict"] = harness.ENGINE_REFUSED
        deterministic["escalate"] = True
        tail = ((completed.stderr or "") or (completed.stdout or ""))[-400:]
        deterministic["detail"] = (
            "the child produced no record (exit %d) -- a crash, an OOM or an "
            "import failure, all of which are defects in the engine or the rig "
            "rather than boundaries of the problem: %s"
            % (completed.returncode, tail.strip())
        )
        record = harness._record(spec, deterministic,
                                 {"wall_seconds": round(wall, 6)}, timeout_seconds)
        return _corrected(record, spec)

    payload["budget_seconds"] = timeout_seconds
    payload["timing"]["wall_seconds"] = round(wall, 6)
    return payload


# ------------------------------------------------------------- derived columns

def derived(record: Dict[str, Any], spec: PredicateSpec) -> Dict[str, Any]:
    """The columns this axis exists for, kept out of `deterministic`.

    Out of it because `harness.DETERMINISTIC_FIELDS` is compared key by key by a
    verify pass and adding a key there would make every axis A artefact fail
    that comparison.  Everything here is a pure function of the record and the
    spec, so a verify pass re-derives it by calling this.
    """
    det = record["deterministic"]
    n_satisfying = det.get("n_satisfying")
    abstraction = None
    if n_satisfying is not None and spec.n_reachable:
        abstraction = round(n_satisfying / float(spec.n_reachable), 6)
    return {
        "encoding": spec.encoding_label,
        "scheme": spec.scheme,
        "k": spec.k,
        "n_predicates": spec.n,
        "native_n_predicates": spec.native_n,
        # `n_states` is deliberately NOT repeated here. It is a deterministic
        # field, it is corrected there, and a second copy in a dict a verify
        # pass does not compare is a copy that can drift from the one it does.
        "n_reachable": spec.n_reachable,
        "encoding_slack": reencode.encoding_slack(spec.n, spec.n_states),
        "abstraction": abstraction,
        "vocabulary": "world" if spec.scheme in (reencode.NATIVE, reencode.DUAL)
                      else "state index",
        "adjudicable": spec.scheme in (reencode.NATIVE, reencode.DUAL),
        "has_native_form": spec.scheme in (reencode.NATIVE, reencode.DUAL),
    }


def _clauses_off_the_row(system, deterministic: Dict[str, Any]):
    """Read a row's invariant back, with the three guards `clauses_of` has.

    `recheck_column.clauses_of` refuses a reading that does not re-render to the
    recorded string, or that produces a different clause or literal count than
    the row published, and its module says why: the invariant crosses the
    process boundary as text, and a reading that quietly lost a literal would
    still recheck ACCEPT while denoting a smaller set.  That function is peg-
    shaped -- it takes the row's `n` and builds a peg system -- so it cannot be
    called here, but its guards can be, and an adversarial pass over an earlier
    version of this file found them missing.
    """
    clauses = recheck_column.parse_cnf(deterministic.get("cnf_text"),
                                       system.variables)
    rendered = system.render_cnf(clauses)
    if rendered != (deterministic.get("cnf_text") or ""):
        raise recheck_column.ColumnError(
            "the row's invariant does not round-trip: read back as %r, recorded "
            "as %r" % (rendered, deterministic.get("cnf_text")))
    if len(clauses) != deterministic.get("n_clauses"):
        raise recheck_column.ColumnError(
            "the row's invariant reads as %d clause(s) and the row says %s"
            % (len(clauses), deterministic.get("n_clauses")))
    literals = sum(len(clause) for clause in clauses)
    if literals != deterministic.get("n_literals"):
        raise recheck_column.ColumnError(
            "the row's invariant reads as %d literal(s) and the row says %s -- "
            "a reading that lost one would still recheck ACCEPT"
            % (literals, deterministic.get("n_literals")))
    return clauses


def _blank_recheck(status: str, detail: str) -> Dict[str, Any]:
    column = {key: None for key in recheck_column.COLUMN_FIELDS}
    column["status"] = status
    column["finding"] = False
    column["detail"] = detail
    return column


def recheck_for(record: Dict[str, Any], spec: PredicateSpec) -> Dict[str, Any]:
    """The independent recheck column, via the native form where one exists.

    A `dual` rung's invariant is a clause set over `pos*` and `free_pos*`.
    `free_pos3` is not a new fact, it is `!pos3` under a second name, so the
    clause set has an exact native form -- `reencode.desugar` computes it -- and
    that form is an inductive invariant of the *native* peg system if and only
    if the original was one of the recoded system.  So it can be handed to the
    rechecker of `recheck/`, which shares no code with the engine and speaks
    only peg.  Doing that is the whole reason `desugar` exists.

    The translation is not trusted either.  `engines.ic3_pdr.check.verify` is
    re-run on the native system and the native clause set, and if its count
    disagrees with the recoded row's, that is a finding and the run fails on it
    -- the two numbers count the same set through a bijection and can only
    differ if the rewriting is wrong.

    Computed in the parent, after the budgeted child has exited, so it costs the
    rung's budget nothing and appears in no timing.
    """
    det = record["deterministic"]
    if det.get("verdict") != harness.INVARIANT:
        return _blank_recheck(
            recheck_column.NO_INVARIANT,
            "this rung produced no invariant, so there is nothing to recheck "
            "and nothing to pass.")
    if spec.family != PEG_FAMILY:
        return _blank_recheck(WORLDGEN_RECHECK, WORLDGEN_RECHECK_WHY)
    if spec.scheme not in (reencode.NATIVE, reencode.DUAL):
        return _blank_recheck(
            RECHECK_NOT_AVAILABLE,
            "the invariant is written in %s predicates, which name state "
            "indices rather than world facts, so it has no form recheck/ can "
            "read. Not a pass -- and this is the failure shape the item calls "
            "'certificate not recheckable'." % spec.scheme)

    system, recoding, recoded = build_recoded(spec)
    clauses = _clauses_off_the_row(recoded, det)
    native = reencode.desugar(recoding, clauses)

    from engines.ic3_pdr import check as ic3_check
    result = ic3_check.verify(system, native.clauses)
    if result.n_satisfying != det.get("n_satisfying"):
        column = _blank_recheck(
            "translation-mismatch",
            "the native form of this invariant holds on %d of %d states and the "
            "recoded one on %s -- a re-encoding is a bijection, so these count "
            "the same set and cannot differ. The rewriting is wrong."
            % (result.n_satisfying, result.n_states, det.get("n_satisfying")))
        column["finding"] = True
        return column

    native_record = {
        "spec": {
            "axis": AXIS, "label": spec.label, "n": spec.board,
            "initial": spec.initial, "goal_states": list(spec.goal_states),
        },
        "deterministic": {
            "verdict": harness.INVARIANT,
            "cnf_text": system.render_cnf(native.clauses),
            "n_clauses": native.n_clauses,
            "n_literals": native.literals_after,
            "n_satisfying": result.n_satisfying,
            "n_states": result.n_states,
        },
    }
    column = recheck_column.column_for(native_record)
    column = dict(column)
    column["detail"] = "%s [rechecked through the native form: %d clause(s), " \
                       "%d literal(s), %d tautolog%s dropped]" % (
        column.get("detail") or "",
        native.n_clauses, native.literals_after, native.tautologies_dropped,
        "y" if native.tautologies_dropped == 1 else "ies")
    return column


# ------------------------------------------------------------------ the report

def boundary_of(steps: Sequence[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """The first rung that did not produce an answer, and what stopped it.

    Same rule as axis A's, and the same carve-out: `engine-refused` and
    `adapter-mismatch` are defects in the measurement rather than boundaries of
    the problem, so they never terminate the table.  They are surfaced through
    `escalations`.
    """
    answered = [s for s in steps
                if s["deterministic"]["verdict"] in harness.ANSWERS]
    for step in steps:
        verdict = step["deterministic"]["verdict"]
        if verdict in harness.ANSWERS or verdict in harness.ESCALATING:
            continue
        return {
            "label": step["spec"]["label"],
            "encoding": step["spec"].get("scheme"),
            "n_predicates": step["spec"]["n"],
            "n_states": step["deterministic"]["n_states"],
            "verdict": verdict,
            "machine_dependent": bool(step["deterministic"]["machine_dependent"]),
            "budget_seconds": step.get("budget_seconds"),
            "largest_answered": (answered[-1]["spec"]["label"]
                                 if answered else None),
            "detail": step["deterministic"]["detail"],
        }
    return None


def escalations(steps: Sequence[Dict[str, Any]]) -> List[str]:
    """Rows that are defects rather than data.  Non-empty means stop and fix."""
    return [
        "%s: %s -- %s" % (step["spec"]["label"],
                          step["deterministic"]["verdict"],
                          step["deterministic"]["detail"])
        for step in steps
        if step["deterministic"]["escalate"]
    ]


def recheck_findings(steps: Sequence[Dict[str, Any]]) -> List[str]:
    return [
        "%s: %s -- %s" % (step["spec"]["label"],
                          (step.get("recheck") or {}).get("status"),
                          (step.get("recheck") or {}).get("detail"))
        for step in steps
        if (step.get("recheck") or {}).get("finding")
    ]


def _board_key(step: Dict[str, Any]) -> str:
    spec = step["spec"]
    return spec.get("world_id") or "peg%d" % spec.get("board", 0)


def held_fixed(steps: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """One block per board: the rungs that share a state space exactly.

    This is the axis's control and the only comparison on it that means
    anything.  Every row of a block searched the *same states* and the *same
    edges*; the only difference between them is how many booleans said so.  A
    ratio taken inside a block attributes to predicate count; a ratio taken
    across blocks attributes to nothing, and the table does not offer one.

    Rungs that did not answer are listed and excluded from the ratios rather
    than dropped, so a block whose spread is computed over three of five rungs
    says which two are missing.
    """
    blocks: Dict[str, List[Dict[str, Any]]] = {}
    for step in steps:
        blocks.setdefault(_board_key(step), []).append(step)

    out: List[Dict[str, Any]] = []
    for key, group in blocks.items():
        answered = [s for s in group
                    if s["deterministic"]["verdict"] == harness.INVARIANT
                    and (s.get("timing") or {}).get("wall_seconds") is not None]
        rows = []
        for step in group:
            det = step["deterministic"]
            der = step.get("derived") or {}
            rows.append({
                "label": step["spec"]["label"],
                "encoding": der.get("encoding"),
                "n_predicates": der.get("n_predicates"),
                "verdict": det["verdict"],
                "n_clauses": det["n_clauses"],
                "coverage": det["coverage"],
                "abstraction": der.get("abstraction"),
                "ic3_seconds": (step.get("timing") or {}).get("ic3_seconds"),
            })
        # By label, not by `step not in answered`: that compares whole record
        # dicts, and two rungs whose records happened to be equal would erase
        # each other from the list of what is missing.
        answered_labels = {s["spec"]["label"] for s in answered}
        block_unanswered = [s["spec"]["label"] for s in group
                            if s["spec"]["label"] not in answered_labels]
        times = [s["timing"]["ic3_seconds"] for s in answered
                 if s["timing"].get("ic3_seconds") is not None]
        predicates = [s["spec"]["n"] for s in answered]
        block: Dict[str, Any] = {
            "board": key,
            "n_states": group[0]["deterministic"]["n_states"],
            "n_reachable": (group[0].get("derived") or {}).get("n_reachable"),
            "n_rungs": len(group),
            "n_answered": len(answered),
            "unanswered": block_unanswered,
            "predicate_range": ([min(predicates), max(predicates)]
                                if predicates else None),
            "rows": rows,
            "machine_dependent": True,
        }
        if times and min(times) > 0:
            block["ic3_seconds_range"] = [min(times), max(times)]
            block["ic3_seconds_spread"] = round(max(times) / min(times), 3)
            fastest = min(answered, key=lambda s: s["timing"]["ic3_seconds"])
            block["fastest"] = {
                "label": fastest["spec"]["label"],
                "encoding": (fastest.get("derived") or {}).get("encoding"),
                "n_predicates": fastest["spec"]["n"],
                "abstraction": (fastest.get("derived") or {}).get("abstraction"),
                "adjudicable": (fastest.get("derived") or {}).get("adjudicable"),
            }
        out.append(block)
    return out


def monotone_in_predicates(blocks: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Does cost rise with predicate count inside a block?  Asked, not assumed.

    The hypothesis this axis was built to test, stated as a testable sentence
    and answered per block: within one held-fixed state space, is `ic3_seconds`
    non-decreasing in `n_predicates`?  A single block that says no refutes
    "IC3 pays for the vocabulary" as a general law, and the table has to say so
    even though a monotone ladder would have been the tidier result.
    """
    rows = []
    for block in blocks:
        answered = [row for row in block["rows"]
                    if row["ic3_seconds"] is not None]
        answered.sort(key=lambda row: row["n_predicates"])
        pairs = list(zip(answered, answered[1:]))
        breaks = [
            "%s (m=%d, %.4fs) is slower than %s (m=%d, %.4fs) although it "
            "declares fewer predicates"
            % (left["encoding"], left["n_predicates"], left["ic3_seconds"],
               right["encoding"], right["n_predicates"], right["ic3_seconds"])
            for left, right in pairs
            if left["ic3_seconds"] > right["ic3_seconds"]
        ]
        rows.append({
            "board": block["board"],
            "n_compared": len(answered),
            "monotone": (None if len(answered) < 2 else not breaks),
            "breaks": breaks,
        })
    verdicts = [row["monotone"] for row in rows if row["monotone"] is not None]
    return {
        "question": "inside one held-fixed state space, is IC3's own clock "
                    "non-decreasing in the number of predicates?",
        "per_board": rows,
        "monotone_everywhere": (all(verdicts) if verdicts else None),
        "machine_dependent": True,
        "read_it_as": "a wall clock, so this is a statement about this machine. "
                      "It is reported because a NON-monotone block is robust to "
                      "the machine in a way a monotone one is not: an ordering "
                      "that reverses under a 20x spread is not noise.",
    }


def cost_of_adjudicability(blocks: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """What the cheapest encoding costs a reader.

    The finding this axis hands the paper, in one number per block: if the
    fastest encoding on a board is one whose predicates name state indices, then
    the speed was bought by giving up the certificate -- and the paper sentence
    "the shapes LP cannot reach are covered by IC3" has to be read as covering
    them with an object nobody can adjudicate.
    """
    rows = []
    for block in blocks:
        fastest = block.get("fastest")
        if not fastest:
            continue
        rows.append({
            "board": block["board"],
            "fastest": fastest["label"],
            "fastest_is_adjudicable": bool(fastest.get("adjudicable")),
            "fastest_abstraction": fastest.get("abstraction"),
            "spread": block.get("ic3_seconds_spread"),
        })
    unreadable = [row for row in rows if not row["fastest_is_adjudicable"]]
    return {
        "rows": rows,
        "n_boards": len(rows),
        "n_boards_where_fastest_is_unreadable": len(unreadable),
        "abstraction_note": "abstraction 1.0 means the invariant admits exactly "
                            "the reachable states -- the engine computed "
                            "reachability and returned it as a law. It is "
                            "sound, it is what the three Lean theorems ask "
                            "for, and it explains nothing.",
    }


def report(steps: Sequence[Dict[str, Any]], timeout_seconds: float,
           rungs: Sequence[str], complete: bool,
           stopped_early: Optional[str] = None,
           command: str = "") -> Dict[str, Any]:
    from ic3bounds import axis_size

    blocks = held_fixed(steps)
    return {
        "axis": AXIS,
        "axis_letter": AXIS_LETTER,
        "question": "at a state space held EXACTLY fixed -- same states, same "
                    "edges, same answer -- what does IC3 pay for the number of "
                    "predicates used to say it?",
        "family": "%s and %s" % (PEG_FAMILY, WORLD_FAMILY),
        "ladder": list(rungs),
        "budget_seconds": timeout_seconds,
        "complete": complete,
        "stopped_early": stopped_early,
        "why_this_axis_exists": (
            "on peg-N the predicate count and the state count are the same "
            "number, so axis A cannot tell which of them it measured. Every "
            "block here re-encodes ONE world: the states, the labelled edges, "
            "the initial state and the bad set are identical across a block by "
            "construction and by a gate, and only the vocabulary moves."
        ),
        "what_is_comparable": (
            "coverage and abstraction, which are facts about the world. NOT "
            "n_clauses or n_literals, which are sentences in whichever "
            "language the rung speaks: an onehot rung's single clause is not a "
            "simpler certificate than a native rung's eight."
        ),
        "anchor": {
            "rule": "every board's `native` rung is the same spec axis A ran at "
                    "that n, so the two axes cross once per board.",
            "checked": "ic3bounds.axis_predicates.check_anchors, which raises "
                       "AnchorDrift, when an axis_size.json is supplied.",
        },
        "gate": {
            "runs": "before IC3, in the child, on every rung",
            "first": "the family's own transcription gate on the BASE system "
                     "(harness for peg, worldgen_system for worldgen)",
            "second": "reencode.recoding_mismatches -- the recoded system has "
                      "the same |S|, the same labelled edges, the same init "
                      "and the same bad set as the base one, bijectively",
            "on_failure": "verdict adapter-mismatch, escalate=true, never "
                          "tabulated as a boundary",
        },
        "recheck": {
            "column": "steps[].recheck",
            "via": "reencode.desugar -- a dual clause set is rewritten literal "
                   "for literal into the native vocabulary and handed to "
                   "recheck/, which shares no code with the engine",
            "cross_check": "engines.ic3_pdr.check.verify re-counts the native "
                           "form; a bijection cannot change the count, so a "
                           "disagreement is a finding and fails the run",
            "not_available": RECHECK_WHY,
            "worldgen": WORLDGEN_RECHECK_WHY,
            "taxonomy": dict(recheck_column.TAXONOMY),
        },
        "determinism": {
            "deterministic_half": "re-derived exactly by a verify pass.",
            "timing_half": "presence and ordering only, never equality.",
            "correction": "deterministic.n_states is overwritten with the real "
                          "state count; harness fills it as 2**n, which on an "
                          "onehot rung would claim a space 2^|S| wide.",
        },
        "held_fixed": blocks,
        "monotone_in_predicates": monotone_in_predicates(blocks),
        "cost_of_adjudicability": cost_of_adjudicability(blocks),
        "boundary": boundary_of(steps),
        "escalations": escalations(steps),
        "recheck_findings": recheck_findings(steps),
        "steps": list(steps),
        "provenance": axis_size.provenance(command),
    }


# ------------------------------------------------------------------ the anchor

def check_anchors(steps: Sequence[Dict[str, Any]], axis_size_path: str) -> None:
    """Every `native` rung must be the axis A row it claims to be.  Raises.

    The argument this axis makes is that its blocks extend axis A rather than
    sitting beside it, and the whole of that argument rests on the `native`
    rungs being the same measurement.  If they are not, the two tables describe
    two families and no sentence may draw on both.
    """
    with open(axis_size_path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    by_n = {step["spec"]["n"]: step["deterministic"]
            for step in payload.get("steps", [])}

    drift: Dict[str, Any] = {}
    for step in steps:
        spec = step["spec"]
        if spec.get("scheme") != reencode.NATIVE or spec.get("board") not in by_n:
            continue
        theirs = by_n[spec["board"]]
        mine = step["deterministic"]
        for field in ("verdict", "cnf_text", "coverage", "n_clauses",
                      "n_literals", "converged_at_frame"):
            if theirs.get(field) != mine.get(field):
                drift.setdefault(spec["label"], {})[field] = {
                    "axis_size": theirs.get(field), "axis_predicates": mine.get(field),
                }
    if drift:
        raise AnchorDrift(
            "the native rungs are not axis A's rows, so these blocks do not "
            "extend that ladder: %s" % json.dumps(drift, sort_keys=True)
        )


# --------------------------------------------------------------------- the run

def run(specs: Optional[Sequence[PredicateSpec]] = None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        max_levels: int = harness.DEFAULT_MAX_LEVELS,
        on_step: Optional[Callable[[Dict[str, Any]], None]] = None,
        command: str = "",
        boards: Sequence[int] = PEG_BOARDS,
        worlds: Sequence[str] = WORLDS) -> Dict[str, Any]:
    """Walk the ladder.  `on_step` is called after every rung, with the report so
    far, so an interrupted run still leaves the rungs it finished on disk.

    There is no early stop.  Cost on this axis is not monotone in anything the
    ladder orders by -- that is the finding, not an accident -- so a timeout at
    one rung licenses no prediction about the next, and skipping it would be
    guessing rather than measuring.
    """
    rungs = list(specs) if specs is not None else ladder(boards, worlds, max_levels)
    labels = [spec.label for spec in rungs]
    steps: List[Dict[str, Any]] = []
    current = report([], timeout_seconds, labels, False, None, command)

    for index, spec in enumerate(rungs):
        record = run_step(spec, timeout_seconds=timeout_seconds)
        record["derived"] = derived(record, spec)
        record["recheck"] = recheck_for(record, spec)
        steps.append(record)
        current = report(steps, timeout_seconds, labels,
                         index == len(rungs) - 1, None, command)
        if on_step is not None:
            on_step(current)
    return current


# ---------------------------------------------------------------- the markdown

def markdown(payload: Dict[str, Any]) -> str:
    """The table, computed from nothing the JSON does not already carry."""

    def cell(value: Any) -> str:
        return "-" if value is None else str(value)

    lines = [
        "| board | \\|S\\| | encoding | m | slack | verdict | clauses | "
        "literals | saturation | coverage | abstraction | ic3 (s) | wall (s) | "
        "recheck |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for step in payload["steps"]:
        det = step["deterministic"]
        der = step.get("derived") or {}
        timing = step.get("timing") or {}
        column = step.get("recheck") or {}
        lines.append(
            "| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |"
            % (
                _board_key(step), cell(det["n_states"]), cell(der.get("encoding")),
                cell(der.get("n_predicates")), cell(der.get("encoding_slack")),
                det["verdict"], cell(det["n_clauses"]), cell(det["n_literals"]),
                cell(det["literal_saturation"]), cell(det["coverage"]),
                cell(der.get("abstraction")),
                "-" if timing.get("ic3_seconds") is None
                else "%.4f" % timing["ic3_seconds"],
                "-" if timing.get("wall_seconds") is None
                else "%.3f" % timing["wall_seconds"],
                cell(column.get("status")),
            )
        )
    return "\n".join(lines)


# --------------------------------------------------------------------- the CLI

def _write_json(path: str, payload: Any) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=2, sort_keys=False)
        fh.write("\n")
    os.replace(tmp, path)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="ic3bounds.axis_predicates")
    parser.add_argument("--child", action="store_true",
                        help="run one rung in this process and print the record")
    parser.add_argument("--spec", default=None, help="a PredicateSpec as JSON")
    parser.add_argument("--out", default=None, help="run directory to write")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--max-levels", type=int, default=harness.DEFAULT_MAX_LEVELS)
    parser.add_argument("--boards", default=None,
                        help="comma-separated peg board sizes, e.g. 6,8")
    parser.add_argument("--worlds", default=None,
                        help="comma-separated worldgen ids, or 'none'")
    parser.add_argument("--anchor", default=None,
                        help="an axis_size.json to check the native rungs against")
    args = parser.parse_args(argv)

    if args.child:
        if not args.spec:
            parser.error("--child needs --spec")
        record = measure_one(PredicateSpec.from_json(json.loads(args.spec)))
        sys.stdout.write(harness.SENTINEL + json.dumps(record, sort_keys=False) + "\n")
        sys.stdout.flush()
        return 0

    if not args.out:
        parser.error("--out is required unless --child is given")

    boards = ([int(part) for part in args.boards.split(",") if part.strip()]
              if args.boards else list(PEG_BOARDS))
    if args.worlds is None:
        worlds = list(WORLDS)
    elif args.worlds.strip().lower() == "none":
        worlds = []
    else:
        worlds = [part.strip() for part in args.worlds.split(",") if part.strip()]

    out_dir = os.path.abspath(args.out)
    os.makedirs(out_dir, exist_ok=True)
    artefact = os.path.join(out_dir, "axis_predicates.json")
    command = "python -m ic3bounds.axis_predicates --out %s --timeout %g" % (
        args.out, args.timeout)
    started = datetime.datetime.now(datetime.timezone.utc)

    def on_step(payload: Dict[str, Any]) -> None:
        _write_json(artefact, payload)
        step = payload["steps"][-1]
        det, der = step["deterministic"], step["derived"]
        timing = step.get("timing") or {}
        print("  %-28s |S|=%-6d m=%-5d %-16s clauses=%-4s coverage=%-12s "
              "abstraction=%-8s %-10s recheck=%s"
              % (step["spec"]["label"], det["n_states"], der["n_predicates"],
                 det["verdict"], det["n_clauses"], det["coverage"],
                 der["abstraction"],
                 "-" if timing.get("wall_seconds") is None
                 else "%.3fs" % timing["wall_seconds"],
                 (step.get("recheck") or {}).get("status")),
              flush=True)

    rungs = ladder(boards, worlds, args.max_levels)
    print("axis %s: %d rungs over %d board(s) and %d world(s), %.0fs budget "
          "each -> %s"
          % (AXIS, len(rungs), len(boards), len(worlds), args.timeout, artefact),
          flush=True)
    payload = run(specs=rungs, timeout_seconds=args.timeout,
                  max_levels=args.max_levels, on_step=on_step, command=command)
    _write_json(artefact, payload)

    if args.anchor:
        try:
            check_anchors(payload["steps"], args.anchor)
        except AnchorDrift as exc:
            print("\nANCHOR DRIFT -- the native rungs are not axis A's rows:\n  %s"
                  % exc)
            return 2
        print("\nanchor: every native rung matches %s" % args.anchor)

    elapsed = (datetime.datetime.now(datetime.timezone.utc) - started).total_seconds()
    print("\n" + markdown(payload))
    for block in payload["held_fixed"]:
        if block.get("ic3_seconds_spread") is not None:
            print("\n%s: |S|=%d held fixed, m from %d to %d, IC3's clock spreads "
                  "%.1fx; fastest is %s (adjudicable=%s)"
                  % (block["board"], block["n_states"],
                     block["predicate_range"][0], block["predicate_range"][1],
                     block["ic3_seconds_spread"], block["fastest"]["encoding"],
                     block["fastest"]["adjudicable"]))
    print("\nmonotone in predicate count everywhere: %s"
          % payload["monotone_in_predicates"]["monotone_everywhere"])
    print("wrote %s (%d rung(s), %.1fs total)" % (artefact, len(payload["steps"]),
                                                  elapsed))

    if payload["escalations"] or payload["recheck_findings"]:
        for line in payload["escalations"]:
            print("  ESCALATION - %s" % line)
        for line in payload["recheck_findings"]:
            print("  RECHECK FINDING - %s" % line)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
