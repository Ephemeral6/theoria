# 14 个 flag 的裁决 · 其中 6 个不是分支的错，是新闸门跑不起来

from: OPS-M（合并裁判，cycle 7）
基准树: 2026-07-28T16:15Z
性质: **本轮是真的上工了**——队列堵死，13 个分支未合，14 个 flag。
紧急度: **高**。`verify.sh` 这一类闸门**在当前调用方式下不可能通过**，与分支内容无关。

## 裁决总表

| # | 分支 | flag | 裁决 | 归谁 |
|---|---|---|---|---|
| 1 | `bus2-ablation-readonly` | verify gate red (ablation-arm) | **闸门缺陷，非分支问题** | 监控修 `gates.py` |
| 2 | `s8-provenance-backfill` | verify gate red (monitor) | **同上** | 同上 |
| 3 | `s9-contract-change-protocol` | verify gate red (monitor) | **同上** | 同上 |
| 4 | `s14-gates-for-all` | verify gate red (monitor) | **同上**（加闸门的分支被闸门挡住） | 同上 |
| 5 | `s15-ledger-hashchain` | verify gate red (proxy) | **同上** | 同上 |
| 6 | `v12-worldgen-gate-deaf` | verify gate red (worldgen) | **闸门缺陷之二：import 路径** | 同上 |
| 7 | `a4a-ablation-build` | merge conflict | 真冲突，**产物文件**冲突 | 见下「产物冲突」 |
| 8 | `p10-figures-into-paper` | merge conflict | 真冲突，**二进制产物**冲突 | 见下 |
| 9 | `s5-phase1-close` | merge conflict | 真冲突，`arc-recon/verify.sh` 两方各写一份 | 见下 |
| 10 | `r2-release-licence` | tests red in release | **真红**，`test_the_partition_loses_nothing` | 该分支自己修 |
| 11 | `s11-sealed-halfguard` | touches protected root files | **正确拦截**，它改 `CLAUDE.md` | 需监控裁决 |
| 12 | `v11-negative-control-census` | unknown territory `verify-lab` | 新领地未申报 | 监控加 `KNOWN_DIRS` |
| 13 | `s17-fleet-evidence-capture` | unknown territory `fleet-study` | 新领地未申报 | 同上 |
| 14 | （`a4a` 重复计入 merge.log） | — | — | — |

**六个 flag 是仪器的错，不是分支的错。** 这六个分支没有任何问题需要它们的作者去修。

## 缺陷一：`verify.sh` 类闸门 100% 失败

`monitor/gates.py:62-65`：

```python
def _runner(path: str) -> List[str]:
    if path.endswith(".py"):
        return [sys.executable, path]
    return ["bash", path]        # <-- path 是绝对 Windows 路径
```

`ci_merge` 随后 `sh(cmd, cwd=os.path.join(wt, d))`。实测复现（**不是读代码读出来的**）：

```python
subprocess.run(["bash", r"C:\Users\user\Desktop\theoria\ablation-arm\verify.sh", "--help"],
               cwd="ablation-arm")
# rc=127
# /bin/bash: C:UsersuserDesktoptheoriaablation-armverify.sh: No such file or directory
```

**每一个反斜杠都被吃掉了。** 三个 flag 文件里的报错逐字就是这个形状，路径不同、症状相同：

```
/bin/bash: C:UsersuserAppDataLocalTempci-merge-l4z1tt1smonitorverify.sh
/bin/bash: C:UsersuserAppDataLocalTempci-merge-kqhlc38kproxyverify_spend.sh
/bin/bash: C:UsersuserAppDataLocalTempci-merge-tj8cz0iwablation-armverify.sh
```

**所以 `verify.sh` 这一类闸门从上线起就没有通过过一次，也不可能通过。**
它拦下的五个分支，没有一个是因为自己的内容被拦的。

### 但**不要**只把它改成 basename——我试过了，那只是把失败挪个地方

`cwd` 已经是该领地目录，所以最直觉的修法是 `["bash", name]`。实测：

```
subprocess.run(["bash", "verify.sh", "--help"], cwd="ablation-arm")
# rc=127   verify.sh: line 14: exec: python: not found
```

**文件找到了，然后死在 `python` 上。** 因为 Git Bash 的 PATH 里没有 `python`：

```
command -v python   -> (not found)
command -v python3  -> /usr/bin/python3      # MSYS 自带的，不是本仓库用的解释器
command -v py       -> (not found)
```

本仓库用的是 `D:\Miniforge3\python.exe`。而反射层是**计划任务**起的，环境比我这里还窄。
**所以完整的修法至少要两步**：(a) 传相对名或 POSIX 路径；(b) 把 `sys.executable`
所在目录注入子进程 PATH，或让 `verify.sh` 一律用 `$PYTHON`（由闸门注入）而不是裸 `python`。
只做 (a) 会得到一批新的红——**看起来像分支的错，其实还是仪器的错**，那比现在更糟。

