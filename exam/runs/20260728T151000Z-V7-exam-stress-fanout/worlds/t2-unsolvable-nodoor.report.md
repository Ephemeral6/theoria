# Examiner's report — `t2-unsolvable-nodoor`

Independent audit of the world, its twelve held-out items, the marker that scores
them, and the feasibility of a verdict item over this world.

Paper `v2-heldout-t2-unsolvable-nodoor`, `per_class=2`, 12 items, rubric digest
`e06bdf52…1cb091`. Everything below was recomputed locally; no file outside this
report was written and no source file was edited.

**Headline.** The instrument's classification of this world is **correct on all
twelve items** — I re-derived every transition from `spec.json` with a
hand-written model that never imports `worldgen`, and all twelve agree on
`frame_after`, `rule`, `split`, `frame_changes` and `class`. But the two items it
calls `theory` are not theory items in any useful sense: **a theory-free examinee
scores 12/12 on this paper**, twice over, by two independent routes. The world's
honest effective size is **zero**, not two.

---

## 1. Is the classification true of this world's mechanics?

### 1.1 The world, recomputed

`worldgen/out/worlds/t2-unsolvable-nodoor/spec.json` gives a 6×7 layout, agent
start `(1,2)`, goal `(4,5)`, and two `door` entities at `(3,4)` and `(4,2)`, both
on net `a` with polarity `open_when_on`. **There are no `switch` entities.** Net
`a` is an OR over the empty set, so its aggregate bit is `0`; `open_when_on`
wants `1`; the bits never match. Both doors are impassable and drawn (colour 2)
at every instant, for the whole of time. That single fact is the whole world.

My independent reachability sweep from `(1,2)`:

```
11 agent cells: (1,1) (1,2) (1,3) (2,1) (2,2) (2,3) (3,1) (3,2) (3,3) (4,1) (4,3)
goal (4,5) reachable?  False        -> UNSOLVABLE confirmed
```

which matches `ground_truth.json`'s `solvability.reachable_states = 11` and
`agent_cells = 11` exactly, and matches the certificate statement in
`GROUND_TRUTH.md:37`. Rule firing counts also agree with
`ground_truth.json["reversibility"]["rules"]`: 11 states × 4 actions = 44
transitions = 28 `walk` + 12 `blocked_by_wall` + 4 `blocked_by_door`.

### 1.2 All twelve items, hand-checked

Recomputed with my own transition model (no `GridWorld`, no `ground_truth.json`),
split tag recomputed by re-keying against `raw_trace.jsonl` myself:

| item | action | agent before → after | my rule | frame changes | my split | instrument class | agree |
|---|---|---|---|---|---|---|---|
| `-000` | RIGHT | (3,3) → (3,3) | `blocked_by_door` (target (3,4) is a closed door) | no | heldout | `free` | ✔ |
| `-001` | LEFT | (3,2) → (3,1) | `walk` | yes | replay | `memorised` | ✔ |
| `-002` | LEFT | (4,3) → (4,3) | `blocked_by_door` (target (4,2)) | no | heldout | `free` | ✔ |
| `-003` | UP | (2,1) → (1,1) | `walk` | yes | heldout | `theory` | ✔ |
| `-004` | UP | (4,1) → (3,1) | `walk` | yes | replay | `memorised` | ✔ |
| `-005` | DOWN | (4,1) → (4,1) | `blocked_by_wall` (target (5,1)) | no | replay | `free` | ✔ |
| `-006` | DOWN | (1,1) → (2,1) | `walk` | yes | heldout | `theory` | ✔ |
| `-007` | LEFT | (3,1) → (3,1) | `blocked_by_wall` (target (3,0)) | no | replay | `free` | ✔ |
| `-008` | RIGHT | (1,3) → (1,3) | `blocked_by_wall` (target (1,4)) | no | heldout | `free` | ✔ |
| `-009` | UP | (1,2) → (1,2) | `blocked_by_wall` (target (0,2)) | no | heldout | `free` | ✔ |
| `-010` | RIGHT | (4,1) → (4,1) | `blocked_by_door` (target (4,2)) | no | replay | `free` | ✔ |
| `-011` | DOWN | (3,2) → (3,2) | `blocked_by_door` (target (4,2)) | no | replay | `free` | ✔ |

