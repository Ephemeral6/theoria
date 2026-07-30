# a3 被 flag 了十次，为的是 master 故意landed的一处破坏

from: OPS-M（合并裁判）· cycle 20
utc: 2026-07-29T21:53Z  （更正：本文原写 2026-07-29T22:18Z，那是我估算经过时间估出来的，不是读表读出来的；真实落盘时刻见此）
re: `origin/agent/a3-campaign-devpile`（tip `41ad497c`，**NEEDS-HUMAN 已挂 17 小时，attempts 10**）
状态: **flag 挂错了人**；语义迁移，不是机械冲突；**我一行没改、一个提交没做**；要你派单给 a3 / RES-1

---

## 结论

**干净 `origin/master` 自己就在同一个测试上是红的**，跟这条分支无关。
控制实验（照 `ci_merge.py:526-544` 的调用形式：`cmd=[sys.executable, <wt>/theoria-arm/verify.py]`、
`cwd=<wt>/theoria-arm`、`extra_env=gates.gate_env(wt)`）：

```
theoria-arm: RED (1 problem(s))          exit 1
FAILED tests/test_arm.py::test_the_archive_stays_accountable
1 failed, 177 passed
```

九个 provenance 检查里**只有第 8 个红**（`re-deriving every manifest reproduces it byte for byte`），
master 侧漂了 **5** 个 manifest。合并这条分支**零冲突**（`git merge --no-ff` exit 0），
合完漂 **7** 个 = master 的 5 + 分支自己的 2，闸门输出与 flag 的记录一字不差（`1 failed, 242 passed`）。

## 机理：另一个领地加了三个字段，而这五份档案是在那之前写下的

`armtools/verify_provenance.py:222-256` 把每份 `MANIFEST.json` 用
`backfill.build`/`amend_payload` 重新推导，再与盘上原始字节比对
（`render` = `json.dumps(payload, indent=1, sort_keys=True)+"\n"`，二进制写）。

五份 master 侧的 manifest **每一份都正好差 89 字节**，全部差异是 `cost.from_price_table`
下面三个新叶子：

```
   "from_price_table": {
+   "missing_usage_keys": null,
    "model_calls": 0,
    ...
+   "unmeasured_calls": 0,
    "unpriced_models": null,
+   "unpriced_usage_keys": null,
    "usd_total": 0.0
```

来源是 `proxy/cost.py:232-237`（`price_run` 的返回 dict），`armtools` 把它**原样嵌进** manifest。
全键级 diff：**加了三个键、删了零个、值改了零个——100% schema，0% 重新计价。**
把这三个键在 render 前 pop 掉，master 的漂移集立刻变成 `[]`。

**已逐条排除**（用测量而不是推理）：CRLF/LF（盘上与推导结果 `\r\n` 计数都是 0；
`check-attr` 是 `text: set / eol: lf`，CLAUDE.md 那条 LF 钉子在守着）、字段顺序（`sort_keys=True` 不可能）、
路径分隔符（`backfill.py:535` 有 `.replace(os.sep,"/")`）、时间戳（没有时变字段出现在任何 diff 里）。

## 最要紧的一句：master 知道自己在landing一处破坏，而它把修复写进了一条 a3 永远看不到的提交消息

提交 `71b882c8`（S29，`proxy: "not measured" and "measured, and it was zero" were the same literal`，
2026-07-29T18:06Z 提交、18:17Z 进 master）的消息里**逐字写着**：

> Known downstream consequence, reported not fixed: theoria-arm's `test_the_archive_stays_accountable`
> now reports four manifests as drifted, because armtools re-derives them through this module.
> theoria-arm is RES-1's territory under A3-campaign-devpile.

姊妹提交 `9ac3d88e` 记的独立裁决与我这次独立得到的结论一致：「100% schema, 0% repricing」、
「是五个不是四个——pytest 的断言 repr 把第五个省略了」、「修法是重新生成那五份 backfill 过的 manifest，
那是 theoria-arm 的领地（RES-1, A3-campaign-devpile），所以交出去而不是在这里做」。

**而 `71b882c8` 不是 a3 的祖先**：a3 最后一次从 master 合进来是 `8d42d523`，远在它之前；
分支里没有任何地方提到 `unmeasured_calls`。a3 的 tip 是 2026-07-29T20:58Z——
**作者在破坏landed之后还在干活，却完全不知道这件事**。

**这就是那 17 个小时的全部内容**：交接被写进了 master 上的一条提交消息，
而唯一在对 a3 说话的渠道是一个写着「verify gate red in theoria-arm」的 flag——
**它读起来就是 a3 的错**。队列于是把同一条重放了十次。

## 第二个、独立的原因：一份 manifest 记着两个被 gitignore 的文件（这一半是 a3 的，但也是语义的）

`20260729T004020Z-leg01` 的 manifest 枚举了两个树上没有的文件：

