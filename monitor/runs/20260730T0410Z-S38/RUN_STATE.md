# S38 · append-only 探针的实现与它自己写下的意图，只在 master 上一致

RES-4，infra 赛道，零 API 花费，零封存堆接触。
分支 `agent/s38-append-only-probe-branch-blind`，基线 `origin/master`。
本条目由我在做 S35 时自供——那次是**我自己踩上去的**。

## 1. 先量（要求 1）

`measure.py` / `measure.json`，扫本地 **211** 条分支：

| | 旧判据（锚在 HEAD） | 新判据（锚在 `origin/master` + 本分支净删除） |
|---|---|---|
| 判红的分支 | **26** | **1** |
| 其中假红 | —— | **25** |

已发布删除（`origin/master` 第一父链求和）= **1**，正是 `BASELINE` 里那条已裁决的
主线自我订正（`63ef0bf`，3→4 samples）。**`BASELINE` 里没有任何一条是为压住本条
描述的假红加的**（要求 5 已核）——这很重要，因为那正是这道闸把便宜的错解摆在
顺手位置时，人们会走的那条路。

**留下的那 1 条是 `agent/v26-handover-leak-ruling`。** 它确实原地改写了一段已由
`d35e89cb` 发布到主线的段落。值得单独写下来的是：**同一天由一条完全独立的路径
挑出来的也正是这一条**——S36 里两个 subagent 逐条读 diff 做人工裁决，
在十条分支里把它单独拎出来判「写法不合规」。一个机械判据和一次人工阅读
在 211 条分支上收敛到同一条，这比任何一边单独成立都更有说服力。

## 2. 修了什么

`probe_append_only` 的注释把判据写对了（「once it is on the mainline it is frozen;
on a branch, fix it until it is right」），甚至点名 `6dec6f7` 不该计入。
但实现从 **HEAD** 的第一父链求和，而在分支上那就是这条分支自己的提交，
**包括还没发布的**。于是作者每修正一次自己的草稿段落都被记成一次违反。
在 master 上这个不一致看不见：合并提交的 first-parent numstat 是净变化，
分支内的来回根本不出现——所以那句注释在那里是成立的。

改成两半相加：

* **已发布的删除**：同一个求和，锚在 `origin/master`（`ci_merge` 判祖先用的就是它，
  两处必须用同一个锚，否则又是「同一个问题两个答案」）；
* **本分支自己的净删除**：`merge-base(origin/master, HEAD)..HEAD` 的 numstat。
  **必须用 merge-base，不能用两点 `origin/master..HEAD`**——分支基线落后时，
  两点 diff 会把「基线之后别人加的行」全部报成本分支删的。S35 实测那样算是
  5 增 33 删，而 33 行里一个字都不是它删的。

第二半是这道闸的**牙齿**：一条净删除了已发布行的分支仍然红，而且在它合并
**之前**就红。旧实现在分支上红得毫无分辨力（26 条里 25 条是噪音），
反而让真正该抓的那一类混在噪音里。

没有远端锚点时（新克隆）回落到 HEAD，即旧行为，并把这件事写进 detail
——别让读者以为基础一样强。

## 3. 阴性对照（要求 3、4）

三个，第一个最重要：

1. `test_a_branch_that_deletes_published_lines_is_still_red` —— **这次修复不许把
   闸门拆了。** 一条删掉已发布段落的分支必须红，断言连「本分支净删除 2 行」
   这句理由一起核。
2. `test_a_branch_correcting_its_own_unpublished_paragraph_is_green` —— S35 的形状。
   它先自己算一遍旧判据、断言 `old_dels == 3`，**确认这个 fixture 真的复现了假红**，
   再断言新判据是绿；否则这个测试可能只是在一个本来就绿的仓上通过。
3. `test_the_stated_intent_and_the_code_agree_on_the_mainline_too` —— 回归：
   新锚点没有把「已发布的删除」这一半弄丢。

两个用例各自暴露了一次我写测试时的错，都记下来：

* 第三个用例第一版**只删一行**然后断言红。而 `BASELINE = 1`，删一行等于豁免额，
  判词是绿——它测的是豁免额，不是「主线删除还算不算」。改成两行。
* fixture 第一版只建 `PARTNER_SYNC.md`，于是「文件不存在」那一支先开火：
  判词仍是 `risk`，但**理由完全是另一件事**。它「通过」了状态断言而卡在理由断言上。
  **一个只断言 status 的测试会把两种红混为一谈**——这条经验比这次修的 bug 更通用。

## 4. 一次流程事故，记在这里

本条目开工时我建了 worktree，但**接下来的命令跑在了仓库根目录**（`cd` 没生效），
于是 `monitor/scan.py`、测试文件、`runs/` 全都写进了 **master 的工作树**。
发现后：把 scan.py 的改动导成 patch、把新文件复制进 worktree、
`git checkout -- monitor/scan.py` 还原 master 的树、删掉误建的文件，
再在 worktree 里 `git apply`。已核 master 工作树对这三个路径是干净的。

写下来的理由有两条。一是这违反了 CLAUDE.md「别碰别人在飞的树」的那条精神——
master 的工作树带着整个舰队未提交的状态文件，我在上面改了一个共享模块。
二是**它没有被任何东西挡住**：没有告警、没有闸门，只有我自己回头看 `pwd`。
另有一位 agent 已经为「我改了 master 的工作树」开过 inbox 单
（`20260729T110500Z-RES-2`），所以这是第二例。够两例了，值得有一道闸——
但那是另一件活，不在本条目范围内。

## 5. 验收

```
python -m pytest monitor/tests/test_append_only_probe_anchor.py -q   # 3 个
python monitor/runs/20260730T0410Z-S38/measure.py                    # 211 条分支的普查
python -m pytest monitor/tests/                                      # 397 passed, 2 xfailed
```
