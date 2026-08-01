# call-001-theorize-round1

model: `claude-opus-5` · 530104 ms · $1.573059 · usage {"cache_creation": {"ephemeral_1h_input_tokens": 40322, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 40322, "cache_read_input_tokens": 0, "inference_geo": "not_available", "input_tokens": 2, "iterations": [{"cache_creation": {"ephemeral_1h_input_tokens": 40322, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 40322, "cache_read_input_tokens": 0, "input_tokens": 2, "output_tokens": 45604, "type": "message"}], "output_tokens": 45604, "server_tool_use": {"web_fetch_requests": 0, "web_search_requests": 0}, "service_tier": "standard", "speed": "standard"}

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
    "ms": 19,
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
# theory.dsl -- world observed for 34 states / 33 transitions
# (RESET + A1 A2 A3 A4 A5, then A2 A5 twelve times, then A5 A5 A5 A5).
# 87 cells have ever changed; this manual names and owns all 87.
#
# WHAT THIS ROUND COST AND WHAT IT BOUGHT
#
#   Last round I deleted `colored(spawn_probe, 5)` from thirteen panel rules
#   on a gain-test argument, and said in as many words: my manual now
#   predicts key(5) at spawn toggles 23 panel cells, no frame has ever
#   tested that, if it is wrong I pay 23 pixels and learn something worth
#   more than 23 pixels. THE WORLD ANSWERED. Four commands, all ACTION5,
#   all at spawn, indices 30-33. The panel did not move. Not one panel
#   pixel changed in four presses. THE CUT WAS WRONG AND IT IS REVERSED:
#   the guard is restored on all thirteen rules, and it now has what it
#   never had before -- FOUR NEGATIVE WITNESSES. 13 toggles with the body
#   away, 0 toggles with the body home. The atom is earned.
#
#   THE SAME FOUR COMMANDS SETTLED THE OTHER OPEN QUESTION, and settled it
#   the other way. Row 63 now reads 9 through col 47 and 1 from col 48:
#   SIXTEEN burns, two more than at state 29. Four presses of an ODD key,
#   at indices 30, 31, 32, 33, burned exactly twice -- at 30 and at 32.
#   Reading A (burns iff the key is 2 or 4) predicted ZERO burns and is
#   DEAD. Reading B (burns iff the command index is even) predicted exactly
#   two, in exactly those places, and is now 33/33 with a discriminating
#   set. The meter is a command counter and no key touches it.
#
#   AND THE FOUR COMMANDS PROVED THE THING I HAVE CARRIED AS A BELIEF SINCE
#   STATE 5. s30 and s31 are pixel-identical (distinct_states 30 against 34
#   states = four coincidences: s1=s0, s3=s2, s31=s30, s33=s32). From s30
#   the world was given ACTION5 and returned s31 = s30, identity. From s31,
#   the same pixels, the world was given ACTION5 AGAIN and returned s32,
#   one pixel burned. SAME STATE, SAME ACTION, DIFFERENT SUCCESSOR. This
#   world is NOT a function of the drawn frame, and constraint 5 obliges my
#   manual to be one. See the_world_is_not_a_function_of_the_drawn_frame.
#
#   THE BILL, STATED PLAINLY: replay can no longer be perfect. t31 and t33
#   replay exactly (identity). t30 and t32 each miss by ONE pixel, the
#   parity burn, which no guard in this language can express and which was
#   board at the instant it burned. Expect 31/33. That is the floor, not a
#   defect I can repair, and I would rather post it than hide it behind an
#   action-keyed burn rule that is now known to be a mis-attribution.

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
  Glyph9  [segment: dynamic_colour_9 ev: t0-t33 compress: 51]
  Vacated [segment: dynamic_colour_5 ev: t2-t29 compress: 24]
  Spent   [segment: dynamic_colour_1 ev: t5,t7,t9,t11,t13,t15,t17,t19,t21,t23,t25,t27,t29 compress: 9]
  Dark    [segment: dynamic_colour_0 ev: t5,t7,t9,t11,t13,t15,t17,t19,t21,t23,t25,t27,t29 compress: 3]

rules:
  rule key2_body_leaves forall ?p in Glyph9 [ev: t2,t6,t8,t10,t12,t14,t16,t18,t20,t22,t24,t26,t28 cov: 312/312]
    when act=key(2) and colored(?p, 9) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule key2_body_arrives forall ?v in Vacated [ev: t2,t6,t8,t10,t12,t14,t16,t18,t20,t22,t24,t26,t28 cov: 312/312]
    when act=key(2) and colored(?v, 5) and colored(above(above(above(above(above(above(?v)))))), 9) then recolored(?v, 9)

  rule meter_burn_key2_rightmost forall ?p in Glyph9 [ev: t2 cov: 1/1]
    when act=key(2) and colored(?p, 9) and rightof(?p) = wall then recolored(?p, 1)

  rule meter_burn_key2_next forall ?p in Glyph9 [ev: t6,t8,t10,t12,t14,t16,t18,t20,t22,t24,t26,t28 cov: 12/12]
    when act=key(2) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule meter_burn_key4_next forall ?p in Glyph9 [ev: t4 cov: 1/1]
    when act=key(4) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule key1_inert_at_spawn forall ?p in Glyph9 [ev: t1 cov: 1/1]
    when act=key(1) and colored(spawn_probe, 9) and colored(?p, 9) and colored(above(?p), 5) and colored(leftof(?p), 5) and colored(rightof(?p), 9) then recolored(?p, 9)

  rule key3_inert_below_spawn forall ?v in Vacated [ev: t3 cov: 1/1]
    when act=key(3) and colored(spawn_probe, 5) and colored(?v, 9) and colored(above(?v), 5) and colored(leftof(?v), 5) and colored(rightof(?v), 9) then recolored(?v, 9)

  rule key5_body_clears forall ?v in Vacated [ev: t5,t7,t9,t11,t13,t15,t17,t19,t21,t23,t25,t27,t29 cov: 312/312]
    when act=key(5) and colored(?v, 9) then recolored(?v, 5)

  rule key5_body_respawns forall ?p in Glyph9 [ev: t5,t7,t9,t11,t13,t15,t17,t19,t21,t23,t25,t27,t29 cov: 312/312]
    when act=key(5) and colored(?p, 5) and colored(above(?p), 5) then recolored(?p, 9)

  rule key5_slot1_dims forall ?p in Glyph9 [ev: t5,t9,t13,t17,t21,t25,t29 cov: 56/56]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 9) and above(above(above(above(?p)))) = wall then recolored(?p, 2)

  rule key5_underline1_dims forall ?p in Glyph9 [ev: t5,t9,t13,t17,t21,t25,t29 cov: 21/21]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 9) and colored(above(above(above(above(?p)))), 9) and above(above(above(above(above(above(?p)))))) = wall then recolored(?p, 0)

  rule key5_slot2_row1_lights forall ?s in Spent [ev: t5,t9,t13,t17,t21,t25,t29 cov: 21/21]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(?s)) = wall then recolored(?s, 9)

  rule key5_slot2_row3_lights forall ?s in Spent [ev: t5,t9,t13,t17,t21,t25,t29 cov: 21/21]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and colored(above(above(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_row2_left_lights forall ?s in Spent [ev: t5,t9,t13,t17,t21,t25,t29 cov: 7/7]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(?s)))))) = wall then recolored(?s, 9)

  rule key5_slot2_row2_right_lights forall ?s in Spent [ev: t5,t9,t13,t17,t21,t25,t29 cov: 7/7]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and colored(leftof(leftof(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_centre_darkens forall ?s in Spent [ev: t5,t9,t13,t17,t21,t25,t29 cov: 7/7]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(leftof(?s))))))) = wall and colored(leftof(?s), 1) then recolored(?s, 0)

  rule key5_underline2_lights forall ?d in Dark [ev: t5,t9,t13,t17,t21,t25,t29 cov: 21/21]
    when act=key(5) and colored(spawn_probe, 5) and colored(?d, 0) and colored(above(above(?d)), 1) and colored(above(above(above(above(?d)))), 1) then recolored(?d, 9)

  rule key5_slot1_lights forall ?p in Glyph9 [ev: t7,t11,t15,t19,t23,t27 cov: 48/48]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 2) then recolored(?p, 9)

  rule key5_underline1_lights forall ?p in Glyph9 [ev: t7,t11,t15,t19,t23,t27 cov: 18/18]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 0) and above(above(above(above(above(above(?p)))))) = wall then recolored(?p, 9)

  rule key5_slot2_ring_resets forall ?s in Spent [ev: t7,t11,t15,t19,t23,t27 cov: 48/48]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 9) then recolored(?s, 1)

  rule key5_slot2_centre_resets forall ?s in Spent [ev: t7,t11,t15,t19,t23,t27 cov: 6/6]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 0) then recolored(?s, 1)

  rule key5_underline2_dims forall ?d in Dark [ev: t7,t11,t15,t19,t23,t27 cov: 18/18]
    when act=key(5) and colored(spawn_probe, 5) and colored(?d, 9) then recolored(?d, 0)

goal:

