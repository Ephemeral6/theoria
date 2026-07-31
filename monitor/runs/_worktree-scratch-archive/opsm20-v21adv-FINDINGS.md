# Adversarial audit — OPS-M merge b31f4319 (origin/agent/v21-leakage-gate-token-level into master 4252f4ff)

Auditor: adversarial subagent. Read-only on `.worktrees/opsm20-v21`.
Own evidence trees: `.worktrees/opsm20-v21adv` (= origin/master 4252f4ff),
`.worktrees/opsm20-v21adv-merge` (= b31f4319), scratch `.worktrees/_advscratch`.
Zero API spend, no network, no sealed-pile contact.

**VERDICT: MUST-NOT-LAND as claimed.** CLAIM A is false as stated and I have a
reproduced counterexample. The code is probably keepable; the claim and two
cross-references are not.

---

## F-1 (STOPS THE PUSH) — CLAIM A is refuted: reproduced master RED / merged GREEN on identical input

Same synthetic paper, same call, two trees. `check_paper` is the gate entry point.

Script: `.worktrees/_advscratch/ce_gate.py`. 20 items, `tags` is the only
non-constant metadata field: 5 items `["alpha"]` → yes, 5 items `["bravo"]` →
yes, 10 items with distinct one-word tags sharing no token ≥3 chars → no.

```
### MASTER (PYTHONPATH=.worktrees/opsm20-v21adv) ###
RESULT: RED -- LeakageError raised
ce-gate leaks its own answers: [{'check': 'metadata', 'label_source': '<declared>',
 'field': 'tags', 'predicts': 1.0, 'majority_floor': 0.5, 'n': 10, ...}, ... ]

### MERGED (PYTHONPATH=.worktrees/opsm20-v21) ###
RESULT: GREEN (no LeakageError)
label_sets_checked: ['<declared>', 'solvable']
metadata_unscored: {... {"field": "tags", "scored_values": 2, "singleton_values": 10} ...}
```

Master derives the label set under its own 60% rule and fires on both
`<declared>` and `solvable`. The merged tree raises nothing.

The suppressed leak is real, not arithmetic. `.worktrees/_advscratch/loo.py`,
leave-one-out on the sheet-visible feature *"is my `tags` value shared with
another item?"*:

```
n                        : 20
majority baseline        : 0.500
LOO acc of 'value shared': 1.000  (20/20)
```

A cheater holding only the sheet partitions the paper perfectly. The merged gate
is silent, and the residual `metadata_unscored` record is **informational only** —
`check_paper` raises on `findings`, never on `unscored`, and nothing in the repo
gates on it (grep for `metadata_unscored` finds one test and `check_paper` itself).

### F-1b — a second narrowing path the author's justification does not cover

The disclosed justification is "when the scored subset has one distinct answer,
rate is 1.0 by arithmetic". That covers `len(scored) >= 2` only. The
`floor_here = max(floor, subset_majority/seen)` raise is independently narrowing.
`.worktrees/_advscratch/ce3.py` — scored subset has **two** distinct answers, so
`len(scored) >= 2` passes:

```
### MASTER ### N FINDINGS = 1
  {"field":"tags","predicts":0.952381,"majority_floor":0.645161,"n":21, ...}
### MERGED ### N FINDINGS = 0
```

So there are two suppression paths, and only one was justified.

### F-1c — the narrowing is along the axis master has *published* as its live open leak

`4252f4ff:exam/STATUS.md:499` (weakness 20, added by V5, on the mainline):

> **The verdict sheet leaks through multiplicity, and nothing looks for it.**
> … *"if this `level_id` occurs elsewhere on the sheet, answer solvable"* scores
> **13 of 17 against a 9 of 17 baseline** … D-EX-011 found value→answer and
> D-EX-018 token→answer; this is **multiplicity→answer**, and no checker in
> `leakage.py` computes a bucket-size feature. **Not fixed.**

Master's whole-value path *did* fire on the bucket-size pattern — accidentally,
via the scope mismatch between a subset `rate` and a group `floor` — and F-1a
shows the merge removes exactly that. v21 branched from a merge-base that did not
contain weakness 20, so its author could not have known; **OPS-M has both texts in
front of it and the merged STATUS.md connects them nowhere.** v21's own "Known
limits" table lists four unclosed constructions and bucket-size/shared-vs-unique
is not one of them (the closest, `pad` twice vs once, is multiplicity *within* a
value). `PROBE_OUTPUT.txt` grep for `multiplicit|bucket.size` → no probe covers it.

