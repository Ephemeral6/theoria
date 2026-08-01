priority: 1
cell: A27
territory: theoria-arm
deps: none
spend: none

# A27-freeze-gate-reads-the-rewritable-half · 一次删除加一条离线命令，就能把战役冻结解冻

P-12 于 2026-07-31T18:30Z 把补丁连同复现步骤一起送进
`monitor/inbox/20260731T1830Z-P12-to-theoria-arm-freeze-gate-reads-only-the-
rewritable-half.md`，并且**没有碰臂的领地**。到 2026-08-01 为止
`theoria-arm/harness/freeze_gate.py` 一次提交都没有——这条 ask 至今无人认领。

洞是这样的：`harness/freeze_gate.assert_unfrozen()` 只打开
`arc-recon/data/campaign_freeze.json`，而那是冻结回路里**唯一可重写**的一半。
它旁边就是 `campaign_freeze_log.jsonl`，只追加。`init_freeze_from_runs` 拒绝
**覆盖**已存在的状态文件，却从不拒绝**创建**一个。于是：

```
rm arc-recon/data/campaign_freeze.json
cd arc-recon && python canary.py init-freeze
```

从 `canary_runs.jsonl` 重建出一份未冻结的状态，对此后写下的任何一次冻结毫无
记忆。`refresh_freeze` 花了一整段禁止绿色扫仓库出现的那种自愈形状，从另一扇门
走了进来。P-12 说 `arc-recon` 那一侧在他的分支上已经关掉了；臂这一侧的门还开着。

`Theoria.md:368` 要求冻结清单在**第一局之前**提交并哈希。一个能被一次删除
解冻的冻结，不是冻结。所以这件挂 p1：它不是新能力，是一条已经写下的纪律
今天实际上不成立。

验收：`assert_unfrozen()` 同时读只追加的那一半，两者不一致时**拒绝**并说出
不一致在哪；上面那两条命令的序列在测试里被逐字执行，且必须被拒绝。

负样本，三条：(1) 正常的、两半一致的冻结必须**通过**——一道只会说不的闸和
一道坏闸没有区别；(2) 只删状态文件、不重建，必须拒绝（缺席不等于未冻结）；
(3) 只追加日志缺失而状态文件在，也必须拒绝，而不是退回到「读得到什么就信什么」。

领地边界：本件只改 `theoria-arm/`。`arc-recon` 那一侧是 P-12 的，别去动；
若发现他的补丁与本侧口径冲突，走 `monitor/inbox/`，不要直接编辑。
