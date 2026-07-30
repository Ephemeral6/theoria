# S43 对抗性复核 — 一个专职 subagent 被派去推翻我自己的结论

验收第 4 条要求：「另派一个 subagent 专门试图证明『这三条保护其实还在，只是换了写法』——
推不翻才算数。源码字符串断言是脆的判据，本条目自己也要防这一点。」

复核者拿到的是**反方立场**：默认判「推翻」，只要找得到任何合理读法支持反命题。
它检验了七条反假设（换名换写法／搬到别的文件／被外层机制兜住／`check=True`
／归因搞错了提交／数量多算了／`merge:EXIT` 其实也没了）。

## 结论：六条一条也推不翻，但它推翻了我对第七条的**解释**

(a) sweep / (b) reap / (c) git 守卫 / (d) BOARD-QUERY-FAILED / (e) SUPPLY-UNKNOWN
/ (f) scan 守卫 —— **全部确认真的不在了**，且每一条都给了可执行判据
（源码行号 + 对应测试的实际报错）。它还确认部署中的 reflex.py 与 master 逐字节相同
（主检出 `git status --porcelain -- monitor/reflex.py` 为空），
所以「跑着的 reflex 和 master 上的不是一个」这条退路是关着的。

## 它推翻的东西（我的原始说法错了，以此为准）

**`merge:EXIT-` 不是「873d62ee 手下留情」，而是合并解决的副产品。**

873d62ee **也删了它**，就地删的，和其余六条一样。它今天还在，是因为合并提交
`7c1dd89b`（双亲 `873d62ee` + `1a86d67d`）在解决冲突时，
从另一边取回了被抽成函数的 `merge_events()`。
判据：`git merge-base --is-ancestor c8061d7b cd048b32` → **否**，
即 `merge_events` 那次抽取**根本不在 873d62ee 那条开发线上**；
`git show cd048b32:monitor/reflex.py | grep merge:EXIT` → 第 336 行，就地形式，没有函数。

**所以 873d62ee 删的是七条，不是六条。** 一条靠合并解决活了下来，不是靠意图。
这对读者是有意义的：**能看见的守卫数，不等于被攻击的守卫数。**

## 它提出的、我接受的另外两条修正

1. **(b) 和 (c) 我说轻了。** 873d62ee 不只是不读返回码，它把
   `reap = run(...)` / `reap.stdout` 改回了 `run(...).stdout`——
   状态对象在被读之前就被丢弃，**不是被忽略，是不可恢复**。
2. **(a)(d)(e) 是可观测性损失，不是控制流损失。** 说它们「行为上不在了」，
   对发出的事件为真，对做出的决定为假。**七条里只有 (c) 和 (f) 改变了循环做什么。**
   这一条已经写进新测试文件的 docstring，免得读者以为这里修了六个控制流 bug。

## 它提出的最强反驳（我认为不足以救原命题，但值得写下来）

**复活循环并不是只有 (c) 一道防线。** `reflex.py:331` 调 `dispatch.py --only`
时**没带 `--force`**，而 `dispatch.py:347` 自己会拒绝：
`if branch_taken(pid, branches) and not args.force`，其中 `branches` 来自
`git branch -a`（是 reflex 那条 `git branch -r --list` 的**超集**）。
reflex 只在 `"launched" in r.stdout` 时才计一次复活，
所以被 dispatch 挡下的那次不花钱、不加死亡计数、不占 45 秒 stagger。
再加上 `MAX_DEATHS = 3` 的终身上限——git 失败会产出一串免费的 no-op，
而不是一串付费会话。

**为什么这仍然救不了原命题**：`dispatch.py:49-52` 自己的 `git()` 助手
**同样丢掉返回码、同样裸返回 `.stdout`**。所以一次机器级的 git 故障会
在同一瞬间、朝同一个方向把两层一起弄瞎。第二道防线只挡得住
「只影响 reflex 那一次调用」的故障。

## 它顺手挖到的、比原条目更值钱的一条

**没有任何东西盯着 `reflex.log` 的新鲜度。**
`grep -rn "reflex.log" monitor/*.py` 只命中 `reflex.py` 自己；
而 `probe_standing`（`scan.py:1220-1230`）**恰恰**为 `standing.log` 做了这件事。
`probe_scheduled_tasks`（`scan.py:644-672`）只看任务是否已注册／已禁用，
**从不看上次运行时间或上次结果**。

配上 `\TheoriaReflex` 的 `MultipleInstances: IgnoreNew` 与
`ExecutionTimeLimit: PT72H`，**一个在 `rlog()` 之前死掉的 tick，最长可以隐形 72 小时。**
7 月 30 日那 131 分钟的静默正是这个机制，而它之所以只有 131 分钟，
纯粹是因为有人碰巧在看。

这条超出 S43 的范围，我按契约自供成了一件新条目（见 RUN_STATE「自供」一节），
没有夹带进本次交付。
