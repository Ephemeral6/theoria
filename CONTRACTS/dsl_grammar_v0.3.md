# dsl_grammar_v0.3.md

**Version:** 0.3 · **Status:** 定稿（`theory-compiler` 单方所有，不需要会签）·
**Effective:** 2026-07-28

**Owner:** the `theory-compiler` track. **Supersedes:** `dsl_grammar_v0.2.md`,
which stays frozen and unedited, as v0.1 did before it. **v0.2's validator is
kept and still runs** — see §"Additions only", which is a tested property here
rather than a promise.

**Freeze policy.** Unchanged from v0.2: a change needs a ledger entry or a
defect that forced it, named in the revision record. "It would read better" is
not a reason to touch a contract two tracks compile against.

This revision exists because v0.2 used a word in a definition and never defined
it. `a0-spike`'s expressivity ledger entries **X-1** and **X-5** are the forcing
entries; the numbers 376 and 52 are theirs, and `theory-compiler/tools/probe_mentions.py`
re-derives both from this repository before driving them to zero.

Executable form: `theory-compiler/src/theory_compiler/writes.py` and
`.../parser/`. Where this document and that code disagree, the code is the
defect.

---

## 1. What `mentions` means

v0.2 §semantics:

> | `frame persist` | an object no firing rule **mentions** is unchanged |

Three readings were available and they are not equivalent:

| | reading | on the A0 world |
|---|---|---|
| **R1** | the rule's text — any object named anywhere in it | the successor of a mentioned-but-unassigned object is **undetermined**. `blocked_wall`'s guard reads `Box.pos` and assigns nothing |
| **R2** | the event signature — the objects among the event's arguments | **376 mispredictions** over the 39,960 pairs in which neither object stands on a wall. `slid(Box, dir)` names one object and moves two, so `persist` freezes the Player across every push |
| **R3** | the compiled effect — the objects the effect assigns | **0** |

### The definition

> **`writes(r)`** — for a rule `r`, the set of object instances whose
> observations `r`'s event assigns in the successor state. An object `o` is
> **mentioned by** `r` iff `o ∈ writes(r)`.
>
> **`frame persist`** — for every object `o` outside `⋃ writes(r)` taken over
> the rules that fire on this transition, `s'(o) = s(o)`. **`frame reset`** —
> such an object returns to its declared initial value.
>
> **`conflict`** ranges over pairs of rules whose `writes` sets intersect, and
> only those. This is v0.2 §"Discharging `conflict`" unchanged; what is new is
> that it and `frame` are now stated over one set, by name.
>
> `writes(r)` is fixed by the **event declaration** and by nothing else:
>
> 1. an explicit `writes { … }` clause on the alternative in `events:`; failing
>    that,
> 2. the default table in §3.
>
> An event in neither is a **compile error**.

### Why R3, argued rather than fitted

The 376 shows R2 is false of this world. A definition has to hold for worlds
nobody has measured, so:

1. **R1 is not a definition.** It leaves the successor of a
   mentioned-but-unassigned object unconstrained. A frame axiom exists to make
   the successor total; a reading under which `step` has no defined value on
   representable states has failed at its one job. Not an A0 quirk — any manual
   whose guards read an object they do not write inherits the hole, which is
   most manuals.

2. **R2 and R3 differ exactly where the event language is too weak, and R2
   answers by silently reversing the code.** A push moves two objects; the
   frozen `when <guard> then <event>` shape allows one event; the second
   object's motion therefore hides inside a compound event. Under R2 the frame
   axiom then **undoes** an assignment the compiled effect just made. A rule of
   interpretation that overrides the artefact it interprets is worse than one
   that is merely wrong.

3. **`frame` and `conflict` must range over one set or neither means anything.**
   v0.2 already made the `conflict` obligation range over claimed objects — R3
   under another name, already in the contract for the neighbouring statement.
   Reading `mentions` as R2 while `claims` stays R3 gives one section two
   incompatible notions of what a rule does to an object.

### The objection X-1 actually raised, and where it goes

X-1's complaint is not that R3 is the wrong extension. It is that R3 as shipped
made the manual's meaning depend on a dictionary inside one backend —

> `frame persist` is true only relative to an effect dictionary that lives in
> `gen_exec._compile_effect`, not in the manual and not in the contract.

The answer is to move the dictionary, in three parts, all of which are needed:

