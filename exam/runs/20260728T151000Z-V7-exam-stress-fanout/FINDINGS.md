# V7 — findings

`MANIFEST.json` beside this file is canonical; this is the narrative. Written
incrementally as the twenty per-world examiners reported, so that a context wall
costs the synthesis and not the evidence.

## 0 · The work order's premise, and the honest matrix

V7 asks for "四题型 × 20 个世界，全量 80+ 组合，每个世界派一个 subagent". **That
matrix does not exist.** Of the exam's four question types, exactly one ports to a
generated world:

| question type | builder | signature | world |
|---|---|---|---|
| held-out | `exam/papers/heldout_worldgen.py` | `build_for(world_id, per_class)` | **any of the 20** |
| held-out (A0) | `exam/papers/heldout.py` | `build()` | A0, hand-built |
| handover | `exam/papers/handover.py` | `build()` | A0, hand-built |
| adaptation | `exam/papers/adaptation.py` | `build()` | A0, hand-built |
| verdict | `exam/papers/verdict.py` | `build()` | A2, hand-built |

Three of the four take no world argument at all. The blockers were already
recorded, blocker by blocker, in `exam/runs/20260728T090621Z-V2-exam-on-worldgen/GAPS.md`:
adaptation needs a rule-mutation layer that does not exist (`worldgen.mutate`);
handover needs a theory somebody *authored* for a generated world, and the factory
makes worlds, not theories; verdict class (ii) needs ≥10¹² configurations against a
largest world of 2 654 states, nine orders of magnitude short, and needs nine
unsolvable worlds against a catalogue holding one.

So the true full matrix is **20 worlds × 1 type = 20 papers, 236 items**, and V2
already ran it. Re-running it and calling that a stress test would have been
theatre. What had *not* been done is the thing the work order actually asks for
underneath the arithmetic — grader misjudgement, zero-discrimination items, and
the verdict classes reported apart — so that is what was built and run.

**The twenty subagents were not spent re-running a 1.7-second command.** Each was
given one world and asked to do work no driver does: re-derive that world's items
from `spec.json` by hand against the recorded truth, stress the marker with
near-miss answers, and *try to build a cheap examinee that beats the paper without
a world model*. Twenty independent attempts at the same attack is the only way to
learn whether a single success was a quirk of one world.

## 1 · The headline: the exam's own leak checker rejects all twenty papers, and nothing ever pointed it at them

`exam/papers/heldout_worldgen.py:204` sets each item's tags to
`(split, "rule:%s" % rule)`, and `exam/model.py:108-110` copies `tags` onto the
**sheet side**. So every question prints the name of the rule that answers it:

```
{"item_id": "t1-portal-oneway-000", "action": "UP",  "tags": ["heldout", "rule:walk"]}
{"item_id": "t1-portal-oneway-001", "action": "DOWN","tags": ["heldout", "rule:blocked_by_wall"]}
```

Twelve lines above that assignment, the same module states the discipline it is
breaking: a sheet that lists the rule names "hands the examinee the alphabet it is
being asked to discover."

The exam has a leakage gate built precisely for this, and **the gate works**.
Pointed at these papers by hand it refuses every one:

```
python - <<'PY'
from exam.papers import heldout_worldgen as hw, worldgen_port as port
from exam.grading.registry import digest
from exam import leakage
d = digest()
for w in port.world_ids():
    p = hw.build_for(w, 2)
    try:    leakage.check_paper(p, p.sheet(d), key_doc=p.key(d)); print("CLEAN", w)
    except leakage.LeakageError: print("LEAKS", w)
PY
```

→ **20 of 20 worlds leak, and all 236 of 236 items are hit by their own declared
leak probe** — every item, not a majority.

**A correction to this run's own first draft, which said 160.** That figure was
counted from the text of the raised `LeakageError`, and `check_paper` formats its
message with `findings[:8]` — so 20 worlds × 8 printed findings = 160. The draft
said "verified by the synthesist, not taken from a subagent report", which was
true and did not help: I verified it by reading a truncated error message instead
of counting the findings. The right count comes from the probe test itself:

```python
hit = sum(any(pr in canonical(it.sheet_side()) for pr in it.leak_probes)
          for it in paper.items)     # 236 of 236 across the catalogue
```

An adversarial pass found this. It is the sharpest thing in the run, because the
error is not "trusted a subagent" — it is "checked personally, and the check was
narrower than the claim it licensed".

