# CITECHECK slice C — §7 (metrics battery) and §8 (the exam)

**Audited state.** `papers/phase1-workshop/PAPER.md`, sha256
`6b633fcc35ae612f20f4028eb45aaca1b6ed86a24eb1304af555c46228325376`, **3729**
lines (newline bytes, `wc -l`), **237872** bytes — measured in this worktree with
`sha256sum` / `wc`, not copied from a sibling. Slice: lines 1669-2520 (§7-§8,
including the three-line `---` separator that closes §8). Auditor: CITECHECK
re-run, P18, 2026-07-30.

**Method.** The four passes and the precedence rule ("JSON artefacts beat prose
reports") are copied from `papers/phase1-workshop/CITECHECK.md`. Pass A was
scripted: every backtick span in PAPER.md lines 1669-2520, filtered to path-like
tokens, tested with `Path.exists` at the worktree root, then brace-expanded and
retested, then retested under a section-implied base. Passes B, C and D were
manual — every cited artefact opened and the value read out of the named field
with `json.load`, never by eyeballing a grep hit. Where the paper cites a JSON
artefact I read the JSON; where it cites only a prose report I say so, because
the precedence rule makes that weaker evidence. Zero network calls. Nothing
outside this report was modified. **This report supersedes the 43-line stub that
previously occupied this path**: the stub asserted a per-pass count table with no
findings behind it, and every number below was re-derived from the rows actually
written here rather than carried over.

**Line mapping — verified, not assumed.** `assemble.py` joins sections with
`\n\n---\n\n` after a 2-line banner. I reconstructed the slice from the section
files and compared list-of-lines equality in Python:

| PAPER.md lines | section file | offset |
|---|---|---|
| 1669-2321 | `sections/07_battery.md` 1-653 | `PAPER − 1668` |
| 2322-2324 | separator (blank / `---` / blank) | — |
| 2325-2517 | `sections/08_exam.md` 1-193 | `PAPER − 2324` |
| 2518-2520 | separator (blank / `---` / blank) | — |

Both comparisons returned `True` for the full block, and the four boundary lines
match byte-for-byte (`## 7 · The metrics battery…` / `(\`battery/DECISIONS.md\`
D-B-011).` / `## 8 · The exam…` / `nobody shipped.`). **The offsets asserted by
the stub are correct.** Every finding below gives both line numbers.

**Rule under test.** "Every quantitative claim carries the repo-relative path of
the artefact it came from."

---

## Sealed-pile discipline

**No sealed-game material was read, and none is named by id.** A regex scan for
the repository's game-id shape (`[a-z0-9]{2,4}[0-9]{2}-[0-9a-f]{8}`) over
PAPER.md lines 1669-2520 returns **zero** matches. A scan for the four
development-pile prefixes returns exactly one token, `g50t`, in the two run
directory names at L2236 and L2261-2263
(`theoria-arm/runs/20260728T015354Z-g50t-first-contact/`,
`…-a3-level-boundary/`) — development pile, permitted.

`exam/guard.py` was opened only to confirm what §8.3 says it does (it is Pass D
material, a quoted sentence about its own scope); its `no_network` contextmanager
was read, its game lists were not enumerated into this report.
`battery/artifacts/` provenance was read for *counts* — run counts, arm counts,
`model_calls` and `steps` per run — and for the four development-pile game ids
the battery is scoped to (`provenance.cut.dev_pile`, which is exactly the four).
`arc-recon/data/piles.json` was **hashed, not read**: §7.10a's three digests were
recomputed by feeding its bytes to `hashlib` and parsing it in memory to drop one
field; nothing from it was printed or inspected beyond the digests and a CRLF
count. **No sealed game's content, mechanics, trajectory or artefact was
opened.** Two of §7's claims are unverifiable under the cut and are recorded in
*What this audit could NOT check* rather than passed silently.

---

## Summary

| pass | measure | count |
|---|---|---|
| A | path-like backtick tokens extracted from the slice | **57** |
| A | of those, not a path at all (extractor false positive) | **1** |
| A | distinct path citations | **56** |
| A | resolve as written, repo-relative from the worktree root | **53** |
| A | resolve only under a section-implied base | **1** |
| A | resolve only after shell brace expansion (`{a,b}`) | **2** |
| A | do not exist anywhere in the tree | **0** |
| B | distinct numeric claims traced to a named file and checked | **~150** |
| B | wrong, mis-attributed, or not present in the cited file | **10** |
| C | numbers with no citation at all, or a citation lacking them | **11** (1 overlaps B) |
| D | attributed passages checked (9 blockquotes + 22 inline) | **31** |
| D | inexact — paraphrase, compression, truncation, silent ellipsis | **6** |

*(Counts derived from the enumerated rows below: Pass A from the scripted
extraction, Pass B from rows B1-B10 against the confirmed-correct list, Pass C
from rows C1-C11, Pass D from rows D1-D6 against the verified-exact list.)*

**How this differs from the stub.** The stub asserted B = 6 wrong, C = 7 uncited,
D = 21 checked / 4 inexact. Pass A's five counts hold up exactly. **Pass B, C and
D counts were all too low**: B is 10, C is 11, D checked 31 of which 6 are
inexact. See *Where the stub's asserted counts were wrong* at the end.

**Bottom line.** §7 carries more numbers than any other section of the paper and
survives better than its length suggests: the §7.7a blind-round narrative
(105/91/`main == ["E1","M3"]`, all three re-derived from the run artefact *as
first written*), the 0.125/0.25 power floor, the 32-cluster de-redundancy result,
the 257-of-703 pair coverage and all three pile digests reproduce exactly. Six
places where §7 explicitly **overrides** one of its own sources were checked and
all six hold. The failure mode is concentrated in **§8**: four of the ten Pass B
findings and four of the eleven Pass C findings sit in a 193-line section, and
all four §8 Pass-B findings are the same defect — the paper reproduces an
`exam/` self-description that the `exam/` tree has since overtaken, while citing
the artefact that overtook it. **B1** (a hole reported as open that the cited
JSON records as closed), **B3/B10** (a cheater round the paper says never
happened, whose results are in `exam/artifacts/`) and **D1** (a sentence set in
italics, attributed to "the directory", that exists nowhere in the repository)
are the load-bearing ones. §8's other structural weakness is that it names
`exam/STATUS.md` **zero times** while quoting it three times.

---

## Pass A — path existence

57 path-like backtick spans in lines 1669-2520. **One is an extractor false
positive, not a citation**: `ok_steps / optimal` (L1985 / `07`:317), P4's formula
written inline. Of the remaining **56**, all 56 resolve to something in the tree;
**none is broken**. Three are not repo-relative-as-written.

| # | cited as | PAPER.md line | section:line | resolution |
|---|---|---|---|---|
| **A1** | `mark.py` | 2371 | `08`:47 | **section-implied base.** No `mark.py` at the root. `find` over the tree returns exactly one file, `exam/grading/mark.py`, which the same subsection cites *in full* nineteen lines earlier (L2352 / `08`:28). Unambiguous, but the bare form is the one a reader greps |
| **A2** | `ablation-arm/artifacts/{a0-base,a2-base,a2-charitable}/episode.jsonl` | 2245 | `07`:577 | **brace expansion.** All three expand and all three exist. Not a path as written — `Path(...).exists()` is `False` on the literal string |
| **A3** | `exam/artifacts/reports/p15-handover-a0.reader-tier{1,2}.report.json` | 2404 | `08`:80 | **brace expansion.** Both expand and both exist |

The other 53 resolve exactly as written. Notes on ones that resolve but deserve a
word:

* Three citations are **directories**, not files: `battery/artifacts/` (L1956 /
  `07`:288, cited as the negative — "carried by no artefact in"),
  `battery/audit/exploits/` (L1971 / `07`:303) and
  `theoria-arm/runs/20260728T210000Z-a3-level-boundary/` (L2261 / `07`:593). All
  three exist. The first is used correctly as a *scope* for a negative claim, and
  I verified that negative claim independently — see the confirmed list under
  Pass B.
* `CLAUDE.md` (L2311 / `07`:643) is cited for the pile digest string. It resolves
  at the worktree root and carries the string. This is the paper citing the
  repository's own instructions file as an artefact under audit, which is
  unusual but correct here — §7.10a's closing finding is *about* that file.
* `Theoria.md` is cited six times (L1673, 1713, 1723, 1994, 2161, 2417) and
  resolves; the §-anchors it gives (Phase 2, Phase 2 process 1, Phase 4, process
  3, 1.11) are checked in Pass D where they carry quotations.
* No citation in this slice is **line-anchored** (`file.py:NN`). Slice B found
  three; §7-§8 has none, so the most fragile citation form in the paper does not
  appear here. Several citations instead name a **JSON path** inside the file
  (`provenance.input_digests`, `metrics.P3`, `runs[*].metrics.E2.value`,
  `n_pairs_measured` of `n_pairs`, `K2 support.frame`, `clusters[*].warning`).
  Those field anchors are the thing Pass B actually tests, and they are checked
  one by one below.

---

## Pass B — wrong numbers, mis-attributions, numbers absent from the cited file

| # | § | PAPER.md / section:line | paper says | the artefact says | severity |
|---|---|---|---|---|---|
| **B1** | §8.3 | 2460-2462 / `08`:136-138 | "The repair added label derivation from the key, and it did not fully close the hole: `exam/artifacts/leakage.json` records **`label_sets_checked: []` for the handover and adaptation papers**, so the positional and metadata checks still run on nothing for two of the four" | **The cited artefact says the opposite.** `leakage.json` on this branch records `label_sets_checked` = `["event","level_name"]` (heldout), **`["rule"]`** (handover), **`["exact_on_heldout","label","verdict"]`** (adaptation), `["board_size_class","class","search_credible","witness_length"]` (verdict). **No paper has an empty label set.** The claim was true up to commit `a95f7b32` and was fixed at `1f378483`, whose subject is *"exam: the leak gate was passing, and two of four papers were green because nothing looked at them"*. The paper presents a closed hole as open, and cites the file that closes it | **high** |
| **B2** | §8.4 | 2489-2492 / `08`:165-168 | "**The cheater's numbers are prose, not artefacts.** … no cheater response or transcript is archived. We report those figures as findings the exam reports, not as results a reader can re-derive here" | Half true and half false. The brief directory *is* gitignored (`exam/.gitignore` L9, `artifacts/cheater/`) ✓. But a cheater response **is** archived: `exam/artifacts/answers/p15-verdict-a2.cheater-v4.answers.json` is a full 17-item submission carrying a per-item `meta.exploit_per_item` map, it is scored on `exam/artifacts/matrix/verdict_confusion.json`/`.md` as its own row, and `exam/tests/test_selftest.py` L614-641 asserts against it. `exam/leakage.py`'s own module docstring says "Its transcript is archived next to the paper". The 17/17 and 47.5 % figures of §8.3 are indeed prose-only; the blanket "no cheater response … is archived" is not | **high** |
| **B3** | §8.4 | 2493-2495 / `08`:169-171 | "**Two cheater agents, four sheets, one pass** — and none of them has seen the fixed sheets. In the directory's own words: *the leaks that remain are the ones nobody has looked for yet.*" | `exam/STATUS.md` L267-273 carries this weakness **struck through**: "~~**Two cheater agents, four sheets, one pass.**~~ **Partly closed by V4.** Two more cheaters have now sat the two sheets that changed — verdict and held-out — and both results are above." `exam/runs/20260728T105500Z-V4-exam-selftest/CHEATER.md` L1-6 quotes the same weakness and answers it: "The two sheets that changed when P-15's leaks were fixed are `p15-verdict-a2` and `p15-heldout-a0`. **Both have now been attacked.**" The paper reproduces the superseded form and attributes it to "the directory". (The attributed sentence itself does not exist — see D1) | **high** |
| **B4** | §7.6 | 1956-1958 / `07`:288-290 | "ρ = −0.83 is carried by no artefact in `battery/artifacts/` — it appears **only in `battery/REPORT_V0.md` and `battery/STATUS.md` W-4** — so it is quoted as a report's statement about v0" | The first half holds: `grep` for `-0.83[0-9]*` over all seven files in `battery/artifacts/` returns only `-0.833333333` (a metric value, unrelated) ✓. The second half is wrong. **`battery/STATUS.md` does not contain the string anywhere**, and W-4 (L160-165) is about something else: it carries the *27–45 %* failure rate and a different correlation, **ρ = +0.857 between E6 and P5**. The only other occurrence in the tree is `battery/runs/20260729T025515Z-V18-battery-prereg-check/REVIEW_TABLE.md` L135. A sentence whose whole job is an exhaustive provenance claim names a file that does not carry the number | **medium-high** |
| **B5** | §7.1 | 1700-1704 / `07`:32-36 | "**two of the five arms** live in gitignored payloads — the upstream Schema traces and the S1 campaign shards are absent from every git worktree, so a recompute on a clean checkout silently drops a whole arm and a whole campaign" | One arm, not two. `capability_spectrum.json` records the S1 shards as **48 `bare_cc` runs** with `campaign: "S1 baseline-parity"` and `source: ledger.{ar25,g50t,sk48,tn36}.jsonl` — `bare_cc` is not gitignored as an arm, and 32 of its 80 runs are in-tree. Only `schema_repro` (8 runs, `source: schema_traces`) is wholly gitignored. The cited file says so in as many words: `battery/STATUS.md` L32-33, "否则会静默少掉**一整条臂和一整个战役**" — one arm and one campaign, which is exactly what the paper's *own next clause* says. The lead phrase "two of the five arms" contradicts the rest of its own sentence | **medium** |
| **B6** | §7.7a | 2088-2093 / `07`:420-425 | limit 2: "the sequence rests on `battery/PREREG_V9.md`'s self-report, which records having run **the stricter version** first and seen it lift K12 and E2 back" | Inverted. `PREREG_V9.md` 修订 1 says the *collapse* is what made the rule strict — "方向上它把规则改**严**了" — and that the version which lifted K12 and E2 back into the main table was the **un-collapsed, literally pre-registered** form ("`defended` 作为逐指标布尔量把 K12 与 E2 提回了主表"). That is the *looser* rule, as the paper's own limit 1 establishes three paragraphs earlier: applying the published form leaves four metrics in the table against a published zero. Limits 1 and 2 of the same list disagree about which rule is stricter. (The surrounding claims check out: `verdict.py` first enters at `520dc5dd` alongside `attacks/a1..a6`, `9892d23c` carries only `prereg.py` and `check.py`, and **all three committed versions of `verdict.py` carry the collapsed form** — so "no commit ever contained the un-collapsed form" ✓) | **medium** |
| **B7** | §8.2 | 2397-2400 / `08`:73-76 | "One pre-registered band failed on first contact — the held-out bluffer scored 0.45 against a band ending at 0.35 — and it was **replaced rather than widened**, by two mix-invariant checks, with the original reasoning preserved verbatim in the code (`exam/DECISIONS.md` D-EX-010)" | The band *was* widened, and both cited sources say so. `exam/grading/calibration.py` L93-95 opens the block with "**WIDENED AFTER FIRST CONTACT** -- see D-EX-010. The original band was `Band(0.0, 0.35, "returning the unchanged frame is right only where nothing moved")`, and the built paper scored 0.45" — which also confirms "original reasoning preserved verbatim" ✓. `exam/artifacts/calibration.json` `pre_registered["heldout/bluffer"].band` reads **`"in [0, 0.5]"`**, and D-EX-010's own body says "The band is now `[0, 0.50]` and the work is done by two new checks". *Replaced rather than widened* is D-EX-010's **heading**, and under this paper's precedence rule the JSON artefact beats the heading: the band was widened **and** supplemented. 0.45, 0.35, and the two replacement checks are all correct | **medium** |
| **B8** | §7.10a | 2232-2233 / `07`:564-565 | "`baseline-arms/ledger.jsonl` carries **560 rows** and records `levels_completed` **0 throughout**, and so does every other record in the tree that carries the field" | 560 rows ✓. But the ledger is a **mixed stream**: only **185** rows carry `levels_completed` (all 0 ✓); the other **375** are model-call rows (`prompt_chars`, `usage`, `total_cost_usd`, `is_error`) with no such key. "0 throughout" reads as 560 of 560. The paper attaches exactly the right qualifier — "every other record in the tree **that carries the field**" — to the *other* records and not to this one | **low** |
| **B9** | §7.2a | 1781-1783 / `07`:113-115 | §7.2a: "A second consequence of n = 4 per side: **every δ here is a multiple of 1/16**, so the table's −0.562 and −0.188 print three decimals onto a quantity with **thirty-three** reachable values" | The arithmetic is right (4 × 4 = 16 pairs, δ ∈ {−16/16 … +16/16} = 33 values ✓) and the two figures are the artefact's `cliffs_delta` **−0.5625** and **−0.1875** ✓. But −0.5625 to three decimals is −0.563 under round-half-up and −0.562 only under truncation or banker's rounding; the paper reproduces `REPORT_V2.md`'s rendering rather than the artefact's value, in the one paragraph whose subject is spurious precision. Cosmetic, listed because the paragraph is about exactly this | **low** |
| **B10** | §8.2 | 2405-2406 / `08`:81-82 | "Held-out, adaptation and verdict **have never been answered by anything but the four fakes**; **no answers or reports exist for them in the tree**" | Both halves fail on the verdict paper. `exam/artifacts/answers/p15-verdict-a2.cheater-v4.answers.json` is an answer file for `p15-verdict-a2`, submitted by `cheater-v4` — a fifth, non-fake examinee — and it is scored as its own row of `exam/artifacts/matrix/verdict_confusion.json` and `.md`, where it and the oracle are "identical in every cell". `exam/runs/20260728T105500Z-V4-exam-selftest/CHEATER.md` records that the held-out sheet was answered by a cheater too (measured at 79/80 on the split, per `exam/STATUS.md` weakness 12). Adaptation is the only one of the three that is genuinely untouched | **medium** |

### Numbers checked and confirmed correct

Traced to the named field of the named file, not to a report. §7 is the densest
section in the paper; this is the whole set I opened, not a sample of it.

* **§7.1 · the v2 headline** — `battery/artifacts/capability_spectrum.json`:
  `battery_version: "v2"` ✓; `runs` has exactly **95** entries ✓ over **5** arms
  (`bare_cc` 80, `schema_repro` 8, `theoria_a2` 4, `theoria_a0` 2,
  `theoria_a0_spike` 1) ✓; `cards` has **38** metrics ✓ over **five** families
  (economy, epistemic, exploration, mechanism, planning) ✓;
  `provenance.n_runs` 95, `provenance.n_games` **4** ✓. Summing
  `coverage[*].by_status` over all 38 metrics gives **ok 1433**,
  **not-applicable 2066**, **insufficient-data 111**, total 3610 = 38 × 95 ✓ —
  all three of the paper's slot counts reproduce, and they reconcile.
* **§7.1 · v0 and v1** — `battery/REPORT_V0.md` L3-4 "26 runs, 4
  development-pile games, 2 arms" ✓ and L96 "out of 29 metrics" ✓;
  `battery/REPORT_V1.md` L3-4 "**31 runs, 4 arms, 38 metrics, 417 computed
  values**" ✓. All three reports exist and are unedited-by-policy ✓.
* **§7.1 · the provenance asymmetry** — this is the paper's own correction of
  itself and it is exactly right. `battery/artifacts/` holds **seven** JSON
  files; `provenance` is a top-level key of **`capability_spectrum.json` only**,
  and the other six (`arm_contrast`, `discrimination`, `discrimination_arms`,
  `gaming_audit`, `redundancy`, `validation_material`) have no provenance block
  at all ✓. `provenance.cut.piles_sha256` is the verified digest and
  `provenance.input_digests` is a six-entry map of input file hashes ✓.
* **§7.1 · the two caveats** — `battery/DECISIONS.md` **D-B-008** is headed
  "The determinism test runs against a synthetic fixture" ✓ and **D-B-001** is
  headed "The guardrail verifies the cut, not just the id" ✓, so the paper's
  note about which decision earlier drafts mis-cited is correct.
  `battery/STATUS.md` L36-37 carries `THEORIA_SCHEMA_TRACES` and
  `THEORIA_BASELINE_ARMS` verbatim ✓ (see B5 for the arm count).
* **§7.2 · the whole effect-size table.** Every cell of the eight rows is the
  named field of `battery/artifacts/discrimination_arms.json`:
  P1 `+1.0` / 0.793492681 / 1.015264428; P2 `+1.0` / −0.155038916 / 0.008213513;
  E4 `−0.875` / 0.248594407 / 0.053614176; X1 `−0.625` / 0.278435693 /
  0.084637118; X4 `−0.625` / 0.09305205 / 0.010863339; X3 `−0.5625` /
  0.014987662 / −0.007395678; P3 `−0.375` / 0.129786631 / 0.00093633;
  X2 `−0.1875` / 0.975238357 / 0.94085297 — **all eight δ and all sixteen
  medians round to the printed values** ✓. `agrees_with_declared_direction` is
  `false` on exactly X3 and X2 ✓, matching the "direction held?" column.
  `verdict` is `"underpowered"` on all eight ✓, and on nothing else in the file
  (the other 30 are 23 `no-data` + 7 `not-ranked`). "Ten of 38 pair on at least
  two games" ✓ — 10 metrics have `n_paired_games ≥ 2` (the eight plus the two
  diagnostics P5 and X5) — "eight are rankable" ✓ (8 carry a `cliffs_delta`).
  Tier column matches `gaming_audit.json` `tier` ✓ (P3 main, seven reference).
