# Two adversarial passes over C13, and what they changed

Both were told to refute, not to review, and both were read-only on the repo.
This file records what they found, what was verified independently before being
believed, and what was changed as a result. The headline: **one pass could not
break the reader's soundness and did break its test battery**; the other
**confirmed the premise correction with stronger evidence than I had**.

---

## Pass 1 — attack the reader

**The claim put to it.** `pagoda_reader.check(document) == []` entitles you to
conclude that no state in `goal_states` is reachable from `initial_state` under
the 1-D peg jump relation on `n_pos` cells.

**Result: not broken.** It reduced the search space (a document accepted at
bound `b` is accepted at the tightest bound, since `b >= pot(s₀)` and
`pot(g) > b` give `pot(g) > pot(s₀)`) and then enumerated:

| board | pagoda weight vectors in `[-4,4]ⁿ` | accepted `(initial, goal)` pairs | unsound |
|---|---|---|---|
| n=3 | 185 | 4,576 | **0** |
| n=4 | 375 | 40,070 | **0** |
| n=5 | 1,521 | 680,006 | **0** |
| n=6 | 5,256 | 9,658,037 | **0** |

~10.4M accepted pairs, each cross-checked against `peg1d.reachable_from`; plus
200,000 randomised documents with adversarial bounds, no disagreement. It also
confirmed `jump_moves(n)` is set-equal to `peg1d.move_instances(n)` for
n = 3..40 — the deliberate duplication is faithful — and that the reflexive case
`goal_states == [initial_state]` is refused. Type confusion was closed:
`bool`, floats, `NaN`/`Infinity` (which `json.load` accepts by default),
fullwidth digits, `n_pos != len(initial_state)`, and `10**400`-scale weights all
behave.

**What it did break: the tests.** Four findings, all real, all fixed.

1. **Three independence tests passed a backdoored reader.** With
   `import engines` indented one level inside `check()` and the producer field
   reached as `document['obligations']` — single quotes — the scan saw nothing,
   because it matched on the *unstripped* line and counted only double-quoted
   names. Fixed: strip before matching, count quote-agnostically, and refuse
   `importlib` / `__import__` outright. Re-checked here against a reconstructed
   backdoor: old scan `True` / new scan `False` on both holes, both still `True`
   on the real file.
2. **The `goal_break` boundary was unpinned.** Mutating `value <= bound` to
   `value < bound` passed all 23 tests, because every negative sample used a
   goal strictly under the bound. That mutant is not cosmetic — it issues
   thousands of accepted-but-reachable documents, worst case a 6-cell board with
   the goal four jumps away at potential exactly equal to the bound. Fixed by
   `test_a_goal_whose_potential_equals_the_bound_is_rejected`.
3. **`second_opinion` was never exercised in the direction that matters.** Every
   assertion ran on certificates whose goals are unreachable, so both a stub
   answering `False` always and one doing no search at all survived. Fixed by
   `test_the_second_opinion_tracks_real_reachability`.
4. **A crash and a refusal shared exit code 1.** `main` ran the reachability
   cross-check *before* looking at the rejections, on documents `check` had
   already condemned, so five malformed inputs raised and exited 1 — identical,
   to a caller reading the exit code, with "this certificate is refuted". Fixed:
   `check` returns rather than raises on a non-dict, `main` reports `MALFORMED`
   with exit 2, and the cross-check moved below the early return.

**The finding that improved the argument, not just the tests.** The original
forgery breaks the proof of a claim that is *true* — `01000` really is
unreachable from `11011`. The pass built the missing case: weights
`[-4, -4, 4, 0, 4]`, initial `11011`, bound `-4`, goal `00111`. Exactly one jump
raises the potential, `jump(0,1,2)` by 12 — and that jump is legal in `11011`
and lands on the goal. Delete its witness and `certificate_export.verify()`
returns clean **on a document whose conclusion is false**.

Verified here before adopting, rather than taken on report:

```
pot(11011) = -4    pot(00111) = 8
  jump(0,1,2) delta=12   <- the only violation, and the only deleted witness
  jump(1,2,3) delta=0    jump(2,1,0) delta=-4   jump(2,3,4) delta=0
  jump(3,2,1) delta=-8   jump(4,3,2) delta=0
'00111' in peg1d.reachable_from('11011'): True
```

