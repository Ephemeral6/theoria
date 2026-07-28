# The negative-control census — which of this repository's gates has ever been shown to fail

`verify-lab` holds cross-cutting verification work: questions that belong to no
single territory because the answer is only interesting when asked of all of
them at once. This is the first one.

**The question.** This repository has a methodology it applies unevenly, stated
best in `figures/verify.sh` gate 8:

> a coverage probe that cannot be shown failing is a green light with nothing
> behind it.

Every territory has gates. How many of them have ever been *demonstrated* to
fail? Not documented as able to fail — demonstrated, by something executable
that a reader can run.

**The method.** Six auditors, one per territory group, each asked the same three
questions of every acceptance entry point they could find:

1. **Can it go red?** Is there any input that makes it exit non-zero? Judged by
   reading the code for `sys.exit(1)` / escaping raise / `exit(FAILED)` — not by
   reading what its documentation promises.
2. **Has anyone shown it going red?** Is there an *executable* negative control
   — a `--self-test`, a pre-registered mutant, a deliberately broken fixture, a
   test asserting that a bad input must fail? A promise in prose does not count.
3. **Is the exit code honest?** Where the code prints `FAIL` / `ABORT` /
   `drifted` / `mismatch`, does the process also exit non-zero?

Every cell is marked `实测` (observed by running it) or `读码` (read from the
source). The full table is `runs/20260728T152000Z-V11-negative-control-census/CENSUS_TABLE.md`;
the six auditors' own reports are in that run's `partials/`.

---

## The finding is not "the checks are wrong". It is narrower and worse.

Across six territory groups the same shape recurs, and it is **not** buggy
logic. In nearly every case the detection function is correct: it finds the
thing, it computes the right verdict, it prints the right words. What is missing
is the wire from that verdict to the process exit code — the only channel a
`verify.sh` step, a CI hook, or a merge gate can hear.

> **The verdict was computed correctly and connected to nothing.**

This matters more than a wrong check would, because a wrong check is visible the
first time someone reads it, while this failure is invisible *by construction*:
the tool prints its warning, the harness prints `-- ok`, and the run ends
`VERIFY: green`. The warning is on screen and the exit code says everything is
fine. Nobody reads the screen of a green run.

### The load-bearing instance

`arc-recon/contamination.py` is the executable form of the project's most
consequential promise — the pile cut, "no sealed game has been touched". Its
`main()` prints, when a sealed game has been contacted:

```
ledger audit: <ledger>   <N> calls, sealed ADDRESSED: <game>
```

and then returns:

```python
return 0 if check["matches"] else 1        # contamination.py:338
```

`check` is the sha256 of `piles.json` — whether the *cut file* was edited.
Whether the *cut was violated* does not reach the exit code. `arc-recon/verify.sh:53`
invokes it through a `step` helper that keys on exit status only
(`verify.sh:18-28`), so that step reports `-- ok`.

> **An earlier draft of this file continued: "and the run ends `VERIFY: green`."
> That was wrong, and it was the headline.** An adversarial reviewer injected a
> sealed contact into the *default* ledger in a scratch copy — cleaner than the
> original audit, which had edited a module constant — and the script ends
> **`VERIFY: RED`**. `verify.sh`'s first step is `python -m pytest -q`, and
> `arc-recon/test_hygiene.py` carries two assertions that sit directly on the
> real ledger: `test_the_real_ledger_has_addressed_no_sealed_game` and
> `test_the_cross_track_audit_covers_more_than_our_own_ledger`. The verdict *is*
> wired to an exit code; it is wired in pytest rather than in
> `contamination.py`. Confirmed by reading both tests. The correction is filed
> at `monitor/inbox/20260728T171500Z-RES-3-correction-sealed-audit-and-the-bigger-hole.md`,
> which supersedes the escalation this file originally carried.

**What survives, narrowly:** anyone running `python contamination.py` directly
gets exit 0 on a real sealed contact, and `verify.sh:53`'s own step label — "the
sealed-contact audit" — reads like an invitation to run exactly that. Worth
fixing; not the only gate.

**What replaces it is larger, and I verified it myself.** The two tests that do
wire the verdict to an exit code assert over `all_ledger_audit()`, and that
function's ledger list is hard-coded (`contamination.py:60-63`):

```
scanned: 3   all_clean: True
   arc-recon/data/recon_ledger.jsonl
   baseline-arms/ledger.jsonl
   baseline-arms/probe_log.jsonl
```

