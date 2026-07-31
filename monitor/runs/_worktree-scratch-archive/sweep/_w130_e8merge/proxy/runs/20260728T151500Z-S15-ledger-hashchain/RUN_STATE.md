# S15 · 账本哈希链 —— 运行状态

RES-4，2026-07-28。分支 `agent/s15-ledger-hashchain`，base `f715c5b`。

## 做了什么

按 D-024 已裁决的方案实施（**没有重新设计**——方案在
`monitor/inbox/archive/20260728T2200Z-proxy-ledger-hash-chain.md` 里已经写死，
本任务是施工）：

1. `canon.py` —— `prev` 进 `ENVELOPE`。落在信封里有两个后果，都是要的：
   写入方独占它（调用方给 `prev` 会被 `NonCanonicalField` 拒收，否则链在带内可伪造），
   且它是**可选**字段，所以 `v` 保持 `1.0`——§8 升版的条件是「含义改变」或
   「新增必填字段」，可选字段两者都不是。
2. `ledger.py` —— `line_hash()` + `_tail_state()`；`append` 在**分配 `seq` 的同一把锁内**
   写 `prev`，两者因此不可能对顺序有分歧。文件第一条 `prev: null`
   （「链的起点」与「忘了写链」是两个不同的断言，显式区分）。
3. `proxy/tools/verify_chain.py` —— 逐行按**字节**校验 + 计算链头。
4. `proxy/tests/test_chain.py` —— 19 条，每条都真的动一次文件再要求变红。
5. `runner.py` —— 每个 run 记录里发布 `ledger_head`。

## 两条设计上的选择，及理由

**哈希的是磁盘上的字节，不是重新序列化的记录。** 重算式校验实际检查的是
「今天的 `canonical()` 与写文件那天的是否一致」——那个函数哪天改了行为，
历史上所有账本会同时变红，于是所有人学会忽略这个警报。按字节问的是唯一值得问的
问题：这些还是当初写下的字节吗。

**链头的 `verdict` 与 hash 一起发布。** 给一个自己都验不过的流发布链头，等于
给什么都没做见证；而「unchained」日后绝不能被读成「链已验证」。

## 实测（不是单测，是真跑）

`python -m proxy.runner --mock` 跑了一局完整的（28 步 / 3 关），账本 61 条：

```
proxy/var/ledger.jsonl: PASS
  lines 61  chained 61  unchained 0
  head  sha256:eea1574090eadd8e67e392f0beb02c23f0a91e778aa788e671bfeed175260d2a  last_seq 61
```

run 记录里发布的头与之一致，`verdict: PASS`。

然后拿真账本的副本改**一个数字**（第 3 行 `"score":0` → `"score":3`，
正是「安静的伪造」该有的样子）：

```
BREAK line 4 [broken_link] prev is 'sha256:ddf462e3…'; line 3 hashes to 'sha256:90f4de9c…'
EXIT=1
```

**这里有一件值得单独记下来的事：这次篡改后，链头 `eea15740…` 仍然与发布的头相同。**
因为改的是中间一行，最后一行的字节没动。也就是说 `--expect-head` 单独用**抓不到**
这次篡改，抓到它的是逐行链走查；反过来，整份重写并重算全链的伪造，链走查会给
PASS，只有发布在外的链头抓得到。**两个机制各自漏掉对方覆盖的那一半，必须都在。**
`test_rewriting_the_whole_chain_is_NOT_caught_without_a_published_head` 把后半句
钉成了测试，免得日后有人把这个性质说大。

## 交付前自查抓到的一处「白干」

第一版把链头写进 `runs/<run_id>.json` 就宣称「已发布」。**它没有发布。**
`runs_dir` 默认在 `proxy/var/` 下，而 `proxy/.gitignore` 忽略 `var/`——这条忽略
本身是对的（那是运行时产物）。于是链头被写进了**伪造者同样能随手改的地方**，
整套「篡改可察觉」的论证实际买到零，而外观上完整。

值得记的是它穿过了几道：写代码时没发现、19 条测试没发现、`LEDGER_FORMAT.md`
新写的那一节没发现、`DECISIONS.md` D-029 白纸黑字写着「随分支提交进 git」也没发现。
拆穿它的是对着那行代码写的路径跑了一条 `git check-ignore`。

**这属于我这条赛道的默认怀疑对象，而且是一个新形态**：不是「机制没装」，是
**「机制装了，但装在一个不起作用的位置」**；它同样不报错，同样往令人安心的方向失败。
已建议把这一类补进 S17 的失败分类学。

改法：发布这件事现在有明确的执行者，两个方向各一个——
`play()` 返回 record，由**臂**把 `ledger_head` 抬进自己 tracked 的
`runs/<slug>/MANIFEST.json`；臂之外的操作者用
`python -m proxy.tools.verify_chain <ledger> --emit-head <被跟踪的路径>`，
且**它拒绝为任何非 PASS 的流写头**——给验不过的文件发链头比不发更糟，因为看起来像发了。
`test_the_runners_default_head_location_is_gitignored` 把陷阱本身钉住：
哪天有人把 `var/` 挪出忽略名单，这条测试会逼他重新想一遍，而不是让幻觉悄悄恢复。

## 诚实的边界（D-024 原文，未被本次工作改变）

* **发布之前的伪造照样成立。** 得到的性质精确地是「链头发布之后可察觉篡改」，
  不是「记录被认证」。
* **没有任何本地手段能证明帧来自 ARC。** 只有 API 签名的回执可以，而 API 不提供。

因此收口说法仍是：**账本完整、自洽、臂写不了它——但操作者可以**，
现在加上一句：**且操作者事后的改动会在链头发布之后留下痕迹。**

## 测试

`cd proxy && python -m pytest -q` → **278 通过**（新增 19）。
`test_ledger_has_no_rewrite_path` 仍然绿：`ledger.py` 里 `'"w"'` 出现 0 次。

## 未做（交代清楚）

* `validate_ledger.py` 尚未加链检查项；
* 冻结打分器 `arc_v1` 尚未加「链」检查项与其伪造对照组（D-014 要求每个检查配一个
  必须触发的负对照）；
* 分片合并破链（提案 §2.4）与 lifted 流 `chain.enabled=false`（§2.5）尚未落到
  `upgrade_ledger.py`。

这三项都在提案 §5 的工作清单里，属于同一条线的后续，不影响本次交付的性质。
