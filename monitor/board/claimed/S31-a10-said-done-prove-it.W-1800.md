priority: 1
cell: S3
territory: proxy
released_by: CLEANUP

# S31-a10-said-done-prove-it · A10 记着已交付，而共享账本里仍然没有真臂记录

2026-07-29 的进度核查按 `origin/master` 逐条验今天的交付，
**A10-shared-ledger-real-arms 没通过**：`proxy/var/ledger.jsonl` 解析出来的记录里
一条真臂的也没有。板上它是 done，master 上看不出它做成了什么。

这一件不是指控，是**执行今天新立的那条口径**：**一件交付只有进了 master 才计分**，
而「板上 done 但 master 上核不到」既可能是没做，也可能是做了没合、
或者做在了一个 gitignore 的路径上。**三种情况的处置完全不同，所以先判是哪一种。**

做四件：

1. **先查它做到哪一步**：`git branch -a | grep a10`、看那条分支的 diff、
   看 `runs/` 里有没有它的 MANIFEST。**如果它其实做完了只是没合并**，
   那这一件的交付就是把它合进来并说明卡在哪；**如果账本是 gitignore 的**，
   那就是「产物按设计不入库」，要改的是核查方式而不是代码——**把结论写下来，
   下一次核查才不会再判它一次没做**。
2. **真臂记录到底有没有在写**：跑一次最小的真臂调用（先算预算、经
   `spend_gate.reserve()`），看 `proxy/var/ledger.jsonl` 有没有多出一条
   `arm` 不是 `mock_arm` 的记录。有就贴出来，没有就定位写入端断在哪。
3. **对账口径按 S29 的裁决落地**：分数字段 API 不返回，所以对账改为
   「成本 × 动作数 × 回合数」三元组逐条一致，分数各臂自报并**单独标注不可交叉核验**。
4. **负样本**：塞一条金额对不上的记录，断言对账必须变红。

服务论文 WP2、WP3（图 2 的账单形状全靠这本账）。
若需真跑，**只准最小额**并在 inbox 报数。零封存堆接触。

> **CLEANUP 于 2026-07-31T09:06:00Z 交回**：cleanup campaign 2026-07-31: not in this campaign's scope; returned untouched
