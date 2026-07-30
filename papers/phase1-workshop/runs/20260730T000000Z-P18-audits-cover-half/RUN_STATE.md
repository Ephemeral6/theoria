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

## State

Check G is **red on purpose** as of this writing: `CITECHECK.md` and `REVIEW.md`
carry no stamp, which is G1. That is the pre-P18 state being reported for the
first time rather than a regression. `verify_paper.py` exits 1 on it — the
verdict is wired to the exit code, checked directly rather than through a pipe.

`test_audit_stamp.py`: 44 passed, 1 xfailed.

## Open, and deliberately not done here

The 13 findings of the referee pass are, in its own words, "every one a writing
fix or a re-transcription against an artefact that already exists". **Writing
paper body text is RES-2's exclusive remit** (`monitor/CHARTER.md`), so they are
handed over rather than applied. Six are blocking, including a self-contradictory
abstract — the item asked for those kill shots and they are found and located;
what is out of bounds is only the editing.
