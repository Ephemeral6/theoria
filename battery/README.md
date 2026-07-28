# battery — Theoria Phase 2, the metrics battery

> 分数上限已被拔到 98.98——天花板上没有分辨率。能力差异没有消失，只是从
> "赢没赢"搬进了"怎么赢"，藏在轨迹里。 — `Theoria.md` Phase 2

Score has run out of resolution, so this reads the *trajectories* instead. Same
ledger, second use: the scorer reads it and gets a number; the battery reads it
and gets a capability spectrum.

**Passive by construction.** It opens files. No API calls, no model calls, no
network, no new game spend. Everything it reads already exists.

```bash
python -m battery.run_battery            # 31 runs, 4 arms, 38 metrics -> battery/artifacts/
python -m pytest battery/tests -q        # 117 tests
python -m battery.docs                   # regenerate METRICS.md from the registry
```

## What is here

| file | what |
|---|---|
| [`METRICS.md`](METRICS.md) | the 38 metrics, generated from the code, with a 验证材料 column |
| [`PREDICTIONS.md`](PREDICTIONS.md) | directional pre-registration — **append-only** |
| [`REPORT_V1.md`](REPORT_V1.md) | **what the current recompute found** |
| [`REPORT_V0.md`](REPORT_V0.md) | what the first one found, kept as written |
| [`INPUT_FORMAT.md`](INPUT_FORMAT.md) | the normalised record, and gaps to raise against `proxy/LEDGER_FORMAT.md` |
| [`DECISIONS.md`](DECISIONS.md) | design calls and their reasons |
| [`STATUS.md`](STATUS.md) | milestone state and open weaknesses |
| `guard.py` | the sealed-pile guardrail |
| `adapters/` | source → normalised run — ledger, A0, a0-spike, A2 |
| `metrics/` | the five families |
| `audit/` | discrimination, contrast, validation material, redundancy, anti-gaming |

## The artefacts, and which one answers what

| file | question |
|---|---|
| `capability_spectrum.json` | every metric on every run, plus provenance and what was deliberately *not* read |
| `discrimination.json` | **process 1.** Control arms only — the pass that licenses a metric |
| `arm_contrast.json` | bare CC against the Theoria arms. A **result**, not a validation; every entry carries `confounded_by_world` |
| `validation_material.json` | what each metric's validation actually rests on. Feeds `METRICS.md`'s 验证材料 column |
| `redundancy.json` | clusters **and the full pairwise basis** — every ρ with the run count behind it |
| `gaming_audit.json` | how each metric would be cheated, and the tier that follows mechanically |

## The five families

| family | asks |
|---|---|
| 探索 exploration | systematic, or circling? |
| 计划 planning | is a decision buying more actions over time? |
| 经济 economy | the shape of the bill — front-loaded, or flat forever? |
| 机制 mechanism | how long between seeing a rule and using it? |
| 认识 epistemic | the quality of the two books themselves |

## The four processes the battery runs on itself

1. **Discriminative power** — a metric that cannot separate a *known* capability
   gradient has no business measuring an unknown one. Validated on control arms
   only, never on Theoria, so the instrument cannot be tuned to flatter the
   framework it tests.
   *Status:* every verdict is still `underpowered` at 4 paired games, and **21
   of 38 metrics have never been computed on a control arm at all** — the whole
   epistemic and mechanism families. For those, process 1 is not un-run; it is
   currently impossible.
2. **Directional pre-registration** — `PREDICTIONS.md`, written and committed
   before any metric code existed. Its git commit is the evidence.
   *Status:* the v1 seal is weaker than v0's and says so — the recon passes that
   preceded it quoted values, so most v1 rows are marked `[seen]`. The fix for
   v2 is registered in the same file.
3. **De-redundancy** — Spearman clustering; twenty correlated numbers are not
   twenty findings. The full pairwise basis is emitted, not just the verdict.
   *Status:* first run with enough data to bite — it merged one of v1's own new
   metrics into the one it was supposed to replace.
4. **Anti-gaming audit** — per metric, how would an arm cheat it, and could it
   do so *by accident*? Demotion to the reference tier is applied by code, not
   decided while writing the report.
   *Status:* two v1 metrics failed in exactly the manner their own register
   predicted, in the same recompute that introduced them.

## Red lines

* **Sealed games are refused**, by full id, by de-suffixed short id, and
  case-insensitively. So are ids in neither pile. `guard.py` also recomputes
  `piles.json`'s published digest on every load and refuses to score anything
  if the cut has drifted; every artefact carries the digest it verified.
* **Determinism.** Two recomputes over unchanged inputs are byte-identical.
  No wall clock in any artefact; input digests instead. Statistics are
  hand-rolled rather than scipy so the arithmetic is the same everywhere.
* **No network.** Nothing here opens a socket.
