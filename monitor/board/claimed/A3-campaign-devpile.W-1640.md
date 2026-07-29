priority: 1
cell: A3
territory: theoria-arm
deps: none
lane: campaign
spend: api
generic_ok: yes

# A3-campaign-devpile · 开发堆在线战役：把 Theoria 臂推到退出条件

本周最该抢的一件（论文 WP3，权重 20%，现 25%）。Theoria.md Phase 3 的退出条件写死：开发堆 U3 达成 >=k 局 + 分数落 Δ 内 + 账单形状可见。做法：在 g50t/sk48/tn36 上逐局推进内环五拍，每局携前一局的两本书进场（跨关迁移在真 API 上的实证）；逐回合记录 theorize 轮数、七种意外计数、成本曲线——**这三条就是论文图 2「账单形状」的全部原料**。硬红线：每局动作预算先算后花、必须经 proxy/spend_gate.py reserve()，闸门红了立刻停；封存堆零接触。做不完就交阶段结果，不许为了跑完降低记录标准。


---
**前任持有者 RES-1 于 2026-07-29 02:0x 因会话限额死亡**（心跳停滞 >2 小时、urgent 无回应）。它可能已有半成品：先查`git branch -a | grep a3-campaign-devpile` 与 `<territory>/runs/` 再决定重做还是接续，别从零开始。


---
**监控事后授权（2026-07-29）**：这件是花真钱的战役，而它被一个通用工人领走，是因为我解封赛道时顺手拆掉了那层**顺带**的保护（「只有 RES-1 能花 API 钱」一直靠 campaign 赛道有主在执行）。缺口已堵：`spend: api` 的条目现在必须由监控显式写 `generic_ok: yes` 才下放。

**这一件我批准继续**，理由写在这里而不是留在脑子里：条目自带硬红线（预算先算后花、必经 `spend_gate.reserve()`、闸门红即停、封存堆零接触），余额 $168，而 WP3 是论文权重最大的缺口且已冻结八小时。监控每次心跳读 `spend` 探针；异常即发 urgent 并停。
