"""The two hand-written books, their snapshots, and the four generated forms.

`Theoria.md` 1.10(a): two hand-written artefacts (`theory.dsl`, `playbook.dsl`)
and a set of generated ones (Lean, Python, PDDL, Markdown). Constraint 4 says
the LLM writes only the two books and generated files are never hand-edited;
constraint 1 says the four forms are co-derived from one source so the prover,
the executor, the planner and the human read the same book.

Two things this module is careful about.

**The problem instance is not a third book.** `theory.dsl` is the *domain* --
what travels between levels -- and the level's layout is the *problem*. The
problem instance here is **computed from the frames**, never written by the
desk: the board is the cells that have never varied, the instances are the
declared objects located in the current frame. So the domain/problem split
that `Theoria.md` 1.10(a) draws by hand is drawn here by arithmetic, and C3's
"transfer" has a mechanical meaning -- the same `theory.dsl` against a
different computed problem.

**Every snapshot is kept.** A revision is written to `snapshots/` before and
after every theorize, because the concept-birth timeline that P-8 asks for is
made of exactly those diffs and cannot be reconstructed afterwards.
"""

import hashlib
import json
import os
import shutil
from typing import Any, Dict, List, Optional, Tuple

import _bootstrap                                     # noqa: F401  (sys.path)

#: Above this many reachable states the enumerative Lean route is not
#: attempted. `gen_lean`'s non-pagoda development executes the generated
#: predictor over the whole state space and writes a decision procedure the
#: kernel must chew through; on a 64x64 board with two objects that space is
#: ~1.6e7 before colours. Refusing with a reason is the honest output; hanging
#: the run is not.
LEAN_STATE_CEILING = 200_000

#: How many instances one `arc-instances: all` declaration may produce.
#:
#: Each instance becomes two fields on the generated `State` dataclass and
#: multiplies every `forall`-grounded rule, so `step` cost is linear in this and
#: BFS cost is worse. The bound that matters is the dynamic set -- objects only
#: ever cover cells the board cannot explain -- and on a 64x64 ARC frame that
#: has been observed for a few dozen commands the dynamic set is in the dozens
#: to low hundreds. This cap exists so a declaration naming the background
#: colour cannot produce four thousand instances; when it bites, the level file
#: says so in `instance_caps_hit` rather than silently truncating.
MAX_INSTANCES_PER_DECL = 150


class CompileResult(dict):
    pass


