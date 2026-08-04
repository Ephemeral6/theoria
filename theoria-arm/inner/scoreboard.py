"""scoreboard -- the second witness to a level boundary, and the denominator.

**The finding this module was written from (A27).** The board item says "the arm
cannot see a win even if it gets one". Read against the code, that is half
right, and the half that is right is the expensive half.

What the arm *does* read, today, without this module:

* `levels_completed`, off **every** gameplay envelope, on every recorded step.
  `inner/loop.py:_record` passes it to `LevelLog.observe` before it returns, and
  an increase fires `_on_level_boundary` immediately. The in-band counter is not
  a blind spot and has not been one since `inner/levels.py` was written.
* `state == "WIN"` with levels remaining, at the top of every turn, which drives
  `_try_advance_level`. Also not a blind spot.

What the arm does **not** read, at any point in a leg:

* `score`. Not from an oversight -- ARC gameplay responses carry no `score`
  field at all. The key set is `action_input, available_actions, frame,
  full_reset, game_id, guid, levels_completed, state, win_levels`
  (`armtools/archive.py`, the score-obligation note). `inner/loop.py:_summary`
  states it in one line: `"score": None, # ARC gameplay responses carry no
  score field`.
* `level_scores`, `level_actions`, `level_count`, and -- the one that matters --
  **`level_baseline_actions`**. All four exist only on a scorecard.

And the scorecard is fetched exactly once per leg, by `close_scorecard`, in
`_finish`, **after `_main_loop` has returned**. Closing is destructive: D-015
records that a closed card can never be re-fetched. So every scorecard-side fact
about a leg arrives strictly after the leg can act on it.

That is the true shape of the blindness, and it is narrower and worse than the
board item's wording. The arm is not blind to a win. It is blind to *the price of
one*.

**The decisive number.** `runs/20260728T012311Z-g50t-first-contact-salvage2/
ledger.jsonl` carries a closed g50t scorecard whose `level_baseline_actions` is
`[78, 175, 179, 230, 96, 54, 67]`. Level 1 costs a reference solver 78 actions.
The best recorded leg of this arm spent 33. That number was on the wire, in a
document the arm could have asked for at any moment, from the first RESET
onward -- and the arm asked for it once, at the end, when it was a post-mortem
instead of a plan. A leg that knew it held 27 actions against a 78-action
reference would at least know what it was doing.

**Theoria.md, and what it actually licenses.** Phase 2 layer 4 says the ledger's
`env_step` carries "全帧、动作、关卡边界——level 若非 API 字段则由 score 跳变推导,
现勘定": the level boundary is derived from a score jump *if level is not an API
field*. It is an API field here, so the counter is the primary signal and the
score jump is not required. Same paragraph, next clause, is the one still owing:
"对账义务:账本推得的分数必须等于 API scorecard 分数,不等 = incident". The
reconciliation obligation cannot be met from a ledger whose steps carry no
score. `archive.reconcile` says so and writes `score_reconciliation:
"unavailable"`. A scorecard read *during* the leg is the only thing that puts a
score into the record at all.

So this module does two things and refuses a third.

1. **A second witness.** `ScoreWatch` consumes readings from either source --
   the envelope (free, every step) or a scorecard (a request, no action quota)
   -- normalises them to the same shape, and turns any increase in `score`,
   `level_scores[i]`, or a levels-completed counter into a named event. Two
   independent witnesses to the same boundary can *disagree*, and since neither
   has ever been observed to move, the disagreement is the finding, not a
   nuisance. `corroborate()` reports it rather than picking a winner.

2. **The denominator.** `reach()` is the arithmetic above, as an instrument:
   the reference cost of the level being played, the actions spent on it, the
   actions left, and the gap. It is consulted every turn and it is the only
   number here that could change a decision mid-leg.

3. **Refused: it does not decide anything.** No beat branches on a `ScoreWatch`
   verdict, no surprise is fired (`inner/surprise.py` closes the set at seven
   and says an eighth is a change to `Theoria.md` 1.10(d), not to a file), and
   no model call is bought. `reach()` returning `below_reference` does not stop
   a leg. Making it stop one is a decision with its own evidence, and this is
   not that.

**The rungs.**

* `off` -- nothing observed, nothing recorded. Every artefact byte-identical to
  a run made before this file existed.
* `envelope` -- the free rung, and the default. Reads only fields already on
  every `Step`. Costs no request, no action, no dollar. It adds a `scoreboard`
  block to the turn record and the summary; that is a change to the *record*,
  which is the thing A27 found silent, and it is not a change to behaviour.
* `scorecard` -- adds bounded `GET /api/scorecard/{card_id}` readings.
  **Default off**, because it spends requests against the shared pool and that
  is not a decision this file gets to make on its own.

**Absence is absence.** A watch that has taken no reading reports
`boundary_observed: null` and `verdict: "not_measured"`, never `false` and never
`0`. A watch that has taken readings and seen nothing move reports
`false` / `"measured_absent"`. Those are different claims and the record keeps
them apart -- see `tests/test_scoreboard.py`, which is mostly about that.
"""

