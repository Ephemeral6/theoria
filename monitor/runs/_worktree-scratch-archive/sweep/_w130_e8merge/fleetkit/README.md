# fleetkit

The repository-agnostic core of a self-assembling agent fleet, extracted from
Theoria's `monitor/` — where it ran a 12-agent fleet through 349 commits in a
day.

It provides **coordination, not intelligence**: somewhere for work to sit that
several agents can take from without colliding, a channel they can be
interrupted on, and a state layout both live in. The judgment stays in the
agents.

```bash
python -m fleetkit init --prefix MyFleet-     # writes fleet.json
python -m fleetkit board list
python -m fleetkit board claim W-1
python -m fleetkit bus say W-1 "..."
```

`FLEET_HOME` selects the state tree, so two fleets can share a machine.

## What is here, and what is not

| module | lines | status |
|---|---|---|
| `config.py` | ~150 | new — the whole project-specific surface |
| `board.py` | ~360 | ported: atomic claim, territory exclusivity, lanes, sweep |
| `bus.py` | ~190 | ported: acknowledgement, urgent interruption, cursors |

**Not yet ported**, and named so the gap is not mistaken for a decision:
`dispatch.py`, `reflex.py`, `quota.py`, `assign.py`, `ci_merge.py` — about
1,400 further lines. They are the launching and merging half. The coordination
half is what a second project needs first, and it is what is proven here.

## The design claim, and its evidence

The kernel is ~2,100 lines and almost none of it is about Theoria. The
project-specific surface turned out to be four things, and `fleet.json` is all
of them:

* `task_prefix` — how a live worker is recognised on this machine;
* `territories` — the directories a branch may touch;
* `protected_root` — root files no automatic merge may touch;
* `lanes`, `plain_item` — queue partitioning and dashboard wording.

`config.THEORIA_EXAMPLE` holds what Theoria itself uses, as a worked example
rather than as a default. A second project changes every value in it.

## Acceptance: what has actually been run

S18's bar is *"initialise it in a brand-new empty repository, start two
workers, have them claim two toy items off the board and deliver them — it
counts only if it runs."*

`tests/test_fresh_repo.py` runs that: a fresh `git init`, a generated
`fleet.json`, two items, two workers claiming and delivering, the board log
checked, plus territory exclusivity proven both ways (a second worker is
refused, and the refusal lifts when the first delivers).

**With one substitution, stated rather than glossed:** the two workers are
processes, not language models. They are real OS processes running the real
board CLI against a real filesystem, so everything the kernel owns is exercised
for real — what is simulated is the judgment inside a worker, which is the one
thing fleetkit does not supply.

So **S18 is not finished.** The remaining half is two live agent sessions in
that fresh repo. It costs quota, and it is recorded as outstanding rather than
redefined into what was convenient to test — this repository has a taxonomy
entry for the other choice.

## Before you deploy

Read [`KNOWN_TRAPS.md`](KNOWN_TRAPS.md). Six entries, each one a real outage,
none of which announced itself. The shortest summary of all six: **judge a
worker by its artefacts, not by its exit code.**
