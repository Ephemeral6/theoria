"""v0.3 — what `mentions` means, and the two defects that hung off it.

`CONTRACTS/dsl_grammar_v0.2.md` used the word `mentions` in the definition of
`frame persist` and never defined it. `a0-spike`'s ledger X-1 showed the three
available readings disagree and priced the wrong one at 376 transitions; X-5
showed `free(<obj>.pos)` was a question with only one possible answer, and
priced that at 52. This module pins the grammar half. The numbers themselves are
re-derived by `tools/probe_mentions.py` against the other track's world, which
is the only place ground truth lives.
"""

import subprocess
import sys
from pathlib import Path

import pytest

from theory_compiler.conflict import Uniqueness, disjointness_reason
from theory_compiler.generators.gen_markdown import generate_markdown
from theory_compiler.generators.gen_pddl import generate_pddl
from theory_compiler.generators.gen_python import (
    UnsupportedClause, generate_python,
)
from theory_compiler.ir import build_ir
from theory_compiler.parser.theory_parser import ParseError, parse_theory
from theory_compiler.problem import load_problem
from theory_compiler.writes import (
    DEFAULT_WRITE_SETS, WriteSets, WritesError, check_backend_agreement,
)

FIXTURES = Path(__file__).parent / "fixtures"
REPO = Path(__file__).resolve().parents[2]

HEAD = (
    "word_table:\n  board\n  object Cart { pos: Coord, color: Int }\n"
    "  object Door { pos: Coord, color: Int, present: Bool }\n"
    "semantics:\n  frame persist\n  conflict exclusive\n"
    "  cascade single_frame\n")
TAIL = "goal:\n  goal Cart.pos = (1, 1)\n"


def manual(events: str, rules: str) -> str:
    return HEAD + "events:\n  event %s\n" % events + "rules:\n" + rules + TAIL


# ------------------------------------------------------------------- the clause

class TestWritesClause:
    def test_it_parses_and_names_parameters(self):
        ast = parse_theory(manual(
            "slid(o, p, dir) writes {o, p} | stayed(o) writes {}",
            "  rule r\n    when act=push(Cart, up) then slid(Cart, Door, up)\n"))
        alts = {a.name: a for d in ast.events.events for a in d.alternatives}
        assert alts["slid"].writes == ["o", "p"]
        assert alts["stayed"].writes == []

    def test_an_absent_clause_is_not_an_empty_one(self):
        """`writes {}` is a claim; no clause at all is a deferral to the table.

        Collapsing them would make "this event writes nothing" and "nobody has
        said" the same sentence, which is the distinction the whole revision is
        about.
        """
        ast = parse_theory(manual(
            "moved(o, dir) | stayed(o) writes {}",
            "  rule r\n    when act=push(Cart, up) then moved(Cart, up)\n"))
        alts = {a.name: a for d in ast.events.events for a in d.alternatives}
        assert alts["moved"].writes is None
        assert alts["stayed"].writes == []

    def test_a_written_object_must_be_a_parameter(self):
        """X-1's second request, enforced.

        `writes {o, Player}` would let a manual keep an event whose signature
        does not name what it moves — legibly, but still not nameably. It would
        also make the write set depend on which instances the level supplies,
        and `conflict` is a claim about the domain.
        """
        with pytest.raises(ParseError) as exc:
            parse_theory(manual(
                "slid(o, dir) writes {o, Player}",
                "  rule r\n    when act=push(Cart, up) then slid(Cart, up)\n"))
        assert "not \nparameter" in str(exc.value).replace("'", "") or \
               "parameter" in str(exc.value)
        assert "slid(o, dir, Player)" in str(exc.value)

    def test_a_malformed_alternative_is_refused_not_skipped(self):
        """v0.2's parser skipped what it could not match. A `writes` clause with
        a typo would then have become an event with no declared write set —
        the guess this revision exists to forbid."""
        with pytest.raises(ParseError) as exc:
            parse_theory(manual(
                "moved(o, dir) wrties {o}",
                "  rule r\n    when act=push(Cart, up) then moved(Cart, up)\n"))
        assert "cannot read event alternative" in str(exc.value)


