# CITECHECK 2026-07-30 — the binding citation audit of the current paper

```audit-stamp
target: papers/phase1-workshop/PAPER.md
sha256: 6b633fcc35ae612f20f4028eb45aaca1b6ed86a24eb1304af555c46228325376
lines: 3729
bytes: 237872
scope: full text L1-3729, as an index over five slice reports in runs/20260730T000000Z-P18-audits-cover-half/
status: binding
date: 2026-07-30
```

**What this file is, stated before anything else.** It is an **index**, not a
re-audit. The citation work it binds was done in five slice reports that are
already on disk under
`papers/phase1-workshop/runs/20260730T000000Z-P18-audits-cover-half/`. Every
number below is attributed to the slice file it came from. **Nothing here was
re-verified by the writer of this file**, with two exceptions that are stated as
such: the coverage arithmetic (line ranges, contiguity, the paper's own
sha/line/byte figures) and each slice's own sha/line/byte figures were recomputed
here. A reader who wants a finding's evidence must open the slice, which is why
each row names one.

**What it supersedes.** `papers/phase1-workshop/CITECHECK.md` — the same axis (a
path / number / quote audit against the binding rule) against the **first
assembled draft**: blob `4208b69c`, 1318 lines, 75,885 bytes, which is **31.9 %
of this text by bytes** and none of §7–§12. It is not withdrawn as wrong. Its
coverage expired; its stamp now says `status: stale` and names this file. Its
findings on the draft it read were not re-derived here, but every one of them was
reconciled finding-by-finding against the current paper in
`runs/20260730T000000Z-P18-audits-cover-half/delta-old-vs-new.md`.

**Measured state of the target** (recomputed in this worktree, not copied):
`papers/phase1-workshop/PAPER.md` = sha256
`6b633fcc35ae612f20f4028eb45aaca1b6ed86a24eb1304af555c46228325376`, **3729**
newline bytes, **237872** bytes. The old blob `4208b69c` is retrievable from
`PAPER.md`'s git history at exactly 1318 lines / 75,885 bytes, so the staleness
stamp on `CITECHECK.md` is measured against the blob rather than copied from that
file's own prose (which says "1319" — see the off-by-one note there).

**Rule under test**, unchanged across all five slices: *"Every quantitative claim
carries the repo-relative path of the artefact it came from."* Four passes — path
existence, number verification, orphan numbers, quote fidelity. Precedence: JSON
artefacts beat prose reports.

---

## Coverage map — which slice covers which sections

`assemble.py` prepends a 2-line banner and joins sections with `\n\n---\n\n`.
Every slice verified its own line mapping by regenerating `PAPER.md` from
`sections/*.md` in memory and comparing byte-for-byte; all five report the
reconstruction identical to the file on disk, all 13 sections matched at their
computed offsets.

| slice | PAPER.md lines | sections covered | section files |
|---|---|---|---|
| **A** — `citecheck-A-abstract-to-s3.md` | 1–908 | banner, Abstract, §1, §2, §3 | `00_abstract.md` (L3–148), `01_intro.md` (L152–487), `02_framework.md` (L491–624), `03_a0.md` (L628–905) |
| **B** — `citecheck-B-s4-to-s6.md` | 909–1668 | §4, §5, §6 | `04_a1.md` (L909–1104), `05_a2.md` (L1108–1449), `06_a3_transfer.md` (L1453–1665) |
| **C** — `citecheck-C-s7-to-s8.md` | 1669–2520 | §7, §8 | `07_battery.md` (L1669–2321), `08_exam.md` (L2325–2517) |
| **D1** — `citecheck-D1-s9-to-s10.md` | 2521–3197 | §9, §10 | `09_preflight.md` (L2521–2731), `10_adjudication.md` (L2735–3194) |
| **D2** — `citecheck-D2-s11-to-s12.md` | 3198–3729 | §11, §12 | `11_limitations.md` (L3198–3482), `12_related.md` (L3486–3729) |

