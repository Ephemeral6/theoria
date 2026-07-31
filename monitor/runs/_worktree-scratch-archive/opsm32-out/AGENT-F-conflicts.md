# AGENT-F — triage of the three merge-conflict flags (OPS-M cycle 32)

Base for every experiment: `cc7e414eb3bfde3325a50f9ce0e8dc896bda2b84` (master HEAD at
start of cycle). No `git fetch` was run; all shas are from existing
remote-tracking refs. Nothing was merged, committed or pushed anywhere outside
`.worktrees/opsm32-conf-*`. The main checkout was not touched.

Worktrees (all detached at cc7e414e, then `git merge --no-edit <branch>`; merges
left **uncommitted** so OPS-M can inspect index and tree):

| branch | tip | worktree |
|---|---|---|
| `origin/agent/v5-battery-freeze` | `32fa34d1e01ecd917c144ec256e6c3bb8781db07` | `.worktrees/opsm32-conf-v5` |
| `origin/agent/e8-ic3-scale` | `4ef47a1de3cbab1be9f79a3741afc00fa7401448` | `.worktrees/opsm32-conf-e8` |
| `origin/agent/p18-audits-cover-half-onmaster` | `0eb876f7c3f833284a87562b910997cc7012d8ef` | `.worktrees/opsm32-conf-p18m` |

**All three flag files reproduce verbatim.** The conflict list printed by
`git merge` in each worktree is byte-identical to the block recorded in
`monitor/ci/CONFLICT-*.md`, including file order. So no flag is stale in the
sense of "the reason no longer happens".

## Verdicts

| branch | verdict | one line |
|---|---|---|
| `v5-battery-freeze` | **SEMANTIC** | two rival gates for one canonical filename, and `BATTERY_V1.md`'s freeze is stale against master by 9 hash mismatches + 26 uncovered files — every resolution is red; needs a `BATTERY_V2`, i.e. the battery's author |
| `e8-ic3-scale` | **SEMANTIC, 1 line** | all 9 hunks resolved mechanically and proven byte-clean (51 cases, 0 drifted); one test still red on a line git auto-merged **outside** every conflict region — `recheck/` importing `interop.peg1d` vs E6's ban. Owner is the **engine-rig track**, not the monitor, and not `/CONTRACTS/` |
| `p18-audits-cover-half-onmaster` | **REDUNDANT** | resolving `--ours` yields a tree hash *identical* to master's; master's side of all five files is the documented superseder. Close the flag |

## Attempt accounting

| branch | attempts | distinct | evidence |
|---|---|---|---|
| `v5` | 23 | **≤2** | tip frozen since 2026-07-28T19:46Z (before `first_seen`); master's `battery/verify.py` moved once, at 2026-07-29T15:07Z |
| `e8` | 24 | **≤2** | master's both conflicted files frozen since 2026-07-28T20:19Z (before `first_seen`); tip settled 2026-07-29T12:16Z and has not moved in ~23 h |
| `p18m` | 7 | **1** | master had no run directory until the 11:08:26Z merge, so attempts 1–6 hit a *different, smaller* conflict; only attempt 7 (11:40:17Z) saw the 5-file conflict the flag now quotes |

`merge.log` shows the counter mechanism: `FLAG` lines increment it, the
interleaved `HELD … unchanged since last verdict` lines do not.

## Artefacts (all under `.worktrees/opsm32-out/`)

| file | what |
|---|---|
| `F_gate.py` | runs one territory's gate exactly as `ci_merge` does — `gates.gate_for`, cwd `<wt>/<dir>`, `gates.gate_env(wt)` + `PYTHONIOENCODING/PYTHONUTF8`, timeout 1800. Generalises `.worktrees/opsm31_arms.py` off `monitor` |
| `F-v5-CONTROL-battery-gate.txt` | `battery` gate at master — rc=0 |
| `F-v5-MERGED-ours-battery-gate.txt` | `battery` gate on the v5 merge resolved `--ours` — rc=1, 4 failures |
| `F-v5-battery-verify.py.CONFLICTED` | the add/add conflict as git left it, both gates side by side |
| `F-e8-CONTROL-enginerig-gate.txt` | `engine-rig` gate at master — rc=0 |
| `F-e8-MERGED-enginerig-gate.txt` | `engine-rig` gate on the resolved e8 merge |
| `F-e8-resolution.patch` | the nine-hunk resolution vs `cc7e414e` (796 lines) — apply with `git apply --index` |

