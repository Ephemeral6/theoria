# 级联语义 · the ruling

**Status: adjudicated, 2026-07-28, ticket S5-phase1-close (worker W-5200).**
Closes Theoria.md:301 (「一件轨迹作业」) and the `级联语义已裁决` line of the
Phase 1 验收单 (Theoria.md:305). Supersedes the assertion at
[`ACCESS_CHECK.md`](ACCESS_CHECK.md) §4 that "the environment has an internal
tick"; that sentence was an inference, not a measurement, and this file is the
measurement.

Cited by both tracks. Do not restate it in a manual — cite it.

---

## The ruling, in four lines

1. **`step` is frozen as `S → A → S`**, with `S = frames[-1]`. Not `S → A → S*`.
2. **`cascade single_frame`** for the four development-pile worlds — a
   *measured per-world finding*, with the refutation condition in §5.
3. **`theory.pddl` does not need derived predicates.** This was
   Theoria.md:301's dependent question; the answer falls out of 1 and 2.
4. **The discard is now explicit and mandatory.** A consumer that collapses a
   frame batch to `frames[-1]` must record `n_frames`. Silently dropping frames
   is the one option this ruling removes.

---

## 1 · What the multi-frame batch is *not*

The question Theoria.md:96 actually asks is whether the world has a
**自触发的 tick** — a rule set that re-fires on an intermediate state without a
fresh action. `CONTRACTS/dsl_grammar_v0.2.md:101` says the same thing in the
DSL's own words: `cascade multi_frame` means "rules re-fire until quiescence".

Theoria.md:301 then compresses this into a syllogism —
「单动作若返回多帧序列,世界即有内部 tick」 — and that syllogism is where this
item has been stuck. Theoria.md:299 itself does not endorse it: it names
**动画/内部 tick** as two candidate causes of one observation and says the API
answer settles only **half** the作业. The frame count is the observation. The
tick is the claim. They are not the same, and the repository has been carrying
the claim on the observation's evidence since INC-002a.

They are separable, and on the measurements they come apart.

## 2 · What was measured

Sources, all tracked and re-derivable: [`cascade/`](cascade/) (P-20's per-frame
probe, salvaged into this directory by S5 — see §6), `data/precheck.json`,
`data/canary_runs.jsonl`, `data/recon_ledger.jsonl`, and
`baseline-arms/out/shards/ledger.*.jsonl`, which is the only source that stores
raw grids and therefore the only one that can answer anything about frame
*content*.

**Multi-frame responses are real and the frames are genuinely different.**
Across 494 multi-frame batches (g50t 287, sk48 207), **zero** are an identical
frame repeated. P-20 established this at 25 actions; the shards confirm it at
40× the sample.

**Batch length is a function of (state, action)** — not of the game, not of the
action. ar25 is 1 frame across ~530 responses; tn36 is 1 across 263; sk48's
keyboard actions are 2 (but 58 of 265 returned 1); g50t ranges over
`{1, 7, 9, 13, 15, 17, 21, 25, 29, 32, 35, 37, 41, 49, 113}`.

**Correction worth carrying: the largest batch ever observed is 113 frames**,
one g50t `ACTION5` in `baseline-arms/out/shards/ledger.g50t.jsonl`, containing
only **10 distinct** frames. `ACCESS_CHECK.md` §4 says 7, which was the largest
this track had seen; P-20 saw 17; the shards hold 113.

### The two signatures that decide it

**(a) Plateaus quantised at exactly 4.** g50t's long batches have run-length
shapes `(4,1,1,1,1,1)` ×19, `(4,4,1,1,1,1,1)` ×6, `(4,4,4,1,1,1,1,1)` ×4,
`(4,4,4,4,1,1,1,1,1)` ×4, `(4,4,4,4,4,1,1,1,1,1)` ×3 — the same state emitted
four times, then advance. A rule set re-firing to quiescence emits each new
state **once**; it has no reason to emit one four times and then move on. A
repeat factor pinned at exactly 4 is what a renderer sampling a continuous
process at fixed cadence produces. The 113-frame batch is this taken to its
limit: 113 frames carrying 10 states.

