# V19-unverified-is-not-true — run state

**Cell** V19 · **lane** verify · **territory** `worldgen/`
**Branch** `agent/v19-unverified-is-not-true` · **base** `9348fa4`
**UTC** 2026-07-28T23:03:07Z

Provenance: `MANIFEST.json`. Per-file regeneration evidence: `FLIPS.md`.
Item 4's judgements: `OPTIMISTIC-DEFAULTS.md`. Adversarial review, verbatim:
`ADVERSARIAL-VERBATIM.md`. Raw console output: `evidence/`.

## The finding, restated

```python
"invariants_all_hold": all(i.get("holds", True) for i in invariants),
```

A prose-only invariant carries no `holds` key, so `.get`'s default reported it
as holding. `build.py` promoted that to `invariant_failures: []` in the
manifest, which is the list the build gate reads. Thirteen of thirty-five
shipped `ground_truth.json` files said `invariants_all_hold: true` while the
`GROUND_TRUTH.md` written from the same dict in the same function call printed
`prose only, unverified` about the same claim.

**The shape worth remembering.** The human-readable half was honest the whole
time. Only the machine-read half lied — and the machine is what adjudicates.
Any reviewer who audited the Markdown, which is the artefact designed to be
audited, would have seen the truth and had no reason to suspect the JSON.

## What was done

### 1. Three states replace the boolean

`core/truth.py` gains `INV_HOLDS` / `INV_VIOLATED` / `INV_UNVERIFIED`,
`classify_invariants()` and `all_invariants_hold()`. `invariants_all_hold` is
true only when the `violated` **and** `unverified` lists are both empty.
`ground_truth.json` publishes the whole partition as `invariant_status`, so a
consumer that genuinely wants "no violations" asks for it by name instead of
getting it by accident out of a boolean that claims to mean more.

The partition is **total, disjoint, and sinks to the bad news**: a row counts as
`holds` only when it says so three ways at once (`status == "holds"`,
`verified is True`, `holds is True`), counts as `violated` when it says so *or*
when it is verified and does not hold, and lands in `unverified` in every other
case — a missing status, an unrecognised one, a row from a pre-V19 writer, a
truthy-but-not-`True` value. `test_invariant_status.py` asserts the three lists
reconstruct the input on thirteen adversarial rows, because a three-way split
whose third class is bypassable is the two-way split wearing a third name.

`to_markdown` now prints the three counts and the resulting boolean at the head
of the section, so the two halves of the artefact state the same verdict in the
same place.

### 2. A separate gate, not a widened one

`build.py`'s `invariant_failures` **keeps its old meaning** — a violated
invariant. The one-character repair was to widen it to "anything that is not
`invariants_all_hold`", and that is a different bug: it makes an unexercised
claim indistinguishable from a broken world, and the work each calls for is not
the same. A new gate key `invariant_unverified` sits beside it with its own
sentence. Both block the build; neither is spoken of as the other.

### 3. The claims were verified rather than waived

The three-state alone turned the catalogue red on thirteen worlds
(`evidence/01`, exit 1) — the honest state, and unshippable. There were two ways
out and only one of them is honest: waive the gate for the three known claims
(the V19 disease relocated, wearing an allowlist), or exercise them.

All three are monotonicity properties — they relate two states, and
`check(world, state)` sees one. The mechanism modules said exactly that in their
own comments and were right; what was missing was a seam. `check_invariants`
grew `edge_check(world, prev, action, next)`, run over the whole reachable
graph, and `latch_monotone`, `collection_is_monotone` and
`tile_state_is_monotone` now use it. Two of the three verify **both** clauses of
their sentence rather than the easy first one, so the verdict is not cheaper
than the prose it summarises.

All thirteen came back `true` on measured transition counts — **16 invariant
rows, 84 to 10616 transitions each** (104–1744 across the eight catalogue
worlds, 84–10616 across the five mutants) — not on a default. None is
`violated`; none remains `unverified`.

### 4. The sweep

