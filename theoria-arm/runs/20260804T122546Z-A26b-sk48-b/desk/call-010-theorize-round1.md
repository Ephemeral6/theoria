# call-010-theorize-round1

model: `claude-opus-5` · 752851 ms · $2.014373 · usage {"cache_creation": {"ephemeral_1h_input_tokens": 40891, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 40891, "cache_read_input_tokens": 0, "inference_geo": "not_available", "input_tokens": 2, "iterations": [{"cache_creation": {"ephemeral_1h_input_tokens": 40891, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 40891, "cache_read_input_tokens": 0, "input_tokens": 2, "output_tokens": 63035, "type": "message"}], "output_tokens": 63035, "server_tool_use": {"web_fetch_requests": 0, "web_search_requests": 0}, "service_tier": "standard", "speed": "standard"}

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
  "ACTION7",
  "RESET"
 ],
 "background": 5,
 "cascade_lengths": [
  1,
  2
 ],
 "cells_needing_an_owner": 77,
 "colours_seen": [
  0,
  1,
  2,
  3,
  4,
  5,
  6,
  8,
  9,
  14
 ],
 "constant_cells": 3995,
 "distinct_states": 13,
 "dynamic_box": [
  29,
  10,
  54,
  63
 ],
 "dynamic_cells": 101,
 "max_frames_in_one_command": 2,
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

Only the cells that have EVER changed are shown (rows 29-10, cols 54-63); everything outside this box has held one colour for the whole history and is board by definition.

```
    111111111122222222223333333333444444444455555555556666
    012345678901234567890123456789012345678901234567890123
 29 555335544444444444444444444444444444455555555555555555
 30 555335544444444444444444444444444444455555555555555555
 31 55533554444444444444444444444444eeee455555555555555555
 32 55522554444444444444444444444444eeee455555555555555555
 33 55522554444444444444444444444444eeee455555555555555555
 34 55533554444444444444444444444444eeee455555555555555555
 35 555335544444444444444444444444444444455555555555555555
 36 566666644444444444444444444444444444455555555555555555
 37 560000644444444444444444444444444444455555555555555555
 38 560660121121144444444444444444444444455555555555555555
 39 560660211211244444444444444444444444455555555555555555
 40 560000644444444444444444444444444444455555555555555555
 41 566666644444444444444444444444444444455555555555555555
 42 555555555555555555555555555555555555555555555555555555
 43 555555555555555555555555555555555555555555555555555555
 44 555555555555555555555555555555555555555555555555555555
 45 555555555555555555555555555555555555555555555555555555
 46 555555555555555555555555555555555555555555555555555555
 47 555555555555555555555555555555555555555555555555555555
 48 555555555555555555555555555555555555555555555555555555
 49 555555555555555555555555555555555555555555555555555555
 50 555555555555555555555555555555555555555555555555555555
 51 555555555555555555555555555555555555555555555555555555
 52 555555555555555555555555555555555555555555555555555555
 53 222222222222222222222222222222222222222222222222233333
 54 444444444444444444444444444444444444444444444444444444
```

## Every command, and what changed

`t` indexes the state sequence. `frames` is how many grids one command returned -- more than one means the world took several internal steps for a single action.

- t0   RESET     frames=1   state=NOT_FINISHED (first frame)
- t1   ACTION1   frames=2   state=NOT_FINISHED 96 cells changed, rows 30-41, cols 11-22, [0, 1, 2, 3, 4, 5, 6] -> [0, 1, 2, 3, 4, 5, 6]
- t2   ACTION2   frames=2   state=NOT_FINISHED 96 cells changed, rows 30-41, cols 11-22, [0, 1, 2, 3, 4, 5, 6] -> [0, 1, 2, 3, 4, 5, 6]
- t3   ACTION3   frames=2   state=NOT_FINISHED (38,17) 2->4; (38,18) 1->4; (38,19) 1->4; (38,20) 2->4; (38,21) 1->4; (38,22) 1->4; (39,17) 1->4; (39,18) 1->4; (39,19) 2->4; (39,20) 1->4; (39,21) 1->4; (39,22) 2->4
- t4   ACTION4   frames=2   state=NOT_FINISHED (38,17) 4->2; (38,18) 4->1; (38,19) 4->1; (38,20) 4->2; (38,21) 4->1; (38,22) 4->1; (39,17) 4->1; (39,18) 4->1; (39,19) 4->2; (39,20) 4->1; (39,21) 4->1; (39,22) 4->2; (53,63) 2->3
- t5   ACTION7   frames=1   state=NOT_FINISHED (38,17) 2->4; (38,18) 1->4; (38,19) 1->4; (38,20) 2->4; (38,21) 1->4; (38,22) 1->4; (39,17) 1->4; (39,18) 1->4; (39,19) 2->4; (39,20) 1->4; (39,21) 1->4; (39,22) 2->4
- t6   ACTION1   frames=2   state=NOT_FINISHED 72 cells changed, rows 30-41, cols 11-16, [0, 1, 2, 3, 5, 6] -> [0, 1, 2, 3, 5, 6]
- t7   ACTION2   frames=2   state=NOT_FINISHED 72 cells changed, rows 30-41, cols 11-16, [0, 1, 2, 3, 5, 6] -> [0, 1, 2, 3, 5, 6]
- t8   ACTION1   frames=2   state=NOT_FINISHED 73 cells changed, rows 30-53, cols 11-62, [0, 1, 2, 3, 5, 6] -> [0, 1, 2, 3, 5, 6]
- t9   ACTION3   frames=1   state=NOT_FINISHED no cells changed
- t10  ACTION2   frames=2   state=NOT_FINISHED 72 cells changed, rows 30-41, cols 11-16, [0, 1, 2, 3, 5, 6] -> [0, 1, 2, 3, 5, 6]
- t11  ACTION1   frames=2   state=NOT_FINISHED 73 cells changed, rows 30-53, cols 11-61, [0, 1, 2, 3, 5, 6] -> [0, 1, 2, 3, 5, 6]
- t12  ACTION2   frames=2   state=NOT_FINISHED 72 cells changed, rows 30-41, cols 11-16, [0, 1, 2, 3, 5, 6] -> [0, 1, 2, 3, 5, 6]
- t13  ACTION1   frames=2   state=NOT_FINISHED 72 cells changed, rows 30-41, cols 11-16, [0, 1, 2, 3, 5, 6] -> [0, 1, 2, 3, 5, 6]
- t14  ACTION2   frames=2   state=NOT_FINISHED 73 cells changed, rows 30-53, cols 11-60, [0, 1, 2, 3, 5, 6] -> [0, 1, 2, 3, 5, 6]
- t15  ACTION1   frames=2   state=NOT_FINISHED 72 cells changed, rows 30-41, cols 11-16, [0, 1, 2, 3, 5, 6] -> [0, 1, 2, 3, 5, 6]
- t16  ACTION2   frames=2   state=NOT_FINISHED 72 cells changed, rows 30-41, cols 11-16, [0, 1, 2, 3, 5, 6] -> [0, 1, 2, 3, 5, 6]
- t17  ACTION4   frames=2   state=NOT_FINISHED (38,17) 4->2; (38,18) 4->1; (38,19) 4->1; (38,20) 4->2; (38,21) 4->1; (38,22) 4->1; (39,17) 4->1; (39,18) 4->1; (39,19) 4->2; (39,20) 4->1; (39,21) 4->1; (39,22) 4->2; (53,59) 2->3

## What the engines proposed

These are PROPOSALS. Nothing here is accepted until you accept it, and an engine cannot name anything -- `obj0` is the best it can do.

```json
{
 "cegis_miner": {
  "engine": "cegis_miner",
  "n_actions": 17,
  "n_states": 18,
  "refusals": [
   "ValueError: transition 0 narrates ['vanish']; only move/none are mined on this fixture",
   "ValueError: transition 0 narrates ['vanish']; only move/none are mined on this fixture",
   "ValueError: transition 2 narrates ['vanish']; only move/none are mined on this fixture",
   "ValueError: transition 2 narrates ['vanish']; only move/none are mined on this fixture",
   "ValueError: transition 2 narrates ['vanish']; only move/none are mined on this fixture",
   "ValueError: transition 2 narrates ['vanish']; only move/none are mined on this fixture",
   "ValueError: transition 2 narrates ['vanish']; only move/none are mined on this fixture",
   "ValueError: transition 2 narrates ['vanish']; only move/none are mined on this fixture",
   "ValueError: transition 3 narrates ['vanish']; only move/none are mined on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
   "ValueError: object absent at frame 0; unsupported on this fixture",
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
    "ms": 0,
    "refused": "ValueError: transition 0 narrates ['vanish']; only move/none are mined on this fixture",
    "track_id": "obj0"
   },
   {
    "ms": 0,
    "refused": "ValueError: transition 0 narrates ['vanish']; only move/none are mined on this fixture",
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
    "error": "NoSeparatingGuard: no literal separates transition 2 from the positives",
    "mine_ms": 0,
    "ms": 0,
    "traceback": "Traceback (most recent call last):\n  File \"C:\\Users\\user\\Desktop\\theoria\\theoria-arm\\world\\adapt.py\", line 48, in _timed\n    value = fn(*args, **kwargs)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\__init__.py\", line 92, in run\n    result = mine(transitions)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 320, in mine\n    guard, trace, added = synthesize(positives, universe, masks)\n                          ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 157, in synthesize\n    raise NoSeparatingGuard(\n        \"no literal separates transition %d from the positives\" % cex\n    )\nengines.cegis_miner.miner.NoSeparatingGuard: no literal separates transition 2 from the positives\n",
    "track_id": "obj3",
    "transitions": 17
   },
   {
    "error": "NoSeparatingGuard: no literal separates transition 2 from the positives",
    "mine_ms": 0,
    "ms": 0,
    "traceback": "Traceback (most recent call last):\n  File \"C:\\Users\\user\\Desktop\\theoria\\theoria-arm\\world\\adapt.py\", line 48, in _timed\n    value = fn(*args, **kwargs)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\__init__.py\", line 92, in run\n    result = mine(transitions)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 320, in mine\n    guard, trace, added = synthesize(positives, universe, masks)\n                          ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 157, in synthesize\n    raise NoSeparatingGuard(\n        \"no literal separates transition %d from the positives\" % cex\n    )\nengines.cegis_miner.miner.NoSeparatingGuard: no literal separates transition 2 from the positives\n",
    "track_id": "obj4",
    "transitions": 17
   },
   {
    "error": "NoSeparatingGuard: no literal separates transition 2 from the positives",
    "mine_ms": 0,
    "ms": 0,
    "traceback": "Traceback (most recent call last):\n  File \"C:\\Users\\user\\Desktop\\theoria\\theoria-arm\\world\\adapt.py\", line 48, in _timed\n    value = fn(*args, **kwargs)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\__init__.py\", line 92, in run\n    result = mine(transitions)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 320, in mine\n    guard, trace, added = synthesize(positives, universe, masks)\n                          ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 157, in synthesize\n    raise NoSeparatingGuard(\n        \"no literal separates transition %d from the positives\" % cex\n    )\nengines.cegis_miner.miner.NoSeparatingGuard: no literal separates transition 2 from the positives\n",
    "track_id": "obj5",
    "transitions": 17
   },
   {
    "error": "NoSeparatingGuard: no literal separates transition 2 from the positives",
    "mine_ms": 0,
    "ms": 0,
    "traceback": "Traceback (most recent call last):\n  File \"C:\\Users\\user\\Desktop\\theoria\\theoria-arm\\world\\adapt.py\", line 48, in _timed\n    value = fn(*args, **kwargs)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\__init__.py\", line 92, in run\n    result = mine(transitions)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 320, in mine\n    guard, trace, added = synthesize(positives, universe, masks)\n                          ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 157, in synthesize\n    raise NoSeparatingGuard(\n        \"no literal separates transition %d from the positives\" % cex\n    )\nengines.cegis_miner.miner.NoSeparatingGuard: no literal separates transition 2 from the positives\n",
    "track_id": "obj6",
    "transitions": 17
   },
   {
    "error": "NoSeparatingGuard: no literal separates transition 2 from the positives",
    "mine_ms": 0,
    "ms": 0,
    "traceback": "Traceback (most recent call last):\n  File \"C:\\Users\\user\\Desktop\\theoria\\theoria-arm\\world\\adapt.py\", line 48, in _timed\n    value = fn(*args, **kwargs)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\__init__.py\", line 92, in run\n    result = mine(transitions)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 320, in mine\n    guard, trace, added = synthesize(positives, universe, masks)\n                          ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 157, in synthesize\n    raise NoSeparatingGuard(\n        \"no literal separates transition %d from the positives\" % cex\n    )\nengines.cegis_miner.miner.NoSeparatingGuard: no literal separates transition 2 from the positives\n",
    "track_id": "obj7",
    "transitions": 17
   },
   {
    "error": "NoSeparatingGuard: no literal separates transition 2 from the positives",
    "mine_ms": 0,
    "ms": 0,
    "traceback": "Traceback (most recent call last):\n  File \"C:\\Users\\user\\Desktop\\theoria\\theoria-arm\\world\\adapt.py\", line 48, in _timed\n    value = fn(*args, **kwargs)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\__init__.py\", line 92, in run\n    result = mine(transitions)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 320, in mine\n    guard, trace, added = synthesize(positives, universe, masks)\n                          ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 157, in synthesize\n    raise NoSeparatingGuard(\n        \"no literal separates transition %d from the positives\" % cex\n    )\nengines.cegis_miner.miner.NoSeparatingGuard: no literal separates transition 2 from the positives\n",
    "track_id": "obj8",
    "transitions": 17
   },
   {
    "ms": 0,
    "refused": "ValueError: transition 2 narrates ['vanish']; only move/none are mined on this fixture",
    "track_id": "obj9"
   },
   {
    "ms": 0,
    "refused": "ValueError: transition 2 narrates ['vanish']; only move/none are mined on this fixture",
    "track_id": "obj10"
   },
   {
    "ms": 0,
    "refused": "ValueError: transition 2 narrates ['vanish']; only move/none are mined on this fixture",
    "track_id": "obj11"
   },
   {
    "ms": 0,
    "refused": "ValueError: transition 2 narrates ['vanish']; only move/none are mined on this fixture",
    "track_id": "obj12"
   },
   {
    "error": "NoSeparatingGuard: no literal separates transition 2 from the positives",
    "mine_ms": 0,
    "ms": 0,
    "traceback": "Traceback (most recent call last):\n  File \"C:\\Users\\user\\Desktop\\theoria\\theoria-arm\\world\\adapt.py\", line 48, in _timed\n    value = fn(*args, **kwargs)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\__init__.py\", line 92, in run\n    result = mine(transitions)\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 320, in mine\n    guard, trace, added = synthesize(positives, universe, masks)\n                          ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\Users\\user\\Desktop\\theoria\\engine-rig\\engines\\cegis_miner\\miner.py\", line 157, in synthesize\n    raise NoSeparatingGuard(\n        \"no literal separates transition %d from the positives\" % cex\n    )\nengines.cegis_miner.miner.NoSeparatingGuard: no literal separates transition 2 from the positives\n",
    "track_id": "obj13",
    "transitions": 17
   },
   {
    "ms": 0,
    "refused": "ValueError: transition 2 narrates ['vanish']; only move/none are mined on this fixture",
    "track_id": "obj14"
   },
   {
    "ms": 0,
    "refused": "ValueError: transition 2 narrates ['vanish']; only move/none are mined on this fixture",
    "track_id": "obj15"
   },
   {
    "ms": 0,
    "refused": "ValueError: transition 3 narrates ['vanish']; only move/none are mined on this fixture",
    "track_id": "obj16"
   },
   {
    "error": "NoSeparatingGuard: no literal separates transition 1 from the positives",
    "mine_ms": 1,
    "ms": 0,
    "traceback": "Traceback (most recent call last):\n  File \"C:\\Users\\user\\Desktop\\theoria\\theoria-arm\\world\\adapt.py\", line 48, in _timed\n    value = fn(*args, **kwargs)\n  F
```

The full proposal stream is 2866 rows in `candidates.jsonl`.

## The manual as it stands

```
# theory.dsl -- sixth edition.
#
# WHAT THIS ROUND ACTUALLY BOUGHT: NOTHING FROM THE WORLD, AND I SAY SO FIRST.
# The store is identical to last round in every number I can check: states 14,
# steps 14, dynamic_cells 99, cells_needing_an_owner 75, constant_cells 3997,
# distinct_states 10, actions_used the same six. NO COMMAND WAS PRESSED. The
# round was spent re-certifying the manual I already had. Constraint 6 says the
# honest manual is small; a round with no new observation is a round in which
# the manual MUST NOT GROW A RULE, and this one does not. Every rule below is
# byte-identical to the fifth edition. What is new is verification I did by
# hand, and one repair I computed and then refused.
#
# 1. THE ONE SURPRISE IS THE ONE I PRICED, BY CELL AND BY TRANSITION INDEX.
#    replay_mismatch at t=7, ACTION1, one cell (53,62), manual 2, world 3. The
#    fifth edition said, in the manual and again in the playbook: "replay
#    carries 1 wrong cell from transition 7 and 2 from transition 10" and
#    "row-53 divergences buy nothing". I answer this surprise with an EXPLICIT
#    REFUSAL TO CHANGE, not with silence, and the refusal has arithmetic behind
#    it -- see the_only_repair_available_to_the_meter_makes_replay_worse.
#
# 2. I PREDICTED THE CERTIFY REPORT LINE BY LINE AND IT CAME BACK LINE BY LINE.
#    Written before I saw it: 7 of 13 replay exactly, first divergence t=7, the
#    single cell (53,62) manual 2 world 3, responsibility 0 of 4096, 0 ambiguity
#    clashes. Returned: 7/13, t=7, (53,62) 2 vs 3, 0/4096 unexplained, 0
#    clashes, 70/70 pairs adjudicated, 0 step crashes. Five for five, including
#    the prediction of my own permanent failure. That is what a dated prediction
#    is for, and last round the same device killed my clock.
#
# 3. NEW, AND CHECKED BY HAND: EVERY COVERAGE COLUMN SUMS TO ITS TYPE. I
#    re-derived all 40 swap coverages from the current frame rather than
#    trusting them, and each type's k1 rules and k2 rules each partition its
#    instances exactly -- Field 14+8+1+1 = 24, Frame 14+2+2+4 = 22 and
#    16+2+4 = 22, Hollow 8+2+2 = 12 and 10+2 = 12, BarBody 4+4 = 8 and
#    2+2+2+2 = 8, Dot 1+8 = 9, Blank 8+4 = 12, BarCore 4+1+4 = 9 of 12. The
#    ONLY deficit anywhere is BarCore's 3, and those 3 are the meter cells I
#    have proven unwritable. 96 of 99 owned cells are covered in both
#    directions, and 96 is exactly the largest diff ever observed (t1, t2).
#    The manual's silence is now located to the cell by arithmetic, not by
#    assertion. See every_coverage_column_sums_to_its_type.
#
# 4. THE CENSUS WAS RE-READ OFF THE CURRENT FRAME, NOT COPIED. Box in the TOP
#    slot: 22 sixes (6+2+3+3+2+6 down rows 30-35) and 12 zeroes, ports 1 at
#    (32,16) and 2 at (33,16). Bar in the BOTTOM slot, four rows only: 3,3/3,3
#    at rows 36-37 and 2,2/2,2 at rows 38-39, cols 13-14, rows 40-41
#    background. Row 53: colour 2 from col 10 to col 60, colour 3 at 61, 62,
#    63. 24+8+12+12+22+12+9 = 99 = dynamic_cells, and 99-24 = 75 =
#    cells_needing_an_owner.
#
# WHERE I AM. S13 = S11 = W1, thirteen commands since RESET, both readouts
# blank, three meter cells lit.
#
# WHAT I STILL HAVE NOT SEEN, AFTER FOURTEEN STATES AND TWO ROUNDS OF NOT
# BEING BOUGHT A COMMAND: ACTION1 pressed in W1. ACTION2 in W0. ACTION4 in W1.
# ACTION5 and ACTION6 at all. A GameState other than NOT_FINISHED. Any cell
# outside rows 30-41 and row 53 changing.

semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Field    { pos: Coord, color: Int }   # arc-colour: 5  arc-instances: all
  object BarBody  { pos: Coord, color: Int }   # arc-colour: 3  arc-instances: all
  object BarCore  { pos: Coord, color: Int }   # arc-colour: 2  arc-instances: all
  object Blank    { pos: Coord, color: Int }   # arc-colour: 4  arc-instances: all
  object Frame    { pos: Coord, color: Int }   # arc-colour: 6  arc-instances: all
  object Hollow   { pos: Coord, color: Int }   # arc-colour: 0  arc-instances: all
  object Dot      { pos: Coord, color: Int }   # arc-colour: 1  arc-instances: all
  landmark bottom_port                          # arc-cell: (38, 16)
  Field   [segment: dynamic_colour_5 ev: t0-t13 compress: 24]
  BarBody [segment: dynamic_colour_3 ev: t0-t13 compress: 8]
  BarCore [segment: dynamic_colour_2 ev: t0-t13 compress: 12]
  Blank   [segment: dynamic_colour_4 ev: t0-t13 compress: 12]
  Frame   [segment: dynamic_colour_6 ev: t0-t13 compress: 22]
  Hollow  [segment: dynamic_colour_0 ev: t0-t13 compress: 12]
  Dot     [segment: dynamic_colour_1 ev: t0-t13 compress: 9]

events:
  event recolored(o, c)

rules:
  rule k1_field_to_frame forall ?p in Field [ev: t1,t6,t8,t11,t13 cov: 14/14]
    when act=key(1) and colored(?p, 5) and colored(below(below(below(below(below(below(?p)))))), 6) then recolored(?p, 6)

  rule k1_field_to_hollow forall ?p in Field [ev: t1,t6,t8,t11,t13 cov: 8/8]
    when act=key(1) and colored(?p, 5) and colored(below(below(below(below(below(below(?p)))))), 0) then recolored(?p, 0)

  rule k1_field_to_dot forall ?p in Field [ev: t1,t6,t8,t11,t13 cov: 1/1]
    when act=key(1) and colored(?p, 5) and colored(below(below(below(below(below(below(?p)))))), 1) then recolored(?p, 1)

  rule k1_field_to_core forall ?p in Field [ev: t1,t6,t8,t11,t13 cov: 1/1]
    when act=key(1) and colored(?p, 5) and colored(below(below(below(below(below(below(?p)))))), 2) then recolored(?p, 2)

  rule k1_bar_to_frame forall ?p in BarBody [ev: t1,t6,t8,t11,t13 cov: 4/4]
    when act=key(1) and colored(?p, 3) and colored(below(below(below(below(below(below(?p)))))), 6) then recolored(?p, 6)

  rule k1_bar_to_hollow forall ?p in BarBody [ev: t1,t6,t8,t11,t13 cov: 4/4]
    when act=key(1) and colored(?p, 3) and colored(below(below(below(below(below(below(?p)))))), 0) then recolored(?p, 0)

  rule k1_core_to_frame forall ?p in BarCore [ev: t1,t6,t8,t11,t13 cov: 4/4]
    when act=key(1) and colored(?p, 2) and colored(above(above(?p)), 3) and colored(below(below(below(below(below(below(?p)))))), 6) then recolored(?p, 6)

  rule k1_blank_to_dot forall ?p in Blank [ev: t1 cov: 8/8]
    when act=key(1) and colored(?p, 4) and colored(below(below(below(below(below(below(?p)))))), 1) then recolored(?p, 1)

  rule k1_blank_to_core forall ?p in Blank [ev: t1 cov: 4/4]
    when act=key(1) and colored(?p, 4) and colored(below(below(below(below(below(below(?p)))))), 2) then recolored(?p, 2)

  rule k1_frame_to_field forall ?p in Frame [ev: t1,t6,t8,t11,t13 cov: 14/14]
    when act=key(1) and colored(?p, 6) and colored(above(above(above(above(above(above(?p)))))), 5) then recolored(?p, 5)

  rule k1_frame_to_bar forall ?p in Frame [ev: t1,t6,t8,t11,t13 cov: 2/2]
    when act=key(1) and colored(?p, 6) and colored(above(above(?p)), 3) and colored(above(above(above(above(above(above(?p)))))), 3) then recolored(?p, 3)

  rule k1_frame_clears forall ?p in Frame [ev: t1,t6,t8,t11,t13 cov: 2/2]
    when act=key(1) and colored(?p, 6) and colored(above(above(?p)), 6) and colored(above(above(above(above(above(above(?p)))))), 3) then recolored(?p, 5)

  rule k1_frame_to_core forall ?p in Frame [ev: t1,t6,t8,t11,t13 cov: 4/4]
    when act=key(1) and colored(?p, 6) and colored(above(above(above(above(above(above(?p)))))), 2) then recolored(?p, 2)

  rule k1_hollow_to_field forall ?p in Hollow [ev: t1,t6,t8,t11,t13 cov: 8/8]
    when act=key(1) and colored(?p, 0) and colored(above(above(above(above(above(above(?p)))))), 5) then recolored(?p, 5)

  rule k1_hollow_to_bar forall ?p in Hollow [ev: t1,t6,t8,t11,t13 cov: 2/2]
    when act=key(1) and colored(?p, 0) and colored(above(above(?p)), 3) and colored(above(above(above(above(above(above(?p)))))), 3) then recolored(?p, 3)

  rule k1_hollow_clears forall ?p in Hollow [ev: t1,t6,t8,t11,t13 cov: 2/2]
    when act=key(1) and colored(?p, 0) and colored(above(above(?p)), 6) and colored(above(above(above(above(above(above(?p)))))), 3) then recolored(?p, 5)

  rule k1_dot_to_field forall ?p in Dot [ev: t1,t6,t8,t11,t13 cov: 1/1]
    when act=key(1) and colored(?p, 1) and colored(above(above(above(above(above(above(?p)))))), 5) then recolored(?p, 5)

  rule k1_dot_to_blank forall ?p in Dot [ev: t1 cov: 8/8]
    when act=key(1) and colored(?p, 1) and colored(above(above(above(above(above(above(?p)))))), 4) then recolored(?p, 4)

  rule k1_core_to_field forall ?p in BarCore [ev: t1,t6,t8,t11,t13 cov: 1/1]
    when act=key(1) and colored(?p, 2) and colored(leftof(?p), 0) and colored(above(above(above(above(above(above(?p)))))), 5) then recolored(?p, 5)

  rule k1_core_to_blank forall ?p in BarCore [ev: t1 cov: 4/4]
    when act=key(1) and colored(?p, 2) and colored(leftof(?p), 1) and colored(above(above(above(above(above(above(?p)))))), 4) then recolored(?p, 4)

  rule k2_field_from_frame forall ?p in Field [ev: t2,t7,t10,t12 cov: 14/14]
    when act=key(2) and colored(?p, 6) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule k2_field_from_hollow forall ?p in Field [ev: t2,t7,t10,t12 cov: 8/8]
    when act=key(2) and colored(?p, 0) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule k2_field_from_dot forall ?p in Field [ev: t2,t7,t10,t12 cov: 1/1]
    when act=key(2) and colored(?p, 1) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule k2_field_from_core forall ?p in Field [ev: t2,t7,t10,t12 cov: 1/1]
    when act=key(2) and colored(?p, 2) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule k2_bar_from_frame forall ?p in BarBody [ev: t2,t7,t10,t12 cov: 2/2]
    when act=key(2) and colored(?p, 6) and colored(below(below(below(below(below(below(?p)))))), 3) then recolored(?p, 3)

  rule k2_bar_from_hollow forall ?p in BarBody [ev: t2,t7,t10,t12 cov: 2/2]
    when act=key(2) and colored(?p, 0) and colored(below(below(below(below(below(below(?p)))))), 3) then recolored(?p, 3)

  rule k2_bar_regrows_from_hollow forall ?p in BarBody [ev: t2,t7,t10,t12 cov: 2/2]
    when act=key(2) and colored(?p, 0) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 3)

  rule k2_bar_regrows_from_frame forall ?p in BarBody [ev: t2,t7,t10,t12 cov: 2/2]
    when act=key(2) and colored(?p, 6) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 3)

  rule k2_core_from_frame forall ?p in BarCore [ev: t2,t7,t10,t12 cov: 4/4]
    when act=key(2) and colored(?p, 6) and colored(below(below(below(below(below(below(?p)))))), 2) then recolored(?p, 2)

  rule k2_blank_from_dot forall ?p in Blank [ev: t2 cov: 8/8]
    when act=key(2) and colored(?p, 1) and colored(below(below(below(below(below(below(?p)))))), 4) then recolored(?p, 4)

  rule k2_blank_from_core forall ?p in Blank [ev: t2 cov: 4/4]
    when act=key(2) and colored(?p, 2) and colored(below(below(below(below(below(below(?p)))))), 4) then recolored(?p, 4)

  rule k2_frame_from_field forall ?p in Frame [ev: t2,t7,t10,t12 cov: 16/16]
    when act=key(2) and colored(?p, 5) and colored(above(above(above(above(above(above(?p)))))), 6) then recolored(?p, 6)

  rule k2_frame_from_bar forall ?p in Frame [ev: t2,t7,t10,t12 cov: 2/2]
    when act=key(2) and colored(?p, 3) and colored(above(above(above(above(above(above(?p)))))), 6) then recolored(?p, 6)

  rule k2_frame_from_core forall ?p in Frame [ev: t2,t7,t10,t12 cov: 4/4]
    when act=key(2) and colored(?p, 2) and colored(above(above(above(above(above(above(?p)))))), 6) then recolored(?p, 6)

  rule k2_hollow_from_field forall ?p in Hollow [ev: t2,t7,t10,t12 cov: 10/10]
    when act=key(2) and colored(?p, 5) and colored(above(above(above(above(above(above(?p)))))), 0) then recolored(?p, 0)

  rule k2_hollow_from_bar forall ?p in Hollow [ev: t2,t7,t10,t12 cov: 2/2]
    when act=key(2) and colored(?p, 3) and colored(above(above(above(above(above(above(?p)))))), 0) then recolored(?p, 0)

  rule k2_dot_from_field forall ?p in Dot [ev: t2,t7,t10,t12 cov: 1/1]
    when act=key(2) and colored(?p, 5) and colored(above(above(above(above(above(above(?p)))))), 1) then recolored(?p, 1)

  rule k2_dot_from_blank forall ?p in Dot [ev: t2 cov: 8/8]
    when act=key(2) and colored(?p, 4) and colored(above(above(above(above(above(above(?p)))))), 1) then recolored(?p, 1)

  rule k2_core_from_field forall ?p in BarCore [ev: t2,t7,t10,t12 cov: 1/1]
    when act=key(2) and colored(?p, 5) and colored(above(above(above(above(above(above(?p)))))), 2) then recolored(?p, 2)

  rule k2_core_from_blank forall ?p in BarCore [ev: t2 cov: 4/4]
    when act=key(2) and colored(?p, 4) and colored(above(above(above(above(above(above(?p)))))), 2) then recolored(?p, 2)

  rule k3_dot_blanks forall ?s in Dot [ev: t3 cov: 8/8]
    when act=key(3) and colored(?s, 1) and colored(above(above(above(above(above(above(?s)))))), 4) then recolored(?s, 4)

  rule k3_core_blanks forall ?s in BarCore [ev: t3 cov: 4/4]
    when act=key(3) and colored(?s, 2) and colored(leftof(?s), 1) and colored(above(above(above(above(above(above(?s)))))), 4) then recolored(?s, 4)

  rule k4_dot_lights forall ?s in Dot [ev: t4 cov: 8/8]
    when act=key(4) and colored(?s, 4) and colored(bottom_port, 1) then recolored(?s, 1)

  rule k4_core_lights forall ?s in BarCore [ev: t4 cov: 4/4]
    when act=key(4) and colored(?s, 4) and colored(bottom_port, 1) then recolored(?s, 2)

  rule meter_first_tick_replay_patch forall ?s in BarCore [ev: t4 cov: 1/1]
    when act=key(4) and colored(?s, 2) and rightof(?s) = wall then recolored(?s, 3)

  rule k7_dot_blanks forall ?s in Dot [ev: t5 cov: 8/8]
    when act=key(7) and colored(?s, 1) and colored(above(above(above(above(above(above(?s)))))), 4) then recolored(?s, 4)

  rule k7_core_blanks forall ?s in BarCore [ev: t5 cov: 4/4]
    when act=key(7) and colored(?s, 2) and colored(leftof(?s), 1) and colored(above(above(above(above(above(above(?s)))))), 4) then recolored(?s, 4)

laws:
  invariant field_instances count(Field) = 24 [status: census, recounted by hand from the current frame this round]
  invariant barbody_instances count(BarBody) = 8 [status: census, recounted]
  invariant barcore_instances count(BarCore) = 12 [status: census, 4 bar core + 1 port + 4 readout cores + 3 meter]
  invariant blank_instances count(Blank) = 12 [status: census, the dark readout at frame 0]
  invariant frame_instances count(Frame) = 22 [status: census, 6+2+3+3+2+6 read down the box in the current frame]
  invariant hollow_instances count(Hollow) = 12 [status: census, 4+2+2+4 read down the box in the current frame]
  invariant dot_instances count(Dot) = 9 [status: census, 8 readout dots plus the upper port pixel]
  invariant board_cells count(board) = 3997 [status: matches constant_cells exactly, unchanged this round]
  invariant total_owned_cells count(Field) + count(BarBody) + count(BarCore) + count(Blank) + count(Frame) + count(Hollow) + count(Dot) = 99 [status: matches dynamic_cells exactly, unchanged this round]

  theorem a_round_passed_with_no_new_command_and_the_manual_must_not_grow "Every store number is identical to last edition: states 14, steps 14, distinct_states 10, dynamic_cells 99, cells_needing_an_owner 75, constant_cells 3997, actions_used the same six, dynamic_box the same. NO COMMAND WAS PRESSED THIS ROUND. Therefore there is no new evidence, therefore constraint 2 forbids a new rule, and every rule in this file is byte-identical to the fifth edition. I state this at the top because the temptation in a round like this is to pay for the round with invention, and invention with no witness is exactly what constraint 2 exists to stop. What I did instead was verification I could do without spending a command: I re-read the census off the current frame, I re-derived all forty coverage figures, and I computed the one repair the replay mismatch invites and rejected it with arithmetic."
    [probe: passed]

  theorem the_certify_report_was_predicted_line_by_line "Before seeing it I wrote: 7 of 13 transitions replay exactly, first divergence at t=7, the single cell (53,62) manual 2 world 3, responsibility 0 of 4096 unexplained, 0 ambiguity clashes. Certify returned 7/13, first divergence t=7 ACTION1, cells_wrong 1 at (53,62) manual 2 world 3, cells_unexplained 0 of 4096, n_clashes 0 with 70 of 70 pairs adjudicated and 0 step crashes. Five predictions, five hits, and one of them was a prediction of my own permanent failure. This is the second consecutive round in which a dated prediction decided something -- last round the dated one DIED and took my period-4 clock with it, this round it lived and confirms that the divergence set is closed. A manual that can forecast its own certify report has located its ignorance, which is the only thing an under-claiming manual can offer."
    [depends: the_tick_is_not_a_function_of_the_frame_and_no_guard_language_can_help  probe: passed]

  theorem the_only_repair_available_to_the_meter_makes_replay_worse "The replay_mismatch surprise demands an answer, so here is the answer with numbers. The only repair the guard language admits is propagation: a BarCore wearing colour 2 whose RIGHT NEIGHBOUR is 3 becomes 3. It needs no counter, it fits the observed left-to-right filling, and it is wrong. Under cascade single_frame it would fire on the very next command after each tick, so (53,62) would turn 3 at command 5 while the world turned it at command 8, and (53,61) at command 6 while the world turned it at command 11. Summing wrong-cell-transitions: TODAY the cost is (53,62) wrong across transitions 7-12 and (53,61) across 10-12, nine in all, and it is BOUNDED because no rule of mine ever grounds on a meter cell. WITH THE REPAIR it is about ten, AND IT IS UNBOUNDED: the wave keeps walking left into (53,60), (53,59) and onward, turning cells that have NEVER CHANGED -- cells that are board, not instances -- into confident wrong drawings, and each new tick restarts it. I refuse the repair. A patch that buys no right cell and spends the board is worse than a declared gap, and the playbook already prunes it in two lines."
    [depends: the_tick_is_not_a_function_of_the_frame_and_no_guard_language_can_help  probe: passed]

  theorem every_coverage_column_sums_to_its_type "New this round and checked by hand rather than copied. For each type, the k1 rules partition its instances and so do the k2 rules, exactly. Field 14+8+1+1 = 24 both ways. Frame 14+2+2+4 = 22 going down and 16+2+4 = 22 coming up, and I verified the 16 by reading the current frame: of the 22 frame-0 colour-6 positions, in W1 sixteen show background, two show 3 at row 36 cols 13-14, and four show 2 at rows 38-39 cols 13-14. Hollow 8+2+2 = 12 and 10+2 = 12. BarBody 4+4 = 8 and 2+2+2+2 = 8. Dot 1+8 = 9. Blank 8+4 = 12. BarCore 4+1+4 = 9 OF 12. That single deficit of 3 is the whole of my ignorance about the swap, and it is the three meter cells. So 96 of 99 owned cells are covered in BOTH directions, and 96 is exactly the largest diff the world has ever produced (t1 and t2, when the readout was lit). The manual's silence is now bounded by arithmetic instead of by assertion."
    [depends: the_swap_rules_are_forty_and_constraint_three_is_still_failed  probe: passed]

  theorem the_period_four_clock_is_refuted_and_i_dated_the_prediction_that_died "Last edition but one I wrote, before the commands ran: commands 10 and 11 leave row 53 alone, command 12 turns (53,61) from 2 to 3. The world ticked at COMMAND 11 and left row 53 alone at 10, 12 and 13. Three ticks: command 4 on (53,63), command 8 on (53,62), command 11 on (53,61), intervals 4, 4, 3. The period is dead and I killed it with my own dated prediction rather than re-fitting it. Every counter computable from the log WITHOUT SPENDING A COMMAND fails: swap presses give 2, 5, 7; two-frame commands give 4, 7, 9; commands that changed a cell give 4, 8, 10; cumulative frames give 8, 15, 20 and including RESET 9, 16, 21; entries into W1 give the 3rd and 4th of five. Not one is periodic. What survives is a WALL-CLOCK reading -- a timer ticking in real time, landing 4, 4, 3 commands apart because my thinking time is not constant -- and I hold it loosely, because it explains a drift rather than stating a law. No command ran this round, so this theorem gained no new evidence and lost none."
    [depends: the_tick_is_not_a_function_of_the_frame_and_no_guard_language_can_help  probe: passed]

  theorem the_tick_is_not_a_function_of_the_frame_and_no_guard_language_can_help "The strongest negative result in the file, and proven rather than suspected. S5 and S7 are the SAME FRAME: distinct_states = 10 over 14 states is exhausted by exactly four coincidences, S0 = S2, S5 = S7, S8 = S9, S11 = S13, and I re-derived all four from the diffs this round -- t1 then t2 undoes to S0; t6 then t7 undoes to S5; t9 changed nothing; t12 then t13 returns the widget to S11 with no row-53 change. ACTION1 pressed in S5 changed 72 cells and no meter cell; ACTION1 pressed in S7 changed 73, the extra being (53,62) 2 to 3. Same frame, same key, different successor. NO GUARD OVER THE FRAME CAN WRITE THAT, counter or not, because the two states that disagree are pixel-identical and a guard has nothing else to look at. My compiled step is a function of the frame, so it is WRONG on the meter and must stay wrong. The cost is bounded and located: 1 wrong cell from transition 7, 2 from transition 10, which is exactly what certify reported."
    [probe: passed]

  theorem the_probe_hashes_locate_the_tick_without_a_single_new_rule "From the round before this one, carried unchanged because no probe report was supplied this round and I cite only what I am shown. P-05 (ACTION2, t10) and P-07 (ACTION2, t12) fired from W1 states whose widgets are identical: my manual predicted the same hash both times and the world answered differently. Two visibly-alike starting states with different successors under one key means they were not alike, and (53,61) is the only cell that can differ. P-06 (ACTION1, t11) and P-08 (ACTION1, t13) answered identically, which says S11 = S13 and that no tick occurred at t13. A tick at t11 and nowhere else in t10-t13 entails both facts; no other placement does."
    [depends: the_period_four_clock_is_refuted_and_i_dated_the_prediction_that_died  probe: passed]

  theorem a_probe_goes_vacuous_exactly_when_the_world_ticks "Carried from last edition, still unadjudicated because no probe ran this round. P-06 was the one probe of four whose command ticked and the one probe of four with zero survivors; the other three had two survivors each. Falsifiable in one line: a vacuous probe on a command that leaves row 53 alone refutes it, and would be the first real evidence of a widget mechanism I have not stated. Its predecessor, the_vacuous_probes_were_replay_damage, was struck rather than reinterpreted when P-06 met the refutation clause I had written into it myself."
    [depends: the_probe_hashes_locate_the_tick_without_a_single_new_rule  probe: pending]

  theorem the_probe_tier_is_being_paid_in_clock_noise "Three probes reported 4.882643 bits of realised gain, which is log2(59/2) exactly, and every one was an ACTION1 or ACTION2 press in a configuration I already model to the cell. The gain is not about the widget: my replayed state has the meter cells wrong BY CONSTRUCTION, so my predicted hash cannot match, so every modelled command scores as maximally informative forever. The ranker locked onto the two keys I understand and spent four consecutive commands there; then a whole round passed in which NO COMMAND WAS PRESSED AT ALL. ACTION5 and ACTION6 remain unpressed after fourteen states and ACTION1-in-W1 remains unwitnessed after five ACTION1 presses. This is a systematic defect in what the arm can buy, not a run of bad luck, and it is why the playbook prunes any probe whose whole divergence lies on the clock frontier."
    [depends: the_tick_is_not_a_function_of_the_frame_and_no_guard_language_can_help  probe: pending]

  theorem exchange_versus_scroll_is_still_open_and_i_am_standing_where_it_can_be_asked "READING A, exchange: two 6-row slots trade images, ACTION1 and ACTION2 are the same swap, and the bar simply renders four rows in the bottom slot. READING B, scroll: a list steps by six rows, ACTION1 is one direction and ACTION2 the other, and the four-row glyph in W1's bottom is a THIRD item. Nine swap commands are observed -- A1 at t1, t6, t8, t11, t13 and A2 at t2, t7, t10, t12 -- and EVERY ACTION1 was pressed in W0 and EVERY ACTION2 in W1. ACTION1 HAS STILL NEVER FOLLOWED ACTION1, so the discriminating press is still unmade, and I am still standing in W1 where it costs one command instead of two. The evidence tilting to A: row 29 reads 5,5,3,3,5,5 at cols 11-16 and has NEVER changed in fourteen states, which a scroll window's top row should not survive -- unless the window begins at row 30, which is why this does not close the question."
    [depends: the_bar_is_six_rows_above_and_four_below_in_both_directions  probe: pending]

  theorem the_bar_is_six_rows_above_and_four_below_in_both_directions "The bar reads 3,3 / 3,3 / 2,2 / 2,2 / 3,3 / 3,3 down rows 30-35 at cols 13-14 in the top slot, and 3,3 / 3,3 / 2,2 / 2,2 down rows 36-39 in the bottom with rows 40-41 background -- re-read off the current frame again this round. Going down, the last two rows CLEAR; coming up they REGROW as 3, which is what the two k2 regrowth rules draw and what three further ACTION2 presses have witnessed without a replay complaint. The box, by contrast, renders 22 frame cells and 12 hollow cells in either slot without loss. So the swap is not an information-preserving exchange of two 6x6 windows: the bottom slot is lossy for the bar and the loss is restored from nowhere visible. Every swap since the readouts went dark has moved exactly 72 cells, the full 12x6 window, so no cell of that window is ever left standing."
    [probe: passed]

  theorem the_readout_belongs_to_the_box_so_i_have_guarded_action4_into_silence "At t1 the LIT readout travelled with the box from rows 38-39 to rows 32-33 -- twelve cells of pattern moved six rows in the step the box did -- and the current frame confirms it from the other side: in W1 the port pixels read 1 at (32,16) and 2 at (33,16), six rows above their W0 seats. So the readout is bound to the box, not to the slot, which is why every swap since t2 has moved 72 cells rather than 96: both readouts are dark, so their 24 cells agree in both configurations. ACTION4 has been pressed exactly once, in W0, where bottom_port = (38,16) is 1. Unguarded, my k4 rules would light a strip the box has left whenever they fired in W1: 24 cells drawn confidently wrong. The guard colored(bottom_port, 1) makes them fire on nothing there, so my manual is SILENT about ACTION4 in W1. That silence is a declared gap, not a claim."
    [depends: the_bar_is_six_rows_above_and_four_below_in_both_directions  probe: pending]

  theorem barcore_is_five_unrelated_things_and_the_arm_sees_only_colour "Colour 2 at frame 0 sits on the 4-cell core of the bar, the lower port pixel (39,16), four dots of the readout, and three meter cells (53,61) (53,62) (53,63). Twelve instances, one type, because the arm looks objects up by colour alone. The separators are all cells I have read: the bar core has colour 3 two rows above; the readout cores have a colour-1 dot immediately left; the port has colour 0 to its left; the frame-0 meter tip is the only instance whose rightof is off-board. No k1, k2, k3, k4 or k7 guard grounds on any meter cell in any state -- I re-checked this against every rule again this round, which is why those three cells can be wrong in replay without contaminating a single other cell, and why certify's divergence set is exactly the two cells I named."
    [depends: the_tick_is_not_a_function_of_the_frame_and_no_guard_language_can_help  probe: passed]

  theorem the_swap_rules_are_forty_and_constraint_three_is_still_failed "One law -- take the colour of the cell six away -- is forty rules. recolored takes an INTEGER LITERAL, so a target colour cannot be read out of a cell and must be named, and the law splits once per source colour, per target colour, per direction, per key. THE CONCEPT DOES NOT PAY FOR ITSELF and I will not dress that up: forty rules to explain 72 cells twice over is worse than a lookup table, and I keep it only because the alternative is 96 unexplained pixels. What buys part of it back is that a TYPE IS A FRAME-0 COLOUR, so a rule's source colour already says which half of the widget its instance lives in, and only the four truncation and regrowth rules need geometry on top. The consequence that drives the playbook is unchanged: every k1 rule demands that its instance still wear its frame-0 colour, true only in W0, so the whole family is silent in W1 BY CONSTRUCTION rather than by evidence, and five ACTION1 presses have all been in W0."
    [depends: the_bar_is_six_rows_above_and_four_below_in_both_directions  probe: passed]

  theorem no_goal_section_and_this_is_a_refusal_i_can_now_price "With no goal, is_goal is False everywhere, plan never returns sat, commit never runs, and every command is a probe. I accept that and still decline, for arithmetic. Fourteen states have returned NOT_FINISHED and no other GameState has ever been seen, so no observation distinguishes a win. The pos form is dead: nothing here moves, every rule is a recolour, and cegis_miner refuses every track for exactly that reason. That leaves counts, and the count that LOOKS like progress cannot be written: the meter fills row 53 from the right, so the natural goal is the meter full, but the un-ticked meter cells have never changed, which makes them BOARD rather than instances, so count(BarCore, color = 3) can never exceed 12 and 9 of those 12 are widget cells with nothing to do with the meter. The goal language cannot name a cell that is not yet an object. Logged as E-02. Every other count I can write names a configuration, and count(BarCore, color = 3) = 3 IS TRUE RIGHT NOW. A false goal converts a probe budget into a confident wrong plan, which is strictly worse than silence. WHAT ENDS THIS IS AN OBSERVATION: a GameState other than NOT_FINISHED, or any cell outside rows 30-41 and row 53 changing at all."
    [depends: the_probe_tier_is_being_paid_in_clock_noise  probe: pending]

  theorem the_silences_i_assert_and_which_of_them_are_forged "The compiled step is total, so where nothing fires I assert identity in the same voice I use for what I watched. Audit at S13 = W1, both readouts blank. ACTION2: fully predicted, 72 cells, witnessed here four times, the one action my manual draws in this configuration. ACTION3: witnessed inert here at t9. ACTION7: entailed inert by k3's watched twin, unwitnessed in W1, and I believe it. ACTION1: STILL PREDICTED SILENT ON ZERO WITNESSES, and this remains my largest forgery -- 20 rules and one structural reading ride on it, and the silence is an artefact of every k1 guard demanding a frame-0 colour, so it is a property of my rule-writing rather than a claim about the world. I expect to be wrong and I want to be. ACTION4: predicted silent because bottom_port is 5 here; a declared gap chosen over a wrong drawing. ACTION5, ACTION6: predicted silent, never pressed, no witness of any kind. And every one of these omits the meter: whichever key is pressed, (53,60) may turn 3 on it and I cannot draw that. A ranker prices a predicted identity at zero and pays 4.88 bits for the clock cells, so both effects push the same way -- THE COMMANDS I MOST NEED ARE THE ONES THE RANKER WILL NEVER BUY."
    [depends: exchange_versus_scroll_is_still_open_and_i_am_standing_where_it_can_be_asked, the_probe_tier_is_being_paid_in_clock_noise  probe: pending]

  theorem what_lies_outside_the_widget "Full-frame responsibility means describing the 3997 constant cells, not just naming them board, and certify agrees at 0 of 4096 unexplained. A colour-4 panel fills rows 29-41 from col 17 to col 46 and carries a 4x4 block of colour 14 at rows 31-34, cols 42-45 -- the only colour-14 anywhere and the only structure on the panel. Both readouts are cut into that panel's left edge, which is why connected_components(4) cannot separate them and why every mdl_segmenter blob is a 13x36 slab. Row 29 shows 5,5,3,3,5,5 at cols 11-16 and has never changed in fourteen states: the bar reads seven rows tall on screen while only six of it is alive. Rows 42-52 are background across the window, which is what lets every bottom-half rule test six rows down without a wall test. Row 53 is the meter: colour 2 from col 10 to col 60, colour 3 at cols 61, 62, 63, re-read off the current frame. Row 54 is a solid colour-4 rule. Colours 8 and 9 appear in colours_seen and on no dynamic cell, so they sit on the board outside this window and have never moved."
    [probe: pending]

  theorem what_the_engines_gave_me "The candidate excerpt supplied this round is cegis_miner and nothing else, and it is the SAME refusal profile as last round: every track either refused because the transition narrates vanish rather than move, or refused because the object is absent at frame 0, or mined to NoSeparatingGuard on transition 1 or 2. I take NO structure from it and I accept its verdict as the strongest negative result available here -- THIS WORLD DOES NOT NARRATE AS ONE MOVER, and a miner built for movers is right to refuse rather than invent one. The 2106-row stream contains no named object and no rule I can check. The honest accounting is that the engines contributed nothing to this edition, and since no command was pressed either, the only contributions this round are my own recount and my own rejected repair."
    [probe: passed]

  theorem what_i_predict_before_i_see_it "Written so it can cost me, as one of these already has. CERTIFY, next run, unchanged if no command is pressed: 7 of 13 transitions replay exactly, first divergence t=7, single cell (53,62) manual 2 world 3, transitions 10-12 diverging by TWO cells inherited not newly earned, responsibility 0 of 4096, 0 clashes. STATE: S13 = W1, box top, bar four rows bottom, both readouts blank, three meter cells lit. ACTION1 HERE: my manual says nothing changes; I say that is false, and I name the outcomes in advance -- 72 cells at rows 30-41 cols 11-16 returning W0 exactly means exchange and twenty rules generalise by symmetry, any configuration never seen before means scroll and my word_table is a two-item special case, and genuine silence would be the most surprising result of the run. ACTION2 HERE: exactly 72 cells, no readout cell, no row-53 cell. ACTION4 HERE: my manual says nothing changes; I expect the twelve cells at rows 32-33 cols 17-22 to light instead. ACTION5, ACTION6: I predict only that whichever is pressed produces the largest single addition to this manual available. THE METER: I NAME NO COMMAND INDEX, because I was punished for naming one. I predict (53,60) turns 3 within the next five commands ACTUALLY PRESSED -- a round with no commands cannot adjudicate it and this round did not -- that it does so under whatever key happens to be pressed including an inert one, and that the intervals continue to vary."
    [depends: the_silences_i_assert_and_which_of_them_are_forged, no_goal_section_and_this_is_a_refusal_i_can_now_price  probe: pending]
```

## The playbook as it stands

```
# playbook.dsl -- what to buy with the next command, not a route.
#
# STATE: fifteen entries, fourteen commands (RESET, A1, A2, A3, A4, A7, A1,
# A2, A1, A3, A2, A1, A2, A1). I am in W1: hollow box in the TOP slot, bar
# four rows in the BOTTOM slot (36-39, rows 40-41 background), BOTH readouts
# blank, (53,61) (53,62) (53,63) all colour 3. 99 cells have ever changed; 96
# are the widget and 3 are the meter.
#
# WHAT CHANGED THIS ROUND: NO COMMAND WAS PRESSED.
#   Every store number is identical to last round -- states 14, steps 14,
#   dynamic_cells 99, constant_cells 3997, distinct_states 10. The round was
#   spent re-certifying a manual that already forecast its own certify report.
#   That is the second failure mode this playbook now has to defend against.
#   Jaw one made the ranker re-press the keys I model; jaw two made it press
#   nothing at all. Both cost the same thing: the ONE question that only this
#   configuration can ask is still unasked, three rounds running.
#
# WHAT THE ROUND DID PRODUCE, WITHOUT SPENDING A COMMAND
#   * The certify report was predicted five for five, including the prediction
#     of my own permanent failure. The divergence set is closed: no unpriced
#     cell diverged anywhere in 13 transitions.
#   * All forty coverage figures re-derived by hand. Every type's k1 rules and
#     k2 rules each partition its instances exactly; the ONLY deficit is
#     BarCore 9 of 12, and those 3 are the meter. 96 of 99 covered both ways,
#     and 96 is the largest diff the world has ever produced.
#   * The one repair the mismatch invites -- meter propagates left when its
#     right neighbour is 3 -- was computed and REFUSED: it fires three
#     commands early, it does not reduce the wrong-cell total, and it walks
#     left into cells that are still board, unbounded. Arithmetic in the
#     manual.
#
# THE QUESTION THAT ONLY THIS CONFIGURATION CAN ASK -- UNCHANGED
#   ACTION1 has been pressed FIVE times and every one was in W0. ACTION2 four
#   times, every one in W1. ACTION1 HAS NEVER FOLLOWED ACTION1. Exchange and
#   scroll are both alive; row 29 never changing is evidence against scroll
#   and does not close it. In W1 one ACTION1 splits them: exchange returns W0
#   exactly, scroll shows a configuration never seen, silence would be the
#   most surprising outcome available. Any command that leaves W1 makes the
#   question cost two. I am in W1 now, and I have been in W1 for two rounds.
#
# THE TRAP THIS PLAYBOOK EXISTS TO DEFEAT, NOW WITH A THIRD JAW
#   Jaw one: every k1 rule demands its instance still wear its frame-0 colour,
#   true only in W0, so my silence on ACTION1-in-W1 is an artefact of rule
#   syntax, and a ranker prices a predicted identity at ZERO.
#   Jaw two: the clock makes every command I DO model score 4.88 bits.
#   Jaw three: a manual that correctly forecasts its own mismatch produces a
#   surprise report every round WITHOUT a command being pressed, and that
#   surprise can consume the round. A priced divergence is not news.
#
# WHAT IS GENUINELY UNKNOWN
#   * ACTION5 and ACTION6: never pressed in fifteen entries. Zero constraint.
#   * ACTION1 in W1, ACTION2 in W0, ACTION4 in W1: silences with no witness.
#   * The meter's driver. Not a function of the frame -- two identical frames
#     disagree under the same key -- and not periodic in any count I can do.
#     It rides free on every command; it costs nothing to watch and must never
#     be paid for.
#   * The win condition. No GameState but NOT_FINISHED in fourteen states.
#     The goal language cannot name the un-ticked meter cells because they are
#     still board. The plan tier's silence is a true report of my ignorance.
#
# PRICES ADVERTISED IN ADVANCE, SO A REFUTATION ON THEM IMPLICATES NOTHING
#   * (53,62) is wrong in replay from transition 7 and (53,61) from
#     transition 10, permanently. Row-53 divergences buy nothing.
#   * ACTION1 here is predicted SILENT and I expect that to be wrong.
#   * ACTION4 here is predicted SILENT by a guard I added on purpose.
#   * ACTION2 here is predicted to the cell and repeats t7, t10 and t12.
#   * ACTION3 and ACTION7 here are predicted silent, ACTION3 witnessed silent.
#
# THE RANKED LIST -- UNCHANGED, BECAUSE NOTHING WAS OBSERVED THAT COULD
# CHANGE IT, AND CHANGING IT ANYWAY WOULD BE INVENTION
# 1. ACTION1, HERE, IN W1. Splits exchange from scroll, tests the largest
#    forged silence in the manual (20 rules, now known to cover 96 of 99
#    cells), askable only from where I am standing, three legible outcomes.
#    Unbought for three rounds.
# 2. ACTION5 or ACTION6. Never pressed in fifteen entries. Any outcome is the
#    largest single addition available -- including nothing, which after t9 I
#    know how to read -- and the cheapest place a win condition could come
#    from.
# 3. ACTION4, HERE. Tests the guard and the readout-follows-box reading in one
#    press, and relights the readout so the readout rules can be re-witnessed
#    in the other configuration.
# 4. The meter is checked for free in the raw diff of whatever is pressed.
#    Never spend a command on it.
#
# WHAT NOT TO PRESS, AND WHAT NOT TO DO INSTEAD OF PRESSING
#   ACTION2 here: drawn to the cell, witnessed four times, bits manufactured
#   by row 53. ACTION1 in W0: same, five witnesses. ACTION3 here: witnessed
#   inert in this exact state. ACTION7 here: entailed inert by a watched twin.
#   Anything chosen because the report says 4.88 bits: that is the clock.
#   AND: do not spend a round on certification alone. A surprise whose cells
#   the previous edition named by index is not a reason to re-open the manual.

order     press_something_rather_than_recertify_a_manual_that_forecast_itself [proof: lean]
order     spend_a_probe_only_the_current_state_can_ask_before_one_askable_anywhere [proof: lean]
order     press_an_action_never_pressed_before_repressing_a_modelled_one    [proof: lean]
order     press_a_modelled_action_in_a_configuration_it_was_never_pressed_in [proof: lean]
order     test_a_silence_that_rests_on_no_witness_before_one_that_is_entailed [proof: lean]
order     test_a_silence_that_is_an_artefact_of_rule_syntax_before_any_other [proof: lean]
order     override_a_ranker_that_prices_every_predicted_identity_at_zero    [proof: lean]
order     discount_gain_earned_only_on_a_cell_the_manual_declared_undrawable [proof: lean]
order     recompute_reported_bits_from_survivor_counts_before_trusting_them [proof: lean]
order     suspect_the_scoring_channel_when_one_key_wins_four_rounds_running [proof: lean]
order     prefer_a_probe_with_three_distinct_legible_outcomes_over_one_with_two [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired   [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance                [proof: lean]
order     answer_a_priced_surprise_with_a_stated_refusal_and_arithmetic     [proof: lean]
order     sum_the_wrong_cells_a_repair_would_cost_before_adopting_it        [proof: lean]
order     add_no_rule_in_a_round_that_bought_no_new_observation             [proof: lean]
order     verify_what_a_recount_can_settle_before_asking_the_world          [proof: lean]
order     date_a_prediction_by_index_so_a_wrong_period_can_be_killed        [proof: lean]
order     kill_a_fitted_period_the_moment_one_interval_breaks_it            [proof: lean]
order     test_every_counter_computable_from_the_log_before_spending_a_command [proof: lean]
order     prove_a_quantity_is_not_a_function_of_the_frame_before_guessing_its_guard [proof: lean]
order     find_two_identical_frames_with_different_successors_before_adding_a_rule [proof: lean]
order     honour_the_refutation_clause_you_wrote_into_your_own_theorem      [proof: lean]
order     strike_a_refuted_theorem_rather_than_reinterpret_it               [proof: lean]
order     count_a_coverage_figure_before_writing_it_down                    [proof: lean]
order     check_each_types_coverages_sum_to_its_instance_count              [proof: lean]
order     recount_a_state_census_against_the_store_before_drawing_from_it   [proof: lean]
order     let_a_new_dynamic_cell_join_the_type_its_frame_zero_colour_names  [proof: lean]
order     read_a_never_changing_row_as_evidence_about_structure             [proof: lean]
order     guard_a_rule_into_silence_before_letting_it_draw_an_unwitnessed_state [proof: lean]
order     rename_a_rule_that_survives_only_as_a_replay_patch                [proof: lean]
order     refuse_a_patch_that_buys_one_right_cell_with_three_wrong_ones     [proof: lean]
order     separate_same_coloured_roles_by_a_cell_you_have_actually_read     [proof: lean]
order     cite_only_engine_reports_that_were_actually_supplied_this_round   [proof: lean]
order     buy_the_observation_that_makes_a_goal_writable_before_writing_one [proof: lean]
order     refuse_a_goal_no_observation_distinguishes_and_say_so_out_loud    [proof: lean]
order     emit_every_required_block_before_polishing_any_of_them            [proof: lean]

prune     rule_proposed_with_zero_witnesses_of_any_kind => dead             [proof: lean]
prune     rule_added_in_a_round_whose_store_counts_did_not_move => dead     [proof: lean]
prune     rule_over_a_quantity_shown_not_to_be_a_function_of_the_frame => dead [proof: lean]
prune     repair_that_does_not_reduce_total_wrong_cell_transitions => dead  [proof: lean]
prune     repair_whose_error_walks_into_cells_that_are_still_board => dead  [proof: lean]
prune     rule_that_would_fire_on_every_command_to_draw_a_cell_that_moves_on_one [proof: lean]
prune     rule_that_would_forge_the_reverse_direction_of_an_unobserved_press => dead [proof: lean]
prune     guard_conjunct_with_no_negative_witness_and_no_explained_pixel => dead [proof: lean]
prune     period_fitted_to_two_ticks_and_broken_by_a_third => dead          [proof: lean]
prune     counter_that_fails_on_any_tick_already_in_the_log => dead         [proof: lean]
prune     divergence_lies_only_on_the_meter_frontier => dead                [proof: lean]
prune     divergence_a_later_transition_only_inherited_from_an_earlier_one => dead [proof: lean]
prune     divergence_the_previous_edition_named_by_cell_and_by_command => dead [proof: lean]
prune     probe_whose_reported_bits_are_all_earned_on_undrawable_cells => dead [proof: lean]
prune     probe_that_repeats_a_key_in_a_configuration_already_probed_twice => dead [proof: lean]
prune     repeats_a_key_whose_inertness_here_is_entailed_by_witnessed_rules => dead [proof: lean]
prune     repeats_a_key_already_watched_doing_nothing_in_this_exact_state => dead [proof: lean]
prune     repeats_a_transition_already_witnessed_from_an_identical_frame => dead [proof: lean]
prune     ranked_only_because_the_manual_predicts_the_most_pixels => dead   [proof: lean]
prune     leaves_the_only_configuration_that_can_ask_the_open_question => dead [proof: lean]
prune     every_rule_it_would_witness_is_already_at_full_coverage => dead   [proof: lean]
prune     goal_clause_over_a_cell_that_is_still_board => dead               [proof: lean]
prune     goal_that_is_already_true_at_the_current_state => dead            [proof: lean]
prune     goal_satisfiable_without_leaving_the_two_widget_configurations => dead [proof: lean]
prune     goal_no_observed_gamestate_could_have_distinguished => dead       [proof: lean]

heuristic actions_of_the_alphabet_never_yet_pressed                         [admissible: lean]
heuristic configurations_in_which_a_known_key_has_never_been_pressed        [admissible: lean]
heuristic silences_of_the_manual_that_rest_on_no_witness                    [admissible: lean]
heuristic silences_that_follow_from_rule_syntax_rather_than_from_evidence   [admissible: lean]
heuristic structural_readings_a_single_command_could_eliminate              [admissible: lean]
heuristic rules_that_one_command_could_generalise_or_refute_together        [admissible: lean]
heuristic distinct_legible_outcomes_a_single_command_can_produce            [admissible: lean]
heuristic questions_that_only_the_present_configuration_can_ask             [admissible: lean]
heuristic pairs_of_identical_frames_with_different_successors               [admissible: lean]
heuristic duplicate_state_pairs_the_store_count_requires_and_i_have_named   [admissible: lean]
heuristic coverage_deficits_between_a_types_rules_and_its_instance_count    [admissible: lean]
heuristic repairs_whose_wrong_cell_total_i_have_actually_summed             [admissible: lean]
heuristic counters_still_fitting_every_tick_in_the_log                      [admissible: lean]
heuristic reported_bits_that_survive_deleting_the_undrawable_cells          [admissible: lean]
heuristic consecutive_rounds_in_which_no_command_was_pressed                [admissible: lean]
heuristic consecutive_commands_spent_on_a_single_already_modelled_key       [admissible: lean]
heuristic widget_configurations_never_yet_observed                          [admissible: lean]
heuristic rows_that_have_never_changed_and_constrain_a_structural_reading   [admissible: lean]
heuristic cells_outside_the_widget_a_command_could_turn_dynamic             [admissible: lean]
heuristic cells_whose_first_change_would_make_a_goal_line_writable          [admissible: lean]
heuristic gamestates_other_than_not_finished_ever_returned                  [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_advertised_prices            [admissible: lean]

prefer    any_command_at_all_over_a_second_round_of_pure_certification      [ev: 1/1 rounds]
prefer    a_command_that_splits_two_named_readings_in_one_press             [ev: 1/1 available]
prefer    a_probe_askable_only_from_the_configuration_now_showing           [ev: 1/2 configurations]
prefer    a_key_never_pressed_in_any_state                                  [ev: 2/7 keys]
prefer    a_key_never_pressed_in_the_configuration_now_showing              [ev: 3/5 pressed keys]
prefer    a_command_that_tests_twenty_rules_at_once                         [ev: 2/2 available]
prefer    a_command_whose_outcome_the_manual_cannot_already_hash            [ev: 4/4 last probes failed this]
prefer    a_command_that_would_turn_a_cell_outside_the_widget_dynamic       [ev: 3/15 entries]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                  [ev: 14/14 diffs]
prefer    a_command_that_would_produce_a_third_widget_configuration         [ev: 0/15 entries so far]
prefer    a_command_that_could_return_a_gamestate_never_yet_seen            [ev: 0/15 entries so far]
```

## Why you are being called: the surprises that fired

### replay_mismatch (empirical family -> theory.dsl)

replay diverges at t=7 (frame_mismatch)

```json
{
 "arc_action": "ACTION1",
 "cells": [
  {
   "cell": [
    53,
    62
   ],
   "manual_says": 2,
   "world_says": 3
  }
 ],
 "cells_wrong": 1,
 "kind": "frame_mismatch",
 "t": 7
}
```

### heuristic_miss (computational family -> playbook.dsl)

the manual states no winning condition, so `is_goal` is `False` everywhere and no search can succeed. This is a gap in the manual, NOT a proof that the level is unsolvable -- constraint 6 forbids reading a failed search as an unsolvability claim. Until a `goal` is stated the plan tier cannot return `sat`, `commit` never runs, and every action this arm spends is a probe rather than an attempt to win. Declaring the winning condition is the highest-value edit available to the playbook.

```json
{
 "book_to_edit": "playbook.dsl",
 "consequence": "plan never returns sat; commit never runs; no level can be completed",
 "playbook_token": "559a65436a47af3b",
 "status": "no_goal_declared"
}
```

### probe_refutation (empirical family -> theory.dsl)

THE FRONTIER DID NOT CONTAIN THE WORLD: all 59 hypotheses were refuted, including `inert` (nothing happens) and the manual itself, which predicted '05615f3d5f835100' against the world's 'd2c8aa05e38a2da7'. No hypothesis survives, so this probe eliminated nothing and its realised information gain is 0.0 bits against the 1.925 bits the design expected. The manual needs a mechanism it does not currently state -- deleting one of its rules cannot reach this observation.

```json
{
 "action": 2,
 "expected_bits": 1.925238501883,
 "frontier_vacuous": true,
 "hypothesis_space": "every hypothesis is the manual or an ablation of it, plus `inert`",
 "information_gain_bits": 0.0,
 "manual_predicted": "05615f3d5f835100",
 "n_hypotheses": 59,
 "n_survivors": 0,
 "observed": "d2c8aa05e38a2da7",
 "probe_id": "P-09",
 "vacuous_streak": 1
}
```

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted 'a2785e8b6038ce0d', the world answered '6ff9d480d475e60e'

```json
{
 "action": 1,
 "expected_bits": 1.925238501883,
 "frontier_vacuous": false,
 "hypothesis_space": "every hypothesis is the manual or an ablation of it, plus `inert`",
 "information_gain_bits": 4.882643,
 "manual_predicted": "a2785e8b6038ce0d",
 "n_hypotheses": 59,
 "n_survivors": 2,
 "observed": "6ff9d480d475e60e",
 "probe_id": "P-10",
 "vacuous_streak": 0
}
```

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted '05615f3d5f835100', the world answered 'd2c8aa05e38a2da7'

```json
{
 "action": 2,
 "expected_bits": 1.925238501883,
 "frontier_vacuous": false,
 "hypothesis_space": "every hypothesis is the manual or an ablation of it, plus `inert`",
 "information_gain_bits": 4.882643,
 "manual_predicted": "05615f3d5f835100",
 "n_hypotheses": 59,
 "n_survivors": 2,
 "observed": "d2c8aa05e38a2da7",
 "probe_id": "P-11",
 "vacuous_streak": 0
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
  "arc_action": "ACTION1",
  "cells": [
   {
    "cell": [
     53,
     62
    ],
    "manual_says": 2,
    "world_says": 3
   }
  ],
  "cells_wrong": 1,
  "kind": "frame_mismatch",
  "t": 7
 },
 "proof_layer_available": false,
 "replay": {
  "detail": "7/13 transitions replay exactly",
  "matched": 7,
  "ok": false,
  "transitions": 13
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
  "detail": "no (state, action) among 14 x 5 admitted two rules, and all 70 pairs were adjudicated -- no call to `step` raised",
  "n_clashes": 0,
  "ok": true,
  "pairs_checked": 70,
  "pairs_nominal": 70,
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
# theory.dsl -- seventh edition.
#
# WHAT THIS ROUND BOUGHT: FOUR COMMANDS, AND ONE LAW I CAN PROVE BUT CANNOT
# COMPILE. The store moved for the first time in three rounds: states 14->18,
# steps 14->18, distinct_states 10->13, dynamic_cells 99->101,
# cells_needing_an_owner 75->77, constant_cells 3997->3995. The four commands
# are t14 ACTION2, t15 ACTION1, t16 ACTION2, t17 ACTION4. Two new cells joined
# the dynamic set, (53,60) at t14 and (53,59) at t17, and both are meter cells.
#
# 1. THE METER IS A SIX-FRAME CLOCK. THE ARITHMETIC IS EXACT AND IT IS 5/5.
#    Cumulative frames returned, counting the RESET frame: t1..t17 =
#    3,5,7,9,10,12,14,16,17,19,21,23,25,27,29,31,33. The five ticks are at
#    t4 (9), t8 (16), t11 (21), t14 (27), t17 (33). The thresholds 9, 15, 21,
#    27, 33 are 9 + 6k, and each tick lands on the FIRST command whose
#    cumulative reaches or passes its threshold -- t3 stands at 7 < 9, t7 at
#    14 < 15, t10 at 19 < 21, t13 at 25 < 27, t16 at 31 < 33. Five ticks, two
#    parameters, no residual. The command-count reading (intervals 4,3,3,3)
#    and the wall-clock reading are both DEAD as exact laws: the frame reading
#    explains why the interval was 4 across t4-t8 (t5 returned ONE frame) and
#    why it was still 3 across t8-t11 despite t9 also returning one (the
#    counter is absolute, so t8 overshot its threshold by 1 and carried it).
#    See the_meter_is_an_absolute_six_frame_counter.
#
# 2. AND I STILL CANNOT WRITE IT AS A RULE, WHICH IS THE POINT. The counter is
#    HIDDEN STATE: it is not any function of the frame, and I re-proved that
#    this round with a fresh witness pair -- S11 = S13 exactly, ACTION2 from
#    S11 (t12) did not tick and ACTION2 from S13 (t14) did. The guard language
#    has no counter, no history and no frame-count term, so the law lives in
#    `laws:` and my replay stays wrong on the meter FOREVER, by construction
#    and now by a mechanism I can name. Logged as E-04.
#
# 3. MY STATE RECONSTRUCTION IS CONFIRMED BY A NUMBER I DID NOT FIT. I listed
#    the five duplicate pairs the widget parity and the meter force -- S2=S0,
#    S7=S5, S9=S8, S13=S11, S16=S14 -- and 18 - 5 = 13 = distinct_states
#    exactly. The census is confirmed twice over the same way: 24+8+14+12+22+
#    12+9 = 101 = dynamic_cells, and 101-24 = 77 = cells_needing_an_owner.
#
# 4. THE WORLD HAS COME BACK TO ITS OPENING POSITION. S17 is S0 in every
#    widget cell -- box in the BOTTOM slot rows 36-41, bar in the TOP slot
#    rows 30-35, bottom readout LIT, top readout dark -- and differs from it
#    only in five meter cells. Seventeen commands have moved nothing that
#    persists. There is still no progress variable anywhere in the widget, and
#    that is the strongest thing I can say about the goal.
#
# 5. THE MANUAL DREW t17 CORRECTLY AND I SAID SO IN ADVANCE. k4_dot_lights and
#    k4_core_lights fired on exactly the twelve readout cells, 8 to colour 1
#    and 4 to colour 2, because bottom_port (38,16) reads 1 in W0. Second
#    witness for those two rules; the guard I added on purpose held.
#
# WHERE I AM. S17 = W0, readout LIT, five meter cells lit, seventeen commands
# since RESET. The next swap will therefore move 96 cells, not 72 -- the first
# 96-cell diff since t2.
#
# WHAT I STILL HAVE NOT SEEN AFTER EIGHTEEN STATES: ACTION1 pressed in W1.
# ACTION2 pressed in W0. ACTION4 pressed in W1. ACTION5 or ACTION6 pressed at
# all. Any GameState but NOT_FINISHED. Any cell outside rows 30-41 and row 53
# changing.

semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Field    { pos: Coord, color: Int }   # arc-colour: 5  arc-instances: all
  object BarBody  { pos: Coord, color: Int }   # arc-colour: 3  arc-instances: all
  object BarCore  { pos: Coord, color: Int }   # arc-colour: 2  arc-instances: all
  object Blank    { pos: Coord, color: Int }   # arc-colour: 4  arc-instances: all
  object Frame    { pos: Coord, color: Int }   # arc-colour: 6  arc-instances: all
  object Hollow   { pos: Coord, color: Int }   # arc-colour: 0  arc-instances: all
  object Dot      { pos: Coord, color: Int }   # arc-colour: 1  arc-instances: all
  landmark bottom_port                          # arc-cell: (38, 16)
  Field   [segment: dynamic_colour_5 ev: t0-t17 compress: 24]
  BarBody [segment: dynamic_colour_3 ev: t0-t17 compress: 8]
  BarCore [segment: dynamic_colour_2 ev: t0-t17 compress: 14]
  Blank   [segment: dynamic_colour_4 ev: t0-t17 compress: 12]
  Frame   [segment: dynamic_colour_6 ev: t0-t17 compress: 22]
  Hollow  [segment: dynamic_colour_0 ev: t0-t17 compress: 12]
  Dot     [segment: dynamic_colour_1 ev: t0-t17 compress: 9]

events:
  event recolored(o, c)

rules:
  rule k1_field_to_frame forall ?p in Field [ev: t1,t6,t8,t11,t13,t15 cov: 14/14]
    when act=key(1) and colored(?p, 5) and colored(below(below(below(below(below(below(?p)))))), 6) then recolored(?p, 6)

  rule k1_field_to_hollow forall ?p in Field [ev: t1,t6,t8,t11,t13,t15 cov: 8/8]
    when act=key(1) and colored(?p, 5) and colored(below(below(below(below(below(below(?p)))))), 0) then recolored(?p, 0)

  rule k1_field_to_dot forall ?p in Field [ev: t1,t6,t8,t11,t13,t15 cov: 1/1]
    when act=key(1) and colored(?p, 5) and colored(below(below(below(below(below(below(?p)))))), 1) then recolored(?p, 1)

  rule k1_field_to_core forall ?p in Field [ev: t1,t6,t8,t11,t13,t15 cov: 1/1]
    when act=key(1) and colored(?p, 5) and colored(below(below(below(below(below(below(?p)))))), 2) then recolored(?p, 2)

  rule k1_bar_to_frame forall ?p in BarBody [ev: t1,t6,t8,t11,t13,t15 cov: 4/4]
    when act=key(1) and colored(?p, 3) and colored(below(below(below(below(below(below(?p)))))), 6) then recolored(?p, 6)

  rule k1_bar_to_hollow forall ?p in BarBody [ev: t1,t6,t8,t11,t13,t15 cov: 4/4]
    when act=key(1) and colored(?p, 3) and colored(below(below(below(below(below(below(?p)))))), 0) then recolored(?p, 0)

  rule k1_core_to_frame forall ?p in BarCore [ev: t1,t6,t8,t11,t13,t15 cov: 4/4]
    when act=key(1) and colored(?p, 2) and colored(above(above(?p)), 3) and colored(below(below(below(below(below(below(?p)))))), 6) then recolored(?p, 6)

  rule k1_blank_to_dot forall ?p in Blank [ev: t1 cov: 8/8]
    when act=key(1) and colored(?p, 4) and colored(below(below(below(below(below(below(?p)))))), 1) then recolored(?p, 1)

  rule k1_blank_to_core forall ?p in Blank [ev: t1 cov: 4/4]
    when act=key(1) and colored(?p, 4) and colored(below(below(below(below(below(below(?p)))))), 2) then recolored(?p, 2)

  rule k1_frame_to_field forall ?p in Frame [ev: t1,t6,t8,t11,t13,t15 cov: 14/14]
    when act=key(1) and colored(?p, 6) and colored(above(above(above(above(above(above(?p)))))), 5) then recolored(?p, 5)

  rule k1_frame_to_bar forall ?p in Frame [ev: t1,t6,t8,t11,t13,t15 cov: 2/2]
    when act=key(1) and colored(?p, 6) and colored(above(above(?p)), 3) and colored(above(above(above(above(above(above(?p)))))), 3) then recolored(?p, 3)

  rule k1_frame_clears forall ?p in Frame [ev: t1,t6,t8,t11,t13,t15 cov: 2/2]
    when act=key(1) and colored(?p, 6) and colored(above(above(?p)), 6) and colored(above(above(above(above(above(above(?p)))))), 3) then recolored(?p, 5)

  rule k1_frame_to_core forall ?p in Frame [ev: t1,t6,t8,t11,t13,t15 cov: 4/4]
    when act=key(1) and colored(?p, 6) and colored(above(above(above(above(above(above(?p)))))), 2) then recolored(?p, 2)

  rule k1_hollow_to_field forall ?p in Hollow [ev: t1,t6,t8,t11,t13,t15 cov: 8/8]
    when act=key(1) and colored(?p, 0) and colored(above(above(above(above(above(above(?p)))))), 5) then recolored(?p, 5)

  rule k1_hollow_to_bar forall ?p in Hollow [ev: t1,t6,t8,t11,t13,t15 cov: 2/2]
    when act=key(1) and colored(?p, 0) and colored(above(above(?p)), 3) and colored(above(above(above(above(above(above(?p)))))), 3) then recolored(?p, 3)

  rule k1_hollow_clears forall ?p in Hollow [ev: t1,t6,t8,t11,t13,t15 cov: 2/2]
    when act=key(1) and colored(?p, 0) and colored(above(above(?p)), 6) and colored(above(above(above(above(above(above(?p)))))), 3) then recolored(?p, 5)

  rule k1_dot_to_field forall ?p in Dot [ev: t1,t6,t8,t11,t13,t15 cov: 1/1]
    when act=key(1) and colored(?p, 1) and colored(above(above(above(above(above(above(?p)))))), 5) then recolored(?p, 5)

  rule k1_dot_to_blank forall ?p in Dot [ev: t1 cov: 8/8]
    when act=key(1) and colored(?p, 1) and colored(above(above(above(above(above(above(?p)))))), 4) then recolored(?p, 4)

  rule k1_core_to_field forall ?p in BarCore [ev: t1,t6,t8,t11,t13,t15 cov: 1/1]
    when act=key(1) and colored(?p, 2) and colored(leftof(?p), 0) and colored(above(above(above(above(above(above(?p)))))), 5) then recolored(?p, 5)

  rule k1_core_to_blank forall ?p in BarCore [ev: t1 cov: 4/4]
    when act=key(1) and colored(?p, 2) and colored(leftof(?p), 1) and colored(above(above(above(above(above(above(?p)))))), 4) then recolored(?p, 4)

  rule k2_field_from_frame forall ?p in Field [ev: t2,t7,t10,t12,t14,t16 cov: 14/14]
    when act=key(2) and colored(?p, 6) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule k2_field_from_hollow forall ?p in Field [ev: t2,t7,t10,t12,t14,t16 cov: 8/8]
    when act=key(2) and colored(?p, 0) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule k2_field_from_dot forall ?p in Field [ev: t2,t7,t10,t12,t14,t16 cov: 1/1]
    when act=key(2) and colored(?p, 1) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule k2_field_from_core forall ?p in Field [ev: t2,t7,t10,t12,t14,t16 cov: 1/1]
    when act=key(2) and colored(?p, 2) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule k2_bar_from_frame forall ?p in BarBody [ev: t2,t7,t10,t12,t14,t16 cov: 2/2]
    when act=key(2) and colored(?p, 6) and colored(below(below(below(below(below(below(?p)))))), 3) then recolored(?p, 3)

  rule k2_bar_from_hollow forall ?p in BarBody [ev: t2,t7,t10,t12,t14,t16 cov: 2/2]
    when act=key(2) and colored(?p, 0) and colored(below(below(below(below(below(below(?p)))))), 3) then recolored(?p, 3)

  rule k2_bar_regrows_from_hollow forall ?p in BarBody [ev: t2,t7,t10,t12,t14,t16 cov: 2/2]
    when act=key(2) and colored(?p, 0) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 3)

  rule k2_bar_regrows_from_frame forall ?p in BarBody [ev: t2,t7,t10,t12,t14,t16 cov: 2/2]
    when act=key(2) and colored(?p, 6) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 3)

  rule k2_core_from_frame forall ?p in BarCore [ev: t2,t7,t10,t12,t14,t16 cov: 4/4]
    when act=key(2) and colored(?p, 6) and colored(below(below(below(below(below(below(?p)))))), 2) then recolored(?p, 2)

  rule k2_blank_from_dot forall ?p in Blank [ev: t2 cov: 8/8]
    when act=key(2) and colored(?p, 1) and colored(below(below(below(below(below(below(?p)))))), 4) then recolored(?p, 4)

  rule k2_blank_from_core forall ?p in Blank [ev: t2 cov: 4/4]
    when act=key(2) and colored(?p, 2) and colored(below(below(below(below(below(below(?p)))))), 4) then recolored(?p, 4)

  rule k2_frame_from_field forall ?p in Frame [ev: t2,t7,t10,t12,t14,t16 cov: 16/16]
    when act=key(2) and colored(?p, 5) and colored(above(above(above(above(above(above(?p)))))), 6) then recolored(?p, 6)

  rule k2_frame_from_bar forall ?p in Frame [ev: t2,t7,t10,t12,t14,t16 cov: 2/2]
    when act=key(2) and colored(?p, 3) and colored(above(above(above(above(above(above(?p)))))), 6) then recolored(?p, 6)

  rule k2_frame_from_core forall ?p in Frame [ev: t2,t7,t10,t12,t14,t16 cov: 4/4]
    when act=key(2) and colored(?p, 2) and colored(above(above(above(above(above(above(?p)))))), 6) then recolored(?p, 6)

  rule k2_hollow_from_field forall ?p in Hollow [ev: t2,t7,t10,t12,t14,t16 cov: 10/10]
    when act=key(2) and colored(?p, 5) and colored(above(above(above(above(above(above(?p)))))), 0) then recolored(?p, 0)

  rule k2_hollow_from_bar forall ?p in Hollow [ev: t2,t7,t10,t12,t14,t16 cov: 2/2]
    when act=key(2) and colored(?p, 3) and colored(above(above(above(above(above(above(?p)))))), 0) then recolored(?p, 0)

  rule k2_dot_from_field forall ?p in Dot [ev: t2,t7,t10,t12,t14,t16 cov: 1/1]
    when act=key(2) and colored(?p, 5) and colored(above(above(above(above(above(above(?p)))))), 1) then recolored(?p, 1)

  rule k2_dot_from_blank forall ?p in Dot [ev: t2 cov: 8/8]
    when act=key(2) and colored(?p, 4) and colored(above(above(above(above(above(above(?p)))))), 1) then recolored(?p, 1)

  rule k2_core_from_field forall ?p in BarCore [ev: t2,t7,t10,t12,t14,t16 cov: 1/1]
    when act=key(2) and colored(?p, 5) and colored(above(above(above(above(above(above(?p)))))), 2) then recolored(?p, 2)

  rule k2_core_from_blank forall ?p in BarCore [ev: t2 cov: 4/4]
    when act=key(2) and colored(?p, 4) and colored(above(above(above(above(above(above(?p)))))), 2) then recolored(?p, 2)

  rule k3_dot_blanks forall ?s in Dot [ev: t3 cov: 8/8]
    when act=key(3) and colored(?s, 1) and colored(above(above(above(above(above(above(?s)))))), 4) then recolored(?s, 4)

  rule k3_core_blanks forall ?s in BarCore [ev: t3 cov: 4/4]
    when act=key(3) and colored(?s, 2) and colored(leftof(?s), 1) and colored(above(above(above(above(above(above(?s)))))), 4) then recolored(?s, 4)

  rule k4_dot_lights forall ?s in Dot [ev: t4,t17 cov: 8/8]
    when act=key(4) and colored(?s, 4) and colored(bottom_port, 1) then recolored(?s, 1)

  rule k4_core_lights forall ?s in BarCore [ev: t4,t17 cov: 4/4]
    when act=key(4) and colored(?s, 4) and colored(bottom_port, 1) then recolored(?s, 2)

  rule meter_first_tick_replay_patch forall ?s in BarCore [ev: t4 cov: 1/1]
    when act=key(4) and colored(?s, 2) and rightof(?s) = wall then recolored(?s, 3)

  rule k7_dot_blanks forall ?s in Dot [ev: t5 cov: 8/8]
    when act=key(7) and colored(?s, 1) and colored(above(above(above(above(above(above(?s)))))), 4) then recolored(?s, 4)

  rule k7_core_blanks forall ?s in BarCore [ev: t5 cov: 4/4]
    when act=key(7) and colored(?s, 2) and colored(leftof(?s), 1) and colored(above(above(above(above(above(above(?s)))))), 4) then recolored(?s, 4)

laws:
  invariant field_instances count(Field) = 24 [status: census, re-read off the current frame, rows 30-35 cols 11,12,15,16]
  invariant barbody_instances count(BarBody) = 8 [status: census, rows 30,31,34,35 cols 13-14]
  invariant barcore_instances count(BarCore) = 14 [status: census, GREW BY 2 this round: 4 bar core + 1 port + 4 readout cores + 5 meter]
  invariant blank_instances count(Blank) = 12 [status: census, the dark top readout at frame 0, rows 32-33 cols 17-22]
  invariant frame_instances count(Frame) = 22 [status: census, 6+2+3+3+2+6 read down the box now standing in the BOTTOM slot rows 36-41]
  invariant hollow_instances count(Hollow) = 12 [status: census, 4+2+2+4 read down the same box]
  invariant dot_instances count(Dot) = 9 [status: census, 8 lit readout dots plus the upper port pixel (38,16)]
  invariant board_cells count(board) = 3995 [status: matches constant_cells exactly, down 2 because (53,59) and (53,60) turned dynamic]
  invariant total_owned_cells count(Field) + count(BarBody) + count(BarCore) + count(Blank) + count(Frame) + count(Hollow) + count(Dot) = 101 [status: matches dynamic_cells exactly, and 101 - 24 = 77 = cells_needing_an_owner]
  invariant meter_cells_lit count(BarCore, color = 3) = 5 [status: read off row 53 of the current frame, cols 59-63]

  theorem the_meter_is_an_absolute_six_frame_counter "THE LARGEST RESULT IN THIS FILE AND IT IS ARITHMETIC, NOT A GUESS. Let F(t) be the total number of grids the world has returned up to and including command t, counting the RESET frame: F = 3,5,7,9,10,12,14,16,17,19,21,23,25,27,29,31,33 for t1..t17. The five meter ticks are t4, t8, t11, t14, t17 and their F values are 9, 16, 21, 27, 33. The thresholds 9, 15, 21, 27, 33 are exactly 9 + 6k, and every tick is the FIRST command whose F reaches or passes its threshold: t3 stands at 7 < 9, t7 at 14 < 15, t10 at 19 < 21, t13 at 25 < 27, t16 at 31 < 33. Five ticks, two parameters, zero residual. THE COUNTER IS ABSOLUTE, NOT RESET ON TICK -- that is what explains the one interval every other reading fails on: t8 overshot threshold 15 by one frame, so only five further frames were needed for threshold 21 and the interval came out three commands long even though t9 returned a single frame. It also explains the drift my earlier editions mistook for a wall clock: a command returning two frames costs two clock units and one returning one frame costs one, so the interval in COMMANDS is 3 when every command is a swap and 4 when a one-frame command intervenes. Period-4-in-commands died two editions ago; period-3-in-commands and the wall clock die here. DATED PREDICTION, MADE BEFORE THE NEXT COMMAND: the next tick lights (53,58) and lands on the first command whose F reaches 39. If the next three commands each return two frames that is t20 and the command-count reading agrees; if exactly one of them returns a single frame -- ACTION7 returned one at t5, an inert ACTION3 returned one at t9 -- the frame clock says t21 and the command reading still says t20, and one cheap command decides between them."
    [depends: the_tick_is_not_a_function_of_the_frame_and_no_guard_language_can_help  probe: pending]

  theorem the_clock_cannot_be_compiled_and_this_is_a_language_limit_not_an_ignorance "I now know the mechanism and STILL cannot write a rule for it, and I want that stated plainly rather than smuggled into a guard. The counter is hidden state: it lives outside the grid, it is incremented by the world's own frame production, and the guard language admits only act=, free, colored, adjacent, comparisons of values, and cell = wall -- there is no counter term, no history term, no frames-returned term, and `recolored` takes an integer literal. So the honest manual predicts the widget exactly and the meter never, and my replay error is not a defect I can repair but a projection of a two-variable world onto a one-variable language. Logged as E-04. The consequence is quantified in the next theorem and it is a growing but strictly bounded and strictly located cost."
    [depends: the_meter_is_an_absolute_six_frame_counter  probe: passed]

  theorem the_replay_mismatch_is_answered_by_refusal_and_the_arithmetic_is_now_larger "The surprise fires again at certify t=7, ACTION1, one cell (53,62), manual 2 world 3 -- the cell and the transition index my fifth edition named in advance. It is the same divergence, inherited nine more times, and I refuse to repair it again. Current cost, exactly: 17 transitions, the first seven replay perfectly, and certify t=7,8,9 are wrong by one cell, t=10,11,12 by two, t=13,14,15 by three, t=16 by four -- 22 wrong-cell-transitions in total, growing by one cell every six frames and by nothing else, because NO RULE IN THIS FILE GROUNDS ON A METER CELL in any state. TWO REPAIRS WERE COMPUTED AND BOTH ARE REFUSED. (a) Propagation, a colour-2 BarCore whose right neighbour is 3 becomes 3: under cascade single_frame it walks one cell left per command, so by t17 it would have lit about thirteen cells against the world's five, and every extra cell it lights is still BOARD -- a confident wrong drawing on a cell that has never changed. (b) A second ACTION4-keyed patch, colour 2 with a colour-3 right neighbour under key(4), which would have drawn t17's tick exactly right and buys one transition. I refuse it because it fits a 2-of-2 coincidence: both ACTION4 presses ticked, but so did two ACTION1 presses and one ACTION2 press, and the frame clock explains all five while the key explains two. That patch would fire on the VERY NEXT ACTION4 press regardless of the clock, and ACTION4 is a key I intend to press again. A patch that would be wrong the moment I use it is worse than a declared gap."
    [depends: the_clock_cannot_be_compiled_and_this_is_a_language_limit_not_an_ignorance  probe: passed]

  theorem a_probe_goes_vacuous_exactly_when_the_world_ticks "PROMOTED FROM PENDING, 7 FOR 7, AND NOW WITH A MECHANISM. Of the seven probes I have been shown, P-06 (t11) and P-09 (t14) reported frontier_vacuous with zero survivors, and t11 and t14 are precisely the two commands among t10-t16 on which the meter ticked. P-05, P-07, P-08, P-10, P-11 each reported two survivors and their commands t10, t12, t13, t15, t16 each left row 53 alone. The mechanism is the previous theorem: every hypothesis on the frontier is my manual or an ablation of it, no hypothesis of mine can tick the meter, so on a ticking command the observed frame is outside the whole frontier and the probe eliminates nothing. This is a fact about my frontier, NOT about the world, and I refuse to read it as a widget mechanism. What it buys is real and free: a vacuous probe report is a TICK DETECTOR, so I can adjudicate the six-frame clock from the probe stream even when the raw diff is not in front of me."
    [depends: the_meter_is_an_absolute_six_frame_counter  probe: passed]

  theorem the_probes_that_said_the_manual_was_wrong_were_wrong_about_nothing_i_can_fix "P-10 (ACTION1, t15) and P-11 (ACTION2, t16) each reported THE MANUAL WAS WRONG at 4.882643 bits, which is log2(59/2) exactly, the same figure four earlier probes reported. P-09 and P-11 carry IDENTICAL predicted hashes and IDENTICAL observed hashes, which is itself a check on my reconstruction -- S14 and S16 are the same state, as the duplicate count requires. The divergence in every case is the meter cells my replayed state has wrong by construction, so my predicted hash cannot match no matter how perfectly I draw 96 of 101 cells, and every command I fully model will score as maximally informative forever. I therefore price these three refutations at ZERO structural content and I say so rather than editing a rule to chase them. The check that this is not an excuse: certify's cell-level report names ONE cell at the first divergence and it is a meter cell."
    [depends: a_probe_goes_vacuous_exactly_when_the_world_ticks  probe: passed]

  theorem the_five_duplicate_states_were_predicted_by_parity_and_the_store_agreed "A number I did not fit. From the widget parity, the readout state and the meter alone I list the duplicates among eighteen states: S2 = S0 (W0, readout lit, no meter cell lit), S7 = S5 (W0, dark, one lit), S9 = S8 (t9 ACTION3 changed nothing), S13 = S11 (W1, dark, three lit), S16 = S14 (W0, dark, four lit). Five coincidences, 18 - 5 = 13, and distinct_states = 13. Every element of my reconstruction -- which slot the box is in at each t, which readout is lit, and which meter cells are lit -- is loaded into that one number, and it came out right. S17 is NOT among the duplicates: it matches S0 in every widget cell but differs in five meter cells, so after seventeen commands THE WORLD IS BACK WHERE IT STARTED except for the clock."
    [probe: passed]

  theorem every_coverage_column_sums_to_its_type "Re-derived against the new instance counts. For each type the k1 rules partition its instances and so do the k2 rules: Field 14+8+1+1 = 24 both ways. Frame 14+2+2+4 = 22 going down and 16+2+4 = 22 coming up. Hollow 8+2+2 = 12 and 10+2 = 12. BarBody 4+4 = 8 and 2+2+2+2 = 8. Dot 1+8 = 9. Blank 8+4 = 12. BarCore 4+1+4 = 9 OF 14, and the deficit is now FIVE rather than three, because the two cells that turned dynamic this round are meter cells and joined BarCore by their frame-0 colour. So 96 of 101 owned cells are covered in both directions and the uncovered five are exactly the five cells no rule of mine may touch. The deficit will grow by one every six frames and it will never be anything but meter."
    [depends: the_clock_cannot_be_compiled_and_this_is_a_language_limit_not_an_ignorance  probe: passed]

  theorem the_tick_is_not_a_function_of_the_frame_and_no_guard_language_can_help "Carried, and re-witnessed this round with a fresh pair. The old witness: S5 and S7 are the same frame, ACTION1 from S5 changed 72 cells and no meter cell, ACTION1 from S7 changed 73 and the extra was (53,62). The new witness: S11 and S13 are the same frame -- both W1, both readouts dark, meter {61,62,63} -- and ACTION2 from S11 at t12 left row 53 alone while ACTION2 from S13 at t14 lit (53,60). Same frame, same key, different successor, twice, under two different keys. My compiled step is a function of the frame, so it is WRONG on the meter and must stay wrong. What changed this round is that I now know WHAT the extra variable is."
    [probe: passed]

  theorem exchange_versus_scroll_is_still_open_and_the_discriminating_press_has_moved_to_action2 "READING A, exchange: two 6-row slots trade images and ACTION1 and ACTION2 are the same involution. READING B, scroll: a list steps by six rows, ACTION1 one way and ACTION2 the other, and the four-row glyph is a third item. Eleven swaps are observed now -- ACTION1 at t1, t6, t8, t11, t13, t15 and ACTION2 at t2, t7, t10, t12, t14, t16 -- and EVERY ACTION1 was pressed in W0 and EVERY ACTION2 in W1, so ACTION1 has still never followed ACTION1 and the question is untouched after eighteen entries. I now stand in W0, so the cheap discriminating press has swapped identity: ACTION2 HERE. Exchange predicts it reproduces exactly what ACTION1 does from here; scroll predicts a configuration never seen. The evidence still tilting to A: row 29 reads 5,5,3,3,5,5 at cols 11-16 and has never changed in eighteen states. And there is a bonus this round -- the bottom readout is LIT again, so whichever swap I press moves 96 cells rather than 72 and re-witnesses the four readout-transfer rules that have stood on a single witness since t1 and t2."
    [depends: the_bar_is_six_rows_above_and_four_below_in_both_directions  probe: pending]

  theorem the_bar_is_six_rows_above_and_four_below_in_both_directions "The bar reads 3,3 / 3,3 / 2,2 / 2,2 / 3,3 / 3,3 down rows 30-35 at cols 13-14 in the top slot -- re-read off the current frame, where it is standing -- and 3,3 / 3,3 / 2,2 / 2,2 down rows 36-39 in the bottom with rows 40-41 background. Going down the last two rows CLEAR; coming up they REGROW as 3, which is what the two k2 regrowth rules draw and what six ACTION2 presses have now witnessed without a replay complaint. The box renders 22 frame cells and 12 hollow cells in either slot without loss. So the swap is not an information-preserving exchange of two 6x6 windows: the bottom slot is lossy for the bar and the loss is restored from nowhere visible."
    [probe: passed]

  theorem the_readout_belongs_to_the_box_and_action4_was_drawn_right_a_second_time "At t1 the LIT readout travelled with the box from rows 38-39 to rows 32-33, twelve cells of pattern moving six rows in the step the box did. t17 confirms the binding from the other side: ACTION4 pressed in W0, with the box in the bottom slot and bottom_port (38,16) reading 1, lit exactly the twelve cells at rows 38-39 cols 17-22 -- eight to colour 1 and four to colour 2 -- which is precisely what k4_dot_lights and k4_core_lights draw, second witness, no unpriced cell. The lit pattern is two copies of a 2x3 glyph: reading columns 17..22, (2,1)(1,1)(1,2)(2,1)(1,1)(1,2). ACTION4 IN W1 REMAINS UNPRESSED after eighteen entries. Unguarded my k4 rules would light a strip the box has left, twelve cells drawn confidently wrong; the guard colored(bottom_port, 1) makes them fire on nothing there, so my manual is SILENT about ACTION4 in W1 and that silence is a declared gap, not a claim."
    [depends: the_bar_is_six_rows_above_and_four_below_in_both_directions  probe: pending]

  theorem barcore_is_five_unrelated_things_and_the_arm_sees_only_colour "Colour 2 at frame 0 sits on the 4-cell core of the bar, the lower port pixel (39,16), four dots of the readout, and now FIVE meter cells (53,59) through (53,63). Fourteen instances, one type, because the arm looks objects up by colour alone. The separators are all cells I have read: the bar core has colour 3 two rows above, the readout cores have a colour-1 dot immediately left, the port has colour 0 to its left, and the meter cells have neither. I re-checked every rule against every meter cell again this round: no k1, k2, k3, k4 or k7 guard grounds on one in any state, which is why they can be wrong in replay without contaminating a single other cell, and why certify's divergence set is exactly the cells the clock has lit and my patch did not."
    [depends: the_tick_is_not_a_function_of_the_frame_and_no_guard_language_can_help  probe: passed]

  theorem the_swap_rules_are_forty_and_constraint_three_is_still_failed "One law -- take the colour of the cell six away -- is forty rules. recolored takes an INTEGER LITERAL, so a target colour cannot be read out of a cell and must be named, and the law splits once per source colour, per target colour, per direction, per key. THE CONCEPT DOES NOT PAY FOR ITSELF and I will not dress that up: forty rules to explain 96 cells twice over is worse than a lookup table, and I keep it only because the alternative is 96 unexplained pixels. What buys part of it back is that a TYPE IS A FRAME-0 COLOUR, so a rule's source colour already says which half of the widget its instance lives in, and only the four truncation and regrowth rules need geometry on top. The consequence that drives the playbook is unchanged and is now symmetric: every k1 rule demands its instance still wear its frame-0 colour, true only in W0, and every k2 rule demands the swapped colour, true only in W1. So twenty rules are silent in W1 and twenty in W0 BY CONSTRUCTION rather than by evidence -- and I am standing in W0, where the twenty silent ones are the k2 family."
    [depends: the_bar_is_six_rows_above_and_four_below_in_both_directions  probe: passed]

  theorem action6_may_be_a_click_and_the_colour_14_block_is_the_only_target_on_the_board "A guess I am labelling as one. Five of the seven keys have been pressed and all five act on the widget in rows 30-41; ACTION5 and ACTION6 have never been pressed in eighteen entries. In this action family a coordinate-carrying action is common, and the guard language cannot express one -- there is no way to write act=click(row, col) and no way to name an arbitrary cell without declaring a landmark for it. If one of the unpressed keys is a click, the only structure on the board that looks like a target is the 4x4 block of colour 14 at rows 31-34, cols 42-45: it is the sole appearance of colour 14 anywhere, it sits alone on the colour-4 panel, and nothing in eighteen commands has touched it. Logged as E-05. I assert nothing about what pressing it does; I assert only that this is where I would look and that my manual currently cannot draw any consequence of it."
    [probe: pending]

  theorem no_goal_section_and_the_refusal_is_now_stronger_than_it_was "The heuristic_miss is right that is_goal is False everywhere, that plan never returns sat, that commit never runs and that every command is a probe. I accept every one of those consequences and still decline, and this round gives me a new argument rather than the old one repeated. NEW: after seventeen commands the widget has returned EXACTLY to its opening configuration -- S17 equals S0 in all 96 widget cells -- so nothing I have done is cumulative and there is no monotone quantity anywhere in the widget that a goal could name. The only monotone quantity in this world is the meter, and the meter is a CLOCK driven by frames returned, not by what I press, so it is not progress; it is either decoration or a budget, and a goal over a clock is a goal over the passage of time. The old arithmetic still holds too: the un-ticked meter cells have never changed, so they are board rather than instances, and count(BarCore, color = 3) can never exceed 14 while nine of those fourteen are widget cells with nothing to do with the meter (E-02). And the thing I actually want to write -- goal gamestate != NOT_FINISHED -- has no term in the goal language at all (E-03). A false goal converts a probe budget into a confident wrong plan, which is strictly worse than silence. WHAT ENDS THIS, unchanged and now urgent: a GameState other than NOT_FINISHED, or any cell outside rows 30-41 and row 53 changing at all. Both are most likely to come from ACTION5 or ACTION6."
    [depends: the_five_duplicate_states_were_predicted_by_parity_and_the_store_agreed, action6_may_be_a_click_and_the_colour_14_block_is_the_only_target_on_the_board  probe: pending]

  theorem the_silences_i_assert_and_which_of_them_are_forged "The compiled step is total, so where nothing fires I assert identity in the same voice I use for what I watched. Audit at S17 = W0, bottom readout LIT, five meter cells lit. ACTION1: fully predicted, and this time 96 cells rather than 72 because the lit readout travels with the box -- six witnesses for the swap, one witness for the readout transfer. ACTION3: predicted to blank the twelve lit readout cells, witnessed doing exactly that at t3 in this exact configuration. ACTION7: same twelve cells, witnessed at t5. ACTION4: predicted silent here because the readout is already lit and the k4 guards demand colour 4; entailed, not forged. ACTION2 HERE: PREDICTED SILENT ON ZERO WITNESSES, and this is now my largest forgery -- twenty rules ride on it and the silence is an artefact of every k2 guard demanding a swapped colour, so it is a property of my rule-writing rather than a claim about the world. I expect to be wrong and I want to be. ACTION5, ACTION6: predicted silent, never pressed, no witness of any kind, and a silent one-frame answer would itself adjudicate the six-frame clock. And every one of these omits the meter: whichever key is pressed, (53,58) turns 3 on the command that carries the clock past 39."
    [depends: exchange_versus_scroll_is_still_open_and_the_discriminating_press_has_moved_to_action2, the_meter_is_an_absolute_six_frame_counter  probe: pending]

  theorem what_lies_outside_the_widget "Full-frame responsibility means describing the 3995 constant cells, not just naming them board, and certify agrees at 0 of 4096 unexplained. A colour-4 panel fills rows 29-41 from col 17 to col 46 and carries a 4x4 block of colour 14 at rows 31-34, cols 42-45 -- the only colour 14 anywhere and the only structure on the panel. Both readouts are cut into that panel's left edge, which is why connected_components(4) cannot separate them and why every mdl_segmenter blob is a 13x36 slab. Row 29 shows 5,5,3,3,5,5 at cols 11-16 and has never changed in eighteen states: the bar reads seven rows tall on screen while only six of it is alive. Rows 42-52 are background across the window, which is what lets every bottom-half rule test six rows down without a wall test. Row 53 is the meter: colour 2 from col 10 to col 58 and colour 3 at cols 59-63, re-read off the current frame, which is five lit cells and matches five ticks. Row 54 is a solid colour-4 rule. Colours 8 and 9 appear in colours_seen and on no dynamic cell, so they sit on the board outside this window and have never moved. The meter has 49 unlit cells left inside the dynamic window; at six frames a cell and two frames a command that is about 147 more commands, which is the only number resembling a budget that this world has ever shown me."
    [depends: the_meter_is_an_absolute_six_frame_counter  probe: pending]

  theorem what_the_engines_gave_me "The candidate excerpt supplied this round is cegis_miner and nothing else, and it is the same refusal profile for the third round running: every track either refused because the transition narrates vanish rather than move, or refused because the object is absent at frame 0, or mined to NoSeparatingGuard on transition 1 or 2. I take NO structure from it and I accept its verdict as the strongest negative result available here -- THIS WORLD DOES NOT NARRATE AS ONE MOVER, and a miner built for movers is right to refuse rather than invent one. The 2866-row stream contains no named object and no rule I can check. What the engines could not have found is the thing that made this edition: the meter law is arithmetic over the FRAME COUNTS of commands, which is not in the grid at all and is invisible to any engine that mines transitions cell by cell."
    [probe: passed]

  theorem what_i_predict_before_i_see_it "Written so it can cost me, as three of these already have. CERTIFY, next run, if no command is pressed: 7 of 17 transitions replay exactly, first divergence certify t=7 ACTION1, the single cell (53,62) manual 2 world 3, then one wrong cell at t=8 and t=9, two at t=10, t=11, t=12, three at t=13, t=14, t=15 and four at t=16, twenty-two wrong-cell-transitions in all and every one of them on row 53; responsibility 0 of 4096; 0 clashes; 90 of 90 pairs adjudicated. STATE: S17 = W0, box bottom rows 36-41, bar top rows 30-35, bottom readout LIT, top readout dark, meter cols 59-63. ACTION1 HERE: 96 cells at rows 30-41 cols 11-22, the first 96-cell diff since t2, re-witnessing the four readout-transfer rules that have stood on one witness each since t1. ACTION2 HERE: my manual says nothing changes; I say that is false and I name the outcomes in advance -- 96 cells reproducing exactly what ACTION1 does from here means exchange and twenty rules generalise by symmetry, any configuration never seen before means scroll and my word_table is a two-item special case, and genuine silence would be the most surprising result of the run. ACTION3 and ACTION7 HERE: exactly the twelve readout cells at rows 38-39 cols 17-22 go to colour 4, and ACTION7 does it in ONE frame while ACTION3 does it in two. ACTION5, ACTION6: I predict only that whichever is pressed produces the largest single addition to this manual available, and that if it is inert it returns one frame. THE METER: (53,58) turns 3 on the first command whose cumulative frame count including RESET reaches 39, which is t20 if every intervening command returns two frames and t21 if exactly one returns one; the probe report on that command will be frontier_vacuous with zero survivors; and no other cell of row 53 changes before then."
    [depends: the_meter_is_an_absolute_six_frame_counter, the_silences_i_assert_and_which_of_them_are_forged  probe: pending]
```

=== PLAYBOOK ===
```
# playbook.dsl -- what to buy with the next command, not a route.
#
# STATE: nineteen entries, eighteen commands. I am in W0 AND IT IS THE OPENING
# POSITION: box in the BOTTOM slot rows 36-41, bar in the TOP slot rows 30-35,
# bottom readout LIT at rows 38-39 cols 17-22, top readout dark. S17 equals S0
# in all 96 widget cells. The only thing seventeen commands have changed that
# persists is the meter: five cells, (53,59) through (53,63).
#
# WHAT CHANGED THIS ROUND: FOUR COMMANDS WERE BOUGHT AND THE CLOCK WAS SOLVED.
#   t14 ACTION2, t15 ACTION1, t16 ACTION2, t17 ACTION4. Every one of them was
#   a modelled key in a modelled configuration; the four together added no
#   rule. What they DID add is the fifth meter tick, and five ticks are enough
#   to solve the meter exactly:
#     THE METER ADVANCES ONE CELL EVERY SIX FRAMES OF WORLD OUTPUT.
#   Cumulative frames including RESET at the five ticks: 9, 16, 21, 27, 33,
#   against thresholds 9 + 6k, each tick landing on the first command that
#   reaches its threshold. Two parameters, five ticks, no residual. It is a
#   CLOCK, not a score: it does not care which key I press.
#
# THREE CONSEQUENCES THAT REORDER THIS BOOK
#   1. A COMMAND COSTS TWO CLOCK UNITS, A ROUND OF PURE THINKING COSTS ZERO.
#      The clock is driven by frames, not wall time, so deliberation is free
#      and commands are not. That does not license another certification-only
#      round -- it licenses spending the command on the most informative thing
#      available instead of the cheapest.
#   2. SOME COMMANDS COST HALF. ACTION7 returned ONE frame at t5 while still
#      changing twelve cells, and an inert ACTION3 returned one at t9. If the
#      meter is a budget, those are half-price commands. One witness each.
#   3. THE CLOCK IS ITS OWN EXPERIMENT AND IT IS FREE. The next tick lights
#      (53,58) at cumulative frame 39: t20 if the next three commands all
#      return two frames, t21 if exactly one returns one. That single slip
#      distinguishes the frame clock from period-3-in-commands and from a wall
#      clock, and I do not have to spend a command to get it -- I only have to
#      notice whether one of the commands I would press anyway is short.
#
# A FREE TICK DETECTOR: a probe reports frontier_vacuous with zero survivors
#   EXACTLY on the commands that tick -- P-06 at t11 and P-09 at t14 vacuous,
#   P-05, P-07, P-08, P-10, P-11 not, and their commands did not tick. 7 of 7.
#   It is a fact about my frontier, not about the world: no hypothesis of mine
#   can tick the meter, so a ticking command falls outside the whole frontier.
#   Never pay for it; always read it.
#
# THE QUESTION THAT ONLY THIS CONFIGURATION CAN ASK -- IT HAS SWAPPED KEYS
#   ACTION1 has been pressed six times, every one in W0. ACTION2 six times,
#   every one in W1. ACTION1 HAS NEVER FOLLOWED ACTION1 AND ACTION2 HAS NEVER
#   FOLLOWED ACTION2. Exchange and scroll are both alive. I stand in W0, so
#   the cheap discriminating press is now ACTION2 HERE: exchange says it does
#   exactly what ACTION1 does from here, scroll says a configuration never
#   seen, and my manual says silence -- a silence resting on twenty rules and
#   zero witnesses. BONUS THIS ROUND: the readout is lit again, so any swap
#   moves 96 cells and re-witnesses the four readout-transfer rules that have
#   stood on one witness each since t1 and t2.
#
# THE TRAP THIS PLAYBOOK EXISTS TO DEFEAT
#   Jaw one: every k1 guard demands a frame-0 colour and every k2 guard the
#   swapped one, so twenty rules are silent in W1 and twenty in W0 BY SYNTAX,
#   and a ranker prices a predicted identity at zero.
#   Jaw two: my replayed meter is wrong by construction, so every command I
#   fully model scores 4.88 bits = log2(59/2) forever. Six probes have now
#   reported that same number.
#   Jaw three: a manual that correctly forecasts its own mismatch produces a
#   surprise report every round even when nothing was pressed.
#   Jaw four, new: the clock now guarantees a fresh empirical surprise on one
#   command in three whatever I do. A tick is not news.
#
# WHAT IS GENUINELY UNKNOWN
#   * ACTION5 and ACTION6: never pressed in nineteen entries. Zero constraint.
#     If one of them is a coordinate action the guard language cannot express
#     it (E-05), and the 4x4 colour-14 block at rows 31-34 cols 42-45 is the
#     only untouched structure on the board.
#   * ACTION2 in W0, ACTION1 in W1, ACTION4 in W1: silences with no witness.
#   * The win condition. Eighteen states, all NOT_FINISHED. The widget has
#     returned to its opening position, so nothing in it is cumulative, and
#     the one monotone quantity is a clock. The goal language cannot name a
#     GameState (E-03) or a cell that is still board (E-02).
#
# PRICES ADVERTISED IN ADVANCE, SO A REFUTATION ON THEM IMPLICATES NOTHING
#   * Replay is 7 of 17 and every wrong cell is on row 53. It will lose one
#     more cell every six frames, permanently, and I have refused two repairs
#     with arithmetic rather than accept a wave that walks into board cells.
#   * ACTION2 here is predicted SILENT and I expect that to be wrong.
#   * ACTION1 here is predicted to the cell: 96 cells, rows 30-41, cols 11-22.
#   * ACTION3 and ACTION7 here: the same twelve readout cells go dark, in two
#     frames and one frame respectively.
#   * ACTION4 here is predicted silent, entailed by its own guard.
#
# THE RANKED LIST -- REORDERED, BECAUSE THE CLOCK IS A BUDGET AND THE WIN
# CONDITION IS THE ONLY THING THAT ENDS THE PROBE REGIME
# 1. ACTION5 OR ACTION6. Never pressed in nineteen entries; the only place a
#    GameState other than NOT_FINISHED could come from; the only place a cell
#    outside rows 30-41 and row 53 could turn dynamic; and if it is inert it
#    returns one frame and adjudicates the clock for free. Any outcome is the
#    largest single addition to the manual available, including nothing.
# 2. ACTION2, HERE, IN W0. Splits exchange from scroll, tests the twenty
#    forged-silent k2 rules at once, moves 96 cells because the readout is
#    lit, three legible outcomes, and askable only from W0.
# 3. ACTION1 HERE, only if a 96-cell readout-transfer re-witness is wanted:
#    it re-earns four rules that stand on one witness each. Lower than it
#    looks, because six ACTION1 presses have all been made from W0.
# 4. ACTION4 IN W1, whenever W1 is next occupied with a dark bottom readout.
#    Tests the guard I wrote into silence on purpose.
# 5. The meter is read for free in the raw diff and in the vacuity flag of
#    whatever is pressed. NEVER spend a command on it.
#
# WHAT NOT TO PRESS
#   ACTION1 or ACTION2 in the configuration each has already been pressed six
#   times in, unless the lit readout is the point. ACTION3 or ACTION7 here:
#   witnessed in this exact configuration at t3 and t5. Anything chosen
#   because the report says 4.88 bits: that is my own meter error being sold
#   back to me. And do not spend a round on certification alone -- but note
#   that a thinking round costs no clock, so the argument against it is that
#   it learns nothing, not that it is expensive.

order     press_an_action_never_pressed_before_repressing_a_modelled_one    [proof: lean]
order     buy_the_observation_that_makes_a_goal_writable_before_writing_one [proof: lean]
order     press_a_modelled_action_in_a_configuration_it_was_never_pressed_in [proof: lean]
order     spend_a_probe_only_the_current_state_can_ask_before_one_askable_anywhere [proof: lean]
order     test_a_silence_that_is_an_artefact_of_rule_syntax_before_any_other [proof: lean]
order     test_a_silence_that_rests_on_no_witness_before_one_that_is_entailed [proof: lean]
order     press_something_rather_than_recertify_a_manual_that_forecast_itself [proof: lean]
order     count_the_frames_a_command_returns_as_the_price_it_charges_the_clock [proof: lean]
order     prefer_a_short_command_when_two_probes_are_otherwise_equal        [proof: lean]
order     read_a_free_experiment_off_the_command_you_were_going_to_press_anyway [proof: lean]
order     fit_a_hidden_counter_to_cumulative_frames_before_to_command_index [proof: lean]
order     test_an_absolute_counter_against_one_that_resets_on_every_tick    [proof: lean]
order     prefer_a_two_parameter_law_that_leaves_no_residual_over_a_drifting_one [proof: lean]
order     date_a_prediction_by_index_so_a_wrong_period_can_be_killed        [proof: lean]
order     kill_a_fitted_period_the_moment_one_interval_breaks_it            [proof: lean]
order     test_every_counter_computable_from_the_log_before_spending_a_command [proof: lean]
order     prove_a_quantity_is_not_a_function_of_the_frame_before_guessing_its_guard [proof: lean]
order     find_two_identical_frames_with_different_successors_before_adding_a_rule [proof: lean]
order     name_a_hidden_variable_as_a_language_limit_rather_than_as_ignorance [proof: lean]
order     check_a_reconstruction_against_a_store_number_you_did_not_fit     [proof: lean]
order     list_the_duplicate_states_your_parity_forces_and_count_them       [proof: lean]
order     recount_a_state_census_against_the_store_before_drawing_from_it   [proof: lean]
order     let_a_new_dynamic_cell_join_the_type_its_frame_zero_colour_names  [proof: lean]
order     check_each_types_coverages_sum_to_its_instance_count              [proof: lean]
order     count_a_coverage_figure_before_writing_it_down                    [proof: lean]
order     sum_the_wrong_cells_a_repair_would_cost_before_adopting_it        [proof: lean]
order     answer_a_priced_surprise_with_a_stated_refusal_and_arithmetic     [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired   [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance                [proof: lean]
order     refuse_a_patch_fitted_to_a_two_of_two_coincidence_of_keys         [proof: lean]
order     refuse_a_patch_that_would_be_wrong_on_the_next_press_of_its_own_key [proof: lean]
order     guard_a_rule_into_silence_before_letting_it_draw_an_unwitnessed_state [proof: lean]
order     rename_a_rule_that_survives_only_as_a_replay_patch                [proof: lean]
order     separate_same_coloured_roles_by_a_cell_you_have_actually_read     [proof: lean]
order     read_a_never_changing_row_as_evidence_about_structure             [proof: lean]
order     override_a_ranker_that_prices_every_predicted_identity_at_zero    [proof: lean]
order     discount_gain_earned_only_on_a_cell_the_manual_declared_undrawable [proof: lean]
order     recompute_reported_bits_from_survivor_counts_before_trusting_them [proof: lean]
order     suspect_the_scoring_channel_when_one_number_repeats_six_probes_running [proof: lean]
order     use_a_vacuous_frontier_as_a_detector_rather_than_as_a_defeat      [proof: lean]
order     prefer_a_probe_with_three_distinct_legible_outcomes_over_one_with_two [proof: lean]
order     add_no_rule_in_a_round_that_bought_no_new_observation             [proof: lean]
order     verify_what_a_recount_can_settle_before_asking_the_world          [proof: lean]
order     honour_the_refutation_clause_you_wrote_into_your_own_theorem      [proof: lean]
order     strike_a_refuted_theorem_rather_than_reinterpret_it               [proof: lean]
order     cite_only_engine_reports_that_were_actually_supplied_this_round   [proof: lean]
order     refuse_a_goal_no_observation_distinguishes_and_say_so_out_loud    [proof: lean]
order     emit_every_required_block_before_polishing_any_of_them            [proof: lean]

prune     rule_proposed_with_zero_witnesses_of_any_kind => dead             [proof: lean]
prune     rule_over_a_quantity_shown_not_to_be_a_function_of_the_frame => dead [proof: lean]
prune     rule_keyed_to_an_action_that_explains_two_of_five_occurrences => dead [proof: lean]
prune     rule_that_would_fire_on_the_next_press_of_the_key_it_was_fitted_to => dead [proof: lean]
prune     repair_that_does_not_reduce_total_wrong_cell_transitions => dead  [proof: lean]
prune     repair_whose_error_walks_into_cells_that_are_still_board => dead  [proof: lean]
prune     repair_that_races_ahead_of_a_clock_it_cannot_read => dead         [proof: lean]
prune     rule_added_in_a_round_whose_store_counts_did_not_move => dead     [proof: lean]
prune     rule_that_would_forge_the_reverse_direction_of_an_unobserved_press => dead [proof: lean]
prune     guard_conjunct_with_no_negative_witness_and_no_explained_pixel => dead [proof: lean]
prune     period_fitted_to_two_ticks_and_broken_by_a_third => dead          [proof: lean]
prune     counter_that_fails_on_any_tick_already_in_the_log => dead         [proof: lean]
prune     counter_that_must_be_reset_on_tick_to_fit => dead                 [proof: lean]
prune     divergence_lies_only_on_the_meter_frontier => dead                [proof: lean]
prune     divergence_a_later_transition_only_inherited_from_an_earlier_one => dead [proof: lean]
prune     divergence_the_previous_edition_named_by_cell_and_by_command => dead [proof: lean]
prune     probe_whose_reported_bits_are_all_earned_on_undrawable_cells => dead [proof: lean]
prune     probe_vacuous_because_the_clock_ticked_under_it => dead           [proof: lean]
prune     probe_that_repeats_a_key_in_a_configuration_already_probed_twice => dead [proof: lean]
prune     repeats_a_key_whose_inertness_here_is_entailed_by_witnessed_rules => dead [proof: lean]
prune     repeats_a_key_already_watched_doing_nothing_in_this_exact_state => dead [proof: lean]
prune     repeats_a_transition_already_witnessed_from_an_identical_frame => dead [proof: lean]
prune     ranked_only_because_the_manual_predicts_the_most_pixels => dead   [proof: lean]
prune     leaves_the_only_configuration_that_can_ask_the_open_question => dead [proof: lean]
prune     every_rule_it_would_witness_is_already_at_full_coverage => dead   [proof: lean]
prune     goal_clause_over_a_cell_that_is_still_board => dead               [proof: lean]
prune     goal_over_a_quantity_shown_to_be_a_clock => dead                  [proof: lean]
prune     goal_that_is_already_true_at_the_current_state => dead            [proof: lean]
prune     goal_satisfiable_without_leaving_the_two_widget_configurations => dead [proof: lean]
prune     goal_no_observed_gamestate_could_have_distinguished => dead       [proof: lean]

heuristic actions_of_the_alphabet_never_yet_pressed                         [admissible: lean]
heuristic configurations_in_which_a_known_key_has_never_been_pressed        [admissible: lean]
heuristic silences_that_follow_from_rule_syntax_rather_than_from_evidence   [admissible: lean]
heuristic silences_of_the_manual_that_rest_on_no_witness                    [admissible: lean]
heuristic structural_readings_a_single_command_could_eliminate              [admissible: lean]
heuristic rules_that_one_command_could_generalise_or_refute_together        [admissible: lean]
heuristic rules_still_standing_on_a_single_witness                          [admissible: lean]
heuristic distinct_legible_outcomes_a_single_command_can_produce            [admissible: lean]
heuristic questions_that_only_the_present_configuration_can_ask             [admissible: lean]
heuristic frames_a_command_returns_and_the_clock_units_it_therefore_spends  [admissible: lean]
heuristic commands_that_would_slip_a_clock_prediction_against_a_rival_one   [admissible: lean]
heuristic counters_still_fitting_every_tick_in_the_log                      [admissible: lean]
heuristic store_numbers_a_reconstruction_predicts_without_having_fitted_them [admissible: lean]
heuristic pairs_of_identical_frames_with_different_successors               [admissible: lean]
heuristic coverage_deficits_between_a_types_rules_and_its_instance_count    [admissible: lean]
heuristic repairs_whose_wrong_cell_total_i_have_actually_summed             [admissible: lean]
heuristic reported_bits_that_survive_deleting_the_undrawable_cells          [admissible: lean]
heuristic consecutive_commands_spent_on_a_single_already_modelled_key       [admissible: lean]
heuristic widget_configurations_never_yet_observed                          [admissible: lean]
heuristic rows_that_have_never_changed_and_constrain_a_structural_reading   [admissible: lean]
heuristic cells_outside_the_widget_a_command_could_turn_dynamic             [admissible: lean]
heuristic board_structures_no_command_has_ever_touched                      [admissible: lean]
heuristic cells_whose_first_change_would_make_a_goal_line_writable          [admissible: lean]
heuristic gamestates_other_than_not_finished_ever_returned                  [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_advertised_prices            [admissible: lean]

prefer    a_key_never_pressed_in_any_state                                  [ev: 2/7 keys]
prefer    a_key_never_pressed_in_the_configuration_now_showing              [ev: 3/5 pressed keys]
prefer    a_command_that_splits_two_named_readings_in_one_press             [ev: 1/1 available]
prefer    a_probe_askable_only_from_the_configuration_now_showing           [ev: 1/2 configurations]
prefer    a_command_that_tests_twenty_rules_at_once                         [ev: 2/2 available]
prefer    a_command_that_re_witnesses_a_rule_standing_on_one_witness        [ev: 8/47 rules]
prefer    a_command_that_would_turn_a_cell_outside_the_widget_dynamic       [ev: 5/19 entries]
prefer    a_command_that_could_return_a_gamestate_never_yet_seen            [ev: 0/19 entries so far]
prefer    a_command_that_would_produce_a_third_widget_configuration         [ev: 0/19 entries so far]
prefer    a_command_whose_outcome_the_manual_cannot_already_hash            [ev: 6/6 last probes failed this]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                  [ev: 18/18 diffs]
prefer    a_command_returning_one_frame_when_two_probes_tie                 [ev: 2/18 commands]
prefer    any_command_at_all_over_a_second_round_of_pure_certification      [ev: 1/1 rounds]
```

=== LOG ===
```json
[
  {"id": "O-01", "subject": "colour-5 cells of the top slot", "verdict": "accept", "as": "Field, 24 instances, arc-instances all", "why": "rows 30-35 cols 11,12,15,16 read colour 5 in the current frame and 24+8+14+12+22+12+9 = 101 = dynamic_cells with 101-24 = 77 = cells_needing_an_owner, so the census is checked twice by store numbers I did not fit."},
  {"id": "O-02", "subject": "colour-3 cells", "verdict": "accept", "as": "BarBody, 8 instances", "why": "the bar's rows 30,31,34,35 at cols 13-14 read 3 in the current frame, unchanged from every previous edition."},
  {"id": "O-03", "subject": "colour-2 cells", "verdict": "accept", "as": "BarCore, 14 instances (was 12)", "why": "(53,59) and (53,60) changed for the first time this round at t17 and t14, so they are dynamic and their frame-0 colour was 2; the type therefore grows to 4 bar core + 1 port + 4 readout cores + 5 meter, and board_cells falls 3997 -> 3995 exactly as the store reports."},
  {"id": "O-04", "subject": "colour-4 readout cells", "verdict": "accept", "as": "Blank, 12 instances", "why": "rows 32-33 cols 17-22 read 4 in the current frame, the dark readout of frame 0."},
  {"id": "O-05", "subject": "colour-6 cells", "verdict": "accept", "as": "Frame, 22 instances", "why": "read down the box now standing in the bottom slot rows 36-41: 6+2+3+3+2+6 = 22, with (38,16) and (39,16) taken by the two ports."},
  {"id": "O-06", "subject": "colour-0 cells", "verdict": "accept", "as": "Hollow, 12 instances", "why": "the same box interior: 4+2+2+4 = 12."},
  {"id": "O-07", "subject": "colour-1 cells", "verdict": "accept", "as": "Dot, 9 instances", "why": "8 lit readout dots at rows 38-39 cols 17-22 plus the upper port pixel (38,16), all re-read off the current frame after t17 relit the readout."},
  {"id": "O-08", "subject": "the two newly dynamic meter cells (53,59) and (53,60)", "verdict": "accept", "as": "further BarCore instances", "why": "they wore colour 2 at frame 0 and the arm assigns by colour alone, so they join BarCore automatically; they raise BarCore's coverage deficit from 3 to 5 and that deficit is exactly the set of cells no rule of mine may touch."},
  {"id": "R-01", "subject": "the twenty k1 swap rules", "verdict": "accept", "as": "unchanged text, evidence extended to t15", "why": "t15 ACTION1 changed 72 cells at rows 30-41 cols 11-16 with both readouts dark, which is the sixth exact witness for the dark-readout half of the family and produced no replay complaint outside row 53."},
  {"id": "R-02", "subject": "the twenty k2 swap rules", "verdict": "accept", "as": "unchanged text, evidence extended to t14 and t16", "why": "t14 and t16 each changed 72 widget cells returning W1 to W0, and certify's only wrong cells across both transitions are meter cells."},
  {"id": "R-03", "subject": "k4_dot_lights and k4_core_lights", "verdict": "accept", "as": "unchanged text, evidence extended to t17", "why": "t17 lit exactly (38,17)->2 (38,18)->1 (38,19)->1 (38,20)->2 (38,21)->1 (38,22)->1 (39,17)->1 (39,18)->1 (39,19)->2 (39,20)->1 (39,21)->1 (39,22)->2, which is 8 dots and 4 cores, and the guard colored(bottom_port,1) held because the box was in the bottom slot."},
  {"id": "R-04", "subject": "meter_first_tick_replay_patch", "verdict": "accept", "as": "kept, and now openly labelled an accident", "why": "it draws the t4 tick correctly and can never fire again in replay because its guard needs a colour-2 cell at column 63 and (53,63) is 3 forever after; deleting it would cost one exactly-replayed transition and buy nothing, but the true cause of that tick is the six-frame clock, not key(4)."},
  {"id": "R-05", "subject": "a second meter patch, act=key(4) and colored(?s,2) and colored(rightof(?s),3) then recolored(?s,3)", "verdict": "reject", "why": "it would draw t17's tick exactly right and raise replay to 8/17, but it fits a 2-of-2 coincidence: five ticks occurred, two under ACTION4, two under ACTION1 and one under ACTION2, and it would fire on the very next ACTION4 press regardless of the clock, which the playbook ranks as a command I intend to make."},
  {"id": "R-06", "subject": "the propagation repair carried from earlier editions", "verdict": "reject", "why": "under cascade single_frame it walks one cell left per command, so by t17 it would have lit about thirteen meter cells against the world's five, and every surplus cell it lights is still board."},
  {"id": "R-07", "subject": "every cegis_miner track in the candidate stream", "verdict": "reject", "why": "all 2866 rows resolve to refusals of two kinds -- the transition narrates vanish rather than move, or the object is absent at frame 0 -- or to NoSeparatingGuard on transition 1 or 2; a mover-miner is right to refuse a world in which nothing moves and every event is a recolour."},
  {"id": "L-01", "subject": "the meter is an absolute counter ticking every six frames", "verdict": "accept", "as": "theorem the_meter_is_an_absolute_six_frame_counter [probe: pending]", "why": "cumulative frames including RESET at the five ticks are 9, 16, 21, 27, 33 against thresholds 9+6k, and the command before each tick stands at 7, 14, 19, 25, 31 -- below its threshold in every case; five ticks, two parameters, no residual, and it is a theorem rather than a rule because the guard language has no counter."},
  {"id": "L-02", "subject": "period-3-in-commands, fitted to the intervals 4,3,3,3", "verdict": "reject", "why": "it needs an unexplained first interval and cannot say why t8-t11 was three commands when t9 returned only one frame; the absolute frame counter explains that by the one-frame overshoot at t8 and I have dated a prediction (t20 versus t21) that separates them."},
  {"id": "L-03", "subject": "the wall-clock reading carried from the fifth and sixth editions", "verdict": "reject", "why": "it explained a drift and nothing exact; the frame counter reproduces all five tick indices as integers, and a round in which no command was pressed produced no tick, which a real-time clock would not respect."},
  {"id": "L-04", "subject": "a probe goes vacuous exactly when the world ticks", "verdict": "accept", "as": "promoted from probe: pending to probe: passed", "why": "P-06 (t11) and P-09 (t14) are vacuous and are exactly the ticking commands among t10-t16; P-05, P-07, P-08, P-10, P-11 have two survivors each and their commands left row 53 alone -- 7 of 7, with the mechanism being that no hypothesis on my frontier can tick."},
  {"id": "L-05", "subject": "the five duplicate state pairs S2=S0, S7=S5, S9=S8, S13=S11, S16=S14", "verdict": "accept", "as": "theorem the_five_duplicate_states_were_predicted_by_parity_and_the_store_agreed", "why": "18 states minus 5 duplicates is 13 and distinct_states = 13; the parity, the readout state and the meter reconstruction are all loaded into that number and it was not fitted."},
  {"id": "L-06", "subject": "coverage columns after the instance count changed", "verdict": "accept", "as": "96 of 101 owned cells covered in both directions, deficit 5", "why": "Field 24, Frame 22 both ways, Hollow 12, BarBody 8, Dot 9, Blank 12 all partition exactly; BarCore is 9 of 14 and the missing five are the five meter cells, up from three because two cells turned dynamic."},
  {"id": "L-07", "subject": "the replay_mismatch surprise at t=7 cell (53,62)", "verdict": "reject", "as": "an explicit refusal to change, with arithmetic", "why": "it is the cell and transition index the fifth edition named in advance; the current total cost is 22 wrong-cell-transitions all on row 53, it contaminates nothing because no rule grounds on a meter cell, and both available repairs were computed and are worse."},
  {"id": "L-08", "subject": "the heuristic_miss demanding a goal", "verdict": "reject", "as": "no goal section, with a new argument", "why": "S17 equals S0 in all 96 widget cells, so seventeen commands have produced nothing cumulative and there is no monotone quantity in the widget for a goal to name; the only monotone quantity is a clock driven by frames rather than by my choices, and a goal over a clock is a goal over the passage of time."},
  {"id": "L-09", "subject": "ACTION6 may be a coordinate action and the colour-14 block may be its target", "verdict": "probe-pending", "as": "theorem action6_may_be_a_click_and_the_colour_14_block_is_the_only_target_on_the_board", "why": "labelled a guess: two keys are unpressed after nineteen entries, and the 4x4 colour-14 block at rows 31-34 cols 42-45 is the only structure on the board no command has touched."},
  {"id": "P-09", "subject": "vacuous frontier, ACTION2, 0 of 59 survivors, 0.0 bits", "verdict": "entailed", "why": "P-09 is t14, the command on which the meter ticked to (53,60); no hypothesis on a frontier made of my manual and its ablations can tick, so the observed frame lies outside the frontier and the vacuity is entailed by my own declared gap rather than by a missing widget mechanism."},
  {"id": "P-10", "subject": "manual wrong, ACTION1, 4.882643 bits", "verdict": "entailed", "why": "P-10 is t15; my replayed meter is short by three cells at that point, so my predicted hash cannot match however exactly I draw the 72 widget cells that actually changed, and certify confirms the divergence set is meter-only."},
  {"id": "P-11", "subject": "manual wrong, ACTION2, 4.882643 bits", "verdict": "entailed", "why": "P-11 is t16 and carries hashes identical to P-09's in both columns, which is itself a check: S14 and S16 are the same state, exactly as the duplicate count requires."},
  {"id": "P-12", "subject": "the next tick lights (53,58) at cumulative frame 39", "verdict": "probe-pending", "why": "dated in advance: t20 if the next three commands each return two frames, t21 if exactly one returns one; the probe report on that command will be frontier_vacuous with zero survivors, and no other row-53 cell changes before it."},
  {"id": "E-02", "subject": "a goal naming the un-ticked meter cells", "verdict": "reject", "as": "carried; I wrote no goal section", "why": "cells that have never changed are board rather than instances, so the goal language cannot name them; count(BarCore, color = 3) tops out at 14 and nine of those are widget cells with nothing to do with the meter."},
  {"id": "E-03", "subject": "goal gamestate != NOT_FINISHED", "verdict": "reject", "as": "no goal section; stated in prose in no_goal_section_and_the_refusal_is_now_stronger_than_it_was", "why": "the goal language admits only positions and counts of declared objects; the world's own win signal has no term, so the one goal I would actually endorse cannot be written."},
  {"id": "E-04", "subject": "the six-frame meter counter", "verdict": "reject", "as": "written as theorem the_meter_is_an_absolute_six_frame_counter instead of as a rule", "why": "the guard language has no counter, no history and no frames-returned term, and I proved the tick is not a function of the frame with two identical-frame pairs; so I know the law exactly and my compiled step must stay wrong on five cells and counting."},
  {"id": "E-05", "subject": "a coordinate-carrying action such as a click on (31..34, 42..45)", "verdict": "reject", "as": "written as a theorem with probe: pending", "why": "act=key(n) is the whole action vocabulary the arm maps, and a click carries coordinates the guard language cannot express; I said so rather than inventing syntax."}
]
```
```
