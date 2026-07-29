# E8 — the third axis, and the sentence the three of them settle

**Verdict.** IC3's boundary is measured on all three axes the item named. The
one that changes what may be written is the one that did not exist before this
run: at a state space held *exactly* fixed, IC3's cost moves by 12–35× with the
boolean encoding alone, it is not monotone in predicate count, and on all six
held-fixed blocks the fastest encoding is one whose certificate contains no word
of the world's own vocabulary. The deliverable is `engine-rig/IC3_BOUNDS.md`;
its tables are injected from the artefacts by `ic3bounds/document.py` and
`--check` fails when they drift.

```bash
cd engine-rig
python -m ic3bounds --out runs/<id> --axis predicates      # ~8 min, 26 rungs
python -m ic3bounds.verify runs/20260728T203711Z-E8-ic3-bounds \
                           runs/20260729T120000Z-E8-ic3-scale
python -m ic3bounds.document --check
python -m pytest tests/test_ic3bounds_*.py
```

---

## 1 · What was here when I claimed it

`agent/e8-ic3-scale` already carried commit `4260081f`, a previous session's
uncommitted work committed verbatim and explicitly unreviewed. It contained the
axis A and axis C harnesses and their results, and its own commit message named
the two things it had not done: `IC3_BOUNDS.md` did not exist, and the third
axis had no module and no results file. It was also wrong about a third thing it
did not notice — `ic3bounds/__main__.py` had `AXES = ("size",)`, so axis C was
unreachable from the documented entry point and the command in the docs ran a
third of the package.

This run did not re-measure axes A and C. It audited them, added axis B, wired
the entry point, and wrote the document.

**The audit of the salvaged work came back clean on the thing that matters.**
`python -m ic3bounds.verify` re-parses every published `cnf_text`, rebuilds the
system from the row's own spec, and hands both to `engines.ic3_pdr.check.verify`
— the checker that shares no code with the search. All thirteen published
invariants across axes A and C re-verify, with clause counts, literal counts and
satisfying-state counts matching the rows exactly. Nothing in the salvaged
numbers had to be withdrawn.

## 2 · Axis B — what it is and why axis A needed it

On peg-N the predicate count and the state count are the same number. Axis A
therefore cannot distinguish "IC3 pays for the state space" from "IC3 pays for
the vocabulary": both fit its data perfectly.

`ic3bounds/reencode.py` re-encodes a system — same states, same labelled edges,
same initial state, same bad set, bijectively — into a different number of
booleans. Four schemes: `binary` (⌈log2 |S|⌉ bits of a state index), `native`,
`dual+k` (`free_pos3` declared beside `pos3`), `onehot` (one predicate per
state). Six blocks: peg6/8/10/12 and two worldgen worlds, 26 rungs, 300 s each.

Four findings, all in `IC3_BOUNDS.md` with their numbers:

1. Cost is **not monotone** in predicate count on any block. peg10 `dual+5`
   declares 50 % more predicates than `native` over the identical state space
   and runs 3.8× faster.
2. Nor is it determined by predicate count and state count *together*. peg10
   `binary` and peg10 `native` declare the same ten predicates over the same
   1024 states and differ by 6.4×. Only which ten booleans differs.
3. On six blocks of six, the fastest rung's certificate is in state-index
   vocabulary. The speed is bought with the certificate.
4. Padding degrades the certificate as well as the clock: peg6 `dual+3` returns
   a shorter, weaker invariant than `native` for two extra names for facts the
   world already had.

**`onehot` is the sharp end.** It converges on exactly the reachable set —
`abstraction = 1.0`, 3 states of 64, 6 of 4096 — which is a sound inductive
invariant satisfying all three Lean conditions and is also the engine doing
reachability under another name. That distinction is a first-class column
(`abstraction`) precisely so it cannot be read past.

## 3 · The recheck column on a second axis

Axis C reports `not available` for its recheck, honestly, because nobody has
written an independent transcriber for worldgen. If axis B had done the same,
two of three axes would carry no independent check and the item's third
requirement would be met on one axis only.

It does not have to. A `dual` certificate has an **exact native form**:
`free_pos3` is not a new fact, it is `!pos3` under a second name, so
`reencode.desugar` rewrites the clause set literal for literal into the world's
own vocabulary, and that form can be handed to `recheck/`. All twelve peg
`native`/`dual` rungs come back **ACCEPT with both state counts agreeing**. The
translation is not trusted: `check.verify` re-counts the native form on the
native system, and a disagreement is a finding that fails the run — a bijection
cannot change a set's size.

`binary` and `onehot` rungs read `n/a — no native form`. That is the item's
third failure shape (*证书不可复核*) actually occurring, and it is recorded as a
boundary rather than as a defect: the run does not exit 1 on it.

## 4 · Two adversarial passes, and what they changed

**On `reencode.py`.** A reviewer instructed to refute found thirteen things, and
three of them were real enough to change code or claims:

* The module claimed "the verdict IC3 returns is invariant" under re-encoding.
  False as stated: convergence depth varies with the vocabulary (frame 7 under
  `native`, frame 3 under `onehot`, on peg6), so a tight `max_levels` can make a
  rung report `level-cap` for a reason about the alphabet. The *answer* is
  invariant; the recorded verdict is not. The docstring now says so, and
  `IC3_BOUNDS.md` carries `converged_at_frame`. (`max_levels = 64` never binds
  here — deepest is frame 20 — but the caveat is not conditional on that.)
