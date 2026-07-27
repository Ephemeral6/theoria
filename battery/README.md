# battery — Theoria Phase 2, the metrics battery

> 分数上限已被拔到 98.98——天花板上没有分辨率。能力差异没有消失，只是从
> "赢没赢"搬进了"怎么赢"，藏在轨迹里。 — `Theoria.md` Phase 2

Score has run out of resolution, so this reads the *trajectories* instead. Same
ledger, second use: the scorer reads it and gets a number; the battery reads it
and gets a capability spectrum.

**Passive by construction.** It opens files. No API calls, no model calls, no
network, no new game spend. Everything it reads already exists.

```bash
python -m battery.run_battery            # recompute everything -> battery/artifacts/
python -m pytest battery/tests -q        # 61 tests
python -m battery.docs                   # regenerate METRICS.md from the registry
```

## What is here

| file | what |
|---|---|
| [`METRICS.md`](METRICS.md) | the 29 metrics, generated from the code |
| [`PREDICTIONS.md`](PREDICTIONS.md) | directional pre-registration — **append-only** |
| [`REPORT_V0.md`](REPORT_V0.md) | what the first full recompute found |
| [`INPUT_FORMAT.md`](INPUT_FORMAT.md) | the normalised record, and gaps to raise against `proxy/LEDGER_FORMAT.md` |
| [`DECISIONS.md`](DECISIONS.md) | design calls and their reasons |
| [`STATUS.md`](STATUS.md) | milestone state and open weaknesses |
| `guard.py` | the sealed-pile guardrail |
| `adapters/` | source → normalised run |
| `metrics/` | the five families |
| `audit/` | discrimination, redundancy, anti-gaming |

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
2. **Directional pre-registration** — `PREDICTIONS.md`, written and committed
   before any metric code existed. Its git commit is the evidence.
3. **De-redundancy** — Spearman clustering; twenty correlated numbers are not
   twenty findings.
4. **Anti-gaming audit** — per metric, how would an arm cheat it, and could it
   do so *by accident*? Demotion to the reference tier is applied by code, not
   decided while writing the report.

## Red lines

* **Sealed games are refused**, by full id, by de-suffixed short id, and
  case-insensitively. So are ids in neither pile. `guard.py` also recomputes
  `piles.json`'s published digest on every load and refuses to score anything
  if the cut has drifted; every artefact carries the digest it verified.
* **Determinism.** Two recomputes over unchanged inputs are byte-identical.
  No wall clock in any artefact; input digests instead. Statistics are
  hand-rolled rather than scipy so the arithmetic is the same everywhere.
* **No network.** Nothing here opens a socket.
