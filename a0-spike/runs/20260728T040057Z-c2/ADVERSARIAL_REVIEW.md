# Adversarial review — filed unedited

Commissioned by run `20260728T040057Z-c2` (prompt `C2-semantics-migrate`), step 6
of `PLAN.md`. The reviewer was instructed to **refute**, to default to "refuted"
when uncertain, to judge against `world/sokoban2.py` rather than against the
parser or the test suite, and was told its report would be filed unedited
whatever it said. It is filed unedited below, including the parts that were
right about defects in my own work.

**Timing matters for reading it.** The review ran concurrently with the
migration, so it read `THEORIZE_LOG.md` before T-11 was appended and the run
directory before `RUN_STATE.md` and `MANIFEST.json` existed. Its Attack 7 —
"three dangling citations" — was accurate at the moment it looked, and two of
the three had landed by the time it reported. It also saw `gen_exec.py` change
under it mid-review and said so.

## What was accepted and acted on

| finding | disposition |
|---|---|
| **`render` is injective; the on-wall exclusion was a reachability argument in disguise** | **Accepted — the reviewer was right and I was wrong.** Independently re-verified: 2352 states of `match`, 2352 distinct frames, 0 collisions. Within one level the wall set is fixed, so the wall being hidden under a box does not merge two *states*. The probe no longer excludes any stratum. The verdict rule now turns on whether a case *discriminates* between the two readings, which is the property that was actually wanted, and the 52 fall out of the verdict because both readings mispredict them identically (re-verified: 52/52 agree), not because of where they sit. |
| **The 52 are a `push2` guard defect and are inexpressible in the v1 guard language** | **Accepted.** Ledger **X-5**. `free(Box.pos)` compiles to `_free(state, state.box)`, identically false, so no guard can say "the Box is not on a wall". |
| **The generated `step()` did not enforce `exclusive`** — it tolerated any number of rules firing so long as they agreed | **Accepted and fixed.** `step` now raises on more than one rule firing regardless of agreement, and distinguishes "none fired" from "several fired" (the old code reported both as "ambiguous successor"). Pinned by `test_the_compiled_step_enforces_exclusive_even_when_rules_agree`. |
| **`frame persist` is sound only under the wide reading of `slid`; the narrow reading costs 376 mismatches** | **Accepted.** Folded into ledger **X-1**, which now carries the 376 and the observation that v0.2 never defines "mentions". |
| **`conflict exclusive` is entailed by a level-independent truth table, which is stronger than the sweep** | **Accepted.** The table is now written out in T-11b. The reviewer reconstructed it independently and reached the same partition. |
| **The `multi_frame` refutation is contingent on holding the action** | **Already recorded** in T-11c before the review reported, and the reviewer's framing is sharper, so `predict_multi_frame`'s docstring — which had asserted the reading as a fact about the world — was corrected to state it as an assumption of the probe. |
| **The stored JSON did not attest the checked-in manual** (`section_supplied_by_probe: true`) | **Accepted.** The probe was re-run against the migrated manual; the field now reads `false`. |
| **No `MANIFEST.json`** | **Accepted.** Written. |

## What was not acted on

* **"I did not verify the other three compiled forms honour the values."** Correct
  and it is ledger **X-2**: `pddl_gen` builds from level data and `A0.lean` is
  checked in, so neither reads the manual and neither *can* be guarded without
  rebuilding it as a real generator. Out of scope for a migration; recorded.
* **"I did not test levels outside the five evidence levels."** For `conflict`
  the truth-table argument is level-independent, so this does not bite. For
  `frame` and `cascade` it is a real residue, stated in T-11 rather than closed.

## Report, verbatim

---

# Adversarial review: does a0-spike's `semantics:` describe the A0 world?

Reviewed at `theory/theory.dsl` md5 `3216d1c3…` (mtime 2026-07-28 14:14:09), `pipeline/gen_exec.py` md5 `7d5b7f62…` (mtime 14:19:35), `probes/semantics_probe.py` md5 `464abea1…`. **`gen_exec.py` was edited by another session mid-review** — my first read of it had no `_check_semantics`; the current one does. Everything below is re-run against the files at those hashes.

