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

---

## D-EX-012 — the marker is tested in the middle of its range, not only at the ends

`exam/grading/selftest.py`. Seven mutants with predicted scores, eight injected
marker faults, and a detection matrix over the two.

**Why.** `calibration.py` pins the marker with `oracle == 1.0` and
`null == 0.0`. Both are exact and both follow from construction, and between
them they say nothing about any submission that is neither ground truth nor
silence — which is every real one. A marker can be exact at both endpoints and
arbitrary in between, and every check that existed before this module would
pass it.

The mutants are chosen so the expected score is arithmetic rather than
judgement: dropping a set of answers costs exactly what those items were
awarded; dropping one answer moves one item's mark; reversing the key's item
order moves none. There is no band anywhere in this module, because a band is
what you write when the expectation depends on item mix, and none of these do.

**The faults exist to test the checks, not the marker.** Injecting
`pays_for_silence` and watching the null band fire proves the band is load
bearing; a check nobody has watched refuse is a check nobody has tested. The
matrix that comes out has the same shape as the leakage table in D-EX-011 and
is read the same way: **the zeros are the finding.**

## D-EX-013 — the calibration bands were one-sided, and `truncates_partial` proved it

First fault-matrix run: eight faults injected, seven caught, and
`truncates_partial` — partial credit silently zeroed — caught by nothing at all.

The reason is structural rather than an oversight in one band. Every band in
`EXPECTED` for the two informative fakes is `Band(0.0, x)`: bounded above, open
below. A marker that *depresses* scores satisfies all of them. `oracle == 1.0`
is the only lower bound in the protocol, and it only ever sees answers that are
already full credit, so it cannot see a partial being crushed.

**Closed with a seventh mutant rather than a lower band.** `partial_credit_
survives` removes one component of a composite answer and requires a paper
whose rubrics award partial credit to produce a score strictly between zero and
full. A lower band would have been a number fitted to what the first run
happened to produce, which is the failure D-EX-010 was written about; this is
structural and survives a change of item mix.

It declares itself **inapplicable** on `heldout` and `handover`, whose answers
have no removable component, rather than reporting a pass there. That is
D-EX-011's lesson applied before it costs anything: an optional check is a
check that does not run, and a check that cannot run has not passed.

## D-EX-014 — an illegible answer is no longer read as the claim `never`

`rubrics_adaptation._read_claim` (was `_read_index`). Found by the `garbage`
mutant on its first run, before this module had ever marked anything real.

**The defect.** The function had two outcomes where it needed three. Everything
it could not parse fell through to "did not claim a detection", and the caller
wrote that down as the substantive answer `never`. On `v-a0-03` — the one
variant that is genuinely undetectable on its base level — `never` **is** the
truth. So a submission containing no answer at all collected that item in full:

| submitted on every item | adaptation score |
|---|---|
| an unparseable string | 1.600 / 144 |
| `""` | 1.600 / 144 |
| `{}` | 1.600 / 144 |
| `null` | 1.600 / 144 |

All 1.6 points sit on the two `v-a0-03.detect` items, and
`v-a0-03.detect.match` paid **1.0 of 1.0**. The item exists to ask whether an
examinee can tell "the change is invisible from here" from "I did not look";
the marker could not tell those apart either. The other three papers pay
exactly 0.000 for the same four submissions, which is why nothing had noticed.

**The fix, and the one asymmetry in it.** Illegibility is a third outcome,
scored `wrong` with `said: "unreadable"`. A **bare** `null` is illegible; a
`null` *under a key the examinee wrote down* — `{"per_level": {"match": null}}`
— is a legible "never", because presence of the key is the claim and a bare
null is what a broken serialiser emits. That distinction is load bearing: it is
the spelling the reference answers use.

**No calibration number moved.** oracle 1.0 / null 0.0 / memoriser 0.1708 /
bluffer 0.1708 before and after, on all four papers, and the suite was green
on both sides. A bugfix that also re-tunes the instrument is two changes
wearing one coat, and this one is not.

## D-EX-015 — the confusion pair is split by class, and coverage is printed beside it

`exam/grading/confusion_matrix.py`, and `artifacts/matrix/verdict_confusion.md`.

**Why split.** Classes (i) and (ii) exist because "I enumerated it" and "I
proved it" are different achievements. Pooled sensitivity destroys that
distinction: it sums all nine unsolvable items regardless of which class they
came from, so an arm that aces the small-space family and cannot touch the
large-space one reports the same 1.000 as an arm that reasons.

**Why coverage.** `mark.confusion` keeps abstentions out of the denominator and
says so, which is the right call — an abstention is not a wrong answer. The
consequence is that the rate alone is uninterpretable: an arm that abstains on
everything it cannot do scores 1.000 on what is left. The matrix therefore
prints `rate (answered / class size)` in every cell.

**The measurement that justifies both.** The memoriser's pooled pair is
sensitivity **1.000** and specificity **1.000** — numerically identical to
ground truth — while it scores 0.5882. Split, it abstains on **4 of 4**
large-space items and has never answered one. The pooled pair cannot tell the
memoriser from the oracle; the split can. That is the argument for the split as
a measurement rather than a preference.

**Empty denominators print `--`, never `0.000`.** Class (i) contains no
solvable items, so specificity there is undefined, not zero. An arm cannot fail
a test it was never given, and a table that writes those cells as zero says it
did.

## D-EX-016 — a second digest, over the marker and the bands, pinned by a test

`selftest.protocol_digest()` over `mark.py`, `calibration.py`, `selftest.py`.

**Why a second one.** `registry.digest()` covers the rubrics and travels onto
every sheet. It deliberately does not cover the bands, and `calibration.py`
said so in a comment above `EXPECTED` — "a quiet widening here would not show
up as a digest mismatch" — which is `STATUS.md` open weakness 3, self-reported
and unfixed. One band has already been widened once (D-EX-010), legitimately
and on the record; nothing existed that would catch an unrecorded one.

**Why not extend the existing digest.** That value is the seal on every sheet.
Extending it would change every sheet and every stored artefact for the sake of
a check that has no reason to travel to an examinee. A separate hash, pinned by
`test_a_widened_band_changes_the_protocol_digest`, gets the property at the
cost of one deliberate test edit — which is the point: widening a band now
requires an edit that a reviewer sees.

## D-EX-017 — the fourth question family is a citation set, and a spurious citation costs what a correct one earns

Theoria.md 1.11 names four things a fresh reader is asked: `step` semantics,
which names are level data, the best action, and **why a rule holds**. P-15 built
the first three. The fourth had no rubric, and the obvious reason is that "why"
is prose and prose cannot be marked mechanically.

It is asked here as a *citation*: a claim about the world, a fixed list of the
manual's clauses, and the instruction to name the subset the claim's truth
depends on. That turns 1.11's 「理由:证书,还是"我搜过了没有"」 into something a
marker can settle, and it keeps the marker a pure function of (answer, truth,
item).

**Scoring, and why it has a subtraction in it.**

    awarded = points * clamp01((|A ∩ T| - |A \ T|) / |T|)

Without the penalty term the dominant strategy is to name every clause on the
list, and a rubric whose optimum is "say more" measures fluency. With it, the
calibration bluffer — which does exactly that — scores zero on every
justification item whose support set is not the whole list, and
`test_citing_everything_is_not_a_strategy` pins it below half the family.

**The criterion had to be published or the family would be an argument.** "Does
the claim depend on this clause" has two readings. Under the loose one, changing
*any* rule could break almost any claim, and the answer to every item is "all of
them". The sheet states the tight one: a clause belongs when the claim's truth
uses **what that clause does** — the `then` half — so `blocked_wall`, whose
effect moves nothing, is not cited for a claim about where the Box ends up. Each
item's key carries a `why` field justifying its own set, in the truth file where
the examinee cannot see it and an auditor can.

**One item is not marked against a stored answer at all.** The A0 manual ships
`invariant box_row_parity (Box.pos.row) mod 2 = 1` marked `proven`, and it is
false on most boards of its own world (STATUS, "A defect in the A0 manual"). The
sheet asks for a situation where it fails and the rubric *recomputes the claim
there*. There is no key to loosen, which makes it the one item on the paper whose
marking cannot drift — and it asks the reader to disagree with a document it was
told to trust, which is the disposition the whole framework is betting on.

---

## D-EX-018 — a tag *token* can be an answer key even when the tag *value* is unique

The first V11 cohort was voided. The optimal-action items carried

    "tags": ["optimal_action", "level:stile", "dead"]

and `Item.sheet_side()` prints `tags`. The word `dead` is the answer to the two
sharpest items on the paper, written next to the question. Six readers were
already reading when it was found, and a spawned subagent cannot be stopped by
the agent that spawned it, so the cohort finished and its answers are kept as
evidence, unmarked, under `exam/runs/20260728T202101Z-V11-handover-auto/`.

**Why `metadata_hits` passed it, and why that was not a bug in the usual sense.**
It buckets on the whole value of `tags`. Every item also carries a unique
`level:` token, so every bucket held exactly one item, and D-EX-011's third
exclusion — ignore buckets of size one, because a per-variant tag fits every
answer and predicts nothing — dismissed them all as identifiers.

