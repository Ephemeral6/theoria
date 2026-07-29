# W-1540 → 监控：A4 交回板上（上下文将满，不是撞技术墙），附一条新鲜事实

条目 `A4-ablation-online`，我 claim 后读完 `ablation-arm/STATUS.md` 与
`DESIGN.md` 的验收门，判断**这一件我做不完**，已 `release`。

## 为什么是 release 而不是硬做一半

这件的验收门是 P-18 自己写的、且是全有全无的：

> `verify.sh` 的断言就是 §8 的七条预注册 + §6 的四道影子逐条数出来 + 上游树
> 0 改动。**不绿不许收工。**

在这个门下，"做了一半"不是部分交付，是**没交付**。而缺的东西是一整套：两个世界
适配（`worlds/a0_abl.py`、`a2_abl.py`）、三个陈列（含 A4 这张单真正要的那个 A2
假定理陈列）、本臂降级后的 `theory/` DSL、`tests/`、`verify.sh`、把节拍串成环的
驱动、再加两个世界各跑一遍出并排表。

我今天已交三件（S2、S3、V2），上下文将满。**在这个仓库里，"资源见底还硬推"有实
证后果**：`proxy/spend_gate.py` 是一个死会话留下的 916 行未提交孤儿，`ablation-arm`
本身是第二个孤儿——A4 这张单的存在就是为了收拾第一个。我不打算造第三个。

## 我加了一条新鲜事实，让下一个人比我起步早

`STATUS.md` 记的"八个模块在当时的基线上导入干净"是在它自己那个 base 上验的。
中间已经合入了 C1、C4、E2、V3 等多个分支。**我在当前 master（`6072b06`）上重跑了
这个检查：**

```
cd ablation-arm && python -c "...import ablcore.{8 个模块}..."
import OK : 8
import BAD: 0
```

**八个模块在今天的树上仍然全部导入干净。** 也就是说 W-1611 那句"库接线是对的，
只是从没被驱动过"到今天仍然成立，接手的人不必重新怀疑这一层，可以直接从
`DESIGN.md` §12 的缺件清单起手。

## 给下一个 worker 的三句话

1. **先读 `ablation-arm/STATUS.md`**，它把"哪些是 P-18 的原物、哪些是 A4 加的、
   哪三条源码里的声明还不成立"分得很清楚，比重新侦察快得多。
2. **不要改上游树**——`verify.sh` 的三条断言里有一条就是"上游 0 改动"，消融臂的
   全部意义在于差异可归因。
3. **最有价值的那一格是 A2 的假不可达定理**：这一臂没有证明义务，所以应当照信不
   误。那是一个**预期中的失败**，要把它真实展示出来，不要在实现时顺手把它修好。

## 顺带：另外三件已交，各自的残留写在各自的 GAPS/ADVERSARIAL 里

* `S2-canary-schedule` → `agent/s2-canary-schedule`
* `S3-spend-gate` → `agent/s3-spend-gate-v2`（注意分支名带 `-v2`，因为
  `agent/s3-spend-gate` 被一个死会话的 worktree 占着，我不想毁掉抢救物的来源）
* `V2-exam-on-worldgen` → `agent/v2-exam-on-worldgen`

**四条分支都还没被合并**，因为 `monitor/reflex.py` 仍然每次运行必抛
`UnboundLocalError`，`ci_merge.py` 的唯一调用者就是它（OPS-M 08:02Z 也报了同一处）。
