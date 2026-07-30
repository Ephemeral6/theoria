# delta-old-vs-new — what happened to every finding in the three stale audits

Reconciliation half of P18. Read-only pass: nothing in `PAPER.md`, `sections/`,
`CITECHECK.md`, `REVIEW.md` or any prior report was edited to produce this file.

## The four states

| id | artefact | pinned to | `PAPER.md` sha256 | lines | bytes |
|---|---|---|---|---|---|
| **A** | `papers/phase1-workshop/CITECHECK.md` | commit `4959df1cc` | `4208b69cdd6197a7b5f401223601a56b476d8c9a2f7a471b1412ab469c6dbd7d` | 1318 (`1319` as the audit counts it) | 75 885 |
| **B** | `papers/phase1-workshop/REVIEW.md` | commit `4959df1cc` — **the same state as A** | `4208b69cdd6197a7b5f401223601a56b476d8c9a2f7a471b1412ab469c6dbd7d` | 1318 | 75 885 (11 451 words) |
| **C** | `runs/20260728T173000Z-P12-paper-multi-review/review-d-adversarial.md` | commit `29f865d7c`, `PAPER.md` v0.3 | `500867cdb66e38a258da51acde9ad0709242d8bb68e841b6f3c9f6acff6a8cbc` | 2572 | 157 782 |
| **now** | working tree, HEAD `50e106179323e1af3a2e1b5c82a35fd3d232c552` | — | `6b633fcc35ae612f20f4028eb45aaca1b6ed86a24eb1304af555c46228325376` | 3729 | 237 872 |

Verdicts as recorded: A — no verdict (mechanical audit); B — **Reject** as submitted;
C — **Reject**, "a closer call than the last round".

**A and B are pinned to the identical state.** `OPEN_ITEMS.md` L9–10 says
"REVIEW.md was written against a `PAPER.md` of 75,885 bytes; CITECHECK.md against one of
91,244" — that is wrong. `CITECHECK.md` L3–4 records sha `4208b69c…`, which is the
75 885-byte, 1318-line file, byte for byte the state `REVIEW.md` L3 names. There is no
91 244-byte state in the history of the file. The two audits are one snapshot, not two,
which matters for the counting question at the end: A and B do not bracket a range of
the paper's growth, they bracket a single point of it.

**Scale of the drift.** A and B saw 1318 lines; the paper is now 3729, a 2.83× growth
that added §6 (A3 transfer), §8 (the exam), §9 (the live chain) and §10 (the census)
wholesale, and renumbered every section from §6 onward. C saw 2572 lines and predates
§10's census and §7.2a/§7.7a/§7.10a. Section identities quoted in A and B are therefore
**not** the section identities in the current paper: A/B's §6 (battery) is now §7,
A/B's §7 (limitations) is now §11, A/B's §8 (related work) is now §12.

*(status legend: FIXED / OPEN / SUPERSEDED / REGRESSED / DISPUTED — one per row.)*

## The table

| # | src | finding, one line | status | evidence |
|---|---|---|---|---|
| | | *(filled in below as verification proceeds)* | | |
