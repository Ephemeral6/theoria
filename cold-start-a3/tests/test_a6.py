"""A6, as assertions — including the ones that say the result is smaller than it looks.

`tests/test_transfer.py` is the model: a reader who does not believe the report
runs the suite instead of reading it.  Three groups here:

* **the claim** — the push manual wins a world from another track's factory that
  it has never seen, having written no clause and run no engine;
* **the controls** — A3's two negative controls are still caught through this
  protocol, and the pack's own hashes and fingerprint refuse before an action is
  spent;
* **the limit** — `test_a_green_carry_is_about_the_path_not_the_world`, which
  asserts that a green end-to-end run was obtained on a world the manual is
  *wrong* about.  It is written as a passing test rather than a caveat because a
  caveat in prose is not checked when the code changes under it.
"""

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import pytest  # noqa: E402

import _bootstrap  # noqa: F401,E402

RUN = os.path.join(HERE, "runs", "20260728T1800Z-A6-transfer-protocol")
PACKS = os.path.join(RUN, "packs")
GENERATED = os.path.join(RUN, "generated")


def _acceptance():
    path = os.path.join(RUN, "a6_acceptance.json")
    if not os.path.exists(path):
        pytest.skip("a6_acceptance.json absent — run `python run_a6.py` first")
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _arm(name):
    for row in _acceptance()["arms"]:
        if row["arm"] == name:
            return row
    raise AssertionError("no arm %r in the acceptance artefact" % name)


# ------------------------------------------------------------------- the claim

def test_the_manual_wins_a_world_from_another_track_it_has_never_seen():
    """The item's acceptance, in one assertion.

    `t1-push-corridor` shares a mechanism family with the world the manual was
    theorized from and shares no layout, no grid size, no start cell and no
    goal — `worldgen`'s own `INDEX.json` calls the pair "same mechanism,
    dead-end corridor instead of an open room".
    """
    row = _arm("transfer_corridor")
    assert row["outcome"] == "win"
    assert row["static_certify_green"] is True
    assert row["plan_status"] == "SAT"
    assert row["replay_certify_green"] is True


def test_the_transfer_wrote_no_clause_and_ran_no_engine():
    """C3's cost claim, read off the meter rather than off the prose."""
    row = _arm("transfer_corridor")
    for field in ("theorize_rounds", "dsl_clauses_written",
                  "candidates_adjudicated", "engine_stages"):
        assert row[field] == 0, "%s == %s" % (field, row[field])


def test_the_transfer_planned_before_spending_an_action():
    """One frame in, a whole plan out, nothing spent to get there."""
    cost = _arm("transfer_corridor")["cost_to_first_plan"]
    assert cost["world_actions"] == 0
    assert cost["world_frames"] == 1


def test_both_push_worlds_were_solved_in_the_optimal_number_of_actions():
    """`worldgen`'s catalogue puts the optimum at 5 for both."""
    for arm in ("source_open", "transfer_corridor"):
        assert _arm(arm)["world_actions"] == 5, arm


def test_the_protocol_does_not_break_a3s_own_result():
    assert _arm("a3_l2_positive")["outcome"] == "win"
    assert _arm("a3_l2_positive")["replay_certify_green"] is True


# ---------------------------------------------------------------- the controls

@pytest.mark.parametrize("arm", ("a3_l2_oneway", "a3_l2_rewired"))
def test_a3s_negative_controls_are_still_caught_through_the_new_protocol(arm):
    row = _arm(arm)
    assert row["outcome"] != "win"
    assert row["replay_certify_green"] is False
    assert row["theorize_triggered"] is True


@pytest.mark.parametrize("arm", ("a3_l2_oneway", "a3_l2_rewired"))
def test_neither_negative_control_claimed_a_win(arm):
    row = _arm(arm)
    assert not (row["outcome"] == "win" and row["replay_certify_green"] is True)


@pytest.mark.parametrize("arm", ("a3_l2_oneway", "a3_l2_rewired"))
def test_the_board_still_cannot_reveal_a_transition_function_edit(arm):
    """A3's honest limit, unchanged by the new protocol.

    Both controls edit the transition function and neither touches a pixel, so
    the cheap static layer is green on both and the catch happens at replay —
    after the actions are spent.  Carrying this across is the point: a protocol
    that reported it differently would be reporting a different check.
    """
    assert _arm(arm)["static_certify_green"] is True


def test_tampering_with_a_carried_book_stops_the_run_before_frame_one():
    row = _arm("tampered_books")
    assert row["outcome"] == "pack_tampered"
    assert row["world_actions"] == 0
    assert row["world_frames"] == 0


def test_a_drifted_dependency_fingerprint_refuses():
    """The fingerprint has a reader, which is the only thing that makes it a check.

    `monitor/inbox/20260728T082700Z-W-1521` reports that every manifest in this
    repository records an upstream hash and *nothing ever compares two of them*.
    Here the comparison stops the run.
    """
    control = _acceptance()["fingerprint_control"]
    assert control["refused"] is True
    assert control["file_drifted"]


