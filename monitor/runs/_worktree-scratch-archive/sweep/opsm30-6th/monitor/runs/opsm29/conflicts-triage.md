# OPS-M cycle 29 — conflict triage, four stuck branches

utc: 2026-07-30 (subagent of OPS-M)
base for every merge below: `origin/master` `7972a075` ("OPS-A cycle 50: closing TO-MONITOR")
method: throwaway detached worktrees under `.worktrees/opsm29-t{1,2,3}`, each
`git merge --no-commit --no-ff <branch>` → `git diff --diff-filter=U` → `git merge --abort`.
**Nothing was pushed, nothing was merged into master, no branch was modified.**

Verdict in one line each:

| branch | classification | blocker |
|---|---|---|
| `agent/e8-ic3-scale` | **SEMANTIC** | not the 9 hunks — an auto-merged import that violates E6's independence rule |
| `agent/v5-battery-freeze` | **SEMANTIC** (+ independently red) | two different `battery/verify.py` gates; and the freeze list is 35 files stale |
| `agent/p18-audits-cover-half-onmaster` | **MECHANICAL** (one-line resolution) but branch is **red on its own tip** | new check G fails on `CITECHECK.md`, on the branch alone |
| `agent/opsm-c26-…-tie-at-zero` | **MECHANICAL** (mailbox: union; json: newest wins) | nothing; and it touches *nothing* outside the two OPS-M files |

---

## 1. `origin/agent/e8-ic3-scale`

Flag: `monitor/ci/CONFLICT-origin_agent_e8-ic3-scale.md` — tip `4ef47a1d`, first seen
2026-07-29T04:15:47Z, last seen 2026-07-30T08:53:04Z, **22 attempts**.

### Conflicting files and hunks

```
$ git merge --no-commit --no-ff origin/agent/e8-ic3-scale
Auto-merging PARTNER_SYNC.md
Auto-merging engine-rig/interop/certificate_export.py
Auto-merging engine-rig/recheck/build_cases.py
CONFLICT (content): Merge conflict in engine-rig/recheck/build_cases.py
Auto-merging engine-rig/recheck/verify_all.py
CONFLICT (content): Merge conflict in engine-rig/recheck/verify_all.py
Automatic merge failed; fix conflicts and then commit the result.

$ git diff --name-only --diff-filter=U
engine-rig/recheck/build_cases.py
engine-rig/recheck/verify_all.py

$ grep -n '^<<<<<<< HEAD' engine-rig/recheck/build_cases.py engine-rig/recheck/verify_all.py
engine-rig/recheck/build_cases.py:13
engine-rig/recheck/build_cases.py:100
engine-rig/recheck/build_cases.py:140
engine-rig/recheck/build_cases.py:1085
engine-rig/recheck/build_cases.py:1129
engine-rig/recheck/verify_all.py:50
engine-rig/recheck/verify_all.py:259
engine-rig/recheck/verify_all.py:441
engine-rig/recheck/verify_all.py:485
```

Nine hunks. Eight of them are additive on both sides and union-resolvable by inspection
(a docstring bullet list, a constants table, an import list, two different functions landing
at the same offset, two conjuncts in an `and`-chain, four summary-count keys).

The ninth, `build_cases.py:140`, is the one that looks like the merge: master has

```python
def peg_ruleset(start: str, goal: str = PEG_GOAL,
                name: Optional[str] = None) -> dict:
```

and the branch has

```python
def peg_ruleset(start: str, n: int = PEG_N, goal: str = PEG_GOAL) -> dict:
```

— the *second positional argument means a different thing on each side* (`goal` vs `n`), and
the `provenance` dict differs in shape (master emits `hand_verified`; the branch emits
`anchor` for every board wider than 4). Master's side exists because E6 added a 5-cell board,
a keyed-gate world and three pagoda certificates; the branch's side exists because E8 needs a
size gradient peg4…peg13. **Both feature sets are wanted; neither signature can express the
other.** That is a real two-implementations conflict, but it is decidable rather than a
matter of taste — the committed case files on both sides pin the expected provenance shape,
so `python -m recheck.build_cases --check` is an oracle for any candidate union. A prior
OPS-M cycle already built and measured such a union
(`monitor/inbox/20260730T041353Z-opsm-e8-and-freeze-two-gates-that-fail-for-reasons-outside-the-branch.md`:
`51 cases, 0 drifted`; `verify_all` → `VERDICT GREEN`, both the E6 pagoda rows and the E8
gradient rows present and passing). So the nine hunks are **not** what has kept this branch
stuck for 22 attempts.