**Two nearby claims from the draft were also wrong, and are worth keeping visible.**

* *"`tags=(split,)` is a one-line change."* It is not. Applied to all twenty
  worlds, **16 items across 4 worlds still trip the gate** — the residue comes
  from `Paper.world`, which the sheet also publishes: `world_id` (the string
  `t1-walk-maze` contains `walk`) and `families` (`['push']`). The fix is at
  minimum three places, and `world_id` cannot simply be dropped without breaking
  provenance.
* *"The reason nobody saw it is structural rather than careless."* Half true, and
  the false half matters more. The structural part holds: `leakage.check_paper`
  has exactly one non-test caller, `exam/tools/build_papers.py:72`, which iterates
  `BUILDERS` = `['heldout','handover','adaptation','verdict']` and calls
  `module.build()`; `heldout_worldgen` exposes `build_for(world_id, per_class)` and
  is not merely unlisted but **unreachable** through that path. But **a test
  written for exactly this leak already exists and is vacuous**:
  `exam/tests/test_worldgen_papers.py:71` asserts the JSON-quoted `'"walk"'` is
  absent from the sheet — and the sheet says `"rule:walk"`, so the quote delimiters
  never match. Of 59 (world, rule) pairs, **56 pass on that string-quoting accident**;
  only `push`, on three worlds, is genuinely covered by the test's `spec.json`
  carve-out. The gate was pointed at this. It missed on a matcher bug.

**And the consequence is larger than the draft allowed.** The draft said the leak
"does not affect any number V2 or this run reports" — true, because no synthetic
examinee reads a sheet — and then soft-pedalled the severity. Measured, the tag is
not merely "the alphabet": **the `rule:` tag predicts `frame_changes` on 235 of 236
items (99.6 %)**, which is precisely the `free` / `changing` partition that §3 is
about. Bolted onto §2's prior it is worth **+6.8 points and one further perfect
world** with no world model added. A reader doing no reasoning at all is handed the
answer to "does anything happen here".

## 2 · A theory-free prior scores 1.000 on twelve of the twenty worlds

Five of the twenty examiners independently wrote a variant of the same cheap
strategy and reported it tying the oracle. Convergence from five isolated contexts
is worth more than any one of them, but the claim deserved to be stated once as a
single function applied to all twenty worlds, with no per-world constant that
could hide a fitted parameter. That is `prior_sweep.py` beside this file:

> Read the agent's cell from `legend["agent"]`. Step one cell in the action's
> direction. If the target is off-grid or holds `legend["wall"]`, answer with the
> input frame unchanged; otherwise move the agent there and repaint the vacated
> cell with `legend["floor"]`.

That is the whole of the *code*. It is not the whole of the world model — the
legend is the other half, and the corrections below measure how much of the half
it is. The strategy reads only sheet fields, never `Item.truth`, never
`ground_truth.json`, never the trace, and it contains no world id and no tuned
constant. Scored through the real marker:

| | |
|---|---|
| worlds scoring **1.000** | **12 of 20** |
| worlds beating their own bluffer floor | 18 of 20 |
| frame-changing items taken | **109 of 139 — 78.4 %** |

The twelve perfect worlds: `t1-walk-maze`, `t1-push-corridor`, `t1-switch-toggle`,
`t1-switch-latch`, `t1-portal-oneway`, `t1-cycler-gate`, `t1-fragile-bridge`,
`t2-portal-pair`, `t2-portal-paired`, `t2-lock-fragile`, `t2-cycler-lock`,
`t3-gravity-fragile`. Full table in `prior_sweep.json`.

The two that resist — `t3-full-house` and `t2-unsolvable-nodoor` — resist in an
instructive way: the prior scores *exactly* their bluffer floor, but on a
**different set of items**. It wins frame-changing items and loses an equal number
of unchanged ones. So the total score is not monotone in how much a world model
the examinee holds, and two examinees can tie at the same fraction while agreeing
on nothing.

**The finding is not that the strategy is clever.** It is about eight lines long
and every examiner reached it independently within one session. The finding is
that on most of this catalogue, the held-out paper's score is not evidence that
the examinee learned anything: a prior brought in from outside answers it. Several
examiners put the distinction better than a driver can — the strategy did not
learn a rule, it brought one, and no instrument in the exam separates those.

