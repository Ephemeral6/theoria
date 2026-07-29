# P5 释出包六步全完成；两条给别的领地的发现

RES-2 / paper 赛道 / 分支 `agent/p5-release` 已 push。零 API、零模型、零网络、零花费。

## 交付

`release/`：`LICENCE_POSTURE.md`（许可分级）、`check_redlines.py`（红线探针，两条都实测清白）、
`enumerate.py` + `MANIFEST.jsonl`（1951 个被跟踪文件逐个哈希并分级）、`checklist.py` +
`CHECKLIST.md`（对照 `Theoria.md`:379 清单：7 present / 3 withheld / 0 absent）、
`reproduce.py` + `REPRODUCTION_REPORT.md`、`REPRODUCING.md`。

## 第 6 步：陌生人 subagent

给了一个**干净 clone、没有 `.env`**、只告诉它「从 `release/REPRODUCING.md` 开始」。
规矩是**改文档，不改人**。它卡在**文档的第 2 条命令**上，一共挑出 7 处，已全部修掉。
最要命的一条：`enumerate.py` 因为缺凭据而中止——而文档第 0 节明写「你不需要 API key」；
错误信息还建议了一个 `enumerate.py` **不接受**的开关。**第 2 步就是死路，而且解药印在
屏幕上却用不了。**

另外三条值得当通例传：
* **`--dry-run` 打印 ABORT 却退出 0**，`reproduce.py` 遇到 drifted 也退出 0——**任何拿它
  接 CI 的人都会拿到绿灯**。
* **第 2 步的成功判据是空的**：文档说「不应有 diff」，而中止时 diff **也**是空的，于是
  「通过」和「根本没跑」长得一模一样。
* **手抄的数字又过期了**：`LICENCE_POSTURE` 写 1938 个文件 / 27 处，工具说 1950 / 33；
  `REPRODUCING` 写「有一项 ABSENT」，工具说 0。**一份专门警告「手抄事实会过期」的文件，
  自己有两处手抄事实过期了。**

## 两条给别的领地，我一个字没动

1. **`battery` 复跑漂移。** `python -m battery.run_battery` 之后**七个产物里六个**哈希对不上，
   含 `capability_spectrum.json`——**论文的能力谱主产物**。这条要紧的原因不只是漂移本身：
   `REPRODUCING.md` 第 7 节把「电池」作为**读者拿不到账本时的替代验证路径**推荐出去，
   而那条路径现在是唯一一个跑起来会红的。**建议派单给 battery 领地**：要么重算并提交产物，
   要么写明为什么产物与代码不一致。
2. **`exam/artifacts/build_manifest.json` 里嵌了绝对路径**
   （`C:\Users\user\Desktop\theoria\.worktrees\v4-exam-selftest\...`），因此**对地球上任何
   其他读者都必然对不上**。这不是漂移，是产物里带了机器特定的东西。建议 exam 领地改成相对路径。

## 一条方法论，建议进通用要求

**陌生人是这套工具里唯一可能发现这些的仪器，因为它是唯一一个不预先知道答案的。**
我自己写的探针、闸门、清单，没有一个能抓到「文档第 2 条命令就跑不通」——它们都在
「本来就该绿」的前提下运行。建议：**凡是对外的复跑文档，交付前必须由一个无上下文的
新会话照着走一遍，卡住即改文档。**
