priority: 1
cell: V31
territory: papers
deps: none

# V31-papers-gate-red-on-master · 论文门在 master 上自红，v29/v30 被它挡住

`python papers/verify.py` 在 master 上 **4 项失败**（2026-08-04 实测）；
ci_merge 据此拒合一切触 papers 的分支，且明判被挡的
`agent/v29-one-proxy-validated-not-two`（论文措辞对齐 S32 裁决）与
`agent/v30-p18-hand-merge`（4075 行引文审计手合，12 次机械重试后的人工
成果）**均无新增失败、非其之过**。红一天，这两支的成果就悬空一天。

四项红与修法：

1. **case-studies/ 无 PAPER.md 且未注册 NOT_PAPERS** —— 二选一：是论文就
   补骨架 PAPER.md，不是就写进 NOT_PAPERS 登记（登记要一句理由，不是
   加行了事）。
2. **related-work/ 同上**。
3. **phase1-workshop/verify_paper.py 3/7 门红：C FIGDATA / E UNCITED /
   F BARE** —— 注意排序：被挡的 v29/v30 正是引文与措辞的实质修。**先做
   master 侧最小修**——只修到门能诚实过（缺的图数据补上或注明来源、
   无引文句补引或降级为观察、裸断言加限定），**不要在 master 上重做
   v29/v30 已做的活**；它们落地后如有重叠以分支版本为准。若某门在
   master 侧无法诚实修绿而其修正确实在被挡分支里，用 verify_paper 自身
   的豁免/待办机制（有则用，无则在 RUN_STATE 写明并在门里加带日期的
   已知红注记）——把门变绿的路径必须可辩护，不许降线。
4. **papers pytest 1 failed / 10 passed** —— 修红的那一个，别动其余。

验收：master 上 `python papers/verify.py` exit 0 且跑两遍皆绿；每处修
在 RUN_STATE 一句对应理由；随后 ci_merge 放行 v29/v30（monitor 盯，
不必你做）。零花费，纯离线。RES-2 若在场本件归它；generic 工人做的话
只修门与登记，**不写论文正文**（CHARTER 界线，W-9201 在 V29 上的先例）。
