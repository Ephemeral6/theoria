# E9 · the eight processes, collected into one table

Work order: `monitor/board/claimed/E9-engine-paper-table.RES-3.md`. Deliverables
are `engine-rig/ENGINE_TABLE.md` and its generator `engine-rig/tools/engine_table.py`.
**No engine was modified** — the manifest records zero code bytes changed under
`engines/`. Nothing outside `engine-rig/` was written.

## What was actually built

A table of eight rows — `mdl_segmenter`, `cegis_miner`, `zero_space`,
`lp_potential`, `fd_adapter`, `probe_frontier`, `deadlock_carver`, `ic3_pdr` —
with the five columns the work order named: what it solves, the fixture it was
validated on, how the claim was re-checked, and its known boundary.

**The eight were not invented.** `engine-rig/engines/` holds exactly these eight
directories; `STATUS.md`'s milestone table runs M1–M9 and says the run-all path
"runs the eight engines end to end"; the committed candidate stream carries the
two newest under `payload.producer` (D-018), 17 rows for `deadlock_carver` and 1
for `ic3_pdr`, because the frozen `engine` enum names only the original six.

## The discipline that shaped the generator

The work order asked for a script that regenerates the table from `runs/`
rather than one that prints a hardcoded table. What that means here:

* Every cell value is **probed** out of an artifact — a JSON field, a JSONL
  aggregate, or a regex anchored in a run's Markdown report. The prose in `ROWS`
  contains `{fact.key}` placeholders and no bare figures.
* The `expect` beside each probe is a **tripwire, not a source**. If an artifact
  is edited, `probe() != expect` and the script refuses to write.
* **The verdict is wired to the exit code.** Today's whole-repo sweep found that
  the commonest defect in this repository is a verdict computed correctly and
  then connected to nothing, so this script has five negative controls proving
  its own "no" is reachable (`measured/negative-controls.txt`):

  | control | expected | got |
  |---|---|---|
  | a fact disagrees with its artifact | 1 | 1 |
  | an artifact is missing | 3 | 3 |
  | the committed table is stale (`--check`) | 1 | 1 |
  | the table references a fact that does not exist | 3 | 3 |
  | a row is given an empty boundary cell | 3 | 3 |

  Exit 3 is kept apart from exit 1 deliberately, for the reason D-024 and D-031
  had to learn twice: a checker that fell over must not share a return value
  with a checker that returned a verdict.

98 facts, 19 artifacts, 6 runs.

## Measured, twice each

* `python -m tools.engine_table` — run twice, `ENGINE_TABLE.md` **byte-identical**
  (`sha256 22564de1…10512` both times). `--check` returns 0.
  Transcript: `measured/engine_table.twice.txt`.
* `python -m pytest` — **315 passed, 9 skipped**, twice.
  Transcript: `measured/pytest.twice.txt`. (`STATUS.md` still says 309; the nine
  skips are Fast Downward's, as documented — `.toolchain/` is gitignored and this
  machine has no build.)

## The boundary column, which is the point of the exercise

One row is **边界未测** outright: `ic3_pdr`. It has one certificate, on one
configuration of one 16-state fixture, and no property module in the fuzz
battery at all — so none of the 500-world campaign, none of the 55 mutants and
none of the 111-field publication census touches it. That row states what
measuring it would take and names the open item (`monitor/board/items/E8-ic3-scale.md`),
whose own wording is the right summary: there is one point, so no line can be
drawn.

Four further rows carry a **partially** unmeasured boundary, and each says so in
the same words rather than trailing off:

* `fd_adapter` — the property battery has never run against any Fast Downward
  rung, and the fall-back is *structural* (`backends.py:152-154` forces
  `stub-bfs` for the `solve_parsed` call shape) rather than a fact about this
  machine. So the stub-versus-real-FD difference is unmeasured, and measuring it
  needs a change to `props` **and** a build.
