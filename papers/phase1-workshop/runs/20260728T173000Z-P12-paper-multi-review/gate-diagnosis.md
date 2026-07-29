# Diagnosis — the two failing checks in `verify_paper.py`

Run by `W-1651` at base commit `31bea46`, read-only. Zero network, zero API spend.
Baseline: `verify_paper: FAIL (2/4) -- B PATHS, C FIGDATA`.

---

## B PATHS — four citations, all repairable, all verified against the tree

| # | token | where | verdict | fix |
|---|---|---|---|---|
| B-i | `out/dark/` | `sections/03_a0.md:32` | BROKEN — a bare suffix, resolves from neither root | write the whole path: `figures/out/dark/fig06_concept_timeline.svg` (exists, with `.png`; the full fig02–fig07 dark set is present) |
| B-ii | `theory/theory.dsl` | `sections/03_a0.md:18` | BROKEN — **truncation, not a wrong file**; §3.3 line 99 already cites the same artefact at full length | `cold-start-a0/theory/theory.dsl` — classifies `ok`, and costs no new token because line 99 already carries it |
| B-iii | `.../MANIFEST.json` | `sections/09_preflight.md:35` | ELIDED | `theoria-arm/runs/preflight-20260728T012057Z/MANIFEST.json` — run named at line 25, directory verified |
| B-iv | `.../run.json` | `sections/09_preflight.md:35` | ELIDED | `theoria-arm/runs/preflight-20260728T012057Z/run.json` — same |

**B-i does not close by itself.** `figures/out/dark/…svg` classifies **AMBIGUOUS**,
not `ok`, because `figures/` exists both at the repo root and beside `PAPER.md`,
and only the `out/light/` triple is listed in `ADJUDICATED_AMBIGUITY`. The dark
twin has to be added there with the same ruling string. That is the mechanism the
checker documents — *an ambiguity nobody has ruled on fails* — and using it is
the intended path, not a way around the gate.

---

## C FIGDATA — **stale payload, not nondeterminism.** The check worked.

The extractor is deterministic: two independent runs into two separate scratch
directories produced byte-identical output. `common.emit` sorts keys, pins
`newline="\n"`, writes no timestamp; fig1's only comprehensions are wrapped in
`sorted(...)`; no glob, no float accumulation.

The committed payload is simply older than its input. The whole diff is four rows
appended to `expressivity_ledger` — E-06…E-09 — and nothing else; `adjudications`,
`revisions`, `compiler_defects` and `revisions_driven_by_certify` are unchanged.
fig2 and fig3 diff clean.

**Why fig1 alone drifts, and fig2/fig3 do not:** fig2 and fig3 read frozen JSON
artefacts. fig1 reads `cold-start-a0/THEORIZE_LOG.md` — a *living Markdown log
that another track keeps appending to*. Nothing structural distinguishes the
extractors. The difference is entirely in what they are pointed at.

### The fix is **not** "regenerate", and this is the substantive finding

The obvious repair — rerun the extractor, commit the new payload — is wrong, and
the paper's own text is what proves it.

* `sections/10_limitations.md:41–43`: "A0's run produced an expressivity ledger of
  **five** gaps (… E-03 the frame axiom, E-04 landmark declaration, E-05 weight
  vectors)".
* `sections/04_a1.md:92`: "**What A1 did not settle: E-06, an open problem**", and
  line 112 books E-06 to `theory-compiler/STATUS.md`.

So **E-06 is A1's, by the paper's own account, and it is sitting in A0's log.**
E-06's text — "a proof method for goals no linear pagoda covers" — is pagoda
weights, which is A1 peg solitaire, not A0. The four new rows entered in commits
`3f3f396`, `76e7560`, `4dd8e0f`, all after `4959df1`, which is when the payload
was written.

Regenerating would make the A0 concept-timeline plate silently absorb post-A0
work and contradict the paper's own "five gaps" sentence. The staleness was
holding a correct figure in place.

**Correct repair:** pin the plate to A0's scope rather than to the log's current
state — the extractor should take the ledger rows that existed at A0's close, and
say in the plate's caption which commit that is. The failure is that the figure's
provenance is "whatever this file says today", which is not a provenance.

**A constraint on who fixes it:** `cold-start-a0/` belongs to the
**theory-compiler** track and is off limits to engine-rig (`CLAUDE.md`). This
worker cannot correct the log itself — only the paper and the extractor. If the
right fix is that post-A0 rows do not belong in A0's log, that is the other
track's call and needs a `PARTNER_SYNC.md` paragraph, not an edit from here.

---

## Side finding — the checker dirties the working tree

`check_figdata`'s `finally` block (`verify_paper.py:217–220`) restores only
`data/*.json`. `emit` also writes `figures/<name>.txt`, which is never restored,
so **every run of `verify_paper.py` leaves the tree modified**. It had already
happened before I looked: `git status` showed
`M papers/phase1-workshop/figures/fig1_concept_timeline.txt` from a prior run.

A gate that mutates what it is measuring will eventually be the thing that fails
the next gate. The restore loop should snapshot `figures/*.txt` alongside the
JSON.