from typing import Any, Dict, List, Optional

#: The rungs, weakest first.
PROTOCOLS = ("off", "envelope", "scorecard")

#: The free rung. See the module docstring for why the default is not `off`:
#: `envelope` reads nothing the arm was not already given and spends nothing,
#: and A27's finding is precisely that the record said nothing.
DEFAULT_PROTOCOL = "envelope"

#: Turns between scorecard readings on the `scorecard` rung. A reading costs one
#: request through the proxy and no action quota, but requests are not free
#: either (`harness/spend.py`), and the fields that move -- `score`,
#: `level_scores`, `levels_completed` -- only move at a boundary, which is at
#: best a once-per-78-actions event on g50t. Four matches
#: `loop.MIN_NEW_FRAMES_BETWEEN_THEORIZE` for the same reason it does there:
#: asking again before the world could have moved buys a re-read of the same
#: document.
SCORECARD_EVERY_N_TURNS = 4


# ===================================================================== readings
def reading_from_envelope(envelope: Any, *, source: str = "envelope"
                          ) -> Dict[str, Any]:
    """One gameplay envelope, in the common reading shape.

    `score` is `None` and always will be: no ARC gameplay response carries the
    field. It is `None` rather than `0.0` on purpose -- `0.0` would be a claim
    that the score was read and found to be zero, and every downstream diff
    would then compare a number nobody measured.
    """
    body = envelope if isinstance(envelope, dict) else {}
    return {
        "source": source,
        "score": None,
        "level_scores": None,
        "level_actions": None,
        "level_baseline_actions": None,
        "level_count": body.get("win_levels"),
        "levels_completed": body.get("levels_completed"),
        "state": body.get("state"),
    }


def reading_from_scorecard(card: Any, *, game_id: Optional[str] = None,
                           guid: Optional[str] = None,
                           source: str = "scorecard") -> Dict[str, Any]:
    """One scorecard document, in the common reading shape.

    A card holds `environments[]`, each holding `runs[]` -- one row per session
    guid, because a card outlives a RESET. The row is selected by `guid` when
    one is known and falls back to the last row, and `row_selected_by` says
    which happened: a summed or guessed row would put another session's actions
    into this leg's denominator.
    """
    out: Dict[str, Any] = {
        "source": source,
        "score": None,
        "level_scores": None,
        "level_actions": None,
        "level_baseline_actions": None,
        "level_count": None,
        "levels_completed": None,
        "state": None,
        "row_selected_by": None,
        "card_id": None,
    }
    if not isinstance(card, dict):
        return out

    out["card_id"] = card.get("card_id")
    if card.get("score") is not None:
        out["score"] = _as_float(card.get("score"))
    if card.get("total_levels_completed") is not None:
        out["levels_completed"] = card.get("total_levels_completed")

    envs = [e for e in (card.get("environments") or []) if isinstance(e, dict)]
    if game_id is not None:
        matched = [e for e in envs if e.get("id") == game_id]
        if matched:
            envs = matched
    if not envs:
        return out
    env = envs[0]
    if env.get("level_count") is not None:
        out["level_count"] = env.get("level_count")

    rows = [r for r in (env.get("runs") or []) if isinstance(r, dict)]
    if not rows:
        return out
    row = None
    if guid is not None:
        for candidate in rows:
            if candidate.get("guid") == guid:
                row = candidate
                out["row_selected_by"] = "guid"
                break
    if row is None:
        row = rows[-1]
        out["row_selected_by"] = "last_row" if guid is None else "last_row_guid_absent"

    out["level_scores"] = _as_float_list(row.get("level_scores"))
    out["level_actions"] = _as_int_list(row.get("level_actions"))
    out["level_baseline_actions"] = _as_int_list(row.get("level_baseline_actions"))
    if row.get("levels_completed") is not None:
        out["levels_completed"] = row.get("levels_completed")
    if row.get("score") is not None:
        out["score"] = _as_float(row.get("score"))
    if row.get("state") is not None:
        out["state"] = row.get("state")
    return out


