"""The rechecker: the language, the obligations, the two acceptance runs, the
forgeries, and the anchors that say the rule sets are the worlds they name.

One rule governs this file and is worth stating: **nothing here imports
`engines`**.  If a test needed the engine to say what the answer is, the
independence the whole package is for would be gone at the point it is measured.
The engines' own numbers reach these tests only as literals -- transcribed from
`STATUS.md`, from `fixtures/peg4.py`'s hand-verified docstring, and from the
Lean file `cold-start-a2` shipped -- which is exactly how an independent referee
gets them.
"""

import copy
import hashlib
import json
import os

import pytest

from recheck import anchors, build_cases, forgeries, verify_all
from recheck.certificate import (
    CertificateError,
    certificate_from_spec,
    load_certificate,
)
from recheck.expr import ExprError
from recheck.ruleset import RuleSetError, load_ruleset, ruleset_from_spec
from recheck.verify import (
    ACCEPT,
    INCONSISTENT,
    REJECT,
    reachable_states,
    recheck,
    shortest_plan,
)

CASES = build_cases.CASES_DIR


def rules(name):
    return load_ruleset(os.path.join(CASES, "%s.rules.json" % name))


def cert(name):
    return load_certificate(os.path.join(CASES, "%s.cert.json" % name))


def spec(name, suffix):
    with open(os.path.join(CASES, "%s.%s.json" % (name, suffix)),
              "r", encoding="utf-8") as handle:
        return json.load(handle)


# ------------------------------------------------------- the two acceptance runs

def test_peg_0111_invariant_is_accepted():
    """M9's acceptance line, rechecked without ic3_pdr or its own checker."""
    verdict = recheck(rules("peg4-0111"), cert("peg4-0111-ic3"))
    assert verdict.verdict == ACCEPT
    assert verdict.conditions["inv_init"]
    assert verdict.conditions["inv_closed"]
    assert verdict.conditions["goal_break"]
    assert verdict.stats["n_states"] == 16
    assert verdict.search["goal_reachable"] is False


def test_a2_false_theorem_is_accepted_against_the_manual_it_is_true_of():
    """Agreement with Lean, which is the only way the rejection below means much.

    `generated_holed/theory.lean` proves this invariant closed under the holed
    manual's `step`, by `decide`, with an empty axiom list.  A rechecker that
    rejected it here would not be strict; it would be broken.
    """
    verdict = recheck(rules("a2-holed"), cert("a2-right-room-locked"))
    assert verdict.verdict == ACCEPT
    assert verdict.stats["n_states"] == 148
    assert verdict.search["goal_reachable"] is False


def test_a2_false_theorem_is_rejected_against_the_world():
    """The acceptance line this item exists for.

    The same certificate, one rule apart.  It must fail `inv_closed`, and the
    witness must be the teleport: the Cart at the Door cell, pushed down onto
    the colour-3 portal, landing in the right room where the weight is 1.
    """
    verdict = recheck(rules("a2-world"), cert("a2-right-room-locked"))
    assert verdict.verdict == REJECT
    assert verdict.conditions["inv_closed"] is False
    assert verdict.conditions["inv_init"] is True
    assert verdict.conditions["goal_break"] is True

    witnesses = verdict.witnesses["inv_closed"]
    assert witnesses, "a rejection with no witness is an assertion, not a check"
    assert all("cart=6,4" in w and "-down->" in w and "cart=7,6" in w
               for w in witnesses)

    # And the claim itself is false, found by a search that shares nothing with
    # the three conditions.  A2's own refutation is 18 actions long.
    assert verdict.search["goal_reachable"] is True
    assert len(verdict.search["witness_plan"]) == 18


def test_the_two_a2_rulesets_differ_by_exactly_the_teleport_rule():
    world = spec("a2-world", "rules")
    holed = spec("a2-holed", "rules")
    names = lambda s: [rule["name"] for rule in s["rules"]]
    assert set(names(world)) - set(names(holed)) == {"teleport_down"}
    assert set(names(holed)) - set(names(world)) == set()
    for key in ("variables", "actions", "tables", "defs", "init", "goal"):
        assert world[key] == holed[key], key


