# call-006-theorize-round1

model: `claude-opus-5` · 400930 ms · $1.251219 · usage {"cache_creation": {"ephemeral_1h_input_tokens": 35606, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 35606, "cache_read_input_tokens": 0, "inference_geo": "not_available", "input_tokens": 2, "iterations": [{"cache_creation": {"ephemeral_1h_input_tokens": 35606, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 35606, "cache_read_input_tokens": 0, "input_tokens": 2, "output_tokens": 34736, "type": "message"}], "output_tokens": 34736, "server_tool_use": {"web_fetch_requests": 0, "web_search_requests": 0}, "service_tier": "standard", "speed": "standard"}

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
 "distinct_states": 7,
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
- t8   ACTION1   frames=2   state=NOT_FINISHED 73 cells changed, rows 30-53, cols 11-62, [0, 1, 2, 3, 5, 6] -> [0, 1, 2, 3, 5, 6]
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
    "frames_present": 1,
    "n_cells": 440,
    "shape": [
     13,
     36
    ],
    "track_id": "obj5"
   },
   {
    "color": null,
    "first_frame": 8,
    "frames_present": 2,
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
    "ms": 99,
    "script_bits": 14290,
    "split_by_color": false,
    "tracks": 7
   },
   {
    "baseline_bits": 6762,
    "compression_ratio": 2.17835,
    "events": 92,
    "gain_bits": -7968,
    "ms": 42,
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
  "distinct_states": 7,
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
     "c0@32"
```

The full proposal stream is 1372 rows in `candidates.jsonl`.

## The manual as it stands

```
# theory.dsl -- third edition.
#
# WHAT THE ROUND BOUGHT. Four more commands (t6 A1, t7 A2, t8 A1, t9 A3) and
# they settle three things and open one.
#
# 1. THE REFUTATION IS THE MIRROR OF THE ONE I FIXED LAST ROUND. certify
#    diverges on the ACTION2 transition at exactly four cells: (34,13) (34,14)
#    manual 0 world 3, and (35,13) (35,14) manual 6 world 3. Last round I
#    taught the manual that the bar TRUNCATES going down -- rows 40-41 of the
#    landing site go background instead of 3. I never taught it that the bar
#    REGROWS coming back up. My k2 rules copy the colour from six rows below,
#    and six rows below (34,13) and (35,13) in W1 is background, so nothing
#    fired and the two cells sat still. Two new rules, on BarBody, with the
#    positive guard colored(below^6(?p), 5) -> 3. Coverage 2/2 and 2/2, and
#    they are exclusive against k2_bar_from_frame/k2_bar_from_hollow because
#    those demand colour 3 six rows below. I also CORRECT the coverage I
#    claimed for those two rules: I wrote 4/4 for each and the truth is 2/2
#    each -- the missing two per rule are precisely these four cells. That
#    overclaim is what hid the defect for a round.
#
# 2. THE THREE VACUOUS PROBES HAVE ONE CAUSE AND IT IS THAT DEFECT. P-01,
#    P-02, P-03 each report that every hypothesis including `inert` was
#    refuted and the realised gain was 0.0 bits. That is not a missing
#    mechanism. The probe tier reconstructs the current state by replaying my
#    rules from t0; replay breaks at the SECOND transition, so from t2 onward
#    the manual's internal frame carried those four cells wrong and every
#    predicted hash after it was wrong by at least four cells, ablations
#    included. I predict, before it is run, that the fix restores t1 t2 t3 t4
#    t5 t6 t7 exactly and leaves t8 wrong by ONE cell, (53,62). If a probe
#    stays vacuous after that, the cause is a mechanism and I will have been
#    wrong here in a way that is cheap to read.
#
# 3. THE WORLD IS NOT A FUNCTION OF THE FRAME, AND I CAN PROVE IT FROM THE
#    STORE. distinct_states = 7 over 10 states. S0 = S2 (ACTION2 undid
#    ACTION1) and S5 = S7 (same, later, with both readouts blank); those two
#    coincidences are the only pairs available and they exhaust the count.
#    Now: t6 pressed ACTION1 in S5 and moved 72 cells and NOT the meter; t8
#    pressed ACTION1 in S7 and moved 72 cells AND (53,62) 2->3. Same visible
#    state, same key, different successor. There is hidden state. It ticks at
#    command 4 (ACTION4) and command 8 (ACTION1) -- every fourth command,
#    key-independent -- which kills the reading I encoded last round that
#    ACTION4 advances the meter. See the_meter_is_a_clock_not_a_key.
#
# 4. STILL OPEN, AND ASKABLE ONLY FROM WHERE I STAND: exchange versus scroll.
#    ACTION1 has now been pressed three times and ACTION2 twice, and every one
#    of the five was pressed in the OTHER configuration than its predecessor.
#    ACTION1 has never followed ACTION1. I am in W1 right now, so one command
#    splits the two readings, and I have not spent it.
#
# WHERE I AM. S9 = W1: hollow box in the TOP slot (rows 30-35), bar in the
# BOTTOM slot rendered four rows (rows 36-39, rows 40-41 background), both
# readouts blank, (53,63) and (53,62) both 3. mdl_segmenter corroborates the
# whole reconstruction from outside: its W0 blobs are 440 cells and its W1
# blobs are 436, a difference of exactly the four truncated cells, and its
# frame indices read W1 at 1, W0 at 2-5, W1 at 6, W0 at 7, W1 at 8-9.
#
# THE CENSUS, now 98 cells: 36 top slot + 12 top readout + 36 bottom slot +
# 12 bottom readout + (53,63) + (53,62). BarCore gains the new meter cell and
# becomes 11; board falls to 3998. Both match the store exactly.

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
  Field   [segment: dynamic_colour_5 ev: t0-t9 compress: 24]
  BarBody [segment: dynamic_colour_3 ev: t0-t9 compress: 8]
  BarCore [segment: dynamic_colour_2 ev: t0-t9 compress: 11]
  Blank   [segment: dynamic_colour_4 ev: t0-t9 compress: 12]
  Frame   [segment: dynamic_colour_6 ev: t0-t9 compress: 22]
  Hollow  [segment: dynamic_colour_0 ev: t0-t9 compress: 12]
  Dot     [segment: dynamic_colour_1 ev: t0-t9 compress: 9]

events:
  event recolored(o, c)

rules:
  rule k1_field_to_frame forall ?p in Field [ev: t1,t6,t8 cov: 14/14]
    when act=key(1) and colored(?p, 5) and colored(below(below(below(below(below(below(?p)))))), 6) then recolored(?p, 6)

  rule k1_field_to_hollow forall ?p in Field [ev: t1,t6,t8 cov: 8/8]
    when act=key(1) and colored(?p, 5) and colored(below(below(below(below(below(below(?p)))))), 0) then recolored(?p, 0)

  rule k1_field_to_dot forall ?p in Field [ev: t1,t6,t8 cov: 1/1]
    when act=key(1) and colored(?p, 5) and colored(below(below(below(below(below(below(?p)))))), 1) then recolored(?p, 1)

  rule k1_field_to_core forall ?p in Field [ev: t1,t6,t8 cov: 1/1]
    when act=key(1) and colored(?p, 5) and colored(below(below(below(below(below(below(?p)))))), 2) then recolored(?p, 2)

  rule k1_bar_to_frame forall ?p in BarBody [ev: t1,t6,t8 cov: 4/4]
    when act=key(1) and colored(?p, 3) and colored(below(below(below(below(below(below(?p)))))), 6) then recolored(?p, 6)

  rule k1_bar_to_hollow forall ?p in BarBody [ev: t1,t6,t8 cov: 4/4]
    when act=key(1) and colored(?p, 3) and colored(below(below(below(below(below(below(?p)))))), 0) then recolored(?p, 0)

  rule k1_core_to_frame forall ?p in BarCore [ev: t1,t6,t8 cov: 4/4]
    when act=key(1) and colored(?p, 2) and colored(above(above(?p)), 3) and colored(below(below(below(below(below(below(?p)))))), 6) then recolored(?p, 6)

  rule k1_blank_to_dot forall ?p in Blank [ev: t1 cov: 8/8]
    when act=key(1) and colored(?p, 4) and colored(below(below(below(below(below(below(?p)))))), 1) then recolored(?p, 1)

  rule k1_blank_to_core forall ?p in Blank [ev: t1 cov: 4/4]
    when act=key(1) and colored(?p, 4) and colored(below(below(below(below(below(below(?p)))))), 2) then recolored(?p, 2)

  rule k1_frame_to_field forall ?p in Frame [ev: t1,t6,t8 cov: 14/14]
    when act=key(1) and colored(?p, 6) and colored(above(above(above(above(above(above(?p)))))), 5) then recolored(?p, 5)

  rule k1_frame_to_bar forall ?p in Frame [ev: t1,t6,t8 cov: 2/2]
    when act=key(1) and colored(?p, 6) and colored(above(above(?p)), 3) and colored(above(above(above(above(above(above(?p)))))), 3) then recolored(?p, 3)

  rule k1_frame_clears forall ?p in Frame [ev: t1,t6,t8 cov: 2/2]
    when act=key(1) and colored(?p, 6) and colored(above(above(?p)), 6) and colored(above(above(above(above(above(above(?p)))))), 3) then recolored(?p, 5)

  rule k1_frame_to_core forall ?p in Frame [ev: t1,t6,t8 cov: 4/4]
    when act=key(1) and colored(?p, 6) and colored(above(above(above(above(above(above(?p)))))), 2) then recolored(?p, 2)

  rule k1_hollow_to_field forall ?p in Hollow [ev: t1,t6,t8 cov: 8/8]
    when act=key(1) and colored(?p, 0) and colored(above(above(above(above(above(above(?p)))))), 5) then recolored(?p, 5)

  rule k1_hollow_to_bar forall ?p in Hollow [ev: t1,t6,t8 cov: 2/2]
    when act=key(1) and colored(?p, 0) and colored(above(above(?p)), 3) and colored(above(above(above(above(above(above(?p)))))), 3) then recolored(?p, 3)

  rule k1_hollow_clears forall ?p in Hollow [ev: t1,t6,t8 cov: 2/2]
    when act=key(1) and colored(?p, 0) and colored(above(above(?p)), 6) and colored(above(above(above(above(above(above(?p)))))), 3) then recolored(?p, 5)

  rule k1_dot_to_field forall ?p in Dot [ev: t1,t6,t8 cov: 1/1]
    when act=key(1) and colored(?p, 1) and colored(above(above(above(above(above(above(?p)))))), 5) then recolored(?p, 5)

  rule k1_dot_to_blank forall ?p in Dot [ev: t1 cov: 8/8]
    when act=key(1) and colored(?p, 1) and colored(above(above(above(above(above(above(?p)))))), 4) then recolored(?p, 4)

  rule k1_core_to_field forall ?p in BarCore [ev: t1,t6,t8 cov: 1/1]
    when act=key(1) and colored(?p, 2) and colored(leftof(?p), 0) and colored(above(above(above(above(above(above(?p)))))), 5) then recolored(?p, 5)

  rule k1_core_to_blank forall ?p in BarCore [ev: t1 cov: 4/4]
    when act=key(1) and colored(?p, 2) and colored(leftof(?p), 1) and colored(above(above(above(above(above(above(?p)))))), 4) then recolored(?p, 4)

  rule k2_field_from_frame forall ?p in Field [ev: t2,t7 cov: 14/14]
    when act=key(2) and colored(?p, 6) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule k2_field_from_hollow forall ?p in Field [ev: t2,t7 cov: 8/8]
    when act=key(2) and colored(?p, 0) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule k2_field_from_dot forall ?p in Field [ev: t2,t7 cov: 1/1]
    when act=key(2) and colored(?p, 1) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule k2_field_from_core forall ?p in Field [ev: t2,t7 cov: 1/1]
    when act=key(2) and colored(?p, 2) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule k2_bar_from_frame forall ?p in BarBody [ev: t2,t7 cov: 2/2]
    when act=key(2) and colored(?p, 6) and colored(below(below(below(below(below(below(?p)))))), 3) then recolored(?p, 3)

  rule k2_bar_from_hollow forall ?p in BarBody [ev: t2,t7 cov: 2/2]
    when act=key(2) and colored(?p, 0) and colored(below(below(below(below(below(below(?p)))))), 3) then recolored(?p, 3)

  rule k2_bar_regrows_from_hollow forall ?p in BarBody [ev: t2,t7 cov: 2/2]
    when act=key(2) and colored(?p, 0) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 3)

  rule k2_bar_regrows_from_frame forall ?p in BarBody [ev: t2,t7 cov: 2/2]
    when act=key(2) and colored(?p, 6) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 3)

  rule k2_core_from_frame forall ?p in BarCore [ev: t2,t7 cov: 4/4]
    when act=key(2) and colored(?p, 6) and colored(below(below(below(below(below(below(?p)))))), 2) then recolored(?p, 2)

  rule k2_blank_from_dot forall ?p in Blank [ev: t2 cov: 8/8]
    when act=key(2) and colored(?p, 1) and colored(below(below(below(below(below(below(?p)))))), 4) then recolored(?p, 4)

  rule k2_blank_from_core forall ?p in Blank [ev: t2 cov: 4/4]
    when act=key(2) and colored(?p, 2) and colored(below(below(below(below(below(below(?p)))))), 4) then recolored(?p, 4)

  rule k2_frame_from_field forall ?p in Frame [ev: t2,t7 cov: 16/16]
    when act=key(2) and colored(?p, 5) and colored(above(above(above(above(above(above(?p)))))), 6) then recolored(?p, 6)

  rule k2_frame_from_bar forall ?p in Frame [ev: t2,t7 cov: 2/2]
    when act=key(2) and colored(?p, 3) and colored(above(above(above(above(above(above(?p)))))), 6) then recolored(?p, 6)

  rule k2_frame_from_core forall ?p in Frame [ev: t2,t7 cov: 4/4]
    when act=key(2) and colored(?p, 2) and colored(above(above(above(above(above(above(?p)))))), 6) then recolored(?p, 6)

  rule k2_hollow_from_field forall ?p in Hollow [ev: t2,t7 cov: 10/10]
    when act=key(2) and colored(?p, 5) and colored(above(above(above(above(above(above(?p)))))), 0) then recolored(?p, 0)

  rule k2_hollow_from_bar forall ?p in Hollow [ev: t2,t7 cov: 2/2]
    when act=key(2) and colored(?p, 3) and colored(above(above(above(above(above(above(?p)))))), 0) then recolored(?p, 0)

  rule k2_dot_from_field forall ?p in Dot [ev: t2,t7 cov: 1/1]
    when act=key(2) and colored(?p, 5) and colored(above(above(above(above(above(above(?p)))))), 1) then recolored(?p, 1)

  rule k2_dot_from_blank forall ?p in Dot [ev: t2 cov: 8/8]
    when act=key(2) and colored(?p, 4) and colored(above(above(above(above(above(above(?p)))))), 1) then recolored(?p, 1)

  rule k2_core_from_field forall ?p in BarCore [ev: t2,t7 cov: 1/1]
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

  rule k4_meter_tip_first_advance forall ?s in BarCore [ev: t4 cov: 1/1]
    when act=key(4) and colored(?s, 2) and rightof(?s) = wall then recolored(?s, 3)

  rule k7_dot_blanks forall ?s in Dot [ev: t5 cov: 8/8]
    when act=key(7) and colored(?s, 1) and colored(above(above(above(above(above(above(?s)))))), 4) then recolored(?s, 4)

  rule k7_core_blanks forall ?s in BarCore [ev: t5 cov: 4/4]
    when act=key(7) and colored(?s, 2) and colored(leftof(?s), 1) and colored(above(above(above(above(above(above(?s)))))), 4) then recolored(?s, 4)

