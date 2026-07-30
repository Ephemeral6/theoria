# S42 · measured facts

Every number here was produced by running something. The pre-fix column comes
from a scratch copy of the package in a tempdir with `board.py`, `__init__.py`
and `verify.py` restored from `7972a075` — the tree under test was never
modified to produce a "before".

## 1. `cmd_sweep` frees the claims of workers that are still running

Reproduction, S40's technique: `subprocess.run` is replaced with one returning
a synthetic `schtasks /Query /FO CSV /NH` table, encoded in the **console code
page** (not UTF-8 — that substitution is `KNOWN_TRAPS.md` entry 1's other
half). Two claims are on the board.

```
"\SweepProbe-W-777","2026-07-30 12:00:00","Running"
"\SweepProbe-W-888","2026-07-30 12:00:00","Ready"
```

| | `claimed/` after `cmd_sweep()` | verdict |
|---|---|---|
| pre-fix (`7972a075`) | `[]` | **both freed**, including the Running worker |
| post-fix | `["T1-live.W-777.md"]` | only the Ready worker freed |

Pre-fix stdout, verbatim:

```
SWEEP T1-live released (worker W-777 gone)
SWEEP T2-dead released (worker W-888 gone)
```

`W-777` is Running in the table it just read.

**The discriminating run.** Same CSV, same claim, two configs. Under
`task_prefix="SweepProbe-"` the claim survives; under
`task_prefix="DifferentFleet-"` it is freed. Nothing else varies, so the
decision is demonstrably coming from `fleet.json` — which is exactly what could
not be said of a literal that was never assigned.

**The third value.** With no `fleet.json` anywhere above the tree: pre-fix
`cmd_sweep()` returns 0 having freed every `W-*` claim; post-fix it returns 3
and frees nothing (`SWEEP-REFUSED`). Same for a `schtasks` query that exits
non-zero — pre-fix there was no branch at all, so a failed query gave empty
stdout, which is byte-identical to "nobody is running".

## 2. A `lane:` item is unreachable by construction

`list` on a board holding one `lane: campaign` item and one `spend: api` item,
with a third item's territory held by a live claim:

```
pre-fix:
  === available (通用工人可领 0) ===
  === blocked ===
    C1-waiting                   waits on Z9-never
  === claimed ===
    B1-held                      by W-1
```

`A1-costly` and `B2-blocked-by-territory` appear nowhere; the lane-tagged item
appears nowhere. Post-fix all four items are named, the lane-tagged one under
`available` with tag `lane:campaign`, the other two under `withheld` with a
reason each.

Counted occurrences of `LANE_OWNER` in the pre-fix package: **4** — one
assignment (`board.py:50`), three reads (`:77`, `:203`, `:206`). No `.update`,
no `setdefault`, no monkeypatch, none in `tests/`, none in `verify.py`.
`fleet.json` occurs in the repository **0** times as a file.

Post-fix: `LANE_OWNER` occurs **0** times, `stale_lanes` **0** times.

## 3. `python -m fleetkit init --prefix MyFleet-`

```
pre-fix : No module named fleetkit.__main__;
          'fleetkit' is a package and cannot be directly executed   (exit 1)
post-fix: wrote <root>\fleet.json
          task_prefix=MyFleet- territories=src,docs                 (exit 0)
```

**The gate on top of it.** Against the *identical* pre-fix package:

| gate | verdict |
|---|---|
| `verify.py` at `7972a075` | `fleetkit: green` (exit 0) |
| `verify.py` after S42 | `fleetkit: RED (1 problem(s))` (exit 1) |

The new gate's failure line is the user's error message verbatim:
`the documented entry point 'python -m fleetkit init --prefix GateProbe-'
failed (exit 1): ... No module named fleetkit.__main__`. That pair — same code,
old gate green, new gate red — is the measurement for "a gate that cannot see a
broken front door".

Rung 3 additionally asks the board what prefix it *would* sweep with and
compares it to the file. Pre-fix those two values were `""` and `"GateProbe-"`
and the gate compared the file to itself.

## 4. Encoding

`bus.py:144` emitted `U+26A0` when any agent had an unread URGENT.
`'\u26a0'.encode('cp936')` raises `UnicodeEncodeError`, so `bus status` died
mid-output exactly when it had something urgent to say. Every character in
every file touched by this item now encodes in cp936 (checked over
`fleetkit/**/*.py`, `fleetkit/*.md`, `monitor/tests/test_fleetkit_drift.py`:
**0** offending characters).

## 5. Test counts

| suite | before | after |
|---|---|---|
| `fleetkit` (`python -m pytest`) | 6 passed | **31 passed** |
| `fleetkit/verify.py` | green (on broken code) | green (through the CLI) |
| `monitor/tests/test_fleetkit_drift.py` | 12 passed (S40 branch) | **13 passed** |
| `monitor/tests` (whole) | 5 failed, 392 passed (397 collected) | 5 failed, 405 passed (410 collected) |

The 5 monitor failures are pre-existing on `origin/master` at `7972a075` and
are untouched by this branch — 2 in `test_scan_no_third_value.py`, 3 in
`test_standing_reflex_no_third_value.py`. Recorded before any file was edited.

### The three new files, run against the pre-fix package

| file | pre-fix | post-fix |
|---|---|---|
| `test_sweep_does_not_free_live_claims.py` | 7 failed | 7 passed |
| `test_lane_items_are_reachable.py` | 7 failed, 3 passed | 10 passed |
| `test_documented_entry_point.py` | 8 failed | 8 passed |

The 3 that pass pre-fix in the lane file are the two schema assertions and the
`list`-encoding one, which were already true; they are companion greens, not
padding.

### The amended drift table, run against the pre-fix package

`monitor/tests/test_fleetkit_drift.py` as amended, with `fleetkit/board.py`
restored to `7972a075`: **3 failed, 10 passed**
(`test_the_measured_divergence_count_is_pinned`,
`test_lane_ownership_is_gone_from_fleetkit`,
`test_fleetkits_sweep_reads_a_prefix_instead_of_shipping_an_empty_one`).

That matters: it shows the DECLARED table was re-measured rather than edited to
agree with whatever the code now says.

## 6. The divergence table after the fixes

Recomputed with `ast`, normalised source, same method as S40:

| | S40 | after S42 |
|---|---|---|
| shared top-level functions | 18 | **17** (`stale_lanes` deleted) |
| divergent by source | 8 | 8 |
| byte-identical yet divergent | 2 (`stale_lanes`, `territories_busy`) | **1** (`territories_busy`, through `meta`) |
| behavioural total | 10 | **9** |
| fleetkit-only functions | 0 | 2 (`config_root`, `task_prefix`) |

The divergent-by-source set is unchanged in membership: `candidates`,
`cmd_claim`, `cmd_list`, `cmd_release`, `cmd_sweep`, `heartbeat_age`, `main`,
`meta`. What changed is why three of them diverge — `cmd_sweep` moved from
`defect` to `stale`, and `candidates`/`cmd_list` now diverge partly on purpose.
