"""Check the E7 audit run against the document it is the evidence for.

    cd engine-rig && python -m audit.verify runs/<id>

`DEADLOCK_CLAIM.md` argues from numbers that live in
`runs/20260728T150713Z-E7-deadlock-claim-audit/`.  Between the two there is
nothing but a human's transcription, and two drafts of that document were wrong
before the third.  This module is the machine that re-reads the artefacts and
says whether the document still describes them.

Eight checks, and the reason each one exists:

1. **Manifest hashes.**  Every file the manifest lists still hashes to what it
   said.  The cheap one, and it catches the failure that matters most often: an
   artefact edited by hand after the run that produced it.  `DEADLOCK_CLAIM.md`
   is in that list, so the document cannot drift from its own manifest either.

2. **Section 1's replication table.**  Nine rows, `far{4,6,7}` x
   `blind/lmcut/ipdb`, before and after.  These are the numbers E2 published and
   E7 claims to have reproduced; if the audit's own JSON stops agreeing with the
   table, the replication claim is prose.

3. **Section 3's coverage table.**  Reachable / truly dead / relaxation dead /
   theorem dead on `far{4,5,6}`, and `n_theorem_dead_outside_relaxation == 0` on
   all three.  That zero is the finding the whole document turns on.

4. **The relaxation-vs-FD crosscheck.**  Section 3 rests on a Python
   reimplementation of the delete relaxation.  The run compared it against Fast
   Downward's translator state by state; every row must agree, and the count is
   printed rather than assumed, because "0 disagreements in 0 rows" is not
   evidence.  The count is also summed across the five geometries the document
   quotes -- 116/116, of which only 16 are in `claim_audit.json` -- and the
   exhaustive far4 sweep (0 disagreements in 3342) is checked beside it.  An
   earlier draft published 16/16 as though it were the whole crosscheck.

5. **The rnd0021 counterexample of section 3a**, re-derived from source.  This
   is the one number in the document that says the containment is *not*
   universal, and it is worth more than the numbers that agree with everything
   else.  The instance is regenerated from `attacks/a3_family.py`'s
   `random_level(seed=20260728)` and its three sets are recomputed with the
   audit's own functions.  Pure Python: no planner is involved, so this check
   runs on a machine that has never built one.

6. **Carver soundness.**  On `rnd0021` and on `far4`, no theorem-dead state may
   be alive.  Everything else in the document is a claim about how much the
   theorems buy; this is the claim that they are not wrong.  The `far4` sets are
   re-derived here rather than read, and are required to agree with check 3's
   table -- a soundness check run on numbers that disagree with the document is
   not checking the document.

7. **Structural re-derivation on the real planner.**  A small number of facts
   re-measured and compared for **exact equality**: `far4`'s blind before/after
   (837 / 610), and the dead-start instances' 0-expansion / `h=infinity`
   verdicts.  Node counts, plan lengths, task sizes, initial heuristic values and
   exit codes are a function of the instance and the configuration, so equality
   is the right comparison.  (Section 7b withdraws `ipdb` *expansion counts* as
   evidence because they move between two different tasks with the pattern
   lottery.  That is not this comparison: the same task is re-run, which is the
   case where the lottery cannot bite, and re-running it twice here gives the
   same number.)

8. **Timing sanity, never timing equality.**  Wall clock is a property of this
   machine at this moment.  What can be checked is that the clocks are present,
   non-negative, and no larger than the run they sit inside.  A run where that
   broke would have a parsing bug, which is a real defect; a run 20% slower than
   last time is a busier laptop.

Check 7 is skipped with a stated reason, not silently, when no Fast Downward is
reachable -- the state every machine that has not built P-13's `.toolchain/` is
in, and the state this repo is in as checked out.  `bench/verify.py` set that
precedent and this module follows it: checks 1-6 and 8 are pure Python over the
committed artefacts and still run, so the audit is not wholly unverifiable
without the toolchain.
"""

import argparse
import hashlib
import importlib.util
import json
import os
import random
import sys
import tempfile
from collections import deque
from typing import Dict, List, Optional, Sequence, Tuple

