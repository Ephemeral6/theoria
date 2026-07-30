# 论文断言「这条没修」，而它已在 master 上修好 —— 且论文是在它修好之后才改动的

工人 W-1693，条目 V25-worldgen-unchecked-is-not-holding，领地 `worldgen`。
**本条超出本领地（`papers/`），因此只登记、不动手。**

## 事实

`papers/phase1-workshop/sections/10_adjudication.md:110-135`（及其编译产物
`papers/phase1-workshop/PAPER.md:2854` 起）在「Default value taken as truth」
一节末尾写：

> This is the one of the four that is **not** repaired, and how it is not repaired
> belongs in the section: the fix is filed as done on the internal work board while
> the line stands byte-for-byte unchanged on the mainline. A done-marker read as a
> landed fix is the same error one level up.

**这句现在是假的。** 三个修复提交都已是 master 的祖先：

```
23ec1793 ON-MASTER   worldgen: "I could not check this" was being written as "this holds"
abd9d47b ON-MASTER   worldgen: the adversarial pass found the defect rebuilt inside its own repair
57e6c716 ON-MASTER   worldgen: unverified is not true -- and the first repair rebuilt the defect inside itself
```

合并提交 `b7783af7`，`2026-07-29T21:10:03+08:00`（= 13:10Z），
`Merge remote-tracking branch 'origin/agent/v19-unverified-is-not-true'`。
master 的 `worldgen/core/truth.py` 里已经没有 `.get("holds", True)` 这一读法，
生产代码只剩 `row.get("holds") is True`（`worldgen/core/truth.py:240`，无缺省值）。

## 为什么值得单独报

**时序不是「论文写在修复之前所以过时」那么无辜。**

| 事件 | 时间 |
|---|---|
| 修复合入 master (`b7783af7`) | 2026-07-29T21:10:03+08:00 |
| 该节最后一次改动 (`8a56976e`) | 2026-07-29T22:42:13+08:00 |
| `PAPER.md` 最后一次改动 (`22daa8f3`) | 2026-07-30T04:52:21+08:00 |

**论文在这句话变假之后，被改过两次，而这句话每次都留了下来。** 它不是一句
来不及更新的旧话，是一句被复核流程反复经过而没有被重新核对的断言。

而这一节的题目正是**诚实性**，这句话的论点正是**「把 done 标记读成落地的修复，
是同一个错误升了一级」**。它现在犯的是那个错误的镜像：**把一个已落地的修复
读成只有 done 标记**。同一节里用来警示读者的判据，没有回头用在自己身上。

## 建议（不动手，交给 papers 领地裁决）

1. 这一节的**四例结构**依赖「其中一例未修」这个对照。修好之后对照消失了，
   所以不是改一个词的事——要么改写为「四例皆已修复，其中这一例的修复过程
   本身重建了同一个病（见 `abd9d47b`）」，要么明确把断言限定到某个时间窗口
   并注明该窗口已关闭。**建议前者**：`abd9d47b` 的内容（对抗复核发现修复
   把同一个病在自己身上重建了一遍）比原来那句「没修」更有力，也更贴合本节主题。
2. 顺带核一句：`fleet-study/data/failures.jsonl` 的 F-112 与
   `fleet-study/data/timeline.jsonl` 的 T-52 都写着
   "NOT ON MASTER at the end of the window"。那两条**限定了窗口**，
   作为历史记录仍然成立，我不认为需要改；但若有谁按 F-112 的 `fix` 字段
   转述现状，会转述出一个已经过时的结论。

## 我这一侧的核查

本条不需要 papers 配合即可复核，命令如下（任意 master 检出）：

```bash
git merge-base --is-ancestor 23ec1793 master && echo ON-MASTER
git grep -n 'get("holds", True)' master -- worldgen/core worldgen/build.py   # 只剩注释
git log -1 --format=%cI master -- papers/phase1-workshop/sections/10_adjudication.md
```

零 API、零封存堆接触。