# ------------------------------------------------------ the deadlock certificates

@pytest.mark.parametrize("level", ["sokoban-ringstuck", "sokoban-open4far"])
def test_every_deadlock_theorem_rechecks(level):
    ruleset = rules(level)
    names = sorted(name for name in os.listdir(CASES)
                   if name.startswith(level + "-dead-"))
    assert names
    for filename in names:
        verdict = recheck(ruleset, load_certificate(os.path.join(CASES, filename)))
        assert verdict.verdict == ACCEPT, "%s: %s" % (filename, verdict.report())
        assert verdict.conditions["region_nonempty"]
        assert verdict.conditions["region_closed"]
        assert verdict.conditions["goal_break"]


def test_the_deadlock_count_matches_what_m9_reported():
    """STATUS.md: 16 theorems on open4far, 2 on ringstuck."""
    counted = {}
    for filename in os.listdir(CASES):
        if "-dead-" not in filename:
            continue
        counted.setdefault(filename.split("-dead-")[0], 0)
        counted[filename.split("-dead-")[0]] += 1
    assert counted == {"sokoban-open4far": 16, "sokoban-ringstuck": 2}


# ------------------------------------------------ the pagoda certificates (E6)

PAGODA = tuple(build_cases.PAGODA_CLAIMS)


@pytest.mark.parametrize("name,ruleset_name,weights,bound,document", PAGODA)
def test_every_pagoda_certificate_rechecks(name, ruleset_name, weights, bound, document):
    """lp_potential's three exported certificates, re-derived from the rules.

    The move set is grounded from the declared geometry.  The producer's own
    `obligations` block -- which lists every move instance with its delta
    already evaluated -- is refused as input by the schema, so a document that
    omitted an inconvenient instance would gain nothing here.
    """
    verdict = recheck(rules(ruleset_name), cert(name))
    assert verdict.verdict == ACCEPT, verdict.report()
    assert verdict.conditions["potential_init"]
    assert verdict.conditions["potential_nonincreasing"]
    assert verdict.conditions["goal_break"]
    assert verdict.stats["n_raising_transitions"] == 0
    assert verdict.stats["potential_bound"] == bound
    assert verdict.stats["n_states"] == 2 ** len(weights)
    # The second opinion agrees, from a search sharing nothing with the above.
    assert verdict.search["goal_reachable"] is False


@pytest.mark.parametrize("name,ruleset_name,weights,bound,document", PAGODA)
def test_every_pagoda_case_agrees_with_the_document_it_was_transcribed_from(
        name, ruleset_name, weights, bound, document):
    """The differential against `interop/certificates/`, which is read, not imported.

    Four numbers are transcribed into `build_cases`; the start state, the goal
    states and the move set are re-derived, and this is where the two are
    compared.  It is also the only place the producer's witness list is looked
    at, and a disagreement here would be a transcription finding rather than a
    verdict.
    """
    report = anchors.pagoda_differential(rules(ruleset_name), cert(name), document)
    assert report["agrees"], report
    assert report["n_moves_derived"] == report["n_moves_listed"] > 0
    assert report["replay_mismatches"] == []
    assert list(weights) == report["document_weights"]


