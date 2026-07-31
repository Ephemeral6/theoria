# V-26 · the README pointed at the smoke run

**The finding was never that a number was wrong.** Every number fuzzlab has
published is correct, and the recompute below reproduces the headline result
field for field. The finding is that `README.md` sent a reader to
`out/campaign.json` to check a 3000-world claim, and `out/campaign.json` is a
360-world smoke that reports `violated: 0` exactly as convincingly. The reader
checks. The check passes. What was checked is fifty times smaller than what was
claimed — and a green that arrives whether or not the claim holds is not
evidence about the claim.

## 1 · The recompute

`python -m fuzzlab.campaign --worlds 500`, 2026-07-31, engine-rig `6fabcc7e`,
output in `recompute/` (`campaign.json`, `seeds.jsonl`, `findings.jsonl`) with
raw stdout in `recompute.stdout.txt`.

| quantity | recompute |
|---|---|
| worlds | **3000** (500 × 6 engines) |
| invariants | **26** |
| violated | **0** |
| raised | **0** |
| skipped | **1142** |
| unavailable | **0** |
| generator errors | **0** |
| campaign seed | `0x00005eedc1e4f002` |

Against
`runs/20260729T104608Z-V21-lp-unavailable-is-not-a-pass/campaign/campaign.json`
the two documents are **identical in every field except `elapsed_s` and
`engine_rig_head`**, per-invariant coverage included. The published numbers were
measured at engine-rig `68a8365` (V-13) and `863e899d` (V-21); they hold at
`6fabcc7e`, which is a stronger claim than either originally made.

Per-engine, from the recompute's own stdout: `mdl_segmenter` 4 inv / 0 skipped,
`cegis_miner` 6 inv / 210 skipped, `zero_space` 4 inv / 0, `lp_potential` 4 inv /
932, `fd_adapter` 3 inv / 0, `probe_frontier` 5 inv / 0. Every skip carries a
declared cause and `unavailable` is 0 across all six.

## 2 · Which run is the main result — and the answer is not the one the item named

The item named
`runs/20260728T161127Z-V13-audit-the-published-surface/partials/campaign.500w.json`.
That file is the same 3000 worlds, the same seed and the same totals, but under
the **pre-V-21 schema**: no `skips_by_cause`, no `unavailable`. Resolved toward
the recompute, which is V-21-schema: the main result is

```
runs/20260729T104608Z-V21-lp-unavailable-is-not-a-pass/campaign/campaign.json
```

and the V-13 partial is superseded. The gate rejects the V-13 partial on purpose
(`test_a_pre_v21_artifact_of_the_right_size_still_goes_red`): **absent is not
zero.** A schema with no column for the worlds a *tool* failed on cannot testify
that there were none, and 3000 worlds of unknown instrument health is not the
claim the papers make.

## 3 · Every place the numbers are quoted, and what happened to it

| where | said | disposition |
|---|---|---|
| `README.md` header | pointed at `out/campaign.json` for the raw campaign | **fixed** — a new first section names the V-21 artifact, its numbers, and the smoke's scale |
| `README.md` `out/` caveat | "predates V-21", scale unstated | **fixed** — scale stated, `out/README.md` added |
| `BUGS.md` headline (E-4/V-10) | 23 invariants, 80 skipped | already superseded by § V-13; left as written per append-only, second pointer added in the new § V-26 |
| `BUGS.md` § V-13 supersede | 26 / 3000 / 1142 | **confirmed by recompute**, no change |
| `MUTATION.md` line 3 | "23 invariants" | quoting the E-4 headline; supersede note appended at the foot rather than editing the line |
| `RUN_STATE.md` (fuzzlab root) | 3000 worlds, 80 skipped | the E-4 milestone record; superseded by BUGS § V-13, left as written |
| `engine-rig/ENGINE_TABLE.md` `rig.campaign_worlds` = **60** | the smoke's scale in the paper table's campaign row | **not ours** — reported to engine-rig via `monitor/inbox/` |
| `engine-rig/ENGINE_TABLE.md` `rig.campaign_violations` = 0 | true of both files, earned over 360 | same report |
| `engine-rig/ENGINE_TABLE.md` `ic3.fuzz_engines` = 0 | true at either scale — `ic3_pdr` has no property module | flagged, no defect |

