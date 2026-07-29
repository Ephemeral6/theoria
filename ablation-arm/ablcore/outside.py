"""Did a run of this arm write anything outside `ablation-arm/`?

This module exists because the previous answer to that question was wrong in the
one direction that mattered, and the audit said so:
`monitor/audit/DRIFT-20260728T1501Z-the-tightened-criterion-hides-the-worst-writes.md`
(severity high).

## What was wrong

`tests/test_readonly.py` used to subtract concurrent-fleet noise with a tuple of
**path shapes**::

    CONCURRENT = ("/var/", "/runs/", "/out/", "/artifacts/",
                  ".jsonl", ".log", "state.json")

The comment above it claimed the criterion was "no change, or change traceable to
this arm".  Nothing in the code checked traceability; it checked what the path
looked like.  And the shared ledgers -- the files whose corruption is most
expensive -- look exactly like runtime products.  The audit walked real paths
through that tuple: `proxy/var/spend_gate.jsonl`, `arc-recon/data/*.jsonl`,
`engine-rig/artifacts/candidates.jsonl`, `baseline-arms/ledger.jsonl` and
`monitor/state.json` were all silently excluded.  What survived was mostly
Markdown and source -- precisely where a stray write is least likely.

Worse, the exclusion was *derived from* the only cross-territory write anyone had
ever actually observed (`proxy/var/spend_gate.jsonl`, a false positive from a
concurrent session).  To make one false positive go away, the shape of the only
observed true-positive-looking event was made permanently invisible.

## What replaces it: an empty-run control

The rule is not "this path looks like noise".  The rule is **"this path also
moves when the arm does nothing"**::

    snapshot A  ->  [idle window]  ->  snapshot B     background = A vs B
    snapshot B  ->  [ run_arm   ]  ->  snapshot C     observed   = B vs C
    reported = observed - background            (plus the hard list, below)

Concurrent sessions write during both legs, so their paths land in `background`.
This arm's writes only happen during the second leg.  The subtraction is by
*behaviour*, not by *appearance*.

Two properties are worth stating because they are the reason this beats a hand
written exclusion table:

* **No new concept.**  It reuses the snapshot/diff machinery that was already
  here; there is nothing to learn and nothing to keep in sync.
* **It does not go stale.**  A hand written table has to be edited every time
  another track invents a new runtime file, and until someone edits it the file
  reads as an escape (false positive) -- or, once someone edits it too broadly,
  stops reading as one forever (false negative).  The empty-run control covers
  files that do not exist yet, automatically, because it asks a question about
  *when* the file moved rather than about *what it is called*.

Because the control makes concurrent noise affordable, this module can afford to
be far less selective than `pin.py`: `pin.SKIP_DIRS` drops any directory named
`artifacts` or `runs`, which meant `engine-rig/artifacts/candidates.jsonl` was
never even hashed.  Half the audit's blind spot was that skip.  Here nothing is
skipped except VCS/build/cache scratch, and top-level files (`PARTNER_SYNC.md`,
`CLAUDE.md`, ...) are watched too.

## How long the idle window runs, and why that is not a free choice

The control is only aligned if the empty leg is exposed to concurrent writers for
**at least as long as** the real leg.  But the real leg's duration is not known
until after it has run, so a single constant either under-covers (silently
weakening the control) or over-covers (inflating `background`, which masks real
escapes -- the very failure being fixed).

So the window is a floor plus a make-up window:

1. idle for `IDLE_FLOOR_SECONDS` (2.0s -- comfortably above the ~0.4-1.1s a
   `run_all` leg costs on this machine, so the make-up window is normally empty);
2. run the action, measuring its exposure;
3. if the real leg outlasted the idle leg, idle again for exactly the shortfall
   and union that second background set in.

The control's exposure is then always >= the run's, and never much more.  The
honest caveat, recorded rather than hidden: the make-up window sits *after* the
run, so the control brackets the run rather than strictly preceding it.  Same
wall-clock neighbourhood, which is what alignment needs; `Observation` carries
both durations so a reader can check the ratio instead of trusting this
paragraph.

## Where this actually runs, and what that does to the control

**Read this before trusting the subtraction.**  `observe()` defaults to
`root=REPO`, and `REPO` is the directory above this arm -- which under
`monitor/ci_merge.py` is a throwaway `git worktree`, not the live tree.  A fresh
worktree has no `proxy/var/`, no running fleet and no concurrent writer, so the
background set there is **empty**, and an empty background subtracts nothing.

That is not a hypothesis.  The adversarial review of this module measured 75
consecutive idle windows inside this worktree and got 0 background paths in
75/75, and `background == []` in 6/6 full observations across both trees; the
run directory's own `01`/`02`/`07` artefacts agree.  So in CI this check is
currently a plain "nothing outside the arm moved", with the empty-run control
contributing nothing at all, and `subtracted` / `reported_by_hard_list` have
never had a non-empty input outside a hand-built `Observation` and the
concurrent-writer test that was added to force one.

Which is fine, and is the point worth being clear about: **the control is
insurance, not the mechanism.**  When the check runs somewhere quiet it costs
one 2-second sleep and changes nothing.  When it runs somewhere noisy -- the
live tree, or CI once the fleet writes into the worktree -- it is what stops the
next person from reaching for a path-shape exclusion table.  The failure it
prevents is not a failing test; it is the *fix* someone would apply to a failing
test.

## What the control does *not* remove, measured rather than argued

An empty-run control subtracts a writer only if that writer is active during
**both** legs.  That covers continuous churn -- which is what the original false
positive was: a running fleet appending to `proxy/var/spend_gate.jsonl`.  It does
**not** cover a *periodic* writer whose period is much longer than either leg;
such a writer is absent from both legs most of the time and present in exactly
one leg occasionally, and when that one leg is the real one the check goes red
for something this arm did not do.

This is not hypothetical here.  `runs/20260728T191437Z-A9-readonly-baseline/`
measured it on the live worktree.  The first measurement was too small to trust
and the adversarial review said so: four windows totalling 53s found the tree
still at 2s/5s/15s and moving four files at 30s (the monitor's reflex loop), and
put the residual at ~2% per run.  A 110-window resample over 263s
(`08-live-background-resample.json`) says **24 of 110 windows moved something,
p = 0.22, residual false red ~8.7% per run** -- four times the first estimate.
The dominant writer is `monitor/ci/merge.log` (12 of 24 windows), the CI merge
loop, which the first frame never sampled at all; `monitor/index.html`,
`monitor/ci/merge.lock`, `browser-ops/terms_canary.json`,
`monitor/dispatch-logs/*.log` and `monitor/board/board.log` follow.  `05`/`06`
are kept as the record of the undersized frame rather than overwritten.

Note the sting the review pointed out: `.log` was one of the seven tokens the
superseded criterion excluded.  `monitor/ci/merge.log` is a false-positive class
the broken criterion suppressed and this one re-opens, deliberately, with
nothing to quiet it.

It is left in place rather than patched:

* Excluding those four paths **by name or by shape** is the exact defect this
  module replaces.  The superseded criterion would have reported two of the four
  and hidden the other two -- including `monitor/state.json`, which is on the
  hard list precisely because it must never be hidden.
* Retrying on red and reporting only what repeats would remove it, and would
  also remove a genuine escape that only happens on a cold first run.  Trading a
  2% false red for a silent false negative is the trade that produced the audit
  finding in the first place.

So the residual is reported honestly instead: a red carries `background`,
`observed` and `subtracted` alongside it, which is what a reader needs to tell a
5-minute timer from an escape.  An escape reproduces; a timer does not.

And the deeper objection, which stands and is not answered by any tuning: a
single-sample control subtracts a writer with probability `p` and pays a false
red with probability `p(1-p)`.  No window length drives that to zero -- a short
window means `p -> 0` and nothing is subtracted, a long one means `p -> 1` and
false positives turn into false negatives.  The 2.0s floor sits at the
`p -> 0` end on purpose: at this repo's churn it subtracts almost nothing and
pays ~9% false reds, which is the side of that trade the audit's finding says to
be on.  A red is cheap -- look at `background` and re-run.  The other side of
the trade is what the audit found: silence.

## The hard list: never subtracted, ever

An empty-run control has one structural weakness.  If another session happens to
write a file during *both* legs, that file lands in `background` and is
subtracted -- and for most files that is the correct call.  For a handful it is
not, because the cost of missing a write there dwarfs the cost of a spurious red.
Those are listed in `HARD_LIST` and are reported even when they appear in the
background set.

The reasons are in the table itself, not paraphrased here, because a reason kept
next to the rule is a reason that gets updated with it.
"""

