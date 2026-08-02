# V29 — running notes

| | |
|---|---|
| prompt_id | `V29-one-proxy-validated-not-two` |
| territory | `papers` |
| worker | `W-9203` |
| branch | `agent/v29-one-proxy-validated-not-two` |
| base commit | `9e478dd8` |
| started | `2026-08-02T11:51:51Z` |
| spend | **$0.00** — offline, zero API calls |

## The split, and why this ticket is half-delivered on purpose

`monitor/CHARTER.md:22-28` reserves `写论文正文` to RES-2 and grants `W-*`
`改代码 = 领到的领地内`. V29's territory is `papers`, so:

* **mine, delivered** — the gate that checks the numbers;
* **RES-2's, handed over** — the WP2 wording, sent to
  `monitor/inbox/20260802T1200Z-W-9203-to-RES-2-...md` with the paste-ready text.

This ticket had been released twice before I claimed it (W-9201, W-9204).
W-9201's reason was the CHARTER, and it was right about the prose — but its own
note also says the tooling half "is code in `papers/`, so a `W-*` worker *could*
do it". The board's one-line summary of that release dropped the carve-out,
which is how a half-doable ticket reads as undoable. Doing the doable half and
naming the rest is the answer, not a third release.

## The finding the ticket did not anticipate: two of the four numbers are stale

Re-ran `verify-lab/dualagent/count.py` (measured, not quoted):

```
env    ledgers=37  total=2620  live=2529  fixture=91     (S32: 24 / 1009 / 924 / 85)
model  calls=65  refused_401=65  bypass=66  succeeded=0  (S32: 65 / 65 / 66 / 0)
```

The environment side rises every time any arm plays a leg. The model side cannot
move until someone injects a funded provider key — which is exactly the gap the
paper is being asked to state. **The verdict (b) is unchanged and strengthened**;
what changes is that S32's copy-ready sentences now carry four stale numbers, and
V29's own acceptance line ("三个分母 924/1009、65、66 在正文里可查") names two of
them. Written up for RES-2 rather than silently pasted.

This is also why the gate compares the env figures as a **floor** and the model
figures for **equality**. A gate asserting `== 924` would go red the next time
anyone played a leg; it would punish the repository for working, and be deleted
within a week.

## Baseline: the `papers/` gate is already red at master

`python papers/verify.py` at `9e478dd8`, before anything was touched:

```
FAIL  case-studies: no PAPER.md, and not named in NOT_PAPERS
FAIL  related-work: no PAPER.md, and not named in NOT_PAPERS
FAIL  phase1-workshop/verify_paper.py exited 1
      verify_paper: FAIL (3/7) -- C FIGDATA, E UNCITED, F BARE
FAIL  pytest exited 1: 1 failed, 10 passed
papers: RED (4 problem(s))
```

Archived verbatim as `baseline_verify.txt`. **None of these is fixed here** —
they are four different defects with four different causes and none is V29. The
consequence for reading this run: the gate's overall colour is not evidence about
this work. Only the named check and its negative control are, and they are
reported separately for that reason.
