# Adversarial review of A9 — verbatim

Stored verbatim, not paraphrased. The reviewer ran read-only against
`.worktrees/a9-readonly-baseline/` and the main worktree and returned its report
as text; this file is that text, unedited. Its three assigned attacks were (a)
does the empty-run control really remove background noise, (b) is the hard list
dead letter, (c) is the negative control constructionally bound to go red.

Verdicts: (a) WEAK, (b) WEAK, (c) WEAK.

What was done about it is in `../../RUN_STATE.md` and in
`ADVERSARIAL-RESPONSE.md` next to this file. Where the reviewer overturned me it
says so; nothing here is argued away.

---

Reviewed at `outside.py` md5 `26820b08…`, `test_readonly.py` md5 `f233a6c7…`. **The test file changed under me mid-review** — a fourth slow test, `test_a_mutated_existing_file_outside_the_arm_turns_this_check_red` (test_readonly.py:229), appeared after my first read. My (c) covers both revisions.

---

## (a) Does the empty-run control remove background noise — and what does it wrongly remove?

**It removes essentially nothing, and in the environment the gate actually runs in it removes exactly nothing.**

**1. The control is inert where the gate runs.** `observe()` defaults to `root=REPO` (outside.py:333), and `REPO` is `dirname(ablation-arm)` (_bootstrap.py:32) — the *worktree* root. The monitor runs every territory gate inside a throwaway worktree: `monitor/ci_merge.py:175`, `git worktree add --detach wt origin/master`. In `.worktrees/a9-readonly-baseline/` there is no `proxy/var/` at all and no concurrent writer. I ran 75 consecutive 2.0 s idle windows there: **0 background paths**, and the only three files that ever moved were the A9 session's own negative-control litter. Across six `observe()` calls (worktree and main; actions of 0/1/3 s) `background` was `[]` every time — matching the author's own `01-empty-run-control.json` (`background: []`) and `02-real-run.json` (`background: []`). So `Observation.subtracted` (outside.py:294) and `reported_by_hard_list` (outside.py:290) have never had a non-empty input outside the hand-built `Observation` at test_readonly.py:292. **The subtraction is untested in the environment it was built for. Yes — say so plainly.**

**2. False positives — a concrete class the design claims not to produce, measured.** `monitor/ci/merge.log` is a *tracked* file (not gitignored), written by the CI merge loop. Over 75 windows it moved in **7** — P = 0.093 per 2.3 s window. Its siblings `monitor/ci/merge.lock` and `monitor/ci/CONFLICT-origin_agent_*.md` moved too. Aggregating my two probes (105 windows, ~245 s of exposure on the main tree, 9 windows with ≥1 change, λ ≈ 0.037 events/s) against the measured run leg of 1.765 s (`02-real-run.json`):

> **P(false red per run) ≈ 5.7–6.3 %** — versus the **0.02262** recorded in `06-periodic-writer-residual.json`.

That file is under-measured for two separable reasons, both citable:
- `05-live-background-churn.json` sampled **four** windows totalling 53 s and concluded the tree is "quiet at 2s, 5s and 15s". My 245 s sample shows a 2 s window is non-empty **8.6 %** of the time. The single largest churn source — `monitor/ci/merge.log` — does not appear anywhere in the A9 evidence.
- `06`'s headline `0.02262` = `0.95 / 42` uses `gap_seconds_min`, while its own prose ("present during neither leg ~99.7 % of the time") is the `gap_seconds_median = 300` figure. Two estimators in one number.

Note the sting: `.log` was one of the seven superseded tokens. `monitor/ci/merge.log` is a false-positive class the broken criterion suppressed and A9 re-opens, at ~6 %/run, with nothing to quiet it.

**3. A Windows-specific FP the design has no answer for.** `proxy/spend_gate.py:230-232` takes an `msvcrt` byte-range lock on `proxy/var/spend_gate.jsonl.lock`. While held, another process cannot read it; `snapshot()` swallows the `OSError` and drops the key (outside.py:257-259). The file therefore *vanishes from one snapshot and reappears in the next* — a reported diff with no write at all. `spend_gate.jsonl.lock` is not on the hard list and the old tuple hid it (`/var/`).

