# 预登记 —— 判据作者自己的干读，写在六个判定员交卷之前

写这份判据的人当然知道自己想让它答成什么。**如果不把那个答案先钉在时间线上，
就没有任何办法区分「判据有效」和「判据作者事后把它讲圆了」。**

这份文件在派出六个判定员之后、任何一份判定回来之前提交（见 `MANIFEST.json`
的 `preregistration_commit`）。它是我一个人按 `verify-lab/PARTIAL_CRITERION.md`
对 22 行的干读，**不给任何判定员看**。

对抗复核该拿它做两件事：

1. 看**判据文档**是不是把这张表编码进去了 —— 如果六个判定员只是把我的答案抄了出来，
   那一致率是抄写的一致率。判据里的六个实例都不在这 22 行里，正是为了挡这个，
   但挡没挡住由复核说了算。
2. 看我事后**有没有改口** —— 凡是判定员的多数票和这张表不一致的行，
   报告里必须按判定员的结果写，不许按这张表写。

## 22 行的干读

`部分` 层（V15 判 `部分` 的 14 行）：

| 入口 | V15 | 我的干读 | 理由码 |
|---|---|---|---|
| ablation-arm/exhibits/e2_a2.py | 部分 | 否 | D3 |
| baseline-arms/harness/summarise_envelope.py | 部分 | 否 | D2 |
| cold-start-a2/a2pipeline/certify_a2.py | 部分 | **部分** | C |
| cold-start-a2/a2pipeline/exhibit.py | 部分 | 否 | D3 |
| cold-start-a2/a2pipeline/repair.py | 部分 | **部分** | C |
| cold-start-a3/a3pipeline/certify_a3.py | 部分 | 否 | D3 |
| cold-start-a3/a3pipeline/run_l1.py | 部分 | 否 | D2 |
| engine-rig/recheck/verify_all.py | 部分 | **部分** | C |
| exam/papers/handover.py | 部分 | 否 | D2 |
| monitor/gates.py | 部分 | 否 | D0 |
| monitor/reflex.py | 部分 | 否 | D1 |
| monitor/scan.py | 部分 | 否 | D3 |
| theory-compiler/src/theory_compiler/strips_encoding.py | 部分 | **是** | — |
| worldgen/generate.py | 部分 | 否 | D3 |

对照层（V15 判 `是` / `否` 的 8 行）：

| 入口 | V15 | 我的干读 | 理由码 |
|---|---|---|---|
| cold-start-a0/certify/replay.py | 是 | **部分** | C |
| engine-rig/engines/fd_adapter/validate.py | 是 | 是 | — |
| exam/model.py | 是 | 是 | — |
| monitor/quota.py | 是 | 是 | — |
| cold-start-a0/pipeline/engines_stage.py | 否 | 否 | D3 |
| engine-rig/fixtures/pair_flip.py | 否 | 否 | D2 |
| monitor/ci_merge.py | 否 | 否 | D1 |
| papers/phase1-workshop/figures/fig2_coverage_accuracy.py | 否 | 否 | D1 |

## 我预期会被打的地方

* **`部分` 会变窄。** 干读里 22 行只有 4 行落 `部分`（14 行的 `部分` 层里只剩 3 行）。
  工单明写不许「把 `部分` 定义成一个几乎没人会选的窄格」。我的辩解是理由码
  ——`否` 里的 D1/D2/D3 是三种不同的病，被记下来了，可以在任一处重新折叠 ——
  但**这是辩解，不是证据**。复核要判的正是它站不站得住。
* **`replay.py` 是唯一一个方向相反的预测**（是 → 部分）。如果判定员不同意，
  那么这份判据就只会排干 `部分` 而从不喂它，工单点名的那个失败模式就成立。
* **`monitor/gates.py` 的 D0** 把「根本红不了」判成 `否` 而不是 `不适用`。
  这条会把它从假阴挪进真阴，**方向对我有利**，所以要被单独盯。
