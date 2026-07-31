"""The Theoria arm: the shared outer shell, with Theoria's inner loop inside it.

    observe -> [ theorize -> certify -> probe -> plan -> commit ] -> record

The outer three beats are deliberately identical to the other two arms
(`Theoria.md` 1.10(c)); everything between the brackets is what this arm is.
The loop is driven by surprise: with none pending, plan and commit run silently
and free, and no model is called (constraint 8).

Order of business in one turn, and why:

1. **Surprise pending?** Then theorize. This is the only trigger. A turn with
   no surprise never reaches a model.
2. **certify** the manual against the whole recorded history -- replay and
   render consistency. Its failures are themselves surprises, so a manual that
   arrives broken is caught before it is used, not after it has spent actions.
3. **plan.** SAT goes to commit and the plan is executed as a script with every
   frame marked. UNSAT or no-goal falls through to probe -- and never becomes
   an unsolvability claim (constraint 6).
4. **probe.** The action that most splits the surviving hypotheses, priced in
   actions, prediction written first. If nothing splits anything, the arm
   explores the least-tried legal action and says that is what it did rather
   than dressing it up as an experiment.

The first turn is an exception with a reason: with zero frames there is nothing
to theorize *about*, so the arm spends a short opening sweep -- one of each
legal action -- to buy the evidence a first manual needs. That sweep is the
cheapest possible: no model calls at all.
"""

import hashlib
import json
import os
import shutil
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

import _bootstrap                                     # noqa: F401  (sys.path)

from harness.arc import ArcThroughProxy, SpendGateStopped, frames_of
from harness.budget import Budget, BudgetExhausted
from harness.modelcall import (AnonymityBreach, CostCeilingReached,
                               CredentialBreach, ModelDesk)
from world.adapt import run_engines as adapt_run_engines
from world.frames import FrameStore, Step, grid_hash

from . import (certify, commit, plan as plan_beat, probe as probe_beat,
               theorize, transfer)
from .books import Books
from .levels import LevelLog
from .surprise import Register

#: A first manual needs more than one frame. The sweep tries each legal action
#: once, which is the smallest evidence set from which `mdl_segmenter` can say
#: anything at all (it needs at least two states).
OPENING_SWEEP = True

#: How many theorize rounds one turn may spend before the arm stops repairing
#: and goes back to gathering evidence. Repairing a manual against the same
#: frames forever is how a loop spends a budget on itself.
MAX_THEORIZE_PER_TURN = 2

#: Wall-clock ceiling. ARC's retry waves make a run's duration only loosely
#: related to its action count, and an unattended run needs an end.
DEFAULT_WALL_CLOCK_S = 3 * 3600

#: How much new world must arrive before the desk is worth calling again.
#:
#: The evidence gate started as a binary: any new frame reopened it. On the
#: first live run that meant one probe action per theorize -- a $1.3, nine-minute
#: call to adjudicate a single extra transition -- and a two-hour run spent its
#: whole budget on theory and took about a dozen actions. That is not wrong in
#: principle (Theoria's whole claim is that playing is the byproduct), but it is
#: wasteful in practice: four transitions cost the same one call to adjudicate
#: and tell the desk four times as much, and the engines in particular are
#: starved by single-frame increments -- `zero_space`'s null space shrinks with
#: the transition count, and `mdl_segmenter` cannot amortise a declaration over
#: one frame.
#:
#: So the gate is quantitative: a surprise still triggers theorize, but only
#: once this much new evidence has accumulated since the last call. A run that
#: ends before the quota is met still theorizes on what it has -- the quota
#: delays a call, it never cancels one.
MIN_NEW_FRAMES_BETWEEN_THEORIZE = 4

#: How many probes in a row may come back with an **empty posterior** before the
#: arm stops probing and goes and looks at somewhere else in the world.
#:
#: A probe whose observation matches no hypothesis -- not the manual, not any
#: ablation of it, not even `inert` -- has eliminated nothing. Its realised
#: information gain is 0 bits (`inner/probe.information_gain_bits`), whatever
#: the design's expected bits said. One of those is a finding. Three in a row is
#: a message about the frontier, not about the world: the manual is missing a
#: mechanism, and no ablation of what is already written can reach the answer,
#: so the next ablation-designed probe will be vacuous too.
#:
#: This is measured, not feared. `20260731T1430Z-A3-level2-carried-r3` ran 28
#: resolved probes and every one of them was vacuous; `20260731T1500Z-...-l1`
#: ran 16 and every one of them was vacuous. Between them that is 44 actions
#: and, at one theorize per four probes, roughly $17 of desk time spent on
#: experiments that could not discriminate.
MAX_VACUOUS_PROBES_IN_A_ROW = 3

#: How many probes may be spent between one theorize call and the next.
#:
#: The probe designer has no memory of the answers: it re-derives the frontier
#: from the rolled-forward manual, so until the *manual* changes it keeps
#: proposing from the same hypothesis set. `...-r3` shows the consequence
#: exactly -- P-25 and P-27 were byte-identical designs, as were P-26 and P-28:
#: four actions, two questions. Capping the run of probes between adjudications
#: bounds that without forbidding it.
MAX_PROBES_BETWEEN_THEORIZE = 4

#: **This repo has never observed a level completion.** Across every recorded
#: live response — ~2,600 envelopes spanning all four development-pile games,
#: both baseline arms and this one — `levels_completed` is `0` and `state` is
#: `NOT_FINISHED` (once `GAME_OVER`). Nobody has cleared a level, so nobody has
#: seen which of the two plausible signals ARC actually sends: the counter
#: incrementing in-band, or `state: "WIN"` with levels still to play.
#:
#: Guessing one would be cheap and wrong half the time, and the failure is
#: silent in the expensive direction: if the signal is `WIN`, an arm that reads
#: `WIN` as terminal stops at the end of level 1 and every line of level
#: handling below it is dead code that nobody notices, because a run that ends
#: at a WIN looks like a success.
#:
#: So both are handled. The counter drives `LevelLog.observe`; a `WIN` with
#: levels remaining drives `_try_advance_level`, which sends RESET and then
#: *checks whether the world moved* rather than assuming it did. If it did not
#: move, the run stops with `outcome: "level_advance_unknown"` — which turns
#: the first real level completion into a measurement of the API's semantics
#: instead of a hang or an infinite loop.
LEVEL_SIGNAL_UNKNOWN = True

#: How many RESETs may be spent probing for the next level before the arm
#: admits it does not know how to advance. Two: one to try, one to rule out a
#: transient.
MAX_LEVEL_ADVANCE_ATTEMPTS = 2


def _forbidden_substrings(game_id: str) -> Tuple[str, ...]:
    """Every id that may not appear in a prompt this run sends.

    Two groups, and the second is the one A11 found missing.

    **The game being played**, full id and stem. The stem is the half that
    actually leaks: it is what a run slug embeds, so it is what an absolute
    path in an engine traceback or a Lean diagnostic carries into the prompt
    (`Theoria.md:353`).

    **Every sealed game**, full id and stem. Until now this list held only the
    id being played, which reads as sufficient and is not: the environment path
    is guarded by `SealedPileGuard` inside `EnvProxy`, but *the model path does
    not traverse that guard at all* -- `harness/modelcall.py` starts a
    subprocess and talks to a different upstream, so nothing between the arm
    and the desk has ever consulted the cut. A sealed id reaching model context
    is `Theoria.md:353`'s fourth channel opening from the inside: the desk is a
    pretrained model, and naming a sealed game to it is the same contamination
    as reading about that game, which `CLAUDE.md` forbids in those words. This
    is not hypothetical plumbing -- the *first* group exists precisely because
    an adversarial probe got six occurrences of `g50t` into a 20,975-char
    prompt through an engine traceback, and that channel does not know or care
    which pile the id it is carrying belongs to.

    Sourced from the frozen cut rather than a literal list, so widening the cut
    cannot leave this behind. `proxy/guard.py` belongs to another track and is
    imported, never edited. If the cut cannot be read the arm **fails closed**:
    a run that cannot enumerate the sealed pile is a run that cannot promise it
    kept the pile out of a prompt.
    """
    forbidden = {game_id, game_id.split("-")[0]}

    from proxy.guard import SealedPileGuard, stem     # noqa: PLC0415
    guard = SealedPileGuard()
    for sealed_id in guard.sealed:
        forbidden.add(sealed_id)
        forbidden.add(stem(sealed_id))

    # The game being played is a dev-pile id, so this cannot fire today; it
    # would fire if a caller ever handed this arm a sealed id, and at that
    # point every prompt would be unsendable, which is the correct outcome and
    # a confusing one to debug without being told why.
    forbidden.discard("")
    return tuple(sorted(forbidden))


