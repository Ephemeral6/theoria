# call-003-theorize-round1

model: `claude-opus-5` · 891485 ms · $2.861150 · usage {"cache_creation": {"ephemeral_1h_input_tokens": 99629, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 99629, "cache_read_input_tokens": 35564, "inference_geo": "not_available", "input_tokens": 4, "iterations": [{"cache_creation": {"ephemeral_1h_input_tokens": 64065, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 64065, "cache_read_input_tokens": 35564, "input_tokens": 2, "output_tokens": 8821, "type": "message"}], "output_tokens": 72821, "server_tool_use": {"web_fetch_requests": 0, "web_search_requests": 0}, "service_tier": "standard", "speed": "standard"}

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
 "distinct_states": 8,
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
- t8   ACTION2   frames=7   state=NOT_FINISHED 49 cells changed, rows 8-63, cols 14-60, [5, 9] -> [1, 5, 9]
- t9   ACTION5   frames=9   state=NOT_FINISHED 71 cells changed, rows 1-18, cols 1-18, [0, 1, 5, 9] -> [0, 2, 5, 9]

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
   },
   {
    "ms": 0,
    "refused": "ValueError: object absent at frame 0; unsupported on this fixture",
    "track_id": "obj7"
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
  "candidates": 8,
  "chosen_operator": "connected_components(4)",
  "chosen_split_by_color": false,
  "engine": "mdl_segmenter",
  "event_types": {
   "appear": 3,
   "move": 6,
   "recolor": 10,
   "vanish": 3
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
    "frames_present": 2,
    "n_cells": 9,
    "shape": [
     3,
     3
    ],
    "track_id": "obj6"
   },
   {
    "color": 2,
    "first_frame": 9,
    "frames_present": 1,
    "n_cells": 8,
    "shape": [
     3,
     3
    ],
    "track_id": "obj7"
   }
  ],
  "variants": [
   {
    "baseline_bits": 5848,
    "compression_ratio": 1.378591,
    "events": 22,
    "gain_bits": -2214,
    "ms": 22,
    "script_bits": 8062,
    "split_by_color": false,
    "tracks": 8
   },
   {
    "baseline_bits": 5848,
    "compression_ratio": 7.258208,
    "events": 51,
    "gain_bits": -36598,
    "ms": 38,
    "script_bits": 42446,
    "split_by_color": true,
    "tracks": 27
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
  "distinct_states": 8,
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
```

The full proposal stream is 750 rows in `candidates.jsonl`.

## The manual as it stands

```
# theory.dsl -- world observed for 6 states / 5 transitions (RESET +
# ACTION1..ACTION5). 73 cells have ever changed; this manual names all 73 and
# owns the 70 that any colour-keyed object can own.
#
# WHAT HAPPENED THIS ROUND, IN ORDER OF WHAT IT COST ME:
#
#   1. THE WORLD DID NOT ADVANCE. The store is byte-for-byte the store of the
#      last build: states 6, steps 6, dynamic_cells 73, cells_needing_an_owner
#      70, cascade_lengths [1,7,9], actions ACTION1..ACTION5 + RESET. No new
#      command was issued, so not one of my pending probes could be paid off
#      and no theorem could be promoted on evidence. See
#      the_world_did_not_advance_and_i_say_so_rather_than_pretending_it_did.
#
#   2. THE ONLY SURPRISE IS THE CELL I DECLARED UNPREDICTABLE, AGAIN. replay
#      diverges at t=1, ACTION2, cells_wrong 1, cell (63,63), manual 9 world 1.
#      That is the meter. My answer is an EXPLICIT REFUSAL TO CHANGE, priced
#      out in the_meter_is_a_hidden_clock_and_the_short_window_tempts_me_to_lie
#      -- action-keying fits 5/5 only because each action was pressed once, and
#      a one-parameter clock fits the same pixels with no free parameter.
#
#   3. I FOUND MY PREDECESSOR'S PANEL EXCUSE TO BE FALSE AND I PAID THE DEBT.
#      The last build claimed "no guard in this language separates slot 1's
#      ring from its underline". It does: `above(above(above(above(?p)))) =
#      wall` is true for rows 0-3 and false for row 5, and the arm already
#      proves off-board cell terms evaluate false instead of crashing (0 step
#      crashes with a below-six guard that runs off row 63). Three new rules,
#      witnessed at t5, cut the respawn's error from 23 wrong cells to 4. See
#      the_panel_excuse_was_wrong_and_here_is_the_arithmetic_that_replaces_it.
#
#   4. THE BODY'S HOLE IS AN APERTURE, AND THE MAP PUTS SOMETHING IN IT TWICE.
#      Lattice (8,7) centres on the socket pip (52,46); lattice (1,6) centres
#      on the knob's centre pixel (10,40). Both are exactly where the body's
#      one-pixel hole would land. That is not a coincidence I can prove, but it
#      is a coincidence I can name and test. See the_hole_is_an_aperture.

semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Glyph9  { pos: Coord, color: Int }   # arc-colour: 9  arc-instances: all
  object Vacated { pos: Coord, color: Int }   # arc-colour: 5  arc-instances: all
  object Spent   { pos: Coord, color: Int }   # arc-colour: 1  arc-instances: all
  landmark spawn_center   # arc-cell: (10, 16)
  landmark knob_center    # arc-cell: (10, 40)
  landmark gate_center    # arc-cell: (40, 16)
  landmark socket_center  # arc-cell: (52, 46)
  domain dir { up, down, left, right }
  Glyph9  [segment: dynamic_colour_9 ev: t0-t5 compress: 37]
  Vacated [segment: dynamic_colour_5 ev: t2,t5 compress: 24]
  Spent   [segment: dynamic_colour_1 ev: t0-t5 compress: 9]

rules:
  rule key2_body_leaves forall ?p in Glyph9 [ev: t2 cov: 24/24]
    when act=key(2) and colored(?p, 9) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule key2_body_arrives forall ?v in Vacated [ev: t2 cov: 24/24]
    when act=key(2) and colored(?v, 5) and colored(above(above(above(above(above(above(?v)))))), 9) then recolored(?v, 9)

  rule key5_body_clears forall ?v in Vacated [ev: t5 cov: 24/24]
    when act=key(5) and colored(?v, 9) then recolored(?v, 5)

  rule key5_body_respawns forall ?p in Glyph9 [ev: t5 cov: 24/24]
    when act=key(5) and colored(?p, 5) and colored(above(?p), 5) then recolored(?p, 9)

  rule key5_spends_the_lit_token forall ?p in Glyph9 [ev: t5 cov: 8/8]
    when act=key(5) and colored(?p, 9) and above(above(above(above(?p)))) = wall then recolored(?p, 2)

  rule key5_dims_the_spent_underline forall ?p in Glyph9 [ev: t5 cov: 3/3]
    when act=key(5) and colored(?p, 9) and colored(above(above(?p)), 9) and colored(above(above(above(above(?p)))), 9) and above(above(above(above(above(above(?p)))))) = wall then recolored(?p, 0)

  rule key5_lights_the_spare_token forall ?s in Spent [ev: t5 cov: 8/9]
    when act=key(5) and colored(?s, 1) then recolored(?s, 9)

laws:
  invariant nine_count_this_build count(Glyph9) = 37 [status: counted]
  invariant five_count_this_build count(Vacated) = 24 [status: counted]
  invariant one_count_this_build count(Spent) = 9 [status: counted]
  invariant board_static_this_build count(board) = 4023 [status: counted]

  theorem the_world_did_not_advance_and_i_say_so_rather_than_pretending_it_did "Every number in the store is identical to the last build's: 6 states, 6 steps, 73 dynamic cells, 70 needing an owner, cascade lengths [1,7,9], ACTION1..ACTION5 plus RESET, and the current frame is the post-respawn frame I already described pixel by pixel. So no command was issued between builds, no pending probe was paid off, and every `probe: pending` below is pending for the same reason it was pending before: nobody has pressed the key. The two consequences I will not hide. (a) Nothing in this manual was CONFIRMED this round; what I did was re-derive it from the frame by hand and find one place where my predecessor's excuse was false. (b) The single scheduled separator -- press any command that is not ACTION2 and not ACTION4 and watch (63,61) -- is now overdue by a whole round, and it is the cheapest thing the next desk can do."
    [probe: passed]

  theorem the_descent_replays_to_the_pixel_and_that_is_the_whole_physics_bill "certify's first divergence is t=1, ACTION2, cells_wrong 1, cell (63,63), manual 9 world 1. Nothing else. The descent moves 49 cells and 48 of them are the body; all 48 are drawn correctly by two rules whose whole content is a distance-six recolour pair. So: a rigid 24-pixel mover on this arm is correctly encoded as source-cells-recolour-to-floor plus destination-cells-recolour-to-body, `colored(?p, 9)` reads the CURRENTLY RENDERED colour and not the frame-0 colour that typed the instance, and both guards are inert on the panel, on the meter and on every floor cell the body is not standing on. I re-checked each class by hand against this frame and changed not one character of either rule."
    [depends: key2_body_leaves, key2_body_arrives  probe: passed]

  theorem off_board_cell_terms_evaluate_false_and_that_is_load_bearing "key2_body_leaves grounds on the two meter instances at row 63, where below(below(below(below(below(below(?p)))))) is row 69, off the board. certify reports 0 step crashes and 0 clashes across all 12 adjudicated pairs, so `colored(<off-board>, k)` returns false rather than raising, and `<cell> = wall` is the sanctioned way to test for it. Every new rule I wrote this round rests on exactly this: the panel rules separate row 1-3 from row 5 by whether the fourth cell above is off the board. If this fact were wrong, certify would already be reporting step crashes on the descent rule, and it is not."
    [depends: key2_body_leaves  probe: passed]

  theorem the_panel_excuse_was_wrong_and_here_is_the_arithmetic_that_replaces_it "My predecessor carried 23 wrong cells on every ACTION5 and justified it with 'no guard in this language separates slot 1's ring from its underline, because (1,2) and (5,2) have byte-identical four-neighbourhoods'. The four-neighbourhood claim is true and the conclusion drawn from it is false: guards are not restricted to neighbours. For a cell at row r, the k-th `above` is off-board exactly when k > r, so `above(above(above(above(?p)))) = wall` is TRUE for rows 0-3 and FALSE for row 5, which is precisely the ring-versus-underline split, and it is one atom. The three rules I added draw 19 of the panel's 23 dynamic cells at t5. Grounding, checked cell by cell against the pre-t5 frame: Glyph9 has 37 instances -- 24 spawn ring (rendering 5 at t5, because the body was at (2,2)), 8 slot-1 ring, 3 slot-1 underline, 2 meter (both already burned to 1). `colored(?p, 9)` therefore selects exactly the 11 panel cells. Of those, rows 1-3 have above-four off-board and take colour 2 (8 cells, correct); row 5 has above-four at row 1 which renders 9, above-two at row 3 which renders 9, and above-six off-board, and takes colour 0 (3 cells, correct). The two guards are complementary on one atom, so they cannot both fire. Neither can reach the spawn ring in any future frame: rows 8-12 have above-four at rows 4-8, on-board, so the ring rule is dead there, and row 12 -- the one row whose above-two and above-four can both render 9 while the body sits at spawn -- is killed by the above-six test, which is on-board for every row from 6 down. Neither can reach the meter: row 63's above-four and above-six are rows 59 and 57, on-board. Slot 2 is Spent, a different type, so no rule of mine can double-claim a cell."
    [depends: key5_spends_the_lit_token, key5_dims_the_spent_underline, off_board_cell_terms_evaluate_false_and_that_is_load_bearing  probe: passed]

  theorem the_one_panel_pixel_i_deliberately_draw_wrong "key5_lights_the_spare_token carries cov 8/9 and that fraction is not a typo. All nine Spent instances are slot 2, all nine render 1 before t5, eight of them go to 9 and the CENTRE (2,6) goes to 0 -- the solid block becomes a hollow ring, the same shape slot 1 had. My rule sends all nine to 9, so it draws (2,6) wrong, every time, on purpose. What it would cost to be right: the eight outer cells are exactly those with at least one background neighbour, and 'at least one' is a disjunction this grammar does not have, so the correct encoding is a four-way decision tree -- `not colored(above(?s), 1)` for row 1; `colored(above(?s), 1) and not colored(below(?s), 1)` for row 3; those two plus `not colored(leftof(?s), 1)` for (2,5); those plus `colored(leftof(?s), 1) and not colored(rightof(?s), 1)` for (2,7); and all four positive for (2,6) alone, which is the only cell whose four neighbours are all colour 1. Five rules, mutually exclusive by construction, to draw nine pixels. That is not shorter than the nine pixels, so rule 3 refuses it and rule 3 is right. I take one known-wrong cell over five rules, I write the tree out here verbatim so the next desk can adopt it the moment that cell matters, and I say plainly that my manual is wrong at (2,6) rather than letting a coverage tag of 9/9 hide it. Total remaining panel debt on an ACTION5: 4 cells -- (2,6) plus the three at (5,5),(5,6),(5,7) that no object can own."
    [depends: key5_lights_the_spare_token  probe: passed]

  theorem replay_accumulates_and_the_count_still_proves_it_one_against_two "certify says 1/5. Under the rival reading where replay re-seeds from the world frame before each command: t1 is a world no-op and no rule of mine fires, so it matches; t3 likewise; t2 and t4 miss on the meter; t5 now misses on 4 cells instead of 23 but still misses. That is 2, and 2 is not 1. Under accumulation: t1 matches, t2 diverges at (63,63), and my carried state differs from the world's at that cell forever, so t3, t4, t5 all miss whatever else I get right. That is exactly 1. So replay carries its own state forward and never re-seeds. Operationally: while the meter burns unpredicted, `matched` cannot exceed 1 and `first_divergence` cannot move past t=1 no matter how much of the manual is right, which is exactly why I added three rules this round that cannot possibly raise my score. I score myself on the responsibility check (0 unexplained), on 0 clashes, and on reading the command diffs by hand."
    [probe: passed]

  theorem the_meter_is_a_hidden_clock_and_the_short_window_tempts_me_to_lie "Row 63 is a 64-cell colour-9 bar losing its rightmost live cell to colour 1, right to left: burn at t2 (63,63), burn at t4 (63,62), no burn at t1, t3, t5. THE TEMPTATION, priced honestly. Each of ACTION1..ACTION5 occurs exactly once here, so 'burns iff act is key(2) or key(4)' fits 5/5 and is writable -- `when act=key(2) and colored(?p, 9) and rightof(?p) = wall then recolored(?p, 1)` picks (63,63) and only it, and `when act=key(4) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)` picks (63,62) and only it -- and it would take replay from 1/5 to 4/5. I REFUSE, and this round I can count the rivals it would have to beat, all of which fit the same five transitions with no free parameter. (a) FRAMES PARITY: cumulative frames returned, counting the reset frame, are 2, 9, 10, 11, 20 at the ends of t1..t5, and the bar burns exactly on the odd ones -- 9 and 11 burn, 2, 10, 20 do not, 5 for 5. (b) COMMAND PARITY: burn on even t. 5 for 5. (c) PHASE RESET BY RESPAWN: burn every second command, with ACTION5 re-zeroing the phase; also 5 for 5, and it differs from (a) and (b) at the very next command. Four readings, five transitions, one observation per action -- that is not evidence for an action-keyed law. And no drawn cell can carry the clock: already-burned cells number 0 at t1 (no burn) and 0 at t2 (burn), 1 at t3 (no burn) and 1 at t4 (burn), so the meter's visible state does not separate its own behaviour. cegis_miner hit the same wall from the other side: 'no literal separates transition 1 from the positives'. Finally, my own manual records a longer window, now outside the store, in which ACTION1 burned and ACTION2 did not, which kills action-keying outright; that record is unverifiable here, which is exactly why I will not let a 4/5 score buy me a rule I have already written down as refuted."
    [probe: passed]

  theorem the_next_two_commands_settle_the_meter_and_i_write_the_predictions_first "Cumulative frames stand at 20, even, and every command this world has returned has had an odd frame count (1, 7 or 9), so the next command lands on an odd cumulative count. Predictions for command t6, chosen to be neither ACTION2 nor ACTION4: readings (a) frames-parity and (b) command-parity both say the bar burns (63,61); reading (c) phase-reset-by-respawn says it does NOT, because ACTION5 at t5 re-zeroed the phase; action-keying says it does not. So a burn at t6 kills BOTH action-keying and phase-reset in one command, and I would then write the burn as a clock and stop apologising for it. A non-burn at t6 leaves action-keying and phase-reset alive together and kills (a) and (b); press a second non-key-2, non-key-4 command at t7 and phase-reset predicts a burn while action-keying still predicts none, which separates the survivors. Two commands, total cost two meter ticks out of roughly 62, and the meter is not the binding budget -- the tokens are. I state the four-way prediction table now, before seeing anything, so that it can cost me."
    [depends: the_meter_is_a_hidden_clock_and_the_short_window_tempts_me_to_lie  probe: pending]

  theorem the_maze_is_a_six_pixel_lattice_and_i_re_read_every_span_again "Lattice cell (R,C) is rows 6R+2..6R+6 by cols 6C+2..6C+6; separator strips are the rows and cols congruent to 1 mod 6. Colour 5 is floor, 0 is void, 8 is the machine, and the body is a rigid 5x5 block of colour 9 with a one-cell hole at its centre. Re-read span by span from this frame, independently of the last build and agreeing with it: R=1 (rows 8-12) is floor from col 13 to col 43 except the knob, so C=2,3,4,5 are open, C=6 holds the knob and C=7 is void; R=2 (rows 14-18) is floor only at cols 13-19 and 25-31, so C=2 and C=4; R=3 (rows 20-24) is floor cols 13-31, so C=2,3,4; R=4 and R=5 (rows 26-36) are floor only at cols 13-19, so C=2; R=6 (rows 38-42) is the comb and its only floor pixels are (39,14) and (41,14), so nothing there is enterable; R=7 (rows 44-48) is floor cols 13-19, so C=2; R=8 (rows 50-54) is floor from col 13 to col 48. Separator rows 7, 13, 19, 25, 31, 37, 43, 49 are floor across column 2 and separator col 37 is floor across R=1, so column 2 is continuous from R=1 to R=8 apart from the comb, and row R=1 is continuous from C=2 to C=6. That is the whole map and it costs no concept beyond the lattice."
    [depends: key2_body_arrives  probe: pending]

  theorem the_hole_is_an_aperture_and_only_the_ring_needs_floor "CORRECTED THIS ROUND. The last build wrote that a lattice cell is enterable only if all 25 of its pixels render floor. That cannot be right, because it makes the winning cell unenterable: lattice (8,7) is rows 50-54 cols 44-48, its centre is (52,46), and (52,46) renders colour 9 -- the socket pip. The correct statement is that the 24 RING pixels must render floor and the hole may render anything, and my rules already encode this without my having touched them, which is the evidence. key2_body_arrives fires on a destination pixel only when the pixel six rows above renders 9; at the destination hole that pixel is the SOURCE hole, which renders floor, so the guard fails and the hole is left alone -- witnessed at t2, where (16,16) stayed 5 while its 24 ring neighbours turned 9. By the same argument, entering the socket would leave (52,46) at 9, which is what it already is. So the pip survives the body arriving on top of it and my movement law needs no amendment. Now the coincidence worth naming: the map places something at a hole-centre exactly twice. Lattice (8,7) centres on the pip (52,46). Lattice (1,6) centres on (10,40), which is the centre pixel of the 3x3 colour-8 knob. Both are precisely where the body's aperture would land. I read that as the designer saying the body interacts through its hole, and I record it as a reading, not a law -- the two cells differ in that the socket's 24 ring pixels are floor while the knob's are colour 8, so only one of them is enterable under any reading."
    [depends: the_maze_is_a_six_pixel_lattice_and_i_re_read_every_span_again  probe: pending]

  theorem the_socket_is_a_keyhole_and_the_pip_names_the_winning_position "Re-read from this frame, char by char, and it holds. Rows 49-55 by cols 43-49 form a 7x7 colour-9 bracket: top bar row 49 cols 43-49, bottom bar row 55 cols 43-49, right wall col 49 rows 50-54, and the left side col 43 rows 50-54 is FLOOR -- the bracket is open on the left. Inside it, one lone colour-9 pixel at (52,46) and nothing else; the surrounding frame at rows 48 and 56 cols 42-50 is floor. Overlay the body: 5x5 with its hole at its own centre, standing in lattice (8,7) = rows 50-54 cols 44-48, centre (52,46). The bracket is then flush on three sides and the pip shows through the aperture. That is a socket and a plug drawn to the pixel, and it names the winning position without my guessing a goal predicate: the game is won when the 24 ring pixels of rows 50-54 cols 44-48 render 9. The bracket has never changed in six frames, so it is board today and no object of mine owns it; the first time the body enters, those 24 pixels become dynamic and the manual can finally speak about them."
    [depends: the_hole_is_an_aperture_and_only_the_ring_needs_floor  probe: pending]

  theorem the_socket_is_unreachable_until_the_comb_opens "Flood the map from spawn (1,2) and the body reaches exactly eleven cells: (1,2), (1,3), (1,4), (1,5), (2,2), (2,4), (3,2), (3,3), (3,4), (4,2), (5,2). The socket interior (8,7) is not among them and neither is anything in R=7 or R=8, because every route south crosses (6,2) and 23 of that cell's 25 pixels render colour 8. So the comb is not an obstacle to route around; it is the door, and this game cannot be won without opening it. The wiring is drawn in the open and I re-counted every column of it this round: colour 8 leaves the comb along row 40 running right from col 14 to col 40, climbs col 40 through rows 12 to 39 in a three-wide floor channel whose flanks are cols 39 and 41, and ends in the 3x3 colour-8 knob at rows 9-11 cols 39-41, inside lattice (1,6). Not one colour-8 pixel has moved in six frames, which is why 8 is board and not an object; the first colour-8 pixel that changes turns this theorem into physics and hands me a rule to write."
    [depends: the_maze_is_a_six_pixel_lattice_and_i_re_read_every_span_again  probe: pending]

  theorem the_knob_is_the_only_thing_the_body_can_touch_and_i_do_not_know_how_it_is_pressed "Of the eleven reachable cells, ten are bounded by floor and void alone. The eleventh, (1,5) at rows 8-12 cols 32-36, is separated from (1,6) only by separator col 37, which is floor. So the knob is the single interactive object within reach and pressing it is the only lever I can see. The geometry argues against the obvious reading: lattice (1,6) contains ten colour-8 pixels -- nine knob and the cable at (12,40) -- and nine of those are ring pixels of the cell, so even under the corrected aperture rule the body cannot stand there while 8 is solid. Either 8 is walkable and key2_body_arrives, which demands the destination render 5, is wrong at the knob and at the comb; or the knob answers to proximity from (1,5); or it answers to an action I have never pressed. All three are cheap to tell apart and my rules make the first self-announcing: if the body enters a colour-8 cell, my manual predicts it stays put and the world will say otherwise, in one command."
    [depends: the_socket_is_unreachable_until_the_comb_opens  probe: pending]

  theorem the_action_map_after_five_transitions "Proven: ACTION2 is down, 24 pixels leaving rows 8-12 and 24 arriving at rows 14-18 at t2. Everything else is negative information and I will not overstate it. ACTION1 was a no-op at t1 from spawn (1,2), where up is void and left is void but RIGHT, (1,3), is open floor and DOWN, (2,2), is open floor -- so ACTION1 is neither right nor down, leaving up, left, or inert. ACTION3 and ACTION4 were no-ops at t3 and t4 from (2,2), where left and right are both void but UP, (1,2), was open floor at the time and DOWN, (3,2), is open floor -- so NEITHER ACTION3 NOR ACTION4 IS UP OR DOWN, leaving left, right, or inert. That is what makes the cheapest probe in the game available from where the body stands right now: at spawn, up and left are void and down is excluded for both keys, so RIGHT IS THE ONLY DIRECTION EITHER OF THEM COULD EXPRESS. Press one at spawn and the outcome is unambiguous -- a six-pixel step east identifies the key that walks the body along R=1 toward the knob, and no movement retires that key to left-or-inert. The same command is the meter separator. ACTION5 is respawn, and up remains unassigned among ACTION1, ACTION6, ACTION7."
    [depends: key2_body_leaves  probe: pending]

  theorem what_i_predict_for_that_probe_before_i_see_it "Written in advance so it can cost me, and unchanged from last round because the probe was never run. If the next command is ACTION3 or ACTION4 from spawn and it does NOT move the body, my manual predicts an unchanged frame and the world changes one cell, (63,61) -- one wrong cell and no other. If it DOES move the body east, my manual has no right-hand rule and cols 20-24 have never been dynamic so they carry no instances: I predict 48 wrong cells, 24 at rows 8-12 cols 14-18 where I keep drawing a body that has left and 24 at rows 8-12 cols 20-24 where I cannot draw the body that arrived, plus the meter cell. Anything OTHER than 1 or 49 wrong cells refutes something I currently believe -- most likely my reading of the lattice or of which cells the arm has instanced -- and I would rather learn that from a counted diff than from a vague sense that the manual is drifting."
    [depends: the_action_map_after_five_transitions, only_visited_cells_have_instances  probe: pending]

  theorem two_actions_have_never_been_pressed "The store's actions_used is ACTION1..ACTION5 and RESET; this world's alphabet is ACTION1..ACTION7. Two commands exist that no observation constrains at all, and in this family one of them is normally a click carrying coordinates. That matters here specifically: the knob is a 3x3 target the body appears geometrically unable to stand on, and a click is exactly the shape of interaction that would press it. I cannot write such a rule. The guard language admits `act=key(6)` but has nowhere to put the two coordinates a click carries, so a click rule would be silently wrong about WHICH cell was clicked and would fire on every click anywhere. If a click drives this world, my manual can record its EFFECT -- comb pixels going 8 to 5 -- and never its precondition. I record the limit now rather than discovering it under pressure."
    [probe: pending]

  theorem the_panel_is_two_tokens_and_one_is_already_spent "Rows 1-3 cols 1-3 and rows 1-3 cols 5-7 are two 3x3 icons, each with a 1x3 underline at row 5. Frames 0-4: slot 1 is a hollow colour-9 ring with its underline lit 9, slot 2 is a SOLID colour-1 block with its underline dark. From frame 5: slot 1 is a hollow colour-2 ring with its underline dark, slot 2 is a HOLLOW colour-9 ring with its underline lit. The icons are miniatures of the body -- a hollow square with a one-pixel aperture -- so I read them as bodies: two tokens, the lit hollow 9 is the one in play, colour 2 marks a token consumed, and the solid block is a token not yet issued, which is why slot 2 gains its hole at the same moment it lights. As of this round that reading is no longer only prose: three rules draw 19 of its 23 pixels from t5 alone. The only command that has ever touched the panel is ACTION5, so respawn spends a token and ONE TOKEN REMAINS. This, not the meter, is the binding budget: roughly 120 commands and one life. Every branch that can end in a respawn ranks below every branch that cannot."
    [depends: key5_spends_the_lit_token, key5_dims_the_spent_underline, key5_lights_the_spare_token  probe: pending]

  theorem only_visited_cells_have_instances "Settled by arithmetic and re-checked against this build's numbers. The arm builds one instance per cell of the declared colour THAT THE BOARD CANNOT EXPLAIN, and board is the set of never-varying cells: constant_cells 4023 plus dynamic_cells 73 is 4096, and cells_needing_an_owner is 70, which is 73 minus the three cells that render background at frame 0 and which no colour-keyed object can claim. 37 + 24 + 9 = 70 exactly. An earlier build with a longer window satisfied the same identity at 4021, 75, 72 and 39 + 24 + 9. So the instance set IS the set of cells that have already changed, and the corridor ahead carries no instances however much floor it shows. The consequence, priced three times now: the first step onto never-yet-changed ground costs 48 wrong cells, and the round after, those cells are dynamic, instances exist, and key2_body_arrives draws them with no change to its text. The manual heals itself one step behind the body, and I take the step anyway."
    [depends: key2_body_arrives  probe: passed]

  theorem the_instance_counts_are_build_relative_not_world_facts "The four invariants above are counted at THIS build and were different at an earlier one -- 39, 24, 9, 4021 then, 37, 24, 9, 4023 now, and the only thing that moved was two meter cells falling out of the observation window. They will change again the moment the body steps onto fresh floor. I state them because they are the arithmetic that proves only_visited_cells_have_instances, and I say plainly that they are properties of what has been observed rather than laws of the world. No rule depends on them."
    [probe: passed]

  theorem dynamic_census "Exactly 73 cells have ever changed. 23 are the status panel: slot 1's eight ring pixels going 9 to 2, its three underline pixels going 9 to 0, slot 2's nine block pixels of which eight go 1 to 9 and the centre (2,6) goes 1 to 0, and its three underline pixels going 0 to 9. 24 are the spawn ring, rows 8-12 cols 14-18 minus the hole (10,16), which never changes and is therefore board. 24 are the same shape six rows down, rows 14-18 cols 14-18 minus its hole (16,16). 2 are the right end of the row-63 bar, (63,62) and (63,63). 23+24+24+2 = 73 and nothing is left over. zero_space independently lists 73 cells_used and its cell list ends with exactly those two meter cells. At frame 0 they split as 37 colour-9, 9 colour-1, 24 colour-5 and 3 background; 37+9+24 = 70 = cells_needing_an_owner, and the responsibility check reports 0 unexplained."
    [probe: passed]

  theorem three_cells_no_object_can_ever_own "(5,5), (5,6), (5,7) render background at frame 0 and colour 9 from frame 5, so no colour-keyed object owns them and none can: an arc-colour 0 object would claim three thousand background cells. Any panel rule therefore has a floor of 3 wrong cells, and with the three rules added this round the floor is what remains, plus (2,6). This is exactly the gap between 73 dynamic cells and 70 cells_needing_an_owner, and it is structural, not an oversight."
    [probe: passed]

  theorem key5_is_respawn_and_i_have_written_it_as_respawn "key5_body_clears and key5_body_respawns say that on ACTION5 every floor pixel rendering body-colour returns to floor and the spawn ring lights up; that fits t5 exactly, 24/24 on each half. I re-checked key5_body_respawns for spurious grounding against this frame: the meter Glyph9 cells render 9 or 1 and never 5, and the panel Glyph9 cells rendered 9 before t5 and render 2 or 0 after, so neither can satisfy colored(?p, 5). The rival reading, 'ACTION5 is up', fits t5 equally well because the body happened to sit exactly one lattice cell below spawn, and it is not idle since up is still unassigned. The three panel rules added this round tilt the balance further toward respawn -- an 'up' key has no business consuming a token icon -- but they do not decide it, because they only witness that the panel changed on ACTION5, not why. Separator: press ACTION5 from a cell that is NOT one lattice cell below spawn. It costs the last token, so it waits behind every other probe in the game, including the two keys never pressed."
    [depends: key5_body_clears, key5_body_respawns  probe: pending]

  theorem the_goal_section_is_absent_on_purpose "There is no goal: section, so is_goal is False, and that is deliberate even though I can name the winning position to the pixel. `Cart.pos = exit_cell` needs one named instance and arc-instances: all gives me Glyph9_r8c14 and 36 siblings instead of a Cart. The socket interior has never changed, so it is board, has no instances, and there is nothing there for count() to range over. Worse, and this is new this round: the pip (52,46) will NEVER become dynamic, because it renders 9 now and the body's aperture leaves it rendering 9 when the body arrives, so the one cell that names the win is permanently invisible to the instance machinery. The 24 ring cells DO become dynamic on first entry, but `count(Vacated, color = 9) = 24` is then true of the body standing anywhere it has already been, which is not a win and would stop a planner at its first step. A goal true in the wrong states is worse than no goal at all. Until the body has stood in (8,7) once, the playbook steers by lattice distance to the knob, which is where the game actually is."
    [depends: the_socket_is_a_keyhole_and_the_pip_names_the_winning_position  probe: pending]

  theorem the_one_key2_rule_i_am_still_not_allowed_to_write "The arm types a cell by its frame-0 colour, so the body changes type as it walks: at rows 8-12 its pixels are Glyph9, at rows 14-18 they are Vacated. The next descent, from (2,2) to (3,2), needs Vacated pixels going 9 to 5 at rows 14-18 and pixels going 5 to 9 at rows 20-24 -- the second is key2_body_arrives, already written and already witnessed, which will ground at rows 20-24 the moment they are dynamic. Only the clearing half is missing, verbatim for whoever witnesses it: 'rule key2_floor_leaves forall ?v in Vacated when act=key(2) and colored(?v, 9) and colored(below(below(below(below(below(below(?v)))))), 5) then recolored(?v, 5)'. I have checked it for spurious grounding and it is inert everywhere in this frame, because no Vacated instance renders 9 unless the body stands on it. I still refuse to write it: rule 2 is not negotiable and one descent buys it. Note the asymmetry with the panel rules I DID write this round -- those are witnessed by a transition inside the window at 8/8, 3/3 and 8/9, and this one is witnessed by nothing at all."
    [depends: key2_body_arrives  probe: pending]

  theorem nested_cell_terms_parse "Settled by the compiler several rounds running: below(below(...)) six deep parses and grounds, one line of guard draws 24 pixels, and the fallback I once dreaded -- one landmark per lattice cell, which is coordinates in disguise -- is off the table permanently. This round the same machinery bought the panel: chains of `above` up to six deep, tested against `wall` and against colours, separate three panel rows that no neighbour-level guard can tell apart. The four landmarks declared here carry real arc-cell comments (10,16), (10,40), (40,16), (52,46); an older build shipped them stripped, which silently landed every one at (0,0). No rule references them, so nothing was drawn wrong; it was a latent trap and it is closed."
    [depends: key2_body_leaves, key5_spends_the_lit_token  probe: passed]

  theorem the_meter_rules_i_withdrew "An older build carried meter_burn_key2 and meter_burn_key4 on one observation each. Both were refuted, and meter_burn_key4's guard would additionally have invented a fifth burn. That is the load-bearing lesson every round the window stays short, because the window keeps offering me those exact two rules at a 4/5 replay score: one observation per action is not evidence for a rule keyed on the action when a hidden clock explains the same pixels with no free parameter. It is also why key2_floor_leaves stays out of the rules section despite my being fairly sure it is true -- and why the three rules I added this round are the ones with a transition under them."
    [probe: passed]

  theorem what_the_engines_gave_me "mdl_segmenter scores NEGATIVE on both variants, -5042 and -17520 bits, so its own segmentation loses to writing the pixels out and I owe it nothing structural. Its tracks are a useful audit and nothing more: obj0 (colour 9, 8 cells, 3x3) is panel slot 1, obj1 (colour 1, 9 cells, present 5 frames) is slot 2 before the recolour, obj2 (colour 9, 1x3) is an underline, obj4 (colour 9, 1x64) is the whole row-63 bar of which only two cells are dynamic, obj5 (colour 2, first_frame 5) is slot 1 after the recolour, and obj3 is a 1006-cell colour-null blob that swallowed the maze floor -- a fair description of my board, not an object. Every one is already inside Glyph9, Spent or board, and obj5 gets no type of its own because a second type on the same pixels invites the double claim rule 5 forbids. Its event tally -- 4 recolours, 1 appear, 1 vanish, 2 moves -- is nonetheless the shape of the panel transition I finally wrote down this round. zero_space self-reports THIN in its own words (5 transitions constrain rank 3 of 365 features, null space dimension 362) and its single global law restates my 73-cell census, which I take as corroboration of the census and nothing more. cegis_miner's refusal remains the most useful sentence any engine has produced here: 'no track satisfies the precondition of exactly one move event per transition; the world does not narrate as one mover.' True of the ARM, false of the world. The world has exactly one mover, a rigid 24-pixel ring; the arm can only see 24 simultaneous recolours, which is why my movement law needs a pair of rules per direction instead of one moved() event."
    [probe: passed]
```

## The playbook as it stands

```
# playbook.dsl -- what to buy with the next command, not a route.
# What changed this round:
#   (a) NOTHING WAS SPENT. The store is identical to last build's, so the
#       separator command below is overdue by a full round. It remains the
#       single highest-value command available and it is free: any command that
#       is not ACTION2 and not ACTION4, pressed from spawn, settles the
#       direction of ACTION3-or-ACTION4 AND splits the four meter readings.
#   (b) The meter now has FOUR live readings, not two: frames-parity,
#       command-parity, phase-reset-by-respawn, and action-keying. One command
#       kills two of them; a second command of the same kind kills a third.
#       That upgrades "probe the meter" from a tiebreak to a two-command plan.
#   (c) The panel is now physics, not prose, so an ACTION5 costs 4 wrong cells
#       instead of 23 -- but it still costs the last token, so it stays last.
#   (d) The aperture correction says only the 24 ring pixels of a destination
#       need floor. It opens no new cell today (the comb's ring is colour 8),
#       so no ordering changed; it will matter the moment the comb opens.
#   (e) replay accumulates and one unpredicted meter cell pins it at 1/5, so
#       "wrong cells in replay" is not a currency I can spend down. Probes are
#       chosen by what the raw frame diff will say, not by what certify will.
# No stored sequence anywhere: every line is a criterion on the current frame
# plus the manual's own open questions.

order     prefer_a_command_that_settles_two_open_questions_at_once     [proof: lean]
order     spend_an_overdue_free_probe_before_any_new_idea              [proof: lean]
order     probe_the_meter_by_piggybacking_it_on_a_direction_probe      [proof: lean]
order     identify_a_direction_key_before_routing_with_it              [proof: lean]
order     probe_from_a_cell_where_one_candidate_direction_is_open      [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it           [proof: lean]
order     reach_the_switch_before_testing_the_switch                   [proof: lean]
order     free_probes_before_token_costing_probes                      [proof: lean]
order     try_an_unpressed_key_before_declaring_a_dead_end             [proof: lean]
order     witness_a_rule_before_writing_it                             [proof: lean]

prune     destination_ring_pixels_are_not_all_floor => dead            [proof: lean]
prune     action_excluded_for_this_direction_by_an_earlier_no_op => dead [proof: lean]
prune     route_that_crosses_the_comb_while_it_still_reads_eight => dead [proof: lean]
prune     meter_probe_using_a_key_that_burns_under_every_reading => dead [proof: lean]
prune     respawn_while_a_legal_move_exists => dead                    [proof: lean]
prune     respawn_when_no_token_remains and not goal => dead           [proof: lean]
prune     meter_exhausted and not goal => dead                         [proof: lean]

heuristic lattice_distance_to_the_knob_while_the_gate_is_shut          [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open         [admissible: lean]
heuristic commands_remaining_at_one_burn_per_two_commands              [admissible: lean]
heuristic live_readings_a_command_can_eliminate                        [admissible: lean]
heuristic open_questions_a_command_can_close                           [admissible: lean]
heuristic unexplained_cells_after_redraw                               [admissible: lean]

prefer    an_unassigned_key_where_right_is_its_only_open_candidate     [ev: 3/3 no_ops]
prefer    a_command_whose_rival_readings_predict_different_pixels      [ev: 2/2 meter]
prefer    repeating_a_separator_once_more_when_two_readings_survive_it [ev: 2/2 meter]
prefer    a_step_that_both_advances_and_witnesses_an_unwritten_rule    [ev: 1/1 moves]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff             [ev: 1/1 levels]
prefer    a_step_toward_the_knob_over_a_step_toward_the_socket         [ev: 1/1 levels]
prefer    an_unpressed_key_over_repeating_a_known_no_op                [ev: 2/5 levels]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered      [ev: 1/1 levels]
prefer    stay_on_the_lattice_row_that_reaches_the_knob                [ev: 1/1 levels]
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
    63,
    63
   ],
   "manual_says": 9,
   "world_says": 1
  }
 ],
 "cells_wrong": 1,
 "kind": "frame_mismatch",
 "t": 1
}
```

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted '5da99fd80ff97e24', the world answered 'af3bb95d3135e37c'

```json
{
 "action": 2,
 "observed": "af3bb95d3135e37c",
 "predictions": {
  "inert": "522b40a28b6d9fbc",
  "manual": "5da99fd80ff97e24",
  "without_key2_body_arrives": "522b40a28b6d9fbc",
  "without_key2_body_leaves": "522b40a28b6d9fbc",
  "without_key5_body_clears": "5da99fd80ff97e24",
  "without_key5_body_respawns": "5da99fd80ff97e24",
  "without_key5_dims_the_spent_underline": "5da99fd80ff97e24",
  "without_key5_lights_the_spare_token": "5da99fd80ff97e24",
  "without_key5_spends_the_lit_token": "5da99fd80ff97e24"
 },
 "probe_id": "P-01"
}
```

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted '522b40a28b6d9fbc', the world answered '0e1cd0b30fbb12b3'

```json
{
 "action": 5,
 "observed": "0e1cd0b30fbb12b3",
 "predictions": {
  "inert": "5da99fd80ff97e24",
  "manual": "522b40a28b6d9fbc",
  "without_key2_body_arrives": "522b40a28b6d9fbc",
  "without_key2_body_leaves": "522b40a28b6d9fbc",
  "without_key5_body_clears": "5da99fd80ff97e24",
  "without_key5_body_respawns": "5da99fd80ff97e24",
  "without_key5_dims_the_spent_underline": "522b40a28b6d9fbc",
  "without_key5_lights_the_spare_token": "522b40a28b6d9fbc",
  "without_key5_spends_the_lit_token": "522b40a28b6d9fbc"
 },
 "probe_id": "P-02"
}
```

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted '5da99fd80ff97e24', the world answered 'b90a6233898771e2'

```json
{
 "action": 2,
 "observed": "b90a6233898771e2",
 "predictions": {
  "inert": "522b40a28b6d9fbc",
  "manual": "5da99fd80ff97e24",
  "without_key2_body_arrives": "522b40a28b6d9fbc",
  "without_key2_body_leaves": "522b40a28b6d9fbc",
  "without_key5_body_clears": "5da99fd80ff97e24",
  "without_key5_body_respawns": "5da99fd80ff97e24",
  "without_key5_dims_the_spent_underline": "5da99fd80ff97e24",
  "without_key5_lights_the_spare_token": "5da99fd80ff97e24",
  "without_key5_spends_the_lit_token": "5da99fd80ff97e24"
 },
 "probe_id": "P-03"
}
```

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted '522b40a28b6d9fbc', the world answered '15c2e5de8c8dc96b'

```json
{
 "action": 5,
 "observed": "15c2e5de8c8dc96b",
 "predictions": {
  "inert": "5da99fd80ff97e24",
  "manual": "522b40a28b6d9fbc",
  "without_key2_body_arrives": "522b40a28b6d9fbc",
  "without_key2_body_leaves": "522b40a28b6d9fbc",
  "without_key5_body_clears": "5da99fd80ff97e24",
  "without_key5_body_respawns": "5da99fd80ff97e24",
  "without_key5_dims_the_spent_underline": "522b40a28b6d9fbc",
  "without_key5_lights_the_spare_token": "522b40a28b6d9fbc",
  "without_key5_spends_the_lit_token": "522b40a28b6d9fbc"
 },
 "probe_id": "P-04"
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
     63,
     63
    ],
    "manual_says": 9,
    "world_says": 1
   }
  ],
  "cells_wrong": 1,
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
  "cap_reached": false,
  "clashes": [],
  "detail": "no (state, action) among 6 x 2 admitted two rules, and all 12 pairs were adjudicated -- no call to `step` raised",
  "n_clashes": 0,
  "ok": true,
  "pairs_checked": 12,
  "pairs_nominal": 12,
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
ION4 burned the meter and ACTION3 did not. Under action-keying that asymmetry is bare key identity and says nothing about direction. Under command-parity it is index parity and says nothing either. But under the third gloss on action-keying -- that the meter charges for MOVEMENT-KEY presses whether or not the move lands -- it says ACTION4 is a direction key that was blocked and ACTION3 is not a direction key at all, and ACTION1 is not one either. That gloss fits 9/9 exactly as well. I record it as a reading and refuse to route on it. What is safe: from spawn, RIGHT is open floor and LEFT is void, so a single press of ACTION3 or ACTION4 there is unambiguous -- a six-pixel step east identifies the key that walks the body along R=1 toward the knob, and no movement retires that key to left-or-inert. ACTION5 is return-to-spawn. Up is unassigned among ACTION1, ACTION6, ACTION7."
    [depends: key2_body_leaves, the_meter_and_the_clock_i_cannot_write  probe: pending]

  theorem what_i_predict_for_the_east_probe_before_i_see_it "If the next command is ACTION3 or ACTION4 from spawn and it does NOT move the body, the raw diff is either empty or exactly one cell, (63,59) going 9 to 1, and my manual predicts empty in both cases because (63,59) carries no instance. If it DOES move the body east, the diff is 49 cells: 24 at rows 8-12 cols 14-18 going 9 to 5, 24 at rows 8-12 cols 20-24 going 5 to 9, and the meter cell. My manual predicts none of them -- it has no east rule and cols 20-24 have never been dynamic, so they carry no instances. Anything OTHER than 0, 1 or 49 changed cells refutes my reading of the lattice or of which cells the arm has instanced, and I would rather learn that from a counted diff than from a feeling that the manual is drifting."
    [depends: the_action_map_after_nine_transitions, the_frontier_cell_is_never_drawable_and_the_meter_is_no_exception  probe: pending]

  theorem two_actions_have_never_been_pressed "actions_used is ACTION1..ACTION5 and RESET; the alphabet is ACTION1..ACTION7. Two commands exist that no observation constrains at all, and in this family one of them is normally a click carrying coordinates. That matters here specifically: the knob is a 3x3 target the body appears geometrically unable to stand on, and a click is exactly the shape of interaction that would press it. I cannot write such a rule. The guard language admits `act=key(6)` but has nowhere to put the two coordinates a click carries, so a click rule would be silently wrong about WHICH cell was clicked and would fire on every click anywhere. If a click drives this world my manual can record its EFFECT -- comb pixels going 8 to 5 -- and never its precondition."
    [probe: pending]

  theorem dynamic_census "Exactly 75 cells have ever changed. 23 are the status panel: slot 1's eight ring pixels swapping between 9 and 2, its three underline pixels between 9 and 0, slot 2's nine block pixels of which eight swap between 1 and 9 and the centre (2,6) between 1 and 0, and slot 2's three underline pixels between 0 and 9. 24 are the spawn ring, rows 8-12 cols 14-18 minus the centre (10,16), which never changes and is board. 24 are the same shape six rows down, rows 14-18 cols 14-18 minus its centre (16,16). 4 are the right end of the row-63 bar, (63,60) through (63,63). 23+24+24+4 = 75 and nothing is left over. At frame 0 they split as 39 colour-9, 9 colour-1, 24 colour-5 and 3 background; 39+9+24 = 72 = cells_needing_an_owner, and constant 4021 + 75 = 4096."
    [probe: passed]

  theorem three_cells_no_object_can_ever_own "(5,5), (5,6), (5,7) render background at frame 0 and colour 9 in state B, so no colour-keyed object owns them and none can. This is exactly the gap between 75 dynamic cells and 72 cells_needing_an_owner, it is structural rather than an oversight, and it is why every forward toggle costs me at least three wrong cells."
    [probe: passed]

  theorem the_instance_counts_are_build_relative_not_world_facts "The four invariants above are counted at THIS build. They were 37, 24, 9, 4023 one build ago and 39, 24, 9, 4021 now, and the only thing that moved was two more meter cells entering the observation window. They will change again the moment the body steps onto fresh floor. I state them because they are the arithmetic that proves the frontier theorem, and I say plainly that they are properties of what has been observed rather than laws of the world. No rule depends on them."
    [probe: passed]

  theorem the_one_key2_rule_i_am_still_not_allowed_to_write "The arm types a cell by its frame-0 colour, so the body changes type as it walks: at rows 8-12 its pixels are Glyph9, at rows 14-18 they are Vacated. A second consecutive descent, from (2,2) to (3,2), needs Vacated pixels going 9 to 5 at rows 14-18 and pixels going 5 to 9 at rows 20-24. The second half is key2_body_arrives, already written and witnessed, which grounds at rows 20-24 the moment they are dynamic. Only the clearing half is missing, and here it is verbatim for whoever witnesses it: 'rule key2_floor_leaves forall ?v in Vacated when act=key(2) and colored(?v, 9) and colored(below(below(below(below(below(below(?v)))))), 5) then recolored(?v, 5)'. It is inert everywhere in this frame. I still refuse to write it: ACTION2 has been pressed three times and all three were from spawn, so no transition witnesses it. One second consecutive descent buys it."
    [depends: key2_body_arrives  probe: pending]

  theorem the_goal_section_is_absent_on_purpose "There is no goal: section, so is_goal is False, and that is deliberate even though I can name the winning position to the pixel. `Cart.pos = exit_cell` needs one named instance and arc-instances: all gives me Glyph9_r8c14 and 38 siblings instead of a Cart. The socket interior has never changed, so it is board with no instances and nothing for count() to range over. The pip (52,46) will never become dynamic either, because it renders 9 now and the aperture leaves it rendering 9 when the body arrives, so the one cell that names the win is permanently invisible to the instance machinery. The 24 ring cells DO become dynamic on first entry, but `count(Vacated, color = 9) = 24` would then be true of the body standing anywhere it has already been, which is not a win and would stop a planner at its first step. A goal true in the wrong states is worse than no goal at all. Until the body has stood in (8,7) once, the playbook steers by lattice distance to the knob."
    [depends: the_socket_is_a_keyhole_and_names_the_winning_position  probe: pending]

  theorem what_the_engines_gave_me "mdl_segmenter scores NEGATIVE on both variants, -2214 and -36598 bits, so its own segmentation loses to writing the pixels out and I owe it nothing structural. Its tracks are a useful audit: obj0 (colour 9, 8 cells, 3x3) is panel slot 1, obj1 (colour 1, 9 cells, present 5 frames) is slot 2 in state A, obj2 (colour 9, 1x3) is an underline, obj4 (colour 9, 1x64) is the whole row-63 bar of which only four cells are dynamic, obj5 and obj7 (colour 2, first frames 5 and 9) are slot 1 in state B -- and the fact that obj5 is present for 2 frames and then a SEPARATE track obj7 appears at frame 9 is the segmenter independently seeing my toggle: the colour-2 ring leaves at t7 and comes back at t9. obj6 (colour 1, first_frame 7) is slot 2 returning to state A, which is the same witness from the other side. obj3 is a 1006-cell colour-null blob that swallowed the maze floor, a fair description of my board and not an object. Every one is already inside Glyph9, Spent or board, and none gets a type of its own because a second type on the same pixels invites the double claim rule 5 forbids. zero_space self-reports THIN in its own words -- 9 transitions constrain rank 5 of 375 features, null space dimension 370 -- and its single global law restates my 75-cell census, which I take as corroboration of the census and nothing more. cegis_miner's refusal remains the most useful sentence any engine has produced here: no track satisfies the precondition of exactly one move event per transition, the world does not narrate as one mover. True of the ARM, false of the world. The world has exactly one mover, a rigid 24-pixel ring; the arm sees 48 simultaneous recolours, which is why my movement law needs a pair of rules per direction instead of one moved() event. Its per-track refusals -- 'transition 1 narrates recolor', 'object absent at frame 0' -- are the same fact restated: the panel toggle and the late-appearing colour-2 tracks are recolours of cells that existed all along."
    [probe: passed]

  theorem nested_cell_terms_parse "Settled by the compiler several rounds running: below(below(...)) six deep parses and grounds, one line of guard draws 24 pixels, and the fallback of one landmark per lattice cell -- coordinates in disguise -- is off the table permanently. Chains of `above` up to six deep, tested against `wall` and against colours, separate three panel rows that no neighbour-level guard can tell apart. Every guard in this manual is a positive atom; I deliberately avoided `not` on a `= wall` comparison, whose parse I have never seen confirmed, by using the colour of the fourth cell above as the complementary test instead. The four landmarks carry real arc-cell comments and no rule references them; they are the map's named places and nothing more."
    [depends: key2_body_leaves, key5_marks_slot_one  probe: passed]