**(b) Constant increment.** In g50t's 178 seven-frame batches, consecutive
intra-batch frames differ by a **median of 12 cells (min 12, max 25)**, while
`prev_last → frames[0]` differs by **1 cell**. Uniform motion sampled evenly.
Discrete rule applications would produce effect sizes that vary with what each
rule touches, not a constant step.

### And one structural fact about sk48

sk48's intermediate frame is **never a state the world rests in**: of 207
first-frames, **0** ever appear as the final frame of any response in the same
run. Both `frames[0]` and `frames[1]` differ from `prev_last` (median 42 and 72
cells). A cascade's intermediate states are states. This one is a transient.

### The positive control

The environment defines its **own** no-op semantics against `frames[-1]`:
across the four games, 436 single-frame responses (g50t 146, sk48 36, ar25 9,
tn36 245) returned a frame byte-identical to the previous response's last
frame. When the server means "nothing happened", what it holds fixed is the
last frame. That is the state.

## 3 · Therefore

The bursts are **render/animation frames of one transition**, not a rule-level
cascade. Nothing measured shows a rule firing on an intermediate state without
a fresh action, and two independent signatures point the other way.

So the world's transition relation is `action → single successor state`, the
successor is `frames[-1]`, and `step : S → A → S` stays total and
single-valued — which is what every consumer in this repository already does
(`theoria-arm/world/frames.py:122`, `baseline-arms/harness/bare_cc.py:269`,
`battery/adapters/ledger_jsonl.py:141`, `proxy/variants.py:288`, and five
others). The difference after this ruling is that they are doing it *because it
was adjudicated*, rather than because it was convenient.

### On D-A0-004

`cold-start-a0/DECISIONS.md:47` (D-A0-004, "one action, one frame") chose
`single_frame` for the **A0 synthetic world** and flagged it as pending the API
check. It needs **no revision**. `cascade` is a per-world fact
(`CONTRACTS/dsl_grammar_v0.2.md:335-340`), A0's world and ARC-AGI-3 are two
worlds, and the two declarations were never in conflict — the appearance of one
came from reading the API's frame *list* as a statement about A0's *rules*.
The engine-rig side reached the same place independently and with a stronger
instrument: `a0-spike/THEORIZE_LOG.md:393-424` (T-11c) adjudicated
`single_frame` on 47,040 (state, action) pairs — `multi_frame`-only wrong
27,030, `single_frame`-only wrong 0 — and did so on exactly the criterion used
here: "A0 has no action-free rule, so there is no tick to declare."

**The two tracks agree, and always did.** What needed the ruling was the ARC
side, where the frame list had been mistaken for the answer.

### On `theory.pddl` and derived predicates

Theoria.md:301 made this ruling's dependent question explicit: 「它同时决定
theory.pddl 是否需要 derived predicates」. **It does not.** Derived predicates
are how PDDL expresses facts that follow from other facts without an action —
precisely the axiom-style re-firing that `multi_frame` would need. Under
`single_frame` every effect applies at one transition, which is what
`gen_pddl.py`'s STRIPS encoding already emits. No change to the PDDL backend
is required by this ruling.

## 4 · What is frozen and what is merely ruled

These are different commitments and conflating them is how a defensible ruling
turns into an undefendable one.

| | commitment | revisable by |
|---|---|---|
| **Frozen** | `step : S → A → S`, `S = frames[-1]` | an incident, not a decision |
| **Frozen** | the ledger keeps the whole frame list plus `n_frames` (`proxy/LEDGER_FORMAT.md:85-87`) | an incident |
| **Ruled** | `cascade single_frame` for ar25 / g50t / sk48 / tn36 | the §5 refutation condition, on evidence |
| **Ruled** | no derived predicates in `theory.pddl` | follows the line above |