class TheoriaArm:
    def __init__(self, *, env_base: str, run, game_id: str,
                 budget_actions: int = 120,
                 budget_commands: int = 2000,
                 reserve_for_probes: int = 0,
                 offline: bool = False,
                 model: str = "claude-opus-5",
                 cost_ceiling_usd: Optional[float] = 20.0,
                 wall_clock_s: float = DEFAULT_WALL_CLOCK_S,
                 resume_state: Optional[Dict[str, Any]] = None,
                 seed_books: Optional[str] = None,
                 carry_source_game: Optional[str] = None,
                 tags: Optional[List[str]] = None,
                 prompt_id: str = "P-8",
                 probe_economy: "Optional[probe_beat.ProbeEconomyConfig]" = None):
        self.game_id = game_id
        self.offline = offline
        self.run = run
        self.dir = run.dir
        self.started = time.time()
        self.wall_clock_s = wall_clock_s

        self.budget = Budget(actions=budget_actions, commands=budget_commands,
                             reserve_for_probes=reserve_for_probes)
        if resume_state:
            from harness.budget import resume         # noqa: PLC0415
            self.budget = resume(resume_state.get("budget"),
                                 actions=budget_actions,
                                 commands=budget_commands,
                                 reserve_for_probes=reserve_for_probes)

        self.arc = ArcThroughProxy(
            env_base, game_id, self.budget, on_command=self._on_command,
            # The claim this run draws on, so a refused request ends the leg
            # rather than being retried into the ceiling. `run.run` is the
            # ledger; `harness/run.py` hangs the binding on it.
            spend_binding=getattr(getattr(run, "run", None),
                                  "spend_binding", None))
        self.store = FrameStore()
        self.books = Books(os.path.join(self.dir, "books"), seed_from=seed_books)
        self.levels = LevelLog()
        self.register = Register()
        self.probes = probe_beat.ProbeLog(os.path.join(self.dir, "probes.jsonl"))
        #: Framework change A, default off. An explicit config beats the
        #: environment, so a test can pin the behaviour it means to test and a
        #: round can turn the change on for a whole campaign with one variable.
        #: With neither, `from_env` returns `enabled=False` -- 2026-07-31.
        self.probe_economy = probe_beat.ProbeEconomy(
            config=(probe_economy if probe_economy is not None
                    else probe_beat.ProbeEconomyConfig.from_env()))
        self.candidates_path = os.path.join(self.dir, "candidates.jsonl")
        self.tags = list(tags or ["theoria", "p8", "first-contact"])
        self.prompt_id = prompt_id

        #: (kind, playbook-token) pairs already reported to the desk, so a
        #: standing gap in the playbook fires once per revision of that
        #: playbook rather than once per turn. See `plan.surprises_from`.
        self._plan_gaps_reported: set = set()
        #: Probes spent since the last theorize call. Reset by theorize, not by
        #: the turn: the frontier cannot change until the manual does.
        self._probes_since_theorize = 0

        #: The books this run started from, if it did not start from nothing.
        #: `Books(seed_from=...)` above already copied the pair and hashed it
        #: into `books/CARRIED.json`; this adds what a CROSS-GAME carry needs on
        #: top -- the landmark strip, the source game id, the declared-name
        #: census -- and embeds that record rather than writing a second one.
        #: Done here rather than at the first theorize so that every artefact
        #: written after this point, including a run that dies during the
        #: opening sweep, already shows the manual it was handed.
        self.carried: Optional[Dict[str, Any]] = None
        self.carried_theory = ""
        self.transfer_report: Optional[Dict[str, Any]] = None
        self._carried_compiled: Optional[Dict[str, Any]] = None
        if seed_books:
            self.carried = transfer.carry(
                self.books, seed_books, source_game_id=carry_source_game)
            self.carried_theory = self.books.theory
            _dump(os.path.join(self.dir, "CARRIED.json"), self.carried)

        #: One row per engine per dispatch, appended as the run goes. The claim
        #: E3 is testing -- that the engines supply the desk reliably on a live
        #: game -- is a claim about a sequence of dispatches, so it needs a
        #: record with a row per dispatch and not a total at the end.
        self.engine_log_path = os.path.join(self.dir, "engines_online.jsonl")
        self.engine_rounds: List[Dict[str, Any]] = []
        self._last_dispatch: Optional[Dict[str, Any]] = None
        self._last_dispatch_frames: int = -1
        self._last_dispatch_idx: int = -1

        pricing = None
        try:
            from proxy.cost import PriceTable, DEFAULT_TABLE      # noqa: PLC0415
            pricing = PriceTable.load(DEFAULT_TABLE).reference()
        except Exception:                              # noqa: BLE001
            pricing = None

        self.desk = ModelDesk(
            run.run, model=model, pricing_ref=pricing,
            cost_ceiling_usd=None if offline else cost_ceiling_usd,
            transcript_dir=os.path.join(self.dir, "desk"),
            forbid_in_prompt=_forbidden_substrings(game_id),
            context=self._desk_context)

        #: How many commands had been recorded when the desk was last called.
        #: The evidence gate in `_theorize_and_certify` turns on it.
        self._frames_at_last_theorize = -1

        #: The turn being played, so a level boundary observed inside a commit
        #: script can say which turn it happened on.
        self.current_turn = 0

        #: How many certify reports existed when the current level began.
        #: `certify` asks "have I run *on this level*", not "have I ever run".
        self._certify_reports_at_level_start = 0

        #: The level whose unusable manual has already been reported, so the
        #: surprise fires once per level rather than once per turn.
        self._unusable_manual_reported: Optional[int] = None

        self.desk_failures: List[Dict[str, Any]] = []
        self.turns: List[Dict[str, Any]] = []
        self.theorize_reports: List[Dict[str, Any]] = []
        self.certify_reports: List[Dict[str, Any]] = []
        self.plan_reports: List[Dict[str, Any]] = []
        self.commit_reports: List[Dict[str, Any]] = []
        self.action_counts: Dict[int, int] = {}
        self.outcome = "not_started"
        self.scorecard: Optional[Dict[str, Any]] = None
        self.last_envelope: Optional[Dict[str, Any]] = None
        self.stopped_because = ""

    # -- plumbing ----------------------------------------------------------
    def _desk_context(self) -> Dict[str, Any]:
        """The x-axis of the bill, sampled at the moment the money is spent."""
        return {"actions_at_call": self.budget.actions_ok,
                "commands_at_call": self.budget.commands_sent,
                "transitions_at_call": max(0, len(self.store.grids) - 1),
                "turn": len(self.turns),
                "elapsed_s_at_call": round(self._elapsed(), 1)}

    def _on_command(self, entry: Dict[str, Any]) -> None:
        self._write_run_state()

    def _elapsed(self) -> float:
        return time.time() - self.started

    def _out_of_time(self) -> bool:
        return self._elapsed() > self.wall_clock_s

    def _record(self, action: str, status: int, envelope: Any, *,
                probe: bool = False, note: str = "") -> Step:
        frames = frames_of(envelope) if status == 200 else []
        step = Step(len(self.store.steps), action, frames,
                    status=status,
                    state=(envelope or {}).get("state") if isinstance(envelope, dict) else None,
                    levels_completed=(envelope or {}).get("levels_completed")
                    if isinstance(envelope, dict) else None,
                    available_actions=(envelope or {}).get("available_actions")
                    if isinstance(envelope, dict) else None,
                    probe=probe, note=note)
        if isinstance(envelope, dict):
            self.last_envelope = envelope
        added = self.store.add(step)
        event = self.levels.observe(
            levels_completed=step.levels_completed,
            step_idx=step.step_idx, action=action,
            turn=self.current_turn, actions_spent=self.budget.actions_ok,
            # The last level has no level after it. If the API increments the
            # counter to `win_levels` *and* sets WIN on the final level -- which
            # is exactly what this repo's own mock does -- then without this
            # the arm fires a boundary into a level that does not exist: it
            # snapshots `level7-complete`, drops the problem and the compiled
            # forms, and cuts `starts`. A *winning* run would end with no
            # `problem.json` and a `levels.level` of 8 for a 7-level game.
            final_level=self.arc.win_levels)
        if event is not None:
            self._on_level_boundary(event)
        return added

    # -- the level boundary ------------------------------------------------
    def _frames_this_level(self) -> int:
        """Steps recorded since the current level began.

        The evidence gate counts in this unit, not in absolute steps: a fresh
        level has seen nothing, whatever the run's total.
        """
        return len(self.store.steps) - self.levels.start

    def _level_store(self):
        """The current level's trajectory -- see `inner/levels.py` for why.

        The beats that replay, segment or roll forward take this; `trace.jsonl`
        still gets the whole run.
        """
        return self.store.since(self.levels.start)

    def _on_level_boundary(self, event: Dict[str, Any]) -> None:
        """The domain travels. The problem, the trajectory and every *derived*
        form of the manual do not.

        1. The pair is snapshotted under the level it just finished, so the
           concept-birth timeline has a mark at the boundary. Transfer is a
           claim about *these two files* being unchanged across it.
        2. `problem.json` is dropped: it described level N's board and would
           otherwise be handed to the planner as level N+1's.
        3. **`generated/` is dropped with it.** This is the one that bites.
           `load_predictor` reads `generated/theory.py` off disk with no
           freshness check, and `compile_all` skips `gen_python` when there is
           no problem -- so a later compile does not even overwrite it. Level
           N+1 would load level N's compiled predictor, whose `initial_state()`
           bakes in level N's board, and `plan` would search from that state
           and hand the script to `commit` to fire into a board it has never
           seen. Dropping the problem without dropping the forms derived from
           it leaves exactly that inconsistency.
        4. The evidence gate is re-armed, and certify is re-armed with it: the
           new level has no frames yet, and `certify` has not run *on this
           level* however many times it ran on the last one.

        **Pending surprises are deliberately NOT retired.** An earlier version
        did retire them, on the theory that a surprise fired against a vanished
        trajectory would buy a pointless model call. An adversarial review
        showed the reasoning does not survive contact with the loop: `need` is
        a boolean and `Register.handled` closes *all* pending surprises in one
        call, so one pending surprise costs exactly what three do -- retiring
        bought nothing measurable. Worse, it was load-bearing in the wrong
        direction: emptying `pending` was one of three things that together
        left a run unable to notice its own manual had gone stale, and the arm
        would play out its whole budget on round-robin exploration with a dead
        book and a green `constraint_8`. A boundary should make the desk look
        *again*, not look away. See `DECISIONS.md` D-A3-003.
        """
        self.books.snapshot("level%d-complete" % event["from_level"])
        for path in (self.books.problem_path,):
            try:
                if os.path.exists(path):
                    os.remove(path)
            except OSError:                            # noqa: BLE001
                pass
        try:
            if os.path.isdir(self.books.generated):
                shutil.rmtree(self.books.generated)
            os.makedirs(self.books.generated, exist_ok=True)
        except OSError:                                # noqa: BLE001
            pass
        event["pending_surprises_carried"] = len(self.register.pending)
        self._frames_at_last_theorize = -1
        self._certify_reports_at_level_start = len(self.certify_reports)
        self.turns.append({"turn": "%s-boundary" % self.current_turn,
                           "beat": "level",
                           "detail": "level %d complete" % event["from_level"],
                           "level_boundary": event,
                           "actions_before": self.budget.actions_ok,
                           "actions_spent": self.budget.actions_ok})
        self._write_run_state()

    def _send(self, action_id: int, *, probe: bool = False, note: str = ""):
        status, envelope = self.arc.act(action_id, probe=probe)
        self.action_counts[action_id] = self.action_counts.get(action_id, 0) + 1
        step = self._record("ACTION%d" % action_id, status, envelope,
                            probe=probe, note=note)
        return status, envelope, step.frames

    def _terminal(self) -> Optional[str]:
        state = (self.last_envelope or {}).get("state")
        if state == "WIN" and self._levels_remain():
            # A WIN with levels still to play is a *level* win, not the run's
            # end. See `LEVEL_SIGNAL_UNKNOWN`.
            return None
        return state if state in ("WIN", "GAME_OVER") else None

    def _levels_remain(self) -> bool:
        """Does the game say there are levels after this one?

        `win_levels` comes from the envelope (7 for g50t, 8 for ar25). Unknown
        means unknown: with no roster the arm cannot claim a WIN is partial,
        so it treats it as the end -- the conservative direction, since
        stopping loses a run and mis-continuing spends money on a finished
        game.
        """
        total = self.arc.win_levels
        if total is None:
            return False
        return self.levels.completed + 1 < total

    def _try_advance_level(self) -> bool:
        """The world says WIN and the roster says there are more levels.

        This is the branch nobody has been able to write from evidence, and
        saying so is more useful than guessing: see `LEVEL_SIGNAL_UNKNOWN`. The
        arm sends RESET -- the only command that could plausibly start the next
        level -- and then *checks whether the world actually moved* instead of
        assuming it did.

        **What "moved" means, and why a state string will not do.** An earlier
        version accepted `state != "WIN"` as proof of advance. That is wrong,
        and this repo had already settled it:
        `arc-recon/ACCESS_CHECK.md:24-25`, verified by precheck on all four
        development-pile games, records that `POST /api/cmd/RESET` returns
        `full_reset: false` and that **RESET is a level reset -- the level it
        resets to is the one the session is on**. So the likeliest outcome of
        RESET-after-WIN is a restart of the *same* level, returning
        `NOT_FINISHED` -- which the state check passes. The arm would then have
        recorded a level completion that did not happen, cut `starts`, and fed
        a fabricated boundary into the series behind the paper's figure. A
        fabricated level completion in a figure is the worst outcome available
        here, worse than stopping.

        So the test is the board itself. `ACCESS_CHECK.md` §2 establishes that
        RESET frames are byte-identical across six replays in four sessions, so
        comparing the returned frame against this level's opening frame is a
        real measurement rather than an inference. Identical means the level
        did not advance.

        Either way the arm comes back with data: this branch is the first thing
        in the repository that will ever observe a level completion, and it
        records what it saw under `levels.reset_probe`.
        """
        self.levels.advance_attempts += 1
        if self.levels.advance_attempts > MAX_LEVEL_ADVANCE_ATTEMPTS:
            self.stopped_because = (
                "the world reported WIN with levels remaining, and %d RESET(s) "
                "did not start another level"
                % MAX_LEVEL_ADVANCE_ATTEMPTS)
            self.outcome = "level_advance_unknown"
            return False

        before_completed = self.levels.completed
        opening = self._level_store().grids
        opening_hash = grid_hash(opening[0]) if opening else None

        status, envelope = self.arc.reset()
        step = self._record("RESET", status, envelope, note="advance level")
        if status != 200:
            self.stopped_because = ("RESET after a level WIN returned %s"
                                    % status)
            self.outcome = "level_advance_failed"
            return False

        state = (self.last_envelope or {}).get("state")
        reset_hash = grid_hash(step.grid) if step.grid is not None else None
        probe = {"attempt": self.levels.advance_attempts,
                 "state_after_reset": state,
                 "level_opening_hash": opening_hash,
                 "reset_frame_hash": reset_hash,
                 "counter_moved": self.levels.completed > before_completed}
        self.levels.reset_probes.append(probe)

        if self.levels.completed > before_completed:
            # `_record` already saw the counter move and fired the boundary.
            # The budget is per boundary, not per run: a 7-level game needs to
            # do this six times.
            self.levels.advance_attempts = 0
            probe["verdict"] = "counter moved"
            return True

        if reset_hash is not None and reset_hash == opening_hash:
            # Measured, not inferred: RESET handed back this level's opening
            # board. That is `ACCESS_CHECK.md`'s `full_reset: false` observed
            # from inside the arm, and it means RESET is not an advance
            # mechanism.
            probe["verdict"] = "same board: RESET restarted this level"
            self.stopped_because = (
                "the world reported WIN, and RESET returned this level's own "
                "opening board (frame hash %s) -- RESET restarts a level, it "
                "does not advance one. ACCESS_CHECK.md said full_reset:false; "
                "this is that, measured from inside the arm."
                % (reset_hash or "?")[:12])
            self.outcome = "level_advance_unknown"
            return False

        if state and state != "WIN" and reset_hash != opening_hash:
            # A different board *and* a state that moved on. The WIN was the
            # level signal and RESET started the next one. Record the boundary
            # through the same door so `starts` stays authoritative.
            probe["verdict"] = "new board: WIN was the level signal"
            event = self.levels.force(
                signal="win_then_reset",
                step_idx=len(self.store.steps) - 1,
                note="state went WIN -> %s after RESET and the board changed "
                     "(%s -> %s); the counter did not move, so WIN was the "
                     "level signal"
                     % (state, (opening_hash or "?")[:12],
                        (reset_hash or "?")[:12]),
                turn=self.current_turn,
                actions_spent=self.budget.actions_ok)
            self._on_level_boundary(event)
            self.levels.advance_attempts = 0
            return True

        self.stopped_because = (
            "the world still reports WIN after RESET; this arm cannot tell "
            "how ARC advances a level and will not guess")
        self.outcome = "level_advance_unknown"
        return False

    def _legal_actions(self) -> List[int]:
        actions = list(self.arc.available_actions or [])
        # ACTION6 is the click family; its payload shape is unsolved in this
        # repo (1,254 attempts, every one HTTP 500) and it is not offered here.
        # Recorded rather than silently filtered: see RUN_STATE.md.
        return [a for a in actions if 1 <= a <= 7 and a != 6]

    # -- the run -----------------------------------------------------------
    def play(self) -> Dict[str, Any]:
        self.arc.open_scorecard(
            tags=self.tags,
            opaque={"run_id": self.run.run_id, "prompt_id": self.prompt_id})

        status, envelope = self.arc.reset()
        self._record("RESET", status, envelope)
        if status != 200:
            self.outcome = "reset_failed"
            self.stopped_because = "RESET did not return 200 after %d attempts" % 40
            return self._finish()

        try:
            self._opening_sweep()
            self._cold_transfer()
            self._main_loop()
        except BudgetExhausted as exc:
            self.stopped_because = "budget: %s" % exc
        except CostCeilingReached as exc:
            self.stopped_because = "cost ceiling: %s" % exc
        except SpendGateStopped as exc:
            # 闸门红了立刻停. Not a retry, not a smaller reservation: the pool
            # is the one authority that outranks the plan.
            self.stopped_because = str(exc)
            self.outcome = "spend_gate_tripped"
        except KeyboardInterrupt:
            self.stopped_because = "interrupted"
        return self._finish()

    def _opening_sweep(self) -> None:
        """One of each legal action. No model calls: there is nothing to
        theorize about until there are at least two frames."""
        if not OPENING_SWEEP:
            return
        for action_id in self._legal_actions():
            if self._out_of_time() or self._terminal():
                return
            self.budget.check()
            self._send(action_id, note="opening sweep")
        self.turns.append({"turn": 0, "beat": "observe",
                           "detail": "opening sweep over %s"
                                     % self._legal_actions(),
                           "actions_spent": self.budget.actions_ok})

    def _cold_transfer(self) -> None:
        """What a manual written for another game does on this one, unrepaired.

        Runs after the opening sweep and before the first model call, so its
        every number is attributable to the carried manual alone. Three steps,
        all free: compute this level's problem instance from the carried
        manual's own object declarations, compile, certify.

        Ordering matters and is deliberate. The manual's own render-accounting
        prediction is computed and written to disk BEFORE certify runs, exactly
        as `probe` writes a prediction before its result. A prediction recorded
        after the fact is not one.

        The surprises this fires are left pending on purpose: they are the
        reason the desk will be called on turn 1, and answering "what did the
        old manual get wrong about the new world" is the first useful thing the
        desk can do here.
        """
        if not self.carried:
            return
        report_path = os.path.join(self.dir, "transfer.json")

        objects = theorize._objects_from_theory(self.carried_theory)
        landmarks = theorize._landmarks_from_theory(self.carried_theory)

        prediction = transfer.predict_unexplained(self._level_store(), objects)
        # On disk before the check it predicts, and before anything that could
        # be accused of having seen the answer.
        _dump(report_path, {"stage": "prediction-only",
                            "provenance": self.carried,
                            "prediction": prediction})

        # The engines, dispatched on the opening sweep alone. Zero model calls,
        # and the first evidence for E3's supply-chain claim.
        self._dispatch_engines(label="cold")

        try:
            from .books import problem_from_frames         # noqa: PLC0415
            self.books.write_problem(
                problem_from_frames(self._level_store(), objects,
                                    landmarks=landmarks))
        except Exception as exc:                           # noqa: BLE001
            prediction["problem_error"] = "%s: %s" % (type(exc).__name__, exc)

        compiled = self.books.compile_all()
        self._carried_compiled = compiled
        certify_report = self._certify()

        # Whether this game can test the carried theory at all -- free to
        # compute, and it decides how every other number in this report may be
        # read. See `transfer.action_overlap`.
        namespace, predictor_error = self.books.load_predictor()
        actions = transfer.action_overlap(namespace, self._legal_actions(),
                                          predictor_error=predictor_error)

        self.transfer_report = transfer.cold_report(
            provenance=self.carried, prediction=prediction,
            compiled=compiled, certify_report=certify_report,
            store_summary=self._level_store().summary(),
            actions_spent=self.budget.actions_ok,
            actions=actions)
        _dump(report_path, self.transfer_report)
        self.books.snapshot("after-cold-certify")
        # The cold certify fires the surprises that will bring the desk in on
        # turn 1, and `_write_run_state` is the only thing that flushes the
        # register to `surprises.jsonl`. Without this the first live E3 run sat
        # for a quarter of an hour with two surprises in memory and an empty
        # file on disk -- and a run killed in that window would have lost the
        # record of why it was about to spend a dollar.
        self._write_run_state()
        self.turns.append({
            "turn": 0, "beat": "transfer",
            "detail": "carried manual from %s certified cold on %s"
                      % (self.carried.get("source_run"), self.game_id),
            "prediction": self.transfer_report["prediction_scored"],
            "actions_spent": self.budget.actions_ok})

    def _dispatch_engines(self, *, label: str) -> Dict[str, Any]:
        """Run the engines on everything observed, and record the delivery.

        `theorize` would do this itself; it is lifted out here so that every
        dispatch gets a row whether or not a desk call follows it -- the cold
        stage makes none, and a desk that fails still had its engines run.

        **Identical evidence is not re-swept.** The engines are deterministic
        given the same frames, so a sweep over a store that has not grown
        returns exactly what the last one returned. The first live E3 run paid
        for that lesson in the record: the cold beat and the first theorize both
        dispatched over the same five transitions, took 348 seconds each, and
        appended 680 candidate rows each -- and the second 680 were byte-for-byte
        the first 680, on a stream whose contract says sweeps differ because
        each sees more transitions than the last. Here they saw the same ones,
        so they were copies, and the claim in `README.md` did not hold for them.

        The reuse is recorded as its own row rather than hidden: a dispatch that
        did not run is a fact about the run, and `engines_online.jsonl` is the
        record of what the supply chain actually did.
        """
        # Keyed on the FRAME count, not the transition count. `max(0, n-1)` is
        # not injective at n in {0, 1}: a 200 that carried no frame leaves zero
        # grids and key 0, and the first real frame to arrive also gives key 0,
        # so the engines would be handed an answer computed over no frames at
        # all while one existed.
        level_store = self._level_store()
        frames = len(level_store.grids)
        transitions = max(0, frames - 1)
        if (self._last_dispatch is not None
                and self._last_dispatch_frames == frames):
            entry = {
                "run_id": self.run.run_id,
                "label": label,
                "dispatch_idx": len(self.engine_rounds),
                "step_idx": len(self.store.steps),
                "transitions_seen": transitions,
                "elapsed_ms": 0,
                "reused_from_dispatch_idx": self._last_dispatch_idx,
                "reused_because": (
                    "no new frame since dispatch %d; the engines are "
                    "deterministic given the same frames, so a re-sweep would "
                    "append an exact copy of its rows"
                    % self._last_dispatch_idx),
                "store_summary_refreshed": True,
                "candidate_rows_total": _count_lines(self.candidates_path),
                "candidate_rows_added": 0,
                "error": None,
                "engines": _engine_delivery(self._last_dispatch),
            }
            # `run_engines` returns `store: store.summary()` alongside the
            # engine reports, and that summary counts frameless steps -- a 500
            # on an action appends a step with no frame, which cannot change
            # what the engines computed but does change what the world looks
            # like. Left stale, `theorize` would put the live summary at the
            # top of the desk's prompt and this stale one inside "what the
            # engines proposed", and the two would disagree about the action
            # that had just failed. Refreshed on the reused copy, which is
            # cheap and is not engine output.
            reused = dict(self._last_dispatch)
            reused["store"] = level_store.summary()
            self._last_dispatch = reused
            self.engine_rounds.append(entry)
            with open(self.engine_log_path, "a", encoding="utf-8",
                      newline="\n") as fh:
                fh.write(json.dumps(entry, sort_keys=True, default=str) + "\n")
            return reused

        started = time.time()
        rows_before = _count_lines(self.candidates_path)
        error = None
        try:
            engines = adapt_run_engines(level_store, self.candidates_path)
        except Exception as exc:                           # noqa: BLE001
            error = "%s: %s" % (type(exc).__name__, exc)
            engines = {}
        rows_after = _count_lines(self.candidates_path)

        entry = {
            # This file is append-only and sits beside a ledger that partitions
            # by `run_id` for the same reason: a slug reused across runs must
            # stay readable. Real slugs are UTC-stamped so it should not happen,
            # but "should not happen" is not a partition key.
            "run_id": self.run.run_id,
            "label": label,
            "dispatch_idx": len(self.engine_rounds),
            "step_idx": len(self.store.steps),
            "transitions_seen": transitions,
            "elapsed_ms": int((time.time() - started) * 1000),
            "candidate_rows_total": rows_after,
            "candidate_rows_added": rows_after - rows_before,
            "error": error,
            "engines": _engine_delivery(engines),
        }
        self.engine_rounds.append(entry)
        with open(self.engine_log_path, "a", encoding="utf-8",
                  newline="\n") as fh:
            fh.write(json.dumps(entry, sort_keys=True, default=str) + "\n")
        if error is None:
            self._last_dispatch = engines
            self._last_dispatch_frames = frames
            self._last_dispatch_idx = entry["dispatch_idx"]
        return engines

    def _main_loop(self) -> None:
        turn = 0
        while True:
            turn += 1
            self.current_turn = turn

            # A WIN with levels remaining is a level boundary, not the end of
            # the run -- but which signal ARC sends has never been observed, so
            # this branch probes rather than assumes (`LEVEL_SIGNAL_UNKNOWN`).
            if ((self.last_envelope or {}).get("state") == "WIN"
                    and self._levels_remain()):
                if not self._try_advance_level():
                    return
                continue

            if self._terminal():
                self.stopped_because = "the world reported %s" % self._terminal()
                return
            if self._out_of_time():
                self.stopped_because = "wall clock (%.0fs)" % self._elapsed()
                return
            if self.budget.actions_left <= 0:
                self.stopped_because = "action budget spent"
                return

            record: Dict[str, Any] = {"turn": turn,
                                      "actions_before": self.budget.actions_ok,
                                      "elapsed_s": round(self._elapsed(), 1)}

            # 1 + 2. theorize (only on surprise, or when there is no manual
            #        at all), then certify.
            self._theorize_and_certify(record)

            namespace, error = self.books.load_predictor()
            record["predictor"] = "loaded" if namespace else error

            # 3. plan.
            if namespace is not None:
                compiled = (self.theorize_reports[-1].get("_compiled")
                            if self.theorize_reports else None) or {}
                plan_report = plan_beat.plan(self.books, namespace, compiled)
                self.plan_reports.append(plan_report)
                record["plan"] = {k: v for k, v in plan_report.items()
                                  if k != "tiers"}
                plan_beat.surprises_from(
                    plan_report, self.register,
                    reported=self._plan_gaps_reported,
                    token=_book_token(self.books.playbook))

                if plan_report.get("status") == "sat" and plan_report.get("plan"):
                    self._commit(namespace, plan_report, record)
                    self.turns.append(record)
                    continue

            # 4. probe, or honest exploration.
            self._probe_or_explore(namespace, record)
            self.turns.append(record)

    def _theorize_and_certify(self, record: Dict[str, Any]) -> None:
        # The evidence gate, checked once per turn. A surprise says the manual
        # is wrong; it does not say that another pass over the SAME frames will
        # fix it. Once the desk has answered for this evidence set -- and had
        # one certify-driven repair at it, which is the theorize<->certify arrow
        # A0 reported was never exercised -- re-calling it buys a
        # differently-worded manual against identical data at full price. What
        # the loop needs then is more world. So the turn falls through to probe
        # and the manual stays red until evidence arrives that could change it.
        self._notice_unusable_manual()

        new_frames = self._frames_this_level() - self._frames_at_last_theorize
        if (self.books.theory.strip()
                and new_frames < MIN_NEW_FRAMES_BETWEEN_THEORIZE
                and self.budget.actions_left > MIN_NEW_FRAMES_BETWEEN_THEORIZE):
            record["theorize"] = (
                "skipped: %d surprise(s) pending but only %d new transition(s) "
                "since the last call (want %d). Going to get more."
                % (len(self.register.pending), new_frames,
                   MIN_NEW_FRAMES_BETWEEN_THEORIZE))
            if not self._certified_this_level():
                record["certify"] = _certify_line(self._certify())
            return

        rounds = 0
        while rounds < MAX_THEORIZE_PER_TURN:
            need = (not self.books.theory.strip()) or bool(self.register.pending)
            if not need:
                record.setdefault("theorize", "skipped: no surprise pending")
                break
            if self.offline:
                record["theorize"] = "skipped: offline dry run makes no model calls"
                self.register.handled("offline")
                break

            pending = self.register.pending
            # Dispatched here rather than inside `theorize.run` so that every
            # sweep gets a row in `engines_online.jsonl` even when the desk call
            # that follows it fails. An engine sweep that fed nothing is still a
            # delivery, and E3's claim is about the deliveries.
            engines = self._dispatch_engines(label="theorize")
            try:
                report = theorize.run(
                    self.desk, self.books, self._level_store(),
                    self.candidates_path,
                    surprises=pending,
                    certify_report=(self.certify_reports[-1]
                                    if self.certify_reports else None),
                    step_idx=len(self.store.steps),
                    engines=engines)
            except CostCeilingReached:
                raise                                  # the run's honest end
            except (AnonymityBreach, CredentialBreach):
                # Not a desk failure, and the handler below would have made it
                # one -- recording it, continuing the turn, and spending the
                # rest of the leg's budget on a run that is already
                # inadmissible. `Theoria.md:353` is a hard rule; a run that
                # tried to send the game id does not get to carry on measuring.
                #
                # This is the same shape as `CostCeilingReached` above and for
                # the same reason: the broad handler exists so a timeout or an
                # unusable reply does not end a run, and both of those are
                # things the loop can recover from by gathering more evidence.
                # A leaked id is not, and neither is a leaked credential:
                # `CredentialBreach` means the desk environment held a
                # registered secret under a name the scrub list does not know,
                # which is a defect in the harness rather than a bad reply.
                raise
            except Exception as exc:                   # noqa: BLE001
                # A desk that times out, or returns something unusable, must
                # not end the run. The manual stays as it was, the surprises
                # stay pending, and the turn falls through to gathering more
                # evidence -- which is what a theorize that produced nothing
                # leaves the loop needing anyway.
                record["theorize"] = "the desk failed: %s: %s" % (
                    type(exc).__name__, exc)
                self.desk_failures.append(
                    {"step_idx": len(self.store.steps),
                     "error": "%s: %s" % (type(exc).__name__, exc)})
                self._frames_at_last_theorize = self._frames_this_level()
                self._write_run_state()
                break
            self.register.handled("theorize")
            self.theorize_reports.append(report)
            rounds += 1
            # The manual has been adjudicated, so the ablation frontier is a
            # different set now and the probe caps start again. Reset here
            # rather than per turn: a turn is not what makes a probe novel.
            self._probes_since_theorize = 0
            self.probes.vacuous_streak = 0
            # RUN_STATE is otherwise only written on an ARC command, which
            # leaves a watcher blind for the several minutes a theorize takes.
            self._write_run_state()
            record.setdefault("theorize_rounds", 0)
            record["theorize_rounds"] += 1
            record["theorize_calls"] = report.get("calls")
            record["theorize_ok"] = report.get("ok")

            certify_report = self._certify()
            record["certify"] = _certify_line(certify_report)
            if not self.register.pending:
                break
        else:
            record["theorize"] = ("stopped repairing after %d rounds; going "
                                  "back for evidence" % MAX_THEORIZE_PER_TURN)

        if rounds:
            self._frames_at_last_theorize = self._frames_this_level()
        if not self._certified_this_level() and self.books.theory.strip():
            record["certify"] = _certify_line(self._certify())

    def _certified_this_level(self) -> bool:
        """Has certify run since the current level began?

        It used to ask `if not self.certify_reports` -- has certify *ever*
        run -- which is the same question only while a run has one level. From
        level 2 on, that list is never empty again and **certify never runs
        again at all**: the manual is never checked against the board it is
        actually being used on. The counter is reset at each boundary.
        """
        return len(self.certify_reports) > self._certify_reports_at_level_start

    def _notice_unusable_manual(self) -> None:
        """A manual with no loadable executable form disagrees with the world.

        This exists because of a failure that was reproduced end to end: a run
        seeded with carried books has a non-empty `theory.dsl` but no
        `generated/theory.py` (the compiled forms deliberately do not travel --
        they are re-derived). `certify.cheap` returns early on a failed
        predictor load, and **a failed load is not one of the seven
        surprises**, so nothing fires. The theorize predicate then reads
        `(not theory.strip()) or pending` -- theory is non-empty *because the
        carry succeeded*, pending is empty -- and is False forever. No
        theorize, so no compile, so no predictor, so no plan: the run spends
        its entire budget on round-robin exploration with books it never
        opened, and reports `model_calls: 0, surprises: 0, constraint_8: holds`.
        A green tick on a dead run.

        The inversion is what makes it dangerous: carrying *nothing* works
        (empty theory opens the predicate), carrying *something* bricks it --
        so it fires exactly when transfer is being claimed.

        `replay_mismatch` is the honest kind. The cheap certify layer *is*
        replay, and a manual that cannot be executed is a manual that cannot be
        replayed against the record; the empirical family is the one that
        revises `theory.dsl`, which is the book at fault. Firing it rather than
        just widening the predicate means the condition appears in the
        seven-count series instead of silently steering control flow.
        """
        if not self.books.theory.strip():
            return                                     # nothing to be stale
        namespace, error = self.books.load_predictor()
        if namespace is not None:
            return
        if self._unusable_manual_reported == self.levels.level:
            return                                     # once per level
        self._unusable_manual_reported = self.levels.level
        self.register.fire(
            "replay_mismatch",
            "the manual has no executable form: %s" % error,
            step_idx=len(self.store.steps) - 1,
            payload={"beat": "certify", "level": self.levels.level,
                     "carried": bool(self.books.carried),
                     "why": "theory.dsl is non-empty but generated/theory.py "
                            "could not be loaded, so nothing can replay it"})

    def _certify(self) -> Dict[str, Any]:
        # Before the first theorize there is no compile result from the desk,
        # but on a carried run there IS one -- the cold compile of the manual
        # this run was handed. Falling back to it is what lets the expensive
        # layer report on the carried manual rather than on nothing.
        compiled = (self.theorize_reports[-1].get("_compiled")
                    if self.theorize_reports else self._carried_compiled) or {}
        report = certify.run(self.books, self._level_store(),
                             commit.action_to_manual, compiled)
        self.certify_reports.append(report)
        certify.surprises_from(report, self.register)
        return report

    def _commit(self, namespace, plan_report, record) -> None:
        def send(action_id):
            status, envelope, frames = self._send(action_id, note="commit")
            return status, envelope, frames

        report = commit.execute(namespace, plan_report["plan"], send=send,
                                store=self._level_store(),
                                action_to_arc=commit.action_to_arc)
        self.commit_reports.append(report)
        commit.surprises_from(report, self.register)
        record["commit"] = {k: v for k, v in report.items() if k != "steps"}

    def _probe_or_explore(self, namespace, record) -> None:
        legal = self._legal_actions()
        if not legal:
            self.stopped_because = "the world offers no legal action"
            raise BudgetExhausted(self.stopped_because)

        design = None
        chosen: Optional[int] = None
        #: The live frontier's predictions: what `survived` is measured over.
        predictions: Dict[str, str] = {}
        #: The whole ablation set's predictions: what names the experiment.
        #: Equal to `predictions` unless the economy has retired something.
        identity: Dict[str, str] = {}
        #: Set by whichever rule says no; `None` means the probe is bought.
        refusal: Optional[str] = None
        #: A probe was designed and cleared the entropy floor, so there is a
        #: real allow/refuse decision to write into the economy's audit.
        designed = False

        if namespace is not None:
            # This level's trajectory, not the run's: `_roll_forward` replays
            # the manual's `step` over every recorded action, and across a
            # boundary that replays level N's actions into level N+1's opening
            # board. `inner/levels.py` names this as the third of the three
            # beats that read the trace as one continuous trajectory.
            state = _roll_forward(namespace, self._level_store())
            manual_actions = [("key", a) for a in legal]
            try:
                # The witnesses a candidate claims must be the transitions the
                # engine was actually shown. `state` is rolled forward over
                # this level only, so quoting the whole run's step count here
                # would put level-1 transitions behind a level-2 candidate --
                # in `candidates.jsonl`, which is append-only and governed by a
                # frozen contract. Global step indices are kept as identifiers
                # (they address the run's trace); the *range* is the level's.
                level_steps = len(self._level_store())
                design = probe_beat.design(
                    namespace, state, manual_actions,
                    out_path=self.candidates_path,
                    transitions=list(range(self.levels.start,
                                           len(self.store.steps))),
                    coverage="%d/%d" % (level_steps, level_steps),
                    economy=self.probe_economy)
            except Exception as exc:                   # noqa: BLE001
                design = {"error": "%s: %s" % (type(exc).__name__, exc)}
            best = (design or {}).get("best")
            if best and best.get("entropy_bits", 0) > 0:
                designed = True
                # -- the frontier's own refusals, from `ProbeEconomy` --------
                #
                # These sit *after* the entropy floor and *before* the action
                # is sent, which is the only place a refusal can save anything:
                # the design is free, the action is not. They are the two that
                # depend on the frontier having moved (collapse, and a bits
                # floor a round may set), so they are the two that ride the
                # `enabled` switch. Disabled, `gate` always allows.
                allowed, why_not = self.probe_economy.gate(
                    design, n_frontier=int(design.get("n_hypotheses") or 0))
                if allowed:
                    chosen = int(best["action"][1])
                    # Predict over the whole ablation set once, then keep the
                    # live frontier's half.
                    #
                    # `predictions` must be over the frontier the design
                    # actually partitioned, not the unfiltered one: otherwise a
                    # hypothesis this generation already retired could turn up
                    # in `survived`, and an off-frontier result would look like
                    # an on-frontier one -- which resets the vacuous streak
                    # below.
                    #
                    # `identity` must be over the whole set, for the mirror-
                    # image reason: the fingerprint's job is to say "this
                    # action, from this state", and it does that by hashing
                    # what every hypothesis predicted. Hash a shrinking
                    # frontier and the same experiment gets a new name every
                    # time the theory narrows. Disabled, the two are the same
                    # dict and this is the original line.
                    hypotheses = probe_beat.build_hypotheses(namespace)
                    for hypothesis in hypotheses:
                        try:
                            identity[hypothesis.id] = hypothesis.predict(
                                state, ("key", chosen))
                        except Exception:              # noqa: BLE001
                            identity[hypothesis.id] = "error"
                    predictions = {
                        h.id: identity[h.id]
                        for h in self.probe_economy.filter_hypotheses(hypotheses)
                        if h.id in identity}
                else:
                    refusal = why_not

        # -- the three reasons a designed probe is not worth its action ------
        #
        # Each of these was paid for in the record on 2026-07-31, and each is
        # read straight off what `ProbeLog` writes down -- the vacuous streak
        # and the fingerprint are measurements, not policy, so refusing on them
        # needs no switch and applies to every leg. All three end the same way
        # -- record the refusal as a finding, then explore -- and the
        # exploration is the point: it takes the LEAST-TRIED legal action,
        # which is precisely what breaks the standing pattern. `...-l1` spent
        # its last fourteen actions alternating ACTION4/ACTION3 and revisiting
        # states it had already been in, because the frontier kept nominating
        # the same two actions and nothing in the loop noticed.
        if chosen is not None:
            streak = self.probes.vacuous_streak
            repeat_of = self.probes.already_asked(chosen, identity)
            if streak >= MAX_VACUOUS_PROBES_IN_A_ROW:
                refusal = (
                    "%d probes in a row came back with an empty posterior: "
                    "every hypothesis refuted, including `inert`, so each "
                    "eliminated nothing (0.0 bits realised). The frontier is "
                    "built by ablating the manual, so while the manual is "
                    "unchanged the next one is vacuous too. Going for evidence "
                    "the ablation frontier cannot reach instead."
                    % streak)
            elif repeat_of is not None:
                refusal = (
                    "this is the same experiment as %s -- same action, same "
                    "prediction from every hypothesis, therefore the same "
                    "partition of the frontier. Re-running it cannot separate "
                    "anything %s did not." % (repeat_of, repeat_of))
            elif self._probes_since_theorize >= MAX_PROBES_BETWEEN_THEORIZE:
                refusal = (
                    "%d probes already spent since the last adjudication "
                    "(cap %d). The frontier is a function of the manual, and "
                    "the manual has not changed since, so further probes are "
                    "drawn from the same hypothesis set."
                    % (self._probes_since_theorize,
                       MAX_PROBES_BETWEEN_THEORIZE))
            if refusal is not None:
                chosen = None

        if designed:
            # One audit row per designed probe, carrying whichever half of the
            # policy decided it. Written after both halves have spoken so the
            # trail never says "allowed" about an action that was not sent.
            self.probe_economy.note_decision(
                allowed=refusal is None, reason=refusal or "",
                step_idx=len(self.store.steps),
                action=(design.get("best") or {}).get("action"),
                bits=(design.get("best") or {}).get("entropy_bits"))

        if chosen is None:
            # Nothing splits anything, or nothing worth an action does. Say so,
            # then explore honestly.
            if design is not None:
                self.probes.record_unrunnable(
                    reason=(refusal
                            or design.get("verdict")
                            or design.get("error")
                            or "no separating action"),
                    design_report=design, step_idx=len(self.store.steps))
            chosen = min(legal, key=lambda a: (self.action_counts.get(a, 0), a))
            record["probe"] = {"kind": "exploration",
                               "action": chosen,
                               "why": refusal or
                                      "no action separates the hypotheses; "
                                      "taking the least-tried legal action"}
            self._send(chosen, note="exploration")
            return

        self._probes_since_theorize += 1
        probe_id = self.probes.record_design(
            action=chosen, design_report=design, predictions=predictions,
            step_idx=len(self.store.steps), identity=identity,
            rationale="highest bits per action among %s" % legal)
        self.probe_economy.record_fired()
        status, envelope, frames = self._send(chosen, probe=True, note=probe_id)
        observed = grid_hash(frames[-1]) if frames else "none"
        result = self.probes.record_result(probe_id, observed=observed,
                                           status=status, n_frames=len(frames))
        # The half the old path was missing: the answer goes back into the
        # frontier. Without this the next turn rebuilds the same hypotheses,
        # re-derives the same argmax, and spends an action asking again.
        learnt = self.probe_economy.observe(result)
        record["probe"] = {"kind": "probe", "probe_id": probe_id,
                           "action": chosen,
                           "manual_survived": result["manual_survived"],
                           "information_gain_bits":
                               result["information_gain_bits"],
                           "frontier_vacuous": result["frontier_vacuous"],
                           "refuted": result["refuted"]}
        if self.probe_economy.enabled:
            record["probe"]["economy"] = learnt
        if not result["manual_survived"]:
            # What the desk is given about a refutation, and what it is not.
            #
            # It used to be given `predictions` in full: sixteen to twenty-four
            # opaque sixteen-hex-digit grid hashes, one per hypothesis, dumped
            # as JSON into a prompt that already ran to 100k characters. A hash
            # is unreadable to the reader -- it cannot be compared, decoded, or
            # reasoned from -- so that block was pure token cost, four times
            # over on a turn with four pending surprises.
            #
            # What is diagnostic is the SHAPE: how many hypotheses there were,
            # how many survived, what that is worth in bits against what the
            # design expected, and whether this is the n-th vacuous answer in a
            # row. Those are the numbers that distinguish "one rule of the
            # manual is wrong" from "the manual is missing a mechanism", which
            # is the distinction the desk is being paid to make.
            self.register.fire(
                "probe_refutation", result["verdict"],
                step_idx=len(self.store.steps) - 1,
                payload={"probe_id": probe_id, "action": chosen,
                         "observed": observed,
                         "manual_predicted": predictions.get("manual"),
                         "n_hypotheses": result["n_hypotheses"],
                         "n_survivors": result["n_survivors"],
                         "information_gain_bits":
                             result["information_gain_bits"],
                         "expected_bits": result["expected_bits"],
                         "frontier_vacuous": result["frontier_vacuous"],
                         "vacuous_streak": result["vacuous_streak"],
                         "hypothesis_space": ("every hypothesis is the manual "
                                              "or an ablation of it, plus "
                                              "`inert`")})

    # -- the account -------------------------------------------------------
    def _finish(self) -> Dict[str, Any]:
        self.scorecard = self.arc.close_scorecard()
        if not self.outcome or self.outcome == "not_started":
            self.outcome = self._terminal() or "budget_exhausted"
        self._save_all()
        return self.summary()

    def summary(self) -> Dict[str, Any]:
        return {
            "outcome": self.outcome,
            "stopped_because": self.stopped_because,
            "run_id": self.run.run_id,
            "game_id": self.game_id,
            "steps": len(self.store.steps),
            "model_calls": self.desk.calls,
            "levels_completed": (self.last_envelope or {}).get("levels_completed"),
            # The envelope's counter is whatever the last command happened to
            # carry, and it is absent on a failed one. `levels` is the run's
            # own record of the transitions, which is what a campaign and
            # `battery/INPUT_FORMAT.md`'s gap 4 both actually want.
            "levels": self.levels.summary(),
            "carried_books": self.books.carried,
            "win_levels": self.arc.win_levels,
            "score": None,          # ARC gameplay responses carry no score field
            "scorecard": self.scorecard,
            "budget": self.budget.as_json(),
            "desk": self.desk.summary(),
            "surprises": self.register.summary(),
            "turns": len(self.turns),
            "theorize_rounds": len(self.theorize_reports),
            "desk_failures": self.desk_failures,
            "certify_rounds": len(self.certify_reports),
            "elapsed_s": round(self._elapsed(), 1),
            "world": self.store.summary(),
            "action_counts": dict(sorted(self.action_counts.items())),
            "engine_dispatches": len(self.engine_rounds),
            "engines_online": self._engines_online(),
            "transfer": self.transfer_summary(),
            "bill": self.cost_curve()["totals"],
        }

    def _engines_online(self) -> Dict[str, Any]:
        """Did the engines supply the desk on every dispatch, or not.

        The claim E3 is testing stated as a number: dispatches attempted,
        dispatches in which each engine came back without raising, and the
        refusals -- which are deliveries, not failures, and are counted
        separately so the two can never be confused in a summary line.
        """
        per_engine: Dict[str, Any] = {}
        for name in ("mdl_segmenter", "cegis_miner", "zero_space"):
            rows = [r["engines"].get(name) or {} for r in self.engine_rounds]
            per_engine[name] = {
                "dispatches": len(rows),
                "delivered": sum(1 for r in rows if r.get("delivered")),
                "errored": sum(1 for r in rows if r.get("error")),
                "skipped": sum(1 for r in rows if r.get("skipped")),
                "refused_with_reason": sum(1 for r in rows
                                           if r.get("n_refusals")),
            }
        return {
            "dispatches": len(self.engine_rounds),
            "dispatch_errors": sum(1 for r in self.engine_rounds
                                   if r.get("error")),
            "candidate_rows": _count_lines(self.candidates_path),
            "per_engine": per_engine,
        }

    def _write_run_state(self) -> None:
        path = os.path.join(self.dir, "RUN_STATE.json")
        state = {"budget": self.budget.as_json(),
                 "desk": self.desk.summary(),
                 "surprises": self.register.summary(),
                 "steps": len(self.store.steps),
                 "levels": self.levels.summary(),
                 "elapsed_s": round(self._elapsed(), 1),
                 "outcome": self.outcome,
                 "stopped_because": self.stopped_because}
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(state, fh, indent=1, sort_keys=True)
            fh.write("\n")
        # The register and the desk log are otherwise written only at the end.
        # A run killed by a wall clock or a hard interrupt would lose exactly
        # the two records that say what the loop did, so they are rewritten as
        # they grow. Both are small and both are rewritten whole.
        self.register.to_jsonl(os.path.join(self.dir, "surprises.jsonl"))
        _dump(os.path.join(self.dir, "desk_log.json"), self.desk.log)
        # Deliberately NOT `cost_curve.json`: `armtools/archive.py` owns that
        # name and writes a flat per-call list there from the ledger. This is
        # the per-turn view and it is a different artefact, so it gets a
        # different file rather than racing the archiver for one.
        _dump(os.path.join(self.dir, "bill_shape.json"), self.cost_curve())

    # -- the bill shape ----------------------------------------------------
    def cost_curve(self) -> Dict[str, Any]:
        """Money against world, per desk call and per turn.

        The first live run left a per-call list; what C2 needs is the *shape* --
        what the nth dollar bought in actions and in transitions. So each call
        carries the cumulative spend and the action count standing when it was
        made, and the marginal dollars-per-action between calls falls out of
        that. Written on every command and every desk call, so a killed run
        still has its curve.

        `actions_at_call` is read from the budget, which counts only billed
        actions; the retry amplification lives in the same budget object and is
        reported beside it, because a curve plotted against HTTP requests and a
        curve plotted against billed actions are different curves and the
        difference is this API's retry wave.
        """
        calls: List[Dict[str, Any]] = []
        cumulative = 0.0
        previous_actions = 0
        for idx, entry in enumerate(self.desk.log or []):
            usd = float(entry.get("cli_cost_usd") or 0.0)
            cumulative += usd
            actions = int(entry.get("actions_at_call") or 0)
            gained = actions - previous_actions
            calls.append({
                "call_idx": idx,
                "beat": entry.get("beat"),
                "label": entry.get("label"),
                "turn": entry.get("turn"),
                "step_idx": entry.get("step_idx"),
                "usd": round(usd, 6),
                "usd_cumulative": round(cumulative, 6),
                "actions_at_call": actions,
                "actions_since_last_call": gained,
                "elapsed_ms": entry.get("elapsed_ms"),
                "output_tokens": (entry.get("usage") or {}).get("output_tokens"),
                "usd_per_action_marginal": (round(usd / gained, 6)
                                            if gained else None),
            })
            previous_actions = actions

        budget = self.budget.as_json()
        actions_ok = budget.get("actions_ok") or 0
        return {
            "calls": calls,
            "totals": {
                "desk_calls": len(calls),
                "usd": round(cumulative, 6),
                "actions_billed": actions_ok,
                "commands_sent": budget.get("commands_sent"),
                "http_amplification": budget.get("http_amplification"),
                "usd_per_billed_action": (round(cumulative / actions_ok, 6)
                                          if actions_ok else None),
                "transitions_observed": max(0, len(self.store.grids) - 1),
                "usd_per_transition": (
                    round(cumulative / max(1, len(self.store.grids) - 1), 6)
                    if len(self.store.grids) > 1 else None),
                "elapsed_s": round(self._elapsed(), 1),
            },
            "reading": (
                "`actions_at_call` counts BILLED actions; `commands_sent` counts "
                "HTTP requests, and the two differ by this API's 400-wave retry "
                "envelope. A curve against one is not a curve against the other."),
        }

    def transfer_summary(self) -> Optional[Dict[str, Any]]:
        """The cold report plus what the carried manual still had at the end."""
        if not self.carried:
            return None
        out = dict(self.transfer_report or {"stage": "cold-not-reached"})
        out["retention"] = transfer.retention(self.carried_theory,
                                              self.books.theory)
        out["final_declared_names"] = transfer.declared_names(self.books.theory)
        out["desk_calls_after_carry"] = self.desk.calls
        return out

    def _save_all(self) -> None:
        from world import adapt                        # noqa: PLC0415
        out = self.dir
        self.store.to_jsonl(os.path.join(out, "trace.jsonl"))
        self.register.to_jsonl(os.path.join(out, "surprises.jsonl"))
        with open(os.path.join(out, "levels.jsonl"), "w", encoding="utf-8",
                  newline="\n") as fh:
            for event in self.levels.events:
                fh.write(json.dumps(event, sort_keys=True))
                fh.write("\n")
        _dump(os.path.join(out, "turns.json"), self.turns)
        _dump(os.path.join(out, "theorize.json"),
              [adapt.strip_internals(r) for r in self.theorize_reports])
        _dump(os.path.join(out, "certify.json"), self.certify_reports)
        _dump(os.path.join(out, "plan.json"), self.plan_reports)
        _dump(os.path.join(out, "commit.json"), self.commit_reports)
        _dump(os.path.join(out, "desk_log.json"), self.desk.log)
        _dump(os.path.join(out, "desk_failures.json"), self.desk_failures)
        _dump(os.path.join(out, "engines_online.json"), self._engines_online())
        # Written whether or not the change is on. A leg that ran with the old
        # behaviour still says so on disk, which is what makes an A/B round
        # readable six weeks later without consulting the dispatch prompt.
        _dump(os.path.join(out, "probe_economy.json"),
              dict(self.probe_economy.as_json(),
                   decisions=self.probe_economy.decisions))
        if self.carried:
            _dump(os.path.join(out, "transfer.json"), self.transfer_summary())
        self._write_run_state()