def test_the_potential_obligation_is_quantified_over_moves_legal_from_the_region():
    """The defect the salvaged draft had, kept as an executable exhibit.

    `keyed-gate`'s only potential-raising move needs both keys, and any state
    holding both is already over the bound -- so the move is legal from nowhere
    the invariant admits, and the certificate is inductive.  A checker that
    reads `delta > 0` off the geometry, as the draft did, rejects it.
    """
    ruleset, certificate = rules("keyed-gate"), cert("keyed-gate-pagoda")
    verdict = recheck(ruleset, certificate)
    assert verdict.verdict == ACCEPT, verdict.report()
    assert verdict.stats["n_raising_transitions"] == 0
    assert verdict.search["goal_reachable"] is False

    # ... and the stronger check really would have rejected it: over the whole
    # product, rather than over the region, a move does raise the potential.
    potential = certificate.potential(ruleset)
    states, rows = ruleset.states(), ruleset.transitions()
    raising = [
        "%s -%s-> %s" % (ruleset.render_state(states[i]), action,
                         ruleset.render_state(states[rows[i][a]]))
        for i in range(len(states))
        for a, action in enumerate(ruleset.actions)
        if rows[i][a] >= 0 and potential(states[rows[i][a]]) > potential(states[i])
    ]
    assert raising, "the exhibit is empty unless something raises the potential"
    assert all(potential(states[i]) > certificate.bound
               for i in range(len(states))
               for a in range(len(ruleset.actions))
               if rows[i][a] >= 0 and potential(states[rows[i][a]]) > potential(states[i]))


def test_a_perturbed_weight_is_caught_by_the_potential_obligation():
    """The tamper `interop`'s own test performs, against this checker instead."""
    payload = spec("peg4-1110-pagoda", "cert")
    payload.pop("ruleset")
    payload["weights"]["pos3"] = 5
    verdict = recheck(rules("peg4-1110"), certificate_from_spec(payload))
    assert verdict.verdict == REJECT
    assert verdict.conditions["potential_nonincreasing"] is False
    assert verdict.conditions["potential_init"] is True
    assert verdict.conditions["goal_break"] is True
    assert verdict.witnesses["potential_nonincreasing"], "a rejection needs a witness"
    assert any("raises the potential" in w
               for w in verdict.witnesses["potential_nonincreasing"])


def test_a_goal_sitting_exactly_on_the_bound_does_not_break_it():
    """`potential(goal) > bound` is strict, and `1001` is one jump away."""
    payload = spec("peg4-1110", "rules")
    payload["goal"] = ["and",
                       ["=", ["var", "pos0"], ["lit", 1]],
                       ["=", ["var", "pos1"], ["lit", 0]],
                       ["=", ["var", "pos2"], ["lit", 0]],
                       ["=", ["var", "pos3"], ["lit", 1]]]
    unbound = spec("peg4-1110-pagoda", "cert")
    unbound.pop("ruleset")
    verdict = recheck(ruleset_from_spec(payload), certificate_from_spec(unbound))
    assert verdict.verdict == REJECT
    assert verdict.conditions["goal_break"] is False
    assert verdict.search["goal_reachable"] is True
    assert len(verdict.search["witness_plan"]) == 1


def test_a_pagoda_offered_for_a_solvable_start_fails_where_the_world_starts():
    payload = spec("peg4-1110-pagoda", "cert")
    payload.pop("ruleset")
    verdict = recheck(rules("peg4-1101"), certificate_from_spec(payload))
    assert verdict.verdict == REJECT
    assert verdict.conditions["potential_init"] is False
    assert verdict.search["goal_reachable"] is True


def test_a_pagoda_certificate_may_not_carry_its_producers_obligations():
    """`certificate_export.py::verify` trusts that list; nothing here may.

    A document that omits a move instance from it passes that checker, so the
    block is refused at load rather than ignored -- an ignored key would let the
    same document in and leave a reader unsure which checker had run.
    """
    payload = spec("peg4-1110-pagoda", "cert")
    payload["obligations"] = {"inv_closed": {"holds": True, "witnesses": []}}
    with pytest.raises(CertificateError) as caught:
        certificate_from_spec(payload)
    assert "obligations" in str(caught.value)


@pytest.mark.parametrize("key,value", [
    ("predicate", ["and"]),
    ("tables", {"w": {"arity": 1, "entries": [[0, 0]]}}),
    ("defs", [{"name": "f", "params": [], "body": ["and"]}]),
])
def test_a_pagoda_certificate_carries_weights_and_nothing_else(key, value):
    """Two sets of states and one verdict, or a key nothing reads.

    A predicate alongside the weights could be checked on one and claimed about
    the other; a table or a def has no predicate to appear in, so it would sit
    in the file unread -- which is where a blind spot starts.
    """
    payload = spec("peg4-1110-pagoda", "cert")
    payload[key] = value
    with pytest.raises(CertificateError) as caught:
        certificate_from_spec(payload)
    assert key in str(caught.value)


