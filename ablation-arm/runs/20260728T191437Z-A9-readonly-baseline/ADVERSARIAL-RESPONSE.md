# What the adversarial review changed

Its full text is in `ADVERSARIAL-VERBATIM.md`, unedited. Three verdicts, all
WEAK. Nothing below argues with it; where it was right the code changed, and
where a finding was accepted and *not* fixed the reason is stated rather than
the finding being softened.

## Overturned outright

**1. My residual false-red number was wrong by 4x, from a sampling frame too
small to see the biggest writer.** `05-live-background-churn.json` took four
windows totalling 53s and concluded the live tree is quiet. It is not.
`08-live-background-resample.json` re-measured at 110 windows over 263s:
**24/110 windows moved something (p = 0.22, Wilson 95% 0.15-0.30), residual
false red ~8.7% per run** against the ~2.3% I recorded. The dominant writer is
`monitor/ci/merge.log` — the CI merge loop, 12 of the 24 windows — which my
frame never sampled once. The review said ~6%; the wider frame says the review
was, if anything, generous to me. `05`/`06` are kept as the record of the
undersized measurement rather than quietly overwritten, and both now carry a
`superseded_by` pointer.

The review also caught `06` computing its headline from `gap_seconds_min` while
its prose used the median — two estimators in one number. `08` uses one
estimator (events per second of exposure) and says which.

**2. The empty-run control is inert where this gate actually runs, and I had not
said so.** `observe()` roots at `_bootstrap.REPO`, which under
`monitor/ci_merge.py` is a throwaway worktree with no `proxy/var/` and no fleet.
The review measured 0 background paths in 75/75 idle windows there; my own
`01`/`02`/`07` artefacts agree (`background: []`, 12/12 trials). So in CI this
check is a plain "nothing outside the arm moved" and the control contributes
nothing. That is now the first thing the module docstring says, and
`Observation.message()` prints it on any red with an empty background.

I do not think this makes the control worthless, and the docstring says why: it
is insurance against the day the fleet writes into the worktree, and the failure
it prevents is not a failing test but the *fix* someone reaches for when a test
fails. But "it is doing nothing today" is a fact and it is now written where a
reader hits it first.

**3. Both negative controls were firing against a test that predates A9.** The
victims lived under `proxy/var/`, and `proxy` is in `pin.UPSTREAM_TREES` with
`var` not in `pin.SKIP_DIRS` — so
`test_a_full_run_leaves_every_upstream_tree_byte_identical`, untouched and never
broken, caught the same byte unconditionally. The controls demonstrated a
capability the file already had. Both victims moved to the repo root, which only
`outside.watched()` covers, and both tests now assert `victim not in
pin.hash_tree()` so the discrimination is checked instead of assumed.

**4. `.env` was not watched at all.** `watched()` dropped every top-level name
starting with `.` while nested dot-directories were walked anyway. `CLAUDE.md`
makes `.env` the highest-consequence file in the repo. Skipping is now by name;
`test_dotfiles_at_the_root_are_watched_because_one_of_them_is_the_key` pins it.
Only sha256s are taken, never bytes, so watching it cannot leak the key.

**5. The hard list's mechanism had never executed on real data.** `subtracted`
and `reported_by_hard_list` were reachable only from a hand-built `Observation`.
`test_the_subtraction_and_the_hard_list_against_a_real_concurrent_writer` now
*is* the concurrent session: a thread appends to two files across both legs, one
ordinary and one matching the mandated `**/ledger.jsonl` rule, and asserts the
first is subtracted and the second reported anyway. Same writer, same cadence,
opposite verdicts. This is the only test that runs the subtraction end to end.

**6. My two hard-list extensions over-matched another territory's scratch.** Of
18 files matching `**/candidates.jsonl`, only 2 were the frozen stream; ten were
`worldgen/out/qc/*/candidates.jsonl`. Since the hard list is never subtracted,
a neighbour regenerating QC scratch would have made this check deterministically
red — the exact pressure that produced the tightening the DRIFT note documents.
Narrowed to `engine-rig/**/candidates.jsonl` and
`baseline-arms/**/ledger.*.jsonl`. **The mandated five are untouched**: the
ticket said no discounts, and the extensions were mine to narrow.
`.pytest-runs` joined `SKIP_DIRS` for the same reason — it is pytest's temp
directory, the same class as `.pytest_cache`, and without it the mandated
`**/ledger.jsonl` rule reached another arm's test scratch.