laws:
  invariant field_instances count(Field) = 24 [status: census, responsibility reported 0/4096 unexplained last round]
  invariant barbody_instances count(BarBody) = 8 [status: census, responsibility reported 0/4096 unexplained last round]
  invariant barcore_instances count(BarCore) = 11 [status: census updated this round, was 10, gains (53,62) which became dynamic at t8]
  invariant blank_instances count(Blank) = 12 [status: census, responsibility reported 0/4096 unexplained last round]
  invariant frame_instances count(Frame) = 22 [status: census, responsibility reported 0/4096 unexplained last round]
  invariant hollow_instances count(Hollow) = 12 [status: census, responsibility reported 0/4096 unexplained last round]
  invariant dot_instances count(Dot) = 9 [status: census, responsibility reported 0/4096 unexplained last round]
  invariant board_cells count(board) = 3998 [status: matches constant_cells exactly, was 3999 before (53,62) moved]

  theorem the_regrowth_is_the_answer_to_the_replay_mismatch "The surprise names four cells on the ACTION2 transition: (34,13) (34,14) manual 0 world 3, (35,13) (35,14) manual 6 world 3. All four are BarBody instances -- their frame-0 colour is 3 -- and in W1 they carry the box, 0 in the interior rows and 6 in the border row. My k2 BarBody rules both demand colour 3 six rows below, and six rows below them lies rows 40-41 of the bottom slot, which the truncation I fixed last round leaves BACKGROUND. So no rule fired and the four cells stood still. Two rules with the guard colored(below^6, 5) close it, 2/2 and 2/2, and they are exclusive against the existing pair by that colour alone. I ALSO CORRECT AN OVERCLAIM: I had written cov 4/4 on k2_bar_from_frame and k2_bar_from_hollow when each in fact covers 2/2, and that inflated pair of numbers is exactly what hid this defect for a round. The lesson is not about the bar; it is that a coverage figure I did not count is a lie that costs a round."
    [probe: passed]

  theorem the_bar_is_six_rows_above_and_four_below_in_both_directions "Stated as one fact now that both directions are witnessed. The bar reads 3,3 / 3,3 / 2,2 / 2,2 / 3,3 / 3,3 down rows 30-35 at cols 13-14 in the top slot, and 3,3 / 3,3 / 2,2 / 2,2 down rows 36-39 in the bottom, with rows 40-41 background. Going down the last two rows CLEAR; coming up they REGROW as 3. The box, by contrast, renders 22 frame cells and 12 hollow cells in either slot without loss. So the swap is not an information-preserving exchange of two 6x6 windows: the bottom slot is lossy for the bar and the loss is restored from nowhere visible when it comes back. mdl_segmenter says the same from outside without being asked -- its W0 blobs have 440 cells and its W1 blobs 436, and 440 minus 436 is these four cells."
    [depends: the_regrowth_is_the_answer_to_the_replay_mismatch  probe: passed]

  theorem the_world_is_not_a_function_of_the_frame "The strongest result of this round, and it is a negative one. distinct_states = 7 over 10 states, and the only two coincidences available are S0 = S2 and S5 = S7, which exhausts the count exactly. So S5 and S7 are the SAME visible frame: W0, both readouts blank, (53,63) = 3, (53,62) = 2. ACTION1 in S5 changed 72 cells and no meter cell. ACTION1 in S7 changed 73: the same 72 plus (53,62) 2 to 3. Same frame, same key, different successor. There is state this arm cannot see. My compiled step is a function of the frame, so it MUST be wrong somewhere, and I would rather name where than let it look sound."
    [depends: the_bar_is_six_rows_above_and_four_below_in_both_directions  probe: passed]

  theorem the_meter_is_a_clock_not_a_key "Last round I encoded that ACTION4 advances the meter, on one witness, and listed three readings I could not split. t8 splits them and my reading loses. The meter has advanced twice: at command 4 under ACTION4, painting (53,63), and at command 8 under ACTION1, painting (53,62). Two different keys, and the second is a key that had already been pressed twice without advancing it. What both have in common is the COMMAND INDEX: 4 and 8. I read the meter as a clock that ticks every fourth command from RESET and eats row 53 from the right, and I predict the third tick lands on (53,61) at command 12 -- three commands from now. THE GUARD LANGUAGE HAS NO COUNTER, at any length, so this cannot be written as a rule; it is written here instead. I keep k4_meter_tip_first_advance because it reproduces t4 and, since (53,63) is no longer colour 2, it can never fire again and so can never assert the refuted key-attribution a second time."
    [depends: the_world_is_not_a_function_of_the_frame  probe: pending]

  theorem the_three_vacuous_probes_have_one_cause_and_i_name_it_before_the_rerun "P-01, P-02 and P-03 each refuted all 57 hypotheses including inert and returned 0.0 bits against about 1.9 expected. The report reads that as a missing mechanism. I say it is the four-cell defect above, and here is the argument a reader can check: the probe tier reconstructs the present state by replaying my rules from t0, replay first diverges at the SECOND transition, and after that the manual's own frame carries (34,13) (34,14) as 0 and (35,13) (35,14) as 6 forever. Every hypothesis in the frontier is my manual or an ablation of it, so every one of them inherits those four wrong cells and every predicted hash misses. THE FALSIFIABLE PART: with the regrowth rules in, I predict t1 through t7 replay exactly and t8 is wrong by exactly one cell, (53,62), which no rule of mine may claim. If a probe is still vacuous after that, the cause is a mechanism I have not stated and this theorem is refuted."
    [depends: the_regrowth_is_the_answer_to_the_replay_mismatch, the_meter_is_a_clock_not_a_key  probe: pending]

  theorem exchange_versus_scroll_is_still_open_and_i_am_standing_where_it_can_be_asked "READING A, exchange: two slots trade images and the bar simply renders four rows below. READING B, scroll: a list of at least three items steps by six rows, and the four-row glyph in the bottom of W1 is a THIRD ITEM that happens to look like the bar's first four rows. Five swap commands have now been observed -- A1 at t1, A2 at t2, A1 at t6, A2 at t7, A1 at t8 -- and every one of them was pressed in the opposite configuration from its predecessor, so ACTION1 HAS NEVER FOLLOWED ACTION1 and nothing observed splits the two readings. What tilts me slightly to A is the regrowth: under B, the bar's rows 34-35 would have to be redrawn from an item that has scrolled out of view, which is ordinary for a scroll, whereas under A they are redrawn from a slot that never lost them, which needs no memory at all -- but that is taste, not evidence. I am in W1 now. One ACTION1 answers it: A returns W0 exactly and 20 rules generalise, B shows a configuration never seen and my whole word_table is a two-item special case."
    [depends: the_bar_is_six_rows_above_and_four_below_in_both_directions  probe: pending]

  theorem the_readout_belongs_to_the_box_so_i_have_guarded_action4_into_silence "At t1 the LIT readout travelled with the box from rows 38-39 to rows 32-33 -- twelve cells of pattern moved six rows up in the same step the box did. So the readout is bound to the box, not to the slot. ACTION4 has been pressed exactly once, in W0, where the box is at the bottom and its ports (38,16) = 1 and (39,16) = 2 sit at the left edge of the bottom readout. Unguarded, my k4 rules would fire on the Dot and BarCore instances at rows 38-39 in ANY state, and pressed in W1 they would light a strip the box has left, which is a confident wrong drawing of 24 cells and quite likely 24 more left dark. I have therefore added colored(bottom_port, 1) to both, using a landmark at (38,16): it is 1 exactly when the box is in the bottom slot. In W1 the rules now fire on nothing and my manual is SILENT about what ACTION4 does there. That silence is a declared gap, not a claim, and it is cheaper than a fabricated arrangement of 1s and 2s over twelve Blank instances that my type system cannot even tell apart."
    [depends: the_bar_is_six_rows_above_and_four_below_in_both_directions  probe: pending]

  theorem barcore_is_five_unrelated_things_now_and_the_arm_sees_only_colour "Colour 2 at frame 0 sits on the 4-cell core of the bar, the lower port pixel, four dots of the readout, and now TWO meter cells, (53,63) and (53,62), the latter having joined the census when it moved at t8. Eleven instances, one type, because the arm looks objects up by colour alone. The separators are all cells I have read: the bar core has colour 3 two rows above; the readout cores have a colour-1 dot immediately left; the port has colour 0 to its left; the old meter tip is the only instance whose rightof is off-board. I have checked every rule in this file against the new instance (53,62): its left neighbour is 2, its right neighbour is not a wall, two rows above it is background, so no rule of mine grounds on it in any state. It is a cell I own and cannot move, which is exactly the right shape for a clock I cannot read."
    [depends: the_meter_is_a_clock_not_a_key  probe: passed]

  theorem the_swap_rules_are_forty_and_constraint_three_is_still_failed "One law -- take the colour of the cell six away -- is now forty rules, up two. recolored takes an INTEGER LITERAL, so a target colour cannot be read out of a cell and must be named, and the law splits once per source colour, per target colour, per direction, per key. THE CONCEPT DOES NOT PAY FOR ITSELF and I will not dress that up: forty rules to explain 72 cells twice over is worse than a lookup table would be, and I keep it only because the alternative is 96 unexplained pixels. What buys part of it back is that a TYPE IS A FRAME-0 COLOUR: the frame-0 configuration is W0, so a rule's source colour already says which half of the widget the instance lives in, and only the four truncation and regrowth rules need geometry on top of that."
    [depends: the_regrowth_is_the_answer_to_the_replay_mismatch  probe: passed]

  theorem no_goal_section_and_this_is_a_refusal_not_an_oversight "The heuristic_miss is right about the consequence and I accept it: with no goal, is_goal is False everywhere, plan never returns sat, commit never runs, and every command this arm spends is a probe. I still decline to write one, and the reason is arithmetic rather than modesty. Ten states have returned NOT_FINISHED and no other GameState has ever been seen, so no observation distinguishes a win from a non-win. The pos form is dead -- nothing in this world moves, every rule here is a recolour, and cegis_miner refused all seven tracks for exactly that reason. That leaves counts over seven types, and every count I can write names a CONFIGURATION: count(Frame, color = 5) = 14 says the box is up, count(Dot, color = 4) = 8 says the readout is dark, count(BarCore, color = 3) = 2 IS TRUE RIGHT NOW and would make the plan tier declare victory at a state I have no reason to call one. A false goal is worse than none, because it converts a probe budget into a confident wrong plan. WHAT ENDS THIS IS AN OBSERVATION, NOT AN EDIT: a GameState other than NOT_FINISHED, or any cell outside rows 30-41 and row 53 changing at all. ACTION5 and ACTION6 have never been pressed and are the cheapest place to look for it."
    [depends: the_meter_is_a_clock_not_a_key  probe: pending]

  theorem the_silences_i_assert_and_which_of_them_are_forged "The compiled step is total, so where nothing fires I am asserting identity in the same voice I use for what I watched. Audit at S9, which is W1 with both readouts blank. ACTION2: fully predicted, 72 cells, and it is the only action here my manual draws -- the four regrowth cells are the fix on trial. ACTION1: PREDICTED SILENT ON ZERO WITNESSES and this is my largest forgery, 20 rules and one structural reading riding on it; I expect to be wrong and I want to be. ACTION3, ACTION7: predicted silent because the pattern they erase is already erased, and this silence is ENTAILED by witnessed rules rather than forged -- I believe it. ACTION4: predicted silent because bottom_port is 5 here, and that is a declared gap I chose over a wrong drawing. ACTION5, ACTION6: predicted silent, never pressed in ten states, no witness of any kind. And every one of these predictions omits the clock: on the twelfth command since RESET, whatever it is, one extra cell (53,61) turns 3 and I cannot draw it. A probe ranker prices a predicted identity at zero because every ablation agrees with a rule that does not fire, SO THE ACTIONS I MOST NEED ARE THE ONES IT CAN NEVER BUY, and saying so in prose is the only lever this desk has."
    [depends: exchange_versus_scroll_is_still_open_and_i_am_standing_where_it_can_be_asked, the_readout_belongs_to_the_box_so_i_have_guarded_action4_into_silence  probe: pending]

  theorem what_lies_outside_the_widget "Full-frame responsibility means describing the 3998 constant cells, not just naming them board. A colour-4 panel fills rows 29-41 from col 17 to col 46 and carries a 4x4 block of colour 14 at rows 31-34, cols 42-45 -- the only colour-14 anywhere and the only structure on the panel. Both readouts are cut into that panel's left edge, which is why connected_components(4) cannot separate them from it and why every mdl_segmenter blob is a 13x36 slab. Row 29 shows 5,5,3,3,5,5 at cols 11-16 and has NEVER changed: the bar reads seven rows tall on screen while only six of it is alive. Rows 42-52 are background across the window, which is what lets every bottom-half rule test six rows down without a wall test. Row 53 is the clock, all colour 2 except its two rightmost cells, both now 3. Row 54 is a solid colour-4 rule. Colours 8 and 9 appear in colours_seen and on no dynamic cell, so they sit on the board outside this window and have never moved."
    [probe: pending]

  theorem what_the_engines_gave_me "mdl_segmenter reports BOTH variants at negative gain -- minus 7528 bits on 7 tracks, minus 7968 on 38 -- so by its own measure it compressed nothing and I take none of its structure. What I take is a frame-index witness independent of my rules, and this round it is decisive: obj0 has 440 cells at frame 0, obj2 has 436 at frame 1, obj3 has 440 across frames 2-5, obj4 has 436 at frame 6, obj5 has 440 at frame 7, obj6 has 436 across frames 8-9. That is W0 W1 W0 W0 W0 W0 W1 W0 W1 W1, arrived at without any rule of mine, and it matches my state reconstruction cell for cell -- including that the W1 blobs are exactly four cells smaller, which is the truncation. cegis_miner refuses all seven tracks and its verdict that the world does not narrate as one mover is TRUE and remains the strongest negative result available. zero_space self-reports THIN in its own words -- 9 transitions constraining rank 5 of 686 features, null space 681 -- and its one global law is my census with both meter cells appended; I take the corroboration of the cell set and reject the law as unfalsified rather than confirmed, which is what its own report says."
    [probe: passed]

  theorem what_i_predict_before_i_see_it "Written so it can cost me. STATE: S9 = W1, box in the top slot, bar four rows in the bottom, both readouts blank, (53,63) and (53,62) both 3, nine commands since RESET. ACTION1 HERE: my manual says nothing changes; I say that is false, and I name the two outcomes in advance -- 72 cells back to W0 means exchange and 20 rules generalise by symmetry, anything else means scroll and the bottom glyph is a third item. ACTION2 HERE: exactly 72 cells, no readout cell, no row-53 cell, and (34,13) (34,14) (35,13) (35,14) all become 3; anything but 3 at those four refutes the regrowth. ACTION4 HERE: my manual says nothing changes; I expect the twelve cells at rows 32-33, cols 17-22 to light instead, which refutes the silence and confirms that the readout follows the box. ACTION3, ACTION7: nothing changes, and this one I believe. ACTION5, ACTION6: never pressed in ten states; I predict only that whichever is pressed produces the largest single addition to this manual available, and that it is the cheapest place a win condition could come from. THE CLOCK RIDES ON ALL OF THEM: commands 10 and 11 leave row 53 alone, command 12 turns (53,61) from 2 to 3 and I cannot draw it, so a one-cell divergence in row 53 on that command confirms the clock and implicates nothing else in this file."
    [depends: the_silences_i_assert_and_which_of_them_are_forged, no_goal_section_and_this_is_a_refusal_not_an_oversight  probe: pending]