**Three corrections to how this run first stated that, all from the adversarial
pass, all measured.**

* *"That is the whole world model"* was false. **The legend is the load-bearing
  half.** Strip `legend["agent"]` from the sheet the prior reads and it scores
  **0.4110** — the bluffer floor to four figures; strip `legend["wall"]` and it
  scores 0.4619. Every point above the floor is bought with the sheet's naming of
  the agent and the wall, which in this framework's own vocabulary is the manual's
  **object ontology**, handed to the examinee. The right claim is that *legend plus
  eight lines* beats the paper, and that the legend is on the sheet by design.
* **The prior is exactly the catalogue's two modal rules, and nothing else.** Over
  all 236 items it is right on every `walk`, `blocked_by_wall`, `walk_through_door`
  and `walk_through_cycler` item, and **0 for 32** on `push`, `teleport_twoway`,
  `toggle_switch` and the rest. `walk` and `blocked_by_wall` are 9 181 and 6 150
  transitions catalogue-wide against ≤ 244 for anything else. "No per-world
  constant" defends against parameter fitting; it does not defend against
  hypothesis-class selection by twenty agents who had each already read a world.
* **§2 and §3 are one finding counted twice.** Nine of the twelve perfect worlds
  contain no rule but `walk` and `blocked_by_wall`. So "a theory-free strategy
  scores 1.000 on twelve worlds" and "the rule the world is named for is the one
  rule its paper does not examine" are the same fact from two directions. The
  defensible statement is narrower and still serious: **at `per_class=2` the
  matched quota fills twelve of twenty papers exclusively with movement items, and
  movement is guessable from the legend.** That is a result about the sampler, not
  a proof that the exam is beatable without a world model.

## 3 · Zero-discrimination items: 41 % of the paper ranks nobody, and that is the optimistic figure

`exam/tools/discrimination.py` (new, this run) classifies each item by which of
`oracle` / `memoriser` / `bluffer` answer it correctly. `null` is excluded from the
vote on purpose — a blank page cannot distinguish two items, and letting it vote
would make every item look as though it discriminated something.

Catalogue totals at `per_class=2`, 236 items over 20 worlds:

| class | meaning | count | share |
|---|---|---|---|
| `free` | all three correct — a theory-free bluffer already has it | **97** | 41.1 % |
| `memorised` | oracle + memoriser; separates reading the trace, not holding a theory | 70 | 29.7 % |
| `theory` | oracle alone — the only class asking for a world model | **69** | 29.2 % |
| `dead` | nobody, oracle included — would be a marker defect | **0** | 0 % |

Zero `dead` and zero anomalies, which is the one clean result here: it means the
marker never rejects its own ground truth, and it means this instrument and
`run_matrix`'s calibration agree.

**Four rules produce no informative item on any world at this quota** —
`blocked_by_wall`, `blocked_by_block`, `blocked_by_door`, `latch_already_set`.
The cause is structural, not sampling: each rule's consequent *is* "the frame does
not change", so its ground truth is byte-identical to the bluffer's answer, and no
trace length or world redesign can make a stasis rule discriminate under a
frame-exact rubric. They are **4 of the 8** items on a typical tier-1 paper.

Two qualifications the adversarial pass forced, both measured. **The catalogue has
seven** 100 %-stasis rules over the full reachable relation, not four; the others
are `blocked_by_lock`, `blocked_by_collapsed` and `blocked_toggle_would_shut_door`.
And **which of them reach a paper is a property of the quota**: the barren set is
five at `per_class=1`, four at 2, two at 3 and one at 4. Barrenness is derivable
from the rule table without running anything; membership of the *reported* set is
not, and this run's first draft claimed otherwise.

And §2 shows that 69 is still too generous. The `theory` class is defined against
three voters, none of which implements the most obvious grid prior, so it means
"not settled by these three" and not "requires a world model". Applying the prior
of §2, the informative residue falls from 69 items to **16 across the whole
catalogue** — and to **zero on fourteen of the twenty worlds**. Nine separate
examiners independently reported their world's honest effective size as 0.

(The first draft said 30 and twelve. 30 was `139 − 109`, the *frame-changing* items
the prior missed — a different quantity, spanning `memorised` items too. The
corrected figures are worse for the exam than the ones I first published, which is
the direction an error of this kind least often runs.)

