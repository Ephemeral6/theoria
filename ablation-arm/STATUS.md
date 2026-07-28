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
