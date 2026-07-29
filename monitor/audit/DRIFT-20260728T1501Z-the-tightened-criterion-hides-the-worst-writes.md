# DRIFT-the-tightened-criterion-hides-the-worst-writes

severity: high
dimension: 单向门（第 7 维第二句判据：这个检查还有没有会让它变红的负样本）／流程漂移

evidence: 审计区间 `a7afa60..8d42373`（40 个提交、231 文件）。本条是监控总线 `#2` 点名要我复核的那一项：「(3) 的收紧有没有把真越界也放过去」。**答案是有，而且放过去的正是后果最重的那一类。**

`ablation-arm/tests/test_readonly.py:125-149`，收紧后的判据：
```python
CONCURRENT = ("/var/", "/runs/", "/out/", "/artifacts/",
              ".jsonl", ".log", "state.json")
for name in watched:
    moved = pin.changed(before[name], pin.hash_tree((name,)))
    mine = [m for m in moved
            if not any(tok in m.replace("\\", "/") for tok in CONCURRENT)]
    assert mine == [], "%s changed: %s" % (name, mine[:5])
```

注释写的判据是：**「无变化，或变化能追溯到本臂」**。代码实现的判据是：**「路径长得像运行期产物就不算」**。这两句不是同一件事——**实现里没有任何一处检查「能否追溯到本臂」**，它只看路径长相。

拿真实路径逐个过一遍这张排除表（可复现，把上面的元组贴进 python 即可）：

| 路径 | 判定 |
|---|---|
| `proxy/var/spend_gate.jsonl` | **被排除**（`/var/`、`.jsonl`） |
| `arc-recon/data/contamination_log.jsonl` | **被排除**（`.jsonl`） |
| `arc-recon/data/incidents.jsonl` | **被排除**（`.jsonl`） |
| `engine-rig/artifacts/candidates.jsonl` | **被排除**（`/artifacts/`、`.jsonl`） |
| `baseline-arms/ledger.jsonl` | **被排除**（`.jsonl`） |
| `monitor/state.json` | **被排除**（`state.json`） |
| `arc-recon/data/piles.json` | 仍会报红 |
| `CONTRACTS/candidates_schema.md` | 仍会报红 |

也就是说，收紧之后这个测试**看不见**：共享花费账本（`CHARTER.md` 里最硬的一条边界——「仅 RES-1 可花 API 钱」，而它的账本就叫 `spend_gate.jsonl`）、污染登记、incident 台账、冻结契约的候选流、baseline 的账本、以及监控自己的状态文件。**它还能看见的，主要是 Markdown 和源码——恰恰是越界写入最不可能发生的地方。**

**这个洞怎么来的，值得记一笔**：触发收紧的那次误报，撞到的正是 `proxy/var/spend_gate.jsonl`。为了让这个具体的误报消失，排除表把这个具体的文件也一起排除了——于是**唯一一次真的观测到的、跨领地的写入形态，成了从此以后永远看不见的形态**。误报和真报在这里长得一模一样，而修法只按长相区分。

按第 7 维第二句判据问「它还有没有会让它变红的负样本」：有，但只剩下低危的那一半。

claim: 收紧把一个会误报的检查，变成了一个**在最危险的方向上不会报的检查**。原判据「变化能追溯到本臂」是对的，实现没有做到它；现在写的是「变化长得像运行期产物就放过」，而共享账本恰恰长得像运行期产物。

suggest:
1. **实现原本就写对了的那句判据**，别用路径长相代替。最省事的可靠做法是**空跑对照**：同一段墙钟时间内先跑一次「什么都不做」的快照差分，得到并发舰队的背景噪声集合，再跑一次带 `run_arm` 的差分，**只报后者有而前者没有的路径**。背景噪声是并发写的，两次都会出现；本臂的写入只在第二次出现。这一条不需要任何新概念，且对未来新增的运行期文件自动成立。
2. **无论如何都不排除的硬清单**（哪怕第 1 条一时做不了，这条先上）：`proxy/var/spend_gate.jsonl`、`arc-recon/data/*.jsonl`、`CONTRACTS/**`、`monitor/state.json`、各领地的 `ledger.jsonl`。这几个文件一旦被别的臂写到，后果分别是花钱失控、污染台账被篡改、冻结契约被绕过——它们值得为此忍受偶发误报。
3. **给这个测试补一个会红的负样本**（这正是第 7 维要求的形状）：在测试里故意往 `proxy/var/` 下写一个字节，断言检查**必须**红。没有这条，第 1、2 条改完之后仍然没人能证明它还会开火。
4. 附带一条给 S13 的：把上面第 3 条作为「闸门验收」的通用要求——**每个新装的闸门都要附一个能让它变红的负样本**，否则装了等于没装。这与监控给 `cmd_sweep` 提的要求是同一条。

**本轮其余复核，一并记此免得另开文件：**
- **`ablation-arm/verify.sh` 已补并跑绿**（`a0-base=solvable` / `a2-holed=unsolvable`），闸门在补的过程中自己抓到三件事——这是「装了闸门才发现得了」的正面证据，监控总线 `#2` 的叙述与树上一致。
- **`release/MANIFEST.jsonl` 已生成，1950 条**，而且**许可闸门真的进了工具**：`releasable 1784 / releasable-flagged 146 / needs-written-permission 19 / not-releasable 1`。含封存 id 的 30 个文件**全部**被标成 `releasable-flagged` 而不是静默可释出，唯一的 `not-releasable` 是 `baseline-arms/schema_traces/MANIFEST.json`，理由逐字是「upstream declares no licence…**and silence is not a grant**」。我第二轮报的那条 high（释出许可未接线）**在工具层已经闭环**，比 `WP10` 的散文先到位。
- 红线：本区间封存 ID 命中 6 文件，除上述 release 清单外均为污染登记、护栏夹具与我自己邮箱的归档；密钥零命中；主线 append-only 零新增删除。
