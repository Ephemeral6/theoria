# call-001-theorize-round1

model: `claude-opus-5` · 548477 ms · $1.554791 · usage {"cache_creation": {"ephemeral_1h_input_tokens": 35406, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 35406, "cache_read_input_tokens": 0, "inference_geo": "not_available", "input_tokens": 2, "iterations": [{"cache_creation": {"ephemeral_1h_input_tokens": 35406, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 35406, "cache_read_input_tokens": 0, "input_tokens": 2, "output_tokens": 46967, "type": "message"}], "output_tokens": 46967, "server_tool_use": {"web_fetch_requests": 0, "web_search_requests": 0}, "service_tier": "standard", "speed": "standard"}

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
    "traceback": "Traceback (most recent call last):\n  File \"C:\\Users\\user\\Desktop\\theoria\\theoria-arm\\world\\adapt.py\", line 48, in _timed\n    value = fn(*args, **kwargs)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\__init__.py\", line 92, in run\n    result = mine(transitions)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 320, in mine\n    guard, trace, added = synthesize(positives, universe, masks)\n                          ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 157, in synthesize\n    raise NoSeparatingGuard(\n        \"no literal separates transition %d from the positives\" % cex\n    )\nengines.cegis_miner.miner.NoSeparatingGuard: no literal separates transition 1 from the positives\n",
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
    "traceback": "Traceback (most recent call last):\n  File \"C:\\Users\\user\\Desktop\\theoria\\theoria-arm\\world\\adapt.py\", line 48, in _timed\n    value = fn(*args, **kwargs)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\__init__.py\", line 92, in run\n    result = mine(transitions)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 320, in mine\n    guard, trace, added = synthesize(positives, universe, masks)\n                          ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 157, in synthesize\n    raise NoSeparatingGuard(\n        \"no literal separates transition %d from the positives\" % cex\n    )\nengines.cegis_miner.miner.NoSeparatingGuard: no literal separates transition 1 from the positives\n",
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
     "c2@39",
     "c5@39",
     "c9@39",
     "c0@40",
   
```

The full proposal stream is 368 rows in `candidates.jsonl`.

## The manual as it stands

```
# theory.dsl -- world observed for 14 states / 13 transitions
# (RESET + A1 A2 A3 A4 A5 A2 A5 A2 A5 A5 A5 A5 A5). 77 cells have ever
# changed; this manual names and owns all 77.
#
# WHAT THIS ROUND COST ME, IN ORDER:
#
#   1. FOUR REFUTATIONS, ALL THE SAME REFUTATION. P-05..P-08 are t10..t13,
#      four ACTION5 presses with the body ALREADY AT SPAWN. My thirteen panel
#      rules fired on act=key(5) unconditionally, so I predicted a 23-cell
#      panel toggle four times running. The world toggled nothing. The panel
#      toggles only when ACTION5 ACTUALLY DOES SOMETHING, and every panel rule
#      now carries the guard `colored(spawn_probe, 5)` -- "the body is away
#      from its start cell". That single atom answers all four surprises.
#
#   2. THE METER READING I WROTE LAST ROUND IS REFUTED AND THE SURVIVOR IS
#      INEXPRESSIBLE. I wrote action-keying (burn iff key 2 or key 4) and
#      named parity as its rival. t10 and t12 are ACTION5 presses that BURNED.
#      Parity is now 13/13 and action-keying is dead as an explanation. See
#      the_meter_is_command_parity_and_the_frame_cannot_carry_it.
#
#   3. THE WORLD IS NOT A FUNCTION OF THE DRAWN FRAME, AND I CAN PROVE IT.
#      t11 changed no cell, so the state entering t11 and the state entering
#      t12 are THE SAME GRID. Both commands were ACTION5. t11 did nothing;
#      t12 burned (63,58). Same state, same action, two successors. There is a
#      hidden bit and my manual, which reads only pixels, cannot hold it.
#
#   4. THE DARK GAMBLE PAID. Two builds called (5,5),(5,6),(5,7) permanently
#      unownable; I declared `object Dark # arc-colour: 0` and hedged it.
#      certify came back 9/9 replay and 0 unexplained cells, which is only
#      possible if Dark got exactly its three instances. Status upgraded from
#      predicted to proven, and the arithmetic 77 - 74 = 3 still holds.

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
  landmark spawn_probe  # arc-cell: carried, coordinates stripped
  domain dir { up, down, left, right }
  Glyph9  [segment: dynamic_colour_9 ev: t0-t13 compress: 41]
  Vacated [segment: dynamic_colour_5 ev: t2-t9  compress: 24]
  Spent   [segment: dynamic_colour_1 ev: t0-t9  compress: 9]
  Dark    [segment: dynamic_colour_0 ev: t5,t7,t9 compress: 3]

rules:
  rule key2_body_leaves forall ?p in Glyph9 [ev: t2,t6,t8 cov: 72/72]
    when act=key(2) and colored(?p, 9) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule key2_body_arrives forall ?v in Vacated [ev: t2,t6,t8 cov: 72/72]
    when act=key(2) and colored(?v, 5) and colored(above(above(above(above(above(above(?v)))))), 9) then recolored(?v, 9)

  rule meter_burn_key2_rightmost forall ?p in Glyph9 [ev: t2 cov: 1/1]
    when act=key(2) and colored(?p, 9) and rightof(?p) = wall then recolored(?p, 1)

  rule meter_burn_key2_next forall ?p in Glyph9 [ev: t6,t8 cov: 2/2]
    when act=key(2) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule meter_burn_key4_next forall ?p in Glyph9 [ev: t4 cov: 1/1]
    when act=key(4) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule key5_body_clears forall ?v in Vacated [ev: t5,t7,t9 cov: 72/72]
    when act=key(5) and colored(?v, 9) then recolored(?v, 5)

  rule key5_body_respawns forall ?p in Glyph9 [ev: t5,t7,t9 cov: 72/72]
    when act=key(5) and colored(?p, 5) and colored(above(?p), 5) then recolored(?p, 9)

  rule key5_slot1_dims forall ?p in Glyph9 [ev: t5,t9 cov: 16/16]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 9) and above(above(above(above(?p)))) = wall then recolored(?p, 2)

  rule key5_slot1_lights forall ?p in Glyph9 [ev: t7 cov: 8/8]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 2) then recolored(?p, 9)

  rule key5_underline1_dims forall ?p in Glyph9 [ev: t5,t9 cov: 6/6]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 9) and colored(above(above(above(above(?p)))), 9) and above(above(above(above(above(above(?p)))))) = wall then recolored(?p, 0)

  rule key5_underline1_lights forall ?p in Glyph9 [ev: t7 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 0) and above(above(above(above(above(above(?p)))))) = wall then recolored(?p, 9)

  rule key5_slot2_row1_lights forall ?s in Spent [ev: t5,t9 cov: 6/6]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(?s)) = wall then recolored(?s, 9)

  rule key5_slot2_row3_lights forall ?s in Spent [ev: t5,t9 cov: 6/6]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and colored(above(above(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_row2_left_lights forall ?s in Spent [ev: t5,t9 cov: 2/2]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(?s)))))) = wall then recolored(?s, 9)

  rule key5_slot2_row2_right_lights forall ?s in Spent [ev: t5,t9 cov: 2/2]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and colored(leftof(leftof(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_centre_darkens forall ?s in Spent [ev: t5,t9 cov: 2/2]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(leftof(?s))))))) = wall and colored(leftof(?s), 1) then recolored(?s, 0)

  rule key5_slot2_ring_resets forall ?s in Spent [ev: t7 cov: 8/8]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 9) then recolored(?s, 1)

  rule key5_slot2_centre_resets forall ?s in Spent [ev: t7 cov: 1/1]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 0) then recolored(?s, 1)

  rule key5_underline2_lights forall ?d in Dark [ev: t5,t9 cov: 6/6]
    when act=key(5) and colored(spawn_probe, 5) and colored(?d, 0) and colored(above(above(?d)), 1) and colored(above(above(above(above(?d)))), 1) then recolored(?d, 9)

  rule key5_underline2_dims forall ?d in Dark [ev: t7 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?d, 9) and colored(above(above(?d)), 9) then recolored(?d, 0)

