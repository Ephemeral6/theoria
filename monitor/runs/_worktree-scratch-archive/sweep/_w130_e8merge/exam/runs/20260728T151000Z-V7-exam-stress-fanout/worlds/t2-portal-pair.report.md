# Examiner's report — `t2-portal-pair`

Independent audit of the discrimination profile at
`exam/runs/20260728T151000Z-V7-exam-stress-fanout/worlds/t2-portal-pair.json`
(paper `v2-heldout-t2-portal-pair`, `per_class=2`, 8 items, rubric digest
`e06bdf52…1cb091` — re-computed live and it matches, so the profile is current).

Not to be confused with the sibling world `t2-portal-paired`. Nothing in this
report was read from, or written to, that world.

Read-only throughout: no source file was edited, no `git` command run, no test
suite invoked, no network touched. The only file created is this one.

---

## Headline

**The classification is correct on all 8 items and the marker has no scoring
defect — but the paper does not examine this world.** Every one of the 8 items
is settled by a 25-line strategy that never forms a portal theory: it reads the
frame, the action and the legend, moves the agent token one cell unless the
target shows the wall colour, and stops. It scores **8/8**, capturing **2 of 2**
of the items the instrument calls `theory`.

The reason is a single number. `teleport_twoway` fires 6 times in the reachable
relation; the published trace already contains **5** of them, leaving **1**
held out. The matched-quota test
(`exam/papers/heldout_worldgen.py:127-129`, mirrored at
`exam/papers/worldgen_port.py:262`) needs `per_class=2` on both sides, so the
rule is dropped — and with it the only mechanic in the world that is not a maze.
The paper called `t2-portal-pair` contains no portal.

---

## Q1 — Is the classification true of this world's actual mechanics?

### Method

I transcribed the rule table from `GROUND_TRUTH.md` into an independent stepper
that reads `spec.json` only (`layout`, `entities`, agent start) and never
imports `worldgen/core/world.py`. For each item I located the agent in
`frame_before`, applied my own transition, re-rendered from scratch, and
compared against the recorded `frame_after` and `rule`.

Grid 7x9. Walls from the layout; portal mouths at `(3,1)` and `(4,7)`, both
colour 2; agent 6, floor 0, wall 1. Legend on the sheet is `{0,1,2,6}` and the
truth side carries `legal_cells = [0,1,2,6]`.

### Result — all 8 items verified, zero disagreements

| item | agent before | action | agent after (mine) | rule (mine) | rule (recorded) | frame changes | class |
|---|---|---|---|---|---|---|---|
| `t2-portal-pair-000` | (5,4) | DOWN | (5,4) | `blocked_by_wall` | `blocked_by_wall` | no | free |
| `t2-portal-pair-001` | (1,1) | RIGHT | (1,2) | `walk` | `walk` | yes | theory |
| `t2-portal-pair-002` | (1,3) | UP | (1,3) | `blocked_by_wall` | `blocked_by_wall` | no | free |
| `t2-portal-pair-003` | (5,5) | LEFT | (5,4) | `walk` | `walk` | yes | memorised |
| `t2-portal-pair-004` | (1,3) | RIGHT | (1,4) | `walk` | `walk` | yes | theory |
| `t2-portal-pair-005` | (4,6) | DOWN | (4,6) | `blocked_by_wall` | `blocked_by_wall` | no | free |
| `t2-portal-pair-006` | (3,6) | LEFT | (3,6) | `blocked_by_wall` | `blocked_by_wall` | no | free |
| `t2-portal-pair-007` | (1,1) | DOWN | (2,1) | `walk` | `walk` | yes | memorised |

Frame match and rule match on 8/8. Spot detail: `-000` DOWN from (5,4) targets
(6,4), row 6 is `#########`, so blocked; `-006` LEFT from (3,6) targets (3,5),
layout row 3 is `#...##..#`, col 5 is `#`, so blocked; `-007` DOWN from (1,1)
targets (2,1), layout row 2 is `#.####..#`, col 1 is `.`, and no mechanism claims
it, so `walk` — that is step 1 of the world's optimal plan `DOWN DOWN DOWN`.

### The two consistency checks you asked for

