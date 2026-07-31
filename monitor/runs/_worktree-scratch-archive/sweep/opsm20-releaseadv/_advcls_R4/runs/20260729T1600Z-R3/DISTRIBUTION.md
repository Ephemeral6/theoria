# R3-release-classifier-defaults — the classification, before and after

`prompt_id: R3-release-classifier-defaults`, branch `agent/r3-release-classifier-defaults`,
base commit `7852ef305bc7c12254a9f15e9362db79b9813529`.

The finding this run measures: **in the release enumerator, every default pointed
at "publishable".** Unreadable, unrecognised and uncomputable all fell through to
class A / `releasable`. `release/MANIFEST.jsonl` is the document a release is
assembled from, so the permissive default is not a rough edge — it is the failure
mode.

Two of the three defects are fixed here (defect 2 was not in this work order).
Both changes are in `release/enumerate.py`; `release/check_redlines.py` was not
touched.

## The numbers

5,980 tracked files, enumerated three times. `snapshot.py` in this directory
produces each one; it calls `enumerate.build()` directly rather than
`enumerate.main()`, because `main()` gates the whole enumeration behind the red
lines and this is a census, not a manifest.

| class | verdict | before | after | Δ |
|---|---|---:|---:|---:|
| A | releasable | 5671 | 5671 | 0 |
| B | needs-written-permission | 61 | 61 | 0 |
| C | releasable-flagged | 247 | **244** | **−3** |
| D | not-releasable | 1 | 1 | 0 |
| ? | needs_human | **0** | **3** | **+3** |
| | **total** | 5980 | 5980 | |

Bytes: A 132.55 MB, B 95.16 MB, C 13.48 MB, D 0.04 MB, ? 0.52 MB (after).

The visible diff is small and it is entirely defect 3. Defect 1 is a *latent*
default: `arc-recon/data/piles.json` currently has the `strata` key the reader
asks for, so the id list loads and today's classification is unaffected. Its
impact is measured below as a counterfactual, which is the only way to measure a
default that has not yet fired.

## Defect 1 — the id list that could load empty, measured counterfactually

`release/enumerate.py:123` read the cut through `.get("strata", {})`. A missing
or renamed key is swallowed into an empty dict; a comprehension over an empty
dict is a perfectly legal empty list; and `classify` then finds no ARC game id in
any file and returns **class A / releasable** for every one, with the evidence
string *"no ARC game id appears in this file"* — a positive claim about a
comparison that never happened.

`defect1_counterfactual.jsonl` is the full enumeration with the id list forced
empty, against the **unfixed** enumerator (`git show HEAD:release/enumerate.py`):

| | A | B | C | D | ? |
|---|---:|---:|---:|---:|---:|
| before (id list loads) | 5671 | 61 | 247 | 1 | 0 |
| id list empty | **5955** | 24 | **0** | 1 | 0 |

**284 files move into class A: 37 from B and 247 from C.** That is 92,599,886
bytes (92.6 MB) of material moving into the class that ships, of which the 37
class-B files are the api-derived compilations `LICENCE_POSTURE.md` says need
written permission. The full list is in `MOVED.tsv`, tagged `defect-1`.

> The board item quotes **33 B→A and 223 C→A**. Measured here on this tree at
> base `7852ef3`: **37 and 247**. The item's figures were taken against a smaller
> tree; nothing about the mechanism differs. The larger number is reported rather
> than the quoted one.

The 37 that move B → A:

* `arc-recon/cascade/runs/2026-07-28T034709Z-p20/` — 8 files (`steps.*.jsonl`,
  `summary.*.json`, all four dev-pile games)
* `arc-recon/cascade/runs/2026-07-28T034709Z-p20-followup/` — 2 files
* `arc-recon/data/precheck.json`
* `baseline-arms/ledger.jsonl` and 15 `baseline-arms/out/shards/ledger.*.jsonl`
* `battery/tests/fixtures/ledger_fixture.jsonl` (the one already flagged as
  probably synthetic and held at B on purpose)
* `theoria-arm/runs/*/ledger.jsonl` — 8 files, plus
  `theoria-arm/runs/preflight-20260728T012057Z/run.json`

