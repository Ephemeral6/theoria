# Theoria

> Playing as a Byproduct: A Theory-Maintaining Agent Framework for Interactive Worlds

一个研究框架：让 LLM 维护一份**显式的世界理论**，而不是把世界隐式地编码进权重。

LLM 只写两本书 —— **说明书**（世界是什么）与**攻略**（怎么赢）—— 两本书编译出四种
共导出形式：Lean / Python / PDDL / Markdown。精确的活儿（分割、规则挖掘、线性代数、
搜索）外包给引擎。**引擎提议，LLM 裁决。**

完整设计见 [Theoria.md](Theoria.md)。做任何实质性工作前先读它。

## 目录结构

| 目录 | 内容 |
|---|---|
| [`theory-compiler/`](theory-compiler/) | DSL 及其生成器（两本书 → 四种形式） |
| [`engine-rig/`](engine-rig/) | 六个引擎，全部离线对合成 fixture 验证 |
| [`arc-recon/`](arc-recon/) | API 访问检查与 pile cut（两条 track 共用） |
| [`cold-start-a0/`](cold-start-a0/) | A0 冷启动世界与流水线 |
| [`CONTRACTS/`](CONTRACTS/) | 冻结的跨 track 契约 |

两条 track（`theory-compiler` / `engine-rig`）并行推进，互不通信，只通过 git 历史和
[`PARTNER_SYNC.md`](PARTNER_SYNC.md) 相互可见。

## 快速开始

```bash
cd engine-rig && python -m pytest
```

```bash
cd theory-compiler && pip install -e ".[dev]" && pytest
```

engine-rig 的六个引擎（`mdl_segmenter`、`cegis_miner`、`zero_space`、`lp_potential`、
`fd_adapter`、`probe_frontier`）端到端跑一遍：

```bash
cd engine-rig && python -m tools.run_all --force
```

## 凭据

ARC API key 放在仓库根目录的 `.env` 里（变量名 `ARC_API_KEY`）。`.env` 已被 gitignore
且必须保持如此 —— 见 [`.env.example`](.env.example)。凭据只在环境代理内部注入，不进入
仓库、设计文档或任何一条 track。

## 两条已知的注意事项

* **Fast Downward 未接入。** `fd_adapter` 在同一个 `solve(domain, problem)` 接口后面跑的是
  grounded-STRIPS BFS stub（单位代价下长度最优）。装好 FD 放进 PATH，或设置
  `FAST_DOWNWARD`，adapter 会自动接管，调用方无需改动。
* **`lp_potential` 可靠但不完备。** 它从不把可解配置误判为不可解，但确实有一些真正不可解
  的配置不存在线性 pagoda 证书。

## 许可证

[MIT](LICENSE)