**The cover is complete and contiguous, checked here rather than assumed.**
1 → 908, 909 → 1668, 1669 → 2520, 2521 → 3197, 3198 → 3729: each slice begins on
the line after its predecessor ends, the first begins at L1 and the last ends at
L3729, which is the file's newline count. **No gap, no overlap, and all 13
sections land inside exactly one slice.** The lines not inside a section file are
the 2-line banner and the twelve three-line `---` separators, and each is inside
some slice's range.

**All five slices audited the same object.** Each declares the target as sha256
`6b633fcc…25376`, 3729 lines, 237872 bytes, and each says it measured that rather
than inheriting it. So this is one frontier at one state, not five frontiers at
five states — which is the defect `COVERAGE.md` found in the pair being retired.

**The five slice files, as they stand right now** (recomputed here):

| slice file | lines | bytes | sha256 (first 8) |
|---|---|---|---|
| `citecheck-A-abstract-to-s3.md` | 810 | 70908 | `ce23f2a5` |
| `citecheck-B-s4-to-s6.md` | 536 | 48343 | `e9434905` |
| `citecheck-C-s7-to-s8.md` | 784 | 69933 | `f75e5289` |
| `citecheck-D1-s9-to-s10.md` | 607 | 58103 | `ff9066e1` |
| `citecheck-D2-s11-to-s12.md` | 706 | 54642 | `225be86e` |

Each of the five carries all four enumerated pass sections **and** a
"what this audit could NOT check" section — verified here by reading the heading
structure of all five, not inferred from file size. No slice carries an
in-progress marker, and that claim survives; the census beside it did not, and is
corrected here. `grep -rn "report in progress"` over the run directory returns
**four** hits in three files, not two: `citecheck-A-abstract-to-s3.md:806`, which
is the only one inside a slice and the only one that is "by one slice" —
`CLOSING-PLAN.md:42` and two inside `MANIFEST.json` are not slices at all. The
sentence also omitted the directory's other marker entirely: `[bib: TODO]` at
`citecheck-D2-s11-to-s12.md:89`, which appears only inside "Zero `[bib: TODO]`
markers remain in the slice", i.e. as the name of the thing being reported absent.
Neither hit marks unfinished work, so the load-bearing half stands — but a
miscounted census inside a stamp that is binding on a coverage claim is the same
defect this document exists to catch, and `MANIFEST.json`'s `completeness_check`
is now the more precise of the two records on this point.

---

## What the five slices found, aggregated

Every figure in this table is a **sum of five independently produced slice
counts**, each attributable to its slice. Read the caveats under it before
quoting any of them.

| pass | measure | A | B | C | D1 | D2 | total |
|---|---|---|---|---|---|---|---|
| A | distinct path-like tokens cited in the slice | 69 | 74 | 56 | 62 | 52 | 313† |
| A | resolve as written, repo-relative from the tree root | 62 | 69 | 53 | 53 | 45 | **282** |
| A | resolve only under a section-implied base | 7 | 3 | 1 | 9 | 3 | **23** |
| A | **do not exist anywhere in the tree** | 0 | 0 | 0 | 0 | 0 | **0** |
| B | numeric / field claims traced to a named file and checked | ~125 | ~130 | ~150 | ~150 | ~95 | **~650** |
| B | wrong, stale, mis-attributed, or absent from the cited file | 12 | 11 | 10 | 17 | 9 | **59** |
| C | quantitative claims with no artefact path at all | 8 | 7 | 11 | 10 | 9 | **45**‡ |
| D | attributed passages checked (blockquotes + inline) | 25 | 26 | 31 | 21 | 16 | **119** |
| D | inexact — paraphrase, compression, truncation, punctuation | 5 | 5 | 6 | 5 | 4 | **25** |

