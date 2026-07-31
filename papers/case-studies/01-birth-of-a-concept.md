# Case study 1 · The birth of a concept

**Button and Door: from two unclaimed pixels to two entries in the vocabulary,
against a compression account that says neither should exist.**

Theoria §1.8 asks four questions of any concept and calls the answers a
*concept-birth timeline*: 哪一步进入词汇表、什么证据触发、买到多少压缩、首见到首用隔了几步
([`../../Theoria.md:94`](../../Theoria.md)). A0 answered all four for three
objects, and for two of them the third answer came back **negative** — the
concept costs more than it saves — and they were admitted anyway. This case
study is that admission, and the framework finding it forced.

Every number below is followed by the file it was read from. Nothing here was
re-derived.

---

## 1 · 首见 — before any engine ran

Board extraction runs before the engines and sinks every never-changing cell to
the board: **43 static cells, 38 dynamic, background colour 0**
([`../../cold-start-a0/THEORIZE_LOG.md:36-37`](../../cold-start-a0/THEORIZE_LOG.md)).
What it printed was a map, and one cell in it is not a colour:

```
1 1 1 1 1 1 1 1 1
1 0 0 0 0 1 0 0 1
1 0 0 0 0 1 0 0 1
1 0 0 0 0 1 0 0 1
1 0 0 0 0 . 0 0 1     '.' = dynamic, the board cannot explain it
1 0 0 0 0 1 0 0 1
1 0 0 0 1 1 0 0 1
1 1 1 3 1 1 0 0 1
1 1 1 1 1 1 1 1 1
```

— [`../../cold-start-a0/THEORIZE_LOG.md:39-49`](../../cold-start-a0/THEORIZE_LOG.md).
The adjudication log reads it in words:

> the divider at column 5 has exactly one cell — (4,5) — that the board refuses
> to explain. **A hole in a wall that is not always a hole.** That observation is
> what made me look for a door before any rule was read.
> — [`../../cold-start-a0/THEORIZE_LOG.md:53-56`](../../cold-start-a0/THEORIZE_LOG.md)

So the Door's first appearance in the record is not an object hypothesis. It is a
**failure of the board to account for a pixel** — which is constraint 2's
machinery working one layer earlier than constraint 2 is usually invoked.

## 2 · 什么证据触发 — segmentation, priced

`mdl_segmenter` offered two operators and the candidate payload carried both
scripts, so the choice was arithmetic rather than taste:

| operator | script bits | tracks | events |
|---|---|---|---|
| `connected_components(4)` | 6511 | 90 | 332 |
| `connected_components(4)+uniform_color` | **4423** | **3** | **216** |

— [`../../cold-start-a0/THEORIZE_LOG.md:77-80`](../../cold-start-a0/THEORIZE_LOG.md).
The colour-agnostic operator is not wrong, it is under-determined: the Cart
stands beside the Button often enough that the two merge into one blob, and the
tracker paid for it with 88 vanishes and 87 appears
([`../../cold-start-a0/A0_REPORT.md:96-100`](../../cold-start-a0/A0_REPORT.md)).
Three tracks survive, present in **276 / 100 / 276** frames, carrying **214**
`move` events (all `obj2`), **1** `recolor` (`obj0`) and **1** `vanish` (`obj1`)
([`../../cold-start-a0/THEORIZE_LOG.md:65-67`](../../cold-start-a0/THEORIZE_LOG.md)).

The naming is the only thing in the whole adjudication that is not machine
output, and the log says so:

> `obj2` is the Cart because it is the only thing that ever moves and it moves
> under the action. `obj1` is the Door because it sits in the wall's one
> unexplained cell and it is the thing that stops existing. `obj0` is the Button
> because it is the only object that changes without moving, and it does so in
> the same transition as `obj1` disappearing.
> — [`../../cold-start-a0/THEORIZE_LOG.md:69-73`](../../cold-start-a0/THEORIZE_LOG.md)

## 3 · 买到多少压缩 — the account comes back negative

This is the beat the case study exists for. From the engine's own cost model:

| object | declaration | script bits | pixel baseline | account |
|---|---|---|---|---|
| Cart | 21 | 2169 | 5136 | **+2967** |
| Button | 21 | 29 | 12 | **−17** |
| Door | 21 | 25 | 12 | **−13** |

— [`../../cold-start-a0/THEORIZE_LOG.md:92-96`](../../cold-start-a0/THEORIZE_LOG.md),
restated at [`../../cold-start-a0/A0_REPORT.md:111-115`](../../cold-start-a0/A0_REPORT.md).

