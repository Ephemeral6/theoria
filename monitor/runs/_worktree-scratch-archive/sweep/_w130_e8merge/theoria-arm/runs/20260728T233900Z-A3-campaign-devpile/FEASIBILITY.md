# What a dev-pile campaign actually costs, measured — not estimated

Everything here is read off committed artifacts from P-8, the arm's only online
contact, plus baseline-arms' re-measured unit prices. No new spending.

## The binding constraint is wall clock, not money

From `theoria-arm/RUN_STATE.md` and `runs/20260728T015354Z-g50t-first-contact/`:

| quantity | measured |
|---|---|
| successful actions | 7 |
| HTTP commands | 40 (amplification 5.71) |
| model calls (theorize only) | 5 |
| cost | **$6.32** |
| wall clock | **~17 minutes per turn** |
| surprises | 8 (4 render_mismatch, 4 replay_mismatch) |
| levels completed | 0 of 7 |

The run was stopped from outside. It did not run out of money or actions — it
ran out of clock. **102 actions and roughly $10 of its own ceiling went
unspent.** Almost all of the 17 minutes sat in a single `claude -p` call that
returned 46,000 output tokens.

Scale that honestly. The ticket asks for three games (g50t / sk48 / tn36),
carrying books between them. At ~17 min/turn, even a thin 20-turn game is ~5.7
hours; three of them is **~17 hours of wall clock**, serialized, because the
books must be carried forward in order. That is not a session — it is a
multi-day campaign, and it is why RES-1 died holding this ticket rather than
finishing it.

**This is the single most important planning fact for A3 and it is not a
budget number.** Any plan that reasons only about dollars and action quota will
mis-scope by an order of magnitude.

## What P-8 actually established, and it is a negative result

The headline from the first-contact run is not the cost. Across four certify
rounds the count of unexplained pixels at frame 0 went **69 → 68 → 69 → 69**.

The manual oscillates. It does not converge. Four rewrites and $6.32 bought the
finding that *a loop re-theorizing against a defect its own language cannot
express will cycle*. Two fixes followed (a quantitative evidence gate in
`inner/loop.py`, and E-03 promoted to the top of the expressivity ledger), and
**neither of them is in that run** — so their effect is untested online.

That matters for A3's shape: the bill-shape prediction is 前重后轻,收敛后趋零
(front-heavy, then light, tending to zero after convergence). **A loop that does
not converge has no "after convergence".** If the oscillation reproduces, the
honest deliverable is a measured non-convergence curve, not a missing one — and
that is a result about the framework, which is exactly what Phase 3's scoreboard
(line 351) is built to read.

## The figure-2 pipeline already exists and I must not rebuild it

`figures/fig02_bill_shape.py` consumes, by discovery rule in `figures/sources.py`:

    theoria-arm/runs/<slug>/cost_curve.json   +   MANIFEST.json

Both are written by `python -m armtools.archive --slug <slug>`. A run dir with
only one of the two is **silently skipped**. The rule carries `floor=4` — the
build goes red if fewer than four qualifying dirs exist, because an empty glob
and an empty family look identical.

Consequences I have to respect rather than work around:

* `archive` is **not optional** for any campaign run.
* **One model per run** or the build raises (`calls span models`).
* `MANIFEST.outcome` must be non-null on completed runs, or the curve is drawn
  dotted as "billed and abandoned" while its cost still counts.
* `cost_curve.json` rows carry `label` = the theorize round (`round1`,
  `round2`) and `step_idx` = the turn. **Several calls share a `step_idx`; the
  turn's cost is the sum.** So theorize-rounds-per-turn and the per-turn cost
  curve — two of the ticket's three columns — already have a home.
* The seven surprise counters live in `MANIFEST.json → surprises`
  (`by_family` / `by_kind` / `total` / `unhandled`), also already written by
  `archive`. **No figure currently reads them** — they are manifest facts only.
  So the ticket's third column exists but is not yet plotted.

### The one thing the campaign cannot produce by itself

E2 (front-load index) / E3 (convergence point) / E4 (context-growth fit) are
**read, never recomputed** — from `battery/artifacts/capability_spectrum.json`,
defined in `battery/metrics/economy.py`, keyed by `run_id`. Battery v2's five
arms are `bare_cc`, `schema_repro`, `theoria_a0`, `theoria_a0_spike`,
`theoria_a2`. **The live ARC theoria arm is none of them, and there is no
live-theoria adapter.**

So a new live run lands with `e2_status = no-battery-run` — drawn as an absence
with its reason, never as a zero. Getting real E2/E3/E4 needs a ledger meeting
`battery/INPUT_FORMAT.md` plus a new adapter. The figures track states the rule
plainly and I agree with it: **do not recompute the metrics in plotting code —
a second implementation of a primary endpoint is a second definition**, and E2
is one of Phase 4's three primary endpoints.

Two axis caveats already recorded upstream and still unresolved: battery counts
turns in model-call order while fig02 counts `step_idx` (so `axis_agrees` will
likely be false for this arm and E3 will be reported but not marked — that is
design, not a hole); and `support["turns"]` in `economy.py` is two different
quantities depending on which metric reads it.

## Standing hazards a campaign must not walk into

* **INC-TA-001 (high).** Two arms played g50t concurrently on one quota on
  2026-07-28. Every wall-clock and amplification number from that run is an
  **upper bound, not a measurement**. The proposed fix — a cross-session lock
  under `arc-recon/` that any arm must take before opening a scorecard — was
  never built, because `arc-recon/` is read-only ground. **The hazard is still
  live**, and this repo runs concurrent sessions by design.
* **INC-TA-002.** Live ARC command responses carry no `score` field, so
  `Theoria.md` line 291's reconciliation obligation (ledger score == scorecard
  score) is **undischargeable**; `archive.py` reconciles `levels_completed` and
  action count instead and reports `score_reconciliation: "unavailable"`.
* **INC-TA-003.** `proxy/cost.py` under-bills 1-hour cache writes by 6.8%
  (reads flat `cache_creation_input_tokens`, never the nested
  `ephemeral_1h_input_tokens`). Auto-diagnosed into every MANIFEST.
* **INC-TA-005 (high for measurement).** Every `claude -p` is a fresh process in
  a fresh temp dir (that *is* the sealing, D-P8-013), so cache reads are
  **structurally zero**. `Theoria.md` §1.12's distinguishing column is 单局缓存读
  and **this arm cannot report a number in it.**
* **GAP 1.** The model side is recorded but **not proxied** (`claude -p`, not
  `proxy/model_proxy.py`). No conclusion about input-token composition may be
  drawn from this ledger.
* **GAP 2.** `plan` returns `no_goal_declared` almost always, so `commit` rarely
  has a script and the `execution_mismatch` counter is **structurally zero, not
  measured-zero**. One of the seven surprise counters is therefore not
  informative, and reporting it as a plain 0 beside the others would repeat
  exactly the error E14 just finished fixing ("crash is not a finding").
* **Transport changed mid-history.** The cookie jar landed between ar25 and
  g50t; `BUDGET_REPORT.md` §2.1's HTTP/action 7.11 and all §3 extrapolations are
  too high by ~2–7×. Re-derived unit prices (jar-on): haiku $0.0435/action,
  opus $0.1460, sonnet $0.1793. Unexplained: `$/model call` rose 53–68% across
  all three tiers and **the cause is recorded as undetermined**.
* Across 27 measured cells, `levels_completed` is **0 everywhere**. Every cost
  projection in the repo is a lower bound on cost and says nothing about
  capability.
