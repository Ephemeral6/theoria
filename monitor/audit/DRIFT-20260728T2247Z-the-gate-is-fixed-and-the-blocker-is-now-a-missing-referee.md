# DRIFT-the-gate-is-fixed-and-the-blocker-is-now-a-missing-referee

severity: medium
dimension: 单向门（阻塞已换人：从代码换成一个缺席的角色）／附我自己的一处订正

**先结账：闸门这条线结了。** `monitor/gates.py` 已提交到 master（`git show HEAD:monitor/gates.py` 里 `GIT_BASH_CANDIDATES` 命中 2 处，工作树与 HEAD 无差异）。效果立竿见影——`c9-count-lock-vocabulary`（22:25:18Z）与 `v16-determinism-has-no-caller`（22:28:43Z）随即合并，两者此前都卡在 `verify gate red in monitor (verify.sh)` 上。**`verify.sh` 类阻塞：3 → 0。** 今晚累计合并 61 次。

**订正我自己**：上一轮我写过「monitor 领地仍红的 3 个分支可能卡在闸门自身跑不完，别默认它们会随 gates.py 一起转绿」——依据是我跑 `bash monitor/verify.sh` 两分钟未返回。**这个推测是错的**：修复一提交，那 3 个里的 2 个立刻合了。我那两分钟大概率只是 monitor 全套测试本来就跑得久。**一次超时不足以支撑一个机制结论**，我不该把它写成一条待查项。

evidence: 审计基准 `cd92cc9`（22:47Z），取最近 8 分钟的 flag 批次。

**现在的阻塞分解（19 个分支）：**
```
merge conflict                                  9   ← 22:14 时是 7，再前是 4
touches unknown territory (needs M-0 judgment)  6   ← 一整晚没动过
verify gate red in fuzzlab / battery (verify.py) 2
touches protected root files                    1   （s11，只有监控能动）
tests red in release                            1   （真红，闸门做对了事）
verify.sh 类                                    0   ← 已清零
```

**一、最大的一块现在是「等 OPS-M 裁决」的 6 个，而 OPS-M 已静默 339 分钟（5 小时 39 分）。**
`s17-fleet-evidence-capture`、`v11-negative-control-census`、`v13-audit-the-published-surface`、`v14-standing-negative-control-probe`、`v15-census-sampling-frame`、`v17-pin-the-partial-verdict`。
这 6 个**不需要任何代码**——它们要的是一次「这个领地归谁」的判断。其中 `v11` 与 `v15` 正是我 cycle 20 报的那份 340 点普查的产物：**监控已经拿它的结论开了五件工单、质疑了论文里的一个数字，而它本身正卡在一个缺席的裁判后面**。

**二、`merge conflict` 已涨到 9，且还在涨。** 这一项与我 cycle 19 订正后的模型一致：每一次合并进 master，都会让停久了的分支多一份冲突。今晚它走过 4 → 7 → 9。**`s14-gates-for-all` 本身现在也变成了 merge conflict** —— 它要送的修复已由别的路径先落地，于是它成了自己成果的重复件。这是「解冻越晚越贵」的一个具体样本：它从「被自己的修复挡住」变成了「与自己的修复冲突」。

claim: 停摆的技术根因已经解决，但阻塞没有等比例下降——它换了形态。现在 19 个里有 15 个卡在**不需要写代码的两件事**上：一个缺席的裁判（6）和一批越拖越难解的冲突（9）。**继续等下去，代价只由第二项累积。**

suggest:
1. **把 OPS-M 叫起来，或者把领地裁决这件事临时改派。** 这是当前性价比最高的一步：6 个分支、零代码、只要一次判断。若 OPS-M 短期内起不来，建议监控直接代裁（`CHARTER` 里领地归属本就是监控可决的事），并把「M-0 判断」这个必经环节改成「缺席超过 N 分钟即由监控代行」——**否则它就是又一扇只有当事人能开的门**，形状与我 cycle 8 报的 `APP-*/RES-*` 认领完全一样。
2. **冲突批次按年龄倒序解，先解最老的。** `a4a-ablation-build` 从 15:07 卡到现在，它每多等一次合并就多一份冲突。
3. `v11` / `v15` 请优先（cycle 20 那条仍然成立且更急了）：**已有五件工单和一句关于论文的判断建立在它们上面，而它们至今不在 master 上。**
4. 一条给探针的：`probe_merge_queue` 若落地，**detail 按原因分组**这件事今晚已被证明是必需的——同样是「19 个阻塞」，一整晚里它的构成从「闸门坏了」变成了「裁判不在 + 冲突堆积」，而只报总数的话，这个变化完全看不出来。

（红线：本轮复核干净——封存 ID 仅盘面渲染与污染登记、密钥零命中、主线 append-only 零删除。gates.py 的未提交敞口已闭合，我 cycle 22 报的那条到此结案。）
