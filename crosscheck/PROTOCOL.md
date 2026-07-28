# A2-crosscheck — the protocol both directions run under

Two A0 cold starts were written independently in this repository: `a0-spike/`
(engine-rig track, world **S**) and `cold-start-a0/` (theory-compiler track,
world **C**). Each closed its own loop on its own world and reported success.
That is one implementation per result, which [Theoria.md](../Theoria.md) §8 lists
as a limitation to disclose. This experiment compresses it: run each pipeline
against the *other* world and see which findings survive.

The unit of comparison is deliberately blunt: **a total function from a picture
and an action to the next picture.** Everything else — objects, rules, events,
theorems — is a claim about how you got there.

## What a visitor may see

Exactly one import:

```python
from crosscheck.bridge import open_world
world = open_world("C")            # or "S"
brief = world.briefing()           # actions, grid sizes, goals, frame 0
ep    = world.rollout("c-alpha", ["LEFT", "LEFT", "UP"])
```

* `world.actions` — the action alphabet. Both worlds happen to use
  `UP/DOWN/LEFT/RIGHT`; that coincidence is what makes the experiment cheap and
  it is not a licence to assume the semantics are shared.
* `world.rollout(level_id, actions)` — reset, replay, get frames back. Every
  query is metered in `world.ledger`; exploration cost is a reported number.
* `LevelInfo` — grid size, and the goal as *"the object that starts at (r,c)
  must end on (r,c)"*. Not a colour, not a name.
* `episode.won[t]` — whether the goal held at frame *t*.

Level ids are neutral (`c-alpha`, `s-ev3`). The originals — `match`,
`mismatch`, `a0-no-button` — state their own answers.

## What a visitor may not see

Reading any of these voids the run, and saying so afterwards is cheaper than
being caught by the referee's numbers:

| Sealed | Why |
|---|---|
| the host world's `world/` package | the transition function |
| the host track's `theory/`, including `generated*/` | the answer, written out |
| the host track's `README.md`, `THEORIZE_LOG.md`, `GENERATOR_REPORT.md`, `A0_REPORT.md`, `DECISIONS.md`, `GROUND_TRUTH.md`, `STATUS.md` | every one of them states the mechanics in prose |
| the host track's `artifacts/` | traces carry event labels; reports carry grades |
| `PARTNER_SYNC.md` entries about the host track | same |

Your *own* track's code is yours to use freely — that is the point. You are
porting your pipeline, not rewriting it.

## What a direction delivers

Four files under `crosscheck/<direction>/` (`s_on_c/` or `c_on_s/`):

**`manual.dsl`** — the adjudicated manual, in `CONTRACTS/dsl_grammar_v0.2.md`
form, `semantics:` section included. This is what the agent is accountable for.

**`predictor.py`** — the manual's executable form, behind one function:

```python
WORLD_ID = "C"
def step_frame(level_id: str, frame: list[list[int]], action: str) -> list[list[int]]:
    """Total, deterministic, and loud: raise on any frame the manual refuses."""
```

It must be *compiled from* `manual.dsl`, not written beside it. Never `True` for
a guard you cannot compile and never `pass` for an effect — that failure is
already on the record twice in this repository (`GENERATOR_REPORT.md`, and
`gen_exec`'s dropped `negated` flag found on day one of this run) and it is the
one thing that makes a green certify meaningless.

**`plan.json`** — `{"<level_id>": {"verdict": "solved"|"unsolvable",
"actions": [...], "reason": "..."}}`. `actions` for solved levels; `reason` for
unsolvable ones, stated in the manual's own vocabulary. A verdict of
`unsolvable` with no reason is a search result, not a theory.

**`THEORIZE_LOG.md`** — every adjudication and why, plus an **adaptation
ledger**: for each module of your pipeline you reused, whether it ported
unchanged, needed configuration, or had to be rewritten. That ledger is a
headline result, not paperwork: it measures how much of "the framework works"
was really "this world works".

## How it is scored

The referee holds both worlds' ground truth and both tracks' native manuals, and
runs `crosscheck/judge/`:

1. **replay exactness** — your `step_frame` against every frame of every episode
   the bridge served you;
2. **held-out prediction** — your `step_frame` against the true world over
   *every* state the level can represent, reachable or not. Both native runs
   found their worst rule here and neither found it by replay;
3. **rule-set recovery** — your `manual.dsl` against the host track's, rule by
   rule, adjudicated rather than string-matched;
4. **plan** — your actions executed in the true world; your `unsolvable`
   verdicts against the truth;
5. **divergence** — your predictor against the host track's *native* predictor
   over the same full state space. Every disagreement is one of you wrong, or
   the world being ambiguous, and each is attributed.

The last one is why the experiment exists. Where both predictors are wrong **in
the same place**, the mistake is not either implementation's — it is the
framework's, and it goes in [FINDINGS.md](FINDINGS.md) under its own heading.
