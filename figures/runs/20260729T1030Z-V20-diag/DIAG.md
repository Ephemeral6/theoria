# V20-figures-pipeline-red — diagnosis (no fixes applied)

Worktree `.worktrees/v20-figures-pipeline-red`, branch `agent/v20-figures-pipeline-red`,
HEAD `443211ddfedbdfd284a16748e95102d344731fdb` (`git rev-parse HEAD`).
All commands below were run from that worktree. Raw logs sit beside this file.

## Verdict in one line

**The board item's premise is false at this commit.** `figures/verify.sh` is
**green on all nine gates** (`verify.log`, exit 0). Two of the item's three
asserted defects were real *yesterday* and have already been fixed on the
mainline; the third (fig02/03/04 uncited) is **confirmed**. A fourth, real,
currently-live drift the item does not mention was found: **`release/MANIFEST.jsonl`
has 14 stale `figures/` entries.**

| item claim | verdict |
|---|---|
| 1. `EXPECTED_IDS` stops at E-07 → `build_all.py` must exit non-zero | **REFUTED at HEAD.** Fixed by `abd8d0cb` (2026-07-29T13:15:53+08:00). Was true 2026-07-28T22:41 → 2026-07-29T13:15. |
| 2. `SOURCES.sha256`: 50 entries, 13 drifted, committed drift | **REFUTED at HEAD.** 61 entries, **0** drifted. The "50" is the manifest as of `9239eb1c` (2026-07-28T19:34), two regenerations ago. |
| 3. fig02/03/04 cited 0 times in `papers/` | **CONFIRMED** (fig02 has exactly one incidental mention, in a review run note, not a citation). |
| — (not in the item) | **NEW: `release/MANIFEST.jsonl` is stale for 14 of 57 `figures/` paths.** |

---

## (1) build_all failure — REFUTED

`figures/README.md:14` documents `python figures/build_all.py`. Run from the
worktree root:

```
$ python figures/build_all.py
```

* **exit code 0** (`build_all.exit.txt`)
* **stderr: empty, 0 bytes** (`build_all.stderr.log`) — no `WARN:`, no traceback
* stdout: `build_all.stdout.log`, 21364 bytes, ending `OK: 6 figure(s) built.`
* all six figures built, 6 CSVs + 24 images.

### The code the audit quotes

`figures/fig06_concept_timeline.py:103-109`, read at HEAD — verbatim:

```python
EXPECTED_IDS: tuple[str, ...] = (
    "O-01", "O-02", "O-03", "O-04",
    "R-01", "R-02", "R-03", "R-04", "R-05", "R-06", "R-07", "R-08",
    "L-01", "L-02", "L-03",
    "P-01", "P-02", "P-03",
    "E-01", "E-02", "E-03", "E-04", "E-05", "E-06", "E-07", "E-08", "E-09",
)
```

Line 108 **already contains `"E-08", "E-09"`**. The list does not stop at E-07.

### The log the audit quotes

`cold-start-a0/THEORIZE_LOG.md:364-365`, verbatim (truncated for width):

```
364:| E-08 | a guard that counts (`count(Token, present = false) >= k`) — the count-lock gate | **discharged** — one rung, in the guard language; see below | …
365:| E-09 | putting a *named track* in a *place*: … (`faces(T,D)`) — the miner vocabulary, not the grammar | **discharged** — one rung, mover-relative, one step; see below | …
```

So both halves of the audit's premise are individually correct about the *log*,
and wrong about the *code*: the two sets **agree** at HEAD, which is why the
build is green.

### The exception it *would* have raised, actually obtained

The raise site is `fig06_concept_timeline.py:388-394`. To get the exact text
without editing any tracked file, the module was imported and `EXPECTED_IDS`
monkey-patched in memory back to the pre-`abd8d0cb` value, then `build()` called
(`e07_truncation_demo.txt`):

