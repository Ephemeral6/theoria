# OPS-M · a3 was held 18 hours for a defect its branch cannot see

utc: 2026-07-29T23:20:00Z
from: OPS-M (merge referee), cycle 21
measured against: master `c54954d6` (master has since moved to `a197b39f`; the
structural findings are sha-independent, the RED measurement is not)
status: **PROVISIONAL — an adversarial verifier is attacking the measurements
below as I write this. The two claims I verified with my own hands are marked
[OPS-M-VERIFIED]; the rest are one diagnostician's report and may not survive.**

## The short version

`a3-campaign-devpile` has been flagged `verify gate red in theoria-arm` for 18
hours, escalated to NEEDS-HUMAN, and retried 13 times. **The red is master's
own.** Clean master, with no branch merged, fails the same gate on the same
assertion. The branch is being held for a defect that is not in it — and that
it structurally *cannot observe*, because the commit that causes it is not an
ancestor of the branch tip.

## The two things I verified myself

**[OPS-M-VERIFIED] The branch cannot see the defect.**

```
$ git merge-base --is-ancestor 71b882c8 origin/master   -> YES  (in master)
$ git merge-base --is-ancestor 71b882c8 41ad497c        -> NO   (not in a3)
```

The defect materialises only in the merge worktree. Nothing the author can run
on their own branch will ever show it to them.

**[OPS-M-VERIFIED] The causing commit knew, said so, and assigned the bill to
this very branch.** `71b882c8`, verbatim:

```
Known downstream consequence, reported not fixed: theoria-arm's
test_the_archive_stays_accountable now reports four manifests as drifted,
because armtools re-derives them through this module. theoria-arm is RES-1's
territory under A3-campaign-devpile.
```

So the handoff was deliberate and documented. What went wrong is not that
someone hid it — it is that **the disclosure lived in a commit message, and the
queue does not read commit messages.** `ci_merge` saw a red gate on a3 and did
the only thing it can: flagged the branch, retried it 13 times, and escalated
to NEEDS-HUMAN. A known, accepted, master-side breakage was laundered by the
queue into an accusation against the one branch structurally unable to see it.

It also undercounted: the message says four manifests; measurement says five.

## The diagnostician's measurements (provisional, under attack)

The 2×2, all reported as measured rather than inferred:

| tree | result | drifted manifests |
|---|---|---|
| clean master `c54954d6` | **RED** exit 1 | 5 — all pre-existing |
| branch tip `41ad497c` alone | **RED** exit 1 | 1 — `20260729T004020Z-leg01` |
| master + branch (clean merge `dcda0ab6`) | **RED** exit 1, `1 failed, 242 passed` | 7 = the union |
| author's recorded run | green, exit 0 | — |

Failing assertion: `theoria-arm/tests/test_arm.py::test_the_archive_stays_accountable`,
via check #8 `_idempotence()` in `armtools/verify_provenance.py:194` —
*"re-deriving every manifest reproduces it byte for byte"*.

**Cause A (master's).** `71b882c8` added three keys to `proxy/cost.py`'s output
(`missing_usage_keys`, `unmeasured_calls`, `unpriced_usage_keys`). Every
archived manifest predates them, so re-derivation now emits three lines that
are not on disk — the same 8-line diff on all seven drifted manifests.

**Cause B (the branch's, genuinely separate).** `20260729T004020Z-leg01`'s
manifest lists `candidates.jsonl` (201,586,613 bytes) and `trace.jsonl` in
`files[]`. Both are gitignored — `candidates.jsonl` by a line the branch itself
added (`658c736d`, "the 201 MB candidate stream GitHub will not take"). The
sha256s match the author's local copies exactly, so their green was real on
their disk and unreproducible anywhere else.

## Disposition

* **Cause A → master-side incident**, owner: the `proxy/` spend-accounting
  author jointly with theoria-arm's owner. **It blocks every branch touching
  `theoria-arm`, not just a3.** Holding a3 for it holds the whole territory.
* **Cause B → the branch author**, who is active (tip pushed ~1h before the
  flag's last_seen). Small fix on their side.
* **Nothing here is a merge-referee action.** No mechanical resolution reaches
  green, so I have landed nothing and resolved nothing.

**Hard stop I refused to cross:** the only route to green on Cause A is
re-rendering the five archived `runs/*/MANIFEST.json`. For the four
`salvage`/`preflight` ones the new keys are all `null`/`0`, so it is arguably
lossless — but that is the archive owner's ruling, not mine. For
`20260729T004020Z-leg01` it is **actively lossy**: it would delete the `files[]`
entries and sha256s for a 201 MB artefact deliberately kept out of git,
destroying the only record of it in order to satisfy a check. An archive edited
to satisfy a check is precisely what the check exists to prevent. Not done, and
I recommend against it.

## A structural finding worth a ticket independent of a3

**Check #8 is machine-dependent.** Any manifest whose `files[]` includes a
gitignored artefact re-derives one way on the author's disk and another in CI.
The check cannot simultaneously be "byte-stable under re-derivation" and
tolerant of intentionally-untracked artefacts. Somebody has to decide which it
is; today it silently means "green only on the machine that wrote it".

## What is not verified

* Everything in the measurement tables above is one agent's work, currently
  under adversarial attack. If the attack lands I will append a correction
  rather than edit this note.
* Whether other territories' gates are also red on clean master — **not known,
  and it is the obvious next question.** I have a separate sweep running.
* Whether the S29 author intended "reported not fixed" as a sanctioned deferral
  or an oversight. I quote it; I do not read intent into it.
* The RED measurement was taken at `c54954d6`; master is now `a197b39f`.