So the gap `certificate_export.verify()` leaves is not "an unproven true claim"
but a certified falsehood. Adopted as
`test_the_producer_certifies_a_falsehood_and_the_reader_refuses_it` and as a
check in the acceptance script; the document is on disk as
`forged_falsehood.cert.json`.

**Declined, with reasons.** F6 (memory: ~64× amplification, 322 MB peak at
`n_pos = 10⁶`) is real but linear, bounded, and behind a structural check that
makes the attacker pay ~5 bytes per cell; this reader adjudicates a partner
track's committed artefacts, not hostile uploads, and a generator refactor buys
less than the churn costs. Recorded here rather than fixed. F7 (misleading
messages for tuple-instead-of-list) *was* fixed — a correct refusal with a wrong
reason is worse than it sounds for a tool whose output a human acts on.

### Mutation check, run here

Every mutant the pass named, plus the one that matters most, now dies:

| mutant | outcome |
|---|---|
| `goal_break`: `value <= bound` → `value < bound` | `test_a_goal_whose_potential_equals_the_bound_is_rejected` fails |
| `second_opinion` always answers "not reachable" | 2 tests fail |
| `inv_closed` iterates the document's witness list instead of grounding | 3 tests fail, including both forgeries |

`interop/pagoda_reader.py` was restored byte-identically after each
(`diff -q` clean).

---

## Pass 2 — attack the premise correction

**The claim put to it.** That the item's premise is stale: `probe_a1_state`
reports `green`, not `partial`, and `consumed` is true.

**Result: confirmed, with three pieces of evidence I did not have.**

1. **The live production artefact.** `monitor/state.json`, written by the
   running monitor loop at `2026-07-30T03:49:34Z`, already recorded
   `a1_state: green` — **44 minutes before the item was written** (item mtime
   `04:33:50Z`, claimed `04:34:49Z` per `monitor/board/board.log:380`). The
   dashboard the author would have read said green. My own runs of the probe
   were merely reproductions of what production had already published.
2. **`consumed` has never been false in any recorded artefact.** Every cached
   `partial` snapshot back to 2026-07-29T00:09 carries 「theory-compiler 侧
   消费：已接」 in its own detail string. The `partial` came *entirely* from the
   discarded-boolean bug, never from an unconsumed bridge.
3. **The S26 timeline is tighter than I stated.** The fix is `65e38584`
   (2026-07-29 14:16 +0800), merged at `b354c64a` (14:27) — 22 hours before the
   item. Its commit message says outright: "The live verdict is green, and is
   now true rather than unconditional."

**And it corrected me on something I had left vague.** I had treated the item's
「网格 C4 至今是 0%」 as probably related. It is not. `monitor/spec.py:1182-1198`:
`GRID_COLS` column 4 is 正式战役, so C4 is *编译与证明 × the live campaign* —
「封存局的证书生产线」 — a **hand-written** constant gated on Phase 3, fed by no
probe, movable by no engine-rig work. The item's own sentence is
self-contradictory: it calls C4 one of columns 1–2's gaps while C4 is in column
4, and no cell in columns 1–2 is at 0%. Most likely a token collision on "C4"
(there are two other unrelated `C4`s in `spec.py`). **Neither this item nor any
successor can move that number**, which is worth saying plainly to whoever
grades it. My inbox note asks the monitor to adjudicate rather than asserting
this as settled, since `monitor/spec.py` is not my territory.

**Where it says the real gap is.** Reversed from the item: the half genuinely
missing is **engine-rig's `ic3_pdr` emitter**, for which theory-compiler's
consumer and contract have waited since 2026-07-29T06:00Z. That is the proposal
already filed in `monitor/inbox/`.

**One correction it offered that I did not take.** It judged tasks 1 and 4
"already exist in substance" across `tests/test_interop.py` and theory-compiler's
reader, and task 3 "already done by the other track". Half right, and the half
it misses is the whole point: `test_interop.py` checks with the producer's own
module, `recheck` refuses the exchange document at load (exit 2, by design), and
theory-compiler's reader is on the far side of the boundary — this rig had
nothing that loaded its own exchange artefact and adjudicated it. The two
forgeries above are the evidence that the difference is not academic. Task 3 is
also not substitutable: their paragraph reports their half; ours reports ours,
and carries the contract. **Scope was not reduced on this advice.**