```
ValueError: THEORIZE_LOG.md: entry ids do not match the declared set. unexpected=['E-08', 'E-09'] missing=[]
  File "figures/fig06_concept_timeline.py", line 1513, in build      -> data, notes = extract()
  File "figures/fig06_concept_timeline.py", line 671, in extract     -> parsed = parse_log(sources.read_text("a0_theorize_log"))
  File "figures/fig06_concept_timeline.py", line 391, in parse_log
```

That is the failure the audit predicted. It is real; it is no longer reachable.

### The window in which the item was true (`history_probe.txt`)

| when | commit | event |
|---|---|---|
| 2026-07-28T22:41:15+08:00 | `76e75609` | THEORIZE_LOG gains **E-08** → pipeline goes red |
| 2026-07-29T01:56:05+08:00 | `4dd8e0f7` | THEORIZE_LOG gains **E-09** |
| 2026-07-29T13:15:53+08:00 | `abd8d0cb` | `fig06`'s `EXPECTED_IDS` gains E-08/E-09 → pipeline goes green |

Red for ~14.5 hours. The audit is dated 2026-07-29 and landed inside that window.

### The item's ask #1 still stands as a *design* defect

`EXPECTED_IDS` is still a **hand-copied list**. `abd8d0cb` fixed the *instance*
by hand-editing the list, not the *class* by deriving it from the log. The
docstring at `fig06_concept_timeline.py:12-17` claims "The entry set is not
hard-coded", which is true of the section/entry *discovery* but false of the
*expected set* the discovery is checked against. The next `E-10` reopens this
exact ticket. Recommended fix (not applied): derive the E-family ids from the
log's own table and keep the raise for anything outside `FAMILIES`.

---

## (2) SOURCES.sha256 drift — REFUTED, 0 of 61 drifted

`figures/sources.py:722-727` is the hashing function, used verbatim:

```python
def sha256_file(abspath: str) -> str:
    h = hashlib.sha256()
    with open(abspath, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()
```

**Raw bytes. No normalization at all** — no LF/CRLF rewrite, no encoding step.
`figures/.gitattributes` (384 bytes) is what keeps the bytes stable on Windows;
the hasher itself does nothing. The manifest writer
(`sources.py:780-795`) is the only place normalization appears, and it is on the
*manifest* file, not the sources: `newline="\n"`, `encoding="utf-8"`.

Recomputation via `sources.manifest_rows()` (`sources_recompute.log`):

```
declared source entries: 61
committed manifest entries: 61
DRIFTED: 0
```

Confirmed a second, independent way — `diff -u figures/SOURCES.sha256 <fresh>`
returned **empty, exit 0** (`gate4_sources.txt`, 0 bytes), and `verify.sh` gate 4
reports `ok  (61 sources hashed)`.

**Full per-entry table: `sources_table.md`** — all 61 rows with declared sha256,
recomputed sha256, match flag, tracked/untracked status, and the last commit
(`git log --oneline -3 -- <path>`) with date and subject. 61 rows, **0** marked
`**NO**`. Since no entry drifted, the "update the hash vs regenerate the figure"
adjudication the item asks for has **no cases to adjudicate**; the table is
included anyway so the next person does not have to recompute it.

### Working tree is clean — drift cannot be hidden by uncommitted edits

```
$ git status --porcelain
?? figures/runs/20260729T1030Z-V20-diag/
$ git status --porcelain figures/
?? figures/runs/20260729T1030Z-V20-diag/
```

The only untracked path is this diagnosis directory. **No tracked file under
`figures/` or under any declared source path is modified.** Note this is a
stronger result than it looks: `build_all.py` was run with default paths, so it
*rewrote* `figures/csv/`, `figures/out/` and `figures/SOURCES.sha256` — and git
still reports them unmodified, i.e. the rebuild reproduced the committed bytes
exactly. (Every later build in this diagnosis was redirected into this runs dir
via `FIGURES_OUT`/`FIGURES_CSV`/`FIGURES_SHA`.)

### Where the audit's "50 entries / 13 drifted" came from

`SOURCES.sha256` had **exactly 50** entries at commit `9239eb1c`
(2026-07-28T19:34:17+08:00), and has been regenerated twice since
(`history_probe.txt`):

