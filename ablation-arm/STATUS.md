# ablation-arm — STATUS

**Read this before believing anything else in this directory.**

This arm is **not finished and has never been run**. It was written by P-18,
left uncommitted in a worktree, and preserved here by `A4-ablation-online`
(worker `W-1611`) so that it would stop being at risk of silent loss. Nothing in
`DESIGN.md`, `ablcore/` or `runs/` was modified — it is P-18's work verbatim.
This file, and this file alone, is A4's.

`A4-ablation-online` was **released back to the board unstarted**, because its
stated precondition — "after P-18's ablation arm's offline calibration is
complete" — does not hold. Details below and in
`monitor/inbox/20260728T094500Z-W-1611-a4-precondition-unmet-and-p18-is-a-second-orphan.md`.

## What is here

| | |
|---|---|
| `DESIGN.md` | 21 KB, finished before the code, as it says. The strongest part of the arm. |
| `ablcore/*.py` | 8 modules, ~900 lines. No `TODO`, no `FIXME`, no stub bodies. |
| `runs/2026-07-28-p18/` | three **recon** notes, dated *before* the code |

The cut is a single blade at the U2\|U3 boundary — five incisions (`DESIGN.md`
§C-1…C-5) plus a DSL rewrite demoting `[status: proven]` to `[status:
empirical]`. Four "shadows" fall as consequences and are argued as such, and
seven predictions P-1…P-7 are pre-registered (`DESIGN.md` §8) **before** any run.

## What is verified

Checked by A4, offline, zero cost:

* **All eight `ablcore` modules import cleanly** against upstream from a
  checkout with `ablation-arm/` at the repo root. Every symbol they reach for
  in `cold-start-a0`, `theory-compiler`, `engine-rig` and `proxy` exists. The
  library is wired correctly; it has simply never been driven.

## What is missing

`DESIGN.md` §12 lists the deliverables and closes with its own gate: *"`verify.sh`
的断言就是 §8 的七条预注册 + §6 的四道影子逐条数出来 + 上游树 0 改动。**不绿不许收工。**"*
By that gate this arm is not finished. Absent, all confirmed by inspection:

| missing | consequence |
|---|---|
| `worlds/a0_abl.py`, `worlds/a2_abl.py` | `plan_abl.run_plan(world=…)` has nothing to pass |
| `exhibits/e1_a0.py`, `e2_a2.py`, `e3_charitable.py` | **including the A2 false-theorem exhibit the A4 ticket is about** |
| `theory/` (the arm's downgraded DSL) | `downgrade.py` and `playbook.py` have no input |
| `tests/` | see below — three files claim it exists |
| `verify.sh` | the arm's own completion gate |
| `artifacts/`, `upstream_pin.json` | no calibration result of any kind; `pin.hash_tree` is never called |
| `README.md`, `DECISIONS.md`, `RUN_STATE.md` | `ledger_abl.py:15` and `:59` cite `DECISIONS.md` |
| any driver composing the beats into a loop | the arm cannot be run end to end |

**Zero of the seven pre-registered predictions have been evaluated.** Every
number in `runs/2026-07-28-p18/` is a reading of the *parent* trees' existing
artifacts, not an output of this arm.

## Three claims in the source that are not true yet

Left uncorrected because editing P-18's code would misrepresent what P-18 wrote.
Recorded here instead, which is what a STATUS file is for:

* `_bootstrap.py:24` — *"`tests/test_readonly.py` checks all three by hashing the
  upstream trees around a full run, **so none of the above is on the honour
  system.**"* It is entirely on the honour system; the file does not exist.
* `certify_abl.py:33` — *"`tests/test_incision.py` asserts that nothing calls it."*
* `downgrade.py:22` — *"`downgrade_text` asserts it, and `tests/test_incision.py`
  asserts it again on every generated file."* The in-function assertion is real;
  the test is not.

Also dangling: `ledger_abl.py:25` states *"A request to register `theoria_ablate`
is on PARTNER_SYNC for the proxy track."* No such request was ever posted —
`PARTNER_SYNC.md` has zero occurrences of `ablat`.

## The blocker that outlives this file

A4 requires the arm's ledger to be "同格式、经 proxy" — same format, through the
proxy. It is not, and this needs the **proxy track**, not this one:

```
proxy/ledger.py:31        ARMS = {bare_cc, mock_arm, probe, replay, schema_repro, theoria}
proxy/tools/validate_ledger.py:77-78    if arm not in ARMS: bad(lineno, "unknown_arm", ...)
```

`theoria_ablate` is not in `ARMS`. Verified behaviour: `RunLedger(..., arm=
"theoria_ablate")` **constructs without complaint** — there is no validation at
write time — and the resulting ledger then **fails `validate_ledger.py` on every
line** with `unknown_arm`. So the failure is silent at the point of writing and
loud only later, which is the worst ordering. Registering the name is a
one-line change in a territory this arm may not touch.

## What A4 would additionally need

Beyond finishing the above, the online half needs things that do not exist here
at all: `ablcore/` contains **no harness, no env loop, no model desk, no HTTP,
no API-key read**. `ledger_abl.py:9` says so plainly — *"Zero API calls, zero
network, zero dollars."* The full arm's equivalent (`theoria-arm/harness/`,
`inner/`, `armtools/`) has no counterpart here.

