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

## The judges were also blinded to each other — and only partly to V11

Each agent received:

* the three questions, transcribed from V11's own method section, verbatim;
* its own list of paths;
* one output format.

It received **no** V11 rows, so it could not copy a neighbouring judgement for a
similar file, and **no** statement of what the aggregate result was supposed to
show. The `BRIEF.md` never says which direction of answer would be convenient.

> **An earlier version of this section continued: "**no** counts, so it had no
> target to hit." That was false, and the adversarial pass caught it.** See the
> next section. The claim is withdrawn, not rephrased.

## The blinding was breached, and the breach is the delivery discipline itself

Deleting `verify-lab/` removed every per-file verdict table. It did not remove
the answer key, because the answer key had been copied out of `verify-lab/` and
into a file at the repository root.

**`PARTNER_SYNC.md` is tracked, is in every checkout, and was in all nine judges'
trees.** By this repository's own convention every finished item appends a
paragraph to it. Two of those paragraphs are V11's and V14's:

| line | what it carries |
|---|---|
| 940 | V11's aggregate answer: 「**127 道入口**：能红「否」15、**有负控「否」35**、退出码诚实「否」13；实测支撑 24 行」 — the count, the base rate, and the evidence-class split |
| 958 | V14's headline 「枚举 141 个验收入口 … **FNR 32%** … 110 缺 / 31 有」, **and a per-file probe verdict**: 「`worldgen/build.py` 被判 present」 |

`worldgen/build.py` is the **single false positive in the pinned matrix**. Its
probe verdict was sitting in every judge's tree.

Also tracked, also present: `monitor/board/done/V11-…RES-3.md` and
`monitor/board/claimed/V14-…RES-3.md`, the latter being V14's own work order.

**This is not "the judges peeked."** Nothing suggests any of them opened
`PARTNER_SYNC.md`; they were told to judge from source and their evidence columns
cite line numbers in the files they were given. **The structure failed to prevent
it**, and the structure is a delivery discipline — one appended paragraph per
finished item, at the repository root, in every checkout — colliding with a
blinding protocol that only ever thought about `verify-lab/`. Whoever writes the
protocol owns the collision; that is this run's author, not the nine judges.

### Exposure, measured rather than waved away

`verify-lab/frame/leakage.py` computes it. A judged path counts as *exposed* if
its name appears in a tracked, non-`verify-lab` text file that **also** discusses
negative controls (`负控` / `FNR` / `混淆矩阵` / `KNOWN_GAPS` / "negative
control").

```
judged paths                    126
exposed                          29 (23%)
  present rate, exposed          0.55
  present rate, unexposed        0.34
  pool                           0.39
  one-sided binomial p           0.055
top sources: PARTNER_SYNC.md (9), papers/phase1-workshop/PAPER.md (8),
             papers/phase1-workshop/CITECHECK.md (4)
```

The adversarial pass, with a slightly narrower word list, got 27 / 0.52 / 0.35 /
p 0.121. **The harsher of the two measurements is the one published here**, and
p = 0.055 is close enough to conventional significance that it must not be waved
off as noise.

**Three things follow, and the second is the one that matters.**

1. It is confounded. The paths `PARTNER_SYNC.md` names are the flagship gates,
   which genuinely are the ones most likely to have controls. A correlation was
   expected before any leak was.
2. **The direction is against us.** Exposed rows were judged `present` *more*
   often. A gold `present` that the criterion scores `absent` is a **false
   negative** — so any contamination inflates FN, which is precisely the
   direction that flatters V15's headline. We do not get to use a bias that
   points our way as evidence for our conclusion.
3. **The conclusion survives deleting every exposed row.** Recomputed with all
   28 scoreable exposed supplement rows removed from the gold standard:

   | pinned matrix (strict) | n | TP | FN | FP | TN | FNR |
   |---|---|---|---|---|---|---|
   | V11 gold only | 76 | 29 | 19 | 1 | 27 | 0.396 |
   | V11 + V15 (published) | 145 | 35 | 36 | 1 | 73 | **0.507** |
   | V11 + V15, **every exposed row deleted** | 131 | 33 | 31 | 1 | 66 | **0.484** |

   0.507 → 0.484. Still far above V14's published 0.318 and still above the
   V11-only pinned 0.396. **The leak cannot account for the finding.**

### The fix, for whoever runs the next blind pass

Not done this round — changing the protocol mid-run would invalidate the
judgements already collected.

* The judges' tree should be built by `git archive` **and then**
  `git rm PARTNER_SYNC.md monitor/inbox/ monitor/board/ monitor/audit/`, or built
  from an orphan checkout containing only the territories under judgement.
* Better: `leakage.py` should be run **before** the briefs go out, and any path
  it flags should be either re-judged from a clean tree or reported separately.
  It exists now; it did not exist when it was needed.
* Structural point worth keeping: **a repository whose delivery discipline
  publishes findings to a root-level tracked file cannot host a blind study by
  deleting one directory.** Every future blinding claim in this repository has to
  name `PARTNER_SYNC.md` explicitly and say what was done about it.

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

4. **Two frame units could not be blind-judged at all.** Judging them requires
   reading them, and reading them is the thing the blind forbids. They are
   excluded from the supplement and counted as such — 126 judged of a 128-unit
   non-suite difference set.

   > **This entry named the wrong second file, and the adversarial pass caught
   > it.** It said `verify-lab/negctl/criterion.py`. **`criterion.py` is not a
   > frame unit at all** — no `__main__`, so stratum A fails; it raises no
   > repository-defined exception, so stratum B fails. It is absent from
   > `frame.py --list`, verified directly.
   >
   > The two excluded units are `verify-lab/negctl/probe.py` and
   > **`verify-lab/negctl/calibrate.py`** — line 122 of the archived
   > `difference_set.txt`. The arithmetic 126 + 2 = 128 was right by accident.
   >
   > The error mattered in the worst direction: `calibrate.py` **is the file that
   > computes and prints V14's confusion matrix**. It is the answer key in
   > executable form, and it is the one exclusion that most needed justifying.
   > Naming `criterion.py` instead concealed that. The justification, stated now:
   > it is excluded for the same reason as `probe.py` — a blind judge cannot read
   > it — and the exclusion is exactly the kind this document exists to log
   > rather than let pass.
