# Review (c) — Reproducibility referee

**Status: COMPLETE.**

Paper under review: `papers/phase1-workshop/PAPER.md` (2572 lines)
Worktree: `C:\Users\user\Desktop\theoria\.worktrees\p12-paper-multi-review`
Base commit: `6c2d74a`
Reviewer remit: number-to-artefact traceability, command/path validity,
determinism claims, MANIFEST discipline, environment gaps.

**Constraints honoured.** Zero network calls, zero API calls, zero model calls,
zero game spend. No sealed-pile game was played, inspected, or read about; the
only sealed-pile bytes touched were the *cut definition* itself
(`arc-recon/data/piles.json`, which lists ids and tag strata and no mechanics)
and the sealing counters in the preflight manifest. No tracked file was modified:
every artefact this review regenerated was restored, and the tree was verified
byte-identical to its pre-review state at the end (see §5.3).

**Recommendation: MAJOR REVISION.** The paper's numbers are in unusually good
shape — I checked 51 quantitative values across §§1–9 and every single one
CONFIRMED against the cited artefact, several to more precision than the paper
claims. What does not hold up is the *build*: the README's rebuild recipe is
stale, the repository's own figure stop-gate is red before it reaches its first
real check, and a stranger on a non-Linux checkout hits a silent hashing
divergence. The prose is more reproducible than the pipeline that is supposed to
guarantee it.

---

## 1 · Findings, by severity

### BLOCKING

**B-1. `figures/verify.sh` — the figure pipeline's stop gate — is red at gate 1,
and never reaches gates 2–8.**

```
$ bash figures/verify.sh
== 0. required data sources present ==
ok
== 1. build pass A ==
[fig06_concept_timeline]
  -> FAILED
FAIL: 1 figure(s) failed: fig06_concept_timeline
FAIL: build pass A did not complete
EXIT=1
```

Root cause, from the traceback:

```
File "figures/fig06_concept_timeline.py", line 391, in parse_log
ValueError: THEORIZE_LOG.md: entry ids do not match the declared set.
            unexpected=['E-08', 'E-09'] missing=[]
```

`figures/fig06_concept_timeline.py:108` declares the expressivity-ledger id set
as `"E-01" … "E-07"`. `cold-start-a0/THEORIZE_LOG.md` now carries nine rows —
lines 357–365 of the E table — because two later commits appended them:

| commit | added |
|---|---|
| `76e7560` "C9: the counting guard, one rung" | `E-08` |
| `4dd8e0f` "C9: the mover was the token it ate" | `E-09` |

`figures/fig06_concept_timeline.py` has been touched exactly once, at `8775102`
("P4: salvage the P-21 figure pipeline"), which predates both.

This is the tripwire working as designed — the module's own note says "a changed
miner stops the build instead of redrawing the hole as something else" — but the
consequence is that **`verify.sh` cannot currently be used to verify anything**.
`set -uo pipefail` plus the explicit `exit 1` in gate 1 means gates 2 (second
build), 3 (A vs B determinism), 4 (source manifest), 5 (artefact presence),
6 (committed vs fresh), 7 (undeclared reads) and 8 (coverage) do not execute at
all. A reader told "verify.sh is the stop gate" and "gate 8 is the known-red one"
will run it and get a different, earlier, harder failure.

**B-2. The same upstream edit has staled the paper's own figure payload.**

`papers/phase1-workshop/figures/data/fig1_concept_timeline.json` as committed
does not match what its extractor produces today. Running the README recipe
changes it:

```
$ python figures/fig1_concept_timeline.py
wrote data/fig1_concept_timeline.json and fig1_concept_timeline.txt
$ git diff --numstat papers/phase1-workshop/figures/data/fig1_concept_timeline.json
24      0
```

The whole diff is four rows appended to `expressivity_ledger` — E-06, E-07, E-08,
E-09 — read out of the same living `THEORIZE_LOG.md` that breaks B-1. So one edit
by another track simultaneously (a) hard-fails the repository's main figure
pipeline and (b) makes the paper-local figure payload stale. A stranger following
`README.md` will produce a figure that differs from the committed one and has no
way to tell which is correct.

This directory's `gate-diagnosis.md` (by `W-1651`) reached the same conclusion
independently and pushed it further, correctly in my view: the fix is *not*
"regenerate and commit", because `sections/10_limitations.md:41–43` says A0's
ledger has **five** gaps and `sections/04_a1.md:92` books E-06 to A1. Regenerating
would let the A0 plate silently absorb post-A0 work and contradict the paper's own
text. I endorse that reading and add the pipeline half of it: the same staleness
is a *build failure*, not only a figure-content question, and B-1 has to be closed
by whoever closes B-2.

