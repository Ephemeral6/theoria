# Examiner's report — `t3-latch-maze`

Independent audit of `exam/tools/discrimination.py`'s profile for one world.
Profile under review: `exam/runs/20260728T151000Z-V7-exam-stress-fanout/worlds/t3-latch-maze.json`
(20 items, 8 free / 6 memorised / 6 theory, `effective_size: 6`, `barren_rules: [blocked_by_wall, latch_already_set]`).

**Headline.** The classification is *arithmetically true* — I reproduced all 20
items from `spec.json` with a simulator I wrote myself, and every class label is
consistent with the three voters' verdicts. But the label `theory` overclaims by
a factor of six on this world. A 30-line examinee that has never heard of a
latch, a net, a token count or a lock scores **0.950** against a bluffer floor of
**0.400** and a memoriser's **0.700**, capturing **5 of the 6 `theory` items**.
The honest effective size of this paper is **1 item**, not 6.

---

## 1. Is the classification true of this world's actual mechanics?

### Method

I did not trust `worldgen/core/world.py`. I re-implemented the transition
function and the renderer from `spec.json` plus the prose rule table in
`GROUND_TRUTH.md`, with no import of the world core, then BFS'd my own reachable
set and compared frame-for-frame.

My simulator reaches **436 states / 436 distinct frames**, matching
`ground_truth.json`'s `frame_determines_state` (`states: 436, distinct_frames:
436, injective: true`) and the "checked on 436 reachable states" stamp in
`GROUND_TRUTH.md:46-53`. Frames are injective, so no item is secretly answered
by the trace's visit to a look-alike state.

### Result: all 20 items check out

Every item's `frame_after` and `rule` tag were reproduced exactly. Not a sample —
**all twenty**: `t3-latch-maze-000` through `-019`. Per item, with the changed
cells I recomputed:

| item | rule | split | class | cells changed | changed cells |
|---|---|---|---|---|---|
| `-000` | `collect_token` | heldout | theory | 2 | (5,6) (5,7) |
| `-001` | `blocked_by_wall` | replay | free | 0 | — |
| `-002` | `walk_through_door` | replay | memorised | 2 | (4,4) (5,4) |
| `-003` | `blocked_by_wall` | heldout | free | 0 | — |
| `-004` | `walk_through_door` | heldout | theory | 2 | (4,4) (5,4) |
| `-005` | `walk_through_door` | heldout | theory | 2 | (4,4) (5,4) |
| `-006` | `walk` | heldout | theory | 2 | (6,4) (6,5) |
| `-007` | `blocked_by_wall` | heldout | free | 0 | — |
| `-008` | `collect_token` | replay | memorised | 2 | (4,1) (5,1) |
| `-009` | `latch_already_set` | replay | free | 0 | — |
| `-010` | `collect_token` | replay | memorised | 2 | (1,3) (1,4) |
| `-011` | `walk` | replay | memorised | 2 | (6,2) (6,3) |
| `-012` | `blocked_by_wall` | replay | free | 0 | — |
| `-013` | `walk` | replay | memorised | 2 | (4,1) (5,1) |
| `-014` | `walk` | heldout | theory | 2 | (6,3) (6,4) |
| `-015` | `walk_through_door` | replay | memorised | 2 | (5,4) (6,4) |
| `-016` | `latch_already_set` | replay | free | 0 | — |
| `-017` | `latch_already_set` | heldout | free | 0 | — |
| `-018` | `collect_token` | heldout | theory | **3** | (5,1) (5,8) **(6,1)** |
| `-019` | `latch_already_set` | heldout | free | 0 | — |

**No instrument defect of the kind asked about.** No `free` item changes the
frame (all 8 have zero changed cells); every `theory` and `memorised` item does.
`dead: 0` and `anomalies: []` are both correct. The `frame_changes` field agrees
with my recomputation on all 20.

### The one thing that made me get an item wrong on the first pass

`t3-latch-maze-018` is the **only non-local item in the paper**: the agent walks
from (6,1) onto the third token at (5,1), and cell **(5,8) — seven columns away —
goes from `7` (lock) to `0`**. The lock stops being *drawn* the instant the
global collected count reaches its `k=3`, exactly as a door stops being drawn
when its net matches its polarity.

**That behaviour is undocumented.** `GROUND_TRUTH.md:39-40` and the
`ground_truth.json` rule entries for `walk_through_lock` / `blocked_by_lock` say
only "the agent moves onto the lock's cell" / "nothing changes"; neither mentions
that the lock ceases to render. There is a `door_presence_tracks_net` invariant
(`GROUND_TRUTH.md:48`) and **no `lock_presence_tracks_count` counterpart** in
either the Markdown or the JSON `invariants` list. The behaviour is real — I
confirmed it holds across all 436 states — but a reader deriving the answer key
by hand from the published ground truth will get `-018` wrong, as I did. This is
a worldgen documentation gap, not an exam defect, but it matters here because
`-018` turns out to be the *only* item on this paper that a theory-free examinee
cannot get (§3).

### `latch_already_set`: inherently dead weight, not under-sampled

**Answering the specific question: it is structurally, provably barren — no
sampling regime on any world at any `per_class` can make it produce an
informative item.**

The argument is one line, and it is about the rule's consequent, not its
frequency. `GROUND_TRUTH.md:33` defines the rule as: *when the target holds a
latch whose bit is already 1, **nothing changes***. The bluffer returns the input
frame. For a rule whose consequent is "nothing changes", the input frame **is**
the truth. So `bluffer == correct` on every transition the rule will ever
produce, and `_classify` (`discrimination.py:105-114`) can only ever return
`free`. Sampling more of them samples more free marks.

This is not marginal on this world — the latch is central and the rule is well
witnessed. My census over the full reachable relation (436 states × 4 actions =
1744 transitions):

| rule | firings | of which no-op | can it ever be informative? |
|---|---|---|---|
| `walk` | 858 | 0 | yes |
| `blocked_by_wall` | 740 | **740** | **never** |
| `collect_token` | 33 | 0 | yes |
| `blocked_by_lock` | 25 | **25** | **never** |
| `latch_already_set` | **19** | **19** | **never** |
| `walk_through_door` | 18 | 0 | yes |
| `press_latch` | 12 | 0 | yes |
| `walk_through_lock` | 12 | 0 | yes |
| `blocked_by_door` | 10 | **10** | **never** |
| `blocked_by_collapsed` | 10 | **10** | **never** |
| `cross_fragile` | 7 | 0 | yes |

19 firings is ample — `blocked_by_door` and `blocked_by_collapsed` fire only 10
times each. `latch_already_set` is not starved; it is *definitionally* free.

**Generalisation for the instrument.** Five of this world's eleven rules
(`blocked_by_wall`, `blocked_by_lock`, `latch_already_set`, `blocked_by_door`,
`blocked_by_collapsed`) have "nothing changes" as their consequent and are
therefore guaranteed-barren. `discrimination.py` could compute `barren_rules`
*a priori* from the rule table instead of discovering it empirically per world:
any rule whose `then` is "nothing changes" is barren on every world, forever.
That would turn a per-world observation into a catalogue-level invariant and
would explain, rather than merely report, why `latch_already_set` shows up empty
everywhere.

**A caveat against over-correcting.** Barren ≠ worthless. Deleting the 8 free
items would hand every remaining examinee the free hint *"the frame always
changes"*. The no-op items are the control that keeps "does anything happen?" a
live question. The right conclusion is that they must not be **counted** as
paper size, not that they must be removed.

---

## 2. Does the marker misjudge anything on this world?

I imported `exam/grading/rubrics_heldout.py` and `exam/grading/mark.py` and
graded 24 crafted answers against 6 items spanning all three classes
(`-000`, `-018`, `-004` theory; `-011` memorised; `-009`, `-001` free). No file
was edited.

### Structural invariants — both hold

| examinee | verdicts | score |
|---|---|---|
| `oracle` | 20 correct, 0 wrong | 1.000 |
| `null` | **20 unanswered**, 0 correct | 0.000 |
| `memoriser` | 14 correct, 6 wrong | 0.700 |
| `bluffer` | 8 correct, 12 wrong | 0.400 |

**Silence is never paid** and **ground truth is never marked wrong**, on all 20
items. Confirmed.

### Verdicts that are right

Identical on all six probe items, so I state them once:

- exact frame, bare → `correct`; wrapped `{"frame_after": …}` → `correct`. Both
  documented shapes work. The undocumented aliases `{"frame": …}` and
  `{"after": …}` also pass (`rubrics_heldout.py:88`) — more lenient than the
  sheet promises, which is the safe direction.
- tuples instead of lists → `correct`. Right: a JSON convention, not a prediction.
- **transposed** (8×10 → 10×8) → `wrong`, `shape_ok: False`, `cells_wrong: -1`.
  Right, and the detail correctly attributes it to shape rather than content.
- **one cell changed** → `wrong`, `cells_wrong: 1`. Right — no partial credit is
  the documented and defensible design.
- **short grid** (7 of 8 rows) → `wrong`, `cells_wrong: -1`. Right.
- **ragged grid** → `wrong` (malformed). Right.
- **colour 12** (outside the palette) → `wrong` (malformed). Right.
- `{"abstain": true}` → `abstained`. Right.
- `null` → `unanswered`. Right, and distinct from `wrong` as `mark.py:9-14` intends.
- string `"abstain"` → `abstained`. Right.
- booleans in place of 0/1 → `wrong` (malformed). Right, and the explicit
  `isinstance(cell, bool)` guard at `rubrics_heldout.py:104` is a good catch —
  without it `[[True, False]]` would compare `==` equal to `[[1, 0]]`.
- `frame_before` (the bluffer's answer) → `wrong` with `cells_wrong: 2` on the
  changing items, `cells_wrong: 3` on `-018`, and `correct` on the two free
  items. Right by construction.

### Verdicts I would argue are wrong

**(a) `{"abstain": true, "frame_after": <the correct grid>}` → `abstained`, 0.0.**
`rubrics_heldout.py:144` tests `_is_abstention` before `_as_frame:149`, so an
answer that carries a correct prediction *and* an abstention flag is thrown away.
A fair examiner marks the frame: the examinee did predict, correctly, and the
flag is at worst hedging. As it stands the rubric pays 0 for a right answer.
Verified: the correct grid for `-000`, `-018`, `-004`, `-011`, `-009` and `-001`
all score `abstained`. (Control: `{"abstain": false, "frame_after": <truth>}`
scores `correct`, so it really is the flag ordering.)
Impact on this run: zero — none of the four fakes emits such an answer — but any
real examinee that hedges is silently zeroed.

**(b) `{}` → `wrong`; a missing item key → `unanswered`.**
`_as_frame` falls through to `return None` at `rubrics_heldout.py:90` for a dict
with no recognised field, so an empty submission object is graded `wrong`
(`:151`), while `mark.py:51-53` calls the *same absence* `unanswered`. Both score
0.0, so no examinee is cheated on points — but the report differs, and the
`wrong` count is what a reader treats as "predictions it got wrong". A fair
examiner calls `{}` nothing-submitted. An examinee that emits `{}` for items it
cannot do is reported as having made 20 failed predictions; one that omits the
key is reported as having made none.

**(c) Every malformed answer lands in `wrong`.**
`"cells as strings"`, ragged, out-of-palette, nested, empty-list, floats, an
unknown wrapper key `{"grid": …}`, and a JSON-encoded string of the grid all
return `wrong`. `detail.why` distinguishes them, `verdict` does not — and
`verdict` is what `discrimination.py:144` reads (`verdict == "correct"`) and what
`report.by_tag` aggregates. `VERDICTS` at `exam/model.py:233` has only four
members, so the rubric had nowhere else to put them; this is a model-level
constraint, not a rubric bug. Worth naming because a formatting failure and a
false theory are not the same finding, and downstream nothing can tell them
apart.

**(d) `[[6.0, 0.0, …]]` → `wrong` (malformed).**
Python considers the float grid `==` the truth grid; the rubric rejects it at
`rubrics_heldout.py:104` (`not isinstance(cell, int)`). Defensible — a frame of
floats is not a frame — but a JSON round-trip through any numeric pipeline emits
`6.0`, and a fair examiner would probably call that a serialisation artefact,
not a wrong prediction. Flagging it as arguable rather than as a defect; the
`bool` guard on the adjacent line is unambiguously right, this one is a judgement
call, and it is the *only* case where an answer that equals the truth by
Python's own `==` is marked wrong.

**(e) The palette guard is inert on this world.**
`_legal_cells` (`rubrics_heldout.py:59-70`) resolves to `[0,1,2,3,4,5,6,7,8,9]`
for `t3-latch-maze` — the entire ARC range, because this world uses all ten
colours. So on this world the palette check rejects nothing that the type check
would not already reject. Not a defect; a note that the guard's protection is
world-dependent and here it is zero, so no examinee can be caught inventing a
colour.

**Nothing scores `correct` that should not.** Across all 144 (item, answer)
pairs, no non-truth answer was ever graded `correct`. The marker has no false
positives on this world.

---

## 3. A cheap examinee that beats the bluffer floor

The bluffer floor here is **0.400** (8 of 20 items do not change the frame;
`paper.notes["unchanged_frame_share"] == 0.4`).

### The strategy

Reads only `item.paper`: `frame_before`, `action`, `legend`, `grid`. It never
opens `ground_truth.json`, never touches `item.truth`, never sees the key
document. Full source in this report so the claim is checkable:

```python
def strategy(sheet, enterable_names=()):
    frame  = [list(r) for r in sheet["frame_before"]]
    legend = sheet["legend"]; h, w = sheet["grid"]
    agent_c, wall_c, floor_c = legend["agent"], legend["wall"], legend["floor"]
    enterable = {floor_c} | {legend[n] for n in enterable_names if n in legend}
    pos = next((r, c) for r in range(h) for c in range(w) if frame[r][c] == agent_c)
    dr, dc = {"UP": (-1,0), "DOWN": (1,0), "LEFT": (0,-1), "RIGHT": (0,1)}[sheet["action"]]
    tgt = (pos[0] + dr, pos[1] + dc)
    if not (0 <= tgt[0] < h and 0 <= tgt[1] < w):       return sheet["frame_before"]
    if frame[tgt[0]][tgt[1]] not in enterable:          return sheet["frame_before"]
    frame[pos[0]][pos[1]] = floor_c
    frame[tgt[0]][tgt[1]] = agent_c
    return frame
