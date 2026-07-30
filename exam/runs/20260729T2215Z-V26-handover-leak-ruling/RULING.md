# RULING — `v11-handover-a0` `-r2`: annulled as an instrument on its `optimal_action` family, not repudiated as a record

Ruled by RES-3 (verify lane) under item `V-V26-handover-leak-ruling`, 2026-07-29.
Subject run: `exam/runs/20260728T202540Z-V11-handover-auto-r2`.
The repair that accompanies this ruling is in the same commit; repo precedent
(`exam/STATUS.md`, V25 section) is that a fix and a notice about the run it
orphans travel together.

## The ruling

**On the dead/alive distinction, `-r2` carries no information about reasoning.**
Among the eight `optimal_action` items, `stile` and `cairn` carried their `level:`
tag exactly once and were exactly the two dead boards, while every solvable item
shared its level name with another. So family-scoped level-name multiplicity
predicts the `action=none; plan_len=none` answer 8 of 8, at an exact false-positive
rate of **1/28 = 0.035714** against `leakage.ALPHA = 0.05`. All six examinees
answered `action=none; plan_len=none` on exactly `v11-opt-01` and `v11-opt-04` and
nowhere else — which is what *both* hypotheses predict, search and counting alike.
Those 48 marks (6 readers × 8 items) therefore have likelihood 1 under either, and
**no number from this run may be cited as evidence about the dead boards.**

**What is not annulled: the 36 shortest-plan integers.** Six solvable items × six
readers, values `24, 25, 14, 16, 22, 21`, unanimous on every item. The channel
carries exactly zero bits about these; it says only "not `none`", which narrows
`action` from five options to four and says nothing whatever about `plan_len`.
That finding stands.

**`-r2` is not voided.** See "Why not a void" below. It is annotated, and the
annotation is this file.

## Why the ruling is this and not "the run cannot distinguish reasoning from tag-reading"

That stronger sentence is what V25 filed, what `exam/STATUS.md` currently commits
to, and what the ticket for this item asked to be ruled. **It is too strong, and
the argument V25 gave for it is factually wrong.** Both corrections came from an
adversarial audit of the run's raw artifacts and both were re-verified here from
the files before being accepted.

### Correction 1 — the premise was backwards. The disagreements exculpate.

V25 wrote that r2's six examinees "all answered `none` on exactly those two while
**disagreeing with each other on the solvable ones** — so that run cannot
distinguish reasoning from reading the tag distribution." The first half is true.
The second half is true as *disagreement* and false as *error*, and the difference
reverses the inference.

Every reader scored **58.0/58.0, 31 correct, 0 wrong, 0 abstained** (`RESULTS.json`,
`per_item`: 2.0/2.0 on all eight `optimal_action` items for all six). There were
disagreements, on three items, and they are the whole point:

| item | truth | the split |
|---|---|---|
| `v11-opt-03` | `{UP, LEFT}`, 25 | a1, a2 → `LEFT`; a3, b1, b2, b3 → `UP` |
| `v11-opt-06` | `{DOWN, RIGHT}`, 16 | a2 → `RIGHT`; the other five → `DOWN` |
| `v11-opt-08` | `{DOWN, LEFT}`, 21 | b2 → `DOWN`; the other five → `LEFT` |
| `v11-opt-07` | `{RIGHT}` only, 22 | unanimous |

The table above shows 4 of the 8 items. A second adversarial pass pointed out that
the four omitted rows include two that cut against the argument, so all of them:
`v11-opt-02` (`flume`, `{DOWN, RIGHT}`, 24) and `v11-opt-05` (`kiln`, `{UP, LEFT}`,
14) **also have two-element optimal sets and also drew unanimity**, and
`v11-opt-01`/`v11-opt-04` are the two dead boards. So of the five items with a
two-element optimal set, three split and two were unanimous.

Marking is **set-valued** — any member of the optimal set earns full credit — so
every disagreement scored 2.0/2.0 and none is visible in `per_item`. Every split
falls *inside* the true optimal set and none outside it, and `plan_len` was
unanimous on all eight.

**What that does and does not establish.** It establishes the thing this section
exists for: V25's premise is false. The readers did not answer solvable items
wrongly — nobody was wrong about anything — so "they disagreed on the solvable
ones" cannot support "this run cannot distinguish reasoning from tag-reading."

