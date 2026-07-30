# Fact-check round 1 — the six rows, against the artefacts

Independent subagent, read-only, worktree `.worktrees/p17-machine-checked` at
`78c76bdf`. Condensed; the classifications and every quoted field were taken
from the artefacts, not from the paper.

## Counts — and the item's premise is wrong

| kind | rows |
|---|---|
| Lean kernel proof (**L**) | **1** — row 5, and only its Lean half |
| property computed from an artefact (**A**) | **5** — rows 1, 2, 3, 4, 6 |
| a clause refuted (**R**) | **0** |

**No row is refuted.** All six clauses of `Theoria.md` §1.3 are *confirmed*. The
board item's statement of the facts — "还有一行是被一次 episode 反驳的" — is a
misreading of row 6's `result` cell, and so was my own first reading of it. See
§5 of `RULING.md`.

`refutation.json:49` says plainly what the word points at:

> `"verdict": "REFUTED — the episode ends on the goal cell with win=true, so the
> machine-checked, axiom-free theorem `unsolvable` is false of the world.
> Nothing in the proof is broken: it is true relative to the manual, and the
> manual is missing a rule."`

The refuted object is the **theorem**. The clause 而这一关人类可解 is confirmed,
in 18 actions.

## Row 5 — what is and is not a proof

**The Lean half is real.** `cold-start-a2/theory/generated_holed/theory.lean:784`,
`theorem unsolvable : ¬ ∃ s : St, Reachable s ∧ Goal s = true`, discharged by
`rintro` + induction on `Reachable` with `decide` at `init` and `step`;
`#print axioms unsolvable` at `:791`; 148 states declared at `:3`; no Mathlib
import anywhere in the file, no `sorry`, no `native_decide`.
`exhibit_report.json:31-44` records `returncode: 0`, `errors: []`, `sorries: []`,
`axiom_reports: [{"axioms": [], "name": "unsolvable"}]`, `green: true`, against a
real `lean.exe` 4.9.0.

**Three qualifications the row does not carry.**

1. **The plan half is not a complete search.** `cold-start-a2/a2pipeline/plan.py:69`
   calls `fd_adapter.solve(..., prefer="stub")` — the bundled BFS stub, not Fast
   Downward. `cold-start-a2/A2_REPORT.md:277` says so itself. `plan_holed.json`'s
   `"backend": null` is not evidence of FD; it is `None` because `plan is None`
   on UNSAT (`plan.py:82`). The clause being matched is 完备搜索 — "complete
   search" — so this is the half of the row the clause actually names.
2. **The paper's own §5.8 undercuts the plan half, and the table does not say
   so.** D-A2-006: `gen_pddl_a0` cannot ground a teleport, so the planner returns
   UNSAT on a manual *containing* the rule too. A verdict that is UNSAT either
   way is not evidence about the hole. §5.8 states this defect six subsections
   later; nothing connects the two.
3. **`#print axioms` raw output is not in the record.** `certify_a2.lean_brief`
   (`cold-start-a2/a2pipeline/certify_a2.py:126-128`) drops the `output` key. The
   literal line `'unsolvable' does not depend on any axioms` appears nowhere in
   `cold-start-a2/artifacts/` or in `cold-start-a2/A2_REPORT.md`. The `[]` is a
   regex parse (`cold-start-a0/certify/lean_check.py:27`) of a real run — faithful,
   but a parse. Re-running needs a Lean 4.9.0 toolchain the repo does not ship;
   without it `certify_a2` reports red rather than passing silently
   (`cold-start-a2/a2pipeline/certify_a2.py:80-84`), which is the right failure mode.

## Smaller mismatches, row by row

* **Row 1** — `engines_diff.json:40-57` backs `obj1_jump_DOWN`, `coverage 1/1`,
  effect `{dx: 2, dy: 1}` so |dy|+|dx| = 3 > 1. But that list sits under the
  **`candidates.jsonl`** key, whose own note reads *"the full sweep, teleport
  included"*; the parallel `candidates_history.jsonl` block has
  `rules_with_a_jump_effect: []` (`:103`). "The only proposal" is true **of the
  sweep**, and the row does not say which stream.
* **Row 2** — `history_omits_exactly_one_pair: true`,
  `history_omitted_pairs: ["cart=(6,4) pressed=1 act=DOWN"]`
  (`trace_summary.json:3-6`); the cell matches byte-for-byte. But the
  `(compressed)` label is backwards: 缺的那条传送规则从未触发 is **verbatim** in
  `Theoria.md:36`. The paper restored the full wording, kept the "compressed"
  tag, and dropped the quotation marks.
* **Row 3** — `certify_cheap` records `frames: 184`, `transitions: 183`,
  `pixels_checked: 14904`, `pixels_unexplained: 0`, `anomaly_kinds: []`
  (`exhibit_report.json:2-9`). **`184/184` is not a field and not a ratio the
  artefact computes** — the units checked are 183 transitions and 14 904 pixels.
  **`0 anomalies` is a reading, not a recorded count**: there is no `anomalies`
  key under `certify_cheap`; the only `anomalies` integer in the file is `44`,
  under `certify_cheap_vs_full_sweep` (`:11`). Both statements are *true*; neither
  field exists at the cited path.
* **Row 4** — exact. `engines_diff.json:113`,
  `history_proposes_a_jump: false`, computed at `engines.py:130` as
  `bool(history["rules_with_a_jump_effect"])`. Same backwards `(compressed)` tag:
  模型重放 175/175 全对 is verbatim in `Theoria.md:36`.
* **Row 6** — numbers right: `refutation.json:14-42` gives `length: 18`,
  `frames: 19`, `win_frames: [18]`, `final_win: true`; `solved_episode.jsonl`'s
  last record is `{"action": null, "t": 18, "win": true}`. The cell quotes
  `win: true` (the JSONL key) while §5.5 line 159 cites `final_win` (the JSON
  key) for the same event.

## Artefacts

**None missing.** All six cited paths plus
`cold-start-a2/theory/generated_holed/theory.lean` exist in this worktree and are
in `git ls-files`. Every row can be re-run except row 5's Lean gate, which needs
a toolchain recorded at a machine-local absolute path.
