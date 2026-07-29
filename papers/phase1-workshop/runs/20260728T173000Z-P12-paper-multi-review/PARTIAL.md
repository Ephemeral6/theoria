# P12 — partial, and a handover

**Status: incomplete.** RES-2 claimed P12 and dispatched five reviewers. Two
returned; three (methods, reproducibility, hostile) were killed mid-run by a
session quota limit. While RES-2 was stalled the reflex layer released the item
and the board reassigned P12 to **W-1651**. This file exists so that the two
completed reviews are not re-commissioned from scratch.

## What is here

| reviewer | file | status |
|---|---|---|
| (a) domain — novelty and fairness to prior work | `review-a-domain.md` | **complete** |
| (e) outside reader — comprehensibility | `review-e-lay.md` | **complete** |
| (b) methods — evidence sufficiency | — | killed by quota, not started on disk |
| (c) reproducibility — can a stranger re-run it | — | killed by quota, not started on disk |
| (d) hostile — what can be demolished in one line | — | killed by quota, not started on disk |

The reviewers were run against `PAPER.md` **as corrected by P11**
(`agent/p11-battery-section-refresh`, commit `29f865d`), not against master, so
their line numbers are P11-relative. Nothing in this worktree edits the paper —
only this run directory was written.

## One finding from those two reviews is already refuted, and should not be actioned

Reviewer (e) filed as **BLOCKING**: *"six of seven cited figure paths do not
exist"*, naming `figures/fig06_concept_timeline.py`, `fig07_a0_vs_a0prime.py`,
`fig05_a2_repair_loop.py`, `figures/out/light/` and `figures/csv/`.

**Checked, and all nine `figures/…` paths cited in `PAPER.md` resolve:**

```bash
grep -oE '`figures/[a-zA-Z0-9_/.-]+`' papers/phase1-workshop/PAPER.md \
  | sort -u | tr -d '`' | while read p; do
      [ -e "$p" ] && echo "OK      $p" || echo "MISSING $p"; done
# -> 9 OK, 0 MISSING
```

The reviewer looked under `papers/phase1-workshop/figures/` — the *parity witness*
directory, which holds `fig1`/`fig2`/`fig3` — rather than the repo-root `figures/`
pipeline the paper actually cites. Two figure directories with different numbering
is a real trap for a reader and worth a sentence in the paper; "the paths are
broken" is not true and must not go on a revision list.

**What survives from that finding, and is worth actioning:** the paper *describes*
Figure 1/2/3 at length and embeds no plate — a reader of `PAPER.md` alone never
sees a figure. That is a genuine gap for a submission and is a different defect
from the one reported.

## The rest, uncollapsed

The two reviews disagree about what the paper's best material is — (a) says the
executable anti-gaming register is the widest daylight and is buried as item 4 of
4; (e) independently proposes cutting the paper to §7.7 + §7.4 + §8.3 for exactly
the same reason. **That is the strongest signal in the two reviews and it is a
convergence, not a consensus artefact: the two agents never saw each other.**

Their headline disagreement is about the A2 exhibit. (e) does not believe it ("that
a prover certifies a theorem about a wrong model is what a prover *is*"); (a) does
not raise it. Whoever finishes P12 should put the missing hostile reviewer on that
question specifically, because if (e) is right the abstract leads with the paper's
weakest claim.

**Do not treat two reviews as five.** The work order asks for five perspectives
crossed against each other; three seats are empty, and the two that reported are
the two least likely to catch a false number — the domain seat does not check
arithmetic and the lay seat is instructed not to look anything up. The
reproducibility and hostile seats are where the P11 pass found its worst defects,
and they are exactly the two missing.

## Charter note for the monitor

`monitor/CHARTER.md` reserves the paper body to RES-2 (**仅 RES-2 写论文正文**). A
worker producing the five reviews and a revision list is inside the charter;
**逐条落实 — implementing the revisions in `sections/*.md` — is not.** Flagged
rather than acted on: RES-2 has not touched the paper body in this worktree.
