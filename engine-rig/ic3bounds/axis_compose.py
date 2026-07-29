"""Axis C -- mechanism composition, with state-space size held roughly fixed.

Axis A varies |S| on one family and finds where IC3 stops.  That leaves the
question this axis exists for: when a problem is *composed* out of several
independent mechanisms, does IC3 pay for the composition, or only for the size?
The two are confounded in every naturally occurring benchmark, because adding a
mechanism adds state.  So this ladder holds the declared state space roughly
fixed and varies the number of `worldgen` mechanism families:

    step  world                   families  declared product  variables
    1     t1-switch-latch            1              34            18
    2     t1-tokens-lock             1             128            19
    3     t2-cycler-lock             2             128            19   <- matched
    4     t2-lock-fragile            2             576            30
    5     t3-cycler-portal-lock      3             432            41
    6     t3-latch-maze              3            1680            42   (stretch)

**Steps 2 and 3 are the axis.**  Same declared product (128), same variable
count (19), one family against two.  Every other pair on the ladder moves size
and family count together and can only ever be suggestive; that pair is the one
place a difference could be attributed to composition rather than to size, and
the whole ladder is built around making it exist.

**The `shrunken-domain` caveat, which this axis cannot get rid of.**
`worldgen` states are multi-valued -- `(agent: Cell, vars: Tuple[int, ...])`,
where a `consumable` tile is 0/1/2 and a `color_cycle` phase runs over
`range(k)` -- and `engines.ic3_pdr` is boolean.  Bridging that gap means a
one-hot encoding, and a one-hot encoding over the full 2^n bit space is hopeless
(`t3-latch-maze` would be 2^42).  So `ic3bounds.worldgen_system` hands IC3 the
**declared product**: floor cells crossed with each slot's own domain, 34 to 1680
states, and nothing else exists.

Therefore **the invariant on every row of this table is inductive over the
well-formed subspace and over nothing else.**  Structurally that is the
`shrunken-domain` forgery `recheck/` was written to catch: a certificate that
looks strong because its domain was quietly made small.  What separates this from
a forgery is that the shrink is declared, is carried on every row as
`n_states` / `declared_product`, and is forced rather than convenient.  It is a
caveat and it is stated as one; nothing here claims a theorem about the bit
space.

**The recheck column reads "not available", not "passed".**  `recheck/` accepts a
`certificate-v1` against a rule set built by a *second, independent*
transcription.  For the peg family `ic3bounds.emit` can do that because
`interop.peg1d` and `harness._independent_moves` are two transcriptions of one
short rule.  For `worldgen` the second transcription would have to re-implement
`consumable`'s three-state tile, portal landing and the settle fixpoint -- a
worldgen-to-ruleset transcriber this axis deliberately does not build.  Writing
"passed" from a rechecker fed by the same adapter would make the column mean
nothing, which is the failure `recheck/README.md` opens by naming.  So it says
what is true: not available.

**The gate that does exist.**  Before IC3 runs on any world,
`worldgen_system.transcription_mismatches` asserts that the adapter's transition
relation equals `GridWorld.transitions()` edge for edge on the reachable set,
that the encoding round-trips, that the reachable set is inside the declared
subspace, and that the chosen bad set is disjoint from `GridWorld.reachable()`
and separated by a mechanism rather than by a wall.  A row that fails it is
verdict `adapter-mismatch` -- escalated, never `timeout`, never a capability
claim.  See that module for what the gate is and is not.

**Why the bad set is chosen rather than inherited.**  19 of `worldgen`'s 20
worlds are solvable, so "can the agent reach the goal" returns a
`Counterexample`: a cheap breadth-first walk that measures nothing about
invariant scaling.  `System.bad` is any subset of the declared space, so each
row asks for an unreachable one that a *mechanism* separates -- "the agent stands
on the lock with fewer than k tokens", "the agent stands on the goal with the
latch unset".  Naively picking an unreachable *cell* would have been worse than
useless: only 10 of the 20 worlds have one and 8 of those have exactly one,
almost always a walled-off pocket whose invariant is "the agent is never there".

**Running it.**

    cd engine-rig
    python -m ic3bounds.axis_compose --out runs/<id> --timeout 180
    python -m ic3bounds.axis_compose --out runs/<id> --only t1-switch-latch

Writes `axis_compose.json` into the run directory after every rung, for the
reason `ic3bounds/__main__.py` gives: an interrupted run must leave the rungs it
finished on disk.  Exit 0 if the axis ran (a `timeout` row is a result), 1 if
anything escalated.
"""

