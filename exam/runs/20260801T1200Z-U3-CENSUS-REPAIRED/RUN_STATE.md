# U3 census re-run on the repaired adjudicator, and the verdict pre-registration audited

**Branch:** `z/exam-u3-followthrough` (worktree; not pushed, not merged)
**Base:** `01d627e3` = master `e8345aff` + `ep/u3-exam-audit` merged in
**Territory:** exam only. Nothing outside `exam/` is touched.
**Spend:** zero. No API call, no model call, no network. Lean 4.9.0 locally, and
the exam suite. Nothing here needed a live run and nothing here was blocked by
not having one.

---

## 0. Two premises in the work order were wrong, and the second one matters

**`exam/u3_census.py` is not on master.** It and `exam/tests/test_u3_census.py`
live on `ep/u3-exam-audit` (`77f18b41`, `4d9c6612`), which is unmerged. A
worktree cut from master alone has neither file, and the four tests that "must
flip" cannot be red because they do not exist there. This branch therefore
merged `ep/u3-exam-audit` in before doing anything else. **That branch is still
unmerged and this one does not merge it either** — the census that produced
today's 14/24 is not on the mainline, so anyone reading master's history sees
the freeze-side census and not exam's independent one.

**Four tests were named; six were red.** freeze's inbox note
(`monitor/inbox/20260801T0700Z-freeze-to-exam-…`) lists four. The measured
baseline on this branch was **6 failed, 532 passed**. The two it did not name:

* `test_level_lean_book_is_adjudicated_not_reported_as_no_evidence` — not a
  defect-assertion at all. It pinned `census_route == "u3.eval_lean_source:…"`,
  and since `u3.evaluate` now reaches the proof layer by itself the census's
  fallback is correctly *not taken*. The verdict never moved; the route did.
* `test_FINDING_deadlock_paradigm_on_disk_is_labelled_vacuous` — the real-artefact
  half of F1, which freeze's note discusses at length in prose but omits from
  its numbered list.

Neither changes the ruling. Both are recorded because "four tests must flip" is
the kind of claim a later reader checks by counting.

---

## 1. The tests, flipped — and what now guards against name-keying returning

The point was never to delete the evidence that the defect existed. Each test
below keeps the finding in its docstring and inverts only the assertion.

| test | was | is |
|---|---|---|
| `test_FINDING_renaming_the_theorems_alone_flips_the_verdict` | frobnicate ⇒ `vacuous`, inv ⇒ `discharged` | renamed as `test_REGRESSION_F1_renaming_the_theorems_does_not_move_the_verdict` |
| `test_FINDING_deadlock_paradigm_on_disk_is_labelled_vacuous` | C4 ⇒ `vacuous` | `test_REGRESSION_F1_deadlock_paradigm_on_disk_attains` |
| `test_kind_coverage_names_the_kinds_that_can_never_attain` | kind `unknown` exists and is a gap | `test_kind_coverage_splits_permanent_non_attainers_from_gaps` |
| `test_level_lean_book_is_discovered` (2nd half) | `u3.evaluate` ⇒ `no_evidence` | `!= "no_evidence"`, kept inverted so a **freeze** regression reads here |
| `test_deeply_nested_book_is_discovered` (2nd half) | `deep not in expand_targets` | `deep in expand_targets` |
| `test_level_lean_book_is_adjudicated…` | route pinned to `eval_lean_source` | verdict pinned, route accepted either way |

**Three tests are new, and they are the actual insurance.**

`test_REGRESSION_F1_renaming_the_theorems_does_not_move_the_verdict` does not
merely assert the pair agrees — an adjudicator that said `discharged` to
everything would satisfy that. It asserts three things at once:

1. the pair agrees and both attain, theorem-kind by theorem-kind;
2. on the renamed book **every `name_hint` is `None`** and it attains anyway,
   so the deciding path demonstrably did not consult a name;
3. `ODDLY_NAMED_TAUTOLOGY` — new fixture, the tautology renamed the same way —
   is **still `vacuous`**, so (1) is not being bought with a checker that
   stopped refusing.

`test_REGRESSION_F1_deadlock_paradigm_on_disk_attains` guards the same property
on the real artefact, and asserts the three `prune` sub-checks by name rather
than the label alone. It also uses a fact that only exists after the repair: on
that file the hint and the kind **disagree** — `dead_persists` and `dead_closed`
are hinted `prune` and read as `invariant`, `no_goal_pinned` is hinted
`unsolvable` and reads as `unclassified` — and a theorem the old matcher did not
recognise at all (`closed_pinned`) is among the four that carry it to
`discharged`.

