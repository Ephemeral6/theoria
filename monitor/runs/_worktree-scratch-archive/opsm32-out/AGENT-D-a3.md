# OPS-M cycle 32 / agent D — `origin/agent/a3-campaign-devpile`: settling verdict X vs verdict Y

Status: **in progress** (gate runs launched 2026-07-30 ~20:39 local). Everything
below that is not marked PENDING is measured, not inferred.

## 0. Identities

| thing | sha |
|---|---|
| master HEAD (control arm) | `cc7e414eb3bfde3325a50f9ce0e8dc896bda2b84` |
| `origin/agent/a3-campaign-devpile` tip | `1e29578a58ce1dc398c5830b7be6f6e6b78dd03d` |
| merged arm HEAD | `1e29578a58ce1dc398c5830b7be6f6e6b78dd03d` |

No `git fetch` was run; these are the remote-tracking refs as they stood.

Worktrees (both `--detach` off `cc7e414e`):

* `.worktrees/opsm32-a3-ctl` — control, left at `cc7e414e`
* `.worktrees/opsm32-a3-mrg` — merged arm

## 1. Merge cleanliness — and a fact the brief did not have

`git merge --no-edit origin/agent/a3-campaign-devpile` in the merged arm:
**rc=0, no conflicts, and it FAST-FORWARDED.** HEAD became `1e29578a` exactly.

`git merge-base --is-ancestor cc7e414e 1e29578a` → true. a3's own tip is a
commit *"Merge remote-tracking branch 'origin/master' into
agent/a3-campaign-devpile"* dated 2026-07-30T19:36:04+08:00 — i.e. a3 has
already absorbed current master. So:

> **the merged arm's tree is byte-identical to the a3 branch tip.** There is no
> three-way merge content at all. ci_merge uses `git merge --no-ff`, which would
> add an empty merge commit over the same tree, so the *tree under test* is the
> same either way.

`git diff --stat cc7e414e HEAD`: **203 files changed, 109632 insertions(+), 256
deletions(-)**.
Touched top-level paths: `PARTNER_SYNC.md`, `monitor`, `theoria-arm`.

`sorted(dirs)` in Python is `["PARTNER_SYNC.md", "monitor", "theoria-arm"]`
(uppercase sorts before lowercase), and `ci_merge.try_merge` returns on the
first red. `PARTNER_SYNC.md` is not a directory → `kind=none` → skipped. So the
evaluation order is **monitor, then theoria-arm**, and a red monitor gate hides
whatever theoria-arm would have said. The brief's masking claim is confirmed
from the code, not from the log.

## 2. What the gate actually is for `theoria-arm` — the brief is wrong here

The brief says "for theoria-arm the gate is a pytest gate". It is not.

* `monitor/ci_merge.py:74 gate_for()` consults `TEST_CMDS`, which is **empty**
  (`TEST_CMDS = {}`, line 54), then delegates to `gates.gate_for(wt, d)`.
* `theoria-arm/verify.py` is **tracked and present at `cc7e414e`** and at the
  a3 tip (`git ls-files theoria-arm/verify.py` in both arms).
* `gates.find_gate` tries `CANONICAL = ("verify.sh", "verify.py")`, so
  theoria-arm resolves to `kind="verify"`, `name="verify.py"`,
  `cmd=[sys.executable, "<wt>/theoria-arm/verify.py"]`.

Consequence for the log: a red theoria-arm is flagged as
`"verify gate red in theoria-arm (verify.py)"`, not `"tests red in
theoria-arm"`. Verdict X's own text is consistent with this — it lists
"theoria-arm's verify red 05:25Z and 10:29Z" *separately* from "tests red in
theoria-arm 01:55–02:18Z", i.e. the gate kind changed during 2026-07-29 (S14,
commit `127edab9`, 2026-07-29T09:55:13+08:00 = 01:55Z, gave eleven territories a
`verify` gate). That is itself a change in the instrument mid-history.

My driver (`.worktrees/opsm32-out/agentD_arms.py`) replicates
`try_merge`'s invocation exactly — `gates.gate_for(wt, d)` for discovery,
`dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")` updated with
`gates.gate_env(wt)`, cwd `<wt>/<dir>`, timeout 1800, utf-8/replace decoding —
and then re-runs the directory's own suite with `-q -rf` to name every failing
id, because the gate truncates its detail to the last 2000–3000 chars.
It deliberately does **not** use `gates.run()`: that helper calls `gates.sh()`,
which passes **no `env` at all**, so it sets neither `PYTHONUTF8` nor
`PYTHONPATH=<root>` — a different invocation, and a candidate source of a
different verdict.

## 3. The four gate results

PENDING — running. (2 arms × 2 gates; outputs
`D-{ctl,mrg}-{arm,mon}.{json,gate.txt,pytest.txt}` in this directory.)

## 4. The Verdict-Y mechanism — real, but not as stated

