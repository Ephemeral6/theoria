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

## What the control does *not* remove, measured rather than argued

An empty-run control subtracts a writer only if that writer is active during
**both** legs.  That covers continuous churn -- which is what the original false
positive was: a running fleet appending to `proxy/var/spend_gate.jsonl`.  It does
**not** cover a *periodic* writer whose period is much longer than either leg;
such a writer is absent from both legs most of the time and present in exactly
one leg occasionally, and when that one leg is the real one the check goes red
for something this arm did not do.

This is not hypothetical here.  `runs/20260728T191437Z-A9-readonly-baseline/`
measured it on the live worktree: the tree is completely still at 2s, 5s and 15s,
then moves four files at 30s -- `monitor/index.html`, `monitor/reflex.lock`,
`monitor/reflex.log`, `monitor/state.json` -- the monitor's reflex loop, 127
ticks logged, median gap 300s, shortest 42s.  Against a ~0.95s run leg that is a
residual false-red probability of about 2% per run, worst case.

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
SKIP_DIRS = frozenset({
    ".git", ".worktrees", "__pycache__", ".pytest_cache", ".toolchain",
    ".lake", ".mypy_cache", ".ruff_cache", ".venv", "node_modules",
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
#: * `**/ledger.*.jsonl` -- the ledgers are sharded in practice
#:   (`baseline-arms/out/shards/ledger.a7-g50t.jsonl` and ten siblings exist on
#:   this tree).  A hard list that only matches the unsharded name would not
#:   have covered a single one of the ledgers that actually exist there.
#: * `**/candidates.jsonl` -- the frozen contract's append-only stream.
#:   `CLAUDE.md` names it by that name ("`candidates.jsonl` is append-only");
#:   the audit's table lists `engine-rig/artifacts/candidates.jsonl` as one of
#:   the paths the old criterion wrongly excluded, and `CONTRACTS/**` does not
#:   reach it because it does not live under `CONTRACTS/`.
HARD_LIST_EXTENSIONS: Tuple[Tuple[str, str], ...] = (
    ("**/ledger.*.jsonl", "sharded ledgers: the form the ledgers actually take on this tree"),
    ("**/candidates.jsonl", "the frozen contract's append-only stream, which lives outside CONTRACTS/"),
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
    """
    out = []
    for name in sorted(os.listdir(root)):
        if name == ARM or name in SKIP_DIRS or name.startswith("."):
            continue
        out.append(name)
    return tuple(out)


def snapshot(root: str = REPO,
             entries: Optional[Sequence[str]] = None) -> Dict[str, str]:
    """repo-relative path (forward slashes) -> sha256, for everything watched."""
    out: Dict[str, str] = {}
    for name in (watched(root) if entries is None else entries):
        full = os.path.join(root, name)
        if os.path.isfile(full):
            try:
                out[name.replace(os.sep, "/")] = sha256_file(full)
            except OSError:
                pass
            continue
        for dirpath, dirnames, filenames in os.walk(full):
            dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
            for fname in sorted(filenames):
                path = os.path.join(dirpath, fname)
                rel = os.path.relpath(path, root).replace(os.sep, "/")
                try:
                    out[rel] = sha256_file(path)
                except OSError:
                    # Vanished or locked mid-walk. A concurrent session's file
                    # we cannot read is not evidence about this arm.
                    continue
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
                 makeup_seconds: float, files_watched: int):
        self.background = background
        self.observed = observed
        self.idle_seconds = idle_seconds
        self.run_seconds = run_seconds
        self.makeup_seconds = makeup_seconds
        self.files_watched = files_watched
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
        """Was the empty leg exposed at least as long as the real leg?"""
        return (self.idle_seconds + self.makeup_seconds) >= self.run_seconds

    def as_dict(self) -> Dict[str, object]:
        return {
            "files_watched": self.files_watched,
            "idle_seconds": round(self.idle_seconds, 3),
            "makeup_seconds": round(self.makeup_seconds, 3),
            "run_seconds": round(self.run_seconds, 3),
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
        lines.append("background=%d observed=%d subtracted=%d "
                     "idle=%.2fs makeup=%.2fs run=%.2fs watched=%d"
                     % (len(self.background), len(self.observed),
                        len(self.subtracted), self.idle_seconds,
                        self.makeup_seconds, self.run_seconds,
                        self.files_watched))
        return "\n".join(lines)


def observe(action: Callable[[], None], root: str = REPO,
            idle_floor: float = IDLE_FLOOR_SECONDS) -> Observation:
    """Run `action` between two snapshots, with an empty-run control first.

    The control leg comes first (nothing runs, only the clock), then the real
    leg.  If the real leg outlasted the control, a make-up idle window covers
    the shortfall and its background is unioned in, so the control's exposure is
    never shorter than the run's.
    """
    entries = watched(root)

    t0 = time.time()
    first = snapshot(root, entries)
    time.sleep(idle_floor)
    second = snapshot(root, entries)
    idle_seconds = time.time() - t0
    background = set(diff(first, second))

    t1 = time.time()
    action()
    third = snapshot(root, entries)
    run_seconds = time.time() - t1
    observed = diff(second, third)

    makeup_seconds = 0.0
    shortfall = run_seconds - idle_seconds
    if shortfall > 0:
        t2 = time.time()
        time.sleep(shortfall)
        fourth = snapshot(root, entries)
        makeup_seconds = time.time() - t2
        background |= set(diff(third, fourth))

    return Observation(sorted(background), observed, idle_seconds,
                       run_seconds, makeup_seconds, len(second))


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
