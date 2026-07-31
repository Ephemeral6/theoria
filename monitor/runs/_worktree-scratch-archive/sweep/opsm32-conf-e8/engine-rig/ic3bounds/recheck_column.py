"""The recheck column: what an *independent* checker says about each rung.

E8 asks, per gradient step, for four things: solve time, invariant size, whether
an independent checker's recheck passes, and the failure mode.  `harness.py`
produced the first two and its own six-verdict taxonomy; `emit.py` could turn an
`Invariant` into a `recheck` certificate; `recheck/` could check one.  Nothing
joined them, so the third column did not exist.  This module is the join.

**The taxonomy is `recheck`'s own exit codes, not a new one.**  `python -m
recheck` already answers with a status a caller can read without parsing prose,
and those five codes are exactly the failure modes the item asks to be named:

    0  ACCEPT             the three conditions hold on the emitted predicate
    1  REJECT             at least one fails -- the independent checker refuses
                          the engine's invariant, which is a finding about the
                          invariant or the rule set, never a rounding error
    2  would-not-load     the rule set or the certificate never became an
                          object to check.  This is the honest reading of an
                          *uncheckable* certificate: a peg board of n >= 20
                          declares a product above `recheck.ruleset.MAX_STATES`
                          (1_000_000) and `load_ruleset` refuses it, so there is
                          no verdict rather than a passing one
    3  INCONSISTENT       the conditions hold and the goal is reachable anyway.
                          A defect in the rechecker, escalated rather than
                          rounded down to a pass
    4  rechecker-crashed  the recheck itself failed.  Distinguished from REJECT
                          because Python's own exit status for an uncaught
                          exception is 1, and a crash that looks like a refusal
                          is a benchmark that lies quietly

and one row type that is not an exit code at all:

    n/a -- no invariant   the rung timed out, hit the level cap, or the engine
                          was refused.  There is no invariant, so there is
                          nothing for an independent checker to check.  Such a
                          row reads `n/a -- no invariant` and never `passed`;
                          `is_pass` is False for it, by construction.

**Why the parent re-renders rather than re-running IC3.**  The invariant crosses
the process boundary as `cnf_text`, in the engine's own rendering and in
`emit.ordered_clauses`' order.  Reading it back costs nothing, where a second
`ic3()` call would cost the ladder's whole budget over again -- 310 seconds at
n=12 and n=13 alone.  The read-back is not trusted: the clauses are re-rendered
through `System.render_cnf` and compared with the recorded string character for
character, and their counts against the row's own `n_clauses` and `n_literals`.
A parser that lost or invented a literal fails there, before anything is checked.

**The count cross-check rides on every row, and it is what makes the column
non-vacuous.**  A verdict alone does not say the predicate denotes the set the
engine converged on: on peg-6 a one-literal weakening is ACCEPTed while denoting
27 states instead of 30 (`tests/test_ic3bounds_emit.py`).  So every row carries
both counts -- the engine's, over 2^n boolean tuples, and the rechecker's, over
the product of the declared domains -- and whether they agree.  `emit.cross_check`
does the comparison; it is called with `strict=False` here because a table that
raises reports nothing, and a disagreement has to be *shown*.  It is not
softened: a row whose counts disagree is a finding, `is_pass` is False, and
`axis_size` fails the run on it.

**Two transcriptions, still two.**  The rule set the rechecker reads is
`recheck.build_cases`' -- written from the geometry, importing nothing from
`engines/` -- and is preferred from the committed, byte-checked case file when
one exists at that size.  This module writes only the invariant, through
`emit.py`.  Nothing here builds a rule set out of the `System` IC3 searched.
"""

import os
from typing import Any, Dict, List, Optional, Sequence, Tuple

from ic3bounds import harness
from recheck import build_cases

EXIT_ACCEPT = 0
EXIT_REJECT = 1
EXIT_WOULD_NOT_LOAD = 2
EXIT_INCONSISTENT = 3
EXIT_CRASHED = 4