Theoria §1.8 makes shortening the manual a concept's ticket of admission
([`../../Theoria.md:94`](../../Theoria.md)) and constraint 5 forbids an entry
with no gain — *无证据/无收益不入册*
([`../../Theoria.md:243`](../../Theoria.md)). By that rule the verdict is
unambiguous: **reject both.** Each has exactly one event in 275 transitions, and
a 21-bit declaration costs more than listing the two pixels that changed
([`../../cold-start-a0/THEORIZE_LOG.md:98-101`](../../cold-start-a0/THEORIZE_LOG.md)).

## 4 · 入册 — and the constraint that forced it

They went in. The log is explicit that intuition is not what put them there:

> They are admitted regardless, and the reason is a different constraint.
> Constraint 2 is full-frame responsibility: every pixel belongs to the board or
> to some object. Cells (3,2) and (4,5) change, so they cannot be board; if they
> are not objects either, then two pixels of every frame are unexplained and the
> cheap certify layer fails on frame 0. And the Door's rule cannot even be
> *stated* without the Button in the vocabulary.
> — [`../../cold-start-a0/THEORIZE_LOG.md:104-109`](../../cold-start-a0/THEORIZE_LOG.md)

Constraint 2 is *规划前全史重放——升级为双重对账(转移重放 + 渲染一致性,全帧责任制)*
([`../../Theoria.md:240`](../../Theoria.md)), and the cheap certify layer spells
out the teeth: **全帧责任制**——每个像素要么属棋盘、要么属某个对象,说明书没解释的像素就是意外
([`../../Theoria.md:226`](../../Theoria.md)).

So the decision procedure that admitted the Button was not "a button is obviously
a thing". It was: *this pixel changes, therefore the board cannot own it;
nothing else can own it; an unowned pixel is an anomaly at frame 0; therefore it
is an object.* Two of the framework's own admission criteria pointed opposite
ways, and the one that decided was the one with a machine check behind it.

The log filed it as a finding rather than a footnote, and wrote the negative
numbers into the manual instead of suppressing them
([`../../cold-start-a0/THEORIZE_LOG.md:112-117`](../../cold-start-a0/THEORIZE_LOG.md)).

## 5 · 首见到首用 — 99 transitions of silence

Both concepts entered the vocabulary in **revision 1, at M3, in a single pass
over all 28 candidates plus the board map**
([`../../cold-start-a0/THEORIZE_LOG.md:476-478`](../../cold-start-a0/THEORIZE_LOG.md)).
The Button is visible in every one of the 276 frames; its single event lands at
transition **99**, and the Door's single event lands at the same transition
([`../../cold-start-a0/theory/theory.dsl:21-22`](../../cold-start-a0/theory/theory.dsl)).
Two rules were written on that one witness — `press_left` (coverage 1/1,
guard `act==LEFT ∧ tcolor(LEFT)==7`, frontier size 1, so the vocabulary pinned
it exactly) and `door_opens_left` (coverage 1/1, guard **identical**)
([`../../cold-start-a0/THEORIZE_LOG.md:192-203`](../../cold-start-a0/THEORIZE_LOG.md)).

What one witness cannot buy is written down rather than glossed: the evidence
does not distinguish *press causes the Door to open* from *both are caused
independently by the same push* from *the Door opens whenever the Button is
pressed, whatever pressed it* — and there will never be a second witness,
because the latch is irreversible
([`../../cold-start-a0/THEORIZE_LOG.md:205-215`](../../cold-start-a0/THEORIZE_LOG.md)).

## 6 · What actually paid for them

The concepts were admitted on responsibility, but they were *earned* by an
engine, one layer up. `zero_space`, handed 152 anonymous indicator bits and told
nothing about buttons or doors, returned

```
[cell (3,2) shows 8]  +  [cell (4,5) shows 5]   ≡  1   (mod 2)
```

— **the Door exists if and only if the Button is unpressed**, with **275**
transitions of support against the single witness the rule miner had
([`../../cold-start-a0/THEORIZE_LOG.md:298-311`](../../cold-start-a0/THEORIZE_LOG.md),
[`../../cold-start-a0/A0_REPORT.md:77-88`](../../cold-start-a0/A0_REPORT.md)).
Written into the manual as `invariant door_latch count(Button, 8) + count(Door) = 1`
([`../../cold-start-a0/theory/theory.dsl:59`](../../cold-start-a0/theory/theory.dsl)).

The rule says *when* it happens; the law says *that it always holds*. And the law
is the thing that cannot be paraphrased away: it names both objects, and the
invariant language has no pixel-level form of it.

## 7 · The framework finding, and its correction

A0's diagnosis:

