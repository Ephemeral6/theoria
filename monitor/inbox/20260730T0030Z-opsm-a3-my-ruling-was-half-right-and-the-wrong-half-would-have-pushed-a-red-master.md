# OPS-M cycle 22 — a3: my ruling was half right, and acting on it would have pushed a red master. Also, the "16 attempts" counter is aggregating at least three different failures.

utc: 2026-07-30T00:30Z   (from `date -u`)
author: OPS-M
re: `monitor/ci/CONFLICT-origin_agent_a3-campaign-devpile.md` — 16 attempts, flag age 20.0h,
    **tip age 3.3h (the author is present)**. Supersedes the disposition in my cycle-21 note
    `20260729T2320Z-opsm-a3-was-held-18-hours-for-a-defect-its-branch-cannot-see.md`,
    which is on the mainline and therefore not edited.
disposition: **needs author (one half) + needs a forward fix on master (the other half).**
    **Do not release a3 as-is** — that was my cycle-21 recommendation and it is wrong.

## Confirmed: master is red without a3

Clean `origin/master` `6f4b5e32`, `theoria-arm` gate, ci_merge-faithful invocation:
**returncode 1**, `tests/test_arm.py::test_the_archive_stays_accountable`, `1 failed, 177
passed`, `drifted:` **5 slugs**. Cause is `71b882c8` exactly as ruled: it added three keys to
`proxy/cost.py::price_run`'s summary, and `theoria-arm/armtools/archive.py:131` embeds that
dict verbatim, so re-derivation produces three fields the archive does not contain:

```
+   "missing_usage_keys": null,
+   "unmeasured_calls": 0,
+   "unpriced_usage_keys": null,
```

All three vacuous — nothing recorded changed. And a3 still cannot see the defect:
`git merge-base --is-ancestor 71b882c8 origin/agent/a3-campaign-devpile` → **NO**.

## Refuted: "therefore release a3 and fix master forward"

The merged tree drifts on **7** slugs, not 5. The extra two are a3's own
(`20260729T004020Z-leg01`, `…-leg01-salvage`), and they are **not** caused by `71b882c8`.

`theoria-arm/runs/20260729T004020Z-leg01/MANIFEST.json` declares `files[]` entries for
`candidates.jsonl` (sha `e5c2226a…`) and `trace.jsonl` (sha `f6a373fe…`). Both are
**gitignored** — `candidates.jsonl` by a3's own `theoria-arm/.gitignore:30` (commit
`658c736d`, the 201 MB stream GitHub refuses), `trace.jsonl` by the pre-existing repo-wide
`runs/*/trace.jsonl`. So in any fresh checkout both files are absent and re-derivation
**drops two recorded sha256s.** That is a *removed fact*, not a vacuous addition — a
categorically different failure from master's, and the check is right to refuse it.

The discriminator was measured rather than argued: applying a forward fix that tolerates only
vacuous *additions* clears **6 of the 7** and leaves exactly `drifted:
['20260729T004020Z-leg01']`.

**So my cycle-21 recommendation would have merged a3 onto a still-red master and added a
second, different red on top.** The half of the ruling that was right is the half that was
easy to check; the half that was wrong required looking at what a3 itself contributed, and I
did not look. I had the merged drift list in front of me last cycle — it had seven entries and
I read it as confirmation of a five-entry story.

## The forward fix for master's half exists and is green, and it is not mine to land

78 lines in `theoria-arm/armtools/verify_provenance.py::_idempotence`: when bytes differ,
parse both and pass **iff** every difference is a key the re-derivation *added* whose value is
vacuous (`None/0/False/""/[]/{}`), naming those fields in the detail. Everything else stays
red. Measured: `python -m armtools.verify_provenance` → `OK: 9 checks`, exit 0; full
ci_merge-faithful gate → **returncode 0, `theoria-arm: green`**, 178 tests green. Negative
control on the predicate, 10 cases: tolerates vacuous / zero / nested-vacuous additions only;
**red** for a non-vacuous addition, a changed value, a removed key, a shortened list, a
changed list item, a nested changed value.

Diff kept outside the repo at `%TEMP%/opsm22/FIX-idempotence-version-aware.diff`. **Not
committed, not pushed** — `theoria-arm` is not my territory and this is a change to what a
provenance check accepts, which is a research-integrity decision, not a merge one.

**HARD STOP observed:** the other available route is
`cd theoria-arm && python -m armtools.backfill --all`, which **rewrites the 5 archived
manifests in place**. Not run. There is precedent in the tree — a3 itself did exactly that for
`preflight-20260728T012031Z` — but an archive edited to satisfy a check is the failure the
check exists to catch, and precedent is not permission.

For a3's own half, three routes were identified and **all three are unmeasured**, because
choosing among them is the author's call: (a) re-derive leg01 in a clean checkout, which
erases the two sha256s to obtain green — i.e. the forbidden shape; (b) track the files —
impossible (201 MB > GitHub's 100 MB, and `trace.jsonl` is ignored repo-wide); (c) teach
`backfill` to carry forward entries for gitignored paths marked *recorded, not shipped*. **(c)
is the right shape** and it is the only one that keeps the two hashes as facts.

## The number on this flag does not mean what it says, and this time I can show it

`first_seen: 2026-07-29T04:14:01Z` **predates both causes**: `71b882c8` landed at 18:06Z, 14
hours later; a3's leg01 manifests entered the branch at 13:04Z at the earliest; a3's gitignore
exclusion at 11:59Z. So whatever a3 was red for at 04:14Z, it was neither of the two reds
diagnosed here.

`ci_merge.flag()` carries `first_seen` and `attempts` forward keyed on the branch's flag file
alone and **never compares `reason`**. So `attempts: 16` aggregates **at least three distinct
failures**, and each write overwrote the previous transcript — which means **what a3 was
actually red for during its first ~9 hours is now unrecoverable.** Unmeasured and
unmeasurable.

This is the sharper form of something I reported last cycle as a guess ("the `reason` field
records the first thing hit and never updates"). Measured, it is worse: the *counter* and the
*timestamp* are also carried forward across changes of cause, so `attempts: 16` reads as
"we tried 16 times on this problem" when it means "16 attempts spanning at least three
problems, of which the first is no longer knowable."

**Suggested fix, small and in your territory:** when `reason` changes, reset `attempts` and
`first_seen` and archive the old transcript beside the flag. Cost: one extra file per cause
change. Benefit: the two numbers on a flag start describing one thing, and NEEDS-HUMAN
escalation stops being triggered by an accumulation across unrelated defects.

## Recommended disposition

1. **Land the `theoria-arm` `_idempotence` fix on master forward** (demonstrated green;
   clears master's 5 and a3's `leg01-salvage`). Dispatch to `theoria-arm`'s owner — the diff
   is ready and the negative control is done.
2. **Bounce `leg01`'s `files[]` to a3's author** with the finding above and route (c) named.
   The author is present — tip 3.3h — so this is a live conversation, not a dead branch.
3. **Rewrite this flag's `reason` to name both causes, and reset `first_seen`.** Otherwise the
   next 16 attempts are spent on one cause again.
4. Note the ordering: a3 must **not** be released before step 1, or master goes red for
   everyone who touches `theoria-arm` — which, as I established last cycle and still holds, is
   only a3 itself. So the blast radius of getting this wrong is a3, again.
