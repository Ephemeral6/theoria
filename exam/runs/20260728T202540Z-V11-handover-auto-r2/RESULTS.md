# V11 — the layered handover, automated. What it measured, and what it did not.

Numbers: `RESULTS.json`. Blinding and residue: `BLINDING.md`. Frozen sheet, key
digest and prediction: `PREREGISTRATION.json`.

## The headline, stated the way it should be stated

**No conclusion about the value of the playbook.** Both tiers scored 1.000. The
delta is 0.000, and it is 0.000 because there was nowhere left to go, not
because the two tiers were measured and found equal.

| | tier 1 (manual) | tier 2 (manual + playbook) |
|---|---|---|
| readers | 3 | 3 |
| mean fraction | **1.000** | **1.000** |
| per-family delta | step 0.000 · names 0.000 · optimal 0.000 · why 0.000 | |

Every one of the six readers scored 58/58 — 31 items correct, none wrong, none
abstained, none unanswered.

The pre-registered saturation rule fired:

> if either tier scores above 0.95 overall the sheet has saturated again and the
> delta carries no information, whatever its sign.

That rule was written into `PREREGISTRATION.json` before the first reader ran,
which is the only reason it can be quoted now without it looking like an excuse
invented afterwards. `RESULTS.json` reports `saturated: true`,
`conclusive: false`.

## The error bars, and why they are not the reason for the null

Three instruments were measured, not assumed:

* **Grader noise** — every submission marked twice, and once more after every
  answer was cosmetically rewritten (case flipped, fields reordered, citations
  reversed, whitespace padded). Maximum movement: **0.0 points** on both probes.
  The marker contributes nothing to the spread.
* **Bootstrap over readers** (20 000 resamples, seed pinned): point 0.0, 95%
  interval **[0.0, 0.0]**.
* **Bootstrap over items** (20 000 resamples): point 0.0, interval
  **[0.0, 0.0]**.

Both intervals are degenerate because there is no variance anywhere to resample:
every reader gave a correct answer to every item. An interval of [0, 0] does not
exclude zero and `excludes_zero` is `false` for both. This is the V17 trap
avoided from the other side — there is no point estimate here to over-read.

## The instrument works. The examinees are above its ceiling.

It would be wrong to conclude the sheet is undiscriminating in general. Marked
against the same rubric, in the same run:

| fake examinee | fraction |
|---|---|
| oracle (answers from the key) | 1.000 |
| null (submits nothing) | 0.000 |
| memoriser (perfect on what the bundle states, nothing else) | 0.553 |
| bluffer (one confident answer per family, cites every clause) | 0.231 |

The sheet separates a reader from a memoriser by 45 points of fraction and from a
bluffer by 77. The citation family in particular punishes shotgunning exactly as
designed: the bluffer, which names every clause on every justification item,
scores under half of that family. What the sheet cannot do is separate one good
reader from another good reader, because on this world all six were good.

## What was actually learned

The tier question got no answer. A different question got a strong one.

**A fresh instance handed nothing but `a0-spike/theory/theory.dsl` and its
mechanical English rendering reproduced this world perfectly** — with no
repository, no history, no conversation, and one tool call each. That included:

* all five rules, on transitions covering every one of them, including two
  distinct ways a push fails and two distinct ways a move is blocked;
* exact shortest-plan lengths of 14, 16, 21, 22, 24 and 25 actions on boards up
  to 8×8, all six correct, from all six readers;
* both boards with no solution, including `cairn`, where every parity law the
  manual states *matches* and the board is dead for a geometric reason the
  manual never writes down;
* the citation family, including the one item whose support set is all five
  rules and the one whose set is two clauses and not one;
* a legal counterexample to `invariant box_row_parity … mod 2 = 1 [status:
  proven]` — the sentence the manual ships marked proven and which is false on
  most boards of its own world. Six readers, six valid refutations, on four
  different boards.

In 1.11's terms, 新读者打平作者 is satisfied and then some: the reader did not
merely draw level with the author, it correctly refuted the author's own
theorem. Whatever this manual's limits are, this sheet is not where they are.

**And the pre-registered prediction about where the delta would land is
untested, not confirmed.** The prediction said tier 2 should pull ahead on
`cairn` and nowhere else. Tier 1 got `cairn` right unaided, so the prediction's
premise — that the manual alone would struggle there — was simply false. That is
a finding about the prediction, and it is recorded as a miss rather than
reinterpreted as a hit.

## The most suspicious number in this run

Six readers independently returned the exact shortest-plan length on six search
problems of 14 to 25 actions. That is either genuine competence at a scale worth
noting, or a shortcut this paper did not anticipate, or a leak invisible from
here. It is the first thing the adversarial review was pointed at
(`ADVERSARIAL-BRIEF.md`, claim (a)) and its verdict is in
`ADVERSARIAL-VERBATIM.md`.

Every reader's `TOOLS:` self-report says a single `Read` of the one file it was
given. Six honest self-reports are evidence, not proof, and `BLINDING.md` §2
lists what a dishonest one could have reached.

## Residues found in this run and not repaired

1. **A structural tell in the optimal-action family.** The two dead boards are
   exactly the two levels that appear *once* in that family; the three solvable
   levels appear twice each. A reader looking for sheet structure rather than
   world structure could read deadness off item counts. The fix is a third
   occurrence of each dead level; it needs a new sheet and a new cohort.
2. **Board size correlates with the answer.** `stile` (6×7) and `cairn` (6×6)
   are the two smallest boards on the paper and the two dead ones.
3. **No cost instrument.** 1.11 predicts the manual-only reader draws level *and
   pays for it in search* — 多付的搜索成本 ≈ 玩法书缓存的计算量. `plan_len` shows
   the search was completed; it does not show what completing it cost. This is
   P-15's open weakness 2 and it is still open. It is now the *only* place a
   tier difference could show on this world, since accuracy has no room left.
4. **`abstain` is unpriced.** It scores zero like a wrong answer; nothing here
   distinguishes an honest reader from a reckless one by score.

## One change was made to code after the answers arrived

`bootstrap_over_items` crashed with `KeyError: 'tier2'` on first use — it
indexed the per-item table with the literals `"tier1"`/`"tier2"` instead of the
tier ids. It is a crash, not a threshold: the function could not produce a
number at all, so there was no number to tune. The rubric, the sheet, the key
and the prediction are untouched — `rubric_digest` is `63ce1eabcc32…` in
`PREREGISTRATION.json` and in `RESULTS.json` alike, and `score` refuses to mark
unless the re-derived key still hashes to `f21ee3d66ebc…`. The fix is in its own
commit, after the answers commit, where anyone can see it.

## What to do next, in order

1. Give the sheet a cost instrument, or stop expecting the handover item to test
   1.11's actual prediction. Accuracy on A0 is exhausted.
2. Run the same apparatus on a world where the manual is *known* to be
   incomplete — `worldgen` builds them — so that there is a gap for a playbook
   to fill. A ceiling test on a world nobody fails measures the world.
3. Fix the two structural tells above before either.
