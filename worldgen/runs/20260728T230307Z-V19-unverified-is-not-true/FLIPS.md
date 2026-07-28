# V19 — the regeneration, per file

Work order item 2: rebuild all thirty-five `worldgen/out/**/ground_truth.json`
and report how many flipped from `invariants_all_hold: true` to something else,
**listing each**. "Zero is also a number to report."

The answer is **13, and then 0**, and reporting only one of those would be a
lie by selection. Both are below, with the artefacts that produced them.

Nothing here was edited by hand. Every file was rewritten by
`python -m worldgen.build`; the diff is in git and
`python -m worldgen.build --check` reproduces it byte-for-byte in a fresh
interpreter at a different `PYTHONHASHSEED`.

---

## Stage 1 — the three-state alone: **13 of 35 flipped `true` → `false`**

Source state: `core/truth.py` and `build.py` carry the three-class partition and
the separate `invariant_unverified` gate. No new checks exist yet. This is the
work order's four items applied literally and nothing more.

Console: `evidence/01-stage1-threestate-build.txt` (exit **1**)
Census: `evidence/02-stage1-flip-census.txt`

| # | world | was | became | the unverified claim(s) |
|---|---|---|---|---|
| 1 | `t1-fragile-bridge` | true | false | `tile_state_is_monotone` |
| 2 | `t1-switch-latch` | true | false | `latch_monotone` |
| 3 | `t1-tokens-lock` | true | false | `collection_is_monotone` |
| 4 | `t2-cycler-lock` | true | false | `collection_is_monotone` |
| 5 | `t2-lock-fragile` | true | false | `collection_is_monotone`, `tile_state_is_monotone` |
| 6 | `t3-cycler-portal-lock` | true | false | `collection_is_monotone` |
| 7 | `t3-gravity-fragile` | true | false | `tile_state_is_monotone` |
| 8 | `t3-latch-maze` | true | false | `latch_monotone`, `collection_is_monotone`, `tile_state_is_monotone` |
| 9 | `v-29ace70e` | true | false | `collection_is_monotone` |
| 10 | `v-379c937f` | true | false | `latch_monotone` |
| 11 | `v-bd2babb4` | true | false | `collection_is_monotone` |
| 12 | `v-d2c2b1b9` | true | false | `latch_monotone` |
| 13 | `v-efe43df1` | true | false | `latch_monotone` |

The remaining 22 stayed `true` with empty `unverified` and `violated` lists.
**Zero worlds had a genuinely violated invariant, before or after.** The entire
finding is unverified claims counted as satisfied ones.

The 13 are exactly the 13 the census found before any code changed, and the
three claims are exactly the three that `mechanisms/` declared with
`"check": None` — so the flip set is not a surprise, it is the predicted set
arriving. That is the correct outcome for a defect this well characterised, and
it would have been a warning sign if the number had been different.

### What that build did

`evidence/01` ends:

```
BUILD GATE FAILED:
  t1-fragile-bridge        a declared invariant ships unverified — ... (invariant_unverified)
  ... 13 lines ...
BUILD_EXIT=1
```

Thirteen worlds could no longer ship. **That is the real cost of the honest
boolean, and it is the reason stage 2 exists.**

---

## Stage 2 — verify the claims instead of waiving the gate: **0 of 35 flip**

There were two ways out of a red catalogue, and only one of them is honest:

* waive the gate for the three known claims — which is the V19 disease
  relocated, a default pointing at the good news wearing an allowlist;
* **exercise the claims.** All three are monotonicity properties: they relate
  two states, and `check(world, state)` sees one. The mechanism modules said so
  in their own comments and were right. What was missing was a seam for a
  transition-level predicate, so `check_invariants` grew one —
  `edge_check(world, prev, action, next)`, run over the whole reachable graph.

Console: `evidence/03-stage2-edgecheck-build.txt` (exit **0**)
Census: `evidence/04-stage2-flip-census.txt`

| world | claim | verdict | evidence |
|---|---|---|---|
| `t1-switch-latch` | `latch_monotone` | holds | 104 transitions |
| `t3-latch-maze` | `latch_monotone` | holds | 1744 transitions |
| `t3-latch-maze` | `collection_is_monotone` | holds | 1744 transitions |
| `t3-latch-maze` | `tile_state_is_monotone` | holds | 1744 transitions |
| ... | ... | holds | see each `ground_truth.json` |

Every one of the 13 returned to `invariants_all_hold: true` **on a measured
transition count**, not on a default. The `GROUND_TRUTH.md` line changed from

```
* **latch_monotone** — ...  _(prose only, unverified)_
```

to

```
* **latch_monotone** — ...  _(checked on 104 transitions: holds)_
```

so the human-readable half moved with the machine-read half, in the same
direction, which is the property the whole cell is about.

## Reading the two numbers honestly

**"0 flips in the final tree" is not evidence that nothing was wrong.** It is
the arithmetic of two changes that happen to cancel on one boolean, and anyone
who quotes it alone has been misled. The load-bearing statement is:

> 13 of 35 shipped `ground_truth.json` files asserted a claim that no code had
> ever exercised. All 13 have now been exercised. None of them was false.

The last sentence is a fact about this catalogue and not a fact about the
method: `evidence/05-negative-controls-raw.txt` shows a genuinely violated
invariant going red through the same path, so "none was false" is a measurement
and not a limitation of the measuring instrument.

**What would have made the final number non-zero:** any of the three
monotonicity claims actually failing on the reachable graph. Two of the three
`edge_check`s deliberately verify *both* clauses of their sentence (`collection
is monotone` **and** "a lock that has opened never closes"; `tile state rises`
**and** "a collapsed tile is never crossed again") rather than the easy first
clause alone, precisely so that the verdict is not cheaper than the prose it
summarises.

## Also regenerated

`out/worlds/INDEX.json` and `out/worlds/MUTATIONS.json`: **additive only**,
41 and 31 inserted lines, no deletions. The new keys are
`invariants_violated` / `invariants_unverified` per row and
`invariant_unverified` in `totals`. `claims_now_false` — which
`exam/grading/rubrics_adaptation.py` and `exam/papers/adaptation.py` read by
name, in another track's territory — is byte-identical everywhere.

## Not V19's dirt

`python -m worldgen.verify` rewrote eighteen committed artefacts under
`out/qc/` and created one untracked file. That is the side effect cell V12
measured and registered. QC reads only `raw_trace.jsonl`
(`qc/run_qc.py:81,170`), and V19 modified no `raw_trace.jsonl`, `spec.json`,
`coverage.json` or `reversibility.json` — so none of it is attributable here.
Recorded in `evidence/08-qc-side-effect-not-ours.txt` and reverted, not fixed.