That exclusion is correct about *values* and wrong about *tokens*. A tag list is
not an atom; it is a set, and one member of it can be a key while the set as a
whole is an identifier. The leak lived in a token inside a value that was unique
for an unrelated reason.

**What stands there now.** `test_no_single_tag_token_predicts_an_answer` buckets
each token separately, within one answer alphabet, and fails any token that
appears on more than one item, on fewer than all of them, and agrees with the
answer every time. Run against the tags that shipped, it reports exactly one
offender: `('dead', ['none'], 2)`.

**Why it is a test here and not a fix in `leakage.py`.** The same weakness
applies to all four P-15 papers, and changing a shared checker while six
examinees are mid-run is how the *next* cohort gets voided too. The
generalisation is written up in `STATUS.md` as work for whoever owns
`leakage.py` next. It should be done: a token-level check would have caught this
before anyone read anything.

**The part worth keeping.** Three defences were designed against exactly this and
all three held — forbidden substrings in the prompt, the paper's declared probes
run against the prompt, and a wording check on the reader brief. The leak came
through the one channel none of them watched. 泄漏面会跟着证据走: block one and it
moves. The only durable response is to keep publishing the residue, which is what
`BLINDING.md` is for.


## D-EX-019 — the control arm was handed the treatment, and no checker was looking

The V11 handover sheet asked, as `rule_justification` items, which manual clauses
two claims rest on. The claims were:

> "On a board whose target cell has a different column parity from the cell the
> Box starts on, the game can never be won."

> "If the Box stands where no direction admits a push … then the Box will never
> move again, whatever the Player does."

Those are the playbook's two `prune` entries, in English. The playbook is the
**tier-2-only** half of the deliverable, and the item's prompt — "which of the
listed clauses does this claim's truth depend on?" — presupposes the claim is
true, so the tier-1 reader was not asked to evaluate them. It was told they hold.

The adversarial reviewer showed the two printed criteria are jointly a complete
and sound classifier for all eight optimal-action items — dead on exactly the two
dead boards, no false positives — using no manual, no playbook and no search.
`PREREGISTRATION.json` had pre-registered `optimal_action`, and `cairn` inside it,
as the only place a tier difference should appear. The contamination landed
exactly there.

**Why nothing caught it.** Every defence in this territory compares an item with
*itself*: `probe_hits` looks for an item's own answer in the sheet text;
`structural_hits` compares an item's `truth` keys with its own `paper` keys;
`metadata_hits` asks whether an item's `points`/`tags`/`kind` predicts its own
answer. Nothing compares one item's **prose** with the content of the other
tier's bundle, and nothing ever had reason to, because before V11 no paper was
split into arms that receive different documents.

**What was added.** `handover_auto.cross_item_leak_report` scores each item's
claim text against each playbook entry by **containment of the entry** —
`|claim ∩ entry| / |entry|` — with the DSL's scaffolding words dropped and `_`
treated as a word break. Every one of those three choices was forced:

* Jaccard divides by the union, so a six-word entry restated inside a thirty-word
  claim scores 0.2. The first version used Jaccard and reported the sheet clean.
  **A check that reports clean is not evidence of clean.**
* `no_direction_admits_a_push(Box.pos)` is one identifier and "no direction
  admits a push" is five words; without splitting on `_` a sentence has no
  overlap with its own restatement.
* Without dropping `prune`/`proof`/`lean`/`pos`, every entry matches every claim
  a little and the threshold has to rise until it catches nothing.

At 0.65 it flags exactly `v11-why-02` (0.75) and `v11-why-05` (0.80) and nothing
else. Both are pinned in `test_no_new_sheet_claim_restates_a_playbook_entry` so
that a *third* fails the suite instead of being found by a reviewer afterwards.

**Why the offending items were not deleted.** Six readers answered that sheet.
Editing it now would leave a run whose sheet digest, prompts, answers and results
describe a paper that never existed — the same reason P-15 left its saturated
`name_class` items alone. They come off the next sheet.

**The generalisation worth carrying.** A two-arm exam has a failure mode a
single-arm exam does not: the treatment leaking into the control. It is not a
leak *of the answer key* and no answer-key checker will find it. Any paper that
gives different arms different documents needs a check that the arms actually
differ in what they were given — and that check has to run on the rendered text
each arm receives, not on the metadata around it.

---

## D-EX-020 — there is one transition function, and the certificate graph asks it

`rubrics_verdict._neighbours` now calls `Level.step` instead of reimplementing
it, and `relaxed_edges` builds its node set by closure from the passable cells
rather than by filtering successors.

**What was wrong.** The module docstring said the graph "can never make a
solvable level look unsolvable, which would hand out points for a false
theorem." It could, because the graph was a *second* implementation of the
transition function and the two disagreed in three places:

| disagreement | `Level.step` | the old `_neighbours` |
|---|---|---|
| `portal_dest` is `None` | `portal_dest or target` → the cart rests on the portal cell and walks on | dropped the edge |
| `portal_dest` is a wall | parks the cart in the wall, lets it walk out | dropped the edge (`passable(dest)` is False) |
| a cell that is both door and portal | tests the door **first**, so the portal never fires | tested the portal; had no door branch at all |

In each, `step` moved the cart and the graph did not. An over-approximating
graph that fails *closed* is an under-approximation, and `cart_region` and
`cut_set` certificates for **solvable** levels were accepted and paid in full —
2.0 of 2.0, `reason: certificate`, on a level winnable in three commands. The
first two need only `portal` set and `portal_dest` forgotten, and `_level()` in
the paper builder defaults `portal_dest` to `None`, so that is inside the level
shape rather than outside it. The third needs no malformed field at all.

None of it was reachable through any *shipped* item — a differential fuzz over
41,868 solvable well-formed levels found zero unsound accepts — which is exactly
why nothing had noticed. The reproductions are in
`runs/20260729T020000Z-V5-verdict-three-types/verify_checker_claims.py` and are
pinned as regression tests.

**Why delegation rather than three patches.** Three patches would have fixed
three disagreements between two implementations that will keep producing them.
The teleport rule is stated once now, in `step`, and `_neighbours` inherits it.
The only relaxation left is `pressed=True` — the door treated as already open —
which is the intended one and can only add edges.

**A second line, for Phase 4.** `Level.wellformed_problems()` names the field
combinations that made the disagreement reachable, and `_self_check` refuses to
ship a level that has one. It is not called from the marker: a rubric must mark
whatever it is handed, and refusing a malformed level would turn a builder's
mistake into an examinee's zero. It matters when a level is transcribed from a
sealed game rather than written here.

**And one fix the fix required.** `passable()` now excludes the **button** as
well as the portal, for the same reason: `step` never returns it, because
stepping into B latches the button and leaves the cart where it was. Admitting
it cost nothing while `_neighbours` was separate and yielded it. Once
`_neighbours` asked `step`, the button became a node with no edges — its own
singleton component — and since a component is named by its lexicographically
smallest cell, the atrium's start representative moved from `[1,1]` to `[1,3]`
and the shipped `a2var-i1` certificate was refused. The separation was never in
doubt; the *name* changed. Excluding the button makes the node set mean "cells
the cart can rest on", which is what both certificate kinds always assumed.

**`_check_cut_set` had a vacuous acceptance too.** It read "the goal is not a
node of the graph" as success. Any declared hazard then bought a full-marks cut
set that cut nothing, and that is how the door/portal reproduction was paid. The
goal must now be a node of the *uncut* graph, and must not itself be one of the
cut cells.

---

## D-EX-021 — the 2^m bound checked each dip and never checked the walk between them

`subset_lower_bound` now refuses unless the m dip sources lie on one contiguous
row or column that is switch-free and hazard-free.

**Why.** The bound's argument is "dip into any subset of m switches and come
back, so there are at least 2^m reachable states". It verified that each switch
is individually dippable out-and-back and never verified that the cart can
*travel between* two dips without latching something the subset did not choose.
Where it cannot, the reachable masks are the m prefixes — m+1 of them, not 2^m.

Two falsifiers, and the second is the one that matters:

* a corridor whose own cells are latching switches: `m = 60`, claimed 2^60,
  **1,830** reachable states;
* `comb_open(30)` — a shipped constructor — under `observation_loss` on the
  corridor — a shipped operator: `m = 60`, claimed 2^60 = 1.15e18, **29,791**
  reachable states, and `_large_space` stamped `exhaustive_feasible: False` on
  it. `build()` would have shipped it as a class (ii) item. Overstatement factor
  3.9e13.

`STATUS.md` open weakness 6 said the bound "assumes comb-shaped geometry … and
is applied only to the levels it fits". That was too kind: nothing checked, and
on a non-comb board with switches it returned a large wrong number silently.
17.5% of random boards with arbitrary switch placement produced `2^m` above the
true state count.

The shipped items all satisfy the precondition — every dip source is on row 2,
the corridor — so no number in the paper moved.

---

## D-EX-022 — "enumeration is out of reach" was false, and the rubric was repeating it back

