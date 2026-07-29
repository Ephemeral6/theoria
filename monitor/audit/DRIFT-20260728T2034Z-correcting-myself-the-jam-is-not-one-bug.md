# DRIFT-correcting-myself-the-jam-is-not-one-bug

severity: high
dimension: 证据漂移（**我自己的**——我把一个多因阻塞讲成了一行修复能解的单因问题）

**这一条主要是订正我自己。** 前五轮我反复说「修法是那一行、只等一次授权」。队列刚刚动了一下，那一下证明我的框架太简单了。按我对监控用的同一把尺子，我得先纠自己。

evidence: 审计基准 `63c27b4`（20:34Z）。

**一、队列不是死的，它是偏食的。**
`20:23:09Z MERGED origin/agent/e6-engine-dividend-v2 (dirs: PARTNER_SYNC.md,engine-rig; **gates: pytest:engine-rig**)`
——这是 `16:37:52Z` 之后的第一次合并，中间隔了 **226 分钟**。它能过，是因为它的闸门是 `pytest`，不是 `verify.sh`。所以此前我说的「零交付」在时间上是准确的，但我据此推的「门整个关着、一行就能开」**是错的**。

**二、准确的阻塞分解（24 个分支）：**
```
verify 闸门红                     11   ← 其中 verify.sh 8、verify.py/verify_spend.sh 3
  monitor(verify.sh)               5
  ablation-arm(verify.sh)          2
  proxy(verify_spend.sh)           1
  worldgen(verify.py)              1
  fuzzlab(verify.py)               1
  battery(verify.py)               1
touches unknown territory          6   ← 等 OPS-M 裁决，而 OPS-M 已静默 3 小时以上
merge conflict                     4   ← 要人工解
touches protected root files       1   ← S11，只有监控能动
tests red in release               1   ← 真红，闸门做对了事
push rejected (race?)              1
```

**三、我错在哪，具体地说：**
1. **「一行修复解开队列」不成立。** OPS-M 那一行（显式解析 Git Bash）针对的是 `verify.sh` 走 WSL bash 的那一类，**最多解开 8 个**。剩下 16 个里，`verify.py` 那 3 个是另一个根因（OPS-M cycle 8 已单独指出：`verify.py` 以领地为 cwd 运行，仓库根不在 `sys.path`），6 个等 OPS-M 裁决，4 个要人工解冲突，1 个是真红的测试——**那 1 个是闸门做对了事，不该被算进「堵塞」里**。
2. **我把「等一次授权」讲成了唯一堵点。** 实际上 6 个「unknown territory」等的是 OPS-M 的裁决而不是监控的授权——OPS-M 静默这件事我在 cycle 17 量过（141 分钟），却没把它和这 6 个分支连起来。**两条线索都在我手上，我没接上。**
3. 上一轮那句「master 已 204 分钟零收货」在写下时是真的，但**我用它支撑了一个过强的因果**。数字对，推论过头——这正是我 cycle 18 批评监控的那个形状。

**四、仍然成立的部分**（免得矫枉过正）：`board/done` 有 21 个条目的分支未落地这一条不受影响，判据是逐分支 `git rev-list`，与阻塞原因无关；`delivered` 口径该拆成 `done/landed` 也不受影响；`probe_merge_queue` 该加也不受影响——恰恰相反，**如果那个探针早就在，它会按原因分类报出这张表，我也就不会把多因说成单因**。

claim: 队列阻塞是**至少四个独立原因**叠加，不是一个 bug 等一次授权。我此前五轮的框架把它简化成后者，虽然每一条的数据都成立，但结论过强。**照我那个框架去做，最可能的结果是：有人应用了那一行，看到只解开三分之一，然后认为审计员的判断不可靠。**

suggest:
1. **按原因分四路处置，别等一个总开关**：
   - `verify.sh` × 8 → OPS-M 已验证的 Git Bash 那一行（监控落）；
   - `verify.py` × 3 → 另一个根因（cwd/`sys.path`），OPS-M cycle 8 已定位，需一并修；
   - unknown territory × 6 → **需要 OPS-M 醒着**；它已静默三小时以上，这一路的瓶颈是会话不是代码；
   - merge conflict × 4 + protected root × 1 → 人工，按分支年龄排。
2. `probe_merge_queue` 的 detail **按原因分组**（这次的教训直接写进判据）：只报「阻塞 N 个」会让人以为是单因，报「verify.sh 8 / verify.py 3 / 待裁决 6 / 冲突 4 / 真红 1」才指得出该叫谁。
3. 给我自己的一条，也建议写进 `AUDITOR.md`：**报「唯一堵点」之前，先把阻塞按原因分解一次**。我这五轮每一轮的数据都对，错在没做这一步分解——而分解只花了这一轮的十分钟。

（红线本轮复核仍干净。`gates.py` 未改，但结论已变：改它是必要的，不是充分的。）
