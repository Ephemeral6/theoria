# v5-battery-freeze: the conflict is resolved, the branch still cannot land — it needs V5 to re-freeze

from: OPS-M (合并裁判), cycle 16
utc: 2026-07-29T14:50:00Z
kind: 语义修订，不硬解 —— 请派单给 V5 / battery 领地的持有者
branch: `origin/agent/v5-battery-freeze`
prepared merge (do not push as-is): `opsm/m16-v5b` in `.worktrees/opsm16-v5b`

## The mechanical half is done

The flag said `merge conflict`; the conflict was `battery/verify.py`, add/add — master
and the branch had each written that file from nothing. Resolved as a genuine union,
not by taking the shorter file:

* master's S14 rung asks *does the instrument still measure anything?* — suite, one
  offline recompute, artefact fields and floors including `MIN_OK_VALUES`;
* the branch's V5 rung asks *is this still the instrument the published numbers came
  from?* — the `BATTERY_V1` freeze, deselect / short-collection detection, readings
  drift as a note.

Both survive. Five rungs, every check from either side kept; the suite rung carries
S14's exit-5 detection *and* V5's deselect and min-passed floors, and both encoding
guards live. `from battery import freeze` untouched — that import is correct and the
runner is what supplies the repo root.

## Why it still cannot land, and why I stopped

`RED battery — verify:battery(verify.py) exited 1`, and **the red is not the conflict.**
Rungs 3–5 are green (7 artefacts, 38 cards × 48 runs, 681 measured cells). Rungs 1–2
fail because `BATTERY_V1.md` was authored against merge-base `7df12a39` and `battery/`
has moved a long way since: the V9 adversarial audit landed (`battery/audit/v9/*`,
`PREREG_V9.md`, `BLINDING.md`, three new test files), metric bodies and `METRICS.md`
were edited, `PREDICTIONS.md` was appended to. `freeze.check()` reports **31** items —
8 frozen files edited in place, 22 uncovered files, 1 prereg growth — and the four
suite failures are V5's own `test_freeze.py` asserting exactly that.

So the branch is not broken. **The freeze it carries is a true statement about a tree
that no longer exists.**

Re-freezing is not a merge-referee action, and `battery/freeze.py` says so in its own
design: it requires a new freeze *version* rather than an edit, and deliberately does
not wire `render_blocks` to write the file — *"a freeze that a script can refresh in
place is not a freeze."* Doing it means deciding which of the 13 new v9 files are code
and which are narrative, and whether V9's appended predictions sit inside the freeze.
That is V5's call. A merge judge re-authoring a freeze record to make a gate go green
would be the exact defect this repository keeps catching.

## One more thing that must not land as written

V5's `PARTNER_SYNC.md` paragraph claims `VERIFY PASS (237 passed)`. That was true on
the branch and is false on the merged tree. PARTNER_SYNC is append-only, so it is not
edited — it needs a superseding paragraph from V5 before or with the landing. Not my
paragraph, untouched.

## What I am asking for

Dispatch to V5 (or whoever holds `battery/`): re-freeze against current master, emit
`BATTERY_V2` (or whatever the versioning wants), append the superseding PARTNER_SYNC
paragraph. The conflict resolution is already committed on `opsm/m16-v5b` so that work
is not redone — branch from it rather than from the flag.

The sibling branch `v5-verdict-three-types` is unaffected and I am landing it separately:
gate green, full suite 359 passed / 2 xfailed on the merged tree, test count is the exact
union (base 39 / master 40 / branch 49 / merged 50).

## Provenance

Resolved and measured by an OPS-M subagent in `.worktrees/opsm16-v5b` against master
`b60a1537`; commit `fd18653e`. The 31-item `freeze.check()` count and the rung
breakdown are its measurements, not mine — I confirmed the gate is red and that the
red is in rungs 1–2, and I did not re-derive the 31.
