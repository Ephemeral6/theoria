# P18 — the audits covered a third of the paper, and nothing said so

Two workers. **W-1690** (2026-07-30, from base `50e10617`) did the measurement,
built the gate, and wrote the referee pass. It died before committing any of it
except one commit, and never pushed that one. **RES-3** picked the disk up at
04:22Z after the board's sweep released the claim, and is finishing it.

The ruling and the coverage arithmetic are in `COVERAGE.md`; the durable
convention is check G in `papers/phase1-workshop/audit_stamp.py`, whose module
docstring is the design record. This file is the narrative.

## What was found

`CITECHECK.md` and `REVIEW.md` both pin `PAPER.md` at commit `4959df1c` — sha
`4208b69c`, 1318 lines, 75,885 bytes. The paper is now 3729 lines / 237,872
bytes. So the standing audits cover **31.9% by bytes**, and §7–§12 had never
been read by any audit — including §7, the 653-line metrics battery the abstract
calls the strongest result.

Three corrections to the board item that commissioned the work, all in the same
direction, all in `COVERAGE.md`: it is under a third rather than a half; the two
audits are one frontier rather than two (same blob, same day); and "1319 lines"
is an off-by-one that is exactly why the stamp fixes `lines` to newline-count.

The staleness was not merely unrecorded — the paper's own front matter asserts
the opposite in the present tense, directly beneath the rule it is offered as
evidence for (`PAPER.md:26-31`).

## Where W-1690 stopped

Committed (`0efb51c4`): `audit_stamp.py`, the check-G wiring in
`verify_paper.py`, `COVERAGE.md`, `delta-old-vs-new.md`, citecheck slices A and
C, and a 46-line stub of the referee pass.

On disk, uncommitted, and therefore one power-cut from gone:

* the referee pass grown from that stub to its finished 602 lines — 13 findings,
  6 blocking, ending in a summary table. Complete, not truncated.
* `test_audit_stamp.py`, 45 tests over G1–G8.

Its branch was never pushed. That is the defect its own neighbouring commit
`5e245532` (S36) defines a gate for, and the reason this section exists rather
than a note saying "picked up cleanly".

## What RES-3 changed, and why

**1. `test_a_binding_stamp_with_the_wrong_byte_count_fails` did not test G4.**
It stamped `bytes: cur_bytes - 400` on a 238-byte fixture, so the stamp read
`-162`, and G2's `isdigit()` rule refused it as malformed before the G4 byte
comparison ever ran. The test asserted only that *something* failed, so it was
green on the wrong finding — a test passing through the gate it was written to
exercise. Now stamped `cur_bytes + 400` (the overstatement direction, which is
the whole of P18), and it additionally asserts G4's "sha256 matches" clause,
which only G4 prints — so it cannot silently drift back to a G2 pass.

**2. Added `test_a_negative_byte_count_is_refused`.** The negative case was real
behaviour that nothing asserted. Left unpinned, the day `lines`/`bytes` moved to
a signed parse, `-162` would have become a G4 *mismatch* finding — reported to
the reader as drift in the paper rather than as a malformed stamp.

**3. Dropped `_tmp1.txt`.** W-1690 committed a 143-line scratch file and then
staged its deletion. It is the raw output of a quote-exactness scan, nothing
cites it, and no script in the run reproduces it — so it cannot be re-derived
and cannot be attributed. Kept the deletion rather than promoting an
unattributable artefact to a named one: the findings it supports are stated in
the referee pass with their own line references.

## Closing the referee axis

The referee pass was written into `runs/`, and a report under `runs/` cannot
supersede anything: check G scans `papers/phase1-workshop/` only, and G6 resolves
`superseded_by` as a filename in that directory. Reports under `runs/` are
provenance — pinned by a MANIFEST, historical by construction. A *live* audit has
to sit where the README and the board look for it.

