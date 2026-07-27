"""Can we actually get to the state this probe wants? Ask the planner.

A0's cold start emitted **zero executable probes** (`cold-start-a0/THEORIZE_LOG.md`
P-01..P-03): every design that separated anything lived in the hypothetical
tier, because nothing checked whether the divergent configuration was reachable,
and nothing could price the walk to it.  This module is the missing half.

The bridge is short, because Theoria 1.9 already said what it is: *reaching a
divergent state is itself a planning problem*.  So a probe configuration becomes
a PDDL goal, `fd_adapter` answers, and the answer decides the tier:

  * **SAT** -- the probe is promoted to *executable* and carries its reaching
    plan.  The plan's length is charged to the probe's path cost, which is what
    makes "bits per unit cost" mean something: two probes worth one bit each are
    separated by what it costs to stand where they can be run.
  * **UNSAT** -- the verdict is *unreachable*, and that is a finding, not a
    failure.  It is R-05's shape exactly: an experiment that would settle the
    manual and cannot be performed on this instance.  A probe layer that could
    not say this would quietly propose impossible experiments forever.

The deadlock theorems plug in here too: `prune` is passed straight through to
the search, so a reachability query is answered with the same pruning the
planner gets.  One theorem, three consumers.
"""

import math
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from engines import fd_adapter
from engines.fd_adapter.pddl import Atom, Domain, Problem
from engines.probe_frontier.frontier import Hypothesis, ProbeValue, rank_probes

REACHABLE = "reachable"
UNREACHABLE = "unreachable"

EXECUTABLE = "executable"
HYPOTHETICAL = "hypothetical"


@dataclass
class Reachability:
    """The planner's answer about one configuration."""

    status: str
    problem: str
    goal_atoms: Tuple[Atom, ...]
    plan: Optional[List[str]] = None
    expansions: int = 0
    backend: str = "stub-bfs"

    @property
    def length(self) -> Optional[int]:
        return None if self.plan is None else len(self.plan)

    @property
    def reachable(self) -> bool:
        return self.status == REACHABLE

    def as_json(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "problem": self.problem,
            "goal": [" ".join(atom) for atom in self.goal_atoms],
            "plan": list(self.plan) if self.plan is not None else None,
            "length": self.length,
            "expansions": self.expansions,
            "backend": self.backend,
        }


def reachability_problem(base: Problem, goal_atoms: Sequence[Atom],
                         name: str) -> Problem:
    """The same instance, asking for the probe configuration instead of the goal.

    Objects and initial state are the base problem's, untouched -- the question
    is "can this world reach that configuration", so changing anything but the
    goal would be answering a different one.
    """
    return Problem(
        name=name,
        domain_name=base.domain_name,
        objects=list(base.objects),
        init=list(base.init),
        goal_positive=[tuple(atom) for atom in goal_atoms],
        goal_negative=[],
    )


def reach(domain: Domain, base: Problem, goal_atoms: Sequence[Atom],
          name: str, prune: Optional[Any] = None) -> Reachability:
    """Plan to the configuration; `unreachable` is an answer, not an error."""
    problem = reachability_problem(base, goal_atoms, name)
    plan, result = fd_adapter.solve_parsed(domain, problem, prune=prune)
    if plan is None:
        return Reachability(
            status=UNREACHABLE, problem=name, goal_atoms=tuple(goal_atoms),
            expansions=result.expansions,
        )
    return Reachability(
        status=REACHABLE, problem=name, goal_atoms=tuple(goal_atoms),
        plan=list(plan.actions), expansions=result.expansions, backend=plan.backend,
    )


@dataclass
class Configuration:
    """A candidate probe site: a world state, and what to try there."""

    name: str
    state: Any
    actions: Tuple[str, ...]
    goal_atoms: Tuple[Atom, ...]


@dataclass
class ExecutableProbe:
    """A probe design that knows what it costs to run -- or that it cannot be."""

    configuration: Configuration
    best: Optional[ProbeValue]
    ranked: List[ProbeValue]
    reach: Reachability
    setup_cost: float = 1.0

    @property
    def tier(self) -> str:
        if self.best is None or not self.reach.reachable:
            return HYPOTHETICAL
        return EXECUTABLE

    @property
    def cost(self) -> float:
        """Setup plus the walk. Unreachable configurations cost infinity, which
        is the honest price and sorts them where they belong."""
        if not self.reach.reachable:
            return math.inf
        return self.setup_cost + float(self.reach.length or 0)

    @property
    def entropy(self) -> float:
        return self.best.entropy if self.best is not None else 0.0

    @property
    def value(self) -> float:
        if self.cost == math.inf or self.cost <= 0:
            return 0.0
        return self.entropy / self.cost

    def as_json(self) -> Dict[str, Any]:
        return {
            "configuration": self.configuration.name,
            "tier": self.tier,
            "action": self.best.action if self.best else None,
            "entropy_bits": round(self.entropy, 12),
            "setup_cost": self.setup_cost,
            "path_cost": None if self.cost == math.inf else self.cost,
            "value_bits_per_cost": round(self.value, 12),
            "reach": self.reach.as_json(),
            "verdict": self.reach.status,
        }


def design(hypotheses: Sequence[Hypothesis],
           configurations: Sequence[Configuration],
           domain: Domain, base: Problem,
           prune: Optional[Any] = None,
           setup_cost: float = 1.0) -> List[ExecutableProbe]:
    """Rank probe sites by bits per unit of *real* path cost.

    Ordering is total and deterministic, exactly as in `rank_probes`: most bits
    per unit cost, then most bits, then cheapest, then the configuration's name.
    Unreachable sites fall to the bottom on value 0 and stay in the list, because
    "this cannot be run" is the output the caller needs, not one to drop.
    """
    out: List[ExecutableProbe] = []
    for configuration in configurations:
        ranked = rank_probes(hypotheses, configuration.state, configuration.actions)
        best = ranked[0] if ranked and ranked[0].splits else None
        verdict = reach(
            domain, base, configuration.goal_atoms,
            name="reach-%s" % configuration.name, prune=prune,
        )
        out.append(
            ExecutableProbe(
                configuration=configuration, best=best, ranked=ranked,
                reach=verdict, setup_cost=setup_cost,
            )
        )
    out.sort(
        key=lambda p: (-p.value, -p.entropy, p.cost, p.configuration.name)
    )
    return out
