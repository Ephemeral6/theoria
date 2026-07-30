# `.claude/worktrees/` 只在本机被忽略，新 clone 上根本不被忽略

RES-4 / infra / S39 顺手核出来（要求 4），**不是 monitor 领地，不自己改**。

## 事实

```
$ git check-ignore -v .claude/worktrees
.git/info/exclude:11:**/.claude/worktrees/

$ git check-ignore -v .claude          # 退出 1，未被忽略
$ git check-ignore -v .claude/settings.local.json
.gitignore:15:.claude/settings.local.json
```

`.git/info/exclude` 是**每份 clone 独有的、不被跟踪、永不推送**的文件。根
`.gitignore` 里没有任何 `.claude/` 行——只有 `settings.local.json` 那一条。

所以：

1. **任何一份新 clone 上 `.claude/worktrees/` 完全不被忽略。** 那里现在是
   4 个完整检出（其中 `p11-arc-hygiene` 装着三个付费 shard）。
2. `git status` 现在显示 `?? .claude/`，是因为 `.claude/skills/deterministic-figures/SKILL.md`
   未被跟踪且未被忽略——那是一份 127 行的真项目技能，**任何分支上都没有它的提交**。
3. 任何依赖 `git check-ignore` 判定路径归属的闸门，在这台机器上和在别处会给出
   不同答案，而且不报错。

## 为什么值得管

Phase 4 释出清单发布**每一个被跟踪文件**。今天靠的是一份不会跟着仓库走的本地
排除文件挡着；换台机器、或者谁 `git add -A`（CLAUDE.md 已经明令禁止，但那是
自觉条款），四个检出就进了索引。

## 建议（谁的领地谁定）

* 把 `**/.claude/worktrees/`（以及 `.claude/` 下其余 harness 路径）从
  `.git/info/exclude` 挪进被跟踪的根 `.gitignore`；
* 单独决定 `.claude/skills/` 该不该跟踪——它看起来是真产物，不是 harness 残渣。

## 附带：同一次普查里的另一条

`monitor/board.py:634-637`（`prior_work`）**只扫 `.worktrees/`**。它正是那个
专门提醒「这件活可能已经有人在做」的检查，而 `.claude/worktrees/p11-arc-hygiene`
恰恰就是三个付费 shard 待的地方——S36 那个形状原封不动还在。
全仓库另有 8 处非对称的 skip 集合（7 处只跳 `.worktrees`，1 处只跳 `.claude`），
清单在 `monitor/runs/20260730T0440Z-S39/FINDINGS.md` §3。

`prior_work` 在 monitor 领地内，可以修；**S39 没修它**，因为那会把本条目的
验收面偷偷扩大。建议单独下发一件。
