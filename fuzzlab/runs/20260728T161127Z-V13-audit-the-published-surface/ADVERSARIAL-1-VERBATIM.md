# ADVERSARIAL REVIEW — V-13 (`agent/v13-audit-the-published-surface`) — verbatim

**Provenance of this file.** The reviewer was spawned by the V-13 implementer
and was given a **read-only** worktree, so it could not write its own report; it
returned the text and said archiving was the coordinator's to do. The text was
delivered to the coordinator (RES-3) rather than to the implementer, and **the
implementer never received it** — it declined, correctly, to file a paraphrase
under the review's name, and `ADVERSARIAL-1.md` in this directory is therefore a
*disposition record* written by the implementer, not the review. This file is
the review itself, verbatim, archived by RES-3.

One consequence is recorded here rather than smoothed over: some figures the
coordinator relayed to the implementer (27 fallbacks of 200) **did not
reproduce** against the implementer's later tree (15 of 500), because the relay
predated an operator fix. The implementer re-measured rather than adopting the
relayed number. Numbers below are the reviewer's, against the tree it saw.

**Attribution boundary, in the reviewer's own words.** Everything the
implementer fixed afterwards — the new mutants `pf-zero-cost-value-is-zero` and
`cm-lift-admits-a-wrong-direction`, the committed 4455-world sweep, the uniform
465/500 coverage — was *"reported to me, not verified by me. I have not re-run
anything since my review and those results should not be attributed to this
report."* Read this file as the state of the tree **before** the fixes, not as
sign-off on them.

---

Reviewer: adversarial pass, read-only on `.worktrees/v13-audit-the-published-surface/`.
No network, no `.env`, no writes to the worktree; all scratch work in the session
scratchpad.

**Scope note on a moving target.** The worktree changed under me during the
review (`fuzzlab/props/cegis_miner.py` mtime 00:36 — the `UNRESOLVED` sentinel
appeared; `fuzzlab/MUTATION.md` 00:38; `partials/` regenerated 00:38). **Every
measurement below was re-run against the current tree**, including `_mover_track`
and `UNRESOLVED`. My independent `python -m fuzzlab.mutation --engine cegis_miner
--worlds 40` matches the regenerated partials exactly (`cm-drop-frontier-guard`
33/7, `cm-shrink-lifted-support` 32/8, `cm-flip-effect-delta` 34/6,
`cm-freeze-lifted-direction` 32/8), so nothing here predates either change. Line
numbers may drift; load-bearing code is quoted.

---

## 1. VERDICT on (a): does the effect oracle use the machinery of the engine it judges?

**No for the oracle. Partly for the property — and it is defensible — but two of
the safeguards around it are provably vacuous, and one docstring describing the
oracle's inputs is false.**

### 1.1 The oracle is clean, and I could not break it

`fuzzlab/oracles/motion.py` imports `typing` and nothing else. Measured by
module-graph diff on a fresh interpreter:

```
engines.* imported by oracles.motion: []
new modules: ['fuzzlab', 'fuzzlab.oracles', 'fuzzlab.oracles.motion', 'typing']
```

Note this is only true because the module deliberately omits the `from fuzzlab
import rig` bootstrap that every `props/*.py` carries — as its docstring says,
"an import of `engines.*` here would fail rather than quietly work." That is a
real structural guarantee, not a comment.

Traced every input the oracle reads:

- `world.frames` ← `gridworld.Rules.render(anchor)` per anchor
  (`worlds/gridworld.py:196-203`). Pure generator; no engine.
- `world.action_list` ← `GridWorld.action_list` (`worlds/gridworld.py:227-229`),
  built from `rng.choice(DIRECTIONS)` in `generate()`. No engine.
- `world.spec_json()` ← `GridSpec.json()` (`worlds/gridworld.py:113-126`), a
  dataclass dump.
- `DELTA` in `props/cegis_miner.py:80` is imported from
  `fuzzlab.worlds.gridworld`, **not** `engines.cegis_miner.miner`. Both define
  the same four pairs; the property uses the world's copy. Correct.

