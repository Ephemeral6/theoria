# RUN_STATE — R2-2, the expressivity hole that was not one

**Cell:** R2-2 · **Territory:** `theory-compiler` · **Branch:** `z/r2-2-grammar`
**Spend:** $0.00. No ARC action, no desk call, no model call, no network.
Sealed pile: zero contact. `theoria-arm/` was read and never written.

## What was asked, and what the evidence said back

The brief said: close GAP R2-2 — a genuine expressivity hole — by designing the
smallest grammar extension that lets the edge-advance law be written, entering
it in the 表达力台账, and implementing it across the four forms. It also said,
in instruction 4: *if the honest answer is that the grammar CAN say it and the
arm simply never writes it, that is the finding — say so and stop, with the
counter-example manual.*

**Instruction 4 fired.** Verified before anything was built:

* one manual, byte-identical, three levels differing only in which cells carry
  an instance. With one seated on the leading-edge cell the rule fires and burns
  exactly that cell; with the arm's seating the same bytes fire nothing
  (`SEATING.json`, L1/L2/L3);
* the arm's own r3 manual had already located the cause correctly —
  *"the hole is a property of the arm"* — and `GAPS.md` re-routed it here;
* the arm compiles through this compiler (`theoria-arm/inner/books.py` imports
  `generate_python`), so the question was answerable offline, here.

So no grammar extension was invented, `CONTRACTS/dsl_grammar_v0.3.md` is
untouched, and the parser is untouched.

## What was found instead, and it is the reason R2-2 existed

Nine spellings of the law through the parser and all four forms
(`PROBE.json`). One is a trap, and it is the first spelling anyone reaching for
a board cell writes.

`recolored(<landmark>, 1)` **compiled** in three of the four forms. The declared
write set and the compiled effect both said `{edge}`, so
`check_backend_agreement` passed; the emitted `state.edge_color = 1` landed on a
plain dataclass with no such field, so it *succeeded*; `State.key()` omits it,
so the two states compare equal; `render` rebuilds every frame from the constant
`BOARD`. Measured: the rule is in `RULES`, `fired()` reports it firing, and the
frame does not move.

A rule that fires and means nothing, reading exactly like one that works. That
is strictly worse than a refusal — a refusal names the repair, this sent the
reader away believing the language could not say it.

Second, smaller: `gen_markdown` rendered `recolored(leftof(?s), 1)` as *"then
leftof(?s)'s colour becomes 1"* while `gen_python` and `gen_lean` both refused
the same manual. The prose form was the only one saying the manual meant
something.

## Numbers, verbatim

```
                                    before        after
theory-compiler test suite          363 passed    375 passed, 1 skipped
new tests                           -             12 (3 positive, 7 negative, 2 pins)
negative-control mutation           -             checks removed -> 9 of 12 red,
                                                  survivors = the 3 positive controls

SEATING.json      L1 varied only    fired []                 row unchanged
                  L2 + edge         fired [Bar_5]            9 9 9 9 9 1 1 1
                  L3 every cell     fired [Bar_5]            9 9 9 9 9 1 1 1

PROBE.json        9 spellings x 4 forms; S3 (landmark) was the trap,
                  S6 (moved) is the closest workaround and says a different
                  law: 9 9 9 9 9 1 9 1 -- it slides a mark, it does not
                  advance an edge
```

## Residual gaps, stated

1. **R2-2 is re-addressed, not closed.** The repair — seat an instance on the
   leading-edge cell — is `theoria-arm`'s. Ask in `monitor/inbox/`.
2. **The seating's cost is unmeasured.** L3 on a 64×64 board is 4096 instances;
   L2's targeted seating is the cheap version and is what the ask asks for.
   Neither number was measured; that needs the arm's harness.
3. **`gen_pddl` sees neither new check** — it does not call `build_ir`. It
   refuses this world class for its own pre-existing reason, so nothing is
   currently hidden, but a manual that reaches it and writes a landmark would
   still be compiled. Named, not fixed: the 2026-07-31 PDDL repair must not be
   regressed.
4. **The unseated-instance case warns rather than refusing.** Deliberate — the
   first draft errored and deleted `a0-cart`'s `no-button` level from a
   checked-in handover package. The effect still compiles to a do-nothing
   assignment; the count is pinned in tests rather than trusted to memory.
5. **No live evidence, and none was needed for the routing.** A leg would settle
   whether a seated edge instance turns those 12 predictions into rules that
   survive replay. Cost: one `theoria-arm` leg. Not run, no spend authority.

## Gates

`python -m pytest -q`, `python -m tools.verify_c8`, `python CONTRACTS/verify.py`
— outputs verbatim in `GATES.txt`.
