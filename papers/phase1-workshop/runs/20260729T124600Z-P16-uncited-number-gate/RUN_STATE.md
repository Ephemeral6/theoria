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

## Verification

```
verify_paper.py                 PASS (5/5)   — 327 blocks, 0 uncited, 8 ruled, 0 stale
test_uncited_gate.py            45 passed
mutation_check.py               PASS — 12/12 caught
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

It reads a **block**, not a sentence: a paragraph with one path and six unrelated
numbers passes. That is deliberate — sentence granularity flags every subordinate
clause and gets the gate switched off — but it means the check proves *provenance
is present*, never that the path is the right one for the number. Nothing here is
a substitute for opening the artefact, which is how both wrong numbers in this
run were actually found.

The 8 rulings are the check's own attack surface. They are printed on every run
for exactly that reason.
