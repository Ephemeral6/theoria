"""The scorer the push manual's own header promises, and did not have.

`theory/push/domain.dsl:43-45` says, in the middle of the paragraph that admits
the generalisation:

    `runs/…/scoring_push_manual.json` replays this manual against every reachable
    transition of both worlds, including every vertical shove the explorer never
    reached, and reports the verdict.

That file did not exist.  A promised check with no reader is the A0 failure mode
wearing a disclaimer: `A0′_REPORT §1` is the record of a manual generalised from
one witness and wrong in three places, and the whole argument of the push
manual's header is that *this* generalisation is different because it gets
measured afterwards.  Until the measurement runs, the two are the same object.

## What is measured

Every reachable state of both `worldgen` worlds, crossed with all four actions —
not the transitions some trace happened to walk.  `worldgen/core/world.py:259`
already has a `reachable()`, and it is deliberately not called: it raises on its
own 200k limit (`world.py:270`), and a scorer whose failure mode is a traceback
cannot report the cap.  The BFS below caps and *says so in the artefact*, which
is the difference between a truncated measurement and a silent one.

## What "the manual predicts" means here, stated because it is a choice

The compiled predictor is a function on its own `State` dataclass, not on frames,
so scoring it against a world requires deciding how a world frame becomes a
manual state.  The choice made here is the manual's own reading and no more:

    the frame is scanned for the two colours the word table declares, and the
    unique cell carrying each one is that object's position

— which is exactly what `a6carry/rebuild.py:173-195` (`preflight`) does when the
protocol carries the pack onto a level, so the scorer inherits the arm's reading
rather than inventing a friendlier one.  It is then checked in both directions:
`render(state_from_frame(frame)) == frame` is asserted at every single pre-state
(`readback_mismatches` in the artefact), so a manual whose `BOARD` disagreed with
the world would be caught as a defect here rather than laundered into a
prediction.  Comparison is on rendered frames, cell by cell, never on internal
state — the two state spaces are not the same object and pretending they are is
how a scorer scores itself.

## What "exercised" means, also a choice

A clause can be put to the test from either side, and the two are counted
separately because they can differ:

* `manual_guard_fired` — the compiled guard held on the pre-state.  The manual
  asserts something and can be wrong.
* `world_required` — the world's own ground-truth rule tag
  (`world.py:196 explain`) says the corresponding mechanism fired: `walk` in
  direction *d* implicates `step_d`, `push` in direction *d* implicates both
  `shove_d` and `block_d`, because `worldgen/mechanisms/push.py:81-85` moves the
  block and the agent in one `Outcome` and the manual needs two clauses to say
  so (`domain.dsl:131-137`).

`exercised` is the union.  A clause that fires without world support is
over-firing; one the world required and the manual did not fire is under-firing;
both are counted per rule even when the rendered frames happen to agree, since a
guard can be wrong about *why* while being right about *what*.

`blocked_by_wall` / `blocked_by_block` implicate **no clause**: under
`semantics: frame persist` (`domain.dsl:75`) the manual predicts those correctly
by staying silent, and crediting a clause for them would inflate every count in
the table.  They are scored in their own bucket.

## The distinction the artefact exists to draw

A clause exercised by zero transitions is **not** vindicated.  `never_checked`
and `checked_and_right` are separate lists in the verdict and neither is summed
into the other; `0 disagreements over 0 exercising transitions` is not evidence
and the artefact must not be readable as if it were.

Determinism: states sorted by `State.key()`, actions in `worldgen`'s own fixed
`ACTIONS` order, every list sorted before it is written, no timestamp, no
absolute path, `sort_keys=True`, `newline="\n"`.  Two runs are byte-identical.
"""

import importlib.util
import json
import os
import re
import sys
from collections import deque
from typing import Dict, List, Optional, Sequence, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap  # noqa: F401,E402

