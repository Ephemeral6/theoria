"""The environment interface `protocol.carry` is written against.

**This module imports no world, and neither does `protocol`.**  That is the
whole design: A3's sealing argument is that the transfer arm's *source* contains
no path to a trace, a transition function or a candidate stream — a claim about
what an arm did not read cannot be evidenced by the arm's own report — and the
only way to keep that property while making the driver reusable is for the world
to arrive as an argument.

An `Executor` is shaped like a game API on purpose, and the shape is the
quota model:

* `first_frame()` costs **one frame and zero actions**.  It is the arm's entire
  observation before it commits to anything.
* `execute(actions)` costs one action per action and hands back frames.  On a
  live game that line is the budget, which is why the meter counts the two
  separately.

Nothing else.  No level spec, no reachable set, no `is_win` the arm may call on a
hypothetical state — an executor that offered one would be handing over the
answer key, and `theoria-arm` plugging into this interface should not be able to
do by accident what A3 arranged not to be able to do at all.
"""

import json
import os
from typing import Dict, List, Optional, Sequence

Frame = List[List[int]]


class Executor:
    """Implement these two and A6's protocol will drive your world.

    `name` is used for artefact filenames and appears in every report; make it
    identify the level, not the run.
    """

    name: str = "<level>"

    def first_frame(self) -> Frame:
        raise NotImplementedError

    def execute(self, actions: Sequence[str]) -> Dict[str, object]:
        """Run `actions` from the initial state; return frames and the win flag.

        Required keys: `frames` (n+1 of them), `wins` (aligned), `actions`
        (those actually taken — an executor may stop early on a win), `win`.
        `actions_spent` is derived if absent.
        """
        raise NotImplementedError


def write_execution(path: str, record: Dict[str, object]) -> str:
    """Persist an execution as an ordinary trace, so `certify.replay` can read it.

    The four-key row format every trace in this repository uses — `{t, frame,
    action, win}`, sorted keys, tight separators, LF — with the outgoing action
    on each row and `null` on the last.  A3's `a3world.executor.write_execution`,
    restated here so that an executor for somebody else's world does not have to
    import A3's world module to get the format right.

    Nothing in the file says which arm produced it, which is deliberate: the
    cheap layer must not be able to tell.
    """
    frames = record["frames"]
    actions: List[Optional[str]] = list(record.get("actions") or []) + [None]
    wins = record["wins"]
    if len(actions) < len(frames):
        actions += [None] * (len(frames) - len(actions))
    # D-A6-005: `actions` is padded because a short one is *expected* — an
    # executor may stop early on a win (line 48) and the row format carries
    # `null` where no action was taken, so the padding states something true.
    # `wins` was neither padded nor checked, so an executor returning fewer wins
    # than frames reached `wins[t]` below as an IndexError partway through the
    # file, after some rows had already been written.  It is still not padded,
    # and that is the honest choice rather than the lazy one: `win` is read by
    # `certify_a3.cheap`'s goal-predicate pass, so a fabricated `False` on the
    # tail rows would either report a real win as a replay mismatch or conceal
    # one — a defect in the executor charged to the manual.  The contract says
    # `wins` is aligned with `frames`; an executor that broke it is told the
    # shape it returned, before anything is written.
    if len(wins) != len(frames):
        raise ValueError(
            "executor returned %d wins for %d frames; `Executor.execute` "
            "requires `wins` aligned with `frames` (executor_api.py:44-50).  "
            "`wins` is not padded the way `actions` is, because `win` is a "
            "claim about the world that the certify layer reads back as "
            "evidence." % (len(wins), len(frames)))
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        for t, frame in enumerate(frames):
            handle.write(json.dumps(
                {"t": t, "frame": frame, "action": actions[t],
                 "win": bool(wins[t])},
                sort_keys=True, separators=(",", ":")) + "\n")
    return path


def write_frame(path: str, frame: Frame) -> str:
    """One frame, as the single-frame file the rebuilder reads."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps({"t": 0, "frame": frame}, sort_keys=True,
                                separators=(",", ":")) + "\n")
    return path


def one_row_trace(frame: Frame, path: str) -> str:
    """Frame 0 as a one-row trace, so the cheap layer can run before acting.

    Not a new checker: `certify.replay.certify` on a single frame runs exactly
    the render, responsibility and goal-predicate passes and has no transition to
    replay.  Reusing it beats a bespoke render check, because a bespoke check is
    one more thing that could be lenient in a way the real one is not.  A3's
    `transfer.one_row_trace`, moved here because it is part of the protocol
    rather than part of A3.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps({"t": 0, "frame": frame, "action": None,
                                 "win": False},
                                sort_keys=True, separators=(",", ":")) + "\n")
    return path