def _as_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_float_list(value: Any) -> Optional[List[float]]:
    if not isinstance(value, list):
        return None
    return [(_as_float(v) or 0.0) for v in value]


def _as_int_list(value: Any) -> Optional[List[int]]:
    if not isinstance(value, list):
        return None
    out: List[int] = []
    for v in value:
        try:
            out.append(int(v))
        except (TypeError, ValueError):
            out.append(0)
    return out


# ======================================================================= watch
class ScoreWatch:
    """The arm's standing reading of the scoreboard, over a leg.

    One instance per run. It holds no reference to the loop, opens no socket and
    reads no globals: every number it has was handed to it. That is what makes
    the negative controls in `tests/test_scoreboard.py` possible without an arm.
    """

    def __init__(self, protocol: str = DEFAULT_PROTOCOL, *,
                 game_id: Optional[str] = None,
                 offline: bool = False,
                 scorecard_every: int = SCORECARD_EVERY_N_TURNS) -> None:
        if protocol not in PROTOCOLS:
            raise ValueError(
                "%r is not a scoreboard protocol. The rungs are %s, weakest "
                "first; %r is the default and reads only what the arm was "
                "already given."
                % (protocol, ", ".join(PROTOCOLS), DEFAULT_PROTOCOL))
        self.protocol = protocol
        self.game_id = game_id
        #: Whether this leg is running against `proxy/mock` rather than ARC.
        #:
        #: This is not decoration. A scan of every ledger in the three arms
        #: (`runs/20260802T2100Z-A27-level-boundary-detector/MEASUREMENT.json`)
        #: found `level_baseline_actions: [8, 8, 8]` recorded against **three
        #: different game ids** -- `g50t`, `sk48` and `ar25` -- alongside
        #: `level_count: 3`. That vector is the mock's constant, not any game's
        #: roster: the real g50t is `[78, 175, 179, 230, 96, 54, 67]` over seven
        #: levels and the real sk48 is eight levels long. A `reach` report built
        #: on the mock's 8 would say `at_or_above_reference` on a leg that in
        #: reality is a third of the way to level 1, which is the exact
        #: confusion this module exists to end -- so the provenance travels
        #: with the number rather than being left to the reader.
        self.offline = bool(offline)
        self.scorecard_every = max(1, int(scorecard_every))

        #: The last reading from each source, so the two witnesses diff against
        #: their own history and never against each other's.
        self.last: Dict[str, Dict[str, Any]] = {}
        self.readings: Dict[str, int] = {"envelope": 0, "scorecard": 0}
        self.events: List[Dict[str, Any]] = []
        #: Every scorecard reading's turn, so a summary can say when the last
        #: one was taken rather than only that one was.
        self.scorecard_turns: List[int] = []
        self.last_scorecard_turn: Optional[int] = None
        #: The denominator, once anything has carried it. Sticky: a later
        #: reading that omits it does not erase it.
        self.baseline_actions: Optional[List[int]] = None
        self.level_count: Optional[int] = None
        self.reach_reports: List[Dict[str, Any]] = []

    @property
    def enabled(self) -> bool:
        return self.protocol != "off"

    @property
    def reads_scorecard(self) -> bool:
        return self.protocol == "scorecard"

    # -- the two witnesses -------------------------------------------------
    def observe(self, reading: Dict[str, Any], *, turn: Optional[int] = None,
                step_idx: Optional[int] = None,
                actions_spent: Optional[int] = None) -> List[Dict[str, Any]]:
        """Diff one reading against the previous reading from the same source.

        Returns the events it fired, which is `[]` on the overwhelming majority
        of calls and has been `[]` on every call ever made against live data.
        """
        if not self.enabled:
            return []
        source = reading.get("source") or "envelope"
        self.readings[source] = self.readings.get(source, 0) + 1
        if reading.get("level_baseline_actions"):
            self.baseline_actions = list(reading["level_baseline_actions"])
        if reading.get("level_count") is not None:
            self.level_count = reading["level_count"]

        previous = self.last.get(source)
        self.last[source] = dict(reading)
        if previous is None:
            # The first reading from a source establishes the floor. It is not
            # a jump: comparing it against an assumed zero would report a
            # boundary on any leg that resumed a card with a score already on
            # it, which is a fabricated boundary and the worst thing here.
            return []

        fired: List[Dict[str, Any]] = []
        stamp = {"source": source, "turn": turn, "step_idx": step_idx,
                 "actions_spent": actions_spent}

        before, after = previous.get("score"), reading.get("score")
        if before is not None and after is not None and after > before:
            fired.append(dict(stamp, event="score_moved", signal="score",
                              **{"from": before, "to": after,
                                 "delta": round(after - before, 6)}))

        b_levels = previous.get("levels_completed")
        a_levels = reading.get("levels_completed")
        if (isinstance(b_levels, int) and isinstance(a_levels, int)
                and a_levels > b_levels):
            fired.append(dict(stamp, event="level_boundary",
                              signal="levels_completed:%s" % source,
                              **{"from": b_levels, "to": a_levels}))

        for index, (was, now) in enumerate(zip(previous.get("level_scores") or [],
                                               reading.get("level_scores") or [])):
            if now > was:
                fired.append(dict(stamp, event="level_score_moved",
                                  signal="level_scores[%d]" % index,
                                  level_index=index, level=index + 1,
                                  **{"from": was, "to": now}))

        self.events.extend(fired)
        return fired

    def observe_envelope(self, envelope: Any, **kwargs: Any) -> List[Dict[str, Any]]:
        return self.observe(reading_from_envelope(envelope), **kwargs)

    def observe_scorecard(self, card: Any, *, guid: Optional[str] = None,
                          turn: Optional[int] = None,
                          source: str = "scorecard",
                          **kwargs: Any) -> List[Dict[str, Any]]:
        reading = reading_from_scorecard(card, game_id=self.game_id, guid=guid,
                                         source=source)
        if turn is not None:
            self.scorecard_turns.append(turn)
            self.last_scorecard_turn = turn
        return self.observe(reading, turn=turn, **kwargs)

    def due_for_scorecard(self, turn: int) -> Dict[str, Any]:
        """Should a scorecard be read on this turn.

        Phrased and recorded the way `goal.proposal_due` is: the refusals are
        written down with the numbers they read, because a cadence that only
        appears in the record when it fires is indistinguishable from one that
        always fires.
        """
        checks = [
            {"check": "the scorecard rung is on", "ok": self.reads_scorecard,
             "read": self.protocol},
            {"check": "at least %d turn(s) since the last reading"
                      % self.scorecard_every,
             "ok": (self.last_scorecard_turn is None
                    or turn - self.last_scorecard_turn >= self.scorecard_every),
             "read": (None if self.last_scorecard_turn is None
                      else turn - self.last_scorecard_turn)},
        ]
        refusals = ["NO -- %s [read: %s]" % (c["check"], c["read"])
                    for c in checks if not c["ok"]]
        return {"due": not refusals, "checks": checks,
                "refused_because": refusals}

    # -- the cross-check ---------------------------------------------------
    def corroborate(self, envelope_levels_completed: Optional[int]
                    ) -> Dict[str, Any]:
        """Do the two witnesses agree about how many levels are done.

        Neither has ever been seen to move, so this has never been anything but
        `agree` on a live leg -- which is itself worth recording, because a
        check that has never been shown to be capable of saying no has not been
        shown to check anything. `tests/test_scoreboard.py` makes it say every
        one of its four answers.
        """
        card = (self.last.get("scorecard") or {}).get("levels_completed")
        if card is None and envelope_levels_completed is None:
            return {"verdict": "not_measured",
                    "detail": "neither witness has reported a count",
                    "envelope": None, "scorecard": None}
        if card is None:
            return {"verdict": "envelope_only",
                    "detail": "no scorecard has been read this leg, so the "
                              "envelope counter stands uncorroborated",
                    "envelope": envelope_levels_completed, "scorecard": None}
        if envelope_levels_completed is None:
            return {"verdict": "scorecard_only",
                    "detail": "no envelope has carried the counter",
                    "envelope": None, "scorecard": card}
        if card == envelope_levels_completed:
            return {"verdict": "agree", "detail": "both witnesses read %d" % card,
                    "envelope": envelope_levels_completed, "scorecard": card}
        return {
            "verdict": "disagree",
            "detail": "the envelope counter reads %d and the scorecard reads "
                      "%d. One of the two is wrong about this leg and the arm "
                      "cannot tell which; it is recorded, not resolved."
                      % (envelope_levels_completed, card),
            "envelope": envelope_levels_completed, "scorecard": card,
        }

    # -- the denominator ---------------------------------------------------
    def reach(self, *, level: int, actions_spent_this_level: Optional[int],
              actions_left: Optional[int], turn: Optional[int] = None
              ) -> Dict[str, Any]:
        """How this leg's remaining actions compare to the level's reference cost.

        **What `level_baseline_actions` is and is not.** It is the number of
        actions a reference solver took on that level. It is NOT a lower bound
        and beating it is the entire point of the exercise, so nothing here
        says a level is unreachable. What it does say is the ratio, in the two
        numbers it read. On g50t level 1 the reference is 78; the best leg this
        arm has recorded spent 33 actions in total. A leg holding 27 more
        actions against a 78-action reference is not "failing to solve level
        1" -- it is a third of the way to being able to try, and those are
        different sentences in a paper.

        Unknown stays unknown: with no scorecard reading there is no baseline,
        and the report says `not_measured` rather than substituting a guess.
        """
        report: Dict[str, Any] = {
            "turn": turn,
            "level": level,
            "actions_spent_this_level": actions_spent_this_level,
            "actions_left": actions_left,
            "baseline_source": None,
            "baseline_actions_for_level": None,
            "remaining_reference": None,
            "headroom": None,
            "verdict": "not_measured",
        }
        baseline = self.baseline_actions
        if not baseline:
            report["reading"] = (
                "no reading has carried `level_baseline_actions`, so this leg "
                "does not know what the level costs a reference solver. That "
                "field exists only on a scorecard; on the `%s` rung no "
                "scorecard is read during the leg." % self.protocol)
            self.reach_reports.append(report)
            return report

        report["baseline_source"] = (
            "MOCK scorecard.level_baseline_actions -- this leg ran offline "
            "against proxy/mock, whose card reports [8, 8, 8] whatever game id "
            "it is handed. Not a fact about the game."
            if self.offline else "scorecard.level_baseline_actions")
        report["baseline_is_from_a_mock"] = self.offline
        index = level - 1
        if not 0 <= index < len(baseline):
            report["verdict"] = "level_out_of_range"
            report["reading"] = (
                "level %d has no entry in a %d-long `level_baseline_actions`; "
                "the roster and the level counter disagree and that is "
                "recorded rather than clamped." % (level, len(baseline)))
            self.reach_reports.append(report)
            return report

        cost = baseline[index]
        report["baseline_actions_for_level"] = cost
        spent = actions_spent_this_level or 0
        remaining = max(0, cost - spent)
        report["remaining_reference"] = remaining
        if actions_left is None:
            report["verdict"] = "actions_left_unknown"
            report["reading"] = (
                "the reference cost of level %d is %d action(s) and %d have "
                "been spent on it, but this call was given no remaining-action "
                "count, so the comparison is not made."
                % (level, cost, spent))
            self.reach_reports.append(report)
            return report

        report["headroom"] = actions_left - remaining
        report["verdict"] = ("at_or_above_reference" if actions_left >= remaining
                             else "below_reference")
        report["reading"] = (
            "level %d cost a reference solver %d action(s). This leg has spent "
            "%d on it and holds %d more, against %d still to go at reference "
            "pace: %s by %d. The baseline is a reference cost, not a lower "
            "bound -- being below it is not a proof that the level cannot be "
            "cleared, it is the size of the bet."
            % (level, cost, spent, actions_left, remaining,
               "ahead" if report["headroom"] >= 0 else "short",
               abs(report["headroom"])))
        self.reach_reports.append(report)
        return report

    # -- the record --------------------------------------------------------
    def boundary_verdict(self) -> Dict[str, Any]:
        """Observed, measured-absent, or not measured. Never `0`.

        This is the negative control's whole subject. A leg that took readings
        and saw nothing move has *measured* an absence and says so; a leg that
        took no readings has measured nothing, and reporting that as `false`
        would turn "we did not look" into "we looked and there was none".
        """
        boundaries = [e for e in self.events if e["event"] == "level_boundary"]
        moves = [e for e in self.events
                 if e["event"] in ("score_moved", "level_score_moved")]
        total_readings = sum(self.readings.values())
        if not self.enabled:
            return {"verdict": "off", "boundary_observed": None,
                    "score_moved": None, "readings": 0,
                    "detail": "the scoreboard rung is `off`; nothing was read."}
        if total_readings < 2:
            return {
                "verdict": "not_measured", "boundary_observed": None,
                "score_moved": None, "readings": total_readings,
                "detail": "a jump needs two readings to be a jump and this "
                          "watch has %d. Absence of a boundary here is absence "
                          "of a measurement, not a measured absence."
                          % total_readings,
            }
        if boundaries or moves:
            return {
                "verdict": "observed", "boundary_observed": bool(boundaries),
                "score_moved": bool(moves), "readings": total_readings,
                "detail": "%d boundary event(s) and %d score move(s) over %d "
                          "reading(s)." % (len(boundaries), len(moves),
                                           total_readings),
            }
        return {
            "verdict": "measured_absent", "boundary_observed": False,
            "score_moved": False, "readings": total_readings,
            "detail": "%d reading(s) were taken and no counter, score or "
                      "per-level score ever increased. This is a measured "
                      "absence: the instrument looked and saw nothing."
                      % total_readings,
        }

    def summary(self) -> Dict[str, Any]:
        return {
            "protocol": self.protocol,
            "game_id": self.game_id,
            "offline": self.offline,
            "readings": dict(sorted(self.readings.items())),
            "scorecard_readings_on_turns": list(self.scorecard_turns),
            "events": list(self.events),
            "boundary": self.boundary_verdict(),
            "level_count": self.level_count,
            "level_baseline_actions": (list(self.baseline_actions)
                                       if self.baseline_actions else None),
            "last_reading_by_source": {k: dict(v) for k, v in
                                       sorted(self.last.items())},
            "reach": (dict(self.reach_reports[-1]) if self.reach_reports
                      else None),
            "reach_reports": len(self.reach_reports),
            "reading": self._reading(),
        }

    def _reading(self) -> str:
        verdict = self.boundary_verdict()
        line = verdict["detail"]
        if self.baseline_actions is None:
            line += (" No `level_baseline_actions` was read during this leg, "
                     "so the arm played without knowing what a level costs.")
        elif self.offline:
            line += (" A baseline WAS read -- %s -- but this leg ran offline "
                     "against proxy/mock, whose card answers [8, 8, 8] for "
                     "every game id. It is the mock's constant and says "
                     "nothing about the game." % (self.baseline_actions,))
        else:
            line += (" The level roster's reference costs were on hand: %s."
                     % (self.baseline_actions,))
        if self.protocol == "envelope":
            line += (" On the `envelope` rung there is no score to move: ARC "
                     "gameplay responses carry no `score` field, so `score` "
                     "and `level_scores` are null by construction and only the "
                     "counter can fire. A null here is the API's shape, not a "
                     "zero.")
        return line


