"""Reproduce ledger X-1's 376 and X-5's 52, and drive both to zero.

`CONTRACTS/dsl_grammar_v0.2.md` said `frame persist` means "an object no firing
rule **mentions** is unchanged" and never said what `mentions` ranges over.
`a0-spike`'s expressivity ledger measured the cost of guessing: 376 transitions
under the event-signature reading, and a further 52 the guard language could not
express at all. v0.3 defines the word and repairs the guard; this probe is what
turns those two claims into two numbers this repository can re-derive.

**Ground truth is `a0-spike/world/sokoban2.py`, and it only ever grades.** The
predictor is always a module compiled by `theory_compiler` from a manual in
`tests/fixtures/`. The world belongs to the other track and is read, never
imported into the test suite: the two tracks meet at data, and a probe that
grades against a live implementation is the one place that has to reach across.
If `a0-spike` is absent this exits 77 and says so, rather than passing quietly.

The sweep is every **representable** (state, action) pair — 5 levels × 49 × 48 ×
4 = 47,040 — not the reachable ones. D-TC-012, and `a0-spike`'s own T-9: all
eight mismatching states of an earlier round were unreachable and the rule was
still wrong. `player == box` is the one exclusion, and it is an observability
argument rather than a reachability one: `render` paints the player over the box
and the box's position is genuinely unrecoverable from the frame.

    python -m tools.probe_mentions [--out <dir>]
"""

import argparse
import json
import os
import sys
from dataclasses import replace
from typing import Dict, List, Optional, Sequence, Set, Tuple

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # theory-compiler
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "src"))

from theory_compiler.generators.gen_python import generate_python    # noqa: E402
from theory_compiler.ir import build_ir                              # noqa: E402
from theory_compiler.parser.theory_parser import parse_theory        # noqa: E402
from theory_compiler.problem import load_problem                     # noqa: E402
from theory_compiler.writes import WriteSets                         # noqa: E402
from theory_compiler.parser.ast_nodes import (                       # noqa: E402
    Comparison, FieldAccess, FuncCall, GuardAction, GuardPredicate, NameRef,
    TupleLit,
)

FIXTURES = os.path.join(HERE, "tests", "fixtures")

# The manual's direction domain is lower case; the world's action alphabet is
# upper case. One mapping, in one place, so that a mismatch cannot come from
# the harness disagreeing with itself about which way "up" is.
DIRECTION = {"UP": "up", "DOWN": "down", "LEFT": "left", "RIGHT": "right"}


class GroundTruthMissing(Exception):
    """`a0-spike` is not present; there is nothing to grade against."""


def load_world():
    path = os.path.join(REPO, "a0-spike")
    if not os.path.isdir(path):
        raise GroundTruthMissing(
            "a0-spike/ is not in this checkout. This probe grades a compiled "
            "manual against that track's world; without it there is no ground "
            "truth and a green result would mean nothing.")
    if path not in sys.path:
        sys.path.insert(0, path)
    from world import levels, sokoban2                       # noqa: E402
    return levels, sokoban2


# --------------------------------------------------------- readings of `mentions`

def mentions_declared(rule, writes: WriteSets, instances: Set[str]) -> Set[str]:
    """**R3, the canon.** The objects the event assigns, per the declaration."""
    return writes.of_rule(rule)


def mentions_signature(rule, writes: WriteSets, instances: Set[str]) -> Set[str]:
    """**R2, as X-1 states it.** Every object among the event's arguments.

    This is the reading that measured 376 wrong, and the number is a fact about
    the *manual*, not about the reading: `slid(Box, dir)` had one object among
    its arguments and moved two. Give the event the pusher as an argument and
    this reading stops disagreeing with the canon — which is the whole content
    of X-1's second request, and the reason the fix is a signature change and
    not only a definition.
    """
    event = rule.event
    if not isinstance(event, FuncCall):
        return set()
    return {a.name for a in event.args
            if isinstance(a, NameRef) and a.name in instances}


