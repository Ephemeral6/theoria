# Examiner's report — `t2-portal-paired`

Run `20260728T151000Z-V7-exam-stress-fanout`, base commit `8d42373`, branch
`agent/v7-exam-stress-fanout`. All work read-only; no file outside this report was
written, no `git` invoked, no network, no API, no LLM, no `arc-recon/` contact.
Paper under examination: `v2-heldout-t2-portal-paired`, `per_class=2`, 8 items,
rubric digest `e06bdf52…1cb091`.

**Headline.** The instrument's classification is *correct on every item* — I
re-derived all eight transitions from `spec.json` alone and every `class`,
`rule`, `split` and `frame_changes` field agrees. But the profile's
`effective_size: 2` is an over-estimate. A 12-line examinee that reads only the
sheet scores **8/8**, including both `theory` items. The honest effective size of
this paper is **0**. The reason is structural and is the real finding: the one
rule that distinguishes this world from every other world in the catalogue,
`teleport_paired`, **is not on the paper at all**.

---

## 1. Is the classification true of this world's actual mechanics?

### 1.1 Method

I wrote an independent transition function from `spec.json` and the rule table in
`GROUND_TRUTH.md` — bounds/wall test, then paired-portal landing
(`partner + delta`), then walk — and an independent renderer (walls `1`, both
mouths `2`, agent `6` painted last). I did **not** call `GridWorld`. For each of
the 8 items I checked seven predicates: that `frame_before` re-renders from the
spec, that my `frame_after` equals the recorded one, that my rule name equals the
recorded one, that `frame_changes` matches, that `free ⇒ frame unchanged`, that
`theory ⇒ frame changed`, and that the `replay`/`heldout` tag agrees with actual
membership in `raw_trace.jsonl`. For the four `replay` items I additionally
checked the recorded `frame_after` against the literal next line of the trace.

### 1.2 Result — all 8 items check out

| item | action | agent before → after | rule (mine == recorded) | split | class | verdict |
|---|---|---|---|---|---|---|
| `t2-portal-paired-000` | RIGHT | (1,1) → (1,2) | `walk` | heldout | theory | OK |
| `t2-portal-paired-001` | UP | (1,3) → (1,3) | `blocked_by_wall` | heldout | free | OK |
| `t2-portal-paired-002` | LEFT | (5,7) → (5,7) | `blocked_by_wall` | replay | free | OK |
| `t2-portal-paired-003` | RIGHT | (1,3) → (1,4) | `walk` | heldout | theory | OK |
| `t2-portal-paired-004` | LEFT | (1,1) → (1,1) | `blocked_by_wall` | replay | free | OK |
| `t2-portal-paired-005` | UP | (1,4) → (1,4) | `blocked_by_wall` | heldout | free | OK |
| `t2-portal-paired-006` | DOWN | (1,1) → (2,1) | `walk` | replay | memorised | OK |
| `t2-portal-paired-007` | UP | (2,1) → (1,1) | `walk` | replay | memorised | OK |

No `free` item changes the frame (all four are `blocked_by_wall`, target is a `#`
in `spec.json["layout"]`: (0,3), (5,6), (1,0), (0,4) respectively). Both `theory`
items change the frame. `dead` count is 0, anomalies 0. Replay items 002/004/006/007
match trace lines t=3, t=9, t=0→1 and t=8→9 byte for byte.

**No defect in `exam/tools/discrimination.py` found on this world.** `_classify`
(`discrimination.py:95-114`) and the `frame_changes` computation
(`discrimination.py:149`) are faithful here.

I also confirmed the world's defining mechanic by hand, since the paper never
tests it: from (2,1) `DOWN` the target (3,1) is a mouth; the partner is (4,7);
one step `DOWN` beyond the partner is (5,7), free — so the agent lands on (5,7),
the goal (`raw_trace.jsonl` t=1→t=2). From (5,7) `UP` the target (4,7) is a
mouth, partner (3,1), one step `UP` beyond is (2,1) — lands (2,1) (t=5→t=6).
That is genuinely `paired` and not `twoway`: the landing cell depends on the
direction of travel. It is correct, and it is unexamined.

