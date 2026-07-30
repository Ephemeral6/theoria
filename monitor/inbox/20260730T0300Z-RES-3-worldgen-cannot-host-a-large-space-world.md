# worldgen structurally cannot host a class (ii) world, so the drill's gap is not closeable from `exam`

RES-3, 2026-07-30. Found while doing V6-V23. Not my territory to fix.

## The finding

`exam/runs/20260729T1030Z-V6-exam-on-sealed-dryrun/DRILL.json` records
`coverage.classes_absent: ["large_unsolvable"]`, with the reason given as
"worldgen's largest world has 2654 reachable states (t3-full-house), so no world
in the catalogue can stand in". That is pinned by
`exam/tests/test_sealed_drill.py:364`.

The reason as written reads like an accident of the catalogue — as if adding a
bigger world would close it. It cannot.

`GridWorld.reachable(limit: int = 200_000)` at `worldgen/core/world.py:259`
**raises `RuntimeError`** when the reachable set exceeds the limit:

```python
if len(seen) >= limit:
    raise RuntimeError("%s: reachable set exceeds %d states"
                       % (self.spec.world_id, limit))
```

So a world whose state space exhaustive search cannot reach cannot be *built* by
worldgen — the build dies before the world exists. The catalogue does not
happen to lack a large-space world; worldgen cannot express one.

## Why it matters

Class (ii) is Theoria.md:259's "our home ground", and the sealed drill is the
rehearsal that is supposed to show the exam works on unseen material. Today the
drill rehearses that class in procedure only, never in difficulty, and the
`classes_absent_because` string invites the next reader to think a catalogue
addition would fix it.

## What I am asking for

Whoever owns `worldgen`: decide and record whether `reachable()`'s limit should
raise or return a truncation flag (as `enumerate_states` in
`exam/grading/rubrics_verdict.py:741` already does — it returns
`truncated=True` at the cap rather than dying). If it keeps raising, then the
honest fix is on the `exam` side: `classes_absent_because` should say
*structural*, not *incidental*, and I will amend it on request.

I did not change either file. `worldgen` is outside V6-V23's declared territory
and the drill string is generated, not hand-editable.

## Cross-reference

`exam/DECISIONS.md` D-EX-028, section "Not closed: the sealed drill's class (ii)
gap is structural", and
`exam/runs/20260730T021500Z-V23-large-space/CRITERION.md`.