The 247 that move C → A, by top directory: theoria-arm 52, baseline-arms 39,
proxy 31, arc-recon 30, battery 20, figures 17, monitor 17, release 12, exam 9,
papers 6, freeze 4, verify-lab 4, ablation-arm 2, browser-ops 1, fleet-study 1,
`CLAUDE.md`, `PARTNER_SYNC.md`.

**The fix refuses.** `_arc_game_ids` now raises `PileCutUnreadable` when the cut
file is not the shape it expects — cross-checking the `strata` partition against
the `dev_pile` / `sealed_pile` partition, by set and not only by count, and
refusing outright if either pile is empty. `check_redlines.check_sealed` has
carried this guard since the day it "scanned 2817 files with an empty id list and
then printed `Both red lines clear`"; the guard went into one of the two id
readers and not the other. It is now in both.

## Defect 3 — the licence class that depended on the file's name

`release/enumerate.py:160`, and the same suffix gate one branch earlier at `:146`.
The enumerator asked `rel.endswith((".json", ".jsonl"))` while
`check_redlines.json_shaped` had been written to answer exactly that question
from the *bytes*, and whose docstring says the judgement now lives in one place
and *"both files call it"*. This file was the one that did not, so the sentence
was true of the module and false of the package.

The consequence: identical bytes were class B named `.jsonl` and class C named
`.log` — and the class C branch does not decline to rule, it asserts that the ids
in the file are *"constants, guards or narrative"* carrying *"no environment
payload"*, about a file no parser had opened.

**Three files move, all C → ? / needs_human** (`MOVED.tsv`, tagged `defect-3`):

| path | before | after |
|---|---|---|
| `theoria-arm/runs/20260728T233900Z-A3-campaign-devpile/pytest-baseline.txt` | C | ? |
| `figures/paper/dark/figure6_bill_shape.pdf` | C | ? |
| `figures/paper/light/figure6_bill_shape.pdf` | C | ? |

The work order predicted the first. The two PDFs were not predicted and are
reported as measured. They reach the same verdict by the other half of
`json_shaped`: a file whose bytes do not decode as UTF-8 returns
`(is_json_shaped=True, jsonl=True)` — "not text at all … undetermined, not
prose". Both PDFs literally contain all four dev-pile game ids in their bytes, so
`named` is non-empty and the old code asserted from the `.pdf` suffix that those
ids carry no environment payload. Nobody had parsed them. `?` is the honest
answer and it is the same answer for the same reason.

No file moved in the permissive direction, and no file gained class B from the
transaction-marker branch at `:146` — that branch is now reachable under any
filename, and on this tree nothing outside `.json`/`.jsonl` carries a marker.

## Where the gate now goes red, and why that is correct

`python release/enumerate.py --dry-run --mode verify` → **exit 1**, red lines
clear, 3 files listed as class ? / needs_human. Before the fix, exit 0.

`release/checklist.py` reads `MANIFEST.jsonl`. Driven over the `after` rows:
7 present / **2** withheld / 0 absent / **1 undetermined**, 3 unruled rows →
**exit 1**. Over the `before` rows: 7 / 3 / 0 / 0, 0 unruled → exit 0. The item
that turns is 「runs 档案（P5 条目追加）」, which matches
`theoria-arm/runs/.../pytest-baseline.txt` — it moves from WITHHELD to
UNDETERMINED, which is the checklist's own distinction between "looked, not
shippable" and "could not look".

**This is the fix succeeding.** The alternative on offer is the previous state,
in which those three files were `releasable-flagged` and shipped on the authority
of the characters after the last dot in their names. Nothing here was
reclassified by hand to keep a number tidy.

`release/MANIFEST.jsonl` was **not** regenerated by this run — see
`MANIFEST.json`'s `not_done` for why.

## Files in this directory

| file | what it is |
|---|---|
| `snapshot.py` | the census tool; `python snapshot.py <out>.jsonl` |
| `before.jsonl` | 5,980 rows from the unfixed enumerator (`git show HEAD:release/enumerate.py`) |
| `after.jsonl` | 5,980 rows from the fixed enumerator |
| `defect1_counterfactual.jsonl` | 5,980 rows, unfixed enumerator, id list forced empty |
| `MOVED.tsv` | every file that changes class, tagged with the defect that moves it |
| `MANIFEST.json` | provenance |
