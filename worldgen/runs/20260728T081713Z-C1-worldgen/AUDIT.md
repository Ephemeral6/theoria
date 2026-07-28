# Audit of the inherited `worldgen/` remnant — 2026-07-28

The board item says the predecessor's branch is "可读可弃" (readable, discardable).
It was read. The architecture was kept and the artefacts were not: two
independent adversarial reviews (one over `mechanisms/`, one over `core/` and the
shipped outputs) and one measurement run agreed that the skeleton is sound and
that **both properties the library is sold on are false in the shipped output**.

Adoption decision: **keep the architecture, rebuild the catalogue.** The state
encoding (`State = (agent, vars)` with disjoint per-mechanism slices), the
mechanism dispatch order, the exact-reachability solvability decision and the
trace writer are good and are kept. Everything the audits list below is repaired
in this run, and every world is rebuilt and re-measured afterwards.

Two facts about the remnant that are not defects but matter:

* the shipped `out/worlds/` was **stale** — built from an earlier state of the
  code. A rebuild changed `unsolvable`, `invariant_failures`,
  `claim_disagreements` and `mean_reversibility`. The numbers below are from the
  rebuild, not from the stale files;
* the build **is** byte-deterministic run to run (verified: two consecutive
  builds hash identically, and the auditor reproduced it across three
  interpreters at `PYTHONHASHSEED` 1/2/3). F7 is about the *gate*, not the
  property.

## Findings

Severity is the auditors'; `#n` are the mechanism audit's numbering, `Fn` the
core audit's. Where both found the same thing it is listed once.

