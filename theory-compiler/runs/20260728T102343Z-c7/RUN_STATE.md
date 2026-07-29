# C7 — `mentions`, defined; and the two defects that hung off it

Run `20260728T102343Z-c7` · prompt `C7-dsl-v03-mentions` · branch
`agent/c7-dsl-v03-mentions` · base `f1346fb`.

Design written before the code: [DESIGN.md](DESIGN.md). Re-derive everything:
`bash theory-compiler/runs/20260728T102343Z-c7/verify.sh`.

---

## What was wrong

`CONTRACTS/dsl_grammar_v0.2.md` defined `frame persist` as *"an object no firing
rule **mentions** is unchanged"* and never defined `mentions`. `a0-spike` pinned
the hole with 376 counterexamples (ledger **X-1**) and found a second defect
alongside it (**X-5**, 52 states). Three readings, none equivalent:

| | reading | on the A0 world |
|---|---|---|
| R1 | the rule's text | successor **undetermined** for a mentioned-but-unassigned object |
| R2 | the event signature | **376** wrong |
| R3 | the compiled effect | **0** wrong — and defined by a dictionary inside one backend |

## What was decided

R3's extension, with the dictionary taken away from the backend.
`CONTRACTS/dsl_grammar_v0.3.md` is the new file; v0.2 stays frozen and its
validator is kept.

* **`writes(r)`** — the objects a rule's event assigns. `o` is mentioned by `r`
  iff `o ∈ writes(r)`. `frame` and `conflict` now range over one set, by name.
* fixed by the **event declaration** and nothing else: a `writes { … }` clause,
  or v0.3's published closed default table. **An event in neither is an error.**
* members of `writes { … }` must be **parameters of the event** — which is how
  one addition answers X-1's second request too: if `slid` writes the Player,
  the Player has to be an argument.
* **the backend is checked against the declaration**, per rule, on every
  compile. Before, the arrow pointed the other way.
* **`free(c)`** excludes from the occupancy test every object whose declared
  position is syntactically `c`. Per-occurrence and syntactic.

The three moves — publish the table, let the manual override it, fail closed —
are all needed. Fail closed is the load-bearing one: without it the other two
relocate the guess. Measured, §"the numbers" below.

## The numbers

`tools/probe_mentions.py`, 47,040 representable (state, action) pairs across 5
levels, graded against `a0-spike/world/sokoban2.py`. **Stratified**, because the
two ledger numbers do not share a denominator — 376 was counted over the 39,960
pairs in which neither object stands on a wall, and the 52 are by construction
inside the other 7,080. Mixing them would have made the acceptance criterion
unsatisfiable, and this run's first draft did mix them.

| manual | reading | stratum | mismatches |
|---|---|---|---|
| X-5 open | first argument | off-wall | **376** ← X-1, reproduced |
| X-5 open | declared | on-wall | **52** ← X-5, reproduced |
| X-5 open | declared | off-wall | 0 |
| repaired | declared | all 47,040 | **0** |
| repaired | signature | all 47,040 | **0** |
| repaired | first argument | off-wall | **376** |
| repaired | rule text | all 47,040 | 0 (and 0 unconstrained) |

The last two rows are the interesting ones.

**Row 6 says both halves of X-1 are load-bearing.** The same 376, unmoved, on
the *fully repaired* manual: naming the pusher in the signature rescues the
signature reading and does nothing for a reader who takes `mentions` to be the
first argument. Only the definition rescues that one. A revision that had done
only the signature fix, or only the definition, would have left one of these
two rows red.

**Row 7 is why R1 is not a definition.** It does not mispredict — it cannot,
because "restore the unmentioned" and "leave alone what nothing wrote" coincide
whenever the write set is a subset of the mentioned set. Its defect is a hole in
the semantics, not a wrong answer, and holes do not show up as mismatches. On
this manual the unconstrained count is 0 only because every firing rule here
writes what it mentions or writes nothing; `blocked_wall` reads `Box.pos` and
assigns nothing, so under R1 the Box's successor is unconstrained on every
blocked transition — the probe counts that separately and it is why the row is
reported rather than celebrated.

## The A0 repair, and totality

`push2` gains `free(Box.pos)`; a new `blocked_box_on_wall` catches what it now
refuses; the two other blocked rules take the same clause. Over all 47,040
pairs: **0 mismatches, 0 states with no rule, never two rules.** The middle
number is the one that mattered — a repair that turns 52 wrong answers into 52
missing ones is not a repair, and the probe counts "no rule fired" as a
mismatch for exactly that reason.

