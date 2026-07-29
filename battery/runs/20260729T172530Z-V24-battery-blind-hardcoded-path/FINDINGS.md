# V24 — findings, written as they were established

Worker W-1682. Territory `battery`. Zero API calls, zero sealed-pile contact.

## F1 — the hardcoded path does not merely risk vanishing; it already resolves to the wrong tree

`battery/audit/v9/make_blind.py:16` reads

```python
SRC = r"C:\Users\user\Desktop\theoria\.worktrees\v9-battery-gaming-audit"
```

That worktree is checked out at branch `agent/v9-battery-gaming-audit`, whose HEAD
is `0d586b6f` (`git worktree list`; worktree working tree is clean). The ticket's
concern was that a cleanup would delete the directory and the blinding step would
break. That is true, but it is the smaller half of the problem.

The blinding was performed at commit **`9892d23c`** (2026-07-29 09:52:28 +0800,
"battery V9: pre-registration, poverty certificate, blinding — before any attack").
That commit is the one that introduced, together, `PREREG_V9.md`, `BLINDING.md`,
`make_blind.py`, `check.py` and `attack.py` — matching `BLINDING.md` §preamble
("写在攻击开始之前，与 `PREREG_V9.md` 同一个 commit").

Between `9892d23c` and the worktree's current HEAD `0d586b6f`, five of the ten
files in `make_blind.COPY` changed:

```
$ git diff --stat 9892d23c 0d586b6f -- battery/__init__.py battery/model.py \
      battery/metrics/ battery/audit/v9/check.py battery/audit/v9/attack.py
 battery/audit/v9/check.py    | 35 +++++++++++++++++++++++++++++++++--
 battery/metrics/__init__.py  | 20 ++++++++++++++++++++
 battery/metrics/economy.py   | 40 +++++++++++++++++++++++++++++++++++++++-
 battery/metrics/epistemic.py | 29 ++++++++++++++++++++++++++++-
 battery/metrics/mechanism.py | 23 ++++++++++++++++++++++-
 5 files changed, 142 insertions(+), 5 deletions(-)
```

and the commits that changed them are the *post-attack* ones:

| commit | time | subject | COPY files touched |
|---|---|---|---|
| `9892d23c` | 09:52 | pre-registration, poverty certificate, blinding — before any attack | `attack.py`, `check.py` (added) |
| `520dc5dd` | 10:11 | 105 blind attacks, 37 of 38 metrics gamed, **three defences** | `metrics/{__init__,economy,epistemic,mechanism}.py` |
| `efc21d12` | 10:48 | the adversarial review changed the answer, twice | `check.py` |

So the four metric modules were edited **to add the defences the attacks
provoked**, and `check.py` was edited again after adversarial review. Running
`make_blind.py` today, against the path it hardcodes, therefore builds a blinded
tree containing code the six attackers never saw — the defences that were written
*because of* their attacks. The step named "blinding" would silently reconstruct
a tree that is not the blind.

This is exactly the failure mode the ticket's clause 1 warns about ("一个悄悄
致盲失败的审计，比没有审计更坏，因为它照样出结论"), except that it is not
hypothetical: it is the current state of the file.

**Consequence for the fix:** the ref must be pinned to `9892d23c`, not to the
branch name `agent/v9-battery-gaming-audit` and not to the branch tip. A branch
name would have reproduced the same defect one indirection later.

`9892d23c` is an ancestor of `master` (`git merge-base --is-ancestor 9892d23c
master` → true), so `git show 9892d23c:<path>` keeps working after the worktree
and the branch are deleted. That is what makes the ref-based form safe to hand to
the cleanup.
