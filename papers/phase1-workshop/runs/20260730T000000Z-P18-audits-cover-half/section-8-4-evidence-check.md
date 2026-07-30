# §8.4 evidence check — verifying the withdrawal comment's secondary claims

**Scope.** `papers/phase1-workshop/verify_paper.py`'s `WITHDRAWN 2026-07-30` block
asserts that the false ruling on `("08_exam.md", "**n = 1 per handover tier**, on a
saturated")` also silently exempted several §8.4 bullets carrying refuted claims.
Three specific assertions are checked below, independently — the withdrawal
comment's own wording was taken as a hypothesis, not as evidence.

**Block under examination.** `papers/phase1-workshop/sections/08_exam.md` L154-171
(`PAPER.md` L2478-2495), §8.4 "What the exam does not establish": six bullets, 18
lines, one `_blocks()` block.

**Branch.** `agent/p18-audits-cover-half-the-paper`, worktree
`.worktrees/p18-audits-cover-half-the-paper`. Read-only; nothing under
`sections/` was touched.

**Headline.** All three assertions hold. Assertion 3 is the most serious.
A **fourth** defect not named in the withdrawal comment was also found (bullet 4,
§ "Additional finding" below), and it shares a root cause with assertion 2.

---

## Assertion 1 — "The cheater's numbers are prose, not artefacts" is refuted

### VERDICT: **PARTLY** (the withdrawal comment is right on the decisive clause; one of the bullet's three clauses survives, and it is the first one)

The bullet, quoted exactly (`08_exam.md` L165-168):

> * **The cheater's numbers are prose, not artefacts.** The brief prompts are
>   digested in the run manifest but the directory holding them is gitignored, and
>   no cheater response or transcript is archived. We report those figures as
>   findings the exam reports, not as results a reader can re-derive here.

Three separable assertions. Taking them in order:

**Clause A — "The brief prompts are digested in the run manifest but the directory
holding them is gitignored". TRUE. Fully evidenced.**

```bash
git -C . check-ignore -v exam/artifacts/cheater      # exam/.gitignore:9:artifacts/cheater/
grep -n "brief" exam/runs/p15-rehearsal-01/MANIFEST.json
```

`exam/.gitignore` L9 is `artifacts/cheater/`. `exam/runs/p15-rehearsal-01/MANIFEST.json`
L9-16 carries a sha256 for all eight brief files, e.g.
`"artifacts/cheater/p15-verdict-a2.brief.txt": "c20e4028…4b3d12c0"`. This clause is
correct and well-supported. It is also the reason the bullet is not simply wrong:
it describes a real gap in the *inputs*.

**Clause B — "no cheater response … is archived". FALSE.**

```bash
ls exam/artifacts/answers/
git ls-files exam/artifacts/answers/
```

`exam/artifacts/answers/p15-verdict-a2.cheater-v4.answers.json` exists on disk (2695
bytes) **and is tracked in git** — it appears in `git ls-files` output. It is
unambiguously a cheater response, not a fake examinee's synthetic row:

* `"examinee_id": "cheater-v4"`
* `"meta.what": "an adversarial subagent handed the sheet alone, told to cheat rather than solve"`
* `"meta.sheet_only": true`
* 17 real per-item `claim` values under `answers`, plus `meta.exploit_per_item`, the
  agent's own account of which exploit decided each item.
* `"meta.note": "the claims are its own; the exploit strings are its own account of
  why. Scored against the key by the referee, not self-reported."`

**It is scored, and the scoring artefact is tracked.**

```bash
python -c "import json;d=json.load(open('exam/artifacts/matrix/verdict_confusion.json'));print(d['examinees']['cheater-v4']['awarded'], d['examinees']['cheater-v4']['possible'], d['examinees']['cheater-v4']['fraction'], d['examinees']['cheater-v4']['is_fake'])"
```

