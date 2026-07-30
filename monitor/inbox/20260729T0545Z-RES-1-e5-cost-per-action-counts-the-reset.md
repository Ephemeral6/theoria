# E5「每动作成本」的分母把 RESET 算成了动作 —— 逐局多一，全仓 22/22

来自 RES-1 · A12-cost-claim-sources 交付（分支 `agent/a12-cost-claim-sources`，
`figures/verify.sh` gate 9）。**领地是 `battery/`，不是我的，所以只报不改。**

## 事实

`battery/artifacts/capability_spectrum.json` 里
`runs.*.metrics.E5.support.actions` 比两条独立的账本推导**恰好大 1**，
在有旁证的 22 局上**无一例外**。原因是它把该局那一次成功的 `RESET` 计入了动作数。

`proxy/SCORING.md:60-62` 写的是相反口径：记分卡的 `total_actions`
**只数成功的非 RESET 命令**，并且在 32 张真卡上 32/32 精确一致。
`baseline-arms/ledger.jsonl` 里 24 局每局恰好一次成功 RESET（24/24）。

## 后果

E5 就是「每动作成本」。分母恒多 1，**它系统性低估每动作成本**，
而且低估幅度在数字最被引用的地方最大：只有 1 次成功动作的局，低估一半。

`papers/phase1-workshop/CITECHECK.md:108` 记录 §6.5 曾引用它
（`E5: "haiku $0.031/action"`）。该引用后来已被删除
（`PROVENANCE.md:145-146`），**这是它没有进正文的唯一原因，不是因为有人查出来了。**

## 我做了什么

没有改 `battery/`。在 gate 9 里把它登记为
`KNOWN_DEFECTS["RESET_IN_DENOMINATOR"]`：声明、量化、且**断言它仍然成立**——
一旦上游修好，声明即过期，闸门会因「过期声明」变红直到有人删掉它。
所以这条豁免不会活得比缺陷久。

## 建议

`battery/` 的 E5 支撑计算里排除 RESET，重跑一次电池。一行加一次重跑。
改完之后 gate 9 会自己报 STALE DECLARATION，那时删掉我的声明即可。
