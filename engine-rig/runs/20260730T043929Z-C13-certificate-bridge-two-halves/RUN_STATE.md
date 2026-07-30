# C13 — certificate bridge, our half

Worker `W-1700`. Branch `agent/c13-certificate-bridge-two-halves`, base
`12a48ecc1297fd42f8f31fc362cf7ef15176f9bf`. Territory: `engine-rig/` plus the
two shared surfaces (`/CONTRACTS/`, `PARTNER_SYNC.md`) and `monitor/inbox/`.
`theory-compiler/` is the other track and this branch changes **0 bytes** there
(`git diff --name-only origin/master...HEAD -- theory-compiler` is empty; the
acceptance script checks it).

## The item, and the one thing in it that had expired

Four deliverables were asked for: a round trip through an independent reader, the
format pinned in `/CONTRACTS/`, a PARTNER_SYNC paragraph, and negative samples.
All four are done, at the stated bar.

The item's *premise* was stale, and this is the finding worth reading first.

> 而它长年报 partial …… 所以**现在它的判决是可信的**，partial 就是真的 partial。
> …… 做完之后 `probe_a1_state` 的 `bridge` 应当为真、`consumed` 仍可能为假。

`probe_a1_state` reports **green** on `12a48ecc`. Run in the main tree and in
this worktree, same answer both times, recorded in `probe_a1_state.json`.
`consumed` is true because `theory-compiler/src/theory_compiler/certificate.py:38`
holds `SCHEMA = "lp_potential/pagoda_certificate@1"` — the exact literal
`scan.py:251` looks for, on a line `scan.py:248-250` already names in a comment.
That file has been on master since `f58959e7` (2026-07-28), two days before the
item was written, and is not under a `runs/` directory so the probe's filter does
not skip it.

The shape of the mistake is worth keeping. Before S26 the probe returned
`partial` unconditionally, whatever the tree looked like. S26 made the verdict
conditional — and nobody re-ran it. The item inherited the pre-fix constant and
then vouched for it in prose: *the instrument has been repaired, so its reading
is trustworthy*. **A repaired instrument has to be re-read, not re-endorsed.**

Nothing here was changed to produce that green. `monitor/scan.py` is untouched.
Filed to `monitor/inbox/20260730T050500Z-W-1700-c13-premise-expired-and-two-contracts-unanswered.md`,
which also proposes a board item for the two contracts (`ic3`, `deadlock`) that
have been waiting on an engine-rig countersign since 2026-07-28 with no ticket.

## What was built

**`interop/pagoda_reader.py` — the reference reader.** Independence paid in three
currencies, each checked rather than asserted: it imports only `json`,
`fractions`, `os`, `sys`; it runs from an empty directory under `python -I`; and
it **grounds the move relation** from the geometry instead of reading the witness
list. It never opens `obligations`, `verified` or `conclusion`. `GEOMETRY`
declares the assumption (`peg1d_jump`) rather than pretending the document
settled it.

**`interop/export_certificates.py` — the missing producer.** No script in the
tree rebuilt `interop/certificates/*.json`; the only record of a regeneration was
a prose line in another run's `MANIFEST.json`. `--check` now rebuilds all three
byte-for-byte and is in the suite.

**`CONTRACTS/pagoda_certificate_v0.1.md` — the missing spec.** Zero field
changes: written from what both sides already do, not proposed. `ic3_certificate_v0.1.md:15-17`
had flagged that this format was the one without a written spec. `CONTRACTS/verify.py`
still green (8 documents).

**`tests/test_pagoda_reader.py` — 30 tests.** Eight ordinary negative samples,
the malformed-input separation, and the two forgeries that carry the argument.

**`DECISIONS.md` D-036**, `interop/README.md` updated (it now sends readers to
the reader rather than to `verify()`, and no longer quotes a `checked_over`
string that E16 changed).

## The forgery, and why the pair of results is the point

`weights_integer[2]` moved from `0` to `-1`. That makes `jump(1,2,3)` and
`jump(3,2,1)` raise the potential by 1 each. Both witnesses deleted; the
remaining four recomputed; `n_checked`, `checked_over` and `weights_rational`
all corrected to agree. The bound and the goal are untouched because neither
depends on cell 2, so `inv_init` and `goal_break` still hold. The document is
internally consistent and wrong.

```
certificate_export.verify(forged)                       -> []
pagoda_reader.check(forged, geometry=<the document's own list>) -> []
pagoda_reader.check(forged)                             -> ['inv_closed: jump(1,2,3) raises the potential by 1',
                                                            'inv_closed: jump(3,2,1) raises the potential by 1']
pagoda_reader.check(honest)                             -> []
```

The middle line is the non-vacuity: same reader, same document, only the source
of the move relation changes, and the verdict flips. So the thing being fixed is
not "check `inv_closed`" — `verify()` already did — but **where the transition
relation is allowed to come from**. The forged document is on disk here as
`forged_omission.cert.json`.