### MAJOR

**M-1. The README's rebuild recipe does not rebuild the paper's figures.**

`papers/phase1-workshop/README.md` gives this as the rebuild:

```bash
python figures/fig1_concept_timeline.py
python figures/fig2_coverage_accuracy.py
python figures/fig3_loop_ledger.py
python assemble.py
```

All four commands ran and exited 0. But `figures/fig1_concept_timeline.py`'s own
first line is:

> `"""SUPERSEDED AS A SOURCE (P9). Kept as the witness, not as the figure.`
> … `Do not cite this file from a section. It is not the figure any more."""`

The real figures are built by the repo-root pipeline (`figures/build_all.py`,
gated by `figures/verify.sh`), which the README never mentions. A stranger
following the README believes they have rebuilt the paper's figures and has in
fact rebuilt three superseded witnesses — and has silently dirtied the tree while
doing it (see M-3). The README also does not mention `verify.sh`,
`check_figure_parity.py`, or the untracked `verify_paper.py`.

**M-2. `figures/check_coverage.py` (gate 8) is red — diagnosis CONFIRMED, with a
correction to how it was framed.**

I was asked to confirm or contest the standing diagnosis. **Confirmed on cause,
contested on framing.**

Confirmed: the probe exits non-zero, and the cause is exactly half-written
`theoria-arm/runs/*` directories missing `cost_curve.json`.

```
$ python check_coverage.py --self-test >/dev/null 2>&1; echo $?
0                                   # negative control fires correctly
$ python check_coverage.py > /tmp/cov.txt 2>&1; echo $?
1
$ grep -c '^COVERAGE:' /tmp/cov.txt
11
```

All 11 messages are the same shape — "has MANIFEST.json; missing
cost_curve.json". I verified the population independently by walking
`theoria-arm/runs/` myself: exactly 11 directories contain `MANIFEST.json` and no
`cost_curve.json`, and they are the same 11 the probe names
(`…012311Z-…-salvage`, `…-salvage2`, `…014402Z-…-salvage`, `…015354Z-…-salvage`,
`S8-provenance-backfill`, `a3-desk-gate`, `a3-turn-series`, `a3-level-boundary`,
`A3-campaign-devpile`, `E14-crash-is-not-a-finding`, `preflight-20260728T012031Z`).
Three further directories (`…-leg01`, `…-leg02`, `a3-gate-mock`) also lack
`cost_curve.json` but lack `MANIFEST.json` too, so the probe correctly skips them.

Contested: "gate 8 is the known-red one" understates the state of the tree.
Gate 8 is red *and unreachable* — `verify.sh` dies at gate 1 (B-1). Anyone
running the stop gate today sees a fig06 build crash, not a coverage failure, and
the coverage failure is only visible by invoking `check_coverage.py` directly, as
I did. The tree has two independent reds, not one.

**M-3. Running the paper's own tooling dirties the working tree.**

I began the review with `papers/phase1-workshop/figures/fig1_concept_timeline.txt`
already showing as `M` in `git status`, before I ran anything. `gate-diagnosis.md`
identifies the mechanism: `verify_paper.py:217–220`'s `finally` block restores
only `data/*.json`, while `common.emit` also writes `figures/<name>.txt`, which is
never restored. I can confirm the effect from the other direction — my own
regeneration reproduced that exact modified `.txt` byte-for-byte
(`09c670718c77f6…`), which is what a leftover from a prior tool run looks like.

A verification tool that mutates the tree it is measuring is a reproducibility
hazard in its own right: the next reviewer cannot distinguish "the repo is dirty"
from "the last check left it dirty".

**M-4. `PROVENANCE.md` has no §8 block at all.**

The index covers §1, §3, §4, §5, §6, §7, §9 and §10. **§8, the exam, is absent
entirely** — no rows, no heading. §8 is not a minor section: it carries the
1,790-probe leakage figure, the 46.0/46.0 handover result, the four papers'
item/point counts, the calibration bands and the two shipped leaks. Every one of
those numbers is cited inline in `sections/08_exam.md` and every one I checked
CONFIRMED (see §3 below), so this is an index-completeness failure rather than a
traceability failure — but the paper's front matter names `PROVENANCE.md` as *the
index of the binding rule*, and an index that silently omits a section cannot be
used to audit coverage. §2 and §11 are also absent, which matters less (they are
framework and related-work and carry few load-bearing numbers).