laws:
  invariant glyph9_instances count(Glyph9) = 51 [status: counted]
  invariant vacated_instances count(Vacated) = 24 [status: counted]
  invariant spent_instances count(Spent) = 9 [status: counted]
  invariant dark_instances count(Dark) = 3 [status: counted]
  invariant board_cells count(board) = 4009 [status: counted]
  invariant meter_cells_burned count(Glyph9, color = 1) = 16 [status: counted]

  theorem the_cut_is_reversed_and_the_guard_is_now_earned "THE ROUND'S FIRST STRUCTURAL CHANGE AND IT IS AN UNDO OF MINE. Last round I deleted colored(spawn_probe, 5) from thirteen panel rules, on the argument that its thirteen positive witnesses were confounded -- every ACTION5 in history had followed an ACTION2, so `key(5) was pressed` and `the body is away` were the same thirteen events, and constraint 3 says a conjunct with no discriminating negative explains no pixel. THE ARGUMENT WAS SOUND AND THE CONCLUSION WAS FALSE, and the difference between those two sentences is the whole value of this round. The manual then predicted 23 panel cells for key(5) at spawn; the world was asked four times and answered zero panel cells four times. THE ATOM NOW HAS FOUR NEGATIVE WITNESSES -- t30, t31, t32, t33, all ACTION5, all with the body home at spawn, all with the panel unmoved in configuration B, confirmed cell by cell in the current frame which still reads 222/2.2/222 at cols 1-3 and 999/9.9/999 at cols 5-7 with row 5 dark at 1-3 and lit at 5-7. So the guard is restored on all thirteen rules and it is no longer a correlation: 13/13 toggles with the body away, 0/4 with the body home. WHAT I WOULD DO AGAIN: buy a negative witness by removing an unearned guard, because an unwitnessed silence is invisible and an unwitnessed prediction of change is answered in one press. WHAT I WOULD DO DIFFERENTLY: the answer arrived on the FIRST press and the next three bought nothing new about the panel -- they were paid for by the meter, which is the only reason this round was not a waste."
    [depends: key5_slot1_lights, key5_slot2_ring_resets, the_panel_is_a_marker_that_alternates_between_two_slots  probe: passed]

  theorem the_meter_is_command_parity_and_no_key_touches_it "SETTLED, and settled against the reading my rules encode. Row 63 is a 64-cell colour-9 bar burning 9 to 1 one cell at a time from the right; the current frame reads 9 through col 47 and 1 from col 48 to col 63, SIXTEEN burns after thirty-three commands. Burns occurred at command indices 2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32 -- every even index, sixteen of them, no odd index ever. READING A said burns iff the key is 2 or 4. READING B said burns iff the index is even. For twenty-nine commands the two were numerically identical because every command was an even key at an even index or an odd key at an odd index; I said the separator was one odd key at an even index and cost one command. THIS ROUND SPENT FOUR ODD KEYS AT INDICES 30-33 AND READING A PREDICTED ZERO BURNS. Two burns happened, at 30 and 32, exactly where B says. READING A IS DEAD. The meter counts commands, not keys, and it does not care which key. CONSEQUENCE FOR MY THREE BURN RULES: their attribution is now KNOWN FALSE. I keep them anyway and say why -- they are the shortest expressible shadow of the true law, they draw 14 of the 16 burns on replay, and every alternative is worse. A key(5) burn rule would fire at t31 and t33 where nothing burned; an action-free burn rule would fire at every odd index from t5 on and lose seventeen transitions. Fourteen right, two structurally unreachable, and no better option inside this grammar."
    [depends: meter_burn_key2_next, meter_burn_key4_next, the_world_is_not_a_function_of_the_drawn_frame  probe: passed]

  theorem the_world_is_not_a_function_of_the_drawn_frame "PROVEN THIS ROUND, after carrying it as a belief since state 5. The proof needs two pixel-identical states from which the SAME action produced different successors, and the store hands me the pair: distinct_states is 30 against 34 states, so there are exactly four coincidences, and they are s1=s0, s3=s2, s31=s30, s33=s32. The first two are the old sterile pair -- different keys were pressed from each, so they test nothing. THE LAST TWO ARE NOT. Refutations P-25 and P-26 report the SAME observed hash 132f0bf441d96376, and P-27 and P-28 the same 121cbbc9c93803ed: so s31 = s30 and s33 = s32 to the pixel. Now read the transitions. t31 acted on s30 with ACTION5 and returned s31, which equals s30 -- identity. t32 acted on s31, THE SAME PIXELS, with ACTION5 AGAIN, and returned s32, which differs by one burned bar cell. Same state, same action, two different successors. The hidden bit is the command counter the meter reads and no guard in this language can. WHAT IT COSTS ME IS EXACT AND UNAVOIDABLE: constraint 5 obliges my manual to be a function of the frame, so my manual must be wrong about at least one member of every such pair, and it is wrong about t30 and t32 by exactly one pixel each. Expect replay 31/33 and do not read those two as repairable."
    [depends: the_meter_is_command_parity_and_no_key_touches_it  probe: passed]

  theorem the_four_refutations_are_one_experiment_and_it_paid_for_itself "P-25 through P-28 are four reports of ONE experiment: ACTION5 pressed four times at spawn. Their arithmetic is worth reading because it is how I reconstructed the round. The manual prediction of P-25 is the inert field of P-26 and vice versa -- that is the harness rolling my predicted frame forward without resyncing, so my toggled panel became my next starting point and toggled back, the same closed 2-cycle as the last five rounds. What is NEW is the observed column: P-25 and P-26 observed the same hash, P-27 and P-28 observed the same hash. The world's successors were change, no-change, change, no-change, and the changes are one pixel each at indices 30 and 32. THREE THINGS FELL OUT OF FOUR COMMANDS: the panel guard is earned (four negatives), the meter is command parity (reading A refuted), and the world is not a function of the frame (a pixel-identical pair with the same key and different successors). Compare the six rounds before it: twenty-four refutations, every divergence set a subset of the meter's leading edge, ZERO rules contradicted, nothing learned. A prediction the world can answer is worth more than a prediction that is safe, and this is the evidence for that claim rather than the slogan."
    [depends: the_cut_is_reversed_and_the_guard_is_now_earned, the_meter_is_command_parity_and_no_key_touches_it  probe: passed]

  theorem silence_is_a_prediction_and_exactly_two_of_my_spawn_silences_are_still_forged "The compiled transition function is total: where no rule fires the successor equals the current state, so my manual never says `I do not know`, it says `nothing happens`, in the same voice it uses for things it has seen. Audit the five keys at spawn after this round. key(1) inert: WITNESSED, t1, zero cells. key(2) moves 48 body cells: witnessed thirteen times. key(5) inert: WITNESSED FOUR TIMES, t30-t33, which is the round's gain -- it was an unwitnessed prediction of change last round and it is now a witnessed silence. key(3) inert: NO WITNESS at spawn, pressed once ever, at t3, from one cell south. key(4) inert: NO WITNESS at spawn, pressed once ever, at t4, from one cell south. TWO OF FIVE SILENCES AT SPAWN ARE FORGED DEATH CERTIFICATES and the elimination is now tight enough to say more: ACTION2 is down, ACTION1 is not east (t1, spawn, east open, nothing moved), ACTION5 is not east (t30-t33, spawn, east open, nothing moved). So EAST IS ACTION3 OR ACTION4, one of my two forged silences is FALSE, and one press of either settles which -- if it steps it is east, if it does not the other is east by elimination. That is the cheapest unclaimed bit on the board."
    [depends: the_action_map_after_thirtythree_transitions, the_cut_is_reversed_and_the_guard_is_now_earned  probe: pending]

  theorem the_action_map_after_thirtythree_transitions "WITNESSED: ACTION2 IS DOWN, 13/13, six rows south, one lattice cell. ACTION5 returns the body from lattice (2,2) to (1,2), 13/13, and does NOTHING at spawn, 4/4. NEGATIVE INFORMATION, stated as negative. At spawn (1,2) up and left are void while down and right are open floor; ACTION1 did nothing there at t1, so ACTION1 IS NEITHER DOWN NOR RIGHT; ACTION5 did nothing there four times, so ACTION5 IS NEITHER DOWN NOR RIGHT either. At (2,2) up was open (the body had just vacated rows 8-12) and down was open (rows 20-24 are floor) while left and right were void; ACTION3 and ACTION4 each did nothing there, so NEITHER IS UP AND NEITHER IS DOWN. One assignment survives that invents nothing: ACTION1 up, ACTION2 down, ACTION3 left, ACTION4 right, ACTION5 something else -- and the something-else is now constrained too, see what_action5_is. The conventional mapping for this action family agrees, which is a prior and not evidence. THIRTY-THREE COMMANDS AND NOT ONE HAS TESTED THE EAST KEY. The test is one press from where the body stands."
    [depends: key2_body_arrives, key5_body_respawns, the_cascade_is_animation_and_one_press_is_one_lattice_cell  probe: pending]

  theorem what_action5_is_after_four_presses_at_home "Three readings survived thirteen presses because all thirteen were made from one cell south of spawn, where UP, UNDO and RETURN are indistinguishable. This round pressed it FOUR TIMES AT SPAWN and the body did not move a pixel. UP predicts exactly that -- north of spawn is void, the move is blocked. RETURN predicts exactly that -- the body is already home. UNDO in its plain form is REFUTED: t29 was an effective ACTION5 that carried the body home, so an undo at t30 would have carried it back south, and it did not. UNDO survives only in a stack variant where no-ops are not pushed and t29 emptied the stack; I record that variant rather than pretend it is dead, but I no longer rank it. THE SEPARATOR IS NOW CHEAP AND NAMED: press ACTION5 from any cell that is neither spawn nor one south with open floor above it. From lattice (1,3), one step east, UP is void so UP predicts nothing while RETURN predicts a 48-pixel jump west to spawn. That is one more reason the east key is the next thing to buy. The coupling I still cannot break is the panel's: it toggles on every effective ACTION5 and on no ineffective one, so it is a counter of ACTION5's successes, and the 7-versus-9 cascade split says its state is not merely cosmetic."
    [depends: the_panel_is_a_marker_that_alternates_between_two_slots, the_cut_is_reversed_and_the_guard_is_now_earned  probe: pending]

  theorem the_panel_guard_is_earned_but_its_extrapolation_is_not "The restored guard reads colored(spawn_probe, 5), which is `cell (8,14) renders floor`, which is `the body is not at spawn`. Every one of the thirteen positives had the body at ONE specific cell, lattice (2,2), and every one of the four negatives had it at spawn. So a guard reading `the body is at (2,2)` -- a second landmark at (14,14) tested for colour 9 -- fits the same 13 positives and the same 4 negatives EXACTLY as well. The two guards differ only at cells the body has never occupied: from a third cell, spawn_probe says the panel toggles and a south_probe would say it does not. I choose spawn_probe because it is the guard that already replayed twenty-five transitions and because the panel reads as a counter of effective ACTION5s rather than of one location, but I am naming the confound BEFORE it costs me, unlike last round. THE PROBE: get the body to any third lattice cell and press ACTION5. Panel toggles, spawn_probe wins; panel still, the guard is really about (2,2) and thirteen rules need a different landmark."
    [depends: key5_slot1_dims, the_cut_is_reversed_and_the_guard_is_now_earned  probe: pending]

  theorem the_panel_is_a_marker_that_alternates_between_two_slots "PROVEN over THIRTEEN toggles -- every odd index t5 through t29 -- 23 cells every time; ACTION2 has never touched a panel pixel in thirteen presses; and ACTION5 AT HOME has never touched one in four presses. CONFIGURATION A: slot 1 at rows 1-3 cols 1-3 is a hollow colour-9 ring, its underline at row 5 cols 1-3 lit 9; slot 2 at rows 1-3 cols 5-7 is a SOLID colour-1 block, its underline at row 5 cols 5-7 dark 0. CONFIGURATION B, which states 29 through 33 and the current frame all show: slot 1 a hollow colour-2 ring with dark underline, slot 2 a hollow colour-9 ring with dark centre and lit underline. mdl_segmenter corroborates by frame index and has never seen my rules: colour-1 nine-cell tracks obj1 (0-4), obj6 (7-8), obj8 (11-12), obj10 (15-16), obj12 (19-20), obj14 (23-24), obj16 (27-28); colour-2 tracks obj5 (5-6), obj7 (9-10), obj9 (13-14), obj11 (17-18), obj13 (21-22), obj15 (25-26), obj17 (29 onward, and note it is the ONLY colour-2 track to run past two frames -- five frames, 29 through 33, which is the panel standing still for this round's four commands). Its obj0 (colour 9, eight cells, 3x3, all 34 frames) and obj2 (colour 9, 1x3, all 34) persist while it narrates 26 MOVE events: the hollow ring and the lit underline do not appear and vanish, they TRAVEL between the two slots. One marker, two seats, colour 9 marks the occupied seat. What the seats HOLD is still unknown and I will not guess. I cannot model it as a mover either: the arm gives one instance per cell and moved(o, dir) moves one cell, so an eight-pixel ring travelling four columns is not a move, and ten recolour rules are the shortest thing this DSL can say."
    [depends: key5_slot1_dims, key5_slot1_lights  probe: passed]

  theorem the_cascade_length_is_a_free_channel_that_i_discard_by_construction "cascade_lengths are 1, 7 and 9. ACTION2 returned SEVEN frames from configuration A (t2, t8, t12, t16, t20, t24, t28) and NINE from configuration B (t6, t10, t14, t18, t22, t26), 13/13 with no exception. ACTION5 returned nine frames on all thirteen effective presses; every no-op returned one. THE NET EFFECT IS IDENTICAL IN ALL THIRTEEN ACTION2 PRESSES, so this costs nothing in replay and buys nothing in prediction, and it remains the only evidence that the panel does anything besides display. I record it as a limitation of my own semantics: cascade single_frame compares only the net, so up to eight intermediate frames per command are discarded unread. LIVE PREDICTION, now that the panel is confirmed stuck in configuration B: the next ACTION2 from spawn must take NINE internal frames. Seven would mean the panel's effect on the animation is not what I think, and it would cost me nothing to find out because the diff is free."
    [depends: key2_body_arrives, the_panel_is_a_marker_that_alternates_between_two_slots  probe: passed]

  theorem the_meter_edge_saturates_the_refutation_channel_and_parity_makes_it_worse "A law of this manual rather than of this world, and now the most expensive fact on the board. Each of the 64 cells of the row-63 bar burns EXACTLY ONCE, advancing leftward. At the instant a cell burns it has never changed, so it is board, so no instance exists for it, so NO RULE OF MINE CAN DRAW IT. Therefore my burn rules have zero predictive value on the leading edge and full value on replay -- a division of labour, not a contradiction. WHAT PARITY ADDS: before this round I could tell myself that only keys 2 and 4 burned, so a refutation on key 5 meant something. Now I know EVERY EVEN-INDEX COMMAND BURNS, whatever the key, so every even-index command is scored a refutation before it is even chosen, and refutation-fired carries ZERO information at even indices. The next index is 34, EVEN: whatever I press, (63,47) burns, I cannot draw it, and I am refuted by exactly one pixel. Read refutations by their DIVERGENCE SET; where that set is a subset of the bar's leading edge, the manual is not implicated. All twenty-eight refutations across seven rounds have been exactly that."
    [depends: meter_burn_key2_next, i_cannot_manufacture_an_instance_on_a_cell_that_has_never_changed  probe: passed]

  theorem the_meter_is_a_budget_and_it_is_now_priced_correctly "Sixteen of sixty-four bar cells consumed after thirty-three commands. Under the settled parity reading the bar buys 48 more burns and therefore about 96 MORE COMMANDS, since every second one burns. I do not know that exhaustion ends the game -- no frame has shown it -- but 96 commands against a route I can see costing about nineteen steps plus interactions plus identification probes is not the binding constraint. The route: spawn (1,2) east three cells to (1,5) beside the knob, an unknown number of interactions there, three cells back west, seven cells south down lattice column 2 to (8,2), five cells east to the socket at (8,7). THE BINDING CONSTRAINT IS THIRTY-THREE COMMANDS SPENT AND THE BODY HAVING OCCUPIED TWO LATTICE CELLS. Note that parity makes waste cheaper than I feared and repetition no cheaper: a wasted command still costs half a bar cell."
    [depends: the_meter_is_command_parity_and_no_key_touches_it, the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_two_no_op_rules_still_fail_the_gain_test_and_i_keep_them_for_a_weaker_reason "key1_inert_at_spawn and key3_inert_below_spawn each recolour one pixel to the colour it already has, each has one witness on a transition where zero cells changed, and the manual would replay identically without them. They were bought to test the alphabet hypothesis, which is refuted, so THAT reason is gone. The reason I keep them is weaker and I will not dress it up: deleting them narrows certify's adjudicated action set from five keys to three, removing information I can see for a benefit -- two lines -- I cannot measure. This round supplies a second, better reason: my one deletion of an unearned thing was reversed by the world four commands later. Conservatism about deletions is not a virtue in general, but it is the correct posture toward deletions that change NO prediction, and these two change none. They remain declared failures of the gain test and the two cheapest deletions in this manual."
    [depends: key1_inert_at_spawn, key3_inert_below_spawn, the_key_alphabet_hypothesis_is_refuted  probe: passed]

  theorem the_key_alphabet_hypothesis_is_refuted "Kept compressed, because it is settled. I once hypothesised that the command chooser derives its candidate keys from the act=key(n) literals in my rules, and that this was why round after round bought A2 A5. I paid two witnessed no-op rules to widen the alphabet. THE INSTRUMENT MOVED AS PREDICTED -- certify went from 3 actions and 54 pairs to 5 actions and now 150 pairs, 0 clashes, 0 step crashes -- and THE COMMANDS DID NOT MOVE. Alphabet width is not sufficient. What DID move the commands is now known: last round I gave key(5) at spawn a predicted 23-cell change and the chooser pressed key(5) four times. THE CHOOSER FOLLOWS THE MANUAL'S PREDICTED CHANGE. That is a lever and it is also a trap, because the honest manual after this round predicts change for exactly one key at spawn again."
    [depends: key1_inert_at_spawn, key3_inert_below_spawn  probe: passed]

  theorem the_dsl_cannot_say_unknown_and_cannot_say_parity "Two expressive holes, and this round they interlock. FIRST: there is no third outcome for a (state, action) pair -- not `no change` and not a named successor, but `unobserved, the manual declines to predict`. Rules produce events, absence of a rule produces identity, and the compiled step is total. The one lever the grammar offers is deleting an unearned guard, which converts an unwitnessed silence into an unwitnessed PREDICTION OF CHANGE, testable in one press; I used it, it was answered, and the answer was no -- which is exactly what the lever is for. SECOND: the true meter law is `burns iff the command index is even`, and the guard language reads pixels and the action name and nothing else. There is no command counter, no phase pixel, and the frame provably does not determine the parity, since s30 and s31 are identical and only one of them was followed by a burn. So the parity law CANNOT be written here at all, at any length. If a future desk gains one expressive extension, ask for a state counter before asking for `not`."
    [depends: the_world_is_not_a_function_of_the_drawn_frame, the_cut_is_reversed_and_the_guard_is_now_earned  probe: passed]

  theorem the_manual_heals_one_step_behind_and_the_meter_is_where_it_shows "The arm instances exactly the cells that have ALREADY changed, typed by their frame-0 colour: constant 4009 + dynamic 87 = 4096, and 51+24+9 = 84 = cells_needing_an_owner with the 3 colour-0 cells making up the difference to 87. Consequence: a cell that has never changed is board, no object owns it, and NO RULE CAN DRAW ITS FIRST CHANGE. This is the seventh consecutive round in which that sentence, written in advance, was the entire content of every refutation. The two cells burned this round, (63,49) and (63,48), are dynamic NOW, which is why Glyph9 went 49 to 51 and the burned count 14 to 16 -- but they were board when they burned, so t30 and t32 are one wrong pixel each even after the repair, and this time the repair does not even restore replay, because no rule of mine burns on key 5. The same arithmetic prices the first eastward step: rows 8-12 cols 20-24 have never changed, so 24 arrival pixels are undrawable no matter what rule I write, and the 24 departure pixels are undrawable until an east-leaves rule is witnessed. 48 wrong cells for the first step onto fresh ground, plus one for the parity burn if the index is even, 24 for the second step, 0 thereafter. The body also CHANGES TYPE as it walks -- Glyph9 at rows 8-12, Vacated at rows 14-18 -- because typing is by frame-0 colour and all that floor was 5."
    [depends: key2_body_arrives, dynamic_census  probe: passed]

  theorem dynamic_census "Exactly 87 cells have ever changed and every one has an owner. 23 are the panel: slot 1's eight ring pixels, its centre (2,2) being colour 0 in BOTH configurations and therefore board; underline 1's three at row 5 cols 1-3; slot 2's nine at rows 1-3 cols 5-7, centre included because (2,6) is 1 in A and 0 in B; underline 2's three at row 5 cols 5-7. 24 are the spawn ring, rows 8-12 cols 14-18 minus the aperture (10,16), which never changes and is board. 24 are the same ring six rows south, rows 14-18 cols 14-18 minus its aperture (16,16). 16 are the burned right end of row 63: cols 48 through 63, two more than last round. 23+24+24+16 = 87 = dynamic_cells. By frame-0 colour: 51 colour-9 (8 slot-1 ring + 3 underline-1 + 24 spawn ring + 16 meter), 9 colour-1 (slot 2 solid), 24 colour-5 (the lower ring, floor at frame 0), 3 colour-0 (underline 2). 51+9+24 = 84 = cells_needing_an_owner exactly, and 4096-87 = 4009 = constant_cells exactly."
    [probe: passed]

  theorem the_rules_i_still_have_no_witness_for_and_will_not_write "Three holes, each with its text ready so the transition that witnesses it costs one paste and not one round of rediscovery. (1) A SECOND DESCENT. The body has descended thirteen times and all thirteen started at spawn, so no rule turns Vacated pixels from 9 back to 5 on an ACTION2: rule key2_floor_leaves forall ?v in Vacated when act=key(2) and colored(?v, 9) and colored(below-six(?v), 5) then recolored(?v, 5). One ACTION2 from lattice (2,2) buys it. (2) EAST-WEST MOTION. Whatever the east key is, it needs a pair: a leaves rule over Glyph9 guarded on colour 9 with rightof-six rendering 5, and its arrives twin typed on whichever object owns the destination pixels -- which today is NO object, because rows 8-12 cols 20-24 are board. (3) THE PARITY BURN, which is not a missing rule but an inexpressible one, and which will cost exactly one pixel on every even-index command for the rest of the game. I state all three prices in advance so none can be mistaken for a surprise."
    [depends: key2_body_arrives, the_meter_edge_saturates_the_refutation_channel_and_parity_makes_it_worse  probe: pending]

  theorem off_board_cell_terms_evaluate_false_and_that_is_load_bearing "certify reports 0 step crashes across all 150 adjudicated pairs while key2_body_leaves grounds on meter instances at row 63 whose sixth below is row 69. So colored(off-board, k) is false rather than an exception, and `<cell> = wall` is the sanctioned positive test. Thirteen rules rest on this and every row and column discrimination in the panel is built from it: the k-th above is off-board exactly when k exceeds the row, so row 1 is above-twice equals wall, row 3 is a colour test on above-twice -- false for row 1 precisely because a colour test on an off-board cell is false -- and row 2 is above-three equals wall conjoined with a colour test on above-once. The same trick separates slot 2's middle row by column: col 5 is leftof-six equals wall, col 6 is leftof-seven equals wall with a colour test on leftof-once, col 7 is a colour test on leftof-twice, pairwise exclusive, which is why the ambiguity check reports 0 clashes. Restoring the spawn_probe conjunct only tightens this: it narrows all thirteen panel rules by the same atom, so no pair that was exclusive before can clash now. Not one rule uses `not`, deliberately."
    [depends: key2_body_leaves, key5_slot2_centre_darkens  probe: passed]

  theorem the_cascade_is_animation_and_one_press_is_one_lattice_cell "A move is animated one row per internal frame and the world reports the whole animation for a single action; cascade single_frame compares only the net, which is identical for all thirteen ACTION2 presses (48 body cells, rows 8-18, cols 14-18) whether the command took 7 frames or 9. The refutation I keep: under a slide-until-blocked reading, ACTION2 at spawn would have run the body south through rows 20-24 and 26-30 to the comb; it stopped after exactly six rows over open floor, THIRTEEN times. ONE PRESS IS ONE LATTICE CELL, 13/13, and every distance in the playbook rests on that."
    [depends: key2_body_arrives, the_maze_is_a_six_pixel_lattice  probe: passed]

  theorem the_maze_is_a_six_pixel_lattice "Lattice cell (R,C) is rows 6R+2..6R+6 by cols 6C+2..6C+6; rows and columns congruent to 1 mod 6 are separator strips. Colour 5 is floor, 0 is void, 8 is machinery, and the body is a rigid 5x5 colour-9 block with a one-pixel aperture at its centre. Re-read pixel by pixel from the CURRENT frame and unchanged: R=1 (rows 8-12) is floor from col 13 to col 43, so C=2,3,4,5 are open, C=6 holds the knob, C=7 does not exist in this band; R=2 is floor at cols 13-19 and 25-31, so C=2 and C=4 only; R=3 is floor cols 13-31, so C=2,3,4; R=4 and R=5 are floor only at cols 13-19, so C=2; R=6 is the comb, whose only floor pixels are (39,14) and (41,14), so nothing there is enterable; R=7 is C=2, plus a fragment of floor at row 48 cols 42-50 that is one row deep and cannot hold a body; R=8 (rows 50-54) is floor from col 13 to col 48, so C=2..7 are all open. Separator rows 7,13,19,25,31,37,43,49 are floor across column 2, and separator col 37 is floor across R=1, so lattice column 2 is continuous from R=1 to R=8 apart from the comb, and lattice row 1 is continuous from C=2 to C=6. Spawn is (1,2); in thirty-four frames the body has occupied exactly TWO cells, (1,2) and (2,2), and it has been at spawn in twenty of them."
    [depends: key2_body_arrives, the_cascade_is_animation_and_one_press_is_one_lattice_cell  probe: pending]

  theorem the_hole_is_an_aperture_and_only_the_ring_needs_floor "A destination lattice cell needs its 24 RING pixels to render floor; the centre may render anything, because key2_body_arrives fires on a destination pixel only when the pixel six rows above renders 9, and at the destination centre that pixel is the source centre, which renders floor. Witnessed THIRTEEN times: (16,16) stayed 5 while its 24 neighbours turned 9. This matters because it is the only reading under which the winning cell is enterable: lattice (8,7) is rows 50-54 cols 44-48, its 24 ring pixels all render floor in the current frame, and its centre (52,46) renders colour 9, the socket pip. The map places something at a hole-centre exactly twice -- that pip and the knob's centre pixel at (10,40) -- which I read as the designer saying the body acts through its aperture, and record as a reading, not a law."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_socket_is_a_keyhole_and_names_the_winning_position "Re-verified cell by cell against the current frame. The colour-9 bracket sits entirely on SEPARATOR strips: row 49 cols 43-49, row 55 cols 43-49, col 49 rows 49-55. Rows 49 and 55 are separator rows, col 49 and col 43 are separator columns -- so what is drawn is the north, south and east walls of lattice cell (8,7), painted in colour 9, with the west wall at col 43 left as FLOOR. Inside it, rows 50-54 cols 44-48 are floor except one lone colour-9 pixel at the exact centre (52,46). Outside it, col 50 rows 49-56 is a one-cell strip of floor that leads nowhere. Overlay the body standing in lattice (8,7) -- 5x5, aperture at its centre: flush against three walls, pip showing through the aperture. That is a plug and a socket drawn to the pixel, and it names the winning position without my guessing a goal predicate -- the game is won when the 24 ring pixels of rows 50-54 cols 44-48 render 9. The bracket has never changed in thirty-four frames, so it is board and no object owns it; the first time the body enters, those 24 pixels become dynamic and the manual can finally speak about them."
    [depends: the_hole_is_an_aperture_and_only_the_ring_needs_floor  probe: pending]

  theorem the_socket_is_unreachable_until_the_comb_opens "Flood from spawn and the body reaches eleven lattice cells: (1,2),(1,3),(1,4),(1,5),(2,2),(2,4),(3,2),(3,3),(3,4),(4,2),(5,2). The socket (8,7) is not among them and nothing in R=7 or R=8 is, because every route south crosses (6,2) and 23 of that cell's 25 pixels render colour 8. Nor is there a second route: C=3 exists only at R=3, C=4 dead-ends at R=3, and C=5 and C=6 exist only at R=1, so lattice column 2 is the sole north-south corridor. The comb is not an obstacle to route around, it is the door. Its wiring is drawn in the open and every pixel is re-read in the current frame: a 3x3 colour-8 knob at rows 9-11 cols 39-41, a stem pixel at (12,40), colour 8 filling col 40 from row 12 down to row 40, colour 8 filling row 40 from col 14 to col 40, and the comb teeth at rows 38-42 cols 14-18. It is ONE CONNECTED WIRE from knob to gate, which is why I read the knob as the switch. Not one colour-8 pixel has moved in thirty-four frames, which is why 8 is board and not an object; the first colour-8 pixel that changes turns this theorem into physics and hands me a rule."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_knob_is_the_only_thing_within_reach_and_i_do_not_know_how_it_is_pressed "Ten of the eleven reachable cells are bounded by floor and void alone. The eleventh, (1,5) at rows 8-12 cols 32-36, is separated from the knob's cell (1,6) at cols 38-42 only by separator col 37, which is floor. Lattice (1,6) contains ten colour-8 pixels, nine of them ring pixels of that cell -- the eight knob pixels other than its centre, plus the stem at (12,40) -- so even under the aperture rule the body cannot stand there while 8 is solid. Either 8 is walkable and key2_body_arrives is wrong at the knob; or the knob answers to proximity from (1,5); or it answers to a key never pressed. My rules make the first self-announcing: if the body is driven into a colour-8 cell my manual predicts it stays put, and the world says otherwise in one command. C=2 to C=5 is THREE lattice cells of eastward travel and C=2 to C=6 is four, every step on floor that R=1 shows open. Thirty-three commands spent and none has taken step one."
    [depends: the_socket_is_unreachable_until_the_comb_opens  probe: pending]

  theorem two_actions_have_never_been_pressed_and_one_of_them_may_be_a_click "actions_used is ACTION1..ACTION5 plus RESET; the alphabet is ACTION1..ACTION7. Two commands are entirely unconstrained after thirty-four states, and in this family one is normally a click carrying coordinates. That matters here: the knob is a 3x3 target the body appears unable to stand on, and a click is the shape of interaction that presses it. I cannot write such a rule -- the guard language admits act=key(6) but has nowhere to put two coordinates, so a click rule would fire on every click anywhere and be silently wrong about which cell was clicked. If a click drives this world my manual can record its EFFECT, comb pixels going 8 to 5, and never its precondition. I have no witness for key(6) or key(7), so no rule can name them, so they sit outside the manual's alphabet -- which I once thought decisive and now know is not sufficient, since keys 1 and 3 are inside the alphabet and were still never chosen."
    [depends: the_key_alphabet_hypothesis_is_refuted  probe: pending]

  theorem the_goal_section_is_empty_on_purpose "Still empty, and the reason has not weakened. `Cart.pos = exit_cell` needs one named instance and `arc-instances: all` gives me Glyph9_r8c14 and fifty siblings. The socket interior has never changed, so it is board and count() has nothing to range over there, and the pip (52,46) will never become dynamic because the body's aperture leaves it rendering 9. The 24 ring cells of lattice (8,7) do become dynamic on first entry, but they are frame-0 colour 5 and would type as Vacated -- indistinguishable by this arm from the 24 Vacated cells at rows 14-18 -- so count(Vacated, color = 9) = 24 would be true of the body standing one cell south of spawn, which is not a win. The alternatives fail too: count(Glyph9, color = 5) = 24 is true of every state where the body is anywhere but home, and a Wire type on colour 8 would have zero instances because every colour-8 cell is constant, so count(Wire) = 0 would be true at RESET. A goal true in the wrong states is worse than no goal, because it stops a planner at its first step. I name the price plainly: is_goal compiles to False, no plan terminates, and nothing ranks one command above another except whether the command is predicted to change pixels -- which, with the guard restored, admits exactly ONE key at spawn again, and that key is the one that has been pressed thirteen times."
    [depends: the_socket_is_a_keyhole_and_names_the_winning_position, the_key_alphabet_hypothesis_is_refuted  probe: passed]

  theorem what_i_predict_before_i_see_it "Written in advance so it can cost me. The next command has index 34, EVEN, so (63,47) BURNS WHATEVER I PRESS and I cannot draw it: every option below carries exactly one guaranteed wrong pixel and refutation-fired therefore carries zero information this turn. The body is at spawn, the panel is in configuration B, sixteen meter cells are burned. ACTION3 at spawn: my manual predicts ZERO cells and has NO WITNESS for that, so this is the press I want -- 48 undrawable cells plus the burn means ACTION3 IS EAST and the map is closed; 1 cell, the burn alone, means ACTION3 is not east and therefore ACTION4 IS EAST by elimination, since ACTION1 and ACTION5 are both excluded from east at this very cell. Either answer names the east key. ACTION4 at spawn: the same experiment with the labels swapped. ACTION1 at spawn: 1 cell, key1_inert_at_spawn firing as a no-op, the silence I already have a witness for, nothing bought. ACTION5 at spawn: 1 cell, now WITNESSED four times, nothing bought. ACTION2 at spawn: 48 body cells I draw correctly plus the burn -- one wrong pixel and nothing learned, because key2_body_leaves and key2_body_arrives are at 312/312, except for one free datum, the cascade must be NINE frames from configuration B. If ACTION5 is pressed at spawn a fifth time and the panel moves, this manual is wrong twice over and I would want to know that more than anything else on this list."
    [depends: the_meter_is_command_parity_and_no_key_touches_it, silence_is_a_prediction_and_exactly_two_of_my_spawn_silences_are_still_forged  probe: pending]

  theorem a_landmark_is_only_as_true_as_the_comment_beside_it "Kept compressed because the lesson is structural and cost a full round. Thirteen panel rules once carried colored(spawn_probe, 5) while the landmark line read a prose placeholder instead of a coordinate; the grammar puts such a landmark at (0,0), (0,0) is background in every frame this world has drawn, and so all thirteen rules were unreachable text that fired never and clashed never. Responsibility passed, ambiguity passed, step crashed zero times, and ONLY replay caught it. The coda, now complete: that same atom was deleted last round for failing the gain test and is restored this round with four negative witnesses. It has been wrong by pointing nowhere, wrong by being absent, and is now right for a reason I can state. The landmark reads (8, 14), the top-left pixel of the spawn ring, which renders 9 while the body is home and 5 the moment it is anywhere else. Before ranking any probe, check that the rules it is meant to test can actually fire."
    [depends: key1_inert_at_spawn, key3_inert_below_spawn  probe: passed]

  theorem i_cannot_manufacture_an_instance_on_a_cell_that_has_never_changed "Recorded because a future desk will be tempted by the same repair I have now rejected five times. To draw the leading-edge burn I would need an instance on a board cell. The arm offers exactly one lever, arc-instances: all, and its documented behaviour is to instance every cell OF THAT COLOUR THE BOARD CANNOT EXPLAIN -- a never-varying cell is precisely what the board explains, so it gets no instance. The tempting workaround is a second declared type on colour 9 without arc-instances, hoping the arm seats one instance somewhere useful. I reject it: the arm looks objects up by colour and nothing else, so a second colour-9 type is indistinguishable from Glyph9, the seat is unspecified, and any cell it landed on would be claimed twice, which is the constraint-5 error the grammar warns about in as many words. A landmark cannot help either, because landmarks are cells and every event in the language takes an object as its first argument. So the hole is a property of the arm, it is permanent for this level, and with parity confirmed it now costs one pixel on EVERY second command rather than only on key 2 and key 4."
    [depends: the_meter_edge_saturates_the_refutation_channel_and_parity_makes_it_worse  probe: passed]

  theorem what_the_engines_gave_me "mdl_segmenter keeps a positive gain of +11940 bits at compression_ratio 0.527 on split_by_color=false, against -132740 bits when split by colour; its segmentation beats writing the pixels out and I still owe it nothing structural. Its eighteen tracks corroborate the panel by frame index and one of them corroborates THIS ROUND specifically: obj17, colour 2, first_frame 29, frames_present 5 -- the only colour-2 track longer than two frames, which is the panel standing still through t30-t33 exactly as the restored guard requires. obj0 and obj2 persisting through all 34 frames while the segmenter narrates 26 moves is the marker-with-two-seats reading. obj4 is the whole 64-cell bar of which 16 cells are now dynamic. obj3 is a 1006-cell colour-null blob that swallowed the maze floor AND the body ring: connected_components(4) cannot see the mover at all, because the mover is a ring of floor-adjacent pixels that merges with the floor, and THAT ABSENCE IS THE FINDING. None of these gets a type of its own; a second type on the same pixels invites the double claim rule 5 forbids. zero_space self-reports THIN in its own words -- 33 transitions constrain rank 17 of 435 features, null space dimension 418, nearly every vector in it a law true over these states and unfalsified rather than confirmed -- and its single global law is my census. cegis_miner refuses on every track and its verdict, `the world does not narrate as one mover`, remains true of the arm and false of the world: there is one mover, a rigid 24-pixel ring, and the arm can only see 24 simultaneous recolours."
    [probe: passed]
```

## The playbook as it stands

```
# playbook.dsl -- what to buy with the next command, not a route.
#
# ========= WHAT THE LAST FOUR COMMANDS SETTLED =========
# Four presses of ACTION5 at spawn, indices 30-33. The panel did not move.
# Two bar cells burned, at indices 30 and 32.
#
#   1. THE CUT IS REVERSED. `colored(spawn_probe, 5)` is back on thirteen
#      panel rules and it now has FOUR NEGATIVE WITNESSES: 13/13 toggles
#      with the body away, 0/4 with the body home. ACTION5 at spawn is a
#      witnessed no-op.
#   2. THE METER IS COMMAND PARITY. Four ODD keys at indices 30-33 burned
#      exactly twice, at the two EVEN indices. The action-keyed reading
#      predicted zero burns and is dead. 33/33 for parity, with a
#      discriminating set at last. No key touches the meter.
#   3. THE WORLD IS NOT A FUNCTION OF THE DRAWN FRAME -- PROVEN. s30 and
#      s31 are pixel-identical; ACTION5 from s30 returned identity and
#      ACTION5 from s31 burned a cell. Same pixels, same key, two
#      successors.
#
# The wrong prediction was worth more than six safe rounds. But only the
# FIRST of the four presses answered it; presses two, three and four were
# the harness re-choosing the same key against a rolled-forward frame, and
# they were paid for by the meter alone. Buying a negative witness is right;
# buying it four times is not.
#
# ========= THE BOARD AS THE MANUAL NOW SEES IT =========
#   At spawn (where the body IS):  key(2) -> 48 body cells
#                                  keys 1, 5 -> nothing, WITNESSED
#                                  keys 3, 4 -> nothing, NO WITNESS
#   Index 34 is EVEN, so (63,47) burns under every key and I cannot draw it:
#   one guaranteed wrong pixel this turn whatever is pressed, and
#   refutation-fired carries ZERO information at an even index.
#
# ========= THE ONE THING WORTH BUYING =========
# EAST IS ACTION3 OR ACTION4 AND ONE PRESS SETTLES IT.
#   ACTION2 is down (13/13). ACTION1 is not east -- pressed at spawn at t1
#   with east open, nothing moved. ACTION5 is not east -- pressed at spawn
#   four times this round with east open, nothing moved. Two candidates
#   remain and the body is standing where the test is free: east of spawn is
#   three lattice cells of unbroken floor, west is void.
#   Press ACTION3 (or ACTION4): if the body steps, that key is EAST and the
#   map is closed; if it does not, the OTHER is east by elimination. Both
#   outcomes name the east key. No other command on the board names anything.
#
# The advertised price of the step onto fresh ground: 48 pixels my manual
# cannot draw, because rows 8-12 cols 20-24 have never changed and are board.
# That is a refutation I have priced in advance and it must not be read as a
# defect. 24 pixels for the second step, 0 for the third.
#
# ------------------------------------------------------------------------
# STATE 33: body home at lattice (1,2); panel configuration B; SIXTEEN meter
# cells burned, cols 48-63 of row 63; next command index 34, EVEN. Eleven
# lattice cells reachable, the body has stood in TWO in thirty-four states.
# Three steps east along lattice row 1 reach the cell beside the knob; the
# knob is the far end of one connected colour-8 wire whose near end is the
# comb; the comb gates every route to the socket at (8,7). Under parity the
# bar buys about 96 more commands against a route of about nineteen steps:
# the budget is not binding, repetition is.

order     settle_the_east_key_before_anything_else_at_this_cell            [proof: lean]
order     treat_predicted_inertness_as_ignorance_unless_a_witness_backs_it [proof: lean]
order     rank_by_witnesses_a_command_would_create_not_by_pixels_it_moves  [proof: lean]
order     stop_pressing_a_key_the_moment_its_question_has_been_answered    [proof: lean]
order     buy_the_probe_that_closes_a_question_no_other_command_can_close  [proof: lean]
order     never_repeat_a_key_at_a_cell_where_its_rules_are_already_full    [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired  [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance               [proof: lean]
order     ignore_refutation_pressure_entirely_when_the_index_is_even       [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it               [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it       [proof: lean]

prune     ranked_only_because_the_manual_predicts_the_most_pixels => dead   [proof: lean]
prune     every_rule_it_would_witness_is_already_at_full_coverage => dead    [proof: lean]
prune     ranked_only_because_a_refutation_fired_on_it => dead               [proof: lean]
prune     divergence_lies_only_on_the_meter_leading_edge => dead             [proof: lean]
prune     repeats_a_key_whose_inertness_here_is_already_witnessed => dead    [proof: lean]
prune     repeats_the_key_that_the_previous_command_just_answered => dead    [proof: lean]
prune     revisits_a_lattice_cell_by_an_already_witnessed_key => dead        [proof: lean]
prune     ranked_only_to_separate_the_two_meter_readings => dead             [proof: lean]
prune     destination_ring_pixels_are_not_all_floor => dead                  [proof: lean]
prune     action_excluded_for_this_direction_by_an_earlier_no_op => dead     [proof: lean]
prune     route_that_crosses_the_comb_while_it_still_reads_eight => dead     [proof: lean]
prune     meter_exhausted and not goal => dead                               [proof: lean]

heuristic keys_whose_inertness_here_rests_on_no_witness                     [admissible: lean]
heuristic direction_labels_a_command_would_fix_by_elimination               [admissible: lean]
heuristic open_questions_a_command_can_close                                [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_meter_edge                   [admissible: lean]
heuristic lattice_cells_the_body_has_never_occupied                         [admissible: lean]
heuristic lattice_distance_to_the_knob_while_the_gate_is_shut               [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open              [admissible: lean]
heuristic live_readings_a_command_can_eliminate                             [admissible: lean]
heuristic commands_remaining_under_the_confirmed_parity_budget              [admissible: lean]

prefer    a_key_whose_predicted_inertness_here_has_never_been_witnessed    [ev: 2/5 keys at spawn]
prefer    a_key_that_names_a_direction_whichever_way_it_answers            [ev: 2/2 candidates]
prefer    a_key_never_pressed_from_the_cell_the_body_stands_on             [ev: 0/33 commands]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                 [ev: 33/33 diffs]
prefer    east_along_lattice_row_one_over_any_other_axis                   [ev: 1/1 levels]
prefer    an_unpressed_key_over_repeating_a_witnessed_no_op                [ev: 2/7 keys]
prefer    a_press_at_a_third_cell_that_splits_up_from_return               [ev: 4/4 key5_at_home]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered          [ev: 1/1 levels]
```

## Why you are being called: the surprises that fired

### replay_mismatch (empirical family -> theory.dsl)

the manual has no executable form: theory.py has not been generated

```json
{
 "beat": "certify",
 "carried": true,
 "level": 1,
 "why": "theory.dsl is non-empty but generated/theory.py could not be loaded, so nothing can replay it"
}
```


## What certify said about the manual you have now

```json
{
 "expensive": {
  "available": false,
  "detail": "no Lean form was generated",
  "ok": false,
  "state_estimate": null
 },
 "first_divergence": null,
 "proof_layer_available": false,
 "replay": {},
 "responsibility": {},
 "unambiguous": null
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
# theory.dsl -- world observed for 6 states / 5 transitions (RESET, A1 A2 A3 A4 A5).
# 73 cells have ever changed; this manual names and owns all 73.
#
# WHY THIS ROUND EXISTS AND WHAT IT COST
#
#   The only surprise fired was not empirical: theory.dsl was non-empty and
#   generated/theory.py COULD NOT BE LOADED. Nothing replayed, nothing was
#   adjudicated, responsibility and ambiguity both returned empty. A manual
#   that does not compile predicts nothing at all, so every other question
#   waited on this one.
#
#   THE FAULT AND THE FIX. The grammar says every `landmark` line must carry
#   a trailing `# arc-cell: (row, col)` and that a landmark the level cannot
#   place is a HARD compile error. The line I was handed read
#   `landmark spawn_probe  # arc-cell: carried, coordinates stripped`.
#   That is prose where a coordinate must be, and thirteen rules depended on
#   it. It now reads `# arc-cell: (8, 14)` -- the top-left pixel of the spawn
#   ring, which renders 9 while the body is home and 5 the moment it is not.
#   I also DELETED the empty `goal:` section rather than leave a section
#   header with no body: the grammar sanctions having no goal section at all,
#   and does not sanction an empty one. Two edits, both structural, neither
#   about the world.
#
#   THE SECOND THING I FOUND IS LARGER. The manual I was handed is written
#   against 34 states, 33 transitions and 87 dynamic cells. The evidence
#   brief for THIS level reports 6 states, 5 transitions, 73 dynamic cells,
#   two burned meter cells and distinct_states 4 (s1=s0 and s3=s2 -- the two
#   no-ops, nothing more). Those are not the same observation. Every `ev:`
#   tag past t5 and every coverage past this window was a claim no frame in
#   front of me witnesses, and constraint 2 does not let me keep them. So
#   the rules are re-derived from t0-t5 alone and re-counted cell by cell.
#   The map theorems survive untouched because they are read off the CURRENT
#   FRAME rather than off history, and I re-verified every one of them pixel
#   by pixel this round. The longer history's findings that this window
#   cannot witness are demoted to `probe: pending` and named as such.
#
#   WHAT I GAVE UP BY DOING THAT, STATED PLAINLY. Five panel rules for the
#   reverse toggle (configuration B back to A) are gone: this window shows
#   exactly ONE panel toggle, A to B at t5, so the return direction has zero
#   witnesses. Their text is preserved in the_panel_toggle_is_witnessed_in_
#   one_direction_only so that the transition which witnesses them costs one
#   paste. The price is 23 cells I will fail to draw on the next effective
#   ACTION5. I would rather pay it than tag an unwitnessed rule with t5.
#
#   EXPECTED REPLAY: 5/5. Every one of the 73 dynamic cells is owned, every
#   changed cell in all five diffs is fired by exactly one rule, and no rule
#   fires on a cell that did not change. If it is not 5/5 the likeliest
#   single cause is Dark: colour 0 is the background, and the brief's own
#   cells_needing_an_owner is 70 rather than 73, which is 73 minus exactly
#   the three colour-0 cells. See dark_may_have_no_instances.

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
  Vacated [segment: dynamic_colour_5 ev: t2-t5 compress: 24]
  Spent   [segment: dynamic_colour_1 ev: t5 compress: 9]
  Dark    [segment: dynamic_colour_0 ev: t5 compress: 3]

events:
  event recolored(o, c)

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
  invariant dark_instances count(Dark) = 3 [status: unverified]
  invariant board_cells count(board) = 4023 [status: counted]
  invariant meter_cells_burned count(Glyph9, color = 1) = 2 [status: counted]

  theorem the_compile_failure_was_a_landmark_comment_and_nothing_else "The only surprise this round was replay_mismatch with the reason that theory.dsl is non-empty but generated/theory.py could not be loaded. That is a parse or generation failure, not a wrong belief about the world, and until it is fixed no rule in this manual has any executable meaning. I found two places where the text I was handed departs from the stated grammar. FIRST, and I believe decisive: the grammar says EVERY landmark line must carry a trailing arc-cell comment naming a row and a column, and that a landmark the level cannot place is a HARD compile error. The line read spawn_probe with the comment carried, coordinates stripped -- prose in the slot where a coordinate must be. It now reads (8, 14). SECOND: the manual carried a bare goal: header with an empty body, while the grammar sanctions having NO goal section and says nothing about an empty one; sections take bodies indented by at least one space, so a header with no body line is the kind of thing a line-oriented parser rejects. I removed the section rather than argue about it. I cannot prove which of the two was fatal because certify returned no error text, only that loading failed -- so I fixed both and I say openly that this is a repair by inspection against the grammar, not a repair against a diagnostic."
    [depends: a_landmark_is_only_as_true_as_the_comment_beside_it  probe: pending]

  theorem the_manual_i_was_handed_describes_a_longer_history_than_the_evidence "Stated first because it explains every deletion below. The manual I inherited is written against 34 states, 33 transitions, 87 dynamic cells, 16 burned meter cells and distinct_states 30. The store in front of me reports 6 states, 5 transitions, 73 dynamic cells, 2 burned meter cells, distinct_states 4, and cells_needing_an_owner 70. The current frame agrees with the store and not with the manual: row 63 reads 9 through col 61 and 1 at cols 62 and 63, exactly two burns. The four coincidences the inherited manual leaned on to prove the world is not a function of the frame do not exist here; this window has exactly two, s1=s0 and s3=s2, and they are the sterile pair, because different keys were pressed from each. So I re-derive every rule from t0-t5 and re-count every invariant, and where the longer history claimed something this window cannot witness I keep the claim as a theorem with probe: pending rather than as a rule with an invented ev tag. What I do NOT discard is the map: the lattice, the comb, the knob and the socket are read off the current frame, and I re-verified all four pixel by pixel this round."
    [depends: dynamic_census  probe: passed]

  theorem dynamic_census "Exactly 73 cells have ever changed and every one has an owner. 23 are the panel: slot 1 at rows 1-3 cols 1-3 contributes its 8 ring pixels, its centre (2,2) rendering colour 0 in both configurations and therefore board; underline 1 is row 5 cols 1-3, three cells; slot 2 at rows 1-3 cols 5-7 contributes all NINE cells, centre included, because (2,6) is 1 in configuration A and 0 in B; underline 2 is row 5 cols 5-7, three cells. 24 are the spawn ring, rows 8-12 cols 14-18 minus the aperture (10,16), which never changes and is board. 24 are the same ring six rows south, rows 14-18 cols 14-18 minus its aperture (16,16). 2 are the burned right end of row 63, cols 62 and 63. 23+24+24+2 = 73 = dynamic_cells, and zero_space lists exactly those cells and no others. By frame-0 colour: 37 colour-9 (8 slot-1 ring + 3 underline-1 + 24 spawn ring + 2 meter), 9 colour-1 (slot 2 solid in configuration A), 24 colour-5 (the lower ring, floor at frame 0), 3 colour-0 (underline 2 dark at frame 0). 37+9+24 = 70 = cells_needing_an_owner exactly, and 4096-73 = 4023 = constant_cells exactly."
    [probe: passed]

  theorem dark_may_have_no_instances "The one arithmetic gap in the census and I will not hide it. cells_needing_an_owner is 70 while dynamic_cells is 73, and the difference is precisely the three colour-0 cells of underline 2. Colour 0 is the background, and the arm instances every cell of a declared colour THE BOARD CANNOT EXPLAIN; whether a dynamic cell whose frame-0 colour is the background counts as explained is not something I can settle from the brief. If Dark seats three instances, key5_underline2_lights draws (5,5), (5,6) and (5,7) at t5 and replay is 5/5. If Dark seats none, that rule can never fire, those three pixels are drawn as background at state 5, and t5 is wrong by exactly three cells -- while the responsibility check, which counts against the 70, does not flag them. I keep the declaration because it is weakly dominant: it costs three lines, it is correct under one reading and inert under the other, and no alternative owner exists for those cells inside this arm."
    [depends: dynamic_census  probe: pending]

  theorem the_meter_reading_is_two_readings_and_this_window_cannot_split_them "Row 63 is a 64-cell colour-9 bar burning 9 to 1 one cell at a time from the right. Two cells have burned: (63,63) at t2 under ACTION2, (63,62) at t4 under ACTION4. READING A says a burn happens iff the key is 2 or 4. READING B says a burn happens iff the command index is even. Over t1-t5 the two are numerically IDENTICAL -- key 2 at index 2, key 4 at index 4, keys 1, 3 and 5 at odd indices 1, 3, 5 -- so 5 transitions of evidence separate them not at all, and any claim that one is settled is a claim about a history this window does not contain. I encode reading A because it is the only one this grammar can express: the guard language reads pixels and the action name, and there is no command counter and no phase pixel. THE SEPARATOR IS CHEAP AND IT IS AVAILABLE ON THE VERY NEXT COMMAND. Index 6 is EVEN. Press any key other than 2 or 4 and reading A predicts no burn while reading B predicts (63,61) turns 1. One press decides it, and it is the same press I want for a different reason -- see the_east_key_is_action3_or_action4."
    [depends: meter_burn_key2_rightmost, meter_burn_key4_next  probe: pending]

  theorem the_burn_rule_i_cannot_write_yet "meter_burn_key2_rightmost fires only on the rightmost bar cell, because at t2 nothing to its right existed to test. The general shape -- burn the colour-9 cell whose right neighbour is already 1 -- is witnessed exactly once, at t4, under key 4, and that is meter_burn_key4_next. The twin under key 2 has NO witness in this window and is therefore not in the rules section. Its text is ready: rule meter_burn_key2_next forall ?p in Glyph9 when act=key(2) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1). The price of not writing it is exact: the next ACTION2 burns (63,61) and I will be wrong by that one pixel. One ACTION2 buys the rule."
    [depends: meter_burn_key2_rightmost  probe: pending]

  theorem the_panel_toggle_is_witnessed_in_one_direction_only "This window contains ONE panel toggle, at t5, and it runs configuration A to configuration B. CONFIGURATION A, states 0 through 4: slot 1 is a hollow colour-9 ring, underline 1 lit 9, slot 2 a SOLID colour-1 block, underline 2 dark 0. CONFIGURATION B, state 5 and the current frame: slot 1 a hollow colour-2 ring, underline 1 dark, slot 2 a hollow colour-9 ring with a dark centre, underline 2 lit 9. Eight rules draw that toggle and they draw all 23 cells. THE RETURN JOURNEY HAS ZERO WITNESSES and I refuse to tag it t5. Five rules are therefore missing and I name them so the transition that witnesses them costs one paste: key5_slot1_lights over Glyph9 on colour 2 to 9; key5_underline1_lights over Glyph9 on colour 0 with above-six equal to wall, to 9; key5_slot2_ring_resets over Spent on colour 9 to 1; key5_slot2_centre_resets over Spent on colour 0 to 1; key5_underline2_dims over Dark on colour 9 to 0. THE PRICE, ADVERTISED: the next effective ACTION5 changes 23 panel cells I will not draw. mdl_segmenter corroborates the toggle without seeing my rules -- its obj0 is an 8-cell 3x3 colour-9 track present in all six frames, its obj1 a 9-cell colour-1 track present in frames 0-4 and vanishing, its obj5 an 8-cell colour-2 track first seen at frame 5 -- and it narrates 2 MOVE events and 1 vanish and 1 appear, which is a marker with two seats travelling, not two objects blinking."
    [depends: key5_slot1_dims, key5_slot2_row1_lights  probe: pending]

  theorem the_spawn_probe_guard_is_carried_and_is_currently_inert "Eight panel rules carry colored(spawn_probe, 5), which reads cell (8,14) renders floor, which reads the body is not at home. In THIS window that atom has one positive witness and no negative: key(5) has been pressed once, at t5, with the body away. The longer history I was handed claims four negative witnesses for it and I cannot cite them here. So why keep it? Because right now it changes NO prediction, and I can show that cell by cell: with the panel in configuration B, slot 1 renders 2 and not 9, underline 1 renders 0 and not 9, slot 2 renders 9 and not 1, underline 2 renders 9 and not 0, so every one of the eight rules is already blocked by its colour test whatever the body is doing. The guard becomes load-bearing only when the panel is back in configuration A, and by then I will have witnessed the return toggle and can test the guard properly. It is a free carry, not an earned atom, and I mark the difference."
    [depends: key5_slot1_dims  probe: pending]

  theorem the_action_map_after_five_transitions "WITNESSED: ACTION2 is DOWN. At t2 the body moved six rows south, one lattice cell, 48 cells, 1/1. ACTION5 moved it six rows NORTH again at t5, 1/1 -- which is consistent with ACTION5 being UP and equally consistent with its being RETURN or UNDO, and one witness cannot split those. NEGATIVE INFORMATION, stated as negative and read off the map. At spawn, lattice (1,2), north is void (row 2 col 14 is 0) and west is void (cols 8-12 are 0) while EAST is open floor (rows 8-12 cols 20-24 all render 5) and SOUTH is open. ACTION1 was pressed there at t1 and nothing changed, so ACTION1 IS NEITHER EAST NOR SOUTH. At lattice (2,2) after the descent, north was open (the body had just vacated rows 8-12) and south was open (rows 20-24 are floor) while east and west are void (rows 14-18 cols 20-24 are 0). ACTION3 at t3 and ACTION4 at t4 each moved nothing, so NEITHER IS NORTH AND NEITHER IS SOUTH. Combine: ACTION2 is south, ACTION1 is not east, ACTION5 moved north. EAST IS ACTION3 OR ACTION4 and there is no third candidate. FIVE COMMANDS SPENT AND NOT ONE HAS TESTED THE EAST KEY, at a cell where east is three unbroken lattice cells of floor."
    [depends: key2_body_arrives, key5_body_respawns, the_cascade_is_animation_and_one_press_is_one_lattice_cell  probe: pending]

  theorem the_east_key_is_action3_or_action4_and_one_press_names_it "The cheapest unclaimed bit on the board, and it is cheap twice over. The body is at spawn. My manual predicts ZERO cells for ACTION3 there -- key3_inert_below_spawn needs colored(spawn_probe, 5) and the body is home, so (8,14) renders 9 and the rule cannot fire -- and that silence has NO witness at this cell. If ACTION3 steps the body east, ACTION3 is east and the map closes. If it does not, ACTION4 is east by elimination, since ACTION1, ACTION2 and ACTION5 are each excluded from east by a witnessed transition. Either answer names the key. AND THE SAME PRESS SPLITS THE METER: index 6 is even, key 3 is neither 2 nor 4, so reading A predicts no burn and reading B predicts (63,61) burns. One command, two questions, both closed. I state the price in advance so no part of it can be mistaken for a defect: rows 8-12 cols 20-24 have NEVER changed, so they are board, no instance exists there, and the 24 arrival pixels are undrawable by any rule I could write today; the 24 departure pixels are Glyph9 instances but no east-leaves rule is witnessed, so they are undrawn too. 48 wrong cells for the first step onto fresh ground, 24 for the second, 0 thereafter."
    [depends: the_action_map_after_five_transitions, the_meter_reading_is_two_readings_and_this_window_cannot_split_them  probe: pending]

  theorem silence_is_a_prediction_and_three_of_my_spawn_silences_are_forged "The compiled transition function is total: where no rule fires the successor equals the current state, so my manual never says I do not know, it says nothing happens, in the same voice it uses for things it has seen. Audit the five keys at spawn. key(2) moves 48 body cells: witnessed, t2. key(1) inert: WITNESSED, t1, zero cells changed. key(3) inert: NO WITNESS at spawn -- pressed once, at t3, from one cell south. key(4) inert at spawn: NO WITNESS -- pressed once, at t4, from one cell south, where it burned a meter cell and moved nothing. key(5) inert at spawn: NO WITNESS AT ALL in this window; ACTION5 has been pressed exactly once, at t5, from one cell south, where it was effective. THREE OF FIVE SILENCES AT SPAWN ARE FORGED DEATH CERTIFICATES, and two of the three are the east candidates. This is the argument for pressing one of them and against pressing ACTION2 again."
    [depends: key1_inert_at_spawn, key3_inert_below_spawn, the_action_map_after_five_transitions  probe: pending]

  theorem the_two_no_op_rules_fail_the_gain_test_and_i_say_so "key1_inert_at_spawn and key3_inert_below_spawn each recolour one pixel to the colour it already has, each has exactly one witness, and each witnesses a transition on which zero cells changed. The manual would replay identically without them: constraint 3 is failed outright and I am not going to dress it up. The reason I keep them is smaller than the rule text: they put key(1) and key(3) into the manual's action alphabet, which is what certify adjudicates over, and deleting them removes information I can see for a saving -- four lines -- I cannot measure. They change no prediction, so keeping them cannot cost a pixel, and they are the two cheapest deletions in this manual if a later desk wants them gone."
    [depends: key1_inert_at_spawn, key3_inert_below_spawn  probe: passed]

  theorem off_board_cell_terms_evaluate_false_and_that_is_load_bearing "key2_body_leaves grounds on meter instances at row 63 whose sixth-below is row 69, and it must not fire there. It does not, because colored(off-board, k) is FALSE rather than an exception, and <cell> = wall is the sanctioned positive test. Every row and column discrimination in the eight panel rules is built from that one fact: the k-th above is off-board exactly when k exceeds the row, so panel row 1 is above-twice equals wall; row 3 is a colour test on above-twice, false for row 1 precisely because a colour test on an off-board cell is false; row 2 is above-three equals wall conjoined with a colour test on above-once. The same trick separates slot 2's middle row by column -- col 5 is leftof-six equals wall, col 6 is leftof-seven equals wall with a colour test on leftof-once, col 7 is a colour test on leftof-twice -- and those three are pairwise exclusive, which is what keeps constraint 5 satisfied on (2,5), (2,6) and (2,7). I checked the one case that looks dangerous: leftof-seven from col 5 is also off-board, so centre_darkens and row2_left_lights are separated NOT by that atom but by colored(leftof(?s), 1), which is false at col 5 because (2,4) is a separator rendering 0. Not one rule uses not, deliberately."
    [depends: key5_slot2_centre_darkens, key2_body_leaves  probe: passed]

  theorem the_cascade_is_animation_and_one_press_is_one_lattice_cell "cascade_lengths are 1, 7 and 9. ACTION2 returned SEVEN frames at t2, from configuration A. ACTION5 returned NINE at t5. Every no-op returned one. A move is animated one row per internal frame and the world reports the whole animation for a single action; cascade single_frame compares only the net, so up to eight intermediate frames per command are discarded unread, and I record that as a limitation of my own semantics rather than of the world. The refutation I keep: under a slide-until-blocked reading, ACTION2 at spawn would have run the body south through rows 20-24 and 26-30 to the comb. It stopped after exactly six rows over open floor. ONE PRESS IS ONE LATTICE CELL, and every distance in the playbook rests on that one transition -- which is thin, and I say so."
    [depends: key2_body_arrives  probe: passed]

  theorem the_maze_is_a_six_pixel_lattice "Lattice cell (R,C) is rows 6R+2..6R+6 by cols 6C+2..6C+6; rows and columns congruent to 1 mod 6 are separator strips. Colour 5 is floor, 0 is void, 8 is machinery, and the body is a rigid 5x5 colour-9 block with a one-pixel aperture at its centre. Re-read pixel by pixel from the CURRENT frame this round. R=1 (rows 8-12) is floor from col 13 to col 43, so C=2,3,4,5 are open and C=6 holds the knob. R=2 (rows 14-18) is floor at cols 13-19 and 25-31 only, so C=2 and C=4. R=3 (rows 20-24) is floor cols 13-31, so C=2,3,4. R=4 and R=5 are floor only at cols 13-19, so C=2. R=6 is the comb, whose only floor pixels are (39,14) and (41,14), so nothing there is enterable. R=7 is C=2, plus a fragment of floor at row 48 cols 42-50 that is one row deep and cannot hold a body. R=8 (rows 50-54) is floor from col 13 to col 48, so C=2..7 are open. Separator rows 7,13,19,25,31,37,43,49 are floor across column 2 and separator col 37 is floor across R=1, so lattice column 2 is continuous from R=1 to R=8 apart from the comb, and lattice row 1 is continuous from C=2 to C=6. Spawn is (1,2); in six frames the body has occupied exactly TWO cells, (1,2) and (2,2)."
    [depends: the_cascade_is_animation_and_one_press_is_one_lattice_cell  probe: pending]

  theorem the_hole_is_an_aperture_and_only_the_ring_needs_floor "A destination lattice cell needs its 24 RING pixels to render floor; the centre may render anything, because key2_body_arrives fires on a destination pixel only when the pixel six rows above renders 9, and at the destination centre that pixel is the source centre, which renders floor. Witnessed at t2: (16,16) stayed 5 while its 24 neighbours turned 9. This matters because it is the only reading under which the winning cell is enterable: lattice (8,7) is rows 50-54 cols 44-48, its 24 ring pixels all render floor in the current frame, and its centre (52,46) renders colour 9, the socket pip. The map places something at a hole-centre exactly twice -- that pip and the knob's centre pixel at (10,40) -- which I read as the designer saying the body acts through its aperture, and record as a reading, not a law."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_socket_is_a_keyhole_and_names_the_winning_position "Re-verified cell by cell against the current frame. The colour-9 bracket sits entirely on SEPARATOR strips: row 49 cols 43-49, row 55 cols 43-49, col 49 rows 49-55. Rows 49 and 55 are separator rows and cols 49 and 43 are separator columns, so what is drawn is the north, south and east walls of lattice cell (8,7) painted in colour 9, with the west wall at col 43 left as FLOOR. Inside it, rows 50-54 cols 44-48 are floor except one lone colour-9 pixel at the exact centre (52,46). Outside it, col 50 rows 49-56 is a one-cell strip of floor that leads nowhere. Overlay the body standing in lattice (8,7) -- 5x5, aperture at its centre: flush against three walls, pip showing through the aperture. That is a plug and a socket drawn to the pixel, and it names the winning position without my guessing a goal predicate: the game is won when the 24 ring pixels of rows 50-54 cols 44-48 render 9. The bracket has never changed in six frames, so it is board and no object owns it; the first time the body enters, those 24 pixels become dynamic and the manual can finally speak about them."
    [depends: the_hole_is_an_aperture_and_only_the_ring_needs_floor  probe: pending]

  theorem the_socket_is_unreachable_until_the_comb_opens "Flood from spawn and the body reaches eleven lattice cells: (1,2),(1,3),(1,4),(1,5),(2,2),(2,4),(3,2),(3,3),(3,4),(4,2),(5,2). The socket (8,7) is not among them and nothing in R=7 or R=8 is, because every route south crosses (6,2) and 23 of that cell's 25 pixels render colour 8. Nor is there a second route: C=3 exists only at R=3, C=4 dead-ends at R=3, and C=5 and C=6 exist only at R=1, so lattice column 2 is the sole north-south corridor. The comb is not an obstacle to route around, it is the door. Its wiring is drawn in the open and every pixel is re-read in the current frame: a 3x3 colour-8 knob at rows 9-11 cols 39-41, a stem pixel at (12,40), colour 8 filling col 40 from row 12 down to row 40, colour 8 filling row 40 from col 14 to col 40, and the comb teeth at rows 38-42 cols 14-18. It is ONE CONNECTED WIRE from knob to gate, which is why I read the knob as the switch. Not one colour-8 pixel has moved in six frames, which is why 8 is board and not an object; the first colour-8 pixel that changes turns this theorem into physics and hands me a rule."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_knob_is_the_only_thing_within_reach_and_i_do_not_know_how_it_is_pressed "Ten of the eleven reachable cells are bounded by floor and void alone. The eleventh, (1,5) at rows 8-12 cols 32-36, is separated from the knob's cell (1,6) at cols 38-42 only by separator col 37, which is floor. Lattice (1,6) contains ten colour-8 pixels, nine of them ring pixels of that cell -- the eight knob pixels other than its centre, plus the stem at (12,40) -- so even under the aperture rule the body cannot stand there while 8 is solid. Either 8 is walkable and key2_body_arrives is wrong at the knob; or the knob answers to proximity from (1,5); or it answers to a key never pressed. My rules make the first self-announcing: if the body is driven into a colour-8 cell my manual predicts it stays put, and the world says otherwise in one command. C=2 to C=5 is THREE lattice cells of eastward travel and C=2 to C=6 is four, every step on floor that R=1 shows open. Five commands spent and none has taken step one."
    [depends: the_socket_is_unreachable_until_the_comb_opens  probe: pending]

  theorem i_cannot_manufacture_an_instance_on_a_cell_that_has_never_changed "Recorded because it is the permanent shape of every refutation this level will produce. To draw the leading-edge burn, or the first step onto fresh ground, I would need an instance on a board cell. The arm offers exactly one lever, arc-instances: all, and its documented behaviour is to instance every cell of that colour THE BOARD CANNOT EXPLAIN -- a never-varying cell is precisely what the board explains, so it gets no instance. The tempting workaround is a second declared type on colour 9 without arc-instances, hoping the arm seats one instance somewhere useful. I reject it: the arm looks objects up by colour and nothing else, so a second colour-9 type is indistinguishable from Glyph9, its seat is unspecified, and any cell it landed on would be claimed twice, which is the constraint-5 error the grammar warns about in as many words. A landmark cannot help either, because landmarks are cells and every event in the language takes an object as its first argument. So the manual heals ONE STEP BEHIND the world, permanently, and the correct way to read a refutation here is by its divergence set: where that set lies on cells that had never changed before the transition, the manual is not implicated."
    [depends: dynamic_census  probe: passed]

  theorem the_dsl_cannot_say_unknown_and_cannot_say_parity "Two expressive holes. FIRST: there is no third outcome for a (state, action) pair -- not no change and not a named successor, but unobserved, the manual declines to predict. Rules produce events, absence of a rule produces identity, and the compiled step is total. So every one of the three unwitnessed spawn silences is being asserted by my manual in the same voice as the two witnessed ones, and only the audit in silence_is_a_prediction distinguishes them. SECOND: if the meter turns out to run on command parity, that law CANNOT be written here at any length, because the guard language reads pixels and the action name and there is no command counter and no phase pixel. I encode the action-keyed reading because it is the expressible one, and I have named the single press that decides between them. If a future desk gains one expressive extension, ask for a state counter before asking for not."
    [depends: the_meter_reading_is_two_readings_and_this_window_cannot_split_them  probe: pending]

  theorem there_is_no_goal_section_and_that_is_deliberate "Cart.pos = exit_cell needs one named instance and arc-instances: all gives me Glyph9_r8c14 and thirty-six siblings, none of which is the body. The socket interior has never changed, so it is board and count has nothing to range over there, and the pip (52,46) will never become dynamic because the body's aperture leaves it rendering 9. The 24 ring cells of lattice (8,7) do become dynamic on first entry, but their frame-0 colour is 5, so they would type as Vacated -- indistinguishable by this arm from the 24 Vacated cells at rows 14-18 -- and count(Vacated, color = 9) = 24 is true of the body standing one cell south of spawn, which is not a win. The alternatives fail too: count(Glyph9, color = 5) = 24 is true of every state where the body is anywhere but home, and a Wire type on colour 8 would have zero instances because every colour-8 cell is constant, so count(Wire) = 0 would be true at RESET. A goal true in the wrong states is worse than no goal, because it stops a planner at its first step. I name the price plainly: is_goal compiles to False, no plan terminates, and nothing ranks one command above another except whether the command is predicted to change pixels."
    [depends: the_socket_is_a_keyhole_and_names_the_winning_position  probe: passed]

  theorem two_actions_have_never_been_pressed_and_one_of_them_may_be_a_click "actions_used is ACTION1 through ACTION5 plus RESET; the alphabet is ACTION1 through ACTION7. Two commands are entirely unconstrained, and in this family one is normally a click carrying coordinates. That matters here: the knob is a 3x3 target the body appears unable to stand on, and a click is the shape of interaction that presses it. I cannot write such a rule -- the guard language admits act=key(6) but has nowhere to put two coordinates, so a click rule would fire on every click anywhere and be silently wrong about which cell was clicked. If a click drives this world my manual can record its EFFECT, comb pixels going 8 to 5, and never its precondition."
    [probe: pending]

  theorem what_the_engines_gave_me "mdl_segmenter reports NEGATIVE gain on both variants this round -- minus 5042 bits at 6 tracks and minus 17520 at 17 -- so by its own accounting its segmentation does not pay for itself over writing the pixels out, and I take nothing structural from it. What I do take is corroboration by frame index, which is independent of my rules: obj1, colour 1, nine cells, 3x3, present frames 0-4 and then gone; obj5, colour 2, eight cells, 3x3, FIRST FRAME 5; obj0, colour 9, eight cells, 3x3, present all six frames; obj2, colour 9, a 1x3 strip, present all six. Two moves, one vanish, one appear. That is a marker with two seats travelling at t5, not two ornaments blinking, and it is exactly the toggle my eight rules draw. obj4 is the whole 64-cell bar of which 2 cells are now dynamic. obj3 is a 1006-cell colour-null blob that swallowed the maze floor AND the body ring: connected_components(4) cannot see the mover at all, because the mover is a ring of floor-adjacent pixels that merges with the floor, and THAT ABSENCE IS THE FINDING. cegis_miner refuses every track and its verdict, the world does not narrate as one mover, is true of the arm and false of the world -- there is one mover, a rigid 24-pixel ring, and the arm can only see 24 simultaneous recolours. zero_space self-reports THIN in its own words: 5 transitions constrain rank 3 of 365 features, null space dimension 362, nearly every vector in it a law true over these states and unfalsified rather than confirmed. Its single global law is my census and nothing more."
    [probe: passed]

  theorem a_landmark_is_only_as_true_as_the_comment_beside_it "The lesson that cost this whole round, kept at the top of the laws it protects. A landmark whose arc-cell comment does not name a coordinate is not a landmark: the grammar calls it a hard compile error, and the manual I was handed carried prose in that slot while eight rules tested it. Responsibility, ambiguity and step-crash counts can all pass on a manual that never compiles, and they did -- certify returned empty for every check. Before ranking any probe, check that the rules it is meant to test can actually fire; before trusting any check, check that the manual it checked was loaded at all."
    [depends: the_compile_failure_was_a_landmark_comment_and_nothing_else  probe: pending]

  theorem what_i_predict_before_i_see_it "Written in advance so it can cost me. The body is at spawn, lattice (1,2). The panel is in configuration B. Two meter cells are burned, cols 62 and 63. The next command has index 6. ACTION3 at spawn: my manual predicts ZERO cells changed and has no witness for that silence. If the body steps east, ACTION3 is east, and I pay 48 pixels I have priced. If it does not step, ACTION4 is east by elimination. Either way, if (63,61) burns, reading A of the meter is dead and reading B is confirmed by a discriminating transition; if it does not burn, reading A survives its first real test. ACTION4 at spawn: the same experiment with the labels swapped. ACTION1 at spawn: predicted identity, a silence I already have a witness for, nothing bought. ACTION2 at spawn: 48 body cells I draw correctly, plus one burn at (63,61) that I will NOT draw because meter_burn_key2_next has no witness -- one wrong pixel, and the only new datum is free, that the cascade from configuration B should be NINE internal frames rather than the seven t2 returned from configuration A. ACTION5 at spawn: my manual predicts identity and has NO witness for it in this window; if the panel moves, the spawn_probe guard is wrong and I want to know."
    [depends: the_east_key_is_action3_or_action4_and_one_press_names_it, the_meter_reading_is_two_readings_and_this_window_cannot_split_them  probe: pending]
```

=== PLAYBOOK ===
```
# playbook.dsl -- what to buy with the next command, not a route.
#
# ========= THE STATE OF PLAY =========
# Six states, five transitions: RESET, A1, A2, A3, A4, A5.
#   t1 A1 at spawn        -> nothing
#   t2 A2 at spawn        -> body one lattice cell SOUTH (48 cells) + burn (63,63)
#   t3 A3 one cell south  -> nothing
#   t4 A4 one cell south  -> burn (63,62) and nothing else
#   t5 A5 one cell south  -> body back NORTH (48 cells) + panel toggles A to B (23)
# Body is at spawn, lattice (1,2). Panel is in configuration B. Two meter
# cells burned. Next command index is 6.
#
# THE ROUND ITSELF WAS NOT ABOUT THE WORLD. The manual did not compile --
# theory.py could not be loaded -- so nothing replayed and no check ran. The
# landmark line carried prose where a coordinate must be, and eight rules
# depended on it. Fixed to (8, 14); the empty goal: header removed. Until
# certify loads the manual, every number below is a plan and not a measurement.
#
# ========= THE ONE THING WORTH BUYING, AND IT PAYS TWICE =========
# PRESS ACTION3 AT SPAWN.
#
#   Question 1, the east key. A2 is south (witnessed). A5 went north
#   (witnessed). A1 was pressed at spawn with east OPEN and moved nothing, so
#   A1 is not east. EAST IS A3 OR A4 and there is no third candidate. East of
#   spawn is three lattice cells of unbroken floor; west and north are void.
#   If the body steps, A3 is east and the map closes. If it does not, A4 is
#   east by elimination. Both outcomes name the key.
#
#   Question 2, the meter. Two burns, at index 2 under key 2 and index 4
#   under key 4. Reading A -- burns iff the key is 2 or 4 -- and reading B --
#   burns iff the index is even -- agree on all five transitions and cannot
#   be told apart by anything observed. Index 6 is EVEN and key 3 is neither
#   2 nor 4. A burns nothing; B burns (63,61). One press decides it.
#
#   No other command on the board closes either question, and this one closes
#   both. A2 closes neither: its two rules are at full coverage and its only
#   new datum is the free cascade length.
#
# ========= PRICES ADVERTISED IN ADVANCE, NOT DEFECTS =========
#   * First step onto fresh ground costs 48 undrawable pixels. Rows 8-12 cols
#     20-24 have never changed, so they are board, so no instance exists to
#     draw the arrival; and no east-leaves rule is witnessed, so the departure
#     is undrawn too. 24 for the second step, 0 thereafter.
#   * The next effective A5 costs 23 panel cells: this window witnessed the
#     A-to-B toggle only, so the five return rules are not in the manual.
#   * The next A2 costs one pixel: meter_burn_key2_next has no witness.
#   Read a refutation by its divergence set. Where the set is exactly one of
#   these three, the manual is not implicated -- it said so first.
#
# ------------------------------------------------------------------------
# THE MAP, re-verified pixel by pixel against the current frame this round.
# Lattice cell (R,C) is rows 6R+2..6R+6 by cols 6C+2..6C+6. Eleven cells are
# reachable from spawn; the body has stood in two. Three steps east along
# lattice row 1 reach (1,5), beside the knob at (1,6); the knob is the far end
# of one connected colour-8 wire whose near end is the comb at R=6; the comb
# gates the sole north-south corridor and therefore every route to the socket
# at (8,7), which is drawn as three colour-9 walls, an open west side and a
# pip at its centre -- a keyhole shaped to the body's aperture.

order     compile_before_anything_else_a_manual_that_does_not_load_predicts_nothing [proof: lean]
order     settle_the_east_key_before_anything_else_at_this_cell            [proof: lean]
order     prefer_a_command_that_closes_two_open_questions_over_one         [proof: lean]
order     treat_predicted_inertness_as_ignorance_unless_a_witness_backs_it [proof: lean]
order     rank_by_witnesses_a_command_would_create_not_by_pixels_it_moves  [proof: lean]
order     stop_pressing_a_key_the_moment_its_question_has_been_answered    [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired  [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance               [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it               [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it       [proof: lean]
order     buy_the_direction_of_a_toggle_before_buying_its_repetition       [proof: lean]

prune     ranked_only_because_the_manual_predicts_the_most_pixels => dead   [proof: lean]
prune     every_rule_it_would_witness_is_already_at_full_coverage => dead    [proof: lean]
prune     ranked_only_because_a_refutation_fired_on_it => dead               [proof: lean]
prune     divergence_lies_only_on_a_cell_that_had_never_changed => dead      [proof: lean]
prune     repeats_a_key_whose_inertness_here_is_already_witnessed => dead    [proof: lean]
prune     repeats_the_key_that_the_previous_command_just_answered => dead    [proof: lean]
prune     revisits_a_lattice_cell_by_an_already_witnessed_key => dead        [proof: lean]
prune     destination_ring_pixels_are_not_all_floor => dead                  [proof: lean]
prune     action_excluded_for_this_direction_by_an_earlier_no_op => dead     [proof: lean]
prune     route_that_crosses_the_comb_while_it_still_reads_eight => dead     [proof: lean]
prune     meter_exhausted and not goal => dead                               [proof: lean]

heuristic keys_whose_inertness_here_rests_on_no_witness                     [admissible: lean]
heuristic direction_labels_a_command_would_fix_by_elimination               [admissible: lean]
heuristic open_questions_a_command_can_close                                [admissible: lean]
heuristic live_readings_of_the_meter_a_command_can_eliminate                [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_advertised_prices            [admissible: lean]
heuristic lattice_cells_the_body_has_never_occupied                         [admissible: lean]
heuristic lattice_distance_to_the_knob_while_the_gate_is_shut               [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open              [admissible: lean]
heuristic unwitnessed_directions_of_a_toggle_the_manual_half_knows          [admissible: lean]

prefer    a_key_whose_predicted_inertness_here_has_never_been_witnessed    [ev: 3/5 keys at spawn]
prefer    a_key_that_names_a_direction_whichever_way_it_answers            [ev: 2/2 candidates]
prefer    a_key_that_splits_the_two_meter_readings_at_an_even_index        [ev: 5/5 transitions tie]
prefer    a_key_never_pressed_from_the_cell_the_body_stands_on             [ev: 3/5 keys at spawn]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                 [ev: 5/5 diffs]
prefer    east_along_lattice_row_one_over_any_other_axis                   [ev: 1/1 levels]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered          [ev: 1/1 levels]
```

=== LOG ===
```json
[
  {"id": "S-01", "subject": "replay_mismatch: theory.py could not be loaded", "verdict": "accept",
   "why": "The only surprise, and it is structural not empirical: the landmark line read '# arc-cell: carried, coordinates stripped' where the grammar demands '# arc-cell: (row, col)' and calls a landmark the level cannot place a HARD compile error; fixed to (8, 14), and the bare 'goal:' header with an empty body was removed since the grammar sanctions no goal section but not an empty one. No diagnostic text was returned, so this is a repair by inspection against the grammar and I say so in the_compile_failure_was_a_landmark_comment_and_nothing_else."},

  {"id": "S-02", "subject": "the inherited manual describes 34 states; the brief describes 6", "verdict": "accept",
   "why": "store reports states 6, steps 6, dynamic_cells 73, distinct_states 4, and the current frame shows exactly two burned meter cells at (63,62) and (63,63) — so every ev tag past t5 and every coverage past this window witnessed nothing I can see; all rules re-derived from t0-t5, all invariants re-counted, and the longer history's unwitnessable claims demoted to probe: pending."},

  {"id": "O-01", "subject": "mdl obj0 (colour 9, 8 cells, 3x3) + obj2 (colour 9, 1x3) + the spawn ring + the bar", "verdict": "accept",
   "as": "Glyph9, arc-instances: all", "why": "37 cells whose frame-0 colour is 9 have changed — 8 slot-1 ring, 3 underline-1, 24 spawn ring, 2 meter — and the arm looks objects up by colour alone, so one type covers all four groups; the rules separate them by off-board row and column tests, not by type."},

  {"id": "O-02", "subject": "mdl obj1 (colour 1, 9 cells, 3x3, frames 0-4, then vanish)", "verdict": "accept",
   "as": "Spent, arc-instances: all", "why": "rows 1-3 cols 5-7 are solid colour 1 in states 0-4 and all nine cells change at t5, centre included, which is why the count is 9 and not 8."},

  {"id": "O-03", "subject": "the 24 floor cells at rows 14-18 cols 14-18 that turned 9 at t2", "verdict": "accept",
   "as": "Vacated, arc-instances: all", "why": "frame-0 colour 5, they carry the body one lattice cell south and back; (16,16) is excluded because it never changed — the aperture rides over it."},

  {"id": "O-04", "subject": "row 5 cols 5-7 (underline 2), frame-0 colour 0", "verdict": "accept",
   "as": "Dark, arc-instances: all", "why": "they change at t5 and nothing else can own them; but colour 0 is the background and cells_needing_an_owner is 70 = 73 - 3, so the arm may seat no instance here — recorded as dark_may_have_no_instances, cost bounded at 3 pixels on t5."},

  {"id": "O-05", "subject": "mdl obj3 (colour null, 1006 cells, 50x38)", "verdict": "reject",
   "as": null, "why": "connected_components(4) merged the maze floor with the body ring because the mover is floor-coloured at its own boundary; a type on that blob would claim 1006 cells the board already explains and would double-claim the ones my objects own."},

  {"id": "O-06", "subject": "colour 8 machinery (knob, wire, comb teeth)", "verdict": "reject",
   "as": null, "why": "not one colour-8 pixel has changed in six frames, so it is board; a Wire type would have zero instances and any goal over it would be true at RESET."},

  {"id": "R-01", "subject": "key2_body_leaves / key2_body_arrives", "verdict": "accept",
   "why": "t2 changed 49 cells and these two draw 48 of them: 24 spawn-ring cells whose sixth-below renders floor go to 5, 24 lower-ring cells whose sixth-above renders 9 go to 9; no other Glyph9 instance satisfies the leaves guard (the panel's sixth-below is void, the bar's is off-board and colour tests off-board are false)."},

  {"id": "R-02", "subject": "meter_burn_key2_rightmost", "verdict": "accept",
   "why": "the 49th cell of t2 is (63,63) going 9 to 1, and it is the unique Glyph9 instance whose rightof is wall; it cannot clash with key2_body_leaves because its sixth-below is off-board."},

  {"id": "R-03", "subject": "meter_burn_key4_next", "verdict": "accept",
   "why": "t4 changed exactly one cell, (63,62) 9 to 1, and it is the unique colour-9 instance whose right neighbour renders 1 — the panel's right neighbours at that state are separator zeros."},

  {"id": "R-04", "subject": "meter_burn_key2_next (the key-2 twin of R-03)", "verdict": "probe-pending",
   "why": "no witness in this window: the only key-2 burn was the rightmost cell, where the right neighbour did not exist. Text is written out in the_burn_rule_i_cannot_write_yet; the next ACTION2 buys it and costs one pixel until it does."},

  {"id": "R-05", "subject": "key5_body_clears / key5_body_respawns", "verdict": "accept",
   "why": "48 of the 71 cells of t5: the 24 Vacated instances rendering 9 go to 5, and the 24 spawn-ring instances rendering 5 with floor above go to 9; no panel instance renders 5-with-floor-above at state 4, so the respawn rule is confined to the body."},

  {"id": "R-06", "subject": "the eight A-to-B panel rules (slot1_dims, underline1_dims, slot2 row1/row3/row2-left/row2-right/centre, underline2_lights)", "verdict": "accept",
   "why": "they draw exactly the remaining 23 cells of t5 — 8+3+3+3+1+1+1+3 — and they are pairwise exclusive because the row and column discriminations rest on off-board colour tests being false; I checked the one dangerous pair (col 5 vs col 6 in slot 2), separated not by leftof-seven but by colored(leftof, 1) failing at the separator."},

  {"id": "R-07", "subject": "the five B-to-A panel rules (slot1_lights, underline1_lights, ring_resets, centre_resets, underline2_dims)", "verdict": "reject",
   "why": "this window contains ONE toggle and it runs A to B; tagging return rules with t5 would be a fabricated witness. Their text is preserved in the_panel_toggle_is_witnessed_in_one_direction_only and the price is stated: 23 undrawn cells on the next effective ACTION5."},

  {"id": "R-08", "subject": "key1_inert_at_spawn / key3_inert_below_spawn", "verdict": "accept",
   "why": "each has one witness on a zero-change transition and each recolours one pixel to the colour it already has, so both FAIL the gain test outright and I say so in the manual; kept only because they put keys 1 and 3 into the adjudicated alphabet at no predictive cost, and named as the two cheapest deletions here."},

  {"id": "L-01", "subject": "dynamic_census (73 = 23 panel + 24 spawn ring + 24 lower ring + 2 meter)", "verdict": "accept",
   "why": "zero_space's global law lists exactly those 73 cells; by frame-0 colour 37+9+24 = 70 = cells_needing_an_owner and 4096-73 = 4023 = constant_cells, both exact."},

  {"id": "L-02", "subject": "cegis_miner verdict: the world does not narrate as one mover", "verdict": "reject",
   "why": "true of the arm, false of the world — the mover is a rigid 24-pixel ring and the arm can only see 24 simultaneous recolours, which is why every track was refused for narrating recolor or vanish."},

  {"id": "L-03", "subject": "zero_space self-report THIN (rank 3 of 365 features, null space 362)", "verdict": "accept",
   "why": "recorded verbatim in what_the_engines_gave_me; its only global law is my census, and nothing else it offers is treated as a conservation law."},

  {"id": "L-04", "subject": "mdl_segmenter gain is NEGATIVE this round (-5042 and -17520 bits)", "verdict": "accept",
   "why": "by its own accounting its segmentation does not pay for itself, so I take nothing structural from it; what I keep is the frame-index corroboration of the toggle (obj1 present 0-4 then vanish, obj5 colour 2 first seen at frame 5, two move events), which is independent of my rules."},

  {"id": "L-05", "subject": "EAST is ACTION3 or ACTION4", "verdict": "accept",
   "why": "A2 moved the body south (t2), A5 moved it north (t5), and A1 was pressed at spawn where east is open floor and moved nothing (t1) — leaving exactly two candidates, both of which were tested only at a cell where east and west are void."},

  {"id": "L-06", "subject": "the meter law: action-keyed vs command-parity", "verdict": "probe-pending",
   "why": "burns at index 2 under key 2 and index 4 under key 4 fit BOTH readings on all five transitions; I encode the action-keyed one because parity is inexpressible in this guard language, and I name the discriminating press rather than claim the question is settled."},

  {"id": "L-07", "subject": "the map: six-pixel lattice, comb gate, knob, keyhole socket at (8,7)", "verdict": "accept",
   "why": "re-verified cell by cell against the current frame this round, not carried on trust — R=1 floor cols 13-43, R=2 floor cols 13-19 and 25-31, comb teeth rows 38-42 cols 14-18 with only (39,14) and (41,14) floor, socket walls at row 49 and row 55 cols 43-49 and col 49 rows 49-55 with the pip at (52,46)."},

  {"id": "P-01", "subject": "ACTION3 at spawn (next command, index 6)", "verdict": "probe-pending",
   "why": "closes two questions with one press: it names the east key whichever way it answers, and because index 6 is even while key 3 is neither 2 nor 4, a burn at (63,61) kills the action-keyed meter reading while no burn confirms it."},

  {"id": "P-02", "subject": "ACTION5 at spawn", "verdict": "probe-pending",
   "why": "my manual predicts identity there and has NO witness for it in this window; the spawn_probe guard currently changes no prediction because configuration B blocks all eight panel rules by colour anyway, so this probe tests a silence rather than a guard."},

  {"id": "P-03", "subject": "ACTION2 from spawn with the panel in configuration B", "verdict": "probe-pending",
   "why": "free datum only — the net effect is already at full coverage, but the cascade length would test whether the panel's state changes the animation (t2 returned 7 frames from configuration A)."},

  {"id": "E-01", "subject": "a command counter or phase bit", "verdict": "probe-pending",
   "why": "I wanted to write 'burns iff the command index is even'; the guard language reads pixels and the action name and nothing else, so I wrote the action-keyed rules instead and recorded the alternative in the_meter_reading_is_two_readings_and_this_window_cannot_split_them."},

  {"id": "E-02", "subject": "a third outcome meaning 'unobserved, I decline to predict'", "verdict": "probe-pending",
   "why": "the compiled step is total, so absence of a rule asserts 'nothing happens' in the same voice as a witnessed silence; I wrote silence_is_a_prediction_and_three_of_my_spawn_silences_are_forged instead, and named which three."},

  {"id": "E-03", "subject": "an instance on a cell that has never changed", "verdict": "reject",
   "why": "needed to draw the meter's leading edge and the first step onto fresh ground; arc-instances: all only covers cells the board cannot explain, and a second colour-9 type would be indistinguishable from Glyph9 and would double-claim — so the hole is permanent and priced in advance instead."},

  {"id": "E-04", "subject": "a goal predicate", "verdict": "reject",
   "why": "every expressible candidate is true in states that are not wins (count(Vacated, color = 9) = 24 holds one cell south of spawn; count(Wire) = 0 holds at RESET), and a goal true in the wrong state stops a planner at its first step — so there is no goal section and is_goal compiles to False."}
]
```
```
