# W-1412 · S8 收工：两件需要你派单的事

来自 `agent/s8-provenance-backfill`（theoria-arm 归档补留痕，已完成，9 项 verify 全绿）。

## 1. 一张 scorecard 还开着，需要一次免费 API 调用才能封口

`theoria-arm/runs/preflight-20260728T012031Z` 打开了 scorecard
`bbbd5b57-de5d-4f14-aa0e-adaedb234fef`，此后**没有任何 run 关闭过它**——四次
salvage 针对的是另外三张卡。该 run 的账本记录 0 次 `env_step`，所以「0 个计费动作」
是账本的说法，但**从未经 API 自己的口径确认过**，离线也无法确认。

- 关卡不花动作配额、不花钱，但它是一次**实网调用**，按红线必须先过共享花费闸门；
  我在离线补档任务里不擅自打这一枪，故留给你派单。
- 工具现成：`theoria-arm/armtools/salvage.py`，目标 card id 如上。
- 打完之后 `python -m armtools.backfill --all` 会把回来的 scorecard 自动写进
  该 run 的 manifest，`verify_provenance` 的第 4/5 项会把它纳入对账。

## 2. `agent/e3-engines-online` 分支上还有两个无 manifest 的 run

`20260728T072604Z-E3-sk48-carried` 和 `preflight-20260728T074237Z`。不是本分支的
领地，我没碰。该分支合入 master 后，跑一次
`cd theoria-arm && python -m armtools.backfill --all` 即可补齐；
`verify_provenance` 会在缺失时直接 FAIL，所以漏掉会被拦住。

## 顺带一个可能对别的臂有用的发现

现有 manifest 里的 `base_commit` 记的是**写 manifest 那一刻的 HEAD**，不是 run 实际
跑的那棵树。theoria-arm 四份旧 manifest 全部对不上。`armtools/armversion.py` 用
`run_start` 里记的 `arm_version` 哈希反查提交，可以判定真实提交、或证明该 run 跑在
未提交的工作树上（本臂有两个是后者，不可复现，已如实标注）。

`baseline-arms` 同样零 `runs/` 档案且同样花过钱——如果那边要清偿，这两个模块可以直接
借用（只依赖 `proxy/ledger.py` 和 git，没有 theoria-arm 私有假设）。
