# THEORIZE_LOG — every candidate, and why it was accepted, rejected, or left to a probe

The engines propose; only the theorize step writes into the two books
(Theoria 1.10(b), 分工三律 rule 1).  This file is that step's record for
`cold-start-a3`.  It covers **41 candidate rows** from `artifacts/candidates_l1.jsonl`
(3 object hypotheses, 36 rule hypotheses, 2 invariants) plus the 17 probe
designs in `artifacts/engines_report_l1.json`.

Two conventions, both inherited from A0 and A2:

* a rejection is a **ruling**, not an omission — every rejected family has a
  line here, and the reason is a criterion, not a preference;
* where two readings fit the evidence equally, the log says so and the manual
  carries the ambiguity openly rather than closing it quietly.

**When the referee's copy was first read.** `artifacts/ground_truth.json` was
not opened before `theory/domain.dsl` reached revision 1.  It was read
afterwards, to score the manual and to write `A3_REPORT.md` §3.  The traces and
the candidate streams are the only inputs to everything below.

---

## O — objects (3 candidates, `mdl_segmenter`)

The chosen operator is `connected_components(4)+uniform_color`, on
`script_bits`, over `connected_components(4)`.  Three tracks, all 1×1.

| id | colour | frames present | ruling |
|---|---|---|---|
| obj0 | 7 | 333/333 | **accept as `Switch`** |
| obj1 | 6 | 333/333 | **accept as `Cart`** (the mover) |
| obj2 | 5 | 161/333 | **accept as `Door`**, with `present: Bool` |

**O-01 · the mover is obj1.**  `multi_miner.mover_track` picks it and the
evidence is not close: 225 of 332 transitions move it, and no other track ever
changes position.

**O-02 · the Door needs a `present` field, the other two do not.**  obj2 is
absent in 172 frames and present in 161.  A colour field cannot express "not
there"; `vanished` / `appeared` need a boolean.

**O-03 · the two portal cells are NOT objects, and this is a result.**  Colours
3 and 4 are constant across all 333 frames, so `extract_board` assigns them to
the **board** and they never reach the object layer.  That is correct — they are
terrain, not objects — and it is only true because the Cart never stands on
one.  The first version of this world made each portal's exit the *other*
portal's cell so that both landmarks could be read off frame 0; the Cart then
stood on marked cells, and the segmenter's frame-to-frame matcher preferred
"the resident recolours to 6, and the mover vanishes" to "the mover jumped".
The mover's track went missing in 19 of 326 frames and the miner proposed
`obj3_appear_*` / `obj3_vanish_*` instead of a jump.  The run is kept at
`artifacts/finding_d_a3_003/` and written up as **D-A3-003**.  The world was
changed, not the engine, and the price of the change is that a portal exit is
invisible in every frame and must be supplied per level — see §P below.