`papers/phase1-workshop/PAPER.md` quotes **no** fuzzlab campaign number directly;
the paper reaches these numbers through `ENGINE_TABLE.md`, which is the surface
that drifted.

## 4 · The rename that could not happen, and what replaced it

The item asked for `campaign.60w.smoke.json` or equivalent, so the smoke stops
looking like a main result. Blocked: `engine-rig/tools/engine_table.py:529,532,533`
resolves three paper numbers through the literal path
`fuzzlab/out/campaign.json`, and **fuzzlab never modifies engine-rig**. Renaming
would repair this territory's honesty by breaking another territory's gate.

So the annotation route the item offers as the alternative was taken —
`out/README.md`, naming the scale in a table and naming the real artifact — and
the enforcement went where it cannot drift.

## 5 · The gate, and the negative sample that makes it worth having

`verify.py` grew a fourth check. It reads the artifact fuzzlab publishes as the
main result and goes **red** when `worlds_per_engine`, `totals.worlds_checked`,
`totals.invariants` or `campaign_seed` falls short of the documented claim, or
when `totals.unavailable` is absent or non-zero. The path is
`FUZZLAB_MAIN_RESULT`-overridable, which is how the negative control reaches it.

**A violation still does not make it red.** 失败是战利品 — findings are the
campaign's product, and this gate is about scale and provenance, not about the
reading. `test_a_violation_does_not_make_the_gate_red` pins that: a fabricated
artifact carrying `violated: 7` passes.

Controls, all in `tests/test_main_result_scale.py`:

| control | asserts |
|---|---|
| the unmodified 60-world `out/campaign.json` in the main slot | **red**, naming `worlds_per_engine is 60` and `worlds_checked is 360` |
| the same via `FUZZLAB_MAIN_RESULT` | **red** by the route the command line resolves |
| the V-13 3000-world artifact (pre-V-21 schema) | **red** on `unavailable`, *not* on scale |
| 3 engines / 1500 worlds | **red** on both counts |
| right size, wrong seed | **red** on `campaign_seed` |
| right size, 7 violations | **green** |
| the constants vs. the prose | `README.md` and `BUGS.md` must quote 3000 and the seed, so the gate cannot be made green by lowering the claim |

At the command line, `FUZZLAB_MAIN_RESULT=fuzzlab/out/campaign.json
python -m fuzzlab.verify` exits **1** — captured verbatim in
`negative-control-smoke-in-main-slot.txt`. The unmodified gate exits **0** —
`verify.txt`.

## 6 · `figures/SOURCES.sha256` — the null result, written down

Asked whether any drifted entry points at a fuzzlab artifact. **No — the file
contains zero fuzzlab entries.** 68 sources: `baseline-arms` 24, `theoria-arm`
14, `cold-start-a2` 12, `cold-start-a3` 7, `battery` 5, `cold-start-a0` 5,
`papers` 1.

Recomputed all 68: **62 match, 6 drifted, 0 missing** — the audit's 13 is down to
6, consistent with V-23 regenerating the manifest on 2026-07-31. All six are
`baseline-arms/out/pilot_*.json`, and it is **not a line-ending artefact**:
`git show HEAD:<path>` hashes to the same value as the working tree, so the
committed bytes disagree with the manifest. Reported to the V-23 holder in
`monitor/inbox/20260731T000000Z-V26-engine-table-campaign-row-is-the-smoke.md`
part 2; `figures/` was not touched. Script and raw output: `sources_audit.py`,
`sources_audit.txt`.

## 7 · Gates

| gate | result |
|---|---|
| `cd fuzzlab && python -m pytest -q` | **140 passed** (131 before; 9 new) |
| `python -m fuzzlab.verify` | **green**, exit 0 — all three stages ok plus the new main-result check |
| negative control | exit **1**, `FAILED: published main result is not at the claimed scale` |

`out/` is restored to its committed bytes after every run — `verify.py` stage 2
writes there by design, and those bytes are an input to another territory's
gate, so they are left exactly as they were found.

## 8 · Scope

No file outside `fuzzlab/` was modified. The two cross-territory findings
(engine-rig's table, `figures/SOURCES.sha256`) went to `monitor/inbox/` as a new
file. Zero API calls, zero spend, zero sealed-pile contact — no sealed game id
appears in anything written here. No credential value anywhere.