Independent end-to-end confirmation: I ran `motion.motions()` against
`gridworld.Rules.step` over 200 worlds — **4455 transitions, 0 disagreements, 0
unreadable**.

### 1.2 The strongest counter-argument I found, and why it does not land

`_mined_subject` reads `transitions[0].state.shape` and `t.state.anchor`. Those
are `mdl_segmenter` output, arriving through
`cegis_miner.transitions_from_segmentation` — i.e. `engines.*` data inside the
invariant's decision path.

**Against the author:** the invariant `effects_agree_with_the_evidence` will not
fire unless this engine-derived data clears a gate, so engine output
participates in whether a violation can be reported at all.

**For the author:** (i) the engine under judgement is `cegis_miner`;
`mdl_segmenter` is a different engine and this is not the miner grading itself.
(ii) `State.anchor` is the miner's *input* — the same input its guards are
evaluated against — so consulting it settles *which object the rule set is
about*, not *what happened to that object*. (iii) The effect comparison itself
is 100% pixels: `truth = motion.motions(world)` and nothing else.

**Decision: legitimate.** The house rule governs the source of the *truth*, and
the truth here never touches `engines.*`. The identity question is a scoping
question, and scoping the subject from the engine's own input is the weakest
possible use of it.

### 1.3 But `_mined_subject` is dead code on the path it was written for

`_mover_track` accepts a track only if:

```python
if tuple(track.shape) != shape: continue
if len(track.anchors) < len(anchors): continue
if all(track.anchors[t] is not None
       and tuple(track.anchors[t]) == tuple(anchors[t])
       for t in range(len(anchors))):
    return track
```

`_mined_subject` then re-checks `tuple(transitions[0].state.shape) != shape` and

```python
off = [t.index for t in transitions
       if t.index >= len(anchors) or tuple(anchors[t.index]) != tuple(t.state.anchor)]
```

These are **the same two comparisons over a subset of the same index range**
(`t.index` ranges over `0 … len(action_list)-1`, and `len(anchors) ==
len(action_list)+1`). So whenever `_mover_track` returns a track, `off` is empty
and the shape check passes — `_mined_subject` provably cannot fire. Measured
over the campaign seed's first 60 gridworlds:

```
_mined_subject says 'not the mover': 6
...of those, _mover_track had returned a track: 0
worlds where _mover_track redirected off tracks[0]: 15
```

It survives only as a guard on the `_mover_track → None` fallback. That is fine
as engineering. The docstring does not say so, and reads as though the check is
the live defence it was in the pre-`_mover_track` tree.

### 1.4 `_mover_track` — does it feed the engine an input a real caller would not?

Measured over 200 worlds (first successful segmentation operator per world):

```
mover IS tracks[0]              118
mover is tracks[1..6] REDIRECTED 49    (25% of the 195 minable)
fallback to tracks[0]            27    (pixels fix the mover, but no track matches)
unminable                         5
```

Who picks the track in real callers (`grep -rn transitions_from_segmentation`
across the repo including `a0-spike/` and `cold-start-a0/`):

| caller | track |
|---|---|
| `engine-rig/engines/cegis_miner/README.md:106` (the documented API example) | **default `tracks[0]`** |
| `engine-rig/tools/run_all.py:88` | **default `tracks[0]`** |
| `engine-rig/tests/test_cegis_miner.py:20`, `test_probe_frontier.py:156` | default (one-object fixtures) |
| `theoria-arm/world/adapt.py:195` | explicit, loops `for track in seg.tracks` |
| `cold-start-a0/pipeline/multi_miner` (per `artifacts/candidates.jsonl`) | explicit per track, and adds its own `"track": "obj0"` payload field |
| `a0-spike/` | does not call it (imports `synthesize`/`enumerate_frontier` only) |

