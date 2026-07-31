# Case studies — the Phase 3 结 deliverable, drafted early

Theoria's stage-deliverable clause fixes what each phase boundary owes:

> Phase 3 结:开发堆案例研究(概念诞生时间线 + 死锁定理集)
> — [`../../Theoria.md:381`](../../Theoria.md)

This directory is the prose half of that unit, written now rather than after the
online campaign, because the material for three deep cases already exists on the
tree. Two of the three are the text bodies of figures §3.2 already books:
**图 6 概念诞生时间线** and **图 5 DC22 案例**
([`../../Theoria.md:416`](../../Theoria.md)).

| # | case | what it is | figure |
|---|---|---|---|
| 1 | [The birth of a concept](01-birth-of-a-concept.md) | Button and Door from two unclaimed pixels to two vocabulary entries, against a compression account that says neither should exist | 图 6 |
| 2 | [Reversibility beats coverage](02-reversibility-beats-coverage.md) | A0 vs A0′ as a controlled pair: 99 % coverage with three errors against 47 % with none | — |
| 3 | [A true theorem that is false](03-a-theorem-true-and-false.md) | A2's exhibit and its six-beat repair; the two-layer truth regime as two Lean files you can diff | 图 5 |

Chart data for each lives in [`data/`](data/), one file per case. Figures
themselves are the **P21-figures** ticket's territory; this directory ships the
numbers and the words, not the plots.

---

## The scope this set does and does not cover

**It is not on the development pile.** Phase 3 结 asks for 开发堆案例研究 —
case studies on the ARC development pile. All three cases here run on
**self-built worlds** (A0, A0′, A2), which is what Phase 1's offline acceptance
items produced. The ARC development pile has been touched only at the
`scores_only` level, by blind action probes with no model or human reading a
frame ([`../../baseline-arms/TOUCHED_GAMES.md:20-26`](../../baseline-arms/TOUCHED_GAMES.md)),
and the Theoria arm has reached first contact on one level
([`../../theoria-arm/runs/20260728T015354Z-g50t-first-contact/`](../../theoria-arm/runs/20260728T015354Z-g50t-first-contact/)).
So these are **pre-campaign case studies standing in for the ones the clause
asks for**, and when the campaign produces its own they should be re-cut on live
material rather than retrofitted.

**The 死锁定理集 half is not here.** That half exists and is
`engine-rig`'s: `deadlock_carver` produces conditional mini unsolvability
theorems of the form `pattern AND not-goal => dead`, and the node account for
them — including the zero row that stays on the record — is at
[`../../engine-rig/STATUS.md:25-45`](../../engine-rig/STATUS.md) and
[`../../engine-rig/engines/deadlock_carver/README.md`](../../engine-rig/engines/deadlock_carver/README.md).
It is written up there, on a sokoban fixture rather than a development-pile
level, and it is not restated here.

**The sharpest limit on all three cases.** In A0, A0′ and A2 the theorize step
was performed by hand and the DSL files are checked in as artefacts. *A2 tests
the instrument and the loop, not the theorizer*
([`../../cold-start-a2/A2_REPORT.md:271-273`](../../cold-start-a2/A2_REPORT.md)).
Nothing in this directory is evidence about what an LLM does under experimental
conditions. Every case restates this in its own §"what this does not show", and
none of them should be cited without it.

---

## Citation discipline

The rule for this set is that **every number and every quotation points back at a
file and a line on the tree**. Citations are Markdown links whose text is a
backticked relative path with a line or line range:

```markdown
[`../../cold-start-a0/THEORIZE_LOG.md:104-109`](../../cold-start-a0/THEORIZE_LOG.md)
[`:117-118`](../../cold-start-a2/A2_REPORT.md)      <- short form; path comes from the href
```

[`check_citations.py`](check_citations.py) is the executable form of that rule.
It resolves every citation, checks the target exists and is long enough, and
with `--show` prints the cited lines so the anchor can be checked by eye rather
than trusted:

```bash
cd papers/case-studies && python check_citations.py          # summary, non-zero exit on failure
cd papers/case-studies && python check_citations.py --show    # print every cited passage
```

It is a *link* checker, not a *claim* checker: it proves a citation points at
real, non-blank lines, not that those lines say what the sentence says. Running
it caught two mis-anchored ranges during drafting; a skeptical read caught the
rest.

Cross-references between cases are relative paths. Nothing here links outside
the repository.

## Three upstream corrections these case studies produced

Writing the citations down at line granularity found three places where a
published number or sentence does not survive contact with the artefact. All
three are recorded in the case studies and in `data/`, and none of them changes
a load-bearing claim:

1. **`A0P_REPORT.md:51`'s "A0: 0 of 22" is not reproducible.** A0's base run
   emits 9 probe rows (17 across both its manuals); the frontier members across
   those rows sum to 29. The existing gloss in the workshop figure data proposes
   frontier-member counting, which gives 29, not 22. The load-bearing half —
   **0 executable versus 13** — is verifiable from both artefacts.
   ([case 2 §5](02-reversibility-beats-coverage.md))
2. **`A2_REPORT.md:69-71`'s "the deletion is the whole diff" is true of the rule
   content and false of the file.** The holed manual also drops the `jumped`
   event, re-counts four coverage figures, re-prices the Cart, and swaps the
   pending theorem — all of which is what an honest re-derivation on the shorter
   evidence *should* produce. ([case 3 §1](03-a-theorem-true-and-false.md))
3. **A0's two compression tables differ by a uniform 4 bits per object.** They
   are different accountings and neither report claims they should agree, but the
   offset is unexplained on the tree.
   ([case 1 §9](01-birth-of-a-concept.md))

## Provenance

Run record: [`runs/`](runs/). The case studies were written from the four
reports and their `THEORIZE_LOG`s, the primary artefacts under each spike's
`artifacts/`, and `Theoria.md`. No file outside `papers/case-studies/` was
modified; `cold-start-a0/`, `cold-start-a2/` and `engine-rig/` were read only.
