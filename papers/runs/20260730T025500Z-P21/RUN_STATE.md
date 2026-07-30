# P21 — the line number in a citation was parsed and thrown away

`prompt_id` `P-P21-line-anchor-range` · lane `paper` · territory `papers` ·
RES-2 cycle 38 · branch `agent/p-p21-line-anchor-range`, stacked on
`agent/s-p20-nosecret-noop`

P19 measured the paper's line-anchored citations and split the answer in two:
**wire the range check** — 22 of 22 in range, so it costs nothing today and
cannot silently degrade afterwards — and **do not build the content-anchor
gate**, measured at 2 HIT / 12 MISS / 8 NOQUOTE with both hand-checked MISSes
false. The first half was adopted and never wired. This item wires it. The
second half stays unbuilt, and there is a test asserting the gate does not print
a sentence that reads as though it had been built.

## What was actually broken

`PATH_TOKEN` and `CITE_TOKEN` both matched the `:722-724` tail and both **threw
it away**. The tail was added so a line-anchored citation would be matched *at
all* — before that, `no/such/dir/thing.md:3` matched neither regex, so adding a
line number to a citation was a way to stop it being checked. Matching it and
then discarding it is the other half of the same hole: the path was resolved and
the number was not read by anything.

## Measurement, and the part of it that changed the design

`sections/`, reproducing P19 exactly: **22 line-anchored citations, 22 in
range.** But the split matters:

| | count | seen by |
|---|---|---|
| with a `/` | **8** | check B |
| bare filename | **14** | check F only — B skips a token with no `/` by design |

So **wiring the range check into check B alone would have covered 8 of 22.** The
other half is in `scan_bare`, where F has already resolved the file to a single
candidate and was dropping the number. That is not in P19's write-up; it came out
of re-running the census against the two regexes rather than against a
standalone script.

## The scan boundary: measured, then declined

The item asked this to be decided rather than inherited. P18's actual defect —
`:148` for a line at `:149` — was in a `runs/.../RULING.md`, and nothing checks
there, while the Phase 4 release manifest publishes every tracked file. So the
run records were measured too: **80 tracked `.md` outside `sections/`, 1025 line
anchors — 916 in range, 3 out of range, 62 resolving to no file, 44 to an
ambiguous basename.**

**Gating them would put the gate red on arrival with 109 findings**, which is the
condition P19 refused for the content-anchor gate and this repository has paid
for more than once. Declined, with the count written down instead of the reason
being left implicit.

Two of the three out-of-range anchors are **mine, in last night's S34 run
record**: it cites `monitor/ci/merge.log:1872` and `:1875`. Worth stating exactly,
because the naive reading is wrong:

* against the repo root's working tree today, `merge.log` has **2043** lines and
  line 1872 is precisely the `MERGED origin/agent/s32-close-gate-gap` entry the
  claim describes — **the citation is correct**;
* against **the commit S34 shipped**, `merge.log` has **1862** lines, so the same
  citation is out of range in the tree that carries the claim.

An anchor into an append-only log is a moving target: correct against the
author's working tree, out of range in the commit, and it is the commit the
release manifest publishes. This is the same defect check F's docstring already
lists as *"the candidate set is the working tree, not the commit"*, one level
down — and it is the reason the count above is a measurement and not an
accusation. The third is `README.md:68` in P11's findings, where the file has 59
lines.

## What landed

* `PATH_TOKEN` and `CITE_TOKEN` capture the anchor in a named group instead of
  discarding it. The group is optional and not defaulted, so `if anchor:` is the
  whole test at every call site.
* `anchor_overruns(path, anchor)` returns `(last line named, lines in the file)`
  or `None`. A range is judged by its end; en dash and hyphen both parse, because
  the token class has always accepted both and a checker that understood only the
  hyphen would skip exactly those citations silently.
* check B reports `OUTOFRANGE` for the 8, and **does not** report it when the
  path itself is already a finding — two findings for one defect makes the counts
  disagree.
* check F reports it for the 14, and only when the bare name has exactly one
  candidate: with several there is no file to measure against, and picking one
  would invent a verdict.
* Both summary lines now say how many anchors were *read*. "0 out of range" and
  "no anchors seen" were the same green before this item, and separating those
  two is what the rest of this gate exists for.

## Verification

`papers: green` — `verify_paper: PASS (6/6)`, **184 tests** (was 171; 13 new in
`test_anchor_range.py`). Two mutations planted in the **live** tree, gate run,
tree restored clean:

| mutation | verdict |
|---|---|
| `` `engine-rig/STATUS.md:99999` `` (pathful) | `[FAIL] B` — "has 428 lines, so line 99999 is not in it" |
| `` `Theoria.md:99999` `` (bare filename) | `[FAIL] F` — "resolves to Theoria.md, which has 427 lines" |

The second is the one that matters: it is the half check B cannot see, and the
half that carries 14 of the paper's 22 anchors.

## What this does not do

* **It cannot catch P18's defect.** `:148` for a line at `:149` is in range and
  wrong. P19 measured the check that could and ruled against shipping it; that
  ruling stands, and `test_the_gate_does_not_claim_the_anchors_are_correct`
  pins the gate's wording so a future reader cannot take *in range* for
  *correct*.
* **The number of content-wrong anchors is still unmeasured.** P19 spot-checked
  two plus the P18 site. Nothing here changed that, and nothing here prints a
  sentence implying it did.
* **The run records are not gated**, per the measurement above. If that is ever
  revisited, the first thing to fix is not the gate but the anchors into
  append-only logs, which are wrong the moment they are committed.