from __future__ import annotations

import os
import re
import time
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import _bootstrap  # noqa: F401
from _bootstrap import REPO  # noqa: E402

from ablcore.pin import sha256_file  # noqa: E402

#: This arm's own directory name.  Everything under it is *supposed* to move.
ARM = "ablation-arm"

#: Scratch that is nobody's territory.  Deliberately **much** shorter than
#: `pin.SKIP_DIRS`: `artifacts` and `runs` are not here, because another track's
#: `artifacts/` is one of the things it is worst to write and `pin` skipping it
#: was half of what the audit found.
#:
#: Everything here is a tool's own cache or a checkout of something else.
#: `.pytest-runs` earns its place the same way `.pytest_cache` does -- it is
#: pytest's per-run temporary directory (`theoria-arm/.pytest-runs/pytest-*/`),
#: not an arm's output.  The adversarial review found that without it the
#: `**/ledger.jsonl` hard-list rule reaches another arm's pytest temp files and
#: makes them un-suppressible.
SKIP_DIRS = frozenset({
    ".git", ".worktrees", "__pycache__", ".pytest_cache", ".pytest-runs",
    ".toolchain", ".lake", ".mypy_cache", ".ruff_cache", ".venv",
    ".claude", "node_modules",
})

#: Paths that are reported even when they also move during the empty run.
#:
#: Every entry is here because a write by another arm has a named consequence,
#: and each is worth an occasional false red:
#:
#: * `proxy/var/spend_gate.jsonl` -- the spend gate's ledger.  `CHARTER.md`'s
#:   hardest boundary is "only RES-1 may spend API money", and this file is how
#:   that boundary is enforced and audited.  A foreign write here is **spending
#:   out of control**, and it is also the exact path the old exclusion table was
#:   built around.
#: * `arc-recon/data/*.jsonl` -- the contamination log and the incident ledger.
#:   A foreign write here is **the pile-cut record being tampered with**, which
#:   is the record every Phase 3 result rests on.
#: * `CONTRACTS/**` -- frozen v0.1.  `CLAUDE.md`: "Neither track may modify it."
#:   A foreign write here is **a frozen contract being routed around**.
#: * `monitor/state.json` -- the monitor's own view of the fleet.  A foreign
#:   write here means the thing that is supposed to notice drift has been
#:   edited by the thing it is watching.
#: * `**/ledger.jsonl` -- each territory's ledger.  Same class as the spend
#:   gate: the accounting a claim is later checked against.
HARD_LIST: Tuple[Tuple[str, str], ...] = (
    ("proxy/var/spend_gate.jsonl", "spend gate ledger: foreign write = spending out of control"),
    ("arc-recon/data/*.jsonl", "contamination/incident ledgers: foreign write = the pile-cut record tampered with"),
    ("CONTRACTS/**", "frozen v0.1 contracts: foreign write = a frozen contract routed around"),
    ("monitor/state.json", "monitor state: foreign write = the watcher edited by the watched"),
    ("**/ledger.jsonl", "per-territory ledger: the accounting a claim is later checked against"),
)

