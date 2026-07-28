# S2 · 金丝雀重放常态化 + 接入核查清尾

Worker `W-1540`, branch `agent/s2-canary-schedule`, base `ded9cd7`.
Action budget declared ≤12; **spent exactly 12**, in one live sweep.

## What the ticket asked for, and what happened to each part

| ask | outcome |
|---|---|
| 定期重跑脚本 | [`canary_schedule.py`](../../canary_schedule.py) — profiles, due-check, state, exit codes |
| 漂移判据（帧哈希不等 = incident + 冻结战役） | already built in `canary.py`; **kept unchanged**, and now reached by the schedule. What was missing and is added: the *blindness* criterion |
| 接入 reflex 的可调度形态（按天，不必每 5 分钟） | `install` prints a daily scheduled task; `due` is free so the 5-minute reflex can gate on it. **Not installed** — that is an owner action, and a worktree is the wrong place to register a path from |
| 跨会话残留的全量结论 | ACCESS_CHECK §2 — closed; six replays, four sessions, two transports, and the question now has a standing owner |
| 帧缓存与释出许可，交叉核对 `browser-ops/TERMS.md` 后落一行结论 | ACCESS_CHECK §8a — closed, and **less restrictive than we had read it** |

## The one number that mattered

The daily sweep costs **12 actions and gives up nothing.**

INC-009 had already established that only 11 of the full sweep's 16 expected
ACTION hashes can discriminate at all: the other five either repeat their own
game's RESET hash or land on the counterfeit fingerprint `801726dc499f3f52`, so
a forged response satisfies them exactly as well as a genuine one. That finding
was sitting in `ACCESS_CHECK.md` as a caveat on a claim. Read as a *budget*, it
says which steps are worth buying every day.

| profile | actions | discriminating steps | RESET checks |
|---|---|---|---|
| `quick` (daily) | **12** | **11 / 11** | 4 / 4 |
| `full` (weekly) | 16 | 11 / 11 | 4 / 4 |

The four actions `quick` drops are tn36's accepted no-ops; the game stays in as
a **RESET-only check**, which is free — RESET is a command, not an action
(ACCESS_CHECK §6b). So the daily sweep gives up 25% of the cost and 0% of the
drift-detection power, and the weekly sweep exists to buy back the one thing
that is genuinely lost: the *invariance* of those no-ops, which nothing else in
the repository watches.

The plan is **derived from `canary.json` at run time**, not written down. A
re-baseline that changes which steps discriminate changes the plan on the next
run. A hardcoded game list would have gone stale silently, which is the failure
mode this whole instrument exists to prevent one level up.

## What is genuinely new, not just scheduled

`canary.py` could already fail correctly. Three things it could not do:

1. **Buy a prefix.** `apply_plan` truncates `sequence` *and* `expected`
   together. Truncating only the sequence is the bug that would make every
   scheduled sweep report INCOMPLETE — the verdict reserved for an outage —
   and there is a test asserting exactly that failure on the untruncated spec,
   as the negative control for the test asserting the fix.
2. **Notice that it has gone blind.** INCOMPLETE is deliberately neither a pass
   nor drift, so an outage can neither halt the programme nor hide drift. On a
   *schedule* that verdict grows a failure mode of its own: a canary that is
   INCOMPLETE every day has stopped measuring, silently, while its log fills
   with entries. Three in a row now files a `process`-severity incident saying
   so. It does **not** freeze campaigns — being unable to look is not evidence
   that anything changed.
3. **Refuse to spend into an unresolved freeze.** A frozen programme is waiting
   on a human; another sweep answers a question nobody asked. `--force`
   overrides, deliberately and visibly.

## The live sweep

2026-07-28T07:57Z, fourth session, own scorecard tagged `canary/v1/scheduled/quick`.

```
ar25-0c556536  PASS  agreed=6/6  actions=5  http=6
g50t-5849a774  PASS  agreed=3/3  actions=2  http=3
sk48-d8078629  PASS  agreed=6/6  actions=5  http=6
tn36-ef4dde99  PASS  agreed=1/1  actions=0  http=1
```

**16 HTTP calls for 16 commands** (4 RESET + 12 ACTION) — 1.00 attempt per
command, every step first-attempt on every game. That reproduces the
post-INC-007 figure in a session that had nothing to do with the one that
measured it, which is a small independent confirmation that the cookie fix is
the thing doing the work rather than a quiet afternoon on the API's side.

It is also the sixth agreeing replay of the development pile, in a fourth
session, and that is what closes the cross-session-residue item.

## Two things found on the way, both outside the ticket

**`.env` is unreachable from a worktree, and every agent is required to work in
one.** `client.load_api_key` read `<repo>/.env`; in a linked worktree that path
does not exist, because `.env` is gitignored and lives only in the main
checkout. Every network-facing tool in this directory was therefore unusable
from the one place the working agreement puts agents — I hit it trying to run my
own sweep. `client.main_checkout` now follows the `gitdir:` pointer in a
worktree's `.git` file back to the main checkout and looks there, and only
there. Four tests, including the negative controls: a normal checkout has no
fallback, a `.git` file that is not a worktree marker is ignored, and an
explicitly passed `env_path` is never second-guessed.

**`monitor/reflex.py` cannot run.** Line 100 reads `if not hold and avail:`;
`hold` is not assigned until line 143. Every invocation raises `NameError`
before it reaches the reap, the quota check, the CI merge or the dashboard
refresh. `monitor/reflex.log`'s last entry is `03:57:22Z`, and the commit that
introduced the line (`ab99697`) landed at 07:24Z — so the layer has been dead
for hours and would stay dead. Monitor's territory, not mine: filed to
`monitor/inbox/` rather than fixed. It matters to this ticket because the
reflex is the thing that was supposed to call `due`.

## Gaps — declared, not quietly narrowed

* **Nothing is installed.** `install` prints; it does not run `schtasks`. The
  path it would register from here is the worktree's, which disappears.
* **The spend gate is not on this path yet.** `proxy/spend_gate.py` is not on
  master at this commit, so `open_spend_gate` records `spend_gate: "absent"`
  rather than treating absence as approval. When it lands it is used with no
  flag and no opt-out; a test asserts a refusal stops the sweep. The reverse
  direction is *not* done: the gate does not know the canary exists, so nobody's
  headroom calculation currently anticipates 12 actions a day.
* **`blind_after: 3` is a guess.** Nothing measured it. It is in the config file
  so it can be argued with in a diff.
* **The canary still sees only what its sequences reach.** Drift deeper in a
  level, or in response fields other than `frame`, is outside the instrument.
* **The ledger grows by 16 raw response bodies per sweep**, and those bodies are
  ARC's content. The release obligation in ACCESS_CHECK §8.4 is unchanged and
  now compounds daily — an argument for redacting at release time, since the
  ledger's completeness is what makes it evidence.

## Verify

```bash
cd arc-recon && bash verify.sh     # offline: 82 tests, plans, pile hash, ledger audits
```

Green at `20260728T08`. The suite is 82 offline tests (40 inherited + 42 new),
no API, no network.
