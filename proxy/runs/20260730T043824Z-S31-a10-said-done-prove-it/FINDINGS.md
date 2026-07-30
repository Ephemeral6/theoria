# S31 — findings, written as they land

Worker W-1702. Branch `agent/s31-a10-said-done-prove-it`, base commit `12a48ecc`
(= `origin/master` at 2026-07-30T04:38Z). Territory `proxy`.

Machine-readable summary: `MANIFEST.json`. Ruling for auditors: `RULING.md`.

---

## Step 0 — the branch I was handed was not a delivery

The ticket warned that a branch and worktree already existed. Both did. What
they contained:

* Branch `agent/s31-a10-said-done-prove-it` was **45 commits ahead of `master`**,
  and every one of those 45 was somebody else's merge — `s35`, `s36`, `p20`,
  `p21`, `p22`, plus merge commits of `origin/master`. Not one line of S31 work.
  It was a prior attempt's staging branch: someone had merged the mainline into
  it repeatedly. Reset to `origin/master` (`12a48ecc`); nothing of S31's was
  lost because nothing of S31's was there. The branch had **never been pushed**
  (`git ls-remote --heads origin | grep s31` → empty), so the reset destroyed
  no published history.
* The worktree held one untracked directory,
  `proxy/runs/20260730T034733Z-S31-a10-said-done-prove-it/`, from worker
  **W-1691**: a `MANIFEST.json` with `"files": []` and a `FINDINGS.md` that
  stops mid-sentence at *"(Sections below filled in as the four parallel
  investigations report.)"*. W-1691 died at the same point in the same item.

**Treated as notes, not as delivery** — per the ticket's own instruction. I
re-derived every factual claim below with my own commands rather than
inheriting it. Where W-1691 and I agree the agreement is independent; where we
disagree, §1 records it, because one of its central claims is false.

---

## Step 1 — the ledger is not frozen, and the prior attempt wrote into it

W-1691's `FINDINGS.md` states that the working-tree ledger is "byte-identically"
A10's published `before` state, 107 records, "mtime 2026-07-28, i.e. it has not
been written since before A10 ran".

**That is no longer true, and it was already untrue when W-1691 wrote it.**
Measured at 2026-07-30T04:38Z:

```
$ wc -l < proxy/var/ledger.jsonl
113
$ python  # arm histogram
mock_arm 78
replay   35
unparseable 0
```

113 records, not 107. The six extra all carry `ts` of **2026-07-30T03:57Z** —
i.e. ten minutes into W-1691's own session (started 03:47Z). Their shape:

```
seq 108 mock_arm 2026-07-30T03:57:14.907Z  event=incident kind=score_mismatch
seq 109 replay   2026-07-30T03:57:14.915Z  event=incident kind=score_mismatch
seq 110 mock_arm 2026-07-30T03:57:14.919Z  event=incident kind=score_mismatch
seq 111 mock_arm 2026-07-30T03:57:26.410Z  event=incident kind=score_mismatch
seq 112 replay   2026-07-30T03:57:26.415Z  event=incident kind=score_mismatch
seq 113 mock_arm 2026-07-30T03:57:26.419Z  event=incident kind=score_mismatch
```

Three distinct incidents, appended **twice**, twelve seconds apart. That is
`reconcile --all` run twice against the live shared ledger.

### Why it happened: auditing this ledger mutates it

`proxy/reconcile.py:520-530` appends an incident record whenever it finds a
problem, and the CLI enables that by default —
`--no-incident` is opt-*out* (`reconcile.py:548-549`,
`write_incident=not args.no_incident`). So the act of asking "does this ledger
reconcile?" writes to the ledger, and asking twice writes twice. There is no
idempotency key: the same three problems produced six records.

Three consequences, and they are separate:

1. **Any worker who audits the live ledger silently grows it.** W-1691 did not
   report doing so; on the evidence it did not notice.
2. **Incident records carry an `arm` they did not earn.** `reconcile.py:521`
   sets `arm = steps[0].get("arm", "probe")` — the incident inherits the arm
   identity of the run it is complaining about. So `mock_arm` and `replay` in
   the histogram above are **not all calls**; 6 of the 113 are the auditor's own
   complaints wearing an arm's name.
3. Therefore **an audit that counts records by `arm` without filtering on
   `event` is counting its own footprints.** That is directly relevant to the
   2026-07-29 audit this item exists to adjudicate — see `RULING.md`.

### Discipline adopted for the rest of this item

Every reconciliation this item runs goes against a **copy** in the run
directory or a `tmp_path`, never `proxy/var/ledger.jsonl`, and passes
`--no-incident` where a report is all that is wanted. The six records already
appended are **not** removed: the file is append-only and rewriting it would be
a worse offence than the one it repairs. They are documented here and in
`RULING.md` so the next reader knows what they are.

---

## Step 2 — the three-way question, answered

Ticket asks which of: (a) never done, (b) done but never merged, (c) delivered
onto a gitignored path so the audit method is what is wrong.

Established directly, at `12a48ecc`:

```
$ git merge-base --is-ancestor origin/agent/a10-shared-ledger-real-arms master
  → exit 0                                      # A10 IS an ancestor of master
$ git diff --stat master...origin/agent/a10-shared-ledger-real-arms
  → (empty)                                     # nothing of A10 is outstanding
$ git check-ignore -v proxy/var/ledger.jsonl
  proxy/.gitignore:3:var/   proxy/var/ledger.jsonl
$ git ls-files proxy/var/
  → (empty)                                     # untracked, by design
```

**(b) is excluded: A10 is merged, entirely.** A10's own artefacts are on the
mainline at `proxy/runs/20260729T010000Z-A10/`.

The remaining detail of the ruling — whether this is (a), (c), or a fourth
thing — is in `RULING.md`, which is the artefact an auditor is meant to read.

*(Sections for the four parallel investigations follow as they report.)*
