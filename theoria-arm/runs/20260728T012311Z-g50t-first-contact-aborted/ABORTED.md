# Aborted — first attempt at the first contact

**Aborted after 5 successful actions and one theorize call, by decision, not by
failure of the world.** The cause was a defect in this arm, it is fixed, and
the run is kept because the defect is worth more as evidence than as a memory.

## What happened

The opening sweep spent 5 actions (ACTION1–5 once each, 85 HTTP commands under
an active 400 wave). The engines dispatched on the resulting 6 states and the
desk wrote a first manual — a good one: it identified 4023 of 4096 cells as
board, decomposed the 73 varying cells into named regions, and checked its own
decomposition against the observed diffs by cell count rather than by eye.

Then the compiler refused it:

```
ProblemError: theory.dsl declares landmark(s)
['exit_cell', 'slot2_bar', 'slot2_glyph'] that problem 'level-1' does not locate
```

The manual was fine. **The arm was wrong.** `inner/books.problem_from_frames`
computed the level instance from the frames — board, objects, colours — and
emitted no `landmarks` key at all, while the grammar card invited the desk to
declare landmarks. A landmark the level cannot place is a hard error in
`check_against_theory`, and correctly so: the rule that names it has no value
to use.

Left alone, every theorize round would have paid $1.31 and ~9 minutes to be
told the same thing, and the desk's only available repair would have been to
delete the landmarks — losing `jumped(o, landmark)` and every goal of the form
`X.pos = landmark`, which is most of the expressive power the manual has for
saying where something goes.

## The fix

The desk now writes the coordinates on the declaration line
(`landmark exit_cell   # arc-cell: (7, 3)`), exactly as it already writes
`# arc-colour:` for objects, and `problem_from_frames` places them.
A landmark declared without a hint lands at the origin and is listed in
`landmarks_defaulted` rather than killing the compile.
`tests/test_arm.py::test_a_declared_landmark_is_placed_from_its_cell_hint` and
`::test_a_manual_declaring_a_landmark_compiles_once_the_level_places_it` pin
it. This is the second instance of the failure mode `DECISIONS.md` D-P8-014
names: an expressivity gap that was really a prompt bug.

## What this run is still evidence of

* **g50t returns up to 9 frames from one command.** The cascade lengths in
  `trace.jsonl` are 1, 7 and 9. `arc-recon`'s precheck recorded a maximum of 7,
  so this widens the observed bound on this game.
* **Eight retries is not enough to close a scorecard under a wave.** The close
  failed with 404 on all 8 attempts of `baseline-arms`' D-015 envelope and then
  succeeded on a retry with 40. Without that second attempt the card's score
  would have been permanently unrecoverable, since a closed card cannot be
  re-fetched and an unclosed one yields nothing. The default in
  `harness/arc.py` is now 40.
* **The scorecard, recovered:** `score 0.0`, `total_actions 5`,
  `levels_completed 0`, 7 levels, all `level_scores` zero. Five actions bought
  no progress, which is unsurprising on an opening sweep.
* **The desk's first manual is worth reading** — `desk/call-001-theorize-round1.md`.
  It cost $1.31 and 548 seconds for 43,066 output tokens on `claude-opus-5`.

## Cost of the abort

5 successful actions and $1.31, both of which are counted in this track's
totals rather than written off. The replacement run starts a fresh scorecard
and a fresh 120-action budget, as `INCIDENTS.md` and the final report record.