# ----------------------------------------------------------------- resolution

class TestResolution:
    def test_the_declaration_beats_the_table(self):
        ast = parse_theory(manual(
            "moved(o, dir) writes {}",
            "  rule r\n    when act=push(Cart, up) then moved(Cart, up)\n"))
        rule = ast.rules.rules[0]
        assert DEFAULT_WRITE_SETS[("moved", 2)] == (0,)
        assert WriteSets(ast).of_rule(rule) == set()

    def test_the_table_fills_a_silent_declaration(self):
        ast = parse_theory(manual(
            "moved(o, dir)",
            "  rule r\n    when act=push(Cart, up) then moved(Cart, up)\n"))
        assert WriteSets(ast).of_rule(ast.rules.rules[0]) == {"Cart"}

    def test_an_unknown_event_fails_closed(self):
        ast = parse_theory(manual(
            "dissolved(o, other, dir)",
            "  rule r\n    when act=push(Cart, up) then dissolved(Cart, Door, up)\n"))
        with pytest.raises(WritesError) as exc:
            WriteSets(ast).of_rule(ast.rules.rules[0])
        assert "has no write set" in str(exc.value)

    def test_stayed_writes_nothing(self):
        """The one default-table row that is not a transcription of
        `CLAIMED_ARGS`. An event whose compiled effect assigns nothing writes
        nothing; the old table had it claiming its argument."""
        assert DEFAULT_WRITE_SETS[("stayed", 1)] == ()

    def test_two_declarations_of_one_event_must_agree(self):
        source = manual(
            "moved(o, dir) writes {o}",
            "  rule r\n    when act=push(Cart, up) then moved(Cart, up)\n")
        source = source.replace(
            "  event moved(o, dir) writes {o}\n",
            "  event moved(o, dir) writes {o}\n  event moved(a, b) writes {}\n")
        with pytest.raises(WritesError) as exc:
            WriteSets(parse_theory(source))
        assert "different write sets" in str(exc.value)


# ------------------------------------------------------- the backend obligation

class TestBackendAgreement:
    def _rule(self):
        ast = parse_theory(manual(
            "moved(o, dir)",
            "  rule r\n    when act=push(Cart, up) then moved(Cart, up)\n"))
        return ast.rules.rules[0], WriteSets(ast)

    def test_agreement_passes(self):
        rule, writes = self._rule()
        check_backend_agreement(rule, ["Cart"], writes, "test")

    def test_an_undeclared_write_is_the_dangerous_direction(self):
        """The frame axiom promises the object is unchanged; the code changes
        it. That is X-1's 376 with the sign flipped."""
        rule, writes = self._rule()
        with pytest.raises(WritesError) as exc:
            check_backend_agreement(rule, ["Cart", "Door"], writes, "test")
        assert "frame persist" in str(exc.value)
        assert "Door" in str(exc.value)

    def test_a_missing_write_is_also_an_error(self):
        rule, writes = self._rule()
        with pytest.raises(WritesError) as exc:
            check_backend_agreement(rule, [], writes, "test")
        assert "does not assign Cart" in str(exc.value)

    def test_the_predictor_is_held_to_it_on_every_compile(self):
        """Not a separate pass a caller can forget: `generate_python` calls it
        for every rule, so the drift pin is the compile itself."""
        ast = parse_theory(manual(
            "moved(o, dir) writes {}",
            "  rule r\n    when act=push(Cart, up) then moved(Cart, up)\n"))
        problem = load_problem(str(FIXTURES / "cart_problem.json"))
        with pytest.raises(WritesError) as exc:
            generate_python(ast, problem)
        assert "gen_python" in str(exc.value)


