# Case study 2 · Reversibility beats coverage

**A0 saw 99 % of its world and shipped a manual wrong in three places. A0′ saw
47 % and shipped one with no errors. The controlled variable was not how much
was seen — it was whether what was seen could be seen again.**

This is the case study where a framework prediction, a design change made in
response to it, and a seeded-error experiment all land in the same directory and
can be diffed. It runs in four beats: the blind spot Theoria predicts, its
reproduction in A0, the design change, and the controlled test that closes the
loop.

---

## 1 · The prediction, made before the measurement

Theoria §1.3 says that a missing rule makes the modelled world *smaller* than the
real one and that replay — being a prediction about the past — cannot see it
([`../../Theoria.md:32-36`](../../Theoria.md)). A0's adjudication reproduced that
shape deliberately, and wrote the consequence down before scoring.

The candidate stream offered a lifted push rule across all four directions, so
the obvious move was to lift the press rule too. It was **rejected**:

> **Rejected**, and the manual is knowingly left incomplete. Constraint 5 forbids
> an entry without evidence, and the evidence for `press_up`, `press_down`,
> `press_right` is precisely zero — not thin, zero. The analogy to the lifted
> push rule is an argument, not a witness.
> — [`../../cold-start-a0/THEORIZE_LOG.md:225-230`](../../cold-start-a0/THEORIZE_LOG.md)

And then, in the same entry, the prediction:

> **the manual as written says that pushing up into the Button does nothing, and
> full-history replay will never catch that.** It is the DC22 shape from Theoria
> 1.3 — a rule that is missing rather than wrong, invisible to replay, and it
> makes the modelled world *smaller* than the real one.
> — [`../../cold-start-a0/THEORIZE_LOG.md:234-237`](../../cold-start-a0/THEORIZE_LOG.md)

The rule was entered instead as `theorem press_is_direction_free [probe: pending]`
([`../../cold-start-a0/theory/theory.dsl:60`](../../cold-start-a0/theory/theory.dsl)),
under constraint 7 — *定理未经戳探不得定案*
([`../../Theoria.md:245`](../../Theoria.md)).

## 2 · The measurement, taken at M6 behind a seal

Ground truth was first opened at M6, after M4 and M5 were both green, and only by
the scorer ([`../../cold-start-a0/THEORIZE_LOG.md:502-507`](../../cold-start-a0/THEORIZE_LOG.md)).

| measurement | result |
|---|---|
| full-history replay (what certify sees) | **276/276 frames, 22 356/22 356 pixels, 0 anomalies** |
| every reachable (state, action) pair, base world | **233/236 = 98.73 %** |
| the 3 pairs the trajectory could never contain | **0/3 = 0 %** |
| every reachable (state, action) pair, variant | **92/92 = 100 %** |
| Lean obligations discharged | **2/2**, axiom lists empty in both |

— [`../../cold-start-a0/A0_REPORT.md:38-44`](../../cold-start-a0/A0_REPORT.md);
raw at [`../../cold-start-a0/artifacts/score_vs_truth.json`](../../cold-start-a0/artifacts/score_vs_truth.json)
(`base.behavioural`: `accuracy 0.987288`, `agree 233`, `disagree 3`, `pairs 236`).

The three misses, verbatim from the artefact:

```
cart (2,2) pressed=false  DOWN   world: Button pressed   manual: nothing happens
cart (3,1) pressed=false  RIGHT  world: Button pressed   manual: nothing happens
cart (4,2) pressed=false  UP     world: Button pressed   manual: nothing happens
```

— [`../../cold-start-a0/A0_REPORT.md:48-52`](../../cold-start-a0/A0_REPORT.md).

They are the Button pressed from above, below and the right — *the three pairs
R-05 named, for the reason R-05 gave, before the score existed*
([`../../cold-start-a0/THEORIZE_LOG.md:512-514`](../../cold-start-a0/THEORIZE_LOG.md)).
Coverage and agreement are both 233 and that is not a coincidence: the three
uncovered pairs are exactly the three the manual gets wrong
([`../../papers/phase1-workshop/figures/data/fig2_coverage_accuracy.json`](../phase1-workshop/figures/data/fig2_coverage_accuracy.json),
key `derivations.A0.covered_equals_agreed`).

## 3 · Why no probe could save it

Constraint 7 requires a probe. A0 emitted **zero executable probes**, and the
reason is structural rather than incidental:

> The one thing that could have exposed it — a probe — could not be run, and the
> reason is structural rather than incidental: the Button's latch is
> **irreversible**, so once the trajectory presses it from the left the other
> three approaches are permanently unobservable. A0's own design made the
> decisive experiment impossible.
> — [`../../cold-start-a0/A0_REPORT.md:64-69`](../../cold-start-a0/A0_REPORT.md)