import argparse
import datetime
import json
import os
import sys
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from ic3bounds import harness, worldgen_system
from ic3bounds.harness import StepSpec

AXIS = "compose"
FAMILY = "worldgen catalogue"

#: The ladder, in the order it is walked.  Not sorted: the point is the family
#: count, and `t3-cycler-portal-lock` (432) is deliberately smaller than
#: `t2-lock-fragile` (576) so that size and family count are not collinear.
LADDER: Tuple[str, ...] = (
    "t1-switch-latch",
    "t1-tokens-lock",
    "t2-cycler-lock",
    "t2-lock-fragile",
    "t3-cycler-portal-lock",
    "t3-latch-maze",
)

#: The one comparison on the ladder that isolates composition from size.
MATCHED_PAIR: Tuple[str, str] = ("t1-tokens-lock", "t2-cycler-lock")

#: The rung that is expected to be expensive, and is on the ladder to find out
#: rather than to be reported as a boundary if it is not reached.
STRETCH: Tuple[str, ...] = ("t3-latch-maze",)

DEFAULT_TIMEOUT_SECONDS = 180.0

RECHECK_STATUS = "not available"
RECHECK_WHY = (
    "recheck/ accepts a certificate only against a rule set built by a second, "
    "independent transcription. A worldgen-to-ruleset transcriber would have to "
    "re-implement consumable's three-state tile, portal landing and the settle "
    "fixpoint, and this axis does not build one. A rechecker fed by the same "
    "adapter would agree with itself, so the column says 'not available' rather "
    "than 'passed'."
)


# ------------------------------------------------------------------- the spec

@dataclass(frozen=True)
class ComposeSpec(StepSpec):
    """`StepSpec` with the world named and its declared size carried alongside.

    A subclass rather than a parallel type, so that `harness.measure_in_process`
    -- the one runner in this package -- can be handed it unchanged.  The
    inherited fields keep their meanings: `n` is the number of boolean variables
    (which is what `literal_saturation` and `cube_limit` are per), `initial` and
    `goal_states` are the *rendered* initial and bad states, and the gate checks
    the System the child builds against both.  `n_states` is carried because the
    declared product is not 2^n and `harness._blank_deterministic` cannot know
    that; see `_corrected`.
    """

    world_id: str = ""
    families: Tuple[str, ...] = ()
    n_states: int = 0
    n_bad: int = 0
    bad_key: str = ""

    def as_json(self) -> Dict[str, Any]:
        payload = StepSpec.as_json(self)
        payload.update({
            "world_id": self.world_id,
            "families": list(self.families),
            "n_families": len(self.families),
            "n_states": self.n_states,
            "n_bad": self.n_bad,
            "bad_key": self.bad_key,
        })
        return payload

    @classmethod
    def from_json(cls, payload: Dict[str, Any]) -> "ComposeSpec":
        return cls(
            axis=str(payload["axis"]),
            label=str(payload["label"]),
            n=int(payload["n"]),
            initial=str(payload["initial"]),
            goal_states=tuple(str(g) for g in payload["goal_states"]),
            max_levels=int(payload.get("max_levels", harness.DEFAULT_MAX_LEVELS)),
            world_id=str(payload["world_id"]),
            families=tuple(str(f) for f in payload.get("families", ())),
            n_states=int(payload.get("n_states", 0)),
            n_bad=int(payload.get("n_bad", 0)),
            bad_key=str(payload.get("bad_key", "")),
        )


def spec_for(world_id: str,
             max_levels: int = harness.DEFAULT_MAX_LEVELS) -> ComposeSpec:
    """Build the rung's spec from `worldgen` alone -- no transition relation.

    `worldgen_system.summary` is deliberately cheap: the parent has no use for
    the relation, the child builds its own, and the spec that crosses between
    them carries the rendered initial and bad states so the child's gate can
    check that the two agree.
    """
    info = worldgen_system.summary(world_id)
    return ComposeSpec(
        axis=AXIS,
        label=world_id,
        n=int(info["n_variables"]),
        initial=str(info["initial"]),
        goal_states=tuple(info["bad_states"]),
        max_levels=max_levels,
        world_id=world_id,
        families=tuple(info["families"]),
        n_states=int(info["declared_product"]),
        n_bad=int(info["n_bad"]),
        bad_key=str(info["bad"]["key"]),
    )