### MINOR

**m-1. `arc-recon/data/piles.json` hashes differently on a Windows checkout —
three values are now in circulation for one file.**

```
$ sha256sum arc-recon/data/piles.json
f2ef44d100caee9075b9c52b6c2694d9bb47d628702e0c1911655eb9f9790826   # working tree, here
$ git show HEAD:arc-recon/data/piles.json | sha256sum
d3140eff4889095f64aff6360697eeff0a1b159a53d80a1ef6407b2c4dd5b8c9   # committed blob
$ grep -n '3feca53e' CLAUDE.md
127: `arc-recon/data/piles.json` (sha256 `3feca53e…41bbc19a`)          # published
```

Cause: `core.autocrlf=true`, and the file is checked out with CRLF (111 CRLF
pairs in 3248 bytes). `CLAUDE.md` says `engine-rig/.gitattributes` pins LF "so
`core.autocrlf` cannot corrupt them" — true of `engine-rig/`, but **`arc-recon/`
has no `.gitattributes`**, and the repo-root `.gitattributes` contains exactly one
line, `PARTNER_SYNC.md merge=union`. Ten directories carry their own
`.gitattributes`; `arc-recon/` is not one of them.

`PROVENANCE.md`'s last table already says CLAUDE.md's `3feca53e…` "is not a file
hash" and gives `d3140eff…` as the real one. **That row CONFIRMS** — against the
committed blob. I can strengthen it: `3feca53e…` is a *field stored inside
`piles.json` itself* (`{"sha256": "3feca53e5ede…"}`), so it can never equal the
file's own digest, and every consumer that appears to "verify" the cut —
`theoria-arm` ledger seq 1, `battery/artifacts/capability_spectrum.json`
`provenance.cut.piles_sha256` — is reading that field back rather than hashing
anything. The cut *is* intact; the verification of it is circular. That is
`PROVENANCE.md`'s own D-B-011 finding, and it is understated there.

**m-2. Battery artefacts cannot be opened with a bare `open()` under a non-UTF-8
locale.**

```
UnicodeDecodeError: 'gbk' codec can't decode byte 0x94 in position 3114
```

on `battery/artifacts/capability_spectrum.json`. The repo's own code is careful —
every script I ran (`fig1–3`, `assemble.py`, `build_all.py`, `check_coverage.py`,
`check_figure_parity.py`) passes `encoding=` and worked fine — so this bites the
*reader* writing a throwaway check, not the pipeline. Worth one line in the README
for anyone auditing on a CJK-locale Windows box, which is what this repository is
being developed on.

**m-3. §9 does not surface a `verdict` field in the manifest it cites.**

`theoria-arm/runs/preflight-20260728T012057Z/MANIFEST.json` → `cost` carries,
alongside the `model_calls: 0` / `usd: 0.0` the paper quotes:

> `"verdict": "the price table and the provider's own arithmetic DISAGREE -- this
> is a finding about proxy/pricing/pricing_v1.json, not about the run"`

The zero-spend claim is **sound regardless** — with `model_calls: 0` no price
table can change the total, and I confirm the arithmetic — so this is not a
correctness problem. But the paper's stated discipline is that where sources
disagree it "cites both and says which is later", and here a disagreement flagged
inside the very object being cited goes unmentioned. One clause would close it.

**m-4. Four `.../`-elided paths do not resolve mechanically.**

My path sweep over `PAPER.md` found 142 distinct path-like citations, **139 of
which exist**. The three that do not are `.../MANIFEST.json` and `.../run.json`
(`PAPER.md:1931`, elided against the run directory named six lines earlier) and a
truncated `theory/theory.dsl` (`PAPER.md:412`, cited at full length elsewhere).
`PROVENANCE.md` scores 72/76 with the same pattern. These are readable by a human
and unresolvable by a script; `gate-diagnosis.md` already itemises them as B-i…B-iv
with fixes. I confirm the sweep independently and rate it MINOR — the elisions are
locally unambiguous.

---

## 2 · What I ran, and what happened

Every command below was run from the worktree with no network access.

