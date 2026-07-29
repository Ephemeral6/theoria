# Per-world index — V7

One row per world, one report per world. `theory` is this run's instrument;
`prior` is the eight-line theory-free strategy from `prior_sweep.py` scored through
the real marker. **Where `prior` is 1.000 the world ranks nobody**, whatever the
`theory` column says — that gap between the two columns is the run's main result.

| world | tier | items | free | mem | theory | floor | prior | changed taken | barren rules | report |
|---|---|---|---|---|---|---|---|---|---|---|
| `t1-walk-maze` | 1 | 8 | 4 | 2 | 2 | 0.500 | **1.000** | 4/4 | `blocked_by_wall` | [report](t1-walk-maze.report.md) |
| `t1-push-open` | 1 | 12 | 4 | 4 | 4 | 0.333 | 0.667 | 4/8 | `blocked_by_wall` | [report](t1-push-open.report.md) |
| `t1-push-corridor` | 1 | 8 | 4 | 2 | 2 | 0.500 | **1.000** | 4/4 | `blocked_by_wall` | [report](t1-push-corridor.report.md) |
| `t1-switch-toggle` | 1 | 8 | 4 | 2 | 2 | 0.500 | **1.000** | 4/4 | `blocked_by_wall` | [report](t1-switch-toggle.report.md) |
| `t1-switch-latch` | 1 | 12 | 4 | 4 | 4 | 0.333 | **1.000** | 8/8 | `blocked_by_wall` | [report](t1-switch-latch.report.md) |
| `t1-portal-oneway` | 1 | 8 | 4 | 2 | 2 | 0.500 | **1.000** | 4/4 | `blocked_by_wall` | [report](t1-portal-oneway.report.md) |
| `t1-cycler-gate` | 1 | 8 | 4 | 2 | 2 | 0.500 | **1.000** | 4/4 | `blocked_by_wall` | [report](t1-cycler-gate.report.md) |
| `t1-tokens-lock` | 1 | 12 | 4 | 4 | 4 | 0.333 | 0.917 | 7/8 | `blocked_by_wall` | [report](t1-tokens-lock.report.md) |
| `t1-fragile-bridge` | 1 | 8 | 4 | 2 | 2 | 0.500 | **1.000** | 4/4 | `blocked_by_wall` | [report](t1-fragile-bridge.report.md) |
| `t2-switch-push` | 2 | 24 | 8 | 8 | 8 | 0.333 | 0.500 | 8/16 | `blocked_by_block, blocked_by_wall` | [report](t2-switch-push.report.md) |
| `t2-portal-pair` | 2 | 8 | 4 | 2 | 2 | 0.500 | **1.000** | 4/4 | `blocked_by_wall` | [report](t2-portal-pair.report.md) |
| `t2-portal-paired` | 2 | 8 | 4 | 2 | 2 | 0.500 | **1.000** | 4/4 | `blocked_by_wall` | [report](t2-portal-paired.report.md) |
| `t2-gravity-push` | 2 | 8 | 5 | 2 | 1 | 0.625 | 0.875 | 3/3 | `blocked_by_wall` | [report](t2-gravity-push.report.md) |
| `t2-lock-fragile` | 2 | 12 | 4 | 4 | 4 | 0.333 | **1.000** | 8/8 | `blocked_by_wall` | [report](t2-lock-fragile.report.md) |
| `t2-cycler-lock` | 2 | 12 | 4 | 4 | 4 | 0.333 | **1.000** | 8/8 | `blocked_by_wall` | [report](t2-cycler-lock.report.md) |
| `t2-unsolvable-nodoor` | 2 | 12 | 8 | 2 | 2 | 0.667 | 0.667 | 4/4 | `blocked_by_door, blocked_by_wall` | [report](t2-unsolvable-nodoor.report.md) |
| `t3-full-house` | 3 | 24 | 8 | 8 | 8 | 0.333 | 0.333 | 4/16 | `blocked_by_block, blocked_by_wall` | [report](t3-full-house.report.md) |
| `t3-gravity-fragile` | 3 | 8 | 4 | 2 | 2 | 0.500 | **1.000** | 4/4 | `blocked_by_wall` | [report](t3-gravity-fragile.report.md) |
| `t3-cycler-portal-lock` | 3 | 16 | 4 | 6 | 6 | 0.250 | 0.750 | 8/12 | `blocked_by_wall` | [report](t3-cycler-portal-lock.report.md) |
| `t3-latch-maze` | 3 | 20 | 8 | 6 | 6 | 0.400 | 0.750 | 11/12 | `blocked_by_wall, latch_already_set` | [report](t3-latch-maze.report.md) |

**Totals** — 236 items: 97 free, 70 memorised, 69 theory, 0 dead, 0 anomalies. Zero-discrimination share 0.411. Barren everywhere: `blocked_by_block`, `blocked_by_door`, `blocked_by_wall`, `latch_already_set`.

**The prior** takes 109 of 139 frame-changing items (78.4%), scores 1.000 on 12 of 20 worlds and beats the bluffer floor on 18. The two it does not beat — `t3-full-house` and `t2-unsolvable-nodoor` — it *ties* at the floor while answering a different set of items, so the score is not monotone in how much world model an examinee holds.
