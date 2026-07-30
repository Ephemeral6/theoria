# V22 — working notes (written incrementally)

## Step 0 — reproduce the audit tally (2026-07-29T14:32Z)

`battery/artifacts/discrimination_arms.json`, 38 metrics:

| verdict | n | metric ids |
|---|---|---|
| `separating` (code name: `discriminating`) | **0** | — |
| `underpowered` | 8 | E4 P1 P2 P3 X1 X2 X3 X4 |
| `not-ranked` | 7 | E1 E6 K7 K11 M6 P5 X5 |
| `no-data` | 23 | E2 E3 E5 E7 K1–K6 K8–K10 K12–K14 M1–M5 P4 X6 |

Audit's 23/8/7/0 reproduces exactly. `arms_present = [bare_cc, schema_repro]`,
`available = true`, `control_runs = 88`.

## Step 1 — the zero is not a measurement (own reading, before subagents report)

`battery/audit/stats.py:166` — `min_attainable_p = min(1.0, 2.0 / 2**n)`.
`battery/audit/discriminate.py:120` — the verdict ladder tests
`min_attainable_p > 0.05` **first**, before effect size:

```
n = 4  ->  2/16  = 0.125    > 0.05
n = 5  ->  2/32  = 0.0625   > 0.05
n = 6  ->  2/64  = 0.03125 <= 0.05
```

The development pile is fixed at **4 games** (`arc-recon/data/piles.json`; the
other 21 are sealed). Game-level pairing therefore caps `n` at 4, so
`min_attainable_p` is 0.125 for every metric that has data, so the
`underpowered` branch fires **unconditionally** and `discriminating` is
unreachable for all 38 metrics no matter what the data say.

**Consequence: the 0 is a property of the design, not a finding about the
metrics.** A rerun of the identical pass on the identical pile is guaranteed to
return 0 again. This is the single most important thing V22 has to say, and it
changes what the paper may claim in both directions: it is not evidence that
the metrics are bad, and it is not evidence that they are good.

`battery/STATUS.md` W-3 already states the p=0.125 ceiling for the model-ladder
pass; what was missing is that it also determines the cross-arm pass's headline
number, and that the monitor's "60%" for cell V3 was scoring a cell whose
maximum attainable score was 0.

## Step 2 — baseline

`python -m pytest battery -q` -> **319 passed**, 8.00s, at base commit
b60a1537 before any edit.

## Step 3 — fan-out (five subagents, independent contexts)

no-data root causes / power analysis / not-ranked provenance / arm inventory,
then one adversarial reviewer over the finished conclusions. Every load-bearing
number re-derived here before adoption. Two subagent findings changed the
deliverable:

* the honest denominator is **8**, not the 31 I first wrote (verified: 10
  metrics pair ≥2 games, 8 of those are rankable);
* the model-ladder pass **also** separates zero (verified: 18 no-data,
  13 underpowered, 7 not-ranked, 0 discriminating) — so the alternative
  gradient is not an escape.

## Step 4 — delivery

* `battery/docs.py` — new generated "Process 1" section in `METRICS.md`
  (generated, not hand-edited: the file forbids hand edits and
  `tests/test_docs.py` enforces it). Threshold derived, not hard-coded.
* `battery/STATUS.md` — W-13, stating separation power 0 and the paper wording.
* `battery/verify.py` — fourth rung, with an anti-staleness flip.
* `battery/tests/test_verify_separation_claim.py` — 15 tests, 8 mutants.

`python -m pytest battery -q` -> **334 passed**. `python battery/verify.py` ->
exit 0, four rungs green.
