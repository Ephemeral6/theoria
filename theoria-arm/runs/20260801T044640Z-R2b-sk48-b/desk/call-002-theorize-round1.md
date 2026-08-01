# call-002-theorize-round1

model: `claude-opus-5` · 687514 ms · $1.836808 · usage {"cache_creation": {"ephemeral_1h_input_tokens": 33265, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 33265, "cache_read_input_tokens": 0, "inference_geo": "not_available", "input_tokens": 2, "iterations": [{"cache_creation": {"ephemeral_1h_input_tokens": 33265, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 33265, "cache_read_input_tokens": 0, "input_tokens": 2, "output_tokens": 59167, "type": "message"}], "output_tokens": 59167, "server_tool_use": {"web_fetch_requests": 0, "web_search_requests": 0}, "service_tier": "standard", "speed": "standard"}

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
 "cells_needing_an_owner": 73,
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
 "constant_cells": 3999,
 "distinct_states": 5,
 "dynamic_box": [
  29,
  10,
  54,
  63
 ],
 "dynamic_cells": 97,
 "max_frames_in_one_command": 2,
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
 38 560660144444444444444444444444444444455555555555555555
 39 560660244444444444444444444444444444455555555555555555
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
 53 222222222222222222222222222222222222222222222222222223
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

## What the engines proposed

These are PROPOSALS. Nothing here is accepted until you accept it, and an engine cannot name anything -- `obj0` is the best it can do.

```json
{
 "cegis_miner": {
  "engine": "cegis_miner",
  "n_actions": 5,
  "n_states": 6,
  "refusals": [
   "ValueError: transition 0 narrates ['vanish']; only move/none are mined on this fixture",
   "ValueError: transition 3 narrates ['recolor']; only move/none are mined on this fixture",
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
  "candidates": 4,
  "chosen_operator": "connected_components(4)",
  "chosen_split_by_color": false,
  "engine": "mdl_segmenter",
  "event_types": {
   "appear": 2,
   "recolor": 4,
   "vanish": 2
  },
  "n_frames": 6,
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
    "frames_present": 6,
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
   }
  ],
  "variants": [
   {
    "baseline_bits": 3475,
    "compression_ratio": 2.161727,
    "events": 8,
    "gain_bits": -4037,
    "ms": 6,
    "script_bits": 7512,
    "split_by_color": false,
    "tracks": 4
   },
   {
    "baseline_bits": 3475,
    "compression_ratio": 3.995396,
    "events": 61,
    "gain_bits": -10409,
    "ms": 15,
    "script_bits": 13884,
    "split_by_color": true,
    "tracks": 33
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
   "dynamic_cells": 97,
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
  "cells_needing_an_owner": 73,
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
  "constant_cells": 3999,
  "distinct_states": 5,
  "dynamic_box": [
   29,
   10,
   54,
   63
  ],
  "dynamic_cells": 97,
  "max_frames_in_one_command": 2,
  "shape": [
   64,
   64
  ],
  "states": 6,
  "steps": 6
 },
 "window": {
  "box": [
   29,
   10,
   54,
   63
  ],
  "covered": 1.0,
  "dynamic_cells": 97,
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
  "cells_dynamic": 97,
  "cells_used": 97,
  "colours": [
   "c0",
   "c1",
   "c2",
   "c3",
   "c4",
   "c5",
   "c6"
  ],
  "difference_rank": 3,
  "engine": "zero_space",
  "evidence_adequacy": {
   "constrained_fraction": 0.004418,
   "difference_rank": 3,
   "features": 679,
   "space_dimension": 676,
   "transitions": 5,
   "verdict": "THIN: 5 transitions constrain rank 3 of 679 features, so the null space has dimension 676 and nearly every vector in it is a 'law' that is true over these states and unfalsified rather than confirmed. Treat every law below as a correlation awaiting a transition that could break it, not as a conservation law."
  },
  "features": 679,
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
     "c1@32",
     "c2@32",
     "c3@32",
     "c4@32",
     "c5@32",
     "c6@32",
     "c0@33",
     "c1@33",
     "c2@33",
     "c3@33",
     "c4@33",
     "c5@33",
     "c6@33",
     "c0@34",
     "c1@34",
     "c2@34",
     "c3@34",
     "c4@34",
     "c5@34",
     "c6@34",
     "c0@35",
     "c1@35",
     "c2@35",
     "c3@35",
     "c4@35",
     "c5@35",
     "c6@35",
     "c0@36",
     "c1@36",
     "c2@36",
     "c3@36",
     "c4@36",
     "c5@36",
     "c6@36",
     "c0@37",
     "c1@37",
     "c2@37",
     "c3@37",
     "c4@37",
     "c5@37",
     "c6@37",
     "c0@38",
     "c1@38",
     "c2@38",
     "c3@38",
     "c4@38",
     "c5@38",
     "c6@38",
     "c0@39",
     "c1@39",
     "c2@39",
     "c3@39",
     "c4@39",
     "c5@39",
     "c6@39",
     "c0@40",
     "c1@40",
     "c2@40",
     "c3@40",
     "c4@40",
     "c5@40",
     "c6@40",
     "c0@41",
     "c1@41",
     "c2@41",
     "c3@41",
     "c4@41",
     "c5@41",
     "c6@41",
     "c0@42",
     "c1@42",
     "c2@42",
     "c3@42",
     "c4@42",
     "c5@42",
     "c6@42",
     "c0@43",
     "c1@43",
     "c2@43",
     "c3@43",
   
```

The full proposal stream is 680 rows in `candidates.jsonl`.

## The manual as it stands

```
# theory.dsl -- REWRITTEN FROM SCRATCH. This is not the world the previous
# manual described.
#
# WHY THE OLD MANUAL IS GONE, IN ONE PARAGRAPH
#
#   The store now reads: 6 states, 6 steps, 5 transitions, background 5,
#   97 dynamic cells, dynamic box rows 29-54 cols 10-63, colours seen
#   {0,1,2,3,4,5,6,8,9,14}, actions used A1 A2 A3 A4 A7. The manual I was
#   handed described 34 states, an 87-cell dynamic set at rows 8-18 and
#   row 63, a 5x5 body ring, a two-slot panel and a 64-cell meter bar. Not
#   one of those pixels exists in these frames. This is a different level
#   (the surprise says level 1) with a fresh store. Every rule, every
#   landmark and every count in that manual is about geometry that is not
#   on this board, so keeping any of it would be inventing pixels. I have
#   kept exactly three things from it and they are all method, not content:
#   price your defects in advance, never write a rule the diff did not
#   show you cell by cell, and check that a rule can fire before ranking a
#   probe that tests it.
#
# THE SURPRISE THAT BROUGHT ME HERE, AND MY ANSWER
#
#   certify: "theory.dsl is non-empty but generated/theory.py could not be
#   loaded". The old manual did not COMPILE, so replay, responsibility and
#   ambiguity all reported nothing. Two constructs in it are the plausible
#   causes and this manual removes both:
#     (1) `landmark spawn_probe  # arc-cell: carried, coordinates stripped`
#         -- the grammar says a landmark the level cannot place is a HARD
#         compile error, and "carried, coordinates stripped" is not a
#         coordinate. THIS MANUAL DECLARES NO LANDMARKS AT ALL. Every
#         discrimination below is done with colour and neighbour tests, so
#         there is nothing for the level to fail to place.
#     (2) a bare `goal:` header with an empty body. "No goal section at all
#         is legal"; an EMPTY one is not documented to be. THIS MANUAL HAS
#         NO GOAL SECTION.
#   I cannot bisect a compiler I cannot run, so I say plainly: I have
#   removed the two constructs I can argue for and I do not know which one
#   it was. If theory.py still fails to load, the cause is neither, and the
#   next desk should delete rule blocks in halves rather than re-reason.
#
# WHAT I ACTUALLY KNOW ABOUT THIS WORLD
#
#   Every one of the 97 dynamic cells is accounted for, and the account is
#   not my guess -- zero_space's single global law enumerates its cells and
#   they are exactly these four rectangles plus one corner pixel:
#     icon1  rows 30-35 x cols 11-16   36 cells
#     icon2  rows 36-41 x cols 11-16   36 cells
#     tape1  rows 32-33 x cols 17-22   12 cells
#     tape2  rows 38-39 x cols 17-22   12 cells
#     meter  (53,63)                    1 cell
#   36+36+12+12+1 = 97 = dynamic_cells, exactly.
#
#   Three of the five transitions are known cell by cell and are fully
#   ruled below. Two of them -- A1 and A2 -- were reported only as a count,
#   a bounding box and two colour sets, so I have NO cell-level evidence and
#   I write NO rule. That is the one large hole and I price it in advance:
#   replay will miss t1 and t2 by up to 96 cells each and be exact on
#   t3, t4, t5. Expect 3/5.

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

  theorem the_dynamic_set_is_four_rectangles_and_one_corner_pixel "THE LOAD-BEARING FACT OF THIS MANUAL, AND IT IS NOT MY GUESS. zero_space's single global law enumerates the cells it constrains and I read them off one by one: (30,11)-(30,16) through (41,11)-(41,16), which is a 12x6 column band; (32,17)-(32,22) and (33,17)-(33,22); (38,17)-(38,22) and (39,17)-(39,22); and (53,63). That is 72 + 12 + 12 + 1 = 97, and the store says dynamic_cells is 97. The bounding box of that set is rows 30-41 x cols 11-63, which is the reported box [29,10,54,63] padded by one on each side, so the two agree exactly and nothing is left over. I name the four parts by what the pixels look like rather than by what they do, because what they do is only partly known: ICON1 rows 30-35 cols 11-16, ICON2 rows 36-41 cols 11-16, TAPE1 rows 32-33 cols 17-22, TAPE2 rows 38-39 cols 17-22, METER (53,63). Note the alignment that makes the reading almost forced: each tape is exactly the middle two rows of its icon, extended six columns to the right. Two rows of a list, each an icon with a value strip beside it."
    [probe: passed]

  theorem the_census_closes_to_the_pixel_and_that_is_why_seven_types "Read the frame-0 colour of all 97 cells from the current frame (which IS frame 0 outside tape2, since s2 = s0 and s5 differs from s0 only in tape2 and the meter, and tape2's frame-0 colours are recoverable from the t4 diff). ICON1: cols 11,12,15,16 x rows 30-35 render background 5, that is 24 cells; cols 13,14 x rows 30,31,34,35 render 3, that is 8; cols 13,14 x rows 32,33 render 2, that is 4. ICON2: 22 cells of colour 6, 12 of colour 0, plus (38,16) colour 1 and (39,16) colour 2. TAPE1: 12 cells of colour 4. TAPE2, from the t4 diff's target colours: 8 of colour 1 and 4 of colour 2. METER: 1 of colour 2. By colour the totals are 0:12, 1:9, 2:10, 3:8, 4:12, 5:24, 6:22, summing to 97. TWO INDEPENDENT CHECKS PASS. First, 97 - 24 = 73 = cells_needing_an_owner exactly, and the 24 excluded are precisely the background-coloured ones -- so the store's `needing an owner` means `dynamic and not the background colour`, and Ink5 is the type that owns the 24 the store does not count. Second, 4096 - 97 = 3999 = constant_cells exactly. That is why there are seven types and not four: the arm looks objects up by colour and nothing else, so a type per frame-0 colour is the ONLY declaration that owns every dynamic cell. It buys no structure and I do not pretend it does -- ICON1 is spread across Ink5, Ink3 and Ink2 and no rule can say `icon1`."
    [depends: the_dynamic_set_is_four_rectangles_and_one_corner_pixel  probe: passed]

  theorem the_ninety_six_cell_transition_is_the_hole_and_here_is_its_price "A1 and A2 each changed 96 cells in rows 30-41 x cols 11-22 and the diff reported a COUNT, A BOX AND TWO COLOUR SETS AND NOTHING ELSE. 96 is exactly icon1 + icon2 + tape1 + tape2, so I know that EVERY dynamic cell of the widget area changes under A1 and again under A2 and that the meter does not. I also know A2 undoes A1: distinct_states is 5 against 6 states, so exactly one pair coincides, and it can only be s0 = s2 because s3, s4, s5 are separated from each other and from s0 by the tape and the meter. So A2 o A1 is the identity on this state. WHAT I DO NOT KNOW is which colour each of the 96 cells takes, and no amount of reasoning recovers it from a colour SET. THEREFORE I WRITE NO RULE. The compiled step is total, so my manual predicts identity for key(1) and key(2), which is KNOWN FALSE by 96 cells each. I state the bill before certify does: t1 misses 96, t2 misses 96, t3 t4 t5 are exact, expect replay 3/5. This is a defect of my evidence and not of my vocabulary, and it is repaired by one command and no thought at all -- see the_cheapest_command_on_this_board."
    [depends: the_dynamic_set_is_four_rectangles_and_one_corner_pixel  probe: passed]

  theorem the_cheapest_command_on_this_board "The frame I am shown each round is the CURRENT one, in full, over every cell that has ever changed. The frame I am NOT shown is s1, the configuration A1 produces, because it was two states ago and the diff that made it was summarised. So the entire content of the 96-cell hole is one press away: press key(1) now, and next round the current frame IS the other configuration, cell by cell, and the A1 and A2 rules can be written from pixels instead of guessed. Nothing else on this board buys 96 cells. The cost is exactly the refutation I priced above -- 96 divergent cells on a transition whose ignorance I declared in advance -- and it must not be read as the manual failing. A second press of key(1) afterwards is worth almost as much and answers a different question: if it returns to s0 the widget is a 2-cycle, and if it produces a third configuration it is a longer cycle or a scroll, which changes what a rule over it has to say."
    [depends: the_ninety_six_cell_transition_is_the_hole_and_here_is_its_price  probe: pending]

  theorem tape2_is_hidden_and_shown_and_the_guard_that_isolates_it "Three transitions, 12 cells each way, and they are the whole of what this manual predicts. In s0 the seven cells (38,16)-(38,22) render 1,2,1,1,2,1,1 and (39,16)-(39,22) render 2,1,1,2,1,1,2 -- one diagonal stripe pattern, colour 2 exactly where (row + col) mod 3 = 1 and colour 1 elsewhere, verified on all fourteen. Six of each row, cols 17-22, are dynamic; the col-16 pair never changes and is board. key(3) at t3 and key(7) at t5 turned all twelve to 4, the colour of the canvas they sit in; key(4) at t4 turned all twelve back to their stripe colours, each to its own. So the tape is SEVEN long when shown and ONE long when hidden, or equivalently the canvas is painted over it -- the two readings are the same pixels and I take the painting one because it is what a recolour rule can say. THE GUARD. `colored(above(above(?p)), 4)` is what separates the twelve tape cells from the other seven Ink1 and Ink2 instances, and I checked every one: (38,16) has (36,16) = 6, (39,16) has (37,16) = 6, the four icon1 cells at rows 32,33 cols 13,14 have (30,13)=(30,14)=(31,13)=(31,14) = 3, and the meter (53,63) has (51,63) = 5 -- all excluded, while every tape cell has (36,c) or (37,c) = 4. Twelve fire, seven do not, 12/12 on three transitions."
    [depends: the_dynamic_set_is_four_rectangles_and_one_corner_pixel  probe: passed]

  theorem the_guard_i_did_not_write_and_why "I considered conjoining `colored(below(below(?p)), 4)` to all six tape rules. It is TRUE of every one of the twelve tape cells -- (40,c) and (41,c) are canvas -- and it excludes not one instance that `colored(above(above(?p)), 4)` had not already excluded. It therefore has ZERO discriminating witnesses and constraint 3 keeps it out: a conjunct that explains no pixel does not earn a line. I am recording the confound rather than burying it, because the two guards differ on cells no frame has shown: after key(1) redraws the widget area, an Ink1 or Ink2 instance could land somewhere with canvas two above and something else two below, and there the one-atom guard fires and the two-atom guard does not. THE PROBE IS THE SAME PRESS I ALREADY WANT: expose the other configuration, then press key(3) in it. If twelve cells hide, the guard survives; if more than twelve hide, the second atom was load-bearing and goes back in. I have been burned before by deleting an unearned atom, and the lesson I took was not `never delete` -- it was `delete, and name the press that will answer you`."
    [depends: tape2_is_hidden_and_shown_and_the_guard_that_isolates_it  probe: pending]

  theorem tape1_has_never_been_shown "TAPE1, rows 32-33 cols 17-22, renders colour 4 in every one of the six observed frames, and yet all twelve of its cells are in zero_space's dynamic list. Both statements can only be true if TAPE1 was non-4 in some frame I was not shown at cell level -- which is s1, the A1 configuration. That is independent corroboration of the reading: the t1 diff's before-colour set contains 4, and the only dynamic cells rendering 4 in s0 are exactly these twelve. So A1 shows tape1 and hides or changes tape2, and A2 puts it back. It also says something about key(3), key(4) and key(7): all three touched only tape2, never tape1, in three transitions. Either those keys address the second list row specifically, or they address `the shown tape` and tape1 was already hidden. I cannot separate those two readings from here and I will not pretend to; one press of key(4) after the A1 press separates them, because it would act on tape1 under the first reading and on tape2 under the second."
    [depends: the_ninety_six_cell_transition_is_the_hole_and_here_is_its_price, tape2_is_hidden_and_shown_and_the_guard_that_isolates_it  probe: pending]

  theorem the_meter_pixel_has_one_witness_and_three_live_readings "(53,63) went 2 to 3 at t4 and at no other command. It sits at the right end of row 53, a row that renders 2 across the whole window and is otherwise constant, above row 54 which renders 4 across the whole window -- a status bar at the bottom of the screen with one cell consumed at its right edge. THREE READINGS FIT ONE WITNESS EQUALLY WELL. (A) key(4) advances it: 1/1, and it is what I wrote, because it is the only reading the guard language can express at all. (B) SHOWING the tape advances it, whatever key does the showing: also 1/1, and t4 is the only reveal in history. (C) it counts something else entirely -- a score, a move budget, a level timer -- that happened to tick once. WHAT KILLS THE READING THE PREVIOUS LEVEL TAUGHT ME: command-index parity predicted burns at indices 2 and 4 and only index 4 burned, so parity is REFUTED here and I do not carry it over. THE SEPARATOR IS ONE COMMAND AND I NAME ITS PREDICTION. The tape is hidden now and the meter renders 3, so my rule cannot fire; press key(4) and my manual predicts exactly 12 cells and no meter change. If the meter advances anyway, reading A is a counter rather than a one-shot and the guard `colored(?p, 2)` is wrong; if it does not, I have a negative witness where I currently have none."
    [depends: tape2_is_hidden_and_shown_and_the_guard_that_isolates_it  probe: pending]

  theorem three_and_seven_are_the_same_key_so_far_and_i_wrote_them_twice "key(3) at t3 and key(7) at t5 produced identical 12-cell effects, each from a state in which the tape was shown. I have one witness apiece and no state in which they differ. THE GRAMMAR HAS NO `or`, so `act=key(3) or act=key(7)` cannot be written and I paid four rules where two would do -- a doubling I am declaring rather than hiding, and the honest reason is expressiveness, not evidence. TWO THINGS ARE NOT THE SAME ABOUT THEM. key(7) returned ONE frame; key(1), key(2), key(3) and key(4) each returned TWO. cascade_lengths is [1,2] and max_frames_in_one_command is 2, so key(7) is the only single-frame command in this world's history. That is a free channel my semantics discards by construction -- cascade single_frame compares only the net -- and it is the only evidence that 3 and 7 are different mechanisms with a coinciding net effect. THE SEPARATOR: press one of them when the tape is already HIDDEN. If it is `hide`, nothing happens; if it is `toggle`, twelve cells show. Two presses separate hide from toggle for both keys, and my manual currently predicts nothing for either in that state -- an unwitnessed silence, which is the shape of claim this world has punished before."
    [depends: tape2_is_hidden_and_shown_and_the_guard_that_isolates_it  probe: pending]

  theorem silence_is_a_prediction_and_almost_all_of_mine_are_forged "The compiled step is total: where no rule fires the successor equals the current state, so my manual never says `I do not know`, it says `nothing happens`. Audit what it now claims from the current state s5, in which tape2 is hidden and the meter reads 3. key(1): predicted silent, KNOWN FALSE, 96 cells, declared. key(2): predicted silent, KNOWN FALSE, 96 cells, declared. key(3): predicted silent -- the hide rules need colour 1 or 2 and the tape renders 4 -- NO WITNESS, this is exactly the hide-versus-toggle question. key(7): same, NO WITNESS. key(4): predicted 12 cells shown and no meter change, and the meter half of that has NO WITNESS. key(5) and key(6): NEVER PRESSED IN THIS WORLD, predicted silent, no witness of any kind. So of seven keys, my manual has an honest witnessed prediction for none of them in this state, two known-false silences it has priced, and five untested claims. That is what six commands buys and I would rather post the number than dress it up."
    [depends: the_ninety_six_cell_transition_is_the_hole_and_here_is_its_price, three_and_seven_are_the_same_key_so_far_and_i_wrote_them_twice  probe: pending]

  theorem two_keys_have_never_been_pressed_and_one_of_them_is_probably_a_pointer "actions_used is A1 A2 A3 A4 A7 plus RESET; the alphabet is ACTION1..ACTION7. key(5) and key(6) are entirely unconstrained after six states. In this action family one command conventionally carries coordinates -- a click -- and that is a prior about the family, not evidence about this world; note that ACTION7 was used here and ACTION6 was not, which is mild evidence that the usual numbering does not hold. IT MATTERS BECAUSE OF WHAT THIS BOARD LOOKS LIKE: two icons, two value tapes, a scrollbar-shaped 2-wide colour-3 track at cols 13-14 with a colour-2 segment at rows 32-33, a large colour-4 canvas, a 4x4 colour-14 block at rows 31-34 cols 42-45 that has never changed, and a status bar. That is the anatomy of a MENU, and menus are usually pointed at. I CANNOT WRITE A CLICK RULE: the guard language admits act=key(6) but has nowhere to put two coordinates, so such a rule would fire on every click anywhere and be silently wrong about which cell was clicked. If a pointer drives this world my manual can record its EFFECT and never its precondition."
    [probe: pending]

  theorem what_the_current_frame_shows_outside_the_dynamic_set "Everything here is board and none of it earns an object, but a future desk will want it written down because the window hides it the moment it stops mattering. Cols 10-12 and 15-16 of rows 29 and above render background 5. Cols 13-14 render 3 at rows 29,30,31,34,35 and 2 at rows 32,33 -- a two-wide vertical track with a two-row segment in it, and row 29's pair is CONSTANT while rows 30-35 are dynamic, so the track extends above the window and only the part inside icon1 varies. The canvas is colour 4 filling rows 29-41 cols 17-46, with a 4x4 colour-14 block at rows 31-34 cols 42-45 that has not changed in six frames. Col 47 and beyond in rows 29-41 is background 5. Rows 42-52 are background 5 across the window. Row 53 is colour 2 across the window except (53,63); row 54 is colour 4 across the window. I HAVE NEVER SEEN rows 0-28 or rows 55-63, at any column, because the display only shows cells that have ever changed -- colours 8 and 9 appear in colours_seen and I cannot point at a single cell that holds them. That is a gap in my knowledge and not in the manual: those cells are constant, so board owns them, and no rule of mine references them."
    [probe: passed]

  theorem what_the_engines_gave_me "zero_space is the round's one useful engine and it gave me the census, not a law: its single global law enumerates exactly the 97 dynamic cells and that enumeration is what turned my four-rectangle reading from a guess into an arithmetic identity. Its own verdict on its laws is THIN in its own words -- 5 transitions constrain rank 3 of 679 features, null space dimension 676, nearly every vector in it true over these states and unfalsified rather than confirmed -- so I took the cell list and left the law. mdl_segmenter I REJECT WHOLESALE and its own numbers are why: both variants have NEGATIVE gain, -4037 bits at split_by_color=false and -10409 at true, so by its own measure its segmentation loses to writing the pixels out. Its tracks say what is wrong with connected_components(4) here: obj0 (frame 0), obj2 (frame 1), obj3 (frames 2-5) are all ~440-cell 13x36 blobs, which is one blob -- the canvas with the widgets embedded in it -- being re-identified as a new object every time any pixel inside it changes; obj1 is the 2x54 bottom bar. Four-connectivity cannot separate a widget from a canvas it is drawn on, and THAT ABSENCE IS THE FINDING. cegis_miner refused every track and its verdict, `the world does not narrate as one mover`, is TRUE here and not merely an artefact: nothing in six frames moved, everything recoloured in place."
    [probe: passed]

  theorem the_dsl_cannot_say_unknown_and_cannot_say_or "Two expressive holes, both paid for in this manual. FIRST: there is no third outcome for a (state, action) pair -- not `no change`, not a named successor, but `unobserved, the manual declines to predict`. So my complete ignorance of key(1) is emitted in the same voice as my three-times-witnessed knowledge of key(3), and only this prose distinguishes them. SECOND: guards join with `and` only. key(3) and key(7) have identical observed effects and I cannot write one rule for both, so six rules do the work of three and the manual is longer than the world. I record both rather than working around them, because a workaround here means inventing a distinction the evidence does not support. If a future desk gains one extension, ask for `or` before asking for anything else -- it is the one that would shorten this manual today."
    [depends: three_and_seven_are_the_same_key_so_far_and_i_wrote_them_twice  probe: passed]

  theorem there_is_no_goal_section_and_that_is_deliberate "No frame has ever reported anything but NOT_FINISHED and nothing in six states resembles a win. The candidates all fail and I would rather have no goal than a goal true in the wrong states, which stops a planner at its first step. `count(Ink2, color = 3) = 1` is true right now, in a state that is plainly not a win. `count(Ink4) = 0` is false at RESET and stays false forever, since instances are fixed by the arm. A goal over the meter would need me to know what the meter counts, and I have one witness and three readings for it. There is also a structural reason nothing can be named: `arc-instances: all` gives me Ink2_r53c63 and nine siblings, so there is no single instance to write `X.pos = exit_cell` about, and I have declared no landmarks at all after the compile failure. I name the price plainly: is_goal compiles to False, no plan terminates, and nothing ranks one command above another except what the playbook says -- which is why the playbook is about buying pixels rather than about reaching anything."
    [depends: the_census_closes_to_the_pixel_and_that_is_why_seven_types, two_keys_have_never_been_pressed_and_one_of_them_is_probably_a_pointer  probe: passed]

  theorem what_i_predict_before_i_see_it "Written in advance so it can cost me. State s5: tape2 hidden (rows 38-39 cols 17-22 all render 4), meter (53,63) renders 3, tape1 hidden, both icons in configuration s0. key(1): my manual predicts ZERO cells and the truth is 96 -- the largest wrong prediction in it, made on purpose, and the press I want, because it converts a summarised diff into a readable frame. key(2): the same 96-cell hole with nothing new bought, since A2 from here is not the A2 I have a witness for. key(3): my manual predicts ZERO and has NO witness -- if twelve cells appear, key(3) is a toggle and my four hide rules need their converses; if nothing happens, key(3) is `hide` and I gain a negative witness I currently lack. key(7): the identical experiment, and it additionally tests the one-frame-versus-two-frame difference. key(4): my manual predicts EXACTLY TWELVE cells shown and NO meter change; twelve-plus-one refutes `colored(?p, 2)` in the meter rule and tells me the meter counts rather than fires once. key(5), key(6): predicted silent, never pressed, and if either moves a pixel this manual learns a whole action. If key(1) is pressed and the 96 cells land where I cannot see them, that is not a refutation of anything I claimed -- read it by its divergence set."
    [depends: the_cheapest_command_on_this_board, the_meter_pixel_has_one_witness_and_three_live_readings  probe: pending]

  theorem a_manual_that_does_not_compile_predicts_nothing_at_all "The lesson of the surprise, kept because it is worth more than any rule above. The previous manual was thirty theorems long, replayed twenty-five transitions in earlier rounds and had a carefully argued account of its own defects -- and this round it scored NOTHING, because theory.py could not be loaded. Responsibility: empty. Replay: empty. Unambiguous: null. A manual that does not compile is not a slightly worse manual, it is no manual, and every hour of reasoning inside it is unbanked. TWO CONCRETE RULES FALL OUT. First, prefer constructs that cannot fail to be placed: this manual has no landmarks, no goal section and no domain, and every discrimination is a colour test on a cell reachable by above/below/leftof/rightof from an instance. Second, when a section is optional, OMIT IT rather than emit it empty -- an empty `goal:` header was legal-looking and may well have been the fault. Small and running beats large and dark, and this manual is deliberately the former."
    [probe: passed]
```

## The playbook as it stands

```
# playbook.dsl -- what to buy with the next command, not a route.
#
# ========= WHERE THIS ROUND STANDS =========
# The world changed under me: this is a new level with a fresh store, six
# states, 97 dynamic cells, none of the old geometry. The old manual did not
# compile, so it scored nothing at all. The new one is small, has no
# landmarks and no goal section, and predicts three of five transitions
# exactly.
#
# ========= THE BOARD AS THE MANUAL NOW SEES IT =========
#   97 dynamic cells, and every one has an owner:
#     icon1 rows 30-35 cols 11-16 (36)   icon2 rows 36-41 cols 11-16 (36)
#     tape1 rows 32-33 cols 17-22 (12)   tape2 rows 38-39 cols 17-22 (12)
#     meter (53,63) (1)
#   KNOWN CELL BY CELL: key(3) and key(7) hide tape2, twelve cells; key(4)
#   shows it, twelve cells, and advanced the meter once.
#   NOT KNOWN AT ALL: key(1) and key(2) each change all 96 widget cells and
#   the diff reported only a count, a box and two colour sets. key(5) and
#   key(6) have never been pressed.
#   Current state: tape2 hidden, tape1 hidden, meter reads 3.
#
# ========= THE ONE THING WORTH BUYING =========
# THE FRAME I AM SHOWN IS THE CURRENT ONE, IN FULL. The 96-cell hole is not
# a hole in my reasoning, it is a hole in what the summariser printed, and
# it closes the instant the other configuration BECOMES the current frame.
# Press the key whose diff was never itemised. Next round the pixels are on
# the page and two rules can be written from evidence instead of guessed.
#
# The advertised price: my manual predicts zero cells there and the world
# will change 96. That refutation is declared in advance, in the manual, in
# writing, and it must not be read as a defect. Every other command on this
# board buys at most twelve cells and most buy one.
#
# ========= THE THREE CHEAP QUESTIONS BEHIND IT =========
#   1. HIDE OR TOGGLE. tape2 is hidden now, so a hide-key pressed here does
#      nothing under one reading and shows twelve cells under the other. My
#      manual predicts silence and has NO witness for it.
#   2. ONE-SHOT OR COUNTER. The meter rule fires only on colour 2 and the
#      meter now reads 3, so my manual predicts the show-key moves twelve
#      cells and not thirteen. Thirteen refutes the guard.
#   3. TWO KEYS OR ONE. The two hide-keys have identical twelve-cell effects
#      and differ only in frame count, one versus two. Nothing separates
#      them yet and I wrote each rule twice because the grammar has no `or`.
#
# ------------------------------------------------------------------------
# Do not read a divergence on the widget area as a failed rule: there is no
# rule there, only a declared ignorance, and closing it is the whole plan.

order     buy_the_frame_the_summariser_refused_to_itemise                 [proof: lean]
order     close_a_declared_ignorance_before_refining_a_witnessed_rule     [proof: lean]
order     treat_predicted_silence_as_ignorance_unless_a_witness_backs_it  [proof: lean]
order     rank_by_witnesses_a_command_would_create_not_by_pixels_it_moves [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance              [proof: lean]
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

heuristic dynamic_cells_whose_colour_map_is_still_unknown                 [admissible: lean]
heuristic configurations_no_frame_has_ever_shown_in_full                  [admissible: lean]
heuristic keys_never_pressed_in_this_world                                [admissible: lean]
heuristic silences_the_manual_asserts_without_a_witness                   [admissible: lean]
heuristic live_readings_a_single_command_can_eliminate                    [admissible: lean]
heuristic divergent_cells_lying_outside_a_declared_ignorance              [admissible: lean]

prefer    the_key_whose_ninety_six_cell_diff_was_never_itemised           [ev: 2/5 commands]
prefer    a_state_that_makes_the_hidden_configuration_the_current_frame   [ev: 1/1 displays]
prefer    a_key_whose_predicted_silence_here_has_never_been_witnessed     [ev: 4/7 keys]
prefer    an_unpressed_key_over_a_key_already_at_full_coverage            [ev: 2/7 keys]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                [ev: 3/5 diffs]
prefer    the_press_that_splits_a_one_shot_from_a_counter                 [ev: 1/1 witnesses]
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
    30,
    11
   ],
   "manual_says": 5,
   "world_says": 6
  },
  {
   "cell": [
    30,
    12
   ],
   "manual_says": 5,
   "world_says": 6
  },
  {
   "cell": [
    30,
    13
   ],
   "manual_says": 3,
   "world_says": 6
  },
  {
   "cell": [
    30,
    14
   ],
   "manual_says": 3,
   "world_says": 6
  },
  {
   "cell": [
    30,
    15
   ],
   "manual_says": 5,
   "world_says": 6
  },
  {
   "cell": [
    30,
    16
   ],
   "manual_says": 5,
   "world_says": 6
  },
  {
   "cell": [
    31,
    11
   ],
   "manual_says": 5,
   "world_says": 6
  },
  {
   "cell": [
    31,
    12
   ],
   "manual_says": 5,
   "world_says": 0
  },
  {
   "cell": [
    31,
    13
   ],
   "manual_says": 3,
   "world_says": 0
  },
  {
   "cell": [
    31,
    14
   ],
   "manual_says": 3,
   "world_says": 0
  },
  {
   "cell": [
    31,
    15
   ],
   "manual_says": 5,
   "world_says": 0
  },
  {
   "cell": [
    31,
    16
   ],
   "manual_says": 5,
   "world_says": 6
  },
  {
   "cell": [
    32,
    11
   ],
   "manual_says": 5,
   "world_says": 6
  },
  {
   "cell": [
    32,
    12
   ],
   "manual_says": 5,
   "world_says": 0
  },
  {
   "cell": [
    32,
    13
   ],
   "manual_says": 2,
   "world_says": 6
  },
  {
   "cell": [
    32,
    14
   ],
   "manual_says": 2,
   "world_says": 6
  },
  {
   "cell": [
    32,
    15
   ],
   "manual_says": 5,
   "world_says": 0
  },
  {
   "cell": [
    32,
    16
   ],
   "manual_says": 5,
   "world_says": 1
  },
  {
   "cell": [
    32,
    17
   ],
   "manual_says": 4,
   "world_says": 2
  },
  {
   "cell": [
    32,
    18
   ],
   "manual_says": 4,
   "world_says": 1
  },
  {
   "cell": [
    32,
    19
   ],
   "manual_says": 4,
   "world_says": 1
  },
  {
   "cell": [
    32,
    20
   ],
   "manual_says": 4,
   "world_says": 2
  },
  {
   "cell": [
    32,
    21
   ],
   "manual_says": 4,
   "world_says": 1
  },
  {
   "cell": [
    32,
    22
   ],
   "manual_says": 4,
   "world_says": 1
  }
 ],
 "cells_wrong": 96,
 "kind": "frame_mismatch",
 "t": 0
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
     30,
     11
    ],
    "manual_says": 5,
    "world_says": 6
   },
   {
    "cell": [
     30,
     12
    ],
    "manual_says": 5,
    "world_says": 6
   },
   {
    "cell": [
     30,
     13
    ],
    "manual_says": 3,
    "world_says": 6
   },
   {
    "cell": [
     30,
     14
    ],
    "manual_says": 3,
    "world_says": 6
   },
   {
    "cell": [
     30,
     15
    ],
    "manual_says": 5,
    "world_says": 6
   },
   {
    "cell": [
     30,
     16
    ],
    "manual_says": 5,
    "world_says": 6
   },
   {
    "cell": [
     31,
     11
    ],
    "manual_says": 5,
    "world_says": 6
   },
   {
    "cell": [
     31,
     12
    ],
    "manual_says": 5,
    "world_says": 0
   },
   {
    "cell": [
     31,
     13
    ],
    "manual_says": 3,
    "world_says": 0
   },
   {
    "cell": [
     31,
     14
    ],
    "manual_says": 3,
    "world_says": 0
   },
   {
    "cell": [
     31,
     15
    ],
    "manual_says": 5,
    "world_says": 0
   },
   {
    "cell": [
     31,
     16
    ],
    "manual_says": 5,
    "world_says": 6
   },
   {
    "cell": [
     32,
     11
    ],
    "manual_says": 5,
    "world_says": 6
   },
   {
    "cell": [
     32,
     12
    ],
    "manual_says": 5,
    "world_says": 0
   },
   {
    "cell": [
     32,
     13
    ],
    "manual_says": 2,
    "world_says": 6
   },
   {
    "cell": [
     32,
     14
    ],
    "manual_says": 2,
    "world_says": 6
   },
   {
    "cell": [
     32,
     15
    ],
    "manual_says": 5,
    "world_says": 0
   },
   {
    "cell": [
     32,
     16
    ],
    "manual_says": 5,
    "world_says": 1
   },
   {
    "cell": [
     32,
     17
    ],
    "manual_says": 4,
    "world_says": 2
   },
   {
    "cell": [
     32,
     18
    ],
    "manual_says": 4,
    "world_says": 1
   },
   {
    "cell": [
     32,
     19
    ],
    "manual_says": 4,
    "world_says": 1
   },
   {
    "cell": [
     32,
     20
    ],
    "manual_says": 4,
    "world_says": 2
   },
   {
    "cell": [
     32,
     21
    ],
    "manual_says": 4,
    "world_says": 1
   },
   {
    "cell": [
     32,
     22
    ],
    "manual_says": 4,
    "world_says": 1
   }
  ],
  "cells_wrong": 96,
  "kind": "frame_mismatch",
  "t": 0
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

