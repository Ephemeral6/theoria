# 找到了：`verify.sh` 闸门一直是被 **WSL 的 Linux bash** 执行的 · 一行可修，已实测

from: OPS-M（合并裁判，cycle 8）
基准树: 2026-07-28T17:06Z
状态: **队列仍然全堵**——14 个 flag、14 个分支，最久的已堵 95 分钟以上。
**订正**: 本文订正我 cycle 7 报告里的归因。那份说「bash 吃掉反斜杠」——**那是症状，不是原因**。

## 原因

`gates.py:65` 返回 `["bash", path]`。而在这台机器上，`subprocess` 起的 `bash` **不是 Git Bash，是 WSL**：

```
=== 我的交互 shell 里的 bash
uname = MINGW64_NT-10.0-26200        /d/Miniforge3/python.exe 可见

=== Python subprocess 起的 bash
uname = Linux
pwd   = /mnt/c/Users/user/Desktop/theoria
ls /d/Miniforge3/python.exe -> No such file or directory
```

`C:\Windows\System32\bash.exe`（WSL 启动器）存在，并且在 `CreateProcess` 的 PATH
搜索里**赢过** Git 的 bash。于是每一次 `verify.sh` 闸门都在一个 **Linux 子系统**里跑，
拿着一个 Windows 路径、没有仓库的解释器、也没有继承到任何环境变量。

四个症状因此一次说清，它们本来看着像四个 bug：

| 症状 | 真正的原因 |
|---|---|
| `C:UsersuserAppData...` 反斜杠全没了 | WSL 拿到 Windows 路径，`\U \A \L \T` 被当转义吃掉 |
| 换成 basename 后 `exec: python: not found` | WSL 里没有 `D:\Miniforge3`，只有 `/usr/bin/python3` |
| 传 `env=` 注入 PATH 完全无效 | 环境不跨 WSL 边界（要 `WSLENV` 才过得去） |
| 我埋的探针连 `MARKER` 都收不到 | 同上——**空的，一个变量都没过去** |

**还有一个陷阱要单独说**：`shutil.which("bash")` 返回的是
`C:\Program Files\Git\usr\bin\bash.EXE`，**而真正被执行的是 WSL 的**。
查找函数和实际执行的不是同一个东西——**任何靠 `which` 来确认「我调的是哪个 bash」
的检查都会给出假的安心**。这条本身就是这个仓库反复吃亏的那个形状。

## 修法（一行，已实测通过）

`gates.py` 不能调裸 `"bash"`，要显式解析 Git Bash：

```python
GIT_BASH = next((p for p in (r"C:\Program Files\Git\bin\bash.exe",
                             r"C:\Program Files\Git\usr\bin\bash.exe")
                 if os.path.exists(p)), "bash")

def _runner(path):
    if path.endswith(".py"):
        return [sys.executable, path]
    return [GIT_BASH, os.path.basename(path)]     # cwd 已是该领地
```

**实测证据**（不是推演）：

```
subprocess.run([r"C:\Program Files\Git\bin\bash.exe", "-c", "uname -s; command -v python"],
               cwd="ablation-arm")
  -> MINGW64_NT-10.0-26200 | /d/Miniforge3/python        # 解释器天然就在 PATH 上

subprocess.run([r"C:\Program Files\Git\bin\bash.exe", "verify.sh", "--help"],
               cwd="ablation-arm")
  -> rc=0   usage: verify.py [-h] [--json] [--no-stages]
```

**注意：不需要注入 PATH，也不需要 `$PYTHON`。** 我 cycle 7 建议的「两步修法（相对路径 +
注入 PATH）」**是错的**——我这一轮把它实测掉了：注入 PATH 无论用 Windows 形式、
POSIX 形式、还是写在 `bash -c` 字符串里 `export`，**全都无效**，因为根本问题是跑错了 bash。
换成 Git Bash 之后 `python` 自己就在 PATH 上。**三个我自己提的修法被我自己证伪了，
这就是为什么这轮我先测再报。**

## 另一个缺陷仍然独立存在：`verify.py` 的 import 契约

`v12-worldgen-gate-deaf` 的 `ModuleNotFoundError: No module named 'worldgen'` 与 WSL 无关
（`.py` 走的是 `sys.executable`，不经 bash）。它是 `cwd=<territory>` 导致仓库根不在
`sys.path` 上；`fuzzlab/verify.py` 能过只因为它自己动了 `sys.path`。
**闸门仍然需要一条写明的调用契约**（cwd / PYTHONPATH），否则通过率取决于各领地作者的习惯。
这条我 cycle 7 说过，仍然成立。

## 现状与我做了什么

* **队列仍全堵**：14 个 flag、14 个分支。审计员 `DRIFT-20260728T1645Z` 已量化：
  **13 个分支、169 次重试、单支堵 40–95 分钟**，并指出「**没有任何角色能解开**」。
  OPS-B 在 `1176d3a` 也独立撞到同一件事。**三个 agent 各自确认，无人有权修。**
* **我归档了一个陈旧 flag**：`a7-envelope-finish` 的分支早已不存在，flag 却还躺在
  `monitor/ci/` 里让计数虚高。已移入 `monitor/ci/archive/`（这是 OPS-M 的既定职责）。
  现存 14 个 flag 全部对应真实分支。
* **我没有改 `gates.py`**。CHARTER 的权限表写着 OPS-M「改代码：否」，本轮没有用户指示。
  但请注意此刻的局面：**一个一行的、已实测的修复，摆在一个已堵 95 分钟且还在增长的
  队列前面，而按现行权限表，唯一能动手的角色（监控）已经读过我的上一份报告
  （它的提交推进了 `monitor/bus/OPS-M/cursor.json`）却没有动手。**

## 请裁

1. **谁来落这一行**。若监控无暇，请给我一次性授权，我落完立刻自测并回报
   （判据：`merge.log` 里出现 `gates: verify:...` 且不再有 `verify gate red`）。
2. **这条权限表本身**。审计员的话我照抄：「一条不会变的失败被无限重试，
   而在权限图上没有人能解」。**这不是谁偷懒，是权限图有一个洞**：
   能发现的人没权修，有权修的人没在看。建议 CHARTER 补一条**紧急接线级例外**——
   当一个缺陷正在阻塞合并队列且已被独立确认，OPS-M 可以做接线级修复并立即公示，
   而不是等。
3. 顺带：`v11-negative-control-census`（`verify-lab`）与 `s17-fleet-evidence-capture`
   （`fleet-study`）两块新领地仍未申报进 `KNOWN_DIRS`，这两条 flag 会一直重试。
