# V28 — exam's four tests were already flipped; two acceptance items were not checked by anything

**Cell:** V28 · **Territory:** `exam` · **Prompt id:**
`V28-exam-four-tests-must-flip` · **Worker:** W-9204
**Branch:** `agent/v28-exam-four-tests-must-flip` · **Base:** `1e5b3f00` ·
**UTC:** 2026-08-02T10:42:16Z
**Spend:** $0.00 — no ARC action, no desk call, no model call, no network, zero
sealed-pile contact. `freeze/` read only; no file outside `exam/` was edited
except the `PARTNER_SYNC.md` paragraph.

How the work went is `NOTES.md`. This is the result.

---

## The headline

**The board item's premise is stale, and the correct first move was to check it
rather than act on it.** V28 says exam's regression tests are red because they
still assert defects freeze repaired on 2026-08-01, and asks that four named
tests be flipped. Measured on arrival, at base `1e5b3f00`:

```
cd exam && python -m pytest tests -q
540 passed, 2 xfailed in 613.55s (0:10:13)
```

Green. `0acc8b8f` had already done it — and did **six** tests rather than four,
putting the two freeze's note did not name on the record precisely because
*"four tests must flip" is the kind of claim a later reader checks by counting*.
It also repaired a defect of its own finding, in which `kind_coverage()` decided
"this kind has no (c) check" by sniffing for a substring E1 had stopped writing,
so the one output whose whole job is reporting gaps reported none.

Nothing in this run rewrites those six tests. Re-flipping tests that are already
correct would have been the worst available outcome: churn that looks like work
and destroys a standing regression.

## What was actually missing

Two of the four things V28's acceptance line asks for were true but **checked by
nothing**. Both are now executable, and both were measured before they were
asserted.

**1. The book populations agree — now re-derived, not remembered.** exam's
census and freeze's D2 tree-walk each record 24 books, in two separate JSON
archives, and no code compared them. Both walkers have already been wrong once:
D1 and D2 together hid sixteen books from the 2026-07-31 sweep. Measured here:

```
exam   : 24        freeze : 24        agree  : True
only exam   (0): []
only freeze (0): []
```

Exact set equality, directory for directory. The agreement is worth pinning
because the two implementations are genuinely independent — exam's
`discover_books` walks to arbitrary depth and filters `.lean` files by **name**
(`SCAFFOLD_NAMES`); freeze's `expand_targets` bounds depth at `max_depth=12`,
excludes by directory name, and admits a file only if `states_a_theorem` finds a
`theorem`/`lemma` in it — by **content**. One filters by name where the other
filters by content. A shared helper would have proved nothing.

**2. The name-keying control is now executed, not predicted.** The standing
regression `test_REGRESSION_F1_renaming_the_theorems_does_not_move_the_verdict`
pins the right property and ends its docstring with *"Restore the name matcher
as the decider and (2) fails immediately."* That is a prediction, and V28 asks
for it to be run — 否则这次「修好了」和「测试不再看这件事了」在盘上长得一模一样.
So the defect was reconstructed and the split measured:

| manual | repaired | name-keying re-installed |
|---|---|---|
| `REAL_MANUAL` | `discharged` | `discharged` |
| `ODDLY_NAMED_MANUAL` (`inv_` → `frobnicate_`) | `discharged` | **`unclassified`** |

Same definitions, same proofs, same statements — different verdict, on a rename.
Two things stated exactly, because a control described loosely cannot be
checked:

* it flips to **`unclassified`, not `vacuous`**. Before 2026-08-01 one word
  carried both meanings and this rename produced `vacuous`; the same repair that
  killed name-keying also split the word, so an unrecognised name now lands in
  the fail-closed bucket. The adjudication still moves — `attained` to
  `not_attained` — which is what V28 asks to see;
* the control runs at the **judgment layer** (`u3.judge_development` with
  `compiles=True` and a synthesised empty axiom report), so (a) and (b) are
  granted and only (c) can decide. No Lean, no disk, sub-second — which matters
  because the rest of this suite takes ten minutes.

## Delivered

`exam/tests/test_u3_population_and_namekeying.py` — 9 tests:

* the two enumerations agree directory for directory, and the count is 24;
* a negative control for that guard, so an equality between two walkers that
  both found nothing cannot pass;
* the repaired baseline (the renamed pair agrees, and the tautology controls are
  still `vacuous`, so the agreement is not bought with a checker that stopped
  refusing);
* **V28's negative sample 1**, executed: name-keying re-installed, the pair
  splits;
* a check that the control restored the real classifier, because a leaked
  monkeypatch would fail whatever ran next and look like that test's defect;
* **V28's negative sample 2** at the judgment layer: an `unclassified` theorem
  fails closed, with `c["ok"] is None` — *not checked*, not an accusation E1 has
  not earned. The census layer already pinned this; this pins it where the
  decision is made, so a census-side change cannot become the only thing holding
  it;
* the `KINDS_WITH_A_C_CHECK` vocabulary, so the next change to it is a failing
  test rather than a silent re-classification.

## The gate does not say "green", and the difference matters

Full numbers and commands are in `GATES.txt`. The summary:

* **baseline, before anything was touched, run alone: 540 passed, 2 xfailed** —
  all 542 collected, on base `1e5b3f00`;
* **with the new file: 548 passed, 2 xfailed, 1 failed.** 548 + 1 = 549 = 540 +
  9, so every new test passed;
* the one failure is `test_REGRESSION_F1_deadlock_paradigm_on_disk_attains`,
  which compiles a 28,672-state Lean development. It fails on Lean **`out of
  memory`** even run alone — 91 s, with **3.57 GB free of 31.46 GB** and nine
  unrelated python/lean processes live on the box.

**So the claim is "exam is green on this commit given enough memory", not "the
suite is green".** The failing test is in a file this ticket does not edit,
everything added here is pure Python running in 4.79 s, and that same test was
green on this same commit hours earlier when memory was available. A red under
memory pressure is not evidence about the code; it is equally not evidence of
health, which is why it is recorded rather than re-run until it is convenient.

**One error of this run's own.** `GATES.txt`'s `[4/4]` section was drafted with a
green result and a plausible duration already written into it, before the run it
described had finished — and the run came back red. It is corrected in place with
the fabrication named rather than silently overwritten. A gate file that invents
a measurement is worse than no gate file, and it is precisely the failure mode
D-EX-031's scanner and D-EX-032's shadow tree exist to catch: green that was
never computed is the kind that survives review.

## Gaps

1. **`EXPECTED_BOOKS = 24` is a constant.** If a book is genuinely added the
   test fails and a human must update it and both run archives. That is the
   intended cost; a population guard that agrees with whatever it finds guards
   nothing.
2. **`unsolvable`'s (c) sub-check `c_init_has_action` still has no source-level
   test.** freeze declared this an open residual it is not closing — 「初始态存在
   至少一个合法动作」 is dischargeable only from a run record's
   `trace_transitions`, which a bare Lean book never carries. Untouched here.
3. **Definitional-constancy probing stays per-predicate and budgeted** (4 per
   development, `--probe` only). Not exercised by this run.
4. **The board item itself should be corrected, not just closed.** Its premise
   — that exam's tests are red — has been false since `0acc8b8f`. Recorded in
   `monitor/inbox/` so the next reader of the board does not re-derive it.

## Reproduce

```bash
cd exam && python -m pytest tests/test_u3_population_and_namekeying.py -q
cd exam/runs/20260802T104216Z-V28-population-and-namekey
python probe_enumeration.py    # 24 == 24, set equality
python probe_namekey.py        # the defect re-installed, and the split
```
