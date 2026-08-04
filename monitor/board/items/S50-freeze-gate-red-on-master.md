priority: 1
cell: S50
territory: freeze
deps: none

# S50-freeze-gate-red-on-master · 冻结门在 master 上自红，全队被它挡住

`bash freeze/verify.sh` 在 master 上 **3 项失败**（2026-08-02 实测；
`monitor/ci/CONFLICT-origin_master.md` 是闸门旗）。后果是结构性的：
ci_merge 对触 freeze 的分支一律拒合——s45 已被明判"无新增失败、非其之过、
被 master 挡住"。红着的每一小时，freeze 队列全部停摆。

三项红，各自的病与药：

1. **[12] MANIFEST.json 与树漂移** —— register #13/#14 越表裁决与 A18 后
   的新 tracked run 落地后，冻结伴生品没再生。按检查自己的话做：
   `regenerate and read the diff`——先读 diff 确认每处漂移都有对应的
   已落地事实，再提交再生成物。另注意 inbox 里 W-9204 的
   `20260802T085557Z-...-freeze-manifest-will-not-hash-dsl-grammar-v0-4.md`
   ——若 v0.4 哈希缺口属实，本件一并裁掉或立新件说明。
2. **BUDGET_TABLE.{json,md} 不再从账本复算** —— 移动的 sections:
   balance / pool / tracked_theoria / verdict。**余额真的动了**
   （register #14 已入账、pool 已透支 -35.17 对 214.9 天花板，[20] 号
   检查自己就 PASS 在"公布负余额并 hold 项目 [12]"上）——所以这不是
   改表凑数，是把表再生成到与账本一致，diff 里的每个数都要能指到
   账本行。**排序注意**：`origin/agent/m-1-money-single-truth`（monitor
   领地的钱账单一真源）正在待合，它动 monitor/money.json 与登记簿
   测试——若它先落地，BUDGET_TABLE 复算以它为准源重跑一遍再提交。
3. **[18] 16 处工件记录了机器路径而无豁免** —— 逐条看：是新 run 落地
   带进来的就补 dated exemption（豁免要带日期与理由，不是清单里加行
   完事）；是生成器又开始写绝对路径就修生成器。M-1 的 inbox 件
   `20260802T1240Z-...-9-2-cannot-be-cleared-a-one-token-tautology-passes.md`
   指出某个检查存在一字通过的同义反复——若涉及本门，修判据本身并加
   负样本。

验收：master 上 `bash freeze/verify.sh` 全绿（跑两遍，第二遍必须还绿——
防再生成物自身不定）；每处 diff 在 RUN_STATE 有一句对应事实；随后
ci_merge 重跑放行 s45（不必你做，monitor 盯）。零花费，纯离线。
