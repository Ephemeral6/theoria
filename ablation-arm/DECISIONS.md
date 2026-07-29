# DECISIONS — ablation-arm

Design calls and their reasons.

**Who wrote what.** `DESIGN.md` and `ablcore/` are P-18's, verbatim and
unmodified. P-18 never wrote this file, but two lines of P-18's source cite it
and one cites a specific entry:

    ledger_abl.py:15   "One honest wrinkle, and it is registered rather than
                        patched around (DECISIONS D-AB-004)."
    ledger_abl.py:59   "See ablation-arm/DECISIONS.md D-AB-004."

So **D-AB-004 is reconstructed from the source that cites it**, quoting P-18's
own reasoning rather than inventing a rationale, and it is labelled as
reconstructed. A4a's own calls start at D-AB-010, leaving the gap for anything
else of P-18's that turns out to be recoverable from the code.

---

## D-AB-004 — the ledger goes out under `arm: "theoria"` *(reconstructed)*

**Reconstructed from `ablcore/ledger_abl.py:9-30`, which states the decision and
its reason in full. Nothing here is A4a's judgement.**

`proxy.ledger.ARMS` is a frozenset with no name for an ablation arm, and adding
one means editing another track's file, which every arm README in this repo
forbids. So records go out under `arm: "theoria"` — true, in that this *is* the
Theoria inner loop — and the `run_start` record carries an `ablation` block
naming the incision, the prompt, and the name that was wanted
(`requested_arm_name: "theoria_ablate"`).

**A4a re-verified the consequence P-18 could not.** `STATUS.md` (A4's, not
P-18's) recorded this as a live cross-track blocker: `RunLedger(arm=
"theoria_ablate")` constructs silently and then fails `validate_ledger` on every
line. That is true of the *name* and does not apply to the *code as written*:

```
proxy.ledger.ARMS   = [bare_cc, mock_arm, probe, replay, schema_repro, theoria]
ledger_abl.ARM      = 'theoria'         -> in ARMS
requested_arm_name  = 'theoria_ablate'  -> not in ARMS, and never used as the
                                           arm field; it is metadata in the
                                           ablation block