## Verdict per statement

| statement | declared value | my verdict | one-line reason |
|---|---|---|---|
| `frame` | `persist` | **SOUND** | `sokoban2.step` returns `state` unchanged on BLOCKED and `State(player=target, box=state.box)` on MOVE (`world/sokoban2.py:141,146`) — unwritten objects never move; and I proved the 52 counterexamples the probe excludes are *not* frame counterexamples (`reset` predicts the identical wrong successor on all 52, so the frame axiom is vacuous there). |
| `conflict` | `exclusive` | **SOUND, and entailed** — the strongest of the three | The five guards form a 12-row partition over the four guard atoms, wall-set-independent, so it holds for *every* level, not just the five swept. |
| `cascade` | `single_frame` | **SOUND as a claim; the probe's evidence for it is UNDERDETERMINED** | `step` is a function to one `State` (`world/sokoban2.py:156`) and the two-cell slide emits no intermediate frame — so the value is right. But the probe's refutation of `multi_frame` survives only under a reading of "re-fire" that the contract does not fix; under the alternative reading the refutation is vacuous. |

Bottom line: **all three values describe the world.** The defects I found are in the *evidence*, in one rule, and in three dangling citations — not in the three declared values.

## Attacks attempted and what happened

### Attack 1 — `slid(Box, dir)` hides the Player's motion. Does `frame persist` survive?

**Partly refuted, in a way that matters.** `slid` is compound at `pipeline/gen_exec.py:183-188`: it writes `state.box` two cells *and* `state.player` one. The manual's event declaration (`theory/theory.dsl:42`) is `slid(o, dir)` — one object argument, `Box`.

There are three readings of the contract's word "mentions":

- **(a) the rule's text mentions.** `blocked_wall`'s guard contains `not Box.pos = ahead(Player, dir)` (`theory.dsl:55`) — it *mentions* Box. So under (a) the frame axiom is silent about the Box on the most common transition in the world, and the manual determines no successor at all. Reading (a) is dead.
- **(b-narrow) the event writes, read off the signature.** `slid` writes `{Box}`, so `persist` freezes the Player across a push. I ran this: **376 off-wall mismatches out of 39,960**, all `push2`, e.g. `match`, player (0,0), box (0,1), RIGHT → manual predicts player (0,0), world gives (0,1). Reading (b-narrow) is *refuted by the world*.
- **(b-wide) the event writes, read off `_compile_effect`.** `slid` writes `{box, player}`. 0 off-wall mismatches. This is the probe's reading (`semantics_probe.py:78-82`) and the only one that works.

So: `frame persist` is sound, but **only relative to an effect dictionary that lives in `pipeline/gen_exec.py`, not in the manual and not in `CONTRACTS/dsl_grammar_v0.2.md`.** Two of the three readings of the contract's own word produce a different world; one of them by 376 concrete counterexamples. The probe chose correctly and said why, but the manual's `semantics:` block does not record that its `persist` is reading-dependent, and the contract does not define "mentions".

Does this make `exclusive` a smuggled cascade? **No.** The probe reads `slid` wide, which *enlarges* the set of rule pairs whose claimed objects intersect (push2 now collides with all four player-writing rules), and the discharge still goes through. Reading wide is the conservative choice and it was made. Attack fails against `exclusive`.

### Attack 2 — construct a two-rule-firing configuration by hand

**Failed to refute, decisively, and the manual's `exclusive` is stronger than the probe's own evidence for it.**

Let `A = free(ahead(P,d))`, `B = (Box.pos = ahead(P,d))`, `C = free(ahead(Box,d))`, `D = free(beyond(Box,d))`. Guards are `walk: A`; `push2: B∧C∧D`; `blocked_wall: ¬A∧¬B`; `blocked_box_crossing: B∧¬C`; `blocked_box_landing: B∧C∧¬D`. `free(c)` excludes `c == box` in both the world (`world/sokoban2.py:121`) and the compiled form (`_free`, verified in the generated source), so `A∧B` is unsatisfiable. Enumerating the remaining 12 assignments: **exactly one rule fires in all 12, zero violations.**