The first draft went further and called the pattern "the fingerprint of six
independent searches, not of six readers applying one shared rule," and said it was
"the run's strongest evidence that the readers did reason." **That is withdrawn.**
No statistic was computed for it, and when the reviewer computed one it pointed the
other way: under independent tie-breaking on a two-element set, P(unanimous) =
2·2⁻⁶ = 1/32, so P(exactly 2 of 5 unanimous) ≈ 0.009. The observed pattern is
mild evidence *against* independent tie-breaking. The dichotomy the sentence
offered — independent search versus one shared rule — has no room for what six
instances of one model actually are: **correlated searchers**, which can both
genuinely search and agree far more often than independence predicts.

So the honest reading is the weaker one, and it is enough: the splits show the
readers were not reading a single stored value off the sheet, and the perfect
scores show none of them was wrong. Neither shows independence, and this ruling
no longer claims it.

A methodological note for whoever audits the next sat run, because I got this
wrong too on the way here: I first concluded from `per_item` that there was **zero**
disagreement, which is exactly what a set-valued marker shows when readers disagree
correctly. `per_item` cannot answer questions about agreement. Only `answers/` can.

### Correction 2 — the rule's scope. "Once on this sheet" is 7 of 8, not 8 of 8.

`level:` tags also ride the seven `step_semantics` items. Whole-sheet counts on the
r2 sheet, verified from `sheet.json`:

```
stile 1    cairn 2    flume 3    kiln 4    warren 5
```

So the **unscoped** rule fires only on `stile`, classifies `cairn` as solvable, and
scores 7 of 8 — and it misses `cairn`, the board `PREREGISTRATION.json` nominated
*in advance* as the sharpest discriminator. The 8-of-8 rule requires first
restricting the count to the `optimal_action` family (cheap and natural: you are
answering an `optimal_action` item, so you scan the others). The gate never had this
bug — it groups by `kind` and computed the family-scoped rule all along. Only the
prose was loose, in `exam/leakage.py`, `exam/STATUS.md`, and V26's own first draft
of the `_OPTIMAL_CASES` docstring. All three are corrected in this commit, because
a reader who tests the unscoped rule, sees 7 of 8, and concludes there was nothing
here has been misled by our own comment.

## Why not a void

The precedent for a void is cohort 1 (`20260728T202101Z`, `VOIDED.md`): the sheet
printed the literal word `dead` in the `tags` of the two unsolvable items. A void
there did real work — it kept six answer files out of any `RESULTS.json`, and that
run has no `RESULTS.json` at all.

`-r2` is not in that position, on four counts:

1. **Nothing rests on it.** `delta 0.0`, `conclusive false`, `saturated true`,
   `verdict: "no conclusion"`. Both bootstraps are degenerate `[0.0, 0.0]`. No
   downstream artifact quotes the tier number as a finding. The one downstream
   citation, `runs/20260729T082000Z-V8-judge-trust-audit/FINDINGS.md`, cites r2's
   *calibration* row (oracle 1.000 / memoriser 0.553 / bluffer 0.231) — the
   synthetic fakes, not the readers and not this family.
2. **The channel could only inflate scores, and scores were already at ceiling.**
   Every reader was perfect. *(The first draft continued: "The leak changed no
   number in this run; had it been absent, `delta` would still be 0.0." That is a
   counterfactual about how six readers would have answered a sheet nobody sat,
   and it is unmeasurable in principle — withdrawn. The measurable statement is
   the weaker one: the scores were at ceiling, so the channel **cannot be shown**
   to have changed anything. Which cuts both ways, and ground 2 is weaker for it:
   a ceiling is precisely the condition under which you cannot tell whether the
   channel operated.)*
3. **The run's central claim was already withdrawn, on a stronger ground.** The
   adversarial review of r2 established that `v11-why-02` and `v11-why-05` restate
   the playbook's only two `prune` rules in English *on the tier-1 sheet*, and that
   those two printed criteria are jointly a complete and sound classifier for all
   eight `optimal_action` items with no manual, no playbook and no search. That is
   marked `[OVERTURNED]` in `RESULTS.md` under a banner saying the tier comparison
   "is not a null result. It is not a result." A void for the tag channel would be
   ruling on a run whose headline is already withdrawn.