| # | command | result |
|---|---|---|
| 1 | `python figures/fig1_concept_timeline.py` | exit 0 — **but rewrote the committed payload** (B-2) |
| 2 | `python figures/fig2_coverage_accuracy.py` | exit 0, output byte-identical to committed |
| 3 | `python figures/fig3_loop_ledger.py` | exit 0, output byte-identical to committed |
| 4 | `python assemble.py` | exit 0 — "12 sections, ~24107 words"; `PAPER.md` byte-identical to committed |
| 5 | `bash figures/verify.sh` | **exit 1 at gate 1** (B-1) |
| 6 | `python figures/check_coverage.py --self-test` | exit 0 — negative control fires |
| 7 | `python figures/check_coverage.py` | **exit 1**, 11 findings (M-2) |
| 8 | `python papers/phase1-workshop/figures/check_figure_parity.py` | **exit 0** — 12 agree, 1 one-sided, 1 ruled, 0 new |
| 9 | `python assemble.py` ×2, `fig3` ×2, `fig1` ×3 | byte-identical (§5) |

No command required an environment variable, an API key, a network fetch, or a
gitignored payload. **`ARC_API_KEY` was never loaded and never needed** — the
paper's offline claim holds for everything the README asks a reader to run.
Nothing reached for the network.

### 2.1 The parity witness passes, and is the best instrument in the tree

`check_figure_parity.py` exits **0** and is genuinely informative rather than
decorative:

```
figure parity: 3 paper figures mapped onto the pipeline
  AGREE       A0 accuracy vs truth (on trace): both 0.987288 (fig07, status=ok)
  AGREE       A0 state-action pairs: both 236.0
  AGREE       A0' state-action coverage: both 0.469298
  AGREE       manual revisions driven by certify: both 0.0
  AGREE       ledger beats: both 8.0        loop beats proper: both 6.0
  ONE-SIDED   A0 executable probes: paper states 0; fig07 REFUSES to state it
  ADJUDICATED adjudications on the timeline: paper 18 vs fig06 17.0
12 agree, 1 one-sided, 1 known and ruled on, 0 new.
```

Two things deserve credit. The `ONE-SIDED` row is a disagreement *about evidence*
rather than arithmetic, and the tool says so in those words. The `ADJUDICATED` row
rules against the paper's own directory — "the pipeline is right and this
directory is wrong … filling an absence with a value is the one thing every figure
in this repository is required not to do", concluding the count is 17 with one
entry never ruled on, not 18. A parity checker that adjudicates against its own
side is the strongest reproducibility artefact I found here.

Note the tension with M-1: this tool works by running the *superseded* extractors
against the pipeline, so it is the one place where the README's three scripts still
have a job. The README does not say so.

---

## 3 · Citation sample — 51 values checked, 51 CONFIRMED

I opened every cited artefact and read the value out. **Not one NOT-FOUND and not
one DIFFERENT-VALUE.** Where the paper rounds, the artefact carries the unrounded
value and the rounding is correct.

### §1 / §3 — A0 and A0′

| # | claim | cited | verdict |
|---|---|---|---|
| 1 | 276/276 frames, 22 356/22 356 px, 0 anomalies | `cold-start-a0/A0_REPORT.md` §2 | **CONFIRMED** — line 40, verbatim in bold |
| 2 | 233 of 236 pairs, 0.987288 | `score_vs_truth.json` | **CONFIRMED** — `base.behavioural = {accuracy: 0.987288, agree: 233, disagree: 3}` |
| 3 | held-out accuracy 0.000 on 3 pairs | ibid. | **CONFIRMED** — `base.held_out = {accuracy: 0.0, agree: 0, disagree: 3}` |
| 4 | the three missed pairs are Button from below/right/above | ibid. `examples` | **CONFIRMED** — DOWN@(2,2), RIGHT@(3,1), UP@(4,2), each `world_pressed: true` against an unchanged `manual_cart` |
| 5 | ground truth first read at M6 | ibid. `seal` | **CONFIRMED** — `"ground truth first read at M6, after M4 and M5 were green"` |
| 6 | 59 reachable states, 276 frames | `A0_REPORT.md` §1 | **CONFIRMED** — line 24 |
| 7 | K4 = 1.000 over 7 annotated clauses | `capability_spectrum.json` run `a0-base` | **CONFIRMED** — `K4 = {value: 1.0, support: {annotated: 7, unannotated: 3}}` |
| 8 | K2 = 0.000 over 3 pairs, 0 agreements | ibid. | **CONFIRMED** — `K2 = {value: 0.0, support: {agree: 0, pairs: 3}}` |

Claim 8's `support.frame` adds a caveat the paper honours: "Adversarial gaps left
by the trace, not a sample drawn from the world -- not comparable with an
exhaustive enumeration."

### §4 — A1 (the empty axiom list)