def mentions_first_argument(rule, writes: WriteSets,
                            instances: Set[str]) -> Set[str]:
    """**R2′.** The event's first argument — "the object the event is about".

    Reported rather than argued against: it is what a reader with only the
    event *name* in front of them infers, it is what `CLAIMED_ARGS` would have
    guessed for an unknown event, and it is the guess v0.3's fail-closed clause
    exists to refuse. Its cost on the *repaired* manual is the measurement that
    says why refusing beats guessing.
    """
    event = rule.event
    if isinstance(event, FuncCall) and event.args:
        first = event.args[0]
        if isinstance(first, NameRef) and first.name in instances:
            return {first.name}
    return set()


def _names_in(expr, into: Set[str]) -> None:
    if isinstance(expr, NameRef):
        into.add(expr.name)
    elif isinstance(expr, FieldAccess):
        into.add(expr.obj)
    elif isinstance(expr, FuncCall):
        for a in expr.args:
            _names_in(a, into)
    elif isinstance(expr, Comparison):
        _names_in(expr.left, into)
        _names_in(expr.right, into)
    elif isinstance(expr, TupleLit):
        for e in expr.elements:
            _names_in(e, into)


def mentions_rule_text(rule, writes: WriteSets, instances: Set[str]) -> Set[str]:
    """**R1.** Every object name the rule writes down, guard included."""
    found: Set[str] = set()
    for clause in rule.guard.clauses:
        if isinstance(clause, GuardAction):
            for a in clause.action.args:
                _names_in(a, found)
        elif isinstance(clause, GuardPredicate):
            _names_in(clause.expr, found)
    _names_in(rule.event, found)
    return found & instances


READINGS = {
    "declared": mentions_declared,
    "signature": mentions_signature,
    "first_argument": mentions_first_argument,
    "rule_text": mentions_rule_text,
}


# ------------------------------------------------------------------- the predictor

def compile_manual(manual: str, problem_path: str):
    ast = parse_theory(open(os.path.join(FIXTURES, manual), encoding="utf-8").read())
    problem = load_problem(os.path.join(FIXTURES, problem_path))
    ir = build_ir(ast, problem)
    namespace: Dict[str, object] = {}
    exec(compile(generate_python(ast, problem), "<%s>" % manual, "exec"),
         namespace)
    by_name = {r.name: r for r in ir.rules}
    return namespace, ir, by_name


def predict(module, state, action, ir, by_name, reading, objects: Sequence[str]):
    """One successor under one reading of `mentions`, or a report of no answer.

    `cascade single_frame`: every guard reads the pre-state and all effects
    apply together. The frame axiom is then applied *on top* — which is the
    whole experiment, because when `mentions` under-reports the write set the
    axiom **undoes** an assignment the compiled effect just made.

    Returns `(successor, fired, unconstrained)`. `unconstrained` names the
    objects a firing rule mentions and no firing rule assigns: under R1 those
    have no defined successor at all, and counting them is how a reading that
    is not a definition shows up as something other than a mismatch.
    """
    fired = [name for name, guard, _effect, _objs in module["RULES"]
             if guard(state.copy(), action)]
    if not fired:
        return None, fired, []

    successor = state.copy()
    for name, _guard, effect, _objs in module["RULES"]:
        if name in fired:
            effect(successor)

    mentioned: Set[str] = set()
    written: Set[str] = set()
    instances = set(objects)
    for name in fired:
        mentioned |= reading(by_name[name], ir.writes, instances)
        written |= ir.writes.of_rule(by_name[name])
    for obj in objects:
        if obj not in mentioned:
            for axis in ir.axes:
                if axis.instance == obj:
                    setattr(successor, axis.field, getattr(state, axis.field))
    return successor, fired, sorted(mentioned - written)


# ---------------------------------------------------------------------- the sweep

