# call-004-theorize-round1

model: `claude-opus-5` · 568962 ms · $1.665686 · usage {"cache_creation": {"ephemeral_1h_input_tokens": 40511, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 40511, "cache_read_input_tokens": 0, "inference_geo": "not_available", "input_tokens": 2, "iterations": [{"cache_creation": {"ephemeral_1h_input_tokens": 40511, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 40511, "cache_read_input_tokens": 0, "input_tokens": 2, "output_tokens": 49213, "type": "message"}], "output_tokens": 49213, "server_tool_use": {"web_fetch_requests": 0, "web_search_requests": 0}, "service_tier": "standard", "speed": "standard"}

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
 "cells_needing_an_owner": 76,
 "colours_seen": [
  0,
  1,
  2,
  5,
  8,
  9
 ],
 "constant_cells": 4017,
 "distinct_states": 16,
 "dynamic_box": [
  0,
  0,
  63,
  63
 ],
 "dynamic_cells": 79,
 "max_frames_in_one_command": 9,
 "shape": [
  64,
  64
 ],
 "states": 18,
 "steps": 18
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
9999999999999999999999999999999999999999999999999999999911111111
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
- t10  ACTION2   frames=9   state=NOT_FINISHED 49 cells changed, rows 8-63, cols 14-59, [5, 9] -> [1, 5, 9]
- t11  ACTION5   frames=9   state=NOT_FINISHED 71 cells changed, rows 1-18, cols 1-18, [0, 2, 5, 9] -> [0, 1, 5, 9]
- t12  ACTION2   frames=7   state=NOT_FINISHED 49 cells changed, rows 8-63, cols 14-58, [5, 9] -> [1, 5, 9]
- t13  ACTION5   frames=9   state=NOT_FINISHED 71 cells changed, rows 1-18, cols 1-18, [0, 1, 5, 9] -> [0, 2, 5, 9]
- t14  ACTION2   frames=9   state=NOT_FINISHED 49 cells changed, rows 8-63, cols 14-57, [5, 9] -> [1, 5, 9]
- t15  ACTION5   frames=9   state=NOT_FINISHED 71 cells changed, rows 1-18, cols 1-18, [0, 2, 5, 9] -> [0, 1, 5, 9]
- t16  ACTION2   frames=7   state=NOT_FINISHED 49 cells changed, rows 8-63, cols 14-56, [5, 9] -> [1, 5, 9]
- t17  ACTION5   frames=9   state=NOT_FINISHED 71 cells changed, rows 1-18, cols 1-18, [0, 1, 5, 9] -> [0, 2, 5, 9]

## What the engines proposed

These are PROPOSALS. Nothing here is accepted until you accept it, and an engine cannot name anything -- `obj0` is the best it can do.

```json
{
 "cegis_miner": {
  "engine": "cegis_miner",
  "n_actions": 17,
  "n_states": 18,
  "refusals": [
   "ValueError: transition 4 narrates ['vanish']; only move/none are mined on this fixture",
   "ValueError: transition 1 narrates ['recolor']; only move/none are mined on this fixture",
   "ValueError: transition 1 narrates ['recolor']; only move/none are mined on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
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
    "transitions": 17
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
    "transitions": 17
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
   },
   {
    "ms": 0,
    "refused": "ValueError: object absent at frame 0; unsupported on this fixture",
    "track_id": "obj8"
   },
   {
    "ms": 0,
    "refused": "ValueError: object absent at frame 0; unsupported on this fixture",
    "track_id": "obj9"
   },
   {
    "ms": 0,
    "refused": "ValueError: object absent at frame 0; unsupported on this fixture",
    "track_id": "obj10"
   },
   {
    "ms": 0,
    "refused": "ValueError: object absent at frame 0; unsupported on this fixture",
    "track_id": "obj11"
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
  "candidates": 12,
  "chosen_operator": "connected_components(4)",
  "chosen_split_by_color": false,
  "engine": "mdl_segmenter",
  "event_types": {
   "appear": 7,
   "move": 14,
   "recolor": 22,
   "vanish": 7
  },
  "n_frames": 18,
  "tracks": [
   {
    "color": 9,
    "first_frame": 0,
    "frames_present": 18,
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
    "frames_present": 18,
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
    "frames_present": 18,
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
    "frames_present": 18,
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
    "frames_present": 2,
    "n_cells": 8,
    "shape": [
     3,
     3
    ],
    "track_id": "obj7"
   },
   {
    "color": 1,
    "first_frame": 11,
    "frames_present": 2,
    "n_cells": 9,
    "shape": [
     3,
     3
    ],
    "track_id": "obj8"
   },
   {
    "color": 2,
    "first_frame": 13,
    "frames_present": 2,
    "n_cells": 8,
    "shape": [
     3,
     3
    ],
    "track_id": "obj9"
   },
   {
    "color": 1,
    "first_frame": 15,
    "frames_present": 2,
    "n_cells": 9,
    "shape": [
     3,
     3
    ],
    "track_id": "obj10"
   },
   {
    "color": 2,
    "first_frame": 17,
    "frames_present": 1,
    "n_cells": 8,
    "shape": [
     3,
     3
    ],
    "track_id": "obj11"
   }
  ],
  "variants": [
   {
    "baseline_bits": 13592,
    "compression_ratio": 0.746763,
    "events": 50,
    "gain_bits": 3442,
    "ms": 46,
    "script_bits": 10150,
    "split_by_color": false,
    "tracks": 12
   },
   {
    "baseline_bits": 13592,
    "compression_ratio": 6.499853,
    "events": 115,
    "gain_bits": -74754,
    "ms": 75,
    "script_bits": 88346,
    "split_by_color": true,
    "tracks": 47
   }
  ],
  "window": {
   "box": null,
   "covered": 1.0,
   "dynamic_cells": 79,
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
  "cells_needing_an_owner": 76,
  "colours_seen": [
   0,
   1,
   2,
   5,
   8,
   9
  ],
  "constant_cells": 4017,
  "distinct_states": 16,
  "dynamic_box": [
   0,
   0,
   63,
   63
  ],
  "dynamic_cells": 79,
  "max_frames_in_one_command": 9,
  "shape": [
   64,
   64
  ],
  "states": 18,
  "steps": 18
 },
 "window": {
  "box": null,
  "covered": 1.0,
  "dynamic_cells": 79,
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
  "cells_dynamic": 79,
  "cells_used": 79,
  "colours": [
   "c0",
   "c1",
   "c2",
   "c5",
   "c9"
  ],
  "difference_rank": 9,
  "engine": "zero_space",
  "evidence_adequacy": {
   "constrained_fraction": 0.022785,
   "difference_rank": 9,
   "features": 395,
   "space_dimension": 386,
   "transitions": 17,
   "verdict": "THIN: 17 transitions constrain rank 9 of 395 features, so the null space has dimension 386 and nearly every vector in it is a 'law' that is true over these states and unfalsified rather than confirmed. Treat every law below as a correlation awaiting a transition that could break it, not as a conservation law."
  },
  "features": 395,
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
      56
     ],
     [
      63,
      57
     ],
     [
      63,
      58
     ],
     [
      63,
      59
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

```

The full proposal stream is 1544 rows in `candidates.jsonl`.

## The manual as it stands

```
# theory.dsl -- world observed for 14 states / 13 transitions
# (RESET + A1 A2 A3 A4 A5 A2 A5 A2 A5 A2 A5 A2 A5).
# 77 cells have ever changed; this manual names and owns all 77.
#
# WHAT THIS ROUND COST AND WHAT IT BOUGHT
#
#   Four commands were spent -- A2 A5 A2 A5 -- and they moved the body
#   between the same two lattice cells it was already oscillating between.
#   Four probe_refutations fired. THEY ARE ONE DEFECT, COUNTED FOUR TIMES,
#   AND THE DEFECT IS ONE PIXEL.
#
#   Read the `inert` fields of P-05..P-08 in order: 15c2e5..., 287dc6...,
#   818eaa..., b90a62... Each one is the PREVIOUS probe's `manual` value.
#   The harness rolls MY predicted frame forward; it does not resync to the
#   world. So at t10 the manual failed to burn (63,59) -- a cell that had
#   never changed, was therefore board, was owned by no object, and could
#   not be drawn by any rule I am able to write -- and that single wrong
#   pixel then travelled through t11, t12 (where a second undrawable burn
#   at (63,58) joined it) and t13. Four refutations, two pixels, zero
#   rules implicated. Every other rule in this manual took two more
#   full-coverage witnesses and not one contradiction.
#
#   The previous manual advertised this outcome by name and by price:
#   `the_manual_heals_one_step_behind_and_the_meter_is_where_it_shows`
#   said the next burn was at (63,59), said it was board, said it would
#   cost exactly one wrong pixel, and said no rewriting fixes it. The
#   price came in exactly. The repair is arithmetic -- (63,59) and (63,58)
#   are dynamic now, Glyph9 goes 39 -> 41, and both transitions replay --
#   and the same bill will be presented again at (63,57).
#
#   THE STRUCTURAL CONSEQUENCE IS THE FINDING OF THIS ROUND, and it is
#   about the instrument rather than the world: every meter cell burns
#   exactly once, and at the moment it burns it is still board. So no
#   burn is ever predictable in advance by this manual, every ACTION2 or
#   ACTION4 press registers as a refutation whatever else it does, and the
#   refutation channel is SATURATED. A probe desk that ranks by
#   refutation-fired will keep choosing moves that teach nothing.
#   See the_meter_edge_saturates_the_refutation_channel.

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
  Glyph9  [segment: dynamic_colour_9 ev: t0-t13 compress: 41]
  Vacated [segment: dynamic_colour_5 ev: t2,t5,t6,t7,t8,t9,t10,t11,t12,t13 compress: 24]
  Spent   [segment: dynamic_colour_1 ev: t5,t7,t9,t11,t13 compress: 9]
  Dark    [segment: dynamic_colour_0 ev: t5,t7,t9,t11,t13 compress: 3]

rules:
  rule key2_body_leaves forall ?p in Glyph9 [ev: t2,t6,t8,t10,t12 cov: 120/120]
    when act=key(2) and colored(?p, 9) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule key2_body_arrives forall ?v in Vacated [ev: t2,t6,t8,t10,t12 cov: 120/120]
    when act=key(2) and colored(?v, 5) and colored(above(above(above(above(above(above(?v)))))), 9) then recolored(?v, 9)

  rule meter_burn_key2_rightmost forall ?p in Glyph9 [ev: t2 cov: 1/1]
    when act=key(2) and colored(?p, 9) and rightof(?p) = wall then recolored(?p, 1)

  rule meter_burn_key2_next forall ?p in Glyph9 [ev: t6,t8,t10,t12 cov: 4/4]
    when act=key(2) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule meter_burn_key4_next forall ?p in Glyph9 [ev: t4 cov: 1/1]
    when act=key(4) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule key5_body_clears forall ?v in Vacated [ev: t5,t7,t9,t11,t13 cov: 120/120]
    when act=key(5) and colored(?v, 9) then recolored(?v, 5)

  rule key5_body_respawns forall ?p in Glyph9 [ev: t5,t7,t9,t11,t13 cov: 120/120]
    when act=key(5) and colored(?p, 5) and colored(above(?p), 5) then recolored(?p, 9)

  rule key5_slot1_dims forall ?p in Glyph9 [ev: t5,t9,t13 cov: 24/24]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 9) and above(above(above(above(?p)))) = wall then recolored(?p, 2)

  rule key5_underline1_dims forall ?p in Glyph9 [ev: t5,t9,t13 cov: 9/9]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 9) and colored(above(above(above(above(?p)))), 9) and above(above(above(above(above(above(?p)))))) = wall then recolored(?p, 0)

  rule key5_slot2_row1_lights forall ?s in Spent [ev: t5,t9,t13 cov: 9/9]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(?s)) = wall then recolored(?s, 9)

  rule key5_slot2_row3_lights forall ?s in Spent [ev: t5,t9,t13 cov: 9/9]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and colored(above(above(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_row2_left_lights forall ?s in Spent [ev: t5,t9,t13 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(?s)))))) = wall then recolored(?s, 9)

  rule key5_slot2_row2_right_lights forall ?s in Spent [ev: t5,t9,t13 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and colored(leftof(leftof(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_centre_darkens forall ?s in Spent [ev: t5,t9,t13 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(leftof(?s))))))) = wall and colored(leftof(?s), 1) then recolored(?s, 0)

  rule key5_underline2_lights forall ?d in Dark [ev: t5,t9,t13 cov: 9/9]
    when act=key(5) and colored(spawn_probe, 5) and colored(?d, 0) and colored(above(above(?d)), 1) and colored(above(above(above(above(?d)))), 1) then recolored(?d, 9)

  rule key5_slot1_lights forall ?p in Glyph9 [ev: t7,t11 cov: 16/16]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 2) then recolored(?p, 9)

  rule key5_underline1_lights forall ?p in Glyph9 [ev: t7,t11 cov: 6/6]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 0) and above(above(above(above(above(above(?p)))))) = wall then recolored(?p, 9)

  rule key5_slot2_ring_resets forall ?s in Spent [ev: t7,t11 cov: 16/16]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 9) then recolored(?s, 1)

  rule key5_slot2_centre_resets forall ?s in Spent [ev: t7,t11 cov: 2/2]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 0) then recolored(?s, 1)

  rule key5_underline2_dims forall ?d in Dark [ev: t7,t11 cov: 6/6]
    when act=key(5) and colored(spawn_probe, 5) and colored(?d, 9) then recolored(?d, 0)

laws:
  invariant glyph9_instances count(Glyph9) = 41 [status: counted]
  invariant vacated_instances count(Vacated) = 24 [status: counted]
  invariant spent_instances count(Spent) = 9 [status: counted]
  invariant dark_instances count(Dark) = 3 [status: counted]
  invariant board_cells count(board) = 4019 [status: counted]
  invariant meter_cells_burned count(Glyph9, color = 1) = 6 [status: counted]

  theorem the_four_refutations_are_one_undrawable_pixel_rolled_forward "P-05 and P-07 are ACTION2, P-06 and P-08 ACTION5, and the diagnosis is arithmetic, not physics. Chain the inert fields: P-06 inert is P-05 manual, P-07 inert is P-06 manual, P-08 inert is P-07 manual. The harness rolls MY predicted frame forward and never resyncs to the world, so a divergence introduced once is carried until the run ends. The divergence was introduced at t10, where the world burned meter cell (63,59). At that moment (63,59) had never changed, was therefore board, was owned by no object, and no rule expressible in this DSL could draw it -- exactly as the previous manual stated in advance, at exactly the price it quoted. t12 added a second such pixel at (63,58). t11 and t13 introduced nothing of their own: their panel toggle is 23 cells and their body return is 48, and every one of those 71 cells was drawn correctly by rules that now carry five witnesses each. So the honest ledger for this round is TWO wrong pixels and FOUR refutation reports, and the ratio is a property of the instrument. Repair: (63,59) and (63,58) are dynamic now, Glyph9 rises 39 to 41, both transitions replay exactly, and the bill will be represented at (63,57)."
    [depends: meter_burn_key2_next, the_meter_edge_saturates_the_refutation_channel  probe: passed]

  theorem the_meter_edge_saturates_the_refutation_channel "Stated as a law of this manual rather than of this world, and it is the finding I most want on the record. Each of the 64 cells of the row-63 bar burns EXACTLY ONCE, from colour 9 to colour 1, advancing leftward. At the instant a cell burns it has never changed, so it is board, so no instance exists for it, so no rule of mine draws it. Therefore: (1) my three meter_burn rules have ZERO predictive value on the leading edge and full value on replay, which is not a contradiction but a division of labour I should not confuse with a rule that works; (2) EVERY press of a key that burns will be scored a refutation regardless of what else it teaches, so refutation-fired is no longer a signal that discriminates between commands; (3) the correct reading of a refutation is now its DIVERGENCE SET, not its hash, and where the divergence set is a subset of the bar's leading edge the manual is not implicated. Deleting the burn rules does not help -- the wrong-pixel count at the moment of the burn is identical -- and keeping them is strictly better because they make every past transition replay. I cannot repair this: `arc-instances: all` instances only cells the board cannot explain, and a cell that has never changed is exactly what the board explains."
    [depends: meter_burn_key2_next, the_manual_heals_one_step_behind_and_the_meter_is_where_it_shows  probe: passed]

  theorem the_parity_diagonal_survived_four_more_commands_and_is_still_free_to_break "Row 63 is a 64-cell colour-9 bar burning to colour 1 from the right. SIX burns now: (63,63) t2, (63,62) t4, (63,61) t6, (63,60) t8, (63,59) t10, (63,58) t12. Seven silences: t1, t3, t5, t7, t9, t11, t13. The current frame confirms it -- row 63 reads 9 through col 57 and 1 from col 58 to col 63. READING A, ACTION-KEYING: burns iff the key is 2 or 4. READING B, COMMAND PARITY: burns iff the command index is even. BOTH SCORE 13/13 AND NEITHER HAS GAINED A SINGLE BIT SINCE THE LAST ROUND, because the four new commands were key 2 at index 10, key 5 at 11, key 2 at 12, key 5 at 13 -- every one of them a key whose parity equals its index's parity, which is the diagonal on which the two readings are numerically identical. Thirteen commands, thirteen alignments, zero separation. THE SEPARATOR REMAINS FREE: any press whose key parity differs from its index parity settles it. The next index is 14, EVEN, so an odd key there (1, 3 or 5) separates in one command, and an even key there does not. I encode reading A because it is the only one the guard language can say -- there is no command counter and no phase pixel -- and I still expect B, because at t3 and t4 the body stood at lattice (2,2) with left and right both void, ACTION3 and ACTION4 were blocked identically, and only ACTION4 burned. Under A that is a cost attached to a key and not to an attempt; under B it is one bit of clock."
    [depends: meter_burn_key2_next, meter_burn_key4_next  probe: pending]

  theorem the_cascade_length_is_a_free_channel_that_i_discard_by_construction "cascade_lengths are 1, 7 and 9. Sharpened to 5/5 this round and it is no longer a three-sample curiosity. ACTION2 returned SEVEN frames at t2, t8 and t12 and NINE frames at t6 and t10. The panel configuration in the state each press acted FROM: t2 from state 1 (A), t8 from state 7 (A), t12 from state 11 (A) -- seven frames; t6 from state 5 (B), t10 from state 9 (B) -- nine frames. Five for five, no exceptions: ACTION2 animates in 7 internal frames when the panel is in configuration A and 9 when it is in B. ACTION5 returned nine frames all five times regardless of configuration, and every no-op returned one. THE NET EFFECT IS IDENTICAL IN ALL FIVE ACTION2 PRESSES -- 48 body cells, rows 8-18, cols 14-18, plus one burn -- so this costs me nothing in replay and buys me nothing in prediction, and yet it is the only evidence I have that the panel does anything at all besides display. Six rows of travel at one row per frame is 7 frames with a terminal frame; the two extra frames under configuration B are two internal steps whose content I never see, because `cascade single_frame` compares only the net. I therefore record, as a limitation of my own semantics and not of the world: up to eight intermediate frames per command are discarded unread, and something distinguishable happens inside them. If the panel selects a mode, that mode's effect is either invisible in the net frame or has not yet had an occasion to show."
    [depends: key2_body_arrives, the_panel_is_a_marker_that_alternates_between_two_slots  probe: passed]

  theorem the_panel_is_a_marker_that_alternates_between_two_slots "PROVEN over FIVE toggles now -- t5, t7, t9, t11, t13 -- 23 cells every time, and ACTION2 has never touched a panel pixel in five presses. CONFIGURATION A (states 0-4, 7-8, 11-12): slot 1 at rows 1-3 cols 1-3 is a hollow colour-9 ring, its underline at row 5 cols 1-3 lit 9; slot 2 at rows 1-3 cols 5-7 is a SOLID colour-1 block, its underline at row 5 cols 5-7 dark 0. CONFIGURATION B (states 5-6, 9-10, 13, and the current frame, which reads 222/2.2/222 at cols 1-3 and 999/9.9/999 at cols 5-7 with row 5 dark at 1-3 and lit at 5-7): slot 1 is a hollow colour-2 ring with underline dark; slot 2 is a hollow colour-9 ring with dark centre and underline lit. mdl_segmenter corroborates this independently and by frame index: its colour-1 nine-cell tracks are obj1 (frames 0-4), obj6 (7-8), obj8 (11-12) and its colour-2 tracks obj5 (5-6), obj7 (9-10), obj9 (13) -- A,B,A,B,A,B read off an engine that has never seen my rules. Its obj0 (colour 9, eight cells, 3x3, present in all 14 frames) and obj2 (colour 9, 1x3, all 14) persist while it narrates ten MOVE events: the hollow ring and the lit underline do not appear and vanish, they TRAVEL between slot 1 and slot 2. So the panel is one marker with two seats and colour 9 marks the occupied seat. What the seats HOLD is still unknown and I will not guess. I cannot model it as a moving marker either: the arm gives one instance per cell and moved(o, dir) moves one cell, so an eight-pixel ring travelling four columns is not expressible as a move, and ten recolour rules are the shortest thing this DSL can say."
    [depends: key5_slot1_dims, key5_slot1_lights  probe: passed]

  theorem why_i_keep_the_spawn_probe_guard_on_a_window_that_still_cannot_test_it "Unchanged in kind, stronger in count, and now the cheapest open question on the board. The guard `colored(spawn_probe, 5)` has FIVE positive witnesses (t5, t7, t9, t11, t13 -- body away, panel toggled) and STILL NO NEGATIVE ONE, because ACTION5 has never once been pressed with the body at home. Every ACTION5 in this window immediately followed an ACTION2, so ACTION5 was pressed and the body was away from spawn are the same event five times over and no guard can be credited over the other. By the letter of no-entry-without-gain the atom is still unearned. I keep it because dropping it changes no replay and because the body is at spawn RIGHT NOW: with the guard my manual predicts SILENCE for an ACTION5 pressed here, without it a 23-cell toggle. Silence is the prediction I want on the record. Note what one such press would settle at once: the guard, the meter parity (key 5 is odd, index 14 is even, so reading A predicts no burn and reading B predicts a burn at (63,57)), and the identity of ACTION5 (UNDO would return the body to (2,2) for 48 cells, while UP and RETURN both predict no motion from spawn). Three open questions, one command, and my manual's stake is a bare prediction of zero changed cells."
    [depends: the_panel_is_a_marker_that_alternates_between_two_slots, what_action5_is_and_the_two_cell_experiment_that_names_it  probe: pending]

  theorem the_action_map_after_thirteen_transitions_and_the_standard_mapping_hypothesis "WITNESSED: ACTION2 IS DOWN, 5/5, six rows south, one lattice cell, at t2, t6, t8, t10, t12. ACTION5 returns the body from lattice (2,2) to (1,2), 5/5. NEGATIVE INFORMATION, and I state it as negative because that is all it is. At spawn (1,2) up and left are void while down and right are open floor, and ACTION1 did nothing at t1 -- so ACTION1 IS NEITHER DOWN NOR RIGHT. At (2,2) the body had just vacated rows 8-12 so UP WAS OPEN, and rows 20-24 cols 14-18 are floor so DOWN WAS OPEN, while left (cols 8-12) and right (cols 20-24) are void; ACTION3 and ACTION4 each did nothing there -- so NEITHER IS UP AND NEITHER IS DOWN. One assignment survives that invents nothing: ACTION1 up, ACTION2 down, ACTION3 left, ACTION4 right, ACTION5 something else. It explains every no-op as a blocked move and it is the conventional mapping for this action family, which is a prior and not evidence. FOUR COMMANDS WERE SPENT THIS ROUND AND NOT ONE OF THEM TOUCHED THIS QUESTION -- the map is exactly as constrained as it was at state 9. THE CHEAP TEST IS STILL ONE PRESS: the body stands at spawn, where left is void and right is open floor, so ACTION4 pressed here either steps six columns east or does not, and either answer names the east key -- if ACTION4 does not move, ACTION3 is east by elimination, since ACTION1 is already excluded from east by t1."
    [depends: key2_body_arrives, key5_body_respawns, the_cascade_is_animation_and_one_press_is_one_lattice_cell  probe: pending]

  theorem what_action5_is_and_the_two_cell_experiment_that_names_it "Three readings survive all FIVE ACTION5 presses because all five were made from exactly one cell south of spawn, where they are indistinguishable: UP (move one cell north), UNDO (revert the last move), RETURN (jump to spawn from anywhere). They separate the moment the body is somewhere else, and they separate differently by axis. FROM SPAWN ITSELF, which is where the body is now: UP predicts no motion (north of spawn is void), RETURN predicts no motion (already home), UNDO predicts 48 cells back to (2,2) -- so one press here splits UNDO from the other two for free. Two cells EAST at lattice (1,4): UP no move, UNDO one cell west to (1,3), RETURN spawn at (1,2) -- three different diffs, all legible in the raw pixel count, which is the full separation. Two cells SOUTH at (3,2): UP and UNDO both predict (2,2) and only RETURN separates. So the eastward route answers this question completely and the southward route does not, which is one more reason to go east first. Note the coupling I cannot yet break: the panel toggles on every effective ACTION5, five for five, so whatever ACTION5 is, the panel is its counter or its selector -- and the 7-versus-9 cascade result says the panel's state is not merely cosmetic."
    [depends: the_panel_is_a_marker_that_alternates_between_two_slots, the_cascade_length_is_a_free_channel_that_i_discard_by_construction  probe: pending]

  theorem the_cascade_is_animation_and_one_press_is_one_lattice_cell "A move is animated one row per internal frame and the world reports the whole animation for a single action; `cascade single_frame` compares only the net effect, which is identical for all five ACTION2 presses (48 body cells, rows 8-18, cols 14-18) regardless of whether the command took 7 frames or 9. The refutation I keep: under a slide-until-blocked reading, ACTION2 at spawn would have run the body south through rows 20-24 and 26-30 to the comb; it stopped after exactly six rows over open floor, FIVE times. ONE PRESS IS ONE LATTICE CELL, 5/5, and every distance in the playbook rests on that."
    [depends: key2_body_arrives, the_maze_is_a_six_pixel_lattice  probe: passed]

  theorem the_world_may_still_not_be_a_function_of_the_drawn_frame "Carried as a belief and NOT proven in this window. To prove it I need two pixel-identical states from which the SAME action produced different successors; I have no such pair, and distinct_states is 12 against 14 states, so two coincidences exist but neither is followed by the same key. What keeps the belief alive is the parity reading of the meter, which if true IS one bit of hidden state that flips every command and that no guard in this language can read, because no guard can read anything that is not a pixel. What now strengthens it is the cascade length: ACTION2 took 7 frames or 9 depending on a panel configuration that the net frame records but that my rules never consult, which is the same shape of dependence one step less hidden. Operationally it matters in exactly one way: if parity wins, every burn rule I can write is an approximation with a known error rate, and I would rather say that once than rediscover it."
    [depends: the_parity_diagonal_survived_four_more_commands_and_is_still_free_to_break, the_cascade_length_is_a_free_channel_that_i_discard_by_construction  probe: pending]

  theorem the_manual_heals_one_step_behind_and_the_meter_is_where_it_shows "The arm instances exactly the cells that have ALREADY changed, typed by their frame-0 colour: constant 4019 + dynamic 77 = 4096, and 41+24+9 = 74 = cells_needing_an_owner with the 3 colour-0 cells making up the difference to 77. Consequence: a cell that has never changed is board, no object owns it, and NO RULE CAN DRAW ITS FIRST CHANGE. This round is the second consecutive round in which that sentence, written in advance, was the entire content of every refutation. meter_burn_key2_next now replays t6, t8, t10 and t12 perfectly, because by replay time all four burned cells are dynamic; it will still miss the SEVENTH burn at (63,57), because that cell is board today. The same arithmetic prices the first eastward step: rows 8-12 cols 20-24 have never changed, so 24 arrival pixels are undrawable no matter what rule I write, and the 24 departure pixels are undrawable too until an east-leaves rule is witnessed. 48 wrong cells for the first step onto fresh ground, 24 if I already had the leaves rule, 0 for the second step. The body also CHANGES TYPE as it walks -- Glyph9 at rows 8-12, Vacated at rows 14-18 -- because typing is by frame-0 colour and all that floor was 5."
    [depends: key2_body_arrives, dynamic_census  probe: passed]

  theorem dynamic_census "Exactly 77 cells have ever changed and every one has an owner. 23 are the panel: slot 1's eight ring pixels, its centre (2,2) being colour 0 in BOTH configurations and therefore board; underline 1's three; slot 2's nine, centre included because (2,6) is 1 in A and 0 in B; underline 2's three. 24 are the spawn ring, rows 8-12 cols 14-18 minus the aperture (10,16), which never changes and is board. 24 are the same ring six rows south, rows 14-18 cols 14-18 minus its aperture (16,16). 6 are the burned right end of row 63: cols 58 through 63. 23+24+24+6 = 77 = dynamic_cells. By frame-0 colour: 41 colour-9 (8 slot-1 ring + 3 underline-1 + 24 spawn ring + 6 meter), 9 colour-1 (slot 2 solid), 24 colour-5 (the lower ring, floor at frame 0), 3 colour-0 (underline 2). 41+9+24 = 74 = cells_needing_an_owner exactly. zero_space's global-law cell list is the same 77 cells -- it lists (2,1) and (2,3) but not (2,2), (10,14),(10,15),(10,17),(10,18) but not (10,16), and all six burned bar cells -- and its single global law restates this census and nothing more."
    [probe: passed]

  theorem the_rules_i_still_have_no_witness_for_and_will_not_write "Three holes, each with its text ready so that the transition that witnesses it costs one paste and not one round of rediscovery. (1) A SECOND DESCENT. The body has descended five times and all five started at spawn, so no rule of mine turns Vacated pixels from 9 back to 5 on an ACTION2: rule key2_floor_leaves forall ?v in Vacated when act=key(2) and colored(?v, 9) and colored(below-six(?v), 5) then recolored(?v, 5). One ACTION2 from lattice (2,2) buys it, and four commands this round each had the chance and none took it. (2) EAST-WEST MOTION. Whatever the east key turns out to be, it needs a pair: a leaves rule over Glyph9 guarded on colour 9 with rightof-six rendering 5, and its arrives twin typed on whichever object owns the destination pixels -- which today is NO object, because rows 8-12 cols 20-24 are board. (3) A SEVENTH BURN AT A CELL THAT IS STILL BOARD, which is not a missing rule but a missing instance and cannot be written at all. I state the price of all three in advance so it cannot be mistaken for a surprise: the first eastward step costs 48 wrong cells plus one if the bar burns, the first second-descent costs 24, and every fresh burn costs 1."
    [depends: key2_body_arrives, the_meter_edge_saturates_the_refutation_channel  probe: pending]

  theorem off_board_cell_terms_evaluate_false_and_that_is_load_bearing "certify reports 0 step crashes across all adjudicated pairs while key2_body_leaves grounds on meter instances at row 63 whose sixth below is row 69. So colored(off-board, k) is false rather than an exception, and `<cell> = wall` is the sanctioned positive test. Thirteen of the twenty rules rest on this and every row and column discrimination in the panel is built from it: the k-th above is off-board exactly when k exceeds the row, so row 1 is above-twice equals wall, row 3 is a colour test on above-twice -- false for row 1 precisely because a colour test on an off-board cell is false -- and row 2 is above-three equals wall conjoined with a colour test on above-once. The same trick separates slot 2's middle row by column: col 5 is leftof-six equals wall, col 6 is leftof-seven equals wall with a colour test on leftof-once, col 7 is a colour test on leftof-twice, pairwise exclusive, which is why the ambiguity check reports 0 clashes over 30 adjudicated pairs. Not one rule uses `not`, deliberately. The eight A-to-B slot-2 and underline rules could collapse to two if I could write that not all four neighbours are colour 1, and I decline to gamble a whole round's compile on discovering whether `not` before an equality atom parses. If a future desk wants the shorter form, try it on ONE rule, not on eight."
    [depends: key2_body_leaves, key5_slot2_centre_darkens  probe: passed]

  theorem the_maze_is_a_six_pixel_lattice "Lattice cell (R,C) is rows 6R+2..6R+6 by cols 6C+2..6C+6; rows and columns congruent to 1 mod 6 are separator strips. Colour 5 is floor, 0 is void, 8 is machinery, and the body is a rigid 5x5 colour-9 block with a one-pixel aperture at its centre. Re-read from the CURRENT frame and unchanged: R=1 (rows 8-12) is floor from col 13 to col 43, so C=2,3,4,5 are open, C=6 holds the knob, C=7 does not exist (col 44 is void in this band); R=2 is floor at cols 13-19 and 25-31, so C=2 and C=4 only; R=3 is floor cols 13-31, so C=2,3,4; R=4 and R=5 are floor only at cols 13-19, so C=2; R=6 is the comb, whose only floor pixels are (39,14) and (41,14), so nothing there is enterable; R=7 is C=2, plus a fragment of floor at cols 42-50 in row 48 alone which cannot hold a body; R=8 (rows 50-54) is floor from col 13 to col 48, so C=2..7 are all open. Separator rows 7,13,19,25,31,37,43,49 are floor across column 2, and separator col 37 is floor across R=1, so column 2 is continuous from R=1 to R=8 apart from the comb, and row R=1 is continuous from C=2 to C=6. Spawn is (1,2); in fourteen frames the body has occupied exactly TWO cells, (1,2) and (2,2), and it has been at spawn in eight of them."
    [depends: key2_body_arrives, the_cascade_is_animation_and_one_press_is_one_lattice_cell  probe: pending]

  theorem the_hole_is_an_aperture_and_only_the_ring_needs_floor "A destination lattice cell needs its 24 RING pixels to render floor; the centre may render anything, because key2_body_arrives fires on a destination pixel only when the pixel six rows above renders 9, and at the destination centre that pixel is the source centre, which renders floor. Witnessed FIVE times: (16,16) stayed 5 while its 24 neighbours turned 9. This matters because it is the only reading under which the winning cell is enterable: lattice (8,7) is rows 50-54 cols 44-48 and its centre (52,46) renders colour 9, the socket pip. The map places something at a hole-centre exactly twice -- that pip and the knob's centre pixel at (10,40) -- which I read as the designer saying the body acts through its aperture, and record as a reading, not a law."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_socket_is_a_keyhole_and_names_the_winning_position "Rows 49-55 by cols 43-49 form a 7x7 colour-9 bracket, verified again against the current frame: top bar row 49 cols 43-49, bottom bar row 55 cols 43-49, right wall col 49 rows 50-54, and col 43 rows 50-54 is FLOOR, so it is open on the left. Inside it one lone colour-9 pixel at (52,46). Overlay the body standing in lattice (8,7) -- rows 50-54 cols 44-48, aperture at (52,46): flush on three sides, pip showing through the aperture. That is a plug and a socket drawn to the pixel, and it names the winning position without my guessing a goal predicate -- the game is won when the 24 ring pixels of rows 50-54 cols 44-48 render 9. The bracket has never changed in fourteen frames, so it is board and no object owns it; the first time the body enters, those 24 pixels become dynamic and the manual can finally speak about them."
    [depends: the_hole_is_an_aperture_and_only_the_ring_needs_floor  probe: pending]

  theorem the_socket_is_unreachable_until_the_comb_opens "Flood from spawn and the body reaches eleven lattice cells: (1,2),(1,3),(1,4),(1,5),(2,2),(2,4),(3,2),(3,3),(3,4),(4,2),(5,2). The socket (8,7) is not among them and nothing in R=7 or R=8 is, because every route south crosses (6,2) and 23 of that cell's 25 pixels render colour 8. The comb is not an obstacle to route around, it is the door. Its wiring is drawn in the open and I have re-read every pixel of it in the current frame: colour 8 fills row 40 from col 14 to col 40, climbs col 40 through rows 12 to 39, and ends in a 3x3 colour-8 knob at rows 9-11 cols 39-41 with a stem pixel at (12,40), all inside lattice (1,6). Not one colour-8 pixel has moved in fourteen frames, which is why 8 is board and not an object; the first colour-8 pixel that changes turns this theorem into physics and hands me a rule."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_knob_is_the_only_thing_within_reach_and_i_do_not_know_how_it_is_pressed "Ten of the eleven reachable cells are bounded by floor and void alone. The eleventh, (1,5) at rows 8-12 cols 32-36, is separated from the knob's cell (1,6) at cols 38-42 only by separator col 37, which is floor. Lattice (1,6) contains ten colour-8 pixels, nine of them ring pixels of that cell, so even under the aperture rule the body cannot stand there while 8 is solid. Either 8 is walkable and key2_body_arrives is wrong at the knob; or the knob answers to proximity from (1,5); or it answers to a key never pressed. My rules make the first self-announcing: if the body is driven into a colour-8 cell my manual predicts it stays put, and the world says otherwise in one command. Four lattice cells of eastward travel put the body at (1,5) and every one of those four steps is on floor that R=1 shows open. Thirteen commands have been spent and none of them has taken step one."
    [depends: the_socket_is_unreachable_until_the_comb_opens  probe: pending]

  theorem two_actions_have_never_been_pressed_and_one_of_them_may_be_a_click "actions_used is ACTION1..ACTION5 plus RESET; the alphabet is ACTION1..ACTION7. Two commands are entirely unconstrained after fourteen states, and in this family one is normally a click carrying coordinates. That matters here: the knob is a 3x3 target the body appears unable to stand on, and a click is the shape of interaction that presses it. I cannot write such a rule -- the guard language admits act=key(6) but has nowhere to put two coordinates, so a click rule would fire on every click anywhere and be silently wrong about which cell was clicked. If a click drives this world my manual can record its EFFECT, comb pixels going 8 to 5, and never its precondition. Note that the standard mapping I favour -- 1 up, 2 down, 3 left, 4 right, 5 undo-or-return -- accounts for every key pressed, which makes 6 and 7 more likely to be a click and a spare than more directions."
    [depends: the_action_map_after_thirteen_transitions_and_the_standard_mapping_hypothesis  probe: pending]

  theorem the_goal_section_is_absent_on_purpose "Still absent, and the reason has not weakened. Cart.pos = exit_cell needs one named instance and `arc-instances: all` gives me Glyph9_r8c14 and forty siblings. The socket interior has never changed, so it is board and count() has nothing to range over there, and the pip (52,46) will never become dynamic because the body's aperture leaves it rendering 9. The 24 ring cells of lattice (8,7) do become dynamic on first entry, but they are frame-0 colour 5 and would type as Vacated -- indistinguishable by this arm from the 24 Vacated cells at rows 14-18 -- so count(Vacated, color = 9) = 24 would be true of the body standing one cell south of spawn, which is not a win. A goal true in the wrong states is worse than no goal, because it stops a planner at its first step. Until the body has stood in lattice (8,7) once, the playbook steers by lattice distance, and is_goal -> False is the honest compilation."
    [depends: the_socket_is_a_keyhole_and_names_the_winning_position  probe: pending]

  theorem what_the_engines_gave_me "mdl_segmenter has crossed into POSITIVE gain for the first time, +614 bits at compression_ratio 0.937 on split_by_color=false, against -55676 bits when split by colour -- so its segmentation now just barely beats writing the pixels out, and I still owe it nothing structural. Its ten tracks remain the round's best independent corroboration and this round they corroborate the toggle by frame index: colour-1 nine-cell tracks obj1 (frames 0-4), obj6 (7-8), obj8 (11-12); colour-2 tracks obj5 (5-6), obj7 (9-10), obj9 (13). That is A,B,A,B,A,B derived by an engine that has never seen my rules. obj0 and obj2 persisting through all fourteen frames while the segmenter narrates ten moves is the marker-with-two-seats reading. obj4 is the whole 64-cell bar of which 6 cells are now dynamic. obj3 is a 1006-cell colour-null blob that swallowed the maze floor AND the body ring: connected_components(4) cannot see the mover at all, because the mover is a ring of floor-adjacent pixels that merges with the floor, and THAT ABSENCE IS THE FINDING. None of these gets a type of its own; a second type on the same pixels invites the double claim rule 5 forbids. zero_space self-reports THIN in its own words -- 13 transitions constrain rank 7 of 385 features, null space dimension 378, nearly every vector in it is a law true over these states and unfalsified rather than confirmed -- and its single global law is my census. cegis_miner refuses on every track and its verdict, the world does not narrate as one mover, remains true of the arm and false of the world: there is one mover, a rigid 24-pixel ring, and the arm can only see 24 simultaneous recolours, which is why movement costs a pair of rules per direction instead of one moved() event."
    [probe: passed]

  theorem what_i_predict_before_i_see_it "Written in advance so it can cost me. The next command has index 14, which is EVEN, and the body is at spawn with the panel in configuration B. ACTION4: if the standard mapping holds, the world changes 48 cells in rows 8-12 cols 14-24 and burns (63,57) for 49 total, and MY MANUAL DRAWS NONE OF THEM -- no east rules exist and (63,57) is board -- so I expect a 49-cell divergence, which is the advertised price of the first step onto fresh ground and not a failure of physics. If instead ZERO cells change, ACTION4 is not east, ACTION3 is east by elimination, AND BOTH METER READINGS DIE AT ONCE, because key 4 is even and index 14 is even and both demanded a burn. If exactly ONE cell changes and it is (63,57), ACTION4 is not east and both readings survive. ACTION5: I predict ZERO changed cells anywhere, on the strength of the spawn_probe guard and nothing else; a 23-cell panel toggle refutes the guard outright, a 48-cell move south says ACTION5 is UNDO, and a lone burn at (63,57) kills action-keying while leaving parity standing. ACTION2: 48 cells I draw correctly plus a burn at (63,57) I cannot draw -- exactly one wrong pixel, and nothing else learned, because key2_body_leaves and key2_body_arrives are at 120/120 and a sixth witness buys nothing. ACTION1 OR ACTION3 from spawn: zero cells under my manual, one cell at (63,57) under parity."
    [depends: the_action_map_after_thirteen_transitions_and_the_standard_mapping_hypothesis, the_parity_diagonal_survived_four_more_commands_and_is_still_free_to_break  probe: pending]

  theorem a_landmark_is_only_as_true_as_the_comment_beside_it "Kept in compressed form because the lesson is structural and cost a full round. Thirteen panel rules once carried colored(spawn_probe, 5) while the landmark line read a prose placeholder instead of a coordinate; the grammar puts such a landmark at (0,0), (0,0) is background in every frame this world has drawn, and so all thirteen rules were unreachable text that fired never and clashed never. Responsibility passed, ambiguity passed, step crashed zero times, and ONLY replay caught it. The landmark now reads (8, 14), the top-left pixel of the spawn ring, which renders 9 while the body is home and 5 the moment it is anywhere else. Before ranking any probe, check that the rules it is meant to test can actually fire."
    [depends: key5_slot1_dims  probe: passed]
```

## The playbook as it stands

```
# playbook.dsl -- what to buy with the next command, not a route.
#
# STATE OF PLAY (state 13): body home at lattice (1,2); panel in
# configuration B; SIX meter cells burned, cols 58-63 of row 63; thirteen
# commands spent; the next command has index 14, which is EVEN.
#
# THE ONE NUMBER THAT MATTERS: thirteen commands spent, TWO lattice cells
# ever occupied, and the last eight commands were the same two keys
# alternating between the same two cells. The previous edition of this file
# already carried the prune that forbids exactly that, and four more such
# commands were bought anyway. So the prune was not the problem; the RANKING
# was. This edition names the reason and fixes the ranking.
#
# WHY THE RANKING FAILED: every ACTION2 press burns a meter cell, every burn
# lands on a cell that is board at the instant it burns, and no rule the
# manual can express draws it. So EVERY ACTION2 PRESS FIRES A REFUTATION no
# matter how little it teaches, and a desk that ranks by refutation-fired
# will keep buying the move that fires one. Four refutations this round,
# two wrong pixels, zero rules implicated, one whole round consumed. The
# refutation channel is saturated and must be read by its divergence SET,
# not by whether it fired. First two prunes below encode that.
#
# WHAT THE FOUR COMMANDS DID BUY, honestly: a fifth and sixth witness for
# rules already at full coverage (worth nothing), a fifth toggle of the
# panel (worth nothing), two more burns on the diagonal where the two meter
# readings agree (worth nothing), and ONE real finding -- ACTION2 animates
# in 7 frames under panel configuration A and 9 under B, 5/5, which is the
# only evidence that the panel is not purely cosmetic.
#
# WHAT TO BUY NEXT, and the reasoning, not the sequence:
#  (a) THE EAST KEY IS THE ONLY QUESTION WHOSE ANSWER MOVES THE BODY. At
#      spawn, west is void and east is open floor, so one press of the
#      right-hand candidate either steps a lattice cell east or names the
#      other candidate by elimination -- ACTION1 was already excluded from
#      east at t1. Either outcome is decisive and one outcome also spends
#      the first of the four steps that reach the knob at lattice (1,6).
#      Advertised cost: 49 divergent cells, all of them cells the manual
#      said in advance it cannot own. Do not read that as a refutation.
#  (b) A ZERO-CELL ANSWER TO (a) KILLS BOTH METER READINGS AT ONCE, because
#      index 14 is even and the key candidate is even, so action-keying and
#      command-parity both demand a burn. That is the one branch where the
#      cheap probe pays double.
#  (c) THE METER SEPARATOR IS STILL FREE AND STILL UNTAKEN. Thirteen
#      commands, thirteen times a key whose parity equalled its index's
#      parity, zero separation. Any odd key at index 14, or any even key at
#      index 15, breaks it. Walking east on two consecutive commands breaks
#      it on the second step at no cost, which is why no dedicated meter
#      probe is worth a command while the map is open.
#  (d) THE CHEAPEST TRIPLE ON THE BOARD IS THE RETURN KEY PRESSED AT HOME.
#      The body is at spawn for the first time with a free command: the
#      manual predicts total silence there, which tests the spawn guard
#      (five positives, zero negatives, five rounds running); the key is
#      odd and the index even, which separates the meter; and a 48-cell
#      move south would say the key is UNDO rather than UP or RETURN.
#      Three open questions, one press, zero route progress. Rank it second
#      to (a), and first if (a) turns out to leave the body where it stands.
#  (e) ONE PRESS IS ONE LATTICE CELL, 5/5. Every distance below is counted
#      in lattice cells, not pixels.
# No stored sequence anywhere: every line is a criterion on the current
# frame plus the manual's own open questions.

order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired    [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance                 [proof: lean]
order     settle_the_east_key_before_routing_toward_the_knob                 [proof: lean]
order     prefer_the_probe_that_advances_over_the_probe_that_only_answers    [proof: lean]
order     probe_a_key_from_a_cell_where_exactly_one_candidate_is_open        [proof: lean]
order     take_a_separation_that_arrives_free_over_one_that_costs_a_command  [proof: lean]
order     read_the_cascade_length_it_is_evidence_that_costs_no_pixel         [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it         [proof: lean]
order     identify_a_direction_key_before_routing_with_it                    [proof: lean]
order     separate_two_readings_before_planning_against_either               [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it                 [proof: lean]
order     reach_the_switch_before_testing_the_switch                         [proof: lean]
order     try_an_unpressed_key_before_declaring_a_dead_end                   [proof: lean]
order     witness_a_rule_before_writing_it                                   [proof: lean]
order     spend_commands_on_information_while_the_bar_is_still_long          [proof: lean]

prune     divergence_lies_only_on_the_meter_leading_edge => dead              [proof: lean]
prune     ranked_only_because_a_refutation_fired_on_it => dead                [proof: lean]
prune     every_rule_it_would_witness_is_already_at_full_coverage => dead     [proof: lean]
prune     revisits_an_occupied_cell_by_an_already_witnessed_key => dead       [proof: lean]
prune     repeats_a_transition_whose_rule_already_has_full_coverage => dead   [proof: lean]
prune     dedicated_meter_probe_while_a_map_question_is_open => dead          [proof: lean]
prune     key_parity_equals_command_index_parity_when_bought_for_the_meter => dead [proof: lean]
prune     destination_ring_pixels_are_not_all_floor => dead                   [proof: lean]
prune     action_excluded_for_this_direction_by_an_earlier_no_op => dead      [proof: lean]
prune     route_that_crosses_the_comb_while_it_still_reads_eight => dead      [proof: lean]
prune     probe_where_both_live_readings_predict_the_same_pixel => dead       [proof: lean]
prune     probe_that_repeats_a_key_at_a_cell_that_cannot_separate_it => dead  [proof: lean]
prune     guard_whose_landmark_carries_no_arc_cell_comment => dead            [proof: lean]
prune     meter_exhausted and not goal => dead                                [proof: lean]

heuristic open_questions_a_command_can_close                                 [admissible: lean]
heuristic lattice_distance_to_the_knob_while_the_gate_is_shut                [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open               [admissible: lean]
heuristic lattice_cells_the_body_has_never_occupied                          [admissible: lean]
heuristic live_readings_a_command_can_eliminate                              [admissible: lean]
heuristic cells_this_command_makes_ownable_for_the_first_time                [admissible: lean]
heuristic unwitnessed_rules_this_command_would_witness                       [admissible: lean]
heuristic commands_remaining_under_the_worse_of_the_two_meter_readings       [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_meter_edge                    [admissible: lean]

prefer    a_direction_key_at_a_cell_where_its_two_candidates_disagree        [ev: 5/7 no_ops]
prefer    a_step_that_both_advances_and_witnesses_an_unwritten_rule          [ev: 5/5 moves]
prefer    a_cell_the_body_has_never_stood_in_over_one_it_has                 [ev: 2/11 cells]
prefer    east_along_lattice_row_one_over_any_other_axis                     [ev: 1/1 levels]
prefer    a_key_whose_parity_differs_from_the_command_index                  [ev: 0/13 commands]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                   [ev: 13/13 diffs]
prefer    a_press_at_home_that_splits_up_from_undo_from_return               [ev: 5/5 key5]
prefer    a_step_toward_the_knob_over_a_step_toward_the_socket               [ev: 1/1 levels]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered            [ev: 1/1 levels]
prefer    an_unpressed_key_over_repeating_a_known_no_op                      [ev: 2/7 keys]
```

## Why you are being called: the surprises that fired

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted '30332fff54b4924c', the world answered '4dfbfe14d4e85299'

```json
{
 "action": 2,
 "observed": "4dfbfe14d4e85299",
 "predictions": {
  "inert": "06e79195f0adc15f",
  "manual": "30332fff54b4924c",
  "without_key2_body_arrives": "06e79195f0adc15f",
  "without_key2_body_leaves": "06e79195f0adc15f",
  "without_key5_body_clears": "30332fff54b4924c",
  "without_key5_body_respawns": "30332fff54b4924c",
  "without_key5_slot1_dims": "30332fff54b4924c",
  "without_key5_slot1_lights": "30332fff54b4924c",
  "without_key5_slot2_centre_darkens": "30332fff54b4924c",
  "without_key5_slot2_centre_resets": "30332fff54b4924c",
  "without_key5_slot2_ring_resets": "30332fff54b4924c",
  "without_key5_slot2_row1_lights": "30332fff54b4924c",
  "without_key5_slot2_row2_left_lights": "30332fff54b4924c",
  "without_key5_slot2_row2_right_lights": "30332fff54b4924c",
  "without_key5_slot2_row3_lights": "30332fff54b4924c",
  "without_key5_underline1_dims": "30332fff54b4924c",
  "without_key5_underline1_lights": "30332fff54b4924c",
  "without_key5_underline2_dims": "30332fff54b4924c",
  "without_key5_underline2_lights": "30332fff54b4924c",
  "without_meter_burn_key2_next": "30332fff54b4924c",
  "without_meter_burn_key2_rightmost": "30332fff54b4924c",
  "without_meter_burn_key4_next": "30332fff54b4924c"
 },
 "probe_id": "P-09"
}
```

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted 'e66afa8078cb4fd2', the world answered 'd09fae77a1d46f2c'

```json
{
 "action": 5,
 "observed": "d09fae77a1d46f2c",
 "predictions": {
  "inert": "30332fff54b4924c",
  "manual": "e66afa8078cb4fd2",
  "without_key2_body_arrives": "e66afa8078cb4fd2",
  "without_key2_body_leaves": "e66afa8078cb4fd2",
  "without_key5_body_clears": "30332fff54b4924c",
  "without_key5_body_respawns": "30332fff54b4924c",
  "without_key5_slot1_dims": "e66afa8078cb4fd2",
  "without_key5_slot1_lights": "30332fff54b4924c",
  "without_key5_slot2_centre_darkens": "e66afa8078cb4fd2",
  "without_key5_slot2_centre_resets": "30332fff54b4924c",
  "without_key5_slot2_ring_resets": "30332fff54b4924c",
  "without_key5_slot2_row1_lights": "e66afa8078cb4fd2",
  "without_key5_slot2_row2_left_lights": "e66afa8078cb4fd2",
  "without_key5_slot2_row2_right_lights": "e66afa8078cb4fd2",
  "without_key5_slot2_row3_lights": "e66afa8078cb4fd2",
  "without_key5_underline1_dims": "e66afa8078cb4fd2",
  "without_key5_underline1_lights": "30332fff54b4924c",
  "without_key5_underline2_dims": "30332fff54b4924c",
  "without_key5_underline2_lights": "e66afa8078cb4fd2",
  "without_meter_burn_key2_next": "e66afa8078cb4fd2",
  "without_meter_burn_key2_rightmost": "e66afa8078cb4fd2",
  "without_meter_burn_key4_next": "e66afa8078cb4fd2"
 },
 "probe_id": "P-10"
}
```

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted '0c86941f09a0caaf', the world answered '44c44660a53cf5d4'

```json
{
 "action": 2,
 "observed": "44c44660a53cf5d4",
 "predictions": {
  "inert": "e66afa8078cb4fd2",
  "manual": "0c86941f09a0caaf",
  "without_key2_body_arrives": "e66afa8078cb4fd2",
  "without_key2_body_leaves": "e66afa8078cb4fd2",
  "without_key5_body_clears": "0c86941f09a0caaf",
  "without_key5_body_respawns": "0c86941f09a0caaf",
  "without_key5_slot1_dims": "0c86941f09a0caaf",
  "without_key5_slot1_lights": "0c86941f09a0caaf",
  "without_key5_slot2_centre_darkens": "0c86941f09a0caaf",
  "without_key5_slot2_centre_resets": "0c86941f09a0caaf",
  "without_key5_slot2_ring_resets": "0c86941f09a0caaf",
  "without_key5_slot2_row1_lights": "0c86941f09a0caaf",
  "without_key5_slot2_row2_left_lights": "0c86941f09a0caaf",
  "without_key5_slot2_row2_right_lights": "0c86941f09a0caaf",
  "without_key5_slot2_row3_lights": "0c86941f09a0caaf",
  "without_key5_underline1_dims": "0c86941f09a0caaf",
  "without_key5_underline1_lights": "0c86941f09a0caaf",
  "without_key5_underline2_dims": "0c86941f09a0caaf",
  "without_key5_underline2_lights": "0c86941f09a0caaf",
  "without_meter_burn_key2_next": "0c86941f09a0caaf",
  "without_meter_burn_key2_rightmost": "0c86941f09a0caaf",
  "without_meter_burn_key4_next": "0c86941f09a0caaf"
 },
 "probe_id": "P-11"
}
```

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted '06e79195f0adc15f', the world answered '3a11719074841328'

```json
{
 "action": 5,
 "observed": "3a11719074841328",
 "predictions": {
  "inert": "0c86941f09a0caaf",
  "manual": "06e79195f0adc15f",
  "without_key2_body_arrives": "06e79195f0adc15f",
  "without_key2_body_leaves": "06e79195f0adc15f",
  "without_key5_body_clears": "0c86941f09a0caaf",
  "without_key5_body_respawns": "0c86941f09a0caaf",
  "without_key5_slot1_dims": "0c86941f09a0caaf",
  "without_key5_slot1_lights": "06e79195f0adc15f",
  "without_key5_slot2_centre_darkens": "0c86941f09a0caaf",
  "without_key5_slot2_centre_resets": "06e79195f0adc15f",
  "without_key5_slot2_ring_resets": "06e79195f0adc15f",
  "without_key5_slot2_row1_lights": "0c86941f09a0caaf",
  "without_key5_slot2_row2_left_lights": "0c86941f09a0caaf",
  "without_key5_slot2_row2_right_lights": "0c86941f09a0caaf",
  "without_key5_slot2_row3_lights": "0c86941f09a0caaf",
  "without_key5_underline1_dims": "0c86941f09a0caaf",
  "without_key5_underline1_lights": "06e79195f0adc15f",
  "without_key5_underline2_dims": "06e79195f0adc15f",
  "without_key5_underline2_lights": "0c86941f09a0caaf",
  "without_meter_burn_key2_next": "06e79195f0adc15f",
  "without_meter_burn_key2_rightmost": "06e79195f0adc15f",
  "without_meter_burn_key4_next": "06e79195f0adc15f"
 },
 "probe_id": "P-12"
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
  "detail": "13/13 transitions replay exactly",
  "matched": 13,
  "ok": true,
  "transitions": 13
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
  "detail": "no (state, action) among 14 x 3 admitted two rules, and all 42 pairs were adjudicated -- no call to `step` raised",
  "n_clashes": 0,
  "ok": true,
  "pairs_checked": 42,
  "pairs_nominal": 42,
  "replay_truncated_by_crash": false,
  "sample_cap": 400,
  "scope": "sampled",
  "states": 14,
  "states_reconstructed": 14,
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
# theory.dsl -- world observed for 18 states / 17 transitions
# (RESET + A1 A2 A3 A4 A5 then A2 A5 six times over).
# 79 cells have ever changed; this manual names and owns all 79.
#
# WHAT THIS ROUND COST AND WHAT IT BOUGHT
#
#   Four commands were spent -- A2 A5 A2 A5 -- for the THIRD consecutive
#   round, and they moved the body between the same two lattice cells it has
#   been oscillating between since state 1. Four probe_refutations fired,
#   P-09..P-12. THEY ARE ONE DEFECT, COUNTED FOUR TIMES, AND THE DEFECT IS
#   ONE PIXEL PER BURN.
#
#   Chain the `inert` fields in order: P-10 inert = P-09 manual, P-11 inert =
#   P-10 manual, P-12 inert = P-11 manual. The harness rolls MY predicted
#   frame forward and never resyncs. At t14 the world burned meter cell
#   (63,57); at that instant (63,57) had never changed, was therefore board,
#   was owned by no object, and no rule expressible in this DSL could draw
#   it. That one wrong pixel then travelled through t15, t16 (where a second
#   undrawable burn at (63,56) joined it) and t17. FOUR REFUTATIONS, TWO
#   WRONG PIXELS, ZERO RULES IMPLICATED. Every other rule took two more
#   full-coverage witnesses and not one contradiction.
#
#   The previous manual advertised this outcome by name, by cell and by
#   price: it said the next burn would be at (63,57), said it was board,
#   said it would cost exactly one wrong pixel, and said no rewriting fixes
#   it. The price came in exactly, to the cell. The repair is arithmetic --
#   (63,57) and (63,56) are dynamic now, Glyph9 goes 41 -> 43, and both
#   transitions replay -- and the same bill will be presented at (63,55).
#
#   THREE ROUNDS OF EVIDENCE NOW SAY THE MANUAL IS NOT THE BOTTLENECK.
#   Twelve refutations across three rounds; every single divergence set has
#   been a subset of the meter's leading edge. Responsibility 0 unexplained,
#   ambiguity 0 clashes, replay exact. What is failing is command selection,
#   and the playbook -- not the manual -- is where I can act on that.
#   See the_manual_is_complete_on_what_it_has_been_allowed_to_see.

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
  Glyph9  [segment: dynamic_colour_9 ev: t0-t17 compress: 43]
  Vacated [segment: dynamic_colour_5 ev: t2,t5,t6,t7,t8,t9,t10,t11,t12,t13,t14,t15,t16,t17 compress: 24]
  Spent   [segment: dynamic_colour_1 ev: t5,t7,t9,t11,t13,t15,t17 compress: 9]
  Dark    [segment: dynamic_colour_0 ev: t5,t7,t9,t11,t13,t15,t17 compress: 3]

rules:
  rule key2_body_leaves forall ?p in Glyph9 [ev: t2,t6,t8,t10,t12,t14,t16 cov: 168/168]
    when act=key(2) and colored(?p, 9) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule key2_body_arrives forall ?v in Vacated [ev: t2,t6,t8,t10,t12,t14,t16 cov: 168/168]
    when act=key(2) and colored(?v, 5) and colored(above(above(above(above(above(above(?v)))))), 9) then recolored(?v, 9)

  rule meter_burn_key2_rightmost forall ?p in Glyph9 [ev: t2 cov: 1/1]
    when act=key(2) and colored(?p, 9) and rightof(?p) = wall then recolored(?p, 1)

  rule meter_burn_key2_next forall ?p in Glyph9 [ev: t6,t8,t10,t12,t14,t16 cov: 6/6]
    when act=key(2) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule meter_burn_key4_next forall ?p in Glyph9 [ev: t4 cov: 1/1]
    when act=key(4) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule key5_body_clears forall ?v in Vacated [ev: t5,t7,t9,t11,t13,t15,t17 cov: 168/168]
    when act=key(5) and colored(?v, 9) then recolored(?v, 5)

  rule key5_body_respawns forall ?p in Glyph9 [ev: t5,t7,t9,t11,t13,t15,t17 cov: 168/168]
    when act=key(5) and colored(?p, 5) and colored(above(?p), 5) then recolored(?p, 9)

  rule key5_slot1_dims forall ?p in Glyph9 [ev: t5,t9,t13,t17 cov: 32/32]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 9) and above(above(above(above(?p)))) = wall then recolored(?p, 2)

  rule key5_underline1_dims forall ?p in Glyph9 [ev: t5,t9,t13,t17 cov: 12/12]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 9) and colored(above(above(above(above(?p)))), 9) and above(above(above(above(above(above(?p)))))) = wall then recolored(?p, 0)

  rule key5_slot2_row1_lights forall ?s in Spent [ev: t5,t9,t13,t17 cov: 12/12]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(?s)) = wall then recolored(?s, 9)

  rule key5_slot2_row3_lights forall ?s in Spent [ev: t5,t9,t13,t17 cov: 12/12]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and colored(above(above(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_row2_left_lights forall ?s in Spent [ev: t5,t9,t13,t17 cov: 4/4]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(?s)))))) = wall then recolored(?s, 9)

  rule key5_slot2_row2_right_lights forall ?s in Spent [ev: t5,t9,t13,t17 cov: 4/4]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and colored(leftof(leftof(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_centre_darkens forall ?s in Spent [ev: t5,t9,t13,t17 cov: 4/4]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(leftof(?s))))))) = wall and colored(leftof(?s), 1) then recolored(?s, 0)

  rule key5_underline2_lights forall ?d in Dark [ev: t5,t9,t13,t17 cov: 12/12]
    when act=key(5) and colored(spawn_probe, 5) and colored(?d, 0) and colored(above(above(?d)), 1) and colored(above(above(above(above(?d)))), 1) then recolored(?d, 9)

  rule key5_slot1_lights forall ?p in Glyph9 [ev: t7,t11,t15 cov: 24/24]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 2) then recolored(?p, 9)

  rule key5_underline1_lights forall ?p in Glyph9 [ev: t7,t11,t15 cov: 9/9]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 0) and above(above(above(above(above(above(?p)))))) = wall then recolored(?p, 9)

  rule key5_slot2_ring_resets forall ?s in Spent [ev: t7,t11,t15 cov: 24/24]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 9) then recolored(?s, 1)

  rule key5_slot2_centre_resets forall ?s in Spent [ev: t7,t11,t15 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 0) then recolored(?s, 1)

  rule key5_underline2_dims forall ?d in Dark [ev: t7,t11,t15 cov: 9/9]
    when act=key(5) and colored(spawn_probe, 5) and colored(?d, 9) then recolored(?d, 0)

laws:
  invariant glyph9_instances count(Glyph9) = 43 [status: counted]
  invariant vacated_instances count(Vacated) = 24 [status: counted]
  invariant spent_instances count(Spent) = 9 [status: counted]
  invariant dark_instances count(Dark) = 3 [status: counted]
  invariant board_cells count(board) = 4017 [status: counted]
  invariant meter_cells_burned count(Glyph9, color = 1) = 8 [status: counted]

  theorem the_four_refutations_are_one_undrawable_pixel_rolled_forward "P-09 and P-11 are ACTION2, P-10 and P-12 ACTION5, and the diagnosis is arithmetic, not physics -- the second time in a row it has been exactly this. Chain the inert fields: P-10 inert is P-09 manual, P-11 inert is P-10 manual, P-12 inert is P-11 manual. The harness rolls MY predicted frame forward and never resyncs to the world, so a divergence introduced once is carried until the run ends. The divergence was introduced at t14, where the world burned meter cell (63,57). At that moment (63,57) had never changed, was therefore board, was owned by no object, and no rule expressible in this DSL could draw it -- exactly as the previous manual stated in advance, naming the cell. t16 added a second such pixel at (63,56). t15 and t17 introduced nothing of their own: their panel toggle is 23 cells and their body return is 48, and every one of those 71 cells was drawn correctly by rules that now carry seven witnesses each. The honest ledger for this round is TWO wrong pixels and FOUR refutation reports, and the ratio is a property of the instrument. Repair: (63,57) and (63,56) are dynamic now, Glyph9 rises 41 to 43, both transitions replay exactly, and the bill will be represented at (63,55)."
    [depends: meter_burn_key2_next, the_meter_edge_saturates_the_refutation_channel  probe: passed]

  theorem the_meter_edge_saturates_the_refutation_channel "Stated as a law of this manual rather than of this world, and after three rounds it is the single most expensive fact on the board. Each of the 64 cells of the row-63 bar burns EXACTLY ONCE, from colour 9 to colour 1, advancing leftward. At the instant a cell burns it has never changed, so it is board, so no instance exists for it, so no rule of mine draws it. Therefore: (1) my three meter_burn rules have ZERO predictive value on the leading edge and full value on replay, which is a division of labour and not a contradiction; (2) EVERY press of a key that burns will be scored a refutation regardless of what else it teaches, so refutation-fired is not a signal that discriminates between commands; (3) the correct reading of a refutation is its DIVERGENCE SET, not its hash, and where the divergence set is a subset of the bar's leading edge the manual is not implicated. All twelve refutations across three rounds have been exactly that. Deleting the burn rules does not help -- the wrong-pixel count at the moment of the burn is identical -- and keeping them is strictly better because they make every past transition replay. I cannot repair this: `arc-instances: all` instances only cells the board cannot explain, and a cell that has never changed is exactly what the board explains. RIGHT NOW all eight meter instances render colour 1, so meter_burn_key2_next matches nothing and my manual predicts NO burn at (63,55) under any key -- which is not a claim about the world, it is the shape of the hole."
    [depends: meter_burn_key2_next, the_manual_heals_one_step_behind_and_the_meter_is_where_it_shows  probe: passed]

  theorem the_manual_is_complete_on_what_it_has_been_allowed_to_see "The finding of this round, and it is about the process rather than the physics. Certify on the previous edition: 13/13 transitions replay exactly, 0 cells unexplained of 4096, 0 clashes over 42 adjudicated pairs, 0 step crashes. Twelve probe_refutations have now fired across three rounds and EVERY ONE of their divergence sets is a subset of the meter's leading edge -- cells that were board at the instant they changed. Not one rule has ever been contradicted. Twenty rules stand at full coverage on seven witnesses each. Meanwhile the body has occupied TWO of the eleven lattice cells reachable from spawn, in eighteen states, and the last twelve commands were two keys alternating. The conclusion I draw and will act on in the playbook, not the manual: additional evidence of the kind these commands produce has zero marginal value, the manual cannot be improved by watching the same transition an eighth time, and the only remaining sources of information are (a) a key never pressed from the cell the body is standing on, (b) a lattice cell never occupied, (c) a key never pressed at all. Everything else is already at coverage."
    [depends: the_meter_edge_saturates_the_refutation_channel, dynamic_census  probe: passed]

  theorem the_parity_diagonal_survived_four_more_commands_and_is_still_free_to_break "Row 63 is a 64-cell colour-9 bar burning to colour 1 from the right. EIGHT burns now: (63,63) t2, (63,62) t4, (63,61) t6, (63,60) t8, (63,59) t10, (63,58) t12, (63,57) t14, (63,56) t16. Nine silences: t1, t3, t5, t7, t9, t11, t13, t15, t17. The current frame confirms it -- row 63 reads 9 through col 55 and 1 from col 56 to col 63. READING A, ACTION-KEYING: burns iff the key is 2 or 4. READING B, COMMAND PARITY: burns iff the command index is even. BOTH SCORE 17/17 AND NEITHER HAS GAINED A SINGLE BIT IN TWO ROUNDS, because every command bought since state 5 has been key 2 at an even index or key 5 at an odd index -- the diagonal on which the two readings are numerically identical. Seventeen commands, seventeen alignments, zero separation. THE SEPARATOR REMAINS FREE AND IS NOW CHEAPER THAN EVER: the next index is 18, EVEN, so ANY odd key there (1, 3 or 5) settles it in one command, and an even key there does not. Note the consequence for ordering: an odd-key probe bought at an even index separates, and the even-key probe it displaces separates too when bought at the following odd index -- so taking the odd key first collects the separation twice, and taking the even key first collects it never. I encode reading A because it is the only one the guard language can say -- there is no command counter and no phase pixel -- and I still expect B, because at t3 and t4 the body stood at lattice (2,2) with left and right both void, ACTION3 and ACTION4 were blocked identically, and only ACTION4 burned. Under A that is a cost attached to a key and not to an attempt; under B it is one bit of clock."
    [depends: meter_burn_key2_next, meter_burn_key4_next  probe: pending]

  theorem the_meter_is_a_budget_i_can_now_price "Eight of sixty-four bar cells are consumed after seventeen commands. I do not know that exhaustion ends the game -- no frame has shown it -- but I can price both readings and the price is reassuring, which is worth saying because it argues against panic as well as against waste. Under reading A the bar only burns on keys 2 and 4, so a route made of eastward and southward steps burns once per step and 56 steps remain. Under reading B every second command burns and 112 commands remain. The route I can see costs about this: spawn (1,2) east to (1,5) is THREE steps, an unknown number of interactions at the knob, three steps back west, then seven steps south down lattice column 2 to (8,2) and five steps east to the socket at (8,7) -- roughly nineteen steps plus interactions plus the probes that identify the keys. That fits inside 56 with room to spare. So the meter is not yet the binding constraint; the binding constraint is that twelve of seventeen commands bought nothing. I record the arithmetic so that a future desk neither ignores the bar nor treats it as an emergency."
    [depends: the_parity_diagonal_survived_four_more_commands_and_is_still_free_to_break, the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_cascade_length_is_a_free_channel_that_i_discard_by_construction "cascade_lengths are 1, 7 and 9. Now 7/7 and no longer a curiosity. ACTION2 returned SEVEN frames at t2, t8, t12, t16 and NINE frames at t6, t10, t14. The panel configuration in the state each press acted FROM: t2 from state 1 (A), t8 from state 7 (A), t12 from state 11 (A), t16 from state 15 (A) -- seven frames; t6 from state 5 (B), t10 from state 9 (B), t14 from state 13 (B) -- nine frames. Seven for seven, no exceptions: ACTION2 animates in 7 internal frames when the panel is in configuration A and 9 when it is in B. ACTION5 returned nine frames all seven times regardless of configuration, and every no-op returned one. THE NET EFFECT IS IDENTICAL IN ALL SEVEN ACTION2 PRESSES -- 48 body cells, rows 8-18, cols 14-18, plus one burn -- so this costs me nothing in replay and buys me nothing in prediction, and yet it remains the only evidence I have that the panel does anything besides display. Six rows of travel at one row per frame is 7 frames with a terminal frame; the two extra frames under configuration B are two internal steps whose content I never see, because `cascade single_frame` compares only the net. I record, as a limitation of my own semantics and not of the world: up to eight intermediate frames per command are discarded unread, and something distinguishable happens inside them."
    [depends: key2_body_arrives, the_panel_is_a_marker_that_alternates_between_two_slots  probe: passed]

  theorem the_panel_is_a_marker_that_alternates_between_two_slots "PROVEN over SEVEN toggles -- t5, t7, t9, t11, t13, t15, t17 -- 23 cells every time, and ACTION2 has never touched a panel pixel in seven presses. CONFIGURATION A (states 0-4, 7-8, 11-12, 15-16): slot 1 at rows 1-3 cols 1-3 is a hollow colour-9 ring, its underline at row 5 cols 1-3 lit 9; slot 2 at rows 1-3 cols 5-7 is a SOLID colour-1 block, its underline at row 5 cols 5-7 dark 0. CONFIGURATION B (states 5-6, 9-10, 13-14, 17, and the current frame, which reads 222/2.2/222 at cols 1-3 and 999/9.9/999 at cols 5-7 with row 5 dark at 1-3 and lit at 5-7): slot 1 is a hollow colour-2 ring with underline dark; slot 2 is a hollow colour-9 ring with dark centre and underline lit. mdl_segmenter corroborates this independently and by frame index: its colour-1 nine-cell tracks are obj1 (frames 0-4), obj6 (7-8), obj8 (11-12), obj10 (15-16) and its colour-2 tracks obj5 (5-6), obj7 (9-10), obj9 (13-14), obj11 (17) -- A,B,A,B,A,B,A,B read off an engine that has never seen my rules. Its obj0 (colour 9, eight cells, 3x3, present in all 18 frames) and obj2 (colour 9, 1x3, all 18) persist while it narrates fourteen MOVE events: the hollow ring and the lit underline do not appear and vanish, they TRAVEL between slot 1 and slot 2. So the panel is one marker with two seats and colour 9 marks the occupied seat. What the seats HOLD is still unknown and I will not guess. I cannot model it as a moving marker either: the arm gives one instance per cell and moved(o, dir) moves one cell, so an eight-pixel ring travelling four columns is not expressible as a move, and ten recolour rules are the shortest thing this DSL can say."
    [depends: key5_slot1_dims, key5_slot1_lights  probe: passed]

  theorem why_i_keep_the_spawn_probe_guard_on_a_window_that_still_cannot_test_it "Unchanged in kind, stronger in count, and now by a wide margin the cheapest open question on the board. The guard `colored(spawn_probe, 5)` has SEVEN positive witnesses (t5, t7, t9, t11, t13, t15, t17 -- body away, panel toggled) and STILL NO NEGATIVE ONE, because ACTION5 has never once been pressed with the body at home. Every ACTION5 in this window immediately followed an ACTION2, so ACTION5 was pressed and the body was away from spawn are the same event seven times over and no guard can be credited over the other. By the letter of no-entry-without-gain the atom is still unearned. I keep it because dropping it changes no replay and because the body is at spawn RIGHT NOW for the third round running: with the guard my manual predicts SILENCE for an ACTION5 pressed here, without it a 23-cell toggle. Silence is the prediction I want on the record, because it is the only prediction this manual can make that costs exactly zero pixels if right. Note what one such press would settle at once: the guard, the meter parity (key 5 is odd, index 18 is even, so reading A predicts no burn and reading B predicts a burn at (63,55)), and the identity of ACTION5 (UNDO would return the body to (2,2) for 48 cells, while UP and RETURN both predict no motion from spawn). Three open questions, one command, and my manual's stake is a bare prediction of zero changed cells."
    [depends: the_panel_is_a_marker_that_alternates_between_two_slots, what_action5_is_and_the_two_cell_experiment_that_names_it  probe: pending]

  theorem the_action_map_after_seventeen_transitions_and_the_standard_mapping_hypothesis "WITNESSED: ACTION2 IS DOWN, 7/7, six rows south, one lattice cell, at t2, t6, t8, t10, t12, t14, t16. ACTION5 returns the body from lattice (2,2) to (1,2), 7/7. NEGATIVE INFORMATION, and I state it as negative because that is all it is. At spawn (1,2) up and left are void while down and right are open floor, and ACTION1 did nothing at t1 -- so ACTION1 IS NEITHER DOWN NOR RIGHT. At (2,2) the body had just vacated rows 8-12 so UP WAS OPEN, and rows 20-24 cols 14-18 are floor so DOWN WAS OPEN, while left (cols 8-12) and right (cols 20-24) are void; ACTION3 and ACTION4 each did nothing there -- so NEITHER IS UP AND NEITHER IS DOWN. One assignment survives that invents nothing: ACTION1 up, ACTION2 down, ACTION3 left, ACTION4 right, ACTION5 something else. It explains every no-op as a blocked move and it is the conventional mapping for this action family, which is a prior and not evidence. TWELVE COMMANDS HAVE NOW BEEN SPENT ACROSS THREE ROUNDS AND NOT ONE OF THEM TOUCHED THIS QUESTION -- the map is exactly as constrained as it was at state 5. THE CHEAP TEST IS STILL ONE PRESS: the body stands at spawn, where west is void and east is open floor for three lattice cells, so either eastward candidate pressed here settles it -- if it steps, it is east; if it does not, the other is east by elimination, since ACTION1 was excluded from east at t1."
    [depends: key2_body_arrives, key5_body_respawns, the_cascade_is_animation_and_one_press_is_one_lattice_cell  probe: pending]

  theorem what_action5_is_and_the_two_cell_experiment_that_names_it "Three readings survive all SEVEN ACTION5 presses because all seven were made from exactly one cell south of spawn, where they are indistinguishable: UP (move one cell north), UNDO (revert the last move), RETURN (jump to spawn from anywhere). They separate the moment the body is somewhere else, and they separate differently by axis. FROM SPAWN ITSELF, which is where the body is now: UP predicts no motion (north of spawn is void), RETURN predicts no motion (already home), UNDO predicts 48 cells back to (2,2) -- so one press here splits UNDO from the other two for free. Two cells EAST at lattice (1,4): UP no move, UNDO one cell west to (1,3), RETURN spawn at (1,2) -- three different diffs, all legible in the raw pixel count, which is the full separation. Two cells SOUTH at (3,2): UP and UNDO both predict (2,2) and only RETURN separates. So the eastward route answers this question completely and the southward route does not, which is one more reason to go east. Note the coupling I cannot yet break: the panel toggles on every effective ACTION5, seven for seven, so whatever ACTION5 is, the panel is its counter or its selector -- and the 7-versus-9 cascade result says the panel's state is not merely cosmetic."
    [depends: the_panel_is_a_marker_that_alternates_between_two_slots, the_cascade_length_is_a_free_channel_that_i_discard_by_construction  probe: pending]

  theorem the_cascade_is_animation_and_one_press_is_one_lattice_cell "A move is animated one row per internal frame and the world reports the whole animation for a single action; `cascade single_frame` compares only the net effect, which is identical for all seven ACTION2 presses (48 body cells, rows 8-18, cols 14-18) regardless of whether the command took 7 frames or 9. The refutation I keep: under a slide-until-blocked reading, ACTION2 at spawn would have run the body south through rows 20-24 and 26-30 to the comb; it stopped after exactly six rows over open floor, SEVEN times. ONE PRESS IS ONE LATTICE CELL, 7/7, and every distance in the playbook rests on that."
    [depends: key2_body_arrives, the_maze_is_a_six_pixel_lattice  probe: passed]

  theorem the_world_may_still_not_be_a_function_of_the_drawn_frame "Carried as a belief and NOT proven in this window. To prove it I need two pixel-identical states from which the SAME action produced different successors; I have no such pair, and distinct_states is 16 against 18 states, so two coincidences exist but neither is followed by the same key. What keeps the belief alive is the parity reading of the meter, which if true IS one bit of hidden state that flips every command and that no guard in this language can read, because no guard can read anything that is not a pixel. What strengthens it is the cascade length: ACTION2 took 7 frames or 9 depending on a panel configuration that the net frame records but that my rules never consult, which is the same shape of dependence one step less hidden. Operationally it matters in exactly one way: if parity wins, every burn rule I can write is an approximation with a known error rate, and I would rather say that once than rediscover it."
    [depends: the_parity_diagonal_survived_four_more_commands_and_is_still_free_to_break, the_cascade_length_is_a_free_channel_that_i_discard_by_construction  probe: pending]

  theorem the_manual_heals_one_step_behind_and_the_meter_is_where_it_shows "The arm instances exactly the cells that have ALREADY changed, typed by their frame-0 colour: constant 4017 + dynamic 79 = 4096, and 43+24+9 = 76 = cells_needing_an_owner with the 3 colour-0 cells making up the difference to 79. Consequence: a cell that has never changed is board, no object owns it, and NO RULE CAN DRAW ITS FIRST CHANGE. This is the third consecutive round in which that sentence, written in advance, was the entire content of every refutation. meter_burn_key2_next now replays t6, t8, t10, t12, t14 and t16 perfectly, because by replay time all six burned cells are dynamic; it will still miss the NINTH burn at (63,55), because that cell is board today. The same arithmetic prices the first eastward step: rows 8-12 cols 20-24 have never changed, so 24 arrival pixels are undrawable no matter what rule I write, and the 24 departure pixels are undrawable too until an east-leaves rule is witnessed. 48 wrong cells for the first step onto fresh ground, 24 if I already had the leaves rule, 0 for the second step. The body also CHANGES TYPE as it walks -- Glyph9 at rows 8-12, Vacated at rows 14-18 -- because typing is by frame-0 colour and all that floor was 5."
    [depends: key2_body_arrives, dynamic_census  probe: passed]

  theorem dynamic_census "Exactly 79 cells have ever changed and every one has an owner. 23 are the panel: slot 1's eight ring pixels, its centre (2,2) being colour 0 in BOTH configurations and therefore board; underline 1's three; slot 2's nine, centre included because (2,6) is 1 in A and 0 in B; underline 2's three. 24 are the spawn ring, rows 8-12 cols 14-18 minus the aperture (10,16), which never changes and is board. 24 are the same ring six rows south, rows 14-18 cols 14-18 minus its aperture (16,16). 8 are the burned right end of row 63: cols 56 through 63. 23+24+24+8 = 79 = dynamic_cells. By frame-0 colour: 43 colour-9 (8 slot-1 ring + 3 underline-1 + 24 spawn ring + 8 meter), 9 colour-1 (slot 2 solid), 24 colour-5 (the lower ring, floor at frame 0), 3 colour-0 (underline 2). 43+9+24 = 76 = cells_needing_an_owner exactly. zero_space's global-law cell list is the same 79 cells -- it lists (2,1) and (2,3) but not (2,2), (10,14),(10,15),(10,17),(10,18) but not (10,16), and all eight burned bar cells -- and its single global law restates this census and nothing more."
    [probe: passed]

  theorem the_rules_i_still_have_no_witness_for_and_will_not_write "Three holes, each with its text ready so that the transition that witnesses it costs one paste and not one round of rediscovery. (1) A SECOND DESCENT. The body has descended seven times and all seven started at spawn, so no rule of mine turns Vacated pixels from 9 back to 5 on an ACTION2: rule key2_floor_leaves forall ?v in Vacated when act=key(2) and colored(?v, 9) and colored(below-six(?v), 5) then recolored(?v, 5). One ACTION2 from lattice (2,2) buys it, and eight commands across two rounds each had the chance and none took it. (2) EAST-WEST MOTION. Whatever the east key turns out to be, it needs a pair: a leaves rule over Glyph9 guarded on colour 9 with rightof-six rendering 5, and its arrives twin typed on whichever object owns the destination pixels -- which today is NO object, because rows 8-12 cols 20-24 are board. (3) A NINTH BURN AT A CELL THAT IS STILL BOARD, which is not a missing rule but a missing instance and cannot be written at all. I state the price of all three in advance so it cannot be mistaken for a surprise: the first eastward step costs 48 wrong cells plus one if the bar burns, the first second-descent costs 24, and every fresh burn costs 1."
    [depends: key2_body_arrives, the_meter_edge_saturates_the_refutation_channel  probe: pending]

  theorem off_board_cell_terms_evaluate_false_and_that_is_load_bearing "certify reports 0 step crashes across all adjudicated pairs while key2_body_leaves grounds on meter instances at row 63 whose sixth below is row 69. So colored(off-board, k) is false rather than an exception, and `<cell> = wall` is the sanctioned positive test. Thirteen of the twenty rules rest on this and every row and column discrimination in the panel is built from it: the k-th above is off-board exactly when k exceeds the row, so row 1 is above-twice equals wall, row 3 is a colour test on above-twice -- false for row 1 precisely because a colour test on an off-board cell is false -- and row 2 is above-three equals wall conjoined with a colour test on above-once. The same trick separates slot 2's middle row by column: col 5 is leftof-six equals wall, col 6 is leftof-seven equals wall with a colour test on leftof-once, col 7 is a colour test on leftof-twice, pairwise exclusive, which is why the ambiguity check reports 0 clashes over 42 adjudicated pairs. Not one rule uses `not`, deliberately. The eight A-to-B slot-2 and underline rules could collapse to two if I could write that not all four neighbours are colour 1, and I decline to gamble a whole round's compile on discovering whether `not` before an equality atom parses. If a future desk wants the shorter form, try it on ONE rule, not on eight."
    [depends: key2_body_leaves, key5_slot2_centre_darkens  probe: passed]

  theorem the_maze_is_a_six_pixel_lattice "Lattice cell (R,C) is rows 6R+2..6R+6 by cols 6C+2..6C+6; rows and columns congruent to 1 mod 6 are separator strips. Colour 5 is floor, 0 is void, 8 is machinery, and the body is a rigid 5x5 colour-9 block with a one-pixel aperture at its centre. Re-read pixel by pixel from the CURRENT frame and unchanged: R=1 (rows 8-12) is floor from col 13 to col 43, so C=2,3,4,5 are open, C=6 holds the knob, C=7 does not exist (col 44 is void in this band); R=2 is floor at cols 13-19 and 25-31, so C=2 and C=4 only; R=3 is floor cols 13-31, so C=2,3,4; R=4 and R=5 are floor only at cols 13-19, so C=2; R=6 is the comb, whose only floor pixels are (39,14) and (41,14), so nothing there is enterable; R=7 is C=2, plus a fragment of floor at cols 42-50 in row 48 alone which cannot hold a body; R=8 (rows 50-54) is floor from col 13 to col 48, so C=2..7 are all open. Separator rows 7,13,19,25,31,37,43,49 are floor across column 2, and separator col 37 is floor across R=1, so column 2 is continuous from R=1 to R=8 apart from the comb, and row R=1 is continuous from C=2 to C=6. Spawn is (1,2); in eighteen frames the body has occupied exactly TWO cells, (1,2) and (2,2), and it has been at spawn in ten of them."
    [depends: key2_body_arrives, the_cascade_is_animation_and_one_press_is_one_lattice_cell  probe: pending]

  theorem the_hole_is_an_aperture_and_only_the_ring_needs_floor "A destination lattice cell needs its 24 RING pixels to render floor; the centre may render anything, because key2_body_arrives fires on a destination pixel only when the pixel six rows above renders 9, and at the destination centre that pixel is the source centre, which renders floor. Witnessed SEVEN times: (16,16) stayed 5 while its 24 neighbours turned 9. This matters because it is the only reading under which the winning cell is enterable: lattice (8,7) is rows 50-54 cols 44-48 and its centre (52,46) renders colour 9, the socket pip. The map places something at a hole-centre exactly twice -- that pip and the knob's centre pixel at (10,40) -- which I read as the designer saying the body acts through its aperture, and record as a reading, not a law."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_socket_is_a_keyhole_and_names_the_winning_position "Rows 49-55 by cols 43-49 form a 7x7 colour-9 bracket, verified again cell by cell against the current frame: top bar row 49 cols 43-49, bottom bar row 55 cols 43-49, right wall col 49 rows 50-54, and col 43 rows 50-54 is FLOOR, so it is open on the left. Inside it one lone colour-9 pixel at (52,46). Overlay the body standing in lattice (8,7) -- rows 50-54 cols 44-48, aperture at (52,46): flush on three sides, pip showing through the aperture. That is a plug and a socket drawn to the pixel, and it names the winning position without my guessing a goal predicate -- the game is won when the 24 ring pixels of rows 50-54 cols 44-48 render 9. The bracket has never changed in eighteen frames, so it is board and no object owns it; the first time the body enters, those 24 pixels become dynamic and the manual can finally speak about them."
    [depends: the_hole_is_an_aperture_and_only_the_ring_needs_floor  probe: pending]

  theorem the_socket_is_unreachable_until_the_comb_opens "Flood from spawn and the body reaches eleven lattice cells: (1,2),(1,3),(1,4),(1,5),(2,2),(2,4),(3,2),(3,3),(3,4),(4,2),(5,2). The socket (8,7) is not among them and nothing in R=7 or R=8 is, because every route south crosses (6,2) and 23 of that cell's 25 pixels render colour 8. Nor is there a second route: C=3 exists only at R=3, C=4 dead-ends at R=3, and C=5 and C=6 exist only at R=1, so lattice column 2 is the sole north-south corridor. The comb is not an obstacle to route around, it is the door. Its wiring is drawn in the open and I have re-read every pixel of it in the current frame: colour 8 fills row 40 from col 14 to col 40, climbs col 40 through rows 12 to 39, and ends in a 3x3 colour-8 knob at rows 9-11 cols 39-41 with a stem pixel at (12,40), all inside lattice (1,6). Not one colour-8 pixel has moved in eighteen frames, which is why 8 is board and not an object; the first colour-8 pixel that changes turns this theorem into physics and hands me a rule."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_knob_is_the_only_thing_within_reach_and_i_do_not_know_how_it_is_pressed "Ten of the eleven reachable cells are bounded by floor and void alone. The eleventh, (1,5) at rows 8-12 cols 32-36, is separated from the knob's cell (1,6) at cols 38-42 only by separator col 37, which is floor. Lattice (1,6) contains ten colour-8 pixels, nine of them ring pixels of that cell, so even under the aperture rule the body cannot stand there while 8 is solid. Either 8 is walkable and key2_body_arrives is wrong at the knob; or the knob answers to proximity from (1,5); or it answers to a key never pressed. My rules make the first self-announcing: if the body is driven into a colour-8 cell my manual predicts it stays put, and the world says otherwise in one command. CORRECTION TO THE PREVIOUS EDITION, which said four steps: C=2 to C=5 is THREE lattice cells of eastward travel and C=2 to C=6 is four, and every one of those steps is on floor that R=1 shows open. The playbook's distance heuristic uses the corrected number. Seventeen commands have been spent and none has taken step one."
    [depends: the_socket_is_unreachable_until_the_comb_opens  probe: pending]

  theorem two_actions_have_never_been_pressed_and_one_of_them_may_be_a_click "actions_used is ACTION1..ACTION5 plus RESET; the alphabet is ACTION1..ACTION7. Two commands are entirely unconstrained after eighteen states, and in this family one is normally a click carrying coordinates. That matters here: the knob is a 3x3 target the body appears unable to stand on, and a click is the shape of interaction that presses it. I cannot write such a rule -- the guard language admits act=key(6) but has nowhere to put two coordinates, so a click rule would fire on every click anywhere and be silently wrong about which cell was clicked. If a click drives this world my manual can record its EFFECT, comb pixels going 8 to 5, and never its precondition. Note that the standard mapping I favour -- 1 up, 2 down, 3 left, 4 right, 5 undo-or-return -- accounts for every key pressed, which makes 6 and 7 more likely to be a click and a spare than more directions. One press of either is a wholly unconstrained command whose every outcome is new information, which is a strong claim to make about a board where twenty rules sit at full coverage."
    [depends: the_action_map_after_seventeen_transitions_and_the_standard_mapping_hypothesis  probe: pending]

  theorem the_goal_section_is_absent_on_purpose_and_the_playbook_must_carry_the_ranking "Still absent, and the reason has not weakened. Cart.pos = exit_cell needs one named instance and `arc-instances: all` gives me Glyph9_r8c14 and forty-two siblings. The socket interior has never changed, so it is board and count() has nothing to range over there, and the pip (52,46) will never become dynamic because the body's aperture leaves it rendering 9. The 24 ring cells of lattice (8,7) do become dynamic on first entry, but they are frame-0 colour 5 and would type as Vacated -- indistinguishable by this arm from the 24 Vacated cells at rows 14-18 -- so count(Vacated, color = 9) = 24 would be true of the body standing one cell south of spawn, which is not a win. A goal true in the wrong states is worse than no goal, because it stops a planner at its first step. I now name the price of that choice, because three rounds of oscillation are consistent with it: with no goal section the manual compiles is_goal -> False, no plan can ever terminate at a goal, and therefore NOTHING in the manual ranks one command above another. The entire ranking lives in playbook.dsl. That is why this round's playbook is short and front-loaded rather than long and complete: a criterion buried at line thirty is a criterion that has not been read."
    [depends: the_socket_is_a_keyhole_and_names_the_winning_position, the_manual_is_complete_on_what_it_has_been_allowed_to_see  probe: pending]

  theorem what_the_engines_gave_me "mdl_segmenter has widened its positive gain to +3442 bits at compression_ratio 0.747 on split_by_color=false, against -74754 bits when split by colour -- so its segmentation now clearly beats writing the pixels out, and I still owe it nothing structural. Its twelve tracks remain the round's best independent corroboration and this round they corroborate the toggle by frame index: colour-1 nine-cell tracks obj1 (frames 0-4), obj6 (7-8), obj8 (11-12), obj10 (15-16); colour-2 tracks obj5 (5-6), obj7 (9-10), obj9 (13-14), obj11 (17). That is A,B,A,B,A,B,A,B derived by an engine that has never seen my rules. obj0 and obj2 persisting through all eighteen frames while the segmenter narrates fourteen moves is the marker-with-two-seats reading. obj4 is the whole 64-cell bar of which 8 cells are now dynamic. obj3 is a 1006-cell colour-null blob that swallowed the maze floor AND the body ring: connected_components(4) cannot see the mover at all, because the mover is a ring of floor-adjacent pixels that merges with the floor, and THAT ABSENCE IS THE FINDING. None of these gets a type of its own; a second type on the same pixels invites the double claim rule 5 forbids. zero_space self-reports THIN in its own words -- 17 transitions constrain rank 9 of 395 features, null space dimension 386, nearly every vector in it is a law true over these states and unfalsified rather than confirmed -- and its single global law is my census. cegis_miner refuses on every track and its verdict, the world does not narrate as one mover, remains true of the arm and false of the world: there is one mover, a rigid 24-pixel ring, and the arm can only see 24 simultaneous recolours, which is why movement costs a pair of rules per direction instead of one moved() event."
    [probe: passed]

  theorem what_i_predict_before_i_see_it "Written in advance so it can cost me. The next command has index 18, which is EVEN, and the body is at spawn with the panel in configuration B. ACTION5: I predict ZERO changed cells anywhere, on the strength of the spawn_probe guard and nothing else, and this is the only zero-pixel stake this manual can offer. Zero cells confirms the guard AND kills the parity reading of the meter outright, because parity demanded a burn at (63,55) and action-keying forbade one. Exactly one changed cell at (63,55) confirms the guard and kills action-keying instead. Twenty-three cells refutes the spawn_probe guard and puts thirteen rules into repair. Forty-eight cells says ACTION5 is UNDO. Four outcomes, all legible in the raw pixel count, and every one of them closes something. THE EASTWARD CANDIDATE at index 18: if it is east, the world changes 48 cells in rows 8-12 cols 14-24 and MY MANUAL DRAWS NONE OF THEM -- no east rules exist and rows 8-12 cols 20-24 are board -- plus a burn at (63,55) for 49 total, which is the advertised price of the first step onto fresh ground and not a failure of physics. If instead ZERO cells change, that key is not east, the other is east by elimination, AND BOTH METER READINGS DIE AT ONCE, because an even key at an even index is the one case where both demand a burn. ACTION2: 48 cells I draw correctly plus a burn at (63,55) I cannot draw -- exactly one wrong pixel, and nothing else learned, because key2_body_leaves and key2_body_arrives are at 168/168 and an eighth witness buys nothing. ACTION1 from spawn: zero cells under my manual, one cell at (63,55) under parity."
    [depends: the_action_map_after_seventeen_transitions_and_the_standard_mapping_hypothesis, the_parity_diagonal_survived_four_more_commands_and_is_still_free_to_break  probe: pending]

  theorem a_landmark_is_only_as_true_as_the_comment_beside_it "Kept in compressed form because the lesson is structural and cost a full round. Thirteen panel rules once carried colored(spawn_probe, 5) while the landmark line read a prose placeholder instead of a coordinate; the grammar puts such a landmark at (0,0), (0,0) is background in every frame this world has drawn, and so all thirteen rules were unreachable text that fired never and clashed never. Responsibility passed, ambiguity passed, step crashed zero times, and ONLY replay caught it. The landmark now reads (8, 14), the top-left pixel of the spawn ring, which renders 9 while the body is home and 5 the moment it is anywhere else. Before ranking any probe, check that the rules it is meant to test can actually fire."
    [depends: key5_slot1_dims  probe: passed]

  theorem i_cannot_manufacture_an_instance_on_a_cell_that_has_never_changed "Recorded because a future desk will be tempted by the same repair I considered and rejected this round. To draw the leading-edge burn I would need an instance on a board cell. The arm offers exactly one lever, `arc-instances: all`, and its documented behaviour is to instance every cell OF THAT COLOUR THE BOARD CANNOT EXPLAIN -- a never-varying cell is precisely what the board explains, so it gets no instance. The tempting workaround is a second declared type on colour 9 without arc-instances, hoping the arm seats one instance somewhere useful. I reject it: the arm looks objects up by colour and nothing else, so a second colour-9 type is indistinguishable from Glyph9, the seat is unspecified, and any cell it landed on would be claimed twice, which is the constraint-5 error the grammar warns about in as many words. A landmark cannot help either, because landmarks are cells and every event in the language takes an object as its first argument. So the hole is a property of the arm, it is permanent for this level, and the only correct response is the one the playbook now encodes: price the burn in advance and read refutations by their divergence set."
    [depends: the_meter_edge_saturates_the_refutation_channel  probe: passed]
```

=== PLAYBOOK ===
```
# playbook.dsl -- what to buy with the next command, not a route.
#
# ================= THE ONLY THING THAT MATTERS THIS ROUND =================
# ACTION2 FROM SPAWN IS EXHAUSTED. It has been pressed seven times, its two
# rules stand at 168/168, its cascade behaviour is settled 7/7, and its only
# remaining effect is one meter cell I cannot draw. An eighth press buys
# NOTHING and costs one command and one bar cell. The same is true of
# ACTION5 pressed from lattice (2,2): seven presses, 168/168, seven panel
# toggles, nothing left in it.
#
# Twelve of the last twelve commands were those two keys alternating between
# those two cells. Three consecutive rounds. The manual is not the problem:
# certify replays every transition exactly, explains every pixel, admits no
# clash, and all twelve probe_refutations in three rounds had divergence sets
# lying entirely on the meter's undrawable leading edge. The RANKING is the
# problem, so this file is deliberately short -- a criterion at line thirty
# is a criterion nobody read.
#
# ---------------------------------------------------------------------------
# WHY THE RANKING FAILED: every ACTION2 press burns a meter cell; every burn
# lands on a cell that is board at the instant it burns; no rule the manual
# can express draws it. So EVERY ACTION2 PRESS FIRES A REFUTATION however
# little it teaches, and a desk that ranks by refutation-fired keeps buying
# the move that fires one. Read divergence SETS, not hashes. The first two
# prunes encode this.
#
# WHAT THIS ROUND ACTUALLY BOUGHT, honestly: two more witnesses for rules
# already at full coverage (nothing), two more panel toggles (nothing), two
# more burns on the diagonal where both meter readings agree (nothing), and
# one sharpening -- the 7-frame/9-frame cascade split is now 7/7.
#
# ---------------------------------------------------------------------------
# THE BOARD AS IT STANDS (state 17): body home at lattice (1,2); panel in
# configuration B; EIGHT meter cells burned, cols 56-63 of row 63; the next
# command has index 18, which is EVEN. Eleven lattice cells are reachable and
# the body has stood in TWO. Three steps east along lattice row 1 reach the
# cell adjacent to the knob; the knob gates the comb; the comb gates every
# route to the socket. Under the harsher meter reading 56 commands remain and
# the route costs about nineteen, so the budget is not yet binding -- waste
# is.
#
# WHAT TO BUY, AND WHY, AS CRITERIA:
#
#  (1) PARITY FIRST, BECAUSE IT IS FREE AND IT COMPOUNDS. Seventeen commands,
#      seventeen times a key whose parity matched its index's parity, zero
#      separation of the two meter readings. Index 18 is even. An ODD key
#      bought now separates them; the EVEN-key probe it displaces separates
#      them too when bought at index 19. Taking the odd probe first collects
#      the separation on both commands; taking the even one first collects it
#      on neither. That is an ordering consequence, not a stored route.
#
#  (2) THE ODD PROBE AVAILABLE HERE IS THE FIFTH KEY PRESSED AT HOME, AND IT
#      IS THE CHEAPEST TRIPLE ON THE BOARD. The body has never been at spawn
#      when that key was pressed -- seven presses, all from one cell south.
#      The manual stakes a prediction of EXACTLY ZERO CHANGED CELLS, the only
#      zero-pixel stake it can make. Zero cells confirms the spawn_probe
#      guard and kills the parity reading. One cell on the bar confirms the
#      guard and kills the action-keying reading. Twenty-three cells refutes
#      the guard and puts thirteen rules into repair. Forty-eight cells names
#      that key as UNDO rather than UP or RETURN. Four outcomes, all legible
#      in the raw pixel count, every one decisive.
#
#  (3) THE EAST KEY IS THE ONLY QUESTION WHOSE ANSWER MOVES THE BODY, and it
#      is next. At spawn west is void and east is open floor for three
#      lattice cells, so the right-hand direction candidate pressed here
#      either steps east or names the other candidate by elimination -- the
#      first key was already excluded from east at t1. Advertised cost if it
#      moves: 49 divergent cells, all of them cells the manual said in
#      advance it cannot own. DO NOT READ THAT AS A REFUTATION. A zero-cell
#      answer at an even index kills both meter readings at once.
#
#  (4) TWO KEYS HAVE NEVER BEEN PRESSED AT ALL. Every outcome of either is
#      new information on a board where twenty rules sit at full coverage,
#      and one of them is plausibly the click that presses a knob the body
#      cannot stand on. Rank behind (2) and (3), ahead of any repeat.
#
#  (5) ONE PRESS IS ONE LATTICE CELL, 7/7. Every distance below is counted in
#      lattice cells, not pixels.
#
# No stored sequence anywhere: every line below is a criterion on the current
# frame plus the manual's own open questions.

order     never_repeat_a_key_at_a_cell_where_its_rules_are_already_full      [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired    [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance                 [proof: lean]
order     take_the_separation_that_compounds_before_the_one_that_does_not    [proof: lean]
order     buy_the_probe_that_closes_three_questions_before_one_that_closes_one [proof: lean]
order     settle_the_east_key_before_routing_toward_the_knob                 [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it                 [proof: lean]
order     try_an_unpressed_key_before_repeating_an_exhausted_one             [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it         [proof: lean]

prune     every_rule_it_would_witness_is_already_at_full_coverage => dead     [proof: lean]
prune     ranked_only_because_a_refutation_fired_on_it => dead                [proof: lean]
prune     divergence_lies_only_on_the_meter_leading_edge => dead              [proof: lean]
prune     repeats_a_key_already_pressed_from_this_very_cell => dead           [proof: lean]
prune     revisits_a_lattice_cell_by_an_already_witnessed_key => dead         [proof: lean]
prune     key_parity_equals_command_index_parity_while_the_meter_is_open => dead [proof: lean]
prune     destination_ring_pixels_are_not_all_floor => dead                   [proof: lean]
prune     action_excluded_for_this_direction_by_an_earlier_no_op => dead      [proof: lean]
prune     route_that_crosses_the_comb_while_it_still_reads_eight => dead      [proof: lean]
prune     meter_exhausted and not goal => dead                                [proof: lean]

heuristic open_questions_a_command_can_close                                 [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_meter_edge                    [admissible: lean]
heuristic lattice_cells_the_body_has_never_occupied                          [admissible: lean]
heuristic lattice_distance_to_the_knob_while_the_gate_is_shut                [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open               [admissible: lean]
heuristic live_readings_a_command_can_eliminate                              [admissible: lean]
heuristic commands_remaining_under_the_worse_of_the_two_meter_readings       [admissible: lean]

prefer    a_key_never_pressed_from_the_cell_the_body_stands_on               [ev: 0/12 commands]
prefer    a_key_whose_parity_differs_from_the_command_index                  [ev: 0/17 commands]
prefer    a_press_at_home_that_splits_up_from_undo_from_return               [ev: 7/7 key5]
prefer    a_direction_key_at_a_cell_where_its_two_candidates_disagree        [ev: 7/9 no_ops]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                   [ev: 17/17 diffs]
prefer    east_along_lattice_row_one_over_any_other_axis                     [ev: 1/1 levels]
prefer    an_unpressed_key_over_repeating_a_known_no_op                      [ev: 2/7 keys]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered            [ev: 1/1 levels]
```

=== LOG ===
```json
[
  {"id": "O-01", "subject": "mdl_segmenter obj0 (colour 9, 8 cells, 3x3, all 18 frames) + obj2 (colour 9, 1x3, all 18) + obj4 (colour 9, 1x64 bar)", "verdict": "accept", "as": "Glyph9 with arc-instances: all", "why": "all three are colour-9 regions the board cannot explain; one per-cell type covers the slot-1 ring, underline 1, the spawn ring and the 8 burned bar cells in 43 instances, and the arm cannot distinguish same-colour types anyway, so declaring them separately would double-claim pixels."},
  {"id": "O-02", "subject": "the 24 lower-ring cells at rows 14-18 cols 14-18", "verdict": "accept", "as": "Vacated (colour 5, arc-instances: all)", "why": "frame-0 colour is floor 5, they change only when the body occupies lattice (2,2), and typing is by frame-0 colour, so the mover changes type as it walks -- stated explicitly in the_manual_heals_one_step_behind."},
  {"id": "O-03", "subject": "mdl_segmenter obj1/obj6/obj8/obj10 (colour 1, 9 cells) and obj5/obj7/obj9/obj11 (colour 2, 8 cells)", "verdict": "entailed", "as": "Spent (9 instances) plus the colour-2 phase of Glyph9's slot-1 ring", "why": "their first_frame indices 0,5,7,9,11,13,15,17 reproduce the A,B,A,B,A,B,A,B toggle my key5 rules already generate; they are phases of two declared 3x3 regions, not new objects, and a second type on the same pixels would clash under constraint 5."},
  {"id": "O-04", "subject": "mdl_segmenter obj3 (colour null, 1006 cells, 50x38)", "verdict": "reject", "why": "connected_components(4) merged the maze floor with the body ring because the mover is floor-adjacent and shares no separating colour; the blob is 1006 cells of which only 48 ever change, so it fails no-entry-without-gain outright, and its failure to isolate the mover is itself recorded in what_the_engines_gave_me."},
  {"id": "O-05", "subject": "the colour-8 comb, column, stem and knob", "verdict": "reject", "as": "board", "why": "not one colour-8 pixel has changed in 18 frames, so the arm gives it no instance and no rule could draw it; declaring it would add a type that explains nothing and owns nothing."},
  {"id": "R-01", "subject": "cegis_miner verdict 'the world does not narrate as one mover'", "verdict": "reject", "why": "the miner requires exactly one move event per transition and every track refused with 'narrates recolor/vanish' or 'object absent at frame 0'; the world does have one mover, but the arm can only express its 24-pixel rigid step as 24 simultaneous recolours, so the verdict describes the instrument, not the physics."},
  {"id": "R-02", "subject": "key2_body_leaves / key2_body_arrives", "verdict": "accept", "why": "seven witnesses t2,t6,t8,t10,t12,t14,t16, 168/168 cells, zero contradictions in three rounds, and the pair is strictly shorter than writing 48 pixels per press."},
  {"id": "R-03", "subject": "meter_burn_key2_next", "verdict": "accept", "why": "six witnesses and it replays every past burn exactly; accepted with the stated limitation that it has zero predictive value on the leading edge because that cell is always board at the moment it burns."},
  {"id": "R-04", "subject": "the thirteen panel rules guarded on colored(spawn_probe, 5)", "verdict": "accept", "why": "seven positive witnesses each at full coverage; the guard atom itself is still unearned (no negative witness in 18 states) and I say so in why_i_keep_the_spawn_probe_guard rather than dropping it, because it is what makes the manual predict silence for a home press."},
  {"id": "R-05", "subject": "key2_floor_leaves (a second-descent rule, text drafted in the manual)", "verdict": "probe-pending", "why": "all seven descents began at spawn, so no transition witnesses the body leaving lattice (2,2) southward; the rule text is parked in the_rules_i_still_have_no_witness_for so one ACTION2 from (2,2) costs a paste, not a round."},
  {"id": "R-06", "subject": "an east-leaves / east-arrives rule pair", "verdict": "probe-pending", "why": "no eastward motion has ever occurred, and the arrival cells rows 8-12 cols 20-24 are board today, so even a correct rule would draw nothing on the first step -- priced in advance at 48 wrong cells."},
  {"id": "L-01", "subject": "zero_space's single global law over 79 cells", "verdict": "entailed", "why": "its cell list is exactly my census -- (2,1) and (2,3) but not (2,2), the aperture cells (10,16) and (16,16) absent, all eight burned bar cells present -- so it restates dynamic_census and adds nothing; zero_space's own verdict is THIN (rank 9 of 395 features, null space 386)."},
  {"id": "L-02", "subject": "the meter parity readings A (key-keyed) and B (index-keyed)", "verdict": "probe-pending", "why": "both score 17/17 and are still numerically identical on every command bought so far; index 18 is even, so any odd key there separates them in one command, and the ordering consequence is now written into the playbook."},
  {"id": "L-03", "subject": "the socket at rows 49-55 cols 43-49 as the winning position", "verdict": "probe-pending", "why": "re-read pixel by pixel from the current frame -- 7x7 colour-9 bracket, open on the left, lone pip at (52,46) coinciding exactly with the aperture of a body standing in lattice (8,7) -- but it has never changed, so it is board and nothing in the manual can yet speak about it."},
  {"id": "L-04", "subject": "the previous manual's claim that four eastward steps reach lattice (1,5)", "verdict": "reject", "why": "C=2 to C=5 is three lattice steps and C=2 to C=6 is four; corrected in the_knob_is_the_only_thing_within_reach because the playbook's distance heuristic depends on it."},
  {"id": "P-01", "subject": "probe_refutations P-09..P-12", "verdict": "accept", "as": "one undrawable pixel per burn, rolled forward by the harness", "why": "the inert chain (P-10 inert = P-09 manual, and so on) shows no resync; the divergence entered at t14 with the burn of (63,57) and gained a second at t16 with (63,56); all 71 cells of the two ACTION5 transitions were drawn correctly, so the ledger is two wrong pixels and four reports."},
  {"id": "P-02", "subject": "the fifth key pressed with the body at home, at command index 18", "verdict": "probe-pending", "why": "the manual stakes exactly zero changed cells; the four possible answers separately settle the spawn_probe guard, the meter reading (odd key at even index), and UNDO versus UP versus RETURN -- three open questions for one command, ranked first in the playbook."},
  {"id": "P-03", "subject": "the eastward direction candidate pressed at spawn", "verdict": "probe-pending", "why": "west is void and east is open, so it either steps or names the other candidate by elimination; ranked second only because at an even index it collects no meter separation, whereas at the following odd index it collects one."},
  {"id": "E-01", "subject": "drawing the ninth meter burn at (63,55)", "verdict": "probe-pending", "as": "impossible in this DSL, recorded as i_cannot_manufacture_an_instance_on_a_cell_that_has_never_changed", "why": "I wanted an instance on a board cell; arc-instances: all only instances cells the board cannot explain, a second colour-9 type would be indistinguishable to the arm and would double-claim, and landmarks cannot receive events -- so I wrote the theorem and priced the burn instead."},
  {"id": "E-02", "subject": "a goal predicate naming the socket", "verdict": "probe-pending", "as": "no goal section, compiling to is_goal -> False", "why": "the socket ring cells are board today and would type as Vacated on first entry, making count(Vacated, color = 9) = 24 true of the body one cell south of spawn; I wanted a goal, wrote none, and named the price in the_goal_section_is_absent_on_purpose -- with no goal the manual ranks nothing and the playbook carries all of it."},
  {"id": "E-03", "subject": "a rule for a click action on the knob", "verdict": "probe-pending", "as": "prose in two_actions_have_never_been_pressed_and_one_of_them_may_be_a_click", "why": "the guard language has act=key(6) but nowhere to put coordinates, so a click rule would fire on every click anywhere; I can record a click's effect once seen and never its precondition."}
]
```
```
