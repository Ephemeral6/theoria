# call-003-theorize-round1

model: `claude-opus-5` · 623643 ms · $1.461651 · usage {"cache_creation": {"ephemeral_1h_input_tokens": 25839, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 25839, "cache_read_input_tokens": 0, "inference_geo": "not_available", "input_tokens": 2, "iterations": [{"cache_creation": {"ephemeral_1h_input_tokens": 25839, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 25839, "cache_read_input_tokens": 0, "input_tokens": 2, "output_tokens": 47363, "type": "message"}], "output_tokens": 47363, "server_tool_use": {"web_fetch_requests": 0, "web_search_requests": 0}, "service_tier": "standard", "speed": "standard"}

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
0222099900000000000000000000000000000000000000000000000000000000
0202090900000000000000000000000000000000000000000000000000000000
0222099900000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000099900000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000555555555555555555555555555555500000000000000000000
0000000000000555555555555555555555555555555500000000000000000000
0000000000000555555555555555555555555558885500000000000000000000
0000000000000555555555555555555555555558885500000000000000000000
0000000000000555555555555555555555555558885500000000000000000000
0000000000000555555555555555555555555555855500000000000000000000
0000000000000555555555555555555555555555855500000000000000000000
0000000000000599999500000555555500000005850000000000000000000000
0000000000000599999500000555555500000005850000000000000000000000
0000000000000599599500000555555500000005850000000000000000000000
0000000000000599999500000555555500000005850000000000000000000000
0000000000000599999500000555555500000005850000000000000000000000
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
- t6   ACTION1   frames=1   state=NOT_FINISHED (63,61) 9->1
- t7   ACTION2   frames=9   state=NOT_FINISHED 48 cells changed, rows 8-18, cols 14-18, [5, 9] -> [5, 9]
- t8   ACTION3   frames=1   state=NOT_FINISHED (63,60) 9->1
- t9   ACTION4   frames=1   state=NOT_FINISHED no cells changed

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
   "ValueError: object absent at frame 0; unsupported on this fixture"
  ],
  "tracks": [
   {
    "error": "NoSeparatingGuard: no literal separates transition 1 from the positives",
    "mine_ms": 0,
    "ms": 0,
    "traceback": "Traceback (most recent call last):\n  File \"C:\\Users\\user\\Desktop\\theoria-wt-p8\\theoria-arm\\world\\adapt.py\", line 48, in _timed\n    value = fn(*args, **kwargs)\n  File \"C:\\Users\\user\\Desktop\\theoria-wt-p8\\engine-rig\\engines\\cegis_miner\\__init__.py\", line 92, in run\n    result = mine(transitions)\n  File \"C:\\Users\\user\\Desktop\\theoria-wt-p8\\engine-rig\\engines\\cegis_miner\\miner.py\", line 320, in mine\n    guard, trace, added = synthesize(positives, universe, masks)\n                          ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\Users\\user\\Desktop\\theoria-wt-p8\\engine-rig\\engines\\cegis_miner\\miner.py\", line 157, in synthesize\n    raise NoSeparatingGuard(\n        \"no literal separates transition %d from the positives\" % cex\n    )\nengines.cegis_miner.miner.NoSeparatingGuard: no literal separates transition 1 from the positives\n",
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
    "traceback": "Traceback (most recent call last):\n  File \"C:\\Users\\user\\Desktop\\theoria-wt-p8\\theoria-arm\\world\\adapt.py\", line 48, in _timed\n    value = fn(*args, **kwargs)\n  File \"C:\\Users\\user\\Desktop\\theoria-wt-p8\\engine-rig\\engines\\cegis_miner\\__init__.py\", line 92, in run\n    result = mine(transitions)\n  File \"C:\\Users\\user\\Desktop\\theoria-wt-p8\\engine-rig\\engines\\cegis_miner\\miner.py\", line 320, in mine\n    guard, trace, added = synthesize(positives, universe, masks)\n                          ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\Users\\user\\Desktop\\theoria-wt-p8\\engine-rig\\engines\\cegis_miner\\miner.py\", line 157, in synthesize\n    raise NoSeparatingGuard(\n        \"no literal separates transition %d from the positives\" % cex\n    )\nengines.cegis_miner.miner.NoSeparatingGuard: no literal separates transition 1 from the positives\n",
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
   "recolor": 7,
   "vanish": 1
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
    "frames_present": 5,
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
    "baseline_bits": 2808,
    "compression_ratio": 2.587251,
    "events": 11,
    "gain_bits": -4457,
    "ms": 22,
    "script_bits": 7265,
    "split_by_color": false,
    "tracks": 6
   },
   {
    "baseline_bits": 2808,
    "compression_ratio": 9.185185,
    "events": 31,
    "gain_bits": -22984,
    "ms": 38,
    "script_bits": 25792,
    "split_by_color": true,
    "tracks": 22
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
  "difference_rank": 6,
  "engine": "zero_space",
  "evidence_adequacy": {
   "constrained_fraction": 0.016,
   "difference_rank": 6,
   "features": 375,
   "space_dimension": 369,
   "transitions": 9,
   "verdict": "THIN: 9 transitions constrain rank 6 of 375 features, so the null space has dimension 369 and nearly every vector in it is a 'law' that is true over these states and unfalsified rather than confirmed. Treat every law below as a correlation awaiting a transition that could break it, not as a conservation law."
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
     "c
```

The full proposal stream is 1111 rows in `candidates.jsonl`.

## The manual as it stands

```
# theory.dsl -- world observed for 5 transitions (RESET + ACTION1..ACTION5).
# 73 cells in this world ever change and this manual accounts for every one.
#
# What changed this round, and why:
#   The surprise was replay_mismatch at t2 (ACTION2, 49 cells). It is the
#   defect the previous manual already declared: the body is a 24-cell rigid
#   donut and it slides SIX pixels, while `moved` moves one cell and `jumped`
#   moves at most two. That part I still cannot say, and I say so again below.
#   But two things I CAN say, and did not, are now rules:
#     - the row-63 meter burns its rightmost live cell on ACTION2 and ACTION4
#       (this is a genuine law, general, and it makes t4 exact);
#     - on ACTION2 the body vacates the cells it occupied and floor shows
#       through (24/24, general, grammar-safe). It draws half of the move.
#   Everything I refused to write is named in `laws:` with the exact text I
#   would have written, so it is a probe and not a silence.

semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Glyph9  { pos: Coord, color: Int }   # arc-colour: 9  arc-instances: all
  object Glyph2  { pos: Coord, color: Int }   # arc-colour: 2  arc-instances: all
  object Spent   { pos: Coord, color: Int }   # arc-colour: 1  arc-instances: all
  object Vacated { pos: Coord, color: Int }   # arc-colour: 5  arc-instances: all
  landmark spawn_center    # arc-cell: (10, 16)
  landmark socket_center   # arc-cell: (52, 46)
  landmark knob_center     # arc-cell: (10, 40)
  landmark gate_center     # arc-cell: (40, 16)
  domain dir { up, down, left, right }
  Glyph9  [segment: dynamic_colour_9 ev: t0-t5 compress: 37]
  Glyph2  [segment: dynamic_colour_2 ev: t5 compress: 8]
  Spent   [segment: dynamic_colour_1 ev: t0-t5 compress: 9]
  Vacated [segment: dynamic_colour_5 ev: t2,t5 compress: 24]

events:
  event moved(o, dir) | jumped(o, dest) | recolored(o, c) | vanished(o)

rules:
  rule meter_burn_key2 forall ?p in Glyph9 [ev: t2 cov: 1/1]
    when act=key(2) and below(?p) = wall and rightof(?p) = wall then recolored(?p, 1)

  rule meter_burn_key4 forall ?p in Glyph9 [ev: t4 cov: 1/1]
    when act=key(4) and below(?p) = wall and colored(rightof(?p), 1) then recolored(?p, 1)

  rule key2_vacates_body forall ?p in Glyph9 [ev: t2 cov: 24/24]
    when act=key(2) and not colored(above(?p), 0) and not colored(below(?p), 0) and not colored(leftof(?p), 0) and not colored(rightof(?p), 0) then recolored(?p, 5)

laws:
  invariant nine_count_frame0 count(Glyph9) = 37 [status: counted]
  invariant board_static count(board) = 4023 [status: counted]

  theorem dynamic_census "Exactly 73 cells ever change and I can name all of them, from the engine's own cell list: 23 are a status panel at rows 1-5, cols 1-7; 24 are a 5x5 donut of colour 9 at rows 8-12, cols 14-18, minus its hole (10,16); 24 are the same shape at rows 14-18, cols 14-18, minus its hole (16,16); 2 are the right end of a 64-cell bar on row 63. 23+24+24+2 = 73, which closes the budget with nothing left over. At frame 0 those 73 split as 37 colour-9 cells, 9 colour-1 cells, 24 colour-5 cells and 3 background cells, and 37+9+24 = 70, which is exactly the arm's cells_needing_an_owner."
    [probe: pending]

  theorem meter_head_is_uniquely_addressable "The interior of the row-63 bar never changes, so it is board, and the ONLY Glyph9 instances with below(?p) = wall are (63,62) and (63,63). That is why meter_burn_key2 and meter_burn_key4 can name the head of the meter with two documented guards and no coordinates. meter_burn_key2 picks (63,63) by rightof(?p) = wall; meter_burn_key4 picks (63,62) by its right neighbour already being spent. If colored() on an off-board cell were to return true for 1, meter_burn_key4 would also ground on (63,63), where recolored(?p, 1) is a no-op -- so the rule is safe under either reading of off-board."
    [depends: meter_burn_key2, meter_burn_key4  probe: pending]

  theorem meter_depletes_rightward "ACTION2 burned (63,63) and ACTION4 burned (63,62), both 9 -> 1, so the bar empties from its right end leftward and is shared across actions. ACTION1, ACTION3 and ACTION5 burned nothing. I have one observation per action and therefore two rules rather than one law over a key domain; I do not know whether key(1)/key(3) are free because they are different actions or because they were refused moves. Candidate separator: at t4 the destination lattice cell is interior void, while at t1 and t3 the destination is off the play area entirely -- so 'a move attempt that stays on the play area costs one meter cell, whether or not it succeeds' is the hypothesis, and it predicts that key(1) and key(3) WILL burn a cell once the body is somewhere they can legally aim."
    [depends: meter_burn_key2, meter_burn_key4  probe: pending]

  theorem body_guard_isolates_the_donut "The arm finds objects by colour alone, so Glyph9's 37 frame-0 instances are three different things: the 24 donut cells, 8 panel-ring cells, 3 underline cells, 2 meter cells. The conjunction used by key2_vacates_body -- no neighbour in any of the four directions renders as background -- is true of all 24 donut cells and false of all 13 others, at BOTH observed body positions: the donut is embedded in colour-5 floor on every side (row 7 and row 13 and row 19 are floor across cols 14-18, col 13 and col 19 are floor), while every panel cell touches row 0, row 4, col 0 or col 4, and every meter cell has row 62 above it. This is the only separator I have and it is a property of the floor, not of the body, so it will fail the moment the body stands next to a background cell."
    [depends: key2_vacates_body  probe: pending]

  theorem the_move_is_six_pixels_and_the_dsl_cannot_say_it "Both observed body positions have their top-left at (6R+2, 6C+2) -- rows 8-12 is R=1, rows 14-18 is R=2 -- and the observed displacement is exactly six pixels. The maze agrees: void columns run cols 20-24 and cols 32-36 with single floor columns 19, 25, 31 between them. So the world is a coarse 6-pixel lattice and one action moves the donut one lattice cell. The event table tops out at two cells: moved(o, dir) is one, jumped(o, over, dir) is two. There is no event of any arity that displaces an instance by six, and no way to move 24 instances as a body. This is the largest compression in the world and it is inexpressible; cegis_miner reached the same wall from the other side and refused every track with 'the world does not narrate as one mover'."
    [probe: pending]

  theorem what_key2_vacates_body_deliberately_does_not_draw "key2_vacates_body draws the 24 cells the donut LEAVES and nothing the donut ARRIVES at, so after ACTION2 my manual shows an empty maze. That is a hole, not a lie: it takes t2 from 49 wrong cells to 24, and every cell it does draw is right. I know exactly which 24 it misses -- rows 14-18, cols 14-18 minus (16,16). I accept an avatar-less state model rather than the two alternatives, both of which I reject below."
    [depends: key2_vacates_body  probe: pending]

  theorem the_two_destination_rules_i_refused "First: 'rule key2_lands forall ?v in Vacated when act=key(2) then recolored(?v, 9)'. It is 24/24 on t2 and takes t2 to zero wrong cells, because the arm's Vacated instances happen to be exactly the 24 destination cells and nothing else. That is not a law, it is the t2 answer key wearing a forall -- it would be right again only for an ACTION2 pressed from spawn and wrong for every other ACTION2 in the game. Rejected as a stored solution. Second, and this one I want: 'rule key2_lands forall ?v in Vacated when act=key(2) and colored(above(above(above(above(above(above(?v)))))), 9) then recolored(?v, 9)' -- a floor cell whose cell six above is body-coloured becomes body-coloured. That IS general, it is 24/24 on t2, and it even leaves (16,16) alone for the right reason, because the cell six above it is the donut's hole. I did not write it because the grammar is published as 'cells -- EXHAUSTIVE: above(x) below(x) ...' without saying whether x may itself be a cell, and a parse error costs the entire manual, not one rule. PROBE: compile this one rule alone. If cell terms nest, it goes in next round and t2 replays exactly."
    [depends: key2_vacates_body  probe: pending]

  theorem key1_key3_are_silent_here "ACTION1 (t1) and ACTION3 (t3) changed not one pixel and burned no meter cell. Having no rule for them IS the prediction 'nothing happens', and that prediction is exactly right on both. Both are consistent with up and left being refused at rows 8-12, cols 14-18: above the donut is background past row 7 and left of it is background past col 13."
    [probe: pending]

  theorem key5_is_a_respawn_not_a_direction "ACTION5 changed 71 cells: 48 put the donut back at rows 8-12 from rows 14-18, and 23 flipped the whole panel. It burned no meter cell and it landed the body exactly where t0 started it. I read ACTION5 as respawn/next-attempt, and I have written no rule for it, because the honest rule needs the same six-pixel displacement plus a panel rewrite that includes three cells I cannot own. A plain 'up' plus an unrelated panel tick fits the same pixels and I cannot yet separate the two readings; the separator is cheap -- press ACTION5 from a position that is not one lattice cell below spawn."
    [probe: pending]

  theorem panel_layout "Two 3x3 icon slots at cols 1-3 and cols 5-7 of rows 1-3, each with a 1x3 underline at row 5. Frames 0-4: slot 1 is a hollow colour-9 ring with its underline lit, slot 2 is a solid colour-1 block with no underline. Frame 5: slot 1 is a hollow colour-2 ring with no underline, slot 2 is a hollow colour-9 ring with its underline lit. I read this as attempts or lives with the underline marking the live one and colour 2 marking a spent one, but that reading is a guess; the layout is not."
    [probe: pending]

  theorem three_cells_i_cannot_own "At frame 5 the cells (5,5),(5,6),(5,7) go 0 -> 9, and at frame 0 they are background, so no colour-keyed object owns them and none can: an arc-colour 0 object would claim all three thousand background cells. Symmetrically (5,1),(5,2),(5,3) and (2,6) end at background. Any future rule for ACTION5 therefore has a floor of 3 wrong cells. This is the arm's 70-of-73 figure and it is structural, not an oversight."
    [probe: pending]

  theorem socket_is_the_conjectured_goal "Rows 49-55, cols 43-49 hold a static 7x7 colour-9 outline, open on its left at col 43 rows 50-54, with a single dot at its centre (52,46). The donut is 5x5 with a hole at its centre. If the body enters at rows 50-54, cols 44-48 -- lattice cell (8,7) -- the dot lands exactly in the hole. That is a lock and a key and it is the only shape in the frame that fits the body. I have written NO goal section: every observed state is NOT_FINISHED, so I have zero evidence about winning, and this is geometry."
    [probe: pending]

  theorem i_cannot_write_the_goal_i_believe "Even granting the socket, `goal Glyph9.pos = socket_center` does not compile, because arc-instances: all means there is no instance named Glyph9 -- only Glyph9_r8c14 and its 36 siblings -- and there is no aggregate in the goal grammar that says 'some instance of this type is here'. count(Glyph9) = 37 is true of winning and losing states alike. So the manual has no goal and the planner cannot plan; that is a language limit I am recording, not a belief I am hiding."
    [probe: pending]

  theorem wire_and_gate "A static colour-8 structure runs from a 3x3 knob at rows 9-11, cols 39-41 (lattice cell (1,6)) down col 40 to row 40, then left along row 40 to a five-toothed comb filling rows 38-42, cols 14-18 -- lattice cell (6,2). Cols 14-18 is the only floor corridor running from spawn to the bottom room, and (6,2) is its one non-plain cell. So the comb is plausibly a gate, the knob plausibly its switch, and the cable is drawn between them. Nothing in five transitions tests this: no colour-8 cell has ever changed, which is why colour 8 is board and not an object."
    [probe: pending]

  theorem engines_gave_me_no_object_i_did_not_have "mdl_segmenter's own MDL is negative on both variants (-5042 and -17520 bits), so its segmentation loses to writing the pixels out; I take its tracks as hints only. Its obj3 is a 1006-cell colour-null blob that has swallowed the maze floor and the donut together and is not an object. zero_space returns THIN by its own verdict -- 5 transitions constrain rank 3 of 365 features -- and its single global law is a restatement of the 73-cell census, which I had already. No engine proposed anything I accepted as new."
    [probe: pending]
```

## The playbook as it stands

```
# playbook.dsl -- ordering for probes, not a route.
# The manual still cannot draw where the body lands, and it has no goal it can
# state, so anything resembling a route here would be a stored solution.
# Every line below is about which question to buy next with a metered action.

order     free_probes_before_metered_probes                   [proof: lean]
order     identify_each_key_direction_before_routing          [proof: lean]
order     resolve_gate_before_committing_to_left_corridor     [proof: lean]

prune     action_that_changed_nothing_in_this_lattice_cell => dead   [proof: lean]
prune     meter_exhausted and not goal => dead                [proof: lean]
prune     panel_slots_exhausted and not goal => dead          [proof: lean]

heuristic lattice_manhattan_to_socket                         [admissible: lean]
heuristic unexplained_cells_after_redraw                      [admissible: lean]

prefer    press_a_key_whose_direction_is_still_unknown        [ev: 2/5 levels]
prefer    probe_from_a_cell_where_two_readings_disagree       [ev: 1/1 levels]
prefer    descend_the_left_corridor                           [ev: 1/1 levels]
prefer    probe_the_knob_cell_along_the_open_top_band         [ev: 1/1 levels]
prefer    avoid_the_respawn_action_while_progress_exists      [ev: 1/1 levels]
prefer    untried_action_in_an_unvisited_lattice_cell         [ev: 2/5 levels]
```

## Why you are being called: the surprises that fired

### replay_mismatch (empirical family -> theory.dsl)

replay diverges at t=1 (frame_mismatch)

```json
{
 "arc_action": "ACTION2",
 "cells": [
  {
   "cell": [
    14,
    14
   ],
   "manual_says": 5,
   "world_says": 9
  },
  {
   "cell": [
    14,
    15
   ],
   "manual_says": 5,
   "world_says": 9
  },
  {
   "cell": [
    14,
    16
   ],
   "manual_says": 5,
   "world_says": 9
  },
  {
   "cell": [
    14,
    17
   ],
   "manual_says": 5,
   "world_says": 9
  },
  {
   "cell": [
    14,
    18
   ],
   "manual_says": 5,
   "world_says": 9
  },
  {
   "cell": [
    15,
    14
   ],
   "manual_says": 5,
   "world_says": 9
  },
  {
   "cell": [
    15,
    15
   ],
   "manual_says": 5,
   "world_says": 9
  },
  {
   "cell": [
    15,
    16
   ],
   "manual_says": 5,
   "world_says": 9
  },
  {
   "cell": [
    15,
    17
   ],
   "manual_says": 5,
   "world_says": 9
  },
  {
   "cell": [
    15,
    18
   ],
   "manual_says": 5,
   "world_says": 9
  },
  {
   "cell": [
    16,
    14
   ],
   "manual_says": 5,
   "world_says": 9
  },
  {
   "cell": [
    16,
    15
   ],
   "manual_says": 5,
   "world_says": 9
  },
  {
   "cell": [
    16,
    17
   ],
   "manual_says": 5,
   "world_says": 9
  },
  {
   "cell": [
    16,
    18
   ],
   "manual_says": 5,
   "world_says": 9
  },
  {
   "cell": [
    17,
    14
   ],
   "manual_says": 5,
   "world_says": 9
  },
  {
   "cell": [
    17,
    15
   ],
   "manual_says": 5,
   "world_says": 9
  },
  {
   "cell": [
    17,
    16
   ],
   "manual_says": 5,
   "world_says": 9
  },
  {
   "cell": [
    17,
    17
   ],
   "manual_says": 5,
   "world_says": 9
  },
  {
   "cell": [
    17,
    18
   ],
   "manual_says": 5,
   "world_says": 9
  },
  {
   "cell": [
    18,
    14
   ],
   "manual_says": 5,
   "world_says": 9
  },
  {
   "cell": [
    18,
    15
   ],
   "manual_says": 5,
   "world_says": 9
  },
  {
   "cell": [
    18,
    16
   ],
   "manual_says": 5,
   "world_says": 9
  },
  {
   "cell": [
    18,
    17
   ],
   "manual_says": 5,
   "world_says": 9
  },
  {
   "cell": [
    18,
    18
   ],
   "manual_says": 5,
   "world_says": 9
  }
 ],
 "cells_wrong": 24,
 "kind": "frame_mismatch",
 "t": 1
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
 "first_divergence": {
  "arc_action": "ACTION2",
  "cells": [
   {
    "cell": [
     14,
     14
    ],
    "manual_says": 5,
    "world_says": 9
   },
   {
    "cell": [
     14,
     15
    ],
    "manual_says": 5,
    "world_says": 9
   },
   {
    "cell": [
     14,
     16
    ],
    "manual_says": 5,
    "world_says": 9
   },
   {
    "cell": [
     14,
     17
    ],
    "manual_says": 5,
    "world_says": 9
   },
   {
    "cell": [
     14,
     18
    ],
    "manual_says": 5,
    "world_says": 9
   },
   {
    "cell": [
     15,
     14
    ],
    "manual_says": 5,
    "world_says": 9
   },
   {
    "cell": [
     15,
     15
    ],
    "manual_says": 5,
    "world_says": 9
   },
   {
    "cell": [
     15,
     16
    ],
    "manual_says": 5,
    "world_says": 9
   },
   {
    "cell": [
     15,
     17
    ],
    "manual_says": 5,
    "world_says": 9
   },
   {
    "cell": [
     15,
     18
    ],
    "manual_says": 5,
    "world_says": 9
   },
   {
    "cell": [
     16,
     14
    ],
    "manual_says": 5,
    "world_says": 9
   },
   {
    "cell": [
     16,
     15
    ],
    "manual_says": 5,
    "world_says": 9
   },
   {
    "cell": [
     16,
     17
    ],
    "manual_says": 5,
    "world_says": 9
   },
   {
    "cell": [
     16,
     18
    ],
    "manual_says": 5,
    "world_says": 9
   },
   {
    "cell": [
     17,
     14
    ],
    "manual_says": 5,
    "world_says": 9
   },
   {
    "cell": [
     17,
     15
    ],
    "manual_says": 5,
    "world_says": 9
   },
   {
    "cell": [
     17,
     16
    ],
    "manual_says": 5,
    "world_says": 9
   },
   {
    "cell": [
     17,
     17
    ],
    "manual_says": 5,
    "world_says": 9
   },
   {
    "cell": [
     17,
     18
    ],
    "manual_says": 5,
    "world_says": 9
   },
   {
    "cell": [
     18,
     14
    ],
    "manual_says": 5,
    "world_says": 9
   },
   {
    "cell": [
     18,
     15
    ],
    "manual_says": 5,
    "world_says": 9
   },
   {
    "cell": [
     18,
     16
    ],
    "manual_says": 5,
    "world_says": 9
   },
   {
    "cell": [
     18,
     17
    ],
    "manual_says": 5,
    "world_says": 9
   },
   {
    "cell": [
     18,
     18
    ],
    "manual_says": 5,
    "world_says": 9
   }
  ],
  "cells_wrong": 24,
  "kind": "frame_mismatch",
  "t": 1
 },
 "proof_layer_available": false,
 "replay": {
  "detail": "1/5 transitions replay exactly",
  "matched": 1,
  "ok": false,
  "transitions": 5
 },
 "responsibility": {
  "cells_unexplained": 0,
  "detail": "every pixel of frame 0 belongs to the board or to an object",
  "ok": true,
  "total_cells": 4096
 },
 "unambiguous": {
  "actions": 2,
  "clashes": [],
  "detail": "no (state, action) among 6 x 2 admitted two rules",
  "ok": true,
  "scope": "sampled",
  "states": 6
 }
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
# theory.dsl -- world observed for 9 commands (RESET + ACTION1..ACTION5,
# ACTION1..ACTION4). 75 cells in this world have ever changed and this manual
# names every one of them and owns 72 of the 72 that can be owned.
#
# What changed this round, and why:
#   1. THE MOVE IS NOW DRAWN. t7 (ACTION2, 48 cells, rows 8-18 cols 14-18) is
#      the twin of t2 and settles the reading: ACTION2 slides the 5x5 ring
#      DOWN exactly six pixels, and t5 slid it back up. I have taken the parse
#      risk the previous manual refused: cell terms are nested six deep, so a
#      floor cell whose sixth-above neighbour is body-coloured becomes
#      body-coloured. If the grammar does not nest, this manual does not
#      compile and that is a whole round lost -- I say so in
#      nested_cell_terms_are_the_bet_of_this_round. If it does nest, t2 and t7
#      replay to the pixel and the manual can, for the first time, carry the
#      body's position as state.
#   2. THE METER RULES ARE WITHDRAWN. They said ACTION2 and ACTION4 burn a
#      meter cell. t7 is an ACTION2 that burned nothing and t9 is an ACTION4
#      that burned nothing; t6 (ACTION1) and t8 (ACTION3) burned. The true
#      pattern is a clock, not a key, and the DSL has no step counter, so I
#      write no meter rule at all and take one wrong cell on four transitions.
#   3. THE ACTION MAP is now a named conjecture: 1=up, 2=down, 3=left,
#      4=right, 5=respawn. Only 2 is proven; the other four are the unique
#      assignment consistent with every no-op and with the panel burn at t5.

semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Glyph9  { pos: Coord, color: Int }   # arc-colour: 9  arc-instances: all
  object Vacated { pos: Coord, color: Int }   # arc-colour: 5  arc-instances: all
  object Spent   { pos: Coord, color: Int }   # arc-colour: 1  arc-instances: all
  landmark spawn_center    # arc-cell: (10, 16)
  landmark socket_center   # arc-cell: (52, 46)
  landmark gate_center     # arc-cell: (40, 16)
  landmark knob_center     # arc-cell: (10, 40)
  domain dir { up, down, left, right }
  Glyph9  [segment: dynamic_colour_9 ev: t0-t9 compress: 39]
  Vacated [segment: dynamic_colour_5 ev: t2,t5,t7 compress: 24]
  Spent   [segment: dynamic_colour_1 ev: t0-t9 compress: 9]

events:
  event moved(o, dir) | jumped(o, dest) | recolored(o, c) | vanished(o)

rules:
  rule key2_body_leaves forall ?p in Glyph9 [ev: t2,t7 cov: 48/48]
    when act=key(2) and colored(?p, 9) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule key2_body_arrives forall ?v in Vacated [ev: t2,t7 cov: 48/48]
    when act=key(2) and colored(?v, 5) and colored(above(above(above(above(above(above(?v)))))), 9) then recolored(?v, 9)

  rule key5_body_clears forall ?v in Vacated [ev: t5 cov: 24/24]
    when act=key(5) and colored(?v, 9) then recolored(?v, 5)

  rule key5_body_respawns forall ?p in Glyph9 [ev: t5 cov: 24/24]
    when act=key(5) and colored(?p, 5) and colored(above(?p), 5) then recolored(?p, 9)

goal:
  # deliberately empty -- see theorem i_still_cannot_write_the_goal_i_believe.
  # Every observed state is NOT_FINISHED, so I have zero evidence about
  # winning, and the goal I do believe is not sayable in this grammar.

laws:
  invariant nine_count_frame0 count(Glyph9) = 39 [status: counted]
  invariant five_count_frame0 count(Vacated) = 24 [status: counted]
  invariant one_count_frame0 count(Spent) = 9 [status: counted]
  invariant board_static count(board) = 4021 [status: counted]

  theorem dynamic_census "Exactly 75 cells have ever changed and I can name all of them. 23 are the status panel at rows 1-5, cols 1-7. 24 are a 5x5 ring of colour 9 at rows 8-12, cols 14-18, minus its hole (10,16) which never changes and is therefore board. 24 are the same shape one lattice cell down, rows 14-18, cols 14-18, minus its hole (16,16). 4 are the right end of the 64-cell bar on row 63, cols 60-63. 23+24+24+4 = 75, and nothing is left over. At frame 0 those 75 split as 39 colour-9 cells (8 panel ring + 3 panel underline + 24 ring + 4 meter), 9 colour-1 cells (the solid slot-2 block), 24 colour-5 cells (the lower ring's footprint) and 3 background cells ((5,5),(5,6),(5,7)); 39+9+24 = 72, which is exactly the arm's cells_needing_an_owner."
    [probe: pending]

  theorem the_body_is_a_ring_on_a_six_pixel_lattice "The mover is a 5x5 hollow ring of colour 9 whose top-left sits at (6R+2, 6C+2). It has been seen at (R,C) = (1,2), rows 8-12, and (R,C) = (2,2), rows 14-18, and one command displaces it exactly six pixels. The maze agrees that six is the module: void columns run cols 20-24 and cols 32-36 with single floor columns at 19, 25 and 31, and the socket's interior is rows 50-54, cols 44-48, which is lattice (8,7). The ring's hole is at its centre, (6R+4, 6C+4)."
    [depends: key2_body_leaves, key2_body_arrives  probe: pending]

  theorem nested_cell_terms_are_the_bet_of_this_round "The published cell grammar is 'above(x) below(x) leftof(x) rightof(x)' and does not say whether x may itself be a cell term. Six-deep nesting is the only way this grammar can say 'six pixels away', and six pixels is the largest single compression in the world -- one line of guard draws 24 pixels and does it at any position the arm has instances for, not just the observed one. So I have spent the manual on it. If it does not parse, nothing compiles; the fallback I would write next round is one landmark per lattice cell plus one rule per landmark, which is coordinates in disguise, generalises to nothing, and is what I am trying to avoid."
    [depends: key2_body_leaves, key2_body_arrives  probe: pending]

  theorem the_two_key2_rules_i_am_not_yet_allowed_to_write "The arm types cells by their frame-0 colour, so the body's own cells change type as it moves: the ring at rows 8-12 is Glyph9 and the ring at rows 14-18 is Vacated. Every movement law therefore needs four rules -- leave-a-9-cell, arrive-at-a-5-cell, leave-a-5-cell, arrive-at-a-9-cell -- and for ACTION2 I have witnesses for only the first two. The missing pair, verbatim: 'rule key2_floor_leaves forall ?v in Vacated when act=key(2) and colored(?v, 9) and colored(below(below(below(below(below(below(?v)))))), 5) then recolored(?v, 5)' and 'rule key2_body_arrives_at_nine forall ?p in Glyph9 when act=key(2) and colored(?p, 5) and colored(above(above(above(above(above(above(?p)))))), 9) then recolored(?p, 9)'. Until a second consecutive ACTION2 witnesses them I refuse to write them, and I state the cost plainly: on that command my manual will draw the body in two places at once and lose about 24 cells. That mismatch IS the probe."
    [depends: key2_body_leaves, key2_body_arrives  probe: pending]

  theorem the_action_map "ACTION2 is down: proven twice, t2 and t7, six pixels each. The rest is the unique assignment consistent with every observation. ACTION1 did nothing at t1 and t6, both from rows 8-12, where six above is rows 2-6, off the floor. ACTION3 did nothing at t3 and t8, both from rows 14-18, where six left is cols 8-12, off the floor. ACTION4 did nothing at t4 and t9, both from rows 14-18, where six right is cols 20-24, interior void. So 1=up, 3=left, 4=right all fit as blocked moves, and no other assignment explains all six no-ops. ACTION5 is respawn: at t5 it returned the body to spawn AND flipped the panel to its second slot, which is a life being consumed, and no direction key has ever touched the panel. Separator, and it is cheap: from rows 14-18 the cell above IS floor, so pressing ACTION1 here must move the body up if 1=up, and must do nothing if it is anything else."
    [depends: key2_body_leaves, key5_body_respawns  probe: pending]

  theorem the_meter_is_a_clock_and_the_dsl_has_no_counter "Row 63 is a 64-cell colour-9 bar that loses its rightmost live cell to colour 1. Burns: t2 (63,63), t4 (63,62), t6 (63,61), t8 (63,60). No burns: t1, t3, t5, t7, t9. That is 4/4 on even-numbered commands and 5/5 on odd, and it cuts clean across the actions -- ACTION2 burned at t2 and not at t7, ACTION4 burned at t4 and not at t9, ACTION1 burned at t6 but not at t1, ACTION3 burned at t8 but not at t3. Equivalently: the bar loses one cell every second command, and equivalently again, it burns exactly when the number already burned is even. Every one of these readings needs a counter over commands, and the guard language has no state that is not a cell. I therefore write NO meter rule, which predicts 'the bar never burns' and is wrong by exactly one cell on four of nine transitions -- I take that over the alternative rule 'burn on every command', which would be wrong by one cell on five of nine and would also empty the bar four times too fast for any planning that reads it as a budget."
    [probe: pending]

  theorem the_meter_rules_i_withdrew "The previous manual carried meter_burn_key2 and meter_burn_key4, on one observation each. t7 refuted the first (an ACTION2 with no burn) and t9 refuted the second (an ACTION4 with no burn); worse, meter_burn_key4's guard 'right neighbour already spent' now grounds on (63,59) and would invent a fifth burn. Both are deleted, and the lesson is written down: one observation per action is not evidence for a rule keyed on the action when a clock explains the same pixels."
    [probe: pending]

  theorem the_panel_debt_i_am_choosing_to_carry "The panel is two 3x3 icon slots at rows 1-3, cols 1-3 and cols 5-7, each with a 1x3 underline at row 5. Frames 0-4: slot 1 is a hollow colour-9 ring with its underline lit; slot 2 is a solid colour-1 block, underline dark. Frame 5 onward: slot 1 is a hollow colour-2 ring, underline dark; slot 2 is a hollow colour-9 ring, underline lit. I read it as two lives with the lit underline marking the live one and colour 2 marking a spent one. I have written no rule for it and every ACTION5 therefore costs me 23 wrong cells. The reason is rule 3 and rule 5, not laziness: separating the slot-1 ring from the slot-1 underline is impossible with four-neighbour colour guards -- (1,2) and (5,2) have byte-identical neighbourhoods -- and separating the slot-2 ring from its centre needs a disjunction the guard language does not have (there is no `or`), so the honest encoding is four rules that all fire on a corner cell, which is exactly the ambiguity rule 5 forbids. 23 wrong cells on a command I intend never to press again is cheaper than that."
    [probe: pending]

  theorem three_cells_no_object_can_ever_own "(5,5), (5,6), (5,7) are background at frame 0 and colour 9 from frame 5, so no colour-keyed object owns them and none can: an arc-colour 0 object would claim three thousand background cells. Any future panel rule has a floor of 3 wrong cells. This is the gap between the arm's 75 dynamic cells and its 72 cells_needing_an_owner, and it is structural."
    [probe: pending]

  theorem key5_is_respawn_and_i_have_written_it_as_respawn "key5_body_clears and key5_body_respawns together say: on ACTION5 any floor cell that is body-coloured goes back to floor, and the spawn ring lights up. That is respawn-from-anywhere, and it fits t5 exactly (24/24 both halves). The rival reading, 'ACTION5 is up', fits t5 exactly too, because at t5 the body happened to be one lattice cell below spawn. I chose respawn because ACTION5 is the only command that has ever touched the panel and because 1-4 already exhaust the four directions. The separator is one command: press ACTION5 from a cell that is NOT one lattice cell below spawn. If the body lands at spawn, respawn; if it moves up one cell, my two rules are wrong and become an up-rule."
    [depends: key5_body_clears, key5_body_respawns  probe: pending]

  theorem the_socket_is_the_conjectured_lock "Rows 49-55, cols 43-49 hold a static colour-9 outline, open on the left at col 43 for rows 50-54, with a single dot at its centre (52,46). Its interior, rows 50-54 cols 44-48, is lattice cell (8,7), and the body is a 5x5 ring with its hole at the centre -- so a body parked there puts the dot exactly in the hole and covers not one pixel of it. That is a lock and a key, and it is the only shape in the frame that fits the body. It also means the win leaves NO colour signature I can test: the 24 arriving cells go 5 to 9 like any other move and the dot never changes."
    [probe: pending]

  theorem i_still_cannot_write_the_goal_i_believe "arc-instances: all means there is no instance named Glyph9 or Vacated, only Glyph9_r8c14 and 38 siblings, and the goal grammar offers only `<instance>.pos = <landmark>` and `count(Type, color = k) = n`. There is no aggregate that says 'some instance of this type sits at socket_center'. count(Vacated, color = 9) = 24 is true of the body standing anywhere off spawn, not of the body standing in the socket. So the goal section is empty, is_goal is False, and the planner cannot plan a win; the playbook has to steer by distance instead. This is a language limit I am recording, not a belief I am hiding."
    [depends: the_socket_is_the_conjectured_lock  probe: pending]

  theorem the_only_route_down_and_the_gate_across_it "Cols 14-18 is the sole corridor from spawn to the bottom room; it is floor at lattice rows R=1..5 and R=7..8 and it is blocked at R=6 by a five-toothed colour-8 comb filling rows 38-42, cols 14-18. A colour-8 cable leaves that comb along row 40, runs right to col 40 and up col 40 to a 3x3 colour-8 knob at rows 9-11, cols 39-41 -- lattice (1,6), the same lattice row as spawn. So the comb is plausibly a gate and the knob plausibly its switch. No colour-8 cell has changed in nine commands, which is why 8 is board and not an object. My rules make a falsifiable prediction here: key2_body_leaves needs the destination to render colour 5, and the comb renders 8, so my manual says the body stops at R=5 and nothing happens. If it walks through, the gate is open and I learn that in one command."
    [depends: key2_body_leaves  probe: pending]

  theorem what_the_engines_gave_me "mdl_segmenter's MDL is negative on both variants (-4457 and -22984 bits), so its own segmentation loses to writing the pixels out; obj3 is a 1006-cell colour-null blob that has swallowed the maze floor, which is not an object but is a fair description of my `board`. Its obj0/obj2/obj4 are colour-9 fragments already inside Glyph9, and obj5 is the colour-2 panel ring, which is Glyph9 cells after a recolour and needs no type of its own -- I dropped the Glyph2 declaration the previous manual carried, because at frame 0 there is no colour-2 cell for it to own and a second type on the same pixels invites a double claim. zero_space self-reports THIN (9 transitions constrain rank 6 of 375 features) and its one global law restates the 75-cell census I already had. cegis_miner's refusal is the most useful thing any engine said: 'no track satisfies the precondition of exactly one move event per transition; the world does not narrate as one mover'. That is correct and it is a fact about the ARM, not the world -- the world has exactly one mover, a 24-cell rigid ring, and the arm can only see 24 recolours."
    [probe: pending]
```

=== PLAYBOOK ===
```
# playbook.dsl -- what to buy with the next command, not a route.
# The manual can now carry the body's position, but it has no goal it can
# state, so nothing here may name a sequence. Every line is a criterion on the
# current frame plus the manual's own open questions.

order     confirm_a_key_direction_before_relying_on_it            [proof: lean]
order     descend_the_only_corridor_before_testing_the_gate       [proof: lean]
order     resolve_gate_passability_before_planning_the_bottom_room [proof: lean]
order     free_probes_before_life_costing_probes                  [proof: lean]

prune     action_that_was_a_no_op_from_this_lattice_cell => dead   [proof: lean]
prune     respawn_while_the_body_still_has_a_legal_move => dead    [proof: lean]
prune     destination_lattice_cell_is_not_floor => dead            [proof: lean]
prune     meter_exhausted and not goal => dead                     [proof: lean]
prune     panel_slots_exhausted and not goal => dead               [proof: lean]

heuristic lattice_manhattan_to_socket_interior                     [admissible: lean]
heuristic unexplained_cells_after_redraw                           [admissible: lean]
heuristic meter_cells_still_lit                                    [admissible: lean]

prefer    a_step_that_both_advances_and_witnesses_an_unwritten_rule [ev: 1/1 levels]
prefer    step_toward_the_socket_when_the_destination_reads_floor   [ev: 2/2 moves]
prefer    press_a_direction_key_from_a_cell_where_it_is_unblocked   [ev: 6/6 no_ops]
prefer    stay_in_the_corridor_that_reaches_the_socket              [ev: 1/1 levels]
prefer    probe_the_knob_only_if_the_gate_refuses_the_body          [ev: 1/1 levels]
prefer    untried_action_in_an_unvisited_lattice_cell               [ev: 2/5 levels]
```

=== LOG ===
```json
[
  {"id": "O-01", "subject": "mdl_segmenter obj0/obj2/obj4 (colour 9, 8+3+64 cells)", "verdict": "accept",
   "as": "Glyph9 (arc-colour 9, arc-instances all, 39 frame-0 instances)",
   "why": "the three colour-9 tracks are the panel ring, the panel underline and the row-63 bar; one type keyed on colour 9 owns all of them plus the spawn ring, because the arm can only look objects up by colour and cannot tell them apart anyway."},
  {"id": "O-02", "subject": "the 24 floor cells at rows 14-18 cols 14-18 that no engine tracked", "verdict": "accept",
   "as": "Vacated (arc-colour 5, arc-instances all, 24 instances)",
   "why": "they are the only colour-5 cells the board cannot explain, they are exactly the cells the ring's second position occupies, and without them there is no instance for the body to be drawn on after a move."},
  {"id": "O-03", "subject": "mdl_segmenter obj1 (colour 1, 9 cells, frames_present 5)", "verdict": "accept",
   "as": "Spent (arc-colour 1, 9 instances)",
   "why": "the solid 3x3 block in panel slot 2 at frame 0; it must be owned or its 9 pixels are unexplained, and its 5-frame lifetime is exactly the panel flip at t5."},
  {"id": "O-04", "subject": "mdl_segmenter obj5 (colour 2, first_frame 5, 8 cells)", "verdict": "reject",
   "as": null,
   "why": "colour 2 does not exist at frame 0, so a colour-2 type owns nothing and risks a second claim on the eight slot-1 ring cells that Glyph9 already owns; the previous manual's Glyph2 declaration is deleted."},
  {"id": "O-05", "subject": "mdl_segmenter obj3 (colour null, 1006 cells, 50x38)", "verdict": "reject",
   "as": null,
   "why": "it is the maze floor with the ring swallowed into it; it never varies, so it is board, and the engine's own MDL is negative (-4457 bits) on the segmentation that produced it."},
  {"id": "R-01", "subject": "key2_body_leaves", "verdict": "accept",
   "why": "t2 and t7 are the same command from the same lattice cell and both vacate the same 24 colour-9 cells, 48/48; the guard 'the cell six below renders floor' excludes every panel cell (six below is background) and every meter cell (six below is wall) with no coordinates."},
  {"id": "R-02", "subject": "key2_body_arrives", "verdict": "accept",
   "why": "the mirror half, 48/48 over t2 and t7; it leaves the ring's hole alone for the right reason, because the cell six above (16,16) is (10,16), the hole of the source ring, which renders floor and not 9."},
  {"id": "R-03", "subject": "key5_body_clears", "verdict": "accept",
   "why": "24/24 at t5; any floor cell showing body colour returns to floor on ACTION5, which is the half of respawn that needs no assumption about where the body was."},
  {"id": "R-04", "subject": "key5_body_respawns", "verdict": "accept",
   "why": "24/24 at t5 with a guard ('I am floor and the cell above me is floor') that picks the spawn ring and nothing else at that frame, and that keeps working from any body position, unlike the 'six below is body-coloured' guard which would only work from one cell below spawn."},
  {"id": "R-05", "subject": "meter_burn_key2 (carried in the previous manual)", "verdict": "reject",
   "why": "t7 is an ACTION2 that burned no meter cell; the rule is refuted by direct observation and is deleted."},
  {"id": "R-06", "subject": "meter_burn_key4 (carried in the previous manual)", "verdict": "reject",
   "why": "t9 is an ACTION4 that burned no meter cell, and with cols 60-63 already spent the rule's guard now grounds on (63,59) and would invent a burn that never happened."},
  {"id": "R-07", "subject": "key2_vacates_body (carried in the previous manual)", "verdict": "accept",
   "as": "superseded by key2_body_leaves",
   "why": "its four-neighbour guard was a property of the floor around the ring, not of the ring; the new destination-is-floor guard covers the same 24 cells, survives the body standing next to void, and doubles as the legality test for the move."},
  {"id": "R-08", "subject": "key2_floor_leaves (the ring vacating a Vacated-typed cell)", "verdict": "probe-pending",
   "why": "no transition witnesses ACTION2 leaving rows 14-18; writing it now would be a rule with cov 0/0, so the exact text sits in theorem the_two_key2_rules_i_am_not_yet_allowed_to_write and the next consecutive ACTION2 buys it."},
  {"id": "R-09", "subject": "key2_body_arrives_at_nine (the ring arriving on a Glyph9-typed cell)", "verdict": "probe-pending",
   "why": "same gap, same probe; together R-08 and R-09 mean the next ACTION2 from rows 14-18 will draw the body twice, and I state that cost in the manual rather than hide it."},
  {"id": "L-01", "subject": "cegis_miner verdict 'the world does not narrate as one mover'", "verdict": "accept",
   "why": "correct about the arm and wrong about the world: the mover is one rigid 24-cell ring, and the arm can only report 24 simultaneous recolours, which is why no track has exactly one move event per transition."},
  {"id": "L-02", "subject": "zero_space global law over the 75 dynamic cells", "verdict": "entailed",
   "why": "it restates the census already in theorem dynamic_census, and the engine's own adequacy verdict is THIN (9 transitions, rank 6 of 375 features), so it is a correlation, not a conservation law."},
  {"id": "L-03", "subject": "meter parity: burns at t2,t4,t6,t8 and never at t1,t3,t5,t7,t9", "verdict": "probe-pending",
   "why": "9/9 as a clock at half rate and 0/9 as anything keyed on the action; recorded as theorem the_meter_is_a_clock_and_the_dsl_has_no_counter and testable by any single command, since the parity says the next one must burn."},
  {"id": "L-04", "subject": "1=up 2=down 3=left 4=right 5=respawn", "verdict": "probe-pending",
   "why": "only 2 is proven; the other four are the unique assignment that makes all six no-ops blocked moves, and the separator is one free press of ACTION1 from rows 14-18, where the cell above is floor."},
  {"id": "E-01", "subject": "a step counter, needed for the meter clock", "verdict": "probe-pending",
   "why": "I wanted 'burn the head of the bar every second command'; the guard language has no state that is not a cell and no parity, so I wrote no meter rule and accepted one wrong cell on four of nine transitions."},
  {"id": "E-02", "subject": "the winning condition", "verdict": "probe-pending",
   "why": "I wanted 'some instance of the body type sits at socket_center'; with arc-instances: all there is no instance named for the type and no aggregate for 'some', so the goal section is empty and the playbook steers by lattice distance instead."},
  {"id": "E-03", "subject": "a six-pixel displacement of a 24-cell rigid body", "verdict": "accept",
   "as": "six-deep nested cell terms in two guards",
   "why": "moved is one cell and jumped is two, so the displacement is inexpressible as an event; I expressed it as a relation between the source and destination cell instead, and that bet is the one thing in this manual that can cost the whole round if the grammar does not nest."},
  {"id": "E-04", "subject": "disjunction in guards, needed for the panel", "verdict": "reject",
   "why": "separating the slot-2 ring from its centre needs 'a neighbour is background', which without `or` becomes four rules that all fire on a corner cell -- exactly the ambiguity constraint 5 forbids -- so I left the panel undrawn and named the 23-cell debt."},
  {"id": "P-01", "subject": "second consecutive ACTION2 from rows 14-18", "verdict": "probe-pending",
   "why": "it advances toward the socket, and it simultaneously witnesses R-08 and R-09 and tests whether the corridor at lattice R=3 accepts the body; the mismatch it produces is the cheapest one available."},
  {"id": "P-02", "subject": "ACTION1 from rows 14-18", "verdict": "probe-pending",
   "why": "the cell above is spawn floor, so this is the one position where 1=up makes a visible prediction; it settles L-04 without spending a life."},
  {"id": "P-03", "subject": "ACTION2 pressed from lattice row R=5, one cell above the colour-8 comb", "verdict": "probe-pending",
   "why": "my rules predict the body stops, because the destination renders 8 and not 5; if it walks through, the gate is decorative and the knob at (10,40) can be dropped from the plan."}
]
```
```