Class (ii) publishes `lower_bound` (2^60 to 2^120) and now also
`positional_states`, and `search_credible` is derived from the second.

**The defect.** `lower_bound` is a true statement about the raw
`(cart, button, latch mask)` product space, which is what a naive forward
enumerator walks. It is not a statement about what a *complete search* costs. On
these boards latching is monotone and gates no geometry, so every non-full mask
at a position behaves alike and the space that decides the question is the
`(cart, button)` quotient. Measured:

| item | claimed `lower_bound` | reachable `(cart, button)` |
|---|---|---|
| `a2var-ii1-gantry-sealed` | 2^120 | **180** |
| `a2var-ii2-lattice-bridge` | 2^120 | **180** |
| `a2var-ii3-spindle-budget` | 2^60 | **600** |
| `a2var-ii4-orchard-noleft` | 2^118 | **177** |

The rubric read `search_credible: False` off the first number and told an
examinee that had honestly searched the second:

> the state space of this level is beyond enumeration, so 'I searched it all' is
> not a reason, it is a false statement about the search.

That sentence was the false statement. A marker that calls a true claim false is
the failure this territory exists to prevent, and it was doing it on the four
items where the examinee had done the *better* thing.

**What changed and what did not.** `search_credible` is now
`positional_states <= SEARCH_FEASIBLE_STATES`, so a quotient search is paid its
0.4. The `search_not_credible` branch survives and still fires where the
quotient really is out of reach — a test pins that. The incentive class (ii)
exists to create is untouched: a certificate is worth 1.0 of the reason and a
search 0.4, on every class, and that ordering is what the replacement test
asserts.

**What this costs the paper, stated rather than hidden.** Class (ii)'s premise
as written — "enumeration is out of reach, so only invariant reasoning answers"
— is false of these boards. What survives is weaker and still worth having: a
*naive* enumerator cannot finish, and a proof is worth two and a half times a
search. Making the premise true again means switches that gate geometry, which
is a different world family and a different paper. It is `STATUS.md`'s open
weakness, not a thing this run repaired.

---

## D-EX-023 — the key says whether its own answer came from a search or a construction

`truth["witness_source"]` is `"search"` or `"construction"`, and `_self_check`
refuses a solvable item that does not say.

**Why.** The paper's premise is 由构造即知答案. `README.md` said class (iii)
items each carry "a computed witness plan" and the module said "computed and
replayed, not asserted". Neither word separates a breadth-first search from a
construction, and **five of the eight** solvable witnesses come from
`enumerate_states`, which is a BFS. That is not a defect — a plan that replays
and wins proves solvability however it was found — but leaving it unsaid on a
paper about constructive grounds is. The three large-board witnesses come from
`waypoint_plan`, which builds a sweep from the board's shape; a test pins that
the constructed ones are exactly the items where a search was not available.

---

## D-EX-024 — the class split cannot report a pair, because the class *is* the answer

`per_class_confusion` now also splits on `board_size_class`, `axes()` publishes
it, and `calibration` asserts the bluffer's signature per stratum.

**The observation.** The three classes partition the paper by answer:

```
small_unsolvable 5 unsolvable / 0 solvable
large_unsolvable 4 unsolvable / 0 solvable
solvable_hard    0 unsolvable / 8 solvable
```

So one denominator is empty in **every** class cell, and the pair the protocol
asks for appears nowhere except pooled — which is the reading D-EX-015 shows
cannot separate ground truth from a reader who never saw a board. The renderer's
footer already stated the fact; nobody had drawn the consequence.

**The fix was already in the truth file.** `board_size_class` cross-cuts the
answer — small 5/5, large 4/3 — and splits on precisely the distinction classes
(i) and (ii) were invented to draw: whether exhaustive search was available. So
both rates are defined in both strata. Measured, the difference is not cosmetic:

| examinee | class split | board-size split |
|---|---|---|
| `bluffer` | `(1.0, --)`, `(1.0, --)`, `(--, 0.0)` | `(1.0, 0.0)` and `(1.0, 0.0)` |
| `memoriser` | `(--, --)`, `(1.0, --)`, `(--, 1.0)` | `small (1.0, 1.0)`, `large (--, --)` at 0/4 and 0/3 |

敢说不可解的框架必须在可解题上闭嘴 is the pair `(1.0, 0.0)`. Under the class
split a reader has to join one row's sensitivity to another row's specificity,
across item sets that do not overlap — which is the join the pooled rate makes.
Under the board-size split it is one cell, twice. And the memoriser's emptiness
becomes one cell saying it has never answered a large board in either direction,
instead of two cells each printing `1.000`.

`calibration`'s `verdict_bluffer_pair` asserted `(1.0, 0.0)` on the pooled pair
only, which is the weakest available place to assert it. It now asserts it in
each stratum, which is strictly stronger and independent of item mix.

---

## D-EX-025 — an unreadable answer was being reported as an abstention

`mark.confusion` and `per_class_confusion` both branched on
`score.verdict == "abstained" or said in (None, "abstain", "unknown")`.
`grade_verdict` returns verdict `wrong` with `said = None` for an answer it
cannot parse, and `unanswered` items have no `said` at all. So three different
things — *did not submit*, *declined*, *submitted something unreadable* — were
one column, and it was the column D-EX-006 introduced **so that an abstention
could not be confused with anything else**.

Consequences, measured: an examinee submitting `{"verdict": ...}` (no `claim`
key) on four items printed the identical row and identical score to one that
honestly abstained on those four; an examinee whose every answer was unreadable
printed the identical row to `null`, which submitted nothing.

Three counters now, and `n_positive` sums over all of them so coverage still
adds up. The change immediately falsified a claim in an existing test: the
memoriser's docstring said it "abstains on all four large-space items", and it
does not — `reference_answers` skips them, so they are `unanswered`. The old
counter could not tell, and neither could the docstring.

---

## D-EX-026 — the fakes calibrate the paths the fakes walk, and that is two of eleven

`calibration._type_specific` now runs five **answer-shape probes** against the
verdict paper, each with a score fixed by arithmetic over the paper's own points.

**The measurement that forced it.** An adversarial audit injected fourteen
faults into the verdict rubric. **Thirteen passed `assert_calibrated`** — the
gate that "refuses to mark a real submission" — and twelve passed all seven
mutants of D-EX-012. Two were caught by nothing at all: not the gate, not the
mutants, not 73 tests. All four calibration fractions stayed bit-identical under
every one of the fourteen.

The mechanism is not subtle once stated. The sheet's `INSTRUCTIONS` advertise
**five** answer shapes; the four fakes submit **three**. Nobody ever submits
`{"claim": ..., "reason": "exhaustive_search"}` or `{"claim": "abstain"}`, and
the seven mutants are all derived from the *oracle's* answers, so they inherit
the same three shapes. Coverage says the same thing more starkly: of the eleven
terminal outcomes of `grade_verdict`, the oracle reaches **two**, all four fakes
together reach four, and fakes-plus-mutants reach six. Of `check_certificate`'s
twenty-nine outcomes, **every semantic refusal in all three kind-specific
checkers** is reached by no fake and no mutant — on a module whose thesis is
"the machine actually refuses things". And the `null` fake executes **zero**
statements of the verdict rubric; it tests `mark.unanswered`.

**The five probes**, and what each closes:

| probe | expected | closes |
|---|---|---|
| `abstainer` | exactly 0, all 17 `abstained` | abstain read as a claim (worth 9/34) |
| `illegible` | exactly 0, all 17 `wrong` | a broken serialiser looking like restraint |
| `searcher` | 0.5 + 0.5·0.4 per credible item | search paid in full, or not at all |
| `wrong_claim_with_reason` | exactly 0, all 17 `wrong` | the reason half paid on a wrong claim |
| `forged_certificate` | exactly half the paper | certificate values believed instead of re-derived |

**The first draft of this check did not work, and the reason is the point.**
`_verdict_probe_expectation` imported `SEARCH_CREDIT` from `rubrics_verdict`, so
injecting `SEARCH_CREDIT = 1.0` moved the marker and the expectation together
and the gate stayed green. **A check that reads its expectation out of the code
it is checking is not a check.** The three weights are now pre-registered in
`calibration.VERDICT_WEIGHTS` and the live constants are asserted against them —
same argument D-EX-016 makes for the protocol digest.

**A side effect worth recording.** The probes are exact equalities, not upper
bounds, so they catch a marker that *depresses* scores. That closes D-EX-013's
standing finding — every band for the informative fakes is `Band(0.0, x)`, open
below — **for the verdict paper**, without adding a lower band fitted to a first
reading. `heldout`, `handover` and `adaptation` still have no probes and
D-EX-013 stands there unchanged; a test asserts exactly that, so the day someone
adds probes elsewhere the claim gets re-examined rather than quietly inherited.

---

## D-EX-027 — the adversarial review of D-EX-020…026, and the two things it broke