def test_a_predicate_certificate_may_not_carry_weights():
    """The split runs both ways, or a kind could be chosen after the fact."""
    for key, value in (("weights", {"pos1": 1}), ("bound", 0), ("occupied", 1)):
        payload = spec("peg4-0111-ic3", "cert")
        payload[key] = value
        with pytest.raises(CertificateError) as caught:
            certificate_from_spec(payload)
        assert key in str(caught.value)


def test_a_weight_on_a_value_the_world_cannot_hold_is_refused():
    """`occupied: 2` on a 0/1 board makes the potential constant, and constant
    potentials satisfy every closure obligation there is."""
    payload = spec("peg4-1110-pagoda", "cert")
    payload.pop("ruleset")
    payload["occupied"] = 2
    verdict = recheck(rules("peg4-1110"), certificate_from_spec(payload))
    assert verdict.verdict == REJECT
    assert verdict.conditions["predicate_wellformed"] is False


def test_a_weight_must_be_an_integer():
    payload = spec("peg4-1110-pagoda", "cert")
    payload["weights"]["pos0"] = -0.5
    with pytest.raises(CertificateError) as caught:
        certificate_from_spec(payload)
    assert "integer" in str(caught.value)


def test_the_potential_counters_are_not_shared_with_the_other_kinds():
    """One field per thing counted.

    The draft this was salvaged from reused a single `n_transitions_checked`
    across two certificate schemas, where it meant move instances in one and
    legal transitions in the other; a reader of the report could not tell which
    number they had.
    """
    pagoda = recheck(rules("peg4-1110"), cert("peg4-1110-pagoda"))
    invariant = recheck(rules("peg4-0111"), cert("peg4-0111-ic3"))
    assert "n_potential_checks" in pagoda.stats
    assert "n_raising_transitions" in pagoda.stats
    assert "n_potential_checks" not in invariant.stats
    assert "n_raising_transitions" not in invariant.stats
    # and it counts what its name says: one per action out of each region state
    assert pagoda.stats["n_potential_checks"] == (
        pagoda.stats["n_satisfying"] * len(rules("peg4-1110").actions))


# ---------------------------------------------------------------- the anchors

def test_peg_reachability_matches_the_hand_verified_docstring():
    """fixtures/peg4.py argues these four by exhaustive expansion, by hand."""
    for start, optimum in (("1110", None), ("0111", None),
                           ("1011", None), ("1101", 2)):
        plan = shortest_plan(rules("peg4-%s" % start))
        assert (len(plan) if plan is not None else None) == optimum, start


def test_peg5_reaches_the_five_states_interop_counted():
    """interop/README.md: `11011` reaches only {00111, 11100, 01001, 10010}.

    Enumerated there over a graph this package shares no code with, and the
    thing both pagoda certificates for that board are claims about.
    """
    for name in verify_all.PEG5_RULESETS:
        derived = tuple(sorted("".join(str(value) for value in state)
                               for state in reachable_states(rules(name))))
        assert derived == verify_all.PEG5_REACHABLE, name
        assert min(state.count("1") for state in derived) == 2


def test_sokoban_optima_match_the_fixture():
    for name, optimum, _why in verify_all.SOKOBAN_OPTIMA:
        plan = shortest_plan(rules(name))
        assert (len(plan) if plan is not None else None) == optimum, name


def test_the_sokoban_constraint_is_proved_not_assumed():
    """Restricting the space is only sound because the restriction is inductive."""
    ruleset = rules("sokoban-open4far")
    conditions = ruleset.obligations().conditions
    assert conditions["constraint_init"]
    assert conditions["constraint_closed"]
    assert ruleset.n_states == 16 ** 3


