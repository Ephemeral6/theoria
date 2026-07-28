# E6 — what an engine is worth, in numbers

**What was asked.** Turn "engines propose, the LLM adjudicates" into quantities
for the paper's §3: the deadlock dividend as node counts before and after, the
independent recheck pass rate for IC3 invariants and LP pagoda certificates, and
the three-rung ladder's optimality and wall clock on one batch. All as
regenerable tables, data under `runs/`, scripts deterministic.

**What came out.** `../../ENGINE_DIVIDEND.md`, assembled by
`python -m tools.engine_dividend_table` from three artefacts, with
`--check` to fail if it goes stale. Two of the three measurements already
existed and are cited rather than re-run; the third did not exist and was built.

```bash
cd engine-rig
export FAST_DOWNWARD=".../.toolchain/downward/fast-downward.py"
python -m bench --out runs/20260728T191530Z-E6-engine-dividend --prompt-id E6-engine-dividend
python -m recheck.verify_all
python -m tools.engine_dividend_table            # write the §3 table
python -m tools.engine_dividend_table --check    # fail if stale
```

---

## 1. Scope — two thirds of this item was already done

Scoping first saved most of the work, and the honest report is that E6's brief
overlapped two finished runs:

| part | state | where |
|---|---|---|
| (A) deadlock dividend, node counts | **done twice** — E2 measured it, E7 audited it to destruction | `runs/20260728T072633Z-E2-fd-ladder-bench/`, `DEADLOCK_CLAIM.md` |
| (C) three-rung ladder, optimality + wall clock | **done** | `runs/20260728T072633Z-E2-fd-ladder-bench/LADDER.md` |
| (B) independent recheck pass rate | **half done** — E5 covered IC3 and dead regions; `lp_potential`'s pagoda certificates were uncovered, and E5's own RUN_STATE §7 said so | `runs/20260728T141724Z-E5-cert-recheck/` |

So E6's real work was: close (B), add the two rows (A) was missing, and build the
assembly that makes the three quotable together without letting one stand in for
another.

## 2. What was built

**(B) — pagoda certificates, rechecked cold.** `recheck/` gains a fourth
condition shape, `potential_bound`. The gap it closes is specific: the only
existing pagoda checker was `interop/certificate_export.py::verify`, which is
independent on neither count — it imports `engines.lp_potential.potential`, and
it iterates the producer's *own* witness list. The new one imports nothing from
`engines/` or `interop/` (a test enforces this by reading the import statements
and asserting the scan covered every module), grounds the move set from the
declared geometry, and **refuses** an `obligations` key outright so the
producer's witness list cannot be an input. That list is read exactly once, in
`anchors.pagoda_differential`, where a disagreement is a *finding* rather than a
rejection.

4 pagoda certificates rechecked, all ACCEPT; 3 have a producer document to run a
differential against and all 3 agree. 11 new forgeries, all behaving as declared.

The fourth certificate, `keyed-gate`, is the one worth knowing about: it was
built because a naive checker **false-rejects** it. Its only potential-raising
move needs two keys, and every two-key state is already outside the region — so
quantifying closure over *all* moves rather than over moves legal *from the
region* rejects a certificate that is genuinely inductive. That is the defect the
salvaged draft had, and the case exists so it cannot come back.

**(A) — the two rows that were missing.** `open4` and `open4far` are now in a
regenerable table, `open4` first.

**`open4` is the zero row: 16 true theorems, 47 expansions before and 47 after,
pruner fired 0 times.** D-020 argued that row is the informative one and it
existed in no artefact anybody regenerated. The theorems are sound — all 16 check
out by hand — and the hook is connected; there is simply no dead region on the
path this search takes. A table of only the instances where the engine paid is a
different and less honest table.

Also added: the FD-side seconds dividend charged against `search_seconds` rather
than the ~150 ms driver clock, with `carve_seconds` on the invoice; and a
tie-break sensitivity sweep closing E2's gap G7.

## 3. Salvage — what was taken from a dead session and what was thrown away

W-1611 claimed E6, worked for four hours, and was swept with everything
uncommitted on a stale base. Two pieces were left:

