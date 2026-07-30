# Pre-registration — V6-V22-wintighten-absent-vs-below

Written and committed **before** the implementation ran. `git merge-base
--is-ancestor <this commit> <the commit that carries the results>` is the check
that this is true; the run directory keeps the two commit ids.

* prompt_id: `V6-V22-wintighten-absent-vs-below`
* branch: `agent/v22-wintighten-absent-vs-below`
* base_commit at pre-registration: recorded in `MANIFEST.json` as `base_commit`
* territory: `proxy/` only. `exam/` is not touched, not one byte.
* no network, no API, no `.env`, no sealed-pile contact.

## The defect being addressed

`proxy/variants.py::VariantRuntime.after` treats `have is None` and
`have < needed` as the same condition. On a world that reports no score
(`score` is always `None`), every `WIN` is rewritten to `NOT_FINISHED` at every
`require` value. Reading "absent" as "below" is the conservative side and stays;
what is being fixed is that the collapse leaves no distinguishable trace.

## What I will judge the result by

These are the criteria. They are written down now so that "it passed" cannot be
arranged afterwards by moving them.

**P1 — the two paths are distinguishable in the record.**
An `applied` record produced by an absent score and one produced by a shortfall
must differ in at least one field whose name says which happened, and the
difference must survive JSON round-tripping (it goes into the ledger).
FAIL if the two records can be equal for any input.

**P2 — the first absent-driven rewrite is loud, and loud is defined as
"something exits non-zero".**
There must exist at least one consumer that reads the new field and changes an
outcome — a non-zero exit code, a refused verdict, or a record that a gate
reads. A field that no code path reads is decoration and P2 fails. The
consumer must be exercised by a test that fails if the consumer is removed.

**P3 — the negative control fires on both kinds of session.**
Two sessions are built: one whose bodies carry `score` (a *scoring* session),
one whose bodies carry `score: None` throughout (a *scoreless* session).
Required:
  * P3a: on the scoreless session the guard flags the degeneracy;
  * P3b: with the flag removed (the marker deleted from the record before the
    consumer reads it), the same session is **passed** by the consumer — i.e.
    the guard is what catches it, not something else;
  * P3c: on the scoring session the consumer passes;
  * P3d: on the scoring session the guard can still be made to go red by a
    construction that deserves it (a forged degenerate marker), so "passes on a
    scoring session" is a fact about the input and not about the guard being
    inert.
FAIL unless all four hold. P3d is the half that stops "it passed on one kind of
session" from counting as a negative control.

**P4 — the mutation surface is wider than the test surface.**
At least 15 distinct source mutations, spread over all three files that carry
the new behaviour (the rewriter, the consumer, the wiring), each run against
the whole suite. Every mutant must be killed. A surviving mutant is reported as
a survivor, not quietly dropped — and one mutant is deliberately included that
I expect to survive (a pure-wording change) so that "all killed" is not the
only outcome the harness can print.
FAIL if fewer than 15 mutants, or if a behavioural survivor is found and not
reported.

**P5 — the certificate-grammar adjudication lands as an executable rule.**
Whatever I decide about a fourth certificate form, the outcome must include a
rule that a program enforces, not only a paragraph. If the decision is "do not
add a fourth form", then "this class of variant does not count toward the
reason score" must be checkable by running something, and that something must
be able to go red. `exam/` is off limits, so the enforcement lives on the
`proxy/` side of the boundary and says so.
FAIL if the adjudication produces only prose.

**P6 — the whole suite stays green.**
`python -m pytest proxy -q` exits 0, with the observed output pasted into the
run record including the exit code. No pre-existing test is edited to make room
for the new behaviour; if one has to change, the change and its reason are
called out separately.

## What would make me say this failed

* Any `applied` record where an absent score and a shortfall are
  indistinguishable (P1).
* A marker with no reader (P2).
* A negative control that only ever ran on the scoreless session (P3).
* Fewer than 15 mutants or an unreported survivor (P4).
* An adjudication that is only prose (P5).

## Deliberately not in scope

* Changing the conservative reading itself. Treating an absent score as
  satisfying `score_at_least` would let a scoreless game win a tightened
  variant outright; that is the worse side and it is not being touched.
* Anything under `exam/`. The finding is already recorded there.
* Any live API call or any decision about a specific sealed game.
