# `out/` is the 60-world smoke. It is not the campaign.

Every JSON file in this directory is a **60-worlds-per-engine smoke snapshot**,
left behind by whichever item last ran `python -m fuzzlab.campaign` without
`--out`. 360 worlds total, against the campaign's 3000.

| file | what it is | scale |
|---|---|---|
| `campaign.json` | smoke campaign summary | **60 worlds per engine, 360 total** |
| `seeds.jsonl` | its seed table | 360 rows |
| `findings.jsonl` | its findings | pre-V-21 rows, `cause` still inside `data` |
| `mutation.<engine>.json` | the mutation battery's catalogues | 40 worlds per mutant |

**The main result is elsewhere:**

```
../runs/20260729T104608Z-V21-lp-unavailable-is-not-a-pass/campaign/campaign.json
```

3000 worlds, 26 invariants, 0 violated, 0 raised, 1142 skipped, 0 unavailable,
seed `0x00005eedc1e4f002`.

## Why this file exists rather than a rename

The obvious fix for "a smoke file that looks like the main result" is to call it
`campaign.60w.smoke.json`. It is not available here. `engine-rig/tools/engine_table.py`
resolves three of the paper's numbers through the literal path
`fuzzlab/out/campaign.json`, and fuzzlab never modifies engine-rig — renaming
would repair this territory's honesty by breaking another territory's gate.

So the name stays and the scale is written down beside it, which is the weaker
half of the fix. The load-bearing half is in code: `fuzzlab/verify.py` gates on
the main result's world count, invariant count and seed, and
`fuzzlab/tests/test_main_result_scale.py` puts *this* `campaign.json` in the main
slot and asserts the gate goes red. That negative sample is the reason to
believe the gate can tell the two files apart at all.

Two of the three numbers engine-rig reads out of here — `rig.campaign_worlds`
(`60`) and `rig.campaign_violations` (`0`) — are this smoke's numbers occupying
the paper table's campaign row. That is engine-rig's call to make; it was
reported, not edited, in
`monitor/inbox/20260731T000000Z-V26-engine-table-campaign-row-is-the-smoke.md`.
