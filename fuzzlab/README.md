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

## The house rule

**An oracle may not call the engine it judges.** Checking `zero_space` with
`zero_space.verify` establishes that the module agrees with itself, which is not
the question. So `oracles/gf2.py` is a separate bitset Gaussian elimination and
`oracles/search.py` a separate BFS, plan validator and entropy computation.

`fuzzlab` **never modifies `engine-rig`** — `rig.py` puts it on `sys.path` and
that is the entire interaction. Defects go here and to `PARTNER_SYNC.md`.

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
| `cegis_miner` | `gridworld` | frontier guards are consistent · frontier complete to its own size bound · applicable == support · guards partition the evidence |
| `zero_space` | `parityworld` | laws hold on the trajectory · law space is complete (both directions) · rank–nullity · membership agrees |
| `lp_potential` | `jumpgraph` | certificate ⟹ unreachable · the three conditions hold in exact rationals · heuristic is admissible · infinite ⟹ unreachable |
| `fd_adapter` | `blockworld` | plan replays to the goal · optimal rungs are optimal · no plan ⟹ unsolvable |
| `probe_frontier` | `hypset` | partition matches the observation table · entropy matches brute force · ranking is sound · `splits` is honest |

`BUGS.md` lists what was **deliberately not** asserted and why. Writing an
invariant against a guarantee nobody made produces a confident, wrong bug report,
and that is the failure mode this battery is most exposed to.

## Three kinds of result, kept apart

`props/finding.py`: `violated` (the engine did something it says it does not),
`raised` (an exception where an answer was expected), `skipped` (the property
could not be evaluated here, **with the reason**). They are counted separately
because a campaign that silently drops the worlds its oracle cannot handle
reports coverage it did not earn. Documented outcomes — `NoSeparatingGuard`,
`CertificateError`, `PddlError`, an unminable segmentation — are `skipped`, not
failures.

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
