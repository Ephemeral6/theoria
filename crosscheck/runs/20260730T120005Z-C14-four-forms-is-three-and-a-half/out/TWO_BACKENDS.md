# Two PDDL backends, one front end, and nobody wrote down that they are two

This document exists because the C14 census nearly published a wrong headline. It
measured `theory_compiler.generators.gen_pddl`, found 0 of 303, and concluded that
the framework's four-forms claim was false. There is a **second PDDL backend** in
the repository, it works, and it is the one behind every planning number in the
paper. The finding is still real; its scope is much narrower than first written.

## The two

| | **A — `theory-compiler/src/theory_compiler/generators/gen_pddl.py`** | **B — `cold-start-a0/compile/gen_pddl_a0.py`** |
|---|---|---|
| parser | `theory_compiler.parser.theory_parser.parse_theory` | **the same** (via `compile_a0.py:30,44`) |
| language accepted | frozen `dsl_grammar_v0.1` | the same grammar |
| *class of theories* accepted | world-general in shape | **hard-fitted to the A0 family** |
| committed domains | 2 (both live-arm) | **25** |
| actions | 3 + 3 | **263** |
| well-formed and non-empty | **0** | **263 (100 %)** |
| Fast Downward | rejects, or accepts the vacuous ones | **accepts, rc 0** |
| state model | `(at ?o - object ?c - cell)`, `(free ?c)`, `adjacent-*` | `(at ?c)`, `(passable ?c)`, `adj-*`, `(switched)` |

**They read the same language and emit incompatible encodings of it.** Neither
document in either track compares them.

## A is general in shape and broken in content

Run over every rule-bearing DSL in the repository: 303 actions, **0** semantically
non-empty and well-formed — 190 empty effects, 58 undeclared variables, 45
undeclared predicates, 39 empty preconditions, 18 rules refused outright.
Details: `census.md`, `ROOT_CAUSE.md`.

A is the backend on **both documented compile paths from the two books**:

* the live arm — `theoria-arm/inner/books.py:229` imports A, inside a `try/except`
  that records the error and continues, with `result["ok"]` keyed on **Python
  only** (`books.py:202`). That is why the only two live-run `domain.pddl` in the
  repository are the empty ones;
* the handover packages — `theory_compiler/handover.py:91` imports A, and
  `check_pddl` (`handover.py:1209`) correctly refuses its output, which is why
  both packages ship a stated 3-of-4.

## B is correct in content and hard-fitted in shape

B is not a general PDDL backend that happens to live elsewhere. Its limits are
structural, and each is a line of code:

| B requires | where |
|---|---|
| an object literally named `Cart` — else `StopIteration` | `gen_pddl_a0.py:113`, `:66` |
| a barrier named `Door`, a switch named `Button` or `Switch` | `:115-117` |
| exactly five event kinds (`moved`, `jumped`, `recolored`, `vanished`, `appeared`) — anything else raises | `:164-176` |
| every rule to carry a `GuardAction` whose 2nd argument is a direction | `:78-82` |
| portal landing sites only from a landmark literally named `portal_exit` | `:299-301` |
| a `Problem` derived from a **played trace** — B cannot emit from the manual alone | signature `:110`; `compile_a0.py:46` |

**Its entire state space is one cell plus one boolean** (`gen_pddl_a0.py:143-152`).
It cannot represent a second moving object, a counter, or a multi-instance type.
The repository already records what that costs — `cold-start-a3/a6carry/pddl_push.py:1-22`,
**D-A6-001**:

> `gen_pddl_a0`'s state is one cell and one boolean … So a manual with a pushable
> block compiles to a domain in which the block never moves … the planner returns
> **UNSAT for a manual that is correct**, silently and with confidence.

B also has **no `semantics:` guard** — A refuses a manual declaring `frame reset` /
`conflict priority` / `cascade multi_frame` (`gen_pddl.py:24-42`); B never mentions
semantics and is only covered transitively because its driver runs the Python
generator first. And B has been **re-patched for every new world**: `compile_a2.py:128`
(arena addressability), `compile_a3.py:245-377` (per-landmark portal predicate,
D-A3-005), and `a6carry/pddl_push.py`, which is whole-domain *text surgery* and says
so at line 26: *"a post-hoc rewrite of generated text and it is coupled to that text"*.

