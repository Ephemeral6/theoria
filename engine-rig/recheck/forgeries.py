"""Certificates and rule sets built to get a wrong ACCEPT out of the rechecker.

A checker nobody attacked is a checker nobody has measured.  Each entry below is
a specific way to lie -- to the rechecker, not to a reader -- together with the
rejection it must draw and the name of the condition that must be the one to
fail.  The runner asserts all three: the verdict, the failing condition, and,
for the malformed ones, that the input is refused at load time rather than
quietly normalised.

They fall into three families.

**Lying in the certificate.**  Claim nothing (an unsatisfiable invariant), claim
everything (a universal one), or bring your own goal / state space / transition
relation so the claim is checked against itself.  These are cheap to build and
the reason the certificate schema refuses `goal`, `init`, `states`,
`transitions` and `rules` by name.

**Lying in the rule set.**  Strictly the more dangerous family, because the rule
set is the thing the rechecker trusts.  Shrink a variable's domain so the
escaping successor has nowhere to land; declare a well-formedness constraint
that excludes the state the certificate fails on; smuggle in an edge list.  All
three are caught before any certificate is read, by the obligations the rule set
owes about itself.

**The one that is not caught, and is listed anyway.**  Delete a rule.  A rule
set missing a rule is a perfectly well-formed rule set, its constraint is
inductive, its step is single-valued, and a certificate true of it verifies.
That is not a hole in this rechecker; it is the whole of Theoria §1.3, and the
only instrument for it is the refutation loop, not a checker.  `expect:
NOT-CAUGHT` is a declared result with a witness attached, and the suite fails if
it ever starts being caught, because that would mean the checker had grown an
opinion about worlds it cannot see.
"""

import copy
import json
import os
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

from recheck.certificate import CertificateError, certificate_from_spec
from recheck.ruleset import RuleSetError, ruleset_from_spec
from recheck.verify import ACCEPT, INCONSISTENT, REJECT, recheck

CASES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cases")

LOAD_ERROR = "LOAD-ERROR"
NOT_CAUGHT = "NOT-CAUGHT"


def case(name: str) -> dict:
    with open(os.path.join(CASES_DIR, name), "r", encoding="utf-8") as handle:
        return json.load(handle)


@dataclass(frozen=True)
class Forgery:
    name: str
    family: str
    what: str
    expect: str                              # REJECT | LOAD-ERROR | NOT-CAUGHT
    build: Callable[[], Tuple[dict, dict]]   # -> (ruleset spec, certificate spec)
    condition: Optional[str] = None          # the condition that must fail
    why: str = ""


# ------------------------------------------------- family 1: lie in the certificate

def _peg_cert(**overrides) -> dict:
    spec = case("peg4-0111-ic3.cert.json")
    spec.pop("ruleset", None)
    spec.update(overrides)
    return spec


def _claims_nothing() -> Tuple[dict, dict]:
    """An invariant no state satisfies is closed and goal-free for free."""
    return case("peg4-0111.rules.json"), _peg_cert(
        name="forged-empty-invariant",
        predicate=["and", ["=", ["var", "pos1"], ["lit", 0]],
                   ["=", ["var", "pos1"], ["lit", 1]]],
    )


def _claims_everything() -> Tuple[dict, dict]:
    """An invariant every state satisfies holds at init and is closed."""
    return case("peg4-0111.rules.json"), _peg_cert(
        name="forged-universal-invariant", predicate=["and"],
    )


def _brings_its_own_goal() -> Tuple[dict, dict]:
    spec = _peg_cert(name="forged-own-goal")
    spec["goal"] = ["=", ["var", "pos0"], ["lit", 1]]
    return case("peg4-0111.rules.json"), spec


def _brings_its_own_transitions() -> Tuple[dict, dict]:
    spec = _peg_cert(name="forged-own-transitions")
    spec["transitions"] = []
    return case("peg4-0111.rules.json"), spec


def _brings_its_own_states() -> Tuple[dict, dict]:
    spec = _peg_cert(name="forged-own-states")
    spec["states"] = ["0111", "1001"]
    return case("peg4-0111.rules.json"), spec


