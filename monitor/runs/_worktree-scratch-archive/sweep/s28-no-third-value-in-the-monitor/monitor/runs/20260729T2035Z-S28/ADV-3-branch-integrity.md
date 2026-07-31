# ADV-3 · 分支整体可交付性（对抗性复核）

Reviewer scope: **whole-branch deliverability**, not individual defects.
Attacks A (cross-caller breakage), B (generated / append-only / territory),
C (does the gate measure anything), D (determinism / line endings),
E (merge safety).

Branch `agent/s28-no-third-value-in-the-monitor`. Base `5a997ef8`
(= `origin/master` at branch time). Zero API spend, zero sealed-pile contact.

## The target moved during this review — read this first

The brief named commits `1585dd04` and `fad88ca3`. While this review was
running the branch advanced to **`d8714f1d`** ("the review found a regression
this item introduced, plus the same regex three lines down"), which landed two
sibling reports (`ADV-1-board-scan.md`, `ADV-2-fleet-loop.md`) and 11 tests.
At the time of writing there are **further uncommitted edits in flight** in the
worktree (`monitor/reflex.py` extracting `merge_events()`, plus four test
files), and a `stash@{0}` holding the item's own WIP.

Every measurement below is stamped with the commit it was taken at. The
headline consequence for the orchestrator is in **E**: what gets merged is not
what any of the three reviewers read.

### Two confounds, recorded so nobody re-investigates them

1. **`verify.py` appeared to mutate live board state.** First run deleted
   `monitor/board/items/S28-no-third-value-in-the-monitor.md`, created
   `monitor/board/claimed/S28-….RES-4.md` and appended to `board/board.log`.
   **Not reproducible** — a second identical run left the tree clean, and
   `monitor/runs/20260729T2035Z-S28/ADV-1-board-scan.md` appeared in the same
   interval. A concurrent sibling agent claimed the item; `verify.py` has no
   claim path (`_board_states_disjoint` reads, `_real_run` runs
   `board.py list`). **REFUTED.** I restored the three board paths to `HEAD`
   with `git checkout --` plus one `rm` of the untracked claim file; the tree
   is at `HEAD` for those paths now. Disclosed because it was a write.
2. **`monitor/quota.py` was found mutated in the live worktree**
   (`- if due and now >= due:` / `+ if False:` — verbatim `mutants.py`'s
   `check-never-lifts-the-hold-on-its-deadline`; the coordinator separately
   observed a different hunk on `st["last_ping_at"]`). Reverted on request;
   `git status --short` then clean and `stash@{0}` intact. **Origin
   unresolved.** It was not this reviewer's: every mutation run here used
   `shutil.copytree` into a `tempfile.TemporaryDirectory()` (later an explicit
   scratch dir outside the repo), and no mutant list in this review contained a
   `quota.py` entry. Recording the coordinator's result regardless, since it is
   a datum for **C**: that mutation took `test_quota_autoexit.py` from 10
   passed to 3 failed, so `quota.check`'s deadline exit is **not** decorative.
   It also contaminated one mutation batch here — see C.

---

## CONFIRMED DEFECTS

### D1 · Four of the branch's fixes have zero test coverage — reverting them leaves the suite green and `verify.py` GREEN

This is the branch-level version of the item's own thesis. The suite grew by
66+11 tests and `verify.py` is GREEN, but four fixes are pinned by nothing: put
the pre-fix behaviour back and **nothing goes red**.

Method: copy `monitor/` to a scratch dir outside the repo, measure a baseline
in the same run (the copy is not a git repo, so a handful of tests fail there
for reasons unrelated to any mutation — subtracting a same-run baseline is what
makes `SURVIVED` falsifiable, per `mutants.py`'s own `baseline()` docstring),
then apply one mutation per throwaway copy.

```
$ SC=C:/Users/user/AppData/Local/Temp/res4mutbase
$ cp -r .worktrees/s28-no-third-value-in-the-monitor/monitor "$SC"
$ python <driver> "$SC"
CLEAN BASELINE failures=12 [...environment-dependent, listed in the transcript...]
reflex-sweep-rc-ignored-again              **SURVIVED** []
reflex-reap-rc-ignored-again               **SURVIVED** []
reflex-git-remote-rc-ignored-again         **SURVIVED** []
state-board-available-scrapes-again        **SURVIVED** []
meta-regex-eats-next-line-again            KILLED      ['test_an_empty_metadata_field_does_not_borrow_the_next_line', ...]
```

The four mutations, each a verbatim revert of an S28 fix:

| # | file | fix reverted | mutation |
|---|---|---|---|
| a | `reflex.py` | `board.py sweep` return code | `if sw.returncode != 0:` → `if False:` |
| b | `reflex.py` | `dispatch.py --reap` return code | `if reap.returncode != 0:` → `if False:` |
| c | `reflex.py` | `git branch -r` return code | `if _remote.returncode != 0:` → `if False:` |
| d | `scan.py` | `state["board"]["available"]` twin | `_available = len(_bmod.candidates())` → `_available = 4` |

**Why (a)-(c) survive.** The logic is inline in `reflex.main()`, and no test
drives `main()` — deliberately, because that tick launches paid sessions
(`test_standing_reflex_no_third_value.py`: *"Driving `reflex.main()` end to end
would be the real behavioural test, and it is refused on purpose"*). What does
exist is a **source scan** for the marker strings:

```
monitor/tests/test_standing_reflex_no_third_value.py:189
    for marker in ("sweep:EXIT-", "reap:EXIT-", "revive:GIT-EXIT-", ...)
```

`if False:` leaves `events.append("sweep:EXIT-%d" % sw.returncode)` in the
source, so the scan still passes. A source scan cannot distinguish "this line
runs" from "this line exists", which is this item's disease with a new spelling.

**(c) is the one the branch itself calls the worst.** `RUN_STATE.md`: *"`remote`
为空使每个死会话都读作「没交付过」，复活循环会重启已经干完活的会话。**失败方向
花真钱**。"* That is the highest-cost silent failure the item found, and it is
the one with no test.

**(d) reinforces ADV-1/D6 with a second, stronger fact.** ADV-1 established that
`state["board"]["available"]` has no consumer, so the twin fix's stated
motivation ("前端据此显示「不知道」") is false. Adding to that: it also has no
test. `verify.py`'s `_fields` checks `board.listing`, never `board.available`
(`monitor/verify.py:207`), so a hardcoded `4` passes all four gate stages.

**`verify.py` cannot catch any of the four.** Its stages are `_tests`,
`_board_states_disjoint`, `_real_run` (`scan.build` + `gates.survey` +
`board.py list`), `_fields`. `grep -c reflex monitor/verify.py monitor/verify.sh`
→ `0` and `0`: the gate never executes `reflex.py` at all. So the `tests` stage
is the only possible catcher, and it does not.

Not a style opinion and not a request to test `main()`: the fix already applied
to the fourth sibling is the answer. The item's own in-flight work extracts
`merge_events(r)` out of `main()` *precisely so a test can reach it* — and its
docstring says why in words that apply verbatim to (a)-(c):

> **This lives in a function only so that a test can reach it.** … the logic was
> inline in `main()`'s loop and unreachable from a test, so the two tests that
> claimed to cover it exercised a re-implementation of these eight lines
> *inside the test file* and passed against the pre-fix `reflex.py` verbatim.

Three siblings of that extraction were left inline. Same treatment closes D1.

### D2 · `monitor/tests/mutants.py` was not extended, so the branch could not have found D1 itself

```
$ git diff 5a997ef8..HEAD --stat -- monitor/tests/mutants.py
(empty)
```

`mutants.py`'s docstring is a standing contract for exactly this situation:

> every defect this suite claims to catch is re-introduced here into a throwaway
> copy of `monitor/`, and the suite is run against it. **A mutant that survives
> means the test covering it is decorative.**

S28 claims 11 + 16 fixed defects and added **zero** mutants. Running the four
mutations above is a ~2-minute job that the harness in the repo already
automates; it would have surfaced D1 before review. Note the brief's premise
that the diff "touches `monitor/tests/mutants.py`" is wrong — see R1; the file
is untouched, and that is the defect.

Adjacent, **pre-existing, not S28's**: two of the eight existing anchors no
longer apply, so the harness silently skips them.

```
$ cd monitor && python -c "import sys,os; sys.path.insert(0,'tests'); import mutants; ..."
**DEAD ANCHOR** quota.py resume-empty-queue-never-clears-the-mode
**DEAD ANCHOR** quota.py resume-relaunches-into-a-closed-window
APPLIES  reflex.py ci-merge-blocked-by-the-quota-hold
APPLIES  scan.py   a-crashed-scan-writes-nothing-and-the-page-just-gets-older
(+4 more APPLIES)
```

Both are in `quota.py`, which this branch does not touch. Filed here only so it
is not re-derived.

### D3 · The deliverable is in flight, so no reviewer has read what would be merged

Not a code defect; a delivery defect, and the reason for the verdict.

```
$ git log --oneline -3
d8714f1d monitor: the review found a regression this item introduced, ...
fad88ca3 monitor: five probes that reported a state they had not measured
1585dd04 monitor: three ways the fleet loop reported a failure as good news

$ git status --short          # taken after d8714f1d was pushed
 M monitor/reflex.py
 M monitor/tests/test_board_no_third_value.py
 M monitor/tests/test_dispatch_no_third_value.py
 M monitor/tests/test_scan_no_third_value.py
 M monitor/tests/test_standing_reflex_no_third_value.py

$ git stash list
stash@{0}: WIP on agent/s28-no-third-value-in-the-monitor: d8714f1d ...
```

`d8714f1d` is already on `origin`
(`git ls-remote origin "*s28*"` → `d8714f1d refs/heads/agent/s28-…`), while the
`merge_events()` extraction that its own new test's uncommitted sibling asserts
on is **not committed**. During this review the worktree passed through a state
where `monitor/quota.py` was mutated and three `test_quota_autoexit.py` tests
were red (see confound 2), and the branch tip changed under three separate
measurements. The branch is a moving target mid-repair; it should be quiesced,
the in-flight work committed, and the gate re-run on the final tip before any
merge.

---

## REFUTED HYPOTHESES

**R1 · "`monitor/state.json` (+542) and `monitor/tests/mutants.py` (+93) are in
this commit; check for proxy/ and other tracks' paths."** REFUTED — those come
from a mis-scoped baseline. Local `master` is 15+ commits behind
`origin/master`, so `git diff master...HEAD` shows unrelated upstream work
(`figures/`, `proxy/`, `verify-lab/`, 303k insertions). The branch base is
`5a997ef8`:

```
$ git diff --stat 5a997ef8..HEAD
 monitor/_runner.py | 86 +-   monitor/board.py    | 122 +-   monitor/dispatch.py | 117 +-
 monitor/reflex.py  | 118 +-  monitor/scan.py     | 113 +-   monitor/standing.py |  40 +-
 monitor/runs/20260729T2035Z-S28/{EVIDENCE-1..4,MANIFEST.json,RUN_STATE.md}
 monitor/tests/test_{board,dispatch,scan,standing_reflex}_no_third_value.py
 16 files changed, 2623 insertions(+), 71 deletions(-)
```

Every path is under `monitor/` — the item's territory. **No `state.json`, no
`mutants.py`, no `proxy/`, no other track's paths, no `PARTNER_SYNC.md`, no
append-only file.** (`d8714f1d` adds `monitor/board.py`, `monitor/standing.py`,
two ADV reports, two test files, `RUN_STATE.md` — also all `monitor/`.) No
generated artifact is hand-edited: `verify.py`'s `_real_run` writes `state.json`
into a throwaway `out_dir`, and two consecutive `verify.py` runs left the tree
clean.

**R2 · "`via_task`'s return-type change breaks callers; someone truthy-tests an
object that is always truthy."** REFUTED — the specific hazard is real and is
handled, and there are exactly two callers, both in `monitor/`. See the caller
audit. Repo-wide search for callers outside `monitor/` (including `proxy/`,
`release/`, `figures/`, `*.sh`, `*.md` runbooks, `.claude/`) found **none**;
the only outside hits are prose in `verify-lab/SUPPLEMENT_TABLE.md`,
`papers/`, `fleet-study/` and `monitor/FLEET.md`. `schtasks /Query` exposes no
task command line naming these entry points.

**R3 · "`heartbeat_age`'s split into `heartbeat_evidence` broke its callers."**
REFUTED — `heartbeat_age` is kept as a thin wrapper returning `[0]`, so its four
callers (`board.py:107`, `scan.py:1311`, `standing.py:350`, plus tests) are
unaffected. Mutation `heartbeat-prefers-tracked-json-again` is KILLED by two
tests.

**R4 · "`state["board"]["available"] = None` crashes a consumer."** REFUTED as a
crash. `available` has no reader anywhere: the only match for `available` in
`monitor/index.html` is the substring of a run id (`…v21-lp-unavailable…`),
`monitor/app.html` has none, and `verify.py` checks `board.listing` only. The
`None` is inert. It remains a real *coverage* gap — D1(d).

**R5 · "The gate is decorative — GREEN because it skips what matters."**
REFUTED as a blanket claim.

```
$ python monitor/verify.py ; echo EXIT=$?
== tests              ok      (360 passed, 2 xfail)
== board states disjoint ok   (109 delivered, 6 claimed)
== real run           ok      (scan.build wrote history.jsonl, index.html, state.json;
                               24 gated, 1 tests-only, 0 UNGATED; board.py list: 132 lines)
== artifact fields    ok      (13 required fields; gate survey consistent)
GREEN
EXIT=0

$ bash monitor/verify.sh ; echo EXIT=$?
… identical … GREEN   EXIT=0
```

**19 of 23 mutations were killed**, several by tests that name the exact
property (`test_each_writer_gets_its_own_temp_file`,
`test_a_failed_ledger_write_stops_being_silent`,
`test_a_missing_ledger_is_distinguishable_from_an_empty_one`,
`test_exit_summary_counts_what_the_start_line_cannot_see`,
`test_a_disabled_task_is_detected_in_both_languages`,
`test_the_gate_count_admits_how_many_were_never_proven`,
`test_an_unacknowledged_urgent_is_owed`,
`test_crashed_board_query_is_not_reported_as_an_empty_board`,
`test_exotic_line_separators_do_not_borrow_either[\u2028]`). The gate measures
real things. Its blind spots are the four in D1, not the whole surface.

*Caveat on one batch:* an earlier batch ran while `quota.py` was mutated in the
live worktree (confound 2), so its baseline was polluted and three mutants were
mis-reported `KILLED` on `test_quota_autoexit.py` failures. Those three were
re-run against a clean same-run baseline and are the `SURVIVED` results in D1.
Recorded because a mutation report whose baseline drifts is decorative in the
way it accuses its subjects of being.

**R6 · "CRLF entered tracked files, or artifacts are byte-unstable."** REFUTED.

```
$ git ls-files --eol $(git diff --name-only 5a997ef8..HEAD)
i/lf    w/crlf  attr/    monitor/_runner.py
i/lf    w/crlf  attr/    monitor/board.py
i/lf    w/crlf  attr/    monitor/dispatch.py
i/lf    w/crlf  attr/    monitor/reflex.py
i/lf    w/crlf  attr/    monitor/scan.py
i/lf    w/crlf  attr/    monitor/standing.py
i/lf    w/lf    attr/    monitor/runs/…/EVIDENCE-{1,2,3,4}-*.md, RUN_STATE.md
i/lf    w/crlf  attr/    monitor/runs/…/MANIFEST.json
i/lf    w/lf    attr/    monitor/tests/test_*_no_third_value.py
```

**All 16 are `i/lf`** — the index is LF throughout; `w/crlf` is `core.autocrlf`
in the working tree, which is what the setting is for. Worth one note, not a
defect: `attr/` is empty for `monitor/*.py` — root `.gitattributes` pins only
`PARTNER_SYNC.md merge=union` and `monitor/board/** text eol=lf`, so LF here
rests on `core.autocrlf` rather than on an attribute, unlike
`engine-rig/.gitattributes`. All new writers in the diff pass
`newline="\n"` explicitly (`_note_failure`, `record_exit`).

**R7 · "The merge conflicts destructively with live monitor state."** REFUTED.

```
$ git merge-tree --write-tree --messages HEAD origin/master ; echo exit=$?
457cbbfe40ce49e6f3850f4482c3129deaf21045   exit=0   CONFLICT count: 0
$ git merge-tree --write-tree --messages HEAD master ; echo exit=$?
28141d4614f73fb1199b62155ed260807251fd23   exit=0   CONFLICT count: 0
$ comm -12 <(git diff --name-only 5a997ef8..origin/master|sort) \
           <(git diff --name-only 5a997ef8..HEAD|sort)
(empty — zero overlapping paths with origin/master)
```

Local `master` overlaps in `board.py`, `reflex.py`, `scan.py` and still merges
with 0 conflicts. Run in the worktree via `merge-tree` (no index or working-tree
write) plus one throwaway worktree at `.worktrees/_res4_advmerge`, since
removed (`git worktree remove --force`; `git worktree list` confirms). The main
checkout was not modified.

**R8 · "`d8714f1d` commits a test for code it did not commit."** REFUTED, and it
looked strong: the worktree's `test_standing_reflex_no_third_value.py` asserts
`"merge_events(r)" in loop`, while `git show HEAD:monitor/reflex.py | grep -c
merge_events` → `0`. But that assertion is **uncommitted** (the test file is
`M`), so the tip is self-consistent. Exported and run clean:

```
$ git archive d8714f1d monitor | tar -x -C $SC && cd $SC/monitor && python -m pytest tests -q
FAILED tests/test_a1_gate.py::test_the_real_repository_still_reads_green
FAILED tests/test_gate_enforcement.py::test_the_merge_log_line_names_gated_and_ungated_separately
FAILED tests/test_gate_enforcement.py::test_the_probe_would_still_catch_a_named_script_that_was_never_built
FAILED tests/test_gates.py::test_this_repository_is_where_the_survey_says_it_is
FAILED tests/test_scan_no_third_value.py::test_a_deleted_append_only_file_is_a_risk
```

All five are "must run from the real repository root" tests and fail identically
at the base commit; `verify.py` runs pytest with `cwd=HERE` inside the real
checkout, where they pass. No `merge_events` failure. The tip's suite is green
in its intended environment.

**R9 (not in the brief, checked anyway) · "a `.sh` gate does source assertions on
`reflex.py` that S28 invalidated."** UNCONFIRMED. `monitor/verify_quota_exit.sh`
does assert on `reflex.py` source (`'"ping", "--if-due"' in src`,
`'"ping"]' not in src`, `"quota:RESUMED(auto)"`, `"quota:probe-throttled"`);
S28 touched none of those strings and `ast.parse(src)` still succeeds
(`python -c py_compile` clean for all six changed modules). The script itself
did not finish within the time budget here, so this is reported as unverified
rather than green.

**R10 · territory / vendored-fork divergence.** Not a defect of this branch, but
a consequence worth one line: `fleetkit/fleetkit/board.py` is an independent
copy carrying the **pre-S28** forms of two of the defects this item fixed —
`heartbeat_age` on `os.path.getmtime(path)` of the tracked json (`:66`) and the
cross-line `re.search(r"^%s:\s*(\S+)" % key, …)` (`:99`). `fleetkit` is not
this item's territory and calls nothing in `monitor/`, so this is a
follow-up item, not a merge blocker.

---

## CALLER AUDIT

Search basis: repo-wide content search for each changed symbol and for
`monitor/<module>.py` invocations across `*.py *.html *.js *.sh *.ps1 *.bat
*.md *.json`, including `proxy/`, `release/`, `figures/`, `.claude/`,
`fleetkit/`, `verify-lab/`, plus `schtasks /Query` for scheduled command lines.

| changed symbol | callers found | still correct? |
|---|---|---|
| `dispatch.via_task` **bool → status string** | `standing.py:394` (`ok = via_task(...)`, then `if ok == "running":`) | **y** — explicit compare, not truthiness; pinned by `test_standing_compares_the_status_explicitly` (asserts `'if ok == "running":' in src` **and** `"\n        if ok:\n" not in src`). Mutation `standing-truthy-test-on-status-string` → KILLED |
| " | `dispatch.py:330` `--worker` CLI, return value discarded, `main` returns 0 | **y (unchanged contract)** — exit code was already independent of launch success pre-S28 (recorded in `verify-lab/SUPPLEMENT_TABLE.md`). Not a regression; still an open pre-existing defect |
| " (printed word, grepped) | `reflex.py:263-265` `"started" in r.stdout` | **y** — `via_task` prints `started` only for `status == "running"`; every other status prints `status.upper()`, none containing `started`. `test_a_session_that_dies_on_arrival_is_not_reported_as_started` asserts exactly this. Mutation → KILLED (5 tests) |
| " (log line `ok=%s`) | `standing.py:401` writes `standing.log`; consumer is `scan.py:1221` `" START " in l` | **y** — no consumer parses `ok=`; repo-wide search for `ok=True`/`ok=False` parsing found only prose and comments |
| " (added `LAUNCH_SETTLE_S = 8` sleep) | `standing.sweep`, `reflex` refill | **y** — additive latency only, both already `sleep(45)`/`sleep(20)` between launches |
| `board.heartbeat_age` → wrapper over `heartbeat_evidence` | `board.py:107`, `scan.py:1311`, `standing.py:350`, `test_board_no_third_value.py:194,200` | **y** — signature and `None` contract preserved; mutation KILLED |
| `board.heartbeat_evidence` (new, 2-tuple) | `board.py:376` only | **y** — unpacks `age, source` |
| `board.withheld_items` (new) | `board.py:404` (`cmd_list`) only | **y** — mutation `no-fifth-partition` KILLED by 3 tests |
| `board.meta` regex `\s*` → `[ \t]*` | all `meta()` callers (`candidates`, `withheld_items`, `cmd_list`, `standing`, `scan`) | **y** — narrower match only; mutation KILLED by 4 tests incl. `[\u2028]`/`[\u2029]` |
| `board.cmd_claim` `except OSError` → `except FileNotFoundError` | CLI `board.py claim`; `reflex`/worker prompts grep `BOARD-EMPTY` | **y** — mutation `board-swallows-every-OSError-again` KILLED by 2 tests |
| `scan._supply` (scrape → `board.candidates()`), can return `risk` | `scan.py:1403` `PROBES["supply"]` | **y** — `risk` is an existing status; mutation KILLED by 2 tests |
| `scan.build` → `state["board"]["available"]` may be `None` | **no reader anywhere** (`verify.py:207` reads `board.listing`; frontend reads neither) | **y (no crash) / n (untested)** — **D1(d)**; mutation to a hardcoded `4` SURVIVED |
| `scan.probe_append_only` new `risk`-on-absent branch | `PROBES["append_only"]` | **y** — `git_or_none`'s `missing` return still fires first, so `test_the_other_verdicts_built_on_git_also_stop_reading_empty_as_clean` (expects `"missing"`) still holds. Mutation KILLED |
| `scan.probe_scheduled_tasks` → `childio.run_console` | `PROBES` | **y** — mutation `schtasks-forced-back-to-utf8` KILLED by `test_a_disabled_task_is_detected_in_both_languages` |
| `scan.probe_verify_gates` prints `decorative` | `PROBES`; `verify.py:_fields` checks survey partitions | **y** — `decorative` is not a partition, so `counted != len(rows)` unaffected. Mutation KILLED |
| `scan._ACK_REQUIRED` (module-import-time `from bus import ACK_REQUIRED`) | `scan.py:1045` `_bus_probe` | **y** — no circular import (`bus.py` imports nothing from `scan`); mutation KILLED by `test_an_unacknowledged_urgent_is_owed`. Frozen at import time (ADV-1/D5) |
| `standing.work_for` — `claimable` gains `-1`; `any` now `claimable > 0` | `standing.sweep:367` only | **y** — third value gets a third branch; both mutations KILLED |
| `standing.CLAIMABLE_UNKNOWN` (new) | `standing.sweep` only | **y** |
| `reflex` sweep / reap / git-remote return-code guards | inline in `reflex.main()`; no test drives `main()` | **n — D1(a)(b)(c)**, all three mutations SURVIVED |
| `reflex` `BOARD-QUERY-FAILED` / `SUPPLY-UNKNOWN` events | inline in `reflex.main()` | **y** — both mutations KILLED (`test_supply_unknown_is_distinct_from_supply_low_zero`) |
| `_runner.load_exits` (new, 2-tuple) | `_runner.record_exit` only | **y** — mutation `load_exits-empty-on-corruption` KILLED |
| `_runner.record_exit` per-writer tmp + `_note_failure` | `_runner.main` (×2, incl. the new abort path) | **y** — writes land in `monitor/dispatch-logs/`, gitignored at root `.gitignore:14`, so the new `exits-write-failures.log` and `exits.json.corrupt-*` cannot dirty the tree. Both mutations KILLED |
| `_runner.main` `sys.exit(127)` on missing CLI | `__main__` calls `main()` and drops the return value | **y** — `sys.exit`, not `return`, is why the process exits 127; `import sys`/`time` present at module top |
| `dispatch.read_exits` / `exit_summary` (new) | `exit_summary` → `read_exits`; nothing else yet | **y** — both mutations KILLED (`test_a_missing_ledger_is_distinguishable_from_an_empty_one`, `test_exit_summary_counts_what_the_start_line_cannot_see`) |
| callers **outside `monitor/`** for any of the above | **none** | **y** — only prose references; `fleetkit/fleetkit/board.py` is an independent copy, not a caller (R10) |

---

## Verdict

**needs-fix-first.** No cross-caller breakage, no territory or append-only
violation, no CRLF, no merge conflict — A, B, D, E all come back clean, and the
gate is substantially real (19/23 mutants killed). Two things block:

1. **D1** — four fixes, including the one the item itself names as the
   money-spending failure direction, are provably untested. The remedy is the
   one the item already applied to their fourth sibling: lift the three
   `reflex.main()` guards into a reachable function, and give
   `state["board"]["available"]` one test.
2. **D3** — the branch is mid-repair with uncommitted source and test changes
   and a live stash. Quiesce it, commit, re-run `verify.py`, then merge.

**D2** is the process note that would have prevented D1 and should land with it:
extend `monitor/tests/mutants.py`, which is the repo's own answer to "does this
test measure anything".
