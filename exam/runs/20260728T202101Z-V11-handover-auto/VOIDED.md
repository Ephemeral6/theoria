# VOIDED — this run's answers are not a result

The sheet built here printed `"dead"` in the `tags` of the two optimal-action
items whose boards have no solution. `Item.tags` is shown to the examinee, so
those two items came with their answer attached.

Six readers had already been spawned when this was found, and a spawned subagent
cannot be stopped by the agent that spawned it. They were allowed to finish. Their
answers are kept in `answers/` **as evidence about the leak**, never as a score:
no number from this run appears in any `RESULTS.json`, and the run has no
`RESULTS.json` of its own.

The clean run is `exam/runs/20260728T202540Z-V11-handover-auto-r2`. Its
`BLINDING.md` carries the full account, including why the leak checker missed it
and what now stands in that gap.

---

**Correction (V26, 2026-07-29): the last sentence above is wrong.** `-r2` was not
clean. It carried a second, undetected leak into the same two items -- family-scoped
`level:` tag multiplicity, 8 of 8 at an exact false-positive rate of 0.035714 --
found only after it had been sat, when V25 switched on the pooled private-marker
cut. `-r2` is annulled as an instrument on its `optimal_action` family (not voided;
the ruling says why) and the paper is repaired. See
`exam/runs/20260729T2215Z-V26-handover-leak-ruling/RULING.md`.
