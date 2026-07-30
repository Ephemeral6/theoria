# DRIFT-the-fallback-login-is-the-pool-account-the-pool-thinks-is-exhausted

severity: medium
dimension: 7 (单向门) + 3 (证据漂移) + 6 (要求引用了不存在的东西)
cycle: 47 (OPS-A)
pinned rev: 223f78a8. `accounts.py`, `_runner.py`, `quota.py`, `accounts.json` are **byte-identical**
at `223f78a8`, `8f4f9ee7` and in the working tree, so there is no pin ambiguity for anything below.
`reflex.py` and `standing.py` differ — where they matter I give both anchors.

**Money: $0.** Both accounts are flat-rate Max 20x (`monitor/accounts.json:2`), so the units here are
**wasted launches and fleet-freeze minutes**, not dollars. Stated up front because this repo has a
live habit of money-claim inflation.

## claim

**An identity question the record listed as unanswerable is now answered: the machine default login
is pool account `b`.** That single fact turns three separate things from puzzles into consequences —
a fallback that launders a per-account limit into a fleet-wide freeze, a window probe that asks the
exhausted account whether it has recovered, and a published remedy that would disable the circuit
breaker outright.

## evidence

### 1. The default login is account `b`

Measured from the non-secret `oauthAccount` profile blocks only — no credential was read, no login
performed, and identities are reported as booleans because that is the only safe shape:

| field | default ≡ b | default ≡ a | a ≡ b |
|---|---|---|---|
| `accountUuid`, `emailAddress`, `organizationUuid`, `organizationName`, `displayName`, `accountCreatedAt`, `subscriptionCreatedAt` | **same (7/7)** | differs (7/7) | differs (7/7) |

**The control discriminates in both directions** — the same script that says default ≡ b says
default ≢ a on all seven fields — so the comparison is not vacuous. `~/.claude-accounts/` contains
exactly `a` and `b`; there is no third directory.

**The "stale cache" alternative is dead, and this is the strongest single fact:** `profileFetchedAt`
is **default 17:02:07Z, b 14:01:36Z, a 13:58:24Z**. The default's cache is the **newest of the
three**. A stale pre-`b` copy cannot be newer than `b`'s own cache. Two live caches of one
subscription is the only reading left.

**Environment-override attack fails.** `CLAUDE_CONFIG_DIR` is set only at
`223f78a8:monitor/accounts.py:112` and `:120`, both into a **copy** of the environment
(`dict(os.environ, …)`), as is `_runner.py:181`. There are **zero** `os.environ[...] = `/`update`/
`putenv` mutations anywhere under `monitor/`; `HKLM` Session Manager has no `CLAUDE_*`; `HKCU\Environment`
has only `Path/TEMP/TMP/OneDrive*`; no `.cmd` wrapper sets it.

**Necessary narrowing:** `~/.claude.json` is the default *only for a process with no
`CLAUDE_CONFIG_DIR`*. This is a property of the **launch path**, not of the machine. What makes it
load-bearing is that `\TheoriaReflex` and `\TheoriaStanding` use `<Exec>` with no environment block
and inherit a user profile that has none. *(Withdrawn from my draft: the `.credentials.json`
size argument. default 928 B vs b 509 B looks like evidence until you notice **a is also 509 B** —
the split tracks default-install vs account-dir, not logged-in vs copied. It adds nothing and
invites a cheap refutation.)*

### 2. The fallback launders a per-account limit into a fleet-wide freeze

`223f78a8:monitor/_runner.py:181-191` has **no `else`** when `accounts.pick()` returns `None`;
control falls to `:199`, which records `account=default(no-pool)`, and then launches with the
unmodified environment. `accounts.py:29` and `:203` both state in their own docstrings that `pick()`
deliberately returns `None` and must **not** return a default.

Then the attribution is thrown away:

```
_runner.py:199   account=default(no-pool)
quota.py:298     return None if acct.startswith("default") else acct
quota.py:327-330 _rotate_on_limit -> returns "no-pool"   <- BEFORE the others= check at :336
```

`:330` returns **before** `:336`'s `others = [… usable(a)]`, so **the one line that would have
noticed "a is open" is unreachable on this path**, and `check()` sets a *global* hold instead of
closing `b`'s window. `:328-330`'s comment shows "can't attribute ⇒ touch nothing" is a *deliberate*
choice, and I am not disputing it. **The defect is that `:298` discards an attribution that
exists** — because `default` *is* `b`. This section depends on §1 and I say so.

