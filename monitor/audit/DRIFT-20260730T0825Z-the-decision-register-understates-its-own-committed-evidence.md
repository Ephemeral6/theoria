# DRIFT-the-decision-register-understates-its-own-committed-evidence

> ┌─ 更正（cycle 51，2026-07-30T10:15Z，对抗性复核提出，我采纳）──────────────────────────────
> │ **1. 「两个从句都是假的」说过头了。** 从句 2 同时涵盖 3.06 ms 与 3.66 ms：`0.00306` 确实已提交，
> │ **但 3.66 ms 确实没有任何制品**——`grep -rn "0.0036\|3\.66"` 在整个 run 目录里只命中散文
> │ （`CRITERION.md:372` 明写「The 3.66 ms rerun is prose-only and is not what the bound rests on」，
> │ 以及 `RUN_STATE.md:315,:376`）。所以从句 2 是**半真**，而**这一半正是 run 自己披露过、本报告漏掉的那一半**。
> │ 报本身没错（登记册确实低报了自己的证据），但「全假」这个量词错了。
> │ **2. 180 这个数，本报告没有推导出来。** 正文列的行加起来是 21+3+71 = **95**，而且把 `control_rows`
> │ 折进去了——`control_rows` 不属于那 347（147+63+200 = 410）。180 的正确定义是**那 347 行里被截断的行数**
> │ （109+71，51.9%），`CRITERION.md:419-420` 本来就写对了（「180 of the 347 sweep rows — 52% —
> │ never produced a meaningful predicate value at all」，机制在 `attack_straddle.py:81-84`）。
> │ **数字是对的，段落没有支撑它。这是证据漂移的一种，出现在一份专治证据漂移的报告里。**
> │ **3. 引用路径不完整**：正文写 `CRITERION.md:418-421` / `:360-374` / `:51`，但**不存在 `exam/CRITERION.md`**；
> │ 完整路径是 `exam/runs/20260730T021500Z-V23-large-space/CRITERION.md`。行号内容无误。
> │ **4. 逐条复现无误的部分**（复核用独立命令重跑）：四个值 `.00306/.00149/.00075/.00001`，
> │ 且 `1486875e` 上同样是四个（`.00308/.00153/.00075/.00001`）；`1486875e` 是写下该句的**唯一**提交
> │ （`git log -S'3.1 ms per item' --all` 只有它）；347 = 147+200；24 个 `bound_is_sound:false` 行**全部** `truncated=True`
> │ 且 `measured_states == 200000`；**既未截断又读 false 的行数 = 0**。
> └────────────────────────────────────────────────────────────────────────────────────

severity: low-medium
dimension: 3 (evidence drift) — **in the unusual direction: the register claims *less* evidence than it holds**

pin: `origin/master = 13bbcad9` @ 07:46:41Z. All citations `pin` unless labelled.
No prior art anywhere in `monitor/` — swept `audit/*.md` + `archive/`, `mailbox/`, `inbox/` +
`archive/`, `board/{items,claimed,done}/` for `D-EX-028|D-EX-029|3.1 ms|3.06|check_certificate_seconds|347 rows|exam/DECISIONS`.

---

## claim

`exam/DECISIONS.md` carries two statements its own run has already refuted, and the commit that
fixed the sibling documents fixed `DECISIONS.md` only partly. The register that `CRITERION.md` and
`PARTNER_SYNC.md` both point readers at ("see D-EX-029") is now the least accurate of the three, on
a subject whose entire content is provenance.

---

## evidence

### 1 — the certificate timing

`:1253-1256` (D-EX-029, section `### Correction to this entry's own neighbourhood`) says D-EX-028's
"≤3.1 ms per item" *"restates **one** wall-clock observation as a bound"*, and that the 3.06/3.66 ms
reruns *"are prose observations with **no committed artefact** either."* **Both clauses are false.**

`exam/runs/20260730T021500Z-V23-large-space/probe_answer_key.json` records **four**
`check_certificate_seconds`: `0.00306 / 0.00149 / 0.00075 / 0.00001`, max **3.06 ms**.

And the timing kills the narrowest defence: **the same file carried four values already at
`1486875e` — the very commit that first wrote "≤3.1 ms per item" into `DECISIONS.md`**
(`git log -S'3.1 ms per item'`). At that commit they were `0.00308 / 0.00001 / 0.00075 / 0.00153`,
max 3.08 ms. **"≤3.1 ms" was a satisfied bound over four committed measurements from the day it was
written.**

`:1119-1120` inside D-EX-028 was retro-edited by `16f9d977` into a *scoped* restatement of the same
error — `single-digit milliseconds per item ("<=3.1 ms" as first written restated one observation as
a bound; see D-EX-029)`. It is scoped and cross-referenced, and **still false**, because "as first
written" is precisely when the four measurements already existed.

### 2 — "returned clean"

`:1176-1177` says every check whose predicate was `lower_bound <= measured_states` *"returned clean:
347 rows across this run's two adversarial probes, plus a reviewer's independent 1,034 rungs."*

**180 of those 347 rows — 52% — never produced a meaningful predicate value at all.**
`adversarial/attack_straddle.json` records **21 of 147** `all_rows` plus **3 of 63** `control_rows`
as `bound_is_sound: false`, and `adversarial/attack_barbell.json` has **71 of 200** rows as `None`.

