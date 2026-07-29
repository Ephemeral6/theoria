"""What connecting a real planner buys, measured rather than asserted.

Two experiments, both of which need Fast Downward and neither of which the stub
could run:

**A -- the deadlock dividend, re-run on FD.**  M9 measured `deadlock_carver`'s
theorems as a Python pruner inside the bundled BFS (808 -> 571 expansions on
`open4far`, 44 -> 22 on `ringstuck`, 0 on `open4`).  That measurement is only
about the stub.  Here the same theorems are *compiled into PDDL* and handed to
Fast Downward, so the node account is taken by a planner that knows nothing
about this rig.  If the dividend is real it survives the change of engine; if it
was an artefact of the stub's node ordering, this is where that shows.

The compilation is a static-predicate guard rather than a search callback, since
FD reads files and cannot be handed a pruner:

    push ... :precondition (and <original>
                                (safe1 ?b ?to)
                                (forall (?o - box ?c2 - cell)
                                  (or (not (at ?o ?c2)) (safe2 ?b ?to ?o ?c2))))

`safe1` and `safe2` are static and enumerated in `:init`: every box/cell pair and
every ordered pair-of-boxes placement that no theorem condemns.  `push` is the
only action that moves a box, so guarding it is enough to make every dead state
unreachable.  Soundness rests on the theorems' own second obligation -- no state
containing a pattern is a goal state (`excludes_goal`) -- which is what makes
"forbid the pattern outright" not throw away any solution.

**B -- stub versus FD on the cold-start domains.**  A0's and A2's generated
`domain.pddl` were only ever solved by the bundled BFS.  Here each is solved by
both and the answers are compared.  Disagreement on an optimal configuration is
a defect in one of the two, and we would want to know which.

    python -m tools.p13_fd_dividend            # needs $FAST_DOWNWARD

Deterministic: no timestamps in the artefact, instances in a fixed order.  This
tool is *not* part of `run_all`; the committed candidate stream must not depend
on whether this machine has a planner installed (D-A0-021's discipline, adopted).
"""

import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engines import deadlock_carver as dc
from engines.fd_adapter import backends, search as fd_search
from engines.fd_adapter.pddl import Atom, parse_domain, parse_problem
from fixtures import sokoban

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(HERE)
OUT_DIR = os.path.join(HERE, "runs", "p13-fd-real")

# `astar(blind())` and BFS are the same search in different clothes -- both
# length-optimal, both uninformed -- which is the only pairing under which a
# node count taken from one says anything about the other.
BLIND = "astar(blind())"

EXPANDED = re.compile(r"Expanded (\d+) state\(s\)\.")
PLAN_LENGTH = re.compile(r"Plan length: (\d+) step\(s\)\.")


# ------------------------------------------------------------------ FD calling

@dataclass
class FdRun:
    """One Fast Downward invocation, reduced to what an experiment reads.

    `unsolvable` means **proved unsolvable**, adjudicated by
    `backends.proves_unsolvable`; it is never `True` because the process merely
    stopped.  `answered` is the separate bit every consumer here has to read
    first: a run that neither produced a plan nor proved unsolvability said
    nothing about the instance, and `False`/`None` in the other fields is the
    absence of an answer, not a negative one.
    """

    config: str
    rung: str
    exit_code: int
    expansions: Optional[int]
    plan_length: Optional[int]
    plan: Optional[List[str]]
    unsolvable: bool
    exhausted_reported: bool

    @property
    def answered(self) -> bool:
        """Did this run settle the instance either way?"""
        return self.plan is not None or self.unsolvable

    def as_json(self) -> Dict[str, object]:
        return {
            "config": self.config,
            "rung": self.rung,
            "exit_code": self.exit_code,
            "expansions": self.expansions,
            "plan_length": self.plan_length,
            "unsolvable": self.unsolvable,
            "answered": self.answered,
            # The evidence the unsolvability verdict rests on, recorded so a
            # reader of the artefact can re-apply `proves_unsolvable` without
            # the log.  The published p13 artefact predates this field, which is
            # why its three exit-12 rows could only be reconciled indirectly.
            "exhausted_reported": self.exhausted_reported,
        }


