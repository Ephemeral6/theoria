"""The sealed drill: the Phase 4 exam procedure, rehearsed end to end on worlds
that are not sealed games, with the sealed guardrail firing inside the rehearsal.

Run it:

    python -m exam.tools.sealed_drill                 # writes the run, gates on it
    python -m exam.tools.sealed_drill --out <dir>     # somewhere else (determinism)

Exit 0 green, 1 red.  What makes it red is listed in `_gates`, and every gate is
evaluated -- an early failure does not hide a later one.

---------------------------------------------------------------------------
Why this exists when `exam/` already rehearses Phase 4
---------------------------------------------------------------------------

`exam/README.md` is right that the operator library, the spec format and the
marker are already exercised.  But every verdict item ships against `a2`
(`exam/papers/verdict.py:80`), a world its author built and understood from the
first line.  Phase 4's situation is the opposite one, and Theoria.md:372 spells
out the deadlock: constructing a justified unsolvable variant of a sealed game
means understanding that game, and understanding it breaks the seal -- so the
main table runs first and the exam subset is studied only afterwards.  What is
frozen *now* is the operator library and the procedure.

Freezing a procedure is a claim that it works.  This drill is where that claim
can still be falsified, because of one asymmetry that never comes back:

    On a sealed game, "unsolvable by construction" is the only source of truth
    there is, and it can never be checked.  On a worldgen world it can -- the
    world is small enough to enumerate.

So the drill states each variant's truth **by construction**, in a
machine-checkable certificate (`exam/drill_certificates.py`), and only then asks
the exhaustive oracle (`exam/drill_wrapper.py`).  A disagreement is the whole
return on the exercise: it is a defect in the procedure caught on a world that
costs nothing, instead of on a sealed game where it would be invisible.

The second question it answers is whether the frozen library is really
game-agnostic.  `LEGAL_OPERATORS` was chosen as the wrapper-legal set -- the
edits a proxy can make to any hosted game without touching server-side dynamics.
Applying all five to a world they were not designed against is the first real
test of that.  §4 of `exam/SEALED_DRILL.md` reports what happened; one operator
does not survive contact.

---------------------------------------------------------------------------
What it does not do
---------------------------------------------------------------------------

It does not register a rubric.  `exam/grading/registry.py:33` is a frozen,
ordered tuple whose digest is stamped into every sheet and every archived
manifest; appending to it to score a rehearsal would move the digest under four
shipped papers.  So the drill marks with its own loop and then hands the real
`Report` and key to the real `exam.grading.confusion_matrix.per_class_confusion`
-- the statistics half, which is the half V6 asks about, is the shipped code.
The marking ladder deliberately mirrors `rubrics_verdict.grade_verdict`'s, and
`exam/tests/test_sealed_drill.py` pins the two together so they cannot drift
silently.
"""

from typing import Any, Dict, List, Optional, Sequence, Tuple

import argparse
import inspect
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXAM = os.path.dirname(HERE)
REPO = os.path.dirname(EXAM)
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from exam import drill_certificates as certs  # noqa: E402
from exam import guard  # noqa: E402
from exam.drill_wrapper import replay, solve  # noqa: E402
from exam.grading.confusion_matrix import per_class_confusion  # noqa: E402
from exam.model import (Item, ItemScore, Paper, Report, Submission,  # noqa: E402
                        sha256, sha256_text, write_json)
from proxy.variants import Variant  # noqa: E402
from worldgen.core.world import GridWorld  # noqa: E402
from worldgen.generate import BY_ID  # noqa: E402

PROMPT_ID = "V6-exam-on-sealed-dryrun"
PAPER_ID = "drill-verdict-worldgen"
QUESTION_TYPE = "verdict"
RUBRIC_ID = "drill.worldgen.claim_and_certificate"
DEFAULT_OUT = os.path.join(EXAM, "runs", "20260729T1030Z-V6-exam-on-sealed-dryrun")

#: Equal on both claims, on purpose.  `exam/papers/verdict.py:96-106` records
#: what happened when they were not: `points` rides on the sheet, so a cheater
#: read the class straight off it and scored 17/17 without looking at a board.
POINTS = 2.0

#: The agent's colour in every worldgen render (`worldgen/core/types.py:42`).
#: An `observation_loss` keyed on it means "standing here loses".
AGENT_COLOUR = 6

#: The commands an examinee may submit in a witness, and the cap on how many.
#: Both mirror `exam/grading/rubrics_verdict.py:107` -- a marker replays what it
#: is sent, so the length and the alphabet are the marker's problem, not the
#: examinee's. RESET is deliberately absent: it is not an action of an episode.
COMMANDS: Tuple[str, ...] = ("UP", "DOWN", "LEFT", "RIGHT")
MAX_WITNESS = 5000


# --------------------------------------------------------------------------
# The variant catalogue.
#
# Every entry states its truth *by construction* in `justification` and, where
# the frozen grammar has a form for it, in `certificate`.  Nothing here was
# written by running the world first; the oracle runs afterwards and the drill
# reports both.
# --------------------------------------------------------------------------

