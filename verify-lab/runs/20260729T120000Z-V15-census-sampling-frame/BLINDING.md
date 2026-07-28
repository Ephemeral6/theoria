# How the manual judging was kept blind to the probe, and where it was not

The item this run repairs is a gold standard that covered 47% of its population.
The obvious way to repair it badly is to fill in the missing 53% *while looking at
what the probe said about them* — which produces a gold standard fitted to the
thing under test, and a confusion matrix that is a tautology. This file is the
record of what was done to prevent that, written in the order it happened, and it
ends with the part that could not be prevented.

## The mechanism: the judges' tree does not contain the probe

`verify-lab/` does not exist on `master`. It exists only on
`agent/v11-negative-control-census` and `agent/v14-standing-negative-control-probe`,
which this branch merged. So a checkout of the repository *without* `verify-lab/`
is not a redaction anybody has to remember to perform — it is the state of the
mainline.

The nine judging agents were given a `git archive` export of this branch's HEAD
with `verify-lab/` deleted, at

    <scratchpad>/blindtree/

and nothing else. In that tree there is no `criterion.py`, no `probe.py`, no
`KNOWN_GAPS.json`, no `CALIBRATION.md`, no `NEGATIVE_CONTROL.md`, and no census
table. A judge cannot read a verdict it does not have, and it cannot read one by
accident. The instruction not to go looking in the main worktree or in
`.worktrees/` was given as well (`BRIEF.md`, 纪律), but the instruction is the
second line of defence, not the first.

The export is read-only in intent and disposable in fact: it is a scratch copy,
so nothing a judge did could reach the repository even if it tried to write.

## The judges were also blinded to each other, and to V11

Each agent received:

* the three questions, transcribed from V11's own method section, verbatim;
* its own list of paths;
* one output format.

It received **no** V11 rows, so it could not copy a neighbouring judgement for a
similar file; **no** counts, so it had no target to hit; and **no** statement of
what the aggregate result was supposed to show. The `BRIEF.md` never says which
direction of answer would be convenient.

## The one instruction that changes the evidence class: nobody ran anything

V11 marked 24 of its 127 rows `实测` — the auditor ran the entry point and
watched the exit code. V11 then found that this was a mistake *as executed*: the
six auditors shared one worktree, several entry points write into the tracked
tree, and so a finding of the shape "I ran X and afterwards N tracked files
changed" could not be attributed to X. V11 wrote that up as its own method
defect.

This run does not repeat it, and pays for that:

> **Every cell in the V15 supplement is `读码`.** No judge executed any entry
> point. The batch is a code-reading census.

That is a real weakening against V11's standard, and it is stated in the
supplement table as well as here. It buys the removal of the cross-contamination
confound and the guarantee that nine parallel agents left the repository exactly
as they found it. It costs the class of finding that only running produces —
V11's sharpest such finding (`arc-recon/contamination.py` printing
`sealed ADDRESSED:` and exiting 0) was `实测`, and a `读码` judge is more likely
to credit an exit path that in practice is unreachable.

**Consequence for the confusion matrix:** a supplement built entirely from
reading is more likely to say a gate *can* go red than a supplement built from
running it. It is not obviously biased for or against the *negative-control*
column, which is the column the matrix is computed over, because that column was
already predominantly `读码` in V11.

## What was not blinded, and cannot now be

Stated plainly, because a blinding claim with an unstated exception is worse than
no claim.

1. **The aggregator — this session — had already read V14's report before any of
   this started.** The work order itself names
   `cold-start-a2/a2pipeline/engines.py` as the confirmed false positive, so that
   one file's probe verdict was known to the aggregator from the first minute and
   could not be unknown. It was **not** passed to any judge: batch `b5` received
   that path in a list of thirteen with a generic instruction — check whether the
   test targets *this* file or a second implementation elsewhere — that was
   written to apply to the whole batch, and the same shape of warning appears in
   `b3`'s and `b6`'s briefs for library modules. That is a mitigation, not a
   blind. **The judgement on `cold-start-a2/a2pipeline/engines.py` should be
   read as the weakest single cell in this supplement.**

2. **The aggregator read `CALIBRATION.md` and `KNOWN_GAPS.json`.**
   `KNOWN_GAPS.json`'s *keys* had to be read to compute the difference set at all
   — that is unavoidable and harmless, since a path is not a verdict, and
   `verify-lab/frame/reconcile.py` is written to read the keys and never the
   `verdict` field. `CALIBRATION.md` was read for its *method* (how V14 mapped
   census rows to files) after all nine batches were dispatched and before any
   returned; the dispatch timestamps and the read are both in `RUN_STATE.md`. No
   judge could be affected by a read that happened after its instructions were
   sealed, but the aggregator's own later choices — how to resolve an ambiguous
   row, where to draw a tie — were made by somebody who had seen the answer key.
   The defence against that is that those choices are mechanical and in
   `reconcile.py` and `matrix.py`, not in prose.

3. **The frame itself was designed by somebody who knew what V14's enumerator
   does.** `frame.py` deliberately admits three classes V14's enumerator drops —
   files with no non-zero exit path, terminal-refusal libraries, and test suites
   — and it admits them *because* they were known to be dropped. That is the
   correct direction (a frame drawn to exclude the enumerator's blind spots would
   be the fraud this item exists to catch) but it is not neutral, and an
   adversarial pass was commissioned specifically against it
   (`ADVERSARIAL.md`).

4. **Two frame units could not be blind-judged at all**:
   `verify-lab/negctl/probe.py` and `verify-lab/negctl/criterion.py`. Judging
   them requires reading them, and reading them is the thing the blind forbids.
   They are excluded from the supplement and counted as such — 126 judged of a
   128-unit non-suite difference set.
