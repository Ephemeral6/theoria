# 引擎：lp_potential

seam：`fuzzlab/props/lp_potential.py:_solve` —— 四条不变式全部经由它调用
`engines.lp_potential.run`，一次改绑即可覆盖四条；它返回 `(certificate,
heuristic)` 二元组，证书与启发式共享同一个 `Certificate` 对象（`deepcopy` 的 memo
保留这个共享），所以"改一个权重"会同时波及两侧，两个相关变异体因此显式把
`heuristic.certificate` 换回未改动的副本（理由写在 catalog 的 docstring 里：D-007
的 `limit_denominator` 快照发生在写入证书的路上，快照引入的缺陷本来就只动已发布的
权重）。

**oracle 侧、我没有动**：`_successors`（从 `graph["edges"]` 重建跳子关系）和
`_goal_set`。它们是 fuzzlab 自己算真值的地方；在那里注入是骗判官不是骗引擎，测出来
的数没有意义。我只**读**它们来给注入瞄准——即"这个谎在这个世界上确实是谎"，
和 `mutants/zero_space.py:_add_bogus_basis_vector` 用 `gf2.in_span` 挑一个确实在零
空间外的向量是同一个做法。判定仍然由属性自己重跑 BFS 完成。

世界数：40（`--worlds 40`，seed `0x00005eedc1e4f002`，engine-rig HEAD `baf1671`）；
基线：**干净**（`baseline_dirty_worlds: 0`，无 `BASELINE NOT CLEAN`）。
报告文件：`fuzzlab/out/mutation.lp_potential.json`。

## 逐不变式检出力

| 不变式 | 变异体 | 预注册命中？ | killed/eval | 首杀世界数 | inert | raised-only |
|---|---|---|---|---|---|---|
| `certificate_implies_unreachable` | `lp-certify-solvable` | 是 | 10/10 | 1（第 1 个被评估世界；原始世界序号 2） | 30 | 0 |
| `three_conditions_hold` | `lp-certify-solvable`（预注册的第二条） | 是 | 10/10 | 1 | 30 | 0 |
| `three_conditions_hold`（inv_closed 支） | `lp-raise-one-move` | 是 | 12/12 | 1（原始世界序号 0） | 28 | 0 |
| `three_conditions_hold`（inv_closed 支，藏起来） | `lp-hide-the-raised-move` | **否，SURVIVED** | 0/12 | — | 28 | 0 |
| `three_conditions_hold`（goal_break 支） | `lp-overstate-margin` | 是 | 21/21 | 1 | 19 | 0 |
| `heuristic_is_admissible` | `lp-heuristic-off-by-one` | 是 | 21/21 | 1 | 19 | 0 |
| `infinite_means_unreachable` | `lp-infinite-on-reachable` | 是 | 21/21 | 1 | 19 | 0 |
| `heuristic_is_admissible`（同上，预注册的第二条） | `lp-infinite-on-reachable` | 是 | 21/21 | 1 | 19 | 0 |

`unexpected_kills` 全部为空；`predicted_but_missed` 只有 `lp-hide-the-raised-move`
的 `three_conditions_hold` 一条，那是**写在跑之前的规范性预期**（见下）。
`raised_only` 全零：没有一个变异体是靠让属性崩溃被"检出"的。

**首杀数的读法**：所有列都是 1，即第一个能被评估的世界就足以杀死。以"检出力"论，
lp_potential 的四条不变式一个都不需要 500 世界；它们需要的是**一个发了证书的世界**
（或对第一条而言：一个可解的世界）。500 这个数对本引擎买到的不是检出力，是别的东西。

## 证书相关不变式的真实评估面（本引擎专有）

四条不变式**全部**以 `if cert is None: return []`（或 `heuristic is None`）开头。
所以"引擎没发证书"的世界对四条不变式**一条都不算测过**，只花了一次 `linprog`。

在同一 seed 下实测：

| | 40 世界 | 200 世界 |
|---|---|---|
| 引擎发了证书 | 21（52.5%） | 108（54.0%） |
| 没发证书 | 19 | 92 |
| 其中 BFS 证实**可解**（不发证书是正确的） | 10 | 44 |
| 其中真不可解、只是没有线性 pagoda（**文档化的不完备**，D-014） | 9 | 48 |
| `CertificateError` | 0 | 0 |

所以：**"3000 世界"对本引擎的四条不变式来说，实际约 54% 是空转**。按标准战役的
500 世界折算，四条不变式各自真正被评估的世界数约 270，不是 500。

再往里一层，在那 21 个发了证书的世界上：

* `certificate_implies_unreachable`：21 次评估，每次跑一次 BFS，**在干净运行里
  永远不可能响**——引擎是可靠的，证书只发给不可达的配置。它不是构造上不可证伪
  （`lp-certify-solvable` 让它 10/10 响了），但它的全部检出力只有在注入下才看得见；
  干净战役里它是一条"从未有机会开口"的不变式。
