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

import json
import os
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

import _bootstrap                                     # noqa: F401  (sys.path)

from harness.arc import ArcThroughProxy, frames_of
from harness.budget import Budget, BudgetExhausted
from harness.modelcall import CostCeilingReached, ModelDesk
from world.frames import FrameStore, Step, grid_hash

from . import certify, commit, plan as plan_beat, probe as probe_beat, theorize
from .books import Books
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


class TheoriaArm:
    def __init__(self, *, env_base: str, run, game_id: str,
                 budget_actions: int = 120,
                 budget_commands: int = 2000,
                 reserve_for_probes: int = 0,
                 offline: bool = False,
                 model: str = "claude-opus-5",
                 cost_ceiling_usd: Optional[float] = 20.0,
                 wall_clock_s: float = DEFAULT_WALL_CLOCK_S,
                 resume_state: Optional[Dict[str, Any]] = None):
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

        self.arc = ArcThroughProxy(env_base, game_id, self.budget,
                                   on_command=self._on_command)
        self.store = FrameStore()
        self.books = Books(os.path.join(self.dir, "books"))
        self.register = Register()
        self.probes = probe_beat.ProbeLog(os.path.join(self.dir, "probes.jsonl"))
        self.candidates_path = os.path.join(self.dir, "candidates.jsonl")

        pricing = None
        try:
            from proxy.cost import PriceTable, DEFAULT_TABLE      # noqa: PLC0415
            pricing = PriceTable.load(DEFAULT_TABLE).reference()
        except Exception:                              # noqa: BLE001
            pricing = None

        self.desk = ModelDesk(
            run.run, model=model, pricing_ref=pricing,
            cost_ceiling_usd=None if offline else cost_ceiling_usd,
            transcript_dir=os.path.join(self.dir, "desk"))

        #: How many commands had been recorded when the desk was last called.
        #: The evidence gate in `_theorize_and_certify` turns on it.
        self._frames_at_last_theorize = -1

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
        return self.store.add(step)

    def _send(self, action_id: int, *, probe: bool = False, note: str = ""):
        status, envelope = self.arc.act(action_id, probe=probe)
        self.action_counts[action_id] = self.action_counts.get(action_id, 0) + 1
        step = self._record("ACTION%d" % action_id, status, envelope,
                            probe=probe, note=note)
        return status, envelope, step.frames

    def _terminal(self) -> Optional[str]:
        state = (self.last_envelope or {}).get("state")
        return state if state in ("WIN", "GAME_OVER") else None

    def _legal_actions(self) -> List[int]:
        actions = list(self.arc.available_actions or [])
        # ACTION6 is the click family; its payload shape is unsolved in this
        # repo (1,254 attempts, every one HTTP 500) and it is not offered here.
        # Recorded rather than silently filtered: see RUN_STATE.md.
        return [a for a in actions if 1 <= a <= 7 and a != 6]

    # -- the run -----------------------------------------------------------
    def play(self) -> Dict[str, Any]:
        self.arc.open_scorecard(
            tags=["theoria", "p8", "first-contact"],
            opaque={"run_id": self.run.run_id, "prompt_id": "P-8"})

        status, envelope = self.arc.reset()
        self._record("RESET", status, envelope)
        if status != 200:
            self.outcome = "reset_failed"
            self.stopped_because = "RESET did not return 200 after %d attempts" % 40
            return self._finish()

        try:
            self._opening_sweep()
            self._main_loop()
        except BudgetExhausted as exc:
            self.stopped_because = "budget: %s" % exc
        except CostCeilingReached as exc:
            self.stopped_because = "cost ceiling: %s" % exc
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

    def _main_loop(self) -> None:
        turn = 0
        while True:
            turn += 1
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
                plan_beat.surprises_from(plan_report, self.register)

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
        new_frames = len(self.store.steps) - self._frames_at_last_theorize
        if (self.books.theory.strip()
                and new_frames < MIN_NEW_FRAMES_BETWEEN_THEORIZE
                and self.budget.actions_left > MIN_NEW_FRAMES_BETWEEN_THEORIZE):
            record["theorize"] = (
                "skipped: %d surprise(s) pending but only %d new transition(s) "
                "since the last call (want %d). Going to get more."
                % (len(self.register.pending), new_frames,
                   MIN_NEW_FRAMES_BETWEEN_THEORIZE))
            if not self.certify_reports:
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
            try:
                report = theorize.run(
                    self.desk, self.books, self.store, self.candidates_path,
                    surprises=pending,
                    certify_report=(self.certify_reports[-1]
                                    if self.certify_reports else None),
                    step_idx=len(self.store.steps))
            except CostCeilingReached:
                raise                                  # the run's honest end
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
                self._frames_at_last_theorize = len(self.store.steps)
                self._write_run_state()
                break
            self.register.handled("theorize")
            self.theorize_reports.append(report)
            rounds += 1
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
            self._frames_at_last_theorize = len(self.store.steps)
        if not self.certify_reports and self.books.theory.strip():
            record["certify"] = _certify_line(self._certify())

    def _certify(self) -> Dict[str, Any]:
        compiled = (self.theorize_reports[-1].get("_compiled")
                    if self.theorize_reports else None) or {}
        report = certify.run(self.books, self.store, commit.action_to_manual,
                             compiled)
        self.certify_reports.append(report)
        certify.surprises_from(report, self.register)
        return report

    def _commit(self, namespace, plan_report, record) -> None:
        def send(action_id):
            status, envelope, frames = self._send(action_id, note="commit")
            return status, envelope, frames

        report = commit.execute(namespace, plan_report["plan"], send=send,
                                store=self.store,
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
        predictions: Dict[str, str] = {}

        if namespace is not None:
            state = _roll_forward(namespace, self.store)
            manual_actions = [("key", a) for a in legal]
            try:
                design = probe_beat.design(
                    namespace, state, manual_actions,
                    out_path=self.candidates_path,
                    transitions=list(range(len(self.store.steps))),
                    coverage="%d/%d" % (len(self.store.steps),
                                        len(self.store.steps)))
            except Exception as exc:                   # noqa: BLE001
                design = {"error": "%s: %s" % (type(exc).__name__, exc)}
            best = (design or {}).get("best")
            if best and best.get("entropy_bits", 0) > 0:
                chosen = int(best["action"][1])
                for hypothesis in probe_beat.build_hypotheses(namespace):
                    try:
                        predictions[hypothesis.id] = hypothesis.predict(
                            state, ("key", chosen))
                    except Exception:                  # noqa: BLE001
                        predictions[hypothesis.id] = "error"

        if chosen is None:
            # Nothing splits anything. Say so, then explore honestly.
            if design is not None:
                self.probes.record_unrunnable(
                    reason=(design.get("verdict")
                            or design.get("error")
                            or "no separating action"),
                    design_report=design, step_idx=len(self.store.steps))
            chosen = min(legal, key=lambda a: (self.action_counts.get(a, 0), a))
            record["probe"] = {"kind": "exploration",
                               "action": chosen,
                               "why": "no action separates the hypotheses; "
                                      "taking the least-tried legal action"}
            self._send(chosen, note="exploration")
            return

        probe_id = self.probes.record_design(
            action=chosen, design_report=design, predictions=predictions,
            step_idx=len(self.store.steps),
            rationale="highest bits per action among %s" % legal)
        status, envelope, frames = self._send(chosen, probe=True, note=probe_id)
        observed = grid_hash(frames[-1]) if frames else "none"
        result = self.probes.record_result(probe_id, observed=observed,
                                           status=status, n_frames=len(frames))
        record["probe"] = {"kind": "probe", "probe_id": probe_id,
                           "action": chosen,
                           "manual_survived": result["manual_survived"],
                           "refuted": result["refuted"]}
        if not result["manual_survived"]:
            self.register.fire(
                "probe_refutation", result["verdict"],
                step_idx=len(self.store.steps) - 1,
                payload={"probe_id": probe_id, "action": chosen,
                         "predictions": predictions, "observed": observed})

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
        }

    def _write_run_state(self) -> None:
        path = os.path.join(self.dir, "RUN_STATE.json")
        state = {"budget": self.budget.as_json(),
                 "desk": self.desk.summary(),
                 "surprises": self.register.summary(),
                 "steps": len(self.store.steps),
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

    def _save_all(self) -> None:
        from world import adapt                        # noqa: PLC0415
        out = self.dir
        self.store.to_jsonl(os.path.join(out, "trace.jsonl"))
        self.register.to_jsonl(os.path.join(out, "surprises.jsonl"))
        _dump(os.path.join(out, "turns.json"), self.turns)
        _dump(os.path.join(out, "theorize.json"),
              [adapt.strip_internals(r) for r in self.theorize_reports])
        _dump(os.path.join(out, "certify.json"), self.certify_reports)
        _dump(os.path.join(out, "plan.json"), self.plan_reports)
        _dump(os.path.join(out, "commit.json"), self.commit_reports)
        _dump(os.path.join(out, "desk_log.json"), self.desk.log)
        _dump(os.path.join(out, "desk_failures.json"), self.desk_failures)
        self._write_run_state()


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


def _dump(path: str, obj: Any) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, indent=1, sort_keys=True, default=str)
        fh.write("\n")
