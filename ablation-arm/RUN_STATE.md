# ablation-arm — run state

Human narrative for this arm's runs. Append only; never rewrite a paragraph that
is already on the mainline. The canonical machine record is each run's
`runs/<id>/MANIFEST.json`, and this file never stands in for one.

---

## 2026-07-28T19:14:37Z — A9-readonly-baseline

`runs/20260728T191437Z-A9-readonly-baseline/` · branch `agent/a9-readonly-baseline`
· base `7df12a3` · zero API calls, zero network, zero sealed-pile contact.

**Why.** The previous read-only criterion was falsified by
`monitor/audit/DRIFT-20260728T1501Z-the-tightened-criterion-hides-the-worst-writes.md`
(high). It subtracted concurrent-fleet noise with a tuple of path shapes —
`("/var/", "/runs/", "/out/", "/artifacts/", ".jsonl", ".log", "state.json")` —
while its own comment claimed the criterion was "no change, or change traceable
to this arm". Nothing in the code checked traceability. The shapes it excluded
were the shared spend ledger, the contamination and incident ledgers, the frozen
candidates stream, the baseline ledger and the monitor's own state; what
survived was mostly Markdown and source, where a stray write is least likely.
The exclusion had been derived from the only cross-territory write anyone had
ever observed, so the one observed shape of the offence became permanently
invisible.

**What replaced it.** `ablcore/outside.py`. Three fixes, all three from the
audit's own suggestion list.

1. **Empty-run control.** `snapshot → idle → snapshot` gives a background set;
   `snapshot → run_arm → snapshot` gives the observed set; only
   `observed − background` is reported. The subtraction is by *behaviour* —
   background noise appears in both legs, this arm's writes only in the second —
   not by appearance. It introduces no new concept, and it covers runtime files
   that do not exist yet, which a hand-written table cannot.
   **Idle length.** The real leg's duration is not knowable before it runs, and a
   single constant either under-covers (weakening the control) or over-covers
   (inflating the background, which masks escapes — the failure being fixed). So
   it is a **2.0s floor plus a make-up window**: after the run, if the real leg
   outlasted the idle leg, idle again for exactly the shortfall and union that
   background in. Exposure is then always ≥ the run's and never much more. The
   honest caveat: the make-up window sits *after* the run, so the control
   brackets the run rather than strictly preceding it. Both durations ride along
   in `Observation` so the alignment is checkable, and one assertion checks it.
2. **Hard list, never subtracted** even when it is background noise, with the
   consequence of a foreign write written next to each rule: `spend_gate.jsonl`
   (spending out of control), `arc-recon/data/*.jsonl` (the pile-cut record
   tampered with), `CONTRACTS/**` (a frozen contract routed around),
   `monitor/state.json` (the watcher edited by the watched), `**/ledger.jsonl`.
   Two extensions are kept in a separate tuple so a reader can see what the
   ticket mandated and what was added: `**/ledger.*.jsonl` (ten sharded ledgers
   exist on this tree and the unsharded pattern reaches none of them) and
   `**/candidates.jsonl` (the append-only frozen stream, which the audit's table
   names and which does not live under `CONTRACTS/`).
3. **Negative controls, shown failing against the old code.** One byte created
   under `proxy/var/`, and — because a created file is a pure key addition that
   *any* diff would catch — one byte **appended to a file that already existed
   before the first snapshot**, which is the shape a real escape would take.
   Both are run through `outside.superseded_criterion`, the falsified tuple kept
   executable for exactly this purpose, and both are shown to be **let through**
   there. Per V12/V16: a control that is also red against the old code is not a
   control for this change. Both victims are this arm's own litter, removed in a
   `finally`, asserted gone; no foreign ledger is corrupted to test the alarm.

A fourth, unasked-for fix rides along because the audit's finding had two
halves. `pin.SKIP_DIRS` drops any directory named `artifacts` or `runs`, so
`engine-rig/artifacts/candidates.jsonl` was never *hashed*, and no criterion
could have reported it. `outside.SKIP_DIRS` skips only VCS/build/cache scratch,
and top-level files (`PARTNER_SYNC.md`, `CLAUDE.md`, …) are watched too — the
old check watched directories only, so a run that appended to the shared status
board would have passed it. 2 430 files are now watched, against 468 before.

**Measured.**

| | |
|---|---|
| files watched | 2 433 (was: six trees, `artifacts/`+`runs/` skipped, 468 files) |
| background set, this worktree | 0 paths (idle 2.0s) — and that is a finding, see below |
| observed set, real run | 0 paths |
| reported | 0, in 12/12 repeat trials (`07`) |
| alignment | idle sleep 2.0s ≥ action 1.00s, make-up 0.00s |
| negative control (create, repo root) | reported ✅ / superseded criterion lets it through ✅ / invisible to `pin` ✅ |
| negative control (append, repo root) | reported ✅ / superseded criterion lets it through ✅ |
| concurrent-writer control (`03c`) | ordinary path **subtracted**, hard-listed path **reported anyway** — same writer, same cadence |
| audit's six hidden paths | 6/6 hidden by the superseded criterion, 6/6 on the hard list |
| hard-list patterns matching a real file | 6 of 7 (`spend_gate.jsonl` is gitignored runtime output, absent on a fresh checkout — which is why it is pinned by name, and cross-checked against `proxy.paths.VAR_DIR`) |
| live-tree churn (`08`, 110 windows / 263s) | 24 windows moved something, p = 0.22, **residual false red ~8.7% per run** |
| suite | `python -m pytest` → **65 passed**, exit 0 |
| gate | `bash verify.sh` → **GREEN**, exit 0 |

