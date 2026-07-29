# E8 — the third axis, one withdrawn headline, and half a paper sentence

**Verdict.** IC3's boundary is measured on all three axes the item named, and
the deliverable is `engine-rig/IC3_BOUNDS.md`, whose tables are injected from
these artefacts by `ic3bounds/document.py` (`--check` fails when they drift).
Three of the four things worth carrying out of this run are corrections to
claims the work itself was making:

* **Axis B (new).** At a state space held *exactly* fixed, IC3's cost moves by
  an order of magnitude with the boolean encoding, non-monotonically in
  predicate count — and the sharpest pair on it is not about vocabulary at all.
  peg `binary` and peg `native` are the **same predicates in reverse declaration
  order** over the same states, and differ by six to eight times.
* **Axis C's headline is withdrawn.** On five of its six rungs no edge leads
  into the bad set, so `¬bad` was already inductive and the sub-second timings
  are closure checks. It does not measure composition cost.
* **Axis A's ladder was re-walked densely.** It was every-other-rung plus one
  odd one; parity matters on this family, and the near-vacuity onset was being
  reported two rungs late.
* **The paper sentence half-survives.** LP infeasible on 10 of 10 with an
  algebraic witness; the null-space half refuted on 7 of 10.

```bash
cd engine-rig
python -m ic3bounds --out runs/<id> --axis size          # dense, ~12 min
python -m ic3bounds --out runs/<id> --axis predicates    # ~8 min, 26 rungs
python -m ic3bounds --out runs/<id> --axis compose       # ~2 s
python -m ic3bounds.verify runs/20260729T120000Z-E8-ic3-scale \
                           runs/20260729T120000Z-E8-ic3-scale/axis_size_dense
python -m ic3bounds.document --check
python -m pytest tests/ -k ic3bounds
```

---

## 1 · What was here when I claimed it

`agent/e8-ic3-scale` already carried commit `4260081f`: a previous session's
uncommitted work, committed verbatim and explicitly unreviewed. It had the axis A
and axis C harnesses and their results, and its own message named two gaps —
`IC3_BOUNDS.md` did not exist and the third axis had no module. It missed a
third: `ic3bounds/__main__.py` had `AXES = ("size",)`, so axis C was unreachable
from the documented entry point and the command in the docs ran a third of the
package.

**The audit of the salvaged work came back clean on soundness and dirty on
framing.** `ic3bounds/verify.py` re-parses every published `cnf_text`, rebuilds
the system from the row's own spec, and hands both to
`engines.ic3_pdr.check.verify` — the checker that shares no code with the
search. Every published invariant across axes A and C re-verifies, counts
matching exactly. Nothing measured had to be withdrawn. What had to be withdrawn
was what the numbers were said to mean.

## 2 · Axis B — the axis A could not have

On peg-N the predicate count and the state count are the same number, so axis A
cannot distinguish "IC3 pays for the state space" from "IC3 pays for the
vocabulary". `ic3bounds/reencode.py` re-encodes a system — same states, same
labelled edges, same init, same bad set, bijectively — into a different number of
booleans: `binary` (⌈log2 |S|⌉ index bits), `native`, `dual+k` (`free_pos3`
declared beside `pos3`), `onehot` (one predicate per state). Six blocks
(peg6/8/10/12 and two worldgen worlds), 26 rungs, 300 s each.

**The result that survived hardest scrutiny is a variable-ordering result.**
`peg_system` sorts its states as binary strings, so a state's index *is* its bit
string: peg `binary` and peg `native` are the same ten (or twelve) predicates in
opposite declaration order, over identical states, and they differ by a factor of
six to eight. Everything that could confound it is pinned by construction and by
a gate.

Alongside it: cost is not monotone in predicate count on any peg block (`dual+5`
declares 50 % more predicates than `native` and runs faster; `onehot`, at a
hundred times the predicates, also runs faster), and on the peg blocks the
cheaper certificate is also the *tighter* one.

**`onehot` is where a real trade appears.** It converges on exactly the reachable
set — `abstraction = 1.0`, verified against an independent BFS — which satisfies
all three Lean conditions and explains nothing. Its predicates genuinely name
state ordinals; its certificate genuinely has no world form.

## 3 · The recheck column on a second axis, and the correction inside it