* **`bench/dividend.py` + `bench/fdrun.py` edits — salvaged.** Master had not
  touched either file since that base, so they applied cleanly. Four defects
  were fixed on the way in: absolute paths (an operator's home directory) in the
  artefact; verdicts computed at a different precision than they publish; a
  comment asserting `goalcount()` is admissible, which it is not; and
  `bench/__main__.py` silently destroying this run's `MANIFEST.json`.
* **`interop/recheck.py` — its IC3 half thrown away, its pagoda math kept.** The
  file claimed independence in its docstring, and three of its error messages are
  byte-identical to the theory-compiler track's implementation — so the IC3 half
  is a transcription of the checker it claimed to be independent of, which is
  precisely the failure mode E5 exists to prevent. Its pagoda arithmetic is
  correct and was verified against `pagoda_4_1110_to_0100.json` before being
  ported into `recheck/` under that package's enforced-independence test. It was
  also promising a test that did not exist ("`tests/` asserts this by reading the
  import statements of this file" — no such test).

## 4. The assembly, and the bug that justifies the rule it now states

`tools/engine_dividend_table.py` reads three artefacts and writes the §3 table.
Its governing rule — **read verdicts, do not re-derive them** — is written in the
docstring because breaking it produced this module's worst bug.

An earlier draft recomputed section C's optimality agreement instead of reading
`verdicts.agreement_ok`. Four sokoban instances have no *known* optimum; the
recomputation scored "no ground truth" as "disagreement" and rendered **no** in
the agreement column against `lmcut`, `ipdb` and the bundled BFS — a false
accusation of returning non-optimal plans, in the file whose purpose is to be
quoted in a paper. It also printed the self-contradicting sentence *"Every
optimal rung agrees … (4 disagreements)"*. E2's artefact carries
`agreement_ok: true` on all four rows and E2's own `LADDER.md` renders them
`yes`. Reading the field gives **0 disagreements**.

An adversarial review found 15 defects in the first assembled draft; that was the
worst, and three others were the same shape — a column reading a key that does
not exist and rendering as a valid table full of `--`:

| column | read | actual field |
|---|---|---|
| §A FD blind | `config` | `rung` |
| §A plan | `plan_unchanged` | `plan_length_unchanged` |
| §B region | `n_region` | `n_satisfying` |
| §A tie-break dividend | `dividend_min` | `guards.<guard>.dividend_min_pct` |

**`--check` cannot catch any of these** — it proves the file matches its
renderer, never that the renderer reads the right field. Only a test pinning a
real number does that, and the test file now pins several, plus perturbation
tests that move one field and require exactly the matching cell to move.

Other corrections from the same review, all now in the document: the theorem
count beside an FD row is not what reached the planner (the `singleton` guard
carries 8 of 40 on `far7`, so there is a `carried` column); `far4` and `open4far`
are the same board and the batch is 10 distinct boards, not 11; the five
translator-settled `ringstuck` rows are excluded from §D rather than scored on
the microsecond noise of a search that never ran; §B's forgery count is 40 of 42
caught with **2 declared escapes**, not 42 catches — `delete-the-rule` is a class
of attack no certificate checker can see, and calling it a catch would convert an
admitted blind spot into a virtue.

## 5. What this run does not establish

* **The three sections are three results, not one.** Different batches,
  different instruments, different claims. There is no combined score and the
  assembler deliberately does not compute one.
* **§A's two columns are both heuristic-free controls** — the bundled BFS and
  `astar(blind())`. The rungs a caller actually gets gain far less, and E7
  demoted the `ipdb` column to *measured, not evidence*. The §3 table must not be
  quoted without its boundary subsection.
* **The guard is a choice with a sign.** The FD column is the `singleton` guard.
  The same artefact holds an `indexed` encoding under which the theorems make the
  search **worse** — `far5` blind 958 → 1159, a 21% loss. "The expansion dividend
  is real" is true of the column printed and false of one that could have been.
* **Two domains** (sokoban, gripper), one planner build, one machine.
* **Wall clock is not reproducible** and §D says so. The comparison there
  survives only because the two sides differ by three orders of magnitude.
* **§C is E2's measurement, quoted.** This run re-ran nothing of it.

## 6. Verification

```
python -m pytest                                  407 passed
python -m tools.engine_dividend_table --check     ok -- ENGINE_DIVIDEND.md is current
python -m recheck.verify_all                      VERDICT GREEN (42 forgeries as declared)
python -m bench.verify runs/20260728T072633Z-E2-fd-ladder-bench   ok
```

**A gap in the verification surface, stated rather than hidden:**
`bench.verify` cannot be pointed at this run — it requires `ladder.json`, which a
dividend-only run does not produce, and its checks cover ladder rows only, none
of the new dividend fields. The manifest hashes verify, `--check` covers the
assembled table, and the pytest suite covers the new code; but there is no
single `verify <this run>` entry point, and building one was not in scope. That
is the one thing a reader should not assume is there.