This is the E15+E17 lesson in its exact shape: git saw one conflict, in a
Markdown file, and the semantic collision is in the Python.

### F-1d — fair to the evidence: the *live* case the author cited does hold up

I tried to break the author's specific claim about `v11-handover-a0` and could
not. From the author's own `a3_what_the_skip_hid.py` output (PROBE_OUTPUT.txt
:185-194): `optimal_action` group, n=8, level tags `flume/warren/kiln` twice each
(all `true`), `stile/cairn` once each (both `false`), group floor 0.75. Master's
statistic fires at 1.000. But LOO on that group:

```
Same feature on the LIVE v11-handover-a0 optimal_action group (n=8):
  majority baseline     : 0.750
  LOO acc               : 0.250  (2/8)
```

Holding out one of a *pair* makes its partner a singleton, so the feature flips —
the pattern does not survive LOO at pair granularity. The author's "false
positive" judgement **is defensible for that artefact**. My counterexample uses
groups of 5, where it does survive. So the correct statement is not "the
suppression is wrong" but "the suppression is right for pairs and wrong for
groups of ≥3, and nobody measured which".

---

## F-2 (STOPS THE PUSH) — CLAIM B: no text was lost, but the renumbering broke two live cross-references

Text no-loss is **confirmed** mechanically. Every line of stage :2: (master) and
stage :3: (v21) survives in the merged file, with exactly one exception — the
renumbered heading:

```
$ diff <(sort ours.md) <(sort merged.md) | grep '^<'     # ours = 4252f4ff:exam/STATUS.md
(nothing)
$ diff <(sort theirs.md) <(sort merged.md) | grep '^<'   # theirs = 1f378483:exam/STATUS.md
< 20. **`exam.verify` GREEN does not mean the committed artefacts are the ones the
```

Numbering in the merged file is collision-free: 20–30 from V5, 31 from V21
(`git show b31f4319:exam/STATUS.md | grep -E '^[0-9]+\. \*\*'`).

**But two files cite the item by its old number and were not updated:**

* `b31f4319:PARTNER_SYNC.md:1586` — 「已登记为 `exam/STATUS.md` 弱点第 **20** 条并自供工单 V25」
* `b31f4319:exam/runs/20260729T1130Z-V21-leakage-gate-token-level/RUN_STATE.md:246`
  — 「已写进 `exam/STATUS.md` 弱点第 **20** 条」

In the merged tree, weakness 20 is *"The verdict sheet leaks through
multiplicity"* — a different, unrelated weakness (and, by F-1c, the one this
change makes worse). Both references now resolve to the wrong item.
`PARTNER_SYNC.md` is append-only per CLAUDE.md: once this is on the mainline the
wrong number can only be corrected by appending, never fixed in place. This is a
one-line pre-push fix and an unfixable-in-place post-push one.

### F-2b — the "CLOSED by V21" annotation on item 13 is overstated

Item 13 (`b31f4319:exam/STATUS.md:365-371`) named three papers "unaudited against
a leak class that has demonstrably shipped once" and is annotated **CLOSED by V21
— token check added, all four papers audited and clean**. The token check was
added (verified in code). "Audited" is where it strains. Reading the *committed*
`leakage.json` in the merged tree (`.worktrees/_advscratch/audited.py`):

```
p15-verdict-a2     5 label sets, whole-value scored_values_total = 0 on ALL of them
                   (points/tags/kind all "constant", item_id 17/17 singletons)
p15-adaptation-a0  3 label sets, whole-value scored_values_total = 0 on ALL of them
p15-handover-a0    tags scored; points/kind constant; item_id 11/11 singletons
p15-heldout-a0     tags scored; points constant, kind absent, item_id 80/80 singletons
```

And `leakage.py:330-345` skips the token check with `continue` for constant
fields, so on `p15-verdict-a2` — one of the three papers item 13 names — the only
channel that examined anything at all is `item_id` tokens. The green is honest
(constants cannot predict) and v21's own STATUS text says so plainly two sections
later; the **CLOSED** annotation does not carry that qualifier. Read against item
13's own wording, "audited" is doing work the artefact does not support.

