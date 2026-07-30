# V22 — the battery separated zero metrics: three failures, diagnosed apart

Prompt id `V22-battery-separated-zero-metrics`, worker W-1671, cell V3.
Source of record: `battery/artifacts/discrimination_arms.json` (gradient
`bare_cc` weaker vs `schema_repro` stronger, paired by game, `control_runs = 88`,
`available = true`). **No rerun of the battery, zero API calls, zero sealed-pile
contact.** Every number below is read out of committed artefacts.

Tally reproduces the 2026-07-29 audit exactly: **0 separating, 8 underpowered,
7 not-ranked, 23 no-data**, over 38 metrics.

---

## 0. The finding that reframes the other three

**The zero is not a measurement. It is a ceiling the design fixes in advance.**

`battery/audit/stats.py:166` sets `min_attainable_p = min(1.0, 2.0 / 2**n)`.
`battery/audit/discriminate.py:120` tests `min_attainable_p > 0.05` **before**
it consults any effect size. So:

```
require 2 / 2**n <= 0.05  <=>  2**n >= 40  <=>  n >= log2(40) = 5.32  <=>  n >= 6
  n = 4 -> 0.125     n = 5 -> 0.0625     n = 6 -> 0.03125  <- first pass
```

The development pile is **4 games** (`arc-recon/data/piles.json`; the other 21
are sealed and must not be played or inspected). Game-level pairing therefore
caps `n` at 4, so `min_attainable_p` is **0.125 at best — and 0.25 for P3, X2
and X3, each of which loses a pair to an exact tie** — and the verdict
`discriminating` is **unreachable for all 38 metrics regardless of what the
data say**.

*Precision, because the loose version invites a rebuttal.* The power branch is
not literally unconditional: it is guarded by `p_value is not None`, and
`delta` is in fact read just above it (`discriminate.py:113-118`) to emit the
wrong-direction warning. The only path reaching the effect-size ladder at n≤4
is an all-ties artefact, where `sign_test` returns `n=0, p_value=None`. That
path cannot yield `discriminating` either: if every pair ties then `highs` and
`lows` are the same multiset, so Cliff's δ is exactly 0 and the verdict is
`no-effect`. The conclusion stands; the word "unconditionally" did not.

Two consequences, and both matter more than the tally:

1. **Rerunning the identical pass on the identical pile is guaranteed to return
   0 again.** "Run it again and get more" is not available.
2. **The wall is the design unit, not the statistic.** Swapping the sign test
   for Wilcoxon signed-rank does not help: 4 pairs give 2^4 = 16 equally likely
   sign patterns, so its smallest two-sided p is also 2/16 = 0.125. Any exact
   permutation test whose exchangeable unit is the game has ≤16 rearrangements
   at n=4 and the same floor.

So the monitor's earlier "60%" for cell V3 was scoring a cell whose maximum
attainable score, under the pass as written, was 0.

---

## 1. `no-data` (23) — how many are collection failures? **Zero.**

The question the work item asks is the right one, and the answer is clean:
**0 of 23 are fixable by re-running collection; 23 of 23 need a changed input
format, a new arm, or a changed metric definition.** No metric here fails
because a run was not done — both arms cover all four development-pile games
(bare_cc 80 runs, schema_repro 8 = 2 collections × 4 games).

The artifact carries its own signature for the split. `no-data` means
`len(shared) < 2`, and the `(n_low_games, n_high_games)` pattern separates the
two shapes:

| pattern | n | metrics | meaning |
|---|---|---|---|
| `(4, 0)` | 5 | E2 E3 E5 E7 X6 | bare_cc scores all four games; the **Schema trace format cannot carry the field** |
| `(0, 0)` | 18 | K1–K6 K8–K10 K12–K14 M1–M5 P4 | **neither arm** can produce the field |

### Five root causes cover all 23

