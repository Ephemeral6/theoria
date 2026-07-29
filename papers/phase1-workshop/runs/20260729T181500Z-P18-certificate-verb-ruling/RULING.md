# P18 · Ruling on "a machine-checked impossibility certificate whose weights cross a data boundary"

RES-2, paper lane, 2026-07-29. Item `P18-P18-certificate-verb-ruling`, opened by
the P17 ruling as `OPEN_ITEMS.md` **C12**.

## 0 · What is being ruled on, and the correction that had to come first

C12 said the same proof-verb defect P17 deleted from §5.2 survives in two more
prominent places — §1's contribution list and §4's own heading — and asked for
the same ruling.

**C12 was half right, and its other half was false.** The false half was mine: I
widened C12 at P17 to say that the defect was really a *conjunction*, because
§4.4 states that `unsolvable` closes by exhaustion and never invokes the
certificate's `inv_all` lemma — so, I wrote, the weights crossed the boundary and
the machine-checked impossibility does not depend on them. The tracked A1 Lean
artefact says otherwise, on one line:

> `theory-compiler/lean/TheoriaLean.lean:148` — `have h1 := inv_all _ hr`

That `have` is the only thing in the proof connecting `Reachable` to anything.
Remove it and `unsolvable` does not close. The shipped impossibility **does**
depend on the crossed weights.

I wrote the false half from an adversary's summary of §4.4's prose without
opening the Lean file. **That is the third time in two days that reading the
paper's account of an artefact, instead of the artefact, produced a false claim**
— the P17 ruling's §7 is about the first two. Struck in place on the P17 branch
before it could reach the mainline (`OPEN_ITEMS.md` C12), because the recurrence
is worth more than the tidiness.

## 1 · The three sites are not one defect, and only one of them is wrong

The phrase is not the same phrase in the three places it appears. What the
adjective is attached to differs, and that is the whole ruling.

| site | text | adjective sits on |
|---|---|---|
| §1 contribution bullet | "A machine-checked impossibility **certificate** whose weights cross a data boundary." | the **certificate** |
| §4 heading | "A1 — a machine-checked **impossibility** whose weights crossed a data boundary" | the **impossibility** |
| §11 recap | "a machine-checked **impossibility** can be produced whose weights crossed a data boundary between two sessions that do not import each other's code" | the **impossibility** |

**The certificate is a JSON blob.** `engine-rig/interop/certificates/pagoda_5_11011_to_00010.json`,
schema `lp_potential/pagoda_certificate@1`, produced by an LP. What re-checks it
is **Python** — `theory-compiler/src/theory_compiler/certificate.py`, which
deliberately ignores the blob's own `"verified": true` and re-derives the move
geometry rather than reading the witness list. No kernel is involved anywhere in
the certificate's own validation. Calling *that* machine-checked, in a paper that
teaches the term strictly two sections later, is exactly the §5.2 defect: the
strongest verb in the paper on a non-proof object.

**The impossibility is a Lean theorem, and it is machine-checked in the strict
sense.** `TheoriaLean.lean:144-151`, `theorem unsolvable : ¬ ∃ s : St, Reachable s ∧ Goal s = true`,
discharged by `decide` with no Mathlib and no `native_decide`; `#print axioms` is
emitted for all four theorems at `:153-156`. It is not vacuous: `St` is a 5-field
`Bool` structure with 32 inhabitants rather than a hand-built enumeration of the
reachable set, `Goal` picks out one of them that genuinely exists, `Reachable` is
inhabited by `init`, and `inv_closed` decides 192 move × state instances.

**And the weights really are the ones that crossed.** The certificate's
`weights_integer` is `[-1, 1, 0, 1, -1]`; `TheoriaLean.lean:101-106` is
`.p0 => -1 | .p1 => 1 | .p2 => 0 | .p3 => 1 | .p4 => -1`. The generator holds no
vector of its own — every reference is `cert.weights` — the manual declares the
invariant without numbers, the level fixture carries no `weights` key, and a test
fails if the committed `.lean` differs by a byte from a regeneration off the
certificate.

So §4's heading and §11's recap are true as written, and the noun under the
adjective is the reason. **C12's demand that they get the §5.2 treatment is
refused.**

## 2 · Ruling

**Repair §1's bullet. Leave §4's heading and §11 alone. Name the development in
§4.4.**

1. **§1's bullet is repaired, not deleted.** Unlike §5.2's sentence, the content
   here is true and load-bearing — it is one of the paper's four contributions.
   What is wrong is which noun the adjective governs. The bullet is rewritten so
   that the machine-checked object is the impossibility and the certificate is
   the thing that crossed, which is what the abstract already does correctly
   ("A pagoda-style impossibility certificate computed by a linear program in one
   track crosses a JSON boundary into a second, which re-verifies every
   obligation rather than trusting the producer and emits a Lean proof with an
   empty axiom list"). The paper contained the right sentence all along, in the
   place with the least room, and got it wrong in the place with the most.
2. **"An independent engine's linear program" needs no repair — the bullet
   already scopes it, in its own last sentence.** *This point replaced a longer
   one, which was wrong.* A fact-gathering pass reported that the qualifier lives
   three sections away in §4.2 and that the bullet lacks it. The bullet ends:
   "The two sides are sessions that do not import each other's code (§4.2), which
   is weaker than independent implementation and is not claimed as more." It is
   inline, it is exact, and it cites the section. Recorded rather than quietly
   dropped, because it is the *fourth* claim in two days that dissolved on
   opening the file it was about, and the first three are the subject of §0.

3. **§4's heading and §11's recap stand, unchanged.** Recorded here with the
   evidence so the next round does not re-open them on C12's authority.
4. **§4.4 names which development it is describing.** This is the repair the
   item did not ask for and the one that caused the damage. §4.4 says "the
   development it actually writes" of a development the repository **never
   writes to disk**: it is `gen_lean.py::_hybrid_lean`, reached only when a
   manual's goal is broader than the certificate covers, and A1's own fixture
   (`goal_states: ["00010"]`, a single state the certificate covers) never
   reaches it. The hybrid exists as generator code exercised by three tests
   against a test-local five-goal problem; a grep for the banner it emits hits
   one file, the generator. §4.4's subject is **E-06's broader proposition**, and
   everything it says is true of that. A reader who arrives from §4's heading
   reads it as A1's shipped artefact and concludes the opposite of the truth
   about it. I am that reader, and I wrote the conclusion into an audit item.

The word "machine-checked" is left in place at both surviving sites. That is the
opposite of P17's disposition on the same word, and deliberately so: P17 deleted
it because the object underneath it was not a proof. Here the object underneath
it is a kernel proof with an empty axiom list, and the paper's own strict use of
the term is the standard it meets. **The rule is not "distrust the adjective", it
is "check the noun".**

## 3 · Two residual caveats, both already disclosed, neither repaired here

* **The boundary is a module boundary, not a held-out-data boundary.** Nothing
  was withheld from anyone. What crosses is defence-in-depth, not independent
  replication, and §4.2 says exactly that.
* **The empty axiom list is test-asserted, not stored.** No `lean` transcript
  exists anywhere in the tree; the assertion lives in tests that *skip* when the
  toolchain is absent, which §4 discloses and `OPEN_ITEMS` C8 already tracks. The
  negative control that makes the check falsifiable — perturbing one weight until
  all four theorems report `[sorryAx]` — is likewise recorded only in prose.
  Under this paper's own rule that an invited check must survive being run, a
  reader without Lean cannot run this one. Left to C8 rather than folded in here,
  and noted in `OPEN_ITEMS` so the two are linked.
