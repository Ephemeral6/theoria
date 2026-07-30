# S42 · fleetkit 的三处谎 — run state

Territory `fleetkit`, branch `agent/s42-fleetkit-three-lies`, base `7972a075`.
Numbers live in `FINDINGS.md`; this file is the reasoning, including the one
decision the item left open.

## Before anything was edited

Baseline recorded first, because "no new failures" is not a claim you can make
retroactively:

* `fleetkit`: 6 passed.
* `monitor/tests`: 5 failed / 392 passed (397 collected). The failures are pre-existing on
  `origin/master` — 2 in `test_scan_no_third_value.py`, 3 in
  `test_standing_reflex_no_third_value.py`. This branch touches neither file.
* `fleetkit/verify.py`: **green** — on the code described below.

## Defect 1 — `_PREFIX = ""` was never assigned

`board.py:31` shipped an empty prefix and nothing in the package ever wrote to
it; `from fleetkit import config as _config` appeared exactly once, on the
import line. So `if len(cols) >= 3 and _PREFIX and _PREFIX in cols[0]` was
constantly false, `live` was constantly empty, and every `W-*` claim was judged
an orphan and freed. That is not a latent bug on an unused path — `sweep` is
the routine housekeeping command, and its effect was to take work off workers
that were still running. `KNOWN_TRAPS.md` entry 1, verbatim, in the package
that ships the warning.

**Reproduced before fixing**, with S40's technique: `subprocess.run` replaced
by one returning a synthetic `schtasks` CSV with one worker `Running` and one
`Ready`, encoded in the console code page rather than UTF-8 (getting that
substitution wrong would have proved the fix against the wrong input). Pre-fix
`claimed/` ends empty — both freed. Post-fix only the `Ready` one is freed.

**The fix has two halves, and the second matters more.**

1. `task_prefix()` reads `fleet.json` at the point of use. `config_root()`
   walks up from `FLEET_ROOT`, then `FLEET_HOME`, then the cwd — searched
   rather than assumed, because the state tree and the repository root are
   deliberately allowed to be different directories.
2. **`cmd_sweep` refuses (exit 3) when it cannot read a prefix**, and also when
   the `schtasks` query itself exited non-zero. Wiring the prefix alone would
   have left the shape of the bug intact: a fleet with no config, or a failed
   query, still produces an empty `live` set, and an empty `live` set still
   frees everything. Not knowing whether a worker is alive is a third answer,
   and freeing its claim is the one thing that answer must not mean. A default
   here would be the same trap wearing a different value.

There is deliberately no module-level default to fall back to. `verify.py` now
asks the board what prefix it *would* sweep with and compares that to the file
— pre-fix those were `""` and `"GateProbe-"`, and the gate was comparing the
file to itself.

## Defect 2 — `LANE_OWNER`, and the decision the item asked for

The claim was:

    #: Filled from fleet.json at import; empty means "no lane has an owner",
    #: which is the correct behaviour for a fleet that has not declared any.
    LANE_OWNER = {}

False twice over, as the item says. Four occurrences in the package: one
assignment, three reads, no writer of any kind — not in the tests, not in
`verify.py`. `fleet.json` did not exist anywhere in the repository. And
`FleetConfig.lanes` is a `List[str]`: even a wired-up loader had no lane-to-owner
map to load.

### The decision: DELETE. And the justification.

**Deleted, with lane *filtering* kept.**

*Why not "make it true".* The cost is a config schema change —
`lanes: List[str]` becomes a mapping, dragging `THEORIA_EXAMPLE` and
`REQUIRED_CONFIG` with it — and the item made the bar for paying it concrete: a
real caller that needs lane ownership. I looked for one and there is none.
fleetkit's callers are its own suite and `verify.py`; nothing else in this
repository imports the package. Theoria's monitor has its own `board.py` with
its own `LANE_OWNER` and does not import this one. Growing a schema to serve a
hypothetical user is precisely how a claim comes to be written with no
mechanism behind it — repeating the cause while repairing the symptom.

*What is kept, and why it is not a consolation prize.* `FleetConfig.lanes`'
own docstring says "lanes a standing agent can be **restricted to**". That is a
statement about the worker, not about the item, and a `List[str]` expresses it
exactly. So `--lane X` narrows what a worker is willing to take and can never
widen it; every lane-tagged item is listed and claimable by anybody. The code
and the schema now say the same thing, which they did not before.

*Handling the unreachable loop body.* Deleting `LANE_OWNER` required removing
`stale_lanes()` (a 13-line function with a 6-line docstring narrating a real
outage, which given `{}` could only ever return `set()`) and the `reserved`
section of `cmd_list` (reachable code whose loop body never executed; given
`{}` it printed nothing, not an empty heading). Both are gone.

*The consequence I did not expect, and did not leave.* With lanes as
worker-side filters, the `spend: api` guard could not stay lane-conditional. It
read `if not lane and m.get("spend") == "api" and ...`, so a worker that typed
`--lane campaign` walked straight past the money guard — the worker's own word
about itself acting as authorisation (this is S40's finding (d), reached from
the other direction). It is now unconditional, which is what "a lane can only
narrow" has to mean if it means anything. Two tests hold it.