### The actual disagreement

It is a line git merged **silently**, outside every conflict hunk:

```
$ grep -n "^from interop import peg1d" engine-rig/recheck/verify_all.py
47:from interop import peg1d
$ grep -n "<<<<<<<" engine-rig/recheck/verify_all.py | head -1
50:<<<<<<< HEAD
```

Line 47 is before the first conflict marker — no resolution of any hunk can touch it.
Master forbids exactly that import:

```
$ sed -n '622p;634p' engine-rig/tests/test_recheck.py
    forbidden = ("engines", "tools.", "interop")
                    token in stripped for token in forbidden):
$ git log --oneline -1 origin/master -S'"engines", "tools.", "interop"' -- engine-rig/tests/test_recheck.py
5b982a07 E6: what an engine is worth -- and the two thirds of it already measured
$ git diff --stat origin/master...origin/agent/e8-ic3-scale -- engine-rig/tests/test_recheck.py
(empty — the branch never touched the test)
```

**Classification: SEMANTIC.** The disagreement is a contract change with a downstream
effect, between two authors who never met: E6 (on master) wrote down that `recheck/` is
independent *by construction* and must import nothing from `interop`, and E8 (on the branch)
makes `interop.peg1d` its independent anchor for the wide boards precisely because
"an anchor is worth something only if it comes from somewhere else". Both are defensible
readings of "independent". A merge referee cannot pick one; the E6 rule's owner has to say
whether an anchor-only import is inside or outside it — and if it is inside, whether the rule
should be narrowed (it is currently a literal substring scan over import lines, which is
wider than the reason written above it).

### Territory gate

Touches `engine-rig/` (gate: `engine-rig/verify.py`) and `PARTNER_SYNC.md` (root, auto-merged
clean). Gate outlook after any hunk resolution: **red**, on
`engine-rig/tests/test_recheck.py::test_recheck_never_imports_the_engines`, for the reason
above. Note also that `engine-rig/pytest.ini` sets `addopts = -q`, so the CLAUDE.md-documented
`python -m pytest -q` runs `-qq` and swallows the summary line — any earlier "green" reported
from that command was reading an exit code, not a count.

---

## 2. `origin/agent/v5-battery-freeze`

Flag: `monitor/ci/CONFLICT-origin_agent_v5-battery-freeze.md` — tip `32fa34d1`, first seen
2026-07-29T04:33:05Z, last seen 2026-07-30T08:41:47Z, **21 attempts**.

### Conflicting files and hunks

```
$ git merge --no-commit --no-ff origin/agent/v5-battery-freeze
Auto-merging PARTNER_SYNC.md
Auto-merging battery/verify.py
CONFLICT (add/add): Merge conflict in battery/verify.py
Automatic merge failed; fix conflicts and then commit the result.

$ git diff --name-only --diff-filter=U
battery/verify.py

$ git diff --diff-filter=U | head -1
diff --cc battery/verify.py
index 9f972ddf,dd27b1af..00000000
--- a/battery/verify.py
+++ b/battery/verify.py
@@@ -1,501 -1,109 +1,610 @@@
```

`add/add`: one hunk covering the whole file. 501 lines on master, 109 on the branch, zero
lines in common. Confirmed by history — master's file was created independently of the
branch:

```
$ git log --oneline -3 origin/master -- battery/verify.py
1fd01893 battery V22: the discrimination pass separated nothing, and the zero was a ceiling
dd5fdb05 S14: the gates' own stdout survives a cp936 console
127edab9 S14: eleven territories get a completion gate; coverage 6/21 -> 17/21
```

### The actual disagreement

Two authors independently wrote *the* canonical territory gate for `battery/`, and they
disagree about what battery's gate is for.

* **Master's** (`S14` + `V22`, 501 lines) is a *completion* gate: four rungs — suite,
  one real offline `run_battery` recompute into a mkdtemp, artefact field/floor checks
  (`MIN_OK_VALUES = 100` measured cells, so an all-`not-applicable` spectrum is not a pass),
  and a check that the committed documents state process 1's true separation count.
