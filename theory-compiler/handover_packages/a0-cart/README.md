# The cart world — handover package (manual and playbook)

This directory is a complete handover of one world's theory. It is everything you get: there is no repository behind it, no record of anyone playing this world, and no earlier conversation about it. If something is not in this directory, you do not know it.

You have been given **the manual and the playbook**.

## Read in this order

1. `manual/MANUAL.md` — the manual in English. Mechanically rendered from `manual/MANUAL.dsl`; no model wrote a word of it.
2. `manual/PRIMITIVES.md` — the handful of words the rules are built from. Short, and the rules are unreadable without it.
3. `levels/` — two boards. Everything in there is supplied by a board; nothing in there is a law.
4. `GLOSSARY.md` — every name in the package with where it comes from, and a table showing which names differ between the two boards.
5. `playbook/PLAYBOOK.md` — how to win, and how to avoid search. It answers to the manual, not to the world.

`manual/MANUAL.dsl` is the manual as its author wrote it, byte for byte. Where the English rendering and the source seem to disagree, the source is the deliverable.

## The four forms

One manual compiles to four co-derived forms. Two are of the manual alone and two must be grounded on a board, which is why this package carries two boards: what is identical between them is the world, and what differs is the board.

| form | where | derived from |
|---|---|---|
| English | `manual/MANUAL.md` | the manual alone |
| planning (domain) | `manual/DOMAIN.pddl` | the manual alone |
| executable | `levels/<board>/predictor.py` | the manual, on that board |
| proof | `levels/<board>/Level.lean` | the manual, on that board |
| planning (problem) | `levels/<board>/problem.pddl` | the manual, on that board |

## What is deliberately not here

- **No worked example.** No file in this package steps a concrete board through a concrete action. Working one out is the point.
- **No plan.** Not in the manual, and not in the playbook either — its grammar has no sentence form for a sequence of actions.
- **No history.** No trace, no ledger, no record of how the manual was arrived at. Comments in the source cite that record; you neither have it nor need it. See `SEAL.md`.

## Provenance

`MANIFEST.json` carries a sha256 of every file here, and records which repository files these were copied or compiled from. That is metadata about how the package was made; you have no access to that repository and nothing in it is needed to read this one.

## Boards in this package

- `levels/base/`
- `levels/no-button/`