VARIANTS: Tuple[Dict[str, Any], ...] = (
    {
        "key": "walk-forbid-down",
        "world": "t1-walk-maze",
        "klass": "small_unsolvable",
        "claim": "unsolvable",
        "operators": [{"op": "forbid_action", "action": "DOWN"}],
        "justification":
            "t1-walk-maze has no mechanisms at all, so the agent's row changes "
            "only by the command it issues: UP decreases it by one, DOWN "
            "increases it by one, LEFT and RIGHT leave it alone. Forbidding "
            "DOWN removes the only command that can increase the row. The agent "
            "starts on row 1 and the goal is on row 5, so the row would have to "
            "increase by four and cannot increase at all. Unsolvable by "
            "construction, with no reference to the board's walls.",
        "certificate": {"kind": "invariant", "invariant": "agent_row",
                        "initial_value": 1, "goal_value": 5},
    },
    {
        "key": "walk-forbid-up",
        "world": "t1-walk-maze",
        "klass": "solvable_hard",
        "claim": "solvable",
        "operators": [{"op": "forbid_action", "action": "UP"}],
        "justification":
            "The mirror of walk-forbid-down, and the reason it is here: the "
            "same operator on the same board, one command over. The route "
            "DOWN DOWN DOWN DOWN RIGHT RIGHT RIGHT RIGHT RIGHT RIGHT walks down "
            "column 1 and then along row 5, and issues no UP, so forbidding UP "
            "leaves it intact. Solvable, witnessed by construction. A framework "
            "that says unsolvable here is producing a false alarm.",
        "certificate": None,
        "witness": ["DOWN", "DOWN", "DOWN", "DOWN",
                    "RIGHT", "RIGHT", "RIGHT", "RIGHT", "RIGHT", "RIGHT"],
    },
    {
        "key": "walk-remap-down-to-up",
        "world": "t1-walk-maze",
        "klass": "small_unsolvable",
        "claim": "unsolvable",
        "operators": [{"op": "remap_action", "from": "DOWN", "to": "UP"}],
        "justification":
            "The same row invariant reached by a different operator. After the "
            "remap the four commands perform UP, UP, LEFT and RIGHT: the "
            "alphabet still has four commands, and the board is untouched, but "
            "no command performs DOWN any more. The row can never increase, and "
            "the goal is four rows below the start. This variant matters "
            "because it is the case where a remap is not a relabelling -- it is "
            "non-injective, and the action it collides onto is the one the "
            "route needed.",
        "certificate": {"kind": "invariant", "invariant": "agent_row",
                        "initial_value": 1, "goal_value": 5},
    },
    {
        "key": "walk-remap-left-to-right",
        "world": "t1-walk-maze",
        "klass": "solvable_hard",
        "claim": "solvable",
        "operators": [{"op": "remap_action", "from": "LEFT", "to": "RIGHT"}],
        "justification":
            "Also non-injective, also loses a command, and does not bite: the "
            "route down column 1 and along row 5 never issues LEFT, so removing "
            "LEFT from the alphabet costs nothing. The pair with "
            "walk-remap-down-to-up is the point -- 'the variant destroyed an "
            "action' is not on its own a reason to answer unsolvable, and an "
            "arm that reasons from the operator's shape rather than the board "
            "gets exactly one of these two right.",
        "certificate": None,
        "witness": ["DOWN", "DOWN", "DOWN", "DOWN",
                    "RIGHT", "RIGHT", "RIGHT", "RIGHT", "RIGHT", "RIGHT"],
    },
    {
        "key": "walk-budget-nine",
        "world": "t1-walk-maze",
        "klass": "small_unsolvable",
        "claim": "unsolvable",
        "operators": [{"op": "step_limit", "limit": 9}],
        "justification":
            "A counting argument, not a search. The agent starts at (1,1) and "
            "the goal is (5,7); one command moves it at most one cell along one "
            "axis, so any winning sequence has length at least "
            "|5-1| + |7-1| = 10. The variant allows nine commands. Ten is more "
            "than nine, so no winning sequence fits, whatever the walls look "
            "like.",
        "certificate": {"kind": "counting", "bound": 10, "limit": 9},
    },
    {
        "key": "walk-budget-ten",
        "world": "t1-walk-maze",
        "klass": "solvable_hard",
        "claim": "solvable",
        "operators": [{"op": "step_limit", "limit": 10}],
        "justification":
            "One command more than walk-budget-nine, which is the whole "
            "content: the Manhattan bound of 10 is achieved, not merely "
            "approached, because column 1 and row 5 are both clear. The "
            "ten-command route is the witness. This is the tight side of the "
            "boundary, and it is here so that a budget argument cannot be "
            "waved at any budget -- a framework that answers unsolvable "
            "whenever it sees a step_limit fails this item.",
        "certificate": None,
        "witness": ["DOWN", "DOWN", "DOWN", "DOWN",
                    "RIGHT", "RIGHT", "RIGHT", "RIGHT", "RIGHT", "RIGHT"],
    },
    {
        "key": "walk-cut-row-four",
        "world": "t1-walk-maze",
        "klass": "small_unsolvable",
        "claim": "unsolvable",
        "operators": [{"op": "observation_loss",
                       "cells": [[4, 1], [4, 7]], "value": AGENT_COLOUR}],
        "justification":
            "Row 4 of this board is '#.#####.#': every cell is wall except "
            "columns 1 and 7. The start is on row 1 and the goal on row 5, so "
            "every route crosses row 4, and it can only cross at (4,1) or "
            "(4,7). Declaring a loss on both cells cuts the board in two. This "
            "is a separation argument read off the layout -- no path is "
            "enumerated, and the two cells are exactly the frontier.",
        "certificate": {"kind": "cut_set", "cells": [[4, 1], [4, 7]]},
    },
    {
        "key": "walk-cut-half",
        "world": "t1-walk-maze",
        "klass": "solvable_hard",
        "claim": "solvable",
        "operators": [{"op": "observation_loss",
                       "cells": [[4, 1]], "value": AGENT_COLOUR}],
        "justification":
            "Half of walk-cut-row-four's cut, and therefore not a cut. With "
            "(4,1) lethal the column-1 descent is closed, but the second "
            "crossing at (4,7) is untouched and the route through row 1 "
            "columns 5-7, column 7 down, and row 5 leftward still reaches the "
            "goal. An incomplete separation proves nothing, and this item is "
            "the specificity test for that: the reasoning shape is identical "
            "to the item above and the answer is opposite.",
        "certificate": None,
        "witness": ["RIGHT", "RIGHT", "DOWN", "DOWN", "RIGHT", "RIGHT",
                    "UP", "UP", "RIGHT", "RIGHT", "DOWN", "DOWN", "DOWN",
                    "DOWN"],
    },
    {
        "key": "bridge-cut-column-three",
        "world": "t1-fragile-bridge",
        "klass": "small_unsolvable",
        "claim": "unsolvable",
        "operators": [{"op": "observation_loss",
                       "cells": [[1, 3], [3, 3]], "value": AGENT_COLOUR}],
        "justification":
            "The start (1,1) and the goal (1,5) sit either side of column 3, "
            "and column 3 is open on rows 1, 2 and 3 only. (2,3) is walled in "
            "on both sides -- (2,2) and (2,4) are walls -- so its only "
            "neighbours are (1,3) and (3,3). Declaring a loss on those two "
            "therefore severs column 3 entirely, including the cell they "
            "surround. A second world is used here so the cut-set form is not "
            "demonstrated only on the one board it was written against, and "
            "this one carries a mechanism (consumable) while the maze carries "
            "none.",
        "certificate": {"kind": "cut_set", "cells": [[1, 3], [3, 3]]},
    },
    {
        "key": "walk-win-tighten-scoreless",
        "world": "t1-walk-maze",
        "klass": "small_unsolvable",
        "claim": "unsolvable",
        "operators": [{"op": "win_tighten",
                       "require": {"kind": "score_at_least", "value": 1}}],
        "justification":
            "This variant is in the drill to be reported, not to be admired. "
            "worldgen keeps no score -- its recorded trace carries t, frame, "
            "action and win, and nothing else -- so the body the wrapper sees "
            "always has score None. The frozen win_tighten rewrites WIN to "
            "NOT_FINISHED whenever the score is absent or below the "
            "requirement, so on a scoreless game it rewrites every win, at "
            "every requirement, unconditionally. The variant is unsolvable, but "
            "not because anything about this board is hard: the operator has "
            "degenerated from a tightening into a total ban. No certificate is "
            "offered because the frozen grammar has no form for 'the win "
            "condition is unsatisfiable because the game reports no score'.",
        "certificate": None,
    },
)


