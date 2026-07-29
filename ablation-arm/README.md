# ablation-arm — Theoria minus the theorem obligations

> 消融臂 = 只留表示层。刀口落在 **U2|U3 边界**：保留 DSL、对象化、廉价重放层；
> 砍掉全部证明义务——无 Lean、无证书、UNSAT 裸信、玩法书定理级降为经验级。
> — [`DESIGN.md`](DESIGN.md) §3, §4

This is the arm a reviewer who read only the representation half of the paper
could build for themselves. It exists so that the punch *"你只是发了 diff"* can be
**caught and measured** rather than argued with.

```bash
bash ablation-arm/verify.sh              # the completion gate. GREEN or nothing.
python ablation-arm/build_theory.py      # cut theory/ from upstream manuals
python ablation-arm/run_arm.py           # the five worlds, every beat
python ablation-arm/run_arm.py --twice   # two runs, compared
python ablation-arm/run_exhibits.py      # E1, E2, E3
python -m pytest ablation-arm/tests -q   # 56 tests
```

Zero API calls, zero network, zero dollars, zero sealed-pile contact. Every
world here is self-built and in neither pile.

## What it found

**A true impossibility and a false one come back identical.** Ten
decision-carrying fields — verdict, `settled_by`, `certificate_owed`,
`directed_probes_scheduled`, `distinguishes_proof_from_exhaustion`, the cheap
layer's verdict, the surprise count, whether the loop turned, whether theorize
was owed — are the same for `a0-no-button` (really unsolvable) and `a2-holed`
(really solvable in 18 moves).

Nothing here is a bug. The fields match because the cut removed the only
machinery whose output would have differed: the certificate obligation and the
directed probes it schedules. That is P-6, and it is the A4 ticket's question
answered with a table instead of an argument.

**Measured at the verdict, the two arms are indistinguishable.** E1 gets the
right answer for a world that really is unsolvable. An evaluation that scores
answers would report this ablation as having cost nothing. What separates the
arms is the column next to it — the full arm leaves `[{"axioms": [], "name":
"unsolvable"}]`, this arm leaves `certificate: None, certificate_owed: False`.
判决相同,理由蒸发.

**The ablated arm can still repair; it just never learns it has to.** Handed the
world's solved episode for free, it localises the holed manual correctly —
`culprits = ['mispredicted_step']`, one disagreeing step. So the ablation did
not remove the ability to repair. It removed the thing that *produces* the
counterexample. The repair machinery is intact and idle.

## The five worlds

| world | manual | verdict | what it is for |
|---|---|---|---|
| `a0-base` | `a0_base.dsl` | solvable | P-1/P-2's numbers, P-5's verdict |
| `a0-no-button` | `a0_no_button.dsl` | unsolvable, **and right** | **E1** — a true impossibility |
| `a2-base` | `a2_base.dsl` | solvable | the A2 world with its teleport rule |
| `a2-holed` | `a2_holed.dsl` | unsolvable, **and wrong** | **E2** — the ticket's exhibit |
| `a2-charitable` | `a2_base.dsl`, workaround off | solvable | E3's material — see below |

## The loop turns on a bus, and that is the whole design

`DESIGN.md` §7.2: an ablation that *deleted* `refute/locate/probe/repair` from a
step table and then reported that the ablated arm never repairs would be
dismantling the loop by hand and calling the result a finding.

So both arms share one scheduling rule, `Theoria.md:233`'s 有意外才回 theorize,
written once:

```python
if bus.turns_the_loop():   # i.e. `not bus.empty()`
```

`run_arm.BEATS` includes `theorize`. Whether the loop turns is a consequence of
what can reach the bus, and the incision decides that: no certificate obligation
⇒ no theorem ⇒ no `depends:` clause ⇒ no directed probe ⇒ nothing to raise.
**The loop not turning is derived, not arranged.**

Theorize is reached when the bus says so and records *that a turn is owed and
what owes it*, then stops — it is the LLM's beat and this arm is offline by
construction. Recording the debt is honest; inventing the turn would not be.

## The U ladder, as a measurement

| rung | state | how it is known |
|---|---|---|
| U1 对上过去了吗 | attained | cheap replay green on all five worlds |
| U2 说得清吗 | attained | every manual parses; 3 of 4 forms emitted |
| U3 证得动吗 | **unreachable by construction** | 0 certificates owed, expensive layer omitted and raising, 0 theorems survive the cut |
| U4 修得好吗 | **unreachable by consequence** | 0 loops turned, 0 directed probes scheduled |

U4 is out of reach **not because repair is broken** but because the refutation
never arrives. That is P-7, and it carries E2's finding.

## The exhibits

| | holds | |
|---|---|---|
| **E1** | yes | a true impossibility: verdict identical, reason evaporates |
| **E2** | yes | a false one, believed in silence — plus the charity control above |
| **E3** | **no** | the charitable variant's construction no longer exists |

E3 is reported as a **pre-registered falsifier**, not as a missing deliverable.
Its recipe needed D-A2-006's PDDL grounding defect, and that defect was closed
upstream: the workaround now emits byte-identical PDDL with the patch on and
off, so the complete manual plans SAT either way and the exhibit cannot start.
Five measurements are in [`exhibits/e3_charitable.py`](exhibits/e3_charitable.py)
and [`DECISIONS.md`](DECISIONS.md) D-AB-015. `run_exhibits.py` exits 0 anyway — a
falsifier that turns the build red is a falsifier nobody will ever report.

## What A4a settles, and what it hands to A4b

`verify.sh` asserts **three and a half of the seven pre-registered predictions**
(P-3, P-6, P-7, and the *correct* half of P-5), all four of §6's shadows, and
the read-only pin. The other three and a half are **comparisons against an arm
nobody has run**; they are printed under their own heading and can never turn
the gate red.

Two of them are worse than uncompared — **the instrument does not exist**:
nothing here computes a held-out split (P-2) or a search-and-proof fuel account
(P-4). A4b needs both built before those predictions can be read at all.

## Read-only, and how that is checked

`cold-start-a0`, `cold-start-a2`, `theory-compiler`, `engine-rig`, `CONTRACTS`
and `proxy` are imported and never written. `pin.hash_tree` runs either side of
every full run, and `tests/test_readonly.py` asserts nothing moved — including
the two upstream `artifacts/` directories that `pin.SKIP_DIRS` deliberately
excludes, because that exclusion is a blind spot exactly where the exhibits call
into `a2pipeline`.

## Layout

| path | what |
|---|---|
| [`DESIGN.md`](DESIGN.md) | P-18's, finished before the code, unmodified |
| `ablcore/` | P-18's eight modules — the incisions themselves |
| `worlds/` | the worlds, selected from upstream and not reimplemented |
| `theory/` | **generated**: upstream manuals with the laws section cut |
| `build_theory.py` | the cut, and `--check` |
| `run_arm.py` | the driver: the beats, the bus, the loop gate |
| `exhibits/` | E1, E2, E3 |
| `verify.sh` / `verify.py` | the completion gate |
| [`DECISIONS.md`](DECISIONS.md) | design calls and their reasons |
| [`STATUS.md`](STATUS.md) | what is done and what is not |
| [`RUN_STATE.md`](RUN_STATE.md) | the human narrative |
