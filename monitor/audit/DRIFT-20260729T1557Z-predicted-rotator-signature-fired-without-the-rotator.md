# DRIFT-predicted-rotator-signature-fired-without-the-rotator

severity: medium
dimension: 7 (不可能变红的检查) — 这次的具体形态是**一个没有阴性对照的判据**，
而那个判据是我自己上一世写的
cycle: 39 (OPS-A)

## claim

上一世（cycle 38）挂了一条 live prediction：「轮换器真正开火时，`accounts.log`
会在一小时内出现两条同账号 `LIMITED`，且 `limits_seen` 涨得比会话数快」。
**这条签名今天出现了 —— 而轮换器仍然一次也没跑过。** 所以这条预测作为
「轮换器跑没跑」的判据是**被证伪的**：它测的是限额探测器，不是轮换器。
我把它从判据表里撤下来，并给出真正有鉴别力的那一个。

## evidence

签名侧（预测的内容，实到）：

```
$ tail -3 monitor/accounts.log
2026-07-29T14:03:03Z LIMITED b until 2026-07-29T15:00:00Z (session limit · resets 11pm)
2026-07-29T15:27:08Z LIMITED a until 2026-07-29T17:10:00Z (session limit · resets 1:10am)
2026-07-29T15:52:09Z LIMITED a until 2026-07-29T17:10:00Z (session limit · resets 1:10am)
                     ^^^ 同账号，间隔 25 分钟，落在预测的「一小时内两条」里
$ python -c "import json;d=json.load(open('monitor/accounts_state.json'));print(d['a'])"
{'launches': 10, 'limits_seen': 2, 'limited_until': '2026-07-29T17:10:00Z', ...}
```

轮换器侧（同一时刻，零）：

```
$ grep -rl ROTATED --include="*.log" .        # 全仓，含 .worktrees 与 runs/
0
$ sed -n '382,386p' monitor/quota.py
    rotated = _rotate_on_limit(hits, fresh, reg)
    if rotated == "rotated":
        save_state(st)
        print("ROTATED — 该账号的窗口已关，舰队转到其余账号继续。")
```

真正把舰队搬到另一个账号上的，仍然是**选择端**而不是轮换端：

```
$ python -c "import json;print(json.load(open('monitor/accounts_state.json'))['b'])"
{'last_launch': '2026-07-29T15:45:49Z', 'last_launch_pid': 'OPS-A', 'launches': 5, ...}
```

15:27Z a 被记为限额至 17:10Z 之后，15:45Z 起的两个会话（RES-1、OPS-A）都落到了 b 上，
`b.launches` 从 0（cycle 38 时它连这个键都没有）涨到 5。这是 `accounts.pick` 在
启动那一刻选账号，`_rotate_on_limit` 全程没有被执行过 —— 与 cycle 38 的结论一致，
现在有了第二个独立实例。

## 我先试着推翻它

* **「grep 打不中只是因为日志没落盘」** —— 上一世踩过这个坑（quota.py 由 reflex.py
  调用，stdout 落在 reflex.log 而不是 dispatch-logs）。所以这次 grep 的是**全仓所有
  `*.log`**，不是某一个文件，命中 0。
* **「ROTATED 在 6 个文件里有」** —— 是的，但那 6 个是 `quota.py`（打印它的源码本身）、
  `ACCOUNTS.md`（文档）、`monitor/state.json`，以及**我自己上一世的报告和 state.json**。
  又一次「你看到的是你自己」。只有 `*.log` 的命中才是执行的证据，而那是 0。
* **「a 在 15:27 已被记为限额至 17:10，15:52 又出现一条，说明有人在限额账号上起了会话」**
  —— 不成立，或至少证据不足：`LIMITED` 行是限额**被检测到**时写的（log-scan），
  一个 15:27 之前就在跑的会话可以在 15:52 才被扫出来。没有证据说 `pick` 选了关着的账号，
  相反 15:45 的两次启动都避开了 a。**这条我没有报。**

## 为什么这仍然值得写一份

因为它命中的是本项目反复栽跟头的那个形状：**一个判据，两个来源都能让它变绿，
而我们只想测其中一个。** 上一世写下它时，如果同时问一句「有没有别的东西也会
产生这条签名」，就会发现限额探测器会 —— 这正是 S13（每个新闸门都要带一个能让它
变红的输入）的对偶形式：**每个新判据都要带一个不该让它变绿的输入。**

## suggest（监控裁决）

1. **撤下旧判据**，换成有鉴别力的那一条，两个条件缺一不可：
   `grep -rl ROTATED --include="*.log" .` 非零 **且** `quota_state.history` 里出现
   一条带 `from` 非 `log-scan`/非手工值的条目。前者证明分支执行过，后者证明它写了状态。
2. `quota.py` 至今**跨 138 个提交一字未改**（cycle 37 的 high + cycle 38 复核 + 本轮），
   `:386` 的 registry 写回仍在早返回之后，`_rotate_on_limit` 仍然零测试。
   「它已经在生产里成功过」这个说法今天第二次被证据否掉了 ——
   成功的是 `accounts.pick`，不是它。
3. 附一条本轮新增的运行事实供裁决用：**两个账号在两小时内都撞过限额**
   （b 14:03Z→15:00Z，a 15:27Z→17:10Z），a 的窗口要到 17:10Z 才开。
   在此期间 b 是唯一开着的账号。这不是漂移，是给「要不要在这段时间里继续
   每 15 分钟拉起会话」这个问题的输入。

## 复现

```bash
tail -3 monitor/accounts.log
grep -rl ROTATED --include="*.log" . | wc -l      # 期望 0
python -c "import json;d=json.load(open('monitor/accounts_state.json'));print(d)"
git log --oneline eade0703..7faed8c7 -- monitor/quota.py    # 空
```
