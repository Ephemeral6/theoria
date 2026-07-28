"""The `conflict` obligation, and the inventory of what it currently proves.

v0.2 made a manual declare which of constraint 9's two routes it claims and
checked neither. `theory_compiler.conflict` discharges the declaration; this
module pins what it can prove, what it refuses, and — in `TestInventory` — the
exact status of every manual in the repository, so that a new undischarged pair
anywhere turns this file red rather than passing unnoticed.
"""

import json
from pathlib import Path

import pytest

from theory_compiler.conflict import (
    CLAIMED_ARGS, CONDITIONS, DISTINCT_POSITIONS, ConflictError, Uniqueness,
    cell_universe, certify_conflict, certify_uniqueness, check_conflict,
    claimed_objects, disjointness_reason,
)
from theory_compiler.generators.gen_python import generate_python
from theory_compiler.ir import build_ir
from theory_compiler.parser.ast_nodes import SemanticsSection
from theory_compiler.parser.theory_parser import parse_theory
from theory_compiler.problem import load_problem

FIXTURES = Path(__file__).parent / "fixtures"
REPO = Path(__file__).resolve().parents[2]

EXCLUSIVE = SemanticsSection(frame="persist", conflict="exclusive",
                             cascade="single_frame")


def rules_of(source: str):
    return parse_theory(source).rules.rules


def one_rule(guard: str, event: str, name: str = "r"):
    source = (
        "word_table:\n  board\n  object Cart { pos: Coord, color: Int }\n"
        "  object Door { pos: Coord, color: Int, present: Bool }\n"
        "  landmark origin\n"
        "semantics:\n  frame persist\n  conflict exclusive\n"
        "  cascade single_frame\n"
        "events:\n  event moved(o, dir) | teleported(o, dest) | vanished(o)\n"
        "rules:\n  rule %s\n    when %s then %s\n"
        "goal:\n  goal Cart.pos = (1, 1)\n" % (name, guard, event))
    return rules_of(source)[0]


# ------------------------------------------------------- what "claims" means

class TestClaimedObjects:
    def test_a_single_object_event_claims_its_subject(self):
        rule = one_rule("act=push(Cart, up)", "moved(Cart, up)")
        assert claimed_objects(rule) == {"Cart"}

    def test_a_peg_jump_claims_both_the_mover_and_the_jumped(self):
        source = (FIXTURES / "peg_theory.dsl").read_text(encoding="utf-8")
        ast = parse_theory(source)
        ir = build_ir(ast, load_problem(str(FIXTURES / "peg5_problem.json")))
        jump = next(r for r in ir.rules if r.name.startswith("jump_right"))
        assert len(claimed_objects(jump)) == 2, (
            "jumped/3 kills the peg it jumps over; a claim set of one would "
            "skip every pair that event creates")

    def test_an_unknown_event_fails_closed(self):
        rule = one_rule("act=push(Cart, up)", "dissolved(Cart, Door, up)")
        with pytest.raises(ConflictError) as exc:
            claimed_objects(rule)
        assert "no claim table" in str(exc.value)

    def test_the_claim_table_covers_every_event_the_predictor_implements(self):
        """Drift pin. `gen_python._effect` decides what actually gets mutated;
        this table decides what gets *checked*. If the first grows and the
        second does not, a two-object event silently stops being examined."""
        source = (Path(generate_python.__globals__["__file__"])).read_text(
            encoding="utf-8")
        implemented = set()
        for line in source.splitlines():
            line = line.strip()
            for prefix in ('if key == ("', 'if key in (("'):
                if line.startswith(prefix):
                    for chunk in line.split('("')[1:]:
                        name, _, rest = chunk.partition('"')
                        arity = rest.strip(" ,)").split(")")[0].strip(", ")
                        if arity.isdigit():
                            implemented.add((name, int(arity)))
        assert implemented, "could not read the backend's event table"
        missing = sorted(implemented - set(CLAIMED_ARGS))
        assert not missing, (
            "gen_python mutates state for %s, and the conflict checker has no "
            "claim table for them, so pairs involving them are skipped" % (missing,))


# --------------------------------------------------- the five decidable rules

