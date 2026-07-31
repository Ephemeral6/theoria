# E7 — auditing a design-document promise its own experiment refuted

**What was asked.** Theoria.md §1.9 promises *每证一个死锁，规划器同时提速* — every
deadlock proved, the planner speeds up at the same time. E2
(`runs/20260728T072633Z-E2-fd-ladder-bench/`) measured that against a real Fast
Downward and reported the speed-up half false. E7's brief: replicate it, attack
it, quantify where it holds, and write a `DEADLOCK_CLAIM.md` with evidence, a
boundary and a suggested wording — **without** editing Theoria.md, which is the
monitor's hand.

**What came out.** E2's numbers replicate to the expansion. E2's *explanation*
does not survive, and neither did E7's first replacement for it. The document is
`../../DEADLOCK_CLAIM.md`; this file is the run's narrative.

Two sessions produced it. **W-1411** built the `audit/` package, ran the
measurements and the seven attack scripts, and was swept before writing any of it
up — `DEADLOCK_CLAIM.md` §7 was left as the placeholder *"Filled in when they
report"*, and the attack results sat unread on disk. **W-130** read them, ran two
independent verifications of the load-bearing ones, corrected three published
numbers, wrote §7 and the verifier, and finished the run.

```bash
cd engine-rig
export FAST_DOWNWARD=".../.toolchain/downward/fast-downward.py"
python -m audit --out runs/<id>                                  # re-measure
python -m audit.verify runs/20260728T150713Z-E7-deadlock-claim-audit   # check
```

---

## 1. The conclusion, and the three claims that had to be withdrawn to reach it

The verdict E7 publishes is that §1.9's speed clause should be conditioned on
**whether the theorems' proof system is stronger than the planner's own
pre-search relaxation** — the carver proves with h² mutexes, Fast Downward's
pre-search deadness test is h¹. Getting there cost three claims, all of them
E7's own, all broken by the adversarial pass:

| withdrawn | by what | what replaced it |
|---|---|---|
| "not one state, at any size, that a theorem detects and the relaxation misses" | `rnd0021`, 11 witness states, verified against real FD | a **structural** argument for why `far{N}` cannot exhibit one — the zero was a theorem about that family, not a measurement (§3a) |
| "the dividend is zero because the information is redundant, not because it is unused" | `astar(lmcut())` saving up to 153 expansions with containment holding | a third mechanism: the guard is a domain transformation, and deleting dead push operators raises h on **live** states (§3c) |
| "the saving on an admissible heuristic is 0–3 expansions" | `far9` ipdb 78→30, `swap-passage` 454→0 | both **withdrawn in turn** as iPDB pattern-generation artefacts; the honest surviving range is 0–153 expansions on lmcut (§7b) |

The last row is the one worth reading twice. The two numbers that appeared to
refute the audit turned out to be instrument failures, and disposing of them
took more work than the original measurement did. `far9`'s dividend dies under
two of eight random seeds and under a larger PDB budget. `swap-passage`'s is a
`pdb_max_size` effect: iPDB's winning projection returns h = ∞ on the *unguarded*
task too, and the guard's entire contribution is shrinking that PDB from
2,725,888 entries to 1,103,872, under the 2,000,000 default cap. Raise the cap
and the unguarded run reports 0 expansions on its own.

**So `ipdb` expansion counts are ruled inadmissible as evidence at this effect
size**, and an earlier draft's `far8` 27 → 24 was one of these artefacts.

## 2. What survived being attacked

* **The guard is connected.** far6 goes 312 → 296 ground actions, 16 removed and
  0 added, identically at the rig's grounder and at FD's own translator.
* **The relaxation really is FD's.** `far4` verified **exhaustively** — all 3342
  states injected into the translated SAS task, `astar(hmax())` infinite on
  exactly the audit's 2904, **0 disagreements** — plus 116/116 one-state
  crosschecks across five geometries and two encodings. A `blind()` oracle
  sharing no code with the audit independently reproduces truly-dead = 2904.
