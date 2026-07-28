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
from recheck.verify import ACCEPT, INCONSISTENT, REJECT, recheck, shortest_plan

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


# ---------------------------------------------------------------- the anchors

def test_peg_reachability_matches_the_hand_verified_docstring():
    """fixtures/peg4.py argues these four by exhaustive expansion, by hand."""
    for start, optimum in (("1110", None), ("0111", None),
                           ("1011", None), ("1101", 2)):
        plan = shortest_plan(rules("peg4-%s" % start))
        assert (len(plan) if plan is not None else None) == optimum, start


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


def test_the_only_forgery_that_works_is_the_one_no_checker_can_catch():
    accepted = [a for a in forgeries.run_all() if a.verdict == ACCEPT]
    assert [a.forgery.name for a in accepted] == ["delete-the-rule"]
    assert accepted[0].forgery.expect == forgeries.NOT_CAUGHT


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
    """The independence claim, enforced rather than asserted."""
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    package = os.path.join(here, "recheck")
    offenders = []
    for name in sorted(os.listdir(package)):
        if not name.endswith(".py"):
            continue
        with open(os.path.join(package, name), "r", encoding="utf-8") as handle:
            text = handle.read()
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith(("import ", "from ")) and (
                    "engines" in stripped or "tools." in stripped):
                offenders.append("%s: %s" % (name, stripped))
    assert not offenders, offenders


def test_the_whole_verify_script_is_green():
    assert verify_all.main([]) == 0


def test_deep_copies_of_the_cases_do_not_leak_between_forgeries():
    """`forgeries.case()` must hand out a fresh object every time."""
    first = forgeries.case("peg4-0111.rules.json")
    first["name"] = "mutated"
    second = forgeries.case("peg4-0111.rules.json")
    assert second["name"] == "peg4-0111"
    assert copy.deepcopy(second) == second
