# call-003-theorize-round2

model: `claude-opus-5` · 727728 ms · $1.919613 · usage {"cache_creation": {"ephemeral_1h_input_tokens": 37513, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 37513, "cache_read_input_tokens": 0, "inference_geo": "not_available", "input_tokens": 2, "iterations": [{"cache_creation": {"ephemeral_1h_input_tokens": 37513, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 37513, "cache_read_input_tokens": 0, "input_tokens": 2, "output_tokens": 60674, "type": "message"}], "output_tokens": 60674, "server_tool_use": {"web_fetch_requests": 0, "web_search_requests": 0}, "service_tier": "standard", "speed": "standard"}

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
  one of its pixels as unexplained.

### OBJECTS WITH EXTENT — read this before declaring anything
An instance is drawn as EXACTLY ONE CELL. A 3x3 token or a 24-pixel ring is
therefore not one instance, however you declare it, and if you declare it as
one then every other cell of it is an unexplained pixel forever.

Add `arc-instances: all` and the arm creates ONE INSTANCE PER CELL, all of the
same declared type, covering every cell of that colour the board cannot explain:

    object Ring  { pos: Coord, color: Int }   # arc-colour: 9  arc-instances: all
    object Token { pos: Coord, color: Int }   # arc-colour: 1  arc-instances: all
    object Pip   { pos: Coord, color: Int }   # arc-colour: 3

`Pip` has no `arc-instances`, so it is a single cell — correct for a genuine
one-pixel marker, wrong for anything else.

Consequences you must design for:

* **There is no instance called `Ring`.** There are `Ring_r8c14`,
  `Ring_r8c15`, … A rule that names `Ring` will not compile. Write rules over
  the TYPE instead:

        rule shift forall ?p in Ring [ev: t2 cov: 1/1]
          when act=key(2) and free(below(?p)) then moved(?p, down)

  `forall ?p in <ObjectType>` grounds the rule once per instance.
* **Every cell that ever changed needs an owner**, or it is unexplained. Count
  them: the evidence brief gives you `dynamic_cells`. If your declarations
  cannot cover them all, say which are left over and why, in a `theorem`.
* Two objects of the SAME colour still cannot be told apart by this arm — it
  looks objects up by colour and nothing else. Declare one type covering both
  and carry the belief that they are distinct as a `theorem`.

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

  THE TWO ARE NOT INTERCHANGEABLE AND THIS IS THE EASIEST MISTAKE TO MAKE:

    `invariant <name> <expr> <op> <value> [status: ...]`
        The body MUST contain one of  =  !=  <  >  <=  >=  . It is an
        equation, not a sentence. `invariant foo "in words ..."` is a parse
        error: "No comparison op in invariant".

    `theorem <name> "<prose>" [depends: ... probe: pending|passed]`
        The body MUST be a quoted sentence. This is where a belief you cannot
        write as an equation goes -- and most of what you want to say after
        six transitions belongs here, not in `invariant`.

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
 "cells_needing_an_owner": 72,
 "colours_seen": [
  0,
  1,
  2,
  5,
  8,
  9
 ],
 "constant_cells": 4021,
 "distinct_states": 7,
 "dynamic_box": [
  0,
  0,
  63,
  63
 ],
 "dynamic_cells": 75,
 "max_frames_in_one_command": 9,
 "shape": [
  64,
  64
 ],
 "states": 10,
 "steps": 10
}
```

## The current frame

Each cell is one hex digit 0-f standing for a colour. Row numbers on the left, column numbers on top.

```
0000000000000000000000000000000000000000000000000000000000000000
0999011100000000000000000000000000000000000000000000000000000000
0909011100000000000000000000000000000000000000000000000000000000
0999011100000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0999000000000000000000000000000000000000000000000000000000000000
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
9999999999999999999999999999999999999999999999999999999999991111
```

## Every command, and what changed

`t` indexes the state sequence. `frames` is how many grids one command returned -- more than one means the world took several internal steps for a single action.

- t0   RESET     frames=1   state=NOT_FINISHED (first frame)
- t1   ACTION1   frames=1   state=NOT_FINISHED no cells changed
- t2   ACTION2   frames=7   state=NOT_FINISHED 49 cells changed, rows 8-63, cols 14-63, [5, 9] -> [1, 5, 9]
- t3   ACTION3   frames=1   state=NOT_FINISHED no cells changed
- t4   ACTION4   frames=1   state=NOT_FINISHED (63,62) 9->1
- t5   ACTION5   frames=9   state=NOT_FINISHED 71 cells changed, rows 1-18, cols 1-18, [0, 1, 5, 9] -> [0, 2, 5, 9]
- t6   ACTION2   frames=9   state=NOT_FINISHED 49 cells changed, rows 8-63, cols 14-61, [5, 9] -> [1, 5, 9]
- t7   ACTION5   frames=9   state=NOT_FINISHED 71 cells changed, rows 1-18, cols 1-18, [0, 2, 5, 9] -> [0, 1, 5, 9]
- t8   ACTION1   frames=1   state=NOT_FINISHED (63,60) 9->1
- t9   ACTION3   frames=1   state=NOT_FINISHED no cells changed

## What the engines proposed

These are PROPOSALS. Nothing here is accepted until you accept it, and an engine cannot name anything -- `obj0` is the best it can do.

```json
{
 "cegis_miner": {
  "engine": "cegis_miner",
  "n_actions": 9,
  "n_states": 10,
  "refusals": [
   "ValueError: transition 4 narrates ['vanish']; only move/none are mined on this fixture",
   "ValueError: transition 1 narrates ['recolor']; only move/none are mined on this fixture",
   "ValueError: transition 1 narrates ['recolor']; only move/none are mined on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture"
  ],
  "tracks": [
   {
    "error": "NoSeparatingGuard: no literal separates transition 1 from the positives",
    "mine_ms": 0,
    "ms": 0,
    "traceback": "Traceback (most recent call last):\n  File \"C:\\Users\\user\\Desktop\\theoria\\theoria-arm\\world\\adapt.py\", line 48, in _timed\n    value = fn(*args, **kwargs)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\__init__.py\", line 92, in run\n    result = mine(transitions)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 320, in mine\n    guard, trace, added = synthesize(positives, universe, masks)\n                          ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 157, in synthesize\n    raise NoSeparatingGuard(\n        \"no literal separates transition %d from the positives\" % cex\n    )\nengines.cegis_miner.miner.NoSeparatingGuard: no literal separates transition 1 from the positives\n",
    "track_id": "obj0",
    "transitions": 9
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
    "traceback": "Traceback (most recent call last):\n  File \"C:\\Users\\user\\Desktop\\theoria\\theoria-arm\\world\\adapt.py\", line 48, in _timed\n    value = fn(*args, **kwargs)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\__init__.py\", line 92, in run\n    result = mine(transitions)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 320, in mine\n    guard, trace, added = synthesize(positives, universe, masks)\n                          ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 157, in synthesize\n    raise NoSeparatingGuard(\n        \"no literal separates transition %d from the positives\" % cex\n    )\nengines.cegis_miner.miner.NoSeparatingGuard: no literal separates transition 1 from the positives\n",
    "track_id": "obj2",
    "transitions": 9
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
   },
   {
    "ms": 0,
    "refused": "ValueError: object absent at frame 0; unsupported on this fixture",
    "track_id": "obj6"
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
  "candidates": 7,
  "chosen_operator": "connected_components(4)",
  "chosen_split_by_color": false,
  "engine": "mdl_segmenter",
  "event_types": {
   "appear": 2,
   "move": 4,
   "recolor": 8,
   "vanish": 2
  },
  "n_frames": 10,
  "tracks": [
   {
    "color": 9,
    "first_frame": 0,
    "frames_present": 10,
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
    "frames_present": 10,
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
    "frames_present": 10,
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
    "frames_present": 10,
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
    "frames_present": 2,
    "n_cells": 8,
    "shape": [
     3,
     3
    ],
    "track_id": "obj5"
   },
   {
    "color": 1,
    "first_frame": 7,
    "frames_present": 3,
    "n_cells": 9,
    "shape": [
     3,
     3
    ],
    "track_id": "obj6"
   }
  ],
  "variants": [
   {
    "baseline_bits": 3944,
    "compression_ratio": 1.918611,
    "events": 16,
    "gain_bits": -3623,
    "ms": 19,
    "script_bits": 7567,
    "split_by_color": false,
    "tracks": 7
   },
   {
    "baseline_bits": 3944,
    "compression_ratio": 7.956643,
    "events": 39,
    "gain_bits": -27437,
    "ms": 34,
    "script_bits": 31381,
    "split_by_color": true,
    "tracks": 24
   }
  ],
  "window": {
   "box": null,
   "covered": 1.0,
   "dynamic_cells": 75,
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
  "cells_needing_an_owner": 72,
  "colours_seen": [
   0,
   1,
   2,
   5,
   8,
   9
  ],
  "constant_cells": 4021,
  "distinct_states": 7,
  "dynamic_box": [
   0,
   0,
   63,
   63
  ],
  "dynamic_cells": 75,
  "max_frames_in_one_command": 9,
  "shape": [
   64,
   64
  ],
  "states": 10,
  "steps": 10
 },
 "window": {
  "box": null,
  "covered": 1.0,
  "dynamic_cells": 75,
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
  "cells_dynamic": 75,
  "cells_used": 75,
  "colours": [
   "c0",
   "c1",
   "c2",
   "c5",
   "c9"
  ],
  "difference_rank": 5,
  "engine": "zero_space",
  "evidence_adequacy": {
   "constrained_fraction": 0.013333,
   "difference_rank": 5,
   "features": 375,
   "space_dimension": 370,
   "transitions": 9,
   "verdict": "THIN: 9 transitions constrain rank 5 of 375 features, so the null space has dimension 370 and nearly every vector in it is a 'law' that is true over these states and unfalsified rather than confirmed. Treat every law below as a correlation awaiting a transition that could break it, not as a conservation law."
  },
  "features": 375,
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
      60
     ],
     [
      63,
      61
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
     
```

The full proposal stream is 749 rows in `candidates.jsonl`.

## The manual as it stands

```
# theory.dsl -- world observed for 6 states / 5 transitions
# (RESET, then ACTION1 ACTION2 ACTION3 ACTION4 ACTION5, one command each).
# 73 cells have ever changed; this manual names and owns all 73.
#
# ================= READ THIS BEFORE THE RULES =================
#
# 1. THE MANUAL I INHERITED DID NOT COMPILE, SO NOTHING WAS CHECKED.
#    certify reports no replay, no responsibility, no ambiguity verdict:
#    theory.dsl was non-empty and generated/theory.py could not be loaded.
#    The grammar names exactly one HARD compile error and the file had it:
#        landmark spawn_probe  # arc-cell: carried, coordinates stripped
#    "carried, coordinates stripped" is not (row, col). A landmark the
#    level cannot place kills the file. It now reads # arc-cell: (8, 14).
#    I also removed the bare `goal:` header with no indented body as the
#    second suspect -- a section with an empty body is not a documented
#    legal form, "no goal section at all" is. Everything below is downstream
#    of that repair, and the repair is the round's whole deliverable: a
#    manual that cannot be run is a manual with no evidence at all.
#
# 2. THE STORE HOLDS SIX STATES. THE MANUAL I INHERITED CLAIMED THIRTY-FOUR.
#    That is not a difference of opinion, it is a contradiction with the
#    frame in front of me. The old manual asserted SIXTEEN burned meter
#    cells, 87 dynamic cells, 51 Glyph9 instances, thirteen ACTION2 presses.
#    The current frame's row 63 reads 9 through col 61 and 1 at cols 62-63:
#    TWO burns. The store reads dynamic_cells 73, constant_cells 4023,
#    cells_needing_an_owner 70, states 6, steps 6. Every one of those
#    numbers matches the six-state history and refutes the thirty-four-state
#    history. Either the episode was restarted and the store rewound, or
#    that narrative was never in this store. I cannot tell which, and it
#    does not change what I am allowed to write: CONSTRAINT 2 BINDS ME TO
#    THE TRANSITIONS THIS STORE ACTUALLY HOLDS. Every `ev:` tag below cites
#    only t1-t5. Every count below is recomputed from this frame.
#    The inherited beliefs I cannot witness are not deleted -- they are
#    demoted to `theorem ... [probe: pending]`, which is what that keyword
#    is for, and each names the pixels it will cost if it is right and I
#    left it out.
#
# 3. WHAT SIX TRANSITIONS ACTUALLY BOUGHT, AND IT IS NOT NOTHING.
#    t1 A1 at spawn: 0 cells. t2 A2: 48 body cells six rows south + 1 burn.
#    t3 A3 one south: 0 cells. t4 A4 one south: 1 cell, a burn, body still.
#    t5 A5 one south: 48 body cells back north + 23 panel cells.
#    Every one of the 73 dynamic cells is touched by that history except the
#    burn edge, and the manual below replays all five transitions to the
#    pixel except nothing -- I expect 5/5, and if it is not 5/5 the defect
#    is mine and legible.

semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Glyph9  { pos: Coord, color: Int }   # arc-colour: 9  arc-instances: all
  object Vacated { pos: Coord, color: Int }   # arc-colour: 5  arc-instances: all
  object Spent   { pos: Coord, color: Int }   # arc-colour: 1  arc-instances: all
  object Dark    { pos: Coord, color: Int }   # arc-colour: 0  arc-instances: all
  landmark spawn_probe  # arc-cell: (8, 14)
  domain dir { up, down, left, right }
  Glyph9  [segment: dynamic_colour_9 ev: t0-t5 compress: 37]
  Vacated [segment: dynamic_colour_5 ev: t2,t5 compress: 24]
  Spent   [segment: dynamic_colour_1 ev: t5 compress: 9]
  Dark    [segment: dynamic_colour_0 ev: t5 compress: 3]

rules:
  rule key2_body_leaves forall ?p in Glyph9 [ev: t2 cov: 24/24]
    when act=key(2) and colored(?p, 9) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule key2_body_arrives forall ?v in Vacated [ev: t2 cov: 24/24]
    when act=key(2) and colored(?v, 5) and colored(above(above(above(above(above(above(?v)))))), 9) then recolored(?v, 9)

  rule meter_burn_key2_rightmost forall ?p in Glyph9 [ev: t2 cov: 1/1]
    when act=key(2) and colored(?p, 9) and rightof(?p) = wall then recolored(?p, 1)

  rule meter_burn_key4_next forall ?p in Glyph9 [ev: t4 cov: 1/1]
    when act=key(4) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule key1_inert_at_spawn forall ?p in Glyph9 [ev: t1 cov: 1/1]
    when act=key(1) and colored(spawn_probe, 9) and colored(?p, 9) and colored(above(?p), 5) and colored(leftof(?p), 5) and colored(rightof(?p), 9) then recolored(?p, 9)

  rule key3_inert_below_spawn forall ?v in Vacated [ev: t3 cov: 1/1]
    when act=key(3) and colored(spawn_probe, 5) and colored(?v, 9) and colored(above(?v), 5) and colored(leftof(?v), 5) and colored(rightof(?v), 9) then recolored(?v, 9)

  rule key5_body_clears forall ?v in Vacated [ev: t5 cov: 24/24]
    when act=key(5) and colored(?v, 9) then recolored(?v, 5)

  rule key5_body_respawns forall ?p in Glyph9 [ev: t5 cov: 24/24]
    when act=key(5) and colored(?p, 5) and colored(above(?p), 5) then recolored(?p, 9)

  rule key5_slot1_dims forall ?p in Glyph9 [ev: t5 cov: 8/8]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 9) and above(above(above(above(?p)))) = wall then recolored(?p, 2)

  rule key5_underline1_dims forall ?p in Glyph9 [ev: t5 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 9) and colored(above(above(above(above(?p)))), 9) and above(above(above(above(above(above(?p)))))) = wall then recolored(?p, 0)

  rule key5_slot2_row1_lights forall ?s in Spent [ev: t5 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(?s)) = wall then recolored(?s, 9)

  rule key5_slot2_row3_lights forall ?s in Spent [ev: t5 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and colored(above(above(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_row2_left_lights forall ?s in Spent [ev: t5 cov: 1/1]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(?s)))))) = wall then recolored(?s, 9)

  rule key5_slot2_row2_right_lights forall ?s in Spent [ev: t5 cov: 1/1]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and colored(leftof(leftof(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_centre_darkens forall ?s in Spent [ev: t5 cov: 1/1]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(leftof(?s))))))) = wall and colored(leftof(?s), 1) then recolored(?s, 0)

  rule key5_underline2_lights forall ?d in Dark [ev: t5 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?d, 0) and colored(above(above(?d)), 1) and colored(above(above(above(above(?d)))), 1) then recolored(?d, 9)

laws:
  invariant glyph9_instances count(Glyph9) = 37 [status: counted]
  invariant vacated_instances count(Vacated) = 24 [status: counted]
  invariant spent_instances count(Spent) = 9 [status: counted]
  invariant dark_instances count(Dark) = 3 [status: counted]
  invariant board_cells count(board) = 4023 [status: counted]
  invariant meter_cells_burned count(Glyph9, color = 1) = 2 [status: counted]

  theorem the_compile_error_was_one_comment_and_it_cost_the_whole_round "The single most useful sentence I can leave behind. The inherited manual declared `landmark spawn_probe  # arc-cell: carried, coordinates stripped`. The grammar says in as many words that every landmark line MUST carry a trailing `# arc-cell: (row, col)` and that a landmark the level cannot place is a HARD compile error. So theory.py was never generated, and every downstream verdict came back empty: replay {}, responsibility {}, unambiguous null, first_divergence null. NOTHING IN THAT MANUAL WAS EVER CHECKED, including the thirteen panel rules its prose spends four paragraphs defending. Note the failure mode: a manual that does not compile produces no divergence and therefore looks exactly like a manual with no defects. The lesson generalises past this bug -- an empty certify block is the loudest possible signal and must be read as `nothing is known` rather than `nothing is wrong`. The repair is (8, 14), the top-left pixel of the spawn ring, which renders 9 while the body is home and 5 the moment it is anywhere else. I also dropped the bare `goal:` header with no indented body, since `no goal section at all is legal` is documented and `a section with an empty body` is not."
    [depends: key5_slot1_dims  probe: pending]

  theorem the_store_holds_six_states_and_every_tag_in_this_file_cites_one_of_them "The inherited manual narrated thirty-three transitions and the store hands me five. This is not a disagreement I can split. Its claims are refuted by the frame on my desk: it says SIXTEEN meter cells burned and row 63 shows TWO, at cols 62 and 63; it says 87 dynamic cells and the store says 73; it says 51 Glyph9 instances and the census below counts 37; it says the body has been driven south thirteen times and the store records ONE ACTION2. Every number in the store -- constant_cells 4023, cells_needing_an_owner 70, distinct_states 4, states 6, cascade_lengths [1,7,9] -- fits the six-state history exactly. So either the episode restarted and the store rewound, or that narrative never described this store; I cannot distinguish those from here and I do not need to, because constraint 2 binds me to witnessed transitions either way. WHAT I DID WITH THE INHERITED BELIEFS: kept every one that this frame independently confirms (the map, the lattice, the socket, the aperture -- all readings of pixels I can re-read now), demoted every one whose only support was t6-t33 to `probe: pending`, and priced each demotion. WHAT I REFUSE TO DO: re-cite t30-t33. A tag that names a transition the store does not hold is worse than no tag, because it cannot be checked and it looks checked."
    [depends: dynamic_census  probe: passed]

  theorem dynamic_census "Exactly 73 cells have ever changed and every one has an owner. 23 are the panel: slot 1's eight ring pixels at rows 1-3 cols 1-3, its centre (2,2) being colour 0 in both configurations and therefore board; underline 1's three at row 5 cols 1-3; slot 2's nine at rows 1-3 cols 5-7, centre included because (2,6) is 1 before t5 and 0 after; underline 2's three at row 5 cols 5-7. 24 are the spawn ring, rows 8-12 cols 14-18 minus the aperture (10,16), which never changes and is board. 24 are the same ring six rows south, rows 14-18 cols 14-18 minus its aperture (16,16). 2 are the burned right end of row 63, cols 62 and 63. 23+24+24+2 = 73 = dynamic_cells. By frame-0 colour: 37 colour-9 (8 slot-1 ring + 3 underline-1 + 24 spawn ring + 2 meter), 9 colour-1 (slot 2, solid at frame 0), 24 colour-5 (the lower ring, floor at frame 0), 3 colour-0 (underline 2). 37+9+24 = 70 = cells_needing_an_owner EXACTLY, which is the store telling me it does not count background-coloured cells as needing an owner; the 3 colour-0 cells are the difference between 70 and 73 and Dark is declared to carry them anyway. 4096-73 = 4023 = constant_cells exactly."
    [probe: passed]

  theorem the_dark_type_is_the_one_declaration_i_am_not_sure_the_arm_honours "Dark is declared on colour 0, which is the background. The arm instances every cell of a declared colour THE BOARD CANNOT EXPLAIN, and (5,5),(5,6),(5,7) do vary, so they should be instanced; but the store's own arithmetic excludes them from cells_needing_an_owner, so the arm may treat background-coloured cells as board unconditionally. IF IT DOES, key5_underline2_lights never fires and t5 replays three pixels short, at row 5 cols 5-7, and the divergence set will say so precisely. There is no alternative declaration -- those three cells are colour 0 at frame 0 and colour 9 after t5, and typing is by frame-0 colour -- so the choice is Dark or three permanently unexplained pixels. I take Dark and name the exact three cells to look for in the first divergence report."
    [depends: key5_underline2_lights, dynamic_census  probe: pending]

  theorem the_action_map_after_five_transitions "WITNESSED HERE, not inherited. ACTION2 IS DOWN: t2, the 5x5 body block moved from rows 8-12 to rows 14-18, exactly six rows, one lattice cell, over floor that continues further south -- so one press is one lattice cell and not a slide. ACTION5 CARRIES THE BODY BACK NORTH: t5, rows 14-18 to rows 8-12. NEGATIVE INFORMATION, stated as negative. At spawn (1,2) north and west are void, south and east are open floor; ACTION1 did nothing at t1, so ACTION1 IS NEITHER DOWN NOR EAST. At lattice (2,2) north was open (the body had just vacated rows 8-12) and south was open (rows 20-24 are floor at cols 13-31) while east and west were void (cols 8-12 and 20-24 are 0 at those rows); ACTION3 and ACTION4 each did nothing there, so NEITHER IS UP AND NEITHER IS DOWN, and their inertness is fully explained if they are the horizontal pair. One assignment survives that invents nothing: ACTION1 up, ACTION2 down, ACTION3 and ACTION4 the two horizontals in some order, ACTION5 up-or-return. EAST IS ACTION3 OR ACTION4 AND NOTHING IN THIS STORE SAYS WHICH. The body stands at spawn where east is three lattice cells of unbroken floor: one press names the key whichever way it answers, because a step means that key is east and no step means the other one is."
    [depends: key2_body_arrives, key5_body_respawns, the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem key5_is_written_as_spawn_refills_and_that_is_a_return_reading_i_did_not_choose "Worth stating because it is a prediction I will be held to. key5_body_respawns is guarded on PIXELS -- a Glyph9 cell rendering 5 whose neighbour above renders 5 -- and not on where the body is. Its one witness had the body one cell south, where UP and RETURN are indistinguishable. But as written it fires from ANY state in which the spawn ring reads floor. So my manual predicts that after a first eastward step, ACTION5 redraws the body at spawn WITHOUT erasing it from its new cell, because the cells it would have to erase are at rows 8-12 cols 20-24, which have never changed, are board, and have no instance. TWO BODIES, 24 wrong pixels, and I am naming it now so it cannot be sold to me later as a surprise. The honest content is: this rule is a spawn-ring refill rule, its RETURN flavour is an artefact of guarding on pixels, and the first ACTION5 pressed from a third lattice cell separates UP from RETURN in one command -- UP predicts nothing at all from any cell whose north is void, RETURN predicts a 48-pixel jump."
    [depends: key5_body_respawns, the_action_map_after_five_transitions  probe: pending]

  theorem the_panel_toggles_with_the_body_away_and_the_return_half_is_unwitnessed_here "t5 turned 23 panel cells over, all at once, while the body returned home: slot 1's eight ring pixels 9 to 2, underline 1's three 9 to 0, slot 2's nine 1 to 9 except its centre (2,6) 1 to 0, underline 2's three 0 to 9. The current frame still shows that configuration -- call it B -- at rows 1-3 and row 5, cols 1-3 and 5-7, and I have re-read every pixel of it. ONE WITNESS, and the guard colored(spawn_probe, 5) means `the body is not at spawn`, which was true at the start of t5 and is the only discriminator I have; ACTION2 at t2 touched no panel pixel with the same guard true, which is one negative for `any key toggles it`. WHAT I DO NOT HAVE IN THIS STORE IS THE RETURN HALF. Nothing here witnesses B going back to A, so under constraint 2 the six rules that would do it are NOT in the manual, and I write them out here so that the transition which witnesses them costs one paste: key5_slot1_lights over Glyph9 on colour 2 to 9; key5_underline1_lights over Glyph9 on colour 0 with above-six equal wall to 9; key5_slot2_ring_resets over Spent on colour 9 to 1; key5_slot2_centre_resets over Spent on colour 0 to 1; key5_underline2_dims over Dark on colour 9 to 0; all five guarded by act=key(5) and colored(spawn_probe, 5). THE PRICE OF LEAVING THEM OUT IS EXACTLY 23 PIXELS on the first effective ACTION5 taken from configuration B, and it buys the certainty that no rule in this file rests on a transition the store does not hold."
    [depends: key5_slot1_dims, key5_slot2_centre_darkens  probe: pending]

  theorem the_meter_is_a_leftward_bar_and_two_readings_still_fit_it "Row 63 is a 64-cell colour-9 bar burning 9 to 1 one cell at a time from the right. Two cells are burned: (63,63) at command index 2 under ACTION2, (63,62) at index 4 under ACTION4. READING A: a burn happens when the key is 2 or 4. READING B: a burn happens when the command index is even. BOTH FIT ALL FIVE TRANSITIONS PERFECTLY, because indices 1, 3, 5 carried odd keys and indices 2, 4 carried even ones -- this store contains no separator and I will not pretend otherwise. My two burn rules encode reading A because reading B cannot be written in this grammar at all: the guard language reads pixels and the action name, there is no command counter, and no pixel of the frame records the parity. THE SEPARATOR IS ONE COMMAND AND IT IS FREE: press an ODD key at the next index, which is 6 and therefore even. If (63,61) burns, reading A is dead and my two burn rules are known mis-attributions kept only for replay. If nothing burns, reading A survives another round. Note that ACTION3 is an odd key and is also the east probe -- one press answers two questions, which is why the playbook ranks it first."
    [depends: meter_burn_key2_rightmost, meter_burn_key4_next  probe: pending]

  theorem i_cannot_draw_the_leading_edge_burn_whichever_reading_wins "A law of this manual rather than of this world. The arm instances exactly the cells that have ALREADY changed, so the next cell to burn, (63,61), is board right now, has no instance, and NO RULE OF MINE CAN RECOLOUR IT. My burn rules therefore have zero predictive value at the leading edge and full value on replay, which is a division of labour and not a contradiction: t2 and t4 replay to the pixel because (63,63) and (63,62) are dynamic NOW. The tempting repair -- a second declared type on colour 9 without arc-instances, hoping the arm seats an instance somewhere useful -- I reject: the arm looks objects up by colour and nothing else, so a second colour-9 type is indistinguishable from Glyph9, its seat is unspecified, and any cell it landed on would be claimed twice, which is exactly the constraint-5 error the grammar warns about. CONSEQUENCE FOR READING REFUTATIONS: a divergence set consisting only of the bar's leading edge does not implicate this manual. A divergence set containing anything else does."
    [depends: the_meter_is_a_leftward_bar_and_two_readings_still_fit_it  probe: passed]

  theorem the_world_may_not_be_a_function_of_the_drawn_frame_and_this_store_cannot_tell "distinct_states is 4 against 6 states, so there are exactly two pixel-coincidences: s1 = s0 (ACTION1 changed nothing) and s3 = s2 (ACTION3 changed nothing). To show the world is not a function of the frame I would need a pixel-identical pair from which THE SAME action produced different successors. My two pairs are sterile: from s0 the world was given ACTION1 and from s1 it was given ACTION2, and from s2 it was given ACTION3 and from s3 ACTION4. Different keys, so nothing is tested. If reading B of the meter is true then such a pair MUST exist -- press any key twice in a row from a state where it does nothing, and the even press burns while the odd press does not -- and constraint 5 obliges my manual to be a function of the frame, so it would be wrong about one member of every such pair by exactly one pixel. I record the prediction rather than the conclusion: THE CHEAPEST WAY TO PRODUCE THAT PAIR IS TWO CONSECUTIVE PRESSES OF A KEY THAT IS INERT WHERE THE BODY STANDS, and it is the same experiment as the meter separator."
    [depends: the_meter_is_a_leftward_bar_and_two_readings_still_fit_it  probe: pending]

  theorem silence_is_a_prediction_and_three_of_my_five_spawn_silences_are_forged "The compiled transition function is total: where no rule fires the successor equals the current state, so my manual never says `I do not know`, it says `nothing happens`, in the same voice it uses for things it has seen. Audit the five keys at spawn, where the body stands now. key(1) inert: WITNESSED, t1, zero cells. key(2) moves 48 body cells: witnessed once, t2. key(3), key(4), key(5) at spawn: NO WITNESS -- key(3) and key(4) were each pressed once ever, both from one cell south, and key(5) has never been pressed at spawn in this store at all. THREE OF FIVE SILENCES AT SPAWN ARE FORGED DEATH CERTIFICATES. Two of them are the east key by the elimination above, so at least one of those three silences is FALSE, and the manual is currently claiming with a straight face that four of the five keys do nothing here. That is the largest single block of unearned confidence in this file and it is also the cheapest to fix: one press."
    [depends: the_action_map_after_five_transitions, key1_inert_at_spawn  probe: pending]

  theorem the_two_no_op_rules_fail_the_gain_test_and_i_keep_them_for_a_narrow_reason "key1_inert_at_spawn and key3_inert_below_spawn each recolour one pixel to the colour it already has, each has one witness on a transition where zero cells changed, and replay is identical without them. They explain no pixel and they lengthen the manual, so they fail constraint 3 and I say so rather than dressing them up. The reason I keep them: they are the only occurrences of act=key(1) and act=key(3) in the file, and deleting them narrows the action set certify adjudicates from five keys to three. Since the next command I want is ACTION3, removing the only rule that mentions ACTION3 is a way to make my own probe unchooseable. They are declared failures of the gain test and the two cheapest deletions here the moment the east key is named."
    [depends: key1_inert_at_spawn, key3_inert_below_spawn  probe: passed]

  theorem i_deleted_the_key2_leading_edge_burn_rule_and_here_is_why "The inherited manual carried `meter_burn_key2_next`, firing on a Glyph9 whose right neighbour reads 1. In this store it has NO witness -- t2's burn was the rightmost cell, guarded by rightof equals wall, and t4's was under key(4). It also cannot pay its way going forward: the only cell it could ever recolour next is (63,61), which is board and has no instance, so the rule would fire on nothing. Zero witnesses, zero pixels explained, zero pixels predictable: it fails constraints 2 and 3 simultaneously and it is gone. meter_burn_key4_next survives only because t4 witnesses it exactly and it replays that transition to the pixel."
    [depends: meter_burn_key4_next, i_cannot_draw_the_leading_edge_burn_whichever_reading_wins  probe: passed]

  theorem the_rules_are_pairwise_exclusive_and_off_board_cell_terms_are_false "Constraint 5 checked by hand, since certify has never had an executable form to check it with. Under key(2): body_leaves needs below-six to render 5, which is off-board for any row past 57, so it cannot fire on either meter cell; the rightmost-burn rule needs rightof equal wall, true only at col 63, where no other Glyph9 instance sits. Under key(5): body_respawns needs colour 5 while both panel-dim rules need colour 9. slot1_dims needs above-four equal wall (rows 0-3); underline1_dims needs a COLOUR TEST on above-four, which is false for rows 0-3 precisely because a colour test on an off-board cell evaluates false rather than raising -- that is the load-bearing fact, and it is the same trick that separates slot 2 by row (row 1 is above-two equals wall, row 3 is a colour test on above-two, row 2 is above-three equals wall with a colour test on above-one) and by column (col 5 is leftof-six equals wall, col 6 is leftof-seven equals wall with a colour test on leftof-one, col 7 is a colour test on leftof-two). Pairwise exclusive in every combination I can construct on the observed states. Not one rule uses `not`, deliberately."
    [depends: key2_body_leaves, key5_slot2_centre_darkens  probe: pending]

  theorem the_maze_is_a_six_pixel_lattice "Lattice cell (R,C) is rows 6R+2..6R+6 by cols 6C+2..6C+6; rows and columns congruent to 1 mod 6 are separator strips. Colour 5 is floor, 0 is void, 8 is machinery, and the body is a rigid 5x5 colour-9 block with a one-pixel aperture at its centre. Re-read pixel by pixel from the CURRENT frame, which is the only authority I have: R=1 (rows 8-12) is floor from col 13 to col 43, so C=2,3,4,5 are open and C=6 holds the knob; R=2 is floor at cols 13-19 and 25-31, so C=2 and C=4 only; R=3 is floor cols 13-31, so C=2,3,4; R=4 and R=5 are floor only at cols 13-19, so C=2; R=6 is the comb, whose only floor pixels are (39,14) and (41,14), so nothing there is enterable; R=7 is C=2 plus a one-row fragment at row 48 cols 42-50 that cannot hold a body; R=8 (rows 50-54) is floor from col 13 to col 48, so C=2..7 are open. Separator rows 7,13,19,25,31,37,43,49 are floor across column 2 and separator col 37 is floor across R=1, so lattice column 2 is continuous from R=1 to R=8 apart from the comb, and lattice row 1 is continuous from C=2 to C=6. Spawn is (1,2); in six frames the body has occupied exactly TWO cells, (1,2) and (2,2), and it is at spawn now."
    [depends: key2_body_arrives, the_action_map_after_five_transitions  probe: pending]

  theorem the_hole_is_an_aperture_and_only_the_ring_needs_floor "A destination lattice cell needs its 24 RING pixels to render floor; the centre may render anything, because key2_body_arrives fires on a destination pixel only when the pixel six rows above renders 9, and at the destination centre that pixel is the source centre, which renders floor. Witnessed at t2: (16,16) stayed 5 while its 24 neighbours turned 9, and again at t5 in reverse with (10,16). This matters because it is the only reading under which the winning cell is enterable: lattice (8,7) is rows 50-54 cols 44-48, its 24 ring pixels all render floor in the current frame, and its centre (52,46) renders colour 9, a lone pip. The map places something at a hole-centre exactly twice -- that pip and the knob's centre at (10,40) -- which I read as the designer saying the body acts through its aperture, and record as a reading, not a law."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_socket_is_a_keyhole_and_names_the_winning_position "Verified cell by cell against the current frame. The colour-9 bracket sits entirely on SEPARATOR strips: row 49 cols 43-49, row 55 cols 43-49, col 49 rows 49-55. Rows 49 and 55 are separator rows, cols 43 and 49 separator columns -- so what is drawn is the north, south and east walls of lattice cell (8,7) painted colour 9, with the west side left as floor. Inside it, rows 50-54 cols 44-48 are floor except the lone colour-9 pixel at the exact centre (52,46). Overlay the body standing there -- 5x5, aperture at its centre -- and it is flush against three walls with the pip showing through the aperture. That is a plug and a socket drawn to the pixel, and it names the winning position without my guessing a goal predicate: the game is plausibly won when the 24 ring pixels of rows 50-54 cols 44-48 render 9. The bracket has never changed, so it is board and no object owns it; the first time the body enters, those 24 cells become dynamic and the manual can finally speak about them."
    [depends: the_hole_is_an_aperture_and_only_the_ring_needs_floor  probe: pending]

  theorem the_socket_is_unreachable_until_the_comb_opens "Flood from spawn and the body reaches eleven lattice cells: (1,2),(1,3),(1,4),(1,5),(2,2),(2,4),(3,2),(3,3),(3,4),(4,2),(5,2). The socket (8,7) is not among them and nothing in R=7 or R=8 is, because every route south crosses (6,2) and 23 of that cell's 25 pixels render colour 8. Nor is there a second route: C=3 exists only at R=3, C=4 dead-ends at R=3, C=5 and C=6 exist only at R=1, so lattice column 2 is the sole north-south corridor. The comb is not an obstacle to route around, it is the door. Its wiring is drawn in the open and every pixel re-read in the current frame: a 3x3 colour-8 knob at rows 9-11 cols 39-41, a stem at (12,40), colour 8 filling col 40 from row 12 to row 40, colour 8 filling row 40 from col 14 to col 40, and the comb teeth at rows 38-42 cols 14-18. ONE CONNECTED WIRE from knob to gate, which is why I read the knob as the switch. Not one colour-8 pixel has moved in six frames, which is why 8 is board and not an object; the first colour-8 pixel that changes turns this theorem into physics and hands me a rule."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_knob_is_the_only_interactive_thing_within_reach_and_i_do_not_know_how_it_is_pressed "Ten of the eleven reachable cells are bounded by floor and void alone. The eleventh, (1,5) at rows 8-12 cols 32-36, is separated from the knob's cell (1,6) at cols 38-42 only by separator col 37, which is floor. Lattice (1,6) contains ten colour-8 pixels, nine of them ring pixels of that cell, so even under the aperture rule the body cannot stand there while 8 is solid. Either 8 is walkable and key2_body_arrives is wrong at the knob; or the knob answers to proximity from (1,5); or it answers to a key never pressed. My rules make the first self-announcing: drive the body into a colour-8 cell and my manual predicts it stays put, and the world contradicts that in one command if 8 is walkable. C=2 to C=5 is three lattice cells of eastward travel and C=2 to C=6 is four, every step on floor that R=1 shows open. Six commands spent and none has taken step one."
    [depends: the_socket_is_unreachable_until_the_comb_opens  probe: pending]

  theorem two_actions_have_never_been_pressed_and_one_of_them_may_be_a_click "actions_used is ACTION1..ACTION5 plus RESET; the alphabet is ACTION1..ACTION7. Two commands are entirely unconstrained, and in this action family one is normally a click carrying coordinates. That matters here: the knob is a 3x3 target the body appears unable to stand on, and a click is the shape of interaction that presses it. I cannot write such a rule -- the guard language admits act=key(6) but has nowhere to put two coordinates, so a click rule would fire on every click anywhere and be silently wrong about which cell was clicked. If a click drives this world my manual can record its EFFECT, comb pixels going 8 to 5, and never its precondition."
    [probe: pending]

  theorem the_first_step_east_costs_forty_eight_pixels_and_that_is_not_a_defect "Priced in advance so it cannot be sold to me as a surprise. The arm instances exactly the cells that have already changed, so rows 8-12 cols 20-24 -- lattice (1,3), the first cell east of spawn -- are board and have NO instance. When the body first steps there, 24 arrival pixels are undrawable no matter what rule I write, and the 24 departure pixels at rows 8-12 cols 14-18 are undrawable too until an east-leaves rule is witnessed, because no rule of mine turns spawn-ring Glyph9 cells from 9 to 5 on any key but 2. 48 wrong cells for the first step onto fresh ground, plus one for the burn if reading B is right, then 24 for the second step, then 0. The body also CHANGES TYPE as it walks -- Glyph9 at rows 8-12, Vacated at rows 14-18 -- because typing is by frame-0 colour and all that floor was 5. A manual that heals one step behind is the price of this arm, and the pixels it costs are the tuition, not the damage."
    [depends: the_maze_is_a_six_pixel_lattice, i_cannot_draw_the_leading_edge_burn_whichever_reading_wins  probe: pending]

  theorem the_goal_section_is_empty_on_purpose "`Cart.pos = exit_cell` needs one named instance and arc-instances: all gives me Glyph9_r8c14 and thirty-six siblings; there is no instance called Glyph9. The socket interior has never changed, so it is board and count() has nothing to range over there, and the pip (52,46) never becomes dynamic because the body's aperture leaves it rendering 9. The 24 ring cells of lattice (8,7) do become dynamic on first entry, but they are frame-0 colour 5 and would type as Vacated, indistinguishable by this arm from the 24 Vacated cells at rows 14-18 -- so count(Vacated, color = 9) = 24 would also be true of the body standing one cell south of spawn, which is not a win. count(Glyph9, color = 5) = 24 is true of every state where the body is anywhere but home. A goal true in the wrong states is worse than no goal, because it stops a planner at its first step. THE PRICE, PLAINLY: is_goal compiles to False, no plan terminates, and nothing ranks one command above another except whether the manual predicts pixels to move -- which at spawn today is exactly one key, ACTION2, the one key here whose rules are already at full coverage. The playbook exists to fight that gradient."
    [depends: the_socket_is_a_keyhole_and_names_the_winning_position  probe: passed]

  theorem the_cascade_length_is_a_free_channel_i_discard_by_construction "cascade_lengths are 1, 7 and 9. ACTION2 returned SEVEN frames at t2; ACTION5 returned NINE at t5; every command that changed nothing returned one. With one witness each I cannot tell whether the count belongs to the key or to the panel configuration -- both were in configuration A at the start. The net effect is what my semantics compares, so this costs nothing in replay and buys nothing in prediction, and I record it as a limitation of my own choice of `cascade single_frame`: up to eight intermediate frames per command are discarded unread. LIVE PREDICTION, free to check in the raw diff: the next ACTION2, taken from configuration B, is 7 frames if the count belongs to the key and 9 if it belongs to the panel."
    [depends: key2_body_arrives  probe: pending]

  theorem what_i_predict_before_i_see_it "Written in advance so it can cost me. The body is at spawn, the panel is in configuration B, two meter cells are burned, the next command index is 6 and it is EVEN. ACTION3 at spawn: my manual predicts ZERO cells and has NO WITNESS for that. If the body steps east, ACTION3 IS EAST and I pay 48 undrawable pixels I have already priced; if nothing moves, ACTION4 IS EAST by elimination since ACTION1 was inert here with east open. Either answer names the key. Independently, ACTION3 is an ODD key at an EVEN index, so (63,61) burning separates the two meter readings and (63,61) staying 9 separates them the other way -- one press, two questions, and both answers legible in the raw diff. ACTION4 at spawn: the same experiment with the labels swapped. ACTION5 at spawn: my manual predicts zero cells and has no witness; a step or a jump would refute the UP reading loudly, so it is the second-best press. ACTION1 at spawn: 1 cell, an identity recolour, the one silence I already have a witness for, nothing bought. ACTION2 at spawn: 48 body cells I draw correctly plus a burn I cannot draw -- one wrong pixel, nothing learned, since both its rules are already at full coverage, except the free cascade datum. IF THE PANEL MOVES ON ANY COMMAND TAKEN AT SPAWN, the guard colored(spawn_probe, 5) is wrong and thirteen rules need rewriting; that is the single observation that would most change this file."
    [depends: the_action_map_after_five_transitions, the_meter_is_a_leftward_bar_and_two_readings_still_fit_it  probe: pending]

  theorem what_the_engines_gave_me "mdl_segmenter reports NEGATIVE gain on both variants -- -5042 bits with connected_components(4) unsplit, -17520 split by colour -- which is the segmenter saying its own script costs more than writing the pixels. I take its TRACK LIST and not its verdict. obj0 (colour 9, eight cells, 3x3, all six frames) and obj2 (colour 9, 1x3, all six frames) are slot 1's ring and underline 1 persisting while it narrates 2 moves and 4 recolours: it does not see the panel as appearing and vanishing, which corroborates a marker with two seats. obj1 (colour 1, nine cells, 3x3, frames 0-4) is slot 2 solid, and obj5 (colour 2, eight cells, 3x3, FIRST FRAME 5) is slot 1 after the dim -- the appear event at frame 5 is exactly key5_slot1_dims and its frame index is independent corroboration, since the segmenter has never seen my rules. obj4 is the whole 64-cell row-63 bar, of which 2 cells are dynamic. obj3 is a 1006-cell colour-null blob that swallowed the maze floor AND the body: connected_components(4) cannot see the mover at all, because the mover is a ring adjacent to floor on every side, and THAT ABSENCE IS THE FINDING. None of these gets a type of its own; a second type on the same pixels invites the double claim rule 5 forbids. zero_space self-reports THIN in its own words -- 5 transitions constrain rank 3 of 365 features, null space dimension 362 -- and its one global law is my census cell for cell. cegis_miner refuses every track and its verdict, `the world does not narrate as one mover`, is true of the arm and false of the world: there is one mover, a rigid 24-pixel ring, and the arm can only see 24 simultaneous recolours."
    [probe: passed]
```

## The playbook as it stands

```
# playbook.dsl -- what to buy with the next command, not a route.
#
# ========= THE STATE OF PLAY =========
# The manual did not compile last round, so nothing has ever been checked:
# certify's replay, responsibility and ambiguity blocks are all empty. The
# landmark comment is repaired and the first thing this round must produce
# is an EXECUTABLE manual and a real divergence report. Until that exists,
# every ranking below is a ranking of expected information, not of proof.
#
# The store holds SIX states. The inherited manual claimed thirty-four and
# the current frame refutes it (two burned meter cells, not sixteen). All
# rules now cite t1-t5 only; the beliefs that cannot be witnessed here are
# demoted to pending theorems with their prices named.
#
# ========= THE BOARD AS THE MANUAL NOW SEES IT =========
#   Body at spawn, lattice (1,2). North and west void, south and east open.
#   At spawn:  key(2) -> 48 body cells, both its rules already full
#              key(1) -> nothing, WITNESSED at t1
#              key(3), key(4), key(5) -> nothing, NO WITNESS, and at least
#              one of those three silences is FALSE because east is 3 or 4.
#   Next command index is 6, EVEN: under the parity reading of the meter it
#   burns (63,61) whatever is pressed, and I cannot draw that cell.
#
# ========= THE ONE THING WORTH BUYING =========
# ONE ODD, UNTESTED KEY AT THIS CELL ANSWERS TWO QUESTIONS AT ONCE.
#   (a) DIRECTION. ACTION2 is down. ACTION1 was inert at spawn with east
#       open, so ACTION1 is not east. ACTION3 and ACTION4 were each inert
#       one cell south, where east and west are both void -- which is
#       exactly what the horizontal pair would do there. So east is ACTION3
#       or ACTION4, and pressing either names the key whichever way it
#       answers: a step means that key is east, no step means the other one
#       is east by elimination.
#   (b) THE METER. Reading A says burns follow keys 2 and 4; reading B says
#       burns follow even command indices. Both fit all five transitions
#       because every even index so far carried an even key. An ODD key at
#       the EVEN index 6 splits them in one press, and ACTION3 is odd.
#
# The advertised price of the step onto fresh ground: 48 pixels the manual
# cannot draw, because rows 8-12 cols 20-24 have never changed and are
# board, plus the departure ring which has no east-leaves rule yet. That is
# a refutation priced in advance and it must not be read as a defect.
# 24 pixels for the second step east, 0 for the third.
#
# ------------------------------------------------------------------------
# STATE 5: body home at lattice (1,2); panel in configuration B; TWO meter
# cells burned, cols 62-63 of row 63; next command index 6. Eleven lattice
# cells reachable; the body has stood in two of them. Three steps east
# along lattice row 1 reach the cell beside the knob; the knob is the far
# end of one connected colour-8 wire whose near end is the comb; the comb
# gates every route to the socket at (8,7).

order     make_the_manual_executable_before_trusting_any_other_verdict     [proof: lean]
order     read_an_empty_certify_block_as_nothing_known_not_nothing_wrong   [proof: lean]
order     settle_the_east_key_before_anything_else_at_this_cell            [proof: lean]
order     prefer_a_press_that_answers_two_open_questions_over_one          [proof: lean]
order     treat_predicted_inertness_as_ignorance_unless_a_witness_backs_it [proof: lean]
order     rank_by_witnesses_a_command_would_create_not_by_pixels_it_moves  [proof: lean]
order     stop_pressing_a_key_the_moment_its_question_has_been_answered    [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired  [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance               [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it               [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it       [proof: lean]

prune     ranked_only_because_the_manual_predicts_the_most_pixels => dead   [proof: lean]
prune     every_rule_it_would_witness_is_already_at_full_coverage => dead    [proof: lean]
prune     repeats_a_key_whose_inertness_here_is_already_witnessed => dead    [proof: lean]
prune     repeats_the_key_that_the_previous_command_just_answered => dead    [proof: lean]
prune     divergence_lies_only_on_the_meter_leading_edge => dead             [proof: lean]
prune     ranked_only_because_a_refutation_fired_on_it => dead               [proof: lean]
prune     revisits_a_lattice_cell_by_an_already_witnessed_key => dead        [proof: lean]
prune     action_excluded_for_this_direction_by_an_earlier_no_op => dead     [proof: lean]
prune     destination_ring_pixels_are_not_all_floor => dead                  [proof: lean]
prune     route_that_crosses_the_comb_while_it_still_reads_eight => dead     [proof: lean]
prune     meter_exhausted and not goal => dead                               [proof: lean]

heuristic keys_whose_inertness_here_rests_on_no_witness                     [admissible: lean]
heuristic direction_labels_a_command_would_fix_by_elimination               [admissible: lean]
heuristic live_readings_a_single_command_can_eliminate                      [admissible: lean]
heuristic open_questions_a_command_can_close                                [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_meter_edge                   [admissible: lean]
heuristic lattice_cells_the_body_has_never_occupied                         [admissible: lean]
heuristic lattice_distance_to_the_knob_while_the_gate_is_shut               [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open              [admissible: lean]
heuristic commands_remaining_before_the_bar_is_spent                        [admissible: lean]

prefer    a_key_whose_predicted_inertness_here_has_never_been_witnessed    [ev: 3/5 keys at spawn]
prefer    a_key_that_names_a_direction_whichever_way_it_answers            [ev: 2/2 candidates]
prefer    an_odd_key_at_an_even_index_while_the_meter_readings_are_tied    [ev: 0/5 commands so far]
prefer    a_key_never_pressed_from_the_cell_the_body_stands_on             [ev: 3/5 keys at spawn]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                 [ev: 5/5 diffs]
prefer    east_along_lattice_row_one_over_any_other_axis                   [ev: 1/1 levels]
prefer    a_press_at_a_third_cell_that_splits_up_from_return               [ev: 1/1 key5_presses]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered          [ev: 1/1 levels]
```

## Why you are being called: the surprises that fired

### heuristic_miss (computational family -> playbook.dsl)

the manual states no winning condition, so `is_goal` is `False` everywhere and no search can succeed. This is a gap in the manual, NOT a proof that the level is unsolvable -- constraint 6 forbids reading a failed search as an unsolvability claim. Until a `goal` is stated the plan tier cannot return `sat`, `commit` never runs, and every action this arm spends is a probe rather than an attempt to win. Declaring the winning condition is the highest-value edit available to the playbook.

```json
{
 "book_to_edit": "playbook.dsl",
 "consequence": "plan never returns sat; commit never runs; no level can be completed",
 "playbook_token": "b16e361ca6ced547",
 "status": "no_goal_declared"
}
```

### probe_refutation (empirical family -> theory.dsl)

THE FRONTIER DID NOT CONTAIN THE WORLD: all 18 hypotheses were refuted, including `inert` (nothing happens) and the manual itself, which predicted '25cac958273811a3' against the world's 'af3bb95d3135e37c'. No hypothesis survives, so this probe eliminated nothing and its realised information gain is 0.0 bits against the 0.650 bits the design expected. The manual needs a mechanism it does not currently state -- deleting one of its rules cannot reach this observation.

```json
{
 "action": 2,
 "expected_bits": 0.650022421648,
 "frontier_vacuous": true,
 "hypothesis_space": "every hypothesis is the manual or an ablation of it, plus `inert`",
 "information_gain_bits": 0.0,
 "manual_predicted": "25cac958273811a3",
 "n_hypotheses": 18,
 "n_survivors": 0,
 "observed": "af3bb95d3135e37c",
 "probe_id": "P-01",
 "vacuous_streak": 1
}
```

### probe_refutation (empirical family -> theory.dsl)

THE FRONTIER DID NOT CONTAIN THE WORLD: all 18 hypotheses were refuted, including `inert` (nothing happens) and the manual itself, which predicted '9bb17844cc3a57c9' against the world's '0e1cd0b30fbb12b3'. No hypothesis survives, so this probe eliminated nothing and its realised information gain is 0.0 bits against the 0.650 bits the design expected. The manual needs a mechanism it does not currently state -- deleting one of its rules cannot reach this observation.

```json
{
 "action": 5,
 "expected_bits": 0.650022421648,
 "frontier_vacuous": true,
 "hypothesis_space": "every hypothesis is the manual or an ablation of it, plus `inert`",
 "information_gain_bits": 0.0,
 "manual_predicted": "9bb17844cc3a57c9",
 "n_hypotheses": 18,
 "n_survivors": 0,
 "observed": "0e1cd0b30fbb12b3",
 "probe_id": "P-02",
 "vacuous_streak": 2
}
```


## What certify said about the manual you have now

```json
{
 "expensive": {
  "available": false,
  "detail": "not attempted: the enumerative development decides every state in the kernel and this level has about an unknown number of them (ceiling 200000). The pagoda development is the alternative and needs a LINE world plus an lp_potential certificate; this is a grid world with no state graph.",
  "ok": false,
  "state_estimate": null
 },
 "first_divergence": null,
 "proof_layer_available": false,
 "replay": {
  "detail": "5/5 transitions replay exactly",
  "matched": 5,
  "ok": true,
  "transitions": 5
 },
 "responsibility": {
  "cells_unexplained": 0,
  "detail": "every pixel of frame 0 belongs to the board or to an object",
  "ok": true,
  "total_cells": 4096
 },
 "unambiguous": {
  "actions": 5,
  "cap_reached": false,
  "clashes": [],
  "detail": "no (state, action) among 6 x 5 admitted two rules, and all 30 pairs were adjudicated -- no call to `step` raised",
  "n_clashes": 0,
  "ok": true,
  "pairs_checked": 30,
  "pairs_nominal": 30,
  "replay_truncated_by_crash": false,
  "sample_cap": 400,
  "scope": "sampled",
  "states": 6,
  "states_reconstructed": 6,
  "step_crashes": {
   "by_phase": {},
   "by_type": {},
   "count": 0,
   "note": "`step` is documented total and its only declared exception, AmbiguousTransition, is a constraint-9 violation which is counted as a clash rather than here. Anything counted here is a bug in the compiled manual, and each one removed a pair from adjudication while leaving it inside the nominal coverage.",
   "sample_cap": 8,
   "samples": [],
   "site": "certify._ambiguity: step(state, action)"
  }
 }
}
```

## The compiler refused your last manual

This is not a style complaint. The manual did not compile, so it has no executable form and nothing downstream can run. Fix the named clause; do not work around it by deleting the content unless the content really is inexpressible, in which case say so with an `E-` entry in the log.

```json
{
 "reply": "the reply carried no === THEORY === block; emit all three blocks"
}
```

## The manual has no goal section, and that has a price

This is not a complaint and not a request to invent one. It is a number you have not been shown.

The manual as it stands declares no `goal` clause. `is_goal` therefore compiles to `False` everywhere, so the planner cannot succeed on any input: every `plan` beat this leg has returned `no_goal_declared` without entering either rung of the ladder. So far that is 1 turn(s) and at least 5 action(s) spent with no target. The world has moved since the last time this was asked: 4 distinct states are now on record (the bar is 4 new ones).

Two answers are acceptable and one is not.

1. **A `goal` clause**, if the evidence now supports one. It must be false in the states you have already seen -- a goal satisfied by the current board stops the planner at the first node and is worse than no goal at all.
2. **A `theorem`** whose name says the goal is absent (it must contain both `goal` and one of absent, no_goal, unsigned, silence, not_signed, without_a_goal) and whose body gives the argument and the evidence that would settle it. Declining is a position; the record will carry it as one.

What is not acceptable is silence: a manual with neither a goal nor an argument about its absence leaves the arm exploring without knowing that it is exploring, which is the state this rider exists to end.


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
# theory.dsl -- world observed for 10 states / 9 transitions
# (RESET, then A1 A2 A3 A4 A5 A2 A5 A1 A3, one command each).
# 75 cells have ever changed; this manual names and owns all 75.
#
# ================= WHAT HAPPENED SINCE THE LAST MANUAL =================
#
# 0. MY LAST REPLY WAS NOT REFUSED BY THE GRAMMAR. The refusal reads
#    `the reply carried no === THEORY === block; emit all three blocks`.
#    That is a harness-level formatting failure on my side, not a parse
#    error: the manual that WAS compiled replayed 5/5 with 0 unexplained
#    cells and 0 clashes. Three blocks are emitted this time.
#
# 1. FOUR NEW TRANSITIONS ARRIVED AND TWO OF THEM REFUTED ME OUTRIGHT.
#    t6 A2: 49 cells, rows 8-63 cols 14-61 -- the 48 body cells I draw
#           correctly, plus a meter burn at (63,61) I could not draw.
#    t7 A5: 71 cells, rows 1-18 -- the 48 body cells I draw correctly,
#           plus THE PANEL TOGGLING BACK, 23 cells I had no rule for.
#    t8 A1: 1 cell, (63,60) 9->1. A METER BURN UNDER ACTION1.
#    t9 A3: 0 cells, at spawn.
#    Both probe_refutations are answered by construction, not by excuse:
#    the 23 return-half panel cells now have five rules (t7 witnesses
#    them), and the two new meter cells are now dynamic, so instances
#    exist and rules can finally draw them. I expect 9/9 replay.
#
# 2. ACTION1 BURNED A METER CELL AT t8 AND DID NOT AT t1. That single
#    fact kills reading A of the meter (burns follow keys 2 and 4) and
#    confirms reading B EXACTLY: burns happen on EVEN command indices,
#    4/4 of them, and never on odd, 5/5. See the_meter_is_a_two_command
#    _clock. The guard language cannot count commands, so my burn rules
#    are knowingly mis-attributed to keys; they replay all four burns and
#    predict nothing, and I say so rather than dressing them up.
#
# 3. ACTION3 IS INERT AT SPAWN (t9), WHERE EAST IS OPEN. With ACTION1
#    inert at spawn twice (t1, t8), ACTION2 down and ACTION5 up-or-home,
#    ACTION4 IS THE LAST CANDIDATE FOR EAST and is the only key never
#    pressed from the cell the body stands on. That is the whole of the
#    playbook's first line.

semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Glyph9  { pos: Coord, color: Int }   # arc-colour: 9  arc-instances: all
  object Vacated { pos: Coord, color: Int }   # arc-colour: 5  arc-instances: all
  object Spent   { pos: Coord, color: Int }   # arc-colour: 1  arc-instances: all
  object Dark    { pos: Coord, color: Int }   # arc-colour: 0  arc-instances: all
  landmark spawn_probe  # arc-cell: (8, 14)
  domain dir { up, down, left, right }
  Glyph9  [segment: dynamic_colour_9 ev: t0-t9 compress: 39]
  Vacated [segment: dynamic_colour_5 ev: t2,t5,t6,t7 compress: 24]
  Spent   [segment: dynamic_colour_1 ev: t5,t7 compress: 9]
  Dark    [segment: dynamic_colour_0 ev: t5,t7 compress: 3]

rules:
  rule key2_body_leaves forall ?p in Glyph9 [ev: t2,t6 cov: 48/48]
    when act=key(2) and colored(?p, 9) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule key2_body_arrives forall ?v in Vacated [ev: t2,t6 cov: 48/48]
    when act=key(2) and colored(?v, 5) and colored(above(above(above(above(above(above(?v)))))), 9) then recolored(?v, 9)

  rule meter_burn_edge_key2 forall ?p in Glyph9 [ev: t2 cov: 1/1]
    when act=key(2) and colored(?p, 9) and rightof(?p) = wall then recolored(?p, 1)

  rule meter_burn_next_key2 forall ?p in Glyph9 [ev: t6 cov: 1/1]
    when act=key(2) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule meter_burn_next_key4 forall ?p in Glyph9 [ev: t4 cov: 1/1]
    when act=key(4) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule meter_burn_next_key1 forall ?p in Glyph9 [ev: t8 cov: 1/1]
    when act=key(1) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule key3_inert_below_spawn forall ?v in Vacated [ev: t3,t9 cov: 1/1]
    when act=key(3) and colored(spawn_probe, 5) and colored(?v, 9) and colored(above(?v), 5) and colored(leftof(?v), 5) and colored(rightof(?v), 9) then recolored(?v, 9)

  rule key5_body_clears forall ?v in Vacated [ev: t5,t7 cov: 48/48]
    when act=key(5) and colored(?v, 9) then recolored(?v, 5)

  rule key5_body_respawns forall ?p in Glyph9 [ev: t5,t7 cov: 48/48]
    when act=key(5) and colored(?p, 5) and colored(above(?p), 5) then recolored(?p, 9)

  rule key5_slot1_dims forall ?p in Glyph9 [ev: t5 cov: 8/8]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 9) and above(above(above(above(?p)))) = wall then recolored(?p, 2)

  rule key5_underline1_dims forall ?p in Glyph9 [ev: t5 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 9) and colored(above(above(above(above(?p)))), 9) and above(above(above(above(above(above(?p)))))) = wall then recolored(?p, 0)

  rule key5_slot2_row1_lights forall ?s in Spent [ev: t5 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(?s)) = wall then recolored(?s, 9)

  rule key5_slot2_row3_lights forall ?s in Spent [ev: t5 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and colored(above(above(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_row2_left_lights forall ?s in Spent [ev: t5 cov: 1/1]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(?s)))))) = wall then recolored(?s, 9)

  rule key5_slot2_row2_right_lights forall ?s in Spent [ev: t5 cov: 1/1]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and colored(leftof(leftof(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_centre_darkens forall ?s in Spent [ev: t5 cov: 1/1]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(leftof(?s))))))) = wall and colored(leftof(?s), 1) then recolored(?s, 0)

  rule key5_underline2_lights forall ?d in Dark [ev: t5 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?d, 0) and colored(above(above(?d)), 1) and colored(above(above(above(above(?d)))), 1) then recolored(?d, 9)

  rule key5_slot1_lights forall ?p in Glyph9 [ev: t7 cov: 8/8]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 2) then recolored(?p, 9)

  rule key5_underline1_lights forall ?p in Glyph9 [ev: t7 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 0) then recolored(?p, 9)

  rule key5_slot2_ring_resets forall ?s in Spent [ev: t7 cov: 8/8]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 9) then recolored(?s, 1)

  rule key5_slot2_centre_resets forall ?s in Spent [ev: t7 cov: 1/1]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 0) then recolored(?s, 1)

  rule key5_underline2_dims forall ?d in Dark [ev: t7 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?d, 9) then recolored(?d, 0)

laws:
  invariant glyph9_instances count(Glyph9) = 39 [status: counted]
  invariant vacated_instances count(Vacated) = 24 [status: counted]
  invariant spent_instances count(Spent) = 9 [status: counted]
  invariant dark_instances count(Dark) = 3 [status: counted]
  invariant board_cells count(board) = 4021 [status: counted]

  theorem dynamic_census "Exactly 75 cells have ever changed and every one has an owner. 23 are the panel: slot 1's eight ring pixels at rows 1-3 cols 1-3, its centre (2,2) being colour 0 in both configurations and therefore board; underline 1's three at row 5 cols 1-3; slot 2's nine at rows 1-3 cols 5-7, centre included because (2,6) is 1 in configuration A and 0 in B; underline 2's three at row 5 cols 5-7. 24 are the spawn ring, rows 8-12 cols 14-18 minus the aperture (10,16), which never changes and is board. 24 are the same ring six rows south, rows 14-18 cols 14-18 minus its aperture (16,16). 4 are the burned right end of row 63, cols 60 to 63 -- two more than last round, at (63,61) under t6 and (63,60) under t8. 23+24+24+4 = 75 = dynamic_cells. By frame-0 colour: 39 colour-9 (8 slot-1 ring + 3 underline-1 + 24 spawn ring + 4 meter), 9 colour-1 (slot 2, solid at frame 0), 24 colour-5 (the lower ring, floor at frame 0), 3 colour-0 (underline 2). 39+9+24 = 72 = cells_needing_an_owner EXACTLY, which is the store telling me again that it does not count background-coloured cells as needing an owner; Dark carries the remaining 3 anyway and t5 and t7 both prove the arm does instance them, because key5_underline2_lights and key5_underline2_dims are the only rules that can touch row 5 cols 5-7 and last round's replay was exact. 4096-75 = 4021 = constant_cells exactly."
    [probe: passed]

  theorem the_dark_type_is_honoured_after_all "Last round I flagged Dark, declared on the background colour, as the one declaration I was not sure the arm would instance, and named the exact price: three pixels at row 5 cols 5-7 missing from t5. Replay came back 5/5 with zero unexplained cells, so the arm does instance background-coloured cells that vary. The doubt is discharged and I record the discharge rather than quietly deleting the doubt."
    [depends: key5_underline2_lights, dynamic_census  probe: passed]

  theorem the_goal_is_absent_because_no_instance_can_name_the_socket "I decline to declare a goal and here is the argument, with the price. The winning position I believe in is lattice cell (8,7), rows 50-54 cols 44-48, whose 24 ring pixels are floor and whose centre (52,46) is a colour-9 pip inside a three-sided colour-9 bracket -- a plug and a socket drawn to the pixel. Four forms of goal are available and every one of them is refuted. (1) Cart.pos = exit_cell needs ONE named instance; arc-instances: all gives me Glyph9_r8c14 and thirty-eight siblings and there is no instance called Glyph9, and a second colour-9 type would be indistinguishable to an arm that looks objects up by colour alone, which is the constraint-5 double claim. (2) count over the socket interior has nothing to range over: those cells have never changed, so they are board and carry no instances. (3) count(Vacated, color = 9) = 24 is TRUE of the body standing one cell south of spawn, a state I have already seen four times; when the body first enters any new floor cell those 24 cells also become Vacated and the count still reads 24, so no threshold on it ever names the socket. (4) count(Glyph9, color = 9) = 11 is false in all ten observed states and is therefore admissible by the letter of the rider -- and it is satisfied by pressing ACTION2 once from where the body stands right now, because it means nothing more than the body is off spawn in panel configuration A with all four instanced meter cells burned. A goal that a planner satisfies with its first move is worse than no goal, and the rider says so. THE PRICE I AM PAYING: is_goal compiles to False, plan returns no_goal_declared, commit never runs, and every command remains a probe -- one turn and nine actions so far. THE OBSERVATION THAT ENDS THIS: the first frame in which any pixel of the bracket rows 49-55 cols 43-49, or the pip (52,46), changes colour. Those cells become dynamic that instant, get instances, and a count over them becomes writable and false everywhere before it. Until then I am exploring, and the playbook now says out loud that I am exploring."
    [depends: the_socket_is_a_keyhole_and_names_the_winning_position  probe: pending]

  theorem the_meter_is_a_two_command_clock "SETTLED, and it was settled by ACTION1. Row 63 is a 64-cell colour-9 bar burning 9 to 1 one cell at a time from the right. Four cells are burned and the command indices are 2, 4, 6, 8 -- every even index, no odd index, 4 out of 4 and 5 out of 5. Reading A of last round (burns follow keys 2 and 4) predicted no burn at t8 under ACTION1 and no burn at t2 versus t1 distinction; t8 burned (63,60) under ACTION1 and t1 under the same key at the same cell burned nothing. READING A IS DEAD. The meter is a clock that ticks once every two commands, and it does not care which key. Consequences I accept: 60 cells remain, so about 120 commands remain before the bar is spent, which is a budget and not an emergency; and the next command, index 10, is EVEN and will burn (63,59)."
    [depends: meter_burn_next_key1  probe: passed]

  theorem the_burn_rules_are_deliberate_mis_attributions_kept_only_for_replay "Constraint 3 and constraint 6 both apply and I would rather be caught saying this than caught implying otherwise. My four burn rules are keyed on act=key(1), key(2) and key(4) because THE GUARD LANGUAGE HAS NO COMMAND COUNTER and no pixel of the frame records the parity, so the true law cannot be written here at all. They replay all four burns exactly -- t2 by rightof = wall, t4, t6 and t8 by a colour-1 right neighbour -- and that is the whole of their value. They are wrong about the mechanism, and they were saved from being caught by an accident I want on the record: the only odd-index press of a key they name was ACTION1 at index 1, when nothing was yet burned, so no cell had a colour-1 right neighbour and the rule correctly did not fire. THE TIME BOMB, NAMED IN ADVANCE: once (63,59) burns and becomes dynamic, an instance exists for it, and the first ODD-index press of key 1, 2 or 4 after that moment will make my manual predict a burn the world will not deliver -- exactly one wrong pixel, at the bar's leading edge, and it is my mis-attribution and not a new mechanism."
    [depends: the_meter_is_a_two_command_clock  probe: pending]

  theorem i_cannot_draw_the_leading_edge_burn "A law of this manual rather than of this world, and it has now been paid twice. The arm instances exactly the cells that have ALREADY changed, so the next cell to burn is board, has no instance, and NO RULE OF MINE CAN RECOLOUR IT. That is precisely why probe P-01 refuted the manual at t6: I drew the 48 body cells correctly and missed (63,61), which was board at the time. It is now dynamic, so t6 replays whole. The same will happen at index 10 with (63,59). CONSEQUENCE FOR READING REFUTATIONS: a divergence set consisting only of the bar's leading edge does not implicate this manual and must not be allowed to consume a round. A divergence set containing anything else does."
    [depends: the_meter_is_a_two_command_clock  probe: passed]

  theorem the_world_is_probably_not_a_function_of_the_drawn_frame "Now nearly forced rather than merely possible. The bar shows floor(index/2) burned cells, so a frame with b burns is consistent with index 2b and with index 2b+1, and those two differ in whether the NEXT command burns. Concretely: s0 and s1 are pixel-identical (ACTION1 at t1 changed nothing) and both show zero burns, yet the command taken from s1 burned and the command taken from s0 did not; s2 and s3 are pixel-identical and both show one burn, and the command from s3 burned while the command from s2 did not. WHAT STOPS THIS BEING A PROOF is that in each pair the two commands were different keys, so a frame-function that distinguishes keys is not yet contradicted. THE DIRECT WITNESS COSTS TWO COMMANDS: press the same inert key twice in a row from the current cell -- ACTION3 twice, say -- and the pixel-identical predecessor states will have received identical actions with different successors, one burning and one not. Constraint 5 obliges my manual to be a function of the frame, so it will be wrong about one member of that pair by exactly one pixel, and that pixel is the leading edge I cannot draw anyway. I record the prediction and rank the experiment low precisely because its cost and its lesson are already priced."
    [depends: the_meter_is_a_two_command_clock  probe: pending]

  theorem the_panel_is_a_two_slot_selector_toggled_by_action5 "BOTH DIRECTIONS ARE NOW WITNESSED and this is the round's largest repair. t5 turned 23 panel cells from configuration A to B while the body returned north; t7 turned the same 23 back from B to A, again while the body returned north. A: slot 1's ring reads 9 with underline 1 reading 9, slot 2 reads solid 1 with underline 2 reading 0. B: slot 1's ring reads 2 with underline 1 reading 0, slot 2 reads a ring of 9 with its centre hollowed to 0 and underline 2 reading 9. The current frame is A, re-read pixel by pixel. THE READING: two slots, an underline under each, and the underlined slot is also the one rendered in colour 9 -- a two-item selector whose cursor ACTION5 advances, wrapping after two. The unselected slot reverts to its own colour, 2 for slot 1 and 1 for slot 2, and slot 2's centre fills in when it is unselected, so the two glyphs are a hollow square and a solid square, the hollow one being the shape of the body itself. WHAT I DO NOT CLAIM: what the selection selects. ACTION2 moved the body down identically from configuration A at t2 and from configuration B at t6, so the selector does NOT remap ACTION2, which is the only cross-configuration comparison this store contains. Return-half rules were absent last round and I named their price as exactly 23 pixels on the first effective ACTION5 from configuration B; that bill arrived at t7 as probe P-02 and it is now paid with five rules, key5_slot1_lights, key5_underline1_lights, key5_slot2_ring_resets, key5_slot2_centre_resets and key5_underline2_dims, each guarded by colour alone because colours 2, 0 and 9 occur nowhere else in their types."
    [depends: key5_slot1_lights, key5_slot2_ring_resets, key5_underline2_dims  probe: passed]

  theorem the_spawn_probe_guard_is_the_untested_half_of_thirteen_rules "Every panel rule carries colored(spawn_probe, 5), which reads the body is not at home. Both witnesses had the body one cell south, so the guard has never been tested with the body home: ACTION5 has never been pressed at spawn in this store. If the panel toggles anyway, thirteen rules are guarded on the wrong thing and my manual under-predicts 23 pixels on that command; if nothing happens, the guard survives and the manual is right that ACTION5 at spawn is inert. Either way the answer arrives in one press and it is the second-ranked probe. Note the asymmetry that makes this cheap: my manual currently predicts ZERO cells for ACTION5 at spawn, so any change at all is legible."
    [depends: key5_slot1_dims, key5_slot1_lights  probe: pending]

  theorem the_action_map_after_nine_transitions "WITNESSED, with the negatives stated as negatives. ACTION2 IS DOWN: t2 and t6, the 5x5 body block from rows 8-12 to rows 14-18, exactly six rows, one lattice cell, twice. ACTION5 CARRIES THE BODY NORTH: t5 and t7, the reverse, twice, each time with the panel toggle. NEGATIVES. At spawn (1,2) north and west are void while south and east are open floor; ACTION1 did nothing there at t1 AND at t8, and ACTION3 did nothing there at t9 -- so NEITHER ACTION1 NOR ACTION3 IS EAST and neither is south. At (2,2) north and south are open while east and west are void; ACTION3 at t3 and ACTION4 at t4 each did nothing -- so neither is up and neither is down. Combine: ACTION3 is neither vertical nor east, which leaves west, and west is void at both cells it was pressed from, which explains all three of its silences without inventing anything. ACTION4 IS THE ONLY REMAINING CANDIDATE FOR EAST AND HAS NEVER BEEN PRESSED WHERE EAST IS OPEN. If ACTION4 also does nothing at spawn then NO KEY IS EAST, movement in this world is vertical only, and the map theorem below is wrong about what a lattice is -- that is a big finding cheaply bought, which is why the probe is ranked first whichever way it answers. The residue I cannot resolve: ACTION1 is consistent with up, and so is ACTION5, and two up keys is a smell. ACTION1 has only ever been pressed at spawn where up is void, so one press of ACTION1 from (2,2) separates them."
    [depends: key2_body_arrives, key5_body_respawns  probe: pending]

  theorem action5_is_up_or_home_or_undo_and_two_presses_separate_them "Both ACTION5 witnesses moved the body from (2,2) to (1,2), a move that up, return-home and undo-last-move all predict identically, so this store cannot separate them and I will not pretend it can. The separator is cheap and I write it as a shape, not as a route: reach any cell TWO lattice steps from spawn and press ACTION5 once. Up predicts one step back; home predicts a jump of two cells, 48 pixels I cannot draw; undo predicts one step back along the arrival direction, which differs from up as soon as the last step was horizontal. My rules encode neither reading -- key5_body_respawns is guarded on PIXELS, a Glyph9 cell rendering 5 whose neighbour above renders 5, so it is a spawn-ring refill rule and nothing more. As written it fires from ANY state where the spawn ring reads floor, so from a third cell my manual predicts the body is DRAWN AT SPAWN WITHOUT BEING ERASED where it stood: two bodies, 24 wrong pixels, priced here in advance so it cannot be sold to me later as a new mechanism."
    [depends: key5_body_respawns, the_action_map_after_nine_transitions  probe: pending]

  theorem the_maze_is_a_six_pixel_lattice "Lattice cell (R,C) is rows 6R+2..6R+6 by cols 6C+2..6C+6; rows and columns congruent to 1 mod 6 are separator strips. Colour 5 is floor, 0 is void, 8 is machinery, and the body is a rigid 5x5 colour-9 block with a one-pixel aperture at its centre. Re-read pixel by pixel from the CURRENT frame. R=1 (rows 8-12) is floor from col 13 to col 43, so C=2,3,4,5 are open and C=6 holds the knob; R=2 is floor at cols 13-19 and 25-31, so C=2 and C=4 only; R=3 is floor cols 13-31, so C=2,3,4; R=4 and R=5 are floor only at cols 13-19, so C=2; R=6 is the comb, whose only floor pixels are (39,14) and (41,14), so nothing there is enterable; R=7 is C=2 plus a one-row fragment at row 48 cols 42-50 that cannot hold a body; R=8 (rows 50-54) is floor from col 13 to col 48, so C=2..7 are open. Separator rows 7,13,19,25,31,37,43,49 are floor across column 2 and separator col 37 is floor across R=1, so lattice column 2 is continuous from R=1 to R=8 apart from the comb, and lattice row 1 is continuous from C=2 to C=6. Spawn is (1,2); in ten frames the body has occupied exactly TWO cells, (1,2) and (2,2), and it is at spawn now. THIS THEOREM IS HOSTAGE TO THE EAST PROBE: if ACTION4 does not move the body east from spawn, then no horizontal move exists, the lattice is a column and not a grid, and the reachability argument below collapses to a line."
    [depends: key2_body_arrives, the_action_map_after_nine_transitions  probe: pending]

  theorem the_hole_is_an_aperture_and_only_the_ring_needs_floor "A destination lattice cell needs its 24 RING pixels to render floor; the centre may render anything, because key2_body_arrives fires on a destination pixel only when the pixel six rows above renders 9, and at the destination centre that pixel is the source centre, which renders floor. Witnessed four times now: (16,16) stayed 5 at t2 and t6 while its 24 neighbours turned 9, and (10,16) did the same in reverse at t5 and t7. This matters because it is the only reading under which the winning cell is enterable: lattice (8,7) is rows 50-54 cols 44-48, its 24 ring pixels all render floor, and its centre (52,46) renders colour 9, a lone pip. The map places something at a hole-centre exactly twice -- that pip and the knob's centre at (10,40) -- which I read as the designer saying the body acts through its aperture, and record as a reading, not a law."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_socket_is_a_keyhole_and_names_the_winning_position "Verified cell by cell against the current frame. The colour-9 bracket sits entirely on SEPARATOR strips: row 49 cols 43-49, row 55 cols 43-49, col 49 rows 49-55. Rows 49 and 55 are separator rows, cols 43 and 49 separator columns -- so what is drawn is the north, south and east walls of lattice cell (8,7) painted colour 9, with the west side left as floor. Inside it, rows 50-54 cols 44-48 are floor except the lone colour-9 pixel at the exact centre (52,46). Overlay the body standing there -- 5x5, aperture at its centre -- and it is flush against three walls with the pip showing through the aperture. That is a plug and a socket drawn to the pixel. The bracket has never changed, so it is board and no object owns it; the first time any of it changes, those cells become dynamic and the goal section can finally be written."
    [depends: the_hole_is_an_aperture_and_only_the_ring_needs_floor  probe: pending]

  theorem the_socket_is_unreachable_until_the_comb_opens "Flood from spawn and the body reaches eleven lattice cells: (1,2),(1,3),(1,4),(1,5),(2,2),(2,4),(3,2),(3,3),(3,4),(4,2),(5,2). The socket (8,7) is not among them and nothing in R=7 or R=8 is, because every route south crosses (6,2) and 23 of that cell's 25 pixels render colour 8. Nor is there a second route: C=3 exists only at R=3, C=4 dead-ends at R=3, C=5 and C=6 exist only at R=1, so lattice column 2 is the sole north-south corridor. The comb is not an obstacle to route around, it is the door. Its wiring is drawn in the open and re-read in the current frame: a 3x3 colour-8 knob at rows 9-11 cols 39-41, a stem at (12,40), colour 8 filling col 40 from row 12 to row 40, colour 8 filling row 40 from col 14 to col 40, and the comb teeth at rows 38-42 cols 14-18 with floor gaps only at (39,14) and (41,14). ONE CONNECTED WIRE from knob to gate, which is why I read the knob as the switch. Not one colour-8 pixel has moved in ten frames, which is why 8 is board and not an object; the first colour-8 pixel that changes turns this theorem into physics and hands me a rule."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_knob_is_the_only_interactive_thing_within_reach "Ten of the eleven reachable cells are bounded by floor and void alone. The eleventh, (1,5) at rows 8-12 cols 32-36, is separated from the knob's cell (1,6) at cols 38-42 only by separator col 37, which is floor. Lattice (1,6) contains nine colour-8 ring pixels, so even under the aperture rule the body cannot stand there while 8 is solid. Either 8 is walkable and key2_body_arrives is wrong at the knob; or the knob answers to proximity from (1,5); or it answers to a key never pressed. My rules make the first self-announcing: drive the body into a colour-8 cell and my manual predicts it stays put, and the world contradicts that in one command if 8 is walkable. C=2 to C=5 is three lattice cells of eastward travel and C=2 to C=6 is four. Ten commands spent and none has taken step one, because the east key is still unnamed."
    [depends: the_socket_is_unreachable_until_the_comb_opens  probe: pending]

  theorem two_actions_have_never_been_pressed_and_one_of_them_may_be_a_click "actions_used is ACTION1..ACTION5 plus RESET; the alphabet is ACTION1..ACTION7. Two commands are entirely unconstrained, and in this action family one is normally a click carrying coordinates. That matters here: the knob is a 3x3 target the body appears unable to stand on, and a click is the shape of interaction that presses it. I cannot write such a rule -- the guard language admits act=key(6) but has nowhere to put two coordinates, so a click rule would fire on every click anywhere and be silently wrong about which cell was clicked. If a click drives this world my manual can record its EFFECT, comb pixels going 8 to 5, and never its precondition."
    [probe: pending]

  theorem the_first_step_east_costs_forty_eight_pixels_and_that_is_not_a_defect "Priced in advance so it cannot be sold to me as a surprise. The arm instances exactly the cells that have already changed, so rows 8-12 cols 20-24 -- lattice (1,3), the first cell east of spawn -- are board and have NO instance. When the body first steps there, 24 arrival pixels are undrawable no matter what rule I write, and the 24 departure pixels at rows 8-12 cols 14-18 are undrawable too until an east-leaves rule is witnessed, because no rule of mine turns spawn-ring Glyph9 cells from 9 to 5 on any key but 2. 48 wrong cells for the first step onto fresh ground, plus one for the leading-edge burn at index 10, then 24 for the second step, then 0. The body also CHANGES TYPE as it walks -- Glyph9 at rows 8-12, Vacated everywhere else -- because typing is by frame-0 colour and all that floor was 5. A manual that heals one step behind is the price of this arm, and the pixels it costs are the tuition, not the damage."
    [depends: the_maze_is_a_six_pixel_lattice, i_cannot_draw_the_leading_edge_burn  probe: pending]

  theorem silence_is_a_prediction_and_two_of_my_five_spawn_silences_are_forged "The compiled transition function is total: where no rule fires the successor equals the current state, so my manual never says I do not know, it says nothing happens, in the same voice it uses for things it has seen. Audit the five keys at the cell the body stands on. key(1): inert, WITNESSED twice, t1 and t8, apart from the t8 burn. key(2): moves 48 body cells, witnessed twice, both rules at full coverage. key(3): inert, WITNESSED once, t9. key(4): NO WITNESS AT THIS CELL -- pressed once ever, from one cell south, where east and west are void. key(5): NO WITNESS AT THIS CELL -- never pressed at spawn at all. So two of five silences at spawn are forged death certificates, down from three, and one of the two is the last surviving candidate for east. That is the largest remaining block of unearned confidence in this file and it is the cheapest to fix: one press each."
    [depends: the_action_map_after_nine_transitions, the_spawn_probe_guard_is_the_untested_half_of_thirteen_rules  probe: pending]

  theorem the_cascade_length_is_a_free_channel_and_it_just_paid_out "Last round I predicted, free to check in the raw diff, that the next ACTION2 taken from configuration B would return 7 frames if the cascade count belongs to the key and 9 if it belongs to the panel. It returned NINE. So the count is not a function of the key alone: ACTION2 gave 7 frames from configuration A at t2 and 9 from configuration B at t6, while ACTION5 gave 9 both times and every no-op gave 1. Something outside the key -- the panel configuration is the candidate with a witness -- lengthens the animation. This is hidden state I discard by construction, since cascade single_frame compares only net effect, and it corroborates the_world_is_probably_not_a_function_of_the_drawn_frame from a second direction. It costs nothing in replay and buys nothing in prediction; I keep reading it because it is free."
    [depends: the_panel_is_a_two_slot_selector_toggled_by_action5  probe: passed]

  theorem the_no_op_rule_fails_the_gain_test_and_i_keep_it_for_a_narrow_reason "key3_inert_below_spawn recolours one pixel to the colour it already has, has two witnesses on transitions where zero cells changed, and replay is identical without it. It explains no pixel and lengthens the manual, so it fails constraint 3 and I say so rather than dressing it up. The reason I keep it: it is the ONLY occurrence of act=key(3) in the file, and deleting it narrows the action set certify adjudicates from five keys to four. Its counterpart key1_inert_at_spawn is DELETED this round, because meter_burn_next_key1 now mentions key(1) with a real witness at t8 and does real work, so the placeholder is redundant on both counts."
    [depends: key3_inert_below_spawn, meter_burn_next_key1  probe: passed]

  theorem the_rules_are_pairwise_exclusive_and_off_board_cell_terms_are_false "Constraint 5, checked by hand over all four instance types in both panel configurations. Under key(2): body_leaves needs below-six to render 5, off-board for any row past 57, so it cannot fire on a meter cell; the two burn rules split on rightof = wall against a colour test on rightof, which cannot both hold. Under key(5) the type Glyph9 is split five ways by COLOUR FIRST -- 5 for respawns, 9 for the two dim rules, 2 for slot1_lights, 0 for underline1_lights -- and colours 2 and 0 occur on no other Glyph9 cell in any observed state, so the return half needs no geometry at all. The two colour-9 rules are then split by above-four: slot1_dims needs it to BE WALL, true only for rows 0-3; underline1_dims needs a COLOUR TEST on it, which is false off-board rather than raising, so it selects row 5 and excludes rows 0-3, and its above-six wall test excludes the meter at row 63. Spent splits by colour into 1 (the five configuration-A rules) against 9 and 0 (the two configuration-B rules); within colour 1 the geometry is row 1 by above-two wall, row 3 by a colour test on above-two, row 2 by above-three wall plus a colour test on above-one, and within row 2 col 5 by leftof-six wall, col 6 by leftof-seven wall plus a colour test on leftof-one, col 7 by a colour test on leftof-two -- each pair separated by the same off-board-is-false trick, which is the load-bearing fact of this whole file. Dark splits by colour 0 against 9. Not one rule uses not, deliberately."
    [depends: key2_body_leaves, key5_slot2_centre_darkens, key5_slot1_lights  probe: pending]

  theorem what_i_predict_before_i_see_it "Written in advance so it can cost me. The body is at spawn, the panel is in configuration A, four meter cells are burned at row 63 cols 60-63, and the next command index is 10, which is EVEN, so under the clock it burns (63,59) whatever is pressed and I cannot draw that cell. ACTION4 at spawn, my first choice: my manual predicts ZERO cells and has NO WITNESS for that silence. If the body steps east I pay 48 undrawable pixels already priced, and EAST IS ACTION4; if nothing moves beyond the burn, NO KEY IS EAST and the lattice is a column, which rewrites four theorems. ACTION5 at spawn, my second choice: my manual predicts ZERO cells; a panel toggle refutes the spawn_probe guard on thirteen rules, a body jump refutes the up reading of ACTION5, and nothing at all confirms both. ACTION1 at spawn: 0 cells plus a burn I cannot draw, one witnessed silence repeated, nothing bought. ACTION2 at spawn: 48 body cells I draw correctly plus the undrawable burn, and both its rules are already at full coverage, so it buys only the cascade datum. ACTION3 at spawn: 0 cells, witnessed at t9, nothing bought. THE SINGLE OBSERVATION THAT WOULD MOST CHANGE THIS FILE: any panel pixel moving on a command taken while the body is HOME, because that falsifies the guard on thirteen rules at once."
    [depends: the_action_map_after_nine_transitions, the_meter_is_a_two_command_clock  probe: pending]

  theorem what_the_engines_gave_me "mdl_segmenter reports NEGATIVE gain on both variants, -3623 bits unsplit and -27437 split by colour, which is the segmenter saying its own script costs more than writing the pixels. I take its TRACK LIST and not its verdict. obj0 (colour 9, eight cells, 3x3, all ten frames) and obj2 (colour 9, 1x3, all ten frames) are slot 1's ring and underline 1 persisting through both toggles, so it does not see the panel as appearing and vanishing, which corroborates a marker with two seats rather than two objects. obj1 (colour 1, nine cells, 3x3, frames 0-4) is slot 2 solid in configuration A; obj5 (colour 2, eight cells, FIRST FRAME 5, present 2 frames) is slot 1 after the dim, and its appearance at frame 5 and disappearance by frame 7 is exactly key5_slot1_dims followed by key5_slot1_lights, dated independently by an engine that has never seen my rules; obj6 (colour 1, nine cells, FIRST FRAME 7, present 3 frames) is slot 2 solid again after the return. THAT IS THE ROUND'S CORROBORATION AND IT ARRIVED FROM OUTSIDE. obj4 is the whole 64-cell row-63 bar, of which 4 cells are now dynamic. obj3 is a 1006-cell colour-null blob that swallowed the maze floor AND the body: connected_components(4) cannot see the mover, because the mover is a ring adjacent to floor on every side, and THAT ABSENCE IS THE FINDING. None of these gets a type of its own; a second type on the same pixels invites the double claim rule 5 forbids. zero_space self-reports THIN in its own words -- 9 transitions constrain rank 5 of 375 features, null space dimension 370 -- and its one global law is my census cell for cell, 75 cells, which is a consistency check and not a discovery. cegis_miner refuses every track and its verdict, the world does not narrate as one mover, is true of the arm and false of the world: there is one mover, a rigid 24-pixel ring, and the arm can only see 24 simultaneous recolours."
    [probe: passed]
```

=== PLAYBOOK ===
```
# playbook.dsl -- what to buy with the next command, not a route.
#
# ========= THE STATE OF PLAY =========
# Ten states, nine transitions. The manual compiles and replayed 5/5 last
# round with zero unexplained cells; the two refutations that brought me
# back are both repaired IN THE MANUAL, not here: the 23 panel cells of
# t7 now have five return rules, and the two new meter cells are dynamic
# so their burns can finally be drawn. I expect 9/9 this round, and if it
# is not 9/9 the defect is mine and legible.
#
# ========= THERE IS STILL NO GOAL, AND I HAVE SAID WHY IN THE MANUAL =========
# theorem the_goal_is_absent_because_no_instance_can_name_the_socket gives
# the argument and the price: is_goal is False, plan returns
# no_goal_declared, commit never runs, and EVERY COMMAND THIS LEG IS A
# PROBE. That is now a stated position rather than a silence, and the
# ranking below is a ranking of expected information, which is the only
# currency available while the goal section is empty. The observation
# that ends it: the first colour change anywhere in the socket bracket,
# rows 49-55 cols 43-49, or its pip at (52,46).
#
# ========= THE BOARD AS THE MANUAL NOW SEES IT =========
#   Body at spawn, lattice (1,2). North and west void, south and east open.
#   Panel in configuration A. Meter: 4 cells burned, cols 60-63 of row 63.
#   At spawn:  key(2) -> 48 body cells, both rules already at full coverage
#              key(1) -> nothing, WITNESSED twice, t1 and t8
#              key(3) -> nothing, WITNESSED once, t9
#              key(4) -> UNWITNESSED HERE, and the last candidate for east
#              key(5) -> UNWITNESSED HERE, and the only test of the guard
#                        colored(spawn_probe, 5) that thirteen rules share
#   The meter is a clock, one cell per two commands, 60 cells left. Index
#   10 is EVEN and burns (63,59) whatever is pressed; that cell is board,
#   has no instance, and no rule of mine can draw it. Discount it.
#
# ========= THE ONE THING WORTH BUYING =========
# ACTION4 AT SPAWN. It is the only key never pressed from this cell whose
# answer names a direction either way. ACTION2 is down; ACTION5 carries
# the body north; ACTION1 was inert here twice and ACTION3 once, with
# east open the whole time, so neither is east; ACTION3 and ACTION4 were
# both inert one cell south where east and west are void, which is what
# the horizontal pair would do there. So east is ACTION4 or east does not
# exist. A step east means the road to the knob is open and costs 48
# undrawable pixels I have priced in the manual. No step means NO KEY IS
# EAST, movement is vertical only, and four theorems get rewritten -- a
# bigger finding than the step, bought for the same one command.
#
# SECOND: ACTION5 AT SPAWN. My manual predicts zero cells. A panel toggle
# there falsifies the spawn_probe guard on thirteen rules at once, which
# is the single observation that would most change the file; a body jump
# falsifies the up reading of ACTION5; nothing at all confirms both.
#
# ------------------------------------------------------------------------
# STATE 9: body home at lattice (1,2); panel configuration A; four meter
# cells burned; next command index 10. Eleven lattice cells reachable and
# the body has stood in two. Three steps east along lattice row 1 reach
# the cell beside the knob; the knob is the far end of one connected
# colour-8 wire whose near end is the comb; the comb gates every route to
# the socket at (8,7).

order     say_out_loud_that_every_command_is_a_probe_while_is_goal_is_false [proof: lean]
order     treat_the_first_socket_pixel_that_moves_as_the_goal_writing_event [proof: lean]
order     settle_the_east_key_before_anything_else_at_this_cell            [proof: lean]
order     prefer_a_press_that_answers_two_open_questions_over_one          [proof: lean]
order     treat_predicted_inertness_as_ignorance_unless_a_witness_backs_it [proof: lean]
order     rank_by_witnesses_a_command_would_create_not_by_pixels_it_moves  [proof: lean]
order     stop_pressing_a_key_the_moment_its_question_has_been_answered    [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired  [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance               [proof: lean]
order     spend_the_clock_on_unwitnessed_key_cell_pairs_not_on_repeats     [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it               [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it       [proof: lean]
order     read_an_empty_certify_block_as_nothing_known_not_nothing_wrong   [proof: lean]

prune     ranked_only_because_the_manual_predicts_the_most_pixels => dead   [proof: lean]
prune     every_rule_it_would_witness_is_already_at_full_coverage => dead    [proof: lean]
prune     repeats_a_key_whose_inertness_here_is_already_witnessed => dead    [proof: lean]
prune     repeats_the_key_that_the_previous_command_just_answered => dead    [proof: lean]
prune     divergence_lies_only_on_the_meter_leading_edge => dead             [proof: lean]
prune     probes_the_meter_parity_that_nine_transitions_already_settled => dead [proof: lean]
prune     ranked_only_because_a_refutation_fired_on_it => dead               [proof: lean]
prune     revisits_a_lattice_cell_by_an_already_witnessed_key => dead        [proof: lean]
prune     action_excluded_for_this_direction_by_an_earlier_no_op => dead     [proof: lean]
prune     destination_ring_pixels_are_not_all_floor => dead                  [proof: lean]
prune     route_that_crosses_the_comb_while_it_still_reads_eight => dead     [proof: lean]
prune     meter_exhausted and not goal => dead                               [proof: lean]

heuristic keys_whose_inertness_here_rests_on_no_witness                     [admissible: lean]
heuristic direction_labels_a_command_would_fix_by_elimination               [admissible: lean]
heuristic rules_whose_shared_guard_a_single_command_would_falsify           [admissible: lean]
heuristic live_readings_a_single_command_can_eliminate                      [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_meter_edge                   [admissible: lean]
heuristic lattice_cells_the_body_has_never_occupied                         [admissible: lean]
heuristic lattice_distance_to_the_knob_while_the_gate_is_shut               [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open              [admissible: lean]
heuristic commands_remaining_before_the_bar_is_spent                        [admissible: lean]

prefer    a_key_whose_predicted_inertness_here_has_never_been_witnessed    [ev: 2/5 keys at spawn]
prefer    a_key_that_names_a_direction_whichever_way_it_answers            [ev: 1/1 candidates left]
prefer    a_press_that_tests_the_guard_shared_by_thirteen_rules            [ev: 13/22 rules]
prefer    a_key_never_pressed_from_the_cell_the_body_stands_on             [ev: 2/5 keys at spawn]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                 [ev: 9/9 diffs]
prefer    east_along_lattice_row_one_over_any_other_axis                   [ev: 1/1 levels]
prefer    a_press_at_a_third_cell_that_splits_up_from_home_from_undo       [ev: 2/2 key5_presses]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered          [ev: 1/1 levels]
```

=== LOG ===
```json
[
  {"id": "O-01", "subject": "mdl obj0 + obj2 (colour 9, 3x3 ring and 1x3 bar, present all 10 frames)", "verdict": "accept", "as": "Glyph9 instances at rows 1-3 cols 1-3 and row 5 cols 1-3", "why": "the segmenter keeps them present through both panel toggles, which is what a marker with two colour seats looks like and not what two objects appearing and vanishing looks like."},
  {"id": "O-02", "subject": "mdl obj5 (colour 2, 8 cells, first_frame 5, frames_present 2)", "verdict": "accept", "as": "slot 1 in configuration B, owned by Glyph9", "why": "an engine that has never seen my rules dates its appearance to frame 5 and its disappearance by frame 7, which is exactly key5_slot1_dims followed by key5_slot1_lights."},
  {"id": "O-03", "subject": "mdl obj1 + obj6 (colour 1, 9 cells, frames 0-4 then from frame 7)", "verdict": "accept", "as": "Spent, slot 2 solid in configuration A", "why": "the gap in presence spans exactly frames 5-6, the interval between the t5 and t7 toggles, corroborating the two-configuration reading from outside the manual."},
  {"id": "O-04", "subject": "mdl obj4 (colour 9, 1x64)", "verdict": "accept", "as": "row 63 meter bar, 4 of its 64 cells dynamic and instanced as Glyph9", "why": "the bar is one connected component to the segmenter but only its burned right end has ever varied, so only that end can carry instances."},
  {"id": "O-05", "subject": "mdl obj3 (colour null, 1006 cells, 50x38)", "verdict": "reject", "as": "no type", "why": "connected_components(4) merged the maze floor with the mover; a type on those pixels would double-claim every cell Vacated already owns, which is the constraint-5 error the grammar warns about."},
  {"id": "O-06", "subject": "Dark, declared on background colour 0", "verdict": "accept", "as": "underline 2, rows 5 cols 5-7", "why": "last round I flagged it as possibly not instanced and named the exact three pixels it would cost; replay came back 5/5 with 0 unexplained, so the arm does instance varying background-coloured cells and the doubt is discharged."},
  {"id": "R-01", "subject": "key5_slot1_lights, key5_underline1_lights, key5_slot2_ring_resets, key5_slot2_centre_resets, key5_underline2_dims", "verdict": "accept", "as": "the panel return half, ev t7", "why": "t7 witnesses all 23 cells going from configuration B back to A, and each rule needs only a colour test because colours 2, 0 on Glyph9 and 9, 0 on Spent occur nowhere else in those types."},
  {"id": "R-02", "subject": "meter_burn_next_key1 (ACTION1 burns the cell left of a burned cell)", "verdict": "accept", "as": "replay machinery for t8", "why": "t8 burned (63,60) under ACTION1 while t1 under the same key at the same cell burned nothing; the rule fires at t8 and correctly cannot fire at t1 because nothing was yet burned to its right."},
  {"id": "R-03", "subject": "meter_burn_next_key2 (ev t6)", "verdict": "accept", "as": "replay machinery", "why": "(63,61) is dynamic now, so an instance exists and the transition that refuted me as P-01 can finally be drawn."},
  {"id": "R-04", "subject": "reading A of the meter (burns follow keys 2 and 4)", "verdict": "reject", "as": "refuted", "why": "ACTION1 burned at t8; reading A predicts no burn under ACTION1 and is dead, while the even-index reading fits 4/4 burns and 5/5 non-burns."},
  {"id": "R-05", "subject": "all four burn rules as statements about mechanism", "verdict": "probe-pending", "why": "they are knowingly mis-attributed to keys because the guard language cannot count commands; they replay all four burns and predict nothing, and the manual names the exact future press that will expose them."},
  {"id": "R-06", "subject": "key1_inert_at_spawn", "verdict": "reject", "as": "deleted", "why": "it existed only to keep act=key(1) in the adjudicated action set, and meter_burn_next_key1 now does that with a real witness and a real pixel."},
  {"id": "R-07", "subject": "key3_inert_below_spawn", "verdict": "accept", "as": "kept against the gain test, and said so", "why": "it recolours one pixel to the colour it already has and explains nothing, but it is the only occurrence of act=key(3) and deleting it would shrink the adjudicated action set to four keys."},
  {"id": "R-08", "subject": "key5_body_respawns as a RETURN rule", "verdict": "probe-pending", "why": "it is guarded on pixels, not on where the body is, so from any third lattice cell it predicts a second body drawn at spawn without erasing the first; 24 wrong pixels, priced in the manual before the press."},
  {"id": "L-01", "subject": "the meter is a two-command clock", "verdict": "accept", "as": "theorem the_meter_is_a_two_command_clock", "why": "burns at command indices 2, 4, 6, 8 and nowhere else, across three different keys, which no key-based rule can produce."},
  {"id": "L-02", "subject": "ACTION4 is the last candidate for east", "verdict": "probe-pending", "why": "ACTION1 inert at spawn twice and ACTION3 once with east open rules them out; ACTION3 and ACTION4 inert one cell south rules both out of vertical; ACTION2 is down and ACTION5 carries the body north."},
  {"id": "L-03", "subject": "the panel is a two-slot selector toggled by ACTION5", "verdict": "accept", "as": "theorem, both directions witnessed", "why": "t5 A to B and t7 B to A, 23 cells each time, and the underlined slot is always the one rendered in colour 9."},
  {"id": "L-04", "subject": "the panel guard colored(spawn_probe, 5)", "verdict": "probe-pending", "why": "both witnesses had the body away; ACTION5 has never been pressed at spawn, so the guard shared by thirteen rules is untested in one direction and one press settles it."},
  {"id": "L-05", "subject": "cascade length belongs to the key", "verdict": "reject", "as": "refuted by t6", "why": "last round predicted 7 frames for ACTION2 from configuration B if the count were key-determined; it returned 9 against 7 from configuration A, so hidden state outside the key drives the animation length."},
  {"id": "L-06", "subject": "the world is a function of the drawn frame", "verdict": "probe-pending", "why": "the clock makes it nearly impossible -- s0 equals s1 and s2 equals s3 pixel for pixel while their successors differ in whether a cell burns -- but each pair received different keys, so the direct witness still costs two identical presses."},
  {"id": "P-01", "subject": "probe P-01 (ACTION2 at t6, frontier vacuous)", "verdict": "accept", "as": "answered by construction", "why": "the missing pixel was (63,61), board at the time and undrawable by any rule; it is dynamic now and meter_burn_next_key2 draws it, so t6 should replay whole."},
  {"id": "P-02", "subject": "probe P-02 (ACTION5 at t7, frontier vacuous)", "verdict": "accept", "as": "answered by five new rules", "why": "the manual had no return half for the panel and I had priced its absence at exactly 23 pixels; the bill arrived and is paid, not excused."},
  {"id": "P-03", "subject": "next command", "verdict": "probe-pending", "as": "ACTION4 at spawn", "why": "the only key never pressed from this cell whose answer names a direction either way: a step means east is ACTION4, no step means no key is east and the lattice is a column."},
  {"id": "E-01", "subject": "the true meter law, burn on every even command index", "verdict": "probe-pending", "as": "inexpressible", "why": "wanted a guard on a command counter or on index parity; the guard language reads only pixels, off-board tests and the action name, and no pixel records the parity, so I wrote four key-attributed replay rules and declared them mis-attributions in theorem the_burn_rules_are_deliberate_mis_attributions_kept_only_for_replay."},
  {"id": "E-02", "subject": "a winning condition naming lattice cell (8,7)", "verdict": "probe-pending", "as": "inexpressible", "why": "wanted goal Body.pos = socket; arc-instances: all gives no single named instance, a second colour-9 type would double-claim, the socket interior is board so count has nothing to range over, and every count that is currently false is also satisfied by an irrelevant one-move state. Wrote theorem the_goal_is_absent_because_no_instance_can_name_the_socket with the price and the observation that ends it."},
  {"id": "E-03", "subject": "a click action on the knob", "verdict": "probe-pending", "as": "inexpressible", "why": "ACTION6 and ACTION7 have never been pressed and one is normally a click; act=key(6) parses but there is nowhere to put coordinates, so such a rule would fire on every click anywhere. Recorded as a theorem instead."}
]
```
```