The probe log is more specific still. `probe_frontier` was asked to separate the
push rule's three-member guard frontier — `free(strip(D))` / `clear(strip(D))` /
`tcolor(D)==0` — and answered that **no experiment in this world can**, because
`clear` differs from `free` only off-grid and the border is solid wall, and
`tcolor(D)==0` *is* `free` for a 1×1 mover
([`../../cold-start-a0/THEORIZE_LOG.md:130-143`](../../cold-start-a0/THEORIZE_LOG.md),
[`:336-339`](../../cold-start-a0/THEORIZE_LOG.md)). Three names, one predicate.

So A0's ambiguities came in exactly two flavours, and neither is probeable:
**extensionally identical predicates**, and **a question gated behind an
irreversible latch**. The probe designed for the latter is trivial and
impossible: *drive the Cart to (2,2) and push DOWN into an unpressed Button. In
this world the Button is already pressed by then*
([`../../cold-start-a0/THEORIZE_LOG.md:241-245`](../../cold-start-a0/THEORIZE_LOG.md)).

## 4 · The design change

A0′ changes one thing about the world: the latch becomes a **toggle**. Everything
else — the 9×9 grid, the push mechanics, the portal, the Door in the divider — is
the same shape, and the explorer is made *worse*, truncated at 40 % of the
exhaustive walk ([`../../cold-start-a0/prime/A0P_REPORT.md:17-19`](../../cold-start-a0/prime/A0P_REPORT.md)).

The mechanism census from the truncated trace shows what that buys. Witnessed:
`step` 82, `blocked_by_wall` 18, `teleport` 2, and **`toggle_on` and `toggle_off`
once each in all four directions**. Never witnessed: `step` 79,
`blocked_by_wall` 35, `blocked_by_crate` 6, `blocked_by_closed_door` 1
([`../../cold-start-a0/prime/artifacts/prime_report.json`](../../cold-start-a0/prime/artifacts/prime_report.json),
key `trace.a0p-base`; 111 frames, 110 transitions, 57 reachable states,
`coverage "107/228"`).

The adjudication that was impossible in A0 is now arithmetic:

> Each clause has coverage 1/1 — but there are **sixteen of them and every
> direction-by-polarity combination has its own witness**. A0's `press_left` had
> one witness and *no* way to get a second, so `THEORIZE_LOG` R-05 there had to
> reject the direction generalisation and knowingly ship a hole. Here the
> generalisation is not an analogy, it is enumerated evidence, and it goes in.
> — [`../../cold-start-a0/prime/THEORIZE_LOG.md:73-76`](../../cold-start-a0/prime/THEORIZE_LOG.md)

Constraint 5 did not change. The evidence did.

## 5 · The 13 probes — before and after

| | A0 | A0′ |
|---|---|---|
| probe rows emitted by `probe_frontier` | **9** | **27** |
| of which `tier: executable` | **0** | **13** |
| of which `tier: hypothetical` | 2 | 9 |
| untyped rows | 7 | 5 |

Counted from
[`../../cold-start-a0/artifacts/engines_report.json`](../../cold-start-a0/artifacts/engines_report.json)
and [`../../cold-start-a0/prime/artifacts/engines_report.json`](../../cold-start-a0/prime/artifacts/engines_report.json),
key `probes`; the 13 and the 27 agree with `engines.executable_probes` and
`engines.total_probes` in
[`../../cold-start-a0/prime/artifacts/prime_report.json`](../../cold-start-a0/prime/artifacts/prime_report.json).

The 13 executable designs, with the split each one buys:

| rule | action | at t | coverage | bits | hypotheses |
|---|---|---|---|---|---|
| `obj0_recolor7_LEFT` | RIGHT | 85 | 1/1 | 1.000 | 2 |
| `obj1_appear_LEFT` | RIGHT | 85 | 1/1 | 1.000 | 2 |
| `obj2_jump_DOWN` | RIGHT | 11 | 2/2 | 1.000 | 4 |
| `obj0_recolor7_RIGHT` | RIGHT | 38 | 1/1 | 0.918 | 18 |
| `obj1_appear_RIGHT` | RIGHT | 38 | 1/1 | 0.918 | 18 |
| `obj0_recolor7_UP` | UP | 39 | 1/1 | 0.863 | 21 |
| `obj0_recolor8_UP` | UP | 12 | 1/1 | 0.863 | 21 |
| `obj1_appear_UP` | UP | 39 | 1/1 | 0.863 | 21 |
| `obj1_vanish_UP` | UP | 12 | 1/1 | 0.863 | 21 |
| `obj0_still_UP` | UP | 12 | 17/17 | 0.811 | 4 |
| `obj1_still_UP` | UP | 12 | 17/17 | 0.811 | 4 |
| `obj2_step_UP` | UP | 12 | 17/17 | 0.811 | 4 |
| `obj2_still_UP` | UP | 12 | 2/2 | 0.811 | 4 |