Eight sites in `worldgen/` carry a default that could point at good news; four
are defects. `build.py`'s `gate_failures` read `totals.get(key, ())`, so a
manifest missing a gate key cleared that gate silently — the same shape, one
function from the original. `to_markdown`'s `corr.get("agrees", True)` rendered
an unmeasured rule correspondence as agreement. Full table and reasoning in
`OPTIMISTIC-DEFAULTS.md`.

## Negative controls

Both required samples run the **real command line** in a package-copy sandbox
(`tests/invariant_sandbox.py`, built on V16's precedent) and assert the
**process exit code** and **which gate line the build printed** — not a helper's
return value. Raw output: `evidence/05-negative-controls-raw.txt`.

| injection | weakening | exit | gate that fired |
|---|---|---|---|
| — | — | **0** | none (clean control) |
| `prose_only` | — | **1** | `invariant_unverified` |
| `prose_only_explicit_none` | — | **1** | `invariant_unverified` |
| `violated_state` | — | **1** | `invariant_failures` |
| `violated_edge` | — | **1** | `invariant_failures` |
| `holds_state` | — | **0** | none |
| `holds_edge` | — | **0** | none |
| `prose_only` | `pre_v19` | **0** | none — **the defect, reproduced** |
| `prose_only_explicit_none` | `pre_v19` | **0** | none |
| `violated_state` | `pre_v19` | **1** | `invariant_failures` |
| `prose_only` | `boolean_default` | **1** | `invariant_unverified` + `invariant_verdict_mismatch` |
| `prose_only` | `unverified_sinks_to_holds` | **0** | none |
| `prose_only` | `drop_unverified_gate` | **0** | none |
| `prose_only` | `all_hold_hardcoded_true` | **1** | `invariant_unverified` + `invariant_verdict_mismatch` |
| `prose_only` | `hardcoded_true_and_no_unverified_gate` | **1** | `invariant_verdict_mismatch` **only** |

The last two rows are the post-review addition (F8). Before them, hard-coding
`invariants_all_hold` to `True` was a **no-op on the exit code** — nothing read
the field this cell is named for. The final row is the isolation: the
unverified gate is removed, the boolean lies, and the verdict-mismatch gate is
the only thing left that can see the world. Raw output for all fifteen cells:
`evidence/10-negative-controls-after-review.txt`.

Four things this table is arranged to prove, beyond "the gate is red":

* **(a) is caught as unverified and (b) as violated**, and the tests assert the
  *absence* of the other gate key in each case. A repair that answered
  "unverified is not true" by refusing everything would pass an exit-code-only
  test and fail here.
* **`holds_state` / `holds_edge` are green.** Without them every red above could
  be a build that is red for its own reasons, and the new `edge_check` seam
  could be one that is red on everything — as useless as one green on
  everything.
* **`pre_v19` puts the boolean back and the defect returns**, which is the
  demonstration the work order asks for in as many words.
* **`unverified_sinks_to_holds` reproduces the bug while leaving all three class
  names in the schema.** That is the failure a three-way split invites: a third
  class that exists in the JSON and is unreachable in the code.

### One unflattering result, kept

`boolean_default` reverts **only** `all_invariants_hold` and the build stays
**red**. So the honest conjunction is *not* what stops the defect at the gate —
the separate `GATES` key is. Anyone who repairs only `truth.py` next time will
believe they have fixed this and will have fixed the reporting alone. Pinned as
`test_the_boolean_alone_is_not_what_catches_it`.

> **[OVERTURNED — adversarial F7]** The *conclusion* above is true. The test
> did not establish it. `boolean_default`'s process output was **byte-identical**
> to the unweakened run — same rc, same gate lines, same stdout — so that test
> passed whether or not the weakening had applied: a control that could not
> fail, in a file whose entire subject is controls that cannot fail. It now
> reads `invariants_all_hold` out of the produced `ground_truth.json`, which is
> the only thing the weakening moves, and a sibling asserts the *unweakened*
> run reports `false` so the assertion is measuring the patch and not a
> constant. (Since F8 added the verdict-mismatch gate the process output does
> now differ — but the artefact assertion is what makes the test honest, not
> that coincidence.)

## Measurements

| | before | after |
|---|---|---|
| `pytest worldgen -q` | 432 passed, 13 skipped | **512 passed, 13 skipped** |
| `python -m worldgen.build` | exit 0 | exit **0** |
| `python -m worldgen.build --check` | — | exit **0**, byte-identical across interpreters |
| `python -m worldgen.verify` | — | exit **0**, `green` |
| `ground_truth.json` with a `holds`-less invariant | 13 of 35 | **0 of 35** |
| worlds asserting an unexercised claim | 13 | **0** |

`verify` reports its two standing pre-registered QC misses (`RUN_STATE.md`
§gaps). They are unchanged by this cell and do not gate.

## Encountered, recorded, not fixed

`python -m worldgen.verify` rewrote eighteen committed artefacts under
`out/qc/` and left one untracked file — the side effect cell V12 measured and
registered. QC reads only `raw_trace.jsonl` (`qc/run_qc.py:81,170`) and V19
modified no trace, spec, coverage or reversibility file, so none of it is
attributable here. Reverted so this branch carries only its own change;
`evidence/08-qc-side-effect-not-ours.txt` has the diffstat and the attribution
argument. Not ours to fix.

## Deferred, with the reason

`mutate.py`'s `claims_now_false` counts violations only, so a mutation that
turns a verified invariant into an *unverified* one is invisible to it. Closing
that means a `claims_now_unverified` sibling in `MUTATIONS.json`, and
`claims_now_false` is read by name from `exam/grading/rubrics_adaptation.py` and
`exam/papers/adaptation.py` — another track's territory. Recorded at the call
site and in `OPTIMISTIC-DEFAULTS.md` §4 rather than done unilaterally.

## Downstream compatibility

`INDEX.json` and `MUTATIONS.json` changed **additively only** (41 and 31
inserted lines, zero deletions). `claims_now_false` is byte-identical for all
fifteen mutants. No key was removed or re-signed.

---

# What the adversarial pass changed

80 mutants, **30 escapees**. The three attack lines that held are recorded first
because they were genuinely attacked, not waved through; then every overturn,
each one accounted for where the original claim stood rather than by rewriting
it.

Reviewer's full report, verbatim: `ADVERSARIAL-VERBATIM.md`.
Replay of the escapees against the repaired suite:
`evidence/11-escapee-replay.txt`.

## Attacks that failed — these stand

* **(b) not over-corrected.** `violated` and `unverified` stay distinguishable
  at every layer: row `status`, `invariant_status`, the manifest row, the
  manifest totals, the gate line, the exit code. The vacuity hole is closed and
  has a positive control.
* **(c) the flip number is not read favourably.** `FLIPS.md` reports 13 *and* 0
  and explicitly refuses the flattering reading. The reviewer instrumented all
  three `edge_check`s and measured them actually firing — `latch_monotone` 111
  times, `collection_is_monotone` 94, `tile_state_is_monotone` 43 — built six
  discriminating mutants of them that went red at both layers, and re-derived
  all 35 artefacts from the generator byte-for-byte with 0 mismatches. **The
  reviewer states this attack line failed.**
* **(a) partially** — the partition itself was sound; two holes were in what
  *reads* it, below.

## Overturned

### F1 (CRITICAL) — swallowing an exception rebuilt the defect, verbatim, in the rewritten function

Replacing the two `except` bodies in `check_invariants` with a bare `continue`
makes an invariant whose check raises **on all 24 states** report
`states_checked: 24, verified: True, holds: True, status: "holds"`. **Both
gates green.** That is this cell's own sentence — "I could not check this"
written as "this holds" — reconstructed by a two-line edit inside the function
rewritten to prevent it.

The docstring spent a full paragraph justifying `raise -> violated` and **no
test pinned that the branch existed**. Prose defending a decision is not a test
of it; that is the same substitution this cell exists to punish.

Fixed: `test_a_check_that_always_raises_is_a_violation_not_a_pass`, both seams,
asserting the status, `holds is False`, and that the recorded violation carries
the exception text.

### F2 (CRITICAL) — the evidence counts were unpinned; 7 escapees

`states_checked` was written from `len(states)` **outside** the loop, so
slicing the loop header to `states[:1]` left the artefact reporting 26 states
checked that it never visited. Same for `transitions(...)[:1]`, `[::2]`, `= 0`,
and dropping the key entirely (which fell through `to_markdown`'s `or "no
states"` and rendered as a quirk).

**And stage 2 of this cell rests entirely on those numbers** — "84 to 10616
transitions, not a default". Nothing asserted they were non-zero, let alone
real. The argument was one slice away from evaporating while every artefact
still looked right.

Fixed: both counters increment inside their loop from the call that happened;
four new tests, including one where the callable counts its own invocations
(the only witness a slice cannot fool) and one that independently recounts the
world's transitions.

**A caveat that outlives this cell, and belongs in the territory's memory:**
`--check` does not protect the committed artefacts. `main()` **rebuilds `OUT`
before** `check_determinism` diffs it, so under a mutation it compares
mutated-against-mutated and reports byte-identical. `determinism_sandbox.py:12-16`
already wrote this down for V16. **The 35 committed artefacts are pinned by
`git diff` and human attention, and by nothing else.**

### F3 (HIGH) — `to_markdown` was a second classifier, and the more forgiving one

`if not inv.get("verified")` and `inv["holds"]` are *truthiness* — precisely
what `classify_invariants` refuses and what this cell's own test ("truthy is
not True") forbids one function further down. Measured: a row
`{verified: 1, holds: 1}` was `unverified` in the JSON and printed **`holds`**
on the page.

Two verdicts in one document, and **the line a human actually reads was the
kinder one**. That is this cell's thesis inverted — the Markdown more
optimistic than the JSON.

Fixed: the Markdown *calls* `classify_invariants`, per row, via `_sole_class`.
One classifier, asked twice.

### F8 (HIGH) — the load was moved off the boolean, not onto it

After the first pass, **no gate read `invariants_all_hold`** — `build.py` read
the two class lists directly. Hard-coding the boolean to `True` left
`build_rc=0`. It is the field this cell is *named* for, it is published in all
35 ground truths and all 35 `INDEX.json` rows, and it is the only invariant
field a naive downstream reads.

The reviewer's framing is the one that stings and is correct: **this
territory's last two findings were both "a verdict nobody exits on is a
decoration", and the fix for this one moved the load off the field instead of
onto it.**

Fixed: new gate `invariant_verdict_mismatch`, which cross-checks the published
boolean against the partition it summarises rather than re-deriving it.
Isolated by the `hardcoded_true_and_no_unverified_gate` weakening, where it is
the only gate left that can see the defect — measured rc **1**.

*Side effect worth its own line:* adding this gate broke the `pre_v19`
weakening, because reverting the boolean makes it disagree with the lists and
the new gate caught it. The historical defect stopped reproducing. `pre_v19`
now removes both V19 gates, as true pre-V19 shape requires.

### F4 (HIGH) — the whole Markdown layer had no negative control; 4 escapees

All 165 invariant bullets in the shipped catalogue are `holds`; zero violated,
zero unverified. So the branches rendering `**VIOLATED**` and `**unverified**`
were **never executed by any test**. Deleting either literal, hard-coding the
summary counts to `true`, and dropping the unverified bullet entirely — all
four green. **A layer exercised only on inputs that cannot go wrong is not
exercised.**

Fixed: nine tests rendering from injected violated/unverified/truthy rows,
asserting the literals, the counts, the verdict line, and that every invariant
reaches the page.

### F6, F9, F10 — smaller, same shape

* **F6** `cert.get("blocking_entities") or []` (in the file this cell named)
  collapsed "the analysis ran and found none" into "the analysis is absent" —
  fixed, the two now render differently. `test_build_gate.py`'s `pytest.skip`
  when `INDEX.json` is missing made the *only* test holding gate keys against a
  real manifest evaporate silently — now an assert.
* **F9** with explicit world ids the mutant half is never built or gated, and
  the green banner said "N catalogue world(s) green" without mentioning it —
  covering 20 of 35 worlds, including **5 of the 13 this cell is about**. The
  banner now names what it did not check.
* **F10** a row with no `name` was invisible to the name-keyed partition test.
  Conservation is now enforced inside `classify_invariants` via `_conserving`,
  which is a separate function so that it can have a negative control of its
  own — a check written inline can only be exercised by breaking the code
  around it, which means in practice it never is.

## Registered, deliberately not fixed — and it is bigger than V19

`core/reversibility.py:251-273`: `deferred` and `unreachable` **both** stay out
of `claim_disagreements`, which is the build gate. Independently re-measured
here: **90 of 218 published claims (41.3%) have never been checked, and all
35/35 worlds carry at least one.** The most common is `walk`, written as prose
and recorded `deferred` in **every world**. `claim_disagreements` is empty
across the whole catalogue — the gate has never fired because the only class
that can trip it is empty.

**This is `check: None` under a different word, at seven times V19's scale.**
`truth.py:23` still says "the reversibility stamp is measured" and
`README.md:118` reads the same way; here **both halves are optimistic**, which
is worse than the split V19 found.

Not repaired here, for the reason RES-3 gave when it found V19 inside V16 and
declined to fix it in passing — a repair seven times the size of the cell it
rides in makes the acceptance line something nobody can review. Proposal
written for the board:
`INBOX-PROPOSAL-20260729-reversibility-deferred-is-the-same-disease-at-7x-scale.md`
(kept in this run directory rather than filed into `monitor/inbox/`, which is
outside this cell's write territory). It carries a companion item: **37 rules
self-exempt from `declared_never_fires` via `cascade: True` / `clause: True`,
declared by the rule and independently checked by nobody.**

## Score after the repair

All 13 reconstructable escapees replayed against the repaired suite:
**13 red, 0 still escaping** (`evidence/11-escapee-replay.txt`).

---

# The reviewer's Section 5, verbatim

Reproduced word for word from `ADVERSARIAL-VERBATIM.md`, not summarised.
What a review could **not** reach is the part a later reader most needs and the
part most likely to be smoothed away in a retelling.

## 5. WHAT I COULD NOT CHECK

- **`python -m worldgen.verify`.** Not run, per the work order — cell V12's known `out/qc/` rewrite. Its interaction with the new `invariant_status` key is therefore untested by me; `qc/run_qc.py:81,170` reads only `raw_trace.jsonl`, which V19 did not touch, so I have no reason to expect one.
- **Other tracks' full suites.** I ran `exam/tests/test_worldgen_papers.py` (95 passed) because it reads the regenerated artefacts directly. I did not run all of `exam/`, `battery/`, or `theory-compiler/` — out of territory, and my grep found no consumer of any invariant verdict outside `worldgen/`.
- **Whether the three monotonicity claims are *true statements about the mechanisms*** as opposed to true on the reachable graphs of these 35 worlds. The `edge_check`s are exhaustive over each world's reachable graph, which is the strongest available claim; a mechanism-level proof is out of scope for a build gate.
- **Whether `deferred`/`unreachable` reversibility claims (F5) are individually correct.** I established that 90 of 218 are unexercised and that the gate cannot fail on them. I did not attempt to verify any of them, and I did not fix it — it is a separate cell.
- **The exact state of the branch at the time you read this.** The implementer committed `23ec179` and has continued editing `worldgen/RUN_STATE.md` and two run-directory files during this review. Everything I measured is pinned to the MANIFEST hashes, which all still matched at the end of the review. I made no commits and dirtied no artefacts.