#: Two entries the ticket did not name, kept separate so a reader can see exactly
#: what was mandated and what was added, and reject the additions without
#: touching the mandated five.  Both close a row of the audit's own table:
#:
#: * `baseline-arms/**/ledger.*.jsonl` -- the ledgers are sharded in practice
#:   (`baseline-arms/out/shards/ledger.a7-g50t.jsonl` and ten siblings exist on
#:   this tree).  A hard list that only matches the unsharded name would not
#:   have covered a single one of the ledgers that actually exist there.
#: * `engine-rig/**/candidates.jsonl` -- the frozen contract's append-only
#:   stream.  `CLAUDE.md` names it by that name ("`candidates.jsonl` is
#:   append-only") and `engine-rig/tools/validate_candidates.py` is its
#:   executable schema; the audit's table lists
#:   `engine-rig/artifacts/candidates.jsonl` as one of the paths the old
#:   criterion wrongly excluded, and `CONTRACTS/**` does not reach it because it
#:   does not live under `CONTRACTS/`.
#:
#: **Both were narrower once and were widened back by review.**  They started as
#: `**/ledger.*.jsonl` and `**/candidates.jsonl`, and the adversarial review
#: measured what that actually caught on the live tree: of the 18 files matching
#: `**/candidates.jsonl`, only 2 are the frozen stream -- ten are
#: `worldgen/out/qc/*/candidates.jsonl`, another territory's regenerated QC
#: scratch.  Since the hard list is never subtracted, a neighbour regenerating
#: QC scratch would have made this check *deterministically* red for something
#: this arm did not do.  That is the exact pressure that produced the tightening
#: the DRIFT note documents, so the prefixes are anchored to the territory whose
#: file the audit actually named.  The mandated five below are untouched.
HARD_LIST_EXTENSIONS: Tuple[Tuple[str, str], ...] = (
    ("baseline-arms/**/ledger.*.jsonl", "sharded ledgers: the form the ledgers actually take on this tree"),
    ("engine-rig/**/candidates.jsonl", "the frozen contract's append-only stream, which lives outside CONTRACTS/"),
)

