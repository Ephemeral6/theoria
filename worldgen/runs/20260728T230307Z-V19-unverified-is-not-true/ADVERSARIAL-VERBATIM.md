# ADVERSARIAL REVIEW — V19-unverified-is-not-true

Worktree `C:\Users\user\Desktop\theoria\.worktrees\v19-unverified-is-not-true`. Baseline: `512 passed, 13 skipped`; `python -m worldgen.build --check` exit 0, byte-deterministic; tree left clean (`git status --short` shows only the implementer's own uncommitted prose edits — none of mine).

**Procedural note first:** the branch is no longer at the stated base. The implementer committed **`23ec179`** during this review and has since further modified `worldgen/RUN_STATE.md` and two files in the run directory. I re-verified all 91 `MANIFEST.json` sha256s after the commit — every one still matches, so the code I mutated is exactly the code that was committed, and every result below stands.

## 1. VERDICT

| line | verdict |
|---|---|
| **(a)** three-state hides unverified in another class | **PARTIALLY OVERTURNED** — no *live* path mis-files a row, but the partition is not total (nameless rows vanish, A09) and `to_markdown` runs a **second, independent, truthiness-based classifier** that can disagree with `classify_invariants` about the same row in the same document |
| **(b)** over-corrected into "reject everything" | **UPHELD** — violated and unverified stay distinct at every layer but the exit code; vacuity on 0 states/0 transitions is closed *and* tested with a control. One hole: the exception path is untested, and removing it reconstructs V19's defect verbatim (C12) |
| **(c)** flip number read favorably | **UPHELD** — `FLIPS.md` reports 13 *and* 0 and explicitly refuses the favorable reading. All three `edge_check`s are genuinely exercised and genuinely consumed. All 35 artefacts re-derive byte-identically from the generator. Caveat: the *evidence counts* the verdicts rest on are pinned by nothing |
| **(d)** sweep only one file | **PARTIALLY OVERTURNED** — the sweep did cover all of `worldgen/` and is unusually good, but it missed the largest instance of the disease in the repository: `core/reversibility.py`, where **90 of 218 shipped claims (41%) are unverified and the gate reads only `DISAGREES`** |

**Mutants: 80. Escapees: 30.** Test cells in the surface under review: 92. Mutant count exceeds test count and the mutant set is not a mirror of the test list — 12 of the escapees hit layers no test names at all.

---

## 2. FINDINGS

### F1 — CRITICAL. Swallowing the exception rebuilds V19's defect exactly, and both gates stay green (C12/C13)

`worldgen/core/truth.py:316-320` (state loop) and `:331-337` (edge loop). Change the `except` branch to `continue` instead of recording a violation:

```
cd .worktrees/v19-unverified-is-not-true
# in a package copy: replace the state-loop except body with `continue`
python -m pytest worldgen -q            # 512 passed  <-- GREEN
python -m worldgen.build --into TMP     # exit 0      <-- GREEN
```

Observed consequence, measured directly (a `check` that raises on **every** one of 24 reachable states):

```
row: {'name': 'always_raises', 'states_checked': 24, 'verified': True,
      'holds': True, 'status': 'holds'}
all_invariants_hold: True
```

`states_checked: 24`, `holds: true`, `status: "holds"` — for a check that never once returned a value. This is the cell's own sentence ("I could not check this" written as "this holds") reconstructed by a two-line edit, in the function the cell rewrote, with the suite green. The docstring devotes an entire paragraph (`truth.py:288-296`) to defending the raise→`violated` choice as a judgement call; **nothing tests that the branch exists.** C13 is the same for `edge_check`.

### F2 — CRITICAL. The evidence counts are unpinned: the edge/state loops can be gutted with the suite green (C07, C08, C14, C15, C18, C19, C20 — seven escapees)

`truth.py:301-341`. Every one of these leaves `pytest` and `build` green:

| edit | resulting artefact |
|---|---|
| `world.transitions(states)` → `list(...)[:1]` (C07) | edge_check sees 1 of 10616 transitions |
| `for state in states` → `states[:1]` (C08) | `check` sees 1 state, JSON still says `"states_checked": 26` |
| `row["states_checked"] = 0` (C14) | `_(checked on 0 reachable states: holds)_` |
| `row["transitions_checked"] = 0` (C15) | `_(checked on 0 transitions: holds)_` |
| omit `transitions_checked` entirely (C18) | `_(checked on no states: holds)_` — the `or "no states"` fallback at `truth.py:507` |

C08 is the sharpest: `states_checked` is written from `len(states)` on a separate line from the loop, so the artefact reports evidence it did not gather. The sandbox cannot see this because `violated_state` injects `lambda: False`, which fails on the first state.

This matters for line (c). The whole of `FLIPS.md`'s stage-2 argument is "84 to 10616 transitions each, not a default" — and **no test and no gate asserts those numbers are non-zero, let alone correct.**

`--check` does not save you. Direct measurement:

```
build --check exit code: 0
committed artefact changed by the mutant: True
'transitions_checked': 104 present before: True
'transitions_checked': 0 present after:  True
```

`main()` rebuilds `OUT` *before* `check_determinism` diffs it, so `--check` compares mutated-against-mutated. (`worldgen/tests/determinism_sandbox.py:12-16` already says this in as many words about V16.) Committed artefacts are pinned by `git diff` and human eyes only.

### F3 — HIGH. `to_markdown` is a second classifier, and it disagrees with the first

`worldgen/core/truth.py:496` — `if not inv.get("verified")` — and `:508` — `inv["holds"]`. The section *summary* uses `classify_invariants`; the per-row *bullets* do not. Truthiness, not identity, which is the exact idiom test row `k` (`"truthy is not True — identity, so a stray 1 cannot pass"`) exists to forbid, one function below where it is forbidden.

Reproduction (row with `verified: 1, holds: 1`):

```
JSON classify  -> {'holds': [], 'violated': [], 'unverified': ['z']} all_hold: False
MARKDOWN       -> 0 hold, 0 violated, 1 unverified — ... `invariants_all_hold` is `false`.
MARKDOWN       -> * **z** — s  _(checked on 10 reachable states: holds)_
```

One document, two verdicts on one claim, and the per-claim line — the one a human actually reads — is the kinder of the two. `test_the_json_verdict_is_never_kinder_than_the_markdown` asserts the implication in one direction only and structurally cannot catch this.

### F4 — HIGH. The entire Markdown layer is unguarded (D03, D04, D05, D07 — four escapees)

The catalogue ships **165 `holds` rows, 0 violated, 0 unverified**. Every "against the real catalogue" test therefore exercises only the happy path:

- `D04` — delete `**VIOLATED**` from `truth.py:508`. Green. The Markdown can never again say a word about a violated invariant.
- `D03` — delete `**unverified**` from `truth.py:497`. Green.
- `D05` — hardcode the summary to `` `true` `` (`truth.py:460`). Green.
- `D07` — drop unverified rows from the bullet list entirely. Green (`len(bullets) == len(invariants)` still holds because there are none).

Half the cell's stated thesis is "no machine-read field may be more optimistic than the Markdown rendered beside it." The Markdown half of that thesis has **no negative control** — `invariant_sandbox.py` asserts on gate lines and exit codes and never reads a `GROUND_TRUTH.md`.

Same root cause: `C02` (drop `row["status"] = INV_UNVERIFIED` from the prose branch) escapes, because `test_every_shipped_invariant_row_carries_an_explicit_status`'s `if row["status"] == UNVERIFIED:` branch never executes on any shipped world.

### F5 — HIGH. (d) The sweep missed the biggest instance in the repository: `core/reversibility.py`

`worldgen/core/reversibility.py:260-266`:

```python
if measured is None:
    verdict = "unreachable"          # the rule can never fire in this world
elif isinstance(stated, bool):
    verdict = "agrees" if stated == measured["re_witnessable"] else "DISAGREES"
else:
    verdict = "deferred"
```

`claim_disagreements` (`:275`) counts only `DISAGREES`, and `claim_disagreements` is a build gate. So a claim written as prose (`"conditional — ..."`) is `deferred` and passes, and a claim about a rule that never fires is `unreachable` and passes. Measured across the 35 shipped `reversibility.json`:

```
Counter({'agrees': 128, 'deferred': 53, 'unreachable': 37})
worlds with >=1 unexercised reversibility claim: 35 of 35
```

**90 of 218 claims (41%) ship unverified.** The most common single case is `walk`, in all 35 worlds, claimed `"conditional — reversible on open floor, not ..."` and recorded `deferred`. That is `check: None` wearing a different word, at 7× the scale of the 13 worlds V19 was written about.

The header of the very file V19 rewrote says (`truth.py:23`) "**the reversibility stamp is measured**", and `worldgen/README.md:118` says "every mechanism's `re_witnessable` claim against the measurement". Both are the optimistic reading. Neither was updated.

### F6 — MEDIUM. (d) Four more sites the sweep missed

1. **`core/truth.py:518`** — `blockers = cert.get("blocking_entities") or []`. This is the only `or []` in `worldgen/`, it is in the file V19 is named for, and `OPTIMISTIC-DEFAULTS.md` states "`or []` … outside the one site above: **none in `worldgen/`**." Reachable via `ground_truth(diagnose=False)` (used by `mutate.py:1117` and by the cell's own new test at `test_invariant_status.py:239`); a certificate that was never diagnosed renders identically to one with no blockers found. Same shape and same file as `corr.get("agrees", True)`, which the sweep *did* find.
2. **`core/truth.py:169-171`** — `dormant = names - fired - cascade`, `primary_never = dormant - clause`. A mechanism marks its own rule `cascade: True` or `clause: True` and exempts itself from the never-fires gate. **37 declared rules across the catalogue are exempt this way** (19 dormant clauses + 18 cascade), exactly matching the 37 `unreachable` reversibility claims. Nothing audits an exemption.
3. **`build.py:186-188` and `mutate.py:1415`** — `if r["intended_solvable"] is not None` / `if claimed is not None`: a missing claim skips the check in silence, with no count of how many were skipped. This is the identical shape to `totals.get(key, ())`, which the implementer fixed *and* wrote a parametrised test for. Currently unreachable (all 20 worlds and all 15 mutations carry a claim) — which is precisely the argument they used to justify fixing the other one. Inconsistent treatment.
4. **`tests/test_build_gate.py:91`** — `pytest.skip("no shipped INDEX.json")`. The only test that checks the gate against a *real* manifest turns green when the artefact is absent. A skipped test is a passed test.

`worldgen/qc/` is clean and I want to say so plainly: `verdict()` at `run_qc.py:266-276` reads `l12.get("l1_pass")` with **no** default, `_l3_failure` sets every accuracy to `None`, and both resolve to *not passed*. The implementer's judgement there is correct.

### F7 — MEDIUM. `boolean_default` is an observational no-op — a control that cannot distinguish itself from its own control

`worldgen/tests/invariant_sandbox.py:245-250` / `test_invariant_gate.py:194-205`. I ran every `(prose_only, weakening)` pair the tests use and diffed the full subprocess output against the unweakened run:

```
boolean_default            rc=1 (unweakened rc=1)  gate_lines_equal=True   stdout_equal=True
pre_v19                    rc=0 (unweakened rc=1)  gate_lines_equal=False  stdout_equal=False
unverified_sinks_to_holds  rc=0 (unweakened rc=1)  gate_lines_equal=False  stdout_equal=False
drop_unverified_gate       rc=0 (unweakened rc=1)  gate_lines_equal=False  stdout_equal=False
```

`boolean_default`'s run is **byte-identical** to the unweakened one. So `test_the_boolean_alone_is_not_what_catches_it` asserts exactly what `test_a_prose_only_invariant_cannot_pass_the_gate` already asserts, on a process whose entire output is the same; if that weakening silently failed to apply, the test would still pass. The *finding* it reports (the conjunction is not what catches the defect) is true and valuable — but it is established by the identity of those outputs, which the test never reads. The other three weakenings are real. Fix: have that test read `invariants_all_hold` out of the produced `ground_truth.json`, which is the only thing the weakening actually moves.

### F8 — MEDIUM. `invariants_all_hold` is now a decoration nothing exits on

Post-repair, no gate reads it — `build.py:178,180` read `invariants_violated` / `invariants_unverified` directly. Demonstrated: `all_invariants_hold` → `return False` gives `pytest_rc=1, build_rc=0`; `D01` (`"invariants_all_hold": True` hardcoded in `ground_truth`) gives `pytest_rc=1, build_rc=0`. The build ships whatever that boolean says. It is the one field a naive downstream consumer would read, it is the field the cell is named after, it is published into all 35 `ground_truth.json` and 35 `INDEX.json` rows, and **the build gate cannot tell whether it is true.** This territory's two prior findings were both "a verdict nothing exits on is a decoration"; the repair moved the load off the boolean rather than putting the boolean under load.

### F9 — MEDIUM. `E11` — the mutant corpus's gate results can be discarded silently

`build.py:349`: `failures.extend(gate_failures(mutants))` → `gate_failures(mutants)`. Both layers green. Fifteen of the thirty-five worlds — including five of the thirteen this cell is about (`v-29ace70e`, `v-379c937f`, `v-bd2babb4`, `v-d2c2b1b9`, `v-efe43df1`) — stop being gated and nothing says so. Note `tests/support.py:24` sets `WORLD_IDS` from `CATALOGUE` only, so the new per-world tests cover 20 of 35 worlds; the mutant half is covered by the build alone, and E11 removes that.

### F10 — LOW. The partition is not total for nameless rows (A09)

`truth.py:238`. Insert `if "name" not in row: continue`. Both layers green. `classify_invariants`'s docstring says "no row can escape the partition" and cites `test_the_three_classes_partition_the_input` as the assertion that matters — but every row in `ROWS` carries a `name`, so the `row.get("name", "<unnamed>")` default is never exercised and a row can be dropped from all three lists. Defensive-only today (`check_invariants` always writes a `name`), but the docstring's claim is stronger than the test.

### F11 — LOW. Provenance and documentation

- `runs/…/RUN_STATE.md:8` points at `ADVERSARIAL-VERBATIM.md`. **The file does not exist** and is not in `MANIFEST.json`.
- `MANIFEST.json` hashes sources, tests, `evidence/*` and all 70 artefacts, but not `FLIPS.md`, `RUN_STATE.md` or `OPTIMISTIC-DEFAULTS.md` — the three narrative files, two of which have been edited since the commit.
- `worldgen/README.md:117` — "**invariants** — every declared invariant, checked on every reachable state" — is now wrong twice over (three are checked on transitions) and was the optimistic framing before V19.
- `test_build_gate.py:33-36`'s named-gate list, whose stated purpose is "a gate *dropped* is exactly the regression", was not updated to name `invariant_unverified`. (The sandbox catches `E06` anyway, via real assertions — verified — so this is cosmetic.)

### What I tried and could not break

- **Old-writer, self-contradictory and malformed rows.** Every one of the 13 adversarial shapes lands where the docstring says, including `{verified: True, holds: False}` with no status (→ `violated`) and `{verified: 1, holds: 1, status: "holds"}` (→ `unverified`).
- **Vacuity.** `check_invariants(world, [])` → every row `unverified`, no `holds` key, `all_invariants_hold` False. Edge-only invariant on 0 transitions → `unverified`. This is closed at `truth.py:344-356` **and** has a positive control (`test_the_same_invariants_do_verify_on_a_real_state_set`). Good work; the work order predicted this would be the hole and it is not.
- **Both callables, one failing.** `check` fails / `edge` passes → `violated`; `check` passes / `edge` fails → `violated`. Correct both ways.
- **Cross-track consumers.** Nothing outside `worldgen/` reads `invariants_all_hold`, `invariant_failures`, `invariant_status` or an invariant `holds`. `exam/` reads `ground_truth.json` for solvability/palette/rules and iterates `invariants` only for `statement` strings (`exam/tests/test_worldgen_papers.py:55`); `battery/`, `theory-compiler/`, `fuzzlab/` use unrelated "invariant" concepts. `exam/tests/test_worldgen_papers.py` — 95 passed against the regenerated artefacts. `claims_now_false` is unchanged (`H01`/`H02` are equivalent mutants — confirms the implementer's claim empirically).
- **Hand editing.** I re-derived all 35 `ground_truth.json` **and** `GROUND_TRUTH.md` from the current generator into a temp tree: **0 byte mismatches**. All 91 MANIFEST hashes match. `--check` exit 0.
- **The sandbox's anchor discipline.** Breaking `_TABLE_ANCHOR` with the guard intact → `InjectionFailed`, tests red (G02). Breaking it *with the guard disabled* → still red, because the injection tests assert **red** outcomes (G03). A failed patch cannot produce a green control for the injections. (It can for `boolean_default` — F7.)

### (c), settled with numbers

The three `edge_check`s are not decorative. I instrumented the reachable graph of all 35 worlds and counted transitions on which the monotone quantity actually **moves**:

```
latch bit rises:            111    net bit rises:       111
collected count rises:       94    lock openings:        42
tile state rises:            43    collapsed-tile transitions: 995
```

And all six discriminating mutants go red on **both** layers: `F02`/`F07`/`F12` (comparison direction flipped) and `F16`/`F17`/`F18` (`return False`). The "13 resolved worlds" are resolved by a real, exercised, consumed measurement. `F05`/`F10`/`F15` (revert to `"check": None`) go red via `invariant_unverified` — the gate does what it says. This attack line fails, and I say so plainly.

The one soft spot: `F03/F04/F08/F09/F13/F14` — dropping any single *clause* from any of the three checks is green everywhere. That is arithmetically unavoidable for a passing check, but it means the "both clauses of the sentence" claim in `FLIPS.md` is unfalsifiable on this catalogue. Note also `latch_rise == latch_net_rise` in every world: the per-switch clause and the net clause never separate here, so the second clause is measured but has no discriminating power in the current corpus.

---

## 3. FULL MUTANT TABLE (80)

`pytest` = `python -m pytest worldgen -q`; `build` = `python -m worldgen.build --into TMP --quiet`. Each mutant ran in its own copy of the package.

| mutant | what it changed | pytest red? | build red? | ESCAPED? |
|---|---|---|---|---|
| A01-holds-key-optimistic-default | `classify`: `row.get("holds", True)` | yes | no | |
| A02-holds-ignores-status | `classify`: drop `status == HOLDS` | yes | no | |
| A03-holds-ignores-verified | `classify`: drop `verified is True` | yes | no | |
| A04-truthy-not-identity | `classify`: `is True` → `bool(...)` | yes | no | |
| A05-sink-to-holds | `classify`: sink branch → `holds` | yes | no | |
| A06-sink-to-violated | `classify`: sink branch → `violated` | yes | no | |
| A07-drop-status-violated-clause | `classify`: drop `status == VIOLATED` | yes | no | |
| A08-drop-verified-violated-clause | `classify`: drop `verified/holds False` | yes | no | |
| **A09-nameless-rows-vanish** | `classify`: skip rows with no `name` | **no** | **no** | **ESCAPED** |
| A10-unverified-list-emptied-at-return | `classify` returns `unverified: []` | yes | no | |
| A11-violated-list-emptied-at-return | `classify` returns `violated: []` | yes | no | |
| A12-violated-and-unverified-swapped | `classify` swaps two lists | yes | no | |
| B01-all-hold-ignores-unverified | `all_invariants_hold` drops unverified | yes | no | |
| B02-all-hold-ignores-violated | drops violated | yes | no | |
| B03-all-hold-always-true | `return True` | yes | no | |
| C01-prose-branch-reports-holds | prose row stamped `holds` | yes | no | |
| **C02-prose-branch-drops-status-stamp** | prose row loses `status` key | **no** | **no** | **ESCAPED** |
| C03-vacuity-guard-disabled | `if False and not violations…` | yes | no | |
| C04-vacuity-guard-states-only | `evidence += len(states)` → 0 | yes | yes | |
| C05-vacuity-guard-edges-not-counted | `evidence += edges` → 0 | yes | yes | |
| C06-edge-check-never-runs | edge branch disabled | yes | yes | |
| **C07-edge-loop-first-transition-only** | `transitions(states)[:1]` | **no** | **no** | **ESCAPED** |
| **C08-state-loop-first-state-only** | `for state in states[:1]` | **no** | **no** | **ESCAPED** |
| C09-holds-hardcoded-true | `row["holds"] = True` | yes | no | |
| **C10-status-hardcoded-holds** | `row["status"] = INV_HOLDS` | **no** | **no** | **ESCAPED** |
| C11-status-hardcoded-violated | `row["status"] = INV_VIOLATED` | yes | yes | |
| **C12-check-exception-swallowed** | state-loop `except` → `continue` | **no** | **no** | **ESCAPED** |
| **C13-edge-exception-swallowed** | edge-loop `except` → `continue` | **no** | **no** | **ESCAPED** |
| **C14-states-checked-misreported** | `states_checked = 0` | **no** | **no** | **ESCAPED** |
| **C15-transitions-checked-misreported** | `transitions_checked = 0` | **no** | **no** | **ESCAPED** |
| C16-verified-stamp-false | `row["verified"] = False` | yes | yes | |
| C17-edge-violations-not-recorded | edge violations dropped | yes | no | |
| **C18-transitions-checked-key-omitted** | key never written | **no** | **no** | **ESCAPED** |
| **C19-edge-loop-half-the-transitions** | `transitions(...)[::2]` | **no** | **no** | **ESCAPED** |
| **C20-state-loop-half-the-states** | `states[::2]` | **no** | **no** | **ESCAPED** |
| D01-ground-truth-all-hold-true | `"invariants_all_hold": True` | yes | no | |
| D02-ground-truth-status-emptied | `invariant_status` all empty | yes | no | |
| **D03-markdown-unverified-marker-removed** | drop `**unverified**` | **no** | **no** | **ESCAPED** |
| **D04-markdown-violated-marker-removed** | drop `**VIOLATED**` | **no** | **no** | **ESCAPED** |
| **D05-markdown-summary-always-true** | summary hardcodes `true` | **no** | **no** | **ESCAPED** |
| D06-markdown-rulecorr-and-not-or | `or` → `and` in the new guard | yes | no | |
| **D07-markdown-omits-unverified-bullets** | unverified rows unrendered | **no** | **no** | **ESCAPED** |
| D08-markdown-invariant-section-dropped | render no invariants at all | yes | no | |
| E01-row-violated-emptied | `build_world` row → `[]` | yes | no | |
| E02-row-unverified-emptied | `build_world` row → `[]` | yes | no | |
| E03-totals-unverified-emptied | totals → `[]` | yes | no | |
| E04-totals-failures-emptied | totals → `[]` | yes | no | |
| E05-totals-keys-swapped | two totals keys swapped | yes | no | |
| E06-unverified-gate-removed | `GATES` entry deleted | yes | no | |
| E07-violated-gate-removed | `GATES` entry deleted | yes | no | |
| E08-missing-key-back-to-optimistic-get | `totals.get(key, ())` restored | yes | no | |
| E09-gate-failures-returns-empty | `return []` | yes | no | |
| E10-main-exits-zero-on-gate-failure | `return 1` → `return 0` | yes | no | |
| **E11-mutant-gate-results-discarded** | mutant gate output dropped | **no** | **no** | **ESCAPED** |
| E12-gates-tuple-emptied | `GATES = ()` | yes | no | |
| **F01-latch-edge-check-returns-true** | `latch_monotone → True` | **no** | **no** | **ESCAPED** (expected) |
| F02-latch-monotone-direction-flipped | `<` → `>` | yes | **yes** | |
| **F03-latch-per-switch-clause-dropped** | clause disabled | **no** | **no** | **ESCAPED** |
| **F04-latch-net-clause-dropped** | clause disabled | **no** | **no** | **ESCAPED** |
| F05-latch-reverted-to-prose | `edge_check` → `check: None` | yes | **yes** | |
| **F06-collection-edge-check-returns-true** | `→ True` | **no** | **no** | **ESCAPED** (expected) |
| F07-collection-direction-flipped | `<` → `>` | yes | **yes** | |
| **F08-collection-count-clause-dropped** | clause disabled | **no** | **no** | **ESCAPED** |
| **F09-collection-lock-reopen-clause-dropped** | `now_closed <= was_closed` → `True` | **no** | **no** | **ESCAPED** |
| F10-collection-reverted-to-prose | `edge_check` → `check: None` | yes | **yes** | |
| **F11-tile-edge-check-returns-true** | `→ True` | **no** | **no** | **ESCAPED** (expected) |
| F12-tile-monotone-direction-flipped | `>=` → `<=` | yes | **yes** | |
| **F13-tile-monotone-clause-dropped** | monotone clause dropped | **no** | **no** | **ESCAPED** |
| **F14-tile-collapsed-crossing-clause-dropped** | crossing clause dropped | **no** | **no** | **ESCAPED** |
| F15-tile-reverted-to-prose | `edge_check` → `check: None` | yes | **yes** | |
| F16-latch-edge-check-returns-false | `→ False` | yes | **yes** | |
| F17-collection-edge-check-returns-false | `→ False` | yes | **yes** | |
| F18-tile-edge-check-returns-false | `→ False` | yes | **yes** | |
| **G01-sandbox-anchor-guard-disabled** | `if found != 1:` → `if False:` | **no** | **no** | **ESCAPED** |
| G02-sandbox-table-anchor-broken-guard-intact | anchor corrupted | yes | no | |
| G03-sandbox-anchor-broken-and-guard-disabled | both | yes | no | |
| **G04-sandbox-pythonpath-not-isolated** | real checkout appended to path | **no** | **no** | **ESCAPED** (equivalent) |
| G05-sandbox-gate-lines-always-empty | `gate_lines()` → `()` | yes | no | |
| **H01-mutate-now-false-back-to-optimistic-get** | pre-V19 idiom restored | **no** | **no** | **ESCAPED** (equivalent) |
| **H02-mutate-now-false-includes-unverified** | widened to unverified | **no** | **no** | **ESCAPED** (equivalent) |

**14 mutants turned the build red. 36 were caught by pytest only. 30 escaped.**

---

## 4. ESCAPEES, DISCUSSED

**Tier 1 — reconstruct the defect or gut a layer (12).** `C12`/`C13` (F1): the exception branch is undefended and its removal produces `holds: true, states_checked: 24` for a check that never returned. `C07`/`C08`/`C14`/`C15`/`C18`/`C19`/`C20` (F2): the loops and the counts they report can be hollowed out in seven distinct ways; the artefact then overstates its own evidence, and neither `pytest` nor `build` nor `--check` notices. `D03`/`D04`/`D05`/`D07` (F4): the Markdown can be made to never again print `**VIOLATED**`, never print `**unverified**`, always print `` `true` ``, and omit unverified bullets — all four green, because the catalogue contains 165 `holds` rows and nothing else. This is C11's escapee shape precisely: a layer that is only ever exercised on inputs where it cannot be wrong.

**Tier 2 — real gaps, lower blast radius (5).** `E11` (F9): the mutant half of the gate can be discarded. `C10`: `status` can be hardcoded to `holds` — the redundancy in `classify_invariants` absorbs it for the *classification*, but the artefact then ships rows reading `"status": "holds", "holds": false`, and nothing checks a row against itself. `C02`: the prose branch's explicit stamp is removable because no shipped world has a prose row. `A09` (F10): nameless rows leave the partition. `G01`: `invariant_sandbox.py`'s own anchor guard — the discipline the file's docstring is proudest of — has no test; disabling it is green because the anchors currently apply. (`G02`/`G03` show the *consequences* of a failed patch are caught, so the guard is belt-and-braces, not load-bearing — but it is untested.)

**Tier 3 — informative negatives, correctly green (10).** `F01`/`F06`/`F11` (`edge_check → True`) must be green: a check that never fails cannot fail a catalogue where nothing is wrong. They prove nothing on their own, which is why I ran `F02`/`F07`/`F12` and `F16`/`F17`/`F18` — all six red on both layers. `F03`/`F04`/`F08`/`F09`/`F13`/`F14` (clause drops) cannot go red by construction; they measure that the clauses have no independent test coverage, which they do not.

**Tier 4 — equivalent mutants, reported for honesty (3).** `G04` (I appended rather than prepended to `PYTHONPATH`, so `root` still wins — my error, not a finding), `H01` and `H02` (both confirm the implementer's own claim that `claims_now_false` is unchanged; no mutant world has an unverified invariant).

---

## 5. WHAT I COULD NOT CHECK

- **`python -m worldgen.verify`.** Not run, per the work order — cell V12's known `out/qc/` rewrite. Its interaction with the new `invariant_status` key is therefore untested by me; `qc/run_qc.py:81,170` reads only `raw_trace.jsonl`, which V19 did not touch, so I have no reason to expect one.
- **Other tracks' full suites.** I ran `exam/tests/test_worldgen_papers.py` (95 passed) because it reads the regenerated artefacts directly. I did not run all of `exam/`, `battery/`, or `theory-compiler/` — out of territory, and my grep found no consumer of any invariant verdict outside `worldgen/`.
- **Whether the three monotonicity claims are *true statements about the mechanisms*** as opposed to true on the reachable graphs of these 35 worlds. The `edge_check`s are exhaustive over each world's reachable graph, which is the strongest available claim; a mechanism-level proof is out of scope for a build gate.
- **Whether `deferred`/`unreachable` reversibility claims (F5) are individually correct.** I established that 90 of 218 are unexercised and that the gate cannot fail on them. I did not attempt to verify any of them, and I did not fix it — it is a separate cell.
- **The exact state of the branch at the time you read this.** The implementer committed `23ec179` and has continued editing `worldgen/RUN_STATE.md` and two run-directory files during this review. Everything I measured is pinned to the MANIFEST hashes, which all still matched at the end of the review. I made no commits and dirtied no artefacts.
