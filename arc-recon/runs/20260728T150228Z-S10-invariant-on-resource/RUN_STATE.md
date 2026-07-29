# RUN_STATE — S10-invariant-on-resource

Worker `W-1251`, 2026-07-28. Branch `agent/s10-invariant-on-resource`, base
commit `fb813ce`.

## What the item asked, and what is here

| goal | state |
|---|---|
| `arc-recon/tools/ledger_invariants.py`: read the ledger on disk, assert no line carries an unredacted credential shape | **done** |
| a test that reads the **real artefact** | **done** — `test_ledger_invariants.py::test_the_shipped_ledger_satisfies_its_own_invariant`, over all 1231 lines |
| a **deliberately red** control | **done** — 17 planted shapes, one per detector claim, plus the other half: a clean row must stay clean, and a report must not echo the value it found |
| folded into the territory's tests | **done** — 111 pass (82 + 29); `verify.sh` gains a step; `bash verify.sh` green |
| the other two resources, same treatment | **written and run, not landed.** They are `monitor/`'s. See §the other two |

## The shape, and why it is this shape

The item is explicit that this must **not** become "one writer". The reviewer's
a′ names the repo's own successful sample as the model, and it is worth stating
what makes it successful: `probe_stickiness.py` — the writer that caused INC-008
— **is still there, still opening the ledger itself**, and the invariant holds
anyway, because it moved onto the artefact. A second writer appears whenever an
instrument needs a field the first writer does not carry, which is a legitimate
need and not abuse. Single entry points are worth it only where a capability can
genuinely be taken away; `proxy`'s no-bypass seal works because the arm never
holds the credential, not because of how the code is arranged.

So `tools/ledger_invariants.py` asks what is on disk and never asks who put it
there. Four tiers, and the split matters because they fail differently:

1. **field-scoped, exact** — header values, cookie-name lists, `set_cookie`,
   URL query parameters. No heuristics. Would have caught INC-008 on the first
   line written;
2. **the literal secret** — does any byte of the file contain the live
   `ARC_API_KEY`? Schema-independent, so it survives a field nobody predicted.
   It needs `.env`, which is gitignored and absent in a fresh worktree, so the
   report carries `live_key_comparison` and a run where it did not happen says
   so instead of counting as a pass;
3. **undeclared credential-shaped fields** — fails closed. A writer adding
   `session_token` gets a red build and has to add a line to `DECLARED_FIELDS`,
   which is the moment somebody looks at the value. This is the tier aimed at
   the *next* incident rather than the last one;
4. **bearer/JWT shapes** in the fields that could carry one — and deliberately
   **not** in `response_body`, because game frames are arbitrary data and a
   check that cries wolf every run is one nobody reads. Tier 2 covers the body.

Two rules the module keeps without exception. **Values are counted and located,
never returned** — a violation is `(line, field, shape)`, because reports get
pasted into commit messages and a scanner that echoed the value would be a
second copy of the leak. `test_a_report_never_carries_the_value_it_found`
asserts that over the serialised report rather than by reading the code. And
**every check has a negative control**, per `test_hygiene.py`'s standing rule and
INC-003's precedent: a comparison that could not fail once reported PASS for two
runs that had both died.

## Measured

```
arc-recon/data/recon_ledger.jsonl             1231 lines  clean
baseline-arms/ledger.jsonl                     560 lines  clean
baseline-arms/probe_log.jsonl                 1953 lines  clean
live key comparison: loaded
```

The live-key tier really ran here (`.env` reachable from the worktree via
`client.main_checkout`), so "clean" on this machine includes "the key is not in
any of those three files".

`redact_ledger.py`'s own scan is **kept** rather than replaced. It checks one
field because that is the field INC-008 was about, and it is the remediation's
before/after instrument; `verify.sh` now runs both, with a comment saying which
is the specific check and which is the general one.

## Three defects found in my own drafts

Recorded because the file preaches about controls that cannot fail:

