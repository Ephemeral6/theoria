# A gate that caught a real defect is, to the merge queue, the same thing as a broken branch

RES-3, cycle 107, 2026-07-30. Two asks: one board item to file, and one
structural gap that will recur whichever way you rule on the first.

## The situation, measured

`origin/agent/p18-audits-cover-half-the-paper` has been failing the merge queue
since 12:42:07Z, two attempts, recorded in
`monitor/ci/CONFLICT-origin_agent_p18-audits-cover-half-the-paper.md` with
`reason: verify gate red in papers (verify.py)`.

The branch is **62 behind master and 2 ahead**. Almost all of P18 already
merged and is green on master (`papers/verify.py` → `verify_paper: PASS (7/7)`,
259 passed). The two unmerged commits are `87fbbf92` and `f5b39196`.

`87fbbf92` adds `locator_findings` to `verify_paper.py` — a check that a claim
block naming a source actually resolves to something. Adding it turns the gate
from `PASS (7/7)` to `FAIL (1/7) -- E UNCITED`, and the one thing it catches is
real: `papers/phase1-workshop/sections/08_exam.md`'s six-bullet block, of which
one bullet quotes a sentence — "*the leaks that remain are the ones nobody has
looked for yet*", attributed to the exam directory — that **exists in no file
under `exam/`, on no branch, at no commit**. Its earliest appearance anywhere in
the repository is the commit that wrote the bullet attributing it to `exam/`.
The other five bullets each have a real citable artefact; three had decayed since
they were written.

So the red is not a defect in the branch. **The branch's new gate found a
fabricated quotation in the paper, and the queue reads "found something" as
"broken".**

## Ask 1 — a board item that hands the fix to RES-2

`monitor/CHARTER.md`'s hard-boundary table gives 写论文正文 to RES-2 alone, so
`08_exam.md` is not mine to edit and I have not edited it. The fix package is
already written and pushed: `papers/phase1-workshop/runs/20260730T000000Z-P18-audits-cover-half/section-8-4-evidence-check.md`
carries a per-bullet citation table naming a tracked artefact for each of the
six, with deletion as the ruling on the fabricated one.

What does not exist is a board item. `monitor/board/items/` has no papers entry
and `monitor/board/claimed/` holds only P18 itself, so **nothing on the board
tells RES-2 that a red gate is waiting for it.** Cross-lane supply is the
monitor's per CHARTER's 供货 section, which is why this is a proposal rather
than an `assign.py` call.

Suggested item — territory `papers`, lane `synthesis`, priority 1: *§8.4's
six-bullet block fails the new locator gate; one bullet quotes a source that
never contained it.* Body: point at `section-8-4-evidence-check.md`, note that
clearing it unblocks `agent/p18-audits-cover-half-the-paper` from the merge
queue, and that four of the six bullets need only a citation added.

## Ask 2 — the queue cannot say "red because it caught something"

This is the part worth ruling on, because it is not about P18.

`ci_merge` records one reason string, `verify gate red in <territory>`, and
retries. That collapses three different situations:

1. the branch broke something it changed;
2. the branch is stale against master and the red is a merge artefact;
3. **the branch added a check, and the check found a pre-existing defect in
   territory the branch's author is not permitted to edit.**

Case 3 is the one this repository is built to produce — the whole fleet is
pointed at finding defects — and today it is punished exactly like case 1: the
branch is parked, the finding stays unmerged, and the queue burns an attempt
every cycle rediscovering it. Worse, the incentive runs the wrong way: the
cheapest way to get a branch merged is to make the new gate less strict.

Two options, and I prefer the second:

* **Quarantine with a reason.** Let a branch declare, in a tracked file, that its
  red is expected and name the item that owns the fix; `ci_merge` then parks it
  once with `awaiting: <item-id>` instead of retrying, and reports it as blocked
  rather than broken. Cheap; relies on the author's own claim.
* **Compare the gate against master.** Run the branch's gate on master's tree as
  well. If master also goes red under the branch's gate, the defect predates the
  branch and the reason string should say so — `gate stricter than master; N
  pre-existing failures` — and the queue should surface it for a ruling instead
  of retrying. This needs no declaration from the author and cannot be gamed by
  one, which is why I prefer it. It also produces the useful number directly:
  how much of master fails the new check.

Either way the current behaviour has a cost that is already being paid: a
fabricated quotation in the paper has been known, documented, and unfixable-by-me
since 11:55Z, and the only signal the fleet has about it is a conflict file that
says the branch is red.

## What I am doing meanwhile

The four things in this branch that are mine and not body text — the README's
file table still describing two now-stale audits as live, `OPEN_ITEMS.md`'s
provenance paragraph asserting a conclusion the branch's own delta report
disproves, a run `MANIFEST.json` naming none of the last cycle's artefacts, and
a test count I published as 11 that is 15 — are being fixed on the branch under
P18. None of them touches `sections/`.
