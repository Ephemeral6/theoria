# call-002-theorize-round1

model: `claude-opus-5` · 714628 ms · $1.881302 · usage {"cache_creation": {"ephemeral_1h_input_tokens": 36244, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 36244, "cache_read_input_tokens": 0, "inference_geo": "not_available", "input_tokens": 2, "iterations": [{"cache_creation": {"ephemeral_1h_input_tokens": 36244, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 36244, "cache_read_input_tokens": 0, "input_tokens": 2, "output_tokens": 59673, "type": "message"}], "output_tokens": 59673, "server_tool_use": {"web_fetch_requests": 0, "web_search_requests": 0}, "service_tier": "standard", "speed": "standard"}

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
    "ms": 23,
    "script_bits": 8062,
    "split_by_color": false,
    "tracks": 8
   },
   {
    "baseline_bits": 5848,
    "compression_ratio": 7.258208,
    "events": 51,
    "gain_bits": -36598,
    "ms": 37,
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

## The playbook as it stands

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

## Why you are being called: the surprises that fired

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted '25cac958273811a3', the world answered 'af3bb95d3135e37c'

```json
{
 "action": 2,
 "observed": "af3bb95d3135e37c",
 "predictions": {
  "inert": "9bb17844cc3a57c9",
  "manual": "25cac958273811a3",
  "without_key2_body_arrives": "9bb17844cc3a57c9",
  "without_key2_body_leaves": "9bb17844cc3a57c9",
  "without_key5_body_clears": "25cac958273811a3",
  "without_key5_body_respawns": "25cac958273811a3",
  "without_key5_slot1_dims": "25cac958273811a3",
  "without_key5_slot2_centre_darkens": "25cac958273811a3",
  "without_key5_slot2_row1_lights": "25cac958273811a3",
  "without_key5_slot2_row2_left_lights": "25cac958273811a3",
  "without_key5_slot2_row2_right_lights": "25cac958273811a3",
  "without_key5_slot2_row3_lights": "25cac958273811a3",
  "without_key5_underline1_dims": "25cac958273811a3",
  "without_key5_underline2_lights": "25cac958273811a3",
  "without_meter_burn_key2_rightmost": "25cac958273811a3",
  "without_meter_burn_key4_next": "25cac958273811a3"
 },
 "probe_id": "P-01"
}
```

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted '9bb17844cc3a57c9', the world answered '0e1cd0b30fbb12b3'

```json
{
 "action": 5,
 "observed": "0e1cd0b30fbb12b3",
 "predictions": {
  "inert": "25cac958273811a3",
  "manual": "9bb17844cc3a57c9",
  "without_key2_body_arrives": "9bb17844cc3a57c9",
  "without_key2_body_leaves": "9bb17844cc3a57c9",
  "without_key5_body_clears": "25cac958273811a3",
  "without_key5_body_respawns": "25cac958273811a3",
  "without_key5_slot1_dims": "9bb17844cc3a57c9",
  "without_key5_slot2_centre_darkens": "9bb17844cc3a57c9",
  "without_key5_slot2_row1_lights": "9bb17844cc3a57c9",
  "without_key5_slot2_row2_left_lights": "9bb17844cc3a57c9",
  "without_key5_slot2_row2_right_lights": "9bb17844cc3a57c9",
  "without_key5_slot2_row3_lights": "9bb17844cc3a57c9",
  "without_key5_underline1_dims": "9bb17844cc3a57c9",
  "without_key5_underline2_lights": "9bb17844cc3a57c9",
  "without_meter_burn_key2_rightmost": "9bb17844cc3a57c9",
  "without_meter_burn_key4_next": "9bb17844cc3a57c9"
 },
 "probe_id": "P-02"
}
```

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted '25cac958273811a3', the world answered 'b90a6233898771e2'

```json
{
 "action": 2,
 "observed": "b90a6233898771e2",
 "predictions": {
  "inert": "9bb17844cc3a57c9",
  "manual": "25cac958273811a3",
  "without_key2_body_arrives": "9bb17844cc3a57c9",
  "without_key2_body_leaves": "9bb17844cc3a57c9",
  "without_key5_body_clears": "25cac958273811a3",
  "without_key5_body_respawns": "25cac958273811a3",
  "without_key5_slot1_dims": "25cac958273811a3",
  "without_key5_slot2_centre_darkens": "25cac958273811a3",
  "without_key5_slot2_row1_lights": "25cac958273811a3",
  "without_key5_slot2_row2_left_lights": "25cac958273811a3",
  "without_key5_slot2_row2_right_lights": "25cac958273811a3",
  "without_key5_slot2_row3_lights": "25cac958273811a3",
  "without_key5_underline1_dims": "25cac958273811a3",
  "without_key5_underline2_lights": "25cac958273811a3",
  "without_meter_burn_key2_rightmost": "25cac958273811a3",
  "without_meter_burn_key4_next": "25cac958273811a3"
 },
 "probe_id": "P-03"
}
```

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted '9bb17844cc3a57c9', the world answered '15c2e5de8c8dc96b'

```json
{
 "action": 5,
 "observed": "15c2e5de8c8dc96b",
 "predictions": {
  "inert": "25cac958273811a3",
  "manual": "9bb17844cc3a57c9",
  "without_key2_body_arrives": "9bb17844cc3a57c9",
  "without_key2_body_leaves": "9bb17844cc3a57c9",
  "without_key5_body_clears": "25cac958273811a3",
  "without_key5_body_respawns": "25cac958273811a3",
  "without_key5_slot1_dims": "9bb17844cc3a57c9",
  "without_key5_slot2_centre_darkens": "9bb17844cc3a57c9",
  "without_key5_slot2_row1_lights": "9bb17844cc3a57c9",
  "without_key5_slot2_row2_left_lights": "9bb17844cc3a57c9",
  "without_key5_slot2_row2_right_lights": "9bb17844cc3a57c9",
  "without_key5_slot2_row3_lights": "9bb17844cc3a57c9",
  "without_key5_underline1_dims": "9bb17844cc3a57c9",
  "without_key5_underline2_lights": "9bb17844cc3a57c9",
  "without_meter_burn_key2_rightmost": "9bb17844cc3a57c9",
  "without_meter_burn_key4_next": "9bb17844cc3a57c9"
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
# theory.dsl -- world observed for 10 states / 9 transitions
# (RESET + A1 A2 A3 A4 A5 A2 A5 A2 A5). 75 cells have ever changed; this
# manual names and owns all 75.
#
# WHAT THE FOUR REFUTATIONS COST AND WHAT THEY BOUGHT
#
#   The window grew from 6 states to 10 and the four new commands were
#   A2 A5 A2 A5 -- the body oscillating between lattice (1,2) and (2,2).
#   Four probe_refutations fired and ALL FOUR are the same two holes, both
#   of which the previous manual named in advance and priced in advance:
#
#   HOLE 1, 23 cells, transition t7. The panel has two configurations and
#   the previous window only ever witnessed the A->B half, so the five
#   B->A rules sat in `laws:` as preserved text. t7 is the first B->A
#   toggle. The manual, having no rule that fires on a B-coloured panel,
#   predicted no panel change at all and was wrong on exactly the 23 panel
#   cells -- the advertised price, to the cell. The five rules are now
#   witnessed and are back in `rules:`.
#
#   HOLE 2, 1 cell, transitions t6 and t8. `meter_burn_key2_next` had been
#   removed for want of a witness; t6 burned (63,61) and t8 burned (63,60).
#   Advertised price one wrong pixel per burn, paid twice, rule restored.
#
#   The four observed hashes are all distinct while the manual's two
#   predictions repeat (25cac.../9bb17...) because the manual was a 2-cycle
#   -- panel frozen in B, meter frozen at two burns -- while the world is
#   an open trajectory. That is the exact signature of a missing toggle
#   plus a missing counter, and nothing else needed diagnosing.
#
#   WHAT NOTHING FIXES: the NEXT burn is at (63,59), a cell that has never
#   changed and is therefore board, so no object owns it and no rule of
#   mine can draw it. Every burn costs one wrong pixel in the round it
#   happens and zero pixels forever after. See the_manual_heals_one_step_behind.

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
  Vacated [segment: dynamic_colour_5 ev: t2,t5,t6,t7,t8,t9 compress: 24]
  Spent   [segment: dynamic_colour_1 ev: t5,t7,t9 compress: 9]
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

  rule key5_underline1_dims forall ?p in Glyph9 [ev: t5,t9 cov: 6/6]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 9) and colored(above(above(above(above(?p)))), 9) and above(above(above(above(above(above(?p)))))) = wall then recolored(?p, 0)

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

  rule key5_underline2_lights forall ?d in Dark [ev: t5,t9 cov: 6/6]
    when act=key(5) and colored(spawn_probe, 5) and colored(?d, 0) and colored(above(above(?d)), 1) and colored(above(above(above(above(?d)))), 1) then recolored(?d, 9)

  rule key5_slot1_lights forall ?p in Glyph9 [ev: t7 cov: 8/8]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 2) then recolored(?p, 9)

  rule key5_underline1_lights forall ?p in Glyph9 [ev: t7 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 0) and above(above(above(above(above(above(?p)))))) = wall then recolored(?p, 9)

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

  theorem the_four_refutations_were_two_holes_and_both_were_advertised "P-01 and P-03 are ACTION2 presses, P-02 and P-04 ACTION5 presses, and the manual's predictions repeat (25cac.../9bb17...) while the world's four answers are all distinct. That pattern is the whole diagnosis: my compiled manual was a two-state cycle -- spawn and one-cell-south, panel frozen in configuration B because no rule of mine fires on B-coloured panel pixels, meter frozen at two burns because meter_burn_key2_next had been struck for want of a witness -- and the world is an open trajectory whose panel toggles B->A->B and whose bar burns twice more. Two holes, both named in the previous manual's own laws, both priced in advance: 23 cells for the missing B->A half and one pixel per unwitnessed burn. Both prices came in exactly. Repair: the five B->A rules move from prose back into `rules:` with t7 as their witness (8+3+8+1+3 = 23), and meter_burn_key2_next returns with t6,t8 as witnesses. Nothing else in the manual was implicated -- key2_body_leaves, key2_body_arrives, key5_body_clears and key5_body_respawns each gained two more full-coverage witnesses and not one contradiction. I record the shape of this because it is the CHEAP kind of failure: a manual that says in advance what it cannot draw and what that will cost is refuted at a price it already quoted, and the repair is a paste, not a rethink."
    [depends: key5_slot1_lights, key5_slot2_ring_resets, meter_burn_key2_next  probe: passed]

  theorem the_panel_is_a_marker_that_alternates_between_two_slots "PROVEN over three toggles now, t5 t7 t9, 23 cells every time, and ACTION2 has never touched a panel pixel in three presses. CONFIGURATION A (states 0-4, 7, 8): slot 1 at rows 1-3 cols 1-3 is a hollow colour-9 ring, its underline at row 5 cols 1-3 lit 9; slot 2 at rows 1-3 cols 5-7 is a SOLID colour-1 block, its underline at row 5 cols 5-7 dark 0. CONFIGURATION B (states 5, 6, 9, and the current frame): slot 1 is a hollow colour-2 ring with underline dark; slot 2 is a hollow colour-9 ring with a dark centre and its underline lit 9. mdl_segmenter, which knows nothing of my rules, corroborates this independently and adds a reading I had not seen: its obj0 is a colour-9 8-cell 3x3 present in ALL TEN frames and its obj2 a colour-9 1x3 present in all ten, and it narrates six MOVE events -- because the hollow 9 ring and the lit underline do not appear and vanish, they TRAVEL between slot 1 and slot 2, three toggles times two objects. So the panel is one marker with two seats, not two independent lamps, and colour 9 marks the occupied seat. What is still unknown is what the seats hold. I will not guess; nothing downstream needs it, because the rules encode the swap and the swap is fully witnessed in both directions. I cannot model it AS a moving marker: the arm gives one instance per cell and `moved(o, dir)` moves one cell, so an eight-pixel ring travelling four columns is not expressible as a move and the ten recolour rules are the shortest thing this DSL can say."
    [depends: key5_slot1_dims, key5_slot1_lights  probe: passed]

  theorem why_i_keep_the_spawn_probe_guard_on_a_window_that_still_cannot_test_it "Unchanged in kind, stronger in count: the guard `colored(spawn_probe, 5)` now has THREE positive witnesses (t5, t7, t9 -- body away, panel toggled) and STILL NO NEGATIVE ONE, because ACTION5 has never once been pressed with the body at home. Every ACTION5 in this window immediately followed an ACTION2, so 'ACTION5 was pressed' and 'the body was away from spawn' are the same event ten times over and no guard can be credited over the other. By the letter of no-entry-without-gain the atom is still unearned. I keep it because dropping it changes no replay and because the body is at spawn RIGHT NOW: with the guard, my manual predicts SILENCE for an ACTION5 pressed here; without it, it predicts a 23-cell toggle. Silence is the prediction I want on the record, and one press refutes it or confirms it outright."
    [depends: the_panel_is_a_marker_that_alternates_between_two_slots  probe: pending]

  theorem the_meter_question_after_nine_transitions_and_why_it_is_still_open "Row 63 is a 64-cell colour-9 bar burning to colour 1 from the right. Four burns: (63,63) at t2, (63,62) at t4, (63,61) at t6, (63,60) at t8. Five silences: t1, t3, t5, t7, t9. READING A, ACTION-KEYING -- burns iff the key is 2 or 4 -- scores 9/9 and is what the three burn rules encode. READING B, COMMAND PARITY -- burns iff the command index is even -- also scores 9/9. NINE TRANSITIONS CANNOT SEPARATE THEM, and now I know exactly why: every command so far has used a key whose parity equals its own index's parity (indices 2,4,6,8 used keys 2,4,2,2; indices 1,3,5,7,9 used keys 1,3,5,5,5). The two readings are numerically identical on that diagonal and differ nowhere else. THE SEPARATOR IS THEREFORE FREE AND NEEDS NO DEDICATED COMMAND: any press that breaks the alignment settles it -- key 2 or 4 at an odd index, or key 1, 3 or 5 at an even one. Next index is 10, EVEN. One new piece of evidence STRAINS reading A without refuting it: at t3 and t4 the body stood at lattice (2,2) with left and right BOTH void, so ACTION3 and ACTION4 were blocked identically -- and ACTION4 burned while ACTION3 did not. Under action-keying that means the cost is attached to the key and not to the attempt, with keys 2 and 4 charging and 1, 3 and 5 free; under parity it is one bit of clock and no special pleading. I encode A because it is the only one the guard language can say -- there is no command counter and no phase pixel, which is the same wall cegis_miner hit when it reported 'no literal separates transition 1 from the positives' -- and I expect B to win."
    [depends: meter_burn_key2_next, meter_burn_key4_next  probe: pending]

  theorem the_action_map_after_nine_transitions_and_the_standard_mapping_hypothesis "WITNESSED: ACTION2 IS DOWN, 3/3, six rows south, one lattice cell, at t2, t6, t8. ACTION5 returns the body from lattice (2,2) to (1,2), 3/3. NEGATIVE INFORMATION, and I state it as negative because that is all it is. At spawn (1,2) up and left are void while down and right are open floor, and ACTION1 did nothing -- so ACTION1 IS NEITHER DOWN NOR RIGHT. At (2,2) the body had just vacated rows 8-12 so UP WAS OPEN, and rows 20-24 cols 14-18 are floor so DOWN WAS OPEN, while left (cols 8-12) and right (cols 20-24) were both void; ACTION3 and ACTION4 each did nothing there -- so NEITHER IS UP AND NEITHER IS DOWN. Fit those together and one assignment survives that invents nothing: ACTION1 up, ACTION2 down, ACTION3 left, ACTION4 right, ACTION5 something else. It explains every no-op as a blocked move and it is the conventional mapping for this action family, which is a prior and not evidence. It has one cost, and I name it: under it, ACTION3 and ACTION4 were blocked in exactly the same way at the same cell and only one of them burned the meter, which is why I expect the parity reading of the bar. THE CHEAP TEST IS ONE PRESS: the body stands at spawn, where left is void and right is open floor, so ACTION4 pressed here either steps six columns east or does not, and either answer names the east key -- if ACTION4 does not move, ACTION3 is east by elimination, since ACTION1 is already excluded from east by t1."
    [depends: key2_body_arrives, key5_body_respawns, the_cascade_is_animation_and_one_press_is_one_lattice_cell  probe: pending]

  theorem what_action5_is_and_the_two_cell_experiment_that_names_it "Three readings survive all three ACTION5 presses because all three were made from exactly one cell south of spawn, where they are indistinguishable: UP (move one cell north), UNDO (revert the last move), RETURN (jump to spawn from anywhere). They separate the moment the body is TWO cells from spawn, and they separate differently depending on the axis. Two cells EAST at lattice (1,4): up is void there so UP predicts no move, UNDO predicts one cell west to (1,3), RETURN predicts spawn at (1,2) -- three different diffs, all legible in the raw pixel count. Two cells SOUTH at (3,2): UP and UNDO both predict (2,2) and only RETURN separates. So the eastward route answers this question for free and the southward route does not, which is one more reason to go east first. Note the coupling I cannot yet break: the panel toggles on every effective ACTION5, so whatever ACTION5 is, the panel is its counter or its selector, and if ACTION5 turns out to be UNDO then the panel is plausibly an undo-parity display -- a reading I record and do not act on."
    [depends: the_panel_is_a_marker_that_alternates_between_two_slots, the_action_map_after_nine_transitions_and_the_standard_mapping_hypothesis  probe: pending]

  theorem the_cascade_is_animation_and_one_press_is_one_lattice_cell "cascade_lengths are 1, 7 and 9. Every ACTION5 returned 9 frames; ACTION2 returned 7 frames at t2 and t8 and 9 frames at t6; every no-op returned 1. So a move is animated one row per internal frame, the world reports the whole animation for a single action, and `cascade single_frame` compares only the net effect -- which is identical for all three ACTION2 presses (48 body cells, rows 8-18, cols 14-18) regardless of whether the command took 7 frames or 9. TWO THINGS FOLLOW. First, a refutation I keep: under a slide-until-blocked reading, ACTION2 at spawn would have run the body south through rows 20-24 and 26-30 to the comb; it stopped after exactly six rows over open floor, three times. ONE PRESS IS ONE LATTICE CELL, 3/3, and every distance in the playbook rests on that. Second, an anomaly I will not over-read: the two 7-frame ACTION2 presses both had the panel in configuration A and the 9-frame one had it in B. Three samples, one clean correlation, zero effect on the net frame. It is not evidence of unobservable state -- it is evidence that the animation length is a function of something the panel also depends on -- and since the net effect is what I model, it costs me nothing either way."
    [depends: key2_body_arrives, the_maze_is_a_six_pixel_lattice  probe: passed]

  theorem the_world_may_still_not_be_a_function_of_the_drawn_frame "Carried as a belief and NOT proven in this window. To prove it I need two pixel-identical states from which the SAME action produced different successors; I have no such pair. The near misses: states 2 and 3 are pixel-identical (ACTION3 changed nothing at t3) but were followed by different keys; t2 and t8 are the same key from the same lattice cell but from states differing in row 63. What keeps the belief alive is the parity reading of the meter, which if true IS one bit of hidden state that flips every command and that no guard in this language can read, because no guard can read anything that is not a pixel. Operationally it matters in exactly one way: if parity wins, every burn rule I can write is an approximation with a known error rate, and I would rather say that once than rediscover it."
    [depends: the_meter_question_after_nine_transitions_and_why_it_is_still_open  probe: pending]

  theorem the_manual_heals_one_step_behind_and_the_meter_is_where_it_shows "The arm instances exactly the cells that have ALREADY changed, typed by their frame-0 colour: constant 4021 + dynamic 75 = 4096, and 39+24+9 = 72 = cells_needing_an_owner with the 3 colour-0 cells making up the difference to 75. Consequence, stated as a law of this manual rather than of this world: a cell that has never changed is board, no object owns it, and NO RULE CAN DRAW ITS FIRST CHANGE. The bar makes this exact and unavoidable. meter_burn_key2_next now replays t6 and t8 perfectly, because by replay time (63,61) and (63,60) are dynamic and have instances; it will still miss the FIFTH burn at (63,59), because that cell is board today. Every burn therefore costs exactly one wrong pixel in the round it first happens and zero pixels forever after, and no rewriting of the rule fixes it -- only observation does. The same arithmetic prices the first eastward step: rows 8-12 cols 20-24 have never changed, so 24 arrival pixels are undrawable no matter what rule I write, and the 24 departure pixels are undrawable too until an east-leaves rule is witnessed. 48 wrong cells for the first step onto fresh ground, 24 if I already had the leaves rule, 0 for the second step. The body also CHANGES TYPE as it walks -- Glyph9 at rows 8-12, Vacated at rows 14-18 -- because typing is by frame-0 colour and all that floor was 5."
    [depends: key2_body_arrives, dynamic_census  probe: passed]

  theorem dynamic_census "Exactly 75 cells have ever changed and every one has an owner. 23 are the panel: slot 1's eight ring pixels, its centre (2,2) being colour 0 in BOTH configurations and therefore board; underline 1's three; slot 2's nine, centre included because (2,6) is 1 in A and 0 in B; underline 2's three. 24 are the spawn ring, rows 8-12 cols 14-18 minus the aperture (10,16), which never changes and is board. 24 are the same ring six rows south, rows 14-18 cols 14-18 minus its aperture (16,16). 4 are the burned right end of row 63: (63,63), (63,62), (63,61), (63,60). 23+24+24+4 = 75 = dynamic_cells. By frame-0 colour: 39 colour-9 (8 slot-1 ring + 3 underline-1 + 24 spawn ring + 4 meter), 9 colour-1 (slot 2 solid), 24 colour-5 (the lower ring, floor at frame 0), 3 colour-0 (underline 2). 39+9+24 = 72 = cells_needing_an_owner exactly. zero_space's cell list is the same 75 cells -- it lists (2,1) and (2,3) but not (2,2), (10,14),(10,15),(10,17),(10,18) but not (10,16), and all four burned bar cells -- and its single global law restates this census."
    [probe: passed]

  theorem the_rules_i_still_have_no_witness_for_and_will_not_write "Three holes, each with its text ready so that the transition that witnesses it costs one paste and not one round of rediscovery. (1) A SECOND DESCENT. The body has descended three times and all three started at spawn, so no rule of mine turns Vacated pixels from 9 back to 5 on an ACTION2: 'rule key2_floor_leaves forall ?v in Vacated when act=key(2) and colored(?v, 9) and colored(below(below(below(below(below(below(?v)))))), 5) then recolored(?v, 5)'. One ACTION2 from lattice (2,2) buys it. (2) EAST-WEST MOTION. Whatever the east key turns out to be, it needs a pair: 'rule keyE_body_leaves forall ?p in Glyph9 when act=key(N) and colored(?p, 9) and colored(rightof(rightof(rightof(rightof(rightof(rightof(?p)))))), 5) then recolored(?p, 5)' and its arrives-twin typed on whichever object owns the destination pixels -- which today is NO object, because rows 8-12 cols 20-24 are board. (3) A FIFTH BURN AT A CELL THAT IS STILL BOARD, which is not a missing rule but a missing instance and cannot be written at all. I state the price of all three in advance so it cannot be mistaken for a surprise: the first eastward step costs 48 wrong cells plus one if the bar burns, the first second-descent costs 24, and every fresh burn costs 1."
    [depends: key2_body_arrives, the_manual_heals_one_step_behind_and_the_meter_is_where_it_shows  probe: pending]

  theorem off_board_cell_terms_evaluate_false_and_that_is_load_bearing "certify reports 0 step crashes across all adjudicated pairs while key2_body_leaves grounds on meter instances at row 63 whose sixth `below` is row 69. So `colored(<off-board>, k)` is false rather than an exception, and `<cell> = wall` is the sanctioned positive test. Thirteen of the twenty rules rest on this and every row and column discrimination in the panel is built from it: the k-th `above` is off-board exactly when k exceeds the row, so row 1 is `above(above(?s)) = wall`, row 3 is `colored(above(above(?s)), 1)` -- false for row 1 precisely because a colour test on an off-board cell is false -- and row 2 is `above^3 = wall` conjoined with `colored(above(?s), 1)`. The same trick separates slot 2's middle row by column: col 5 is `leftof^6 = wall`, col 6 is `leftof^7 = wall and colored(leftof(?s), 1)`, col 7 is `colored(leftof(leftof(?s)), 1)`, pairwise exclusive, which is why the ambiguity check reports 0 clashes. Not one rule uses `not`, deliberately. The eight A->B slot-2 and underline rules could collapse to two if I could write 'not all four neighbours are colour 1', and I decline to gamble a whole round's compile on discovering whether `not` before an equality atom parses. If a future desk wants the shorter form, try it on ONE rule, not on eight."
    [depends: key2_body_leaves, key5_slot2_centre_darkens  probe: passed]

  theorem the_maze_is_a_six_pixel_lattice "Lattice cell (R,C) is rows 6R+2..6R+6 by cols 6C+2..6C+6; rows and columns congruent to 1 mod 6 are separator strips. Colour 5 is floor, 0 is void, 8 is machinery, and the body is a rigid 5x5 colour-9 block with a one-pixel aperture at its centre. Read from the current frame: R=1 (rows 8-12) is floor from col 13 to col 43 except the knob, so C=2,3,4,5 are open, C=6 holds the knob, C=7 is void; R=2 is floor at cols 13-19 and 25-31, so C=2 and C=4 only; R=3 is floor cols 13-31, so C=2,3,4; R=4 and R=5 are floor only at cols 13-19, so C=2; R=6 is the comb, whose only floor pixels are (39,14) and (41,14), so nothing there is enterable; R=7 is C=2; R=8 is floor from col 13 to col 48, so C=2..7. Separator rows 7,13,19,25,31,37,43,49 are floor across column 2, and separator col 37 is floor across R=1, so column 2 is continuous from R=1 to R=8 apart from the comb, and row R=1 is continuous from C=2 to C=6. Spawn is (1,2); in ten frames the body has occupied exactly two cells, (1,2) and (2,2), and it has been at spawn in six of them."
    [depends: key2_body_arrives, the_cascade_is_animation_and_one_press_is_one_lattice_cell  probe: pending]

  theorem the_hole_is_an_aperture_and_only_the_ring_needs_floor "A destination lattice cell needs its 24 RING pixels to render floor; the centre may render anything, because key2_body_arrives fires on a destination pixel only when the pixel six rows above renders 9, and at the destination centre that pixel is the source centre, which renders floor. Witnessed three times: (16,16) stayed 5 while its 24 neighbours turned 9. This matters because it is the only reading under which the winning cell is enterable: lattice (8,7) is rows 50-54 cols 44-48 and its centre (52,46) renders colour 9, the socket pip. The map places something at a hole-centre exactly twice -- that pip and the knob's centre pixel at (10,40) -- which I read as the designer saying the body acts through its aperture, and record as a reading, not a law."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_socket_is_a_keyhole_and_names_the_winning_position "Rows 49-55 by cols 43-49 form a 7x7 colour-9 bracket: top bar row 49 cols 43-49, bottom bar row 55 cols 43-49, right wall col 49 rows 50-54, and col 43 rows 50-54 is FLOOR, so it is open on the left. Inside it one lone colour-9 pixel at (52,46). Overlay the body standing in lattice (8,7): flush on three sides, pip showing through the aperture. That is a plug and a socket drawn to the pixel, and it names the winning position without my guessing a goal predicate -- the game is won when the 24 ring pixels of rows 50-54 cols 44-48 render 9. The bracket has never changed in ten frames, so it is board and no object owns it; the first time the body enters, those 24 pixels become dynamic and the manual can finally speak about them."
    [depends: the_hole_is_an_aperture_and_only_the_ring_needs_floor  probe: pending]

  theorem the_socket_is_unreachable_until_the_comb_opens "Flood from spawn and the body reaches eleven lattice cells: (1,2),(1,3),(1,4),(1,5),(2,2),(2,4),(3,2),(3,3),(3,4),(4,2),(5,2). The socket (8,7) is not among them and nothing in R=7 or R=8 is, because every route south crosses (6,2) and 23 of that cell's 25 pixels render colour 8. The comb is not an obstacle to route around, it is the door. Its wiring is drawn in the open: colour 8 leaves the comb along row 40 from col 14 to col 40, climbs col 40 through rows 12 to 39, and ends in a 3x3 colour-8 knob at rows 9-11 cols 39-41 with a stem pixel at (12,40), all inside lattice (1,6). Not one colour-8 pixel has moved in ten frames, which is why 8 is board and not an object; the first colour-8 pixel that changes turns this theorem into physics and hands me a rule."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_knob_is_the_only_thing_within_reach_and_i_do_not_know_how_it_is_pressed "Ten of the eleven reachable cells are bounded by floor and void alone. The eleventh, (1,5) at rows 8-12 cols 32-36, is separated from the knob's cell (1,6) only by separator col 37, which is floor. Lattice (1,6) contains ten colour-8 pixels, nine of them ring pixels of that cell, so even under the aperture rule the body cannot stand there while 8 is solid. Either 8 is walkable and key2_body_arrives is wrong at the knob; or the knob answers to proximity from (1,5); or it answers to a key never pressed. My rules make the first self-announcing: if the body is driven into a colour-8 cell my manual predicts it stays put, and the world says otherwise in one command. Four lattice cells of eastward travel put the body at (1,5) and every one of those four steps is on floor that R=1 shows open."
    [depends: the_socket_is_unreachable_until_the_comb_opens  probe: pending]

  theorem two_actions_have_never_been_pressed_and_one_of_them_may_be_a_click "actions_used is ACTION1..ACTION5 plus RESET; the alphabet is ACTION1..ACTION7. Two commands are entirely unconstrained after ten states, and in this family one is normally a click carrying coordinates. That matters here: the knob is a 3x3 target the body appears unable to stand on, and a click is the shape of interaction that presses it. I cannot write such a rule -- the guard language admits act=key(6) but has nowhere to put two coordinates, so a click rule would fire on every click anywhere and be silently wrong about which cell was clicked. If a click drives this world my manual can record its EFFECT, comb pixels going 8 to 5, and never its precondition. Note that the standard mapping I now favour -- 1 up, 2 down, 3 left, 4 right, 5 undo-or-return -- accounts for every key I have pressed, which makes 6 and 7 more likely to be a click and a spare than more directions."
    [depends: the_action_map_after_nine_transitions_and_the_standard_mapping_hypothesis  probe: pending]

  theorem the_goal_section_is_absent_on_purpose "Still absent, and the reason has not weakened. `Cart.pos = exit_cell` needs one named instance and `arc-instances: all` gives me Glyph9_r8c14 and thirty-eight siblings. The socket interior has never changed, so it is board and count() has nothing to range over there, and the pip (52,46) will never become dynamic because the body's aperture leaves it rendering 9. The 24 ring cells do become dynamic on first entry, but `count(Vacated, color = 9) = 24` would then be true of the body standing anywhere it has already been, which is not a win -- a goal true in the wrong states is worse than no goal, because it stops a planner at its first step. Until the body has stood in lattice (8,7) once, the playbook steers by lattice distance, and `is_goal -> False` is the honest compilation."
    [depends: the_socket_is_a_keyhole_and_names_the_winning_position  probe: pending]

  theorem what_the_engines_gave_me "mdl_segmenter scores NEGATIVE on both variants, -2214 and -36598 bits, so its segmentation still loses to writing the pixels out and I owe it nothing structural -- but its EIGHT tracks are the round's best independent corroboration. obj1 (colour 1, nine cells, first seen frame 0, present 5 frames) and obj6 (colour 1, nine cells, first seen frame 7, present 2 frames) are slot 2 solid in configurations A; obj5 (colour 2, first seen frame 5, present 2) and obj7 (colour 2, first seen frame 9, present 1) are slot 1 dimmed in configurations B. Read the frame indices off those four tracks and you get A at 0-4, B at 5-6, A at 7-8, B at 9 -- exactly the toggle sequence my three ACTION5 rules produce, derived by an engine that has never seen my rules. obj0 and obj2 persisting through all ten frames while the segmenter narrates six moves is the marker-with-two-seats reading. obj4 is the whole 64-cell bar of which 4 cells are dynamic. obj3 is a 1006-cell colour-null blob that swallowed the maze floor AND the body ring: connected_components(4) cannot see the mover at all, because the mover is a ring of floor-adjacent pixels that merges with the floor, and THAT ABSENCE IS THE FINDING. None of these gets a type of its own; a second type on the same pixels invites the double claim rule 5 forbids. zero_space self-reports THIN in its own words -- 9 transitions constrain rank 5 of 375 features, null space dimension 370, 'nearly every vector in it is a law that is true over these states and unfalsified rather than confirmed' -- and its single global law is my census. cegis_miner refuses on every track and its verdict, 'the world does not narrate as one mover', remains true of the arm and false of the world: there is one mover, a rigid 24-pixel ring, and the arm can only see 24 simultaneous recolours, which is why movement costs a pair of rules per direction instead of one moved() event."
    [probe: passed]

  theorem what_i_predict_before_i_see_it "Written in advance so it can cost me. ACTION4 FROM SPAWN, command index 10: if the standard mapping holds, the world changes 48 cells in rows 8-12 cols 14-24 and burns (63,59) for 49 total, and MY MANUAL DRAWS NONE OF THEM -- no east rules exist and (63,59) is board -- so I expect a 49-cell divergence and that is the advertised price of the first step onto fresh ground, not a failure of physics. If instead ZERO cells change, ACTION4 is not east, ACTION3 is east by elimination, and action-keying is refuted too, because index 10 is even and parity demanded a burn. If exactly ONE cell changes and it is (63,59), ACTION4 is not east and both meter readings survive. ACTION2 FROM SPAWN: 48 cells I draw correctly plus a burn at (63,59) I cannot draw -- exactly one wrong pixel, every time, forever, until that cell has burned once. ACTION5 FROM SPAWN: I predict ZERO changed cells anywhere, on the strength of the spawn_probe guard and nothing else; any panel toggle there refutes the guard outright and means the toggle is bound to the key and not to the return. ACTION1 OR ACTION3 FROM SPAWN at an even index: zero cells under my manual, one cell at (63,59) under parity -- the cheapest single-bit experiment on the board, and worth buying only when no map question is open."
    [depends: the_action_map_after_nine_transitions_and_the_standard_mapping_hypothesis, the_meter_question_after_nine_transitions_and_why_it_is_still_open  probe: pending]

  theorem a_landmark_is_only_as_true_as_the_comment_beside_it "Kept in compressed form because the lesson is structural and cost a full round. Thirteen panel rules once carried `colored(spawn_probe, 5)` while the landmark line read `# arc-cell: carried, coordinates stripped`, which is not a coordinate; the grammar puts such a landmark at (0,0), (0,0) is background in every frame this world has drawn, and so all thirteen rules were unreachable text that fired never and clashed never. Responsibility passed, ambiguity passed, step crashed zero times, and ONLY replay caught it. The landmark now reads `# arc-cell: (8, 14)`, the top-left pixel of the spawn ring, which renders 9 while the body is home and 5 the moment it is anywhere else. Before ranking any probe, check that the rules it is meant to test can actually fire."
    [depends: key5_slot1_dims  probe: passed]
```

=== PLAYBOOK ===
```
# playbook.dsl -- what to buy with the next command, not a route.
#
# STATE OF PLAY (state 9): body home at lattice (1,2); panel in configuration
# B; four meter cells burned, (63,60)..(63,63); nine commands spent; the next
# command has index 10, which is EVEN.
#
# WHAT CHANGED THIS ROUND:
#  (a) THE FOUR REFUTATIONS COST WHAT THE MANUAL SAID THEY WOULD -- 23 cells
#      for the panel's unwitnessed half, one pixel per unwitnessed burn. No
#      line below caused them and none is retracted for them.
#  (b) THE REAL FAILURE IS NOT IN THE MANUAL, IT IS HERE. Nine commands have
#      been spent and the body has occupied exactly TWO lattice cells; six of
#      those commands were spent oscillating between them. An oscillation is
#      not a probe: the second ACTION2-then-ACTION5 pair bought two witnesses
#      the first pair had already bought, and the third bought none at all.
#      New prune, and it is the load-bearing line of this file: a command
#      that returns the body to a cell it has already occupied, from a cell
#      it has already occupied, with a key already witnessed there, is dead.
#  (c) ACTION4 NOW DOMINATES ACTION3 as the way to ask the east question.
#      At spawn, left is void and right is open floor. Either outcome of one
#      ACTION4 press names the east key -- it moves, or ACTION3 is east by
#      elimination, ACTION1 having been excluded from east at t1 -- and one
#      of the two outcomes also advances four cells' worth of route toward
#      the knob at lattice (1,6).
#  (d) THE METER SEPARATOR IS FREE AND NEEDS NO COMMAND OF ITS OWN. Every
#      command so far used a key whose parity matches its own index's parity,
#      which is exactly why nine transitions cannot separate action-keying
#      from command parity. Walking east breaks that alignment on the SECOND
#      step. Buying a dedicated parity probe now would pay a command for a
#      bit that arrives free.
#  (e) ONE PRESS IS ONE LATTICE CELL, 3/3. Every distance below is counted in
#      lattice cells, not pixels.
# No stored sequence anywhere: every line is a criterion on the current frame
# plus the manual's own open questions.

order     settle_the_east_key_before_routing_toward_the_knob                 [proof: lean]
order     prefer_the_probe_that_advances_over_the_probe_that_only_answers    [proof: lean]
order     probe_a_key_from_a_cell_where_exactly_one_candidate_is_open        [proof: lean]
order     take_a_separation_that_arrives_free_over_one_that_costs_a_command  [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it         [proof: lean]
order     identify_a_direction_key_before_routing_with_it                    [proof: lean]
order     separate_two_readings_before_planning_against_either               [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it                 [proof: lean]
order     reach_the_switch_before_testing_the_switch                         [proof: lean]
order     try_an_unpressed_key_before_declaring_a_dead_end                   [proof: lean]
order     witness_a_rule_before_writing_it                                   [proof: lean]
order     spend_commands_on_information_while_the_bar_is_still_long          [proof: lean]

prune     revisits_an_occupied_cell_by_an_already_witnessed_key => dead      [proof: lean]
prune     repeats_a_transition_whose_rule_already_has_full_coverage => dead  [proof: lean]
prune     dedicated_meter_probe_while_a_map_question_is_open => dead         [proof: lean]
prune     destination_ring_pixels_are_not_all_floor => dead                  [proof: lean]
prune     action_excluded_for_this_direction_by_an_earlier_no_op => dead     [proof: lean]
prune     route_that_crosses_the_comb_while_it_still_reads_eight => dead     [proof: lean]
prune     probe_where_both_live_readings_predict_the_same_pixel => dead      [proof: lean]
prune     probe_that_repeats_a_key_at_a_cell_that_cannot_separate_it => dead [proof: lean]
prune     guard_whose_landmark_carries_no_arc_cell_comment => dead           [proof: lean]
prune     meter_exhausted and not goal => dead                               [proof: lean]

heuristic lattice_distance_to_the_knob_while_the_gate_is_shut                [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open               [admissible: lean]
heuristic lattice_cells_the_body_has_never_occupied                          [admissible: lean]
heuristic live_readings_a_command_can_eliminate                              [admissible: lean]
heuristic open_questions_a_command_can_close                                 [admissible: lean]
heuristic cells_this_command_makes_ownable_for_the_first_time                [admissible: lean]
heuristic unwitnessed_rules_this_command_would_witness                       [admissible: lean]
heuristic commands_remaining_under_the_worse_of_the_two_meter_readings       [admissible: lean]
heuristic unexplained_cells_after_redraw                                     [admissible: lean]

prefer    a_direction_key_at_a_cell_where_its_two_candidates_disagree        [ev: 3/5 no_ops]
prefer    a_step_that_both_advances_and_witnesses_an_unwritten_rule          [ev: 3/3 moves]
prefer    a_cell_the_body_has_never_stood_in_over_one_it_has                 [ev: 2/11 cells]
prefer    east_along_lattice_row_one_over_any_other_axis                     [ev: 1/1 levels]
prefer    a_key_whose_parity_differs_from_the_command_index                  [ev: 0/9 commands]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                   [ev: 9/9 diffs]
prefer    distance_from_spawn_that_makes_up_undo_and_return_differ           [ev: 3/3 key5]
prefer    a_step_toward_the_knob_over_a_step_toward_the_socket               [ev: 1/1 levels]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered            [ev: 1/1 levels]
prefer    an_unpressed_key_over_repeating_a_known_no_op                      [ev: 2/7 keys]
```

=== LOG ===
```json
[
  {"id": "P-01", "subject": "probe_refutation P-01 (ACTION2, manual 25cac... vs world af3bb...)", "verdict": "accept",
   "why": "The manual's successor for ACTION2 from spawn repeats across P-01 and P-03 while the world's answers differ, which is the signature of a frozen counter: the missing piece is the second and later bar burn, restored as meter_burn_key2_next with witnesses t6 and t8."},
  {"id": "P-02", "subject": "probe_refutation P-02 (ACTION5, manual 9bb17... vs world 0e1cd...)", "verdict": "accept",
   "why": "The manual had no rule firing on a configuration-B panel, so its ACTION5 successor was body-up-with-panel-unchanged; t7 is the first B-to-A toggle ever seen and it accounts for exactly 23 cells, the price the previous manual quoted in the_five_rules_i_no_longer_have_a_witness_for."},
  {"id": "P-03", "subject": "probe_refutation P-03 (ACTION2, second occurrence)", "verdict": "entailed",
   "why": "Same hole as P-01, one burn further left at (63,60); it adds a second witness for meter_burn_key2_next and no new information, which is itself the evidence for the playbook's new anti-oscillation prune."},
  {"id": "P-04", "subject": "probe_refutation P-04 (ACTION5, third occurrence)", "verdict": "entailed",
   "why": "The A-to-B half again, already covered by key5_slot1_dims and its siblings; it raises their coverage from 8/8 to 16/16 and adds a third witness for the spawn_probe guard without adding the negative witness the guard still lacks."},
  {"id": "R-01", "subject": "key5_slot1_lights, key5_underline1_lights, key5_slot2_ring_resets, key5_slot2_centre_resets, key5_underline2_dims", "verdict": "accept",
   "why": "The B-to-A half of the panel, held as preserved prose since the window shrank, is witnessed by t7 with coverage 8+3+8+1+3 = 23 cells, and each is separated from its A-to-B twin by the pre-state colour alone (2 vs 9, 0 vs 9, 9 vs 1, 0 vs 1) so no instance admits two rules."},
  {"id": "R-02", "subject": "meter_burn_key2_next", "verdict": "accept",
   "why": "Struck last round for want of a witness, now witnessed twice: (63,61) at t6 and (63,60) at t8, each the unique Glyph9 instance whose right neighbour renders 1, and disjoint from meter_burn_key2_rightmost because colored(wall, 1) is false."},
  {"id": "R-03", "subject": "key2_body_leaves / key2_body_arrives", "verdict": "accept",
   "why": "Coverage rises from 24/24 to 72/72 over t2, t6 and t8 with no contradiction, and the net effect is identical all three times despite cascade lengths of 7, 9 and 7."},
  {"id": "R-04", "subject": "key5_body_clears / key5_body_respawns", "verdict": "accept",
   "why": "72/72 over t5, t7 and t9; the 48 body cells plus 23 panel cells reproduce the brief's 71 changed cells for each of those three commands exactly."},
  {"id": "R-05", "subject": "meter_burn_key4_rightmost (the key-4 twin of the rightmost rule)", "verdict": "reject",
   "why": "ACTION4 has never been pressed while (63,63) still rendered 9, so the rule has no witness at all; writing it would be a coverage claim with an empty evidence set."},
  {"id": "R-06", "subject": "key2_floor_leaves (descent from a cell that is not spawn)", "verdict": "probe-pending",
   "why": "All three descents started at spawn, so no transition witnesses Vacated pixels going 9 back to 5; the text is preserved verbatim in the_rules_i_still_have_no_witness_for and one ACTION2 from lattice (2,2) buys it."},
  {"id": "R-07", "subject": "eastward keyE_body_leaves / keyE_body_arrives pair", "verdict": "probe-pending",
   "why": "No eastward motion has ever been observed and the arrival cells rows 8-12 cols 20-24 are board with no instances, so even the correct rule could draw only half the step; both halves wait on the first ACTION4 press from spawn."},
  {"id": "O-01", "subject": "mdl obj0 (colour 9, 8 cells, 3x3, all 10 frames) and obj2 (colour 9, 1x3, all 10 frames)", "verdict": "entailed",
   "why": "A colour-9 ring and a colour-9 underline that persist through every frame while the segmenter narrates six move events is the same 23-cell panel swap my rules encode, seen as one marker travelling between two seats; both are already inside Glyph9 and Spent and get no type of their own."},
  {"id": "O-02", "subject": "mdl obj1 and obj6 (colour 1, 9 cells) and obj5 and obj7 (colour 2, 8 cells)", "verdict": "accept",
   "why": "Their first_frame and frames_present values read off the panel configuration sequence as A at 0-4, B at 5-6, A at 7-8, B at 9, which is independent corroboration of three toggles at t5, t7 and t9 from an engine that has never seen my rules."},
  {"id": "O-03", "subject": "mdl obj3 (1006 cells, colour null)", "verdict": "reject",
   "why": "connected_components(4) merged the maze floor with the body ring because the mover is floor-coloured at its boundary; accepting it as an object would double-claim every pixel Vacated already owns."},
  {"id": "O-04", "subject": "mdl obj4 (colour 9, 64 cells, row 63)", "verdict": "entailed",
   "why": "The whole bar, of which exactly four cells are dynamic and therefore instanced; the other sixty are board and that is precisely why the next burn is undrawable."},
  {"id": "O-05", "subject": "cegis_miner verdict 'the world does not narrate as one mover'", "verdict": "accept",
   "why": "True of the arm and false of the world: the mover is a rigid 24-pixel ring the arm can only see as 24 simultaneous recolours, which is why every direction costs a leaves-rule and an arrives-rule instead of one moved() event."},
  {"id": "L-01", "subject": "zero_space single global law over 75 cells", "verdict": "entailed",
   "why": "Its cell list is exactly my census -- (2,1) and (2,3) but not (2,2), the four ring cells of row 10 but not the aperture (10,16), and all four burned bar cells -- and its own THIN verdict says rank 5 of 375 features, so it confirms the accounting and licenses no law."},
  {"id": "L-02", "subject": "meter reading A (burns iff key is 2 or 4) versus reading B (burns iff command index is even)", "verdict": "probe-pending",
   "why": "Both score 9/9 and cannot be separated here because every command so far used a key whose parity equals its index's parity; reading A is encoded because parity is inexpressible in the guard language, and the strain on A is that ACTION3 and ACTION4 were blocked identically at lattice (2,2) yet only ACTION4 burned."},
  {"id": "L-03", "subject": "standard action mapping (1 up, 2 down, 3 left, 4 right, 5 undo-or-return)", "verdict": "probe-pending",
   "why": "It is the only assignment consistent with all four observed no-ops -- including the new fact that at t3 and t4 both up and down were OPEN at lattice (2,2) and neither ACTION3 nor ACTION4 moved -- but it rests on a prior about this action family, and one ACTION4 press at spawn tests it."},
  {"id": "L-04", "subject": "cascade length 7 for ACTION2 in panel configuration A, 9 in configuration B", "verdict": "probe-pending",
   "why": "Three samples with a clean correlation and identical net effects; recorded as an anomaly rather than physics because cascade single_frame compares net effects only, so it costs nothing either way and is not yet evidence of unobservable state."},
  {"id": "L-05", "subject": "spawn_probe guard on the thirteen panel rules", "verdict": "probe-pending",
   "why": "Three positive witnesses and still no negative one, because every ACTION5 in the window followed an ACTION2 and so had the body away; kept because it makes the manual predict silence for an ACTION5 pressed here, which is falsifiable in one command."},
  {"id": "E-01", "subject": "owning a bar cell that has not yet burned", "verdict": "reject",
   "why": "I wanted to predict the fifth burn at (63,59); the arm instances only cells that have already changed, so an unburned bar cell is board and no rule can draw its first change. I wrote the_manual_heals_one_step_behind instead, which prices this at exactly one wrong pixel per burn and zero forever after."},
  {"id": "E-02", "subject": "one rule for slot 2's eight ring cells instead of four", "verdict": "reject",
   "why": "The ring is the complement of a centre defined by four colour-1 neighbours and the guard language has no disjunction; `not` is documented but untried, and a parse error costs the whole compile, so I kept the four working row-and-column rules and said so in off_board_cell_terms_evaluate_false."},
  {"id": "E-03", "subject": "modelling the panel as one 3x3 marker that moves between slots", "verdict": "reject",
   "why": "mdl_segmenter's move narration is the better description, but moved(o, dir) displaces one cell and the arm gives one instance per cell, so an eight-pixel ring travelling four columns is not expressible; the ten recolour rules are the shortest thing this DSL can say."}
]
```
```