```
abd8d0cb 2026-07-29 A12: …RESET                      -> 61 entries   <- HEAD
059f6ed1 2026-07-28 figures: a run that billed nothing … -> 54 entries
9239eb1c 2026-07-28 figures: an oracle can be captured … -> 50 entries   <- the audit's snapshot
f0e43896 2026-07-28 figures: declare the growing inputs … -> 47 entries
87751026 2026-07-28 P4: salvage the P-21 figure pipeline  -> 43 entries
```

Comparing that 50-entry manifest against today's on-disk bytes
(`audit_hypothesis.txt`) gives **7 hash drifts + 4 paths no longer on disk = 11**,
not 13 — so the "13" does not reproduce exactly and its provenance is unknown.
The "50", the "committed drift" framing, and the general shape all match a read
of `9239eb1c`. The seven that would have drifted:
`baseline-arms/BUDGET_REPORT.md`, `cold-start-a0/THEORIZE_LOG.md`,
`cold-start-a0/artifacts/candidates.jsonl`, and four
`theoria-arm/runs/**/MANIFEST.json`.

### The real, currently-live drift the item missed

`release/MANIFEST.jsonl` (last regenerated `6b095965`, 2026-07-28T22:53:53+08:00
— i.e. *before* both `059f6ed1` and `abd8d0cb`) declares sha256 for 57
`figures/` paths. **14 no longer match** (`release_manifest_check.txt`):

| path | declared → actual size |
|---|---|
| `figures/SOURCES.sha256` | 6859 → 7784 |
| `figures/check_coverage.py` | 13963 → 18392 |
| `figures/verify.sh` | 9802 → 11008 |
| `figures/fig06_concept_timeline.py` | 67186 → 67202 |
| `figures/csv/fig02_bill_shape.csv` | 104789 → 137687 |
| `figures/csv/fig06_concept_timeline.csv` | 15922 → 16436 |
| `figures/out/{light,dark}/fig02_bill_shape.{svg,png}` (4 files) | e.g. 1006130 → 1096149 |
| `figures/out/{light,dark}/fig06_concept_timeline.{svg,png}` (4 files) | e.g. 592472 → 604354 |

43 of 57 match; 0 missing on disk. This is a genuine WP10 (release-package
reproducibility) defect and it is *of exactly the kind the item describes*, just
in a different file. Adjudication is unambiguous here: the sources legitimately
changed and the figures were legitimately regenerated (gate 6 proves the
committed plates are what the pipeline currently produces), so **the release
manifest must be regenerated** — nothing needs re-plotting.

---

## (3) Byte determinism — GREEN, obtained, not assumed

Build (1) completed, so no figures were skipped. The mechanism is the one
`verify.sh` gates 1–3 already use (`verify.sh:63-95`): the
`FIGURES_OUT`/`FIGURES_CSV`/`FIGURES_SHA` env overrides into two scratch trees,
then `diff -r`. Reused verbatim, with the scratch trees redirected inside this
runs dir so no tracked path is touched:

```
$ FIGURES_OUT=…/detA/out FIGURES_CSV=…/detA/csv FIGURES_SHA=…/detA/SOURCES.sha256 python build_all.py   # exit 0
$ FIGURES_OUT=…/detB/out FIGURES_CSV=…/detB/csv FIGURES_SHA=…/detB/SOURCES.sha256 python build_all.py   # exit 0
$ diff -r detA detB                                                                                     # exit 0
```

* `det_diff.txt`: **0 bytes**. No differing file, in either the CSV layer or the
  image layer. 6 CSVs + 24 images + the manifest, all byte-identical.
* `detA.log` and `detB.log` are themselves byte-identical (22338 bytes each).

Two further diffs, which is `verify.sh` gate 6 (`verify.sh:140-147`) — the
committed tree against a fresh build:

* `diff -r figures/csv …/detA/csv` → exit 0, `gate6_csv.txt` 0 bytes
* `diff -r figures/out …/detA/out` → exit 0, `gate6_out.txt` 0 bytes

**Nothing committed under `figures/` is stale.**

### Full gate run

