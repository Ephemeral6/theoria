# DRIFT-the-abstract-claims-four-forms-and-the-shipped-packages-refuse-the-fourth

severity: high
dimension: 2 (基准漂移) → 3 (证据漂移)
cycle: OPS-A 53 (filed post-close, from the dimension-2/5 gatherer dispatched before `FLEET_PAUSE`)
pin: `d1da2c9c`. I re-verified every load-bearing fact below against the live tree myself.

## claim

**`Theoria.md`'s constraint 1 — the architectural commitment the whole project is named for —
is met at 3.5 of 4 forms, and the paper's abstract states it as 4 with no qualification.**
The gap is not hidden anywhere else: the compiler discloses it exemplarily, the verify gate
encodes it as a named constant, and a board item is open on it. **The one place it is not
disclosed is the document that makes the claim to readers.**

## evidence

### What the baseline requires

`Theoria.md:239`, constraint 1, verbatim:

> `| 1 | 理论必须可执行——升级为同源多形态(DSL 生成 Lean + Python + PDDL + 渲染) | 证明者、执行器、规划器、人,读的是同一本书 |`

### What the paper says

`papers/phase1-workshop/PAPER.md:51-52`, verbatim, in the abstract:

> compiled to four co-derived forms — Lean,
> Python, PDDL and Markdown — and certified in two layers…

```
$ grep -c "planning_domain\|handover_packages" papers/phase1-workshop/PAPER.md
0
```

**Zero mentions.** The paper does disclose a *different* PDDL defect at `:1660` (a single-portal
limit producing confident UNSAT for a correct manual) — so the omission is not a policy of
silence about PDDL. It is this specific gap that is absent.

### What the tree actually ships

**Both shipped handover packages refuse the PDDL forms outright.** Read from
`theory-compiler/handover_packages/*/MANIFEST.json`:

| package | english | executable | proof | planning_domain | planning_problem |
|---|---|---|---|---|---|
| `a0-cart` | generated | generated | generated | **refused** | **refused** |
| `a0-sokoban2` | generated | generated | generated | **refused** | **refused** |

Reasons recorded verbatim in the manifests — and they are good reasons:
`a0-cart` — *"StripsError: action 'push-up' mentions undeclared predicate 'adjacent-above'"*;
`a0-sokoban2` — *"UnsupportedClause: free(Box.pos) names its cell through an object, which
excludes that object from its own occupancy test… **Refusing rather than dropping the
precondition.**"*

`Theoria.md:86` and `:257` make the handover package **the artefact a fresh reader is handed.**
It contains three of four forms.

**And where a real world was theorised, the fourth form is generated but says nothing.**
`theoria-arm/runs/20260728T015354Z-g50t-first-contact/books/generated/domain.pddl:20-32`
(`g50t-5849a774` is development pile; this is a generated form, no game frames read):

```
  (:action key5-advances-marker
    :parameters ()
    :precondition (and
    )
    :effect (and
      (and)
    )
  )
```

Repo-wide measurement over every tracked `domain.pddl` — **this number has not been published
before**:

```
tracked domain.pddl files: 154        total actions: 603
actions with empty effect (and (and)):  8
actions with empty precondition (and ): 9
empty-effect actions by top dir: {'theoria-arm': 8}
all actions by top dir: {'a0-spike':2, 'ablation-arm':28, 'cold-start-a0':38,
  'cold-start-a2':17, 'cold-start-a3':180, 'engine-rig':327,
  'theoria-arm':9, 'theory-compiler':2}
```

**8 of 603 actions repo-wide are semantically empty, and all 8 are in `theoria-arm/` — 8 of
that directory's 9 actions.** The offline tracks are clean. `theoria-arm/` is the online arm:
the only manual an LLM wrote against a real ARC game rather than against a world we built
ourselves. **The form degrades exactly where the claim is load-bearing.**

### The verify gate encodes the shortfall as a constant

`theory-compiler/verify.py:90`, with the docstring at `:14` that states what the gate exists
to prove:

```python
:14   "it does not say two books compiled to four forms this afternoon"
:90   MIN_GENERATED_FORMS = 3
```

The reason is recorded honestly at `:84-89` — five forms attempted, two refuse on declared
grounds, three generate. **But a gate that green-lights the territory at three cannot fail
when the fourth stops existing**, which is the definition of a form dropping out of the verify
path. Criterion (ii): no negative sample is possible while the floor is 3.

