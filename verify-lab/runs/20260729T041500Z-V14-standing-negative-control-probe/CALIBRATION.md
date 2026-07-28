# Calibrating the mechanical criterion against V11's 127 hand judgements

The probe rests on one substitution: V11 asked a human *does this gate have an
executable negative control*, and `verify-lab/negctl/criterion.py` asks `ast`
*does a test in this repository construct a bad input for this file and assert it
fails*. Those are different questions. This file measures how different.

Everything below is reproducible:

```bash
python verify-lab/negctl/calibrate.py                                # the matrices
python verify-lab/negctl/calibrate.py --disagreements --detector A-B # every miss, named
python verify-lab/negctl/calibrate.py --json                         # calibration.json
```

The gold standard is parsed out of
`verify-lab/runs/20260728T152000Z-V11-negative-control-census/CENSUS_TABLE.md`
§1 — the `有负控` column, nothing transcribed by hand — so it cannot drift away
from the document it claims to come from.

---

## 1. What is in scope, and what the criterion refuses to answer

| | rows | why |
|---|---|---|
| census rows parsed | 127 | all of §1 |
| **in scope** | **103** | a single Python file this criterion can be asked about |
| out of scope | 8 | 4 shell entry points (`figures/verify.sh`, `arc-recon/verify.sh`, `ablation-arm/verify.sh`, `proxy/verify_spend.sh`) and 4 rows whose "entry point" is itself a test file |
| unresolvable | 16 | `python -m pytest` suites, globs (`battery/metrics/*`), one gate that does not exist (`release/bundle.py --check`) |

The 4 shell gates are a declared hole and a real one: `figures/verify.sh` is the
most-cited acceptance command in the repository and this criterion cannot see it
at all.

A second limitation, measured rather than asserted: **8 of the 103 in-scope rows
share a file with another row the census judged differently.** The census is
function-granular (`worldgen/build.py --check` = 是, `worldgen/build.py::
check_determinism` = 否; `proxy/spend_gate.py` SpendGate = 是, its `__main__` =
否), and this criterion is file-granular. No file-granular criterion can be right
about both. Those 8 are reported in the main matrix *and* separately excluded, so
the reader can see exactly how much of the error is granularity rather than
judgement.

## 2. The matrices

`gold` is V11's `有负控` column. `strict` folds `部分` into *has a negative
control* (the census's own reading: some executable demonstration exists, just not
for every branch). `harsh` folds it the other way. `clean` is `strict` with the
8 granularity-conflict rows removed.

| detector | TP | FN | FP | TN | FPR | **FNR** | precision | accuracy | clean FP / FPR |
|---|---|---|---|---|---|---|---|---|---|
| **N** — the test function's *name* looks negative | 35 | 28 | 3 | 31 | 0.088 | 0.444 | 0.921 | 0.680 | 0 / 0.000 |
| A− — structural failure assertion | 40 | 23 | 3 | 31 | 0.088 | 0.365 | 0.930 | 0.732 | 0 / 0.000 |
| A — A− plus `assert <bad> not in <output>` | 42 | 21 | 4 | 30 | 0.118 | 0.333 | 0.913 | 0.742 | 1 / 0.034 |
| B — an in-tree `--self-test` / `--calibrate` | 5 | 58 | 0 | 34 | 0.000 | 0.921 | 1.000 | 0.402 | 0 / 0.000 |
| **A−B — shipped** | **44** | **19** | **3** | **31** | **0.088** | **0.302** | **0.936** | **0.773** | **0 / 0.000** |
| AB — A−B plus the containment rule | 46 | 17 | 4 | 30 | 0.118 | 0.270 | 0.920 | 0.784 | 1 / 0.034 |

Under `harsh`, A−B is TP 35 / FN 11 / FP 12 / TN 39 — FPR 0.235, FNR 0.239. The
`partial` rows are where the two definitions genuinely diverge and no folding is
free; both numbers are here so nobody has to take one on faith.

### Read the two error directions the right way round

They are not symmetric for a *gate*, and getting this backwards is how the
recommendation in §6 would go wrong:

* A **false `present`** (criterion says yes, human says no) means the probe stays
  **quiet** about a real gap. That is a missed detection — the probe under-reports
  and nobody is inconvenienced. **3 of 34** gold-negative rows, **0 of 29** once
  the granularity conflicts are set aside; all three are granularity conflicts.
* A **false `absent`** (criterion says no, human says yes) means the probe goes
  **red** on a gate that does have a negative control. That is a false alarm, and
  false alarms are what turn a gate into an exemption ritual and then into a
  disabled gate. **19 of 63** gold-positive rows: **30%.**

So the number that decides CI admission is 30%, not 8.8%.

## 3. Where the 19 false alarms come from

Every one of them, from `disagreements.A-B.txt`, sorted into three classes by
reading the cited negative control:

**(a) The demonstration lives one level down — 9 rows.**
`cold-start-a0/run_all.py`, `cold-start-a3/run_all.py`, `exam/verify.py`,
`exam/tools/build_papers.py`, `battery/run_battery.py`, `engine-rig/bench/__main__.py`,
`theory-compiler/tools/verify_c8.py`, `worldgen/qc/run_qc.py`,
`baseline-arms/harness/audit_cells.py`. These are orchestrators. V11 credited them
because a mutant suite fires *inside* something they call. The criterion asks about
the file and answers no.