An adversarial reviewer was pointed at this run's own changes and told to refute
them. It refuted three of seven claims. Two were defects **this run introduced**,
and one was a decision this run got wrong and has withdrawn. All reproductions
are in `runs/20260729T020000Z-V5-verdict-three-types/verify_review_claims.py`,
re-derived here before anything was changed.

### 1 — excluding the button from `passable` created a new unsoundness

D-EX-020 excluded the button because `step` never returns it, which is right for
the movement graph. `row_col_deltas` was also using `passable`, to ask a
different question: not *where can the cart rest* but **where can the cart be
standing when it issues a command**. The cart can *start* on the button.

On a board where the cart starts on the button and the button is the teleport's
only entry, the jump's row displacement was dropped from the closure, `cart_row`
came out monotone, and a level solvable in **one command** was paid **2.0 of
2.0** for a certificate asserting it unsolvable — the exact failure D-EX-020
claims to have eliminated, reintroduced by D-EX-020's own fix, and through a
function D-EX-020 never touched. The pre-change `passable` refused it.

`Level.can_stand` is now the predicate for that question and is deliberately
generous: extra entry cells only add displacements, and more displacements make
monotonicity harder to prove, so erring wide refuses certificates rather than
accepting false ones. `wellformed_problems` also refuses `button == start` and
`portal_dest == button`, so the shape cannot reach a sheet.

**The lesson is about the fix, not the bug.** D-EX-020's argument was "there is
one transition function now, so the two cannot disagree again". True, and
insufficient: the disagreement moved into a *predicate* with two callers asking
two different questions of it. A shared helper whose name answers one question
and whose callers ask two is the same defect wearing a smaller coat.

### 2 — D-EX-022 is withdrawn: the quotient is not a sound abstraction

D-EX-022 derived `search_credible` from `positional_states`, the `(cart, button)`
quotient, on the argument that latching is monotone and gates no geometry so the
quotient decides the question. **The argument is false**, in two independent
ways, both reachable with a shipped constructor and a shipped operator:

* `positional_states` **does not read `step_limit`**. `comb_open(6)` under a
  budget of 12 has 18 quotient states and the goal is reachable in the quotient;
  the level is unsolvable. `a2var-ii3-spindle-budget` is exactly this shape, and
  its recorded 600 is not even the number of positions reachable inside its
  budget.
* the quotient **carries no latch state**, and on a `require_all_switches` board
  reaching the goal is not winning. `comb_room(5)` with an `observation_loss` on
  one switch cell has 25 quotient states, the quotient says the goal is
  reachable, and the level is unsolvable.

So D-EX-022 replaced *a true statement being called false* with **a false
statement being called true** — and the second one pays 0.4 of the reason. It
also made `search_credible` `True` on 17 of 17 items, so the field discriminated
nothing and `search_not_credible` was dead code.

`search_credible` is `state_space["exhaustive_feasible"]` again, which is what it
always was. `positional_states` stays, as a measurement, with the truth file
saying in the same breath that it is not a search space — because the inference
this run made is the one the next reader will make too.

**What survives of D-EX-022**: nothing about `search_credible`. The ordering it
also asserted — a certificate always beats a search, on every class — was worth
keeping and is now asserted alongside the restored original.

**And the check that should have caught it could not.** The `searcher` probe's
expectation reads `truth["search_credible"]` from the same key the marker reads
it from, so flipping the field moves both and the gate stays green. That is the
self-reference D-EX-026's own `VERDICT_WEIGHTS` comment was written about,
surviving one field to the left. Not fixed: recomputing credibility
independently means running an enumeration per item inside calibration, which
runs in every test. Recorded as `STATUS.md` open weakness 28.

### 3 — a claim outside the answer alphabet was scored as a *negative*

Both confusion functions treated "anything that is not the positive label" as
the negative label. `{"claim": "I do not know"}` on all 17 items therefore scored
**specificity 1.000** — better than the bluffer's 0.000 — for having classified
nothing, on a submission worth 0.0000. `_ABSTAIN` is a five-word closed set and
does not contain the most natural English phrasing of an abstention, so this is
not an exotic input. The alphabet is now read off the key and anything outside it
is unclassified.

### 4 — D-EX-025's fix landed in one of the two places that needed it

The three-way split went into `confusion_matrix.tally` and not into
`mark.confusion` — which is what `axes()` publishes, what the renderer prints
first, and what the calibration gate reads. `null` and an all-unreadable
submission still printed identical pooled rows. Fixed, and pinned by a test that
compares the two pooled rows directly.

### 5 — the `forged_certificate` probe was vacuous on half the paper

On a *solvable* item `_score_unsolvable_reason` is never called, so the reason
half was refused for lack of a witness rather than because any arithmetic was
re-derived: the probe scored exactly right on 8 of 17 items whatever the checker
did. The reviewer demonstrated it by making `check_certificate` a rubber stamp
and watching the award move by 9 rather than 17. The probe now sends a losing
witness as well, so both halves of the reason channel are exercised on every
item. A probe that passes for the wrong reason on half the paper is half a probe.

### What the review did not break

`relaxed_edges` as an over-approximation survived 8,210 fuzzed solvable levels
across nine adversarial shapes with zero unsound acceptances, and the node-set
closure adds no nodes and costs under 1.5 ms on every shipped level. All nine
shipped certificates verify, each for its stated reason. The board-size split's
arithmetic, its absence from the sheet and the absence of an import cycle all
hold. The three-way disjointness and the denominator sums inside
`per_class_confusion` hold across 48 cells. The pre-registered weight
cross-check holds. Determinism and byte-identical artefact regeneration hold.

---

## D-EX-028 — what earns the class (ii) label, and what class (ii) may claim

V6-V23. Theoria.md:259 calls class (ii) — "large space unsolvable, only
invariant reasoning can answer" — our home ground, and until this run it was the
one class never actually tested. Measurements in
`runs/20260730T021500Z-V23-large-space/`.

### The criterion: a constructive bound AND a measured enumerator failure

Four criteria were available and the choice between them is the decision.

*Rejected: a reachable-state count over a threshold.* `LARGE_SPACE_THRESHOLD =
10**12` (verdict.py:88) had no entry in this file — a number that arrived
without an argument — and it was being applied to a count the class (ii) path
never took. A threshold over an asserted quantity is a tautology wearing a gate's
clothes.

*Rejected: measured failure of real complete solvers at declared budgets.* The
obvious objection is engine-rig's D-024, "a proof and a shrug must not share a
return value" (engine-rig/DECISIONS.md:779-781) — a timeout is not a verdict.
But this criterion fails before that objection is reached. On these boards the
strong solvers do not time out; **they win in milliseconds**, because the
switches are monotone and gate no geometry, which is exactly the structure
standard techniques eliminate for free. Adopting it would not be inadmissible,
it would be false.

*Adopted, conjunctively:*

1. **A search-free constructive lower bound.** `subset_lower_bound` exhibits 2^m
   distinct reachable states by construction. It is a proof, not a resource
   observation, so D-024 does not reach it.
2. **The reference enumerator, measured to truncate.** Circular as evidence
   about the level — we chose the enumerator — but not circular as the
   complement of the claim class (i) already makes, since `_small_space` defines
   `naive_enumeration_feasible: True` by exactly this enumerator terminating
   under exactly this cap. Its only admissible use is that parity, and it must
   be run.
   It previously was not merely unmeasured but counterfactually recorded:
   `_large_space` hardcoded `"truncated": False`, true only because no
   enumeration was ever attempted, and reading as though one had run and come
   back clean.

### `exhaustive_feasible: False` is withdrawn

The field asserted that no exhaustive method is feasible on the board. Every
shipped class (ii) item is settled by an exhaustive computation over at most 600
nodes, against bounds of 1.15e18 to 1.33e36
(`crux_quotient_settles.json`): ii1 by components of `relaxed_edges` on 300
nodes; ii2 by the same pass with the cut cell deleted; ii3 by a relaxed distance
of 199 against a budget of 150; ii4 by observing the surviving column deltas are
{0, 0, +1}. The four mechanisms differ — an earlier draft of the probe assumed
one components pass settled all four and the measurement refuted that for three
of them.

D-EX-022's disclaimer, that the quotient can report the goal reachable when the
level is unsolvable, is correct and is **one-sided in the direction that matters
here**: an over-approximation produces false *solvable*, never false
*unsolvable*, so "different components" is a sound unsolvability proof. D-EX-022
read the one-sidedness as grounds to distrust the number. For the refutation
direction it was the alarm bell that the barrier is apparent rather than real.

What survives is narrower and checkable: **`naive_enumeration_feasible: False`**
— forward enumeration over the full (cart, button, latch mask) state, the method
class (i) is graded on, cannot terminate here. So class (ii) does not measure
"only invariant reasoning can answer this"; it measures **method selection under
an apparent search barrier**. That is weaker than the design document's claim and
it is the one the artefacts support. It is also the more useful one: it is
falsifiable by a single counterexample examinee, whereas a universal over all
methods is not establishable by any experiment.

