# THEORIZE log — A0

The adjudication record. Engines propose; this is where the LLM decides what
enters the manual, and why. Each entry is a decision, its evidence, and what it
cost or bought.

---

## T-1 · Two objects, and a board

**Proposed by** `mdl_segmenter` (colour-splitting operator).

**Evidence** 5 connected components across every frame. Two of them account for
every event in the edit script; three never move.

**Adjudicated** `object Player { pos: Cell }`, `object Box { pos: Cell }`. The
three static components settle into `board` — "what never co-varies is the
board" (Theoria 1.8), and they need no name of their own.

**Cost** the edit script runs 373 bits against a 412-bit per-pixel baseline on
the longest episode. A real but unimpressive win: this world's typical
transition moves one cell, so a pixel dump is only two edits and there is little
to compress. The Cart fixture's 0.29 ratio is not the number to expect here.

---

## T-2 · The colour-splitting segmentation operator

**Why it is in the manual** The default colour-agnostic operator fuses the player
with any wall it stands against and with the box it is about to push, and the
trajectory becomes unreadable. Which operator a world needs is part of the
manual, not a hidden default (Theoria 1.8: the operator hypothesis space).

**Adjudicated** recorded as the segmentation method for this world.

---

## T-3 · `walk` — accepted immediately

**Proposed by** `cegis_miner` core, four rules, 56–101 witnesses each.

    act==D and ahead_free(D)  ->  player moves one cell

**Adjudicated** in. Well-evidenced, uniform across all four directions, and it
lifts to one schema over `?dir`.

---

## T-4 · `push2` — rejected on the first pass, accepted on the second

**First pass** (a 28-step casual walk) gave

    act==D and ahead_is_box(D)  ->  box moves two cells

with **one witness per direction**. Replay was exact. The rule is still wrong:
it predicts a push even when the box has nowhere to go.

**This is the DC22 shape** — perfect on history, broken on the unseen. Accepting
it because replay passed is exactly the failure the framework exists to catch, so
it was refused.

**Probe** The discriminating situation is "box ahead, but the cells it would
cross are not clear". Exploration was re-planned to witness each *situation*
rather than each *outcome*, reaching those states by prefix replay.

**Second pass** with 341 transitions:

    act==D and ahead_is_box(D) and box_beyond_free(D)  ->  box moves two cells

12–19 witnesses per direction. **Adjudicated in.** The probe cost 341 actions and
bought the difference between a rule that replays and a rule that holds.

---

## T-5 · `blocked` — the guard language bites

**Finding** No single conjunction covers the class. "Nothing moved" is genuinely
disjunctive: a wall ahead, *or* the box ahead with its path obstructed.
`cegis_miner.synthesize` raised `NoSeparatingGuard`, correctly.

**Adjudicated** as *several* rules with conjunctive guards whose disjunction is
the class — sequential covering. Every individual rule stays inside the frozen
grammar, which says guards are conjunctions. The alternative (adding disjunction
to the guard language) would have needed a contract change and an entry in the
expressiveness ledger; it was not taken.

**Known wart** `blocked_DOWN_1` carries literals about LEFT and RIGHT that are
accidental. Greedy covering found a local optimum. It is sound on all 341
transitions — replay is exact and every transition has exactly one successor —
but it is not the rule a person would write. Recorded rather than hand-edited:
the manual is supposed to say what the evidence forced.

---

## T-6 · The conservation law — the engine found a stronger one than I proposed

**I proposed** `(box.row + box.col) mod 2 = 0` — the box never changes
checkerboard colour.

**`zero_space` returned** a null space of dimension **2**, basis `[[1,0],[0,1]]`:
`box.row mod 2` and `box.col mod 2` are *each* conserved, separately. That is
strictly stronger, and it is true — a push moves the box by two cells along one
axis, so each coordinate's parity survives on its own.

**Adjudicated** the stronger pair goes into the manual; the sum is kept as a
derived corollary because it is the form the unsolvability argument uses.

**Why this entry matters** The engine corrected the adjudicator, which is the
division of labour working in the direction it was designed to work in: the
engine computes, the LLM decides, and the LLM was wrong.

---

## T-7 · The unsolvability theorem

**Adjudicated**

    theorem unsolvable_mismatch
      "箱子每次滑动两格，(row+col) 的奇偶不变；开局箱子在偶格，目标格是奇格，
       所以永远到不了"

Three lines, no search: the law holds at the start, no rule breaks it, and
winning requires breaking it.

**What it bought** On `mismatch` the planner exhausts the state space to report
"no plan". The theorem answers in one arithmetic step and, unlike the planner,
says *why*. That gap — a certificate against "I searched and found nothing" — is
the whole thesis, and A0 shows it on a world small enough to check by hand.

---

## T-8 · Compiling the manual caught an error the mined rules had not

**What happened** certify was rewired to replay history through the executable
form compiled from `theory.dsl`, rather than through the miner's in-memory rule
objects. The generated code immediately walked the player off the board.

**Cause, in the manual, not the engine** I had adjudicated

    rule blocked_wall  ... then moved(Player, dir)
    rule blocked_box   ... then moved(Player, dir)

The mined rules had the right effect all along — `(0,0), (0,0)`, nothing moves.
The error was in my transcription of them into the manual, and the event
vocabulary was complicit: `moved | slid` had no way to say "nothing happened", so
the nearest available event was a movement one.

**Adjudicated** `stayed(o)` added to the event vocabulary; both blocked rules now
end `then stayed(Player)`.

**Why this entry is the point of the exercise** Replaying through the mined rules
would never have found this: those rules were correct. Only the compiled manual
is accountable for what the manual actually says, which is exactly why the
framework insists the sole predictor be generated from it. One rewiring, one real
error caught, in a manual I had already reviewed and called done.

---

## T-9 · Held-out testing found a wrong rule that replay could not

**What happened** With certify green — 341 transitions replayed exactly through
the compiled manual — the theory was checked against the world on *every*
well-formed state of the board, not just the observed ones. **8 mismatches.**

**The missing literal** `push2` required only `free(beyond(Box, dir))` — the cell
the box lands on. The world also requires `free(ahead(Box, dir))` — the cell the
box *crosses*. Example: player (1,3), box (1,4), RIGHT. The landing cell (1,6) is
free, so the theory pushed; the crossed cell (1,5) is a wall, so the world did
nothing.

**Why no amount of exploring `match` could have found it** The box's crossed cell
always has odd parity, and every wall in `match` sits on an even cell. "Blocked
while crossing" is not merely unobserved there — it is **unreachable**. All 8
mismatching states are unreachable from `s0`; on the 315 reachable states the
theory was already exact.

**So the rule was right as a *problem* solution and wrong as a *domain*.** That
distinction is the frozen contract's own (`word_table + rules + laws` is domain,
the layout is problem), and it has teeth: a manual meant to travel between levels
cannot be pinned down by one level's evidence.

**Adjudicated** four more evidence levels, one per direction, each with a wall on
an odd-parity cell so that "blocked while crossing" becomes reachable in that
direction. Evidence pooled across all five. The mined guard gained
`box_ahead_free(dir)` in every direction, and `blocked_box` split into
`blocked_box_crossing` and `blocked_box_landing` — two conjunctions, because the
disjunction cannot be one.

**Result** 39,960 well-formed states across five levels, **0 mismatches**.

**What this cost and bought** 1,966 actions instead of 341. It bought the
difference between a theory that is right about the level it was learned on and
one that is right about the world. Replay said "exact" both times.
