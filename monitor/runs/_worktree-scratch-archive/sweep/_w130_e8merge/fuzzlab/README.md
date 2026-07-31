# fuzzlab — property testing for the six engines

500 randomly generated deterministic worlds per engine, ≥3 invariants each,
judged by oracles that recompute the answer instead of asking the engine.

```bash
python -m fuzzlab.verify                         # tests + smoke campaign + engine-rig's own suite
python -m fuzzlab.campaign                       # the standing 500-world campaign
python -m fuzzlab.campaign --engine zero_space --worlds 200
python -m fuzzlab.minimize --engine cegis_miner --invariant frontier_guards_are_consistent
python -m fuzzlab.minimize --replay 0x… --family gridworld --engine mdl_segmenter
```

Results: [`BUGS.md`](BUGS.md). Raw: `out/campaign.json`, `out/seeds.jsonl`,
`out/findings.jsonl`. Archived reproducers: `archive/`.

**`out/` is a snapshot from whichever item last ran a campaign without `--out`,
not a live artifact.** It currently predates V-21 and so carries neither
`skips_by_cause` nor `invariant_worlds_unavailable`, and its `findings.jsonl`
rows still keep `cause` inside `data`. A V-21-schema 500-world run is at
`runs/20260729T104608Z-V21-lp-unavailable-is-not-a-pass/campaign/`. Regenerate
`out/` deliberately or read the run directory; do not read `out/` as the current
schema.

## The house rule

**An oracle may not call the engine it judges.** Checking `zero_space` with
`zero_space.verify` establishes that the module agrees with itself, which is not
the question. So `oracles/gf2.py` is a separate bitset Gaussian elimination and
`oracles/search.py` a separate BFS, plan validator and entropy computation.

`fuzzlab` **never modifies `engine-rig`** — `rig.py` puts it on `sys.path` and
that is the entire interaction. Defects go here and to `PARTNER_SYNC.md`.

The rule bites hardest where an engine consumes another engine's output.
`cegis_miner` publishes `effect.*` — what a rule says *happens* — and the
obvious source of truth for it is `transitions[i].effect`, which is
`cegis_miner` repeating `mdl_segmenter`'s narration. Judging one against the
other establishes that the two agree, and is blind to both being wrong the same
way. So `oracles/motion.py` recomputes what happened from the world's rendered
pixels and imports nothing from `engines` at all.

## The other half: can these invariants fire at all?

A green campaign says something about the engines only to the extent that the
battery could have contradicted them, and an invariant that can *never* fire
produces the same line in `campaign.json` as one that is satisfied. So there is
a second battery whose subject is this one:

```bash
python -m fuzzlab.mutation                       # inject known defects, see who notices
python -m fuzzlab.mutation --engine zero_space
python -m pytest fuzzlab/tests/test_mutation.py  # the harness's own negative control
```

Method and results: [`MUTATION.md`](MUTATION.md). Catalogues: `mutants/<engine>.py`.

Injection happens at **fuzzlab's own seam** — the private helper each property
calls the engine through — so the house rule above is kept in fact and not only
in intent: the engine runs untouched and returns its true answer, and the lie is
told between the engine and the property. That is the right place regardless,
because what is under test is the property.

It found, on its first run, that `partition_matches_truth` had never been able
to report a violation: its only reporting call passed `engine=` to
`finding.violated()`, which already binds that name, so detection raised
`TypeError` instead of returning a finding. The line only runs when the engine
partitions wrongly, and the engine never did — so a dead invariant sat inside a
green campaign for as long as it existed.

## What is checked

| engine | family | invariants |
|---|---|---|
| `mdl_segmenter` | `gridworld` | masks partition the foreground · masks follow anchors · events agree with tracks · script-bits identity |
| `cegis_miner` | `gridworld` | frontier guards are consistent · frontier complete to its own size bound · applicable == support · guards partition the evidence · **effects agree with the evidence** · **rules fire on the action they name** |
| `zero_space` | `parityworld` | laws hold on the trajectory · law space is complete (both directions) · rank–nullity · membership agrees |
| `lp_potential` | `jumpgraph` | certificate ⟹ unreachable · the three conditions hold in exact rationals · heuristic is admissible · infinite ⟹ unreachable |
| `fd_adapter` | `blockworld` | plan replays to the goal · optimal rungs are optimal · no plan ⟹ unsolvable |
| `probe_frontier` | `hypset` | partition matches the observation table · entropy matches brute force · ranking is sound · `splits` is honest · **costs are the world's** |