def check_fixture_matches_level(problem, level, sokoban2) -> None:
    """The fixture is data; the level is live. They must still agree."""
    walls = {(r, c) for r in range(level.height) for c in range(level.width)
             if problem.board[r][c] == sokoban2.WALL}
    if walls != set(level.walls):
        raise SystemExit(
            "fixture %r has walls %s and level %r has %s. Regenerate with "
            "runs/20260728T102343Z-c7/make_sokoban2_problems.py — a probe run "
            "against a stale board measures a different world."
            % (problem.name, sorted(walls), level.name, sorted(level.walls)))
    by_name = {i.name: tuple(i.pos) for i in problem.instances}
    if by_name.get("Box") != tuple(level.box) or by_name.get("Player") != tuple(level.player):
        raise SystemExit(
            "fixture %r starts at %r and level %r starts at player=%r box=%r"
            % (problem.name, by_name, level.name, level.player, level.box))
    if tuple(problem.landmarks.get("target", ())) != tuple(level.target):
        raise SystemExit("fixture %r has a stale `target`" % problem.name)


def sweep(manual: str, reading_name: str, levels, sokoban2) -> Dict[str, object]:
    """One manual, one reading, every representable pair, stratified.

    **The stratification is not decoration.** X-1's 376 and X-5's 52 were
    counted in *different denominators* and mixing them would make this run's
    numbers unfalsifiable. `a0-spike`'s probe reports 376 out of the 39,960
    pairs in which neither object stands on a wall; the 52 are by construction
    inside the other 7,080. So each expectation below names the stratum it was
    measured in, and the all-pairs total is reported beside it rather than
    instead of it.
    """
    reading = READINGS[reading_name]
    objects = ("Box", "Player")
    strata = ("off_wall", "on_wall")
    pairs = {s: 0 for s in strata}
    wrong = {s: 0 for s in strata}
    no_rule = 0
    max_fired = 0
    undetermined = 0
    witnesses: List[dict] = []
    by_level: Dict[str, int] = {}

    for level in (levels.MATCH,) + levels.CROSSING_LEVELS:
        module, ir, by_name = compile_manual(
            manual, "sokoban2_%s_problem.json" % level.name)
        check_fixture_matches_level(ir.problem, level, sokoban2)
        State = module["State"]
        walls = set(level.walls)
        wrong_here = 0

        for pr in range(level.height):
            for pc in range(level.width):
                for br in range(level.height):
                    for bc in range(level.width):
                        if (pr, pc) == (br, bc):
                            continue
                        stratum = ("on_wall"
                                   if (pr, pc) in walls or (br, bc) in walls
                                   else "off_wall")
                        for world_dir in sokoban2.DIRECTIONS:
                            pairs[stratum] += 1
                            action = ("move", "Player", DIRECTION[world_dir])
                            state = State(Box_pos=(br, bc), Player_pos=(pr, pc))
                            successor, fired, loose = predict(
                                module, state, action, ir, by_name, reading,
                                objects)
                            max_fired = max(max_fired, len(fired))
                            if loose:
                                undetermined += 1
                            truth, _event = sokoban2.step(
                                level,
                                sokoban2.State(player=(pr, pc), box=(br, bc)),
                                world_dir)
                            if successor is None:
                                no_rule += 1
                                wrong[stratum] += 1
                                wrong_here += 1
                                continue
                            got = (successor.Player_pos, successor.Box_pos)
                            if got != (truth.player, truth.box):
                                wrong[stratum] += 1
                                wrong_here += 1
                                if len(witnesses) < 6:
                                    witnesses.append({
                                        "level": level.name,
                                        "player": [pr, pc], "box": [br, bc],
                                        "action": world_dir,
                                        "stratum": stratum,
                                        "fired": fired,
                                        "predicted": [list(got[0]), list(got[1])],
                                        "truth": [list(truth.player),
                                                  list(truth.box)],
                                    })
        by_level[level.name] = wrong_here

    return {
        "manual": manual,
        "reading": reading_name,
        "pairs": sum(pairs.values()),
        "pairs_by_stratum": pairs,
        "mismatches": sum(wrong.values()),
        "mismatches_by_stratum": wrong,
        "mismatches_by_level": by_level,
        "no_rule_fired": no_rule,
        "max_rules_fired": max_fired,
        "transitions_with_an_unconstrained_object": undetermined,
        "witnesses": witnesses,
    }