```

=== PLAYBOOK ===
```
# playbook.dsl -- what to buy with the next command, not a route.
#
# What changed this round, and it is mostly deletion:
#   (a) THE TOKEN BUDGET IS GONE. t7 ran the panel backwards, so ACTION5 is a
#       reversible two-state toggle and not a life counter. Every line that
#       ranked respawn last on the strength of "one token remains" is deleted.
#       Respawn is now a cheap way to undo a wrong step.
#   (b) The binding budget is the row-63 meter and NOTHING ELSE. Four of its
#       64 cells are burned after nine commands.
#   (c) The meter has two live readings and they are perfectly confounded so
#       far. Planning is done under the PESSIMISTIC one -- assume every
#       command costs half a meter cell -- while the manual writes the only
#       expressible one. That is not a contradiction; it is the difference
#       between what I can prove and what I should risk.
#   (d) Two probes are now available that pay twice: pressing a candidate
#       direction key from spawn (right open, left void) settles the key AND
#       advances toward the knob; pressing the same key again on the next
#       command settles the meter, because the second press lands on the other
#       index parity.
#   (e) Nothing south of R=5 is plannable until the comb opens, and the comb's
#       only visible switch is the knob, which the body cannot stand on.
# No stored sequence anywhere: every line is a criterion on the current frame
# plus the manual's own open questions.

