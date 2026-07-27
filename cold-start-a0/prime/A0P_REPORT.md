# A0′_REPORT — the follow-up spike, and what it settles

A0′ exists to answer the three things `A0_REPORT.md` §6 said A0 could not test.
It answers all three, and one answer is the opposite of what the A0 report
assumed.

```bash
cd cold-start-a0 && python -m prime.run_prime     # both runs, ~15 s
```

---

## 1 · The headline

| | A0 | A0′ |
|---|---|---|
| mechanism | Button, **latch** — pressable once | Switch, **toggle** — re-witnessable |
| explorer | exhaustive | **truncated at 40 %** of the exhaustive walk |
| state-action coverage | 233/236 = **99 %** | 107/228 = **47 %** |
| full-history replay | green | green |
| **accuracy vs ground truth** | 233/236 = **98.73 %** | **228/228 = 100 %** |
| executable probes emitted | **0** | **13** |
| rules left untested by the trace | 1 (unprobeable) | **0** |

**Half the coverage, perfect accuracy.** A0 saw almost everything and still
shipped a manual that was wrong in three places; A0′ saw less than half and
shipped a manual with no errors at all.

The variable is not how much was seen. It is whether what was seen could be seen
**again**. A0's latch meant `press_left` had exactly one witness and no way to
obtain a second, so the direction generalisation had to be rejected on evidence
grounds and the manual shipped a known hole. A0′'s toggle gives every
direction-by-polarity combination its own witness, so the same generalisation is
enumerated evidence rather than an analogy, and it goes in.

**Recommendation, stronger than A0_REPORT §7.2 stated it:** when designing a
self-built world — or choosing which ARC levels to develop on — *reversibility of
the mechanisms matters more than the breadth of the trajectory*. An irreversible
mechanism caps what any amount of exploration can establish.

---

## 2 · Run A — the cold start

| step | result |
|---|---|
| trace | 111 frames, 110 transitions, 107/228 pairs |
| segmentation | 3 tracks, after **re-identification** merged 7 → 3 (48 bits) |
| mining | 35 rule hypotheses, all guards mutually exclusive and total, per track |
| `zero_space` | 2 global laws, including the Switch↔Door dependency again |
| probes | 13 executable of 27 designed (A0: **0** of 22) |
| manual | 3 objects, 21 rules, 2 invariants, 1 theorem |
| certify cheap | 111 frames, 8991 pixels, **0 anomalies** |
| certify Lean | `inv_all`, **axiom list empty**, `decide` only |
| coverage probes | 21 rules, **0 untested** |
| plan → commit | SAT, 10 steps, manual and world agree frame-for-frame, **win** |
| score vs truth | **228/228 = 1.0000** |
| **revisions** | **0** |

A revision count of 0, again — but for a reason that is now measured rather than
guessed. A0 reported 0 and could not say why. A0′ reports 0 *and* shows that no
rule was untested and no probe refuted anything, on 47 % coverage. The manual was
complete, and the loop had nothing to do because there was nothing wrong.

### The re-identification finding

`mdl_segmenter` matches frame *t* against *t+1* only, so an object that vanishes
and returns is a **fresh track every time**. A0 never saw this: its Door opened
once. A0′'s Door closes and reopens, and the raw segmentation came back with
**five Doors**. Five Doors is not a theory — no rule can be stated about an
object whose identity resets on every use.

The repair is Theoria 1.8's own template-matching operator, and it is priced
rather than asserted: two tracks are the same object when they have identical
relative cells and colours and disjoint lifetimes, and the merge is applied only
because it shortens the script. `pipeline/reidentify.py`. This is the second
segmentation gap A0-family worlds have found in `mdl_segmenter`, after the
touching-objects one, and it is worth reporting upstream as a capability the
engine needs rather than a bug.

---

## 3 · Run B — does the loop repair a wrong theory?

A0's report called this the untested bet. It is a **controlled experiment**, not
a discovery, and it is labelled that way in the seeded manual's own header.

**The seed.** One clause added to Run A's manual:

```
rule push_onto_crate [ev: none cov: 0/0]
  when act=push(Cart, right) and colored(rightof(Cart), 4) then moved(Cart, right)
```

It claims the Cart can walk onto colour 4. It is false. It is chosen to be
**invisible to replay**: the trajectory never once pushes into the Crate, so the
rule never fires during the whole 110-transition history. This is the DC22 shape
of Theoria 1.3 and the exact shape of A0's own real miss — the difference is that
here the firing state is reachable.

