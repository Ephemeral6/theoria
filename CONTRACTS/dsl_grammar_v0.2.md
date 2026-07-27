# dsl_grammar_v0.2.md

**Owner:** the `theory-compiler` track. **Supersedes:** `dsl_grammar_v0.1.md`,
which stays frozen and unedited — v0.1 is what the M8 rehearsal was built and
tagged against, and rewriting it would rewrite that history.

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
  domain and travel across levels. Grid layout, initial state, landmark
  coordinates and weight vectors are the problem, and are supplied per level.

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

Ledger entries E-01 through E-05 are **discharged** by this revision. E-03 was
the one named as "the one to fix first"; it is item 1.

### Deliberately not changed

* `candidates_schema.md` — frozen, and not this track's.
* `dsl_grammar_v0.1.md` — frozen. v0.2 is a new file.
* Connectivity-class invariants — still out of the invariant language. No manual
  has yet needed one, and adding it would mean a proof strategy this compiler
  does not have.
