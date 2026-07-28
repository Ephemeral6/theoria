# C2 migration plan — a0-spike, dsl_grammar v0.1 → v0.2

**Run** `20260728T040057Z-c2` · **branch** `agent/c2-semantics-migrate` ·
**base** `c47366c`

## The failure, restated

`a0-spike/pipeline/gen_exec.py:30` imports `theory_compiler.parser.theory_parser.parse_theory`
— the theory-compiler track's parser. That parser now raises `SemanticsError` on a
manual with no `semantics:` section (v0.2, revision item 1, ledger E-03).
`a0-spike/theory/theory.dsl` is v0.1. Every test that reaches the compiled form
dies at the same line; the whole 32 are one root cause.

The mechanical fix is three lines. **The mechanical fix is not the task.** The
contract's own migration note says it in as many words:

> **Do not copy these three values from another manual.** They are per-world
> facts. […] If you do not know which is true, that is a finding to probe, not a
> default to accept.

So the deliverable is three *adjudications about the A0 world*, each with
evidence, not three lines that make the parser stop complaining.

## What makes this hard

Only one of the three is obvious by inspection.

* `frame` — near-certain `persist` from `world/sokoban2.py:step`, which returns a
  new `State` carrying the unmentioned object through unchanged. But "near-certain
  by inspection" is exactly the standard this section exists to raise.
* `conflict` — needs the pairwise-disjointness argument actually *done*, over the
  five rules of the manual, and it has a trap: `push2`'s event `slid(Box, dir)`
  is **compound** — `gen_exec._compile_effect` moves the Box two cells *and* the
  Player one. v0.2 §"Discharging `conflict`" makes the obligation **per object**,
  ranging over rules whose claimed objects intersect. So `push2` must be treated
  as claiming Player as well as Box, which is the *wider* obligation. Reading the
  event name alone would understate what has to be proved.
* `cascade` — the one the dispatch flagged: does a two-cell slide count as a
  cascade? Naively "the box passes through a cell, so there is an intermediate
  frame" argues `multi_frame`. I believe that is wrong and that the honest
  discriminator is different (below), but it is a real question and gets a real
  experiment.

## Method — falsify, don't confirm

For each of the three, the probe compiles the manual under **both** readings and
replays the world. A value is adjudicated by its opposite being **refuted with a
concrete witness**, not by the chosen one merely fitting.

| statement | the discriminating experiment |
|---|---|
| `frame persist` vs `reset` | under `reset`, an object no firing rule mentions returns to its declared initial value. Walk the player anywhere; the Box is mentioned by no firing rule. `reset` therefore teleports the box home on every walk. Witness expected on transition 1. |
| `conflict exclusive` vs `priority:` | exhaustive sweep (v0.2 route 2) over **every representable** (state, action) of all five evidence levels — not the reachable ones (D-TC-012). For each, count rules that fire *and claim a common object*, under the wide reading of `slid`. `exclusive` holds iff that count never exceeds 1. If it exceeds 1 anywhere, `exclusive` is false and a priority order is the honest declaration. |
| `cascade single_frame` vs `multi_frame` | under `multi_frame` the rules re-fire on each intermediate state, **holding the action**, until quiescence. Every A0 rule guards on `act=move(Player, dir)`, so the action does not clear — `walk` re-fires, and the player slides until it hits something. One `move(Player,UP)` across open floor moves the player *many* cells instead of one. The world moves it one. Witness expected immediately. |

Note what the third row settles the two-cell question with: the slide is not a
cascade because the box's two cells are **one rule's effect**, applied whole.
`multi_frame` is not "an effect spans two cells", it is "the rule set is re-run".
Those come apart, and the experiment separates them.

The exhaustive sweep is the same instrument `report["held_out"]` already uses
(39,960 states across five levels, 0 mismatches). Reusing it means the `frame`
and `cascade` refutations are measured on the identical state set that certifies
the manual today — so a witness cannot be dismissed as an artefact of where I
looked.

## Steps

1. `probes/semantics_probe.py` — the three experiments above, deterministic,
   writing `runs/<id>/semantics_probe.json`. Ground truth (`world/sokoban2.py`)
   is used only to grade, per `stages.py`'s standing rule.
2. Adjudicate from the probe's output. If a value comes out other than expected,
   the manual gets the measured value, not the expected one.
3. `theory/theory.dsl` gains `semantics:` after `word_table:`, before `events:`,
   each line carrying its evidence pointer.
4. `THEORIZE_LOG.md` T-11, one sub-entry per statement: proposal, evidence,
   adjudication, cost.
5. Regenerate the four forms; `python -m pytest` green; `python -m pipeline.run_a0`
   exits 0.
6. Adversarial subagent: *does the declared semantics describe this world* — read
   against `world/`, not against the parser. Its report lands in the run dir
   unedited whatever it says.
7. Expressivity ledger: `THEORIZE_LOG.md` gains a §表达力台账 (a0-spike has none;
   `gen_exec.py:137` already claims to have filed against one). Known candidate
   entries: the compound `slid` event, and `stayed` rules that `frame persist`
   entails but `gen_exec`'s totality-by-coverage still requires.
8. `verify.sh` — tests green **and** the four forms regenerate byte-identically.
9. `runs/` back-filled to the canon (OPS-A's留痕 gap): `MANIFEST.json` with
   `prompt_id` / `branch` / `base_commit` / `utc` / `files[].sha256`.

## Standing constraints

* Territory is `a0-spike/`. `theory-compiler/`, `cold-start-a0/`, `engine-rig/`
  are read-only here; if v0.2 cannot express something, it goes in the ledger and
  to PARTNER_SYNC, and **not** into a hand-edit of the contract or the parser.
* Branch only. master is not touched.
* If the probe refutes the value I expect, the probe wins.
