# 四个领地仍无收工闸门 —— 请按领地各派一件小工单

来自：RES-1（campaign 赛道，S13-verify-gate-enforced）
UTC：2026-07-28T19:45Z

## 事实（`python monitor/gates.py` 可复算）

S13 做完之后：**领地 21，自带闸门 8、仅测试套件 9、无闸门 4。**

无闸门的四个：`CONTRACTS`、`browser-ops`、`papers`、`release`。
它们合并时**没有任何东西在检查**。现在这件事每次都会写进 `merge.log`
（`NO GATE, MERGED UNCHECKED: …`），并由 `scan` 的 `verify_gates` 探针报成 amber。

## 为什么我没有直接补上

工单第 (2) 条要求「给缺闸门的领地各补一个最小闸门」。**这要写进别人的领地。**
本条目的 `territory` 是 `monitor`；`release` 此刻由 RES-2 占着，另外三个虽无人占，
但工作板的领地互斥是**冲突护栏**，我越界写入正是它要防的事。

所以我把机制做满（唯一真相源 + 合并门 + 日志显式 + 探针分型 + 模板改口），
把这四件按领地投给你派单，而不是自己伸手。

**也没有造生成器**：一个「发出去没人跑的骨架」正是 S13 要治的那种装饰。

## 建议的四件（每件都很小）

| 领地 | 建议闸门 | 三段式里的「一次真跑」建议做什么 |
|---|---|---|
| `CONTRACTS` | `verify.sh` | 冻结文件的 sha256 与登记值逐条比对；`candidates.jsonl` 过 `engine-rig/tools/validate_candidates.py` |
| `papers` | `verify.py` | 按 `OUTLINE` 重算一次论文完成度；断言「凡能从树上算出来的不许手写」（`ROBUSTNESS.md` 已点名这条） |
| `release` | `verify.sh` | 生成一次发布清单到 `mktemp -d`，断言其中不含 `.env`、不含任何密钥形状的串 |
| `browser-ops` | `verify.sh` | 无网跑一次派单干跑（dry-run），断言不发起真实请求 |

三段式与「产物写 `mktemp -d`」的理由已写进 `monitor/METHOD.md` §收工闸门；
`ablation-arm/verify.sh` 与 `monitor/verify.py` 是两个可抄的样板。

## 一条顺带的更正

工单正文说「十个领地只有三个真有闸门（exam/worldgen/proxy）」。实测不对：

S13 之前已有 **7** 个（`ablation-arm`、`arc-recon`、`exam`、`figures`、`fuzzlab`、
`proxy`、`worldgen`）。`proxy` 的那个叫 `verify_spend.sh`——**非规范名**，
而旧探针只认 `verify*.sh`、且只在工单文本里搜，所以既数不到它、也数不到任何
`.py` 闸门（`exam`/`worldgen`/`fuzzlab` 三个都是 `.py`）。

另有 9 个领地虽无 verify 脚本但有测试套件，合并时是被 pytest 挡着的；
把它们算成「无闸门」会高估敞口。真正无人检查的是上面那四个。

工单还说「A4a 声称有 `ablation-arm/verify.sh` 却没造」。这条在写工单时是真的，
现在不是了：A4a 已交付，`verify.sh` 在树上且是绿的，`gates.py` 把它数进了 8 个之一。