def run_fd(executable: str, domain_path: str, problem_path: str,
           search_config: str = BLIND, alias: Optional[str] = None,
           timeout: int = 600, rung: Optional[str] = None) -> FdRun:
    """Call FD and read back the node account as well as the plan.

    `backends.run_fast_downward` deliberately returns only the plan -- callers of
    `solve()` have no business reading a planner's log.  An experiment about node
    counts is exactly the caller that does, so it invokes FD itself rather than
    widening the adapter's contract for one measurement.

    Reading the log is where that licence stops.  Whether the run *proved* the
    instance unsolvable is decided by `backends.proves_unsolvable`, not by this
    module: exit 12 is FD's code for both "I explored everything and there is
    nothing" and "I gave up", and only the rung plus FD's own
    "Completely explored state space" separates them (`backends.py`'s constants
    block, measured against the installed build).  `rung` defaults to the
    conservative reading -- anything this function cannot vouch for as a
    complete, unbounded search is treated as the satisficing rung, on which
    `proves_unsolvable` refuses exit 12 outright.
    """
    if rung is None:
        rung = (backends.FD_OPTIMAL if alias is None and search_config == BLIND
                else backends.FD_SATISFICING)
    with tempfile.TemporaryDirectory() as workdir:
        plan_path = os.path.join(workdir, "sas_plan")
        command = [executable, "--plan-file", plan_path]
        if alias:
            command += ["--alias", alias, domain_path, problem_path]
        else:
            command += [domain_path, problem_path, "--search", search_config]
        if executable.endswith(".py"):
            command = [sys.executable] + command
        # `encoding=` is pinned: `text=True` alone decodes with the locale
        # codec, and on a cp936 machine a UnicodeDecodeError is raised inside
        # subprocess's reader thread -- neither an OSError nor a
        # SubprocessError, so it escapes as a bare crash and destroys the log
        # this function then has to adjudicate.
        done = subprocess.run(command, cwd=workdir, capture_output=True,
                              text=True, encoding="utf-8", errors="replace",
                              timeout=timeout)
        log = done.stdout + done.stderr
        expanded = EXPANDED.findall(log)
        length = PLAN_LENGTH.findall(log)
        plan = None
        if os.path.exists(plan_path):
            with open(plan_path, "r", encoding="utf-8") as fh:
                plan = backends.parse_sas_plan(fh.read())
        return FdRun(
            config=alias or search_config,
            rung=rung,
            exit_code=done.returncode,
            # A portfolio prints one account per iteration; the last is the one
            # that answered.  Blind search prints exactly one.
            expansions=int(expanded[-1]) if expanded else None,
            plan_length=int(length[-1]) if length else (len(plan) if plan else None),
            plan=plan,
            unsolvable=backends.proves_unsolvable(rung, done.returncode, log),
            exhausted_reported=backends.FD_EXHAUSTED in log,
        )


def same_answer(before: FdRun, after: FdRun) -> Optional[bool]:
    """Did the guard leave this instance's answer alone?  `None` = nobody knows.

    This is the gate on "the deadlock theorems did not change the instance", so
    it is a named function rather than an expression inline in the row: the
    guard that makes it three-valued has to be somewhere a test can reach
    without a planner installed.  Two failed runs have `plan_length is None` and
    `unsolvable is False` on both sides, so the plain conjunction is True and a
    row that measured nothing publishes itself as a passing control.
    """
    if not (before.answered and after.answered):
        return None
    return (before.plan_length == after.plan_length
            and before.unsolvable == after.unsolvable)


def backends_agree(stub_unsolvable: bool, stub_length: Optional[int],
                   fd: FdRun) -> Optional[bool]:
    """Do the stub and Fast Downward give the same answer?  `None` = FD gave none.

    `fd.unsolvable` is False both when FD found a plan and when FD fell over, so
    comparing it to the stub's verdict without this guard files a cross-backend
    disagreement against a backend that never spoke.
    """
    if not fd.answered:
        return None
    return (stub_unsolvable == fd.unsolvable
            and (stub_unsolvable or stub_length == fd.plan_length))