three episodes      -> PASS (0 problems) each, under proxy validate_ledger
```

The blocker is retired with evidence. Registering `theoria_ablate` would still
be *better* — a reader filtering ledgers by arm cannot separate the two arms
today — and that remains a request for the proxy track, not a defect here.

---

## D-AB-010 — worlds and manuals are **selected**, not reimplemented

`worlds/a0_abl.py` hands the upstream `A0World` through unwrapped;
`build_theory.py` produces `theory/` by running upstream manuals through
`ablcore.downgrade` and nothing else.

**Why.** `DESIGN.md` §5 is the other half of attribution: 一字不改的部分. Every
line of adapter between this arm and the world is a place a **second** difference
could enter unnoticed — a subtly different `step`, a render that transposes, a
goal test that rounds. P-1 and P-2 predict this arm's replay accuracy equals the
full arm's; if the two arms do not drive the *same object*, those predictions
stop testing the cut and start testing the adapter.

The same argument makes `theory/` a build rather than five edited copies. A
hand-edited copy is a *claim* that only the laws section moved.
`downgrade_text` asserts that byte-for-byte on every run, so routing every file
through it converts the claim into a check, and `--check` makes a hand-edit a
red build instead of a silent divergence.

**The one wrapper**, `a2_abl.HoledManualWorld`, exists because the exhibit needs
two transition functions that disagree and upstream deliberately does not
present the second one as a world — `A2World.step_holed` is documented there as
*"not a variant of the world … the referee's copy of what the holed manual
claims"*. It delegates every method except `step` and carries
`is_a_world = False`, because confusing the two is precisely the failure E2
exists to display.

## D-AB-011 — the cut is checked in the parser, not in a grep

`build_theory.verify_ast()` reads all four cut manuals back through the real
`parse_theory` + `parse_semantics` and asserts zero theorems and every invariant
`empirical`.

**Why.** A grep says the *text* no longer contains `[status: proven]`. The file
the arm runs on is the **AST**, and a cut that satisfied a grep while leaving a
theorem the parser can still see would be a cut in name only.

It also settles, at the earliest possible point, something the driver depends on
absolutely: `compile_ablated` calls `parse_semantics`, which raises on a manual
that does not declare semantics. That failure is not hypothetical — `a0-spike`'s
v0.1 manual is refused by the v0.2 grammar for exactly this reason — and it
would otherwise surface inside the driver, three steps from its cause.

Both failure modes were watched refusing: appending one comment turns `--check`
red on the byte diff, and restoring one `[status: proven]` turns it red on the
byte diff **and** the parser independently.

## D-AB-012 — the loop turns on the bus, and the repair beats are not deleted

`run_arm.BEATS` includes `theorize`, and the schedule is one line:
`if bus.turns_the_loop()`.

**Why.** `DESIGN.md` §7.2 is the most important sentence in the design: 不能把
`refute/locate/probe/repair` 从步骤表里删掉,然后报告"消融臂修不好". A driver with
those beats missing would be dismantling the loop by hand and calling the result
a finding — and it would violate the attributability constraint, because the
difference would be the author's rather than the incision's.

So whether the loop turns is a consequence of *what can reach the bus*, which
the incision decides. On a UNSAT plan the full arm owes a certificate, generates
invariants, proves them, reads the theorem's `depends:` clauses, probes them,
and the probe's refutation is a surprise. This arm owes nothing, so nothing
reaches the bus.

**Theorize is reached and records a debt rather than being run.** Theorize is
the LLM's beat and this arm is offline by construction. When the bus is
non-empty the driver writes down *that a turn is owed and what owes it*, and
stops. Recording the debt is honest; inventing the turn would not be.

## D-AB-013 — the trace is the record its manual was theorized from

Each world's `trace` is read out of the upstream artefact that names it, never
guessed, never re-explored.

**Why, and what it cost to learn.** The rule sounds obvious and is not
self-applying. The driver's first run pointed the holed manual at
`raw_trace.jsonl` — the A2 world's trace, the "obvious" choice — and the cheap
layer went red, the loop turned, and **P-6 looked falsified**.
`cold-start-a2/artifacts/exhibit_report.json` names the holed manual's evidence
as `history_trace.jsonl` and records both readings itself: green over 184
frames on the evidence, red with 44 anomalies on the fuller sweep, with its own
note that *the hole is invisible to the evidence its theorizer had*. The run had
reproduced the **sweep**, not the evidence.

Three consequences, and the third is the one that matters:

1. `a2-holed`'s evidence is `history_trace.jsonl`;
2. the fuller record is kept as a **sweep** — run, reported, and explicitly off
   the bus, because a surprise the arm could not have had is not a surprise, and
   putting it on the bus would turn the loop on the referee's knowledge;
3. **P-1's pre-registered counts are asserted at run time.** `DESIGN.md` §8
   states P-1 as counts — A0 base 22356 pixels, A2 holed 14904 — and a pixel
   count is a fingerprint of *which record was replayed*. A wrong trace now
   turns the run red instead of producing a plausible finding.

Re-exploring instead of reading was never an option: a different trace is a
second difference, and `Theoria.md:280` says a second difference makes the first
unattributable.

## D-AB-014 — a falsifier is a result, and does not turn the build red

`run_exhibits.py` exits 0 with E3 reporting `holds: False`.

**Why.** `DESIGN.md` §10 pre-registers four ways this design could be wrong. A
build that goes red when one of them fires creates pressure to not report it —
the discovery and the broken build become indistinguishable at the exit code,
and the cheapest way to a green build is to stop looking. The status code is for
a broken run: a missing artefact, an exhibit that cannot read the arm's own
output. `verify.sh` inherits the same rule for the four predictions that need a
second arm.

`tests/test_exhibits.py` **asserts E3 is not constructible**, which reads oddly
until you consider the alternative: a test that skipped it, or asserted
`holds is True` and got deleted when it failed, would leave the repository with
no record that a designed exhibit had expired. If the mechanism is ever
restored, that test fails, and its message says to rebuild E3 and rewrite the
test rather than relax it.

## D-AB-015 — E3's designed construction no longer exists, and is reported, not substituted

`DESIGN.md` §E3 builds the charitable exhibit by disabling D-A2-006's workaround
so the planner returns UNSAT on a manual with nothing wrong with it. Five
measurements say it cannot be built here any more:

| | |
|---|---|
| M1 | `pddl_addressable(enabled=False)` and `enabled=True` emit **byte-identical** PDDL |
| M2 | the generator names 38 cell objects where the derived arena holds 37, so the Portal entry grounds with the patch off — **D-A2-006 was closed upstream** and `compile_abl.pddl_addressable` is dead code on this input |
| M3 | so the complete manual plans **SAT** either way |
| M4 | the nearest live UNSAT on a blameless manual (complete manual, truncated evidence) **raises** a missing-landmark `KeyError` on the witness path, so `locate` cannot return a culprit set at all |
| M5 | the empty culprit set exists on the complete manual with full evidence — but that manual plans SAT, so there is no false impossibility for it to be empty *about* |

E3 needs the conjunction. §10 item 3 pre-registered *三查没有全绿* as a
falsifier; **what is refuted is narrower — not the reading of D-A2-006 but its
continued existence.**

**The point E3 defended survives, and moved.** `e2_a2.charity_control` hands the
holed manual the world's solved episode and gets `culprits =
['mispredicted_step']` with exactly one disagreeing step. The review's punch —
你没给它反例,当然它修不好 — is answered on the exhibit it threatens: the ablation
did not remove the ability to repair, it removed the thing that *produces* the
counterexample.

What is genuinely lost is E3's other half — a clean demonstration that a
planner's UNSAT can be a fact about the encoding rather than the world. M4 is
weaker evidence for it, since a reader can fairly say the fault is the truncated
evidence. Recorded as a gap for A4b.

## D-AB-016 — the gate asserts what A4a can settle and records the rest

`verify.py` splits the seven pre-registered predictions: **P-3, P-6, P-7 and the
correctness half of P-5** are asserted; **P-1, P-2, P-4 and the identity half of
P-5** are recorded and can never turn the gate red.

**Why the split, and why it is loud.** A gate that failed because a comparison
was missing would push whoever runs it toward inventing the second arm's
numbers. A gate that passed while silently skipping four predictions would be
worse — the next reader would take GREEN to mean seven of seven. So the recorded
half is printed in full under a heading that says nobody has compared them yet,
and two of them additionally say that the **instrument does not exist**: nothing
in this arm computes a held-out split (P-2) or a search-and-proof fuel account
(P-4). A4b reading `RECORDED` and expecting numbers would lose a day finding
that out.

**A missing field is not read as the value the gate wants.** `plan_abl` writes
`certificate_owed` and `directed_probes_scheduled` only on the UNSAT branch,
because a SAT plan has no impossibility claim to certify — the witness *is* the
answer. The first version of the gate read that absence as a failure; the repair
was deliberately not to default it to 0, because a gate that defaults a missing
field to the value it wants would pass a run in which the field had silently
vanished. It asks the question only of the worlds where it arises.

The gate was doctored and **watched going red** on exactly the claims that
should have failed. Doing that turned up a second defect: it crashed while
building the evidence for a red claim, which would have lost the report and
every other claim in it. A gate that cannot explain why it refused is barely
better than one that never does.

## D-AB-017 — a subset run declines to overwrite the full record

`run_arm.run_all` writes `artifacts/run_all.json` **only when every world ran**,
decided by itself; `write=True` overrides deliberately.

**Why.** Two different test files ran a subset and silently replaced the
five-world deliverable with a partial one. The first occurrence was fixed by
adding `write=False` at the call site; the second, in another file, showed why
that was the wrong fix. A rule every caller has to remember is a rule that gets
forgotten. The behaviour is pinned by a test, because the default is invisible
at every call site that relies on it.