def _brings_its_own_constraint() -> Tuple[dict, dict]:
    spec = _peg_cert(name="forged-own-constraint")
    spec["constraint"] = ["=", ["var", "pos0"], ["lit", 0]]
    return case("peg4-0111.rules.json"), spec


def _reads_the_action() -> Tuple[dict, dict]:
    """A predicate over actions is a rule, not a set of states."""
    return case("peg4-0111.rules.json"), _peg_cert(
        name="forged-action-predicate",
        predicate=["!=", ["act"], ["lit", "jump(0,1,2)"]],
    )


def _returns_a_number() -> Tuple[dict, dict]:
    """`pos1` is 0 or 1, and Python is happy to call 1 true.

    A predicate that returns an integer denotes no set of states.  It must be
    rejected on those grounds rather than coerced -- and, since the rechecker
    evaluates it on every state, it must not escape as a traceback either.
    """
    return case("peg4-0111.rules.json"), _peg_cert(
        name="forged-integer-predicate", predicate=["var", "pos1"],
    )


def _names_an_undeclared_variable() -> Tuple[dict, dict]:
    return case("peg4-0111.rules.json"), _peg_cert(
        name="forged-undeclared-variable",
        predicate=["=", ["var", "pos9"], ["lit", 0]],
    )


def _claims_the_wrong_theorem() -> Tuple[dict, dict]:
    return case("peg4-0111.rules.json"), _peg_cert(
        name="forged-mismatched-claim", claim="conditional_unsolvability",
    )


def _bound_to_another_ruleset() -> Tuple[dict, dict]:
    spec = _peg_cert(name="forged-wrong-binding")
    spec["ruleset"] = {"name": "peg4-1101"}
    return case("peg4-0111.rules.json"), spec


def _shadows_a_definition() -> Tuple[dict, dict]:
    """Redefining `free` would rewrite every guard in the A2 rule set."""
    spec = case("a2-right-room-locked.cert.json")
    spec["name"] = "forged-shadowed-def"
    spec["defs"] = [{"name": "free", "params": ["x"], "body": ["and"]}]
    return case("a2-world.rules.json"), spec


def _invariant_for_a_solvable_start() -> Tuple[dict, dict]:
    """The same clause set, moved to the configuration `ic3_pdr` refuses.

    `1101` is solvable in two moves, so no invariant exists; the engine returns
    a replayed counterexample instead.  A certificate that claims one anyway is
    the most ordinary forgery there is.
    """
    return case("peg4-1101.rules.json"), _peg_cert(name="forged-invariant-on-1101")


# ---------------------------------------------- family 2: dead-region forgeries

def _vacuous_region() -> Tuple[dict, dict]:
    spec = case("sokoban-ringstuck-dead-b1-11.cert.json")
    spec["name"] = "forged-vacuous-region"
    spec.pop("ruleset", None)
    spec["predicate"] = ["and", ["=", ["var", "b1"], ["lit", "1,1"]],
                         ["=", ["var", "b1"], ["lit", "1,4"]]]
    return case("sokoban-ringstuck.rules.json"), spec


def _region_that_leaks() -> Tuple[dict, dict]:
    """A box in the open is not dead, however confidently the pattern says so."""
    spec = case("sokoban-open4far-dead-b1-11.cert.json")
    spec["name"] = "forged-open-cell-region"
    spec.pop("ruleset", None)
    spec["predicate"] = ["and", ["=", ["var", "b1"], ["lit", "2,2"]]]
    return case("sokoban-open4far.rules.json"), spec


def _region_containing_the_goal() -> Tuple[dict, dict]:
    spec = case("sokoban-ringstuck-dead-b1-11.cert.json")
    spec["name"] = "forged-region-over-the-goal"
    spec.pop("ruleset", None)
    spec["predicate"] = ["and", ["=", ["var", "b1"], ["lit", "3,1"]]]
    return case("sokoban-ringstuck.rules.json"), spec


# -------------------------------------------------- family 3: lie in the rule set

