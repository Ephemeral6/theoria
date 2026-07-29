"""Process 4 — the anti-gaming audit.

`Theoria.md`: *逐指标写下"怎么刷它"，判断各臂是否可能无意中优化它；刷得动又防不住
的，降级为参考项，不入主表.*

Three fields decide a metric's tier, and the rule is mechanical:

    gameable AND accidental AND NOT defended  ->  reference
    otherwise                                 ->  main

`accidental` is the field that does the work. A metric an arm could cheat if
it wanted is a much smaller problem than a metric an arm optimises *without
trying* — nobody in this project is going to deliberately game their own
instrument, but a harness that batches its actions will inflate P1 by accident
on the first run, and an arm that crashes on turn three will look perfectly
front-loaded.

`defended` means **the battery implements the defence**, not that a defence is
imaginable. "Pair by game and it goes away" is not a defence until something
pairs by game.

Demotion is not deletion. Reference metrics are computed, reported and
correlated; they are excluded from ordering claims and from the main table.
"""

from __future__ import annotations

from typing import Dict

from battery.metrics import REGISTRY

# metric_id -> how_to_game / accidental / defence / defended
GAMING_REGISTER: Dict[str, Dict[str, object]] = {

    # ---- exploration --------------------------------------------------
    "X1": {
        "how_to_game": "Never revisit anything: flail through a large state "
                       "space taking a fresh action every turn. A run that "
                       "dies on turn three scores a perfect 0.",
        "accidental": True,
        "defence": "Floor the run length and read it beside X5; a low revisit "
                   "rate over 8 distinct states is not the same fact as a low "
                   "revisit rate over 200.",
        "defended": False,
    },
    "X2": {
        "how_to_game": "Take a never-before-tried action every turn. Short "
                       "runs score 1.0 automatically -- three of the pilot's "
                       "runs do exactly that.",
        "accidental": True,
        "defence": "Same floor as X1; X2 is really X3's input rather than a "
                   "score of its own.",
        "defended": False,
    },
    "X3": {
        "how_to_game": "Repeat yourself deliberately in the last quarter to "
                       "widen the gap.",
        "accidental": False,
        "defence": "Gaming it requires deliberately wasting late turns, which "
                   "costs score on every other metric at once.",
        "defended": True,
    },
    "X4": {
        "how_to_game": "End the run before a streak can form.",
        "accidental": True,
        "defence": "Normalised by run length, which removes the length effect "
                   "but not the early-exit effect.",
        "defended": False,
    },
    "X5": {"how_to_game": "Not a ranking.", "accidental": False,
           "defence": "Diagnostic.", "defended": True},
    "X6": {
        "how_to_game": "Vary the action after every failure on principle, "
                       "without reading the failure. A harness that rotates "
                       "its action list on retry scores 1.0 having modelled "
                       "nothing at all.",
        "accidental": True,
        "defence": "Would need the arm's action to be attributable to a "
                   "decision rather than to a retry policy. The ledger "
                   "collapses the harness's retry loop into one row, so a "
                   "repeat across logged steps *is* an arm decision -- but "
                   "nothing checks that the arm was shown the failure before "
                   "choosing, and on the pilot harness it demonstrably was "
                   "not.",
        "defended": False,
    },

    # ---- planning -----------------------------------------------------
    "P1": {
        "how_to_game": "Emit ten actions per model call. Any actions. The "
                       "metric cannot tell a plan from a burst.",
        "accidental": True,
        "defence": "Read against P4 (were those actions on the shortest "
                   "path?) -- but P4 needs ground truth, so most runs have no "
                   "check at all.",
        "defended": False,
    },
    "P2": {
        "how_to_game": "Batch more actions per call as the run goes on.",
        "accidental": False,
        "defence": "An *increasing* batch size is a deliberate schedule; a "
                   "harness that batches does so at a constant rate, which "
                   "cancels in the difference.",
        "defended": True,
    },
    "P3": {
        "how_to_game": "Never undo -- easy in a game whose actions are "
                       "irreversible, impossible in one where they are not.",
        "accidental": True,
        "defence": "Compared only within a game, where every arm faces the "
                   "same reversibility. The pairing is implemented.",
        "defended": True,
    },
    "P5": {
        "how_to_game": "Not a ranking -- it measures the infrastructure, "
                       "which is the point.",
        "accidental": False,
        "defence": "Diagnostic. Read it before believing P1 or P2.",
        "defended": True,
    },
    "P4": {
        "how_to_game": "Nothing cheap: the ratio needs a real optimal plan and "
                       "a real attempt to reach the goal.",
        "accidental": False,
        "defence": "Restricted to solve attempts with ground truth; coverage "
                   "walks are refused outright.",
        "defended": True,
    },

    # ---- economy ------------------------------------------------------
    "E1": {"how_to_game": "Not a ranking.", "accidental": False,
           "defence": "Diagnostic.", "defended": True},
    "E2": {
        "how_to_game": "Die early -- a run that ends on turn four spent 100% "
                       "of its cost in its first quarter. Or dump one enormous "
                       "prompt on turn one.",
        "accidental": True,
        "defence": "Requires at least eight turns, and pairs by game so two "
                   "arms are compared over the same problem.",
        "defended": True,
    },
    "E3": {
        "how_to_game": "As E2, from the other end.",
        "accidental": True,
        "defence": "Same eight-turn floor and same pairing.",
        "defended": True,
    },
    "E4": {
        "how_to_game": "Truncate or compact the context on a schedule and the "
                       "quadratic term vanishes.",
        "accidental": True,
        "defence": "None implemented. Prompt caching and context compaction "
                   "do exactly this, for reasons that have nothing to do with "
                   "understanding, and the battery cannot currently tell a "
                   "compaction policy from a theory that closed.",
        "defended": False,
    },
    "E5": {
        "how_to_game": "Emit many cheap actions; the denominator grows faster "
                       "than the numerator.",
        "accidental": True,
        "defence": "Would need pairing against P4. Not implemented.",
        "defended": False,
    },

    "E6": {
        "how_to_game": "Not a ranking -- it measures the API and the retry "
                       "policy, which is the point.",
        "accidental": False,
        "defence": "Diagnostic, and registered `neutral` so no ordering can "
                   "use it. Read it before believing E1 or E5.",
        "defended": True,
    },
    "E7": {
        "how_to_game": "Truncate or summarise the assembled prompt on a "
                       "schedule and the quadratic term vanishes -- exactly "
                       "E4's defect, one layer further out.",
        "accidental": True,
        "defence": "None implemented. `prompt_chars` counts what the harness "
                   "chose to assemble, so a compaction policy and a theory "
                   "that closed produce the same flat curve. The improvement "
                   "over E4 is only that the axis is no longer constant by "
                   "construction, so the metric can now be wrong in an "
                   "interesting way instead of silent.",
        "defended": False,
    },

    # ---- mechanism ----------------------------------------------------
    "M1": {
        "how_to_game": "Flail at random and hit the mechanism early by luck.",
        "accidental": True,
        "defence": "Luck does not repeat across games, and the pairing is "
                   "cross-game. Read beside M2.",
        "defended": True,
    },
    "M2": {
        "how_to_game": "Same flailing; uptake is a hit counter and random "
                       "play eventually hits everything.",
        "accidental": True,
        "defence": "None beyond reading it with M1 -- a mechanism used late is "
                   "still used.",
        "defended": False,
    },
    "M3": {"how_to_game": "Unimplemented.", "accidental": False,
           "defence": "n/a", "defended": True},
    "M4": {
        "how_to_game": "Inject only changes that fire on the first action. "
                       "The delay is a property of which rule was broken at "
                       "least as much as of the manual that noticed.",
        "accidental": False,
        "defence": "The variants are authored before the metric reads them "
                   "and are named in the artefact, so the choice of change is "
                   "auditable rather than tunable after the fact. Gaming it "
                   "requires choosing easy variants *and* publishing the list "
                   "of variants chosen.",
        "defended": True,
    },
    "M5": {
        "how_to_game": "Inject only changes you already know the evidence "
                       "exercises, and the rate is 1.0 by construction.",
        "accidental": True,
        "defence": "None implemented. Nothing in the battery checks that the "
                   "injected variants were chosen independently of the "
                   "evidence set, and the only producer in the repository "
                   "authored both.",
        "defended": False,
    },
    "M6": {
        "how_to_game": "Not a ranking -- and both directions have a bad "
                       "reading, which is why it does not rank.",
        "accidental": False,
        "defence": "Diagnostic. The unambiguous number is in the support "
                   "field: how many repairs would have left a silently false "
                   "theorem standing without dependency tracking.",
        "defended": True,
    },

    # ---- epistemic ----------------------------------------------------
    "K1": {
        "how_to_game": "Overfit. A model with enough parameters replays its "
                       "own history perfectly and knows nothing.",
        "accidental": True,
        "defence": "None, and none is wanted. K1 is the battery's *control*: "
                   "it is the number the field already optimises, and its job "
                   "here is to be high for everyone so that K2 can be the "
                   "thing that separates. Reporting K1 as an achievement is "
                   "the error this whole phase exists to avoid.",
        "defended": False,
    },
    "K2": {
        "how_to_game": "Very little: the pairs are by construction the ones "
                       "the trace never exercised.",
        "accidental": False,
        "defence": "Held-out by construction; the manual is frozen before the "
                   "held-out pairs are scored, and A0's seal is stamped in "
                   "THEORIZE_LOG.md.",
        "defended": True,
    },
    "K3": {
        "how_to_game": "Write many trivial theorems. `0 = 0` is a theorem.",
        "accidental": True,
        "defence": "An LLM asked for theorems will produce them in quantity. "
                   "Needs a non-triviality filter that does not exist yet.",
        "defended": False,
    },
    "K4": {
        "how_to_game": "Only write down clauses you have complete evidence "
                       "for. Omitting every hard rule scores 1.0.",
        "accidental": True,
        "defence": "None implemented -- and A0 demonstrates the failure "
                   "rather than merely predicting it. A0's manual scores K4 = "
                   "1.000 *because* it rejected the one generalisation it "
                   "lacked evidence for (THEORIZE_LOG R-05), and that same "
                   "omission is why its K2 is 0.000. Evidence coverage rewards "
                   "exactly the caution that held-out accuracy punishes. K4 "
                   "must never be reported without K2 beside it.",
        "defended": False,
    },
    "K5": {
        "how_to_game": "Name more things.",
        "accidental": True,
        "defence": "K6 is meant to price each name, but see K6.",
        "defended": False,
    },
    "K6": {
        "how_to_game": "Admit one enormous concept and reject every small "
                       "one. A0's mean is +706 bits, carried entirely by the "
                       "Cart at +2125 while two of the three concepts are "
                       "negative.",
        "accidental": True,
        "defence": "The minimum would be the honest statistic; the mean is "
                   "reported with min and max in its support fields, but the "
                   "headline number is still a mean. Fix in v1.",
        "defended": False,
    },
    "K7": {"how_to_game": "Not a ranking -- a count of a framework conflict.",
           "accidental": False, "defence": "Diagnostic.", "defended": True},
    "K8": {
        "how_to_game": "Design only probes you already know you can run.",
        "accidental": True,
        "defence": "None. And the denominator is tiny (9 on A0), so the ratio "
                   "is noisy as well as gameable.",
        "defended": False,
    },
    "K9": {
        "how_to_game": "Write more playbook entries.",
        "accidental": True,
        "defence": "None implemented.",
        "defended": False,
    },
    "K10": {
        "how_to_game": "Emit many trivial `prune ... => dead` entries.",
        "accidental": False,
        "defence": "A deadlock theorem carries a Lean proof obligation with "
                   "zero axioms; a false one does not compile. The battery "
                   "counts rather than checks, so the defence is external to "
                   "it -- but it is a real one, and it is why this metric "
                   "stays in the main table.",
        "defended": True,
    },
    "K11": {"how_to_game": "Not a ranking.", "accidental": False,
            "defence": "Diagnostic; a low count is ambiguous between 'right "
                       "first time' and 'never checked'.", "defended": True},
    "K12": {
        "how_to_game": "Declare fewer beats. The denominator is the arm's own "
                       "claim about what a repair loop consists of.",
        "accidental": False,
        "defence": "`beats_required` is fixed at six by `Theoria.md`'s A2 "
                   "acceptance, not by the arm, and the adapter sets it. An "
                   "arm that closes four of six reports 0.67 and cannot "
                   "redefine the six.",
        "defended": True,
    },
    "K13": {
        "how_to_game": "Report the patch and not the re-derivation. An "
                       "incremental repair that quietly re-mines the world "
                       "afterwards looks five times cheaper than one that "
                       "says so.",
        "accidental": True,
        "defence": "None implemented, and the exposure is live rather than "
                   "hypothetical: the two arms in hand used different repair "
                   "strategies (`patch` vs `rebuild`) and the ratio cannot "
                   "separate strategy from capability. `strategy` is carried "
                   "into the support field so the confound is at least "
                   "visible, which is not the same as defended.",
        "defended": False,
    },
    "K14": {
        "how_to_game": "Admit no small concepts. A vocabulary of one large "
                       "concept has a minimum equal to its maximum.",
        "accidental": True,
        "defence": "K5 counts the vocabulary and would show the shrinkage, "
                   "but nothing pairs them automatically, and K5 is itself "
                   "gameable in the opposite direction. The pair K7/K14 is "
                   "the intended reading and it is a convention, not a "
                   "mechanism.",
        "defended": False,
    },
}


