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

---

## AMENDMENT 2026-07-30T04:17Z（周期 48 · 两个独立 refuter 之后。**§1 更硬了，§2 与 §4 都要降**）

上一周期这份报告在收工前落盘，指定的 refuter 没赶回来。本轮我派了两个独立方向去打它，
两个都回来了。**§1（身份证明）经受住了，而且被加固；§2 的后果链与 §4 的一个数字必须改。**
按本文件自己的红线，我不回填正文，全部写在这里。

### §1 身份证明：**未被推翻，且四个混淆已被逐一排除**

原文只做了字段比对。refuter 补上了我没做的对照，四条都不成立：

* **同一目录／符号链接／junction**：三个 config dir 都真实存在，`reparse_point=False`，
  `realpath` 两两不同；`~/.claude-accounts` 下恰好只有 `a`、`b`。
* **同一文件／硬链接**：file id 各异，`nlink=1`，三对两两字节比对全 False。
* **`b` 是默认存档的复制品**：**决定性排除**。复制会带上安装期字段，而 `userID` 与
  `firstStartTime` 在 default~b **不同**；default 有 54 个顶层键、b 只有 26，
  **30 个键只有 default 有**。而且 `monitor/accounts.py:238-260 scaffold` **根本不复制**任何东西，
  它只 `makedirs` 再写两个布尔键。仓库里的工具做不出这种「相同」。
* **同源就会导致相同**：refuter 找到了一个我没用的**内部对照**——
  `a` 与 `b` 的顶层键集完全相同、`projects` 也相同（它们是同源孪生），
  **但 7 个身份字段 a~b 全异**。所以同源不产生 `oauthAccount` 相同，只有同一账号才会。

**唯一应加的收窄**：`oauthAccount` 是 profile 缓存而非活令牌，三份存档的凭据文件 mtime
都晚于自己的 `profileFetchedAt`（差 7.9–9.3 小时）。所以严格表述是
**「默认 config dir 的 profile 缓存所指的订阅，与池内 `b` 的缓存是同一个」**，
「默认登录就是 b」= 这句话 + 「一份持续被写入的活缓存是当前的」这个常识假设。
我没能打破那个假设，但把它写出来，免得被当成比实际更强的结论。
（另有一处措辞小错：`profileFetchedAt` 是 epoch **整数**，不是正文暗示的 ISO 字符串。）

### §2 后果链：**每一行都对，结论错。降为 informational，不算漂移**

原文 `:166-168` 写「§2 在非 standing 路径上**没有第二条拒绝**」。**这句是假的，有两条，都在同一个函数里**：

1. **`monitor/quota.py:321-324` 是一个循环，不是一次读取**：
   `for pid_str, _line in hits: … if acct: break`——它会扫**每一个**被杀的会话，
   只有当**全部**都是回落发车时才放弃。批次里有一个池内会话，归因就成功。
   所以原文 `:71-72` 的「那唯一会注意到『a 还开着』的行不可达」，
   前提是**整批全是回落发车**，而不是「有一次回落发车」。
2. **`monitor/quota.py:325-326`**：`if acct is None and fresh: acct = _last_scanned_account()`
   ——第二个独立归因来源，在 `:330` 之前。

第三条在函数之外，它限定了「整队」这个词：**`monitor/standing.py:163-165`**
`if pool: return not any(_acct.usable(a) for a in pool)`——它**问池子，不看全局 flag**。

**而最要紧的是实测：那个有害结果的样本量是 0。**
`quota_state.json` 共 **12** 次 hold，池配置之后 **6** 次，归因失败 **3** 次——
**三次全部落在 13:07:57Z–13:17:11Z 这 57 分钟里，即两个账号都还没登录之前**。
那时 `pick()` 返回 None 是**正确的**，回落是唯一能发车的方式，全局 hold 也是**正确的**。
两次池后的 `"hold"`（16:32:10Z、2026-07-30T01:17:09Z）都是**两个账号同时关闭**时的合法停机。
**本报告标题所指的那件事——「a 还开着却整队冻结」——从未发生过。**

**并且它是已登记的限制**：`monitor/ACCOUNTS.md:69-71` 把整条 §2 后果写在明面上，
包括那句 **「只是撞限时仍然会整队停机」**。原文只引了同一处的后半句
（`:180` 的「具名、可见」承诺），而**前半句本身就是这个发现**。
它的免责范围写着「在你登录之前」，而**三次实测firing全部落在这个范围内**。
机制本身也是既有项：`DRIFT-20260729T1830Z:107-109` 早一个周期走过同一条链，severity high。

**结论：§2 降为 informational，并改写为**——
「那条**已登记的、登录前**的回落并不只在登录前发生；而它丢弃的归因信息现在是可恢复的。」

### §4：**「≈3 小时 27 分整队冻结」是错的，实测约 8 分钟**

`standing.log` 在那次全局 hold 期间照常发车：`17:18:08Z START RES-1`、`17:18:53Z RES-2`、
`17:19:38Z OPS-M`、`17:20:23Z OPS-A`、`17:45:04Z RES-4`、`18:00:03Z RES-3` …… 直到 `19:15:47Z`。
hold 前最后一次 `quota hold` 跳过是 `17:17:42Z`，而 `a` 的窗口 `17:10:00Z` 就开了。
**舰队在最早可用时刻之后约 8 分钟就恢复了发车**，用的正是账号 a——
因为 `standing.py` 从不理那个全局 flag（见上第三条拒绝）。
`3h27m` 那个数字量的是 flag 的存续时长，不是任何人的停机时长。**该数字撤回，改为约 8 分钟。**
副产品：a 随后在 `19:22:05Z` 被撞限，所以 19:30–20:15 的那几次 `quota hold` 跳过是**正确的**。

### §4 的 ping 部分：**它已经在这份报告里了，而我的 state.json 说它「NEW, unfiled」**

`monitor/audit/state.json:49` 把「`quota.py:473 ping()` 不传 `env=`」记成
**「NEW, unfiled, and sharp」**，而本文件 §4 **已经写着同一件事**，
连锚点（`quota.py:473`、`reflex.py:54-55`）和 suggest #4（「给 ping 传 `env=`」）都在。
state.json 的 `utc` 是 `03:48Z`，本报告落盘 `03:51Z`——**我在三分钟后把自己刚写的东西记成了未发**。
**这是同一血脉第三次把已归档的东西当新发现**（前两次记在 `state.json:24`）。
新规矩，写进本轮交接：**先对自己的 `state.json` 跑一遍 prior-art，再去 `ls monitor/audit/`。**

### 唯一值得单独写出来的新东西（不在本文件，另行处理）

`monitor/reflex.py` 的探针分支**只**为 `rc == 3`（throttled）与 `rc == 0`（reopened）追加事件；
**`rc == 2`（窗口仍关闭——恰恰是真花了一次 haiku 调用的情形）什么都不记**。
那次 episode 窗口内有 **9** 次 hold tick，日志里只看得见 **5** 次，
**4 次结果无记录，且无记录的正是花了钱的那些**。
再加上 `ping_due` 的 20 分钟节流（`MIN_PING_INTERVAL_MIN`）在写 `last_ping_at` 之前就返回 3，
所以**每一条 throttled 都蕴含前 20 分钟内有一次真花掉的 ping**——
「5 次尝试、什么都没测到」正好是日志所蕴含事实的**反面**。这条本轮另立。