† **Not a whole-paper distinct count.** Each slice counted tokens distinct
*within itself*; a path cited in §3 and again in §7 is counted twice here. The
sum is an upper bound on distinct citations and a lower bound on citation
occurrences. Also non-additive in kind: slice B reports 2 of its 74 as extractor
false positives (not paths at all), slice C 1 of 57, and slice D2 breaks its 52
out further — 2 resolve only after restoring a dropped extension, 1 is an
ambiguous bare filename, 1 is absent by design and the prose says so; slice C
reports 2 that resolve only after shell brace expansion.

‡ Pass C and Pass B overlap by construction: slice A reports 5 of its 8 Pass C
rows also appearing under Pass B, slice B 1 of 7, slice C 1 of 11. So **45 is a
row count, not 45 distinct defects**, and at least 7 of the 45 are already inside
the 59.

**The one figure that is a genuine whole-paper result: zero broken paths.**
All five slices independently report 0 tokens that resolve nowhere in the tree.
Every path the paper cites points at something that exists. The rule's failure
mode across the whole paper is *base-relative citation* (23 rows) and
*uncited number* (45 rows), not dead links.

**Severity is only reported where a slice reported it.** Slice D1 classifies its
32 findings as **5 high / 8 medium / 19 low**. Slice D2 separately classifies 9
findings as flattering-direction, **4 of them high**. Slices A, B and C name
load-bearing findings individually but publish no severity tally, so there is no
whole-paper severity total here and one must not be constructed by addition.

---

## The load-bearing findings, per slice, as each slice names them

Each row is that slice's own characterisation. Open the slice for the evidence.

| slice | what it calls load-bearing |
|---|---|
| **A** (Abstract–§3) | Failure concentrated in **§1.2** — 5 of 12 Pass B and 4 of 8 Pass C rows, all of one kind: a number true in *some* battery file, attached to a different one (worst: B3, both halves of a disclosure parenthesis wrong). **B1**: §3.3's "from above, from below and from the right" is contradicted by the artefact's own `uncovered_pairs`, which make the third *from the left* — the paper is faithful to a source that is wrong. **B2**: a parenthetical staleness warning that is itself stale (5704 vs the artefact's 5284). The draft-status box's "roughly 27 500 words" is **36 242** by the paper's own generator. Slice A also **withdraws** a finding asserted by the stub it replaced: the §1.2 five-family split is correct in the file it cites, field for field — the defect did not exist. |
| **B** (§4–§6) | Failure concentrated in **§6**, where the paper stops naming the artefact and trusts `A3_REPORT.md`: 5 of 11 Pass B and 6 of 7 Pass C rows are there, and §6.3's negative-control table — the one table whose job is to show the safety valve is real — carries four figures appearing in no file the paper cites. Three load-bearing: the "35-line diff" a reader gets 20 lines for (B1); a first-plan comparison that silently swaps arms inside a "like-for-like" subsection (B2); §6.3's uncited 13/8/891 (B4/C1). §5 survives sustained pressure — the 163/220 denominator, the 52-line Lean diff and the `first_error` truncation all reproduce. |
| **C** (§7–§8) | **§7 survives better than its length suggests** — the §7.7a blind-round narrative, the 0.125/0.25 power floor, the 32-cluster de-redundancy result, the 257-of-703 pair coverage and all three pile digests reproduce exactly, and six places where §7 overrides one of its own sources all hold. Failure concentrated in **§8**: 4 of 10 Pass B and 4 of 11 Pass C rows in 193 lines, all four §8 Pass-B rows the same defect — reproducing an `exam/` self-description the `exam/` tree has overtaken, while citing the artefact that overtook it. Load-bearing: **B1** (a hole reported open that the cited JSON records closed), **B3/B10** (a cheater round the paper says never happened, whose results are in `exam/artifacts/`), **D1** (an italicised sentence attributed to "the directory" that exists nowhere in the repository). §8 names `exam/STATUS.md` zero times while quoting it three times. |
| **D1** (§9–§10) | First audit ever to read these sections. **§9's arithmetic is in unusually good shape** — essentially every number in §9.1/§9.2/§9.4 reproduces exactly, including the $6.317658 / $5.795338 disagreement, the 116 470 cache-creation tokens, the 83.6 % attribution and the 66/65 bypass ledger; §9's failures are citation-shaped. **§10** has extraordinarily accurate internal census arithmetic but a staleness cluster at §10.2 (`worldgen/core/truth.py` "byte-for-byte unchanged on the mainline", "13 of 35" → 0 of 35, and two quoted strings — all three high), plus §10.4's `scope_exhaustive`/E15 (high) and a paraphrased `proxy/DECISIONS.md` blockquote (high). |
| **D2** (§11–§12) | First audit ever to read these sections. Almost nothing is cited to the wrong base; the limitations-section failure mode is different and present in quantity: **§11 is systematically blind to §6 (A3) and §9 (the live chain)** — neither section, report nor incident is named anywhere in §11 — and §11.5's closing sentence disclaims "the bill shape, transfer, the exam, the cost magnitude" as unevidenced while §6.2 is headed *The bill*, §6 is transfer, §8 is the exam and §9.4 reports live spend. Four disclosure clauses are materially weaker than the artefacts they cite (§11.1(d) omits `CONTRACTS/dsl_grammar_v0.3.md`; §11.4 reports one of seven pre-registration defects; §11.1(f) grades nothing; §11.2's premise is a `CLAUDE.md` sentence deleted 33 hours before). §12: **65 / 65 bibliography keys resolve** in `references.bib`; its 67 external claims are classified 22 checkable in-repo / 30 unverifiable offline / 15 not falsifiable as stated. |

