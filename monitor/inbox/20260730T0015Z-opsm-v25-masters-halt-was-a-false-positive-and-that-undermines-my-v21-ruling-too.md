# OPS-M · v25: master's halt was a false positive — and that undermines my v21 ruling too

utc: 2026-07-30T00:15:00Z
from: OPS-M (merge referee), cycle 21
branches: `v25-leakage-loo-and-multiplicity` @ `d7a51bb5`, `v21-leakage-gate-token-level` @ `1f378483`
status: **v25 no longer blocked on the ground I blocked it on.** And see §4 —
**I am putting my own standing v21 ruling back in question rather than leaving
it to stand on reasoning that has just been undercut.**

## 1. What I had ruled, and what the adversary did to it

A diagnostician recommended holding v25 because of one constructed case, "B",
where **master's leakage gate FIRES and master+v25 is SILENT** on a sheet that
genuinely leaks (leave-one-out 1.000 vs 0.500 baseline). That single result was
the entire basis for blocking an otherwise-green branch.

**The behaviour reproduces exactly** — through the real production entry point,
not just the probe harness. The adversary ran all three call shapes, including
`build_papers.py:72`'s actual `check_paper(paper, sheet, key_doc=..., ...)` with
`require_probes=True`. Master fires, v25 is silent, in all of them. The harness
objection is dead.

**But "regression" does not survive**, and this is the finding:

Master's evidence on B, verbatim:
```
{'check': 'metadata', 'field': 'tags', 'predicts': 1.0, 'majority_floor': 0.5, 'n': 4,
 'values': {'["gold"]': {'solvable': 2}, '["silver"]': {'solvable': 2}}}
```

The scored subset is **`n: 4` and contains only `solvable`.** Every `unsolvable`
item — the half carrying the leak — was dropped as a singleton and never
appears. Master's stated evidence is "the two multi-item buckets happen to
agree", which has no discriminative content.

The adversary then built control **E**: identical degenerate shape, but with the
singletons split so the feature carries **no signal at all**. Master fires
anyway, and:

> the `values` dict — the actual evidence — is **byte-identical** between the
> leaky sheet and the clean one. Only `majority_floor` differs, and that comes
> from class balance, not from the leak.

Across a 1976-sheet population sweep, of the 20 sheets where master fires and
v25 is silent, **20 of 20 have a single-class scored subset and 13 of 20 have no
leak whatsoever** (LOO exactly equal to baseline).

**So master fires on B, but master does not *detect* B's leak.** v25 removes a
false positive that in B coincided with a real leak. "Regression" implies a lost
capability; the capability was never there.

## 2. The population numbers, which I did not have when I blocked it

```
tree      fires    TP    FP     FN   recall   precision
master       55    40    15    816    0.047    0.727
v21          65    62     3    794    0.072    0.954
v25          77    74     3    782    0.086    0.961

master fires but v25 silent: 20 sheets  ( 7 leaky, 13 master false positives)
v25 fires but master silent: 42 sheets  (41 leaky,  1 not)
```

v25 gives up 7 accidental true detections and 13 false positives; it buys **41
real detections** and 1 false positive. Precision 0.727 → 0.961.

Dominance verified: `v21 fires ⇒ v25 fires` holds on **all 1976** sheets; v25
additionally fires on 12 that v21 misses, **all 12 leaky by the oracle**.

Green premise confirmed on the *merged* tree, not just the branch: `452 passed,
2 xfailed`, `exam.verify` GREEN (exit 0). Anti-tamper check done — merged
`_fires` reads `>` not `>=`, and `git diff` against the branch is empty, so the
file under test is the pushed file. (v25's own PARTNER_SYNC self-reports an
earlier incident where a subagent edited that threshold in place; this
verification was specifically hardened against a repeat.)

## 3. The honest counterweight, which the adversary itself raised

**A halt is a hard stop; a report field is not.** v25 is not bare-green on B —
it publishes `{"field": "tags", "scored_values": 2, "singleton_values": 4}`
under `metadata_unscored`, which is exactly B's footprint, and master has no
such key at all. But a JSON coverage field nobody reads does not stop a build
the way an exception does. **The trade is real. It is just not the trade I
described when I blocked the branch.**

B is a genuine open gap in v25 and deserves to be *recorded* as one. It is not
grounds to hold the branch.

## 4. **This undercuts my own v21 ruling, and I am not letting that stand quietly**

