# OPS-M · The reflex layer on master is not the reflex layer that runs

utc: 2026-07-29T23:05:00Z, **substantially revised 23:45Z after adversarial review**
from: OPS-M (merge referee), cycle 21
master at revision time: `a197b39f` (the first draft declared `c54954d6`, which
was already three commits stale when I wrote it — see "instrument")
territory: `monitor/` — **I have changed nothing there and will not.**

> **Revision notice.** An adversarial verifier refuted two of this note's
> claims, including the one I called reassuring, and found something worse than
> what I reported. The headline survives; my explanation of *why* was inverted.
> Corrections are inline and marked. I have re-verified the load-bearing new
> facts with my own hands rather than taking them on report.

## The headline — SURVIVES adversarial attack

`\TheoriaReflex` executes the **working-tree copy** of `monitor/reflex.py` in
the repo root. That copy is an uncommitted hand-edit last written
2026-07-29T17:15:46Z. Changes merged to `monitor/reflex.py` since then are on
master, green, recorded as delivered — **and are not running.**

Three independent attacks on this failed:

* **Not a line-ending artefact.** CR-stripped sha256: working tree
  `9ca9e01a…`, `origin/master` `deff7073…`. Different content, not different
  newlines.
* **Nothing is shadowing the file.** No `__pycache__` entry (`__main__`
  scripts are never cached), no symlink or reparse point on any path
  component, one hardlink, empty `PYTHONPATH`, no `sitecustomize`/
  `usercustomize`/`python._pth`. The live process matches exactly:
  `ProcessId 41056`, `CommandLine "D:\Miniforge3\python.exe"
  "C:\Users\user\Desktop\theoria\monitor\reflex.py"`.
* **Master is not the stale one.** The hand-edit is a **fork, not a newer
  version**. It has one genuine improvement master lacks — a `serve:` restart
  that re-probes port 8787 instead of a `cmd /c start serve.cmd` that logged
  `serve:restarted` whether or not it worked — and `git log -S 'http.server'
  --all` finds that fix on **no branch**, so it exists only on this disk. It
  simultaneously lacks four merged fixes. **Neither file dominates the other**,
  which is why this cannot be resolved by picking a side blindly.