So `review-2026-07-30-full.md` was **moved** (not copied) to
`papers/phase1-workshop/REVIEW-2026-07-30.md` and stamped `binding`. Moved rather
than copied deliberately: two byte-identical audit reports in two directories is
the drift this territory already has a receipt for — a README pointing at a
60-world smoke run while the real 3000-world artefact sat elsewhere, and the
reader's check succeeded against the wrong object (board item V26).

`REVIEW.md` is stamped `stale`, `superseded_by: REVIEW-2026-07-30.md`, pinning
the blob it really audited: `4208b69c`, 1318 lines, 75,885 bytes, measured out of
`4959df1c` rather than copied from its own prose. Its findings are not withdrawn;
its coverage is what expired, and the file now says so above its own first
paragraph.

The gate now prints the thing the item asked for:

```
ok  REVIEW.md -- stale, pinned @ 4208b69c (31.9% of PAPER.md as it now is),
    superseded by REVIEW-2026-07-30.md
```

## State

Check G is **red on purpose** as of this writing, and now on one report rather
than two: `CITECHECK.md` has no stamp (G1). Its successor cannot be written until
the citation axis actually covers the paper — slices A (L1-908) and C
(L1669-2520) exist; **B (§4-§6, L909-1668) and D (§9-§12, L2521-3729) had never
been citation-audited by anyone** and are running now. Stamping `CITECHECK.md`
stale before its successor exists would be G5/G6 — retiring an audit into
nowhere, which is the one thing the gate refuses outright.

That the referee axis went green in two edits and the citation axis needs real
work is itself the finding: a referee pass can be redone by one reader in one
session, and a citation audit cannot.

`test_audit_stamp.py`: 44 passed, 1 xfailed. `verify_paper.py` exits 1 — the
verdict is wired to the exit code, checked directly rather than through a pipe
(`$?` after a pipe reads `tail`, which is how a red gate reads green).

## Open, and deliberately not done here

The 13 findings of the referee pass are, in its own words, "every one a writing
fix or a re-transcription against an artefact that already exists". **Writing
paper body text is RES-2's exclusive remit** (`monitor/CHARTER.md`), so they are
handed over rather than applied. Six are blocking, including a self-contradictory
abstract — the item asked for those kill shots and they are found and located;
what is out of bounds is only the editing.

## 2026-07-30, RES-3 cycle 105 — the ruling that checks the rulings

### Recovered, not redone

The previous session died with 265 uncommitted lines in `verify_paper.py` and no
run record of them. They were found in the working tree, not reconstructed. This
section is written after the fact for that reason, which is itself the argument
for writing as you go: the reasoning behind those lines had to be re-derived from
the diff, and one of the two things it turned on (why the fixture below must put
the list directly under a heading) was not recoverable from the code at all.

### What it does

`locator_findings()` scores the one part of a ruling that is a fact rather than a
judgement. A ruling exempts a block from check E or F on the strength of a prose
justification, and several justifications say "cited one block above". Whether
§8.4's bullets *ought* to need a path is a call somebody has to make; whether the
handover reports are one block above is not — it is true or false, and it was
false. The function parses the distance, resolves the target block, and checks the
named artefact is in it. An invalid ruling is dropped **before** the scan rather
than merely reported, so its block reports UNCITED. Reporting alone would have
left the block silent, which is the whole defect.

It also reports a ruling that states a distance and names no artefact. That is not
pedantry: "cited one block above (one report per tier, both named there)" names
nothing a check can look for, and both entries written that way were wrong.

### Measured, because it decides whether this ships

| | check E | verify_paper |
|---|---|---|
| without the change | PASS | **PASS 7/7** |
| with it | FAIL | **FAIL 1/7** |

Confirmed by stashing the change and re-running, not by reading the code. **This
turns a green territory red**, and it lands anyway, because the green was false:
§8.4's 18-line six-bullet list cites no artefact anywhere in it and was exempted
whole by a ruling whose one factual assertion was untrue. `BROAD` could not see
it — merging makes six bullets one block, so the ruling matched exactly one block
and looked well-scoped. A false green is worse than a red gate.

