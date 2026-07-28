# V2 · 考卷跑在世界工厂的产物上 — running notes

Worker `W-1540`, branch `agent/v2-exam-on-worldgen`, base `6072b06`.
Written as the work happens.

## 0 · The dependency landed, and what it changes

`C1-worldgen` merged at `7cb6775`. `worldgen/out/worlds/` now holds **20
generated worlds**, three tiers, each shipping its own ground truth, coverage,
and an A0′ reversibility stamp — and a read licence that keeps the truth files
away from anything being examined.

That matters to `exam/` specifically, because the exam's hardest constraint is
stated in its own README: *an exam has to have ground truth, ground truth has to
come from construction, and the construction has to stay away from the
examinee.* Until now the exam had four hand-built worlds to construct from. It
now has twenty generated ones, with their ground truth generated alongside.

## 1 · Baselines before anything is touched

| suite | result |
|---|---|
| `python -m pytest exam/tests -q` | 158 passed |
| `python -m pytest worldgen/tests -q` | 241 passed |

## 2 · What the item asks for

1. the four question types, run over the factory's output, in batch;
2. a first grading matrix and a per-question-type difficulty distribution;
3. the marker calibrated on the new worlds against known full-score and
   zero-score fake examinees — i.e. *does the marker itself get it wrong.*

Point 3 is the one that governs the order of work. The exam's own rule is that
the question-setter can be checked by reading it and the marker cannot, because
a marking bug produces a plausible number and a plausible number is
indistinguishable from a result. So calibration is not a final step here; a
grading matrix produced by an uncalibrated marker is not a measurement.

## 3 · What shipped

**Held-out prediction, over all twenty worlds, with the marker calibrated on
each.** 236 items. `python -m exam.tools.run_matrix`.

Three things the A0 paper had to *construct* are now *measured*, and that is the
real content of the port rather than "more boards":

| the A0 paper reconstructs | the factory measured |
|---|---|
| the event class of a transition, via a hand-written six-way classifier | `GridWorld.explain()` returns the rule name from the same code path that produced the state |
| what the arm was shown, by re-running the explorer | `raw_trace.jsonl`, the published artefact itself |
| the well-formed universe, as a Cartesian product | `GridWorld.reachable()` |

The classifier is not ported, it is deleted. A0 could only *test* that its
classifier and its world agreed; here they cannot disagree.

### The quota had to become derived, and that is what makes twenty worlds work

A0 fixes six event classes at hand-tuned counts. That cannot survive contact
with worlds whose rule sets differ in name, count and frequency --
`t1-walk-maze` fires two rules, `t3-full-house` six. So the quota is derived per
world, and a rule qualifies only when it has `per_class` transitions **inside**
the published trace and `per_class` **outside** it.

Both halves matter. The second is A0's own recorded failure: a rule witnessed
once has no second witness to hold out, which is the A0' criterion the factory
now stamps every world with. The reconnaissance estimate was that roughly the
tier-1 half of the catalogue would be unusable; with derived quotas **all twenty
qualify**, 2-6 examinable rules each, 59 examinable and 46 blocked in total.

### The matrix

```
world                    tier items  oracle   null memoriser  bluffer     gap
t1-walk-maze             1        8   1.000  0.000     0.750    0.500   0.500
t1-push-open             1       12   1.000  0.000     0.667    0.333   0.667
...
t3-cycler-portal-lock    3       16   1.000  0.000     0.625    0.250   0.750
t3-latch-maze            3       20   1.000  0.000     0.700    0.400   0.600

236 items; mean gap 0.555; mean bluffer floor 0.439
gap by tier: {"1": 0.556, "2": 0.512, "3": 0.629}
```

### The difficulty finding, which is the one worth carrying

**Raw fractions are not comparable across worlds.** The floor a theory-free
examinee gets for predicting stasis ranges from **0.25 to 0.667** across the
catalogue, because worlds differ in how much of their rule set is a
`blocked_by_*` rule that changes nothing. A 0.70 on `t2-gravity-push` (floor
0.625) is worse than a 0.50 on `t3-cycler-portal-lock` (floor 0.25).

The matrix publishes the floor and the headroom per world and says so in a
`comparability_note`, and there is a test pinning the note, because this is
exactly the kind of finding that gets dropped in a later refactor and then
silently mis-read.

## 4 · Three things my own tests caught

* **Publishing the world roster leaked answer vocabulary.** I put
  `generated_worlds` into `guard.provenance()`, which lands on every sheet. The
  ids `t2-unsolvable-nodoor` and `t1-walk-maze` put *unsolvable* and *walk* --
  both live answers on the adaptation paper -- in front of the examinee, and the
  exam's existing leak probes failed two tests immediately. The roster is now a
  count. This is the argument for having the probes, stated as an event rather
  than as a principle.
* **The marker's expectation for the memoriser was wrong, in my favour.** I
  predicted it would score exactly the replay share. It scores more: it predicts
  stasis on the held-out half and is *right* wherever the world does nothing. The
  expectation is now derived from the paper item by item, which pins the
  interaction of the two behaviours rather than just the split -- a drifting
  quota would move that number and nothing else would notice.
* **`t2-gravity-push` has a residual tag bias, and it is published rather than
  argued away.** My first test asserted that both splits change the frame equally
  often; matched rule mixes make the splits equivalent *by rule* but not *by
  outcome*, because a cascading mechanism can fire the same rule and settle back
  to the same frame. The choices were to drop that world, widen until it passed,
  or measure it. `tag_bias` is now a column on the matrix, bounded at 0.25, and
  `t2-gravity-push` is the only world carrying any.

## 5 · What did not ship, and what each is waiting on

Three of the four question types. **None of the three is a matter of effort
inside `exam/`** -- each is blocked on an artefact that does not exist anywhere
in the repository, and two would have to be built in another track's territory.

| type | blocked on | whose territory |
|---|---|---|
| adaptation | a rule-mutation layer, claim-to-rule dependency edges, a mechanism-aware miner | `worldgen/`, `engine-rig/` |
| handover | a theory somebody authored for a generated world -- the factory makes worlds, not theories about them | upstream (a cold start) |
| verdict, class (ii) | worlds with >=10^12 configurations. The largest the factory ships is 2,654 states; the gap is nine orders of magnitude | `worldgen/` |

Full statements, including what *could* have shipped and why it did not:
[GAPS.md](GAPS.md). The short version of the verdict case, because that is the
one where a partial ship was tempting: classes (i) and (iii) are buildable today,
and shipping them under the name of a three-class question type is precisely the
misreport this question type exists to catch.

The smallest next step that unblocks the most is **`worldgen.mutate`** -- a
declared, enumerable set of semantic knobs per mechanism. It is the whole of
adaptation's first blocker and most of verdict's second.

## 6 · Verify

```bash
python -m pytest exam/tests -q          # 253 (158 inherited + 95 new)
python -m exam.tools.run_matrix         # the matrix, rebuilt
```

Zero network (the matrix runs inside `guard.no_network()`), zero model calls,
zero API calls, zero contact with either pile.
