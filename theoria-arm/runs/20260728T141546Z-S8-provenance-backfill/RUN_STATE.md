# S8 · giving the arm that spent the money its provenance back

**Worker** W-1412 · **branch** `agent/s8-provenance-backfill` · **base**
`6beb2e6` · **utc** 2026-07-28T14:15:46Z

No network, no model call, no ARC action, no dollar. Everything below is
derived from ledgers already on disk and from git objects.

## What was asked, and what it turned into

The item was: eleven run directories, four manifests, on the only arm that has
ever spent ARC quota. Classify each run, backfill the real ones, mark what
cannot be recovered, and write down which runs a paper may cite.

Two of the eleven turned out to be pytest fixtures (gitignored, so never in the
repository, but sitting in the archive all the same) — so the archive holds
**nine** runs, not eleven, and **five** of them lacked a manifest.

All five now have one, and building the tool that writes them turned up three
things that were not in the item:

1. **No existing manifest names the commit its run ran at.** `base_commit` was
   `git rev-parse HEAD` at manifest-writing time. Checked against the
   `arm_version` hash each run recorded, all four disagree — two name a later
   commit, two name a commit whose tree contradicts the recorded hash.
2. **Two runs ran against files that were never committed**, so they are not
   reproducible from git. Their manifests say so now instead of implying
   otherwise with a commit id.
3. **A scorecard is still open.** `preflight-20260728T012031Z` opened
   `bbbd5b57-…` and nothing ever closed it. Its ledger's claim of zero billed
   actions has never been confirmed by the API and cannot be offline.

And one number that was in the archive but unreachable from the file that
needed it: the two aborted runs' scorecards. Both died before closing their own
card, so `archive.py` wrote `scorecard: null` — while the API's own count sat in
the ledger of the salvage run that closed the card ten minutes later.

## The number that matters

**18 ARC actions is this arm's entire lifetime spend** (5 + 6 + 7), and it now
reconciles from two independent sides: the ledgers say 18, the four closed
scorecards say 18. `verify_provenance` asserts the equality, so it cannot drift.

## What was built

| file | what it does |
|---|---|
| `armtools/armversion.py` | recomputes `_bootstrap.arm_version()` from any commit's tree, so a recorded hash identifies the tree a run's sources match — or proves no reachable commit carries it |
| `armtools/backfill.py` | writes a manifest from a run's own ledger; `null` + a stated reason wherever the evidence does not reach |
| `armtools/verify_provenance.py` | nine checks over the whole archive; writes nothing |
| `armtools/archive.py` | now emits `utc` (required by CLAUDE.md, never written before) and checks `base_commit` at write time |
| `harness/run.py`, `tests/test_arm.py` | fixtures write to `.pytest-runs/`, not into the archive |

## What an adversarial review changed

The derivation was handed to a reviewer told to refute it. **The four verdicts
survived** — reproduced over a 347-commit universe including reflog-only and
dangling commits, and cross-checked by extracting six commits' trees and running
the real `_bootstrap.arm_version()` in each, which agreed exactly, file counts
included. Three defects in the *mechanism* came back and all three are fixed
here:

* **`matched` overclaimed.** The scan walked `git log --all -- theoria-arm`, so
  it missed every commit that leaves the arm alone and inherits its parent's
  hash — one arm version here is shared by **187** commits while that scan found
  one and called it unique. Now exhaustive over `rev-list --all`, keyed by the
  arm's subtree so it stays cheap. The four verdicts are unchanged.
* **The git-side reimplementation did not match the walk.** `_bootstrap` uses
  substring tests, so `runsim/` and `__pycache__x/` are skipped; the
  reimplementation read them as path components. Never triggered — no such
  directory has existed here — but silent, and it would have shown up as a real
  run matching no commit for no reason. Pinned by a test.
* **`arm_version` depended on the checkout path.** The substring test ran on the
  *absolute* path, so under `.worktrees/runs-cleanup/` every file was skipped and
  the function returned `files: 0` and the sha256 of the empty string. Fixed in
  `_bootstrap.py`, pinned by a test.

A fourth was caught by this arm's own reproducibility check before the review
saw it: `branch` came from `git branch --contains`, which returned 55 branches
for one commit and took the alphabetically first — `agent/a2-crosscheck`, with no
relation to the run — and wrote it into a required field.

One wording correction the review forced, and it matters: **the derived commit is
not "the commit the run was launched from."** Two were created *during* their
run (21 s and 57 s after start), because the fix under test was committed
mid-run. The claim is that the run's `.py` sources were byte-identical to that
commit's tree — recorded with the arithmetic under
`provenance.arm_version_lookup.relation_to_the_run`.

Standing limit: **`arm_version` covers `.py` only.** Two commits differing in a
prompt, a log or a fixture share a hash; four of seventeen groups are
multi-commit for that reason.

## Verify

```bash
cd theoria-arm && python -m armtools.verify_provenance   # 9 checks, all pass
cd theoria-arm && python -m pytest                       # 54 passed
cd theoria-arm && python -m armtools.backfill --all      # idempotent: no diff
```

## Artefacts here

* `classification.json` — every directory under `runs/`, its kind, and why
* `armversion_scan.json` — every reachable commit carrying the arm, with the arm version its tree hashes to; the lookup table behind every `base_commit` here
* `backfill_report.json` — what was created, amended and skipped
* `verify.txt` — the nine checks

## Gaps left open, deliberately

* `preflight-20260728T012031Z` and `20260728T012311Z-…-aborted` are not
  reproducible from git. Nothing can change that now; it is recorded.
* The open scorecard `bbbd5b57-…` needs one free API call to settle. Not made:
  it is a live call and belongs behind the shared spend gate, not inside an
  offline archive-repair pass. Proposed to monitor rather than done unilaterally.
* The `agent/e3-engines-online` branch carries two further manifest-less runs
  (`20260728T072604Z-E3-sk48-carried`, `preflight-20260728T074237Z`). Not this
  branch's territory to fix, and `backfill --all` covers them when it merges.
