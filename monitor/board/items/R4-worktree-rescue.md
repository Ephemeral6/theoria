priority: 1
cell: P5
territory: theoria-arm

# R4-worktree-rescue · 只存在于工作树里的东西，先救出来再谈清理

十四个 agent 的清理审计（2026-07-29）里，安全复核员**拦下**的那一半比可删清单值钱。
它找出若干**任何 git ref 里都没有过**的产物——`git log --all --diff-filter=A` 对这些
路径全部返回空。一次 `git worktree prune` 或 `git clean -fdx` 就没了。

**这一件必须在任何 worktree 清理之前完成。** 按代价排序：

1. **最贵的一件**：`.worktrees/e3-engines-online/theoria-arm/runs/20260728T083400Z-E3-sk48-carried-v2/`
   —— ledger 自证 `env_upstream=https://three.arcprize.org`、`key_injected=true`、
   **252 次 env_step、30 次 model_call、elapsed 7417.8 秒、281 条 incident**，
   145 个文件全未跟踪，**且没有 MANIFEST.json**。
   这是一次花过钱、花过墙钟的真实在线对局。做两件：补一份符合留痕正典的
   MANIFEST（`prompt_id` / `branch` / `base_commit` / `utc` / `files[].sha256`），
   然后入库。**体积大到不该入库的部分，至少入哈希与摘要，并说明为什么。**
2. `.worktrees/opsm-push` 的 HEAD `a59d5dc0`（"Merge branch opsm/m16-v5v"）
   **不被任何 ref 包含**，唯一的 GC 根就是那棵树；`diff --stat` 是 44 文件
   +4184/−276，一次合并冲突的解决结果。给它一个分支名，推上去。
3. `.claude/worktrees/agent-a84bd79e7c2e1dca9` 里有 V8 分检官层独有的
   MANIFEST.json 与 61,417 字节的 `probe/calib.json`（master 钉的是另一份
   57,713 字节的）。master 的 V8 MANIFEST 自己写着 `fan_out: {examiners: 3}`
   ——**那三个分检官的产物从未合回**。三棵都查，把独有的救回来。
4. 顺手产出一份清单：**还有哪些路径只存在于某棵工作树里**
   （判据：`git log --all --diff-filter=A -- <path>` 为空）。这份清单是
   S30 清理的前置条件，也是这件工单最持久的交付物。

**只增不删**：本件不许删除任何工作树、任何分支。
零 API、零封存堆接触——救出来的那次在线对局是**开发堆 sk48**，不是封存局。