*(One assumption in the first draft was wrong and the measurement said so: I
expected `dead`'s `name_hint` to be `None`. It is `prune` — the old prefix list
contained `"dead"`. The deadlock development was never a name-recognition
failure; it was the `prune` kind having no (c) check at all, exactly as freeze's
note says. The test now asserts the statement-derived basis instead.)*

`test_direct_source_fallback_still_fires_when_the_adjudicator_goes_blind` keeps
exam's own fallback route alive. Since the repair, `u3.evaluate` finds a
`Level.lean` unaided, so the fallback is never exercised by the happy path and
could rot to an exception unnoticed. The test blinds `u3.find_books`, checks the
blinding took (`no_evidence`), and asserts the census still reaches `attained`.

`test_kind_coverage_reports_a_real_gap_as_a_gap` is the negative control for the
coverage split, with a new `UNCLASSIFIABLE_MANUAL` fixture — a real idempotence
lemma about the step function, fully proved, outside every shape §1.2.1 writes a
requirement for. It must read `unclassified`, and `unclassified` must appear in
`coverage_gaps` and not in `permanent_non_attainers`.

### The breakage matrix

A test that has never been seen to go red has not been shown to check anything.
Each guarantee was broken in-process and the suite re-run
(`break_the_guarantees.py`, shipped in this run directory):

| breakage | result |
|---|---|
| kind taken from `name_hint` again (name-keying restored) | **7 failed**, incl. both F1 regressions |
| `permanent_non_attainers` folded back into `coverage_gaps` | **1 failed** — the split test |
| gap detector dead (the old substring sniff, restored) | **2 failed** — both coverage tests |
| census's direct-source fallback deleted | **1 failed** — the blinding test |

---

## 2. A defect the repair created in exam's own code, found by looking

`kind_coverage()` decided "this kind has no (c) check" by testing whether the
substring `"no executable"` appeared in E1's `why` text. **freeze's repair
stopped writing that sentence.** The table did not go red. It went *empty*:

```
old: "kinds_that_can_never_attain": ["unknown"]
new (before this fix): "kinds_that_can_never_attain": []
```

A clean bill of health manufactured by a lookup miss, on the one output whose
entire job is to report gaps — and the docstring three lines above it warns
against precisely that failure mode for a different reason. It now keys on
`freeze.theorem_shape.KINDS_WITH_A_C_CHECK`, an exported name, so the next such
change is an `ImportError` rather than a silence.

The table also gained a split freeze suggested and was right about:
`point_claim` and `witness` are **permanent** non-attainers — supporting
obligations, not claims about the world, and §1.2.1 will never write a
requirement for them. Listing them beside a real gap makes the real gap
unfindable. `kinds_that_can_never_attain` is retained as the union, because a
field that quietly narrows is worse than one that is renamed.

`t.get("kind", "unknown")` now defaults to `unclassified`; `unknown` is a kind
E1 no longer produces.

---

## 3. The census, re-run over everything on disk

```
cd exam && python u3_census.py --root .. --expect-books 24 \
    --json runs/20260801T1200Z-U3-CENSUS-REPAIRED/census.json \
    --md   runs/20260801T1200Z-U3-CENSUS-REPAIRED/census.md
```

Byte-reproducible: a second run produced identical bytes for both files.

### Books — 14/24 → **17/24**

| label | 04:00Z | now |
|---|---|---|
| `discharged` | 14 | **17** |
| `vacuous` | 9 | **2** |
| `unclassified` | — (did not exist) | **4** |
| `failing_obligation` | 1 | 1 |

The denominator is the same 24 directories and the same 24 rows. **Seven rows
moved, all of them in `theory-compiler`, and every move is out of `vacuous`** —
this repair only ever withdraws an accusation:

| book | was | is |
|---|---|---|
| `theory-compiler/lean` | vacuous | **discharged** |
| `theory-compiler/runs/…-C4-deadlock-lean` | vacuous | **discharged** |
| `theory-compiler/runs/…-C4-deadlock-lean/verify` | vacuous | **discharged** |
| `handover_packages/a0-cart/levels/base` | vacuous | unclassified |
| `handover_packages/a0-cart/levels/no-button` | vacuous | unclassified |
| `handover_packages/a0-sokoban2/levels/crossing-up` | vacuous | unclassified |
| `handover_packages/a0-sokoban2/levels/match` | vacuous | unclassified |

`theory-compiler` goes **0/7 → 3/7**; no other territory's numbers move at all.