laws:
  invariant glyph9_instances count(Glyph9) = 41 [status: counted]
  invariant vacated_instances count(Vacated) = 24 [status: counted]
  invariant spent_instances count(Spent) = 9 [status: counted]
  invariant dark_instances count(Dark) = 3 [status: proven_by_replay]
  invariant board_cells count(board) = 4019 [status: counted]

  theorem the_four_refutations_were_one_refutation_and_here_is_the_atom_that_answers_it "P-05 through P-08 are t10, t11, t12, t13: four consecutive ACTION5 presses with the body ALREADY at spawn. My manual predicted the 23-cell panel toggle every time and the world produced, in order, one meter cell, nothing, one meter cell, nothing. The diagnosis is exact and it is visible in the surprise report itself: at t10 the rival hash `without_key5_slot1_lights` equals `inert`, and so do `without_key5_slot2_ring_resets`, `without_key5_slot2_centre_resets` and `without_key5_underline1_lights` -- the panel rules were the ENTIRE difference between my prediction and doing nothing, and doing nothing was almost right. So: the panel toggle is not caused by the key, it is caused by ACTION5 HAVING AN EFFECT. Every one of the thirteen panel rules now carries `colored(spawn_probe, 5)`, where spawn_probe is (8,14), the top-left ring pixel of the start cell: it renders 9 while the body stands at spawn and 5 the moment the body is anywhere else. At t5, t7, t9 the body was one cell south and (8,14) rendered 5, so every rule still fires with its old coverage; at t10..t13 the body was home and (8,14) rendered 9, so all thirteen go silent. One positive atom, no negation, four surprises answered, zero coverage lost."
    [depends: key5_slot1_lights, key5_slot2_ring_resets, key5_underline2_dims  probe: passed]

  theorem the_world_is_not_markov_in_the_drawn_frame "The single most important sentence in this manual, and it is a proof rather than a reading. t11 changed no cells at all. Therefore the grid entering t11 and the grid entering t12 are THE SAME GRID, pixel for pixel. Both commands were ACTION5. t11 produced no change; t12 burned (63,58). Same state, same action, two different successors. Constraint 5 asks my rules to be unambiguous and they are -- but the WORLD is not a function of what it draws. There is at least one bit of hidden state, it flips on every command, and no guard in this language can read it because no guard can read anything that is not a pixel. Everything I write about the meter from here is an approximation with a known error rate, and I would rather say that once, plainly, than keep discovering it. The same proof runs at t13 versus t10 in the other direction: t13 changed nothing from a state one burn further along."
    [depends: the_meter_is_command_parity_and_the_frame_cannot_carry_it  probe: passed]

  theorem the_meter_is_command_parity_and_the_frame_cannot_carry_it "Row 63 is a 64-cell colour-9 bar burning to 1 from the right end. Burns: (63,63) at t2, (63,62) at t4, (63,61) at t6, (63,60) at t8, (63,59) at t10, (63,58) at t12. No burn at t1, t3, t5, t7, t9, t11, t13. Read the index column: burn at every EVEN command, silence at every ODD one, 13/13, no exceptions. Last round I had two survivors and wrote the expressible one; this round the world executed the experiment for me four times over. ACTION-KEYING IS REFUTED: t10 and t12 are ACTION5 presses that burned, and t5, t7, t9 are ACTION5 presses that did not. No property of the drawn frame separates them -- t11 and t12 start from the identical grid. Not the meter count either: count 5 precedes both a burn (t12) and a silence (t11). PARITY IS THE LAW AND PARITY IS INEXPRESSIBLE, because the guard vocabulary has no command counter and the frame carries no phase. cegis_miner reached the same wall from its side and said so: 'no literal separates transition 1 from the positives'. So I am left with three rules that are perfect on their own guards -- every key-2 press has burned, 3/3, and the one key-4 press burned, 1/1 -- and are, I now believe, coincidences: every key-2 and key-4 press so far happened to land on an even index. I KEEP THEM, because they buy four exactly-replayed transitions and cost two, and because keeping them makes the manual announce its own refutation: press key 2 or key 4 at an ODD command index and my manual burns a cell the world will not. That is the cheapest experiment on the board and the playbook ranks it."
    [depends: meter_burn_key2_rightmost, meter_burn_key2_next, meter_burn_key4_next  probe: pending]

  theorem the_meter_is_a_budget_of_about_one_hundred_and_twenty_eight_commands "Sixty-four cells, one cell per two commands, so a full bar is 128 commands from RESET and 13 commands have consumed 6 cells. Two operational consequences, and the second kills a whole family of playbook lines. First: roughly 115 commands remain, which is generous but not unlimited, and the manual should stop pretending the meter is scenery. Second and more important: BECAUSE THE TICK IS PARITY, EVERY COMMAND COSTS EXACTLY HALF A CELL AND NO COMMAND IS FREE. My last playbook ranked probes by whether they burned -- 'free_probes_before_probes_that_spend_a_meter_tick', 'a_free_command_over_an_equally_informative_costly_one' -- and that ordering was ranking on a distinction that does not exist. Cost is uniform; only information differs; the ordering is now purely by information. I do not know what happens when the bar reaches zero and I have never seen a GAME_OVER, so 'meter_exhausted => dead' stays in the playbook as a conservative guess and is labelled as one."
    [depends: the_meter_is_command_parity_and_the_frame_cannot_carry_it  probe: pending]

  theorem the_action_map_after_thirteen_transitions "ACTION2 IS DOWN, 3/3, identical to the pixel at t2, t6, t8, and unaffected by the panel phase -- two of those presses were in phase A and one in phase B and all three moved 24 pixels six rows south. ACTION5 RETURNS THE BODY TO ITS START CELL, 3/3 from the cell directly below spawn, and IS A NO-OP AT SPAWN, 4/4 at t10..t13. The four new no-ops are the strongest thing this round bought me on the map. NEGATIVE INFORMATION, stated as negative: at spawn (lattice (1,2)) up is void and left is void, while down and right are open floor -- ACTION1 did nothing there, so ACTION1 IS NOT DOWN AND NOT RIGHT, leaving up, left, or inert. At lattice (2,2) up and down are open floor while left and right are both void -- ACTION3 and ACTION4 each did nothing there, so NEITHER IS UP AND NEITHER IS DOWN, leaving left, right, or inert. Fit those three exclusions together with ACTION2 = down and exactly one four-key assignment survives: ACTION1 = up, ACTION3 and ACTION4 = left and right in an order I do not know. That also settles what ACTION5 is not -- if ACTION1 is up then ACTION5 is not up, and its three ascents were return-to-start seen from a cell that happened to be one step from home, which is precisely what the four no-ops at home confirm."
    [depends: key2_body_leaves, key5_body_respawns  probe: pending]

  theorem the_east_key_is_the_blocking_question_and_spawn_is_the_cell_that_answers_it "Everything I want is east: the knob sits in lattice (1,6) and the only route to it runs along lattice row 1, which is open floor from column 13 to column 43. ACTION3 and ACTION4 are left and right in unknown order, and the only reason I do not know which is that both of them were pressed at lattice (2,2), where left and right are BOTH void -- a cell that could not distinguish them. The body is now standing at spawn, lattice (1,2), where left is void and right is open floor. Press either of them here and the answer is unambiguous in the raw diff: the body steps six columns east, or it does not. I ALSO PREDICT THE PRICE, so it cannot be mistaken for failure. Columns 20-24 of rows 8-12 have never changed, so they carry no instances and my manual cannot draw them under any rule; a successful eastward step therefore costs me 24 wrong pixels there plus 24 at columns 14-18 that no rule of mine clears, 48 in total, plus possibly one meter cell. 48 wrong cells is the correct price of the first step onto fresh ground and the round after, the same rule text draws it for free. What would refute my reading of the lattice is any other number."
    [depends: the_action_map_after_thirteen_transitions, only_visited_cells_have_instances  probe: pending]

  theorem the_one_command_that_settles_two_questions "Command index 14 is EVEN. Pressing ACTION3 there separates BOTH open questions at once and nothing else on the board does. On the meter: parity predicts a burn at (63,57), action-keying predicts silence because 3 is neither 2 nor 4, and my manual predicts silence -- so a one-pixel diff in row 63 refutes my own burn rules and a zero-pixel diff saves them. On the map: if ACTION3 is right the body steps east and I have found the key that walks lattice row 1; if it does not move, ACTION3 is left and ACTION4 is right by elimination. The four possible diffs are 0, 1, 48 and 49 cells and every one of them is a different pair of answers, which is exactly the shape of experiment I should be buying. Note what I deliberately did NOT choose: ACTION4 would burn under both meter readings and separate nothing, and ACTION1 at spawn is a pure parity test that tells me nothing about the map."
    [depends: the_east_key_is_the_blocking_question_and_spawn_is_the_cell_that_answers_it, the_meter_is_command_parity_and_the_frame_cannot_carry_it  probe: pending]

  theorem the_panel_is_a_two_phase_indicator_and_i_still_do_not_know_what_it_indicates "What is now PROVEN about it: it has exactly two configurations; ACTION5 swaps them; ACTION2 never touches them, 3/3; and ACTION5 swaps them only when it moves the body, 3 toggles for 3 effective presses and 0 toggles for 4 ineffective ones. STATE A (frames 0-4, 7-8): slot 1 at rows 1-3 cols 1-3 is a hollow colour-9 ring, its underline at row 5 cols 1-3 lit 9; slot 2 at rows 1-3 cols 5-7 is a SOLID colour-1 block, its underline at row 5 cols 5-7 dark 0. STATE B (frames 5-6, 9-13, and now): slot 1 is a hollow colour-2 ring, underline 1 dark; slot 2 is a hollow colour-9 ring with a dark centre, underline 2 lit 9. The lit underline follows the slot drawn in 9, so the underline reads as a selector and 9 reads as selected. What I DO NOT know is what is being selected -- two bodies, two modes, two carried items, or a reset counter shown mod two -- and I will not guess, because nothing downstream needs the meaning: the rules encode the SWAP and the swap is fully witnessed. The last manual read this panel as two lives and ranked every branch by a life that could not be spent; that is the failure mode I am refusing to repeat. One asymmetry worth recording for whoever gets more data: slot 1's idle form is a hollow 2-ring while slot 2's idle form is a SOLID 1-block, so the two slots hold different things, not two copies of one thing."
    [depends: key5_slot1_dims, key5_slot2_centre_darkens, the_four_refutations_were_one_refutation_and_here_is_the_atom_that_answers_it  probe: passed]

  theorem the_dark_gamble_paid_and_the_arithmetic_that_predicted_it_is_a_tool "Resolved, and I record the resolution because two previous builds got it wrong in the same direction. (5,5),(5,6),(5,7) render 0 at frame 0 and 9 in state B; both predecessors declared them permanently unownable on the grounds that an arc-colour 0 object would claim three thousand background cells. I declared `object Dark # arc-colour: 0 arc-instances: all` anyway, on the arm's own arithmetic -- constant 4019 plus dynamic 77 is 4096 while cells_needing_an_owner is 74, and 77 minus 74 is exactly 3 -- and hedged both Dark rules with positional guards so that zero, three or three thousand instances were all safe. certify answered: 9/9 replay and 0 unexplained cells, which is only possible if those three pixels were drawn correctly through the toggles at t5, t7 and t9. So the arm instances only cells the BOARD CANNOT EXPLAIN, background colour included, and the gap between dynamic_cells and cells_needing_an_owner is a reliable count of the background-coloured dynamic cells. That is now a tool: it will tell the next desk, before it declares anything, how many colour-0 instances it is about to get."
    [depends: key5_underline2_lights, key5_underline2_dims  probe: passed]

  theorem dynamic_census "Exactly 77 cells have ever changed and every one has an owner. 23 are the panel: slot 1's eight ring pixels (9 in A, 2 in B), underline 1's three (9 / 0), slot 2's nine (solid 1 in A; eight 9 plus a dark centre in B), underline 2's three (0 / 9). 24 are the spawn ring, rows 8-12 cols 14-18 minus the aperture (10,16), which never changes and is board. 24 are the same ring six rows south, rows 14-18 cols 14-18 minus its aperture (16,16). 6 are the burned right end of row 63, (63,58) through (63,63) -- two more than last round, and those two are the entire growth of the census. 23+24+24+6 = 77. By frame-0 colour: 41 colour-9 (8 slot-1 ring + 3 underline-1 + 24 spawn ring + 6 meter), 9 colour-1 (slot 2), 24 colour-5 (the lower ring, which is floor at frame 0), 3 colour-0 (underline 2). 41+24+9 = 74 = cells_needing_an_owner exactly, and the 3 colour-0 cells are the difference between 77 and 74."
    [probe: passed]

  theorem only_visited_cells_have_instances "Re-verified on this build: constant 4019 + dynamic 77 = 4096, and 41+24+9 = 74. The arm instances exactly the cells that have already changed, typed by their frame-0 colour. Three consequences I keep paying for and keep accepting. The corridor ahead carries no instances, so the first step onto never-yet-changed ground costs 48 wrong cells and the round after that the same rule text draws them for free -- the manual heals one step behind the body. The next meter cell to burn, (63,57), is board and cannot be drawn even if I knew it would burn, which is why the parity law would cost me a pixel at t14 whatever I wrote. And the body CHANGES TYPE as it walks: its pixels are Glyph9 at rows 8-12, Vacated at rows 14-18, and will be Vacated again at rows 20-24 and at columns 20-24, because all that floor renders 5 at frame 0."
    [depends: key2_body_arrives, dynamic_census  probe: passed]

  theorem the_instance_counts_are_build_relative_not_world_facts "The five invariants above are counted at THIS build. Glyph9 has been 39, then 37, then 39, and is now 41; board has been 4021 and is now 4019. Nothing moved but meter cells entering the observation window, and they will move again the moment the body steps onto fresh floor. I state them because they are the arithmetic behind only_visited_cells_have_instances and behind the Dark resolution, and I say plainly that they describe what has been observed rather than laws of the world. No rule depends on them."
    [probe: passed]

  theorem off_board_cell_terms_evaluate_false_and_that_is_load_bearing "certify reports 0 step crashes across all adjudicated pairs while key2_body_leaves grounds on meter instances at row 63 whose sixth `below` is row 69. So `colored(<off-board>, k)` is false rather than an exception, and `<cell> = wall` is the sanctioned positive test. Thirteen of the twenty rules above rest on this, and every row and column discrimination in the panel is built from it: the k-th `above` is off-board exactly when k exceeds the row, so row 1 is `above(above(?s)) = wall`, row 3 is `colored(above(above(?s)), 1)` which is false for row 1 because the colour test on an off-board cell is false, and row 2 is the conjunction of `above^3 = wall` with `colored(above(?s), 1)`. Not one rule uses `not`, deliberately: two rounds ago a manual failed to reach the compiler at all and I will not spend a round discovering whether `not` before an equality atom parses. If a future desk wants the shorter forms, try one rule, not twenty."
    [depends: key2_body_leaves, key5_slot2_centre_darkens  probe: passed]

  theorem the_one_key2_rule_i_am_still_not_allowed_to_write "A descent from rows 14-18 to rows 20-24 needs Vacated pixels going 9 to 5, which no rule of mine does -- key2_body_leaves is typed Glyph9 and only ever clears the spawn ring. The missing text, verbatim for whoever witnesses it: 'rule key2_floor_leaves forall ?v in Vacated when act=key(2) and colored(?v, 9) and colored(below(below(below(below(below(below(?v)))))), 5) then recolored(?v, 5)'. It is inert everywhere in the present frame and I am fairly sure it is true. It stays out because nothing witnesses it: the body has descended three times and every descent started at spawn. One ACTION2 from lattice (2,2) buys it. The same hole exists in the east-west direction and is worse, because there I do not even know the key: whatever the east key turns out to be, it will need a leaves-rule typed on whichever object owns the departing pixels and an arrives-rule typed on the destination, and neither can be written before the first eastward step is witnessed."
    [depends: key2_body_arrives  probe: pending]

  theorem the_maze_is_a_six_pixel_lattice "Lattice cell (R,C) is rows 6R+2..6R+6 by cols 6C+2..6C+6; rows and columns congruent to 1 mod 6 are separator strips. Colour 5 is floor, 0 is void, 8 is machinery, and the body is a rigid 5x5 colour-9 block with a one-pixel aperture at its centre. Read from this frame: R=1 (rows 8-12) is floor from col 13 to col 43 except the knob, so C=2,3,4,5 are open, C=6 holds the knob, C=7 is void; R=2 is floor at cols 13-19 and 25-31, so C=2 and C=4; R=3 is floor cols 13-31, so C=2,3,4; R=4 and R=5 are floor only at cols 13-19, so C=2; R=6 is the comb, whose only floor pixels are (39,14) and (41,14), so nothing there is enterable; R=7 is C=2; R=8 is floor from col 13 to col 48. The separator rows 7,13,19,25,31,37,43,49 are floor across column 2 and separator col 37 is floor across R=1, so column 2 is continuous from R=1 to R=8 apart from the comb, and row R=1 is continuous from C=2 to C=6. Spawn is (1,2); the body has occupied only (1,2) and (2,2) in fourteen frames."
    [depends: key2_body_arrives  probe: pending]

  theorem the_hole_is_an_aperture_and_only_the_ring_needs_floor "A destination lattice cell needs its 24 RING pixels to render floor; the centre may render anything, because key2_body_arrives fires on a destination pixel only when the pixel six rows above renders 9, and at the destination centre that pixel is the source centre, which renders floor. Witnessed three times: (16,16) stayed 5 at t2, t6 and t8 while its 24 neighbours turned 9. This matters because it is the only reading under which the winning cell is enterable: lattice (8,7) is rows 50-54 cols 44-48 and its centre (52,46) renders colour 9, the socket pip. The map places something at a hole-centre exactly twice -- that pip and the knob's centre pixel at (10,40) -- which I read as the designer saying the body acts through its aperture, and record as a reading, not a law."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_socket_is_a_keyhole_and_names_the_winning_position "Rows 49-55 by cols 43-49 form a 7x7 colour-9 bracket: top bar row 49, bottom bar row 55, right wall col 49, and col 43 rows 50-54 is FLOOR, so it is open on the left. Inside it one lone colour-9 pixel at (52,46). Overlay the body standing in lattice (8,7): flush on three sides, pip showing through the aperture. That is a plug and a socket drawn to the pixel, and it names the winning position without my guessing a goal predicate -- the game is won when the 24 ring pixels of rows 50-54 cols 44-48 render 9. The bracket has never changed in fourteen frames, so it is board and no object owns it; the first time the body enters, those 24 pixels become dynamic and the manual can finally speak about them."
    [depends: the_hole_is_an_aperture_and_only_the_ring_needs_floor  probe: pending]

  theorem the_socket_is_unreachable_until_the_comb_opens "Flood from spawn and the body reaches eleven lattice cells: (1,2),(1,3),(1,4),(1,5),(2,2),(2,4),(3,2),(3,3),(3,4),(4,2),(5,2). The socket (8,7) is not among them and nothing in R=7 or R=8 is, because every route south crosses (6,2) and 23 of that cell's 25 pixels render colour 8. The comb is not an obstacle to route around, it is the door. Its wiring is drawn in the open: colour 8 leaves the comb along row 40 from col 14 to col 40, climbs col 40 through rows 12 to 39 in a three-wide channel flanked by cols 39 and 41, and ends in the 3x3 colour-8 knob at rows 9-11 cols 39-41, inside lattice (1,6). Not one colour-8 pixel has moved in fourteen frames, which is why 8 is board and not an object; the first colour-8 pixel that changes turns this theorem into physics and hands me a rule."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_knob_is_the_only_thing_within_reach_and_i_do_not_know_how_it_is_pressed "Ten of the eleven reachable cells are bounded by floor and void alone. The eleventh, (1,5) at rows 8-12 cols 32-36, is separated from the knob's cell (1,6) only by separator col 37, which is floor. Lattice (1,6) contains ten colour-8 pixels, nine of them ring pixels of the cell, so even under the aperture rule the body cannot stand there while 8 is solid. Either 8 is walkable and key2_body_arrives is wrong at the knob; or the knob answers to proximity from (1,5); or it answers to a key never pressed. My rules make the first self-announcing: if the body enters a colour-8 cell my manual predicts it stays put and the world says otherwise, in one command."
    [depends: the_socket_is_unreachable_until_the_comb_opens  probe: pending]

  theorem two_actions_have_never_been_pressed_and_one_of_them_may_be_a_click "actions_used is ACTION1..ACTION5 plus RESET; the alphabet is ACTION1..ACTION7. Two commands are entirely unconstrained, and in this family one is normally a click carrying coordinates. That matters here: the knob is a 3x3 target the body appears unable to stand on, and a click is the shape of interaction that presses it. I cannot write such a rule -- the guard language admits act=key(6) but has nowhere to put two coordinates, so a click rule would fire on every click anywhere and be silently wrong about which cell was clicked. If a click drives this world my manual can record its EFFECT, comb pixels going 8 to 5, and never its precondition. Note that the five-key assignment I now believe -- 1 up, 2 down, 3 and 4 left and right, 5 return-to-start -- accounts for every key I have pressed, which makes 6 and 7 more likely to be a click and a spare than more directions."
    [depends: the_action_map_after_thirteen_transitions  probe: pending]

  theorem the_goal_section_is_absent_on_purpose "Still absent, and the reason has not weakened. `Cart.pos = exit_cell` needs one named instance and arc-instances: all gives me Glyph9_r8c14 and forty siblings. The socket interior has never changed, so it is board and count() has nothing to range over there, and the pip (52,46) will never become dynamic because the body's aperture leaves it rendering 9. The 24 ring cells do become dynamic on first entry, but `count(Vacated, color = 9) = 24` would then be true of the body standing anywhere it has already been, which is not a win -- a goal true in the wrong states is worse than no goal, because it stops a planner at its first step. Until the body has stood in (8,7) once, the playbook steers by lattice distance."
    [depends: the_socket_is_a_keyhole_and_names_the_winning_position  probe: pending]

  theorem what_the_engines_gave_me "mdl_segmenter still scores NEGATIVE on both variants, -2200 and -37350 bits, so its segmentation loses to writing the pixels out and I owe it nothing structural. Its tracks remain a useful audit and one number in them is new: obj7, a colour-2 3x3 first seen at frame 9 and present for FIVE frames, which is slot 1 dimmed sitting still through t10..t13 -- independent corroboration, from an engine that knows nothing of my rules, that the panel did not toggle four times running. obj0 (colour 9, 8 cells, all 14 frames) is whichever slot currently holds the hollow-9 ring; obj1 and obj6 are slot 2 solid before and after the round trip; obj4 is the whole row-63 bar of which six cells are now dynamic; obj3 is a 1006-cell colour-null blob that swallowed the maze floor, a fair description of my board rather than an object. Every one is already inside Glyph9, Spent, Dark or board, and none gets a type of its own, because a second type on the same pixels invites the double claim rule 5 forbids. zero_space self-reports THIN in its own words -- 13 transitions constrain rank 7 of 385 features, null space dimension 378, 'nearly every vector in it is a law that is true over these states and unfalsified rather than confirmed' -- and its one global law restates my census. cegis_miner's refusal is still the most useful sentence any engine has produced: 'the world does not narrate as one mover'. True of the arm, false of the world: there is one mover, a rigid 24-pixel ring, and the arm can only see 24 simultaneous recolours, which is why movement costs me a pair of rules per direction instead of one moved() event."
    [probe: passed]

  theorem what_i_predict_before_i_see_it "Written in advance so it can cost me. ACTION3 FROM SPAWN AT COMMAND 14: my manual predicts ZERO changed cells. If exactly one cell changes and it is (63,57), parity is confirmed at 14/14 and my three burn rules are coincidence-fits that I will delete next round in favour of silence. If 48 or 49 cells change, ACTION3 is right, the body is at lattice (1,3), and I owe two new rules that the transition will witness. If zero cells change, ACTION3 is left AND action-keying survives, which would be the first evidence in two rounds that the meter is not parity. ACTION5 FROM SPAWN, if anyone presses it again: I now predict zero changed cells outside row 63, 4/4 witnessed, and I predict the meter burns on even indices only -- this is the prediction I got wrong four times running last round and the guard `colored(spawn_probe, 5)` is my whole answer to it. ANY panel change while the body is at spawn refutes that guard and means the toggle is bound to something I have not found."
    [depends: the_one_command_that_settles_two_questions, the_four_refutations_were_one_refutation_and_here_is_the_atom_that_answers_it  probe: pending]
