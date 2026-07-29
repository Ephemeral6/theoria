# P16 — check E: the binding rule finally has an executor

`prompt_id` P16-P16-uncited-number-gate · branch `agent/p16-uncited-number-gate`
· base `9bc8c880` · RES-2 · zero API calls, zero sealed-pile contact.

## What was wrong

P15's adversarial pass caught a paragraph with six quantities, zero paths, and
two numbers that could not be reproduced — while `verify_paper.py` reported
**PASS (4/4)**. The gate was not broken. Check B asks "does every *cited* path
resolve?", so a claim that cites nothing at all is invisible to it: **uncited and
cited-correctly were the same green.** The paper's central discipline — every
quantitative claim in the body carries a path — had no executor.

## What check E is

`check_uncited` splits each body section into claim blocks, strips the tokens
that are structure rather than measurement (section refs, figure refs, versions,
coordinates, vectors, shas, dates, identifiers, complexity classes), and fails
any block that still holds a quantity but resolves no repository path. Numerals,
spelled-out numerals, money, percentages, ratios and magnitude words all count as
quantities. `00_abstract.md` is the one declared exemption, because the paper
declares it.

False positives are handled the way this repository already handles them
elsewhere (`figures/`'s `KNOWN_DISAGREEMENTS`): a table, `ADJUDICATED_UNCITED`,
keyed by a verbatim anchor from the claim, each entry carrying the reason the
number needs no path. **The reasons are printed on every run.** A ruling whose
anchor no longer matches anything goes stale and fails the check, so rewriting a
ruled sentence retires its ruling rather than silently inheriting it.

## First run: 23 uncited across 12 sections

Triaged one at a time. The split:

* **7 real citation holes** — claims whose provenance existed and was never
  written down. Fixed by adding the path, in sections 3, 4, 6, 7, 8, 9 and 10.
* **2 wrong numbers**, found only because fixing the citation meant opening the
  artefact:
  * §7 — "seventeen reachable delta values" is **thirty-three**;
  * §7 — "thirty clusters" is **thirty-two**.
* **1 wrong number and 1 hole in the same block** (§4.4, found on the second
  pass after magnitude words were added to the vocabulary): the paragraph
  asserts what the Lean generator's docstring says and what its emitted banner
  concedes, and cited neither. The docstring is at
  `theory-compiler/src/theory_compiler/generators/gen_lean.py:722-724` and the
  concession at `:786` — **62 lines apart, not "a dozen"**. Both the path and
  the corrected distance are now in the text.
* **4 blocks ruled** on first triage, **4 more** after the sections 8–10 pass —
  8 entries in `ADJUDICATED_UNCITED`, each with its reason in the table.
* **2 classifier defects** the triage exposed, fixed rather than ruled:
  * a **brace-path blind spot** — `arm/artifacts/{a0,a2}/episode.jsonl` is one
    token citing three siblings, and *both* check B and check E were blind to
    it. Now expanded, and every sibling must resolve;
  * the `commit-sha` class `[0-9a-f]{7,40}` ate any 7-digit quantity, so
    "1750000 cache tokens" read as a hash and vanished. It now requires at least
    one `a-f`.

## The adversarial pass, and what it broke

Four evasions landed, all four are closed and all four now have controls:

1. **A ratio cited itself.** `` `233/236` `` has a slash, and `_mark_citations`
   treated any backticked token containing a slash as a path. A backticked
   fraction was its own provenance. Check B already knew better (`NOT_A_PATH`);
   check E now uses the same exclusion.
2. **An invented filename passed.** Check B skips bare filenames by design, so
   for `` (`ledger_summary.jsonl`) `` — a plausible name for a file that does not
   exist — E accepted the suffix and B never saw the token: a citation *nobody*
   checked. E now requires the basename to exist somewhere in the tree. It is the
   weakest test that still costs an inventor something, and it is free: all 34
   distinct bare filenames the sections cite already exist.
3. **A one-character ruling silenced the paper.** `" "` is a substring of every
   block, so a single entry `("07_body.md", " ")` ruled all 327 of them and
   reported **no** stale rulings. The escape hatch was one character wide and
   nothing said so. `MIN_ANCHOR = 24` now rejects it; the eight live anchors run
   34–47 characters, so the floor cost nothing.
4. **An unclosed code fence hid everything after it.** `_blocks` skips fenced
   content, so one stray ``` ``` ``` parks the rest of a section where the
   scanner never looks. Sections are now checked for balanced fences.

## Second pass: the fence counter was inverted

Writing the controls for (3) and (4) found that the fence check itself was
wrong. It counted `"\n```"`, which misses a fence on line 1 — so a **balanced**
section opening with a fence failed, and an **unbalanced** one opening with a
fence passed. Exactly backwards, and the only reason it looked fine is that no
section currently opens with a fence. It now counts with the block splitter's own
predicate.

This is the run's second instance of one shape: **a defence added without a
control is a defence nobody has watched work.** The first was in the mutation
file itself (below).

## The second adversarial pass, and the check it broke that mattered most

A second adversary was run against the changed gate. It landed **14** evasions.
Six were fixed, one turned out to be a bug in a *different* check, and the rest
are recorded as limits rather than quietly dropped.

**The one that mattered: check B could not see a line-anchored path at all.**
`PATH_TOKEN` had no `:\d+` tail, so `` `foo/bar.md:3` `` never matched — and a
path check B never matches is a path it never resolves. Check E accepted the
token as a citation, check B never saw it, so **adding a line number to a
citation was a way to stop it being checked**. This is the P16 defect exactly,
one check over: for line-anchored paths, *invented* and *resolves-correctly*
were the same green.

It was not hypothetical. The citation this run added an hour earlier —
`gen_lean.py:722-724` — was itself unvalidated. Fixing `PATH_TOKEN` raised the
paper's checked citations from **207 to 213** and immediately found **2 broken
paths** in §10 that had never been resolved by anything: `cegis_miner/miner.py`
and `probe_frontier/reach.py`, both missing their `engine-rig/engines/` prefix
while the third file in the same sentence carried it. Both fixed.

The other five fixed:

* **A ruling could silence several blocks.** `MIN_ANCHOR` guards length, not
  genericity: a 47-character anchor of boilerplate ruled three distinct uncited
  blocks and reported nothing stale. A ruling is written about *one* claim, so
  it must now match exactly one.
* **Leading-dot decimals were unreachable.** `.562`, `p = .003` — the standard
  way to write an effect size, and the lookbehind made every digit in them
  invisible.
* **A unit turned a measurement into a name.** `` `41s` ``, `` `1.4GB` ``,
  `` `4.7x` `` were erased whole by the branch meant for `cost.delta_usd`.
* **The binary-label exemption ate powers of ten.** `[01]{5,}` matched
  `100000` and `1000000` — which are exactly the context budgets this paper
  quotes. Narrowed to the board's five cells. Residual, stated in the code and
  pinned by a test: `` `10000` `` is a genuine label here and cannot be told
  from ten thousand inside backticks.
* **`frame-index` ate numbers after contractions.** `\bt` matched the `t` in
  `wasn't`, so "the regression wasn't 40 percent" was read as frame index 40.

Two more were closed after checking the cost empirically rather than guessing:

* **Headings were never scanned** — `_blocks` skipped past them without ever
  emitting their text, so `## Repair recovers 38 percent of failed arms` was a
  result stated where nothing looked. Naively scanning them flags **87**
  headings for carrying their own section number; stripping that number first
  leaves exactly **2**, both summarising a cited claim below, both ruled. 327
  blocks → 414.
* **Fractions and multipliers** — "a factor of three", "double the baseline",
  "a third of" — carry a result with no digit in it. Measured before adding:
  **zero** new flags on the current draft.

`ARTEFACT_SUFFIX` also gained `.log .png .pdf .tex .tsv .ipynb .pddl .lock`,
which were false positives: a real artefact type missing from the list meant a
properly cited claim got flagged, and a gate with false positives is a gate that
gets switched off.

## Verification

```
verify_paper.py                 PASS (5/5)   — 414 blocks, 0 uncited, 10 ruled, 0 stale
                                             — 213 path citations, 0 broken
test_uncited_gate.py            62 passed
mutation_check.py               PASS — 21/21 caught
```

`test_uncited_gate.py` is check E's negative control: every evasion the work item
names, plus the four the adversarial pass found, plus 13 false-positive cases
that must *not* fire.

`mutation_check.py` breaks check E twelve ways and asserts the suite goes red for
each. It was 8, and on rerun one of the eight came back **PATTERN NOT FOUND** —
the fix it was written against had been rewritten, and a mutation that cannot
find its target reports nothing rather than failing loudly. Repointed, and
extended by the four defences that had no mutation on them: ratio self-citation,
invented basename, the anchor floor, the fence balance.

## What check E does not do

Six known gaps are listed in `verify_paper.py`'s own docstring, each reproduced
against the live scanner and left open deliberately. The two that matter most:

It reads a **block**, not a sentence: a paragraph with one path and six unrelated
numbers passes. That is deliberate — sentence granularity flags every subordinate
clause and gets the gate switched off.

And **any real path satisfies the block**. The check proves *provenance is
present*, never that the path is the right one for the number. Nothing here is a
substitute for opening the artefact, which is how all three wrong numbers in this
run were actually found.

The 10 rulings are the check's own attack surface. They are printed on every run
for exactly that reason.

## What this run says twice

Three times, in fact, at three levels, and it is the transferable finding:

| level | the thing with no control on it | how it was actually broken |
|---|---|---|
| the paper | a quantitative claim with no path | P15, by hand, expensively |
| the gate | four fixes added without tests | the fence counter was inverted |
| the controls | a mutation whose target was rewritten | it reported PATTERN NOT FOUND, silently |

**A defence added without a control is a defence nobody has watched work**, and
at every level the failure was invisible in the same way: the thing reported
green, because the case that would have made it report red was never run.
