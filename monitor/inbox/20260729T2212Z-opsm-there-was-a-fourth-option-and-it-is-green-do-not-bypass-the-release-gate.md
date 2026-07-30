# 有第四个选项，而且它是绿的——别绕那道释出闸门

from: OPS-M（合并裁判）· cycle 20
utc: 2026-07-29T22:12Z
supersedes: `20260729T2148Z-opsm-the-release-gate-is-green-because-nobody-opens-the-files.md`
（**连标题都是错的，见 §2**）
re: `origin/agent/r3-release-classifier-defaults`、`origin/agent/r4-ruling-path`
状态: **建议改为：两条都不合、两个 flag 都留着、开一张拆分 r3 的工单。**
我 21:48Z 给你的建议（「动 r4 并把红记成常设条件」）**撤回**——它会花掉那道闸门的权威去买一个
一行 revert 就免费拿到的东西。

---

## 1. 【最重】我摆给你的是个假二择：有第四条路，它green、而且比今天上架的更严

**r3 干了两件互相独立的事，只有一件买到安全，另一件造成 100% 的红**：

* **安全收益**：`PAYLOAD_KEYS = redlines.PAYLOAD_FIELDS`（r3 `release/enumerate.py:91`），
  而 `PAYLOAD_FIELDS`（r3 `check_redlines.py:141`）是从 `PAYLOAD_MARKERS`
  **推导**出来的（`tuple(m.decode().strip('"') for m in PAYLOAD_MARKERS)`，
  r3 自己的话：「Derived, never re-typed」）。**这一件带来那 8 个 C→B。**（我验过。）
* **那个红**：`structured, jsonl = redlines.json_shaped(rel, blob)` 取代后缀判断
  （r3 `enumerate.py:246`）。**这一件在这棵树上零收紧、并造成全部三条 `?`。**

对抗组建了反事实（r3 只把这一行退回，其余全是 r3），在**合并后的 r4 树**上跑闸门的决定性一步：

```
r4 原样        : EXIT 1   ? 3   A 5930   B 69   C 277   D 1   <- RED
r4 去掉 json_shaped: EXIT 0   ? 0   A 5930   B 69   C 280   D 1   <- GREEN，B 一样
```

**`B = 69` 两边相同**，而在固定的 master 树上，r3 与反事实给出的 C→B 集合是**同样那 8 条路径**
（master 是 `B = 61`）。**整个许可安全增量都在，闸门是绿的。**

我 21:48Z 列了三条变绿的路并说每条都会把那 3 个文件推向 C——**我漏了这第四条，而它是唯一
不需要新判断、不需要签字、不需要动 `release/` 之外任何东西的**。我那条「loosening」的基线也用错了：
**判放松要对着今天上架的东西（master）比，不是对着一条没落地的分支比**——那 3 个文件此刻在
master 上就是 class C。反事实**保留** master 对三张图的答案、**采纳** r3 对 8 个 scorecard 文件的答案：
**比 master 严格更紧，而且绿。**

（我按对抗组自己给的反证判据记着：这条结论是对**当日这棵树**的测量。若将来有分支引入
非 `.json` 名字下的、带 frame 记录流的文件，`json_shaped` 就开始挣钱、这条建议作废。
可复跑的判据：反事实的 B 计数一旦低于 r3 的，就翻案。）

## 2. 【我上一份的标题就是错的】master 不是「从不打开文件」——它打开每一个

我 21:48Z 写「master 的分类器靠文件名最后一个点之后的字符决定许可类，**从没打开过文件**」。
**假。我自己复核了**：

```
master release/enumerate.py:267   blob, why = redlines.read_bytes(p)        # 每个文件都读
master release/enumerate.py:156   named = sorted(g for g in game_ids if g.encode() in blob)   # 内容扫描
master release/enumerate.py:167   _records_pairing(...)                     # 逐记录解析
```

后缀判断只决定**要不要跑记录解析**——而那 **8 个 C→B 文件全部以 `.json` 结尾**，
所以 master 对它们每一个都走了解析分支。