# ---------------------------------------------------------------- the child body

def _corrected(record: Dict[str, Any], spec: ComposeSpec) -> Dict[str, Any]:
    """Put the declared product where `harness._blank_deterministic` put 2^n.

    The one field of the harness's schema that assumes the peg family.  `n_states`
    is filled from the spec alone there, as `2 ** n`, because for peg-N the state
    space *is* the bit space.  Here it is not -- `System.states` is an explicitly
    enumerated tuple and that is the entire premise of this axis -- so the value
    is corrected rather than left to claim a space IC3 never searched.  Every
    other field is the harness's, unmodified; `coverage` and `coverage_ratio`
    already come from `check.verify`, which counts the real `System.states`.
    """
    record["deterministic"]["n_states"] = spec.n_states
    return record


def measure_one(spec: ComposeSpec) -> Dict[str, Any]:
    """One rung, here and now, with no budget.  This is the child's body.

    It is `harness.measure_in_process` -- the same runner, the same six-verdict
    taxonomy, the same record schema -- with the two world-specific seams
    substituted: which `System` to build, and which gate proves it is the world.
    Those two are module-level names in `harness` precisely so that the peg
    family is a *choice* the runner makes rather than something baked into it;
    swapping them here is what lets axis C avoid inventing a second runner, which
    is the one thing `ic3bounds/__init__.py` says the package must not do.

    Restored in `finally` because the tests call this in-process, and a patch
    that leaked would make every later peg row build a worldgen system.
    """
    build, gate = harness.build_system, harness.transcription_mismatches
    harness.build_system = lambda s: worldgen_system.build_system(s.world_id)
    harness.transcription_mismatches = worldgen_system.transcription_mismatches
    try:
        record = harness.measure_in_process(spec)
    finally:
        harness.build_system, harness.transcription_mismatches = build, gate
    return _corrected(record, spec)


# ------------------------------------------------------------- the subprocess