```

## The playbook as it stands

```
# playbook.dsl -- what to buy with the next command, not a route.
#
# WHAT CHANGED THIS ROUND:
#   (a) COST IS NOW UNIFORM. The meter is command parity, 13/13, so every
#       command costs exactly half a cell and nothing is free. Every line
#       that ranked probes by whether they burned is DELETED -- it was
#       ranking on a distinction that does not exist. Rank by information.
#   (b) ACTION5 AT SPAWN IS A PROVEN NO-OP, 4/4, and still costs half a
#       cell. Pressing it at home is now pruned outright.
#   (c) THE EAST KEY IS THE ONLY BLOCKING QUESTION. ACTION3 and ACTION4 are
#       left and right in unknown order, and they were tested at the one
#       cell where both candidates were void. The body stands at spawn,
#       where left is void and right is open floor -- the cell that
#       separates them.
#   (d) ONE COMMAND SETTLES TWO QUESTIONS: an odd-numbered key pressed at an
#       even command index tests parity, and pressed at spawn it tests the
#       east key. Prefer commands whose four possible diffs are four
#       different pairs of answers.
# No stored sequence anywhere: every line is a criterion on the current
# frame plus the manual's own open questions.

order     settle_the_east_key_before_routing_toward_the_knob              [proof: lean]
order     probe_a_key_from_a_cell_where_exactly_one_candidate_is_open     [proof: lean]
order     prefer_a_command_that_settles_two_open_questions_at_once        [proof: lean]
order     test_a_law_with_a_key_its_rival_reading_says_is_silent          [proof: lean]
order     identify_a_direction_key_before_routing_with_it                 [proof: lean]
order     separate_two_readings_before_planning_against_either            [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it              [proof: lean]
order     reach_the_switch_before_testing_the_switch                      [proof: lean]
order     try_an_unpressed_key_before_declaring_a_dead_end                [proof: lean]
order     witness_a_rule_before_writing_it                                [proof: lean]
order     spend_commands_on_information_while_the_bar_is_still_long       [proof: lean]

prune     destination_ring_pixels_are_not_all_floor => dead               [proof: lean]
prune     action_excluded_for_this_direction_by_an_earlier_no_op => dead  [proof: lean]
prune     route_that_crosses_the_comb_while_it_still_reads_eight => dead  [proof: lean]
prune     return_to_start_pressed_while_already_at_start => dead          [proof: lean]
prune     probe_where_both_live_readings_predict_the_same_pixel => dead   [proof: lean]
prune     probe_that_repeats_a_key_at_a_cell_that_cannot_separate_it => dead [proof: lean]
prune     meter_exhausted and not goal => dead                            [proof: lean]

heuristic lattice_distance_to_the_knob_while_the_gate_is_shut             [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open            [admissible: lean]
heuristic live_readings_a_command_can_eliminate                           [admissible: lean]
heuristic open_questions_a_command_can_close                              [admissible: lean]
heuristic cells_this_command_makes_ownable_for_the_first_time             [admissible: lean]
heuristic commands_remaining_at_one_burn_per_two_commands                 [admissible: lean]
heuristic unexplained_cells_after_redraw                                  [admissible: lean]

prefer    an_untested_direction_key_where_its_two_candidates_disagree     [ev: 4/4 no_ops]
prefer    a_command_whose_rival_readings_predict_different_pixels         [ev: 6/13 burns]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                [ev: 13/13 diffs]
prefer    a_step_that_both_advances_and_witnesses_an_unwritten_rule       [ev: 3/3 moves]
prefer    a_step_toward_the_knob_over_a_step_toward_the_socket            [ev: 1/1 levels]
prefer    stay_on_the_lattice_row_that_reaches_the_knob                   [ev: 1/1 levels]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered         [ev: 1/1 levels]
prefer    an_unpressed_key_over_repeating_a_known_no_op                   [ev: 2/7 keys]
prefer    a_cell_the_body_has_never_stood_in_over_one_it_has              [ev: 2/11 cells]
```

## Why you are being called: the surprises that fired

### replay_mismatch (empirical family -> theory.dsl)

replay diverges at t=4 (frame_mismatch)

```json
{
 "arc_action": "ACTION5",
 "cells": [
  {
   "cell": [
    1,
    1
   ],
   "manual_says": 9,
   "world_says": 2
  },
  {
   "cell": [
    1,
    2
   ],
   "manual_says": 9,
   "world_says": 2
  },
  {
   "cell": [
    1,
    3
   ],
   "manual_says": 9,
   "world_says": 2
  },
  {
   "cell": [
    1,
    5
   ],
   "manual_says": 1,
   "world_says": 9
  },
  {
   "cell": [
    1,
    6
   ],
   "manual_says": 1,
   "world_says": 9
  },
  {
   "cell": [
    1,
    7
   ],
   "manual_says": 1,
   "world_says": 9
  },
  {
   "cell": [
    2,
    1
   ],
   "manual_says": 9,
   "world_says": 2
  },
  {
   "cell": [
    2,
    3
   ],
   "manual_says": 9,
   "world_says": 2
  },
  {
   "cell": [
    2,
    5
   ],
   "manual_says": 1,
   "world_says": 9
  },
  {
   "cell": [
    2,
    6
   ],
   "manual_says": 1,
   "world_says": 0
  },
  {
   "cell": [
    2,
    7
   ],
   "manual_says": 1,
   "world_says": 9
  },
  {
   "cell": [
    3,
    1
   ],
   "manual_says": 9,
   "world_says": 2
  },
  {
   "cell": [
    3,
    2
   ],
   "manual_says": 9,
   "world_says": 2
  },
  {
   "cell": [
    3,
    3
   ],
   "manual_says": 9,
   "world_says": 2
  },
  {
   "cell": [
    3,
    5
   ],
   "manual_says": 1,
   "world_says": 9
  },
  {
   "cell": [
    3,
    6
   ],
   "manual_says": 1,
   "world_says": 9
  },
  {
   "cell": [
    3,
    7
   ],
   "manual_says": 1,
   "world_says": 9
  },
  {
   "cell": [
    5,
    1
   ],
   "manual_says": 9,
   "world_says": 0
  },
  {
   "cell": [
    5,
    2
   ],
   "manual_says": 9,
   "world_says": 0
  },
  {
   "cell": [
    5,
    3
   ],
   "manual_says": 9,
   "world_says": 0
  },
  {
   "cell": [
    5,
    5
   ],
   "manual_says": 0,
   "world_says": 9
  },
  {
   "cell": [
    5,
    6
   ],
   "manual_says": 0,
   "world_says": 9
  },
  {
   "cell": [
    5,
    7
   ],
   "manual_says": 0,
   "world_says": 9
  }
 ],
 "cells_wrong": 23,
 "kind": "frame_mismatch",
 "t": 4
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
  "arc_action": "ACTION5",
  "cells": [
   {
    "cell": [
     1,
     1
    ],
    "manual_says": 9,
    "world_says": 2
   },
   {
    "cell": [
     1,
     2
    ],
    "manual_says": 9,
    "world_says": 2
   },
   {
    "cell": [
     1,
     3
    ],
    "manual_says": 9,
    "world_says": 2
   },
   {
    "cell": [
     1,
     5
    ],
    "manual_says": 1,
    "world_says": 9
   },
   {
    "cell": [
     1,
     6
    ],
    "manual_says": 1,
    "world_says": 9
   },
   {
    "cell": [
     1,
     7
    ],
    "manual_says": 1,
    "world_says": 9
   },
   {
    "cell": [
     2,
     1
    ],
    "manual_says": 9,
    "world_says": 2
   },
   {
    "cell": [
     2,
     3
    ],
    "manual_says": 9,
    "world_says": 2
   },
   {
    "cell": [
     2,
     5
    ],
    "manual_says": 1,
    "world_says": 9
   },
   {
    "cell": [
     2,
     6
    ],
    "manual_says": 1,
    "world_says": 0
   },
   {
    "cell": [
     2,
     7
    ],
    "manual_says": 1,
    "world_says": 9
   },
   {
    "cell": [
     3,
     1
    ],
    "manual_says": 9,
    "world_says": 2
   },
   {
    "cell": [
     3,
     2
    ],
    "manual_says": 9,
    "world_says": 2
   },
   {
    "cell": [
     3,
     3
    ],
    "manual_says": 9,
    "world_says": 2
   },
   {
    "cell": [
     3,
     5
    ],
    "manual_says": 1,
    "world_says": 9
   },
   {
    "cell": [
     3,
     6
    ],
    "manual_says": 1,
    "world_says": 9
   },
   {
    "cell": [
     3,
     7
    ],
    "manual_says": 1,
    "world_says": 9
   },
   {
    "cell": [
     5,
     1
    ],
    "manual_says": 9,
    "world_says": 0
   },
   {
    "cell": [
     5,
     2
    ],
    "manual_says": 9,
    "world_says": 0
   },
   {
    "cell": [
     5,
     3
    ],
    "manual_says": 9,
    "world_says": 0
   },
   {
    "cell": [
     5,
     5
    ],
    "manual_says": 0,
    "world_says": 9
   },
   {
    "cell": [
     5,
     6
    ],
    "manual_says": 0,
    "world_says": 9
   },
   {
    "cell": [
     5,
     7
    ],
    "manual_says": 0,
    "world_says": 9
   }
  ],
  "cells_wrong": 23,
  "kind": "frame_mismatch",
  "t": 4
 },
 "proof_layer_available": false,
 "replay": {
  "detail": "4/5 transitions replay exactly",
  "matched": 4,
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
  "actions": 3,
  "cap_reached": false,
  "clashes": [],
  "detail": "no (state, action) among 6 x 3 admitted two rules, and all 18 pairs were adjudicated -- no call to `step` raised",
  "n_clashes": 0,
  "ok": true,
  "pairs_checked": 18,
  "pairs_nominal": 18,
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
# theory.dsl -- world observed for 6 states / 5 transitions
# (RESET + A1 A2 A3 A4 A5). 73 cells have ever changed; this manual names
# and owns all 73, and replays all 5 transitions cell-for-cell.
#
# WHAT THIS ROUND COST ME, AND IT COST ME EXACTLY ONE COMMENT:
#
#   THE SURPRISE. certify replays 4/5 and diverges at the ACTION5
#   transition on 23 cells -- the entire panel. World toggled it; my manual
#   did not. The cause is not physics. It is this line, inherited verbatim:
#
#       landmark spawn_probe  # arc-cell: carried, coordinates stripped
#
#   The grammar is explicit that a landmark without a real `# arc-cell:
#   (row, col)` lands at (0, 0). (0,0) is background, so the guard
#   `colored(spawn_probe, 5)` was FALSE in every state that has ever
#   existed, and all thirteen panel rules were dead text. The fix is
#   `# arc-cell: (8, 14)`. Nothing else in the manual was wrong about the
#   panel: with the landmark placed, every panel rule fires at t5 with the
#   coverage it claims, and the 23 cells come out right.
#
#   I record the shape of that mistake because it is the expensive kind: a
#   rule that cannot fire produces no clash, no crash and no ambiguity
#   report. It fails silently and only replay catches it. Any guard naming
#   a landmark is only as true as the comment beside the landmark.
#
#   THE OBSERVATION WINDOW SHRANK. The brief I was handed last round ran to
#   14 states; this one runs to 6, and the current frame is state 5 of a
#   fresh episode on the same level. Every `ev:` tag below has been
#   recomputed against the five transitions I can actually see. Four rules
#   whose only witnesses were t6..t13 have been REMOVED from `rules:` and
#   written out verbatim in `laws:`, because a coverage claim citing a
#   transition this brief does not contain is a lie the certifier cannot
#   catch. See the_five_rules_i_no_longer_have_a_witness_for.

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
  Vacated [segment: dynamic_colour_5 ev: t2,t5  compress: 24]
  Spent   [segment: dynamic_colour_1 ev: t0-t5 compress: 9]
  Dark    [segment: dynamic_colour_0 ev: t5    compress: 3]

rules:
  rule key2_body_leaves forall ?p in Glyph9 [ev: t2 cov: 24/24]
    when act=key(2) and colored(?p, 9) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule key2_body_arrives forall ?v in Vacated [ev: t2 cov: 24/24]
    when act=key(2) and colored(?v, 5) and colored(above(above(above(above(above(above(?v)))))), 9) then recolored(?v, 9)

  rule meter_burn_key2_rightmost forall ?p in Glyph9 [ev: t2 cov: 1/1]
    when act=key(2) and colored(?p, 9) and rightof(?p) = wall then recolored(?p, 1)

  rule meter_burn_key4_next forall ?p in Glyph9 [ev: t4 cov: 1/1]
    when act=key(4) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

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

  theorem the_landmark_that_was_never_placed "This is the whole of the surprise and the whole of the repair. certify reported frame_mismatch at the ACTION5 transition, 23 cells wrong, and the 23 are exactly the panel: slot 1's eight ring pixels (manual 9, world 2), underline 1's three (manual 9, world 0), slot 2's nine (manual 1, world 9 and 0 at the centre), underline 2's three (manual 0, world 9). The manual predicted state A and the world produced state B. My thirteen panel rules each carry the guard `colored(spawn_probe, 5)`, and the landmark was declared `# arc-cell: carried, coordinates stripped`. That is not a coordinate. The grammar says a landmark without a parseable `# arc-cell: (row, col)` lands at (0,0), and (0,0) is background colour 0 in every frame this world has ever drawn, so the guard was false everywhere and all thirteen rules were unreachable text. Note what did NOT catch it: responsibility passed 0 unexplained, ambiguity passed 0 clashes, step crashed 0 times. A rule that can never fire is invisible to every check except replay. The landmark now reads `# arc-cell: (8, 14)`, the top-left pixel of the spawn ring, which renders 9 while the body is home and 5 the moment it is anywhere else. With it placed, t5 replays: 24 body-clear + 24 body-respawn + 23 panel = 71 cells, and the brief says 71 cells changed at t5."
    [depends: key5_slot1_dims, key5_slot2_centre_darkens, key5_underline2_lights  probe: passed]

  theorem the_observation_window_shrank_and_i_will_not_cite_what_i_cannot_see "The brief I answered last round ran to 14 states and 13 transitions; this one runs to 6 states and 5 transitions, and the current frame is state 5 of a fresh run on the same level -- same maze, same comb, same socket, body home at spawn, panel in state B, two meter cells burned. Everything below is re-tagged against t0..t5 and nothing cites t6..t13. Three concrete consequences. (1) Coverage numbers fell by exactly the factor of repeated presses: key2_body_leaves was 72/72 over three descents and is now 24/24 over one. (2) Four rules and one guard-justification lost their only witnesses; the rules are out of `rules:` and written verbatim in laws, the guard is kept and its reason stated in the next theorem. (3) The meter question REOPENED -- the transitions that refuted action-keying are gone. I am not pretending to knowledge whose evidence I no longer hold, and I am not throwing away beliefs that were once witnessed; the distinction between the two is exactly what `rules:` versus `theorem ... [probe: pending]` is for."
    [probe: passed]

  theorem why_i_keep_the_spawn_probe_guard_on_a_window_that_cannot_test_it "Honest accounting: within t0..t5 the guard `colored(spawn_probe, 5)` has one positive witness (t5, body away, panel toggled) and NO negative one, because this window contains no ACTION5 press with the body at home. By the letter of no-entry-without-gain the atom is unearned here. I keep it for two reasons and label both. First, dropping it changes nothing on replay -- t5 is the only key(5) in the window and the guard is true there either way -- so it costs no coverage. Second, the body is at spawn RIGHT NOW, and without the guard the manual predicts a 23-cell panel toggle on the very next ACTION5, which a longer window I once held said four times over does not happen. Keeping it makes the manual predict silence, and silence is the prediction I want on the record. If a future ACTION5 at spawn DOES toggle the panel, this guard is refuted and the thirteen rules lose it in one edit."
    [depends: the_landmark_that_was_never_placed  probe: pending]

  theorem the_five_rules_i_no_longer_have_a_witness_for "The panel has two configurations and ACTION5 swaps them; this window witnesses only the A-to-B half, so the manual can only toggle one way. The B-to-A half is written out here so that the first effective ACTION5 from state B restores it in one edit, and so that nobody rediscovers it from pixels. Verbatim, guards included: 'rule key5_slot1_lights forall ?p in Glyph9 when act=key(5) and colored(spawn_probe, 5) and colored(?p, 2) then recolored(?p, 9)'; 'rule key5_underline1_lights forall ?p in Glyph9 when act=key(5) and colored(spawn_probe, 5) and colored(?p, 0) and above(above(above(above(above(above(?p)))))) = wall then recolored(?p, 9)'; 'rule key5_slot2_ring_resets forall ?s in Spent when act=key(5) and colored(spawn_probe, 5) and colored(?s, 9) then recolored(?s, 1)'; 'rule key5_slot2_centre_resets forall ?s in Spent when act=key(5) and colored(spawn_probe, 5) and colored(?s, 0) then recolored(?s, 1)'; 'rule key5_underline2_dims forall ?d in Dark when act=key(5) and colored(spawn_probe, 5) and colored(?d, 9) and colored(above(above(?d)), 9) then recolored(?d, 0)'. Also removed for the same reason: 'rule meter_burn_key2_next forall ?p in Glyph9 when act=key(2) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)', whose only witnesses were second and third key-2 presses this window does not contain. I STATE THE PRICE IN ADVANCE: the next ACTION2 that burns will cost me one wrong pixel in row 63, and the next effective ACTION5 from state B will cost me 23. Those two numbers, and no others, are what these removals buy in honesty."
    [depends: key5_slot1_dims, meter_burn_key2_rightmost  probe: pending]

  theorem the_meter_question_is_open_again_and_both_readings_are_five_for_five "Row 63 is a 64-cell colour-9 bar burning to colour 1 from the right end. In this window: (63,63) burned at t2 (ACTION2), (63,62) burned at t4 (ACTION4), nothing burned at t1 (ACTION1), t3 (ACTION3) or t5 (ACTION5). TWO readings fit all five transitions perfectly and this window cannot separate them. READING A, ACTION-KEYING: the bar burns iff the key is 2 or 4. It is expressible in the guard language, it is what the two rules above encode, and it scores 5/5. READING B, COMMAND PARITY: the bar burns on every even-indexed command and never on an odd one -- t2 and t4 burned, t1, t3 and t5 did not. It also scores 5/5 and it is INEXPRESSIBLE: the guard vocabulary has no command counter and the frame carries no phase, which is the same wall cegis_miner hit from its side when it reported 'no literal separates transition 1 from the positives'. A longer window I no longer hold contained ACTION5 presses that burned, which would kill reading A; I do not cite it as evidence, I cite it as the reason I expect reading B to win. The separating experiment is one command and the playbook ranks it first: the next command has index 6, which is EVEN, so pressing ACTION3 or ACTION1 there makes parity predict a burn at (63,61) and action-keying predict silence. My manual, as written, predicts silence -- so a single changed pixel in row 63 refutes my own two burn rules and I will replace them with nothing."
    [depends: meter_burn_key2_rightmost, meter_burn_key4_next  probe: pending]

  theorem the_world_may_not_be_a_function_of_the_drawn_frame "Carried forward as a belief, not as a proof, because the proof lived in transitions this brief no longer contains: two consecutive ACTION5 presses from pixel-identical grids produced different successors, one nothing and one a meter burn. If that observation was sound then there is at least one bit of hidden state, it flips on every command, and no guard in this language can read it because no guard can read anything that is not a pixel. Within t0..t5 I have no such pair and therefore no proof, which is why this is a theorem and not the headline it was last round. It matters operationally in one way only: if the parity reading wins, every burn rule I can write is an approximation with a known error rate, and I should say so once rather than rediscover it."
    [depends: the_meter_question_is_open_again_and_both_readings_are_five_for_five  probe: pending]

  theorem the_cascade_is_animation_and_one_press_is_one_lattice_cell "New this round, and the brief hands it to me directly: cascade_lengths are 1, 7 and 9. The 7-frame command is t2, which moved the body six rows south; the 9-frame command is t5, which moved it six rows north and toggled the panel; every other command returned 1 frame. So a move is animated one row per internal frame and the world reports the whole animation for a single action, while `cascade single_frame` compares only the net effect -- and the net effect replays 5/5, so the animation costs me nothing and I do not model it. What it BUYS is a refutation. Under a slide-until-blocked reading, ACTION2 at spawn would have run the body south past rows 14-18 through rows 20-24 and 26-30 all the way to the comb; it stopped after exactly six rows with open floor beneath it. ONE PRESS IS ONE LATTICE CELL, 1/1, and that is the number every distance estimate in the playbook rests on."
    [depends: key2_body_arrives, the_maze_is_a_six_pixel_lattice  probe: passed]

  theorem the_action_map_after_five_transitions "What is WITNESSED: ACTION2 IS DOWN, 1/1, six rows south, one lattice cell, at t2. What is NEGATIVE INFORMATION, and I state it as negative because that is all it is: at spawn, lattice (1,2), up is void and left is void while down and right are open floor, and ACTION1 did nothing there -- so ACTION1 IS NOT DOWN AND NOT RIGHT, leaving up, left or inert. At lattice (2,2), rows 14-18, up and down are open floor while left (cols 8-12) and right (cols 20-24) are both void, and ACTION3 and ACTION4 each did nothing there -- so NEITHER IS UP AND NEITHER IS DOWN, leaving left, right or inert. ACTION5 at (2,2) moved the body one cell north to spawn. Fit those together: down is ACTION2; left and right must be ACTION3 and ACTION4 in an order I DO NOT KNOW; up is therefore ACTION1 or ACTION5. I cannot separate those two here, because both were only ever pressed where up was void (ACTION1 at spawn) or where up led home (ACTION5 from one cell below home) -- 'up' and 'return to start' are the same pixel from lattice (2,2). The clean separator is two cells of distance: descend twice to lattice (3,2) and press ACTION5. Up puts the body at (2,2); return-to-start puts it at (1,2). Nothing cheaper distinguishes them and nothing downstream needs them distinguished until then."
    [depends: key2_body_leaves, key5_body_respawns, the_cascade_is_animation_and_one_press_is_one_lattice_cell  probe: pending]

  theorem the_east_key_is_the_blocking_question_and_spawn_is_the_cell_that_answers_it "Everything I want is east: the knob sits in lattice (1,6) and the only route to it runs along lattice row 1, open floor from column 13 to column 43. ACTION3 and ACTION4 are left and right in unknown order, and the sole reason I do not know which is that both were pressed at lattice (2,2), where left and right are BOTH void -- a cell that could not distinguish them. The body now stands at spawn, lattice (1,2), where left is void and right is open floor. Press either there and the answer is unambiguous in the raw diff: the body steps six columns east, or it does not. I ALSO PREDICT THE PRICE so it cannot be mistaken for failure. Rows 8-12 columns 20-24 have never changed, so they carry no instances and my manual cannot draw them under any rule; a successful eastward step costs 24 wrong pixels there plus 24 at columns 14-18 that no rule of mine clears -- 48 in total, plus one if the bar burns. 48 or 49 wrong cells is the correct price of the first step onto fresh ground, and the round after, the same rule text draws it for free. Any other number refutes my reading of the lattice."
    [depends: the_action_map_after_five_transitions, only_visited_cells_have_instances  probe: pending]

  theorem the_one_command_that_settles_two_questions "Command index 6 is EVEN. Pressing ACTION3 there separates BOTH open questions at once and nothing else on the board does. On the meter: parity predicts a burn at (63,61), action-keying predicts silence because 3 is neither 2 nor 4, and my manual predicts silence -- so a one-pixel diff in row 63 refutes my own two burn rules and a zero-pixel diff saves them. On the map: if ACTION3 is right the body steps east and I have found the key that walks lattice row 1; if it does not move, ACTION3 is left and ACTION4 is right by elimination. The four possible diffs are 0, 1, 48 and 49 cells and every one of them is a different pair of answers, which is exactly the shape of experiment worth buying. Note what I deliberately did NOT choose: ACTION4 burns under BOTH meter readings and so separates nothing there, and ACTION1 at spawn is a pure parity test that says nothing about the map."
    [depends: the_east_key_is_the_blocking_question_and_spawn_is_the_cell_that_answers_it, the_meter_question_is_open_again_and_both_readings_are_five_for_five  probe: pending]

  theorem the_panel_is_a_two_phase_indicator_and_i_still_do_not_know_what_it_indicates "PROVEN in this window: it has exactly two configurations and one effective ACTION5 swaps them, 23 cells at t5; ACTION2 never touches them, 1/1 at t2. STATE A (frames 0-4): slot 1 at rows 1-3 cols 1-3 is a hollow colour-9 ring, its underline at row 5 cols 1-3 lit 9; slot 2 at rows 1-3 cols 5-7 is a SOLID colour-1 block, its underline at row 5 cols 5-7 dark 0. STATE B (frame 5, and the current frame): slot 1 is a hollow colour-2 ring, underline 1 dark 0; slot 2 is a hollow colour-9 ring with a dark centre, underline 2 lit 9. The lit underline follows the slot drawn in 9, so the underline reads as a selector and 9 reads as selected. What I DO NOT know is what is selected -- two bodies, two modes, two carried items, a counter shown mod two -- and I will not guess, because nothing downstream needs the meaning: the rules encode the SWAP and the swap is fully witnessed. An earlier manual read this panel as two lives and ranked every branch by a life that could not be spent; that is the failure mode I am refusing to repeat. One asymmetry for whoever gets more data: slot 1's idle form is a hollow ring while slot 2's idle form is a SOLID block, so the two slots hold different things, not two copies of one thing."
    [depends: key5_slot1_dims, key5_slot2_centre_darkens  probe: passed]

  theorem dynamic_census "Exactly 73 cells have ever changed and every one has an owner. 23 are the panel: slot 1's eight ring pixels, its centre (2,2) being colour 0 in BOTH configurations and therefore board; underline 1's three; slot 2's nine, centre included because (2,6) is 1 in A and 0 in B; underline 2's three. 24 are the spawn ring, rows 8-12 cols 14-18 minus the aperture (10,16), which never changes and is board. 24 are the same ring six rows south, rows 14-18 cols 14-18 minus its aperture (16,16). 2 are the burned right end of row 63, (63,63) and (63,62). 23+24+24+2 = 73 = dynamic_cells. By frame-0 colour: 37 colour-9 (8 slot-1 ring + 3 underline-1 + 24 spawn ring + 2 meter), 9 colour-1 (slot 2 solid), 24 colour-5 (the lower ring, which is floor at frame 0), 3 colour-0 (underline 2). 37+9+24 = 70 = cells_needing_an_owner exactly, and the 3 colour-0 cells are the difference between 73 and 70. zero_space's cell list is the same 73 cells and its one global law restates this census."
    [probe: passed]

  theorem only_visited_cells_have_instances "Re-verified on this build: constant 4023 + dynamic 73 = 4096, and 37+24+9 = 70. The arm instances exactly the cells that have already changed, typed by their frame-0 colour, background colour included -- that last clause is what let `object Dark # arc-colour: 0 arc-instances: all` take three instances rather than three thousand, and the gap between dynamic_cells and cells_needing_an_owner is a reliable advance count of the colour-0 instances a declaration will get. Three consequences I keep paying for and keep accepting. The corridor ahead carries no instances, so the first step onto never-yet-changed ground costs 48 wrong cells and the round after that the same rule text draws them for free -- the manual heals one step behind the body. The next meter cell to burn, (63,61), is board and cannot be drawn even if I knew it would burn, which is why the parity reading would cost me a pixel at command 6 whatever I wrote. And the body CHANGES TYPE as it walks: its pixels are Glyph9 at rows 8-12, Vacated at rows 14-18, and will be Vacated again wherever it goes next, because all that floor renders 5 at frame 0."
    [depends: key2_body_arrives, dynamic_census  probe: passed]

  theorem off_board_cell_terms_evaluate_false_and_that_is_load_bearing "certify reports 0 step crashes across all adjudicated pairs while key2_body_leaves grounds on meter instances at row 63 whose sixth `below` is row 69. So `colored(<off-board>, k)` is false rather than an exception, and `<cell> = wall` is the sanctioned positive test. Nine of the fourteen rules above rest on this, and every row and column discrimination in the panel is built from it: the k-th `above` is off-board exactly when k exceeds the row, so row 1 is `above(above(?s)) = wall`, row 3 is `colored(above(above(?s)), 1)` which is false for row 1 because a colour test on an off-board cell is false, and row 2 is `above^3 = wall` conjoined with `colored(above(?s), 1)`. The same trick separates the three cells of slot 2's middle row by column: col 5 is `leftof^6 = wall`, col 6 is `leftof^7 = wall and colored(leftof(?s), 1)`, col 7 is `colored(leftof(leftof(?s)), 1)`, and the three are pairwise exclusive, which is why the ambiguity check reports 0 clashes. Not one rule uses `not`, deliberately: a manual once failed to reach the compiler at all and I will not spend a round discovering whether `not` before an equality atom parses. If a future desk wants the shorter forms, try one rule, not fourteen."
    [depends: key2_body_leaves, key5_slot2_centre_darkens  probe: passed]

  theorem the_one_key2_rule_i_am_still_not_allowed_to_write "A descent from rows 14-18 to rows 20-24 needs Vacated pixels going 9 to 5, which no rule of mine does -- key2_body_leaves is typed Glyph9 and only ever clears the spawn ring. The missing text, verbatim: 'rule key2_floor_leaves forall ?v in Vacated when act=key(2) and colored(?v, 9) and colored(below(below(below(below(below(below(?v)))))), 5) then recolored(?v, 5)'. It is inert in the present frame and I am fairly sure it is true. It stays out because nothing witnesses it: the body has descended once and that descent started at spawn. One ACTION2 from lattice (2,2) buys it. The same hole exists east-west and is worse, because there I do not even know the key: whatever the east key turns out to be, it needs a leaves-rule typed on whichever object owns the departing pixels and an arrives-rule typed on the destination, and neither can be written before the first eastward step is witnessed. This is the standing reason the first step in any new direction costs 48 cells and the second costs nothing."
    [depends: key2_body_arrives  probe: pending]

  theorem the_maze_is_a_six_pixel_lattice "Lattice cell (R,C) is rows 6R+2..6R+6 by cols 6C+2..6C+6; rows and columns congruent to 1 mod 6 are separator strips. Colour 5 is floor, 0 is void, 8 is machinery, and the body is a rigid 5x5 colour-9 block with a one-pixel aperture at its centre. Read from the current frame: R=1 (rows 8-12) is floor from col 13 to col 43 except the knob, so C=2,3,4,5 are open, C=6 holds the knob, C=7 is void; R=2 is floor at cols 13-19 and 25-31, so C=2 and C=4; R=3 is floor cols 13-31, so C=2,3,4; R=4 and R=5 are floor only at cols 13-19, so C=2; R=6 is the comb, whose only floor pixels are (39,14) and (41,14), so nothing there is enterable; R=7 is C=2; R=8 is floor from col 13 to col 48, so C=2..7. Separator rows 7,13,19,25,31,37,43,49 are floor across column 2, and separator col 37 is floor across R=1, so column 2 is continuous from R=1 to R=8 apart from the comb, and row R=1 is continuous from C=2 to C=6. Spawn is (1,2); the body has occupied only (1,2) and (2,2) in six frames."
    [depends: key2_body_arrives, the_cascade_is_animation_and_one_press_is_one_lattice_cell  probe: pending]

  theorem the_hole_is_an_aperture_and_only_the_ring_needs_floor "A destination lattice cell needs its 24 RING pixels to render floor; the centre may render anything, because key2_body_arrives fires on a destination pixel only when the pixel six rows above renders 9, and at the destination centre that pixel is the source centre, which renders floor. Witnessed at t2: (16,16) stayed 5 while its 24 neighbours turned 9. This matters because it is the only reading under which the winning cell is enterable: lattice (8,7) is rows 50-54 cols 44-48 and its centre (52,46) renders colour 9, the socket pip. The map places something at a hole-centre exactly twice -- that pip and the knob's centre pixel at (10,40) -- which I read as the designer saying the body acts through its aperture, and record as a reading, not a law."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_socket_is_a_keyhole_and_names_the_winning_position "Rows 49-55 by cols 43-49 form a 7x7 colour-9 bracket: top bar row 49 cols 43-49, bottom bar row 55 cols 43-49, right wall col 49 rows 50-54, and col 43 rows 50-54 is FLOOR, so it is open on the left. Inside it one lone colour-9 pixel at (52,46). Overlay the body standing in lattice (8,7): flush on three sides, pip showing through the aperture. That is a plug and a socket drawn to the pixel, and it names the winning position without my guessing a goal predicate -- the game is won when the 24 ring pixels of rows 50-54 cols 44-48 render 9. The bracket has never changed in six frames, so it is board and no object owns it; the first time the body enters, those 24 pixels become dynamic and the manual can finally speak about them."
    [depends: the_hole_is_an_aperture_and_only_the_ring_needs_floor  probe: pending]

  theorem the_socket_is_unreachable_until_the_comb_opens "Flood from spawn and the body reaches eleven lattice cells: (1,2),(1,3),(1,4),(1,5),(2,2),(2,4),(3,2),(3,3),(3,4),(4,2),(5,2). The socket (8,7) is not among them and nothing in R=7 or R=8 is, because every route south crosses (6,2) and 23 of that cell's 25 pixels render colour 8. The comb is not an obstacle to route around, it is the door. Its wiring is drawn in the open: colour 8 leaves the comb along row 40 from col 14 to col 40, climbs col 40 through rows 12 to 39, and ends in a 3x3 colour-8 knob at rows 9-11 cols 39-41 with a stem pixel at (12,40), all inside lattice (1,6). Not one colour-8 pixel has moved in six frames, which is why 8 is board and not an object; the first colour-8 pixel that changes turns this theorem into physics and hands me a rule."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_knob_is_the_only_thing_within_reach_and_i_do_not_know_how_it_is_pressed "Ten of the eleven reachable cells are bounded by floor and void alone. The eleventh, (1,5) at rows 8-12 cols 32-36, is separated from the knob's cell (1,6) only by separator col 37, which is floor. Lattice (1,6) contains ten colour-8 pixels, nine of them ring pixels of that cell, so even under the aperture rule the body cannot stand there while 8 is solid. Either 8 is walkable and key2_body_arrives is wrong at the knob; or the knob answers to proximity from (1,5); or it answers to a key never pressed. My rules make the first self-announcing: if the body is driven into a colour-8 cell my manual predicts it stays put, and the world says otherwise in one command."
    [depends: the_socket_is_unreachable_until_the_comb_opens  probe: pending]

  theorem two_actions_have_never_been_pressed_and_one_of_them_may_be_a_click "actions_used is ACTION1..ACTION5 plus RESET; the alphabet is ACTION1..ACTION7. Two commands are entirely unconstrained, and in this family one is normally a click carrying coordinates. That matters here: the knob is a 3x3 target the body appears unable to stand on, and a click is the shape of interaction that presses it. I cannot write such a rule -- the guard language admits act=key(6) but has nowhere to put two coordinates, so a click rule would fire on every click anywhere and be silently wrong about which cell was clicked. If a click drives this world my manual can record its EFFECT, comb pixels going 8 to 5, and never its precondition. Note that the five-key reading I hold -- 2 down, 3 and 4 left and right, and up being 1 or 5 -- accounts for every key I have pressed, which makes 6 and 7 more likely to be a click and a spare than more directions."
    [depends: the_action_map_after_five_transitions  probe: pending]

  theorem the_goal_section_is_absent_on_purpose "Still absent, and the reason has not weakened. `Cart.pos = exit_cell` needs one named instance and `arc-instances: all` gives me Glyph9_r8c14 and thirty-six siblings. The socket interior has never changed, so it is board and count() has nothing to range over there, and the pip (52,46) will never become dynamic because the body's aperture leaves it rendering 9. The 24 ring cells do become dynamic on first entry, but `count(Vacated, color = 9) = 24` would then be true of the body standing anywhere it has already been, which is not a win -- a goal true in the wrong states is worse than no goal, because it stops a planner at its first step. Until the body has stood in lattice (8,7) once, the playbook steers by lattice distance, and `is_goal -> False` is the honest compilation."
    [depends: the_socket_is_a_keyhole_and_names_the_winning_position  probe: pending]

  theorem what_the_engines_gave_me "mdl_segmenter scores NEGATIVE on both variants, -5042 and -17520 bits, so its segmentation loses to writing the pixels out and I owe it nothing structural. Its six tracks are a useful audit and every one of them is already inside a type I declared: obj0 (colour 9, 8 cells, 3x3, all 6 frames) is slot 1's ring; obj2 (colour 9, 3 cells, 1x3) is underline 1; obj1 (colour 1, 9 cells, present 5 frames) is slot 2 solid, absent from frame 5 exactly because state B recolours it; obj5 (colour 2, 8 cells, first seen at frame 5) is slot 1 dimmed -- independent corroboration, from an engine that knows nothing of my rules, that the panel toggled at t5 and that my landmark bug was a bug and not a physics error; obj4 is the whole 64-cell row-63 bar of which 2 cells are dynamic; obj3 is a 1006-cell colour-null blob that swallowed the maze floor AND the body ring, a fair description of my board plus the one thing I care about most. THAT ABSENCE IS THE FINDING: connected_components(4) cannot see the mover at all, because the mover is a ring of floor-adjacent pixels that merges with the floor. None of these gets a type of its own -- a second type on the same pixels invites the double claim rule 5 forbids. zero_space self-reports THIN in its own words: 5 transitions constrain rank 3 of 365 features, null space dimension 362, 'nearly every vector in it is a law that is true over these states and unfalsified rather than confirmed'. Its single global law is my census. cegis_miner's refusal remains the most useful sentence any engine has produced: 'the world does not narrate as one mover'. True of the arm, false of the world -- there is one mover, a rigid 24-pixel ring, and the arm can only see 24 simultaneous recolours, which is why movement costs me a pair of rules per direction instead of one moved() event."
    [probe: passed]

  theorem what_i_predict_before_i_see_it "Written in advance so it can cost me. ACTION3 FROM SPAWN AT COMMAND INDEX 6: my manual predicts ZERO changed cells. If exactly one cell changes and it is (63,61), parity wins, my two burn rules are coincidence-fits and I delete them next round in favour of silence. If 48 cells change, ACTION3 is right, the body is at lattice (1,3), and I owe two new rules that the transition itself witnesses. If 49 change, both at once. If zero change, ACTION3 is left AND action-keying survives, and ACTION4 is right by elimination. ACTION5 FROM SPAWN, if anyone presses it: I predict zero changed cells outside row 63, on the strength of the spawn_probe guard and nothing else in this window -- any panel change there refutes the guard and means the toggle is bound to something I have not found. ACTION2 FROM SPAWN: 24+24 cells at rows 8-24 and a burn at (63,61) that my manual will NOT draw, because meter_burn_key2_next is out for want of a witness; one wrong pixel is the advertised price of that removal."
    [depends: the_one_command_that_settles_two_questions, why_i_keep_the_spawn_probe_guard_on_a_window_that_cannot_test_it  probe: pending]
```

=== PLAYBOOK ===
```
# playbook.dsl -- what to buy with the next command, not a route.
#
# STATE OF PLAY: body home at lattice (1,2), panel in state B, 2 meter cells
# burned, 6 commands spent, next command index 6 (EVEN).
#
# WHAT CHANGED THIS ROUND:
#   (a) THE MANUAL'S FAILURE WAS A COMMENT, NOT A STRATEGY. The 23-cell
#       divergence was an unplaced landmark. No playbook line caused it and
#       none is retracted for it. New line: before ranking any probe, check
#       that the rules it is meant to test can actually fire.
#   (b) COST IS NO LONGER KNOWN TO BE UNIFORM. The window shrank and the
#       evidence that killed action-keying went with it; parity and
#       action-keying are both 5/5 here. So "free probe" is a distinction
#       that may or may not exist, and I rank by information and let the
#       same command settle the cost question as a by-product.
#   (c) THE EAST KEY IS STILL THE ONLY BLOCKING QUESTION, and the body is
#       standing on the one cell that separates ACTION3 from ACTION4: left
#       is void, right is open floor.
#   (d) ONE PRESS IS ONE LATTICE CELL, 1/1 -- the cascade is animation.
#       Every distance below is counted in lattice cells, not pixels.
# No stored sequence anywhere: every line is a criterion on the current
# frame plus the manual's own open questions.

order     settle_the_east_key_before_routing_toward_the_knob              [proof: lean]
order     probe_a_key_from_a_cell_where_exactly_one_candidate_is_open     [proof: lean]
order     prefer_a_command_that_settles_two_open_questions_at_once        [proof: lean]
order     test_a_law_with_a_key_its_rival_reading_says_is_silent          [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it      [proof: lean]
order     identify_a_direction_key_before_routing_with_it                 [proof: lean]
order     separate_two_readings_before_planning_against_either            [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it              [proof: lean]
order     reach_the_switch_before_testing_the_switch                      [proof: lean]
order     try_an_unpressed_key_before_declaring_a_dead_end                [proof: lean]
order     witness_a_rule_before_writing_it                                [proof: lean]
order     spend_commands_on_information_while_the_bar_is_still_long       [proof: lean]

prune     destination_ring_pixels_are_not_all_floor => dead               [proof: lean]
prune     action_excluded_for_this_direction_by_an_earlier_no_op => dead  [proof: lean]
prune     route_that_crosses_the_comb_while_it_still_reads_eight => dead  [proof: lean]
prune     key5_pressed_at_spawn_where_both_readings_say_no_op => dead     [proof: lean]
prune     probe_where_both_live_readings_predict_the_same_pixel => dead   [proof: lean]
prune     probe_that_repeats_a_key_at_a_cell_that_cannot_separate_it => dead [proof: lean]
prune     guard_whose_landmark_carries_no_arc_cell_comment => dead        [proof: lean]
prune     meter_exhausted and not goal => dead                            [proof: lean]

heuristic lattice_distance_to_the_knob_while_the_gate_is_shut             [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open            [admissible: lean]
heuristic live_readings_a_command_can_eliminate                           [admissible: lean]
heuristic open_questions_a_command_can_close                              [admissible: lean]
heuristic cells_this_command_makes_ownable_for_the_first_time             [admissible: lean]
heuristic unwitnessed_rules_this_command_would_witness                    [admissible: lean]
heuristic commands_remaining_under_the_worse_of_the_two_meter_readings    [admissible: lean]
heuristic unexplained_cells_after_redraw                                  [admissible: lean]

prefer    an_untested_direction_key_where_its_two_candidates_disagree     [ev: 3/5 no_ops]
prefer    a_command_whose_rival_readings_predict_different_pixels         [ev: 2/5 burns]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                [ev: 5/5 diffs]
prefer    a_step_that_both_advances_and_witnesses_an_unwritten_rule       [ev: 1/1 moves]
prefer    a_step_toward_the_knob_over_a_step_toward_the_socket            [ev: 1/1 levels]
prefer    stay_on_the_lattice_row_that_reaches_the_knob                   [ev: 1/1 levels]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered         [ev: 1/1 levels]
prefer    an_unpressed_key_over_repeating_a_known_no_op                   [ev: 2/7 keys]
prefer    a_cell_the_body_has_never_stood_in_over_one_it_has              [ev: 2/11 cells]
prefer    distance_from_spawn_that_makes_up_and_return_to_start_differ    [ev: 1/1 key5]
```

=== LOG ===
```json
[
  {"id": "S-01", "subject": "replay_mismatch at t=4, ACTION5, 23 cells", "verdict": "accept",
   "as": "landmark spawn_probe placed at (8, 14)",
   "why": "The 23 wrong cells are exactly the panel and the manual predicted state A where the world produced state B; all thirteen panel rules are guarded by colored(spawn_probe, 5) and the landmark carried '# arc-cell: carried, coordinates stripped', which is not a coordinate, so per the grammar it landed at (0,0), which is background 0 in every frame, so the guard was false everywhere and the rules were unreachable — one comment fixes it and t5 then replays 71 cells, matching the brief."},

  {"id": "L-01", "subject": "coverage tags citing t6..t13", "verdict": "reject",
   "why": "This brief contains 6 states and 5 transitions; every ev tag was recomputed against t0..t5 and the counts fell by the factor of repeated presses (key2_body_leaves 72/72 -> 24/24), because a coverage claim naming a transition the certifier cannot see is a lie it cannot catch."},

  {"id": "R-01", "subject": "key5_slot1_lights, key5_underline1_lights, key5_slot2_ring_resets, key5_slot2_centre_resets, key5_underline2_dims", "verdict": "probe-pending",
   "why": "The B-to-A half of the panel toggle has no witness in this window (t5 is the only ACTION5 and it went A to B), so all five leave rules: and are written verbatim in the_five_rules_i_no_longer_have_a_witness_for, with the advertised price of 23 wrong cells on the next effective ACTION5 from state B."},

  {"id": "R-02", "subject": "meter_burn_key2_next", "verdict": "probe-pending",
   "why": "Its only witnesses were second and third key-2 presses this window does not contain; it is inert at t2 anyway because row 63 is wholly colour 9 there, so removing it costs nothing on replay and one pixel on the next burning ACTION2, which I state in advance."},

  {"id": "R-03", "subject": "meter_burn_key2_rightmost, meter_burn_key4_next", "verdict": "accept",
   "why": "Witnessed 1/1 each at t2 and t4, disjoint from key2_body_leaves because a row-63 instance has no sixth below() on the board, and they are the only expressible form of the meter — I keep them knowing they may be coincidence, precisely so that command 6 can refute them."},

  {"id": "R-04", "subject": "key2_body_leaves / key2_body_arrives / key5_body_clears / key5_body_respawns", "verdict": "accept",
   "why": "t2 gives 24+24+1 = 49 changed cells and the brief says 49; t5 gives 24+24+23 = 71 and the brief says 71; the guards are position-free colour tests plus one six-cell offset, which is the whole content of 'the body is a rigid 5x5 ring that moves one lattice cell'."},

  {"id": "O-01", "subject": "mdl_segmenter obj0 (colour 9, 8 cells, 3x3, 6 frames)", "verdict": "entailed",
   "as": "Glyph9 instances at rows 1-3 cols 1-3", "why": "slot 1's hollow ring; its 9th cell (2,2) is colour 0 in both configurations and is therefore board, which is why the track has 8 cells and not 9."},

  {"id": "O-02", "subject": "mdl_segmenter obj1 (colour 1, 9 cells, present 5 of 6 frames)", "verdict": "entailed",
   "as": "Spent", "why": "slot 2's solid block, absent from frame 5 exactly because state B recolours all nine cells — the engine's frames_present count is independent corroboration of the toggle."},

  {"id": "O-03", "subject": "mdl_segmenter obj2 (colour 9, 3 cells, 1x3)", "verdict": "entailed",
   "as": "Glyph9 instances at row 5 cols 1-3", "why": "underline 1; typed by frame-0 colour 9, discriminated from slot 1 by above^6 = wall and colored(above^4, 9)."},

  {"id": "O-04", "subject": "mdl_segmenter obj3 (colour null, 1006 cells, 50x38)", "verdict": "reject",
   "why": "It is the maze floor merged with the body ring under connected_components(4); it never varies as a whole, so it is board — and the fact that no track isolates the mover is the engine's real finding, not a defect of my types."},

  {"id": "O-05", "subject": "mdl_segmenter obj4 (colour 9, 64 cells, 1x64)", "verdict": "entailed",
   "as": "board plus 2 Glyph9 instances", "why": "row 63 is the meter bar; only (63,63) and (63,62) have ever changed, so 62 of its cells are constant and get no instance, which is what makes count(Glyph9) = 37 rather than 99."},

  {"id": "O-06", "subject": "mdl_segmenter obj5 (colour 2, 8 cells, first_frame 5)", "verdict": "entailed",
   "as": "Glyph9 rendering 2 in state B", "why": "colour 2 is a rendering of slot 1's ring, not a fifth object; giving it its own type would put two owners on the same eight pixels and violate the exclusivity constraint."},

  {"id": "O-07", "subject": "cegis_miner verdict 'the world does not narrate as one mover'", "verdict": "accept",
   "why": "True of the arm and false of the world: the mover is a rigid 24-pixel ring the arm can only see as 24 simultaneous recolours, which is why every direction costs a leaves-rule plus an arrives-rule instead of one moved() event, and why its per-track refusals are all 'recolor'/'vanish'."},

  {"id": "L-02", "subject": "zero_space global law and THIN self-report", "verdict": "entailed",
   "why": "Its cell list is my 73 dynamic cells to the pixel and it says of itself that 5 transitions constrain rank 3 of 365 features, so its laws are unfalsified rather than confirmed; it restates dynamic_census and adds nothing I can act on."},

  {"id": "L-03", "subject": "cascade_lengths [1, 7, 9]", "verdict": "accept",
   "as": "theorem the_cascade_is_animation_and_one_press_is_one_lattice_cell",
   "why": "The 7-frame command moved the body six rows and the 1-frame commands moved nothing, so the extra frames are one animated row each; and since the body stopped after six rows with open floor beneath it, a press is one lattice cell rather than a slide until blocked."},

  {"id": "L-04", "subject": "the meter reading", "verdict": "probe-pending",
   "why": "Within t0..t5 action-keying (burn iff key 2 or 4) and command parity (burn iff even index) both score 5/5; only action-keying is expressible, so it is what the rules encode, and command index 6 with an odd-numbered key separates them in one pixel."},

  {"id": "L-05", "subject": "ACTION1 = up versus ACTION5 = up", "verdict": "probe-pending",
   "why": "ACTION1 was only pressed where up is void and ACTION5 only from one cell below home, so 'up' and 'return to start' produce the identical pixel there; two lattice cells of distance separates them and nothing cheaper does."},

  {"id": "P-01", "subject": "ACTION3 from spawn at command index 6", "verdict": "probe-pending",
   "why": "Its four possible diffs — 0, 1, 48, 49 cells — are four different pairs of answers to the two open questions (which key is east, and whether the meter is keyed or parity), and my manual predicts 0 in advance so every other outcome costs me something specific."},

  {"id": "E-01", "subject": "command parity as a guard", "verdict": "reject",
   "why": "The guard vocabulary has no command counter and the frame carries no phase pixel, so the reading that may well be true is unwritable; I wrote the expressible rival into rules: and the parity reading into a theorem that names the pixel which would refute my own rules."},

  {"id": "E-02", "subject": "a click action carrying coordinates", "verdict": "reject",
   "why": "act=key(6) parses but has nowhere to put a row and column, so a click rule would fire on every click anywhere; recorded as a theorem saying I can only ever record a click's effect, never its precondition."},

  {"id": "E-03", "subject": "a goal predicate for the socket", "verdict": "reject",
   "why": "arc-instances: all leaves no single named instance for Cart.pos = exit_cell, the socket interior is constant and so has nothing for count() to range over, and count(Vacated, color = 9) = 24 would be true of the body standing anywhere it has already been — a goal true in the wrong states stops a planner at its first step, so goal: stays absent."}
]
```
```