Control fact used throughout: the `battery` gate is GREEN on master
(`.worktrees/opsm32-out/F-v5-CONTROL-battery-gate.txt`, rc=0, 352 passed, all four
rungs ok). The `monitor` gate is separately known-red on master; that caveat is
only invoked where a `monitor` gate is involved, and none of these three
branches touches `monitor/`.

---

## 1. `origin/agent/v5-battery-freeze` — **SEMANTIC**

### Conflicted files

    battery/verify.py        (add/add)

`PARTNER_SYNC.md` auto-merged. That is the only conflict.

### Shape of the branch

`git merge-base cc7e414e origin/agent/v5-battery-freeze` = `7df12a39`. One commit
ahead (`32fa34d1`), adding 1921 lines and **nothing else**:

    PARTNER_SYNC.md                                   |   6 +
    battery/BATTERY_V1.md                             | 788 +
    battery/freeze.py                                 | 489 +
    battery/runs/.../MANIFEST.json                    |  68 +
    battery/runs/.../RUN_STATE.md                     | 165 +
    battery/tests/test_freeze.py                      | 295 +
    battery/verify.py                                 | 110 +

`battery/freeze.py` and `battery/BATTERY_V1.md` do **not** exist on master
(`git cat-file -e cc7e414e:battery/freeze.py` → NO). So the branch's deliverable
is not duplicated anywhere; it is not redundant.

### Per-file classification

**`battery/verify.py` — semantic collision (two different gates claiming the same
canonical filename).** The conflict is the whole file: one hunk, HEAD lines 1–499
vs branch lines 500–606. At the merge base the file did not exist; both sides
then invented it independently.

* master's version (from `127edab9` S14, `dd5fdb05`, `1fd01893` V22) is a
  four-rung gate: suite → one real offline pipeline recompute → seven-artefact
  field/floor check → V22's "the committed documents state process 1's true
  separation count".
* the branch's version is a three-gate script: `freeze` (the tree still matches
  `BATTERY_V1.md`) → `tests` (≥200 collected, deselection is a failure) →
  `readings` (artefact drift reported, tolerated).

They are not two edits to one intent; they are two different answers to "what is
the battery's completion gate", with no overlap except the suite. Nothing
mechanical picks between them, and the obvious dodge — rename one to
`verify_freeze.py` — silently disarms it: `monitor/gates.py:find_gate` returns
the **first** match, canonical names first, so a second gate script under a
non-canonical name is never run once `verify.py` exists. That is the exact
"a skipped gate and a passing gate look identical" failure gates.py was written
to close, so the dodge is not available.

### The finding that makes the call, and it is bigger than the conflict

Even if `verify.py` is resolved *any* way, **the merged tree fails the branch's
own freeze.** `battery/freeze.py`, `battery/BATTERY_V1.md` and
`battery/tests/test_freeze.py` all merged cleanly, so this is measurable in the
conflicted worktree without resolving anything:

```
cd .worktrees/opsm32-conf-v5
python -c "from battery import freeze; print(len(freeze.check()))"
# 36
```

The 36 break down as:

* **9 frozen files hash-mismatched** — `battery/audit/gaming.py`,
  `battery/metrics/{__init__,economy,epistemic,mechanism}.py`,
  `battery/METRICS.md`, `battery/docs.py`,
  `battery/tests/test_exploits_economy.py`, and `battery/verify.py` itself.
  freeze.py's own message: *"A frozen file has been edited in place. The numbers
  published under BATTERY_V1 were produced by the old file … register a new
  freeze version (BATTERY_V2.md) instead of editing this one."*
* **26 files under `battery/` covered by no freeze bucket** — the whole V9
  anti-gaming audit (`battery/audit/v9/**`, 7 attack modules, 4 test files),
  `battery/PREREG_V9.md`, `battery/BLINDING.md`,
  `battery/tests/test_verify_separation_claim.py`.
