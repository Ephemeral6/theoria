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
| A− — structural failure assertion | 39 | 24 | 3 | 31 | 0.088 | 0.381 | 0.929 | 0.722 | 0 / 0.000 |
| A — A− plus `assert <bad> not in <output>` | 41 | 22 | 4 | 30 | 0.118 | 0.349 | 0.911 | 0.732 | 1 / 0.035 |
| B — an in-tree `--self-test` / `--calibrate` | 5 | 58 | 0 | 34 | 0.000 | 0.921 | 1.000 | 0.402 | 0 / 0.000 |
| **A−B — shipped** | **43** | **20** | **3** | **31** | **0.088** | **0.318** | **0.935** | **0.763** | **0 / 0.000** |
| AB — A−B plus the containment rule | 45 | 18 | 4 | 30 | 0.118 | 0.286 | 0.918 | 0.773 | 1 / 0.035 |

Under `harsh`, A−B is TP 34 / FN 12 / FP 12 / TN 39 — FPR 0.235, FNR 0.261. The
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
  disabled gate. **20 of 63** gold-positive rows: **32%.**

So the number that decides CI admission is 32%, not 8.8%.

## 3. Where the 20 false alarms come from

Every one of them, from `disagreements.A-B.txt`, sorted into three classes by
reading the cited negative control:

**(a) The demonstration lives one level down — 10 rows.**
`cold-start-a0/run_all.py`, `cold-start-a3/run_all.py`, `a0-spike/pipeline/run_a0.py`,
`exam/verify.py`, `exam/tools/build_papers.py`, `battery/run_battery.py`,
`engine-rig/bench/__main__.py`, `theory-compiler/tools/verify_c8.py`,
`worldgen/qc/run_qc.py`, `baseline-arms/harness/audit_cells.py`. These are
orchestrators. V11 credited them because a mutant suite fires *inside* something
they call. The criterion asks about the file and answers no.

This is the class where the criterion is arguably **stricter and more correct**,
and I am not going to claim that, because the census is the gold standard and it
said otherwise. But it is worth naming what makes the class uncomfortable: the
census's own sharpest finding is `theoria-arm/armtools/archive.py` — the negative
control exists, on `inner/surprise.py::Register.audit`, which is *a second
implementation of the same rule*, and the one that ships is the untested one.
Transitive credit is how that hides. A "detector C" that credited an entry point
for anything its imports can do would erase all 10 of these false alarms and make
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

All three false `present` are the granularity conflicts of §1:
`worldgen/build.py`, `proxy/spend_gate.py`, `arc-recon/client.py` — each a file the
census judged twice, once 是 and once 否.

## 3b. The limitation that matters most: a file is not a gate

**A file-level `present` does not imply that every gate in the file has a negative
control.** The criterion is file-granular; a gate is function-granular. `present`
means *some* test constructs a bad input for *something* in that file, and the
probe will then stay silent about every other gate living beside it.

The worked example, found by the adversarial pass and the most valuable single
finding it returned:

> `worldgen/build.py` is pinned `present`. The evidence is real —
> `worldgen/tests/test_build_gate.py:49/:57` synthesises a manifest violating each
> gate in turn and asserts each is reported. That is a proper negative control for
> `gate_failures()`.
>
> The same file also contains `check_determinism()` (`build.py:231`, called at
> `:344`, `NOT DETERMINISTIC → return 1` at `:347`) — the strongest determinism
> claim in this repository: a subprocess under a different `PYTHONHASHSEED`,
> rebuilding 35 worlds × 6 artefacts and diffing them byte for byte. The name
> `check_determinism` appears **three times in every `.py` file in the tree**: the
> definition, the call, and one docstring mention in
> `worldgen/tests/test_determinism.py:10`. **No test calls it.** Its own docstring
> says *a gate that cannot fail is not a gate*.
>
> The probe is, and will remain, silent about it.

Same shape, also confirmed and also pinned `present`: `engine-rig/tools/run_all.py`
(sole evidence is `test_integration.py:317`, a CLI-usage `exit 2`; the
schema-failure red path at `:260-264` is undemonstrated, which is what V11 said),
`arc-recon/contamination.py`, `arc-recon/precheck.py`, `proxy/spend_gate.py`,
`ablation-arm/run_arm.py`.

**This is worse than a missing verdict.** A gate with no verdict prompts someone to
look; a gate carrying a `present` it did not earn is read as covered. So the
caveat is written into `KNOWN_GAPS.json`'s header as well, where a reader
consulting the inventory will meet it before the entries.

