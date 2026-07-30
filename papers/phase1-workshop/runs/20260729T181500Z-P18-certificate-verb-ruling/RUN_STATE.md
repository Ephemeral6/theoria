# P18-certificate-verb-ruling — run state

RES-2, paper lane. Branch `agent/p18-certificate-verb-ruling`, based on
`agent/p17-machine-checked-ruling` (not on `master`) because both items edit the
same `OPEN_ITEMS.md` C12 row, and stacking is cheaper than resolving that
conflict twice.

`RULING.md` is the deliverable. This file is the narrative.

## What the item asked, and what it got wrong

C12 asked for the §5.2 treatment at two more prominent sites: §1's contribution
bullet and §4's own section heading, both reading "a machine-checked impossibility
certificate whose weights cross a data boundary".

**The item's own premise was false in one half, and I wrote that half.** At P17 I
widened C12 to say the real defect was a *conjunction* — that §4 states
`unsolvable` closes by exhaustion and never invokes the certificate's `inv_all`,
so the machine-checked impossibility does not depend on the crossed weights.

`theory-compiler/lean/TheoriaLean.lean:148` is `have h1 := inv_all _ hr`. It is
the only thing in the proof connecting `Reachable` to anything. The shipped
theorem **does** depend on the crossed weights.

I wrote that from an adversary's summary of §4.4's prose without opening the Lean
file. **Third time in two days.** The P17 ruling's §7 is about the first two. The
sentence was struck on the P17 branch before it could reach the mainline, and
struck rather than deleted, because by now the recurrence is worth more than any
one of its instances.

Then a *fourth*: the fact-gathering pass for this item reported that §1's bullet
lacks the "two sessions, not two teams" qualifier and that the qualifier lives
three sections away. The bullet ends with it, inline, citing the section. Caught
by reading the bullet before editing it. Recorded in `RULING.md` §2.2.

The pattern is now specific enough to name: **every one of the four was a claim
about what a file says, sourced from something other than that file, and every
one of them was wrong in the direction that made the paper look worse.**

## The ruling

**Repair §1. Leave §4 and §11. Name the development in §4.4.**

The three sites are not one defect, and the difference is grammatical. §1 hangs
"machine-checked" on the **certificate** — a JSON document whose re-checker is
Python, which deliberately ignores the blob's own `verified: true`. That is the
§5.2 defect exactly: the strongest verb in the paper on a non-proof object.
§4's heading and §11's recap hang it on the **impossibility** — a Lean theorem,
`decide` only, no Mathlib, no `native_decide`, `#print axioms` emitted for all
four theorems, non-vacuous (32 inhabitants of `St`, not a hand-built enumeration
of the reachable set; `inv_closed` decides 192 move × state instances). Those two
are true as written, and **C12's demand that they get the §5.2 treatment is
refused** — recorded with the evidence so the next round does not re-open them on
this item's authority.

So the word "machine-checked" survives here where P17 deleted it. That is not
inconsistency: P17 deleted it because the object underneath was not a proof.
**The rule is "check the noun", not "distrust the adjective".**

§1's bullet is repaired rather than deleted, because unlike §5.2's sentence its
content is true and it is one of the paper's four contributions. The abstract
already states it correctly — the paper had the right sentence all along, in the
place with the least room, and got it wrong in the place with the most.

§4.4 is the repair the item did not ask for and the one that caused the damage.
It said "the development it actually writes" of a development this repository
never writes: the five-goal hybrid branch, which exists as generator code
exercised by three tests against a problem declared inside the test module. A1's
fixture asks for one goal state, which the certificate covers, so A1 takes the
other branch. §4.4 now says which is which.

## Tests

`python verify_paper.py` → **PASS (6/6)** after each edit. Zero API calls, zero
sealed-pile contact, $0.00. Only `papers/` is touched — the Lean, generator and
certificate files named above were **read** as evidence and not modified; they
belong to the theory-compiler track.

## Adversarial round

Briefed with the standing instruction this run earned: verify against the artefact,
never against prose or a summary. Attacking the load-bearing Lean claim, the weight
provenance, whether "machine-checked" is earned at the two surviving sites given that
the axiom-list evidence is test-asserted rather than stored, the §4.4 branch claim,
and whether the repair to §1 introduced a new error.

**The session that dispatched it died before harvesting it.** The next session picked
the item up off disk — branch present, `a2269994` committed and never pushed, this
file's own line reading "result recorded below when it returns" — and re-ran the
round. Nothing already finished was redone.

**No independent adversary could be obtained.** Four launches (one combined, then the
attacks split two ways to shorten each run) all died on `API Error: 529 Overloaded`.
The attacks were therefore run by the ruling's author against the ruling, which is
the weaker arrangement the contract's fan-out discipline exists to avoid, and it is
recorded as a limitation rather than smoothed over. What compensated: every check went
to the artefact, none to the ruling's own quotations.

**It found three defects, all in this item's own work** — full account in `RULING.md`
§2a:

1. `:148` for `have h1 := inv_all _ hr`, which is at **`:149`**; plus `:144-151` →
   `:145-152` and `:153-156` → `:154-157`. The file had not moved. **The fifth
   instance of §0's class, and the first about a file's coordinates rather than its
   contents** — sitting on the one citation that carried the refusal of C12, and
   propagated into `OPEN_ITEMS.md` and the commit message.
2. §4.4's "three tests" did not reproduce — six exercise the branch, four generating
   and two refusing — and it had reached the paper. Fixed with the split stated and
   the test file cited.
3. The repaired §1 bullet cited §4.1 for the empty axiom list; it is in §4.2.

Defects 2 and 3 were introduced by this ruling's *own repairs*. No gate the paper has
would have caught any of the three, which is the argument for self-supplied item P19.

**The substance held.** `inv_all` is load-bearing and numerically tight (`potential
s0 = 0`, goal `potential = 1`); no `import` anywhere so no Mathlib; no `native_decide`,
`sorry` or `axiom`; `St` 5 Bools → 32 states, `Move` 6 constructors → the **192** is
real; provenance is enforced by three named tests, and A1's fixture carries no
`weights` key.

**One caveat was overturned in the ruling's favour.** §3 said no `lean` transcript
exists in the tree. `LEAN_TRANSCRIPT.md` now holds one: Lean 4.9.0 was on PATH, so the
check ran rather than skipped — four theorems, "does not depend on any axioms", exit 0,
over sha256 `951981b6…5496bee0`, with `test_gen_lean.py` at 21 passed / 0 skipped.
C8 stays open.

## Task 3 — B5

Done and recorded separately in `B5_CHECK.md`: **still only recorded, no contradiction
reached the paper.** Re-measured from the two `.lean` files rather than from B5's
account of itself — plain `diff` 52, `diff -u` 7 hunks, `diff -U0` 15 groups, all
matching §5.6, including the 28-of-52 weight-table share. `diff -U0`'s 69-line total
decomposes exactly as 2 file headers + 15 hunk headers + 52 changed lines, so the
audit's 70 has no convention that yields it. `CITECHECK.md` has not been edited since
before B5 was opened.
