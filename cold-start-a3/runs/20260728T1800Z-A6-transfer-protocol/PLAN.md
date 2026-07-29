# A6 · plan on disk, written before the code

Board item `A6-transfer-protocol`, worker `W-5201`, cell A3, territory
`cold-start-a3`.  Branch `agent/a6-transfer-protocol`, worktree
`.worktrees/a6-transfer-protocol/`.

## What the item asks for

> A3 证明了 domain 带得走（离线，四条边界见 A3_REPORT §6，其中一条严重）。工程化两件：
> **携带包格式**（domain + playbook 定理级条目 + 依赖指纹）与 **problem 重建器**
> （从首帧重建关卡实例的通用形态，不是 A3 世界专用）。验收：拿 worldgen 产的两个
> 同机制异布局世界端到端验证，且 A3 的两个负对照在新形态下同样被抓住。接口写进
> RUN_STATE 供 theoria-arm 调用，不改对方目录。

## The two worlds

`worldgen/out/worlds/INDEX.json` declares exactly one **same mechanism, different
layout** pair, and its `variant_delta` says so in those words:

| | `t1-push-open` | `t1-push-corridor` |
|---|---|---|
| grid | 5×7 | 5×6 |
| families | `push` | `push` |
| agent start | (2,2) | (1,1) |
| block | (2,3) | (1,3) |
| goal | (2,5) | (3,4) |
| optimal | 5 | 5 |
| `push` witnesses in the trace | 2 (RIGHT only) | 1 (RIGHT only) |
| `reversibility_score` | 1.0 | 0.75, `push` is `single_witness` |

Direction of carry is **open → corridor**, and it is not arbitrary: the corridor
is the world `worldgen/README.md` names as the A0 failure mode (`push` has one
witness and no way to obtain a second).  Books written there would be books
written on one witness.  Books written on the open room and *carried* to the
corridor is the honest direction, and it is the direction A0′ argues for.

## Deliverables

1. `a6carry/pack.py` — **carrypack v1**.  A directory holding the two books
   verbatim plus `PACK.json`: theorem-grade entries lifted from the parsed AST
   (not retyped), the `requires` block (objects↔colours, landmarks, supplied
   constants, action vocabulary, guard contexts, semantics, emittable forms) and
   a **dependency fingerprint** over every upstream module the compile path
   touches.
2. `a6carry/rebuild.py` — the **generic problem rebuilder**.  `requires`-driven,
   not A3-shaped: it is handed the colour bindings rather than holding them.
   Preflight refuses (loudly, structured) before a single action is spent.
3. `a6carry/protocol.py` — the online driver, with a pluggable `Executor`.  This
   is the interface `theoria-arm` calls; it is written into `RUN_STATE.md`.
4. Two executors: `worldgen` (read-only import of another track's library) and
   `a3world` (A3's own, for the negative controls).
5. `theory/push/` — the push manual, theorized from `t1-push-open`'s trace.
6. Acceptance: source arm on `t1-push-open`, transfer arm on `t1-push-corridor`,
   both to a **won** game with a green replay; A3's `l2-oneway` and `l2-rewired`
   re-run through the **new** protocol and still caught.

## Known hazards, found by reading before writing

* **The fingerprint has no consumer.**  `monitor/inbox/20260728T082700Z-W-1521`
  reports that `_bootstrap.upstream_pin()` writes a sha256 of every upstream file
  into every manifest and *nothing in the repository ever compares two of them* —
  a check that is not even optional, it has no reader.  carrypack's fingerprint
  is only worth adding if the protocol **refuses to run** on drift.  It does.
* **`gen_pddl_a0` cannot move a second object.**  Its state is `(at ?c)` plus one
  `(switched)` boolean; `moved(Block, right)` compiles to a *second Cart move*
  and the Block stays an immovable obstacle.  On `t1-push-open` the only route
  runs through the Block, so the planner answers a confident **UNSAT for a
  correct manual** — D-A3-005's failure family, from a different direction.
  A6 patches it in A6's own tree.  → D-A6-001.
* **`gen_lean_a0` cannot see a second object's position.**  `build_axes` collects
  only non-mover fields ending `_colour`/`_present`, so `Block_pos` is not a
  state axis: the Lean file would be a certificate about a *projection* of the
  manual, silently.  That is not patchable without rewriting the generator, which
  is another track's file and outside this item.  The pack therefore declares
  which forms it may be compiled to, and the protocol **withholds** the Lean form
  rather than emitting a green one that proves the wrong thing.  → D-A6-002.

## Red lines

Sealed pile: zero contact, no network, no API spend, no key read.  Writes confined
to `cold-start-a3/` plus an appended `PARTNER_SYNC.md` paragraph and a
`monitor/inbox/` note.  `worldgen/`, `cold-start-a0/`, `engine-rig/`,
`theory-compiler/`, `CONTRACTS/` are imported and hashed, never written.
