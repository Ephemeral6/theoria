# A18 — scorer at run end

`跑完一局即打分` (`Theoria.md:371`) and Phase 1 (5)'s
`逐局跑完即打分入库、与 scorecard 对账`, the half that had never happened.

* ticket: `monitor/board/claimed/A18-scorer-at-run-end.W-A18.md` (worker W-A18)
* branch: `agent/a18-scorer-at-run-end`, base `4c08ea6` (newest `master`)
* territory: `theoria-arm` only
* cost: **zero**. No network, no API call, no model call. Every run here is
  `proxy/mock/arc_mock.py` against a scratch spend pool the test owns; the
  fleet's shared pool is untouched.

---

## 1. What was delivered

### (1) The run scores itself, at its own ending

`theoria-arm/harness/run.py` calls `proxy.scoring.score_run` from `play()`'s
`finally`, between `run_end` and `run.json`. Not a sweep afterwards: Phase 3
audits the order results arrive in, and a batch scored later is a batch
somebody could have scored after seeing it.

* new `score_at_end(run_id, ledger_path, out_dir, ...)` — reconciles and files;
* new `_scores_dir_for(runs_root)` — where the scoring layer's own copy goes;
* new `SCORE_ARTEFACT = "score.json"` — the verdict, in the run's own
  directory, beside `run.json`, following the run-dir convention;
* `Run.write_run_json(summary, score=None)` — the report goes into `run.json`
  too, with the scorer's `{id, version, sha256, frozen_at}` fingerprint, so a
  number can be traced to the rule that produced it (`proxy/SCORING.md` §1);
* `play(..., score=True, scores_dir=None)` — on by default; the switch exists
  so a test can prove the wiring is what produces the verdict;
* the returned summary gains `score_verdict`.

**Production semantics.** `write_incident=True`, `write_artifact=True`.
`--no-incident/--no-artifact` are for a read-only audit
(`proxy/DELIVERY_RULING.md` §5) and a *run* using them would find a mismatch
and record it nowhere. Asserted at the call, not by grepping source.

**Degrades, never crashes.** A scorer whose freeze no longer verifies, an
unreadable ledger, a scorecard that never arrived — each lands as
`UNDETERMINED` in `score.json` with the reason attached, and files a
`score_unreconciled` incident. `UNDETERMINED` is never `PASS`.

### (2) `main()` forwards `ledger_path` — DELIVERY_RULING.md §4 axis 1

The gap that document calls **configuration only**: `Run` and `play()` have
taken `ledger_path` since they were written and `main()` never passed it, so no
invocation of this arm could put its records in `proxy/var/ledger.jsonl`.

`main()` now has `--ledger PATH`, defaulting to **the shared ledger for a live
leg and the run's own directory under `--mock`**. Recorded as `D-A18-002` with
the reason: `tools/audit_delivery.py` counts axis 1 by `arm` alone, so a
rehearsal in the shared file would make axis 1 read as satisfied by a run that
never left this machine.

Axis 2 (a live, non-localhost run) is **not** closed here and is not this
item's to authorise. It costs money.

### (3) Decisions

`theoria-arm/DECISIONS.md` gains `D-A18-001` (score at run end, production
semantics, degrade honestly, score out of the ledger) and `D-A18-002` (the
shared-ledger default, and why it is asymmetric).

### (4) Tests — `theoria-arm/tests/test_score_at_run_end.py`, 11 of them

A new file rather than edits to `tests/test_arm.py`: other sessions are working
in this territory.

| test | what it pins |
|---|---|
| a finished mock game scores itself | end to end, `PASS`, all 13 checks ran, verdict in `score.json` + `run.json` + the summary |
| **a planted score mismatch comes back red** | the negative control (below) |
| the same run without the forgery is green | non-vacuity for the control |
| a run with no scorecard is `UNDETERMINED` | degrade honestly; `score_unreconciled` filed |
| a scorer that cannot run does not take the run down | `ScorerDriftError` → `UNDETERMINED`, run record still written |
| without the wiring there is no verdict at all | non-vacuity for the whole file |
| a rehearsal's score does not land in the shared index | `_scores_dir_for` |
| `main()` forwards the ledger path | live → shared, mock → run dir, `--ledger` wins |
| the CLI really writes where it was told | a whole mock game through `main()` |
| the scorer is reached through the package | no second scorer in this territory |
| production semantics, not audit semantics | `write_incident`/`write_artifact` at the call |

