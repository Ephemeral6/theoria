# P19b — the zero, its three explanations, and four numbers that were wrong in our favour

Offline. No ARC action, no model call, no network, no ledger, $0. No directory
whose name contains `A26b` was read or written; a long-leg experiment owns those
and was writing them while this ran.

## What the brief asked for and where it was wrong

The brief handed to this run named four things to carry into the paper. Three of
them were right, one was wrong, and one more turned out to be wrong in a way the
brief could not have known. Re-deriving each against its artefact before writing
it is the only reason any of that surfaced, and it is the fourth instruction the
brief gave.

**Right, and carried.** The zero-completion fact and its three competing
explanations (§11.3b). The baseline zero being a budget artefact on two of the
four games (§7.10a). The generated frontier lifting live probe containment from
9.6 % to 78 %, with the offline replay having predicted 83 % beforehand
(§11.3a).

**Wrong: "nothing ever exceeded 33 actions."** That is the Theoria arm's
maximum. The baseline arm's best `g50t` observation is **73** successful actions
— 93.6 % of the 78 the level costs — and its best `ar25` observation is **67**
against a reference of 32. The sentence the brief offered would have made the
budget argument look airtight on all four games; the artefact refutes it on two.
`baseline-arms/runs/20260802T2040Z-A28-baseline-zero-examined/audit_zero.json`
had this already; nothing in the paper had read it.

**Wrong, and nobody had said it: the paper's own ledger sentence.** §7.10a and
§11.2 both read 「`baseline-arms/ledger.jsonl` carries 560 rows and records
`levels_completed` 0 throughout」. Recounted: **656** rows, **214** carrying the
field (all 0), **442** not carrying it at all. *Throughout* was never true of any
version of that file — it promoted 442 absences to zeros, in a section whose
entire argument is that absences must not be promoted to zeros. Both sites are
corrected.

Also corrected, from `baseline-arms/runs/20260802T2040Z-A28-.../RUN_STATE.md` and
from `theoria-arm/runs/20260802T2100Z-A27-.../MEASUREMENT.json`, neither of which
the paper had read: the denominator 46 is the manifest's *entry* count and 43 is
the run count; no `bare_cc` `run.json` has ever carried a `score` key, so "highest
score 0" was reading `levels_completed`; and the claim that the arm "cannot see a
win" is half wrong — the detector is wired into `inner/loop.py` and fires mid-leg,
what has never happened is the *write*.

## What is in this directory

| file | what it is |
|---|---|
| `census.py` | recomputes every number the 2026-08-04 paper edit states, from tracked files only, and prints AGREES / DIFFERS against each source arm's published figure. `--check` exits 1 on any DIFFERS. `--negative-control` runs the four mutations. |
| `census.json` | its output. |
| `RUN_STATE.md` | this file. |
| `stamp_manifest.py` / `MANIFEST.json` | provenance, hashed over the bytes git publishes rather than the working copy. |

The negative controls also run in the papers suite, as
`papers/phase1-workshop/test_zero_census.py` (9 tests). A census that is only
ever run by hand is a census that stops being true silently.

## The measurement

**27 comparisons, 27 AGREES, 0 DIFFERS, 3 recorded as `unmeasurable-here`.**

Three absences are carried as their own categories rather than folded into zeros,
because that folding is the defect the whole edit is about:

* 7 of 43 `bare_cc` runs have no summary, so they have no `levels_completed`
  at all. `absent`, never 0.
* 4 of 16 live Theoria legs record no `levels_completed`; `summary.score` is
  `null` on all sixteen, while the eleven archived scorecard bodies record
  `0.0`. Those are different facts about different fields.
* all 22 per-leg level logs are zero bytes. `never_written`, not `0 rows` — the
  recording path has not executed once, in any leg, including the mocks.

The three `unmeasurable-here` rows are the per-tier baseline action totals (the
tier lives in the scorecard `tags`, which this census does not join — read from
A28 and labelled as read), the anchor-drift decomposition behind the 47
off-frontier probes of 2026-07-31 (needs a gitignored frame trace), and whether
any leg would complete a level at adequate budget (the experiment does not
exist).

## What changed in the paper