def test_a2_world_replays_a2s_own_refutation_frame_by_frame():
    try:
        report = anchors.a2_replay_episode(rules("a2-world"))
    except anchors.AnchorUnavailable as exc:
        pytest.skip("cold-start-a2's episode is not on this machine: %s" % exc)
    assert report["mismatches"] == []
    assert report["n_actions"] == 18
    assert report["world_reports_win"] and report["rules_reach_goal"]


def test_a2_holed_agrees_with_the_step_table_lean_accepted():
    try:
        report = anchors.a2_lean_step_table(rules("a2-holed"))
    except anchors.AnchorUnavailable as exc:
        pytest.skip("cold-start-a2's Lean file is not on this machine: %s" % exc)
    assert report["complete"], report
    assert report["n_rows"] == 592
    assert report["n_mismatches"] == 0, report["mismatches"]


# --------------------------------------------------------------- the forgeries

def test_a_certificate_binds_to_a_file_and_not_just_to_a_name():
    """Every generated certificate carries the digest of its rule set file."""
    for filename in sorted(os.listdir(CASES)):
        if not filename.endswith(".cert.json"):
            continue
        payload = json.load(open(os.path.join(CASES, filename), encoding="utf-8"))
        binding = payload.get("ruleset")
        if binding is None:
            # Exactly one certificate is unbound on purpose: the A2 one is
            # checked against two rule sets, which is the whole exhibit.
            assert payload["name"] == "a2-right-room-locked", filename
            continue
        assert len(binding["sha256"]) == 64, filename
        path = os.path.join(CASES, "%s.rules.json" % binding["name"])
        with open(path, "rb") as handle:
            assert hashlib.sha256(handle.read()).hexdigest() == binding["sha256"], filename


def test_every_forgery_behaves_as_the_catalogue_declares():
    attempts = forgeries.run_all()
    off_script = [a for a in attempts if not a.as_declared]
    assert not off_script, "\n".join(
        "%s: expected %s, got %s (%s)"
        % (a.forgery.name, a.forgery.expect, a.verdict, a.message)
        for a in off_script)
    assert len(attempts) >= 20


def test_nothing_is_accepted_except_the_two_that_are_declared():
    """Two forgeries end in ACCEPT, and both are on the record for why.

    `delete-the-rule` is the one no certificate checker can catch.
    `region-reaching-outside-the-constraint` is correct under the reachability
    qualifier the carver's theorem actually carries -- and is only allowed to
    pass while the verdict reports, with a count, how much of the region rested
    on that qualifier rather than on a check.
    """
    accepted = [a for a in forgeries.run_all() if a.verdict == ACCEPT]
    assert sorted(a.forgery.name for a in accepted) == [
        "delete-the-rule", "region-reaching-outside-the-constraint"]
    assert sorted(a.forgery.expect for a in accepted) == [
        forgeries.QUALIFIED, forgeries.NOT_CAUGHT]


def test_a_def_cannot_smuggle_the_action_label_into_a_state_predicate():
    """The one forgery that produced a real wrong ACCEPT before it was fixed."""
    payload = spec("peg4-1101", "rules")
    payload["defs"] = [{"name": "peek", "params": [],
                        "body": ["=", ["act"], ["lit", "jump(0,1,2)"]]}]
    payload["goal"] = ["call", "peek"]
    with pytest.raises(RuleSetError) as caught:
        ruleset_from_spec(payload)
    assert "action" in str(caught.value)


def test_a_certificate_can_call_the_rule_sets_own_defs():
    """`compile_macros` used to drop the enclosing scope, which hid the above."""
    payload = spec("a2-right-room-locked", "cert")
    payload["predicate"] = ["not", ["call", "free", ["var", "cart"]]]
    verdict = recheck(rules("a2-world"), certificate_from_spec(payload))
    assert verdict.conditions["predicate_wellformed"] is True