class TestDisjointness:
    def test_different_action_names(self):
        a = one_rule("act=push(Cart, up)", "moved(Cart, up)", "a")
        b = one_rule("act=pull(Cart, up)", "moved(Cart, up)", "b")
        assert "different actions" in (disjointness_reason(a, b) or "")

    def test_same_action_different_direction(self):
        """The common case: one schema grounded over four directions."""
        a = one_rule("act=push(Cart, up)", "moved(Cart, up)", "a")
        b = one_rule("act=push(Cart, down)", "moved(Cart, down)", "b")
        reason = disjointness_reason(a, b) or ""
        assert "action arguments differ at position 1" in reason
        assert "up" in reason and "down" in reason

    def test_same_action_same_arguments_is_not_a_reason(self):
        a = one_rule("act=push(Cart, up)", "moved(Cart, up)", "a")
        b = one_rule("act=push(Cart, up)", "teleported(Cart, origin)", "b")
        assert disjointness_reason(a, b) is None

    def test_a_predicate_against_its_negation(self):
        a = one_rule("act=push(Cart, up) and free(above(Cart))",
                     "moved(Cart, up)", "a")
        b = one_rule("act=push(Cart, up) and not free(above(Cart))",
                     "teleported(Cart, origin)", "b")
        assert "negation" in (disjointness_reason(a, b) or "")

    def test_two_colours_of_one_cell(self):
        a = one_rule("act=push(Cart, up) and colored(above(Cart), 3)",
                     "moved(Cart, up)", "a")
        b = one_rule("act=push(Cart, up) and colored(above(Cart), 7)",
                     "teleported(Cart, origin)", "b")
        assert "different colours" in (disjointness_reason(a, b) or "")

    def test_free_against_a_non_background_colour(self):
        a = one_rule("act=push(Cart, up) and free(above(Cart))",
                     "moved(Cart, up)", "a")
        b = one_rule("act=push(Cart, up) and colored(above(Cart), 3)",
                     "teleported(Cart, origin)", "b")
        assert "free" in (disjointness_reason(a, b, background=0) or "")

    def test_free_against_the_background_colour_is_not_a_reason(self):
        """The soundness edge: `colored(t, 0)` and `free(t)` agree."""
        a = one_rule("act=push(Cart, up) and free(above(Cart))",
                     "moved(Cart, up)", "a")
        b = one_rule("act=push(Cart, up) and colored(above(Cart), 0)",
                     "teleported(Cart, origin)", "b")
        assert disjointness_reason(a, b, background=0) is None

    def test_free_against_wall(self):
        a = one_rule("act=push(Cart, up) and free(toward(Cart, up))",
                     "moved(Cart, up)", "a")
        b = one_rule("act=push(Cart, up) and above(Cart) = wall",
                     "teleported(Cart, origin)", "b")
        assert "off the board" in (disjointness_reason(a, b) or "")

    def test_above_and_toward_up_name_one_cell(self):
        """Without normalisation the two spellings never meet and every pair
        written in mixed style is reported undischarged."""
        a = one_rule("act=push(Cart, up) and free(above(Cart))",
                     "moved(Cart, up)", "a")
        b = one_rule("act=push(Cart, up) and colored(toward(Cart, up), 3)",
                     "teleported(Cart, origin)", "b")
        assert disjointness_reason(a, b, background=0) is not None


# ----------------------------------------------------------- the policy check

class TestExclusive:
    def test_rules_claiming_different_objects_never_conflict(self):
        """A0's cascade: identical guards, one Button and one Door.

        The naive reading of `exclusive` — all guards pairwise disjoint —
        rejects this correct manual.
        """
        a = one_rule("act=push(Cart, left) and colored(leftof(Cart), 7)",
                     "moved(Cart, left)", "press")
        b = one_rule("act=push(Cart, left) and colored(leftof(Cart), 7)",
                     "vanished(Door)", "opens")
        report = check_conflict([a, b], EXCLUSIVE)
        assert report.green and report.overlapping == []

    def test_an_undischarged_pair_raises_in_strict_mode(self):
        a = one_rule("act=push(Cart, up)", "moved(Cart, up)", "a")
        b = one_rule("act=push(Cart, up)", "teleported(Cart, origin)", "b")
        with pytest.raises(ConflictError) as exc:
            check_conflict([a, b], EXCLUSIVE)
        assert "a and b both claim Cart" in str(exc.value)
        assert "sound and incomplete" in str(exc.value)

    def test_non_strict_mode_reports_instead_of_raising(self):
        a = one_rule("act=push(Cart, up)", "moved(Cart, up)", "a")
        b = one_rule("act=push(Cart, up)", "teleported(Cart, origin)", "b")
        report = check_conflict([a, b], EXCLUSIVE, strict=False)
        assert not report.green
        assert any("not discharged" in w for w in report.warnings())


