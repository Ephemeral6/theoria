# call-002-theorize-round1

model: `claude-opus-5` · 513761 ms · $1.253450 · usage {"cache_creation": {"ephemeral_1h_input_tokens": 23899, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 23899, "cache_read_input_tokens": 0, "inference_geo": "not_available", "input_tokens": 2, "iterations": [{"cache_creation": {"ephemeral_1h_input_tokens": 23899, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 23899, "cache_read_input_tokens": 0, "input_tokens": 2, "output_tokens": 39874, "type": "message"}], "output_tokens": 39874, "server_tool_use": {"web_fetch_requests": 0, "web_search_requests": 0}, "service_tier": "standard", "speed": "standard"}

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
 "cells_needing_an_owner": 70,
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
    "ms": 34,
    "script_bits": 7018,
    "split_by_color": false,
    "tracks": 6
   },
   {
    "baseline_bits": 1976,
    "compression_ratio": 9.866397,
    "events": 19,
    "gain_bits": -17520,
    "ms": 23,
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
  "cells_needing_an_owner": 70,
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
     "c2@39
```

The full proposal stream is 736 rows in `candidates.jsonl`.

## The manual as it stands

```
# theory.dsl -- world observed for 5 transitions (RESET + ACTION1..ACTION5).
# The whole dynamic budget of this world is 73 cells and this manual accounts
# for every one of them. What it CANNOT do is move them: the only mover is a
# 24-cell rigid body that displaces six pixels at a time, and neither
# `moved` (one cell) nor `jumped` (one named cell, one instance) can say that.
# So this manual is deliberately rule-free. It names the world correctly and
# it lies about nothing; the dynamics live in `laws:` as probes.

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
  landmark meter_head      # arc-cell: (63, 61)
  domain dir { up, down, left, right }
  Glyph9  [segment: dynamic_colour_9 ev: t0-t5 compress: 35]
  Glyph2  [segment: dynamic_colour_2 ev: t5 compress: 8]
  Spent   [segment: dynamic_colour_1 ev: t2,t4 compress: 2]
  Vacated [segment: dynamic_colour_5 ev: t2,t5 compress: 24]

events:
  event moved(o, dir) | jumped(o, dest) | recolored(o, c) | vanished(o)

laws:
  invariant nine_count count(Glyph9) = 35 [status: observed]
  invariant board_static count(board) = 4023 [status: observed]

  theorem dynamic_census "Exactly 73 cells ever change and I can name all of them: 48 are the two occupied squares of a 5x5 body of colour 9 at rows 8-12 and rows 14-18, cols 14-18, minus its two centre cells (10,16) and (16,16) which are constant floor because the body is a donut with a one-pixel hole; 23 are a status panel at rows 1-5, cols 1-7; 2 are the right end of a 64-cell bar on row 63. 48+23+2 = 73, which closes the budget with nothing left over."
    [probe: pending]

  theorem panel_layout "The panel is two 3x3 icon slots, cols 1-3 and cols 5-7 of rows 1-3, each with a 1x3 underline at row 5. Cell (2,2) never varies and is background, so slot 1 is hollow in every frame; (2,6) does vary, so slot 2 was solid and became hollow. At frames 0-4: slot 1 = hollow colour 9 with the underline beneath it, slot 2 = solid colour 1, no underline. At frame 5: slot 1 = hollow colour 2, no underline, slot 2 = hollow colour 9 with the underline beneath it. I read this as two attempts or two lives with the underline marking the live one, but that reading is a guess; the layout is not."
    [probe: pending]

  theorem lattice_step "Both observed body positions have their top-left corner at (6R+2, 6C+2) -- rows 8-12 is R=1, rows 14-18 is R=2, cols 14-18 is C=2 -- and both observed displacements are exactly six pixels, never one. The maze walls agree: the void columns run cols 20-24 and cols 32-36 with single floor columns 19, 25, 31 between them. So this is a coarse grid of 6-pixel cells and one action moves the body one coarse cell. This is the largest compression available in the world and it is the one thing the rule language cannot state."
    [probe: pending]

  theorem key2_steps_down "ACTION2 at t2 displaced the body from rows 8-12 to rows 14-18, one lattice cell down. 49 cells changed = 24 vacated + 24 occupied + one meter cell, which is the exact arithmetic of a pure vertical slide of a donut whose hole keeps its column. Coverage 1/1: it is the only ACTION2 observed."
    [probe: pending]

  theorem key1_key3_are_noops_here "ACTION1 (t1) and ACTION3 (t3) changed not one pixel and did not touch the meter. Both are consistent with up and left being refused at the body's position: above rows 8-12 the grid is background, and left of cols 14-18 the grid is background past col 13. This manual encodes them by having no rule -- absence of a rule is the prediction 'nothing happens', and that prediction is correct on 2 of 5 transitions."
    [probe: pending]

  theorem key4_burned_a_meter_cell_without_moving "ACTION4 (t4) changed exactly one cell, (63,62) from 9 to 1, and moved nothing. ACTION2 also burned one, (63,63). ACTION5 burned none. So the row-63 bar depletes from the right end leftward, and it is charged by some actions and not others; a blocked move that costs nothing (t1, t3) and a blocked move that costs one (t4) are both in the record, and I cannot yet separate them. The candidate separator: at t4 the destination lattice cell (rows 14-18, cols 20-24) is interior void, while at t1 and t3 the destination is off the play area entirely."
    [probe: pending]

  theorem key5_returns_body_to_spawn "ACTION5 (t5) changed 71 cells = 48 for the body going from rows 14-18 back to rows 8-12, plus 23 for the whole panel flipping to its second configuration. It burned no meter cell. The body ends exactly where it started at t0, so I read ACTION5 as a respawn or attempt-reset rather than as the direction 'up', and the panel flip as that attempt being consumed. Both readings are unforced: a plain 'up' plus an unrelated panel tick fits the same pixels."
    [probe: pending]

  theorem cascade_is_animation "ACTION2 returned 7 frames and ACTION5 returned 9, while the two no-ops returned 1. Seven frames is exactly a six-pixel slide drawn one pixel per frame plus the settled frame. Only the last frame of a command is kept as a state, so the six-pixel step is atomic for prediction purposes and the intermediate frames carry no extra state."
    [probe: pending]

  theorem socket_is_the_conjectured_goal "Rows 49-55, cols 43-49 hold a static 7x7 outline of colour 9 that is open on its left side (col 43 is floor at rows 50-54) and carries a single dot at its centre (52,46). The body is 5x5 with a hole at its centre. If the body enters at rows 50-54, cols 44-48 -- lattice cell (8,7) -- the dot lands exactly in the hole. That is a lock and a key, and it is the only shape in the frame that fits the body. I have written NO goal section, because the world has reported NOT_FINISHED for every state and I have no evidence about winning at all; this is geometry, not a win condition."
    [probe: pending]

  theorem wire_and_gate "A static colour-8 structure runs from a 3x3 knob at rows 9-11, cols 39-41 (inside lattice cell (1,6)) down col 40 to row 40, then left along row 40 to a five-toothed comb filling rows 38-42, cols 14-18 -- which is lattice cell (6,2). The left corridor, cols 14-18, is the only column of floor that runs from the body's spawn down to the bottom room, and cell (6,2) is the one cell of it that is not plain floor. So the comb is plausibly a gate and the knob plausibly its switch, joined by the drawn cable. Nothing in five transitions tests this: the colour-8 cells have never changed."
    [probe: pending]

  theorem same_colour_conflation "Glyph9 is one type because the arm finds objects by colour and nothing else, so its instances are the 24 body cells AND the 8 panel-ring cells AND the 3 underline cells together. They are three different things and I believe they obey three different laws. Any future rule over `forall ?p in Glyph9` must carry a guard that isolates the body; the guard `not colored(above(?p), 0) and not colored(below(?p), 0) and not colored(leftof(?p), 0)` does exactly that in the current frame and in no way that I have proven will survive the body moving."
    [probe: pending]

  theorem four_cells_left_to_the_background "Four dynamic cells show background in the current frame -- (2,6), the hollowed centre of slot 2, and (5,1),(5,2),(5,3), the vacated underline -- and no colour-keyed object can own a background cell without owning all 3000 of them. I leave them to the background and say so rather than declare an arc-colour 0 object. At frame 0 the corresponding uncovered set is (5,5),(5,6),(5,7), which is the arm's count of 70 cells needing an owner out of 73 dynamic."
    [probe: pending]

  theorem no_rules_is_a_defect_not_a_position "This manual compiles to a predictor that says 'nothing ever changes'. That is right for t1 and t3 and wrong for t2, t4 and t5, costing about 48 cells on each of three frames. It is deliberate: the true transition is a rigid six-pixel displacement of a 24-instance body, `moved` moves one cell, `jumped` moves one instance to one landmark, and writing 24 landmarks and 24 jump rules per observed step would be a stored solution rather than a law. I would rather carry a known 3-frame drawing defect than a rule I know to be false."
    [probe: pending]
```

## The playbook as it stands

```
# playbook.dsl -- what to do with a manual that cannot yet predict.
# Every line below is about ordering probes, not about a route: after five
# transitions the only route I could write down would be a stored solution.

order     resolve_gate_before_committing_to_left_corridor   [proof: lean]
order     free_probes_before_metered_probes                 [proof: lean]

prune     action_that_changed_nothing_in_this_lattice_cell => dead   [proof: lean]
prune     panel_slots_exhausted and not goal => dead        [proof: lean]

heuristic lattice_manhattan_to_socket                       [admissible: lean]
heuristic unexplained_cells_after_redraw                    [admissible: lean]

prefer    probe_the_knob_cell_along_the_open_top_band       [ev: 1/1 levels]
prefer    descend_the_left_corridor                         [ev: 1/1 levels]
prefer    avoid_the_respawn_action_while_progress_exists    [ev: 1/1 levels]
prefer    untried_action_in_an_unvisited_lattice_cell       [ev: 2/5 levels]
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
    8,
    14
   ],
   "manual_says": 9,
   "world_says": 5
  },
  {
   "cell": [
    8,
    15
   ],
   "manual_says": 9,
   "world_says": 5
  },
  {
   "cell": [
    8,
    16
   ],
   "manual_says": 9,
   "world_says": 5
  },
  {
   "cell": [
    8,
    17
   ],
   "manual_says": 9,
   "world_says": 5
  },
  {
   "cell": [
    8,
    18
   ],
   "manual_says": 9,
   "world_says": 5
  },
  {
   "cell": [
    9,
    14
   ],
   "manual_says": 9,
   "world_says": 5
  },
  {
   "cell": [
    9,
    15
   ],
   "manual_says": 9,
   "world_says": 5
  },
  {
   "cell": [
    9,
    16
   ],
   "manual_says": 9,
   "world_says": 5
  },
  {
   "cell": [
    9,
    17
   ],
   "manual_says": 9,
   "world_says": 5
  },
  {
   "cell": [
    9,
    18
   ],
   "manual_says": 9,
   "world_says": 5
  },
  {
   "cell": [
    10,
    14
   ],
   "manual_says": 9,
   "world_says": 5
  },
  {
   "cell": [
    10,
    15
   ],
   "manual_says": 9,
   "world_says": 5
  },
  {
   "cell": [
    10,
    17
   ],
   "manual_says": 9,
   "world_says": 5
  },
  {
   "cell": [
    10,
    18
   ],
   "manual_says": 9,
   "world_says": 5
  },
  {
   "cell": [
    11,
    14
   ],
   "manual_says": 9,
   "world_says": 5
  },
  {
   "cell": [
    11,
    15
   ],
   "manual_says": 9,
   "world_says": 5
  },
  {
   "cell": [
    11,
    16
   ],
   "manual_says": 9,
   "world_says": 5
  },
  {
   "cell": [
    11,
    17
   ],
   "manual_says": 9,
   "world_says": 5
  },
  {
   "cell": [
    11,
    18
   ],
   "manual_says": 9,
   "world_says": 5
  },
  {
   "cell": [
    12,
    14
   ],
   "manual_says": 9,
   "world_says": 5
  },
  {
   "cell": [
    12,
    15
   ],
   "manual_says": 9,
   "world_says": 5
  },
  {
   "cell": [
    12,
    16
   ],
   "manual_says": 9,
   "world_says": 5
  },
  {
   "cell": [
    12,
    17
   ],
   "manual_says": 9,
   "world_says": 5
  },
  {
   "cell": [
    12,
    18
   ],
   "manual_says": 9,
   "world_says": 5
  }
 ],
 "cells_wrong": 49,
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
     8,
     14
    ],
    "manual_says": 9,
    "world_says": 5
   },
   {
    "cell": [
     8,
     15
    ],
    "manual_says": 9,
    "world_says": 5
   },
   {
    "cell": [
     8,
     16
    ],
    "manual_says": 9,
    "world_says": 5
   },
   {
    "cell": [
     8,
     17
    ],
    "manual_says": 9,
    "world_says": 5
   },
   {
    "cell": [
     8,
     18
    ],
    "manual_says": 9,
    "world_says": 5
   },
   {
    "cell": [
     9,
     14
    ],
    "manual_says": 9,
    "world_says": 5
   },
   {
    "cell": [
     9,
     15
    ],
    "manual_says": 9,
    "world_says": 5
   },
   {
    "cell": [
     9,
     16
    ],
    "manual_says": 9,
    "world_says": 5
   },
   {
    "cell": [
     9,
     17
    ],
    "manual_says": 9,
    "world_says": 5
   },
   {
    "cell": [
     9,
     18
    ],
    "manual_says": 9,
    "world_says": 5
   },
   {
    "cell": [
     10,
     14
    ],
    "manual_says": 9,
    "world_says": 5
   },
   {
    "cell": [
     10,
     15
    ],
    "manual_says": 9,
    "world_says": 5
   },
   {
    "cell": [
     10,
     17
    ],
    "manual_says": 9,
    "world_says": 5
   },
   {
    "cell": [
     10,
     18
    ],
    "manual_says": 9,
    "world_says": 5
   },
   {
    "cell": [
     11,
     14
    ],
    "manual_says": 9,
    "world_says": 5
   },
   {
    "cell": [
     11,
     15
    ],
    "manual_says": 9,
    "world_says": 5
   },
   {
    "cell": [
     11,
     16
    ],
    "manual_says": 9,
    "world_says": 5
   },
   {
    "cell": [
     11,
     17
    ],
    "manual_says": 9,
    "world_says": 5
   },
   {
    "cell": [
     11,
     18
    ],
    "manual_says": 9,
    "world_says": 5
   },
   {
    "cell": [
     12,
     14
    ],
    "manual_says": 9,
    "world_says": 5
   },
   {
    "cell": [
     12,
     15
    ],
    "manual_says": 9,
    "world_says": 5
   },
   {
    "cell": [
     12,
     16
    ],
    "manual_says": 9,
    "world_says": 5
   },
   {
    "cell": [
     12,
     17
    ],
    "manual_says": 9,
    "world_says": 5
   },
   {
    "cell": [
     12,
     18
    ],
    "manual_says": 9,
    "world_says": 5
   }
  ],
  "cells_wrong": 49,
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
  "actions": 0,
  "detail": "the manual declares no actions, so no pair of rules can claim one object",
  "ok": true,
  "scope": "sampled",
  "states": 0
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