And note what the A4 ticket asks to demonstrate — that the arm believes an
A2-type false theorem — is, by P-18's own design (`DESIGN.md` §E2), an
**offline exhibit on a self-built world**. Running on a live game does not
demonstrate it. P-18 also already qualified the ticket's premise
(`DESIGN.md:186`, from `runs/…/02-a2-anatomy.md` §1): *"工单写的'没有证明义务就没
有打脸机制'，在**框架层面**成立，在 **A2 的实现层面不成立**"* — A2's refutation is
driven by the judge's own solver, not by the theorem. The surprise bus in
`surprise.py` is the workaround, and it too has never been exercised.

## Discipline

Nothing here has ever made an API call, spent a dollar, or touched the sealed
pile. A4 kept that true: this preservation was pure file copy plus eight
offline imports.

---

# A4a-ablation-build — 2026-07-28, worker RES-1

**Everything above this line was written by `A4-ablation-online` (`W-1611`) and
is left standing.** It was accurate when written. Four of its statements are no
longer true, and they are superseded here rather than edited, so a reader who
saw the earlier version can see exactly what changed and why.

The arm is now built and runs end to end. Branch `agent/a4a-ablation-build`,
run record `runs/20260728T130500Z-A4a-ablation-build/`.

## Superseded: "What is missing"

That table is now empty except where noted. Built by this item:

| was missing | now |
|---|---|
| `worlds/a0_abl.py`, `worlds/a2_abl.py` | selected from upstream, not reimplemented (D-AB-010) |
| `exhibits/e1_a0.py`, `e2_a2.py`, `e3_charitable.py` | all three; E1 and E2 hold, E3 is a reported falsifier (D-AB-015) |
| `theory/` | **generated** by `build_theory.py`: 4 manuals + 1 playbook, 7 invariants demoted, 4 theorems deleted |
| `tests/` | 56 tests |
| `verify.sh` | GREEN |
| `artifacts/`, `upstream_pin.json` | `artifacts/` is populated; the pin runs inside `run_arm.run_all` either side of every run rather than as a standalone file |
| `README.md`, `DECISIONS.md`, `RUN_STATE.md` | written |
| any driver composing the beats into a loop | `run_arm.py` |

**Zero of the seven pre-registered predictions had been evaluated.** Three and a
half are now asserted by `verify.sh` — P-3, P-6, P-7, and the *correct* half of
P-5. The other three and a half are equalities with an arm that has not been
run; they are recorded and can never turn the gate red.

## Superseded: "Three claims in the source that are not true yet"

All three were true statements about a state that no longer holds. P-18's source
was deliberately left uncorrected, which was right. The tests it named now
exist, so the sentences are true as written:

