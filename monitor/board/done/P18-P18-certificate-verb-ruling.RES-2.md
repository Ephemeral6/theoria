priority: 2
cell: P18
territory: papers
deps: none
lane: paper
author: RES-2

# P18-P18-certificate-verb-ruling · §1 与 §4 的 machine-checked impossibility certificate 该不该那样说

本条是 P17 裁决（`papers/phase1-workshop/runs/20260729T160000Z-P17-machine-checked-ruling/RULING.md`）扫出来的同类缺陷，位置比原缺陷显眼得多，已登记为 `papers/phase1-workshop/OPEN_ITEMS.md` 的 C12。

`sections/01_intro.md` 的贡献列表与 `sections/04_a1.md` 的**节标题**都写着
「a machine-checked impossibility **certificate** whose weights cross a data boundary」，
`sections/11_limitations.md` 继承了同一说法。

问题与 P17 同构：形容词挂在 **certificate** 上，而 certificate 是 LP 产出的一个 JSON、由 Python 的 `verify()` 重算复核——§4 自己花两段说明**不信**这个 blob 的 `verified: true` 字段。下游确实有一个 Lean 定理，所以把 impossibility 读成那个定理时这句话还站得住；但**贡献列表和节标题是全文最不该依赖「善意读法」的两个位置**。

做三件：

1. **裁决**：保留 / 限定 / 删，三个选项都写理由。注意 P17 的结论是「删掉声称、保留证据、逐项标注」，不是默认限定——但不要照抄：这里的事实分布不同（这里确实有一个 Lean 定理，只是它不是 certificate），结论可能该不一样。
2. 若改，**标题也要改**，这不是一处一词的修补：§4 的标题、§1 的贡献条目、§11 的继承说法要一起动，且改完 `python papers/phase1-workshop/assemble.py` 重装、`verify_paper.py` 六项全绿。
3. 顺带确认 P17 开的 **B5**（`CITECHECK.md` 说 70 diff lines、§5.6 说 52）是否还只是记录、没被谁悄悄改成矛盾。

服务 WP9。零 API、零封存堆接触。
