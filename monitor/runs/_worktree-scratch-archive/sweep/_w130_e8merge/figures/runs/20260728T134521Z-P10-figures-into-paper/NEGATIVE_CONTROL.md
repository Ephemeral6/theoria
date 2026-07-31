# The three new gates, shown failing

`PLAN.md` §10 records that P8's coverage probe was green over the exact defect it
had been written to catch, twice, because it took its expectations from the thing
it was auditing. Gates 9, 10 and 11 therefore state their roster as **literals**
in `verify.sh` — six figure stems, six caption numbers, the count `6`, and the
six plate-to-paper pairings — rather than importing `paper_map.py`.

This file is the demonstration that the literals bite.

## The injected regression

The kind a careless edit actually produces: one entry dropped from the registry.

```python
# figures/paper_map.py — PaperFigure(number=6, ...) removed from PAPER_FIGURES
>>> [f.cite for f in paper_map.PAPER_FIGURES]
['Figure 1', 'Figure 2', 'Figure 3', 'Figure 4', 'Figure 5']
```

`build_all.py` still succeeds: `fig02_bill_shape` simply stops being a paper
figure and emits 4 images instead of 10, which is a legal state for a plate the
paper does not cite. Gates 0–8 stay green. **The whole point is what happens
next.**

## What the gates said

```
== 9. every publication artefact exists ==
FAIL: missing or empty publication artefact: paper/light/figure6_bill_shape.pdf
FAIL: missing or empty publication artefact: paper/light/figure6_bill_shape.png
FAIL: missing or empty publication artefact: paper/light/figure6_bill_shape.svg
FAIL: missing or empty publication artefact: paper/dark/figure6_bill_shape.pdf
FAIL: missing or empty publication artefact: paper/dark/figure6_bill_shape.png
FAIL: missing or empty publication artefact: paper/dark/figure6_bill_shape.svg
FAIL: missing caption: paper/captions/figure6.md
checked 6 paper figures -> 36 artefacts + 6 captions + index

== 10. the paper's SVG is the plate the pipeline built ==
FAIL: paper/light/figure6_bill_shape.svg differs from out/light/fig02_bill_shape.svg -- the two profiles have diverged
FAIL: paper/dark/figure6_bill_shape.svg differs from out/dark/fig02_bill_shape.svg -- the two profiles have diverged

== 11. the index's digests match the files on disk ==
FAIL: the paper index disagrees with the tree:
    expected 6 paper figures, index declares 5
    checked 5 figures

VERIFY: red.
```

Three gates fired **independently**, on three different grounds — a missing file,
a broken pairing, and a short roster. Note gate 9's summary line still reads
`checked 6 paper figures`: the gate counted what it was told to expect, not what
the registry offered. That is the property being demonstrated. Had it imported
`paper_map`, it would have reported `checked 5 paper figures` and passed.

The registry was restored and `verify.sh` returned to green before anything was
committed.

## Gate 10 was also shown failing for real, not just by injection

Gate 10 failed on **all twelve** plate/theme pairs the first time it was ever
run, on the tree as committed at `ff796cd`. That was not a test fixture; it was
the defect in `FINDINGS.md` F-1 — every plate's committed SVG and PNG carried
different geometry. A gate whose first run is red on the live tree does not need
an argument that it can fail.