| source claim | now |
|---|---|
| `_bootstrap.py:24` — `tests/test_readonly.py` hashes the upstream trees around a full run | true. It also covers the two upstream `artifacts/` directories that `pin.SKIP_DIRS` excludes — a blind spot exactly where the exhibits call into `a2pipeline` |
| `certify_abl.py:33` — `tests/test_incision.py` asserts that nothing calls `expensive` | true, and **parsed rather than grepped**: every `ast.Call` in the arm's sources, because a grep misses `getattr(...)` and trips over the word in a docstring |
| `downgrade.py:22` — the test asserts it again on every generated file | true, and the two halves are separated: the in-function assertion checks the transform *as it runs*, the test checks *the files that shipped* |

`ledger_abl.py:25`'s dangling note stands: **no request to register
`theoria_ablate` has been posted** to PARTNER_SYNC. Still true, still not this
item's to post.

## Superseded: "The blocker that outlives this file"

**It does not apply to the code as written.** The blocker is real about the
*name* and was reasoned about the wrong object:

```
proxy.ledger.ARMS   = [bare_cc, mock_arm, probe, replay, schema_repro, theoria]
ledger_abl.ARM      = 'theoria'         -> in ARMS
requested_arm_name  = 'theoria_ablate'  -> not in ARMS, and never used as the
                                           arm field; it is metadata inside the
                                           run_start record's ablation block
```

Three episodes, checked with `python -m proxy.tools.validate_ledger`:

```
artifacts/a0-base/episode.jsonl        PASS (15 records, 0 problem(s))
artifacts/a2-base/episode.jsonl        PASS (21 records, 0 problem(s))
artifacts/a2-charitable/episode.jsonl  PASS (21 records, 0 problem(s))
```

Registering the name would still be *better* — a reader filtering ledgers by arm
cannot separate the ablated arm from the full one today — and that remains a
request for the proxy track. It is not a blocker on this arm. See D-AB-004.

## Superseded: "What A4 would additionally need"

Still correct that this arm has no harness, no env loop, no model desk, no HTTP
and no API key read, and that A4's online half needs all of them. One line in
that section now has a measurement behind it:

> the A4 ticket asks to demonstrate that the arm believes an A2-type false
> theorem

**It does.** `a2-holed` is green over 184/184 frames of its own evidence, the
planner returns UNSAT, this arm settles it bare, the bus stays empty, the loop
does not turn, and a level solvable in 18 moves is archived as impossible. Ten
decision-carrying fields are identical to `a0-no-button`, where the same verdict
is **true**. Nothing the arm records distinguishes them.

And P-18's qualification of the ticket's premise — 在框架层面成立,在 A2 的实现
层面不成立 — is confirmed and sharpened. `a2pipeline/locate.py` survives the
ablation byte for byte: handed the world's solved episode, this arm localises the
holed manual correctly (`culprits = ['mispredicted_step']`, one step). So *"no
proof obligation means no refutation mechanism"* is false as stated. The true
statement is **nothing ever schedules the experiment that produces the
counterexample** — the repair machinery is intact and idle.

## Still open after A4a

1. **A4b's four predictions**, two of which need instruments that do not exist:
   nothing here computes a held-out split (P-2) or a search-and-proof fuel
   account (P-4).
2. **E3's other half.** No live construction in this repository makes a planner
   return UNSAT on a manual that is correct *and* executable, because D-A2-006
   was closed upstream. D-AB-015.
3. **Two self-built offline worlds only.** `DESIGN.md` §10 item 5: this arm
   demonstrates a mechanism, not an effect size on ARC. That limit must be
   printed beside every conclusion drawn from it.
4. **`theoria_ablate` unregistered** — see above.
5. **`a2_holed` and `a0_no_button` are wrong on purpose.** A future session that
   repairs either one deletes the experiment.

## Discipline

Unchanged and re-verified: no API call, no dollar, no sealed-pile contact, and
no byte written into any upstream tree. `pin.hash_tree` runs either side of
every full run (386 files across six trees), and `tests/test_readonly.py`
asserts nothing moved.