This is a *total partition* and it never mentions a wall set, a board size, or a level. `conflict exclusive` therefore holds for the whole domain, not merely for the five levels the sweep covers — which is exactly what `v0.2 §Discharging conflict` route 1 asks for, and it is a stronger result than the exhaustive sweep the manual leads with. The pair `walk`/`push2` is covered by the contract's listed criterion "one requires `free(t)` and the other a non-background colour of `t`"; every other pair is settled by an explicit `not` of a predicate the partner requires.

I could not construct any counterexample. I also confirmed by exhaustive sweep: 47,040 pairs, `max_rules_fired = 1`, `no_rule_fired = 0`.

### Attack 3 — is holding the action a fair reading of `multi_frame`?

**Succeeded against the evidence; failed against the value.**

Every one of the five rules carries a `GuardAction` clause — I checked the parsed AST: each rule's clause list begins with `GuardAction`. So under the action-consumed reading, round 2 has no action, zero rules fire, quiescence is immediate, and `multi_frame` is *observationally identical* to `single_frame` on all 47,040 pairs. The probe's 22,582 off-wall "multi_frame mismatches" are entirely an artifact of `predict_multi_frame` holding `direction` across rounds (`semantics_probe.py:151-160`).

`CONTRACTS/dsl_grammar_v0.2.md:101` says only "one action yields a frame sequence; rules re-fire until quiescence". It does not say whether the action survives into round 2. The contract's own motivating example (`press_left` recolours a button, `door_opens_left` re-reads its guard, line 110-113) is a *state-triggered* second round, not an action-triggered one — which if anything favours the consumed reading. The probe's docstring asserts "nothing switches the action off" as though that were a fact about the world; it is a fact about the probe's loop. Note also that `gen_exec.generate` *discards* the `GuardAction` clause entirely (`continue`, `gen_exec.py:295`), so the compiled predictor cannot represent the consumed reading even in principle.

**Does `single_frame` survive?** Yes, but on different grounds than the probe gives. `sokoban2.step` is a function to one `State`; `rollout` (`world/sokoban2.py:168-184`) renders only post-step states. The two-cell slide is `_add(state.box, delta, 2)` — a single assignment inside a single rule's effect, with no state in which the box sits at `box+1`. No intermediate frame exists. `single_frame` is simply true.

So the value is right and the probe's claimed *refutation of the alternative* — which is the probe's own declared standard, `semantics_probe.py:12-17` — does not hold under a reading the contract permits. This should be recorded as a conditional adjudication, not as a refutation.

### Attack 4 — is the on-wall exclusion legitimate?

**Refuted. This is the real finding.**

The probe's stated ground (`semantics_probe.py:327-332`, repeated in eight JSON witnesses): "`render` paints walls first and the object over them, so an object standing on a wall produces the *same frame* as the same object standing on bare floor. No observation denotes such a state."

I checked `render` (`world/sokoban2.py:159-165`). It writes `BOX` at exactly one cell and `PLAYER` at exactly one other. **I enumerated all 2,352 representable states of `match` and got 2,352 distinct frames — zero collisions.** `render` is injective on the representable set. Every on-wall state has a frame of its own. The stated reason is factually false.

What is actually hidden is the *wall*, which is level-static data, not state. And the two states are not even behaviourally confusable: I built `match` minus the wall at (1,5) and stepped both from player (0,5) / box (1,5) / DOWN. Pre-frames identical; **successors differ — `blocked` vs `push` to (3,5)**. So the disputed state is denoted by a unique frame *and* distinguishable from its supposed twin by one observation. There is something there for the manual to be wrong about, and it is wrong about it.

This contrasts with the `player == box` exclusion the probe leans on for precedent, which *is* legitimate: `render` writes PLAYER after BOX, so the box's position is genuinely unrecoverable. The two exclusions are not the same kind of thing, and the probe treats them as one.