* `heuristic_is_admissible`：21 个世界共扫 5088 个状态，其中只有 **409 个（8.0%）**
  有有限的真实距离、进入真正的比较；其余 4679 个被 `continue` 掉（BFS 说到不了目标）。
  可采纳性这条命题实际只在这 409 次比较上被检验过。
* `infinite_means_unreachable`：5088 个状态里有 **2601 个 h=inf**，每个都被 BFS 复核。
  这条是四条里评估最扎实的一条（在有证书的世界上）。
* 21 个世界**全部**至少有 1 个可达状态、也至少有 1 个 inf 状态，所以没有哪个"有证书"
  的世界对启发式两条不变式是空的。

**skipped 相关**：没有任何一个变异体把世界推进 `skipped`。`_skip_certificate_error`
在 200 个世界里**一次都没被触发**（`CertificateError` 计数为 0），即 D-007 那条
"raise 而不是发出只在 1e-9 上成立的权重"的分支，在这个世界族上是死代码——战役从
未测试过它。`heuristic_is_admissible` / `infinite_means_unreachable` 的
`SWEEP_BUDGET=4096` 跳过分支也从未触发（最大世界 512 个状态）。

## 杀不死的变异体（逐个裁决）

### `lp-hide-the-raised-move` —— SURVIVED，裁决为 **(a) 不变式不够**

与 `lp-raise-one-move` 是一对受控对照：**完全相同**的权重改动（同一个
`_pick_break` 挑出的 move / position / 增量），唯一差别是把那个被破坏的 move 从
`cert.moves` 里删掉。inert 集合因此逐世界相同（都是 28），eval 都是 12。

* `lp-raise-one-move`：12/12 被 `three_conditions_hold` 杀死。
* `lp-hide-the-raised-move`：0/12，四条不变式没有一条出声，也没有 raised。

原因不是"这不是缺陷"。`three_conditions_hold` 复核 `inv_closed` 时迭代的是
**`cert.moves`——引擎自己报的那份跳法清单**，不是世界的 `graph["edges"]`：

```python
for move in cert.moves:                      # props/lp_potential.py:141
    delta = weights[move.dst] - weights[move.src] - weights[move.over]
```

而 `check_exactly` 的闭包论证只有在这份清单**完整**时才"独立于哪些状态可达"
（potential.py:205-209 自己就是这么写的）。少报一个会抬高势的合法 move，证书的
"不可达"结论就建立在一个有洞的论证上，而属性拿引擎自报的清单去复核，看不见这个洞。

这**不是**文档化的不完备性：不完备性说的是"该不发证书时不发"，这里引擎发了证书，
而且发出的论证是错的。是真缺陷，不变式漏了。

**怎么补**：`three_conditions_hold` 应当从 `world.graph["edges"]` 独立重建跳法几何
（`{tuple(e["positions"]) for e in graph["edges"]}`），先断言它与 `cert.moves` 的集合
相等（少报即 violated），再在这份独立清单上验 `inv_closed`。这与该模块 oracle 侧
`_successors` 的既有做法一致——那里已经明确"从 edges 重建，不读引擎算过的表"，只是
`three_conditions_hold` 没有照做。

（其余五个变异体全部按预注册被杀，没有需要裁决的幸存者。）

### 一个我**故意没写**的变异体

"在不可解的配置上不发证书"没有变异体。那是 `CLAUDE.md` / D-014 /
`engines/lp_potential/README.md` 三处明写的能力边界（sound but incomplete）。给它写
变异体，它会在所有世界上"幸存"，然后我就会报出一条"不变式漏检"——那是假阳性，也是
本引擎最容易犯的错。实测里这种世界占 40 个里的 9 个（200 个里的 48 个），量不小，
足以把一份不小心的报告变成一份自信的错报告。

## 构造上不可证伪的检查

1. **`three_conditions_hold` 的 `inv_closed` 支不是构造上不可证伪，但它是
   "同源比较"**：它用引擎自报的 `cert.moves` 复核引擎自报的 `cert.weights`。
   两者同源，所以对"清单本身不全"这一类缺陷完全无感——上面那个幸存者就是证据。
   （`goal_break` 支不同：它用 `world` 的 goal_states 与 initial，是独立的。）
2. **`inv_init` 从不被检查，且不可能被检查**：`check_exactly` 里它是
   `potential(s0) <= potential(s0)`，恒真。属性模块自己在 docstring 里点明了这一点
   并明确拒绝"复核"它（"a property that 'checks' a tautology reports a pass it did
   not earn"）。也就是说三条件里只有两条是可测的——这是已被记录的、正确的处理，
   我把它列在这里只是为了让"三条件"这个数不被误读成 3。