* **The branch's** (`V5`, 109 lines) is a *freeze* gate: three gates — `freeze.check()`
  (the tree still matches `BATTERY_V1.md`), the suite (with an explicit "deselected counts as
  failed" and a `< 200 passed` floor), and readings drift reported-but-tolerated.

`monitor/gates.py:53` treats `verify.py` as the single canonical gate name, so there is one
slot and two claimants. Neither is wrong; the ruling needed is whether battery's gate is
"did the pipeline actually measure something" or "does the tree still match its freeze" —
or, most likely, a union with V5's freeze/readings rungs appended to master's four.

**Classification: SEMANTIC.**

### …and the resolution will not make it green

The conflict is not the blocker. Measured on the merged tree with the conflict resolved
`--theirs` (i.e. V5's own bytes for `battery/verify.py`, the most favourable case for the
branch):

```
$ python -c "from battery import freeze; print('freeze.check failures:', len(freeze.check()))"
freeze.check failures: 35
  - battery/audit/gaming.py hashes to sha256:0ade8fbb… but BATTERY_V1.md says sha256:23954c11…
  - battery/metrics/economy.py hashes to sha256:99bb1003… but BATTERY_V1.md says sha256:be3c44d3…
  - battery/METRICS.md hashes to sha256:c6861db5… but BATTERY_V1.md says sha256:b04a3467…
  … (35 total)

$ python -m pytest battery/tests/test_freeze.py -q
FAILED battery/tests/test_freeze.py::test_the_freeze_holds_on_the_real_tree
FAILED battery/tests/test_freeze.py::test_the_fixture_reproduces_the_real_verdict
FAILED battery/tests/test_freeze.py::test_an_edited_artefact_is_reported_but_does_not_fail
FAILED battery/tests/test_freeze.py::test_rendering_the_blocks_reproduces_the_record
4 failed, 19 passed in 1.61s
```

`battery/verify.py` is itself pinned by the branch's own freeze list
(`battery/freeze.py:161`, bucket `FREEZE`), so *any* resolution changes one of the 36
pinned digests — but the other **35** failures are files master edited after V5 took the
freeze, and no merge resolution can clear them. This corroborates and does not extend
`monitor/inbox/20260729T184500Z-opsm-v5-i-corrected-a-wrong-reason-with-another-wrong-reason.md`,
which reached the same 35/36 split from the other direction. **The branch needs its author to
register `BATTERY_V2`; it is not a merge-referee problem.**

### Territory gate

Touches `battery/` (gate `battery/verify.py` — the conflicted file itself) and
`PARTNER_SYNC.md`. Outlook: **red under either resolution**, since rung 1 of master's gate
runs `pytest battery/tests` and the branch adds `test_freeze.py`, which fails 4/23 as shown.
Second-order hazard already on record: landing V5 would leave `battery/freeze.py` and
`BATTERY_V1.md` on master describing a tree that no longer exists, which is a trap for the
next author of `battery/` rather than for V5.

---

## 3. `origin/agent/p18-audits-cover-half-onmaster`

Flag: `monitor/ci/CONFLICT-origin_agent_p18-audits-cover-half-onmaster.md` — tip `0eb876f7`,
first seen 2026-07-30T05:00:19Z, last seen 2026-07-30T09:02:01Z, 5 attempts.

### Conflicting files and hunks

```
$ git merge --no-commit --no-ff origin/agent/p18-audits-cover-half-onmaster
Auto-merging papers/phase1-workshop/verify_paper.py
CONFLICT (content): Merge conflict in papers/phase1-workshop/verify_paper.py
Automatic merge failed; fix conflicts and then commit the result.
```

Exactly one file, exactly one hunk — the `CHECKS` table:

```
 <<<<<<< HEAD
    ("A GENERATED", "PAPER.md == assemble(sections/)", check_generated, False),
    ("B PATHS", "every cited path resolves, unambiguously", check_paths, True),
    ("C FIGDATA", "figure extractors are byte-deterministic", check_figdata, False),
    ("D NOSECRET", "no credential value in any published file", check_nosecret, False),
    ("E UNCITED", "every quantitative claim block cites an artefact", check_uncited, True),
    ("F BARE", "no citation is an ambiguous bare filename", check_bare, True),
 =======
    ("A GENERATED", "PAPER.md == assemble(sections/)", check_generated),
    … (same six, 3-tuples)
    ("G AUDITSTAMP", "every audit report pins what it audited, correctly",
     audit_stamp.check),
 >>>>>>> origin/agent/p18-audits-cover-half-onmaster
```

Master widened every row from a 3-tuple to a 4-tuple (adding `reads_sections`, consumed by
`for tag, blurb, fn, reads_sections in CHECKS:` in `main()`); the branch appended a seventh
row as a 3-tuple. No line of prose or logic contradicts.

**Classification: MECHANICAL.** The rule: keep master's six 4-tuples verbatim and append the
branch's G row with the fourth field filled in. The fourth field is not a judgement call —
it is "does this check read `sections/` rather than `PAPER.md`", and
`papers/phase1-workshop/audit_stamp.py` reads `PAPER.md` and the audit reports and never
opens `sections/` (`target: papers/phase1-workshop/PAPER.md`, `_history_blobs(root, rel)`
over `PAPER.md`'s git history), so the value is `False`. Everything else in the branch's
44-line diff to that file (docstring, `import audit_stamp`, the `--explain-uncited` prose)
auto-merged clean.

I applied that resolution in the worktree to check it, and it is syntactically and
semantically fine — but the result is red:

```
$ python papers/phase1-workshop/verify_paper.py --quiet
[PASS] A GENERATED … [PASS] F BARE
[FAIL] G AUDITSTAMP -- every audit report pins what it audited, correctly
  FAIL      CITECHECK.md -- no ```audit-stamp block
  ok        REVIEW-2026-07-30.md -- binding on `PAPER.md` @ 6b633fcc, 3729 lines, 237872 bytes
  ok        REVIEW.md -- stale, pinned @ 4208b69c (31.9% of `PAPER.md` as it now is), superseded by REVIEW-2026-07-30.md
verify_paper: FAIL (1/7) -- G AUDITSTAMP
```

**This is not caused by the merge.** The same run at the branch's own tip `0eb876f7`,
unmerged, in a separate worktree, produces byte-identical output — `FAIL (1/7)`, same
`CITECHECK.md -- no ```audit-stamp block`. `CITECHECK.md` exists at the branch's merge-base
`b5998e5d`, so the branch shipped a gate that its own tree fails: it stamped `REVIEW.md` and
`REVIEW-2026-07-30.md` and left `CITECHECK.md` unstamped. Fix is one stamp block in
`CITECHECK.md`, by its author.

### One thing I could not settle

There is a sibling branch `origin/agent/p18-audits-cover-half-the-paper` (also flagged),
7 commits vs this branch's 4, based on an older master. It is **not** an ancestor of
`onmaster` (`git merge-base --is-ancestor` → NO) and carries three later commits
(14:46–15:34 +0800, vs `onmaster`'s 12:36–12:58) including
`papers/…/citecheck-A-abstract-to-s3.md` at **810 lines against `onmaster`'s 77** —
"citecheck slice A, actually done — 12 findings where the stub asserted 8". So the two
branches are **not** duplicates and `onmaster` is **not** simply the rebased newer one:
merging `onmaster` would land the shorter, stubbier slice A. Which of the two is the one
to keep — or whether `the-paper`'s later work needs re-rebasing onto `onmaster` — is a call
for P18, not for the referee. I am flagging it rather than claiming STALE, because the
evidence points both ways.

### Territory gate

Touches `papers/` only. `papers/verify.py` is a delegator that shells out to every
`verify_paper.py` it finds (`GATE_NAMES = ("verify_paper.py", "verify.py")`). Outlook:
**red**, on G, until `CITECHECK.md` is stamped. After that, likely green — A–F all pass on
the merged tree today.

---

## 4. `origin/agent/opsm-c26-never-tried-branches-tie-at-zero`

Flag: `monitor/ci/CONFLICT-origin_agent_opsm-c26-never-tried-branches-tie-at-zero.md` —
tip `ad55d10d`, first seen 2026-07-30T05:36:14Z, 4 attempts.

### What else the branch changes (the question asked)

**Nothing.** The branch is a single commit and touches exactly the two conflicted files:

```
$ git diff --stat origin/master...origin/agent/opsm-c26-never-tried-branches-tie-at-zero
 monitor/mailbox/OPS-M.md      | 431 ++++++++++++++++++++++++++++++++++++++++++
 monitor/ops-status/OPS-M.json |   9 +-
 2 files changed, 432 insertions(+), 8 deletions(-)

$ git log --format="%h %ci %s" origin/master..origin/agent/opsm-c26-never-tried-branches-tie-at-zero
ad55d10d 2026-07-30 12:54:52 +0800 OPS-M cycle 26: five branches the queue has never once looked at, because every never-tried branch ties at sort key 0.0
```

No code, no tests, no `monitor/*.py`, no `PARTNER_SYNC.md`. Landing it lands OPS-M's own
cycle-24/25/26 report paragraphs and nothing else.

### `monitor/mailbox/OPS-M.md` — both sides only appended

merge-base is `1a86d67d`. Neither side deleted or edited a single pre-existing line:

```
$ git diff --numstat 1a86d67d origin/master -- monitor/mailbox/OPS-M.md
201     0       monitor/mailbox/OPS-M.md
$ git diff --numstat 1a86d67d origin/agent/opsm-c26… -- monitor/mailbox/OPS-M.md
431     0       monitor/mailbox/OPS-M.md
```

(`0` in the deletions column on both sides; a grep for `^-[^-]` in either diff returns 0.)

The two blocks are disjoint and time-ordered:

```
headings added by MASTER side:
  ## TO-MONITOR 2026-07-30T06:40:42Z
  ## TO-MONITOR 2026-07-30T06:52:26Z （更正上一段：我不是 cycle 23，是 cycle 27；…）
headings added by BRANCH side:
  ## TO-MONITOR 2026-07-30T01:02:06Z
  ## TO-MONITOR 2026-07-30T03:03:53Z
  ## TO-MONITOR 2026-07-30T03:49:11Z
  ## TO-MONITOR 2026-07-30T04:30:55Z （cycle 25 收尾）
  ## TO-MONITOR 2026-07-30T04:34:02Z （更正上一段关于 a3 的那一行…）
  ## TO-MONITOR 2026-07-30T04:51:39Z
```

None of the branch's six headings already exists on master (grep count 0 for each), so
nothing here is a duplicate arriving by another route.

**Classification: MECHANICAL — union merge, both sides kept, chronological order.**
The rule: concatenate the branch's six paragraphs (01:02:06Z … 04:51:39Z) *before* master's
two (06:40:42Z, 06:52:26Z), preserving each side's internal order — master's 06:52 paragraph
supersedes its own 06:40 one and must stay after it.

This is exactly the case `monitor/mailbox/PROTOCOL.md` defines as correct: "在自己邮箱末尾
追加一段 `## TO-MONITOR <UTC>`". **No discipline violation on either side** — both sides
corrected earlier paragraphs by appending a `更正上一段` paragraph rather than editing in
place, which is the rule working as written.

### `monitor/ops-status/OPS-M.json` — not append-only, newest wins

```
HEAD:   {"id": "OPS-M", "utc": "2026-07-30T07:46:31Z", "cycle": 28, …}
BRANCH: {"id": "OPS-M", "utc": "2026-07-30T04:48:02Z", "cycle": 26, …}
```

One-line heartbeat snapshot; both sides replaced the merge-base line in place, which is what
this file is *for* (it is a state file, not a board). **MECHANICAL: take master's** — cycle 28
at 07:46:31Z strictly supersedes cycle 26 at 04:48:02Z, and taking the branch's would rewind
OPS-M's published heartbeat by 3 hours and 2 cycles. Nothing is lost: the branch's cycle-26
note text is preserved in full in the `OPS-M.md` paragraphs being unioned above.

### Territory gate

Touches `monitor/` only. `monitor/verify.py` and `monitor/verify.sh` contain no reference to
`ops-status` or `mailbox` (grep: no matches), so neither file is under the gate's eye.
Outlook: **green** — the merge changes no executable line in the territory.

---

## Cleanup

Worktrees `.worktrees/opsm29-t1`, `-t2`, `-t3` were used for the merges and removed. All
merges were aborted or discarded; `origin/master` and all four branches are untouched.
