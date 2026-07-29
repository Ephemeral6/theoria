# DRIFT-v23-was-boarded-65-seconds-after-its-premise-was-fixed

severity: medium
dimension: 3（证据漂移）＋ 6（要求引用了不存在的东西）
cycle: OPS-A 41
adversarial-review: 有。一个专职找反例的 subagent 攻了五个轴，判定 **PARTLY REFUTED**
——事实脊柱全部挺住，**结论句被驳回并已按它的措辞改写**。下面标了它改了什么。

## claim

工作板条目 `monitor/board/claimed/V23-figures-sources-absent.W-1681.md`（priority 1，
已被 W-1681 认领）与提交 `7a71b5ab` 的说明，都用**现在时**断言
「`figures/SOURCES.sha256` 把四个开发堆账本记成 `ABSENT0000`，所以 `figures/verify.sh`
有一关**此刻是红的**」。**这句话在写下时已经是假的——早了 65 秒。**

## evidence

**时间线（全部 UTC，均可复核）：**

| 时刻 | 事件 |
|---|---|
| 16:19:27Z | `a5f597dd` 提交，把那四行 `ABSENT0000` 换成真哈希（在一条分岔分支上） |
| 17:15:22Z | `2d603da1` 提交，**仍然带着**那四行 ABSENT |
| **17:15:56Z** | 合并 `580c645d` 落盘。`figures/SOURCES.sha256` 的 mtime 精确等于这一秒 |
| **17:17:01Z** | **V23 条目文件被写出**（mtime，文件未被 git 跟踪，mtime 是现有最好的证据） |
| 17:22:09Z | `board.log:313` `CLAIM V23-figures-sources-absent by W-1681` |
| 17:30:06Z | `7a71b5ab` 提交，说明里重复同一句现在时断言 |

`a5f597dd` 对该文件的改动**只有四行**，正是条目引用的 `SOURCES.sha256:24-27`：

```
-ABSENT0000…000  baseline-arms/out/shards/ledger.{ar25,g50t,sk48,tn36}.jsonl  [absent-optional]
+a82d1f40c667…   baseline-arms/out/shards/ledger.ar25.jsonl  [untracked]      （四行，真 sha256）
```

**此刻树上**：`grep ABSENT figures/SOURCES.sha256` 只命中第 3 行的表头注释，
**数据行零命中**；四个 shard 全部在盘；61 条声明里**没有一条 MISSING**。

**存在一个 34 秒的窗口**（17:15:22–17:15:56）里那句话是真的。V23 不是在那个窗口里写的，
而且它自己的正文（「刚刚由监控入库」）就把作者时间锚在 `2d603da1` 之后。

### 顺带两条，同一份条目里

1. **条目第 22 行「50 条里 13 条已漂移，且是已提交的漂移」两个数都不对。**
   实测：**61 条**声明（`a5f597dd^` 也是 61），主工作树里 55 匹配 / 6 不匹配 / 0 缺失，
   而那 6 条**全是 CRLF 检出假象**——`core.autocrlf=true`，6 个 `baseline-arms/out/pilot_*.json`
   在盘上带 CRLF，其 **blob（LF）哈希逐字节等于声明值**。
   **在 W-1681 自己的工作树 `.worktrees/v23-figures-sources-absent` 里：61/61 全绿。**
   所以「已提交的漂移」这个判断本身就是同一类误测——工人被要求去逐条裁决 13 条不存在的漂移。
2. **条目第 26 行要求「在 `figures/STATUS.md` 里写清处置」，而 `figures/STATUS.md` 不存在**
   （第 6 维）。fig03/fig04 在 `papers/` 下确实出现 0 次，这一条的**事由**是真的。

### verify.sh 那一关到底红不红（这是我原来想当然、被复核纠正的地方）

`figures/verify.sh` 共 **13 关（0–12）**。ABSENT 只可能让**第 4 关**变红，而第 4 关是
`diff -u 已提交的 SOURCES.sha256 重建出来的 SOURCES.sha256`（verify.sh:112）——
它红在**状态发生了变化**，不红在「记成 ABSENT」本身。
**没有任何一关会因为「记成 ABSENT 且确实不在盘上」而变红**：第 0 关
`sources.check_required()`（`sources.py:807`）按 `not s.optional` 过滤掉可选项；
第 12 关（verify.sh:352-355）查的是**反面**——「记成 ABSENT 却在盘上」。
`absent-optional` 被容忍是**写下来的设计**（`figures/SOURCES.md:97-99`：
「absent 是这里的预期状态，一个要求它们存在的构建没法从干净检出跑起来」）。

## suggest

1. **重定范围，不要关闭。** 复核明确驳回了我原来的结论句（「一个 priority-1 工人在重做已完成的活」）。
   准确的说法是：**V23 四件事里的第 1 件，在条目写下前 65 秒已由 `580c645d` 落盘**；
   剩下三件**没被碰过而且独立有价值**——
   （a）为什么一道红闸门没人报（`a5f597dd` 自己的说明确认了这个前提：
   master 的 figures 闸门从 `9307f139` 起就红着并遮住了整个 figures 领地）；
   （b）其余哈希的逐条裁决——但**必须先把 CRLF 误测改掉**，否则工人会去追 13 条幽灵；
   （c）fig02/03/04 的存废，并且得先**创建** `figures/STATUS.md`。
2. **给 `figures/` 加一条 `.gitattributes`（`baseline-arms/out/**.json` 定 LF）**，
   否则任何在主工作树上核对 `SOURCES.sha256` 的人都会看见 6 条假漂移。
   `engine-rig/.gitattributes` 已经为同样的理由存在，这是同一个坑。
3. **给供货加一步：条目落板前，把它引用的文件路径与行号在当前 HEAD 上复核一次。**
   本轮三条被登板的断言里，`scan.py 崩溃不写 state.json` 在 HEAD 上**是真的**（S30 前提成立），
   `battery 盲化硬编码路径` 在写下时**是真的**（已由 V24 修好并交付）——
   **三分之二为真，所以这不是系统性的陈旧供货，是单点**。我原本准备写成前者，被复核杀掉了。

## 复核改了什么（留痕）

- **杀掉**：「一个 priority-1 工人在重做已经完成的活」——过头了，四件里只有一件已完成。
- **杀掉**：「监控在拿陈旧审计批量供货」——三条里两条为真，样本不支持。
- **加进来**：真正落盘的是合并 `580c645d` 而非 `a5f597dd` 本身，差距是 65 秒不是 71 分钟；
  以及那个 34 秒真值窗口的存在（对我不利，仍然写上）。
- 复核**没能**推翻的：路径对得上、祖先关系对得上、工作树与 HEAD 一致、时序对得上。

## 复现命令

```bash
git show a5f597dd -- figures/SOURCES.sha256          # 只有那四行
grep -c ABSENT0000 figures/SOURCES.sha256            # 0
stat -c '%y %n' figures/SOURCES.sha256 monitor/board/claimed/V23-figures-sources-absent.W-1681.md
grep -n V23 monitor/board/board.log                  # 只有一行 CLAIM，无 DONE
sed -n '352,357p' figures/verify.sh                  # 第 12 关查的是反面
ls figures/STATUS.md                                 # 不存在
```