def _book_token(text: str) -> str:
    """A short, stable name for one revision of a book.

    Used to decide whether a standing gap has already been reported: the gap
    belongs to the text, so the token is the text's digest. A rewrite that
    leaves the gap in place gets a new token and the desk hears about it again,
    which is right -- it just failed to fix it.
    """
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()[:16]


def _roll_forward(namespace, store):
    """Where the manual thinks the world is now."""
    state = namespace["initial_state"]()
    step = namespace["step"]
    for arc_action in store.actions:
        if arc_action is None:
            break
        try:
            state = step(state, commit.action_to_manual(arc_action))
        except Exception:                              # noqa: BLE001
            break
    return state


def _certify_line(report: Dict[str, Any]) -> Dict[str, Any]:
    cheap = (report.get("cheap") or {}).get("checks") or {}
    return {"cheap_green": report.get("cheap_green"),
            "responsibility_ok": (cheap.get("responsibility") or {}).get("ok"),
            "unexplained_cells": (cheap.get("responsibility") or {}).get(
                "cells_unexplained"),
            "replay_ok": (cheap.get("replay") or {}).get("ok"),
            "replay": (cheap.get("replay") or {}).get("detail"),
            "proof_layer_available": report.get("proof_layer_available")}


def _delivery(report: Any, **fields: Any) -> Dict[str, Any]:
    """One engine's row. `delivered` is about the engine, not about the answer.

    A refusal is a delivery. `cegis_miner`'s precondition -- exactly one `move`
    event per transition -- is a real claim about a world, and a real game need
    not satisfy it, so "refused, and here is the reason" is the engine working
    exactly as designed. What would falsify E3's supply-chain claim is an engine
    that raises, hangs, or comes back empty without saying why, and those are
    `error` and `skipped`, which are separate columns for that reason.
    """
    if not isinstance(report, dict):
        return {"delivered": False, "error": "no report",
                "detail": type(report).__name__}
    row: Dict[str, Any] = {
        "delivered": not report.get("error"),
        "error": report.get("error"),
        "skipped": report.get("skipped"),
    }
    row.update({k: v for k, v in fields.items() if v is not None})
    return row