# =========================================================== the goal handoff
#: The name the witness asks the desk to use for the goal it may now write. Kept
#: distinct from `goal.TARGET_THEOREM_PREFIX`, which names the target the desk
#: believes in but *cannot* compile; this one names a target the world has been
#: seen to satisfy.
WITNESS_THEOREM_PREFIX = "the_goal_the_world_satisfied_at"


def witness_from_boundary(event: Dict[str, Any], *,
                          final_grid: Optional[List[List[int]]] = None,
                          final_grid_hash: Optional[str] = None,
                          opening_grid_hash: Optional[str] = None,
                          actions_this_level: Optional[int] = None,
                          reach: Optional[Dict[str, Any]] = None,
                          corroboration: Optional[Dict[str, Any]] = None,
                          ) -> Dict[str, Any]:
    """The evidence a recorded boundary makes available, as one artefact.

    **Why this exists, and what it is for.** `Theoria.md` 1.8 puts the goal
    clause in the manual, and R1b measured what happens when the arm asks for
    one: on `20260801T001851Z-R1b-g50t-a` the desk declined three times out of
    three, each time with the theorem
    `the_goal_is_absent_because_no_instance_can_name_the_socket`, and
    `inner/goal.prompt_rider` records the reading of those refusals -- they are
    arguments about *reach*, not about confidence. The desk will not name a
    winning position it has never seen the world occupy, because a goal true in
    the wrong states stops the planner at the first node and is worse than none.

    A recorded boundary is exactly the evidence that refusal was waiting for.
    The step whose envelope carried the increment is the first frame of the next
    level, so the step *before* it is the last frame of the level that was
    cleared: a state the world has been observed to treat as winning. That is
    not a goal clause -- turning one witnessed state into a general condition is
    adjudication and belongs to the desk -- but it is the one thing the desk has
    never had.

    This function is the observation half and it is complete: it captures the
    witness. The proposal half is `witness_rider` below, which renders it, and
    the wiring that would put that rider on a theorize call is **deliberately
    not written** -- see the note on `witness_rider`.
    """
    witness: Dict[str, Any] = {
        "witness": "level_cleared",
        "from_level": event.get("from_level"),
        "to_level": event.get("to_level"),
        "signal": event.get("signal"),
        "step_idx": event.get("step_idx"),
        "action": event.get("action"),
        "turn": event.get("turn"),
        "actions_spent_at_boundary": event.get("actions_spent"),
        "actions_this_level": actions_this_level,
        "opening_grid_hash": opening_grid_hash,
        "final_grid_hash": final_grid_hash,
        "final_grid": final_grid,
        "reach_at_boundary": reach,
        "corroboration": corroboration,
        "goal_evidence": (
            "the state at step %s is the last frame of level %s, and the world "
            "advanced out of it. It is a state the world has been observed to "
            "treat as terminal-and-won. Generalising it into a `goal` clause "
            "is the desk's call, not this arm's."
            % (event.get("step_idx"), event.get("from_level"))),
    }
    return witness