`test_the_forgery_is_not_caught_by_the_obligations_block_being_short` rules out
the cheap explanation: delete `obligations`, `verified` and `conclusion` from
both documents and both verdicts are unchanged.

**The stronger forgery, which an adversarial pass found and I did not.** The one
above breaks the proof of a claim that is *true* — `01000` really is unreachable
from `11011` — so it shows the reader catching a bad proof, not a false
conclusion. The stronger case: weights `[-4, -4, 4, 0, 4]`, bound `-4`, goal
`00111`. Exactly one jump raises the potential, `jump(0,1,2)` by 12, and that
jump is legal in `11011` and lands **on the goal**. Delete its witness and
`certificate_export.verify()` returns clean on a document whose conclusion is
false. Verified here before being believed (deltas recomputed, `'00111' in
peg1d.reachable_from('11011')` is `True`), then adopted as a test, an acceptance
check, and `forged_falsehood.cert.json`. So the gap is not "an unproven true
claim" but a certified falsehood.

Full record of both adversarial passes, including the four test-battery defects
they found in my own tests and the mutation run confirming each is now caught:
`adversarial_review.md`.

## Tests

| Command | Result |
|---|---|
| `cd engine-rig && python -m pytest` | **584 passed, 27 skipped** |
| `cd engine-rig && python -m pytest --ignore=tests/test_pagoda_reader.py` | 554 passed, 27 skipped (baseline; +30 new, zero regressions) |
| `cd CONTRACTS && python verify.py` | green, 8 contract documents |
| `cd engine-rig && python -m interop.export_certificates --check` | 3 certificates rebuild byte-for-byte |
| `cd engine-rig && python runs/20260730T043929Z-C13-certificate-bridge-two-halves/verify.py` | **ALL CHECKS PASS** (9 groups) |

Zero API calls, zero network, zero sealed-pile contact.

## Gaps, recorded rather than closed

1. **`certificate_export.verify()` still has the omission gap.** It was not
   changed. The test now *pins* that it accepts the forgery, so closing it later
   shows up as a failing test rather than as silence. Closing it properly means
   grounding the relation, which is what the reader does — duplicating that
   inside the producer would put the check back on the producer's side of the
   exchange, which D-036 argues against.
2. **The reader duplicates `peg1d.move_instances`.** Deliberate — importing it
   would re-check the producer's premise against itself — but two
   implementations can drift. Both are exercised against the same three
   documents and the reader carries an exhaustive second opinion, which is what
   would catch drift on these board sizes and nothing larger.
3. **Byte-reproducibility is conditional.** The LP is solved in floating point by
   HiGHS and snapped with `Fraction.limit_denominator(1000)`. The guarantee is
   "same scipy/HiGHS build ⟹ same bytes".
4. **The contract is unsigned.** `theory-compiler` has not countersigned; the one
   substantive open question put to them is whether `initial_potential` is read
   as a declared bound (this contract requires it) or recomputed.
5. **Two other contracts remain unanswered by this track**, and answering them is
   real work (writing `ic3_pdr` / `deadlock_carver` exporters), not a signature.
   Out of scope here; proposed as a separate item in the inbox.

## Artefacts in this directory

| File | What it is |
|---|---|
| `MANIFEST.json` | provenance |
| `verify.py` | the acceptance script, runnable from `engine-rig/` |
| `forged_omission.cert.json` | the document that passes the producer and fails the reader |
| `forged_falsehood.cert.json` | the stronger one: same trick, but the deleted move is the move that reaches the goal, so the producer certifies something false |
| `round_trip.cert.json` | engine → export → disk, the document the round trip wrote |
| `reader_transcript.json` | the reader's verdict and second opinion on all three committed certificates |
| `isolated_run.txt` | stdout of the reader run from an empty directory under `python -I` |
| `probe_a1_state.json` | what the monitor probe actually says, recorded not steered |
| `partner_sync_paragraph.md` | the exact bytes appended to `PARTNER_SYNC.md` |
| `decision_d036.md` | the exact bytes appended to `DECISIONS.md` |
| `adversarial_review.md` | two adversarial passes over this work and what they changed |

## Log

- `04:39Z` worktree created, baseline `python -m pytest` exits 0.
- `04:5xZ` recon (5 parallel agents): `recheck` refuses an `obligations` key at
  load, so it never reads the exchange document — the gap is real and unfilled.
- `05:0xZ` `pagoda_reader.py`; all three committed certificates accepted.
- `05:1xZ` `export_certificates.py`; `--check` green first try.
- `05:2xZ` 23 tests; forgery built; non-vacuity confirmed.
- `05:3xZ` contract, README, D-036.
- `05:4xZ` PARTNER_SYNC appended (CRLF preserved, backticks intact — the
  PowerShell here-string hazard recorded at `PARTNER_SYNC.md:632` was avoided by
  appending bytes from a file).
- `05:5xZ` inbox note; acceptance script ALL CHECKS PASS.
- `06:0xZ` two adversarial passes; see `adversarial_review.md`.