**No defect found.** Every `free` item leaves the frame bit-identical (all eight
are `blocked_by_*`, and `blocked_by_*` means "nothing changes" by definition —
`GROUND_TRUTH.md:25-26`). Both `theory` items do change the frame. The four
replay tags were each traced to a specific line of `raw_trace.jsonl`
(`-011`↔t=2, `-001`↔t=3, `-005`↔t=5, `-010`↔t=7, `-007`↔t=9, `-004`↔t=8), and
the eight heldout keys are genuinely absent from the trace.

### 1.3 Why two-thirds are free — and it *is* structural

Your hypothesis is right, and it is sharper than "mostly `blocked_by_*` rules".
The mechanism is arithmetic:

> Under a matched quota, **every usable rule gets exactly `2 × per_class` items**
> (`heldout_worldgen.py:172-175`). A rule whose `then` clause is "nothing
> changes" produces `2 × per_class` items on which `frame_before == frame_after`,
> so the bluffer is right on all of them and they are all `free`. A
> state-changing rule produces `per_class` `memorised` and `per_class` `theory`.
> Therefore **free share ≈ (no-op rules) / (usable rules)**.

Here that is 2/3 — `blocked_by_wall` and `blocked_by_door` are both no-op rules,
and only `walk` moves anything. 8/12 = 0.667, the catalogue maximum:

```
t2-unsolvable-nodoor   12 items   8 free   0.667   <- rank 1 of 20
t2-gravity-push         8 items   5 free   0.625
t1-* (seven worlds)     8 items   4 free   0.500
t3-cycler-portal-lock  16 items   4 free   0.250   <- rank 20
```

And the causation runs through the unsolvability, not alongside it. This world is
`t1-switch-toggle` with the switch deleted (`spec.json:52`,
`variant_delta`). Deleting the switch does two things at once:

1. it makes the world unsolvable, and
2. it converts the `switch_door` family's *dynamic* machinery into permanent
   scenery. `door_mirrors_net` becomes a cascade that never changes anything
   (`ground_truth.json` records `verdict: "unreachable"`, `measured: null`); the
   toggle rule does not exist at all; and `blocked_by_door` — which in a solvable
   switch world fires only while the net is off — fires forever.

So the entity that makes the world unsolvable is precisely the entity that turns
a state-changing mechanism into a no-op rule. Measured against the solvable
parent:

| | `t1-switch-toggle` (parent) | `t2-unsolvable-nodoor` (switch deleted) |
|---|---|---|
| rules that fire | 6 | **3** |
| firing counts | `walk` 62, `blocked_by_wall` 32, `walk_through_door` 4, `blocked_by_door` 3, `toggle_switch` 2, `blocked_toggle_would_shut_door` 1 | `walk` 28, `blocked_by_wall` 12, `blocked_by_door` 4 |
| usable at `per_class=2` | `blocked_by_wall`, `walk` (2) | `blocked_by_door`, `blocked_by_wall`, `walk` (3) |
| no-op rules among them | 1 of 2 | **2 of 3** |
| free share | 0.500 | **0.667** |