`baseline-arms/out/shards/` currently holds **28 shard ledgers** —
`ledger.ar25.jsonl`, `ledger.g50t.jsonl`, `ledger.a7up-opus-*.jsonl` and their
paired `probe_log.*`. **Not one of them is scanned.** The campaign moved to
sharded writes; the audit's hand-written list still names the pre-shard paths.
And the test meant to guard coverage asserts `ledgers_scanned >= 1` — a lower
bound that cannot fail when 28 ledgers go unread.

So the corrected shape is sharper than the one I first reported:

> **The verdict is wired to an exit code. It is wired to the wrong object.**
> `all_clean is True` is a true statement about three ledgers, and the money was
> spent elsewhere.

This is *harder* to fix than a missing `and`, because the repair is to make the
scan surface **discover itself** rather than be listed by hand — which is
exactly what `figures/sources.py` already does with its `Rule` type (declare the
directory, the filename pattern, and a floor; let the filesystem enumerate), and
exactly the failure `figures/PLAN.md §3, §10` records happening twice: data
landed on disk and did not reach a figure until somebody edited two files.
Same disease, this time on the sealed-contact audit.

Three layers, and only the third is broken — saying this imprecisely would
misdirect the fix:

| layer | state |
|---|---|
| **interception** — the proxy guard refusing a live request to a sealed game | **sound, and the best-tested thing in the repository.** A numbered red-line suite, each case constructing a specific attack and asserting it is blocked, short-id forms included. 259 proxy tests green. |
| **detection** — `sealed_api_contacts()`, `claim_set()` | **correct on what it is pointed at.** It identifies injected contact; `report["clean"]` is `False` and the game is named. |
| **reporting** — verdict → exit code | **present, via pytest; absent in `contamination.py` itself.** |
| **scope** — which ledgers get looked at | **3 of 31.** The real gap. |

So this is not "the guard failed", and it is not "nothing would go red" either.
It is: **the thing that goes red is looking at three ledgers, and the campaign
writes twenty-eight others.**

The red-line suite's own numbering, checked because I had cited it as the
standard: the series runs to 46 but **42 cases exist** — `RED-24` and `RED-25`
are missing, and both belong to the critical sealed class. They were never
written. That does not change the suite's standing as the best negative-control
work in the repository; it does mean the number I quoted was wrong, and a gap in
the sealed class is the least comfortable place for one.

Not fixed here: `arc-recon` and `proxy` are not this item's territories.

---

## What good looks like, and it exists here

The census is not a list of complaints about a careless repository. Two
territories are doing this properly, and they are the reason the standard is
stateable at all.

**`figures/check_coverage.py --self-test`** reconstructs the pre-P8 tree and
*requires the probe to fail on it*, before the real check runs. It was written
because P8 found the failure twice — data tracked, committed, and never read by
the figure that was supposed to draw it, with every other gate green. The
negative control exists because a real incident proved the positive control
insufficient.

**`proxy/`'s red-line suite** is constructive rather than confirmatory: each
test builds the attack and asserts it is refused. That is the difference between
"we ran it and nothing bad happened" and "we made the bad thing happen and
watched it get stopped".

**`exam/`'s calibration** does the same for a judge rather than a guard:
pre-registered fake candidates — an oracle that must score 1.0, a null that must
score 0.0 — plus injected faults, observed turning `run_exam --calibrate` red.

The pattern common to all three is worth naming, because the rest of the
repository can copy it without inventing anything:

> **The negative control is an input, not a claim.** You do not assert that the
> gate would catch X. You construct X, run the gate on it, and assert the
> non-zero exit.

---

## Why this concentrates in exit codes, and what it costs the paper

A gate's audience is a machine. `verify.sh` steps, the merge gate, and any CI
hook consume exactly one bit — the exit status — and discard stdout. A verdict
rendered into a report and not into that bit has been written for a reader who,
by construction, is not reading: the whole point of a green run is that nobody
looks at it.

**A claim this file originally made here, withdrawn.** The draft asserted that
several paper claims rest on "the verify script is green". The adversarial
reviewer searched `papers/` and found **no reference to `verify.sh` anywhere in
the text**. That section was arguing against a position nobody holds, and it is
removed rather than rephrased.

What survives is narrower and does not need the paper to have said anything:
**greenness carries different amounts of evidence in different territories, and
the difference is not visible from the green line itself.** A gate with a
demonstrated negative control (exam's calibration, figures' coverage probe, the
proxy red lines) supports a claim in a way an undemonstrated one does not — and
the census's answer is that 35 of 127 entry points have no such demonstration at
all. Whoever eventually cites a gate should cite *which* one, and whether it has
ever been observed red. That is advice for future citation, not a correction of
existing text.

