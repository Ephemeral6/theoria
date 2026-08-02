# RUN_STATE · A23-anchor-drift-on-the-default-leg

Branch `agent/a23-anchor-drift-on-the-default-leg`, base `1e5b3f00`, worker
`W-9202`. Offline throughout: zero ARC actions, zero model calls, zero network,
`$0.00`, zero sealed-pile contact.

## What was asked and what happened

GAP R2-1: a leg on the default frontier cannot see its own anchor drift,
because keeping `--frontier ablation` byte-identical means the anchor block is
written only when a switch is on. R3 paid the forward half. This pays the
backward half — a tool that computes the drift triple for any archived leg,
offline, from `probes.jsonl` (tracked) and `trace.jsonl` (gitignored).

Delivered: `armtools/anchor_drift.py`, `tests/test_anchor_drift.py` (33 tests),
and this run directory. Eight legs measured — 72 probes, 47 drifted, 47 drifted
and off-frontier. The four R1/R1b legs had never had an anchor number at all
and now have one (20 probes, 12 drifted). The four legs R2 measured reproduce
**35 of 52 exactly**, per leg, per probe, and as sets of probe ids, by a reader
that shares no line with R2's.

Nine negative controls, all held. Two synthetic legs per compiled manual, on
two development-pile games: the self-consistent leg must drift on exactly no
probe, the mispredicting leg on exactly `[P-04, P-05]` (derived from the roll
arithmetic, not restated), and a cascade leg answering in four frames per
command must not move the triple. Plus three refusals, each required to name
its own reason.

## What was not delivered as asked

The ticket wanted the triple written **inside each measured leg's own `runs/`
directory**, reasoning that a new file changes no byte the published manifest
covers. It does — measured, not argued: `backfill._files_the_clone_carries`
takes `runs/20260731T1240Z-A3-level2-carried` from 37 paths to 38, so
`backfill.render(build(...))` stops matching the manifest and
`verify_provenance` check 8 goes red for a live-spend archive record.
Absorbing it means regenerating four manifests that R2 and R3 each declined to
touch by name, and that GAP A3-B-3 already reports as CRLF-red on a fresh
worktree.

Each leg still gets its own file — `ANCHOR_DRIFT.<leg>.json`, eight of them —
filed under the run that took the measurement. `GAPS.md` GAP A23-1 carries the
evidence so the trade can be reversed knowingly.

## What three adversarial passes changed, since it is most of the value here

Each of these was written wrong first and is corrected in place rather than
quietly fixed, because the wrong version is the more instructive record.

1. **`crosscheck()` could not support its own docstring.** It compared the
   `(leg, probe_id)` pairs both readers carried and skipped the rest, so
   `equal: true` was reachable while the two disagreed about which probes
   exist — and while a leg it named had never been opened (withhold one
   `trace.jsonl` and a four-leg crosscheck still said EQUAL over 52 probes).
   Now compares row sets as sets, and a leg it could not measure fails the
   comparison instead of counting zero.
2. **Two control predicates were too weak to be worth writing.**
   `drifted == 0` folds an *unknown* anchor into the same zero as an anchored
   one, so a leg whose trace notes no longer join would have passed the
   self-consistent control. `drifted > 0` accepts the check firing anywhere —
   which is how a comment in this directory came to predict `P-03` onward
   while the file's own output said `P-04`, `P-05`.
3. **The mispredicting control cannot witness the finding it looked like it
   witnessed.** Freezing the state collapses the frontier to width 1, so its
   drifted probes are off-frontier *because of the collapse*. On the toy manual
   the collapse is strictly wider than the drift. GAP A23-3; asserted in the
   suite rather than mentioned.
4. **The headline second finding was inverted.** The anchored probe ids looked
   periodic and were filed as *a period observed and not explained*. The period
   is `MIN_NEW_FRAMES_BETWEEN_THEORIZE = 4` (`inner/loop.py:86`) and every
   measured leg's own `turns.json` prints the gate firing. The corrected
   finding is smaller and better: **the anchored ids are exactly the theorize
   turns on four of the six legs with probes** — the manual is right when
   freshly written and wrong by the next probe. What is genuinely open is the
   two exceptions. GAP A23-2.
5. **Three overstatements struck.** "across five days" — the eight legs span
   11 h 56 m. "Seven of eight legs support the pattern" — three of those seven
   have zero or one anchored probe and cannot test it. And
   `recorded_vs_recomputed_disagreements: 0` was called evidence about the
   recording; it is a tamper check that holds by construction, since both
   columns come off the same `Step` objects through the same production code.

## Numbers a later reader should not have to re-derive

* **72 probes, 47 drifted, 47 drifted-and-off-frontier**, eight legs.
* **Only 5 of the 72 ever landed on-frontier at all** — all five on
  `sk48-carried-l1`, all five anchored, all five named by `manual`. On the other
  seven legs the on-frontier count is 0 of 16 anchored *and* 0 of 40 drifted, so
  the entire drifted-vs-anchored contrast comes from one leg (Fisher one-tailed
  p ≈ 0.004).
* **20 of the 25 anchored probes were off-frontier too.** Anchoring is
  necessary, nowhere near sufficient.
* **16 of the 72 rows are byte-identical repeats** — 8 of them on
  `sk48-carried-l1`. 56 distinct experiments; de-duplicated triple 56 / 33 / 33.
  The arm as it stands today refuses these. GAP A23-5.
* **`frontier_width_distinct` is 2 on all 72**, against 9–24 hypotheses.
* `R1b-sk48-b`'s single probe came back HTTP 400 with no frame. Its
  `drifted: false` is genuine; its `off_frontier: true` means nothing.

## Gates

`GATES.txt`, verbatim. The suite's five pre-existing failures were reproduced on
an untouched `master` worktree before anything here was written, and are named
there.

## Next

Nothing in this ticket changes the arm's path — `inner/`, `world/` and
`harness/` are untouched, so no leg's bytes can move. Five gaps are left
standing (A23-1 … A23-5); the cheapest and most informative is A23-2's join of
each probe to the snapshot the arm held when it designed it, which needs no new
data and would settle both exceptions.
