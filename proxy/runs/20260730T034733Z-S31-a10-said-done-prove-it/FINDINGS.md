# S31 — findings, written as they land

Worker W-1691. Base commit `50e10617`. Branch `agent/s31-a10-said-done-prove-it`.

## Step 0 — established directly, before any delegation

Three commands, run against the live repo at 2026-07-30T03:45Z:

```
$ git rev-list --left-right --count origin/master...origin/agent/a10-shared-ledger-real-arms
490     0
```

The a10 branch is **0 commits ahead** of `origin/master`. Whatever a10 committed
is on the mainline. So situation (b) "done but never merged" is **excluded**.

```
$ git check-ignore -v proxy/var/ledger.jsonl
proxy/.gitignore:3:var/ proxy/var/ledger.jsonl
$ git ls-files proxy/var
(empty)
```

`proxy/var/` is gitignored by design. The shared ledger is a **runtime artifact
that never enters the repository**. So any audit that claims to read
`proxy/var/ledger.jsonl` "from `origin/master`" is reading something that
cannot exist in `origin/master`.

```
$ python - <<'PY'   # over the working-tree ledger
lines 107 bad 0
arms: [('mock_arm', 74), ('replay', 33)]
PY
```

The working-tree ledger has 107 well-formed records and **zero real-arm
records**. mtime 2026-07-28.

## The distinction that decides this item

Two different sentences, and only one of them is true:

* "The audit could not find real-arm records **because the ledger is
  gitignored**" — this would make the audit method wrong and the code fine.
* "The audit could not find real-arm records **because none have ever been
  written**" — this makes the finding real, and gitignore merely explains why
  the audit had to read the working tree to see anything at all.

Both facts are true at once and they are not alternatives: the path is
gitignored *and* the working-tree copy has no real arm. Which means the audit
reached a **correct conclusion by a method that cannot support it** — on a
clean CI checkout the same script sees an absent file, and "absent file" and
"file with no real arms" must not print the same verdict.

## Step 1 — what A10 actually delivered (`proxy/runs/20260729T010000Z-A10/`)

A10's own artefacts are on master and answer the item's first question outright.
`MANIFEST.json` `demonstration`:

```json
"before": { "records": 107, "by_arm": {"mock_arm": 74, "replay": 33},
            "real_arm_records": 0 },
"after":  { "records": 42,
            "by_arm": {"theoria": 14, "bare_cc": 14, "schema_repro": 14},
            "duplicate_seq": 0, "verify_chain": "PASS", "processes": 3 },
"scope":  "ledger identities of three arms driven by a script; NOT the three
           real arms running their own loops -- that is cross-territory"
```

Two things follow, and they matter separately.

**First: the number the 2026-07-29 audit "discovered" is A10's own `before`
number, verbatim.** 107 records, 74 `mock_arm`, 33 `replay`, `real_arm_records:
0`. The working-tree ledger today is byte-identically that state (mtime
2026-07-28, i.e. it has not been written since before A10 ran). The audit did
not find a broken delivery; it re-read the snapshot A10 published as the
starting condition it was measuring against.

**Second: A10's `after` went to a scratch file, on purpose.** `demo_output.txt`
names it: `C:\Users\...\Temp\tmp6umtuho3\ledger.jsonl`. The demo drove three
OS processes (pids `[35884, 41288, 2148]`) writing one ledger, 42 records, 0
duplicate seq, chain PASS. It never wrote to `proxy/var/ledger.jsonl` — and
`SCOPE.md` explains why that is a decision rather than an omission: each arm
writes its own ledger by an already-registered design decision
(`ablcore/ledger_abl.py:9-25`, D-AB-004), and repointing them is **another
territory's source**.

### So the word "real" carries two senses and the audit picked the other one

In `proxy/ledger.py` the arm names are a frozenset
`{bare_cc, schema_repro, theoria, probe, replay, mock_arm}`. "A real arm" in
A10's title means **an arm identity that is not `mock_arm`/`replay`** — that is
what its `real_arm_records: 42` counts. It does **not** mean "an arm that made
a paid API call". The audit read the second sense, checked a file, and found 0
— which is true in *both* senses, which is exactly why nobody noticed the two
questions had been collapsed into one word.

### Verdict on the item's first question

None of (a) never done / (b) done-not-merged / (c) output on a gitignored path,
cleanly. It is a fourth situation:

> **A10 is done, merged, and honest — and the shared ledger genuinely still has
> zero real-arm records, because A10 recorded that as a scope gap rather than
> closing it.** The audit rediscovered A10's own published gap and scored it as
> a missing delivery.

The audit was wrong about *whose* gap it is and *what it means*, and right that
the gap is open. `proxy/README.md` says the harder half out loud already: **"No
live run has gone through these proxies yet."**

## Step 2 — asks 3 and 4 are already on master, in an amended form

`proxy/reconcile.py:102`:

```python
RECONCILIATION_KEY = ("actions", "cost", "score_per_run")
```

with `turns` carried as a named non-voting gap (`_gap_turns`,
`reconcile.py:395`) and `score_per_step` surfaced as
`recorded: True, cross_verified: False` (`_gap_step_score`,
`reconcile.py:401-410`). `proxy/tests/test_reconcile.py` has a red-path test per
leg plus `test_every_leg_of_the_key_has_a_proven_failing_path`.

So S31's ask 3 ("re-key reconciliation to cost × actions × turns; mark score
self-reported and non-cross-verifiable") and ask 4 ("a negative sample must turn
it red") are **discharged on master already** — but *not literally*. A10
deliberately deviated on two points and wrote down why (`SCOPE.md` §2, §3):

* **`turns` is not in the key, because the field does not exist.** Not in the
  ledger, not in baseline-arms at any level; theoria-arm keeps a turn axis in a
  separate `turns.json` joined structurally with a self-declared
  `join_confidence`. A comparison over a field nobody records cannot fail, so
  putting it in the key would have bought a leg that is green by construction.
* **`score_per_run` IS cross-verified, and only `score_per_step` is not.** The
  premise "the API does not return score" is true of a *command response* and
  false of a *scorecard close* — `POST /api/scorecard/close` returns `score`,
  and 32 real closed cards in `tests/fixtures/scorecard_corpus.json` carry one.
  Marking the whole quantity self-reported would have discarded a check that
  works.

Both deviations are, I think, correct — and note what the first one is an
instance of. The `20260729T1700Z-S29-measurement` run's whole subject is that
**"not measured" and "measured, and it was zero" must not be the same literal**.
A `turns` leg comparing a field nobody records is that defect wearing a
reconciliation's clothes: it would print agreement where there is no
measurement. S31 asks me to land a ruling that its own neighbouring ruling
forbids.

## Step 3 — what is therefore actually left to do

Asks 3 and 4: verify, adjudicate, record. Not re-implement.

What is genuinely open, and is this item's work:

1. **The ruling lives in a run directory, where audits do not look.** A10's
   reasoning is in `proxy/runs/20260729T010000Z-A10/SCOPE.md`. That is why the
   next audit re-judged it 20 hours later. It has to move somewhere an auditor
   reads, and — better — become a check rather than a paragraph.
2. **The audit method itself.** An auditor asking "does the shared ledger carry
   real-arm records?" must not be able to print the same verdict for *the file
   is untracked and absent from this checkout* and *the file is here and the
   answer is zero*. Today it can, and did.
3. **The real-arm write path has never been exercised end to end.**
   `proxy/README.md`: "No live run has gone through these proxies yet."

(Sections below filled in as the four parallel investigations report.)