**4. What the idle window wrongly absorbs (false negatives).** Credit where due: the p≈1 continuous writers on this repo — `proxy/var/spend_gate.jsonl` (appended per API call) and `baseline-arms/out/shards/ledger.*.jsonl` (appended through a live campaign) — **are** on the hard list. That hole is genuinely closed. What is *not* covered and *is* continuous during a live dispatch: `monitor/ci/merge.log`, `monitor/bus/*/out.jsonl`, `monitor/board/board.log`, `monitor/inbox/*`, `monitor/dispatch-logs/*.log`. An arm forging a board claim or an inbox message is a real consequence and would be silently subtracted.

Two structural false negatives nobody has named:
- **`.env` is not watched at all.** `watched()` skips every top-level name starting with `.` (outside.py:231). I verified: `.env`, `.env.example`, `.gitignore`, `.gitattributes` are absent from the snapshot. CLAUDE.md makes `.env` the single highest-consequence file in the repo. Meanwhile *nested* dot-directories **are** walked — `theoria-arm/.pytest-runs/…` is in the snapshot. The rule is inconsistent with itself.
- **The `OSError → continue` swallow is a false negative, not just an FP.** A write that leaves the file locked across both snapshots is absent from both dicts and produces no diff. The hard list cannot save it: the path never enters the snapshot.

**5. If ablation-arm's escape hit a path another session writes continuously** — the scenario the module docstring names at outside.py:87-92 — the arithmetic is: subtracted unless hard-listed. On this repo the plausible collision targets are `proxy/var/spend_gate.jsonl` and the shard ledgers, both hard-listed. So this specific attack **does not land**. I could not break it.

**6. Wall-clock alignment — sounder than the docstring claims, with one small real error.** Let S = snapshot duration, A = action duration. Per-file exposure: idle leg = 2.0 + S; run leg = A + S; make-up leg = shortfall + S = A − 2.0. When the make-up fires, control exposure = (2.0+S) + (A−2.0) = **A + S = exactly the run exposure**. Measured S = 0.24 s (worktree) / 0.40 s (main); `idle_seconds ≈ 2S + 2.0` confirmed (2.50/2.52/2.56 and 2.68–2.79). The bug is in the *predicate*: `aligned` (outside.py:300) tests `2S+2.0 ≥ A+S`, i.e. `A ≤ 2.0+S`, while true per-file alignment needs `A ≤ 2.0`. For `A ∈ (2.0, 2.0+S]` it reports `True` while the control is short by up to S. Small now, linear in tree size.

The deeper objection is not the clock, it is the estimator. A single-sample control has residual FP = p(1−p): maximised at p = 0.5, driven to zero by **no** window length. Shorten it and p→0 (nothing subtracted — where we are, at p≈0.09, paying ~6 %). Lengthen it and p→1 (everything subtracted, FPs become FNs). There is no window that works.

One live hazard: the make-up window sits *after* the run and unions `diff(third, fourth)` into `background` (outside.py:361-363), so any trailing/async write by the action gets subtracted. I checked — the arm's runtime path has no `subprocess`/`threading` (only `verify.py:59`), so this is not exploitable today. Flagging as a future trap, not a finding.

**VERDICT (a): WEAK — the control is provably inert in the worktree the gate runs in (background = [] in 75/75 windows and 6/6 observations), and where it is not inert its measured residual false-red rate is ~6 %/run, roughly 3× what the run record claims, driven by a writer the A9 evidence never sampled.**

---

## (b) Is the hard list dead letter?

**Not as a rule — every pattern matches real files. But as a *mechanism* it has never fired, and three of seven patterns over-match in the direction that recreates the original failure.**

**Existence (measured, both trees).** Worktree / main hit counts: `arc-recon/data/*.jsonl` 4/4 · `CONTRACTS/**` 7/7 · `monitor/state.json` 1/1 · `**/ledger.jsonl` 10/15 · `**/ledger.*.jsonl` 10/14 · `**/candidates.jsonl` 17/18 · `proxy/var/spend_gate.jsonl` **0**/1. So no pattern is decoration for want of a file.

**Is the `spend_gate.jsonl` skip (test_readonly.py:331-334) a hole?** Yes, a narrow but real one. It is the only bare-literal pattern, so it is the only one where a typo cannot be caught by a shape assertion — and the two tests that *do* mention it (line 288, line 313) compare the literal in `outside.py` against the same literal retyped in the test. That is a tautology: rename the ledger upstream and all eleven tests stay green while the hard list protects nothing. The authority exists and is never consulted — `proxy/paths.py:12-13` defines `VAR_DIR = HERE/var` and `LEDGER_PATH = VAR_DIR/ledger.jsonl`. Assert against *that*, not against a retyped string.