### 1.3 Can a paper be built on 6 states at all? Numbers first

The reachable set is 6 states — I re-ran `GridWorld.reachable()`: agent at
(1,1), (1,2), (1,3), (1,4), (2,1), (5,7). The layout has **24 non-wall cells**;
**18 of them (75%) are unreachable decoration**. The whole right-hand chamber
(rows 1–5, cols 6–7) is reachable only at (5,7), and only through the portal.

6 states × 4 actions = **24 reachable transitions**, of which 10 are in the
published trace (`evidence_index` returns 10 keys) and 14 are held out:

| rule | reachable transitions | in trace | held out | on the paper |
|---|---|---|---|---|
| `blocked_by_wall` | 14 | 6 | 8 | 4 items (all `free`) |
| `walk` | 8 | 2 | 6 | 4 items (2 `memorised`, 2 `theory`) |
| `teleport_paired` | 2 | 2 | **0** | **excluded** |
| `blocked_portal_exit` | 0 | 0 | 0 | never fires (dormant clause) |

`heldout_worldgen.plan` (`exam/papers/heldout_worldgen.py:127-129`) requires
`per_class` witnesses on *both* sides. `teleport_paired` has 2 in-trace and 0
held-out, so it is blocked with the reason *"every reachable transition of this
rule is already in the trace"*. The paper is therefore feasible only in the
formal sense: it clears the ≥2-usable-rules bar with `walk` and
`blocked_by_wall`, the two rules every world in the catalogue shares. **Nothing
portal-shaped is asked.**

### 1.4 Is the held-out half fully determined by the replay half?

**Yes, completely.** Every one of the 14 held-out transitions is either
`walk`-onto-floor or `blocked_by_wall`, and the trace witnesses both: `walk` at
(1,1)`DOWN` and (2,1)`UP`, `blocked_by_wall` six times. No held-out transition
exercises a mechanism the trace does not already display, because the only such
mechanism — the portal — has *zero* held-out transitions. The generalisation
required to go from replay to held-out is "the same two rules, at four fresh
agent positions in an otherwise empty corridor". That is positional
generalisation, not theory. `gap_replay_minus_heldout`, the headline this
question type exists to produce (`heldout_worldgen.py:309-311`), is measuring
almost nothing on this world; my cheap examinee scores a gap of exactly 0.0.

The `per_class=2` quota is also fully saturating: `walk` has exactly 2 in-trace
transitions, so its replay half is *all* of the walk evidence, not a sample.

---

## 2. Does the marker misjudge anything on this world?

I imported `exam.grading.rubrics_heldout.grade_frame_exact` and called it
directly on items `-000` (theory, frame changes), `-001` (free, frame static) and
`-006` (memorised, replay). The rubric was not edited. Verdicts were identical
across all three items in every case, so one table suffices.

### 2.1 Structural invariants — both hold

| invariant | result |
|---|---|
| silence is never paid | `null` examinee: 0.0/8, **8× `unanswered`, 0 `correct`** |
| ground truth is never marked wrong | `oracle`: 8.0/8, **8× `correct`, 0 `wrong`** |

Baselines for reference: `memoriser` 6.0/8 (2 wrong — exactly the 2 theory
items), `bluffer` 4.0/8. Bluffer floor = 4/8 = **0.500**.

### 2.2 Full stress table

