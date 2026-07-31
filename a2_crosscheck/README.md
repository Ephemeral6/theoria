# crosscheck — two independent A0s, each made to theorise the other's world

This repository grew two A0 cold starts by accident of its own division of
labour. `cold-start-a0/` is the theory-compiler track's; `a0-spike/` is
engine-rig's. Neither track saw the other's design, and the two worlds have
almost nothing in common — one is a sokoban whose pushes slide two cells, the
other is a cart that must press a button to open a door. Both closed the loop.
Both reported success.

Two successes, one implementation each. [Theoria.md](../Theoria.md) §8 lists
single-implementation bias as a limitation to disclose. This is the experiment
that shrinks it: **swap the worlds.** Run each pipeline against the other's
world, give it trajectories and an action alphabet and nothing else, and see
which of the two reports was about the framework and which was about the author.

```bash
python -m pytest a2_crosscheck/tests -q          # the seal, and the referee's calibration
python -m a2_crosscheck.judge.score              # score both directions
python a2_crosscheck/s_on_c/run.py               # reproduce one direction
python a2_crosscheck/c_on_s/run.py
```

Results and their reading: **[FINDINGS.md](FINDINGS.md)**. The rules both
directions ran under: **[PROTOCOL.md](PROTOCOL.md)**.

## Layout

| Path | What |
|---|---|
| `bridge/` | the sealed handoff. A visitor's only import |
| `judge/` | the referee: both worlds' truth, both tracks' manuals, the sweep |
| `s_on_c/` | a0-spike's pipeline on cold-start-a0's world |
| `c_on_s/` | cold-start-a0's pipeline on a0-spike's world |
| `runs/` | the record of each run, timestamped |

## The one interface

Every predictor in this directory — the two worlds, the two incumbent manuals,
the two cross-run manuals — is wrapped in

```python
step_frame(level_id, frame, action) -> frame
```

That is not a convenience. It is the only contract both tracks' compiled manuals
can wear, so it is the only place they can be made to disagree in public. It is
also full-frame responsibility (Theoria constraint 2) by construction: a theory
that tracks the right positions and draws the wrong picture fails on `==`. And
it takes a *frame*, not an internal state, which is what lets the referee ask
about states nobody ever reached.

## Two sweeps, never averaged

`representable` is every state a level's own state type admits. `reachable` is
the subset it actually gets to from its initial configuration. Both are
reported.

The gap is not bookkeeping. The incumbent manual for world C's second level
scores **92/92 reachable and 150/300 representable**: it sank the door into the
static board, which is exactly right for a level whose button does not exist and
exactly wrong as a statement about the domain. `CONTRACTS/dsl_grammar_v0.2.md`
calls that the standing lesson — a rule can be right as a problem solution and
wrong as a domain — and averaging the two numbers would have hidden it.

## Calibration

The referee recomputes each track's own claim from scratch before it is allowed
to grade anybody. If these drift, the numbers downstream are measuring the
referee:

| Claim, as published by its track | Recomputed here |
|---|---|
| `cold-start-a0`: 59 reachable states | 59 |
| `cold-start-a0`: manual 233/236 correct | 233/236 |
| `a0-spike`: manual exact on every well-formed state | 0 wrong in 48,240 |
| `a0-spike`: `s-beta` unsolvable, `s-alpha` optimal in 2 | confirmed by BFS |

## Where the contamination is, and what was done about it

The orchestrator of this run read both worlds' source: writing the bridge and
the referee requires knowing each world's palette and state space. So the
orchestrator is **not** blind, and no claim here rests on its judgement about
what the worlds are.

Both cross-runs were therefore delegated to agents that had only
`crosscheck/bridge/`, under the seal in [PROTOCOL.md](PROTOCOL.md), and the
grading is mechanical — a sweep and an `==`, with no place for an opinion to
enter. Where a human judgement was unavoidable (attributing a divergence), it
was made adversarially and both sides are recorded in
[FINDINGS.md](FINDINGS.md).