def _demonstrated() -> Dict[str, object]:
    """The executable register, or nothing if it cannot be built.

    Imported lazily so a broken exploit module degrades this audit to the
    prose register rather than taking the whole recompute down with it.
    """
    try:
        from battery.audit.exploits import collect
        return collect()
    except Exception:            # pragma: no cover - defensive
        return {}


def _v9() -> Dict[str, object]:
    """The blind round's demotions, or nothing if it cannot be built.

    Same lazy-and-forgiving shape as `_demonstrated()`: a broken attack module
    degrades this to the sighted evidence rather than taking the whole
    recompute down.
    """
    try:
        from battery.audit.v9.verdict import v9_demotions
        return v9_demotions()
    except Exception:            # pragma: no cover - defensive
        return {}


def tier_of(metric_id: str) -> str:
    """`main` or `reference` — decided by demonstration where one exists.

    v0 and v1 ran this rule over two hand-set booleans, and the suite only ever
    checked that an entry *existed*, never that it was true. A wrong
    `defended: True` therefore kept a gameable metric in the main table and
    nothing noticed. `battery/audit/exploits/` closes that: where a metric has
    an executed exploit, its `accidental`/`defended` are facts about the code
    and they win. The prose entry is kept beside them so the disagreement stays
    visible rather than being edited away.
    """
    # V9 (blind round) outranks both. `battery/audit/exploits/` was written in
    # the same tree as this register, whose every entry names the hole and the
    # defence, so a sighted attacker could be reading the answer off the page;
    # `battery/BLINDING.md` records what V9's attackers were and were not
    # given. Where the blind round landed a poverty-certified attack that this
    # battery does not defend, that is the newer and the harder evidence, and
    # it decides. It only ever demotes: `PREREG_V9.md` R1 refuses to promote a
    # metric on the strength of nobody having thought of an attack.
    if metric_id in _v9():
        return "reference"

    exploit = _demonstrated().get(metric_id)
    if exploit is not None:
        return exploit.proposed_tier
    entry = GAMING_REGISTER.get(metric_id)
    if entry is None:
        return "reference"      # unregistered means unaudited means not main
    if entry.get("accidental") and not entry.get("defended"):
        return "reference"
    return "main"