| # | cause | metrics | n | class |
|---|---|---|---|---|
| 1 | No cost field anywhere in the upstream Schema corpus (`adapters/schema_traces.py:226-227`, *"No cost field exists anywhere in this corpus, under any spelling"*); the Codex-side collection carries no token usage at all | E2 E3 E5 | 3 | structural-high |
| 2 | No prompt-size field upstream (`schema_traces.py:230`, `prompt_chars=None`) | E7 | 1 | structural-high* |
| 3 | `Step.failed` has no source in upstream `events.jsonl` and is **deliberately** not synthesised from `dead` (`schema_traces.py:149-150`) — conflating them would hand the Schema arm bare_cc's ~29% API-failure rate | X6 | 1 | structural-high |
| 4 | **`bare_cc` has no explicit theory and no repair record, and cannot be given one** — see the correction below, which narrows this from "neither arm" to "the baseline side" | K1–K6 K8–K10 K14 (theory, 10); K12 K13 M4 M5 (repairs, 4) | 14 | structural-low |
| 5 | **No ground truth exists for ARC dev games** — no hand-written mechanism annotation, no known shortest plan (`schema_traces.py:274-275`) | M1 M2 P4 | 3 | structural-both |
|  | …plus M3, which has cause 5 **and** an unimplemented body: `metrics/mechanism.py:81-84`. It is `not-applicable` on 89 of the 95 runs and `insufficient-data` on the remaining 6 — the stub is reached on 6 runs, not on all 95 | M3 | 1 | stub |

\* E7 is the single borderline case and is recorded as such rather than
smoothed over. `prompt_chars` is the one *metric-relevant* field the adapter
leaves `None` without listing it in `notes["absent_by_construction"]`
(`step_idx`, `duration_ms` and `attempt` are also unlisted, but nothing in the
registry reads them), and the Claude-side
session transcript may in principle allow a char count to be reconstructed. Two
reasons it is not counted as fixable: the payload is gitignored and absent from
any worktree, so the claim is unverifiable here; and a transcript-reconstructed
char count is **not the same quantity** as bare_cc's harness-assembled
`prompt_chars`, so pairing them would contrast two different measurements.

### The honest conclusion for group 4 — corrected, and still a real result

My first draft said *"neither control arm has a theory, and neither can be
given one,"* and justified it with the fact that the Schema side cannot be
re-run (`baseline-arms/SCHEMA_PATH_A.md:168`, the official harness code was
never published). **Adversarial review refuted both halves, and it was right.**

The Schema corpus **does** ship explicit world models. Counted from the tracked
`baseline-arms/schema_traces/MANIFEST.json` (165 admitted dev-pile files):

* `world_model_v5.py` × 8 — one per run;
* `snapshots/cleared_level_{0..7}.py` × 60 — a versioned world-model ladder;
* `planner.py`, `planner2.py`, `wm_candidate.py`, `world_model_full.py`,
  `notes.md`, and in one run **40 numbered `cand*.py` candidate world models**.

And "cannot be re-run" was a non-sequitur: you do not need to re-run anything
to parse committed Python. What `schema_traces.py:294-298` actually does is
**decline** to build a `Theory` from that source, as a stated decision — *"the
world model in these run directories is Python source and prose; reading it
would be a separate decision with its own contamination argument, and a Theory
assembled from it would not be the one upstream reasoned with."* That is a
judgement, not an impossibility.

**The conclusion survives, but the reason is one-sided and that is the more
precise finding.** Pairing needs *both* sides, and the side that cannot supply
a theory is **`bare_cc`** — a one-shot CLI baseline whose world model lives in
weights, with no manual to be refuted and no repair loop to record
(`adapters/ledger_jsonl.py:245-266` passes no `theory=`). So even a complete
Theory adapter for the Schema arm would leave all 14 at `no-data`: `n_high`
would rise to 4 and `n_low` would stay 0, giving 0 shared games.

The design finding is therefore sharper than I first wrote it. Process 1 as
`Theoria.md` specifies it — *validate on the control arms only* —
**structurally cannot validate the metrics that measure the thing Theoria is
for**, because the property being measured is precisely what makes an arm not a
control. Fourteen metrics, the largest single block in the tally, and no
amount of upstream material fixes it. That is the work item's *"this quantity
is not measurable on the current arm set"* verdict, earned rather than assumed.