def test_a_wrong_mechanism_world_spends_no_actions():
    """`t1-switch-latch` under the push manual: UNSAT, and nothing spent."""
    row = _arm("wrong_world_t1_switch_latch")
    assert row["world_actions"] == 0
    assert row["outcome"] == "no_plan"


# -------------------------------------------------------------------- the limit

def test_a_green_carry_is_about_the_path_not_the_world():
    """The most important negative result here, and it is a passing test.

    The push manual carried onto `t1-cycler-gate` — whose colour 2 is a cycler
    that recolours when bumped, not a block that slides — returns `win`, replay
    green, zero unexplained pixels.  The planner routed around the mechanism the
    manual is wrong about, so every transition the manual was asked about was one
    it happens to get right.

    Both halves are asserted together on purpose.  Either alone is misleading:
    the first without the second reads as "the manual generalises further than
    claimed", the second without the first as "the protocol catches wrong
    manuals".  Neither is true.
    """
    row = _arm("wrong_world_t1_cycler_gate")
    assert row["outcome"] == "win"
    assert row["replay_certify_green"] is True

    off = _acceptance()["off_route_control"]
    assert off["world"] == "t1-cycler-gate"
    assert off["green"] is False
    assert off["anomaly_count"] > 0
    assert "render_mismatch" in off["anomaly_kinds"]


def test_the_acceptance_artefact_reports_the_limit_rather_than_hiding_it():
    """A verdict file that only listed passes would be the wrong artefact."""
    acceptance = _acceptance()["acceptance"]
    assert acceptance["green_carry_can_be_earned_on_a_wrong_world"] is True
    assert _acceptance()["all_green"] is True


# ---------------------------------------------------------------- the pack format

def test_the_lean_form_is_withheld_from_the_push_pack():
    """D-A6-002: a Lean certificate here would be green and about the wrong thing.

    `gen_lean_a0.build_axes` admits only non-mover `_colour`/`_present` fields as
    state axes, so a Block's *position* is not in the Lean state type.  The pack
    declares the form unemittable and the protocol emits no file, rather than
    emitting one that proves a projection of the manual.
    """
    with open(os.path.join(PACKS, "push-v1", "PACK.json"), encoding="utf-8") as h:
        manifest = json.load(h)
    assert "lean" not in manifest["requires"]["forms"]
    assert "lean" in manifest["requires"]["forms_withheld"]
    assert not os.path.exists(os.path.join(GENERATED, "transfer_corridor",
                                           "theory.lean"))


def test_the_a3_pack_still_gets_its_lean_form():
    """The withholding is a property of the manual, not a blanket refusal."""
    with open(os.path.join(PACKS, "a3-v1", "PACK.json"), encoding="utf-8") as h:
        manifest = json.load(h)
    assert "lean" in manifest["requires"]["forms"]


def test_a3s_playbook_does_not_parse_and_the_pack_says_so():
    """D-A6-003, pinned so it cannot be quietly "fixed" by a lenient parser.

    A3's `theory/playbook.dsl` line 81 writes `[ev: 2/2 levels, n=2 — indicative
    only]` where `_parse_prefer` accepts only `[ev: k/n]`.  A3 never found out
    because A3 compiles its domain and never hands its playbook to a parser —
    "carrying the two books" was carrying one book and a file.  The pack carries
    what parses and names, by line, what it left behind.
    """
    with open(os.path.join(PACKS, "a3-v1", "PACK.json"), encoding="utf-8") as h:
        manifest = json.load(h)
    playbook = manifest["books"]["playbook"]
    assert playbook["parsed"] == "partial"
    assert [u["line"] for u in playbook["entries_unparsed"]] == [81]
    assert "unparsed:line 81" in playbook["entries_left_behind"]


def test_the_push_pack_carries_the_theorem_and_leaves_the_heuristic():
    """Only theorem-grade entries travel; `[admissible: none]` is a refusal."""
    with open(os.path.join(PACKS, "push-v1", "PACK.json"), encoding="utf-8") as h:
        manifest = json.load(h)
    assert manifest["books"]["playbook"]["entries_carried"] == 1
    assert "heuristic:shove_debt" in \
        manifest["books"]["playbook"]["entries_left_behind"]
    assert manifest["books"]["domain"]["laws"] == 3


def test_the_pack_holds_no_coordinate_of_the_level():
    """The domain/problem split, checked on the file rather than asserted.

    A carried domain that named a cell would be a carried *level*.  `goal_cell`
    is in `supplied_constants` — declared as something a receiver must be handed
    — and nothing in the manual is a coordinate.
    """
    with open(os.path.join(PACKS, "push-v1", "domain.dsl"), encoding="utf-8") as h:
        body = "\n".join(line.split("#", 1)[0] for line in h.read().splitlines())
    import re
    assert re.search(r"\(\s*\d+\s*,\s*\d+\s*\)", body) is None, \
        "the carried manual names a coordinate"
    with open(os.path.join(PACKS, "push-v1", "PACK.json"), encoding="utf-8") as h:
        manifest = json.load(h)
    assert manifest["requires"]["supplied_constants"] == ["goal_cell"]
    assert manifest["requires"]["goal_in_domain"] is False