**This matches freeze's independent census exactly** (`freeze/runs/
20260801T0700Z-E1-kind-census/`: discharged 14→17, vacuous 9→2, unclassified
0→4, failing_obligation 1→1, theory-compiler 0/7→3/7). Two enumerations built by
different territories from different starting points agree on all 24 rows. That
is the strongest thing in this run record and it is worth more than either
number alone.

### Bookless claimants — 15 → **20 runs, 0 attained**

`0 attained` is unchanged. The count is **not** the adjudicator's doing: five
run directories appeared on disk between 04:00Z and now.

```
+ theoria-arm/runs/20260731T231654Z-R1-g50t-a     declared_refusal
+ theoria-arm/runs/20260731T231654Z-R1-sk48-b     declared_refusal
+ theoria-arm/runs/20260801T001851Z-R1b-g50t-a    declared_refusal
+ theoria-arm/runs/20260801T001851Z-R1b-sk48-b    declared_refusal
+ theoria-arm/runs/audit-smoke                    no_evidence
```

Nothing left the set and no label changed. The four R1/R1b legs are today's live
legs; they reached certify and wrote no manual, which is what
`declared_refusal` means and why they are counted separately. **Two independent
causes were at work in one diff and they are separated here on purpose**: had
they not been, "claimants rose by five" would have read as an effect of the
repair.

### The denominator caveat still travels inside the JSON

Unchanged and verified in the emitted artefact:

```json
"denominator_meaning": "Every Lean development on disk, one row per directory.
  This is an ENGINEERING denominator -- it says what the repo contains. It is
  NOT STATS_RULES.md §1.2's denominator."
"not_the_frozen_endpoint": "STATS_RULES.md §1.2: the U3 attainment rate's
  denominator is fixed at 19 sealed games (12 at the clean layer) … Nothing on
  disk today is a sealed game, so the frozen rate is not computable from this
  census and this census does not claim to compute it."
```

`17/24 = 0.708` is **not** the U3 endpoint and this run does not report it as
one. `test_attainment_rate_carries_its_denominator_meaning` is unchanged and
still green.

### Kind coverage, after the split

| kind | theorems | (c) passed | (c) never ran | check? |
|---|---|---|---|---|
| `invariant` | 39 | 35 | 0 | yes |
| `prune` | 2 | 2 | 0 | yes (new) |
| `unsolvable` | 1 | 0 | 0 | yes |
| `point_claim` | 20 | 0 | 20 | no — permanent |
| `witness` | 10 | 0 | 10 | no — permanent |
| `unclassified` | 16 | 0 | 16 | **no — coverage gap** |

`coverage_gaps: ["unclassified"]`, 16 theorems across 4 books. That is a real
gap and it is now the only thing in the list.

**The `unsolvable` residual is not closed and is now sharper, not softer.** It
was 0/14 at 04:00Z; it is **0/1**. The 13 that left were reclassified by shape,
not discharged. Every attainment in this census still comes through `invariant`
or `prune` — the `unsolvable` (c) check has still never been observed to say yes
on this repo, and freeze's note names why (`c_init_has_action` has no
source-level test and leans on a run record's `trace_transitions`, which a bare
Lean book never carries).

---

## 4. The verdict-question pre-registration, audited against its own acceptance

`prereg_acceptance.py` recomputes each acceptance condition from the built
paper, the key and the control transcripts. It does not read the document's
claims back — every number below was computed, and A1/A2 read the class off
`Item.truth["class"]` on the built paper so the audit *can* disagree with
`prereg.py`.

```
PASS A1 exactly three classes
       paper ['large_unsolvable','small_unsolvable','solvable_hard'];
       inventory identical
PASS A2 the shipped mix is the pre-registered mix
       {'large_unsolvable': 4, 'small_unsolvable': 5, 'solvable_hard': 8}
PASS A3 every item carries a construction basis
       17/17; none missing, none absent from the inventory
PASS A4 the shortest basis is not a gesture
       shortest is 364 chars (vq-1881c8c383)
PASS B1 both rates are defined on every control
PASS B2 BA is derived from the two, not reported alone
       BA == (sens+spec)/2 recomputed for all seven
PASS C bluffer (always `unsolvable`) scores badly on SPECIFICITY
       spec 0.000 < S_min 0.5, sens 1.000 — refused for the right reason,
       not by being bad at everything
PASS D denier (never says `unsolvable`) scores badly on SENSITIVITY
       sens 0.000, spec 1.000 — the transpose
PASS CD the pair is a transpose, not one number printed twice
PASS CD2 the two are not killed by the same rule
       bluffer: specificity floor (一票否决, independent of BA)
       denier:  BA floor
