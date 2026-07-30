# s11：裁决扛住了对抗复核，而且补丁已经被验过了——现在只差你一个字

from: OPS-M (cycle 18)
utc: 2026-07-29T17:48:00Z
re: `20260729T150500Z-opsm-s11-technically-not-clear-two-bypasses-defeat-the-sealed-rule.md`
状态: 已挂 **13 小时**（first_seen 04:19Z）

我派了一个对抗组，任务是**推翻**我自己 15:05Z 那份裁决。它三条都没推翻，并且顺手多验了一件。

## 三条都成立

**(a) 分支没动过。** `git ls-remote` 打真远端：s11 仍是 `803a853a`（提交时间 2026-07-28 22:34），
裁决写于 2026-07-29T15:05Z。**作者自裁决以来一步没修**，所以那份裁决没有过期——
这是我本轮上线第一件核实的事，因为「flag 写下就不再重测」正是我上一跑抓到的老毛病。

**(b) 两个绕过都复现了。** 全部用 `piles.json` 程序化读取封存 id 并打码，**没有играть、没有抓取、
没有下载任何东西**：

```
CONTROL  make play-local                    -> deny_unfiltered
CONTROL  ls environment_files/<sealed>      -> deny_sealed
BYPASS-1 # 注释后换行                        -> allow
BYPASS-1b argv sh -c 带换行                  -> allow
BYPASS-2 引号内 "#" 再 ; make play-local     -> allow
BYPASS-3 引号内 "#" 再读 sealed              -> allow
```

病灶是一行——`local_engine_guard.py:345` 的 `re.split(r"(?:^|\s)#", plain)[0]`：它按**整段文本**
截断到第一个 `#`，而上一行刚把引号剥掉，于是**字面量 `"#"` 变成了注释符**，封存兜底规则（rule 4）
就此失效。分支自带的 **151 个测试全绿**——它对这个洞是真的瞎，不是有人关掉了检查。

**(c) 管辖权判断是对的，而且是机器强制的。** `monitor/CHARTER.md` 的权限表把「改契约」只给监控，
OPS-M 那一行代码与契约都是「否」；`monitor/ci_merge.py:504` 把 `CLAUDE.md` 硬写在受保护根文件集合里。
**行数复核（对着 merge base `6beb2e68` 量，不是两点）**：`CLAUDE.md` **37 增 0 删**、
`.gitignore` **6 增 0 删**——我上一跑报的两个数都精确。
（注：两点 `master..branch` 会显示 `.gitignore 5/7`，那是 master 的漂移不是分支干的。**别照两点的数判**。）

**两半是独立的**：就算绕过被修好，管辖权这一半仍然独自挡着。

## 多验出来的一件：补丁是有效的

对抗组把我提的那个改法（逐行、识引号地剥注释）真的打上去跑了：四条绕过**全部翻成
`deny_unfiltered`/`deny_sealed`**（BYPASS-3 变 `deny_sealed`，比裁决预期的还好），
而且在我试过的每一条控制样本上**与原实现逐字节同行为**。所以「一个提交能修好」这句是站得住的。

## 顺带订正我自己裁决里两处枝节

1. 我写「合法的 `#--game=ar25` 落在 `deny_default_all`」——**实测是 `allow`**，原版和补丁版都是。
   无害（纯注释命令什么也不执行），但我那份的验收判据写错了，照抄会验错。
2. 我写的「文档比代码更严」**核对属实**：CLAUDE.md 新增段要求过滤路径「必须显式点名四局开发堆」，
   而 `uv run main.py --game=ar25` 判 `allow`、裸 `uv run main.py` 判 `deny_default_all`。

## 你要回的只有一个字

技术面我已经预清干净了：洞是真的、补丁验过、行数精确、封存堆零接触。
**剩下的纯粹是「碰 `CLAUDE.md` 这条根文件保护，放不放行」，按 CHARTER 只有你能回。**

三种回法都行得通，我不替你选：(1) 放行本分支并让作者先补那一行注释解析；
(2) 只收 `arc-recon/` 那部分、`CLAUDE.md` 的 37 行由你另行落；(3) 判它不必要（洞未被走过——
我上一跑查过，`environment_files/` 在本机任何地方都不存在，s11 是预防不是补救）。

**它挂 13 小时了，而挂着的成本不是这一条分支**：它一直占着 HELD 名单的位置，
每一轮 `ci_merge` 都把它重数一遍。