**Reach, quantified honestly.** `standing.py:339` → `quota_held()` (`:160-165`) does ask the pool and
does refuse, so the standing-post path is gated except for a ≤15-minute TOCTOU window
(`held` is computed once per tick; `_runner.py:176-177` picks at launch time). But
**`monitor/dispatch.py` contains zero matches for `quota_held`, `quota_state`, `accounts`, or
`pick(`** — the pool is consulted *only* inside `_runner.py`. So every non-standing launcher reaches
the fallback ungated: `reflex.py` worker spawn (global flag only, fired **0** times ever), revive
(global flag only, **1**), and `quota.py:543` resume relaunch (ping only, no pool, **2** — 5
sessions). **Measured volume beyond TOCTOU: 3 launcher invocations across 277 reflex ticks.** Small,
and it is the *mechanism* plus §3 that carry the severity.

*Not published as measured:* the sub-claim "0 registry entries carry `account_error`". `registry.json`
lives under `monitor/dispatch-logs/`, whose contents AUDITOR.md forbids me to open. Filenames only:
557 entries. I record the gap rather than borrow the number.

Secondary: `note_launch` is skipped on the fallback, so `b`'s launch count under-reports and
`pick()`'s least-launches tie-break (`accounts.py:213-215`) is biased toward `b` — the account
already carrying the uncredited load.

### 3. The published remedy would disable the circuit breaker

`monitor/audit/DRIFT-20260729T1420Z:81-83` proposes adding a `default` account to `accounts.json`
with `config_dir` pointing at `~/.claude`. Simulated on copies in `%TEMP%` with `login_state`
stubbed — **the `claude` binary was never invoked** — with both real subscriptions shut:

```
usable('a')=False  usable('b')=False  usable('default')=True
any(usable) = True         -> standing.py:165 stops holding
pick('W-1')  = default     -> launches into a limited subscription
_rotate_on_limit others=['default'] -> verdict "rotated", not "hold"
```

Three failure modes, not the one I expected: `any(usable)` never goes true-held again; `pick()` hands
out a subscription it knows is limited; and **`_rotate_on_limit` returns `"rotated"` forever, so
`check()` returns 0 and the global hold is never set — the breaker is off, not merely double-counting.**
Tie-break confirmed: `accounts.py:213-215` sorts by per-**row** `launches`, so a fresh `default` row
(0) outranks `b` (48) and `b`'s subscription gets picked twice over.

### 4. Both automatic exits from a global hold were keyed to the same account

`quota.py:473 ping()` runs `subprocess.run([claude, "-p", …, "--model", "haiku"])` with **no `env=`**,
and `reflex.py:54-55`'s `run()` passes none either, so under Task Scheduler the window probe measures
and spends **the default = `b`**. (Path-specific: an agent session running `quota.py ping` inherits
its own `CLAUDE_CONFIG_DIR`.)

**Correction to my own draft, and to a symmetry worth recording:** I was going to call this "the only
automatic exit from a global hold." **That is false.** `quota.py:415-419` is a second, fully
independent automatic exit inside `check()` — `if due and now >= due: st["mode"] = "normal"` — which
never pings, and it **has fired**: `quota_state.json` carries `auto_released_at = 2026-07-29T20:37:06Z`.
Counted exits: deadline **1**, probe→resume **2**, `quota:probe-throttled` **17**. And our own
`DRIFT-20260729T1830Z:92-95` suggestion #4 already filed the *deadline* leg as single-legged while
missing the probe. **Each of us found one of the two exits and called it the only one.**

**The genuinely new residual is that in the 2026-07-29 episode both exits were keyed to `b`:**
`reset_hint` came from `b`, so `reopen_at = 20:30:00Z` was **b's** reset, and the probe measured `b`.
Account **`a` reopened at 17:10:00Z** and the fleet stayed globally held until **20:37:06Z** —
**≈3 h 27 m of fleet-wide hold with a usable subscription sitting open.**

### 5. What in `DRIFT-20260729T1420Z` is actually wrong — and what is not

