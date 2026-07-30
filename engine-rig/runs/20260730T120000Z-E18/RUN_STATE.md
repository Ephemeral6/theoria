# E18 · giving every survey number a script, and finding out the report was mostly honest

**Ticket** E18-survey-numbers-reproducible (W-1711, generic lane) · **territory**
`engine-rig` · **branch** `agent/e18-survey-numbers-reproducible` · **base**
`cc7e414e` · **worktree** `.worktrees/e18-survey-numbers-reproducible` ·
2026-07-30. Zero API calls, zero network, zero sealed-pile contact, $0.00.

## What the ticket said, and what was actually there

The cross-check run `runs/20260729T000000Z-E11-engine-crosscheck-deep/` holds
**nine `.md` files and one `MANIFEST.json`** — no data, no scripts. (The ticket
said eight `.md`; it is nine. The premise is unaffected.) So its five headline
ratios — 639/2189 = 29.2 %, 126/300, 104/149, 1633/4000, 82/4000 — were prose.
The defects' *mechanisms* had been confirmed by later auditors reading source;
the *counts* had been confirmed by nobody.

Two things the ticket did not know, both found before any recomputation started:

* **The blast radius is 87, not 5.** That many `ENGINE_TABLE.md` registry facts
  are probed out of the E11 directory.
* **Of those 87, exactly two reach the paper body** — `lp.incomplete`
  (639/2189) and `lp.no_farkas` (638), both in §10.5, both load-bearing. The
  other three named ratios, and `104/149`, appear in no section and no figure.
  Full census with per-key paper sites: `SCOPE-census.md`.

## The rule this produced

`DECISIONS.md` **D-036**. The short form: *a regex over prose is a
transcription check, not a recomputation check.* Every one of the 87 entries is
an `md(path, regex)` probe (`tools/engine_table.py:116-131`), which guarantees
that the table's digits match the report's digits and says nothing about
whether the report's digits match anything that ran. `jf`/`jlf` already read
real JSON for other facts, so in the rendered provenance table a prose-backed
fact and a data-backed fact are typographically indistinguishable.

Three dispositions for a number nobody can recompute, and only these three:
re-measure on today's code and label the caliber change; withdraw it; or publish
a declared spread with a declared seed. A frozen reimplementation of deleted
behaviour is not a fourth one on its own.

## The result: the cross-check was honest

Six modules under `tools/survey_numbers/`, one per family. Counts in `counts/`,
per-world raw records in `raw/`, every input sha256-pinned.

| family | numbers recomputed | outcome |
|---|---|---|
| `mdl_segmenter` | 22 | **22/22 exact**, including 126/300 |
| `cegis_miner` | 11 at E11's caliber | **11/11 exact**, including 104/149 and 131/149 |
| `lp_potential` | base-rate table, 29.2 %, 638, bound triple, N=500 slice | **all exact** |
| `zero_space` | 11 registry + 23 supporting | **all exact** |
| deadlock / `fd` / `ic3` | 11 registry + 25 supporting | **all exact** |
| `probe_frontier` | 13 registry + §4B table | all exact **except `pf.infinity_rows`** |

That is a real result and it was not available before, because a report that
agrees with itself is not evidence either way.

## The three things a rerun found that re-reading could not

**`2a1c30d` does not move 29.2 %.** The ticket's premise was that it did. The
commit narrowed `if not result.success: return None` to "status 2 → `None`,
statuses 1/3/4 raise". The solver-status histogram over the corpus is
`{0: 1550, 2: 1450}` — **no world lands in the band where the two rules
differ**. Checked twice: derived from the histogram, then measured by extracting
the genuine pre-`2a1c30d` module out of git into a tempdir and running all 3000
worlds. 3000/3000 agree. An adversary proved the extracted module is
uncontaminated — 0 entries added to `sys.modules`, 0 symbols resolving under
`engines/`, every method's `co_filename` in the temp file. **True of the code
path, false of the number.**

**`cegis`'s caliber did change, and the defect survived the repair.** V-13
(`eb61aa98`) made `props._mine` mine the mover rather than `tracks[0]`, so
104/149 describes a mining path the engine no longer takes; today it is 155/232.
The ratio barely moves (69.8 % → 66.8 %) because the defect is structural in
`lift` — repairing F-1 handed the miner *more* unverified rules to publish. Both
calibers are published side by side. The F-1 counts collapse as they should
(72 worlds → 8, 1209 rows → 110), and the residual 8 are exactly the worlds
where `_mover_track` returns `None`, verified as identical sets rather than
equal counts.

**`probe_frontier`'s corpus is gone.** E11's generator lived in a session
scratchpad and was never committed; its partial records the draw's shape but no
seed, no RNG, no draw order — because, as §1 says outright, it deliberately
imported nothing from `fuzzlab`, and so never touched the discipline that would
have recorded a seed. An adversary swept full history, dangling blobs, both
stashes, the reflog and the `e11` worktree: no generator. `pf.infinity_rows` is
therefore unreproducible **to the unit by construction**. Its registry entry
should be a spread with a declared seed, not a digit — D-036's third
disposition, used in earnest.

## What the adversarial reviews overturned, including my own claims

