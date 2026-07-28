# DECISIONS — exam

Design calls and the reason each one was made. A decision without its reason is
a habit, and habits do not survive contact with a reviewer.

---

## D-EX-001 — a question has two sides, and they live in different files

`Item.paper` and `Item.truth` are separate fields, `Paper.sheet()` is built from
a method that never receives the truth, and the two land in
`artifacts/papers/` and `artifacts/truth/` respectively.

**Why.** An exam whose paper carries its answer key measures nothing, and the
failure is silent: the paper still looks like a paper, the examinee still
scores, and the number is worthless. Making the split structural means a leak
requires someone to write the truth into the paper field on purpose, rather than
requiring everyone to remember not to.

**Rejected.** A single `Item` dict with a convention that certain keys are
private. Conventions are enforced by attention, and attention is the resource
that runs out first.

---

## D-EX-002 — leakage is attacked from four directions, three of them code

`exam/leakage.py` runs declared probes, structural key disjointness, and
positional independence. A cheater subagent is then handed the sheet alone.

**Why.** Each check has a blind spot the others cover. Probes catch the leak the
builder can imagine; structural disjointness catches the one they cannot;
positional independence catches the leak that is not in any field but in the
*arrangement* of fields. None of the three catches a leak that lives in the
wording, which is what the cheater is for.

**The probe requirement is deliberately hostile.** An item with a non-trivial
truth and no declared probe fails the check. "I could not think of a probe" is
precisely the state in which leaks survive, so it is treated as a failure rather
than as a pass with a caveat.

---

## D-EX-003 — the rubric is hashed, and the hash travels with the paper

`exam/grading/registry.py` hashes the **source text** of every rubric module in
frozen order. The digest goes onto every sheet at build time and onto every
report at marking time; a mismatch is printed rather than raised.

**Why.** A rubric loosened after the answers came in is the most natural way for
this instrument to lie, and it is not detectable by reading the final numbers.
Hashing the source rather than the rubric ids matters: an id list is stable while
the marking behind it changes. Docstrings and comments are inside the digest on
purpose — a mark whose stated justification has drifted away from its behaviour
is the failure this project cares about most, and a tighter digest over the code
alone would hide exactly that.

**Mismatch warns rather than raises.** Re-marking an old submission under a new
rubric is sometimes the right thing to do; doing it without saying so is not.

---

## D-EX-004 — four fake examinees, pre-registered bands, and a hard block

`exam/grading/calibration.py` runs `oracle`, `null`, `memoriser` and `bluffer`
through every paper and checks each against a band written down in advance.
`assert_calibrated` raises, and `run_exam` calls it before marking anything real.

**Why.** The question-setter can be checked by reading it. The marker cannot — a
marking bug produces a plausible number, and a plausible number is
indistinguishable from a result. The two exact bands (`oracle == 1.0`,
`null == 0.0`) follow from construction: a marker that rejects ground truth
depresses every real score by an unknown amount, and a marker that pays for
silence inflates every one of them.

