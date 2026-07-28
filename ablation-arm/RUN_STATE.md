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
| files watched | 2 430 (was: six trees, `artifacts/`+`runs/` skipped) |
| background set, this worktree | 0 paths (idle 2.5s) |
| observed set, real run | 0 paths |
| reported | 0 |
| alignment | idle 2.58s ≥ run 1.77s, make-up 0.00s |
| negative control (create) | reported ✅ / superseded criterion lets it through ✅ |
| negative control (append) | reported ✅ / superseded criterion lets it through ✅ |
| audit's six hidden paths | 6/6 hidden by the superseded criterion, 6/6 on the hard list |
| hard-list patterns matching a real file | 6 of 7 (`spend_gate.jsonl` is gitignored runtime output, absent on a fresh checkout — which is why it is pinned by name, not by presence) |
| suite | `python -m pytest` → **62 passed**, exit 0 |
| gate | `bash verify.sh` → **GREEN**, exit 0 |

**The limitation, measured rather than argued.** A background set of zero inside
this worktree measures the criterion but not the problem, so the same machinery
was pointed read-only at the live worktree where the fleet actually runs
(`05-live-background-churn.json`). It is completely still at 2s, 5s and 15s, and
at 30s four files move: `monitor/index.html`, `monitor/reflex.lock`,
`monitor/reflex.log`, `monitor/state.json` — the monitor's reflex loop, 127 ticks
logged, median gap 300s, shortest 42s (`06-periodic-writer-residual.json`).

That is a **periodic** writer, and an empty-run control removes a writer only if
it is active in both legs. This one is in neither leg ~98% of the time and in
exactly one leg the rest, so against a ~0.95s run leg it is a residual **false
red of about 2% per run**. It is left in place deliberately: excluding those four
paths by name or by shape is the precise defect this ticket removes, and the
superseded criterion would have reported two of the four while hiding the other
two — including `monitor/state.json`, which is on the hard list because it must
never be hidden. Retrying on red and reporting only what repeats would remove
the false red and would also remove a genuine escape that only fires on a cold
first run; trading a 2% false red for a silent false negative is the trade that
produced the audit finding. So a red carries `background`, `observed` and
`subtracted` with it, which is what a reader needs to tell a five-minute timer
from an escape: an escape reproduces, a timer does not.

The same measurement is the answer to "is the hard list decoration": on the live
tree `monitor/state.json` moved as pure background noise inside a 30s window, so
`Observation.reported_by_hard_list` is reachable in a real run and not only in
the hand-built unit test. That is the occasional false red the audit said was
worth accepting, observed rather than predicted.

**Tree discipline.** `run_arm` and `verify.sh` rewrite this arm's own committed
artifacts (timestamps in `episode.jsonl`, `run_all.json`, `verify.json`); every
one was restored with `git checkout -- ablation-arm/artifacts` and
`git status ablation-arm/` is clean apart from the intended changes. Nothing
outside `ablation-arm/` is modified by this ticket; the two negative-control
bytes under `proxy/var/` exist only inside a single `observe()` call and are
removed and asserted gone in a `finally`.