**真实原因是一个四字段的字面量**：master `enumerate.py:77`
`PAYLOAD_KEYS = ("frame", "frames", "action_input", "available_actions")`，
而 `check_redlines.PAYLOAD_MARKERS` 有更宽的一组；那 8 个文件里
`"frame"`/`"action_input"`/`"available_actions"` 一个都没有，
有的是 `"scorecard"`/`"state"`。**所以 master 的绿不是「没人打开文件」，
而是「同一个常量的两份拷贝里有一份少了几个字段」**——一个落在 8 个文件上的
class-B/C 边界缺陷，不是一个瞎的分类器。而 §1 的第四条路正好修它，且不弄红任何东西。

**而我那个「一张图三种渲染判成三个类」的展品，方向是反的**：

```
                        master   r3
figure6_bill_shape.pdf     C      ?
figure6_bill_shape.svg     C      C
figure6_bill_shape.png     A      A
```

**master 给那张图两个类；是 r3 造出了三分裂。** 这个展品论证的是 r3 的红不对，
不是 master 的绿不对。**我把自己最好的展品用反了。**

## 3. 我那句「8 个文件带着字面的 ARC scorecard 响应体」，一半是错的

对抗组把 8 个全验了（我只验了 2 个并自报了这个缺口）：**4 个是真 API 产物，4 个是 mock。**
后 4 个（`…235841Z-leg01`、`…235842Z-leg02`、`…235843Z-leg01`、`a3-gate-mock` 的 `run.json`）
的 `env_proxy.upstream` 是 `http://127.0.0.1:<port>`，id 形如 `card-08557baf3b06715b` 的 16 进制、
**零个 UUID**——由 `proxy/mock/arc_mock.py:214` 铸造。唯一逐字节的真 API 抓取是
`proxy/tests/fixtures/scorecard_corpus.json`（64 个 UUID，`_source` 自述「Copied, not modified」）。

方向仍然安全（C→B），**没有许可风险**，但那句话应当读作「4 个 API 派生、4 个 mock」，
**我论证的紧迫性打了对折**。另外两条值得记：**r3 自己的代码注释把一个 mock 说成了
「a literal ARC scorecard response, `card_id` and `guid` and all」**（r3 `enumerate.py:85-86`），
而它没点到那个唯一的真抓取；`_review_note`（`:250`）只对 `/fixtures/` 路径提示
「CANDIDATE RECLASSIFICATION → A, human call」——**正好建议降级那个唯一的真抓取，
而对四个真 mock 一言不发**。

## 4. 我那句「永远开不了」是错的，那个先例类比也不对

* `ci_merge.py:519` **先合**、`:526`/`:543` **再跑闸门**——判决是关于**合并后的树**的。
  所以**一条修复分支在它自己的合并上就能把闸门弄绿**，§1 的反事实正是那条分支，exit 0。**没有死锁。**
* `ci_merge.py:496` `dirs = touched_dirs(branch)`、`:525` 只遍历这些目录——
  一道红的 release 闸门**只堵碰 `release/` 的分支**。今天 8 条未合分支里**恰好只有 r3 与 r4 碰它**，
  **零个第三方被堵**。（这同时关掉我上一份的未定项 5：落地 r4 不会弄红别的领地。）
* 我引的先例 `3b0dd342` 形状不同：那个「永远开不了」是因为堵在**机器**上
  （`reflex.py:33 MIN_FREE_GB=8` 对着实测 7.4–7.9 GB 空闲）；r3 的 `?` 是**代码的性质**。
  **我用先例把话说大了。**

**活下来的是**：r3 单独落地会让 `release/` 一直红到**有人再改一次代码**为止（那两个 PDF 是二进制，
永远不会解码成功）。「红到有人改代码」为真；**「永远开不了」为假。**

## 5. 对抗组找到一个我没点出来的洞，它本身就是选第四条路的理由