*The silent-unreachability rule, generalised.* The item requires that
lane-tagged items must not be silently dropped. Rather than fix that one class,
`cmd_list` now counts the other way: every file in `items/` that is not in
`available` must be named by some section with a reason, and an item nobody can
explain prints `原因不明——这是 board 的 bug，请报告` instead of vanishing. That
also closes the `spend: api` invisibility, which was never lane-specific.
Unclaimable is fine. Unclaimable *and unmentioned* is how a board with eleven
items on it reads as empty, which is the S28 incident.

`heartbeat_age` and `STALE_MIN` survive with no in-package caller. That is
stated in a comment above them rather than left to be rediscovered: the
unported launching half decides liveness with exactly those two and imports
them by name. They are honest functions; deleting them would be tidying, and
would break the unported half's landing.

## Defect 3 — the front door, and the gate above it

`python -m fleetkit init --prefix MyFleet-` is line 13 of `README.md` and line
8 of `__init__.py`. It died with `No module named fleetkit.__main__`. Created
`fleetkit/fleetkit/__main__.py` with `init`, `board` and `bus`; `board` and
`bus` delegate to the modules' own `main()`, so `python -m fleetkit board list`
and `python -m fleetkit.board list` cannot drift apart — a test asserts their
output is byte-identical.

`init` refuses to overwrite an existing `fleet.json` without `--force`
(`task_prefix` is the fleet's identity; changing it makes every worker already
running under the old one read as dead on the next sweep) and refuses an
explicitly empty `--territories`, which `config.write_default` would otherwise
have quietly replaced with its starter default.

**The deeper half.** `verify.py` called `config.write_default()` in-process, so
it was structurally incapable of noticing that the entry point did not exist —
green for every run during which the first documented command was broken. It
now drives `python -m fleetkit init` and `python -m fleetkit board ...` as
subprocesses. Measured on the *identical* pre-fix package: the old gate is
green, the new gate is red, and its failure line is the user's error verbatim.
That pair is the evidence; "I improved the gate" without it is an assertion.

`board list` is also now run by the gate, with the requirement that both toy
items be named in its output.

## Also fixed: a cp936 crash in the same territory

`bus.py:144` printed `U+26A0` whenever an agent had an unread URGENT.
`'U+26A0'.encode('cp936')` raises, so `bus status` died mid-output exactly when
it had something urgent to report — a print that raises is a command that did
not run. Replaced with ASCII. Every file this branch touches was then checked
character by character against cp936: zero offenders.

## S40's drift table

`monitor/tests/test_fleetkit_drift.py` is S40's and lives in monitor's
territory; this item is authorised to amend it and did:

* `stale_lanes`' DECLARED entry **deleted** (the function no longer exists in
  fleetkit, so it would have failed
  `test_declared_names_all_exist_in_both_files` as dead text).
* `cmd_sweep` moved `defect` to `stale`, with the remaining divergence spelled
  out in three parts: extraction (config-backed prefix, locale-based decode), a
  fix that goes *beyond* monitor (refusing on an unreadable prefix or a failed
  query — monitor still reads a failed query as an empty task table), and
  genuine staleness (`include_standing`, the S34 re-offer guard).
* `candidates` and `cmd_list` amended: both now diverge partly **on purpose**,
  and the entries say "do not close this one by copying monitor".
* `GLOBAL_ONLY` reduced to `territories_busy`, which is the last case of
  byte-identical source with divergent behaviour.
* Counts re-pinned: 18 shared to 17, behavioural total 10 to 9.
* `test_the_false_docstring_is_still_there_and_still_false`, which S40 built to
  go red at this exact moment, is rewritten as
  `test_lane_ownership_is_gone_from_fleetkit` — the same watchpost pointed at
  the new state, asserting that reintroducing `LANE_OWNER` requires a config
  that can express it.
* One test added,
  `test_fleetkits_sweep_reads_a_prefix_instead_of_shipping_an_empty_one`,
  asserting from monitor that no module-level prefix literal comes back. It
  compares *bindings* via `ast`, not text, so `board.py` is still free to
  explain in prose what `_PREFIX` was.

The amended file was then run against the pre-fix `board.py`: **3 failed, 10
passed**. A DECLARED table edited to agree with the code would have stayed
green there.

## Coordination note for whoever merges

S40 is not on master. `monitor/tests/test_fleetkit_drift.py` was taken from
`9ca9278a` and amended here, so the file appears as an addition on both
branches. **This branch's copy supersedes S40's**; whichever lands second
should take this one. S40's `monitor/runs/20260730T0625Z-S40/` artefacts were
deliberately not copied — they are monitor's territory and belong to that
branch.

## Left undone

* `meta()`'s `\s*` regex (S40 finding (c)) is untouched: `\s` crosses newlines,
  so an empty front-matter field takes its value from the next line. It is a
  real defect, it is why `territories_busy` still diverges with identical
  source, and it is outside this item's three. Its DECLARED entry stands.
* `cmd_release`'s missing reason gate, `cmd_claim`'s `except OSError`, and
  `candidates`' missing S34 re-offer guard: still `stale`/`defect` in DECLARED,
  still fleetkit's debt, not this item's scope.
* S18's acceptance gap is unchanged — the workers in every run here are
  processes, not language models, and `verify.py` still prints that on every
  run.