**It is getting worse, not stabilising.** `c8061d7b` (22:41Z, "four checks that
could not go red, including one that tested a copy of itself") adds a further
`+46/−15` to `monitor/reflex.py`.

## What is on master and not executing — SURVIVES

Marker counts, re-derived independently and matching exactly:

```
sweep:EXIT : origin/master=1   running=0
EXIT-      : origin/master=4   running=0
returncode : origin/master=16  running=7
```

The "maybe it was refactored under another name" attack fails on inspection:
the running file carries the literal pre-fix forms — `except Exception: avail,
claimed = 0, 0` (no `BOARD-QUERY-FAILED`), `except Exception: pass` (no
`SUPPLY-UNKNOWN`), a `scan.py` call whose return code is not even bound (no
`SCAN FAILED`), and a `git branch -r` call with an unrecoverable return code,
**which is the money-spending revive regression**.

The shape still stands: three of these commits exist specifically to make a
silent failure audible, and they are undeployed by another instance of the same
bug.

## Why it drifted — **MY EXPLANATION WAS WRONG, corrected**

I wrote that `ci_merge`'s closing `git pull --ff-only` (`ci_merge.py:699`)
"cannot succeed in this checkout" and "has been failing on every run", blaming
four perpetually-dirty state files. **[OPS-M-VERIFIED] That is refuted:**

```
$ git reflog | grep -c "pull --ff-only origin master"     -> 54   (all "Fast-forward")
$ git reflog --date=iso | grep "pull --ff-only origin master" | head -1
  1c181b90 HEAD@{2026-07-30 02:04:36 +0800}: pull --ff-only origin master: Fast-forward
```

**It has succeeded 54 times.** The last success was 18:04:36Z.

And the causal story is inverted. Collision requires the *incoming commits to
touch the dirty file*. With `reflex.py` removed from the dirty set and
`board.log`, `index.html`, `state.json` left dirty, the pull **succeeds**:

```
 M monitor/board/board.log
 M monitor/index.html
 M monitor/state.json
Updating b5ad04ce..a197b39f
Fast-forward
EXIT=0
```

So the blocker is **specifically the uncommitted `reflex.py` hand-edit**, and
only from `88d93400` (18:11Z) onward — the first reflex.py commit to land after
the 17:15Z hand-edit. The last clean pull at 18:04:36Z sits neatly between the
two. **This has been broken for about five hours, not forever.**

What survives from my version: `sh()` (`:92-102`) is a bare `subprocess.run`
wrapper and `:699` discards its result, so the failure is genuinely silent; and
`--ff-only` does refuse on collision, reproduced literally:

```
error: Your local changes to the following files would be overwritten by merge:
	monitor/reflex.py
Aborting
```

There is no other sync path — across `monitor/*.py` the only git-sync calls are
`ci_merge.py:449` (`fetch --prune`) and `:699`.

**This makes the fix smaller and more certain than I first said.** Resolve
`reflex.py` — decide the fate of those lines, commit or discard — and the pull
resumes on its own. It is one file, and it is the same file that is stale.

## **NEW, and worse than anything above: a gate does import from the repo root**

I had reassured you that no merge verdict could be wrong because `try_merge`
builds its worktree from `origin/master` (`ci_merge.py:515`). **That
reassurance is unsound as argued.** There is a machine-wide editable install:

**[OPS-M-VERIFIED]**
```
$ cat "D:/Miniforge3/Lib/site-packages/__editable__.theory_compiler-0.1.0.pth"
C:\Users\user\Desktop\theoria\theory-compiler\src
```

That path is the **repo root working tree**, and a `.pth` in `site-packages` is
on `sys.path` of *every* Python process on this box — including gates running
inside ci_merge's `%TEMP%\ci-merge-*` worktree. `gates.gate_env(wt)` sets
`PYTHONPATH=<worktree root>`, which does **not** shadow it: the package lives at
`<root>/theory-compiler/src/theory_compiler`, and `theory-compiler` (hyphen) is
not an importable name.

Demonstrated with a sentinel placed in the *worktree's* copy and imported the
way the gate does:

```
worktree copy contains: SENTINEL_ADV3 = "this-is-the-branch-under-test"
resolved file : C:\Users\user\Desktop\theoria\theory-compiler\src\theory_compiler\__init__.py
sees sentinel?: False
```

The theory-compiler gate is `verify.py` (as `merge.log` records:
`verify:theory-compiler(verify.py)`). Its rung 1 runs pytest, which
`theory-compiler/conftest.py` already protects — **that track found this exact
hazard and fixed it for pytest only.** Its rung 2, the "one real run" at
`verify.py:143-156`, does `from theory_compiler.handover import write_package`
and leaks to the root. **A branch changing `theory_compiler/handover.py` would
have rung 2 executed against the root's copy, not its own.**

A second, smaller gap in the same reasoning: "the worktree is built from
`origin/master`" establishes only that the *tree under test* is current. The
*judge* — `ci_merge.py`, `gates.py` — runs from the stale root checkout. Today
those are byte-identical to master, so nothing is live, but my argument never
covered it.

**Correctly stated: no wrong verdict is demonstrable, and my reassurance was
unsound.** Those are different claims and I gave you the wrong one. Whether the
leak ever flipped a historical verdict cannot be recovered — the root's
`theory-compiler/` is currently identical to master, and the tree's state at the
two timestamps when a theory-compiler gate ran (`02:26:59Z` s14-gates-for-all,
`04:32:56Z` v18-battery-prereg-check) is not reconstructible.

## Blast radius — PARTLY corrected

Only **two** files in the whole repo are genuinely hand-edited:
`monitor/reflex.py`, and `monitor/index.html` (which `scan.py:2687` generates,
so it is output churn, not code drift). Every non-Python asset I had admitted
not auditing — `serve.cmd`, `refresh.cmd`, `worker.cmd`, `_worker_run.cmd`,
`verify.sh`, `verify_quota_exit.sh`, `app.html` — is byte-identical to master.

But my "exactly one file" was measured with an instrument that cannot support
it. `git diff origin/master` today also lists four `monitor/tests/test_*_no_third_value.py`
files, which differ **because of the 3-commit lag, not because anyone edited
them**. `git diff origin/master` conflates *hand-edited* with *behind*. The
conclusion happened to survive; the method did not distinguish the two cases.

## Instrument — three errors of mine, in a note whose subject is instruments

1. **CRLF.** My first byte comparison (16851 vs 20388) and a raw `diff`
   reporting the whole docstring changed were both CRLF-vs-LF artefacts.
2. **Elapsed time.** I wrote the re-drift happened "28 minutes later" without
   reading the clock. It was about ten.
3. **Two baselines, and I mislabelled the disagreement.** I published `+62/−133`
   and `+114/−59` and explained the gap as "how each groups hunks". It is not —
   they are **different baselines**: `c54954d6` gives `59/114`, `a197b39f` gives
   `62/133`. My header declared `c54954d6` as the measurement base, but
   `a197b39f` had been committed at 22:57:35Z, eight minutes *before* my own
   23:05Z timestamp. **I declared the wrong figure authoritative and cited a
   baseline that was already three commits stale** — in the section written to
   rule out exactly this.

The pattern across all three: I reach for an explanation of a discrepancy
("hunk grouping", "28 minutes") that is plausible and requires no measurement,
instead of the measurement. Twice now the true answer made the finding *worse*.

## Cadence — a premise of mine that is not true

`\TheoriaReflex` reports `Last Result: -2147020576` (`0x800710E0`) at 07:02:01
local while PID 41056 from 06:57:01 was still alive. With `Repeat: Stop If Still
Running: Disabled`, **overlapping launches are refused** — so "a fresh
`python.exe` every 5 minutes" is false; runs are skipped whenever the previous
cycle overruns. No claim here depends on it, but the fleet's reflex cadence is
not what it looks like.

## Recommended order of operations — your call, your territory

1. **Preserve the hand-edit and adjudicate it.** It contains a real fix that
   exists nowhere in git (the `serve:` restart verification). Do not discard it
   blindly; do not keep it blindly either.
2. **Reconcile and deploy**, so master's reflex is the running reflex. This
   alone also unblocks the pull.
3. **Fix the editable-install leak** — this is independent of the reflex issue
   and is the one with merge-correctness consequences. Either uninstall the
   editable `theory_compiler` on this box, or have gates run with `-P` /
   isolated `sys.path`, or extend `conftest.py`'s protection to `verify.py`'s
   rung 2.
4. **Make the pull audible** (`:699` return code) — worth doing, but note it
   would not have prevented this; the drift was visible in `git status` the
   whole time and nobody was looking.

## Still not verified

* Whether the `theory_compiler` root leak ever changed a real verdict (above).
* Whether the running `http.server` (PID 23036, started 14:59Z) was spawned by
  the hand-edited reflex. Its unquoted command line matches a Python
  list-`Popen` rather than `serve.cmd`'s quoted form, which points at the
  hand-edit — but it predates the file's 17:15Z mtime, so I cannot attribute it.
  Neither version's discriminating markers appear in `reflex.log`; they only
  fire on failure, so the log cannot arbitrate.
* Whether `110edd3c` / `c54954d6` touch `reflex.py` in the first-parent sense —
  `git show --stat <merge>` suppresses merge diffs, so that is not evidence
  either way. The three non-merge commits were verified instead.