def run_step(spec: ComposeSpec,
             timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
             python: Optional[str] = None) -> Dict[str, Any]:
    """One rung, in a child process, under a wall-clock budget.

    Everything here except the module name is `harness`'s, reused rather than
    reimplemented: the environment, the sentinel parsing, the blank record and
    the record shape.  The module name has to differ because
    `harness.run_step` spawns `-m ic3bounds.harness`, whose `_child_main` builds
    a peg system from the spec -- so a worldgen rung needs its own child entry
    point, and this is it.  The `timeout` branch below is the harness's wording
    for the harness's reason: a killed run is a statement about this budget on
    this machine, and it is flagged `machine_dependent` so a verify pass does not
    compare it for equality.
    """
    import subprocess

    command = [
        python or sys.executable, "-m", "ic3bounds.axis_compose",
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

def families_in_invariant(cnf_text: Optional[str],
                          info: Dict[str, Any]) -> List[str]:
    """Which mechanism families' variables the invariant actually mentions.

    The column that turns "composition cost nothing" from an assertion into an
    observation with a reason attached.  An invariant that names one family's
    slots in a three-family world never had to reason about the composition at
    all, and the row's cost is evidence about *that property*, not about
    composed worlds in general.  `at_rNcM` variables are the agent's position and
    belong to no family, so they are reported separately as `geometry`.
    """
    if not cnf_text:
        return []
    found: List[str] = []
    if "at_r" in cnf_text:
        found.append("geometry")
    for slot in info["layout"]["slots"]:
        if slot["name"] in cnf_text and slot["family"] not in found:
            found.append(slot["family"])
    return found


def derived(record: Dict[str, Any], info: Dict[str, Any]) -> Dict[str, Any]:
    """Columns computed from the deterministic half and the world, nothing else.

    Kept out of the record's `deterministic` dict on purpose: that dict is
    `harness.DETERMINISTIC_FIELDS` exactly, and a verify pass compares it key by
    key. These are re-derivable from it and are reported alongside.
    """
    det = record["deterministic"]
    n_states = det.get("n_states")
    n_satisfying = det.get("n_satisfying")
    n_bad = info["n_bad"]
    excluded = (None if n_satisfying is None or n_states is None
                else n_states - n_satisfying)
    return {
        "n_families": info["n_families"],
        "families": list(info["families"]),
        "n_bad": n_bad,
        "bad_fraction": round(n_bad / float(n_states), 6) if n_states else None,
        "states_excluded": excluded,
        # 1.0 means the invariant is exactly the complement of the bad set and
        # generalisation bought nothing; above 1.0 it had something to say.
        "strengthening": (None if excluded is None or not n_bad
                          else round(excluded / float(n_bad), 6)),
        "families_in_invariant": families_in_invariant(det.get("cnf_text"), info),
        "recheck": RECHECK_STATUS,
    }


# -------------------------------------------------------------- the comparison

def matched_comparison(steps: Sequence[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Steps 2 vs 3: one family against two, at the same declared size.

    Returns `None` rather than a half-comparison if either rung did not produce
    an invariant -- a timing ratio against a row that timed out would be a
    comparison of two different things wearing one number.
    """
    by_id = {s["spec"]["world_id"]: s for s in steps}
    left, right = MATCHED_PAIR
    if left not in by_id or right not in by_id:
        return None
    one, two = by_id[left], by_id[right]
    d1, d2 = one["deterministic"], two["deterministic"]
    if d1["verdict"] != harness.INVARIANT or d2["verdict"] != harness.INVARIANT:
        return {
            "comparable": False,
            "why": "one of the matched rungs did not return an invariant (%s: %s, "
                   "%s: %s), and a ratio across two different verdicts would be a "
                   "number with no referent"
                   % (left, d1["verdict"], right, d2["verdict"]),
        }
    t1 = (one["timing"] or {}).get("ic3_seconds")
    t2 = (two["timing"] or {}).get("ic3_seconds")
    return {
        "comparable": True,
        "one_family": left,
        "two_families": right,
        "n_states": [d1["n_states"], d2["n_states"]],
        "n_variables": [one["spec"]["n"], two["spec"]["n"]],
        "n_bad": [one["spec"]["n_bad"], two["spec"]["n_bad"]],
        "n_clauses": [d1["n_clauses"], d2["n_clauses"]],
        "n_literals": [d1["n_literals"], d2["n_literals"]],
        "converged_at_frame": [d1["converged_at_frame"], d2["converged_at_frame"]],
        "states_blocked": [d1["states_blocked"], d2["states_blocked"]],
        "coverage": [d1["coverage"], d2["coverage"]],
        "ic3_seconds": [t1, t2],
        # Reported, and flagged for what it is: a wall clock on one machine on
        # one afternoon. `bench/README.md` rule 3 -- timings are never compared
        # for equality by a verify pass, and this ratio is not a deterministic
        # field.
        "ic3_seconds_ratio": (round(t2 / t1, 3)
                              if isinstance(t1, (int, float)) and t1
                              and isinstance(t2, (int, float)) else None),
        "machine_dependent": True,
    }


def separability(steps: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """How many families each invariant actually had to talk about.

    The column that decides how far the headline of this axis reaches.  If every
    invariant names one family's variables, then no row on the ladder ever asked
    IC3 to reason across a composition, and "composition cost nothing" is a
    statement about *separable properties in composed worlds* rather than about
    composed worlds.  That is a real result and a narrower one, and the table is
    only honest if it says which it has.
    """
    rows = []
    for step in steps:
        if step["deterministic"]["verdict"] != harness.INVARIANT:
            continue
        mentioned = [f for f in (step["derived"]["families_in_invariant"] or [])
                     if f != "geometry"]
        rows.append({
            "world_id": step["spec"]["world_id"],
            "n_families": step["spec"]["n_families"],
            "families_in_invariant": mentioned,
            "n_families_in_invariant": len(mentioned),
            "strengthening": step["derived"]["strengthening"],
        })
    if not rows:
        return {"rows": [], "separable_everywhere": None, "note": "no invariant rows"}
    separable = all(row["n_families_in_invariant"] <= 1 for row in rows)
    return {
        "rows": rows,
        "separable_everywhere": separable,
        "note": (
            "Every invariant on this ladder names the variables of at most one "
            "mechanism family (plus the agent's position). The extra families in "
            "the 2- and 3-family worlds contribute state that the invariant never "
            "mentions, so IC3 was never asked to reason across the composition. "
            "The ladder therefore measures composition cost for a SEPARABLE "
            "property; a property whose proof had to couple two families would be "
            "a different measurement and this table does not stand in for it."
            if separable else
            "At least one invariant names more than one family's variables, so at "
            "least one row required reasoning across the composition."
        ),
    }


def boundary_of(steps: Sequence[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """The first rung that did not produce an answer, and what stopped it.

    Same rule as axis A: an escalating verdict is not a boundary, because
    `engine-refused` and `adapter-mismatch` say the measurement is broken rather
    than that the problem is hard.
    """
    solved = [s for s in steps if s["deterministic"]["verdict"] in harness.ANSWERS]
    for step in steps:
        verdict = step["deterministic"]["verdict"]
        if verdict in harness.ANSWERS or verdict in harness.ESCALATING:
            continue
        return {
            "world_id": step["spec"]["world_id"],
            "label": step["spec"]["label"],
            "n_families": step["spec"]["n_families"],
            "n_states": step["deterministic"]["n_states"],
            "verdict": verdict,
            "machine_dependent": bool(step["deterministic"]["machine_dependent"]),
            "budget_seconds": step.get("budget_seconds"),
            "largest_answered": (solved[-1]["spec"]["world_id"] if solved else None),
            "detail": step["deterministic"]["detail"],
        }
    return None


def escalations(steps: Sequence[Dict[str, Any]]) -> List[str]:
    return [
        "%s: %s -- %s" % (step["spec"]["label"],
                          step["deterministic"]["verdict"],
                          step["deterministic"]["detail"])
        for step in steps
        if step["deterministic"]["escalate"]
    ]


def gate_results(steps: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """One line per rung: did the adapter gate pass, and what would it have said.

    Reported explicitly rather than inferred from the absence of an
    `adapter-mismatch`, because "the gate passed" is the load-bearing claim under
    every other number in the table and a reader should not have to reconstruct
    it from a silence.
    """
    out = []
    for step in steps:
        verdict = step["deterministic"]["verdict"]
        passed = verdict != harness.ADAPTER_MISMATCH
        out.append({
            "world_id": step["spec"]["world_id"],
            "passed": passed,
            "checks": "edges vs GridWorld.transitions() on the reachable set, "
                      "encode/decode round trip, reachable set inside the declared "
                      "subspace, init, bad set disjoint from GridWorld.reachable() "
                      "and separated by a mechanism",
            "detail": None if passed else step["deterministic"]["detail"],
        })
    return out


# ------------------------------------------------------------------ the artefact

def report(steps: Sequence[Dict[str, Any]], timeout_seconds: float,
           ladder: Sequence[str], complete: bool,
           stopped_early: Optional[str] = None,
           command: str = "") -> Dict[str, Any]:
    from ic3bounds import axis_size

    return {
        "axis": AXIS,
        "axis_letter": "C",
        "question": "at a held-fixed declared state-space size, does IC3 pay for "
                    "the number of mechanism families a world composes, or only "
                    "for the size?",
        "family": FAMILY,
        "ladder": list(ladder),
        "matched_pair": {
            "worlds": list(MATCHED_PAIR),
            "why": "same declared product (128) and same variable count (19), one "
                   "family against two. Every other adjacent pair moves size and "
                   "family count together, so this is the only comparison on the "
                   "ladder that can attribute a difference to composition.",
        },
        "stretch": list(STRETCH),
        "budget_seconds": timeout_seconds,
        "complete": complete,
        "stopped_early": stopped_early,
        "shrunken_domain_caveat": (
            "worldgen states are multi-valued and IC3 is boolean, so the adapter "
            "hands IC3 the DECLARED PRODUCT -- floor cells crossed with each "
            "mechanism slot's own domain -- not the 2^n bit space. Every invariant "
            "in this table is therefore inductive over that well-formed subspace "
            "and over nothing else. Structurally that is the shrunken-domain "
            "forgery recheck/ exists to catch; what makes it a caveat rather than "
            "a forgery is that the shrink is declared, is carried on every row as "
            "n_states, and is forced -- a one-hot relaxation over 2^42 states has "
            "no enumerating oracle. No row here claims a theorem about the bit "
            "space."
        ),
        "recheck": {
            "status": RECHECK_STATUS,
            "why": RECHECK_WHY,
        },
        "adapter_gate": {
            "runs": "before IC3, on every world",
            "on_failure": "verdict adapter-mismatch, escalated -- never timeout "
                          "and never a capability claim",
            "results": gate_results(steps),
        },
        "vacuity": {
            "guard": "every row carries n_satisfying / n_states and near_vacuous "
                     "at ratio >= %s" % harness.NEAR_VACUOUS_RATIO,
            "read_it_with": "bad_fraction and strengthening. On this axis coverage "
                            "is high BY CONSTRUCTION: the bad set is a small "
                            "mechanism-separated corner of the declared space, so "
                            "1 - coverage can never exceed bad_fraction by much. "
                            "The quantity that carries information is "
                            "`strengthening` = states_excluded / n_bad -- 1.0 means "
                            "the invariant is exactly the negation of the goal and "
                            "generalisation bought nothing.",
        },
        "determinism": {
            "deterministic_half": "Re-derived exactly by a verify pass, as on axis "
                                  "A. The one correction this axis makes is "
                                  "n_states: harness._blank_deterministic fills it "
                                  "as 2**n, which is right for peg-N and wrong "
                                  "here, where System.states is an enumerated "
                                  "tuple.",
            "timing_half": "Presence and ordering only, never equality.",
            "sorting": "Declared states, each state's move list, and the bad set "
                       "are all sorted, following "
                       "engines.ic3_pdr.system.peg_system; worldgen itself has no "
                       "RNG anywhere.",
        },
        "boundary": boundary_of(steps),
        "escalations": escalations(steps),
        "matched_comparison": matched_comparison(steps),
        "separability": separability(steps),
        "steps": list(steps),
        "provenance": axis_size.provenance(command),
    }


def markdown(payload: Dict[str, Any]) -> str:
    lines = [
        "| world | fam | \\|S\\| | vars | bad | verdict | clauses | literals | "
        "widest | saturation | frame | blocked | coverage | strengthen | "
        "invariant mentions | recheck | wall (s) |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for step in payload["steps"]:
        det = step["deterministic"]
        der = step.get("derived") or {}
        wall = (step.get("timing") or {}).get("wall_seconds")

        def cell(value):
            return "-" if value is None else str(value)

        lines.append(
            "| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | "
            "%s | %s | %s | %s |"
            % (
                step["spec"]["world_id"], step["spec"]["n_families"],
                det["n_states"], step["spec"]["n"], step["spec"]["n_bad"],
                det["verdict"], cell(det["n_clauses"]), cell(det["n_literals"]),
                cell(det["widest_clause"]), cell(det["literal_saturation"]),
                cell(det["converged_at_frame"]), cell(det["states_blocked"]),
                cell(det["coverage"]), cell(der.get("strengthening")),
                ", ".join(der.get("families_in_invariant") or []) or "-",
                der.get("recheck", RECHECK_STATUS),
                "-" if wall is None else "%.3f" % wall,
            )
        )
    return "\n".join(lines)


# ------------------------------------------------------------------- the ladder

def run(worlds: Sequence[str] = LADDER,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        max_levels: int = harness.DEFAULT_MAX_LEVELS,
        on_step: Optional[Callable[[Dict[str, Any]], None]] = None,
        command: str = "") -> Dict[str, Any]:
    """Walk the ladder in its declared order.

    No early stop.  Axis A stops after two timeouts because its cost is monotone
    in `n`, so a third rung would spend a full budget to record a word already
    known.  This ladder is deliberately *not* monotone -- step 5 is smaller than
    step 4 -- so a missed budget says nothing about the rung after it, and
    skipping would throw away the only readings that could separate composition
    from size.
    """
    steps: List[Dict[str, Any]] = []
    ordered = list(worlds)
    current = report([], timeout_seconds, ordered, False, None, command)

    for index, world_id in enumerate(ordered):
        info = worldgen_system.summary(world_id)
        record = run_step(spec_for(world_id, max_levels=max_levels),
                          timeout_seconds=timeout_seconds)
        record["world"] = {
            "summary": {k: v for k, v in info.items() if k != "layout"},
            "layout": info["layout"],
            "ground_truth": worldgen_system.ground_truth(world_id),
        }
        record["derived"] = derived(record, info)
        steps.append(record)
        complete = index == len(ordered) - 1
        current = report(steps, timeout_seconds, ordered, complete, None, command)
        if on_step is not None:
            on_step(current)
    return current


# ---------------------------------------------------------------------- the CLI

def _write_json(path: str, payload: Any) -> None:
    """LF-pinned and replaced atomically -- the reader of a half-written artefact
    is the next agent, and a truncated JSON file is worse than a missing one."""
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=2, sort_keys=False)
        fh.write("\n")
    os.replace(tmp, path)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="ic3bounds.axis_compose")
    parser.add_argument("--child", action="store_true",
                        help="run one rung and print a sentinel-prefixed record")
    parser.add_argument("--spec", default=None, help="a ComposeSpec as JSON")
    parser.add_argument("--out", default=None, help="run directory to write")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_SECONDS,
                        help="wall-clock budget per rung, in seconds")
    parser.add_argument("--only", default=None,
                        help="comma-separated world ids, in ladder order")
    parser.add_argument("--max-levels", type=int, default=harness.DEFAULT_MAX_LEVELS)
    args = parser.parse_args(argv)

    if args.child:
        if not args.spec:
            parser.error("--child needs --spec")
        spec = ComposeSpec.from_json(json.loads(args.spec))
        record = measure_one(spec)
        sys.stdout.write(harness.SENTINEL + json.dumps(record, sort_keys=False) + "\n")
        sys.stdout.flush()
        return 0

    if not args.out:
        parser.error("--out is required unless --child is given")

    out_dir = os.path.abspath(args.out)
    os.makedirs(out_dir, exist_ok=True)
    if args.only:
        wanted = [w.strip() for w in args.only.split(",") if w.strip()]
        worlds = [w for w in LADDER if w in wanted] or wanted
    else:
        worlds = list(LADDER)

    command = "python -m ic3bounds.axis_compose --out %s --timeout %g%s" % (
        args.out, args.timeout, " --only %s" % args.only if args.only else "",
    )
    artefact = os.path.join(out_dir, "axis_compose.json")
    started = datetime.datetime.now(datetime.timezone.utc)

    def on_step(payload: Dict[str, Any]) -> None:
        _write_json(artefact, payload)
        step = payload["steps"][-1]
        det, der = step["deterministic"], step["derived"]
        wall = (step.get("timing") or {}).get("wall_seconds")
        print("  %-24s fam=%d |S|=%-5d %-16s clauses=%-4s literals=%-5s "
              "frame=%-4s coverage=%-10s strengthen=%-6s %s"
              % (step["spec"]["world_id"], der["n_families"], det["n_states"],
                 det["verdict"], det["n_clauses"], det["n_literals"],
                 det["converged_at_frame"], det["coverage"],
                 der["strengthening"],
                 "-" if wall is None else "%.3fs" % wall),
              flush=True)

    print("axis compose: %d rungs, %.0fs budget each -> %s"
          % (len(worlds), args.timeout, artefact), flush=True)
    payload = run(worlds=worlds, timeout_seconds=args.timeout,
                  max_levels=args.max_levels, on_step=on_step, command=command)
    _write_json(artefact, payload)

    elapsed = (datetime.datetime.now(datetime.timezone.utc) - started).total_seconds()
    print("\n" + markdown(payload))
    comparison = payload["matched_comparison"]
    if comparison and comparison.get("comparable"):
        print("\nmatched pair (%s vs %s): |S| %s, vars %s, clauses %s, frame %s, "
              "blocked %s, ic3 seconds %s (ratio %s -- one machine, one afternoon)"
              % (comparison["one_family"], comparison["two_families"],
                 comparison["n_states"], comparison["n_variables"],
                 comparison["n_clauses"], comparison["converged_at_frame"],
                 comparison["states_blocked"], comparison["ic3_seconds"],
                 comparison["ic3_seconds_ratio"]))
    elif comparison:
        print("\nmatched pair not comparable: %s" % comparison["why"])
    print("\nseparability: %s" % payload["separability"]["note"])
    boundary = payload["boundary"]
    if boundary:
        print("\nboundary: %s (|S|=%d, %d families) -- %s"
              % (boundary["label"], boundary["n_states"], boundary["n_families"],
                 boundary["verdict"]))
    else:
        print("\nno boundary reached: every rung answered within the budget.")
    print("recheck column: %s -- %s" % (RECHECK_STATUS, RECHECK_WHY))
    print("wrote %s (%d rung(s), %.1fs total)" % (artefact, len(payload["steps"]),
                                                  elapsed))

    if payload["escalations"]:
        print("\nESCALATIONS (%d) -- these are defects, not boundaries:"
              % len(payload["escalations"]))
        for line in payload["escalations"]:
            print("  - %s" % line)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
