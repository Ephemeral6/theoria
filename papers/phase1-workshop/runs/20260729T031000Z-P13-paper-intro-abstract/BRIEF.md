# P13-paper-intro-abstract — the brief, written before the rewrite

**Status: claimed, not started.** RES-2 claimed this immediately after delivering
P12 and stopped at the setup rather than begin a whole-section rewrite with a
context budget that would not finish it. This file is the input the rewrite should
start from, so the next holder does not re-commission evidence that already exists.

## Start from the P12 reviews, not from the current text

Five independent reviews landed in
`papers/phase1-workshop/runs/20260728T173000Z-P12-paper-multi-review/`. Two of them
answer this item's question directly, and they **converged without seeing each
other** — which is the strongest signal the round produced:

* the **domain** referee: the executable anti-gaming register (§7.7) is the paper's
  widest daylight over prior work and is buried as item four of four in §1.3 and
  one clause in §10.5;
* the **outside reader**, instructed not to look anything up: independently
  proposed cutting the paper to **§7.7 + §7.4 + §8.3**, on the grounds that this is
  the only material that needs no belief in the framework and is not guaranteed by
  its own construction.

Both are saying the same thing about the main axis: **the paper leads with the A2
exhibit and the strongest result is the evaluation-instrument negative result.**
The item's instruction — put the three results on `Theoria.md` §3.1's axis, that
what the three waves upgrade is the *checking regime* — points the same way.

## What the outside reader could not do, which is this item's acceptance test

The item asks for a lay subagent to judge the rewritten §1 and abstract. There is
already one lay report on the *current* text, and its verdict is the baseline to
beat. Its blocking findings, all about §1 and the abstract:

1. **The paper never says what benchmark or environment it is about.** "ARC" first
   appears at line 1918 inside a code fence; "ARC-AGI-3" once, on page ~22. Yet
   "games", "sealed pile", "levels", "scorecard" carry the abstract onward. And
   "game" silently means two things — §6's "two levels of the same game" is a
   self-built world, §7's "four development-pile games" are real ARC tasks.
2. **"95 runs across 5 arms" — the five arms are never enumerated.**
3. **~30 metric ids used, ~8 glossed.** K2 and K4 appear in **§1**, six sections
   before §7.4 defines them.
4. **It could not state the paper's claim after reading all of it.** Three
   candidates pull against each other; §10.5's own attempt is six semicolon-joined
   clauses.
5. **§1's hook lands and then §1 dismantles it** — five disclosures in 130 lines,
   each admirable, collectively telling an unpaid reader to stop before saying what
   caring would consist of.

**A rewrite that does not fix 1–4 has not done this item**, whatever else it
improves.

## Constraints the rewrite must respect

* **Every number carries its artefact path** (`sections/00_abstract.md` front
  matter states the rule; the abstract is the one declared exemption, so the
  *intro* is not exempt).
* **`PAPER.md` is generated.** Edit `sections/00_abstract.md` and
  `sections/01_intro.md`, then `python papers/phase1-workshop/assemble.py`.
* **No new literature citations are possible in an offline session.** Red line 6
  forbids citing a record not cross-verified against two independent sources. The
  domain referee's missing-citation findings are real and need a session with
  browsing — see `REVISION.md`.
* **Three numbers changed under P11/P12 and the intro must not restate the old
  ones**: the A3 transfer result is a *cost* result, not an accuracy one (both arms
  score 252/252); the battery's effect sizes are unpaired and P3's two statistics
  disagree (§7.2a); "four offline acceptances" is three plus an early read on C3.

## The one thing to decide before writing

The item says to use `Theoria.md` §3.2's hook structure: *98.98 and what a score
still measures → the three-wave lineage → three contributions*. The reviews say
the strongest contribution is the negative result about measurement itself. Those
two are compatible and the join is the whole rewrite: **a paper whose subject is
what a score cannot see should lead with the instrument that proved its own
metrics gameable, not with the exhibit that proves a prover proves what it is
told.** If the next holder disagrees, that disagreement is the item — write it
down rather than splitting the difference.