# --------------------------------------------------------------------------
# The sealed guardrail, fired inside the rehearsal
# --------------------------------------------------------------------------

def fire_the_guard() -> Dict[str, Any]:
    """Feed the guard every id the cut knows, and require the right answer to each.

    The first version of this probed one sealed id, its stem, and one synthetic
    control -- and the V6 adversarial pass showed that a guard broken for the
    other twenty sealed ids, and for all four dev-pile ids, still made this
    report `fired: True`. The docstring's own argument ("any one alone is
    satisfiable by a broken guard") was right and then taken at n=1.

    So the sweep is total:

    * all 21 sealed ids **and** all 21 short stems -> `SealedPileError`;
    * all 4 dev-pile ids -> refused too (`UnknownGameError`), because a dev game
      spent on a rehearsal is a dev game spent and that should take a decision,
      not a default (`exam/DECISIONS.md` D-EX-007);
    * every world in the worldgen roster -> **accepted**. A guard that refuses
      everything passes every refusal test ever written.

    Ids are read from `piles.json` at run time and are redacted out of everything
    recorded here, so the evidence cannot become the leak.
    """
    evidence: Dict[str, Any] = {"checks": [], "counts": {}}

    def record(label: str, ok: bool, detail: str) -> None:
        evidence["checks"].append({"check": label, "passed": ok, "detail": detail})

    try:
        piles = guard.load_piles()          # verifies its own digest on load
    except Exception as exc:                # noqa: BLE001
        # M3: this used to escape and kill the run with a traceback, so a
        # doctored cut produced no DRILL.json and no RED block at all -- which
        # contradicted the header's promise that every gate is evaluated.
        record("cut_integrity", False,
               "%s: %s" % (type(exc).__name__, str(exc)[:160]))
        evidence["fired"] = False
        return evidence
    record("cut_integrity", True, "piles.json verified against its own digest")

    prov = piles.provenance()
    evidence["cut_digest"] = prov["piles_sha256"]
    evidence["n_sealed"] = len(piles.sealed_pile)

    def redact(text: str) -> str:
        for name in sorted(piles.sealed_pile, key=len, reverse=True):
            text = text.replace(name, "<sealed>").replace(name.split("-", 1)[0], "<sealed>")
        return text[:160]

    def sweep(label: str, probes: Sequence[str], want) -> None:
        bad = []
        for probe in probes:
            try:
                guard.assert_synthetic_world(probe)
            except want:
                continue
            except Exception as exc:        # noqa: BLE001
                bad.append("%s -> %s" % (redact(probe), type(exc).__name__))
            else:
                bad.append("%s -> NOT REFUSED" % redact(probe))
        evidence["counts"][label] = {"probed": len(probes), "failed": len(bad)}
        record(label, not bad,
               "all %d refused with %s" % (len(probes), want.__name__) if not bad
               else "; ".join(bad[:6]))

    sealed = list(piles.sealed_pile)
    sweep("sealed_full_ids", sealed, guard.SealedPileError)
    sweep("sealed_short_ids", [i.split("-", 1)[0] for i in sealed], guard.SealedPileError)
    sweep("dev_pile_ids", list(piles.dev_pile), guard.UnknownGameError)

    roster = sorted(set(guard.generated_worlds()) | {v["world"] for v in VARIANTS})
    accepted, refused = 0, []
    for world_id in roster:
        try:
            guard.assert_synthetic_world(world_id)
        except Exception as exc:            # noqa: BLE001
            refused.append("%s -> %s" % (world_id, type(exc).__name__))
        else:
            accepted += 1
    evidence["counts"]["synthetic_control"] = {"probed": len(roster),
                                               "failed": len(refused)}
    record("synthetic_control", not refused,
           "all %d worldgen worlds accepted, so the guard discriminates rather "
           "than refusing everything" % accepted if not refused
           else "; ".join(refused[:6]))

    evidence["fired"] = all(c["passed"] for c in evidence["checks"])
    return evidence


