# RUN_STATE — R3, the anchor duality

Narrative. The numbers live in `MANIFEST.json`, `DRIFT.json` and
`ANCHOR_REPLAY.json`; the argument lives in `README.md`. This is what happened
and in what order, including the two things that turned out not to be true.

## What was asked

The deepest defect found on 2026-08-01 and deliberately left unrepaired,
because the obvious repair destroys an instrument. Design the honest fix,
recommend one, implement it switchable with default = today's behaviour,
measure it on the archive, and report the divergence per turn per leg as a
deliverable in its own right.

## The order things happened

**1. Read R2, then read the code, and found the tension is smaller than it
looks — and therefore fixable.** The brief says re-seating the state would make
certify's replay trivially green. That is true of a re-seat *in certify*. But
`certify.cheap` does not call `_roll_forward` at all: it keeps its own
`state = initial_state()` and its own replay loop. The two paths are already
separate. What is shared is not code, it is the *idea* that there is one answer
to "where is the manual now", and the ambition to re-use it. So the fix does
not have to fight certify; it has to give probe design its own anchor and put a
check in the way of anyone later merging the two. That check is
`test_certify_never_reads_the_anchor`, which asserts the module's source
contains neither `anchor` nor `_roll_forward`.

**2. Found that the state cannot be re-seated even if one wanted to.** `render`
is not injective. The generated `State` is one `<name>_pos` / `<name>_color`
pair per instance and many assignments paint the same grid, so "the state the
world is in" is not well-posed. That ruled out design D3 on its own terms and
pointed at what Job B actually needs, which is not a state but a *frame*.

**3. Implemented D2b.** Every hypothesis keeps its mechanism and only the frame
its answer is read against moves. Needed one refactor: `Hypothesis` is a frozen
dataclass whose `predict` returns a *hash*, and a hash cannot be re-anchored.
So `probe.ablation_grid_specs` now defines the family once at the **grid**
level and `build_hypotheses` wraps it — one definition, two consumers, and
`test_the_grid_specs_and_the_hypotheses_are_one_definition` pins that they
agree. The alternative (a second builder kept in step by hand) would break
silently, in the direction that makes the A/B compare two different arms.

**4. Wrote the drift meter and hit a contradiction.** The first version read
drift off the last certify round of each leg and reported `r3` at **zero drift
on all 29 transitions** — while R2 reported 21 of r3's 28 probes drifted. Both
turned out to be true and the reconciliation is the finding: certify's last
round replays the manual the leg *ended with*, and theorize had repaired it.
The probes were bought while it was still wrong. `DRIFT.json` therefore reports
per certify round as well as at the end, and `README.md` §5 gives both readings
side by side because the disagreement is the point.

**5. Suspected R2's harness and checked it.** R2's replay rolls the manual over
`[s.action for s in prefix.steps]`, which begins with the leg's `RESET`;
`_roll_forward` rolls it over `store.actions`, which is that list shifted by
one with a trailing `None`. Different action sequences. If they produced
different states, R2's headline 35 — the number this whole ticket is built on —
would have been an artefact of R2's own harness. Recomputed on every probe:
**equal on 52 of 52, disagreed on 0.** The number holds. It was worth an hour
to find that out rather than to assume it, because it would have been wrong in
exactly the direction that flatters the conclusion.

**6. Refuted a sentence this arm has been repeating.** "One mispredicted
transition desynchronises the manual's state permanently" is in R2's README and
in this ticket's brief. The archive says no: drift **recovers**, 8 events across
the 8 legs, on 4 of the 6 legs that ever drifted, non-monotone on those 4.
`sk48-carried-l1` runs `[96, 0, 0, 0, 0, 0, 1, 0, 1, 1, 1, 1, 2, 1, 1, 1, 0]`.
The manual's `step` is not injective, so a capped mover re-converges. This does
not weaken the case for the change — 35 of 52 probes were designed on a wrong
anchor and that is the operative fact — but it does mean the failure is "the
anchor is often wrong", not "wrong forever after the first mistake", and the
stronger sentence would have gone into the next round unexamined.

**7. Measured the 2×2 and found the subsumption.** `manual` under the observed
anchor is right on exactly 25 probes; R2's `world_anchored_manual` is right on
exactly 25. `inert` anchored is right on 4; `world_inert` on 4. They are the
same predictions, which is provable from the definitions and is now pinned as a
test rather than left as a coincidence of the measurement. So the anchor switch
subsumes half of `--frontier generated` and delivers it at width 2 instead of
5–10.

## The number that decided it

```
                              contains the world's answer   width
rolled   × ablation  (today)          5 / 52                2
observed × ablation  (this)          25 / 52                2 on 48, 1 on 4
rolled   × generated (R2)            43 / 52                5, 6, 8, 10
observed × generated (both)          43 / 52                3, 6, 8
```

Five times the containment at unchanged width, and it makes R2's change cheaper
rather than competing with it.

## What was deliberately not done

* **`certify` was not touched.** Not one line, and a test enforces it.
* **No eighth surprise.** `Theoria.md` 1.9 closes the taxonomy at seven and
  `inner/surprise.py` raises on an eighth by construction. Drift is not a new
  kind of evidence; it is the accumulated consequence of a `replay_mismatch`
  that has already fired and already paid for a desk call, so a second surprise
  would double-count against constraint 8's arithmetic and buy a paid call to
  hear the same news twice. It is a measurement attached to the surprise that
  already exists.
* **Nothing live.** Zero spend authority, and the programme is over its
  ceiling. What a live leg would cost ($16–19, one leg not two, because the
  archive supplies the control) and what it would settle is in `README.md` §9
  and in the manifest, so the next person does not have to re-derive it.

## Where the residue is

Four gaps, all in `GAPS.md` as R3-1 … R3-4. The one that matters most is R3-3:
with drift closed, the 9 probes still missed are entirely the expressivity
residue — a confirmed edge hypothesis is a fact this arm can predict and cannot
write down. That is a grammar change and belongs to `theory-compiler`.
