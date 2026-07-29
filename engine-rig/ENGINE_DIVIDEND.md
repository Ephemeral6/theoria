# What an engine is worth

Ammunition for the paper's §3 -- the quantitative support for *engines
propose, the LLM adjudicates*. Three engines, three claims, three batches.

**Regenerate:** `python -m tools.engine_dividend_table`;
**check it is not stale:** `python -m tools.engine_dividend_table --check`.

Every **measurement** below is read from an artefact; where the artefact
carries a verdict this reads that verdict rather than re-deriving one. The
arithmetic done here is percentages and totals over those fields, nothing
more. Sources:

* A, D -- `runs/20260728T191530Z-E6-engine-dividend/dividend.json`
* B -- `runs/20260728T191530Z-E6-engine-dividend/recheck_report.json`
* C -- `runs/20260728T072633Z-E2-fd-ladder-bench/ladder.json` (E2's measurement, quoted)

**Read the three sections as three results, not one.** They were measured on
different batches with different instruments against different claims. There
is no combined score and this file deliberately does not compute one.

---

## A · A proved deadlock, wired in as a pruner

The claim under test is Theoria 1.9: *every deadlock proved, the planner
speeds up at the same time*. **It is false as an unconditional promise, and
the zero row -- rendered first -- is why it has to be stated conditionally.**

`expansions` is the honest column; wall clock is §D and it is worse. Both
searches here are **controls, not rungs the ladder ever selects**: the
bundled BFS is the determinism-pinned default and `astar(blind())` is A\*
with a zero heuristic, which is the same search in other clothes. The rungs
a caller would actually get -- lmcut, ipdb, lama -- gain far less or
nothing, which is the subject of the next subsection and is the reason this
table must not be quoted on its own.

`carried` is the number of theorems the compiled guard could express, against the number proved. The `singleton` guard takes size-1 theorems only;
the pair theorems are left on the floor, so a row reading `40` theorems and
`8` carried bought its dividend with eight.

| instance | theorems | carried | bundled BFS before | after | saved | FD `blind()` before | after | saved | plan length |
|---|---|---|---|---|---|---|---|---|---|
| `open4` | 16 | 8 | 47 | 47 | 0.0% | 49 | 49 | 0.0% | unchanged |
| `open4far` | 16 | 8 | 808 | 571 | 29.3% | 837 | 610 | 27.1% | unchanged |
| `far4` †open4far | 16 | 8 | 808 | 571 | 29.3% | 837 | 610 | 27.1% | unchanged |
| `far5` | 24 | 8 | 988 | 869 | 12.0% | 958 | 872 | 9.0% | unchanged |
| `far6` | 32 | 8 | 3152 | 2788 | 11.5% | 3070 | 2762 | 10.0% | unchanged |
| `far7` | 40 | 8 | 8003 | 7041 | 12.0% | 7196 | 6365 | 11.5% | unchanged |
| `ringstuck4` | 2 | 2 | 44 | 22 | 50.0% | 0 | 0 | -- | unchanged |
| `ringstuck5` | 2 | 2 | 75 | 45 | 40.0% | 0 | 0 | -- | unchanged |
| `ringstuck6` | 2 | 2 | 114 | 76 | 33.3% | 0 | 0 | -- | unchanged |
| `ringstuck7` | 2 | 2 | 161 | 115 | 28.6% | 0 | 0 | -- | unchanged |
| `ringstuck8` | 2 | 2 | 216 | 162 | 25.0% | 0 | 0 | -- | unchanged |

† **`far4` ≡ `open4far`** -- the committed fixture and the generated ladder's bottom rung are the same board, checked column by column and agreeing. They are printed as two rows because the agreement is a measurement, but the batch is **10 distinct boards**, not 11.

**The `0 | 0 | --` rows are not missing data.** Fast Downward's translator settles `ringstuck4`, `ringstuck5`, `ringstuck6`, `ringstuck7`, `ringstuck8` during relaxed reachability and the search never starts, so there is no search for a deadlock theorem to shorten. The bundled rung's 44 -> 22 on `ringstuck4` is a fact about the bundled rung, which has no such check.

**The zero row.** `open4` proves **16 true theorems and saves nothing** -- 47 expansions before, 47 after, and the pruner fired **0 times** where it cuts 69-100 states on the rows below. The theorems are not wrong and the hook is not disconnected; there is simply no dead region on the path this search takes. A table of only the instances where the engine paid would be a different and less honest table.

**One number per cell is less than this run knows.** The same batch was re-measured under three tie-break rules for A\*'s open list. The *absolute* baselines move a great deal and the *dividends* move little:

| instance | baseline min | baseline max | dividend min | dividend max |
|---|---|---|---|---|
| `open4` | 45 | 82 | 0.0% | 0.0% |
| `open4far` | 607 | 874 | 21.6% | 27.3% |
| `far4` | 607 | 874 | 21.6% | 27.3% |
| `far5` | 958 | 1479 | 9.0% | 12.5% |
| `far6` | 3030 | 4519 | 10.0% | 12.6% |
| `far7` | 5508 | 8172 | 9.5% | 11.6% |

So an absolute expansion count in the columns above is one open list's, not a property of the instance. The ratios are the durable part. E7 §3c answers the same objection with a stronger instrument than this one -- the count of distinct states with *f* < C\*, which A\* must expand under any tie-break rule.

### Where that dividend goes, and why

Audited in depth by E7 (`engine-rig/DEADLOCK_CLAIM.md, branch agent/e7-deadlock-claim-audit`).
The short form, because a summary table that reprints the dividend without
its boundary is the thing E7 exists to prevent:

* **fd-optimal/ipdb** (§6, §7b) -- The whole astar(ipdb()) column is measured, not evidence. Its expansion counts move with iPDB's pattern generation and with pdb_max_size by more than the effect under study: far9 78 -> 30 vanishes under two of nine seeds, and swap-passage 454 -> 0 is the guard shrinking the abstraction under the default 2,000,000-entry cap rather than a deadlock dividend.
* **fd-optimal/blind** (§1, §7c) -- The blind band on the far{N} family is -8.7% to -27.1% across far4..far10, not the '10-27%' E2 published; and that band is itself one open list's. Across instances generally the blind dividend runs 0% to 100%.
* **fd-optimal/lmcut** (§3c, §4) -- On lmcut the saving is 0 to -153 expansions (0% to -7.8%), and where the theorems are contained in FD's own delete relaxation it is not pruning at all: the states removed were already evaluated as dead ends and never expanded. The one isolated mechanism is a tightened relaxation raising h on live states.
* **tiebreak_sensitivity** (§3c) -- E7 already answered the tie-break objection with a stronger instrument than this one: the count of distinct states with f < C*, which A* must expand under any tie-break rule. This module measures absolute counts under three rules, which establishes the dependence and not its absence.

**And the guard is a choice with a sign.** The FD column above is the
`singleton` guard. The same artefact holds two other encodings of the same
theorems, and one of them makes the search *worse*: on `far5`,
`astar(blind())` goes 958 -> 872 under `singleton`, 958 -> 839 under `full`,
and 958 -> **1159** under `indexed` -- a 21% loss, because that encoding
inflates the operator set. "The expansion dividend is real" is true of the
column printed here and false of a column that could have been printed
instead.

The boundary in one line: **a proved deadlock is worth expansions to the
extent its proof system is stronger than the planner's own pre-search
relaxation.** The carver proves with h^2 mutexes; Fast Downward's
pre-search deadness test is h^1. Where they coincide the pruning dividend
is nil; where they do not it can be total.

## B · Certificates rechecked by a stranger

The claim under test is 1.10(a): an engine's output is an artefact a
*separate* reader can check. The rechecker imports nothing from `engines/`
or `interop/`, and a test enforces that by reading its own import
statements and asserting the scan actually covered every module -- so an
engine and its checker cannot be wrong together by sharing code.

| what | count | behaved as declared |
|---|---|---|
| certificates rechecked | 26 | 26 |
| — of those, ACCEPT / REJECT | 24 / 2 | — |
| — of those, pagoda (new in E6) | 4 | 4 |
| forgeries attempted | 42 | 42 |
| committed case files | 37 | — |

**26/26 certificates and 42/42 forgeries behaved as declared.**

Three things that column does *not* say, each of which an earlier draft of
this file got wrong:

* **The matrix is not paired accept-for-reject.** It is 24 accepts and 2 rejects; only two accepts have a matched reject control. The pairing discipline is real for the forgery set, not for the matrix.
* **2 forgeries are declared non-catches, not catches** — `region-reaching-outside-the-constraint` (ACCEPT-QUALIFIED), `delete-the-rule` (NOT-CAUGHT). `delete-the-rule` in particular is a class of attack **no certificate checker can see**: a rule that never fired owes no frame, so deleting it leaves every certificate valid. It is recorded as a known blind spot and the suite fails if it ever starts being "caught". So the honest catch count is 40 of 42, with 2 declared escapes — not 42 catches.
* **`37 committed case files` is files, not certificates** — certificate documents plus the rule sets they are checked against. It is a drift guard on the corpus, not a second pass rate.

**Pagoda, added by E6.** 4 certificates rechecked, of which 3 have a producer document to run a differential against and all 3 agree. E5 left `lp_potential`'s
certificates uncovered -- the only checker for them imported the producing
engine and trusted the producer's own witness list. E6 re-derives the move
set from the declared geometry and **refuses** the producer's obligation
list as input, comparing it once as a differential where a disagreement is
a finding rather than a rejection.

| certificate | verdict | states | satisfying | delta checks | raising |
|---|---|---|---|---|---|
| `peg4-1110-pagoda` | ACCEPT | 16 | 8 | 32 | 0 |
| `peg5-11011-to-01000-pagoda` | ACCEPT | 32 | 22 | 132 | 0 |
| `peg5-11011-to-00010-pagoda` | ACCEPT | 32 | 22 | 132 | 0 |

The certificate missing from that table is the interesting one. `keyed-gate-pagoda` has no producer document, so there is no differential to run -- but it is carried because a naive checker **false-rejects** it: its only potential-raising move needs two keys, while every two-key state is already outside the region, so quantifying closure over all moves rather than over moves legal from the region rejects a certificate that is genuinely inductive. It is in the matrix above and it is an ACCEPT.

## C · The three-rung ladder

Measured by E2 (`runs/20260728T072633Z-E2-fd-ladder-bench`), quoted here rather than re-run, and the
agreement column is **read from the artefact's own verdict**, not recomputed.
**Node counts are not comparable across rungs** -- the artefact says so in a
top-level field -- so this table compares plan lengths, which are.

| instance | optimum | source | stub-bfs | fd/lmcut | fd/lama | rungs agree |
|---|---|---|---|---|---|---|
| `gripper-01` | 3 | closed form | 3 | 3 | 3 | yes |
| `gripper-02` | 5 | closed form | 5 | 5 | 5 | yes |
| `gripper-03` | 9 | closed form | 9 | 9 | 9 | yes |
| `gripper-04` | 11 | closed form | 11 | 11 | 11 | yes |
| `gripper-05` | 15 | closed form | 15 | 15 | 15 | yes |
| `gripper-06` | 17 | closed form | 17 | 17 | 17 | yes |
| `gripper-07` | 21 | closed form | 21 | 21 | 21 | yes |
| `gripper-08` | 23 | closed form | 23 | 23 | 23 | yes |
| `gripper-09` | 27 | closed form | 27 | 27 | 27 | yes |
| `gripper-10` | 29 | closed form | 29 | 29 | 29 | yes |
| `sokoban-open4` | 6 | hand-derived | 6 | 6 | 6 | yes |
| `sokoban-open4far` | -- | -- | 11 | 11 | 37 | yes (no optimum) |
| `sokoban-ring` | 1 | hand-derived | 1 | 1 | 1 | yes |
| `sokoban-ringstuck` | -- | -- | -- | -- | -- | -- |
| `sokoban-far4` | -- | -- | 11 | 11 | 37 | yes (no optimum) |
| `sokoban-far5` | -- | -- | 13 | 13 | 21 | yes (no optimum) |
| `sokoban-far6` | -- | -- | 17 | 17 | 27 | yes (no optimum) |

**0 disagreements.** Where an optimum is known the optimal rungs hit it; on the 4 sokoban rows where none is known they agree with each other, which is a weaker statement and is labelled as one. The gripper oracle is a closed form and the small sokoban optima are hand-derived; neither shares code with any planner.

The satisficing rung is genuinely not optimal, which is the point of keeping
it: on `sokoban-open4far` LAMA returns 37 where all three optimal rungs
return 11. It is also the only rung that scales here. `plan.optimal = False`
on that rung is not a formality, and its answer is not a length anyone may
quote as an optimum.

## D · What it costs -- the column that does not flatter the engines

Expansions are what the theorems buy. Seconds are what they cost, and the
carve costs more than the search saves on every row that ran a search.

**These are wall-clock numbers, so they are this machine's afternoon and not
reproducible.** The producing run's verifier checks their ordering and never
their equality, and neither should a reader. The comparison below survives
that caveat only because the two sides differ by three orders of magnitude.

| instance | theorems | carve seconds | FD `blind()` search saved | repaid? |
|---|---|---|---|---|
| `open4` | 16 | 0.074694 | -0.000018 | **no** |
| `open4far` | 16 | 0.073258 | 0.000394 | **no** |
| `far4` | 16 | 0.074225 | 0.000249 | **no** |
| `far5` | 24 | 0.239224 | 0.000077 | **no** |
| `far6` | 32 | 0.640455 | 0.000684 | **no** |
| `far7` | 40 | 1.464719 | 0.002146 | **no** |
| `ringstuck4` | 2 | 0.011131 | -- | n/a -- no search |
| `ringstuck5` | 2 | 0.021929 | -- | n/a -- no search |
| `ringstuck6` | 2 | 0.044892 | -- | n/a -- no search |
| `ringstuck7` | 2 | 0.081420 | -- | n/a -- no search |
| `ringstuck8` | 2 | 0.131781 | -- | n/a -- no search |

**0 of 6 rows that ran a search repay the carve.** The other 5 (`ringstuck4`, `ringstuck5`, `ringstuck6`, `ringstuck7`, `ringstuck8`) are settled by the translator before search, so their microsecond deltas are the noise of a search that never happened and are excluded rather than scored.

The expansion dividend is real; the wall-clock dividend, once carving is on
the invoice, is negative everywhere in this batch. It would turn positive on
an instance large enough that the saved fraction of a much longer search
exceeds a carve whose cost grows with the board rather than with the search
-- which this batch does not contain.

## What this table is not

* **Not a comparison between engines.** Three engines measured on three
  batches against three different claims. Nothing here ranks them, and the
  title question -- *what is an engine worth?* -- has three answers, not one.
* **Not a general result about planning.** A and D are sokoban as
  `fixtures/sokoban.py` encodes it; C is sokoban and gripper. Two domains.
* **Not a measurement of the rungs a caller gets.** §A's two columns are both
  heuristic-free controls. The selectable rungs gain far less, and the
  `ipdb` one was demoted by E7 to *measured, not evidence*.
* **Not a wall-clock win.** §D is the honest version of §A.
* **Not an independent check of §C.** Those numbers are E2's, quoted. This
  file re-runs nothing; `--check` proves only that it matches its renderer.

