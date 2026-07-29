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

> `theory-compiler/lean/TheoriaLean.lean:149` — `have h1 := inv_all _ hr`

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
sense.** `TheoriaLean.lean:145-152`, `theorem unsolvable : ¬ ∃ s : St, Reachable s ∧ Goal s = true`,
discharged by `decide` with no Mathlib and no `native_decide`; `#print axioms` is
emitted for all four theorems at `:154-157`. It is not vacuous: `St` is a 5-field
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

## 2a · The adversarial round, and what it found in this ruling

Run 2026-07-30 by the session after the one that wrote §0–§2, which died before
harvesting the round it had dispatched.

**No independent adversary could be obtained, and that weakens this round.** Four
subagent launches — one combined, then the same attacks split two ways for shorter
runs — all died on `API Error: 529 Overloaded` without returning a finding. So the
attacks below were run by the author of the ruling against the ruling, which is the
weaker arrangement the contract exists to avoid: a self-adversary shares the priors
that produced the error. It is recorded as a limitation of this round rather than
papered over. **What compensated is that every check was run against the artefact and
none against this ruling's own quotations** — which is exactly how the three defects
below surfaced.

**Three defects found, all three in the ruling or in what it wrote into the paper.**

1. **The load-bearing citation was off by one, and so were two others.** §0 cited
   `TheoriaLean.lean:148` for `have h1 := inv_all _ hr`. **It is at `:149`.** Line 148
   is `| St.mk p0 p1 p2 p3 p4 =>`. Likewise `:144-151` for `theorem unsolvable` is
   `:145-152`, and `:153-156` for the four `#print axioms` is `:154-157`. The file has
   not moved — its last commit is `07b820f6`, before this ruling, and the repo-root
   and worktree copies are byte-identical — so these were wrong when written. All
   three are corrected above. `:101-106` for the weight table was right.

   **This is the fifth instance of the class §0 is about, and the worst-sited.** The
   first four were claims about file *contents* sourced from something other than the
   file; this one is a claim about a file's *coordinates*, and it sat on the single
   citation carrying the refusal of C12. It also propagated: `OPEN_ITEMS.md` C12 and
   commit `a2269994`'s message both carry `:148`. C12 is corrected; the commit message
   is immutable and is superseded by this section. `OPEN_ITEMS.md` B4 already named the
   gap that let it through — "check F resolves the file, nothing resolves the anchor
   inside it" — and self-supplied item **P19** is that gap.

2. **"Three tests" did not reproduce, and it was in the paper.** §4.4's repair — the
   one this ruling added on its own initiative — said the hybrid development is
   "exercised by three tests against a five-goal problem declared inside the test
   module". Counted in `theory-compiler/tests/test_gen_lean.py`: **six** tests exercise
   the uncovered-goal branch. Four generate the hybrid development (`:126`, `:288`,
   `:304`, `:349`) and two check it refuses rather than emitting (`:323`, `:332`).
   "Three" is reachable only under an unstated criterion — the three that use the
   module-level `ANY_SINGLE_PEG` constant at `:280`, excluding `:126`, which declares
   its own five-goal problem inline at `:141-147`. A count whose criterion is invisible
   is the defect P16's gate exists for. §4.4 now says six, with the split, and cites
   the test file.

3. **The repaired §1 bullet cross-referenced the wrong subsection.** It cited "an
   empty axiom list (§4.1)". §4.1 is "What A1 was for" (`04_a1.md:3-27`) and contains
   no mention of an axiom list; the evidence is the chain block in **§4.2** at
   `:41-42`. Corrected to §4.2. Defects 2 and 3 were both introduced by this ruling's
   own repairs, which is the answer to "did the repair introduce a new error" — twice,
   and neither would have been caught by any gate the paper has.

**What survived, verified against the artefacts.** The substance of the ruling did not
move:

* `inv_all` **is** load-bearing. `rintro ⟨s, hr, hg⟩` binds `hr : Reachable s`, and
  `inv_all _ hr` at `:149` is its only consumer; the proof then rewrites `h2` with
  `h1` and closes on `Bool.noConfusion`. Delete the `have` and nothing connects
  `Reachable` to anything. The dependency is numerically tight, not nominal:
  `potential s0 = -1+1+0+1-1 = 0 ≤ 0` gives `inv_init`, and the goal state
  `⟨false,false,false,true,false⟩` has `potential = 1 > 0`, which is what `goal_break`
  needs. Different weights break it.
* Strictly machine-checked and non-vacuous: **no `import` line anywhere** in the file,
  so no Mathlib; no `native_decide`, no `sorry`, no `axiom` declaration; `St` is a
  5-field `Bool` structure (`:37-43`) so 32 inhabitants; `Move` has exactly 6
  constructors (`:61-68`), which is where **192** comes from — 6 × 32, and it is real;
  `Reachable` is inhabited by `init` at `:118`.
* Weight provenance is **enforced, not asserted** — more tightly than §1 claimed. The
  certificate's `weights_integer` is `[-1, 1, 0, 1, -1]`, matching `def w` at
  `:101-106`; `gen_lean.py:376` writes the table from `cert.weights`; the manual
  declares `weights w over Peg.pos` with no numbers (`peg_theory.dsl:20`); A1's fixture
  `peg5_problem.json` has keys `name, n_pos, background, objects, goal_states` and
  **no `weights` key**, with `goal_states: ["00010"]`. Three tests hold the chain shut:
  `test_weights_come_from_the_certificate` (`:62`),
  `test_refuses_weights_that_disagree_with_the_certificate` (`:162`), and
  `test_the_committed_lean_artifact_is_not_stale` (`:260`). The one hard-coded
  `[-1, 1, 0, 1, -1]` in the generator's package, `problem.py:23`, is inside the module
  docstring's JSON shape example, not live code.
* The §4.4 branch condition is what the ruling says: `gen_lean.py:257-268`, `missing =
  covers(cert, goal_states)`, and only a non-empty `missing` routes to `_hybrid_lean`.
  A1's single covered goal takes the other branch.

**And one caveat was overturned in the ruling's favour.** §3 below said no `lean`
transcript exists anywhere in the tree. One does now:
`LEAN_TRANSCRIPT.md`, beside this file. Lean 4.9.0 was on PATH, so the check ran
instead of skipping — all four theorems reported "does not depend on any axioms",
exit 0, against sha256 `951981b6…5496bee0`; `test_gen_lean.py` was **21 passed, 0
skipped**. This strengthens "machine-checked" at the two surviving sites: the verb is
now backed by a stored kernel transcript over a named hash, not only by a test that
skips. It does **not** close C8 — see that file's "What this does not fix".

## 3 · Two residual caveats, both already disclosed, neither repaired here

* **The boundary is a module boundary, not a held-out-data boundary.** Nothing
  was withheld from anyone. What crosses is defence-in-depth, not independent
  replication, and §4.2 says exactly that.
* **The empty axiom list is test-asserted, not stored.** *Partly overturned by §2a —
  a transcript now exists at `LEAN_TRANSCRIPT.md`, and the sentence is kept rather
  than rewritten because the reasoning below still holds for a reader without a
  toolchain.* No `lean` transcript
  exists anywhere in the tree; the assertion lives in tests that *skip* when the
  toolchain is absent, which §4 discloses and `OPEN_ITEMS` C8 already tracks. The
  negative control that makes the check falsifiable — perturbing one weight until
  all four theorems report `[sorryAx]` — is likewise recorded only in prose.
  Under this paper's own rule that an invited check must survive being run, a
  reader without Lean cannot run this one. Left to C8 rather than folded in here,
  and noted in `OPEN_ITEMS` so the two are linked.
