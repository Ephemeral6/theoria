# P23 — the paper claimed the probe beat closes the gap, and today's measurement says it does not

Territory: `papers/` (phase1-workshop). Everything outside it was read, never
written. Offline throughout: no ARC action, no model call, no network, no spend.
Development-pile legs only (`g50t-5849a774`, `sk48-d8078629`); zero sealed-pile
contact.

## The ticket, and what checking it first changed

The brief said: check before writing, because the paper may be carrying a claim
that today's measurement contradicts. It is. `PAPER.md`'s §2.3 offered the probe
beat as the answer to the paper's own title — *neither layer certifies the manual
against the world, that is what `probe` is for* — and §12 claimed the work adds a
use for a version space's width. Both describe a mechanism, and the mechanism was
measured against live play for the first time on 2026-08-01:

* the frontier being split is built by **ablation** — the manual, an inert
  reading, one without-rule-N variant per schema — a family closed downward under
  clause deletion, so it cannot contain a mechanism the manual lacks;
* **width 2 on every one of 52** completed probes, **47 of the 52** observations
  matching nothing in it, **0.000 bits** realised on all 56 designed, **0**
  monotone frontier shrinks;
* and the engine `Theoria.md` assigns to supply 全体一致假设的前沿 refused **48
  of 48** dispatches across every live leg that carries an engine record.

So the claim was not qualified because it was risky. It was qualified because it
is false as written, and the paper's own precedent for that is one day old: the
four-forms claim was dated and qualified on 2026-07-31 in exactly this shape.

## What was built

* `census.py` / `census.json` — a **papers-territory recount** of every live-leg
  number the edit puts in the body, from `git ls-files`-tracked files only. It
  exists because the arm's own measurement reads a gitignored frame trace, so a
  reader of this repository cannot re-run it and the paper's binding rule
  promises they can. Six quantities recomputed, **six AGREES, zero DIFFERS**.
  What it cannot see it records as `unmeasurable_here`, and a leg with no file is
  `absent`, never 0 — the anchor-drift decomposition and the virgin-cell counts
  are both recorded as unmeasurable rather than reported as zero.
* Section edits at eight sites: the abstract, §1.5's closing note, §2.2, §2.3,
  new **§11.3a** and **§11.4a**, §11.5's closing note, and §12.
* `CITECHECK-2026-08-01.md` and `REVIEW-2026-08-01.md`, delta audits with binding
  stamps; the two 2026-07-31 stamps flipped to `stale` naming them.
* `PROVENANCE.md` gained 12 rows; `README.md`'s audit table was corrected and now
  tells the reader not to trust it, because it had been wrong for a day.

## The four findings the paper now carries beside the big one

Each with its own path, in §11.4a and §11.3a:

1. **the curves defect** — every gate-tripped leg understated its own bill,
   $1.63 of $9.56 and $1.68 of $13.44, which is 12–17 % of the money, invisible
   to the arm's self-check because the vanished turn issued no ARC command;
2. **the anchor drift** — 35 of the 47 misses were probes designed from a state
   the world had already left, which reclassifies the failure out of 戳探设计差
   entirely;
3. **U3's name-keying defect** — a frozen primary endpoint deciding its criterion
   by matching theorem *names*, repaired to read what a theorem proves;
4. **the battery's E2 ruling** — 38 of 38 is one finding stated 38 times, because
   the attacker was the record's author, which demotes an interpretation without
   moving a number.

Plus the flat statement that **zero levels have been completed** — 0 rows across
ten tracked live legs, `levels_completed: 0` on every leg of both rounds.

## What was deliberately not claimed

The repair to the frontier is stated four times as default-off, byte-identical on
the old path, replayed rather than forecast, and **never run live**. The `gen_pddl`
repair keeps its 103 declared refusals of 299 in §11.3 unchanged. Nothing here
says an improvement was measured on a game, because nothing has been.

## Gates

Baseline and after are byte-identical in their finding counts:

```
before   papers pytest: 2 failed, 272 passed, 1 xfailed
         verify_paper: FAIL (2/7) -- E UNCITED (1 uncited), F BARE (24 ambiguous)
after    papers pytest: 2 failed, 272 passed, 1 xfailed
         verify_paper: FAIL (2/7) -- E UNCITED (1 uncited), F BARE (24 ambiguous)
```

The two pytest failures and the two red checks are pre-existing on clean
`master` in a fresh worktree and were reproduced there before anything was
edited. F BARE went 24 → 26 → 24 during the work: the first draft introduced two
bare filenames, and both were rewritten rather than ruled, because a ruling is an
exemption and a rewrite is a fix.

## Residual, stated not closed

* The two most persuasive numbers in the edit — the 35/12/0 decomposition and
  the 43-of-52 replay — are **read** from another territory's manifest and cannot
  be recomputed from this repository. `CITECHECK-2026-08-01.md` grades every
  claim recomputed / read / derived for this reason; the disclosure does not make
  them checkable.
* §1.5 item 1 and §7 keep the old framing of the battery's 37-of-38, which §11.4a
  now demotes. Left standing deliberately: rewriting §7 is a re-audit of a
  chapter this delta did not open.
* No independent adversary reviewed this delta.
* Two of the ten live legs carry no engine record at all, so the 48-of-48 refusal
  is over eight legs and the paper says eight, not ten.