class Books:
    """The pair of books for one run, with their snapshots and their forms."""

    def __init__(self, root: str, seed_from: Optional[str] = None):
        self.root = root
        self.theory_path = os.path.join(root, "theory.dsl")
        self.playbook_path = os.path.join(root, "playbook.dsl")
        self.problem_path = os.path.join(root, "problem.json")
        self.generated = os.path.join(root, "generated")
        self.snapshots = os.path.join(root, "snapshots")
        for path in (root, self.generated, self.snapshots):
            os.makedirs(path, exist_ok=True)
        self.revision = 0
        self.carried: Optional[Dict[str, Any]] = None
        if seed_from:
            self.carried = self._carry_in(seed_from)

    # -- carrying the pair in from a previous run --------------------------
    def _carry_in(self, seed_from: str) -> Dict[str, Any]:
        """Seed this run's pair from an earlier run's, and prove it by hash.

        Exactly two files travel. `problem.json` deliberately does not: it is
        *computed* from the frames of the level being played (see the module
        docstring), so carrying it would be carrying an answer to a question
        this level has not asked. Nor do `generated/` or `snapshots/` -- the
        four forms are re-derived from the domain, which is the whole point of
        co-derivation, and a snapshot history belongs to the run that made it.

        The reference implementation is `cold-start-a3/a3pipeline/transfer.py`,
        whose test asserts byte-identity by sha256 rather than by inspection.
        Same discipline here: the hashes go in `CARRIED.json` next to the
        books, so "the manual that played level 2 is the manual level 1 wrote"
        is a checkable claim about the artefacts and not a sentence in a
        report.

        A missing or empty source is not an error -- the first level of the
        first game has nothing to carry. It is recorded as such, because
        "carried nothing" and "carried something" produce very different bills
        and the figure needs to tell them apart.
        """
        record: Dict[str, Any] = {"seed_from": seed_from, "carried": {},
                                  "skipped": []}
        for name, dst in (("theory.dsl", self.theory_path),
                          ("playbook.dsl", self.playbook_path)):
            src = os.path.join(seed_from, name)
            if not os.path.exists(src):
                record["skipped"].append({"file": name, "why": "not present"})
                continue
            text = _read(src)
            if not text.strip():
                record["skipped"].append({"file": name, "why": "empty"})
                continue
            _write(dst, text)
            # The digest is taken over the bytes that are now on disk, not over
            # the string in hand. `_write` normalises -- it appends a trailing
            # newline and writes LF -- so hashing `text` would record a value
            # that describes neither the source file nor the file it sits next
            # to, and "the manual that played level 2 is the manual level 1
            # wrote" would stop being a checkable claim about the artefacts.
            with open(dst, "rb") as fh:
                digest = hashlib.sha256(fh.read()).hexdigest()
            record["carried"][name] = {"sha256": digest, "chars": len(text)}
        record["empty"] = not record["carried"]
        with open(os.path.join(self.root, "CARRIED.json"), "w",
                  encoding="utf-8", newline="\n") as fh:
            json.dump(record, fh, indent=1, sort_keys=True)
            fh.write("\n")
        return record

    # -- the hand-written pair ---------------------------------------------
    @property
    def theory(self) -> str:
        return _read(self.theory_path)

    @property
    def playbook(self) -> str:
        return _read(self.playbook_path)

    def write(self, theory: Optional[str] = None,
              playbook: Optional[str] = None) -> None:
        if theory is not None:
            _write(self.theory_path, theory)
        if playbook is not None:
            _write(self.playbook_path, playbook)

    def snapshot(self, tag: str) -> Dict[str, Any]:
        """Both books, verbatim, under a tag. The timeline is these files."""
        self.revision += 1
        stamp = "rev%02d-%s" % (self.revision, tag)
        out = os.path.join(self.snapshots, stamp)
        os.makedirs(out, exist_ok=True)
        written = []
        for src in (self.theory_path, self.playbook_path, self.problem_path):
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(out, os.path.basename(src)))
                written.append(os.path.basename(src))
        return {"revision": self.revision, "tag": tag, "dir": out,
                "files": written}

    # -- the problem instance, computed ------------------------------------
    def write_problem(self, problem: Dict[str, Any]) -> str:
        with open(self.problem_path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(problem, fh, indent=1, sort_keys=True)
            fh.write("\n")
        return self.problem_path

    # -- the four forms ----------------------------------------------------
    def compile_all(self) -> CompileResult:
        """Parse, then generate every form that this manual can support.

        A refusal is a result. `gen_python` raises `UnsupportedClause` rather
        than approximating, and that refusal names exactly which clause the
        executable form cannot carry -- which is the expressivity ledger
        writing itself.
        """
        from theory_compiler.parser.theory_parser import parse_theory   # noqa: PLC0415
        from theory_compiler.problem import load_problem                # noqa: PLC0415

        result = CompileResult(ok=False, forms={}, errors={}, warnings=[])
        text = self.theory
        if not text.strip():
            result["errors"]["parse"] = "theory.dsl is empty"
            return result

        try:
            ast = parse_theory(text)
        except Exception as exc:                       # noqa: BLE001
            result["errors"]["parse"] = "%s: %s" % (type(exc).__name__, exc)
            return result
        result["parsed"] = True

        problem = None
        if os.path.exists(self.problem_path):
            try:
                problem = load_problem(self.problem_path)
            except Exception as exc:                   # noqa: BLE001
                result["errors"]["problem"] = "%s: %s" % (type(exc).__name__, exc)

        result["forms"]["markdown"] = self._gen_markdown(ast, result)
        if problem is not None:
            result["forms"]["python"] = self._gen_python(ast, problem, result)
        result["forms"]["pddl"] = self._gen_pddl(ast, result)
        result["forms"]["lean"] = self._gen_lean(ast, problem, result)

        result["ok"] = bool(result["forms"].get("python"))
        result["_ast"] = ast
        result["_problem"] = problem
        return result

    def _out(self, name: str, text: str) -> str:
        path = os.path.join(self.generated, name)
        _write(path, text)
        return path

    def _gen_markdown(self, ast, result) -> Optional[str]:
        from theory_compiler.generators.gen_markdown import generate_markdown  # noqa: PLC0415
        try:
            return self._out("theory.md", generate_markdown(ast))
        except Exception as exc:                       # noqa: BLE001
            result["errors"]["markdown"] = "%s: %s" % (type(exc).__name__, exc)
            return None

    def _gen_python(self, ast, problem, result) -> Optional[str]:
        from theory_compiler.generators.gen_python import generate_python      # noqa: PLC0415
        try:
            return self._out("theory.py", generate_python(ast, problem))
        except Exception as exc:                       # noqa: BLE001
            result["errors"]["python"] = "%s: %s" % (type(exc).__name__, exc)
            return None

    def _gen_pddl(self, ast, result) -> Optional[List[str]]:
        from theory_compiler.generators.gen_pddl import generate_pddl          # noqa: PLC0415
        try:
            domain, problem_text = generate_pddl(ast)
            return [self._out("domain.pddl", domain),
                    self._out("problem.pddl", problem_text)]
        except Exception as exc:                       # noqa: BLE001
            result["errors"]["pddl"] = "%s: %s" % (type(exc).__name__, exc)
            return None

    def _gen_lean(self, ast, problem, result) -> Optional[str]:
        """Attempted only when the state space is small enough to be decided.

        The non-pagoda development enumerates; the pagoda development needs a
        LINE world and an `lp_potential` certificate, and this world is neither.
        Both refusals are recorded with the number that caused them."""
        if problem is None:
            result["errors"]["lean"] = "no problem instance"
            return None
        estimate = _state_space_estimate(problem)
        result["lean_state_estimate"] = estimate
        if estimate is None or estimate > LEAN_STATE_CEILING:
            result["errors"]["lean"] = (
                "not attempted: the enumerative development decides every state "
                "in the kernel and this level has about %s of them (ceiling %d). "
                "The pagoda development is the alternative and needs a LINE "
                "world plus an lp_potential certificate; this is a grid world "
                "with no state graph."
                % ("an unknown number" if estimate is None else "%.3g" % estimate,
                   LEAN_STATE_CEILING))
            return None
        from theory_compiler.generators.gen_lean import generate_lean          # noqa: PLC0415
        try:
            return self._out("theory.lean", generate_lean(ast, problem))
        except Exception as exc:                       # noqa: BLE001
            result["errors"]["lean"] = "%s: %s" % (type(exc).__name__, exc)
            return None

    # -- the executable form ------------------------------------------------
    def load_predictor(self) -> Tuple[Optional[Any], Optional[str]]:
        """`exec` the generated Python and hand back its module namespace.

        This is the system's only predictor (`Theoria.md` 1.10(a): prediction
        has no side door). It is loaded from the generated file rather than
        imported, so there is no chance of a stale module object surviving a
        recompile.
        """
        path = os.path.join(self.generated, "theory.py")
        if not os.path.exists(path):
            return None, "theory.py has not been generated"
        namespace: Dict[str, Any] = {"__name__": "theoria_generated_theory"}
        try:
            with open(path, encoding="utf-8") as fh:
                exec(compile(fh.read(), path, "exec"), namespace)   # noqa: S102
        except Exception as exc:                       # noqa: BLE001
            return None, "%s: %s" % (type(exc).__name__, exc)
        return namespace, None


def _state_space_estimate(problem) -> Optional[float]:
    """How many states the enumerative Lean route would have to decide."""
    try:
        cells = len(problem.cells()) if hasattr(problem, "cells") else 0
        movers = max(1, len(problem.instances))
        if not cells:
            return None
        return float(cells) ** movers
    except Exception:                                  # noqa: BLE001
        return None


def _read(path: str) -> str:
    if not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _write(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    if not text.endswith("\n"):
        text += "\n"
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def problem_from_frames(store, objects: List[Dict[str, Any]], *,
                        landmarks: Optional[Dict[str, Any]] = None,
                        name: str = "level-1") -> Dict[str, Any]:
    """The level instance, computed from what has been observed.

    `objects` is the desk's own declaration -- `[{"name","type","color"}]` --
    and the *only* thing here that came from a model. Where each one currently
    sits is read off the frame, not asked for.
    """
    # Objects are located in the FIRST observed frame, not the current one.
    # The problem instance is the level's *initial* state: `initial_state()` is
    # where certify starts its replay and where plan starts its search, and both
    # then roll forward through the recorded actions. Locating objects in the
    # latest frame would make the manual's t=0 disagree with the world's t=0 on
    # the very first comparison.
    grids = store.grids
    if not grids:
        raise ValueError("no frame observed yet")
    grid = grids[0]
    height, width = len(grid), len(grid[0])
    background = store.background()

    # The board is what has never varied. A cell that has changed cannot be
    # board (constraint 2), so it is written as background and an object must
    # account for it -- or certify's responsibility pass will say so.
    board = [row[:] for row in grid]
    dynamic = set(store.dynamic_cells())
    for r, c in dynamic:
        board[r][c] = background

    instances = []
    unlocated = []
    spread: Dict[str, int] = {}
    capped: List[str] = []
    for decl in objects:
        colour = decl.get("color")

        # E-08: one declaration may cover many cells.
        #
        # `gen_python`'s `render` paints exactly one cell per instance
        # (`grid[r][c] = colour`), so an object with extent -- a 24-cell ring, a
        # 3x3 token -- cannot be one instance however it is declared. That limit
        # is theory-compiler's and is not ours to change. What *was* ours, and
        # was wrong, is that a declaration produced exactly one instance at the
        # first matching cell, which left every other cell of the object with no
        # owner and the responsibility check reporting them forever.
        #
        # `arc-instances: all` uses the compiler's own machinery instead of
        # fighting it: one instance per cell, all of the same declared TYPE, so
        # `forall ?x in <Type>` grounds a rule over the whole object. The cells
        # chosen are the DYNAMIC ones showing that colour -- the board already
        # explains the constant cells, and constraint 2 asks objects to account
        # for exactly what the board cannot.
        if decl.get("instances") == "all" and colour is not None:
            cells = sorted(cell for cell in dynamic
                           if grid[cell[0]][cell[1]] == colour)
            if len(cells) > MAX_INSTANCES_PER_DECL:
                capped.append("%s: %d cells of colour %s, capped at %d"
                              % (decl["name"], len(cells), colour,
                                 MAX_INSTANCES_PER_DECL))
                cells = cells[:MAX_INSTANCES_PER_DECL]
            if not cells:
                unlocated.append(decl["name"])
            spread[decl["name"]] = len(cells)
            for r, c in cells:
                instances.append({
                    "name": "%s_r%dc%d" % (decl["name"], r, c),
                    "type": decl.get("type", decl["name"]),
                    "pos": [r, c], "present": True, "color": colour})
            continue

        pos = _find_colour(grid, colour) if colour is not None else None
        if pos is None:
            # A declared object the frame cannot locate is a defect in the
            # manual, not a reason to crash. It enters the level at the origin
            # and marked absent, and certify's responsibility pass then reports
            # every pixel it should have explained -- which is the diagnosis
            # the desk needs, delivered by the check that exists for it.
            unlocated.append(decl["name"])
        instance = {"name": decl["name"], "type": decl.get("type", decl["name"]),
                    "pos": list(pos) if pos else [0, 0],
                    "present": pos is not None}
        if colour is not None:
            instance["color"] = colour
        instances.append(instance)

    problem = {"name": name, "grid": [height, width], "background": background,
               "board": board, "objects": instances}
    if spread:
        problem["instances_per_declaration"] = spread
    if capped:
        problem["instance_caps_hit"] = capped
    # What the manual's objects will and will not be able to draw, computed
    # here so the number is in the level file rather than only in certify's
    # report -- and computed the way certify computes it, or it would be a
    # number that disagrees with the check it predicts.
    #
    # A dynamic cell needs an owner only if it is NOT showing the background
    # colour at t0: the board writes background into every dynamic cell, so a
    # dynamic cell that happens to be background at t0 already renders
    # correctly. Counting those as unexplained (the first version of this did)
    # over-reports by exactly the number of cells an object has yet to move
    # into.
    owned = {(i["pos"][0], i["pos"][1]) for i in instances if i.get("present")}
    needs_owner = {cell for cell in dynamic
                   if grid[cell[0]][cell[1]] != background}
    problem["responsibility"] = {
        "dynamic_cells": len(dynamic),
        "need_an_owner_at_t0": len(needs_owner),
        "covered_by_objects": len(owned & needs_owner),
        "will_be_unexplained_at_t0": sorted(
            [list(c) for c in (needs_owner - owned)])[:32],
        "n_unexplained_at_t0": len(needs_owner - owned),
    }
    # A landmark the manual declares but the level does not locate is a HARD
    # error in `check_against_theory` -- the rule that names it has no value to
    # use -- so a manual that reaches for a named cell cannot compile unless the
    # level supplies coordinates. The desk gives them on the declaration line
    # (`# arc-cell: (r, c)`); anything it forgets is defaulted to the origin and
    # listed, so the failure is a visible placement rather than a compile that
    # dies with a message about a level file the desk never sees.
    if landmarks:
        placed, defaulted = {}, []
        for lm_name, cell in landmarks.items():
            if cell is None:
                placed[lm_name] = [0, 0]
                defaulted.append(lm_name)
            else:
                placed[lm_name] = list(cell)
        problem["landmarks"] = placed
        if defaulted:
            problem["landmarks_defaulted"] = defaulted
    if unlocated:
        problem["unlocated"] = unlocated
    return problem


def _find_colour(grid, colour: int) -> Optional[Tuple[int, int]]:
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v == colour:
                return (r, c)
    return None
