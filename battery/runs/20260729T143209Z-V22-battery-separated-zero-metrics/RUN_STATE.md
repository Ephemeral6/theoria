# RUN_STATE — V22-battery-separated-zero-metrics

Worker W-1671, cell V3, territory `battery`, branch
`agent/v22-battery-separated-zero-metrics`, base `b60a1537`.
Zero API calls, zero model calls, zero network, $0.00, zero sealed-pile
contact. The battery was **not** re-run to produce any finding; every number is
read out of committed artefacts, as the work item required.

## What was asked, and what landed

| # | asked | landed |
|---|---|---|
| 1 | diagnose the three failure classes apart | `DIAGNOSIS.md` §1–§3 |
| 2 | say per-metric what is fixable and what this design cannot measure | `DIAGNOSIS.md` §1 (five root causes; **0 of 23 fixable by rerun**) |
| 3 | the minimal next experiment, as one executable sentence | `DIAGNOSIS.md` §5 |
| 4 | STATUS.md + METRICS.md state separation power 0, with paper wording | `battery/STATUS.md` W-13; `battery/METRICS.md` "Process 1" (generated) |

## The finding that reframes the item

**The zero is a ceiling the design fixes in advance, not a measurement.**
`audit/discriminate.py:120` tests `min_attainable_p > 0.05` before it consults
any effect size, and `audit/stats.py:166` puts that at `2/2**n`. Six non-tied
paired games are needed; the development pile has four. So `discriminating` is
unreachable for all 38 metrics regardless of the data, and rerunning the
identical pass is guaranteed to return 0 again. The monitor's earlier 60% for
this cell was scoring a cell whose maximum attainable score was 0.

## How METRICS.md was changed without hand-editing a generated file

`METRICS.md` carries "Do not edit by hand" and `tests/test_docs.py` fails if it
drifts from the registry. The new "Process 1" section is therefore **generated**
— `battery/docs.py::_discrimination` reads `artifacts/discrimination_arms.json`
and derives the tally, the denominator and the threshold. Nothing about the
result is asserted in prose that the artefact does not carry, and
`_sign_test_games_needed` recomputes the 6 from the same formula
`audit/stats.py` uses rather than hard-coding it.

## The fourth verify rung, and why it flips

`verify.py` gained `rung_separation_claim`. Rungs 1–3 were green throughout the
period when this cell was being reported as 60%, and would have stayed green:
**none of them reads a sentence.** The new rung checks the committed documents
against the committed artefact, and its third check **changes direction with the
data** — the moment a metric pairs enough games for p<0.05 to be attainable, the
"unreachable" paragraph becomes false and the gate goes red until someone
rewrites it. A gate that could only catch the claim drifting too high would let
it rot the other way.

## What the adversarial review changed

It was told to refute, and it did. Eleven findings; I verified each against the
artefacts before acting, and adopted nine. The three that changed the
deliverable materially:

1. **The recommendation was unsafe as written.** I had nominated E4, P1, P2, X1
   and X4 for a 12–17-game confirmation on the strength of their cross-arm
   effect sizes. Checked across both gradients: **only E4 keeps its sign.** P1
   goes +1.000 → −0.750 *with a wrong-direction warning*, P2 → 0.000, X1 →
   +0.333, X4 → +0.111. A sign flip between the two passes is the signature of
   the harness confound the artefact's own `confounds` list names, and the
   ladder is the pass that controls it. The nomination is now **E4 and P3**
   (the two that hold their sign), and the executable sentence carries the
   "keeps its sign on both gradients" clause explicitly.
2. **I missed `tier` entirely, and it is the more binding limit.** All 8
   metrics in the honest denominator are `reference`, which the battery's own
   rule bars from ordering claims — and the **main table is empty (0 of 38)**
   after B17. So the set that is both eligible for the gradient and admissible
   for an ordering claim is empty, **and would stay empty if the pile were
   large enough to power the test.** Unlike the power ceiling, more games does
   not fix it. This is now in `METRICS.md` (generated from `tier_of`) and W-13.
   The reviewer read the committed `gaming_audit.json` and concluded "one
   main-tier metric (P3) has paired data"; that artefact is **stale** — it
   still lists 9 main-tier metrics and disagrees with the code on all nine,
   while a fresh recompute yields `main = []`. Logged as provenance drift.