Axis C reports `not available` honestly, because nobody has written an
independent worldgen transcriber. Axis B does not have to: a `dual` certificate
has an exact native form (`free_pos3` *is* `!pos3`), so `reencode.desugar`
rewrites it literal for literal and hands it to `recheck/`.

**Then a reviewer refuted the column.** It was deciding "does this certificate
have a native form?" from the *scheme's name* — and `binary` on peg is the
world's own vocabulary reversed, so four rungs were being reported as unreadable
when they were perfectly readable. `reencode.renaming_map` now decides it by
comparing every predicate against every state. The same measurement finds
`binary` on the worldgen worlds genuinely foreign (seven bits cannot rename
nineteen variables) and `onehot` foreign everywhere. Sixteen of twenty peg rungs
now recheck ACCEPT with both state counts agreeing; the four `onehot` rungs read
`n/a — no native form`, which is the item's third failure shape (*证书不可复核*)
actually occurring, recorded as a boundary and not as a defect.

The translation is not trusted either: `check.verify` re-counts the native form
on the native system, and a disagreement is a finding that fails the run — a
bijection cannot change a set's size.

## 4 · Axis C — the headline is withdrawn

An adversarial audit of the salvaged axis C found the thing its own metrics were
saying quietly. **On five of its six rungs no edge leads from outside the bad set
into it**, so `¬bad` is an inductive invariant unaided, the proof obligation is a
closure check, and the sub-second timings measure IC3 noticing that.
`strengthening = 1.0` had been reporting exactly this in a number whose failing
value looks neutral; five of six rungs read 1.0, five of six carry
`near_vacuous`, and the one rung that needed any strengthening is a *one-family*
world.

The artefact's own `separability` block adds the deeper reason: every invariant
on the ladder names the variables of at most one family, including in the two-
and three-family worlds. IC3 was never asked to reason across a composition.

Fixed in the axis rather than only in the prose: `property_already_inductive` and
`edges_into_bad` are now measured columns, `near_vacuous` is in the rendered
table (it was computed on every row and published on none), the `question` field
no longer says "held-fixed" for a ladder whose sizes span 49×, the `vacuity` note
that claimed high coverage was structural has been replaced with the real reason,
and `gate_results` no longer reports `passed: true` for a rung that never reached
the gate.

## 5 · Axis A — re-walked densely

The published ladder was `4, 6, 8, 10, 12, 13, 14`: every rung even but one.
Board parity matters here — odd boards give a systematically more vacuous
invariant at the same |S| — so the even ladder reported the near-vacuity onset
two rungs late and fitted its cost exponent through the confound. `LADDER` is now
contiguous, with a test pinning it contiguous and saying why.

With the missing rungs measured: the flag first fires at **n=11, |S| = 2048**;
the largest non-vacuous answer is **n=12, |S| = 4096**, half the headline; and
n=13's invariant excludes **fewer states in absolute terms** than n=12's, from a
state space twice the size. `axis_size.json` now carries a `vacuity` block that
consumes the flag — `boundary_of` counts a row as answered regardless of it, so
without this the two boundaries could not be told apart.

`n=14` was re-run at a **900-second** budget (`axis_size_budget900/`) and still
times out, so the boundary is not a marginal budget artefact.

Also corrected: the harness hard-coded *"max_levels=64 did not bind"* into every
timeout row's `detail`, which a killed child cannot know — it reports no frame.
All three axes now say what is knowable instead.

## 6 · The paper sentence

`Theoria.md:205` claims of IC3/PDR: *"LP/零空间够不着的形状由它兜"*.

**The LP half survives and is now evidence.** `lp_reach.json`: `lp_potential`
returns a certificate on none of ten unsolvable peg rungs, n = 4…13. Not merely
"the solver said infeasible" — an algebraic witness in three steps, whose premise
(that both directions of every triple are rows of the LP the engine builds) the
artefact machine-checks on all ten rungs. The inequality chain itself is hand
algebra and is *not* machine-verified, which the document says in the same
paragraph that quotes Theoria constraint 6. Same verdict at `bound` 10, 100 and
10000 and with the box deleted; positive controls return certificates.

**The null-space half does not survive.** GF(2) conservation laws separate the
initial state from the goal on **seven of the ten** rungs — five of axis A's six.
n=8 is the only rung of the six where IC3 is the only one of the three methods
that gets there. At n=4 the law GF(2) produces renders as *positions 1 and 2
always agree*: the M9 invariant, character for character, the anchor the whole
ladder is pinned to. One linear elimination away.