```

## The playbook as it stands

```
# playbook.dsl -- what to buy with the next command, not a route.
#
# STATE: ten states, nine commands (RESET, A1, A2, A3, A4, A7, A1, A2, A1, A3).
# I am in W1: hollow box in the TOP slot, bar four rows in the BOTTOM slot
# (rows 36-39, rows 40-41 background), BOTH readouts blank, (53,63) and
# (53,62) both 3. 98 cells have ever changed; 96 are the widget and 2 are the
# clock.
#
# WHAT CHANGED THIS ROUND.
#  * The four-cell replay defect was the MIRROR of last round's: the bar
#    truncates going down and REGROWS coming up, and my ACTION2 rules had no
#    way to say so. Two rules added; two coverage figures I had inflated to
#    4/4 corrected to 2/2. That inflation is what hid the defect for a round.
#  * The three vacuous probes are downstream of that one defect, not evidence
#    of a missing mechanism. Every hypothesis in the frontier is my manual or
#    an ablation, so all 57 inherited the same four wrong cells.
#  * THE WORLD HAS HIDDEN STATE. S5 and S7 are the same frame; ACTION1 in S5
#    moved 72 cells, ACTION1 in S7 moved 73. The extra cell is the clock,
#    which ticks at command 4 and command 8 -- every fourth command, whatever
#    the key. My rule that ACTION4 advances it is refuted as an attribution
#    and survives only because it can never fire again.
#  * ACTION4 is now guarded into silence outside W0, because the readout
#    travels with the box and firing it in W1 would draw 24 cells wrong.
#
# THE QUESTION THAT ONLY THIS STATE CAN ASK
#   ACTION1 has been pressed three times and ACTION2 twice, and every press
#   was in the opposite configuration from its predecessor -- ACTION1 HAS
#   NEVER FOLLOWED ACTION1. Exchange and scroll are therefore still both
#   alive. I am standing in W1, where one ACTION1 splits them: exchange
#   returns W0 exactly, scroll shows a configuration never seen. If I spend
#   this command on anything that leaves W1, the question costs two commands
#   instead of one.
#
# WHAT IS GENUINELY UNKNOWN
#   * ACTION5 and ACTION6: never pressed in ten states. Zero constraint.
#   * ACTION1 in W1, ACTION2 in W0, ACTION4 in W1, ACTION3/7 in W1-lit: all
#     silences with no witness behind them.
#   * The clock's period is fitted to two ticks. 4 and 8 fit every-fourth;
#     they also fit other arithmetics I cannot write either.
#   * The win condition. Nothing countable separates a win from here, no
#     GameState but NOT_FINISHED has ever been returned, and I refuse to
#     invent one -- see no_goal_section_and_this_is_a_refusal_not_an_oversight.
#     The plan tier's silence is a true report of my ignorance.
#
# PRICES ADVERTISED IN ADVANCE, SO A REFUTATION ON THEM IMPLICATES NOTHING
#   * The clock is undrawable one cell ahead of itself. (53,61) is board and
#     holds no instance, so command 12 costs exactly one pixel of accuracy
#     and every fourth command after it costs one more, permanently.
#   * ACTION1 here is predicted SILENT and I expect that to be wrong.
#   * ACTION4 here is predicted SILENT by a guard I added on purpose; if the
#     top readout lights, the guard was right about the box and wrong about
#     the silence, and that is a purchase.
#   * ACTION2 here is predicted at exactly 72 cells with the four regrowth
#     cells turning 3. That is the whole fix on trial in one command.
#
# THE RANKED LIST
# 1. ACTION1, HERE, IN W1. The only command that splits exchange from scroll,
#    the largest forged silence in the manual (20 rules), and it is askable
#    only from the configuration I am standing in. Three legible outcomes:
#    W0 exactly, a new configuration, or nothing.
# 2. ACTION5 or ACTION6. Never pressed in ten states. Any outcome is the
#    largest single addition available -- including nothing, which would be
#    the first WITNESSED inertness here -- and it is the cheapest place a win
#    condition could come from. Askable from any state, which is why it sits
#    below a probe that is not.
# 3. ACTION4, HERE. Tests the guard I just added and the readout-follows-box
#    reading in one press, and lights the readout so the A1/A2 readout rules
#    can be re-witnessed in the other configuration.
# 4. Any three commands in a row, to watch command 12. Confirms or kills the
#    clock, and the answer is legible in the raw diff as one cell of row 53.
#
# WHAT NOT TO PRESS
#   ACTION3 or ACTION7 here: the pattern they erase is already erased, my
#   manual predicts identity AND I believe it. Confirmed silence, no witness.
#   ACTION2 here: it repeats t7 from a state identical to t7's, so it buys
#   only what replay already tells me for free.
#   Anything chosen because my manual predicts the most pixels for it: that
#   number measures my coverage, not the world's information.

