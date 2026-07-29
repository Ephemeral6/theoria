# Examiner's report — `t2-switch-push`

Independent audit of the discrimination profile at
`exam/runs/20260728T151000Z-V7-exam-stress-fanout/worlds/t2-switch-push.json`.
Read-only; no source file was edited, no `git` run, no network. All numbers below
were recomputed locally.

**Headline.** The instrument's classification is *correct on every one of the 24
items* — no misclassification, no anomaly, no `dead` item, and the shipped JSON
reproduces byte-for-byte from `exam.tools.discrimination.profile_world`. But its
`effective_size: 8` is a four-fold overstatement of this paper's real size. A
25-line answer strategy that reads nothing but the sheet scores **20/24**,
capturing 6 of the 8 `theory` items; a 35-line one scores **24/24**. The honest
effective size of this paper is **2 items** — both `toggle_switch`, both
`heldout` — and even those fall to a coin-flip guess about switch polarity that
this paper never gets to punish.

---

## 0. What the world actually is

Recomputed independently from `worldgen/out/worlds/t2-switch-push/spec.json` plus
the rule table in `GROUND_TRUTH.md`, without importing `worldgen`
(scratchpad `indep.py`). 7x9 grid, three corridors (rows 1/3/5) joined by two
vertical passages (cols 1 and 7).

| | |
|---|---|
| agent start | `(1,1)` |
| block | `(3,2)` |
| door | `(3,4)`, net `a`, polarity `open_when_on` |
| switch | `(5,1)`, mode `toggle`, net `a` |
| palette | floor 0, wall 1, block 2, switch 3, switch\_on 4, door 5, agent 6 |

My re-derivation reproduces **175 reachable states** (matches
`ground_truth.json.frame_determines_state.states` and the invariant stamps in
`GROUND_TRUTH.md`), all **190 published trace steps** with zero mismatches, and
the full 700-transition rule census:

```
blocked_by_wall 336 | walk 329 | toggle_switch 12 | walk_through_door 7
push 6 | blocked_by_block 5 | blocked_by_door 5
```

`frame_determines_state.injective = true`, `collisions: []` — so a `correct`
verdict on this world provably implies the examinee named the right *state*, not
just a colliding rendering. That is the precondition for everything below.

The state space is tiny because a block may not enter a *mechanism* cell. I
verified this by re-running the closure under the three alternative readings of
"free":

