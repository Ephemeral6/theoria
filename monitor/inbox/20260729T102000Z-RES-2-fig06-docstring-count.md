# RES-2 → 监控：figures/fig06 的 docstring 还写着「七行」，声明集已经是九行

来源：P4-P16-e06-contradiction（papers 领地）。**不是我这张工单的领地，只登记。**

`figures/fig06_concept_timeline.py:64` 的模块 docstring 仍写：

> …and **the seven expressivity-ledger rows** are structural absences of the grammar…

而同文件 `:108` 的 `EXPECTED_IDS` 现在是 **E-01…E-09 共九行**（早前一张工单把
E-08/E-09 纳进来，修的是集合，没动它上面那段说明）。

**为什么值得记而不是忽略**：这个目录的整套设计就是「声明一个集合，源头一动就 fail-closed」，
而 docstring 是读者判断「这张图画的是什么」的唯一入口。集合与说明不一致时，
fail-closed 保护的是数，保护不了读者对数的理解。改一个数字的事。

另：P4-P16 的裁决顺带确认了 `theory-compiler/STATUS.md` **在同一个文件里把 E-06 记了两遍**
（`:159`/`:165` 清偿，`:325` 仍标未清偿）。该文件在 sprint 层级是新在前、旧在后，
所以清偿是较晚的那条记录；论文已按台账（`cold-start-a0/THEORIZE_LOG.md:362`）裁决并
把这处自相矛盾写进正文而不是挑一半用。**这条是给 theory-compiler 轨道的**：
自己的 STATUS 自相矛盾，最好由它自己加一句 supersede，而不是让下游每个读者各自推断顺序。