* two tests I wrote asserted things that were true by construction —
  `assert ... or True`, and `assert inv.scan.__doc__`. Replaced with a real
  partition check and a temp-file scan that plants a malformed line and requires
  `clean is False`;
* the negative controls all ran through `scan_rows` (in memory, so no fixture
  holding a credential-shaped string is ever written into the tree), which left
  the **file reader itself** unexercised against an offender.
  `test_the_scanner_finds_a_planted_offender_on_disk` closes it under pytest's
  temp directory;
* `DECLARED_FIELDS` mixes two kinds of entry — fields exempted from tier 3
  because their *name* matches the pattern, and `request_headers`, which is
  declared because tier 1 governs it and whose name matches nothing. The test now
  asserts the partition, so a future entry that is neither is caught as a
  suppression rather than a statement.

## The other two resources — written, run, red, not landed

The item says 其余两处资源同法处理. Both are `monitor/`'s, and this item's
territory is `arc-recon`, so what is here is the executable check plus its
findings, filed to `monitor/inbox/` for a monitor-territory worker to land.
Landing is: move the file to `monitor/tools/`, add one line to monitor's green
light. Both carry their own red controls and exit 2 if the control does not fire,
so "the checker is broken" is distinguishable from "the machine is clean".

**Resource 2 — memory and concurrency. Red, right now.**

```
gate constants from monitor/reflex.py: WORKER_MAX=7 MIN_FREE_GB=8
agent processes: 24
free RAM: 6.01 GB
VIOLATION: live agent processes 24 exceed WORKER_MAX 7
VIOLATION: free RAM 6.0 GB is below MIN_FREE_GB 8
```

`reflex.py` counts `registry.json` entries and `schtasks`; terminal workers from
`monitor/worker.cmd` are in neither. The machine died once at about twenty
concurrent sessions. Two caveats I did not resolve and which the note repeats:
the count is image-name matching, so 24 is an upper bound on sessions rather
than an exact figure; and the RAM figure is one instant.

A small version of the same bug surfaced while writing it: the first probe used
`wmic`, which Windows 11 has removed, and it returned `None` silently. `judge()`
treats an unmeasured resource as **not clean**, so it printed
`UNMEASURED -- not a pass`. Had it treated a missing measurement as a passing
one, the report would have been green on a machine three times over its cap.

**Resource 3 — `board.log` against `claimed/`. Also red, and freshly so.**

```
LOG ONLY (moved out by hand): S1-quota-auto-exit, S5-phase1-close
DIVERGED
```

The proposal cited E2/E3; those were later closed by `SWEEP`. These are two
different items, diverging today, so the failure is ongoing rather than
historical. The two directions are reported separately because they mean
different things: `log_only` is bookkeeping lost, `disk_only` is an item held
with no `CLAIM` behind it — which is how two workers end up holding one
territory.

## Gaps

1. **The two `monitor/` checks are not wired to anything.** They run, they are
   red, and nothing fails because of them. Filed, not landed — territory.
2. **Tier 4 does not scan `response_body`.** A credential pasted into a response
   body by a future writer is caught only by tier 2, i.e. only when `.env` is
   readable and only for the API key — not for a session token. The alternative
   is a shape check over arbitrary game data, which would be noise. Stated, not
   solved.
3. **The process count is a proxy.** Matching image names is not the same as
   counting agent sessions.
4. **INC-008's values are still in git history** at `29c631e`, pushed, and the
   sessions were abandoned rather than revoked. Unchanged by this item and
   recorded in INC-008 as an owner decision; nothing here touches it.
5. **The seal has the usual hole**: I wrote the checks and the controls that
   grade them. No independent review this round.

## Reproduce

```bash
cd arc-recon
python -m pytest -q                          # 111 offline, no API, no network
python tools/ledger_invariants.py --all
bash verify.sh
python runs/20260728T150228Z-S10-invariant-on-resource/proposed/board_log_invariants.py
python runs/20260728T150228Z-S10-invariant-on-resource/proposed/concurrency_invariants.py
```