* **§7.2 · the Schema-side-runs column, which the paper adds itself.** Recomputed
  from `capability_spectrum.json` by counting `status == "ok"` among the 8
  `schema_repro` runs: **P1 4/8, P2 4/8, E4 4/8, X1 8/8, X4 8/8, X3 8/8, P3 8/8,
  X2 8/8** — every cell as printed ✓. The confound is real and reproduces:
  `model_calls` on the `claude_fable_opus` collection is **279, 197, 288, 564**
  (the paper's "197–564") and **0, 0, 0, 0** on `gpt_5_6_sol` ✓. "Codex-side" is
  `REPORT_V2.md`'s own term (L139) ✓.
* **§7.2 · the median steps** — cited to `REPORT_V2.md` (a prose report, so
  weaker under the precedence rule), but it reproduces from the JSON:
  median `steps` over the 8 `schema_repro` runs is **450.0** and over the 80
  `bare_cc` runs is **27.0** ✓.
* **§7.2 · the arm's provenance** — 8 runs = 4 games × 2 collections ✓;
  `baseline-arms/SCHEMA_LOCATE.md` L3 and §2.3 do say the harness was never
  published ("官方 harness 代码从未发布") ✓; `battery/DECISIONS.md` D-B-019 and
  D-B-004 exist and are headed what they are cited for ✓.
* **§7.2a · the statistic.** `battery/audit/stats.py` L55-66 `cliffs_delta` is
  literally `(greater - lesser) / (len(highs) * len(lows))` over the full
  cross-product — **unpaired, exactly as the paper says** ✓; only `sign_test`
  pairs. P3's disagreement reproduces: `cliffs_delta −0.375` with
  `agrees_with_declared_direction: true`, against `sign_test` `{wins 1, losses 2,
  ties 1, n 3, p_value 1.0}` ✓ — "1 win, 2 losses, 1 tie, p = 1.0" is exact.
  X2 sits in the same position ✓ (identical sign-test shape).
* **§7.2a · the register/tier split** — `gaming_audit.json`: `main` is the nine
  `["E2","E3","K11","K12","K7","M3","M6","P3","P4"]` ✓; of the seven
  reference-tier metrics with a cross-arm effect size, exactly **P2 and X3**
  carry `register_tier: "main"` ✓, the other five were already `reference` ✓.
* **§7.2 · X3's warning** — quoted below in Pass D; the numbers in it
  (`|d| = 0.562`) match `cliffs_delta −0.5625` ✓, and the sign of the Schema
  median (−0.0074) is negative ✓, so "novelty is higher in the last quarter" is
  the artefact's own reading.
* **§7.3 · the scoreboard** — `REPORT_V2.md` L121-124 gives "**Strict score: 7
  hits, 11 misses out of 18**" and "**11 of 18**" under the registered
  conditional ✓, with the conditional's wording ("a finding, not a failure of
  the prediction") verbatim ✓. Prose-only, and the paper says so by citing the
  report rather than an artefact.
* **§7.3 · the economy correction, which is the paper overriding its source.**
  `discrimination_arms.json` `verdict` per economy metric: **E2 `no-data`, E3
  `no-data`, E5 `no-data`, E7 `no-data`** (four ✓), **E1 `not-ranked`, E6
  `not-ranked`** (direction-less diagnostics ✓), **E4 `underpowered` with
  `cliffs_delta −0.875`** ✓. So "four of the seven collapsed" and "E4 did not
  collapse at all" are both right against the JSON, and `REPORT_V2.md` L138's
  flat "the economy family collapsed to `no-data`" is wrong as stated ✓.
  The reason checks too: `capability_spectrum.json` card `E4` has
  `definition: "R^2 of a quadratic fit to context tokens per turn minus R^2 of a
  linear fit"` and `needs: ["model_calls"]` — **a curvature fit over context
  tokens, asking for calls and not for a price**, exactly as claimed ✓.
* **§7.3 · the structural prediction** — `validation_material.json`
  `n_unvalidated: 21` ✓, and the list is all 14 K metrics + all 6 M metrics +
  P4 = 21 ✓, which is the paper's "all of epistemic, all of mechanism, and P4"
  (§7.10). `control_arms: ["bare_cc","schema_repro"]` ✓. The five missed
  behavioural predictions X1/X3/X4/P2/P3 are `REPORT_V2.md` L143 ✓.
  `battery/PREDICTIONS.md` L5-7 carries the append-only clause and the quoted
  sentence ✓; `battery/STATUS.md` W-1 is headed 指标定义与预测出自同一人 ✓.
* **§7.4 · the two scores on one manual** — `capability_spectrum.json`, run
  `a0-base`: `K4 {value 1.0, support {annotated 7, unannotated 3,
  min_witnesses 1}}` ✓ and `K2 {value 0.0, support {agree 0, pairs 3, frame …}}`
  ✓. **K4 = 1.000 over 7 annotated clauses and K2 = 0.000 over 3 pairs with 0
  agreements, on the same run** — all four numbers exact. §1's hook,
  "replay accuracy 0.987", is `K1 {value 0.987288136, support {agree 233,
  pairs 236}}` ✓.
* **§7.4 · K4's tier** — `gaming_audit.json` `metrics.K4`: `status: "register
  confirmed by demonstration"` ✓, `defended: false` ✓, `tier: "reference"` ✓,
  and the defence string ends "K4 must never be reported without K2 beside it" ✓.
  "the audit's majority outcome, **21 of 38**" ✓ — counting `status` over all 38:
  21 confirmed-by-demonstration, 12 contradicted on accidental+defended, 3 on
  accidental, 2 on defended.
* **§7.4 · R-05** — `cold-start-a0/THEORIZE_LOG.md` L224-229 carries both quoted
  fragments verbatim: "the Button is presumably pressable from any of the four
  directions" and "precisely zero — **not thin, zero**" ✓.
* **§7.4 · K2's failed defence** — `capability_spectrum.json` `K2 support.frame`
  on `a0-base` is "3 state-action pair(s) …" ✓ and on `a0-spike` is
  "exhaustive enumeration … (**39960** cases)" with `agree 39960, pairs 39960,
  value 1.0` ✓. So "K2 = 0.000 over 3 adversarial gaps" and "1.000 over 39 960
  exhaustive cases" both come out of the frame field the defence added ✓.
  The exploit's declared frame and "K2 stays in the reference tier" are
  `REPORT_V2.md` v2.1 L350-352 ✓.
* **§7.5 · the floor** — `REPORT_V0.md` L40-43 is the blockquote, verbatim (Pass
  D). `discrimination_arms.json` carries a top-level `power` string ✓ and
  `min_attainable_p` nested under every ranked metric's `sign_test` ✓. **P3, X2
  and X3 each have `ties: 1`, `n: 3` and `min_attainable_p: 0.25`** ✓ — three of
  the eight rows at the worse floor, exactly as claimed, and the other five sit
  at 0.125 ✓. 31 → 95 ✓.
* **§7.6 · E5** — `discrimination.json` `metrics.E5`: `cliffs_delta 1.0`,
  `agrees_with_declared_direction false`, and a `warning` reading "separates the
  gradient strongly (|d| = 1.000) but in the opposite direction to the one
  declared" ✓. `discrimination.json`'s `gradient` is "model ladder within
  bare_cc" ✓, so "on the model ladder" is the right frame.
* **§7.6 · P1 in both passes** — ladder `cliffs_delta −0.75` with the
  wrong-direction warning raised ✓; specified gradient `+1.0` with
  `agrees_with_declared_direction: true` ✓. The `role` field is quoted exactly
  (Pass D). v0's ladder figure "δ = −1.000" is `REPORT_V0.md` L55 ✓ and the
  "between 27 % and 45 % … on HTTP 500s and 'game not found'" is L57-58 verbatim
  ✓. The v2 replacement figure reproduces from the JSON: `redundancy.json`
  `matrix` entry `{a: "P1", b: "P5", rho: -0.89891825, shared_runs: 82}` —
  **ρ = −0.899 over 82 shared runs** ✓.
* **§7.7 · the executable register** — `gaming_audit.json`: `n_demonstrated 38`
  ✓, `n_disagreements 17` ✓, `main` 9 ✓, `reference` 29 ✓, and counting
  `metrics[*].demonstrated.succeeded` gives **34 true / 4 false (E2, K12, M3,
  P4)** — "38 exploits exist, **34** still land" ✓. The endpoint arithmetic is
  re-derivable exactly as the paper says it is: `register_tier == "main"` counts
  **19** ✓, `tier == "main"` counts **9** ✓, `demoted_by_demonstration` has
  **10** entries ✓, and `REPORT_V2.md` L83 names the intermediate six by hand
  (E3, K11, K7, M3, M6, P3) ✓. 19 − 13 = 6, 13 − 3 = 10, 6 + 3 = 9 ✓.
* **§7.7 · the four defences** — every figure is `REPORT_V2.md`'s: P4 `0.083`
  against a 12-step plan and `Step.won` read by no metric (L209-214) ✓; K12's
  six self-reported booleans (L218-221) ✓; E2's `ceil(n × 0.25)` giving 0.333 at
  9 turns and 0.250 at 12 (L222-228) ✓; the concentration attack at **0.993 over
  twenty turns** (L375-376) ✓. The two E2 ranges are both checkable and both
  right: `gaming_audit.json` `metrics.E2.demonstrated.claim` says "whose whole
  observed range is 0.162-0.321" ✓, and the current
  `runs[*].metrics.E2.value` over the 67 runs that return one spans
  **0.161553883 – 0.297300947** ✓ — so "0.162–0.297 in the current artefact, the
  top having fallen when the fix landed" is exact.
* **§7.7 · the epistemic family cannot rank** —
  `battery/tests/test_exploits_mechanism_epistemic.py` L393 is literally
  `assert len(landed) == 18` ✓, and its docstring L381-382 reads "Eighteen of
  twenty metrics in this family are reachable at or near their best value by a
  run with none of the capability -- **nineteen before v2.1 closed K12**" ✓.
  Scope = 14 epistemic + 6 mechanism = 20 ✓; the two unreached are K12 (the
  test asserts `not exploits["K12"].succeeded`) and M3 ✓. The paper's note that
  earlier drafts printed nineteen is its own disclosure and the test is the
  authority.
* **§7.7a · the blind round, checked against the frozen artefact.** I read the
  run directory as first written (`git show 0b6e4939:…/v9_gaming_audit.json`)
  and as delivered. **As first written**: `n_attacks 105`, 105 attack records,
  **91 with `succeeded: true`**, `verdict.main == ["E1","M3"]`, `not_gameable
  ["M3"]`, and **no `undetermined` key at all** — every clause of the paper's
  "took the main table from nine metrics to two, leaving E1 and M3 … the
  `undetermined` tier did not yet exist" ✓. **As delivered**: `n_attacks 112`,
  95 landed, `main []`, `undetermined ["M3"]`, `reference` 37 ✓. The sighted
  review is the difference: 112 − 105 = **7 more attacks**, 95 − 91 = **4 more
  landed** ✓. "37 of the 38 metrics reached their pre-registered threshold" ✓
  (`gameable` lists 37; M3 is the exception, `n_landed: 0` over 5 attacks ✓).
  `b14_baseline_main` is the nine ✓ and `demoted_by_v9` is nine of which M3 was
  retiered ✓, so "demoted **eight** and the ninth is a later retier" ✓.
* **§7.7a · six attackers, and what they could see** — `battery/BLINDING.md` §1
  says 六个攻击者, each with an independent copy outside the repository, mutually
  invisible ✓, and §2 confirms the three exclusions the paper names: the register
  (`battery/audit/gaming.py`), the exploits (`battery/audit/exploits/`), and the
  reports (`REPORT_V0..V2.md`, `METRICS.md`, `STATUS.md`, `DECISIONS.md`,
  `PREDICTIONS.md`) ✓, plus mechanical docstring stripping.
* **§7.7a · the empty table** — `battery/METRICS.md` L33 is
  `**Main table (0):** ` and L35 is `**Reference (38):**` followed by all 38 ids
  ✓. And the contradiction the paper flags is real:
  `battery/artifacts/gaming_audit.json` **still records `main` as the nine** ✓,
  by the pre-registration's own leave-published-artefacts-alone rule.
* **§7.7a · limit 1, which is the sharpest check in the section and holds.**
  `git log -- battery/audit/v9/verdict.py` bottoms out at **`520dc5dd`**, whose
  diffstat adds `attacks/a1.py … a6.py`, `mutants.py`, `run.py` and
  `verdict.py` in one commit ✓; **`9892d23c`** adds only `BLINDING.md`,
  `PREREG_V9.md`, `attack.py`, `check.py`, `make_blind.py`, `prereg.py` —
  thresholds and the poverty certificate, no adjudication ✓. The delivered
  artefact's `rule` field publishes the pre-registered form verbatim, `NOT
  defended` included ✓. Applying it to the artefact's own per-metric fields:
  E2, E3, K12 and M6 all have `gameable true`, `accidental_if_gameable true`,
  **`defended_by_v9 true`** and `prior_tier "main"` — **four of the nine would
  have stayed** ✓, and no fifth qualifies (E1 is also `defended_by_v9` but its
  `prior_tier` is `reference`).
* **§7.7a · limits 3-7.** Limit 3: `battery/audit/v9/REPORT.md` §9 closing
  paragraph says "裁决里除 `accidental` 之外没有任何字段是作者断言的" ✓.
  Limit 4: the delivered artefact has **112 of 112** attacks with
  `S3_poverty_certified: true` ✓ and the first-written one **105 of 105** ✓;
  `check.py` is in the pre-registration commit ✓; §9(a) exhibits **two**
  constructions that searched and certified clean (the closure/BFS factory and
  the lambda-plus-conditional-comprehension) ✓. Limit 5: §9(c)'s strength table
  is 强 = E2/E3/K12, 中 = P3/P4/E1, 弱 = K7/K11/M6 ✓ — nine rows including E1 and
  omitting M3 ✓, and **no metric row in the artefact carries a strength field**
  ✓ (`R1_promotion_refused, accidental_if_gameable, attacks, defence,
  defended_by_v9, gameable, n_attacks, n_landed, prior_tier, r2_satisfied,
  v9_tier`). Limit 6: §6's heading is 这不是 37 个独立发现 ✓ and its item 1 is the
  one label-swapping convention satisfying **X1, X2, X4, X5, X6** ✓, with five
  numbered structural causes ✓. Limit 7: §7 says "91 条落地攻击里 **51** 条捏造
  生产者侧记录" ✓, and K12 is 强-graded ✓ with `Beat(env_actions=1)` set directly
  (§9(a)) ✓. The two blind-fall figures also check: P4 at **0.05 after 10000
  failed actions** and K12 at **1.0 on a repair episode that spent zero
  environment actions**, both from §2's table ✓.
* **§7.8 · E2 on the ladder** — `discrimination.json` `metrics.E2`:
  `cliffs_delta 1.0`, `agrees_with_declared_direction true`, `sign_test {wins 4,
  losses 0, ties 0, n 4, p_value 0.125, min_attainable_p 0.125}` ✓ — "δ = +1.000
  in the declared direction, 4 wins of 4 paired games, p = 0.125 against a floor
  of 0.125", all five figures exact. And `discrimination_arms.json` `metrics.E2`
  is `{n_paired_games 0, verdict "no-data", note "schema_repro scores 0 game(s)
  … nothing to pair"}` ✓ — **zero** pairs ✓, so "pairs by game has never fired
  once" ✓. E2/E3's eight-turn floor is `gaming_audit.json`'s defence string ✓.
* **§7.9 · de-redundancy** — `redundancy.json`: `n_clusters 32` ✓,
  `n_metrics 38` ✓, `n_eliminated 5` ✓, and the five retirements are exactly
  **E7→E4 (shared_runs 70)**, **X4→X1 (87)**, **K14→K5 (5)**, **K7→K5 (5)**,
  **K8→K10 (5)** ✓. K7's ρ is `1.0` ✓. `cross_family_clusters` is the single
  `["K6","X1","X4"]` ✓, and it is the only cluster carrying a `warning` key ✓,
  against one global `coverage_note` ✓ — so the paper's correction ("the artefact
  does not flag that cluster by cluster, which is where this paper previously
  said it did") is right. The **two** K-only clusters are `{K10, K8}` and
  `{K14, K5, K7}` with three retirements between them ✓ — and this is the paper
  correcting `REPORT_V2.md` L186, which says "three K-family clusters".
* **§7.9 · the collision** — `redundancy.json` `eliminated` contains K7 ✓ and
  `gaming_audit.json` `main` contains K7 ✓, so "both say so" ✓. K7 fell in the
  blind round on its own account ✓ (`v9_tier: "reference"`, 2 of 2 attacks
  landed).
* **§7.9 · the pair coverage** — `redundancy.json` `n_pairs 703`,
  `n_pairs_measured 257`, and the `matrix` list has 703 entries of which
  **exactly 257** carry a non-null `rho` ✓. "The identical count as v1" is
  verified against v1's own archived artefact, not just the report:
  `battery/runs/P-14/redundancy.json` has `n_pairs 703, n_pairs_measured 257`
  (and 33 clusters against v2's 32) ✓. 95 − 31 = 64 ✓.
* **§7.10 · the one run that reaches a goal** — `capability_spectrum.json`: P4
  returns `status "ok"` on **exactly one** of the 95 runs, `a2-refutation`,
  with `support {actions 18, optimal 18, won true}` ✓. Every clause of that row
  is exact.
* **§7.10a · the empty capability column** — `theoria-arm/runs/20260728T015354Z-g50t-first-contact/run.json`
  carries all four fields as printed: `summary.scorecard.total_levels_completed 0`,
  `total_environments_completed 0`, `environments[0].completed false`, and
  `environments[0].runs[0].level_actions **[7, 0, 0, 0, 0, 0, 0]**` ✓ — and the
  paper is right that they are four fields of one object.
  `ablation-arm/artifacts/{a0-base,a2-base,a2-charitable}/episode.jsonl` each
  contain **exactly one** row with `levels_completed: 1`, and every row carries
  `card_id: null` and `score: null` ✓ — three non-zero values, all disqualified
  by their own records ✓.
  `baseline-arms/runs/20260728T103135Z-a7/envelope.json`
  `pooled_cv.levels_completed` is **`null`** ✓, beside `usd_per_action
  0.033244` ✓ and `http_per_action 0.09574` ✓; every other pooled quantity has a
  number ✓.
* **§7.10a · the budget arithmetic** — `theoria-arm/runs/20260728T210000Z-a3-level-boundary/FINDINGS.md`
  L11-13: `level_baseline_actions: [78, 175, 179, 230, 96, 54, 67]` and "**78
  successful actions**. The authorised budget is **40 per level**" ✓. The a7
  envelope's per-cell figure is `actions_ok` min = mean = max = **30.0** ✓, so
  "neither budget buys the first level" is arithmetic on two verified numbers.
* **§7.10a · the bill shape** — recomputed from
  `capability_spectrum.json`: E2 returns `ok` on **67 of the 80 `bare_cc` runs**
  ✓, their median is **0.229019685** ✓, and **53 of the 67** are below 0.250 ✓.
  `battery/metrics/economy.py` L26 `FRONTLOAD_K = 0.25` with an interpolated
  head (L142-144, and the docstring L111-121 "flat run score 0.250 at every
  length") ✓ — so "a construction null of exactly 0.250" is the definition's
  own ✓. E4's δ = −0.875 over four paired games with its direction holding ✓.
* **§7.10a · the v3 list, and the paper's correction of it** —
  `REPORT_V2.md` L300-314 gives the five items in the order the paper prints
  them ✓. The correction checks in the code: `Step.won` is aggregated in
  `battery/model.py` and gated through `battery/metrics/__init__.py` (P4 returns
  `not-applicable` on a run that never won — confirmed by P4 answering on
  exactly one run, above); `held_out_frame` gates K2 in
  `battery/metrics/epistemic.py` (confirmed by K2's `support.frame` existing on
  `a0-base`); `Beat.env_actions` is summed into `Repair.env_actions` in
  `battery/model.py` and read by K12/K13 ✓. All three fields are read now ✓.
* **§7.10a · the pile digest, recomputed rather than read.** All three digests
  reproduce exactly from `arc-recon/data/piles.json` in this worktree:
  canonical JSON of the payload minus its own `sha256` field →
  **`3feca53e…41bbc19a`** ✓ (the `CLAUDE.md` value); the file LF-normalised →
  **`d3140eff…4dd5b8c9`** ✓ (D-B-011's value); the file as it sits on this
  Windows checkout → **`f2ef44d1…f9790826`** ✓ (the paper's third value, which
  D-B-011 does *not* carry — this one is the paper's own addition and it is
  right). The file contains **111** CRLF pairs ✓. `git check-attr -a` on it
  returns no attributes and `git ls-files --eol` reports `i/lf w/crlf` ✓; the
  repository root `.gitattributes` has two lines, `PARTNER_SYNC.md merge=union`
  and `monitor/board/** text eol=lf`, neither covering it ✓. `D-B-011` exists
  and says what it is cited for ✓. (Digests only; no game content was read.)
* **§8.1 · the four papers** — every item and point count is confirmed against
  `exam/artifacts/papers/*.paper.json` (`n_items` / `total_points`):
  held-out **80 / 80.0**, handover **29 / 46.0**, adaptation **60 / 144.0**,
  verdict **17 / 34.0** ✓. See C1: the paper cites no artefact for these.
* **§8.1 · the three verdict classes** — `exam/artifacts/leakage.json`,
  `p15-verdict-a2` → `positional_derived.class.label_counts` =
  `{small_unsolvable 5, large_unsolvable 4, solvable_hard 8}` with `n: 17` ✓.
  **5 / 4 / 8** exactly, in the cited file.
* **§8.1 · the marker** — `exam/grading/mark.py` L3-4: "The marker is
  deliberately dumb. It looks up each item's rubric by id, hands it
  (answer, truth, item)" ✓. `confusion()` (L95-102) returns sensitivity and
  specificity together, `None` on an empty denominator, with abstentions counted
  as neither and reported separately ✓. The partial-credit split checks in
  `exam/grading/rubrics_verdict.py`: `VERDICT_WEIGHT = 0.5`,
  `JUSTIFICATION_WEIGHT = 0.5` ✓, `SEARCH_CREDIT = **0.4**` ✓, and an invalid
  certificate `return 0.0` at L865 **before** the search-reason branch at L867 —
  a genuine short-circuit with no fallback ✓.
* **§8.2 · calibration** — `exam/artifacts/calibration.json`: `calibrated true`,
  `failures []`; **oracle `fraction: 1.0` and null `fraction: 0.0` on all four
  papers** ✓. The held-out memoriser's `axes.by_split` is `{replay 1.0 (40/40),
  heldout 0.15 (6/40)}` with `gap_replay_minus_heldout: **0.85**` ✓, and
  `by_split_event` gives `replay/blocked_crossing 5/5` against
  `heldout/blocked_crossing 0/5` ✓ — the paper's "5/5 to 0/5" is exact. The
  verdict bluffer's `confusion` is `{tp 9, fp 8, tn 0, fn 0, sensitivity **1.0**,
  specificity **0.0**}` ✓, and `structural_expectations.verdict_bluffer_pair`
  demands exactly that pair ✓. The adaptation memoriser's
  `axes.silently_wrong` is **2** ✓ (and 0 for every other mode). `0.45` and the
  band are B7.
* **§8.2 · the one real result** — both reports carry `awarded 46.0`,
  `possible 46.0`, `fraction 1.0` ✓, and `axes.tier2_minus_tier1: **null**` with
  a note explaining why ✓. `assert_calibrated` does raise rather than warn
  (`exam/grading/calibration.py` L524-531) ✓.
* **§8.3 · the static checks** — `exam/artifacts/leakage.json`: summing
  `probes_declared` over the four papers gives **363 + 58 + 1284 + 85 = 1790** ✓,
  and `probe_hits` and `structural_hits` are **0** on all four ✓. "1,790
  declared probes, 0 probe hits, 0 structural hits" is exact.
* **§8.3 · the construction** — `exam/model.py` `Item` has `paper` and `truth`
  as separate fields, docstring "`paper` and `truth` are disjoint by contract"
  ✓; `Paper.sheet()` docstring "Cannot contain a truth: it is built from
  `Item.sheet_side`, which never sees one" ✓; `check_paper()` "Raises on any
  hit" ✓. The **five** attack surfaces all exist as named functions in
  `exam/leakage.py` — `probe_hits` (56), `structural_hits` (86),
  `positional_report` (95), `metadata_hits` (232), `cheater_brief` (1146) ✓,
  even though that file's own module docstring still says "Three checks" plus a
  fourth: `metadata_hits` was added by D-EX-011 and the docstring was not
  updated. The paper's count of five is the correct one. `key_sha256` and
  "copies no truth file" are `exam/DECISIONS.md` **D-EX-009** ✓ (uncited — see C).
* **§8.3 · the two leaks** — `exam/DECISIONS.md` D-EX-011: the verdict paper
  "weighted the solvable items **3** against **2**" ✓, "the class was readable
  off the point value on **17 of 17 items** … Measured, not estimated" ✓;
  the held-out world description published the push rule and the cheater went
  "from **47.5%** … to essentially full marks" ✓; both fixed (uniform points; a
  world block that names the world and says nothing about how it behaves) ✓;
  both yields confirmed against the key before anything changed ✓.
* **§8.4 · the digest hole** — `exam/grading/registry.py` L33-38 lists
  `RUBRIC_MODULES` as the five `rubrics_*` modules and **`calibration.py` is not
  among them**, so the bands are genuinely outside the digest ✓; L8 says the
  digest "travels onto every sheet and report" ✓ (both handover reports carry
  `rubric_digest`). "One band has already been changed once — recorded, and
  correctly" is D-EX-010 ✓ (and see B7 for how it was changed).
* **§8.5 · the invariant** — `a0-spike/theory/theory.dsl` L71 is byte-exact:
  `  invariant box_row_parity (Box.pos.row) mod 2 = 1 [status: proven]` ✓.

---

## Pass C — uncited numbers

Eleven. C4 and C5 are the same citation gap in two places and are counted
separately because they are two different claims. **C9 is the only row that
overlaps Pass B** (it is B3's sentence, failing this test as well as that one);
C10 shares a source with D2 and D6 but is a different defect — those two are
about what was altered, this one about the missing path.

| # | § | PAPER.md / section:line | the claim | what it would need |
|---|---|---|---|---|
| **C1** | §8.1 | 2338-2343 / `08`:14-19 | the four-paper table's **items** and **points** — held-out 80/80, handover 29/46, adaptation 60/144, verdict 17/34 | a path. The row citations name the *implementation* modules (`exam/papers/heldout.py` and its three siblings) and the lead names `exam/model.py`; none of the four counts is in `heldout.py` or `handover.py` at all, and `verdict.py`/`adaptation.py` carry only 34 and 144 inside comments. All eight numbers are `n_items` and `total_points` of `exam/artifacts/papers/*.paper.json` — **four files the paper cites nowhere**. This is the largest uncited block in the slice: eight figures in the section's opening table |
| **C2** | §7.2 | 1730-1739 / `07`:62-71 | the table's **Schema-side runs** column — "4 of 8" three times, "8 of 8" five times | a field. The paragraph that explains the column cites `battery/artifacts/capability_spectrum.json`, **`model_calls` per run** — which is what supports the 197–564/zero split, not the run counts. The counts are `runs[*].metrics.<id>.status == "ok"` over the eight `schema_repro` runs. The values are right (I recomputed all eight); the named field is a different one |
| **C3** | §7.7 | 1974-1977 / `07`:306-309 | "38 exploits exist, **34 still land**, and 17 register entries were contradicted (`battery/artifacts/gaming_audit.json`: `n_demonstrated` 38, `n_disagreements` 17, `main` 9, `reference` 29)" | a field for the 34. The parenthesis is unusually careful — it names four fields — and **none of them is 34**. 34 is a count over `metrics[*].demonstrated.succeeded`, which the artefact does not aggregate. The other three figures are exact |
| **C4** | §7.7a | 2034-2037 / `07`:366-369 | "They wrote **105 attacks, of which 91 landed**, and **37 of the 38 metrics** reached their pre-registered threshold" | a path. The citation is `battery/BLINDING.md`; `battery/PREREG_V9.md` — **neither carries any of the three numbers**; both predate the attacks by construction. All three are in `battery/runs/20260729T021247Z-V9-battery-gaming-audit/v9_gaming_audit.json` *at commit `0b6e4939`* (`n_attacks` 105; 91 records with `succeeded: true`; `gameable` listing 37). The paper cites that path three times — at L248, L410 and L3476 — **and not once inside §7**, which is the section that reports the round |
| **C5** | §7.7a | 2039-2042 / `07`:371-374 | "`verdict.main` = `["E1", "M3"]`, **the run directory as first written**" | the run directory's name. The sentence points at a file by description and declines to name it, in the one claim of §7.7a that cannot be checked against the tree as it stands — the delivered artefact reads `main: []`. It is `git show 0b6e4939:battery/runs/20260729T021247Z-V9-battery-gaming-audit/v9_gaming_audit.json`, and it does read `["E1","M3"]` |
| **C6** | §7.7a | 2097-2101 / `07`:429-433 | limit 4: "It passed **105 of 105** attacks in the blind phase and **112 of 112** in the delivered artefact" | a path. The limit carries none. 105/105 is `battery/audit/v9/REPORT.md` §7 (prose); 112/112 exists only as a count over `metrics[*].attacks[*].S3_poverty_certified` in the delivered artefact, which the limit does not name |
| **C7** | §7.4 | 1895-1897 / `07`:227-229 | "The recompute also puts numbers on §1's hook — **replay accuracy 0.987** against held-out accuracy 0.000" | a path. The nearest citation is `battery/artifacts/gaming_audit.json`, `metrics.K4`, which carries neither figure. 0.987 is `capability_spectrum.json` run `a0-base`, `K1.value` = 0.987288136 — the file is cited 21 lines earlier for a different claim, and the metric id K1 is never named |
| **C8** | §7.6 | 1942-1945 / `07`:274-277 | "In v0, P1 separated the model ladder at **δ = −1.000** … between **27 %** and **45 %** of pilot steps failed outright" | a path *at the point of use*. Both are `battery/REPORT_V0.md` L55 and L57-58. The paragraph's citations are `discrimination.json` (for the v2 figures) and, fourteen lines later, `REPORT_V0.md` — attached there only to ρ = −0.83, and wrongly (B4). A reader tracing 27–45 % has no pointer |
| **C9** | §8.4 | 2493 / `08`:169 | "**Two cheater agents, four sheets, one pass**" | a path. It is `exam/STATUS.md` weakness 11 — quoted in bold, and **`exam/STATUS.md` is not cited anywhere in §8**. See B3: the source also strikes the sentence through |
| **C10** | §8.2 | 2409-2418 / `08`:85-94 | the two blockquotes introduced by "The exam's own status file says so before anyone else can" | a path. Both are `exam/STATUS.md` L157-160 and L164-166. Named by description, never by path; §8 cites `exam/STATUS.md` zero times. Two of the slice's nine blockquotes are attributed to a file the section will not name |
| **C11** | §8.1 | 2356-2360 / `08`:32-36 | "a machine-checked certificate earns the full reason half, a credible exhaustive search earns **40 %** of it, and an *invalid* certificate short-circuits to zero" | a path. The sentence's only citation is `mark.py` (L2371). All three facts are in `exam/grading/rubrics_verdict.py` — `SEARCH_CREDIT = 0.4` (L795), the docstring's table (L19-22), and the `return 0.0` at L865 that precedes the search branch. That file is cited in §8.1's table for the *verdict paper*, not here |

Paragraphs that *look* orphaned and are not, checked and cleared: §7.2's effect-size
table (the lead names `discrimination_arms.json` and every δ and median is in it);
§7.5's 0.25 floor for P3/X2/X3 (the preceding sentence cites the file and the field);
§7.7's four defence bullets (the lead cites `gaming_audit.json`, and P4's 0.083 and
K12's "six booleans … zero environment actions" are verbatim in
`metrics.P4.demonstrated.claim` and `metrics.K12.demonstrated.claim`); §7.9's
retirement list (lead cites `redundancy.json`); §8.3's `answer_labels` blockquote
(D-EX-011 is cited nine lines above and holds it); §8.2's calibration bullets (lead
cites `calibration.json`); §7.1's slot counts (the file is named, and the three
figures are sums over `coverage[*].by_status` in it).

---

## Pass D — quote fidelity

**31 attributed passages checked: 9 blockquotes and 22 inline attributed
fragments.** Six are inexact. Every check was byte-for-byte after unfolding the
paper's hard wrap and stripping the source's own `>` or `#` markers; nothing was
accepted on a keyword match.

**One normalisation is not counted as a defect, stated so the count is
reproducible.** The paper converts ASCII `--` to an em dash when quoting Python
comments, and collapses the double space PEP-8 leaves after a full stop. Both are
typographic and both are systematic across the whole paper. They are noted where
they accompany a substantive change and never counted alone.

| # | § | PAPER.md / section:line | quoted as | source | problem |
|---|---|---|---|---|---|
| **D1** | §8.4 | 2494-2495 / `08`:170-171 | "In the directory's own words: *the leaks that remain are the ones nobody has looked for yet.*" | **none** | **The sentence does not exist.** `grep` for "nobody has looked for" over every `.md`, `.py` and `.json` in the repository returns exactly one hit, and it is `papers/phase1-workshop/sections/08_exam.md` itself. `exam/`'s nearest real sentence is `STATUS.md` L272: "a cheater pass is a sample, not a proof: **what it did not find is not absent**." A paraphrase is set in italics, introduced as a quotation, and attributed to a directory. It is also the *superseded* form of the point (B3) |
| **D2** | §8.2 | 2416-2418 / `08`:92-94 | > **Worse, the exam measures the wrong side of the pre-registered prediction.** `Theoria.md` 1.11 predicts that the manual-only reader *catches up*, and that the difference shows up as **多付的搜索成本** — a **cost**, not an accuracy. | `exam/STATUS.md` L164-166 | two defects. (a) The source's bolded phrase is **多付的搜索成本 ≈ 玩法书缓存的计算量** — the paper deletes "≈ 玩法书缓存的计算量" **from inside the bold span with no ellipsis**, and that clause is the half that says what the cost is *equal to*, in a paragraph about what the exam failed to measure. (b) The bold is moved: the source bolds the Chinese phrase and leaves "a cost, not an accuracy" plain; the paper unbolds the Chinese and bolds **cost**. Also unattributed (C10) |
| **D3** | §8.3 | 2473-2474 / `08`:149-150 | "It is honest about its own scope: "Not a sandbox — a process determined to get out can get out. It is a tripwire for the accident that actually happens."" | `exam/guard.py` L81-83 | **silently truncated.** The source sentence continues past the full stop the paper closes on: "…a tripwire for the accident that actually happens: **a helper three imports down that quietly fetches something.**" The dropped clause is the only part that says what accident, and the paper is citing the sentence *as* a scope statement. No ellipsis. (Plus the `--` → `—` normalisation, not counted) |
| **D4** | §8.1 | 2366-2368 / `08`:42-44 | > on a 7x7 A0 board a typical transition changes two cells, so an examinee that returns the input frame unchanged already scores 47/49 = 96 % under a cells-correct rubric | `exam/grading/rubrics_heldout.py` L5-7 | three alterations inside a blockquote: the source begins "**On** a 7x7"; the source italicises "*input frame unchanged*" and the paper drops the emphasis; the source writes "96%" and the paper writes "96 %". Content otherwise byte-identical. Listed because a reader grepping the string gets nothing, which is the same class as slice B's D4 |
| **D5** | §8.1 | 2352-2355 / `08`:28-31 | "`exam/grading/mark.py` looks each item's rubric up by id and hands it exactly `(answer, truth, item)`; a rubric never learns who it is marking, because "**a rubric that can see who it is marking is a rubric that can flatter**"" | `exam/model.py` L240-241 | quoted accurately, from a different file. The sentence names exactly one path, `mark.py`, and the quotation is the `Rubric` dataclass docstring in `exam/model.py` — which §8.1 cites two paragraphs earlier (L2335) for the four question types. `mark.py`'s own docstring (L3-4) supports the first half of the sentence exactly; it does not contain the quoted words. Same class as slice B's D5 |
| **D6** | §8.2 | 2411-2414 / `08`:87-90 | > **The second number is not a measurement.** … reporting it as "the playbook is worth nothing" would be wrong. | `exam/STATUS.md` L157-162 | truncated at a sentence boundary with no ellipsis: the source continues "**The sheet needs harder items — boards where a manual-only reader must actually pay for the search — before the delta means anything.**" The quoted portion is byte-exact and the dropped sentence is a remedy rather than a qualifier, so this is the mildest row here; it is listed because the same paragraph's sibling quote (D2) drops a qualifier, and the two together are why §8.2's blockquotes are not reliable transcriptions. Also unattributed (C10) |

### Quotes verified exact

* **`Theoria.md` Phase 2's 同一本账,两次使用** (§7.1, L1673-1674) — byte-exact
  against `Theoria.md` L309, **half-width comma preserved**. This is the exact
  class `CITECHECK.md` flagged in §4.1 and it is clean here.
* **`Theoria.md` process 3's 相关性聚类,一族留代表** (§7.9, L2161) — byte-exact
  against `Theoria.md` L327, half-width comma preserved — and notably *not*
  copied from `battery/REPORT_V2.md` L155, which renders the same phrase with a
  full-width comma. The paper went to the design document.
* **`battery/REPORT_V2.md`'s P3 sentence** (§7.2, L1755-1757) — byte-exact
  against L80-81, bold markers included, and correctly attributed with a path.
* **`battery/REPORT_V0.md`'s K4/K2 sentence** (§7.4, L1885-1887) — byte-exact
  against L25-26.
* **`battery/REPORT_V0.md`'s power floor** (§7.5, L1916-1920) — byte-exact
  against L40-43, all four lines, bold on **0.125** and **Six** included.
* **X3's `warning`** (§7.2, L1808-1809) — the ellipsis is honest: the source runs
  "…in the opposite direction to the one declared. **Either the definition is
  measuring something else, or the declared direction is wrong.** Do not use
  until resolved.", and the paper's `…` sits exactly where the dropped sentence
  is. Both quoted fragments byte-exact.
* **`battery/PREDICTIONS.md`** "a prediction that can be edited after the fact is
  not a prediction" (§7.3, L1826-1827) — exact against L5-6 modulo the
  sentence-initial capital, which is the standard fragment convention and is not
  counted here (see D4 for where it is, because that one is inside a blockquote).
* **`battery/REPORT_V2.md`** "a finding, not a failure of the prediction"
  (§7.3, L1834) and "the economy family collapsed to `no-data`" (§7.3,
  L1839-1840) — both exact substrings of L123 and L138.
* **`battery/artifacts/gaming_audit.json`** "K4 must never be reported without K2
  beside it" (§7.4, L1890) and `register confirmed by demonstration` (§7.4,
  L1892) — both byte-exact field values.
* **`battery/REPORT_V2.md`** "the single pair we withheld after checking that the
  manual already got it right" (§7.4, L1903-1904) — exact against L350-351,
  including the paper's correct decision to keep it in quotation marks as the
  exploit's *declared* frame.
* **`cold-start-a0/THEORIZE_LOG.md` R-05** — "the Button is presumably pressable
  from any of the four directions" (L1881-1882) and "not thin, zero" (L1883) —
  both byte-exact against L224-229.
* **`battery/artifacts/discrimination.json`'s `role`** (§7.6, L1948-1950) — "are
  confounded in different directions and disagreement between them is
  information rather than noise" is an exact substring of the field.
* **`battery/audit/v9/REPORT.md`** 这不是 37 个独立发现 (§7.7a, L2116) — exact,
  and correctly identified as a **section heading** (§6's title).
* **`battery/audit/v9/REPORT.md` §9(c)'s strength glosses** — 弱 ("weak"),
  中 ("medium"), 强 (§7.7a, L2106-2109) — the three labels and their nine
  members are exact.
* **`battery/artifacts/redundancy.json`'s `coverage_note`** (§7.9, L2199-2200) —
  "reflects thin data, not twenty independent findings" is an exact substring.
* **`baseline-arms/BUDGET_REPORT.md` §12.2** (§7.10a, L2256-2258) —
  「在 30 动作预算下**任何重复数都不能让它变得可比**——n 修不好一个没有信号的
  指标」 is byte-exact against L618-620 once the source's line wrap is unfolded,
  bold span and double em dash included; the paper starts at 在 rather than 而
  and drops the trailing 。, both inside an explicit 「」 fragment.
* **`exam/grading/mark.py`'s `confusion` docstring** (§8.1, L2375-2377) — "a
  framework that answers "unsolvable" to everything has perfect sensitivity and
  is worthless. Both numbers, always, or neither." is byte-exact against
  L100-101 (fragment start, double space collapsed).
* **`exam/grading/calibration.py`** "an uncalibrated marker's output is not a
  low-confidence result, it is not a result" (§8.2, L2383-2384) — exact against
  L41 modulo the sentence-initial capital.
* **`exam/DECISIONS.md` D-EX-011's `answer_labels` block** (§8.3, L2454-2457) —
  **byte-exact**, all four lines, italics and bold preserved. The best-transcribed
  passage in §8, and the only §8 blockquote whose source the section names.
* **`exam/DECISIONS.md`** "the static checks are necessary and cheap, and the
  adversarial reader is the one that found the leaks" (§8.3, L2462-2464) —
  exact substring of L259-260 (attributed as "the directory's own reading", with
  no path).
* **`exam/tests/test_core.py`** "a leak checker that cannot be made to fire is
  not a leak checker" (§8.3, L2467-2468) — exact against L4-5. "Opens with" is
  loose — it is the fourth line of the module docstring, not the first — but the
  string is right.
* **`exam/grading/calibration.py`'s trenchcoat paragraph** (§8.4, L2500-2503) —
  exact against L3-6 modulo the `--` → `—` normalisation and one collapsed
  double space. Unattributed by path, like the rest of §8's quotations, but
  transcribed faithfully.
* **`a0-spike/theory/theory.dsl`'s invariant** (§8.5, L2508-2509) — the inline
  `invariant box_row_parity (Box.pos.row) mod 2 = 1` and `[status: proven]` are
  byte-exact against L71.

---

## Regressions, and where §7's self-corrections land

`papers/phase1-workshop/CITECHECK.md` targeted a 1319-line draft that predates
most of §7; it has no findings inside this slice, so there is no inherited list
to dispose of. What §7 does have instead is an unusual density of **self-
corrections** — places where the paper explicitly overrides one of its own
sources. Every one of them was checked, and **all six hold**:

| the paper's correction | verdict |
|---|---|
| §7.1: only one of the seven artefacts carries provenance, "this paper had the stronger claim in it until the sentence was checked" | **holds** — 1 of 7 |
| §7.3: `REPORT_V2.md`'s "the economy family collapsed to `no-data`" is "right about the family's cost-bearing members and wrong as stated" | **holds** — 4 collapsed, 2 not-ranked, E4 underpowered with a real δ |
| §7.2a: the battery's flagship P3 sentence rests on δ (unpaired) while the pairing lives only in the sign test | **holds** — `stats.py` L64-66, and P3's sign test is 1/2/1 at p = 1.0 |
| §7.9: `REPORT_V2.md` says "three K-family clusters"; the artefact has two K-only clusters and three retirements | **holds** |
| §7.9: "the artefact does not flag that cluster by cluster, which is where this paper previously said it did" | **holds** — one global `coverage_note`, one `warning`, on the cross-family cluster alone |
| §7.10a: `REPORT_V2.md`'s v3 item 2 ("read the fields the model already carries") is out of date; all three fields are read now | **holds** — `Step.won`, `held_out_frame`, `Beat.env_actions` all gate a metric today |

The pattern that produces this slice's findings is the mirror image. §7's
corrections run *against* its sources and survive; §8's failures run *with* a
source and inherit its staleness — B1, B3 and B10 are all cases of the paper
faithfully reproducing an `exam/` self-description that the `exam/` tree has
since overtaken, and D1 is a case of inventing one. **§7 was audited against
artefacts and §8 was written from reports**, and the difference is visible in
every count above.

---

## What this audit could NOT check

Stated so the coverage claim above is not read as more than it is.

1. **Whether the battery's suite passes, or its artefacts regenerate.** §7.1's
   "byte-identical across two consecutive recomputes" and `battery/STATUS.md`'s
   "213 passed" were read, not executed. I did not run `python -m
   battery.run_battery` — and §7.7a says running it bare would overwrite
   `battery/artifacts/`, which is exactly the artefact set this audit is
   checking against. Every value in Pass B is the artefact's, not a re-derivation
   of the artefact.
2. **Whether the exam's build is reproducible.** `exam/artifacts/*.json` were
   read as they sit. I did not rebuild a paper, run `check_paper`, or re-mark a
   submission. B1's finding is that the artefact contradicts the paper *today*;
   whether a rebuild would change `label_sets_checked` again is not something
   this audit tested.
3. **The upstream Schema corpus.** Two of §7.2's figures — the 8-run arm's
   composition and the 197–564 model-call range — were checked only through
   `capability_spectrum.json`'s derived statistics. The payload itself
   (`baseline-arms/schema_traces/`) is gitignored, absent from this worktree, and
   under `D-B-020` only aggregate statistics may enter an artefact anyway. I did
   not look for it and could not have read it.
4. **Anything requiring sealed-pile material.** Two claims fall here.
   §7.10a's "**No arm in this repository has completed a level**" is a universal
   over the whole tree; I verified the four instruments the paper names
   (`ledger.jsonl`, the g50t run scorecard, the three ablation episode files, the
   a7 envelope) and the three non-zero values it concedes, but a sealed-game
   trajectory carrying a completion would not be visible to me **by rule**, and I
   did not sweep for one. Likewise §7.1's "zero sealed-pile reads" is the
   battery's own assertion in `REPORT_V2.md` L8-9; `capability_spectrum.json`'s
   `provenance.cut.dev_pile` lists the four permitted ids and every `game_id` in
   the 95 runs is one of them or `null`, which is as far as a reader inside the
   cut can go. **No sealed game's content was opened.**
5. **`arc-recon/data/piles.json` was hashed, never read.** The three digests in
   §7.10a were recomputed by feeding the file's bytes to `hashlib` and parsing
   it in memory to drop one field. Nothing from it was printed, summarised, or
   inspected beyond the digests and a CRLF count. Its sealed-game ids did not
   enter this report and were not looked at.
6. **Whether the eight Pass-A brace-expanded and section-implied paths are the
   ones the author meant.** `mark.py` resolves to exactly one file in the tree
   and the two brace forms expand to five files that all exist, so the
   resolutions are forced rather than guessed — but I did not confirm intent
   against a draft or a commit message.
7. **`exam/STATUS.md` was read only where a claim pointed into it.** It is 1121
   lines; I read the handover result (L157-169), weaknesses 10-14 (L263-300) and
   the cheater section (L116-146). A contradiction sitting in an unvisited
   paragraph would not appear here. The same caveat applies to
   `battery/PREDICTIONS.md` (603 lines, read at L5-11 and the v2 seal) and
   `exam/leakage.py` (read at its docstring, the five named functions, and
   `check_paper`). By contrast `battery/REPORT_V2.md`, `battery/audit/v9/REPORT.md`,
   `battery/PREREG_V9.md` §修订, `battery/BLINDING.md` §1-2 and
   `exam/DECISIONS.md` D-EX-009/010/011 **were** read in full or in the relevant
   whole section, which is how B4, B6 and B7 surfaced.
8. **The "~150" in the Pass B summary is a count of claims I opened a file for,
   not a claim of exhaustiveness.** It is the sum of the itemised figures in
   *Numbers checked and confirmed correct* plus the ten defects. §7 contains
   further arithmetic I treated as derived rather than cited — the 1/16
   quantisation, 19 − 13 = 6, 95 − 31 = 64, 38 × 95 = 3610 — which I checked but
   did not count as citations under test.

Both sibling reports were consulted for method. `citecheck-B-s4-to-s6.md` is
complete and its structure is followed here. `citecheck-A-abstract-to-s3.md` was
delivered incomplete and has since been redone. **The 43-line stub this file
replaces asserted a summary table with no findings behind it; its Pass A counts
were right and its Pass B, C and D counts were all too low.** Every count in the
summary above is derived from the enumerated rows in this document, and every
claim about a file's contents comes from having opened that file in this session.

---

## Where the stub's asserted counts were wrong

| measure | stub asserted | this audit found | note |
|---|---|---|---|
| A · distinct path-like tokens | 56 | **56** (57 extracted, 1 false positive) | correct |
| A · resolve as written | 53 | **53** | correct |
| A · section-implied base | 1 | **1** (`mark.py`) | correct |
| A · brace expansion | 2 | **2** | correct |
| A · do not exist | 0 | **0** | correct |
| B · claims checked | ~185 | **~150** | the stub's figure is not reproducible from any enumeration; mine is the sum of the rows above |
| B · wrong or mis-attributed | 6 | **10** | the stub missed B1, B2, B3 and B10 — the four §8 findings, which are the load-bearing ones |
| C · uncited numbers | 7 | **11** | |
| D · quotations checked | 21 | **31** | the slice has 9 blockquotes and 22 inline attributed fragments; 21 undercounts by ten |
| D · inexact | 4 | **6** | including D1, a quotation with no source anywhere in the repository |

The stub's line mapping was **correct** and is confirmed above by list-equality
against the section files, not assumed.