* **`battery/PREDICTIONS.md` has grown** since the freeze — prefix intact, so
  nothing was rewritten, but predictions were appended after the instrument was
  frozen.

And the branch's own tests say so:

```
cd .worktrees/opsm32-conf-v5
python -m pytest battery/tests/test_freeze.py -q -rf
# 4 failed, 19 passed
#   test_the_freeze_holds_on_the_real_tree
#   test_the_fixture_reproduces_the_real_verdict
#   test_an_edited_artefact_is_reported_but_does_not_fail
#   test_rendering_the_blocks_reproduces_the_record
```

`battery/tests/` is inside rung 1 of *master's* gate too ("the suite passes"), so
**both** candidate resolutions produce a red `battery` gate:

| resolution | battery gate | evidence |
|---|---|---|
| keep master's `verify.py` (`--ours`) | **RED, rc=1, measured** | `F-v5-MERGED-ours-battery-gate.txt`: `[1/4] suite  FAIL  suite red (exit 1)` … `4 failed, 371 passed`, all four in `test_freeze.py`; `battery: RED (1 problem(s))` |
| keep branch's `verify.py` (`--theirs`) | RED | its gate 1 `freeze` fails with the 36 items above; gate 2 (`tests`) is the same suite, also red |
| compose both | RED | inherits both reasons |
| **control: master, unmerged** | **GREEN, rc=0** | `F-v5-CONTROL-battery-gate.txt`: all four rungs ok, 352 passed |

Master's rung 1 is `pytest battery/tests` (`battery/verify.py:144`), which is why
it picks up the branch's new `test_freeze.py`; 352 + the branch's 23 new tests =
the 375 collected. The failing-id set differs from the control's (the control has
none), so this red is **caused by the merge**, not inherited — exactly the
discrimination the `monitor`-gate caveat asks for, applied to `battery`.

Both worktree states are preserved: the conflicted `battery/verify.py` is saved at
`.worktrees/opsm32-out/F-v5-battery-verify.py.CONFLICTED`, and
`.worktrees/opsm32-conf-v5` now holds the `--ours` resolution (staged, **not
committed, not pushed**).

### Verdict: SEMANTIC — do not force-resolve

The two incompatible meanings:

1. `BATTERY_V1.md` asserts *these 8 buckets of files, at these sha256s, are the
   instrument that produced the published readings.* The branch computed that
   assertion against `7df12a39`.
2. master, at `cc7e414e`, asserts *the battery is this tree* — which now includes
   the V9 blinding/anti-gaming audit and V22's separation rework, i.e. edits to
   9 of the frozen files and 26 files the freeze never heard of.

Both are true statements about different trees. Reconciling them means **choosing
what the freeze is a freeze of**, and freeze.py explicitly forbids the cheap fix
(re-hashing `BATTERY_V1.md` in place) because that would silently re-attribute
already-published numbers to code that did not produce them. The honest
resolution is a `BATTERY_V2.md` — new buckets for `audit/v9/**` and the appended
predictions, new readings — which is authored work, not a merge.

**Who must decide:** the battery territory's owner / the V5 author, with the
monitor's sign-off on whether re-freezing invalidates any published number. This
is a *freeze version bump making downstream files non-compliant* — structurally
the same case as a contract version bump, and OPS-M's standing rule says file it,
do not force it.

### The flag's stated reason vs. what happened

Reason matches exactly: `add/add` on `battery/verify.py`, `PARTNER_SYNC.md`
auto-merged. Reproduced verbatim.

`attempts: 23 since 2026-07-29T04:33:05Z`. How many are distinct:

* the branch tip `32fa34d1` is dated 2026-07-29T03:46:42+08:00 =
  **2026-07-28T19:46:42Z** — *before* `first_seen`. **The tip has not moved once in
  the whole window** (~40 h old at time of writing).
* master's side moved exactly once: `battery/verify.py` was last touched by
  `1fd01893` (V22), 2026-07-29T23:07:33+08:00 = **2026-07-29T15:07:33Z**, which is
  inside the window.

So at most **2 of the 23 attempts** are distinct computations, and the shape
(whole-file add/add, zero common lines) was identical in both. Everything after
15:07Z — the majority — is the same doomed pass re-reaching a branch whose author
has not touched it for 40 hours.

