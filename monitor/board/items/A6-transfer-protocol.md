priority: 3
cell: A3
territory: cold-start-a3
deps: none
lane: campaign
spend: api

# A6 · 把 A3 的迁移协议做成在线可用的形态

A3 证明了 domain 带得走（离线，四条边界见 A3_REPORT §6，其中一条严重）。工程化两件：**携带包格式**（domain + playbook 定理级条目 + 依赖指纹）与 **problem 重建器**（从首帧重建关卡实例的通用形态，不是 A3 世界专用）。验收：拿 worldgen 产的两个同机制异布局世界端到端验证，且 A3 的两个负对照在新形态下同样被抓住。接口写进 RUN_STATE 供 theoria-arm 调用，不改对方目录。
