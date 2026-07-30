# delta-old-vs-new — what happened to every finding in the three stale audits

Reconciliation half of P18. Read-only pass: nothing in `PAPER.md`, `sections/`,
`CITECHECK.md`, `REVIEW.md` or any prior report was edited to produce this file.
No git write command was run.

## The four states

Every field below was recomputed this session (`sha256sum`, `wc -lc`, and
`git cat-file` over the full history of the blob), not copied from the audits.

| id | artefact | pinned to | `PAPER.md` sha256 | lines | bytes |
|---|---|---|---|---|---|
| **A** | `papers/phase1-workshop/CITECHECK.md` | **no commit named** — the file pins by hash only (L3–4) | `4208b69cdd6197a7b5f401223601a56b476d8c9a2f7a471b1412ab469c6dbd7d` | 1318 (`1319` as the audit counts it) | 75 885 |
| **B** | `papers/phase1-workshop/REVIEW.md` | commit `4959df1c` — **the same state as A** | `4208b69cdd6197a7b5f401223601a56b476d8c9a2f7a471b1412ab469c6dbd7d` | 1318 | 75 885 (11 451 words as B counts them) |
| **C** | `runs/20260728T173000Z-P12-paper-multi-review/review-d-adversarial.md` | commit `29f865d7`, `PAPER.md` v0.3 | `500867cdb66e38a258da51acde9ad0709242d8bb68e841b6f3c9f6acff6a8cbc` | 2572 | 157 782 |
| **now** | working tree, HEAD `0096a2c3cdd603b7574d75502115b3cc1d1e4442` | — | `6b633fcc35ae612f20f4028eb45aaca1b6ed86a24eb1304af555c46228325376` | 3729 | 237 872 |

**The pin holds.** `papers/phase1-workshop/PAPER.md` on disk hashes to
`6b633fcc…5376` at 3729 lines and 237 872 bytes — exactly the values this run was
given. Nothing below rests on a file that moved under it.

**Provenance of the three older rows.** C's sha, line count and byte count are
confirmed against the blob at commit `29f865d7` and against
`runs/20260728T173000Z-P12-paper-multi-review/MANIFEST.json`, whose `subject.sha256`
is `500867cd…`. (That manifest's own `base_commit` is `29f41ea4`; the note in it
records that `PAPER.md` is byte-identical at both, which the blob history confirms.)
`review-d-adversarial.md` itself states only "v0.3, 2 572 lines" — the hash and byte
count come from the manifest and the history, not from the review.

**A and B are pinned to the identical state, and the record about that is wrong in
two different directions.** `OPEN_ITEMS.md` L8–10 says "REVIEW.md was written
against a `PAPER.md` of 75,885 bytes; CITECHECK.md against one of 91,244", and
concludes "CITECHECK is the later of the two and is the review of record". That
conclusion does not survive: `CITECHECK.md` L3–4 records sha `4208b69c…`, which is
the 75 885-byte, 1318-line blob, byte for byte the state `REVIEW.md` L5 names.

But the *premise* is not fabricated either. A 91 244-byte state does exist — commit
`080f05da`, sha256 `112058bf…`, 1534 lines — and it is the very commit `OPEN_ITEMS.md`
credits four paragraphs later with closing four of REVIEW's six blocking issues.
So `OPEN_ITEMS` appears to have attached the post-repair state to the wrong audit.
An earlier draft of *this* file asserted flatly that "there is no 91 244-byte state
in the history of the file"; that assertion is withdrawn — the history above is the
check that should have been run before writing it.

One consequence that matters for reading A: `CITECHECK.md` L5–8 says the file was
edited *during* the audit and that §2.2, §5.4 and §6.7 were corrected mid-pass.
Those corrections are not in `4208b69c`. A's stamp therefore pins a state that
predates edits A says it watched, and a handful of A's rows (A-63, A-64 below)
describe text that only exists after the pin. This is not a defect in A's findings;
it is a defect in A's stamp, and it is why gate G of `verify_paper.py` still fails
on `CITECHECK.md` ("no ```audit-stamp block") in the run I made this session.

**Scale of the drift.** A and B saw 1318 lines; the paper is now 3729, a 2.83×
growth that added §6 (A3 transfer), §8 (the exam), §9 (the live chain) and §10 (the
census) wholesale, and renumbered every section from §6 onward. C saw 2572 lines:
in C's numbering §10 is Limitations and §11 is Related work, so C predates the
census too. Section identities quoted in the audits are therefore **not** the
section identities in the current paper:

| audit's § | what it was | where it is now |
|---|---|---|
| A/B §6 | the battery | §7 (L1669) |
| A/B §7 | limitations | §11 (L3198) |
| A/B §8 | related work | §12 (L3486) |
| C §10 | limitations | §11 (L3198) |
| C §10.5 | "The one thing this paper claims" | §11.5 (L3447) |
| C §11 | related work | §12 (L3486) |
| C §11.3 | "what the neighbours own" | §12.3 (L3702) |
| — | — | §10 (L2735) is new: the adjudication census |

The paper's **title and subtitle also changed**, which is load-bearing for C: C's
kill shot 5 attacks the title *"Certifying a world theory against something other
than its own past"*. The title is now **"Neither layer certifies the manual against
the world"** (L3), and the subtitle no longer names transfer or the exam (L5–7).

---

## Verdict vocabulary

Eight verdicts. Every row carries an anchor into the current `PAPER.md` — a line
number, or an explicit "no longer present".

| verdict | means |
|---|---|
| **fixed** | repaired; the anchor is the current text (or the commit) that repairs it |
| **partly-fixed** | the substance is addressed and a named part of the finding survives; both anchors given |
| **still-open** | the defect survives in text that has since been rewritten or renumbered around it; the audit's suggested fix was not made |
| **moved** | the defective text is *verbatim* what the audit quoted and nothing was done to it — only its address changed, so a reader following the audit's coordinates lands in the wrong place |
| **superseded** | a later audit, or a later state of the underlying artefact, re-examined it and reached a different verdict; the superseding thing is named |
| **withdrawn** | the finding was wrong when written; how I know is stated |
| **adjudicated** | still factually true, but a recorded ruling in the current tree holds it is not a defect; the ruling is named |
| **not-a-defect** | the audit's own row records it as already handled, or as an attack that does not land — kept in the count so the count is complete |
| **unverifiable** | cannot be checked now; the reason is stated |

