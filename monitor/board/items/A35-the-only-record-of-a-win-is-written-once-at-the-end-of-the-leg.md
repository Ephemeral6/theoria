priority: 1
cell: A35
territory: theoria-arm
deps: none
spend: none

# A35-the-only-record-of-a-win-is-written-once-at-the-end-of-the-leg · 通关事件的记录路径是「跑完再写」，而这个项目最贵的两次调用正是死在跑完之前

A31 说边界探测器一次也没发过；本件说的是**另一件事**，且它在探测器发得出信号
的那一天才会伤人。逐字，`theoria-arm/inner/loop.py:1983-1991`：

```python
    def _save_all(self) -> None:
        ...
        with open(os.path.join(out, "levels.jsonl"), "w", encoding="utf-8",
                  newline="\n") as fh:
            for event in self.levels.events:
                fh.write(json.dumps(event, sort_keys=True))
```

`levels.jsonl` 只有这一个写入点，模式是 `"w"`，调用点是 `_save_all` ——腿的
末尾。边界事件在 `_record` 里当场产生（`loop.py:443`，`self.levels.observe`），
然后**在内存里一直等到腿结束**。腿没能走到 `_save_all`，事件就不存在过。

## 这不是假想的失败模式，它已经发生过两次

`loop.py:1951` 的 `_adopt_the_turn_in_flight` 的 docstring 自己记着：

> Two live legs (`20260731T1310Z-A3-level2-carried-r2`,
> `...T1430Z-...-r3`) lost their final and most expensive call to this

同一份代码里，2026-08-02 的 A27 交付给**新**产物 `witnessed_wins.json`
写了正好相反的规矩（`runs/20260802T2100Z-A27-level-boundary-detector/RUN_STATE.md`）：

> Written to disk the instant the boundary exists, because a leg that dies two
> actions later must not take the only positive example in the project's
> history with it.

**A27 的作者为自己的新文件认出了这个危险，没有回头看旧的那条路。** 于是今天
仓库里有两条记录同一件事的路：一条边界一出现就落盘，一条等到腿善终才落盘。
`CLAUDE.md` 的规矩只有一条：「Write as you go: a session's context evaporates,
the disk is the memory.」

## 量出来的现状

`theoria-arm/runs/*/levels.jsonl`：**22 个文件，非零字节的 0 个**（本件复算，
与 A31 逐目录点的结果一致）。所以今天这条路上没有数据可丢——**这正是修它最
便宜的时刻**，也是唯一一个改写它不会碰到任何既有归档的时刻。等它开始出数据
再来修，第一条数据就是最可能丢的那条。

## 欠的是什么

1. `levels.jsonl` 改成**产生即追加**（`"a"`，每条事件一行，落盘后再返回），
   `_save_all` 保留但降级为「补齐内存里还没落的」而不是唯一写入点。
2. `armtools/noise_floor.py:275` 已经把 `levels.jsonl` 列进期望产物清单；
   追加式写入不得改变一条正常结束的腿的产物字节——这是本件的兼容性约束。

## 验收

一条 mock 腿在产生一次边界事件之后**被强杀**（不走 `_save_all`），
`levels.jsonl` 里必须有那一行；同一条腿正常结束时的 `levels.jsonl` 与今天的
实现**逐字节相同**。

## 负样本，两条

* 一条**没有**任何边界事件的腿：`levels.jsonl` 必须仍然存在且为空文件，
  **不是缺席**——今天 22 条腿都是这个形状，把它改成「没事件就不建文件」会让
  22 份既有 MANIFEST 的 `files[]` 全部对不上。
* 一条产生了边界事件、随后**同一条事件又被 `_save_all` 写一遍**的腿必须
  被测出重复并红。追加式写入最容易坏的地方就是与末尾那次全量写重叠，
  而一次被记录两次的通关，和一次没被记录的通关一样不能用。