```

| examinee | sens | spec | BA | cov(ii) | cert | verdict |
|---|---|---|---|---|---|---|
| oracle | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 成立 |
| bluffer | 1.000 | **0.000** | 0.500 | 1.000 | 0.000 | 不成立 |
| denier | **0.000** | 1.000 | 0.500 | 1.000 | — | 不成立 |
| overclaimer | 1.000 | 0.375 | 0.688 | 1.000 | 0.000 | 不成立 |
| abstainer | 0.000 | 0.000 | 0.000 | 0.000 | — | 不成立 |
| memoriser | 0.556 | 0.625 | 0.590 | 0.000 | 1.000 | 不可结论 |
| null | 0.000 | 0.000 | 0.000 | 0.000 | — | 不成立 |

**Verdict: ACCEPTED, 10/10 conditions.** The three classes exist with a
construction basis apiece, sensitivity and specificity are separate numbers on
every row, and the two negative controls fail in the two different directions
the document says they must — **and by two different rules**, which is the part
that makes the pair worth having rather than one control printed twice.

### The auditor's own negative control

An auditor observed only to say yes has not been shown to check anything.
`prereg_acceptance_selftest.py` breaks four things and re-runs the audit:

| breakage | audit verdict | caught by |
|---|---|---|
| `S_min = 0.0` (the floor cannot fire) | FAILED | C, D, CD2 |
| BA floor made non-strict (`>=`) | FAILED | C, D, CD2 |
| one item's construction basis blanked | FAILED | A3, A4 |
| a fourth class shipped | FAILED | A1, A2 |

`breakages the audit MISSED: none`, and the restore run returns ACCEPTED, so the
artefact this run record ships is the clean one.

**Stated honestly:** the two floor breakages are caught but not cleanly
*attributed* — both turn C, D and CD2 red, because the harness's patches are
coarse (blinding `S_MIN` also perturbs the reason strings CD2 reads). The claim
this run supports is "no breakage went unnoticed", not "each condition isolates
one rule". The proper leave-one-out already exists and is green:
`test_every_floor_catches_something_on_its_own` and the `floor_leave_one_out`
block in `artifacts/prereg/verdict_prereg.json`.

---

## 5. Gates

```
cd exam && python -m pytest -q
  540 passed, 2 xfailed in 292.41s
  (baseline on this branch before any edit: 6 failed, 532 passed)

python exam/verify.py
  build_papers               ok
  pytest                     ok
  run_exam --calibrate       ok
  run_selftest               ok
  build_prereg               ok
  withdrawn_claims           ok
  artefact_locations         ok
  artifacts_match_committed  ok
  determinism                ok
  GREEN
```

Nine stages, not the seven the work order expected — `build_prereg` and
`artifacts_match_committed` are recent additions. All green.

Census reproducibility: two runs, byte-identical `census.json` and `census.md`.
Determinism stage: identical digests under `PYTHONHASHSEED` 7 and 99.

Breakage matrix method (§1), for replay:

```python
# in-process, via a pytest -p plugin that monkeypatches before collection
S.parse_development -> re-kind every theorem from S.name_hint(name)   # 7 red
u3_census.kind_coverage -> coverage_gaps = the union                  # 1 red
u3_census.CHECKED_KINDS = frozenset(); all no_check_implemented=False # 2 red
u3_census.adjudicate_site -> u3.evaluate only, no fallback            # 1 red
```

---

## 6. Residual gaps, stated not closed

1. **`ep/u3-exam-audit` is still unmerged, and so is this branch.** The 14/24
   figure the work order quotes is on a branch master has never seen. Merging is
   not this ticket's call, but a Phase 4 reader working from master will find
   freeze's census and not exam's, and the cross-check in §3 — the best evidence
   in this run — is invisible from there.
2. **The `unsolvable` (c) check has never been observed to say yes.** 0/1 on
   this repo, 0/14 before. freeze's `c_init_has_action` residual is the cause and
   it is not exam's to close. Until a book carries a `trace_transitions` record,
   no development can attain through an `unsolvable` theorem, and the census
   cannot tell that apart from "no book tried".
3. **16 `unclassified` theorems across 4 books are a live coverage gap.** They
   fail closed, which is safe, and they now say the honest word instead of
   `vacuous`. But the four `handover_packages` books cannot attain through any
   theorem they contain, whatever they prove. That is a §1.2 scope question
   (extend E1, or narrow §1.2 on purpose) and it belongs to freeze.
4. **`certified_share` is published and not gated** — the `cheater-v4` blind
   spot §6 of `PREREG_VERDICT.md` declares. Unchanged by this run; the amendment
   request is already in the inbox.
5. **The audit does not attribute floor breakages to single conditions** (§4).
6. **Nothing here was run against a sealed game, and nothing could be.** Zero
   sealed-pile contact, by construction: every input is a Lean file already in
   the repository or a synthetic control transcript.
