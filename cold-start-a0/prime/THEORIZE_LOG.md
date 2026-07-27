# THEORIZE_LOG — A0′

Same discipline as A0's: the ground truth (`prime/world/GROUND_TRUTH.md`,
`prime/artifacts/ground_truth.json`) was **not opened until the scoring pass at
the end of Run A**, and every verdict below is written to be re-derivable from
`prime/artifacts/candidates.jsonl` and the board map alone. The seal has the same
hole as A0's and it is named there: one instance built the world and adjudicated
it.

Evidence here is **deliberately incomplete** — the explorer stops at 40 % of the
exhaustive walk, 107/228 state-action pairs. That is the point of A0′.

---

## O — objects

Three tracks after two adjudications, both by script length.

### O-01 Segmentation operator
Colour-agnostic components: 2848 bits. Uniform-colour: **1923**. Same call as
A0, same reason (the Cart is forever adjacent to the Switch).

### O-02 Re-identification — **new, and A0 never needed it**
The raw segmentation returned **seven** tracks for a three-object world: the
Switch (one track, recolours match fine), the Cart, and **five Doors**. A0's Door
opened once and stayed open; A0′'s Switch is a toggle, so its Door closes and
reopens, and `mdl_segmenter` matches only frame *t* against frame *t+1* — nothing
local can recognise an object that comes back.

Merging same-template, disjoint-lifetime tracks costs nothing to state and saves
**48 bits** (re-declaring a returning object vs naming one already in the
vocabulary), so it is applied: **7 → 3**. On the colour-agnostic operator the
same pass gives 68 → 6. Written up in `pipeline/reidentify.py`; it is Theoria
1.8's template-matching operator, priced rather than asserted.

### O-03 `obj0` colour 7/8 → **Switch** · `obj1` colour 5 → **Door** · `obj2` colour 6 → **Cart**

Naming is mine. `obj2` is the Cart (the only thing that moves under the action).
`obj1` sits in the divider's single unexplained cell and is the thing that comes
and goes. `obj0` changes without moving, and its changes coincide exactly with
`obj1` coming and going.

### O-04 Concept accounts, on the responsibility-complete baseline
Cart **+1698**, Switch **−13**, Door **−9**; all three `mandatory`, because
`door_mirrors_switch` names two of them and the invariant language has no
pixel-level paraphrase (`pipeline/concept_account.py`). Same conflict as A0's
O-04, same resolution, and the same recommendation stands.

---

## R — rules

### R-01 `push_{up,down,left,right}` → **accept**
`act==D ∧ free(strip(D))`, coverage 17/17, 26/26, 16/16, 23/23; lifted 82/82.
Frontier of 3 per direction (`free` / `clear` / `tcolor==0`), extensionally
identical here as in A0, tie broken on strength.

### R-02 `teleport_down` → **accept**, 2/2
`act==DOWN ∧ tcolor(DOWN)==3`. Same two-member frontier as A0 (`tcolor==3` vs
`at(6,3)`) and the same argument: cheaper, and it is a *domain* fact rather than
a problem fact wearing its clothes.

### R-03 The toggle — **accept all sixteen clauses, and this is the difference from A0**

Eight switch rules and eight Door rules:

| pushing into | Switch becomes | Door | witnesses |
|---|---|---|---|
| colour 7 | 8 | vanishes | one per direction, all four |
| colour 8 | 7 | appears | one per direction, all four |

Each clause has coverage 1/1 — but there are **sixteen of them and every
direction-by-polarity combination has its own witness**. A0's `press_left` had
one witness and *no* way to get a second, so `THEORIZE_LOG` R-05 there had to
reject the direction generalisation and knowingly ship a hole. Here the
generalisation is not an analogy, it is enumerated evidence, and it goes in.

That is the whole design change of A0′ paying off: **a reversible mechanism can
be re-witnessed, so thin evidence does not have to stay thin.**

### R-04 `*_still_*` rules → **entailed**, as in A0
Eleven of them, up to 33/33. All consequences of `frame persist`, which — unlike
in A0 — the manual now *states*, because `semantics:` exists
(`proposals/dsl_grammar_v0.2_semantics.md`). The rejection no longer appeals to
something outside the file.

### R-05 The Crate → **no clause, and no clause is right**
The trajectory never pushes the Cart into colour 4 (6 uncovered pairs). Under
`frame persist` plus `free`, the manual already predicts that nothing happens:
colour 4 is not background, so no push rule fires. **Correct by omission**, and
the coverage probe in Run A confirms there is nothing untested here.

Run B seeds the opposite of this decision on purpose, to find out what would have
happened had the theorizer over-generalised. See `A0P_REPORT.md` §3.

---

## L — laws

### L-01 `count(Cart) = 1` → **accept**
From `zero_space`'s cart-occupancy parity law.

### L-02 `count(Switch, 8) + count(Door) = 1` → **accept** as `door_mirrors_switch`
`zero_space` returned `[cell (3,2) shows 8] + [cell (4,5) shows 5] ≡ 1 (mod 2)`
over all 110 transitions — *the Door exists iff the Switch shows 7*. Identical in
form to A0's `door_latch`, recovered again from anonymous indicator bits, and now
with a toggle underneath it rather than a latch, which makes it a genuinely
universal statement rather than one that holds because the world only ever moved
one way.

Proved in Lean over the full 2 × 36-state product: `inv_all`, axiom list empty.

---

## Goal — supplied, not induced, and flagged

The truncated trajectory never reaches the goal cell (`win_frames: []`), so
unlike A0 the goal clause cannot be read off a win flag. `goal Cart.pos = (2,7)`
is therefore **taken from the problem statement**, and that is recorded here
rather than quietly assumed. It is confirmed later, empirically: the plan of
Run A reaches (2,7) and the world's win flag fires (`plan_a0p_base.json`).

---

## Revisions

**Run A: 0.** Both certify layers green on the first manual, no rule untested, no
probe refuted, 228/228 against the truth.

Unlike A0, the zero is now explained rather than merely reported: the manual is
complete because **every mechanism could be re-witnessed**, not because the
explorer saw everything. Coverage was 47 %.

**Run B: 1**, driven by a probe refutation. Details in `A0P_REPORT.md`.

---

## Ground-truth seal

First opened by the scoring pass at the end of Run A, after both certify layers
and the probe stage were green. Run B's seed was written before that scoring pass
and does not depend on it — the Crate's behaviour is visible in the board map
(a colour-4 cell) without opening the referee's file.
