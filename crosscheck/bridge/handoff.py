"""The handoff surface: everything a visiting pipeline may see of a sealed world.

The A2-crosscheck experiment runs each A0 track's pipeline against the *other*
track's world. For the result to mean anything, the visitor has to arrive as
cold as the original author did. So this module defines the only sanctioned
channel, and it carries exactly three things:

  * the **action alphabet** -- the names you may send;
  * **trajectories on demand** -- reset, replay an action prefix, get frames back;
  * the **goal**, stated observationally: an object identified by where it starts
    must end up on a named cell, and each frame says whether that has happened.

It does not carry the world's transition function, its source, its ground truth,
its optimal plans, its author's manual, or its author's prose. Those live behind
`crosscheck/judge/`, which only the referee runs.

Why frames-on-demand rather than a fixed dump: `a0-spike`'s explorer plans
episodes by prefix replay (Theoria 1.10b -- returning to a discriminating state
costs actions, not model calls), and a static trace cannot serve that. Every
query is metered, so "what did this cost" is a number in the run record rather
than a claim.

The predictor contract, and why it is frame-to-frame
----------------------------------------------------
A cross-run's deliverable is

    step_frame(level_id, frame, action) -> frame

and nothing else. Not a state class, not a rule list -- a total function from a
picture and an action to the next picture. Three reasons:

1. It is the only interface both tracks' compiled manuals can be wrapped in, so
   the two pipelines become comparable on one world instead of on their own.
2. It is full-frame responsibility (Theoria constraint 2) by construction: a
   theory that tracks the right positions and draws the wrong picture fails.
3. It lets the referee sweep states the visitor never reached, which is the whole
   of the held-out test. Both A0 runs found their worst rule that way, and
   neither found it by replay.

A predictor that refuses a frame must raise. Silence is the failure mode this
repository keeps re-learning (`GENERATOR_REPORT.md`, and gen_exec's own
`negated` bug found on day one of this run).
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

Cell = Tuple[int, int]
Frame = List[List[int]]


@dataclass(frozen=True)
class LevelInfo:
    """What a visitor is told about one level, before it acts.

    `goal_object_start` names the goal's subject by *where it begins* rather than
    by colour or by name. Colour would leak the palette; a name would leak the
    word table. Where a thing starts is visible in frame 0.
    """

    level_id: str
    height: int
    width: int
    goal_object_start: Cell
    goal_cell: Cell
    note: str = ""

    def as_json(self) -> Dict[str, Any]:
        return {
            "level_id": self.level_id,
            "height": self.height,
            "width": self.width,
            "goal_object_start": list(self.goal_object_start),
            "goal_cell": list(self.goal_cell),
            "note": self.note,
        }


@dataclass
class Episode:
    """One reset-and-replay. `frames` has one more entry than `actions`."""

    level_id: str
    actions: List[str]
    frames: List[Frame]
    won: List[bool]
    purpose: str = ""

    def as_json(self) -> Dict[str, Any]:
        return {
            "level_id": self.level_id,
            "actions": list(self.actions),
            "frames": [[list(row) for row in f] for f in self.frames],
            "won": list(self.won),
            "purpose": self.purpose,
        }


@dataclass
class Ledger:
    """What the visit cost. Exploration is not free and the number is a metric."""

    episodes: int = 0
    actions: int = 0
    frames: int = 0
    by_level: Dict[str, int] = field(default_factory=dict)

    def charge(self, level_id: str, n_actions: int) -> None:
        self.episodes += 1
        self.actions += n_actions
        self.frames += n_actions + 1
        self.by_level[level_id] = self.by_level.get(level_id, 0) + n_actions

    def as_json(self) -> Dict[str, Any]:
        return {
            "episodes": self.episodes,
            "actions": self.actions,
            "frames": self.frames,
            "by_level": dict(sorted(self.by_level.items())),
        }


class SealedWorld:
    """A foreign world, seen only through frames.

    Subclasses supply `_reset` / `_advance` / `_render` / `_won` over an opaque
    internal state. Nothing about that state is exposed; a visitor that wants to
    know what the world is tracking has to infer it from pictures, which is the
    experiment.
    """

    world_id: str = ""
    actions: Tuple[str, ...] = ()
    background: int = 0
    rendering_note: str = ""

    def __init__(self) -> None:
        self.ledger = Ledger()

    # ----------------------------------------------------------- to implement

    def levels(self) -> List[LevelInfo]:
        raise NotImplementedError

    def _reset(self, level_id: str) -> Any:
        raise NotImplementedError

    def _advance(self, level_id: str, state: Any, action: str) -> Any:
        raise NotImplementedError

    def _render(self, level_id: str, state: Any) -> Frame:
        raise NotImplementedError

    def _won(self, level_id: str, state: Any) -> bool:
        raise NotImplementedError

    # --------------------------------------------------------------- the API

    def level(self, level_id: str) -> LevelInfo:
        for info in self.levels():
            if info.level_id == level_id:
                return info
        raise KeyError("no such level: %r (have %s)"
                       % (level_id, [i.level_id for i in self.levels()]))

    def rollout(self, level_id: str, actions: Sequence[str],
                purpose: str = "") -> Episode:
        """Reset and replay `actions`. The only way to see anything move."""
        self.level(level_id)                      # validates the id
        for action in actions:
            if action not in self.actions:
                raise ValueError("unknown action %r; alphabet is %s"
                                 % (action, list(self.actions)))
        state = self._reset(level_id)
        frames = [self._render(level_id, state)]
        won = [self._won(level_id, state)]
        for action in actions:
            state = self._advance(level_id, state, action)
            frames.append(self._render(level_id, state))
            won.append(self._won(level_id, state))
        self.ledger.charge(level_id, len(actions))
        return Episode(level_id=level_id, actions=list(actions), frames=frames,
                       won=won, purpose=purpose)

    def initial_frame(self, level_id: str) -> Frame:
        """Frame 0. Free -- looking at a level costs no actions."""
        return self._render(level_id, self._reset(level_id))

    def briefing(self) -> Dict[str, Any]:
        """Everything the visitor is allowed to be told, in one object."""
        return {
            "world_id": self.world_id,
            "actions": list(self.actions),
            "background": self.background,
            "rendering_note": self.rendering_note,
            "levels": [info.as_json() for info in self.levels()],
            "initial_frames": {
                info.level_id: self.initial_frame(info.level_id)
                for info in self.levels()
            },
        }


# ------------------------------------------------------------------ helpers

def frames_equal(a: Frame, b: Frame) -> bool:
    return [list(r) for r in a] == [list(r) for r in b]


def frame_key(frame: Frame) -> Tuple[Tuple[int, ...], ...]:
    return tuple(tuple(int(v) for v in row) for row in frame)


def describe_frame(frame: Frame) -> str:
    return "\n".join("".join("%X" % v for v in row) for row in frame)


def parse_frame(text: str) -> Frame:
    return [[int(ch, 16) for ch in line] for line in text.strip().splitlines()]