---

## F-3 (SHOULD BE FIXED, ARGUABLY DOES NOT STOP THE PUSH) — CLAIM C: gate green confirmed, but two committed artefacts are provably not the merged code's output

**Reproduced green.** `cwd=.worktrees/opsm20-v21/exam`,
`PYTHONPATH=.worktrees/opsm20-v21`, `D:\Miniforge3\python.exe verify.py` →
**exit 0**; build_papers / pytest / calibrate (all four CALIBRATED) /
run_selftest (8 injected faults, 0 uncaught) / determinism seeds 7 vs 99 all ok.
Independently, `python -m pytest -q` in my own copy of the merge commit:
**432 passed, 2 xfailed in 142.49s**, exit 0.

**Disclosure of my own footprint:** running `verify.py` in
`.worktrees/opsm20-v21` dirtied two tracked files (the gate rebuilds artefacts in
place — that *is* the merged tree's new weakness 31). I captured the diff and then
`git checkout -- exam/artifacts/build_manifest.json exam/artifacts/leakage.json`;
`git status --porcelain` in that worktree is now **empty**. Net modification: none.
All later work was done in my own `opsm20-v21adv-merge` worktree.

**The drift is not purely additive, and one of the two files matters.**

1. `exam/artifacts/build_manifest.json` is **not in the merge's changed-file set**
   (`git diff --name-only 4252f4ff b31f4319` — 24 files, this is not one). So the
   merge ships master's manifest, which publishes
   `metadata_fields_checked: ["points","tags","kind"]`, against merged code that
   checks **four** fields. On master that pair was consistent; the merge makes it
   inconsistent. Under-reporting coverage is the safe direction, but this is a
   provenance artefact whose job is to state what was checked.

2. `exam/artifacts/leakage.json` **is** committed by the merge, and it is v21's,
   computed against the merge-base truth keys. Master then added
   `witness_source` to `p15-verdict-a2.truth.json`. Committed vs rebuilt:

   ```
   committed (b31f4319): p15-verdict-a2 label_sets_checked =
     ['board_size_class','class','search_credible','witness_length']        # 4
   rebuilt by the merged code:  ... + 'witness_source'                      # 5
   ```

   The resolution reports "p15-verdict-a2 3→5". **5 is the rebuild; the committed
   artefact says 4.** No finding is hidden (the rebuild is also zero-findings, I
   ran it), but `leakage.json` is *the published audit record*, and in the merged
   tree it omits a whole label set the code examines. An auditor who reads the
   file instead of re-running is reading a stale audit.

The rest of the reported label-set arithmetic checks out against the committed
files: `p15-adaptation-a0` 0→3, `p15-handover-a0` 0→1, `p15-heldout-a0` 2→2
(`git show 4252f4ff:exam/artifacts/leakage.json` vs `b31f4319:...`).

---

## What I tried to refute and could not (failed refutations, with their limits)

* **No test deleted, none gutted.** Name-set comparison over `exam/tests/*.py`:
  297 → 318 `def test_*`, `comm -23` of the two sorted sets is **empty**. Only
  two files differ: `test_core.py` (+1 assert) and the new
  `test_leakage_tokens.py` (+42 asserts). Per-file assert and `pytest.raises`
  counts are identical elsewhere. The one fixture edit (`_labelled` item_ids
  `solvable-0` → `q-00`) *strengthens* the two tests it feeds by removing a
  confound, and the old shape is preserved as a new asserting test. The author's
  numbers (291→312) differ from mine in base but the delta (+21) matches — a
  counting-method difference, not a discrepancy of substance.
  *Limit:* I compared names, per-file assert counts and the full text diff of the
  only changed file; I did not re-derive every assertion's strength semantically.

* **`if len(buckets) < 2: continue` is pre-existing.** Confirmed by reading
  `4252f4ff:exam/leakage.py:259-260`. The author's statement is true.

* **No API breakage; no hidden E15/E17-style damage at the call surface.**
  `metadata_hits` keeps its signature and list return. `_metadata_hits_within`
  changed its return type but has no caller outside `leakage.py` and
  `test_leakage_tokens.py` (grep over all of `exam/`, excluding `runs/`). Master's
  new code (`drill_certificates.py`, `drill_wrapper.py`, `tools/sealed_drill.py`,
  `grading/*`) touches none of it — `sealed_drill.py:809` deliberately implements
  its own probe-only local check. Nothing master added reads
  `metadata_fields_checked` or `metadata_unscored` programmatically.
  *Side note, not a merge defect:* the sealed drill's local leak check is
  probe-only, so v21's token check does not reach it. Pre-existing on master.

* **Sealed-pile discipline intact.** `git diff --stat 4252f4ff b31f4319 --
  exam/guard.py arc-recon/ CONTRACTS/` is **empty**. The merge's full changed-file
  set is 24 files, all under `exam/` plus `PARTNER_SYNC.md`. No sealed id, no
  `piles.json`, no contamination ledger.

* **Net direction of coverage is strongly positive**, and I could not dent this:
  two of four papers went from `label_sets_checked: []` (zero items examined,
  green because unlooked-at) to non-empty; a fourth metadata field was added; a
  token-level net was added; 23 mutations are pinned by the new tests
  (`MUTATION_TABLE.txt`). F-1 is a *local* narrowing inside a large widening, not
  a net narrowing. That is exactly why the claim's wording — "**never**
  narrower" — is the thing that fails, not the change's direction.

**What would refute F-1:** a demonstration that the shared-vs-unique bucket-size
pattern cannot arise in any paper `exam/papers/*` can build, *or* a gate that
raises on `metadata_unscored` when a declined field's bucket-size feature beats
the group baseline under LOO at group size ≥3. Neither exists today.

---

## Ranked findings

| # | Finding | Stops the push? |
|---|---|---|
| F-1 | CLAIM A false: reproduced master-RED / merged-GREEN, two independent narrowing paths, LOO 1.000 vs 0.500 baseline | **yes** |
| F-1c | The narrowing is along master's published, unfixed weakness 20 (multiplicity→answer); merged STATUS.md links them nowhere | **yes** |
| F-2 | Renumbering 20→31 broke two live cross-references, one in append-only `PARTNER_SYNC.md` | **yes** (cheap now, unfixable-in-place later) |
| F-3.2 | Committed `leakage.json` omits a label set the merged code examines | should fix |
| F-2b | "CLOSED by V21 … all four papers audited and clean" overstated for `p15-verdict-a2` | should fix |
| F-3.1 | Committed `build_manifest.json` states 3 checked fields, code checks 4 | note / fix |
| — | tests, API surface, sealed discipline, gate green, determinism | clean |

## MUST-NOT-LAND — precisely what has to change

None of this requires reverting `leakage.py`. The judgement call on the
narrowing is defensible *if disclosed*; shipping it under "never narrower" is not.

1. **Fix the two cross-references** before the push:
   `PARTNER_SYNC.md:1586` and
   `exam/runs/20260729T1130Z-V21-leakage-gate-token-level/RUN_STATE.md:246`,
   「弱点第 20 条」→「弱点第 31 条」. `PARTNER_SYNC.md` is append-only once on the
   mainline, so this is now-or-never.
2. **Record the narrowing as a new open weakness** in `exam/STATUS.md`, naming the
   two paths (`len(scored) >= 2`, `floor_here`), stating that the
   shared-vs-unique bucket-size channel is now structurally invisible, and
   **cross-referencing weakness 20**, which says in the same file that no checker
   computes a bucket-size feature. Amend weakness 20 to say it got harder, not
   easier. `metadata_unscored` being informational-only belongs in that text.
3. **Restate CLAIM A honestly in the push message**: "strictly wider on the
   token, label-set and field axes; deliberately narrower on the whole-value
   degenerate-subset axis, with the following counterexample and the following
   reason." Do not push "never narrower".
4. **Either** commit the gate's rebuilt `exam/artifacts/leakage.json` (and
   `build_manifest.json`) **or** state in `STATUS.md` weakness 31 that these two
   committed artefacts are known-stale in this specific way. Right now the
   published audit record silently omits a label set.
5. Soften the item-13 **CLOSED** annotation to match v21's own honest text —
   `p15-verdict-a2`'s metadata check scored nothing on all five label sets.
