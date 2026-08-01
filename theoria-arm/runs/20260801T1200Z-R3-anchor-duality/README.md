# R3 — the anchor duality: one state doing two jobs, and the repair that keeps both

Offline. No ARC action, no model call, no network, no spend. Development-pile
games only (`g50t-5849a774`, `sk48-d8078629`); nothing here touches the sealed
pile. Nothing in this directory was run live and nothing here needs to be.

Reproduce, both from this directory:

```bash
python measure_drift.py  --legs-root ../    # DRIFT.json          (all 8 live legs)
python replay_anchor.py  --legs-root ../    # ANCHOR_REPLAY.json  (the 52 probes)
```

Both read `trace.jsonl`, which `theoria-arm/.gitignore` excludes. In a clone
without the traces they refuse per leg and measure nothing, rather than
reporting zero. `DRIFT.json` and `ANCHOR_REPLAY.json` are the durable record;
they carry counts and cell coordinates, never frames.

---

## 1. The tension, stated precisely

`inner/loop._roll_forward` answers exactly one question — *where would the
manual be if it were right?* — and the arm spends that one answer on two jobs
whose requirements are opposed.

| | Job A — audit | Job B — experiment design |
|---|---|---|
| who | `certify.cheap`'s replay | `probe.build_hypotheses` / `design` |
| the question | does the manual reproduce the whole recorded trajectory? | what will the world's **next** frame be? |
| needs the state to be | **open-loop from t=0**, free to drift | **the frame the world is showing**, never drifting |
| what breaks if it isn't | a re-seated replay cannot diverge by more than one step, so it goes green on a manual that is wrong everywhere — `Theoria.md` 1.3's 写错的规则 detector stops detecting | every hypothesis is a successor of a frame that no longer exists, so the experiment is about a different world |

One variable serves both, and Job A wins silently. That is the defect, and it
is why the obvious repair is not a repair: **re-seating the manual's state on
the world's observed frame each turn fixes Job B by destroying Job A's
instrument.**

There is a second reason the obvious repair is not available even if one wanted
it. `render` is not injective — the generated `State` is one `<name>_pos` /
`<name>_color` pair per instance, and many assignments paint the same grid — so
"the state the world is in" is not a well-posed thing to compute. A re-seat
would have to *guess* an assignment and seat the guess inside the manual's own
state, where nothing downstream could tell it from something the manual had
derived.

---

## 2. The designs, and why three of the four trade one blindness for another

**D0 — today.** One anchor, rolled forward. Default. Drift invisible: no
artefact in this arm reports it.

**D1 — re-seat everywhere** (the obvious fix). Rejected on the argument above:
it makes `certify`'s replay trivially green and needs an assignment nobody can
derive. It buys a correct probe anchor at the price of the only check that
catches a wrong rule, which is the worst trade available.

**D2 — dual anchor.** Keep the rolled-forward state exactly as it is, for
certify and for the mechanism of every hypothesis. Give Job B its own anchor,
and make the divergence between the two a first-class measurement.
**Recommended, implemented.** Its two sub-forms differ in what the second
anchor *is*:

* **D2a — add world-anchored hypotheses beside the ablations.** This is
  R2's shipped `--frontier generated`. It works (43 of 52) but the anchoring
  half of it arrives as two extra hypotheses that widen the frontier from 2
  distinct predictions to 5–10, which lowers the split entropy of every action
  and prices every probe higher.
