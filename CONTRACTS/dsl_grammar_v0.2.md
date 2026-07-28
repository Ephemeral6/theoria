# dsl_grammar_v0.2.md

**Version:** 0.2 · **Status:** 定稿（`theory-compiler` 单方所有，不需要会签）·
**Effective:** 2026-07-28

**Owner:** the `theory-compiler` track. **Supersedes:** `dsl_grammar_v0.1.md`,
which stays frozen and unedited — v0.1 is what the M8 rehearsal was built and
tagged against, and rewriting it would rewrite that history.

**Freeze policy.** v0.2 is frozen at the tag that carries this line. Anything
further goes into a `dsl_grammar_v0.3.md`, by the same rule that produced this
file: **a change needs a ledger entry or a defect that forced it**, named in the
revision record. "It would read better" is not a reason to touch a contract two
tracks compile against.

**Why this one needs no countersignature and `candidates_schema_v0.2.md` does.**
`CONTRACTS/` holds contracts of two different kinds. This grammar is *owned* by
this track — `engine-rig` neither writes nor reads `theory.dsl` — so adopting a
ledger-forced extension is this track's call alone. `candidates_schema.md` is
the other kind: `engine-rig` is the writer and this track only reads, so its
revision is a draft until the writer signs. Ownership, not politeness, decides
which is which.

Every change below was forced by a specific entry in the expressivity ledger
(`cold-start-a0/THEORIZE_LOG.md` §表达力台账) or by a specific defect found while
compiling a real manual. The revision record at the bottom names which, for each.

Executable form: `theory-compiler/src/theory_compiler/parser/`. Where this
document and that parser disagree, the parser is the defect.

---

## theory.dsl — five sections

### word_table (extended)

```
word_table:
  board                                   # never co-varies; implicit
  object <Name> { <field>: <Type>, ... }  # observations only
  <ObjName> [segment: <method> ev: <range> compress: <bytes>]
  domain   <name> { <v1>, <v2>, ... }     # NEW — a finite value set        (E-02)
  landmark <name>                         # NEW — a cell the level locates  (E-04)
  weights  <name> over <field>            # NEW — a potential the level fills (E-05)
```

`domain`, `landmark` and `weights` all declare a **name** whose **value** lives
in the problem instance. That is the domain/problem split made writable: v0.1
had the split but no way to say which free names crossed it, so a reader of
`theory.dsl` alone could not tell level data from world data.

### semantics (new section, **mandatory**)

```
semantics:
  frame     persist | reset
  conflict  exclusive | priority: <rule> > <rule> [> ...]
  cascade   single_frame | multi_frame
```

Placement: after `word_table:`, before `events:`. Order inside is free; all
three must be present. Adopted from `cold-start-a0/proposals/dsl_grammar_v0.2_semantics.md`
essentially verbatim.

| statement | meaning | why it is per-world |
|---|---|---|
| `frame persist` | an object no firing rule mentions is unchanged | sokoban persists; a decaying cellular automaton does not |
| `frame reset` | such an object returns to its declared initial value | |
| `conflict exclusive` | at most one rule per object per transition; the guards are pairwise disjoint and `certify` must prove it | constraint 9 offers two discharge routes and the manual has to say which it claims |
| `conflict priority: ...` | if several fire, the earliest listed wins; `certify` proves the order is total over colliding rules | |
| `cascade single_frame` | one action, one successor. **Every guard reads the pre-state and all effects apply together.** | Theoria 1.8 defers this to the trace, so it is a fact about the world |
| `cascade multi_frame` | one action yields a frame sequence; rules re-fire until quiescence | |

**Mandatory is the whole point.** The v0.1 parser skips lines it does not
recognise, so a manual carrying `semantics:` still parses there — silently, and
to a different world. Defaulting the section would reproduce exactly the hazard
it exists to close, so a manual without it is **rejected**, with the same status
as a missing `goal:`.

The parenthetical under `single_frame` is not decoration. Applying rules in file
order instead cost the A0 sprint a real bug: `press_left` recoloured a button,
and `door_opens_left` then re-read its guard against the updated state, found
the new colour and silently did not fire.

**Every backend must refuse a value it does not implement.** Declaring the fact
buys nothing if a generator reads the declaration and encodes a different world
anyway — that is this section's own hazard, one layer down. So a backend
supporting only part of the value set raises, names the value, and stops;
`fd_adapter`'s rule, applied to the compiler. As of v0.2 no backend in this
repository implements `frame reset`, `conflict priority:`, or `cascade
multi_frame`; all three parse, and all three are refused at generation.

### events

Unchanged in syntax. Newly load-bearing: a backend dispatches on **name and
arity**, and the declaration is what distinguishes `jumped(o, dest)` — move to a
landmark — from `jumped(p, over, dir)` — a peg jump. Two manuals may use one word
for different events; the signature is what says which.

### rules (extended)