B works on the A0 family because each arm patched it into working there.

## Every planning number in the paper is B's

`sections/03_a0.md:22-23` reports *"a SAT plan of **12 steps** that the world
agrees with frame-for-frame (M4)"*. `cold-start-a0/artifacts/fd_real.json`,
instance `a0-base`, `"status": "SAT"`, `"length": 12`, real Fast Downward,
`"identical_plan": true`:

```
(push-right c5-1 c5-2) … (press-left c3-3 c3-2 c4-5) … (push-up c3-7 c2-7)
```

Those are B's fingerprints and only B's: the cell naming `c%d-%d` is
`gen_pddl_a0.py:42-43`, and a three-parameter `press-left` is `:241-266`. Backend A
names cells `cell-r-c` (`gen_pddl.py:151`) and has no `press-left` at all. A2
(`compile_a2.py:51,179`), A3/A6 transfer (`compile_a3.py:50,527`,
`a6carry/forms.py:52,110`) and the ablation arm (`compile_abl.py:51`) all call B.

**So no empirical planning claim in the paper is falsified by A being broken.**
What A being broken falsifies is the *framework* claim about the fourth form.
Keeping these two apart is the whole point of this document.

## The sharpest single fact

`theory-compiler/handover_packages/a0-cart/manual/MANUAL.dsl` is **byte-identical**
to `cold-start-a0/theory/theory.dsl` (verified: one sha256 across both).

So the repository simultaneously:

* ships that manual with a working, real-Fast-Downward-solved PDDL form under
  `cold-start-a0/theory/generated/domain.pddl` (6 actions, e.g.
  `:precondition (and (at ?from) (adj-left ?from ?s) (not (switched)))`), and
* publishes on that package's own front page that its planning form could not be
  generated — `handover_packages/a0-cart/README.md:33-34`:
  *"`planning_domain` — StripsError: action 'push-up' mentions undeclared predicate
  'adjacent-above'"*.

Both statements are true. They are about different programs, and nothing in the
package says so. **D-TC-031** (`theory-compiler/DECISIONS.md:597-613`) even measures
backend A's failure *on this exact file* and pins it in a test, without noting that
the manual's shipped PDDL comes from a different generator.

## What is recorded, and what is not

**Recorded** — the fork's origin, one-way:

* `cold-start-a0/DECISIONS.md:170-184`, **D-A0-011**: *"Reuse `theory_compiler.parser`
  … and write A0's own backends in `cold-start-a0/compile/`. Nothing upstream is
  modified … recorded as a **gap in the compiler track's coverage**, not as a
  defect."*
* `theory-compiler/runs/P-10/RUN_STATE.md:213-216` — the only theory-compiler-track
  acknowledgment that B exists (and now partly stale: `gen_pddl.py:47` later grew a
  `problem` parameter).
* B's own defect history is well kept: D-A0-019, D-A2-006, D-A3-005, D-A6-001.

**Not recorded anywhere:** that the two backends emit incompatible encodings of the
same manual; that the paper's planning results and the handover packages' PDDL
refusal concern *different generators*. No test cross-checks them. It is a **known
fork with an undocumented divergence** — each side knows its own half.

## The honest headline

> The repository has two independent PDDL generators over one shared front end.
> The framework's general backend produces nothing usable — 0 of 303 actions
> well-formed and non-empty — and it is the one on both documented compile paths
> from the two books, so the live arm's handbook and both handover packages carry
> no working planning form. A second, hand-fitted backend produces everything the
> paper reports, but its state is one cell and one boolean, it hard-codes the
> object names, it needs a played trace rather than the manual alone, and it
> returns a confident UNSAT for a correct manual containing a second moving
> object. Neither is "the manual compiles to PDDL" in general form, and no
> document in either track records that these are two different programs.

## Why the census could not see this

The census's population is *every `.dsl` in the repository, as `gen_pddl`'s own
front end sees it* — a corpus defined by **input** files. Backend B leaves no trace
in such a corpus, because it is a different **output** path over the same inputs.

The instrument also had **no positive control**: it was never shown a known-good
domain and asked to score it GOOD. B is exactly that control, and it was found by
an adversarial review of the finished document, not by the measurement. It is now
wired into the gate (`crosscheck/tools/c14_positive_control.py`), where absence of
B is reported RED rather than skipped — a control that did not run is not a pass.
