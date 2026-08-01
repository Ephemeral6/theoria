priority: 1
cell: A24
territory: theoria-arm
deps: none
spend: none

# A24-round-scoreboard-columns-are-null · 记分板上 `Theoria.md:351` 点名的那一列，四条腿全是 null

`armtools/round.py:100-111` 老老实实去读两个键，而 harness 从来没写过它们。
两份轮记录，四条腿，逐字：

```
_rounds/20260731T231654Z-R1/round.json    legs[*].theorize_rounds = null   game_id = null
_rounds/20260801T001851Z-R1b/round.json   legs[*].theorize_rounds = null   game_id = null
```

`theorize_rounds` 不是随便一列。`Theoria.md:351` 定义记分板时点了名——
「每关 theorize 轮数」——`round.py` 自己的注释也这么写。今天它 4/4 是 null，
也就是**记分板的一整列从未被记过一次**；而 `game_id` 是 null 意味着一份轮记录
无法自证它跑的是哪一局，尽管 slug 里写着 `g50t-a` / `sk48-b`（**slug 是人写的
标签，不是记录**——这正是 freeze 在 `E2` 上刚裁过的同一种毛病：轴由记录方随手
写下，就不能拿来做跨臂比较）。

要做的：让 `harness/run.py` 的 `run.json` 真写这两个键，`round.py` 照原样汇总。
`theorize_rounds` 的定义要写下来再实现——本关内 theorize beat 的调用次数，
关号从 `levels.jsonl` 取；四条腿 `levels_completed` 全 0，所以第一版必然是
「level 1 上的轮数」，那就把它如实叫 level 1，别假装是「每关」。

验收：mock 整轮跑通后 `round.json` 的四条腿两个键都非 null；R1/R1b 这两份
**已发布**的记录不许回填改写（追加一份重算，不改已归档的字节）。

负样本：一条 `run.json` 缺 `theorize_rounds` 的腿，汇总必须落 `null` **并带
一句原因**，不得落 0——「一个从未跑过的 beat 记 0，不是关于那个 beat 的证据」
是 GAP 2 已经写下的话，这里是同一条纪律的第二次用场。第二条负样本：
`game_id` 与 slug 不一致时必须报出来，而不是让 slug 静默取胜。
