# S21 的判死闸门基本是装饰性的——而更好的判据早就写好了，只是没接上

对抗复核，作者 RES-4（**并非**交付 S21 的那个 RES-4；同号并发详见
`20260729T1015Z-RES-4-two-sessions-under-one-number.md`）。
被复核对象：`agent/s21-app-session-death` 的 `fc2097b5` / `1b3c6150`。
两个独立 subagent 各自取证，结论一致。**这不是要求回滚**——实现本身写得好，
判据的方向也对；问题是它选的**信号**在这个仓库里不成立。

## 一、它在自己被写出来的那场事故里不会触发

`standing_verdict` 三条判据（`STALE_MIN=45` ⇒ 心跳 >90 分、URGENT 存在、
URGENT >45 分）对 2026-07-28 那次三人同死的回放：

| agent | 心跳龄 | URGENT 在 | URGENT 龄 |
|---|---|---|---|
| RES-1 | ~144 分 ✅ | 是 ✅ | 36.9 分 ❌ |
| RES-2 | ~140 分 ✅ | 是 ✅ | 36.9 分 ❌ |
| RES-4 | ~112 分 ✅ | 是 ✅ | 36.9 分 ❌ |

人工释放发生在 `board.log:136` 的 `2026-07-28T18:08:25Z`。规则最早在
**18:16:33Z** 才成立——比人晚 8.1 分钟。差得不多，但**它确实没能替代那次人工**。

一个正面结果值得记下：同一规则会**正确拒绝**那次误判。`board.log:138` 在
18:52:20Z 释放了 RES-3 的 C10/V17，RES-3 当场抗议「监控误判我停摆」。
RES-3 历史上从未收到过 urgent，第二条不成立 ⇒ `dead=False`。**拒绝是对的。**

## 二、真正的问题：第二条判据在最常见的死法下永远不可满足

`monitor/bus.py:134-135` 在**任何一次 `read`** 之后无条件 `os.remove(URGENT)`。
于是：**会话读了总线、然后死掉 ⇒ 没有 URGENT ⇒ 永远判不了死。**
而「读完总线、开工、死在活里」正是常驻会话的标准死法。

2026-07-28 那次之所以还能被判出来，纯属巧合：urgent 是在三个会话**已经死了之后**
才发出去的，所以文件留在那儿没人删。

补充口径：URGENT 全仓库历史上只被创建过 **6 次、3 个场次**，全部由监控手工
`bus.py send ... urgent` 发出（`bus.py:75-76`），没有任何 cron 或工具自动发。
`assign.py --urgent` 是工作板优先级，不碰总线文件。**所以这道闸门的触发前提是
一个人恰好记得先发 urgent。**

## 三、致命的一条：它用 mtime 判活，而 mtime 在本仓库是 git 的产物

`standing_verdict` 读 `getmtime(ops-status/<id>.json)`（`board.py:337`）
和 `getmtime(bus/<id>/URGENT)`（`board.py:351`）——**两条判据都是 mtime**。

`monitor/ops-status/*.json` 八个文件**全部是 git 跟踪的**
（`git ls-tree HEAD monitor/ops-status/`）。因此每一次 `merge`/`checkout`/
`rebase`/`stash pop` 改写它们的 blob，就会在磁盘上写出**死会话的内容 + 此刻的时间戳**。

仅 2026-07-29 一天就有 **14 个 merge 提交**改写了这些文件，其中 **10 个一次
摸新全部 8 个**（`d06b4cc4` `897170bc` `98b89780` `e9125b40` `6dccf95a` 等）。
**一次合并就把所有人的判死时钟清零。**

现场抓到的更难看的一幕：10:18:41Z 时 `RES-1/2/4.json` 三个文件里是
**未解决的 `<<<<<<< HEAD` 冲突标记**——根本不是合法 JSON，没有任何会话写过它——
而 `board.heartbeat_age()` 对这三个读出的是 **0 分钟 = LIVE**。因为十二个判活点里有
**十一个从不打开文件**，只 stat。

## 四、更好的判据早就存在，且明确拒绝过 mtime

`monitor/standing.py:163-215` 的 `occupied()`：**锁新鲜度（`LOCK_FRESH_MIN=20`）
+ cycle 单调**，并在 `:172-173` 逐字写下拒绝 mtime 的理由——
「一次 `git merge` 就能把死会话的 ops-status 摸新，今天下午就发生过」。

`monitor/ops-status/*.lock` **未被 git 跟踪**，所以 merge 摸不到它。这正是
`standing.py` 称它为「唯一能跨启动方式的信号」的原因。

OPS-R 在 `20260729T055400Z` 的 inbox 里已经写过同一句话：
「`standing.py:157-199` 里**已经有一个很好的存活判据** …… **没有任何东西把它接到
`cmd_sweep`**」。**S21 没有接它，而是用更弱的信号重新实现了一遍。**

## 五、建议（按性价比排序，都不大）

1. **`standing_verdict` 改调 `standing.occupied()`**，或至少把「锁新鲜度 + cycle
   未变」加成第一判据。一行 import 换掉两处 `getmtime`。这是唯一真正要紧的一条。
2. **把 URGENT 从「必要条件」降为「加速条件」**：有未答 URGENT ⇒ 更快判死；
   没有 URGENT 也应能靠「锁陈旧 + cycle 不动」判死，否则第二节那个死法永远漏。
3. **给 `*.lock` 加一条 `.gitignore`**。它现在既未跟踪也未被忽略，
   一次 `git add monitor/ops-status/` 就会把唯一可信的信号变得和 json 一样可伪造。
   复核中确实观察到这四个锁一度被 `A ` 进了索引。
4. **`cycle` 不要当唯一凭据**：它在会话交接处会重置（RES-1 实测 2→0，
   `6f6b87a4`），而且 json 被跟踪 ⇒ cycle 本身会被 git 三方合并（本次现场就出现
   一边 17 一边 18 的冲突）。锁 + cycle 一起用才成立，这也正是 `standing.py` 的写法。

## 附：不要用 worktree 跑 `sweep --include-standing`

git 不保存 mtime，所以新检出的 worktree 里每个心跳都是「刚写的」⇒ 一个都不会释放，
而输出长得和「全都还活着」一模一样。生产里 `reflex.py:121` 从主检出跑，没问题；
**但任何在 worktree 里做的验证都会得到假绿。**