| answer form | verdict | fair? |
|---|---|---|
| bare correct grid | `correct` | yes |
| `{"frame_after": grid}` | `correct` | yes |
| `{"frame": grid}` / `{"after": grid}` | `correct` | lenient, undocumented (see 2.3a) |
| `{"frame_after": {"frame_after": grid}}` | `correct` | over-lenient (see 2.3a) |
| tuple-of-tuples | `correct` | yes |
| transposed (9×7) | `wrong`, `shape_ok=False` | yes |
| one cell changed | `wrong`, `cells_wrong=1` | yes |
| short (last row dropped) | `wrong`, `shape_ok=False` | yes |
| extra row appended | `wrong`, `shape_ok=False` | yes |
| ragged (one short row) | `wrong`, "not a well-formed frame" | yes |
| colour outside palette (`3`) | `wrong`, "not a well-formed frame" | yes |
| colour `8` (in A0 default palette, not this world's) | `wrong`, "not a well-formed frame" | yes — `legal_cells` `[0,1,2,6]` is correctly world-specific |
| booleans instead of ints | `wrong`, "not a well-formed frame" | yes (`rubrics_heldout.py:104`, deliberate) |
| all-zero grid | `wrong`, `cells_wrong=42` | yes |
| two agents / no agent | `wrong`, `cells_wrong=1` | yes |
| **strings instead of ints** | `wrong`, "not a well-formed frame" | **arguably no — 2.3b** |
| **floats (`6.0`) instead of ints** | `wrong`, "not a well-formed frame" | **arguably no — 2.3b** |
| **JSON string of the correct grid** | `wrong`, "not a well-formed frame" | **arguably no — 2.3b** |
| `{"abstain": true}` | `abstained` | yes |
| `"abstain"` / `"unknown"` / `"i cannot tell"` | `abstained` | lenient, undocumented |
| `"IDK"` | `wrong` | defensible (closed list at `rubrics_heldout.py:119-120`) |
| `{"abstain": false}` | `wrong` | **arguably no — 2.3c** |
| **`{}` (empty dict)** | `wrong` | **arguably no — 2.3c** |
| `[]` (empty list) | `wrong` | arguably no — same family as 2.3c |
| `{"frame_after": null}` | `wrong` | arguably no — same family as 2.3c |
| `{"answer": grid}` | `wrong` | yes — not a promised wrapper |
| `null` | `unanswered` | yes (`rubrics_heldout.py:138-142`) |
| `0` (a bare int) | `wrong` | yes |

### 2.3 Where the verdict is arguably wrong

**(a) The wrapper aliases are wider than the sheet promises.** The instructions
(`heldout_worldgen.py:214-218`) promise exactly two shapes: the bare grid and
`{"frame_after": …}`. `_as_frame` (`rubrics_heldout.py:88`) also accepts `frame`
and `after`, and recurses, so `{"frame_after": {"frame_after": grid}}` marks
`correct`. This is leniency, not unfairness — nobody is penalised — but it means
the marker's accepted language is not the documented one, and two examinees who
both "followed the sheet" are not being held to the same contract as one who
guessed a synonym. A fair examiner would either document the aliases or drop
them.

**(b) The formatting/prediction asymmetry is the one substantive complaint.**
The rubric's own docstring justifies accepting both wrappers on the grounds that
*"an examinee that predicts the world correctly and wraps it differently has not
made a prediction error, and a rubric that scored it as one would be marking JSON
conventions"* (`rubrics_heldout.py:80-83`). By exactly that principle,
`[["1","1",…]]`, `[[1.0,1.0,…]]` and `"[[1,1,…]]"` — each of which encodes the
correct frame cell for cell — are also not prediction errors. The rubric marks
all three `wrong`, the same verdict a genuinely mispredicted frame receives, and
the only trace is a `detail.why` string that no aggregate reads. On this paper
that is worth up to 8 points of misattribution: a submission that got the world
completely right but emitted stringified cells (a common JSON-serialiser
outcome) reads on the report as **0/8, identical to an examinee with no theory at
all**, and would be indistinguishable from the `bluffer`'s wrong items in
`by_rule` and `gap_replay_minus_heldout`. A fair examiner would say either
"correct" (coerce, since `int("1")` and `int(6.0)` are unambiguous and the
palette check still applies) or, at minimum, return a distinct fifth verdict such
as `malformed` so that a formatting failure cannot be reported as a theory
failure. Note `VERDICTS` is enforced at `exam/grading/mark.py:56-58`, so adding
one is a deliberate change, not a slip — I am reporting the asymmetry, not
proposing the patch.

**(c) "Nothing submitted" has three spellings and two verdicts.** A missing item
key → `unanswered` (`mark.py:51-53`); an explicit `null` → `unanswered`
(`rubrics_heldout.py:138-142`); but `{}`, `[]`, `{"frame_after": null}` and
`{"abstain": false}` → `wrong`. All five are the same act — the examinee produced
no frame — yet only some of them are booked as such. Points are unaffected (all
score 0), so this is not a scoring defect; it corrupts the *bookkeeping* that the
report is for. `axes()` publishes `abstained` and `unanswered` counts
(`heldout_worldgen.py:342-343`), and an examinee whose client serialises "no
answer" as `{}` will show 0 unanswered and 8 wrong, which is the profile of an
examinee that tried and failed. A fair examiner would treat an empty container as
nothing submitted.

**(d) Not a misjudgement, but a mislabelled statistic.** In
`heldout_worldgen.axes` (`heldout_worldgen.py:332-334`) the local is named
`unchanged` but counts entries whose `frame_after` is not `None` — i.e. every
item — and it is published under the key `"items"` (`:345`). The value is right
for the key; the variable name is a leftover and reads as if the axis reported
the static-frame share. On this world both numbers happen to be quotable (8 items,
4 unchanged) and it would be easy to misread 8 as the latter.

Nothing else misjudged. In particular the world-specific palette plumbing works
exactly as `worldgen_port.legal_cells` (`worldgen_port.py:173-181`) intends:
`legal_cells` is `[0,1,2,6]` on every item, so this world's frames are accepted
and A0's hardcoded `{0,2,4,8}` (`rubrics_heldout.py:56`) never bites.

---

## 3. A cheap examinee that beats the bluffer floor — it beats the ceiling

**It scores 8.0/8 = 1.000.** Bluffer floor 0.500, memoriser 0.750, oracle 1.000.
It captures **2 of 2 (100%) of the `theory` residue**, and both `memorised`
items. `replay = 1.0`, `heldout = 1.0`, `gap_replay_minus_heldout = 0.0`.

The whole strategy, verbatim as run:

```python
DELTA = {'UP':(-1,0),'DOWN':(1,0),'LEFT':(0,-1),'RIGHT':(0,1)}

def corridor_walker(sheet):
    """Sheet-only: frame_before, action, legend, grid. No truth file, no item truth."""
    f = [list(r) for r in sheet['frame_before']]
    leg = sheet['legend']; A, W, F = leg['agent'], leg['wall'], leg['floor']
    H, Wd = sheet['grid']
    pos = next((r,c) for r in range(H) for c in range(Wd) if f[r][c] == A)
    dr, dc = DELTA[sheet['action']]
    t = (pos[0]+dr, pos[1]+dc)
    if not (0 <= t[0] < H and 0 <= t[1] < Wd) or f[t[0]][t[1]] == W:
        return [r[:] for r in f]          # target is a wall or off-grid: nothing changes
    if f[t[0]][t[1]] != F:                # some mechanism owns the target; unknown
        return [r[:] for r in f]          # (a variant returning {"abstain": true} scores the same 8/8)
    f[pos[0]][pos[1]] = F                 # vacate to floor
    f[t[0]][t[1]] = A
    return f
```

Inputs used: `item.paper['frame_before']`, `['action']`, `['legend']`, `['grid']`
— nothing else. It never opens `ground_truth.json`, never touches `item.truth`,
never reads `raw_trace.jsonl`. The heuristics are generic to grid worlds: *the
agent is the cell holding the legend's agent colour; walls block; otherwise step
one cell and leave floor behind.* It carries no portal knowledge whatever — the
third branch is an explicit admission of ignorance, and it is never taken on this
paper because no item's target cell is a portal mouth.

That last sentence is the finding. The strategy has **no world model**, does
**not** know that this world has portals, and cannot predict a single teleport —
and it still tops the paper, because the paper contains no teleport item. It
scores +0.500 over the bluffer floor and +0.250 over the memoriser.

I also ran the abstain-on-unknown variant (returns `{"abstain": true}` when the
target cell is neither floor nor wall) so that the strategy could not be accused
of guessing through a mechanism it does not model: **also 8.0/8**, zero
abstentions triggered.

---

## 4. This world's honest effective size

**Zero.**

`discrimination.py` reports `effective_size: 2`, and by its own stated contract
that is correct — it counts items that `oracle`, `memoriser` and `bluffer` settle
differently, and items `-000` and `-003` do. But the module's docstring names its
own limit precisely (`discrimination.py:60-67`): *"a fourth strategy nobody has
written could settle it for free, and the taxonomy would not notice."* This world
is that case, demonstrated rather than hypothesised. The fourth strategy is
twelve lines of `corridor_walker`, it needs no theory, and it takes both `theory`
items. **0 of 8 items on this paper require a world model.**

Two examinees cannot be ranked apart by this paper on any axis that matters. The
achievable score band above the theory-free heuristic is empty: 8/8 is reachable
without a theory, so a genuine world-modeller and a corridor-walker tie at the
top, and everything below the tie is measuring whether the examinee can find the
agent and read a legend.

### Dead weight, by name

| rule | status here | why |
|---|---|---|
| **`teleport_paired`** | **excluded from the paper** | 2 reachable transitions, **both inside the published trace**, 0 held out. Blocked by the matched-quota rule at `heldout_worldgen.py:127-129`. This is the world's entire reason for existing — `spec.json["variant_delta"]` says so — and the paper never asks about it. The two mouths are pure decoration on all 8 sheets: colour `2` sits at (3,1) and (4,7) in every `frame_before` and every `frame_after`, and the correct answer never depends on it. |
| **`blocked_portal_exit`** | never fires | Declared in `ground_truth.json["rules"]` as a clause, `rule_correspondence.dormant_clauses = ["blocked_portal_exit"]`. Zero reachable transitions: both landing cells, (5,7) and (2,1), are always free. Untestable in principle here. |
| **`blocked_by_wall`** | barren | 14 reachable transitions, 4 items, **all four `free`**. Confirmed by the profile's own `barren_rules: ["blocked_by_wall"]`. The bluffer takes all of them; so does anything that copies the input. |
| **`walk`** | the only informative rule | Produces the 2 `memorised` and 2 `theory` items. It is also the single most generic rule in the catalogue — one cell, one direction, onto floor — and is fully witnessed twice inside the trace. |

So the paper's informative residue is carried entirely by the rule that is
common to all twenty worlds, while the rule unique to this world is silently
dropped. What the profile calls a small-but-nonzero theory share is, mechanically,
`t1-walk-maze` wearing a portal costume.

### Why 6 states makes this structural, not bad luck

`teleport_paired` is excluded *because* the world is small. The portal has
exactly two reachable transitions — (2,1)`DOWN` and (5,7)`UP` — and the published
trace, doing its job of witnessing every rule for the A0′ reversibility stamp,
consumes both. Witnessing a rule and holding it out are in direct competition
when a rule has only two witnesses, and at `per_class=2` the trace wins every
time. Any world whose signature mechanism fires ≤ 3 times reachably will have
that mechanism dropped from its held-out paper. This is not a bug in
`heldout_worldgen` — refusing beats shrinking a class, and the refusal is
reported honestly in `plan()["blocked_rules"]` — but it means **feasibility is
not informativeness**, and `feasible: true` on this world is close to meaningless.

---

## 5. Things you did not ask about

**5a. The sibling `t2-portal-pair` is not merely similar — it is the same world
with one string changed, and the two papers share half their items, including
100% of the theory residue.** You invited a remark on the naming; the substance
is worse than the naming. Diffing the two `spec.json` files, every substantive
field is byte-identical — `layout`, `agent_start` `[1,1]`, `goal` `[5,7]`,
`colors`, `families`, `flags`, `tier`, and both portal mouths at `[3,1]` and
`[4,7]`. The **only** functional difference is the portal entities' `props.mode`:
`"twoway"` vs `"paired"`. The rest is metadata (`seed` 202 vs 203, `notes`,
`variant_of`, `world_id`).

Since the papers exclude the portal rule on *both* worlds (`t2-portal-pair`'s
plan blocks `teleport_twoway` with `in_trace: 5, held_out: 1`), what remains on
each is walk-and-wall over a shared layout. I compared the two papers by
`(frame_before, action, frame_after)` triple:

- **4 of 8 items are literally identical**, byte for byte:
  - `t2-portal-paired-000` == `t2-portal-pair-001` (walk, heldout) — **theory item**
  - `t2-portal-paired-003` == `t2-portal-pair-004` (walk, heldout) — **theory item**
  - `t2-portal-paired-001` == `t2-portal-pair-002` (blocked_by_wall, heldout)
  - `t2-portal-paired-006` == `t2-portal-pair-007` (walk, replay)

**Both** of this world's theory items are duplicates of the sibling's. Across the
catalogue, `t2-portal-paired` therefore contributes **zero new informative items**
even by the instrument's own generous count: an examinee that has seen
`t2-portal-pair` has already been handed the answers. If the matrix ever averages
or sums across worlds, these two worlds are double-counting shared items, and the
naming similarity is a symptom of the duplication rather than a separate cosmetic
issue.

(Reachable sets do diverge — `t2-portal-pair` has 24 states to this world's 6,
because a `twoway` portal deposits the agent on the partner mouth inside the
right-hand chamber, whereas `paired` throws it straight through to (5,7). So the
worlds are genuinely different *worlds*; it is their *papers* that collapse onto
each other once the portal rule is excluded from both.)

**5b. This world is the catalogue's smallest and it is not marginal — it is
degenerate.** 6 reachable states, 24 transitions, 18 of 24 non-wall cells
unreachable. `ground_truth.json["frame_determines_state"]` reports
`injective: true` with `distinct_frames: 6`, so at least the frame-keyed evidence
index is sound (`worldgen_port.frame_ambiguous` returns `False`) — no held-out
item is secretly answered by a colliding trace frame. That check passes; it is
the only smallness-related check that does.

**5c. The published trace is 63% redundant relative to its own coverage job.**
`raw_trace.jsonl` has 11 frames / 10 actioned transitions, but only 3 distinct
frames appear in it (agent at (1,1), (2,1), (5,7)). Six of the ten transitions
are `blocked_by_wall` no-ops on the same three states. The trace spends most of
its length re-witnessing the rule that turns out to be barren, while spending
both of the portal's only two witnesses.

**5d. `mouths_static` is vacuously satisfied here.** The invariant reads *"each of
the 2 portal mouths shows colour 2 unless the agent is standing on it"*. In this
world the agent can never stand on a mouth — `paired` mode always throws it
through — so the `unless` clause has no witness in any of the 6 states, and
colour `2` is a compile-time constant of every frame. An invariant whose escape
clause is unreachable is not being tested by the 6 states it was checked on.

---

### Reproduction

Everything above is `python -c`-scale and offline. The paper is rebuilt with
`exam.papers.heldout_worldgen.build_for("t2-portal-paired", 2)`; it is
deterministic (sha256-salted selection, no RNG, no clock), so the item ids in
this report are stable. The rubric was exercised through
`exam.grading.rubrics_heldout.grade_frame_exact` and
`exam.grading.mark.mark`; no source file was modified and `pytest` was not run.