=== PLAYBOOK ===
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

=== LOG ===
```json
[
  {"id": "O-01", "subject": "mdl_segmenter obj0/obj2/obj3 (~440-cell 13x36 blobs)", "verdict": "reject",
   "as": null, "why": "all three are the same connected component -- the colour-4 canvas with the widgets embedded in it -- re-identified as a new track whenever any interior pixel changes; the engine's own gain is negative (-4037 bits, -10409 bits), so by its own measure the segmentation loses to writing the pixels out."},
  {"id": "O-02", "subject": "mdl_segmenter obj1 (2x54 bottom bar)", "verdict": "entailed",
   "as": "board rows 53-54 plus the single Ink2 instance at (53,63)", "why": "the bar is constant in every frame except its rightmost pixel, so 107 of its 108 cells are board by definition and the one that varies is already owned by Ink2."},
  {"id": "O-03", "subject": "zero_space's enumerated 97-cell support", "verdict": "accept",
   "as": "the seven Ink types, one instance per dynamic cell, typed by frame-0 colour", "why": "the enumeration is exactly icon1 36 + icon2 36 + tape1 12 + tape2 12 + meter 1 = 97 = dynamic_cells, and the per-colour census 12+9+10+8+12+24+22 closes to 97 with 97-24=73=cells_needing_an_owner and 4096-97=3999=constant_cells."},
  {"id": "O-04", "subject": "the 24 cells of cols 17-22 at rows 30,31,34,35 that zero_space omits", "verdict": "accept",
   "as": "board", "why": "they are the swap partners that hold canvas-4 on both sides, which is why a swap leaves them constant -- and their omission is what makes the changed count 96 rather than 144."},
  {"id": "R-01", "subject": "key(1) as a six-row block swap of rows 30-41 x cols 11-22", "verdict": "accept",
   "as": "eighteen a1_* rules, one per (Ink type, destination colour)", "why": "certify printed 24 divergent cells at t=0 and all 24 equal the current frame's colour six rows below them; independently, 72 partner pairs minus 24 canvas-on-both-sides pairs times 2 equals the reported 96 changed cells."},
  {"id": "R-02", "subject": "key(2) as the inverse swap", "verdict": "accept",
   "as": "eight a2_* rules, one per Ink type", "why": "s2 = s0 (distinct_states 5 against 6 states, and s3,s4,s5 are separated by the strip and the meter), so A2 from s1 restores every instance to its frame-0 colour, which is the same partner-copy specialised to that state."},
  {"id": "R-03", "subject": "the Ink2 top/bottom split by free(six-below)", "verdict": "accept",
   "as": "guard free(below^6(?p)) on the lower-block Ink2 rules", "why": "a lower Ink2's six-below lands in rows 44-45, background in every state; an upper Ink2's six-below lands in the lower block, which renders background only where icon1's field sits and that field is Ink5, never Ink2."},
  {"id": "R-04", "subject": "excluding the meter from the swap rules", "verdict": "accept",
   "as": "guard not rightof(?p) = wall on all five Ink2 swap rules", "why": "the meter has (47,63)=5 so a1_lower_ink2_takes_5 would fire on it whenever (59,63) renders background, and (59,63) is a cell no frame has ever shown; the diffs show the meter unchanged at t1 and t2."},
  {"id": "R-05", "subject": "generalised hide/show rules for the strip after a swap", "verdict": "reject",
   "why": "in s1 the stripe content is Ink4 and Ink5 instances at rows 32-33, and no transition has ever shown key(3), key(4) or key(7) acting on them; constraint 2 forbids the rule and the theorem the_hide_and_show_rules_are_pinned_to_rows_38_39 names the two-press probe that would witness it."},
  {"id": "R-06", "subject": "a3/a7 hide rules written twice because the grammar has no `or`", "verdict": "accept",
   "as": "four rules where two would do", "why": "key(3) and key(7) have identical 12-cell effects with one witness apiece and nothing separating them but frame count, and guards join with `and` only."},
  {"id": "R-07", "subject": "cegis_miner's verdict that the world does not narrate as one mover", "verdict": "accept",
   "as": "no move/jump/teleport event anywhere in the manual", "why": "the swap relocates 96 cells at once and every other transition is a recolour in place; nothing in six frames translates a single object."},
  {"id": "L-01", "subject": "zero_space's single global law", "verdict": "reject",
   "why": "its own evidence_adequacy says THIN -- 5 transitions constrain rank 3 of 679 features, null space dimension 676 -- so the law is unfalsified rather than confirmed; I kept its enumerated cell list, which is an observation, and left the law."},
  {"id": "L-02", "subject": "a goal section", "verdict": "reject",
   "why": "every state reports NOT_FINISHED, count(Ink2, color = 3) = 1 is already true in a plainly non-winning state, and arc-instances: all leaves no single instance to name; is_goal compiles to False and the playbook ranks by information instead."},
  {"id": "P-01", "subject": "swap versus scroll-by-one", "verdict": "probe-pending",
   "why": "with two entries and wrapping the two permutations coincide; two presses of key(1) separate them, and a third configuration would mean my key(1) colour enumeration is complete only for the witnessed pair."},
  {"id": "P-02", "subject": "hide versus toggle for key(3) and key(7)", "verdict": "probe-pending",
   "why": "the strip is hidden now, so my manual predicts silence with no witness; one press gives either a negative witness I lack or twelve cells that force four converse rules."},
  {"id": "P-03", "subject": "the meter as one-shot versus counter", "verdict": "probe-pending",
   "why": "the meter renders 3 so a4_advances_the_corner_pixel cannot fire; key(4) from here predicts exactly twelve cells and no meter change, and thirteen refutes the colored(?p, 2) guard."},
  {"id": "P-04", "subject": "whether key(3)/key(4)/key(7) address a screen row or a list entry", "verdict": "probe-pending",
   "why": "key(1) then key(4): twelve cells at rows 38-39 means row-addressed and my typed rules are accidentally right; twelve at rows 32-33 means entry-addressed and they are wrong in the swapped state."},
  {"id": "P-05", "subject": "key(5) and key(6), never pressed", "verdict": "probe-pending",
   "why": "every other key is now ruled, so these two and a possible click are the only places a win condition or a new mechanism can still be hiding."},
  {"id": "E-01", "subject": "copying a colour from one cell to another", "verdict": "probe-pending",
   "why": "I wanted one rule saying `?p takes the colour of the cell six rows away`; recolored takes an integer literal and colored takes an integer literal, so I wrote 26 rules enumerating every (type, destination colour) pair the witness exhibits, and the enumeration is complete for the witnessed configuration pair and for no other."},
  {"id": "E-02", "subject": "a positional guard for `is this instance in the upper block`", "verdict": "probe-pending",
   "why": "there is no row predicate; I used the object types, which are frozen at frame 0 and therefore permanent, and split the one type spanning both blocks by free(below^6(?p)) plus a wall test for the meter."},
  {"id": "E-03", "subject": "disjunction for key(3) and key(7)", "verdict": "probe-pending",
   "why": "guards join with `and` only, so act=key(3) or act=key(7) cannot be written and four rules do the work of two; if one grammar extension were available this is the one that would shorten the manual today."},
  {"id": "E-04", "subject": "a third outcome meaning `unobserved, the manual declines to predict`", "verdict": "probe-pending",
   "why": "the compiled step is total, so my complete ignorance of key(5) is emitted in the same voice as my three-times-witnessed knowledge of key(3); only the theorem silence_is_a_prediction distinguishes them."}
]
```
```