**Is `reported_by_hard_list` reachable in a real run?** Effectively no. It requires a path in **both** `background` and `observed`. In a worktree `background` is always empty (75/75 windows measured) → probability exactly 0. In main, for the hard-listed `monitor/state.json` (λ ≈ 1/300 s) P(both legs) ≈ 6×10⁻³ × 8×10⁻³ ≈ **5×10⁻⁵**. The branch at outside.py:290-291 is reached only by the hand-built `Observation` at test_readonly.py:292. The rule is real; its trigger is not.

**The more serious problem is over-reach, and it is un-suppressible by construction.** `**/candidates.jsonl` matches 18 files in main; **only 2** are the frozen contract stream (`engine-rig/artifacts/`, `engine-rig/out/`). Ten are `worldgen/out/qc/*/candidates.jsonl` — another territory's regenerated QC scratch. `**/ledger.jsonl` matches `theoria-arm/.pytest-runs/pytest-*/ledger.jsonl` — another arm's pytest temp dirs. `**/ledger.*.jsonl` matches 14 `baseline-arms/out/shards/*`, which a live campaign appends to continuously. Because the hard list is *never* subtracted, **a concurrent worldgen QC run or baseline campaign makes `test_a_full_run_writes_only_inside_this_arm` deterministically red for something ablation-arm did not do**, and the control is forbidden from quieting it. That is exactly the pressure that produced the tightening the DRIFT note documents. The trade is stated honestly at outside.py:88-90 ("worth an occasional false red") — but it was priced against the *frozen contract stream*, and what it actually buys is a permanent red whenever a neighbour regenerates QC scratch.

**VERDICT (b): WEAK — every pattern matches real files, but the mechanism (`reported_by_hard_list`) is unreachable outside a hand-built `Observation`, the one pattern the audit was built around is verified only against a retyped copy of itself, and three of seven patterns over-match another territory's regenerated scratch — making un-suppressible false reds the expected outcome of a concurrent campaign.**

---

## (c) Is the negative control constructionally bound to go red?

**Yes, and worse: it demonstrates a capability an untouched, pre-A9 test in the same file already had.**

**The stray-byte control (test_readonly.py:173-225) is near-vacuous as a control for A9.** The victim is created *inside* the action with a pid-unique name, so it cannot be in `background`; `is_hard` is false (asserted at line 198). Therefore `reported` ⟺ `observed` ⟺ "`os.walk` found a new file". It exercises `snapshot`+`diff` and nothing else — not `IDLE_FLOOR_SECONDS`, not the subtraction, not the make-up window, not the hard list. Any criterion that reports additions catches it.

**The killer for discrimination:** the victim lives under `proxy/`, a member of `pin.UPSTREAM_TREES` (pin.py:35-36), and `pin.SKIP_DIRS` does **not** contain `var`. I verified `pin.hash_tree()` returns **81 files under `proxy/var/`** on the main tree. So the same byte is caught, unconditionally and with no exclusion tuple whatsoever, by `test_a_full_run_leaves_every_upstream_tree_byte_identical` (test_readonly.py:94) — which predates A9 and was never broken. The negative control proves a capability the file already had, in a directory the old code already watched. Only the *second* section of the file ever applied the `CONCURRENT` tuple.

**The "superseded lets it through" arm is trivially true by construction, and the docstring says so** (lines 186-188: the victim is "chosen to … trip two of the old exclusion tokens at once"). Since `SUPERSEDED_CONCURRENT_TOKENS` is a constant in the same module (outside.py:375-376), `victim_rel not in superseded_criterion(...)` reduces to `".jsonl" in TOKENS`. And `test_the_hard_list_covers_every_path_the_old_criterion_hid:319` **already asserts exactly that**, in microseconds, over six *real* paths. The slow test pays ~2.6 s of sleeps plus a full arm run to re-assert it on a synthetic path.

**The mutation control (test_readonly.py:229-276) is a genuine improvement and answers half my objection.** The victim is seeded before the first snapshot, so its key is in `before` and `after` and only its content moves — the realistic shape (an append). But it is still the test's own file, still under `proxy/var/` (so still covered by the untouched pin test), and line 267's `assert victim_rel not in obs.background` is guaranteed by construction: the file is written once before the first snapshot and again only during the run leg. **It still never exercises the subtraction.** The one case that would — a victim genuinely present in `background` — remains reachable only through the hard list, which is tested only with the hand-built `Observation` at line 292.

