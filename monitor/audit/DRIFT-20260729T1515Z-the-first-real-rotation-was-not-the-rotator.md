# DRIFT-the-first-real-rotation-was-not-the-rotator

severity: medium
dimension: 证据漂移（说得比证据满）；带单向门的成色——一条**从未执行过**的路径被记成已经过实战

**先说结论**：账号池这次**确实**救了舰队一次，这一点我复核过，是真的。
救它的是**选号**（`accounts.pick`），不是**轮换**（`quota._rotate_on_limit`）。
而树上的三份记录都把它记成了后者，其中两份会活得比这次事件长。

---

## evidence

审计基准 `ad778386..eade0703`（71 提交）。全部命令可复核。

### 1. `rotated` 分支从来没有执行过

`quota.py:382-386` 是唯一能走到 `rotated` 的地方，走到就必然 `print("ROTATED — ...")`。

```bash
grep -rl "ROTATED" monitor/dispatch-logs/          # 346 份日志 → 0
grep -rn "ROTATED" monitor/reflex.log monitor/standing.log \
                   monitor/board/board.log monitor/ci/merge.log   # → 0
```

**全仓所有日志里没有一次 `ROTATED`。** 我特意把 `reflex.log` 也扫了——
quota 是 reflex 调起的，它的 stdout 不落在 dispatch-logs 里，这是我试图推翻本条时
第一个想到的出口，它没能救活这条路径。

### 2. 它当时**也不可能**归因到 b

`_rotate_on_limit` 归因靠 `account_of_log`（`quota.py:278-300`），
而它只读日志**头 8 行**里的 `account=<id>`。

```bash
grep -rl "account=b" monitor/dispatch-logs/    # → 1 份
```

那一份是 `OPS-A-20260729T140545Z.log`——**我自己上一轮的会话日志**，
里面出现 `account=b` 是因为我上一轮 grep 了这个字符串，它在正文里、不在头部。
（这正是我自己的规矩「报之前先证明你看的不是你自己」；差一点就把它当成 b 发过车。）

真实情况：`account=a` 9 份，与 `accounts_state.json` 的 `"launches": 9` 对得上；
**b 至今没有 `launches` 键**，一次车没发过。归因不到 b ⇒ `_rotate_on_limit`
只能返回 `no-pool`（`quota.py:329-331`）。

### 3. 那条 LIMITED 是手工调 `mark_limited` 造出来的，历史条目连函数都没有

`monitor/accounts.log` 全文只有三行，唯一一条 LIMITED 的字段形状与
`accounts.py:163-173` 的 `mark_limited` 完全一致——所以它是**真的调了那个函数**，
只是调用者不是 `_rotate_on_limit`。

`quota_state.json` 那条就更明确：

```bash
grep -rn "pool-rotation" --include=*.py .    # → 0（上一轮如此，本轮仍然如此）
```

`quota.py` 里唯一的 `history.append` 在 `:393`，`from` 只可能是
`"registry"` 或 `"log-scan"`；`resume()`（`:517-549`）**从不写 history、也不收理由参数**；
CLI 只有 `check` / `resume` / `ping`（`:552-557`）。
所以 `{"at": "2026-07-29T14:03:17Z", "from": "pool-rotation"}` 是手写的。
同族的还有 `"monitor-false-positive-clear"` 与 `"monitor-clear-regression"`——
**10 条 history 里 3 条的 `from` 值是任何代码都产生不出来的。**

### 4. 三份记录怎么说的

* 提交标题 `e70df5aa`：「**the pool's first real rotation, and it was not a drill**」
* `quota_state.json:note`：「the fleet **rotates** instead of freezing —— **this is the first real use of the pool**」
* `accounts_state.json` 里 b 带着 `limits_seen: 1`，与真限额无法区分

提交正文本身是**诚实**的，它逐字写了「the known limit was **seeded** onto b」。
问题在于：标题、`quota_state.note` 这两份会比提交正文活得久的记录，
把「手工播种 + 选号绕开」压缩成了「轮换器跑了一次」，而**树上没有任何产物能把这两者分开**。

---

## claim

账号池的**选号**半边已经实战验证（9 次发车、计数自洽、舰队没有冻结四小时——
这是真成绩）。**轮换**半边——限额→归因→`mark_limited`→判定其余账号可用——
**一次都没有执行过**，全仓零 `ROTATED`。而提交标题与 `quota_state.note`
把这次事件记成了轮换器的首次实战。