Two agents were commissioned to refute the two heaviest conclusions. Both
earned their cost, and both are recorded because a review that only confirms is
not evidence.

**The census's headline finding was mine and was wrong.** I reported that
`PAPER.md:3023`'s "bounds of 100, 10⁴ and 10⁶" is cited to `ENGINE_TABLE.md`,
which contains none of those strings. The parenthetical belongs to the item
*heading*, which that file publishes verbatim, and §10.5 uses that form
throughout. Reading a heading's artefact reference as a citation for every
sentence under it is the misreading of someone hunting a defect. What survives
is smaller and real: there is **no registry key** for the bound triple, so those
three numbers sat in the paper unregistered and unscripted. The claim had
already propagated into `lp_incomplete.py`'s docstrings and a
`citation_is_wrong` field; corrected in `SCOPE-census.md` in place rather than
deleted, and removed from the module.

**`probe_frontier`'s findings were three-quarters overstated, including in a
commit message of mine.** Of four figures declared non-reproducing: the two
entropy deltas reproduce **exactly** under the right reading (max over states of
the *top-ranked* action's entropy — which is what the surrounding prose is
about); `zero_cost_bug` at 80 vs 82 **agrees within noise**, a difference of 2
against a difference-sd of ~10; and the "row shift in the prose" was a
coincidence over-read. Only `infinity_rows` remains open. Sharpest of all, the
module impeached E11's 82 as "outside the 32-corpus range" while its own 80 sits
outside that same range at z = +2.34 — **the instrument impeached its own number
identically** — and its caveats quoted a 200-replicate run the artefact does not
produce. For a ticket whose thesis is "prose is not where a number is stored",
that is the defect reappearing inside the fix.

**Four latent defects in `lp_incomplete.py`, each proven by injection**, none of
which move today's numbers but all of which would corrupt a future rerun:
`_incompleteness` counted `not certificate_issued` — the collapsed predicate
`2a1c30d` exists to remove, so a status-1 world lands in the numerator;
`_caliber` double-counted; `_wider_box` entered a *failed* solve into
`feasible_any` and thence into `lp.box_blocked`, which is precisely "a tool that
failed is not a fact about the world" reintroduced inside the audit of it; and
`bounds_table["undecided"]` always read 0. Also refuted: a
`same_set_of_worlds: true` that was a subset test on a one-element list, and so
could not fail — the artefact published a `true` that meant nothing.

## What is enforced, and what is not

`tests/test_survey_numbers.py` guards the **wiring**: every module exposes
`compute()`; every counts file names a module that still exists and inputs that
were present when it ran; every disagreement with E11 carries a caveat; and
every registry key still probed out of E11 prose is declared in
`tools/survey_numbers/unscripted.py` **with a reason**. `verify.py` rung 4
guards the **values** by re-deriving them and failing on drift. The split is
deliberate: a suite that recomputed thousands of worlds would be too slow to
run, would be skipped, and a skipped check is the defect this ticket is about.

Limits, stated rather than implied:

* The gate distinguishes a present computation from an absent one. It cannot
  distinguish a right one from a wrong one.
* Three modules resolved ambiguities in E11's prose recipe by reading code, and
  each recorded which reading it took rather than the one that made the number
  come out. A *shared* misreading of the same document would still pass.
* `input_digests()` pins what a script read, not that it read the right thing.
* The `open4far` four-way encoding agreement is evidence about the encodings,
  not about the board: all four descend from one byte-identical `.pddl` file.
* `zs.same_span = 200/200` is a control, not evidence — the two row spaces
  provably coincide, so it cannot come out otherwise.
* Fast Downward is absent on this machine. No number here depends on it; the
  three sokoban encodings are complete BFS.

## Prose defects found in E11 that move no digit

Recorded because the next reader will hit them. `mdl`: none. `zero_space`: the
13-row table's column headed 轨迹步数 ("steps") holds **state** counts (13/13
match under that reading, 0/13 under the other); two quoted `coverage` payloads
are `4/4` and `18/18` where the engine writes `3/3` and `17/17`; and
`CROSSCHECK.md:104`'s "2911 such rows" over-attributes — 2911 is the right total
but only 1098 are the 370/366/4 group. Deadlock: §6b's printed `inv_closed`
witness for `a2-world` shows `button: 7`, and no such state is reachable — the
rule, the cells and the localisation are right, the printed field is stale.

## Reported elsewhere, not fixed here

`monitor/inbox/20260730T1430Z-W-1711-the-same-disease-lives-in-two-other-territories.md`:
`fuzzlab/runs/20260728T152000Z-V10-fuzz-mutation-power` is markdown-only and
supplies **16** registry facts (none reaching the paper yet — the same defect,
one step earlier); `runs/20260729T080000Z-C11-tool-failure-as-truth` is
markdown-only and cited twice by the paper, both times for claims carrying no
number; and `PAPER.md:3125`'s "14 of 19 mutants" is cited to a prose file and is
in no registry key at all.

## How to re-run everything

```bash
cd engine-rig
python -m tools.survey_numbers.run_all --out runs/20260730T120000Z-E18/counts          # regenerate
python -m tools.survey_numbers.run_all --out runs/20260730T120000Z-E18/counts --check  # re-derive and diff
python verify.py                                                                        # all four rungs
```