**Coverage is reported per invariant and it is not the world count.**
`campaign.json`'s `invariant_worlds_evaluated` subtracts the worlds an invariant
filed a `skipped` on, so an invariant that declines is visible as a smaller
number rather than as a silent pass. Beside it, and not derivable from it,
`invariant_worlds_unavailable` counts the worlds that went unjudged because a
*tool* could not compute, and `skips_by_cause` gives the full breakdown; a
`totals.unavailable` above zero means the run measured less than its coverage
column claims, and both gates fail on it: `python -m pytest fuzzlab` on the short
per-engine campaign, and `python -m fuzzlab.campaign` by exit code — which is
consistent with that exit code being about the instrument rather than the
reading, since a tool that did not compute is an instrument fault and not a
finding. A *violation* still exits 0: that is the campaign's product. Two of them decline often and for
stated reasons: `lp_potential`'s four evaluate 267 of 500, because the engine issues no
certificate on 46.6% of `jumpgraph` worlds and every claim there is conditional
on one; all six `cegis_miner` invariants evaluate 465 of 500, declining the
worlds where the object that was mined cannot be established as the mover.
Those numbers used to read 500 and 500 — and the second one used to read 480
while 54 of those 480 were auditing a rock. See `BUGS.md` § V-13 supersede.

`BUGS.md` lists what was **deliberately not** asserted and why. Writing an
invariant against a guarantee nobody made produces a confident, wrong bug report,
and that is the failure mode this battery is most exposed to.

## Three kinds of result, kept apart

`props/finding.py`: `violated` (the engine did something it says it does not),
`raised` (an exception escaped the property), `skipped` (the property could not
be evaluated here, **with the reason and a declared cause**). They are counted
separately because a campaign that silently drops the worlds its oracle cannot
handle reports coverage it did not earn. Documented outcomes —
`NoSeparatingGuard`, `CertificateError`, `PddlError`, `LpUnavailable`, an
unminable segmentation — are `skipped`, not failures.

`finding.failures()` is the gate, and it is **`violated` + `raised`**. Every
documented outcome is caught at its property and converted to a `skipped` with a
cause, so what reaches `raised` is by construction an exception nobody wrote a
policy for. Until V-21 the docstring said exactly that and the body returned
`violated` alone — the prose was the wider of the two, which is the direction
that misleads, and the function had no callers at all, so nothing could observe
the gap. The body moved rather than the prose; see `props/finding.py:failures`.

### `skipped` is three columns, not one

A skip records **why**, and the why is classified:

| class | meaning | expected |
|---|---|---|
| `declined` | a fact about the configuration or the evidence — the property had nothing to judge, and that is correct | large (`lp_potential` declines on ~47% of `jumpgraph`) |
| `budget` | *this battery* declined, on a cost threshold it chose in advance and can quote | non-zero |
| `unavailable` | a tool did not compute — a solver limit, an unbounded relaxation, numerical difficulties. Nobody knows the answer | **zero**, and gated |

The taxonomy is `finding.CAUSE_CLASS`; `cause` is a **required** keyword on
`finding.skipped()` and an undeclared one is a `ValueError`, so a new way for a
world to go unjudged cannot be added without appearing in a diff.

This exists because `lp_potential` had two of them in one integer. E-15 made the
engine raise `LpUnavailable` for HiGHS status 1/3/4 rather than collapse them
into the `(None, None)` that reads as *no linear pagoda exists* — and `props/`
caught `CertificateError` in four places and `LpUnavailable` in none, so the
refusal escaped as a `raised`, and `invariant_worlds_evaluated` (which subtracts
`skipped`, and only `skipped`) counted the world as **evaluated**. Measured on
12 worlds with HiGHS starved to `maxiter=0`: the four invariants reported **11**
worlds evaluated each, against **5** with the solver running normally. Blinding
the battery raised the coverage it claimed, because honest declines are
subtracted and blind spots were not. `tests/test_solver_unavailable.py` is that
experiment, kept as a regression, and it drives the real solver into a real
iteration limit rather than stubbing a result object.

## Seeds and replay

Every world is a pure function of a 64-bit seed. `prng.derive(campaign_seed,
family, index)` folds the family name through FNV-1a so world 17 of one family
and world 17 of another share a campaign seed and nothing else. Each world's
`(family, seed, fingerprint, spec)` goes to `out/seeds.jsonl`; a replay that
regenerates a *different* world is caught by the fingerprint rather than by a
property mysteriously flipping.

`minimize.py` is **minimisation by search**, and is called that because it is not
delta-debugging: a world is a pure function of a seed, so perturbing the seed
replaces the world rather than shrinking it. It draws a pool of seeds, keeps
every one reproducing the same `(engine, invariant, kind)` signature, and returns
the smallest under a stated per-family size metric. That is a small, exactly
replayable reproducer — not a proven minimum, and the archive says so.

## The corpus is the experiment

A green campaign over an easy corpus certifies nothing, and this battery shipped
one before it shipped anything else: the inherited `gridworld` generator could
**never** produce an obstacle — 0 in 3200 worlds — so every world had one object
and `mdl_segmenter`'s component finder was never exercised at all. Three of five
generators were repaired before the corpus was worth running against. The
measured before/after is in `BUGS.md`; the audit is in
`runs/20260728T085448Z-E4-property-fuzz/GENERATOR_AUDIT.md`.

Whenever an invariant fires, **check the oracle before filing**. This battery
made two false accusations against engines that were right every time, both
caught by reading the first finding instead of the count.