* **publish it** — §3, so a reader of `CONTRACTS/` alone can check it;
* **let the manual override it** — §2, so a world with an event the table has
  never heard of says so in its own manual;
* **fail closed** — §4. Without this the first two only relocate the guess.

After those, `writes(r)` is what the manual declares, and the backend is
**checked against** it (§5) rather than being its source. That reversal of
authority is the fix; the definition alone would be a comment.

---

## 2. `writes { … }` — new, optional

```
events:
  event <name>(<params>) [writes { <param>, ... }] | ... | ...
```

Every member of the set must be a **parameter of that event**. `writes {o,
Player}` is rejected, with a message naming the repair.

That restriction is how one addition answers both halves of X-1. X-1 asks for a
definition of `mentions` **and** for "an event signature that names every object
it writes". If an event writes an object, the object must be an argument:

```
event slid(o, p, dir) writes {o, p}     # the A0 push, with its pusher visible
event stayed(o)       writes {}         # nothing happens, and it says so
```

Allowing a free type name instead would be more permissive and is refused for a
reason beyond legibility: the written set would then depend on which instances
the level supplies, and `conflict` is a claim about the **domain** (D-TC-012).
Parameters keep it one.

**An absent clause is not an empty one.** `writes {}` is a claim that the event
assigns nothing; no clause at all defers to §3. Collapsing the two would make
"this event writes nothing" and "nobody has said" the same sentence, which is
the distinction this whole revision is about.

---

## 3. The default write-set table

Keyed by `(name, arity)`; entries are 0-based argument indices.

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

Transcribed from `conflict.CLAIMED_ARGS`, which is where this repository's
answer already lived unpublished.

**The table is closed.** It exists so that every manual the v0.2 chain compiled
is compiled unchanged by the v0.3 chain, and for no other reason. A new event
does not join it; a new event declares.

**`stayed/1` is the one row that is not a transcription.** `CLAIMED_ARGS` had it
claiming its argument; its compiled effect assigns nothing. Under the adopted
reading an event that assigns nothing writes nothing. Two consequences, both
stated rather than discovered later:

* it **narrows** the `conflict` obligation. Sound — a rule that writes no object
  cannot be the second writer of one — but real: on the A0 manual it drops the
  overlapping pairs from 15 to 1.
* "at most one rule per **object**" (which is what `conflict exclusive` says)
  and "at most one rule **fires**" are now visibly different properties. v0.3
  requires the first. The second is stronger, is what `a0-spike`'s `gen_exec`
  enforces at runtime, and is **not** a contract requirement; a manual that
  wants it must keep its blocked-rule guards disjoint by hand, and a manual that
  does not still has a well-defined successor because empty effects commute.

**And a hazard, admitted rather than hidden.** The table is keyed by signature
**across all worlds**, while what a rule writes is a fact about one world —
exactly the objection v0.2 §Migrating makes in bold about copying `semantics:`
values between manuals. v0.3 keeps the table because it buys backward
compatibility for every manual in the repository, and pays for it by making the
inheritance **loud**: a compiler must emit a warning naming every event whose
write set came from the table rather than from the manual. A default that is
announced is a different thing from a default that is silent, and the silent
kind is what E-03 was filed about.

---

## 4. Fail closed

An event that is in neither the table nor a `writes` clause is a compile error,
and the message must name the repair. Guessing "one object, the first argument"
is not available: measured on the fully repaired A0 manual, that guess is still
wrong on **376** transitions.

That number is worth reading twice. It is the *same* 376, on a manual whose
signature has already been fixed. Naming the pusher in the signature rescues the
R2 reading and does nothing for the R2′ one; only the definition rescues both.
Both halves of X-1 are load-bearing, and this is the measurement that says so.

---

## 5. The backend obligation

> For every rule a backend compiles, the objects its emitted effect assigns must
> equal `writes(r)` — no object outside it, and every object inside it. A
> backend that cannot satisfy this for an event must **refuse that event**,
> naming it, per v0.2 revision item 10.

The *extra* direction is the dangerous one: an object the backend writes and the
declaration omits is an object the frame axiom promises is unchanged while the
code changes it — X-1's 376 with the sign flipped.

**`gen_python` satisfies this and is held to it on every compile.**
`check_backend_agreement` runs per rule inside `generate_python`, so the drift
pin is the compilation itself rather than a test somebody has to remember to
write.