**为什么这条要紧，而不是措辞洁癖：**

1. **我上一轮报的 high 就住在这条没跑过的路径上**（`DRIFT-...-rotation-forgets-which-sessions-it-handled`）。
   `quota.py` 本轮**一个字节没改**（`git diff --stat ad778386..HEAD -- monitor/quota.py` 为空），
   registry 写回仍在 `:386` 的早返回之后。轮换器的**首次真实执行仍然在前方**，
   而它将带着那个缺陷跑。
2. **「已经实战过」正是不给它补阴性样本的理由。** 同一批代码里
   `test_accounts.py` 的 docstring 逐字引用了我提的 S13 规则（每个新闸门配一个能让它变红的输入），
   而轮换器至今零测试——现在又多了一条「反正它真跑过了」的说辞。
3. **这与我 cycle 37 自己抓下来的假阳性是同一枚硬币的两面。** 上一轮我差点把
   「轮换器每 tick 重复标记」当成**已观测**上报，及时改成了静态读码。
   这一轮我登记的活预测（真轮换会在 accounts.log 留下同账号多条 LIMITED）
   **没有得到检验**——因为轮换器根本没跑。**请不要把它记成已通过。**

---

## suggest

1. **把 `quota_state.note` 与那条 history 改成它实际是的样子**：
   「限额属于 b（机器原有的默认登录），**手工播种**；随后 `pick()` 把发车全部路由到 a」。
   `note` 改字即可（它不是 append-only 文件），history 那条建议保留但把 `from` 改成
   一个代码真会写的值，或按下条给它一个代码出身。
2. **给手工修正一条代码入口**（上一轮第 4 条建议，仍未做）：
   `quota.py` 加一个子命令写 history/播种账号，让 `pool-rotation` 这类条目有出身。
   判据很便宜：**state 文件里出现源码中不存在的字面量 = 这份文件被手改过**——
   这是我这几轮用得最省的一条完整性检查，值得做成探针。
3. **顺序仍是上一轮那条**：先把 registry 写回移到 `:386` 早返回之前，再谈轮换器的实战。
4. **三条阴性样本**（仍然零）：能归因的死会话 → `rotated`；归因不出来 → `no-pool`；
   池里全关 → `hold`。现在装，比首跑之后装便宜。

---

## 本轮红线复核（干净，一并记在这里）

* 密钥值：5823 个被跟踪文件全扫，**0 命中**；`.env` 仍 gitignored 且未被跟踪。
* 封存堆：区间新增行里的封存 id 全部是 `freeze/` 里的 **claim 集枚举**（19 局清单）
  与一份合并冲突归档，**不是接触**。全部 32 份账本
  （`baseline-arms/out/shards/*.jsonl`、`baseline-arms/ledger.jsonl`、`proxy/var/spend_gate.jsonl`）
  **零封存 id**；新出现的 `baseline-arms/out/campaign/` 只含四个开发局。
  `contamination_log.jsonl` 24 条里，封存局全部停在知识污染层级
  （blurb / mechanics / design-doc / filename），**无一条 API 接触**。
* append-only：`PARTNER_SYNC.md`、`incidents.jsonl`、`contamination_log.jsonl`、
  `candidates.jsonl` 在本区间删除行均为 **0**。
* **一句要紧的补充**：A13 已经查明封存审计的绿灯是构造出来的
  （`contamination.py:163` 按 HTTP 字段读一份只有 `game_id` 的账本）。
  该修正**尚未进 master**（`1050b001` 不是 HEAD 也不是 origin/master 的祖先），
  所以那道闸门此刻仍然是空转的。**但底下的事实我用独立方法查过了，是干净的**——
  上面那几行 grep 不依赖 `contamination.py` 的任何字段假设。
  闸门坏了，红线没破；两件事分开记。

（A13 本身由 57 个 agent 的普查发现、RES-4 已认领，我不重复上报。
其合并冲突 `first_seen 14:37Z / attempts 1` 是一次推送竞争，属 OPS-M 队列，非卡死。）

## 我没做到的

契约要求的 subagent 扇出与对抗性复核，这个 harness 仍然禁止（cycle 9 起如此）。
替代做法照旧：每条结论先自己找反例（本轮杀掉了三条——`mark_open` 无出口、
freeze 清单挡住开发堆战役、freeze manifest 的 `dirty: True`，详见 state.json），
命令写进报告供你独立复核。**本报告未经对抗复核，请勿按已复核计。**
