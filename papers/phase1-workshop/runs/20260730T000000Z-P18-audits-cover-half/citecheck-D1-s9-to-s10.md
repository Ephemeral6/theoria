# CITECHECK slice D1 — §9 (the live chain) and §10 (the adjudication census)

**Audited state.** `papers/phase1-workshop/PAPER.md`, sha256
`6b633fcc35ae612f20f4028eb45aaca1b6ed86a24eb1304af555c46228325376`, 3729 lines
(newline bytes, `wc -l`), 237872 bytes. Measured in this run, not copied. Slice:
lines 2521-3197 (§9-§10). Auditor: CITECHECK re-run, P18, 2026-07-30. First audit
ever to read these two sections.

**Rule under test.** "Every quantitative claim carries the repo-relative path of
the artefact it came from." Four passes: path existence, number verification,
orphan numbers, quote fidelity. Precedence: JSON artefacts beat prose reports
(`papers/phase1-workshop/CITECHECK.md`).

**Line mapping — derived and verified empirically.** `assemble.py` writes a 2-line
banner (`<!-- GENERATED … -->\n\n`) and joins sections with `"\n\n---\n\n"`, so a
section ending on PAPER line *X* is followed by blank / `---` / blank and the next
section opens on *X+4*. Re-running the assembly in memory reproduces `PAPER.md`
byte-for-byte, and the first and last line of each section were compared against
the paper at the computed offsets (all 13 sections verified True):

| PAPER.md lines | section file | offset |
|---|---|---|
| 2521-2731 | `sections/09_preflight.md` 1-211 | `PAPER − 2520` |
| 2732-2734 | separator (blank, `---`, blank) | — |
| 2735-3194 | `sections/10_adjudication.md` 1-460 | `PAPER − 2734` |
| 3195-3197 | separator | — |

Every finding below gives both numbers. Note in passing: the brief's lead cited
"`sections/10_adjudication.md` L119/L123/L133" for PAPER L2853/L2857/L2869. The
first two are right; the third is L135. §10 is 460 section lines, not 463 — 463 is
the span including its two separators.

---

## Summary

| pass | measure | count |
|---|---|---|
| A | distinct path-like tokens cited in backticks | **62** |
| A | resolve as written, repo-relative from the worktree root | **53** |
| A | exist, but **only** under a section-implied base | **9** |
| A | do not exist anywhere in the tree | **0** |
| B | distinct numeric / field claims traced to a file and checked | **~150** |
| B | wrong, stale, mis-attributed, or not present in the cited file | **17** |
| C | quantitative claims with no artefact path at all | **10** |
| D | attributed quotations checked (2 blockquotes + 19 inline fragments) | **21** |
| D | inexact — paraphrase, dead string, or altered wording | **5** |

**Findings by severity: 5 high, 8 medium, 19 low (32 total).**

**Bottom line.** §9's arithmetic is in unusually good shape — the preflight and
first-contact manifests were opened field by field and essentially every number
in §9.1, §9.2 and §9.4 reproduces exactly, including the $6.317658 / $5.795338
disagreement, the 116 470 cache-creation tokens, the 83.6 % attribution and the
66/65 bypass ledger. §9's failures are citation-shaped: two blockquotes carry no
path at all and one of them is a paraphrase, and the sealing-scan paragraph
attributes the guard fingerprint to a manifest that has no guard block.

§10 is a different matter. Its *internal* census arithmetic is extraordinarily
accurate — 51 table rows, 11 prose paths, 40 rows against a stated 37, 8/7/6
exemplars, 20-row cap table, 13.1 % / 1680 / 92.9 % / 26.4 % / 1408 / 58 / 289,
0-of-2160 and 7200-of-7200, 14 of 19 mutants, and its own "eight occurrences of
verified" self-census all reproduce exactly, several of them only after
recomputation. But §10 has been overtaken by the repository it audits. **Two of
its load-bearing "not repaired" / "still open" claims were true at the section's
own base commit `32f078c2` and are false on the current mainline**, and both
became false through merges that landed after that commit. §10.5 diagnoses
precisely this failure mode in two other people's numbers ("one number has a
fixed method and a stale citation, the other a fixed method and a stale
artefact"); §10.2 and §10.4 are now the third and fourth instances, in the
section that names the disease.

---

## Sealed-pile discipline

**No sealed game is named anywhere in §9 or §10.** Every game id in the slice is
development-pile: `g50t-5849a774` (§9.1, §9.2, §9.4) and `ar25-0c556536` (§9.3,
via `replay_spotcheck_ar25.json`). The pile-cut fingerprint the slice reports
(`n_dev: 4`, `n_sealed: 21`, `unknown_policy: "deny"`) is a *count*, read from
`theoria-arm/runs/…/ledger.jsonl` `run_start.guard` and `run.json`; no sealed id
was read from `arc-recon/data/piles.json` and that file was not opened.

One disclosure, because §9 is a live-API section and the rule requires it:
`proxy/REDTEAM.md`, cited by §9.2 for the 46/29/4 attack figures, contains the
sealed short stem **`ls20`** at its line 74, as the label of test vector RED-20
("bare short id (`ls20`) is invisible to the guard"). I read that table row while
counting `| critical` rows; I did not follow it, did not open any `ls20` artefact,
and read nothing about that game's mechanics. `ls20` is one of the two games
CLAUDE.md already records as quarantined by F-11, so this is a re-encounter with
an already-disclosed identifier used as a guard fixture, not new contamination.
It is worth noting that the paper cites `proxy/REDTEAM.md` without warning a
referee that the file names sealed ids.

The four census reports state their own discipline: `SURVEY-success-as-truth.md`
line 116 — 封存堆零接触（未打开 21 局中任何一局的任何产物）— and
`SURVEY-empty-as-negative.md` line 5, 封存堆零接触. Both check out against their
contents; neither names a sealed id.

**No API call and no network access was made or needed.** Nothing in this slice
requires either: §9's claims are all recoverable from committed manifests,
ledgers and run.json files. That is itself worth recording as a positive — a live
section that is fully auditable offline.

---

## Pass A — path existence

62 distinct path-like backtick tokens in lines 2521-3197 (extraction scripted:
every backtick span, filtered to tokens containing `/` or ending in a known
extension, `:`-suffix line refs stripped, then `os.path.exists` at the worktree
root). **All 62 resolve to something in the tree; none is broken.** Nine are not
repo-relative as written.

| cited as | PAPER.md line(s) | section file:line | actually at |
|---|---|---|---|
| `SURVEY-solver-status.md` | 2767, 2778, 2792, 2813, 2927 | `10_adjudication.md`:33, 44, 58, 79, 193 | `papers/phase1-workshop/runs/20260729T140000Z-P14-honesty-section/inputs-verbatim/SURVEY-solver-status.md` |
| `SURVEY-empty-as-negative.md` | 2768, 2785, 2799, 2937 | `10_adjudication.md`:34, 51, 65, 203 | same directory |
| `SURVEY-environment-as-semantics.md` | 2769, 2782, 2796, 2814, 2913, 2929 | `10_adjudication.md`:35, 48, 62, 80, 179, 195 | same directory |
| `SURVEY-success-as-truth.md` | 2770, 2786, 2931 | `10_adjudication.md`:36, 52, 197 | same directory |
| `ground_truth.json` | 2861 | `10_adjudication.md`:127 | 41 tracked files carry the name; the same sentence cites `worldgen/out/worlds/`, which holds the 35 meant |
| `ladder.py` | 2948 | `10_adjudication.md`:214 | `engine-rig/bench/ladder.py`, cited in full nine lines earlier at L2939 |
| `p13_fd_dividend.py` | 3057 | `10_adjudication.md`:323 | `engine-rig/tools/p13_fd_dividend.py`, cited in full at L2841 |
| `potential.py` | 3021 | `10_adjudication.md`:287 | `engine-rig/engines/lp_potential/potential.py`, cited in full at L2899 and L2983 |
| `validate.py` | 2934, 2971 | `10_adjudication.md`:200, 237 | `engine-rig/engines/fd_adapter/validate.py` — but the **first** use (L2934, §10.3) precedes the full citation at L2968 by 34 lines, so a reader meeting it first has nothing to resolve it with |