## A defect in this census's own method, found by the census

**The six auditors shared one worktree.** That was my design error, and it
confounds a specific class of finding.

Several auditors ran the entry points they were surveying — which is the right
thing to do, `实测` beats `读码` — and several of those entry points *write*:
runners regenerate artefacts, `battery.run_battery` defaults its `--out` to the
tracked `battery/artifacts`, figure builds write `out/` and `csv/`. Because all
six were operating in the same checkout at the same time, any finding of the
shape

> "I ran X, and afterwards N tracked files were modified"

**cannot be attributed to X from this run alone.** One auditor noticed exactly
this and reported it as an anomaly — 51 tracked files changed under directories
it had never entered — which is the correct reaction and is why it is written
down here rather than quietly dropped.

What this touches, and what it does not:

* **Confounded, and must be re-run in isolation before anyone quotes it:** the
  claim that running the arms' offline runners leaves ~29 tracked files
  modified with no gate going red. The *shape* of that claim is corroborated
  independently by reading — `battery.run_battery`'s default output path is the
  tracked artefact directory, which is a code fact, not a timing observation —
  but the count and the file list are not safe to cite.
* **Also confounded, which this file first got wrong.** The draft claimed exit
  codes were safe: "every `实测` finding whose evidence is a command's exit code
  rather than a change to the tree". The adversarial reviewer found three
  sources pinned by `figures/SOURCES.sha256` that a *different* auditor had
  rewritten mid-census — so a gate can go red or green because of what a
  neighbour did, and its exit code is then evidence about the neighbour. **An
  exit code is not immune; it is downstream of the tree.** The clean class is
  narrower than I wrote: findings established by **reading source**, plus exit
  codes observed against an **injected input in a private scratch copy** (which
  is how the reviewer's own sealed-contact reproduction was done, and why that
  one stands).

The artefact-drift findings and the tree-dependent exit-code findings are marked
in `CENSUS_TABLE.md` §4. The census's surviving headline — the audit's scan
surface covering 3 ledgers of 31 — was established by reading the hard-coded
list and running the function in isolation, and does not depend on the shared
tree.

**The lesson is the item's own lesson, applied to itself:** an auditor that
writes must be isolated from an auditor that observes, or the observation is
about the wrong cause. A parallel survey of *read-only* questions can share a
tree; this one stopped being read-only the moment `实测` was required, and I did
not notice the change of kind when I wrote the six briefs.

## What this item did and did not do

**Did:** surveyed the entry points, filed the per-territory tables, and escalated
each finding to the territory that owns it. **Did not:** fix anything outside
`verify-lab/` and `worldgen/`. A census that repaired what it counted would be
unable to say what the state was.

One fix *is* being carried out, deliberately, as a worked example: `worldgen`'s
factory gate prints `green` and exits 0 while `QC.json` and `QC_MUTANTS.json`
both carry `pass: false`. It is being repaired under `V12-worldgen-gate-deaf`
with the negative control as the acceptance line — a fix without one would be,
in evidence, indistinguishable from the current state. A census that produced
only accusations and no demonstration of the remedy would be easy to file and
easy to ignore.

---

# The standing probe (V14)

The census above is a photograph. 35 of 127 entry points had no executable
demonstration that they can fail, and nothing in this repository asks the 36th
for one. `verify-lab/negctl/` is the part that asks.

```bash
python verify-lab/negctl/probe.py             # the probe; exit 1 on a finding
python verify-lab/negctl/probe.py --verbose   # every entry point and its verdict
python verify-lab/negctl/calibrate.py         # the criterion against V11's 127 rows
python -m pytest verify-lab/negctl/tests -q   # the probe's own negative control
```

On this tree, today: **141 entry points, 141 pinned, PROBE: green, exit 0.**

## What had to be decided before any of it could be written

**"Has a negative control" was a human judgement.** Six auditors read code and
decided. To make it standing it has to become decidable, and the proxy is:

> some `test_*` function in some `test_*.py` **targets this file** — an import
> binding in its module resolves here, and the function, or a helper defined
> beside it, uses that name — **and contains a failure assertion**:
> `pytest.raises`, `assert <exit code> == <nonzero>`, `assert not <verdict>`,
> `assert <findings> != []`, `assert any(... for ... in <findings>)`, and the
> short pinned list in `criterion.py`.

Parsed with `ast`, never grepped, for the reason `figures/verify.sh` gate 7
records: its first version was a regex and its first finding was a phrase inside a
docstring. A docstring that says "this is the negative control" is invisible to
this criterion on purpose.