# --------------------------------------------------------------------------
# Build: specs, truth by construction, then the oracle
# --------------------------------------------------------------------------

def build_items(spec_dir: str, out_dir: str) -> Tuple[List[Item], List[Dict[str, Any]]]:
    """Emit every variant spec, check its certificate, and decide it exhaustively.

    Returns `(items, findings)`.  A finding is one variant's full record,
    including the two verdicts that the drill exists to compare.
    """
    os.makedirs(spec_dir, exist_ok=True)
    items: List[Item] = []
    findings: List[Dict[str, Any]] = []

    for entry in VARIANTS:
        world_id = entry["world"]
        guard.assert_synthetic_world(world_id)      # every world, every run
        world = GridWorld(BY_ID[world_id])

        variant_id = "drill-%s" % entry["key"]
        spec = {
            "variant_id": variant_id,
            "base_game": world_id,
            "base_level": world_id,
            "claim": entry["claim"],
            "justification": entry["justification"],
            "operators": entry["operators"],
            "notes": "sealed drill (%s); worldgen world standing in for a sealed "
                     "game. Zero API, zero sealed contact." % PROMPT_ID,
        }
        variant = Variant(spec)                     # the frozen validator, first
        path = os.path.join(spec_dir, "%s.json" % variant_id)
        write_json(path, spec)
        loaded = Variant.load(path)
        with open(path, "r", encoding="utf-8", newline="") as handle:
            text = handle.read()
        spec_record = {
            "variant_id": loaded.variant_id,
            "spec_sha256": loaded.sha256,
            # Relative to the run, not to the repo. A run written outside the
            # repo (the determinism check writes to a temp dir) would otherwise
            # embed `..\..\..\Temp\...` in a byte-reproducible truth file, and
            # the digest would then depend on where the run happened to land.
            "spec_file": os.path.relpath(path, out_dir).replace(os.sep, "/"),
            "spec_file_sha256": sha256_text(text),
            "operators": [op["op"] for op in loaded.operators],
        }

        # (1) the constructive side -- what Phase 4 will have, and all it will have
        cert = entry.get("certificate")
        cert_check = certs.check(world.spec, loaded.operators, cert)

        # (2) the side Phase 4 will never have
        oracle = solve(world, loaded)

        # (3) a declared witness is replayed rather than believed
        witness = entry.get("witness")
        witness_check: Optional[Dict[str, Any]] = None
        if witness is not None:
            outcome = replay(world, loaded, witness)
            witness_check = {"declared": witness, "wins": bool(outcome["win"]),
                             "commands_used": outcome["used"]}

        agrees = (entry["claim"] == "unsolvable") == (not oracle["solvable"])
        findings.append({
            "key": entry["key"], "variant_id": variant_id, "world": world_id,
            "class": entry["klass"], "claimed": entry["claim"],
            "operators": [op["op"] for op in loaded.operators],
            "certificate_offered": cert is not None,
            "certificate_kind": (cert or {}).get("kind"),
            "certificate_check": cert_check,
            "oracle_solvable": oracle["solvable"],
            "oracle_witness_length": (None if oracle["witness"] is None
                                      else len(oracle["witness"])),
            "oracle_nodes": oracle["reachable_nodes"],
            "witness_check": witness_check,
            "construction_agrees_with_oracle": agrees,
            "spec": spec_record,
        })

        items.append(Item(
            item_id=_opaque_id(entry["key"]),
            rubric_id=RUBRIC_ID,
            points=POINTS,
            paper=_sheet_side(world, entry),
            truth={
                "claim": entry["claim"],
                "class": entry["klass"],
                "world_id": world_id,
                "operators": loaded.operators,
                "certificate": cert,
                "witness": witness,
                "oracle_solvable": oracle["solvable"],
                "oracle_witness": oracle["witness"],
                "justification": entry["justification"],
                "spec": spec_record,
                "search_credible": True,
                "weights": {"verdict": 0.5, "justification": 0.5},
            },
            leak_probes=[variant_id, spec_record["spec_sha256"],
                         entry["justification"][:80], entry["klass"],
                         json.dumps(cert, sort_keys=True) if cert else "",
                         " ".join(witness) if witness else ""],
            tags=("verdict", "worldgen-drill"),
        ))

    # S2: `VARIANTS` alternates unsolvable / solvable, and `Paper.sheet()` keeps
    # order, so the 1-based index alone answered 9 of 10 items for an examinee
    # that read nothing else. `exam/papers/verdict.py:96-106` records the same
    # channel one field over -- a cheater that read the class off `points`.
    # Shuffled by a digest of the item id, so the order is fixed, reproducible,
    # and carries nothing.
    items.sort(key=lambda item: sha256_text("%s|%s" % (PAPER_ID, item.item_id)))
    return items, findings


