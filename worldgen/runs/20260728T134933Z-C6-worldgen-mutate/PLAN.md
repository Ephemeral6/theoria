# C6 · plan, fixed before any code was written

## What the item asks for

`worldgen/mutate.py`: a built world + one rule-level edit → new world + new ground
truth + a **machine-readable description of the edit**, from which the exam can
compute 检测延迟 / 修复成本 / 连带作废. Four edit families (forbid an action,
change a guard, turn a reversible mechanism irreversible, move a portal exit),
≥2 instances each, factory inspection as in C1.

## What the survey found (before deciding anything)

`exam/runs/20260728T090621Z-V2-exam-on-worldgen/GAPS.md` states the blockage:
"[worldgen's] semantics live in mechanism classes' `interact()` bodies; push
distance is one cell because `mechanisms/push.py` says so in code, not because a
parameter says so."

That is true of push. It is **not** true of most of the catalogue. `Entity.props`
is already read at every decision point that matters:

| mechanism | prop read in `interact`/guards | file:line |
|---|---|---|
| `switch_door` | `mode` (toggle/latch) | `mechanisms/switch_door.py:132` |
| `switch_door` | `polarity`, `net` | `:89-92`, `:84` |
| `count_lock` | `k` on a lock | `mechanisms/count_lock.py:63` |
| `color_cycle` | `k`, `open_phase`, `phase0` | `mechanisms/color_cycle.py:72-79` |
| `portal` | `mode`, `dest`, `pair` | `mechanisms/portal.py:98-110` |

So three of the four families are edits to an **existing** parameterisation that
nobody had declared or enumerated. The fourth — forbidding an action — has no
knob anywhere and needs one.

**Decision.** Do not retrofit a second parameter system. Declare the one that
exists (`KNOBS` in `mutate.py`: which props are semantic knobs, their domains,
which mechanism reads them, which edit family they belong to), add exactly one
new engine knob (`flags["forbidden_actions"]`, read in `GridWorld.explain`), and
back the declaration with a test that every declared knob demonstrably changes
the transition function. A knob table nothing checks is prose.

Blast radius of the new knob: zero when the flag is absent, which it is for all
twenty catalogue worlds, so their artefacts stay byte-identical.

## Admission into the exam, without touching `exam/`

`exam/guard.py:57-70` admits a generated world iff its id is a row in
`worldgen/out/worlds/INDEX.json → worlds[]`; `exam/papers/worldgen_port.py:61-67`
then opens six files from `out/worlds/<id>/`. So mutants must ship the full
six-file set in that directory and appear in that index. They will.

They must **not** join `generate.CATALOGUE`: `tests/test_catalogue_invariants.py:108`
asserts the catalogue has exactly one unsolvable world, and several mutants are
deliberately unsolvable (which is itself an exam need — GAPS.md: "Only one world
is unsolvable. The paper needs nine"). Mutants therefore come from
`mutate.mutant_specs()` and `build.py` builds `CATALOGUE + mutant_specs()`, so
all six build gates and the determinism gate apply to them unchanged.

Ids are opaque handles (`v-<digest8>-NN`), per the leak incident recorded in
`monitor/inbox/archive/…-W-1540-…md` §三: "世界 id 是**词**，不是不透明句柄"
— `t2-unsolvable-nodoor` printed the answer to an adaptation item.

## The three metrics, and which of them worldgen can actually close

* **检测延迟 — closed here.** Exact, by BFS over the *product* graph
  `(state_base, state_mutant)` from the two initial states, edges labelled by the
  same action, stopping at the first pair whose rendered frames (or win bits)
  differ. Depth = the fewest actions any prober needs before the change is
  observable. `null` ⇒ the edit is observationally equivalent on the whole
  product graph, which is the undetectable variant `exam.papers.adaptation.build()`
  refuses to ship a paper without. Also reported per concrete stream (the base
  world's own `raw_trace.jsonl`, the base world's optimal plan) with stream
  length and completeness, so a truncated stream can never read as "never".
* **连带作废 — closed here.** `rules_falsified` measured in both directions from
  the product graph; `claims_now_false` = base invariants that fail on the
  mutant's reachable set; `claims_to_reexamine` from a computed claim→rule
  dependency graph (the artefact GAPS.md names as missing), over-approximating on
  purpose — "re-examine" is the safe direction to err in; verdict + verdict_flipped
  from the exhaustive solvability decision.
* **修复成本 — partly. Says so.** GAPS.md blocks the real number on a
  mechanism-aware miner in `engine-rig`, which is another territory. What ships
  is what worldgen owns: the divergent-observation count, the divergent
  rule-pair classes, and a greedy witness budget (shortest walk that witnesses
  every divergent class). The miner-measured field is emitted as `null` with the
  blocker named, not omitted and not faked.

## Order of work

1. `forbidden_actions` knob + rule tag + tests; rebuild the twenty and prove
   byte-identical.
2. `mutate.py`: KNOBS, operators, `apply`, `mutant_specs()`.
3. Descriptor computation (product BFS, collateral, repair proxy).
4. Wire into `build.py` (gates + determinism + INDEX) and `run_qc` (sampling).
5. Adversarial review of my own conclusions by independent subagents.
6. `verify.py` green, RUN_STATE, PARTNER_SYNC, push.
