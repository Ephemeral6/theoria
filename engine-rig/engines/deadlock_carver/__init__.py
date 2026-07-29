"""deadlock_carver -- public entry points.

One theorem, two consumers: the candidate stream (where the LLM may adjudicate it
into the playbook as a `prune` clause) and the planner (where it is a pruner and
pays for itself in nodes).  Theoria 1.9's claim is that these are the same
object; this engine is that claim made executable, so it produces both from one
`carve()` and reports the node account rather than asserting a speed-up.

    from engines import deadlock_carver as dc
    task = dc.Task.build(domain, problem)
    theorems = dc.carve(task)
    report = dc.pruning_report(domain, problem, theorems)

Candidate provenance: the frozen contract's `engine` enum has six values and
predates this engine, so its proposals go out as `fd_adapter` -- the enum member
whose work they are part of -- and name themselves in `payload.producer`.  See
DECISIONS.md D-018.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence

from common.candidates import emit, make_candidate
from engines.deadlock_carver.carve import (  # noqa: F401
    MAX_PATTERN,
    Blocked,
    State,
    Task,
    Theorem,
    atom_text,
    breaks,
    carve,
    excludes_goal,
    pattern_text,
    prove,
    pruner,
    why_blocked,
)
from engines.deadlock_carver.mutex import Mutexes, reachable_pairs  # noqa: F401
from engines.fd_adapter import search as fd_search
from engines.fd_adapter.pddl import Domain, Problem

ENGINE = "fd_adapter"                  # the frozen enum; see D-018
PRODUCER = "deadlock_carver"


class UnfinishedComparison(RuntimeError):
    """Two searches were compared and at least one of them had not finished.

    Raised rather than folded into `same_answer`'s boolean, so that a search
    which stopped can never be reported as evidence about a theorem.
    """


@dataclass
class PruningReport:
    """The same instance solved twice: once blind, once with the theorems."""

    problem: str
    n_theorems: int
    baseline: fd_search.SearchResult
    pruned: fd_search.SearchResult

    @property
    def saved(self) -> int:
        return self.baseline.expansions - self.pruned.expansions

    @property
    def ratio(self) -> float:
        if not self.baseline.expansions:
            return 1.0
        return self.pruned.expansions / self.baseline.expansions

    @property
    def same_answer(self) -> bool:
        """Pruning must change the node count and nothing else.

        The comparison is only meaningful when **both** searches finished.  On
        two unfinished searches `solved == solved` and `length(None) ==
        length(None)` are both True, so the plain conjunction reports agreement
        between two runs that answered nothing -- the same shape C11 corrected in
        `tools/p13_fd_dividend.same_answer`, and this property feeds the same
        kind of gate (`bench/dividend.py` reads `plan_length_unchanged` as
        "pruning did not change the bundled rung's answer -- unsound theorem").

        Today `search()` raises on its expansion budget rather than returning,
        so a returned `SearchResult` is always exhaustive and this guard never
        fires.  It is here anyway, because *that* is the argument C11 refused to
        accept for `p13_fd_dividend` -- "an upstream mechanism makes it safe" is
        a property of code twenty files away, and it is exactly what stops
        holding when someone adds a budget that returns instead of raising.  The
        entitlement is now checked where the claim is made.

        It raises rather than returning a third value: `False` here means
        "pruning changed the answer -- unsound theorem", so returning it for an
        unfinished search would file a soundness violation against a theorem on
        the strength of a search that stopped -- this work item's defect wearing
        the other sign.
        """
        if not (self.baseline.exhaustive and self.pruned.exhaustive):
            raise UnfinishedComparison(
                "%s: a search that did not finish cannot be compared -- "
                "baseline exhaustive=%r, pruned exhaustive=%r"
                % (self.problem, self.baseline.exhaustive, self.pruned.exhaustive)
            )
        return (
            self.baseline.solved == self.pruned.solved
            and self.baseline.length == self.pruned.length
        )

    def as_json(self) -> Dict[str, Any]:
        return {
            "problem": self.problem,
            "n_theorems": self.n_theorems,
            "baseline": self.baseline.as_json(),
            "pruned": self.pruned.as_json(),
            "expansions_before": self.baseline.expansions,
            "expansions_after": self.pruned.expansions,
            "expansions_saved": self.saved,
            "expansions_ratio": round(self.ratio, 6),
            "states_pruned": self.pruned.pruned,
            "plan_length": self.pruned.length,
            "plan_length_unchanged": self.same_answer,
            "rendering": (
                "%d deadlock theorem(s) cut %s from %d expansions to %d (%.1f%% fewer), "
                "plan length %s either way"
            ) % (
                self.n_theorems, self.problem,
                self.baseline.expansions, self.pruned.expansions,
                100.0 * (1.0 - self.ratio), self.pruned.length,
            ),
        }


def pruning_report(domain: Domain, problem: Problem, theorems: Sequence[Theorem],
                   max_expansions: int = 500000) -> PruningReport:
    """Solve twice and compare. The claim being tested is that nothing but the
    node count moves -- an unsound theorem shows up here as a changed answer."""
    baseline = fd_search.search(domain, problem, max_expansions=max_expansions)
    pruned = fd_search.search(
        domain, problem, prune=pruner(theorems), max_expansions=max_expansions
    )
    return PruningReport(
        problem=problem.name,
        n_theorems=len(theorems),
        baseline=baseline,
        pruned=pruned,
    )


def to_payload(theorem: Theorem, task: Task) -> Dict[str, Any]:
    """The `invariant` payload shape for a deadlock theorem; frozen in the README."""
    payload = theorem.as_json()
    payload["producer"] = PRODUCER
    payload["problem"] = task.problem.name
    payload["domain"] = task.domain.name
    payload["mutexes"] = task.mutexes.stats()
    return payload


def candidates(theorems: Sequence[Theorem], task: Task,
               report: Optional[PruningReport] = None,
               timestamp: Optional[str] = None) -> List[Dict[str, Any]]:
    """One `invariant` per theorem, plus one `plan` carrying the node account."""
    n_actions = len(task.actions)
    rows = []
    for theorem in theorems:
        deleting = [
            index
            for index, action in enumerate(task.actions)
            if breaks(action, theorem.pattern)
        ]
        rows.append(
            make_candidate(
                engine=ENGINE,
                kind="invariant",
                payload=to_payload(theorem, task),
                # Every ground action was examined and none of them escapes the
                # pattern; `transitions` names the ones that had to be discharged.
                transitions=deleting,
                coverage="%d/%d" % (n_actions, n_actions),
                timestamp=timestamp,
            )
        )
    if report is not None:
        payload = report.as_json()
        payload["producer"] = PRODUCER
        payload["form"] = "pruning_account"
        rows.append(
            make_candidate(
                engine=ENGINE,
                kind="plan",
                payload=payload,
                transitions=list(range(report.pruned.length or 0)),
                # Nodes the pruned search still had to expand, out of the nodes
                # the blind search generated -- the account, in the contract's
                # own "<k>/<n>" field rather than only in the payload.
                coverage="%d/%d" % (report.pruned.expansions, report.baseline.generated),
                timestamp=timestamp,
            )
        )
    return rows


def run(domain: Domain, problem: Problem, out_path: Optional[str] = None,
        max_pattern: int = MAX_PATTERN, with_report: bool = True,
        timestamp: Optional[str] = None):
    """Carve the theorems, measure what they buy, emit both.

    Returns (task, theorems, report). `report` is None when `with_report` is off.
    """
    task = Task.build(domain, problem)
    theorems = carve(task, max_pattern=max_pattern)
    report = pruning_report(domain, problem, theorems) if with_report else None
    if out_path:
        emit(out_path, candidates(theorems, task, report=report, timestamp=timestamp))
    return task, theorems, report