**The proxy is not the judgement, and the gap is measured, not guessed.**
`runs/20260729T041500Z-V14-standing-negative-control-probe/CALIBRATION.md`, on the
103 census rows that name a single Python file:

| | count | rate |
|---|---|---|
| false `present` — a real gap the probe stays quiet about | 3 of 34 | 8.8% (**0.0%** excluding the 8 files the census itself judged twice) |
| false `absent` — a red on a gate that *does* have a negative control | **20 of 63** | **31.8%** |

The naive criterion — judge by whether the test function's *name* sounds negative
— is strictly worse at the same false-positive rate (FNR 44%), and is kept in the
code only as the weakened probe in the not-idling proof.

**Only deviation gates.** Somebody else's 35 gaps are not this item's to close, so
`negctl/KNOWN_GAPS.json` pins all 141 entry points with the territory that owns
each — the shape and the reasoning are `worldgen/qc/KNOWN_MISS.json`'s. A pinned
gap is quiet. A **new** entry point with no negative control, or a pinned
`present` that has become `absent`, is red. Two of V12's rules are deliberately
softened and the reasons are in `probe.py`'s docstring: a *closed* gap reports
rather than gates (141 files across nine territories, and a probe that turns every
repair into a red gets switched off), and so does a gate that has lost its
non-zero exit path (the enumerator that decides what counts as a gate has never
been calibrated against anything, and gating on an uncalibrated enumerator is the
mistake this lab exists to name).

**The probe has its own negative control, and it is not idling.**
`negctl/tests/test_probe.py`, 24 tests: a synthetic tree with a new gate and no
negative control must exit non-zero; the same tree with one must exit 0; tests
that only exercise the happy path must not count. Then each planted red is replayed
against a deliberately weakened probe and the test asserts the weak version *lets
it through* — `NOT_IDLE.md` has the table. It earned its keep immediately: the
first run failed 9 of 24 because the enumerator only recognised `return 1` and not
`return 1 if problems else 0`, which is how most of this repository spells it. The
probe was reporting green on a tree containing a planted, undemonstrated gate.

## Should this be a merge gate

**No. Not today, and not on `NEW_GAP`.** Run it standing and report-only. The
argument is six numbers, not an impression of how noisy it felt; an adversarial
pass (`runs/20260729T041500Z-V14-.../ADVERSARIAL.md`) went looking for reasons to
trust it more and returned reasons to trust it less.