**7. `aligned` was comparing the wrong quantities.** It tested
`2*snapshot + sleep >= action + snapshot`, so it reported aligned while the
control was short by up to one snapshot's exposure. Both legs pay exactly one
snapshot per file, so it cancels: the predicate is now sleeps vs action, and
`Observation` carries `action_seconds`, `idle_sleep`, `makeup_sleep` and
`snapshot_seconds` so the arithmetic is checkable. The make-up window's
shortfall is computed the same corrected way.

**8. The `OSError` swallow hid evidence in both directions.** A file locked
across one snapshot is a phantom diff; locked across both, it vanishes from the
evidence entirely and no hard list can reach it. `snapshot()` now records
unreadable paths and `Observation.unreadable` reports the count.

**9. The `spend_gate.jsonl` assertions were tautologies** — a literal in
`outside.py` compared against the same literal retyped in the test.
`test_the_ledger_rules_are_checked_against_the_proxy_s_own_layout` now derives
from `proxy.paths.VAR_DIR` / `LEDGER_PATH`, the module whose docstring says "One
module so no other file guesses at the layout". `spend_gate.jsonl` itself is not
a constant there (the gate takes its ledger path from configuration), so what is
pinned is the directory and the sibling ledger; move `VAR_DIR` and the suite
goes red.

## Found while fixing the above, and worse than anything in the report

Moving the negative control's victim to the repo root made it **stop being
detected**. `observe()` computed the watched top-level list once and reused it
for every snapshot, so a **new file or directory created at the repo root during
the run was never hashed and never appeared in the diff**. A run that dropped a
file in the repo root would have passed silently — which is verbatim the failure
`test_a_full_run_writes_only_inside_this_arm`'s own docstring says it exists to
catch. Each snapshot now re-enumerates. The relocated negative control is the
regression test for it.

That bug existed only because the review forced the victim out of `proxy/var/`.
It is the strongest argument in this file for the review having been worth
running.

## Accepted, not fixed, with reasons

* **The single-sample estimator cannot be tuned out.** A one-window control
  subtracts with probability ~p and pays a false red with ~2p(1-p); no window
  length drives that to zero. The 2.0s floor deliberately sits at the p→0 end:
  it subtracts almost nothing and pays ~9% false reds. That is the side of the
  trade the audit finding says to be on — a red costs a re-run, and the other
  side is silence.
* **The `.log` false-positive class is re-opened on purpose.** `.log` was one of
  the seven superseded tokens, and `monitor/ci/merge.log` is now the single
  largest source of false reds. Excluding it by name is the defect this ticket
  removes.
* **The Windows lock on `proxy/var/spend_gate.jsonl.lock` can still produce a
  phantom diff.** It is now counted rather than swallowed, but not suppressed;
  suppressing a path under `/var/` by name is how the original bug was written.
* **`monitor/bus/*`, `monitor/board/board.log`, `monitor/inbox/*` are not on the
  hard list**, so a forged board claim during a live dispatch could be
  subtracted. They are the monitor's territory and the ticket's hard list did
  not name them; adding them is a monitor-side call, not this arm's. Flagged
  here rather than decided unilaterally.
* **The negative controls are visible to a concurrent observer for 1-2s.** The
  review saw the earlier `proxy/var/` victims appear and disappear from its own
  probe, with no leak. Now that both victims are at the repo root and outside
  every upstream tree, they are outside `pin`'s reach entirely — but a
  root-level file is still visible to anything watching the root. Cleanup is in
  a `finally` and asserted; the residual is one uniquely-named file for the
  length of one observation.

## Not accepted

Nothing. Every finding was either fixed or recorded above with a reason.
