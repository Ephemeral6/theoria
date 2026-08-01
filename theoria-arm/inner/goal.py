"""goal -- the winning condition, and the state of not having one.

**The reading this module was written from.** Four live carried legs on
2026-07-31 spent about $35 and 92 actions and completed zero levels. The
tempting conclusion is that the planner is weak. The record says something
else. Across those four legs `plan()` was called 56 times and returned
`no_goal_declared` 56 times -- 1 + 9 + 29 + 17, no other status, ever. Both
tiers of the ladder were skipped every time: `tiers` is `[]` in all 56
reports, so `fd_adapter` was never asked and BFS never expanded a node.
`commit.json` is `[]` in all four legs. Not one plan was produced, so not
one plan was executed, so not one plan could have failed.

The arm was not trying to win and missing. It was never trying.

And that is not a bug in `inner/plan.py`, which reports the situation
exactly right and has done since it was written:

    "the manual states no winning condition, so `is_goal` is `False`
    everywhere and no search can succeed. This is a gap in the manual, NOT a
    proof that the level is unsolvable"

It is not a bug in the desk either. Both carried manuals *know*. Each carries
a signed theorem saying the goal section is absent and why -- one argues a
goal true in the wrong states is worse than none, because the planner stops
at the first one; the other argues a wrong goal sends the searcher after a
fiction and costs the level. Those are good arguments. The desk made a
deliberate, defensible call and wrote it down.

The gap is between them. `no_goal_declared` is a leaf value that
`inner/loop.py` reads once, compares against `"sat"`, and drops. Nothing
accumulates it. Nothing in `summary()`, `RUN_STATE.json`, `turn_series.json`
or the campaign scoreboard says the arm held no winning condition for the
entire leg. The arm explored for 92 actions without knowing that it was
exploring, without a criterion for when to stop exploring, and its record
reads like a planner that kept failing rather than like an arm that never had
a target.

**What landed on master while this was being written, and how the two
differ.** A parallel session (`P12-probe-economics`, commit `79b948a1`) reached
the same diagnosis from the same artefacts and answered it at the other end:
`plan.surprises_from` now fires `heuristic_miss` on `no_goal_declared`, once
per playbook token, so the desk *is* told. That is the telling half and it is
already done; nothing here duplicates it or argues against it. What it does not
do is the recording half. After it, a leg that never holds a goal still reports
`levels_completed: 0` beside a plan history a reader has to reconstruct from
`plan.json` by hand, and the campaign scoreboard still cannot separate a
campaign that searched and lost from one that never searched. It also fires on
the playbook token alone: a rewritten playbook that still has no goal speaks up
again whether or not any new world has arrived to change the answer, which is
the case `proposal_due`'s third conjunct exists to refuse.

So the two compose: master's change opens the door, this one keeps the books
and decides when knocking is worth anything.

This module makes the state first class. It does three things and refuses to
do a fourth:

1. **Names the state.** `mode` is one of `planning`, `exploring_no_goal`,
   `no_manual` -- and `exploring_no_goal` further distinguishes an absence the
   manual *signed* (a theorem arguing for it) from an absence that is merely
   silence. A signed absence is a position; silence is an oversight. They read
   identically in today's record and they are not the same thing.

2. **Carries a criterion for proposing one**, with named refusals. See
   `proposal_due`. The criterion is taken from what the manuals themselves
   said they were waiting for: new world. Both said, in different words, that
   the goal could not be written until states they had not yet seen arrived.
   So the criterion is new *distinct* states since the last ask, not turns and
   not dollars -- a hundred turns over the same twelve states buys nothing.

3. **Says so in the record**, per turn and per run, including the zeros. A
   turn where the criterion said *no* prints its reason. A check that has
   never been seen to say no has not been shown to check anything.

**The fourth thing, refused.** It does not fire a surprise of its own.
`inner/surprise.py` closes the set at seven and says in the constructor that an
eighth is a change to `Theoria.md` 1.10(d), not to a file; master's change
already spends the one legitimate reuse (`heuristic_miss`, whose family's book
is the playbook, which is where the goal belongs) and firing a second time for
the same fact would double-call the desk for one gap. So the `propose` rung
buys no model call at all. It attaches the ask to the *next* theorize call that
a surprise -- master's `heuristic_miss` among them -- has already paid for.
Constraint 8 is untouched: no surprise, no model call, and the beat count does
not move.

**The rungs.** `off` is today's behaviour, byte for byte: nothing observed,
nothing recorded, nothing proposed. `record` observes and writes, changes no
decision and spends nothing. `propose` adds the rider to a theorize call the
loop was making anyway. Default is `off`, so this file is prepared and not
adopted; adopting it is a separate decision with its own evidence.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

#: The rungs, weakest first. `off` must leave every artefact identical to the
#: run that would have happened without this module at all.
PROTOCOLS = ("off", "record", "propose")
DEFAULT_PROTOCOL = "off"

#: How much *new* world must arrive before asking for a goal again.
#:
#: Four, matching `loop.MIN_NEW_FRAMES_BETWEEN_THEORIZE`, and for the same
#: reason: a desk re-asked against evidence it has already refused on returns a
#: differently-worded refusal at full price. Counted in DISTINCT states, not
#: frames -- a toggle pressed forty times produces forty frames and two states,
#: and it is the states that could carry a goal.
MIN_NEW_STATES_FOR_PROPOSAL = 4

#: How many times one leg may ask. Bounded so an arm that cannot name a goal
#: stops asking instead of spending every theorize on the same question. Three:
#: one on first evidence, one after the world has moved, one last.
MAX_PROPOSALS_PER_LEG = 3

#: A `goal ` clause in the DSL. The same test `inner/plan.py:_has_goal` makes,
#: kept here as one function so the loop and the planner cannot disagree about
#: whether a manual has a goal.
_GOAL_LINE = re.compile(r"^\s*goal\s+\S", re.M)

#: A theorem whose *name* argues about the absence of a goal. Both live
#: manuals signed their absence and both named the theorem for it, which is the
#: only machine-readable trace of a deliberate call that the DSL currently has.
#: Deliberately narrow: it must mention a goal AND mention absence. A theorem
#: merely mentioning "goal" is not a signature.
_THEOREM_NAME = re.compile(r"^\s*theorem\s+(\w+)", re.M)
_ABSENCE_WORDS = ("absent", "no_goal", "unsigned", "silence", "not_signed",
                  "without_a_goal")


def has_goal(theory_text: Optional[str]) -> bool:
    """Does this manual declare a winning condition at all."""
    return bool(_GOAL_LINE.search(theory_text or ""))


def absence_signature(theory_text: Optional[str]) -> Optional[str]:
    """The name of the theorem that argues the goal is absent, if there is one.

    Returns `None` when the manual has a goal, and `None` when it has neither a
    goal nor an argument for not having one. The two `None`s are different and
    the caller distinguishes them with `has_goal`; this function answers only
    "was the absence argued for".
    """
    if has_goal(theory_text):
        return None
    for name in _THEOREM_NAME.findall(theory_text or ""):
        low = name.lower()
        if "goal" in low and any(word in low for word in _ABSENCE_WORDS):
            return name
    return None


def read_manual(theory_text: Optional[str]) -> Dict[str, Any]:
    """What this manual says about winning, as three separable facts."""
    declared = has_goal(theory_text)
    signature = absence_signature(theory_text)
    return {
        "goal_declared": declared,
        "absence_is_signed": bool(signature),
        "absence_signature": signature,
    }


class GoalState:
    """The arm's standing relationship to a winning condition, over a leg.

    One instance per run. `observe()` is called once per turn, after `plan`,
    and returns the block that goes into the turn record. Everything it
    accumulates is derived from arguments it is given; it reads no globals and
    holds no reference to the loop, so it is testable without an arm.
    """

    def __init__(self, protocol: str = DEFAULT_PROTOCOL, *,
                 min_new_states: int = MIN_NEW_STATES_FOR_PROPOSAL,
                 max_proposals: int = MAX_PROPOSALS_PER_LEG) -> None:
        if protocol not in PROTOCOLS:
            raise ValueError(
                "%r is not a goal protocol. The rungs are %s, weakest first; "
                "%r is the default and means today's behaviour unchanged."
                % (protocol, ", ".join(PROTOCOLS), DEFAULT_PROTOCOL))
        self.protocol = protocol
        self.min_new_states = min_new_states
        self.max_proposals = max_proposals

        self.turns = 0
        self.turns_without_goal = 0
        self.turns_planning = 0
        self.turns_without_manual = 0
        self.actions_without_goal = 0
        self.first_no_goal_turn: Optional[int] = None
        self.goal_declared_ever = False
        self.absence_signature: Optional[str] = None
        #: Distinct states standing when the last proposal was made. `None`
        #: means none has been made, and the first ask is gated on the absolute
        #: count rather than on a delta from nothing.
        self.states_at_last_proposal: Optional[int] = None
        self.proposals: List[Dict[str, Any]] = []
        #: Plan statuses seen, counted. The whole finding of change B is a
        #: histogram with one bar in it, and this is that histogram.
        self.plan_status_counts: Dict[str, int] = {}
        self.mode = "not_started"

    @property
    def enabled(self) -> bool:
        return self.protocol != "off"

    # -- the criterion -----------------------------------------------------
    def proposal_due(self, *, mode: str, distinct_states: int,
                     has_predictor: bool) -> Dict[str, Any]:
        """Should the arm ask the desk to name a winning condition now.

        Four conjuncts, each of which must be able to say no on its own, and
        each of which says no in words that name the number it read. The
        returned dict is written into the record whether it is due or not: a
        criterion that only appears when it fires is indistinguishable from a
        criterion that always fires.
        """
        checks: List[Dict[str, Any]] = []

        checks.append({
            "check": "the manual declares no winning condition",
            "ok": mode == "exploring_no_goal",
            "read": mode,
        })
        checks.append({
            "check": "there is a compiled predictor for a goal to be written "
                     "against -- a goal clause naming objects the manual "
                     "cannot instantiate is not a goal",
            "ok": bool(has_predictor),
            "read": has_predictor,
        })

        if self.states_at_last_proposal is None:
            new_states = distinct_states
            basis = "distinct states seen so far (no proposal has been made yet)"
        else:
            new_states = distinct_states - self.states_at_last_proposal
            basis = ("distinct states since the last proposal (%d now, %d then)"
                     % (distinct_states, self.states_at_last_proposal))
        checks.append({
            "check": "enough new world has arrived to change the answer: %s "
                     ">= %d" % (basis, self.min_new_states),
            "ok": new_states >= self.min_new_states,
            "read": new_states,
        })

        checks.append({
            "check": "the leg's proposal budget is not spent (< %d)"
                     % self.max_proposals,
            "ok": len(self.proposals) < self.max_proposals,
            "read": len(self.proposals),
        })

        # Each check is phrased as the condition that must HOLD, so quoting it
        # verbatim as a refusal reads as its own opposite. R1b's records are
        # full of lines saying `refused_because: ["enough new world has
        # arrived to change the answer: distinct states since the last
        # proposal (5 now, 4 then) >= 4"]` -- an affirmative sentence given as
        # the reason nothing happened. The check text is kept (callers match on
        # substrings of it) and negated in front, with the number it read.
        refusals = ["NO -- %s [read: %s]" % (c["check"], c["read"])
                    for c in checks if not c["ok"]]
        return {
            "due": not refusals,
            "checks": checks,
            "refused_because": refusals,
            "proposals_made": len(self.proposals),
            "new_states": new_states,
        }

    # -- the beat ----------------------------------------------------------
    def observe(self, *, turn: int, theory_text: Optional[str],
                plan_report: Optional[Dict[str, Any]],
                distinct_states: int, actions_spent: int,
                has_predictor: bool) -> Dict[str, Any]:
        """One turn's reading. Returns the block for the turn record.

        `actions_spent` is the count standing at the *top* of this turn, so
        `actions_without_goal` is the answer to "how much of this leg's action
        budget was spent while the arm held no target", which is the number the
        finding is about.
        """
        self.turns += 1
        manual = read_manual(theory_text)
        if manual["goal_declared"]:
            self.goal_declared_ever = True
        if manual["absence_signature"]:
            self.absence_signature = manual["absence_signature"]

        status = (plan_report or {}).get("status")
        if status:
            self.plan_status_counts[status] = (
                self.plan_status_counts.get(status, 0) + 1)

        if not has_predictor:
            mode = "no_manual"
            self.turns_without_manual += 1
        elif manual["goal_declared"]:
            mode = "planning"
            self.turns_planning += 1
        else:
            mode = "exploring_no_goal"
            self.turns_without_goal += 1
            if self.first_no_goal_turn is None:
                self.first_no_goal_turn = turn
        self.mode = mode

        # Actions are attributed to the state the turn was in. A turn spent
        # planning does not count toward "spent without a goal" even if the
        # plan then failed -- that would be exactly the confusion this module
        # exists to remove.
        if mode == "exploring_no_goal":
            self.actions_without_goal = max(self.actions_without_goal,
                                            actions_spent)

        block: Dict[str, Any] = {
            "protocol": self.protocol,
            "turn": turn,
            "mode": mode,
            "why": _WHY[mode],
            "plan_status": status,
            "distinct_states": distinct_states,
            "turns_without_goal": self.turns_without_goal,
            "turns_planning": self.turns_planning,
        }
        block.update(manual)

        proposal = self.proposal_due(mode=mode, distinct_states=distinct_states,
                                     has_predictor=has_predictor)
        block["proposal"] = proposal
        return block

    def record_proposal(self, *, turn: int, distinct_states: int,
                        reason: str) -> Dict[str, Any]:
        """Book an ask. Called only on the `propose` rung, only when due.

        Booking it *moves the bar*: `states_at_last_proposal` is set here, so
        the next ask needs another `min_new_states`. That is what stops the
        criterion from firing on every subsequent turn once it has fired once.
        """
        entry = {"proposal_idx": len(self.proposals) + 1, "turn": turn,
                 "distinct_states": distinct_states, "reason": reason,
                 "delivered_on_turn": None,
                 "answered": None}
        self.proposals.append(entry)
        self.states_at_last_proposal = distinct_states
        return entry

    def mark_delivered(self, *, turn: int) -> Optional[Dict[str, Any]]:
        """The ask left the peg and went out with a theorize call.

        Booking and posting are separate events and R1b is the reason they now
        have separate fields. `20260801T001851Z-R1b-sk48-b` booked one ask on
        turn 1; the next three turns skipped theorize under the
        new-transitions gate, the beat after that lost all five of its replies
        in transit, and the leg then hit its spend reservation. The ask was
        never sent. The record said `"answered": null` -- true, and read by
        every later summary as "the desk gave no answer", which is not what
        happened, because the desk was never asked.

        `answered is None` therefore now means one of two things and the pair
        distinguishes them: `delivered_on_turn is None` is an ask that never
        went out, and `delivered_on_turn` set with `answered` still null is an
        ask that went out and whose reply the beat never got to read.
        """
        if not self.proposals:
            return None
        entry = self.proposals[-1]
        if entry.get("delivered_on_turn") is None:
            entry["delivered_on_turn"] = turn
        return entry

    def answer_proposal(self, *, theory_text: Optional[str]) -> Optional[Dict[str, Any]]:
        """What the desk did with the last ask, read off the manual it wrote.

        Three outcomes and all three are recorded: `signed` (a goal clause now
        exists), `declined_with_argument` (still no goal, but a theorem now
        argues for the absence), `silent` (still no goal and no argument). The
        third is the only one that is a defect in the answer rather than a
        position taken.
        """
        if not self.proposals:
            return None
        entry = self.proposals[-1]
        if entry.get("answered") is not None:
            return entry
        manual = read_manual(theory_text)
        if manual["goal_declared"]:
            entry["answered"] = "signed"
        elif manual["absence_is_signed"]:
            entry["answered"] = "declined_with_argument"
            entry["signature"] = manual["absence_signature"]
        else:
            entry["answered"] = "silent"
        return entry

    # -- the record --------------------------------------------------------
    def summary(self) -> Dict[str, Any]:
        return {
            "protocol": self.protocol,
            "final_mode": self.mode,
            "turns": self.turns,
            "turns_without_goal": self.turns_without_goal,
            "turns_planning": self.turns_planning,
            "turns_without_manual": self.turns_without_manual,
            "actions_without_goal": self.actions_without_goal,
            "first_no_goal_turn": self.first_no_goal_turn,
            "goal_declared_ever": self.goal_declared_ever,
            "absence_is_signed": bool(self.absence_signature),
            "absence_signature": self.absence_signature,
            "plan_status_counts": dict(sorted(self.plan_status_counts.items())),
            "proposals": list(self.proposals),
            "proposals_made": len(self.proposals),
            "proposals_delivered": sum(
                1 for p in self.proposals
                if p.get("delivered_on_turn") is not None),
            "proposals_answered": sum(
                1 for p in self.proposals if p.get("answered")),
            "criterion": {"min_new_states": self.min_new_states,
                          "max_proposals": self.max_proposals},
            "reading": _reading(self),
        }


_WHY = {
    "planning": "the manual declares a winning condition, so the ladder in "
                "inner/plan.py has something to search for and the plan beat "
                "is doing its job.",
    "exploring_no_goal": "the manual declares no winning condition, so "
                         "`is_goal` compiles to False everywhere and NO search "
                         "can succeed. The arm is exploring. That is a "
                         "legitimate state -- a goal true in the wrong states "
                         "stops the planner at the first one -- but it is a "
                         "state, not a planner failure, and every action spent "
                         "in it is spent without a target.",
    "no_manual": "there is no compiled predictor, so there is nothing for a "
                 "goal to be written against and the question does not arise "
                 "yet.",
    "not_started": "no turn has been observed.",
}


def _reading(state: "GoalState") -> str:
    if state.turns_planning and not state.turns_without_goal:
        return ("this leg held a winning condition on every turn it had a "
                "manual; `plan` was searching for something the whole time.")
    if not state.turns_without_goal:
        return ("this leg never reached a turn with a compiled manual, so it "
                "was never in a position to hold a goal or to lack one.")
    line = ("this leg spent %d of %d turns, and at least %d actions, with no "
            "winning condition in the manual. On those turns `plan` could not "
            "succeed by construction -- not because the search was hard, but "
            "because `is_goal` was False everywhere. Reading those turns as "
            "failed planning is a category error."
            % (state.turns_without_goal, state.turns,
               state.actions_without_goal))
    if state.absence_signature:
        line += (" The absence is SIGNED: the manual carries `%s`, a theorem "
                 "arguing for not naming a goal yet. That is a position, and "
                 "the record should show it as one."
                 % state.absence_signature)
    else:
        line += (" The absence is UNSIGNED: nothing in the manual argues for "
                 "it. Silence and a considered refusal read identically in "
                 "the old record and are not the same thing.")
    if state.proposals:
        delivered = [p for p in state.proposals
                     if p.get("delivered_on_turn") is not None]
        answered = [p.get("answered") for p in delivered if p.get("answered")]
        line += (" %d proposal(s) were BOOKED and %d were DELIVERED; answers: %s."
                 % (len(state.proposals), len(delivered),
                    ", ".join(answered) if answered else "none"))
        if len(delivered) < len(state.proposals):
            line += (" %d ask(s) never left the peg -- the rider rides on the "
                     "next theorize call a surprise pays for, and no such call "
                     "completed before the leg ended. NOTHING HERE IS EVIDENCE "
                     "ABOUT THE DESK: it was not asked."
                     % (len(state.proposals) - len(delivered)))
        if delivered and not answered:
            line += (" Every delivered ask came back unread -- the call raised, "
                     "or the reply did not survive the transport "
                     "(armtools/replyloss.py). The desk's position on a goal is "
                     "UNKNOWN on this leg, not negative.")
    elif state.protocol == "propose":
        line += (" No proposal was made: the criterion refused every turn, "
                 "which is the criterion working, not the criterion missing.")
    return line


#: The name the third channel asks the desk to use for the target it believes
#: in but cannot compile. Fixed rather than free-form so `armtools/
#: goal_forensics.py` can find it without guessing, and narrow enough that a
#: theorem about something else cannot be mistaken for one.
TARGET_THEOREM_PREFIX = "the_goal_i_cannot_write_is"


def prompt_rider(state: "GoalState", proposal: Dict[str, Any],
                 distinct_states: int) -> str:
    """The ask, as Markdown, to ride along on a theorize call already paid for.

    Deliberately does NOT tell the desk to invent a goal. It states the cost of
    the current position in the arm's own numbers and asks for one of three
    things back. Only silence is not an answer. The manuals that produced this
    finding declined, with good arguments, and a rider that made that choice
    harder to take would be a rider that bought a bad goal.

    **What R1b's records changed here.** The first two channels below are the
    original pair, and on `20260801T001851Z-R1b-g50t-a` the desk took the
    second one three times out of three, each time with the theorem
    `the_goal_is_absent_because_no_instance_can_name_the_socket`. Reading those
    arguments settles the question the round could not: **the rider engages
    half of the desk's case and talks past the other half.**

    The half it engages is soundness. Both carried manuals argued that a wrong
    goal sends the searcher after a fiction, and the rider agrees with them in
    so many words -- "it must be false in the states you have already seen".

    The half it talks past is *reach*. The desk's refusal is not a worry about
    being wrong; it is a demonstration that this grammar cannot say the thing.
    The goal section admits `Cart.pos = <landmark>` and `count(<Type>, color =
    c) = n`, one equation, no conjunction. The position the desk believes wins
    is a 5x5 body seated in a socket whose cells have never changed -- so they
    are board, so `arc-instances: all` seats nothing on them, so no `count`
    ranges over them and no landmark names them. Four candidate forms, each
    refuted against the frame, three times running. That is the same wall
    `20260801T0900Z-R2-frontier-by-generation` measured from the other side:
    12 of 47 off-frontier probes missed by exactly one never-before-changed
    cell.

    A rider offering only "write one" or "argue why not" forces the desk to
    smuggle its actual target into free prose -- which it did, unprompted, in
    `the_socket_is_a_keyhole_and_names_the_winning_position`, where nothing
    reads it. The third channel gives that answer a name and a place. It buys
    no model call: it is the same rider on the same already-paid-for turn.
    """
    return "\n".join([
        "## The manual has no goal section, and that has a price",
        "",
        "This is not a complaint and not a request to invent one. It is a "
        "number you have not been shown.",
        "",
        "The manual as it stands declares no `goal` clause. `is_goal` "
        "therefore compiles to `False` everywhere, so the planner cannot "
        "succeed on any input: every `plan` beat this leg has returned "
        "`no_goal_declared` without entering either rung of the ladder. "
        "So far that is %d turn(s) and at least %d action(s) spent with no "
        "target. The world has moved since the last time this was asked: "
        "%d distinct states are now on record (the bar is %d new ones)."
        % (state.turns_without_goal, state.actions_without_goal,
           distinct_states, state.min_new_states),
        "",
        "Three answers are acceptable and one is not.",
        "",
        "1. **A `goal` clause**, if the evidence now supports one. It must be "
        "false in the states you have already seen -- a goal satisfied by the "
        "current board stops the planner at the first node and is worse than "
        "no goal at all.",
        "2. **A `theorem`** whose name says the goal is absent (it must "
        "contain both `goal` and one of %s) and whose body gives the argument "
        "and the evidence that would settle it. Declining is a position; the "
        "record will carry it as one." % (", ".join(_ABSENCE_WORDS),),
        "3. **If, and only if, you decline because the goal section cannot "
        "SAY what you believe wins** -- not because you are unsure -- add a "
        "second `theorem` named `%s_...` whose body states, in your own "
        "words, the winning position you do believe in, and then names which "
        "of the section's forms you tried against it and what each one lacked. "
        "This arm has read your last three refusals and they are arguments "
        "about reach, not about confidence; the target you named in prose is "
        "the most valuable thing in the manual and there is currently nowhere "
        "for it to go. Answer 3 is not a substitute for answer 2 and does not "
        "soften it. It is the part of your case the record has been throwing "
        "away." % (TARGET_THEOREM_PREFIX,),
        "",
        "What is not acceptable is silence: a manual with neither a goal nor "
        "an argument about its absence leaves the arm exploring without "
        "knowing that it is exploring, which is the state this rider exists "
        "to end.",
    ])


def turn_row_fields(turn_record: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """The scoreboard columns, from one `turns.json` row.

    Three, and they are `None` rather than absent on a run made before this
    existed or with the protocol `off` -- so a scoreboard can tell "this leg
    was not measured" from "this leg was measured and had a goal", which a
    default of `False` would destroy.
    """
    block = (turn_record or {}).get("goal") or {}
    return {
        "goal_mode": block.get("mode"),
        "goal_declared": block.get("goal_declared"),
        "goal_proposal_due": (block.get("proposal") or {}).get("due"),
    }
