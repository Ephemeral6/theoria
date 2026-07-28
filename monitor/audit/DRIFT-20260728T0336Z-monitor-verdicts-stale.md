# DRIFT-monitor-verdicts-stale

severity: medium
dimension: 监控自身漂移（`monitor/spec.py` 手写判断与 `monitor/scan.py` 探针判据与树上实况脱节）

evidence: 审计基准 `HEAD=7c55c09`（2026-07-28T03:36Z）。`monitor/spec.py` 最后一次改动是 `153d5f3`，早于 `e33e71a`(P-11) / `f7830ed`(P-13) / `2a2c471`(P-14) 三个合并——手写 note 因此停在合并前的世界。

1. **`p1-cut` 的 note 说 F-11 未落账，但已落账。** `monitor/spec.py:105-109` 写「F-11 裁决（主张集 21→19）**尚未落账**——contamination_log 还没有那 9 局的登记 → P-11」，据此把该项钉在 `status: risk`。树上：`arc-recon/data/claim_set.json` 已是 `"claim_set_size": 19`，`quarantined` 含 ls20/ft09，`contamination_log.jsonl` 已含 9 局登记（`git log` 见 `29c631e` "F-11 on the books"）。同项的机器探针 `pile_integrity` 报 green，是手写 note 单方面把它拉红的。

2. **`p1-engines` 的 note 说 FD 是桩，但 FD 已连。** `monitor/spec.py:144-145`「FD 是 grounded-STRIPS BFS 桩，接口同形但『白捡二十五年规划工程』这句话目前不成立」。树上：`cf400ce` / P-13 已把 Fast Downward 24.06+ (`7120aa01`) 真编译接入，`engine-rig/STATUS.md:120-151` 记三级梯子（stub-bfs / fd-optimal / fd-satisficing），溯源在 `engine-rig/runs/p13-fd-real/TOOLCHAIN_MANIFEST.md`。**同一条陈旧还在 `CLAUDE.md:110`**（"Fast Downward is not connected"）——那是每个新会话开局就读的文件，陈旧代价比 spec.py 更高。
   （附一条不算漂移但值得记的实况：`.toolchain/` 按设计 gitignored，所以**主工作树上 FD 不可达**，`engine-rig/STATUS.md:71` 自己写明「255 passed with FD reachable; 252 passed, 3 skipped without」。这是诚实的写法，无需处理。）

3. **`credential_hygiene` 探针把一个合规的 worktree 副本判成泄漏。** `monitor/scan.py:88-115` 遍历全树，凡文件含密钥值即报 `risk`；当前命中 `.claude/worktrees/p11-arc-hygiene/.env`，`monitor/state.json` 因此把 `p1-seal-test` 涂成 risk。复核：`git check-ignore -v` 命中 `.git/info/exclude:11:**/.claude/worktrees/`，且根 `.gitignore` 的 `.env` 规则本身在任意层级都匹配；`git ls-files --error-unmatch` 确认该文件**未被跟踪**。`CLAUDE.md` 的红线是「never write the key's value into any **tracked** file」，Phase 4 释出清单只发布已跟踪文件——这条没有被违反。

claim: 监控对自己盘子里三格的判断是错的：两处手写 note 停在合并前（其中一处同样污染了 `CLAUDE.md`），一处探针把 gitignored 的 worktree 副本当泄漏。方向都一样——**都是把已经变绿的东西继续报红**。单看每一条都无害，合起来的后果不无害：`p1-seal-test` 那格会永远红着，等真出现一次密钥泄漏时，它和现在这条假阳性长得一模一样。

suggest:
1. `p1-cut` 的 note 重写为「F-11 已落账（claim_set 19，ls20/ft09 隔离，9 局登记在册）」，status 交回探针 `pile_integrity`（green）。
2. `p1-engines` 的 note 与 `CLAUDE.md:110` 的 standing caveat 同批订正为「FD 已连，三级梯子；`.toolchain/` 不入库，故未装机器上退到 stub 并跳过 3 个测试」。`CLAUDE.md` 属仓库共享面，改动请走监控自己的手，不要派给执行会话顺手改。
3. `probe_credential_hygiene` 加一道 `git check-ignore` 过滤：**已被忽略的路径不算泄漏，但要单列成 `note` 而不是消失**（例：「密钥另有 1 处工作副本，均在 gitignore 内：.claude/worktrees/...」）。这样红色重新只留给真泄漏，而副本扩散仍然可见。
4. 更根本的一条：凡带 `probe` 的条目，手写 note 与探针结论矛盾时，**以探针为准并把矛盾本身报出来**。这次三条里有两条正是「探针绿、手写红」，机器早就知道了。
