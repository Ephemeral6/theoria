# Extension request · `semantics:` — dsl_grammar v0.1 → v0.2

**To:** the `theory-compiler` track (owner of `CONTRACTS/dsl_grammar_v0.1.md`)
**From:** `cold-start-a0`
**Status:** implemented as a local dialect here, requesting adoption upstream.
`CONTRACTS/dsl_grammar_v0.1.md` is frozen and **has not been touched**.

---

## The hole

`A0_REPORT.md` §4, found the hard way on the first real cold start:

> The most important semantic fact about `step` is not in the DSL.

The frame axiom — *if no rule fires for an object, that object is unchanged* —
had nowhere to live. In the A0 sprint it lived in a comment at the top of
`theory.dsl` and was hard-coded three times, once in each backend. Two
consequences, both bad:

1. **The handover test fails silently.** Theoria 1.8's first-tier deliverable is
   `theory.dsl` itself, read by a new agent with no context. A reader who
   compiles the A0 manual under any other default gets a different world, and
   nothing in the file tells them they have.
2. **Rejecting the `*_still_*` rules became unjustifiable on paper.**
   `cegis_miner` proposed eleven no-op rules with up to 74/74 coverage.
   `THEORIZE_LOG` R-07 rejects all eleven as *entailed by the frame axiom* — a
   correct call that shortens the manual by eleven clauses and removes eleven
   mutual-exclusion obligations, but it appeals to something the manual does not
   contain. Either the eleven clauses go in (and the manual is 11 clauses longer
   for no predictive content), or the axiom goes in.

Two neighbouring facts have the same problem and the same fix:

* **constraint 9** offers two routes to "exactly one successor" — provable guard
  disjointness, or an explicit and total priority order. The manual has to say
  which it is claiming, or `certify`'s expensive layer does not know what
  obligation to discharge.
* **cascade semantics** is left open by Theoria 1.8 on purpose, pending the API
  check ("先去复现轨迹里核实 ARC-3 有无世界自触发的 tick,再冻结"). It is a
  property of the world, so it belongs in the per-world book, not in the
  framework. A0 pinned it by fiat in `DECISIONS.md` D-A0-004 and had no way to
  write the decision down where it would be read.

---

## Proposed addition

One new top-level section. Three statements, each over a closed value set, no
free text, mandatory.

```
semantics:
  frame     persist | reset
  conflict  exclusive | priority: <rule> > <rule> [> ...]
  cascade   single_frame | multi_frame
```

Placement: after `word_table:`, before `events:`. Order inside the section is
free; all three must be present.

### `frame`

| value | meaning |
|---|---|
| `persist` | an object no firing rule mentions is unchanged in the successor |
| `reset` | such an object returns to its declared initial value |

This is what makes `step` **total**, and totality is half of constraint 9. It is
genuinely per-world: sokoban persists, a decaying cellular automaton does not.

### `conflict`

| value | meaning | proof obligation it declares |
|---|---|---|
| `exclusive` | at most one rule may fire per object per transition | the guards are pairwise disjoint — `certify` must prove it |
| `priority: r1 > r2 > ...` | if several fire, the earliest listed wins | the order is total over the rules that can collide — `certify` must prove *that* instead |

This is constraint 9's other half, and it names which of the contract's two
discharge routes the manual is taking. Today a reader cannot tell.

### `cascade`

| value | meaning |
|---|---|
| `single_frame` | one action yields one successor. **Every guard is read against the pre-state and all effects apply simultaneously.** |
| `multi_frame` | one action yields a frame *sequence*: rules re-fire on each intermediate state until quiescence |

The parenthetical in `single_frame` is not decoration. It cost this sprint a real
bug: rules were applied in file order, `press_left` recoloured the Button, and
`door_opens_left` then re-read its guard, found colour 8 instead of 7, and
silently did not fire — the Door never opened. With the semantics named, that is
a violation of a declared property rather than an implementation detail nobody
had written down.

`multi_frame` also changes the shape of the replay comparison and of the PDDL
encoding, which is exactly why it should be declared rather than inferred.

---

## Reference implementation

`cold-start-a0/compile/dialect.py` — parser, validator, and a deterministic
natural-language renderer for `theory.md` (a lookup over three closed value sets;
no model in the path, per Theoria 1.8's "不过 LLM,不许润色").

Used by all four A0 backends. `theory.dsl` and `theory_no_button.dsl` both carry
the section; `compile/compile_a0.py` **refuses to compile a manual without it**.

Rendered output, for the human reader:

> **How a Turn Works**
> If no rule applies to an object in a turn, that object is exactly as it was.
> At most one rule may apply to any one object in any one turn; the rules are
> written so that this cannot fail.
> One action produces one new situation. Every rule reads the situation as it was
> before the action, and all of their effects happen together.

---

## Compatibility, and the one thing to be careful about

`TheoryParser.parse()` skips lines it does not recognise, so a v0.2 manual still
parses under the v0.1 parser — **silently, and to a different world.** That is a
hazard, not graceful degradation: it is the very failure mode the section
exists to close.

So the request is specifically that **v0.2 make the section mandatory** and that
the parser **reject** a manual without it, rather than defaulting. A missing
`semantics:` should be an error with the same status as a missing `goal:`. The
A0 dialect already behaves this way (`SemanticsError`), and the A0 backends
additionally raise on any declared value they do not implement, following
`fd_adapter`'s rule that outside the supported subset is an error and never a
silent approximation.

---

## Cost

Three statements, ~40 lines of parser, one rendering table. The syntax is
world-independent and only the values vary per world, so the
`语法跨局同一,内容随局变` boundary of Theoria 1.7 is preserved: this gives a
manual the *concept* of a frame axiom, not any particular one.
