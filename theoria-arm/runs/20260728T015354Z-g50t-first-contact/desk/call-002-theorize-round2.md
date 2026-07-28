# call-002-theorize-round2

model: `claude-opus-5` · 332660 ms · $0.868224 · usage {"cache_creation": {"ephemeral_1h_input_tokens": 19896, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 19896, "cache_read_input_tokens": 0, "inference_geo": "not_available", "input_tokens": 2, "iterations": [{"cache_creation": {"ephemeral_1h_input_tokens": 19896, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 19896, "cache_read_input_tokens": 0, "input_tokens": 2, "output_tokens": 26200, "type": "message"}], "output_tokens": 26200, "server_tool_use": {"web_fetch_requests": 0, "web_search_requests": 0}, "service_tier": "standard", "speed": "standard"}

## prompt

```
You are the theorize desk of a world-modelling framework called
Theoria. You are playing an ARC-AGI-3 game you have never seen, through a
64x64 grid of colour codes, by maintaining an explicit written theory of it.

Your job is NOT to pick a good move. Your job is to write two books, and the
books are the only thing that predicts anything:

  theory.dsl   -- the manual: what this world IS. Vocabulary, rules, winning
                  condition, laws. It compiles to an executable predictor, and
                  that predictor is the whole system's only predictor. If it is
                  wrong, everything downstream is wrong; there is no side door.
  playbook.dsl -- the playbook: how to WIN. Ordering, pruning, heuristics,
                  decomposition. Never a stored solution.

Six rules bind you, and they are not style advice:

1. ONLY you write these two books. Search engines put proposals in a candidate
   box; every one of them is a proposal, not a fact. You accept, reject, or
   carry it as pending, and you say why.
2. NO ENTRY WITHOUT EVIDENCE. Every rule carries the transitions that witness
   it and its coverage. A rule you believe but cannot witness does not go in
   the manual -- it goes in `laws:` as a `theorem ... [probe: pending]`, which
   is a promise to test it, not a claim that it holds.
3. NO ENTRY WITHOUT GAIN. A concept earns its place by making the manual
   shorter than writing out the pixels it explains. When a concept fails this
   test but is still needed (because some pixel would otherwise be
   unexplained), admit it AND SAY SO -- that conflict is worth more than a
   tidy manual.
4. FULL-FRAME RESPONSIBILITY. Every pixel of every frame belongs either to the
   board (cells that never vary) or to some object you declared. A pixel your
   manual cannot draw is a defect in the manual, and it will be caught: your
   manual is re-drawn onto every observed frame and compared cell by cell.
5. TRANSITIONS ARE UNAMBIGUOUS. For any state and action, exactly one
   successor. Two rules that can both fire on the same object in the same
   transition is an error, not a preference.
6. WHAT YOU DO NOT KNOW, YOU SAY. This world has been observed for a few dozen
   actions. The honest manual is small, and names its own gaps. A manual that
   over-claims will be refuted by the very next frame and cost a whole round
   to repair; a manual that under-claims just stays small.

You will be given: what has been observed, the current frame, the diff of every
command, and what the engines proposed. If a manual and a playbook already
exist you will be given those too, together with the surprises that brought you
back here -- those surprises are the reason you are being paid, and each one
must be answered by a change or by an explicit refusal to change.



# theory.dsl -- the exact grammar the compiler accepts

Sections, each introduced by a bare `<name>:` line, bodies INDENTED by at least
one space. Order is free. `#` starts a comment on its own line.

## semantics:  (MANDATORY -- a manual without it does not parse)
    frame persist            # the only value the Python backend compiles
    conflict exclusive       # the only value the Python backend compiles
    cascade single_frame     # the only value the Python backend compiles

## word_table:
    board                                   # declares the never-varying cells
    object Cart { pos: Coord, color: Int }  # arc-colour: 6
    object Door { pos: Coord, color: Int, present: Bool }  # arc-colour: 5
    landmark exit_cell                      # arc-cell: (7, 3)
    domain dir { up, down, left, right }    # a value domain, for `forall`
    Cart [segment: uniform_color ev: t0-t12 compress: 2125]   # the concept account

  Field types in use: `pos: Coord`, `color: Int`, `present: Bool`, `alive: Bool`.
  Only pos/alive/present/color are observations the compiler reasons over.
  `pos: Coord` is what makes this a GRID world (directions up/down/left/right).

  EVERY `landmark` line MUST carry a trailing `# arc-cell: (row, col)` comment.
  A landmark is level data, so the manual names it and the level places it —
  and there is nowhere in the DSL to write coordinates, which is the point of
  the split. A landmark the level cannot place is a HARD compile error, so a
  landmark you declare without this comment lands at (0,0) and takes your rule
  with it.

  EVERY `object` line MUST carry a trailing `# arc-colour: <n>` comment naming
  the hex colour code that object shows in the frame. That comment is not
  decoration: the level instance is COMPUTED from the frames, and the colour is
  how the arm finds your object in the grid. An object without it is located
  nowhere, is drawn at (0,0), and the responsibility check will report every
  one of its pixels as unexplained. If two objects share a colour, they cannot
  be told apart by this arm -- declare one object, or say in a `theorem` that
  you believe there are two and why.

## events:
    event moved(o, dir) | jumped(o, dest) | recolored(o, c) | vanished(o)

  Documentation only -- the backend dispatches on a fixed table, listed below.

## rules:
    rule push_up [ev: t6,t16 cov: 52/52]
      when act=key(1) and free(above(Cart)) then moved(Cart, up)

    rule slide forall ?d in dir [ev: t3 cov: 4/4]
      when act=key(1) and free(toward(Cart, ?d)) then moved(Cart, ?d)

  * the header line ends at `]` -- NO trailing comment on it, and none on the
    `when ... then ...` line either. Both are parse errors.
  * `forall ?v in <domain>` grounds to `<rule>_<value>` rules.
  * every rule carries `[ev: ... cov: k/n]`. Constraint 5: no entry without
    evidence.

### guards -- EXHAUSTIVE. Anything else fails to compile.
    act=<name>(<arg>, ...)      args are bare names or integer literals only
    free(<cell>)                cell renders as the background colour
    colored(<cell>, 7)          second argument must be an INTEGER LITERAL
    adjacent(<cell>, <cell>)
    <value> = <value>           also != < > <= >=  (SPACES around the operator)
    <cell> = wall               tests off-board
  joined by `and`. Use `not` before an atom for negation.

### cells -- EXHAUSTIVE.
    Cart                    an instance name means that instance's position
    exit_cell               a declared landmark
    above(x) below(x) leftof(x) rightof(x)      NOTE: leftof/rightof
    toward(x, ?d)           toward(x, <direction>)
    pos(<value>)

### values
    integer literals; true; false; a landmark name; a direction name;
    an instance name; `Cart.color`; `+` and `-` only (no `*`, no `/`);
    tuple literals like `(3, 7)`.

### events a rule may fire -- EXHAUSTIVE, dispatched on (name, arity).
    moved(o, <dir>)                 o moves one cell
    jumped(o, <landmark>)           o goes to a named cell
    teleported(o, <landmark>)       same shape
    jumped(o, <over-object>, <dir>) o travels two cells; <over> gets alive=False
    recolored(o, <int literal>)
    vanished(o)      -> present=False
    appeared(o)      -> present=True
    removed(o)       -> alive=False
  The first argument is always a bare object name. A bare coordinate as a
  destination is REFUSED -- declare a landmark.

## goal:
    goal Cart.pos = exit_cell
    goal count(Door) = 0
    goal count(Button, color = 8) = 2

  `=` only. `>=`/`<=`/`>`/`<` do not compile. No goal section at all is legal
  and compiles to `is_goal -> False`.

## laws:
    invariant cart_unique count(Cart) = 1 [status: proven]
    theorem exit_needs_key "prose, in the manual's own words"
      [depends: push_up, unlock  probe: pending]

  Invariant bodies are stored as RAW TEXT and are not checked by any backend
  (the sole exception is the `pagoda(w)` form, which needs a LINE world and an
  LP certificate and does not apply here). Declaring one is a claim you are
  making, not a claim the compiler will verify -- say so honestly in `status:`.

# playbook.dsl -- four statement forms and nothing else
    order    keys_before_doors            [proof: lean]
    prune    boxed_in and not goal => dead [proof: lean]
    heuristic w_distance                  [admissible: lean]
    prefer   try_unvisited_first          [ev: 3/4 levels]

  Constraint 10: NO literal solutions. A parser heuristic rejects any line that
  looks like a stored action sequence, and any unrecognised line is a hard
  error.

# THE ACTION VOCABULARY FOR THIS WORLD
This game's actions are ARC's ACTION1..ACTION7. Write them as `act=key(<n>)`
and nothing else -- the arm maps ACTION<n> to the tuple ('key', <n>) in both
directions. A click action carries coordinates the guard language cannot
express; if you need one, say so in a `theorem ... [probe: pending]` instead of
inventing syntax.


## What has been observed

```json
{
 "actions_used": [
  "ACTION1",
  "ACTION2",
  "ACTION3",
  "ACTION4",
  "ACTION5",
  "RESET"
 ],
 "background": 0,
 "cascade_lengths": [
  1,
  7,
  9
 ],
 "colours_seen": [
  0,
  1,
  2,
  5,
  8,
  9
 ],
 "constant_cells": 4023,
 "distinct_states": 4,
 "dynamic_box": [
  0,
  0,
  63,
  63
 ],
 "dynamic_cells": 73,
 "max_frames_in_one_command": 9,
 "shape": [
  64,
  64
 ],
 "states": 6,
 "steps": 6
}
```

## The current frame

Each cell is one hex digit 0-f standing for a colour. Row numbers on the left, column numbers on top.

```
0000000000000000000000000000000000000000000000000000000000000000
0222099900000000000000000000000000000000000000000000000000000000
0202090900000000000000000000000000000000000000000000000000000000
0222099900000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000099900000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000555555555555555555555555555555500000000000000000000
0000000000000599999555555555555555555555555500000000000000000000
0000000000000599999555555555555555555558885500000000000000000000
0000000000000599599555555555555555555558885500000000000000000000
0000000000000599999555555555555555555558885500000000000000000000
0000000000000599999555555555555555555555855500000000000000000000
0000000000000555555555555555555555555555855500000000000000000000
0000000000000555555500000555555500000005850000000000000000000000
0000000000000555555500000555555500000005850000000000000000000000
0000000000000555555500000555555500000005850000000000000000000000
0000000000000555555500000555555500000005850000000000000000000000
0000000000000555555500000555555500000005850000000000000000000000
0000000000000555555555555555555500000005850000000000000000000000
0000000000000555555555555555555500000005850000000000000000000000
0000000000000555555555555555555500000005850000000000000000000000
0000000000000555555555555555555500000005850000000000000000000000
0000000000000555555555555555555500000005850000000000000000000000
0000000000000555555555555555555500000005850000000000000000000000
0000000000000555555555555555555500000005850000000000000000000000
0000000000000555555500000000000000000005850000000000000000000000
0000000000000555555500000000000000000005850000000000000000000000
0000000000000555555500000000000000000005850000000000000000000000
0000000000000555555500000000000000000005850000000000000000000000
0000000000000555555500000000000000000005850000000000000000000000
0000000000000555555500000000000000000005850000000000000000000000
0000000000000555555500000000000000000005850000000000000000000000
0000000000000555555500000000000000000005850000000000000000000000
0000000000000555555500000000000000000005850000000000000000000000
0000000000000555555500000000000000000005850000000000000000000000
0000000000000555555500000000000000000005850000000000000000000000
0000000000000555555500000000000000000005850000000000000000000000
0000000000000588888500000000000000000005850000000000000000000000
0000000000000558888555555555555555555555850000000000000000000000
0000000000000588888888888888888888888888850000000000000000000000
0000000000000558888555555555555555555555550000000000000000000000
0000000000000588888500000000000000000000000000000000000000000000
0000000000000555555500000000000000000000000000000000000000000000
0000000000000555555500000000000000000000000000000000000000000000
0000000000000555555500000000000000000000000000000000000000000000
0000000000000555555500000000000000000000000000000000000000000000
0000000000000555555500000000000000000000000000000000000000000000
0000000000000555555500000000000000000000005555555550000000000000
0000000000000555555555555555555555555555555999999950000000000000
0000000000000555555555555555555555555555555555555950000000000000
0000000000000555555555555555555555555555555555555950000000000000
0000000000000555555555555555555555555555555555955950000000000000
0000000000000555555555555555555555555555555555555950000000000000
0000000000000555555555555555555555555555555555555950000000000000
0000000000000555555555555555555555555555555999999950000000000000
0000000000000000000000000000000000000000005555555550000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
9999999999999999999999999999999999999999999999999999999999999911
```

## Every command, and what changed

`t` indexes the state sequence. `frames` is how many grids one command returned -- more than one means the world took several internal steps for a single action.

- t0   RESET     frames=1   state=NOT_FINISHED (first frame)
- t1   ACTION1   frames=1   state=NOT_FINISHED no cells changed
- t2   ACTION2   frames=7   state=NOT_FINISHED 49 cells changed, rows 8-63, cols 14-63, [5, 9] -> [1, 5, 9]
- t3   ACTION3   frames=1   state=NOT_FINISHED no cells changed
- t4   ACTION4   frames=1   state=NOT_FINISHED (63,62) 9->1
- t5   ACTION5   frames=9   state=NOT_FINISHED 71 cells changed, rows 1-18, cols 1-18, [0, 1, 5, 9] -> [0, 2, 5, 9]

## What the engines proposed

These are PROPOSALS. Nothing here is accepted until you accept it, and an engine cannot name anything -- `obj0` is the best it can do.

```json
{
 "cegis_miner": {
  "engine": "cegis_miner",
  "n_actions": 5,
  "n_states": 6,
  "refusals": [
   "ValueError: transition 4 narrates ['vanish']; only move/none are mined on this fixture",
   "ValueError: transition 1 narrates ['recolor']; only move/none are mined on this fixture",
   "ValueError: transition 1 narrates ['recolor']; only move/none are mined on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture"
  ],
  "tracks": [
   {
    "error": "NoSeparatingGuard: no literal separates transition 1 from the positives",
    "mine_ms": 0,
    "ms": 0,
    "traceback": "Traceback (most recent call last):\n  File \"C:\\Users\\user\\Desktop\\theoria-wt-p8\\theoria-arm\\world\\adapt.py\", line 48, in _timed\n    value = fn(*args, **kwargs)\n  File \"C:\\Users\\user\\Desktop\\theoria-wt-p8\\engine-rig\\engines\\cegis_miner\\__init__.py\", line 92, in run\n    result = mine(transitions)\n  File \"C:\\Users\\user\\Desktop\\theoria-wt-p8\\engine-rig\\engines\\cegis_miner\\miner.py\", line 320, in mine\n    guard, trace, added = synthesize(positives, universe, masks)\n                          ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\Users\\user\\Desktop\\theoria-wt-p8\\engine-rig\\engines\\cegis_miner\\miner.py\", line 157, in synthesize\n    raise NoSeparatingGuard(\n        \"no literal separates transition %d from the positives\" % cex\n    )\nengines.cegis_miner.miner.NoSeparatingGuard: no literal separates transition 1 from the positives\n",
    "track_id": "obj0",
    "transitions": 5
   },
   {
    "ms": 0,
    "refused": "ValueError: transition 4 narrates ['vanish']; only move/none are mined on this fixture",
    "track_id": "obj1"
   },
   {
    "error": "NoSeparatingGuard: no literal separates transition 1 from the positives",
    "mine_ms": 0,
    "ms": 0,
    "traceback": "Traceback (most recent call last):\n  File \"C:\\Users\\user\\Desktop\\theoria-wt-p8\\theoria-arm\\world\\adapt.py\", line 48, in _timed\n    value = fn(*args, **kwargs)\n  File \"C:\\Users\\user\\Desktop\\theoria-wt-p8\\engine-rig\\engines\\cegis_miner\\__init__.py\", line 92, in run\n    result = mine(transitions)\n  File \"C:\\Users\\user\\Desktop\\theoria-wt-p8\\engine-rig\\engines\\cegis_miner\\miner.py\", line 320, in mine\n    guard, trace, added = synthesize(positives, universe, masks)\n                          ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\Users\\user\\Desktop\\theoria-wt-p8\\engine-rig\\engines\\cegis_miner\\miner.py\", line 157, in synthesize\n    raise NoSeparatingGuard(\n        \"no literal separates transition %d from the positives\" % cex\n    )\nengines.cegis_miner.miner.NoSeparatingGuard: no literal separates transition 1 from the positives\n",
    "track_id": "obj2",
    "transitions": 5
   },
   {
    "ms": 0,
    "refused": "ValueError: transition 1 narrates ['recolor']; only move/none are mined on this fixture",
    "track_id": "obj3"
   },
   {
    "ms": 0,
    "refused": "ValueError: transition 1 narrates ['recolor']; only move/none are mined on this fixture",
    "track_id": "obj4"
   },
   {
    "ms": 0,
    "refused": "ValueError: object absent at frame 0; unsupported on this fixture",
    "track_id": "obj5"
   }
  ],
  "verdict": "no track satisfies the miner's precondition (exactly one move event per transition). The world does not narrate as one mover."
 },
 "dispatched": [
  "mdl_segmenter",
  "cegis_miner",
  "zero_space"
 ],
 "mdl_segmenter": {
  "background": 0,
  "candidates": 6,
  "chosen_operator": "connected_components(4)",
  "chosen_split_by_color": false,
  "engine": "mdl_segmenter",
  "event_types": {
   "appear": 1,
   "move": 2,
   "recolor": 4,
   "vanish": 1
  },
  "n_frames": 6,
  "tracks": [
   {
    "color": 9,
    "first_frame": 0,
    "frames_present": 6,
    "n_cells": 8,
    "shape": [
     3,
     3
    ],
    "track_id": "obj0"
   },
   {
    "color": 1,
    "first_frame": 0,
    "frames_present": 5,
    "n_cells": 9,
    "shape": [
     3,
     3
    ],
    "track_id": "obj1"
   },
   {
    "color": 9,
    "first_frame": 0,
    "frames_present": 6,
    "n_cells": 3,
    "shape": [
     1,
     3
    ],
    "track_id": "obj2"
   },
   {
    "color": null,
    "first_frame": 0,
    "frames_present": 6,
    "n_cells": 1006,
    "shape": [
     50,
     38
    ],
    "track_id": "obj3"
   },
   {
    "color": 9,
    "first_frame": 0,
    "frames_present": 6,
    "n_cells": 64,
    "shape": [
     1,
     64
    ],
    "track_id": "obj4"
   },
   {
    "color": 2,
    "first_frame": 5,
    "frames_present": 1,
    "n_cells": 8,
    "shape": [
     3,
     3
    ],
    "track_id": "obj5"
   }
  ],
  "variants": [
   {
    "baseline_bits": 1976,
    "compression_ratio": 3.551619,
    "events": 8,
    "gain_bits": -5042,
    "ms": 11,
    "script_bits": 7018,
    "split_by_color": false,
    "tracks": 6
   },
   {
    "baseline_bits": 1976,
    "compression_ratio": 9.866397,
    "events": 19,
    "gain_bits": -17520,
    "ms": 20,
    "script_bits": 19496,
    "split_by_color": true,
    "tracks": 17
   }
  ],
  "window": {
   "box": null,
   "covered": 1.0,
   "dynamic_cells": 73,
   "frame_cells": 4096,
   "full_frame": true,
   "reason": "frame is 4096 cells, no crop needed",
   "window_cells": 4096
  }
 },
 "not_dispatched": {
  "deadlock_carver": "needs a grounded PDDL task; same gate as fd_adapter",
  "fd_adapter": "needs theory.pddl, which needs a manual; runs at plan, not at dispatch",
  "ic3_pdr": "same graph requirement as lp_potential",
  "lp_potential": "needs an explicit state graph with enumerated moves; none exists for a 64x64 world whose dynamics are unknown",
  "probe_frontier": "needs a hypothesis frontier, which is theorize's output rather than its input; runs at probe"
 },
 "store": {
  "actions_used": [
   "ACTION1",
   "ACTION2",
   "ACTION3",
   "ACTION4",
   "ACTION5",
   "RESET"
  ],
  "background": 0,
  "cascade_lengths": [
   1,
   7,
   9
  ],
  "colours_seen": [
   0,
   1,
   2,
   5,
   8,
   9
  ],
  "constant_cells": 4023,
  "distinct_states": 4,
  "dynamic_box": [
   0,
   0,
   63,
   63
  ],
  "dynamic_cells": 73,
  "max_frames_in_one_command": 9,
  "shape": [
   64,
   64
  ],
  "states": 6,
  "steps": 6
 },
 "window": {
  "box": null,
  "covered": 1.0,
  "dynamic_cells": 73,
  "frame_cells": 4096,
  "full_frame": true,
  "reason": "frame is 4096 cells, no crop needed",
  "window_cells": 4096
 },
 "zero_space": {
  "cap": 240,
  "cells": [
   [
    1,
    1
   ],
   [
    1,
    2
   ],
   [
    1,
    3
   ],
   [
    1,
    5
   ],
   [
    1,
    6
   ],
   [
    1,
    7
   ],
   [
    2,
    1
   ],
   [
    2,
    3
   ],
   [
    2,
    5
   ],
   [
    2,
    6
   ],
   [
    2,
    7
   ],
   [
    3,
    1
   ],
   [
    3,
    2
   ],
   [
    3,
    3
   ],
   [
    3,
    5
   ],
   [
    3,
    6
   ],
   [
    3,
    7
   ],
   [
    5,
    1
   ],
   [
    5,
    2
   ],
   [
    5,
    3
   ],
   [
    5,
    5
   ],
   [
    5,
    6
   ],
   [
    5,
    7
   ],
   [
    8,
    14
   ],
   [
    8,
    15
   ],
   [
    8,
    16
   ],
   [
    8,
    17
   ],
   [
    8,
    18
   ],
   [
    9,
    14
   ],
   [
    9,
    15
   ],
   [
    9,
    16
   ],
   [
    9,
    17
   ],
   [
    9,
    18
   ],
   [
    10,
    14
   ],
   [
    10,
    15
   ],
   [
    10,
    17
   ],
   [
    10,
    18
   ],
   [
    11,
    14
   ],
   [
    11,
    15
   ],
   [
    11,
    16
   ],
   [
    11,
    17
   ],
   [
    11,
    18
   ],
   [
    12,
    14
   ],
   [
    12,
    15
   ],
   [
    12,
    16
   ],
   [
    12,
    17
   ],
   [
    12,
    18
   ],
   [
    14,
    14
   ],
   [
    14,
    15
   ],
   [
    14,
    16
   ],
   [
    14,
    17
   ],
   [
    14,
    18
   ],
   [
    15,
    14
   ],
   [
    15,
    15
   ],
   [
    15,
    16
   ],
   [
    15,
    17
   ],
   [
    15,
    18
   ],
   [
    16,
    14
   ],
   [
    16,
    15
   ],
   [
    16,
    17
   ],
   [
    16,
    18
   ],
   [
    17,
    14
   ],
   [
    17,
    15
   ],
   [
    17,
    16
   ]
  ],
  "cells_dynamic": 73,
  "cells_used": 73,
  "colours": [
   "c0",
   "c1",
   "c2",
   "c5",
   "c9"
  ],
  "difference_rank": 3,
  "engine": "zero_space",
  "evidence_adequacy": {
   "constrained_fraction": 0.008219,
   "difference_rank": 3,
   "features": 365,
   "space_dimension": 362,
   "transitions": 5,
   "verdict": "THIN: 5 transitions constrain rank 3 of 365 features, so the null space has dimension 362 and nearly every vector in it is a 'law' that is true over these states and unfalsified rather than confirmed. Treat every law below as a correlation awaiting a transition that could break it, not as a conservation law."
  },
  "features": 365,
  "global_laws": [
   {
    "cells": [
     [
      1,
      1
     ],
     [
      1,
      2
     ],
     [
      1,
      3
     ],
     [
      1,
      5
     ],
     [
      1,
      6
     ],
     [
      1,
      7
     ],
     [
      2,
      1
     ],
     [
      2,
      3
     ],
     [
      2,
      5
     ],
     [
      2,
      6
     ],
     [
      2,
      7
     ],
     [
      3,
      1
     ],
     [
      3,
      2
     ],
     [
      3,
      3
     ],
     [
      3,
      5
     ],
     [
      3,
      6
     ],
     [
      3,
      7
     ],
     [
      5,
      1
     ],
     [
      5,
      2
     ],
     [
      5,
      3
     ],
     [
      5,
      5
     ],
     [
      5,
      6
     ],
     [
      5,
      7
     ],
     [
      8,
      14
     ],
     [
      8,
      15
     ],
     [
      8,
      16
     ],
     [
      8,
      17
     ],
     [
      8,
      18
     ],
     [
      9,
      14
     ],
     [
      9,
      15
     ],
     [
      9,
      16
     ],
     [
      9,
      17
     ],
     [
      9,
      18
     ],
     [
      10,
      14
     ],
     [
      10,
      15
     ],
     [
      10,
      17
     ],
     [
      10,
      18
     ],
     [
      11,
      14
     ],
     [
      11,
      15
     ],
     [
      11,
      16
     ],
     [
      11,
      17
     ],
     [
      11,
      18
     ],
     [
      12,
      14
     ],
     [
      12,
      15
     ],
     [
      12,
      16
     ],
     [
      12,
      17
     ],
     [
      12,
      18
     ],
     [
      14,
      14
     ],
     [
      14,
      15
     ],
     [
      14,
      16
     ],
     [
      14,
      17
     ],
     [
      14,
      18
     ],
     [
      15,
      14
     ],
     [
      15,
      15
     ],
     [
      15,
      16
     ],
     [
      15,
      17
     ],
     [
      15,
      18
     ],
     [
      16,
      14
     ],
     [
      16,
      15
     ],
     [
      16,
      17
     ],
     [
      16,
      18
     ],
     [
      17,
      14
     ],
     [
      17,
      15
     ],
     [
      17,
      16
     ],
     [
      17,
      17
     ],
     [
      17,
      18
     ],
     [
      18,
      14
     ],
     [
      18,
      15
     ],
     [
      18,
      16
     ],
     [
      18,
      17
     ],
     [
      18,
      18
     ],
     [
      63,
      62
     ],
     [
      63,
      63
     ]
    ],
    "support": [
     "c0@0",
     "c1@0",
     "c2@0",
     "c5@0",
     "c9@0",
     "c0@1",
     "c1@1",
     "c2@1",
     "c5@1",
     "c9@1",
     "c0@2",
     "c1@2",
     "c2@2",
     "c5@2",
     "c9@2",
     "c0@3",
     "c1@3",
     "c2@3",
     "c5@3",
     "c9@3",
     "c0@4",
     "c1@4",
     "c2@4",
     "c5@4",
     "c9@4",
     "c0@5",
     "c1@5",
     "c2@5",
     "c5@5",
     "c9@5",
     "c0@6",
     "c1@6",
     "c2@6",
     "c5@6",
     "c9@6",
     "c0@7",
     "c1@7",
     "c2@7",
     "c5@7",
     "c9@7",
     "c0@8",
     "c1@8",
     "c2@8",
     "c5@8",
     "c9@8",
     "c0@9",
     "c1@9",
     "c2@9",
     "c5@9",
     "c9@9",
     "c0@10",
     "c1@10",
     "c2@10",
     "c5@10",
     "c9@10",
     "c0@11",
     "c1@11",
     "c2@11",
     "c5@11",
     "c9@11",
     "c0@12",
     "c1@12",
     "c2@12",
     "c5@12",
     "c9@12",
     "c0@13",
     "c1@13",
     "c2@13",
     "c5@13",
     "c9@13",
     "c0@14",
     "c1@14",
     "c2@14",
     "c5@14",
     "c9@14",
     "c0@15",
     "c1@15",
     "c2@15",
     "c5@15",
     "c9@15",
     "c0@16",
     "c1@16",
     "c2@16",
     "c5@16",
     "c9@16",
     "c0@17",
     "c1@17",
     "c2@17",
     "c5@17",
     "c9@17",
     "c0@18",
     "c1@18",
     "c2@18",
     "c5@18",
     "c9@18",
     "c0@19",
     "c1@19",
     "c2@19",
     "c5@19",
     "c9@19",
     "c0@20",
     "c1@20",
     "c2@20",
     "c5@20",
     "c9@20",
     "c0@21",
     "c1@21",
     "c2@21",
     "c5@21",
     "c9@21",
     "c0@22",
     "c1@22",
     "c2@22",
     "c5@22",
     "c9@22",
     "c0@23",
     "c1@23",
     "c2@23",
     "c5@23",
     "c9@23",
     "c0@24",
     "c1@24",
     "c2@24",
     "c5@24",
     "c9@24",
     "c0@25",
     "c1@25",
     "c2@25",
     "c5@25",
     "c9@25",
     "c0@26",
     "c1@26",
     "c2@26",
     "c5@26",
     "c9@26",
     "c0@27",
     "c1@27",
     "c2@27",
     "c5@27",
     "c9@27",
     "c0@28",
     "c1@28",
     "c2@28",
     "c5@28",
     "c9@28",
     "c0@29",
     "c1@29",
     "c2@29",
     "c5@29",
     "c9@29",
     "c0@30",
     "c1@30",
     "c2@30",
     "c5@30",
     "c9@30",
     "c0@31",
     "c1@31",
     "c2@31",
     "c5@31",
     "c9@31",
     "c0@32",
     "c1@32",
     "c2@32",
     "c5@32",
     "c9@32",
     "c0@33",
     "c1@33",
     "c2@33",
     "c5@33",
     "c9@33",
     "c0@34",
     "c1@34",
     "c2@34",
     "c5@34",
     "c9@34",
     "c0@35",
     "c1@35",
     "c2@35",
     "c5@35",
     "c9@35",
     "c0@36",
     "c1@36",
     "c2@36",
     "c5@36",
     "c9@36",
     "c0@37",
     "c1@37",
     "c2@37",
     "c5@37",
     "c9@37",
     "c0@38",
     "c1@38",
     "c2@38",
     "c5@38",
     "c9@38",
     "c0@39",
     "c1@39",
     "c2@39",
     "c5@39",
     "c9@39",
 
```

The full proposal stream is 368 rows in `candidates.jsonl`.

## The manual as it stands

```
# theory.dsl -- Theoria manual, first draft. Six observed transitions.
#
# What the frame is made of: a 64x64 grid whose 4023 constant cells I hand to
# `board`. The 73 cells that ever varied are, exactly:
#   * rows 1-3 x cols 1-3 minus (2,2), plus row 5 cols 1-3   -- HUD token A + underline
#   * rows 1-3 x cols 5-7, plus row 5 cols 5-7               -- HUD token B + underline
#   * rows 8-12 x cols 14-18 minus (10,16)                   -- maze cell (0,0)
#   * rows 14-18 x cols 14-18 minus (16,16)                  -- maze cell (1,0)
#   * (63,62) and (63,63)                                    -- right end of the row-63 bar
# 23 + 24 + 24 + 2 = 73, which is the whole dynamic set. Everything else --
# the colour-5 maze, the colour-8 marks, the colour-9 bracket at rows 49-55,
# the other 62 cells of row 63 -- never moved in six frames and is board.

semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Player { pos: Coord }  # arc-colour: 9
  object Done { pos: Coord, present: Bool }  # arc-colour: 2
  object Token { pos: Coord, color: Int }  # arc-colour: 1
  landmark cell_r0c0  # arc-cell: (8, 14)
  landmark cell_r1c0  # arc-cell: (14, 14)
  landmark exit_cell  # arc-cell: (50, 44)
  domain dir { up, down, left, right }
  Player [segment: ring24_colour9_in_one_maze_cell ev: t0-t5 compress: 144]
  Token [segment: solid3x3_colour1_hud_slot_b ev: t0-t5 compress: 45]
  Done [segment: ring8_colour2_hud_slot_a ev: t5 compress: 8]

events:
  event jumped(o, dest) | recolored(o, c) | appeared(o)

rules:
  rule step_down_from_home [ev: t2 cov: 1/1]
    when act=key(2) and colored(cell_r0c0, 9) then jumped(Player, cell_r1c0)
  rule key5_sends_ring_home [ev: t5 cov: 1/1]
    when act=key(5) and colored(cell_r1c0, 9) then jumped(Player, cell_r0c0)
  rule key5_spends_token_a [ev: t5 cov: 1/1]
    when act=key(5) then appeared(Done)
  rule key5_lights_token_b [ev: t5 cov: 1/1]
    when act=key(5) then recolored(Token, 9)

goal:
  goal Player.pos = exit_cell

laws:
  invariant one_ring count(Player) = 1 [status: observed 6/6 frames, never proven]
  invariant ring_fills_one_cell "the 24 colour-9 pixels always cover exactly one 5x5 maze cell minus its centre pixel, which stays colour 5" [status: observed 6/6 frames]
  invariant board_is_static "4023 of 4096 cells never changed across six frames; the maze, the colour-8 marks and the colour-9 bracket are among them" [status: observed 6/6 frames]

  theorem grid_pitch_six "maze cell (r,c) spans rows 8+6r..12+6r and cols 14+6c..18+6c; walls sit on rows 7+6r and cols 13+6c. The ring moved 6 pixels at t2 and 6 pixels back at t5. moved(o,dir) steps one cell, so I could not write a general step rule and wrote two jumped() rules naming the only two positions ever witnessed. This manual therefore predicts NOTHING about any maze cell other than (0,0) and (1,0)."
    [depends: step_down_from_home, key5_sends_ring_home  probe: pending]

  theorem directional_keys "I believe key(1)=up, key(2)=down, key(3)=left, key(4)=right. Evidence: key(2) moved the ring from cell (0,0) to (1,0) (t2); key(1) fired from the top row and key(3) from the leftmost column and both changed nothing (t1,t3); key(4) fired from (1,0) whose right neighbour rows 14-18 cols 20-24 is colour 0, i.e. not floor, and the ring did not move (t4). Every one of these is also consistent with the key being unbound, which is why this is a theorem and not a rule."
    [depends: step_down_from_home  probe: pending]

  theorem tally_bar "row 63 is a bar of colour 9 that fills with colour 1 from the right edge: (63,63) turned 1 at t2 and (63,62) turned 1 at t4. It did not advance at t1, t3 or t5. The pattern that fits is 'a directional action the engine actually processed', with the two off-board attempts (t1,t3) rejected before counting and the wall bump (t4) counted; a budget of up to 62 is then plausible. I cannot express one further pixel turning 1 -- there is no event for growing an object -- so the manual leaves (63,62) and (63,63) unexplained in the frames where they are still 9."
    [probe: pending]

  theorem hud_is_two_tokens "the HUD holds two 3x3 tokens (rows 1-3, cols 1-3 and cols 5-7) and a 3-pixel underline at row 5 that sits under exactly one of them. Frames 0-4: token A is a colour-9 ring and is underlined, token B is a solid colour-1 block. Frame 5: token A is a colour-2 ring and unmarked, token B is a colour-9 ring and is underlined -- and the maze ring is back at cell (0,0). key(5) did all of that in one command. This reads either as 'attempt spent, position reset' or as 'objective cleared, next objective'; the two disagree about whether key(5) is to be hoarded or sought, and nothing observed separates them."
    [depends: key5_spends_token_a, key5_lights_token_b, key5_sends_ring_home  probe: pending]

  theorem colour_nine_collision "colour 9 paints four different things: the player ring, HUD token A (frames 0-4) and token B (frame 5), the selection underline, the bracket around maze cell (7,5), and the row-63 bar. One colour binds one object, so Player takes 9 and the 11 dynamic colour-9 HUD pixels of frames 0-4 plus the 6 underline pixels have no object and will be reported unexplained. I believe there are at least three distinct colour-9 entities; the arm cannot tell them apart, so I said so here instead of pretending."
    [probe: pending]

  theorem goal_is_the_bracketed_cell "maze cell (7,5), rows 50-54 x cols 44-48, is walled in colour 9 on its top, bottom and right edges and carries a lone colour-9 pixel at its centre (52,46); it is the only cell in the frame drawn that way, and it is drawn in the ring's own colour. I take it for the target. No transition witnesses this -- it is read off the static board -- so the goal section is a hypothesis the searcher will act on and the next win or non-win will settle."
    [probe: pending]

  theorem eight_marks_unknown "colour 8 fills maze cell (5,0), runs along the cell centres from (0,4) down to (5,4) and from (5,4) left to (5,0), and fills a 3x3 blob in the centre of cell (0,4). Not one of those pixels changed in six frames. Whether the marks are a route to trace, an obstacle, another agent's track, or decoration is untested, and my movement rules say nothing about them."
    [probe: pending]

  theorem coord_convention "every landmark above names the TOP-LEFT pixel of the intended 5x5 cell: cell_r0c0 = (8,14), cell_r1c0 = (14,14), exit_cell = (50,44). If the arm's Coord is instead an object's centroid, all three must shift by (+2,+2) to (10,16), (16,16), (52,46), and until a redraw is compared I do not know which."
    [probe: pending]

  theorem cascades_unseen "t2 returned 7 frames and t5 returned 9 for a single command, but only the last frame of each reached me, and `cascade single_frame` is the only value that compiles. Any intermediate motion -- a ring sliding cell by cell, for instance -- is invisible to this manual and would be evidence for grid_pitch_six."
    [probe: pending]
```

## The playbook as it stands

```
# playbook.dsl -- six transitions in, three of them no-ops. Almost everything
# below is an ordering preference, not a claim about the world.

order   map_the_action_table_before_routing     [proof: lean]
order   test_movement_before_spending_key5      [proof: lean]
prefer  untried_action_from_the_current_cell    [ev: 2/5 actions changed anything]
prefer  step_toward_the_bracketed_cell          [ev: 1/1 goal candidates in frame]
heuristic maze_cells_between_ring_and_exit_cell [admissible: lean]
prune   both_hud_tokens_spent and not goal => dead [proof: lean]
```

## The compiler refused your last manual

This is not a style complaint. The manual did not compile, so it has no executable form and nothing downstream can run. Fix the named clause; do not work around it by deleting the content unless the content really is inexpressible, in which case say so with an `E-` entry in the log.

```json
{
 "parse": "ParseError: Line 50: No comparison op in invariant: \"the 24 colour-9 pixels always cover exactly one 5x5 maze cell minus its centre pixel, which stays colour 5\""
}
```


# What to reply

Reply with EXACTLY three blocks, in this order, and nothing else outside them.

=== THEORY ===
```
<the whole of theory.dsl, not a diff>
```

=== PLAYBOOK ===
```
<the whole of playbook.dsl, not a diff. If you have nothing defensible to say
yet, emit only comment lines -- an empty playbook is honest, an invented one is
not.>
```

=== LOG ===
```json
[
  {"id": "O-01", "subject": "obj0 (colour 6)", "verdict": "accept",
   "as": "Cart", "why": "one sentence of reasoning a reader could check
   against the candidate stream alone"},
  {"id": "R-01", "subject": "obj0_step_UP", "verdict": "probe-pending",
   "why": "..."}
]
```

`verdict` is one of: accept, reject, entailed, probe-pending.
Use `id` prefixes O- for objects, R- for rules, L- for laws, P- for probes,
E- for a thing the DSL cannot express (say what you wanted and what you wrote
instead).

```

## reply

```
=== THEORY ===
```
# theory.dsl -- Theoria manual, second draft. Six observed transitions.
#
# COMPILER FIX: the last draft died on `invariant ring_fills_one_cell "<prose>"`.
# The invariant body is parsed for a comparison operator, so a prose invariant
# cannot exist. Every prose claim that was an `invariant` is now a `theorem`,
# which is where prose belongs. Nothing was deleted; two claims changed section.
#
# What the frame is made of: a 64x64 grid whose 4023 constant cells are `board`.
# The 73 cells that ever varied are, exactly, and they add up:
#   HUD token A  rows 1-3 x cols 1-3 minus (2,2)          =  8
#   HUD token B  rows 1-3 x cols 5-7                      =  9
#   underline    row 5 cols 1-3 and row 5 cols 5-7        =  6
#   maze cell (0,0)  rows 8-12  x cols 14-18 minus (10,16) = 24
#   maze cell (1,0)  rows 14-18 x cols 14-18 minus (16,16) = 24
#   tally bar    (63,62) and (63,63)                       =  2
#   8 + 9 + 6 + 24 + 24 + 2 = 73, the whole dynamic set.
# Cross-check against the diffs: t2 touched 24+24+1 = 49, t4 touched 1,
# t5 touched 23+24+24 = 71, and the union is exactly those 73 cells.
# Everything else -- the colour-5 maze, the colour-8 route, the colour-9
# bracket at rows 48-56, the other 62 cells of row 63 -- is board.

semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Player { pos: Coord }  # arc-colour: 9
  object Done { pos: Coord, present: Bool }  # arc-colour: 2
  object Token { pos: Coord, color: Int }  # arc-colour: 1
  landmark cell_r0c0  # arc-cell: (8, 14)
  landmark cell_r1c0  # arc-cell: (14, 14)
  landmark cell_r0c4  # arc-cell: (8, 38)
  landmark cell_r5c0  # arc-cell: (38, 14)
  landmark exit_cell  # arc-cell: (50, 44)
  domain dir { up, down, left, right }
  Player [segment: ring24_colour9_in_one_maze_cell ev: t0-t5 compress: 144]
  Token [segment: solid3x3_colour1_hud_slot_b ev: t0-t5 compress: 45]
  Done [segment: ring8_colour2_hud_slot_a ev: t5 compress: 8]

events:
  event jumped(o, dest) | recolored(o, c) | appeared(o)

rules:
  rule step_down_from_home [ev: t2 cov: 1/1]
    when act=key(2) and colored(cell_r0c0, 9) then jumped(Player, cell_r1c0)
  rule key5_sends_ring_home [ev: t5 cov: 1/1]
    when act=key(5) and colored(cell_r1c0, 9) then jumped(Player, cell_r0c0)
  rule key5_spends_token_a [ev: t5 cov: 1/1]
    when act=key(5) then appeared(Done)
  rule key5_lights_token_b [ev: t5 cov: 1/1]
    when act=key(5) then recolored(Token, 9)

goal:
  goal Player.pos = exit_cell

laws:
  invariant one_ring count(Player) = 1 [status: observed]

  theorem ring_fills_one_cell "the 24 colour-9 pixels of the maze ring always cover exactly one 5x5 maze cell minus its centre pixel, and that centre pixel stays colour 5. This was an invariant in the last draft and would not parse, because an invariant body must contain a comparison operator and this claim is about a shape. It is 6/6 frames true and unproven."
    [probe: pending]

  theorem board_is_static "4023 of the 4096 cells never changed across six frames; the maze, the colour-8 route, the colour-9 bracket at rows 48-56 and 62 of the 64 cells of row 63 are all among them. Also demoted from invariant for the same parse reason."
    [probe: pending]

  theorem maze_grid_pitch_six "maze cell (r,c) spans rows 8+6r..12+6r and cols 14+6c..18+6c; the separator lines sit on rows 7+6r and cols 13+6c and are themselves colour 5, so adjacent floor cells are not divided by anything. Cell centres are (10+6r, 16+6c). The ring moved 6 pixels down at t2 and 6 pixels back up at t5. The only movement event I have is moved(o,dir), which steps ONE pixel, so I cannot write a general step rule at all; I wrote two jumped() rules naming the only two cells ever witnessed. This manual therefore predicts NOTHING about any maze cell other than (0,0) and (1,0)."
    [depends: step_down_from_home, key5_sends_ring_home  probe: pending]

  theorem walkable_is_colour_five "inside the maze rectangle a cell is floor when its pixels are colour 5 and void when they are colour 0. Witness: cell (1,1), rows 14-18 x cols 20-24, is all colour 0, and key(4) fired from cell (1,0) at t4 did not move the ring. This inverts the guard language: free(x) tests for the BACKGROUND colour, which here is 0, i.e. exactly the cells that are NOT enterable. Any future movement rule must be guarded with colored(x, 5), never with free(x). I am recording this before I need it, because writing free() would have silently meant the opposite of what I intend."
    [probe: pending]

  theorem directional_keys "I believe key(1)=up, key(2)=down, key(3)=left, key(4)=right. Evidence: key(2) moved the ring from cell (0,0) to (1,0) (t2); key(1) fired from the top cell row and key(3) from the leftmost cell column, both off-board, and both changed nothing (t1,t3); key(4) fired from (1,0) whose right neighbour cell (1,1) is colour 0 by walkable_is_colour_five, and the ring did not move (t4). A second reading fits every one of these frames equally well: key(2) and key(4) are bound and key(1) and key(3) are unbound, which is why this is a theorem. The two readings are separated by one experiment -- fire key(1) or key(3) from a cell that is not on the boundary."
    [depends: step_down_from_home  probe: pending]

  theorem tally_bar "row 63 is a 64-cell bar of colour 9 that fills with colour 1 from the right edge: (63,63) turned 1 at t2 and (63,62) turned 1 at t4. It did not advance at t1, t3 or t5. So it counts something that the two off-board attempts did not do, that the blocked-into-void attempt DID do, and that key(5) did not do. 'Move commands the engine actually processed' fits; so does 'key(2) and key(4) are the only bound movement keys'. There is no event in the language for growing an object one pixel, so I cannot draw this at all: the manual leaves (63,62) and (63,63) unexplained in every frame, and I expect the responsibility check to report exactly those two cells."
    [probe: pending]

  theorem cascade_length_is_a_signal "t2 returned 7 frames and t5 returned 9 frames for one command; t1, t3 and t4 returned 1 each. t4 returned one frame yet still changed a pixel. So a multi-frame command is an animation of real motion and a single-frame command is an instant verdict. Only the last frame of each cascade reaches me and `cascade single_frame` is the only value that compiles, so any intermediate cell-by-cell slide is invisible here -- and seeing one would be direct evidence for maze_grid_pitch_six."
    [probe: pending]

  theorem hud_is_two_tokens "the HUD holds two 3x3 tokens (rows 1-3 cols 1-3, and cols 5-7) and a 3-pixel underline at row 5 that sits under exactly one of them. Frames 0-4: token A is a colour-9 ring and is underlined, token B is a solid colour-1 block. Frame 5: token A is a colour-2 ring and unmarked, token B is a colour-9 ring and IS underlined, the underline having jumped from cols 1-3 to cols 5-7 -- and the maze ring is back at cell (0,0), while the tally bar did not reset. key(5) did all of that in one 9-frame command. This reads either as 'attempt spent, position reset' or as 'objective cleared, next objective'. They disagree about whether key(5) is to be hoarded or sought. Nothing observed separates them, though the tally bar NOT resetting is weak evidence against a full restart."
    [depends: key5_spends_token_a, key5_lights_token_b, key5_sends_ring_home  probe: pending]

  theorem colour_nine_collision "colour 9 paints at least five different things: the player ring, HUD token A (frames 0-4), HUD token B (frame 5), the 3-pixel selection underline, the bracket around maze cell (7,5), and the row-63 bar. One colour binds one object in this arm, so Player takes 9 and the HUD colour-9 pixels and the 6 underline pixels have no object and will be reported unexplained. Worse, the arm locates Player by searching colour 9, and it may find the bar or the bracket instead of the ring; if the redraw puts Player somewhere absurd, that is this collision and not a bad movement rule. I believe there are at least three distinct colour-9 entities and the arm cannot tell them apart, so I say so here rather than declaring a second object that would be indistinguishable from the first."
    [probe: pending]

  theorem colour_one_collision "colour 1 paints HUD token B (frames 0-4) and also the filled pixels of the row-63 tally bar (from t2 onward). Token is declared with colour 1, so from t2 the arm has two colour-1 regions to choose between and may locate Token at (63,62)-(63,63) instead of the HUD. Same defect as colour_nine_collision, same reason for not splitting the object."
    [probe: pending]

  theorem vacated_cell_repaints_to_five "when the ring left cell (0,0) at t2, those 24 pixels became colour 5, not the background colour 0; and cell (1,0) did the same at t5. My manual has no object that owns 'floor', and no event that repaints a cell an object has left, so on any frame where the ring is at one of the two witnessed cells I expect the OTHER cell's 24 pixels to be drawn wrong. That is 24 unexplained pixels per frame and it is the largest known defect in this manual. Declaring a colour-5 Floor object would seize the entire 1006-cell maze, which is worse."
    [probe: pending]

  theorem goal_is_the_bracketed_cell "maze cell (7,5), rows 50-54 x cols 44-48, is edged in colour 9 on row 49 cols 43-48, row 55 cols 43-48 and col 49 rows 50-54, and carries a lone colour-9 pixel at its centre (52,46). It is the only cell in the frame drawn that way and it is drawn in the ring's own colour. I take it for the target. No transition witnesses this -- it is read off the static board -- so the goal section is a hypothesis the searcher will act on and the next win or non-win settles it."
    [probe: pending]

  theorem colour_eight_is_a_drawn_route "colour 8 is not scattered decoration; it is one connected polyline along maze cell centres. A 3x3 blob at rows 9-11 cols 39-41 sits on the centre of cell (0,4); a vertical line at col 40 (the centre column of cell column 4) runs from row 12 down to row 40; a horizontal line at row 40 (the centre row of cell row 5) runs from col 40 left to col 14; and cell (5,0), rows 38-42 x cols 14-18, is filled solid. So the route is cell (0,4) -> (5,4) -> (5,0), with a small mark at one end and a filled cell at the other. Not one of those pixels changed in six frames. Whether it is a worked example to imitate, a path already consumed, a barrier, or another agent's track is untested, and no rule of mine mentions it. Note it does NOT touch the player's start cell (0,0) nor the bracketed cell (7,5), which is the main reason I did not make it the goal."
    [probe: pending]

  theorem coord_convention "every landmark above names the TOP-LEFT pixel of the intended 5x5 cell: cell_r0c0 = (8,14), cell_r1c0 = (14,14), cell_r0c4 = (8,38), cell_r5c0 = (38,14), exit_cell = (50,44). If the arm's Coord is instead a centroid, all five must shift by (+2,+2) to (10,16), (16,16), (10,40), (40,16), (52,46). The ring's centroid happens to be its own colour-5 hole, which is a coincidence worth remembering when reading a failed redraw. Until one redraw is compared I do not know which convention holds."
    [probe: pending]
```

=== PLAYBOOK ===
```
# playbook.dsl -- six transitions in, three of them no-ops. Everything below is
# an ordering preference or a pruning rule, not a claim about the world. The one
# substantive addition since the last draft is that colour 0 inside the maze is
# void and colour 5 is floor, so the searcher must not read free() as walkable.

order   settle_the_action_table_before_routing          [proof: lean]
order   probe_the_two_silent_actions_from_an_inner_cell [proof: lean]
order   test_movement_before_spending_key5              [proof: lean]
prefer  untried_action_from_the_current_cell            [ev: 2/5 actions changed anything]
prefer  colour5_neighbour_over_colour0_neighbour        [ev: 1/1 blocked attempts]
prefer  step_toward_the_bracketed_cell                  [ev: 1/1 goal candidates in frame]
heuristic maze_cells_between_ring_and_exit_cell         [admissible: lean]
prune   target_cell_is_background_colour => dead        [proof: lean]
prune   both_hud_tokens_spent and not goal => dead      [proof: lean]
```

=== LOG ===
```json
[
  {"id": "E-01", "subject": "invariant ring_fills_one_cell (compiler refusal, line 50)", "verdict": "accept",
   "why": "The refusal is correct and not a style complaint: an invariant body is parsed for a comparison operator, and 'the 24 colour-9 pixels cover one 5x5 cell minus its centre' is a shape claim with no comparison in it. I wanted to write a shape predicate and the DSL has no such form, so I moved the claim verbatim into `theorem ring_fills_one_cell [probe: pending]` and did the same pre-emptively for `board_is_static`, which had the identical defect one line later. Only `invariant one_ring count(Player) = 1` remains, and that one does have a comparison op. Nothing was deleted."},

  {"id": "O-01", "subject": "mdl_segmenter obj0 (colour 9, 8 cells, 3x3, present 6/6)", "verdict": "accept",
   "as": "the HUD token A ring, but NOT as a declared object",
   "why": "It is the 3x3 ring at rows 1-3 cols 1-3 that turns colour 2 at t5; obj5 (colour 2, 8 cells, first_frame 5) is the same 8 pixels afterwards, so I declared Done on colour 2 and left the colour-9 phase owned by nothing, because colour 9 is already bound to Player."},

  {"id": "O-02", "subject": "mdl_segmenter obj1 (colour 1, 9 cells, 3x3, present 5/6)", "verdict": "accept",
   "as": "Token",
   "why": "Nine cells at rows 1-3 cols 5-7, present in exactly the five frames t0-t4 and gone at t5, which is precisely the frame in which those cells read as a colour-9 ring; frames_present 5/6 in the candidate stream is the same fact seen from the segmenter's side."},

  {"id": "O-03", "subject": "mdl_segmenter obj5 (colour 2, 8 cells, first_frame 5)", "verdict": "accept",
   "as": "Done",
   "why": "It appears for the first time in the last frame and only there, which is what `appeared(Done)` fired by key(5) asserts; colour 2 occurs nowhere else in the frame so the arm can find it unambiguously."},

  {"id": "O-04", "subject": "mdl_segmenter obj2 (colour 9, 3 cells, 1x3)", "verdict": "reject",
   "as": "the HUD selection underline",
   "why": "It is a real entity -- three pixels that jump from row 5 cols 1-3 to row 5 cols 5-7 at t5 -- but it is colour 9, which Player already holds, and this arm locates objects by colour, so declaring it would give me two objects the arm cannot separate. Recorded as prose in theorem colour_nine_collision instead, with its six pixels admitted as unexplained."},

  {"id": "O-05", "subject": "mdl_segmenter obj4 (colour 9, 64 cells, 1x64, row 63)", "verdict": "reject",
   "as": "the tally bar",
   "why": "Same colour collision as O-04, and worse: I have no event that turns one more pixel of an object a new colour, so even a declared bar would be undrawable. Its two dynamic pixels are admitted unexplained in theorem tally_bar."},

  {"id": "O-06", "subject": "mdl_segmenter obj3 (color null, 1006 cells, 50x38)", "verdict": "reject",
   "as": "the maze plus the player ring, merged",
   "why": "connected_components(4) with split_by_color false glued the colour-9 ring to the colour-5 floor it sits in, which is why the segmenter never produced the mover as its own track. 1006 cells of which only 48 ever change is not an object; those 958 constant cells are board, and I took the ring out of it by hand as Player."},

  {"id": "O-07", "subject": "mdl_segmenter variants (gain_bits -5042 and -17520)", "verdict": "accept",
   "as": "evidence against its own segmentation",
   "why": "Both variants have negative gain -- the script costs more bits than the raw pixels -- so by constraint 3 the segmenter's object set does not earn its place, and I used its tracks as hints rather than adopting its decomposition. My three declared objects cover 41 of the 73 dynamic cells and I say in the manual which of the other 32 go unexplained and why."},

  {"id": "R-01", "subject": "cegis_miner, all six tracks", "verdict": "reject",
   "why": "Its verdict is that no track satisfies 'exactly one move event per transition', and the refusal texts say so directly: recolor at transition 1, vanish at transition 4, object absent at frame 0. That is a correct report about this world, not a failure to look hard enough -- key(5) recolors two HUD tokens and moves the ring in one command, so the world genuinely does not narrate as one mover. I mined nothing from it."},

  {"id": "R-02", "subject": "step_down_from_home, key5_sends_ring_home", "verdict": "accept",
   "why": "One witnessed transition each, cov 1/1, and both are jumped() to a named landmark because the ring travels 6 pixels and moved(o,dir) travels 1. They predict nothing outside the two cells they name, which theorem maze_grid_pitch_six states in the manual's own words."},

  {"id": "R-03", "subject": "a general one-cell step rule over dir", "verdict": "probe-pending",
   "why": "It needs `toward(x, ?d)` to mean 'one maze cell over', pitch 6, and the cell language only steps one pixel. Until the DSL or my landmark set covers more cells there is no way to write it, so the manual carries the pitch as a theorem and the playbook carries the routing preference instead of a rule."},

  {"id": "L-01", "subject": "zero_space evidence_adequacy (rank 3 of 365 features, 5 transitions)", "verdict": "accept",
   "as": "a limit on every law in this manual",
   "why": "Its own verdict says the null space has dimension 362 and nearly every vector in it is unfalsified rather than confirmed. I therefore imported none of its global_laws as invariants; the single invariant I kept, count(Player) = 1, is marked [status: observed] and not [status: proven]."},

  {"id": "L-02", "subject": "zero_space cells list (73 cells)", "verdict": "accept",
   "why": "Its 73 cells match my hand-count exactly -- HUD 23, maze cell (0,0) 24, maze cell (1,0) 24, plus (63,62) and (63,63) -- and the union of the t2, t4 and t5 diffs reproduces the same set. That is the one thing in the candidate stream I can check independently, and it checks out, so the board/dynamic split at the top of the manual is not a guess."},

  {"id": "L-03", "subject": "walkable_is_colour_five", "verdict": "accept",
   "as": "theorem, with a warning about free()",
   "why": "New this round and it changes how any future rule must be written: the background is colour 0, cell (1,1) at rows 14-18 cols 20-24 is colour 0, and key(4) from cell (1,0) did not move the ring. So free(x), which tests for background, is true of exactly the cells that cannot be entered. Guarding a movement rule with free() would have meant the opposite of what I intend, and the playbook line prefers colour-5 neighbours accordingly."},

  {"id": "L-04", "subject": "colour_eight_is_a_drawn_route", "verdict": "accept",
   "as": "theorem, replacing eight_marks_unknown",
   "why": "Re-reading the frame column by column shows the colour-8 pixels are one polyline on cell centres -- a 3x3 mark on the centre of cell (0,4), a vertical run at col 40 down to row 40, a horizontal run at row 40 back to col 14, and cell (5,0) filled solid. That is a much sharper statement than 'unknown marks', and I still refuse to say what it is FOR, since none of its pixels moved in six frames."},

  {"id": "L-05", "subject": "vacated_cell_repaints_to_five", "verdict": "accept",
   "as": "a declared defect, not a fix",
   "why": "The cell the ring leaves goes to colour 5, not to background, and I have no floor object and no repaint event. Constraint 3 says admit the conflict rather than tidy it: this costs me 24 wrongly drawn pixels on every frame, and declaring a colour-5 Floor would seize all 1006 maze cells, which is worse. Named so the redraw report is read as this and not as a broken movement rule."},

  {"id": "L-06", "subject": "tally_bar advancing at t4 but not at t1 or t3", "verdict": "probe-pending",
   "why": "Two readings survive: the bar counts move commands the engine processed, with off-board attempts rejected before counting and the void-bump counted; or key(2) and key(4) are the only bound keys and key(1) and key(3) do nothing at all. Both are consistent with all six frames, and the playbook's first ordering line exists to separate them."},

  {"id": "P-01", "subject": "fire key(1) or key(3) from an interior cell", "verdict": "probe-pending",
   "why": "This is the single cheapest experiment in the world right now. If the ring moves, directional_keys is confirmed and the tally bar counts processed moves; if nothing happens and the bar does not advance, those two keys are unbound and half my action table is wrong. Cell (1,0) is not interior in the left direction, so the probe wants a cell with floor on its up or left side."},

  {"id": "P-02", "subject": "compare one redraw against one observed frame", "verdict": "probe-pending",
   "why": "Settles coord_convention (top-left versus centroid, a uniform (+2,+2) shift on all five landmarks) and simultaneously shows whether colour_nine_collision has put Player on the row-63 bar or the bracket rather than the ring. Both are cheap to read off the per-cell comparison the arm already performs."},

  {"id": "P-03", "subject": "spend key(5) a second time", "verdict": "probe-pending",
   "why": "hud_is_two_tokens has two readings that disagree about whether key(5) should be hoarded or sought. A second key(5) resolves it -- if token B also turns colour 2 and there is no third slot, they are attempts and the prune line 'both_hud_tokens_spent and not goal => dead' is real. I deliberately did not order this before movement testing, since under the costly reading it is irreversible."}
]
```
```