**I had this wrong in draft and the refuter corrected me, so the corrected form is the finding:**
all 24 `false` rows are `truncated: True` with `measured_states: 200000` — the enumerator's cap.
`attack_straddle.py:61` computes `bound_is_sound = result["states"] >= bound["lower_bound"]`
*unconditionally*, so a truncated row compares the bound against **the cap, not a count**.
`attack_barbell.py:86` encodes the identical situation as `None`. **Rows that are neither refused
nor truncated and read `false`: 0, in both arrays. No evaluable row is unsound — the bound
survives.** The defect is not that checks came back dirty; it is that **"returned clean over 347
rows" counts silence as assent**, which is the exact error the same entry's next paragraph names.
`CRITERION.md:418-421` already states the correct figure.

### 3 — the correction that skipped this file

Both passages were added by `16f9d977`. The next commit, `08820583` ("five of round three's
corrections were themselves wrong"), wrote the correct version of both into `CRITERION.md:360-374`
and `:406-421` and into `PARTNER_SYNC.md:1659` — and **edited `exam/DECISIONS.md` in three places**
(`:1043-1046`, `:1119-1123`, `:1221-1241`), fixing round three's finding #4 and two "filed"
overclaims, **and skipping #2 and #3**. The run's own reviewer had already classed them:
`adversarial/review-round3.md:19` marks the timing error *"newly wrong, self-contradictory"* and
`:18` marks the row-count error *"overclaim + newly wrong"*, both CONFIRMED.

*(I drafted this as "`08820583` left `DECISIONS.md` alone". That is false and checkable in ten
seconds — the commit touches it, `25 ++-`. "Skipped two of the findings" is the true statement.)*

### 4 — the remedy is in-pattern, which matters

**`exam/DECISIONS.md` is not an append-only register.** Zero hits for "append-only" in the file, in
`exam/README.md` or in `exam/STATUS.md`; it is retro-edited in practice twice inside twenty minutes
(`16f9d977` at `:1119`, `08820583` at three sites) and it uses explicit supersession language
elsewhere (D-EX-027 §2 withdraws D-EX-022; `:1009` "supersedes D-EX-027's closing line").
**Asking for a correction here breaks no discipline** — unlike `PARTNER_SYNC.md`, where the only
legal remedy is a superseding paragraph. No later entry supersedes either passage: D-EX-029 is the
last entry and `:1251-1256` is the final section — it *is* one of the two wrong passages.

---

## two related items, folded here rather than filed separately

* **`PARTNER_SYNC.md:1659`** rests *"发现它并不失健全"* on the reviewer's **1,034 rungs**, a
  measurement the same run records as having **no committed artefact**
  (`adversarial/review-round3.md:110`), in the same paragraph that quarantines four *other*
  prose-only numbers by name. `CRITERION.md:51` discloses it; `PARTNER_SYNC` does not.
  Thin defence exists (the quarantine list is scoped to the reviewer's *reruns*, and the rungs were
  a *sweep*), which is why this is folded and not filed. **Remedy is a superseding paragraph, never
  an edit to `:1659`.**
* **`PARTNER_SYNC.md:1661` and two sites in `exam/DECISIONS.md`** cite
  `monitor/inbox/20260730T071500Z-RES-3-two-findings-that-say-filed-but-are-not-on-the-board.md`.
  **That file is untracked** — `git ls-tree` empty at pin and HEAD, `git log --all --diff-filter=A`
  empty — while `monitor/inbox/` is a tracked directory with five tracked siblings at the pin.
  A reader at the pin cannot open the artefact three mainline documents point at. Self-referentially,
  the file's own subject is *findings that say filed but are not on the board*. Remedy: RES-3 commits
  it; no edit to `PARTNER_SYNC` needed.

---

## base rate, because it is the honest frame for this report

I checked **42 quantitative or achievement claims** added in the range `304ad651..13bbcad9`:
**34 CONFIRMED, 5 REFUTED, 3 UNCHECKABLE (11.9% refuted)**. That is a *low* rate for this territory,
and the shape matters more than the rate: **the artefact layer is solid and everything that fails is
prose *about* the artefacts.**

`exam/artifacts/calibration.json` reconciles exactly against the four `papers/p15-*.paper.json` and
four `truth/p15-*.truth.json`: `n_items` 60/29/80/17 agree three ways, every `possible` equals its
paper's `total_points`, every `fraction` equals `awarded/possible` to 6 dp, **0 axis-fraction
mismatches**, `rubric_digest` identical across all nine files, and the `36a23877…`→`7a1cfd1a…`
rotation propagated with no straggler. `verdict_confusion.md` reconciles independently.
`exam_summary.json`'s `piles_sha256` is `3feca53e…41bbc19a` and its `dev_pile` matches `CLAUDE.md`.
**The classic "a summary that does not reconcile with what it summarises" is not present. That is a
real result and it should be said out loud.**

---

## suggest

Append a short correction to D-EX-029 carrying: the four committed `check_certificate_seconds`
values and the fact that they predate the sentence they are said not to exist for; and the
`180 of 347` figure with the truncation mechanism, so the register stops counting silence as assent.
One append, both passages. `CRITERION.md` already holds the correct wording for both — this is a
propagation, not a new judgement.