| block may enter | reachable states |
|---|---|
| neither switch nor open door (**the world's actual rule**) | **175** |
| open door too | 415 |
| switch too | 222 |
| both | 462 |

The block therefore only ever occupies `(3,1) (3,2) (3,3) (4,1)`.

---

## 1. Is the classification true of this world's mechanics?

**Yes — all 24 items check out.** I recomputed `frame_after` and the rule tag for
every item from my own simulator and compared against `Item.truth`.

* **24/24 frames match**, **24/24 rule tags match**.
* Every `free` item has `frame_after == frame_before`; every `theory` and
  `memorised` item changes the frame. The two directions the brief asked about
  (`free` that moves, `theory` that doesn't) **do not occur**.
* `by_class` 8 free / 8 memorised / 8 theory, `dead: 0`, `anomalies: []` —
  all confirmed.

Items hand-checked in full (state before → state after, re-derived):

| item | action | agent / block / net-bit before | rule | class | verdict on the label |
|---|---|---|---|---|---|
| `-000` | UP | (3,4) / (3,3) / 1 | `blocked_by_wall` | free | correct — target `(2,4)` is wall |
| `-001` | RIGHT | (3,1) / (3,2) / 1 | `push` | theory | correct — block → (3,3), agent → (3,2) |
| `-005` | RIGHT | (3,3) / (3,2) / 1 | `walk_through_door` | theory | correct — agent → (3,4) |
| `-006` | LEFT | (5,2) / (4,1) / 0 | `toggle_switch` | theory | correct — bit 0→1, **door at (3,4) erased** |
| `-010` | DOWN | (3,1) / (4,1) / 1 | `blocked_by_block` | free | correct — beyond is the **switch cell** |
| `-012` | DOWN | (2,1) / (3,1) / 0 | `push` | theory | correct — block → (4,1) |
| `-017` | DOWN | (3,1) / (4,1) / 0 | `blocked_by_block` | free | correct — beyond is the switch cell |
| `-018` | LEFT | (3,5) / (3,2) / 1 | `walk_through_door` | theory | correct — agent → (3,4) |
| `-020` | LEFT | (3,2) / (3,1) / 1 | `blocked_by_block` | free | correct — beyond is wall |
| `-021` | RIGHT | (3,2) / (3,3) / 0 | `blocked_by_block` | free | correct — beyond is the **shut door** |
| `-023` | LEFT | (3,5) / (3,3) / 1 | `walk_through_door` | memorised | correct |

The remaining 13 were checked by the same procedure in bulk; the run reports
`MISMATCHES: none`.

### The two-mechanism interaction — and where it went

The spec's own note (`spec.json:63`) says the point of composing `push` with
`switch_door` is that "the block can be parked in front of the door, which is a
configuration no single-family world can produce." That configuration is real and
reachable, and it produces exactly one genuinely cross-mechanism transition:

> `agent=(3,2) block=(3,3) bit=1 RIGHT` → **nothing happens** (`blocked_by_block`,
> `heldout`).

The door is **open** — it renders as `0`, indistinguishable from floor — and the
push *still* fails, because a block may not enter a mechanism cell. No
single-family theory predicts this: a push theory says "beyond is floor, so the
block slides"; a door theory says "the door is open, so things pass". This is the
one transition in the world that requires both books at once.

Two things happen to it, and neither is a bug in your instrument, but both matter:

1. **The instrument classifies it `free`** (frame unchanged ⇒ the bluffer is
   right ⇒ all three voters agree). Under the taxonomy's own definitions that is
   the right label. But it is the single item in this world that defeats *every*
   cheap strategy I could write (§3), so `free` here means "ranks nobody among
   these three fakes", not "easy". Worth a line in the tool's docstring: the
   classification is a fact about the three voters, and the most discriminating
   transition in this world is invisible to all of them because they all happen to
   say "nothing happens".
2. **It is not on the paper.** `blocked_by_block` has 3 held-out candidates;
   `_pick` (`exam/papers/heldout_worldgen.py:113`) takes the 2 whose salted sha256
   sorts first, and those are the two `beyond = switch cell` variants (`-010`,
   `-017`). The interaction item is dropped by the hash. Not a defect — the
   sampler is doing what it says — but on this world the sampler discarded the one
   item the world was built to produce.

No defect found in the classifier itself.

---

## 2. Does the marker misjudge anything?

Stressed via `exam.grading.rubrics_heldout.grade_frame_exact` imported directly,
25 answer shapes × 5 items (`-001` push/heldout, `-006` toggle/heldout,
`-010` blocked/heldout, `-018` door/heldout, `-021` blocked/replay). The rubric
was not edited.

### Structural invariants — both hold

| examinee | verdict tally | score |
|---|---|---|
| `oracle` | **24 correct** | 1.000 |
| `null` | **24 unanswered** (0 correct) | 0.000 |
| `memoriser` | 16 correct / 8 wrong | 0.667 (replay 1.000, heldout 0.333, gap +0.667) |
| `bluffer` | 8 correct / 16 wrong | 0.333 (gap 0.000) |

Ground truth is never marked wrong; silence is never paid. Combined with
`injective: true`, no answer other than the true frame can be marked `correct`.

### Verdicts, all identical across the five items tested

| answer shape | verdict | fair? |
|---|---|---|
| exact grid, bare | `correct` | yes |
| `{"frame_after": g}` / `{"frame": g}` / `{"after": g}` | `correct` | yes |
| double-wrapped `{"frame_after": {"frame_after": g}}` | `correct` | lenient, fine |
| tuple-of-tuples | `correct` | yes |
| `{"frame_after": g, "note": "hi"}` | `correct` | yes |
| `{"abstain": false, "frame_after": g}` | `correct` | yes |
| transposed (9x7) | `wrong`, `shape_ok:false, cells_wrong:-1` | yes |
| one cell changed | `wrong`, `cells_wrong:1` | yes |
| short grid (6 rows) | `wrong`, `shape_ok:false` | yes |
| ragged row | `wrong`, "not a well-formed frame" | yes |
| colour `9` (outside palette) | `wrong`, "not a well-formed frame" | yes |
| all-zero grid (A0's `{0,2,4,8}` habit) | `wrong`, `cells_wrong:41` | yes |
| `{"abstain": true}` | `abstained` | yes |
| `"abstain"` (bare string) | `abstained` | yes |
| `{"abstain": true, "frame_after": <correct>}` | `abstained` | defensible (abstain wins) |
| `null` | `unanswered` | yes |
| `[]` | `wrong` | defensible |
| **`{}`** | **`wrong`** | **no — see below** |
| **cells as strings `"6"`** | **`wrong`** | **arguably no** |
| **cells as floats `6.0`** | **`wrong`** | **arguably no** |
| booleans | `wrong` | yes (documented at `rubrics_heldout.py:104`) |
| JSON string of the grid | `wrong` | defensible |
| input frame (bluffer) | `wrong` where the frame moves, `correct` where it doesn't | yes |

### The three arguable mismarks

**(a) `{}` scores `wrong`; `null` and an omitted key score `unanswered`.**
`grade_frame_exact:138` special-cases `None`, and `mark()` (`exam/grading/mark.py:51`)
emits `unanswered` for a missing key — but an empty dict falls through
`_is_abstention` (`:115`) and `_as_frame` (`:75`) and lands on
`wrong / "answer is not a well-formed frame"` (`:151`). A fair examiner would
call `{}` what it is: nothing submitted, i.e. `unanswered`. Points are unaffected
(all three are zero) but the `unanswered` count in `axes()`
(`heldout_worldgen.py:343`) is the statistic that reports "this examinee had
nothing to hand in", and it silently misses an examinee whose harness emits `{}`
per item rather than omitting the key.

**(b) A correct prediction written with string cells is marked `wrong`.**
`_as_frame:104` requires `isinstance(cell, int)`. The rubric's own stated
principle, three lines above at `:80-83`, is that accepting two wrappers is "a
decision about what is being measured — an examinee that predicts the world
correctly and wraps it differently has not made a prediction error, and a rubric
that scored it as one would be marking JSON conventions." `[["1","1",...]]` is the
same case one level down: the examinee has named the world exactly right and is
marked as having got the physics wrong. A fair examiner would coerce a cell that
is an exact decimal integer (`"6"`, `6.0`) and reject anything else.

**(c) Malformed and mispredicted are the same verdict.** Every row above marked
"not a well-formed frame" is reported as `wrong`, indistinguishable in `axes()`
from a genuine physics error; only `detail.why` separates them, and no axis reads
it. A report on this world cannot tell "cannot emit JSON" from "has no theory of
the door". Suggest a fourth verdict or an axis counting `detail.why`.

None of these three changes a single mark on this paper's four synthetic
examinees, and none of them is a defect in the discrimination instrument. They
are marker fairness issues that will bite the first real examinee whose output
format is not hand-tuned to this rubric.

**No case was found where a wrong answer was paid, or a right one refused for a
reason of physics.**

---

## 3. A cheap examinee that beats the bluffer floor — yes, comfortably

Bluffer floor on this paper: **8/24 = 0.3333** (the 8 items whose frame does not
change). Four strategies, each reading only `item.paper` — `frame_before`,
`action`, `legend`, `grid` — and never `ground_truth.json`, never `Item.truth`,
never `raw_trace.jsonl`. All four are graded through the real
`exam.grading.mark.mark` against the real key.

| strategy | score | vs floor | `theory` residue captured | `free` | `memorised` | replay/heldout gap |
|---|---|---|---|---|---|---|
| `h0` bluffer (control) | 8/24 = 0.333 | — | 0/8 | 8/8 | 0/8 | 0.000 |
| `h1` **walker** — move the agent one cell if the target cell is the floor colour, else nothing | **16/24 = 0.667** | **+8** | **4/8** | 8/8 | 4/8 | 0.000 |
| `h2` **sokoban** — h1, plus: if the target holds any non-floor/non-wall/non-agent colour and the cell beyond it is floor, slide that sprite one cell and take its place | **20/24 = 0.833** | **+12** | **6/8** | 8/8 | 6/8 | 0.000 |
| `h4` **sokoban + switch guess** — h2, plus: stepping into a legend colour that has an `X`/`X_on` twin flips it in place and (guessing "on = open") erases every other mechanism-coloured cell | **24/24 = 1.000** | **+16** | **8/8** | 8/8 | 8/8 | 0.000 |

Per-rule, `h2` is exact on `walk` 4/4, `blocked_by_wall` 4/4, `blocked_by_block`
4/4, `push` 4/4, `walk_through_door` 4/4 and `toggle_switch` **0/4**.

`h1` deserves a note of its own: **it scores 4/4 on `walk_through_door` without
any concept of a door.** Every `walk_through_door` transition requires the door to
be open, and `door_presence_tracks_net` renders an open door as *nothing* — cell
value `0`. So on the sheet, walking through a door is pixel-for-pixel a walk onto
floor. The `switch_door` family contributes 4 items to this paper via that rule
and none of them tests any door theory whatsoever.

`h2`'s only failures are the four `toggle_switch` items, and it fails them for the
right reason: flipping the switch at `(5,1)` also erases the door at `(3,4)`, a
cell six columns away that the action never touched. That distant coupling is the
world model, and it is the only thing on this paper that demands one.

`h4` clears it — and I am flagging it as an *honest ceiling, not an honest
strategy*. It guesses that a switch turning **on** opens what it is wired to, and
it gets all four items because **all four `toggle_switch` items on this paper flip
`0 → 1`** (verified: `-006 -007 -008 -011`, every one `bit_before=0`). Measured
against the world rather than the paper:

* on the 6 reachable `bit 1 → 0` toggles, `h4` scores **0/6** — it cannot redraw a
  door it cannot see;
* on the whole 700-transition reachable relation: `h1` 682/700, `h2` 683/700,
  `h4` 689/700.

So the paper's four toggle items all point the same way, and a strategy with a
50/50 prior on polarity is never charged for the coin flip. Two of the eight
`theory` items are the ones `h2` misses; those two are also the only two `h4`
would lose in a world declared `open_when_off`.

Every strategy above has `gap_replay_minus_heldout = 0.000` exactly. The gap axis
therefore correctly declines to call `h2` a memoriser — and equally correctly
fails to notice that `h2`, at 0.833, outranks the memoriser (0.667) while holding
no theory at all. **The gap axis and the score axis together do not separate
"learned the rules" from "applied a sokoban prior".** Only two items do.

---

## 4. Honest effective size

**The instrument says 8. The defensible number is 2, and it is thin.**

| measure | items | share |
|---|---|---|
| printed size | 24 | 1.000 |
| zero-discrimination (`free`) | 8 | 0.333 |
| instrument's `effective_size` (`theory`) | 8 | 0.333 |
| survives `h1` (a 15-line sprite-mover) | 4 | 0.167 |
| **survives `h2` (a 25-line sokoban prior)** | **2** | **0.083** |
| survives `h4` (h2 + a polarity coin flip) | 0 | 0.000 |

The two survivors are `t2-switch-push-006` and `t2-switch-push-011`, both
`toggle_switch`, both `heldout`. They are the only items on the sheet whose answer
requires knowing that a cell the action did not touch changes.

### Dead weight, by name

| rule | items | why it is dead weight here |
|---|---|---|
| `blocked_by_wall` | 4 (all `free`) | 336 of 700 transitions. "Target is the wall colour ⇒ nothing happens" is readable off the sheet from the legend. Zero discrimination by construction. |
| `blocked_by_block` | 4 (all `free`) | Frame never changes, so the bluffer has them. Contains the world's only genuine two-mechanism transition — which the sampler did not pick (§1). |
| `walk` | 4 (2 `theory`) | 329 of 700 transitions. Falls to `h1` 4/4. |
| `walk_through_door` | 4 (2 `theory`) | **Dead weight for a structural reason, and this is the finding.** An open door renders as `0`; every `walk_through_door` transition has the door open; so all four items are visually plain walks. `h1` gets 4/4 with no door concept. The paper's `switch_door` family is represented here by four items that test nothing about switches or doors. |
| `push` | 4 (2 `theory`) | Falls to a generic "sprite with floor beyond it slides" prior. `h2` 4/4, and 6/6 across the whole reachable relation. |
| `toggle_switch` | 4 (2 `theory`) | **The only load-bearing rule on this paper**, and only because the switch's effect is non-local. Even so, all four items flip in the same direction. |
| `blocked_by_door` | **0 — excluded** | 5 reachable transitions, 1 in the trace, 4 held out. `plan()` (`heldout_worldgen.py:127`) needs ≥2 on both sides, so the rule is blocked as the A0′ failure mode. This is the *only* rule in which the door is drawn and visibly stops the agent — the one rule where the `switch_door` mechanism is legible on the sheet. `h2` scores **1/5** on it. The paper excludes, on a quota technicality, the single rule that would most have punished a theory-free examinee. |

The profile's `barren_rules` names `blocked_by_block` and `blocked_by_wall`. That
is right as far as it goes, but on this world `walk_through_door` and `push` are
barren too against any examinee that is not one of the three voters, and
`walk_through_door` is barren for a reason built into the renderer rather than
into the sampling.

### Can it rank two examinees apart?

Marginally, and only in one dimension. Two examinees that differ **only** on
switch/door theory are separated by 2 items — a score difference of 0.083 on a
24-item paper, with no partial credit and no repeated trials to average.
Everything else on the sheet is settled by a sokoban prior. Two examinees that
differ on *anything but the switch–door net* are not separated at all.

Concrete recommendation, in order of value:

1. **Lower `per_class` to 1 for `blocked_by_door`, or relax the quota for it
   specifically.** It has 5 reachable transitions with 1/4 split; it is the only
   rule that renders the door and the only rule where `h2` fails badly.
2. **Balance the `toggle_switch` sample across bit directions.** All four items
   currently flip `0 → 1`; sampling one of each direction would cost nothing and
   would charge a polarity guess (`h4` drops from 24/24 to 20/24).
3. **Prefer the interaction transition when a rule is oversubscribed.** The
   `blocked_by_block` heldout pool has 3 candidates, one of which is the
   cross-family item; the hash took the other two.
4. **Add `h2` (or any sokoban prior) as a fifth calibration voter** in
   `discrimination.VOTERS`. The tool's own docstring warns that "a fourth strategy
   nobody has written could settle [a `theory` item] for free, and the taxonomy
   would not notice." On this world that fourth strategy settles 6 of the 8, and
   it is 25 lines long.

---

## 5. Things not asked for

* **`GROUND_TRUTH.md` contradicts itself on this world.** The rendered prose
  (from `worldgen/core/truth.py:252`) says "Any *non*-cascade rule reading `never
  fires` is a defect, and the build refuses to ship one" — and then the table
  ships `blocked_toggle_would_shut_door` with `never fires` and no cascade mark. It
  is not a defect: `ground_truth.json` records it as `clause: true` and
  `rule_correspondence.dormant_clauses`, an exemption `truth.py:88-96` describes at
  length. The Markdown just omits the clause exemption from the sentence, so a
  reader of the shipped artefact would conclude the world is broken. One-word fix
  in the prose at `truth.py:252`; nothing else is wrong.
* **`blocked_toggle_would_shut_door` is structurally unreachable here**, not
  merely unwitnessed: the switch is at `(5,1)` and the door at `(3,4)`, so the
  agent can never stand on the door and step into the switch in one move. The
  dormancy is geometry, and the artefact does not say so.
* **The shipped profile reproduces exactly.** `profile_world("t2-switch-push", 2)`
  serialises byte-identically to the checked-in JSON; `rubric_digest`
  `e06bdf52…1cb091` matches the live registry.
* **`unchanged_frame_share` on the sheet is `0.333333`** (`Paper.notes`), i.e. the
  bluffer floor is printed on the paper itself. An examinee that reads its own
  notes block knows exactly what fraction of items to answer "nothing happens" to.
  Harmless as a scalar, but it is answer-adjacent information on the open side.
* **All four `walk_through_door` items and all four `toggle_switch` items involve
  the same two grid cells** — `(3,4)` and `(5,1)`. Nine of the paper's 24 items are
  transitions at or adjacent to `(3,x)` in row 3. The paper is geometrically
  concentrated.

---

### Reproduction

Scratchpad (not in the repo):
`…/scratchpad/t2sp/{indep,interact,census,stress,cheap,cheap2,final}.py`.
`indep.py` reimplements the transition function from `spec.json` + the published
rule table without importing `worldgen`; everything else imports `exam.*`
read-only. No file under `worldgen/` or `exam/` was modified.
