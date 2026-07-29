# V5-verdict-three-types — what this run did, and what it did not

Worker `W-1652`. Territory `exam`. Branch `agent/v5-verdict-three-types`, base
`31bea46`. Suite **338 passed** (321 at base). `python -m exam.verify` GREEN,
determinism holds across `PYTHONHASHSEED` 7 and 99.

## The scope call, made first and stated plainly

The board item asks for three classes of verdict question in a self-built world
family, a constructive justification per item, calibration by a known-full and a
known-zero fake examinee, and sensitivity and specificity reported separately.

**All four were already on `master`**, delivered by P-15 and V4 as
`p15-verdict-a2`: 17 items across the three classes (not one each), 17
`proxy`-format specs carrying a justification, `oracle` 1.000 and `null` 0.000
against pre-registered bands with two further informative fakes, and a confusion
matrix split by class with coverage. Building a second one would have been
theatre.

So this run took the item's stated premise — 考卷的可信度取决于判卷者本身对不对 —
and asked whether the delivered instrument is right. It is not, in six ways, and
five are fixed here.

## Method

Six adversarial auditors in parallel, each read-only, each required to back every
claim with a command it ran: certificate-checker soundness, the class (ii)
bound, leakage, marker calibration, sensitivity/specificity reporting, and the 17
constructive justifications. **Every finding acted on was re-derived here before
anything was changed** — `STATUS.md` open weakness 14 says a cheater's
confidence is not evidence, and two of this territory's four recorded cheater
claims did not survive being scored against the key. The re-derivation scripts
are in this directory and are artefacts, not scratch:

| script | what it establishes |
|---|---|
| `probe_pair_by_stratum.py` | F-1: the class split holds one rate per cell; the board-size split holds both |
| `verify_leak_claims.py` | F-2: the multiplicity leak, and that `claim` never reaches the metadata check |
| `verify_checker_claims.py` | the two unsound certificate accepts, and the falsified class (ii) bound |
| `probe_multiplicity_threshold.py` | the lift an innocent field produces, for a threshold not yet chosen |

A seventh auditor then attacked this run's own conclusions.

## What was wrong, and what was done

| finding | fixed? | where |
|---|---|---|
| the certificate checker accepted proofs of false theorems | yes | D-EX-020 |
| `subset_lower_bound` unsound off the comb; a shipped constructor reaches it | yes | D-EX-021 |
| ~~class (ii) is searchable via its quotient~~ — **my error, withdrawn** | n/a | D-EX-027 |
| the fix for the above introduced a new unsoundness | yes | D-EX-027 |
| a claim outside the answer alphabet scored as a negative classification | yes | D-EX-027 |
| the key did not say whether its own witness was searched or constructed | yes | D-EX-023 |
| the class split cannot report the pair the item asks for | yes | D-EX-024 |
| an unreadable answer was counted as an abstention | yes | D-EX-025 |
| the gate sees 2 of the marker's 11 outcomes; 13 of 14 faults passed it | yes | D-EX-026 |
| four of the 17 justifications asserted something false or insufficient | yes | `papers/verdict.py` |
| the sheet leaks through board multiplicity — 13/17 against a 9/17 baseline | **no** | weakness 20 |
| the leak check has never been run against the real answer | **no** | weakness 21 |

Full detail with the numbers: `FINDINGS.md` here, `../../DECISIONS.md`
D-EX-020…026, and `../../STATUS.md`'s V5 section.

## What this run did NOT do, and why

Stated rather than left to be discovered. None of these is a lowered acceptance
line; each is work with a reason it was not attempted here.

1. **The multiplicity leak is measured and not repaired.** Seven of the nine
   boards appear once and six of those seven are unsolvable, so "reused ⇒
   solvable" scores 13 of 17 against a 9 of 17 baseline with no key. Repairing
   it means either a new checker plus a balancing item on each singleton board —
   which changes the paper's item set and needs its own pre-registration — or
   accepting it on the record. This run did the second and wrote the first down.
   Note the direction of the rule is a prior a cheater must guess; guessed the
   other way it scores 4 of 17.
