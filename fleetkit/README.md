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
| `config.py` | ~160 | new — the whole project-specific surface |
| `__main__.py` | ~105 | new in S42 — the `python -m fleetkit` front door above |
| `board.py` | ~435 | ported: atomic claim, territory exclusivity, sweep, lane *filtering*. Lane **ownership** was removed rather than ported — see below. |
| `bus.py` | ~195 | ported: acknowledgement, urgent interruption, cursors |

### What that row used to say, and why it was wrong

It said `ported: atomic claim, territory exclusivity, lanes, sweep`, and S40
measured two of those four as not working:

* **sweep** freed the claims of workers that were still running. Liveness was
  decided by matching scheduled-task names against `_PREFIX`, a module global
  that nothing in the package ever assigned — so the test was constantly false,
  nothing ever entered the live set, and every `W-*` claim read as an orphan.
  That is [`KNOWN_TRAPS.md`](KNOWN_TRAPS.md) entry 1 word for word, latent in
  the package that ships the warning, while `config.py` validated a
  `task_prefix` no code opened. `board.py` now reads it from `fleet.json` at
  the point of use, and **refuses to sweep** (exit 3) when it cannot — not
  knowing whether a worker is alive is not the same as knowing it is dead.
* **lanes** did not partition the board; it hid parts of it. `LANE_OWNER`
  claimed in a comment to be "Filled from `fleet.json` at import" and was
  filled by nothing, from a file that did not exist, into a shape
  `FleetConfig.lanes: List[str]` cannot hold. A `lane:` item was therefore in
  no section of `list`, and had no exit but editing the file by hand.

Lane ownership is **deleted, not repaired**. Repairing it meant growing the
config schema to buy a reservation feature no caller asked for. What remains is
what `lanes: List[str]` already describes — "lanes a standing agent can be
restricted to": `--lane X` narrows what a worker will take and can never widen
it, and every lane-tagged item is listed and claimable by anyone. A consequence
worth naming: the `spend: api` guard used to be skipped whenever a worker
passed `--lane`, so a worker's own word about itself was acting as
authorisation. It is no longer lane-conditional.

`list` now also prints a `withheld` section, so every item in `items/` appears
under exactly one heading with a reason. Unclaimable is fine; unclaimable and
unmentioned is how a board with eleven items on it reads as empty.

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

`verify.py` drives the same acceptance through the commands this README
documents, rather than around them. Until S42 it called `config.write_default()`
in-process, and stayed green for every run in which `python -m fleetkit init`
— line 13 above — died with `No module named fleetkit.__main__`. A gate that
reaches around the front door cannot see the front door break.

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
