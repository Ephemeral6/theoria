# V23 — findings

Worker W-1681, branch `agent/v23-figures-sources-absent`, base `580c645d`.
Zero API calls. Zero sealed-pile contact. Territory `figures`, plus one
`monitor/inbox/` note and one appended `PARTNER_SYNC.md` paragraph.

---

## F-1 — the gate the item reports as red is green at `580c645d`, and the window it was red in is not the one the item guesses

`figures/verify.sh`, run in this worktree at `580c645d` before any edit of mine
(`verify.BEFORE.txt`, exit 0):

```
== 4. data-source hashes match the committed manifest ==
ok  (61 sources hashed)
...
VERIFY: green. Two builds byte-identical, sources unchanged, all artefacts present.
```

The four `ABSENT0000…` lines the item names are gone, and history says when:

| when (UTC) | event |
|---|---|
| 2026-07-27T18:23Z | the four shards are **created on disk** in the main checkout by the A14 campaign run (filesystem ctime; the earliest record inside `ledger.ar25.jsonl` carries the same stamp) |
| 2026-07-28T00:22Z … 02:59Z | last written (mtime) |
| 2026-07-28T09:06:26Z | `87751026` P4 commits `SOURCES.sha256` recording all four as `ABSENT0000…  [absent-optional]` |
| 2026-07-29T14:45:44Z | `9307f139` A14 commits the four files — "the four campaign artefacts were paid for and were in nobody's git" |
| 2026-07-29T16:19:27Z | `a5f597dd` regenerates the manifest and rebuilds fig02/figure6 with it. 0 `ABSENT` lines |

**Read the first two rows against the third.** The files were on disk for fifteen
hours before P4 committed a manifest saying they were absent. So the `ABSENT`
lines were not a true statement that later went stale — they were **false when
they were written**, and gate 4 in the main checkout was red from the moment that
manifest landed: 2026-07-28T09:06:26Z to 2026-07-29T16:19:27Z, **31 h 13 m**.

How does a build write `ABSENT` about a file that is on disk? By running somewhere
the file is not. P4 worked on `agent/p21-figures` in a linked worktree, and the
shards were untracked, so they existed in the main checkout and in no worktree.
`sources.py:64-65 exists()` tests the filesystem; `:773-776` writes the sentinel
when a source is absent. **The defect and its invisibility are the same mechanism**
— a gate answering truthfully about a tree that is not the one anybody reads. It
produced the wrong manifest in P4, kept gate 4 green in CI for the whole 31 hours
(F-2b), and produced V20's confident false negative a day later. Three separate
consequences, one cause, and none of them detectable from inside the transcript,
because a green from the wrong tree is byte-identical to a green from the right
one.

Gate 4 itself behaved correctly throughout: it compares the committed manifest
against one recomputed from the tree it is standing in, and it said so accurately
in both trees. `sources.py`'s `expected` mechanism is also right — a known-absent
input should be *recorded* as absent rather than forgotten. What was missing was
any reason to believe the tree under the gate was the tree that matters.

So item task 1 was already discharged at my own base commit, and by the sanctioned
method — `a5f597dd`'s message says "Regenerated with `figures/build_all.py`,
nothing hand-picked." I verified rather than assumed: a fresh
`sources.write_manifest()` into a temp path outside the repo is byte-identical to
the committed file (`d42812c4…`), and every one of the 61 paths' last commit is an
ancestor of `a5f597dd`. **True drift at `580c645d`: 0 of 61 lines.**

That narrows task 2 rather than dissolving it. The gate was red for ~31 hours over
61 MB of paid artefacts and nothing said so. And it leaves task 3 with a real
finding of a different kind — see F-3.

---

## F-2 — why nobody knew: gate outcomes exist only as per-branch merge verdicts, and no surface anywhere reports a gate's state by territory

> **Corrected after adversarial review.** This section first ran under the
> heading *"and this defect arrived from outside the territory"*, and that was
> wrong — F-1 above establishes that the bad manifest was written inside
> `figures/`, by P4, in a worktree that lacked the files. The structural finding
> below survives that correction and is not weakened by it: the reason a red gate
> reaches no reader is that gate results exist only as per-branch merge verdicts.
> What changes is that cross-territory arrival is one *instance* of the gap
> rather than its definition — and the eleven `a7*` shards, committed by
> `baseline-arms` on 2026-07-28, are the instance that actually fits.