from a6carry.executors import WorldgenExecutor  # noqa: E402  (puts REPO on path)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUN_DIR = os.path.join(ROOT, "runs", "20260728T1800Z-A6-transfer-protocol")
DOMAIN_DSL = os.path.join(ROOT, "theory", "push", "domain.dsl")
OUT_PATH = os.path.join(RUN_DIR, "scoring_push_manual.json")

#: `(pack slug, worldgen world id)`.  The slug is the directory the protocol
#: already compiled the predictor into (`runs/…/generated/<slug>/theory.py`), so
#: the scorer grades the artefact the protocol actually produced rather than a
#: fresh compile of its own — `a6carry/forms.compile_forms` would give a second
#: predictor and a second thing to keep in step.  Carry direction is open →
#: corridor and PLAN.md says why: the corridor is the world that cannot supply a
#: second `push` witness, so books written there would be A0's mistake again.
WORLDS: Tuple[Tuple[str, str], ...] = (
    ("source_open", "t1-push-open"),
    ("transfer_corridor", "t1-push-corridor"),
)

#: The world emits `UP/DOWN/LEFT/RIGHT`; the manual speaks `push(Cart, up)`.
#: That naming is THEORIZE_LOG's adjudication and not the world's, which is why
#: it is written down here as well as at `cold-start-a0/certify/replay.py:35`
#: rather than derived: two copies that agree are a checkable claim, one copy
#: shared across tracks is a coupling A3's `_bootstrap` docstring refuses.
ACTION_NAMES: Dict[str, Tuple[str, str, str]] = {
    "UP": ("push", "Cart", "up"),
    "DOWN": ("push", "Cart", "down"),
    "LEFT": ("push", "Cart", "left"),
    "RIGHT": ("push", "Cart", "right"),
}

#: Every rule name in `domain.dsl`, in the file's own order.  Not derived from
#: the parse: if a clause is added upstream and this tuple is not updated, the
#: cross-check in `parse_evidence` fails loudly instead of the scorer quietly
#: grading eleven rules out of twelve.
RULE_ORDER: Tuple[str, ...] = (
    "step_up", "step_down", "step_left", "step_right",
    "shove_up", "shove_down", "shove_left", "shove_right",
    "block_up", "block_down", "block_left", "block_right",
)

#: `worldgen/core/world.py:270` raises at 200_000.  This scorer stops and reports
#: instead; both worlds are two orders of magnitude under it, so the branch is
#: never taken here and exists so that a larger world produces a *labelled*
#: partial measurement rather than an exception or a silent truncation.
STATE_CAP = 200_000

#: Enough disagreements to diagnose a class of failure, few enough that the
#: artefact stays readable.  `total_disagreements` is always the true count.
DISAGREEMENT_LIST_CAP = 50

#: Number words the manual's header might use for its own clause count.  The
#: header sentence is one of the things being scored, so the number is **read
#: from the file**, not written here.
#:
#: It was written here, as `= 8`, for exactly as long as it took the header to be
#: corrected — at which point the scorer went on reporting a disagreement with a
#: sentence that no longer existed.  A constant recording what another file says
#: is a copy that starts rotting on write; that is the same defect this module
#: was built to answer, reproduced inside the answer.
NUMBER_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
                "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
                "twelve": 12}
HEADER_SYMMETRY_CITATION = "theory/push/domain.dsl"


def header_symmetry_claim(domain_text):
    """What the manual's header claims about its own unwitnessed clause count.

    Returns `(count, line number, the sentence)` or `(None, None, None)` if the
    header stops making the claim — in which case there is nothing to disagree
    with, and the artefact says so rather than reporting a stale mismatch.
    """
    # Searched, not anchored: the sentence begins mid-line in the file
    # ("… explorer at all.  Six of the twelve clauses below …").  Anchoring it
    # to the start of the comment is how the first version of this function
    # returned `None` for a header that plainly states a number, which would
    # have reported "the header makes no claim" — a false all-clear, and a
    # worse failure than the stale constant it replaced.
    pattern = re.compile(
        r"\b(%s|\d+)\s+of\s+the\s+(%s|\d+)\s+clauses\b"
        % ("|".join(NUMBER_WORDS), "|".join(NUMBER_WORDS)), re.I)
    for number, line in enumerate(domain_text.splitlines(), start=1):
        if not line.lstrip().startswith("#"):
            continue
        match = pattern.search(line)
        if match is None:
            continue
        word = match.group(1).lower()
        return (NUMBER_WORDS.get(word, None) if not word.isdigit()
                else int(word)), number, line.strip().lstrip("# ")
    return None, None, None


