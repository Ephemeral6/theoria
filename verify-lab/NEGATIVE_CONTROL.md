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
invokes it through a `step` helper that keys on exit status only (`verify.sh:18-28`),
so a real sealed contact prints its own name and is then reported `-- ok`,
and the run ends `VERIFY: green`.

Three layers, and only the third is broken — saying this imprecisely would
misdirect the fix:

| layer | state |
|---|---|
| **interception** — the proxy guard refusing a live request to a sealed game | **sound, and the best-tested thing in the repository.** RED-01…46, each asserting a specific attack is blocked, short-id forms included. 259 proxy tests green. |
| **detection** — `sealed_api_contacts()`, `claim_set()` | **correct.** They identify injected contact; `report["clean"]` is `False` and the game is named. |
| **reporting** — verdict → exit code | **absent.** |

So this is not "the guard failed". It is: *if the guard were ever bypassed,
nothing afterwards would go red.* The first is not happening today; the second
is the only thing we would have to find out.

Reproduced twice by the auditor against injected ledgers in a scratch directory,
then confirmed independently by me reading `main()` and `step()` end to end.
Filed to the owning territory at
`monitor/inbox/20260728T154500Z-RES-3-sealed-contact-audit-cannot-fail.md`; not
fixed here, because `arc-recon` is not this item's territory and because whether
`needs_adjudication` *should* turn the gate red today is a judgement belonging
to whoever understands that ledger's semantics.

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

For the paper this cashes out concretely. Several claims are backed by "the
verify script is green":

* determinism of artefacts,
* zero sealed contact,
* the figure pipeline matching its sources.

The census's answer is that **greenness carries different amounts of evidence in
different territories, and the difference is not visible from the green line
itself.** A claim resting on a gate with a demonstrated negative control (the
proxy's interception, exam's calibration, figures' coverage probe) is supported
in a way that a claim resting on an undemonstrated one is not. Any paragraph
that cites "verify is green" should be citing *which* gate and whether that gate
has ever been observed red.

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