Deleting the switch does both halves of the damage at once. It destroys three
dynamic rules (`toggle_switch`, `walk_through_door`,
`blocked_toggle_would_shut_door` — 7 firings between them, all gone), and it
*promotes* `blocked_by_door` from 3 firings (one short of the matched quota, so
excluded from the parent's paper) to 4 (exactly enough to qualify). A no-op rule
is added to the usable set at the same moment three state-changing rules leave
it. **Examining an unsolvable world by held-out frame
prediction is structurally biased toward free marks, because unsolvability in
this factory is manufactured by disabling a mechanism, and a disabled mechanism
is a rule that does nothing — one that fires constantly and changes nothing,
which is the ideal shape for a free item.** That generalises past this world: any
"unsolvable-by-removal" variant will inherit the same profile.

### 1.4 A cross-check on the instrument itself

The class is a **deterministic function of two other fields the instrument
already records**:

```
class = free       if not frame_changes         (regardless of split)
      = memorised  if frame_changes and split == "replay"
      = theory     if frame_changes and split == "heldout"
```

I verified this holds on **236 of 236 items across all 20 profiled worlds**, with
0 violations, 0 `dead`, 0 anomalies. This is not a defect — it is what the three
voters *are* — but it is worth stating plainly, because it means `theory` does
not mean "requires a world model". It means "a state-changing transition the
published trace did not contain". Section 3 shows how far apart those two are.

---

## 2. Does the marker misjudge anything?

### 2.1 The two structural invariants — both hold

| examinee | score | verdicts | `gap_replay_minus_heldout` |
|---|---|---|---|
| `oracle` | 12.0 / 12 | 12 correct, **0 wrong** | 0.0 |
| `null` | 0.0 / 12 | **12 unanswered**, 0 wrong | 0.0 |
| `memoriser` | 10.0 / 12 | 10 correct, 2 wrong | 0.333 |
| `bluffer` | 8.0 / 12 | 8 correct, 4 wrong | 0.0 |

Ground truth is never marked wrong; silence is never paid and is never confused
with error. Both confirmed.

### 2.2 Twenty-eight near-truth probes

All against `-003` (a `theory` item), via `rubrics_heldout.grade_frame_exact`
directly, with the item's real truth dict. `✓` = the verdict a fair examiner
would give.

| answer | verdict | detail | fair? |
|---|---|---|---|
| exact, bare list | `correct` | `cells_wrong: 0` | ✓ |
| exact, `{"frame_after": …}` | `correct` | | ✓ |
| exact, `{"frame": …}` | `correct` | | ✓ (undocumented leniency) |
| exact, `{"after": …}` | `correct` | | ✓ (undocumented leniency) |
| exact, tuple of tuples | `correct` | | ✓ |
| exact, double-wrapped `{"frame_after":{"frame_after":…}}` | `correct` | | ✓ (leniency) |
| **transposed** (7×6) | `wrong` | `shape_ok:false, cells_wrong:-1` | ✓ |
| **one cell changed** 0→1 | `wrong` | `shape_ok:true, cells_wrong:1` | ✓ |
| one cell = 4 (outside palette) | `wrong` | `"not a well-formed frame"` | ✓ |
| **strings instead of ints** | `wrong` | `"not a well-formed frame"` | ~ (see A) |
| floats `6.0`/`0.0` | `wrong` | `"not a well-formed frame"` | ~ (see A) |
| bools instead of ints | `wrong` | `"not a well-formed frame"` | ✓ (documented, `:104`) |
| **short grid** (5 rows × 7) | `wrong` | `shape_ok:false, cells_wrong:-1` | ✓ |
| **ragged** (one row of 5) | `wrong` | `"not a well-formed frame"` | ✓ |
| flat 42-int list | `wrong` | `"not a well-formed frame"` | ✓ |
| **`{"abstain": true}`** | `abstained` | | ✓ |
| `"abstain"` / `"I cannot tell"` (strings) | `abstained` | | ✓ |
| `"no idea"` (string) | `wrong` | `"not a well-formed frame"` | ~ (see C) |
| **`{}`** empty dict | **`wrong`** | `"not a well-formed frame"` | **✗ (see B)** |
| `[]` empty list | `wrong` | | ✓ |
| **`null`** | `unanswered` | `"null answer"` | ✓ |
| `{"frame_after": null}` | `wrong` | | ~ (see B) |
| `{"abstain":true, "frame_after": <truth>}` | `abstained` | 0 points | ~ (see D) |
| all-wall 6×7 grid | `wrong` | `cells_wrong: 17` | ✓ |
| two agents (invariant violated) | `wrong` | `cells_wrong: 1` | ✓ |
| bluffer answer (input frame) | `wrong` | `cells_wrong: 2` | ✓ |

On the `free` item `-000`: the bluffer's answer *is* the truth and scores
`correct`; transposed → `wrong`; `{"abstain": true}` → `abstained`; `{}` →
`wrong`.

### 2.3 The four arguably-wrong verdicts

**(B) `{}` is scored `wrong`, but `null` is scored `unanswered`.** This is the
only one I would call a defect rather than a judgement call. `mark.py:51-53`
gives `unanswered` to an item id *absent* from the submission; `grade_frame_exact`
(`rubrics_heldout.py:138-142`) gives `unanswered` to an explicit `None`; but an
empty JSON object falls through `_as_frame` (`:86-90`: dict, not abstaining, none
of the three frame fields) and returns `None`, which the caller reads as
malformed and scores `wrong`. An examinee whose harness emits `{}` for "I
produced nothing" is charged with a wrong prediction rather than a blank. It
costs no points either way, but `wrong` vs `unanswered` is exactly the
distinction `mark.py:9-14` says matters — "an arm with no deliverable … that is a
finding, not a failure to answer". Same for `{"frame_after": null}`. **Not
world-specific; a one-line fix in `_as_frame`'s dict branch would settle it.**

**(A) A well-formed prediction in the wrong type is `wrong`, not distinguishable
from a wrong prediction.** `[["6","0",…]]` and `[[6.0,0.0,…]]` both carry the
exactly-correct frame and are scored identically to a genuinely mistaken grid.
The verdict vocabulary (`model.py:233`) has no `malformed`, so the rubric has
nowhere else to put it; `detail.why` does distinguish them, so a diagnosing
reader can tell. I record it as a known limit, not a bug — but note it is the
same failure mode `_LEGAL_CELLS` (`:56`, and the comment at `:50-55`) was fixed
to avoid: a formatting refusal "reads on the report as an examinee that cannot
format an answer".

**(C) The abstention vocabulary is four strings.** `_is_abstention`
(`:115-121`) accepts `abstain / abstained / unknown / i cannot tell`. `"no idea"`,
`"I don't know"`, `"cannot determine"` all fall through to `wrong`. Zero points
either way; it only mislabels the verdict.

**(D) An abstention that also carries the correct frame is paid nothing.**
`grade_frame_exact` tests `_is_abstention` (`:144`) before `_as_frame` (`:149`),
so `{"abstain": true, "frame_after": <exactly right>}` scores `abstained` = 0.
Defensible — a declared abstention is a declared abstention — but worth knowing
if a real examinee ever hedges.

**Non-issue, checked and cleared:** `detail.expected_shape` (`:152-154`) reveals
`[6,7]` on the malformed branch, but the sheet already publishes
`paper["grid"] = [6, 7]`, so nothing is leaked. And `_legal_cells` correctly
takes this world's own palette `{0,1,2,6}` from the truth side rather than A0's
`{0,2,4,8}` — a frame of this world would have been rejected wholesale under the
default.

---

## 3. A cheap examinee that beats the bluffer floor — it beats the *oracle's* score

Five strategies, each a pure function of the sheet (`frame_before`, `action`,
`legend`, grid dims). None reads `ground_truth.json`, `Item.truth`, or the trace.

| strategy | score | free | memorised | **theory** | replay | heldout |
|---|---|---|---|---|---|---|
| `bluffer` (the published floor) | 8.0 / 12 | 8/8 | 0/2 | 0/2 | 0.67 | 0.67 |
| always-move (if in bounds) | 4.0 / 12 | 0/8 | 2/2 | 2/2 | 0.33 | 0.33 |
| wall-only prior (blocked only by `legend["wall"]`) | 8.0 / 12 | 4/8 | 2/2 | 2/2 | 0.67 | 0.67 |
| **legend prior: move iff target == `legend["floor"]`** | **12.0 / 12** | 8/8 | 2/2 | **2/2** | 1.00 | 1.00 |
| **no-legend frame statistics** | **12.0 / 12** | 8/8 | 2/2 | **2/2** | 1.00 | 1.00 |

The winning strategy is one sentence: *the agent moves one cell in the action's
direction if that cell shows the colour the legend calls `floor`, and otherwise
nothing happens; the vacated cell becomes floor.* It captures **2 of 2 theory
items — 100% of the residue** — and ties the oracle at 12/12.

The last row removes even the legend: infer `agent` = the unique colour appearing
exactly once, `floor` = the modal interior colour, then apply the same rule. Also
12/12. So the residue does not survive **any** contact with a generic grid-game
prior, not even one that does not know what the colours are called.

**Why this world in particular is defenceless.** Three of its own recorded
properties conspire:

* `frame_determines_state.injective = true` (11 states, 11 distinct frames) —
  there is no hidden state to reason about;
* the invariant `door_presence_tracks_net` holds on all 11 states, which
  *guarantees* that a cell is impassable exactly when it is drawn — so
  impassability is a visible property of the frame, never an inference;
* the doors never open, so "drawn ⇒ blocked" needs no dynamics at all.

Together: every one of the 44 reachable transitions is settled by reading one
cell's colour. A world model is not merely unnecessary — there is nothing for it
to model.

This is not universal. I ran the same `move-into-floor` prior across the whole
catalogue: it matches the oracle exactly on **10 of 20 worlds** and captures only
25–67% of the theory residue on the pushing / latching / portal worlds
(`t3-full-house` 2/8, `t3-cycler-portal-lock` 2/6, `t1-push-open` 2/4,
`t2-switch-push` 4/8). `t2-unsolvable-nodoor` is among the ten it saturates, and
it is the largest of them by item count.

**Honest reading:** the report is a failure for the paper, not for the strategy.
This world's `theory` residue is an artefact of the taxonomy's three voters, none
of which happens to encode the one prior that settles it.

---

## 4. Honest effective size

**Zero.** With the bluffer as the baseline the instrument's answer is 2; with a
generic grid prior as the baseline it is 0. Both numbers should be quoted, and
the second is the one a reader should carry.

Even taking the instrument's own number at face value, 2 overstates it. The two
`theory` items are:

```
-003   heldout   UP    (2,1) -> (1,1)
-006   heldout   DOWN  (1,1) -> (2,1)
```

They are **exact inverses of the same board edge** `(1,1)—(2,1)`. And this world
ships a reversibility stamp asserting `walk` is re-witnessable with score 1.00
and "reversible on open floor" (`GROUND_TRUTH.md:24,43`). An examinee that has
`-003` has `-006` for free from a property the world itself publishes. **One
distinct fact is being tested twice.** Effective size 1 by that reading, 0 by
Section 3's.

**Dead weight, by name:**

| rule | items | classes | verdict |
|---|---|---|---|
| `blocked_by_wall` | 4 (2 replay, 2 heldout) | 4 free | **dead weight** — `then: nothing changes` |
| `blocked_by_door` | 4 (2 replay, 2 heldout) | 4 free | **dead weight** — same, and permanently so |
| `door_mirrors_net` | **0** | — | carries no item at all: a cascade whose net has no driver, `verdict: "unreachable"` in `ground_truth.json` |
| `walk` | 4 (2 replay, 2 heldout) | 2 memorised, 2 theory | the only rule that discriminates |

Three of the world's four declared rules contribute nothing. `barren_rules` in
the profile lists two of them; the third (`door_mirrors_net`) is invisible to the
instrument because it never fires and so never appears in `by_rule` — worth a
line in the report renderer, since "0 items" and "4 free items" are different
kinds of nothing.

**Can it rank two examinees apart?** Yes, weakly, and only against the reference
set: 12 / 10 / 8 / 0 for oracle / memoriser / bluffer / null are four distinct
scores. But every one of those gaps is the same single question — *does the frame
change?* — and any examinee that answers it (see §3) lands at 12 and is
indistinguishable from the oracle. The paper cannot separate a world theory from
a colour lookup, which is the separation it exists to make.

**Two quota facts worth recording.** `blocked_by_door` has exactly 4 reachable
transitions in the entire world (2 in trace, 2 out), so the `per_class=2` quota
**exhausts the rule completely** — there is no third witness anywhere. At
`per_class=3` the world drops to 2 usable rules; at `per_class=4` it drops to 1
and the paper is refused as infeasible. This world sits on the feasibility edge.
Also, the `gap_replay_minus_heldout` headline is **diluted by the free share**:
the memoriser posts 0.333 here where a free-free world would give 1.0, because
the eight free items are scored 1.0 on both sides. On the world with the highest
free share in the catalogue, the exam's headline axis is at its weakest.

---

## 5. Could this world carry a `verdict` item?

**Answer: it would fall squarely into class (i), `small_unsolvable` — and no, it
cannot carry one today. The blocker is not the world; it is that the certificate
grammar has no kind that can express why this world is unsolvable, and the one
kind that comes closest is guaranteed to refuse it.**

### 5.1 The numbers

| quantity | value | threshold | verdict |
|---|---|---|---|
| reachable states | **11** | `LARGE_SPACE_THRESHOLD = 10^12` (`verdict.py:88`) | 11 / 10^12 = **1.1 × 10⁻¹¹** |
| `enumerate_states` result | 11 states, `truncated: False` | `MAX_ENUMERATION = 200 000` (`rubrics_verdict.py:112`) | enumeration finishes in microseconds |
| board | 6 × 7 | `SMALL_BOARD_MAX_HEIGHT/WIDTH = 12 / 24` (`verdict.py:92-93`) | `board_size_class = "small"` |
| solvable? | no; `enumerate_states(...)["solution"] is None` | — | `claim = "unsolvable"` |

`_small_space` (`verdict.py:579-598`) would accept it without complaint.
`_large_space` (`:601-618`) would **raise** — 11 is eleven orders of magnitude
short of the class (ii) bar, and the `AssertionError` at `:604-608` says exactly
why: *"enumeration is not out of reach and the question does not test what it
claims to"*. So: **class (i), `small_unsolvable`, `search_credible = True`.**

That is the least valuable of the three classes for this framework. Class (ii) —
"our home ground" (`rubrics_verdict.py:11-12`) — is out of reach by construction:
this world has 11 states and no latching mechanism to inflate them.

### 5.2 What is missing — measured, not asserted

I encoded the world as an A2-family `Level` doc (layout verbatim, `S` at (1,2),
`G` at (4,5), `D` at (3,4), `button: null` so the door never opens) and ran the
real `check_certificate` against every kind in the closed grammar. Two encodings
of the second door at (4,2), since `Level` has room for only one `door`:

```
(4,2) as '#'         enumerate_states -> 11 states, truncated=False, solution=None
(4,2) as '.'         enumerate_states -> 12 states, truncated=False, solution=None
                     both: relaxed graph puts start (1,2) and goal (4,5) in
                     the SAME component, representative (1,1)
```

| certificate offered | verdict | why (from the checker itself) |
|---|---|---|
| `{"kind":"invariant","invariant":"cart_region",…}` | **refused** | *"start and goal are in the same component ([1,1]), so this invariant does not separate them"* |
| `{"kind":"invariant","invariant":"cart_row",…}` | refused | *"cart_row is not monotone … (deltas [-1,0,1])"* |
| `{"kind":"invariant","invariant":"cart_col",…}` | refused | *"cart_col is not monotone … (deltas [-1,0,1])"* |
| `{"kind":"cut_set","cells":[[3,4]]}` | refused | *"[[3,4]] are not declared hazards by this variant"* |
| `{"kind":"cut_set","cells":[[3,4],[4,2]]}` | refused | same |
| `{"kind":"counting","bound":6,"limit":5}` | refused | *"this variant has no step limit, so a counting argument has nothing to count against"* |

**All four certificate forms fail.** The interesting one is `cart_region`, and it
fails for a reason that is a design decision, not an accident:

* `Level.passable` (`rubrics_verdict.py:177-189`) treats **the door as open** —
  "Door open, button walkable, hazards ignored";
* `relaxed_edges` (`:300-321`) inherits that, deliberately over-approximating so
  that a separation in the relaxed graph is a separation in the real one;
* in A2 that is sound, because A2's door *can* be opened by its button;
* in `t2-unsolvable-nodoor` the door **can never open**, because its net has no
  driver — and the over-approximation cannot see the difference between "closed
  now" and "closed forever".

So the relaxed graph joins start to goal through (3,4), the true statement *"the
goal is in a different component"* is refused, and the honest certificate for
this world is not expressible. That is a **false negative** of exactly the kind
`rubrics_verdict.py:81-86` announces it is willing to pay for — it costs the
examinee points and never hands out points for a false theorem. Correct
soundness direction; wrong world.

### 5.3 What an examinee could actually score

With no admissible certificate, the best available reason is
`{"claim":"unsolvable","reason":"exhaustive_search"}`, which
`_score_unsolvable_reason` (`:697-704`) pays at `SEARCH_CREDIT = 0.4` of the
reason half since `search_credible = True`. Ceiling:

```
0.5 (verdict) + 0.5 x 0.4 (reason) = 0.7 of the item's points
```

**A verdict item over this world would be an item on which nobody can score full
marks and on which "I enumerated eleven states" is the best answer obtainable.**
That is the degenerate corner of class (i), not a question about theory.

### 5.4 The gap, stated concretely

Four things are missing, in increasing order of difficulty:

1. **No adapter.** `Level` (`rubrics_verdict.py:129-155`) parses an A2 level doc
   — `rows` of `#.SGBDPXs!` markers, one optional `button`/`door`/`portal`.
   Nothing translates a `worldgen` `spec.json` into one. `verdict.build()` is
   hard-wired to `WORLD_ID = "a2"` (`verdict.py:80`) and every item goes through
   `_emit_spec` → `proxy.variants.Variant` with `base_game: "a2"`.
2. **Representational loss.** `Level` holds **one** door and ties it to a button.
   This world has **two** doors and **no** button. One door has to be re-encoded
   as wall (which throws away the mechanic the item would be about) or as floor
   (which changes the reachable count from 11 to 12).
3. **The certificate grammar cannot say it.** There is no kind for *"a mechanism
   is permanently in state X because its driver does not exist"*. The missing
   kind is roughly `{"kind":"dead_mechanism","entity":[3,4],"reason":"net 'a' has
   no switch"}` — plus a relaxation that consults it, i.e. `relaxed_edges` would
   need to accept a set of provably-never-passable cells. That is the real work,
   and it is a change to a frozen, digest-covered marking rule.
4. **The class this world can offer is the one the framework least needs.**
   Class (i) with 11 states, where an enumerating searcher is right and gets 70%.
   The catalogue's single unsolvable world cannot supply a class (ii) item at
   all; nothing in `worldgen` builds a state space anywhere near 10^12 (the
   largest is `t3-full-house` at 2 654 reachable states — nine orders short).

**Recommendation:** do not point `verdict.py` at this world. If the goal is a
generated verdict paper, the cheaper route is a `worldgen` family that inflates
the state space with latches the way `comb_open`/`comb_room` do
(`verdict.py:258-310`), *and* a certificate kind for dead mechanisms. Until both
exist, the honest statement is the one you expected: **no, and the gap is a
certificate grammar that treats every door as openable.**

---

## Things you did not ask about

### A. The sheet prints the answer's rule name on every item

`exam/papers/heldout_worldgen.py:204` sets `tags=(split, "rule:%s" % cand["rule"])`,
and `exam/model.py:108-110` (`Item.sheet_side`) copies `tags` verbatim onto the
sheet. What the examinee receives for this world:

```
t2-unsolvable-nodoor-000  tags=['heldout', 'rule:blocked_by_door']  action=RIGHT
t2-unsolvable-nodoor-003  tags=['heldout', 'rule:walk']             action=UP
t2-unsolvable-nodoor-009  tags=['heldout', 'rule:blocked_by_wall']  action=UP
...
```

`blocked_by_wall` and `blocked_by_door` are printed on the eight items whose
answer is "nothing changes". `walk` is printed on the four whose answer is "the
agent moves one cell in the action's direction". **An examinee that reads only
the tag and never looks at a single colour scores 12.0/12 — free 8/8, memorised
2/2, theory 2/2, replay 1.00, heldout 1.00.** I built it; that is a measured
number.

The paper's own notes call this out as something it is careful *not* to do
(`heldout_worldgen.py:239-241`): *"The rule names are the answer vocabulary … a
sheet that lists them hands the examinee the alphabet it is being asked to
discover"* — and then withholds the names from `notes.quota` while printing them
on every item. `exam/papers/handover.py:739-741` gets the same call right, for
the same stated reason.

**The exam's own gate already refuses this paper.** `exam.leakage.check_paper` on
`v2-heldout-t2-unsolvable-nodoor` raises `LeakageError`, with `check: "probe"`
hits on every item — the `leak_probes=(cand["rule"],)` declared at
`heldout_worldgen.py:203` are found in the sheet text. Two instruments disagree,
and the leakage checker is the one that is right.

Fix is one line: drop `"rule:%s"` from `tags` and put the rule in `Item.truth`
only (it is already there, `heldout_worldgen.py:195`; `axes()` reads it from the
key doc at `:311-313`, not from tags). Nothing downstream of the sheet needs it.

*Not world-specific* — it affects all 20 held-out papers. A sibling examiner
(`t1-portal-oneway`) reports the same finding independently, which is
corroboration rather than duplication.

### B. `door_mirrors_net` is invisible to the discrimination instrument

`_cross(items, "rule")` (`discrimination.py:174-179`) builds `by_rule` from the
items, so a declared rule that carries zero items simply is not in the table, and
`barren_rules` (`:194-196`) can only name rules that *have* items. This world's
`by_rule` lists 3 rules; the world declares 4. "Zero items" and "four free items"
are different diagnoses and the report cannot currently distinguish them.

### C. The world id announces its own answer

`paper.sheet()` publishes `paper_id = "v2-heldout-t2-unsolvable-nodoor"` and
`world.world_id = "t2-unsolvable-nodoor"`. Harmless on a frame-prediction paper.
**Fatal on a verdict paper** — `verdict.py:41-48` goes to considerable trouble to
give items opaque digest ids precisely so the class is not readable off the
sheet, and this world's name contains the string `unsolvable`. If §5's adapter
is ever built, the world ids need the same opaque treatment.

### D. `unchanged_frame_share` is computed and then not published

`heldout_worldgen.py:249` puts `unchanged_frame_share: 0.666667` in `notes`, and
`Paper.sheet` (`model.py:156-167`) does **not** include `notes`. Checked, because
on this world that number would be a strong hint (predict stasis, score 8/12).
It is correctly withheld.

---

## Provenance

* World: `worldgen/out/worlds/t2-unsolvable-nodoor/` (`spec.json`,
  `raw_trace.jsonl`, `ground_truth.json`, `GROUND_TRUTH.md`) — read only.
* Profile audited: `exam/runs/20260728T151000Z-V7-exam-stress-fanout/worlds/t2-unsolvable-nodoor.json`.
* Code read, never modified: `exam/tools/discrimination.py`,
  `exam/papers/heldout_worldgen.py`, `exam/papers/worldgen_port.py`,
  `exam/papers/verdict.py`, `exam/grading/rubrics_heldout.py`,
  `exam/grading/rubrics_verdict.py`, `exam/grading/mark.py`, `exam/leakage.py`,
  `exam/model.py`.
* All computation local, deterministic, offline. No network, no LLM, no `git`.
  No sealed-pile contact — this world is synthetic and `arc-recon/` was never
  opened. `pytest` was not run.
* This report is the only file created.
