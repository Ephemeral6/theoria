priority: 1
cell: P5
territory: release
deps: none
lane: infra

# R3-release-classifier-defaults · 释出分类器的每个默认值都指向「可发布」

对抗性普查（2026-07-29）在释出包这一侧抓到三条，方向一致：
**读不到、认不出、算不出，一律落进 A 类 releasable。** 这是要公开发布的那一包。

1. **`release/enumerate.py:123`** —— `_arc_game_ids()` 从 `.get("strata", {})`
   取 id 列表，键缺失被吞成空 dict，空推导是合法的空列表。于是 `classify` 对每个文件
   都走到 :158 返回 **A 类**，证据串写着「no ARC game id appears in this file」。
   实测影响：**33 个 B→A、223 个 C→A**。
   同包的 `check_redlines.check_sealed:443-450` **已经补过这道守卫**，
   注释逐字记着这种情况过去会「拿一个空 id 列表扫过 2817 个文件，然后印
   Both red lines clear」——补在了两个 id 读取器中的**一个**上。
2. **`release/check_redlines.py:417`** —— `PAYLOAD_MARKERS` 声明了 7 个载荷字段
   （常量在 :116-124），而 417 行是个**死常量**，实际只测 3 个。
   漏掉的 `scorecard` / `state` / `available_actions` / `guid` / `full_reset` 意味着
   一条把封存 id 和记分板正文配在一起的记录会被归入「提及」，
   并附上一句自我表扬：「NO record pairs a sealed id with payload —
   checked record by record, not by co-occurrence」。
3. **`release/enumerate.py:160`（另一处 :146）** —— 仍按**文件名后缀**判类，
   而 `check_redlines` 已经建了 `json_shaped()` 去嗅内容，docstring 还说共享判断
   「两个文件都调用它」——`enumerate.py` 唯独没调。同样的字节叫 `.jsonl` 是 B 类，
   叫 `.log` 就是 C 类并附上「carry no environment payload」的正面断言。

做四件：

1. `_arc_game_ids()` 加形状守卫：`len(ids) == len(dev_pile) + len(sealed_pile)`，
   否则**拒绝运行**（不是警告）。
2. :417 换成 `PAYLOAD_MARKERS`（常量已经写好了）；给测试补一个 `scorecard`
   阴性样本——现有 9 个违规夹具**全用 `frame`**。
3. :160/:146 换成 `redlines.json_shaped`。**这条不便宜，要事先说清楚**：
   修完 `theoria-arm/runs/.../pytest-baseline.txt` 会变成 needs_human，
   `enumerate.main()` 与 `checklist.py` 都会退出 1。**正确的修法会把闸门变红——
   那是这件工单的成功，不是失败。**
4. 三条各配阴性样本，并跑一次完整枚举，把「修前分类分布 / 修后分类分布」
   两份都归档进 `runs/<id>/`。**这次修复的价值全在那个 diff 里。**

服务论文 WP10 与 WP6（封存主张随释出包发出去）。零 API、零封存堆接触。
