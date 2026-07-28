# C7 · design — what "mentions" means, and the two defects it drags along

Run `20260728T102343Z-c7` · prompt `C7-dsl-v03-mentions` · base `f1346fb`.

Written before the code, so that the hardest call — **which reading of
"mentions" is canonical, and why** — is on record as an argument rather than as
whatever the implementation happened to do.

---

## 0. The hole, stated exactly

`CONTRACTS/dsl_grammar_v0.2.md` §semantics:

> | `frame persist` | an object no firing rule **mentions** is unchanged |

`mentions` is never defined. `a0-spike/THEORIZE_LOG.md` §表达力台账 **X-1** nails
three readings down with 376 measured counterexamples:

| reading | what "`r` mentions `o`" means | verdict on the A0 world |
|---|---|---|
| **R1 · rule text** | `o`'s name occurs anywhere in `r` (guard or event) | successor **undetermined** — `blocked_wall`'s guard mentions `Box.pos`, so the Box is "mentioned" by a rule that assigns it nothing, and the frame axiom now says nothing about its value |
| **R2 · event signature** | `o` is an argument of `r`'s event | **376 mispredictions**, measured. `slid(Box, dir)` names only the Box, so the Player is unmentioned, so `persist` freezes it — and a push visibly moves the player |
| **R3 · compiled effect** | `r`'s compiled effect assigns `o` | **0 mispredictions** |

R3 is the only reading that agrees with the world. It is also, as written, the
worst possible thing to put in a contract — which is the actual content of X-1's
complaint, and the reason this entry is a grammar defect and not a bug report:

> `frame persist` is true only relative to an effect dictionary that lives in
> `gen_exec._compile_effect`, not in the manual and not in the contract.

So the canon cannot be "R3, as the backend happens to compile it". It has to be
R3's *extension* made **declarable, checkable, and public**.

---

## 1. The adjudication

> **v0.3 · `writes(r)`.** For a rule `r`, `writes(r)` is the set of object
> instances whose observations `r`'s event assigns in the successor state. An
> object `o` is **mentioned by** `r` iff `o ∈ writes(r)`.
>
> `frame persist` — for every object `o` outside `⋃ writes(r)` over the rules
> that fire on this transition, `s'(o) = s(o)`.
>
> `writes(r)` is fixed by the **event declaration**, in one of two ways, and by
> nothing else:
>
> * an explicit `writes { … }` clause on the alternative in `events:`, whose
>   members must be **parameters of that event**; or
> * failing that, this contract's **published default table** (§ below), keyed
>   by `(name, arity)`.
>
> An event that is in neither is a **compile error**. There is no third source
> and no default-to-first-argument.
>
> **Backend obligation.** A backend's compiled effect must assign exactly
> `writes(r)` — no object outside it, and every object inside it. A backend that
> cannot is defective and must raise, in the sense §"Every backend must refuse a
> value it does not implement" already gives that word.

### Why R3, argued rather than measured

The 376 settles that R2 is *false of this world*. It does not by itself settle
that R3 is *the definition*, because a definition has to hold for worlds nobody
has measured. Three arguments, none of which is "it fit":

1. **R1 is not a definition at all.** It leaves the successor of a
   mentioned-but-unassigned object unconstrained. A frame axiom exists to make
   the successor total; a reading under which `step` has no defined value on
   states the level can represent has failed at the one job. This is not a close
   call and it is not about A0: any manual whose guards read an object they do
   not write — which is most manuals — inherits the hole.

2. **R2 and R3 differ exactly when the event language is too weak, and R2
   answers by silently corrupting the world rather than by complaining.** A push
   moves two objects; the frozen `when <guard> then <event>` shape allows one
   event; so the second object's motion has to hide inside a compound event.
   Under R2 the frame axiom then *overrides* the effect — the compiler emits the
   player's move and the frame axiom undoes it. A rule of interpretation that
   quietly reverses the code it interprets is worse than one that is merely
   wrong: 376 is what it cost here and there is no upper bound on what it costs
   elsewhere.