def tier_before_v9(metric_id: str) -> str:
    """What B14's sighted round alone concluded.

    `tier_of` now consults the blind round first, which is right for every
    consumer — but it makes "what did we think before V9?" unaskable, and that
    is the comparison the whole exercise is for.  Kept as a separate entry
    point so the two audits can be diffed rather than merged.
    """
    exploit = _demonstrated().get(metric_id)
    if exploit is not None:
        return exploit.proposed_tier
    return _register_tier(metric_id)


def _register_tier(metric_id: str) -> str:
    """What the prose register alone would have said.  Kept for the diff."""
    entry = GAMING_REGISTER.get(metric_id)
    if entry is None:
        return "reference"
    if entry.get("accidental") and not entry.get("defended"):
        return "reference"
    return "main"


def audit() -> Dict[str, object]:
    demonstrated = _demonstrated()
    rows = {}
    disagreements = []
    for metric_id in sorted(GAMING_REGISTER):
        entry = dict(GAMING_REGISTER[metric_id])
        entry["tier"] = tier_of(metric_id)
        entry["register_tier"] = _register_tier(metric_id)

        # For a `neutral` metric the tier is advisory and the direction is the
        # real guard: a diagnostic is excluded from every ordering because it
        # declares no direction, whether it sits in `main` or `reference`.
        # Worth saying in the artefact because the three independent audits
        # that produced these demonstrations did *not* agree on how to treat
        # neutral metrics -- some recorded the neutral direction as itself a
        # defence, some recorded the exploit and let the tier fall. Both
        # readings are defensible and the disagreement is left standing rather
        # than normalised, since normalising it would hide that a hand-set
        # boolean is still doing work here.
        card = REGISTRY.get(metric_id)
        entry["direction"] = card.direction if card else None
        if card is not None and card.direction == "neutral":
            entry["tier_is_advisory"] = True
            entry["tier_note"] = (
                "diagnostic: declares no direction, so it is excluded from "
                "ordering claims by `direction` regardless of tier. The "
                "exploit still matters -- this metric is named as the defence "
                "for other metrics, and a defence that can be reached without "
                "the capability defends nothing.")

        exploit = demonstrated.get(metric_id)
        if exploit is None:
            entry["demonstrated"] = None
            entry["status"] = "prose only — no executed exploit"
            rows[metric_id] = entry
            continue

        entry["demonstrated"] = {
            "claim": exploit.claim,
            "succeeded": exploit.succeeded,
            "accidental": exploit.accidental,
            "defended": exploit.defended,
            "defence": exploit.defence,
        }
        deltas = [field for field in ("accidental", "defended")
                  if bool(entry.get(field)) != bool(
                      getattr(exploit, field))]
        if entry["tier"] != entry["register_tier"] or deltas:
            disagreements.append({
                "metric": metric_id,
                "register_tier": entry["register_tier"],
                "tier": entry["tier"],
                "fields_contradicted": deltas,
                "claim": exploit.claim,
            })
        entry["status"] = ("register contradicted on %s" % ", ".join(deltas)
                           if deltas else "register confirmed by demonstration")
        rows[metric_id] = entry

    return {
        "rule": ("accidental and not defended -> reference; else main. Where "
                 "an executed exploit exists its fields decide, because the "
                 "prose register's booleans are unfalsifiable as written."),
        "n_demonstrated": len(demonstrated),
        "n_prose_only": sum(1 for m in rows if rows[m]["demonstrated"] is None),
        "n_disagreements": len(disagreements),
        "disagreements": disagreements,
        "demoted_by_demonstration": sorted(
            d["metric"] for d in disagreements
            if d["register_tier"] == "main" and d["tier"] == "reference"),
        "main": sorted(m for m in rows if rows[m]["tier"] == "main"),
        "reference": sorted(m for m in rows if rows[m]["tier"] == "reference"),
        "metrics": rows,
    }
