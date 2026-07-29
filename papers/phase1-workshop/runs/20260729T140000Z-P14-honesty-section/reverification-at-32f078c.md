# Re-verification of every source claim at `32f078c`

`evidence-survey-located.md` was audited against `b05e1c9`. Master moved before
the section was written, so the branch merged `origin/master` (merge commit
`32f078c`) and **every load-bearing claim was re-read against that tree** by an
independent pass. This file records the result. Where a line number here differs
from the one in `evidence-survey-located.md`, **this file is the current one.**

## Nothing was overturned

No repair regressed, no figure moved, no artefact changed. The differences are
line drift inside files that were edited elsewhere.

| Claim | Status at `32f078c` | Current lines |
|---|---|---|
| `p13_fd_dividend.py` writes `unsolvable` via the predicate | repaired | `:171`; `exhausted_reported` `:172` |
| `backends.FD_SEARCH_UNSOLVED_INCOMPLETE = 12` | unchanged | `:74`; `FD_EXHAUSTED` `:88`; `proves_unsolvable` `:239-270`, decision at `:268-270` |
| `worldgen/core/truth.py` `.get("holds", True)` | **still live** | `:279`; prose append without `holds` `:195-200`; verified branch sets it `:218`; honest renderer `:333-334` |
| `a0-spike/pipeline/stages.py` crash split | repaired | `NoSeparatingGuard` `:375` (reason `:379`); `except Exception as exc` `:388` (reason `:392`, `record_crash` `:393-394`); `all_guards_searched` `:276-277`, published `:290` |
| `theoria-arm/inner/plan.py` crash routing | repaired | `crashes.record` `:303`; `step_crashes` `:230`; `if crashes.count:` `:320` → `unsat_unsound` `:322`, `exhaustive: False` `:323`; clean path `:336` |
| `lp_potential` only status 2 returns `None` | repaired | `HIGHS_INFEASIBLE = 2` `:34`; `LpUnavailable` `:41`; guard `:211`, raise `:212-217`, `return None` `:218` |
| `"admissible"` derived, not a literal | repaired | `:357`; `entitlement()` `:294-336`, its `admissible` `:335` |
| `bench/ladder.py` gold standard | unchanged | over-budget dict `:75-82`, `proved_unsolvable: False` `:77`, `error` `:80`; `STUB_MAX_EXPANSIONS = 200000` `:51`; published `:226`; the exclusion `:248` |
| `validate_plan` unconditional on all rungs | unchanged | `solve_parsed` `:79`; no-plan returns `:117`, `:128`; `validate_plan(...)` **`:140`**, unguarded; `return` `:141` |
| `validate.py` does not import the searcher | unchanged | imports are `:25` and `:27-32` only; the word `search` occurs solely in the docstring (`:1,3,4,9,14`) |
| `deadlock_carver` gate | repaired | `WITHHOLD`/`MARK` `:161-162`; `refutation()` `:166-189`; `candidates()` `:192`; gate `:226`; MARK path `:236`; `UnfinishedComparison` class `:47`, raised `:100-105` |
| `zero_space` truncation bit not in the payload | **still open** | `SUBSET_ENUMERATION_LIMIT = 8` `:145`; truncation `:175-177`; `Law.scope_exhaustive` `:45`, set `:221`; `as_json` `:75-92` emits 8 keys, none of them `scope_exhaustive`; deferral comment `:76-82` |
| `zero_space.verify` circular | **still circular** | `verify()` `:235-243`, encodes the passed `states` at `:237`; caller `__init__.py:51-52` passes the fitting `states` |
| `dividend.json` three `fd_unsolvable: true` | unchanged | 7 `cross_check` rows; the three are `a0-spike/mismatch`, `cold-start-a0/no-button`, `cold-start-a2/holed`, each `fd_exit_code: 12`, `agree: true`, `stub_unsolvable: true`; row keys carry no `fd_rung` / `fd_answered` / `fd_exhausted_reported`; still one commit, `cf400ce` |
| `ENGINE_TABLE.md` 29.2 % | unchanged | `:23`, `:109`; provenance row `:249` still cites the reviewer's E11 partial |
| Z-S2 `delta_hit` 13.1 % | unchanged | `:225`; laws 1680 `:226`; cell_local 92.9 `:229`; novelty 7200/7200 `:230-231` |
| L-L1 26.4 % of 1408, 58 false | unchanged | `:219`, `:211`, `:212`; all 58 emitted under partial evidence `:213`, `:215` |
| the standing rule on 已验证 | unchanged | `:69` heading, `:71-72` rule |
| synthetic corpora only | unchanged | `:100-105` |
| held-out marker is a biconditional in test | unchanged | `test_engine_table.py:96,98,99` |
| `candidates.jsonl` carries both dual fields | unchanged | line 22 `kind: heuristic` (`admissible` + `admissibility_check` + `admissible_basis`); line 41 `kind: plan` (`plan_length_unchanged: true`); both `status: "candidate"` |

## Two branch facts the section depends on

`git merge-base --is-ancestor <branch> 32f078c`:

| branch | in HEAD? |
|---|---|
| `agent/c11-tool-failure-as-truth` | yes |
| `agent/e14-crash-is-not-a-finding` | yes |
| `agent/e16-verdict-must-gate` | yes |
| `agent/e17-held-out-validation` | yes |
| `agent/e15-solver-status-bit` | **no** |
| `agent/v19-unverified-is-not-true` | **no** |

* **`e15` is unmerged but its subject is repaired anyway** — the `lp_potential`
  status fix reached the mainline through other commits, which is why `:211-218`
  above is present at HEAD. The branch not being merged is not evidence the fix
  is absent, and the section does not claim it is.
* **`v19` is unmerged and its subject is *not* repaired.** `truth.py:279` is
  byte-identical to the surveyed line. The board records the item as done. This
  is the discrepancy §10.2 reports, and it was re-checked here rather than
  inherited from the earlier audit.

## The census reports are still on no ref

Re-checked 2026-07-29T14:45Z. All four `SURVEY-*.md` remain `??` untracked in
`.worktrees/e11-engine-crosscheck-deep/`; `origin` still carries no
`agent/e11-engine-crosscheck-deep`. The copies in `inputs-verbatim/` are
byte-identical to the originals (sha256 in `MANIFEST.json`, re-compared at that
time). §10.7 of the paper says this in the paper's own voice.

## One count corrected against the earlier audit

`evidence-survey-located.md` §G.5 reported **8** occurrences of "verified" in
`PAPER.md`, at the line numbers of `b05e1c9`. At `32f078c` there are **7**, at
lines 177, 429, 922, 942, 1545, 2819, 2884 of the pre-insertion `PAPER.md`. The
characterisation is unchanged and the conclusion is unchanged: none of them is a
claim to have verified an engine, and 已验证 occurs zero times. The section
quotes the corrected count.