#: `python -m recheck`'s exit code -> the word this column prints for it.
STATUS_BY_EXIT: Dict[int, str] = {
    EXIT_ACCEPT: "ACCEPT",
    EXIT_REJECT: "REJECT",
    EXIT_WOULD_NOT_LOAD: "would-not-load",
    EXIT_INCONSISTENT: "INCONSISTENT",
    EXIT_CRASHED: "rechecker-crashed",
}

#: The row that has nothing to check.  Never "passed", and `is_pass` says so.
NO_INVARIANT = "n/a — no invariant"

#: A row whose spec is not a single-goal peg board.  Axis A never produces one;
#: it is here so a caller that does gets a word rather than a wrong verdict.
NOT_A_PEG_BOARD = "n/a — not a single-goal peg board"

#: Every key of the column, in the order they are written.  Present on every
#: row, `None` where the status makes them inapplicable -- a missing key and a
#: null are different claims, as in `harness.DETERMINISTIC_FIELDS`.
COLUMN_FIELDS: Tuple[str, ...] = (
    "status",
    "exit_code",
    "ruleset",
    "ruleset_source",
    "certificate",
    "engine_n_states",
    "engine_n_satisfying",
    "recheck_n_states",
    "recheck_n_satisfying",
    "counts_agree",
    "agrees_with_recorded_row",
    "conditions",
    "finding",
    "detail",
)

TAXONOMY: Dict[str, str] = {
    "0": "ACCEPT -- the three conditions hold on the emitted predicate",
    "1": "REJECT -- an independent checker refuses the engine's invariant",
    "2": "would-not-load -- the rule set or certificate never became an object "
         "to check (a peg board of n >= 20 exceeds recheck.ruleset.MAX_STATES = "
         "1000000). This is the honest reading of an uncheckable certificate",
    "3": "INCONSISTENT -- the conditions hold and the goal is reachable anyway; "
         "a defect in the rechecker, escalated rather than rounded to a pass",
    "4": "rechecker-crashed -- the recheck itself failed, kept separate from "
         "REJECT because Python's own status for a crash is 1",
    "n/a": "%s -- the rung produced no invariant, so there is nothing for an "
           "independent checker to check. Not a pass." % NO_INVARIANT,
}


class ColumnError(RuntimeError):
    """The column could not be produced.  Reported as `rechecker-crashed`."""


def _blank() -> Dict[str, Any]:
    return {key: None for key in COLUMN_FIELDS}


def _ordered(column: Dict[str, Any]) -> Dict[str, Any]:
    return {key: column.get(key) for key in COLUMN_FIELDS}


# ------------------------------------------------------------------ the parser

def parse_cnf(text: Optional[str], variables: Sequence[str]) -> List[frozenset]:
    """`(!pos1 | pos2) & (pos1 | !pos2)` -> the clause set that rendered it.

    The inverse of `System.render_cnf`, and never used without the round trip in
    `clauses_of` checking it.  `"true"` is that function's word for the empty
    clause set and is read back as one.
    """
    if text is None:
        raise ColumnError("the row carries no cnf_text, so there is no "
                          "invariant to hand an independent checker")
    stripped = text.strip()
    if stripped in ("", "true"):
        return []
    index_of = {name: index for index, name in enumerate(variables)}
    clauses: List[frozenset] = []
    for chunk in stripped.split(" & "):
        if not (chunk.startswith("(") and chunk.endswith(")")):
            raise ColumnError("clause %r is not parenthesised as render_clause "
                              "writes them" % chunk)
        literals: List[Tuple[int, bool]] = []
        for token in chunk[1:-1].split(" | "):
            value = not token.startswith("!")
            name = token if value else token[1:]
            if name not in index_of:
                raise ColumnError("literal %r names no variable of the system "
                                  "(%s)" % (token, ", ".join(variables)))
            literals.append((index_of[name], value))
        clause = frozenset(literals)
        if len(clause) != len(literals):
            raise ColumnError("clause %r repeats a literal, so reading it back "
                              "would lose one" % chunk)
        clauses.append(clause)
    return clauses