---

## 2. `underpowered` (8) — how much more would it take?

All eight have `n_paired_games = 4`; three lose a pair to an exact tie (P3, X2,
X3 → n=3, floor 0.25).

| metric | dir | Cliff's δ | magnitude | agrees? | non-tied n | pairs agreeing | observed p | verdict **if power sufficed** |
|---|---|---|---|---|---|---|---|---|
| E4 | lower | −0.875 | large | yes | 4 | 4/4 | 0.125 | **discriminating** |
| P1 | higher | +1.000 | large | yes | 4 | 4/4 | 0.125 | **discriminating** |
| P2 | higher | +1.000 | large | yes | 4 | 4/4 | 0.125 | **discriminating** |
| P3 | lower | −0.375 | medium | yes | 3 | 2/3 | 1.000 | discriminating (barely; 0.375 vs the 0.33 gate) |
| X1 | lower | −0.625 | large | yes | 4 | 4/4 | 0.125 | **discriminating** |
| X2 | higher | −0.1875 | small | **no** | 3 | 1/3 | 1.000 | `no-effect` |
| X3 | higher | −0.5625 | large | **no** | 3 | 0/3 | 0.250 | `wrong-direction` |
| X4 | lower | −0.625 | large | yes | 4 | 4/4 | 0.125 | **discriminating** |

### "To separate, n = ?"

`N_min` for a *perfect* split is **6** non-tied paired games (arithmetic in §0).
A perfect split is an optimistic assumption, so the realistic sizing uses the
observed per-pair agreement with shrinkage (exact binomial, α=0.05 two-sided,
80% power):

| per-pair success p | first n at ≥80% power | stable from |
|---|---|---|
| 1.00 | 6 | 6 |
| 0.90 (Jeffreys on 4/4) | 12 | 12 |
| 0.833 (Laplace on 4/4) | 17 | 17 |
| 0.80 | 20 | 23 (power dips at 21–22 as the critical k steps) |
| 0.667 (P3, X2) | 72 | 77 |

Per metric, tie-inflated where a tie was observed:

* **E4, P1, P2, X1, X4** — 4/4 agreement, large clean effects: **6 games** at
  the optimistic p=1.0, **12** at Jeffreys-shrunk p=0.90, **17** at p=0.833.
  **But see the cross-gradient check below before nominating any of them.**
* **X3** — separates strongly *backwards*: **6–22 games**, and what that would
  buy is confirmation that the metric is broken, not that it works.
* **P3, X2** — marginal / flat: **72 optimistic, 125–199 shrunk, ~167
  tie-inflated**. These are not power problems that a slightly bigger pile
  fixes.

### Cross-gradient check — four of the five "clean" metrics disagree with themselves

The two passes are independent gradients over the same metrics, so a metric
that separates one way on one and the other way on the other is telling us
something the effect size alone does not. Verified across both artefacts:

| metric | cross-arm δ (agrees?) | ladder δ (agrees?) | ladder warning |
|---|---|---|---|
| **E4** | −0.875 ✔ | −0.500 ✔ | — |
| P1 | +1.000 ✔ | **−0.750 ✘** | **yes** |
| P2 | +1.000 ✔ | **0.000 ✘** | — |
| X1 | −0.625 ✔ | **+0.333 ✘** | — |
| X4 | −0.625 ✔ | **+0.111 ✘** | — |
| P3 | −0.375 ✔ | −0.333 ✔ | — |
| X3 | −0.5625 ✘ | −0.667 ✘ | yes |

**Only E4 and P3 are correctly signed on both gradients.** P1 is the sharpest
case: a *maximal* +1.000 on the cross-arm pass and a warning-triggering −0.750
on the ladder. A sign flip between gradients is exactly the signature of the
harness/plumbing confound the artefact's own `confounds` list names — the
cross-arm pass bundles capability with plumbing, the ladder holds the harness
fixed, and where they disagree the ladder is the one controlling the confound.

