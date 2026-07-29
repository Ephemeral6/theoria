# cascade — P-20 · 级联语义在线裁决

一个问题，25 个动作：**一个动作会不会返回不止一帧？**

答案与它的全部限制在 [VERDICT.md](VERDICT.md)。这一页只讲仪器：怎么跑、记了什么、
为什么这样记。

```bash
cd arc-recon
python -m cascade.spec                                   # 冻结的序列与预算，零 API
python -m cascade.probe --game <id> --run-dir <dir>      # 一局，花动作
python -m cascade.probe --game tn36-ef4dde99 --set followup --run-dir <dir>
./cascade/verify.sh [<run-dir>]                          # 停工核对，零 API，退出码即结论
python -m cascade.make_manifest --run-dir <dir>          # 重算全部 sha256
```

## 它相对预检新增的唯一一件事：逐帧哈希

`data/precheck.json` 已经见过 7 帧和 2 帧的响应，`arc-recon/README.md` 也早已记下
`frame` 是列表。但预检把**整批一起哈希**，于是「7 个不同的状态」和「同一帧重复 7 次」
在它的记录里是同一个类别 —— 而这两者对 `step` 该建成什么形状的含义完全相反。

所以本探针每步多记四个字段，裁决全部压在它们上面：

| 字段 | 含义 |
|---|---|
| `frame_hashes` | 逐帧哈希，保序 |
| `distinct_frames` | 其中有几个互不相同 |
| `intra_batch_changes` | 相邻帧有几处不同（区分「变化」与「静止游程」） |
| `first_equals_prev_last` | 本批首帧是否等于上一批末帧 |

## 不重新发明、直接沿用的纪律

* `precheck.assert_playable` 逐局把关，**封存堆不可触碰**，这个文件不对此另有主张。
* `precheck.send_command` 就是 INC-005 / INC-007a 的重试包络：只发全 id、40 次尝试、
  退避封顶 5 秒、每 5 次失败重抽 ALB 路由。短 id 一次都没发过 —— INC-005 的伪造 200
  正来自短 id。
* 密钥由 `client.load_api_key` 读取，除 `mask()` 的四位handle 外不出现在任何输出里。

## 三条本探针自己的规矩

**账本写进跑目录，不写 `data/recon_ledger.jsonl`。** P-20 的工单只允许**新增**
`arc-recon/cascade/`。往既有的 append-only 账本里追加是对领地外文件的改动，也是与
P-11 分支的合并风险。代价照说：本目录的账本不参与 `contamination.py` 的全账本审计，
所以 `verify.py` 自己实现了封存 id 的请求体检查（A7）。

**预测是代码闸门，不是习惯。** `predictions/<game>.md` 不存在时，`probe.py` 拒绝下第一个
动作。看完帧再写预测，正是 INC-003 那类「不会失败的检查」；顺序由代码保证。

**同一跑目录不许重跑。** `steps.<game>.jsonl` 已存在即拒绝——重跑会把第二个会话的步
追加进同一个文件，既超预算，又让两段不同的历史在记录里无法分辨。

## 停工核对（`verify.sh`）

七条断言，每条都真的能失败。最吃劲的是 **A3：帧哈希从账本里的原始响应体重算**，
而不是从摘要里转录 —— 自洽的摘要证明不了任何事（PARTNER_SYNC，proxy 的安全登记：
账本自洽 ≠ 账本可信），但一份哈希可被原始字节重新导出的摘要至少不能与字节漂移。
其余六条：请求在账本里（A1）、响应与状态对得上且尝试次数一致（A2）、序列完整或
末步带错误（A4）、预算未越界（A5）、密钥与 cookie 值不在任何文件里（A6）、
21 个封存 id 不在任何请求体里（A7）。

`verify.sh` 在跑目录里没有 `steps.*.jsonl` 时**退出 1** —— 一个无事可查时会通过的检查
不是检查。

## 会被发布的东西里有什么

Theoria Phase 4 发布每一个受版本控制的文件，所以这里逐项说清：

* **没有** API key，**没有** cookie 值。A6 每次跑都在整个跑目录上按字节搜一遍，
  包括本 README。
* **有** `guid` 与 `card_id`，在账本的请求体与响应体里。`guid` 是活会话的持有者令牌，
  这一点不隐瞒；但它是 `proxy/LEDGER_FORMAT.md` §3 明文规定要记的字段，既有的
  `data/recon_ledger.jsonl` 已有 968 行带 `guid`，本目录沿用同一惯例而非新开一个口子。
  相关会话均已废弃。
* **有** 全部 74 帧的原始 64×64 栅格，在账本的响应体里。这是有意的：裁决靠逐帧哈希，
  而哈希必须能被任何人从原始字节重算 —— 否则 A3 就成了自证。

## 跑目录

```
runs/2026-07-28T034709Z-p20/            主跑，4 局，22 个动作
runs/2026-07-28T034709Z-p20-followup/   追加跑，tn36，3 个动作（ACTION6 坐标形状）
  predictions/<game>.md                 预测（先）+ 结果对照（后）
  steps.<game>.jsonl                    每命令一行，边跑边 fsync
  ledger.<game>.jsonl                   每次 HTTP 调用一行，请求与响应全文
  summary.<game>.json                   收尾聚合
```

追加跑是**对冻结计划的一处偏离**，理由与账写在 `spec.py` 的 `FOLLOWUP` 上方，
不藏在 diff 里。