def clauses_of(system, deterministic: Dict[str, Any]) -> List[frozenset]:
    """The row's invariant, read back and then proved to be the row's invariant.

    Three guards, because a silent parser bug here would make every verdict
    below it a verdict about a different clause set: the re-rendering must equal
    the recorded string exactly, and the clause and literal counts must equal the
    ones the harness recorded from the object the engine returned.
    """
    text = deterministic.get("cnf_text")
    clauses = parse_cnf(text, system.variables)
    rendered = system.render_cnf(clauses)
    if rendered != text:
        raise ColumnError(
            "reading the invariant back did not reproduce it: recorded %r, "
            "re-rendered %r" % (text, rendered))
    n_clauses = deterministic.get("n_clauses")
    if n_clauses is not None and len(clauses) != n_clauses:
        raise ColumnError("the row records %d clause(s); reading its cnf_text "
                          "back gives %d" % (n_clauses, len(clauses)))
    n_literals = deterministic.get("n_literals")
    if n_literals is not None and sum(len(c) for c in clauses) != n_literals:
        raise ColumnError("the row records %d literal(s); reading its cnf_text "
                          "back gives %d" % (n_literals,
                                             sum(len(c) for c in clauses)))
    return clauses


# ----------------------------------------------------------------- the ruleset

def case_name(n: int, start: str) -> str:
    return build_cases.peg_name(start, n)


def case_path(n: int, start: str) -> str:
    return os.path.join(build_cases.CASES_DIR, "%s.rules.json" % case_name(n, start))


def ruleset_for(n: int, start: str, goal: str):
    """`(rule set, where it came from)`, from the independent transcription.

    The committed case is preferred where one exists: it is byte-checked by
    `python -m recheck.build_cases --check`, so using it makes the column a
    statement about a file under review rather than about something generated on
    the spot.  Above the committed sizes the same generator is called in memory
    -- `recheck.ruleset.ruleset_from_spec` hashes it over exactly the bytes
    `build_cases` would have written, so the binding still means the file it
    would be.  Either way the rule set comes from `recheck/`, never from the
    `System` IC3 searched.
    """
    from recheck.ruleset import load_ruleset, ruleset_from_spec

    path = case_path(n, start)
    if os.path.exists(path):
        # Repo-relative on purpose: an absolute path in an artefact is this
        # machine's directory layout wearing the clothes of a result.
        return load_ruleset(path), "recheck/cases/%s.rules.json" % case_name(n, start)
    # OPS-M cycle 32 merge note: `peg_ruleset` is `(start, goal, name, gradient)`
    # after the merge -- `n` is derived from `start`, and `gradient=True` selects
    # the `interop.peg1d` provenance these sizes carry.  The old positional
    # `(start, n, goal)` silently passed an int as `goal`.
    return (ruleset_from_spec(build_cases.peg_ruleset(start, goal=goal,
                                                      gradient=True)),
            "recheck.build_cases.peg_ruleset(%r, %d, %r) -- no committed case "
            "at this size" % (start, n, goal))


# ------------------------------------------------------------------ the column

def _no_invariant(deterministic: Dict[str, Any]) -> Dict[str, Any]:
    column = _blank()
    column["status"] = NO_INVARIANT
    column["counts_agree"] = None
    column["finding"] = False
    column["detail"] = (
        "the rung's verdict is %r, so no invariant exists and an independent "
        "checker has nothing to check. This row is not a pass and must not be "
        "read as one." % deterministic.get("verdict")
    )
    return _ordered(column)


def _failed(exit_code: int, detail: str, **extra: Any) -> Dict[str, Any]:
    column = _blank()
    column.update(extra)
    column["status"] = STATUS_BY_EXIT[exit_code]
    column["exit_code"] = exit_code
    column["finding"] = True
    column["detail"] = detail
    return _ordered(column)