**This corrects my own §5 recommendation.** Nominating P1, X1 and X4 for a
12–17-game confirmation on the strength of their cross-arm effect alone would
have been unsafe advice: three of the four nominees disagree with themselves
across the two passes, and one of them trips a wrong-direction warning on the
gradient that controls the confound. **The nomination is E4 alone** — and E4 is
`reference` tier, so even confirming it licenses no ordering claim.

### A defect the gate ordering hides

Because `min_attainable_p > 0.05` is tested *first*, **X2 and X3 are labelled
`underpowered` when neither is power-limited**. X2's effect is 0.1875 — below
the 0.33 medium threshold, i.e. genuinely flat, a conclusion that does not
depend on n. X3's is −0.5625 with 0/3 pairs agreeing — a large effect in the
**opposite direction to its declared one**, which is the single most
informative thing this pass can find. The artifact does emit X3's
`warning` field (verified: *"separates the gradient strongly (|d| = 0.562) but
in the opposite direction… Do not use until resolved"*), so the information is
not lost — but the *verdict* reads `underpowered`, and anyone tallying verdicts
(as the audit and the monitor both did) will file two power-independent results
under "we need more data". Recorded as a gap; see `RUN_STATE.md`.

---

## 3. `not-ranked` (7) — never candidates in the first place

`discriminate.py:179` assigns `not-ranked` on `card.direction == "neutral"`
alone, **before any data is looked at**. E1, E6, K7, K11, M6, P5, X5 are
declared diagnostics: they describe a run without ranking it. They could not
have separated anything under any amount of data, and counting them in a
denominator of 38 overstates how much the pass had to work with.

**The neutral set was never touched after the data landed.** Checked with
`git log -S'direction="neutral"' -- battery/metrics/`: the flag was set in
exactly two commits, `0be176c0` (v0) and `e82558b1` (v1), both ancestors of
`82a6925f`, which first added `discrimination_arms.json`. No metric was moved
into or out of `neutral` after the gradient data existed, in either direction.
The one weak case is **K11**: `BLINDING.md:52` names the diagnostics as
E1/E6/K7/M6/P5/X5 — K11 is absent from that list — and `epistemic.py:204-212`
makes its neutrality explicitly provisional (*"until the theorize→certify loop
has produced a genuine revision, this number ranks nothing"*). K11 is neutral
because the loop was never exercised, not because the quantity is unrankable.
Moot for this pass — it has no paired data either way.

---

## 4. What the denominator should be — **8**, not 38, and not 31 either

My first pass said 31 (the rankable metrics). That is still too flattering.
The set actually *put to the question* needs a declared direction **and** at
least two paired games; verified against the artifact:

| set | n | metrics |
|---|---|---|
| registered | 38 | — |
| pairing ≥2 games | 10 | E4 P1 P2 P3 **P5** X1 X2 X3 X4 **X5** |
| …of those, rankable → **the honest denominator** | **8** | E4 P1 P2 P3 X1 X2 X3 X4 |

### The limit that outranks all of this: **tier**

Process 1 is not the only gate a metric must pass to carry an ordering claim.
The anti-gaming audit demotes anything an arm could optimise by accident with
no defence implemented, and `METRICS.md`'s own rule is that `reference` metrics
are *excluded from ordering claims*. Checked against the live registry
(`battery.audit.gaming.tier_of`):

```
main-tier metrics: []          # 0 of 38
tier of all 8 in the honest denominator: reference, every one
```

**The main table is empty.** `STATUS.md` B17 records why — the V9 adversarial
review knocked out the last two (E1 to four unintentional attacks, M3 to
`undetermined`). So the set that is both eligible for the specified gradient
*and* admissible for an ordering claim is **empty**, and it would still be
empty if the pile were large enough to power the test. **This is the more
binding of the two limits, and unlike the power ceiling it is not fixed by more
games.** Any reading of §2's effect sizes that reaches for the large clean ones
is reaching for `reference` metrics.

*Provenance note, and it is how this was nearly missed:* the committed
`battery/artifacts/gaming_audit.json` still lists **9** main-tier metrics (E2
E3 K11 K12 K7 M3 M6 P3 P4) and disagrees with the code on all nine. A fresh
recompute yields `main = []`, matching `tier_of` and matching `METRICS.md`'s
generated "Main table (0)" line. The committed artefact predates B17 and is
stale. An adversarial reviewer reading the artefact concluded "exactly one
main-tier metric has paired data (P3)"; the live answer is zero. Logged with
the other provenance drift in §6.

**The `neutral` flag costs the tested denominator only 2 metrics, not 7.**
Verified per metric: of the seven diagnostics, five (E1, E6, K7, K11, M6) have
`n_paired_games = 0` and would have been excluded by missing data anyway; only
P5 and X5 pair all four games. This matters for how the battery is criticised:
**it is not hiding failures behind `neutral`, it is short of material.** The
thing that collapses 38 to 8 is absent control-arm data, not the diagnostic
flag.

The version that is neither self-flattering nor falsely damning:

> Process 1 is **undetermined**, not negative. Of 38 registered metrics only 8
> were eligible for the specified gradient: 7 are pre-registered `neutral`
> diagnostics that rank nothing by construction, and 28 were never computed on
> both arms — 14 of those because neither control arm carries an explicit
> theory or a repair record, which no rerun can supply. All 8 eligible metrics
> returned `underpowered` rather than `no-effect`: on four paired games the
> exact two-sided sign test's smallest attainable p is 0.125 at best, and 0.25
> where a pair ties, so no metric could reach p<0.05 however cleanly it
> separated. Five (E4, P1, P2, X1, X4) show large, correctly-signed separation
> on the cross-arm gradient, **but only E4 keeps its sign on the model-ladder
> gradient**; P1, P2, X1 and X4 reverse, and P1 trips a wrong-direction warning
> there. One (X3) separates strongly against its declared direction on **both**
> gradients and must be resolved before use. All eight are `reference` tier,
> which the battery's own rule bars from ordering claims — the main table is
> empty, so no metric here is admissible for one regardless of power.

**Sentence to avoid:** *"0 of our 38 metrics separated a known capability
gradient."* True as written, false as read.

---

## 5. The minimal next experiment — and why it is not a bigger pilot

The work item asks for one executable sentence. The honest answer has to start
with a finding that closes off the obvious move:

**No experiment permitted inside Phase 2 can make this pass separate anything.**

Three independent facts, each verified:

1. **A fifth paired game cannot be bought at any price.** `bare_cc` is blocked
   before the socket opens — `harness/arc_client.py` raises `SealedGameError`
   for all 21 sealed games. `schema_repro` cannot grow either: the upstream
   corpus holds 1058 files, of which the whitelist admitted 165 (exactly the
   four development games) and denied 885 as sealed plus 8 as unknown paths —
   which are repository furniture (`.gitattributes`, `README.md`,
   `score_trajectories.py`, two PNGs, three CSVs), not cross-game aggregates as
   I first wrote. 165 + 885 + 8 = 1058, and `denied_sealed_counts` enumerates
   exactly the 21 sealed games, so the corpus covers 25 and **there is no fifth
   non-sealed game in it.** So the gap between the pile's 4 and the test's
   required 6 is not a budget problem; it is the pile cut, and changing it is
   an incident, not a fix.
2. **Repeat runs buy exactly zero paired games.** `discriminate.py:67-79`
   (`_per_game_mean`) collapses every run on a game to one number per side
   before pairing — deliberately, so a game with many runs cannot dominate a
   four-game sign test. There are already 80 `bare_cc` runs across the four
   games. Adding more changes no verdict — at a measured $1.1707/cell (haiku,
   jar-on) to $3.8857/cell (sonnet-5, jar-on) from
   `baseline-arms/runs/20260728T103135Z-a7/unit_prices.json`, that is money
   spent to move nothing.
3. **The secondary gradient is in no better shape.** The model-ladder pass
   (`artifacts/discrimination.json`, haiku-4.5 < sonnet-5 < opus-5 within
   `bare_cc`) tallies **18 no-data, 13 underpowered, 7 not-ranked,
   0 discriminating** — verified. It scores more metrics (13 vs 8) but pairs
   *fewer* games on several of them, and hits the identical ceiling. Two
   gradients, two zeros, same cause.

### So the executable sentence

> **Pre-register, before Phase 4 opens the sealed pile, that process 1's
> confirmatory test runs on ≥6 non-tied paired games (target 12–17, sized from
> the observed 4/4 agreement shrunk to p≈0.83–0.90), on the metrics that keep
> their sign across both existing gradients — today that is E4 and P3 — and
> until then license no metric on a p-value; report effect sizes and directions
> only.**

The "keeps its sign on both gradients" clause is not decoration: without it the
obvious nominees are P1, X1 and X4, all of which reverse on the ladder (§2).
And note what powering E4 or P3 would and would not buy — both are `reference`
tier, so a confirmed effect still licenses no ordering claim while the main
table is empty. **Powering the test is necessary and not sufficient**, which is
the single most important thing for WP5 not to elide.

That is the whole minimal experiment: it costs nothing now, it is the only
route that is both statistically clean and inside the pile cut, and it converts
the current zero from an embarrassment into a correctly-sized plan.

Two things that can and should be done immediately, at zero cost, because they
do not depend on more data:

* **Resolve X3.** It separates the gradient strongly in the wrong direction on
  the cross-arm pass (δ = −0.5625, 0/3 pairs agreeing, `warning` already
  emitted) **and** on the model ladder (δ = −0.667). A metric that is backwards
  on two independent gradients is not underpowered; it is broken, and no
  additional games will fix it. Either the definition measures something else
  or the declared direction is wrong.
* **Stop reporting X2 and X3 as `underpowered`.** Both are power-independent
  results the gate ordering conceals — see §2.

### Options considered and rejected

| route | reaches p<0.05? | why rejected |
|---|---|---|
| pair by schema run (8 high-side runs) | yes for 5 metrics | **pseudo-replication.** The 2 schema runs on a game are the same upstream agent on the same world; n doubles, effective n stays 4. Fails anyway for E4/P1/P2, which score only one schema run per game. |
| fully crossed run pairs (~150) | trivially, p→1e-40 | severe pseudo-replication; the binomial(n, 0.5) null in `stats.py:161` is simply the wrong reference distribution, and the p is a number with no inferential content. |
| swap the sign test for Wilcoxon | **no** | 4 pairs give 2⁴ = 16 sign patterns, so its floor is also 2/16 = 0.125. Any exact permutation test whose exchangeable unit is the game has the same floor. **The wall is the design unit, not the statistic.** |
| unseal games to buy power | yes | an incident. Phase 3 iterates until it gets results, which is only honest if confirmation runs on unseen problems. |
| more repeats on the 4 games | no | collapsed by `_per_game_mean`; see fact 2. |

---

## 6. Two findings outside the work item's four questions

Recorded because they were found on the way and would otherwise be lost.

* **The Schema arm is not one model.** `capability_spectrum.json` shows the
  `claude_fable_opus` collection used `claude-opus-4-8` on ar25/g50t and
  `claude-fable-5` on sk48/tn36, with `gpt-5.6-sol` supplying the other four
  runs. The artifact's `confounds` list records the harness confound and the
  released-material confound but **not this one**: the "stronger arm" is three
  different models across four games. Any effect size on this gradient is a
  contrast against a mixture.
* **The committed spectrum cannot be reproduced from a clean worktree.**
  `capability_spectrum.json`'s `input_digests` names four shard ledgers
  (`ledger.{ar25,g50t,sk48,tn36}.jsonl`) that are untracked and absent here,
  while 11 `a7-*` shards that *are* on disk contribute 17 run_ids appearing
  nowhere in the committed artifact — they were committed after the artifacts
  were last written. A recompute today ingests a **different run set** than the
  one the committed numbers were built from. `battery/STATUS.md` documents the
  two env vars but not this drift. Not V22's territory to fix; logged here and
  in `RUN_STATE.md` so it is not rediscovered a third time.
