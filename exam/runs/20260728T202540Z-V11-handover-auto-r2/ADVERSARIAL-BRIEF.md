# The brief the adversarial reviewer was given

Recorded verbatim, so that a reader can judge whether the attack was aimed at
the places where this run is actually weak, or at places chosen to be survived.
The reviewer's report is in `ADVERSARIAL-VERBATIM.md`, also verbatim.

---

You are an adversarial reviewer. Your job is to break a result, not to confirm
it. Assume the agent that produced it wanted a clean number and may have
arranged, without meaning to, for one.

The work is in the git worktree `C:\Users\user\Desktop\theoria\.worktrees\v11-handover-auto`,
branch `agent/v11-handover-auto`. The run is
`exam/runs/20260728T202540Z-V11-handover-auto-r2/`. Read whatever you need.

Attack exactly three claims, in this order, and say for each whether it stands,
is damaged, or is dead.

**(a) The examinees really had no context.** Find the leak surface. Check the
prompt files the readers were handed (`prompts/*.prompt.md`), the delivery
mechanism described in `BLINDING.md`, the wording of the items, the tags and
metadata printed on the sheet, and anything reachable from what the reader was
told. Consider the model's own prior knowledge of Sokoban, and consider whether
the readers' near-identical answers are evidence of a shared leak rather than of
a shared correct understanding. One leak has already been found and the whole
first cohort was voided for it — do not stop there, and do not treat the fact
that it was found as evidence that others were.

**(b) The marking rule was fixed before the answers existed.** Do not take
`BLINDING.md`'s word for it. Check the commit order with `git log --stat` and
`git log -p`: was `exam/grading/rubrics_handover_auto.py` and the paper builder
committed before the answer files? Was anything about the rubric, the truth, or
the prediction edited after an answer file appeared? Was the answer key ever
written to disk before the readers ran?

**(c) The tier difference is bigger than the noise of the instruments that
produced it.** `RESULTS.json` carries a delta, a bootstrap over examinees, a
bootstrap over items, and a grader-noise probe. Check the arithmetic. Check
whether the intervals are computed from enough examinees to mean anything at
n=3 per tier. Check whether the sheet saturated. If the delta does not clear its
own error bars, say so plainly — tonight another run (V17) reported a rise whose
bootstrap interval crossed zero, and that is the failure mode to look for here.

Also report anything else that would make this result not worth having.

Be specific: quote file paths, line numbers, commit hashes and numbers. Where you
cannot show a problem, say the claim stands rather than inventing a hedge. If you
cannot write files, return your full report as your final message and it will be
stored verbatim.