This **supersedes D-EX-027's closing line on the field name** — "`search_credible`
is `state_space["exhaustive_feasible"]` again, which is what it always was", in
D-EX-027 above — in the name and not in the substance: credibility is still not
derived from the quotient, but the field `verdict.py:720` reads is now
`state_space["naive_enumeration_feasible"]`, and `exhaustive_feasible` exists
nowhere in the code.

### A bound must defend its own premise where it is claimed

Every guard on class (ii) truth fired *after* the record was written.
`Level.wellformed_problems()` is reached only from `_self_check` at
verdict.py:1278, while the seven `_large_space` calls sit at 1010, 1030, 1055,
1081, 1212, 1241 and 1267. Measured: a `comb_open` whose switch list repeats one
cell 60 times produced 2^60 = 1.15e18 on a board with **359** reachable states,
an overstatement of 3.2e15, and neither the lane premise nor the threshold
objected. `build()` did abort before returning a paper, so nothing false
shipped — but the exposure was real for every direct caller, and a bound that
survives only because a distant caller happens to check is not a bound.

`subset_lower_bound` now refuses it itself. The check is gated on
`candidates[:m]`, not on `level.switches`: a repeated entry naming a wall never
becomes a dip candidate and the arithmetic over the real alcoves stays sound, so
the coarser guard would be a false refusal. Both directions are pinned —
`test_the_bound_itself_refuses_a_duplicated_switch` and
`test_a_duplicate_outside_the_bounded_prefix_still_yields_a_bound` — and both
were mutation-tested red, the second against the coarse guard specifically.

The pre-existing `test_a_duplicated_switch_is_refused_by_the_builder` is left
standing but it is not the guard: it names this consequence in its own docstring
and then asserts only that a `Level` accessor returns a string.

### Not closed: the sealed drill's class (ii) gap is structural

`GridWorld.reachable(limit=200_000)` (worldgen/core/world.py:259) **raises**
above the limit, so worldgen cannot build a world whose state space exhaustive
search cannot reach — the catalogue does not merely happen to lack one.
`DRILL.json`'s `classes_absent: ["large_unsolvable"]` therefore cannot be closed
from inside `exam`. Not done here; it needs a worldgen change. **Not on the
board either** -- "filed" was written before any ticket existed, which is this
ticket's own defect class at one more remove; cross-territory supply is the
monitor's per `CHARTER.md`, so it is requested in `monitor/inbox/20260730T071500Z-RES-3-two-findings-that-say-filed-but-are-not-on-the-board.md`.

### The measurement that licenses the extrapolation

The bound is arithmetic and no class (ii) board has ever had its states counted;
the affordable ceiling on this hardware is ~5e6 states against ii1's 1.33e36,
with memory binding harder than time (~473 B/state, so 10^12 alone wants ~473
TB) and the enumerator's own cost curve running at N^1.49 rather than N because
it copies a command path per state. Raising `MAX_ENUMERATION` is not a lever:
there is no cap between 200,000 and 10^12 at which class (ii) becomes
enumerable.

What is affordable is the same families at small k. Enumerated to completion,
nothing fitted: gantry, lattice and the unbudgeted spindle give
`measured = 2k*4^k = 2k*2^m` exactly at every k with m = 2k; orchard gives
`(2*4^k - 8)/3 = (8/3)(2^m - 1)` with **m = 2(k-1)**, since with LEFT forbidden
the two column-1 alcoves sit behind the start and are not dippable -- which is
why shipped ii4 reports m=118 rather than 120. So the bound is sound at every
rung measured and loose by 2k (growing) or 8/3 (constant), and the exponent is
verified over 5.77 orders of magnitude.

