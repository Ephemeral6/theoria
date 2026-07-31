
---

## D-036 · The checker for an exchange format cannot sit on the producer's side of the exchange

*(Numbered 036 after D-035. C13, `agent/c13-certificate-bridge-two-halves`.)*

**Context.** D-035 listed six checkers that do not import their producer and
named the one that is "exploitable by omission rather than by error":
`interop/certificate_export.verify` iterates the witness list the certificate
itself supplies, so a document that leaves out an inconvenient move instance
passes with an empty finding list. That entry recorded the gap and corrected the
prose around it. It did not close it, and `interop/certificates/*.json` is the
one artefact class in this rig that leaves the track — the theory-compiler
reader has been consuming it since `f58959e7`.

**The decision.** The rig ships a reference reader for its own exchange format,
`interop/pagoda_reader.py`, and the format is pinned in
`CONTRACTS/pagoda_certificate_v0.1.md`. The reader pays independence in three
currencies, each checked rather than asserted:

* **It imports nothing from here.** `json`, `fractions`, `os`, `sys`, and that
  is the whole list — no `engines`, no `interop`, no `recheck`, not even numpy.
  `tests/test_pagoda_reader.py` scans the import lines.
* **It runs alone.** Copied into an empty directory and executed with `python
  -I`, it still adjudicates. A promise about the import graph that no process
  ever tests is a promise about a comment.
* **It grounds the move relation instead of reading it.** This is the one that
  matters; the other two are hygiene.

**Why the geometry is duplicated on purpose.** `pagoda_reader.jump_moves` is a
second implementation of `peg1d.move_instances`, six lines re-written rather than
imported. Importing them would make the reader re-check the producer's premise
against itself, which is exactly the shape D-035 was about. The duplication is
the guarantee, and the contract is the single text both copies are written from.
The cost is real and named: two implementations can drift. What catches drift is
that both are exercised against the same three committed documents, and that the
reader carries an exhaustive second opinion on boards small enough to settle.

**The non-vacuity, because a checker that has never said no is not a checker.**
A forged certificate: `weights_integer[2]` moved from `0` to `-1`, which makes
`jump(1,2,3)` and `jump(3,2,1)` raise the potential, with those two witnesses
deleted and every remaining field — deltas, `holds`, `n_checked`, `checked_over`,
`weights_rational` — recomputed to agree. The bound and the goal are untouched
because neither depends on cell 2, so `inv_init` and `goal_break` still hold.

```
certificate_export.verify(forged)                  -> []          # accepted
pagoda_reader.check(forged, geometry=<the document's own list>) -> []          # accepted
pagoda_reader.check(forged)                        -> two rejections
```

The middle line is the point. Same reader, same document; only the source of the
move relation changes, and the verdict flips. So what the decision fixes is not
"check `inv_closed`" — `verify()` already did — but **where the transition
relation is allowed to come from**.

**A second consequence, smaller but load-bearing.** `initial_potential` is read
as a *declared* bound and `potential(initial) <= bound` is checked against it,
rather than recomputed from `initial_state`. `certificate_export.build` writes
the bound *as* `potential(initial)`, so recomputing turns `inv_init` into
`x <= x` — a certificate with a tampered-down bound would then be caught by no
obligation at all. Its own docstring already admitted the field "is here for the
Lean skeleton's third slot"; reading it as a declaration is what makes it
evidence.

**What this does not buy.** That peg1d is the right rule set for anybody's world.
Three obligations discharged entitle a reader to "no goal state is reachable
under the 1-D peg jump relation on `n_pos` cells", and the reader declares that
assumption in `GEOMETRY` rather than pretending the document settled it. A
different rule family needs a different schema id, not an extra field — an extra
field would put the relation back inside the document.

**Two things repaired in passing.** `interop/certificates/*.json` had no
producer: no script in the tree rebuilt them, and the only record of a
regeneration was a prose line in another run's `MANIFEST.json`.
`interop/export_certificates.py --check` rebuilds all three byte-for-byte and is
in the suite. And the item that commissioned this work asserted that
`monitor/scan.py`'s `probe_a1_state` reports the bridge unconsumed; it reports
`green`, and has been able to since `f58959e7` landed the consumer two days
earlier. Nothing here was changed to make that so — the probe is untouched and
this branch changes zero bytes under `theory-compiler/`. The correction is filed
on the board and in `monitor/inbox/`, because a work item whose premise has
expired is worth more as a correction than as a completed ticket.