def _opaque_id(key: str) -> str:
    """An item id that carries nothing.

    `exam/papers/verdict.py:493` does the same and for the same reason: a
    readable id is a channel. `drill-walk-budget-nine` beside
    `drill-walk-budget-ten` tells a reader which of the pair is the tight one
    before they have looked at a board, and the two are meant to be
    indistinguishable except by reasoning.
    """
    return "dq-" + sha256_text("%s|%s" % (PAPER_ID, key))[:10]


def _sheet_side(world: GridWorld, entry: Dict[str, Any]) -> Dict[str, Any]:
    """What the examinee sees: the board, the wrapper's edit, and the question.

    The class is not here, the claim is not here, and the justification is not
    here.  `points` is equal on every item so it carries nothing either.
    """
    spec = world.spec
    return {
        "kind": "verdict",
        "world": spec.world_id,
        "board": {"grid": list(spec.layout),
                  "start": list(spec.agent_start),
                  "goal": list(spec.goal)},
        "commands": list(("UP", "DOWN", "LEFT", "RIGHT")),
        "wrapper_edit": entry["operators"],
        "question": "Under the wrapper edit shown, is this world solvable "
                    "within one episode? Answer 'solvable' or 'unsolvable', "
                    "and give a certificate (invariant, cut_set or counting) "
                    "or a witness.",
    }


# --------------------------------------------------------------------------
# Marking
# --------------------------------------------------------------------------