**Verdict: `_mover_track` does not mask a defect in `mine()`.** `mine()` is
track-agnostic — it consumes a transition list. Feeding it the mover's
transitions is a strictly *harder* input than a rock's: a rock yields one
`blocked_<D>` rule per action, all `effect: none`, guards trivially exclusive
and trivially complete; the mover yields varied effects and makes
`clear(strip(D))` load-bearing. BUGS.md § S2's control reproduces: **unminable
unchanged 3 → 3** over 60 worlds, so no worlds were quietly routed around.

**What it does mask is the `track = track or seg.tracks[0]` default itself**
(`engines/cegis_miner/__init__.py:36`) — the exact line the engine's own README
example exercises. On 25% of worlds fuzzlab no longer makes the documented call.
That is a deliberate change of subject and should be recorded in BUGS.md as an
un-audited surface, not left implicit.

### 1.5 `_claimed_delta`'s `?dir` resolution is the engine's semantics, with one caveat

`miner.py:219-224` `_normalise` admits a member only if `(rule.effect.dy,
rule.effect.dx) == DELTA.get(rule.action)`, and `miner.py:249-263` `lift()`
emits `Effect(type="move", direction=DIR_VAR)`. So "`?dir` resolves to the delta
of the witness's action" is the engine's own admission predicate, not the
author's invention. **The docstring's claim on this point is correct.**

Caveat worth recording: the engine ties `?dir` to the *member rule's* `action`;
`_claimed_delta` resolves it against `world.action_list[index]`. Those agree
only when `rules_fire_on_the_action_they_name` holds — a mild dependency between
two invariants presented as independent. It bites nothing today: ground-rule
claims are read straight off `dy/dx` and ignore `action`, and measured
`unexpected_kills` is `[]` for `cm-relabel-rule-action`.

---

## 2. VERDICT on (b): per-mutant — informative / tautological / mis-claimed / never-ran

All figures from my own `--worlds 40` run against the current tree. **None of
the seven is "counted-but-never-run"**: all report `determined: true` with
`worlds_evaluated > 0`. **None is mis-claimed**: I verified every `claim` string
against the cited engine source line by line. **None produced an unexpected
kill** — `unexpected_kills` is `[]` for all 14 cegis mutants, which is the
evidence that the new invariants are independent of the four old ones rather
than one check written twice.