Is it a reachability argument in disguise? Yes. The 7,080 on-wall pairs are exactly the ones no play reaches. And `THEORIZE_LOG.md` T-9 closes with "**39,960 well-formed states across five levels, 0 mismatches**" — 39,960 is precisely the off-wall count. So the new sweep widened the domain by 7,080 states, found 52 mispredictions, and then restored the old 0. T-9's own moral is quoted in the probe's docstring: "a rule can be right as a problem solution and wrong as a domain… all 8 mismatching states were unreachable, and the rule was still wrong." The probe cites T-9 to justify sweeping wide for `conflict` and then commits T-9's error for `frame` and `cascade`, three paragraphs apart.

**But the 52 are not evidence against `frame persist`.** I attributed every one of them: **all 52 fire `push2`**, and `push2` writes both objects, so the frame axiom has nothing to do. I confirmed numerically that `predict_reset` produces the *identical wrong successor* on all 52 — the two frame values agree there. The mismatch is a **rule-guard defect**: `world/sokoban2.py:140-145` checks `in_bounds(target)` and `is_wall(target)` **before** `target != state.box`, so a box parked on a wall blocks the player; `push2` (`theory.dsl:52`) has no clause that can see this. And it cannot get one — `free(Box.pos)` compiles to `_free(state, state.box)`, which is unconditionally `False` because `_free` excludes the box's own cell. The fact "the Box is not standing on a wall" is **inexpressible in the v1 guard language**.

So the correct disposition, in the contract's own vocabulary (`dsl_grammar_v0.2.md:143-148`): this is a **conditional discharge relative to a well-formedness condition the manual does not declare**, which "is simultaneously a defect report… and belongs in the ledger." It was instead labelled an observability artifact and filed as `on_wall_witnesses`.

### Attack 5 — does `frame persist` bite, or is it unfalsifiable?

**Failed to refute.** The rule set is total (`no_rule_fired = 0`, confirmed independently), so one might expect `persist` to be doing nothing. It is not: `reset` does not mean "no-op", it means unwritten objects *return to the initial value*. Since four of five rules write only the Player, `reset` teleports the Box to (3,3) on almost every transition — **38,712 off-wall mismatches of 39,960**. The two values are maximally separated and `persist` is the one the world implements. `persist` is falsifiable here and survives.

### Attack 6 (mine) — does the backend actually enforce `exclusive`?

**Partly succeeded.** `gen_exec._check_semantics` (added to the file *during* this review) now refuses `frame reset` / `conflict priority:` / `cascade multi_frame` at generation, which satisfies `dsl_grammar_v0.2.md:114-120` and closes revision item 10 for this backend. But the generated `step()` does not enforce `exclusive` at runtime: `if len(fired) != 1:` it only raises when the successors *disagree* (`gen_exec.py:261-267`). I spliced a duplicate of `_rule_walk` into `RULES` — two rules fired, no exception, `step` returned normally. Under `conflict exclusive` two firing rules are a violation regardless of whether they agree. The docstring says "Exactly one rule must fire (constraint 9)"; the code enforces "at most one distinct successor". The source comment at `gen_exec.py:43-45` also describes `STEP_TEMPLATE` as taking "the first rule whose guard holds", which is not what the code does either. Cosmetic today (the guards really are disjoint), load-bearing the moment a rule is added.

### Attack 7 (mine) — do the manual's cited sources exist?

**Succeeded.** `theory/theory.dsl:17` cites "逐项裁决理由见 ../THEORIZE_LOG.md T-11"; `theory.dsl:28-29` cites "另有独立的句法证明（route 1）在 THEORIZE_LOG T-11c"; `theory.dsl:19` cites "复算命令见 runs/20260728T040057Z-c2/RUN_STATE.md". **`THEORIZE_LOG.md` ends at T-10** — there is no T-11 or T-11c. **`runs/20260728T040057Z-c2/` contains only `PLAN.md` and `semantics_probe.json`** — no `RUN_STATE.md`, and no `MANIFEST.json` anywhere under `a0-spike/runs/`, which `CLAUDE.md` requires of every experiment. `semantics_probe.py` refers to "RUN_STATE FINDING-2" three times, including in eight strings baked into the checked-in JSON. The strongest single argument for `exclusive` — the syntactic route-1 proof, which I independently reconstructed and which is valid — is cited to a document that does not exist.