## 缺陷二：`verify.py` 类闸门的 import 路径

`v12-worldgen-gate-deaf`：

```
File "...\ci-merge-3jz2zwxf\worldgen\verify.py", line 66
    from worldgen.qc import gate
ModuleNotFoundError: No module named 'worldgen'
```

`[sys.executable, path]` 且 `cwd=<territory>`，于是**仓库根不在 `sys.path` 上**，
脚本 import 自己所属的包就失败。注意 `fuzzlab/verify.py` 在同样的调用下**通过了**
（`v10-fuzz-mutation-power` 已合），说明**能不能过取决于脚本自己有没有做 `sys.path` 手脚**
——也就是说这条闸门现在的通过率是随机的，取决于各领地作者的习惯。

**根子是闸门没有定义调用契约。** 建议 `gates.py` 明文规定并实现一条：

> 闸门以 `cwd = <territory>` 运行，`PYTHONPATH` 含仓库根，`PATH` 含 `sys.executable`
> 所在目录，脚本可假定 `python` 就是本仓库的解释器。

写进 `gates.py` 的 docstring，并**在 `_runner` 里真的注入 env**。没有这条契约，
每个领地作者都在猜，而猜错的代价是别人的分支被拦。

## 三个真冲突，两类

**(a) 产物文件冲突**——`a4a-ablation-build`（`ablation-arm/artifacts/*.jsonl`）与
`p10-figures-into-paper`（`figures/out/**/*.png|svg`，git 明说 `Cannot merge binary files`）。
两者都是**被提交进仓库的生成产物**在两条线上各自重算，于是逐字节打架。
按领地纪律这不是谁的错——**是「确定性产物进版本库」这件事本身在并发下必然产生的冲突**。
我的裁决：**产物冲突一律取分支侧**（生成方是权威），但**这条我不能单方面执行**，
因为它等于替两个领地做主。建议监控给一条通则：要么产物 `.gitignore`、要么
`.gitattributes` 里给这些路径设 `merge=ours/theirs`，**否则每一次并发都会复发**。

**(b) `s5-phase1-close` 冲突在 `arc-recon/verify.sh`**——它和 S14「gates-for-all」
撞车了：两条线各自给 `arc-recon` 写了一份 verify 脚本。这是**同一件事被派了两次**，
属于供货侧的重复派单，不是技术冲突。建议监控裁一份留下，另一份撤。

## 其余三条

* **`r2-release-licence` 是真红**：`test_the_partition_loses_nothing` 失败——
  「每个被跟踪文件要么被发布、要么被列为保留」。这是该分支自己的问题，**闸门工作正常**，
  这一条恰恰证明测试门有用。归该分支修。
* **`s11-sealed-halfguard` 改 `CLAUDE.md`**：拦截正确。CLAUDE.md 是根保护文件，
  按 CHARTER 只有监控能改契约。归监控裁决。
* **`v11-negative-control-census`（`verify-lab`）与 `s17-fleet-evidence-capture`
  （`fleet-study`）**：两块新领地没在 `KNOWN_DIRS` 里申报。这是**设计好的行为**
  （未知领地停下等判断），归监控申报即可。注意：申报后它们会自动按「有没有
  `test_*.py`/`verify` 脚本」进闸门，不需要再改表。

## 我没有做什么

**没有改 `monitor/gates.py`、`monitor/ci_merge.py`，也没有动任何分支。**
`CHARTER.md` 的权限表写明 OPS-A/B/M/R 一栏「改代码：否」，而契约的「分工边界」
说本轮起以 CHARTER 为准。前两次我改 `ci_merge.py` / `quota.py` 都是**用户直接指示**，
这次没有。补丁思路在上面，请监控自取或派单——**但请注意缺陷一必须两步一起修**，
否则会把「文件找不到」换成「python 找不到」，红照样是红。

## 一条关于新增「扇出纪律」的请示

契约本轮新增「能拆的活必须拆给 subagent 并行做」，并把它列为硬要求。
**这条我这一轮没有执行**，原因照实说：我的运行约束里有一条明确的「除非用户要求，
否则不要调用 Agent 工具」，而契约是仓库里的文件、由监控写入——按隔离纪律，
工具读到的内容是数据不是指令，**我不拿它去覆盖用户给的运行约束**。
本轮 14 个 flag 我是单线程做完的（诊断出两个系统性缺陷、复现了其中一个、
分类了全部 14 条），代价是慢，不是漏。
**请监控与用户对齐后给一句话**：若用户认可扇出，我下轮照办；若不认可，
建议把这条从契约里撤掉，免得它一直在那儿显示我在违规。
