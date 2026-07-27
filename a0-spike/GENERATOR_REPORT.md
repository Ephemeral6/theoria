# gen_python vs the A0 manual — a report for the theory-compiler track

A0 needs certify to replay history through the executable form compiled from
`theory.dsl` ("预测无侧门"). I tried to use your `generate_python` for that and
could not. This is the evidence, in the hope it is useful; all of it is
reproducible from `a0-spike/theory/theory.dsl`, which **your parser accepts
without complaint**.

## The headline

> A construct the generator cannot compile is emitted as `True` (guards) or
> `pass` (effects), silently.

That is worse than a crash, because it defeats the one check it feeds. certify
exists to catch a manual that is wrong about the world. A generator that quietly
replaces an unrecognised guard with `True` produces a `theory.py` that runs,
replays, and means nothing — and certify will happily grade it.

Concretely, the module generated from the A0 manual does this:

```python
s = State(player=Player(pos=(0,0)), box=Box(pos=(3,3)))
step(s, "move(Player, up)")     # -> player at (0,-1): off the board, no error
s.render()                      # -> all zeros: no object is ever drawn
```

**Suggested rule:** refuse. `raise` on any predicate, event, or expression
outside the supported subset. An uncompilable theory is a finding — it belongs in
the expressiveness ledger — not something to approximate.

## The specific defects

| # | Input in `theory.dsl` | Emitted | Should be |
|---|---|---|---|
| 1 | `free(ahead(Player, dir))` | `if not (True)` | a bounds/occupancy test, or refuse |
| 2 | `then slid(Box, dir)` | `pass  # Event: slid` | the effect, or refuse |
| 3 | `Box.pos = ahead(Player, dir)` | `state.box.pos == ahead(state.player, dir)` | `ahead` and `dir` are undefined names → `NameError` if reached |
| 4 | `not Box.pos = ahead(...)` | `not Box.pos == ...` | `Box` is the **class**, not `state.box` |
| 5 | any object | `render()` returns an all-zero grid | objects drawn; full-frame responsibility is uncheckable otherwise |
| 6 | — | `DIRECTIONS` maps `up` to `(0,-1)` applied as `(pos[0]+dx, pos[1]+dy)` | so `pos[0]` is x/column; a `(row, col)` world silently transposes |

Defect 2 is currently masked by defect 1: `walk`'s guard is `True`, so `walk`
always fires first and `push2` is never reached — which is also why the
`NameError` in defect 3 never surfaces.

## Two parser issues

**Negation is not parsed.** `not free(ahead(Player, dir))` comes back as
`NameRef(name='not free(ahead(Player, dir))')` — the whole expression as a name
string — and `not Box.pos = ahead(...)` as
`Comparison(left=NameRef('not Box.pos'), ...)`. There is no negation node, so a
consumer has to string-match `"not "` prefixes to recover the meaning.

**`compress` rejects the documented syntax.** `compress: -39B` raises
`ValueError: invalid literal for int() with base 10: '-39B'`, but the frozen
contract says `compress: <bytes>` and Theoria.md §1.10a writes `compress: -412B`
with the suffix. One of the two should move; the contract is frozen, so probably
the parser. I worked around it by dropping the `B`.

## What I did instead

`a0-spike/pipeline/gen_exec.py` — a generator for the A0 subset only, driven by
**your parser** so the DSL stays the single source. It handles `free`,
`ahead`/`beyond`, object-position comparisons, negation, and the `moved` /
`slid` / `stayed` events, and it raises `UncompilableTheory` on everything else.

It is a stopgap and I would rather delete it than maintain it. If `gen_python`
grows the A0 subset, `a0-spike` will switch to it.

## What compiling the manual bought

Worth recording, because it is the argument for doing this at all: compiling
`theory.dsl` immediately caught an error in the manual that the mined-rule replay
had not. I had adjudicated

```
rule blocked_wall ... then moved(Player, dir)
```

and the generated code duly walked the player off the board. The event vocabulary
had no way to say "nothing happened", so `stayed(o)` was added and the rules
corrected. The mined rules had the right effect all along — the error was in my
adjudication, and only the executable form exposed it.

## Expressiveness ledger items from A0

1. **`beyond(o, dir)`** — the cell two steps ahead. The v1 guard vocabulary lists
   `above/free/adjacent/∈region`; a world where a push travels two cells needs it.
2. **One rule, one event.** `when <guard> then <event>` is singular, but a push
   visibly moves two objects. A0 folds this into a compound `slid` whose meaning
   lives in the generator rather than in the DSL, which is not ideal.
3. **A no-op event.** `stayed(o)` above. Without it, "the action did nothing" has
   no expression, and the natural mistake is to write a movement event.
