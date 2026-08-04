# CONFLICT-origin_master.md
branch: origin/master
reason: BASE RED in freeze (verify.sh): origin/master fails this gate on its own
tip: cf4a8c4fc137d72d10400f43d7113c2518135809
base: cf4a8c4fc137d72d10400f43d7113c2518135809
first_seen: 2026-08-04T12:39:01Z
last_seen: 2026-08-04T12:39:01Z
attempts: 1

```
--- cause lines (lifted out of the transcript) ---
[31m  FAIL  MANIFEST.json has drifted from the tree -- regenerate and read the diff[0m
[31m  FAIL  BUDGET_TABLE.{json,md} no longer recompute from the ledgers -- regenerate and read the diff[0m
[31m  FAIL  tracked artefacts name a machine without an exemption:[0m
--- tail of the transcript ---
file(s) record an absolute path and this run directory is not in the dated allowlist
          run       theoria-arm/runs/2026-08-01T045542Z-A18                  1 file(s) record an absolute path and this run directory is not in the dated allowlist
          run       theoria-arm/runs/20260801T001851Z-R1b-g50t-a             23 file(s) record an absolute path and this run directory is not in the dated allowlist
          run       theoria-arm/runs/20260801T001851Z-R1b-sk48-b             7 file(s) record an absolute path and this run directory is not in the dated allowlist
          run       theoria-arm/runs/20260801T043743Z-R2-g50t-a              5 file(s) record an absolute path and this run directory is not in the dated allowlist
          run       theoria-arm/runs/20260801T043743Z-R2-sk48-b              5 file(s) record an absolute path and this run directory is not in the dated allowlist
          run       theoria-arm/runs/20260801T044640Z-R2b-g50t-a             16 file(s) record an absolute path and this run directory is not in the dated allowlist
          run       theoria-arm/runs/20260801T044640Z-R2b-sk48-b             7 file(s) record an absolute path and this run directory is not in the dated allowlist
        
        An artefact violation is fixed at the generator, then regenerated -- generated files are never hand-edited. A run violation is fixed either by fixing whatever wrote the path (if the run is still being produced) or by adding a dated entry to tools/locations_allowlist.json saying why this write-once record is allowed to name a machine. Deleting the pattern from a captured log is not one of the options: it falsifies a third party's output.

[19] the §3.0 withdrawal of the front-load endpoint is intact, at its price
[32m  PASS  e2_withdrawal.py --verify: the §3.0 withdrawal is stated in both files, the Holm divisor is still 3, all three C2 blocks carry the identity sentence, §8 carries no exception, and the surviving axis defect is disclosed[0m
[32m  PASS  e2_withdrawal.py --selftest: 8/8 controls, every one demonstrated to fire[0m

[20] the freeze manifest tells the truth about the money
[32m  PASS  MANIFEST.json publishes the balance and holds on it: OVER CEILING: remaining_measured_usd = -157.0131 against a 214.9 ceiling; items held: [12][0m
[32m  PASS  build_manifest.py --selftest: 8/8 budget-hold controls, including the two that must NOT fire[0m

==============================================================
[31m DRAFT INCOMPLETE -- 3 check(s) failed[0m
==============================================================

```
