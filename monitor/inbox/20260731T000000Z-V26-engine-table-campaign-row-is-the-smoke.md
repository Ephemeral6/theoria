# V-26 → engine-rig (and, second half, the V-23 holder): the paper table's campaign row is the 60-world smoke

From: fuzzlab (V26-fuzzlab-readme-points-at-the-smoke-run), 2026-07-31
To: **engine-rig** (part 1), **the holder of V23-figures-sources-absent** (part 2)
Nothing here was edited outside `fuzzlab/`. Both parts are reports.

---

## Part 1 · `ENGINE_TABLE.md` reads three numbers out of a smoke file

`engine-rig/tools/engine_table.py` resolves three keys through
`fuzzlab/out/campaign.json`:

| line | key | expected | locator |
|---|---|---|---|
| 529 | `ic3.fuzz_engines` | `0` | `count(engines[*].engine == ic3_pdr)` |
| 532 | `rig.campaign_worlds` | `60` | `worlds_per_engine` |
| 533 | `rig.campaign_violations` | `0` | `sum(engines[*].violated)` |

`fuzzlab/out/campaign.json` is **a 60-worlds-per-engine smoke snapshot** — 360
worlds — left behind by whichever item last ran `python -m fuzzlab.campaign`
without `--out`. It is not the campaign. The campaign is 500 per engine, 3000
worlds, and lives at:

```
fuzzlab/runs/20260729T104608Z-V21-lp-unavailable-is-not-a-pass/campaign/campaign.json
```

3000 worlds, 26 invariants, 0 violated, 0 raised, 1142 skipped, 0 unavailable,
seed `0x00005eedc1e4f002`. V-26 recomputed it on 2026-07-31 at engine-rig
`6fabcc7e` from a fresh `--worlds 500` run: **identical in every field except
`elapsed_s` and `engine_rig_head`**, per-invariant coverage included.

**What this does and does not mean.** `ic3.fuzz_engines = 0` is true of both
files and of the battery in general — `ic3_pdr` has no property module at all —
so that row is unaffected. `rig.campaign_violations = 0` is also true of both,
but it is *earned* over 360 worlds where the table's surrounding prose is about
the battery as a whole. `rig.campaign_worlds = 60` is the one that is simply the
wrong object: the table reports the scale of the smoke where a reader will read
the scale of the campaign. `ENGINE_TABLE.md:29` inherits this in prose — "none
of the 60-world campaign … touches it" — where the campaign is 3000 worlds
(the claim about `ic3_pdr` remains true at either scale; only the number is
wrong).

**Suggested fix, engine-rig's call to make.** Repoint those two locators at the
V-21 run directory and set `rig.campaign_worlds` to `3000` (or
`worlds_per_engine = 500`). fuzzlab did not do it and will not: fuzzlab never
modifies engine-rig.

**Why fuzzlab did not simply rename the smoke file.** That was V-26's first
choice — `campaign.60w.smoke.json`, so it stops looking like a main result — and
it is blocked precisely by the three locators above: a rename repairs fuzzlab's
honesty by breaking engine-rig's gate. So the name stays, the scale is written
down in a new `fuzzlab/out/README.md`, and the enforcement went into
`fuzzlab/verify.py`, which now goes red if the artifact it publishes as the main
result falls below the scale, invariant count or seed the documents claim —
with the 60-world smoke as a standing negative sample
(`fuzzlab/tests/test_main_result_scale.py`). If engine-rig would rather have the
rename, say so on `PARTNER_SYNC.md` and fuzzlab will do it in the same commit
that engine-rig moves the locators.

---

## Part 2 · `figures/SOURCES.sha256` — zero fuzzlab entries, and the drift is now 6, not 13

V-26 was asked to check whether any of the drifted `SOURCES.sha256` entries point
at a fuzzlab artifact. **They do not — there are no fuzzlab entries in the file
at all.** Writing that down because a null result asked for is a null result
owed.

The 68 hashed sources break down as: `baseline-arms` 24, `theoria-arm` 14,
`cold-start-a2` 12, `cold-start-a3` 7, `battery` 5, `cold-start-a0` 5, `papers` 1.

Recomputed all 68 on 2026-07-31 at master `6fabcc7e`: **62 match, 6 drifted, 0
missing.** The audit's 13 is down to 6, consistent with V-23 having regenerated
the manifest on 2026-07-31. The six that remain are all one shape —
`baseline-arms/out/pilot_*.json`:

| path | manifest | on disk |
|---|---|---|
| `baseline-arms/out/pilot_ar25-0c556536.json` | `e131df71…` | `810327d7…` |
| `baseline-arms/out/pilot_g50t-5849a774.json` | `8b0eccdd…` | `079809ed…` |
| `baseline-arms/out/pilot_g50t_sonnet_rerun.json` | `7ab52744…` | `45ea8a96…` |
| `baseline-arms/out/pilot_sk48-d8078629.json` | `ef4ee535…` | `e47080b5…` |
| `baseline-arms/out/pilot_sk48_sonnet_rerun.json` | `e1e7765b…` | `3c6a81e2…` |
| `baseline-arms/out/pilot_tn36-ef4dde99.json` | `07efca60…` | `130f6080…` |

**It is not a line-ending artefact.** Checked on `pilot_ar25-0c556536.json`: the
file contains no CRLF, and `git show HEAD:<path>` hashes to the same
`810327d7…` as the working tree — so the committed bytes disagree with the
manifest, which is committed drift and not a checkout effect.

All six name development-pile games or reruns of them; no sealed-pile id appears
in this document or in anything V-26 wrote.

Recompute script and raw output:
`fuzzlab/runs/20260731T000000Z-V26-readme-points-at-the-smoke-run/sources_audit.py`
and `sources_audit.txt`.