# ----------------------------------------------------- the patched planning form

@pytest.mark.parametrize("arm", ("source_open", "transfer_corridor"))
def test_the_patched_pddl_is_readable_by_the_planner_that_reads_it(arm):
    """D-A6-001's rewrite, checked by its actual consumer.

    Until 2026-07-29 the rewrite dropped the domain's closing paren every time —
    the final action in a push manual is always a deleted `block_*` rule, and the
    lone `)` that ends `(define …)` lives inside its text.  It surfaced as
    `PddlError: unbalanced parentheses` from four frames inside the planner.  A
    balance check now guards the writer; this runs the reader.
    """
    from engines.fd_adapter.pddl import parse_domain, parse_problem
    out = os.path.join(GENERATED, arm)
    with open(os.path.join(out, "domain.pddl"), encoding="utf-8") as handle:
        domain = parse_domain(handle.read())
    with open(os.path.join(out, "problem.pddl"), encoding="utf-8") as handle:
        parse_problem(handle.read())
    names = {a.name if hasattr(a, "name") else a["name"]
             for a in (domain.actions if hasattr(domain, "actions") else domain["actions"])}
    assert not any(n.startswith("block-") for n in names), \
        "a duplicate mover-move action survived the rewrite: %s" % sorted(names)
    assert any(n.startswith("shove-") for n in names), sorted(names)


# --------------------------------------------------------------- the scoring pass

def _scoring():
    path = os.path.join(RUN, "scoring_push_manual.json")
    if not os.path.exists(path):
        pytest.skip("scoring_push_manual.json absent — run `python -m a6carry.score`")
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def test_the_manual_agrees_with_both_worlds_on_every_reachable_transition():
    """The exhaustive answer to `test_a_green_carry_is_about_the_path_not_the_world`.

    A carry certifies the path it took.  This certifies the whole space: every
    reachable state of both worlds crossed with all four actions, which is what
    "the manual is right about this world" actually requires.
    """
    scoring = _scoring()
    assert scoring["verdict"]["all_transitions_agree"] is True
    assert scoring["verdict"]["checked_and_wrong"] == []
    assert scoring["totals"]["transitions_checked"] == 256
    assert scoring["totals"]["disagreements"] == 0


def test_two_symmetry_clauses_were_never_exercised_and_are_not_counted_as_right():
    """The result is smaller than "zero disagreements" sounds, and stays smaller.

    Six clauses carry `ev: symmetry` — an explicit generalisation from the one
    direction the source world's explorer could witness.  Four of them were put
    to the test, by **one transition each**, all in `t1-push-open`.  Two were
    never put to the test at all: neither world lets the agent reach the block's
    right-hand side, so `shove_left` and `block_left` are unrefuted and
    unvindicated.

    Zero disagreements over zero transitions is not evidence, and this asserts
    that the artefact keeps the two lists apart so nobody can sum them.
    """
    verdict = _scoring()["verdict"]
    assert sorted(verdict["never_checked"]) == ["block_left", "shove_left"]
    assert sorted(verdict["checked_and_right"]) == [
        "block_down", "block_up", "shove_down", "shove_up"]
    for clause in verdict["never_checked"]:
        assert verdict["exercising_transitions"][clause] == 0
        assert clause not in verdict["checked_and_right"]
    # The four that were checked were checked thinly, and the artefact says so.
    for clause in verdict["checked_and_right"]:
        assert verdict["exercising_transitions"][clause] == 1


def test_the_scorer_reads_the_headers_claim_rather_than_remembering_it():
    """A constant recording what another file says is a copy that rots on write.

    It did: the scorer hardcoded the header's "eight", the header was corrected
    to six, and the artefact went on reporting a disagreement with a sentence
    that no longer existed.  Both numbers are now read at run time.
    """
    header = _scoring()["verdict"]["header_clause_count"]
    assert header["agrees"] is True
    assert header["claimed_by_header"] == header["counted_in_file"] == 6

    from a6carry import score
    with open(os.path.join(HERE, "theory", "push", "domain.dsl"),
              encoding="utf-8") as handle:
        text = handle.read()
    assert score.header_symmetry_claim(text)[0] == 6
    flipped = text.replace("Six of the twelve", "Eight of the twelve")
    assert score.header_symmetry_claim(flipped)[0] == 8


# ------------------------------------------------------------------ determinism

def test_the_acceptance_artefact_is_byte_reproducible():
    """Determinism is a requirement here, not a nicety.

    Against a fixed tree only: the artefact embeds the dependency fingerprint,
    so it is *supposed* to change when an upstream file changes.  That is the
    check, not a determinism failure.
    """
    path = os.path.join(RUN, "a6_acceptance.json")
    with open(path, "rb") as handle:
        before = handle.read()
    result = subprocess.run([sys.executable, "run_a6.py"], cwd=HERE,
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stdout[-2000:] + result.stderr[-2000:]
    with open(path, "rb") as handle:
        assert handle.read() == before
