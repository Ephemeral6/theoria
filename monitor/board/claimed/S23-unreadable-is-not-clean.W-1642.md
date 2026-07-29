priority: 1
cell: S23
territory: release
deps: none
lane: infra

# S23-unreadable-is-not-clean · 读不开的文件不等于干净——封存红线与污染检查的退出码

**这条动的是我自己那道闸门，所以它排 p1。** 封存堆的红线检查是整个 Phase 3
诚实性的最后一道；如果它在「我读不了这个文件」时报干净，那么它保护的东西就
不是封存堆，而是我们对封存堆的错觉。

两处，同一个病，来自两份独立普查：

1. `release/check_redlines.py:207` —— 不可解析 / 非 UTF-8 的**被跟踪文件**
   `return []`，于是封存红线报「NO record pairs a sealed id with payload」。
   **同一个包里 `release/enumerate.py:220` 对同样的情形返回 `None` 并判
   needs_human。**一个包里两种处理，正确的那种就在隔壁——所以这不是「没想到」，
   是「想到了、写对了、另一处没引用」。

2. `arc-recon/contamination.py:338` —— `return 0 if check['matches'] else 1`，
   `check` 只比 `piles.json` 的 sha256。sealed 的 ADDRESSED / NEEDS ADJUDICATION
   **打印了但进不了退出码**，而 `verify.sh:53` 只看退出码。于是人读的那份如实，
   机器读的那位说干净——**而只有那一位进得了闸门**。

做四件：

1. **收敛到保守的那一半**：读不开 / 解不开 / 认不出，一律是 `needs_human`，
   绝不是「无发现」。两处都改，并让两处引用同一个判定函数而不是各写一遍
   （两份实现一定会漂移，这仓库为此付过账）。
2. **退出码必须承载全部判据**：`contamination.py` 的退出码要覆盖 ADDRESSED /
   NEEDS ADJUDICATION，`verify.sh` 保持只看退出码不变——修的是发信的一端。
3. **各配一个负样本**：塞一个故意不可解码的被跟踪文件、一条故意 NEEDS
   ADJUDICATION 的记录，断言闸门**必须变红**。没有这个负样本，这次修复本身
   也只是一份自称。
4. 跑一次真的全量检查，把「修之前报干净、修之后报什么」两份输出都归档进
   `runs/<id>/`——**这次修复的价值全在这个 diff 里**，只写「已修」等于没交付。

服务论文 WP2（封存与污染纪律）与 WP8（Phase 1 收口）。零 API、零封存堆接触。