* **The carver is sound** on all 280 instances checked: not one theorem-dead
  state is alive.
* **The goal-state cut does not bias the sets** (`goalcut.json`).
* **The instrument is sound**: 104 of E2's committed logs, 0 structural problems,
  0 of 36 pairs given mismatched `--search`.

## 3. Gaps — stated, not papered over

* **`a6_subsets.py` produced nothing.** It is the one instrument that would test
  monotonicity in the number of theorems carried, which is the clean way to
  separate information from perturbation. W-1411's session was killed with ~9 of
  72 configurations run. The ipdb disposal was reached another way; this test
  remains undone.
* **`wider.py`'s zero is vacuous** — it evaluates its question only on states the
  wide theorems cover and the narrow ones do not, and that set is empty on both
  instances it ran. Width 4 never ran; `four-block`, the board built so the
  textbook 2×2 four-box deadlock is one push from the start, is absent from the
  output. **The textbook four-box deadlock was never measured.**
* **`far7`/`far8` have no coverage measurement**; containment at those sizes
  rests on §3a's structural argument, not on a number.
* **Only `far4` is verified exhaustively against FD**; `far5`/`far6` rest on the
  audit's own Python relaxation, now validated exactly at `far4`.
* **The `occupied` re-encoding is not a faithful delete relaxation** —
  `relaxed_reachable_goal` ignores `pre_negative`. The direction is conservative
  (a faithful one could only find *more* dead states), but those numbers must not
  be published as that encoding's relaxation.
* **A labelling defect, corrected in §2 of the claim document**: `coverage()`
  counts every theorem while the guard carries only the 8 singletons, so "dead"
  and "what the guard removes" are different numbers (1624 vs 1512 at far4). The
  overcount inflates the theorems and so cannot manufacture the redundancy
  finding.

## 4. Verification

```
python -m audit.verify runs/20260728T150713Z-E7-deadlock-claim-audit
```

Eight checks, exit 0, and it runs on a machine with **no planner at all** —
checks 1–6 and 8 are pure Python and only the FD re-derivation skips, with a
stated reason:

1. every file the manifest lists still hashes to what it said — 38 files;
2. §1's nine replication rows, exact;
3. §3's coverage table, exact, including `n_theorem_dead_outside_relaxation = 0`
   on all three;
4. the relaxation-against-FD crosscheck — 116/116 agree, plus the 3342/3342
   exhaustive `far4` sweep;
5. **§3a's `rnd0021` counterexample re-derived from source** — 92 / 92 / 59 / 70
   / 11, exact, no planner needed;
6. carver soundness on `rnd0021` and `far4` — 0 theorem-dead states alive;
7. 29 structural FD measurements re-derived and compared for equality (skips
   without a planner);
8. timings present and sanely ordered — **ordering only, never equality**.

`tests/test_audit_claim.py` and `tests/test_audit_verify.py` pin both halves.
Whole suite: **317 passed** with Fast Downward, 317 passed / 13 skipped without.

The percentage column of §1 is compared to within 0.06 of a point rather than for
equality, because the table truncates (4.35 → "4.3") and asserting equality there
would be asserting a rounding rather than a measurement.

## 5. The reproducibility gap, unchanged from E2

Every Fast Downward number here came from the same untracked binary
(sha256 `645671ae…`, FD 24.06+ rev `7120aa0`), re-derived from the live build at
run time and checked against P-13's manifest rather than quoted from it.
`.toolchain/` is gitignored by design, so the repo's byte-reproducibility
requirement does not reach the FD numbers; the hash, commit and build command
stand in for it. Recipe: `runs/p13-fd-real/TOOLCHAIN_MANIFEST.md`.

What is fully reproducible without a planner is the part the conclusion now turns
on: the three set computations, the containment result, and `rnd0021`. Check 5
re-derives the counterexample from source on any machine.