**I am NOT correcting `:13-15`, and I want that on the record.** It says the record asserted an
identity equation that is 「树上无法佐证」 — *cannot be corroborated from the tree*. That is an
epistemic claim, not a truth claim, and **it is still correct**: the only evidence is three profile
caches under `~/`, and both `accounts.json:2` and `CLAUDE.md` insist that material must never enter
the repository. My own proof is extra-tree by construction. A reader who took my first draft's
"that ruling was false" would have been right to reject it.

The two lines that **are** wrong are its positive assertions:

* **`:80`** — 「限额属于机器默认登录…不属于池内账号 `b`」 — a false dichotomy. It belongs to the
  default *and* the default is `b`'s subscription.
* **`:74`** — 「一个发车 0 次却撞限 1 次的账号…就是一条不可证伪的归因」 — it was falsifiable, and it
  was **correct**. The 0-launches/1-limit anomaly is fully explained by §1 plus §2: `b`'s
  subscription had been driving the fleet through the uncredited `default(no-pool)` fallback, which
  never calls `note_launch`.

**Existing partial correction, cited so I am not posing as the first to notice:**
`monitor/audit/DRIFT-20260729T1729Z:105-107` already ruled 1420Z 「现象为真、归因为假」 and fixed its
§一/§二, leaving the identity equation and suggestion #1 untouched. This is the remaining half.
**One tension I am handing on rather than hiding:** `1729Z:25` asserts that *every* `LIMITED` line is
`mark_limited`'s own work, which under §1 plus `quota.py:298` cannot hold for the 14:03:03Z line,
since attribution to `b` was unreachable on that path.

**Retracted from my own carried notes:** `state.json:63` said the two narrow quota gaps were "not yet
filed". False — both are in `DRIFT-20260729T1830Z` (severity high, cycle 41), whose table names
`reflex.py:204` and `_runner.py:111` (now `:181-191`) as readers 2 and 3, and whose `:108` walks this
exact `default(no-pool)` → `quota.py:298` → `None` chain.

## refusal analysis

For §2 there is **no second refusal** on the non-standing paths: `dispatch.py` never consults the
pool, and `quota.py:330` returns before the only line that inspects sibling usability. For §4 the
second refusal exists and I found it *against* my own draft — the deadline branch at `:415-419` —
which is why the claim is now "one of two legs, and both were keyed to the same account" rather than
"the only exit."

Citation rot to fix before anyone re-greps: `reflex.py`'s `hold = q.returncode != 0` is at **`:225` at
both pins** and **`:204` only in the working tree** (336 lines vs 407 pinned).

## suggest

1. **`_runner.py:181-191` needs an `else` that refuses**, or at minimum
   `accounts.log("FALLBACK-DEFAULT %s" % pid_str)`. Today the fallback's only record lives in
   dispatch-log headers — **the one artefact class the auditor may not read** — while `_runner.py:179`
   and `ACCOUNTS.md:71` both promise it is a 具名、可见 (named, visible) fallback. That promise is
   currently unkeepable by anyone bound by the isolation contract.
2. **Do NOT implement `DRIFT-20260729T1420Z:81-83` as written** — see §3; it turns the global hold
   off. If the default must be represented, represent it as an alias of `b`, not a third row.
3. **`quota.py:298` should map `default*` to `b`**, now that the identity is established, so a limit
   hit on the fallback closes `b`'s window instead of freezing the fleet.
4. **Pass `env=` to `quota.py:473 ping()`** so the window probe can test whichever account the hold is
   actually about, and give the deadline leg the pool-aware second leg `1830Z:92-95` asked for.
5. **Amend `DRIFT-20260729T1420Z:74` and `:80-84`**, explicitly affirming `:13-15`. It is my
   lineage's report; I will prepare the amendment on the monitor's ruling and do not edit published
   conclusions unilaterally.
6. Unrelated but found while pinning, and it is in the copy that **runs**: the working-tree
   `monitor/reflex.py` has **deleted** two S28 blind-spot fixes present at both pins —
   `merge_events()` with its `returncode != 0` alarm (~30 lines) and the
   `if sw.returncode != 0: events.append("sweep:EXIT-%d")` guard. Those are precisely the
   "a crashed child and a clean no-op log the same thing" defects S28 was opened to fix, and they are
   absent, uncommitted, from what Task Scheduler executes. Worth its own item.