=== PLAYBOOK ===
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

=== LOG ===
```json
[
  {"id": "O-01", "subject": "mdl_segmenter obj0 (colour 9, 8 cells, 3x3, all 6 frames)", "verdict": "accept",
   "as": "Glyph9 instances at rows 1-3 cols 1-3 (panel slot 1 ring)",
   "why": "a hollow 3x3 of colour 9 present in every frame and changing colour at frame 5 is the panel ring; it is colour 9 so the arm cannot separate it from the body, and it is folded into Glyph9 with arc-instances: all."},

  {"id": "O-02", "subject": "mdl_segmenter obj1 (colour 1, 9 cells, 3x3, 5 of 6 frames)", "verdict": "accept",
   "as": "Spent",
   "why": "a solid 3x3 of colour 1 at rows 1-3 cols 5-7 that is present frames 0-4 and gone at frame 5 is panel slot 2; frames_present 5 matches the panel flip at t5 exactly."},

  {"id": "O-03", "subject": "mdl_segmenter obj2 (colour 9, 3 cells, 1x3)", "verdict": "accept",
   "as": "Glyph9 instances at row 5 (the underline)",
   "why": "a 1x3 bar of colour 9 under a slot, which moves from cols 1-3 to cols 5-7 at t5; same colour as the body so it cannot be its own type."},

  {"id": "O-04", "subject": "mdl_segmenter obj3 (colour null, 1006 cells, 50x38)", "verdict": "reject",
   "why": "connected_components(4) over background 0 merged the whole colour-5 maze with the colour-9 donut sitting inside it; a 1006-cell blob with no colour is the segmenter failing to find a boundary, and both its variants report negative gain_bits, so its own MDL agrees it is not worth declaring."},

  {"id": "O-05", "subject": "mdl_segmenter obj4 (colour 9, 64 cells, 1x64, row 63)", "verdict": "accept",
   "as": "board for cols 0-61, Glyph9 instances for (63,62) and (63,63)",
   "why": "only 2 of the bar's 64 cells appear in the 73-cell dynamic census, so 62 of them are constant and belong to the board; this split is what makes the meter head uniquely addressable by below(?p) = wall."},

  {"id": "O-06", "subject": "mdl_segmenter obj5 (colour 2, 8 cells, first_frame 5)", "verdict": "accept",
   "as": "Glyph2",
   "why": "colour 2 exists in the world only from frame 5, as the hollow ring that replaces slot 1; declared so the colour is named, with the admission in dynamic_census that it has no frame-0 instances and therefore fires nothing."},

  {"id": "O-07", "subject": "the 5x5 donut as a single object", "verdict": "reject",
   "why": "an instance is drawn as exactly one cell, so a 24-cell rigid body declared without arc-instances: all would be located at one cell and leave 23 pixels unexplained forever; it stays 24 Glyph9 instances and the body-ness lives in a guard, per body_guard_isolates_the_donut."},

  {"id": "R-01", "subject": "meter_burn_key2", "verdict": "accept",
   "why": "t2's diff contains exactly one cell outside the body's two squares, (63,63) 9 -> 1; the only Glyph9 instances on row 63 are (63,62) and (63,63) because the rest of the bar is constant, and rightof(?p) = wall picks the second of those and nothing else in the frame. cov 1/1."},

  {"id": "R-02", "subject": "meter_burn_key4", "verdict": "accept",
   "why": "t4 changed exactly one cell, (63,62) 9 -> 1, and moved nothing; colored(rightof(?p), 1) grounds only on (63,62) because (63,63) had already burned at t2. This is the one transition my manual now replays exactly."},

  {"id": "R-03", "subject": "key2_vacates_body", "verdict": "accept",
   "why": "the replay_mismatch report itself is the evidence: it lists 24 cells at rows 8-12 cols 14-18 minus (10,16) where the manual said 9 and the world said 5, i.e. 24/24 of the donut vacated to floor on ACTION2. The four-way not-background guard separates those 24 from the other 13 Glyph9 instances at both observed body positions."},

  {"id": "R-04", "subject": "key2_lands via 'forall ?v in Vacated then recolored(?v, 9)'", "verdict": "reject",
   "why": "it is 24/24 on t2 and would take t2 to zero wrong cells, but only because the arm's colour-5 dynamic instances happen to be precisely the t2 destination; it is the answer key with a forall around it and would be wrong for every ACTION2 not pressed from spawn. Rejected as a stored solution, and said so in the_two_destination_rules_i_refused."},

  {"id": "R-05", "subject": "key2_lands via colored(above^6(?v), 9)", "verdict": "probe-pending",
   "why": "genuinely general -- 'floor whose cell six above is body-coloured becomes body-coloured' -- 24/24 on t2, and it leaves the donut's hole alone for the right reason. Held back only because the published cell grammar does not state that above(x) accepts a cell for x, and a parse error costs the whole manual rather than one rule. Exact text is in laws; compile it in isolation first."},

  {"id": "R-06", "subject": "a one-cell moved(?p, down) for ACTION2", "verdict": "reject",
   "why": "the displacement is six pixels, not one, so the rule is false as written and would put the donut at rows 9-13 where the world has floor; it trades 24 known-wrong cells for 24 differently-wrong cells and buys a falsehood with them."},

  {"id": "R-07", "subject": "any rule for ACTION5", "verdict": "probe-pending",
   "why": "t5 needs the same six-pixel displacement I cannot write plus a 23-cell panel rewrite of which 3 cells -- (5,5),(5,6),(5,7), background at frame 0 -- can be owned by no colour-keyed object. Writing the fragment I can write would claim a respawn reading I have one observation for."},

  {"id": "R-08", "subject": "no rule for ACTION1 and ACTION3", "verdict": "entailed",
   "why": "absence of a rule compiles to 'nothing happens', which is exactly what t1 and t3 did, pixel for pixel and meter cell included; adding anything here would cost coverage, not gain it."},

  {"id": "L-01", "subject": "cegis_miner verdict 'the world does not narrate as one mover'", "verdict": "accept",
   "why": "every track was refused -- two for NoSeparatingGuard, two for narrating recolor, one for vanish, one for absence at frame 0 -- which is independent confirmation that no single-cell mover exists here; it is the same wall the_move_is_six_pixels_and_the_dsl_cannot_say_it hits from the manual's side."},

  {"id": "L-02", "subject": "zero_space global law over the 73-cell support", "verdict": "reject",
   "as": "kept only as the census in dynamic_census",
   "why": "its own evidence_adequacy says THIN: 5 transitions constrain rank 3 of 365 features, leaving a 362-dimensional null space in which nearly every vector is unfalsified rather than confirmed. The cell list is useful arithmetic; the law it wraps is not a law."},

  {"id": "L-03", "subject": "invariant nine_count corrected from 35 to 37", "verdict": "accept",
   "why": "the previous manual counted the current frame, not frame 0: at frame 0 Glyph9 is 24 donut + 8 ring + 3 underline + 2 unburned meter cells = 37, and 37 + 9 Spent + 24 Vacated = 70, which is the arm's cells_needing_an_owner exactly. The 35 figure is the current frame after two meter burns and the ring change."},

  {"id": "L-04", "subject": "invariant that the meter never regrows", "verdict": "reject",
   "why": "I wanted count(Spent) monotone, but Spent is colour 1 and the panel's slot-2 block of 9 colour-1 cells stopped being colour 1 at t5, so the count fell from 11 to 2; the meter and the panel share a colour and the invariant is simply false as stated."},

  {"id": "P-01", "subject": "does the cell grammar nest", "verdict": "probe-pending",
   "why": "compile 'when act=key(2) and colored(above(above(above(above(above(above(?v)))))), 9) then recolored(?v, 9)' on its own. If it parses, R-05 enters next round and t2 replays exactly; if it does not, the six-pixel move is confirmed inexpressible and the manual stops trying."},

  {"id": "P-02", "subject": "what separates a free refusal from a metered one", "verdict": "probe-pending",
   "why": "t1 and t3 cost nothing, t4 cost one meter cell, and none of the three moved anything. The hypothesis in meter_depletes_rightward is that aiming inside the play area costs one whether or not it succeeds; press ACTION1 or ACTION3 from a lattice cell where those directions are on-board and see whether a cell burns."},

  {"id": "P-03", "subject": "is ACTION5 respawn or is it 'up'", "verdict": "probe-pending",
   "why": "at t5 the two readings are indistinguishable because the body was exactly one lattice cell below spawn. Press ACTION5 from anywhere else and they separate in one action."},

  {"id": "E-01", "subject": "a six-pixel rigid displacement of a 24-instance body", "verdict": "probe-pending",
   "as": "written as the_move_is_six_pixels_and_the_dsl_cannot_say_it, plus half of it as key2_vacates_body",
   "why": "wanted an event moving a whole declared body by one lattice cell; the event table's maximum displacement is two cells (jumped over an object) and there is no aggregate over instances, so the arriving half of the move has no expression at all except the probe in R-05."},

  {"id": "E-02", "subject": "the goal 'the donut is seated in the socket'", "verdict": "probe-pending",
   "as": "written as socket_is_the_conjectured_goal and i_cannot_write_the_goal_i_believe, with no goal section",
   "why": "wanted goal Glyph9.pos = socket_center; arc-instances: all means no instance is named Glyph9, and the goal grammar offers only = over counts, which cannot distinguish a won state from a lost one here. Also, every observed state is NOT_FINISHED, so I have no evidence about winning even if I could write it."},

  {"id": "E-03", "subject": "ownership of (5,5),(5,6),(5,7) and (2,6)", "verdict": "probe-pending",
   "as": "written as three_cells_i_cannot_own",
   "why": "they are background at frame 0 and coloured later; an arc-colour 0 object would claim all ~3000 background cells, so any future ACTION5 rule carries a structural floor of 3 wrong cells. Saying this is worth more than a tidier manual."}
]
```
```
