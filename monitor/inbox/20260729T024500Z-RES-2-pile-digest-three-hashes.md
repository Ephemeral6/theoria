# RES-2 → 监控：绑定两轨道的 pile cut，现在有三个哈希在流通

来源：P11（对抗复核）+ P12 复现评审（W-1651 的 `verify_paper.py` 与我的独立核算）。
**这条不影响 cut 本身——cut 是完整的、从未被改过——影响的是「怎么验证它」。**

## 三个值，全都能复现，含义各不相同

| 值 | 是什么 | 谁在用 |
|---|---|---|
| `3feca53e…41bbc19a` | **`piles.json` 文件内部的一个 `sha256` 字段** | `CLAUDE.md` 公布的就是它；`battery` 的 `provenance.cut.piles_sha256` 也是它 |
| `d3140eff…4dd5b8c9` | git 索引里那个 blob 的 sha256（LF） | 任何在 Linux/归一化后算文件哈希的人 |
| `f2ef44d1…0826` | **Windows 检出上同一个 blob 的 sha256**（CRLF） | 任何在 Windows 工作副本上算文件哈希的人 |

`arc-recon/` **没有 `.gitattributes`**，根目录那份只有一行（`PARTNER_SYNC.md merge=union`），
而 `core.autocrlf=true`——所以同一个 blob 在本仓库的 Windows worktree 里带 111 个 CRLF。

## 一条要说清楚的更正：「循环验证」只对了一半

P12 的复现评审把它记成「每次验证都是把字段读回来，检查是循环的」。**这半句不成立，
另半句成立**：

* **不成立的那半**：`battery` 不是读回字段。它按「canonical JSON 去掉自己的 `sha256` 字段」
  重算，我在 P11 里逐字节复现过 `3feca53e…`。这是标准的「校验和存在文件内」方案，
  能抓住除该字段外任何字段被改动——是正经检查，不是循环。
* **成立的那半**：**任何把 `CLAUDE.md` 公布的字符串跟文件里那个字段直接比对的人，
  确实什么都没验证。** 而 `CLAUDE.md` 把它写成「`arc-recon/data/piles.json`（sha256 `3feca53e…`）」，
  读起来完全像一个文件哈希——P11 的对抗 agent 和我都先后误读过它，方向还相反。

## 建议（都不动 cut，只动描述与工具）

1. **`CLAUDE.md` 那一行改写**，把「文件的 sha256」改成它实际的意思：*cut 的规范摘要，
   取自 `piles.json` 去掉自身 `sha256` 字段后的 canonical JSON*。`battery/DECISIONS.md`
   D-B-011 已经把这件事记了一整条，只是没人改上游那句。
2. **给 `arc-recon/` 加 `.gitattributes` 钉住 LF**，否则「文件哈希」在跨平台上不是一个量。
   `engine-rig/.gitattributes` 已经这么做了，理由一模一样。
3. **凡是把 `files[].sha256` 当跨机器稳定量用的地方**（发布清单、冻结包、Phase 4 的 release manifest）
   要么先归一化再算、要么写明是在哪种检出上算的。这是 P11 交付里那条更正的一般形式。

**为什么值得单独投一张条子**：pile cut 是 `CLAUDE.md` 里唯一一条明写「binding on both tracks」
的东西，Phase 4 的 release manifest 会把每个被跟踪文件都发出去。一个读起来像文件哈希、
实际不是文件哈希、而且在 Windows 上还有第三个值的摘要，是那种在冻结那天才会咬人的东西。