3. **My group-4 reasoning was wrong even though its conclusion held.** I wrote
   "neither control arm has a theory and neither can be given one," justified
   by the Schema arm being unrunnable. Both halves fail: the corpus ships
   `world_model_v5.py` × 8, 60 level snapshots and up to 40 `cand*.py`
   candidate models, and you need not re-run anything to parse committed
   Python — `schema_traces.py:294-298` *declines* to build a `Theory`, as a
   stated decision. The corrected reason is one-sided and sharper: **`bare_cc`
   is the side that cannot have a theory**, so even a full Theory adapter for
   the Schema arm leaves all 14 at `no-data` (n_high 4, n_low 0, shared 0).

Smaller corrections adopted: `min_attainable_p` is 0.125 *at best* and 0.25 for
P3/X2/X3, which tie a pair (my §0 contradicted my §2); M3 is `not-applicable`
on 89 of 95 runs and `insufficient-data` on 6, not "insufficient-data on all
95"; the power branch is guarded by `p_value is not None` and `delta` *is* read
just above it, so "fires unconditionally" was wrong (the all-ties path lands in
`no-effect` because δ is provably 0 — which strengthens the claim); the 8
`denied_unknown_files` are repository furniture, not cross-game aggregates; the
$1.11 cost figure was unsourced and is now $1.1707/cell from
`unit_prices.json`; `prompt_chars` is the one *metric-relevant* unlisted field,
not the only unlisted field. A dangling citation to a `NOT_RANKED.md` I never
wrote is replaced by the git provenance inline.

**And it found a real bug in my gate** — see the fourth self-report below.

## Self-reports

* **My gate's first draft was nearly vacuous, and its own negative control
  caught it.** The STATUS.md check was `str(n_separating) in section` — i.e.
  `"0" in section` — which `0.125`, `80 run` and most of the prose in the file
  satisfy. It passed on a STATUS.md that never stated the count. Now it
  requires one derived sentence verbatim (`verify.STATUS_CLAIM`), and the cheap
  version is pinned as a failing mutant
  (`test_the_status_check_is_not_satisfied_by_a_stray_digit`). Worth recording
  because the weak check and the real one read as equivalent.
* **My first denominator was wrong and a subagent corrected it.** I wrote "the
  honest denominator is 31" (the rankable metrics). The defensible number is
  **8** — declared direction *and* ≥2 paired games. The correction matters in
  the battery's favour and against it at once: it is a smaller instrument than
  38 suggests, but the `neutral` flag costs the tested denominator only **2**
  metrics (P5, X5), because five of the seven diagnostics had no paired data
  anyway. **The battery is not hiding failures behind `neutral`; it is short of
  material.** Verified per metric before adoption.
* **The anti-staleness flip keyed on the wrong count, and would have fired a
  false positive on the first real pile growth.** `2/2**n` is a function of the
  sign test's **non-tied** `n`, not of `n_paired_games` — and the two already
  differ here (P3, X2, X3 pair four games and score three). A pile that grew to
  exactly six while every metric lost one pair to a tie leaves n=5, floor
  0.0625, still above 0.05: the ceiling paragraph would still be **true** and
  my gate would have gone red demanding it be rewritten. Both `verify.py` and
  `docs.py` now take the count from one shared `_non_tied` helper, and
  `test_paired_games_alone_do_not_trip_the_flip` pins the case. The old test
  could not have caught this: it mutated `n_paired_games` and asserted the
  property the code did not implement — a test and a bug that agreed with each
  other. Found by the adversarial reviewer, not by me.
* **I corrupted `verify.py` with a PowerShell one-liner.** Using
  `Get-Content | Set-Content -Encoding utf8` to renumber the rung labels
  round-tripped the file through the wrong codec: it added a BOM, converted 341
  LF to CRLF (against `battery/.gitattributes`, which pins LF for
  byte-reproducibility) and mangled the one non-ASCII line into
  `"%d 鏉℃寚鏍囬噷 ..."`, leaving an unterminated string literal. Repaired by
  rewriting the literal from code points and normalising back to LF with no
  BOM; verified `BOM: False, CRLF: 0, LF: 502`. The lesson is the boring one:
  use the editing tool for edits, not a shell codec round-trip, on a box whose
  default codepage is cp936.
