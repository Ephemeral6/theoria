# Review — hostile referee, full text, P18 re-run

**Reviewed state.** `papers/phase1-workshop/PAPER.md`, sha256
`6b633fcc35ae612f20f4028eb45aaca1b6ed86a24eb1304af555c46228325376`, 3729 lines,
237872 bytes, 35 624 words. Full text. Referee: adversarial re-run, P18,
2026-07-30. Prior rounds consulted: REVIEW.md (1318 lines / 75885 B),
review-d-adversarial.md (2572 lines / 157782 B).

**Word count method.** `wc -w PAPER.md` = **35 624**. A whitespace split in
Python gives 36 256 (the two differ on how CJK punctuation is tokenised);
stripping fenced code blocks gives 36 152, stripping markdown table rows as well
gives 34 439. Every one of those is in the same band. The paper's own draft note
(PAPER.md L12, `sections/00_abstract.md` L12) says "roughly 27 500 words". See
**B7**.

**Remit.** Attackability and evidence sufficiency over the whole current text,
with priority on §7–§12 (PAPER.md L1669–3729), which no prior round has read:
`REVIEW.md` pins the first draft (1318 lines, 32 % of the current text by bytes)
and `review-d-adversarial.md` pins v0.3 (2572 lines, 66 %). §7.2a, §7.7a, §7.10a,
§8, §9, §10 in its entirety, and §11.4/§11.5 as they now stand have never been
reviewed by anyone.

**Method.** Every file cited below was opened. Where the paper cites a JSON
field the field was read; where it cites a count the count was recomputed in
Python against the artefact, not against the report prose. Where the paper cites
a test assertion the test file was opened. No network, no API calls, no sealed
pile reads: the only ARC game ids appearing below are the four development-pile
ids.

**Prior-status convention.** Each finding carries one of:
**missed** (no prior round names it), **logged and knowingly kept** (a prior
round or the paper's own checklist names it and it stands), or **new damage**
(introduced by material written after both prior rounds).

---

## Recommendation

*(filled at the end of this document — see "Recommendation and defence")*

---

## Blocking findings

*(in progress)*

