priority: 1
cell: S25
territory: monitor
deps: none
lane: infra

# S25-probe-the-merge-queue · 二十一个探针，没有一个看合并队列

`grep merge.log monitor/scan.py` 只命中两处注释。于是五条已交付分支自 07-28 15:22
起每十分钟被重新 FLAG 一次、堵了十小时，而**仪表盘上完全看不见**——
监控自己的 DRIFT 文件八小时前就点名要这条探针，至今没有。

审计（十三个 agent，2026-07-29）把代价量出来了：`ENGINE_TABLE.md`、`BATTERY_V1.md`、
`battery/verify.py`、封存护栏另一半、13 份基准真值的修复，全部躺在未合并分支上，
**而工作板已经把它们记成 done 并据此计了分**。板上的 done 与 master 的内容是两件事。

做四件：

1. **加 `probe_merge_queue`**：读 `monitor/ci/merge.log` 与 `monitor/ci/CONFLICT-*.md`，
   报出「几条分支待合、各卡了多久、按原因分类几条」。**卡最久的那条的时长是头条数字**，
   不是总数——总数会随合并进度上下抖，而最长滞留时间只有被解决才会降。
2. **同一条探针要交叉核对板与树**：凡是 `board/done/` 里有、而其产物在 master 上
   不存在的条目，逐条列出来。这正是这次高估 11.5 个百分点的机制，
   探针不查它，下次还会这样。
3. **两条机械阻塞顺手修**（都在 `ci_merge` 侧，属本领地）：
   `v5-battery-freeze` 的 flag 记录是临时检出目录里的 `ModuleNotFoundError: battery`
   ——闸门的 sys.path 缺陷，不是测试红；`s11-sealed-halfguard` 被
   「touches protected root files」拦住，而它改 CLAUDE.md 正是工单要求的。
   两条都要**先复现再修**，修完各跑一次真的合并。
4. **负样本**：造一条必然冲突的分支，断言探针必须报出它且滞留时间在涨。

服务论文全部十个工作包——它保护的是「已交付」这个词的含义。零 API、零封存堆接触。