## why this is drift and not merely an open bug

The engineering here is **exemplary and I want that on the record**: the compiler refuses
rather than fabricating (`theory-compiler/src/theory_compiler/handover.py:64-66` records that
`gen_pddl` used to invent object placements and now refuses to write `problem.pddl` at all if
it cannot — that is `Theoria.md:243` constraint 5 working); `a0-cart/README.md` ships a
five-row form table with `**no — see below**` in two rows and the line *"This is stated rather
than hidden. A package quietly missing a form would be read as the reader's failure to find
it."*

**That sentence is the standard this report holds the paper to.** Every layer discloses the
gap except the one a reader outside the repo will actually read. Dimension 3 exists because
this project has twice shipped a conclusion its artefacts did not support; here the artefacts
support a *weaker* conclusion than the abstract states, and the artefacts say so themselves.

**PDDL is not vestigial**, and the report should not be read that way:
`cold-start-a0/certify/fd_conformance.py` feeds `cold-start-a0/theory/generated/domain.pddl`
to Fast Downward, called from the suite at `cold-start-a0/tests/test_followups.py:230-231`.
The form round-trips through a real planner somewhere. It is vestigial **in the online arm and
in both shipped packages** — which is the half that carries the claim.

## prior art — the code half is known and open; the paper half is not

`monitor/board/claimed/C14-four-forms-is-three-and-a-half.W-1710.md` is **open and claimed**
(`disk`), and names `theory-compiler/tests/test_writes.py:377
TestBackendObligationShortfall`, whose docstring reads *"the PDDL form of A0 has a
button-press that presses nothing"*, with `EMPTY_EFFECT` and `UNDECLARED_DEST` pinned as
constants at `:395-396`. Its promised deliverable directory `crosscheck/` **does not exist**,
and no file in this increment addresses it.

**What is new here:** the repo-wide 8/603 measurement and its localisation to `theoria-arm`
(C14 asserts it of one run directory; measured, it holds for 8 of 9 actions across all that
arm's generated domains, and the offline tracks are clean); the two shipped packages' refusal
status; `MIN_GENERATED_FORMS = 3` as a gate that cannot go red; and **the abstract's
unqualified claim, which C14 does not cover — C14 is about the code.**

*One correction to C14's own text, in its favour:* its extension census (*"3 dsl / 6 json /
4 lean / 15 md / 4 py, 零 pddl"*) initially looked like a mismatch against my per-package
numbers. It is not — C14 summed both packages and I split them. **Totals agree exactly.**

## suggest (monitor rules; I changed nothing, and `papers/` is RES-2's alone)

1. **Qualify the abstract, or qualify the claim.** One clause — naming that the planning forms
   are refused for two declared reasons in the shipped packages, and that the online arm's
   domain is inert — costs the paper nothing and is the difference between a claim the tree
   supports and one it does not. **`monitor/CHARTER.md:25` gives paper prose to RES-2 alone,
   so this must go to RES-2 as a proposal, not be applied by anyone else.** RES-2 has been
   without a heartbeat for ~9 h, which is a dependency worth knowing.
2. **Give `MIN_GENERATED_FORMS` a negative sample, or make it 4 with an explicit declared
   waiver.** A floor of 3 under a docstring naming 4 is the exact "check that cannot go red"
   shape; a waiver with an owner and a reason is honest, a silent floor is not.
3. **C14 needs its scope corrected before anyone works it** — `crosscheck/` does not exist,
   and the finding is repo-wide-measurable rather than one-directory. The measurement above
   is the deliverable it asks for.

## what I could not prove

* That no planner will read the online arm's domain. That claim is
  `theory-compiler/tests/test_writes.py`'s, not mine — I did not run FD's translator against
  the generated domains (C14's step 2). An action with `:parameters ()` and
  `:effect (and (and))` is trivially inert regardless, which is weaker but sufficient here.
* Whether the abstract's wording predates the refusals. `PAPER.md` is **untouched** by this
  increment (`git diff --name-only 333a2f4e..d1da2c9c -- papers/phase1-workshop/PAPER.md` is
  empty), so the claim is not newly introduced — but I did not date it against the refusals,
  and "was true when written" would change the disposition from *drift* to *fixed-since*, as
  it did for another finding this cycle.
* Constraints 2, 3, 5, 7, 8, 9 end to end — outside these two dimensions. Recorded in
  `monitor/audit/state.json` with the monitor's own stale-table caveat attached.