**`gen_pddl` does not satisfy it, and this contract says so rather than
implying it.** Measured on `cold-start-a0/theory/theory.dsl`, 2026-07-28:

* `teleport-down`, `press-left` and `door-opens-left` compile to `:effect (and
  (and))` — an action with no effect at all. The PDDL form of A0 has a
  button-press that presses nothing.
* `push-left` and `push-right` emit `?dest` in their effect while never
  declaring it as a parameter: `_extract_pred_pddl` knows the direction words
  `above|below|left|right` and the manual writes `leftof`/`rightof`. Those two
  actions are **malformed**, not merely weak.

Both are pre-existing and neither is repaired by this revision — repairing the
STRIPS backend changes the fourth form of four manuals and is its own piece of
work. They are pinned by name in `theory-compiler/tests/test_writes.py`, so the
shortfall is a checked number rather than a discovery someone makes twice. v0.2
revision item 11 is the standing lesson: a declaration nobody verifies reads
exactly like a verified one.

**Correction, 2026-07-31.** The shortfall above is repaired. `gen_pddl` now
dispatches events on (name, arity) — `moved/2`, `jumped/2`, `teleported/2`,
`recolored/2`, `vanished/1`, `appeared/1`, `stayed/1` — refuses everything
else by raising `UnsupportedClause`, translates the spatial spellings through
`gen_python`'s `SPATIAL` table, and folds same-guard rules into one action
(`cascade single_frame`). The generator's last step is `strips.parse_domain`
on its own output, so an undeclared predicate, an unbound variable or an
empty effect can no longer be shipped, only refused. The pin in
`tests/test_writes.py` (`TestBackendObligationShortfall`) went red on the
repair and was deleted, per its own instruction; the positive obligation now
lives in `test_gen_pddl_meets_the_backend_obligation_on_a0` and
`tests/test_e2e_rehearsal.py::TestForeignManual::
test_pddl_compiled_against_the_level_solves_like_the_world`, which holds the
A0 planning form to the known 12-step plan. The peg world's planning form is
a *declared refusal* (line geometry, field-arithmetic guards), which is the
honest count for that world: three forms and a named gap.

---

## 6. `free` on an object's own cell — ledger X-5

`free(c)` is "on the board, not a wall, no object occupies `c`", and the
predictor implements it by asking whether `c` renders as the background colour.
Every live object is painted on that frame. So `free(Box.pos)` asks whether the
Box's own cell is empty of the Box, and the answer is unconditionally `False`.

The A0 world tests `is_wall(target)` **before** it notices the box
(`a0-spike/world/sokoban2.py:142-145`), so "the Box is not standing on a wall" is
a guard the manual needs and could not write. 52 mispredictions, all firing
`push2`.

> **`free`, v0.3.** `free(c)` holds when `c` is on the board, is not a wall, and
> no object occupies it — **excluding from that test every object whose declared
> position is syntactically `c`**. The exclusion is per-occurrence and
> syntactic: `free(Box.pos)` excludes the Box; `free(ahead(Box, d))` excludes
> nothing.