from audit import claim, deadstart
from bench import compile_theorems, instances as bench_instances, toolchain
from engines.deadlock_carver.carve import Task, carve, pruner
from engines.fd_adapter import backends, pddl, search
from fixtures import sokoban

# --------------------------------------------------------------- what is pinned

# DEADLOCK_CLAIM.md section 1, transcribed.  instance, configuration, before,
# after, and the percentage the table prints.  `before` and `after` are
# expansion counts and are compared for equality; the percentage is a rounded
# derivative of them and is compared to 0.06 of a point, because equality of a
# rounding is not a fact about the measurement.
REPLICATION: Tuple[Tuple[str, str, int, int, float], ...] = (
    ("far4", "astar(blind())", 837, 610, 27.1),
    ("far4", "astar(lmcut())", 23, 22, 4.3),
    ("far4", "astar(ipdb())", 12, 12, 0.0),
    ("far6", "astar(blind())", 3070, 2762, 10.0),
    ("far6", "astar(lmcut())", 47, 47, 0.0),
    ("far6", "astar(ipdb())", 18, 18, 0.0),
    ("far7", "astar(blind())", 7196, 6365, 11.6),
    ("far7", "astar(lmcut())", 69, 68, 1.4),
    ("far7", "astar(ipdb())", 21, 21, 0.0),
)
PERCENT_TOLERANCE = 0.06

# DEADLOCK_CLAIM.md section 3: instance, reachable, truly dead, relaxation dead,
# theorem dead.  Every one exact, plus the zero in the last column.
COVERAGE: Tuple[Tuple[str, int, int, int, int], ...] = (
    ("far4", 3342, 2904, 2904, 1624),
    ("far5", 13774, 10687, 10687, 4508),
    ("far6", 42803, 29776, 29776, 9928),
)

# Section 3: "the state-by-state crosscheck of the Python relaxation against
# FD's translator now stands at 116/116 across five geometries and two
# encodings, not the 16/16 an earlier draft claimed."  16 of those live in
# `claim_audit.json`; the other 100 are in the five files below, and a document
# that quotes the total should be checked against the total.
CROSSCHECKS: Tuple[str, ...] = (
    "attacks/crosscheck_sokoban_ell.json",
    "attacks/crosscheck_sokoban_goal-in-corner.json",
    "attacks/crosscheck_sokoban_three-b.json",
    "attacks/crosscheck_noclear_far4.json",
    "attacks/crosscheck_noclear_box-on-goal.json",
)
CROSSCHECK_TOTAL = 116

# Section 3's exhaustive sweep: "0 disagreements in 3342".
FULLCHECK = "attacks/independent/fullcheck.json"
FULLCHECK_STATES = 3342

# DEADLOCK_CLAIM.md section 3a.  The counterexample, and the only row in the
# document where a theorem beats the relaxation.
RND0021 = {
    "n_reachable": 92,
    "n_truly_dead": 92,
    "n_relaxation_dead": 59,
    "n_theorem_dead": 70,
    "n_theorem_dead_outside_relaxation": 11,
}
# `attacks/a3_family.py`'s sweep, verbatim: `python a3_family.py random 60 20260728`.
RND0021_SEED = 20260728
RND0021_SWEEP_SIZE = 60
RND0021_NAME = "rnd0021"

# The verified copy of those numbers the run left beside the instance.  Read as
# a second opinion on the transcription above, not as the source of it.
RND0021_RECOMPUTE = os.path.join("attacks", "verify", "rnd0021", "recompute.json")

# Section 1's top row, re-measured in check 7.  One row, not nine: the other
# eight exercise the same three code paths and would cost a minute to say so
# again.  `blind` because it is the row with a dividend big enough that a
# regression could not hide in it.
FAR4_BLIND_BEFORE = 837
FAR4_BLIND_AFTER = 610

# Section 3d's instances, all three sizes.  They are the cheapest FD runs in the
# audit -- the dead ones expand nothing at all -- so there is no reason to sample.
DEADSTART_SIDES = (4, 5, 6)

# Compared for exact equality when a measurement is re-derived.  `initial_h` is
# in the list on purpose: `blind=infinity` versus `blind=1` is the difference
# between section 3d's finding and its opposite.
STRUCTURAL = ("expanded", "generated", "evaluated", "initial_h", "solved",
              "proved_unsolvable", "plan_length", "translator_facts",
              "returncode")