def grade(answer: Any, item: Item, run_dir: str) -> ItemScore:
    """The `rubrics_verdict.grade_verdict` ladder, on this drill's item shape.

    Half the marks are the claim and half are the reason, and the reason half is
    paid only for something checkable: a certificate that verifies, or a witness
    that replays to a win.  Being right without a reason is worth half, which is
    the point of the split -- an arm that guesses 'unsolvable' everywhere is
    right about half the time and must not be able to bank that as understanding.
    """
    truth = item.truth
    said = None
    if isinstance(answer, dict):
        said = answer.get("claim")
    detail: Dict[str, Any] = {"said": said}

    if said in (None, "abstain", "unknown", "unsure", "no_verdict"):
        detail["said"] = "abstain" if said is not None else None
        detail["reason"] = "abstained"
        return ItemScore(item_id=item.item_id, rubric_id=item.rubric_id,
                         awarded=0.0, possible=item.points,
                         verdict="abstained", detail=detail)
    if said not in ("solvable", "unsolvable"):
        detail["reason"] = "unparseable"
        return ItemScore(item_id=item.item_id, rubric_id=item.rubric_id,
                         awarded=0.0, possible=item.points,
                         verdict="wrong", detail=detail)
    if said != truth["claim"]:
        detail["reason"] = "wrong_claim"
        return ItemScore(item_id=item.item_id, rubric_id=item.rubric_id,
                         awarded=0.0, possible=item.points,
                         verdict="wrong", detail=detail)

    half = item.points * 0.5
    world = GridWorld(BY_ID[truth["world_id"]])
    if said == "unsolvable":
        offered = answer.get("certificate")
        if offered is not None and not isinstance(offered, dict):
            # `rubrics_verdict.py:107` says it plainly: "a rubric is handed
            # untrusted input; 'replay whatever they sent' is a denial-of-service
            # surface". A string here used to reach `cert.get` and abort the whole
            # marking run with an AttributeError -- one malformed submission
            # taking down everybody else's marks. Found by the V6 adversarial pass.
            detail["reason"] = "malformed_certificate"
            return ItemScore(item_id=item.item_id, rubric_id=item.rubric_id,
                             awarded=half, possible=item.points,
                             verdict="correct", detail=detail)
        if offered is None:
            detail["reason"] = "none"
            awarded = half
        else:
            check = certs.check(world.spec, truth["operators"], offered)
            detail["certificate_check"] = check
            if check["ok"]:
                detail["reason"] = "certificate"
                awarded = item.points
            else:
                detail["reason"] = "invalid_certificate"
                awarded = half
    else:
        offered = answer.get("witness")
        if offered is not None and (
                not isinstance(offered, list)
                or len(offered) > MAX_WITNESS
                or not all(isinstance(c, str) and c in COMMANDS for c in offered)):
            detail["reason"] = "malformed_witness"
            detail["witness_rejected"] = (
                "a witness must be a list of at most %d commands drawn from %s"
                % (MAX_WITNESS, ", ".join(COMMANDS)))
            return ItemScore(item_id=item.item_id, rubric_id=item.rubric_id,
                             awarded=half, possible=item.points,
                             verdict="correct", detail=detail)
        if offered is None:
            detail["reason"] = "none"
            awarded = half
        else:
            # `spec_file` is repo-relative on purpose: an absolute path in a
            # truth file is a machine-local value in a byte-reproducible
            # artefact, which is the defect `exam/runs/p15-rehearsal-01`
            # already carries in its `report_path` entries.
            variant = Variant.load(os.path.join(
                run_dir, truth["spec"]["spec_file"].replace("/", os.sep)))
            outcome = replay(world, variant, offered)
            detail["witness_replay"] = {"wins": bool(outcome["win"]),
                                        "used": outcome["used"]}
            if outcome["win"]:
                detail["reason"] = "witness"
                awarded = item.points
            else:
                detail["reason"] = "invalid_witness"
                awarded = half
    return ItemScore(item_id=item.item_id, rubric_id=item.rubric_id,
                     awarded=awarded, possible=item.points,
                     verdict="correct", detail=detail)


def mark(paper: Paper, submission: Submission, rubric_digest: str,
         run_dir: str) -> Report:
    scores = [grade(submission.answers.get(item.item_id), item, run_dir)
              for item in paper.items]
    return Report(paper_id=paper.paper_id, examinee_id=submission.examinee_id,
                  question_type=paper.question_type,
                  rubric_digest=rubric_digest,
                  scores=scores, meta={"rubric_id": RUBRIC_ID})


#: The fakes.  `oracle` and `null` fix the two ends of the scale by
#: construction; `bluffer` and `contrarian` are the two single-answer arms, and
#: they exist to prove that sensitivity and specificity are genuinely separate
#: numbers -- the bluffer must score 1.0 / 0.0 and the contrarian 0.0 / 1.0.  A
#: marker that reports one blended accuracy cannot tell them apart, which is
#: exactly the fault `exam/grading/selftest.py:453` injects on the real marker.
FAKES = ("oracle", "null", "bluffer", "contrarian", "claim_only")


def fake_answers(mode: str, paper: Paper) -> Dict[str, Any]:
    answers: Dict[str, Any] = {}
    for item in paper.items:
        truth = item.truth
        if mode == "null":
            continue
        if mode == "bluffer":
            answers[item.item_id] = {"claim": "unsolvable"}
        elif mode == "contrarian":
            answers[item.item_id] = {"claim": "solvable"}
        elif mode == "claim_only":
            answers[item.item_id] = {"claim": truth["claim"]}
        elif mode == "oracle":
            answer: Dict[str, Any] = {"claim": truth["claim"]}
            if truth["certificate"] is not None:
                answer["certificate"] = truth["certificate"]
            if truth["witness"] is not None:
                answer["witness"] = truth["witness"]
            answers[item.item_id] = answer
    return answers


# --------------------------------------------------------------------------
# The run
# --------------------------------------------------------------------------

def _git(*args: str) -> str:
    try:
        return subprocess.run(["git"] + list(args), cwd=REPO, check=False,
                              capture_output=True, text=True).stdout.strip()
    except OSError:
        return ""