2. **No unsolvable `win_tighten` item.** It is constructible
   (`win_score_required=2` gives 55 states and no solution, and
   `proxy/variants.py` accepts the spec) but no certificate in the closed
   grammar states that reason, so the oracle would score below 1.0 and
   calibration would fail. The blocker is the certificate grammar, not the
   world. Recorded as weakness 22, which is a sharper form of the old weakness 5.
3. **No solvable control in class (i).** Two examinees with opposite
   pathologies are identical in all ten printed cells and in the score; one
   control item separates them at 0.000 against 1.000. Adding it changes the
   class sizes the matrix and its tests are written against. Weakness 23.
4. **`certified_share_of_correct_unsolvable` still has a `correct`-subset
   denominator**, so it reads 1.000 for a pure bluffer. Weakness 24.
5. **Abstention is still weakly dominant, and the two directions are still
   priced asymmetrically.** Weaknesses 25 and 26.
6. **Class (ii) is not rebuilt.** D-EX-022 stopped the marker asserting a
   falsehood; it did not make the class mean what its name says. That needs
   switches that gate geometry, which is a different world family. Weakness 27.
7. **Only the verdict paper is covered.** The answer-shape probes are
   verdict-only, so D-EX-013's one-sided-band finding stands unchanged for
   `heldout`, `handover` and `adaptation` — and a test asserts exactly that, so
   the claim gets re-examined rather than quietly inherited when someone adds
   probes elsewhere.

## The places this run broke something

Three, and the adversarial pass is the only reason two of them are not shipping.

**1. The button exclusion, twice.** Delegating `_neighbours` to `Level.step`
made the button cell a node with no edges, which moved the atrium's component
representative from `[1,1]` to `[1,3]` and caused the shipped `a2var-i1`
certificate to be refused. Found by the justification auditor mid-run and fixed
by excluding the button from `passable()` — for the same reason the portal
already is: `step` never returns it.

That fix then **created a new unsoundness**, and the adversarial reviewer found
it. `row_col_deltas` was also using `passable`, to ask a different question:
where can the cart be *standing* when it issues a command, which includes the
button because the cart can start there. The teleport's row displacement
vanished from the closure, `cart_row` came out monotone, and a level solvable in
one command was paid **2.0 of 2.0** for a certificate saying it is unsolvable —
the exact failure D-EX-020 exists to remove, reintroduced by D-EX-020's own fix.
`Level.can_stand` is the predicate for that question now.

The lesson is not "check your callers". D-EX-020's argument was *there is one
transition function now, so the two cannot disagree again* — true, and
insufficient, because the disagreement moved into a **predicate** whose name
answers one question and whose two callers ask two.

**2. D-EX-022 was wrong and is withdrawn.** Deriving `search_credible` from the
`(cart, button)` quotient rested on the quotient being a sound abstraction. It is
not: it ignores `step_limit` outright and carries no latch state, and both
counterexamples use a shipped constructor and a shipped operator. I had verified
the auditor's *numbers* (180/180/600/177, all correct) and not its *inference*,
which is the whole claim. The decision replaced "a true statement was called
false" with "a false statement is called true" — and the second one pays.

**3. D-EX-025 landed in one of the two places that needed it.** The three-way
split went into `confusion_matrix.tally` and not `mark.confusion`, which is what
the gate actually reads.

All three are recorded rather than quietly repaired, because a run that only
publishes the defects it found in *other* people's work is not reporting its own
error rate. Detail: D-EX-027.

## Provenance

No API call, no network, no model call from any code path in `exam/`. No contact
with the sealed pile. Nothing written outside `exam/` except the `PARTNER_SYNC`
paragraph and one `monitor/inbox` note.