def header_verdict(counted):
    """The header's claim about itself, against the brackets in the same file."""
    with open(DOMAIN_DSL, encoding="utf-8") as handle:
        claimed, line, sentence = header_symmetry_claim(handle.read())
    if claimed is None:
        return {
            "citation": HEADER_SYMMETRY_CITATION,
            "claimed_by_header": None,
            "counted_in_file": counted,
            "agrees": None,
            "note": ("the header no longer states a count of its own "
                     "unwitnessed clauses, so there is nothing to disagree "
                     "with; the file carries %d `ev: symmetry` clauses."
                     % counted),
        }
    return {
        "citation": "%s:%d" % (HEADER_SYMMETRY_CITATION, line),
        "claimed_by_header": claimed,
        "counted_in_file": counted,
        "agrees": claimed == counted,
        "sentence": sentence,
        "note": ("the header says %d, the file carries %d `ev: symmetry` "
                 "clauses.  Both numbers are read at run time — the count from "
                 "the `[ev: …]` brackets, the claim from the header sentence — "
                 "so neither is a copy that can rot.  They disagreed until "
                 "2026-07-29, when the header said eight."
                 % (claimed, counted)),
    }

_RULE_LINE = re.compile(
    r"^\s*rule\s+(?P<name>\w+)\s*\[\s*ev:\s*(?P<ev>\S+)\s+cov:\s*(?P<cov>\S+?)\s*\]")


# --------------------------------------------------------------- the manual's ev

def parse_evidence(dsl_path: str = DOMAIN_DSL) -> Dict[str, Dict[str, object]]:
    """`{rule: {ev, cov, witnessed}}`, read off the manual's own annotations.

    `witnessed` is `ev != "symmetry"` and nothing else.  Hardcoding the six
    witnessed names would make this module the authority on which clauses rest on
    a witness, and it is not: the manual is, in the `[ev: …]` brackets, and a
    scorer that decides for itself which clauses were guesses cannot catch a
    manual that later relabels one.
    """
    evidence: Dict[str, Dict[str, object]] = {}
    with open(dsl_path, "r", encoding="utf-8") as handle:
        for line in handle:
            match = _RULE_LINE.match(line)
            if match is None:
                continue
            evidence[match.group("name")] = {
                "ev": match.group("ev"),
                "cov": match.group("cov"),
                "witnessed": match.group("ev") != "symmetry",
            }
    missing = [r for r in RULE_ORDER if r not in evidence]
    extra = sorted(set(evidence) - set(RULE_ORDER))
    if missing or extra:
        raise ValueError(
            "domain.dsl no longer holds exactly the twelve rules this scorer "
            "grades: missing=%r unexpected=%r" % (missing, extra))
    return evidence


# ------------------------------------------------------------- the predictor

