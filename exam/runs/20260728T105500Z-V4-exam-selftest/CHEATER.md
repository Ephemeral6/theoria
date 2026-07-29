# The cheater pass — two sheets, and every claim scored against the key

`STATUS.md` open weakness 11: *"Two cheater agents, four sheets, one pass. No
adversarial reader has seen the fixed sheets."* The two sheets that changed when
P-15's leaks were fixed are `p15-verdict-a2` and `p15-heldout-a0`. Both have now
been attacked.

**Protocol.** Each subagent was handed exactly one file —
`artifacts/cheater/<paper>.brief.txt`, which is `leakage.cheater_brief()`
verbatim: the instruction to cheat rather than solve, plus the serialised sheet.
Each was told, explicitly and in the negative, not to read any other file, any
`.py`, any path containing `truth`, or any git history. Both reported reading
exactly the one file.

**The rule that made this run worth doing.** Nothing a cheater says is believed
until it is scored against the key by the referee. That rule already existed —
P-15 wrote it after two of its cheater's claims failed checking — and this pass
produced two more instances, failing in opposite directions.

---

## Verdict sheet — 17 of 17 claims, and it still capped at half

| | |
|---|---|
| claims correct | **17 / 17** |
| its own forecast | 13.8 / 17 — it under-predicted itself |
| majority-class baseline | 9 / 17 = 0.529 |
| per class | small_unsolvable 5/5, large_unsolvable 4/4, solvable_hard 8/8 |
| **score on the real rubric** | **17.0 / 34 = 0.5000** |
| certificates submitted | 0 |
| witnesses submitted | 0 |

The cap at exactly one half is the rubric working as designed: each item pays 1
point for the claim and 1 for the reason, and the per-item detail reads *"right
verdict, no witness plan. On a solvable level the constructive answer is the
plan; without it the claim is indistinguishable from a guess."* That sentence
stops being a design note and becomes a measurement.

Its answers are archived as a real submission at
`artifacts/answers/p15-verdict-a2.cheater-v4.answers.json`, with its own account
of which exploit decided each item, and it is a row on the confusion matrix.

### What it actually exploited

Most of its leverage was **cheap arithmetic on the ASCII board** — budget versus
Manhattan distance from `S` to `G`, an all-`#` row separating the two, a hazard
sitting on the only non-wall cell of its row or column. That is not a leak. The
board must be on the sheet; you cannot ask whether a level is solvable without
showing the level, and answering cheaply is solving cheaply.

Three of its seven exploits are genuine sheet structure, and these are the ones
worth recording:

* **X5** — every `relabelled` field is `{LEFT: RIGHT, RIGHT: LEFT}`, a bijection
  on a command set containing both, so it is provably a no-op. A decoy that can
  never bite, on all 4 items carrying it.
* **X6** — 17 items over 5 distinct grid skeletons, several byte-identical, so an
  item whose grid matches another's under a weaker wrapper inherits its answer
  with no reasoning at all.
* **X7** — exactly one item has every wrapper at its default, and an exam that
  states wrappers per item includes an unrestricted positive control.

It also reported, unprompted and against its own interest, that the naive
metadata cheat — *"any non-default wrapper means unsolvable"* — scores 9 of 16,
barely above chance, because the builder paired every biting wrapper with a
non-biting twin. **P-15's `points` leak is confirmed dead**: `points` is 2.0 on
all 17 items and `question` is byte-identical on all 17.

---

## Held-out sheet — three claims, one confirmed, one refuted, one real

| claim | as stated | verified against the key |
|---|---|---|
| **E1** `instructions` names the genre while `world.description` says the dynamics are withheld | decides 80/80 | **confirmed verbatim** |
| **E2** the replay/heldout split is recoverable from box coordinate parity | 79/80 | **confirmed exactly: 79/80 = 0.9875** |
| **E3** six items' answers are printed as other items' inputs | 6 items, confidence 0.97 | **refuted: 0 of 6** |

### E1 — confirmed, and its measured yield is negative

The sheet contradicted itself. `instructions` opened with *"A0 is a sokoban
variant"*; `world.description`, two fields later, said the dynamics *"are what
this paper asks about and are deliberately not stated here"*.

But **A0's push slides the box two cells** — a0-spike's `push2`, the T-9 finding
this paper is built around. Vanilla sokoban slides it one. So:

| what it answered | measured |
|---|---|
| six items via the genre prior, confidence 0.97 | **0 / 6** |
| nine items needing no dynamics (`blocked_edge`, `blocked_crossing`) | **9 / 9** |
| its own forecast for the whole sheet | 60–72 of 80 |
| the null baseline it had itself identified | 26 / 80 = 0.325 |

It scored the floor and nothing above it. A confirmed information leak had
**negative** yield, because what leaked was a wrong prior — and the cheater was
most confident exactly where it was entirely wrong.

By the item's acceptance condition — 榨得出即验收失败 — the sheet passes.

**Removed anyway, and not because of cheating.** This paper exists to ask
whether a theory learned `push2` from evidence instead of assuming push-one from
a prior. A sheet that names a genre whose rules differ from the world's is not a
neutral question with a harmless hint in it; it is an undeclared second
experiment. Regression test:
`test_no_sheet_names_the_genre_of_the_world_it_asks_about`, over all four sheets.

### E2 — confirmed exactly, and left for its own run

```
replay   40 items, box on  7 distinct cells, all both-odd coordinates
heldout  40 items, box on 29 distinct cells, one of them on the sublattice
both-odd-box predicts the split: 79/80 = 0.9875   (miss: a0h-063)
```

The two halves are not distributionally matched at the level of *state*: a
memorising theory can tell which half it is standing in without reading the tag.

It leaks nothing about the **answers** — the answer-class stratification is exact
to the item, `blocked_edge` 4, `blocked_crossing` 5, `blocked_wall` 4,
`blocked_landing` 5, `push` 16, `move` 6 in *both* halves — so the sheet's
promise that the tag carries no information about the answer holds. What it means
is that "held-out" here partly means "box on an even coordinate" rather than
"same situation, unseen transition", and `gap_replay_minus_heldout` inherits
that. New STATUS weakness 12; fixing it means resampling the split, which is a
substantive change to the paper and needs its own pre-registration.

### E3 — refuted as stated, and one real instance it missed

All six pairs it named are `push` events, and it predicted one-cell translations
from the genre prior. Every one is wrong. A full 80×80 successor scan over the
key finds exactly **one** true instance:

```
a0h-074 (replay) -- its frame_after is a0h-042's frame_before (replay)
```

Inside the replay half consecutive trajectory states are expected to neighbour
each other, so this is a generation-time check that was never written rather
than a surprise. New STATUS weakness 13, same resampling run as 12.

---

## What the two passes say together

The verdict cheater **under**-estimated itself; the held-out cheater was most
confident precisely where it was wrong. Neither error is one a reader could have
caught by reading the report — both took scoring against the key. The rule holds
and now has numbers behind it: **an unverified cheater is just another confident
agent**, and a cheater that found a real leak is not thereby right about what
the leak is worth.