The ladder stops at k=6 for a reason that is not cost: gantry at k=7 is 229,376
states, past the shipped cap, so 6 is the largest rung that can be enumerated to
completion under `MAX_ENUMERATION` at all. (k=1..9 costs ~128 s, not the 2.3 s
this run's own first notes recorded; k<=6 costs ~3 s.)

This licenses the *exponent*, not the shipped number, and it does **not** cover
ii3, whose m=60 comes from `step_limit=150` rather than from its 400 switches.
No closed form for a budgeted board is established.

### Scope: seven records, not four

`_large_space` is called by **seven** items -- ii1..ii4 and the three
`solvable_hard` items -- so the unmeasured record was on all seven and a check
scoped to `large_unsolvable` would have left three behind. Measured: all seven
truncate at the cap, none finds a solution inside it, ~5 s for the set.
`test_class_ii_levels_actually_truncate_the_enumerator` is therefore scoped by
the record (`naive_enumeration_feasible is False`) and not by the class, and it
asserts `solution is None` as well as `truncated` -- a `solvable_hard` item
whose plan turned up inside the cap would mean the naive method works there,
which is the opposite of what its record claims.

### No engine can walk the invariant path

The ticket asked whether `lp_potential` can certify these instances. It cannot,
for two independent reasons, and the second is the one that matters.

The expected obstacle holds: `solve` needs a materialised edge list (~6e36
entries at corridor 60), so the input cannot be built and `solve` is never
entered. But `lp_potential` is a peg-solitaire engine whose move algebra is
`row[dst]+=1; row[src]-=1; row[over]-=1` -- **every expressible transition has
coefficient sum -1**, verified exhaustively over all role assignments at
n_pos=5, while an A2 cart move has sum 0, or +1 when it latches. No assignment
expresses an A2 transition at any size, so no amount of memory would help.

There is no A2->`lp_potential` adapter in the repo, and the one a reader would
naturally write **fails silently**: encoding a comb level and running it anyway
returns `certified` at every size, including at corridor 4 where the level is
*solvable*. All four of the engine's self-checks agree, because all four read
the same wrong move list. Recorded here because a silent unsoundness in the
direction of "proved unsolvable" is the single worst failure this exam can have,
and the next reader to reach for that engine will not find this out by running
it.

Surveying the rest: `ic3_pdr` enumerates up front by its own docstring;
`fd_adapter` and `probe_frontier` need grounded PDDL and no A2/worldgen->PDDL
compiler exists anywhere in the repo; `zero_space` re-checks only against the
sample it was handed; `cegis_miner` and `mdl_segmenter` mine candidates, never
verdicts. **No shipped engine can find a certificate for a class (ii) level at
shipped size.** What does walk the path is `rubrics_verdict.check_certificate`,
purpose-built for this world, single-digit milliseconds per item ("<=3.1 ms" was
withdrawn as one observation restated as a bound, then reinstated as a bound over
the four committed rows of `probe_answer_key.json`; see D-EX-029 as superseded on
that point by D-EX-030), with zero connection to
`engine-rig` -- so "engines propose, the LLM adjudicates" has no engine on this
path today. Not fixed: it is an engine-rig change, and requested in
`monitor/inbox/20260730T071500Z-RES-3-two-findings-that-say-filed-but-are-not-on-the-board.md` rather than
asserted as filed.

### Two adjacent findings, recorded not fixed

* **The quotient can exceed the true count.** Class (i) item i4 enumerates to 31
  states but reports `positional_states` 55, because `positional_states` ignores
  `step_limit` while `enumerate_states` honours it. That is a live shipped
  instance of exactly the unsoundness `quotient_note` warns about, now with a
  number on it.
* **The calibration gate cannot catch a wrong `search_credible`.**
  `rubrics_verdict.py:869` marks on `truth.get("search_credible")` and
  `calibration.py:318` gates on the same key, so a wrong derivation at
  verdict.py:720 would be graded and calibrated consistently wrong. Already
  noted at `exam/STATUS.md:597-598`; repeated here because the rename passes
  through that line.

## D-EX-029 — the premise was checked in two directions out of three, and the document rejected the criterion it ships

V6-V23, second and third rounds, after three adversarial reviewers on D-EX-028.
Measurements in the same run directory,
`runs/20260730T021500Z-V23-large-space/`.

This entry exists because it was cited before it was written. `verdict.py`,
`test_verdict.py`, `CRITERION.md` and `RUN_STATE.md` referred to "D-EX-029" in ten
places while no such entry existed — a citation pointing at nothing, which is the
same defect class this ticket has now produced three times. Caught by asking the
mechanical question of a citation rather than a number: *can I open what this
points at?*

### The bound's premise held in two directions and nobody checked the third

`subset_lower_bound` costs the walk at `dist(c_m) + 2m`. That is the true cost
only when the start lies **outside** the span of the dip sources. Every shipped
item has `start_col=1`, a corridor end, so it was true of everything ever tried
and was assumed of all boards.

With an *interior* start the m nearest sources straddle it: no single walk to c_m
touches the ones behind it, and the real cost is a there-and-back sweep. Built
from one shipped constructor and two shipped operators — `comb_open` with hazards
on both switch rows and an interior `start_col` — a board on which
`wellformed_problems()` is empty, both existing guards pass, `subset_lower_bound`
returns m=40 and `lower_bound` 2^40 over the threshold, `_large_space` **accepts
it and writes the class (ii) record**, the enumerator truncates so that half
passes too — and the walk the published `arithmetic` describes costs 137 commands
against a budget of 99, so it does not exist.

Measured at three sizes: 758 of a claimed 2^10 latch masks actually reachable,
28,188 of 2^15, and 32 of 32 only where the start sits at a corridor end.

**The number survived every attack; the justification did not.** 2^m remains a
true lower bound on total reachable states — it is loose by roughly 2k, and that
slack absorbs the whole over-count — so every check whose predicate was
`lower_bound <= measured_states` returned clean: 347 rows across this run's two
adversarial probes, plus a reviewer's independent 1,034 rungs. What shipped false
was the *reason printed beside the number*, on the class that is graded on its
reason. **A check on the bound cannot see that**, and this is the general lesson:
an adversarial probe inherits whatever gap sits between its predicate and the
claim it defends, so "the attack found nothing" is only as strong as its
predicate — which is therefore a thing to state and audit, not to assume.

Fixed at the selection rather than by refusing: m is now the largest prefix whose
**sweep cost** fits the budget (`_sweep_cost` — reach the nearer end of the span,
sweep to the far end, 2 per dip). Verified both directions:

* the falsified boards now claim exactly what they realise (32/32, 256/256,
  2048/2048), and the straddle board drops to m=29, under threshold, refused;
* **all seven shipped records are unchanged** — m = 60, 118, 120, 120, 120, 120,
  120, every bound identical to the byte, because `min(ends) + span` collapses to
  `dist(c_m)` exactly when the start is outside the span.

The published `arithmetic` now names the sweep and prints its measured value
(spindle: 149 commands against its budget of 150) instead of the `dist + 2m`
shorthand that was the false clause.

### The refusal message was true only by a coincidence of two constants

`enumeration_refused_because` asserts the bound is "past the cap", and nothing
checked it. It held because `MAX_ENUMERATION` (200,000) happens to sit below
`LARGE_SPACE_THRESHOLD` (10^12). Raise the cap above the threshold and the record
still published "past the cap of ...", a false sentence about the arithmetic
printed beside it. `_large_space` now asserts the ordering. Mutation-tested:
disabling the assertion DID NOT RAISE.

*That sentence is wrong about the mechanism, and the code is the right half: the
gate asserts a property of each bound (`lower_bound <= MAX_ENUMERATION` raises),
not the ordering of the two constants. Superseded by D-EX-030.*

### D-EX-028 rejected a bare threshold and then shipped one as its only gate

This is the substantive amendment. D-EX-028 rejects "a reachable-state count over
a threshold" as a standalone criterion **on the grounds that the constant arrived
without an argument** — while in code that same constant, applied to a computed
bound, *is* the whole of what `_large_space` gates on. The document was rejecting
the criterion it ships.

Resolved by supplying the missing argument rather than by softening the
rejection, because the rejection was right and the gate is necessary:

* the requirement is only `> MAX_ENUMERATION`. Past the cap the naive enumerator
  provably cannot terminate, and that is the entire claim the class makes;
* 10^12 is that with about seven orders of headroom, so raising the cap by any
  plausible factor cannot silently reclassify an item;
* every shipped class (ii) item clears it by 6 to 24 orders (smallest bound
  2^60 = 1.15e18);
* the upper endpoint is exact: `2^60` keeps every label, `2^60 + 1` flips ii3.

It is a floor with margin, not a measurement or a tuned number. What makes the
criterion non-tautological is not the threshold at all: it is the conjunction with
the constructive bound, whose count is exhibited rather than asserted.

**A claim this entry made and then had to withdraw.** It first asserted that "any
threshold in `(256, 1.15e18]` labels the same seven records and refuses both
negative controls", offered as robustness "across ~16 orders". An adversarial
reviewer ran it. Both controls are refused at **every** `T` tested, down to
`T = 2`, because the refusal migrates to the second gate above; `256` is control
2's own bound and is the endpoint you get if the first gate is the only one, i.e.
the derivation predates the gate this same entry adds. The audit set therefore
cannot distinguish `10^12` from `2` and does not constrain the threshold from
below at all. The claimed robustness was a property of the audit set presented as
a property of the constant — which is a tautology dressed as a gate, the exact
ground on which D-EX-028 rejected criterion (a). **The threshold's defence is the
argument above, not a sweep.**

### What a class (ii) record may not do, restated

Truncation alone must never earn the label. The second negative control is the
point: a 400-switch board that truncates *exactly as ii1..ii4 do* is still
refused, because its bound is only 2^8. Without the conjunction, a board thirty
orders of magnitude smaller than ii1 would ship as class (ii) on the strength of
a cap we chose ourselves.

### Correction to this entry's own neighbourhood

D-EX-028's closing survey states `check_certificate` runs at "<=3.1 ms per item".
That restates one wall-clock observation as a bound, and a timing is not a bound —
reruns give 3.06 ms and 3.66 ms, and those are prose observations with no
committed artefact either. The defensible claim is the order of magnitude. Every
timing in this ticket is machine-dependent and nothing gates on one.

*This subsection is superseded on the count of samples by D-EX-030 below: there
are four committed measurements, not one observation.*

---

## D-EX-030 — two sentences this record still held after the documents had moved

V6-V23, fifth adversarial round; findings F5-1, F5-2 and F5-10 in
`runs/20260730T021500Z-V23-large-space/adversarial/round5-findings.md`. Both
corrections below supersede published text in **D-EX-029**, which is left standing
and corrected here rather than rewritten.

### `_large_space` does not assert the constants' ordering — supersedes D-EX-029

D-EX-029, on the refusal message that was true only by a coincidence of two
constants, closes: "`_large_space` now asserts the ordering." It does not, and the
code is right where this record was wrong. The gate that entry added asserts a
property of each *bound*, per item — `lower_bound <= MAX_ENUMERATION` raises — and
its own comment says why that was chosen over an ordering check: the ordering is
not stated anywhere as a requirement, and either constant can be moved by someone
who never reads the function. The effect is the same (raise the cap past the
threshold and the affected item is refused instead of publishing a false "past the
cap of ...") but the mechanism is not, and a summary of a guard must not claim more
than the guard.

The same sentence shipped inside `verdict.py`'s own `LARGE_SPACE_THRESHOLD`
comment, 800 lines above the guard it mischaracterised, for two rounds after
`CRITERION.md` withdrew it — alongside the withdrawn "any threshold in
`(256, 1.15e18]` … robust across ~16 orders" (F5-1). Both are now gone from the
source, and that comment states what the audit set does *not* establish. The
lesson, recorded because this ticket produced it three times: a correction written
into a run document is not landed until it is landed in every file that carries the
sentence, and the file that carries it most often is the code.

### "<=3.1 ms per item" is a bound over four committed samples — supersedes D-EX-029

D-EX-029's "Correction to this entry's own neighbourhood" withdrew that figure on
the ground that it "restates one wall-clock observation as a bound". That is wrong
on the count. `probe_answer_key.json` records
`check_certificate_seconds` for four items — `0.00306`, `1e-05`, `0.00075`,
`0.00149`, as the artefact stores them — maximum 3.06 ms, so 3.1 ms bounds all
four. Four committed
measurements in an artefact, not one number in prose. `CRITERION.md` restored the
figure on that basis and this record was left holding the withdrawal, so for one
commit the run document and the decision record disagreed about a single number —
the exact defect D-EX-029 records against `~6e36`, in the opposite direction.

What is **not** claimed: that 3.1 ms is machine-independent. It is a bound over the
four committed samples on the machine that produced them. A prose-only rerun of the
same check gave 3.66 ms, and the repo's evidence-precedence rule (artefact over
prose) ranks evidence *for* a claim — it is not a licence to discard a
counter-observation *against* one, which is a different move and is noted as such.
So both halves stand: 3.1 ms is sourced and recheckable as a bound over
`probe_answer_key.json`'s four rows, and "single-digit milliseconds" is what
survives a change of machine. Every timing in this ticket is machine-dependent and
no gate reads one.

D-EX-028's closing survey and D-EX-029's correction subsection are superseded on
this point by this entry.

### Correction to D-EX-030's own second subsection: the reruns exceed 3.1 ms

The subsection above was written before the reruns existed, and it is now wrong in
the one direction that matters — it says "3.1 ms bounds all four" and then treats
3.1 ms as the sourced, recheckable figure, with "single-digit milliseconds" as the
weaker fallback for a change of machine. The reruns invert that. Four fresh
processes replicating `probe_answer_key.py`'s measurement order gave ii3 at
**0.00348, 0.00360, 0.00369 and 0.00364 s**, and a regeneration of
`probe_answer_key.json` in the V23 worktree recorded **0.00313**. Every one of the
five exceeds 3.1 ms, on the same machine — not a different one. The earlier
prose-only 3.66 ms was not an outlier; it was the first sight of the real spread.

So the honest statement is the fallback, and there is no longer a stronger one
behind it. **What survives is "single-digit milliseconds".** 3.1 ms remains a true
maximum over the four rows `probe_answer_key.json` happens to have committed, and
that is all it is: a property of one recorded run, not a bound on the check. It
must not be quoted as a bound, which is what the subsection above does.

Two things worth keeping from how this went wrong. First, the subsection was
written to correct a withdrawal that was itself wrong on the count — D-EX-029 had
called four committed samples "one wall-clock observation" — and in correcting the
count it inherited the claim, restating a maximum over four rows as a bound without
asking whether the check reproduces near it. Being right about the arithmetic is not
being right about the claim. Second, the evidence-precedence note in that subsection
is exactly the reasoning that let 3.1 ms stand: artefact-over-prose was invoked to
rank the four committed rows above a prose 3.66 ms, and the rule really does not
license discarding a counter-observation — the subsection says so and then does it
anyway, by keeping the figure the counter-observation refutes. Writing down the
right rule is not applying it.

`≤3.1 ms` was struck from all four files that carried it in the same cycle as this
entry: `exam/papers/verdict.py`'s `naive_enumeration_feasible` comment, two places
in this file, `exam/STATUS.md` entry 27, and the V23 run's `CRITERION.md` headline.
The 600-node figure carries that argument on its own and is structural. No gate in
this territory reads a timing, and none should be added.

## D-EX-031 — a tracked generated artefact may not record where its builder stood

**Ruling.** No file under `exam/artifacts/` may contain a path outside the
repository, the building user's name, a temporary directory, or a `.worktrees/`
segment. Paths recorded in generated artefacts are **repo-relative with forward
slashes**, so the value is identical on every checkout and on both platforms.
Enforced by `exam/tools/check_artefact_locations.py`, wired into
`exam/verify.py` as the `artefact_locations` stage and pinned by
`exam/tests/test_artefact_locations.py`.

**What was wrong.** `build_manifest.json` recorded twelve absolute paths — four
papers × `sheet_path` / `key_path` / `cheater_brief_path` — naming whichever
worktree last ran `build_papers`. `write_json` returns an absolute path and
`os.path.join(ARTIFACTS, ...)` builds one, and neither was relativised.

**Why it is a ruling and not a tidy-up.** Three costs, and the third is the one
that binds. Every delivery in this territory carried twelve lines of pseudo-diff
whose two sides mean the same thing — a merge-conflict generator between `exam`
and `exam`. `CLAUDE.md` states determinism as a requirement rather than a
preference, and "same build, same bytes" was false for this file. And
`exam/tools/archive_run.py` folds `build_manifest.json` into the manifest it
writes for every archived run, so the leak propagates into the provenance canon
and from there into a Phase 4 release manifest that publishes every tracked
file; to an outside reader `.worktrees/v5-verdict-three-types/…` is noise and a
disclosure of local directory structure at once.

**What this does not say.** The determinism stage was **not** falsely green.
It compares two in-process builds' sheet digests (`module_for(t).build().sheet(digest())`)
and never reads `build_manifest.json` — `grep -n build_manifest exam/verify.py`
was empty before this change. So the graded sheets were always
location-independent, and the honest statement is that a dimension went
unmeasured, not that a gate lied. The draft of this ticket said the stronger
thing and was corrected by its own author ten minutes later; the stronger thing
would have been worse than the defect.

**Scope, measured rather than assumed.** All 41 tracked files under
`exam/artifacts/` were scanned for Windows and POSIX absolute paths, usernames,
temp directories and worktree segments: every hit was in `build_manifest.json`
and in those twelve values. The other 40 files are clean. So this is a
single-file repair plus a gate, not a sweep — and the gate exists because the
next artefact to grow an absolute path should not need a person to notice it.

**Seen red before it was believed.** `exam/runs/20260730T1640Z-V27-manifest-absolute-paths/GATE-SEEN-RED.md`
records the stage failing on the pre-fix `build_manifest.json` at `8a5a83f9`,
with four independent patterns firing on that one file and no other file
matching any of them.

**One correction inside the fix.** The scanner's first version searched raw file
bytes and reported seven findings in four exam papers, all false: JSON escapes a
newline as backslash-n, so prose containing `asked:` before a line break holds
`asked:\n` on disk, which matches both a drive-letter and a backslash-separator
pattern. It decodes JSON and searches the values a reader would see. A location
scanner that fires on ordinary prose gets switched off within a day, so that is
pinned by a test too.

## D-EX-032 — verify may not overwrite the artefacts it is there to check

**Ruling.** The producers `exam/verify.py` runs write to a **shadow tree**, never
to `exam/artifacts/`. Verify seeds a temporary copy of the artefact tree, points
`build_papers`, `run_exam --calibrate` and `run_selftest` at it through
`EXAM_ARTIFACTS_DIR`, and the new `artifacts_match_committed` stage then asks two
questions that both have to hold: `exam/artifacts` on disk still equals HEAD, and
every tracked artefact a producer wrote is byte-identical to its committed twin.
Mismatch is red. **The gate reports and never adopts** — adopting a rebuild means
running `python -m exam.tools.build_papers` yourself and committing the diff with
the reason in the message. Enforced by
`exam/tools/check_artifacts_match.py`, pinned by
`exam/tests/test_artifacts_match_committed.py`.

**What was wrong.** `python exam/verify.py` printed GREEN without ever comparing
a build against a committed artefact, and the reason was structural rather than
an omission: `build_papers` overwrote the tracked artefacts in place as stage
one, so by the time any later stage could have asked the question, the evidence
was already gone. The determinism stage compares two *fresh* builds to each other
in memory (`PYTHONHASHSEED` 7 vs 99) and opens no committed file at all. So the
four sheets, four keys, `calibration.json`, `exam_summary.json`, `selftest.json`,
`matrix/` and `build_manifest.json` could have been generated by a rubric that no
longer existed — and on the branches lagging `18a39417` they were, `e06bdf52` on
disk against `63ce1eab` from a rebuild — with every gate green throughout.

**Why the shadow tree rather than a diff after the build.** Comparing after an
in-place build only works while nothing has run yet: run verify twice and the
second run compares a rebuild against a rebuild, which is the determinism stage
again under a different name. Redirecting the writes is what makes the question
answerable at any point in the run, and it makes the S23 rule structural rather
than a matter of discipline — verify *cannot* silently adopt, because it never
holds a pen over the tracked tree.

Seeded as a copy rather than empty, because the producers read as well as write:
`run_exam` marks the submissions under `answers/` against the keys under
`truth/`, and a run against an empty tree would be a different run, not a purer
one. The consequence is that files no producer touches compare equal trivially,
so the gate prints its own coverage — on this delivery, *producers rewrote 32 of
41 tracked artefacts; 0 of those differ from the seed* — rather than letting
"green" stand for "compared nothing".

**Two paths had to move before the gate could ever be green.** A build in a
shadow tree recorded where it stood: `build_manifest.json` and the verdict answer
key's `spec_file` entries both derived their values with `os.path.relpath(path,
REPO)`, which under the redirect resolves to `../../AppData/Local/Temp/...`. The
gate would have read the redirect's own footprint as drift. `_repo_rel` therefore
moved out of `build_papers` into `exam.model.artifact_rel`, is now relative to
the **artefact root** rather than the repo root, relabels to `exam/artifacts/…`,
and raises on a path outside the tree. `exam/papers/verdict.py` and the
`report_path` that `run_exam` writes into `exam_summary.json` now use it too —
that last one has been empty in every committed summary, so the absolute path
never shipped, but one marked submission was all it would have taken. D-EX-031's
ruling is unchanged and now has one implementation instead of three.

**The second step of the ticket did not need doing, and the check is why we
know.** RES-3 had already ruled (V25 cycle 72) that the drift was stale committed
artefacts rather than an edited rubric, and prescribed regeneration. On today's
master there is nothing to regenerate: the gate rebuilds all 41 tracked artefacts
and every one reproduces byte for byte, `rubric_digest` `f01dbeb2b6c6`. The
staleness was a property of the lagging branches, and merging them fixed it
before this ticket ran — which is exactly the state the old verify could not tell
apart from drift, and the new one can.

## D-EX-033 — the third primary endpoint had a statistic and no executable protocol

EP, 2026-08-01. Measurements in `runs/20260801T0000Z-EP-endpoint2-prereg/`.

`Theoria.md:373` names 判决题准确率(含特异度) as one of three primary endpoints.
`freeze/STATS_RULES.md` §2 pre-registers the *statistic* — BA from the confusion
half, a specificity floor, the ⟨m⟩ selection rule, a gaming audit. What did not
exist anywhere was a scoring rule tied to code by more than a line number, a
directional prediction per arm per class, or an implementation of §2's own two
rulings. Both of those rulings are registered as launch blockers
(`freeze/launch_blockers.json` 9.15 and 9.16) and both were `unimplemented`.

### 弃权计错 is a layer, not an edit — and the reason is that both sides are right

§2.2 rules that an abstention counts as wrong and names `mark.confusion()` as
the implementation. `mark.confusion()` does the opposite, in three places
(abstained / unanswered / unreadable each `continue` out of the tally), and
D-EX-015 records that as **the right call** — which it is, for a marker: an
abstention is not a wrong answer. The two are both correct and cannot both be
executed on one number, so neither was changed. `exam/endpoint.py:abstain_as_wrong`
converts a confusion cell rather than the marker, keeps the observed rates
beside the converted ones, and prints the arithmetic that connects them.

The consequence that matters is not the rates, it is the **order**: after
conversion `tp+fn` and `tn+fp` equal the class sizes, so neither rate is ever
`None`, so `specificity < ⟨S_min⟩` has a total order. Before it, an arm that
abstained on every class-(iii) item made the pre-registered veto not false but
*undefined* — measured, not argued: the expression raises `TypeError`. A
one-vote veto that cannot be evaluated is not a veto.

**Coverage is read before the conversion.** Conversion fills every denominator
by construction; a coverage read afterwards is 1.0 on every arm including one
that submitted nothing. That single ordering is what lets the memoriser be told
from ground truth.

### The floor that had never cast a vote

Three floors: specificity (不成立), class (ii) coverage (**不可结论**, never
不成立 — silence is not refutation), and BA > 0.5. The third is not a chosen
constant: always-`unsolvable` scores (1.0, 0.0) and always-`solvable` scores
(0.0, 1.0), both averaging one half, so a strict inequality above 0.5 is the
weakest statement that an arm is not a constant. That is also why the two
constant controls are a **matched pair** — a gate that had only ever seen the
bluffer cannot be told apart from one that distrusts the word `unsolvable`.

`prereg.floor_leave_one_out()` disables each floor and re-judges every control,
and on its first run it **refuted this file's draft**: with `bluffer`,
`abstainer` and `null` on the sheet, removing `S_min` changed no verdict,
because all three fail the BA floor too. The floor `STATS_RULES.md` §2.2 calls a
一票否决 had never been observed to cast one. `overclaimer` was then constructed
to be the case only `S_min` refuses — `unsolvable` everywhere but three solvable
items: sensitivity 1.000, specificity 0.375, BA 0.688, full class-(ii) coverage.
Each floor now catches exactly one control alone, and the table is recomputed on
every verify run rather than asserted.

### What the gate credits that it should not, stated rather than hidden

`cheater-v4` — a real transcript, a reader handed the sheet and nothing else —
is **credited**, and is identical to `oracle` in every gated number. The only
column that separates them is `certified_share`, 0.000 against 1.000, and §2.2
demotes exactly that column to exploratory *while citing 这里考的是理由 as its
reason for choosing the scalar*. exam reports the number on every transcript and
does not gate on it: a territory that legislated around a frozen document from
inside itself would be doing the thing this whole apparatus exists to prevent.
Requested through `monitor/inbox/`, with the measurement attached.

### The withdrawn claim was still shipping in a generated artefact

D-EX-028 withdrew 唯不变量推理能答 on 2026-07-30. On 2026-08-01 it was still in
`grading/confusion_matrix.py`'s `class_meaning`, which is **written into
`artifacts/matrix/verdict_confusion.json` and rendered into the `.md` beside
it** — so the last place the withdrawn sentence survived was the version a
reader quotes, three cycles after the decision log said otherwise. Also in two
module docstrings (`papers/verdict.py`, `grading/rubrics_verdict.py`).

`tools/check_withdrawn_claims.py` is the gate, and it is scoped by two rulings
that the first version got wrong and the measurement corrected: a hit within two
lines of a withdrawal marker is **acquitted** (the first version reported 63
hits, nearly all of them records of the withdrawal, including `README.md`'s own
announcement of it), and `exam/runs/**` is **exempt** (the V23 archive quotes
the withdrawn field name on nearly every page because that is what it was
investigating; demanding it be rewritten would be asking for the record to be
falsified).

**A consequence worth naming: the rubric digest moved.** The digest is over
rubric *source*, so correcting a false sentence in a docstring changes it —
`f01dbeb2b6c6` to `26a518d99d99` — and every artefact was rebuilt. That is the
digest working, not a defect: the graded text changed, and a digest that ignored
prose would let the rubric's own description of what it measures drift free of
the rubric.

### Class (ii): why the stronger claim cannot be bought back

Asked to either construct items whose state space genuinely defeats exhaustive
search or re-scope honestly, this ticket found the withdrawal already made in
D-EX-028 and made two things checkable instead — that it reached the artefacts
(above), and *why* the gap cannot be closed from inside this paper:

1. **构造性依据 and a genuine search barrier pull against each other.**
   Theoria.md:289 requires the truth to follow from construction. A variant
   whose unsolvability we know by construction has a short proof by definition,
   and a short proof in a checkable grammar is a cheap decision procedure for
   that instance. All nine unsolvable items carry one — `invariant`, `cut_set`,
   `counting` — and checking any of them is polynomial in the board.
2. **Every wrapper-legal operator is monotone.** `forbid_action`,
   `remap_action`, `step_limit`, `observation_loss`, `win_tighten` remove
   behaviour; none makes a latched switch un-latch. A monotone world is exactly
   the structure relaxations settle for free, which is why the quotient settles
   all four items. Building a level whose relaxation returns *unknown* needs a
   non-monotone dynamic — a toggle, a consumable, a door that re-closes — and no
   wrapper can introduce one, because the hosted environment owns the dynamics
   (Theoria.md Phase 1, 包裹合法集).

So the honest scope is the one shipped, and closing it is an environment-proxy
change rather than a paper change. Written into
`artifacts/prereg/verdict_class_inventory.md` next to the per-item constructive
justifications, so the next reader meets the argument where the items are.

## D-EX-034 — the class (ii) state space is counted, not bounded

`exam/state_space.py`, `exam/tools/state_census.py`, `exam/tests/test_state_space.py`.
Run: `exam/runs/20260802T0000Z-V29-class-ii-state-census/`.

**The complaint.** Class (ii) is "large-space unsolvable", and the number that
made it large was `subset_lower_bound`'s 2^m — a floor derived from a
construction, never a count. The floor is sound and its premises are checked
(D-EX-021, D-EX-029), but `verdict_class_inventory.md` printed it in a column a
reader reads as the state space, and the truth record said
`enumeration_attempted: false` beside `enumerated: null`. So the sentence "the
naive method cannot walk this space" rested on an inequality nobody had ever
turned into a number, on the class that carries the third primary endpoint.

**What it turned out to be.** Three of the four items are now **counted
exactly** on the shipped board:

| item | board | exact states | vs. the 2^m floor |
|---|---|---|---|
| ii1 `vq-721d09813c` | gantry, k=60 | 159,507,359,494,189,904,748,456,847,233,641,349,120 | 120x |
| ii2 `vq-6150a6eeb7` | lattice, k=60 | 159,507,359,494,189,904,748,456,847,233,641,349,120 | 120x |
| ii4 `vq-2986ed8ffc` | orchard, k=60 | 886,151,997,189,943,915,269,204,706,853,563,048 | 8/3x |

The fourth, ii3 `vq-ee54166153`, ships a `step_limit` of 150, which puts an
exact count out of reach of every method here, and carries a **two-sided
bracket** instead: 1.661e37 to 4.133e63. Its lower side is computed from an
explicit strategy, so it is a floor with no optimality argument in it — and it
is **19 orders of magnitude above** the 2^60 the construction proves, which is
the number the inventory had been publishing for that item.

**The method, and why it is checkable.** Positions are enumerated explicitly;
the latch mask is carried as a reduced ordered BDD; the transition relation is
`Level.step` itself rather than a second copy of it. It is the same least
fixpoint `enumerate_states` computes, taken over sets instead of elements — so
the two must agree wherever the enumerator can finish, and
`test_symbolic_census_agrees_with_brute_force` requires exactly that, at k=2..6
across all four constructor+operator families. Nothing is fitted. Applying the
method at k=60 extrapolates the *method*, not a curve.

**Two things are now derived that were literals.** `naive_enumeration_feasible`
comes from the census rather than from the branch the builder called, and
`_large_space` **refuses to build** an item whose census puts it within reach of
the naive enumerator — the reclassification the brief asked for is a gate, not a
belief. Nothing moves: all four items survive it.

**What this does NOT revive.** D-EX-028 withdrew 唯不变量推理能答 because every
class (ii) item is settled by an exhaustive computation over at most 600 nodes.
A count of 1.6e38 does not bring that back; the two numbers answer different
questions and now sit on the same record with a test
(`test_the_count_and_the_search_barrier_answer_different_questions`) that fails
if either is dropped. The count says the *naive* method cannot run. The 600
nodes say *a* method can. Both are true and the class is scored on method
selection, exactly as D-EX-028 left it.

**Two costs paid on the way.** The BDD variable order is column-major, and it is
load bearing: under (row, column) the two alcoves of one column sit 60 variables
apart and the intermediate "reachable within t commands" families need diagrams
quadratic in that separation — row-major exhausted this machine's memory on the
shipped boards. `test_the_variable_order_does_not_move_the_answer` runs both and
requires the same count, so the order is a size decision that cannot become a
correctness decision. And the census's naive probe is `naive_reach`, which is
`enumerate_states` without the per-state shortest path: the path bookkeeping
costs ~473 bytes a state and 200,000-state ceilings across seventeen boards in
one process exhausts memory. `test_the_counting_probe_matches_the_recording_one`
pins the two to the same count and the same truncation flag, including at a cap
that lands exactly on the state count.