3. **`frame` and `conflict` must range over one set or neither means anything.**
   v0.2 §"Discharging `conflict`" already makes the conflict obligation range
   over *claimed objects* — the objects a rule's event mutates. That is R3,
   under another name, already in the contract for the neighbouring statement.
   Reading `mentions` as R2 while `claims` stays R3 gives one section two
   incompatible notions of "what a rule does to an object". Choosing R3 for both
   is the only choice that leaves `semantics:` internally consistent, and it is
   why `conflict.CLAIMED_ARGS` and `gen_python._effect` were already pinned
   against each other by a test: the repository had discovered the constraint and
   had nowhere in the contract to write it down.

### Why the private-dictionary objection is a real objection, and how it dies

X-1 is right that R3-as-shipped makes the manual's meaning depend on a table
inside one backend. The fix is not to pick a weaker reading; it is to **move the
table**. Three moves, together:

* **publish it** — the default table goes in the contract, so `moved/2 writes
  {arg 0}` is a fact a reader of `CONTRACTS/` alone can check;
* **let the manual override it** — `writes { … }` on the event declaration, so a
  world with an event the table has never heard of says so in its own manual
  rather than waiting for a backend to grow a case;
* **fail closed** — an event in neither the table nor a `writes` clause is an
  error. This is the load-bearing third: without it, "publish the table" just
  moves the guess.

After those three, R3 is no longer "whatever `_compile_effect` does". It is
"whatever the manual declares", and `_compile_effect` is *checked against* the
declaration rather than being its source. The direction of authority is
reversed, and that reversal is the whole fix.

### Members of `writes { … }` must be parameters — and that *is* X-1's request (2)

X-1 asks for two things: a definition of `mentions`, and "an event signature that
names every object it writes (or multiple events per rule)". Restricting write-set
members to the event's own parameters is how one addition delivers both. If
`slid` writes the Player, the Player has to be an argument:

```
event slid(o, p, dir) writes {o, p}
```

The alternative — allowing `writes {o, Player}` with a free type name — would let
a manual keep the compound event *and* be legible about it, and is tempting for
exactly that reason. It is rejected: a free name in the write set makes the
written object depend on which instances the level supplies, so a rule's claimed
set would stop being a property of the domain. `conflict` is a claim about the
domain (v0.2, D-TC-012). Parameters keep it one.

### Default table (v0.3 §Event write sets)

Lifted verbatim from `conflict.CLAIMED_ARGS`, which is where this repository's
answer already lived. Argument indices are 0-based.

| event | writes |
|---|---|
| `moved(o, dir)` | `{o}` |
| `jumped(o, dest)` | `{o}` |
| `teleported(o, dest)` | `{o}` |
| `jumped(p, over, dir)` | `{p, over}` |
| `recolored(o, c)` | `{o}` |
| `vanished(o)` | `{o}` |
| `appeared(o)` | `{o}` |
| `removed(o)` | `{o}` |
| `stayed(o)` | `{}` |

`stayed/1` is the one entry that is **not** a transcription: `CLAIMED_ARGS` has
it claiming its argument and it assigns nothing (`gen_exec` compiles it to
`pass`). Under R3 an event that assigns nothing writes nothing, and the table
says so. The effect is to *narrow* the conflict obligation, which is sound —
a rule that writes no object cannot be the second writer of one — and it makes
ledger **X-3** sharper rather than duller: a rule with `writes {}` is now
syntactically identifiable as the no-op rule X-3 wants `certify` to adjudicate.

---

## 2. `free(...)` on an object's own cell — ledger X-5

Independent defect, same run because it is the other thing standing between the
A0 manual and a clean sweep.

`_free(state, cell)` is `_cell_colour(state, cell) == BACKGROUND`, and
`_cell_colour` reads `render(state)` — the frame with every live object painted
on it. So `free(Box.pos)` asks "is the Box's cell background?", the Box is
painted on it, and the answer is **unconditionally false**. The manual cannot
say "the Box is not standing on a wall", the A0 world checks exactly that before
considering a push (`world/sokoban2.py:142-145`), and the manual is wrong about
**52 states** as a result.

The defect is not in `free`'s meaning. It is that the occupancy test counts the
object whose own cell is being asked about — a question that has an obvious
intended answer and gets a degenerate one.

