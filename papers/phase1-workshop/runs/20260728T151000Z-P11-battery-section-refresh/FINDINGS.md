# P11 — findings

`MANIFEST.json` beside this file is canonical; this is the narrative.

## 0 · The work order's premise had already expired

P11 reads: *"papers 里电池一节标着 stale，而 battery 的 REPORT 已更新过两轮（区分力首跑、
去冗余聚类）。按最新 REPORT 重写该节。"*

Both halves of that premise are false as written, and the tree says so in its own
records:

* **§7 is not marked stale.** It was re-derived against `battery_version: "v2"` at
  P7. `papers/phase1-workshop/OPEN_ITEMS.md:25` carries item A1 — "§7 reports v0,
  battery is v2" — struck through and closed. `REVIEW_TRIAGE.md:133` records the
  moment the note went out of date: *"…still said '§7 is known stale', which
  stopped being true when §7 was"* re-derived.
* **The two rounds named are already in the section.** 区分力首跑 and 去冗余首跑
  are battery v1 (milestones B9/B10); the section reports **v2**, which re-ran
  both on better material — process 1 on the gradient `Theoria.md` actually
  specifies (B12) and process 3 with per-family representatives (B13).

This is the third work order in this territory to arrive with an expired premise
(`runs/20260728T115500Z-P9/FINDINGS.md:15` records the second). The pattern is
worth naming rather than routing around: **the board is slower than
`OPEN_ITEMS.md`, and `OPEN_ITEMS.md` is slower than the artefacts.**

So the item was executed on its second clause, which had not expired: *"顺带核对
论文里引用 battery 的其它段落有没有跟着过时"* — cross-check every other battery
citation in the paper for drift. That clause turned out to be the live one, and it
found drift **inside** §7 as well as outside it.

## 1 · Method

Three verifiers were dispatched in parallel, each given a disjoint slice and the
same instruction: check the paper against `battery/artifacts/*.json`, **not**
against the prose of `battery/REPORT_V*.md`. That distinction is the paper's own
precedence rule (`sections/07_battery.md:129-130`), and it is what turned up the
defects — six of the twenty-one below are places where the paper faithfully
reproduces a report sentence that the artefacts contradict.

* verifier A — `sections/07_battery.md` lines 1–210 (§7.1–§7.5)
* verifier B — `sections/07_battery.md` lines 211–364 (§7.6–§7.10)
* verifier C — every battery restatement outside §7, plus `PROVENANCE.md`

A fourth agent built an independent fact sheet of the battery arm from scratch, to
catch anything all three verifiers might inherit from the paper's own framing.

## 2 · Defects found

Severity: **W** = wrong (the artefact says something else), **D** = drifted (true
once, not now, or true of a different quantity), **S** = overstated.

### Inside §7 — 13