def _gates(payload: Dict[str, Any]) -> List[str]:
    """Every condition that makes the drill red, evaluated in full.

    Nothing here short-circuits: a rehearsal that stops at the first problem
    tells you about one problem.
    """
    failures: List[str] = []
    if not payload["guard"]["fired"]:
        for check in payload["guard"]["checks"]:
            if not check["passed"]:
                failures.append("guard: %s -- %s" % (check["check"], check["detail"]))
    for finding in payload["findings"]:
        if not finding["construction_agrees_with_oracle"]:
            failures.append(
                "%s: constructed truth says %s, exhaustive oracle says %s"
                % (finding["key"], finding["claimed"],
                   "solvable" if finding["oracle_solvable"] else "unsolvable"))
        if finding["certificate_offered"] and not finding["certificate_check"]["ok"]:
            failures.append("%s: certificate refused -- %s"
                            % (finding["key"], finding["certificate_check"]["why"]))
        wc = finding["witness_check"]
        if wc is not None and not wc["wins"]:
            failures.append("%s: declared witness does not win on replay" % finding["key"])
    cal = payload["calibration"]
    # The oracle's band is *computed*, not assumed to be 1.0. An item whose
    # claim the frozen certificate grammar has no form for caps ground truth
    # itself at the verdict half, and pretending otherwise would turn a real
    # property of the frozen library into a mysterious calibration failure.
    # The cap is reported as a finding either way -- see `reason_ceiling`.
    if abs(cal["oracle"]["fraction"] - payload["reason_ceiling"]["fraction"]) > 1e-9:
        failures.append(
            "calibration: the oracle scored %.4f but every item it can fully "
            "answer sums to %.4f"
            % (cal["oracle"]["fraction"], payload["reason_ceiling"]["fraction"]))
    if abs(cal["null"]["fraction"] - 0.0) > 1e-9:
        failures.append("calibration: null scored %.4f, expected 0.0"
                        % cal["null"]["fraction"])
    if abs(cal["claim_only"]["fraction"] - 0.5) > 1e-9:
        failures.append(
            "calibration: an arm with every claim right and no reason at all "
            "must score exactly half, got %.4f -- the split between the verdict "
            "half and the reason half has moved"
            % cal["claim_only"]["fraction"])
    blf = cal["bluffer"]["confusion"]["overall"]
    if blf["sensitivity"] != 1.0 or blf["specificity"] != 0.0:
        failures.append(
            "calibration: the bluffer must be sensitivity 1.0 / specificity 0.0, "
            "got %r / %r" % (blf["sensitivity"], blf["specificity"]))
    con = cal["contrarian"]["confusion"]["overall"]
    if con["sensitivity"] != 0.0 or con["specificity"] != 1.0:
        failures.append(
            "calibration: the contrarian must be sensitivity 0.0 / specificity "
            "1.0, got %r / %r" % (con["sensitivity"], con["specificity"]))
    if payload["leakage"]["failures"]:
        failures.extend("leakage: %s" % f for f in payload["leakage"]["failures"])
    return failures


def _cut_provenance() -> Dict[str, Any]:
    """Which cut this paper was set under, without naming a live game.

    `guard.provenance()` carries `dev_pile` as four ids, and this block goes on
    the *sheet*. `exam/guard.py:15-16` states the rule as no business naming any
    live game, dev pile included, and `provenance()` withholds the worldgen
    roster for exactly that reason -- an id on a sheet is a channel. The digest
    is what pins the cut; the names add nothing a reader of a rehearsal needs.
    Counts are kept so the block still says which cut it was.
    """
    prov = guard.provenance()
    return {"cut_version": prov["cut_version"],
            "piles_sha256": prov["piles_sha256"],
            "n_sealed": prov["n_sealed"],
            "n_dev": len(prov["dev_pile"]),
            "note": "ids withheld: this block rides on the sheet, and a sheet "
                    "has no business naming a live game, dev pile included."}


def _reason_ceiling(paper: Paper) -> Dict[str, Any]:
    """The best score ground truth itself can reach, and where it cannot reach full.

    Half of every item is the reason, and the reason half is only payable
    against something checkable. An unsolvable item with no certificate in the
    frozen grammar therefore caps *the oracle* at half -- not because the oracle
    is wrong but because the library has no way to say why it is right.

    This is computed rather than assumed so that the fact surfaces as a named
    item in the run record instead of as an unexplained 0.95 in a calibration
    band. `exam/SEALED_DRILL.md` §4 is where it is argued; here it is only
    measured.
    """
    capped, total = [], 0.0
    for item in paper.items:
        truth = item.truth
        reachable = item.points
        if truth["claim"] == "unsolvable" and truth["certificate"] is None:
            reachable = item.points * 0.5
            capped.append({"item_id": item.item_id,
                           "variant_id": truth["spec"]["variant_id"],
                           "why": "the claim is unsolvable and the frozen "
                                  "certificate grammar (invariant / cut_set / "
                                  "counting) has no form for it, so the reason "
                                  "half is unpayable to anyone, ground truth "
                                  "included"})
        elif truth["claim"] == "solvable" and truth["witness"] is None:
            reachable = item.points * 0.5
            capped.append({"item_id": item.item_id,
                           "variant_id": truth["spec"]["variant_id"],
                           "why": "solvable with no declared witness"})
        total += reachable
    possible = sum(i.points for i in paper.items)
    return {"awarded": round(total, 6), "possible": possible,
            "fraction": round(total / possible, 6) if possible else 0.0,
            "capped_items": capped}