```
rules:
  rule <name> [forall ?<var> in <domain-or-type>]... [ev: <t,...>  cov: <k>/<n>]
    when <guard> then <event>
```

Two extensions:

* **`forall ?v in <domain>`** (E-02) — the rule is a schema. Grounded at compile
  time into one rule per value, named `<rule>_<value>`. `<domain>` may be a
  declared `domain` (grounded from the manual) or a declared object type
  (grounded from the level's instances, so one clause covers a board with any
  number of pegs on it). Distinct variables always take distinct instances.

* **`not <predicate>`** (E-01) — a guard clause may be negated. The complement of
  a decidable spatial predicate is decidable, so this stays inside the v1 guard
  language. `not act=...` is **rejected**: a rule fires on one action, and
  negating the action match would make it fire on every other action instead.

### goal

Unchanged in syntax. `count(<Type>[, <field> = <value>]) = <n>` is now
compiled rather than ignored.

### laws (extended)

```
laws:
  invariant <name> <expr> <op> <const>  [status: proven|open  source: <engine>]
  theorem   <name> "<one sentence>"     [depends: <rules>  probe: passed|pending]
```

* **`pagoda(<weights-name>)`** (E-05) — an invariant body may name a declared
  weight function. Its meaning is `sum of w[i] over occupied i`. v0.1 had no way
  to name a weight, so the A0 and peg manuals both spelled the potential out as a
  free-text comprehension no backend could read.

* **`source:`** (E-05) — where the numbers came from. `source: lp_potential`
  means an engine solved for them, not the author. A1 turns on exactly that
  distinction, and a reader should not have to take it on trust.

---

## Expressivity boundary (v2)

* **Guard language:** spatial predicates, object comparisons, integer arithmetic,
  and negation. Proof goes through a decidable procedure (`decide`/`omega`).
* **Invariant language:** linear arithmetic, object counts, mod-2 parity, and
  finite weight functions of pagoda type. **Connectivity-class invariants remain
  unsupported** — record them in the ledger; do not extend this contract by hand.
* **domain/problem split:** `word_table` + `semantics` + `rules` + `laws` are the
  domain and travel across levels. Grid layout, initial state and landmark
  coordinates are the problem, and are supplied per level.

* **Weight vectors are the one thing the split does not settle.** A `weights w`
  declaration names a free vector, and its numbers may arrive from the level
  *or* from an engine certificate. **A compiler must accept the certificate as a
  source** — requiring the level to repeat the numbers means hand-copying an
  engine's output into a checked-in file, and a hand-copy is how a proof comes
  to rest on weights nobody re-solved. If both sources supply the vector they
  must be **equal**, and a disagreement is an error, not a precedence question.
  One certificate fills one declared name; a compiler holding one certificate
  and two unfilled declarations must **refuse** rather than pick.
  Whichever source won must be recorded in every form that prints the numbers —
  `source: lp_potential` says an engine solved for them, and a reader who cannot
  see which file they came from cannot check that.

### A standing limit worth stating in the contract

`pagoda(...)` is **sound but incomplete**: some genuinely unsolvable
configurations admit no linear pagoda function at all. On the 5-cell peg board
from `11011`, exactly two of the five single-peg goals are certifiable this way.
A generator must therefore **refuse** to emit a proof whose theorem is broader
than the certificate it was given, rather than narrowing the claim silently. An
uncoverable goal is an open question, and belongs in the ledger.

---

## playbook.dsl

Unchanged from v0.1, including the hard anti-cheat rule: no literal action
sequences, and a parser that finds one must reject it rather than accept it
silently.

---

## Revision record — which rule forced which change

| # | change | forced by | what it cost to not have |
|---|---|---|---|
| 1 | `semantics:` section, mandatory | **E-03**, and `A0_REPORT` §4 | the most important semantic fact about `step` was a comment, hard-coded three times, once per backend; and rejecting eleven mined no-op rules appealed to an axiom the manual did not contain |
| 2 | `not` in guards | **E-01** | A0 had to name a complement predicate `blocked` to say "not clear" |
| 3 | `forall ?v in <domain>` | **E-02** | one lifted rule mined at 212/212 was written out as four rules that each looked like a weaker claim |
| 4 | `forall ?v in <ObjectType>` | **E-02**, and D-A0-011 | `gen_python` assumed one instance per declared type, so the peg world's rules compiled to `pass  # Implemented in specific game code` |
| 5 | `landmark <name>` | **E-04** | free-floating names resolved by the problem instance; a reader of `theory.dsl` alone could not tell which names were level data |
| 6 | `weights <n> over <f>` and `pagoda(<n>)` | **E-05** | the weight vector had no name, so the invariant could not refer to it and the potential was free text |
| 7 | `source:` on an invariant | **E-05** | nothing distinguished an engine-derived invariant from an author-derived one |
| 8 | balanced-paren argument parsing | **D-A0-013** | `then jumped(Cart, (1, 1))` parsed its second argument as the name `(1, 1` and raised nothing — a silently wrong AST |