* **D2b — move the anchor of the ablations themselves.** Every hypothesis keeps
  its mechanism (still the manual's own `step` from the rolled-forward state)
  and only the frame its answer is read against changes:

  ```
  prediction = hash( world_frame ⊕ ( render(h(state, a)) − render(state) ) )
  ```

  Same ids, same order, same width. **This is what is implemented**, as
  `--anchor observed`.

**D3 — re-anchor for probe design only, discarding the rolled state, logging
each re-anchor as evidence.** Rejected, and the reason is measurable rather
than aesthetic: a re-anchor event is a *bit*, and this run's central number is a
*magnitude*. D3 can say "the anchor was wrong 35 times"; it cannot say the drift
was one cell on 20 of them and 23–25 cells on 8, which is the difference between
"the manual is nearly right and the frontier is comparing whole-frame hashes"
and "the manual is lost". D2 subsumes everything D3 records and adds the size.
D3 also still needs the ill-posed state inversion, and D2b does not.

**D4 — drift as an eighth surprise.** Rejected on two grounds, and the second
is the substantive one.

* `Theoria.md` 1.9 closes the taxonomy at seven — empirical five, computational
  two — and `inner/surprise.py` raises on an eighth by construction with the
  message that adding one is a change to 1.10(d), not to that file. This is a
  design change and would have to be argued as one.
* It would also be the wrong eighth. Drift is not a new *kind* of evidence; it
  is the accumulated consequence of a `replay_mismatch` that has **already**
  fired and already paid for a desk call. A second surprise for the same defect
  double-counts against constraint 8's arithmetic — `Register.audit` checks
  that model calls and surprises line up — and buys a paid call to be told the
  same news twice. Its correct home is a *measurement attached to the surprise
  that already exists*, which is where it now is.

---

## 3. What was found on the way, and it corrects two things

### 3a. The arm has been computing the drift every certify beat and discarding it

`certify.cheap` replays the manual open-loop from `initial_state()` and writes
`entry["cells_wrong"]` per transition. That series **is** the anchor's drift:
`_roll_forward` and certify's replay are the same walk, from the same origin,
over the same actions. `certify.json` archives only the summary line
(`16/21 transitions replay exactly`) and the first divergence; `replay_steps`,
where the per-transition counts live, never reaches disk.

So the quantity `GAPS.md` R2-1 says a default leg cannot see has been measured
every certify beat since P-8 and filed as an audit line nobody read as the
error of the frame the probes were designed against. `measure_drift.py`
recomputes it, and the recomputation is checked first: a snapshot is accepted
only if the `checks.replay` block it produces equals the archived one on `ok`,
`transitions`, `matched`, `detail` and `first_divergence`.

### 3b. "One mispredicted transition desynchronises the state permanently" is false

That sentence is in R2's README and in this ticket's own brief. The archive
refutes it. Drift **recovers**: 8 recovery events across the 8 legs, on 4 of the
6 legs that ever drifted, and the series is non-monotone on those 4.

```
20260731T1500Z-A3-sk48-carried-l1   [96, 0, 0, 0, 0, 0, 1, 0, 1, 1, 1, 1, 2, 1, 1, 1, 0]
20260801T001851Z-R1b-g50t-a         [0,0,0,0,0,0,0,0,0,0,0,0,1,0,1,0,1,1,1,0,0]
```

The mechanism is that the manual's `step` is not injective — a mover that is
capped at a wall, or a cell that is set rather than toggled, re-converges. The
correction does **not** weaken the case for the change: what matters is whether
the anchor was wrong *at the moment a probe was designed*, and it was, on 35 of
52. It does mean the failure is "the anchor is often wrong" and not "the anchor
is wrong forever after the first mistake", and the second sentence would have
been repeated into the next round unchallenged.

### 3c. R2's harness was checked, and it is sound

R2's replay rolls the manual over `[s.action for s in prefix.steps]`, which
begins with the leg's `RESET`; `inner/loop._roll_forward` rolls it over
`store.actions`, which is that list shifted by one with a trailing `None`. Those
are different action sequences, and had they produced different states, R2's
headline 35 would have been an artefact of its own harness. `replay_anchor.py`
recomputes both on every probe: **equal on 52 of 52, disagreed on 0.** R2's 35
is a fact about the arm.

---

## 4. The measurement — `ANCHOR_REPLAY.json`

Same 52 completed probes R2 measured, same reconstruction check (a snapshot is
accepted only if its ablation prediction dict equals the dict `probes.jsonl`
recorded, key for key and hash for hash), 52 of 52 reconstructed, 0
unreconstructed.

**"How many of the 35 would have been designed from the right state" is 35, by
construction and not by measurement.** Under `--anchor observed` the frontier's
anchor *is* the world's last observed frame, so it cannot have drifted from it.
Reporting that as a result would be reporting a definition. The measurement is
the consequence:

```
                              contains the world's answer   frontier width
rolled   × ablation   (today)          5 / 52               2 on all 52
observed × ablation   (this change)   25 / 52               2 on 48, 1 on 4
rolled   × generated  (R2)            43 / 52               5, 6, 8, 10
observed × generated  (both)          43 / 52               3, 6, 8

on the 35 drifted probes only:
rolled   × ablation                    0 / 35
observed × ablation                   20 / 35
rolled   × generated                  30 / 35
observed × generated                  30 / 35
```

Read out:

* **Anchoring alone takes containment from 5 to 25 of 52 — a 5× gain at
  unchanged width.** Every one of the 20 recovered on the drifted subset is the
  `manual` hypothesis being right once it is asked about the right frame.
* **The subsumption is exact, not approximate.** `manual` under the observed
  anchor is right on 25 probes; `world_anchored_manual` is right on 25.
  `inert` under the observed anchor is right on 4; `world_inert` is right on 4.
  They are the same predictions, which is provable from the definitions and is
  pinned as a test rather than left as a measurement.
* **Anchoring makes the generated frontier cheaper for the same answer.**
  `observed × generated` gets the same 43 as `rolled × generated` at widths
  `[3, 6, 8]` instead of `[5, 6, 8, 10]`, because two of R2's four generators
  collapse onto hypotheses the ablation family already had. The two that
  survive as distinct are the `*_edge` pair, which are about expressivity — a
  board cell no rule can name — and not about anchoring.
* **The 9 still missed by `observed × generated` are R2's 9, unchanged**:
  `r2 P-01/P-02/P-04`, `r3 P-01/P-02/P-04` (opening probes, no history for an
  edge chain) and `sk48-l1 P-03/P-06/P-09` (correctly anchored, one virgin
  board cell each). Anchoring was never going to reach them; they are the
  expressivity residue and they remain open.

**The cost, stated rather than buried.** On 4 of the 52 the anchored ablation
frontier collapses to **width 1** — every hypothesis predicts the same frame
once they are all read against the world's. Entropy is then 0 and
`design` returns no best action, so the arm refuses to spend an action. That is
the right refusal (an action that cannot separate anything buys nothing) but it
is a real behavioural change: 4 probes that were bought on the rolled anchor
would not be bought on the observed one.

---

## 5. The divergence, per turn, per leg — `DRIFT.json`

Item 4's deliverable and the thing nothing reported. Read off `certify`'s own
replay, under the manual **the leg finished with**, over the leg's whole
history. `cells_wrong` is out of 4096 on every leg.

| leg | transitions | drifted | max | mean | last | max per certify round |
|---|---|---|---|---|---|---|
| `20260731T1240Z-A3-level2-carried` | 5 | 4 | 25 | 5.80 | 25 | 25 |
| `20260731T1310Z-…-r2` | 13 | 4 | 2 | 0.46 | 2 | 6, 6, 6, 0, 2 |
| `20260731T1430Z-…-r3` | 29 | 0 | 0 | 0.00 | 0 | 23, 0, 0, 0, 0, 0, 0, 0 |
| `20260731T1500Z-…-sk48-carried-l1` | 17 | 10 | 96 | 6.24 | 0 | 96 × 9 |
| `20260731T231654Z-R1-g50t-a` | 9 | 0 | 0 | 0.00 | 0 | –, 0, 4, 0 |
| `20260731T231654Z-R1-sk48-b` | 5 | 1 | 96 | 19.20 | 0 | –, 96 |
| `20260801T001851Z-R1b-g50t-a` | 21 | 5 | 1 | 0.24 | 0 | –, 0, 0, 0, 1, 1, 1, 1 |
| `20260801T001851Z-R1b-sk48-b` | 5 | 1 | 96 | 19.20 | 0 | –, 96, 96 |

Eight legs, not six: the four of 2026-07-31 plus R1's two and R1b's two. All
eight measured; none refused.

**Two readings, and their disagreement is the point.** The table above is the
manual the leg *ended with*. At the moment the probes were actually designed,
under the manual then in force, the drift was:

```
0 cells   17 probes
1 cell    20 probes
2 cells    5 probes
6–7        2 probes
23–25      8 probes
```

35 of 52 non-zero. The end-state table understates the bill because theorize
repairs the manual and the repaired one replays clean — `r3` is the extreme
case: 23 cells wrong at its first certify round, 0 at every round after, and
21 of its 28 probes designed while it was still wrong.

**A one-cell error is fatal to the frontier.** 20 of the 35 drifted probes are
off by exactly one cell out of 4096. Predictions are compared by whole-frame
hash, so 1/4096 wrong and 96/4096 wrong are the same answer: no hypothesis
matches. That is why the drift number is worth reporting as a magnitude and why
the failure looked catastrophic when the manual was mostly right.

**The negative control, which is the reason to believe the rest.** Two of the
eight legs — `r3` on its final manual, and `R1-g50t-a` — report **zero drift on
every transition**, and `R1-g50t-a` reports it on all four of its certify
rounds. An instrument that had never been seen to say "no drift" would not have
been shown to be measuring drift. It says no.

---

## 6. What shipped

`inner/anchor.py`, threaded through `inner/probe.build_hypotheses` and
`design`, `inner/loop.TheoriaArm`, and `harness/run.py --anchor
{rolled,observed}` — exactly the plumbing `--goal-protocol`,
`--probe-economy`, `--desk-diet` and `--frontier` already use, one path.
`THEORIA_ANCHOR=observed` as a positive whitelist: `1`, `true`, `OBSERVED`,
`observed!` and the empty string all leave it on `rolled`.

`rolled` is the default and is byte-identical: same hypotheses, same order,
same ids, same predictions, and `design`'s report grows no key. Four tests pin
that, including one that passes `anchor=` *while on the default*, because the
way this breaks is that the new path leaks into the old one and every leg that
left the switch off silently runs a different arm.

**`certify` was not touched, and a test enforces that it stays untouched.**
`test_certify_never_reads_the_anchor` asserts that no function in
`inner/certify.py` takes an `anchor` parameter, that the module's source
contains neither `anchor` nor `_roll_forward`, and it will fail the day someone
wires the two together. The instrument is protected by a check, not by a
paragraph.

**`GAPS.md` R2-1 is closed, and not by paying its price.** R2 could not give a
default leg its own drift reading because the reading had to go into a report
that already existed, and byte-identity was worth more. This writes the
per-turn series to **`anchor.jsonl` and `anchor.json`, files that did not exist
before**, so every leg from now on reports its own drift and no existing
artefact moves a byte. The `--anchor-measure` flag additionally puts the block
inline in `design`'s report, for a leg that wants it there.

### The negative control on the change itself

`test_no_drift_means_no_change`: on a manual that has not drifted,
`render(state)` **is** the world's frame, the transplant is the identity, and
every anchored prediction is byte-identical to the rolled one, hypothesis for
hypothesis. `test_drift_means_the_predictions_move_and_the_anchor_is_the_world`
is its partner, so neither is vacuous. A switch that changed the answer even
when there was nothing to correct would not be re-anchoring, and no number
taken through it would mean anything.

---

## 7. The falsifiable prediction

Written before any live leg runs it, and against the archive rather than in
place of it.

| quantity | today (`rolled × ablation`) | predicted with `--anchor observed` |
|---|---|---|
| frontier width | 2 on 52 of 52 | **2 on most, 1 on some** — unchanged or narrower, never wider |
| off-frontier rate | 47/52 = 90.4% | **≤ 60%** (the replay says 27/52 = 51.9%; the allowance is for a live leg diverging after its first probe) |
| `information_gain_bits` realised | 0.000 on all 52 | **> 0 on at least a third of completed probes** |
| probes refused for a collapsed frontier | 0 | **> 0** — width 1 is now reachable, and 4 of the archived 52 would hit it |
| drift reported | never | **every turn, on every leg, whatever the switch is set to** |

**What refutes it**, as opposed to merely disappointing:

1. **Off-frontier rate stays above 80% with the anchor on.** The replay's 25/52
   rests on `manual` being right about the *mechanism* and wrong only about the
   frame. If a live leg is correctly anchored and `manual` still misses, the
   diagnosis was wrong and the anchor is not the binding constraint.
2. **The frontier collapses to width 1 on most probes.** Then anchoring has not
   fixed the experiment, it has abolished it, and the arm will explore blind
   instead of probing. 4 of 52 is tolerable; a majority is a different change.
3. **Drift measured live is 0 throughout on a leg whose probes still land
   off-frontier.** That would say the 35 was a property of those four legs and
   not of this arm, and the change would be solving a problem this game does
   not have.

Explicitly **not** predicted: that this completes a level. Nothing here was run
against ARC.

---

## 8. What this does not do

* **No live evidence.** The programme is over its spend ceiling and this
  ticket had zero spend authority. Every number here is off the archive. What a
  live run would settle, and what it would cost, is in §9.
* **The replay is a counterfactual for the frontier, not for the leg.** A real
  leg diverges after the first probe whose answer differs, and 4 of the 52
  would not have been bought at all under the observed anchor. `(5, 25, 43,
  43)` of 52 is containment on the recorded states, not a forecast of a leg.
* **The expressivity gap is untouched and is now the whole residue.** The 9
  probes `observed × generated` still misses are the same 9 R2 missed. 12 of
  R2's 47 were never about anchoring, and `GAPS.md` R2-2 still holds: a
  confirmed edge hypothesis is a fact this arm can predict and cannot write
  down, because the DSL cannot state a rule about a cell it has no instance on.
  That is a grammar change and belongs to `theory-compiler`.
* **`certify` still has only one layer here.** Nothing in this change touches
  `GAPS.md` GAP 3: both Lean routes remain shut on a real ARC level, so the
  replay this change is protecting is still the *only* check the arm has, which
  is precisely why it was protected.
* **The drift series is per certify beat, not per turn, on the archive.** The
  live arm records it per probe beat (`anchor.jsonl`); the archived legs can
  only be re-measured where a certify report exists to verify the
  reconstruction against. Turns between certify beats are not measured and are
  not reported as zero.

---

## 9. What a live run would settle, and what it would cost

Not run. No spend authority, and this says so rather than leaving the reader to
infer it.

A live A/B is **one leg**, not two: the archive already supplies the `rolled`
arm on the same games, and `anchor.jsonl` now makes any future `rolled` leg
report its own drift, so the control is free. The `observed` leg is the only
new spend.

* **Shape:** one carried leg on `g50t-5849a774` or `sk48-d8078629`,
  `--anchor observed`, the same budget the R1b legs ran on.
* **Cost basis, measured not projected:** R1b's two legs are the nearest
  comparable and `GAPS.md` E3-3 is the warning against projecting from a cold
  run's basis. A carried leg's desk call was measured at **$2.695** on sk48;
  R1b-g50t-a spent 21 transitions across 8 certify rounds. A leg of that shape
  is **6–7 desk calls, roughly $16–19**, on the same arithmetic `BUDGET_PLAN`
  uses and with the same 2.1× carried-manual premium already in it.
* **What it settles, and nothing else does:** whether `manual` on a correctly
  anchored frontier is *right* — the replay says 25 of 52 on recorded states,
  but a live leg's states are the states this change itself produced, and the
  first probe whose answer differs makes every later state unshared with the
  archive. Refutations 1 and 2 above are only decidable live.
* **What it does not need to settle:** the drift magnitudes. Those are measured
  here, off the archive, at no cost, and a live leg would add an eighth and
  ninth number to a series that already has eight.