* `lp_potential` — for 638 of the 639 genuine silences, "no linear pagoda
  exists" is HiGHS returning float infeasibility. No exact Farkas dual was
  produced, so that is a solver's claim and not a proof.
* `cegis_miner` — minimal guards of 4+ literals, and every world family but the
  grid.
* `probe_frontier` — the planner-backed path (`run_with_planner` /
  `ExecutableProbe`) has no brute-force comparison at all.

## Two numbers that move against the rig's own interest

Both were checked back to their source rather than taken from circulation.

1. **`lp_potential`'s incompleteness is 639/2189 = 29.2 %, not 46 %.** The
   circulating 46 % (46.6 % at the campaign's N=500) is the *no-certificate*
   rate. 24.0 pp of it is the engine correctly declining to prove a false
   statement — the goal was reachable. Quoting 46 % as incompleteness overstates
   the boundary by about 2×.
2. **`deadlock_carver`'s pruning dividend is zero against an admissible
   heuristic.** On `far6`: blind 3070 → 2762, `lmcut` 47 → 47, `ipdb` 18 → 18.
   Theoria 1.9's frequency argument stands; its speed-up half does not survive a
   real planner.

## Corrections made to the inputs while building this

Recorded because they are the kind of thing that gets silently absorbed.

* **`CROSSCHECK.md`'s `zero_space` headline conflates two populations.** It
  reads `space_dimension = 366 / difference_rank = 4 / n_features = 370` with
  "2911 such rows in `theoria-arm`". Counted from the artifact, `theoria-arm`
  holds 2911 `zero_space` rows across **three** g50t files (two of them aborted
  runs), and only 1098 of those carry (366, 4). Inside the one completed run,
  `20260728T015354Z-g50t-first-contact`, there are 1821 rows in three groups:
  (365 features, 362 dims, rank 3, coverage 5/5) × 724, **(370, 366, rank 4,
  coverage 6/6) × 732**, and (370, 365, rank 5, coverage 7/7) × 365. The table
  quotes the modal group of the completed run and says which run it is. The
  `ADVERSARIAL-zero_space.md` figure (362 / 365 / rank 3) is the *other* group of
  the same file, and is also correct.
* **`STATUS.md` understates the forgery catalogue.** It says "25 forgeries, 24
  refused and one that works"; `E5/recheck_report.json` records 31 attempts and
  `n_accepted: 2`. The table takes the artifact.
* **`STATUS.md`'s far4 deadlock figure is guard-specific.** "far4 blind 837 →
  574" is the `full` and `indexed` guards; the `singleton` guard gives 837 → 610
  on the same run. The table quotes `far6`, and names the guard and the rung for
  every expansion count it prints.
* **`ic3_pdr`'s recheck is stronger than first read.** `E5` carries two matrix
  rows for that certificate, not one: ACCEPT against `peg4-0111` and REJECT
  against `peg4-1101`. That is a differential, and the table says so — while the
  boundary stays 未测, because a certificate being correctly bound says nothing
  about where the engine stops.

## Adversarial review

An adversarial reviewer was dispatched against the finished table with two
assignments: sample 8 numbers at random and re-derive them from `runs/`, and
audit every boundary cell for "not measured" written as "the boundary is X".
Its report is `ADVERSARIAL-table-audit.md` in this directory. Its findings are
recorded in `ADVERSARIAL-outcome.md` alongside what was changed in response —
including anything it overturned, which is recorded as overturned rather than
argued with.

## Not done, and why

* The table quotes one artifact outside `engine-rig/` (the g50t candidate
  stream) because that is where `zero_space`'s boundary is visible at real
  scale. It is read, never written. `g50t` is development-pile; the sealed pile
  had zero contact.
* `E2`'s ladder timings are quoted from `STATUS.md`'s prose rather than
  re-derived from `ladder.json`, because the milliseconds are wall-clock and not
  byte-stable. Probed as text, so a rewrite of that paragraph trips the script.
* No `PARTNER_SYNC.md` paragraph was appended: this is a branch, not the
  mainline, and the append-only rule starts at the merge.