| id | severity | where | what |
|---|---|---|---|
| **F1** | critical | `core/reversibility.py:143` | `unbounded = any(can_reach(t, s) for t in targets for s in sources)` quantifies over the **cross product** of firing targets and firing sources, where the docstring specifies a firing transition reaching **its own** source. Firing A reaching firing B's source is not a cycle. Two consequences: every finite-but-repeatable rule is stamped `UNBOUNDED`, and the `else` branch is dead — if no `(t,s)` pair reaches, `edges[i]` is empty for all `i`, so `longest(i) == 1` always. Across 20 worlds: 94 rules read `-1`, 8 read `1`, **none** reads anything else. The graded measurement does not exist. This is the A0′ criterion the item names as the framework finding, so it is the single most important defect here. |
| **F2 / #1** | critical | `mechanisms/portal.py:132` | Uses `world.is_free` for the teleport landing cell. `is_free` excludes `no_rest`, and `Portal` never overrides `no_rest`, so the default (`base.py:134` — every cell the mechanism owns) puts **both mouths** in it. For `mode="twoway"` the landing cell *is* the partner mouth, so `is_free` is always false and `teleport_twoway` **never fires in any world in the catalogue**. `t2-portal-pair` collapses to 5 reachable states and ships unsolvable; the `t2-portal-pair`/`t2-portal-paired` contrast pair is confounded because one half is dead code. `world.py:119` says in as many words that `can_stand` is the predicate "used by teleports"; the teleport is its only non-caller. |
| **F3** | critical | `generate.py` (`switch_art`), `build.py:118` | The catalogue's solvability labels are inverted. **`t2-unsolvable-nodoor` — the world whose declared purpose is to ship an unsolvability certificate — is solvable in 5 steps** (`DOWN DOWN RIGHT RIGHT RIGHT`): the door sits at `(2,4)` but rows 1 and 3 are open floor, so it fences nothing. The same geometry means `t1-switch-toggle` and `t1-switch-latch` are winnable **without ever touching the switch** — the headline mechanic is decorative in three worlds. `t3-full-house`'s block is walled on two opposite sides, so `push` can only ever be `blocked_by_block`. Nothing asserts an *intended* solvability, so the inversion shipped silently. |
| **#2** | high | `mechanisms/switch_door.py:112` | A door can close **under the agent**. Toggle a switch adjacent to a door the agent is standing on: `(2,2) in occupied(state)` while `state.agent == (2,2)`, the mechanism's own `door_presence_tracks_net` invariant returns False, and the renderer paints the agent last so the closed door's colour is erased. This is the `invariant_failures: ["t2-switch-push"]` the stale index reported. |
| **#3** | high | `mechanisms/gravity.py:70`, `:117` | Gravity uses `is_free` for the **agent**, so the agent will not fall onto a cell that any mechanism owns — including a token cell already collected, which renders as bare floor. The agent hovers with plain floor rendered directly beneath it, in a world whose ground truth says everything falls. The self-check `nothing_rests_on_a_free_cell` evaluates the *same wrong predicate*, so it reports True on exactly the states it exists to reject. An invariant that reuses the implementation's predicate tests nothing. |
| **F4** | high | `core/truth.py:47` | The rule table is hand-written prose concatenated from each mechanism's `truth_rules`. Only `name` is tied to `Outcome.rule`, **and only by convention — nothing checks either direction**. Measured drift: `fall` and `up_is_inert` (`gravity.py`) and `door_mirrors_net` (`switch_door.py`) are **not `Outcome.rule` tags at all** — they describe the `settle` cascade, which never names a rule — so `GROUND_TRUTH.md` prints them `unreachable` in 7 worlds, which is a false statement about a mechanism that fires on nearly every step. A reader cannot distinguish "impossible by design" from "impossible by bug" (`teleport_twoway` reads the same way, and is F2). |
| **F5** | high | `build.py:172` | 7 of 20 worlds ship non-empty `claim_disagreements`; `main()` prints them and returns **0**. Only `--check` can fail the build and only on determinism. Every current disagreement is a false alarm produced by F1 — which means a *real* disagreement is now indistinguishable from the standing noise. |
| **#4** | medium | `mechanisms/gravity.py:103` | The `up_is_inert` ground-truth rule is false and is published with `reversible: True`. Gravity's `interact` claims nothing, so `UP` dispatches to whoever owns the cell above and several of them mutate state before the fall-back: one `UP` into a fragile tile leaves the agent where it started and the tile **permanently collapsed**. Same for a toggle, a latch, or a shut cycler. |
| **#5** | medium | `mechanisms/portal.py:132` | `is_free` also rejects `cell == state.agent`, which is right for placing an object and wrong for the agent's own destination — it has already left. Any paired portal whose mouths are two apart is silently inert in one direction. |
| **F6** | medium (latent) | `worldgen/` | **No `.gitattributes`**, and `core.autocrlf` is true on this machine. Every sibling artefact directory pins `* text eol=lf`. The tree is entirely untracked today, so it has not bitten — but the *first commit* normalises the `.jsonl`/`.json`/`.md`, the next Windows checkout materialises CRLF, `write_trace`'s `newline="\n"` stops matching the working tree, and the traces stop being byte-identical to the reference producer. Must be fixed **before** the directory is first committed. |
| **#6** | low/medium | `mechanisms/base.py:134` | `no_rest` is static: a collected token's cell renders as bare floor but stays unpushable-onto forever. The *state* still determines it (the token var is set), so it is not a frame-determinism violation, but a reader sees a block that will not move onto empty floor with nothing in the frame to explain it. |
| **F7** | low | `build.py:134` | `check_determinism` builds the comparison copy **in the same process**, so `PYTHONHASHSEED` is shared and hash-order nondeterminism is invisible to it; it also diffs against the module constant `OUT` rather than the `root` it was asked to build. Determinism is real; the gate does not demonstrate it. |
| **F8** | low | `core/solvability.py:101` | `blocking_entities` deletes one entity at a time, so on a paired portal both deletions leave an unpaired mouth, `GridWorld` raises, and the certificate names no blocker — exactly the sentence an unsolvable world exists to produce. |
| **F9** | low | `core/reversibility.py:153` | `longest` is recursive behind a `setrecursionlimit` bump (past the real C stack this is a hard interpreter crash, not an exception), and writes `depth[i] = 1` *before* exploring children, which is a wrong memo on any cyclic graph. Both are unreachable today only because F1 makes `edges` always empty — they go live the moment F1 is fixed, and `t3-latch-maze` already has 858 firing transitions for `walk`. |

## The fix hazard the mechanism audit flagged

`consumable.py:104` renders `ARMED` identically to `INTACT`, justified by the
agent always covering it. That holds **only because** gravity and portals
currently use `is_free` and therefore can never deposit the agent onto a fragile
tile without going through `interact`. So the naive repair for F2 and #3 — swap
`is_free` for `can_stand` — would make `(agent on tile, INTACT)` and `(agent on
tile, ARMED)` both reachable and pixel-identical: a genuine
frame-does-not-determine-state bug, which is worse than what it fixes. The
library is missing a third predicate. That is how it is repaired here.

## What the QC harness independently found

Before any repair, on the pre-repair catalogue:

* `t1-switch-toggle` — replay accuracy **0.967**, below the 1.0 the bar requires;
  the mined rules contradict transitions they were mined from;
* `t1-switch-latch` — replay 1.0, held-out 0.845;
* `t2-lock-fragile` — `NoSeparatingGuard: no literal separates transition 1 from
  the positives`. The miner cannot synthesise a rule set at all.

The render self-check passed exactly (168/168 and 89/89 frames), so the
board-plus-tracks decomposition reproduces observed frames and these numbers are
measuring rules rather than the renderer.
