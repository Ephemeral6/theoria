# E1 stops reading theorem names — F1, D1, D2 repaired, and the paradigm case attains

**Branch:** `r2/u3-kind` · **Base:** `af138a0d` · **UTC:** 2026-08-01T07:00Z
**Territory:** freeze · **Ask:** `monitor/inbox/20260801T0400Z-exam-to-freeze-u3-vacuous-label.md`
**Offline throughout.** Lean 4.9.0 only. No API call, no model call, no network,
no spend. Nothing under `theoria-arm/runs/*R1*` was read or written — this
worktree is at `master`, so the live R1 legs do not exist in it at all.

## The defect, in one line

`u3.classify_theorem` was a prefix matcher over theorem NAMES, so E1 — the
first of the three frozen primary endpoints — was a naming-convention detector.
`STATS_RULES.md:123` names the C4 sokoban deadlock development as *the*
paradigm of what U3 means ("它产出的、跨 28,672 个状态的死锁定理正是 U3 所指的那类
非平凡定理"); E1 called it **`vacuous`**.

## What was built

* **`freeze/theorem_shape.py`** (new). Parses a Lean development into
  declarations and per-theorem statement shapes, and classifies each theorem by
  **what it asserts over the development's own declarations**: `unsolvable`,
  `prune`, `invariant`, `point_claim`, `witness`, `unclassified`. The full
  argument for the criterion, and the frozen text it is read from, is in that
  module's docstring.
* **`freeze/u3.py`**:
  * `classify_theorem` is now `theorem_shape.name_hint` — reported as
    `per_theorem[t].name_hint`, read by nothing that decides anything.
  * `judge_nonvacuity` is three-valued (`True` / `False` / `None`) and takes the
    theorem's shape plus the whole development, so a sub-check can look for the
    co-theorem that discharges it.
  * **`prune` gets the §1.2.1 check it never had**, discharged from
    co-theorems, each of which must have passed (b) itself.
  * `scan_defs` and `probe_constancy` no longer hard-code the names `I` and
    `Goal`; the predicate is read off the theorem being judged.
  * **`unclassified`** joins `STAGES`, ranked above `vacuous`, below
    `discharged`.
  * **D1**: `find_books()` — any `*.lean` in the directory that states a
    theorem, `theory.lean` first.
  * **D2**: `expand_targets()` walks, and declares its exclusions.
* **`freeze/tests/test_u3_kind.py`** (new, 23 tests). Roughly half negative
  controls, because the repair is a loosening.

## The decision, and the argument

§1.2.1 defines non-vacuity **按断言的种类** — by the kind of *assertion*. Its
three rows are written `theorem unsolvable …` / `invariant …` / `prune …`,
which reads like a naming convention but is not one: every sub-check in the
table is a statement about content. So the kind is decided by the shape of the
statement over the development's declarations, and by nothing else. A name may
remain a hint; it may not be the decision.

The `prune` / `unsolvable` split is `CONTRACTS/deadlock_certificate_v0.1.md`
made executable: 「本份证书对 `s₀` 一个字都不说」 — the certificate says nothing
about the initial state. What makes a deadlock theorem *conditional* is that
its start state is universally quantified and constrained by a pattern, and
that is exactly what the classifier keys on. The pattern is read off the
theorem: it is the set of predicates positively hypothesised at the start
state.

**exam asked whether `prune` gets a check or whether §1.2 is knowingly
narrowed. It gets a check.** Narrowing was cheaper and not defensible: an E1
that cannot pass the development its own rule text calls the paradigm is not a
narrower E1, it is one that contradicts itself.

## The two verdicts one word carried

`vacuous` is an **accusation** — §1.2.1's check ran and said no. `unclassified`
is a **confession** — E1 does not know what kind of assertion this is, so
nothing ran. Both are `not_attained`; no arithmetic moved. When a development
holds both, the label is `vacuous` and `criteria.refuted` /
`criteria.unclassified` name which theorems the word covers and which it does
not, with a residual line saying so in words.

## Gate output

```
$ python -m pytest freeze -q
52 passed in 20.60s          (29 pre-existing + 23 new)

$ cd freeze && bash verify.sh
DRAFT INCOMPLETE -- 3 check(s) failed
  FAIL  MANIFEST.json has drifted from the tree
  FAIL  BUDGET_TABLE.{json,md} no longer recompute from the ledgers
  FAIL  tracked artefacts name a machine without an exemption
```

**No stage moved.** The same three fail on clean `master` in this worktree
(measured with `git stash push -u`, re-run, `git stash pop`), and all three name
other territories' in-flight work — the locations finding lists eleven run dirs
under `arc-recon/`, `proxy/` and `theoria-arm/`, none of them freeze's. Stages
[0]–[11] and [13]–[17] pass, including every negative control they carry.

## Mutation check — the controls were seen to say no

A check never seen to say no has not been shown to check anything, so each new
guarantee was deliberately broken and the suite re-run:

| mutation | tests that went red |
|---|---|
| prune (c) always returns `ok=True` | 4 (the three deadlock negative controls + the held-constant pair) |
| `unclassified` label collapsed back to `vacuous` | 2 |
| shape classifier replaced by the old name matcher | 18 |

## Census: 24 books on disk, before and after

Full table in `COMPARISON.md`; raw verdicts in `census.json`; the book table in
`CENSUS.md`.

| label | before | after |
|---|---|---|
| `discharged` | 14 | **17** |
| `vacuous` | 9 | **2** |
| `unclassified` | 0 | **4** |
| `failing_obligation` | 1 | 1 |

Seven books moved, all of them `vacuous` → something else — this repair only
ever removes an accusation. Three become `discharged` (the two copies of the C4
deadlock development, and `theory-compiler/lean`, whose invariant is called
`Inv` rather than `I`: the old (c) hard-coded `defs["I"]` and reported "no
`def I` found to check"). Four become `unclassified` (the handover packages,
whose only two theorems are a closure lemma about the `Reachable` relation and
an existential goal witness — neither is one of §1.2.1's three kinds, so
nothing was ever checked). `theory-compiler` goes from 0/7 attained to 3/7.

The two genuine vacuity findings survive, by shape rather than by prefix,
including the frozen §9.2 negative control `cold-start-a3/theory/
generated_l1_vacuous` — 抓不住它就不许冻结.

Walking the tree enumerates **the same 24 books** exam's census enumerates,
which is the agreement I most wanted to see: D1 and D2 are closed against an
independent discovery implementation.

## Residual gaps, stated

1. **`unsolvable`'s sub-check `c_init_has_action` still has no source-level
   test.** 「初始态存在至少一个合法动作」 is discharged only from a run record's
   `trace_transitions`, which a bare Lean book never carries. `d_goal_nonempty`
   can now be discharged from an existential co-theorem, so exam's 0/14 finding
   is partly relieved — but not closed. Every affected verdict carries the
   residual line rather than passing open. **This is not registered in
   `freeze/RESIDUALS.json`**, because that file is generated from `declared_at`
   pointers into `MANIFEST_DRAFT.md`, a frozen draft this ticket has no mandate
   to edit. It should be registered before 开跑; that is an ask, not a done.
2. **The parser covers the fragment the repo's generators emit** — `∀`-prefixed,
   `→`-chained, `∧`-conjoined statements over unary `Bool`/`Prop` predicates. A
   statement outside it reads `unclassified`, which fails closed. Four books on
   disk exercise that path today and they are visible as such rather than
   buried.
3. **Constancy probing is per-predicate and budgeted** (4 per development,
   `--probe` only). The fifth distinct invariant subject gets the static scan
   and a residual saying so.
4. **§1.2.1's acknowledged residual is untouched**: this clause blocks 空转, not
   平庸. A real, non-constant, entirely easy invariant still attains. In
   particular `closed_pinned` and `dead_persists` in the C4 development attain
   as `invariant`-kind theorems in their own right, independently of `dead`.
   That is correct under the frozen text — both are non-constant conserved
   properties — but it means the C4 verdict does not rest on the prune check
   alone. The freeze-side tests therefore assert `per_theorem["dead"]["c"]["ok"]`
   directly, and the minimal deadlock fixture carries no closure lemma so its
   negative controls cannot be rescued by one.
5. **`u3.UNKNOWN_KIND` is gone.** `exam/u3_census.py` reads
   `t.get("kind", "unknown")` rather than importing it, so nothing breaks, but
   that default string is now never produced.

## Coordination

`monitor/inbox/20260801T0700Z-freeze-to-exam-e1-keys-on-the-statement-now-four-of-your-tests-must-flip.md`
names the four exam tests that must flip and re-derives, on the freeze side,
the seven that must not. `exam/` was not edited.