def load_theory(path: str, alias: str):
    """One generated `theory.py`, loaded under a caller-chosen module name.

    `cold-start-a0/certify/replay.py:43` is the same six lines with the name
    fixed to `a0_theory`.  The name is a parameter here because this scorer holds
    **two** predictors live at once — one per world — and a shared module name
    would make the second `exec_module` overwrite the first's globals, which is a
    silent wrong answer rather than an import error: `BOARD` and `GRID` are
    module-level in the generated backend (`source_open/theory.py:24-33`).
    """
    spec = importlib.util.spec_from_file_location(alias, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[alias] = module
    spec.loader.exec_module(module)
    return module


def state_from_frame(theory, frame: Sequence[Sequence[int]]):
    """A world frame -> the manual's `State`, or `None` with a reason.

    The manual's word table declares two objects and one colour each
    (`domain.dsl:62-63`), and `initial_state()` is where the compiled form
    records which colour is which; reading them from there rather than from a
    literal keeps the scorer honest about `worldgen` assigning colours per world
    out of a pool (`worldgen/core/types.py:POOL`) — a hardcoded `2` here would be
    the exact carried assumption `PACK.json`'s `requires.guard_colours` exists to
    stop travelling unchecked.

    `None` is returned rather than a guess when a colour is absent or duplicated:
    the manual's `count(Cart) = 1` / `count(Block) = 1` invariants
    (`domain.dsl:157-158`) are then false of the frame, and the honest report is
    "the manual cannot read this state", not a prediction from a fabricated one.
    """
    reference = theory.initial_state()
    height, width = theory.GRID
    found: Dict[str, List[Tuple[int, int]]] = {"Cart": [], "Block": []}
    wanted = {"Cart": reference.Cart_colour, "Block": reference.Block_colour}
    for r in range(height):
        for c in range(width):
            value = frame[r][c]
            for name, colour in wanted.items():
                if value == colour:
                    found[name].append((r, c))
    for name in ("Block", "Cart"):
        if len(found[name]) != 1:
            return None, "%s: %d cells carry colour %d, the manual declares one" % (
                name, len(found[name]), wanted[name])
    return theory.State(
        Block_pos=found["Block"][0], Block_colour=reference.Block_colour,
        Cart_pos=found["Cart"][0], Cart_colour=reference.Cart_colour,
    ), None


# ------------------------------------------------------------------- the worlds

def reachable_states(world, cap: int = STATE_CAP):
    """BFS from `initial()` over the four actions; returns `(states, capped)`.

    States come back sorted by `State.key()` (`worldgen/core/types.py:State.key`)
    so the transition order in the artefact is a property of the world and not of
    this process's dict iteration.  `capped` is returned rather than raised —
    see the module docstring; `world.py:270` takes the other option and a caller
    cannot report a traceback.
    """
    start = world.initial()
    seen = {start.key(): start}
    frontier = deque([start])
    capped = False
    from worldgen.core.types import ACTIONS  # noqa: E402  (read-only, the world's)
    while frontier:
        state = frontier.popleft()
        for action in ACTIONS:
            nxt = world.step(state, action)
            if nxt.key() in seen:
                continue
            if len(seen) >= cap:
                capped = True
                continue
            seen[nxt.key()] = nxt
            frontier.append(nxt)
    return [seen[k] for k in sorted(seen)], capped


def clauses_required(world_rule: str, action: str) -> Tuple[str, ...]:
    """The clause(s) the world's ground truth says had to fire, if any.

    The tags are `worldgen`'s, produced by the same code path that produces the
    successor state (`world.py:196`), so they cannot drift from the transition
    they label.  `blocked_by_wall` and `blocked_by_block` map to the empty tuple
    on purpose: the manual handles both by having no rule fire and letting
    `frame persist` (`domain.dsl:75`) hold the frame, so there is no clause to
    credit and counting one would inflate the per-rule table with transitions
    that test nothing.  `action_forbidden` (`world.py:34`) is likewise empty and
    is unreachable on these two specs, neither of which sets `flags`.
    """
    direction = ACTION_NAMES[action][2]
    if world_rule == "walk":
        return ("step_%s" % direction,)
    if world_rule == "push":
        # Two clauses, one mechanism: the event language gives a rule exactly one
        # object (`domain.dsl:131-137`), so `worldgen`'s single `push` Outcome —
        # which writes the block and moves the agent together
        # (`mechanisms/push.py:81-85`) — is two clauses on the manual's side.
        return ("block_%s" % direction, "shove_%s" % direction)
    return ()


def _blank_rule_row() -> Dict[str, int]:
    return {
        "exercised": 0,
        "correct": 0,
        "disagreements": 0,
        "manual_guard_fired": 0,
        "world_required": 0,
        "fired_without_world_support": 0,
        "required_but_not_fired": 0,
    }


def score_world(slug: str, world_id: str) -> Dict[str, object]:
    """Every reachable transition of one world, graded against its predictor."""
    from worldgen.core.types import ACTIONS  # noqa: E402

    executor = WorldgenExecutor(world_id)
    world = executor._world          # the same object `execute()` drives; read-only
    theory_path = os.path.join(RUN_DIR, "generated", slug, "theory.py")
    theory = load_theory(theory_path, "a6score_theory_%s" % slug)

    states, capped = reachable_states(world)

    rules = {name: _blank_rule_row() for name in RULE_ORDER}
    disagreements: List[Dict[str, object]] = []
    total_disagreements = 0
    checked = 0
    agreements = 0
    readback_mismatches = 0
    unreadable_states = 0
    ambiguous = 0
    # The two "no clause fired, and the world agrees nothing happened" tags, kept
    # out of the per-rule table but not out of the accounting: they are 61% of
    # the open world's transitions and dropping them would leave the totals
    # unexplained.
    no_clause = {"transitions": 0, "correct": 0, "by_world_rule": {}}

    first_frame = world.render(world.initial())
    first_state, first_reason = state_from_frame(theory, first_frame)
    first_frame_agrees = (
        first_reason is None
        and theory.render(theory.initial_state()) == first_frame
        and first_state.key() == theory.initial_state().key()
    )

    for state in states:
        pre_frame = world.render(state)
        manual_state, reason = state_from_frame(theory, pre_frame)
        if manual_state is None:
            # Cannot happen while `push`'s `block_count` invariant holds
            # (`mechanisms/push.py:125`), which is why it is counted rather than
            # asserted: an assertion here would delete the evidence that it did.
            unreadable_states += 1
            continue
        readback = theory.render(manual_state)
        if readback != pre_frame:
            readback_mismatches += 1

        for action in ACTIONS:
            checked += 1
            world_next, world_rule = world.explain(state, action)
            post_frame = world.render(world_next)

            act = ACTION_NAMES[action]
            fired = tuple(theory.fired(manual_state, act))
            required = clauses_required(world_rule, action)

            try:
                predicted = theory.render(theory.step(manual_state, act))
                ambiguity = None
            except theory.AmbiguousTransition as exc:
                # `conflict exclusive` (`domain.dsl:76`) makes two rules on one
                # object an error rather than a precedence question, so this is a
                # disagreement of the manual with itself and is recorded as one.
                predicted = None
                ambiguity = str(exc)
                ambiguous += 1

            agree = predicted == post_frame
            if agree:
                agreements += 1
            else:
                total_disagreements += 1

            for name in sorted(set(fired) | set(required)):
                row = rules[name]
                row["exercised"] += 1
                row["correct"] += 1 if agree else 0
                row["disagreements"] += 0 if agree else 1
                if name in fired:
                    row["manual_guard_fired"] += 1
                if name in required:
                    row["world_required"] += 1
                if name in fired and name not in required:
                    row["fired_without_world_support"] += 1
                if name in required and name not in fired:
                    row["required_but_not_fired"] += 1

            if not required:
                no_clause["transitions"] += 1
                no_clause["correct"] += 1 if agree else 0
                no_clause["by_world_rule"][world_rule] = (
                    no_clause["by_world_rule"].get(world_rule, 0) + 1)

            if not agree and len(disagreements) < DISAGREEMENT_LIST_CAP:
                cells = []
                if predicted is not None:
                    for r in range(theory.GRID[0]):
                        for c in range(theory.GRID[1]):
                            if predicted[r][c] != post_frame[r][c]:
                                cells.append({"cell": [r, c],
                                              "manual": predicted[r][c],
                                              "world": post_frame[r][c]})
                disagreements.append({
                    "action": action,
                    "ambiguous_transition": ambiguity,
                    "block": list(manual_state.Block_pos),
                    "cart": list(manual_state.Cart_pos),
                    "differing_cells": cells,
                    "manual_fired": sorted(fired),
                    "world_required": sorted(required),
                    "world_rule": world_rule,
                    "world_state_key": json.loads(json.dumps(state.key())),
                })

    return {
        "world_id": world_id,
        "pack_slug": slug,
        "predictor": os.path.relpath(theory_path, ROOT).replace(os.sep, "/"),
        "grid": list(theory.GRID),
        "reachable_states": len(states),
        "state_cap": STATE_CAP,
        "capped": capped,
        "transitions_checked": checked,
        "agreements": agreements,
        "disagreements": total_disagreements,
        "readback_mismatches": readback_mismatches,
        "unreadable_states": unreadable_states,
        "ambiguous_transitions": ambiguous,
        "first_frame_agrees": first_frame_agrees,
        "first_frame_note": (
            "the theorem `shove_is_relative_not_absolute` (domain.dsl:160) says "
            "an absolute reading of the shove would mis-render this world at "
            "frame 0; this is that check, and it passes only under the relative "
            "reading" if first_frame_agrees else
            "frame 0 already disagrees: %s" % (first_reason or "render mismatch")),
        "no_clause_transitions": {
            "by_world_rule": dict(sorted(no_clause["by_world_rule"].items())),
            "correct": no_clause["correct"],
            "note": (
                "wall- and block-blocked commands implicate no clause: the manual "
                "predicts them by having no rule fire and letting `frame persist` "
                "hold the frame (domain.dsl:75).  Counted here so the per-world "
                "totals add up, and excluded from the per-rule table so no clause "
                "is credited for a transition that tests nothing."),
            "transitions": no_clause["transitions"],
        },
        "rules": {name: dict(sorted(rules[name].items())) for name in RULE_ORDER},
        "disagreement_sample": disagreements,
    }


# ------------------------------------------------------------------ the verdict

def build_report() -> Dict[str, object]:
    evidence = parse_evidence()
    worlds = {slug: score_world(slug, world_id) for slug, world_id in WORLDS}

    unwitnessed = sorted(n for n in RULE_ORDER if not evidence[n]["witnessed"])
    witnessed = sorted(n for n in RULE_ORDER if evidence[n]["witnessed"])

    rules: Dict[str, object] = {}
    for name in RULE_ORDER:
        per_world = {slug: worlds[slug]["rules"][name] for slug, _ in WORLDS}
        exercised = sum(row["exercised"] for row in per_world.values())
        correct = sum(row["correct"] for row in per_world.values())
        wrong = sum(row["disagreements"] for row in per_world.values())
        if exercised == 0:
            # The load-bearing branch of this whole artefact.  A clause no
            # transition reaches has been *asserted*, not tested; the A0 failure
            # mode is exactly a clause in this state being read as a passing one.
            status = "never_exercised"
        elif wrong == 0:
            status = "checked_and_right"
        else:
            status = "checked_and_wrong"
        rules[name] = {
            "cov": evidence[name]["cov"],
            "ev": evidence[name]["ev"],
            "exercised_total": exercised,
            "correct_total": correct,
            "disagreements_total": wrong,
            "status": status,
            "witnessed": evidence[name]["witnessed"],
            "worlds": {slug: dict(per_world[slug]) for slug, _ in WORLDS},
        }

    never = sorted(n for n in unwitnessed if rules[n]["status"] == "never_exercised")
    right = sorted(n for n in unwitnessed if rules[n]["status"] == "checked_and_right")
    wrong = sorted(n for n in unwitnessed if rules[n]["status"] == "checked_and_wrong")

    total_disagreements = sum(w["disagreements"] for w in worlds.values())
    total_transitions = sum(w["transitions_checked"] for w in worlds.values())

    verdict = {
        "checked_and_right": right,
        "checked_and_wrong": wrong,
        "never_checked": never,
        "exercising_transitions": {n: rules[n]["exercised_total"] for n in unwitnessed},
        "exercising_transitions_by_world": {
            n: {slug: rules[n]["worlds"][slug]["exercised"] for slug, _ in WORLDS}
            for n in unwitnessed
        },
        "unwitnessed_clauses": unwitnessed,
        "witnessed_clauses": witnessed,
        "header_clause_count": header_verdict(len(unwitnessed)),
        "all_transitions_agree": total_disagreements == 0,
        "statement": (
            "%d of the %d unwitnessed clauses were exercised by at least one "
            "reachable transition and agreed with the world everywhere they were; "
            "%d were exercised by zero transitions across both worlds and are "
            "therefore NOT vindicated by this run -- they remain assertions."
            % (len(right), len(unwitnessed), len(never))
            if not wrong else
            "%d of the %d unwitnessed clauses DISAGREED with the world (%s); %d "
            "were never exercised at all."
            % (len(wrong), len(unwitnessed), ", ".join(wrong), len(never))),
        "reading_note": (
            "`never_checked` is not a pass.  A clause with zero exercising "
            "transitions has zero disagreements for the same reason an unopened "
            "box has no broken contents, and the two lists are kept apart here so "
            "no reader can sum them.  A0′_REPORT §1 is what happens when they are "
            "summed."),
    }

    return {
        "artefact": "scoring_push_manual.json",
        "promised_by": "theory/push/domain.dsl:43-45",
        "manual": "theory/push/domain.dsl",
        "method": {
            "action_vocabulary": {k: list(v) for k, v in sorted(ACTION_NAMES.items())},
            "comparison": "rendered frames, cell by cell; never internal state",
            "disagreement_list_cap": DISAGREEMENT_LIST_CAP,
            "enumeration": "BFS from initial() over the four actions, all four "
                           "actions applied at every reachable state",
            "exercised_definition": "union of (the manual's guard fired) and (the "
                                    "world's ground-truth rule tag implicates the "
                                    "clause); both components reported separately",
            "state_cap": STATE_CAP,
            "state_reading": "the unique cell carrying each declared object colour, "
                             "as a6carry/rebuild.py:preflight reads it",
        },
        "rules": rules,
        "totals": {
            "disagreements": total_disagreements,
            "transitions_checked": total_transitions,
            "reachable_states": sum(w["reachable_states"] for w in worlds.values()),
            "worlds": len(worlds),
        },
        "verdict": verdict,
        "worlds": worlds,
    }


def write_report(report: Dict[str, object], path: str = OUT_PATH) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(report, indent=2, sort_keys=True,
                                ensure_ascii=False) + "\n")
    return path


