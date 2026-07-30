# How deep is the gap? — 0 is the number, but not all zeros are the same depth

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
| **naming-only** — precondition AND effect both non-empty | **94** | uses an identifier nobody declared | shallow: 8 distinct names |
| no effect — precondition non-empty | 152 | `:effect (and (and))` placeholder | deep: the event model is absent |
| vacuous — both empty | 38 | asserts nothing at all | deep |
| no precondition — effect non-empty | 1 | always applicable | shallow |
| **GOOD** | **0** | — | — |

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

## What this means for the two audiences

**For the paper.** The claim "four co-derived forms" is false today — 0 of 303,
no slicing rescues it, and an independent planner confirms it. But the correct
characterisation of *why* is not "PDDL was never implemented". It is: the backend
emits structurally correct PDDL for a third of the corpus and then invalidates it
with an eight-identifier vocabulary bug, and for the other two thirds it has no
event model to emit. Write both numbers.

**For the theory-compiler track.** The 94 naming-only actions are the shallow
third — but see the correction below before costing the repair. This territory has
not attempted the fix and will not: `theory-compiler/` is the other track's and not
one byte of it may be modified from here. The 152 empty-effect actions are a
different and much larger problem, and the 3 refused files may not be reachable in
STRIPS at all. Full diagnosis and an ordered fix proposal: `ROOT_CAUSE.md`.

---

## CORRECTION — "one change" was wrong, and the way it is wrong matters

An earlier revision of this document said the 94 naming-only actions "become
candidates for GOOD in one change". **That is false.** A subsequent read of the
generator found a fifth defect that none of the census's four criteria can see:

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

So reconciling the eight identifiers makes the domain *parse* and leaves it
grounding to **zero actions**. The repair distance for those 94 is at minimum two
independent changes, not one.

**The general lesson is more important than the correction.** The census's bar —
non-empty precondition, non-empty effect, no undeclared variable, no undeclared
predicate — is a test of well-formedness and non-vacuity. It is **too lenient, not
too strict**: an action can satisfy all four and still ground to nothing, still
carry an inverted precondition (`GuardPredicate.negated` is never read by this
backend), or still let a teleport land anywhere (declared landmarks become free
cell parameters). `0 of 303` is therefore a **ceiling on correctness, not a floor
on brokenness** — the true number of *usable* actions cannot be higher than 0 and
the defect list cannot be shorter than four classes. Nothing in this document's
headline weakens; the estimate of what a fix costs was too optimistic, and is
corrected upward.

**Do not report "94 nearly work" as progress.** Nearly-valid PDDL is invalid PDDL;
a planner rejects the file. The number today is 0.
