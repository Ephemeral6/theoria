priority: 1
cell: A19
territory: baseline-arms
deps: none

# A19-bare-cc-seal-split · GAP-5 清账：bare_cc 照 theoria 臂的样子封印

`baseline-arms/STATUS.md` GAP-5（2026-07-31）自己登记的差距：
`harness/arc_client.py:137` 直接开 `.env` 取 `ARC_API_KEY` 存进臂进程，
调用直打 ARC 不经环境代理——Theoria.md 封印合取两项都不满足，
且「未做同样拆分前不得再飞」。这把 p1-seal-test 与 p1-same-shell
各锁了一半。

做法照抄已验证的先例（merge b375a9bd，theoria 臂）：

1. 把凭据注入移进独立子进程 / 或直接改走 `proxy/` 环境代理
   （`theoria-arm/harness/proxy_process.py` 是现成模板；
   `test_seal_process.py` 是现成测试样式）。
2. 负样本：断言臂父进程环境无 `ARC_API_KEY`、read_secret 抛错、
   哨兵请求仍能经代理达上游（mock 上游即可，零花费）。
3. `STATUS.md` 把 GAP-5 从「只登记」改为「已拆分」，注明 commit。

验收：mock 整局在父进程无钥匙状态下跑通；GAP-5 段落更新。零花费。
绿了之后 bare_cc 恢复飞行资格，p1-seal-test 左合取项对三臂成立。