Worth noting for the earlier hypothesis on record in `monitor/mailbox/OPS-M.md`
(*"add/add — the default resolution is the union, not either/or, but make it prove
that rather than assume it"*): **the union is red too.** Proven above; the union
inherits both gates' suite stage and `test_freeze.py` fails in it.

**`PARTNER_SYNC.md` is a clean append-only union** and needed no help:
`git diff --numstat 7df12a39 <each side> -- PARTNER_SYNC.md` is `6 0` and `723 0`
— zero deletions on either side — so git's own merge is the correct keep-both. One
cosmetic consequence: v5's paragraph is stamped `2026-07-28T19:40:00Z` and lands
*after* the `2026-07-30T05:40:00Z` exam paragraph. Per the repo's append-only rule
that is corrected by appending, never by reordering, so it is not a defect of the
merge.

**What would falsify this call:** the only escape would be `BATTERY_V1.md` turning
out to be a *regenerable* artefact rather than a record — then this is a
generated-artifact collision, resolvable by re-running the generator. **I checked,
and the branch's own code refuses that reading in writing.** `freeze.py` has a
`render_blocks()` that produces exactly the fenced blocks the record carries, and
its docstring says:

> *"Used to author the record and to re-author it for a new freeze version.
> **Deliberately not wired to write the file: a freeze that a script can refresh
> in place is not a freeze.**"*

`freeze.py:53-55` also hard-codes `RECORD = battery/BATTERY_V1.md` and
`FREEZE_VERSION = "BATTERY_V1"`, and `NARRATIVE` lists `BATTERY_V1.md` with the
comment *"the record does not hash itself"*. So a V2 is not a re-render: it needs
new buckets covering `battery/audit/v9/**` and the appended predictions, new
constants, and new readings. That is authored work in `battery/`, which is the
disposition above.

The remaining falsifier is a *ruling* rather than a fact: if the battery's owner
declares BATTERY_V1's published readings not to depend on the 9 changed files,
re-rendering becomes legitimate and this flips to MECHANICAL. That ruling is
exactly the thing to ask for; nothing a merge referee can measure decides it.

---

## 2. `origin/agent/e8-ic3-scale` — **SEMANTIC, but reduced to one line**

The prior cycles' claim was **tested, not inherited, and it holds** — except for
its ownership. It is *not* a `/CONTRACTS/` matter.

### Conflicted files

    engine-rig/recheck/build_cases.py   (content, 5 hunks)
    engine-rig/recheck/verify_all.py    (content, 4 hunks)

`PARTNER_SYNC.md` and `engine-rig/interop/certificate_export.py` auto-merged.

### Shape of the branch

Merge base `a4d2ef2b`; 4 commits ahead; 50 files, +32 297/−52. It adds the
`ic3bounds` package, the peg5…peg13 size gradient with `ic3_pdr`'s invariants, and
six test modules. **It touches no file under `/CONTRACTS/`** —
`git diff --name-only a4d2ef2b origin/agent/e8-ic3-scale -- CONTRACTS/` is empty.
The only "schema" strings in the diff are engine-rig-internal
(`lp_potential/pagoda_certificate@1`, `ic3_pdr/inductive_invariant_certificate@1`)
and the branch only *extracts them into named constants* — both sides agree on the
values, and that file auto-merged.

### The nine hunks: MECHANICAL, and I resolved them

Both sides refactored `peg_ruleset` and `all_cases`, and both added new functions
at the same point of `verify_all.py`:

| file | hunks | shape |
|---|---|---|
| `build_cases.py` | docstring bullet list | prose, both sides' bullets kept |
| | `PEG_SIZE_WORD` vs `_NUMBER_WORDS` | two names for one table; **union under one name**; the sides agree on 4 and 5, the only sizes HEAD's cases use |
| | `peg_ruleset` signature | HEAD `(start, goal, name)` with `n = len(start)`; e8 `(start, n, goal)` and **no `name`** |
| | `all_cases` peg block | HEAD's `peg5-11011-*` pair + `keyed-gate`; e8's gradient loop |
| | `all_cases` tail | HEAD's `PAGODA_CLAIMS` loop vs e8's `})` — brace bookkeeping only |
| `verify_all.py` | imports | union: `RuleSet` (e8) + `reachable_states` (HEAD) |
| | `run_pagoda` (HEAD, new) vs `peg_relation_anchor` (e8, new) | neither exists at the merge base — **adjacent additions, keep both** |
| | `run_anchors`' `agrees` | HEAD's `peg5` term + e8's `relations` term, both `and`-ed |
| | `main`'s `counts` dict | HEAD's two pagoda keys + e8's two counts keys, both kept |

The one hunk with real content in it is `peg_ruleset`. **The 5-cell board appears
on both sides at once with two different provenance stories** — HEAD's
`peg5-11011-to-01000/00010` are *anchored* (they cite `interop/README.md`'s finding
that the pagoda exists for cells 1 and 3 and for no disjunction), e8's
`peg5-01111` is a *gradient* step (it cites `interop.peg1d`). So e8's `n == PEG_N`
discriminator cannot decide it and neither can `n`; the distinction has to become
an argument. Resolution: `peg_ruleset(start, goal, name=None, gradient=False)`,
`n = len(start)`, `_peg_goal_prose` (e8's, a strict superset of HEAD's one-liner
for every single-peg goal in the tree).

**Proof the resolution is right, not merely plausible** — the generator is a
byte-stability checker, so it grades itself:

```
cd .worktrees/opsm32-conf-e8/engine-rig
PYTHONPATH=<wt> python -m recheck.build_cases --check
# 51 cases, 0 drifted        rc=0
```

51 committed cases — HEAD's peg4/peg5/keyed-gate/pagoda/a2/sokoban set **and**
e8's peg5…peg13 gradient — all reproduced byte-for-byte from the unified
generator. Neither side's published bytes moved.

#### The signature change has call sites OUTSIDE the conflicting files, and `--check` did not see them

Worth recording as its own finding, because it is the third appearance of the
shape OPS-M has already written down twice (*"git being satisfied proves
nothing — run the tree"*). `--check` was green and both conflicted files were
clean, and the gate still found two more failures on the first run:

```
FAILED tests/test_ic3bounds_recheck_column.py::test_every_ladder_rung_that_answers_has_a_rule_set_available
FAILED tests/test_ic3bounds_recheck_column.py::test_the_committed_case_is_preferred_over_one_generated_on_the_spot
```

Cause: `peg_ruleset` has two more callers, both in files git never marked
conflicted and in a **different package**:

* `engine-rig/ic3bounds/recheck_column.py:234` — `peg_ruleset(start, n, goal)`,
  used above the committed sizes to generate a ladder rung's rule set in memory;
* `engine-rig/tests/test_ic3bounds_recheck_column.py:340` —
  `peg_ruleset("0111", 4, "0100")`.

Under the unified signature the positional `n` lands in `goal` and `goal` lands in
`name`, i.e. an int is silently accepted as a goal string. `--check` missed both
because `all_cases()` never routes through them. Fixed in the resolution
(`gradient=True` for the ladder path, `goal="0100"` for the peg4 assertion — the
same call `all_cases` makes for that file, so the test's meaning is preserved);
after the fix `python -m pytest tests/test_ic3bounds_recheck_column.py` is
**16 passed** and `--check` is still 51/0.

A sweep for the remaining call sites is one command and should be part of any
signature-changing resolution:
`grep -rn "peg_ruleset(" --include=*.py .`

Resolution is staged in `.worktrees/opsm32-conf-e8` (merge in progress, index
resolved, **not committed, not pushed**) and exported as
`.worktrees/opsm32-out/F-e8-resolution.patch` (1 616 lines vs `cc7e414e`, four
files: the two conflicted ones plus the two call sites).

Reproduce:
```bash
git worktree add --detach .worktrees/<new> cc7e414e
cd .worktrees/<new> && git merge --no-edit origin/agent/e8-ic3-scale   # 2 conflicts
git apply --index ../opsm32-out/F-e8-resolution.patch
cd engine-rig && PYTHONPATH=<wt> python -m recheck.build_cases --check   # 51 / 0 drifted
PYTHONPATH=<wt> python -m pytest tests/test_ic3bounds_recheck_column.py -q  # 16 passed
```

### The one thing that is NOT mechanical, and it is outside every conflict region

The merged tree still fails exactly one test, and **git auto-merged the line that
breaks it** — it never appeared as a conflict, so no amount of hunk-resolving
touches it:

```
cd .worktrees/opsm32-conf-e8/engine-rig
python -m pytest tests/test_recheck.py -q -rf
# FAILED tests/test_recheck.py::test_recheck_never_imports_the_engines
#   AssertionError: ['verify_all.py: from interop import peg1d']
# (that is the only failure in the file)
```

The two files that collide are on *different sides and neither is in conflict*:

* `engine-rig/tests/test_recheck.py` — **master's** (E6 added the ban;
  base blob `23f6cedd` == e8's blob, master's is `fb1f60bc`, +240/−4). Line 622:
  `forbidden = ("engines", "tools.", "interop")`.
* `engine-rig/recheck/verify_all.py:47` — **e8's**: `from interop import peg1d`,
  under a five-line comment arguing the case.

Because e8 never touched the test, git took master's; because master never touched
that import region, git took e8's. Both auto-merges are individually correct and
their conjunction is red.

**Full `engine-rig` gate on the resolved merge** — run exactly as `ci_merge` does
(`gates.gate_for(wt,'engine-rig')` → `verify.py`, cwd `<wt>/engine-rig`, env
`gates.gate_env(wt)` + `PYTHONIOENCODING/PYTHONUTF8`, timeout 1800; driver
`.worktrees/opsm32-out/F_gate.py`):

* **control at master** (`.worktrees/opsm32-ctl`): **rc=0, GREEN** — all three
  stages ok (`F-e8-CONTROL-enginerig-gate.txt`), ~1 minute.
* **resolved merge** (`.worktrees/opsm32-conf-e8`): see
  `F-e8-MERGED-enginerig-gate.txt` for the final rc and stage lines. It is red at
  `[1/3] suite` on the id above; the targeted run of the whole
  `tests/test_recheck.py` shows that file's **only** failure is
  `test_recheck_never_imports_the_engines`, so the nine-hunk resolution
  introduces no breakage of its own. (This run is far slower than the control
  because the branch's `ic3bounds` tests re-derive IC3 invariants up to 8 192
  states.)

**The two incompatible meanings:**

1. **E6 / master:** `recheck/` imports nothing from `interop`, because
   `interop/certificate_export.py` imports `engines.lp_potential.potential`, so
   *"importing anything from `interop` would reach the engine one hop further out
   and the independence would be gone at exactly the point it is being claimed."*
   Reading files under `interop/certificates/` is fine; importing is not.
2. **E8 / branch:** `interop.peg1d` is precisely the outside artefact an anchor
   requires — *"built for lp_potential, before this package existed, and sharing
   no code with either the rechecker or IC3"*. Without it `peg_relation_anchor`
   cannot compare the gradient's derived relation against an independent
   transcription, and a gradient step with no independent checker is the thing
   axis A exists to avoid.

### Evidence that makes the ruling decidable (gathered so the owner need not)

E6's stated rationale is **false for `peg1d` specifically**. Measured on the
merged tree:

```
engine-rig/interop/__init__.py            0 bytes
engine-rig/interop/peg1d.py imports       collections, typing   (stdlib only)
python -c "from interop import peg1d; ..."  →  engines modules loaded: NONE
```

So the import does not reach `engines` at all, one hop or any number of hops. The
ban is over-broad relative to its own justification: it bans a *package* because a
*sibling module* in it imports the engine. The narrow rule E6's reasoning actually
supports is "nothing under `recheck/` may import a module that transitively
imports `engines`", which `interop.peg1d` satisfies.

No published prose depends on the wide form — `grep -rn interop
papers/phase1-workshop/sections/` finds only citations of
`interop/certificates/*.json` and `interop/README.md`, never a claim that
`recheck` imports nothing from `interop`. The rule lives only in that test's
docstring; `engine-rig/DECISIONS.md` has no D-entry for it.

### Verdict: SEMANTIC — file it, do not force it. Nine hunks are already done.

**Who must decide:** the **engine-rig track** — the owner of `engine-rig/` and of
E6's `test_recheck.py`. *Not* the monitor, and *not* a `/CONTRACTS/` question:
prior cycles addressed this to the monitor as 「契约问题」, and that framing is off
by one owner. `/CONTRACTS/` holds `candidates_schema.md` and
`dsl_grammar_v0.1.md`; neither is involved, and neither branch touches them. What
is at stake is engine-rig's *internal* independence rule, which the engine-rig
track wrote and may narrow.

**What must be decided (one line):** does `forbidden` become
`("engines", "tools.")` plus a transitive-import check, or does `verify_all.py`
lose `peg_relation_anchor` (and axis A lose its independent checker above n=4)?

**Why I did not just narrow the test**, even though the evidence points that way:
narrowing a check so a merge turns green is the move OPS-M's own standing
instruction forbids (「不许为了变绿放宽检查」), and the check encodes an
independence claim — the one property that makes `recheck` worth anything. The
evidence above is *material for* the ruling, not the ruling.

**What would falsify this call:** (a) if `interop/__init__.py` or `peg1d.py`
acquired an `engines` import, meaning is #1 becomes literally true of `peg1d` and
the branch is simply wrong; (b) if the test's ban is found restated in a frozen
artefact or in `PAPER.md` — then it is a published claim and narrowing it is a
retraction, not a ruling; (c) if `peg_relation_anchor` can be sourced from
somewhere that is not `interop` (a fresh independent transcription inside
`recheck/`), the collision dissolves and the whole branch becomes mechanical —
but that is new work, not a merge, and it re-raises "independent of what?".

### The flag's stated reason vs. what happened

Reason matches exactly: two content conflicts in `recheck/{build_cases,verify_all}.py`,
reproduced verbatim.

`attempts: 24 since 2026-07-29T04:15:47Z`. How many are distinct:

* master's side of the conflict has not moved since **`5b982a07`,
  2026-07-29T04:19:13+08:00 = 2026-07-28T20:19Z** — *before* `first_seen`. Both
  conflicted files have that commit as their last master touch.
* the branch tip is `4ef47a1d`, 2026-07-29T20:16+08:00 = **12:16Z**, i.e. it moved
  once during the window (after `first_seen` at 04:15Z) and not since — 23h ago.

So both sides of both conflicting files have been frozen for ~23 hours and **all
24 attempts after the tip settled computed the identical conflict**. At most 2 of
the 24 are distinct computations; the rest are the same doomed pass re-reaching a
branch nothing has changed. `merge.log` shows the mechanism plainly: `FLAG` lines
increment the counter (09:42 → 21×, 10:26 → 22×, 11:31 → 23×, 11:36 → 24×) while
`HELD … unchanged since last verdict` lines in between do not.

---

## 3. `origin/agent/p18-audits-cover-half-onmaster` — **REDUNDANT**

### Conflicted files

    papers/phase1-workshop/runs/20260730T000000Z-P18-audits-cover-half/MANIFEST.json                 (add/add)
    papers/phase1-workshop/runs/20260730T000000Z-P18-audits-cover-half/citecheck-A-abstract-to-s3.md (add/add)
    papers/phase1-workshop/runs/20260730T000000Z-P18-audits-cover-half/citecheck-C-s7-to-s8.md       (add/add)
    papers/phase1-workshop/runs/20260730T000000Z-P18-audits-cover-half/delta-old-vs-new.md           (add/add)
    papers/phase1-workshop/verify_paper.py                                                           (content)

### Containment proof — this is the whole answer

`git merge-base cc7e414e <branch>` = `b5998e5d`. The branch is 4 commits ahead and
touches **14 files**. Comparing each against master at `cc7e414e`:

| state | count | files |
|---|---|---|
| byte-identical to master | 10 | `REVIEW-2026-07-30.md`, `REVIEW.md`, `audit_stamp.py`, `test_audit_stamp.py`, and the run dir's `COVERAGE.md`, `RUN_STATE.md`, `citecheck-B-s4-to-s6.md`, `citecheck-D1-s9-to-s10.md`, `citecheck-D2-s11-to-s12.md` |
| differ | 4+1 | exactly the five conflicted files |

Resolving every conflict `--ours` (i.e. keep master) produces a tree
**byte-identical to master's**:

```
cd .worktrees/opsm32-conf-p18m           # already left in this state
git checkout --ours -- $(git diff --name-only --diff-filter=U); git add -A
git write-tree                  # a4f932e90378166a6adc61c26e9059d0ab36a244
git rev-parse cc7e414e^{tree}   # a4f932e90378166a6adc61c26e9059d0ab36a244   ← equal
git diff --stat cc7e414e -- .   # empty
```

So the branch contributes **zero bytes master does not already have**. This is not
an inference from commit graph shape; it is the tree hash.

### Why master's side is the right side of each of the five (not merely "ours")

* **`citecheck-A-abstract-to-s3.md`** — branch 4 448 bytes, master 70 908. Master's
  file says so in its own second paragraph: *"…not copied from the stub this file
  replaces"*, and a section headed **"What this file replaces"** enumerates the
  branch version's numbers and their corrections: *"Pass A confirmed (69/62/7/0),
  Pass B 8 → 12, Pass C 9 → 8, Pass D 14 checked → 25, 4 inexact → 5, and one of
  the stub's three load-bearing findings does not exist."* The branch's file is
  the stub being described.
* **`citecheck-C-s7-to-s8.md`** — branch 1 992 bytes, master 69 933; same pattern,
  master's version measured in its own worktree rather than inherited.
* **`delta-old-vs-new.md`** — branch 2 579 bytes, master 47 321; master's is the
  full reconciliation table, every field recomputed.
* **`MANIFEST.json`** — branch 451 bytes, master 11 063. The branch's manifest
  even declares `"branch": "agent/p18-audits-cover-half-the-paper"` — the two
  branches are two checkouts of the *same run* by the same worker (`W-1690`), and
  master now carries the finished one.
* **`verify_paper.py`** — a pure table-widening conflict. Both sides list the same
  seven checks with the same names, descriptions and callables, `G AUDITSTAMP →
  audit_stamp.check` included; master's rows carry a fourth tuple field the
  branch's do not. The branch's rows are a projection of master's. The branch's
  `audit_stamp.py` / `test_audit_stamp.py` — the thing check G needs — are already
  in master byte-identically.

No gate needs to be run: the resolved tree *is* master's tree, so any gate on it
returns master's own answer by construction.

### Verdict: REDUNDANT — close the flag, nothing to merge

Mechanical disposition, if OPS-M wants the reflag loop to stop rather than just
the flag file removed:

```bash
git merge -s ours origin/agent/p18-audits-cover-half-onmaster   # tree unchanged by definition
```

`-s ours` records the branch as an ancestor without moving a byte, which is
exactly true here and is what makes `ci_merge` stop re-reaching it. (OPS-M's call
whether to record it that way or simply clear the flag; either is defensible, but
`-s ours` is the one that survives the next pass.)

### The flag's stated reason vs. what happened — it changed character today

The flag says `first_seen: 2026-07-30T05:00:19Z, attempts: 7` and quotes a
five-file conflict. But master did not contain the run directory at all until
`p18-audits-cover-half-the-paper` merged:

```
git log --diff-filter=A --format='%H %cI %s' cc7e414e -- <rundir>/RUN_STATE.md
# 34036ec4 2026-07-30T12:29:59+08:00   (reachable only via the merge)
git log -1 --format='%cI' 9d0cb6b9    # 2026-07-30T19:08:26+08:00 = 11:08:26Z
merge.log: 2026-07-30T11:09:04Z MERGED origin/agent/p18-audits-cover-half-the-paper
```

So attempts 1–6 (05:00:19Z … 10:41:36Z) hit a **different, smaller** conflict —
the run dir did not exist on master, so those four add/add conflicts could not
have occurred. Only attempt 7 (11:40:17Z) saw the conflict the flag file now
quotes. The flag body is accurate *as of its last_seen*; its `first_seen` and
`attempts: 7` describe a different failure, and reading "7 attempts" as "seven
attempts at this conflict" is wrong. **1 of 7.**

Note also that the merge which made this branch redundant is the same merge that
created the add/add conflict: the branch went from "one small code conflict" to
"fully superseded and noisier" in the same instant.
