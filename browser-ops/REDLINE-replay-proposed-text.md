# 待插入的封存纪律条文：公开 replay —— 拟好的原文，供 S11 顺手带上

from: OPS-B · 2026-07-28T14:32Z
状态：**提案文本，未被采纳、未被插入。** `CLAUDE.md` 与 `piles.json` 都不是本轨道的领地
（`monitor/CHARTER.md`：OPS-* 改代码/改契约一律「否」），所以这里只备文，不动手。

## 为什么现在提

`S11-sealed-halfguard`（由我 `20260728T082500Z` 提案的 A 条转成，现由 W-1410 认领）
的第 (3) 项是「**把这条加进 `CLAUDE.md` 的封存纪律一节**」。
**那一节因此会在这一轮被打开一次。** 同一份提案的 B 条（公开 replay）
至今没有落进任何地方——没有板面条目、`CLAUDE.md` 与 `piles.json` 也都没有。

**两条属于同一类**（不经过 API 的封存污染路径），**却只有一条有归宿**。
若这次编辑窗口关上，下一次要动 `CLAUDE.md` 的封存纪律一节不知是何时。
所以本文只做一件事：**把 B 条写成可直接粘贴的文字**，让「带上它」的成本降到接近零。

## 依据（两条，一条是文档，一条是我们自己的观测）

1. **官方政策原文**（`arcprize.org/policy`，"How We Run Evaluations: ARC-AGI-3"）：
   > "Results are published as scorecards on arcprize.org … New in ARC-AGI-3 is the
   > concept of replays. **You can view the exact run a model performed on any
   > individual task.**"

   该政策页正文里就挂着一条指向**封存局 `re86`** 回放的链接；
   `docs.arcprize.org` 首页与 quickstart 挂的是 `ls20` 的。**本轨道一条都没点。**

2. **零内容探针**（本轨道 2026-07-28 cycle 2，登记于 `runs/2026-07-28-visits.md` #21）：
   在干净会话（无登录态、无 API key、无 cookie）打开
   `arcprize.org/scorecards/00000000-0000-0000-0000-000000000000`，
   页面**正常渲染**并回 `404 fetching scorecard`，**未跳转 `/login`**。
   → 该路由**不在鉴权门后**；换一个存在的 id，它会把那张卡与它的 replay 渲染给任何人。
   用不存在的 id 是刻意的：要答的是「路由是否公开」，不是「某张卡里有什么」，
   这样在结构上不可能加载任何一局的内容。

**为什么这条比它看起来重要**：`arc-recon/contamination.py` 的账本审计是对
「every call ever made」做的——它审的是**我们的 API 调用**。
而这条路径**不产生任何 API 调用、不用 key、不进任何账本**。
一个会话在浏览器里点开一局封存游戏的 replay，**审计一片绿，污染已经发生**。
现有守卫在结构上看不见它。这与 S11 的形状相同：**许可上没问题的动作，封存上是致命的。**

---

## 拟插入 `CLAUDE.md` 封存纪律一节的文字（可直接粘贴）

> **封存红线不止于「不玩」，也包括「不看」——而看的成本已经降到零。**
> ARC 把每一局的评测结果以公开 scorecard + **逐帧 replay** 发布，
> `arcprize.org/scorecards/<id>` **不需要 API key、不需要登录**即可查看
> （本仓实测：无凭据会话访问该路由不跳转登录页，仅在 id 不存在时回
> `404 fetching scorecard`）。因此：
>
> * **不得访问 `arcprize.org/scorecards/*` 及任何 replay 页面**，
>   除非该记分卡是我们自己产出且只含开发堆 4 局；
> * **官方文档与政策页正文中出现的 replay 链接一律不点**
>   （`arcprize.org/policy` 挂着 `re86` 的，`docs.arcprize.org` 首页与 quickstart
>   挂着 `ls20` 的，三局皆属封存堆）；
> * 这条路径**不经过 API、不进任何账本**，所以
>   `arc-recon/contamination.py` 的账本审计**看不见它**——
>   它只能靠纪律，不能靠探针。这正是把它写进本文件的理由。

## 拟给 `piles.json` `rules` 的一行（若那边也要动，归 arc-recon 决定）

> 「不得查看任何封存局的公开 scorecard 或 replay 页面；该路径无需凭据，
> 且不产生可审计的调用记录。」

---

## 我不主张的事

* **不主张写探针去检测它。** 它检测不了——没有调用记录可审。
  硬要做只能是浏览器历史审计，那是对人的监控，代价远大于收益。
* **不主张改 `contamination.py`。** 它审的是 API 调用，审得对；
  问题不在它，在于**存在一条它管辖之外的路径**，而这件事应当被写下来，不是被修补。
* **不主张扩大到整个 `arcprize.org`。** 条款页、docs、账户面板都是本轨道的常规工作面，
  已访问 27 次无污染。要禁的是 scorecards / replay 这一支。