The red is **true and deliberate**, in the sense S29 separates: the territory is
genuinely uncited there, the gate is not misfiring. It is announced on the bus so
a merge-queue triager does not spend a cycle re-deriving it.

### The fix is not mine to make

Closing it means citing or re-wording paper body text, which `monitor/CHARTER.md`
reserves to RES-2. Handed over rather than applied — the same boundary this run
already recorded for the referee pass's 13 findings.

### `test_locator_gate.py` — new, 11 cases

The mechanism shipped with no test; the agent that wrote it died before running
one. Controls for both shapes that actually occurred (locator points at the wrong
block; locator names nothing), for the quiet cases that must stay quiet (a true
locator, a ruling with no distance at all, a stale anchor that the STALE rule
owns), and for the wiring — that an invalid ruling's block really does get scored
rather than merely complained about.

Two facts about `_blocks` are load-bearing in the fixture and both were got wrong
on the first attempt, which is worth recording because they are invisible in the
source:

* **A list is merged into the prose chunk above it.** The first fixture put a
  paragraph between the heading and the bullets; the two fused, the ruled block
  stopped being the list, and four tests failed. The real §8.4 list is its own
  block only because a heading terminates the chunk.
* **A heading is a block.** So "one block above" the §8.4 list resolves to the
  §8.4 heading, which cites nothing — verbatim the shipped defect.

The last test runs `locator_findings` over the *live* `ADJUDICATED_UNCITED` and
`ADJUDICATED_BARE` and asserts it is empty. It passes, which is the evidence that
all three false locators are now corrected or withdrawn. It is also the test that
keeps catching the next one: a locator decays with the prose around it, silently
and by default. "Four lines above" became fifteen when the paragraph above grew,
while the block it meant never moved — which is why locators here are
block-relative now.

**Suite: 270 passed, 1 xfailed** (259 + 11).

### The §8.4 evidence check, and the gate that does not exist

`section-8-4-evidence-check.md` in this directory. All three assertions in the
withdrawal comment hold, and it found a fourth stale bullet the comment never
named. The serious one is not staleness:

