priority: 2
cell: A20
territory: proxy
deps: none

# A20-model-side-bypass-negative · 密封测试右合取项的模型侧负样本

p1-seal-test 右合取项（绕开双代理的出网必须失败）现只有环境侧覆盖
（`test_bypass_negative.py`）。模型侧 2026-08-01 起有了所有者裁决的常态：
模型调用走 Claude 订阅额度的 vendor CLI（D-P8-002；封存裁决见
`monitor/spec.py` p1-proxy-model 注记末段）——「双代理」的模型半边
正式读作『CLI 包络 + 臂内无供应商凭据』。

据此把右合取项的模型侧变成可测断言（proxy 领地，零花费）：

1. 负样本一：断言 `.env` 与臂进程环境**不存在** `ANTHROPIC_API_KEY`
   等供应商凭据变量（以变量名核验，永不读值——凭据卫生纪律）。
2. 负样本二：无凭据直连供应商端点必须失败——mock 侧断言 401 路径；
   已有的 65-of-65 全 401 史实（`verify-lab/DUAL_PROXY.md` S32 分母）
   作为活证据引入测试文档字符串。
3. 在 `proxy/tests/test_bypass_negative.py`（或姊妹文件）落地，
   并在 DUAL_PROXY.md 附一段「右合取项模型侧的订阅传输读法」，
   引所有者裁决日期。

验收：新负样本入 suite 且红绿可翻（把 mock 凭据塞进环境须变红）。
绿了之后 p1-seal-test 右合取项两侧都有负样本覆盖，只剩 bare_cc
（A19）一角。