| # | the number | why it blocks admission |
|---|---|---|
| 1 | **the enumerator has never been calibrated, and `NEW_GAP` is 100% its output** | 141 entry points; of the 90 gates V11 located to a `.py` file, it finds **67 — it misses 23, or 26%.** Every miss is a class: 13 are library gates that refuse by raising and have no `__main__` at all (`proxy/guard.py`, `exam/leakage.py`, `theoria-arm/armtools/archive.py` — *the file V11's sharpest finding is about*). `probe.py` already exempts `NOT_A_GATE` from gating on the grounds that gating on an uncalibrated enumerator is the mistake this lab exists to name. That exemption covers one error direction and `NEW_GAP` rides the other. |
| 2 | **≥17 of the 141 are not acceptance entry points** | 4 world definitions (`*/ground_truth.py`), 3 report scripts, a package `__init__`, 3 exhibits, and **5 one-off scripts inside frozen `runs/<id>/` directories**. |
| 3 | **`runs/<id>/` grows on every experiment** | `MANIFEST.json` provenance is canonical here, and dropping a `main() -> return 0 if ok else 1` script beside it is routine. Under a blocking gate, **every new run directory is a red**. |
| 4 | **FNR 32%** | 20 of 63 gates that V11 says have a negative control are scored `absent`. Each is a red on somebody who did the thing right. The live example is the worst one available: `monitor/tests/mutants.py` — a full mutation testbed that reinstates each fixed defect in a scratch copy and fails if the suite stays green — is enumerated as a gate and registered in `KNOWN_GAPS.json` as *lacking* a negative control. Exactly backwards. First red is a discussion, third is a line in the pin, tenth is the probe switched off. |
| 5 | **the criterion is tree-global; a merge gate is PR-local** | Resolution is over the whole tree, so **one track's import decides another track's verdict**. Before round 5 that was literal: `ablation-arm/tests/test_exhibits.py` determined the verdict of `cold-start-a0/run_all.py`. In a repository whose first rule is that the two tracks do not communicate and commit only their own paths, a gate that lets track A redden track B manufactures ownership disputes. |
| 6 | **a file-level `present` is not a promise about every gate in the file** | See `CALIBRATION.md` §3b. `worldgen/build.py` is `present` on a real negative control for `gate_failures()`, while `check_determinism()` beside it — the strongest determinism claim in the repository — is called by no test anywhere. The probe is silent about it. A verdict that claims coverage it has not got is more dangerous than no verdict. |

### The most aggressive form that is defensible today

Standing, report-only. **If it is ever put in the gate, let `REGRESSION` block and
`NEW_GAP` only report.** The reason is structural rather than a matter of taste:
`REGRESSION` requires the file to have been scored `present` at pin time, which
means it has **already passed the resolver and the enumerator** — the two
uncalibrated layers. It fires only on a *change against a definite prior state*, so
its false-positive mechanism is far narrower than `NEW_GAP`'s, which inherits every
error in an enumerator with 26% miss and ≥17 spurious entries. `NEW_GAP` is the
high-value finding and the low-confidence one; that combination belongs on a review
checklist, not in branch protection.

### What would have to be true first

1. **Calibrate the enumerator** against V11's 90 locatable gates and print its
   confusion matrix beside the criterion's, as prominently. Exclude `runs/**` and
   `**/ground_truth.py`, or require an entry point to be tracked and outside
   `runs/`.
2. **Index package directories** and read the `sys.path.insert` arguments in test
   files. Round 5 closed the cross-territory leak by refusing to resolve, which
   buys silence at the cost of recall; the real fix is to resolve correctly.
3. **Make the criterion function-granular**, or stop reporting `present` at file
   level at all.

Until those three, the honest claim for this probe is: high precision on `NEW_GAP`
when it fires, no useful recall, and two uncalibrated layers underneath. That is a
good reviewer's assistant and a bad merge gate.

## Confirmed by the adversarial pass and deliberately not fixed here

Recorded rather than repaired, so the next person inherits findings instead of
rediscovering them. Each is real and each was reproduced.

* **`_looks_like_exit_code` matches `_EXIT_WORDS` as bare substrings on dict
  keys.** `x["search_timeout"]`, `x["source"]`, `x["arc_calls"]`, `x["n_forced"]`
  all contain `rc`, so `assert register.counts()["search_timeout"] == 1`
  (`theoria-arm/tests/test_arm.py:471`) reads as a non-zero exit assertion. It is a
  counter. This is the same bug the function's own docstring claims to have fixed,
  surviving on the `ast.Subscript` branch, which uses substring matching while the
  `ast.Name` branch uses equality. No entry point flips on it today. It is loaded.
* **Detector B matches function names, never file names.**
  `cold-start-a3/a3pipeline/negctl.py` — a module that is nothing but a negative
  control, and which V11 calls the best one in the repository — is scored `absent`,
  while `"negctl"` sits in `_SELFTEST_NAMES` being compared against `run_all` and
  `main`.
* **`scan_selftests` issues itself a certificate.** Its own name contains
  `selftest` and its body calls `.append`, which is all `_shape_of_selftest`
  requires.
* **The thin-CLI-over-a-tested-library pattern is a systematic false-negative
  generator.** `exam/tools/run_selftest.py` reads `absent` because its negative
  controls import `exam/grading/selftest.py`, which is not itself an entry point.
  63 of the 110 `absent` entry points sit in territories carrying at least one
  failure-assertion edge.
* **`--detector AB` should be withdrawn.** 118 test functions in the tree qualify
  *only* through `assert <bad> not in <output>`, and 104 of them are outside
  `proxy/`, where the rule was justified — sampling finds format checks, invariant
  checks and hygiene assertions at the end of successful runs. The one extra false
  positive it buys is `theoria-arm/harness/run.py`, whose `assert DEFAULT_KEY not in
  json.dumps(everything)` closes a green end-to-end run into which nobody planted a
  key. Shipping `A-B` was right; leaving `AB` on the CLI leaves a known
  false-positive source within reach.
* **All 7 shell gates are out of scope, and all 7 are gates.** `figures/verify.sh`,
  `arc-recon/verify.sh`, `ablation-arm/verify.sh`, `proxy/verify_spend.sh`,
  `monitor/verify.sh`, `monitor/verify_quota_exit.sh`, and the c7 run's own
  `verify.sh`. `monitor/gates.py` defines this repository's canonical gate name as
  `verify.sh` **or** `verify.py`, so shell is a first-class citizen of the
  repository's own definition and the probe excises it entirely. One of the best
  negative controls in the tree — `probe_mentions`'s pre-registered expectations —
  runs from a heredoc inside one of them.