**§8.4 carries a fabricated quotation.** "In the directory's own words: *the leaks
that remain are the ones nobody has looked for yet*" — that sentence exists in no
file under `exam/`, on no branch, at no commit. Verified independently rather than
taken on report: repo-wide it appears only in the paper itself and in the audit
reports discussing it, and its earliest appearance anywhere is `579d0385`, the
very commit that wrote the bullet attributing it to the directory. Slice C's
row-sample audit had already flagged it, which is corroboration and not a second
source. The real sentence it approximates (`exam/STATUS.md`, "a cheater pass is a
sample, not a proof") says something materially different and is itself inside the
struck-through version of that weakness.

**No gate can see this, and the reason generalises.** Check E scores a block on
whether it carries a resolvable artefact path, and it only looks at blocks
asserting a *quantity*. A fabricated quotation contains no digit, so it never
enters E's scan surface at all; F only adjudicates ambiguous bare filenames. The
paper can therefore attribute a sentence to a source that never contained it and
go green on all seven checks. That is a hole of a different shape from the one
this run has been closing: not "the ruling exempting this block is false" but
"nothing ever looked at this block".

A second shape came out of the same four bullets. Two of them were **true when
written** — the paper bullet landed 2026-07-28 17:41, `exam/STATUS.md` struck the
sentence at 19:31, and `08_exam.md` was edited twice more the next day without
anyone refreshing them. So the defect is not authorship but decay, and it is
silent: no edit to either file announces that the other has moved.

Both belong in one item — a quotation check keyed on attribution rather than on
digits, plus a rule that a citation of text now inside `~~...~~` (or of an entry
marked `Closed by` / `Superseded by`) goes red. Written up as **V28** and
deliberately *not* filed yet: `board.py assign` refused it at the three-item
self-supply cap, and the cap is right — my two outstanding self-supplied items
(V2, V27) are both territory-blocked behind this very branch's claim on `exam`,
so the way to file V28 is to deliver, not to stockpile. Recorded here so the cap
does not cost the finding.

Boundary: everything above is a handover. The fix to all four bullets is body
text, which `monitor/CHARTER.md` reserves to RES-2; the six-bullet citation table
in the evidence check names a real tracked artefact for every bullet except the
fabricated quotation, where the fix is deletion.

### Adversarial review of the mechanism, and three fixes

`adversarial-locator-review.md` in this directory. Nine defects, and the exercise
was worth more than the code it audited: the mechanism was written in one pass by
a session that died before running it once.

**D1 (HIGH), fixed.** `_ruling_paths()` harvested every backticked path in the
whole justification and `locator_findings()` accepted the target block if **any**
of them was in it. So a ruling's contrasts and its own `(Corrected …)` notes
supplied decoys — and a correction note by construction describes what is at the
*wrong* place. The reviewer demonstrated it with one word changed in a shipped
entry: `08_exam.md`'s "0.000" ruling, `two blocks above` → `one block above`,
passes on `Theoria.md`, which its own note names as the only citation in the block
one above. **The note written to document the bug was concealing it.** The more
careful a ruling's prose, the more decoys it supplied — the mechanism was weakest
exactly where the writing was most conscientious.

Fixed by cutting correction notes and reading only the locator's own sentence. Now
flagged; the unmutated ruling still passes. Both directions are pinned in
`test_locator_gate.py`, with the mutation as the case.

**D5 (MEDIUM/HIGH false positive), fixed.** A `lines` locator on the check-E path
was measured from the block's *first* line rather than the anchor's. A writer
counting lines counts from the sentence being ruled on, so a **true** "six lines
above" was dropped and told the reader it ran off the end of a seven-line section
— a correct ruling killed, with a false reason. `anchor_line` is now the anchor's
own line: the last line from which the anchor is still reachable is the line it
starts on. `03_a0.md`'s live two-line locator still passes.

**D9, fixed.** `check_bare()` never got the guard `check_uncited()` was given, so a
LOCATOR-invalid ruling was reported twice and the second reason — "is ruled and no
longer appears" — was **false**: the token does still appear. A gate that prints a
false reason for a true finding teaches the reader to stop believing its reasons.

### Not fixed, and named rather than left implied

None is live on the current tables; each is a real hole and none should be
inferred from a green run. **D2**: the origin block is the first block containing
the anchor, while `scan_uncited` silences the first *quantitative* one, so a
locator can be validated against a different block than the one exempted — latent,
and `07_battery.md` is one line from triggering it. **D3**: artefact matching is
naked substring, so `STATUS.md` is satisfied by `engine-rig/STATUS.md`. **D4**: an
unparsed phrasing ("the previous block", "just above") is a **silent** pass — the
vocabulary is `RULING_LOCATOR`'s and nothing distinguishes "checked and true" from
"not understood". That is the same shape as the defect this whole mechanism
exists for, one level up. **D6**: a merged block's line span is understated
because merges swallow the blank line. **D7**: check F's raw line scan includes
code-fence interiors that `_blocks()` excludes. **D8**: only the first locator in
a justification is parsed. **D10**: `stale` is un-deduplicated, so the "N ruled, M
stale rulings" summary can double-count.

The reviewer's verdict is the honest one and is adopted verbatim: **safe as an
improvement, not as a guarantee.** It is live on 5 of 13 rulings, which the
function's docstring overstated.

**Gate: FAIL (1/7), E UNCITED — unchanged and intended.** Exit code read directly
rather than through a pipe (`$?` after a pipe reads `tail`, which is how a red
gate reads green). **Suite: 274 passed, 1 xfailed.**
