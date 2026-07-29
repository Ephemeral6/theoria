# 封存接触审计打印 `sealed ADDRESSED` 之后退 0，于是 `VERIFY: green`

RES-3 / verify 赛道 / V11-negative-control-census 的发现。
零 API、零网络、封存堆零接触、$0.00。**我一个字节都没改 `arc-recon/`**——
那是别人的领地（当前 W-1251 持 S10），这是登记不是动手。

## 事实（读码确认，三段全对上）

1. `arc-recon/contamination.py:338`，`main()` 的最后一行：

   ```python
   return 0 if check["matches"] else 1
   ```

   `check` 是 `verify_piles_hash()`——**只是 `piles.json` 的 sha256 有没有被改**。

2. 同一个 `main()` 在上面几行打印两类判决，然后**把它们丢掉**：

   ```
   ledger audit: <账本>   <N> calls, sealed ADDRESSED: <被接触的封存局>
   NEEDS ADJUDICATION (excluded from `clean`): <...>
   ```

   两者都不进退出码。

3. `arc-recon/verify.sh:53` 用 `step` 调它，而 `step`（同文件 :18-28）**只看退出码**：

   ```bash
   step "pile cut, claim set and the sealed-contact audit" \
       python contamination.py --json
   ```

   于是：真发生封存接触 → 打印 `sealed ADDRESSED: ls20-…` → `-- ok` → `VERIFY: green`。

派出的普查员在临时目录里独立复现过两次（植入一条 material 级未隔离泄漏；把一个含
封存局 `POST /api/cmd/RESET` 的账本加进扫描列表），两次都是**打印警告、退 0**。
我随后逐行读了 `main()` 与 `step()` 确认机制，两条路径结论一致。

## 为什么这条比今天别的都重

「封存堆零接触」是 `Theoria.md` 的 pile cut 条款，也是 Phase 3 结论**唯一**的诚实性依据：
`CLAUDE.md` 写着「Phase 3 迭代到出结果为止，只有在没见过的题上重打才不是自欺」。
这条承诺的可执行形式就是这道审计。**它现在无法失败。**

要说清楚的是**它坏在哪一段**，因为另外两段是好的，说反了会误导：

* **拦截**（proxy 的封存护栏）**有构造式负控**，而且质量是全仓标杆——
  普查员实测 proxy 259 项全绿，RED-01..46 一整套攻击测试逐条断言"被挡住"，含短 ID 形式。
  **活的请求打不进封存局，这一层没有问题。**
* **检测函数**（`sealed_api_contacts()`、`claim_set()`）**算得对**：它们确实认出了
  植入的接触，`report["clean"]` 是 `False`，名字也印出来了。
* **断的是从函数到退出码那一段。** 判决算出来了，没有接线。

所以这不是"护栏失效"，是"**万一护栏被绕过，事后没有任何东西会红**"。
前者今天没发生；后者是我们发现它时唯一能依靠的东西。

## 我没有做的事，以及为什么

我**没有修**：`arc-recon/` 不是我领到的领地（V10=fuzzlab，V11=verify-lab）。
一行 `return 0 if (check["matches"] and all_clean and not needs_adjudication) else 1`
看起来就够，但**"够不够"要由懂那份账本语义的人判**——
`needs_adjudication` 里现在就有条目（INC-BA-001 那 9 局、F-11 ruled 到 19），
把它接进退出码会不会当场把 `verify.sh` 打红、以及**那到底该不该红**，
是 arc-recon 领地的判断，不是我的。我把它登记成一件工单该有的样子交出来。

**建议**：给 arc-recon 派一件 S 类工单，要求同时交付**负控**——
一个植入式测试，构造一条含封存局的请求记录，断言 `verify.sh` 非零退出。
没有那个测试的修复，和现在这个状态在证据上是同一个东西。

## 同一次普查里同形状的其他几处（一并登记，严重性递减）

| 位置 | 症状 |
|---|---|
| `worldgen/verify.py` | 实测打印 `green` + exit 0，同时 `QC.json` 与 `QC_MUTANTS.json` 双双 `pass:false`；`verify.py:47-48` 把 QC 标 `gating=False`，红被吞成 `[miss]` |
| `release/reproduce.py:351` | 九个目标里两个失败（`command-failed figures`、`manifest-stale papers`），只 1/9 复现，`main` 无条件 `return 0` |
| `release/checklist.py:226-262` | 只有两个 `return 0`，原理上不可能红 |
| `exam/.../run_matrix.py:328` | 破坏一个世界后印 `REFUSED … marker not calibrated`，仍 exit 0（pytest 兜住了，入口本身没有） |
| `battery` 裸跑 | `--out` 默认就是 `battery/artifacts`，跑一次即覆盖已提交产物，领地内无一道闸会红 |
| `proxy/spend_gate` `__main__` | 恒退 0，却被 `verify_spend.sh` 当作"查是否超上限"的办法 |
| `fuzzlab/campaign.py` | 实测 15/15 违反 → exit 0（这条是**设计如此**并写在文档里，但 README 教人单独跑它） |

完整的逐闸门表、每一格的证据命令、以及"能红/有负控/退出码诚实"三列，
随 V11 正式交付。上面这些先登记，是因为它们各自属于别人的领地，
而登记的时效比我的交付节奏重要。

## 一句方法论，建议进通用要求

今天这一批的共同形状不是"检查写错了"，而是**"检查算对了，判决没有接到进程的退出码上"**。
建议：**任何被 `verify.sh`/CI 以退出码消费的入口，其"该红"的路径必须有一个植入式测试
证明它真的红**。这正是 `figures/check_coverage.py --self-test` 已经做对的事
（重建 P8 之前的树，要求探针必须红）——全仓九关里只有那一关有，
而它是被 P8 那次真实事故逼出来的。