* **`python battery/verify.py` could not import `battery`.** The file documents
  itself as runnable directly from anywhere, and in that mode the interpreter
  puts `battery/` on the path rather than its parent. Fixed by inserting the
  repo root rather than by restating the threshold locally — a gate holding its
  own copy of the number it exists to check is not a gate.

## Gaps — stated, not smoothed over

* **X2 and X3 are mislabelled `underpowered` and I did not change the code.**
  Neither is power-limited: X2's |δ| = 0.1875 is below the 0.33 gate (flat), and
  X3's δ = −0.5625 with 0/3 pairs agreeing is a large effect **opposite** to its
  declared direction — and it is backwards on the model ladder too (δ = −0.667).
  Reordering `_verdict`'s branches would change published verdicts for metrics
  outside this work item's scope and would be a pre-registration change, not a
  bug fix. Recorded as a gap for whoever owns process 1's verdict ladder.
  `discrimination_arms.json` does already emit X3's `warning` field, so the
  information is present; the *verdict* is what misleads a tally.
* **E7's root cause is "structural" with one unverifiable escape.**
  `prompt_chars` is the only field the schema adapter nulls without listing it
  in `notes["absent_by_construction"]`, and the upstream session transcripts may
  in principle allow a reconstruction. Unverifiable here — the payload is
  gitignored and absent from every worktree — and a reconstructed count would
  not be the same quantity as bare_cc's harness-assembled one. Counted as not
  fixable, with the reasoning exposed rather than hidden in the tally.
* **The committed spectrum is not reproducible from a clean worktree.**
  `capability_spectrum.json`'s `input_digests` names four shard ledgers absent
  here, while 11 `a7-*` shards on disk contribute 17 run_ids that appear nowhere
  in the committed artifact. A recompute today ingests a different run set than
  the committed numbers were built from (this run: 48 runs vs the artifact's
  95). `verify.py`'s `shipped_note` already prints the count difference as a
  note; the *digest* mismatch is not checked by anything. Not V22's territory —
  logged in `DIAGNOSIS.md` §6 so it is not rediscovered a third time.
* **The Schema arm is three models, and `confounds` does not say so.**
  `claude-opus-4-8` on ar25/g50t, `claude-fable-5` on sk48/tn36,
  `gpt-5.6-sol` for the other four runs. The artifact records the harness
  confound and the released-material confound but not this one. Any effect size
  on this gradient is a contrast against a mixture. Logged, not fixed — the
  `confounds` list is process 1's pre-registered text.
* **No fix for the zero is delivered, because none is available inside Phase 2.**
  A fifth non-sealed game does not exist on either arm, and repeats are
  collapsed by `_per_game_mean` before pairing. The deliverable is a correctly
  sized plan (≥6, target 12–17 paired games, pre-registered before Phase 4
  opens the sealed pile), not a result.

## Tests

```
python -m pytest battery -q                                  -> 335 passed
python -m pytest battery/tests/test_verify_separation_claim.py -q -> 16 passed
python battery/verify.py                                     -> exit 0, four rungs
python -m battery.docs                                       -> METRICS.md byte-stable
```

The 16 new tests are negative controls: 8 distinct corruptions of the honest
tree (hand-edited headline, dropped ceiling paragraph, deleted W-13 section,
wrong count, stray-digit near-miss, an arithmetically impossible
`discriminating` verdict, the staleness flip, a missing artefact, an empty
artefact) each must turn the rung red — plus one that must leave it **green**
(`test_paired_games_alone_do_not_trip_the_flip`), because a gate that goes red
on a correct document is as broken as one that stays green on a wrong one. The
gate's ability to go red is the only evidence that it checks anything; its
ability to stay green under the near-miss is the only evidence it checks the
right thing.

## Method

Five subagents with independent contexts: no-data root causes, power analysis,
not-ranked provenance, arm/data inventory, and one adversarial reviewer tasked
with refuting the conclusions rather than confirming them. Every load-bearing
number a subagent reported was re-derived from the artefacts here before it was
written down; the denominator correction above is the case where that mattered.
