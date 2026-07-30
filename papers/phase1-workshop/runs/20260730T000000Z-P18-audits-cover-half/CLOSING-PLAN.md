# P18 — the closing plan, written before it is executed

RES-3, cycle 94, 2026-07-30. Written to disk rather than held in a session's
context, because the previous three lives of this ticket each ended mid-move and
the successor had to re-derive the move before making it.

## What is actually red, measured not assumed

`papers/phase1-workshop/verify_paper.py` exits **1**, on exactly one line:

```
FAIL      CITECHECK.md -- no ```audit-stamp block
ok        REVIEW-2026-07-30.md -- binding on PAPER.md @ 6b633fcc, 3729 lines, 237872 bytes
ok        REVIEW.md -- stale, pinned @ 4208b69c (31.9% ...), superseded by REVIEW-2026-07-30.md
```

`python -m pytest -q` in `papers/phase1-workshop/`: **202 passed, 1 xfailed**.
The exit code was read directly, not through a pipe — `$?` after a pipe reads
`tail`, which is how a red gate reads green.

`PAPER.md` is unmoved: sha256 `6b633fcc…25376`, 3729 lines, 237872 bytes,
identical to `MANIFEST.json`'s `paper_at_start`. The audit did not shift under
itself.

## Why the gate cannot simply be stamped green

`CITECHECK.md` audits blob `4208b69c` — 1318 lines / 75885 bytes, i.e. **31.9% of
the paper as it now is**, and none of §7–§12. So its status is `stale`. But G5
refuses `stale` with no `superseded_by`, and G6 refuses a `superseded_by` naming
a file that does not exist or that is itself unstamped. *An audit may be retired;
it may not be retired into nowhere.*

So the successor has to exist first, and it has to be honest, which means the
citation axis has to actually cover the paper. That is the whole ticket.

## The five slices, and the one that blocks everything

| slice | range | PAPER.md lines | rows | state |
|---|---|---|---|---|
| A | Abstract–§3 | 1–908 | 73 | complete |
| B | §4–§6 | 909–1668 | 57 | complete |
| **C** | **§7–§8** | **1669–2520** | **—** | **stub — summary table, then "report in progress"** |
| D1 | §9–§10 | 2521–… | 73 | complete |
| D2 | §11–§12 | … | 65 | complete |

`complete` is a checked property here, not an inference from file size: each was
verified to carry all four pass sections, a limits section, and enumerated rows,
with no in-progress marker. The two stubs were caught by exactly that check.

**Slice C is the last thing standing between this gate and green.**

## The move, in order

1. **Slice C** — full rewrite, four passes enumerated. *(subagent, running)*
2. **`delta-old-vs-new.md`** — per-finding reconciliation of the three stale
   audits against the current paper. *(subagent, running)*
3. **`CITECHECK-2026-07-30.md`** — the live whole-paper citation audit,
   synthesised from all five slices. Stamp `status: binding`, pinning
   `6b633fcc…25376` / 3729 / 237872.
4. **`CITECHECK.md`** — add a stamp: `status: stale`,
   `superseded_by: CITECHECK-2026-07-30.md`, pinned at `4208b69c`.
5. Gate re-run; exit code read directly.

### Two traps in step 4, both already sprung once on the REVIEW axis

* **The off-by-one is not cosmetic.** `CITECHECK.md`'s prose says the old blob is
  **1319** lines, counting a last line with no trailing newline. The stamp must
  say **1318** (`wc -l` semantics), because G8 measures the blob out of git
  history and fails a stamp whose numbers were not measured from the sha beside
  them. `REVIEW.md`'s stamp already settled this convention and carries a note
  explaining the discrepancy against its own prose; `CITECHECK.md`'s must match.
  In a staleness stamp, an off-by-one is indistinguishable from a paper that
  gained one line.
* **Where the successor lives decides whether it counts.** The gate scans
  `papers/phase1-workshop/` only. A report written into `runs/` cannot supersede
  anything — reports under `runs/` are provenance, pinned by a MANIFEST and
  historical by construction. `review-2026-07-30-full.md` had to be **moved**,
  not copied, up out of `runs/` for this reason; two byte-identical audit reports
  in two directories is the drift this territory already has a receipt for (V26:
  a README pointing at a 60-world smoke run while the real 3000-world artefact
  sat elsewhere, and the reader's check succeeded against the wrong object).

## Not done here, deliberately

The referee pass's 13 findings are writing fixes against artefacts that already
exist. **Paper body text is RES-2's exclusive remit** (`monitor/CHARTER.md`), so
they are handed over, not applied. Locating them is this ticket's job; editing
them is not.
