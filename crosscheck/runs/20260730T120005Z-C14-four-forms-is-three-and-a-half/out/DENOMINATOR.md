# Is 303 the right denominator?

`0 of 303` is only as good as the 303. An independent audit was run against the
census's population (`dsl_files()`), specifically to find the slicing that would
make the number look better. **None exists.** The numerator is 0 under every
slicing tried, including every one chosen to flatter the generator.

## Provenance of the 59 DSL files

All 59 are git-tracked; nothing untracked or gitignored entered the corpus.
Outcomes: 34 `compiled`, 3 `refused`, 22 `not-a-theory` (20 of those are
playbooks, which owe no PDDL action and correctly contribute 0).

| class | files | actions | good |
|---|---|---|---|
| canonical hand-authored theory (`*/theory/`, `*/prime/theory/`) | 19 | 165 | **0** |
| run artefact / snapshot (`runs/`, `artifacts/`, `packs/`, `snapshots/`) | 26 | 102 | **0** |
| handover-package copy (`handover_packages/`, `handover_bundles/`) | 6 | 13 | **0** |
| theory-compiler test fixture (`tests/fixtures/`) | 8 | 23 | **0** |
| **total** | **59** | **303** | **0** |

**Unit check.** A hostile reviewer's first shot is that the census compares
lifted schemas against grounded rules. It does not: `gen_pddl` emits exactly one
lifted `:action` per DSL rule, and `n_rules == len(actions)` holds for all 34
compiled files. Counting the 3 refused files by their `n_rules` (18) is therefore
apples-to-apples.

## Duplication — 303 is an inflated ceiling

16 sha256 collision groups. **61 of 303 actions (20.1%) are byte-identical
copies**; deduplicated the corpus is 41 files / 242 actions. The largest:

| actions | copies | files |
|---|---|---|
| 20 | 2 | `cold-start-a3/theory/domain.dsl` ≡ `…/packs/a3-v1/domain.dsl` |
| 12 | 2 | `cold-start-a3/theory/push/domain.dsl` ≡ `…/packs/push-v1/domain.dsl` |
| 7 | 2 | `cold-start-a0/theory/theory.dsl` ≡ `theory-compiler/handover_packages/a0-cart/manual/MANUAL.dsl` |
| 3 | 3 | theoria-arm rev08 ≡ rev09 ≡ `books/theory.dsl` |

The `theoria-arm/…g50t-first-contact` snapshot lineage is **one book counted nine
times**: 9 files, 4 distinct hashes, 29 actions collapsing to 13 distinct.

## Denominator table

| slicing | files | actions | GOOD |
|---|---|---|---|
| all `.dsl` in repo (**the headline**) | 59 | **303** | **0** |
| deduplicated by sha256 | 41 | 242 | **0** |
| excluding theory-compiler test fixtures | 51 | 280 | **0** |
| canonical hand-authored theories only | 19 | 165 | **0** |
| dedup + canonical + no tests | 15 | 133 | **0** |
| compiled files only (refusals folded out — the flattering slice) | 34 | 285 | **0** |
| dedup + compiled only | 26 | 230 | **0** |
| theory-compiler/ contribution alone | 11 | 36 | **0** |
| **narrowest defensible** (one latest file per distinct world) | 10 | **115** | **0** |
| domains Fast Downward accepted | 7 | 21 | **0** |
| FD-accepted **and** goal `stated` | 0 | 0 | **0** |
| best single file in the repo | 1 | — | **0** |

**The maximum GOOD over any single file in the corpus is 0.** No slicing rescues it.

This is not a knife-edge result. Of 285 compiled actions, 152 fail on
`empty-effect` alone, 49 on `undeclared-variable` alone, 37 on
`undeclared-predicate` alone, 38 on empty-precondition *and* empty-effect.
Relaxing any single criterion leaves the other three biting; exactly one action
in the whole corpus fails on a combination that a single relaxation would clear.

## The two refused fixtures are evidence *for* the finding, not contaminants

`theory-compiler/tests/fixtures/countlock_theory.dsl` (6 rules) and
`sokoban2_theory.dsl` (6 rules) are the files `generate_pddl` refuses outright.
Neither is broken: `tests/test_count_guard.py` compiles countlock to **Python**
and executes it, and `tests/test_writes.py::TestSokoban2Fixture` compiles
sokoban2 to Python and asserts 24 grounded rules. So the DSL expresses them and
other backends handle them — PDDL alone cannot. Folding them out of the
denominator is precisely how a 3-of-4 is made to read as a 4-of-4.

Only one DSL file in the repo is an intentionally-malformed negative fixture
(`playbook_violation.dsl`, header: *"违规样本: 含有字面动作序列, 解析器必须拒绝"*),
and it contributes 0 actions, so it distorts nothing.

## Two disclosed defects in the denominator

**1. Fixed — the corpus used to depend on which checkout you ran from.**
`SKIP_DIRS` excluded `.worktrees` (the CLAUDE.md convention) but not the agent
harness's `.claude/worktrees/`. Run from a worktree the census saw 59 DSL files;
run from the main checkout it saw **237**, because four nested agent checkouts
each carry a full copy of the corpus. A census whose population changes with the
caller's cwd is not a measurement. `SKIP_DIRS` now also excludes `worktrees` and
`.claude`, both checkouts yield 59, and `c14_verify.py` pins it: it recomputes
the corpus with `REPO` pointed at the main checkout and fails on any difference.
The headline numbers are unchanged by the fix.

**2. Not fixed, disclosed — the census slightly UNDER-counts.**
`exam/handover_bundles/tier1_manual/MANUAL.dsl` and
`tier2_manual_playbook/MANUAL.dsl` (byte-identical) are genuine manuals with
`word_table:`, `events:`, `rules:` (5 rules), `goal:` and `laws:`, but
`parse_theory` rejects them for a missing `semantics:` section, so they land in
`not-a-theory` and contribute 0. On a reading where "expressible" means "an
author wrote rules in it" rather than "the front end accepts it", the honest
denominator is **313, not 303** (247 deduplicated). It is left at 303 because the
census's documented population is *what `gen_pddl`'s own front end sees*, and
that choice is stated rather than silently taken. Either way the extra 5–10
actions are all defective and the numerator stays 0.

Neither defect moves the numerator in any direction.

## Verdict

303 is an honest but duplicate-inflated ceiling. The defensible figures are
**242 deduplicated, 133–165 canonical, 115 at the narrowest**. Good is **0** at
every one of them, so the paper may quote whichever denominator it prefers — the
claim does not rest on the choice.