**The limitation, measured rather than argued.** An empty-run control removes a
writer only if it is active in *both* legs. A writer that is periodic, or simply
sparse, is in neither leg most of the time and in exactly one leg the rest — and
when that one leg is the real one, the check goes red for something this arm did
not do.

The first measurement of this was too small and is left in place, marked, as the
record of an error rather than overwritten: `05` sampled four windows totalling
53s, found the live tree still at 2s/5s/15s and moving four monitor files at
30s, and put the residual at ~2% per run. `08` resampled at 110 windows over
263s: **24/110 windows moved something, p = 0.22, residual ~8.7% per run**, four
times the first figure. The dominant writer — `monitor/ci/merge.log`, the CI
merge loop, in 12 of the 24 — was never sampled by the first frame at all.

It is left in place deliberately. `.log` was one of the seven tokens the
superseded criterion excluded, so excluding `monitor/ci/merge.log` by name is
the precise defect this ticket removes. Retrying on red and reporting only what
repeats would remove the false red and would also remove a genuine escape that
only fires on a cold first run; trading a ~9% false red for a silent false
negative is the trade that produced the audit finding. A red carries
`background`, `observed`, `subtracted` and `unreadable` with it, which is what a
reader needs to tell a timer from an escape: an escape reproduces, a timer does
not.

And the objection that no tuning answers: a single-sample control subtracts with
probability ~p and pays a false red with ~2p(1−p). No window length drives that
to zero — short means nothing is subtracted, long means false positives become
false negatives. The 2.0s floor sits at the "subtract almost nothing" end on
purpose.

**The adversarial review overturned most of the first draft.** Full text in
`runs/…/ADVERSARIAL-VERBATIM.md`, verbatim; what changed in response, item by
item, in `ADVERSARIAL-RESPONSE.md`. Three verdicts, all WEAK. The load-bearing
ones:

* **The control is inert where this gate runs.** `observe()` roots at the
  worktree, and under `monitor/ci_merge.py` that is a throwaway checkout with no
  fleet in it — 0 background paths in 75/75 idle windows. So in CI this is
  currently a plain "nothing outside moved" and the control contributes nothing.
  That is now the first thing the module docstring says, and `message()` prints
  it on any red with an empty background. It is insurance, not the mechanism:
  what it prevents is not a failing test but the *fix* someone reaches for when
  a test fails.
* **Both negative controls were firing against a test that predates A9.** The
  victims sat under `proxy/var/`, which `pin` hashes unconditionally, so the
  pre-existing upstream test caught the same byte. Both victims moved to the
  repo root and both tests now assert `victim not in pin.hash_tree()`.
* **My residual false-red figure was wrong by 4×**, from a four-window frame.
  Re-measured above.
* **`.env` was not watched at all** — `watched()` dropped every top-level
  dotfile while walking nested dot-directories anyway. Now skipped by name;
  `test_dotfiles_at_the_root_are_watched_because_one_of_them_is_the_key` pins
  it. Only sha256s are taken, never bytes.
* **`subtracted` and `reported_by_hard_list` had never executed on real data.**
  `test_the_subtraction_and_the_hard_list_against_a_real_concurrent_writer` now
  *is* the concurrent session — a thread appending to two files across both
  legs, one ordinary and one matching the mandated `**/ledger.jsonl` rule — and
  asserts the first is subtracted and the second reported anyway. `03c` is the
  measured form.
* **My two hard-list extensions over-matched.** Of 18 files matching
  `**/candidates.jsonl`, only 2 were the frozen stream; ten were another
  territory's regenerated QC scratch, which would have made this check
  deterministically red for something this arm did not do — the exact pressure
  that produced the tightening being undone. Narrowed to
  `engine-rig/**/candidates.jsonl` and `baseline-arms/**/ledger.*.jsonl`. **The
  mandated five are untouched**; the extensions were mine to narrow.
* **`aligned` compared the wrong quantities** (both legs pay one snapshot, so it
  cancels), and the **`OSError` swallow** hid a locked file from the evidence in
  both directions. Both fixed; `Observation` now carries `action_seconds`,
  `idle_sleep`, `makeup_sleep`, `snapshot_seconds` and `unreadable`.
* **The `spend_gate.jsonl` assertions were tautologies** — a literal compared
  against itself retyped. Now derived from `proxy.paths`.

**And one the review did not find, which moving the victim exposed.** `observe()`
enumerated the watched top-level entries once and reused the list for every
snapshot, so **a new file or directory created at the repo root during the run
was never hashed and never appeared in the diff**. A run that dropped a file in
the repo root would have passed silently — verbatim the failure
`test_a_full_run_writes_only_inside_this_arm`'s docstring claims to catch. Each
snapshot now re-enumerates, and the relocated negative control is the regression
test. That bug was only reachable because the review forced the victim out of
`proxy/var/`; it is the best argument in this entry for having run the review.

**Tree discipline.** `run_arm` and `verify.sh` rewrite this arm's own committed
artifacts (timestamps in `episode.jsonl`, `run_all.json`, `verify.json`); every
one was restored with `git checkout -- ablation-arm/artifacts` and
`git status ablation-arm/` is clean apart from the intended changes. Nothing
outside `ablation-arm/` is modified by this ticket; the negative controls' files
are uniquely named, live at the repo root for the length of one `observe()`
call, and are removed and asserted gone in a `finally`. No file belonging to
another territory is written at any point.

**Left for whoever owns the monitor, not decided here.** `monitor/bus/*`,
`monitor/board/board.log` and `monitor/inbox/*` are written continuously during
a live dispatch and are *not* on the hard list, so an arm forging a board claim
during one could be subtracted as background. They are the monitor's territory
and the ticket's hard list did not name them; adding them is a monitor-side
call.
