"""The **problem** half of the domain/problem split.

`theory.dsl` is the domain: it travels between levels. Everything true of *this*
level and no other lives here — the board map, where the instances start, what
`portal_exit` names, which cell wins, and (ledger entry E-05) the weight vectors
a `pagoda(...)` invariant refers to.

This module reads JSON and nothing else. It deliberately does **not** import
anything from `cold-start-a0/` or `engine-rig/`: the tracks meet at data files,
not at call sites, so a problem instance produced by any pipeline compiles here
as long as it has the shape below.

```json
{
  "name": "a0-base",
  "grid": [9, 9],
  "background": 0,
  "board": [[...], ...],
  "objects": [{"name": "Cart", "type": "Cart", "pos": [4, 4], "color": 6}],
  "goal_cell": [2, 7],
  "landmarks": {"portal_exit": [1, 1]},
  "arena": [[1, 1], ...],
  "weights": {"w": [-1, 1, 0, 1, -1]},
  "goal_states": ["00010"]
}
```

`type` defaults to `name`, so a one-instance-per-type problem (which is every
problem `cold-start-a0` produces) needs no change to be read here. Several
instances of one declared type is the general case and the reason this module
exists — `gen_python`'s predecessor assumed exactly one, which is why the peg
world's rules compiled to `pass`.
"""

import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

Cell = Tuple[int, ...]


class ProblemError(Exception):
    """The problem instance is malformed, or disagrees with the manual."""


@dataclass
class Instance:
    """One concrete object. `name` is unique; `type` names a word_table entry."""
    name: str
    type: str
    pos: Cell
    color: Optional[int] = None
    present: bool = True
    extra: Dict[str, object] = field(default_factory=dict)


@dataclass
class ProblemSpec:
    name: str
    background: int = 0
    height: Optional[int] = None
    width: Optional[int] = None
    board: List[List[int]] = field(default_factory=list)
    instances: List[Instance] = field(default_factory=list)
    goal_cell: Optional[Cell] = None
    landmarks: Dict[str, Cell] = field(default_factory=dict)
    arena: List[Cell] = field(default_factory=list)
    # E-05. Weight vectors by declared name, indexed by position.
    weights: Dict[str, List[int]] = field(default_factory=dict)
    # Optional narrowing of the manual's goal to specific states. A problem may
    # target fewer states than the domain goal admits; it may never target more.
    goal_states: List[str] = field(default_factory=list)
    # Number of positions for a 1-D (line) world; `None` means a grid.
    n_pos: Optional[int] = None

    @property
    def is_line(self) -> bool:
        return self.n_pos is not None

    def instances_of(self, type_name: str) -> List[Instance]:
        return [i for i in self.instances if i.type == type_name]

    def cells(self) -> List[Cell]:
        if self.is_line:
            return [(i,) for i in range(self.n_pos)]
        return list(self.arena)


def _cell(value) -> Cell:
    if isinstance(value, int):
        return (value,)
    return tuple(int(v) for v in value)


def load_problem(path: str) -> ProblemSpec:
    with open(path, encoding="utf-8") as handle:
        return from_json(json.load(handle), default_name=path)


def from_json(doc: dict, default_name: str = "problem") -> ProblemSpec:
    grid = doc.get("grid")
    height = width = None
    if grid:
        height, width = int(grid[0]), int(grid[1])

    instances = []
    for raw in doc.get("objects", []):
        if "name" not in raw:
            raise ProblemError("every object needs a `name`: %r" % (raw,))
        known = {"name", "type", "pos", "color", "colour", "present"}
        instances.append(Instance(
            name=raw["name"],
            type=raw.get("type", raw["name"]),
            pos=_cell(raw.get("pos", 0)),
            color=raw.get("color", raw.get("colour")),
            present=bool(raw.get("present", True)),
            extra={k: v for k, v in raw.items() if k not in known},
        ))

    names = [i.name for i in instances]
    if len(set(names)) != len(names):
        raise ProblemError(
            "instance names must be unique; got %r. A rule that quantifies over "
            "a type grounds one clause per instance and needs to be able to "
            "tell them apart." % (sorted(names),))

    weights = {k: [int(x) for x in v]
               for k, v in doc.get("weights", {}).items()}

    return ProblemSpec(
        name=doc.get("name", default_name),
        background=int(doc.get("background", 0)),
        height=height,
        width=width,
        board=[list(row) for row in doc.get("board", [])],
        instances=instances,
        goal_cell=_cell(doc["goal_cell"]) if doc.get("goal_cell") else None,
        landmarks={k: _cell(v) for k, v in doc.get("landmarks", {}).items()},
        arena=[_cell(c) for c in doc.get("arena", [])],
        weights=weights,
        goal_states=list(doc.get("goal_states", [])),
        n_pos=doc.get("n_pos"),
    )


def check_against_theory(problem: ProblemSpec, ast) -> List[str]:
    """Check the manual against the level. Returns warnings; raises on errors.

    The split between the two is deliberate. A landmark the manual *declares*
    and the level does not supply is a broken compile — the rule that uses it
    has no value to use. A landmark the level supplies and the manual never
    declares compiles to exactly the same world; what it costs is legibility,
    which is the whole of ledger entry E-04: a reader of `theory.dsl` alone
    cannot tell which free names are level data. So that direction warns.

    Erroring on it instead would reject every v0.1 manual written before
    `landmark` existed — including `cold-start-a0/theory/theory.dsl`, which is
    a correct manual and stays a correct manual. E-03 is mandatory because a
    missing `semantics:` silently changes the world; E-04 is not, because a
    missing `landmark` only makes the manual harder to read.
    """
    warnings: List[str] = []
    wt = ast.word_table
    if wt is None:
        return warnings

    declared = {lm.name for lm in wt.landmarks}
    supplied = set(problem.landmarks)
    if declared - supplied:
        raise ProblemError(
            "theory.dsl declares landmark(s) %s that problem %r does not "
            "locate" % (sorted(declared - supplied), problem.name))
    if supplied - declared:
        warnings.append(
            "problem %r locates %s, which theory.dsl never declares as a "
            "landmark. Add `landmark <name>` to word_table so a reader of the "
            "manual alone can tell it is level data (E-04)."
            % (problem.name, sorted(supplied - declared)))

    for decl in wt.weights:
        if decl.name not in problem.weights:
            raise ProblemError(
                "theory.dsl declares `weights %s over %s`, but problem %r "
                "supplies no vector for it. The manual names the potential; "
                "the level supplies the numbers."
                % (decl.name, decl.over, problem.name))

    types = {o.name for o in wt.objects}
    for inst in problem.instances:
        if inst.type not in types:
            raise ProblemError(
                "problem %r has instance %r of type %r, which theory.dsl's "
                "word_table does not declare" % (problem.name, inst.name,
                                                 inst.type))
    return warnings
