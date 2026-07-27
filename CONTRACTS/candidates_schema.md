# candidates_schema.md（冻结 v0.1，任何一方不得修改此文件本身）
引擎的每条提案是 candidates.jsonl 里追加的一行 JSON 对象：
{
  "id": "<uuid>",
  "engine": "<mdl_segmenter|cegis_miner|zero_space|lp_potential|fd_adapter|probe_frontier>",
  "kind": "<object_hypothesis|rule_hypothesis|invariant|heuristic|plan|probe_design>",
  "payload": { ... 引擎自定义,kind 相同的 payload 形状需在本引擎的 README 里写清楚 ... },
  "evidence": {"transitions": [<int>, ...], "coverage": "<k>/<n>"},
  "status": "candidate",
  "timestamp": "<ISO8601>"
}
规则：
- 本文件只追加（append-only），任何引擎不得删除或修改已写入的行。
- status 字段永远是 "candidate"——引擎不裁决,裁决是 theorize(LLM)的事,不发生在这个 sprint 里。
- 每个引擎各自的 payload 形状由该引擎目录下的 README.md 定义并保持稳定。