# ------------------------------------------------------------- free, ledger X-5

FREE_MANUAL = (
    "word_table:\n  board\n  object Cart { pos: Coord, color: Int }\n"
    "semantics:\n  frame persist\n  conflict exclusive\n"
    "  cascade single_frame\n"
    "events:\n  event stayed(o) writes {}\n"
    "rules:\n  rule r\n    when act=push(Cart, up) and free(Cart.pos) "
    "then stayed(Cart)\n"
    "goal:\n  goal Cart.pos = (1, 1)\n")


class TestFreeOnAnObjectsOwnCell:
    def test_the_predictor_excludes_the_asker(self):
        ast = parse_theory(FREE_MANUAL)
        problem = load_problem(str(FIXTURES / "cart_problem.json"))
        source = generate_python(ast, problem)
        assert "_free_except(state, state.Cart_pos, ('Cart',))" in source, (
            "free(Cart.pos) must not compile to a test the Cart's own "
            "rendering makes unconditionally false (X-5)")

    def test_it_is_true_on_an_empty_cell_and_false_on_a_wall(self):
        ast = parse_theory(FREE_MANUAL)
        problem = load_problem(str(FIXTURES / "cart_problem.json"))
        namespace = {}
        exec(compile(generate_python(ast, problem), "<free>", "exec"), namespace)
        board = problem.board
        empty = next((r, c) for r, row in enumerate(board)
                     for c, v in enumerate(row) if v == problem.background)
        wall = next(((r, c) for r, row in enumerate(board)
                     for c, v in enumerate(row) if v != problem.background), None)
        State = namespace["State"]
        assert namespace["_free_except"](
            State(Cart_pos=empty, Cart_color=6), empty, ("Cart",)) is True
        if wall is not None:
            assert namespace["_free_except"](
                State(Cart_pos=wall, Cart_color=6), wall, ("Cart",)) is False

    def test_it_is_not_referentially_transparent_and_the_checker_knows(self):
        """`free(Cart.pos)` and `colored(Cart.pos, 2)` can both hold — the first
        lifts the Cart off the frame and the second does not. Reporting them
        *proved disjoint* would be a false proof in the one checker whose whole
        value is that its answers are proofs."""
        source = (HEAD + "events:\n  event stayed(o) writes {}\n" + "rules:\n"
                  "  rule a\n    when act=push(Cart, up) and free(Cart.pos) "
                  "then stayed(Cart)\n"
                  "  rule b\n    when act=push(Cart, up) and colored(Cart.pos, 2) "
                  "then stayed(Cart)\n" + TAIL)
        rules = parse_theory(source).rules.rules
        assert disjointness_reason(rules[0], rules[1]) is None

    def test_a_cell_named_without_an_object_still_contradicts_a_colour(self):
        """The transparent case must keep working, or the fix has cost a proof
        rather than removed a false one."""
        source = (HEAD + "events:\n  event stayed(o) writes {}\n" + "rules:\n"
                  "  rule a\n    when act=push(Cart, up) and free(above(Cart)) "
                  "then stayed(Cart)\n"
                  "  rule b\n    when act=push(Cart, up) and "
                  "colored(above(Cart), 3) then stayed(Cart)\n" + TAIL)
        rules = parse_theory(source).rules.rules
        assert disjointness_reason(rules[0], rules[1]) is not None

    def test_the_strips_form_refuses_it_rather_than_dropping_it(self):
        """`gen_pddl` keeps `free` as a predicate of a cell and withholds it
        from every cell an object holds, so a per-occurrence exclusion has no
        image there. v0.2 revision item 10: refuse, do not approximate."""
        ast = parse_theory(FREE_MANUAL)
        with pytest.raises(UnsupportedClause) as exc:
            generate_pddl(ast)
        assert "X-5" in str(exc.value)

    def test_the_human_form_does_not_say_the_opposite(self):
        ast = parse_theory(FREE_MANUAL)
        text = generate_markdown(ast)
        assert "is free (unoccupied)" not in text
        assert "legal empty one" in text


