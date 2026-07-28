# `audit` — E7, checking a negative result about deadlocks

E2 measured Theoria §1.9's promise that *每证一个死锁，规划器同时提速* and
reported that the speed-up half fails. This package audits that report.

```bash
cd engine-rig
export FAST_DOWNWARD=".../.toolchain/downward/fast-downward.py"
python -m audit --out runs/<id>
```

It **refuses to run without a real Fast Downward**. The claim is about a real
planner; measuring it against the bundled stub would answer a different question,
and answering a different question quietly is the failure mode this whole
exercise is about.

The conclusion, the evidence and a suggested wording for the design document are
in [`../DEADLOCK_CLAIM.md`](../DEADLOCK_CLAIM.md). This README is about the
measurements.

## Five sections, each answering a named objection

| section | objection it answers | how |
|---|---|---|
| `replication` | "did it reproduce?" | E2 §3b re-measured from a fresh process, singleton guard held fixed on both sides |
| `wiring` | "nothing was pruned" | counts the pruner's firings on the bundled rung, and — with an independent walk that never consults it — how much of the reachable space is dead |
| `coverage` | "*why* zero?" | three sets over the whole reachable space: truly dead, delete-relaxation dead, theorem dead |
| `relaxation_vs_fd` | "your relaxation is not FD's" | rebuilds sampled states as one-state problems and compares against FD's translator verdict |
| `dead_starts` | "the planner was never asked" | instances whose *initial state* is already dead, one per theorem kind, with a live control |
| `size_ladder` | "the instances are too small" | the same guard and configurations at `far8`, where blind expands five figures |

## Two things this package does deliberately

**It writes its own breadth-first walk.** `engines/fd_adapter/search` has one,
and using it would mean the module whose pruning hook is under suspicion is also
the module reporting how much there was to prune. The walk in `claim.py` uses
only data-level primitives (`ground_actions`, `applicable`, `successor`) and
never touches a pruner.

**It reimplements the delete relaxation in Python.** Not because Fast Downward's
is unavailable, but because the interesting number needs it evaluated on 3 342
states and that is 3 342 subprocesses otherwise. An independent reimplementation
nobody compared to the original is a second guess rather than a second opinion,
so `relaxation_vs_fd` compares them state by state and the agreement count is
reported next to every conclusion that rests on it (16/16 at the time of
writing).

## The prediction this package got wrong

`deadstart.py` was built to test a split: corner deadlocks (`no_deleting_action`
— grounding discarded every push) should survive the delete relaxation, while
pair deadlocks (`deleting_actions_blocked` — the pushes exist and need a cell the
other box holds) should not, because the relaxation drops exactly the deletes
that argument turns on.

**They do not split.** The relaxation catches both, and the reason is worth more
than the prediction was: dropping deletes does not *manufacture* atoms. `clear`
is false on a box's cell at the start and the relaxation never adds it back
without an actual push, so the player still cannot get between two adjacent
boxes. The module keeps its original reasoning in its docstring, and the result
that refuted it beside it.
