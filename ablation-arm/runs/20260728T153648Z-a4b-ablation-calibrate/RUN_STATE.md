# RUN_STATE — A4b · ablation-arm calibration

`prompt_id: A4b-ablation-calibrate` · branch `agent/a4b-ablation-calibrate` ·
base `e46e7fe` · started 2026-07-28T15:36:48Z · **offline, zero API, zero dollars**

Written as the work went, not at the end.

---

## 0 · What I found before running anything

`STATUS.md` in this directory is **stale**. It says the arm "has never been run"
and lists `worlds/`, `exhibits/`, `theory/`, `tests/`, `verify.sh` and
`artifacts/` as missing. All of them now exist: A4a (`agent/a4b`'s predecessor
item, run dir `runs/20260728T130500Z-A4a-ablation-build/`) built them. STATUS is
left alone — it is A4's file and correcting it is not this item's business —
but the discrepancy is recorded here so the next reader does not trust it.

The split A4a left for A4b is written down explicitly in `verify.py`'s
docstring: of the seven pre-registered predictions, A4a asserts P-3, P-6, P-7 and
the *correct* half of P-5; it **records** P-1, P-2, P-4 and the *identical* half
of P-5 under a heading that says nobody has compared them yet. **Settling those
four is exactly this item's job**, and the work order's four quantities map onto
them one for one:

| work order asks for | prediction it settles |
|---|---|
| replay accuracy | P-1 |
| score | P-2 (and P-5's identical half) |
| theorize rounds | — (no prediction; the honest answer is a gap, see §3) |
| cost | P-4 |

## 1 · Baseline runs (all green before any new code)

```
python ablation-arm/run_arm.py      -> 5 worlds, upstream unchanged (468 files hashed)
cd ablation-arm && python -m pytest -q  -> 56 passed
bash ablation-arm/verify.sh         -> GREEN, exit 0
```

`verify.sh` did **not** hit the `read-only` / `proxy/var/spend_gate.jsonl`
defect the work order warned about. `read-only ok`.

## 2 · Where the full arm's counterparts live

Found by reading, not assumed:

| quantity | full arm's file |
|---|---|
| A0 replay (cheap layer) | `cold-start-a0/artifacts/certify_cheap_raw_trace.json` |
| A0 score vs ground truth | `cold-start-a0/artifacts/score_vs_truth.json` |
| A0 verdict + certificate | `cold-start-a0/artifacts/plan_generated.json`, `unsolvable_report.json` |
| A0 Lean (expensive layer) | `cold-start-a0/artifacts/certify_lean_generated_theory_lean.json` |
| A2 holed exhibit | `cold-start-a2/artifacts/exhibit_report.json` |
| A2 loop after the refutation | `refutation.json`, `locate_report.json`, `probe_report.json`, `repair_report.json`, `plan_repaired.json`, `loop_ledger.json` |

`theoria-arm/runs/` holds the full arm's **live ARC** runs (g50t). Those are a
different world with a real dollar ledger and are **not** an A0 counterpart;
noted so the absence is a decision rather than an oversight.

## 3 · The gap I hit first, and it is the important one

**The ablated arm never theorized.** `build_theory.py` builds its manuals by
mechanically downgrading the full arm's DSL
(`cold-start-a0/theory/theory.dsl` → `theory/a0_base.dsl`, laws section
demoted, theorems deleted — `theory/DOWNGRADE_REPORT.json` records the delta
file by file with both sha256s). That is A4a's design choice and it is the
right one — a re-theorized manual would be a second difference and
`Theoria.md:280` says a second difference makes the first unattributable — but
it means **"theorize rounds" is not a quantity on which the two arms can be
compared on these worlds.** Recorded as `not_comparable` with the reason,
not as a number. See REPORT.md §3.

Consequence that must not be blurred: equal replay accuracy and equal score are
**partly by construction**, because the two arms hold the same manual. What they
show is that the incision did not damage the representation layer (which is what
P-1/P-2 were pre-registered to test) — not that the ablated arm *induces* as
good a manual. Stated in the report in those words.

## 4 · Cost — choosing the unit

Dollars is unavailable and would be a lie in either direction: neither arm spent
any on A0/A2, both cold starts are offline, and no proxy ledger was ever written
for either (`proxy/var/` is empty; `grep -rl 'cost_usd' cold-start-a0
cold-start-a2` finds only prose). So cost is reported in **three units that are
actually measured on these runs**, each defended in REPORT.md §4:

1. **certification fuel — Lean elaboration seconds.** Lean 4 is installed
   (`~/.elan/bin/lean.exe`) and the full arm's `theory.lean` files are on disk,
   so this is measurable now rather than inferred. Measured on a *copy* in a
   temp dir so the upstream tree is not touched.
2. **proof-artefact bytes** — `theory.lean` bytes emitted. Byte-exact,
   deterministic, zero interpretation.
3. **world interactions spent on probes** — the currency that transfers to the
   wild, where every step is an API call. The full arm's A2 repair loop grew the
   trace 184 → 196 frames; the ablated arm spends 0.

## 5 · What I built

`calibrate.py` → `artifacts/calibration.json`. It reads both arms' artefacts,
computes the ablated arm's score with the **full arm's own scorer**
(`cold-start-a0/certify/score_vs_truth.behavioural` / `held_out`, imported as a
library function, never its `main()` which writes), times Lean on copies, and
emits the side-by-side table plus the A2 fork. `tests/test_calibration.py`
pins the claims the report makes.

## 6 · Progress log

* 15:36 — orientation done; baseline runs green; run dir opened.
* 15:52 — `calibrate.py` written; first run.
* 16:05 — **A2 fork measured**: full arm proves `unsolvable` axiom-free, then is
  refuted by its own witness and repairs to SAT/18; ablated arm settles the same
  UNSAT bare and archives it. Both from artefacts, no prose.
* 16:20 — Lean timing collected on copies; upstream hash unchanged either side.
* 16:35 — `REPORT.md` written; pytest and verify.sh re-run.