**What happened, in order:**

| layer | verdict |
|---|---|
| full-history replay | **GREEN** — 111 frames, 8991 pixels, 0 anomalies. Blind, exactly as predicted. |
| Lean transcription | **CAUGHT IT.** `ArenaEscape: step sends the mover to (2,4), which the board does not list as arena (from (2,3) on right)` |
| coverage probe | **CAUGHT IT.** `push_onto_crate` has 2 firing states and neither is in the trace → navigate 3 steps to (2,3), predict Cart→(2,4), execute, observe Cart stays at (2,3) → **refuted** |
| repair | delete the clause; 1 revision; accuracy **0.9912 → 1.0000** |

**Two independent mechanisms caught what replay could not**, and they caught it
in different ways, which is worth separating:

* the **coverage probe** is the empirical one and is the mechanism Theoria
  specifies (constraint 7). It found the rule *because* nothing in the trace
  exercised it, navigated to a firing state using the manual, wrote its
  prediction down first, and let the world disagree. This is the machinery A0
  could not run at all;
* the **Lean form** caught it as an *internal* inconsistency, before the world
  was consulted: the manual's `step` sends the Cart to a cell the manual's own
  board does not list as arena. That is a genuine second check and it was not
  designed for — it fell out of transcribing the state space, and it turned a
  `KeyError` into a typed certify diagnostic.

So the answer to §6.1 is **yes, the loop repairs** — and the cheap layer is not
the thing that does it. Whether the loop repairs a *subtler* error, one that
neither escapes the arena nor sits on an untested rule, remains untested.

---

## 4 · Failure-taxonomy diagnosis, A0′

| class | verdict | evidence |
|---|---|---|
| **概念不成形** | **hit, new form** | not the vocabulary and not the compression account this time, but **object identity across absence** — the segmenter cannot recognise a returning object, and a toggle world makes that fatal (5 Doors). Fixed by a priced operator; upstream needs the capability |
| **机制归纳错** | **clear** | 0 replay mismatches, 228/228 against truth, no probe refuted an accepted clause |
| **调度失误** | **clear** | every number in the manual traces to an engine payload |
| **表达力不够** | **improved, still hit** | `semantics:` closed the frame-axiom hole (E-03), so R-04's rejection of eleven no-op rules now appeals to something *in* the file. Still open: no `?dir` lifting, so the toggle costs **sixteen** clauses where the world has two rules — E-02's cost went from 3 extra clauses in A0 to 14 here |
| **证明打不动** | **clear** | `inv_all` in ~2 s, axiom list empty, no Mathlib |
| **搜索爆炸** | **clear** | 10-step optimal plan, instantly |
| **戳探设计差** | **resolved** | 13 executable probes vs A0's 0, and the coverage prober found and killed the seeded clause. The design change (reversibility) is what did it |
| **修订抖动** | **still not measurable** | Run A 0 revisions, Run B 1. Neither run got near thrash; a world that forces several rounds is still to be built |

---

## 5 · What A0′ still does not show

1. **No multi-round repair.** Run B took exactly one revision and the repair was
   a deletion. Nothing here exercises a manual that has to be revised, re-probed
   and revised again — the "修订抖动" row is still empty.
2. **The seeded error was of a convenient kind.** It escaped the arena, which is
   what let the Lean form catch it for free. An error that stays inside the arena
   would have had only the coverage probe to catch it, and only because the
   clause was untested. A wrong-but-tested clause would fail replay; a
   right-looking-but-wrong clause on a *tested* firing state is not covered by
   either mechanism, and that gap is real.
3. **The goal was supplied, not induced** — the truncated trace never wins. It is
   confirmed empirically afterwards, but the manual did not derive it.
4. **Scale is still untested.** 57 reachable states, 36 arena cells. Lean's
   `decide` is affordable here and will not be at 10⁶.
5. **The seal has the same hole as A0's:** one instance built the world and
   adjudicated it.

---

## 6 · Verdict

A0′ settles the two questions A0 left open and adds one finding nobody asked
for:

* **probes work, and A0's inability to run them was a property of A0, not of the
  framework** — 13 executable probes, and the coverage prober killed a seeded
  clause that replay could not see;
* **the loop repairs** — one seeded, replay-invisible error, caught twice
  independently, repaired in one revision, accuracy back to 1.0;
* **reversibility beats coverage** — 47 % of the state-action pairs and a perfect
  manual, against A0's 99 % and three errors. This is the finding that should
  change how the next world, and the choice of development levels, is designed.