`bash figures/verify.sh` → **exit 0**, `verify.log`:

```
0. required data sources present            ok
1. build pass A                             ok  (24 images)
2. build pass B                             ok  (24 images)
3. A vs B, byte for byte                    ok  (csv, out, SOURCES.sha256 all identical)
4. data-source hashes match the manifest    ok  (61 sources hashed)
5. every declared artefact exists           checked 6 figures -> 24 images + 6 CSVs
6. committed tree matches a fresh build     ok
7. no figure reads an undeclared path       ok
8. coverage: everything on disk reaches …   ok (negative control fires) / ok
9. cross-arm cost claim reconciles          ok  (AGREE(known-defect) 22, UNCORROBORATED 77)
VERIFY: green.
```

Gate 9 surfaces one *pre-declared, documented* known defect —
`RESET_IN_DENOMINATOR`, 22 runs, `capability_spectrum.actions +1`, against
`proxy/SCORING.md:60-62`. It is reported as a known defect, not a failure, and
does not make the gate red.

---

## (4) Citation census — audit CONFIRMED for fig02/03/04

There is no `fig01` in this pipeline; `build_all.py:57-64` declares exactly six:
fig02…fig07. Raw greps: `census_papers.txt` (all hits, verbatim),
`census_breakdown.txt` (split by area).

Search terms per figure: the stem (`figNN`), the full slug
(`figNN_<name>`), the output filenames (`out/{light,dark}/<slug>.{svg,png}`,
`csv/<slug>.csv`) — all four are substrings of the stem search, so the stem
count is the upper bound — plus the `**Figure N**` caption forms in the paper body.

| figure | hits in `papers/` | in the paper BODY (`PAPER.md`, `sections/`, `OUTLINE.md`, `verify_paper.py`) | cited as |
|---|---|---|---|
| `fig02_bill_shape` | **1** | **0** | — |
| `fig03_capability_spectrum` | **0** | **0** | — |
| `fig04_a3_transfer` | **0** | **0** | — |
| `fig05_a2_repair_loop` | 19 | 11 | "Figure 3" |
| `fig06_concept_timeline` | 32 | 10 | (unnumbered plate, §3 A0) |
| `fig07_a0_vs_a0prime` | 23 | 10 | "Figure 2" |

**fig03 and fig04 have literally zero occurrences anywhere under `papers/`.**
fig02's single hit is not a citation:

```
papers/phase1-workshop/runs/20260728T173000Z-P12-paper-multi-review/gate-diagnosis.md:12
  | B-i | `out/dark/` | `sections/03_a0.md:32` | BROKEN — a bare suffix … | write the whole path:
    `figures/out/dark/fig06_concept_timeline.svg` (exists, with `.png`; the full fig02–fig07 dark set is present) |
```

i.e. the string `fig02` appears only inside the range-phrase "fig02–fig07" in a
review note about a *different* figure's broken path. **The audit is right: three
of six plates are uncited.**

Exact file:line for the three that are cited:

* **fig05** — `papers/phase1-workshop/PAPER.md:1163-1165`;
  `papers/phase1-workshop/sections/05_a2.md:134-136`;
  `papers/phase1-workshop/OUTLINE.md:72`;
  `papers/phase1-workshop/verify_paper.py:78,81,85`;
  `papers/phase1-workshop/figures/check_figure_parity.py:15,67,180,184,187`;
  `papers/phase1-workshop/figures/PARITY.md:22`.
* **fig06** — `PAPER.md:642-644`; `sections/03_a0.md:31-33`; `OUTLINE.md:70`;
  `verify_paper.py:79,82,84,86`; plus 10 hits in `papers/**/figures/` and 11 in
  `papers/**/runs/`.
* **fig07** — `PAPER.md:714-716`; `sections/03_a0.md:103-105`; `OUTLINE.md:71`;
  `verify_paper.py:80,83,87`; plus 8 in `papers/**/figures/`, 5 in `papers/**/runs/`.

### Why: the paper runs a *second*, three-figure set