`exam/artifacts/matrix/verdict_confusion.json` → `examinees["cheater-v4"]`:
`awarded 17.0`, `possible 34.0`, `fraction 0.5`, `is_fake false`, and a full
confusion split (`pooled`: tp 9, tn 8, fp 0, fn 0, sensitivity 1.0, specificity
1.0). The human-readable twin is `exam/artifacts/matrix/verdict_confusion.md`.
`exam/runs/20260728T105500Z-V4-exam-selftest/MANIFEST.json` L46-47 digests the
answers file (`sha256 322c21514a8ac07a424e53317ab5f3e0dca076209d7df4b38a69eb00d184718b`).

The exam directory says so in as many words —
`exam/runs/20260728T105500Z-V4-exam-selftest/CHEATER.md` L40-42:

> Its answers are archived as a real submission at
> `artifacts/answers/p15-verdict-a2.cheater-v4.answers.json`, with its own account
> of which exploit decided each item, and it is a row on the confusion matrix.

So the paper says a cheater response is not archived, on the same day the exam
directory wrote a paragraph whose entire point is that one is.

**Clause C — "or transcript". TRUE on a narrow reading.**
No conversational transcript of the cheater subagent is archived anywhere; the
answers file is a structured submission, not a transcript. This clause survives.

**Also false: the bullet's own heading.** "The cheater's numbers are prose, not
artefacts" is contradicted by the figure §8 itself reports. `08_exam.md` L118-120
states the verdict `points` leak "yielded **17 of 17 claims with no board reasoning
at all**, measured rather than estimated". That 17-of-17 is re-derivable from
tracked artefacts: 17 claims in the answers file, `awarded 17.0 / possible 34.0`
with `fp 0, fn 0` in `verdict_confusion.json`. The final sentence — "not as results
a reader can re-derive here" — is therefore false for the verdict cheater
specifically.

**Narrower reading that partly defends the bullet.** Only the *verdict* cheater's
response is archived. There is no archived response for the held-out cheater, nor
for P-15's original adaptation/handover cheaters; the E1/E2/E3 held-out figures
really are prose, in
`exam/runs/20260728T105500Z-V4-exam-selftest/CHEATER.md` L74-120. A bullet scoped
to "the held-out and P-15 cheater figures" would be defensible. As written —
unscoped, and asserting "no cheater response … is archived" — it is refuted.