def witness_rider(witness: Dict[str, Any]) -> str:
    """The witnessed win, as Markdown, for a theorize call already paid for.

    **This is written and not wired, on purpose.** `inner/goal.py` refuses to
    fire a surprise of its own because `inner/surprise.py` closes the set at
    seven, and the same argument applies here: a rider must ride on a call some
    surprise has already bought, and the call it should ride on is the one a
    boundary itself provokes. But no live leg has ever crossed a boundary, so
    the shape of that call has never been observed, and every claim about which
    turn it lands on would be a guess dressed as a design. Wiring it is a
    separate decision with its own evidence -- the first recorded boundary is
    that evidence -- and A27 asked for the observation half implemented and the
    other half designed. This is the seam, and it is drawn where the evidence
    stops.

    It is a pure function of the witness: no state, no I/O, no model call, and
    calling it costs nothing.
    """
    lines = [
        "## A level was cleared, and that is new evidence about the goal",
        "",
        "Every previous ask for a `goal` clause was made against a manual that "
        "had never seen the world satisfy one. That is no longer true.",
        "",
        "* Level %s was completed at step %s, on turn %s, after %s action(s) "
        "on that level (%s in the leg)."
        % (witness.get("from_level"), witness.get("step_idx"),
           witness.get("turn"), witness.get("actions_this_level"),
           witness.get("actions_spent_at_boundary")),
        "* The signal was `%s`. The command that carried it was `%s`."
        % (witness.get("signal"), witness.get("action")),
        "* The last frame of that level hashes to `%s`; the level opened at "
        "`%s`." % ((witness.get("final_grid_hash") or "?")[:16],
                   (witness.get("opening_grid_hash") or "?")[:16]),
        "",
        "The state below is a state the world was observed to treat as won. "
        "It is one instance, not a condition.",
        "",
        "Two answers are acceptable.",
        "",
        "1. **A `goal` clause** that is TRUE in that state and FALSE in the "
        "states preceding it on the same level. You now have a positive "
        "example to check it against, which every earlier ask lacked. It must "
        "still be false in the states you have already seen on the current "
        "level, or the planner stops at its first node.",
        "2. **A `theorem` named `%s_...`** if the witnessed state still cannot "
        "be said in the goal section -- naming which forms you tried against "
        "this specific frame and what each one lacked. A refusal that engages "
        "an actual positive example is worth more than three that could not."
        % (WITNESS_THEOREM_PREFIX,),
        "",
        "What is not acceptable is repeating an argument written before this "
        "frame existed. The reason for the previous refusals was that no "
        "winning state had been seen. One has.",
    ]
    return "\n".join(lines)