def _engine_delivery(engines: Dict[str, Any]) -> Dict[str, Any]:
    """Per engine, per dispatch: did it deliver, how much, and what did it say."""
    seg = engines.get("mdl_segmenter")
    mined = engines.get("cegis_miner")
    law = engines.get("zero_space")

    seg_row = _delivery(
        seg,
        chosen_operator=(seg or {}).get("chosen_operator"),
        n_tracks=len((seg or {}).get("tracks") or []) or None,
        candidate_rows=(seg or {}).get("candidates"),
        variant_ms=[v.get("ms") for v in ((seg or {}).get("variants") or [])]
        or None)

    mine_tracks = (mined or {}).get("tracks") or []
    mine_row = _delivery(
        mined,
        n_tracks=len(mine_tracks) or None,
        n_refusals=len((mined or {}).get("refusals") or []) or None,
        refusals=((mined or {}).get("refusals") or [])[:4] or None,
        verdict=(mined or {}).get("verdict"),
        n_rules=sum(len(t.get("rules") or []) for t in mine_tracks) or None)

    adequacy = (law or {}).get("evidence_adequacy") or {}
    law_row = _delivery(
        law,
        n_laws=(law or {}).get("n_laws"),
        n_global_laws=(law or {}).get("n_global_laws"),
        features=(law or {}).get("features"),
        cells_used=(law or {}).get("cells_used"),
        cells_dynamic=(law or {}).get("cells_dynamic"),
        narrowed=(law or {}).get("narrowed"),
        difference_rank=(law or {}).get("difference_rank"),
        adequacy=(adequacy.get("verdict") or "")[:24] or None,
        ms=(law or {}).get("ms"))

    return {"mdl_segmenter": seg_row, "cegis_miner": mine_row,
            "zero_space": law_row,
            "not_dispatched": sorted((engines.get("not_dispatched") or {}).keys())}


def _count_lines(path: str) -> int:
    if not os.path.exists(path):
        return 0
    with open(path, encoding="utf-8") as fh:
        return sum(1 for line in fh if line.strip())


def _dump(path: str, obj: Any) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, indent=1, sort_keys=True, default=str)
        fh.write("\n")