def _shrink_the_domain() -> Tuple[dict, dict]:
    """Cut the Cart's domain to the left room so the teleport has nowhere to land.

    The most economical attack on the A2 case: leave every rule intact, and
    simply stop admitting the cell the escaping transition goes to.
    """
    spec = copy.deepcopy(case("a2-world.rules.json"))
    spec["name"] = "forged-a2-shrunken-domain"
    zero = {"1,3", "1,4", "2,1", "2,2", "2,3", "2,4", "3,1", "3,2", "3,3", "3,4",
            "4,1", "4,2", "4,3", "4,4", "5,1", "5,2", "5,3", "5,4",
            "6,2", "6,3", "6,4"}
    for variable in spec["variables"]:
        if variable["name"] == "cart":
            variable["domain"] = sorted(zero)
    spec["tables"]["nb"]["entries"] = [
        row for row in spec["tables"]["nb"]["entries"] if row[0] in zero
    ]
    return spec, case("a2-right-room-locked.cert.json")


def _constrain_away_the_witness() -> Tuple[dict, dict]:
    """Declare the escaping state ill-formed and hope nobody checks the claim.

    `constraint` exists so the sokoban theorems can be checked against a state
    space the grounded task can actually represent.  It is exactly as dangerous
    as it sounds, which is why it is proved inductive rather than believed.
    """
    spec = copy.deepcopy(case("a2-world.rules.json"))
    spec["name"] = "forged-a2-constrained-witness"
    spec["constraint"] = ["!=", ["var", "cart"], ["lit", "6,4"]]
    return spec, case("a2-right-room-locked.cert.json")


def _tamper_under_the_same_name() -> Tuple[dict, dict]:
    """Edit the rule set, keep its name, and hope the binding is by name only.

    It was, until the transcription audit said so: every generated certificate
    now carries the digest of the rule set file it was written for.
    """
    spec = copy.deepcopy(case("sokoban-ringstuck.rules.json"))
    spec["rules"] = [rule for rule in spec["rules"] if rule["name"] != "push_left"]
    return spec, case("sokoban-ringstuck-dead-b1-11.cert.json")


def _smuggle_an_edge_list() -> Tuple[dict, dict]:
    spec = copy.deepcopy(case("peg4-0111.rules.json"))
    spec["name"] = "forged-peg-edge-list"
    spec["transitions"] = [["0111", "jump(2,1,0)", "1001"]]
    return spec, _peg_cert(name="cert-over-a-smuggled-edge-list")


def _two_rules_one_variable() -> Tuple[dict, dict]:
    """Ambiguous step: the successor stops being a function of the state."""
    spec = copy.deepcopy(case("peg4-0111.rules.json"))
    spec["name"] = "forged-peg-ambiguous-step"
    spec["rules"].append({
        "name": "shadow_jump",
        "action": "jump(0,1,2)",
        "guard": ["=", ["var", "pos0"], ["lit", 1]],
        "effects": {"pos2": ["lit", 0]},
    })
    return spec, _peg_cert(name="cert-over-an-ambiguous-step")


def _rule_that_leaves_the_domain() -> Tuple[dict, dict]:
    spec = copy.deepcopy(case("peg4-0111.rules.json"))
    spec["name"] = "forged-peg-off-domain-effect"
    spec["rules"][0]["effects"]["pos0"] = ["lit", 2]
    return spec, _peg_cert(name="cert-over-an-off-domain-rule")


def _owns_less_than_it_writes() -> Tuple[dict, dict]:
    spec = copy.deepcopy(case("peg4-0111.rules.json"))
    spec["name"] = "forged-peg-undeclared-write"
    spec["rules"][0]["owns"] = ["pos0"]
    return spec, _peg_cert(name="cert-over-an-undeclared-write")


def _a_rule_set_that_raises() -> Tuple[dict, dict]:
    """A table with a missing key and no default: the world stops being total.

    The temptation is to treat the raising state as absent, which would make a
    rule set able to delete states by making them un-evaluable.
    """
    spec = copy.deepcopy(case("peg4-0111.rules.json"))
    spec["tables"] = {"t": {"arity": 1, "entries": [[0, 0]]}}
    spec["goal"] = ["=", ["table", "t", ["var", "pos1"]], ["lit", 0]]
    return spec, _peg_cert(name="cert-over-a-partial-table")


def _delete_the_rule() -> Tuple[dict, dict]:
    """The one that works, and is listed for that reason."""
    return case("a2-holed.rules.json"), case("a2-right-room-locked.cert.json")