* **Does any `free` item change the frame?** No. All 4 `free` items
  (`-000`, `-002`, `-005`, `-006`) have `frame_after == frame_before`, all four
  are `blocked_by_wall`, and all four are correctly recorded
  `frame_changes: false`.
* **Does any `theory` item leave the frame static?** No. Both `theory` items
  (`-001`, `-004`) move the agent one cell. Both `memorised` items (`-003`,
  `-007`) do too.

**No instrument defect found in the classification.** `_classify`
(`exam/tools/discrimination.py:95-114`) reports no anomaly and none is warranted:
the four reachable triples are the four that occur.

### Is the held-out half determined by the replay half? — yes, 55/56

The world has 24 reachable states and, because state is exactly the agent cell,
24 distinct frames (`frame_determines_state.injective = true`). That gives
**96 state-action pairs**; the published trace covers **40**, leaving **56** held
out. The trace's 41 frames visit only **14 of the 24** agent cells, never
reaching `(1,2) (1,3) (1,4) (1,6) (1,7) (2,6) (2,7) (3,3) (3,6) (3,7)` — so the
held-out items really are drawn from unvisited board, and items `-001`, `-002`,
`-004`, `-006` all sit on cells the trace never entered. That part is honest.

But *unvisited* is not *unpredictable*. A portal-blind model —
"the agent moves one cell along the action unless the target is a wall or out of
bounds" — reproduces:

* **55 of 56 held-out transitions (98.2%)**, and
* 35 of 40 in-trace transitions (87.5%).

The single held-out transition it misses is

    agent (3,7) --DOWN--> target (4,7) is a portal mouth --> agent (3,1)

which is the one and only held-out `teleport_twoway`. **The entire theoretical
content of the held-out half of this 24-state world is one transition, and the
quota rule excludes it from the paper.**

---

## Q2 — Does the marker misjudge anything on this world?

54 probes across a changing item (`-004`, `theory`) and a static item (`-000`,
`free`), by importing `exam.grading.rubrics_heldout.grade_frame_exact` directly.
The rubric was not edited.

### Verdicts that are right