def test_a_shrunken_domain_that_drops_the_goal_is_refused():
    """`unsolvable` is free in a world with no goal state."""
    payload = spec("peg4-0111", "rules")
    payload["variables"][1]["domain"] = [0]        # pos1, which the goal needs
    payload["init"]["pos1"] = 0
    unbound = spec("peg4-0111-ic3", "cert")
    unbound.pop("ruleset")
    verdict = recheck(ruleset_from_spec(payload), certificate_from_spec(unbound))
    assert verdict.verdict == REJECT
    assert verdict.ruleset_conditions["goal_satisfiable"] is False


def test_a_dead_region_may_not_hide_a_goal_state_outside_the_constraint():
    payload = spec("sokoban-open4far-dead-b1-11", "cert")
    payload.pop("ruleset")
    payload["predicate"] = [
        "or", ["=", ["var", "b1"], ["lit", "1,1"]],
        ["and", ["=", ["var", "player"], ["lit", "1,3"]],
         ["=", ["var", "b1"], ["lit", "4,2"]],
         ["=", ["var", "b2"], ["lit", "1,3"]]]]
    verdict = recheck(rules("sokoban-open4far"), certificate_from_spec(payload))
    assert verdict.verdict == REJECT
    assert verdict.conditions["goal_break"] is False


def test_every_accepted_region_reports_what_the_constraint_left_unchecked():
    """The genuine pair deadlocks lean on the qualifier too, by 2 states each."""
    verdict = recheck(rules("sokoban-open4far"),
                      cert("sokoban-open4far-dead-b1-12-b2-13"))
    assert verdict.verdict == ACCEPT
    assert verdict.stats["n_satisfying_outside_constraint"] == 2
    assert any("reachability qualifier" in reason for reason in verdict.reasons)


def test_the_constraint_provably_contains_everything_reachable():
    conditions = rules("sokoban-open4far").obligations().conditions
    assert conditions["constraint_contains_reachable"]


def test_no_forgery_ever_produces_an_inconsistent_verdict():
    """INCONSISTENT means the checker caught itself contradicting itself."""
    assert not [a for a in forgeries.run_all() if a.verdict == INCONSISTENT]


# ------------------------------------------------------- the language's limits

def test_a_certificate_cannot_bring_its_own_world():
    for key in ("goal", "init", "states", "transitions", "rules", "actions",
                "variables", "constraint"):
        payload = spec("peg4-0111-ic3", "cert")
        payload[key] = []
        with pytest.raises(CertificateError) as caught:
            certificate_from_spec(payload)
        assert key in str(caught.value)


def test_defs_may_not_recurse():
    payload = spec("a2-world", "rules")
    payload["defs"] = [{"name": "loop", "params": ["x"],
                        "body": ["call", "loop", ["param", "x"]]}]
    with pytest.raises(RuleSetError):
        ruleset_from_spec(payload)


def test_defs_keep_their_declared_order():
    """`free` calls `rendered`, so `rendered` must be declared first."""
    payload = spec("a2-world", "rules")
    payload["defs"] = list(reversed(payload["defs"]))
    with pytest.raises(RuleSetError):
        ruleset_from_spec(payload)


def test_a_non_boolean_predicate_is_rejected_rather_than_coerced_or_crashed():
    """`pos1` is 0 or 1, and Python would happily call 1 true.

    The predicate must denote a *set of states*; a certificate whose predicate
    evaluates to an integer denotes nothing, and the tool has to say so with a
    verdict rather than a traceback.
    """
    payload = spec("peg4-0111-ic3", "cert")
    payload.pop("ruleset", None)
    payload["predicate"] = ["var", "pos1"]
    verdict = recheck(rules("peg4-0111"), certificate_from_spec(payload))
    assert verdict.verdict == REJECT
    assert verdict.conditions["predicate_wellformed"] is False


def test_a_rule_set_that_raises_is_rejected_rather_than_crashed():
    payload = spec("peg4-0111", "rules")
    payload["tables"] = {"t": {"arity": 1, "entries": [[0, 0]]}}
    payload["goal"] = ["=", ["table", "t", ["var", "pos1"]], ["lit", 0]]
    unbound = spec("peg4-0111-ic3", "cert")
    unbound.pop("ruleset")           # else it is refused at the digest first
    verdict = recheck(ruleset_from_spec(payload), certificate_from_spec(unbound))
    assert verdict.verdict == REJECT
    assert verdict.ruleset_conditions["rules_evaluate"] is False


