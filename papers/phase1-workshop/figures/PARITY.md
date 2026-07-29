# figures/PARITY.md — the paper's figures against the repository's pipeline

`P9-paper-to-submittable`, scoped by ruling to the figure clause. RES-2, branch
`agent/p9-paper-to-submittable`.

## What was wrong

The paper had **its own figure pipeline**. This directory's `fig1`/`fig2`/`fig3`
scripts read repository artefacts, emit a JSON payload and an ASCII plate, and
the sections cited *the script* as the figure's provenance — `sections/03_a0.md`
pointed at `fig1_concept_timeline.py`, and so on. Meanwhile `figures/` at the
repository root builds six plates deterministically, through a CSV audit layer,
from a hashed source registry, behind eight gates.

**Three of those six are these three figures**, computed independently from
overlapping artefacts by two authors who never compared them:

| paper | pipeline | what it draws |
|---|---|---|
| Figure 1 `fig1_concept_timeline` | `figures/fig06_concept_timeline` | the adjudication timeline |
| Figure 2 `fig2_coverage_accuracy` | `figures/fig07_a0_vs_a0prime` | coverage against accuracy |
| Figure 3 `fig3_loop_ledger` | `figures/fig05_a2_repair_loop` | the A2 repair loop |

Two implementations of one figure is two definitions of every number in it. The
work order asked for the paper's figures to come from the deterministic pipeline
rather than be pasted in by hand.

## Why this directory was not simply deleted

Deleting it would have destroyed the one thing it had become uniquely good for.
It is a **second opinion**, and a second opinion is the only instrument that can
catch a first one being wrong. So `check_figure_parity.py` makes the two answer
the same questions, and the sections now cite the pipeline while these scripts
stay as the witness.

## What the comparison found

**12 agree**, and they are the load-bearing ones: A0's accuracy and coverage
(0.987288, 233/236), A0′'s accuracy (1.000) and coverage (0.469298, 107/228),
A0′'s 13 executable probes, zero manual revisions driven by `certify`, three
compiler defects, and the A2 ledger's eight beats over a six-beat loop.

**1 one-sided.** `figures/fig07` marks A0's executable-probe count
`absent-not-in-source-registry` — the number exists only in a source the
registry does not declare, and therefore does not hash — while this directory
prints it as **0**. This is not a rounding difference. It is a disagreement
about what counts as evidence, and it is `OPEN_ITEMS.md` C11 arriving from the
other direction: *"Two figure payload fields are hard-coded against their own
docstrings (`revisions_driven_by_certify: 0`, `executable_probes: 0`)."* The
pipeline's refusal is the stricter and the correct standard. Reported, not
failed, because the difference is deliberate on both sides and a red light here
would only teach someone to suppress it.

**1 disagreement, and it is adjudicated.**

> The paper's figure counts **18** adjudications; the pipeline counts **17**
> distinct ids. The difference is exactly **P-03**.
>
> `cold-start-a0/THEORIZE_LOG.md` records no bold verdict for P-03.
> `figures/fig06` emits it as `event_kind: verdict-absent-ABSENT` with the label
> *"the log records no bold verdict for this entry"*, and declines to count it
> as adjudicated. This directory's parser instead assigns it the verdict string
> **`"see body"`** and counts it.
>
> **Ruling: the pipeline is right and this directory is wrong.** `"see body"` is
> a placeholder the parser invented to fill a hole in the source. Filling an
> absence with a value is the single thing every figure in this repository is
> required not to do — it is `PLAN.md` §0's standing rule and `REPORT_V0`'s whole
> complaint. The honest count is **17 adjudications, with one probe designed and
> never ruled on**.
>
> The consequence for the prose is small and real: `sections/03_a0.md` describes
> Figure 1 as "every decision with its verdict". One entry has no verdict, and
> that is now said.

## How this stays true

`check_figure_parity.py` runs the comparison. A disagreement that has been
looked at and ruled on lives in `KNOWN_DISAGREEMENTS` **with its adjudication**,
which is printed on every run; a disagreement that is not listed fails the
check, because it is new. A permanently red check is a check people learn to
scroll past, and a check that hides its rulings is worse than no check.

Two of the probes in that script were wrong when first written, and both are
described in the code rather than quietly corrected. The first counted every
timeline row and manufactured a disagreement of 18 against 115. The second
compared 18 items against 20 *events*, because the pipeline rules on some items
more than once. A wrong probe is loud, specific and about nothing, and the only
defence is to check the probe against the data before believing what it says.