def column_for(record: Dict[str, Any]) -> Dict[str, Any]:
    """One row's recheck column, computed from the record and nothing else.

    Runs in the parent, after the budgeted child has exited, so it costs the
    rung's wall-clock budget nothing and appears in no timing.  It is
    deterministic: same record in, same column out.
    """
    deterministic = record.get("deterministic") or {}
    spec = record.get("spec") or {}
    if deterministic.get("verdict") != harness.INVARIANT:
        return _no_invariant(deterministic)

    goal_states = list(spec.get("goal_states") or ())
    if len(goal_states) != 1:
        column = _blank()
        column["status"] = NOT_A_PEG_BOARD
        column["finding"] = False
        column["detail"] = (
            "the rule set generator `recheck.build_cases.peg_ruleset` takes one "
            "goal state and this rung declares %d, so no independent rule set "
            "exists for it. Not a pass." % len(goal_states))
        return _ordered(column)

    n = int(spec["n"])
    start = str(spec["initial"])
    goal = str(goal_states[0])
    name = case_name(n, start)
    certificate_name = "%s-ic3-invariant" % name

    try:
        ruleset, source = ruleset_for(n, start, goal)
    except Exception as exc:                     # noqa: BLE001 -- see the docstring
        return _failed(
            EXIT_WOULD_NOT_LOAD,
            "the rule set for %s would not load, so the certificate is "
            "uncheckable rather than refused: %s: %s"
            % (name, type(exc).__name__, exc),
            ruleset=name, certificate=certificate_name,
            engine_n_states=deterministic.get("n_states"),
            engine_n_satisfying=deterministic.get("n_satisfying"))

    from ic3bounds import emit

    try:
        system = harness.build_system(harness.StepSpec(
            axis=str(spec.get("axis", "size")),
            label=str(spec.get("label", name)),
            n=n, initial=start, goal_states=(goal,)))
        clauses = clauses_of(system, deterministic)
        certificate = emit.certificate_spec(
            system, clauses, name=certificate_name,
            ruleset_name=ruleset.name, ruleset_sha256=ruleset.sha256,
            produced_by="engines/ic3_pdr, via ic3bounds/emit.py (E8 axis A)")
        crossed = emit.cross_check(system, clauses, ruleset, certificate,
                                   strict=False)
    except Exception as exc:                     # noqa: BLE001 -- deliberately broad
        return _failed(
            EXIT_CRASHED,
            "producing or rechecking the certificate for %s failed, which is "
            "neither a REJECT nor a pass: %s: %s"
            % (name, type(exc).__name__, exc),
            ruleset=ruleset.name, ruleset_source=source,
            certificate=certificate_name,
            engine_n_states=deterministic.get("n_states"),
            engine_n_satisfying=deterministic.get("n_satisfying"))

    column = _blank()
    column.update({
        "ruleset": ruleset.name,
        "ruleset_source": source,
        "certificate": certificate_name,
        "engine_n_states": crossed.engine_n_states,
        "engine_n_satisfying": crossed.engine_n_satisfying,
        "recheck_n_states": crossed.recheck_n_states,
        "recheck_n_satisfying": crossed.recheck_n_satisfying,
        "conditions": dict(sorted(crossed.recheck_conditions.items())),
    })

    # The engine counted twice: once inside the budgeted child, once here.  If
    # those two disagree the row is not describing the run it claims to.
    recorded_ok = (crossed.engine_n_satisfying == deterministic.get("n_satisfying")
                   and crossed.engine_n_states == deterministic.get("n_states"))
    column["agrees_with_recorded_row"] = recorded_ok

    if crossed.verdict is None:
        # `cross_check` returned before the rechecker ever counted anything --
        # an off-domain literal, or a binding the certificate could not satisfy.
        # Nothing was checked, and an unchecked translation is not a weak pass.
        column.update(_failed(
            EXIT_WOULD_NOT_LOAD,
            "the certificate for %s was never evaluated, so there is no verdict "
            "to report: %s" % (name, "; ".join(crossed.reasons) or "no reason given"),
            **{key: column[key] for key in
               ("ruleset", "ruleset_source", "certificate", "engine_n_states",
                "engine_n_satisfying", "conditions")}))
        column["agrees_with_recorded_row"] = recorded_ok
        return _ordered(column)

    from recheck.verify import ACCEPT, INCONSISTENT, REJECT

    exit_code = {ACCEPT: EXIT_ACCEPT, REJECT: EXIT_REJECT,
                 INCONSISTENT: EXIT_INCONSISTENT}[crossed.verdict]
    column["status"] = STATUS_BY_EXIT[exit_code]
    column["exit_code"] = exit_code
    column["counts_agree"] = bool(crossed.counts_agree)
    column["finding"] = bool(
        exit_code != EXIT_ACCEPT or not crossed.counts_agree or not recorded_ok)

    detail = []
    if exit_code != EXIT_ACCEPT:
        failed = sorted(k for k, ok in crossed.recheck_conditions.items() if not ok)
        detail.append("the independent checker returned %s (failing: %s)"
                      % (crossed.verdict, ", ".join(failed) or "none named"))
    if not crossed.counts_agree:
        detail.append(
            "COUNT MISMATCH: the engine's invariant holds on %s of %s states, "
            "the emitted predicate on %s of %s -- the predicate denotes a "
            "different set, so the verdict is about a different object"
            % (crossed.engine_n_satisfying, crossed.engine_n_states,
               crossed.recheck_n_satisfying, crossed.recheck_n_states))
    if not recorded_ok:
        detail.append(
            "the row records %s/%s satisfying; re-counting the same invariant "
            "here gives %s/%s"
            % (deterministic.get("n_satisfying"), deterministic.get("n_states"),
               crossed.engine_n_satisfying, crossed.engine_n_states))
    if not column["finding"]:
        detail.append(
            "%s of %s states, counted over 2^%d boolean tuples by the engine and "
            "over the product of %s's declared domains by the rechecker"
            % (crossed.engine_n_satisfying, crossed.engine_n_states, n,
               ruleset.name))
    detail.extend(crossed.reasons)
    column["detail"] = " | ".join(detail) or "no reason given"
    return _ordered(column)