class TestPriority:
    def _pair(self):
        return (one_rule("act=push(Cart, up)", "moved(Cart, up)", "a"),
                one_rule("act=push(Cart, up)", "teleported(Cart, origin)", "b"))

    def test_a_ranked_collision_is_discharged(self):
        a, b = self._pair()
        sem = SemanticsSection(frame="persist", conflict="priority",
                               cascade="single_frame", priority=["a", "b"])
        report = check_conflict([a, b], sem)
        assert report.green and report.ordered == [("a", "b")]

    def test_an_unranked_collision_is_not(self):
        """`priority` claims the order is *total over colliding rules*."""
        a, b = self._pair()
        sem = SemanticsSection(frame="persist", conflict="priority",
                               cascade="single_frame", priority=["a", "other"])
        with pytest.raises(ConflictError) as exc:
            check_conflict([a, b], sem)
        assert "no ground rule for" in str(exc.value)

    def test_the_order_must_name_ground_rules(self):
        """After `forall` expansion a schema is one rule per value, so an order
        naming the schema ranks nothing that exists."""
        a, b = self._pair()
        sem = SemanticsSection(frame="persist", conflict="priority",
                               cascade="single_frame", priority=["a", "schema"])
        with pytest.raises(ConflictError) as exc:
            check_conflict([a, b], sem)
        assert "schema" in str(exc.value)


# ------------------------------------------------- the whole repo, pinned

def _manuals():
    return [
        ("peg", FIXTURES / "peg_theory.dsl", FIXTURES / "peg5_problem.json"),
        ("cart", FIXTURES / "cart_theory.dsl", FIXTURES / "cart_problem.json"),
        ("a0", REPO / "cold-start-a0/theory/theory.dsl",
         REPO / "cold-start-a0/artifacts/problem_a0-base.json"),
        ("a0-no-button", REPO / "cold-start-a0/theory/theory_no_button.dsl",
         REPO / "cold-start-a0/artifacts/problem_a0-no-button.json"),
        ("a2", REPO / "cold-start-a2/theory/theory.dsl",
         REPO / "cold-start-a2/theory/generated/problem.json"),
        ("a2-holed", REPO / "cold-start-a2/theory/theory_holed.dsl",
         REPO / "cold-start-a2/theory/generated_holed/problem.json"),
        ("a2-repaired", REPO / "cold-start-a2/theory/theory_repaired.dsl",
         REPO / "cold-start-a2/theory/generated_repaired/problem.json"),
    ]


def _status(dsl: Path, problem: Path) -> dict:
    """The same call `build_ir` makes, uniqueness context included.

    The first version of this helper omitted `uniq=`, so it exercised a path
    production never takes and reported peg as `conditional` long after the
    `unique` declaration had made it green. A harness that measures a different
    code path than the one that ships is worse than no harness: it goes on
    agreeing with a stale expectation.
    """
    ast = parse_theory(dsl.read_text(encoding="utf-8"))
    ir = build_ir(ast, load_problem(str(problem)))
    uniq = Uniqueness(ast, ir.problem)
    report = check_conflict(ir.rules, ir.semantics, ir.problem.background,
                            strict=False, uniq=uniq)
    ns: dict = {}
    exec(generate_python(ast, ir.problem), ns)
    if uniq:
        # A disjointness proof that rests on `unique` is only worth as much as
        # `unique` is, so the declaration is discharged before it is used.
        certify_uniqueness(ns, uniq, cell_universe(ir.problem))
    if report.green:
        return {"status": "green", "route": "guard analysis",
                "unique_fields": dict(uniq.unique_field)}
    report = certify_conflict(report, ns, ir.semantics, cell_universe(ir.problem))
    return report.swept


