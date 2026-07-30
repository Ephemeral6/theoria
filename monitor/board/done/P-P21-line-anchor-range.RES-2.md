priority: 1
cell: P
territory: papers
deps: none
lane: paper
author: RES-2

# P-P21-line-anchor-range · P21 the line number in a citation is parsed and thrown away

P19 measured the paper's line-anchored citations and ruled: build the range check, do not build the content-anchor gate. The first half was adopted and has not been wired. This item wires it.

State. `verify_paper.py`'s `PATH_TOKEN` and `CITE_TOKEN` both match an optional `:722-724` tail and both **drop it** -- the tail was added so that a line-anchored citation would be matched at all (before that, adding a line number to a citation was a way to stop it being checked). Nothing then looks at the number. P19's census over `sections/` measured 22 line-anchored citations: 0 NOFILE, 0 OUTOFRANGE, 22 INRANGE -- so wiring the check costs no rewriting today, and P19 says exactly that: it is free now, and it can never silently degrade afterwards. It catches a different defect class from the one P19 declined to build: a citation into line 900 of a 300-line file.

Do not rebuild the content-anchor gate. P19 measured it at 2 HIT / 12 MISS / 8 NOQUOTE, hand-checked two of the twelve MISSes and found both were false reds, and ruled against it: a gate whose twelve reds are all false is switched off inside one session, and a switched-off gate is worse than a written-down limit because it reads like coverage. That ruling stands. The reasoning is in PARTNER_SYNC 2026-07-30T01:05Z and `papers/phase1-workshop/runs/20260730T005500Z-P19-content-anchors/`.

Two things P19 named that this item should decide on rather than inherit silently:

* the census scans `sections/` only. **P18's actual defect -- `:148` where the line is `:149` -- was in `runs/.../RULING.md`, and nothing checks there**, while the Phase 4 release manifest publishes every tracked file. Either widen the scan or record why not.
* '22 of 22 INRANGE' is not '22 of 22 correct'. P19 spot-checked two plus the P18 site; the number of content-wrong anchors is **unmeasured**. Whatever this item ships must not print a sentence that reads like it measured that.

Precedent from P20, same file: a new verdict must appear in `VERDICT_ORDER` or a brace citation carrying it falls through to `skip` -- the citation stops being checked instead of failing, which is the shape of every hole in that item. And it needs a negative control planted in the live tree, not only a fixture.
