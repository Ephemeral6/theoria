# How deep is the gap? — 0 is the number, but not all zeros are the same depth

> **Scope, added after the fact.** Everything here concerns
> `theory_compiler.generators.gen_pddl` only. A second PDDL backend
> (`cold-start-a0/compile/gen_pddl_a0.py`) exists and produces 263/263 non-empty,
> Fast-Downward-accepted actions across 25 committed domains. See
> `../../../FOUR_FORMS_TRUTH.md` §0 and `TWO_BACKENDS.md`.
>
> **Two numbers below were corrected after an adversarial pass.** The
> "naming-only" bucket was published as 94 and described as structurally correct;
> it is **37**, and the 57 that were wrongly folded in are not near-correct at all.
> The corrected table is immediately below; the original error and why it happened
> are kept at the end of this file rather than silently rewritten.

`0 of 303` is correct and survives every attack. Reported alone it is still
misleading, in the *opposite* direction from the usual one: it reads as "the PDDL
backend is an unimplemented stub", and that is not what the corpus shows. A third
of the compiled actions carry real semantic content and fail on a vocabulary
mismatch across **eight identifiers**.

Both facts belong in the paper. Stating only the first overstates the damage;
stating only the second hides that the form does not currently work at all.

## Every compiled action, bucketed by repair distance

285 compiled actions (+18 in the 3 refused files = 303 owed):

| bucket | actions | what is wrong | depth |
|---|---|---|---|
| **vocabulary-only** — both bodies non-empty, sole defect `undeclared-predicate` | **37** | emits `adjacent-above`, declares `adjacent-up` | shallow: 3 names |
| both bodies non-empty, **undeclared variable** | 57 | effect moves an object to an unbound `?dest` | **deep** — same missing event model as the 152 |
| no effect — precondition non-empty | 152 | `:effect (and (and))` placeholder | deep: the event model is absent |
| vacuous — both empty | 38 | asserts nothing at all | deep |
| empty precondition **and** undeclared variables | 1 | `budget-advances` | deep |
| **GOOD** | **0** | — | — |

37 + 57 + 152 + 38 + 1 = 285 compiled (+18 in the 3 refused files = 303 owed).
Split of the 57 + 37 by literal counts, from `census.json`:

| profile | count | sole defect |
|---|---|---|
| prec 3, eff 4 | 36 | `undeclared-predicate` |
| prec 2, eff 4 | 1 | `undeclared-predicate` |
| prec 3, eff 4 | 8 | `undeclared-predicate` **and** `undeclared-variable` |
| prec 1, eff 4 | 49 | `undeclared-variable` |

## The eight names

Undeclared **predicates** — 3 distinct, and the mismatch is inside one generator:
it *emits* `adjacent-above` / `adjacent-below` while *declaring* `adjacent-up` /
`adjacent-down` in the same domain's `(:predicates ...)` block.

| name emitted | declared instead | actions |
|---|---|---|
| `adjacent-above` | `adjacent-up` | 22 |
| `adjacent-below` | `adjacent-down` | 22 |
| `boundary-above` | `boundary-up` | 1 |

Undeclared **variables** — 5 distinct, used in a body but absent from
`:parameters`:

| name | actions |
|---|---|
| `?dest` | 50 |
| `?block-pos` | 12 |
| `?block` | 8 |
| `?spent` | 1 |
| `?spent-pos` | 1 |

## Worked example — what a "naming-only" failure actually looks like

`ablation-arm/theory/a0_base.dsl`, action `push-up`, generated verbatim:

```pddl
  (:action push-up
    :parameters (?cart - cart ?up - object ?dest - cell ?cart-pos - cell)
    :precondition (and
      (at ?cart ?cart-pos)
      (adjacent-above ?cart-pos ?dest)
      (free ?dest)
    )
    :effect (and
      (not (at ?cart ?cart-pos))
      (at ?cart ?dest)
      (not (free ?dest))
      (free ?cart-pos)
    )
  )
```

Three precondition literals, four effect literals, correct add/delete structure,
`?dest` properly declared here. This is a *real* push action. It is invalid for
one reason: the domain declares `adjacent-up`, never `adjacent-above`. Fast
Downward, which has never heard of the generator, stops at exactly that token:

```
	->Parsing action 'push-up'
	->Parsing precondition
Expected logical operator or predicate name
Got: adjacent-above
```

Verified by hand against the raw generated PDDL, not taken from the census.

## The 57 are not near-correct — the error this file originally made