3. **`infinite_means_unreachable` 被 `heuristic_is_admissible` 完全蕴含**：一个在
   真实距离有限的状态上返回 inf 的启发式，按定义就是高估。两条不变式扫同一份
   `graph["states"]`、同一个 `SWEEP_BUDGET`、都在第一处违规 `break`。实测印证：
   `lp-infinite-on-reachable` 21/21 同时杀死两条，且不存在只杀第四条的杀法。
   第四条不是无效（它给出的报告信息更精确），但它**不是一条独立的检出力**：任何
   能杀它的缺陷都能杀第三条。四条不变式的独立检出力实为三条。
4. 一个理论上的补充（未做实验）：在**可解**的世界上，任何被发出的证书必然违反
   `three_conditions_hold`——若三条件同时成立，可达性就与 pagoda 论证矛盾。所以
   `certificate_implies_unreachable` 与 `three_conditions_hold` 在可解世界上是重叠的，
   `lp-certify-solvable` 的 10/10 双杀正是这个重叠。前者的价值在于它不依赖证书内部
   条件的自洽（能抓住一个"三条件都自洽、但世界其实可解"的证书；后者理论上抓不到，
   如果这种证书存在的话）。

## 预测错的地方

**没有**。六个变异体的 `expect_kill` 全部写在跑之前（文件先写完，再跑驱动），
`unexpected_kills` 为空，`predicted_but_missed` 只有一条：
`lp-hide-the-raised-move` 的 `three_conditions_hold`。

需要讲清楚这一条的性质：框架强制 `expect_kill` 非空（`Mutant.__post_init__` 会拒绝
空元组），所以我无法把"我预期它幸存"注册为预期。我按 `mutants/__init__.py` 的措辞
（"which invariants *should* catch it"）填了**规范性**预期——应当抓住它的那条——
同时在 catalog 的 `description` 里写死了我的**经验性**预测："the empirical
prediction, written before the run, is that it cannot"。经验预测也命中了。

## 我不确定的 / 框架挡住我的地方

1. **seam 返回元组，`touched()` 用不了。** `mutants.applied` 是在 seam 的返回值上读
   `MARK` 的，而这里返回值是 tuple，`touched(tuple)` 按设计会抛 `TypeError`。于是
   "影子掉内层对象的一个方法"这类变异体（正是启发式两条不变式唯一自然的注入方式）
   会在每个世界上被判 inert，分母塌成 0，而表里还留着一行。我没有改框架，改用
   `Heuristic` 的**子类**返回：dataclass 的 `__repr__` 渲染 `__class__.__qualname__`，
   所以替换在框架的 `repr(before) != repr(after)` 回退检查里是可见的。这是个可用的
   出口，但它是我摸出来的，不是文档里的；建议 `touched()` 补一句"seam 返回容器时
   请让 repr 可见"，或让 `applied` 对 tuple/list 递归查 MARK。
2. **`lp-raise-one-move` / `lp-hide-the-raised-move` 的 eval 只有 12/21。** 另外 9 个
   有证书的世界上 `_pick_break` 返回 None。我单独测了原因：**9 个全部**卡在我自己
   加的"gap 中性"约束（被改的位置在 initial 与所有 goal 里占据情况一致，从而
   `goal_break` 分支的判定不受影响）；"其他 move 不能翻正"那条约束一次都没成为瓶颈。
   也就是说这 28 个 inert 是我为了让两个变异体各自只打一条支路而付的代价，不是世界
   的性质。放宽它能让 eval 到 21/21，但那时 `three_conditions_hold` 可能是靠
   `goal_break` 支杀死的，inv_closed 支到底有没有响就分不清了——而结论不会变
   （12/12 已经是 100%，幸存者也仍然幸存，因为它幸存的原因与 goal_break 无关）。
3. **`lp-certify-solvable` 用的是全零权重证书。** 它对应"两处返回 None 的守卫都被
   拿掉"的引擎（`result.success` 检查与 `CertificateError`），我认为这是一个真实可能
   的缺陷形状（不看 `linprog` 的 status 是经典误用）。但全零权重让
   `max_decrease = 0`、h 恒为 0，所以启发式两条不变式在它下面是静音的——这是我选它
   的原因（窄），也意味着"伪造证书"这一类缺陷里，权重非零的那些变体我没有覆盖。
4. **世界族的偏斜**：`jumpgraph` 生成器在 40 个世界里只给出 10 个可解世界，而
   `certificate_implies_unreachable` 的唯一检出面就是可解世界。这条不变式在标准战役
   里实际只有约 25% 的世界可能对它说话，而且只有在引擎出错时才说得上话。
5. 我没有跑标准 500 世界战役来核对上面的比例在大 N 下是否稳定；只跑了 40（变异）与
   200（仅证书率）。两者的证书率是 52.5% 与 54.0%，看起来稳定，但这是两个样本。
