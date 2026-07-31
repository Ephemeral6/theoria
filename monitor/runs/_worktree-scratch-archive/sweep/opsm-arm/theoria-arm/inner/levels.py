"""The level boundary: where the domain travels and the problem does not.

`Theoria.md` C3 calls the claim "transfer", and `inner/books.py` already fixes
its mechanical meaning:

    `theory.dsl` is the *domain* -- what travels between levels -- and the
    level's layout is the *problem* ... so C3's "transfer" has a mechanical
    meaning: the same `theory.dsl` against a different computed problem.

Everything in this module follows from taking that sentence literally.

**Why a boundary needs handling at all.** ARC advances a level in-band: no
action causes it, the envelope's `levels_completed` simply increments and the
next frame is a different board. Three parts of the loop read the trace as one
continuous trajectory and are wrong across such a jump:

* `certify.cheap` replays the manual's `step` over every recorded action and
  compares grids. Across the boundary the manual predicts level 1's next state
  and observes level 2's opening board, so it fires `replay_mismatch` --
  and a `replay_mismatch` is a surprise, and a surprise is the *only* thing
  that calls the desk. The arm would pay opus prices to repair a manual that
  was never wrong. On the one live run of this arm, replay and render
  mismatches were 8 of 8 surprises recorded; a multi-level run would
  manufacture two more of them per level for free.
* `books.problem_from_frames` computes the board from the cells that never
  varied. Pooled across a boundary, "never varied" is the intersection of two
  unrelated boards -- which is not a description of either.
* `loop._roll_forward` rolls the manual forward from the initial state over
  every action, to tell probe where the world is now.

So the beats that reason over a trajectory get `store.since(level_start)`,
and the boundary is recorded rather than smoothed over.

**What is deliberately NOT done here.** The alternative design is to model the
level advance *inside* the manual, as an event with a precondition and an
effect. That is a stronger and more interesting claim -- it would let the
playbook plan *through* a level boundary -- and it is not what this does.
Segmenting is the conservative reading: it says the domain is silent about
level advance, rather than saying something about it that no evidence
supports. Recorded as a decision, not slipped in: see `DECISIONS.md` D-A3-001.
"""

from typing import Any, Dict, List, Optional


class LevelLog:
    """Level boundaries as first-class events.

    `battery/INPUT_FORMAT.md`'s known-gaps list, item 4: *"No level-boundary
    event. `levels_completed` is still a running counter, and it is `0` on
    every envelope row that carries it."* This is that event. The counter was
    always there (`world/frames.Step.levels_completed`, captured since the
    first live run); nothing branched on it and nothing wrote it down as a
    transition.
    """

    def __init__(self) -> None:
        self.events: List[Dict[str, Any]] = []
        #: Index into `FrameStore.steps` where the current level's trajectory
        #: begins. Level 1 begins at the first step of the run.
        self.starts: List[int] = [0]
        self.completed = 0
        #: Set when the counter reaches the game's last level: the game is won
        #: and there is no level after this one.
        self.finished = False
        #: RESETs spent probing for the next level after a `WIN` that the
        #: roster says is not the last one. Bounded so an arm that cannot
        #: advance stops rather than spins, and **reset on a successful
        #: advance** -- it is a budget per boundary, not per run, and a
        #: seven-level game has to cross six of them.
        self.advance_attempts = 0

        #: What each RESET-after-WIN actually returned. This is the first thing
        #: in the repository that will ever observe a level completion, so it
        #: keeps the evidence whichever way the probe goes.
        self.reset_probes: List[Dict[str, Any]] = []

    @property
    def level(self) -> int:
        """1-based: the level being played now."""
        return len(self.starts)

    @property
    def start(self) -> int:
        return self.starts[-1]

    def observe(self, *, levels_completed: Optional[int], step_idx: int,
                action: str, turn: Optional[int] = None,
                actions_spent: Optional[int] = None,
                final_level: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Called for every recorded step. Returns the event, or None.

        Only an *increase* is a boundary. The field is absent on failed
        commands and on some envelopes, and absence is not a decrease --
        reading `None` as 0 would report a boundary on the next successful
        command and cut the trajectory in half for no reason.
        """
        if levels_completed is None:
            return None
        if levels_completed <= self.completed:
            return None
        if final_level is not None and levels_completed >= final_level:
            # The game is won, not advanced. Count it, but do not open a level
            # that does not exist: the caller's boundary handling drops the
            # problem and the compiled forms, which on a winning run would
            # delete exactly the artefacts that say how it was won.
            self.completed = levels_completed
            self.finished = True
            return None

        event = {
            "event": "level_boundary",
            "signal": "levels_completed",
            "from_level": self.level,
            "to_level": self.level + 1,
            "levels_completed": levels_completed,
            "levels_completed_before": self.completed,
            # The boundary is observed *at* this step: the step whose envelope
            # carries the new count is the first frame of the new level.
            "step_idx": step_idx,
            "action": action,
            "turn": turn,
            "actions_spent": actions_spent,
        }
        # A jump of more than one is possible in principle and would mean a
        # level was completed without a frame of its own being recorded. Say so
        # rather than quietly counting it as one.
        if levels_completed - self.completed > 1:
            event["skipped"] = levels_completed - self.completed - 1

        self.completed = levels_completed
        self.starts.append(step_idx)
        self.events.append(event)
        return event

    def force(self, *, signal: str, step_idx: int, note: str,
              turn: Optional[int] = None,
              actions_spent: Optional[int] = None) -> Dict[str, Any]:
        """Record a boundary the counter did not report.

        The counter is one of two possible signals and it is the one this repo
        has never observed (see `LEVEL_SIGNAL_UNKNOWN` in `inner/loop.py`). If
        the world instead says `WIN` with levels still to play, that is a level
        boundary too, and it has to be recorded through the same door so that
        `starts` stays the single answer to "where does this level's trajectory
        begin".
        """
        self.completed += 1
        event = {"event": "level_boundary", "signal": signal,
                 "from_level": self.level, "to_level": self.level + 1,
                 "levels_completed": self.completed,
                 "step_idx": step_idx, "note": note, "turn": turn,
                 "actions_spent": actions_spent}
        self.starts.append(step_idx)
        self.events.append(event)
        return event

    def summary(self) -> Dict[str, Any]:
        return {
            "levels_completed": self.completed,
            "level": self.level,
            "boundaries": len(self.events),
            "finished": self.finished,
            "starts": list(self.starts),
            "events": list(self.events),
            "reset_probes": list(self.reset_probes),
        }
