# STATUS — cold-start-a0

## All six milestones green, plus the four follow-ups (2026-07-28)

Follow-ups from `A0_REPORT.md` §7, all four attempted:

| # | item | state | tag |
|---|---|---|---|
| 1 | a frame-axiom sentence form for the DSL | ✅ `semantics:` dialect + v0.2 proposal | `cold-start-a0-n1-semantics` |
| 2 | A0′: reversible mechanics, probe-separable frontier, scored on revisions | ✅ 228/228 on 47 % coverage; seeded repair control passes | `cold-start-a0-n2-a0prime` |
| 3 | responsibility-complete concept accounts | ✅ Button −17→−5, Door −13→−1, both `mandatory` | `cold-start-a0-n3-concept-account` |
| 4 | connect Fast Downward, re-run M4 | ⚠️ **half** — the code path is verified, the planner could not be built | `cold-start-a0-n4-fd-path` |

```bash
cd cold-start-a0 && python -m prime.run_prime   # A0-prime, both runs
cd cold-start-a0 && python -m pytest            # 44 passed
```

### A0′ headline

| | A0 | A0′ |
|---|---|---|
| state-action coverage | 99 % | **47 %** |
| accuracy vs ground truth | 98.73 % | **100 %** |
| executable probes | 0 | **13** |

**Reversibility beats coverage.** A0's latch capped what any amount of
exploration could establish; A0′'s toggle did not. Full diagnosis:
`prime/A0P_REPORT.md`.

### The Fast Downward blocker (stopping rule invoked)

Three attempts at a C++ compiler, all failed — Lean's bundled clang has no libc++
headers; `conda install m2w64-toolchain` dies on a `setuptools` RemoveError;
winlibs/mingw-builds direct URLs 404 and the GitHub API is rate-limited from this
host. `cmake` and `ninja` are installed and `aibasel/downward` is cloned to
`.toolchain/downward`; **only the compiler is missing.** Recorded per the
ticket's stopping rule and left for human intervention (D-A0-018).

Delivered instead: `certify/fd_conformance.py` drives `fd_adapter`'s FD code path
end to end against a stand-in that speaks FD's CLI and plan-file protocol —
discovery, invocation, `sas_plan` parsing, independent validation — and confirms
`solve()` picks FD with no `prefer=` hint and returns the same optimal 12-step
plan. **It establishes nothing about Fast Downward's own search**, and says so
everywhere it is reported.

---

## The original six milestones (2026-07-28)

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
cd cold-start-a0 && python -m pytest      # 44 passed (26 at the m6 tag)
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

**~~The frame axiom is not in the DSL.~~ CLOSED by follow-up 1.** It is now a
declared `semantics:` section that every manual here carries and that
`compile_a0.py` refuses to default (D-A0-014); the extension request for the
frozen grammar is `proposals/dsl_grammar_v0.2_semantics.md`. The rest of the
expressivity ledger stands, and E-02 got *worse*: with no `?dir` lifting, A0′'s
two-rule toggle costs sixteen clauses.

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