The four `SURVEY-*.md` tokens are the interesting group. They are the section's
*primary* evidence, they are cited 18 times with line numbers, and they are named
as bare filenames throughout — including inside the §10.1 table, whose column is
headed "File". The `inputs-verbatim/` directory is cited in full five lines above
the table (L2762) and again at L3162, so a diligent reader resolves them; but §10.7
argues at length that citing a path a reader cannot reach is "the documentary form
of the error this section is about", and the bare filenames are a milder version
of the same thing. None of the four names is ambiguous in the tree — no other file
in the repository carries any of them — so this is cosmetic rather than
mis-resolvable.

`ladder.py`, `p13_fd_dividend.py`, `potential.py` and `validate.py` are each
unique in the tree (`git ls-files` gives exactly one hit for each), so none is
mis-resolvable either.

---

## Pass B — wrong, stale or mis-attributed numbers

### The four high-severity findings

| # | § | PAPER / section line | paper says | the artefact says | severity |
|---|---|---|---|---|---|
| **B1** | §10.2 | L2867-2870 / `10_adjudication.md`:133-136 | "This is the one of the four that is **not** repaired … the fix is filed as done on the internal work board while **the line stands byte-for-byte unchanged on the mainline**" | The line is gone. `worldgen/core/truth.py` was rewritten by V19 in two mainline commits — `23ec1793` ("worldgen: \"I could not check this\" was being written as \"this holds\"", 2026-07-29 07:28:58 +0800) and `abd9d47b` (08:18:19 +0800). Invariants now land in a three-class partition `holds / violated / unverified` (`INV_HOLDS`/`INV_VIOLATED`/`INV_UNVERIFIED`, lines 208-210), `classify_invariants` requires `status == "holds"` **and** `verified is True` **and** `holds is True` (lines 239-241), and `all_invariants_hold` reads the partition. `truth.py`'s own module docstring, lines 14-18, describes the old shape in the **past tense**: "It was a two-class boolean read with `.get(\"holds\", True)` **until V19**" | **high** |
| **B2** | §10.2 | L2857-2861 / :123-127 | "**Thirteen** worlds carry at least one unverified invariant and every one of them publishes the boolean as true … so it is **13 of 35**" | Recomputed independently, both ways. At the section's own base commit `32f078c2`: 35 `ground_truth.json` files, **13** with ≥1 invariant lacking a `holds` key and `invariants_all_hold: true` — the paper was exactly right then. On the current mainline: 35 files, `invariant_status.unverified == []` in **all 35**, `invariants_all_hold: true` in all 35, and **0** with any unverified invariant. It is now **0 of 35**. Every `GROUND_TRUTH.md` reads "N hold, 0 violated, 0 unverified" | **high** |
| **B3** | §10.2 | L2852-2854, L2862-2863 / :118-120, :128-129 | (a) "`worldgen/core/truth.py` **derives** a manifest-level claim as `\"invariants_all_hold\": all(i.get(\"holds\", True) for i in invariants)`"; (b) "the same module's Markdown renderer **prints** `_(prose only, unverified)_`" | (a) Present tense, and false. `truth.py:472` now reads `"invariants_all_hold": all_invariants_hold(invariants),` and publishes `"invariant_status": classify_invariants(invariants)` beside it (line 471). The quoted expression appears in `truth.py` only inside a docstring describing the defect it replaced. It **was** verbatim at `32f078c2:worldgen/core/truth.py:279`, which is also the line the census cites (`SURVEY-solver-status.md` U-2, `truth.py:279`). (b) The string `_(prose only, unverified)_` appears in **zero** files under `worldgen/` on the mainline: 0 of 35 `GROUND_TRUTH.md` files contain "prose only", and `to_markdown` now emits `_(**unverified** — %s)_` (line 559) with the note "prose only — no callable check, so this claim is …" (line 342). See D2 | **high** |
| **B4** | §10.4 | L3001-3010 / :267-276 | "**Still open:** … records that it did so in a `scope_exhaustive` field — which `Law.as_json` deliberately does **not** emit, because `candidates.jsonl` is sha256-pinned … **A reader of the published stream still cannot tell a proved `scope: \"global\"` from an unsearched one.** It is the clearest case the census found of a fix blocked by a release pin" | Closed by E15 (`99204472`, "E15 items 1+3: the status bit survives to the caller, and zero_space says when it degraded", 2026-07-29 12:50:22 +0800). `zerospace.py` now has a third scope value `UNDETERMINED` (line 43); `analyse` sets `quotient_scope = GLOBAL if not truncated_cells else UNDETERMINED` (line 300); and `Law.as_json` **does** emit degradation keys on a truncated row — `scope_proved: False`, `subset_enumeration_limit`, `truncated_cells`, an `error` string naming the cap, and a `scope_note` (lines 121-140). A truncated law is published as `undetermined`, not `global`, so a reader *can* tell them apart. The code's own comment states the mechanism: "until E15 it was published with `scope: \"global\"` … the affected representatives are now labelled `undetermined` and carry the cap in their own payload" (lines 245-250). The release pin turned out not to block the fix: un-truncated rows stay byte-identical, so nothing re-hashes. Only the *literal field name* claim survives — `Law.as_json` still does not emit a key spelled `scope_exhaustive`; `ZeroSpaceResult.as_json` does, at line 193 | **high** |

**On the timing of B1/B2/B4, which is the part that matters.** I checked ancestry
rather than dates. The section was written and re-verified at `32f078c2`
(2026-07-29 14:42:54 +0800; `papers/phase1-workshop/runs/20260729T140000Z-P14-honesty-section/reverification-at-32f078c.md`).
`git merge-base --is-ancestor` reports that **none** of `23ec1793`, `abd9d47b` or
`99204472` is an ancestor of `32f078c2`. So all three fixes existed as commits on
other branches at the time §10 was written but had not reached the tree the
section was verified against, and the section's own re-verification document
therefore confirmed the claims correctly. They arrived on the mainline afterwards.
The paper is not careless here; it is stale, and it is stale in exactly the way
§10.5 warns about — with the aggravating detail that §10.2's "byte-for-byte
unchanged on the mainline" is a claim *about the mainline*, which makes it the one
sentence in the section that a merge can falsify without anyone touching the paper.

**On the lead I was asked to test independently.** Confirmed, and stronger than
stated. The "13 of 35" is not merely arguable — it is **0 of 35**, recomputed from
all 35 artefacts; the "not repaired … byte-for-byte unchanged" is false; and the
`.get("holds", True)` expression and the `_(prose only, unverified)_` string that
the paragraph is built around are both absent from the file. There is one further
twist the lead did not mention: §10.2 says "the denominator is re-derived here,
**because the census never states one**". That is true of the census, but the file
the paragraph cites in the same breath states it outright —
`worldgen/core/truth.py:203` reads "**Thirteen of the thirty-five** shipped
`ground_truth.json` files said `invariants_all_hold: true` …". That sentence sits
eleven lines above the code the paper quotes, and it is written in the past tense
because V19 had already landed. Whoever last touched this paragraph read the file
at the old commit and did not re-read it.

### Medium