| # | claim | cited | verdict |
|---|---|---|---|
| 9 | solved weight vector `[-1,1,0,1,-1]` | `pagoda_5_11011_to_00010.json` | **CONFIRMED** — `weights_integer: [-1,1,0,1,-1]` (field is `weights_integer`, not `weights`) |
| 10 | `inv_closed`: 6 move instances, all delta ≤ 0 | ibid. `obligations.inv_closed` | **CONFIRMED** — `n_checked: 6, holds: true`, "all move instances on the full state space" |
| 11 | `goal_break`: goal potential 1 > initial 0 | ibid. | **CONFIRMED** — `potential: 1, exceeds_initial_by: 1`; `initial_potential: 0` |
| 12 | **four theorems, empty axiom lists** | `theory-compiler/STATUS.md` | **CONFIRMED** — line 20, `inv_init`/`inv_closed`/`inv_all`/`unsolvable` → **四条全空**; line 284 `'inv_init' does not depend on any axioms` |
| 13 | negative control: all four `[sorryAx]`, exit 1 | ibid. §独立复核 | **CONFIRMED** — line 344 "四条定理全部变成 `depends on axioms: [sorryAx]`"; line 94 "退出码非零、`sorryAx` 出现" |
| 14 | 83 passed, 8 invoking `lean` | ibid. | **CONFIRMED** — lines 271 and 364, both |

Claim 12 is the §4 headline the remit named. It confirms, and the negative control
at 13 is what makes it meaningful: the same harness is shown producing `sorryAx`
when the weight table is sabotaged, so the empty list is a measurement rather than
a default.

### §5 — A2 (the repair beats)

| # | claim | cited | verdict |
|---|---|---|---|
| 15 | 8 beats, 8 pass, 0 fail, 0 absent | `loop_ledger.json` | **CONFIRMED** — `summary: {absent: 0, fail: 0, pass: 8, total: 8}`, `len(beats) == 8` |
| 16 | authority = INC-004 ruling, option (b) | ibid. `authority` | **CONFIRMED** — verbatim, incl. "No upstream DC22 artifact was read" |
| 17 | holed manual cheap certify: 184 frames, 14 904 px, 0 anomalies | `exhibit_report.json` | **CONFIRMED** — `{frames: 184, pixels_checked: 14904, pixels_unexplained: 0, green: true}` |
| 18 | the bound: 248 frames, `green: false`, 44 anomalies, first at t184 (6,4) | ibid. `certify_cheap_vs_full_sweep` | **CONFIRMED** — all four exactly; `first_anomaly: {cell: [6,4], t: 184, kind: render_mismatch}` |
| 19 | "128 unexplained of 20 088" is **report-only** | `A2_REPORT.md` §2 | **CONFIRMED AS ABSENT** — the sweep block carries no pixel key at all, exactly as `PROVENANCE.md` declares |

Claim 19 is a credit rather than a defect: the index predicted the artefact would
*not* carry the figure, and it does not. That is what a working provenance index
looks like.

### §6 — A3 (the transfer numbers)