`moved`, `still-open` and `partly-fixed` are all *open* in some form; the closing
section gives that combined number too.

**What is not tabulated, and why.** A's "Numbers checked and confirmed correct"
spot list (L113–183, roughly 100 figures) and the ~25 plain-**match** rows of B's
numbers table are *confirmations*, not findings. They assert nothing was wrong, so
there is nothing to reconcile. They are excluded from the count and named here so
the exclusion is visible rather than silent.

---

## A · `CITECHECK.md` — 66 rows

### A · Pass A — the 31 citations that were not repo-relative (A-1 … A-31)

Method: for each token, a scripted search of the current `PAPER.md` for the same
bare backtick span. `verify_paper.py` gate B was also run this session and reports
**225 distinct path citations, 215 ok, 10 ambiguous-but-ruled, 0 broken** — so the
replacements resolve; the rows below are about whether the *bare* form survives.

| # | cited as (A L58–88) | verdict | current `PAPER.md` |
|---|---|---|---|
| A-1 | `PROVENANCE.md` | fixed | no longer bare — L23 cites `papers/phase1-workshop/PROVENANCE.md` |
| A-2 | `theory.dsl` | adjudicated | still bare at **L3245**; gate F ruling (`11_limitations.md`): names the v0.1-grammar era, not one instance |
| A-3 | `playbook.dsl` | adjudicated | still bare at **L506**; gate F ruling (`02_framework.md`): names the *form*, pointing at `CONTRACTS/dsl_grammar_v0.1.md` |
| A-4 | `THEORIZE_LOG.md` | adjudicated | still bare at **L549**; gate F ruling (`02_framework.md`): indefinite article, "a `THEORIZE_LOG.md`" |
| A-5 | `raw_trace.jsonl` | fixed | no longer present as a bare token |
| A-6 | `theory/theory.dsl` | fixed | no longer present as a bare token |
| A-7 | `A0P_REPORT.md` | **still-open** | still bare at **L757** and **L3345** |
| A-8 | `prime_report.json` | **still-open** | still bare at **L829** |
| A-9 | `gen_lean.py` | **still-open** | still bare at **L997** |
| A-10 | `engines_diff.json` | fixed | full path at L1195, L1198 |
| A-11 | `trace_summary.json` | fixed | full path at L1159, L1196 — the `cold-start-a2/` one §5.2 meant; the `cold-start-a0/` homonym is written in full at L317 |
| A-12 | `artifacts/plan_holed.json` | fixed | full path at L1256 |
| A-13 | `theory/generated_holed/theory.lean` | fixed | full path at L1259, L1199 |
| A-14 | `A2_REPORT.md` | fixed | full path at L1264, L1280, L1351, L1371 |
| A-15 | `solved_episode.jsonl` | fixed | full path at L1264 |
| A-16 | `refute.py` | fixed | full path at L1302 |
| A-17 | `locate.py` | **still-open** | still bare at **L1309** — and beside it in the same sentence `cold-start-a2/a2pipeline/probe.py` is written in full, so the inconsistency is now visible in one line |
| A-18 | `probe.py` | fixed | full path at L1304, L1310, L1311 |
| A-19 | `artifacts/refutation.json` | fixed | full path at L1263, L1319 |
| A-20 | `artifacts/locate_report.json` | fixed | full path at L1320 |
| A-21 | `artifacts/probes.jsonl` | fixed | full path at L1321 |
| A-22 | `theory/theory_repaired.dsl` | fixed | full path at L1322, L1344 |
| A-23 | `artifacts/repair_report.json` | fixed | full path at L1323, L1348 |
| A-24 | `artifacts/plan_repaired.json` | fixed | full path at L1324 |
| A-25 | `artifacts/probe_report.json` | fixed | no longer present as a bare token |
| A-26 | `theory/generated_repaired_stale/` | fixed | full path at L1346 |
| A-27 | `generated_holed/theory.lean` | fixed | full path at L1199, L1259 |
| A-28 | `generated_repaired/theory.lean` | fixed | full path at L1359 (§5.6's diff block) |
| A-29 | `probed_trace.jsonl` | fixed | no longer present as a bare token |
| A-30 | `artifacts/engines_diff_probed.json` | fixed | no longer present as a bare token |
| A-31 | `run_battery.py` | fixed | no longer present as a bare token |

**A note the count would hide.** The rule has been *weakened* since A was written.
A tested "is this repo-relative"; the current gate F tests "is this bare filename
*ambiguous*", and passes an unambiguous bare name. A-7, A-8, A-9 and A-17 are all
unambiguous, so the gate is green over them while A's finding is still true of them.
Four of A's 31 remain open under A's rule and none under the rule now enforced.

### A · Wrong numbers (A-32 … A-41, plus A-66)

| # | A's finding (L100–111) | verdict | current `PAPER.md` |
|---|---|---|---|
| A-32 | §6.4/§7.4: "every discriminative verdict came back `underpowered` or `no-data`" is false — 5 are `not-ranked` (**high**) | fixed | **L3412–3415** (§11.4): "Every *ranked* metric's verdict … the other 7 in each case being direction-less diagnostics returned as `not-ranked`". §7.3 **L1840–1845** does the same for the economy family. Closed by commit `080f05d` per `OPEN_ITEMS.md` L14–17 |
| A-33 | Abstract/§1.2/§5.6: the two Lean files "differ in their weight table and in nothing else" is false (**high**) | fixed | **L1370–1382** — the paper now corrects its own source report by name and runs the diff. Abstract **L106–108** states only "identical in generator, tactic, dependency surface and axiom list". Closed by `080f05d` |
| A-34 | §3.4: 111 frames / 8991 px cited to `run_b.certify_cheap`, which is the bare boolean `true` | fixed | **L814–821** — the paper now says exactly this, in the artefact's own words, and explains why it is the one place a reader could suspect a thumb on the scale. Closed by `080f05d` |
| A-35 | §6.5: P1 "haiku 0.97 actions per call" — no aggregation yields 0.97 | fixed | the figure is gone. §7.6 **L1940–1962** reports P1 under battery v2; the only `0.97` left in the paper is a δ value at L1739 |
| A-36 | §7.3: "sound but incomplete" cited to `engine-rig/STATUS.md`, which does not contain it | fixed | **L3364–3367** cites `engine-rig/DECISIONS.md` D-014 and `engine-rig/interop/README.md`, and adds "the phrasing is `CLAUDE.md`'s" |
| A-37 | §7.3: "258 files" cited to `upstream_pin.json`, which pins 22 | fixed | **L3325–3328** — both numbers, each to its own source, with "the pin file does not carry it" said out loud |
| A-38 | §6.5: E5 "haiku $0.031/action" aggregated differently from its neighbours | fixed | the price list is gone; §7.6 **L1934–1938** reports E5 as a definitional artefact with no per-model prices |
| A-39 | §6.5: "Between **27 %** and 45 %" — the lower bound recomputes to 28.3 % | **still-open** | **L1942** still prints "between 27 % and 45 % of pilot steps failed outright". The sentence is now scoped to v0, but the number is stated as fact and the artefact gives 28.3 % |
| A-40 | §5.5: the `decide` quote is cut short in the JSON it is cited to | fixed | **L1346–1351** names the truncation (`"…proved that the proposition"`) and sends the full phrase to `A2_REPORT.md` §3 |
| A-41 | §3.1: 29 vs the log's 28 candidates (paper right, gap unexplained) | fixed | **L642–644** explains the gap inline: "it counts the 28 it adjudicated, the 29th row being a `plan`" |
| A-66 | *(sub-claim of A-33)* "`diff` of the two files: **70 diff lines**" | **withdrawn** | wrong when written. Run this session: `diff` gives **52** changed lines (25 insertions / 27 deletions by `git diff --numstat`), 7 unified hunks, 791 vs 789 lines. 70 does not reproduce under any reading — plain changed lines 52, whole `diff` output 82, `diff -u` ± lines 54, groups 15. A's *substance* (the files differ in more than the weight table) is confirmed and is what the paper now says |

### A · Uncited numbers (A-42 … A-48)

| # | A's finding (L191–197) | verdict | current `PAPER.md` |
|---|---|---|---|
| A-42 | §3.6's "−5 and −1" carries no path | fixed | **L880–881** cites `cold-start-a0/A0_REPORT.md` §8 |
| A-43 | §3.1's "about six seconds" carries no path | fixed | **L651–652** cites `cold-start-a0/A0_REPORT.md`, "preamble and §7" — the two places A said it actually lives |
| A-44 | §7.3's "258 files" needs `A2_REPORT.md` §7 | fixed | **L3327–3328** (same repair as A-37) |
| A-45 | §7.3's "1 (A2)" revision count: no file in the tree states it | fixed | **L3330–3335** now says exactly that — "no file in the tree states a revision count for A2 … so 'one revision' for A2 is this paper's reading of the ledger, not a figure it can cite" — and drops A2 from the enumerated list |
| A-46 | §6.5's "ρ = −0.83" is carried by no artefact | fixed | **L1956–1962**: "carried by no artefact in `battery/artifacts/` … quoted as a report's statement about v0", plus the v2 re-measurement (ρ = −0.899 over 82 shared runs) |
| A-47 | §2.5's "`Theoria.md` Phase 2 §Phase 1" is a malformed anchor | fixed | **L602** reads "(`Theoria.md`, Part 2, Phase 1)" |
| A-48 | the abstract takes an exemption the binding rule does not grant | fixed | **L23–25** grants it explicitly: "**The abstract is the one exemption, by convention** — and the exemption holds only because every figure below recurs, cited, in the body" |

### A · Inexact quotes (A-49 … A-56)

All eight re-read against the current text this session.

| # | A's finding (L214–221) | verdict | current `PAPER.md` |
|---|---|---|---|
| A-49 | §2.5 Phase-4 deliverables quote: punctuation silently normalised to full-width | fixed | **L612–613** now carries half-width `:` and `,`, matching the source |
| A-50 | §4.1 A1 孔明棋 quote: same normalisation | fixed | **L916–917** half-width throughout |
| A-51 | §4.1 "三个小检查代替无穷穷举，…": half-width `,` in source | fixed | the quote is no longer present anywhere in the paper |
| A-52 | §6.1 "同一本账，两次使用" | fixed | **L1673–1674** half-width |
| A-53 | §8.1 "若预测本身就是理解，第一波已经赢了" | fixed | **L3515** half-width |
| A-54 | §5.2 table: `"那条规则从未触发"` is a compression presented as a quotation | fixed | **L1196** quotes the source in full: 缺的那条传送规则从未触发 |
| A-55 | §5.2 table: `"重放全对"` is a compression | fixed | **L1198** quotes 模型重放 175/175 全对 |
| A-56 | §5.5: the `decide` phrase quoted accurately but from a different file | fixed | **L1348–1351** (same repair as A-40) |

### A · Source disagreements (A-57 … A-65)

Five of A's nine rows record dispositions A itself judged correct. They are kept
in the count because "the audit raised it" is the unit being reconciled.

| # | A's row (L259–267) | verdict | current `PAPER.md` |
|---|---|---|---|
| A-57 | `discrimination.json` vs `REPORT_V0.md` — paper followed the report | fixed | **L3412–3415** (see A-32); the artefact now wins, per the paper's own precedence rule |
| A-58 | `A2_REPORT.md` §4 vs the two `.lean` files — paper followed the report | fixed | **L1370–1382**: the paper diverges from the report and says why |
| A-59 | `exhibit_report.json` vs `A2_REPORT.md` on pixel counts — "handled correctly" | not-a-defect | still handled, **L1280–1282** |
| A-60 | `THEORIZE_LOG.md` Round 0 vs `candidates.jsonl` — 28 vs 29, "a reader will hit the gap" | fixed | **L643–644** closes the gap in the sentence itself |
| A-61 | `A0_REPORT.md` vs `STATUS.md`/`fd_real.json` on Fast Downward — "handled correctly" | not-a-defect | still handled, **L3372–3392**, which now cites all three disagreeing statements and says which is later |
| A-62 | `CLAUDE.md` vs `TOUCHED_GAMES.md` on `never_audited` — "handled correctly" | not-a-defect | still handled, §11.2 **L3287–3299** |
| A-63 | `CLAUDE.md` vs `engine-rig/STATUS.md` on engine count — "handled correctly in the current draft" | not-a-defect | still handled, §2.2 **L530–543**, which now also names `deadlock_carver` (see B-47) |
| A-64 | `CLAUDE.md` vs `piles.json` on the digest — "the artefact; §6.7 is exactly right" | not-a-defect | still handled, **L2310–2321**, which now also carries the third (CRLF) hash |
| A-65 | `CLAUDE.md` vs `DECISIONS.md` D-014 on `lp_potential` — "CLAUDE.md's wording, STATUS.md's path" | fixed | **L3364–3367** (see A-36) |

---

## B · `REVIEW.md` — 54 rows

`REVIEW.md` is now stamped `stale`, `superseded_by: REVIEW-2026-07-30.md`, and
covers 31.9 % of the current paper by bytes (75 885 / 237 872 = 31.90 % —
recomputed). Its findings about the text it read are not withdrawn by that stamp;
the rows below say what became of each.

### B · The fifteen major issues (B-1 … B-15)

| # | B's issue | verdict | current `PAPER.md` |
|---|---|---|---|
| B-1 | **[BLOCKING] 1** — the headline "pair" claim is false | fixed | **L1370–1382**; abstract **L106–108**. Closed by `080f05d`. C's disarmed-attack list item 2 independently confirms it as "comprehensively closed" |
| B-2 | **[BLOCKING] 2** — abstract's "no benchmark game was played for any result here" is false | fixed | the phrase is gone (0 hits). Abstract **L129–135** now says "No arm was run against another system's baseline … No game was played *for* this paper: the battery recomputes over trajectories that already existed" |
| B-3 | **[BLOCKING] 3** — "`locate.py` and `probe.py` import no world module at all" is falsified by one grep | fixed | **L1302–1315**: the paper states the defensible form first, then reports D-A2-010's error with the line numbers. Closed by `080f05d` |
| B-4 | **[BLOCKING] 4** — "named, with its three pairs" overstates R-05 | fixed | **L336–354**: "R-05 names three **directions** … It does not enumerate the coordinate pairs", and names the M6 gloss as a gloss. Abstract **L90** says "by direction" |
| B-5 | **[BLOCKING] 5** — §3.4 cites the wrong field and gets Run A's numbers | fixed | **L814–821**. Closed by `080f05d` |
| B-6 | **[BLOCKING] 6** — "every discriminative verdict…" is false | fixed | **L3412–3415**. Closed by `080f05d` |
| B-7 | **[SHOULD FIX] 7** — "diff the files and the deletion is the whole diff" is false | fixed | **L1236–1243**: "the deletion is the whole *substantive* diff, and the qualifier is needed because…", then the four other changes by name |
| B-8 | **[SHOULD FIX] 8** — the "controlled contrast" changes more than one variable; the outcome is entailed | fixed | heading **L719** is now "The A0/A0′ contrast, which is not controlled"; **L723–729** lists all four differing variables and says "'Identical except' would be a false description and is not used here"; **L772–788** supplies B's own sharper objection, analytic entailment, verbatim in substance |
| B-9 | **[SHOULD FIX] 9** — `zero_space` described two incompatible ways | fixed | **L3627–3635**: "A P-invariant is derived symbolically from the **rules**; `zero_space` reads **data**, so what it returns is an empirical regularity over one trajectory, not a symbolically derived invariant" |
| B-10 | **[SHOULD FIX] 10** — "independently developed track" / "independent adversarial review" overreach | fixed | **L953–959** ("A reader should not picture two teams … a *defence-in-depth* result, not an independent replication") and **L991–992** ("run inside the same project rather than by a third party") |
| B-11 | **[SHOULD FIX] 11** — E5 and K4/K2 are entailed by their definitions | fixed | **L1934–1938**: "E5 … is a price list, and that was deducible … reported because the audit acted on it, not because a pass discovered it". K2's n = 3 is in the abstract at **L89** and §7.4 at **L1874** |
| B-12 | **[SHOULD FIX] 12** — the FD paragraph implies A0/A0′ results ran on FD | fixed | **L3372–3392**: the `prefer="stub"` decision is stated, all three disagreeing repository statements are cited with their order, and `BLOCKER_FAST_DOWNWARD.md` is named twice |
| B-13 | **[SHOULD FIX] 13** — `CITECHECK.md` does not exist | fixed | it exists: `papers/phase1-workshop/CITECHECK.md`, 284 lines, read in full this session; cited at **L28** |
| B-14 | **[SHOULD FIX] 14** — novelty: the related work does not cite the literatures that own its results | fixed | §12.3 **L3702–3729** answers issue 14 by name; Angluin at **L794** and **L3713**, Chow's W-method at **L3717–3718**, version space and specification-validity at **L3605–3612** and **L3707**. Vasilevskii is deliberately *not* cited, with the reason given at **L3719–3722** |
| B-15 | **[SHOULD FIX] 15** — a Phase 4 conclusion drawn in a Phase 1 paper | fixed | **L2146–2148**: "This paper does not draw the conclusion … registered as **a confound to separate before Phase 4 freezes**, not as evidence about claim C2" |

### B · Issue 13's six reproducibility sub-bullets (B-16 … B-21)

| # | B's sub-bullet | verdict | current `PAPER.md` |
|---|---|---|---|
| B-16 | a Lean toolchain is required and the paper does not say so; and "eight invoke `lean`" is really 7/6 | fixed | **L980–986**: "**but only with a Lean toolchain on PATH** … without Lean the run is 75 passed, 8 skipped and the empty-axiom-list claim evaporates into skips". The "eight of which invoke `lean` … and read `#print axioms`" claim is gone |
| B-17 | the determinism claim is not tested on the published artefacts; D-B-008, not D-B-001 | fixed | **L1697–1704**: "The determinism *test* runs against a synthetic fixture rather than against the published artefacts (`battery/DECISIONS.md` D-B-008; earlier drafts cited D-B-001, which is about the pile guardrail)" — and adds a gitignored-payload caveat B did not find |
| B-18 | the pile hash reproduces only after LF normalisation | fixed | **L2310–2321** reports all three hashes, explains the CRLF mechanism and names 111 CRLF pairs |
| B-19 | the seal is a declaration, not a control | fixed | **L355–361**: "That stamp is a declaration written by the authors' own script, not a control" |
| B-20 | no figure is cited; two payload fields hard-coded against their docstrings | **partly-fixed** | *citation half fixed*: Figures 1–3 are cited at **L654**, **L731**, **L1294**. *Hard-coding half superseded*: the paper no longer cites its local `fig1/fig2/fig3` extractors at all — it cites the repo-root pipeline (`figures/fig05–07`, ruled by gate B against `figures/PARITY.md`), and **L735–737** discloses the one cell the source registry cannot hash rather than printing a hard-coded 0. B's finding is about scripts the paper has stopped citing; the two local scripts are still in the tree |
| B-21 | submission mechanics: 11 451 words vs a ~4 000 budget; 17 `[bib: TODO]`; placeholder authorship; `runs/` holds one file | **partly-fixed** | *bib fixed* — 0 `[bib: TODO]` markers remain and `references.bib` exists (832 lines). *`runs/` fixed* — 17 run directories. *Length worse* — **L14** self-reports "roughly 27 500 words … about six times a workshop budget"; `verify_paper.py` gate A, run this session, counts **36 256**. The paper's own verifier and the paper's own draft note disagree by 32 % about the paper's length. *Authorship still-open* — **L9** is `⟨AUTHOR PLACEHOLDER⟩` |

### B · The numbers table — the fourteen non-match rows (B-22 … B-35)

| # | B's row (L426–468) | verdict | current `PAPER.md` |
|---|---|---|---|
| B-22 | A0 accuracy — match, "n = 3 undisclosed in abstract" | fixed | abstract **L89**: "on those three its accuracy is 0.000 (n = 3)" |
| B-23 | A0/A0′ table — "47 % of A0's coverage" is 47 % of A0′'s *own* 228 pairs | fixed | **L744** the table row is labelled state-action coverage, `107/228 = 47 %`; abstract **L93–94** says "covering only 47 % of its own state-action pairs" |
| B-24 | MDL segmentation — stale, the artefact now says 5704 / 6 tracks | fixed | **L714–717** discloses both and says which the adjudication was made from |
| B-25 | per-object accounts — Cart +2967 stale against `concept_accounts.json`'s 2125 | **partly-fixed** | **L870–872** now qualifies the figure ("on the pixel baseline in force at adjudication time") and cites `A0_REPORT.md` §4 / `THEORIZE_LOG.md` O-04 rather than the JSON. The revised Cart figure is still not printed anywhere, and `PROVENANCE.md:42` still cites `concept_accounts.json` for +2967 |
| B-26 | A2 anomaly "cap" — match in substance, misleading as phrased (cap is 40, binds two of three kinds, 44 = 40 + 4) | **still-open** | **L1276** still reads "the cheap layer caps its anomaly list" with 44 beside it and no cap value |
| B-27 | loop ledger — the `authority` field cites INC-004 only, not D-A2-001 | not-a-defect | **confirmed true of the artefact** — I opened `cold-start-a2/artifacts/loop_ledger.json` this session; `authority` names only the INC-004 ruling. But no sentence of the current `PAPER.md` asserts otherwise: D-A2-001 is cited at **L1122** and **L1175** for the substitution ruling, not for the ledger |
| B-28 | A1 E-06 — D-014 is about the 4-cell fixture; the tighter cite is the test | superseded | E-06 has since been **discharged**: **L3353–3357** cites `theory-compiler/STATUS.md` E-06 and `THEORIZE_LOG.md` E-06 "**discharged**", records D-TC-010's supersession by D-TC-022, and §4.4 (**L1000**+) reports the closure. The citation B wanted tightened is no longer the one carrying the claim |
| B-29 | `METRICS.md`/`DECISIONS.md` say "twenty-eight" against a 29-entry registry | superseded | the registry is now **38** metrics (**L3413**); "twenty-eight" appears nowhere in the paper. The repo-side stale string is outside this paper's surface |
| B-30 | sign-test floor — `min_attainable_p` is on 11 of 29 metrics, nested, not "per metric" | fixed | **L3418–3421** derives the floor from the design rather than from a field: "a two-sided sign test over four paired games has a smallest attainable p of **0.125**" |
| B-31 | P1 confound — haiku 0.9606 not 0.97; the 27 % lower bound does not reproduce | **partly-fixed** | 0.97 is gone; **27 % survives at L1942** (= A-39) |
| B-32 | E5 "9× spread" is a rounding artefact (true ratio 8.80×) | fixed | the price list and the "9×" claim are both gone; the only `9×` left in the paper is "9×9 world" |
| B-33 | E2 — "three pre-registered primary endpoints" is `REPORT_V0.md`'s phrasing, not `PREDICTIONS.md`'s | fixed | **L2138–2140** attributes it to `battery/REPORT_V0.md` |
| B-34 | X5 cross-check — "independent … pinned by a test" is overstated | fixed | **L316–321**: "Both counts descend from the same explorer, so this makes the identity auditable rather than independently confirmed" — and cites `REVIEW.md` for the finding |
| B-35 | baseline pilot — 109 actions not reconstructible from the printed rows, which sum to 107 | **still-open** | **L3291–3293** still prints "12 cells (4 games × 3 models) plus 2 reruns, 109 successful actions" with no note that the source table's own rows sum to 107 |

### B · The eighteen minor issues (B-36 … B-53)

| # | B's minor (L474–521) | verdict | current `PAPER.md` |
|---|---|---|---|
| B-36 | `CITECHECK.md` absent; `runs/` holds one file | fixed | the file exists (284 lines); `runs/` holds 17 directories |
| B-37 | no figure is cited in the text | fixed | **L654**, **L731**, **L1294** |
| B-38 | `PROVENANCE.md:60` cites the wrong `certificate.py` path | fixed | `PROVENANCE.md:60` now reads `theory-compiler/src/theory_compiler/certificate.py` (read this session); the paper carries the same full path at **L964** |
| B-39 | `PROVENANCE.md:41` cites the segmentation bits to O-03; they are in O-01 | fixed | `PROVENANCE.md:41` now cites `cold-start-a0/THEORIZE_LOG.md D-A0-007 §Segmentation operator`; the O-03 miscite is gone. *Caveat: I did not open `THEORIZE_LOG.md` to confirm D-A0-007 carries the bits, so the replacement citation is unverified by me* |
| B-40 | §6.1 cites D-B-001 for determinism; it is D-B-008 | fixed | **L1699–1700**, which names the earlier miscitation explicitly |
| B-41 | §4.2 cites (D4) for the vector `[1,2,3,2,1]`; D4 never names it | fixed | **L976–979** — D4 now attaches to "hand-computed and typed in as literal constants", which is what D4 supports |
| B-42 | §3.1's "about six seconds" is mis-anchored | fixed | **L651–652** (= A-43) |
| B-43 | §1.1's seal gloss says "after both certify layers and the plan were green" | fixed | **L356–357**: "after M4 and M5 were green — M5 being the unsolvable-variant milestone, not a planning stage" |
| B-44 | §3.3's table calls A0's explorer "exhaustive" one row above 99 % coverage | **moved** | verbatim and unrepaired: "exhaustive" at **L743**, `233/236 = **99 %**` at **L744** |
| B-45 | §3.3 renders the same fraction two ways one line apart | **moved** | verbatim and unrepaired: 99 % at **L744**, 98.73 % at **L746** |
| B-46 | §3.5's "the other track" has no antecedent | **moved** | verbatim and unrepaired at **L842**; the paper still never says which track owns `cold-start-a0` or `theory-compiler` |
| B-47 | `deadlock_carver` is shipped and appears nowhere | fixed | **L535–537** names it beside `ic3_pdr` as an M9 addition not exercised by any result |
| B-48 | §3.5's a0-spike corroboration is about reachability, not reversibility; "same conclusion by a different route" is too strong | **moved** | verbatim and unrepaired at **L844–845** |
| B-49 | §7.1(c): the precheck numbers should be in the sentence | fixed | §11.1(c) **L3229–3234** carries them — "9/9, 3/3, 9/9, 9/9" — with the hedge B endorsed |
| B-50 | the abstract's "caught independently by a coverage probe and by the Lean transcription" drops §3.4's qualification | fixed | abstract **L96–97**: "caught by a coverage probe and, **unplanned**, by the Lean transcription" |
| B-51 | `arc-recon/README.md:185` still says all 25 are `never_audited`; §7.2 corrects `CLAUDE.md` but not this | **partly-fixed** | **L1143–1145** now cites `arc-recon/README.md`'s contamination register for INC-004's correction of DC22's level. But §11.2 (**L3287–3299**) still names only `CLAUDE.md` as the summary being corrected, so B's consistency point stands |
| B-52 | `METRICS.md:7` / `battery/DECISIONS.md:122` say "twenty-eight" | superseded | *duplicate of B-35's neighbour row B-29* — B records this finding twice, once in the numbers table and once as a minor. Both are superseded by the move to 38 metrics |
| B-53 | typography: mixed `·`/`—` separators; 重证 glossed two ways | **still-open** | 重证 is "re-certify" at **L416** and "re-proof" at **L1323** |

### B · One sub-claim that was wrong when written (B-54)

| # | B's sub-claim | verdict | evidence |
|---|---|---|---|
| B-54 | issue 1: "returns **52 changed lines across 7 hunks** … **Only 14 of them are the weight table**" | **withdrawn** (the arithmetic only) | 52 and 7 reproduce exactly (`diff`, run this session). "Only 14" does not: **28** of the 52 changed lines are weight-table lines — 14 entries, each a removed line against its replacement. B counted entries and reported lines. The current paper gets this right and says why: **L1378–1379**, "Twenty-eight of the 52 are the weight table — fourteen entries … which is why the entry count and the line count are not the same number." B's substantive finding is unaffected and is B-1 |

---

## C · `review-d-adversarial.md` — 19 rows

C ran against a state that already had B's four blocking fixes in it, and its
remit was attackability only. Its own summary table (L610–631) is the row list.

| # | C's finding | severity | verdict | current `PAPER.md` |
|---|---|---|---|---|
| **F1** | title/abstract promise transfer + exam; §10.5 disclaims both | blocking | fixed | the subtitle (**L5–7**) no longer names transfer or the exam; the abstract's scope paragraph (**L140–141**) says "Transfer, the exam, the ordering claim, the bill shape and the cost magnitude are **reported here and claimed nowhere**"; §11.5's disclaimer (**L3481–3482**) now agrees with it instead of contradicting it. §6 and §8 are introduced at **L112** as "The remaining sections report, without claiming" |
| **F2** | §10.5 restores "controlled", "independently developed", "predicted in advance" | blocking | **partly-fixed** | two of three repaired in §11.5: **L3461–3463** "an A0/A0′ contrast which is **not** controlled — the two worlds differ in mechanism, rule count, state count and explorer budget at once, so the outcome is entailed by the construction (§3.3)"; **L3465** "two sessions that do not import each other's code". **The third survives: L3460 still reads "predicted in advance and later measured", unqualified**, while L360–361 calls the seal "a declaration written by the authors' own script, not a control". C's sweep of the *class* did land elsewhere — the §3.3 heading is now "which is not controlled" (L719) and §1.5 says "**uncontrolled by construction**" (L424); the one remaining "controlled" at L836 is a different and legitimate use (§3.4's seeded-error experiment) |
| **F3** | "Eight results." vs §11.3's own instruction to the abstract | blocking | fixed | the phrase is gone (0 hits); the abstract now leads with **L54–59** "**The one thing this paper claims is that we built that instrument…** That is a claim about an artefact and a negative result about a measuring instrument. It is not a result about world models." The instruction C quoted still stands, now at §12.3 **L3724–3729** |
| **F4** | "No arm was run against a baseline" vs §6.1's three arms | major | fixed | **L129–131**: "No arm was run against **another system's** baseline, there is no language-model baseline anywhere in this paper, and the three arms of the transfer section are all ours". Repeated at **L478–479** |
| **F5** | §7.10 "still no multi-level run"; §6 is a multi-level run | major | **moved** | verbatim and unrepaired at **L2223**. C's suggested qualifier ("in the ledger the battery reads") was not added |
| **F6** | §5.2's heading argues the forced substitution improved the result | major | **moved** | verbatim and unrepaired at **L1147**: "### 5.2 Why the substitution can make the claim stronger, not weaker". C's second half partly landed — the isomorphism table (**L1193–1200**) now names each check's kind and artefact per row — but the heading, which is what C said "gets read aloud in a rejection", is untouched |
| **F7** | §4 reads as a headline; `Theoria.md` calls A1 plumbing | minor | fixed | **L916–917** quotes `Theoria.md`'s 判死赌的是管线接通,不是 LLM 灵感 verbatim and **L921–922** glosses it; and the abstract no longer numbers A1 as a result |
| **F8** | the title vs the inventory of self-authored ground truth | blocking | fixed | the title changed. **L3** is now "Neither layer certifies the manual against the world" — a claim about the instrument's limit, not a promise of external certification — and it is restated as the thesis at **L54** and **L579**. C asked for a retitle or a reconciling sentence; the paper took the retitle and went further than the version C proposed |
| **F9** | §2.4's "not a success metric of its own choosing" refutes itself | major | **moved** | verbatim and unrepaired at **L592–593** |
| **F10** | the exam's only real sitting is the system grading itself; the readers are never named | major | **still-open** | **L2402–2404** still reads "Two fresh subagent readers, given a bundle and a sheet and nothing else, each scored 46.0/46.0" with no statement of what they were. §8.4 (**L2476–2495**) lists six things the exam does not establish and this is not among them. C's fix was one clause; it was not made |
| **F11** | the anti-gaming audit is self-written, and says so | minor | not-a-defect | C's own verdict: "I tried this attack and it does not land." The disclosure is stronger now — §7.7a **L2110–2113** adds that the strength grading "lives in prose and no artefact carries it" |
| **F12** | the blind control's canonicaliser provenance is unstated | minor | **still-open** | **L1595–1599** still reports "0 % of clauses as written, and … all 20 of L1's clauses once canonicalised" without saying who wrote the canonicaliser or when relative to the blind arm's output |
| **F13** | §6.2's bill: definitional zeros printed as a measurement, over a denominator the paper calls unrealistic | blocking | **partly-fixed** | the *accuracy* half is now handled well — **L1531–1543** prints the control arm's 252/252 beside the transfer arm's and says "**on accuracy the two arms are tied at ceiling, and this measurement cannot separate transfer from induction at all**". The *bill* half is not: **L1501–1504** still tabulates the four zeros and **L1507–1511** still opens "The zeros are the interesting column", with no sentence saying they are entailments of the arm's definition. §6.5 item 3 (**L1624–1626**) concedes the cold-start denominator is an upper bound and item 4 (**L1627–1631**) that the bill is structural, but both are 120 lines below the table. The abstract still carries "wins with zero engine stages and zero adjudicated candidates" at **L115–116** |
| **F14** | every experiment is n = 1; said seven times, never once cumulatively | major | **still-open** | `n = 1` appears exactly twice in the whole paper — **L773** (A0/A0′ per arm) and **L2480** (per handover tier). The cumulative sentence C asked for in §10.3 is not in §11.3 or anywhere else |
| **F15** | K2 = 0.000 to three decimals over n = 3 | — | not-a-defect | C's own verdict: "**Closed. Attack disarmed**". Still closed — **L89** and **L1874** |
| **F16** | abstract result (8) is a successful non-event | major | fixed | the numbered result list is gone. The two live runs are described, not numbered, at **L121–127**, and §9.4 **L2727–2731** keeps C's approved line: "Both are statements about the apparatus, not about the framework" |
| **F17** | "negative results are also results" is not used to launder anything | — | not-a-defect | C's own verdict: "**No finding. Attack fails.**" |
| **F18** | the seal is asserted flatly in the abstract and disclaimed in §1.1 | minor | fixed | abstract **L90–92**: "*before* the ground truth was opened — **though the seal on that ordering is the authors' own declaration**, and the same instance built the world and adjudicated it" |
| **F19** | no LLM baseline anywhere, and no sentence explaining its absence | blocking | **partly-fixed** | the declaration C asked for exists, twice: **L130** and **L478**, "There is no language-model baseline anywhere in this paper". What is missing is the second half of C's minimal edit — no paragraph in §11 says that nothing in Phase 1 establishes the pipeline beats that baseline, that no claim depends on its doing so, and that it is Phase 3 work. §7.10's gap table (**L2219**) names "a theory-bearing control arm", which C correctly identified as the *opposite* ablation, and that is still the only place the gap is tabulated |