def summary_lines(report: Dict[str, object]) -> List[str]:
    out: List[str] = []
    for slug, _world_id in WORLDS:
        world = report["worlds"][slug]
        out.append("%-18s %3d states  %4d transitions  %4d agree  %d disagree%s"
                   % (slug, world["reachable_states"], world["transitions_checked"],
                      world["agreements"], world["disagreements"],
                      "  [CAPPED]" if world["capped"] else ""))
    out.append("")
    out.append("%-13s %-5s %-9s %-9s %s"
               % ("rule", "wit", "open", "corridor", "status"))
    for name in RULE_ORDER:
        row = report["rules"][name]
        cells = []
        for slug, _ in WORLDS:
            per = row["worlds"][slug]
            cells.append("%d/%d" % (per["correct"], per["exercised"]))
        out.append("%-13s %-5s %-9s %-9s %s"
                   % (name, "yes" if row["witnessed"] else "no",
                      cells[0], cells[1], row["status"]))
    out.append("")
    out.append(report["verdict"]["statement"])
    never = report["verdict"]["never_checked"]
    if never:
        out.append("NEVER EXERCISED (not vindicated): " + ", ".join(never))
    return out


def main() -> int:
    report = build_report()
    path = write_report(report)
    for line in summary_lines(report):
        print(line)
    print("")
    print("wrote %s" % os.path.relpath(path, ROOT).replace(os.sep, "/"))
    # Exit non-zero only on an actual disagreement.  A never-exercised clause is
    # not a failure of the manual, it is a limit of the two worlds, and making it
    # red here would push a future session to widen the scoring set until the
    # light goes green — which is the failure this artefact exists to name.
    return 1 if report["totals"]["disagreements"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
