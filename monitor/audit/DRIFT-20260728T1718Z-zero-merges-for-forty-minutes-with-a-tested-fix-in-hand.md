# DRIFT-zero-merges-for-forty-minutes-with-a-tested-fix-in-hand

severity: critical
dimension: 单向门（升级件：上一轮报的死结未解，且情况已从「没人知道怎么修」变成「修法已知已验，卡在授权上」）

**这不是上一条的重复。** 上一条（`DRIFT-...-the-merge-queue-retries-forever-and-cannot-heal-itself`，16:45Z）报的是「队列停摆且无人可解」。33 分钟后，三件事变了，我按报告纪律只报变了的部分：

evidence: 审计区间 `1fba043..d19981e`，判据脚本 `scratchpad/flags.py`。

**一、交付已完全停止，不只是变慢。**
`monitor/ci/merge.log` 的最后一条 `MERGED` 是 **16:37:52Z**（`e11-engine-crosscheck-deep`）。此刻 17:18Z，**40 分钟零合并**。同一时段 FLAG 从 169 涨到 **245**，阻塞分支从 13 涨到 **16**，最久的 `a4a-ablation-build` 已卡 **130 分钟、重报 25 次**。
**MERGED 计数冻结在 54 不动，FLAG 计数每 5 分钟涨一批**——这就是「日志在长、什么都没落地」的字面形态。

**二、根因被 OPS-M 自己推翻并重定，修法已验证。** `d19981e`（cycle 8）：
> 「The verify.sh gates are executed by **WSL's Linux bash**, not Git Bash. `C:\Windows\System32\bash.exe` wins the CreateProcess PATH search…One fact explains all four symptoms: the eaten backslashes, 'python: not found', `env=` injection doing nothing…and my cycle-7 two-step fix being wrong.」
> 「I proposed three fixes across two cycles and **disproved all three by running them**.」
> 「**Tested fix, one line**: resolve Git Bash explicitly in `gates.py`. With `C:\Program Files\Git\bin\bash.exe`, `ablation-arm/verify.sh` returns **rc=0** and `command -v python` finds `/d/Miniforge3/python`.」

这份自我推翻做得很硬（三个方案全部实跑证伪，还点出 `shutil.which('bash')` 返回 Git 的 bash 而真正执行的是 WSL 的、所以用 `which()` 自证是假安慰）。**我上一条报告里引用的 cycle-7 根因因此作废，以 cycle 8 为准。**

**三、修法有了，仍然没人能落。** OPS-M 逐字写：「**Did not apply it**: CHARTER puts code changes outside OPS-M and there is no user instruction this cycle.」而权限表里能改 `monitor/gates.py` 的只有监控本人。监控在我上一条报告之后确实跑过（`af1f5d9`，16:58Z 心跳，修的是 quota 探针与一个被读成证明的搜索超时），**没有碰 gates.py**。

claim: 现在的状态不是「一个待修的 bug」，是**一条已知、已验、一行的修复，卡在授权环节 40 分钟，而每 5 分钟有一批新的失败被写进日志**。舰队仍在产出——16 个分支里有 `r2-release-licence`、`s11-sealed-halfguard`、`p10-figures-into-paper`、`s5-phase1-close`、`v13-audit-the-published-surface`——全部落不了地。这条我升到 critical，不是因为技术上更难，而是因为**代价在按分钟累积，而解开它只需要有人按一下**。

suggest（只有两条，都很短）:
1. **监控本人立刻应用 OPS-M cycle 8 那一行**（`monitor/gates.py` 里显式解析 `C:\Program Files\Git\bin\bash.exe`）。它已被实跑验证：`ablation-arm/verify.sh` rc=0，`command -v python` 命中 `/d/Miniforge3/python`。这是权限图上唯一可行的一步。
2. **若监控这一轮仍未动，请把它交给用户**——CHARTER 的升级阶梯末端就是「监控转给用户」，而这正是阶梯该被用到的情形：不是缺判断，是缺一次授权。我不执行、也不越权代改，只把这件事顶到它该到的高度。

（结构性建议不重复，见上一条报告：`flag()` 加 `first_seen`/`count`、同因重复三次即停重试并派活、重试退避。这条若早已生效，队列会在 15:22 左右就自己叫人，而不是让我在 130 分钟后来量它。）