| answer | verdict | fair? |
|---|---|---|
| correct grid, bare | `correct` 1.0 | yes |
| correct grid, `{"frame_after": …}` | `correct` 1.0 | yes |
| correct grid, tuples instead of lists | `correct` 1.0 | yes |
| transposed (9x7) | `wrong` 0.0, `shape_ok:false, cells_wrong:-1` | yes — a 9x7 answer is not a 7x9 frame |
| one cell changed | `wrong` 0.0, `cells_wrong:1` | yes — no partial credit is the stated design |
| short grid (6 rows of 9) | `wrong` 0.0, `shape_ok:false` | yes |
| ragged (one row short) | `wrong` 0.0, "not a well-formed frame" | yes |
| `1x1` grid `[[0]]` | `wrong` 0.0 | yes |
| grid with an empty trailing row | `wrong` 0.0 | yes |
| colour **3** (in no palette) | `wrong` 0.0 | yes |
| colour **4** or **8** (in the A0 default `{0,2,4,8}`, *not* in this world's `{0,1,2,6}`) | `wrong` 0.0 | yes — confirms `_legal_cells` (`rubrics_heldout.py:59`) is reading this world's own palette off the truth side, not the hardcoded A0 constant at `:56` |
| one cell `True` | `wrong` 0.0 | yes — the `isinstance(cell, bool)` guard at `:104` works |
| `{"abstain": true}` | `abstained` 0.0 | yes |
| string `"abstain"` | `abstained` 0.0 | yes |
| string `"I have no idea"` | `wrong` 0.0 | acceptable — not in `_is_abstention`'s list (`:115-121`) |
| `null` | `unanswered` 0.0 | yes |
| the input frame, on `-004` | `wrong`, `cells_wrong:2` | yes |
| the input frame, on `-000` | `correct` 1.0 | yes by construction — this is the free mark, not a marker fault |

### Four cases where the verdict is arguably wrong

**(a) `{}` and `[]` are marked `wrong`; `null` is marked `unanswered`.**
Three ways of submitting nothing, two different verdicts. `grade_frame_exact`
(`rubrics_heldout.py:138-142`) special-cases `None` as "nothing submitted", but
an empty dict falls through `_as_frame` (`:86-90`, no recognised field → `None`)
and lands on the malformed branch at `:151`. *A fair examiner would say*: an
empty submission is an empty submission — `{}` and `[]` should be `unanswered`,
like `null`. No mark changes (all score 0), but the `wrong` / `unanswered` split
is a reported axis (`heldout_worldgen.py:342-343`) and this quietly moves an
examinee's blanks into its error count.

**(b) `{"abstain": true, "frame_after": <the correct grid>}` is `abstained`,
0.0.** `_is_abstention` is consulted at `:144`, before `_as_frame` at `:149`, so
a declared abstention beats a correct answer sitting in the same object.
Defensible as "you said you did not know", but *a fair examiner would probably
say* the examinee produced the right frame and should be `correct`, or at
minimum that the rubric should refuse the contradiction explicitly rather than
silently discard a scoring answer. (`{"abstain": false, "frame_after": …}`
scores `correct` 1.0, so the flag alone decides it.)

**(c) A correctly predicted frame serialised as strings or floats is
indistinguishable from a wrong prediction.** `[["1","1",…]]` and `[[1.0,…]]`
both return `wrong` 0.0 with `why: "answer is not a well-formed frame"`. There
is no `malformed` verdict — `VERDICTS` is
`('correct','wrong','abstained','unanswered')` — so the only thing separating
"got the world wrong" from "got the world right and typed it as `"6"`" is a key
inside `detail`. The rubric's own docstring (`rubrics_heldout.py:51-55`) worries
about exactly this misreading and then folds the two together anyway. *A fair
examiner would say*: a formatting failure is a fifth outcome, not a wrong
prediction. On this world it changes no mark, but it does mean `_classify`
(`discrimination.py:105`) can call an item `theory` on the strength of a
serialisation slip.

**(d) `_as_frame` accepts undocumented wrappers and unbounded nesting.**
`{"frame": …}` and `{"after": …}` are accepted (`:88`) although the paper's
instructions promise only a bare grid or `{"frame_after": …}`
(`heldout_worldgen.py:213-218`); and `{"frame_after": {"frame_after": {…}}}`
recurses to `correct` with no depth cap. This errs toward leniency, so no
examinee is harmed — but the marker is more permissive than the contract the
sheet published, which is worth knowing before anyone quotes the sheet as the
spec.

None of (a)–(d) changes a single mark on this world's 8 items.

### The two structural invariants — both hold

| examinee | score | verdict tally | `gap_replay_minus_heldout` |
|---|---|---|---|
| `oracle` | 8.0 / 8 | `{"correct": 8}` | 0.0 |
| `null` | 0.0 / 8 | `{"unanswered": 8}` | 0.0 |
| `memoriser` | 6.0 / 8 | `{"correct": 6, "wrong": 2}` | 0.5 |
| `bluffer` | 4.0 / 8 | `{"correct": 4, "wrong": 4}` | 0.0 |

* **Silence is never paid.** `null` returns `{}` as its whole answers dict
  (`heldout_worldgen.py:280`), every item id misses the lookup in `mark`
  (`exam/grading/mark.py:51-52`), and all 8 come back `unanswered`. Never
  `correct`, anywhere.
* **Ground truth is never marked wrong.** `oracle` is `correct` on 8/8, with
  zero `wrong` and zero `abstained`.

---

## Q3 — A cheap examinee that beats the bluffer floor. It does, completely.

**Bluffer floor: 4/8 = 0.500** (the 4 `blocked_by_wall` items, which are the 4
items whose frame does not change).

### The strategy: `sheet-walker`

Inputs are `item.paper` only — `frame_before`, `action`, `legend`, `grid`.
It never opens `ground_truth.json`, never reads `item.truth`, and never sees
another item's answer:

1. Find the cell holding `legend["agent"]`.
2. Step one cell along the action.
3. If that cell is out of bounds, or holds `legend["wall"]`, return the input
   frame unchanged.
4. Otherwise paint the vacated cell `legend["floor"]` and the target
   `legend["agent"]`.

Nothing in it knows this world. "Walls block, agents move one step" is generic
grid-world prior, and the colour names come off the legend that is printed on
the sheet.

### Score

| | score | replay | heldout | gap | free | memorised | theory |
|---|---|---|---|---|---|---|---|
| bluffer | 4/8 = 0.500 | — | — | 0.0 | 4/4 | 0/2 | 0/2 |
| memoriser | 6/8 = 0.750 | 1.0 | 0.5 | 0.5 | 4/4 | 2/2 | 0/2 |
| **sheet-walker** | **8/8 = 1.000** | **1.0** | **1.0** | **0.0** | 4/4 | 2/2 | **2/2** |
| oracle | 8/8 = 1.000 | 1.0 | 1.0 | 0.0 | 4/4 | 2/2 | 2/2 |

It beats the floor by **+0.500** and captures **100% (2/2) of the `theory`
residue**. On this paper it is indistinguishable from the oracle — same score,
same per-item verdicts, same zero gap.

A stricter variant (`sheet-walker+`, which abstains whenever the target cell
shows a colour that is neither floor nor wall — i.e. a token it has no theory
for) also scores **8/8**, because **no item on this paper ever puts a
non-floor, non-wall cell in the agent's path**. That is the cleanest single
statement of the problem: an examinee that explicitly refuses to guess at
unexplained mechanisms is never once asked to.

### Where the strategy does break — off the paper

Over all 96 reachable state-action pairs it scores 84/96:

| rule | plain | background-aware |
|---|---|---|
| `blocked_by_wall` | 44/44 | 44/44 |
| `walk` | 40/46 | **46/46** |
| `teleport_twoway` | **0/6** | **0/6** |
| total | 84/96 | 90/96 |

The 6 `walk` misses are all the agent stepping *off* a portal mouth — from
`(3,1)` UP/DOWN/RIGHT and `(4,7)` UP/DOWN/LEFT — where the vacated cell must be
repainted 2, not 0. That is a sheet-side limitation, not a theory one, and it
vanishes if the strategy reconstructs the static background by taking the
non-agent value of each cell across the frames it has seen (still no ground
truth). What does **not** vanish is `teleport_twoway`: **0/6, both before and
after**. Portals are the only thing on this board that a portal-blind examinee
cannot fake — and the paper contains none of them.

---

## Q4 — This world's honest effective size

### Zero.

The profile reports `effective_size: 2`. Against the three synthetic voters that
is right. Against a fourth strategy that takes ten minutes to write and reads
nothing but the sheet, it is **0**: no item on
`v2-heldout-t2-portal-pair` requires a world model. This is precisely the limit
the instrument's own docstring names at `discrimination.py:60-67` — "a fourth
strategy nobody has written could settle it for free, and the taxonomy would not
notice." Here is that strategy, on this world, with numbers.

### The rules, by name

| rule | reachable firings | in trace | held out | in paper | verdict |
|---|---|---|---|---|---|
| `blocked_by_wall` | 44 | — | — | 4 items, all `free` | **dead weight.** Correctly flagged `barren_rules: ["blocked_by_wall"]`. It is the identity transition; the bluffer has it for nothing. Half the paper. |
| `walk` | 46 | — | — | 4 items (2 `memorised`, 2 `theory`) | **dead weight in practice.** It separates the memoriser from the bluffer, so the instrument scores it informative — but it is one step in a named direction on open floor, which is the first thing any generic strategy does. `sheet-walker` takes 4/4. |
| `teleport_twoway` | 6 | 5 | **1** | **0 items** | **the only rule with real content, and it is excluded.** Blocked by `heldout_worldgen.py:127-129`: 1 held-out witness < `per_class=2`. `plan()` reports it as "every reachable transition of this rule is already in the trace". |
| `blocked_portal_exit` | 0 | 0 | 0 | 0 | declared but never fires — `ground_truth.json` lists it under `dormant_clauses`, and `GROUND_TRUTH.md` marks it `never fires`. Correctly not a paper defect: it is a `clause`, not a standalone rule. |

The spec's own note — "Two mouths, same colour, and nothing in the palette says
they are linked — the pairing has to be induced from behaviour" — describes the
one question this world was built to ask. The paper does not ask it.

### Is the residue large enough to rank two examinees apart?

No, on two independent counts:

1. **Content.** `theory = 2`, and both are plain `walk` steps that a theory-free
   strategy answers. The ranking-relevant residue is empty.
2. **Statistics.** Even taking the profile's own `theory = 2` at face value, two
   binary items cannot separate two examinees at any usable confidence. A gap of
   0.5 between memoriser and bluffer rests on 2 items each side of the split.

### The concrete fix, measured

Dropping to `per_class=1` admits `teleport_twoway` and changes the answer.
The paper becomes 6 items across all three firing rules, and the
background-aware sheet-walker — the strongest theory-free examinee I could build
— scores **4/6**, missing exactly the two portal items:

| item (per_class=1 paper) | class | rule | split | sheet-walker |
|---|---|---|---|---|
| `t2-portal-pair-000` | memorised | `teleport_twoway` | replay | **wrong** |
| `t2-portal-pair-001` | free | `blocked_by_wall` | replay | correct |
| `t2-portal-pair-002` | free | `blocked_by_wall` | heldout | correct |
| `t2-portal-pair-003` | memorised | `walk` | replay | correct |
| `t2-portal-pair-004` | theory | `walk` | heldout | correct |
| `t2-portal-pair-005` | **theory** | **`teleport_twoway`** | **heldout** | **wrong** |

So `per_class=1` has an honest effective size of **1** against a fourth
strategy, versus **0** at `per_class=2`. A smaller paper that is worth one mark
beats a larger paper that is worth none.

I am not recommending `per_class=1` globally — the module's argument for 2
(`heldout_worldgen.py:65-67`: two is the smallest number that distinguishes a
learned rule from a lucky one) is sound, and lowering it everywhere would weaken
the worlds that do carry a residue. The finding is narrower and sharper: **the
quota threshold and the trace budget are in conflict on this world, and the
trace is the cheaper thing to change.** `coverage.json` records the trace
witnessing `teleport_twoway` 5 times out of 6; a trace budget that stopped at 4
would leave 2 held out and the rule would qualify at `per_class=2`. The paper's
size is being decided by how enthusiastically the explorer walked into the
portal.

---

## Things you did not ask about

1. **`coverage.json` already contained the warning.** It records
   `rules_never_witnessed: {teleport_twoway: 1}` against
   `rules_witnessed: {teleport_twoway: 5}` — the one-remaining-witness fact that
   costs this world its only real rule. Nothing in the exam pipeline reads that
   ratio, and `plan()`'s message for the blocked rule ("every reachable
   transition of this rule is already in the trace") states the symptom without
   flagging that a *near-total* trace is as damaging as a sparse one. Worth a
   near-miss warning at 1 held-out witness.

2. **`barren_rules` under-reports.** `_world_summary`
   (`discrimination.py:195-196`) calls a rule barren when it produced no
   `theory` or `memorised` item. A rule the paper never got to carry an item at
   all is invisible to that test — `teleport_twoway` appears nowhere in
   `by_rule`, so a reader of the profile cannot tell this world has a third
   rule. Suggest carrying `plan()["blocked_rules"]` through into the per-world
   profile; it is one field and it would have made this the first thing anyone
   noticed.

3. **`gap_replay_minus_heldout` reads 0.0 for both the bluffer and a perfect
   examinee.** The headline axis is the difference of two means, so it cannot
   tell "learned the rules" from "there was nothing to learn". On this world the
   bluffer and the oracle both post gap 0.0 at scores of 0.500 and 1.000. The
   gap is only interpretable next to the score, and the discrimination profile
   does not carry the score. (This is a general point, but it bites hardest on
   worlds like this one where the free share is 0.5.)

4. **`per_class=2` is the binding constraint, not the item ceiling.**
   `MAX_ITEMS = 96` never engages here — the world offers 8 items where it could
   offer 12. The refusal path everyone worries about (`build_for` raising on
   infeasible worlds) also never engages: this world is `feasible: true` and
   quietly degenerate, which is a worse failure mode than a loud refusal because
   nothing in the pipeline says so.

5. **State is the agent cell and nothing else** (24 reachable states, 24 agent
   cells, `injective: true`). Every `Item.truth.frame_after` on this paper is
   therefore recoverable from a single integer pair, and the "predict the frame
   exactly" framing carries no extra difficulty beyond "predict where the agent
   goes". That is fine for a tier-2 maze, but it means the all-or-nothing rubric
   defended at `rubrics_heldout.py:1-35` is doing no work on this world: there is
   no near-miss to reject: there are only 24 possible answers, and 39 of the 63
   cells hold the same value in every one of them (only the 24 cells the agent
   can occupy ever vary).