`memoriser` and `bluffer` are not padding. They are the two arms Theoria.md 1.11
names explicitly — the one that passes by replay ("重放是对过去的预测,背题也能
满分") and the one that buys sensitivity with confidence. A held-out paper that
cannot separate `memoriser` from `oracle` is testing recall; a verdict paper that
scores `bluffer` well is scoring nerve.

**The bands are wide where the exact value depends on item mix**, because pinning
them tighter would freeze item mix as a side effect of calibrating the marker.

**Uncalibrated means no result, not a weak result.** Hence the raise.

---

## D-EX-005 — the four question types sit behind one interface

Every module in `exam/papers/` exposes `PAPER_ID`, `build()`,
`reference_answers()` and `axes()`, and nothing else is required of it.

**Why.** It is what makes this a protocol rather than four scripts. The runner
does not know what a held-out item is, the marker does not know which type it is
marking, and a fifth question type is a new module rather than an edit to the
driver. It also forces every type to produce its own calibration fakes, which is
the requirement that keeps a type from shipping an unfalsifiable marker.

---

## D-EX-006 — sensitivity and specificity are computed together or not at all

`exam.grading.mark.confusion` returns both rates from one call and reports
abstentions as their own counts rather than folding them into either rate.

**Why.** Theoria.md 1.11 is explicit that the verdict item is scored as a pair,
and the reason is stated there: a framework that answers "unsolvable" to
everything has perfect sensitivity and is worthless. Returning them from one
function means neither can be quoted without the other having been computed.

Abstentions stay separate because an abstention is not a wrong answer and it is
not a right one. Folding it into either rate would let a framework improve a
number by declining to answer.

---

## D-EX-007 — the whole rehearsal runs in self-built worlds, and the guard says so

`exam.guard.assert_synthetic_world` accepts `a0` / `a0-prime` / `a2`, refuses the
sealed pile by full and short id, and refuses **dev-pile** games too unless
`allow_dev=True` is passed explicitly.

**Why.** Theoria.md Phase 4 orders the exam's timing to solve a deadlock:
constructing a justified unsolvable variant for a sealed game requires
understanding that game's mechanics, and studying it breaks the seal. The
resolution is sequence — the main table runs first, and only then are the exam
subset's games studied. Rehearsing the whole procedure in worlds we built
ourselves is what makes that sequence affordable: by the time a sealed game is
opened, the operator library, the spec format, the leak checks and the marker
are all proven, and the only new work is the per-game justification.

Refusing the dev pile by default is the same argument one notch weaker. A dev
game spent on a rehearsal question is a dev game spent; it should take a decision,
not a default.

---

## D-EX-008 — `no_network()` is a tripwire, and it is honest about that

The context manager replaces `socket.socket` and `socket.create_connection` with
a function that raises. It is not a sandbox and the docstring says so.

**Why.** The exam is the *active* instrument — it sets questions and needs a new
run — which makes it the component most likely to reach for the live game. The
realistic failure is not a determined process escaping; it is a helper three
imports down that quietly fetches something. A tripwire catches that. Claiming
more would be worse than claiming less, because a guarantee nobody can honour
stops people from looking.

---

## D-EX-010 — a pre-registered band failed on first contact, and was replaced rather than widened

The band `("heldout", "bluffer") = [0, 0.35]` was written before any paper
existed. The paper as built scored the bluffer at **0.45**, so calibration
failed. The band is now `[0, 0.50]` and the work is done by two new checks.

**This is the exact move pre-registration exists to make difficult, so the
reasoning is recorded in full rather than summarised.**

**What the band assumed.** Its stated reason was "returning the unchanged frame
is right only where nothing moved" — true, and it silently assumed that items
where nothing moves are rare. The held-out paper deliberately over-samples the
guard classes (`blocked_crossing` by 104×, `blocked_landing` by 35×) because
that is where a0-spike's T-9 failure lives, and **every guard's correct answer
is an unchanged frame**. So 45% of items have "nothing moved" as their answer.
The premise was wrong; the paper was not.

**Why widening alone would have been dishonest.** Moving 0.35 to 0.45 because
0.45 is what we observed is curve-fitting the instrument to its first reading,
and it would have to be done again for every future item mix.

**What replaced it.** Two checks that do not depend on item mix at all:

* `bluffer_hits_ceiling` — the paper publishes `unchanged_frame_share`, the
  score obtainable by returning the input frame, and the bluffer must land on it
  **exactly**. A bluffer above its own ceiling means the ceiling is miscomputed;
  below it means the bluffer is doing something else.
* `oracle_minus_bluffer ≥ 0.50` — ground truth must beat the bluffer by half the
  paper. This is what the original band was reaching for, stated as a distance
  rather than as an absolute score.

Both are strictly stronger than the band they replace: the old band admitted any
value under 0.35 including a bluffer that beat a real theory on a paper made
entirely of refusals. The retained `[0, 0.50]` is a backstop, not the
measurement, and the code says so at the definition.

Measured after the change: ceiling 0.45, bluffer 0.45, margin 0.55.

**A remaining hole, stated rather than fixed.** `EXPECTED` is not covered by the
rubric digest (D-EX-003) — that digest hashes `exam/grading/rubrics_*.py`, and
this table lives in `calibration.py`. A future quiet widening here would not
show up as a digest mismatch. The mitigation is only that every band carries its
reason in the same literal, so a widening without a reason is visible to a
reader of the diff. Extending the digest to cover the calibration table would be
the real fix and is not done.

---

## D-EX-011 — the cheater found two real leaks, and the checks that missed them were the bug

The cheater subagents were handed sheets alone and told to extract answers. They
found two leaks that checks 1–3 had passed, and both were confirmed against the
answer key before anything was changed.

**Leak 1 — `points` was a perfect answer key.** The verdict paper weighted the
solvable items 3 against 2, so that a bluffer answering "unsolvable" everywhere
would score badly. `Item.sheet_side()` puts `points` on the sheet. Result: the
class was readable off the point value on **17 of 17 items**, the entire claim
half of the paper, with no reasoning about any board. Measured, not estimated.

The weighting bought nothing it was supposed to. There are 9 unsolvable items
and 8 solvable ones, and half of every item's marks are the reason, which a
bluffer never earns; it scores 9 of 34 with uniform weights and 9 of 42 with the
old ones. Points are now uniform.

**Leak 2 — the held-out sheet published the rule.** `world.description` read
*"sokoban in which a push slides the box two cells"*. That sentence is precisely
what the examinee is being tested on. The cheater went from 47.5% (generic
one-cell-push prior) to essentially full marks on the strength of it. The world
block now names the world and says nothing about how it behaves.

**The deeper fault was in the checker, and it is the one worth recording.**
`answer_labels` was an *optional* hook on each paper module. No module
implemented it. So `check_paper` received `answer_of=None` and checks 3 and 4
**silently did nothing on all four papers**. An optional check is a check that
does not run, and it fails in the direction that looks like success.

Three changes followed:

* `derive_label_sets()` reads answer classes out of the key directly, so the
  check cannot be skipped by a builder not opting in.
* A fourth static check, `metadata_hits()`, asks whether `points`, `tags` or
  `kind` predicts the answer. It is the check that would have caught leak 1.
* It is scored **within one answer alphabet**, ignores buckets of size one, and
  skips classes the sheet already publishes. Each of those three exclusions was
  added in response to a false positive found while wiring it up — a per-variant
  tag fits 6 answers perfectly and predicts nothing; `kind` "predicts" the answer
  whenever two families answer in different vocabularies; the held-out paper
  prints `split` on every item on purpose, having matched the class quotas so
  that it is safe to show. A checker that cries wolf gets switched off, which is
  the same failure as a checker that never runs.

Regression tests pin all of it, including the exact leak that shipped.

**What this says about the four-check design.** It worked, but not the way the
docstring claimed. Checks 1–3 caught nothing here; the cheater caught both. The
honest reading is that the static checks are necessary and cheap, and the
adversarial reader is the one that found the leaks, so it is not optional and
should run on every paper before that paper is used for anything.

---

## D-EX-009 — the run archive digests the answer keys but does not copy them

`exam/tools/archive_run.py` records `key_sha256` for every paper and copies no
truth file.

**Why.** An archive that ships the keys beside the sheets rebuilds, inside the
archive, exactly the leak the rest of this directory exists to prevent — and
archives are the artefacts most likely to be handed around. The digest is enough
for a later reader to prove the keys they hold are the keys that were marked
against, which is the only property the archive actually needs.

The manifest carries no wall clock, for the reason stated in `CLAUDE.md`: a
timestamp makes two identical runs differ, and destroys the cheapest check that
a run was deterministic at all.
