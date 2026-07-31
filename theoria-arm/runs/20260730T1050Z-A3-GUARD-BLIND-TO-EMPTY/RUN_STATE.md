# A3 · 我给自己的迁移守卫披露了一个缺口，对抗复核找到了更大的第二个

上一 leg（`20260730T0700Z-A3-COST-SHAPE-COUPLING`）里我攻了自己的迁移守卫，
找到并披露了一个缺口：`diff_leaves` 比的是 Python 值，而 `0 == 0.0`、
`True == 1`，所以一次把整数变成浮点的再推导会改动磁盘字节而守卫报「无变化」。

**那不是最大的那个。** 本轮的对抗复核（三个独立 subagent，各带一条视角）
在同一个函数里找到了第二个，它结构上更糟。

## 一、缺口

```python
flatten({"a": {}})   # -> {}
flatten({"a": []})   # -> {}
```

`flatten` 只在**非容器**上执行 `out[prefix] = obj`。空容器的 `for` 跑零次、
够不到 `else`，于是**不产生任何叶子**。而 `diff_leaves` 比的是叶子键集合——
所以一个值为 `{}` 或 `[]` 的键对 `added` / `removed` / `changed` **三者同时不可见**：
它可以被删掉、被凭空发明、或在两种容器类型之间翻转，守卫都报「什么也没变」。

已实测的三个突变（`recheck_report.json` 的 `blindness_demo`）：

| 突变 | 出厂守卫 | 修好的守卫 |
|---|---|---|
| `{}` → `[]` | 看不见 | 看见 |
| 整个键被删掉 | 看不见 | 看见 |
| **凭空发明一个顶层键** | 看不见 | 看见 |

**这和我披露的那个不是同一类。** `0 == 0.0` 是对一个守卫**看得见的**叶子的
表示形式失明；这一个是对**键本身是否存在**失明，它直接证伪 docstring 里那句
「nothing else, anywhere in the manifest」。

**而且它是活的，不是假想。** 七份被迁移的清单每一份都带
`cost.from_price_table.per_model = {}`——就在迁移改写的那个块里面。

## 二、那么迁移本身错了吗？没有。这两件事不能混

守卫的**判词**不值它自称的那个价，这不等于**迁移**做错了。分开量：

`recheck_with_a_fixed_flatten.py` 把 `before` 从 git 里取
（`53e6ea0b^`，不是重跑——今天重跑 `build()` 得到的是 *after* 的形状，
等于拿它跟自己比），用修好的 `flatten` 重比七份。结果七份全部：

```
added   = 恰好三个 S29 键（missing_usage_keys / unmeasured_calls / unpriced_usage_keys）
removed = {}
changed = {}
diff_is_exactly_the_three_s29_keys = true
```

修好的守卫同时把我原先披露的那个缺口一并关上：`changed` 的判据加了
`type(a[k]) is not type(b[k])`，所以 `0` → `0.0` 现在会被抓。

所以：**迁移是干净的，守卫是虚的。** 原 docstring 里那句
「the committed diff ... is exactly 21 added lines, three per file, with zero
removals and zero modifications」一直是对的——它本来就是独立于守卫的证据，
这也正是它当时被写下来的理由。

## 三、修好的 `flatten` 关掉的是两类，不是两例

* **空容器产生叶子**，并带上它原本是哪种容器（`("<empty>", "dict")` /
  `("<empty>", "list")`），所以 `{}` 与 `[]` 可区分，且都不再隐形；
* **路径是元组，不是用 `.` 拼的字符串。** 原版拼 `.`，于是 `{"a.b": 1}` 与
  `{"a": {"b": 1}}` 撞在同一个键上。**这份语料里有 265 个带点的键**——
  `upstream_pin` 就是按文件路径做键的（`proxy/cost.py` …）。今天还没咬到，
  但配料已经齐了：一个带点的模型 id（`claude-sonnet-4.5`）就够。

## 四、兄弟守卫的同类失明，我上一轮没攻它

`migrate_files_in_clone.py` 把幸存的 `files[]` 条目做成 Python **集合**再比。
集合对**顺序**和**重复**都失明，而那个脚本别处没有覆盖列表顺序——
所以 46612a9c 的「surviving entries are byte-identical」**逐条为真、逐列表未证**。

按列表重测了（`recheck_report.json` 的 `files_guard`）：

* `before_count` 16 → `after_count` 14
* `survivor_relative_order_preserved`: **true**
* `after_has_no_duplicates`: **true**

也就是说这里同样是：守卫虚，结果实。

**上一轮我攻了 `migrate_cost_shape.py` 却没攻它的兄弟**，而两个脚本是同一天、
同一双手写的。这是「攻自己」这件事最典型的失手方式——攻了被点名的那个，
放过了没被点名的同源那个。

## 五、离开被跟踪树的那两个摘要，接回来

46612a9c 从 leg01 的 `files[]` 里去掉了两条整项，而 `migration_files.json`
只记了路径、没记摘要（对比 `migrate_cost_shape.py`，它的 `leaves_removed`
是带值的）。于是这两个 sha256 在 HEAD 的被跟踪树里 `git grep` 零命中——
它们只活在 git 历史的一个被取代的 blob 里。`CLAUDE.md` 说 Phase 4 释出清单
发布的是**被跟踪文件**，被取代的 blob 不是。两行字的成本，记在这里：

| path（46612a9c 从 leg01 的 files[] 移除） | sha256（取自 `46612a9c^`） |
|---|---|
| `candidates.jsonl` | `e5c2226a52bf71b094b1643310693fcae29e3e04874f60feff35392182c22180` |
| `trace.jsonl` | `f6a373fee6a4e13503a83dcfc50921ecb4130c0eaa3bf45630b3ff0c74a55539` |

顺带把当时说轻了的代价说准。原话是「被排除产物的 `sha256` 不再被带下去」。
实际是：`backfill.build()` 的 `files[]` 摘要是**从磁盘现算**的，而 check 8
逐字节比对——所以 `files[].sha256` 在 theoria-arm 内部是一个**活的漂移探测器**。
迁移之后，这两件产物**在整个仓库里不再有任何漂移探测器**。
代价不是「一个哈希没被带下去」，是「两件产物离开了唯一覆盖过它们的完整性检查」。
（它们是 gitignored 的本地产物，所以这在当前读法下可接受；但那是一个判断，
不是「无损」。）

## 六、留给下一世的一句话

我上一世在心跳里写：「**在它回来之前我已经自己攻掉两条**」。
那句话是真的，也是这次最该被拿掉的一句——**自己攻自己抓不到的正是自己的盲区**，
而这一次盲区就落在我攻过的那个函数里、以及我没想到要攻的那个兄弟脚本里。
自攻的价值是提前修，不是替代对抗复核。这次的顺序（自攻两条 → 对抗复核再拿两条）
是对的顺序，别把前半段当成完成。