# ------------------------------------------------------- the migrated A0 manual

class TestSokoban2Fixture:
    def test_it_compiles_and_the_predictor_agrees_with_its_declaration(self):
        ast = parse_theory((FIXTURES / "sokoban2_theory.dsl")
                           .read_text(encoding="utf-8"))
        problem = load_problem(str(FIXTURES / "sokoban2_match_problem.json"))
        ir = build_ir(ast, problem)
        assert len(ir.rules) == 24, "six schemas grounded over four directions"
        source = generate_python(ast, problem)          # raises on disagreement
        assert "_effect_push2_up" in source

    def test_the_push_writes_both_objects(self):
        ast = parse_theory((FIXTURES / "sokoban2_theory.dsl")
                           .read_text(encoding="utf-8"))
        problem = load_problem(str(FIXTURES / "sokoban2_match_problem.json"))
        ir = build_ir(ast, problem)
        push = next(r for r in ir.rules if r.name.startswith("push2"))
        assert ir.writes.of_rule(push) == {"Box", "Player"}, (
            "the whole of X-1: a push moves the player, and the manual now "
            "says so in its own vocabulary")

    def test_the_blocked_rules_write_nothing(self):
        ast = parse_theory((FIXTURES / "sokoban2_theory.dsl")
                           .read_text(encoding="utf-8"))
        problem = load_problem(str(FIXTURES / "sokoban2_match_problem.json"))
        ir = build_ir(ast, problem)
        for rule in ir.rules:
            if rule.name.startswith("blocked_"):
                assert ir.writes.of_rule(rule) == set()

    def test_conflict_exclusive_is_discharged_by_guard_analysis_alone(self):
        """Route 1, executed rather than argued.

        `a0-spike/theory/theory.dsl`'s own `semantics:` comment claims this —
        *"free(c) 蕴含 c≠Box.pos，这一条就切开了 walk 与 push2"* — and no tool
        checked it. The rule that does is `_occupancy_terms`: an always-present
        object standing on a cell renders its own colour there, so `free(t)` and
        `<inst>.pos = t` contradict.

        It needs the **wide** reading of `slid` to matter at all. Under the
        narrow one `walk` and `push2` share no claimed object and the pair is
        never examined — ledger X-1's "read `slid` by its name and the sweep
        ranges over too few pairs", here as a passing test instead of a hazard.
        """
        from theory_compiler.conflict import check_conflict
        ast = parse_theory((FIXTURES / "sokoban2_theory.dsl")
                           .read_text(encoding="utf-8"))
        problem = load_problem(str(FIXTURES / "sokoban2_match_problem.json"))
        ir = build_ir(ast, problem)
        report = check_conflict(ir.rules, ast.semantics, problem.background,
                                strict=False, uniq=Uniqueness(ast, problem),
                                writes=ir.writes)
        assert report.undischarged == []
        assert len(report.overlapping) == 28
        walk_push = [why for a, b, why in report.disjoint
                     if a.startswith("walk_") and b.startswith("push2_")
                     and a.split("_")[-1] == b.split("_")[-1]]
        assert len(walk_push) == 4
        assert all("always on the frame" in why for why in walk_push)

    def test_exactly_one_rule_fires_on_a_sample(self):
        """Totality and firing-exclusivity, on a stratified sample. The full
        47,040-pair sweep is `tools/probe_mentions.py`; this is the part fast
        enough to run on every commit."""
        ast = parse_theory((FIXTURES / "sokoban2_theory.dsl")
                           .read_text(encoding="utf-8"))
        problem = load_problem(str(FIXTURES / "sokoban2_match_problem.json"))
        namespace = {}
        exec(compile(generate_python(ast, problem), "<sokoban2>", "exec"),
             namespace)
        State = namespace["State"]
        seen = 0
        for pr in range(7):
            for pc in range(7):
                for direction in ("up", "down", "left", "right"):
                    for box in ((3, 3), (1, 5), (4, 4)):     # (1,5) is a wall
                        if (pr, pc) == box:
                            continue
                        state = State(Box_pos=box, Player_pos=(pr, pc))
                        fired = [name for name, guard, _e, _o
                                 in namespace["RULES"]
                                 if guard(state.copy(),
                                          ("move", "Player", direction))]
                        assert len(fired) == 1, (
                            "player %r box %r %s fired %r"
                            % ((pr, pc), box, direction, fired))
                        seen += 1
        assert seen > 500


