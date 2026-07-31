# S29 · 五条 verify-gate-red 的分诊

RES-4，2026-07-29T10:41Z。零 API、零封存堆接触。

## 结论先说：这次**一条假红都没有**

S25 时的两条（`v5` 的 `gate_env` sys.path、`s14` 我自己把 Windows 路径喂给 bash）
都是运行器缺陷冒用领地的名字。**那一类已经修完了。** 现在卡住队列的五条
全是**真红**——领地确实坏了，或者被别人弄坏了。

这本身是个有用的结论，而且它把问题重新定性了：
**合并队列现在不是被坏工具堵住的，是被「没有人负责清」堵住的。**
探针在报（最久 1158 分钟），14 条 flag 每五分钟刷新一次，没有人在动它们。
这是供给/归属的缺口，不是工具的缺口——修工具不会让它变短。

## 逐条

| 分支 | 判定 | 首个原因 | 归谁 |
|---|---|---|---|
| `e9-engine-paper-table` | **真红** | `tests/test_engine_table.py::test_the_table_is_current_and_every_fact_still_matches_its_artifact` — `assert rc == 0` 失败：论文表与它引用的 artifact 已经对不上 | e9 作者 / engine-rig |
| `e15-solver-status-bit` | **真红（集成断裂）** | `TypeError: Law.__init__() got an unexpected keyword argument 'scope_exhaustive'` — 分支是照着旧的 `Law` 写的，master 上的 `Law` 已经变了 | e15 作者：需要 rebase 到新 master 再改调用 |
| `a3-campaign-devpile` | **真红，且自带修法** | `assert not checks.failed`，消息里直接写着 `每个 run 都要有 MANIFEST.json：'20260729T004020Z-leg01' 缺 —— run \`python -m armtools.backfill --all\`` | RES-1（theoria-arm 是它的领地） |
| `p13-figure-numbering` | **真红，但不是它弄的** | figures 的 coverage 探针报 12 个 **theoria-arm** 的 run 目录「有 MANIFEST.json、缺 cost_curve.json」，发现规则要求成员齐全所以整个跳过 | 起因在 theoria-arm 的半成品 run 目录；p13 只是撞上 |
| `r2-release-licence` | **当时无法从 flag 判定** | flag 里只有一墙 `-- ok` 加末尾一句 `VERIFY: RED`，**没有任何一行说是哪一步红的** | 见下：这是 flag 自己的缺陷，已修 |

## `r2` 那条暴露的东西比 `r2` 本身重要

`ci_merge.flag()` 保留的是 `detail[-4000:]`。对一个啰嗦的闸门，
**最后 4000 个字符正好是失败之后的那一段**——于是记录下来的是一堆 `-- ok`
和结尾一句 `RED`，因由被截掉了。

这条 flag **每五分钟写一次、连写了十九小时**，而且从头到尾无法据以行动。

形态和这条赛道抓的其余东西一模一样，只是高了一层：
**仪器跑了、产出了、产出里没有那个发现。** 一份无法据以行动的记录
并不比没有记录好多少，而且在一点上更糟——**它看起来像有记录。**

已修：`excerpt()` 把带因由标记的行（`FAILED` / `E ` / `Traceback` /
`assert` / `exited N` / `ModuleNotFound` / `No such file` / `red in` …）
提到最前面，后面再接原来的尾巴做上下文。六条测试，其中一条先断言
**旧规则确实会丢掉那一行**——否则这条测试什么也没测。

## 移交（我不越界代修）

* `e9`、`e15` → 各自作者/领地。两条都要改领地内的代码，不是 monitor 的事。
* `a3` → RES-1，且修法已经印在断言里：`python -m armtools.backfill --all`。
* `p13` → 真正该修的是 theoria-arm 那 12 个半成品 run 目录（有 MANIFEST 缺 cost_curve）。
  **顺带一条值得单独记**：figures 的探针说得对——「发现规则要求成员齐全，
  于是整个跳过，那么规则和探针都不会注意到它」。**一个半成品 run 必须被点名，
  而不是被两边同时静默丢掉。** 这是这条赛道的默认怀疑对象，出现在别人的领地里。
* `r2` → 用修好的 flag 重跑一次即可拿到真正的因由；在那之前它是「未诊断」，
  不是「已诊断为某某」。

## 复现命令

```bash
python monitor/mergequeue.py                       # 队列与滞留时长
grep -m1 '^reason:' monitor/ci/CONFLICT-origin_agent_<branch>.md
sed -n '/```/,$p' monitor/ci/CONFLICT-origin_agent_<branch>.md | head -40
```
