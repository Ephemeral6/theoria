# call-006-theorize-round1

model: `claude-opus-5` · 1517135 ms · $4.625281 · usage {"cache_creation": {"ephemeral_1h_input_tokens": 130405, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 130405, "cache_read_input_tokens": 38490, "inference_geo": "not_available", "input_tokens": 6, "iterations": [{"cache_creation": {"ephemeral_1h_input_tokens": 64065, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 64065, "cache_read_input_tokens": 34964, "input_tokens": 2, "output_tokens": 3033, "type": "message"}], "output_tokens": 131033, "server_tool_use": {"web_fetch_requests": 0, "web_search_requests": 0}, "service_tier": "standard", "speed": "standard"}

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
 "cells_needing_an_owner": 74,
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
 "constant_cells": 3998,
 "distinct_states": 8,
 "dynamic_box": [
  29,
  10,
  54,
  63
 ],
 "dynamic_cells": 98,
 "max_frames_in_one_command": 2,
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

Only the cells that have EVER changed are shown (rows 29-10, cols 54-63); everything outside this box has held one colour for the whole history and is board by definition.

```
    111111111122222222223333333333444444444455555555556666
    012345678901234567890123456789012345678901234567890123
 29 555335544444444444444444444444444444455555555555555555
 30 566666644444444444444444444444444444455555555555555555
 31 56000064444444444444444444444444eeee455555555555555555
 32 56066014444444444444444444444444eeee455555555555555555
 33 56066024444444444444444444444444eeee455555555555555555
 34 56000064444444444444444444444444eeee455555555555555555
 35 566666644444444444444444444444444444455555555555555555
 36 555335544444444444444444444444444444455555555555555555
 37 555335544444444444444444444444444444455555555555555555
 38 555225544444444444444444444444444444455555555555555555
 39 555225544444444444444444444444444444455555555555555555
 40 555555544444444444444444444444444444455555555555555555
 41 555555544444444444444444444444444444455555555555555555
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
 53 222222222222222222222222222222222222222222222222222233
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
- t8   ACTION3   frames=1   state=NOT_FINISHED (53,62) 2->3
- t9   ACTION1   frames=2   state=NOT_FINISHED 72 cells changed, rows 30-41, cols 11-16, [0, 1, 2, 3, 5, 6] -> [0, 1, 2, 3, 5, 6]

## What the engines proposed

These are PROPOSALS. Nothing here is accepted until you accept it, and an engine cannot name anything -- `obj0` is the best it can do.

```json
{
 "cegis_miner": {
  "engine": "cegis_miner",
  "n_actions": 9,
  "n_states": 10,
  "refusals": [
   "ValueError: transition 0 narrates ['vanish']; only move/none are mined on this fixture",
   "ValueError: transition 3 narrates ['recolor']; only move/none are mined on this fixture",
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
    "refused": "ValueError: transition 3 narrates ['recolor']; only move/none are mined on this fixture",
    "track_id": "obj1"
   },
   {
    "ms": 0,
    "refused": "ValueError: object absent at frame 0; unsupported on this fixture",
    "track_id": "obj2"
   },
   {
    "ms": 0,
    "refused": "ValueError: object absent at frame 0; unsupported on this fixture",
    "track_id": "obj3"
   },
   {
    "ms": 0,
    "refused": "ValueError: object absent at frame 0; unsupported on this fixture",
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
  "background": 5,
  "candidates": 7,
  "chosen_operator": "connected_components(4)",
  "chosen_split_by_color": false,
  "engine": "mdl_segmenter",
  "event_types": {
   "appear": 5,
   "recolor": 5,
   "vanish": 5
  },
  "n_frames": 10,
  "tracks": [
   {
    "color": null,
    "first_frame": 0,
    "frames_present": 1,
    "n_cells": 440,
    "shape": [
     13,
     36
    ],
    "track_id": "obj0"
   },
   {
    "color": null,
    "first_frame": 0,
    "frames_present": 10,
    "n_cells": 108,
    "shape": [
     2,
     54
    ],
    "track_id": "obj1"
   },
   {
    "color": null,
    "first_frame": 1,
    "frames_present": 1,
    "n_cells": 436,
    "shape": [
     13,
     36
    ],
    "track_id": "obj2"
   },
   {
    "color": null,
    "first_frame": 2,
    "frames_present": 4,
    "n_cells": 440,
    "shape": [
     13,
     36
    ],
    "track_id": "obj3"
   },
   {
    "color": null,
    "first_frame": 6,
    "frames_present": 1,
    "n_cells": 436,
    "shape": [
     13,
     36
    ],
    "track_id": "obj4"
   },
   {
    "color": null,
    "first_frame": 7,
    "frames_present": 2,
    "n_cells": 440,
    "shape": [
     13,
     36
    ],
    "track_id": "obj5"
   },
   {
    "color": null,
    "first_frame": 9,
    "frames_present": 1,
    "n_cells": 436,
    "shape": [
     13,
     36
    ],
    "track_id": "obj6"
   }
  ],
  "variants": [
   {
    "baseline_bits": 6762,
    "compression_ratio": 2.11328,
    "events": 15,
    "gain_bits": -7528,
    "ms": 7,
    "script_bits": 14290,
    "split_by_color": false,
    "tracks": 7
   },
   {
    "baseline_bits": 6762,
    "compression_ratio": 2.17835,
    "events": 92,
    "gain_bits": -7968,
    "ms": 25,
    "script_bits": 14730,
    "split_by_color": true,
    "tracks": 38
   }
  ],
  "window": {
   "box": [
    29,
    10,
    54,
    63
   ],
   "covered": 1.0,
   "dynamic_cells": 98,
   "frame_cells": 4096,
   "full_frame": false,
   "reason": "frame is 4096 cells (> 1200), arena is 1404",
   "window_cells": 1404
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
   "ACTION7",
   "RESET"
  ],
  "background": 5,
  "cascade_lengths": [
   1,
   2
  ],
  "cells_needing_an_owner": 74,
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
  "constant_cells": 3998,
  "distinct_states": 8,
  "dynamic_box": [
   29,
   10,
   54,
   63
  ],
  "dynamic_cells": 98,
  "max_frames_in_one_command": 2,
  "shape": [
   64,
   64
  ],
  "states": 10,
  "steps": 10
 },
 "window": {
  "box": [
   29,
   10,
   54,
   63
  ],
  "covered": 1.0,
  "dynamic_cells": 98,
  "frame_cells": 4096,
  "full_frame": false,
  "reason": "frame is 4096 cells (> 1200), arena is 1404",
  "window_cells": 1404
 },
 "zero_space": {
  "cap": 240,
  "cells": [
   [
    30,
    11
   ],
   [
    30,
    12
   ],
   [
    30,
    13
   ],
   [
    30,
    14
   ],
   [
    30,
    15
   ],
   [
    30,
    16
   ],
   [
    31,
    11
   ],
   [
    31,
    12
   ],
   [
    31,
    13
   ],
   [
    31,
    14
   ],
   [
    31,
    15
   ],
   [
    31,
    16
   ],
   [
    32,
    11
   ],
   [
    32,
    12
   ],
   [
    32,
    13
   ],
   [
    32,
    14
   ],
   [
    32,
    15
   ],
   [
    32,
    16
   ],
   [
    32,
    17
   ],
   [
    32,
    18
   ],
   [
    32,
    19
   ],
   [
    32,
    20
   ],
   [
    32,
    21
   ],
   [
    32,
    22
   ],
   [
    33,
    11
   ],
   [
    33,
    12
   ],
   [
    33,
    13
   ],
   [
    33,
    14
   ],
   [
    33,
    15
   ],
   [
    33,
    16
   ],
   [
    33,
    17
   ],
   [
    33,
    18
   ],
   [
    33,
    19
   ],
   [
    33,
    20
   ],
   [
    33,
    21
   ],
   [
    33,
    22
   ],
   [
    34,
    11
   ],
   [
    34,
    12
   ],
   [
    34,
    13
   ],
   [
    34,
    14
   ],
   [
    34,
    15
   ],
   [
    34,
    16
   ],
   [
    35,
    11
   ],
   [
    35,
    12
   ],
   [
    35,
    13
   ],
   [
    35,
    14
   ],
   [
    35,
    15
   ],
   [
    35,
    16
   ],
   [
    36,
    11
   ],
   [
    36,
    12
   ],
   [
    36,
    13
   ],
   [
    36,
    14
   ],
   [
    36,
    15
   ],
   [
    36,
    16
   ],
   [
    37,
    11
   ],
   [
    37,
    12
   ],
   [
    37,
    13
   ],
   [
    37,
    14
   ],
   [
    37,
    15
   ],
   [
    37,
    16
   ],
   [
    38,
    11
   ],
   [
    38,
    12
   ],
   [
    38,
    13
   ],
   [
    38,
    14
   ]
  ],
  "cells_dynamic": 98,
  "cells_used": 98,
  "colours": [
   "c0",
   "c1",
   "c2",
   "c3",
   "c4",
   "c5",
   "c6"
  ],
  "difference_rank": 5,
  "engine": "zero_space",
  "evidence_adequacy": {
   "constrained_fraction": 0.007289,
   "difference_rank": 5,
   "features": 686,
   "space_dimension": 681,
   "transitions": 9,
   "verdict": "THIN: 9 transitions constrain rank 5 of 686 features, so the null space has dimension 681 and nearly every vector in it is a 'law' that is true over these states and unfalsified rather than confirmed. Treat every law below as a correlation awaiting a transition that could break it, not as a conservation law."
  },
  "features": 686,
  "global_laws": [
   {
    "cells": [
     [
      30,
      11
     ],
     [
      30,
      12
     ],
     [
      30,
      13
     ],
     [
      30,
      14
     ],
     [
      30,
      15
     ],
     [
      30,
      16
     ],
     [
      31,
      11
     ],
     [
      31,
      12
     ],
     [
      31,
      13
     ],
     [
      31,
      14
     ],
     [
      31,
      15
     ],
     [
      31,
      16
     ],
     [
      32,
      11
     ],
     [
      32,
      12
     ],
     [
      32,
      13
     ],
     [
      32,
      14
     ],
     [
      32,
      15
     ],
     [
      32,
      16
     ],
     [
      32,
      17
     ],
     [
      32,
      18
     ],
     [
      32,
      19
     ],
     [
      32,
      20
     ],
     [
      32,
      21
     ],
     [
      32,
      22
     ],
     [
      33,
      11
     ],
     [
      33,
      12
     ],
     [
      33,
      13
     ],
     [
      33,
      14
     ],
     [
      33,
      15
     ],
     [
      33,
      16
     ],
     [
      33,
      17
     ],
     [
      33,
      18
     ],
     [
      33,
      19
     ],
     [
      33,
      20
     ],
     [
      33,
      21
     ],
     [
      33,
      22
     ],
     [
      34,
      11
     ],
     [
      34,
      12
     ],
     [
      34,
      13
     ],
     [
      34,
      14
     ],
     [
      34,
      15
     ],
     [
      34,
      16
     ],
     [
      35,
      11
     ],
     [
      35,
      12
     ],
     [
      35,
      13
     ],
     [
      35,
      14
     ],
     [
      35,
      15
     ],
     [
      35,
      16
     ],
     [
      36,
      11
     ],
     [
      36,
      12
     ],
     [
      36,
      13
     ],
     [
      36,
      14
     ],
     [
      36,
      15
     ],
     [
      36,
      16
     ],
     [
      37,
      11
     ],
     [
      37,
      12
     ],
     [
      37,
      13
     ],
     [
      37,
      14
     ],
     [
      37,
      15
     ],
     [
      37,
      16
     ],
     [
      38,
      11
     ],
     [
      38,
      12
     ],
     [
      38,
      13
     ],
     [
      38,
      14
     ],
     [
      38,
      15
     ],
     [
      38,
      16
     ],
     [
      38,
      17
     ],
     [
      38,
      18
     ],
     [
      38,
      19
     ],
     [
      38,
      20
     ],
     [
      38,
      21
     ],
     [
      38,
      22
     ],
     [
      39,
      11
     ],
     [
      39,
      12
     ],
     [
      39,
      13
     ],
     [
      39,
      14
     ],
     [
      39,
      15
     ],
     [
      39,
      16
     ],
     [
      39,
      17
     ],
     [
      39,
      18
     ],
     [
      39,
      19
     ],
     [
      39,
      20
     ],
     [
      39,
      21
     ],
     [
      39,
      22
     ],
     [
      40,
      11
     ],
     [
      40,
      12
     ],
     [
      40,
      13
     ],
     [
      40,
      14
     ],
     [
      40,
      15
     ],
     [
      40,
      16
     ],
     [
      41,
      11
     ],
     [
      41,
      12
     ],
     [
      41,
      13
     ],
     [
      41,
      14
     ],
     [
      41,
      15
     ],
     [
      41,
      16
     ],
     [
      53,
      62
     ],
     [
      53,
      63
     ]
    ],
    "support": [
     "c0@0",
     "c1@0",
     "c2@0",
     "c3@0",
     "c4@0",
     "c5@0",
     "c6@0",
     "c0@1",
     "c1@1",
     "c2@1",
     "c3@1",
     "c4@1",
     "c5@1",
     "c6@1",
     "c0@2",
     "c1@2",
     "c2@2",
     "c3@2",
     "c4@2",
     "c5@2",
     "c6@2",
     "c0@3",
     "c1@3",
     "c2@3",
     "c3@3",
     "c4@3",
     "c5@3",
     "c6@3",
     "c0@4",
     "c1@4",
     "c2@4",
     "c3@4",
     "c4@4",
     "c5@4",
     "c6@4",
     "c0@5",
     "c1@5",
     "c2@5",
     "c3@5",
     "c4@5",
     "c5@5",
     "c6@5",
     "c0@6",
     "c1@6",
     "c2@6",
     "c3@6",
     "c4@6",
     "c5@6",
     "c6@6",
     "c0@7",
     "c1@7",
     "c2@7",
     "c3@7",
     "c4@7",
     "c5@7",
     "c6@7",
     "c0@8",
     "c1@8",
     "c2@8",
     "c3@8",
     "c4@8",
     "c5@8",
     "c6@8",
     "c0@9",
     "c1@9",
     "c2@9",
     "c3@9",
     "c4@9",
     "c5@9",
     "c6@9",
     "c0@10",
     "c1@10",
     "c2@10",
     "c3@10",
     "c4@10",
     "c5@10",
     "c6@10",
     "c0@11",
     "c1@11",
     "c2@11",
     "c3@11",
     "c4@11",
     "c5@11",
     "c6@11",
     "c0@12",
     "c1@12",
     "c2@12",
     "c3@12",
     "c4@12",
     "c5@12",
     "c6@12",
     "c0@13",
     "c1@13",
     "c2@13",
     "c3@13",
     "c4@13",
     "c5@13",
     "c6@13",
     "c0@14",
     "c1@14",
     "c2@14",
     "c3@14",
     "c4@14",
     "c5@14",
     "c6@14",
     "c0@15",
     "c1@15",
     "c2@15",
     "c3@15",
     "c4@15",
     "c5@15",
     "c6@15",
     "c0@16",
     "c1@16",
     "c2@16",
     "c3@16",
     "c4@16",
     "c5@16",
     "c6@16",
     "c0@17",
     "c1@17",
     "c2@17",
     "c3@17",
     "c4@17",
     "c5@17",
     "c6@17",
     "c0@18",
     "c1@18",
     "c2@18",
     "c3@18",
     "c4@18",
     "c5@18",
     "c6@18",
     "c0@19",
     "c1@19",
     "c2@19",
     "c3@19",
     "c4@19",
     "c5@19",
     "c6@19",
     "c0@20",
     "c1@20",
     "c2@20",
     "c3@20",
     "c4@20",
     "c5@20",
     "c6@20",
     "c0@21",
     "c1@21",
     "c2@21",
     "c3@21",
     "c4@21",
     "c5@21",
     "c6@21",
     "c0@22",
     "c1@22",
     "c2@22",
     "c3@22",
     "c4@22",
     "c5@22",
     "c6@22",
     "c0@23",
     "c1@23",
     "c2@23",
     "c3@23",
     "c4@23",
     "c5@23",
     "c6@23",
     "c0@24",
     "c1@24",
     "c2@24",
     "c3@24",
     "c4@24",
     "c5@24",
     "c6@24",
     "c0@25",
     "c1@25",
     "c2@25",
     "c3@25",
     "c4@25",
     "c5@25",
     "c6@25",
     "c0@26",
     "c1@26",
     "c2@26",
     "c3@26",
     "c4@26",
     "c5@26",
     "c6@26",
     "c0@27",
     "c1@27",
     "c2@27",
     "c3@27",
     "c4@27",
     "c5@27",
     "c6@27",
     "c0@28",
     "c1@28",
     "c2@28",
     "c3@28",
     "c4@28",
     "c5@28",
     "c6@28",
     "c0@29",
     "c1@29",
     "c2@29",
     "c3@29",
     "c4@29",
     "c5@29",
     "c6@29",
     "c0@30",
     "c1@30",
     "c2@30",
     "c3@30",
     "c4@30",
     "c5@30",
     "c6@30",
     "c0@31",
     "c1@31",
     "c2@31",
     "c3@31",
     "c4@31",
     "c5@31",
     "c6@31",
     "c0@32",
```

The full proposal stream is 1372 rows in `candidates.jsonl`.

## The manual as it stands

```
# theory.dsl -- the manual of a two-row list whose rows swap.
#
# WHAT CHANGED THIS ROUND, IN ONE PARAGRAPH
#
#   Last round I declared one large hole: A1 and A2 each changed 96 cells and
#   the diff had reported only a count, a box and two colour sets, so I wrote
#   NO rule and priced the refutation in advance -- "expect replay 3/5, t1
#   misses 96". certify came back 4/5 with the first divergence at t=0 and
#   TWENTY-FOUR OF THE MISSING CELLS PRINTED, world_says beside manual_says.
#   Those 24 cells are the whole answer. Read them against the current frame:
#   s1(30,11..16) = 6,6,6,6,6,6 = s0(36,11..16); s1(31,11..16) = 6,0,0,0,0,6 =
#   s0(37,11..16); s1(32,11..16) = 6,0,6,6,0,1 = s0(38,11..16); and
#   s1(32,17..22) = 2,1,1,2,1,1 = s0(38,17..22). Every one of the 24 is the
#   colour standing SIX ROWS BELOW it in s0. A1 swaps the block at rows 30-35
#   with the block at rows 36-41, columns 11-22, and A2 swaps it back. The
#   count confirms it independently and to the cell: 12 rows x 12 columns is
#   72 partner pairs, 24 of those pairs are canvas-4 on both sides (cols 17-22
#   at rows 30,31,34,35 against rows 36,37,40,41 -- which is exactly why those
#   24 cells are NOT in the dynamic set), 72 - 24 = 48 differing pairs, and
#   48 x 2 = 96. The number the summariser gave me is the number the swap
#   predicts, with nothing left over.
#
#   So the manual now writes A1 and A2 as rules, from pixels, and the hole is
#   closed. It also explains the one thing last round's manual could only note:
#   tape1 (rows 32-33, cols 17-22) renders 4 in all six frames yet all twelve
#   of its cells are dynamic -- because in s1 those twelve cells carry TAPE2's
#   stripes, having been swapped up. tape1 was never "shown"; it was tape2
#   passing through.
#
# WHY THIRTY-THREE RULES SAY ONE SENTENCE
#
#   The sentence is "every cell takes the colour of the cell six rows away".
#   The event vocabulary has recolored(o, <int literal>) and nothing that reads
#   a colour out of another cell, so the copy has to be spelled out once per
#   (object type, destination colour) pair that actually occurs. That is 18
#   rules for key(1) and 8 for key(2). This is a cost of the DSL, not of the
#   world, and I am declaring it rather than hiding it -- see
#   the_dsl_cannot_copy_a_colour.
#
# THE PRICE I EXPECT TO PAY NOW
#
#   Replay should be 5/5: t1 and t2 are ruled from the pixels above, t3, t4
#   and t5 were already exact. Responsibility should stay 0 unexplained, since
#   the object declarations are untouched. If the meter (53,63) moves under
#   key(1) or key(2) my Ink2 rules are wrong by one cell and I say where the
#   guard is: `not rightof(?p) = wall`.

semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Ink0 { pos: Coord, color: Int }   # arc-colour: 0  arc-instances: all
  object Ink1 { pos: Coord, color: Int }   # arc-colour: 1  arc-instances: all
  object Ink2 { pos: Coord, color: Int }   # arc-colour: 2  arc-instances: all
  object Ink3 { pos: Coord, color: Int }   # arc-colour: 3  arc-instances: all
  object Ink4 { pos: Coord, color: Int }   # arc-colour: 4  arc-instances: all
  object Ink5 { pos: Coord, color: Int }   # arc-colour: 5  arc-instances: all
  object Ink6 { pos: Coord, color: Int }   # arc-colour: 6  arc-instances: all
  Ink0 [segment: frame0_colour_0 ev: t1,t2 compress: 12]
  Ink1 [segment: frame0_colour_1 ev: t1,t2,t3,t4,t5 compress: 9]
  Ink2 [segment: frame0_colour_2 ev: t1,t2,t3,t4,t5 compress: 10]
  Ink3 [segment: frame0_colour_3 ev: t1,t2 compress: 8]
  Ink4 [segment: frame0_colour_4 ev: t1,t2 compress: 12]
  Ink5 [segment: frame0_colour_5 ev: t1,t2 compress: 24]
  Ink6 [segment: frame0_colour_6 ev: t1,t2 compress: 22]

events:
  event recolored(o, c)

rules:
  rule a1_icon1_field_takes_6 forall ?p in Ink5 [ev: t1 cov: 14/14]
    when act=key(1) and colored(below(below(below(below(below(below(?p)))))), 6) then recolored(?p, 6)

  rule a1_icon1_field_takes_0 forall ?p in Ink5 [ev: t1 cov: 8/8]
    when act=key(1) and colored(below(below(below(below(below(below(?p)))))), 0) then recolored(?p, 0)

  rule a1_icon1_field_takes_1 forall ?p in Ink5 [ev: t1 cov: 1/1]
    when act=key(1) and colored(below(below(below(below(below(below(?p)))))), 1) then recolored(?p, 1)

  rule a1_icon1_field_takes_2 forall ?p in Ink5 [ev: t1 cov: 1/1]
    when act=key(1) and colored(below(below(below(below(below(below(?p)))))), 2) then recolored(?p, 2)

  rule a1_track_takes_6 forall ?p in Ink3 [ev: t1 cov: 4/4]
    when act=key(1) and colored(below(below(below(below(below(below(?p)))))), 6) then recolored(?p, 6)

  rule a1_track_takes_0 forall ?p in Ink3 [ev: t1 cov: 4/4]
    when act=key(1) and colored(below(below(below(below(below(below(?p)))))), 0) then recolored(?p, 0)

  rule a1_tape1_takes_2 forall ?p in Ink4 [ev: t1 cov: 4/4]
    when act=key(1) and colored(below(below(below(below(below(below(?p)))))), 2) then recolored(?p, 2)

  rule a1_tape1_takes_1 forall ?p in Ink4 [ev: t1 cov: 8/8]
    when act=key(1) and colored(below(below(below(below(below(below(?p)))))), 1) then recolored(?p, 1)

  rule a1_thumb_takes_6 forall ?p in Ink2 [ev: t1 cov: 4/4]
    when act=key(1) and not rightof(?p) = wall and colored(below(below(below(below(below(below(?p)))))), 6) then recolored(?p, 6)

  rule a1_lower_ink2_takes_4 forall ?p in Ink2 [ev: t1 cov: 4/4]
    when act=key(1) and not rightof(?p) = wall and free(below(below(below(below(below(below(?p))))))) and colored(above(above(above(above(above(above(?p)))))), 4) then recolored(?p, 4)

  rule a1_lower_ink2_takes_5 forall ?p in Ink2 [ev: t1 cov: 1/1]
    when act=key(1) and not rightof(?p) = wall and free(below(below(below(below(below(below(?p))))))) and colored(above(above(above(above(above(above(?p)))))), 5) then recolored(?p, 5)

  rule a1_icon2_body_takes_5 forall ?p in Ink6 [ev: t1 cov: 14/14]
    when act=key(1) and colored(above(above(above(above(above(above(?p)))))), 5) then recolored(?p, 5)

  rule a1_icon2_body_takes_3 forall ?p in Ink6 [ev: t1 cov: 4/4]
    when act=key(1) and colored(above(above(above(above(above(above(?p)))))), 3) then recolored(?p, 3)

  rule a1_icon2_body_takes_2 forall ?p in Ink6 [ev: t1 cov: 4/4]
    when act=key(1) and colored(above(above(above(above(above(above(?p)))))), 2) then recolored(?p, 2)

  rule a1_icon2_hole_takes_5 forall ?p in Ink0 [ev: t1 cov: 8/8]
    when act=key(1) and colored(above(above(above(above(above(above(?p)))))), 5) then recolored(?p, 5)

  rule a1_icon2_hole_takes_3 forall ?p in Ink0 [ev: t1 cov: 4/4]
    when act=key(1) and colored(above(above(above(above(above(above(?p)))))), 3) then recolored(?p, 3)

  rule a1_tape2_takes_4 forall ?p in Ink1 [ev: t1 cov: 8/8]
    when act=key(1) and colored(above(above(above(above(above(above(?p)))))), 4) then recolored(?p, 4)

  rule a1_tape2_takes_5 forall ?p in Ink1 [ev: t1 cov: 1/1]
    when act=key(1) and colored(above(above(above(above(above(above(?p)))))), 5) then recolored(?p, 5)

  rule a2_icon1_field_takes_5 forall ?p in Ink5 [ev: t2 cov: 24/24]
    when act=key(2) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule a2_track_takes_3 forall ?p in Ink3 [ev: t2 cov: 8/8]
    when act=key(2) and colored(below(below(below(below(below(below(?p)))))), 3) then recolored(?p, 3)

  rule a2_tape1_takes_4 forall ?p in Ink4 [ev: t2 cov: 12/12]
    when act=key(2) and colored(below(below(below(below(below(below(?p)))))), 4) then recolored(?p, 4)

  rule a2_thumb_takes_2 forall ?p in Ink2 [ev: t2 cov: 4/4]
    when act=key(2) and not rightof(?p) = wall and colored(below(below(below(below(below(below(?p)))))), 2) then recolored(?p, 2)

  rule a2_lower_ink2_takes_2 forall ?p in Ink2 [ev: t2 cov: 5/5]
    when act=key(2) and not rightof(?p) = wall and free(below(below(below(below(below(below(?p))))))) and colored(above(above(above(above(above(above(?p)))))), 2) then recolored(?p, 2)

  rule a2_icon2_body_takes_6 forall ?p in Ink6 [ev: t2 cov: 22/22]
    when act=key(2) and colored(above(above(above(above(above(above(?p)))))), 6) then recolored(?p, 6)

  rule a2_icon2_hole_takes_0 forall ?p in Ink0 [ev: t2 cov: 12/12]
    when act=key(2) and colored(above(above(above(above(above(above(?p)))))), 0) then recolored(?p, 0)

  rule a2_tape2_takes_1 forall ?p in Ink1 [ev: t2 cov: 9/9]
    when act=key(2) and colored(above(above(above(above(above(above(?p)))))), 1) then recolored(?p, 1)

  rule a3_hides_tape2_ones forall ?p in Ink1 [ev: t3 cov: 8/8]
    when act=key(3) and colored(?p, 1) and colored(above(above(?p)), 4) then recolored(?p, 4)

  rule a3_hides_tape2_twos forall ?p in Ink2 [ev: t3 cov: 4/4]
    when act=key(3) and colored(?p, 2) and colored(above(above(?p)), 4) then recolored(?p, 4)

  rule a7_hides_tape2_ones forall ?p in Ink1 [ev: t5 cov: 8/8]
    when act=key(7) and colored(?p, 1) and colored(above(above(?p)), 4) then recolored(?p, 4)

  rule a7_hides_tape2_twos forall ?p in Ink2 [ev: t5 cov: 4/4]
    when act=key(7) and colored(?p, 2) and colored(above(above(?p)), 4) then recolored(?p, 4)

  rule a4_shows_tape2_ones forall ?p in Ink1 [ev: t4 cov: 8/8]
    when act=key(4) and colored(?p, 4) and colored(above(above(?p)), 4) then recolored(?p, 1)

  rule a4_shows_tape2_twos forall ?p in Ink2 [ev: t4 cov: 4/4]
    when act=key(4) and colored(?p, 4) and colored(above(above(?p)), 4) then recolored(?p, 2)

  rule a4_advances_the_corner_pixel forall ?p in Ink2 [ev: t4 cov: 1/1]
    when act=key(4) and colored(?p, 2) and rightof(?p) = wall then recolored(?p, 3)

laws:
  invariant board_cells count(board) = 3999 [status: counted]
  invariant ink0_instances count(Ink0) = 12 [status: derived]
  invariant ink1_instances count(Ink1) = 9 [status: derived]
  invariant ink2_instances count(Ink2) = 10 [status: derived]
  invariant ink3_instances count(Ink3) = 8 [status: derived]
  invariant ink4_instances count(Ink4) = 12 [status: derived]
  invariant ink5_instances count(Ink5) = 24 [status: derived]
  invariant ink6_instances count(Ink6) = 22 [status: derived]
  invariant owned_dynamic_cells count(Ink0) + count(Ink1) + count(Ink2) + count(Ink3) + count(Ink4) + count(Ink5) + count(Ink6) = 97 [status: derived]
  invariant cells_needing_an_owner count(Ink0) + count(Ink1) + count(Ink2) + count(Ink3) + count(Ink4) + count(Ink6) = 73 [status: derived]

  theorem the_swap_is_the_answer_to_last_rounds_declared_hole "THE LOAD-BEARING FACT OF THIS ROUND AND IT COMES FROM certify, NOT FROM ME. certify printed 24 of the 96 divergent cells at t=0 with world_says beside manual_says. Read them: s1(30,11..16) = 6,6,6,6,6,6, s1(31,11..16) = 6,0,0,0,0,6, s1(32,11..16) = 6,0,6,6,0,1, s1(32,17..22) = 2,1,1,2,1,1. Now read the current frame six rows lower: s0(36,11..16) = 6,6,6,6,6,6, s0(37,11..16) = 6,0,0,0,0,6, s0(38,11..16) = 6,0,6,6,0,1, and s0(38,17..22) = 2,1,1,2,1,1 (recovered from the t4 diff's target colours). TWENTY-FOUR OF TWENTY-FOUR AGREE. key(1) replaces every cell of rows 30-41 x cols 11-22 by the cell six rows away, wrapping inside that band: the top block becomes the bottom block and the bottom block becomes the top block. THE COUNT IS AN INDEPENDENT SECOND WITNESS. The band is 12 rows x 12 cols = 72 partner pairs. 24 of those pairs are canvas-4 on both sides -- cols 17-22 at rows 30,31,34,35 paired with rows 36,37,40,41 -- and a swap leaves them untouched, which is precisely why zero_space lists them as constant while listing their neighbours as dynamic. 72 - 24 = 48 pairs that differ, 48 x 2 = 96 cells changed. The diff said 96. Nothing is left over and nothing is unaccounted."
    [depends: the_dynamic_set_is_four_rectangles_and_one_corner_pixel  probe: passed]

  theorem tape1_was_never_shown_it_was_tape2_passing_through "Last round I recorded a puzzle I could not solve: tape1 at rows 32-33 cols 17-22 renders colour 4 in all six observed frames, yet all twelve of its cells are in the dynamic list, so it must have been non-4 in the one frame I was never shown at cell level. The swap answers it exactly. In s1 those twelve cells hold TAPE2's stripes, swapped up six rows, and certify's printout confirms four of them directly: s1(32,17..22) = 2,1,1,2,1,1, which is s0(38,17..22) to the cell. There is no second tape that has been hidden all along. There is ONE strip of stripe content and ONE strip of canvas-4, and A1 exchanges which row band each of them occupies. This retires the reading `A1 shows tape1` in favour of `A1 swaps the two list rows wholesale, tapes included`, and it is the more economical of the two by an entire object."
    [depends: the_swap_is_the_answer_to_last_rounds_declared_hole  probe: passed]

  theorem this_is_a_two_row_list_and_a1_a2_move_between_the_rows "What the swap says the board IS. Rows 30-41 x cols 11-22 is a list of two entries, each six rows tall: an icon in cols 11-16 and a value strip in cols 17-22 occupying the entry's middle two rows. Entry A's icon is the sparse one (a colour-3 pair of columns with a colour-2 two-row segment in it -- a scrollbar thumb, or a slider); entry B's icon is the dense 6x6 colour-6 ring with a colour-0 interior and a colour-6 inner block. A1 and A2 exchange which entry is on top. WITH EXACTLY TWO ENTRIES AND WRAPPING I CANNOT TELL A SWAP FROM A SCROLL-DOWN, and I will not pretend to: scroll-by-one with wrap and swap are the same permutation on two items, and A1 then A2 returning to s0 is consistent with `A2 undoes A1`, with `both are the same swap`, and with `A1 scrolls down, A2 scrolls up`. The separator is one press: press key(1) TWICE from here. If the second press returns the board to its present configuration the list has exactly two entries and A1 is an involution; if a third configuration appears, the list is longer than the window and A1 is a scroll, and every rule I wrote for key(1) is right only for the pair of configurations it witnessed."
    [depends: the_swap_is_the_answer_to_last_rounds_declared_hole  probe: pending]

  theorem the_dynamic_set_is_four_rectangles_and_one_corner_pixel "zero_space's single global law enumerates the cells it constrains and I read them off one by one: (30,11)-(41,16), a 12x6 column band; (32,17)-(32,22) and (33,17)-(33,22); (38,17)-(38,22) and (39,17)-(39,22); and (53,63). That is 72 + 12 + 12 + 1 = 97, and the store says dynamic_cells is 97. The bounding box of that set is rows 30-41 x cols 11-63, which is the reported box [29,10,54,63] padded by one on each side. I name the four parts by what the pixels look like: ICON1 rows 30-35 cols 11-16, ICON2 rows 36-41 cols 11-16, TAPE1 rows 32-33 cols 17-22, TAPE2 rows 38-39 cols 17-22, METER (53,63). Each tape is exactly the middle two rows of its icon, extended six columns right. The swap theorem has since explained WHY tape1 is dynamic although it never renders anything but canvas."
    [probe: passed]

  theorem the_census_closes_to_the_pixel_and_that_is_why_seven_types "Frame-0 colours of all 97 dynamic cells. ICON1: cols 11,12,15,16 x rows 30-35 render 5, that is 24; cols 13,14 x rows 30,31,34,35 render 3, that is 8; cols 13,14 x rows 32,33 render 2, that is 4. ICON2: 22 cells of 6, 12 of 0, plus (38,16)=1 and (39,16)=2. TAPE1: 12 cells of 4. TAPE2: 8 of 1 and 4 of 2. METER: 1 of 2. Totals 0:12, 1:9, 2:10, 3:8, 4:12, 5:24, 6:22, summing to 97. TWO INDEPENDENT CHECKS PASS. 97 - 24 = 73 = cells_needing_an_owner exactly, and the 24 excluded are precisely the background-coloured ones, so `needing an owner` means `dynamic and not background` and Ink5 owns the 24 the store does not count. And 4096 - 97 = 3999 = constant_cells exactly. Seven types and not four because the arm looks objects up by colour and nothing else: a type per frame-0 colour is the ONLY declaration that owns every dynamic cell. It buys no structure and I do not pretend it does -- icon1 is spread across Ink5, Ink3 and Ink2 and no rule can say `icon1`. THE PRICE OF THAT SHOWS UP IN THE SWAP RULES: a copy that would be one line if I could name the icon takes eighteen lines because it must be spelled out per type and per destination colour."
    [depends: the_dynamic_set_is_four_rectangles_and_one_corner_pixel  probe: passed]

  theorem how_the_swap_rules_discriminate_top_from_bottom_and_where_they_could_break "The rules must know whether an instance is in the top block (takes the colour six BELOW) or the bottom block (takes the colour six ABOVE), and there is no positional guard in this language. I use the object types, which are frozen at frame 0 and therefore frozen forever, since instances never move. Ink5 (24), Ink3 (8) and Ink4 (12) live entirely in the top block. Ink6 (22), Ink0 (12) and Ink1 (9) live entirely in the bottom block. Only Ink2 spans both: four instances in icon1's thumb at rows 32-33 cols 13,14, five in the bottom block at (38,17),(38,20),(39,19),(39,22),(39,16), and the meter at (53,63). FOR Ink2 THE SPLIT IS `free(six-below)`. A bottom instance's six-below lands in rows 44-45, background, free in every state. A top instance's six-below lands in the bottom block, and the only way that could render background is if the bottom block held a colour-5 cell there -- which happens exactly when the bottom block holds icon1, i.e. in s1, and there the free cells are icon1's field, which is Ink5 and has no Ink2 among it. So the split is exact on all six observed states. THE METER IS EXCLUDED BY `not rightof(?p) = wall` AND IT MATTERS: (53,63) has (47,63) = 5, so without the wall guard the rule a1_lower_ink2_takes_5 would fire on it if (59,63) happens to render background, and (59,63) is a cell no frame has ever shown me. That single guard is the difference between 96 correct cells and 96 correct plus one wrong."
    [depends: the_swap_is_the_answer_to_last_rounds_declared_hole, the_census_closes_to_the_pixel_and_that_is_why_seven_types  probe: pending]

  theorem the_dsl_cannot_copy_a_colour "The sentence the swap rules are trying to say is `?p takes the colour of the cell six rows away`. The event vocabulary offers recolored(o, <int literal>) and the guard language offers colored(<cell>, <int literal>); neither can carry a colour from one cell to another as a variable. So the copy is spelled out once per (type, destination colour) pair that the witnessed transition actually exhibits: 18 rules for key(1), where the destination colours differ cell by cell, and 8 for key(2), where every instance returns to its own frame-0 colour and one rule per type suffices. THE ENUMERATION IS EXHAUSTIVE OVER THE WITNESS AND I CHECKED THE ARITHMETIC: 14+8+1+1 for Ink5, 4+4 for Ink3, 4+8 for Ink4, 4+4+1 for Ink2, 14+4+4 for Ink6, 8+4 for Ink0, 8+1 for Ink1 sums to 96, and 24+8+12+4+5+22+12+9 for key(2) sums to 96. THE HONEST WARNING: this enumeration is complete for the configuration pair I have seen and for no other. If key(1) from a THIRD configuration ever produces a destination colour I did not enumerate, the instance holding it will silently keep its old colour and replay will show it as a one-cell miss, not as a rule firing wrongly. Read a small divergence under key(1) that way before assuming the swap itself is refuted."
    [depends: how_the_swap_rules_discriminate_top_from_bottom_and_where_they_could_break  probe: pending]

  theorem tape2_is_hidden_and_shown_and_the_guard_that_isolates_it "In s0 the seven cells (38,16)-(38,22) render 1,2,1,1,2,1,1 and (39,16)-(39,22) render 2,1,1,2,1,1,2 -- colour 2 exactly where (row + col) mod 3 = 1 and colour 1 elsewhere, verified on all fourteen. Six of each row, cols 17-22, are dynamic; the col-16 pair is icon2's edge and swaps with the icon. key(3) at t3 and key(7) at t5 turned all twelve dynamic ones to 4, the canvas colour; key(4) at t4 turned all twelve back, each to its own stripe colour. THE GUARD `colored(above(above(?p)), 4)` separates the twelve tape cells from the other Ink1 and Ink2 instances and I checked every one in s0: (38,16) has (36,16)=6, (39,16) has (37,16)=6, the four thumb cells at rows 32,33 cols 13,14 have (30,13)=(30,14)=(31,13)=(31,14)=3, and the meter has (51,63)=5 -- all excluded, while every tape cell has (36,c) or (37,c) = 4. Twelve fire, seven do not, on three transitions."
    [depends: the_dynamic_set_is_four_rectangles_and_one_corner_pixel  probe: passed]

  theorem the_hide_and_show_rules_are_pinned_to_rows_38_39_and_the_swap_makes_that_a_live_question "My hide/show rules are typed on Ink1 and Ink2, and those types live at rows 38-39. After a swap the stripe content sits at rows 32-33 as Ink4 instances, so in s1 my manual predicts key(3) and key(7) do NOTHING and key(4) re-shows stripes at rows 38-39 where tape1's canvas now sits. Two readings are open and I have no evidence between them. (A) THE KEYS ADDRESS A SCREEN ROW: whatever is in the lower entry slot is what hides and shows, and my rules are accidentally right for the wrong reason. (B) THE KEYS ADDRESS AN ENTRY: the stripe strip hides and shows wherever it currently sits, and my rules are wrong in s1 by twelve cells at rows 32-33 plus twelve more they would wrongly paint at rows 38-39. I DID NOT WRITE THE GENERALISED RULES because constraint 2 forbids a rule with no witness, and the generalisation would need Ink4 and Ink5 hide rules that no transition has ever shown. THE SEPARATOR IS TWO PRESSES: key(1), then key(4). Under reading A twelve cells at rows 38-39 change; under reading B twelve cells at rows 32-33 change. The diff distinguishes them at a glance."
    [depends: this_is_a_two_row_list_and_a1_a2_move_between_the_rows, tape2_is_hidden_and_shown_and_the_guard_that_isolates_it  probe: pending]

  theorem the_meter_pixel_has_one_witness_and_three_live_readings "(53,63) went 2 to 3 at t4 and at no other command, including both 96-cell swaps -- so the swap does not touch it, and my Ink2 swap rules exclude it by the wall guard. It sits at the right end of row 53, a row rendering 2 across the window, above row 54 rendering 4: a status bar with one cell consumed at its right edge. THREE READINGS FIT ONE WITNESS. (A) key(4) advances it: 1/1, and the only reading the guard language can express, so it is what I wrote. (B) SHOWING the stripes advances it, whatever key does the showing: also 1/1, since t4 is the only reveal in history. (C) it counts something else -- a score, a budget, a timer -- that ticked once. Command-index parity was refuted here already: it predicted burns at indices 2 and 4 and only 4 burned. THE SEPARATOR AND ITS PREDICTION: the stripes are hidden now and the meter renders 3, so my rule a4_advances_the_corner_pixel cannot fire; press key(4) and my manual predicts EXACTLY TWELVE cells and NO meter change. Thirteen cells refutes the guard colored(?p, 2) and makes the meter a counter rather than a one-shot."
    [depends: tape2_is_hidden_and_shown_and_the_guard_that_isolates_it  probe: pending]

  theorem three_and_seven_are_the_same_key_so_far_and_i_wrote_them_twice "key(3) at t3 and key(7) at t5 produced identical 12-cell effects from states where the stripes were shown. One witness apiece, no state where they differ. THE GRAMMAR HAS NO `or`, so I paid four rules where two would do. TWO THINGS ARE NOT THE SAME ABOUT THEM: key(7) returned ONE frame while key(1), key(2), key(3) and key(4) each returned TWO. cascade_lengths is [1,2] and max_frames_in_one_command is 2, so key(7) is the only single-frame command in this world's history -- a channel my semantics discards by construction, and the only evidence that 3 and 7 are different mechanisms with a coinciding net effect. THE SEPARATOR: press one of them while the stripes are ALREADY HIDDEN, which is the state I am in. If it is `hide`, nothing happens; if it is `toggle`, twelve cells appear. My manual predicts silence there and has NO witness for that silence."
    [depends: tape2_is_hidden_and_shown_and_the_guard_that_isolates_it  probe: pending]

  theorem silence_is_a_prediction_and_i_now_have_fewer_forged_ones "The compiled step is total: where no rule fires the successor equals the current state, so the manual never says `I do not know`, it says `nothing happens`. Audit what it claims from the current state s5, stripes hidden, meter 3. key(1): predicted 96 cells, RULED FROM PIXELS, and the prediction is testable in full next round. key(2): 96 cells, ruled -- but note that key(2) from an s0-shaped state was never witnessed; my key(2) rules are witnessed only from s1, and from here they predict the swap by symmetry, which is a claim rather than a witness. key(3): predicted silent -- the hide rules need colour 1 or 2 and the strip renders 4 -- NO WITNESS. key(7): same, NO WITNESS. key(4): predicted 12 cells and no meter change, and the meter half has NO WITNESS. key(5), key(6): NEVER PRESSED, predicted silent, no witness of any kind. So of seven keys I now have two ruled from pixels, one ruled by symmetry, and four untested claims. Last round the same audit read `an honest witnessed prediction for none of them`."
    [depends: the_swap_is_the_answer_to_last_rounds_declared_hole, three_and_seven_are_the_same_key_so_far_and_i_wrote_them_twice  probe: pending]

  theorem two_keys_have_never_been_pressed_and_one_of_them_is_probably_a_pointer "actions_used is A1 A2 A3 A4 A7 plus RESET; the alphabet is ACTION1..ACTION7. key(5) and key(6) are entirely unconstrained after six states, and they are now the LARGEST unknown on this board, because the swap closed the 96-cell hole and nothing else of comparable size is open. In this action family one command conventionally carries coordinates -- a click -- and that is a prior about the family, not evidence about this world; ACTION7 was used here and ACTION6 was not, which is mild evidence that the usual numbering does not hold. IT MATTERS BECAUSE OF WHAT THE BOARD IS: a two-entry list with icons, value strips, a slider or scrollbar in cols 13-14, a large canvas with an untouched 4x4 colour-14 block at rows 31-34 cols 42-45, and a status bar. That is the anatomy of a MENU, and a menu is a thing you point at and then confirm. I CANNOT WRITE A CLICK RULE: the guard language admits act=key(6) but has nowhere to put two coordinates, so such a rule would fire on every click anywhere and be silently wrong about which cell was clicked. If a pointer drives this world my manual can record its EFFECT and never its precondition."
    [probe: pending]

  theorem what_the_current_frame_shows_outside_the_dynamic_set "All board, none of it earning an object, but written down because the window hides it the moment it stops mattering. Rows 29 and above at cols 10-12 and 15-16 render 5; cols 13,14 render 3 at row 29 and continue upward out of the window unseen -- row 29's pair is CONSTANT while rows 30-35 are dynamic, so the two-wide track extends above the window and only the part inside icon1 varies. The canvas is colour 4 filling rows 29-41 cols 17-46, with a 4x4 colour-14 block at rows 31-34 cols 42-45 unchanged in six frames. Col 47 and beyond in rows 29-41 is background 5. Rows 42-52 are background 5 across the window -- which is what makes `free(six-below)` a sound bottom-block test. Row 53 is colour 2 across the window except (53,63); row 54 is colour 4 across the window. I HAVE NEVER SEEN rows 0-28 or rows 55-63 at any column: colours 8 and 9 appear in colours_seen and I cannot point at a single cell holding them. That is a gap in my knowledge and not in the manual -- those cells are constant, board owns them, and no rule references them. The one place it nearly cost me is (59,63), six below the meter, which is why the meter carries a wall guard rather than a colour guard."
    [probe: passed]

  theorem what_the_engines_gave_me_and_what_certify_gave_me_instead "THE FINDING OF THIS ROUND IS THAT certify OUT-MINED EVERY ENGINE. The 24 printed divergence cells solved the transition that three engines could not touch. zero_space earlier gave me the cell census, and its own verdict on its laws is THIN in its own words -- 5 transitions constrain rank 3 of 679 features, null space dimension 676 -- so I took the cell list and left the law. mdl_segmenter I REJECT WHOLESALE and its own numbers are why: both variants have NEGATIVE gain, -4037 bits and -10409 bits, so by its own measure its segmentation loses to writing the pixels out; its tracks are ~440-cell 13x36 blobs re-identified as new objects whenever any pixel inside changes, which is connected_components(4) failing to separate a widget from the canvas it is drawn on. cegis_miner refused every track with `the world does not narrate as one mover`, and that verdict is TRUE and is now doubly true: the swap moves 96 cells at once and nothing in this world translates a single object across the grid. THE LESSON I AM BANKING: a divergence report is an observation channel, not a scolding. Declaring ignorance loudly enough to be refuted bought me the exact pixels I could not otherwise see."
    [probe: passed]

  theorem there_is_no_goal_section_and_that_is_deliberate "No frame has ever reported anything but NOT_FINISHED and nothing in six states resembles a win. `count(Ink2, color = 3) = 1` is true right now in a state that is plainly not a win. `count(Ink4) = 0` is false at RESET and stays false forever, since instances are fixed by the arm. A goal over the meter would need me to know what the meter counts, and I have one witness and three readings. There is also a structural reason nothing can be named: arc-instances: all gives me Ink2_r53c63 and nine siblings, so there is no single instance to write X.pos = exit_cell about. I name the price plainly: is_goal compiles to False, no plan terminates, nothing ranks one command above another except the playbook -- which is why the playbook is about buying pixels rather than about reaching anything. WHAT WOULD CHANGE THIS: the two unpressed keys, or a click, are the only places a win condition can still be hiding, because every other key's effect is now ruled."
    [depends: the_census_closes_to_the_pixel_and_that_is_why_seven_types, two_keys_have_never_been_pressed_and_one_of_them_is_probably_a_pointer  probe: passed]

  theorem what_i_predict_before_i_see_it "Written in advance so it can cost me. Current state: entry A on top (icon1, thumb at rows 32-33), entry B below (icon2), stripes HIDDEN at rows 38-39, tape1 canvas at rows 32-33, meter renders 3. key(1): EXACTLY 96 cells, rows 30-41 cols 11-22, each taking the colour six rows away, meter untouched -- and I predict the resulting frame will differ from the s1 certify showed me only at rows 32-33 cols 17-22, which will render 4 rather than the stripes, because the stripes are hidden now and were shown then. key(2): the same 96 cells, by symmetry and not by witness. key(3): ZERO cells, NO witness -- twelve cells appearing refutes `hide` in favour of `toggle` and my four hide rules then need converses. key(7): identical experiment plus the one-frame-versus-two-frame question. key(4): EXACTLY TWELVE cells and NO meter change; thirteen refutes colored(?p, 2) in the meter rule. key(5), key(6): predicted silent, never pressed, and if either moves a pixel this manual learns a whole action and possibly the win condition. IF REPLAY IS NOT 5/5 NEXT ROUND, look first at whether the miss is one cell at (53,63) -- that is the wall guard -- and second at whether it is a handful of cells under key(1), which is the enumeration being incomplete rather than the swap being wrong."
    [depends: the_dsl_cannot_copy_a_colour, the_meter_pixel_has_one_witness_and_three_live_readings  probe: pending]

  theorem a_manual_that_does_not_compile_predicts_nothing_at_all "Kept from last round because it is worth more than any rule above. Two rounds ago a thirty-theorem manual scored NOTHING because theory.py could not be loaded: responsibility empty, replay empty, unambiguous null. A manual that does not compile is not a slightly worse manual, it is no manual. TWO RULES FALL OUT AND THIS MANUAL STILL OBEYS THEM. First, prefer constructs that cannot fail to be placed: no landmarks, no goal section, no domain, and every discrimination is a colour or free test on a cell reachable by above/below/leftof/rightof from an instance, plus one `= wall`. Second, when a section is optional, OMIT IT rather than emit it empty. THE ONE NEW RISK I AM TAKING is `not rightof(?p) = wall`, which is `not` applied to a documented atom and appears in five rules. If the whole manual fails to load next round, that construct is the first thing to delete -- and deleting it costs one wrong cell at (53,63) under key(1) and key(2), not the swap."
    [probe: pending]
```

## The playbook as it stands

```
# playbook.dsl -- what to buy with the next command, not a route.
#
# ========= WHERE THIS ROUND STANDS =========
# The 96-cell hole is CLOSED. certify printed 24 of the divergent cells and
# every one of them is the colour six rows below it in the previous frame:
# key(1) swaps the two six-row list entries at rows 30-41 x cols 11-22, and
# key(2) swaps them back. The count checks independently -- 72 partner pairs,
# 24 of them canvas-on-both-sides, 48 differing, 96 cells. Both transitions
# are now ruled from pixels, and tape1's old mystery is dissolved: it was
# never a second strip, it was tape2 passing through after a swap.
#
# THE METHOD THAT WORKED, AND IT IS THE MAIN LESSON:
#   Declaring an ignorance loudly, in writing, with its price named in
#   advance, made the checker print the exact pixels that closed it. A
#   divergence report is an observation channel. Do not shrink the manual's
#   claims to avoid divergence; shrink them to avoid UNPRICED divergence.
#
# ========= THE BOARD AS THE MANUAL NOW SEES IT =========
#   A two-entry list, each entry six rows tall: icon in cols 11-16, value
#   strip in cols 17-22 on the entry's middle two rows. Plus a status bar at
#   row 53 with one consumed pixel at (53,63).
#   RULED FROM PIXELS: key(1) and key(2) swap the entries (96 cells);
#   key(3) and key(7) hide the lower strip (12 cells); key(4) shows it
#   (12 cells) and advanced the meter once.
#   NEVER PRESSED: key(5), key(6). NO GOAL IS KNOWN. Nothing in six states
#   resembles a win, so the win condition can only be hiding in an unpressed
#   key or in a click.
#
# ========= THE FOUR QUESTIONS NOW WORTH MONEY, IN ORDER =========
#   1. WHAT WINS. Two keys have never been pressed and every other key's
#      effect is ruled. That is where a whole mechanism can still be, and it
#      is the only place a goal section can come from.
#   2. HIDE OR TOGGLE. The strip is hidden right now, so a hide-key pressed
#      here does nothing under one reading and shows twelve cells under the
#      other. My manual predicts silence and has NO witness for it. One
#      press, legible in the raw diff.
#   3. SWAP OR SCROLL. With two entries and wrapping, swap and scroll-by-one
#      are the same permutation. Two presses of key(1) separate them: back to
#      here means two entries and an involution, a third configuration means
#      the list is longer than the window and my key(1) enumeration is right
#      only for the pair it witnessed.
#   4. ROW OR ENTRY. Do key(3)/key(4)/key(7) address a screen row or the
#      entry that owns the strip? key(1) then key(4): twelve cells at rows
#      38-39 means row, twelve at rows 32-33 means entry.
#
# ------------------------------------------------------------------------
# Do not re-buy the swap. It is ruled from pixels on both directions and a
# further press of key(1) is worth something only for question 3 or 4, not
# for the swap itself.

order     find_the_win_condition_before_refining_a_ruled_transition       [proof: lean]
order     press_a_key_never_pressed_before_re_pressing_a_ruled_one        [proof: lean]
order     close_a_declared_ignorance_before_refining_a_witnessed_rule     [proof: lean]
order     treat_predicted_silence_as_ignorance_unless_a_witness_backs_it  [proof: lean]
order     rank_by_witnesses_a_command_would_create_not_by_pixels_it_moves [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired [proof: lean]
order     price_an_ignorance_in_advance_so_the_checker_prints_its_pixels  [proof: lean]
order     stop_pressing_a_key_the_moment_its_question_has_been_answered   [proof: lean]
order     separate_two_keys_with_one_effect_before_trusting_either        [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it      [proof: lean]
order     prefer_constructs_that_cannot_fail_to_compile_over_expressive_ones [proof: lean]

prune     every_rule_it_would_witness_is_already_at_full_coverage => dead   [proof: lean]
prune     repeats_a_key_whose_effect_here_is_already_known_cell_by_cell => dead [proof: lean]
prune     ranked_only_because_the_manual_predicts_the_most_pixels => dead   [proof: lean]
prune     ranked_only_because_a_refutation_fired_on_it => dead              [proof: lean]
prune     divergence_lies_only_where_the_manual_declared_ignorance => dead  [proof: lean]
prune     restates_a_transition_the_previous_command_just_answered => dead  [proof: lean]
prune     asks_a_question_the_current_state_cannot_pose => dead             [proof: lean]
prune     would_confirm_a_permutation_already_ruled_in_both_directions => dead [proof: lean]

heuristic keys_never_pressed_in_this_world                                [admissible: lean]
heuristic mechanisms_that_could_still_carry_a_win_condition               [admissible: lean]
heuristic silences_the_manual_asserts_without_a_witness                   [admissible: lean]
heuristic configurations_no_frame_has_ever_shown_in_full                  [admissible: lean]
heuristic live_readings_a_single_command_can_eliminate                    [admissible: lean]
heuristic divergent_cells_lying_outside_a_declared_ignorance              [admissible: lean]
heuristic guards_whose_only_support_is_a_cell_no_frame_has_shown          [admissible: lean]

prefer    an_unpressed_key_over_a_key_already_at_full_coverage            [ev: 2/7 keys]
prefer    a_key_whose_predicted_silence_here_has_never_been_witnessed     [ev: 4/7 keys]
prefer    the_press_that_splits_a_one_shot_from_a_counter                 [ev: 1/1 witnesses]
prefer    the_press_that_splits_a_swap_from_a_scroll                      [ev: 1/1 permutations]
prefer    the_press_that_asks_whether_a_key_addresses_a_row_or_an_entry   [ev: 3/5 diffs]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                [ev: 5/5 diffs]
```

## Why you are being called: the surprises that fired

### replay_mismatch (empirical family -> theory.dsl)

replay diverges at t=0 (frame_mismatch)

```json
{
 "arc_action": "ACTION1",
 "cells": [
  {
   "cell": [
    40,
    13
   ],
   "manual_says": 3,
   "world_says": 5
  },
  {
   "cell": [
    40,
    14
   ],
   "manual_says": 3,
   "world_says": 5
  },
  {
   "cell": [
    41,
    13
   ],
   "manual_says": 3,
   "world_says": 5
  },
  {
   "cell": [
    41,
    14
   ],
   "manual_says": 3,
   "world_says": 5
  }
 ],
 "cells_wrong": 4,
 "kind": "frame_mismatch",
 "t": 0
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
 "first_divergence": {
  "arc_action": "ACTION1",
  "cells": [
   {
    "cell": [
     40,
     13
    ],
    "manual_says": 3,
    "world_says": 5
   },
   {
    "cell": [
     40,
     14
    ],
    "manual_says": 3,
    "world_says": 5
   },
   {
    "cell": [
     41,
     13
    ],
    "manual_says": 3,
    "world_says": 5
   },
   {
    "cell": [
     41,
     14
    ],
    "manual_says": 3,
    "world_says": 5
   }
  ],
  "cells_wrong": 4,
  "kind": "frame_mismatch",
  "t": 0
 },
 "proof_layer_available": false,
 "replay": {
  "detail": "5/9 transitions replay exactly",
  "matched": 5,
  "ok": false,
  "transitions": 9
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
  "detail": "no (state, action) among 10 x 5 admitted two rules, and all 50 pairs were adjudicated -- no call to `step` raised",
  "n_clashes": 0,
  "ok": true,
  "pairs_checked": 50,
  "pairs_nominal": 50,
  "replay_truncated_by_crash": false,
  "sample_cap": 400,
  "scope": "sampled",
  "states": 10,
  "states_reconstructed": 10,
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
=== LOG ===
```json
[
  {"id": "O-01", "subject": "mdl_segmenter tracks obj0..obj6 (13x36, ~440 cells)", "verdict": "reject",
   "why": "Both variants report negative gain (-7528, -7968 bits), so by the engine's own measure the segmentation costs more than the pixels; the tracks are whole-arena blobs re-identified whenever any pixel inside changes, and no such blob could expose a two-column scrollbar occluded by a ring."},

  {"id": "O-02", "subject": "seven colour-typed Ink0..Ink6 with arc-instances: all", "verdict": "accept",
   "as": "unchanged, with Ink2 raised from 10 to 11",
   "why": "Census sums to 98 = dynamic_cells, and 98 - 24 = 74 = cells_needing_an_owner with 24 = count(Ink5); the new eleventh Ink2 instance is (53,62), dynamic since it burned at t8."},

  {"id": "O-03", "subject": "cols 13,14 as a scrollbar independent of both icons", "verdict": "accept",
   "as": "carried in Ink3 (track) and Ink2 (thumb), nameable only in prose",
   "why": "It is the one object explaining why (40,13),(40,14),(41,13),(41,14) take background instead of the colour six rows above -- the track ends at row 39 -- and it agrees with every other cell of col 13 in both configurations plus the constant 3 at (29,13)."},

  {"id": "O-04", "subject": "revising the census to Ink3=4 / Ink5=28", "verdict": "reject",
   "why": "My first reading of world_says=5; the gap between dynamic_cells (98) and cells_needing_an_owner (74) is 24 = count(Ink5), so Ink5 cannot be 28. The error is in the transition, not the frame."},

  {"id": "R-01", "subject": "a1_icon2_hole_takes_3 / a1_icon2_body_takes_3 (old, cov 4/4 each)", "verdict": "reject",
   "why": "They swept up all eight instances having colour 3 six rows above and got four wrong -- exactly the four cells certify printed; each is split into takes_3 (2/2) and past_track_end (2/2) on the disjoint guards colored(above(above(?p)),3) vs colored(above(above(?p)),6)."},

  {"id": "R-02", "subject": "a1_body_past_track_end, a1_hole_past_track_end", "verdict": "accept",
   "why": "2/2 coverage each, painting background at the four cells past the track end; their guards are disjoint from the takes_3 guards, so constraint 5 holds."},

  {"id": "R-03", "subject": "a2_track_end_takes_3", "verdict": "accept",
   "why": "The mirror defect: in a Q state the four Ink3 instances at rows 34,35 have background six rows below them, so colored(six-below,3) covered only 4 of 8; free(six-below) catches the rest and both paint 3."},

  {"id": "R-04", "subject": "a3_burns_the_next_meter_cell", "verdict": "accept",
   "why": "(53,62) went 2->3 at t8 under ACTION3, and the guard colored(rightof(?p),3) is false at t3 because (53,63) still read 2 then; it reproduces the witness and claims nothing about mechanism."},

  {"id": "R-05", "subject": "a2_thumb_takes_2 guard changed from `not rightof = wall` to `not colored(below(?p),4)`", "verdict": "accept",
   "why": "The wall guard excluded (53,63) but not (53,62), leaving the rule resting on the never-observed (59,62); row 54 renders 4 beneath both meter cells and beneath nothing the rule needs."},

  {"id": "R-06", "subject": "generalised hide/show rules over Ink4/Ink5 for a Q-state strip", "verdict": "reject",
   "why": "Constraint 2: no transition has ever hidden or shown a strip at rows 32-33, so the rule would have zero witnesses; the row-versus-entry question is left open in a theorem and one press of key(4) from the current Q state settles it."},

  {"id": "L-01", "subject": "zero_space global law over 98 cells", "verdict": "reject",
   "as": "cell list accepted, law discarded",
   "why": "Its own verdict is THIN -- 9 transitions constrain rank 5 of 686 features, null space dimension 681 -- so the law is unfalsified rather than confirmed; the enumerated cells remain the census I check counts against."},

  {"id": "L-02", "subject": "cegis_miner verdict 'the world does not narrate as one mover'", "verdict": "entailed",
   "why": "Nothing here translates an object across the grid: the large transitions repaint 96 or 72 cells at once and the small ones recolour a strip in place."},

  {"id": "L-03", "subject": "the meter is a wasted-move counter that burns while no stripes are visible", "verdict": "probe-pending",
   "why": "Best fit on six witnesses -- burns at t4 and t8 both followed a hidden strip, non-burns at t3 and t5 both followed a shown one, and key(1)/key(2) pressed three times from hidden states never burned -- but bare parity of {3,4,7} presses fits the same points; one press of key(7) separates them."},

  {"id": "L-04", "subject": "the list is scrolled rather than swapped", "verdict": "probe-pending",
   "why": "A two-item exchange has no reason to move a scroll-position indicator, yet the thumb moved exactly one entry height to sit flush with the track end; this does not count the entries, and two presses of key(1) do."},

  {"id": "L-05", "subject": "key(1) predicted from a Q configuration", "verdict": "probe-pending",
   "why": "Every witnessed key(1) ran from a P state and its guards read cells that swap, so the manual's Q-state key(1) prediction is asserted, not observed -- and it is the largest unwitnessed claim the compiled step now makes."},

  {"id": "E-01", "subject": "the meter's true precondition", "verdict": "probe-pending",
   "as": "wanted `act=key(3) and <no stripe cell shows a stripe colour>`; wrote two rules keyed on the meter cell's right neighbour instead",
   "why": "The guard must read a tape cell fifteen rows and forty columns away and the cell grammar walks one step at a time from an instance; a landmark would say it in one line and I refused to spend one after a total compile failure three rounds ago."},

  {"id": "E-02", "subject": "the third meter burn at (53,61)", "verdict": "reject",
   "as": "wanted a rule burning the next unburned meter cell; wrote nothing",
   "why": "(53,61) has held colour 2 in every frame, so the arm calls it board and gives it no instance; no rule can recolour it. Declared as a structural defect in the manual rather than hidden."},

  {"id": "P-01", "subject": "certify counts 4 failed transitions where my trace counts 6", "verdict": "probe-pending",
   "why": "The scrollbar defect should break key(1) at t1,t6,t9 and key(2) at t2,t7, and the meter burn should break key(3) at t8; I cannot tell which two were forgiven, possibly an artefact of the five commands that returned two frames. I fixed all six sites regardless, so next round's replay count is itself the probe."},

  {"id": "P-02", "subject": "press key(7) from the current hidden-strip Q state", "verdict": "probe-pending",
   "why": "Highest-value single press: it tests hide-versus-toggle, tests whether the burn belongs to key(3) alone, and pits my compiled rules (which compute total silence) against my own meter theorem (which predicts one cell at (53,61) that no rule can draw)."},

  {"id": "P-03", "subject": "press key(5) or key(6)", "verdict": "probe-pending",
   "why": "Never pressed in ten states while every other key is ruled cell by cell; with no goal section anywhere in the manual, an unpressed key is the only place a win condition can still be, and the playbook orders it first."}
]
```
```