The single most-repeated structural cause, found independently on world after
world: **the rule the world is named for is the one rule its paper does not
examine.** `t1-portal-oneway` never asks about a portal (1 trace witness, 1
held out, against a matched quota of 2). `t2-portal-pair` never asks about a
portal (5 witnesses in trace, 1 held out). `t1-fragile-bridge` never asks about
the bridge (`cross_fragile`: 0 in trace). `t1-switch-toggle` never asks about the
switch. The matched-quota rule that keeps the printed `replay`/`heldout` tag from
becoming a hint is correct and is doing real work — and its cost is that the
mechanism with the fewest witnesses is always the mechanism that gets dropped,
which is exactly the interesting one.

## 4 · Marker misjudgement, by question type

Every examiner ran the same near-miss battery against `rubrics_heldout.py`. **No
examiner found a case where the marker paid for an answer it should not have** —
transposed grids, one-cell errors, ragged rows, short grids, out-of-palette
colours and prose are all correctly `wrong`, and the per-world palette override
works (the A0 rubric's hard-coded `{0,2,4,8}` would have rejected every generated
frame; it does not). Both structural invariants hold on all twenty worlds: `null`
scores `unanswered` everywhere and never `correct`; `oracle` is never marked
`wrong`.

The defects are all in the **verdict label**, not the mark, and they converge:

* **Format failure is indistinguishable from a wrong prediction.** A submission
  with every frame exactly right but cells serialised as `"6"` or `6.0` scores
  0.000 with a verdict field identical to an examinee that predicted nothing
  correctly. The distinction survives only in `detail["why"]`, which no aggregate
  reads. The float case is the sharpest: JSON has no integer/float distinction, so
  one serialiser writing `6.0` zeroes a correct world model.
* **Silence is punished four different ways.** `None` → `unanswered`, but `{}`,
  `[]` and `{"frame_after": null}` → `wrong`. That is the exact distinction
  `exam/grading/mark.py:9-13` exists to preserve — an arm with no deliverable
  scoring zero *by having nothing to submit* is a finding, not a failure to answer.
  It also has a bite in the new instrument: a `{}`-everywhere examinee would be
  classified `dead`, i.e. reported as a *marker defect* when it is just silence.
* **`{"abstain": 1}`, `{"abstain": "true"}` and "I don't know" are `wrong`, not
  `abstained`** — `_is_abstention` uses an `is True` identity test and a
  four-string allowlist. "unsolvable" is among the words that fall through, which
  is the one word `Theoria.md` 1.11 most cares about an examinee being able to say.

## 5 · The three verdict classes

Reported apart, as the work order requires, and the honest report is short: **no
generated world carries a verdict item, so the three classes can only be reported
on the hand-built A2 paper.** The classes are `small_unsolvable` (5 items),
`large_unsolvable` (4) and `solvable_hard` (8); `exam/grading/confusion_matrix.py`
already splits sensitivity and specificity by class and keeps abstentions out of
both denominators, reporting `null` rather than `0.000` on an empty one.

The catalogue cannot supply class (ii): `large_unsolvable` requires ≥10¹²
configurations (`LARGE_SPACE_THRESHOLD`) and the largest generated world has
**2 654** reachable states. It cannot supply the class balance either — one world
of twenty is unsolvable, against a paper needing nine. V2 refused to ship a
two-class paper under a three-class name, and that refusal still stands.

The finding worth carrying forward is from the unsolvable world itself: **two
thirds of its items are free**, the highest share in the catalogue, and the cause
generalises. An unsolvable world is mostly `blocked_by_*` rules, stasis rules are
permanently free, so *examining unsolvable worlds by held-out frame prediction is
structurally the least informative thing the instrument can do*. A framework that
wants credit for saying "unsolvable" needs the verdict question type on generated
worlds, and that is upstream work in `worldgen/`, not exam work.

## 6 · Two identities, and the instrument's own limit

Both were proposed by individual examiners and both were then checked by the
synthesist over all 236 items rather than accepted:

**`class` is a function of `(split, frame_changes)` — zero violations in 236
items.** The mapping is total and exact: `(*, False) → free`, `(replay, True) →
memorised`, `(heldout, True) → theory`. It follows from the voters' definitions —
the memoriser replays the trace and otherwise predicts stasis, the bluffer always
predicts stasis — so it is not an accident of this catalogue and cannot be fixed by
better sampling. **The profiler therefore does not measure difficulty.** It
measures "held out, and something moved", which is two fields the paper already
carries, one of them printed on the sheet. Its real earnings are `dead` and
`anomaly`: both empty, which is a genuine result about the marker.