Note what the table is made of: **every executable design targets the toggle, the
portal, or a rule adjacent to them.** The seven that were untyped in A0 and the
two hypothetical ones are the same push-frontier questions that were
extensionally undecidable there, and they remain undecidable here. Reversibility
did not make A0's unanswerable questions answerable; it made the *toggle's*
questions answerable, and the toggle was the one that mattered.

**One number does not reconcile, and it is reported rather than rounded off.**
[`../../cold-start-a0/prime/A0P_REPORT.md:51`](../../cold-start-a0/prime/A0P_REPORT.md)
states the comparison as *"13 executable of 27 designed (A0: **0** of 22)"*. The
27 is exactly A0′'s probe-row count. The **22 is not reproducible**: A0's base
run emits 9 probe rows (17 across both its manuals, counting
`engines_report_no_button.json`'s 8), and the frontier members across those 9
rows sum to 29. The existing gloss in
[`../../papers/phase1-workshop/figures/data/fig2_coverage_accuracy.json`](../phase1-workshop/figures/data/fig2_coverage_accuracy.json)
(`derivations.A0.executable_probes`) proposes that the prose figure counts
frontier members rather than probe rows — that explanation does not hold either,
since the frontier-member count is 29. The load-bearing half of the comparison,
**0 executable versus 13**, is verifiable from the artefacts and is what this
case study rests on. The 22 should be corrected upstream or dropped.

## 6 · The headline, and the second finding nobody asked for

| | A0 | A0′ |
|---|---|---|
| mechanism | Button, **latch** — pressable once | Switch, **toggle** — re-witnessable |
| explorer | exhaustive | **truncated at 40 %** |
| state-action coverage | 233/236 = **99 %** | 107/228 = **47 %** |
| full-history replay | green | green |
| **accuracy vs ground truth** | 233/236 = **98.73 %** | **228/228 = 100 %** |
| executable probes emitted | **0** | **13** |
| rules left untested by the trace | 1 (unprobeable) | **0** |

— [`../../cold-start-a0/prime/A0P_REPORT.md:17-23`](../../cold-start-a0/prime/A0P_REPORT.md);
A0′'s side raw in `run_a` of
[`../../cold-start-a0/prime/artifacts/prime_report.json`](../../cold-start-a0/prime/artifacts/prime_report.json)
(`score_vs_truth: accuracy 1.0, agree 228, pairs 228`; `revisions: 0`;
`coverage_probes.rules 21, untested_rules []`).

The toggle also broke the segmenter, which A0 had no way to discover. `mdl_segmenter`
matches frame *t* against *t+1* only, so an object that vanishes and returns is a
fresh track every time — and A0′'s Door closes and reopens. The raw segmentation
came back with **five Doors**, seven tracks for a three-object world; *five Doors
is not a theory — no rule can be stated about an object whose identity resets on
every use*. The repair is Theoria §1.8's own template-matching operator, priced
rather than asserted: merge same-template, disjoint-lifetime tracks, **7 → 3**,
saving **48 bits** (script 1971 → 1923)
([`../../cold-start-a0/prime/THEORIZE_LOG.md:24-34`](../../cold-start-a0/prime/THEORIZE_LOG.md);
[`../../cold-start-a0/prime/artifacts/prime_report.json`](../../cold-start-a0/prime/artifacts/prime_report.json),
key `engines.reidentification`).

## 7 · Run B — the controlled test that A0 could not run

A0's report named the untested bet: *"When the theory is wrong, does the loop
repair it?"* ([`../../cold-start-a0/A0_REPORT.md:169-175`](../../cold-start-a0/A0_REPORT.md)).
A0′ answers it as a **controlled experiment**, labelled as such in the seeded
manual's own header. One clause is added to Run A's manual:

```
rule push_onto_crate [ev: none cov: 0/0]
  when act=push(Cart, right) and colored(rightof(Cart), 4) then moved(Cart, right)
```

It is false, and it is chosen to be invisible to replay: the trajectory never
once pushes into the Crate, so the rule never fires in the whole 110-transition
history ([`../../cold-start-a0/prime/A0P_REPORT.md:88-99`](../../cold-start-a0/prime/A0P_REPORT.md)).

| layer | verdict |
|---|---|
| full-history replay | **GREEN** — 111 frames, 8991 pixels, 0 anomalies. Blind, exactly as predicted. |
| Lean transcription | **CAUGHT IT.** `ArenaEscape: step sends the mover to (2,4), which the board does not list as arena (from (2,3) on right)` |
| coverage probe | **CAUGHT IT.** navigate 3 steps to (2,3), predict Cart→(2,4), execute, observe Cart stays → **refuted** |
| repair | delete the clause; **1 revision**; accuracy **0.9912 → 1.0000** |

— [`../../cold-start-a0/prime/A0P_REPORT.md:104-108`](../../cold-start-a0/prime/A0P_REPORT.md);
raw in `run_b` of [`../../cold-start-a0/prime/artifacts/prime_report.json`](../../cold-start-a0/prime/artifacts/prime_report.json)
(`score_vs_truth_before: accuracy 0.991228, agree 226, disagree 2`;
`score_vs_truth_after: accuracy 1.0`; `revisions: 1`;
`coverage_probes.probes_run: 1, refuted: ["push_onto_crate"]`).

The two catches are different in kind and the report keeps them apart: the
coverage probe is the **empirical** one and is the mechanism Theoria specifies
under constraint 7; the Lean form caught it as an **internal inconsistency**,
before the world was consulted, and *was not designed for — it fell out of
transcribing the state space*
([`../../cold-start-a0/prime/A0P_REPORT.md:110-122`](../../cold-start-a0/prime/A0P_REPORT.md)).

## 8 · The design rule that goes into the framework

> **Recommendation, stronger than A0_REPORT §7.2 stated it:** when designing a
> self-built world — or choosing which ARC levels to develop on — *reversibility
> of the mechanisms matters more than the breadth of the trajectory*. An
> irreversible mechanism caps what any amount of exploration can establish.
> — [`../../cold-start-a0/prime/A0P_REPORT.md:36-39`](../../cold-start-a0/prime/A0P_REPORT.md)

A2 independently met the mirror image of the same constraint: its Portal is
one-way, so *every left-room probe had to run before P-01. An irreversible world
constrains experiment* order*, not only experiment design*
([`../../cold-start-a2/THEORIZE_LOG.md:193-196`](../../cold-start-a2/THEORIZE_LOG.md)).
Two worlds, two ways for irreversibility to bite.

## 9 · What this case study does not show

* **The objection that bites is analytic, not statistical.** A0′'s toggle was
  designed so that every direction-by-polarity case would have a witness, so the
  adjudication rule mechanically admits what it mechanically rejected in A0.
  *This demonstrates the mechanism; it does not test it.*
  ([`../../papers/phase1-workshop/figures/data/fig2_coverage_accuracy.json`](../phase1-workshop/figures/data/fig2_coverage_accuracy.json),
  key `caveat`.) A0′ was built by the same instance that wrote A0's report and
  its recommendation. That is n=1 per arm on two self-built worlds.
* **The seeded error was of a convenient kind.** It escaped the arena, which is
  what let the Lean form catch it for free. *A right-looking-but-wrong clause on
  a tested firing state is not covered by either mechanism, and that gap is
  real* ([`../../cold-start-a0/prime/A0P_REPORT.md:150-155`](../../cold-start-a0/prime/A0P_REPORT.md)).
* **No multi-round repair.** Run A 0 revisions, Run B 1, and the repair was a
  deletion. The 修订抖动 row of the failure taxonomy is still empty
  ([`../../cold-start-a0/prime/A0P_REPORT.md:141`](../../cold-start-a0/prime/A0P_REPORT.md),
  [`:146-149`](../../cold-start-a0/prime/A0P_REPORT.md)).
* **A0′'s goal was supplied, not induced.** The truncated trace never wins, so
  `goal Cart.pos = (2,7)` was taken from the problem statement and recorded as
  such ([`../../cold-start-a0/prime/THEORIZE_LOG.md:115-123`](../../cold-start-a0/prime/THEORIZE_LOG.md)).
* **Scale is untested.** 57 reachable states, 36 arena cells
  ([`../../cold-start-a0/prime/A0P_REPORT.md:158-159`](../../cold-start-a0/prime/A0P_REPORT.md)).

---

*Previous:* [`01-birth-of-a-concept.md`](01-birth-of-a-concept.md) ·
*Next:* [`03-a-theorem-true-and-false.md`](03-a-theorem-true-and-false.md).
Chart data: [`data/cs02-reversibility.json`](data/cs02-reversibility.json).