| # | § | PAPER / section line | paper says | the artefact says | severity |
|---|---|---|---|---|---|
| B5 | §9.2 | L2611-2614 / `09_preflight.md`:91-94 | the guard "reads the cut itself … and its fingerprint is recorded at run start: 4 development games, 21 sealed, `unknown_policy: \"deny\"`", inside a sentence whose only citation is `theoria-arm/runs/20260728T015354Z-g50t-first-contact/MANIFEST.json` | That manifest has **no guard block**. Its top-level keys are `arm, arm_version, base_commit, branch, budget, constraint_8, cost, files, game_id, ledger, outcome, prompt_id, provenance, reconciliation, run_id, scorecard, sealing, seed, seed_note, slug, stopped_because, surprises, upstream_pin, utc, world` — no `guard`, and `sealing` carries only the byte-scan counters. The fingerprint is real and exact, but it lives in `theoria-arm/runs/20260728T015354Z-g50t-first-contact/ledger.jsonl` `run_start.guard` and in `theoria-arm/runs/preflight-20260728T012057Z/run.json` `env_proxy.guard`. Neither file is cited anywhere in §9 | medium |
| B6 | §9.1 | L2556-2561 / :36-41 | "The API's own close response is the witness: `total_actions: 0`, `actions: 0`, `level_actions: [0,0,0,0,0,0,0]`, `score: 0.0`", cited to the preflight `MANIFEST.json` **and** `run.json` | All four values are correct, but they are only in `run.json` (`summary.scorecard_on_close`). The preflight `MANIFEST.json`'s `scorecard` field is `null`. Half the citation contributes nothing to the quartet | medium |
| B7 | §10.7 | L3169-3175 / :435-441 | "Between them they record **eight** corrections … **two** to the census reports themselves … **four** to the work item that commissioned this section … and **two** to downstream documents" | `evidence-survey-located.md`'s "Appendix — where the surveys are wrong, in one list" has exactly 8 rows ✓, but they split **3 / 4 / 1**, not 2 / 4 / 2. Rows 1, 2 and 7 target census reports (`SURVEY-success-as-truth.md:109-112`, `SURVEY-solver-status.md:16`, `SURVEY-environment-as-semantics.md:85-90`); rows 3-6 target the work item (`monitor/board/claimed/P14-honesty-section.RES-2.md`); row 8 targets `engine-rig/tests/test_tool_failure_is_not_truth.py:529-531`. `reverification-at-32f078c.md` adds one further correction ("One count corrected against the earlier audit") but that is a correction *to the audit*, not to the material | medium |
| B8 | §10.3 | L2929-2930 / :195-196 | "`SURVEY-environment-as-semantics.md:138-230` names **28 distinct Python sites**" | 27 by the natural count. Scripting distinct `.py` tokens over lines 138-230 gives 27 (`ablation-arm/verify.py`, `arc-recon/canary.py`, `arc-recon/client.py`, `arc-recon/precheck.py`, `bare_cc.py`, `baseline-arms/harness/campaign.py`, `bench/__main__.py`, `bench/ladder.py`, `bench/report.py`, `build_all.py`, `cold-start-a3/a3pipeline/certify_a3.py`, `cold-start-a3/a3pipeline/plan.py`, `engine-rig/bench/dividend.py`, `engine-rig/engines/fd_adapter/backends.py`, `fdrun.py`, `figures/sources.py`, `fuzzlab/props/finding.py`, `monitor/_runner.py`, `monitor/ci_merge.py`, `monitor/gates.py`, `proxy/forward.py`, `proxy/spend_gate.py`, `report.py`, `theoria-arm/harness/arc.py`, `theory-compiler/src/theory_compiler/deadlock_certificate.py`, `theory-compiler/tools/verify_c4.py`, `verify.py`). 28 requires counting `toolchain.probe`, which is a function name, not a Python site. The figure is not reproducible as stated | medium |
| B9 | §10.5 | L3022-3026 / :288-292 | "of 639 silences, **638 are still infeasible at bounds of 100, 10⁴ and 10⁶** and one is an artefact of a hard-coded weight box", cited to `engine-rig/ENGINE_TABLE.md` | Both numbers are right, but the bound triple is **not** in the cited file — `10⁴` occurs zero times in `ENGINE_TABLE.md`. Its source is `engine-rig/runs/20260729T000000Z-E11-engine-crosscheck-deep/partials/lp_potential-via-exhaustive.md:276` ("still infeasible at `bound = 100`, `10⁴`, `10⁶` \| 638"), with the weight box at `:264-267` and 639/2189 = 29.2 % at `:133`. `ENGINE_TABLE.md` carries 638 only in the Farkas sentence and 1 for the weight box, and its number registry (line 265, `lp.no_farkas`) points at the partials file — so the citation resolves through one indirection the paper does not name | medium |
| B10 | §10.7 | L3157-3158 / :423-424 | the census reports "are the primary evidence for **six** work items and for this section" | `inputs-verbatim/PROVENANCE.md` — the provenance document for the very copies §10.7 is describing — says **five**: "One machine-local copy was backing **five** work-board items and a section of this paper." `papers/…/RUN_STATE.md:107` says six. Two of the section's own run artefacts disagree and the paper follows the one it does not cite | medium |
| B11 | §10.6 | L3122 / :388 | "**Five** further overturns are on the record" | `engine-rig/runs/20260729T034043Z-E17-held-out-validation/CORRECTIONS.md` records **nine** (C1-C9), all marked SUSTAINED. Five is the count of non-minor ones excluding C1 (C2-C6; C7, C8 and C9 carry "SUSTAINED, minor"). The paper's number is defensible under that reading but the reading is not stated, and a referee counting headings gets nine | medium |
| B12 | §10.1 | L2772-2774 / :38-40 | "The obvious headline — around **340** points examined, **48** judged unsafe" | Both are right but the paper does not say what they are: `evidence-survey-located.md:26` establishes that 340/48 is a **three-pass** sum (`60 + 40 + 240 = 340`, `3 + 8 + 37 = 48`) and that "the fourth pass is the separate `105 / 8`". §10.1 presents 340/48 and 445/56 as rival totals of the same four columns, which makes the first look like a mis-addition of the table rather than a sum over a different set of passes. The 445 and 56 do check out (60+40+240+105, 3+8+37+8) | medium |

### Low

| # | § | PAPER / section line | finding |
|---|---|---|---|
| B13 | §9.1 | L2551-2554 / :31-34 | "The ledger holds **23** records:" followed by an enumeration of **21** — a scorecard open, 18 RESETs, and a two-try close. The `run_start` (seq 1) and `run_end` (seq 23) records are omitted. Both `MANIFEST.json` `ledger.records` and the file itself give 23; the colon promises a breakdown and delivers 21 |
| B14 | §9.1 | L2559 / :39 | "the cost block records `model_calls: 0`, `usd: 0.0`". There is no `cost.usd` field. The zeros are `cost.cli_reported_usd: 0.0` and `cost.from_price_table.usd: 0.0`; the same block's `verdict` string is a stale template asserting a DISAGREEMENT that does not exist at 0.0 vs 0.0 |
| B15 | §10.2 | L2847 / :113 | the repaired predicate is written `backends.proves_unsolvable(rung, returncode, log)`. The signature is `def proves_unsolvable(tier: str, returncode: int, log: str)` (`engine-rig/engines/fd_adapter/backends.py:239`) — the first parameter is `tier`, not `rung`. Presented in backticks as a signature |
| B16 | §10.1 / §10.3 | L2818 vs L2928 / :84 vs :194 | §10.1 says the prose paths are "over **10** distinct files"; §10.3 says "across **10** files". It is exactly 10 (11 path tokens, `backends.py` appearing twice — once bare, once in full). "over 10" is wrong by one in the direction that inflates |
| B17 | §9.4 | L2721 / :201 | "Correcting it takes the disagreement from 8.3 % to **1.35 %**". Arithmetic verified — (6.317658 − 5.795338 − 0.436763) / 6.317658 = 0.013543 — but no artefact carries 1.35 %; the paper computed it from three cited fields. Correct, and unlabelled as a derivation |
| B18 | §10.2 | L2894-2896 / :160-162 | "**39,960** well-formed states … **1,966** actions". `a0-spike/artifacts/a0_report.json` carries the bare integers `39960` and `1966`; the thousands separators are the paper's. Cosmetic, but the values are quoted as if read off the field |
| B19 | §10.3 | L2937 / :203 | "`SURVEY-empty-as-negative.md` opens with its summary table" (§10.1, L2785-2786 / :51-52). It opens with a prose 汇总 at lines 7-11; the first table is at line 16, under "## 不安全的". The substance — that the file states no criterion — is correct |

