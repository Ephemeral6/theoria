# How much of the paper each standing audit actually covered

P18, 2026-07-30, worker W-1690. Measured, not estimated: every row below is a
git blob, hashed and counted with `wc -l` semantics (`lines` = newline bytes).

Reproduce:

```bash
git log --format=%H -- papers/phase1-workshop/PAPER.md \
  | while read h; do git show "$h:papers/phase1-workshop/PAPER.md" \
      | python -c "import sys,hashlib; b=sys.stdin.buffer.read(); \
        print(hashlib.sha256(b).hexdigest()[:8], b.count(b'\n'), len(b))"; done
```

## The three pinned states, and the object they pin

| artefact | pinned commit | sha256 | lines | bytes | % of current, by bytes |
|---|---|---|---|---|---|
| `CITECHECK.md` | `4959df1cc` | `4208b69c` | 1318 | 75,885 | **31.9%** |
| `REVIEW.md` | `4959df1cc` | `4208b69c` | 1318 | 75,885 | **31.9%** |
| `runs/20260728T173000Z-P12-paper-multi-review/review-d-adversarial.md` | `29f865d7c` | `500867cd` | 2572 | 157,782 | 66.3% |
| — current `PAPER.md` — | `22daa8f3d` | `6b633fcc` | 3729 | 237,872 | 100% |

## Three corrections to the item that commissioned this work

The board item `P18-audits-cover-half-the-paper` is itself an artefact written
against a state the paper has outgrown. That is not a rhetorical point; all
three of its load-bearing numbers are wrong in the same direction, and the
correction is the finding.

**1. It is not half. It is under a third.** The item says "两份审计都只覆盖了
现在这篇的一半" against a paper of 2572 lines / 157,782 bytes. The paper was
already 3729 lines / 237,872 bytes when the item was claimed. `CITECHECK.md`
and `REVIEW.md` cover **31.9%** by bytes, 35.3% by lines. The item understated
its own finding by a factor of about 1.6.

**2. The two audits are not two states. They are one.** The item reports
`CITECHECK` pinned at "1319 lines / sha 4208b69c" and `REVIEW` pinned at
"75,885 bytes", as though these were two separate coverage frontiers. They are
the same blob: commit `4959df1cc`, the first assembled draft, is 1318 lines
**and** 75,885 bytes. Both audits ran against the same object on the same day.
The paper has therefore never had two independent audit frontiers — it has had
one, and it was set on day one.

**3. "1319 lines" is an off-by-one, and it is the reason the stamp defines the
convention.** `CITECHECK.md`'s own prose says 1319; the blob it names has 1318
newlines. `wc -l` and "number of lines a human counts" differ by one on a file
with a trailing newline, and in a staleness stamp that difference is
indistinguishable from a paper that has gained a line. `audit_stamp.py` fixes
`lines` to newline count and says so, so the next stamp cannot inherit the
ambiguity.

## What follows from the arithmetic

The unaudited region is not a tail. It is §7 through §12 —

| section | PAPER.md lines | never audited by |
|---|---|---|
| §7 the metrics battery | 1669–2324 | CITECHECK, REVIEW |
| §8 the exam | 2325–2520 | CITECHECK, REVIEW |
| §9 the live chain | 2521–2734 | CITECHECK, REVIEW |
| §10 the adjudication census | 2735–3197 | CITECHECK, REVIEW |
| §11 limitations | 3198–3485 | CITECHECK, REVIEW |
| §12 related work | 3486–3729 | CITECHECK, REVIEW |

— which includes the section the abstract calls **"the strongest result"** (the
38-metric battery, §7, the single largest section in the paper at 653 source
lines). The strongest claimed result in the paper had never been through a
citation audit or a referee pass.

## The assertion that made it invisible

The staleness was not merely unrecorded. The paper asserts the opposite, in its
own front matter (`sections/00_abstract.md`, the **Draft status** block,
`PAPER.md:26-31`):

> The rule is tested mechanically rather than asserted:
> `papers/phase1-workshop/verify_paper.py` checks that `PAPER.md` is what
> `assemble.py` generates and that every path cited in the sections resolves;
> `papers/phase1-workshop/CITECHECK.md` is a path/number/quote audit and
> `papers/phase1-workshop/REVIEW.md` an adversarial referee pass.

Present tense, no coverage qualifier, sitting directly beneath the binding rule
it is offered as evidence for. A reader is told the numbers have been audited;
for 68% of the paper by bytes, and for the section carrying the strongest
result, they had not been.

`verify_paper.py --explain-uncited` said the same thing in the same tense
("`CITECHECK.md` is the audit that does that"), which is why the fix there is a
lookup through the stamp rather than a corrected sentence: a corrected sentence
goes stale the same way, silently, and the next reader has no way to tell.