ALL_HARD: Tuple[Tuple[str, str], ...] = HARD_LIST + HARD_LIST_EXTENSIONS

#: Floor for the empty-run window.  See the module docstring: a `run_all` leg
#: costs ~0.4-1.1s here, so 2.0s normally makes the make-up window a no-op while
#: keeping `background` from being inflated by idling far longer than the run.
IDLE_FLOOR_SECONDS = 2.0


def _to_regex(pattern: str) -> "re.Pattern[str]":
    """Glob -> regex, with `*` stopping at `/` and `**` crossing it.

    `fnmatch` is not used: on Windows it lowercases and it lets `*` cross
    separators, so `arc-recon/data/*.jsonl` would silently match paths in
    subdirectories.  A hard list whose semantics change with the host OS is not
    a hard list.
    """
    out: List[str] = []
    i = 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif pattern[i] == "*":
            out.append("[^/]*")
            i += 1
        elif pattern[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    return re.compile("".join(out) + r"\Z")


_HARD_RE: Tuple[Tuple["re.Pattern[str]", str, str], ...] = tuple(
    (_to_regex(p), p, why) for p, why in ALL_HARD)


def hard_reason(rel: str) -> Optional[str]:
    """The reason this path is never subtracted, or None if it is not on the list."""
    norm = rel.replace("\\", "/")
    for compiled, pattern, why in _HARD_RE:
        if compiled.match(norm):
            return "%s -- %s" % (pattern, why)
    return None


def is_hard(rel: str) -> bool:
    return hard_reason(rel) is not None


def watched(root: str = REPO) -> Tuple[str, ...]:
    """Every top-level entry that is not this arm and not scratch.

    Top-level **files** are included on purpose (`PARTNER_SYNC.md`, `CLAUDE.md`,
    `Theoria.md`): the previous check watched only directories, so a run that
    appended to the shared status board would have passed it.

    Entries are skipped **by name**, not by a leading dot.  The adversarial
    review caught the earlier `name.startswith(".")` rule dropping `.env` --
    which `CLAUDE.md` makes the single highest-consequence file in the repo --
    while nested dot-directories were walked anyway, so the rule was not even
    consistent with itself.  Only the sha256 of `.env` is ever taken, never its
    bytes, so watching it cannot leak the key it holds; that is the whole point
    of hashing rather than diffing.
    """
    out = []
    for name in sorted(os.listdir(root)):
        if name == ARM or name in SKIP_DIRS:
            continue
        out.append(name)
    return tuple(out)


def snapshot(root: str = REPO,
             entries: Optional[Sequence[str]] = None,
             unreadable: Optional[List[str]] = None) -> Dict[str, str]:
    """repo-relative path (forward slashes) -> sha256, for everything watched.

    A file that cannot be read is appended to `unreadable` rather than silently
    dropped.  It matters: on Windows the spend gate takes a byte-range lock on
    its own ledger (`proxy/spend_gate.py`), and a locked file leaving the
    snapshot on one side and returning on the other is a reported diff with no
    write behind it -- while a file locked across *both* snapshots disappears
    from both dicts and produces no diff at all, which no hard list can rescue
    because the path never enters the evidence.  Counting them is the honest
    minimum; `Observation.unreadable` carries the count to the reader.
    """
    out: Dict[str, str] = {}
    for name in (watched(root) if entries is None else entries):
        full = os.path.join(root, name)
        if os.path.isfile(full):
            try:
                out[name.replace(os.sep, "/")] = sha256_file(full)
            except OSError:
                if unreadable is not None:
                    unreadable.append(name.replace(os.sep, "/"))
            continue
        for dirpath, dirnames, filenames in os.walk(full):
            dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
            for fname in sorted(filenames):
                path = os.path.join(dirpath, fname)
                rel = os.path.relpath(path, root).replace(os.sep, "/")
                try:
                    out[rel] = sha256_file(path)
                except OSError:
                    # Vanished or locked mid-walk. Recorded, not swallowed.
                    if unreadable is not None:
                        unreadable.append(rel)
    return dict(sorted(out.items()))


def diff(before: Dict[str, str], after: Dict[str, str]) -> List[str]:
    return sorted(key for key in set(before) | set(after)
                  if before.get(key) != after.get(key))


class Observation:
    """One empty-run-controlled measurement, with its own audit trail.

    Every field a reader needs to reject the conclusion is here: both exposure
    durations, the raw background set, the raw observed set, and which reported
    paths survived because of the hard list rather than because of the control.
    """

    def __init__(self, background: List[str], observed: List[str],
                 idle_seconds: float, run_seconds: float,
                 makeup_seconds: float, files_watched: int,
                 action_seconds: float = 0.0, idle_sleep: float = 0.0,
                 makeup_sleep: float = 0.0, snapshot_seconds: float = 0.0,
                 unreadable: Optional[List[str]] = None):
        self.background = background
        self.observed = observed
        self.idle_seconds = idle_seconds
        self.run_seconds = run_seconds
        self.makeup_seconds = makeup_seconds
        self.files_watched = files_watched
        #: The action alone, with the snapshot around it taken out. `aligned`
        #: compares *this* against the sleeps, because both legs pay one
        #: snapshot and it cancels -- the earlier predicate compared
        #: `2*snapshot + sleep >= action + snapshot` and so reported aligned
        #: while the control was short by up to one snapshot's worth of
        #: exposure. Caught by the adversarial review.
        self.action_seconds = action_seconds
        self.idle_sleep = idle_sleep
        self.makeup_sleep = makeup_sleep
        self.snapshot_seconds = snapshot_seconds
        #: Files the snapshot could not read on either leg. Not evidence either
        #: way, but a number the reader is entitled to see.
        self.unreadable = sorted(set(unreadable or ()))
        noise = set(background)
        self.reported = sorted(p for p in observed
                               if p not in noise or is_hard(p))
        #: Reported *despite* being background noise -- i.e. the hard list did
        #: the work, not the control.  Empty in the ordinary case.
        self.reported_by_hard_list = sorted(p for p in self.reported
                                            if p in noise)
        #: Subtracted by the control.  Kept so a reviewer can eyeball whether
        #: anything here looks like it should have been on the hard list.
        self.subtracted = sorted(p for p in observed
                                 if p in noise and not is_hard(p))

    @property
    def aligned(self) -> bool:
        """Was the empty leg exposed at least as long as the real leg?

        Per file, the idle leg's exposure is `idle_sleep + snapshot` and the
        real leg's is `action + snapshot`; the snapshot cancels, so the test is
        sleeps vs action and nothing else.
        """
        return (self.idle_sleep + self.makeup_sleep) >= self.action_seconds

    def as_dict(self) -> Dict[str, object]:
        return {
            "files_watched": self.files_watched,
            "idle_seconds": round(self.idle_seconds, 3),
            "makeup_seconds": round(self.makeup_seconds, 3),
            "run_seconds": round(self.run_seconds, 3),
            "action_seconds": round(self.action_seconds, 3),
            "idle_sleep": round(self.idle_sleep, 3),
            "makeup_sleep": round(self.makeup_sleep, 3),
            "snapshot_seconds": round(self.snapshot_seconds, 3),
            "unreadable": self.unreadable,
            "aligned": self.aligned,
            "background": self.background,
            "observed": self.observed,
            "reported": self.reported,
            "reported_by_hard_list": self.reported_by_hard_list,
            "subtracted": self.subtracted,
            "hard_list": [{"pattern": p, "why": w} for p, w in ALL_HARD],
        }

    def message(self) -> str:
        lines = ["%d path(s) outside %s/ moved during the run and not during "
                 "the empty-run control:" % (len(self.reported), ARM)]
        for path in self.reported[:10]:
            why = hard_reason(path)
            lines.append("  %s%s" % (path, "   [hard list: %s]" % why if why else ""))
        lines.append("background=%d observed=%d subtracted=%d unreadable=%d "
                     "idle_sleep=%.2fs makeup_sleep=%.2fs action=%.2fs "
                     "snapshot=%.2fs watched=%d"
                     % (len(self.background), len(self.observed),
                        len(self.subtracted), len(self.unreadable),
                        self.idle_sleep, self.makeup_sleep,
                        self.action_seconds, self.snapshot_seconds,
                        self.files_watched))
        if not self.background:
            lines.append("NOTE: the background set is empty, so the empty-run "
                         "control subtracted nothing and this reduces to "
                         "'nothing outside the arm moved'. That is the normal "
                         "case inside a worktree; see the module docstring.")
        return "\n".join(lines)


def observe(action: Callable[[], None], root: str = REPO,
            idle_floor: float = IDLE_FLOOR_SECONDS) -> Observation:
    """Run `action` between two snapshots, with an empty-run control first.

    The control leg comes first (nothing runs, only the clock), then the real
    leg.  If the real leg outlasted the control, a make-up idle window covers
    the shortfall and its background is unioned in, so the control's exposure is
    never shorter than the run's.
    """
    # Each snapshot re-enumerates the top level rather than reusing one frozen
    # list. Freezing it was a false negative and a sharp one: a **new** file or
    # directory created at the repo root during the run was not in the list, so
    # it was never hashed, so it never appeared in the diff -- a run that
    # dropped a file in the repo root would have passed silently, which is the
    # exact failure the outer test's own docstring says it exists to catch. It
    # surfaced only when the negative control's victim moved from `proxy/var/`
    # to the root; the listdir it costs is nothing against what it buys.
    unreadable: List[str] = []

    t0 = time.time()
    first = snapshot(root, None, unreadable)
    snap_a = time.time() - t0
    time.sleep(idle_floor)
    t_snap = time.time()
    second = snapshot(root, None, unreadable)
    snap_b = time.time() - t_snap
    idle_seconds = time.time() - t0
    background = set(diff(first, second))

    t1 = time.time()
    action()
    action_seconds = time.time() - t1
    t_snap = time.time()
    third = snapshot(root, None, unreadable)
    snap_c = time.time() - t_snap
    run_seconds = time.time() - t1
    observed = diff(second, third)

    # The make-up window is a second *empty* leg, so its diff is background on
    # the same terms as the first. That is only true because `action` is
    # synchronous: if it ever left a process writing behind it, this window
    # would file the arm's own trailing writes as ambient noise and subtract
    # them. `run_arm` is synchronous, offline and single-threaded
    # (`ledger_abl.py`: zero API calls, zero network), so the premise holds
    # today; it is written down because it is a premise and not a fact.
    makeup_seconds = 0.0
    makeup_sleep = 0.0
    #: Sleeps against the action, not wall clocks against wall clocks: each leg
    #: pays exactly one snapshot per file, so the snapshot cancels out of the
    #: comparison. The earlier `run_seconds - idle_seconds` form compared the
    #: two totals and left the control short by up to one snapshot.
    shortfall = action_seconds - idle_floor
    if shortfall > 0:
        t2 = time.time()
        time.sleep(shortfall)
        makeup_sleep = shortfall
        fourth = snapshot(root, None, unreadable)
        makeup_seconds = time.time() - t2
        background |= set(diff(third, fourth))

    return Observation(sorted(background), observed, idle_seconds,
                       run_seconds, makeup_seconds, len(second),
                       action_seconds=action_seconds, idle_sleep=idle_floor,
                       makeup_sleep=makeup_sleep,
                       snapshot_seconds=(snap_a + snap_b + snap_c) / 3.0,
                       unreadable=unreadable)


#: The criterion this module replaces, kept executable so the negative control
#: can prove it is testing *this change* and not something that was already
#: true.  V12 and V16 established the shape: a negative control that also fires
#: against the old code is not a control for the new code.
#:
#: Do not use it.  It is here to be shown failing.
SUPERSEDED_CONCURRENT_TOKENS = ("/var/", "/runs/", "/out/", "/artifacts/",
                                ".jsonl", ".log", "state.json")


def superseded_criterion(moved: Iterable[str]) -> List[str]:
    """`test_readonly.py:143-149` as it stood before A9.  For contrast only."""
    return [m for m in moved
            if not any(tok in m.replace("\\", "/")
                       for tok in SUPERSEDED_CONCURRENT_TOKENS)]
