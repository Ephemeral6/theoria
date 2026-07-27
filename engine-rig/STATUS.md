# engine-rig · STATUS

Live status of the engine rig track. Milestones are git tags; each one also
appends a paragraph to `/PARTNER_SYNC.md`.

## Milestones

| Tag | Scope | State |
|---|---|---|
| `engine-rig-m1-fixtures` | Fixtures A/B/C, deterministic generators | done |
| `engine-rig-m2-mdl` | `mdl_segmenter` | done |
| `engine-rig-m3-cegis` | `cegis_miner` | done |
| `engine-rig-m4-zerospace` | `zero_space` | done |
| `engine-rig-m5-lp` | `lp_potential` | done |
| `engine-rig-m6-fd` | `fd_adapter` | done (stub backend — see below) |
| `engine-rig-m7-probe` | `probe_frontier` | done |
| `engine-rig-m8-integration` | all six engines + schema validator | done |

All eight milestones are reached. `python -m tools.run_all --force` runs the six
engines end to end and emits 24 candidates, every line of which passes the frozen
schema validator. That stream is committed at `artifacts/candidates.jsonl`
(deterministic mode, so it is byte-stable and cannot drift unnoticed).

## Test suite

161 passed, 1 skipped (`test_fast_downward_agrees_with_the_stub`, which starts
running the moment a Fast Downward executable is reachable).

## Convergence interface (post-M8)

`engine-rig/interop/` exports LP-solved pagoda certificates for the
theory-compiler track, which asked for them in its M8 note. Headline finding:
their peg fixture's stated goal (`count(Peg, alive=true) = 1`) admits **no** linear
pagoda certificate, although the unsolvability claim itself is true and two
narrowed goals (target cell 1 or 3) do get certificates. See
`interop/README.md`.

## Blockers

None. The one deviation from the ticket's ideal is the Fast Downward stub,
covered below and sanctioned by the ticket.

## Fast Downward

**FD is not connected; the stub is in use.** This is the outcome the ticket
allows after two reasonable attempts. Both attempts, verbatim:

1. **Discovery.** Searched PATH for `fast-downward`, `fast-downward.py`,
   `downward`, `fd`, `planner`; checked `FAST_DOWNWARD`, `FAST_DOWNWARD_HOME`,
   `DOWNWARD_ROOT` and any `*downward*` environment variable; checked
   `C:\Program Files\fast-downward`, `C:\fast-downward`, `~/fast-downward`,
   `~/downward`, `/opt/fast-downward`, `/usr/local/lib/fast-downward`; checked
   for importable `downward`, `fast_downward`, `pyperplan`, `unified_planning`
   packages. Nothing found.
2. **Install.** `pip install downward` and `pip download fast-downward` both
   fail with "No matching distribution found" — Fast Downward is a C++ project
   distributed as source, not on PyPI. Building it from source would need a
   repository clone plus a C++ toolchain and CMake, which is outside both "two
   reasonable attempts" and this sprint's offline constraint.

**Substitute.** `engines/fd_adapter/search.py` is a breadth-first search over
grounded STRIPS behind the same `solve(domain, problem)` interface. BFS is
length-optimal for unit costs, exactly like the `astar(blind())` configuration
the FD path would use, so the acceptance criterion ("plan length equals the
hand-verified optimum") means the same thing under either backend. Each plan
records which backend produced it in `payload.backend`.

The Fast Downward code path (discovery, invocation, `sas_plan` parsing) is
implemented and **unexercised**. `test_fast_downward_agrees_with_the_stub` is
skipped here and starts running the moment an FD executable is reachable.