# --------------------------------------------------- compiling theorems away

def _atom_is_box_position(atom: Atom) -> bool:
    return len(atom) == 3 and atom[0] == "at"


@dataclass
class Encoding:
    """A guarded copy of an instance, plus what it could not express."""

    domain_text: str
    problem_text: str
    n_unary: int
    n_pairs: int
    skipped: List[str] = field(default_factory=list)

    @property
    def encoded(self) -> int:
        return self.n_unary + self.n_pairs


def encode(domain_text: str, problem_text: str,
           theorems: Sequence[dc.Theorem]) -> Encoding:
    """Compile deadlock theorems into static guards on `push`.

    Only patterns made of box positions are expressible this way.  Anything else
    is *reported*, not silently dropped: a dividend measured against a subset of
    the theorems is a smaller dividend, and calling it the whole one would be the
    same sin as calling the stub Fast Downward.
    """
    dead_unary: List[Tuple[str, str]] = []
    dead_pairs: List[Tuple[str, str, str, str]] = []
    skipped: List[str] = []

    for theorem in theorems:
        if not all(_atom_is_box_position(a) for a in theorem.pattern):
            skipped.append(theorem.rendering())
            continue
        if theorem.size == 1:
            (_, box, cell), = theorem.pattern
            dead_unary.append((box, cell))
        elif theorem.size == 2:
            (_, b1, c1), (_, b2, c2) = theorem.pattern
            if b1 == b2:                      # one box in two places: unreachable
                skipped.append(theorem.rendering())
                continue
            dead_pairs.append((b1, c1, b2, c2))
            dead_pairs.append((b2, c2, b1, c1))
        else:
            skipped.append(theorem.rendering())

    problem = parse_problem(problem_text)
    boxes = [name for name, kind in problem.objects if kind == "box"]
    cells = [name for name, kind in problem.objects if kind == "cell"]

    safe1 = ["    (safe1 %s %s)" % (b, c)
             for b in sorted(boxes) for c in sorted(cells)
             if (b, c) not in dead_unary]
    # `safe2 b c o d` reads "b at c and o at d is not a condemned pair".  It must
    # be enumerated for `o == b` too, and true there: the guard's `forall` ranges
    # over every box that holds a position in the successor, and the pushed box
    # still holds its *old* one in the state the precondition is evaluated in.
    # Leaving those out does not weaken the guard, it blocks every push -- which
    # is exactly what the first run of this experiment did.
    condemned = set(dead_pairs)
    safe2 = ["    (safe2 %s %s %s %s)" % (b, c, o, d)
             for b in sorted(boxes) for c in sorted(cells)
             for o in sorted(boxes) for d in sorted(cells)
             if (b, c, o, d) not in condemned]

    domain_out = _guard_domain(domain_text)
    problem_out = _add_init(problem_text, safe1 + safe2)
    assert _balanced(domain_out), "guarded domain does not close its parentheses"
    assert _balanced(problem_out), "guarded problem does not close its parentheses"
    return Encoding(domain_out, problem_out, len(dead_unary),
                    len(dead_pairs) // 2, skipped)


GUARD = ("(safe1 ?b ?to)\n"
         "                       (forall (?o - box ?c2 - cell)\n"
         "                         (or (not (at ?o ?c2)) (safe2 ?b ?to ?o ?c2)))")


def _balanced(text: str) -> bool:
    """Parentheses close.  Textual surgery on s-expressions earns this check."""
    depth = 0
    for line in text.splitlines():
        line = line.split(";", 1)[0]
        for character in line:
            depth += (character == "(") - (character == ")")
            if depth < 0:
                return False
    return depth == 0


def _guard_domain(text: str) -> str:
    """Textual surgery on the one action that moves a box.

    Deliberately narrow: this rewrites `fixtures/data/sokoban_domain.pddl`, a
    generated file with a fixed shape, and asserts on every anchor it depends on
    rather than pattern-matching hopefully.
    """
    requirements = "(:requirements :strips :typing)"
    assert requirements in text, "domain's requirement line moved"
    text = text.replace(
        requirements,
        "(:requirements :strips :typing :negative-preconditions"
        " :disjunctive-preconditions :universal-preconditions)")

    anchor = "    (adj ?from - cell ?to - cell ?d - dir))"
    assert anchor in text, "domain's predicate block moved"
    text = text.replace(anchor, anchor[:-1] + "\n"
                        "    (safe1 ?b - box ?c - cell)\n"
                        "    (safe2 ?b - box ?c - cell ?o - box ?c2 - cell))")

    push = "    :precondition (and (at-player ?p) (at ?b ?from) (clear ?to)"
    assert push in text, "push's precondition moved"
    text = text.replace(push, "    :precondition (and " + GUARD
                        + "\n                       (at-player ?p) (at ?b ?from)"
                          " (clear ?to)")
    return text


def _add_init(text: str, atoms: Sequence[str]) -> str:
    marker = "  (:goal"
    assert marker in text, "problem's goal block moved"
    head, tail = text.split(marker, 1)
    head = head.rstrip()
    assert head.endswith(")"), "problem's init block does not close as expected"
    head = head[:-1] + "\n" + "\n".join(atoms) + ")\n"
    return head + marker + tail


# ------------------------------------------------------- experiment A: pruning

LEVELS = ("open4", "open4far", "ringstuck")

M9_STUB = {                                    # STATUS.md's table, for reference
    "open4": (47, 47),
    "open4far": (808, 571),
    "ringstuck": (44, 22),
}


def _write(workdir: str, name: str, text: str) -> str:
    path = os.path.join(workdir, name)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return path


def deadlock_dividend(executable: str) -> List[Dict[str, object]]:
    with open(sokoban.DOMAIN_PATH, "r", encoding="utf-8") as fh:
        domain_text = fh.read()
    domain = parse_domain(domain_text)

    rows: List[Dict[str, object]] = []
    for name in LEVELS:
        level = sokoban.by_name(name)
        problem_text = level.problem_text()
        problem = parse_problem(problem_text)
        theorems = dc.carve(dc.Task.build(domain, problem))
        enc = encode(domain_text, problem_text, theorems)

        with tempfile.TemporaryDirectory() as workdir:
            base_d = _write(workdir, "domain.pddl", domain_text)
            base_p = _write(workdir, "problem.pddl", problem_text)
            enc_d = _write(workdir, "domain_guarded.pddl", enc.domain_text)
            enc_p = _write(workdir, "problem_guarded.pddl", enc.problem_text)
            before = run_fd(executable, base_d, base_p, BLIND)
            after = run_fd(executable, enc_d, enc_p, BLIND)

        stub_before, stub_after = M9_STUB[name]
        rows.append({
            "instance": name,
            "theorems": len(theorems),
            "theorems_encoded": enc.encoded,
            "theorems_skipped": enc.skipped,
            "fd_expansions_before": before.expansions,
            "fd_expansions_after": after.expansions,
            "fd_plan_before": before.plan_length,
            "fd_plan_after": after.plan_length,
            "fd_unsolvable_before": before.unsolvable,
            "fd_unsolvable_after": after.unsolvable,
            "fd_answered_before": before.answered,
            "fd_answered_after": after.answered,
            "fd_exit_code_before": before.exit_code,
            "fd_exit_code_after": after.exit_code,
            "same_answer": same_answer(before, after),
            "stub_expansions_before": stub_before,
            "stub_expansions_after": stub_after,
        })
    return rows


# ------------------------------------------- experiment B: stub versus FD, A0/A2

COLD_START = (
    ("a0-spike/match", "a0-spike/artifacts/pddl/domain.pddl",
     "a0-spike/artifacts/pddl/problem_match.pddl"),
    ("a0-spike/mismatch", "a0-spike/artifacts/pddl/domain.pddl",
     "a0-spike/artifacts/pddl/problem_mismatch.pddl"),
    ("cold-start-a0", "cold-start-a0/theory/generated/domain.pddl",
     "cold-start-a0/theory/generated/problem.pddl"),
    ("cold-start-a0/no-button", "cold-start-a0/theory/generated_no_button/domain.pddl",
     "cold-start-a0/theory/generated_no_button/problem.pddl"),
    ("cold-start-a2", "cold-start-a2/theory/generated/domain.pddl",
     "cold-start-a2/theory/generated/problem.pddl"),
    ("cold-start-a2/holed", "cold-start-a2/theory/generated_holed/domain.pddl",
     "cold-start-a2/theory/generated_holed/problem.pddl"),
    ("cold-start-a2/repaired", "cold-start-a2/theory/generated_repaired/domain.pddl",
     "cold-start-a2/theory/generated_repaired/problem.pddl"),
)


def cross_check(executable: str) -> List[Dict[str, object]]:
    """Every cold-start domain, solved by both backends, answers compared.

    The other tracks' directories are read and nothing else -- these are their
    committed artefacts, used here as instances.
    """
    rows: List[Dict[str, object]] = []
    for name, domain_rel, problem_rel in COLD_START:
        domain_path = os.path.join(REPO, domain_rel)
        problem_path = os.path.join(REPO, problem_rel)
        if not (os.path.exists(domain_path) and os.path.exists(problem_path)):
            rows.append({"instance": name, "status": "absent"})
            continue

        with open(domain_path, "r", encoding="utf-8") as fh:
            domain = parse_domain(fh.read())
        with open(problem_path, "r", encoding="utf-8") as fh:
            problem = parse_problem(fh.read())

        stub = fd_search.search(domain, problem)
        fd = run_fd(executable, domain_path, problem_path, BLIND)

        stub_length = None if stub.plan is None else len(stub.plan)
        agree = backends_agree(stub.plan is None, stub_length, fd)
        rows.append({
            "instance": name,
            "status": "ran",
            "stub_plan_length": stub_length,
            "stub_unsolvable": stub.plan is None,
            "stub_expansions": stub.expansions,
            "fd_plan_length": fd.plan_length,
            "fd_unsolvable": fd.unsolvable,
            "fd_answered": fd.answered,
            "fd_rung": fd.rung,
            "fd_exhausted_reported": fd.exhausted_reported,
            "fd_expansions": fd.expansions,
            "fd_exit_code": fd.exit_code,
            "agree": agree,
        })
    return rows


# ------------------------------------------------------------------- reporting

def render(report: Dict[str, object]) -> str:
    lines = ["# P-13 -- what the real planner bought", "",
             "Fast Downward: `%s`" % report["executable"],
             "Search configuration: `%s` (blind A*, the stub's twin)" % BLIND, "",
             "## A. The deadlock dividend, taken by Fast Downward", "",
             "| Instance | Theorems (encoded) | FD before -> after | FD saved |"
             " Stub before -> after (M9) | Same answer |",
             "|---|---|---|---|---|---|"]
    for row in report["deadlock_dividend"]:
        before, after = row["fd_expansions_before"], row["fd_expansions_after"]
        saved = "n/a"
        if isinstance(before, int) and isinstance(after, int) and before:
            saved = "%d (%.1f%%)" % (before - after, 100.0 * (before - after) / before)
        # Three values, because `same_answer` has three.  A run that did not
        # answer renders as `n/a`, never as `yes`.
        same = {True: "yes", False: "**NO**", None: "n/a — no answer"}[row["same_answer"]]
        lines.append("| `%s` | %d (%d) | %s -> %s | %s | %d -> %d | %s |" % (
            row["instance"], row["theorems"], row["theorems_encoded"],
            before, after, saved,
            row["stub_expansions_before"], row["stub_expansions_after"],
            same))

    lines += ["", "### What the numbers say", ""]
    for row in report["deadlock_dividend"]:
        before, after = row["fd_expansions_before"], row["fd_expansions_after"]
        stub_before, stub_after = row["stub_expansions_before"], row["stub_expansions_after"]
        if row["same_answer"] is None:
            # No prose about an instance neither run settled.  The earlier
            # version reached the `before == after` branch on `None == None` and
            # crashed there on `"%d" % None`; a loud crash was the only thing
            # keeping a fabricated negative result out of the report.
            lines.append(
                "* `%s` -- **no result**: Fast Downward exited %s before the "
                "guard and %s after, and at least one of those runs neither "
                "produced a plan nor proved unsolvability.  Nothing about this "
                "instance follows from it."
                % (row["instance"], row["fd_exit_code_before"],
                   row["fd_exit_code_after"]))
        elif row["same_answer"] is False:
            # Ahead of every other branch on purpose.  A refuted row with
            # `before == after` used to land on "true theorems buy nothing",
            # which asserts the soundness the verdict has just denied; the
            # dividend branches all presume the theorems are true, so the
            # refutation has to be read before any of them (D-034).
            lines.append(
                "* `%s` -- **not a dividend: the answer moved.**  Fast Downward "
                "returned a different answer with the theorems in (%d -> %d "
                "expansions), so at least one of them excludes a state the goal "
                "was reachable from.  A saving bought by an unsound theorem is "
                "not a saving, and no number on this row should be read as one."
                % (row["instance"], before, after))
        elif before == 0 and row["fd_unsolvable_before"]:
            lines.append(
                "* `%s` -- **the theorems had nothing to buy**: Fast Downward's "
                "translator settles this instance by relaxed reachability before "
                "the search starts (`No relaxed solution! Generating unsolvable "
                "task...`), so it expands %d states either way.  M9's %d -> %d is "
                "therefore a fact about the bundled search, which has no such "
                "check, and not a dividend a real planner would collect."
                % (row["instance"], before, stub_before, stub_after))
        elif before == after:
            lines.append(
                "* `%s` -- **zero, on both engines** (%d -> %d here, %d -> %d in "
                "M9).  D-020's negative result replicates: true theorems buy "
                "nothing when the answer lies shallower than any deadlock."
                % (row["instance"], before, after, stub_before, stub_after))
        else:
            fd_cut = 100.0 * (before - after) / before
            stub_cut = 100.0 * (stub_before - stub_after) / stub_before
            lines.append(
                "* `%s` -- **the dividend survives the change of engine**: %.1f%% "
                "fewer expansions on Fast Downward against %.1f%% on the bundled "
                "search, and the plan is %s steps either way.  The saving was not "
                "an artefact of the stub's node ordering."
                % (row["instance"], fd_cut, stub_cut, row["fd_plan_after"]))

    lines += ["", "## B. Stub versus Fast Downward on the cold-start domains", "",
              "| Instance | Stub | FD | Agree |", "|---|---|---|---|"]
    for row in report["cross_check"]:
        if row.get("status") != "ran":
            lines.append("| `%s` | absent | absent | n/a |" % row["instance"])
            continue
        stub = "UNSAT" if row["stub_unsolvable"] else "%s steps" % row["stub_plan_length"]
        if not row["fd_answered"]:
            fd = "no answer (exit %s)" % row["fd_exit_code"]
        elif row["fd_unsolvable"]:
            fd = "UNSAT"
        else:
            fd = "%s steps" % row["fd_plan_length"]
        agreement = {True: "yes", False: "**NO**", None: "n/a — no answer"}[row["agree"]]
        lines.append("| `%s` | %s | %s | %s |" % (
            row["instance"], stub, fd, agreement))
    return "\n".join(lines) + "\n"


def main() -> int:
    executable = backends.find_fast_downward()
    if executable is None:
        print("no Fast Downward reachable -- set FAST_DOWNWARD", file=sys.stderr)
        return 2

    report: Dict[str, object] = {
        "prompt_id": "P-13",
        "executable": executable,
        "search": BLIND,
        "deadlock_dividend": deadlock_dividend(executable),
        "cross_check": cross_check(executable),
    }
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "dividend.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, indent=2, sort_keys=True)
        fh.write("\n")
    text = render(report)
    with open(os.path.join(OUT_DIR, "DIVIDEND.md"), "w",
              encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