order     spend_a_probe_only_the_current_state_can_ask_before_one_askable_anywhere [proof: lean]
order     press_an_action_never_pressed_before_repressing_a_modelled_one    [proof: lean]
order     press_a_modelled_action_in_a_configuration_it_was_never_pressed_in [proof: lean]
order     test_a_silence_that_rests_on_no_witness_before_one_that_is_entailed [proof: lean]
order     score_an_unwitnessed_silence_above_a_witnessed_repetition         [proof: lean]
order     treat_an_action_the_manual_calls_silent_as_unprobeable_not_untested [proof: lean]
order     prefer_a_probe_with_three_distinct_legible_outcomes_over_one_with_two [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired   [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance                [proof: lean]
order     suspect_the_replay_before_the_mechanism_when_every_hypothesis_dies [proof: lean]
order     count_a_coverage_figure_before_writing_it_down                    [proof: lean]
order     look_for_the_mirror_of_a_fixed_defect_in_the_reverse_direction    [proof: lean]
order     guard_a_rule_into_silence_before_letting_it_draw_an_unwitnessed_state [proof: lean]
order     name_the_hidden_state_rather_than_key_a_rule_to_the_wrong_cause   [proof: lean]
order     keep_a_refuted_attribution_only_while_it_can_never_fire_again     [proof: lean]
order     separate_same_coloured_roles_by_a_cell_you_have_actually_read     [proof: lean]
order     prefer_a_landmark_guard_over_a_chain_of_cell_operators            [proof: lean]
order     search_the_engine_report_for_a_count_that_matches_the_divergence  [proof: lean]
order     prefer_a_positive_colour_test_over_a_negated_wall_test            [proof: lean]
order     patch_a_manual_whose_divergence_is_four_cells_rather_than_replacing_it [proof: lean]
order     buy_the_observation_that_makes_a_goal_writable_before_writing_one [proof: lean]
order     extend_the_transition_model_before_extending_the_goal_language    [proof: lean]
order     refuse_a_goal_no_observation_distinguishes_and_say_so_out_loud    [proof: lean]
order     emit_every_required_block_before_polishing_any_of_them            [proof: lean]

prune     rule_proposed_with_zero_witnesses_of_any_kind => dead             [proof: lean]
prune     rule_whose_two_witnesses_demand_opposite_outcomes_from_one_frame => dead [proof: lean]
prune     rule_that_would_forge_the_reverse_direction_of_an_unobserved_press => dead [proof: lean]
prune     guard_conjunct_with_no_negative_witness_and_no_explained_pixel => dead [proof: lean]
prune     goal_clause_over_a_type_with_zero_instances => dead               [proof: lean]
prune     goal_that_is_already_true_at_the_current_state => dead            [proof: lean]
prune     goal_satisfiable_without_leaving_the_two_widget_configurations => dead [proof: lean]
prune     goal_no_observed_gamestate_could_have_distinguished => dead       [proof: lean]
prune     divergence_lies_only_on_a_cell_that_had_never_changed => dead     [proof: lean]
prune     divergence_lies_only_on_the_unadvanced_clock_frontier => dead     [proof: lean]
prune     repeats_a_key_whose_inertness_here_is_entailed_by_witnessed_rules => dead [proof: lean]
prune     repeats_a_transition_already_witnessed_from_an_identical_frame => dead [proof: lean]
prune     ranked_only_because_the_manual_predicts_the_most_pixels => dead   [proof: lean]
prune     leaves_the_only_configuration_that_can_ask_the_open_question => dead [proof: lean]
prune     every_rule_it_would_witness_is_already_at_full_coverage => dead   [proof: lean]

heuristic actions_of_the_alphabet_never_yet_pressed                         [admissible: lean]
heuristic configurations_in_which_a_known_key_has_never_been_pressed        [admissible: lean]
heuristic silences_of_the_manual_that_rest_on_no_witness                    [admissible: lean]
heuristic structural_readings_a_single_command_could_eliminate              [admissible: lean]
heuristic rules_that_one_command_could_generalise_or_refute_together        [admissible: lean]
heuristic distinct_legible_outcomes_a_single_command_can_produce            [admissible: lean]
heuristic questions_that_only_the_present_configuration_can_ask             [admissible: lean]
heuristic pairs_of_identical_frames_with_different_successors               [admissible: lean]
heuristic commands_remaining_before_the_clock_ticks_again                   [admissible: lean]
heuristic widget_configurations_never_yet_observed                          [admissible: lean]
heuristic cells_outside_the_widget_a_command_could_turn_dynamic             [admissible: lean]
heuristic cells_whose_first_change_would_make_a_goal_line_writable          [admissible: lean]
heuristic gamestates_other_than_not_finished_ever_returned                  [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_advertised_prices            [admissible: lean]
heuristic fitted_guards_a_command_could_convert_into_witnessed_ones         [admissible: lean]

prefer    a_command_that_splits_two_named_readings_in_one_press             [ev: 1/1 available]
prefer    a_probe_askable_only_from_the_configuration_now_showing           [ev: 1/2 configurations]
prefer    a_key_never_pressed_in_any_state                                  [ev: 2/7 keys]
prefer    a_key_never_pressed_in_the_configuration_now_showing              [ev: 3/5 pressed keys]
prefer    a_command_that_tests_twenty_rules_at_once                         [ev: 2/2 available]
prefer    a_command_that_would_turn_a_cell_outside_the_widget_dynamic       [ev: 2/10 states]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                  [ev: 9/9 diffs]
prefer    a_command_that_would_produce_a_third_widget_configuration         [ev: 0/10 states so far]
prefer    a_command_that_could_return_a_gamestate_never_yet_seen            [ev: 0/10 states so far]
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
  "detail": "7/9 transitions replay exactly",
  "matched": 7,
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
=== THEORY ===
```
# theory.dsl -- fourth edition.
#
# WHAT THIS ROUND BOUGHT. One command (t9, ACTION3, zero cells changed) and a
# certify report, and between them they settle four things.
#
# 1. THE REGROWTH FIX HELD, AND THE PREDICTION I ATTACHED TO IT WAS EXACT.
#    Last round I wrote, before the rerun: "with the regrowth rules in, I
#    predict t1 through t7 replay exactly and t8 is wrong by exactly one cell,
#    (53,62), which no rule of mine may claim." certify now reports 7/9
#    transitions replaying exactly, first divergence at transition index 7
#    (the ACTION1 command), one cell wrong, (53,62), manual 2 world 3. That is
#    the sentence I wrote, returned to me by the machine. The four-cell
#    ACTION2 defect is gone; responsibility is 0/4096 unexplained; ambiguity
#    is 0 clashes over all 50 adjudicated pairs.
#
# 2. THE SURPRISE IS THE PRICE I ADVERTISED, AND I REFUSE TO PATCH IT. The
#    replay_mismatch names (53,62) and nothing else. The guard language has no
#    counter, so a clock that ticks on the command index cannot be written as
#    a rule at any length; the only rules that would draw that cell would fire
#    on every command and be wrong on three commands out of four. I take the
#    one-cell error permanently and keep saying where it comes from. See
#    the_only_divergence_left_is_the_one_i_priced_in_advance.
#
# 3. THE REPLAY IS CUMULATIVE, AND I CAN READ THAT OFF THE COUNTS. Two
#    transitions failed (7 matched of 9) but only one divergence is named.
#    t9's ACTION3 is an identity in the world and an identity in my manual, so
#    a one-step replay would have matched it and reported 8/9. It reported
#    7/9, so the replay carries my state forward and transition 8 inherits the
#    same single wrong cell. Every future transition inherits it too. The cost
#    is one cell, not one cell per command.
#
# 4. I CORRECT AN ARITHMETIC ERROR OF MY OWN, AND t9 IS WHAT FIXED IT. Last
#    edition I wrote that distinct_states = 7 over 10 states is exhausted by
#    S0 = S2 and S5 = S7. Ten states with seven distinct needs THREE
#    coincidences, not two. The third is S8 = S9: ACTION3 at t9 changed
#    nothing, which is the FIRST WITNESSED INERTNESS in this world's history
#    and closes the count exactly. mdl_segmenter corroborates it from outside
#    -- its obj6 now spans frames 8-9 where last round it spanned only 8. The
#    hidden-state argument is untouched: S5 = S7 still have different
#    successors under the same key.
#
# 5. THE CLOCK SURVIVES A DISCRIMINATION I HAD NOT RUN. Ticks at command 4 and
#    command 8; commands 1,2,3,5,6,7,9 left row 53 alone. A rival counter --
#    "every fourth command that returned two frames" -- is now REFUTED: t4 is
#    the 4th two-frame command but t8 is the 7th, and t5 and t9 returned one
#    frame each. The plain command index survives; the next tick is command 12
#    and lands on (53,61).
#
# WHERE I AM. S9 = S8 = W1: hollow box in the TOP slot (rows 30-35, border 6,
# hollow 0, a 2x2 core of 6 at rows 32-33 cols 13-14, ports 1 and 2 at
# (32,16) and (33,16)); bar in the BOTTOM slot rendered four rows (36-39,
# rows 40-41 background); both readouts blank; (53,63) and (53,62) both 3.
# Nine commands since RESET. Read straight off the current frame, and it
# agrees with the manual cell for cell.
#
# THE CENSUS, 98 cells, and it now decomposes twice over. 24 Field + 8 BarBody
# + 11 BarCore + 12 Blank + 22 Frame + 12 Hollow + 9 Dot = 98 = dynamic_cells.
# Separately, cells_needing_an_owner = 74 = 98 - 24, and 24 is exactly the
# Field count: the store is counting dynamic cells that are NOT background at
# frame 0, and my one background-coloured type covers the difference. Two
# independent numbers in the store land on my type table without adjustment.

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
  Field   [segment: dynamic_colour_5 ev: t0-t9 compress: 24]
  BarBody [segment: dynamic_colour_3 ev: t0-t9 compress: 8]
  BarCore [segment: dynamic_colour_2 ev: t0-t9 compress: 11]
  Blank   [segment: dynamic_colour_4 ev: t0-t9 compress: 12]
  Frame   [segment: dynamic_colour_6 ev: t0-t9 compress: 22]
  Hollow  [segment: dynamic_colour_0 ev: t0-t9 compress: 12]
  Dot     [segment: dynamic_colour_1 ev: t0-t9 compress: 9]

events:
  event recolored(o, c)

rules:
  rule k1_field_to_frame forall ?p in Field [ev: t1,t6,t8 cov: 14/14]
    when act=key(1) and colored(?p, 5) and colored(below(below(below(below(below(below(?p)))))), 6) then recolored(?p, 6)

  rule k1_field_to_hollow forall ?p in Field [ev: t1,t6,t8 cov: 8/8]
    when act=key(1) and colored(?p, 5) and colored(below(below(below(below(below(below(?p)))))), 0) then recolored(?p, 0)

  rule k1_field_to_dot forall ?p in Field [ev: t1,t6,t8 cov: 1/1]
    when act=key(1) and colored(?p, 5) and colored(below(below(below(below(below(below(?p)))))), 1) then recolored(?p, 1)

  rule k1_field_to_core forall ?p in Field [ev: t1,t6,t8 cov: 1/1]
    when act=key(1) and colored(?p, 5) and colored(below(below(below(below(below(below(?p)))))), 2) then recolored(?p, 2)

  rule k1_bar_to_frame forall ?p in BarBody [ev: t1,t6,t8 cov: 4/4]
    when act=key(1) and colored(?p, 3) and colored(below(below(below(below(below(below(?p)))))), 6) then recolored(?p, 6)

  rule k1_bar_to_hollow forall ?p in BarBody [ev: t1,t6,t8 cov: 4/4]
    when act=key(1) and colored(?p, 3) and colored(below(below(below(below(below(below(?p)))))), 0) then recolored(?p, 0)

  rule k1_core_to_frame forall ?p in BarCore [ev: t1,t6,t8 cov: 4/4]
    when act=key(1) and colored(?p, 2) and colored(above(above(?p)), 3) and colored(below(below(below(below(below(below(?p)))))), 6) then recolored(?p, 6)

  rule k1_blank_to_dot forall ?p in Blank [ev: t1 cov: 8/8]
    when act=key(1) and colored(?p, 4) and colored(below(below(below(below(below(below(?p)))))), 1) then recolored(?p, 1)

  rule k1_blank_to_core forall ?p in Blank [ev: t1 cov: 4/4]
    when act=key(1) and colored(?p, 4) and colored(below(below(below(below(below(below(?p)))))), 2) then recolored(?p, 2)

  rule k1_frame_to_field forall ?p in Frame [ev: t1,t6,t8 cov: 14/14]
    when act=key(1) and colored(?p, 6) and colored(above(above(above(above(above(above(?p)))))), 5) then recolored(?p, 5)

  rule k1_frame_to_bar forall ?p in Frame [ev: t1,t6,t8 cov: 2/2]
    when act=key(1) and colored(?p, 6) and colored(above(above(?p)), 3) and colored(above(above(above(above(above(above(?p)))))), 3) then recolored(?p, 3)

  rule k1_frame_clears forall ?p in Frame [ev: t1,t6,t8 cov: 2/2]
    when act=key(1) and colored(?p, 6) and colored(above(above(?p)), 6) and colored(above(above(above(above(above(above(?p)))))), 3) then recolored(?p, 5)

  rule k1_frame_to_core forall ?p in Frame [ev: t1,t6,t8 cov: 4/4]
    when act=key(1) and colored(?p, 6) and colored(above(above(above(above(above(above(?p)))))), 2) then recolored(?p, 2)

  rule k1_hollow_to_field forall ?p in Hollow [ev: t1,t6,t8 cov: 8/8]
    when act=key(1) and colored(?p, 0) and colored(above(above(above(above(above(above(?p)))))), 5) then recolored(?p, 5)

  rule k1_hollow_to_bar forall ?p in Hollow [ev: t1,t6,t8 cov: 2/2]
    when act=key(1) and colored(?p, 0) and colored(above(above(?p)), 3) and colored(above(above(above(above(above(above(?p)))))), 3) then recolored(?p, 3)

  rule k1_hollow_clears forall ?p in Hollow [ev: t1,t6,t8 cov: 2/2]
    when act=key(1) and colored(?p, 0) and colored(above(above(?p)), 6) and colored(above(above(above(above(above(above(?p)))))), 3) then recolored(?p, 5)

  rule k1_dot_to_field forall ?p in Dot [ev: t1,t6,t8 cov: 1/1]
    when act=key(1) and colored(?p, 1) and colored(above(above(above(above(above(above(?p)))))), 5) then recolored(?p, 5)

  rule k1_dot_to_blank forall ?p in Dot [ev: t1 cov: 8/8]
    when act=key(1) and colored(?p, 1) and colored(above(above(above(above(above(above(?p)))))), 4) then recolored(?p, 4)

  rule k1_core_to_field forall ?p in BarCore [ev: t1,t6,t8 cov: 1/1]
    when act=key(1) and colored(?p, 2) and colored(leftof(?p), 0) and colored(above(above(above(above(above(above(?p)))))), 5) then recolored(?p, 5)

  rule k1_core_to_blank forall ?p in BarCore [ev: t1 cov: 4/4]
    when act=key(1) and colored(?p, 2) and colored(leftof(?p), 1) and colored(above(above(above(above(above(above(?p)))))), 4) then recolored(?p, 4)

  rule k2_field_from_frame forall ?p in Field [ev: t2,t7 cov: 14/14]
    when act=key(2) and colored(?p, 6) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule k2_field_from_hollow forall ?p in Field [ev: t2,t7 cov: 8/8]
    when act=key(2) and colored(?p, 0) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule k2_field_from_dot forall ?p in Field [ev: t2,t7 cov: 1/1]
    when act=key(2) and colored(?p, 1) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule k2_field_from_core forall ?p in Field [ev: t2,t7 cov: 1/1]
    when act=key(2) and colored(?p, 2) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule k2_bar_from_frame forall ?p in BarBody [ev: t2,t7 cov: 2/2]
    when act=key(2) and colored(?p, 6) and colored(below(below(below(below(below(below(?p)))))), 3) then recolored(?p, 3)

  rule k2_bar_from_hollow forall ?p in BarBody [ev: t2,t7 cov: 2/2]
    when act=key(2) and colored(?p, 0) and colored(below(below(below(below(below(below(?p)))))), 3) then recolored(?p, 3)

  rule k2_bar_regrows_from_hollow forall ?p in BarBody [ev: t2,t7 cov: 2/2]
    when act=key(2) and colored(?p, 0) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 3)

  rule k2_bar_regrows_from_frame forall ?p in BarBody [ev: t2,t7 cov: 2/2]
    when act=key(2) and colored(?p, 6) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 3)

  rule k2_core_from_frame forall ?p in BarCore [ev: t2,t7 cov: 4/4]
    when act=key(2) and colored(?p, 6) and colored(below(below(below(below(below(below(?p)))))), 2) then recolored(?p, 2)

  rule k2_blank_from_dot forall ?p in Blank [ev: t2 cov: 8/8]
    when act=key(2) and colored(?p, 1) and colored(below(below(below(below(below(below(?p)))))), 4) then recolored(?p, 4)

  rule k2_blank_from_core forall ?p in Blank [ev: t2 cov: 4/4]
    when act=key(2) and colored(?p, 2) and colored(below(below(below(below(below(below(?p)))))), 4) then recolored(?p, 4)

  rule k2_frame_from_field forall ?p in Frame [ev: t2,t7 cov: 16/16]
    when act=key(2) and colored(?p, 5) and colored(above(above(above(above(above(above(?p)))))), 6) then recolored(?p, 6)

  rule k2_frame_from_bar forall ?p in Frame [ev: t2,t7 cov: 2/2]
    when act=key(2) and colored(?p, 3) and colored(above(above(above(above(above(above(?p)))))), 6) then recolored(?p, 6)

  rule k2_frame_from_core forall ?p in Frame [ev: t2,t7 cov: 4/4]
    when act=key(2) and colored(?p, 2) and colored(above(above(above(above(above(above(?p)))))), 6) then recolored(?p, 6)

  rule k2_hollow_from_field forall ?p in Hollow [ev: t2,t7 cov: 10/10]
    when act=key(2) and colored(?p, 5) and colored(above(above(above(above(above(above(?p)))))), 0) then recolored(?p, 0)

  rule k2_hollow_from_bar forall ?p in Hollow [ev: t2,t7 cov: 2/2]
    when act=key(2) and colored(?p, 3) and colored(above(above(above(above(above(above(?p)))))), 0) then recolored(?p, 0)

  rule k2_dot_from_field forall ?p in Dot [ev: t2,t7 cov: 1/1]
    when act=key(2) and colored(?p, 5) and colored(above(above(above(above(above(above(?p)))))), 1) then recolored(?p, 1)

  rule k2_dot_from_blank forall ?p in Dot [ev: t2 cov: 8/8]
    when act=key(2) and colored(?p, 4) and colored(above(above(above(above(above(above(?p)))))), 1) then recolored(?p, 1)

  rule k2_core_from_field forall ?p in BarCore [ev: t2,t7 cov: 1/1]
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

  rule k4_meter_tip_first_advance forall ?s in BarCore [ev: t4 cov: 1/1]
    when act=key(4) and colored(?s, 2) and rightof(?s) = wall then recolored(?s, 3)

  rule k7_dot_blanks forall ?s in Dot [ev: t5 cov: 8/8]
    when act=key(7) and colored(?s, 1) and colored(above(above(above(above(above(above(?s)))))), 4) then recolored(?s, 4)

  rule k7_core_blanks forall ?s in BarCore [ev: t5 cov: 4/4]
    when act=key(7) and colored(?s, 2) and colored(leftof(?s), 1) and colored(above(above(above(above(above(above(?s)))))), 4) then recolored(?s, 4)

laws:
  invariant field_instances count(Field) = 24 [status: census, and 98 minus 24 is exactly cells_needing_an_owner = 74]
  invariant barbody_instances count(BarBody) = 8 [status: census, responsibility reported 0/4096 unexplained this round]
  invariant barcore_instances count(BarCore) = 11 [status: census, includes both meter cells (53,63) and (53,62)]
  invariant blank_instances count(Blank) = 12 [status: census, responsibility reported 0/4096 unexplained this round]
  invariant frame_instances count(Frame) = 22 [status: census, matches the 22 colour-6 cells I count in the current frame's box]
  invariant hollow_instances count(Hollow) = 12 [status: census, matches the 12 colour-0 cells I count in the current frame's box]
  invariant dot_instances count(Dot) = 9 [status: census, responsibility reported 0/4096 unexplained this round]
  invariant board_cells count(board) = 3998 [status: matches constant_cells exactly]

  theorem the_only_divergence_left_is_the_one_i_priced_in_advance "The surprise names one cell, (53,62), manual 2 world 3, on the ACTION1 command at index 7 -- and last edition, in writing, before the rerun, I named that exact cell on that exact command as the one thing my manual may not draw. certify agrees on everything else: 7/9 transitions replay exactly, 0/4096 pixels unexplained, 0 ambiguity clashes over all 50 adjudicated pairs. I therefore make NO CHANGE in response to this surprise, and I say why rather than letting the silence look like an oversight. The tick is keyed to the command index; the guard language has cells, colours, adjacency and off-board tests and NO COUNTER of any length; and any rule that could paint (53,62) from what the frame shows -- say, a colour-2 cell whose right neighbour is 3 -- would fire on commands 9, 10 and 11 as well, buying one right cell at the price of three wrong ones. A permanent one-cell error I can locate and explain is worth more than a rule that is wrong three times in four."
    [depends: the_meter_is_a_clock_not_a_key  probe: passed]

  theorem the_replay_is_cumulative_and_one_cell_contaminates_every_later_frame "certify reports matched 7 of 9 with exactly ONE first divergence. Transition 8 is t9's ACTION3, which changed nothing in the world and fires nothing in my manual, so a one-step replay from the true previous frame would have matched it and reported 8/9. It reported 7/9. The replay must therefore carry MY reconstructed state forward, and transition 8 fails only by inheriting the (53,62) cell that transition 7 got wrong. This matters twice. First, it bounds the damage: the error is one cell held forever, not one cell added per command, until the next tick makes it two. Second, it is the mechanism I blamed last round for three vacuous probes, now demonstrated on a case where I know the answer independently -- a single wrong cell propagates to every downstream hypothesis whether or not that hypothesis has anything to do with it."
    [depends: the_only_divergence_left_is_the_one_i_priced_in_advance  probe: passed]

  theorem the_regrowth_fix_is_confirmed_and_the_prediction_that_confirmed_it_was_dated "I wrote: with the regrowth rules in, t1 through t7 replay exactly and t8 is wrong by exactly one cell, (53,62). certify: first divergence at index 7, one cell, (53,62). No ACTION2 cell appears anywhere in the report, so (34,13) (34,14) (35,13) (35,14) now replay correctly and the two rules k2_bar_regrows_from_hollow and k2_bar_regrows_from_frame are witnessed by the replay as well as by the diff. The corrected coverage figures -- 2/2 rather than the 4/4 I had inflated -- stand. The general lesson I drew last round is now paid for: the coverage number I did not count was the lie that hid the defect, and counting it was what let me date the fix in advance."
    [depends: the_regrowth_is_the_answer_to_the_replay_mismatch  probe: passed]

  theorem the_regrowth_is_the_answer_to_the_replay_mismatch "The previous round's surprise named four cells on the ACTION2 transition: (34,13) (34,14) manual 0 world 3, (35,13) (35,14) manual 6 world 3. All four are BarBody instances -- their frame-0 colour is 3 -- and in W1 they carry the box, 0 in the interior rows and 6 in the border row. Both original k2 BarBody rules demand colour 3 six rows below, and six rows below them lies rows 40-41 of the bottom slot, which the truncation leaves BACKGROUND. So no rule fired and the four cells stood still. Two rules with the guard colored(below^6, 5) close it, 2/2 and 2/2, exclusive against the existing pair by that colour alone."
    [probe: passed]

  theorem the_bar_is_six_rows_above_and_four_below_in_both_directions "The bar reads 3,3 / 3,3 / 2,2 / 2,2 / 3,3 / 3,3 down rows 30-35 at cols 13-14 in the top slot, and 3,3 / 3,3 / 2,2 / 2,2 down rows 36-39 in the bottom, with rows 40-41 background -- I have just re-read all of it off the current frame. Going down the last two rows CLEAR; coming up they REGROW as 3. The box, by contrast, renders 22 frame cells and 12 hollow cells in either slot without loss, and I have re-counted both in the current frame: 22 colour-6 (border ring minus the two port cells, plus a 2x2 core at rows 32-33 cols 13-14) and 12 colour-0. So the swap is not an information-preserving exchange of two 6x6 windows: the bottom slot is lossy for the bar and the loss is restored from nowhere visible when it comes back. mdl_segmenter says the same from outside -- its W0 blobs have 440 cells and its W1 blobs 436, and 440 minus 436 is these four cells."
    [depends: the_regrowth_is_the_answer_to_the_replay_mismatch  probe: passed]

  theorem the_world_is_not_a_function_of_the_frame_and_i_correct_my_own_arithmetic "The conclusion stands and the count that supports it was off by one, so I restate both. distinct_states = 7 over 10 states requires THREE coincidences, not the two I claimed. They are S0 = S2 (ACTION2 undid ACTION1, both readouts lit), S5 = S7 (the same, later, both readouts blank), and -- new this round -- S8 = S9, because ACTION3 at t9 changed nothing at all. That third one is the FIRST WITNESSED INERTNESS this world has produced and mdl_segmenter corroborates it without being asked: obj6 spanned frame 8 alone last round and spans frames 8-9 now. The negative result is untouched by the correction. S5 and S7 are the same visible frame; ACTION1 in S5 changed 72 cells and no meter cell, ACTION1 in S7 changed 73, the extra being (53,62) 2 to 3. Same frame, same key, different successor. My compiled step is a function of the frame, so it MUST be wrong somewhere, and I would rather name where than let it look sound."
    [depends: the_bar_is_six_rows_above_and_four_below_in_both_directions  probe: passed]

  theorem the_meter_is_a_clock_not_a_key "The meter has advanced twice: at command 4 under ACTION4, painting (53,63), and at command 8 under ACTION1, painting (53,62). Two different keys, the second a key already pressed twice without advancing it. What they share is the COMMAND INDEX. This round I ran a discrimination I had not run before, and it kills the best rival: 'every fourth command that returned two frames' predicts a tick at the 4th and 8th two-frame commands, but t8 is only the 7th two-frame command (t5 and t9 returned one frame each), so that counter is REFUTED and the plain command index survives. Seven commands have now failed to tick -- 1,2,3,5,6,7,9 -- and every one of them is a non-multiple of four. I read the meter as a clock ticking every fourth command from RESET, eating row 53 from the right, and I predict the third tick lands on (53,61) at command 12, three commands from now. THE GUARD LANGUAGE HAS NO COUNTER, at any length, so this cannot be written as a rule; it is written here instead. I keep k4_meter_tip_first_advance because it reproduces t4 in replay and, since (53,63) is no longer colour 2, it can never fire again and so can never assert the refuted key-attribution a second time."
    [depends: the_world_is_not_a_function_of_the_frame_and_i_correct_my_own_arithmetic  probe: pending]

  theorem the_vacuous_probes_were_replay_damage_and_half_of_that_is_now_shown "Last round P-01, P-02 and P-03 each refuted all 57 hypotheses including inert and returned 0.0 bits against about 1.9 expected, and I blamed the four-cell replay defect rather than a missing mechanism. The falsifiable half of that claim is now confirmed: the replay does carry my reconstructed state forward (see the_replay_is_cumulative...), so a divergence at transition 1 did contaminate every later predicted hash for every hypothesis, ablations included. The other half is untested, because no probe report reached me this round. IT REMAINS FALSIFIABLE IN THE SAME WORDS: with replay now exact through transition 6 and wrong by one advertised cell after it, a probe that still refutes every hypothesis including inert is evidence of a mechanism I have not stated, and this theorem is refuted."
    [depends: the_replay_is_cumulative_and_one_cell_contaminates_every_later_frame  probe: pending]

  theorem exchange_versus_scroll_is_still_open_and_i_am_still_standing_where_it_can_be_asked "READING A, exchange: two slots trade images and the bar simply renders four rows below. READING B, scroll: a list of at least three items steps by six rows, and the four-row glyph in the bottom of W1 is a THIRD ITEM that happens to look like the bar's first four rows. Five swap commands are observed -- A1 at t1, A2 at t2, A1 at t6, A2 at t7, A1 at t8 -- and every one was pressed in the opposite configuration from its predecessor, so ACTION1 HAS NEVER FOLLOWED ACTION1. t9 spent a command without leaving W1, so the question is still askable from where I stand and still costs one command rather than two. What tilts me slightly to A is the regrowth: under B the bar's rows 34-35 must be redrawn from an item that has scrolled out of view, which is ordinary for a scroll, whereas under A they are redrawn from a slot that never lost them, which needs no memory -- but that is taste, not evidence. One ACTION1 answers it: A returns W0 exactly and 20 rules generalise, B shows a configuration never seen and my whole word_table is a two-item special case."
    [depends: the_bar_is_six_rows_above_and_four_below_in_both_directions  probe: pending]

  theorem the_readout_belongs_to_the_box_so_i_have_guarded_action4_into_silence "At t1 the LIT readout travelled with the box from rows 38-39 to rows 32-33 -- twelve cells of pattern moved six rows up in the same step the box did -- and the current frame confirms the binding from the other side: in W1 the two port pixels read 1 at (32,16) and 2 at (33,16), six rows above where they sit in W0. So the readout is bound to the box, not to the slot. ACTION4 has been pressed exactly once, in W0, where bottom_port = (38,16) is 1. Unguarded, my k4 rules would fire on the Dot and BarCore instances at rows 38-39 in ANY state, and pressed in W1 they would light a strip the box has left: 24 cells drawn confidently wrong and quite likely 24 more left dark. The guard colored(bottom_port, 1) makes them fire on nothing in W1, so my manual is SILENT about what ACTION4 does there. That silence is a declared gap, not a claim, and it is cheaper than a fabricated arrangement of 1s and 2s over twelve Blank instances my type system cannot tell apart."
    [depends: the_bar_is_six_rows_above_and_four_below_in_both_directions  probe: pending]

  theorem barcore_is_five_unrelated_things_and_the_arm_sees_only_colour "Colour 2 at frame 0 sits on the 4-cell core of the bar, the lower port pixel, four dots of the readout, and two meter cells, (53,63) and (53,62). Eleven instances, one type, because the arm looks objects up by colour alone. The separators are all cells I have read: the bar core has colour 3 two rows above; the readout cores have a colour-1 dot immediately left; the port has colour 0 to its left; the old meter tip is the only instance whose rightof is off-board. I have re-checked every rule in this file against (53,62): its left neighbour is 2, its right neighbour is not a wall, two rows above it is background, so no rule of mine grounds on it in any state -- which is precisely why certify can report it wrong and report nothing else. It is a cell I own and cannot move, the right shape for a clock I cannot read."
    [depends: the_meter_is_a_clock_not_a_key  probe: passed]

  theorem the_swap_rules_are_forty_and_constraint_three_is_still_failed "One law -- take the colour of the cell six away -- is forty rules. recolored takes an INTEGER LITERAL, so a target colour cannot be read out of a cell and must be named, and the law splits once per source colour, per target colour, per direction, per key. THE CONCEPT DOES NOT PAY FOR ITSELF and I will not dress that up: forty rules to explain 72 cells twice over is worse than a lookup table, and I keep it only because the alternative is 96 unexplained pixels. What buys part of it back is that a TYPE IS A FRAME-0 COLOUR: the frame-0 configuration is W0, so a rule's source colour already says which half of the widget the instance lives in, and only the four truncation and regrowth rules need geometry on top of that. A consequence worth stating because it drives the playbook: every k1 rule demands that the instance still wears its frame-0 colour, which is true only in W0, so the whole family is silent in W1 BY CONSTRUCTION rather than by evidence."
    [depends: the_regrowth_is_the_answer_to_the_replay_mismatch  probe: passed]

  theorem no_goal_section_and_this_is_a_refusal_not_an_oversight "With no goal, is_goal is False everywhere, plan never returns sat, commit never runs, and every command this arm spends is a probe. I accept that consequence and still decline to write one, for arithmetic rather than modesty. Ten states have returned NOT_FINISHED and no other GameState has ever been seen, so no observation distinguishes a win from a non-win. The pos form is dead -- nothing in this world moves, every rule here is a recolour, and cegis_miner refused all seven tracks for exactly that reason. That leaves counts over seven types, and every count I can write names a CONFIGURATION: count(Frame, color = 5) = 14 says the box is up, count(Dot, color = 4) = 8 says the readout is dark, count(BarCore, color = 3) = 2 IS TRUE RIGHT NOW and would make the plan tier declare victory at a state I have no reason to call one. A false goal is worse than none, because it converts a probe budget into a confident wrong plan. WHAT ENDS THIS IS AN OBSERVATION, NOT AN EDIT: a GameState other than NOT_FINISHED, or any cell outside rows 30-41 and row 53 changing at all. ACTION5 and ACTION6 have never been pressed and are the cheapest place to look for it."
    [depends: the_meter_is_a_clock_not_a_key  probe: pending]

  theorem the_silences_i_assert_and_which_of_them_are_forged "The compiled step is total, so where nothing fires I assert identity in the same voice I use for what I watched. Audit at S9 = W1, both readouts blank. ACTION3: NOW WITNESSED -- t9 pressed it here and changed zero cells, exactly as entailed, and the silence I believed is a silence I have seen; this is the only entry in this audit that has been upgraded. ACTION7: predicted silent by the same entailment (its rules are k3's twins and the pattern they erase is already erased), unwitnessed in W1 but riding on a witnessed twin, and I believe it. ACTION2: fully predicted, 72 cells, the only action here my manual draws. ACTION1: PREDICTED SILENT ON ZERO WITNESSES and this is my largest forgery, 20 rules and one structural reading riding on it; worse, the silence is an artefact of every k1 guard demanding a frame-0 colour, so it is a property of my rule-writing rather than a claim about the world. I expect to be wrong and I want to be. ACTION4: predicted silent because bottom_port is 5 here -- a declared gap I chose over a wrong drawing. ACTION5, ACTION6: predicted silent, never pressed in ten states, no witness of any kind. And every one of these omits the clock: on command 12 one extra cell (53,61) turns 3 and I cannot draw it. A probe ranker prices a predicted identity at zero because every ablation agrees with a rule that does not fire, SO THE ACTIONS I MOST NEED ARE THE ONES IT CAN NEVER BUY, and saying so in prose is the only lever this desk has."
    [depends: exchange_versus_scroll_is_still_open_and_i_am_still_standing_where_it_can_be_asked, the_readout_belongs_to_the_box_so_i_have_guarded_action4_into_silence  probe: pending]

  theorem what_lies_outside_the_widget "Full-frame responsibility means describing the 3998 constant cells, not just naming them board. A colour-4 panel fills rows 29-41 from col 17 to col 46 and carries a 4x4 block of colour 14 at rows 31-34, cols 42-45 -- the only colour-14 anywhere and the only structure on the panel. Both readouts are cut into that panel's left edge, which is why connected_components(4) cannot separate them from it and why every mdl_segmenter blob is a 13x36 slab. Row 29 shows 5,5,3,3,5,5 at cols 11-16 and has NEVER changed: the bar reads seven rows tall on screen while only six of it is alive. Rows 42-52 are background across the window, which is what lets every bottom-half rule test six rows down without a wall test. Row 53 is the clock, all colour 2 except its two rightmost cells, both now 3. Row 54 is a solid colour-4 rule. Colours 8 and 9 appear in colours_seen and on no dynamic cell, so they sit on the board outside this window and have never moved."
    [probe: pending]

  theorem what_the_engines_gave_me "mdl_segmenter reports BOTH variants at negative gain -- minus 7528 bits on 7 tracks, minus 7968 on 38 -- so by its own measure it compressed nothing and I take none of its structure. What I take is a frame-index witness independent of my rules: obj0 440 cells at frame 0, obj2 436 at frame 1, obj3 440 across frames 2-5, obj4 436 at frame 6, obj5 440 at frame 7, obj6 436 across frames 8-9. That is W0 W1 W0 W0 W0 W0 W1 W0 W1 W1 over ten frames, arrived at without any rule of mine, matching my reconstruction cell for cell, including the four-cell size difference that is the truncation, and including obj6's growth from one frame to two, which is t9's inertness seen from outside. cegis_miner refuses all seven tracks and its verdict that the world does not narrate as one mover remains the strongest negative result available. zero_space self-reports THIN in its own words -- 9 transitions constraining rank 5 of 686 features, null space 681 -- and its one global law is my census with both meter cells appended; I take the corroboration of the cell set and reject the law as unfalsified rather than confirmed, which is what its own report says."
    [probe: passed]

  theorem what_i_predict_before_i_see_it "Written so it can cost me. STATE: S9 = S8 = W1, box in the top slot, bar four rows in the bottom, both readouts blank, (53,63) and (53,62) both 3, nine commands since RESET. ACTION1 HERE: my manual says nothing changes; I say that is false, and I name the outcomes in advance -- 72 cells back to W0 means exchange and 20 rules generalise by symmetry, anything else means scroll and the bottom glyph is a third item. ACTION2 HERE: exactly 72 cells, no readout cell, no row-53 cell. ACTION4 HERE: my manual says nothing changes; I expect the twelve cells at rows 32-33, cols 17-22 to light instead, which refutes the silence and confirms the readout follows the box. ACTION3, ACTION7: nothing changes, and ACTION3 has now been watched doing exactly that here. ACTION5, ACTION6: never pressed in ten states; I predict only that whichever is pressed produces the largest single addition to this manual available, and that it is the cheapest place a win condition could come from. THE CLOCK RIDES ON ALL OF THEM: commands 10 and 11 leave row 53 alone, command 12 turns (53,61) from 2 to 3 and I cannot draw it. A one-cell divergence in row 53 on the twelfth command confirms the clock and implicates nothing else in this file; a tick on command 10 or 11 refutes the period and I would rather learn that in three commands than in thirty."
    [depends: the_silences_i_assert_and_which_of_them_are_forged, no_goal_section_and_this_is_a_refusal_not_an_oversight  probe: pending]
```

=== PLAYBOOK ===
```
# playbook.dsl -- what to buy with the next command, not a route.
#
# STATE: eleven entries, ten commands (RESET, A1, A2, A3, A4, A7, A1, A2, A1,
# A3). I am in W1 and t9 did not move me: hollow box in the TOP slot, bar four
# rows in the BOTTOM slot (rows 36-39, rows 40-41 background), BOTH readouts
# blank, (53,63) and (53,62) both 3. 98 cells have ever changed; 96 are the
# widget and 2 are the clock.
#
# WHAT CHANGED THIS ROUND.
#  * The manual is CLEAN except for one cell it declared undrawable in
#    advance. certify: 7/9 replay, 0/4096 unexplained, 0 ambiguity clashes,
#    first divergence (53,62) on the ACTION1 command -- the exact cell and the
#    exact command I named last round before the rerun. No rule changed in
#    response, and the refusal is written out in the manual.
#  * The replay is CUMULATIVE. Two transitions failed but only one diverged;
#    the second inherited it. That is now demonstrated rather than asserted,
#    and it is the same mechanism I blamed for three vacuous probes.
#  * t9 spent a command on ACTION3, which this playbook had listed under WHAT
#    NOT TO PRESS. The outcome was zero cells, exactly as entailed. It was not
#    free and it was not worthless: it is the FIRST WITNESSED INERTNESS here,
#    it supplied the third duplicate state (S8 = S9) that the store's
#    distinct_states = 7 requires and that I had miscounted, and it left me
#    standing where the open question can still be asked for one command.
#  * A rival clock counter died: 'every fourth two-frame command' predicts the
#    8th two-frame command, and t8 was the 7th. The plain command index
#    survives; the next tick is command 12 on (53,61).
#
# THE QUESTION THAT ONLY THIS CONFIGURATION CAN ASK
#   ACTION1 has been pressed three times and ACTION2 twice, and every press
#   was in the opposite configuration from its predecessor -- ACTION1 HAS
#   NEVER FOLLOWED ACTION1. Exchange and scroll are both alive. In W1 one
#   ACTION1 splits them: exchange returns W0 exactly, scroll shows a
#   configuration never seen. Any command that leaves W1 makes the question
#   cost two.
#
# THE TRAP THIS PLAYBOOK EXISTS TO DEFEAT
#   Every k1 rule demands that its instance still wears its frame-0 colour,
#   which is true only in W0. So my manual's silence on ACTION1-in-W1 is an
#   artefact of how the rules are written, not a reading of the world -- and a
#   probe ranker prices a predicted identity at ZERO, because every ablation
#   agrees with a rule that does not fire. The single most informative command
#   available is the one the ranker can never buy. That is why the ranked list
#   below is stated in prose and why the order lines say it twice.
#
# WHAT IS GENUINELY UNKNOWN
#   * ACTION5 and ACTION6: never pressed in eleven entries. Zero constraint.
#   * ACTION1 in W1, ACTION2 in W0, ACTION4 in W1: silences with no witness.
#   * The clock's period is fitted to two ticks and has survived one
#     discrimination. Commands 10, 11, 12 settle it.
#   * The win condition. Nothing countable separates a win from here, no
#     GameState but NOT_FINISHED has ever been returned, and I refuse to
#     invent one. The plan tier's silence is a true report of my ignorance.
#
# PRICES ADVERTISED IN ADVANCE, SO A REFUTATION ON THEM IMPLICATES NOTHING
#   * (53,62) is wrong in replay from transition 7 onward, permanently, and
#     (53,61) joins it at command 12. Row-53 divergences buy nothing.
#   * ACTION1 here is predicted SILENT and I expect that to be wrong.
#   * ACTION4 here is predicted SILENT by a guard I added on purpose; if the
#     top readout lights, the guard was right about the box and wrong about
#     the silence, and that is a purchase.
#   * ACTION3 here is predicted silent AND WITNESSED silent. Repeating it buys
#     nothing at all now.
#
# THE RANKED LIST
# 1. ACTION1, HERE, IN W1. The only command that splits exchange from scroll,
#    the largest forged silence in the manual (20 rules), askable only from
#    the configuration I am standing in, and three legible outcomes: W0
#    exactly, a new configuration, or nothing.
# 2. ACTION5 or ACTION6. Never pressed. Any outcome is the largest single
#    addition available -- including nothing, which after t9 I now know how to
#    read -- and it is the cheapest place a win condition could come from.
# 3. ACTION4, HERE. Tests the guard and the readout-follows-box reading in one
#    press, and relights the readout so the A1/A2 readout rules can be
#    re-witnessed in the other configuration.
# 4. Whatever the first three are, three commands from now is command 12 and
#    the clock is checked for free in the raw diff of one cell of row 53.
#
# WHAT NOT TO PRESS
#   ACTION3 here: witnessed inert in this exact state. It is now the single
#   most expensive command available, because its result is known.
#   ACTION7 here: entailed inert by a twin that has been watched.
#   ACTION2 here: repeats t7 from an identical frame; replay gives it free.
#   Anything chosen because my manual predicts the most pixels for it: that
#   number measures my coverage, not the world's information.

order     spend_a_probe_only_the_current_state_can_ask_before_one_askable_anywhere [proof: lean]
order     press_an_action_never_pressed_before_repressing_a_modelled_one    [proof: lean]
order     press_a_modelled_action_in_a_configuration_it_was_never_pressed_in [proof: lean]
order     test_a_silence_that_rests_on_no_witness_before_one_that_is_entailed [proof: lean]
order     test_a_silence_that_is_an_artefact_of_rule_syntax_before_any_other [proof: lean]
order     score_an_unwitnessed_silence_above_a_witnessed_repetition         [proof: lean]
order     treat_an_action_the_manual_calls_silent_as_unprobeable_not_untested [proof: lean]
order     override_a_ranker_that_prices_every_predicted_identity_at_zero    [proof: lean]
order     prefer_a_probe_with_three_distinct_legible_outcomes_over_one_with_two [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired   [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance                [proof: lean]
order     date_a_prediction_before_the_rerun_so_the_fix_can_be_scored       [proof: lean]
order     suspect_the_replay_before_the_mechanism_when_every_hypothesis_dies [proof: lean]
order     check_whether_a_replay_is_cumulative_before_blaming_a_second_rule [proof: lean]
order     count_a_coverage_figure_before_writing_it_down                    [proof: lean]
order     recount_a_state_census_against_the_store_before_drawing_from_it   [proof: lean]
order     kill_a_rival_counter_with_a_counting_i_can_do_without_a_command   [proof: lean]
order     look_for_the_mirror_of_a_fixed_defect_in_the_reverse_direction    [proof: lean]
order     guard_a_rule_into_silence_before_letting_it_draw_an_unwitnessed_state [proof: lean]
order     name_the_hidden_state_rather_than_key_a_rule_to_the_wrong_cause   [proof: lean]
order     keep_a_refuted_attribution_only_while_it_can_never_fire_again     [proof: lean]
order     refuse_a_patch_that_buys_one_right_cell_with_three_wrong_ones     [proof: lean]
order     separate_same_coloured_roles_by_a_cell_you_have_actually_read     [proof: lean]
order     prefer_a_landmark_guard_over_a_chain_of_cell_operators            [proof: lean]
order     search_the_engine_report_for_a_count_that_matches_the_divergence  [proof: lean]
order     prefer_a_positive_colour_test_over_a_negated_wall_test            [proof: lean]
order     buy_the_observation_that_makes_a_goal_writable_before_writing_one [proof: lean]
order     extend_the_transition_model_before_extending_the_goal_language    [proof: lean]
order     refuse_a_goal_no_observation_distinguishes_and_say_so_out_loud    [proof: lean]
order     emit_every_required_block_before_polishing_any_of_them            [proof: lean]

prune     rule_proposed_with_zero_witnesses_of_any_kind => dead             [proof: lean]
prune     rule_whose_two_witnesses_demand_opposite_outcomes_from_one_frame => dead [proof: lean]
prune     rule_that_would_forge_the_reverse_direction_of_an_unobserved_press => dead [proof: lean]
prune     rule_that_would_fire_on_every_command_to_draw_a_cell_that_moves_on_one => dead [proof: lean]
prune     guard_conjunct_with_no_negative_witness_and_no_explained_pixel => dead [proof: lean]
prune     goal_clause_over_a_type_with_zero_instances => dead               [proof: lean]
prune     goal_that_is_already_true_at_the_current_state => dead            [proof: lean]
prune     goal_satisfiable_without_leaving_the_two_widget_configurations => dead [proof: lean]
prune     goal_no_observed_gamestate_could_have_distinguished => dead       [proof: lean]
prune     divergence_lies_only_on_a_cell_that_had_never_changed => dead     [proof: lean]
prune     divergence_lies_only_on_the_unadvanced_clock_frontier => dead     [proof: lean]
prune     divergence_the_previous_edition_named_by_cell_and_by_command => dead [proof: lean]
prune     divergence_a_later_transition_only_inherited_from_an_earlier_one => dead [proof: lean]
prune     repeats_a_key_whose_inertness_here_is_entailed_by_witnessed_rules => dead [proof: lean]
prune     repeats_a_key_already_watched_doing_nothing_in_this_exact_state => dead [proof: lean]
prune     repeats_a_transition_already_witnessed_from_an_identical_frame => dead [proof: lean]
prune     ranked_only_because_the_manual_predicts_the_most_pixels => dead   [proof: lean]
prune     leaves_the_only_configuration_that_can_ask_the_open_question => dead [proof: lean]
prune     every_rule_it_would_witness_is_already_at_full_coverage => dead   [proof: lean]

heuristic actions_of_the_alphabet_never_yet_pressed                         [admissible: lean]
heuristic configurations_in_which_a_known_key_has_never_been_pressed        [admissible: lean]
heuristic silences_of_the_manual_that_rest_on_no_witness                    [admissible: lean]
heuristic silences_that_follow_from_rule_syntax_rather_than_from_evidence   [admissible: lean]
heuristic structural_readings_a_single_command_could_eliminate              [admissible: lean]
heuristic rules_that_one_command_could_generalise_or_refute_together        [admissible: lean]
heuristic distinct_legible_outcomes_a_single_command_can_produce            [admissible: lean]
heuristic questions_that_only_the_present_configuration_can_ask             [admissible: lean]
heuristic pairs_of_identical_frames_with_different_successors               [admissible: lean]
heuristic duplicate_state_pairs_the_store_count_requires_but_i_have_not_named [admissible: lean]
heuristic rival_counters_still_fitting_both_observed_ticks                  [admissible: lean]
heuristic commands_remaining_before_the_clock_ticks_again                   [admissible: lean]
heuristic widget_configurations_never_yet_observed                          [admissible: lean]
heuristic cells_outside_the_widget_a_command_could_turn_dynamic             [admissible: lean]
heuristic cells_whose_first_change_would_make_a_goal_line_writable          [admissible: lean]
heuristic gamestates_other_than_not_finished_ever_returned                  [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_advertised_prices            [admissible: lean]
heuristic fitted_guards_a_command_could_convert_into_witnessed_ones         [admissible: lean]

prefer    a_command_that_splits_two_named_readings_in_one_press             [ev: 1/1 available]
prefer    a_probe_askable_only_from_the_configuration_now_showing           [ev: 1/2 configurations]
prefer    a_key_never_pressed_in_any_state                                  [ev: 2/7 keys]
prefer    a_key_never_pressed_in_the_configuration_now_showing              [ev: 3/5 pressed keys]
prefer    a_command_that_tests_twenty_rules_at_once                         [ev: 2/2 available]
prefer    a_command_that_would_turn_a_cell_outside_the_widget_dynamic       [ev: 2/11 entries]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                  [ev: 10/10 diffs]
prefer    a_command_whose_only_predicted_divergence_is_one_already_priced   [ev: 2/2 priced cells]
prefer    a_command_that_would_produce_a_third_widget_configuration         [ev: 0/11 entries so far]
prefer    a_command_that_could_return_a_gamestate_never_yet_seen            [ev: 0/11 entries so far]
```

=== LOG ===
```json
[
  {"id": "S-01", "subject": "replay_mismatch at t=7, cell (53,62), manual 2 world 3", "verdict": "reject",
   "as": "no change to the rules",
   "why": "This is verbatim the divergence the previous edition named in advance -- same cell, same command -- as the price of a clock keyed to the command index, and the guard language has no counter of any length, so the only rules that could paint it would fire on every command and be wrong on commands 9, 10 and 11 to be right on 8; the refusal is written into the manual as the_only_divergence_left_is_the_one_i_priced_in_advance."},

  {"id": "L-01", "subject": "the_replay_is_cumulative_and_one_cell_contaminates_every_later_frame", "verdict": "accept",
   "as": "new theorem [probe: passed]",
   "why": "certify reports matched=7 of 9 with exactly one named divergence; transition 8 is t9's ACTION3, an identity in both world and manual, so one-step replay would have scored 8/9 and only a cumulative replay explains 7/9 -- which also bounds the clock's cost at one held cell rather than one new cell per command."},

  {"id": "L-02", "subject": "the_regrowth_fix, previously [probe: pending]", "verdict": "accept",
   "as": "the_regrowth_fix_is_confirmed_and_the_prediction_that_confirmed_it_was_dated [probe: passed]",
   "why": "The prediction written before the rerun was 't1 through t7 replay exactly, t8 wrong by exactly one cell (53,62)'; certify's first divergence is index 7, one cell, (53,62), and no ACTION2 cell appears anywhere in the report, so the four regrowth cells now replay."},

  {"id": "L-03", "subject": "my own arithmetic: distinct_states = 7 over 10 needs three coincidences, not two", "verdict": "accept",
   "as": "correction folded into the_world_is_not_a_function_of_the_frame_and_i_correct_my_own_arithmetic",
   "why": "S0=S2 and S5=S7 give only 8 distinct; t9's zero-cell ACTION3 supplies S8=S9 and closes the count at 7 exactly, and mdl_segmenter's obj6 growing from frame 8 alone to frames 8-9 witnesses the same inertness from outside my rules."},

  {"id": "L-04", "subject": "the_meter_is_a_clock_not_a_key", "verdict": "probe-pending",
   "as": "kept, with one rival counter now refuted",
   "why": "'Every fourth two-frame command' predicts the tick at the 8th two-frame command, but t8 was only the 7th (t5 and t9 returned one frame each), so the plain command index survives with ticks at 4 and 8 and seven non-ticks all at non-multiples of four; the third tick at (53,61) on command 12 is the test and it is three commands away."},

  {"id": "L-05", "subject": "first witnessed inertness (t9 ACTION3 in W1, zero cells)", "verdict": "accept",
   "as": "upgrade inside the_silences_i_assert_and_which_of_them_are_forged",
   "why": "ACTION3-in-W1 moves from entailed-but-unwitnessed to witnessed; its twin ACTION7 stays entailed on a now-watched twin; ACTION1-in-W1 stays the largest forgery and is downgraded further by the observation that its silence follows from every k1 guard demanding a frame-0 colour."},

  {"id": "R-01", "subject": "k4_meter_tip_first_advance", "verdict": "accept",
   "as": "kept unchanged, with its refuted attribution restated",
   "why": "It is needed to reproduce t4 under cumulative replay (deleting it would break transition 3 as well), and since (53,63) is no longer colour 2 its guard can never be satisfied again, so it cannot assert the refuted key-attribution a second time."},

  {"id": "R-02", "subject": "a rule to draw (53,61) from colored(rightof, 3)", "verdict": "reject",
   "why": "It would fire on commands 9, 10 and 11 as well as 12, buying one correct cell at the cost of three wrong ones; the playbook now carries this as a prune line."},

  {"id": "R-03", "subject": "generalising the k1 family by dropping the source-colour guard so ACTION1 acts in W1", "verdict": "reject",
   "why": "Zero witnesses of ACTION1 pressed in W1 -- it has never followed itself -- so this is exactly the forgery of an unobserved reverse direction the playbook prunes; the belief lives in exchange_versus_scroll_is_still_open instead, where it costs one command to settle."},

  {"id": "O-01", "subject": "mdl_segmenter obj0/obj2/obj3/obj4/obj5/obj6 (13x36 slabs, 440 and 436 cells)", "verdict": "reject",
   "as": "structure not taken; frame-index witness taken",
   "why": "Both variants report negative gain (-7528 and -7968 bits), so by the engine's own measure nothing was compressed; what I take is the independent sequence W0 W1 W0 W0 W0 W0 W1 W0 W1 W1 and the 440-436 size gap, which match my reconstruction and my four truncated cells."},

  {"id": "O-02", "subject": "my seven colour types (Field, BarBody, BarCore, Blank, Frame, Hollow, Dot)", "verdict": "accept",
   "as": "unchanged census 24+8+11+12+22+12+9 = 98",
   "why": "Two independent store numbers land on it without adjustment: dynamic_cells = 98 is the total, and cells_needing_an_owner = 74 is exactly 98 minus the 24 Field cells, i.e. the dynamic cells that are not background at frame 0; certify reports 0/4096 unexplained."},

  {"id": "O-03", "subject": "cegis_miner, all seven tracks refused", "verdict": "accept",
   "as": "corroboration of a negative",
   "why": "Its precondition is one move event per transition and nothing in this world moves -- every rule in the manual is a recolour -- so its verdict that the world does not narrate as one mover is true and is also why no pos-form goal can be written."},

  {"id": "O-04", "subject": "zero_space global law over the 98-cell set", "verdict": "reject",
   "as": "cell set corroborated, law not taken",
   "why": "The engine self-reports THIN -- 9 transitions constraining rank 5 of 686 features, null space 681 -- so its law is unfalsified rather than confirmed by its own account; the cell list it emits is my census with both meter cells appended, which I take as corroboration only."},

  {"id": "E-01", "subject": "a guard over the command counter", "verdict": "probe-pending",
   "as": "wrote theorem the_meter_is_a_clock_not_a_key instead",
   "why": "I wanted something like 'when command_index mod 4 = 0 then recolored(meter_frontier, 3)'; the guard vocabulary is exhaustive and has act/free/colored/adjacent/comparison/wall and no counter and no access to command history, so the belief is prose with a dated prediction attached."},

  {"id": "E-02", "subject": "a goal section", "verdict": "reject",
   "as": "no goal section, deliberately",
   "why": "Eleven entries have returned NOT_FINISHED and nothing else, so no observation distinguishes a win; every count I could write names a configuration and count(BarCore, color = 3) = 2 is TRUE RIGHT NOW, which would make the plan tier declare victory at a state I have no reason to call one."},

  {"id": "P-01", "subject": "ACTION1 in W1", "verdict": "probe-pending",
   "why": "The only command that splits exchange from scroll, 20 rules ride on it, it is askable only from the configuration I am standing in and t9 did not cost me that position -- and my manual predicts it silent, so a probe ranker will price it at zero and this desk's prose is the only thing that can buy it."},

  {"id": "P-02", "subject": "ACTION5 or ACTION6", "verdict": "probe-pending",
   "why": "Never pressed in eleven entries; any outcome is the largest single addition available and it is the cheapest place a GameState other than NOT_FINISHED could come from, which is the one observation that would make a goal writable."},

  {"id": "P-03", "subject": "ACTION4 in W1", "verdict": "probe-pending",
   "why": "Tests the bottom_port guard I added on purpose and the readout-follows-box reading in one press; if the twelve cells at rows 32-33 cols 17-22 light, the guard was right about the box and wrong about the silence, and that is a purchase either way."},

  {"id": "P-04", "subject": "the vacuous-probe theorem", "verdict": "probe-pending",
   "why": "Its replay half is now demonstrated (L-01), but no probe report reached me this round, so the falsifiable half stands in the same words: a probe that still refutes every hypothesis including inert refutes it and points at a mechanism I have not stated."}
]
```
```
