"""Exploration through the sealed bridge — a rewrite of `a0-spike/pipeline/explore.py`.

The original planned episodes by running a breadth-first search *inside* the
world: it imported `world.sokoban2.step` and walked the true transition function
to find a discriminating state, then replayed the prefix. Through the bridge
there is no `step` to walk, so the search and the evidence-gathering are the same
activity and every state the search visits has to be paid for in actions.

Two ideas keep the bill down, and both are in the original's spirit:

* **prefix replay** (Theoria 1.10b) — `rollout` resets, so returning to a state
  costs its shortest known prefix and nothing else;
* **harvest the tail** — a rollout hands back *every* intermediate frame, so an
  episode that ends in one untried action can be extended by a fixed
  continuation and every step of that continuation is evidence too. The
  continuation is a De Bruijn sequence over the action alphabet, which is
  deterministic and covers every short action pattern.

The loop closes when no (state, action) pair is untried. That is a *reachable*
closure, not a domain closure — the standing lesson of D-TC-012, and the reason
the manual is also swept over states no episode reached.
"""

from typing import Any, Dict, List, Sequence, Tuple

Frame = List[List[int]]
FrameKey = Tuple[Tuple[int, ...], ...]


def frame_key(frame: Sequence[Sequence[int]]) -> FrameKey:
    return tuple(tuple(int(v) for v in row) for row in frame)


def de_bruijn(alphabet: Sequence[str], order: int) -> List[str]:
    """A cyclic sequence containing every length-`order` word exactly once.

    Deterministic and seedless: the tail of every episode is the same tail, so a
    run is byte-reproducible without a random number generator.
    """
    k = len(alphabet)
    a = [0] * (k * order)
    sequence: List[int] = []

    def db(t: int, p: int) -> None:
        if t > order:
            if order % p == 0:
                sequence.extend(a[1:p + 1])
        else:
            a[t] = a[t - p]
            db(t + 1, p)
            for j in range(a[t - p] + 1, k):
                a[t] = j
                db(t + 1, 1)

    db(1, 1)
    return [alphabet[i] for i in sequence]


class Exploration:
    """The evidence set for one level, plus what it cost."""

    def __init__(self, level_id: str) -> None:
        self.level_id = level_id
        self.prefix: Dict[FrameKey, List[str]] = {}
        self.transitions: Dict[Tuple[FrameKey, str], FrameKey] = {}
        self.frames: Dict[FrameKey, Frame] = {}
        self.won: Dict[FrameKey, bool] = {}
        self.episodes: List[Dict[str, Any]] = []

    # ------------------------------------------------------------- accounting

    def n_states(self) -> int:
        return len(self.prefix)

    def n_transitions(self) -> int:
        return len(self.transitions)

    def actions_spent(self) -> int:
        return sum(len(e["actions"]) for e in self.episodes)

    def untried(self, alphabet: Sequence[str]) -> List[Tuple[FrameKey, str]]:
        out = []
        for key in self.prefix:
            for action in alphabet:
                if (key, action) not in self.transitions:
                    out.append((key, action))
        # deterministic order: shortest prefix first, then the frame itself
        out.sort(key=lambda ka: (len(self.prefix[ka[0]]), ka[0], ka[1]))
        return out

    # ------------------------------------------------------------- harvesting

    def absorb(self, episode: Any) -> int:
        """Record one episode's states and transitions. Returns states added."""
        added = 0
        keys = [frame_key(f) for f in episode.frames]
        for i, key in enumerate(keys):
            if key not in self.prefix:
                self.prefix[key] = list(episode.actions[:i])
                self.frames[key] = [list(row) for row in episode.frames[i]]
                self.won[key] = bool(episode.won[i])
                added += 1
            elif len(episode.actions[:i]) < len(self.prefix[key]):
                self.prefix[key] = list(episode.actions[:i])
        for i, action in enumerate(episode.actions):
            self.transitions[(keys[i], action)] = keys[i + 1]
        self.episodes.append(
            {"actions": list(episode.actions),
             "frames": [[list(r) for r in f] for f in episode.frames],
             "won": list(episode.won),
             "purpose": episode.purpose}
        )
        return added


def explore(world: Any, level_id: str, tail_order: int = 3,
            max_actions: int = 6000) -> Exploration:
    """Close the reachable set of `level_id`, paying in actions."""
    alphabet = list(world.actions)
    tail = de_bruijn(alphabet, tail_order)
    ex = Exploration(level_id)

    ex.absorb(world.rollout(level_id, [], purpose="frame 0"))
    ex.absorb(world.rollout(level_id, tail, purpose="de Bruijn sweep"))

    while True:
        pending = ex.untried(alphabet)
        if not pending:
            break
        key, action = pending[0]
        plan = ex.prefix[key] + [action] + tail
        if ex.actions_spent() + len(plan) > max_actions:
            raise RuntimeError(
                "exploration budget exhausted on %s: %d actions, %d pairs left"
                % (level_id, ex.actions_spent(), len(pending))
            )
        ex.absorb(world.rollout(level_id, plan,
                                purpose="witness %s from a state at depth %d"
                                        % (action, len(ex.prefix[key]))))
    return ex


def situation_census(ex: Exploration, palette: Dict[str, int],
                     alphabet: Sequence[str]) -> Dict[str, int]:
    """How often each (action, colour-ahead) situation was witnessed.

    `a0-spike/pipeline/explore.py` classified situations by geometry specific to
    a box; here the observable situation type is simply *what colour is in front
    of the player*, which is the distinction World C's rules turn out to draw.
    """
    from a2_crosscheck.s_on_c.percept import DELTA, read_frame

    counts: Dict[str, int] = {}
    for (key, action), _dst in ex.transitions.items():
        p = read_frame(ex.frames[key], palette)
        dr, dc = DELTA[action]
        ahead = (p.player[0] + dr, p.player[1] + dc)
        colour = p.colour_at(ahead)
        counts["%s/%s" % (action, colour)] = counts.get("%s/%s" % (action, colour), 0) + 1
    return dict(sorted(counts.items()))