---

## Independent row-level verification of the slices — and where it stops

`runs/20260730T000000Z-P18-audits-cover-half/row-sample-audit.md` (540 lines) is
a separate, read-only re-verification of individual **rows** inside the slices —
testing whether they are true, not whether they are present. Its declared result:

* **31 of 31 sampled rows hold. 0 wrong, 0 overstated, 0 unverifiable**, plus 9
  further rows checked opportunistically, all holding. Draw: A 9, B 8, D1 7,
  D2 7, deliberately weighted toward rows the slices call load-bearing or high
  and toward the *confirmed-correct* rows (where a false confirmation is the more
  dangerous error, since nothing downstream re-checks it).
* **Cross-slice consistency: no disagreement found** on the five artefacts more
  than one slice reads (`v9_gaming_audit.json`, `gaming_audit.json`,
  `loop_ledger.json`, the first-contact `MANIFEST.json` cost block,
  `capability_spectrum.json`).
* Its own judgement: the slices are "sound enough to carry a `binding` stamp",
  conditional on one count being restated — see the next section.

**GAP, stated because it bears directly on this stamp: slice C was not sampled.**
The row-sample audit drew from A, B, D1 and D2 only, because C was still being
rewritten when the sample was drawn. So §7 and §8 — PAPER.md L1669–2520, 852
lines including the 653-line battery section the abstract calls the strongest
result — are **covered by a complete slice that no second reader has spot-checked
at row level**. That is a gap in verification depth, not in coverage: slice C
exists, is complete, enumerates all four passes and states its own limits. But it
is the one fifth of this stamp resting on a single author.