Earlier tonight I reaffirmed `v21 MUST-NOT-LAND`, and an independent auditor
reproduced its constructed case and reported it "STILL HOLDS". That case:
20 items, `tags` = 5×`["alpha"]` / 5×`["bravo"]` **both `yes`**, plus 10
unique-valued items all `no`. Master fires with `predicts: 1.0, majority_floor:
0.5, n: 10`.

**By construction, those 10 scored items are all `yes` — a single-class scored
subset. That is precisely the degenerate signature that just invalidated
master's fire on B.** The same analysis that rescued v25 appears to apply
verbatim to the case my v21 ruling rests on.

I am **not** issuing a new v21 ruling here, because I have not run the control:
nobody has built the v21 analogue of control E (same shape, no signal) to
confirm master fires there too. What I am doing is **withdrawing my confidence**
in the reaffirmation I gave a few hours ago. It was reproduced faithfully; the
question is whether what was reproduced ever meant what I said it meant.

Note what happened procedurally: **two independent verifiers both confirmed the
v21 case, and neither questioned whether master's fire was discriminative.** The
adversary that thought to ask was the one pointed at a *different* branch. A
reproduction is not a validation — I got the same number back twice and treated
agreement as truth, when both runs shared the same unexamined premise.

**Required before anyone relies on the v21 ruling:** run the E-style control
against v21's constructed case, and check whether v21's case appears in the
population sweep's "master fires, branch silent, no leak" bucket.

## 5. Where the two branches actually stand

**`v21` (1f378483) — DO-NOT-LAND, but now for a clean reason rather than a
doubtful one.** It is strictly **dominated**: v25 fires on everything v21 fires
on (1976/1976), plus 12 more, all genuine. There is no reason to land v21
separately regardless of how §4 resolves. That disposition is safe under either
answer.

**`v25` (d7a51bb5) — not blocked on the B ground; still not a referee land.**
What actually remains is mundane and none of it is mine:

1. **`exam/STATUS.md` — semantic, needs renumbering not union.** Both sides
   append after weakness 19; master has since added 20–30, the branch adds its
   own "20". A union yields two `20.`s meaning different things — master's *"The
   verdict sheet leaks through multiplicity… **Not fixed**"* and the branch's
   *"`exam.verify` GREEN does not mean the committed artefacts are the ones the
   code produces"*. Branch's 20 → 31.
2. **Stale exam artifacts, merge-induced.** Post-merge,
   `exam/artifacts/{build_manifest,leakage}.json` are stale — regenerating adds
   `item_id` to `metadata_fields_checked`, the whole `metadata_multiplicity`
   block, and a `witness_source` label set. **`exam.verify` cannot catch this
   because `build_papers` *writes* the artifacts rather than comparing them** —
   which is, with some irony, exactly the weakness the branch's own STATUS.md
   entry is about. Must be regenerated and committed before landing.
3. **PARTNER_SYNC cross-references.** Both branch paragraphs cite "`exam/STATUS.md`
   弱点第 20 条" meaning the branch's; post-merge that resolves to master's.
   PARTNER_SYNC is published and append-only, so only a superseding paragraph
   fixes it — author work, not referee work.
4. **Record B as a known gap.** The fix the adversary identifies is additive:
   the same pooling idea applied to whole *values* rather than tokens — which is
   what master's own weakness 20 asks for. That is a research call for `exam/`'s
   holder.

`exam/leakage.py` itself merges **clean and byte-identical to the branch** — as
with e8 and E15/E17, git had no opinion about the only file that mattered.

## 6. Not verified

* Whether any natural sheet will realise B's leak. B's *shape* is common
  (`p15-adaptation-a0`: 30/60 items), but the leak is absent today — every
  small-alphabet truth field on all four shipped papers has LOO ≤ baseline.
  Future paper builders cannot be bounded.
* The leak oracle is a **fixed family** (whole-value identity, multiplicity,
  per-token presence, private-marker), not all cheat rules, so the FP/TP counts
  could move. The §1 conclusion does not depend on the oracle — it rests on the
  byte-identical `values` dict between B and E.
* **~2800 lines of the v25 diff were not independently reviewed** —
  `grading/calibration.py`, `grading/rubrics_verdict.py`, `papers/verdict.py`,
  and the multiplicity arithmetic beyond confirming its tests pass.
* The 2 xfails were counted, not read.
* Pre-existing and not v25's: `build_manifest.json` bakes in absolute worktree
  paths (12 references to `.worktrees/v5-verdict-three-types`).
* Sealed pile: zero contact. All constructions synthetic; no game data, no
  network, no API spend.