# ------------------------------------------------------------------ the reading

def is_pass(column: Optional[Dict[str, Any]]) -> bool:
    """ACCEPT *and* the two counts agree.  Nothing else is a pass.

    Written as one function because "did the recheck pass?" is the question the
    item asks, and answering it from `status` alone would call the peg-6
    dropped-literal forgery green.
    """
    if not column:
        return False
    return (column.get("status") == "ACCEPT"
            and column.get("counts_agree") is True
            and column.get("agrees_with_recorded_row") is True)


def cell(column: Optional[Dict[str, Any]]) -> str:
    """The table cell: the status, and the two counts where there are two."""
    if not column:
        return "-"
    status = column.get("status") or "-"
    engine = column.get("engine_n_satisfying")
    rechecked = column.get("recheck_n_satisfying")
    if engine is None or rechecked is None:
        # One number is not a comparison, so none is offered: a row that was
        # refused before anything was counted says so and stops there.
        return status
    return "%s (%s=%s%s)" % (status, rechecked, engine,
                             "" if column.get("counts_agree") else " MISMATCH")


def findings(steps: Sequence[Dict[str, Any]]) -> List[str]:
    """Rows whose recheck column is a defect rather than a result.

    A REJECT is in here deliberately.  It is not a boundary of IC3 -- it says an
    independent checker refuses something the engine's own checker accepted, and
    that is the single most interesting thing this column could report.
    """
    out: List[str] = []
    for step in steps:
        column = step.get("recheck")
        if column and column.get("finding"):
            out.append("%s: %s -- %s" % (step["spec"]["label"],
                                         column.get("status"),
                                         column.get("detail")))
    return out