CATALOGUE: Tuple[Forgery, ...] = (
    Forgery("claims-nothing", "certificate", "an invariant no state satisfies",
            REJECT, _claims_nothing, "inv_init",
            "closed and goal-free for free, and true of no state the world can be in"),
    Forgery("claims-everything", "certificate", "an invariant every state satisfies",
            REJECT, _claims_everything, "goal_break",
            "holds at init and is closed; it just fails to exclude the goal"),
    Forgery("brings-its-own-goal", "certificate", "a certificate carrying a `goal`",
            LOAD_ERROR, _brings_its_own_goal, None,
            "would prove a different theorem than the one claimed"),
    Forgery("brings-its-own-transitions", "certificate",
            "a certificate carrying `transitions`", LOAD_ERROR,
            _brings_its_own_transitions, None,
            "the relation is derived here, never read"),
    Forgery("brings-its-own-states", "certificate", "a certificate carrying `states`",
            LOAD_ERROR, _brings_its_own_states, None,
            "the space is the product of the declared domains, not a list"),
    Forgery("brings-its-own-constraint", "certificate",
            "a certificate carrying `constraint`", LOAD_ERROR,
            _brings_its_own_constraint, None,
            "shrinking the space is the rule set's business, and only when proved"),
    Forgery("reads-the-action", "certificate", "a predicate over the action label",
            REJECT, _reads_the_action, "predicate_wellformed",
            "a set of states cannot depend on which rule is being applied"),
    Forgery("integer-predicate", "certificate",
            "a predicate returning 0 or 1 instead of a boolean", REJECT,
            _returns_a_number, "predicate_wellformed",
            "Python would call 1 true; a set of states has to be denoted, not "
            "coerced, and the tool must answer with a verdict not a traceback"),
    Forgery("undeclared-variable", "certificate", "a predicate naming pos9",
            REJECT, _names_an_undeclared_variable, "predicate_wellformed",
            "a name the rule set never declared has no meaning to check against"),
    Forgery("mismatched-claim", "certificate",
            "an inductive invariant claiming conditional unsolvability",
            LOAD_ERROR, _claims_the_wrong_theorem, None,
            "the kind fixes the claim; picking another is picking the conclusion"),
    Forgery("wrong-binding", "certificate", "a certificate bound to another rule set",
            REJECT, _bound_to_another_ruleset, "ruleset_binding",
            "checking peg4-1101's certificate against peg4-0111 proves nothing"),
    Forgery("shadows-a-definition", "certificate",
            "a certificate redefining the rule set's `free`", REJECT,
            _shadows_a_definition, "predicate_wellformed",
            "redefining a guard's vocabulary rewrites the rules under cover"),
    Forgery("invariant-on-a-solvable-start", "certificate",
            "the 0111 invariant, offered for the solvable 1101", REJECT,
            _invariant_for_a_solvable_start, "inv_init",
            "the ordinary forgery: a real certificate for the wrong instance"),

    Forgery("vacuous-region", "dead-region", "a pattern no state satisfies",
            REJECT, _vacuous_region, "region_nonempty",
            "a theorem about no state is closed, goal-free, and empty"),
    Forgery("region-that-leaks", "dead-region", "a box in the open declared dead",
            REJECT, _region_that_leaks, "region_closed",
            "the successor leaves the pattern, which is what dead means"),
    Forgery("region-over-the-goal", "dead-region",
            "the goal configuration itself declared dead", REJECT,
            _region_containing_the_goal, "goal_break",
            "a region containing a goal state cannot be dead"),

    Forgery("shrunken-domain", "rule-set",
            "the Cart's domain cut to the left room so the teleport cannot land",
            REJECT, _shrink_the_domain, "effects_in_domain",
            "every rule intact, and the escaping successor simply not admitted"),
    Forgery("constrained-witness", "rule-set",
            "a constraint declaring the escaping state ill-formed", REJECT,
            _constrain_away_the_witness, "constraint_closed",
            "a declared restriction is refused unless it is itself inductive"),
    Forgery("tampered-under-the-same-name", "rule-set",
            "a rule deleted, the rule set's name kept", REJECT,
            _tamper_under_the_same_name, "ruleset_binding",
            "a binding by name alone would pass; the certificate carries the "
            "digest of the file it was written for"),
    Forgery("smuggled-edge-list", "rule-set", "a rule set shipping `transitions`",
            LOAD_ERROR, _smuggle_an_edge_list, None,
            "an unknown top-level key, refused rather than ignored"),
    Forgery("ambiguous-step", "rule-set",
            "two rules writing one variable on one action", REJECT,
            _two_rules_one_variable, "step_single_valued",
            "`conflict exclusive` is an error, not a precedence question"),
    Forgery("off-domain-effect", "rule-set",
            "a rule setting a variable outside its declared domain", REJECT,
            _rule_that_leaves_the_domain, "effects_in_domain",
            "the product would no longer contain the successor"),
    Forgery("undeclared-write", "rule-set",
            "a rule that owns less than it writes", LOAD_ERROR,
            _owns_less_than_it_writes, None,
            "would let two rules write one variable with neither declaring it"),

    Forgery("partial-table", "rule-set",
            "a table lookup with no entry and no default", REJECT,
            _a_rule_set_that_raises, "rules_evaluate",
            "a state that cannot be evaluated is not a state that is absent"),

    Forgery("delete-the-rule", "not-caught",
            "the world's rule set, minus one rule", NOT_CAUGHT,
            _delete_the_rule, None,
            "Theoria 1.3: a manual is checked against its own past, and a rule "
            "that never fired owes no frame. No certificate checker can see "
            "this; the refutation loop can, and did."),
)