Syntactic and per-occurrence on purpose. A semantic exclusion ("ignore whatever
happens to be there") would make `free` true of every occupied cell and destroy
the predicate.

### What this costs, stated plainly

`free` is no longer referentially transparent: `Box.pos` and `ahead(Player, d)`
can denote one cell and `free` can answer differently about the two spellings.
That is not a wart on the side, it is how the repair works — `free(Box.pos)`
means "the Box's own cell is a legal empty one" and `free(ahead(Player, d))`
means "the cell ahead of the player is empty, Box included". Three consequences,
all handled rather than tolerated:

* **the disjointness checker.** `free(t)` versus `colored(t, c)` is a proof of
  disjointness only when `free` is transparent in `t`. Self-excluding
  occurrences are therefore held in a separate key namespace and never line up
  with a colour or `= wall` clause over the same term. Without that,
  `free(Cart.pos)` and `colored(Cart.pos, 2)` — which both hold whenever the
  Cart is alone on its cell — would be reported *proved disjoint*, and a false
  proof in a soundness-critical checker is worse than no proof.
* **no STRIPS image.** `gen_pddl` holds `free` as a predicate *of a cell*,
  withheld from every cell an object occupies. A per-occurrence exclusion cannot
  be a property of the cell, so the clause would be permanently false in PDDL
  and satisfiable in Python — two of four co-derived forms encoding different
  worlds. The backend **refuses** it.
* **the human form.** `gen_markdown` may not render it as "`Box.pos` is free
  (unoccupied)" about a cell the Box is standing on. The prose form is one of
  the four forms; it is allowed to be prose and not allowed to be wrong.

### And what it does not do

It does not by itself fix the 52. It makes the clause *sayable*; the manual then
has to say it, and the rule set has to stay **total** once it does — a repair
that turns 52 wrong answers into 52 missing ones is not a repair. On the A0
manual that means `push2` gains `free(Box.pos)`, a new `blocked_box_on_wall`
catches what `push2` now refuses, and the two other blocked rules take the same
clause to keep exactly one rule firing. Verified exhaustively over all 47,040
representable pairs: 0 mismatches, 0 states with no rule, never two rules.

---

## 7. Additions only — what is claimed, and what is not

**Claimed, and tested:** every manual the **v0.2 chain compiled**, the v0.3
chain compiles, to the same world. `theory-compiler/tests/test_writes.py`
carries the pin for the fixture manuals; `runs/20260728T102343Z-c7/compat/`
carries a four-form byte diff for peg, `cold-start-a0`, `cold-start-a2` and
`a0-spike`.

**Not claimed:** that every syntactically v0.2-legal manual compiles. A manual
whose rules fire an event outside the table and outside a `writes` clause is
refused at generation.

**Where that refusal is loud, and where it is only a warning.** `build_ir` runs
the `conflict` pass non-strict, so an event with no resolvable write set becomes
a warning there and the IR is still built. The hard refusal is at the point of
use: `gen_python` asks for the write set of every rule it compiles and raises.
This is deliberate and it is the pre-existing arrangement — a manual with an
unrecognised event is going to be refused by a backend with a message about
*that*, and preempting it in the IR replaces a good diagnostic with a worse one.
It does mean a manual compiled only to Markdown never meets the check, because
that form does not need the write set. Stated so nobody reads §4 as stronger
than it is.

**`a0-spike/theory/theory.dsl` is the worked example, and not for the reason it
first appears to be.** Measured, baseline against v0.3: the outcome is
**bit-for-bit identical**, and neither version reaches `slid/2` at all. Both
fail in rule `walk`, on `moved/2` — a default-table event — with

```
UnsupportedClause: expected a direction from ['down','left','right','up'],
                   got NameRef(name='dir')
```

because `dir` is a free name bound by no `forall` and declared in no `domain`.
That is an **E-02** gap, it predates v0.2, and v0.3 neither causes nor cures it.
`gen_pddl` and `gen_markdown` emit byte-identical output on both sides.

So the honest statement about this manual is stronger than "v0.3 does not
regress it": v0.3 changes nothing about it. Migrating it takes three things, of
which only the first two are this revision's:

```
- event moved(o, dir) | slid(o, dir) | stayed(o)
+ event moved(o, dir) | slid(o, p, dir) writes {o, p} | stayed(o) writes {}
```

the rules firing `slid` gain the pusher as an argument, and — the one that
actually makes it compile — every rule binds `forall ?d in direction` over a
declared `domain`. A migrated copy lives at
`theory-compiler/tests/fixtures/sokoban2_theory.dsl`; under it `conflict
exclusive` is discharged by guard analysis alone, 28 overlapping pairs, 0
undischarged.

### The one hazard, stated plainly (as v0.2 did)

**A v0.3 manual parses under a v0.2 parser — silently, and to a different
world.** v0.2's event regex is a prefix match, so `writes {o, p}` is **discarded
without comment** and the event reverts to whatever the backend's private table
said. Measured. Consequences, in both directions:

* **v0.2 manual under a v0.3 parser** → compiles, with a warning naming the
  events whose write sets came from the table.
* **v0.3 manual under a v0.2 parser** → the `writes` clauses vanish and nothing
  warns. If you must, delete them first and accept that you no longer know what
  the manual claims its rules write.

`playbook.dsl` needs no migration, again.

---

## 8. Revision record — which entry forced which change

| # | change | forced by | what it cost to not have |
|---|---|---|---|
| 1 | `mentions` defined as `writes(r)` | **X-1** | v0.2's flagship semantic statement used an undefined word, and the three available readings disagreed by 376 transitions. `frame persist` was true only relative to a dictionary inside one backend |
| 2 | `writes { … }` on an event alternative, members restricted to parameters | **X-1**, second request | `slid(Box, dir)` moved the Player and named him nowhere. A reader of `theory.dsl` alone could not see that a push moves the player, and `conflict`'s per-object obligation ranged over too few pairs as a result |
| 3 | the default table, published and closed | **X-1** | the table existed, in `conflict.py`, unpublished. Publishing it is what lets a reader check the answer without reading a backend |
| 4 | an unknown event is an error | **X-1** | guessing "the first argument" is wrong on 376 transitions of the *repaired* manual. Without this clause, items 1–3 relocate the guess rather than removing it |
| 5 | the backend obligation, checked per rule at compile time | **X-1** | the repository already had this invariant and enforced it by a test that scraped one backend's source for `if key == ("...` lines. A source scrape is not an enforcement |
| 6 | `free` excludes an object from its own cell's occupancy test | **X-5** | "the Box is not standing on a wall" was inexpressible, and the manual was wrong about 52 states. `free(Box.pos)` did not merely fail — under `theory-compiler` it did not compile at all, and under `a0-spike`'s generator it compiled to an unconditional `False` |
| 7 | self-excluding `free` terms are refused by `gen_pddl` and re-worded by `gen_markdown`; the disjointness checker keys them separately | item 6's own consequences, and a false-proof found while writing it | a per-occurrence exclusion silently dropped from a STRIPS precondition is an action that applies where the manual says it does not; and `free(X.pos)` vs `colored(X.pos, c)` would have been reported *proved disjoint* while both hold |
| 8 | `stayed/1` writes `{}` | **X-1**, and ledger **X-3** | `stayed` claimed its argument while assigning nothing, so the no-op rule X-3 wants adjudicated had no syntactic mark. It now has one |
| 9 | `free(t)` contradicts `<inst>.pos = t` for an always-present instance | `a0-spike`'s own `semantics:` comment, which claimed exactly this and had nothing checking it | the A0 manual's stated route-1 discharge — *"free(c) 蕴含 c≠Box.pos，这一条就切开了 walk 与 push2"* — was prose. With it the migrated manual discharges `conflict exclusive` by guard analysis alone; without it that one pair fell through to an exhaustive sweep. It is also the pair that only exists **because** `slid` is read wide: under the narrow reading `walk` and `push2` share no claimed object and are never examined |

---

## 9. Open, and named

Recorded here rather than left for the next reader to rediscover. An adversarial
review of this revision produced the first two; they are real and neither is
closed.

* **`writes` is a waypoint, not the destination.** The strongest objection to §1
  is that it leaves **two artefacts that can disagree** — the declared write set
  and the compiled effect — and answers with an assertion (§5). That is
  structurally the arrangement X-1 was filed about, one level up. The successor
  design is an event **body**: `event slid(o, p, dir): o.pos := beyond(o, dir);
  p.pos := ahead(p, dir)`, from which the write set is *derived* and cannot
  drift, and under which `stayed`'s empty set needs no special row. It is not
  adopted here because it rejects every `events:` line in this repository —
  ten manuals, versus one for §4 — and because publishing bodies for the nine
  legacy events would reinstate the §3 hazard with more surface. **After v0.3,
  `frame persist` is well defined and `step` still is not**: two backends can
  both satisfy `writes {o, p}` and produce different successors. X-1's first
  sentence is not fully closed.
* **Parameters-only fails on a state-dependent write set.** A chain push — a
  pushed box shoving the box behind it, one flag away in `sokoban2.Rules` —
  writes `{Player, Box₁ … Box_k}` with `k` state-dependent. No fixed signature
  names it, and grounding with `forall ?b in Box` gives *k* rules that each
  write `Player`, violating `conflict exclusive` for a transition that is
  perfectly well defined. No manual in this repository refutes the restriction;
  the next obvious variant of this repository's own world does.
* **`gen_pddl`'s shortfall**, §5. Pinned, not fixed.
* **Connectivity-class invariants** remain unsupported, as in v0.2. **E-06**
  remains open on its proof half, as in v0.2. Neither is touched here.

---

## Deliberately not changed

* `dsl_grammar_v0.1.md`, `dsl_grammar_v0.2.md` — frozen. v0.3 is a new file, and
  v0.2's validator is kept and still runs.
* `candidates_schema.md` — frozen, and not this track's.
* `playbook.dsl` — unchanged, including the hard anti-cheat rule.