The ledger contract is frozen *the other way* on purpose: it stores the full
list under either ruling, so the raw evidence for overturning this ruling keeps
accumulating whether or not anyone is looking for it. A ruling that destroyed
its own refutation evidence would not be worth making.

## 5 · The refutation condition, and why it is mandatory

`cascade single_frame` is a claim about a world we have seen 25 actions of at
depth, all at level 0. It can be wrong, and if it is wrong the compiled world is
a different world **that still type-checks and still passes** — the failure mode
`monitor/inbox/20260728T035214Z-opsm-conflict-a0spike-semantics.md:49` names
(「选错了，编译出来的是另一个世界，而且会静默地通过」). A ruling with that
failure mode needs a detector, not a footnote.

**The condition.** This ruling is refuted by an observation where `frames[-1]`
is *not* predicted by applying the manual's rules once to `prev_last`, but *is*
predicted by applying them repeatedly to intermediate states until quiescence.
That is the tick, stated as something an instrument can catch.

**It is a required Phase 3 check, not an optional one.** The theorizing loop
already compares predicted against observed frames; this asks it to record, on
every mismatch, whether re-firing to quiescence would have predicted the
observation. One extra evaluation per mismatch. If that counter is ever
non-zero, `cascade` for that world is `multi_frame` and this file is void.

**Three things it does not cover, stated so nobody reads this as more than it
is:**

* **G-1 — nobody has run the criterion directly.** P-20 hashed frames; it never
  asked whether an intermediate frame is a state a rule could fire from
  (`cascade/VERDICT.md:172-175` says so itself, and calls it "级联语义留下的下一个真问题").
  §3's argument is two signatures pointing away from a tick, not a test of the
  tick.
* **G-2 — every trace stopped at level 0.** A tick introduced deeper in a game
  is outside everything measured.
* **G-3 — the 113-frame batch has never been looked at cell by cell.** It is the
  single largest piece of evidence in the set and it has only been counted.

## 6 · Provenance note — this ruling nearly had no evidence

P-20's probe produced the per-frame data this ruling rests on, and **none of it
was on any branch**. It existed as an untracked directory inside
`.worktrees/wt-p20/`, with no `MANIFEST.json` and no `RUN_STATE.md`, and the
only mention of P-20 in `PARTNER_SYNC.md` (line 570) is a note that it spends
money. A `git worktree prune` would have deleted the evidence for a Phase 1
gate item.

S5 salvaged it into [`cascade/`](cascade/) — code, `VERDICT.md`, the per-step
hash files, the summaries, the prediction sheets, and the raw ledgers. The raw
ledgers came too, despite being ARC content under §8's release obligation,
because `cascade/verify.py`'s load-bearing assertion (A3) **recomputes the frame
hashes from the stored bodies**; without them the salvaged evidence would be a
summary that agrees with itself, which this repository has twice decided is
worth nothing. They are added to the §8 conclusion-4 obligation instead —
redaction at release is a solved problem, unverifiable evidence is not.

Re-check it at any time:

```bash
cd arc-recon && bash cascade/verify.sh      # 27 steps, 31 ledger entries, PASS
```

## 7 · What each track must do

**theory-compiler.** Nothing in the generators changes. One thing must:
`theoria-arm/inner/grammar_card.py:23-25` hands the desk
`cascade single_frame` labelled "the only value the Python backend compiles",
which sets a per-world fact from backend capability — exactly what
`CONTRACTS/dsl_grammar_v0.2.md:335-340` forbids ("Do not copy these three
values from another manual… If you do not know which is true, that is a finding
to probe, not a default to accept"). The value it advertises is now the right
one, which makes this the easiest possible moment to fix the *reason*: cite this
ruling instead of the backend. Filed to monitor's inbox by S5; the file is not
in arc-recon's territory.

**engine-rig.** Nothing changes. T-11c already ruled `single_frame` for A0 on
the same criterion, and this ruling agrees with it.

**Both.** `n_frames` is not optional metadata. Any consumer taking `frames[-1]`
records how many frames it discarded.