| # | line | defect | sev |
|---|---|---|---|
| 1 | 288 | "nineteen of twenty **epistemic** metrics" — the audit's scope is M1–M6 **plus** K1–K14 = 20, and the twentieth is **M3**, a *mechanism* metric (`battery/audit/exploits/mechanism_epistemic.py:876`). The epistemic family has 14 members, so "nineteen of twenty epistemic" is arithmetically impossible. `REPORT_V2.md:236` says "nineteen of twenty metrics" with no family word; the paper added it | **W** |
| 2 | 354–355 | "`Step.won`, `held_out_frame` and `Beat.env_actions` … are populated by adapters and read by no metric" — **all three are now read**, by the v2.1 defences this same section describes twelve paragraphs earlier: `battery/metrics/planning.py:116` (P4's `won` gate), `battery/metrics/epistemic.py:63` (`held_out_frame`), `:233,:277` (`env_actions`). The paper is quoting `REPORT_V2.md:306`, which is itself stale; §7.7 already says the same thing in the past tense at line 260 | **W** |
| 3 | 362–363 | the pile-digest finding: "hashes to `d3140eff…` after LF normalisation and to a third value on a Windows checkout". Recomputed: raw sha256 **equals** the LF-normalised sha256 — `piles.json` carries no CRLF — so the normalisation is a no-op and there is no third value. `DECISIONS.md` D-B-011 mentions neither LF nor Windows. The rest of the sentence is exactly right and reproduces byte-for-byte | **W** |
| 4 | 90 | "seven were **demoted** to `reference` by the anti-gaming audit" — only **two** were demoted (P2, X3: `register_tier` `main` → `tier` `reference`). P1, E4, X1, X2 and X4 were registered `reference` from the start and had no main table to fall from (`gaming_audit.json`, `metrics[*].register_tier`). Seven of the eight *sit in* the reference tier, which is the true and still-damning claim | **W** |
| 5 | 132 | "**Six** of the seven economy metrics did [collapse to `no-data`]" — **four** did: E2, E3, E5, E7. E1 and E6 return `not-ranked` (direction-less diagnostics) and E4 `underpowered`. Six is reachable only by folding `not-ranked` into `no-data`, which the sentence cannot do while putting `no-data` in backticks as the artefact's verdict label | **W** |
| 6 | 176 | "the audit **demotes** K4 to the reference tier" — K4's `register_tier` is already `reference` and its `status` is `"register confirmed by demonstration"`. Nothing was demoted; the instruction quoted next to it is real | **W** |
| 7 | 222 | "between **28 %** and 45 % of pilot steps failed" — the source says **27 %** (`REPORT_V0.md:57`; `STATUS.md:117` W-4). The figure 28 appears nowhere in the repository | **D** |
| 8 | 270 | E2's "entire observed range across every real run (0.162–0.321)" — the current spectrum's 67 E2 values run **0.162–0.297**. 0.321 was the pre-v2.1 maximum and now survives only in frozen exploit claim text. `REPORT_V2.md:371` records the fall; the paper quotes the range from before it | **D** |
| 9 | 236–239 | "ρ = −0.83 is the one v0 number this paper cannot re-derive" — the *literal value* is indeed carried by no artefact, but `redundancy.json`'s `matrix` measures the same correlation for v2: P1↔P5 **ρ = −0.899 over 82 shared runs**. "Cannot re-derive" is too strong; "was not re-measured at the same value" is the honest form, and the v2 number is better evidence for the same point | **S** |
| 10 | 329–331 | "the **three** K-family clusters" — there are **two** K-only clusters ({K10,K8} and {K14,K5,K7}) producing three retirements; and "which the artefact flags on each as not evidence" — no such per-cluster flag exists. `redundancy.json` carries one global `coverage_note` and one cross-family `warning`, neither per-cluster, and the string "not evidence" appears nowhere | **W** |
| 11 | 254 | "The main table fell from **19 to 6** on demonstration and returned to 9" — 19 and 9 are both artefact-derivable (`register_tier` count; `tier` count). **6 is not**: the artefact records `demoted_by_demonstration` of **10**, giving 19 − 10 = 9. The 6 comes from `REPORT_V2.md`'s superseded "13 metrics demoted", a v2.0 figure the report never restated after v2.1 | **D** |
| 12 | 22–24 | "**each** carries the verified pile digest and the sha256 of its inputs" — only `capability_spectrum.json` has a `provenance` block. The other six artefacts (`arm_contrast`, `discrimination`, `discrimination_arms`, `gaming_audit`, `redundancy`, `validation_material`) carry no provenance, no pile digest and no input digests. The path the paper cites is correct; the word "each" is not | **W** |
| 13 | 169 | blockquoted R-05 string is not verbatim: the paper writes "the Button is pressable from any direction"; `cold-start-a0/THEORIZE_LOG.md:224` reads *"the Button is **presumably** pressable from any **of the four** directions"*. The second quote in the same sentence, "not thin, zero", is verbatim | **D** |

Two rounding notes, both defensible and both left alone: X3's δ is `-0.5625`
printed as −0.562 (truncation, but the artefact's own warning string also says
0.562, so the paper agrees with the artefact it quotes) and X2's `-0.1875`
printed as −0.188 (correct rounding).

One asymmetry the section does not state and now does: three of the eight rows in
§7.2's table (P3, X2, X3) carry `min_attainable_p` **0.25**, not 0.125, because a
tie drops them to three paired games. §7.5's floor of 0.125 is the *best* case in
the table, not the uniform one.

### Outside §7 — 8

| # | file:line | defect | sev |
|---|---|---|---|
| 14 | `PROVENANCE.md:196` | "**follows the artefacts.** Six of the seven economy metrics resolved to `no-data`" — four did. The row that exists to adjudicate *in favour of the artefacts* misreports the artefact. The worst of the twenty-one for that reason | **W** |
| 15 | `sections/00_abstract.md:88` | "**17** of its written **defence claims** were contradicted by their own demonstration" — 17 is `n_disagreements`, which counts *register entries*. Only **14** contradict the `defended` field; K7, K11 and M6 contradict `accidental` only (`gaming_audit.json`, `disagreements[*].fields_contradicted`) | **W** |
| 16 | `sections/10_limitations.md:246` | the same overstatement, in §10.5 — the paper's single summary claim sentence | **W** |
| 17 | `sections/10_limitations.md:223` | "**four** metrics on A0 are marked `[seen]` post-dictions" — **five**: K1, K2, K7, K8 in the v0 seal, plus K14 marked `[seen for A0 and A2]` in the v1 table (`battery/PREDICTIONS.md:217`). A v0-era count that a later append moved | **D** |
| 18 | `PROVENANCE.md:137` | the index row for the same fact, same undercount | **D** |
| 19 | `README.md:68` | names `battery/REPORT_V0.md` as what §7 is a reading of, for a section re-derived at v2. `OUTLINE.md:36` already names REPORT_V2 and the artefacts, so the two disagree | **D** |
| 20 | `sections/02_framework.md:119` | "the battery's recompute, now in its third version" — arithmetically right (three reports exist) but it collides three ways: the artefacts self-report `battery_version: "v2"`, the run directory is named `…-v3`, and §7.10 uses "v3" for the *next* version | **S** |
| 21 | `sections/02_framework.md:118` | "It reports the **three** acceptances" against `00_abstract.md:3`'s "**four** offline acceptances". Not a battery defect — a plain internal contradiction that appeared when §6 (A3) landed and nobody swept the framework section. Fixed here because it is one word inside this territory, and declared rather than folded in silently | **W** |

## 2a · The adversarial pass refuted five of my own corrections

A fifth agent was pointed at the diff with instructions to attack, not confirm.
**It broke five of the twenty-one fixes**, and every one of the five has been
verified by hand and reverted or rewritten. This section is longer than it needs to
be because the failures are more instructive than the successes.

| # | my "fix" | why it was wrong | what the section says now |
|---|---|---|---|
| 3 | I deleted the pile paragraph's "third value on a Windows checkout" as an invention | **`arc-recon/data/piles.json` does carry CRLF.** `git ls-files --eol` reports `i/lf w/crlf`, `core.autocrlf` is `true`, no `.gitattributes` covers the path — so this very worktree's copy has **111 CRLF pairs** and hashes to `f2ef44d1…`, while its LF-normalised form is `d3140eff…`. The verifier that reported "no CRLF" measured the *main* checkout, which happens to hold LF; the claim was true of one working copy and false of the repository | the third value is restored **and named**, with the mechanism spelled out: a digest quoted as "the file's hash" is a digest that depends on who checked it out |
| 11 | I said `REPORT_V2.md`'s intermediate main-table low of 6 "rests on a count the report never restated, and no artefact carries it" | **The report restates it at `REPORT_V2.md:338` and names the six at `:83`, and the arithmetic reconciles exactly**: 19 − 13 demoted = 6; 13 − 3 returned = 10, which is the artefact's `demoted_by_demonstration`; 6 + 3 = 9. My "correction" would also have falsified the subsection's own title, "the main table moved twice" | the original sentence is restored, with the reconciliation shown so a reader can see which endpoint is artefact-derivable and which is the report's |
| 6 | I wrote that K4's `register confirmed by demonstration` is "the rarer outcome in this audit and the only kind that reflects well on the author" | **It is the majority outcome — 21 of 38.** Two further slips in one sentence: the field is `status`, not `verdict`; and K4's `defended` is `false`, so what was confirmed is an *admitted, undefended hole*, not a defence that held | the count is given, and the sentence now says what the confirmation actually confirms |
| 21 | I changed §2.5's "the three acceptances" to "four" | **`Theoria.md:294` says 三件离线验收, and the string "A3" appears in `Theoria.md` zero times.** §2.5's own preceding sentence enumerates the three by name. A3 is claim C3 answered early — the paper's own §6 says so. My edit made "that unit and nothing more" self-falsifying | §2.5 is back to three, naming §6 as an early read on C3; and the **abstract**, which said "four offline acceptances" in two places and was the actual source of the contradiction, is corrected to match the mandate |
| 20 | I explained the v2/third-version collision as "counted from different starting points by the report series and the artefacts" | **They agree.** `REPORT_V0/V1/V2` and `battery_version: "v2"` are both zero-indexed. The only mismatch was between my own ordinal prose and the label — and I had invented a disagreement between two sources that do not disagree, which is exactly the unsourced-number habit the house rule exists to stop | the sentence says both count from zero |

Four half-fixes it also caught are closed: `PROVENANCE.md`'s ρ row still called
−0.83 "the one battery number that cannot be re-derived" after §7.6 had named a
second; the `min_attainable_p` row still said 0.125 with no mention of the three
metrics at 0.25; `README.md` claimed §7 "still quotes" `REPORT_V1` when it cites it
once as a filename; and §7.10's field-read sentence named `planning.py` for a read
that actually happens in `model.py` and the `@metric` capability guard.

**The lesson is narrower and worse than "check your work".** Four of the five are
cases where I trusted a verifier's negative result — "this string is not verbatim",
"this file has no CRLF", "no artefact carries this" — without asking *where it
looked*. A negative is only as wide as the search behind it, and none of those
searches was as wide as the claim it licensed. The CRLF one is the sharpest: two
agents ran the same check on two different working copies of the same blob and got
different answers, and the repository's own `core.autocrlf` setting is the thing
that reconciles them.

## 3 · What this says about the paper, beyond the fixes

**Six of the twenty-one are places where the paper faithfully reproduces a
sentence from `battery/REPORT_V*.md` that the artefacts contradict** (#1, #2, #4,
#5, #10, #11). The paper's precedence rule — artefacts over reports — was written
down in §7.3 and then not applied to the report's own summary sentences. A rule
that is stated in one subsection and disregarded in the neighbouring ones is worth
less than no rule, because it invites the reader to trust the parts that were
never checked.

**Two of them are the report being stale about the code rather than about the
data** (#2, #11): `REPORT_V2.md` describes fields as unread that its own v2.1
defences went on to read, and quotes a demotion count from before its own last
round. A report that is left standing unedited on purpose — which this one is, and
for good reasons — accumulates exactly this kind of debt, and every downstream
reader inherits it.

**The restatement warning held.** `REVIEW_TRIAGE.md:135` says *"a restatement in
one section is a cross-reference too, and it goes stale the same way."* Five of the
eight defects outside §7 are restatements of §7 facts (#14–#18). The abstract and
§10.4 are the paper's standing blast radius for any change to §7, and they should
be re-read every time it moves.