**Cleanup: correct for every case that occurs here; two residual notes.** `made_dir` is read before `makedirs` (lines 196, 247) and `rmdir` is guarded on emptiness, so a pre-existing populated `proxy/var/` — the main-tree case, where it holds a 1.4 MB `spend_gate.jsonl`, `ledger.jsonl`, `runs/`, `scores/` — is correctly preserved and never removed. If `proxy/` itself were absent, `makedirs` would create it and only `var` would be removed; `proxy/` always exists on this tree, so I am **not** claiming that as a finding. `proxy/var/` is gitignored (`proxy/.gitignore:3`), so a hard-kill leak would also be invisible to `ci_merge.py:226`'s `git status --porcelain` dirty check — but `git worktree remove --force` at ci_merge.py:250 deletes the tree anyway.

**What I did observe (no leak, but a real interference surface):** my independent read-only probe of the worktree caught `proxy/var/a9-mutation-control-{42880,43496,43524}.jsonl` appearing and disappearing across 6 of 150 two-second windows. Cleanup worked every time — **no leak**. But it demonstrates that the controls do write into another territory's directory and are visible to any concurrent observer for 1–2 s. If this suite ever runs in the main tree while another territory's read-only/pin gate runs, the negative control *is* a cross-territory write and will appear in that gate's report. The docstring's care at line 188 addresses corruption, not visibility.

**VERDICT (c): WEAK — both controls prove only that a diff sees a file the test itself created, on a path already covered unconditionally by the untouched pin test at line 94; the "superseded lets it through" arm is true by construction and is already asserted faster, on real paths, at line 319.**

---

## WHAT I WOULD CHANGE (ranked)

1. **Move a negative control's victim outside `pin.UPSTREAM_TREES`** — `monitor/`, `baseline-arms/out/`, or a top-level file like `PARTNER_SYNC.md`. Only `outside.py` watches those, so only there does the assertion discriminate A9 from the code that predates it. Today both controls fire against the untouched pin test.
2. **Add the control that is actually missing: a victim that IS in the background set.** Have the test itself write the victim during the idle leg *and* the run leg, then assert an ordinary path is subtracted and a hard-listed one is not — end to end, not via a hand-built `Observation`. That is the only assertion that would ever execute outside.py:286-295 on real data.
3. **Fix the `.env` blind spot.** `watched()` (outside.py:230-234) drops every top-level dotfile while nested dot-dirs are walked. Watch `.env`, `.gitignore`, `.gitattributes`; keep `.claude/`, `.git/`, `.worktrees/` skipped by name, not by leading dot.
4. **Correct `06-periodic-writer-residual.json` and re-measure with a sample that can see `monitor/ci/merge.log`.** 4 windows / 53 s is not a sampling frame for a P ≈ 0.09 event. My 245 s sample puts the residual false-red rate at ~6 %/run, ~3× the recorded figure, and identifies a writer the evidence never sampled. Also reconcile the `min`-vs-`median` gap estimator inside that one file.
5. **Narrow the two extension patterns.** `**/candidates.jsonl` → the two engine-rig paths (or exclude `**/out/qc/**`); `**/ledger.jsonl` → exclude `**/.pytest-runs/**`. As written they guarantee an un-suppressible red the moment a neighbour regenerates scratch — the same pressure that produced the tightening this ticket exists to undo.
6. **Assert `proxy/var/spend_gate.jsonl` against `proxy.paths`, not against a retyped literal** (test_readonly.py:288, 313, 331). Import `paths.LEDGER_PATH` / the spend-gate path and derive the expected pattern, so an upstream rename turns the suite red instead of silently emptying the rule.
7. **Handle the `OSError` swallow explicitly** (outside.py:246-247, 257-259). A locked file currently produces a phantom diff on one side and total invisibility on the other. Record unreadable paths in a third bucket on `Observation` so a reader can see how many files the snapshot could not read, rather than having them silently become — or fail to become — evidence.
8. **Tighten `aligned`** to `idle + makeup − snapshot_cost ≥ run` (outside.py:300), or record `snapshot_seconds` on `Observation` so the ≤ S overstatement is visible. And state in the docstring what the measurements show: the subtraction is inert in a worktree, so in CI the check is a plain "nothing outside moved", with the empty-run control contributing nothing.
