# RUN_STATE — P13-figure-numbering-and-plates

`MANIFEST.json` beside this file is canonical; this is the narrative.

**Branch** `agent/p13-figure-numbering`, worktree `.worktrees/p13-figure-numbering/`,
base `e507c8e` (master). **Territory:** `figures/` only, plus one appended
paragraph in `PARTNER_SYNC.md` and one note to `monitor/inbox/`. Nothing under
`papers/` was written — that territory is held by another worker — and nothing
under `cold-start-a0/`, which belongs to the other track.

**Passive:** zero API calls, zero model calls, zero network, $0.00, sealed pile
untouched.

## The item was about numbering. The first `verify.sh` run found something worse.

**`figures/verify.sh` was red on master, and the failing figure is the one the
paper calls Figure 1.**

```
FAIL: 1 figure(s) failed: fig06_concept_timeline
FAIL: build pass A did not complete
ValueError: THEORIZE_LOG.md: entry ids do not match the declared set.
            unexpected=['E-08', 'E-09'] missing=[]
```

`cold-start-a0/THEORIZE_LOG.md` — the other track's file — grew two E-table rows
after `figures/fig06_concept_timeline.py:108` declared the id set it expects.
The parser **failed closed**, which is what it was built to do: the comment above
`EXPECTED_IDS` says the two failure directions are different bugs and both are
silent by default. It is the right behaviour and it had been red long enough that
the paper's Figure 1 could not be rebuilt from master.

Fixed by admitting E-08 and E-09. Both are ordinary rows of the same table
(`THEORIZE_LOG.md:364-365`), both `discharged`, both forced by `worldgen`'s
`t2-lock-fragile`.

## The number I expected to move, and did not

The obvious consequence would be that the paper's "seventeen decisions" (§3.1)
becomes nineteen — a paper-side number, and one that P9 had already adjudicated
once, ruling the paper's eighteen wrong against the pipeline's seventeen.

**It does not move, and I checked before writing it down.** In the regenerated
CSV, E-08 and E-09 carry `event_kind` `no-proposal-ABSENT` and `ledger-logged` —
neither is an adjudication — and `papers/phase1-workshop/figures/check_figure_parity.py`
still reports `paper 18 vs fig06 17.0` with the same ruling in the pipeline's
favour. **The paper needs no change here.** Recording the near-miss because filing
an inbox item asserting "the count is now nineteen" was one step away, and it
would have been wrong in the same shape as the defect it was reporting.

## What the fix revealed underneath

Unblocking gate 1 let gates 2–8 run for the first time. Seven of eight now pass.
**Gate 8 is red, and it was not red before — it was *unreached*:**

```
FAIL: data on disk is not reaching the figures
  COVERAGE: theoria run directory 20260729T080000Z-E14-crash-is-not-a-finding
  (has MANIFEST.json; missing cost_curve.json): the discovery rule requires every
  member and so skips it, which means neither the rule nor this probe would notice
  it. A half-written run must be named, not silently dropped by both.
```

Ten-plus `theoria-arm/runs/*` directories are in that state. **This is not a
figures defect and is not fixed here**: the probe is working exactly as designed
and is telling the theoria-arm track that its run directories are half-written.
Reported to `monitor/inbox/`. The general lesson is worth more than the instance:
**a red gate hiding behind an earlier red gate is invisible, and the earlier one
had been red long enough to be normal.**

## The item's actual subject, unchanged and still true

* **Three numbering authorities.** The paper says "Figure 1 / 2 / 3"; the live
  pipeline numbers `fig02`–`fig07` after `Theoria.md` 3.2; the deprecated parity
  witness at `papers/phase1-workshop/figures/` numbers `fig1`–`fig3`. The paper's
  numbers agree with **the witness it is told not to cite** and disagree with the
  pipeline it does cite: Figure 1 = `fig06`, Figure 2 = `fig07`, Figure 3 = `fig05`.
  A reader following the paper's numbering into `figures/` lands on the wrong
  plate, which is the same trap P9 spent a round closing in a different form.
* **Three built, verified, deterministic figures are cited nowhere in the paper**
  — `fig02_bill_shape`, `fig03_capability_spectrum`, `fig04_a3_transfer`. Those
  serve the bill shape, §7's battery and §6's transfer, which are the sections
  P12's reviewers independently called the least evidenced. The plates exist, pass
  eight gates, and are unused.
* **`PAPER.md` embeds no plate at all.** Figures 1–3 are described at length and
  never shown.

All three are paper-body changes. `papers/` is held by another worker and
`CHARTER.md` reserves the body to RES-2, so they are written up for `inbox/`
rather than acted on.

## One P12 finding refuted before it could be actioned

P12's outside reader filed **BLOCKING**: "six of seven cited figure paths do not
exist". All nine `figures/…` paths cited by `PAPER.md` resolve; the reviewer had
looked under the parity-witness directory. Already recorded in
`agent/p12-paper-multi-review`'s `PARTIAL.md`; repeated here because this run is
where a figures-side reader would look for it.

## Verification

```
bash figures/verify.sh        7 of 8 gates pass; gate 8 red, owner theoria-arm
python figures/build_all.py   OK: 6 figure(s) built
```

Gates 2 and 3 (build twice into separate trees, diff byte for byte) pass, so the
regenerated plates are deterministic.

**One self-inflicted scare, recorded because the disk is the memory.** A stray
`> figures/SOURCES.sha256` redirect in a shell one-liner truncated the committed
source manifest to zero bytes before the command that was meant to write it had
even run. `build_all.py` regenerates it (`sources hashed -> SOURCES.sha256`), and
`wc -c` caught it at 0 before anything was committed. Shell redirection truncates
on parse, not on success.