def test_a_table_lookup_with_no_entry_and_no_default_is_an_error():
    payload = spec("peg4-0111", "rules")
    payload["tables"] = {"t": {"arity": 1, "entries": [[0, 0]]}}
    payload["goal"] = ["=", ["table", "t", ["var", "pos1"]], ["lit", 0]]
    ruleset = ruleset_from_spec(payload)
    with pytest.raises(ExprError):
        ruleset.goal(tuple(1 for _ in ruleset.variables))


def test_the_state_space_is_the_product_and_not_a_reachable_set():
    """`inv_closed` has to hold from every state satisfying I, reachable or not.

    Restricting it to the reachable part would make the check circular: what is
    reachable is exactly what the certificate is supposed to bound.
    """
    ruleset = rules("a2-holed")
    assert ruleset.n_states == 37 * 2 * 2
    assert len(ruleset.states()) == ruleset.n_states
    plan = shortest_plan(ruleset)
    assert plan is None                       # and yet the product is enumerated


def test_a_rule_set_too_large_to_enumerate_is_refused_not_sampled():
    payload = spec("peg4-0111", "rules")
    payload["variables"] = [
        {"name": "pos%d" % i, "domain": [0, 1]} for i in range(64)
    ]
    payload["init"] = {"pos%d" % i: 0 for i in range(64)}
    with pytest.raises(RuleSetError) as caught:
        ruleset_from_spec(payload)
    assert "cap" in str(caught.value)


# ------------------------------------------------------------- reproducibility

def test_the_committed_cases_are_what_the_generator_makes():
    assert build_cases.check() == []


def test_the_generator_is_byte_stable():
    first = {k: json.dumps(v, sort_keys=True) for k, v in build_cases.all_cases().items()}
    second = {k: json.dumps(v, sort_keys=True) for k, v in build_cases.all_cases().items()}
    assert first == second


def test_recheck_never_imports_the_engines():
    """The independence claim, enforced rather than asserted.

    `interop` is on the forbidden list as of E6.  The pagoda kind is rechecked
    against certificates `interop/certificate_export.py` wrote, and that module
    imports `engines.lp_potential.potential` -- so importing anything from
    `interop` would reach the engine one hop further out and the independence
    would be gone at exactly the point it is being claimed.  `anchors.py`
    *reads* files under `interop/certificates/`, which is the same thing it does
    to `cold-start-a2/` and is not an import.

    The scan is also asserted to have covered the modules the pagoda work
    touched: a filter that silently stopped matching would otherwise leave this
    test passing over nothing.
    """
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    package = os.path.join(here, "recheck")
    forbidden = ("engines", "tools.", "interop")
    offenders = []
    scanned = []
    for name in sorted(os.listdir(package)):
        if not name.endswith(".py"):
            continue
        scanned.append(name)
        with open(os.path.join(package, name), "r", encoding="utf-8") as handle:
            text = handle.read()
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith(("import ", "from ")) and any(
                    token in stripped for token in forbidden):
                offenders.append("%s: %s" % (name, stripped))
    assert not offenders, offenders
    assert {"anchors.py", "build_cases.py", "certificate.py", "forgeries.py",
            "verify.py", "verify_all.py"} <= set(scanned), scanned


def test_the_whole_verify_script_is_green():
    assert verify_all.main([]) == 0


def test_deep_copies_of_the_cases_do_not_leak_between_forgeries():
    """`forgeries.case()` must hand out a fresh object every time."""
    first = forgeries.case("peg4-0111.rules.json")
    first["name"] = "mutated"
    second = forgeries.case("peg4-0111.rules.json")
    assert second["name"] == "peg4-0111"
    assert copy.deepcopy(second) == second