Qualified twice, both prominently: this is the *method*, not `zero_space` as
shipped (which consumes a trajectory, takes no goal, returns no unreachability
verdict), and it is *linear* pagodas only on the LP side. The first is a finding
about `zero_space`, not an exoneration.

`monitor/inbox/20260729T133000Z-W-1660-e8-ic3-bounds-touches-a-paper-sentence.md`
hands this to whoever owns the paper. I did not touch `papers/`.

## 7 · What the adversarial passes changed

Four reviewers, all instructed to refute rather than confirm. What they moved:

**On `reencode.py`** — the claim "the verdict IC3 returns is invariant" under
re-encoding was false as stated (convergence depth varies with the vocabulary, so
a tight `max_levels` can make a rung report `level-cap` for an alphabet reason);
`recoding_mismatches` ran five of seven checks through the same `encode`
`reencode` had just used, and now reads every code back through a separately
written inverse, with the *bound* on that independence stated rather than glossed;
`tautologies_dropped` is structurally zero for this engine's output, so its
zeroes are evidence of nothing and both the docstring and the gap list say so.
Also: `encoding_slack`'s stated rationale was false; `ceil(log2 n)` replaced by
`(n-1).bit_length()` behind a shared `floor_width`; a stray edge is named instead
of raising a bare `KeyError` that would blame the engine; `desugar_literal`
refuses an out-of-range index instead of wrapping; and `recheck_for` now applies
the three round-trip guards `recheck_column.clauses_of` documents as load-bearing.

**On the salvaged axes** — everything in §4 and §5 above.

**On `IC3_BOUNDS.md` itself** — a reviewer checked every number in the prose
against the artefacts and found eleven wrong, including all six spreads in a
hand-typed summary table sitting in a document whose opening line said the tables
were generated. That table is now generated. The document also now follows a rule
that prevents the class of error rather than the instance: **prose quotes only
deterministic numbers; every timing lives in a generated table and is referred
to, never retyped.**

**And `ic3bounds.verify` caught one itself** the day it was written: the first
axis B artefact carried a `derived.n_states` column the code had stopped
producing. That run was discarded and redone.

## 8 · Gaps, stated

1. **The peg ladder scales |S|, not difficulty.** Reachable sets are 2–7 states;
   "can `0111…1` reach `0100…0`" is a seven-node BFS. IC3 spends minutes on it at
   n=13. The axis measures cost against state-space size, which is what was
   asked, and says nothing about deep instances.
2. **Axis C has no rung where composition bites.** `worldgen` documents
   `t2-lock-fragile` as outside the current engine vocabulary; a ladder built
   around rungs like that would measure what this one was supposed to.
3. **Every timing is a single sample.** The peg orderings rest on factors of six
   and up and survive that; the two worldgen blocks' orderings are
   sub-millisecond and are not relied on.
4. **No worldgen rung has an independent recheck**, on either axis. Four axis B
   rungs are a real boundary; six are a missing transcriber.
5. **`ENGINE_TABLE.md`'s `ic3_pdr` row is stale and not reachable from here** —
   it says there is no state-space ladder, no predicate-count ladder, no timeout
   and no failure-shape census, and names E8 as the open item. All four now
   exist. Neither the file nor `tools/engine_table.py` exists at this branch's
   base (`a4d2ef2b`); both landed on `master` afterwards, so the fix belongs to a
   follow-up starting from master that adds `FACTS` probes over
   `axis_predicates.json` and `lp_reach.json`.
6. **`--check` guards the marked tables, not the prose.** Nothing can guard the
   prose; two authored tables remain, both labelled as authored.
7. **One machine, and for part of the final pass a contended one.** Another
   session on this host ran `exam.verify` and `exam.tools.run_selftest`
   concurrently with part of the axis B measurement — observed in the process
   table, not inferred. Absolute timings are inflated by an unknown amount. The
   findings rest on orderings *within* a block (whose rungs run sequentially
   under the same conditions) and on factors of six and up, which a uniform
   slowdown does not reverse; it could reverse a sub-millisecond margin, which
   is what the two worldgen blocks have and why they are not relied on. The n=14
   boundary was re-run at 900 s rather than argued about for the same reason.