`conflict exclusive` is discharged by **guard analysis alone** on the migrated
manual: 28 overlapping pairs, 0 undischarged. That needed a new disjointness
rule — `free(t)` contradicts `<inst>.pos = t` for an always-present instance —
which is the argument `a0-spike`'s own `semantics:` comment states in prose and
nothing checked. It is also a pair that exists **only** under the wide reading
of `slid`: read the event by its name and `walk`/`push2` share no claimed object
and are never examined. X-1's "the sweep ranges over too few pairs", as a
passing test.

## Territory

`a0-spike/` is the other track's and was **read, never written**. Its manual's
v0.3 migration is carried here as
`theory-compiler/tests/fixtures/sokoban2_theory.dsl`, with its unrepaired twin
`sokoban2_x5_theory.dsl` as the control that reproduces the 52. The migration is
offered to that track through `PARTNER_SYNC.md`.

## Compatibility — four manuals, four agents, four forms each

[compat/README.md](compat/README.md). PDDL, Lean and Markdown byte-identical
everywhere; `gen_python` differs in three helper hunks and nothing else; one
added warning per manual. Transition relations identical: 83,072 pairs for peg,
792 for the a0 family, 604 for a2.

**The a0-spike manual's own result corrected my account of it.** I had written
that the v0.2 chain refused it with *"unknown event `slid/2`"*. It does not:
both versions fail earlier and identically, in rule `walk`, on `moved/2` — a
default-table event — because `dir` is a free name bound by no `forall`. That is
an **E-02** gap predating all of this. So the true statement is stronger than
"v0.3 does not regress it": v0.3 changes nothing about it, bit for bit. The
contract now says that, and `verify.sh` asserts the refusal so the section
cannot quietly go stale.

## What the adversarial pass changed

An independent reviewer was asked to overturn the definition with a fourth
reading. Six findings survived scrutiny; four changed the work.

* **The 376/47,040 denominator error.** Caught before any number was published.
  The stratification above is the fix.
* **`free` is now referentially opaque, and the disjointness checker did not
  know.** `free(Cart.pos)` and `colored(Cart.pos, 2)` both hold when the Cart is
  alone on its cell, and reason 4 would have reported them *proved disjoint*. A
  false proof in a soundness-critical checker is worse than no proof.
  Self-excluding occurrences now live in a separate key namespace. Latent — no
  shipped manual writes it — and fixed anyway.
* **The same opacity has no STRIPS image and a wrong Markdown rendering.**
  `gen_pddl` refuses the clause; `gen_markdown` re-words it. Both are the
  "refuse what you do not implement" rule applied one layer down.
* **`stayed/1` writing `{}` narrows `conflict`, and my stated reason for the two
  extra `free(Box.pos)` clauses was wrong.** Under the new table those rules
  claim nothing and no pair of them is examined, so the clauses are not needed
  for `conflict exclusive` — they are needed to keep *exactly one rule fires*
  true, which is a strictly stronger property, is what `gen_exec` enforces, and
  fails on 24 pairs without them. The fixture says so now.

Two findings are recorded and **not** closed, in `dsl_grammar_v0.3.md` §9:

* **`writes` is a waypoint.** It leaves two artefacts that can disagree and
  answers with an assertion — structurally the arrangement X-1 was filed about,
  one level up. The successor is an event **body** (`event slid(o, p, dir):
  o.pos := beyond(o, dir); p.pos := ahead(p, dir)`), from which the write set is
  derived and cannot drift. Not adopted because it rejects every `events:` line
  in this repository — ten manuals against one — and because publishing bodies
  for the nine legacy events would reinstate the default-table hazard with more
  surface. **After v0.3 `frame persist` is well defined and `step` still is
  not**: two backends can satisfy `writes {o, p}` and produce different
  successors.
* **Parameters-only fails on a state-dependent write set** — a chain push, one
  flag away in `sokoban2.Rules`. No manual here refutes it; the next obvious
  variant of this repository's own world does.

## Found in passing, recorded not fixed

`gen_pddl` does not meet the backend obligation this contract states, and the
contract says so rather than implying it. Two defects, both pre-existing, both
byte-identical across this change, both pinned by name in `tests/test_writes.py`
so they are known numbers rather than a discovery someone makes twice:

* every event outside `moved`/`teleported` compiles to `:effect (and (and))` —
  the PDDL form of A0 has a button-press that presses nothing;
* `push-left` and `push-right` emit an **undeclared** `?dest`, because the
  manuals write `free(leftof(Cart))` and the extractor matches only
  `above|below|left|right`. Those actions are malformed, and this one
  *over*-approximates applicability: the cart may push left through a wall.

Repairing the STRIPS backend changes the fourth form of four manuals and is its
own piece of work.

## Suite

319 passed, 1 skipped (baseline was 287/1). `verify.sh` green end to end.
