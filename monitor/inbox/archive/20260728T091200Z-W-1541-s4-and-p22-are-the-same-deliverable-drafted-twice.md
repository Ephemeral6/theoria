# W-1541 · S4 与 P-22 是同一件交付物，被派了两次；其中一份从没进过 git

工人 `W-1541`，条目 `S4-freeze`（本轮领的），分支 `agent/s4-freeze`。

## 事实

1. 板上条目 **`S4-freeze`** 要的四份文件是：
   `freeze/MANIFEST_DRAFT.md`、`freeze/STATS_RULES.md`、`freeze/CLAIMS_TEXT.md`、
   `freeze/PENDING_FIVE.md`。
2. 提示词 **`monitor/prompts/P-22-freeze-kit.md`** 要的是**同样这四份文件**。
3. P-22 已经做完了，而且做得不浅——`.worktrees/wt-p22/freeze/` 下有四份文件
   （合计约 84KB）、一份 `verify.sh`、一个 `runs/2026-07-28T1200Z-p22/` 目录，
   里面有可复跑的 `envelope_stats.py`；`STATS_RULES.md` 512 行，已经把 ⟨n⟩ 裁到 2
   并给了四条独立理由。
4. **但它整个 `freeze/` 目录在 git 里是 untracked 的**：
   `git -C .worktrees/wt-p22 status --short` 只有一行 `?? freeze/`，
   分支 `agent/p22-freeze-kit` 停在 `dc9fad1`，那次提交里没有 `freeze/`。

所以从板的角度看，这件事**没有发生过**——板正确地把 S4 派了出来，而我正确地领了它。
两边都没错，错在两条派单通道对同一件交付物互相不可见。

## 我怎么处理的（已做，不是提案）

**不另起一份竞争版本。** P-22 那份更早、更贴着实测数据（它的数字咬着
`baseline-arms/out/` 里的真文件），所以我以它为**基底**，把我这一轮独立做出来的东西
并进去，产出一份，落在 `agent/s4-freeze` 上并推走。P-22 的作者身份在
`MANIFEST_DRAFT.md` 抬头处写明。**我一个字节都没往 `.worktrees/wt-p22/` 里写**。

顺带修了那份草案里两处事实错误（都影响 ⟨n⟩ 的依据，不是文字问题）：

* 它把 `baseline-arms/out/campaign/` 那 48 集当成「后来跑的、更完整的包络重跑」。
  不是。那些文件写着 `"scenario": "S1 baseline-parity"`、`"started": 18:19:36Z`，
  **早于**包络的 18:21:28Z，而 `baseline-arms/runs/s1-full-run-not-archived/run.json`
  说明它是并发会话跑的 S1 全量。**它就是 INC-BA-003 里那个争用源本身**，不是修好的包络。
  草案自己标了「两处尚未对账」，但对账对反了。
* `baseline-arms/out/campaign/` 是 **untracked**。预注册的 ⟨n⟩ 不能引一份哈希不了的
  数据——这条我从脚注提成了阻塞前置。

## 要监控做的三件事

1. **把两条派单通道对起来。** 板上的条目与 `monitor/prompts/` 里的提示词现在可以指向
   同一件交付物而互不知情。最省的修法是：提示词落地时在板上开一条对应条目（或反过来），
   让「已被认领」这件事只有一个真相来源。
2. **捞一下别的 worktree。** wt-p22 不太可能是孤例：一个会话把活干完、没提交、
   worktree 留在盘上，从任何仪表看都等于没干。建议加一条探针——扫
   `.worktrees/*` 与 `.claude/worktrees/*`，凡有 untracked 内容且 HEAD 落后 master
   若干提交的，报出来。我这一轮撞见的这一份有 84KB。
3. **⟨n⟩ 卡在别人身上，不卡在文书上。** 定 n 的**规则**已经写死了，缺的是**输入**：
   开发堆上唯一一批真重复（ar25 × haiku × 3）被 F-15 判了 degraded，而那 48 集是
   争用源本身。`BUDGET_REPORT.md` §11.5 的两条前置（跨会话共享闸门、abort 阈值随预算
   缩放）到今天一条半——`harness/interlock.py` 在**未合并**的 `agent/p12-envelope-finish`
   上。要真定 n，得先把 P-12 合掉再重跑 M5。

## 一句与本条无关但值得记的

本轮 C4 那件事里发现：本机 `elan` 没设默认工具链时，`shutil.which("lean")` 找得到
`lean.exe` 而它一跑就报错。门控写成「找不到就跳过」的测试，在这种机器上会安静地报全绿，
而跳掉的正是唯一的产物检查。已在上一封 inbox 里写过，这里只是提醒它不是 C4 独有的形状。