order     settle_the_east_key_before_routing_east                      [proof: lean]
order     probe_from_a_cell_where_exactly_one_candidate_is_open        [proof: lean]
order     split_a_confounded_reading_while_the_body_is_still_advancing [proof: lean]
order     reach_the_cell_beside_the_knob_before_testing_the_knob       [proof: lean]
order     open_the_comb_before_planning_anything_south_of_it           [proof: lean]
order     try_an_unpressed_key_when_the_only_lever_is_out_of_reach     [proof: lean]
order     witness_a_rule_before_writing_it                             [proof: lean]
order     budget_under_the_pessimistic_meter_reading                   [proof: lean]

prune     destination_ring_pixels_are_not_all_floor => dead            [proof: lean]
prune     direction_excluded_for_this_key_by_an_earlier_no_op => dead  [proof: lean]
prune     route_that_crosses_the_comb_while_it_still_reads_eight => dead [proof: lean]
prune     probe_whose_live_readings_predict_the_same_pixels => dead    [proof: lean]
prune     meter_exhausted and not goal => dead                         [proof: lean]
prune     detour_south_of_row_one_while_the_knob_is_untested => dead   [proof: lean]

heuristic lattice_distance_to_the_knob_while_the_comb_is_shut          [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_comb_is_open         [admissible: lean]
heuristic meter_cells_remaining_at_one_burn_per_command                [admissible: lean]
heuristic live_readings_a_command_can_eliminate                        [admissible: lean]
heuristic open_questions_a_command_can_close                           [admissible: lean]
heuristic unexplained_cells_after_redraw                               [admissible: lean]

prefer    a_key_whose_only_open_candidate_direction_is_east            [ev: 3/3 no_ops]
prefer    a_command_that_advances_and_separates_a_reading_at_once      [ev: 2/2 meter]
prefer    repeating_a_state_action_pair_at_the_other_index_parity      [ev: 1/1 meter]
prefer    a_second_descent_that_witnesses_the_unwritten_clearing_rule  [ev: 1/1 rules]
prefer    an_unpressed_key_when_the_lever_is_geometrically_unreachable [ev: 2/7 keys]
prefer    a_reset_over_an_irreversible_guess_now_that_reset_is_cheap   [ev: 3/3 resets]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff             [ev: 4/4 probes]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered      [ev: 1/1 levels]
prefer    stay_on_the_lattice_row_that_reaches_the_knob                [ev: 1/1 levels]
```

=== LOG ===
```json
[
  {"id": "O-01", "subject": "mdl obj0/obj2 (colour 9, 3x3 and 1x3, rows 1-5 cols 1-3)", "verdict": "entailed", "as": "Glyph9", "why": "panel slot 1 and its underline are already inside the colour-9 type; a separate type on the same pixels would let two rules claim one cell, which constraint 5 forbids."},
  {"id": "O-02", "subject": "mdl obj1 (colour 1, 9 cells, frames_present 5)", "verdict": "entailed", "as": "Spent", "why": "the nine colour-1 cells at rows 1-3 cols 5-7; frames_present 5 rather than 10 is the segmenter seeing them leave at t5 and return at t7, which is my toggle."},
  {"id": "O-03", "subject": "mdl obj5 and obj7 (colour 2, first_frame 5 and 9)", "verdict": "reject", "as": "already Glyph9", "why": "two tracks for one 8-cell ring appearing at frame 5, vanishing, and reappearing at frame 9 is exactly the A/B toggle; declaring a colour-2 object would double-claim the same eight cells Glyph9 owns."},
  {"id": "O-04", "subject": "mdl obj6 (colour 1, first_frame 7)", "verdict": "reject", "as": "already Spent", "why": "same cells as obj1 returning at t7; it is the backward toggle seen from the colour-1 side and needs no type of its own."},
  {"id": "O-05", "subject": "mdl obj4 (colour 9, 1x64, row 63)", "verdict": "entailed", "as": "Glyph9 plus board", "why": "only 4 of its 64 cells have ever varied, so 60 are board and 4 are Glyph9 instances; the arm instances only what board cannot explain."},
  {"id": "O-06", "subject": "mdl obj3 (colour null, 1006 cells, 50x38)", "verdict": "reject", "as": "board", "why": "it swallowed the maze floor, the machine and the socket bracket into one blob; none of those cells has ever changed, so board explains all of them for free."},
  {"id": "R-01", "subject": "key2_body_leaves / key2_body_arrives", "verdict": "accept", "why": "three witnesses now (t2, t6, t8), 72/72 each, 144 pixels drawn by two guards whose whole content is a distance-six recolour pair."},
  {"id": "R-02", "subject": "key5_restores_slot_one, key5_relights_slot_one_underline, key5_darkens_slot_two, key5_refills_slot_two_centre", "verdict": "accept", "why": "the backward toggle at t7 was 71 changed cells my manual drew as zero; these four rules key on rendered colours 2, 0, 9 and 0 and draw 20 of the 23 panel cells, all witnessed at t7."},
  {"id": "R-03", "subject": "key5_marks_slot_one / key5_dims_slot_one_underline", "verdict": "accept", "why": "now witnessed twice each (t5 and t9) at 16/16 and 6/6; I replaced the dims guard's negation-free form with colour tests on the second and fourth cells above so that no guard in this manual uses `not`."},
  {"id": "R-04", "subject": "key5_lights_slot_two", "verdict": "accept", "why": "16/18 and the fraction is deliberate: it draws (2,6) as 9 where the world draws 0, because the correct partition costs five rules for nine pixels and the error self-heals on the next backward toggle."},
  {"id": "R-05", "subject": "meter_burn_leading, meter_burn_trailing_key2, meter_burn_trailing_key4", "verdict": "accept", "why": "four burns witnessed, 4/4 coverage, zero counterexamples in nine transitions, and the only rival that fits equally well -- burns on even command index -- has no term in this grammar; I name the confound and the deletion trigger in the manual rather than staying silent and drawing 0/4."},
  {"id": "R-06", "subject": "key2_floor_leaves (the second-descent clearing rule)", "verdict": "probe-pending", "why": "all three ACTION2 presses were from spawn, so no transition witnesses a Vacated cell clearing; the rule text is written out verbatim in a theorem and stays out of rules: until a second consecutive descent happens."},
  {"id": "R-07", "subject": "a rule for ACTION1, ACTION3, ACTION4 movement", "verdict": "probe-pending", "why": "all three are inert on every observation; ACTION1 is up-left-or-inert and ACTION3/ACTION4 are left-right-or-inert, and no press has yet occurred from a cell where a candidate direction was open."},
  {"id": "L-01", "subject": "the panel is a two-token life budget with one token left", "verdict": "reject", "why": "REFUTED at t7, which ran the panel backwards, [0,2,5,9] -> [0,1,5,9]; three ACTION5 presses gave A,B,A,B and a counter does not run backwards, so respawn is reversible and cheap."},
  {"id": "L-02", "subject": "phase-reset-by-respawn meter reading", "verdict": "reject", "why": "it predicted no burn at t6 and a burn at t7; the world burned (63,61) at t6 and nothing at t7."},
  {"id": "L-03", "subject": "frames-parity meter reading", "verdict": "reject", "why": "every command has returned an odd frame count, so cumulative parity is a function of the command index alone and the reading is not independent of command-parity; and ACTION2 from spawn returned 7, 9 and 7 frames, so frame count is not even a function of state and action."},
  {"id": "L-04", "subject": "action-keyed vs command-parity meter", "verdict": "probe-pending", "why": "both fit 9/9 and are perfectly confounded because every ACTION2 fell on an even index and every ACTION5 on an odd one; command index 10 is even, so any non-key-2, non-key-4 press now separates them in one command."},
  {"id": "L-05", "subject": "only the 24 ring pixels of a destination need to be floor", "verdict": "accept", "why": "witnessed three times: (16,16) stayed 5 while its 24 neighbours turned 9, because the guard reads the source centre, which is floor."},
  {"id": "L-06", "subject": "the socket at rows 50-54 cols 44-48 is the winning position", "verdict": "probe-pending", "why": "re-counted char by char and the 7x7 bracket, the open left side and the lone pip at (52,46) all hold, but nothing there has ever changed, so it is board and the manual cannot yet speak about it."},
  {"id": "L-07", "subject": "the knob is at rows 9-11 cols 39-41 and the cable is column 40", "verdict": "accept", "why": "corrects my predecessor's column arithmetic; row 12, row 13 and row 40 all put the single colour-8 pixel at col 40, and the knob centre (10,40) is exactly where the body's aperture would land in lattice (1,6)."},
  {"id": "P-01", "subject": "controlled repeat of ACTION1 from spawn at an even command index", "verdict": "probe-pending", "why": "identical body position and map to t1, only the index parity differs; empty diff kills command-parity, a lone (63,59) burn kills action-keying and takes three rules with it, body movement kills my map."},
  {"id": "P-02", "subject": "ACTION3 or ACTION4 from spawn", "verdict": "probe-pending", "why": "right is open floor and left is void there, so one press is unambiguous about the key; predicted diff is 0, 1 or 49 cells and anything else refutes the lattice or the instance census."},
  {"id": "P-03", "subject": "the same direction key pressed on two consecutive commands", "verdict": "probe-pending", "why": "pays twice: the second press lands on the other index parity and separates the meter readings while the body is still advancing, and if it is ACTION2 it also witnesses the second-descent clearing rule."},
  {"id": "P-04", "subject": "ACTION6 and ACTION7, never pressed", "verdict": "probe-pending", "why": "the knob's 24 ring pixels include nine colour-8 cells so the body cannot stand on it; a click is the shape of interaction that would press a 3x3 target, and two commands remain untried."},
  {"id": "E-01", "subject": "the command-index clock", "verdict": "probe-pending", "why": "I wanted `when index_parity = 0 then recolored(?p, 1)`; the guard language has no clock, counter or parity term, so I wrote the action-keyed rules instead and recorded the rival and its deletion trigger in the_meter_and_the_clock_i_cannot_write."},
  {"id": "E-02", "subject": "the three cells (5,5), (5,6), (5,7)", "verdict": "accept", "why": "I wanted an object owning cells that render background at frame 0; arc-colour 0 would claim three thousand cells, so they are permanently undrawable and cost three wrong pixels on every forward toggle, stated in three_cells_no_object_can_ever_own."},
  {"id": "E-03", "subject": "a disjunctive guard for slot 2's eight outer pixels", "verdict": "accept", "why": "I wanted 'at least one neighbour is not colour 1'; guards join only with `and`, so the alternative is a five-rule partition for nine pixels, which loses the MDL test, so I kept one rule and one deliberately wrong pixel at (2,6)."},
  {"id": "E-04", "subject": "a goal predicate for standing in lattice (8,7)", "verdict": "reject", "why": "I wanted `goal Body.pos = socket_cell`; arc-instances: all gives 39 named cells and no single instance, the pip never becomes dynamic, and any count() form would be true of the body standing anywhere it has already been, so the goal section stays absent on purpose."}
]
```
```
