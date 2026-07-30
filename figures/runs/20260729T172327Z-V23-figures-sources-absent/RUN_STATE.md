# V23 — RUN_STATE

`prompt_id` V23-figures-sources-absent · worker W-1681 · cell V5 · territory `figures`
branch `agent/v23-figures-sources-absent` · base `580c645d` · 0 API calls · $0.00 · zero sealed-pile contact

The measurements and rulings are in `FINDINGS.md` (F-1…F-4) and `figures/STATUS.md`
(D-F-006, D-F-007). This file is the narrative: what I went in for, what was
actually there, and what I am handing on.

## What the ticket asked, and what was true

The ticket said `figures/SOURCES.sha256:24-27` records four dev-pile ledgers as
`ABSENT0000`, so gate 4 is red right now, and nothing reports it. Three of those
four statements had already stopped being true at my own base commit, and the
fourth is the one worth the run.

I ran the gate before touching anything, which is the only reason I know that:
`verify.BEFORE.txt`, thirteen gates, exit 0, at `580c645d`. `a5f597dd` had already
regenerated the manifest and rebuilt fig02 with it. So task 1 was discharged, by
the sanctioned method, before I arrived — and task 3's "13 of 50 lines have
drifted" does not hold under any reading I could construct. I measured it myself
in the end, with `history_probe.py`, after publishing a first draft that carried
six numbers from a delegated audit which an adversarial review then reproduced
none of — it was right to refuse them. Committed drift is **0 at every one of the
six revisions**; the worst the file ever got *between* regenerations is **7**; and
the "50" is not invented at all, it is `9239eb1c`'s entry count, two regenerations
stale. V20 had already reached the same conclusion and been held on a merge
conflict, so the number was signed out a second time and I nearly became the third
worker to re-measure it. **The measurement, and the script that made it, are in
this run directory now** — which is the only reason the fourth worker will not.

The sharper version of that finding: the number was never audited. It originates
as a hand-written dashboard cell in `monitor/spec.py:1217` (`fc6f1706`), a commit
that touched no `figures/` file and left no run directory, and was then dressed as
「审计逐行确认」 on the way onto the board.

One thing about the ticket's premise did get *sharper* rather than dissolving. The
four `ABSENT` lines were not a true statement that went stale: the files were
created on disk at 2026-07-27T18:23Z and P4 committed a manifest calling them
absent at 2026-07-28T09:06Z, fifteen hours later. They were false when written,
gate 4 was red on the main checkout for the 31 hours until `a5f597dd`, and the
reason a build wrote `ABSENT` about files that were on disk is that it ran in a
linked worktree where they were not — the shards being untracked, they existed in
the main checkout and in no worktree. That single mechanism produced the bad
manifest, kept gate 4 green in CI while it was red on disk, and produced V20's
false negative. F-1 and F-2 carry the arithmetic — including the correction that
the green-in-CI-while-red-on-disk overlap is about ten hours, not the full
thirty-one: for part of the window a clean tree was red too, on five unrelated
sources RES-3 had already reported.

What was real, and live, was underneath: **fifteen lines of that manifest were
asserting something false, and gate 4 is structurally incapable of noticing.** A
manifest line makes three claims — digest, path, status. The first two are
measured. The third is written from `Source.tracked`, a boolean somebody declared.
All fifteen envelope ledger shards became committed -- eleven by `baseline-arms`
on 2026-07-28, four by A14 the next day -- while `envelope_ledger` still said
`tracked=False`, so the manifest said `[untracked]` about fifteen tracked
files, `paper/index.json` published `"tracked": false` for the same fifteen into
the release index, and gate 4 — which diffs a committed manifest against a freshly
generated one — was green throughout, because both sides of it were reading the
same wrong sentence.

That is this directory's oldest lesson arriving through a door it had not been
watched at. `PLAN.md` §§264-274 and 637-657 already record two versions of it: a
probe that asked the registry it audited, then a probe that took its root and
pattern from the rule it audited. *An oracle can be captured through an argument
as easily as through a function call* — and, it turns out, through a column of the
artefact.

## What I changed

* `sources.py` — `envelope_ledger` from `tracked=False` to `tracked=True`,
  dropping a now-redundant `expected` tuple and keeping `optional=True, floor=0`.
  The reversal is recorded in place as a `V23 CORRECTION` comment with all three
  consequences of the stale declaration, because the next reader's question will
  be "why was it ever `tracked=False`".
* `sources.py` — `tracked_but_missing()` and `untracked_but_present()`: the
  floor's guarantee, derived from git rather than counted. My first pass set
  `floor=15, optional=False` here and an adversarial review killed it — these
  shards are class B in `release/LICENCE_POSTURE.md`, excluded from the release
  tree by default, so a numeric floor turns gate 0 red in the one tree that
  matters most, and 15 was also a hand-copied count of exactly the kind `PLAN.md`
  house rule 5 forbids. Deriving it answers both objections at once.
* `sources.py` — `_tracked_paths` reduced to one cached, retried, repo-wide
  `git ls-files`. It had no retry while `git_log` two hundred lines below did,
  its `None` was only ever recorded for a rule's own root so fifteen of seventeen
  roots could fail silently, and the per-root fan-out was forty git spawns per
  build on the host whose git spawns are the thing that fails.
* `sources.py` — `untracked_inclusions()` widened from `tracked=False` rules to
  every declared source. It had been checking the one class that could not occur
  and skipping the class that could: rules are filtered against git by `_scan`,
  and the thirty-odd hand-written `Source` entries never were.