> **CLOSED.** `row-sample-audit-C.md` is the missing draw, same declared method:
> **42 rows, 42 HOLD, 0 WRONG, 0 UNVERIFIABLE**, none dropped, with every Pass B
> finding and every Pass D row taken entire rather than sampled, and the
> confirmed-correct rows recomputed from bytes rather than inspected. The
> abstract's strongest result was the highest-priority row and did not move. So
> §7–§8 now rest on two readers, and the second moved nothing.
>
> Three corrections it produced, none of which touches the cover:
>
> 1. **A defect in the gate, not in the slice.** Gate E's ruling for §8.4 says the
>    handover reports are "cited one block above". They are cited in block [12];
>    the ruled block is [24], ~76 lines earlier, with all of §8.3 between. And a
>    ruling clears its whole merged block, which `_blocks()` merges the six-bullet
>    §8.4 list into — so it also exempts slice C's B2 (high), B3 (high), C9 and
>    D1. §8's only two uncited quantitative blocks are both ruled, so a green
>    `E UNCITED` says nothing about §8.4. This is the defect gate F already records
>    against itself: a ruling whose stated evidence is false, which nothing checks.
> 2. **This index's Pass A figures for C are one low.** 57 distinct citations, not
>    56; 54 resolve as written, not 53 — so the 313 and 282 aggregates are each one
>    low too. The missing token is `.gitattributes` at PAPER L2316, which slice C's
>    extractor did not classify as path-like although the slice *did* open the file
>    and read it correctly. Recorded rather than silently bumped, because every
>    figure in the table above is attributed to the slice that produced it, and
>    editing a slice's number in this index would break that attribution. **"0
>    broken paths" is unaffected and was re-checked over every path in the span,
>    not a sample.**
> 3. §7 carries **three** gate-E rulings, not four. Of the five in slice C's span,
>    three hold in full, one has a stale locator ("four lines above" is fifteen,
>    the paragraph having grown after the ruling was written), one is item 1 above.

---

## Known defects in the surrounding run record, not fixed here

Recorded because a binding stamp should not quietly inherit them. Both are
findings 2 and 3 of `row-sample-audit.md` §*Findings outside the sample*:

1. **`MANIFEST.json`'s `slice_state_note` and `stub_census` are stale about slice
   A**, describing it as a stub while its own `citation_slices` entry reads
   `complete`. Harmless to a reader of the whole file, misleading to a grep.
2. **Slice B's closing paragraph is stale about slice A** ("ends after Pass A, 77
   lines") — true when B was written, false now (A is 810 lines with all four
   passes). Superseded by this paragraph rather than edited, per the
   append-only-once-published convention.

Three line anchors inside the slices are off by one or two (slice A's
`omnibus_manual` docstring, slice D1's `_(**unverified** — %s)_` emission and
`Law.as_json` guard); the sampler confirms every one opens on the right content
within two lines. None is load-bearing.

**Struck from this list, and the error was this index's own: the `MANIFEST.json`
row-count defect — the sampler's finding 1 — was closed before this index
existed.** Checked in git rather than taken on trust. `completeness_check`
asserted "A 73 rows, B 57, D1 73, D2 65" as the checked property behind `state:
complete` through commit `cedb099a`; commit `f3edfacc` removed that assertion,
added the `row_counts_were_wrong: "CORRECTED. …"` field in which the retired
string survives only as a historical citation, and made `completeness_check` end
*"The row counts are now emitted by count_rows.py under the stated rule rather
than asserted."* The commit that added this index, `c100e7ce`, is two commits
later and shipped over that already-corrected manifest. The first version of this
section therefore reported as open a defect its own run had closed, and quoted the
fixed manifest's historical citation as though it were the live claim.

It also understated the defect and denied a fix that is committed beside it.
**Two of the four asserted numbers were wrong, not one.** A's 73 was the raw
pipe-line count *including* the 7 GFM separator rows (66 + 7 = 73), and **D2's 65
was off by one** — D2's true count is 66; the missed row is an indented table row
at `citecheck-D2-s11-to-s12.md:550`, which `^|` does not match but "stripped form
starts with `|`" does. Only B (57) and D1 (73) reproduced. And **one mechanical
rule does yield all of them**: `runs/…/count_rows.py` implements it — a row is a
line whose stripped form starts with `|`, excluding fenced code blocks and GFM
separator lines, header rows counted — and gives **A 66, B 57, C 70, D1 73,
D2 66 = 332**, the total `citation_axis_coverage` states, or 59 / 50 / 62 / 64 /
58 = 293 excluding headers. `python count_rows.py --check` exits **0** with
"ok -- every manifest row count reproduces under the stated rule", run here, not
read. So "no single mechanical rule yields all four" was true of the four numbers
as `cedb099a` asserted them, and is false of the run record as it stands.

