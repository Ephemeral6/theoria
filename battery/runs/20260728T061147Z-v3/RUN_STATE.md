# RUN_STATE — V3-battery-discrimination

`MANIFEST.json` beside this file is canonical; this is the narrative.

**Branch** `agent/v3-battery-discrimination`, worktree
`C:/Users/user/Desktop/theoria-wt-v3b`, base `3205992` (master).
**Territory:** `battery/` only, plus one appended paragraph in
`PARTNER_SYNC.md`. Nothing outside `battery/` was written.

**Passive throughout:** zero API calls, zero model calls, zero network, zero
game spend, zero sealed-pile reads. The sealed-pile guardrail ran over all 192
paths of the new upstream payload before anything was parsed: 0 sealed hits,
all four development-pile games present, `piles.json` re-verified against its
published digest (`3feca53e…`, `cut_version v1`).

## What happened, in order

1. **Read the ground first, and found it had moved.** The prompt asked for
   `REPORT_V1`. That file already existed on master. Reading it turned up the
   finding this whole round is built on: v1 leads with *the Schema arm does not
   exist* and files it as gap one, but `SCHEMA_PATH_A.md` landed the upstream
   Schema trajectories at `63ef0bf` (02:53Z) — six hours **before** battery v1
   at `e82558b` (09:04Z), in the same tree. v1 conflated "we cannot run Schema"
   (true, permanent) with "we have no Schema trajectories" (false since that
   morning). D-B-019.

2. **Sealed the recon before predicting.** `REPORT_V1.md` made this item 1 for
   v2, because v1's surveys quoted values and every metric they fed is
   permanently `[seen]`. Two reconnaissance passes were commissioned under a
   written prohibition on scores, counts, durations, ranges and magnitude
   comparisons — field names, nesting paths, types and closed label sets only.

3. **Wrote the pre-registration before reading either report.** The 38-row
   directional table for CC vs Schema was written to disk in full, then
   committed (`19eafb2`), and only then were the recon reports read. So the
   author did not know, while writing it, which metrics the material could even
   be computed on — which makes it impossible to have quietly dropped the rows
   that were going to look bad. Two leaks are declared in the seal rather than
   left to be found (upstream scores are encoded in four directory names;
   `SCHEMA_PATH_A.md` §2.1 gives per-game file and byte counts).

4. **Built the Schema adapter.** 8 runs, 4 games × 2 upstream collections,
   median 450 steps against `bare_cc`'s 27. Four refusals are the substance of
   it — no invented turn axis, no synthesised cost, `failed` not derived from
   `dead`, `Theory` left `None` — each recorded in the module docstring with
   the reason the alternative would have been a fact-shaped guess.

5. **Ingested the S1 campaign** (56 more `bare_cc` runs) after establishing its
   exclusion premise had expired, and fixed a silent label drop: S1 labels
   itself `scenario` in `out/campaign/`, which `load_campaigns()` did not read.

6. **Ran the three processes.** Process 1 on the specified gradient (new),
   process 3 with per-family representatives (fixed defect), process 4 made
   executable by three independent adversarial audits.

7. **Verified determinism** and wrote the manifest.

## Results, one line each

* **Process 1 ran on the specified gradient for the first time.** 10 of 38
  metrics pair on ≥2 games, 8 rankable. Every verdict is `underpowered` — four
  paired games cannot reach p<0.05, unchanged since v0 — so only effect sizes
  should be read.
* **X3, the exploration family's signature, separates backwards** (|δ| = 0.562)
  and the wrong-direction warning fires automatically. The Schema arm's
  front-load index is *negative*.
* **P3 is the only metric in the battery that is both in the main table and
  validated on the specified gradient.** The validated set and the main-table
  set are very nearly disjoint.
* **Pre-registration: 7 strict hits of 18; 11 honouring the registered
  economy conditional.** Both reported. The structural prediction held exactly
  and the behavioural ones failed systematically in one direction — the author
  predicted the length confound would flatter `bare_cc`, and it flattered
  Schema on every metric.
* **The unvalidated count is unchanged at 21**, metric for metric, after adding
  an entire second control arm. This was the batch's headline prediction and it
  held: the blocker is a theory-bearing control arm, which no baseline supplies.
* **Process 3 retired 5 metrics** into per-family representatives, and 257 of
  703 pairs remain correlatable — the identical count as v1 after tripling the
  run count, because the un-comparability is structural.
* **Process 4 contradicted 17 register entries and demoted 13 metrics. Main
  table 19 → 6.** Including E2, a Phase 4 primary endpoint.

## Verification

```
python -m pytest battery/tests -q                 210 passed, 0 failed
python -m battery.run_battery                     95 runs, 5 arms, 1433 values
python -m battery.docs                            METRICS.md regenerated
```

Determinism: two consecutive recomputes to separate output directories, all
**7 artefacts byte-identical** by sha256. Digests in `MANIFEST.json`.

## Caveats a reader should carry

* **Arm and harness are bundled.** The Schema side is somebody else's agent on
  somebody else's infrastructure. Every effect size here is a capability
  gradient wearing a plumbing gradient's clothes, and P1/P5/E4 are visibly the
  plumbing. This is the gradient `Theoria.md` names; it is not a clean one.
* **Licence is unresolved.** Upstream declares none. The payload stays
  gitignored and only aggregate statistics enter any artefact (D-B-020).
  `SCHEMA_PATH_A.md` §7.1 flags that citing specific numbers may need a licence
  judgement — that judgement is not this track's to make and has **not** been
  made here; it is escalated in `PARTNER_SYNC.md`.
* **Untracked inputs.** `schema_traces/`, `out/shards/` and `out/campaign/` are
  outside git, so nothing pins them for a reader but the sha256 list in
  `MANIFEST.json`. They are also absent from every git worktree, which is why
  the two root-resolution environment variables exist.
* **`⟨复现值⟩` is still empty** and nothing here fills it.