---

## Counts

Derived by counting the rows above, not asserted.

| verdict | A | B | C | total |
|---|---|---|---|---|
| fixed | 52 | 37 | 7 | **96** |
| partly-fixed | 0 | 5 | 3 | **8** |
| still-open | 5 | 3 | 3 | **11** |
| moved | 0 | 4 | 3 | **7** |
| superseded | 0 | 3 | 0 | **3** |
| adjudicated | 3 | 0 | 0 | **3** |
| withdrawn | 1 | 1 | 0 | **2** |
| not-a-defect | 5 | 1 | 3 | **9** |
| unverifiable | 0 | 0 | 0 | **0** |
| **total** | **66** | **54** | **19** | **139** |

Row-block arithmetic, so the per-audit totals are checkable too: A = 31 (Pass A)
+ 10 (wrong numbers) + 7 (uncited) + 8 (quotes) + 9 (disagreements) + 1 (the
withdrawn sub-claim A-66) = 66. B = 15 (major) + 6 (issue 13's sub-bullets) + 14
(non-match number rows) + 18 (minor) + 1 (the withdrawn sub-claim B-54) = 54.
C = F1…F19 = 19.

**Open in some form** — still-open + partly-fixed + moved = **26 of 139**.
**Closed** — fixed + superseded + adjudicated + withdrawn + not-a-defect = **113**.

The three audits between them raised **139** reconcilable findings. **96** are
repaired outright. Four of B's six blocking issues were closed by a single commit,
`080f05d`, which `OPEN_ITEMS.md` L14–17 already identified and which the blob
history confirms is the 91 244-byte state.

---

## The eleven still-open findings, ranked by what they cost

Each with the line a fix has to land on. (Line numbers are `PAPER.md`'s; fixes
land in `sections/`, since `PAPER.md` is generated — `verify_paper.py` gate A.)

1. **C-F13** — §6.2's bill still prints four definitional zeros as a measurement.
   **L1501–1504** (the table), **L1507–1511** (the paragraph), **L115–116** (the
   abstract). The single highest-value open row: C rates it blocking, the fix is
   one sentence, and the paper has already made exactly this move for A0/A0′ at
   L772–788, so a referee who reads both will read the omission as selective.
2. **C-F19** — no language-model baseline. Declared at **L130**/**L478**, but not
   converted into a scope limit in §11. C: "the first question from the floor."
3. **C-F14** — every experiment is n = 1, and the paper never says so once.
   `n = 1` occurs twice, at **L773** and **L2480**. Nothing in §11.3.
4. **C-F2 (residue)** — **L3460**, "predicted in advance and later measured", in
   the paragraph headed "The one thing this paper claims", against L360–361's
   "a declaration written by the authors' own script, not a control".
5. **C-F10** — **L2402–2404**, the exam's readers are never identified.
6. **C-F5** — **L2223**, "still no multi-level run" in a paper containing §6.
7. **C-F6** — **L1147**, §5.2's heading.
8. **C-F9** — **L592–593**, §2.4's self-refuting sentence.
9. **C-F12** — **L1595–1599**, the canonicaliser's provenance.
10. **A-39 / B-31** — **L1942**, "between 27 % and 45 %"; the artefact gives 28.3 %.
    The one surviving *number* finding in the whole reconciliation.
11. **B-35** — **L3291–3293**, 109 actions not reconstructible from a table that
    sums to 107. **B-26** (**L1276**, the anomaly "cap"), **B-53** (**L416** vs
    **L1323**), **B-51** (**L3287–3299**) and the four `moved` rows B-44/45/46/48
    (**L743–746**, **L842**, **L844–845**) are the cosmetic tail.

Two findings are open in a way the counts do not show, because they are about the
paper's apparatus rather than its prose:

* **B-21** — the draft note (**L14**) says "roughly 27 500 words"; `verify_paper.py`
  gate A, run this session, counts **36 256**. Both cannot be right, and the
  length claim is the one a program committee checks first.
* **A's own stamp** — `verify_paper.py` gate G fails on `CITECHECK.md` for having
  no `audit-stamp` block, so A is the one audit of the three that still asserts its
  target in prose only. That is P18's other half, not this file's.

---

## What was checked, and what was not

**Checked, by opening the file this session:** `PAPER.md` (hash, line count and
byte count recomputed; every anchor above read in context), `CITECHECK.md` in full,
`REVIEW.md` in full, `review-d-adversarial.md` in full, `OPEN_ITEMS.md` L1–20,
`PROVENANCE.md` L5/41/42/48/60/122/124, `figures/PARITY.md`, the P12 run
`MANIFEST.json`, `cold-start-a2/artifacts/loop_ledger.json`, and both
`cold-start-a2/theory/generated_{holed,repaired}/theory.lean` (diffed).
`verify_paper.py` was run in full. The blob history of `PAPER.md` was enumerated
commit by commit with `git cat-file`.

**Recomputed rather than read:** the two Lean files' diff (52 changed lines, 7
hunks, 28 weight-table lines, 791 vs 789 lines — this refuted a sub-claim in each
of A and B), the 31 Pass-A bare-token searches, and 31.9 % = 75 885 / 237 872.

**Not checked, and where that shows:**

* **`PROVENANCE.md:41`'s replacement citation (B-39).** I confirmed the O-03
  miscite is gone; I did not open `cold-start-a0/THEORIZE_LOG.md` to confirm that
  D-A0-007 carries the segmentation bits. The row says so.
* **The correctness of Pass A's 24 repaired paths, one by one.** I confirmed the
  bare form is gone and relied on `verify_paper.py` gate B (225 citations, 0 broken,
  run this session) for resolution. If a bare filename was replaced by a full path
  that resolves to the *wrong* file, gate B would not catch it and neither did I.
* **Whether the current text's *own* numbers are right.** That is
  `REVIEW-2026-07-30.md`'s job and the other half of P18. This file only asks what
  became of each stale finding; a `fixed` verdict means the old defect is gone, not
  that the sentence replacing it is correct.
* **Anything under `arc-recon/` or `environment_files/`.** Nothing was opened
  there. The pile-cut rows (A-62, A-64, B-51) were reconciled against `PAPER.md`'s
  own text, which names only the four development-pile games.

**Nothing was marked `unverifiable`.** That is a result, not an omission: every
one of the 139 findings resolved to an anchor in the current paper or to an
explicit "no longer present". If a later reader finds a row whose anchor does not
support its verdict, that row is wrong and should be said to be wrong — which is
the standard this file was written to apply to the three audits before it, and
the one under which it withdrew its own predecessor's claim about the 91 244-byte
state.
