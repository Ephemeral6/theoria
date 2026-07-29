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

**Five tuning rounds, each on a structural class, each recorded.** First draft:
FP 5, FN 26. The two false positives that fell out first are the interesting ones,
because both look right until you read the code: `assert len(rows) == 6` scored
`theoria-arm/harness/run.py` as having a negative control (a count, not an exit
code), and `assert not violations` scored `fuzzlab/campaign.py` (that assertion is
a *positive* control — it says the run found nothing wrong). The fixes are
`_looks_like_exit_code` and `_is_verdict`. `CALIBRATION.md` §4 has all five
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

## What the adversarial pass overturned or weakened

Ledgered in place, as findings against this item rather than as a list of repairs.
Full text: `ADVERSARIAL.md`. It read all 33 (then 31) `present` entries, opened 21
test functions, scanned 770 import bindings and 464 failure-assertion hits, and
compared the enumerator against V11's 90 locatable gates.

**1. My headline claim about false positives was wrong in the way that matters.**
I wrote that the criterion produces "0 false `present`" once granularity conflicts
are excluded, and treated that as the reassuring number. The reviewer's answer:
that row reports 0 **by deleting the failure mode from the denominator**. All three
false `present` are granularity conflicts, function-level masking is a real
detection failure, and `worldgen/build.py::check_determinism` — the strongest
determinism claim in the repository, called by zero tests anywhere — is exactly
what it hides. Overturned. `CALIBRATION.md` §3b now says a file-level `present` is
not a promise about the file, and so does `KNOWN_GAPS.json`'s header.

**2. My false-positive rate is not credible, and the reason is my sampling frame.**
The matrix runs on 103 census rows; the probe runs on 141 entry points, 74 never
surveyed by V11. The reviewer found a false `present` inside those 74 —
`cold-start-a2/a2pipeline/engines.py`, credited with `engine-rig/tests/test_bench.py`
— which **no cell of my matrix can represent**. V11's §3 says in as many words that
A2 has neither a mutant suite nor a `negctl.py` while both its neighbours do. The
probe was covering that gap up. 8.8% is a floor, and I had presented it as a
measurement.

**3. My resolver fix (round 4) closed half the defect and I called it closed.**
The guard ran only after `len(cands) > 1`; `if len(cands) == 1: return cands[0]`
returned before it. The reviewer found the other half live at `b6d8643`: 14
bindings in `engine-rig/tests` resolving to `fuzzlab/props/*.py`,
`a0-spike/tests/test_a0.py` binding `generate` to `worldgen/generate.py`,
`worldgen/tests/test_mutate.py` binding `validate` into `engine-rig/engines/`. Root
cause is not the tie-break: **package directories are not indexed**, so
`from exhibits import run_all` looks for a module and a same-named `.py` elsewhere
absorbs it. Fixed in round 5 — and see item 6 for what the fix proved.

**4. A docstring of mine was simply false.** `criterion.py` claimed the ancestry
rule is "what the interpreter does at run time". It is not: the interpreter walks
`sys.path`, and these test files all `sys.path.insert(0, <their own root>)`. The
ancestry rule is an approximation of that, and it fails outright on package
directories, which is the common case here. The sentence is gone.

**5. One and a half of the three "false positives" may be the census's error, not
mine.** The reviewer read the source for all three and reports that for
`worldgen/build.py --check` and `proxy/spend_gate.py`'s `SpendGate`, the criterion
is right and V11's row is about a different function in the same file. I am not
claiming the correction — the census is the gold standard for this item — but it
belongs in the error bars, and it cuts *against* my numbers looking good, not for.

**6. The most useful thing it produced is a null result.** Round 5 removed all 54
cross-territory bindings and changed **nothing**: no matrix cell, no verdict among
141 entry points, one entry's citation list. Anyone judging that fix by the
calibration would call it unnecessary. It is the cleanest available proof that this
calibration cannot see the defect class, and it is now `CALIBRATION.md` §3c.

**7. Not overturned, and the reviewer says so explicitly.** The three-layer
distinction in the judgement code — counts vs exit codes, positive controls vs
negative ones, findings bags vs verdicts — held under attack; `_VERDICT_WORDS`'
`matches` / `caught` / `agree` produced no false hits in 29 `assert not <verdict>`
sites (they are dead words, which is its own small finding). Its verdict on the
failure was that it is not in the judgement layer but in the **two layers
underneath — resolution and enumeration — neither of which was calibrated**. That
is a fair description and it is why the recommendation is what it is.

**Confirmed and deliberately not fixed** — the substring bug in
`_looks_like_exit_code`, detector B ignoring file names (so `negctl.py` reads
`absent`), `scan_selftests` certifying itself, `monitor/tests/mutants.py` registered
as lacking the thing it *is*, and the 7 shell gates. All listed in
`verify-lab/NEGATIVE_CONTROL.md` §"Confirmed by the adversarial pass and
deliberately not fixed here". Repairing them would be re-tuning the criterion after
seeing its score, which is the move this item was told not to make.

**One correction to the report itself.** Its §0 attributes commits `a65ba9e` /
`b6d8643`, which landed while it was auditing, to "another session in the same
worktree". They are mine — this item's own round 4 and its follow-up. The reviewer
found FP-A and FP-B independently and concurrently, which is a stronger result than
it claimed for itself, not a weaker one.

## The two defects the probe's own negative control found in the probe

Worth more than the probe running green, and recorded as such.

**The enumerator did not recognise this repository's own idiom.**
`can_exit_nonzero` looked for `return 1` and not `return 1 if problems else 0` —
which is how `verify_c4.py:240`, `transcribe_deadlock_certificates.py:120`,
`run_matrix.py:328`, `check_redlines.py:304` and `merge_ledger.py:91` all spell it.
Nine of twenty-four tests failed on their first run and named it. Before the fix
the probe printed green on a tree containing a planted, undemonstrated gate. Entry
points went 128 → 141.

**The resolver credited one track's tests to another track's file.**
`ablation-arm/tests/test_exhibits.py`'s two pre-registered E3 falsifications were
being recorded against `cold-start-a0/run_all.py`. The probe went red against its
own pin, which is how it surfaced. The adversarial pass found the same defect
independently and then found the half I had missed.

Neither would have been caught by running the probe and reading `green`. That is
the whole argument for the negative control, made twice, on the item whose subject
is that argument.

## The recommendation, in one line

Standing and **report-only**; not in branch protection. The enumerator that
`NEW_GAP` rides on has never been calibrated and misses 26% of V11's locatable
gates while over-collecting at least 17 non-gates including one-off scripts in
`runs/<id>/`, which grow with every experiment; the criterion's own false-alarm
rate is 32%; and resolution is tree-global, so one track's import can redden
another track's entry point. If it is ever gated, let **`REGRESSION` block and
`NEW_GAP` only report** — `REGRESSION` fires only against a definite prior state,
so it has already cleared both uncalibrated layers. The full argument, with the
six numbers, is `verify-lab/NEGATIVE_CONTROL.md` §"Should this be a merge gate".