| site | change |
|---|---|
| abstract | new paragraph: the zero, the three explanations, and the refusal to read it as capability; the probe paragraph now carries the live R2b confirmation |
| §1.5 | two closing notes — the R2b confirmation, and the zero flagged before the contributions list rather than only in §11 |
| §7.10a | the four-game reference table, the two-of-four split, the tier qualification, the three denominators, the ledger correction |
| §11.2 | the ledger correction, in the second place it appears |
| §11.3a | "no live leg has ever run with the switch on" → the round that ran 39 minutes later; the methodological result; the twenty-two zero-byte logs replacing "0 rows across ten legs" |
| §11.3b | **new** — the central negative result, the three explanations, and the ordered experiment |
| §11.5 | the containment improvement, scoped so it is not read as the beat working |
| §12.3 | the width claim moves from design to measurement, and still never reaches the miner |
| `PROVENANCE.md` | four rows rewritten, four added |
| `OPEN_ITEMS.md` | A5 (the open question) and A6 (four corrections made, the sweep not done) |
| audit stamps | `CITECHECK-2026-08-01.md` / `REVIEW-2026-08-01.md` → `stale` + `superseded_by`; `CITECHECK-2026-08-04.md` / `REVIEW-2026-08-04.md` written as binding delta successors |

## Gates, verbatim

Baseline, in a fresh worktree on `master` (`4846e66d`), before any edit:

```
cd papers && python -m pytest -q
2 failed, 272 passed, 1 xfailed in 21.69s

python phase1-workshop/verify_paper.py
verify_paper: FAIL (3/7) -- C FIGDATA, E UNCITED, F BARE
  C FIGDATA: fig1_concept_timeline.json changed on rerun
  E UNCITED: 435 claim blocks, 1 uncited, 9 ruled, 0 stale rulings
  F BARE:    95 bare-filename citations, 24 ambiguous, 4 ruled, 0 stale rulings
  B PATHS:   247 distinct path citations, 0 ambiguous-unruled, 0 elided, 0 broken
  G AUDITSTAMP: PASS
```

After:

```
cd papers && python -m pytest -q
2 failed, 281 passed, 1 xfailed in 25.63s

python phase1-workshop/verify_paper.py
verify_paper: FAIL (3/7) -- C FIGDATA, E UNCITED, F BARE
  C FIGDATA: fig1_concept_timeline.json changed on rerun
  E UNCITED: 452 claim blocks, 1 uncited, 9 ruled, 0 stale rulings
  F BARE:    95 bare-filename citations, 24 ambiguous, 4 ruled, 0 stale rulings
  B PATHS:   262 distinct path citations, 0 ambiguous-unruled, 0 elided, 0 broken
  G AUDITSTAMP: PASS
```

**The three reds are the same three, with the same finding counts.** `C FIGDATA`
is the deliberate one — `runs/20260728T173000Z-P12-paper-multi-review/REVISION.md`
records the reasoning for leaving that payload as committed. The two pytest
failures are the same two: `test_the_live_paper_is_green_and_its_anchors_are_in_range`
(it asserts F is green, and F is not) and
`test_the_live_papers_tree_classifies_cleanly` (`case-studies/` and
`related-work/` are unclassified). Neither was introduced or fixed here. The nine
new passes are `test_zero_census.py`.

**During the work F went 24 → 27 → 24 and E went 1 → 10 → 1.** Every new finding
was closed by writing the real citation into the prose. **No `ADJUDICATED_*`
entry was added and `verify_paper.py` was not touched** — a gate edited by the
change that has to pass it is not a gate, and P17 already recorded that a green
gate is not evidence.

## Residual gaps, stated rather than closed

1. **The \$0 experiment is not done and this territory cannot do it.** Making the
   level-boundary detector fire once, offline, belongs to `theoria-arm`. Until it
   lands, §11.3b's third explanation stands and every zero-completion record in
   the repository is worth less than it reads.
2. **The per-tier split is read, not recomputed.** §7.10a's "all six are
   haiku-4.5" comes from A28's own script; joining the scorecard `tags` to the
   run id was out of scope here and the census says so rather than reporting a
   zero.
3. **One leg's two instruments disagree.** `20260801T001851Z-R1b-sk48-b` records
   `probe_actions: 0` in its summary and one completed probe in its
   `probes.jsonl`. The census prints both and names the leg; reconciling it is
   the arm's call, not the paper's.
4. **§3–§6 and §8–§10 have had no equivalent recount.** Four numbers were wrong
   in the flattering direction in the two sections that were checked. That is a
   base rate, not a coincidence, and `OPEN_ITEMS.md` A6 records the unswept
   remainder.
5. **The "several hundred actions" extrapolation in §11.3b is an
   extrapolation**, flagged as such in `REVIEW-2026-08-04.md`. The claim it sits
   beside — largest non-probe action count is 11 — stands without it.
6. **The paper got longer.** Roughly 2,400 words, against `OPEN_ITEMS.md` E1's
   note that it is already ~3× a workshop budget.

## Reproduce

```bash
cd papers/phase1-workshop/runs/20260804T1500Z-P19b-the-zero-and-its-three-explanations
python census.py --check
python census.py --negative-control
python stamp_manifest.py --check
cd ../.. && python assemble.py && python verify_paper.py
cd .. && python -m pytest -q
```