This is the class where the criterion is arguably **stricter and more correct**,
and I am not going to claim that, because the census is the gold standard and it
said otherwise. But it is worth naming what makes the class uncomfortable: the
census's own sharpest finding is `theoria-arm/armtools/archive.py` — the negative
control exists, on `inner/surprise.py::Register.audit`, which is *a second
implementation of the same rule*, and the one that ships is the untested one.
Transitive credit is how that hides. A "detector C" that credited an entry point
for anything its imports can do would erase all 9 of these false alarms and make
`archive.py` invisible, which is why it is not implemented.

**(b) The negative control is not pytest — 6 rows.**
`theory-compiler/tools/probe_mentions.py` (a pre-registered expectations table:
bad readings *must* still misfire at the recorded counts), `exam/tools/run_exam.py
--calibrate`, `exam/tools/run_selftest.py`, `cold-start-a3/a3pipeline/negctl.py`,
`ablation-arm/run_exhibits.py`, `a0-spike/runs/.../make_manifest.py --verify`.
Detector B was written for exactly this class and recovers only 5 across the whole
tree (FNR 0.92 on its own). These are among the *best* negative controls in the
repository and the criterion is close to blind to them.

**(c) The test targets something else — 4 rows.**
`theory-compiler/tools/transcribe_deadlock_certificates.py`,
`theory-compiler/tools/build_deadlock_lean.py`, `a0-spike/probes/semantics_probe.py`,
`proxy/model_proxy.py`.

## 4. Three rounds of tuning, and what each one cost

Recorded because a criterion tuned on its own calibration set reports optimistic
numbers, and the size of the tuning is the size of the optimism.

The row count changed at round 1 (that edit also introduced the scope exclusions
in §1, from 111 rows to 103), so rounds 0 and 1 are not directly comparable to
each other. Counts, not rates, and the caveat is stated rather than smoothed over.

| round | change | why | effect |
|---|---|---|---|
| 0 | first draft, 111 rows, detector AB | — | FP 5, FN 26 |
| 1 | `assert X == <nonzero>` only when X looks like an exit code; `assert not X` only when X is a verdict. Scope exclusions added in the same edit → 103 rows. | `assert len(rows) == 6` in `theoria-arm/tests/test_arm.py:687` scored `theoria-arm/harness/run.py` (gold: no negative control) as present. `assert not violations` in `fuzzlab/tests/test_battery.py:37` did the same for `fuzzlab/campaign.py` — that assertion is a *positive* control, it says the run found nothing wrong. | A−B: FP 2, FN 24 |
| 2 | `assert <complaint> in <findings>`, `assert any(... for ... in <findings>)`, bare `assert <findings>` | `engine-rig/tests/test_integration.py:286` — 14 parametrised mutant rows, each `assert any(fragment in error for error in errors)`. Nothing else in the criterion could see them. | A−B: FP 3, FN 21 |
| 3 | follow one hop through helpers defined in the same test file | `proxy/tests/test_redteam.py` never writes `EnvProxy` inside a test; it writes `with env_proxy_over(...)`. Without the hop, the repository's best negative-control suite targets nothing. | A−B: FP 3, FN 19 |

Round 2 cost one false positive to buy three false negatives — `worldgen/build.py`,
which the census judged twice (是 for `--check`, 否 for `check_determinism`) and
which no file-granular criterion can be right about. That is the only trade in the
three rounds where an error was knowingly added.

All three are structural classes, not row-specific patches, and each is pinned by
a parametrised test in `verify-lab/negctl/tests/test_probe.py` so a future
loosening shows up as a test change. But they were still chosen by looking at the
gold standard, so **the true FPR is at least 8.8% and the true FNR at least 30%.**
There is no held-out set — 127 rows is one census, not two. The adversarial pass
(`ADVERSARIAL.md`) exists to attack the numbers from outside the calibration set.

Detector N is in the table for one reason: it is the criterion a reasonable person
writes first, it is strictly worse on both axes (FNR 0.444 against 0.302 at the
same FPR), and `figures/verify.sh` gate 7 records what the equivalent mistake cost
there — a regex whose first finding was a phrase inside a docstring. The naive
detector is also what `test_the_planted_red_slips_past_the_name_only_criterion`
uses as its weakened probe.

## 5. What the probe measures on the current tree

```
negative-control probe: 141 entry points, 141 pinned, detector A-B
  PINNED_OK=141
PROBE: green
EXIT=0
```

141 files enumerated as acceptance entry points; **108 have no negative control
the criterion can find**, 33 do. The pin (`verify-lab/negctl/KNOWN_GAPS.json`)
records all 141 with the territory that owns each, and marks the 18 where V11's
auditors credited a negative control this criterion cannot see — so the inventory
cannot be read as an accusation against a territory it is actually wrong about.

The enumerator itself (`probe.can_exit_nonzero`) is **not calibrated against
anything**. That is why `NOT_A_GATE` — a pinned file that has lost its non-zero
exit path — reports and does not gate.

## 6. The recommendation, from the numbers

Written out in `verify-lab/NEGATIVE_CONTROL.md` §"Should this be a merge gate";
the short form is **no, not as a blocking gate, yes as a required advisory step**,
and the number that decides it is the 30% false-alarm rate in §2.