It also means §2's `strict, no file shared` row — FP 0, FPR 0.000 — must not be
read as "no false positives". All three false `present` are granularity conflicts,
and that row reports 0 by **deleting them from the denominator**. Function-level
masking is a real detection failure, not statistical noise. FP 0 on that row is a
definition, not a measurement. Making the criterion function-granular is a separate
item; V14 did not do it.

## 3c. What the calibration is structurally unable to see

The matrix runs on 103 census rows. The probe runs on 141 entry points, **74 of
which V11 never surveyed**. A false `present` among those 74 cannot appear in any
cell of any matrix here. The adversarial pass found one:
`cold-start-a2/a2pipeline/engines.py` was being credited with
`engine-rig/tests/test_bench.py` — and V11's §3 says of that territory, in as many
words, that A2 has neither a mutant suite nor a `negctl.py` while both its
neighbours do. The gap was real and the probe was covering it up.

The demonstration that this blindness is not hypothetical is §4's round 5: closing
the resolver hole **changed no number in any matrix and flipped no verdict on the
tree**, while removing every one of the 54 cross-territory bindings. A defect class
can be entirely real and entirely invisible to this calibration at the same time.

## 4. Five rounds of tuning, and what each one cost

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

| 4 | refuse an ambiguous import that shares no path prefix with the importer | `ablation-arm/tests/test_exhibits.py` imports `exhibits.run_all`; four files here are named `run_all.py`, and the tie-break handed the binding to `cold-start-a0`. Two entry points in another track were being credited with `ablation-arm`'s tests. | A−B: FP 3, FN 20 |

| 5 | a binding must resolve into an **ancestor directory of the importer or the same top-level territory**; otherwise refuse | Round 4's guard ran only after `len(cands) > 1`, so the single-candidate path returned before it. Confirmed live by the adversarial pass: `a0-spike/tests/test_a0.py` binding `generate` to `worldgen/generate.py`; 14 bindings in `engine-rig/tests` resolving to `fuzzlab/props/*.py`; `worldgen/tests/test_mutate.py` binding `validate` to `engine-rig/engines/.../validate.py`. The real targets are **package directories** the index cannot see. | A−B: FP 3, FN 20 — **unchanged** |

Round 5 is the one to read carefully. It removed all 54 cross-territory bindings in
the tree (770 → 721 bindings, 54 → 0 crossings) and **moved nothing**: not one cell
of the confusion matrix, not one verdict among the 141 entry points. One entry's
cited evidence changed (`worldgen/generate.py` had 3 of its 11 citations pointing
at `a0-spike`'s tests). A reader who judged the fix by the calibration would
conclude it was unnecessary. That is §3c's point, demonstrated by the fix's own
null result, and it is the strongest available argument that these numbers are a
floor rather than an estimate.

Round 4 traded a true positive for a false negative on purpose, and it is the
trade this probe should always make: a wrongly resolved import is a false
`present`, which makes the probe **silent** about a real gap; an unresolved one is
a false `absent`, which makes it **noisy**. `cold-start-a0/run_all.py` went from
`present` to `absent` and the probe went red against its own pin, which is how the
defect surfaced.

Round 2 cost one false positive to buy three false negatives — `worldgen/build.py`,
which the census judged twice (是 for `--check`, 否 for `check_determinism`) and
which no file-granular criterion can be right about. That is the only trade in the
three rounds where an error was knowingly added.

All three are structural classes, not row-specific patches, and each is pinned by
a parametrised test in `verify-lab/negctl/tests/test_probe.py` so a future
loosening shows up as a test change. But they were still chosen by looking at the
gold standard, so **the true FPR is at least 8.8% and the true FNR at least 32%.**
There is no held-out set — 127 rows is one census, not two. The adversarial pass
(`ADVERSARIAL.md`) exists to attack the numbers from outside the calibration set.

Detector N is in the table for one reason: it is the criterion a reasonable person
writes first, it is strictly worse on both axes (FNR 0.444 against 0.318 at the
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

141 files enumerated as acceptance entry points; **110 have no negative control
the criterion can find**, 31 do. The pin (`verify-lab/negctl/KNOWN_GAPS.json`)
records all 141 with the territory that owns each, and marks the 19 where V11's
auditors credited a negative control this criterion cannot see — so the inventory
cannot be read as an accusation against a territory it is actually wrong about.

The enumerator itself (`probe.can_exit_nonzero`) is **not calibrated against
anything**. That is why `NOT_A_GATE` — a pinned file that has lost its non-zero
exit path — reports and does not gate.

## 6. The recommendation, from the numbers

Written out in `verify-lab/NEGATIVE_CONTROL.md` §"Should this be a merge gate";
the short form is **no, not as a blocking gate, yes as a required advisory step**,
and the number that decides it is the 32% false-alarm rate in §2.