### Numbers checked and confirmed correct

Everything below was read from the named field, not from a report.

**§9.1** — `baseline-arms/BUDGET_REPORT.md:234` "4 个独立样本全部一致" ✓;
`theoria-arm/DECISIONS.md` D-P8-004 (four samples, two models, two games, failed
400s did not bill, RESET not gated) ✓; `proxy/scoring/arc_v1.py:19-20, 52-66`
extends 4 scorecards to 32 with "32/32 exact agreement" ✓; `g50t-5849a774` from
the development pile ✓ (`run.json` `game_id`); the superseded attempt
`preflight-20260728T012031Z` is 26 s earlier and holds exactly 2 records
(`run_start`, `env_meta`) ✓; 23 ledger records ✓; 18 `env_step` records with
statuses **17 × 400 + 1 × 200** ✓ (recounted); the 200 carries `n_frames: 1` and a
frames array of shape (1, 64, 64) ✓; close 404 then 200 ✓ (seq 21, 22);
`total_actions: 0` / `actions: 0` / `level_actions: [0,0,0,0,0,0,0]` / `score: 0.0`
✓; `has_score_field: false` and `envelope_keys` matching INC-TA-002's nine-key list
verbatim ✓; `successful_actions: 0` over `env_steps: 18` ✓; `model_calls: 0` ✓.
`arc-recon/precheck.py:76-77` `RESET_ATTEMPTS = 40` / `ACTION_ATTEMPTS = 40` ✓;
`proxy/forward.py` `max_attempts: int = 5` and `RETRY_STATUSES =
frozenset({429, 500, 502, 503, 504})`, which excludes 400 ✓ — so §9.1's finding 1
is exactly right, and `theoria-arm/RUN_STATE.md:30-33` says the same.

**§9.2** — `proxy/env_proxy.py:80-81` reads `ARC_API_KEY` and `VAULT.register`s it
✓; `proxy/redact.py:5-6` and `proxy/ledger.py:410` wire `VAULT.scrub()` ✓;
`proxy/tests/test_seal.py:61-79` — 401 direct, 200 through the proxy, on a request
the docstring calls "byte-identical to the one that just failed" ✓;
`proxy/mock/arm_mock.py:10` "refuses to start" ✓; `proxy/LEDGER_FORMAT.md:377-383`
records the RED-15 retraction and the surviving claim "A credential the proxies
injected cannot reach the ledger" ✓; `theoria-arm/armtools/archive.py:20`
advertises the sealing check in its docstring and `sealing(records, key_len:
int = 36)` accepts `key_len` and never uses it — I read the whole function body to
confirm ✓; the byte-scanning test is `test_arm.py:755` `assert DEFAULT_KEY not in
json.dumps(everything)`, inside `test_the_shell_turns_end_to_end_against_the_mock`
under `MockArc` ✓. First-contact `sealing` block: `game_ids_anywhere_in_the_records:
["g50t-5849a774"]`, `sealed_game_ids_found: []`, `sealed_pile_untouched: true`,
`cut_integrity: true` ✓ — and the preflight's `sealing` block indeed lacks all
four, carrying only the six counters ✓. Preflight counters `bypass_attempts: 0`,
`guard_blocks: 0`, `credential_in_body: 0`, `sealed_pile_requests: 0`,
`incidents: 0` ✓; all 18 steps `guard.decision: "allow"` ✓ (recounted).
`theoria-arm/evidence/model-proxy-401.jsonl` — 131 rows, **66** `bypass_attempt`
incidents and **65** `model_call` records all at 401, longest consecutive 401 run
= 65 ✓ exactly as claimed. `proxy/REDTEAM.md:13` "46 attacks were run. **29
landed, 17 were blocked.**" ✓, `:385` "All 46 attacks are now blocked" ✓, and
exactly **4** rows carry `| critical` (RED-01, RED-20, RED-24, RED-25) ✓.

**§9.3** — all 5 `model_call` records carry `proxied: false` ✓ (recounted from the
ledger); `theoria-arm/GAPS.md` GAP 1 ✓ including the bolded "No conclusion about
input-token composition may be drawn from this ledger", which the paper reproduces
verbatim; `proxy/spend_gate.py` keyword-only `permit` with no default and the
`TypeError` rationale ✓ (`forward.py:92-99`); the spend-gate manifest's `utc` is
`2026-07-28T08:42:54Z` and the preflight's is `2026-07-28T01:20:57.774Z` ✓; the
adversarial pass found the claim "false in **five** independent ways" ✓
(`ADVERSARIAL.md:5`); the file hashes do differ — recomputing the preflight's
22-file `upstream_pin` against the current tree (LF-normalised) gives 15 DIFF /
7 SAME, `proxy/forward.py` among the DIFFs ✓; and no run artefact mentions a
reservation ✓ (the one "permit"-substring hit in the preflight manifest is
"Constraint 8 permits a call there"). Replay: `n_sessions: 16`,
`pairwise_comparisons: 372`, `steps_compared: 9`, `disagreements: []`,
`game_id: "ar25-0c556536"`, `verdict: "PASS"` ✓ — and `proxy/DECISIONS.md:329-340`
carries both honesty rules (truncation at first failed step; agreement only where
≥2 sessions reach a position), the phrase "cross-session, cross-campaign
determinism **of the environment**", and "The acceptance line asks for two games;
this is the first" ✓.