> **v0.3 · `free`.** `free(c)` holds when `c` is on the board, is not a wall, and
> no object occupies it — **excluding from that test every object whose declared
> position is syntactically `c`**. The exclusion is per-occurrence and
> syntactic: `free(Box.pos)` excludes the Box, `free(ahead(Box, d))` excludes
> nothing.

Syntactic and per-occurrence on purpose. A semantic exclusion ("exclude any
object that happens to be there") would make `free` unconditionally true of every
occupied cell and destroy the predicate. The rule is narrow: it only fires when
the manual asks about a cell it has named *via* an object, which is the only case
where the old answer was information-free.

This is the first of the two repairs X-5 asks for ("a guard predicate over
level-static data … or a `unique`-style declaration"). It is the cheaper one and
it is enough: with it, `free(Box.pos)` becomes "the Box's own cell is a legal,
unoccupied-by-anyone-else cell", which is false exactly when the Box stands on a
wall or off the board.

**It does not fix the 52 by itself.** It gives the manual a *sayable* clause; the
manual then has to say it, and the rule set has to stay total once it does. Both
halves are in §3.

---

## 3. What gets built, and where

Territory: `theory-compiler` is mine; `a0-spike` is `engine-rig`'s and is **read
only** from here. So the A0 manual is not edited in place. Its v0.3 migration is
carried as a fixture in this track, the original is verified to still compile,
and the migration is offered to the other track through `PARTNER_SYNC`.

1. `CONTRACTS/dsl_grammar_v0.3.md` — new file. v0.2 stays frozen and unedited.
   Additions only: `writes { … }`, the default table, the `mentions` definition,
   the `free` clarification, and the backend obligation. **Every v0.2 manual is a
   v0.3 manual** — that is the acceptance criterion for "additions only", and it
   is tested rather than asserted.
2. Parser: `writes` on an event alternative; `EventAlt.writes`.
3. `writes.py` — one module that resolves `rule → writes(r)` from the
   declaration, and is the single source both `conflict.claimed_objects` and
   `gen_python._effect` are checked against.
4. `gen_python` — `slid/3`, `stayed/1`, `ahead`/`beyond` cells, the `free`
   self-exclusion, and the assertion that the compiled effect equals the
   declared write set.
5. Fixtures + probe reproducing **376 → 0** and **52 → 0** against
   `a0-spike/world/sokoban2.py` as ground truth, over all 47,040 representable
   pairs (5 levels × 49 × 48 × 4).
6. Compatibility: peg / cold-start-a0 / a0-spike / cold-start-a2 through the new
   chain, four ways, in parallel.

### The A0 migration, concretely

```
events:
  event moved(o, dir) | slid(o, p, dir) writes {o, p} | stayed(o) writes {}
```

`slid` gains the pusher as an argument — request (2) — and `writes` makes it say
so. `stayed` declares `{}` rather than inheriting it, because a manual that
means "nothing happens" should be readable as saying it.

For the 52, `push2` gains `free(Box.pos)`, and a fifth blocked rule catches the
states it now refuses:

```
rule blocked_box_on_wall
  when act=move(Player, ?d) and Box.pos = ahead(Player, ?d)
       and not free(Box.pos) then stayed(Player)
```

`blocked_box_crossing` and `blocked_box_landing` gain `free(Box.pos)` too, or
they overlap the new rule and `conflict exclusive` stops holding. **Totality is
the thing to watch**: the 52 are currently mispredicted, not undefined, and a
repair that turns a wrong answer into no answer is not a repair. The probe
counts "no rule fired" as a mismatch for exactly this reason.

---

## 4. What would refute this

Recorded before the adversarial pass, so that the pass has something to hit:

* a fourth reading of `mentions` that is total (unlike R1), agrees with the
  world (unlike R2), and does **not** depend on a backend table (unlike R3 as
  shipped) — that would beat this proposal on its own stated grounds;
* a world in which an event must write an object that cannot be a parameter of
  it — that would refute the parameters-only restriction;
* any v0.2 manual that the v0.3 chain rejects — that would refute
  "additions only", which is the one property both tracks compile against.
