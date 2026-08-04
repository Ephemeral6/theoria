# V31 — running notes

Ticket: `monitor/board/items/V31-papers-gate-red-on-master.md`, claimed by W-9208.
Branch `agent/v31-papers-gate-red-on-master`, base `18e7d81b`.
Worktree `.worktrees/v31-papers-gate-red-on-master/`.

Written as the work happens. The disk is the memory.

## Baseline, measured 2026-08-04 on `18e7d81b`

`python papers/verify.py` → exit 1, `papers: RED (4 problem(s))`:

```
[1/3] FAIL case-studies: no PAPER.md, and not named in NOT_PAPERS
      FAIL related-work: no PAPER.md, and not named in NOT_PAPERS
[2/3] FAIL phase1-workshop/verify_paper.py exited 1
        verify_paper: FAIL (3/7) -- C FIGDATA, E UNCITED, F BARE
[3/3] FAIL pytest exited 1: 1 failed, 10 passed
```

Full captured output: `baseline-verify.txt`, `baseline-verify_paper.txt`.

Six red items, of which four are independent faults:

| # | red | independent fault? |
|---|---|---|
| 1 | `case-studies/` stray | yes |
| 2 | `related-work/` stray | yes |
| 3 | C FIGDATA | yes |
| 4 | E UNCITED @ `08_exam.md:154` | yes |
| 5 | F BARE, 24 ambiguous | yes |
| 6 | pytest 1 failed | **no** — symptom of 1/2 and 5 |

Item 6 is not a defect of its own. `papers/verify.py` stage 3 runs `pytest -q -x`;
the `-x` stops at the first failure, which is why it reports `1 failed, 10 passed`
rather than the true `2 failed, 272 passed, 1 xfailed`. The two failures are
`phase1-workshop/test_anchor_range.py::test_the_live_paper_is_green_and_its_anchors_are_in_range`
(calls `vp.check_bare()` in process — it *is* item 5) and
`test_verify_delegator.py::test_the_live_papers_tree_classifies_cleanly`
(calls `V.classify(HERE)` — it *is* items 1/2). Both pass for free once their
upstream causes go. Note also the docstring hypothesis that stage 3 collects only
the delegator's tests is false: 275 tests across 9 files are collected, including
`test_uncited_gate.py` (62) and `test_bare_gate.py` (20).

## Overlap check against the two blocked branches

Neither `origin/agent/v29-one-proxy-validated-not-two` nor
`origin/agent/v30-p18-hand-merge` fixes any of the six. Verified by blob identity:
`papers/verify.py`, `papers/test_verify_delegator.py`, `sections/{04_a1,08_exam,10_adjudication}.md`,
`figures/fig1_concept_timeline.{py,txt}`, `figures/data/fig1_concept_timeline.json`
are the same blob on master, v29 and v30.

* **v29** adds an eighth check `H DUALPROXY` (passes) and says so in its own commit
  message: *"None is fixed here and none is V29."* Its hunks in `verify_paper.py`
  are at 12–18, 148–153, 158–163, 165–170, 2189–2194 (443 lines inserted between
  `check_bare`'s `return` and the `CHECKS` comment) and 2207–2212 (`CHECKS`), plus
  `test_gate_floor.py:229-232`. **This work stays out of all of those spans.**
* **v30** touches zero bytes under `papers/` except a new `papers/runs/` directory;
  its seven conflicts all resolved to master's side and the merged tree is
  byte-identical to master.

So none of this is a redo, and the merge surface is disjoint.

## Plan, and why each fix is the honest one

1+2. **`case-studies/`, `related-work/` → `NOT_PAPERS`, each with a reason.**
   Not a judgement call for `related-work/`: its own `README.md:7` says *"This
   directory is **not** a paper. It is the evidence base a paper draws on"*, and
   `papers/phase1-workshop/references.bib` superseded it before the salvage commit
   `b8a7d6bc` that committed it. `case-studies/` is the judgement call and lands
   the same way: its `README.md:20-22` declares it ships "the numbers and the
   words, not the plots" for figures owned by `figures/`, and `README.md:40-47`
   says the 死锁定理集 half of the Phase 3 unit "is not here" but in `engine-rig`.
   Nothing in the tree cites it. Decisive practical point: `papers/verify.py:132`
   requires a paper to ship a gate, so a skeleton `PAPER.md` converts
   *"neither a paper nor declared provenance"* into *"ships no gate"* — it does not
   turn the gate green, it costs a whole gate implementation, and for
   `case-studies/` that gate would have to be green against a README whose own
   link checker (`check_citations.py`) is currently red on a dangling `runs/`.
   Registration form follows the house precedent at `monitor/gates.py:59-66`
   (`NOT_TERRITORIES`, whose one judgement-call entry carries a dated inline reason).

3. **C FIGDATA → regenerate the stale payload.** Not nondeterminism: three
   consecutive runs of `figures/fig1_concept_timeline.py` give identical bytes.
   The payload was last committed in `9bc27758` (2026-07-29); its only input,
   `cold-start-a0/THEORIZE_LOG.md`, gained the `E-10` expressivity-ledger row in
   `5ee845ee` (2026-08-01), which is not an ancestor. The whole structural diff is
   one added element, `expressivity_ledger[9] = {id: "E-10", ...}`. Honest to
   regenerate: no section, `PAPER.md`, `OUTLINE.md` or `PROVENANCE.md` cites this
   payload or `expressivity_ledger` at all, and the only expressivity count in the
   prose (`11_limitations.md:41-43`) is explicitly scoped to A0's five gaps E-01…E-05.

4. **E UNCITED → a dated, owner-attributed, expiring KNOWN-RED, not a ruling and
   not a prose edit.** See `E-UNCITED-RULING.md` in this directory for the full
   argument; the short form is that the only honest green is a paper-body repair
   that this worker is forbidden to make.

5. **F BARE → narrow the corpus walk to the published tree.** All 24 ambiguities
   are duplicates under one tracked prefix, `monitor/runs/_worktree-scratch-archive/`,
   added 2026-07-31 by `31de4964` / `8bf33ed2` — a committed copy of 328 removed
   agent worktrees. The paper's citations were last touched 2026-07-29 and did not
   regress; the tree grew a second copy of itself two days later. `verify_paper.py:1553-1555`
   already states this exact judgement for `.worktrees` — *"A basename that is
   'ambiguous' only because it also appears in a sibling worktree is not ambiguous
   to a reader of the repository"* — and `_WALK_SKIP` is a basename set that cannot
   express a path prefix, which is the only reason the archive slipped through.

6. Falls out of 1, 2, 5.