**The negative control is a coherent forgery.** Three actions are added to the
closing scorecard — to the run's count, its environment's count and the card
total together — so the card's own arithmetic still adds up and every check
that reads the card alone still passes. Only the ledger contradicts it. That is
the point: a forgery a scorecard can catch by itself needs no reconciliation.

Measured (`evidence/INDEX.json`, regenerate with `make_evidence.py`):

| leg | verdict | S-1 | incidents in the ledger |
|---|---|---|---|
| clean | `PASS` | card 6 == ledger 6 | none |
| forged | `FAIL` | card 9 vs ledger 6 | `score_mismatch` |

The forged leg's `S-10` ("the card's totals agree with its own environments")
and `S-12` ("the records are canonical") both still pass — it fails for the
stated reason and no other — and the incident lands **after** `run_end`, never
instead of it.

## 2. Inputs read, not modified

`proxy/scoring/__init__.py`, `proxy/scoring/arc_v1.py`, `proxy/SCORING.md`,
`proxy/DELIVERY_RULING.md`, `proxy/tools/audit_delivery.py`,
`proxy/ledger.py`, `proxy/mock/arc_mock.py`, `proxy/paths.py`. Nothing outside
`theoria-arm/` was written.

## 3. Gaps

1. **No live evidence yet, by design.** The ticket says so: the first
   *real* leg after this lands produces the first live "跑完即打分" record, and
   this item does not fund it. Axis 2 of `DELIVERY_RULING.md` §4 stays open.
2. **The baseline was already red** — see §4. Two failures on `master` at
   `4c08ea6`, unrelated to this ticket and not absorbed into it.
3. `score.json` is written for every run including rehearsals; the shared index
   `proxy/var/scores/` gets a copy only for archive-material runs. That is
   `D-A18-001`'s stated call, not an omission, but it is a *decision* someone
   could reverse: a live leg is archive material, so it lands in both.
4. The `score=False` switch exists. It is off nowhere in shipped code and one
   test asserts what its absence looks like, but it is a switch, and a future
   caller could turn scoring off without the ledger recording that it did.

## 4. Baseline (red before any change)

`start_ritual.py`, base `4c08ea6`, `cd theoria-arm && python -m pytest`:

```
2 failed, 657 passed in 810.05s (0:13:30)
FAILED tests/test_arm.py::test_the_archive_stays_accountable
  -- re-deriving every manifest reproduces it byte for byte: drifted:
     ['20260731T231654Z-R1-g50t-a', '20260731T231654Z-R1-sk48-b',
      '20260801T001851Z-R1b-g50t-a', '20260801T001851Z-R1b-sk48-b']
FAILED tests/test_desk_gate.py::test_the_ceiling_table_still_covers_the_archive
  -- claude-opus-5: ceiling $12.00 is below $13.4480
```

Both are findings about `master`, not about this ticket. They are untouched:
the four drifted manifests belong to the R1/R1b legs and the ceiling table is
`harness/spend.py`'s, neither of which this item may or should edit.

## 5. Gate outputs

Verbatim below. `verify.sh` is generated into this run directory
(`--out runs/2026-08-01T045542Z-A18/verify.sh`) so the territory's standing
`verify.sh` is not overwritten. `verify_out.txt` beside it holds a second,
post-manifest run of the same checklist verbatim; it is deliberately **not**
listed in `MANIFEST.json:files[]`, because it is the gate's own log and hashing
it would mean that re-running the gate invalidated the manifest that the gate
checks.

Post-change full suite (`suite_after.txt`, complete run, exit 1):

    FAILED tests/test_arm.py::test_the_archive_stays_accountable
    FAILED tests/test_desk_gate.py::test_the_ceiling_table_still_covers_the_archive

— exactly the two pre-existing reds of §4, nothing else. Independently
re-confirmed red in the MAIN checkout at the same tests (so this is master's
red, not a worktree artefact — the check A19's false-red baseline taught).
Zero new failures; the 11 new tests pass in isolation and inside the full run.
The gate's tests line is therefore expected FAIL and is carried, not absorbed:
the drifted manifests belong to the R1/R1b legs, the ceiling table to
`harness/spend.py` after register #13's owner ruling — both filed for the
territory as board item A22-theoria-arm-suite-red.