def _leak_check(paper: Paper, sheet: Dict[str, Any]) -> Dict[str, Any]:
    """Does any item's answer appear in what the examinee is handed?

    Local rather than `exam.leakage.check_paper`, and the reason is recorded in
    SEALED_DRILL.md §5: that gate walks `exam/papers/__init__.py`'s `BUILDERS`
    and refuses all twenty worldgen papers today for a cause V7 already filed
    and nobody has fixed. Borrowing a red gate would make this drill red for
    somebody else's defect; reimplementing the *probe* half is cheap and is
    what actually protects this paper.
    """
    blob = json.dumps(sheet, sort_keys=True, ensure_ascii=False)
    failures: List[str] = []
    for item in paper.items:
        for probe in item.leak_probes:
            if probe and str(probe) in blob:
                failures.append("%s: %r reaches the sheet" % (item.item_id, probe[:60]))
    return {"probes": sum(len(i.leak_probes) for i in paper.items),
            "failures": failures}


def run(out_dir: str) -> Dict[str, Any]:
    with guard.no_network():
        spec_dir = os.path.join(out_dir, "variant_specs")
        guard_evidence = fire_the_guard()
        items, findings = build_items(spec_dir, out_dir)

        paper = Paper(paper_id=PAPER_ID, question_type=QUESTION_TYPE,
                      instructions=_sheet_side.__doc__ or "",
                      items=items, world=_cut_provenance(),
                      notes={"classes": sorted({f["class"] for f in findings}),
                             "prompt_id": PROMPT_ID})
        # The digest binds the paper to the code that marks it. The registry's
        # own digest would be a lie here -- this drill's ladder is not in
        # `registry.RUBRIC_MODULES` -- so it is taken over the marking source
        # itself, which is the same property by the same means.
        rubric_digest = "drill:" + sha256_text(
            inspect.getsource(grade) + inspect.getsource(certs))[:32]
        sheet = paper.sheet(rubric_digest=rubric_digest)
        key = paper.key(rubric_digest=rubric_digest)

        calibration: Dict[str, Any] = {}
        for mode in FAKES:
            submission = Submission(examinee_id="fake-%s" % mode,
                                    paper_id=PAPER_ID,
                                    answers=fake_answers(mode, paper),
                                    capabilities=() if mode == "null" else ("answers",))
            report = mark(paper, submission, rubric_digest, out_dir)
            calibration[mode] = {
                "fraction": report.fraction,
                "awarded": report.awarded, "possible": report.possible,
                "confusion": per_class_confusion(report, key, positive="unsolvable"),
            }

        payload = {
            "prompt_id": PROMPT_ID,
            "paper_id": PAPER_ID,
            "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
            "base_commit": _git("rev-parse", "HEAD"),
            "python": sys.version.split()[0],
            "guard": guard_evidence,
            "findings": findings,
            "calibration": calibration,
            "leakage": _leak_check(paper, sheet),
            "passive": {"api_calls": 0, "network": 0, "sealed_pile_reads": 0,
                        "game_spend_usd": 0.0,
                        "model_calls_on_any_generation_path": 0},
            "coverage": {
                "operators_exercised": sorted({
                    op for f in findings for op in f["operators"]}),
                "certificate_kinds_exercised": sorted({
                    f["certificate_kind"] for f in findings
                    if f["certificate_kind"]}),
                "classes_present": sorted({f["class"] for f in findings}),
                "classes_absent": ["large_unsolvable"],
                "classes_absent_because":
                    "worldgen's largest world has 2654 reachable states "
                    "(t3-full-house), so no world in the catalogue can stand in "
                    "for a state space exhaustive search cannot reach. Class "
                    "(ii) of Theoria.md:259 is rehearsed in procedure only, "
                    "never in difficulty. Recorded rather than simulated.",
            },
        }
        payload["reason_ceiling"] = _reason_ceiling(paper)
        payload["failures"] = _gates(payload)
        payload["green"] = not payload["failures"]

        write_json(os.path.join(out_dir, "sheet.json"), sheet)
        write_json(os.path.join(out_dir, "truth.json"), key)
        write_json(os.path.join(out_dir, "DRILL.json"), payload)
        return payload


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="the Phase 4 sealed drill")
    parser.add_argument("--out", default=DEFAULT_OUT)
    args = parser.parse_args(argv)
    payload = run(args.out)

    print("sealed drill -- %d variants over %d worlds"
          % (len(payload["findings"]),
             len({f["world"] for f in payload["findings"]})))
    print("  guard fired          %s" % ("yes" if payload["guard"]["fired"] else "NO"))
    agree = sum(1 for f in payload["findings"]
                if f["construction_agrees_with_oracle"])
    print("  construction vs oracle  %d/%d agree" % (agree, len(payload["findings"])))
    certified = sum(1 for f in payload["findings"]
                    if f["certificate_offered"] and f["certificate_check"]["ok"])
    print("  certificates checked    %d" % certified)
    for mode in FAKES:
        cell = payload["calibration"][mode]["confusion"]["overall"]
        print("  %-11s %.4f   sens %-6s spec %-6s"
              % (mode, payload["calibration"][mode]["fraction"],
                 cell["sensitivity"], cell["specificity"]))
    if payload["failures"]:
        print("\nRED:")
        for line in payload["failures"]:
            print("  - %s" % line)
        return 1
    print("\nGREEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
