# RUN_STATE — ablation-arm

The human narrative. Numbers and provenance live in
`runs/<id>/MANIFEST.json` and `artifacts/*.json`; this is what a reader needs to
know that a manifest cannot say.

## Where the arm stands

**It runs.** Before A4a it was ~900 lines of library that had never been driven
— eight modules that imported cleanly and had no caller. `run_arm.py` is the
caller, and five worlds now go through every beat end to end, offline, with the
upstream trees hashed either side.

`bash ablation-arm/verify.sh` is **GREEN**: five stages, ten assertions, 56
tests, byte-reproducible across two runs and two launch directories.

## What is deliberately not here

**Calibration and comparison.** This item is A4a, which the board split off from
A4 after two workers hit context walls on the whole thing. 标定与对照留给 A4b.
That split is not cosmetic — four of the seven pre-registered predictions are
*equalities with the full arm*, and the full arm has not been run. They are
recorded and printed, never asserted, and cannot turn the gate red.

**Two of the four are worse than uncompared: the instrument does not exist.**
Nothing in this arm computes a held-out split (P-2) or a search-and-proof fuel
account (P-4). A4b has to build both before those predictions can be read at
all, and finding that out from a `RECORDED` line would cost a day, so the gate
says it in the line itself.

**Theorize.** The arm is offline by construction. When the bus turns the loop
the driver records that a turn is owed and what owes it, and stops.

## The three things this run learned that were not in the design

### 1. A planner's UNSAT and a theorem's absence are the same sentence

E1 and E2 come back **identical on all ten decision-carrying fields**. One
verdict is true and the other false. Nothing the arm records tells them apart,
because the cut removed the only machinery whose output would have differed.

The design predicted this (P-6). What the run adds is that it is *checkable* —
`run_arm._exhibit_comparison` computes the table, and the comparator is itself
tested against a doctored report to prove it can say `different`.

### 2. The ablated arm can repair. It never finds out it should

This is the correction that matters most, and it goes against the prior
argument rather than for it. `a2pipeline/locate.py` survives the ablation byte
for byte — it needs a compiled manual and one real solution path, and reads no
`.lean`. Handed the world's solved episode for free, this arm localises the
holed manual correctly: `culprits = ['mispredicted_step']`, one disagreeing
step.

So *"the ablated arm cannot repair"* would be false. The true statement is
narrower and sharper: **nothing ever schedules the experiment that produces the
counterexample.** The repair machinery is intact and idle, and idle for a reason
derived from the incision. P-18's recon had already found this; A4a measured it.

### 3. E3 expired

The charitable exhibit needed D-A2-006 — a PDDL grounding defect — to still be
there. It is not. The workaround emits byte-identical PDDL with the patch on and
off, so the complete manual plans SAT either way and the exhibit cannot start.
Reported as a pre-registered falsifier with five measurements, not substituted
with something else wearing E3's name.

The point E3 defended survives and moved into E2 (see 2 above). What is lost is
its other half — a clean demonstration that a planner's UNSAT can be a fact
about the encoding rather than about the world. That gap is A4b's.

## Mistakes this run made, and what caught them

Recorded because the next session will be tempted by the same ones.

**The driver's first run was wrong.** `a2-holed` was pointed at
`raw_trace.jsonl` — the A2 world's trace, the obvious choice — and came back
with three surprises and a turning loop, which reads as P-6 falsified. It was
not: upstream names the holed manual's evidence as `history_trace.jsonl` and
records both readings itself, green on the evidence and red on the fuller sweep.
The run had reproduced the sweep.

*Read the artefact the full arm read* is not a rule a driver can follow by
itself; **which** artefact has to be read out of upstream's own report, per
manual. P-1's pre-registered pixel counts are now asserted at run time, because
a pixel count is a fingerprint of which record was replayed — a wrong trace
turns the run red instead of producing a plausible finding.

**The gate read a missing field as a failure**, then crashed while building the
evidence for the red claim. `certificate_owed` and `directed_probes_scheduled`
are *absent* on a SAT world, not zero — a SAT plan has no impossibility to
certify. The repair was deliberately not to default them to 0, since a gate that
defaults a missing field to the value it wants would pass a run in which the
field had vanished.

**A test overwrote the deliverable it was testing**, twice, in two files: a
subset `run_all` replaced the checked-in five-world record with a partial one.
Fixed at the source rather than at the call sites, because a rule every caller
has to remember is a rule that gets forgotten.

## Gaps

1. **A4b's four predictions**, two of which need instruments that do not exist
   (P-2's held-out split, P-4's fuel account).
2. **E3's other half** — no live construction in this repository makes a
   planner return UNSAT on a manual that is correct *and* executable.
3. **Two self-built offline worlds only.** `DESIGN.md` §10 item 5 says it and it
   must be printed beside every conclusion: this arm demonstrates a
   **mechanism**, not an effect size on ARC.
4. **`theoria_ablate` is still unregistered.** The blocker does not apply to the
   code as written — records go out as `arm: "theoria"` and validate — but a
   reader filtering ledgers by arm cannot separate the two arms. That remains a
   request for the proxy track.
5. **`a2_holed` and `a0_no_button` are wrong on purpose.** Any future session
   that "fixes" one deletes the experiment. `build_theory.SOURCES` says so at
   each entry, in capitals.
