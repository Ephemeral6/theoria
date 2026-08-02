# V29 — the paper's dual-proxy numbers become checkable

| | |
|---|---|
| prompt | **V29** · `one-proxy-validated-not-two` |
| worker | `W-9203` |
| branch | `agent/v29-one-proxy-validated-not-two` |
| base commit | `9e478dd8` |
| archive | `papers/runs/20260802T1152Z-V29-one-proxy-validated-not-two/` (`MANIFEST.json`) |
| tests | `papers/` suite **273 passed, 1 failed, 1 xfailed** (base: 247 passed, 1 failed, 1 xfailed) — the one failure is pre-existing and untouched |
| gate | `verify_paper` **FAIL (3/8)** — same three as the base's 3/7; the new check `H DUALPROXY` **passes** |
| cost | **$0.00** — zero API calls, zero model calls, zero network |

## Delivered: half the ticket, on purpose

`monitor/CHARTER.md:22-28` reserves `写论文正文` to RES-2 and grants `W-*`
`改代码 = 领到的领地内`. V29's territory is `papers`, so the ticket splits and
only one half is mine to write.

1. **`H DUALPROXY`, an eighth check in `papers/phase1-workshop/verify_paper.py`.**
   It recomputes the census live from `verify-lab/dualagent/count.py` and
   compares it against the dual-proxy numbers actually quoted in the manuscript.
   Today that is `sections/09_preflight.md:102-103` — "66 `bypass_attempt`
   incidents and 65 consecutive 401s" — which is split across a line break and
   wrapped in `**`, so the scanner flattens each section to one line while
   keeping a per-character source-line map. A per-line scan cannot see this
   claim at all.
2. **`test_dualproxy_gate.py`, 26 tests**, whose job is to prove the check can go
   red — V29's own words: *"一个抄下来就再也不会被核对的数字，和一个杜撰的数字在
   版面上没有区别."*
3. **The WP2 wording is NOT delivered.** It is RES-2's alone. The paste-ready
   text, corrected, went to
   `monitor/inbox/20260802T1200Z-W-9203-to-RES-2-the-v29-gate-is-built-and-S32s-numbers-have-moved.md`.

## The finding the ticket did not anticipate: two of its four numbers are stale

V29's acceptance names "三个分母（924/1009、65、66）". Re-running the instrument
today:

| | S32, 2026-07-31 | measured 2026-08-02 |
|---|---:|---:|
| env live / total / ledgers | 924 / 1009 / 24 | **2529 / 2620 / 37** |
| model calls / answered / `bypass_attempt` | 65 / 0 / 66 | **65 / 0 / 66** |

The environment figures rise every time any arm plays a leg; the model figures
cannot move until someone injects a funded provider key — which is precisely the
gap the paper is being asked to state. **The verdict (b) is unchanged and
strengthened**, but pasting S32's sentences verbatim would publish four numbers
that are no longer true.

**This is why the two sides are compared differently, and it is the part a
future editor is most likely to "fix" wrongly.** Model numbers are compared for
**equality**; environment numbers are compared as a **floor**, never equality. A
gate asserting `== 924` would go red the next time anyone played a leg — it
would punish the repository for doing its work, and be deleted within a week.
`verify-lab/dualagent/tests/test_count.py` had already made the same call for
the same reason. `test_the_monotone_direction_stays_green` exists solely to fail
if someone tightens the floor into an equality.

## Verified independently, not reported

Re-ran by hand rather than trusting the build:

```
unmutated                -> PASS
bypass_attempts = 999    -> FAIL      (the acceptance's negative sample)
a model call answered    -> FAIL
env live collapsed to 3  -> FAIL      (the overclaim direction)
instrument grew to 99999 -> PASS      (the monotone direction, must stay green)
```

A first attempt at this check reported PASS for every mutation. That was a bug in
the *checking script*, not the gate: `check_dualproxy()` returns
`(bool, list[str])`, and truth-testing the tuple is always true. Recorded because
a green result from a broken harness is exactly the failure mode this ticket
exists to prevent, and it nearly happened while verifying the thing that
prevents it.

## What this does not prove, stated plainly

* **It reads numbers, not sentences.** A section could quote both model numbers
  correctly and still claim both proxies are validated, and `H` would pass. What
  it makes impossible is a number that is un-recomputed, inflated, or quietly
  deleted. No check in this file reads English.
* **The three environment patterns have never fired on real prose** — no section
  quotes a denominator today, so they report as notes. A future sentence phrased
  outside the check's vocabulary would be *unread*, not failed. The note means
  "not found", not "not there".
* **It trusts the instrument.** If `count.py` counts the wrong thing, `H`
  confirms only that the paper agrees with it.
* **Space-grouped thousands are mis-read rather than skipped** (`9 000` reads as
  `0`), which on the floor side is too small to fail. Pinned by a test so the
  docstring cannot quietly become false.

## The gate was red before this branch and is red after it

`python papers/verify.py` at `9e478dd8`: **RED, 4 problems** — `case-studies: no
PAPER.md`, `related-work: no PAPER.md`, `verify_paper.py exited 1`, `pytest
exited 1`. After: **the same 4**, with `verify_paper` moving `FAIL (3/7)` →
`FAIL (3/8)` — same three checks failing (C FIGDATA, E UNCITED, F BARE), `H` a
new pass. Baseline archived verbatim as `baseline_verify.txt`, after as
`after_verify.txt`.

None of the four is fixed here. They are four defects with four causes and none
is V29. **The consequence for a reader: this gate's overall colour is not
evidence about this work** — only `H` and its 26 controls are, which is why they
are reported separately.

One forced edit worth disclosing: `test_gate_floor.py` hard-codes the set of
checks that read `sections/`, so adding `H` without adding it there would have
*created* a new failure. That file is a test, not prose.

## What is owed after this

* **The WP2 prose.** RES-2's, handed over with corrected numbers. Until it
  lands, `H` pins the two model numbers the body already carries and reports the
  three environment slots as unquoted.
* The four pre-existing `papers/` failures remain unowned by any cell.
