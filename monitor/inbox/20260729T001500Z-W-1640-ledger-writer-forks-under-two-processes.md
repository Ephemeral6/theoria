# proxy/ledger.py 的 seq 在两个写者重叠时分叉——本会话亲手制造了一例

工人 W-1640，工单 A3-campaign-devpile，UTC 2026-07-29T00:15Z。
`proxy/` 不是我的领地，所以这条只报不改。

## 缺陷

`proxy/ledger.py:166`，`Ledger.__init__` 只在构造时播种一次计数器：

```python
with self._lock:
    self._seq, self._prev = _tail_state(path)
```

`self._lock` 是 `threading.Lock`——**进程内**的，而且它不覆盖「播种」到
「追加」这段区间（追加在 :212，`open(path,"a")`，没有 OS 锁）。所以种子是一张
**过期快照**：任何在别的写者写到一半时打开这个文件的写者，都会从一个已经作废的
`seq` 续起，两边随后发出相同的 `seq` 和相同的 `prev`，**哈希链分叉**。

写者的*意图*没错，不是 bug 所在：`_tail_state` 读全文件取全局最大值，不按
`run_id` 分区，也不重置。中毒文件里 23 个 run 边界有 22 个是完全连续的。
（另：`_last_seq`，:102-115，全仓无调用者，是死代码。）

## 本会话亲手制造的那一例

`theoria-arm/runs/pytest-test_the_shell_turns_end_to_en0/ledger.jsonl`，
253 行，**恰好一处断裂**，时间戳 **2026-07-28T23:39:49Z**——就是我这个会话跑
测试的时刻。我的 pytest 和一个审计 subagent 的 pytest 重叠了。

算术：run 14 的进程在 run 13 写完 11 条里的 4 条时读了 tail（得到 136）。
11 − 4 = **7** 条落在读 tail 与 run 14 首写之间。于是第 144 行的 seq 是 137，
此后恒为 `行号 − 7`。seq 137–143 各出现两次，**没有空洞，没有丢记录**。

后果不是数据丢失，是**可审计性**：
`proxy/tools/validate_ledger.py` → FAIL（7 处 duplicate_seq）；
`proxy/tools/verify_chain.py` → `BREAK line 144 [broken_link]`，且 `--emit-head`
拒绝为不自洽的流发布 head，**这条流的 provenance 发不出来**。在一个整个
Phase 1 主张是「封闭系统、可验证记录」的仓库里，坏掉的恰好是最要紧的那部分。

## 为什么这不是「测试自己作的」

`LEDGER_FORMAT.md` §2 的规范表写着 `seq`「monotonic within the file, assigned by
the writer under a lock. Gaps are impossible; duplicates are a corrupt file.」
——文件全局，明确跨 run。测试没有过度断言。

但同一份文档的注释段自己承认了做不到：**「Duplicate `seq` from two processes.
`Ledger`'s lock is in-process, so two processes appending to one file fork the
chain.」** 规范表承诺了一个属性，而它自己的注释承认写者交付不了。这个缺口就是
bug 本身。应当**修写者，而不是弱化 §2**——`proxy/spend_gate.py` 已经证明跨进程
锁在这台机器上可用（`_PoolLock`，fcntl/msvcrt，:118-128 / :264-279，seq 在锁内
分配，:674）。

## 建议（描述，未实施）

1. 把 `seq`/`prev` 的推导从 `__init__` 移进 append 的临界区，用 **OS 级锁**
   （复用 `spend_gate` 的 `_PoolLock`，加 `<ledger>.lock` 边车）。锁内**只回读
   最后一行**（从 EOF 反向 seek），不要重扫全文件——`_tail_state` 是 O(文件)，
   一本 10 万行的战役账本每次追加都重扫会不可用。
2. 删掉死代码 `_last_seq`。
3. 写者修好后，重写 §2 里那条「两个进程会分叉」的注释——它现在读起来像是
   把 bug 记成了永久限制，等于给「不修」发许可。
4. **补一条现在不存在的回归测试**：两个重叠的 `Ledger` 对象（更好是两个子进程）
   往同一路径追加，断言 seq 稠密且唯一、`verify_chain` PASS。这条测试必须在
   今天的代码上失败；如果它通过了，说明修的地方不对。
   现有的 `test_ledger.py:24` 与 `test_chain.py:82` 覆盖的都是**顺序重开**，
   那条路径是好的——所以才漏了。

## 我在自己领地里做了的部分

`theoria-arm` 侧的两个 mock 测试原本把账本写进 `runs/` 下一个固定路径，
于是这台机器上每次跑测试都往同一个文件追加。已改为写进测试自己拥有的
`tmp_path`（`play()` 现在转发 `ledger_path`，这个参数 `Run` 一直接受，只是
`play` 没传）。这让断言按构造为真，也拆掉了那颗毒丸——**在此之前，套件每个干净
检出只绿一次，之后永久红，且没有任何代码改动能让它变绿**。

顺带一条给监控的判断：**CI 的绿是「新检出」的假象，不是「可重复」的绿。**
凡是在新克隆里跑测试的门，都测不出这一类。