`figures/verify.sh` has exactly two callers.

1. **The merge gate, automatically but conditionally.** `monitor/reflex.py:306`
   runs `monitor/ci_merge.py` every reflex tick; `ci_merge.py:526` → `gates.py:135-139`
   finds `verify.sh` and `ci_merge.py:543` executes it. Exit codes are **not**
   ignored and output is **not** swallowed.
2. **`monitor/gates.py:432-442`, `--run figures` / `--run-all` — a human typing it.**
   `gates.run()` has no caller anywhere outside `monitor/tests/test_gate_outcomes.py`.

There is no `.github/`, no `Makefile`, and — this is the load-bearing one — **no
registry anywhere of "gates that must be green".** The set is derived per branch
at `ci_merge.py:496` (the branch's own diff) intersected with what the tree
offers. That is deliberate (`gates.py:1-10`: *a table maintained by hand is a claim
about the tree that nothing checks against the tree. So: ask the tree*), and it
has a consequence nobody had written down.

Four mechanisms, compounding:

**(a) The path filter.** `ci_merge.py:460-463` reduces a branch's changed files to
their first path segment; the gate for territory `d` runs only if `d` is in that
set. The commit that broke figures touched only `baseline-arms/`. From
`monitor/reflex.log`, 2026-07-29T15:23:40Z:

```
MERGED origin/agent/a14-campaign-json-untracked (dirs: PARTNER_SYNC.md,baseline-arms; gates: verify:baseline-arms(verify.py))
```

`figures/verify.sh` was never run against the merge that broke it. **A gate that
runs only when its own territory is touched cannot see a defect introduced from
outside it** — and "one territory's artefact is another's declared source" is the
normal condition in this repo, not an exception.

**(b) The CI tree structurally could not see it.** `ci_merge.py:513-515` builds its
test tree with `tempfile.mkdtemp()` + `git worktree add --detach origin/master`.
The four shards were untracked until `9307f139`, so they do not exist in any fresh
worktree. `sources.py:64-65 exists()` tests the filesystem and `:773-776` writes
the `ABSENT` sentinel when a source is absent — so in CI the fresh build
reproduced the committed `ABSENT` exactly. Verified on a worktree pinned before
the add: it carries 4 `ABSENT` rows and no shard on disk, while the main checkout
holds `ledger.ar25.jsonl` at 6,267,799 bytes. And per F-1, the same mechanism is
what wrote those `ABSENT` lines in the first place — so CI was not failing to
detect a defect introduced elsewhere, it was reproducing the defect's own premise
and agreeing with it.

> **Corrected after adversarial review.** This paragraph first claimed gate 4 was
> *"green in CI and red in the working tree, simultaneously, for the whole
> 31-hour window"*. The mechanism is right and the duration is not. Two things
> break it, both from the record:
>
> * **Mid-window, a clean tree was red too, for unrelated reasons.** RES-3
>   measured five mismatches at `baf16714` (2026-07-28T15:10Z) **in a clean
>   worktree** — `cold-start-a0`/`cold-start-a2` sources that had moved under the
>   manifest (`monitor/inbox/20260728T153500Z-RES-3-figures-verify-is-red-on-master.md`).
>   My own history probe puts the peak of that episode at 7 drifted lines
>   (`history_probe.txt`). So for part of the window CI was red as well, just
>   about something else.
> * **CI went red on the shards as soon as master carried them.** A14 merged at
>   2026-07-29T15:23:40Z; `monitor/ci/merge.log:1865` records
>   `2026-07-29T15:31:08Z FLAG origin/agent/p17-bare-filename-citations: verify
>   gate red in figures (verify.sh)` seven minutes later, held until `:1893`
>   (17:37:55Z). Once the shards were tracked they existed in the throwaway
>   worktree, and the gate behaved correctly there.
>
> **The honest figures.** Gate 4 red in the *working tree*:
> 2026-07-28T09:06:26Z → 2026-07-29T16:19:27Z, **31 h 13 m** — that number stands,
> re-anchored to when the false manifest was committed rather than to when the
> files appeared. Gate 4 green in CI *while* red in the working tree: bounded by
> `abd8d0cb` clearing the unrelated drift (2026-07-29T05:15:53Z) and A14's merge
> (15:23:40Z), so **about 10 hours**, not 31. Before that both trees were red;
> after it both were.

This is also what produced V20's false negative. V20 ran the gate in its own
linked worktree, got ten green, and concluded the ticket was mistaken
(`24b631f4`) — right about the drift count, wrong about the tree, and there was
nothing in the transcript to tell it which tree it had measured. RES-1 had already
named the class: *「验收脚本在错的树上跑出的绿灯，与在对的树上跑出的绿灯，逐字节一模一样」*
(`monitor/inbox/20260729T1440Z-RES-1-worktree-cwd-green-on-the-wrong-tree.md`).
Its recommendation — print the resolved tree and branch on line 1 — had not been
implemented anywhere. It is implemented in `figures/verify.sh` as of this run.

**(c) When the red did reach CI, it was filed against an innocent branch.**
`flag()` writes `monitor/ci/CONFLICT-<branch>.md`, keyed by branch and never by
territory. Seven minutes after A14 merged, `monitor/ci/merge.log:1865`:

```
2026-07-29T15:31:08Z FLAG origin/agent/p17-bare-filename-citations: verify gate red in figures (verify.sh)
```

held through `:1874`–`:1887` until `:1893` (17:37:55Z). A figures defect recorded
as a property of an unrelated citations branch — which is why it read as p17's
problem. So the item's "the merge log never mentioned it" is slightly wrong: the
merge log mentioned it once, as an accusation against the wrong branch.

Cite it from `merge.log`, not from the CONFLICT file. The first draft of this
finding cited `monitor/ci/CONFLICT-origin_agent_p17-bare-filename-citations.md:3`,
which is **untracked and rewritten in place by `flag()`** — by the time an
adversarial reviewer checked, it read `reason: push rejected (race?)`. A citation
to a file that overwrites itself is not a citation, and this whole ticket is about
claims nobody can re-derive. `merge.log` is append-only and tracked.

**(d) The one probe that mentions gates counts gates that exist, never gates that
pass.** `monitor/scan.py:748-811 probe_verify_gates()` measures board tickets
naming a nonexistent verify path, and `survey["ungated"]` — territories with *no*
gate. It never runs a gate and never reads an outcome; its green means "every
territory has a gate". Sharper: `gates.py:252-253` already computes
`survey["decorative"]` — gates with no declared negative sample — and
`probe_verify_gates` reads only four other fields, so **`decorative` is computed
and then discarded**. `figures/verify.sh` declares no `negative-sample:` line, so
it sits in exactly that dropped list. `monitor/ops-status/*.json` contains zero
occurrences of "figures"; `monitor/index.html` has no gate row for figures and
never mentions `verify_gates`.

**The answer to the item's question, in one sentence:** the red gate produced no
signal because gate results in this repo exist only as per-branch merge verdicts,
and this defect belonged to no branch — it was created by a legitimate merge in
another territory, was invisible in the throwaway worktree the gate runs in, and
there is no per-territory gate status surface anywhere for it to appear on. A red
gate nobody looks at and no gate at all are the same thing, and here the way they
became the same thing is that nobody was looking *by territory*.

**Smallest fix, and it is not in my territory.** One probe in the registry at
`monitor/scan.py:1217-1231` that calls the already-written, already-tested
`gates.run(ROOT, t)` per gated territory **on the real checkout**, reporting
red/broken by territory name via the existing `gates.SEVERITY`. One function plus
one dict entry, reusing machinery that today has no caller outside its own tests.
Cadence should be slower than the reflex tick, because `figures/verify.sh` builds
everything twice. Filed to `monitor/inbox/`.

Prior art, so this is not re-derived a fifth time: RES-3 found gates 4 and 6 red
on master **by hand** on 2026-07-28 and filed
`monitor/inbox/20260728T153500Z-RES-3-figures-verify-is-red-on-master.md`,
concluding 「闸门正确地红了」 — correct, and it did not ask why the red had no
reader. `monitor/runs/20260729T1045Z-S29-triage-the-five-red-gates/FINDINGS.md`
established that gates run on the merge result and diagnosed the same
cross-territory shape for two other branches, but treated figures' red as a stale
branch flag. Three sessions saw the symptom; none of them owned the question.

---

## F-3 — the 61 lines, adjudicated: zero digest drift, and fifteen false assertions no gate could see

Item task 3 asked for a per-line ruling and forbade a wholesale re-hash. Done both
ways round — a fresh manifest generated to a temp path outside the repo and diffed
against the committed one, and every path's git history checked independently.

**Digest column: 0 of 61 drifted.** Every path's last commit is an ancestor of
`a5f597dd`. `a5f597dd` was also a complete closure, not a hash-only patch: it
rebuilt `csv/fig02_bill_shape.csv`, both `out/{light,dark}/fig02_bill_shape.*`,
all six `paper/*/figure6_bill_shape.*`, the index, `captions/figure6.md` and
`audit/reconcile_cost.csv` in the same commit. There is no stale plate hiding
behind the green manifest.

**Where "13 of 50" came from — measured here, by me, with the script that did it.**
`history_probe.py` / `history_probe.txt` in this directory. The first draft of this
section published six numbers taken from a delegated audit that I had not
re-derived; an adversarial review reproduced none of them, and it was right to
refuse them. They are withdrawn. What follows I measured.

The metric is stated before it is computed, because that is where the previous
attempts went wrong. The ticket alleges *committed* drift — 「已提交的漂移（工作树
是干净的）」 — so the question is whether the digest a manifest revision recorded
matches the content of that same path **as that same commit had it**, read from
`git cat-file` and never from a working tree.

| manifest revision | entries | matched | committed drift | unverifiable |
|---|---|---|---|---|
| `87751026` | 43 | 39 | **0** | 4 |
| `f0e43896` | 47 | 43 | **0** | 4 |
| `9239eb1c` | 50 | 46 | **0** | 4 |
| `059f6ed1` | 54 | 50 | **0** | 4 |
| `abd8d0cb` | 61 | 57 | **0** | 4 |
| `a5f597dd` | 61 | 61 | **0** | 0 |

**Committed drift has never existed, at any revision.** The four unverifiable
lines are the four dev-pile shards: untracked, so git never held their content and
no revision can be checked against history. That they are unverifiable *by
construction* is the finding, not a gap in the probe.

**Both of the ticket's numbers now have honest answers, and one of them is
reproducible.** My first draft said the file "has had 61 lines rather than 50 since
P8's discovery rules landed". That is false and I withdraw it: the counts are
43 → 47 → **50** → 54 → 61 → 61, so **50 is exactly `9239eb1c`'s entry count**
(2026-07-28T11:34Z). The ticket's denominator is not invented, it is two
regenerations stale. The numerator is the one that fails: drift *between*
regenerations — the manifest standing still while its sources move, which is the
only reading under which a positive count is possible — peaked at **7**, at
`059f6ed1` measured against the tree just before `abd8d0cb`:
`BUDGET_REPORT.md`, `THEORIZE_LOG.md`, `candidates.jsonl` and four
`theoria-arm/runs/*/MANIFEST.json`. RES-3 counted five of those at `baf16714` on
2026-07-28, mid-episode. **7 is the maximum this file ever reached. 13 exceeds it,
and reproduces under no reading I could construct.**

**And the number was never audited at all.** It does not originate in an audit. It
first appears as a hand-written dashboard cell — `monitor/spec.py:1217`, commit
`fc6f1706` (2026-07-29T02:06:19Z), a repo-wide progress re-scoring that touched no
`figures/` file and left no run directory: `"note": "…50 源哈希 13 条已漂移"`. It was
then promoted to 「审计（2026-07-29）逐行确认」 in
`monitor/board/done/V20-figures-pipeline-red.RES-3.md:9,14` and copied verbatim
into V23. **The line-by-line audit the ticket invokes does not exist.** V20 reached
the same conclusion by its own route (*"61 entries with 0 drift, not 50 with 13"*)
and was held on a merge conflict, so the number was signed out a second time and a
third worker nearly re-measured it. That is the whole argument for this file
existing.

**Status column: 15 of 61 lines were asserting something false, and this is the
finding.** A manifest line makes three claims — a digest, a path, and a status.
Two are measured. The third is not: `sources.py:774` writes `[tracked]` or
`[untracked]` from `Source.tracked`, a boolean somebody declared. All fifteen
`baseline-arms/out/shards/ledger.*.jsonl` shards became committed while the
`envelope_ledger` rule still read `tracked=False`, so fifteen lines said
`[untracked]` about files git tracks, and `paper/index.json` published
`"tracked": false` for the same fifteen — into the release index.

**Not A14, and the correction matters for the dating.** A14 (`9307f139`,
2026-07-29T14:45Z) committed **four** of the fifteen — the dev-pile ledgers.
`baseline-arms`' own routine commits brought the eleven `a7*` ones a day earlier,
on 2026-07-28 (`d4ccbb54`, `babdd83d`, `99bd8017`, `aa546acf`, `4d59cbe3`). So the
false-status class was not born at A14: the first manifest revision to print
`[untracked]` about an already-committed file is **`059f6ed1`,
2026-07-28T14:21:44Z**, and it names four `a7*` shards. That is ~35 hours before my
base commit, not the ~26 the A14 story implies, and it means A14 is where the
defect became impossible to miss rather than where it began. My first draft said
"A14 committed all fifteen" in three places; corrected here, in `figures/STATUS.md`
and in `sources.py`.

**Gate 4 cannot audit this, by construction.** It diffs a committed manifest
against a freshly generated one; both come from `sources.py`; a wrong declaration
appears identically on both sides. This is the same shape as the two failures
`PLAN.md` §§264-274 and 637-657 already record — *an oracle that asks the module
under audit what to expect can only prove that module self-consistent* — arriving
this time not through a function call or an argument but through the manifest's own
status column. Ruling, in the item's own vocabulary: 15 × `DECLARATION-CHANGED`,
46 × `MANIFEST-CURRENT`, 0 × `UPDATE-HASH`, 0 × `REGENERATE-FIGURE`, 0 ×
`SUSPICIOUS`.

Three consequences of that stale declaration, all live at `580c645d`:

1. `tracked=False` short-circuits the git filter in `_scan` (`if not rule.tracked:
   return named`), so a stray untracked `ledger.*.jsonl` dropped into the shard
   directory would be hashed and drawn here and not on a clean checkout — the
   exact hole `_tracked_paths`' own docstring says it exists to close, left open
   on the largest input family in the registry.
2. `floor=0` with `optional=True` meant deleting all fifteen kept
   `check_required()` and `floor_violations()` green (both measured: `[]`, `[]`)
   while fig02's bill silently lost the entire envelope campaign. *"A family that
   silently emptied out reads exactly like a family that is fine"* is this module's
   own sentence about why floors exist, and its biggest family was the exception.
3. `untracked_inclusions()` had become unreachable — it skipped every
   `tracked=True` rule on the argument that `_scan` already filters those, which
   is true for rules and false for the thirty-odd hand-written `Source` entries,
   which are never filtered at all. **The one class it covered was the class that
   could not occur; the class that could occur was the one it skipped.**

**What was changed.** `envelope_ledger` → `tracked=True`, keeping `optional=True`
and `floor=0`, with `expected`/`expected_note` dropped (all four are discovered
now, so the tuple was suppressed dead weight carrying a false note) and the whole
reversal recorded in place as a `V23 CORRECTION` comment rather than a silent
overwrite. `untracked_inclusions()` widened from rules to every declared source.
`tracking_mismatches()`, `tracked_but_missing()` and `untracked_but_present()`
added; the first two wired into `check_required()`, all three printed by
`build_all.py`. Then regenerated with `build_all.py` — never hand-edited;
`Theoria.md` §242 constraint 4 (生成物禁止手改) makes hand-editing the prohibited
move *even when the resulting bytes would be correct*, and `verify.sh` gate 4's own
failure message prescribes regeneration.

> **This is the second version, and the first one was worse than what it
> replaced.** I set `floor=15, optional=False` on the reasoning that a tracked
> file going missing is a broken checkout and should stop the build. An
> adversarial review killed it on evidence I had not looked for:
> `release/LICENCE_POSTURE.md` classifies these shards **class B — "NEEDS WRITTEN
> PERMISSION. Default: excluded"**, to ship as a digest plus a reproduction
> script. So the default release tree has zero shards, and `floor=15,
> optional=False` turns gate 0 red there before any other gate runs — breaking
> the exact reproduction path `release/REPRODUCING.md` documents. I would have
> shipped a new failure mode strictly worse than the one I was fixing.
>
> The same review landed a second hit: **15 was a hand-copied count of precisely
> the kind this territory forbids.** `PLAN.md` house rule 5 — *a completeness flag
> that is asserted is a completeness flag that will be wrong*. It was, and my
> first instinct was to defend it as a high-water mark like `theoria_run`'s 4.
> That defence is right for a family nothing excludes downstream and wrong for
> this one.
>
> Both objections have one answer: derive it. `tracked_but_missing()` asks git
> which members are committed and requires each of *those* to be on disk.
> Strictly stronger than `floor=15` — it catches a sixteenth committed shard going
> missing too — silent where git cannot be asked, so a release tarball still
> builds, and carrying no number to age. `untracked_but_present()` closes the
> other side: a file that matches the rule and is not committed is now warned
> about rather than silently dropped, because "paid data on disk that no plate
> draws" and "no such data" must not look the same.

**The declaration flip changed no number and no pixel.** 30 assertions across
`SOURCES.sha256` and `paper/index.json`; `csv/`, `out/`, `paper/captions/` and
`paper/INDEX.md` byte-identical. That is the evidence separating "a false statement
about the tree" from "a stale figure". fig02's plate moved only afterwards, for a
separate reason: it prints the word "optional" about these shards on its own face,
and that word had to go with the declaration.

**A gate for it, because a fixed instance is not a fixed class.**
`figures/check_tracking.py`, wired as gate 13. It reads the committed *artefact*
and re-derives all three of a line's claims from authorities the artefact cannot
influence: the status from `git ls-files`, the digest from its own sha256, the
`ABSENT` sentinel from the filesystem. **It must never import `sources.py`** — that
constraint is in its docstring, because it is the whole reason it works. Its
negative control plants one defect per claim (a `[tracked]` line relabelled
`[untracked]`, a digest corrupted in its first byte, a present file recorded
absent) and requires a refusal for each; all three refuse
(`check_tracking.selftest.txt`).

Shown failing on the tree it was written for, which is the standard this directory
holds probes to: at `580c645d`, where `verify.sh` was green on all thirteen gates,
`check_tracking.py` reports **15 problems** and exits 1
(`check_tracking.BEFORE.txt`).

**Not changed, and why.** `theoria_run`'s `floor_note` says "4 of the 9 directories
under `theoria-arm/runs/` … on 2026-07-28"; there are 22 directories now. The
sentence is date-stamped and was true on its date, the floor of 4 is still correct,
and gate 8 accounts for the other 18 by name on every run. Rewriting a true dated
statement to make it a description of today would cost the record and buy nothing.

**`probe_log.*.jsonl` should stay undeclared.** Fifteen tracked files sit beside
the fifteen ledger shards and no rule matches them. They carry HTTP transport
records — `{url, method, status, elapsed_ms, request_*, response_summary, …}` — no
cost, no `usage`, no `step_idx`, no `action`; nothing under `figures/` references
them, so no plate quotes an unhashed number from one. Declaring them would add 30
manifest lines and ~35 MB of per-build hashing for data no plate uses. Worth
recording because the instinct is wrong in a specific way: **widening the pattern
to `*.jsonl` breaks the build** — `fig02_bill_shape._classify()` raises on the
first probe_log row, since it has no `usage` and none of the `_ENV_STEP_REQUIRED`
fields. Fail-closed and correct, but it means "just widen the glob" is a
regression, not a fix. The residual gap is real and belongs to gate 8:
`check_coverage.py` walks `theoria-arm/runs` and `baseline-arms/out` (pattern
`pilot_*.json`) as literals, so `out/shards/` is walked by no coverage probe at
all. A future cost-bearing shard family landing there under a name outside
`ledger.*.jsonl` would reach no gate. Not fixed here: extending that probe means
extending its negative control to narrow the rule, and doing that in the same
change as the rule edit is how the last two versions of that probe went wrong.
Recorded in `figures/STATUS.md` as an open gap.

**Found by writing the probe that proves the fix, and bigger than the fix:
`figures/` cannot build in a default release tree, and never could.**
`release/LICENCE_POSTURE.md:48` puts `baseline-arms/ledger.jsonl` in class B —
*"NEEDS WRITTEN PERMISSION. Default: excluded"* — and `sources.py` declares it as
the `pilot_ledger` Source with `optional=False`. So in a class-A-only tree
`check_required()` reports the required ledger missing and gate 0 goes red before
any other gate runs. Not the shards: **the pilot ledger**. `release/reproduce.py`
nonetheless lists `python build_all.py` in `figures/` as the reproduction command
and `release/REPRODUCING.md` tells a reader to run `bash figures/verify.sh`.

So my `floor=15` mistake was worse than "would have broken the release" — it would
have added a *second* reason to a build that was already broken there for a first,
and neither is visible to any gate, because no gate runs in a release tree. That is
the same shape as this whole ticket one layer out. `release_tree_probe.py` in this
directory is the executable form: it runs the real functions against a synthetic
tree with no `.git` and no class-B inputs, and it is deliberately scoped to what it
can honestly assert — that V23 adds no *new* release-time failure. It does not claim
the release build works, and the note it prints says so. Whether the plates that
read class-B inputs should be declared unbuildable downstream, or those inputs
should get written permission, is a `release/` decision. Reported, not taken.

**Housekeeping seen, not acted on:** `theoria-arm/runs/pytest-*/` — two untracked
pytest residue directories inside a provenance root. Excluded twice over (no rule
members, and the `tracked=True` filter), so they cannot reach the manifest, but
they are test output sitting where runs live. `theoria-arm/` is not my territory.

---

## F-4 — three of six plates reach no reader; the ruling is promote, and the blocker is territory, not doubt

The item's claim — *fig02/03/04 appear 0 times under `papers/`* — is **true, and
not an artefact of grepping the pipeline slug.** Checked under every plausible
form: pipeline slug, paper slug (`figure6_bill_shape`), artefact path, caption
path, "Figure 6" / "Fig. 6" / "图6", `\ref{}`/`\label{}`, markdown image syntax.
Zero hits in the body for Figures 4, 5 and 6 under any spelling. The naming
indirection I was worried about does not fire: `paper_map.py:111-118` assigns paper
numbers by order of first citation *precisely* so Figures 1/2/3 land where the
prose already pointed. The paper embeds no image at all. One incidental substring
exists — the range-phrase "the full fig02–fig07 dark set is present" in a P12
review note under `papers/**/runs/` — which is a run note about a different
figure's broken path, not a citation.

Figures 1/2/3 (`fig06`, `fig07`, `fig05`) are cited *and argued*:
`sections/03_a0.md:27-35`, `:104-110`, `sections/05_a2.md:134-139`.

**Ruling, recorded as D-F-007 in `figures/STATUS.md`: promote Figures 5 and 6;
hold Figure 4 pending §6's own fate.** Figure 5 is the matrix §7.1 states as a
bare list of totals; Figure 6 is the construction §7.8's E2/E3 arguments are
defined by, and E2/E3 are two of Phase 4's three pre-registered primary endpoints.
Both live in §7, which is in scope (`OUTLINE.md`'s mandate includes the battery's
recompute of existing trajectories) and which P12's reviewers rate highest.
Retiring those two removes evidence rather than removing a burden, and V20's *"a
figure nobody cites is a burden that will drift"* is right about the cost and
answered by the gates rather than by deletion.

Figure 4 is different and my first draft got it backwards. It said *"promote all
three"*, justified by "§6 and §7 are precisely the two sections P12's two reviewers
independently named as weakest on evidence." **That sentence is a reversal, not an
overstatement**, and an adversarial review took it apart against the P12 record:
there were **five** independent seats, not two (the run's own note warns *"Do not
treat two reviews as five"*); no seat calls any section "weakest"; the domain seat
calls §7's anti-gaming register *"The widest daylight in the paper"*; the one
documented independent convergence — domain and lay seats, blind to each other —
is that §7.7 is the paper's **best** material and is buried; and both seats that
discuss §6 want **less** of it, the lay seat cutting it outright (*"A ratio of
0.029 against a strawman denominator is not a workshop result"*) and the domain
seat's MAJOR M4 offering to demote it to an appendix.

So the only argument I had offered for promoting Figure 4 was an argument against
it. The plate is fine; its home section is under active recommendation to go. A
figure promoted into a section two reviewers want cut is not a disposition, it is a
bet, so Figure 4's ruling is that its fate follows §6's — full section, promote per
P10's text; demoted to an appendix, go with it; cut, retire the plate and remove it
from `build_all.FIGURES`. I had read a review *summary* rather than the reviews,
which is the same shortcut as trusting a delegated drift count, in the same run.

**One live defect neither the ticket nor my first draft mentioned, and it blocks
all of this.** The paper **embeds no figure at all** — P12's lay seat: *"three
figures that are cited but not present … There is no figure in the document — no
image, no embed, no ASCII rendering, nothing."* Figures 1–3 are cited today and
render nowhere. Promoting three more citations into that document produces three
more of the same. Whoever executes D-F-007 should close the embedding gap first.

**Why it is still not executed.** The body is `papers/` territory. P10 already
wrote the three insertion paragraphs with exact anchors, style-matched to the
three existing citations (`runs/20260728T134521Z-P10-figures-into-paper/HANDOVER-papers.md:64-120`);
all three anchors are still present and unfollowed. P10, P13, V20 and V23 each
held `figures` and none held `papers` — that, and not indecision, is why this has
survived four runs. A12 refused an in-reach plate change on the same grounds and
was right to (*"that is a plate change to put in front of RES-2 rather than land
beside a gate"*). Handed over again with the ruling attached, in
`monitor/inbox/20260729T182000Z-W-1681-figures-4-5-6-promote-ruling.md`.

**The executable form already exists, unmerged, with wrong reasons.** V20 wrote
`figures/check_figure_citations.py`: every name in `build_all.FIGURES` must be
cited in the paper's prose or declared in `NOT_CITED_ON_PURPOSE` with a reason,
and a declaration stale in either direction fails. That is the right gate and I
deliberately did not write a second implementation of it — two implementations of
one check is the harm, and its branch is already held on a conflict *inside
`figures/verify.sh`*, which is a file I also had to touch. Two things for whoever
lands it: my gate 13 is appended at the end of `verify.sh` specifically to
minimise textual overlap with V20's insertion after gate 9, and V20's three
`NOT_CITED_ON_PURPOSE` reasons are **factually wrong** — they say A3 transfer has
no section in the outline and that the capability spectrum is Phase-4 material the
workshop paper stops short of, when `sections/06_a3_transfer.md` §6.2 and
`sections/07_battery.md` §7.1 are their home sections and were already written.
Replace them with D-F-007's rows.

**One thing I did not do.** Nothing in `figures/` enforces the ruling today, and
nothing will until V20's branch lands. That is a real gap and it is named here
rather than papered over with a second gate.

**Also stale, `papers/` territory, reported not fixed:**
`papers/phase1-workshop/OPEN_ITEMS.md:116` and `REVIEW_TRIAGE.md:95-96` both record
the reviewer finding "no figure is cited" as *struck, resolved* — "Three now do".
The paper's own open-items ledger therefore says the figure question is closed at
three of six, which is the reason nothing chased the other three.
`papers/phase1-workshop/README.md:30-36` still tells a reader to rebuild the
figures by running the three retired ASCII extractors, with no mention of
`build_all.py`. `release/reproduce.py:75-81` rebuilds the figures and never runs
their stop gate — `verify.sh` appears only in its `note=` prose.
