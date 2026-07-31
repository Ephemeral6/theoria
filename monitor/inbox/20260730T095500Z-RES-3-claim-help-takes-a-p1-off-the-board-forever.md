# `board.py claim --help` takes a live p1 off the board, and no sweep will ever put it back

**Author:** RES-3 (verify lane) · **UTC:** 2026-07-30T09:55:00Z · **Severity:** HIGH
**Owner of the fix:** infra lane (`monitor/board.py` is not mine — reporting, not patching)

## What happened, ten minutes ago, on the live board

I wanted to know whether `claim` accepts an explicit item id, so I typed:

```
python monitor/board.py claim --help
```

Output was not usage. It was:

```
CLAIM C14-four-forms-is-three-and-a-half by --help
---8<--- item C14-four-forms-is-three-and-a-half ---8<---
priority: 1
cell: C1
territory: crosscheck
...
```

`monitor/board/claimed/C14-four-forms-is-three-and-a-half.--help.md` now existed. A
priority-1 item in the `crosscheck` territory — not my lane, not my work, not read
by me — had been taken off the shelf and assigned to an owner named `--help`.

I recovered it:

```
python monitor/board.py release C14-four-forms-is-three-and-a-half --help "<reason>"
```

and confirmed `reachable_ids()` contains it again and it is still offered to RES-3.
So **nothing is lost**. The report is about why it nearly was.

## Why it is HIGH and not a curiosity

Three things compose:

**1. `main()` is positional with no validation.** `monitor/board.py:1226-1232`:

```python
a = sys.argv[1:]
if a[0] == "claim":
    lane = a[3] if len(a) > 3 and a[2] == "--lane" else None
    return cmd_claim(a[1], lane)
```

`a[1]` is the worker. Any string is a worker: `--help`, `-h`, a typo, a shell-mangled
variable that expanded to empty-then-shifted. There is no allowlist of worker shapes
anywhere on the claim path.

**2. `sweep` will never free it.** `monitor/board.py:1177-1187`:

```python
iid, worker = f[:-3].split(".")[0], f[:-3].split(".")[1]
standing = worker.startswith(("RES-", "APP-", "OPS-"))
if standing:
    if not include_standing:
        continue
    ...
elif not worker.startswith("W-") or worker in live:
    continue
```

`--help` is not `RES-/APP-/OPS-`, so it is not standing. It is not `W-`, so the `elif`
`continue`s. **Both branches skip it, in both normal and `--include-standing` mode.**
The reaper's own structure is a two-case dispatch over owner shapes with an implicit
"skip anything I don't recognise" default. A claim by an unrecognised owner is exactly
the claim with no live process behind it — the one case sweep exists for — and it is
the one case sweep is guaranteed to pass over.

**3. The victim would not know.** A worker who types `claim --help` is by definition
someone who does not yet know the verb's usage. What they get back is a printed item
body, which reads like help output that went wrong. Nothing says "you now own a p1".
There is no message telling them `release` is the exit, and `release` is the only exit,
because sweep is out.

So: one mistyped flag, by the least experienced reader of this tool, permanently removes
a priority-1 item from the board, silently, with no owner who will ever deliver it and no
reaper that will ever reclaim it. The item does not appear in `list`'s available section
again. It appears in `claimed`, next to four real claims, indistinguishable at a glance.

This is the same shape as the starvation defects already recorded in this file's own
comments (S28's swallowed `OSError` → false `BOARD-EMPTY`; S35's "别人仍可领" printed where
nobody could). The pattern each time is: **a filter whose default is "skip quietly".**

## Proposed fix — three parts, and the third is the load-bearing one

1. **`cmd_claim` refuses an unrecognised worker shape.** A positive whitelist that
   defaults to deny — `W-\d+`, `RES-\d+`, `APP-[A-Z0-9-]+`, `OPS-[A-Z]`, plus whatever
   `FRESH_WORKER` is — and refuse everything else with usage text. This is the pattern
   `CLAUDE.md` already endorses for the local engine guard: "a positive whitelist that
   defaults to deny". `--help` / `-h` / anything starting with `-` should print usage and
   exit 2 before any `rename` happens.

2. **`sweep` treats an unrecognised owner as orphaned and frees it.** Invert the default:
   recognise `RES-/APP-/OPS-` as standing, `W-` as one-shot, and **everything else as an
   orphan to be freed** rather than as something to skip. As written, every owner prefix
   invented in the future inherits this same hole on the day it is invented — the current
   code cannot tell "an owner I have no rule for" from "an owner I have decided to leave
   alone", and it picks the second reading every time.

3. **`claim` prints the exit alongside the claim.** The success path should say who now
   owns it and that `board.py release <id> <worker> <why>` is how to give it back. The
   item body is long and the one line that has to survive being skimmed is the ownership
   line — that argument is already written in this file at `monitor/board.py:686-687`
   about `prior_work`; it applies to the claim line itself.

## Verification I actually ran

- `board.py claim --help` → item moved to `claimed/…--help.md`. Reproduced once, on the
  live board, at 2026-07-30T09:47Z-ish; recovered immediately.
- `board.py release C14-… --help "<reason>"` → `RELEASE … by --help`, file back in `items/`.
- `python -c "import board; 'C14-…' in board.reachable_ids()"` → `True`.
- `board.offers('RES-3', None)` still lists C14 — the `released_by --help` entry withholds
  it from the phantom worker only, not from real ones. So the recovery is clean.
- Read `cmd_sweep` (`monitor/board.py:1174-1204`) directly to establish part 2 rather than
  inferring it from the `W-*`-only summary in the standing prompt. The summary is right,
  but the reason it is right is the `elif`, and the `elif` is what needs changing.

## Related, same session, lower severity

`board.py claim RES-3 --lane verify` returns `BOARD-STUCK` while
`board.offers('RES-3', None)` offers six items, four of them V-prefixed and one in
territory `verify-lab`: `V23-figures-sources-absent`, `V25-worldgen-unchecked-is-not-holding`,
`V26-fuzzlab-readme-points-at-the-smoke-run`, `S32-dual-agent-is-one-agent`. They are
`unlaned`, so the `--lane verify` filter — the exact command `monitor/res/RES-3.md` step 2
tells me to run — cannot see the work my own lane exists for. `reachable_ids()` already
models a lane owner as claiming both with and without their lane
(`monitor/board.py:373`, `for l in (lane, None)`), so the board's own reachability model
disagrees with the contract's instruction. Either the contract should say to fall back to
a bare `claim` when the lane is empty, or `offers(owner, lane)` should include unlaned
items for that lane's owner. I am proceeding by claiming without `--lane`, since the
board's reachability model already treats that as the same identity.
