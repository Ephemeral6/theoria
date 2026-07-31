# P-12 · 复放抽检 ⟨2⟩ 局, third harness

Territory: `proxy`. Offline throughout — zero API calls, zero model calls,
zero dollars. Every number here was read out of ledgers that already existed.
Development-pile ids only (`g50t-5849a774`, `sk48-d8078629`); no sealed-pile id
appears anywhere in this run.

## What the ticket said, and what was actually there

The ticket said only game 1 (`ar25`) had ever been spot-checked. That was
stale: `proxy/runs/20260731T154336Z-P1-replay-spotcheck-2` already carries a
`g50t-5849a774` check — 26 sessions from four `baseline-arms` shards, 6
positions, 971 pairwise comparisons, zero disagreements. Game 2 was done.

What had *not* been done, and what this run is: the four live `theoria-arm`
legs of 2026-07-31 are a **third harness** on the same games, and
`replay_spotcheck.py` could not read them at all.

## The finding: silence, not a wrong answer

Pointed at the three g50t legs, the tool on `master` returns:

```
"verdict": "INSUFFICIENT",
"detail": "0 session(s) with a failure-free opening; agreement needs at least two",
"sessions": []
```

Zero sessions out of 393 `env_step` rows. Not a disagreement, not an error —
an empty result, which reads exactly like "these ledgers contain nothing".

The cause is a shape the ar25 and baseline sources never had. The arm records
a **refused** command as its own `env_step` at its own `step_idx` and retries
under the next one. Every refusal in all four legs is the same single shape:

```
400  {"error": "SERVER_ERROR", "message": "game <id> not found"}   frames: null, n_frames: 0
```

and there are a lot of them — **494 of the 570 live steps, 87%**. Step 0 is a
refusal in every leg, so "truncate at the first failed step" truncates at the
first step.

| leg | steps | with a frame | refused |
|---|---|---|---|
| `20260731T1240Z-A3-level2-carried` (g50t) | 60 | 6 | 54 |
| `20260731T1310Z-A3-level2-carried-r2` (g50t) | 99 | 14 | 85 |
| `20260731T1430Z-A3-level2-carried-r3` (g50t) | 234 | 34 | 200 |
| `20260731T1500Z-A3-sk48-carried-l1` (sk48) | 177 | 22 | 155 |

## The rule added, and why it cannot manufacture a pass

`--compact-refusals`: a refusal that **provably executed nothing** is not a
step. One shape qualifies (`non_executing_refusal`), it is a closed whitelist,
and anything outside it truncates exactly as before. Two independent witnesses
say nothing ran: no frame came back with `n_frames: 0`, and a failed attempt
is not charged against the scorecard (`total_actions` counts successful
actions only — baseline-arms' four-sample measurement, PARTNER_SYNC
2026-07-28).

The residual risk points the safe way. If a refusal *did* secretly execute,
then two sessions that met different numbers of them have different histories,
and comparing them position by position yields a **disagreement** — a FAIL,
not a false PASS. Compaction can manufacture alarm; it cannot manufacture
agreement. Two guards are unchanged: every position still requires the same
command name in every session, and contiguity is still checked over the **raw**
`step_idx` counter, so a dropped row must be paid for by a refusal at that
exact index and a genuine hole still truncates.

The strict path emits byte-identical output to before — the `policy` and
`session_origin` blocks appear only under the flag. The archived ar25 and g50t
reports are hashed in their manifests; a provenance record you can no longer
reproduce is one you have to take on trust.

## Result 1 — the three live g50t legs agree, byte for byte

`replay_spotcheck_g50t_arm.json`: **PASS**, 3 sessions, 10 positions, 22
pairwise comparisons, **zero disagreements**, 339 refusals compacted. Three
independent live legs launched at 12:40, 13:10 and 14:30 UTC.

`replay_spotcheck_g50t_arm_strict.json` is the same three legs read strictly —
`INSUFFICIENT`, archived so the before/after is on disk rather than in prose.

## Result 2 — and they agree with the other harness too

`crosscheck_arm_vs_baseline.json` (`crosscheck_baseline.py`): **PASS**, 6
overlapping positions, zero disagreements. The arm's live legs land on the
*same frame hashes* the `baseline-arms` campaign recorded through a completely
different harness:

| pos | action | baseline sessions | arm legs | frame hash |
|---|---|---|---|---|
| 0 | RESET | 26 | 3 | `sha256:801726dc…c298fba7` |
| 1 | ACTION1 | 22 | 3 | `sha256:801726dc…c298fba7` |
| 2 | ACTION2 | 21 | 3 | `sha256:e665977d…a4a97dc7` |
| 3 | ACTION3 | 14 | 3 | `sha256:0752f8b0…6fdc9cd4` |
| 4 | ACTION4 | 13 | 3 | `sha256:5cc8add0…78981257` |
| 5 | ACTION5 | 9 | 3 | `sha256:dd5deaac…7905a250` |

The arm ran 4 positions further than the baseline sweep's fixed opening; those
are evidence the arm side carries alone, and are counted separately rather
than folded in.

This compares two archived reports rather than re-deriving the union, and the
reason is on purpose: the baseline half's inputs are four 37 MB shards lifted
into ~33 MB of canonical ledgers that were never archived. Comparing the
reports keeps the finding reproducible from two small tracked files.

## sk48

`replay_spotcheck_sk48_arm.json`: **INSUFFICIENT** — one leg, and one session
agreeing with itself is not evidence. Archived rather than omitted, because an
absent file and a negative result are not the same thing.

## Gates

```
cd proxy && python -m pytest -q   →  450 passed  (426 before; +24)
```

One pre-existing test moved with the code: `test_migration.py::
test_a_session_is_truncated_at_a_step_idx_hole` unpacks `clean_prefix`'s
return, which is now `(prefix, refusals_compacted)`. The contiguity rule it
pins is unchanged and it still asserts the same three hashes.

`proxy/tests/test_replay_spotcheck.py` is new: the tool shipped with P-9
carrying no tests at all, run once by hand with its output treated as the
evidence. It now pins the closed whitelist (7 near-miss mutations that must
*not* compact), the raw-index contiguity rule, the negative control that
compaction does not hide a disagreement, the strict path's key set against all
three archived reports, and the three live legs end to end.

## Residual gaps, stated plainly

* **This is still not a replay.** Nothing here shows *our* proxies can
  reproduce a run; it shows the environment is deterministic across three
  harnesses. A live replay through `proxy/replay.py` costs actions and is
  still owed — the same caveat P-9 wrote and it has not moved.
* **The whitelist has one entry.** The next harness with a different refusal
  shape gets `INSUFFICIENT` again, correctly but silently. A refusal-shape
  census across all ledgers would turn that into a warning; not done.
* **87% refusal rate on live legs is not my finding to fix.** The arm's own
  territory owns why `game <id> not found` came back 494 times, and whether a
  retry loop that burns 234 step indices for 34 frames is the intended
  behaviour. Reported to the inbox, not diagnosed here.
* **The cross-harness check is a two-report comparison**, not a single union
  run over 29 sessions. Equivalent for the overlapping prefix; it does not
  produce a combined pairwise count, so no such number is claimed.
