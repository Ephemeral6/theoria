priority: 2
cell: P5
territory: release
deps: P5-release

# R2 · 释出包的许可合规：帧数据默认不许再释出

OPS-B 查实了基准文件问了两轮的问题（`browser-ops/TERMS.md` §2，逐页留痕在
`browser-ops/runs/2026-07-28-visits.md`）：**本地缓存帧数据无需额外许可**，但
**再释出需要书面许可，且默认是禁止**（ToS 原文 "without our express prior written
permission"）。

这条直接改变 WP10 的可达形态——「规模与开放性够到 Schema 的地板（全公开集 artifacts）」
在帧数据这一项上**做不到**，除非先拿到书面许可。做三件：
(1) 释出清单器加一道许可过滤：原始帧（env_step 的 frame 字段与任何帧转储）默认**不进**
释出包，改为发布帧哈希 + 复现脚本（任何人凭自己的 key 可重生成）；
(2) `release/LICENCE_POSTURE.md`：逐类产物标明可释出/需许可/不可释出，引 TERMS.md 行号；
(3) 给论文开放性声明写一段草稿：我们能释出什么、为什么帧数据只给哈希、这对复现意味着什么。
**不要自行去申请许可**——那是人的决定，写进 needs_human。