```

Its entire theory is: *the thing called "agent" moves one cell; it cannot enter
the thing called "wall" or leave the board; the cell it leaves becomes "floor"*.
It has no concept of a switch, a net, a polarity, a latch, a token count, a lock,
a `k`, a fragile tile, or a cascade.

### Scores

| examinee | score | replay | heldout | **gap** | theory items captured |
|---|---|---|---|---|---|
| `bluffer` (floor) | 0.400 | 0.400 | 0.400 | +0.000 | 0 / 6 |
| `memoriser` | 0.700 | 1.000 | 0.400 | +0.600 | 0 / 6 |
| **S1** `enterable_names=()` | **0.800** | 0.800 | 0.800 | **+0.000** | **4 / 6** |
| **S2** `enterable_names=("token",)` | **0.950** | 1.000 | 0.900 | +0.100 | **5 / 6** |
| `oracle` | 1.000 | 1.000 | 1.000 | +0.000 | 6 / 6 |

**S1 uses zero world-specific tuning.** `floor=0`, `wall=1`, `agent=6` are
declared reserved across every world in `worldgen/core/types.py:40-43`, so S1
ports to the entire catalogue unchanged. It scores **0.800 — double the floor,
and 10 points above the memoriser** — capturing 4 of the 6 `theory` items
(`-004`, `-005`, `-006`, `-014`) and 4 of the 6 `memorised` items.

**S2 adds one word.** It reads the string `"token"` out of the legend that is
*printed on the sheet* and guesses that a thing so named can be walked onto.
That is legend literacy, not a world model — it still has no notion that tokens
are counted, or that the count opens anything. It scores **0.950**, missing only
`-018`.

### Why it works — three separate leaks

1. **`walk_through_door` is invisible.** A door that is passable is *undrawn*
   (`GROUND_TRUTH.md:37`), so the target cell of every `walk_through_door` item
   renders as plain floor `0`. S1 walks onto it and is right — the world's
   marquee mechanism, the switch/door net, contributes four items that are
   indistinguishable from plain `walk` on the sheet. All four
   (`-002`, `-004`, `-005`, `-015`) fall to a strategy that has never heard of a
   door. The classification calls `-004` and `-005` `theory`; they are not.
2. **`collect_token` is self-erasing.** The agent is painted last
   (`world.py:238`), so walking onto a token overwrites it. "Move the agent,
   blank the vacated cell" produces the correct 2-cell diff with no notion of
   collection. Three of four fall (`-008`, `-010`, `-000`).
3. **The no-op rules cost nothing to imitate.** "If I don't recognise the target,
   predict stasis" collects all 8 free items for free — the same marks the
   bluffer gets, kept.

### The residue: exactly one item

**`t3-latch-maze-018` is the only item on this paper that survives.** It is the
only non-local one: collecting the third token at (5,1) makes the lock at (5,8)
vanish. Getting it requires knowing that tokens are *counted*, that a lock has a
threshold `k`, that the count is global rather than per-lock, that the third
collection crosses `k=3`, and that a satisfied lock stops rendering — five facts,
none of which is on the sheet and one of which is not even in the ground truth
(§1). No generic prior produces "blank a cell seven columns away". I could get
`-018` only by hard-coding the lock's cell or the threshold, which would be
peeking, so I did not, and I report the miss.

**Honest failure disclosure:** S1 and S2 are *not* honest failures — they beat
the floor decisively. The honest failure is the reverse of what was asked: I
could not find a theory-free way to get `-018`, and that single item is the whole
of this paper's genuine difficulty.

### The gap axis is fooled too

`heldout_worldgen.py:305-309` documents `gap_replay_minus_heldout` as the
headline: *"A rule-learner is near zero. A memoriser is near one."* S1 posts a
gap of **exactly +0.000** — the perfect rule-learner signature — while holding no
rules at all. S2 posts **+0.100**. Both read as rule-learners on the paper's own
headline metric. The gap axis measures *"does this examinee behave the same on
seen and unseen transitions"*, which a strategy that ignores the trace entirely
satisfies trivially. It cannot distinguish a world model from a reflex, and on
this world it does not.

---

## 4. This world's honest effective size

### The number

| measure | value |
|---|---|
| items on the paper | 20 |
| `discrimination.py`'s `effective_size` (= `theory`) | 6 |
| items no theory-free strategy I could write gets | **1** |
| that item | `t3-latch-maze-018` |

`effective_size: 6` is not wrong by its own definition — those six items *are*
the ones the three chosen voters do not settle. It is wrong as a claim about how
many questions need a world model, and the module's own docstring
(`discrimination.py:60-67`) predicted exactly this failure mode: *"a fourth
strategy nobody has written could settle it for free, and the taxonomy would not
notice."* I wrote the fourth strategy. It settles 5 of the 6.

### Dead weight, by name

**Barren by construction (consequent is "nothing changes") — 8 items, 40% of the paper:**
- **`blocked_by_wall`** (4 items: `-001`, `-003`, `-007`, `-012`). 740 firings,
  740 no-ops. Can never be anything but `free`.
- **`latch_already_set`** (4 items: `-009`, `-016`, `-017`, `-019`). 19 firings,
  19 no-ops. Same, and *inherently* so — see §1.

Both are already named in the profile's `barren_rules`. The profile is right
about them; what it does not say is that they are barren for a structural reason
that will not change with more sampling.

**Barren in practice, though the profile calls them informative — 8 items, 40%:**
- **`walk`** (4 items: `-006`, `-011`, `-013`, `-014`) — S1 gets all four.
- **`walk_through_door`** (4 items: `-002`, `-004`, `-005`, `-015`) — S1 gets all
  four, because a passable door renders as floor. This one is the more serious
  finding: the paper labels `-004` and `-005` `theory`, and they are answered by
  a strategy that does not know doors exist.

**Genuinely load-bearing — 4 items, of which 1 is hard:**
- **`collect_token`** (`-000`, `-008`, `-010`, `-018`). Three are captured by the
  self-erasure leak; `-018` alone requires the count→lock cascade.

### The rules that would have carried real difficulty are all excluded

`plan("t3-latch-maze", 2)` blocks six of the eleven firing rules, every one for
the same reason — the *published trace* witnessed it 0 or 1 times, so the matched
quota cannot be met:

| blocked rule | in trace | held out | what it would have tested |
|---|---|---|---|
| `press_latch` | 1 | 11 | agent does **not** move while two distant cells change (switch 2→3, door 4→undrawn) — the sharpest theory item this world can produce |
| `cross_fragile` | 0 | 7 | delayed collapse: the tile changes *one frame after* the crossing |
| `walk_through_lock` | 0 | 12 | the count→threshold relation, positively |
| `blocked_by_lock` | 0 | 25 | the same relation, negatively |
| `blocked_by_door` | 1 | 9 | net/polarity, negatively |
| `blocked_by_collapsed` | 0 | 10 | tile-state monotonicity |

This is the world's real problem, and it is the one `spec.json:102` predicted in
its own notes: *"almost nothing can be seen twice"*. `press_latch` and
`cross_fragile` are stamped single-witness in `GROUND_TRUTH.md:64` — the A0′
failure mode, correctly detected and correctly refused. But the consequence is
that **the paper examines the five easiest of eleven rules and excludes all six
that would have been hard**, and three of the six exclusions
(`blocked_by_lock` 25, `walk_through_lock` 12, `blocked_by_collapsed` 10) fail
only on the *replay* side — the transitions exist in abundance, the published
trace just never walked through them. A longer or better-targeted exploration
trace would unblock them; a bigger `per_class` would not.

### Can the residue rank two examinees apart?

**No.**

- One item at 1.0 point each means the finest distinction the theory residue can
  draw is 0 or 1 — a single bit, with no confidence interval and no way to tell a
  lucky guess from a world model. `DEFAULT_PER_CLASS = 2` exists precisely so a
  rule learned can be told from a rule got right once
  (`heldout_worldgen.py:65-67`); the genuine residue here is 1, below that bar.
- Two examinees separated by this paper are, with 19/20 probability, separated by
  which of them found the "agent walks onto floor" reflex — not by which of them
  built a manual.
- The visible spread is misleading in the same direction: the range from bluffer
  (0.400) to oracle (1.000) looks like 0.600 of headroom, but 0.550 of it is
  reachable without a theory. The genuinely theory-gated headroom is **0.050**.

**What would fix it, in order of leverage:**
1. **Draw passable doors and satisfied locks.** A door and a lock that vanish
   when open make the world's two headline mechanisms invisible on the sheet, and
   `walk_through_door` collapses into `walk`. Rendering them in a distinct
   "open" colour would restore four items to genuine difficulty at a stroke.
2. **Extend `raw_trace.jsonl` to witness `press_latch` and the lock rules at
   least twice.** That alone would add 12 items across the four sharpest rules,
   including the only rule in the world where the agent does not move but the
   frame changes.
3. **Add the theory-free reflex as a fifth voter in `discrimination.py`.** S1 is
   ~15 lines, needs no world-specific tuning, and would have caught this
   automatically. A `reflex` class between `free` and `theory` would have
   reported `effective_size: 1` for this world instead of 6.

---

## Things I found that were not asked for

1. **Undocumented lock rendering (`worldgen`, not `exam`).** The lock stops being
   drawn once `k ≤ collected`. Neither `GROUND_TRUTH.md:39-40` nor
   `ground_truth.json`'s rule entries mention it, and there is no
   `lock_presence_tracks_count` invariant to match `door_presence_tracks_net`.
   Verified real over all 436 states. A hand-derived answer key would get `-018`
   wrong — I did, first time. This is also the single fact that makes `-018` the
   paper's only theory-demanding item, so the documentation gap and the paper's
   entire difficulty sit on the same undocumented line.

2. **`gap_replay_minus_heldout` cannot detect a theory-free examinee** — S1 posts
   +0.000, the documented rule-learner signature, holding no rules
   (`heldout_worldgen.py:305-309`). The metric measures split-invariance, not
   understanding. It works as an anti-memorisation detector and should not be
   quoted as evidence of a world model.

3. **Misnamed variable in `axes()`.** `heldout_worldgen.py:332-334` binds
   `unchanged = sum(1 for entry in key_doc["items"] if ... frame_after is not
   None)` — that counts every item with a truth frame (20 here), not the
   unchanged ones (8). It is emitted as `axes["items"]`, so the *output* is
   correct; only the name is wrong, and the real unchanged share is already
   published correctly as `notes["unchanged_frame_share"] = 0.4`. Harmless today,
   a trap for whoever reuses the variable.

4. **`blocked_toggle_would_shut_door` never fires here** and is correctly marked
   `never fires` / `clause: true` in the ground truth — it is a guard clause, not
   a rule. Consistent with `GROUND_TRUTH.md:26`; no defect. Noting it so the
   count reconciles: 11 rules fire, 12 are declared.

5. **`discrimination.py` could derive `barren_rules` a priori.** Any rule whose
   `then` is "nothing changes" is barren on every world at every `per_class`, by
   the one-line argument in §1. Five of this world's eleven rules qualify.
   Computing it from the rule table would turn a per-world empirical observation
   into a catalogue invariant, and would answer "is this rule dead or merely
   under-sampled?" without needing an examiner.

---

## Provenance

- Profile audited: `exam/runs/20260728T151000Z-V7-exam-stress-fanout/worlds/t3-latch-maze.json`
- Paper: `v2-heldout-t3-latch-maze`, `per_class=2`, rubric digest
  `e06bdf52e6f5e100008960582dcd931f06d9242bb1fb02edc01b4e81d71cb091`
- Sources read: `worldgen/out/worlds/t3-latch-maze/{spec.json, ground_truth.json,
  GROUND_TRUTH.md, raw_trace.jsonl}`, `exam/papers/heldout_worldgen.py`,
  `exam/papers/worldgen_port.py`, `exam/grading/rubrics_heldout.py`,
  `exam/grading/mark.py`, `exam/model.py`, `exam/tools/discrimination.py`,
  `worldgen/core/{world.py, types.py}`
- Method: independent re-implementation of the transition function and renderer
  from `spec.json` + prose, own BFS (436 states, 1744 transitions), frame-for-frame
  comparison against all 20 items; 144 crafted (item, answer) pairs through
  `grade_frame_exact`; four calibration fakes plus two theory-free strategies
  through `mark`.
- No file outside this report was created or modified. No `pytest` run, no `git`
  command, no network, no LLM, no contact with `arc-recon/` or the sealed pile.