class TestInventory:
    """Every manual in the repo, with its status pinned.

    This is what stops the obligation from quietly becoming decorative again: a
    manual that stops discharging, or a *new* manual that never did, turns this
    red. The peg entry is a recorded gap (E-07), not an exemption — it asserts
    the exact condition, and it asserts that the unconditional sweep really does
    fail, so "conditional" can never silently decay into "green".
    """

    @pytest.mark.parametrize("name,dsl,problem", _manuals(),
                             ids=[m[0] for m in _manuals()])
    def test_every_manual_discharges_its_declared_conflict_policy(
            self, name, dsl, problem):
        if not dsl.exists() or not problem.exists():
            pytest.skip("%s is not generated" % dsl)
        swept = _status(dsl, problem)
        assert swept["status"] == "green", (
            "%s no longer discharges its declared conflict policy: %s"
            % (name, json.dumps(swept, ensure_ascii=False)))

    def test_peg_discharges_only_because_of_the_unique_declaration(self):
        """E-07, closed — and pinned to the reason it closed.

        Delete `unique` from the peg manual and this manual stops entailing
        its own `conflict exclusive`. Asserting the *mechanism* rather than
        just the green keeps that from being rediscovered the hard way.
        """
        ast = parse_theory((FIXTURES / "peg_theory.dsl").read_text(encoding="utf-8"))
        problem = load_problem(str(FIXTURES / "peg5_problem.json"))
        ir = build_ir(ast, problem)

        with_unique = check_conflict(ir.rules, ir.semantics, problem.background,
                                     strict=False,
                                     uniq=Uniqueness(ast, problem))
        assert with_unique.green

        without = check_conflict(ir.rules, ir.semantics, problem.background,
                                 strict=False, uniq=None)
        assert not without.green, (
            "the peg manual now discharges without `unique`, so either the "
            "manual changed or a new disjointness rule made E-07 moot — either "
            "way this test and the ledger entry need revisiting")
        assert len(without.undischarged) == 24

    def test_the_unique_declaration_is_proved_not_assumed(self):
        """`unique` restricts the state space, so it is itself an obligation.

        Both halves: true of the initial state, and preserved by `step`. The
        second is the one that matters — without it the declaration could hold
        at the start, rot one move later, and void every disjointness proof
        resting on it.
        """
        ast = parse_theory((FIXTURES / "peg_theory.dsl").read_text(encoding="utf-8"))
        problem = load_problem(str(FIXTURES / "peg5_problem.json"))
        ns: dict = {}
        exec(generate_python(ast, problem), ns)
        proof = certify_uniqueness(ns, Uniqueness(ast, problem),
                                   cell_universe(problem))
        assert proof["status"] == "proved"
        assert proof["obligations"] == ["initial", "preserved"]
        assert proof["well_formed_transitions_examined"] == 59560
        assert proof["fields"] == {"Peg": "pos"}

    def test_a_world_that_breaks_uniqueness_is_refused(self):
        """The negative control: the check must be capable of failing.

        A manual is free to declare `unique` on a field its rules do not in
        fact keep unique, and then every proof built on it is void. Here two
        pegs are placed on one cell in the level itself.
        """
        ast = parse_theory((FIXTURES / "peg_theory.dsl").read_text(encoding="utf-8"))
        doc = json.loads((FIXTURES / "peg5_problem.json").read_text(encoding="utf-8"))
        doc["objects"][1]["pos"] = doc["objects"][0]["pos"]
        from theory_compiler.problem import from_json
        problem = from_json(doc)
        ns: dict = {}
        exec(generate_python(ast, problem), ns)
        with pytest.raises(ConflictError) as exc:
            certify_uniqueness(ns, Uniqueness(ast, problem),
                               cell_universe(problem))
        assert "initial state" in str(exc.value)

    def test_the_conditional_route_still_exists_for_manuals_without_unique(self):
        """E-07 is closed for peg, not deleted from the tool.

        A manual that needs the condition and does not declare it still gets a
        named conditional discharge rather than a silent pass.
        """
        assert DISTINCT_POSITIONS in CONDITIONS
        assert CONDITIONS[DISTINCT_POSITIONS].startswith("no two live instances")