# ------------------------------------------------------------------- utilities

def sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _measurements(node, path: str = "") -> List[Tuple[str, Dict]]:
    """Every Fast Downward measurement in the report, wherever it is nested."""
    found: List[Tuple[str, Dict]] = []
    if isinstance(node, dict):
        if "heuristic" in node and "search_seconds" in node:
            found.append((path, node))
        for key, value in sorted(node.items()):
            found += _measurements(value, "%s/%s" % (path, key))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            found += _measurements(value, "%s/%d" % (path, index))
    return found


def _sets(problem_text: str) -> Dict[str, object]:
    """The three sets of section 3, over one instance's whole reachable space.

    `claim.coverage()` does this for `far{N}` only, and returns booleans where
    this module wants counts.  The bodies are the same -- `claim._collect`,
    `claim.relaxed_reachable_goal`, the carver's own `pruner` -- so this is the
    audit's own arithmetic, applied to an instance `coverage()` cannot name.
    """
    domain = pddl.parse_domain(open(sokoban.DOMAIN_PATH, encoding="utf-8").read())
    problem = pddl.parse_problem(problem_text)
    task = Task.build(domain, problem)
    theorems = carve(task)
    dead = pruner(theorems)

    grounded = pddl.ground_actions(domain, problem)
    actions, _initial, _ok = search.strip_static(domain, problem, grounded)
    static = pddl.static_predicates(domain)

    states = claim._collect(domain, problem)
    index = {state: i for i, state in enumerate(states)}

    backward: List[List[int]] = [[] for _ in states]
    goals: List[int] = []
    for i, state in enumerate(states):
        if search.is_goal(problem, state, static):
            goals.append(i)
            continue
        for action in actions:
            if not search.applicable(action, state):
                continue
            j = index.get(search.successor(action, state))
            if j is not None:
                backward[j].append(i)
    alive = set(goals)
    queue = deque(goals)
    while queue:
        i = queue.popleft()
        for j in backward[i]:
            if j not in alive:
                alive.add(j)
                queue.append(j)

    theorem_dead = {i for i, s in enumerate(states) if dead(s)}
    truly_dead = {i for i in range(len(states)) if i not in alive}
    relaxation_dead = {
        i for i, s in enumerate(states)
        if not claim.relaxed_reachable_goal(actions, s, problem, static)
    }
    return {
        "n_reachable": len(states),
        "n_goal_states": len(goals),
        "n_theorem_dead": len(theorem_dead),
        "n_relaxation_dead": len(relaxation_dead),
        "n_truly_dead": len(truly_dead),
        "n_theorem_dead_outside_relaxation": len(theorem_dead - relaxation_dead),
        "n_theorem_dead_not_truly_dead": len(theorem_dead - truly_dead),
        "n_theorems": len(theorems),
    }