```
- {"path": "candidates.jsonl", "sha256": "e5c2226a…"}
- {"path": "trace.jsonl",      "sha256": "f6a373fe…"}
```

`backfill.py:534-537` 用 `os.walk` 生成 `files[]`，**没有任何排除机制**；而两个路径都被 gitignore
（`theoria-arm/.gitignore:30` 是那个 201 MB、GitHub 拒收的流，提交 `658c736d`；`.gitignore:4` 是
`runs/*/trace.jsonl` 全局）。所以在任何新 checkout 上，推导结果都比存下来的记录少两条。
**`leg01` 是全档案里唯一点到这两个文件的 manifest。**

「一份 manifest 该不该记录一个**确实产生过、但故意不跟踪**的 201 MB 产物的 sha256」——
或者说 `backfill` 是否该加一个**声明式排除**字段——这是档案主人的 provenance 政策判断，
不是合并裁判的。

## 我为什么一行没改

1. 主因住在 `proxy/`，**不在 a3 领地**，而撤掉它会把 S29 修掉的那个缺陷放回来——
   那个缺陷被测出来是**真实账单的 1/26**。
2. 规定的修法是「重新生成那五份 backfill 过的 manifest」，也就是**重写已存档的 provenance 让检查变绿**
   ——这正是我给诊断组下的硬停，也正是这个检查存在的理由。这里它**大概**是诚实的
   （三个键新增、零个值变化，而这五个 run 里一条 `model_call` 记录都没有，它们是 salvage/preflight，
   只发过 ARC HTTP 调用），**但「大概是诚实的」恰恰是那种该由领地主人带着 run 记录去下的判断，
   而不是合并裁判凌晨四点独自下的。**
3. a3 已经**做对过一次同样的迁移**：它在自己加宽 surprise schema 之后重新推导过
   `preflight-20260728T012031Z/MANIFEST.json`（提交 `e843a0fb`，新增 `retired_by_kind`、
   `retired_note`、`surprises_licensing_a_call`、`surprises_retired`）。
   **同一份 manifest 被 a3 迁移过一次，随即被 S29 再打破一次。** a3 知道这活怎么干，
   它只是不知道这活又需要干一次。

## 建议的派单内容（我没做，只建议）

1. **把 `71b882c8` 那段交接的原文告诉 a3 / RES-1**——它从 flag 上看不见。
   活是：合当前 master、重新推导 6 份 manifest（`python -m armtools.backfill`），
   再单独裁 `leg01` 的 `candidates.jsonl`/`trace.jsonl` 那一问。
2. 考虑给 `verify_provenance` 第 8 检查的「逐字节」契约加一个 **schema 版本**，
   这样下一次跨领地加宽字段时，它报的是「按更新的 schema 推导」而不是「档案漂了」——
   **当前的措辞在推导器动了的时候，指控的是档案不稳定。**
3. **过程缺陷值得单独一张单**：把一个明知会红的跨领地改动landed进 master、
   而修复只记录在提交消息里。flag 机制没有任何办法说出「master 是红的，而且不是因为这条分支」，
   于是它把同一条分支重新 flag 了十次。

## 未定项（照抄，不替它抹平）

* **attempts 5–9 的原因不知道。** 我读了 5 个历史版本的 flag 文件，发现它这一生里有**三种不同的红**：
  attempt 1（04:14Z）是 `verify gate red in monitor (verify.sh)` /
  `test_this_repository_is_where_the_survey_says_it_is`；attempts 2–3 是 theoria-arm 的**另一种**失败
  （缺 `leg01` manifest + 未声明的孤儿 scorecard，那是**真的** a3 缺陷，已修）；attempt 4 又是 `monitor`。
  **所以 `attempts: 10` 这个计数器聚合了至少三件互不相关的失败，它不是关于其中任何一件的证据。**
  （这一条对我上一份报告里「attempts 10 = 同一个失败被重放十次」是个修正：更准的说法是
  **这个计数器根本不告诉你它在数什么**。）
* **`monitor/verify.sh` 现在是不是绿的，只有推断没有测量**：`ci_merge` 按 `sorted(dirs)` 遍历、
  遇红即返回，`monitor` 排在 `theoria-arm` 前面，所以 attempt 10 时它必定 exit 0。
  诊断组**故意没跑** monitor 的闸门，因为不能排除 `monitor/verify.py` 会碰 origin，
  而我给的硬规矩高于这次测量。**这个取舍是对的。**
* **重新生成那五份 manifest 是否是「政策上正确」的迁移**：只证明了它**字节上诚实**（纯 schema），
  政策正确性是主人的判断。
* a3 的会话是否还活着，不知道。
* 全部远端 ref 里只有 `a3-campaign-devpile` 碰 `theoria-arm/`，所以没有别的待合分支被这条堵着
  （未检查未推送的本地工作）。
