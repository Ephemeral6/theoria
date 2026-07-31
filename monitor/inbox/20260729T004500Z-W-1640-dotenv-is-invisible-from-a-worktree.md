# 任何 worktree 里的会话都摸不到 `.env`——而仓库的约定就是在 worktree 里干活

工人 W-1640，工单 A3-campaign-devpile，UTC 2026-07-29T00:45Z。
`proxy/` 不是我的领地，只报不改。

## 现象

从 `.worktrees/a3-campaign-devpile/` 启动第一次真跑，立刻死在：

```
RuntimeError: ARC_API_KEY is not set. Put it in
C:\Users\user\Desktop\theoria\.worktrees\a3-campaign-devpile\.env
(gitignored) -- never in a tracked file.
```

## 原因

`proxy/redact.py:242` 的 `read_secret(name, env_path=DOTENV)`，`DOTENV` 是相对
**当前 checkout 根**解析的。而 `.env` 是 gitignored 的，所以它**只存在于主
checkout**，`git worktree add` 不会带过去，将来也不会。

于是：**CLAUDE.md 要求把工作放在 `.worktrees/<slug>/`（「桌面上不许再长出
theoria-* 目录」），而这条约定使得任何需要凭据的运行开箱即死。** 两条规矩互相
拆台，谁都没错。

## 已经有一份正确实现，就在隔壁文件

`proxy/spend_gate.py:71` 的 `main_checkout(start)` 正是干这个的：linked worktree
的 `.git` 是**文件**不是目录，里面写着 `gitdir: <main>/.git/worktrees/<name>`，
顺着它就能拿到主 checkout 根。spend gate 靠它把 `proxy/var/spend_gate.jsonl`
解析到主 checkout——所以**花费池在 worktree 里是通的，凭据不通**。

建议：`redact.py` 的 `DOTENV` 走同一条路——先看本 checkout，没有就回退到
`main_checkout()`。一行逻辑，和 spend gate 完全同构。

## 我这次的绕法，以及为什么不建议当成解法

按 CLAUDE.md 写的 `set -a; . ./.env; set +a`，从**主 checkout** 把变量导进进程
环境；`read_secret` 第 246 行 `load_dotenv(env_path).get(name) or os.environ.get(name)`
有环境变量回退，所以能跑。

**没有**把 `.env` 复制进 worktree。虽然 worktree 里那份 `.gitignore` 同样会忽略
它，但把凭据在磁盘上多复制一份，正是 Phase 1 封存纪律要避免的事——密钥的副本
越多，将来某次 `git add -f` 或某个打包脚本把它带出去的概率越高。

绕法的问题是它**不留痕、不可复现**：下一个会话不会知道要先 source 主 checkout
的 `.env`，只会看到同一条报错，然后可能选择复制文件那条更危险的路。所以这件事
值得在 `redact.py` 里修一次，而不是让每个工人各自绕一遍。

## 顺带一条，同一次真跑里发现的

`Run.__exit__` 在 `finally` 里释放预留，但 **SIGTERM 跳过 finally**。我用前台
超时跑了一次证明性运行，被十分钟的上限杀掉，于是：

1. 一条正在飞的 haiku 调用按 `MODEL_CALL_CEILING_USD` 记了 **$4.00**（真实成本
   约 $0.15）——这是策略正确工作（「否则等于假设它没花钱」），不是缺陷；
2. 预留**泄漏为 live**，$5.50 的共享额度被一个已经不存在的进程占着。TTL 3600 秒
   会自己过期，但在全队共用的池子里这不够好。已手动 release 并写明原因。

含义给监控：**长时真跑必须后台运行，不能挂在任何前台超时下**；以及池子里如果
出现 holder 进程已死的 live 预留，那多半就是这个。是否值得给 `spend_gate` 加一
条「holder pid 不存在则视为可回收」的清扫，由 proxy 轨道判断。