@dataclass
class Attempt:
    forgery: Forgery
    verdict: str
    failed_conditions: List[str] = field(default_factory=list)
    message: str = ""
    as_declared: bool = False
    detail: Dict[str, object] = field(default_factory=dict)

    def as_json(self) -> Dict[str, object]:
        return {
            "name": self.forgery.name,
            "family": self.forgery.family,
            "what": self.forgery.what,
            "why": self.forgery.why,
            "expected": self.forgery.expect,
            "expected_condition": self.forgery.condition,
            "verdict": self.verdict,
            "failed_conditions": list(self.failed_conditions),
            "message": self.message,
            "as_declared": self.as_declared,
        }


def attempt(forgery: Forgery) -> Attempt:
    """Run one forgery and say whether it behaved as the catalogue declares."""
    try:
        ruleset_spec, certificate_spec = forgery.build()
        ruleset = ruleset_from_spec(ruleset_spec)
        certificate = certificate_from_spec(certificate_spec)
    except (RuleSetError, CertificateError) as exc:
        return Attempt(
            forgery=forgery, verdict=LOAD_ERROR, message=str(exc),
            as_declared=forgery.expect == LOAD_ERROR,
        )

    verdict = recheck(ruleset, certificate)
    failed = sorted(
        [name for name, ok in verdict.conditions.items() if not ok]
        + [name for name, ok in verdict.ruleset_conditions.items() if not ok]
    )
    message = "; ".join(verdict.reasons)

    if forgery.expect == NOT_CAUGHT:
        as_declared = verdict.verdict == ACCEPT
    elif forgery.expect == REJECT:
        as_declared = (
            verdict.verdict == REJECT
            and (forgery.condition is None or forgery.condition in failed)
        )
    else:
        as_declared = False

    return Attempt(
        forgery=forgery, verdict=verdict.verdict, failed_conditions=failed,
        message=message, as_declared=as_declared,
        detail={"witnesses": {k: v[:2] for k, v in verdict.witnesses.items()}},
    )


def run_all() -> List[Attempt]:
    return [attempt(forgery) for forgery in CATALOGUE]


def summary(attempts: List[Attempt]) -> Dict[str, object]:
    return {
        "n_forgeries": len(attempts),
        "n_as_declared": sum(1 for a in attempts if a.as_declared),
        "n_off_script": sum(1 for a in attempts if not a.as_declared),
        "n_accepted": sum(1 for a in attempts if a.verdict == ACCEPT),
        "n_inconsistent": sum(1 for a in attempts if a.verdict == INCONSISTENT),
        "attempts": [a.as_json() for a in attempts],
    }