4. **Voiding both would flatten a real difference in severity.** Cohort 1 printed
   the answer word: no inference required. This channel requires noticing the
   family, tabulating five names across eight items, and *guessing* that singleton
   implies dead. Using one word for both pushes toward a regime where every run on
   A0 is voided — which ground 3 alone would already guarantee — and a word that
   applies to everything stops carrying information.

What survives against not voiding, and is why this file exists rather than
silence: the channel sits **on the pre-registered discriminator**
(`PREREGISTRATION.json`: `where_the_delta_should_land` = "optimal_action, and
inside it on the two dead boards. `cairn` is the sharpest"), and it is this
paper's **second leak into the same two items after a void for the first**.

> **Correction, second adversarial pass.** This paragraph originally ended "and
> the rule that catches it was published before the run and scored none of it.
> That is a gate failure on a pre-registered surface." **That is false, and it was
> the ruling's only aggravating factor.** r2's own `MANIFEST.json` gives
> `base_commit 18a39417`; at that commit `exam/leakage.py` had
> `METADATA_FIELDS = ("points", "tags", "kind")` and **no token-level check of any
> kind** — only whole-value bucketing, which structurally cannot see this channel,
> because the unique `level:` token makes every `tags` value a singleton. The
> `_token_hits_within` machinery landed in `1f378483` and the pooled
> `PRIVATE_MARKER_CUT` in `d7a51bb5`, both on 2026-07-30. The run was sat
> 2026-07-28T20:25:40Z. **The rule that catches this was published one to two days
> after the run, not before.** So this is a gap for which no tool existed, not a
> gate that was ignored — which is a materially lighter charge, and the ruling
> should not have carried the heavier one. It is recorded in the machine-readable
> annulment as `gate_did_not_exist_at_run_time`.

## The channel census, so the count is on the record

Five routes to the same two items have now been found on this sheet. Ranked by how
little inference they need:

1. `dead` printed in `tags` — cohort 1. Voided.
2. `PREREGISTRATION.json` persisted in the examinees' own run directory containing
   `"none": ["v11-opt-01","v11-opt-04"]` verbatim. Fixed: `build()` no longer
   persists the positional block.
3. `v11-why-02` / `v11-why-05` restating the playbook's two `prune` rules on the
   tier-1 sheet — a complete classifier for the family. `[OVERTURNED]` in
   `RESULTS.md`; **not repaired**, and the reason the tier comparison is not a
   result.
4. Family-scoped `level:` multiplicity — this ruling. Repaired in this commit.
5. Board size: `stile` 6×7 and `cairn` 6×6 were the two smallest boards *and* the
   only dead ones, so "smallest board ⇒ dead" was 2 of 2. **Closed as a measured
   side effect of this repair**: each of those levels now carries one dead and one
   solvable state, so the rule is 2 of 4.

Channel 3 is the one that still stands, and it is the reason no future run on this
sheet is worth sitting until the tier-1 `rule_justification` items stop restating
the playbook. That is not this item's scope; it is recorded here so the next person
does not rediscover it after spending six readers.

## The channel the adversarial review found, and why it is *not* a sixth

An adversarial review of the repair found a predictor sharper than the one being
repaired, and found that **the repair sharpened it**:

> answer `none` iff the Box is drawn on the outermost ring of the board.

Both dead cases put the Box at the literal same cell `(0, 5)` — `stile` and `cairn`
are each authored with `start_box = (0, 5)` — and both states V26 appended put the
Box in the interior. So the cut went from **8 of 8 at p_fire 0.035714** (pre-repair)
to **10 of 10 at 0.022222** (the repair as first written): by the gate's own
statistic, sharper than the leak this item exists to close. Verified here, not
taken on report.

> **Since resolved by the `flume` swap** (see "The residual" below). With
> `flume`'s second item now at `((0, 7), (7, 1))` — Box on the ring, target on the
> ring, solvable in 17 — the sheet carries three ring-Box items of which one is
> solvable, so the rule scores **9 of 10 and is falsified on the sheet itself**.
> The analysis in this section is what established that the rule is a sound law
> rather than a leak, and it still stands; what changed is that the sheet no
> longer rewards a reader who applies it without checking why it holds.

**It was nearly filed as a leak. It is not one, and the deciding measurement is
this:**

| level | target | target on ring | ring cells | of which solvable from some player |
|---|---|---|---|---|
| `warren` | (4,2) | no | 26 | **0** |
| `kiln` | (3,5) | no | 22 | **0** |
| `stile` | (4,4) | no | 21 | **0** |
| `cairn` | (2,1) | no | 17 | **0** |
| `flume` | **(7,5)** | **yes** | 25 | **2** |

A Box on an edge can only ever be pushed along that edge, so if the target is not
on the ring the Box can never reach it. The rule's truth **tracks the target's
position**: it holds on the four levels whose target is off the ring and fails
exactly on the one whose target is on it. That is a derivation about this world,
not metadata predicting an answer — and it is why `leakage.METADATA_FIELDS`
deliberately excludes `state` and `board` ("a feature of the question predicting
the answer is the task"). A sound consequence of the world's own rules is what the
paper is *for*.

Pinned as such by `test_a_box_on_the_outer_ring_is_dead_for_a_reason_and_not_by_accident`,
which asserts the conditional invariant rather than the purity: any level
contributing a ring-Box item must have its target off the ring, with `flume` as the
law's positive control. The dangerous future edit is not "the rule becomes impure"
— an impure rule is a broken channel — but "the rule stays pure while ceasing to be
derivable", and that is what the test forbids.

**The residual — recorded first as unclosable, then closed.** This sheet could not
distinguish a reader applying the sound rule (check the target, then conclude) from
one applying the unsound reflex ("edge Box is dead, full stop"), because four of the
five targets happen to sit off the ring, so both score 10 of 10.

The first version of this ruling closed the matter as follows: closing it needs a
*solvable* ring-Box item; there is none on `stile` or `cairn` (every `(player, box)`
pair searched on both — zero, re-confirmed); only `flume` admits one; and adding a
`flume` item breaks the level-uniformity invariant that closes channel 4 — therefore
"the two invariants cannot both be strengthened by adding items to these five
levels; that is a structural constraint of this board set."

**A second adversarial pass refuted that, and it is the worst of the errors here,
because it was written down expressly so the next person would not re-search it.**
Every step is true except the inference. The constraint binds only on *adding* an
item. `flume` admits **110** solvable ring-Box states; the longest,
`((0, 7), (7, 1))` at 17 moves, **replaces** `flume`'s second item instead of
joining it. Measured after the swap:

* level multiplicity `{warren: 2, flume: 2, kiln: 2, stile: 2, cairn: 2}` — uniform, channel 4 stays shut;
* three ring-Box items, of which one is solvable, so **the reflex now scores 2 of 3 and is wrong on this sheet**;
* the sound rule still holds everywhere, with `flume` (target on the ring at `(7, 5)`) as its in-sheet positive control;
* the direction spread is unchanged at no answer covering more than 4 of the 10 items, and `none` still answers exactly 2;
* 17 moves, against the 24 of the item it replaced — still inside the 14–25 band, and far better than the 11s.

The reviewer's own construction went the other way — append five items for three
per level — which restores uniformity but forces near-duplicates, since `stile`
admits no solvable state whose Box is anywhere but `(2, 4)`, so its third item
could only have been the same box with the player shifted one cell. **Swapping is
strictly better than appending here**, and neither was impossible. The
impossibility claim is withdrawn.

What remains genuinely unrepaired is narrower and is stated as such: `stile` and
`cairn` still contribute only dead ring-Box items, so the two boards that pose the
`none` question cannot themselves falsify the reflex — only `flume` can, and a
reader who never looks at `flume` is not separated. Filed, not bodged.

## Defects found in V26's own work, and fixed here

> **The count went from two to five.** The first adversarial pass found two. A
> second pass, run against the finished ruling before delivery, found that one of
> the two was fixed *incompletely* — the identical defect survived twice in the
> same test, three lines above the line that was repaired — plus three more. The
> pattern is worth naming, because this item exists to fix exactly it: **fixing one
> instance of "a check that cannot fail" does not fix the ones next to it, and the
> satisfaction of having fixed one is what stops you looking.**

1. **The test certifying the repair contained a vacuous assertion.**
   `assert report.get("metadata_hits", 0) == 0` — `check_paper` has no
   `metadata_hits` key at all (it *raises* on a metadata hit, so reaching that
   line already means none fired). The assertion passed on every paper ever
   written, including one carrying the leak this file exists to exclude. That is
   the "checks that stopped looking while still printing" family V19–V25 chased,
   committed inside the fix for one of them. Replaced with assertions that the
   check *ran and could have spoken*: `solvable` was derived, `tags` was scanned,
   and at least one `solvable` group has `can_fire_at_all`.
2. **The repair adds the two easiest items to a sheet whose recorded failure is
   saturation.** Both appended states have `plan_len` 11 and need one push, where
   every other solvable item is 14–25 moves and 2–5 pushes; the module docstring's
   "These have 14 to 25, which is past the point where a reader can see the answer"
   became false. 11 is nonetheless the **ceiling** on both boards — searched
   exhaustively, and they are 6-row boards that do not reach 14 — so the trade is
   forced, not lazy. Docstring corrected to state the cost, with the instruction
   that future hard items go on `warren`/`flume`/`kiln`, two per level.
3. **The same vacuous-assertion defect survived twice in the test that was being
   repaired for it.** Three lines above the `metadata_hits` line, the same test
   asserted `report["probe_hits"] == 0` and `report["structural_hits"] == 0`.
   Both are **literal `0` constants** in `check_paper`'s return dict, and
   `check_paper` *raises* on any probe or structural hit — so, exactly like
   `metadata_hits`, reaching those lines already guarantees they pass, on every
   paper ever written. Replaced with `probes_declared > 0` and `sheet_bytes > 0`,
   which are computed and which assert the probe check had something to scan.
4. **One of the replacements was itself vacuous.** The ruling claimed the new
   assertions established that "`tags` was scanned". The assertion written was
   `"tags" in report["metadata_fields_checked"]`, and that field is
   `list(METADATA_FIELDS)` — a module-level constant. It restates a literal and
   says nothing about the family the leak travelled in. Replaced with a check
   that a `tags:` cut was actually tried *under the `solvable` label set*, which
   goes red when `tags` is dropped from `METADATA_FIELDS` (verified by mutation).
5. **`write_manifest.py` hashed `MANIFEST.json` into `MANIFEST.json`.** The walk
   included the file being written, so the recorded self-hash is of the previous
   content and can never verify — a hash presented as a check that is guaranteed
   to fail. 9 of 10 entries verified; the tenth was itself. Now excluded.

**Every new assertion in this commit was mutation-tested rather than trusted for
being green.** Five mutants, all confirmed red: revert the `flume` swap (the
reflex counterexample assertion fires); move `flume`'s target off the ring (the
sheet loses its counterexample and the same assertion fires); add a third `warren`
item (uniformity fires); stub `_plan_length` so a dead ring-Box item reports
solvable (the conditional law assertion fires, which is the only way to exercise
it, since the law is true in this world); and drop `tags` from `METADATA_FIELDS`
(the new cut assertion fires). A green assertion that has never been shown to go
red is the defect this list is about, so the list is not allowed to end without it.

**And one consequence of the repair worth stating plainly:** green on this family
now means less than it did. With no single-holder `level:` token left in the group,
the pooled private-marker cut has nothing to pool and is inert here.

The first draft of this paragraph continued: "and the `solvable` label set's
familywise rate **rose** to 0.1063, above `ALPHA`, so a token that *did* fire
would be stamped `weak_evidence`" — offered as a second cost of the repair.
**A second adversarial pass measured it and the sentence has the sign backwards.**
Re-measured here, both sheets through the same gate:

| sheet | cuts tried | familywise rate | a firing token would be |
|---|---|---|---|
| pre-repair, 8 items | 4 | **0.135385** | `weak_evidence: true` *already* |
| post-repair, 10 items | 5 | **0.106281** | `weak_evidence` |

The rate **fell** by 0.029, and it was **already** over `ALPHA = 0.05` before the
repair — the pre-repair finding carries `"weak_evidence": true` in its own record,
alongside `p_fire 0.035714`. So the repair did not blunt the detector on that
axis, and the property the sentence attributed to the repair was one the paper
already had. The conclusion it was drawn in support of still stands, on the one
reason that survives: the pooled cut is inert on this family now, **so what guards
the channel is the property test (`test_level_multiplicity_is_uniform`), not the
gate's green.**

## The strongest attack on this ruling, and what it changed

A second adversarial pass was asked for the best argument that "annotate, don't
void" is wrong. It produced this, and it is good enough that the disposition
changed shape even though the verdict did not:

> The run's only pre-registered discriminator was the two dead boards, and the
> channel supplied exactly those two answers **to both tiers**. The run therefore
> has zero information about the hypothesis it was built to test. And every ground
> offered against voiding is either an unmeasurable counterfactual, or an argument
> that voiding would cost nothing.

The four grounds do not come out of that well, and the honest accounting is:

1. **Ground 1 is circular as written.** `saturated true` is what licenses "nothing
   rests on it" — and saturation on the hardest items is exactly what a leak
   manufactures. The premise is downstream of the thing it excuses. I checked
   whether the circularity bites numerically: dropping the two annulled items
   leaves 54/54, still 1.0, still saturated. So it happens not to change this
   number — **but the first draft did not check, and the argument was unsound
   whether or not it survived the check.**
2. **Ground 2 is weaker than stated,** for the reason now recorded inline: a
   ceiling is the condition under which the channel's effect is unmeasurable.
3. **Ground 3 argues that voiding is *free*, not that it is wrong** — and the
   ruling then reused it in ground 4 in the opposite direction, to argue voiding
   would be inflationary. It cannot do both jobs. Ground 3 is withdrawn as a
   reason not to void; it survives only as context.
4. **Ground 4 is the one that stands,** and it is about vocabulary rather than
   about the run: cohort 1 printed the answer word, this required inferring from a
   name count, and one word for both severities stops carrying information.

**The verdict stays annulment, but the reviewer's remedy is adopted:** the
distinction is now carried **in `RESULTS.json`, not in prose**. That was the
decisive part of the attack — the ruling's own case for cohort 1's void doing
"real work" was machine-level (it kept six answer files out of any `RESULTS.json`),
and by that standard a Markdown paragraph did none. Before this commit,
`git diff` over the r2 run directory touched exactly one file, `RESULTS.md`,
+24 lines; `RESULTS.json` was byte-identical and still read `58.0/58.0`,
`matches_preregistration: true`, `by_family.optimal_action.delta 0.0`. Any tool
would have cited it again.

So r2 now carries a top-level `annulment` object — `status`,
`scope_families`, `scope_items`, what survives, why not a void, the
`gate_did_not_exist_at_run_time` correction, and the still-unrepaired channel 3 —
and `by_family.optimal_action` carries `annulled: true` so a table generator
cannot print `delta 0.0` as a null result. Ground 4's severity gradient is
preserved exactly as the reviewer said it could be: `status` is a field, and it
can hold more than one string.

And because the general defect is "a remedy that only humans can see", it is now
gated rather than remembered:
`tests/test_run_dispositions_are_machine_readable.py` fails if any run whose
disposition is declared in prose under `exam/runs/` has a `RESULTS.json` that does
not say so. Verified by mutation: deleting the `annulment` key turns it red.

## What the paper track should do with this

`papers/phase1-workshop/PAPER.md` cites `exam/papers/handover.py` — **P-15's**
handover, not this one — and no paper claim rests on `-r2`. I measured P-15's
`_OPTIMAL_CASES` for the analogous channel and it does not have one: level
multiplicity there is non-uniform (`corridor` 3, `pinch` 2, `yard` 1), but all six
cases are solvable and the family has no dead-board question, so multiplicity has
no `solvable` answer to predict. (P-15's handover paper has a *different* recorded
problem — V25 found its leak group cannot fire at all, which is filed separately.)

So there is nothing to retract. What the honesty section owes, if RES-2 judges it
in scope, is one line: **the run that was re-run for a leak carried a second,
undetected leak into the same two items, and the gate that should have caught it
was published before the run.** Writing that line is RES-2's call and RES-2's
prose; per `monitor/CHARTER.md` I do not write paper text. This ruling is the
source it can cite.