Verdict Y claimed: *"four `MANIFEST.json` files pin stale shas of
`proxy/cost.py`, and a3's own cost-shape migration script rewrites exactly
those four."*

Measured:

* **There is no sha pin of `proxy/cost.py` anywhere.** I hashed
  `proxy/cost.py` at `cc7e414e` (`sha256
  d2d5878d508a360d04a2ccd1c35a64f341ad42982a6d269fac72a628e1692fe8`) and walked
  every `theoria-arm/**/MANIFEST.json` looking for a `files[]`/sha entry naming
  `cost.py`: **zero entries.** Nine manifests mention the string
  `proxy/cost.py`, all of them in *prose* inside
  `cost.cache_ttl_diagnosis.verdict`. The only sha in the cost block is the
  price table's (`pricing_v1`, `27ce4bb4…`), which has not moved.
* **The coupling is by output shape, not by sha.**
  `theoria-arm/tests/test_arm.py::test_the_archive_stays_accountable` calls
  `armtools.verify_provenance.run()` and asserts `not checks.failed` over 9
  checks. Check 8 is `_idempotence()`
  (`theoria-arm/armtools/verify_provenance.py:222`): for every archive-material
  run it re-derives the manifest via `backfill.amend_payload` / `backfill.build`
  and compares `backfill.render(payload)` against the bytes on disk. The
  re-derived `cost` block is produced by the *current* `proxy/cost.py`.
* **The commit that moved it is `71b882c8`**, "proxy: 'not measured' and
  'measured, and it was zero' were the same literal" (S29-measurement-missing-
  is-not-zero), committed **2026-07-30T02:06:10+08:00 = 2026-07-29T18:06:10Z**.
  It adds three keys to `price_run`'s output:
  `cost.from_price_table.unmeasured_calls`, `.missing_usage_keys`,
  `.unpriced_usage_keys`. Committed manifests predate them, so re-derivation
  produces three extra leaves and the byte comparison fails.
* **a3's migration rewrites seven runs, not four**, and
  `migration.json`'s own record says the diff is exactly those three keys
  (`"diff_is_exactly_the_three_s29_keys": true`, `leaves_changed: {}`,
  `leaves_removed: {}`, `ledger_unchanged: true`, `refused: []`). The seven:

  ```
  20260728T012311Z-g50t-first-contact-salvage
  20260728T012311Z-g50t-first-contact-salvage2
  20260728T014402Z-g50t-first-contact-salvage
  20260728T015354Z-g50t-first-contact-salvage
  20260729T004020Z-leg01
  20260729T004020Z-leg01-salvage
  preflight-20260728T012031Z
  ```

  Script: `theoria-arm/runs/20260730T0700Z-A3-COST-SHAPE-COUPLING/migrate_cost_shape.py`;
  record `migration.json`. A second script in the same run dir,
  `migrate_files_in_clone.py` / `migration_files.json`, migrates exactly one
  run: `20260729T004020Z-leg01`.

### Is it a genuine repair or a re-pin that will drift again?

It is a **re-pin**, and it is structurally the "committed artefact derived from
live code" pattern — but *not* the unconditionally-red variant.

* The manifests are committed bytes whose content is a pure function of tracked
  code (`proxy/cost.py`, `backfill.render`) plus each run's tracked ledger. So it
  is deterministic for a fixed tree — this gate is not clock- or
  network-dependent (see §6).
* But the coupling is unowned and cross-territory: **any future change to what
  `proxy/cost.py` emits turns `theoria-arm`'s gate red**, and it reds
  *theoria-arm*, not the `proxy` branch that caused it. That is exactly what
  happened here — a proxy-side commit put a red on an arm and thereby on every
  branch touching that arm. Migrating the seven manifests clears today's shape
  mismatch and does nothing about the next one.

## 5. Two of the seven were **added** by a3, and this is the crux

`20260729T004020Z-leg01` — the leg Verdict X names — **does not exist on master
at all.** `ls theoria-arm/runs/20260729T004020Z*` in the control arm: *No such
file or directory*. In the merged arm both `20260729T004020Z-leg01` and
`-leg01-salvage` are present, and `git diff --diff-filter=A` confirms a3 **adds**
18 `MANIFEST.json` files including those two.

So Verdict X was talking about a manifest a3 itself introduced: at the time,
a3's own new leg01 manifest drifted under re-derivation, master had no such run,
and the sign was genuinely **a3 GUILTY**.

## 6. Determinism of `test_the_archive_stays_accountable`

PENDING (two runs in the same arm; and an audit of what
`verify_provenance`/`backfill`/`armversion` read).

## 7. Resolution of X vs Y

PENDING pending §3, but the discriminating evidence is already on the table:
explanation **(i) master moved** — `71b882c8` landed at 2026-07-29T18:06Z,
*between* Verdict X (2026-07-29T16:01:59Z) and Verdict Y (2026-07-30T11:18Z) —
combined with **a3 moving too** (its 2026-07-30T07:00Z migration run).

## 8. What would falsify this

PENDING.