# The claims this probe exists to check. Each names the **stratum** its number
# was measured in, because 376 and 52 do not share a denominator.
EXPECTATIONS = [
    ("sokoban2_x5_theory.dsl", "first_argument", "off_wall", 376,
     "**ledger X-1, reproduced in its own denominator.** Over the 39,960 pairs "
     "in which neither object stands on a wall, taking `mentions` to be the "
     "object the event is about freezes the Player across every push. On the "
     "v0.2 signature `slid(o, dir)` this reading and `signature` coincide — "
     "`dir` is not an object — so this is the number X-1 measured, not a "
     "narrower relative of it"),
    ("sokoban2_x5_theory.dsl", "declared", "on_wall", 52,
     "ledger X-5: `push2` cannot say the Box is not standing on a wall, and "
     "every one of these fires it"),
    ("sokoban2_x5_theory.dsl", "declared", "off_wall", 0,
     "the X-5 defect is confined to the on-wall stratum — the guard set is "
     "otherwise exactly right, which is why X-5 is one defect and not a rot"),
    ("sokoban2_theory.dsl", "declared", None, 0,
     "v0.3, both repairs in: over all 47,040 pairs the manual predicts the "
     "world exactly"),
    ("sokoban2_theory.dsl", "signature", None, 0,
     "**the point of X-1's second request.** Giving `slid` the pusher as an "
     "argument makes the signature reading agree with the canon — the 376 was "
     "a fact about a manual that under-named its own event, and naming it is "
     "what closes the gap. A definition alone would have left the two readings "
     "still disagreeing, with the contract merely picking a side"),
    ("sokoban2_theory.dsl", "first_argument", "off_wall", 376,
     "**and why both halves of X-1 are load-bearing.** The same 376, unmoved, "
     "on the fully repaired manual: naming the pusher in the signature does "
     "nothing for a reader who takes `mentions` to be the first argument. The "
     "signature fix rescues the `signature` reading; only the *definition* "
     "rescues this one, which is why v0.3 does both and fails closed on events "
     "it has not been told about"),
    ("sokoban2_theory.dsl", "rule_text", None, 0,
     "R1 does not mispredict here — it leaves objects unconstrained, which is "
     "reported separately and is why it is not a definition"),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    try:
        levels, sokoban2 = load_world()
    except GroundTruthMissing as exc:
        print("SKIP: %s" % exc)
        return 77

    results = []
    failures = []
    cache: Dict[Tuple[str, str], Dict[str, object]] = {}
    for manual, reading, stratum, expected, why in EXPECTATIONS:
        key = (manual, reading)
        if key not in cache:
            cache[key] = sweep(manual, reading, levels, sokoban2)
        result = dict(cache[key])
        got = (result["mismatches"] if stratum is None
               else result["mismatches_by_stratum"][stratum])
        result["stratum"] = stratum or "all"
        result["expected"] = expected
        result["got"] = got
        result["why"] = why
        results.append(result)
        if got != expected:
            failures.append((manual, reading, stratum or "all", expected, got))
        print("%s %-22s %-17s %-9s %5d / %5d   (expected %d)" % (
            "ok" if got == expected else "XX",
            manual.replace("_theory.dsl", ""), reading, stratum or "all", got,
            result["pairs"] if stratum is None
            else result["pairs_by_stratum"][stratum],
            expected))

    report = {
        "prompt_id": "C7-dsl-v03-mentions",
        "ground_truth": "a0-spike/world/sokoban2.py",
        "predictor": "theory_compiler.generators.gen_python",
        "results": results,
        "failures": [
            {"manual": m, "reading": r, "stratum": s, "expected": e, "got": g}
            for m, r, s, e, g in failures
        ],
    }
    if args.out:
        os.makedirs(args.out, exist_ok=True)
        path = os.path.join(args.out, "mentions_probe.json")
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(report, handle, indent=2, sort_keys=True)
            handle.write("\n")
        print("wrote", path)

    if failures:
        for m, r, s, e, g in failures:
            print("FAIL %s under %s (%s): expected %d, got %d"
                  % (m, r, s, e, g))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
