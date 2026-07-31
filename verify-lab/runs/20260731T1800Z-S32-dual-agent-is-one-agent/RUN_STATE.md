# S32 · 「双代理」这条主张，证据指向单代理 — run record

Board item: `monitor/board/claimed/S32-dual-agent-is-one-agent.W-1800.md`.
Verdict and the paper sentences: `verify-lab/DUAL_PROXY.md`.
Instrument: `verify-lab/dualagent/count.py` (+ `dualagent/tests/test_count.py`).

## What was measured

| | number |
|---|---:|
| environment proxy — legs written, all `forwarded: true` | 1009 |
| … of those, against the **live** endpoint (17 runs) | 924 |
| … of those, against a loopback fixture (7 runs) | 85 |
| live status split | 200×114, 400×726, 404×84 |
| model proxy — records in the archived probe file | 131 |
| … `model_call` | 65 |
| … `model_call` at 401 | 65 |
| … `model_call` at 2xx | **0** |
| … `bypass_attempt` incidents | 66 |
| model proxy against a **fixture** provider (untracked, see below) | 32 at 200 |
| named exclusions: `baseline-arms/ledger.jsonl` / `arc-recon` recon ledger | 656 / 1273 records, **0 proxy legs each** |

**Verdict (b)**: environment proxy built and validated on real traffic; model
proxy built, its boundary behaviour recorded, never validated on real traffic.
(c) was considered and refused with evidence — the chain is unfunded, not
broken: `proxy/model_proxy.py:176-181` records the bypass incident and does not
return, `_forward` injects `x-api-key` only when `cfg.api_key` is set, so all
65 requests reached the real upstream and the 401 came from the provider.

## Three things this run had to get right, and how

**The denominator is a choice, and the wrong choice flatters the claim.**
Counting *lines* in `theoria-arm/runs/*/ledger.jsonl` gives 3568 and would have
made the environment proxy look four times busier; counting every request log
in the tree adds 1929 records that never crossed a proxy at all. The census
counts only records carrying a proxy-written `http` leg, and the two big
exclusions are measured (`proxy_legs == 0`) rather than argued.

**A fixture upstream is not real traffic, and the ledger has no field that says
so.** There is no `mode` / `live` / `dry_run` key anywhere in the canon. The
only discriminator is `run_start.env_upstream`, which `proxy/canon.py` does not
register — so classification rests on an unregistered field, and that is this
finding's largest fragility. It is stated here rather than buried: the split is
by URL *scheme* (`https://` = real endpoint, `http://127.0.0.1:<port>` = fixture),
which is exact for every ledger in the tree today and keeps the game host out
of the source.

**The fixture evidence is gitignored.** `proxy/var/ledger.jsonl` holds the 32
completed model-proxy calls and lives under `proxy/.gitignore:3`, so
`census.json` (generated in this worktree) reports
`model_proxy_fixture.present: false`. That is "not on this checkout", not "the
model proxy never completed a request", and the distinction is pinned by
`test_negative_control_fixture_ledger_absence_is_declared`.
`fixture-snapshot.json` is the count taken from the main checkout, labelled as
such.

## Artefacts

* `census.json` — `python -m dualagent.count` run in this worktree.
* `fixture-snapshot.json` — the gitignored fixture ledger's counts, from the
  main checkout, with the provenance note inline.
* `pytest.stdout.txt` — the territory gate.

## Gate

`python -m pytest verify-lab -q` → **44 passed** on this branch;
**33 passed** on the master baseline (the 11 new are this cell's).
Zero API calls, zero spend, zero sealed-pile contact, no credential value in
any file written here.
