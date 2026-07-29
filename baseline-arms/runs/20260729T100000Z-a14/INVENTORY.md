# A14 step 3 · everything under `baseline-arms/` that git was not holding

Swept in the main working tree (`C:\Users\user\Desktop\theoria`), which is the
only tree where the untracked payload exists.

```bash
git ls-files --others --exclude-standard baseline-arms/          # 12 files
git ls-files --others --ignored --exclude-standard baseline-arms/  # 206 files
```

**12 plain-untracked files = 63,993,495 B. 206 gitignored files = 88,247,208 B.**

## A. Plain untracked — all 12 now committed

| path (under `baseline-arms/`) | bytes | class | ruling | why |
|---|---:|---|---|---|
| `out/campaign/campaign_ar25.json` | 4,533 | cost-bearing rollup | **COMMIT** | battery pins its sha256; sole source for the bare-CC main-table column |
| `out/campaign/campaign_g50t.json` | 4,537 | cost-bearing rollup | **COMMIT** | as above |
| `out/campaign/campaign_sk48.json` | 4,535 | cost-bearing rollup | **COMMIT** | as above |
| `out/campaign/campaign_tn36.json` | 4,540 | cost-bearing rollup | **COMMIT** | as above |
| `out/shards/ledger.ar25.jsonl` | 6,267,799 | **cost-bearing, primary** | **COMMIT** | pinned by battery, `figures/SOURCES.sha256`, `battery/artifacts/capability_spectrum.json`, `proxy/runs/p9-shell-harden/migration_ar25.json` |
| `out/shards/ledger.g50t.jsonl` | 38,311,448 | **cost-bearing, primary** | **COMMIT** | same pins; the one genuine size call — see below |
| `out/shards/ledger.sk48.jsonl` | 6,919,008 | **cost-bearing, primary** | **COMMIT** | same pins |
| `out/shards/ledger.tn36.jsonl` | 3,636,837 | **cost-bearing, primary** | **COMMIT** | same pins |
| `out/shards/probe_log.ar25.jsonl` | 2,362,554 | cost-bearing, HTTP layer | **COMMIT** | `proxy/CANON_MIGRATION.md` §2 argues from it, and it is hashed nowhere — the weakest provenance link found in the sweep |
| `out/shards/probe_log.g50t.jsonl` | 2,669,737 | cost-bearing, HTTP layer | **COMMIT** | see the override note |
| `out/shards/probe_log.sk48.jsonl` | 1,935,799 | cost-bearing, HTTP layer | **COMMIT** | see the override note |
| `out/shards/probe_log.tn36.jsonl` | 1,872,168 | cost-bearing, HTTP layer | **COMMIT** | see the override note |

**Not regenerable.** `run_id` overlap between these four shard ledgers and the
tracked `baseline-arms/ledger.jsonl` is **empty**: the S1 campaign's 56
`run_id`s exist nowhere else in tracked git. And `campaign_*.json` is a
checkpoint mutated in place during the run (it carries `resumed_at`, and
`wall_seconds: null`), not a pure function of the ledger — the aggregates could
be recomputed, the exact bytes could not, and it is the exact bytes that are
pinned.

### The size question, answered with a measurement rather than a feeling

`ledger.g50t.jsonl` at 38.3 MB is ~5.9× the largest blob previously in this
repository, and it was the only entry in this inventory where COMMIT was not
obvious. It was settled by measuring rather than by taste: these files are
repetitive 64×64 integer grids and **gzip at 50–76×**.

| file | raw | gzip -6 | ratio |
|---|---:|---:|---:|
| `ledger.ar25.jsonl` | 6.1 MB | 80 KB | 75.9× |
| `ledger.g50t.jsonl` | 37.4 MB | 592 KB | 63.1× |
| `ledger.sk48.jsonl` | 6.8 MB | 99 KB | 68.2× |
| `ledger.tn36.jsonl` | 3.6 MB | 68 KB | 51.6× |

Observed pack growth for all twelve files: **72.56 MiB → 82.28 MiB**. Roughly
64 MB of working-tree payload for under 10 MiB of pack, most of which is the
probe logs. Size was not a reason to leave any of them out.

