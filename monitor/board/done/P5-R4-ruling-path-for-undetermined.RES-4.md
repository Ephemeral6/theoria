priority: 2
cell: P5
territory: release
deps: none
lane: infra
author: RES-4

# P5-R4-ruling-path-for-undetermined · R4 · needs_human 是一条没有出口的红，同一张图还判出三个类

R3 的对抗性复核（2026-07-29）留下一条**没有修法只有诊断**的结论，单独立项，因为它要造的是**新机制**，不是修一个默认值。

## 一、同一张图，三个容器，三个执照类

`figure6_bill_shape` 以 `.png` / `.svg` / `.pdf` 三种形态被跟踪（light 与 dark 各一套）：

| 文件 | 类 | 证据串 |
|---|---|---|
| `figures/paper/dark/figure6_bill_shape.png` | **A** | 「no ARC game id appears in this file」 |
| `figures/paper/dark/figure6_bill_shape.svg` | **C** | 「ids used as constants, guards or narrative carry no environment payload」 |
| `figures/paper/dark/figure6_bill_shape.pdf` | **?** | 「…undetermined」 |

那个 id 在两种文本形态里扮演**完全相同的角色**：SVG 里是 `<g id="text_42"><!-- g50t-5849a774 --></g>` 挨着一个刻度 `<use>`；PDF 里是 `BT /F1 6.5 Tf 0 0 Td [ (g50t-5849a774) ] TJ ET`，同一坐标上的文字绘制算子。**它是一个坐标轴刻度标签。**

R3 修完，这一族从 A/C/C 变成 A/C/?——**比它接手时更不自洽**。R3 的论点是「按字节判、不按文件名判」，而它把文件名判别式换成了**容器编码**判别式。

## 二、`?` 现在是一条没有出口的红

`release/` 里**没有任何裁定通道**（已 grep `checklist.py` / `bundle.py` / `*.md`）。一个 `?` 行没有办法被人**裁定**掉，只能被**改代码**掉。于是这条闸门对「任何渲染了 per-game 标签的二进制图」永久红——而永久红的闸门，下一个碰到它的人会一行 `return False, False` 关掉它，真红跟着一起走。

## 三、要做什么

1. **裁定通道 `release/RULINGS.jsonl`**（append-only）：每条 `{path, sha256, class, ruled_by, utc, reason}`。
   `enumerate.classify` 在判出 `?` 之后查它：**有匹配 sha256 的裁定就采用该裁定并在证据串里注明是人裁的**；没有就仍是 `?`。
   **裁定必须钉在内容哈希上**，不是路径上——否则同名文件换了字节会悄悄继承上一次的裁定，那正是本赛道在防的形状。
2. **给这三行各写一条裁定**，或者论证它们不该被裁定。PDF 那两个的实际论据是**同源**：`.svg` 孪生文件已被解析、已判 C，且两者由同一条 `figures/` 流水线从同一份数据生成。`enumerate.py:87` 的 `UPSTREAM_PAYLOAD_PREFIX` 已经确立了「出处可以定类、内容定不了的时候」这条先例。
3. **不许把 `?` 削弱成 C**。用现成的 `_review_note`（类 + `review` 字段、不变红）来解决这件事是**错的**方向：它把「读不出来」重新变成「读不出来就发」，而那是 R3 存在的理由。裁定通道让红变成「红到有人裁定为止」，而不是「红到有人关掉为止」。
4. **阴性样本**：(a) 一条裁定钉在旧 sha256 上、文件字节变了 → 裁定**不**生效，仍然红；(b) 没有裁定的 `?` → 红；(c) 有裁定的 `?` → 绿，且清单里标着裁定人；(d) 一条裁定试图把 D 类改成 A → **拒绝**（裁定不能翻越红线）。

服务论文 WP10。零 API、零封存堆接触。