**§9.4** — first-contact `budget.actions_ok: 7`, `commands_sent: 40`,
`cost.model_calls: 5`, `scorecard.score: 0.0`, `levels_completed: 0` of
`level_count: 7` ✓; GAP 2 (plan/commit reached, `no_goal_declared`,
"`execution_mismatch` surprise count is structurally zero on this run, not
measured-zero") ✓ and GAP 4 (`cegis_miner` produced zero `rule_hypothesis` rows)
✓; INC-TA-001 (two arms, one quota, `2026-07-28T01:28Z`, HTTP amplification
15-19 vs 5.07) ✓; INC-TA-005 ✓; and the cost block field by field —
`cli_reported_usd: 6.317658`, `from_price_table.usd_total: 5.795338`,
`relative_delta: -0.0827`, `delta_usd: -0.52232`, verdict string "DISAGREE by
-8.3%", `cache_ttl_diagnosis.cache_creation_1h_tokens: 116470`,
`cache_creation_5m_tokens: 0`, `under_billed_usd: 0.436763` ✓. 0.436763 / 0.52232
= 0.83621 → **83.6 %** ✓ recomputed.

**§10.1** — the four summary lines, at the exact cited lines:
`SURVEY-solver-status.md:16` 约 60 处 / 3 unsafe ✓ (criterion at :7-10, with
`Theoria.md:244` constraint 6 as baseline ✓);
`SURVEY-empty-as-negative.md:9` 约 40 处 / 8 ✓;
`SURVEY-environment-as-semantics.md:11-12` 约 240 处 / 37 ✓ (criterion at :6-7
naming crash / non-zero exit / timeout / decode failure / resource cap /
concurrency ✓); `SURVEY-success-as-truth.md:8` 约 105 处 / 8 ✓ (`:32-33` are the
table header and separator — columns, not a threshold ✓). 445 and 56 ✓;
53 = 56 − 3 ✓. `:274-376` contains 56 non-separator pipe lines of which 5 are
headers (at :280, :306, :325, :343, :357), so **51** data rows ✓ — recomputed.
`:367-374` contains 13 backtick spans of which **11** are paths over **10**
distinct files ✓ — recomputed; note the paper *corrected* its own source here,
`evidence-survey-located.md` appendix row 3 having said "13 CI paths". The three
unsafe tables in env-as-semantics enumerate 8 (:28-35) + 24 (:41-64) + 8 (:76-83)
= **40** against a stated 37 ✓ — recomputed. `:87-92`'s proposed rule ✓. The
overlap trio, all four line references checked open: `potential.py:170-171` 安全
at solver-status `:308` and unsafe at env-sem `:77` ✓;
`probe_frontier/reach.py:94-99` 安全 at `:290`, unsafe at `:80` ✓;
`cegis_miner/miner.py:323` 安全 at `:339` and «有旗标，但对错了尺子» at `:131` ✓.
"more than seventy sites" ✓ (114 distinct `file:line` tokens in the file).
"~45" is at `monitor/inbox/archive/20260729T063000Z-…:168-169` ✓ and appears in no
survey ✓; "~97" is at `…20260729T104500Z-…:100` ✓ and equals 105 − 8 ✓.

**§10.2** — `engine-rig/engines/fd_adapter/backends.py:74`
`FD_SEARCH_UNSOLVED_INCOMPLETE = 12` ✓; the defective line was
`unsolvable=done.returncode == 12,` at `p13_fd_dividend.py:129` in `cf400ce4` ✓
(character-for-character, including the absent spaces around `=`), and the current
line 171 reads `unsolvable=backends.proves_unsolvable(rung, done.returncode, log),`
✓. `a0-spike/pipeline/stages.py` — the split is real: `no_separating_guard` vs
`synthesis_crashed` (:209-211, :251-252, :283-291) and `all_guards_searched`
returns `not self.crashes` ✓ **verbatim** at :276-277.
`a0-spike/artifacts/a0_report.json` `mine`: `n_rules` 20 ✓, and exactly **twelve**
`blocked_<DIR>_1/_2/_3` rows (4 directions × 3) ✓ — enumerated; `reason`,
`no_separating_guard` and `synthesis_crashed` all absent from the whole file ✓.
`theoria-arm/inner/plan.py:26-37` ✓ and `:112, :157` — the "reachable set was
enumerated" line is now gated on `not crashed` ✓. `potential.py` — `LpUnavailable`
at :88, `solve_certificate` returns the certificate on `CERTIFIED`, `None` on
`NO_LINEAR_PAGODA` and raises otherwise (:432-441) ✓, message verbatim ✓.
`SURVEY-environment-as-semantics.md:37-64` is **24** rows of the opposite
direction ✓ and `:92-107`'s 丁组 closes with 方向是保守的 ✓.

**§10.3** — `:274-376` 51 rows / `:367-374` 11 paths ✓ (above);
`:113-134` is a **20**-row cap table (rows at 115-134) ✓ recounted;
`SURVEY-success-as-truth.md:43-79` has exactly **8** bulleted exemplars
(:48, :56, :61, :65, :68, :70, :73, :75) ✓ and `:81`'s 「验了但不独立」 section —
whose heading reads «这一格最容易被误读成安全» ✓ — has exactly **7** table rows
(:89-95) ✓, of which row d is `zerospace.py:194` and row a is `validate.py` ✓;
`SURVEY-empty-as-negative.md:30-58` has **6** numbered exemplars ✓.
`engine-rig/bench/ladder.py:77-80` returns `"proved_unsolvable": False` **and**
`"error": "over budget: %s"` in one dict ✓; `:98` `"proved_unsolvable": not
result.solved` is on the other branch ✓; `:226` publishes
`"stub_max_expansions": STUB_MAX_EXPANSIONS` ✓ and the comment at :47-50 says the
budget was "Chosen so the gripper ladder runs off the end of it inside this
batch" ✓; `:248` is quoted **verbatim**: `if row.get("error") and "over budget"
not in str(row["error"]):` ✓.

**§10.4** — `fd_adapter/__init__.py:140` `validate_plan(domain, problem,
plan.actions)   # never emit an unchecked plan`, unconditional, with the only
early returns at :117 and :128 both being `return None, result` no-plan paths ✓;
`validate.py` imports only from `engines.fd_adapter.pddl` — no `search` import ✓,
and its docstring at :9-16 names `pddl.ground_actions` as the shared premise and
says it "filters on static preconditions while instantiating" ✓;
`ladder.py:89, :131` call the validator directly ✓. **The census correction is
correct, and I verified it against the base commit rather than taking it on
trust**: `git cat-file -p 6ee0466:engine-rig/artifacts/candidates.jsonl` has 44
rows, row 21 (`lp_potential`, `heuristic`) carrying `"admissible": true` as a
literal *alongside* `"admissibility_check"`, and row 40 (`fd_adapter`, `plan`)
carrying `"plan_length_unchanged": true`. `SURVEY-success-as-truth.md:109-112`
claims grep for both is 0 hits and calls them 装好的雷、不是已爆的雷; that claim is
false, and false in the direction the paper says. `potential.py:544-562` now
derives `admissible` from `basis["admissible"]` and publishes `admissible_basis`
beside it ✓. `deadlock_carver/__init__.py` — `PruningReport.same_answer` at :75,
serialised as `"plan_length_unchanged": self.same_answer` at :123, docstring at
:200-201 confirming it was "published *next to* the very theorems it refutes" ✓;
now gated with `WITHHOLD` default, `refuted: True` under `MARK`, and
`invariants_withheld` counts travelling with the row (:208-258) ✓; and
`UnfinishedComparison` raised rather than folded (:50) ✓.
`SUBSET_ENUMERATION_LIMIT = 8` ✓ (but see B4).

**§10.5** — `engine-rig/ENGINE_TABLE.md` row 4: 639 / 2189 = **29.2 %** ✓, exactly
**1** silence is the `bound=10` weight box ✓, **638** rest on HiGHS float
infeasibility with no exact Farkas dual ✓; the reviewer's own reconstruction is
`partials/lp_potential-via-exhaustive.md:264-276` ✓ ("Rebuilding the LP myself for
all 639"). `engine-rig/runs/p13-fd-real/dividend.json` `cross_check` has **7**
rows, of which **3** carry `fd_unsolvable: true` ✓ — enumerated, and on all three
`stub_unsolvable` is also true and `agree` is true, with `fd_exit_code: 12` ✓.
`BLIND = "astar(blind())"` ✓ (`p13_fd_dividend.py:64`). The rig is not pinned to
blind search: `ladder.py:42-44` runs `lmcut`, `ipdb` and `fd-satisficing` ✓, and
`backends.py:59` `FD_DEFAULT_HEURISTIC = "lmcut"` ✓. "The artefact predates the
fix and was never regenerated" ✓ — `dividend.json`'s only commit is `cf400ce4`
(2026-07-28 09:44), the fixes are `2a1c30df` (07-29 06:12) and `c6a5b82a`
(07-29 10:27). "The evidence fields the fix introduced are absent from rows
written before it existed" ✓ — the current writer emits `fd_answered`, `fd_rung`
and `fd_exhausted_reported` (`:453-455`) and none of the three is in any committed
row. The retraction reproduces exactly against
`SURVEY-environment-as-semantics.md:85-90`, including the `%d`/`%s` mechanism, the
`:419-424` prose branch, the `:400-404` table branch that does print `None -> None`,
and 上表第 6 条按后者记 = "replaced rather than dropped" ✓. And the re-opening is
right: `json.dump` at `p13_fd_dividend.py:576` runs **before** `render(report)` at
:579 ✓.

**§10.6** — `ENGINE_TABLE.md` has exactly **8** engine rows ✓;
`engine-rig/tests/test_engine_table.py:101-106` asserts
`claims_held_out == (row["engine"] in {"`zero_space`", "`lp_potential`"})` — an iff
✓; "cannot fail by construction" is **verbatim** in `ENGINE_TABLE.md` row 3 ✓; the
grep result "0 命中" is at `SURVEY-success-as-truth.md:24` ✓. All eight held-out
numbers were read from
`engine-rig/runs/20260729T034043Z-E17-held-out-validation/results.json`, not from
the table: `Z-S2/global` laws 1680, delta_hit 220 → **13.1 %** ✓;
`Z-S2/cell_local` 6320/6800 → **92.9 %** ✓; `Z-S1/global` **100.0 %** ✓;
`lp.corpus.instances` **289** ✓; `held_out_L1.certificates` **1408** ✓,
`heldout_inv_closed_rate_pct` **26.4** ✓, `false_certificates` **58** ✓,
`emit_gate_let_through_reduced_graph` **1408** ✓,
`false_certificates_emitted_reduced_graph` **58** ✓, `emit_gate_let_through` **0**
✓; novelty `Z-S1` 0 novel of 2160 ✓, `Z-S2` 7200 of 7200 ✓. From
`ADVERSARIAL-heldout.md`: random 20/80 → **35.3 %** (:262) ✓, leave TWO ops out →
**2.0 %** (:264) ✓, cyclic → cell_local **100.0 %** / global **66.7 %** (:307) ✓.
`CORRECTIONS.md:164-166` "19 mutants, **14 survived** … nothing under `tests/`
imported it" ✓; C2 is the emit-gate-scored-against-the-complete-graph overturn ✓;
`RUN_STATE.md:25` and `:37` confirm item 3 was deliberately not done and would
"hand every future engine a 100 % hit rate that means…" ✓. Qualification 1 ✓ —
`zero_space/__init__.py:52` `if not verify(result, states):` passes the fitting
trajectory. Qualification 2 ✓ — `engine-rig/heldout/` is a new top-level package
and the only importers are `heldout/*` itself and one adversarial script; no file
under `engines/` imports it. **The self-census is exactly right**: recounting
"verified" (case-insensitive, including compounds) over the current `PAPER.md`
gives **eight** occurrences outside L2735-3194 — at L183, 438, 943, 963, 1691,
3488, 3656, 3721 — and each maps to the paper's own description: L183 the third
party's world model "verified by replaying the entire recorded history"; L438,
L943, L963 the certificate's own `verified` field; L1691 the pile digest; L3488
"cross-verified against two independent sources"; L3656 "no claim is made to have
verified any engine" (**verbatim**); L3721 the citation the paper declines. And
已验证 occurs **once** in the whole file, at L3149, inside this paragraph ✓.

**§10.7** — the provenance claim re-tested live, and it still holds: the branch
`agent/e11-engine-crosscheck-deep` exists locally, `git log --all` finds **no
commit** touching
`engine-rig/runs/20260729T000000Z-E11-engine-crosscheck-deep/SURVEY-solver-status.md`,
that run directory's `MANIFEST.json` contains **zero** occurrences of "SURVEY",
and the on-disk run directory in this worktree holds only `ADVERSARIAL-cegis.md`,
`ADVERSARIAL-zero_space.md`, `CROSSCHECK.md`, `MANIFEST.json` and `partials/` ✓.
The four `SURVEY-*.md` copies exist in `inputs-verbatim/` with the line counts
the located audit records (420 / 92 / 283 / 118) ✓.

---

## Pass C — orphan numbers

| # | § | PAPER / section line | the claim | what it would need | severity |
|---|---|---|---|---|---|
| C1 | §9.3 | L2669-2671 / `09_preflight.md`:149-151 | the closure blockquote, attributed only to "the one the track wrote for itself" | `proxy/DECISIONS.md:468-470`. No path anywhere in §9. This is the section's most quotable sentence and it is unciteable as printed. See D1 | **high** |
| C2 | §9.1 | L2545-2547 / :25-27 | the arm's docstring blockquote, attributed to "The arm's own docstring" | `theoria-arm/armtools/preflight.py:5-9`. `preflight.py` is named nowhere in §9 | medium |
| C3 | §9.2 | L2617-2620, L2624 / :97-100, :104 | "the sealing block reads `bypass_attempts: 0` … and every one of the 18 environment steps carries `guard.decision: \"allow\"`" | The counters are in the preflight `MANIFEST.json` (cited 60 lines earlier at L2560, in a different subsection); the per-step `guard.decision` values exist only in `theoria-arm/runs/preflight-20260728T012057Z/ledger.jsonl`, which §9 never names. §9 cites a *directory* for the ledger once (L2550) and the file never | medium |
| C4 | §9.3 | L2646-2648 / :126-128 | "it was wired at **08:42 Z**" and the quoted "was never pointed at a live upstream" | `proxy/runs/20260728T083000Z-s3/MANIFEST.json` (`utc`, and `money_spent.note`). Neither is cited; the paper's own `PROVENANCE.md:167` carries the path, so the information exists one file away | medium |
| C5 | §10.1 | L2772-2773 / :38-39 | "around 340 points examined, 48 judged unsafe" | A path. It is at `monitor/inbox/archive/20260729T063000Z-RES-3-the-pattern-you-named-appears-three-more-times.md:167-168`, which §10.1 cites **two sentences later** for the "~45" figure. Repairable in place | medium |
| C6 | §10.1 | L2821-2822 / :87-88 | "an enumerated **85 / 56**" and "the 85 omits the largest pass's positives entirely" | A path. `papers/phase1-workshop/runs/20260729T140000Z-P14-honesty-section/ADVERSARIAL_ROUND.md:16, :21` and `RUN_STATE.md:54-55`, both of which state it and neither of which is cited in §10.1 | medium |
| C7 | §9.3 | L2645 / :125 | "an adversarial pass that demonstrated and then fixed **five** bypasses" | `proxy/runs/20260728T083000Z-s3/ADVERSARIAL.md:5` | low |
| C8 | §10.6 | L3141-3142 / :407-408 | "The word occurs **eight** times outside this section" | A path. The number is a measurement of `PAPER.md` itself and the audit trail for it is `papers/…/reverification-at-32f078c.md:68-78` — which asserts **seven**. See the disagreement table | low |
| C9 | §9.4 | L2683-2685 / :163-165 | "the arm's own gap list says why … one engine contributed no rows at all" | `theoria-arm/GAPS.md` GAP 2 and GAP 4. The path appears 45 lines earlier at L2638; inherited rather than absent | low |
| C10 | §10.4 | L2989 / :255 | "at the census's own base commit the defective field was already sitting in the committed, sha256-pinned `candidates.jsonl`" | The commit. `6ee04667ca7e95619ca841e32947f8c87ea87dae` appears nowhere in §10; it is in `inputs-verbatim/PROVENANCE.md` and in each survey's header. A reader cannot check the strongest correction in §10.4 without finding the hash elsewhere | low |

Paragraphs that *look* orphaned but are not: §10.6's two held-out bullets
(L3088-3093) inherit the `engine-rig/ENGINE_TABLE.md` citation from the lead-in
two lines above; §10.2's §3.5 arm figures inherit
`a0-spike/artifacts/a0_report.json` from L2887; §9's "**Two** runs" (L2526) and
§10.1's "Four passes" are editorial counts, not measurements.

---

## Pass D — inexact quotes

21 attributed passages checked: 2 blockquotes and 19 inline attributed fragments.
Five are inexact.

| # | § | PAPER / section line | quoted as | source reads | problem |
|---|---|---|---|---|---|
| **D1** | §9.3 | L2669-2671 / `09_preflight.md`:149-151 | > the ledger is complete and self-consistent, and the arm cannot **write it** — but the operator can. Phase 1's "no bypass" **was always a claim about the** arm, and **that one still holds.** | `proxy/DECISIONS.md:468-470`: "**the ledger is complete and self-consistent, and the arm cannot write to it — but the operator can.** Phase 1's "no bypass" **property was always about the** arm, **and it holds.**" | **Three edits inside a two-sentence blockquote.** "cannot write **to** it" → "cannot write it" (drops the preposition, and with it the access-control reading); ""no bypass" **property** was always **about**" → ""no bypass" was always **a claim about**"; "**and it holds**" → "**and that one still holds**". Presented as a block quotation of "the one the track wrote for itself", with no path. This is a paraphrase set in quotation marks — the same category of error §10 exists to name | **high** |
| **D2** | §10.2 | L2862-2863 / `10_adjudication.md`:128-129 | "the same module's Markdown renderer **prints** `_(prose only, unverified)_` honestly" | The string occurs in no file under `worldgen/` on the mainline. `worldgen/core/truth.py`'s renderer now emits `_(**unverified** — %s)_` (:559) with the note "prose only — no callable check, so this claim is …" (:342), and 0 of 35 `GROUND_TRUTH.md` files contain "prose only" — all 35 read "N hold, 0 violated, 0 unverified". The string survives only in `truth.py:205`'s historical comment (unbacktick-ed, describing V19's motive), in `worldgen/runs/20260728T230307Z-V19-unverified-is-not-true/FLIPS.md:110`, and in `SURVEY-solver-status.md:137`, which attributes it to `truth.py:333-339` | **high** |
| D3 | §9.1 | L2545-2547 / :25-27 | > opening a scorecard, sending one RESET and closing again exercises every link in the live chain for zero quota: `arm -> env proxy -> key injection -> sealed-pile guard -> ARC -> ledger` | `theoria-arm/armtools/preflight.py:5-9`: "**So** opening a scorecard, sending one RESET and closing again exercises every link in the live chain for zero quota: / arm -> env proxy -> key injection -> sealed-pile guard -> ARC -> ledger" | Exact substring; the leading "So" is dropped without ellipsis. The chain line is character-perfect. No path (C2) | low |
| D4 | §10.2 | L2882 / :148 | "**every crash made the health certificate look cleaner.**" | `theoria-arm/inner/plan.py:34`: "Every crash made the health certificate look **better**." | Bolded rather than quoted, so not strictly a quotation — but it is one word away from verbatim, on a sentence the paper presents as the census's finding. "cleaner" for "better" | low |
| D5 | §10.6 | L3097-3099 / :363-365 | "The table's own standing rule is that a cell without held-out validation may say *self-consistent on the observed evidence* and may not say *verified*" | `engine-rig/ENGINE_TABLE.md:73-74`: "**Where no held-out validation exists, a cell may say 「在观测证据上自洽」 and may not say 「已验证」.**" | The rule is stated in the source only in Chinese; the paper renders both terms in English italics as if quoting. Faithful in meaning; not a transcription. (The same is true of §10.1's rendering of `SURVEY-empty-as-negative.md:91-92`, which is a good translation and is not presented as a quote) | low |

### Quotes verified exact

`proxy/LEDGER_FORMAT.md` §4 "a writer cannot redact what it has never been told
and cannot see" (source capitalises "A"; §4 confirmed by the surrounding `## 4.`
/ `## 5.` headings) · `proxy/runs/20260728T083000Z-s3/MANIFEST.json` "was never
pointed at a live upstream" (exact substring of `money_spent.note`) ·
`theoria-arm/GAPS.md` "no conclusion about input-token composition may be drawn
from this ledger" (bolded in both) · `engine-rig/engines/fd_adapter/backends.py`
`FD_SEARCH_UNSOLVED_INCOMPLETE = 12` · `engine-rig/tools/p13_fd_dividend.py`
`unsolvable=done.returncode == 12` (against `cf400ce4`, spacing included) ·
`worldgen/core/truth.py` `"invariants_all_hold": all(i.get("holds", True) for i
in invariants)` (against `32f078c2:worldgen/core/truth.py:279`, exact — the quote
is faithful to the commit and stale against the tree) ·
`a0-spike/pipeline/stages.py` `all_guards_searched` "returns `not self.crashes`"
(:277, exact) · `engine-rig/engines/lp_potential/potential.py:435-438` "this is a
fact about the solver, not about the configuration, so no unreachability claim
follows from it" (source capitalises "This") · `engine-rig/bench/ladder.py:248`
`if row.get("error") and "over budget" not in str(row["error"]):` (exact,
including both quote styles) · `engine-rig/ENGINE_TABLE.md` "cannot fail by
construction" · `papers/phase1-workshop/PAPER.md` L3656 "no claim is made to have
verified any engine" · `engine-rig/engines/fd_adapter/__init__.py:140`
`validate_plan(domain, problem, plan.actions)` · `SURVEY-environment-as-semantics.md:131`
「有旗标，但对错了尺子」 rendered as "mismeasured" (a gloss, correctly signalled
as one) · `engine-rig/engines/zero_space/zerospace.py` `scope_exhaustive` field
name (exists; see B4 for what it now means).

---

## Source disagreements

| # | the two files | what they disagree about | which the paper followed |
|---|---|---|---|
| 1 | `worldgen/core/truth.py` + `worldgen/out/worlds/*/` at `32f078c2` **vs** the same at mainline `HEAD` | 13 of 35 vs 0 of 35; `.get("holds", True)` vs a three-class partition; `_(prose only, unverified)_` vs `_(**unverified** — …)_` | **the base commit.** Correct at the time, false now. §10.2's "byte-for-byte unchanged on the mainline" is the sentence that cannot survive a merge, and it did not (B1, B2, B3, D2) |
| 2 | `engine-rig/engines/zero_space/zerospace.py` at `32f078c2` **vs** at mainline `HEAD` | `scope_exhaustive: bool = True` with "deliberately NOT in this payload yet" vs a third `UNDETERMINED` scope plus five conditional degradation keys | **the base commit** (B4). The paper's supporting citation, `engine-rig/runs/20260729T080000Z-C11-tool-failure-as-truth/CORRECTIONS.md:30`, records «已修：`truncated_cells` / `scope_exhaustive`（**未进 payload**）» and is itself the earlier of two documents on the same defect |
| 3 | `SURVEY-success-as-truth.md:109-112` **vs** `6ee0466:engine-rig/artifacts/candidates.jsonl` | census: grep for `admissible` / `plan_length_unchanged` is 0 hits, so the duals are 装好的雷; artefact: row 21 carries `"admissible": true` and row 40 `"plan_length_unchanged": true` at that very commit | **the artefact**, explicitly and correctly, with the direction of the error named ("wrong in the direction that understates the severity"). Independently reproduced here from `git cat-file`. This is the strongest single move in §10 |
| 4 | `papers/…/reverification-at-32f078c.md:68-78` **vs** `32f078c2:papers/phase1-workshop/PAPER.md` | the reverification "corrects" the count of "verified" from 8 to **7**, listing lines 177, 429, 922, 942, 1545, 2819, 2884, and asserts "The section quotes the corrected count" | **neither — and the paper is right.** Recounting at `32f078c2` gives **8**: the reverification's list omits L2651 ("Every citation in this section was cross-verified against two independent sources"). §10.6 says eight, which is correct at `32f078c2` and correct on the mainline. So the reverification's own claim that the section quotes seven is false, and its correction was a regression |
| 5 | `theoria-arm/INCIDENTS.md` INC-TA-005 **vs** `theoria-arm/runs/20260728T015354Z-g50t-first-contact/MANIFEST.json` | cache-creation tokens: the incident prints `cache_creation_input_tokens : 61,214`; the manifest's `cost.usage_total` and `cost.cache_ttl_diagnosis` both say **116470** | **the artefact** (§9.4 quotes 116 470). Correct under the precedence rule, but a referee reading INC-TA-005 — which §9.4 cites in the paragraph below — meets a number half the size with no reconciliation offered |
| 6 | `SURVEY-solver-status.md:16` **vs** its own `:274-376` and `:367-374` | 约 60 处 scanned vs 62 legitimate sites alone (51 + 11), 74 named in total | **the discrepancy is the finding**, and §10.1 reports it as one. §10.1 also silently corrects `evidence-survey-located.md`'s "13 CI paths" to 11, which is right |
| 7 | `inputs-verbatim/PROVENANCE.md` **vs** `papers/…/RUN_STATE.md:107` | five work-board items vs six | **RUN_STATE** (B10). §10.7 says six and cites neither |
| 8 | `SURVEY-environment-as-semantics.md:12` **vs** its own three unsafe tables | 37 unsafe vs 40 enumerated rows | **both, side by side**, which is the correct handling and is §10.1's second reason. Recomputed: 8 + 24 + 8 = 40 ✓ |

---

## What this slice establishes about the rule

Within §9 and §10 the binding rule fails in three distinct ways, and they are
worth separating because they need different repairs.

1. **Staleness, which the rule as written cannot catch.** B1, B2, B3, B4 and D2
   are all citations that were correct against the artefact at the commit they
   were checked at. The rule demands a path; it does not demand a commit. §10.4
   *does* pin one claim to "the census's own base commit" and is the more robust
   for it — but does not give the hash (C10). A rule that required
   `path @ commit` for any claim about the *current* state of a mutable file
   would have caught all five of these findings.
2. **Blockquotes exempting themselves.** Both blockquotes in §9 carry no path
   (C1, C2), and the one with no path is also the one that is a paraphrase (D1).
   The correlation is not an accident: an unciteable quote is an unchecked quote.
3. **Directory-level and section-level citation.** §9 cites
   `theoria-arm/runs/preflight-20260728T012057Z/` as a directory and then reports
   per-record HTTP statuses and per-step guard decisions from `ledger.jsonl`,
   which it never names (C3, B13). §9.2 attributes the guard fingerprint to a
   manifest that has no guard block (B5).

Against that, three things in this slice are better than the rest of the paper.
§10's number registry discipline is genuinely strong — `ENGINE_TABLE.md`'s
regex-and-path registry made eight of §10.6's figures re-derivable from
`results.json` in one pass, which is what the rule is *for*. §10.4's correction of
its own primary source, reproduced here from `git cat-file`, is the only place in
the audited paper where a prose report was checked against a pinned artefact and
overruled with the direction of the error stated. And §10.6's self-census of the
word "verified" is exact on eight of eight items, including the classification of
each — a claim I fully expected to break and which did not.

---

## What I could NOT check, and why

* **The originals of the four census reports.** They are untracked files in
  `.worktrees/e11-engine-crosscheck-deep/`, which is outside this worktree, and
  `git log --all` confirms they are on no ref. Everything in Passes A-D for §10
  was therefore checked against the `inputs-verbatim/` byte copies, which is what
  §10.7 says to do. I verified that the copies are the only reachable form and
  that the run's `MANIFEST.json` does not list them; I could **not**
  independently verify that the copies are byte-identical to the originals — that
  requires the other worktree. §10.7's own claim rests on
  `reverification-at-32f078c.md:60-67`, and I am taking it on trust.
* **Whether `ls20` appearing in `proxy/REDTEAM.md` is the only sealed id in the
  artefacts §9 cites.** I stopped at the one I met. Auditing this properly would
  mean grepping the sealed-pile list against the cited files, which means reading
  the sealed list, which the pile cut forbids. I chose the discipline over the
  completeness and am recording the gap.
* **`monitor/board/claimed/P14-honesty-section.RES-2.md`**, the work item §10.7
  says received four of the eight corrections. `git status` shows the
  `monitor/board/claimed/` tree has been substantially rewritten since (four files
  deleted on this branch), and the file is not present. I classified B7's split
  from `evidence-survey-located.md`'s appendix, which names the item and its line
  numbers, rather than from the item itself.
* **`SURVEY-*.md` line-anchor drift.** All 18 line references into the four
  surveys were checked and all 18 open on the right content — but the surveys are
  frozen copies, so this verifies the paper against a snapshot, not against a
  live file. That is by design and is a strength, not a gap; I note it only
  because the same cannot be said of the ~40 `path:line` references §10 makes into
  live source files, of which I checked the ~25 that carry a quantitative or
  quoted claim and did not check the rest.
* **Whether §10.2's "the fix is filed as done on the internal work board" was
  true when written.** The board item is not identified by path (part of C-class),
  and the `monitor/board/` tree is mid-rewrite. I verified the half of that
  sentence that is checkable (the mainline half) and it is false; the
  done-marker half I could not locate.
* **The three surprises / two unhandled and the desk-level figures in the
  first-contact run.** §9.4 declines to draw conclusions from them and makes no
  quantitative claim about them, so there was nothing to check. Noted so the
  absence is not read as an omission.
* **No API call, no network access, and none was needed.** Every §9 claim
  resolved against committed artefacts. If any had required a live call, that
  would be reported here as a finding; none did.

---

## Audit method

Pass A was scripted: every backtick span in PAPER.md lines 2521-3197, filtered to
tokens containing `/` or ending in one of 14 known extensions, `:`-suffixes
stripped, tested with `os.path.exists` from the worktree root and then against the
section-implied bases. Pass C was scripted the same way — the slice split into
paragraphs, every paragraph containing a digit tested for a path-like backtick
span, and the 25 hits read by hand to separate genuine orphans from headings and
from paragraphs inheriting a lead citation. Passes B and D were manual: every
cited artefact was opened and the value read from the named field, UTF-8
throughout (four of the five primary §10 sources are Chinese). Recomputed rather
than read: the 13-of-35 and 0-of-35 world censuses (both, from all 35
`ground_truth.json` files, at `32f078c2` and at `HEAD`); the 51 table rows and 11
prose paths in `SURVEY-solver-status.md`; the 40 unsafe rows and 20 cap rows in
`SURVEY-environment-as-semantics.md`; the 8 and 7 exemplar counts in
`SURVEY-success-as-truth.md`; the 6 in `SURVEY-empty-as-negative.md`; the 27/28
Python-site count; the 17×400 + 1×200 preflight status split and all 18
`guard.decision` values; the 66/65 bypass ledger; the 83.6 % and 1.35 % cost
arithmetic; the eight held-out figures from `results.json`; the eight "verified"
occurrences at two different commits; and the 22-file `upstream_pin` hash
comparison. Commit ancestry was tested with `git merge-base --is-ancestor`, not
inferred from dates. Scripts were run inline and not saved. Nothing outside this
file was modified.
