# V14 — turning the negative-control census into a standing probe

Narrative. The machine-readable record is `MANIFEST.json`; the numbers are
`CALIBRATION.md`; the proof the probe is not idling is `NOT_IDLE.md`; the
independent attempt to break it is `ADVERSARIAL.md`.

## What was built

| file | what it is |
|---|---|
| `verify-lab/negctl/criterion.py` | the decidable proxy for "has an executable negative control", pure `ast` |
| `verify-lab/negctl/probe.py` | enumerate entry points, judge, compare to the pin, exit 1 on a deviation |
| `verify-lab/negctl/KNOWN_GAPS.json` | the standing inventory: 141 entry points, verdict + owning territory each |
| `verify-lab/negctl/calibrate.py` | the criterion measured against V11's 127 hand judgements |
| `verify-lab/negctl/tests/test_probe.py` | the probe's own negative control, 24 tests |
| `verify-lab/NEGATIVE_CONTROL.md` §"The standing probe (V14)" | the write-up, including the recommendation to the monitor |

## Observed, on this tree

```
$ python verify-lab/negctl/probe.py
negative-control probe: 141 entry points, 141 pinned, detector A-B
  PINNED_OK=141
PROBE: green
EXIT=0

$ python -m pytest verify-lab/negctl/tests -q
24 passed
EXIT=0
```

## The order the decisions were made in, and why it mattered

**The criterion first, the probe second.** The item warned that this is easy to
build as a toy nobody runs, and the failure mode it named — a false-alarm rate
high enough that people stop reading — is a property of the criterion, not of the
probe. So the criterion was written, calibrated against the census, and only then
wrapped in something that exits non-zero. Had it gone the other way the probe
would have shipped with an uncalibrated predicate and a confident docstring, which
is the exact shape of `arc-recon/verify.sh:53`.

**Four tuning rounds, each on a structural class, each recorded.** First draft:
FP 5, FN 26. The two false positives that fell out first are the interesting ones,
because both look right until you read the code: `assert len(rows) == 6` scored
`theoria-arm/harness/run.py` as having a negative control (a count, not an exit
code), and `assert not violations` scored `fuzzlab/campaign.py` (that assertion is
a *positive* control — it says the run found nothing wrong). The fixes are
`_looks_like_exit_code` and `_is_verdict`. `CALIBRATION.md` §4 has all four
rounds and states the consequence: the reported rates are lower bounds, because
the criterion was tuned against the set it is scored on.

**The pin was written after the enumerator was fixed, not before.** See below.

## The probe's negative control caught the probe, first run

Nine of the twenty-four tests failed the first time they ran, and the cause was in
`probe.can_exit_nonzero`: it recognised `return 1` and not `return 1 if problems
else 0`. That is the dominant form in this repository — `verify_c4.py:240`,
`transcribe_deadlock_certificates.py:120`, `run_matrix.py:328`,
`check_redlines.py:304`, `merge_ledger.py:91`. The synthetic gate in the test is
written in that style, so it was not enumerated at all and the probe printed green
on a tree containing a planted, undemonstrated gate.

The entry-point count went from 128 to 141 after the fix. Without the negative
control this item would have delivered a probe that reads a fraction of the tree
and says green — which is the defect V11 was written to count, committed by the
thing written to stop it.

## A second defect the calibration found: the resolver was guessing

`Index.resolve` picked the candidate sharing the longest path prefix with the
importer — which is what the interpreter does — but when *no* candidate shared any
prefix it still returned one. `ablation-arm/tests/test_exhibits.py` imports
`exhibits.run_all`; four files in this repository are named `run_all.py`; the
tie-break handed the binding to `cold-start-a0/run_all.py`, in another track.
Two entry points were being credited with a negative control belonging to a
different lane.

It now refuses. The trade is deliberate and stated in the code: a wrongly resolved
import is a false `present`, which makes the probe **silent** about a real gap; an
unresolved one is a false `absent`, which makes it **noisy**. Prefer the noise.
The pin was re-measured and the two entries transcribed back to `absent` with the
reason recorded in the entry itself, which is the procedure `KNOWN_GAPS.json.
_how_to_change_it` prescribes. Nothing changed in either territory; what changed
is that the probe stopped crediting them with another lane's test.

## Where I deliberately diverged from V12

`worldgen/qc/gate.py` gates on **any** deviation from its pin, in either
direction, and argues for it well: an improvement means the pin is now a lie, and
a pin only stays worth reading if going stale is loud. Two of its rules are
softened here and the reasons are in `probe.py`'s docstring:

* An entry point that **closed** its gap reports and does not gate. V12's pin is
  three QC stages in one territory; this one is 141 files across nine, and a probe
  that turns every repair into a red is a probe that gets switched off. The cost
  is a pin that drifts optimistic, so it prints loudly and carries its own date.
* A pinned file that has **lost** its non-zero exit path reports and does not
  gate, because `can_exit_nonzero` has never been calibrated against anything.
  Gating on an uncalibrated enumerator is the mistake this lab exists to name.

## Scope, and what was not done

* **Only `verify-lab/` is written.** The probe reads every other territory by
  parsing files and writes to none. `git status` outside `verify-lab/` was empty
  at every commit. No runner, no `verify.sh` from another territory was executed —
  V11's own §4 records what that costs, and the confound it produced there was
  attributable only because five auditors reported the same anomaly.
* **Zero network, zero `.env`, zero sealed-pile contact.** The whole item is `ast`
  over the working tree.
* **The 110 pinned gaps were not closed.** They belong to nine territories and
  closing them is not this item's work; the pin names the owner of each so the
  question can be asked of the right lane.
* **Shell entry points are out of scope** — `figures/verify.sh`,
  `arc-recon/verify.sh`, `ablation-arm/verify.sh`, `proxy/verify_spend.sh`. That
  is declared, not hidden, and it is a real hole: `figures/verify.sh` is the
  most-cited acceptance command in the repository.

## The recommendation, in one line

Advisory in CI and on the review checklist; **not** in branch protection, because
32% of gates that do have a negative control would be flagged as if they did not,
and that number concentrates on the six best non-pytest negative controls in the
repository. The full argument is `verify-lab/NEGATIVE_CONTROL.md` §"Should this be
a merge gate", and it is written from `CALIBRATION.md`'s numbers rather than from
an impression of how noisy the probe felt.