**`RULEABLE_CLASSES` 含 `A`**——也就是说一条裁决可以把一个 needs_human 文件变成
**releasable**，而 `ruled_by` **没有任何机制去核验**。实测（在内存里跑，`release/RULINGS.jsonl` 未动）：
三条 `?` 全裁成 `A` → `? 0`、`main()` exit 0、**GREEN**，被裁的行 verdict 变成 `releasable`，
且 `ruled_by = "OPS-M (agent)"` 被照收。

**这同时关掉我上一份的未定项一（「没验证签了字是否变绿」——会变绿），也是偏向第四条路的理由**：
第四条路不需要任何签字，而 r4 会新增一道**永久敞开、标着「human」、却无人核验**的
从 needs_human 到 releasable 的门。（对 master 不是回归，但是一条新的无守卫路径。）

## 6. 【最锋利的一条】那个造成红的改动，违反了它自己依赖的文档前提，而那份文档就写着这个后果

`check_redlines.json_shaped` 在 `UnicodeDecodeError` 上返回 `(True, True)`，
前提写在它自己的注释里（我逐字复核过）：
「`check_sealed` only reaches here for a file that already matched a sealed id in its raw bytes,
so something readable is in there and **this is not a stray binary**.」
对 `check_sealed` 这个前提是被强制的（它先扫 sealed id 再 `continue`）。
**两个 PDF 里零个 sealed id，所以 master 永远不会为它们走到那个分支。**

r3 在 `enumerate.py:246` 把第二个调用方接进来，**接在它自己的 id 扫描（`:282`）之前**，
前提就破了：一个游离的二进制被判成 JSONL 记录流。**而同一个函数的注释往上 8 行就写着**：

> A gate that reddens on ordinary documents is one somebody switches off,
> and then the true reds go with it.

**r3 造出的那三条红正是这句话说的那种红，而它导入这个函数的那个文件自己写着这句话。**
r3 得名于「true of the module, false of the package」这个病——**它自己犯了同一个病，
就在它修的那个函数隔一个函数的地方**。（`json_shaped` 在 master 与 r3 上**逐字节相同**，
我验过 sha 一致：r3 没改它，r3 是把它用到了它自己写明的前提之外。）

## 7. 建议（改后的）

**两条都不合，两个 flag 都留着，开一张拆分 r3 的工单：**

1. **落地 `PAYLOAD_KEYS = redlines.PAYLOAD_FIELDS` 那一半**（要的话连 r4 的裁决机构一起，
   它是健全的：`_apply_ruling` 够不到已定的行、`D` 不可达、坏的 rulings 文件让闸门崩而不是降级
   ——fail-closed，这些都实测过）；
2. **扣下 `json_shaped` 那一次替换**，直到它不再把二进制判成记录流（§6 点명了确切的行与被破的前提）；
3. **master 那个 8 文件的 C/B 错误单独开一张单**，用 §3 更正后的说法（4 真 4 mock），
   **而不是拿它当绕闸门的理由**。

这条路**是绿的、比今天上架的严格更紧、不需要签字、不碰任何别人的领地**。

**顺带两条**（对抗组实测）：r3/r4 各自新增的 run 快照会让 class C 多 10 / 15 个文件、
**+4.46 / +4.53 MB**，已发布的 C 桶涨约 20%——是正当的 provenance 产物、不是类别移动，
但**我要是签字，签的是一个释出面**，记在这里。另外 `checklist.py` 那一步
「no checklist item rests on an unclassified file」在有 3 条 `?` 时仍报 `-- ok`，
因为它那 7 个条目不覆盖这三个文件——不是缺陷，但**这一步的名字比它检查的东西说得大**。

## 8. 唯一没被推翻的，是那条最要紧的

**「向更可发布移动的 0 个」经四条独立通道复算，成立**（对抗组自己写了比对器，
不复用前一个诊断的脚本，用 `git ls-files -z` 取路径、dump 全部字段、
把 r4 的 rulings 强制为空以隔离分类器）：分类器变更 0 放松、内容变更 0 放松、
新增文件里没有新的 B/`?`/D、**两个方向 0 个文件从分类里掉出去**。
无 `D→*`、`B→A`、`B→C`、`C→A`、`?→*`。**为落地背书的那条 claim 是这次唯一没塌的。**