**Assertion 1 as stated by the withdrawal comment** ("refuted by
`exam/artifacts/answers/p15-verdict-a2.cheater-v4.answers.json`, which exists and is
scored") is **correct on every particular**: the file exists, is tracked, is a
genuine cheater response, and is scored at 17.0/34 in a tracked artefact.

---

## Assertion 2 — "Two cheater agents, four sheets, one pass" is struck through in `exam/STATUS.md` L267-273

### VERDICT: **CONFIRMED** — exact, including the line range

```bash
sed -n '267,273p' exam/STATUS.md
grep -n "cheater" exam/STATUS.md
```

`exam/STATUS.md` L267-273 verbatim:

> 11. ~~**Two cheater agents, four sheets, one pass.**~~ **Partly closed by V4.**
>    Two more cheaters have now sat the two sheets that changed — verdict and
>    held-out — and both results are above. `adaptation` and `handover` are
>    unchanged since P-15's pass, so they are as attacked as they ever were,
>    which is once each. The standing form of this weakness is that a cheater
>    pass is a sample, not a proof: what it did not find is not absent.

The strike-through is real, the line range L267-273 is exact, and the struck text
is character-for-character the paper's bold phrase.

**What superseded it.** The V4 cheater pass,
`exam/runs/20260728T105500Z-V4-exam-selftest/CHEATER.md`, whose L1-6 quote the same
weakness in order to answer it:

> `STATUS.md` open weakness 11: *"Two cheater agents, four sheets, one pass. No
> adversarial reader has seen the fixed sheets."* The two sheets that changed when
> P-15's leaks were fixed are `p15-verdict-a2` and `p15-heldout-a0`. Both have now
> been attacked.

**Correct current numbers.** Four cheater agents, four sheets, and the pass count
is no longer uniform:

| sheet | cheater passes | changed by the leak fixes? |
|---|---|---|
| `p15-verdict-a2` | 2 (P-15, then V4) | yes — `points` made uniform |
| `p15-heldout-a0` | 2 (P-15, then V4) | yes — world block no longer states dynamics |
| `p15-adaptation-a0` | 1 (P-15) | no |
| `p15-handover-a0` | 1 (P-15) | no |

So the paper's trailing clause — "**and none of them has seen the fixed sheets**" —
is precisely the proposition V4 was run to falsify, and it is now false for both
sheets that were fixed.

**Ordering — the paper was right when written, and went stale 1h50m later.**

```bash
git log --format='%h %ad %s' --date=iso -S 'Two cheater agents, four sheets, one pass' -- papers/phase1-workshop/sections/08_exam.md
git log --format='%h %ad %s' --date=iso -1 -L 265,275:exam/STATUS.md
git log --format='%h %ad %s' --date=iso -- papers/phase1-workshop/sections/08_exam.md
```

| event | commit | timestamp |
|---|---|---|
| §8.4 bullet written | `579d0385` "papers: PAPER.md v0.2 …" | 2026-07-28 **17:41:44** +0800 |
| `exam/STATUS.md` weakness 11 struck through | `d43d8f60` "exam: the marker was only ever tested at its endpoints…" | 2026-07-28 **19:31:01** +0800 |

**The paper section came first.** This is a nuance the withdrawal comment does not
state, and it matters for how the author should read the finding: this is not an
author inventing a claim, it is a claim that was true at 17:41 and was superseded
at 19:31. What makes it a live defect rather than a forgivable race is that
`08_exam.md` was edited **twice more afterwards** — `71078f0e` (2026-07-29 22:15)
and `8a56976e` (2026-07-29 22:42) — and the bullet was not refreshed either time.
For 29 hours the block sat under a ruling that exempted it from check E.

---

## Assertion 3 — "the leaks that remain are the ones nobody has looked for yet" appears nowhere in the repository

### VERDICT: **CONFIRMED** — and it is worse than "nowhere else": the sentence originates in the paper that attributes it elsewhere

The paper, `08_exam.md` L169-171:

> * **Two cheater agents, four sheets, one pass** — and none of them has seen the
>   fixed sheets. **In the directory's own words:** *the leaks that remain are the ones
>   nobody has looked for yet.*

"the directory" is `exam/` — §8.3 uses the same construction two blocks earlier
("That number is worth almost nothing on its own, and **the directory** says why",
L116), and every other quotation in §8 that is introduced this way resolves to a
file under `exam/`.

**Working tree, whole repo:**

```bash
grep -rn "the leaks that remain" . -i
grep -rn "nobody has looked for" . -i
```

Four hits, and every one of them is a paper file or an audit of a paper file:

| hit | what it is |
|---|---|
| `papers/phase1-workshop/sections/08_exam.md:170` | the claim itself |
| `papers/phase1-workshop/PAPER.md:2494` | the assembled copy of the same line |
| `papers/phase1-workshop/runs/20260730T000000Z-P18-audits-cover-half/citecheck-C-s7-to-s8.md:161,584` | a prior audit quoting it in order to flag it |
| `papers/phase1-workshop/runs/20260730T000000Z-P18-audits-cover-half/row-sample-audit-C.md:695` | ditto |

Zero hits anywhere under `exam/`.

**All branches:**

```bash
for b in $(git for-each-ref --format='%(refname)' refs/heads refs/remotes); do
  git grep -l "nobody has looked for" "$b" --; done
```

Every branch that has the string has it in exactly two files, `PAPER.md` and
`sections/08_exam.md`. No branch has it under `exam/`.

**Git history:**

```bash
git log --all --format='%h %ad %s' --date=iso -S "nobody has looked for" --name-only
git log --all --format='%h' -S "nobody has looked for" -- exam/     # returns nothing
```

Three commits ever introduced the string. The earliest is `579d0385` (2026-07-28
17:41:44) touching `papers/phase1-workshop/PAPER.md` and
`papers/phase1-workshop/sections/08_exam.md` — the same commit that wrote the
bullet. The other two are the 2026-07-30 audit files. **The string has never existed
in any file under `exam/`, on any branch, at any commit.** It was composed in the
paper and attributed to a source that has never contained it.

**Near-misses, reported separately as instructed.** None is a paraphrase close
enough to excuse the italics, and the nearest one says something materially
different:

| location | text | relation |
|---|---|---|
| `exam/STATUS.md` L271-272 | "The standing form of this weakness is that a cheater pass is a sample, not a proof: what it did not find is not absent." | Nearest real sentence. Says unfound leaks *may* exist — an epistemic caveat. The paper's version asserts that remaining leaks *do* exist and that nobody has looked. Not the same claim. |
| `08_exam.md` L116 | "That number is worth almost nothing on its own, and the directory says why." | Establishes that "the directory" means `exam/`, i.e. fixes the attribution the quotation fails. |
| `exam/runs/20260728T105500Z-V4-exam-selftest/CHEATER.md` L1-6 | "Both have now been attacked." | The opposite of the sentence's premise. |

**Why this is the most serious of the three.** Assertions 1 and 2 are stale claims —
things that were true, or nearly true, and were overtaken by later work. This is
a fabricated quotation: italicised, introduced with "In the directory's own words",
and attributed to a body of files that has never contained it. It is also
*doubly* wrong, because the paraphrase it approximates (`STATUS.md` weakness 11)
is the version of that weakness that has been **struck through** — so the sentence
invents a quotation and invents it from the superseded text.

---

## Additional finding — a fourth stale bullet the withdrawal comment does not name

The withdrawal comment names three refuted claims in the block. There is a
**fourth**, and it went stale in the *same commit* as assertion 2.

`08_exam.md` L161-164:

> * **The calibration bands are outside the rubric digest.** The digest hashes the
>   rubric modules' source text and travels onto every sheet and report; the bands
>   live elsewhere, so a quiet widening there would not surface as a mismatch. One
>   band has already been changed once — recorded, and correctly — which is exactly
>   why the hole matters. **Closing it is not done.**

`exam/STATUS.md` L220-227:

> 3. ~~**`EXPECTED` is not covered by the rubric digest.**~~ **Closed by V4**
>    (D-EX-016). `selftest.protocol_digest()` hashes `mark.py`, `calibration.py`
>    and `selftest.py` together, and a test pins the value, so widening a band now
>    requires a deliberate edit a reviewer sees.

Verified in code, not just in prose:

```bash
grep -n "def protocol_digest" exam/grading/selftest.py          # L620
grep -n "protocol_digest" exam/tests/test_selftest.py           # L186-202
grep -n "D-EX-016" -A 12 exam/DECISIONS.md                      # L383+
git log --all --format='%h %ad %s' --date=iso \
    -S '~~**`EXPECTED` is not covered by the rubric digest.**~~' -- exam/STATUS.md
```

`exam/grading/selftest.py` L620 defines `protocol_digest()`;
`exam/tests/test_selftest.py` L186 `test_the_protocol_digest_covers_the_marker_and_the_bands`
and L195 `test_a_widened_band_changes_the_protocol_digest` pin it;
`exam/DECISIONS.md` D-EX-016 (L383-395) records the decision and explains why it is
a *second* digest rather than an extension of the first.

The strike-through commit is **`d43d8f60`, 2026-07-28 19:31:01 +0800** — identical
to assertion 2's. One commit superseded two of this block's six bullets, 1h50m
after the block was written, and neither was refreshed in the two later edits to
`08_exam.md`.

The first two sentences of the bullet remain true of the *rubric* digest — it still
does not cover `EXPECTED`, deliberately, and D-EX-016 says so. Only the final
sentence, "Closing it is not done", is false. This is a one-sentence fix.

---

## What each of the six bullets should cite

Every path below was checked to exist in this worktree and to be tracked
(`git ls-files`). Line numbers are from the working tree at `agent/p18-audits-cover-half-the-paper`.

| # | Bullet (opening words, `08_exam.md` L) | Status | What should evidence it |
|---|---|---|---|
| 1 | **Three of four papers have no real result** … "Nothing has sat them." (L154-155) | **Evidenceable, with a caveat** | `exam/artifacts/exam_summary.json` — `"marked": []`, the marked-examinee list is empty. Corroborate with `exam/artifacts/reports/`, which contains exactly two files, both `p15-handover-a0.reader-tier{1,2}.report.json`: no report exists for held-out, adaptation or verdict. **Caveat the author must resolve:** `exam/artifacts/matrix/verdict_confusion.json` carries `cheater-v4` with `is_fake: false`, `awarded 17.0/34` — a non-fake examinee *has* sat the verdict sheet. "Nothing has sat them" needs narrowing to "no theory has been marked on them", which the two artefacts above then support exactly. |
| 2 | **n = 1 per handover tier**, on a saturated sheet (L156-157) | **Evidenceable — this is the citation the withdrawn ruling should have been** | `exam/artifacts/reports/p15-handover-a0.reader-tier1.report.json` and `exam/artifacts/reports/p15-handover-a0.reader-tier2.report.json` — one report per tier, which *is* n = 1 per tier. Both are already cited in §8.2 (`08_exam.md` L78), twelve blocks and 76 lines earlier; repeating the two paths here costs one line and removes the need for any ruling. |
| 3 | **No cross-type total should be quoted.** (L158-159) | **Evidenceable** | `exam/STATUS.md` L242-245, open weakness 8: "**The four papers were built by four separate agents.** Their conventions … the rubric weights across types are not calibrated against each other and no cross-type total should be quoted." The paper's sentence is a near-verbatim restatement of it. The four rubric modules `exam/grading/rubrics_{verdict,heldout,adaptation,handover}.py` are the underlying object if a code-level citation is wanted. |
| 4 | **The calibration bands are outside the rubric digest.** (L161-164) | **Evidenceable, but the last sentence must be deleted** | For the hole as stated: `exam/DECISIONS.md` D-EX-010 L191-197. For the band that was changed once: `exam/DECISIONS.md` D-EX-010 L153-157 (`("heldout","bluffer")` moved `[0,0.35]` → `[0,0.50]`). **"Closing it is not done" must go** — `exam/DECISIONS.md` D-EX-016 (L383-395), `exam/grading/selftest.py` L620 `protocol_digest()`, `exam/tests/test_selftest.py` L195 `test_a_widened_band_changes_the_protocol_digest`, and `exam/STATUS.md` L220-227 all record it closed. |
| 5 | **The cheater's numbers are prose, not artefacts.** (L165-168) | **Partly refuted — rewrite, then cite** | Clause that survives: `exam/.gitignore` L9 (`artifacts/cheater/`) and `exam/runs/p15-rehearsal-01/MANIFEST.json` L9-16 (sha256 for all eight brief files). Clause that must go: "no cheater response … is archived" — refuted by `exam/artifacts/answers/p15-verdict-a2.cheater-v4.answers.json` (tracked), scored in `exam/artifacts/matrix/verdict_confusion.json` at `awarded 17.0 / possible 34.0`, narrated in `exam/runs/20260728T105500Z-V4-exam-selftest/CHEATER.md` L40-42, digested in that run's `MANIFEST.json` L46-47. A truthful rewrite: the *inputs* (briefs) are unarchivable, the verdict *response* is archived and scored, and the held-out cheater's figures remain prose. |
| 6 | **Two cheater agents, four sheets, one pass** — and none has seen the fixed sheets (L169-171) | **Superseded — renumber, and delete the quotation** | Current state: `exam/STATUS.md` L267-273 (weakness 11, struck and replaced) and `exam/runs/20260728T105500Z-V4-exam-selftest/CHEATER.md` L1-6. Correct numbers: four cheater agents; verdict and held-out attacked twice, adaptation and handover once each. The trailing clause "none of them has seen the fixed sheets" is false. **The italicised quotation must be deleted outright** — it has no source. If a quotation is wanted, `exam/STATUS.md` L271-272 is the real sentence and is stronger: "a cheater pass is a sample, not a proof: what it did not find is not absent." |

**On the "pure statement of absence" question.** Only bullet 1 comes close, and it
turns out **not** to be one: `exam/artifacts/exam_summary.json`'s empty `"marked"`
array and the two-file `exam/artifacts/reports/` directory are positive artefacts
of the absence, and both are tracked. So no bullet in this block is unevidenceable
in principle. Bullets 3 and 6 are *normative or historical* rather than
quantitative — bullet 3 says what a reader must not do, bullet 6 counts events —
but each has a documented source under `exam/`, so each can carry a path.
The one thing in the block that can never carry a citation is the fabricated
quotation, and the fix there is deletion, not a path.

---

## Commands, collected

```bash
cd .worktrees/p18-audits-cover-half-the-paper

# the block itself
sed -n '152,171p' papers/phase1-workshop/sections/08_exam.md

# assertion 1
ls -la exam/artifacts/answers/
git ls-files exam/artifacts/answers/
cat exam/artifacts/answers/p15-verdict-a2.cheater-v4.answers.json
python -c "import json;d=json.load(open('exam/artifacts/matrix/verdict_confusion.json'));print(d['examinees']['cheater-v4']['awarded'],d['examinees']['cheater-v4']['possible'],d['examinees']['cheater-v4']['is_fake'])"
git check-ignore -v exam/artifacts/cheater
grep -n "brief" exam/runs/p15-rehearsal-01/MANIFEST.json
sed -n '1,45p' exam/runs/20260728T105500Z-V4-exam-selftest/CHEATER.md

# assertion 2
sed -n '267,273p' exam/STATUS.md
git log --format='%h %ad %s' --date=iso -S 'Two cheater agents, four sheets, one pass' -- papers/phase1-workshop/sections/08_exam.md
git log --format='%h %ad %s' --date=iso -1 -L 265,275:exam/STATUS.md
git log --format='%h %ad %s' --date=iso -- papers/phase1-workshop/sections/08_exam.md

# assertion 3
grep -rn "the leaks that remain" . -i
grep -rn "nobody has looked for" . -i
for b in $(git for-each-ref --format='%(refname)' refs/heads refs/remotes); do git grep -l "nobody has looked for" "$b" --; done
git log --all --format='%h %ad %s' --date=iso -S "nobody has looked for" --name-only
git log --all --format='%h' -S "nobody has looked for" -- exam/     # empty

# additional finding
sed -n '218,230p' exam/STATUS.md
grep -n "def protocol_digest" exam/grading/selftest.py
grep -n "protocol_digest" exam/tests/test_selftest.py
grep -n "D-EX-016" -A 12 exam/DECISIONS.md
```

## Summary of verdicts

| assertion | verdict |
|---|---|
| 1. cheater response archived and scored, refuting the bullet | **PARTLY** — decisive clause refuted exactly as claimed; the gitignored-briefs clause and the "transcript" clause survive |
| 2. `exam/STATUS.md` L267-273 struck through | **CONFIRMED** — exact text, exact line range; struck 1h50m *after* the paper was written |
| 3. quotation present nowhere in the repository | **CONFIRMED** — never existed under `exam/` on any branch at any commit; originates in the paper itself |
| (new) 4. bullet 4's "Closing it is not done" | **REFUTED by D-EX-016** — same strike-through commit as assertion 2 |
