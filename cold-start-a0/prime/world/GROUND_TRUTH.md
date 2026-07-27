# GROUND_TRUTH — A0′ referee's copy

**Do not open while theorizing.** Scoring only; the first read is stamped in `prime/THEORIZE_LOG.md`.

## Rules

| name | when | then |
|---|---|---|
| `push` | act=D and the target cell is floor or the open Door | the Cart moves one cell in direction D |
| `toggle` | act=D and the target cell is the Switch | the Switch flips 7<->8 and the Door mirrors it (present iff 7); the Cart does not move.  Works from all four directions, both ways. |
| `teleport` | act=D and the target cell is the Portal marker | the Cart moves to (1,1) |
| `blocked` | act=D and the target is a wall, the Crate, or the closed Door | nothing happens |

## Invariants

* **cart_unique** — exactly one cell shows colour 6
* **door_mirrors_switch** — the Door is present if and only if the Switch shows 7
* **right_room_locked (a0p-no-switch only)** — with no Switch the Door never opens, so the Cart never occupies a right-room cell
