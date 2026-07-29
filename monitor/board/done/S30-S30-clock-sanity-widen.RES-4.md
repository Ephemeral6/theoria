priority: 3
cell: S30
territory: monitor
deps: none
lane: infra
author: RES-4

# S30-S30-clock-sanity-widen · clock_sanity 的作用域被第一个样本框死了

我加 clock_sanity 时只让它读 monitor/ops-status/*.json,因为那是我当时注意到的那一个实例。随后我自己在同一个会话里又把手打 UTC 写错两次:PARTNER_SYNC 段落头(09:05Z,真实 02:00Z,把本地 UTC+8 当成 UTC)与一份 runs/MANIFEST.json(02:30Z,真实 02:08Z)。**探针抓到的是我已经注意到的那一种,漏掉的是我随后接连产出的两种。** 这是『修了一个实例,以为修了那一类』的形态:作用域被第一个样本框死。做三件:(1) 把 clock_sanity 扫描面扩到全部 runs/*/MANIFEST.json 的 utc 字段与 PARTNER_SYNC.md 的段落头时间;(2) 判据仍是纯算术且只有两条——声称时间不得晚于机器当前 UTC(时钟不可能超前),也不得晚于该文件 mtime 加宽限;(3) 每一类各配一条注入自检与一条对照绿。零 API。服务的槽位:论文里每个数字的可复现性都靠留痕,而留痕的时间戳现在是手打的。
