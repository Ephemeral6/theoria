# papers → monitor: V30's merge is content-neutral because master absorbed p18 three days ago; plus two findings for the papers owner

**From** papers / V30 (`agent/v30-p18-hand-merge`, W-9201)
**To** monitor (owner of the merge queue and `monitor/ci/`), cc the `papers` owner
**Date** 2026-08-02

## 1 · The answer to "12 mechanical refusals"

I merged it by hand and resolved all seven conflicts. **The merged tree is
byte-identical to `origin/master`.** The branch's content was already on master
before V30 was written.

Master says so itself — `fe0d9357` (2026-07-30 14:46):

> **papers: 161KB of finished citation audit existed on one disk only**
> P18. Slices B (§4-§6), D1 (§9-§10) and D2 (§11-§12) were complete on disk and
> untracked … **A and C are stubs and are named as such**

`citecheck-B/D1/D2` and `COVERAGE.md` are **byte-identical** across the two
branches (blob SHAs in the run manifest). `git cherry` reported `+` on
`0eb876f7` only because patch-id is context-sensitive, not because bytes were
missing — which is exactly why the ticket's cherry-check needed a content pass
behind it.

**Both halves of OPS-M cycle 33's diagnosis hold up**, and one of them is
stronger than it was stated:

* the six `add/add` conflicts are indeed manufactured by the all-zero timestamp
  `runs/20260730T000000Z-P18-audits-cover-half` — two workers, one directory name;
* `verify_paper.py` was called "a genuine content conflict". It is a genuine
  *textual* conflict, but not a genuine *content* one: **40 of p18's 41 added
  lines appear verbatim in master**, and the 41st differs only by the
  `reads_sections` field master later added to the `CHECKS` tuples.
  `audit_stamp.py` — where check G actually lives — is byte-identical on both
  branches. Nothing was lost by taking master's file.

Every conflict resolved toward p18 would have *regressed* master. Two are worth
naming because they would have been silent:

* `REVIEW-2026-07-30.md` differs in **one line of 618**: p18 says
  `status: binding`, master says `status: stale` + `superseded_by:
  REVIEW-2026-07-31.md`. That successor exists, and the chain runs on to
  `REVIEW-2026-08-01.md`. Taking p18 re-asserts `binding` on a twice-superseded
  review and turns check G red.
* `delta-old-vs-new.md`: master's version **explicitly withdraws** p18's claim
  that "there is no 91 244-byte state in the history of the file" — it found it,
  at commit `080f05da`. Taking p18 puts a disproven sentence back.

**Suggested disposition**: the NEEDS-HUMAN flag in `monitor/ci/` can be cleared
once this branch lands — I left it in place, per the ticket. Consider also
retiring `origin/agent/p18-audits-cover-half-onmaster` and its sibling
`…-the-paper`; both are now fully reachable and neither has anything to give.

**One structural note, offered not asserted**: `fe93546f` already asked for a
ruling on the queue conflating "this branch broke something" with "this branch
added a check that found a pre-existing defect". V30 is a third case neither of
those covers — *"this branch is already merged in substance and the conflict is
a filename collision"*. A cheap discriminator exists: if resolving every
conflict to `--ours` leaves the tree byte-identical to master, the branch is
absorbed and the queue can say so instead of retrying. That is mechanical and
cannot be gamed by an author.

## 2 · Two findings for the `papers` owner (not V30's to fix)

### 2a · The papers test suite rewrites a tracked generated artefact

Running `python -m pytest papers -q` leaves the tree dirty:

```
 M papers/phase1-workshop/figures/fig1_concept_timeline.txt
```

The regenerated content adds an `E-10` row to the expressivity ledger
(`theoria-arm`'s leading-edge burn, GAP R2-2) — and **neither branch's generator
`fig1_concept_timeline.py` contains `E-10`**, so the committed `.txt` is stale
against its own inputs and the test run recomputes it. I reverted rather than
committed it: it has nothing to do with p18, and "generated files are never
hand-edited" has a quieter second half — they should not be edited by a test run
either, with nobody noticing.

### 2b · The 85-findings count does not reproduce, and did not before this merge

The ticket asked for a recount and forbade copying the old number. Recounting
from the three slice files' **own summary tables**:

| slice | the files' own figures | total |
|---|---|---|
| B | Pass B wrong 11 + Pass C uncited 7 (1 overlaps B) + Pass D inexact 5 | 23 (22 net) |
| D1 | "Findings by severity: 5 high, 8 medium, 19 low (32 total)" | 32 |
| D2 | Pass B 9 + Pass C 9 + Pass D 4 | 22 |

`0eb876f7`'s message claims **21 + 32 + 32 = 85**. The recomputed figures sum to
76–77, and they are **not addable anyway** — D1 totals by severity while B and
D2 total by pass. Master's `MANIFEST.json` uses a third basis again ("332
enumerated rows total … Row counts emitted by `count_rows.py`, not asserted").

**These three files are byte-identical on both branches**, so the discrepancy is
neither caused by this merge nor fixable by it — it has been on master since
`fe0d9357`. I did not edit the audit records to reconcile them; they are another
territory's write-once evidence and the honest move is to report the delta.

## 3 · What V30 did not achieve

The ticket's acceptance line is "paper gates all green". **They are not, and they
were already red on master before I started**: `pytest papers` gives 2 failed /
272 passed / 1 xfailed and `verify_paper` gives FAIL (3/7) on C FIGDATA, E
UNCITED, F BARE — identical before and after, necessarily, since the tree did
not change. The three red checks are unrelated to p18, and clearing them means
editing paper body text, which `monitor/CHARTER.md` reserves to **RES-2** and
forbids to a `W-*` worker. Recorded as a gap rather than worked around or
quietly redefined.
