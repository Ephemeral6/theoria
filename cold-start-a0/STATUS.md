# STATUS — cold-start-a0

## All six milestones green (2026-07-28)

| tag | milestone | state |
|---|---|---|
| `cold-start-a0-m1-world` | A0 world + referee ground truth + explorer trace | ✅ |
| `cold-start-a0-m2-engines` | engines wired end to end, 29 schema-valid candidates | ✅ |
| `cold-start-a0-m3-theorize` | `theory.dsl` v1, every candidate adjudicated in `THEORIZE_LOG.md` | ✅ |
| `cold-start-a0-m4-certify` | replay ∧ responsibility green; Lean green, 0 axioms; plan SAT and the world agrees | ✅ |
| `cold-start-a0-m5-unsolvable` | variant UNSAT → certificate → `unsolvable`, 0 axioms, explained in the manual's vocabulary | ✅ |
| `cold-start-a0-m6-report` | `A0_REPORT.md` | ✅ |

```bash
cd cold-start-a0 && python run_all.py     # 8 steps, ~6 s, all green
cd cold-start-a0 && python -m pytest      # 26 passed
```

## Headline numbers

| | |
|---|---|
| replay | 276/276 frames, 22 356/22 356 pixels, 0 anomalies |
| accuracy vs. truth, base | 233/236 = 98.73 % |
| accuracy vs. truth, held-out pairs | **0/3** — the three predicted misses |
| accuracy vs. truth, variant | 92/92 = 100 % |
| Lean | `inv_all` and `unsolvable`, both with empty axiom lists, ~2 s each |
| plan | SAT, 12 steps, optimal; manual and world agree frame-for-frame |
| manual revisions forced by certify | **0** — see the caveat below |

## Standing caveats

**The inner loop was never exercised.** Both certify layers went green on the
first run of the first manual. A0 shows a theory can be *induced*; it shows
nothing about *repair*, which is what Phase 3 is for. `A0_REPORT.md` §6.1.

**Zero executable probes.** Every frontier ambiguity in A0 is either
extensionally undecidable (the competing predicates are the same predicate on
this geometry) or needs a configuration the world cannot be driven into. The one
that mattered — is the Button pressable from any direction? — is unprobeable
because the latch is irreversible. `A0_REPORT.md` §6.2.

**The manual has a known hole.** `press_left` was not generalised to the other
three directions, for want of evidence (`THEORIZE_LOG.md` R-05). The manual is
therefore wrong about three (state, action) pairs, and full-history replay cannot
see it. This was predicted before it was measured; it is the DC22 shape at small
scale and it is the most useful thing the spike produced.

**The frame axiom is not in the DSL.** *If no rule fires for an object, that
object is unchanged* has no sentence form in `dsl_grammar_v0.1`. It lives in a
comment and in three backends. A second reader compiling `theory.dsl` alone would
get a different world. Highest-priority expressivity gap; full ledger in
`THEORIZE_LOG.md` §E.

**Lean toolchain is local and gitignored.** `.toolchain/lean-4.9.0-windows/`,
278 MB, fetched during this sprint. `certify/lean_check.py` finds it or reports
`available: false`; it never downgrades a missing proof to a passing one.
D-A0-012 has the fetch command.

**Fast Downward is still not connected** (inherited from `engine-rig`). The
bundled BFS stub solved the 38-cell instance instantly, so nothing here is
blocked, but the planner path is untested at scale.

## Upstream

`engine-rig` and `theory-compiler` were **not modified**. Two gaps and one
defect were found and worked around inside this directory:

* `mdl_segmenter`'s colour-agnostic component operator fragments a world whose
  objects touch (D-A0-007). Worked around with a second operator chosen by script
  bits. *`engine-rig` added a native `split_by_color` switch mid-sprint;
  `pipeline/segment_operators.py` now detects it and uses it, keeping the local
  operator as a fallback for the `engine-rig-m8-integration` tag.*
* `theory_compiler`'s `gen_lean` and `gen_python` are specialised to the peg and
  cart fixtures and are not world-general (D-A0-011). The **parser** — the
  executable form of the frozen grammar contract — is reused; the backends are
  A0's own.
* **上游缺陷**: `TheoryParser._parse_func_call` matches an argument list with
  `[^)]*`, so a `then` clause containing a nested call or tuple parses its
  argument as a malformed name, silently, with no error (D-A0-013). Not fixed
  here; no tag affected.

## Blocked

Nothing.

## Next

`A0_REPORT.md` §7, in order: a frame-axiom sentence form for the DSL; an A0′ with
reversible mechanics and a probe-separable frontier, scored on revision count;
a responsibility-complete baseline for the concept compression account; connect
Fast Downward.