* `recoding_mismatches` ran five of its seven checks through `recoding.encode`,
  the same function `reencode` had just used, so it could only confirm that
  `encode` equals itself. Fixed: `Recoding.decode` is a separately written
  inverse that reads the declarations the other way round, and the gate now
  walks the recoded system and reads every code back through it. The bound on
  that independence is stated in the docstring rather than glossed — both
  directions read the same `definitions`.
* `tautologies_dropped` and the literal-dedup counters are **structurally zero**
  for this engine's output, because `pdr.generalise` collapses the duplicate
  pairs before `desugar` ever sees them. They are a guard against a different
  producer, not a measurement, and both the docstring and the document's gap
  list now say the zeroes are evidence of nothing.

Also fixed from that pass: `encoding_slack`'s stated rationale was false
(`onehot` slack is |S| minus a logarithm and is almost entirely world size);
`ceil(log2 n)` replaced by `(n-1).bit_length()`, with `binary_recoding` and
`encoding_slack` now sharing one `floor_width` so they cannot disagree; an edge
leaving the declared state set is named instead of surfacing as a bare
`KeyError` that would blame the engine; `desugar_literal` refuses an
out-of-range index instead of wrapping onto the last definition; and
`recheck_for` now applies the three round-trip guards `recheck_column.clauses_of`
documents as load-bearing, which it had been skipping.

**On the whole package.** `ic3bounds.verify` caught a real drift the moment it
was written: the first axis B artefact carried a `derived.n_states` column the
code had stopped producing. The run was thrown away and redone. That is the
check working, and it is why the artefact in this directory is not the first one
measured.

## 5 · The paper sentence

`Theoria.md:205` claims of IC3/PDR: *"LP/零空间够不着的形状由它兜"*. E8's own
wording is that there was one point, so no line could be drawn. There is now a
line, and it does not run where the sentence assumes.

**The LP half survives and is now evidence.** `lp_reach.json`: `lp_potential`
returns a certificate on **none** of ten unsolvable peg rungs, n = 4…13. Not
"the solver reported infeasible" — provably infeasible, by an argument the
artefact machine-checks the premises of: summing the two opposite jump rows over
each triple forces every interior weight non-negative, so Σw[i≥2] ≥ 0, while the
goal row demands Σw[i≥2] ≤ −margin < 0. Same verdict at `bound` 10, 100 and
10000 and with the box deleted; positive controls confirm the harness does
return certificates when they exist.

**The null-space half does not survive.** The GF(2) conservation laws of the
same family separate the initial state from the goal on **seven of the ten**
rungs — five of axis A's six. n=8 is the only rung on the ladder where IC3 is
the only one of the three methods that gets there. And at n=4 the law GF(2)
produces renders as *positions 1 and 2 always agree*: the M9 invariant,
character for character, the anchor the whole ladder is pinned to. One linear
elimination away.

Qualified twice in the document and both qualifications matter: this is the
*method*, not `zero_space` as shipped (which consumes a trajectory, takes no
goal and returns no unreachability verdict), and it is *linear* pagodas only on
the LP side. Neither rescues the sentence; the first is a finding about
`zero_space` rather than an exoneration.

`monitor/inbox/20260729T133000Z-W-1660-e8-ic3-bounds-touches-a-paper-sentence.md`
hands this to whoever owns the paper, with the recommendation to split the cell
into two claims. I did not touch `papers/`.

## 6 · Gaps, stated

1. **The ladder scales |S|, not difficulty.** The board starts full so the first
   jump is forced; the reachable set is 2 states at n=4 and 7 at n=13, inside
   state spaces of 16 and 8192. Axis A measures cost against state-space size,
   which is what was asked, and says nothing about deep instances. A second
   family whose reachable set grows with the board is the missing experiment.
2. **Axis C's rungs are too easy to bite.** Six worlds, all under a second, all
   with invariants admitting 85–98 % of their state spaces, and five of the six
   carrying the harness's own `near_vacuous` flag. "Composition costs nothing"
   is true only for invariants that weak.
3. **No worldgen rung has an independent recheck**, on either axis B or axis C.
   Fourteen of axis B's twenty-six rungs read `not available`; eight of those
   are a real boundary (a state-index certificate has no world form) and six are
   a missing transcriber.
4. **`ENGINE_TABLE.md`'s `ic3_pdr` row is now stale, and is not reachable from
   this branch** — it says there is no state-space ladder, no predicate-count
   ladder, no timeout and no failure-shape census, and names E8 as the open
   item. All four now exist. Neither the file nor its generator
   `tools/engine_table.py` exists at this branch's base (`a4d2ef2b`); both
   landed on `master` afterwards, so the fix belongs to a follow-up that starts
   from master and adds `FACTS` probes over `axis_predicates.json` and
   `lp_reach.json`. Flagged rather than left silent, and flagged rather than
   fixed by merging master into a measurement branch mid-run.
5. **`--check` guards the tables, not the prose.** Nothing can guard the prose.
   The document says so.
6. **One machine, one afternoon.** The axis B spreads survive that; an ordering
   that reverses under 12–35× is not noise. The absolute boundary at n=14 does
   not.