* `sources.py` — new `tracking_mismatches()`, printed by `build_all.py`.
* `figures/check_tracking.py` — new probe, wired as **gate 13**. Reads the
  committed artefact, re-derives all three claims from `git ls-tree -r HEAD`,
  `os.path.isfile` and its own sha256, and **never imports `sources.py`**. Its
  negative control plants one defect per refusal branch it can reach — nine of
  them — and requires a refusal for each. It also carries a floor on line count,
  because the version without one reported green over a manifest truncated to a
  single line.
* `verify.sh` — gate 13; a banner naming tree, branch and commit before gate 0;
  and a loop that surfaces `WARN` lines from the two build passes.
* `fig02_bill_shape.py` — the "untracked by design" comment, and one caveat
  sentence that printed the word "optional" about these shards on the plate's own
  face.
* `SOURCES.md`, `README.md` — the paragraphs that still described the old world.
  Struck through rather than deleted, per this directory's convention: what
  happened to them is the more useful record.
* `figures/STATUS.md` — new, and a first for this territory.

## Two things I found by running the gate rather than by reading it

**The invisibility has a mechanism, and it is not "nobody ran the gate".** The
gate ran, automatically, every reflex tick. It just never ran against the merge
that broke it: `ci_merge.py:460-463` reduces a branch's diff to first path
segments and runs territory `d`'s gate only if `d` is in that set, and A14 touched
only `baseline-arms/`. Worse, the gate's own tree could not hold the defect —
`ci_merge.py:513-515` builds a throwaway `git worktree` from `origin/master`,
where the then-untracked shards do not exist, so the fresh build reproduced the
committed `ABSENT` and **gate 4 was green in CI and red on disk at the same time**.
That is also what produced V20's confident false negative. Full account in F-2,
with the smallest fix named and filed to `monitor/inbox/` — it is one probe in
`monitor/scan.py`'s registry calling the already-written, already-tested
`gates.run()` per territory on the real checkout. Not my territory.

**A latent determinism defect, found because a gate went red for a reason that
was not mine.** Gates 3 and 6 failed on my first post-change verify, on `fig06`,
whose commit-timestamp axis comes from `sources.git_log()`. That function caught
`OSError` and `CalledProcessError` alike and returned `[]`, which the figure draws
as "no git in checkout". Under the live merge daemon's git load, spawning `git`
fails transiently on this host — so one build pass got seven commits and the other
got none, and gate 3 caught it. **The lucky case.** The unlucky case is both
passes degrading together: gate 3 green, gate 6 green, and a committed figure
quietly missing its axis. `git_log` now retries, and then asks whether `REPO_ROOT`
is a git work tree at all: no repository is a legitimate degrade recorded in
`GIT_DEGRADED`, and anything else raises. (The first version of that asked
`shutil.which("git")`, which is the wrong question — a release tarball has a git
binary and no repository, so it would have raised in exactly the case the
docstring promises to survive. Caught in review, before it shipped.) And
`verify.sh` no longer throws the
build transcript away on success, because that is where every `WARN` this pipeline
prints was going.

I did not go looking for either of these. They are what a gate is for.

## Where it stands

`verify.AFTER.txt` — thirteen gates plus the new one, on the tree named in its
first three lines. Gate 13's line reads `61 manifest line(s): 61 tracked, 0
untracked, 0 absent; 61 digest(s) recomputed, every status re-derived from git`.

Shown failing on the tree it was written for, which is the standard this directory
holds probes to: `check_tracking.BEFORE.txt` — fifteen problems at `580c645d`, the
commit where `verify.sh` is green on all thirteen gates.
`check_tracking.AFTER.txt` — all nine planted defects refused, on a tree where the
audit itself is clean. `check_tracking.selftest.txt` is the same control taken
before the correction, when the audit still had its fifteen findings.

## Gaps, honestly

* **Nothing in `figures/` enforces D-F-007's promote ruling.** The executable form
  exists — V20's `check_figure_citations.py` — and is held on a merge conflict
  inside `verify.sh`, a file I also had to touch. I deliberately did not write a
  second implementation of it; two implementations of one check is the harm. So
  the ruling is a document until that branch lands, and I have said so rather
  than shipping a duplicate gate to make this section shorter.
* **The three plates are still uncited.** The body is `papers/` territory. The
  ruling, the sections, the anchors and P10's ready-to-paste text are all named in
  the inbox handover. Four runs have now found this and none of them could execute
  it; that is a routing problem, not a figures problem, and it is stated as one.
* **`out/shards/` is walked by no coverage probe.** `check_coverage.py` states
  `theoria-arm/runs` and `baseline-arms/out` as literals — correctly, that is its
  method — so a future cost-bearing shard family landing under a name outside
  `ledger.*.jsonl` reaches no gate. Not fixed here: extending that probe means
  extending its negative control to narrow the rule, and doing that in the same
  change as the rule edit is precisely how the last two versions of it went wrong.
  Recorded in `STATUS.md`.
* **`probe_log.*.jsonl` stays undeclared**, with the reason measured rather than
  assumed (F-3): no figure reads them, and widening the glob to `*.jsonl` does not
  declare them, it breaks the build — `fig02._classify()` raises on the first
  probe_log row. Worth writing down because the obvious fix is a regression.
* **`theoria_run`'s `floor_note` says "9 directories … on 2026-07-28"; there are
  22 now.** Left alone: the sentence is date-stamped and was true on its date, the
  floor of 4 is still correct, and gate 8 names the other eighteen on every run.
  Rewriting a true dated statement to make it describe today costs the record and
  buys nothing.
* `release/reproduce.py:75-81` rebuilds the figures and never runs their stop
  gate. `papers/phase1-workshop/README.md:30-36` still points a reader at three
  retired ASCII extractors. Both reported, neither mine.