# ------------------------------------------------------------- additions only

V02_MANUALS = [
    ("peg_theory.dsl", "peg5_problem.json"),
    ("peg4_theory.dsl", "peg4_problem.json"),
    ("cart_theory.dsl", "cart_problem.json"),
]


class TestAdditionsOnly:
    @pytest.mark.parametrize("dsl,problem", V02_MANUALS)
    def test_a_v02_manual_still_compiles_untouched(self, dsl, problem):
        ast = parse_theory((FIXTURES / dsl).read_text(encoding="utf-8"))
        generate_python(ast, load_problem(str(FIXTURES / problem)))

    def test_and_is_told_where_its_write_sets_came_from(self):
        """The default table is a cross-world table holding a per-world fact.
        v0.3 keeps it for compatibility and refuses to keep it quiet."""
        ast = parse_theory((FIXTURES / "peg_theory.dsl")
                           .read_text(encoding="utf-8"))
        ir = build_ir(ast, load_problem(str(FIXTURES / "peg5_problem.json")),
                      check_conflicts=False)
        assert any("default table" in w for w in ir.warnings)


# ------------------------------------------ the obligation, now met and checked

def test_gen_pddl_meets_the_backend_obligation_on_a0():
    """The pin this replaces (`TestBackendObligationShortfall`) recorded, by
    name, that `gen_pddl` compiled three A0 rules to `:effect (and (and))` and
    two more to an undeclared `?dest`. Its own docstring said: the day
    `gen_pddl` grows the events, this test goes red and gets deleted. That day
    came with the 2026-07-31 repair; what stands here instead is the positive
    obligation — the A0 manual's PDDL form parses under the track's own STRIPS
    reader, which refuses empty effects and unbound variables outright.
    """
    from theory_compiler import strips

    path = REPO / "cold-start-a0" / "theory" / "theory.dsl"
    if not path.exists():
        pytest.skip("cold-start-a0 is not in this checkout")
    domain, _problem = generate_pddl(
        parse_theory(path.read_text(encoding="utf-8")))
    _name, _arities, _types, schemas = strips.parse_domain(domain)
    # 7 rules, 6 actions: press_left and door_opens_left share a guard and are
    # one transition (`cascade single_frame`), so they fold into one action.
    assert len(schemas) == 6
    for schema in schemas:
        assert schema.pre, schema.name
        assert schema.add or schema.dele, schema.name


# --------------------------------------------------------------- the two numbers

@pytest.mark.slow
def test_the_probe_reproduces_376_and_52_and_drives_both_to_zero():
    """The end-to-end claim, run against the other track's world.

    Slow (47,040 pairs × six sweeps) and it needs `a0-spike`, so it is marked
    and skips rather than failing when the ground truth is absent — a green
    result with nothing to grade against would be worth less than a skip.
    """
    if not (REPO / "a0-spike" / "world" / "sokoban2.py").exists():
        pytest.skip("a0-spike/ is not in this checkout; no ground truth")
    result = subprocess.run(
        [sys.executable, "-m", "tools.probe_mentions"],
        cwd=str(REPO / "theory-compiler"), capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "376 / 39960" in result.stdout
    assert "52 /  7080" in result.stdout
    assert "0 / 47040" in result.stdout