| 9 | weight vectors may come from a certificate | **E-06**, D-TC-013 | `gen_lean` read the numbers from the certificate and the other three backends read them only from the level, so a manual either hand-copied the engine's vector into a checked-in file or rendered a `theory.md` that named a potential it could not show |
| 10 | a backend must refuse an unimplemented `semantics:` value | the `semantics:` proposal's own closing paragraph, and a defect found while finalising this version | `gen_pddl` reads only the AST — never the IR, never the predictor — so no guard reached it, and a manual declaring `frame reset` + `cascade multi_frame` compiled to a STRIPS encoding of `persist` + `single_frame` without a word of complaint |

Ledger entries E-01 through E-05 are **discharged** by this revision. E-03 was
the one named as "the one to fix first"; it is item 1.

**E-06 is not discharged, and item 9 is not it.** E-06 is the ledger entry for
`goal count(Peg, alive) = 1` being *unprovable*: on the 5-cell board from
`11011`, three of the five single-peg goals admit no linear pagoda function at
all — `engine-rig`'s own `test_interop.py` pins them as unprovable by this
method, not merely unexported. The configuration really is unsolvable; the
invariant language cannot carry the conclusion. Item 9 discharges the
*transcription* half that E-06 dragged along with it. The proof half stays open
and needs one of two things, neither of which is a grammar change:

* the invariant language grows past linear arithmetic / counts / parity / finite
  weights — which this contract explicitly forbids doing by hand; or
* a different proof method supplies the certificate. `ic3_pdr` is the live
  candidate: it is the engine that exists *because* `lp_potential` is infeasible
  on exactly this kind of configuration, and it reports the same three
  obligations (`inv_init` / `inv_closed` / `goal_break`) that this compiler
  already knows how to re-derive. What is missing is a certificate export for
  it — `engine-rig/interop/certificates/` holds pagoda documents only. That is
  the shape of the next round, and it is `engine-rig`'s side of the boundary.

Until then a compiler must keep **refusing** to emit a theorem broader than its
certificate. That refusal is the contract's own rule (see the standing limit
above), and it is the entire reason E-06 is a recorded open question rather than
a slightly-overclaiming `unsolvable`.

---

## Migrating a v0.1 manual to v0.2

Mechanical, and short. A v0.1 manual is a v0.2 manual **plus one required
section**; everything else v0.2 added is opt-in.

1. **Add `semantics:`** — the only mandatory step, and the only one that can
   change what the manual means. Place it after `word_table:`, before `events:`,
   and state all three:

   ```
   semantics:
     frame     persist        # or reset
     conflict  exclusive      # or priority: r1 > r2 > ...
     cascade   single_frame   # or multi_frame
   ```

   **Do not copy these three values from another manual.** They are per-world
   facts. `persist` / `exclusive` / `single_frame` is what A0 and A2 both
   declared, but a decaying world does not persist, and a world with a
   self-triggering tick is not `single_frame`. If you do not know which is true,
   that is a finding to probe, not a default to accept — the whole reason the
   section is mandatory is that guessing it silently produces a different world.

2. Everything else is optional and changes nothing until used: `domain`,
   `landmark`, `weights` / `pagoda(...)` / `source:`, `forall ?v in ...`,
   `not <predicate>`. A v0.1 manual that uses none of them compiles under v0.2
   to the same four forms.

3. `playbook.dsl` needs no migration at all.

### The one hazard, stated plainly

**A v0.2 manual parses under a v0.1 parser — silently, and to a different
world.** The v0.1 parser skips lines it does not recognise, so `semantics:` and
its three statements vanish and the manual compiles under whatever default the
backend happens to hard-code. That is not graceful degradation; it is the exact
failure the section was added to close.

Consequences, in both directions:

* **v0.1 manual under a v0.2 parser** → **rejected**, loudly, for a missing
  `semantics:` section. This is deliberate (D-TC-011): the same status as a
  missing `goal:`. Migration is adding three lines, and being told to add them
  beats compiling a world nobody declared.
* **v0.2 manual under a v0.1 parser** → **accepted, wrongly**. Nothing warns.
  If you must feed a manual to a v0.1 parser, delete the `semantics:` section
  first and accept that you no longer know which world you compiled.

By contrast, a missing `landmark` declaration is a **warning**, not an error —
it compiles to exactly the same world and costs only legibility. E-03 is
mandatory because it changes the world; E-04 is not because it does not.

### Deliberately not changed

* `candidates_schema.md` — frozen, and not this track's.
* `dsl_grammar_v0.1.md` — frozen. v0.2 is a new file.
* Connectivity-class invariants — still out of the invariant language. No manual
  has yet needed one, and adding it would mean a proof strategy this compiler
  does not have.