That limit is now written into `exam/tools/discrimination.py`'s own docstring
rather than left in a run report, and `exam/tests/test_discrimination.py` pins it
with a test **designed to fail** the moment a genuinely independent voter is added,
so the fix cannot land quietly and leave the old number in circulation.

**Exactly one rule in the catalogue produces both changing and non-changing
items**: `walk` on `t2-gravity-push`. That world's examiner found the cause without
being told to look — the transition is `up_is_inert`, a declared *cascade* rule
that carries no tag of its own and is filed under `walk`. So the single exception
to the identity is a labelling artefact in `worldgen/`, not a counter-example.

**A rule whose consequent is "nothing changes" is barren a priori** — in every
world, at every quota — because its ground truth *is* the bluffer's answer. The
four rules the profiler discovers empirically (`blocked_by_wall`,
`blocked_by_block`, `blocked_by_door`, `latch_already_set`) are derivable from the
rule table without running anything. On a typical tier-1 paper they are 4 of 8
items: **a flat 50 % tax, known in advance, paid by every world.**

## 7 · The recommendation the fan-out converged on, which nobody was asked for

Nine examiners independently proposed the same fix and three measured it: **the
quota is set too high, and raising it makes papers worse.**

`per_class=2` requires two witnesses of a rule in the trace *and* two held out.
The rules with the fewest witnesses are always the world's signature mechanisms —
they are rare precisely because they are special — so the matched-quota rule
systematically drops the interesting rule and keeps the generic one. Measured
consequences, from three worlds that ran the comparison:

* `t2-cycler-lock`: `per_class=1` admits 5 rules and 10 items and drops the cheap
  prior to 0.800; `per_class=2` admits 3 rules and the prior scores 1.000;
  `per_class≥3` admits 2. **A bigger paper covers less.**
* `t2-portal-pair`: at `per_class=1` the portal rule qualifies and the strongest
  theory-free examinee falls from 8/8 to 4/6.
* `t3-gravity-fragile`: `per_class=1` gives 4 rules instead of 2 at the same item
  count, and is the only setting where the paper ranks its examinees in the right
  order.
* `t2-gravity-push`: `theory_share` *peaks* at `per_class=1` (0.250) and is lower at
  every larger quota (0.125 at 2, 0.167 at 3), because the barren rule grows at the
  same rate as the informative one. An earlier draft said "falls monotonically";
  it falls then partly recovers, and the peak at 1 is the part that matters.

The matched-quota argument — an unmatched quota turns the printed `replay`/
`heldout` tag into a hint — holds just as well at 1 as at 2. The quota was not
chosen against this evidence, because this evidence did not exist until now.

**A cheaper and larger fix, proposed independently by five examiners: add the grid
prior as a fifth calibration fake in `exam/grading/calibration.py`.** It is about
twenty lines, it is world-independent, and it would make the whole failure visible
inside `run_matrix` — as a published number next to the bluffer floor — instead of
requiring an instrument like this one to go looking. That is the shape the exam
already uses for the bluffer, and the bluffer floor is exactly the statistic that
turned out to be too generous.

## 8 · What this run did not do

* **It did not fix the leak.** `tags=(split,)` at `exam/papers/heldout_worldgen.py:204`
  is a one-line change and `exam/model.py` already keeps `rule` on the key side
  where `axes` reads it. It is left undone because a leak that has been in every
  published number since V2 deserves its own item, with the V2 artefacts re-derived
  behind it, rather than a quiet edit inside a measurement run.
* **It did not add the fourth voter**, for the reason the docstring gives: a voter
  that is itself a world model needs an argument for why it is the *right*
  baseline, and inventing that argument inside the run whose numbers it would
  rewrite is the tuning the process exists to forbid.
* **It did not run the other three question types on generated worlds**, because
  they cannot be run: three of four builders take no world argument, and each is
  blocked on named upstream work (`worldgen.mutate`; an authored theory; nine
  orders of magnitude of state space).
* **It measured twenty synthetic worlds and one marker.** Nothing here is a claim
  about ARC, about a real examinee, or about the framework's arms.