| # | claim | cited | verdict |
|---|---|---|---|
| 20 | like-for-like actions 346 → 10 = 0.029 | `bill_table.md` | **CONFIRMED** — line 20, ratio `0.0289` |
| 21 | like-for-like frames 347 → 11 | ibid. | **CONFIRMED** — line 19, ratio `0.0317` |
| 22 | cost to first plan: 1 frame, 0 actions | `bill_l2_transfer.json` | **CONFIRMED** — `{world_frames: 1, world_actions: 0}` |
| 23 | the four zeros | ibid. | **CONFIRMED** — `engine_stages: 0, candidates_adjudicated: 0, theorize_rounds: 0, dsl_clauses_written: 0` |
| 24 | verification unchanged: compile 1, certify 1, plan 1 | ibid. | **CONFIRMED** — `compile_runs: 1, certify_runs: 1, plan_runs: 1` |
| 25 | plan SAT length 10, win | `arm_l2_transfer.json` | **CONFIRMED** — 10 actions listed, `outcome: "win"`, `backend: "stub-bfs"` |
| 26 | referee's shortest for L2 = 10 | `ground_truth.json` | **CONFIRMED** — `a3-l2.truth.shortest_solution_length: 10` |
| 27 | carried manual 252/252 = 1.0 | `score_vs_truth.json` | **CONFIRMED** — `{accuracy: 1.0, pairs_checked: 252, pairs_correct: 252, note: "THE CARRIED MANUAL on a level it never explored"}` |
| 28 | reachable states L1 62, L2 63 | `ground_truth.json` | **CONFIRMED** — both, in `truth` and `coverage` independently |
| 29 | `l2-oneway` 63 → 34, unsolvable | ibid. | **CONFIRMED** — `reachable_states: 34, solvable: false` |
| 30 | `l2-rewired` shortest = 15 | ibid. | **CONFIRMED** — `shortest_solution_length: 15` (and `DECISIONS.md` D-A3-010's 14 is indeed stale, as PROVENANCE says) |
| 31 | negative controls both caught | `negative_controls.json` | **CONFIRMED** — `all_caught: true, none_claimed_a_win: true` |
| 32 | planner backend `stub-bfs`, not Fast Downward | every `plan.backend` | **CONFIRMED** |

### §7 — the battery

| # | claim | cited | verdict |
|---|---|---|---|
| 33 | **95 runs** | `capability_spectrum.json` | **CONFIRMED** — `len(runs) == 95` |
| 34 | **38 metrics** | ibid. | **CONFIRMED** — `len(cards) == 38`, `len(coverage) == 38` |
| 35 | 5 arms | ibid. | **CONFIRMED** — `bare_cc, schema_repro, theoria_a0, theoria_a0_spike, theoria_a2` |
| 36 | 4 games | ibid. `provenance.cut.dev_pile` | **CONFIRMED** — the four dev-pile ids, and only those |
| 37 | **1 433 computed values** | ibid. | **CONFIRMED exactly** — summing `by_status` across all 38 metrics × 95 runs gives `{ok: 1433, not-applicable: 2066, insufficient-data: 111}`, total 3610 |
| 38 | `battery_version: "v2"` | ibid. | **CONFIRMED** |
| 39 | **38 exploits, 34 still land** | `gaming_audit.json` | **CONFIRMED** — `n_demonstrated: 38`; `demonstrated.succeeded == true` for exactly 34 (the 4 that do not: E2, K12, M3, P4) |
| 40 | 17 register entries contradicted | ibid. | **CONFIRMED** — `n_disagreements: 17`, `len(disagreements) == 17` |
| 41 | main table 9, reference 29 | ibid. | **CONFIRMED** — `len(main) == 9`, `len(reference) == 29` |

Claim 37 is the one I most expected to drift, and it lands on the nose. Claim 39
is the §7 headline the remit named; the four survivors are individually named in
the artefact, so the "34" is auditable rather than asserted.

### §8 — the exam (no `PROVENANCE.md` rows exist; checked inline instead)

| # | claim | cited | verdict |
|---|---|---|---|
| 42 | items 80 / 29 / 60 / 17 | `exam/artifacts/leakage.json` | **CONFIRMED** — `n_items` = 80, 29, 60, 17 in that order |
| 43 | **1 790 declared probes** | ibid. | **CONFIRMED** — `probes_declared` 363 + 58 + 1284 + 85 = 1790 |
| 44 | 0 probe hits, 0 structural hits | ibid. | **CONFIRMED** — `probe_hits: 0` and `structural_hits: 0` on all four papers |
| 45 | `label_sets_checked: []` for handover and adaptation | ibid. | **CONFIRMED** — empty for exactly those two; heldout has `["event","level_name"]`, verdict has three |
| 46 | oracle 1.000, null 0.000 on all four papers | `calibration.json` | **CONFIRMED** — oracle 1.0 / null 0.0 across adaptation, handover, heldout, verdict; `calibrated: true, failures: []` |
| 47 | held-out bluffer scored 0.45 against a band ending 0.35 | ibid. | **CONFIRMED** — `heldout.bluffer = 0.45` |
| 48 | both tiers 46.0/46.0 on handover | `reports/p15-handover-a0.reader-tier{1,2}.report.json` | **CONFIRMED** — `awarded: 46.0, possible: 46.0, fraction: 1.0` in both files |
| 49 | `tier2_minus_tier1: null` | `calibration.json` | **CONFIRMED** — three occurrences, each with a note explaining why a delta needs both tiers |

§8's numbers are as well-attached as any section in the paper. The problem is
purely that `PROVENANCE.md` does not index them (M-4). Claim 49 is worth
highlighting as good practice: the paper reports the tier difference as
*unmeasured* and the artefact independently records `null` rather than `0.0`.

### §9 — the preflight (zero spend)

| # | claim | cited | verdict |
|---|---|---|---|
| 50 | 23 ledger records | `preflight-20260728T012057Z/ledger.jsonl` | **CONFIRMED** — 23 rows: 18 `env_step`, 3 `env_meta`, 1 `run_start`, 1 `run_end` |
| 51 | 18 RESET attempts, 17×400 + 1×200 | ibid. | **CONFIRMED exactly** — `POST /api/cmd/RESET` → 400 ×17, 200 ×1 |
| 52 | **`model_calls: 0`, `usd: 0.0`** | `MANIFEST.json` → `cost` | **CONFIRMED** — plus `calls_priced: 0, calls_unpriced: []` |
| 53 | `successful_actions: 0` over 18 env steps | ibid. → `reconciliation` | **CONFIRMED** — `{env_steps: 18, successful_actions: 0, levels_completed_from_ledger: 0}` |
| 54 | sealing counters all zero | ibid. → `sealing` | **CONFIRMED** — `bypass_attempts: 0, guard_blocks: 0, credential_in_body: 0, incidents: 0, sealed_pile_requests: 0` |
| 55 | guard fingerprint: cut v1, 4 dev, 21 sealed, `unknown_policy: "deny"` | ledger seq 1 | **CONFIRMED** — all four fields verbatim |
| 56 | scored actions 0 — the API's own close response | ledger seq 22 | **CONFIRMED** — scorecard close returns `actions: 0, completed: false, levels_completed: 0, resets: 0` |

(Rows run to 56 because several bundle two checks; 51 distinct values were read
out of artefacts.) The zero-spend claim — the §9 headline — is the best-supported
number in the paper: confirmed three independent ways (the cost block, the
reconciliation block, and the provider's own close response), and the `resets: 0`
in row 56 corroborates the separate "RESET is not billed" argument.

---

## 4 · Is `PROVENANCE.md` a real index?

**Yes, with one structural gap (M-4) and one row that undersells itself (m-1).**

Mechanically: 76 distinct path-like citations, **72 resolve**, and the 4 that do
not are the `.../` elisions of m-4. I spot-checked rows across every block and
found no row whose cited file lacked the claimed value.

What raises my confidence above a spot-check is that the index is *falsifiable in
both directions*, and I was able to test that:

* It predicts where an artefact will **not** carry a value — the "128 unexplained
  of 20 088" row, the "read-only verification, 258 files hashed" row, the
  P1↔failure-rate ρ = −0.83 row. I checked the first: the artefact indeed has no
  pixel key. The index told the truth about its own gaps.
* Its "Known source disagreements" table adjudicates against its own sources and
  says which it follows. I tested the pile-hash row and it holds against the
  committed blob (m-1).
* It records **deletions** — the X5 cross-check row and the per-model E5/E2
  aggregates removed rather than repaired, with the reason.

That is a genuine index, not a decorative one. The §8 hole is the thing to fix.

---

## 5 · Determinism

**The determinism claim holds for everything I could test.** The README says
"running them twice produces identical output"; it does.

```
$ python assemble.py && sha256sum PAPER.md
500867cdb66e38a258da51acde9ad0709242d8bb68e841b6f3c9f6acff6a8cbc *PAPER.md
$ python assemble.py && sha256sum PAPER.md
500867cdb66e38a258da51acde9ad0709242d8bb68e841b6f3c9f6acff6a8cbc *PAPER.md   # identical
```

`PAPER.md` also matches the committed file exactly — the generated artefact is in
sync with `sections/*.md`.

```
$ python figures/fig3_loop_ledger.py && sha256sum figures/data/fig3_loop_ledger.json
fd88c32db039cfb3c7dcfbe46a320d63e47f01399d19c3733cb1fc61eb38624d
$ python figures/fig3_loop_ledger.py && sha256sum figures/data/fig3_loop_ledger.json
fd88c32db039cfb3c7dcfbe46a320d63e47f01399d19c3733cb1fc61eb38624d   # identical
```

fig1 likewise produced a stable hash across three consecutive runs
(`0e3cb93fc865e0…`), which is what establishes B-2 as **staleness, not
nondeterminism** — the extractor is reproducible; its committed output is simply
older than its input.

Two determinism claims I could **not** test, and a reader should know it:

* `verify.sh` gates 2–3 are the repository's real determinism proof (two builds
  into separate scratch trees, `diff -r`). They never ran, because gate 1 aborts
  (B-1). **The repository's headline byte-reproducibility claim for the figures is
  currently unverifiable by its own instrument.**
* Cross-platform determinism is not what the repo thinks it is. m-1 shows a
  tracked JSON file whose on-disk bytes differ from its committed bytes on this
  checkout. `git diff` shows it clean (git normalises), so the divergence is
  invisible to the obvious check and visible only to `sha256sum` — which is
  exactly the operation the provenance discipline is built on.

### 5.3 Tree restored

```
$ git checkout -- papers/phase1-workshop/figures/data/fig1_concept_timeline.json
$ diff <pre-review hashes> <post-review hashes>
TREE RESTORED: byte-identical to pre-review state
$ ls -d figures/.verify
ls: cannot access 'figures/.verify': No such file or directory   # verify.sh trap cleaned up
$ git status --porcelain
 M papers/phase1-workshop/figures/fig1_concept_timeline.txt   # pre-existing, from a prior tool run (M-3)
?? papers/phase1-workshop/verify_paper.py                     # pre-existing, untracked
```

Both remaining entries predate this review. No tracked file was modified by me.

---

## 6 · What would block a stranger, in order

Ordered by when they would hit it, cloning this repo cold with no access to the
authors.

1. **`bash figures/verify.sh` fails immediately**, and the failure message is
   about an entry-id set in a Markdown log, not about anything they did. Nothing
   in the README warns them. They cannot tell whether the repo is broken or their
   environment is. *(B-1)*

2. **The README's rebuild recipe rebuilds the wrong thing.** They run four
   commands, all exit 0, and they now believe they have reproduced the figures.
   They have reproduced three files whose own docstrings say they are not the
   figures any more. *(M-1)*

3. **Their rebuild silently disagrees with the repo** — `fig1_concept_timeline.json`
   changes by 24 lines — with no stated rule for which version is right. The
   correct answer (the committed one, because the new rows are post-A0 work) is
   recorded only in a run-directory diagnosis note, not in the README or the
   paper. *(B-2)*

4. **Their tooling dirties the tree**, so the next `git status` is confusing and
   they cannot cleanly re-run. *(M-3)*

5. **On Windows (or any `core.autocrlf` checkout) hashes will not match.**
   `arc-recon/data/piles.json` hashes to a third value distinct from both the
   committed blob and the published constant. A stranger trying to verify the pile
   cut — the one integrity check the whole sealed-pile discipline rests on — gets
   a mismatch and no explanation, because only 10 of the repo's directories pin LF
   and `arc-recon/` is not one of them. *(m-1)*

6. **The pile-cut hash cannot be verified even in principle**, because the
   published constant is a field stored inside the file it purports to hash. A
   diligent stranger will burn time discovering that the check is circular. *(m-1)*

7. **A CJK-locale machine cannot open the battery artefacts** with a naive
   `open()`. Recoverable in seconds once understood, opaque for a while before
   that. *(m-2)*

8. **§8's numbers are not in the index.** A stranger auditing via `PROVENANCE.md`
   will conclude the exam section is uncited. It is not — every number is cited
   inline and every one I checked confirms — but the index is the advertised entry
   point. *(M-4)*

9. **Four `.../` elisions** need a human to resolve. Trivial, listed last because
   a human reader resolves them without noticing. *(m-4)*

Nothing on this list is about a missing API key, a gitignored payload, or an
absent tool. **The paper genuinely runs offline**, and that claim survived every
test I put to it. The blockers are all staleness and documentation drift between a
fast-moving repository and a paper that was, at the moment it was written,
accurate.

---

## 7 · Summary for the editor

The binding rule — every quantitative claim carries the path of the artefact it
came from — **holds**. 51 values checked across §§1–9, including every headline
number named in my remit, and every one confirmed against the cited file. Several
confirmed more precisely than claimed (1 433 exactly; 34 of 38 with the four
survivors individually named; 1 790 as the sum of four per-paper probe counts).
The provenance index is falsifiable in both directions and I confirmed it telling
the truth about its own gaps. This is the most carefully sourced draft I have
refereed in this repository.

The failure is not in the numbers but in the machinery around them. One edit by
another track to `cold-start-a0/THEORIZE_LOG.md` — a living Markdown log that a
figure extractor treats as a frozen source — simultaneously broke the repository's
figure stop gate and staled the paper's own figure payload, and neither the README
nor the paper tells a reader that. Fix B-1 and B-2 together (they are one bug),
correct the README to point at the real pipeline, and add the §8 block to
`PROVENANCE.md`, and this reproduces cleanly for a stranger.

One recommendation beyond the findings: the deepest issue is architectural, and
`gate-diagnosis.md` names it exactly — *"the figure's provenance is 'whatever this
file says today', which is not a provenance."* Every other source in the figure
pipeline is a frozen JSON artefact. This one is a document another track is still
writing. Pinning it to a commit is the repair, and it is the kind of repair that
prevents the next four instances of the same failure.
