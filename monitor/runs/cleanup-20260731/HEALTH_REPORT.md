# 清理战役健康报告 · 2026-07-31

所有者指令：不推进度，先把既有研究成果全部理干净——该合并的合并、偏航从根修、
收官时整个项目处于健康状态。舰队全程暂停；主会话统一执行，子智能体只做侦察、
试合并与隔离实现，master 上每一笔变更由主会话把关。起点 `2fe98e7f`（快照），
终点见本目录 MANIFEST。

## 一、合并队列（起点：17 个冲突档案、24 条领先分支、31 次失败纪录的最长者）

| 处置 | 分支 |
|---|---|
| 合并（origin，14） | a3-campaign-devpile（50 提交，31 次失败全属监控门超时而非内容）、v6-v23、c13、c14、s4-e23-tiers、r4、p18-the-paper、s38、s39、s41、s40、s42、e8-ic3-scale、v5-battery-freeze（29 次失败后，冻结清单第 8 项落地） |
| 记录为严格被包含（3） | s4-freeze ⊂ s4-e23-tiers；r3 ⊂ r4；p18-onmaster 零新字节 |
| preserve/ 空间（7） | v22、p8、a2（迁至 a2_crosscheck/）、p24（当场修三缺陷）、v26（原地改写转为合规追加）、p12（选择性：数据与工具落地、被拒设计不落）、e3（适配移植，非机械合并） |
| 仅本地孤本（6） | e18、v25、v23、s43b 落地；s35a、opsm/m16 以证据关闭；全部先推 preserve/ 备份 |

跨组相互作用两起，均当场解决：c13 pagoda 读取器 × e8 IC3 证书（测试改正向义务）；
seal × e3 在 modelcall.py 的加法碰撞（并集）。

## 二、根修（偏航从根断）

1. **第四形态**：gen_pddl 按 (name,arity) 分派、拒绝显式化、末尾自检；A0 0/303 →
   196/299（103 为声明式拒绝）；books.py 绿灯看齐 PDDL；交接包重建（a0-cart 五形态
   全生成）；0/303 冻结为修复前记录，普查门改为算术一致性；ic3 跨轨契约验证后会签；
   论文五处措辞携带日期（审计戳按其自身机制降级并出具增量继任）。
2. **臂侧封印**：EnvProxy 子进程化（端口握手、父进程看门狗、关停端点）；父进程环境
   与 Run 对象图递归扫描均无钥匙；封存堆 21 局 id+词干运行时载入、入 prompt 即
   SealedPileBreach 致命；baseline-arms 记 GAP-5（退役臂、复飞前须同样拆分）。
3. **账目**：钱门例外登记簿补登 #3–#8（含 S1 战役 $50.39 与自报差额 $2.01 GAP-4）；
   CLAUDE.md 摘要标注（内容摘要 vs 文件哈希）、领地现实、契约表、584/27 实测数；
   上限表随真账升到 $7.00（战役与 e3 各自独立推得同值）。
4. **可见化与卫生**：battery 活体伴生产物 + verify 第 6 阶（陈旧/篡改/撤披露皆红）；
   仓库级位置门（16 件签名工件 + 92 个日期化 run 豁免；上线数分钟即抓到两起真问题）；
   S23 归档单一写者（AST 测试钉住）；写一次 run 记录被覆写的根因（replicate.py）关闭。

## 三、抢救（先于一切删除）

付费不可再生：P11 传输分片、E3 sk48（~$8.40）、P8 g50t（$7.09，提交快照原记
not_started/$0.00，已更正并由账本派生 cost_curve/turn_series 入图）、P12 账本
（含 3 个 tn36 付费格）。从未上任何 ref：papers/related-work、papers/case-studies、
A13 封存审计 +361 行修订、五条困在 worktree 私有总线里的消息。7 条孤本分支推
preserve/。清扫前"先拷后删"：3617 份自著文件入 monitor/runs/_worktree-scratch-archive/。

## 四、清扫

328 个 worktree 全部移除（.worktrees/ 归零、Temp 临时全清、锁死两枚强制解除），
约 73GB 回收；git worktree list 只剩主树。杂项（permtest、日志、散落 scratchpad）清除。

## 五、终验矩阵（全绿）

exam 6/6 · theoria-arm 套件 + 三段门 + 来源门 10/10（84 = 71 可对账 + 13 具名
不可对账）· engine-rig · proxy 414（须从 proxy/ 内起跑）· battery verify 六阶 ·
figures verify 全量（103 条账单曲线全上图）· freeze verify 0 败 · crosscheck GREEN ·
CONTRACTS 绿 · 位置门 clean · 污染审计绿 · 封存扫描零缓存 · monitor 套件全绿
（append-only 探针改具名提交赦免、冲突探针档案/活文件分治 + 战役七笔跨领地提交
具名赦免——新违例零容忍）。

## 六、如实残留（不是缺陷清单，是移交清单）

- freeze kit 仍未到冻结就绪（0/13 ready；campaign_freeze.json 缺席、⛔ 项开列）——
  Phase 4 准备工作，非清理范围。
- 看板剩余 10 项真实未做（S31 共享账本真臂记录、S32、S44×2、V2-V25、V26-fuzzlab、
  A16/A3-A17/A3-campaign-level2/A8 战役线）。
- release/enumerate 有一队 needs_human 待人裁分类。
- 三个主终点（U3/E2/判决题）的可清偿性问题原样保留——那是研究工作。
- 操作者若在 shell 里 export 了 ARC_API_KEY，父进程仍会继承（modelcall 的
  env.pop 作纵深防御）；worktree 内不可发起真跑（.env 只在主检出）。
- BUDGET_REPORT 的累计口径差异归 baseline-arms 领地订正（登记簿#对账附记）。