| mutant | eval / inert | result | verdict |
|---|---|---|---|
| `cm-flip-effect-delta` | 34 / 6 | killed 34/34, first world 1 | **Informative.** Selector `_first_move_rule` is structural (`effect.type == "move" and (dy, dx) != (0, 0)`); it never calls `oracles/motion.py` and never asks whether the write would trip anything. Negating a non-zero delta is false by arithmetic, independent of the oracle. Claim verified: `miner.py:330-335` copies `dy/dx` off `members[0].effect`; `Effect.as_json` (`miner.py:56-67`) publishes them; `cold-start-a0/prime/probe_runner.py:72` is exactly `effect = rule_payload["effect"]`. Sample kill: *"rule push_DOWN claims the mover moves by [-1, 0] on transition 0 (action 'DOWN'), but the frames show a displacement of [1, 0]"*. |
| `cm-effect-none-becomes-move` | 37 / 3 | killed 32/37, first world 1 | **Informative.** Selector structural (first rule with `effect.type == "none"` and `action in DELTA`). Claim verified: `__init__.py:46-47` emits `Effect(type="none")` iff `not events`; `miner.py:208-209` `structural_name` returns `blocked_%s` on that basis. The 5 non-kills are not misses — I instrumented per-world outcomes and they are `skip: mined_track_is_not_the_mover`, i.e. worlds the invariant declined to judge. The accounting works. |
| `cm-drift-effect-destination` | 17 / 23 | killed 17/17, first world 1 | **Informative.** Selector structural (first rule with `effect.to is not None`). Confirmed the kill fires on the destination branch and not the delta branch — `dy/dx` are left alone, and the finding reads *"rule push_RIGHT claims the mover lands at [4, 1] on transition 10, but the frames put it at [3, 1]"* with `data` keys `['actual_to','claimed','claimed_to','rule','transition']`. Claim verified against `miner.py:329-335`. |
| `cm-drop-effect-destination` | 17 / 23 | **SURVIVED — pre-registered** | **Informative negative control, and it holds.** 17 silent passes; no other invariant in the module reads `effect.to`. Identical selector to `cm-drift-effect-destination`, so the pair is properly matched and the difference between them isolates exactly the asymmetry claimed. This is the single strongest artefact in V-13: a measured gap instead of a sentence asserting the gap is small. |
| `cm-freeze-lifted-direction` | 32 / 8 | killed 32/32, first world 1 | **Not a V-10 tautology — but a closed loop of a different kind. See §2.1.** |
| `cm-relabel-rule-action` | 39 / 1 | killed 39/39, first world 1 | **Informative but shallow.** Selector structural (first ground rule with `action in DELTA` and non-empty support). Claim verified: `miner.py:310-312` groups on `(transition.action, transition.effect.key())` and `miner.py:326` sets `action = members[0].action`, so homogeneity is true by construction of those two lines. The invariant it kills can therefore only catch a defect in that grouping plus the verbatim `action = actions[t]` copy at `__init__.py:40-67`. A real check on published surface, but a one-line one. |
| `pf-scale-reported-costs` | 40 / 0 | killed by `costs_are_the_world's` | **Informative.** Order-preservation verified analytically, not empirically: `ProbeValue.value` is `entropy / cost` (`frontier.py:43-44`), so scaling every cost by 2 halves every value; the sort key `(-value, -entropy, cost, str(action))` (`frontier.py:118`) is monotone in both the `-value` and the `cost` tie-break components. So `ranking_is_sound` cannot catch it **on any world**, and the kill is the cost comparison and nothing else — which is exactly what the mutant was built to demonstrate. Claim `_COST_CLAIM` (`mutants/probe_frontier.py:379-385`) checks out against `frontier.py:115` `cost=costs.get(action, 1.0)`. *Quibble:* registered `kind=INCONSISTENT`, but after mutation `value` is perfectly consistent with the lying `cost` — the defect is `UNSOUND` (the engine asserts a cost that is not the caller's). Same mis-kind on `pf-flatten-reported-costs`. |

### 2.1 `cm-freeze-lifted-direction`: the branch that catches it is unreachable from the engine

This is my sharpest finding on (b). The mutant pins `effect.direction` to a
concrete compass name. `_claimed_delta` catches it on exactly one branch:

```python
direction = getattr(effect, "direction", None)
if direction is not None:
    if direction in DELTA:
        return DELTA[direction]           # <-- the only thing that kills this mutant
    resolved = DELTA.get(action)          # the variable, resolved per witness
    return UNRESOLVED if resolved is None else resolved
return (int(effect.dy), int(effect.dx))
```

Two measurements:

**(1) The engine cannot produce a concrete `direction`.** `grep -rn "direction="
engine-rig/engines/cegis_miner/` returns exactly one producer — `miner.py:253`,
`Effect(type="move", direction=DIR_VAR)`. Census over **357 published rules
across 57 worlds** (`result.all_rules`, first 60 gridworlds):

```
effect.direction values seen: {None: 302, '?dir': 55}
rules with effect.to set: 46
```

Nothing else, ever. `Effect.direction` is `None` on every ground rule and
`"?dir"` on every lifted one.

**(2) The branch is 100% load-bearing.** I re-executed `props/cegis_miner.py` in
place with those two lines deleted, against the current file (`UNRESOLVED`
present), and re-ran the mutant:

```
WITH `if direction in DELTA` BRANCH REMOVED:
cm-freeze-lifted-direction  eval=32  killed=0
```

From 32/32 to 0/32.

So: the mutant writes a value outside the engine's output space, and the
invariant contains a two-line interpreter whose only reachable caller is that
mutant. This is **not** the V-10 flaw — the selector (`len(set(concrete)) < 2:
continue`) reads `world.action_list`, never the oracle, and functions as a
non-triviality guard rather than as the invariant's own predicate. But the kill
certifies a hand-written reading of a hypothetical field; it says nothing about
the engine's real `?dir` semantics.

**The claim actually worth testing** — "a lifted rule's `?dir` means `DELTA[the
witness's action]`" — *is* exercised on every clean world by the `return
resolved` path, which returns no violation. But **no mutant makes that path
false.** Ones that would: corrupt `lift()` to collapse members whose `(dy, dx)
!= DELTA[action]` (violating `_normalise`'s own admission rule at
`miner.py:221`), or graft a foreign-direction transition into a lifted rule's
`support`. Recommend adding one.

Consequently the line in MUTATION.md — *"`cm-freeze-lifted-direction` is the one
that closes V-10's largest single hole"* — is the claim I would strike. What
closes the `all_rules` hole is the **scope change** (`applicable_equals_support`
and both new invariants iterating `result.all_rules`), evidenced by
`cm-shrink-lifted-support` going from a V-10 survivor to 32/32 dead. That result
stands on its own and does not need this mutant.

---

## 3. Refuted outright

### R1 — `costs_are_the_world's` does not check the zero-cost convention, and both docstrings say it does

`props/probe_frontier.py:52` (module docstring):
> "`ProbeValue.value` is a *property* (`entropy / cost`) and therefore
> unfalsifiable by construction, so it is checked only for **the divide-by-zero
> convention the engine documents**."

`props/probe_frontier.py:214` (function docstring):
> "the only part of it worth asserting is **the zero-cost convention the engine
> documents, which is checked below**."

`props/probe_frontier.py:228` is:

```python
if expected > 0 and abs(value.value - value.entropy / expected) > EPS:
```

The guard **excludes exactly the zero-cost case**. The engine's convention is
`frontier.py:43-44`:

```python
"""Bits per unit of path cost -- reaching a state is itself a plan."""
return self.entropy / self.cost if self.cost else float("inf")
```

And this is not hypothetical. `worlds/hypset.py:21` says the generator draws
"fractional costs, large costs, and **zero**. Zero is not a hypothetical" —
`hypset.py:185` appends `0.0`. Measured over the standing 500-world corpus:

```
hypset worlds (of 500) with >=1 zero-cost action: 138   (27.6%)   total zero-cost actions: 166
zero-cost action 'DOWN': engine value=inf (convention: inf), entropy=1.5
findings when `value` is falsified to 0.0 at zero cost: []
```

I falsified `value` to `0.0` on the zero-cost action of a real hypset world and
`costs_are_the_world_s` returned an empty list. An engine that returned `0.0` or
`NaN` instead of `inf` at zero cost passes silently on 27.6% of the corpus,
while the prose claims that is the one thing being checked. Either drop the
`expected > 0` guard and assert `value == inf` when `expected == 0`, or fix both
docstrings.

### R2 — `_mined_subject`'s docstring describes code that no longer exists, and it leaks into a user-visible message

The docstring, present tense, in the current file:

> "`transitions_from_segmentation` **is called** with `track=None`, so it mines
> `seg.tracks[0]` — whichever track the segmenter happened to list first.
> Measured on the campaign seed's first 60 gridworlds: of the 57 that mine at
> all, **21 mine a static obstacle** rather than the mover."

False of the code it documents. `_mine` now calls
`engine.transitions_from_segmentation(..., track=_mover_track(world, seg))`.
Measured on the same 60 worlds under the shipped code: **57 minable (matches),
but 6 mine a non-mover, not 21.**

Worse, the same stale claim is in the `skipped` detail string that a triager
reads:

> "the mined track has bounding box %s and the world's mover is %s, so this rule
> set describes some other object; **transitions_from_segmentation mines
> seg.tracks[0] and the segmenter did not list the mover first**"

That will send whoever reads the finding to the wrong cause. The real cause,
which I traced on three instances, is that the segmenter **fragments the mover's
track across frames**:

```
world 12  mover shape=(1,3) colour=8, moved 19 times
  pixel anchors[:8]: [(3,3),(3,3),(2,3),(1,3),(1,4),(1,3),(0,3),(1,3)]  len 23
  track anchors[:8]: [None, None,(2,3),(1,3),(1,4),(1,3),(0,3),(1,3)]  len 23
world 19  mover shape=(3,1) colour=4, moved 12 times
  track anchors[:8]: [None,None,(1,1),None,None,None,None,None]
```

`_mover_track` requires every anchor in range to be non-`None`, so it declines
and falls back. Of the 27 fallback worlds in a 200-world sweep, **25 are "shape
matches but anchors differ"** — i.e. the mover's track exists with the right
bounding box and is riddled with `None`s. That is a candidate `mdl_segmenter`
track-continuity finding in its own right, and the current message hides it.
(`_mover_track`'s own docstring is correctly past-tense — "`_mine` used to take
that fallback". Only `_mined_subject` was left behind.)

### R3 — MUTATION.md cites a measurement its cited test does not contain

`fuzzlab/MUTATION.md:502`:
> "The oracle is checked against `gridworld.Rules.step` end to end in
> `tests/test_oracles.py` — **4455 transitions over 200 worlds**, zero
> disagreement, zero unreadable — which is a check the campaign itself cannot
> perform."

The test is `test_motion_agrees_with_the_generator_on_whole_gridworlds`,
decorated `@pytest.mark.parametrize("index", [0, 3, 11, 29, 57])`. I ran both
sweeps:

```
the test as written (5 parametrised indices): worlds=5   transitions=93    disagreements=0  unreadable=0
MUTATION.md's cited sweep (200 worlds):        worlds=200 transitions=4455  disagreements=0  unreadable=0
```

**In fairness: the number is true and I reproduce it exactly.** But it lives
nowhere in the repo, and the regression that actually ships locks in **93**
transitions, not 4455. Either widen the `parametrize` (it costs ~a second) or
cite the sweep as an ad-hoc measurement rather than as the test.

### R4 — the archived mutation partials were stale when I started (since self-corrected, recorded for provenance)

At 00:21 `partials/cegis-mutation-summary.txt` read `cm-flip-effect-delta
eval=25 inert=15`, `cm-freeze-lifted-direction eval=23 inert=17`,
`cm-drop-frontier-guard eval=24 inert=16`, `cm-shrink-lifted-support eval=23
inert=17`. The current tree gives 34/6, 32/8, 33/7, 32/8. I identified the cause
decisively by re-implementing the pre-V-13 `_mine` (`track=None`, i.e.
`seg.tracks[0]`) and re-running the real driver over the same worlds:

```
CURRENT _mine          cm-drop-frontier-guard eval=33 inert=7   cm-flip-effect-delta eval=34 inert=6
                       cm-shrink-lifted-support eval=32 inert=8 cm-freeze-lifted-direction eval=32 inert=8
OLD _mine (tracks[0])  cm-drop-frontier-guard eval=24 inert=16  cm-flip-effect-delta eval=25 inert=15
                       cm-shrink-lifted-support eval=23 inert=17 cm-freeze-lifted-direction eval=23 inert=17
```

Exact match to the archive on all four. So the archived JSON was the
pre-`_mover_track` run, while `MUTATION.md`'s later prose already carried
post-repair numbers — the two disagreed inside one deliverable, and
`MUTATION.md:484` pointed at the JSON as the raw evidence. The author
regenerated the partials at 00:38 while I was working and they now agree with my
independent run; no action needed. Two residuals: `RUN_STATE.md` and
`MANIFEST.json` both reference an `ADVERSARIAL-1.md` that did not exist on disk,
and the 500-world campaign partial (`campaign.500w.json`, 00:42) is a
*different* vintage from the mutation partials (00:38) — worth a line in the
manifest saying which tree each was taken against.

---

## 4. The two side questions

### 4.1 E-11 vs the author on "1209 false published rows": the author is right, and for a stronger reason than the one given

Verified against source:

- `miner.py:104-119` `Rule.as_json()` emits `name / action / guard /
  guard_cost_bits / effect / frontier / frontier_size / frontier_max_size /
  frontier_truncated / cegis_guard / cegis_iterations / cegis_trace /
  lifted_from`. **No object identifier.**
- `__init__.py:71-87` `to_payload` is `rule.as_json()` verbatim; `candidates()`
  wraps it with `transitions` and `coverage` and adds nothing.
- `CONTRACTS/candidates_schema.md` has no subject/track field (only `kind`).
- `engine-rig/engines/cegis_miner/README.md:73-99` publishes the payload shape —
  no subject.
- The two drivers that publish per-track had to **add the field themselves**:
  `cold-start-a0/artifacts/candidates.jsonl` rows carry `"track":"obj0"` and
  names like `obj0_still_DOWN`, injected by `cold-start-a0/pipeline/multi_miner`,
  not by the engine.

Three points E-11's count cannot survive:

1. **fuzzlab publishes nothing.** `props/cegis_miner.py:_mine` calls
   `engine.mine(transitions)` — never `engine.run(..., out_path=)`. No
   `candidates.jsonl` row was ever emitted from the worlds E-11 counted. "1209
   published rows" has no referent. (Cross-check: `theoria-arm` run artifacts
   contain **0** `cegis_miner` rows, consistent with
   `theoria-arm/THEORIZE_LOG.md:185` "Zero `rule_hypothesis` rows".)
2. **Falsity requires a subject.** `{"name":"blocked_UP","action":"UP","guard":
   ["act==UP"],"effect":{"type":"none"}}` with no subject is not truth-apt. It
   is true of a rock and false of the mover, and the payload does not say which.
   E-11 supplies the mover as subject and then calls the result false — that is
   the reviewer's premise, not the engine's claim. The author's "true statement
   with an unnamed subject" is also slightly too generous; the precise reading is
   *not truth-apt as published*. Both land on the same disposition.
3. **`structural_name` never overclaims.** `miner.py:200-214`: a rock's rules are
   `blocked_*` only; `push_*` requires `step == 1 and (dy,dx) == DELTA[action]`,
   which a static object cannot produce. The one name that implies a mover is
   never generated for one.

**So `skipped` is correct, not `violated`, and the real defect is the contract
one** — a `rule_hypothesis` cannot name its subject — which is where the author
files it. E-11's disposition is wrong; its underlying observation is right and
is worth a CONTRACTS ticket.

### 4.2 One thing the author should have fixed and did not — the same sin, one engine over

On the 54 campaign worlds (6 of 60) where the mined track is still not the
mover, `effects_agree_with_the_evidence` records a `skipped`. But
`frontier_guards_are_consistent`, `frontier_is_complete_to_size`,
`applicable_equals_support` and `guards_partition_the_evidence` all still report
**evaluated — 480/500** on a rule set that says nothing ever happens. Confirmed
against `partials/campaign-500-skip-causes.txt`: those four skip only on
`unminable` (20), never on `mined_track_is_not_the_mover` (54); 500 − 20 = 480,
and 480 − 54 = 426 for the effect invariant.

That is *precisely* the "I could not check this world" ≡ "I checked and found
nothing" conflation V-13 spent an entire section fixing in
`props/lp_potential.py`. `_mover_track`'s own docstring names it — *"in those 21
worlds the four guard invariants are auditing a rule set that says nothing ever
happens"* — and then leaves those four counting the worlds as judged. The remedy
is symmetric: hoist `_mined_subject` into a shared precondition and let all six
invariants skip together, or state in BUGS.md § S3 why 480 is the honest number
for four of them and 426 for the other two.

### 4.3 `test_a_dead_lp_potential_shows_up_as_lost_coverage` is a real negative control, not vacuous

I re-executed a patched copy of `props/lp_potential.py` **in place in memory**
(never touching the worktree): `re.subn(r'return
\[_skip_no_certificate\(world, "[a-z_]+"\)\]', "return []", src)` → **4
substitutions**, then `exec(compile(patched, ...), lp.__dict__)`, verified
`load("lp_potential") is lp`. Ran the test body against both:

```
[NEW code] live={'certificate_implies_unreachable':12,'heuristic_is_admissible':12,
                 'infinite_means_unreachable':12,'three_conditions_hold':12}
[NEW code] dead={... all 0 ...}                       TEST PASSES

[OLD code] live={... all 25 ...}
[OLD code] dead={... all 25 ...}                      TEST FAILS
  FAIL: certificate_implies_unreachable dead=25 != 0   (x4)
  FAIL: every invariant claims all 25 worlds
```

It passes on the new code and fails on the old code for exactly the stated
reason. **Genuine regression, correctly aimed.** Two nits: the docstring says
*"replacing `run` with `return None, None`"* while the test actually patches
`props._solve` — fuzzlab's own seam, which is the right place and consistent
with the mutation harness, but not what the prose says; and
`dead_evaluated[name] == 0` is a strong assertion that will break the day any
invariant in that module gains a certificate-independent check.

---

## 5. Tried to break and could not

- **Oracle independence.** No import path, no transitive path, no data path from
  `engines.*` into a `Motion`. Verified by module-graph inspection on a fresh
  interpreter and by 4455-transition agreement with `gridworld.Rules.step` over
  200 worlds.
- **The `_replay` disambiguation.** I looked for a world where a same-coloured
  obstacle leaves two surviving `(before, after)` pairs and the oracle silently
  picks one. It refuses — `if len(solutions) != 1: raise Unreadable` — and
  `test_motion_is_not_fooled_by_a_same_coloured_neighbour` is a genuine
  adversarial fixture (1×2 mover, same-coloured obstacle placed exactly where
  the wrong reading lands), not a happy path.
- **Teleports.** `read_motion` handles disjoint before/after correctly
  (`test_motion_reads_a_teleport_with_disjoint_before_and_after`), and I found no
  gridworld teleport the oracle mis-read across 4455 transitions.
- **`_mover_track` masking a mining defect.** Could not construct one. It changes
  which object is mined, before `mine()` runs; the unminable count is unchanged
  (3→3 on 60 worlds, 20→20 on 500), so no world the segmenter cannot narrate was
  routed around.
- **Cross-fire between the new invariants.** `unexpected_kills == []` for all 14
  cegis mutants and `predicted_but_missed == []` for all but the two
  pre-registered frontier survivors. The claimed independence of
  `effects_agree_with_the_evidence` and `rules_fire_on_the_action_they_name`
  holds under measurement, including for `cm-relabel-rule-action`, which I
  specifically expected to leak into the effect invariant and does not.
- **`cm-drop-effect-destination` secretly dying.** Survives all five other
  invariants on all 17 evaluated worlds.
- **The `UNRESOLVED` sentinel** (added mid-review). Correctly handled: `if
  claimed is UNRESOLVED: unread.append(index); continue`, which folds into a
  `skipped`, not a violation. Unreachable in `gridworld` (all four actions are
  compass directions). One cosmetic flaw — the resulting `skipped` message says
  "could not be read as one rigid mover translation" and pulls its reason from
  `refused`, which has no entry for a perfectly readable transition, so it would
  print "no reason recorded". Wrong message for that path; the path cannot be
  reached in this corpus.
- **Test suite.** `python -m pytest fuzzlab -q` → **89 passed**, clean, including
  the new negative control.

---

## Priority, if only three things get fixed

1. **R1** — the `expected > 0` guard in `costs_are_the_world's` excludes the one
   case both docstrings claim it checks, on 27.6% of the corpus.
2. **R2** — `_mined_subject`'s stale docstring and, more importantly, the stale
   cause it prints into the user-visible `skipped` detail; the real cause is
   segmenter track fragmentation (25 of 27 fallback worlds).
3. **§2.1 / §4.2** — either add a mutant that falsifies the live `?dir →
   DELTA[action]` path (and downgrade the `cm-freeze-lifted-direction`
   overclaim), or accept that the lifted-rule audit rests on the scope change
   alone; and make the four guard invariants skip the non-mover worlds that
   `effects_agree_with_the_evidence` already skips, so the coverage column is
   honest for all six.