def _regenerate_rnd0021(run_dir: str) -> Tuple[Optional[object], List[str]]:
    """Rebuild the counterexample from the sweep's generator and its seed.

    The board file the run left behind is *not* the source: it is loaded, if it
    is there, only to check that the generator still produces it byte for byte.
    A counterexample that survives only as a file somebody could have edited is
    not a counterexample.
    """
    problems: List[str] = []
    script = os.path.join(run_dir, "attacks", "a3_family.py")
    if not os.path.isfile(script):
        return None, ["missing: attacks/a3_family.py -- the instance cannot be "
                      "regenerated, so section 3a rests on a JSON file alone"]

    attacks = os.path.dirname(script)
    if attacks not in sys.path:
        sys.path.insert(0, attacks)
    spec = importlib.util.spec_from_file_location("audit_verify_a3_family", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    rng = random.Random(RND0021_SEED)
    levels, index = [], 0
    while len(levels) < RND0021_SWEEP_SIZE:
        level = module.random_level(rng, index)
        index += 1
        if level is not None:
            levels.append(level)
    found = [level for level in levels if level.name == RND0021_NAME]
    if not found:
        return None, ["%s is not in the first %d levels of random_level(seed=%d) "
                      "-- the generator has changed"
                      % (RND0021_NAME, RND0021_SWEEP_SIZE, RND0021_SEED)]

    level = found[0]
    board = os.path.join(attacks, "work", "a3", RND0021_NAME, "%s.pddl" % RND0021_NAME)
    if os.path.isfile(board):
        with open(board, encoding="utf-8") as fh:
            if fh.read() != level.problem_text():
                problems.append(
                    "the generator no longer reproduces attacks/work/a3/%s/%s.pddl "
                    "byte for byte -- the measured board and the regenerated one "
                    "have parted company" % (RND0021_NAME, RND0021_NAME))
    else:
        problems.append(
            "attacks/work/a3/%s/%s.pddl is absent, so the regenerated board could "
            "not be compared against the measured one" % (RND0021_NAME, RND0021_NAME))
    return level, problems


# --------------------------------------------------------------------- checks

def check_manifest_hashes(run_dir: str, manifest: Dict) -> Tuple[List[str], str]:
    problems: List[str] = []
    entries = manifest.get("files", [])
    for entry in entries:
        path = os.path.join(run_dir, entry["path"])
        if not os.path.isfile(path):
            problems.append("missing: %s" % entry["path"])
            continue
        actual = sha256(path)
        if actual != entry["sha256"]:
            problems.append(
                "%s: sha256 %s, manifest says %s -- edited after the run?"
                % (entry["path"], actual[:16], entry["sha256"][:16])
            )
    if not entries:
        problems.append("MANIFEST.json lists no files, so nothing was checked")
    return problems, "%d files" % len(entries)


def check_replication(report: Dict) -> Tuple[List[str], str]:
    """Section 1's nine rows, exactly as the table prints them."""
    problems: List[str] = []
    rows = {(row["instance"], row["config"]): row
            for row in report.get("replication", [])}
    for instance, config, before, after, percent in REPLICATION:
        row = rows.get((instance, config))
        if row is None:
            problems.append("%s/%s: section 1 has this row, claim_audit.json "
                            "does not" % (instance, config))
            continue
        for field, expected in (("before", before), ("after", after)):
            actual = row[field].get("expanded")
            if actual != expected:
                problems.append(
                    "%s/%s: %s is %r in claim_audit.json, section 1 prints %r"
                    % (instance, config, field, actual, expected))
        if row.get("guard") != "singleton":
            problems.append(
                "%s/%s: guard is %r, section 1 says the singleton guard was held "
                "fixed on both sides" % (instance, config, row.get("guard")))
        if row.get("plan_unchanged") is not True:
            problems.append(
                "%s/%s: plan_unchanged is %r -- a dividend paid for by a shorter "
                "plan is a broken guard, not a speed-up"
                % (instance, config, row.get("plan_unchanged")))
        dividend = row.get("dividend")
        if dividend is None:
            problems.append("%s/%s: no dividend recorded" % (instance, config))
        elif abs(dividend * 100.0 - percent) > PERCENT_TOLERANCE:
            problems.append(
                "%s/%s: dividend %.2f%%, section 1 prints %.1f%%"
                % (instance, config, dividend * 100.0, percent))
    extra = set(rows) - {(i, c) for i, c, _b, _a, _p in REPLICATION}
    if extra:
        problems.append("claim_audit.json has replication rows section 1 does "
                        "not table: %s" % sorted(extra))
    return problems, "%d rows" % len(REPLICATION)


def check_coverage(report: Dict) -> Tuple[List[str], str]:
    """Section 3's set table, and the zero it turns on."""
    problems: List[str] = []
    rows = {row["instance"]: row for row in report.get("coverage", [])}
    for instance, reachable, truly, relaxation, theorem in COVERAGE:
        row = rows.get(instance)
        if row is None:
            problems.append("%s: section 3 has this row, claim_audit.json does not"
                            % instance)
            continue
        for field, expected in (("n_reachable", reachable),
                                ("n_truly_dead", truly),
                                ("n_relaxation_dead", relaxation),
                                ("n_theorem_dead", theorem),
                                ("n_theorem_dead_outside_relaxation", 0)):
            if row.get(field) != expected:
                problems.append("%s: %s is %r, section 3 prints %r"
                                % (instance, field, row.get(field), expected))
        for flag in ("theorem_dead_within_relaxation_dead",
                     "theorem_dead_within_truly_dead",
                     "relaxation_dead_within_truly_dead"):
            if row.get(flag) is not True:
                problems.append("%s: %s is %r -- section 3's containment chain "
                                "does not hold in the artefact"
                                % (instance, flag, row.get(flag)))
    return problems, "%d instances" % len(COVERAGE)


def check_relaxation_vs_fd(run_dir: str, report: Dict) -> Tuple[List[str], str]:
    """The Python relaxation against Fast Downward's translator, row by row.

    Counted, not just checked for zero disagreements: "0 disagreements in 0
    rows" is not evidence, and section 3 quotes a total (116/116) that no single
    artefact holds.
    """
    problems: List[str] = []
    section = report.get("relaxation_vs_fd") or {}
    rows = section.get("rows", [])
    disagreements = [row for row in rows if not row.get("agree")]
    if not rows:
        problems.append("no crosscheck rows in claim_audit.json: an unchecked "
                        "reimplementation is a second guess, not a second opinion")
    for row in disagreements:
        problems.append(
            "state %s: the Python relaxation says dead=%r, FD's translator says "
            "dead=%r" % (row.get("state"), row.get("python_relaxation_dead"),
                         row.get("fd_translator_dead")))
    if section.get("n_checked") != len(rows):
        problems.append("n_checked is %r but %d rows are recorded"
                        % (section.get("n_checked"), len(rows)))
    if section.get("n_agree") != len(rows) - len(disagreements):
        problems.append("n_agree is %r but %d of %d rows agree"
                        % (section.get("n_agree"), len(rows) - len(disagreements),
                           len(rows)))
    checked = len(rows)
    agreed = len(rows) - len(disagreements)

    for relative in CROSSCHECKS:
        path = os.path.join(run_dir, relative)
        if not os.path.isfile(path):
            problems.append("missing: %s -- part of section 3's 116/116" % relative)
            continue
        with open(path, encoding="utf-8") as fh:
            geometry = json.load(fh)
        checked += geometry.get("n_checked") or 0
        agreed += geometry.get("n_agree") or 0
        for field in ("n_python_dead_fd_alive", "n_python_alive_fd_dead"):
            if geometry.get(field):
                problems.append("%s: %s is %r, so the Python relaxation is not "
                                "FD's on that geometry"
                                % (relative, field, geometry.get(field)))
    if checked != CROSSCHECK_TOTAL or agreed != CROSSCHECK_TOTAL:
        problems.append(
            "the one-state crosscheck stands at %d/%d, section 3 prints %d/%d"
            % (agreed, checked, CROSSCHECK_TOTAL, CROSSCHECK_TOTAL))

    # And the exhaustive one: every far4 state, not a sample.
    full_path = os.path.join(run_dir, FULLCHECK)
    if not os.path.isfile(full_path):
        problems.append("missing: %s -- section 3's exhaustive far4 sweep"
                        % FULLCHECK)
        exhaustive = "no exhaustive sweep"
    else:
        with open(full_path, encoding="utf-8") as fh:
            full = json.load(fh)
        disagreed = full.get("python_relaxation_disagrees_with_fd")
        if full.get("n_checked") != FULLCHECK_STATES:
            problems.append("%s: n_checked is %r, section 3 says all %d far4 "
                            "states" % (FULLCHECK, full.get("n_checked"),
                                        FULLCHECK_STATES))
        if disagreed:
            problems.append("%s: the Python relaxation disagrees with FD on %d "
                            "far4 states" % (FULLCHECK, len(disagreed)))
        if full.get("n_fd_truly_dead_by_blind_search") != \
                full.get("n_fd_relaxation_dead"):
            problems.append(
                "%s: FD's blind oracle found %r truly dead states and FD's "
                "relaxation %r -- section 3 says they are the same set"
                % (FULLCHECK, full.get("n_fd_truly_dead_by_blind_search"),
                   full.get("n_fd_relaxation_dead")))
        exhaustive = ("%d/%d exhaustive on far4"
                      % (full.get("n_checked", 0) - len(disagreed or []),
                         full.get("n_checked", 0)))
    return problems, "%d/%d one-state rows agree, %d disagreements; %s" % (
        agreed, checked, checked - agreed, exhaustive)


def check_rnd0021(run_dir: str) -> Tuple[List[str], str, Optional[Dict[str, object]]]:
    """Section 3a's counterexample, re-derived from the generator.

    Structural, not timed, and no planner is consulted: the sets are recomputed
    from the audit's own functions over the whole 92-state space.  The verified
    copy the run left in `attacks/verify/rnd0021/` is read afterwards and must
    agree with what was just computed, so a drifted artefact and a drifted
    implementation are told apart.
    """
    level, problems = _regenerate_rnd0021(run_dir)
    if level is None:
        return problems, "not regenerable", None

    derived = _sets(level.problem_text())
    for field, expected in sorted(RND0021.items()):
        if derived[field] != expected:
            problems.append("rnd0021: %s re-derives to %r, section 3a states %r"
                            % (field, derived[field], expected))

    recompute_path = os.path.join(run_dir, RND0021_RECOMPUTE)
    if os.path.isfile(recompute_path):
        with open(recompute_path, encoding="utf-8") as fh:
            recorded = json.load(fh)
        for field in sorted(RND0021):
            if recorded.get(field) != derived[field]:
                problems.append(
                    "rnd0021: %s re-derives to %r, %s records %r"
                    % (field, derived[field], RND0021_RECOMPUTE,
                       recorded.get(field)))
    else:
        problems.append("missing: %s -- the run's own verified copy of these "
                        "numbers is gone" % RND0021_RECOMPUTE)

    note = ("%d reachable, %d truly dead, %d relaxation dead, %d theorem dead, "
            "%d outside the relaxation"
            % (derived["n_reachable"], derived["n_truly_dead"],
               derived["n_relaxation_dead"], derived["n_theorem_dead"],
               derived["n_theorem_dead_outside_relaxation"]))
    return problems, note, derived


def check_soundness(manifest: Dict, rnd: Optional[Dict[str, object]]
                    ) -> Tuple[List[str], str]:
    """No theorem-dead state may be alive.  On the counterexample and on far4."""
    problems: List[str] = []
    counts = []

    if rnd is None:
        problems.append("rnd0021 could not be re-derived, so its soundness was "
                        "not checked (see the previous check)")
    else:
        exceptions = rnd["n_theorem_dead_not_truly_dead"]
        counts.append("rnd0021 %d/%d" % (exceptions, rnd["n_theorem_dead"]))
        if exceptions:
            problems.append("rnd0021: %d theorem-dead states are alive -- the "
                            "carver is unsound" % exceptions)

    far4 = _sets(bench_instances.far_level(4).problem_text())
    counts.append("far4 %d/%d"
                  % (far4["n_theorem_dead_not_truly_dead"], far4["n_theorem_dead"]))
    if far4["n_theorem_dead_not_truly_dead"]:
        problems.append("far4: %d theorem-dead states are alive -- the carver is "
                        "unsound" % far4["n_theorem_dead_not_truly_dead"])
    # The sets soundness is asserted over must be the sets the document tables,
    # or this check is about some other instance than the one section 3 reports.
    _name, reachable, truly, relaxation, theorem = COVERAGE[0]
    for field, expected in (("n_reachable", reachable), ("n_truly_dead", truly),
                            ("n_relaxation_dead", relaxation),
                            ("n_theorem_dead", theorem)):
        if far4[field] != expected:
            problems.append("far4: %s re-derives to %r, section 3 prints %r"
                            % (field, far4[field], expected))

    for line in manifest.get("soundness_problems", []):
        problems.append("recorded in MANIFEST.json: %s" % line)
    return problems, "theorem-dead states that are alive: " + ", ".join(counts)


def check_structural_fd(report: Dict, executable: str, work: str,
                        log_dir: str) -> Tuple[List[str], str]:
    """Re-measure, and compare the deterministic half exactly."""
    problems: List[str] = []
    os.makedirs(work, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)
    measured = 0

    # -- section 1's top row: far4, astar(blind()), before and after.
    level = bench_instances.far_level(4)
    text = level.problem_text()
    plain = os.path.join(work, "far4.pddl")
    with open(plain, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    domain = pddl.parse_domain(open(sokoban.DOMAIN_PATH, encoding="utf-8").read())
    problem = pddl.parse_problem(text)
    theorems = carve(Task.build(domain, problem))
    guard_domain, guard_problem = compile_theorems.write_guarded(
        work, "far4", text, theorems, guard="singleton", problem=problem)

    recorded_row = next(
        (row for row in report.get("replication", [])
         if row["instance"] == "far4" and row["config"] == "astar(blind())"), None)
    for side, domain_path, problem_path, expected in (
            ("before", sokoban.DOMAIN_PATH, plain, FAR4_BLIND_BEFORE),
            ("after", guard_domain, guard_problem, FAR4_BLIND_AFTER)):
        fresh = claim._measure(executable, domain_path, problem_path, "blind",
                               log_dir, "V-far4-blind-%s" % side)
        measured += 1
        if fresh.get("expanded") != expected:
            problems.append(
                "far4/astar(blind())/%s: expands %r now, section 1 prints %r"
                % (side, fresh.get("expanded"), expected))
        if recorded_row is not None:
            problems += _compare("far4/astar(blind())/%s" % side,
                                 fresh, recorded_row[side])

    # -- section 3d: the dead starts, and the live control beside them.
    recorded_starts = {row["instance"]: row for row in report.get("dead_starts", [])}
    for level in deadstart.levels(DEADSTART_SIDES):
        path = os.path.join(work, "%s.pddl" % level.name)
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(level.problem_text())
        recorded = recorded_starts.get(level.name)
        if recorded is None:
            problems.append("%s: not in the run's dead_starts section" % level.name)
            continue
        by_heuristic = {row["heuristic"]: row for row in recorded["unguarded"]}
        for _tier, heuristic in claim.CONFIGS:
            name = claim._label(heuristic)
            fresh = claim._measure(executable, sokoban.DOMAIN_PATH, path, heuristic,
                                   log_dir, "V-%s-%s" % (level.name, name))
            measured += 1
            was = by_heuristic.get(name)
            if was is None:
                problems.append("%s/%s: not in the run" % (level.name, name))
                continue
            problems += _compare("%s/%s" % (level.name, name), fresh, was)
            # And the verdict section 3d states in words, independent of what the
            # run happened to record.
            if level.name.startswith("deadstart-"):
                if fresh.get("expanded") != 0 or not fresh.get("proved_unsolvable") \
                        or "infinity" not in (fresh.get("initial_h") or ""):
                    problems.append(
                        "%s/%s: section 3d says 0 expansions, h=infinity, proved "
                        "unsolvable; measured %r / %r / %r"
                        % (level.name, name, fresh.get("expanded"),
                           fresh.get("initial_h"), fresh.get("proved_unsolvable")))
            else:
                if not fresh.get("solved") or not fresh.get("expanded"):
                    problems.append(
                        "%s/%s: the control must search and solve, or the "
                        "instrument cannot tell the two cases apart; measured "
                        "%r expansions, solved=%r"
                        % (level.name, name, fresh.get("expanded"),
                           fresh.get("solved")))
    return problems, "%d measurements re-derived" % measured


def _compare(label: str, fresh: Dict, was: Dict) -> List[str]:
    problems = []
    for field in STRUCTURAL:
        if fresh.get(field) != was.get(field):
            problems.append("%s: %s is now %r, the run recorded %r"
                            % (label, field, fresh.get(field), was.get(field)))
    return problems


def check_timings(report: Dict) -> Tuple[List[str], str]:
    """Present and ordered.  Never equal -- see the module docstring."""
    problems: List[str] = []
    total = report.get("seconds")
    if not isinstance(total, (int, float)):
        problems.append("the run records no total wall clock")
        total = None
    checked = 0
    for path, measurement in _measurements(report):
        if measurement.get("error"):
            # The `full` guard's axiom refusal: FD exits 34 before it searches,
            # so there is no search time to record.  `bench/verify.py` skips its
            # over-budget rows for the same reason.
            continue
        seconds = measurement.get("search_seconds")
        if seconds is None:
            problems.append("%s: no search time recorded and no error to explain it"
                            % path)
            continue
        checked += 1
        if seconds < 0:
            problems.append("%s: search time %.6f is negative" % (path, seconds))
        if total is not None and seconds > total:
            problems.append(
                "%s: FD search time %.6f exceeds the %.1f s the whole run took -- "
                "impossible, so one of them is misparsed" % (path, seconds, total))
    if total is not None and checked and total < 0:
        problems.append("the run's total wall clock is negative")
    return problems, "%d timings present and ordered inside %s s" % (checked, total)


# ----------------------------------------------------------------- the driver

def _verdict(number: int, title: str, problems: Sequence[str],
             skip: Optional[str] = None, note: Optional[str] = None) -> None:
    if skip is not None:
        print("%d. %-52s SKIP" % (number, title))
        print("      reason: %s" % skip)
        return
    print("%d. %-52s %s" % (number, title, "FAIL" if problems else "PASS"))
    if note:
        print("      %s" % note)
    for line in problems:
        print("      - %s" % line)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="audit.verify")
    parser.add_argument("run_dir")
    parser.add_argument("--fd", default=None, help="path to fast-downward.py")
    parser.add_argument(
        "--work", default=None,
        help="where check 7 writes its instances and FD logs. Defaults to a "
             "temporary directory: a verifier that writes into the run it is "
             "checking has changed the thing it is checking.")
    args = parser.parse_args(argv)
    run_dir = os.path.abspath(args.run_dir)

    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    repo_root = os.path.dirname(here)

    with open(os.path.join(run_dir, "MANIFEST.json"), encoding="utf-8") as fh:
        manifest = json.load(fh)
    with open(os.path.join(run_dir, "claim_audit.json"), encoding="utf-8") as fh:
        report = json.load(fh)

    problems: List[str] = []
    skipped: List[str] = []

    found, note = check_manifest_hashes(run_dir, manifest)
    _verdict(1, "manifest hashes", found, note=note)
    problems += found

    found, note = check_replication(report)
    _verdict(2, "section 1 replication table", found, note=note)
    problems += found

    found, note = check_coverage(report)
    _verdict(3, "section 3 coverage table", found, note=note)
    problems += found

    found, note = check_relaxation_vs_fd(run_dir, report)
    _verdict(4, "the Python relaxation against FD's translator", found, note=note)
    problems += found

    found, note, rnd = check_rnd0021(run_dir)
    _verdict(5, "section 3a's rnd0021 counterexample, re-derived", found, note=note)
    problems += found

    found, note = check_soundness(manifest, rnd)
    _verdict(6, "carver soundness on rnd0021 and far4", found, note=note)
    problems += found

    executable = args.fd or backends.find_fast_downward()
    if executable is None:
        reason = (
            "No Fast Downward reachable, so nothing can be re-measured on the "
            "real planner. This is the expected state on a machine that has not "
            "built `.toolchain/` -- see %s. Checks 1-6 and 8 above are pure "
            "Python over the committed artefacts and did run."
            % toolchain.TOOLCHAIN_MANIFEST
        )
        skipped.append(reason)
        _verdict(7, "structural re-derivation on the real planner", [], skip=reason)
    else:
        live = toolchain.probe(executable, repo_root)
        recorded_tool = manifest.get("toolchain", {})
        if recorded_tool.get("binary_sha256") and \
                live["binary_sha256"] != recorded_tool["binary_sha256"]:
            problems.append(
                "planner mismatch: this machine has %s, the run used %s -- the "
                "structural comparison below is against a different binary"
                % ((live["binary_sha256"] or "?")[:16],
                   recorded_tool["binary_sha256"][:16]))
        base = args.work or tempfile.mkdtemp(prefix="audit-verify-")
        work = os.path.join(base, "instances")
        log_dir = os.path.join(base, "logs")
        found, note = check_structural_fd(report, executable, work, log_dir)
        _verdict(7, "structural re-derivation on the real planner", found, note=note)
        problems += found

    found, note = check_timings(report)
    _verdict(8, "timing sanity (ordering only, never equality)", found, note=note)
    problems += found

    if problems:
        print("\nFAIL (%d):" % len(problems))
        for line in problems:
            print("  - %s" % line)
        return 1
    print("\nok -- %s verifies%s"
          % (run_dir, " (FD checks skipped)" if skipped else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