### Override: the three probe logs an independent sweep put at HASH-ONLY

The inventory sweep recommended COMMIT for `probe_log.ar25.jsonl` (it has a
consumer) and HASH-ONLY for the other three (they have none). All four are
committed here instead, for two reasons: the four are one campaign and splitting
the record across dispositions by who happens to cite it today makes the archive
answer a different question next year; and their `a7-*` counterparts for the
*later* campaign are already tracked, so hash-only for these three would leave
the same harness's output recorded two different ways. The cost of the override
is ~220 KB packed.

## B. Gitignored — 206 files, none committed, digests now recorded where they were not

| group | files | bytes | ruling | why |
|---|---:|---:|---|---|
| `schema_traces/**` | 165 | 87,667,651 | **LEAVE UNTRACKED, already hashed** | Third-party HF dataset with **no declared upstream licence**, and Phase 4 publishes every tracked file. `DECISIONS.md` D-013 made this call before A14 and it stands. The tracked `schema_traces/MANIFEST.json` already *is* the hash-only record: it names all 165 paths with per-file sha256, and an independent recompute of all 165 matched 165/165, 0 missing, 0 mismatched. Not duplicated into `COST_ARTEFACTS.json` — one register per fact. |
| `out/campaign/*.log` | 4 | 113,756 | **HASH-ONLY** (now in the register) | Console transcript of the paid campaign; the ledger it shadows is committed. |
| `out/*.log` (pilot + snapshot) | 8 | 24,958 | **HASH-ONLY** (now in the register) | Same class; their `out/pilot_*.json` outputs are tracked. Recorded so the rule is not applied to only some of the paid transcripts. |
| `harness/__pycache__/*.pyc` | 19 | 251,938 | LEAVE UNTRACKED | regenerable, free |
| `tests/__pycache__/*.pyc` | 6 | 181,290 | LEAVE UNTRACKED | regenerable, free |
| `.pytest_cache/` | 4 | 7,615 | LEAVE UNTRACKED | regenerable, free |

## C. Four findings this sweep turned up that are **not** A14's to fix

Reported to the monitor rather than acted on — three of the four live in other
territories, and the fourth is a working-tree condition on this machine.

1. **`figures/SOURCES.sha256:24-27` carries `ABSENT0000…` sentinels for exactly
   the four ledgers this commit tracks.** They were never really absent — they
   have been on disk since 2026-07-28 — but the figure builds ran inside
   `.worktrees/` checkouts where untracked payload does not exist, so the
   sentinel recorded "absent from the build's cwd". **This commit changes that
   for every checkout**, and `figures/sources.py`'s own note says a dropped-in
   file "is picked up automatically", so the next figure rebuild may silently
   change its inputs. This is the one consequence of A14 that reaches outside
   the territory, and it needs a `figures/` owner's decision.
2. **`release/MANIFEST.jsonl:148` pins a stale digest and size for
   `out/campaign_cells.jsonl`** (`dd967e98…`, 16,014 B; the file is now
   `ebe6396e…`, 26,765 B). Walking the history shows monotonic growth
   2191 → … → 26765, consistent with the append-only rule — so this is drift,
   not rewriting. But the Phase 4 *published-surface* manifest no longer
   describes what it would publish. `battery/runs/P-14/MANIFEST.json:33` pins
   the same file's very first 2,191-byte version.
3. **Six tracked `out/pilot_*.json` are CRLF on disk but LF in git.** `git
   status` calls them clean because it normalises on compare, but
   `figures/sources.py:722` and `release/enumerate.py:109` both hash **raw
   bytes** — so re-running either in this working tree emits CRLF digests and a
   spurious manifest diff. Same class of trap as the one A14 hit, one layer
   further out. A `git checkout --` re-materialisation would fix it; A14 did
   not do it because it touches tracked files outside this ticket's scope and
   other sessions are live in this tree.
4. **The `campaign_*.json` restart path drops spend** ($2.01 across the four —
   see `RECONCILIATION.md`). A harness defect, in this territory, but a code
   change rather than a rescue; recorded as a gap, not fixed here.