**O-04 · the concept account, and a difference from A0 and A2.**
`artifacts/concept_accounts.json`, priced against a responsibility-complete
alternative (Theoria 1.8, as corrected by A0's finding O-04):

| object | script with | without | **delta** |
|---|---|---|---|
| Cart | 2539 | 4910 | **+2371** |
| Switch | 73 | 80 | **+7** |
| Door | 72 | 80 | **+8** |

**All three pay for themselves.**  A0 and A2 both had to admit their
Button and Door at a *negative* account (−5 and −1 in A2) and justify them on
responsibility-completeness plus the invariant language having no pixel-level
paraphrase of the latch.  A3 does not need that argument, and the reason is
mechanical: A0's Button is a latch that fires once, so declaring an object to
explain one event costs more than it saves.  A3's Switch is a **toggle** and
recolours 46 times, so the object earns its declaration outright.
Reversibility (F-12) was adopted to make rules re-witnessable; that it also
flips the sign of the concept account was not predicted, and it is worth
recording because it means A0's O-04 conflict between constraint 5 and
constraint 2 is *contingent on irreversibility*, not intrinsic.

---

## R — rules (36 candidates, `cegis_miner`)

### Accepted

**R-01 · `push_<dir>` × 4** — `free(strip(<dir>))` → move one cell.
Coverage 69/69, 70/70, 40/40, 46/46; frontier 3 each.  Adjudicated to `free`
over the two alternates in the frontier on description length, as A0 did.

**R-02 · `teleport_a_<dir>` × 4** — `tcolor(<dir>)==3` → the Cart is placed on
`exit_a`.  Coverage 2/2, 2/2, 4/4, 2/2.

**R-03 · `teleport_b_<dir>` × 4** — `tcolor(<dir>)==4` → `exit_b`.  Same shape.

**R-04 · the Switch and Door cascade × 8** — `press_<dir>` / `door_opens_<dir>`
on `tcolor==7`, `unpress_<dir>` / `door_closes_<dir>` on `tcolor==8`, for the
two directions the geometry admits.  Each pair shares a guard, which is how
`cascade single_frame` is declared and how the PDDL backend recognises the
Door event as a consequence of the toggle rather than an action of its own.

**Both polarities are enumerated evidence, not analogy.**  A0 had one witness
for `press` and no way to obtain a second, so its direction generalisation had
to be rejected and its manual shipped a known hole (A0′_REPORT §1).  A3's
Switch is a toggle in a reversible world, so `unpress` and `door_closes` have
their own witnesses (t2; t58, t114).  This is F-12 being cashed rather than
cited.

### R-05 · the adjudication this spike turns on

The miner proposed the eight teleports as eight **ground displacements**,
because a displacement is what a frame diff shows.  For colour 3 the four
vectors are

    (dy, dx) ∈ { (0, +4), (−1, +3), (−1, +5), (−2, +4) }

— four different vectors — and the four destinations are

    { (1, 6) }

— one cell.  Colour 4 likewise: four vectors `{(0,−4), (+1,−5), (+1,−3),
(+2,−4)}`, one destination `{(3, 2)}`.  The arithmetic is re-run by
`tests/test_theorize.py::test_the_landmark_reading_is_what_the_evidence_shows`
rather than being trusted from this paragraph.

`jumped(Cart, exit_a)` explains all four with one clause; the displacement
reading needs four and has no shorter form.  Description length picks the
landmark reading.

**But description length is not what decides it, and the real reason is worth
more than the ruling.**  The displacement reading **cannot be written down at
all**.  The event language is closed — `moved(o, dir)`, `jumped(o, dest)`,
`recolored(o, c)`, `vanished(o)`, `appeared(o)` — `moved` carries exactly one
cell, and `jumped` carries a **landmark**, whose value the contract assigns to
the problem instance.  There is no form in the grammar for "displace the Cart
by (−1, +3)".  So the only expressible reading of a non-adjacent move is the
portable one.

That is a stronger fact about the framework than the adjudication it produced.
The domain/problem split is usually described as a discipline — *put
coordinates in the problem file* — and a discipline can be violated by a
careless author.  Here it is **enforced by the effect language**: a
level-specific jump is not a clause the theorize step could write badly, it is
a clause it could not write.  Compare R-08, where the *guard* language happily
offered `!at(3,1)` and only the author's judgement kept a coordinate out of the
domain.  The two halves of the language are not equally protected, and that
asymmetry is now on the record.

**Two consequences, and the second one costs A3 something.**

1. Level 1's evidence does not distinguish the two readings — same transitions,
   same predictions, zero residual — and `probe_frontier` cannot manufacture a
   separating experiment inside one level, because separating them requires a
   portal somewhere else.  The clause is therefore carried as a theorem with a
   named dependency (`portal_destination_is_absolute`) whose status after
   level 1 alone is *undecided*, and level 2 is what decides it: the manual
   predicts `(1,5)` and `(4,1)` for level 2's portals, cells it has never seen,
   and either the replay agrees or it does not.
2. A3 therefore **cannot** run the displacement reading as a control arm — the
   compiler would reject it, so there is no artefact to compare against.  The
   claim "the portable reading is the right one" rests on level 2's replay
   agreeing, and not on a side-by-side with the alternative.  The negative
   controls that *are* runnable come from the world side instead
   (`a3pipeline/negctl.py`, L2_ONEWAY and L2_REWIRED), and they test a
   different thing: not "is this reading right" but "would a wrong domain be
   caught".

### Rejected

**R-06 · `obj1_still_<dir>` × 4, `obj0_still_*` × 4, `obj2_still_*` × 4 —
rejected, all twelve.**  `semantics: frame persist` already says an object no
firing rule mentions is unchanged, so a rule whose effect is `none` states
something the manual has declared globally.  Admitting them would also break
`conflict exclusive`: `obj1_still_LEFT` (`tcolor(LEFT)==1`) and `push_left`
(`free(...)`) are disjoint, but `obj0_still_LEFT` has the guard `act==LEFT` and
nothing else, which overlaps every other rule for that object.

**R-07 · the overfitted no-op guards.**  Two of the rejected twelve are worth
naming because they show what the miner does when it is asked for a rule that
should not exist.  `obj1_still_UP` came back as
`!clear(strip(UP)) ∧ !tcolor(DOWN)==1 ∧ !tcolor(UP)==4 ∧ act==UP`, which
mentions the cell *below* the Cart in a rule about pushing *up*, and
`obj0_still_DOWN` came back as `!at(3,1) ∧ act==DOWN` — a coordinate, in a
domain that must not contain one.  Both are consistent with all 332
transitions.  They are artefacts of demanding a positive guard for the absence
of an event, and they are the cleanest argument in this log for why
`frame persist` is a semantics declaration and not a rule.

**R-08 · a coordinate would have entered the domain here.**  `!at(3,1)` and
`!at(5,1)` appear in four proposals.  Had any been accepted, `domain.dsl` would
contain a level-1 cell and C3 would have been untestable — the file would not
have travelled and the reason would have been invisible until level 2 failed.
Recorded because it is the concrete form the domain/problem leak takes: it does
not arrive as a section, it arrives as an atom inside a guard.

### R-09 · left on the record, not compiled

`obj1_step` — one `?dir`-lifted rule, coverage **225/225**, replacing four
ground clauses — is the miner's better answer and it is not in the manual.  The
Python backend's guard subset takes a literal direction, so a lifted rule
compiles to nothing.  This is A2's §8 limitation reproduced on a third world;
it is an expressiveness gap in the backend, logged rather than worked around.
Its cost here is exactly 3 clauses of the 20, twice over (push and the lifted
`still` we rejected anyway).

---

## L — laws (2 candidates, `zero_space`)

**L-01 · `switch_door_latch`, accepted.**  The engine returned
`(8@(4,1) + 5@(6,7)) mod 2 = 1` — "exactly one of *the Switch shows 8* and *the
Door exists*", as a GF(2) law over cell occupancy.  Written into `laws:` with
`source: zero_space` because the numbers came from an engine and a reader
should not have to take that on trust (v0.2, E-05).

The engine states it over two **cells**; the manual states it over two
**counts**.  That rewriting is the theorize step's act, and it is what makes the
law portable: `count(Switch, 8) + count(Door) = 1` mentions no cell and is true
in level 2 unchanged, whereas `8@(4,1) + 5@(6,7)` is a sentence about level 1.
The same conversion is why the playbook's `prune` entry can be carried.

**L-02 · the Cart occupancy law, accepted as `cart_unique`.**  The second
global law is a 32-cell parity over colour 6 — "exactly one of these cells
holds the Cart, always".  Recorded as `count(Cart) = 1`, and deliberately *not*
proved in Lean: representing a state as the Cart's cell already assumes there
is exactly one Cart, so a Lean proof would be discharged by the representation.
It is checked where it can actually fail — per frame, by the cheap layer's
responsibility pass.  (A0's L-01 ruling, unchanged.)

---

## P — probes (17 designs, `probe_frontier`)

**All 17 are `hypothetical`; zero executable.  This is a finding and it is not
the one A0 had.**

A0's first run also emitted zero executable probes, and A0′ diagnosed the cause
as the *irreversibility* of A0's latch: the configurations needed to split the
frontier could not be reached twice.  A3's world is reversible, so that cause is
absent — and the probe count is still zero, for a different and more
interesting reason: **the sweep already covers every reachable (state, action)
pair, so there is no unvisited configuration left to visit.** `probe_frontier`
correctly reports every remaining frontier split as "separable in principle,
but the world was never observed in this configuration" — where *this
configuration* is one level 1 does not contain at all.

So the two runs return the same number for opposite reasons, and the
distinction matters for how the probe machinery should be read: zero executable
probes at 47 % coverage (A0′) means the machine is starved; zero at **100 %**
coverage means the machine is done.  The frontier that remains is not
under-explored, it is **under-determined by this level** — and the only
instrument that can split it is a second level.  That is R-05 again, arriving
from the probe side.

---

## Rounds

**One.**  `theory/domain.dsl` reached revision 1 and was not revised: the cheap
layer was green on the first compile, the plan was SAT, and nothing refuted
anything.  A revision count of 0 is reported the way A0′ reported it — with the
reason measured rather than guessed.  Every rule has as many witnesses as its
geometry admits, no rule is untested by the trace, and the one genuinely open
question (R-05) is open because it is *unanswerable* within level 1, not
because the evidence ran short.

The transfer arm's round count is in `artifacts/bill_*.json`, and it is the
number the report is actually about.