`papers/phase1-workshop/figures/` is its own figure directory —
`fig1_concept_timeline`, `fig2_coverage_accuracy`, `fig3_loop_ledger` (ASCII `.txt`
plates plus `.py` and `data/*.json`). `check_figure_parity.py:67` maps them:

```
"fig3_loop_ledger": "fig05_a2_repair_loop"     # and fig1 -> fig06, fig2 -> fig07
```

and `verify_paper.py:20` states the scope out loud: *"paper cites the root
pipeline's fig05/06/07"*. So the omission of fig02/03/04 is **structural and
enforced**: the paper's own gate requires three citations and would stay green
forever no matter how many plates the pipeline grows. `OPEN_ITEMS.md:116` records
"REVIEW says no sentence references any figure. Three now do." — three, by design.

### Referenced elsewhere in the repo? Yes — all six

| figure | `release/MANIFEST.jsonl` | root `README.md` | `figures/PLAN.md` | `figures/README.md` | `figures/RUN_STATE.md` | `figures/SOURCES.md` | elsewhere (excl. `papers/`, `figures/`) |
|---|---|---|---|---|---|---|---|
| fig02 | 6 | 0 | 6 | 2 | 6 | 0 | 73 |
| fig03 | 6 | 0 | 6 | 3 | 5 | 0 | 21 |
| fig04 | 6 | 0 | 5 | 1 | 2 | 0 | 15 |
| fig05 | 6 | 0 | 4 | 1 | 2 | 0 | 18 |
| fig06 | 6 | 0 | 4 | 1 | 3 | 2 | 29 |
| fig07 | 6 | 0 | 5 | 1 | 3 | 0 | 22 |

Every figure is in the **release manifest** (`.py` + CSV + 4 images = 6 entries
each), in `figures/PLAN.md`, and in `figures/README.md`'s six-row table
(`README.md:40-48`). The root `README.md` mentions none of them. So the item's
"a figure nobody cites is a drifting burden in the release package" is exactly
right, and §2's 14 stale manifest entries — 8 of which are fig02's and fig06's
plates — are the burden already realised.

---

## What is actually actionable (nothing applied here)

1. **Regenerate `release/MANIFEST.jsonl`.** 14 stale `figures/` entries, live now.
   This is the one thing on this ticket that is currently broken.
2. **Derive `EXPECTED_IDS` from the log** (item ask #1). The 2026-07-28 outage is
   fixed by hand; the class is not. `E-10` re-breaks it.
3. **fig02/03/04: cite or retire** (item ask #4). Note `verify_paper.py:78-87`
   hard-codes the three-figure expectation, so "cite them" means editing that
   list too, or the paper gate will not notice if they fall out again.
4. Nothing to do for items 1–3 of the ticket's diagnosis as written: the build is
   green, the source hashes are exact, and the output is byte-reproducible.

## Files in this directory

| file | what it is |
|---|---|
| `build_all.stdout.log` / `build_all.stderr.log` / `build_all.exit.txt` | §1, the documented build, exit 0, empty stderr |
| `e07_truncation_demo.txt` | §1, the exact `ValueError` the pre-fix list raises |
| `sources_recompute.log` | §2, 61 declared / 61 committed / 0 drifted |
| `sources_table.md` | §2, all 61 entries: declared vs recomputed hash + last commit/date/subject |
| `SOURCES.sha256.at-9239eb1c` / `audit_hypothesis.txt` | §2, the 50-entry manifest the audit appears to have read |
| `release_manifest_check.txt` | §2, the 14 stale `release/MANIFEST.jsonl` entries |
| `detA/`, `detB/`, `detA.log`, `detB.log`, `det_diff.txt` | §3, the two scratch builds and their (empty) diff |
| `gate4_sources.txt`, `gate6_csv.txt`, `gate6_out.txt` | §3, committed-vs-fresh diffs, all empty |
| `verify.log` | §3, full `verify.sh` run, exit 0, nine gates green |
| `census_papers.txt`, `census_breakdown.txt` | §4, raw greps |
| `history_probe.txt` | §1/§2, manifest entry counts and `EXPECTED_IDS` per commit |