Separately: the stored artifact carries `"section_supplied_by_probe": true`, i.e. it was produced against a manual with no `semantics:` section. That is methodologically correct (the probe ran before the migration decided it) and the compiled predictor is unaffected, but the checked-in JSON does not attest the checked-in manual, and with no MANIFEST there is nothing pinning which commit it does attest.

## Findings the migration should record but does not

1. **The 52 on-wall mispredictions are a `push2` defect, not an observability artifact, and they are unfixable in the v1 guard language.** The world checks `is_wall(target)` before `target != box` (`world/sokoban2.py:142-145`); no guard can say "the Box is not on a wall" because `free(Box.pos)` is identically false. This belongs in the expressivity ledger next to E-01/E-07, and the frame/cascade discharge should be stated as **conditional on a named well-formedness condition** per `dsl_grammar_v0.2.md:143-148` — which makes it a defect report by the contract's own rule.
2. **`render` is injective on representable states (0 collisions in 2,352).** The justification text in `semantics_probe.py:327-332` and in eight checked-in JSON witnesses is false and should be corrected rather than propagated; on-wall states are observationally distinguishable from their supposed twins by one step (blocked vs push, verified).
3. **`frame persist` is sound only under the wide reading of `slid`.** The narrow reading costs 376 off-wall mismatches; the textual reading of "mentions" leaves the successor undetermined via `blocked_wall`'s guard. The contract does not define "mentions"; the manual does not say which reading it claims. This is a contract gap worth a v0.3 ledger entry, not just a probe comment.
4. **`conflict exclusive` is entailed level-independently by a 12-row truth table** and does not need the 47,040-pair sweep at all. The manual leads with the sweep and relegates the stronger argument to a non-existent T-11c. Write the truth table down — it is four lines and it covers every level the domain will ever travel to.
5. **The `multi_frame` refutation is contingent on holding the action across rounds**, a reading the contract does not fix and the contract's own `press_left` example does not use. Under the alternative, `multi_frame ≡ single_frame` on all 47,040 pairs and nothing is refuted. Record the reading as an assumption of the probe.
6. **The generated `step()` does not enforce `exclusive`** — it tolerates any number of rules firing so long as they agree (demonstrated). Three dangling citations (T-11, T-11c, RUN_STATE.md) and a missing MANIFEST.json.

## What I could not check

- **The worktree is being edited while I review it.** `pipeline/gen_exec.py` changed at 14:19:35, after my first read — `_check_semantics` did not exist when I began and does now. Every number above was re-run against the hashes stated at the top, but any file may have moved since.
- **I did not re-run `probes/semantics_probe.py` itself**; I re-derived its sweep independently and reproduced 47,040 / 39,960 / 7,080 / 52 / 38,712 / max-1-rule exactly, which is stronger evidence than re-running it would have been.
- **I did not verify the other three compiled forms** (Lean, PDDL, Markdown) honour `persist` / `exclusive` / `single_frame`. `dsl_grammar_v0.2.md` revision item 10 records `gen_pddl` as the backend that historically ignored the section; `artifacts/pddl/domain.pddl` is modified in the working tree and I did not audit it. Only the Python form was in scope.
- **I could not read `THEORIZE_LOG` T-11/T-11c** because they do not exist, so I cannot say whether the reasoning I reconstructed matches what the adjudicator actually had in mind.
- **I did not test levels outside the five evidence levels.** For `conflict` this does not matter (the truth-table argument is level-independent); for `frame` and `cascade` a level with different wall parity could in principle expose more, though the rule-by-rule correspondence to `sokoban2.step` I traced by hand suggests the only residue is the box-on-wall class already found.
- **I did not run the test suite** — deliberately. The claim was to be judged against the world, and a green suite that asserts `semantics.frame == "persist"` (`tests/test_a0.py:230`) is not evidence about `sokoban2.step`.
