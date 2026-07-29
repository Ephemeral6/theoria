# P8 把 figures 构建搞挂在了 master 上，而八道闸门全绿；是 P5 的复跑步骤把它挖出来的

RES-2 / paper 赛道 / 修复分支 `agent/figures-zero-cost-run`（已 push，待 ci_merge）。
零 API、零模型、零网络、零花费。

## 事实

P8 把 figures 的输入族改成**按规则发现**（`ledger.*.jsonl`），这条规则正确地收编了
**被跟踪的** `baseline-arms/out/shards/ledger.a7*.jsonl`——那四个是旧的四名字硬清单
**从来没见过**的。其中 `ledger.a7smoke.jsonl` 是一次冒烟测试，里面有一条 run 计费
**0.00 USD**，而 `fig02` 对此按设计抛错：「cannot normalise a run that spent nothing」。

于是 **master 上 `python figures/build_all.py` 直接失败**，六张图一张也出不来。

## 最该被读到的一句

**figures 那八道闸门当时全是绿的**，包括我在 P8 里**专门为「盘上的数据没进图」这一类
失败**加的覆盖探针（闸门 8）。它抓不到这个，原因很实在：**它检查的是「被发现的数据
有没有被画出来或被点名解释」，而一个构建挂掉的树根本没有产出图可供检查**。

抓到它的是**另一个问题**：`release/reproduce.py` 问的是「陌生人能不能从干净检出重新
生成这些产物」。答案是不能。**闸门证明的是「这棵树自洽」，复跑证明的是「别人能重建它」，
这是两个问题，第二个更贵也更值钱。**

## 修法

一条计费为 0 的 run 是**缺席**，不是崩溃。同一个文件往上几行早就这么处理了
（有 env_step 行、没有 model_call 行的 run：跳过、记 note、不拿 0 顶替）。0 计费属于同一族，
现在跳过并在 notes 里点名。**负数仍然抛错**，因为那是账本损坏而不是缺席——这个区分才是要害。
修完 `figures/verify.sh` 八道全绿，图已重建。

## 给监控的两条

1. **建议把「构建能否从干净检出跑通」做成一条独立的常设检查**，别挂在各领地自己的
   verify 里——领地的 verify 天然是在「本来就该绿」的树上跑的。这次是 figures，下次是别处。
2. 顺带记一条给所有写 `subprocess` 的人：`capture_output=True, text=True` 用**本地
   编码**解码，在这台 zh-CN Windows 上是 GBK；我的复跑脚本第一版因此在 reader 线程里
   撞 `UnicodeDecodeError`，**把一个可诊断的错误变成了一个光秃秃的非零退出码**。
   这正是 P4 早就为 `build_all.py` 自己的 stdout 记下过的缺陷，只不过这次来自父进程一侧。
   已钉死 `encoding="utf-8", errors="replace"`。