> The compression account is not wrong, it is comparing against the wrong
> alternative. The alternative to "the Button is an object" is not "encode its
> pixel edits"; it is "leave the cell unexplained forever", which this accounting
> prices at zero. **Recommendation for the framework: the compression account
> should be computed against the shortest *responsibility-complete* description,
> not against a per-object pixel baseline.**
> — [`../../cold-start-a0/A0_REPORT.md:123-129`](../../cold-start-a0/A0_REPORT.md)

That recommendation was implemented and re-run. On a responsibility-complete
baseline the accounts move to **Button −5, Door −1, Cart +2125**, and all three
objects come back `mandatory` on expressibility, each with the reason *"a law
names it … and the invariant language has no pixel-level paraphrase"*
([`../../cold-start-a0/artifacts/concept_accounts.json`](../../cold-start-a0/artifacts/concept_accounts.json),
key `a0-base`; written into the manual at
[`../../cold-start-a0/theory/theory.dsl:20-22`](../../cold-start-a0/theory/theory.dsl)).

The A0 report refuses to call that a dissolution:

> Button −17 → **−5**, Door −13 → **−1** on a responsibility-complete baseline,
> all three objects `mandatory` on expressibility. The §4 conflict is
> **narrowed, not dissolved**: an object with one event in 275 transitions still
> does not pay for itself *on the trace*. It pays on the *manual*, which is what
> 1.8 actually says.
> — [`../../cold-start-a0/A0_REPORT.md:241`](../../cold-start-a0/A0_REPORT.md)

## 8 · It reproduces

The conflict is not an artefact of one world. Two independent re-runs found it
again, with the same sign and the same resolution:

| world | Cart | second object | third object | verdict |
|---|---|---|---|---|
| A0 (pixel baseline) | +2967 | Button **−17** | Door **−13** | admitted on constraint 2 |
| A0 (responsibility baseline) | +2125 | Button **−5** | Door **−1** | all three `mandatory` |
| A0′ (responsibility baseline) | +1698 | Switch **−13** | Door **−9** | all three `mandatory` |
| A2 (responsibility baseline) | +1891 | Button **−5** | Door **−1** | admitted on responsibility |

Sources, in order:
[`../../cold-start-a0/THEORIZE_LOG.md:92-96`](../../cold-start-a0/THEORIZE_LOG.md) ·
[`../../cold-start-a0/artifacts/concept_accounts.json`](../../cold-start-a0/artifacts/concept_accounts.json) ·
[`../../cold-start-a0/prime/THEORIZE_LOG.md:43-47`](../../cold-start-a0/prime/THEORIZE_LOG.md) ·
[`../../cold-start-a2/THEORIZE_LOG.md:38-47`](../../cold-start-a2/THEORIZE_LOG.md).

A2's log states the value of the repetition exactly: *"This is A0's finding
(A0_REPORT §4), reproduced on a second world rather than restated — which is the
only thing A2 can add to it."*
([`../../cold-start-a2/THEORIZE_LOG.md:46-47`](../../cold-start-a2/THEORIZE_LOG.md)).

## 9 · What this case study does not show

* **The seal has a hole.** The same instance built the A0 world at M1 and
  adjudicated it at M3. No ground-truth file was opened between M1 and M5, and
  every verdict is written to be re-derivable from the candidate stream alone,
  but that is weaker than a genuine blind
  ([`../../cold-start-a0/THEORIZE_LOG.md:11-19`](../../cold-start-a0/THEORIZE_LOG.md),
  [`../../cold-start-a0/A0_REPORT.md:182-187`](../../cold-start-a0/A0_REPORT.md)).
* **The theorize step was not done by an LLM under experimental conditions in
  A2**, and A2's own report says so
  ([`../../cold-start-a2/A2_REPORT.md:271-273`](../../cold-start-a2/A2_REPORT.md)).
  The reproduction is of the *criterion collision*, not of an independent
  theorizer arriving at it.
* **The correction is not validated at scale.** Every world here has fewer than
  60 reachable states. Whether a responsibility-complete baseline stays cheap to
  compute on a real level is untested.
* **One number in the chain does not reconcile.** A0's per-object script bits are
  quoted as `Cart 2169 / Button 29 / Door 25` in the log's pixel-baseline table
  and as `2165 / 25 / 21` in `concept_accounts.json`'s
  `script_with_bits`. The two baselines are different accountings and the
  reports never claim otherwise, but the four-bit offsets are not explained
  anywhere on the tree. Recorded rather than reconciled.

---

*Next:* [`02-reversibility-beats-coverage.md`](02-reversibility-beats-coverage.md)
— what happened when the same criterion met evidence that could be re-witnessed.
Chart data for this case: [`data/cs01-concept-birth.json`](data/cs01-concept-birth.json).