The 49 `prec 1, eff 4` actions have a precondition consisting only of
`(at ?cart ?cart-pos)` and an effect that moves the object to an unbound `?dest`.
From `cold-start-a3/theory/push/domain.dsl`:

```pddl
  (:action step-left
    :parameters (?cart - cart ?left - object ?cart-pos - cell)
    :precondition (and (at ?cart ?cart-pos))
    :effect (and (not (at ?cart ?cart-pos)) (at ?cart ?dest)
                 (not (free ?dest)) (free ?cart-pos)))
```

Declaring `?dest` — the "one-line repair" — yields a **valid** action that
teleports the cart to any cell in the arena, unconditionally, and it would pass
this census's GOOD bar. The siblings are worse: `shove-up/down/left/right`
(8 actions) move the cart rather than the block, the effect copy-pasted from
`step-*`; `block-left`/`block-right` move `?block` from `?block-pos` to `?dest`
with all three unbound and no precondition mentioning the block at all.

**So for these 57 the real defect is the missing event model — the same failure as
the 152 — wearing a different label.** Counting them as "one rename away" was
wrong, and it was wrong in the direction that flatters the generator. The genuine
vocabulary-only set is 37 of 285, **13 %**, not a third.

## What this means for the two audiences

**For the paper.** This backend delivers nothing usable — 0 of 303, no slicing
rescues it, an independent planner confirms it. But the correct characterisation
of *why* is not "PDDL was never implemented", and it is also not "a third of it
nearly works". It is: for **13 %** the only defect is a three-name vocabulary
mismatch; for the remaining **87 %** the backend has no event model to emit, whether
that surfaces as an empty effect (152), an unbound destination (57) or a wholly
vacuous action (38). Write the 13/87 split, not the 33/67 one.

**For the theory-compiler track.** The 37 vocabulary-only actions are the shallow
part — but see the correction below before costing the repair. This territory has
not attempted the fix and will not: `theory-compiler/` is the other track's and not
one byte of it may be modified from here. The 152 empty-effect actions are a
different and much larger problem, and the 3 refused files may not be reachable in
STRIPS at all. Full diagnosis and an ordered fix proposal: `ROOT_CAUSE.md`.

---

## CORRECTIONS — two, and both went in the direction that flattered the generator

**Correction 1 — the bucket itself.** This file first published a "naming-only"
bucket of **94** and called it structurally correct PDDL. The real figure is
**37**; the other 57 carry an unbound `?dest` and are not near-correct (see above).
Found by an adversarial review of the finished document, not by the measurement.

**Correction 2 — "one change" was wrong, and the way it is wrong matters.**
An earlier revision said the naming-only actions "become candidates for GOOD in one
change". **That is false.** A read of the generator found a fifth defect that none
of the census's four criteria can see:

`gen_pddl.py:300-307` makes a `:parameters` entry out of *every* `NameRef`
argument, including the direction constants `up`/`down`/`left`/`right`, typing them
`object` because they are not declared object types. **No object of type `object`
is ever declared in the generated problem, so the parameter cannot bind and the
action disappears at grounding.** Measured against the track's own `strips.ground`,
with only the predicate-name defect patched:

```
with the ?up / ?down parameter:      0 ground actions
without it:                        144 ground actions
```

So reconciling the identifiers makes the domain *parse* and leaves it grounding to
**zero actions**. The repair distance for even the 37 is at minimum two independent
changes, not one.

**The general lesson is more important than the correction.** The census's bar —
non-empty precondition, non-empty effect, no undeclared variable, no undeclared
predicate — is a test of well-formedness and non-vacuity. It is **too lenient, not
too strict**: an action can satisfy all four and still ground to nothing, still
carry an inverted precondition (`GuardPredicate.negated` is never read by this
backend), or still let a teleport land anywhere (declared landmarks become free
cell parameters). `0 of 303` is therefore a **ceiling on correctness, not a floor
on brokenness** — the true number of *usable* actions cannot be higher than 0 and
the defect list cannot be shorter than four classes. The headline 0 does not
weaken; the estimate of what a fix costs was too optimistic, and is corrected
upward.

**Do not report "37 nearly work" as progress.** Nearly-valid PDDL is invalid PDDL;
a planner rejects the file. The number today is 0.

**Both corrections ran the same way, and that is worth naming.** Each original
figure made the generator look closer to working than it is — 94 rather than 37,
one change rather than two. Neither was a transcription slip; both came from
taking a defect *label* as a proxy for how broken an action is, when the label only
records which validity rule it tripped. When an error keeps landing on the same
side, the method has a bias, not bad luck.