This changes nothing about the stamp, which is the point of saying it out loud:
this index still does not cite row counts as its evidence of completeness — it
uses the line-range contiguity check and the heading-structure check above, both
recomputed here. What is removed is an overstated defect, not a support.

---

## What this audit could NOT check

Each slice states its own limits in full; this is the union, compressed, and it
is the honest ceiling on the coverage claim above. Do not read a `binding` stamp
as more than this.

1. **Nothing was executed.** No `lean` invocation, no `pytest` run, no
   `battery/run_battery.py`, no exam rebuild, no figure regeneration. Every
   green/red/axiom-list/pass-count verdict in the paper was read from the
   artefact that records it, not re-derived (slices A·1, A·2, B·1, B·2, C·1, C·2,
   D2·5). **A stale artefact passes this audit unchallenged** — and slice A's B2
   is proof that artefacts in this tree do go stale.
2. **Figure plates were not compared to their CSVs or their pixels.** Paths were
   resolved and CSV rows read; no plate was regenerated and the `figures/` source
   registry was not resolved (A·4, A·5, B·3, B·5).
3. **Sealed-pile material was never opened, by rule** — which makes two universal
   claims unverifiable in principle: §7.10a's "no arm in this repository has
   completed a level" and §7.1's "zero sealed-pile reads" were checked as far as
   a reader inside the cut can go (C·4). Slice D1 explicitly chose the discipline
   over completeness on one sweep and recorded the gap. `environment_files/` was
   never touched. `arc-recon/data/piles.json` was hashed, never read (C·5).
4. **30 of §12's 67 external claims cannot be checked offline at all** (D2·1) —
   zero-network is a hard constraint. What was checked is the in-repo *record* of
   the external verification (`search-traces/line*.md`, two audit samples,
   `references.bib`), which confirms a two-source procedure ran; it cannot confirm
   that any external work says what §12 says it says. `brooks2024sora` is open
   even for the repo's own auditor (403).
5. **The §10 census originals are unreachable.** They are untracked files in
   another worktree, on no ref; §10 was audited against the `inputs-verbatim/`
   byte copies, and that the copies are byte-identical to the originals is taken
   on trust (D1).
6. **Large cited sources were read only where a claim pointed into them** —
   `exam/STATUS.md` (1121 lines), `battery/PREDICTIONS.md` (603), `battery/METRICS.md`,
   `battery/BLINDING.md`, `battery/STATUS.md`, `cold-start-a3/A3_REPORT.md`,
   `cold-start-a2/THEORIZE_LOG.md`. A contradiction sitting in an unvisited
   paragraph of any of them would not appear anywhere in this audit (A·8, B·8,
   C·7, D2·7).
7. **The `~` in Pass B is a count of claims a file was opened for, not a claim of
   exhaustiveness** (C·8). Arithmetic the slices treated as derived rather than
   cited was checked but not counted.
8. **Several findings are adjudications, not audit results, and are left open** —
   whether the two acceptance reports may be corrected at source (A·6), whether
   "exercised by a result in this paper" excludes a `theory-compiler` sprint row
   (D2·3), whether "no cost comparison between arms" survives §9.4 and §7.2's E4
   (D2·4). Each slice states what each file says and stops.
9. **`scope` is prose, and check G does not verify it.** `audit_stamp.py` says so
   in its own gaps list: G pins *when* an audit ran, not *how much* it read. The
   coverage claim above is therefore load-bearing on the contiguity table, which
   is why that table was recomputed here rather than copied.

---

## Disposition

The 59 Pass B and 45 Pass C rows are, with few exceptions, writing fixes and
re-transcriptions against artefacts that already exist. **Writing paper body text
is not this run's remit** (`monitor/CHARTER.md`), so the findings are located and
handed over, not applied. Locating them was the job; editing them is not.

Nothing outside this file and `CITECHECK.md` was modified to produce this index.
No network call, no API call, no game spend, no sealed-pile read.
