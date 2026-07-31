# C13 的前提已过期；另有两份契约等本轨道会签，没有工单

投递者：`W-1700` · UTC 2026-07-30T05:05:00Z · 分支 `agent/c13-certificate-bridge-two-halves`
底座 `12a48ecc` · 工单 `C13-certificate-bridge-two-halves`（已做完，另见 PARTNER_SYNC）

## 一、C13 的前提是过期的：`probe_a1_state` 报的是 green，不是 partial

工单原文：

> `engine-rig/interop/certificate_export.py` 已经存在，`theory-compiler` 侧有没有消费
> 则由 `monitor/scan.py` 的 `probe_a1_state` 判断——而它长年报 partial。
> （那个探针本身「算了两个布尔却不用于判定」的缺陷已由 S26 修掉，
> 所以**现在它的判决是可信的**，partial 就是真的 partial。）
>
> 做完之后 `probe_a1_state` 的 `bridge` 应当为真、`consumed` 仍可能为假——
> **那正是我们要的状态：我方就绪，等对方**。

**实测：在 `12a48ecc` 上它报 green，`consumed` 为真。** 主树与 worktree 各跑一次，
结果相同：

```
$ python -c "import sys;sys.path.insert(0,'monitor');import scan;print(scan.ROOT);print(scan.probe_a1_state())"
C:\Users\user\Desktop\theoria
{'status': 'green', 'detail': 'engine-rig 侧证书导出：已建；theory-compiler 侧消费：已接。…'}
```

依据是 `theory-compiler/src/theory_compiler/certificate.py:38`：

```python
SCHEMA = "lp_potential/pagoda_certificate@1"
```

——正是 `scan.py:251` 的 `A1_SCHEMA` 要找的串，而 `scan.py:248-250` 的注释本来就
点名了这一行。该文件自 `f58959e7`（2026-07-28T02:47:59+08:00）就在 master 上，
**比工单早两天**；它不在 `runs/` 下，所以 `scan.py:271` 的过滤不适用。

**这条缺陷的形状值得单记，因为它不是「作者算错了」。** S26 之前探针无条件返回
`partial`，无论树长什么样；S26 把判决改成条件式之后，**没有人重跑它**。工单接手的
是修复前那个恒定值，并且在正文里明确写下「现在它的判决是可信的」——把一个**没有
重新测量过的旧读数**，用「测量仪器已经修好」这句话背书了一遍。仪器修好之后要重读，
不是重读之后才算修好。

**本方没有为了让探针变绿动过任何东西**：`monitor/scan.py` 一字未改；
`git diff --name-only origin/master...HEAD -- theory-compiler` 为空，
本分支 acceptance 脚本第 8 组把这条钉在门里。

**建议监控做两件**：

1. 把 C13 的验收条件从「bridge=true, consumed=false」更正为「两半皆真」；
   本工单的四件交付物**全部照原样做完了**，未因此降低任何一条验收线
   （见下「二」）。
2. 查一下网格 C4 的 0% 是从哪个数据源来的。如果它读的是 `probe_a1_state`，
   那么它现在应当不是 0%；如果它读的是别的缓存，那条缓存与探针不一致本身是缺陷。
   **本方没有动网格，也没有动探针**——这条留给监控裁。

## 二、C13 四件交付物照做，没有因为前提变了而缩水

| 工单要求 | 交付 |
|---|---|
| 端到端往返 + 不 import 引擎的独立读取器 | `engine-rig/interop/pagoda_reader.py`（仅 `json`/`fractions`/`os`/`sys`）；`tests/test_pagoda_reader.py` 23 项，含「复制到空目录用 `python -I` 跑」的子进程隔离检查 |
| 格式钉进 `/CONTRACTS/` | `CONTRACTS/pagoda_certificate_v0.1.md`。**零字段变更**——照两端已有代码补写规格，`CONTRACTS/verify.py` 仍绿 |
| PARTNER_SYNC 写清我方就绪 | 已追加 `## [engine-rig] 2026-07-30T05:06:50Z C13-pagoda-certificate-contract` |
| 负样本：篡改必须被拒、合法必须通过 | 七类负样本 + 一份「删证据」伪证：`certificate_export.verify()` 通过它，读取器拒它，**同一读取器改用文档自带动作表时也通过**——判决翻转只因为动作关系接不接地 |

另外两件顺手补的：`interop/certificates/*.json` 此前**没有任何脚本产得出**
（唯一记录是另一个 run 的 manifest 里的一句散文），现在
`python -m interop.export_certificates --check` 三份逐字节重建；`DECISIONS.md`
新增 D-036。全套 `python -m pytest` 577 passed / 27 skipped（基线 554，零回归）。

## 三、提案：ic3 与 deadlock 两份契约等本轨道会签，板上没有对应工单

`CONTRACTS/ic3_certificate_v0.1.md` 与 `CONTRACTS/deadlock_certificate_v0.1.md`
的状态都是「草案，等 `engine-rig` 会签」，`theory-compiler` 分别在
`PARTNER_SYNC.md:353-357`（2026-07-29T06:00:00Z）与 `:631-635`（2026-07-28T08:52:00Z）
明确请求过回复。**engine-rig 至今零回复**：全文 39 个 `## [engine-rig]` 段落里
没有一段提到这两份契约中的任何一份。

两份契约的「谁写哪一半」表里，**发射端归 `engine-rig`、状态「未实现」**——
也就是说这不是签个字的事，是要真写出 `ic3_pdr` / `deadlock_carver` 的导出函数、
落到 `interop/certificates/`。消费端两侧都已完成并跑通（贵方自报 24 项测试含真
Lean 编译）。

**这不属于 C13，本方没有越界去做，也没有在 PARTNER_SYNC 里代表本轨道对那两份
表态**（该段里照录了这一句，免得被读成默认接受）。建议监控开一件工单，
territory `engine-rig`，内容是「为 `ic3_pdr` 与 `deadlock_carver` 各写一个导出
函数并回会签」——两份格式的消费端都已经在等，跟 pagoda 这一份的历史正好相反：
那一份是两端先跑通、规格欠着（现已补上），这两份是规格先写好、发射端欠着。
