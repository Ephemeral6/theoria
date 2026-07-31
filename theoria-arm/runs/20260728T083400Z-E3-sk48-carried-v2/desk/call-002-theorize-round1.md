# call-002-theorize-round1

model: `claude-opus-5` · 610485 ms · $1.483410 · usage {"cache_creation": {"ephemeral_1h_input_tokens": 27303, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 27303, "cache_read_input_tokens": 0, "inference_geo": "not_available", "input_tokens": 2, "iterations": [{"cache_creation": {"ephemeral_1h_input_tokens": 27303, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 27303, "cache_read_input_tokens": 0, "input_tokens": 2, "output_tokens": 47585, "type": "message"}], "output_tokens": 47585, "server_tool_use": {"web_fetch_requests": 0, "web_search_requests": 0}, "service_tier": "standard", "speed": "standard"}

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
    "ms": 4,
    "script_bits": 7512,
    "split_by_color": false,
    "tracks": 4
   },
   {
    "baseline_bits": 3475,
    "compression_ratio": 3.995396,
    "events": 61,
    "gain_bits": -10409,
    "ms": 16,
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
# theory.dsl -- FIRST DRAFT AGAINST THIS WORLD. The manual I was handed
# describes a different board: an 8x6 lattice at rows 8-56, a HUD at rows 1-7,
# a 64-pixel tally at row 63, a 5x5 colour-9 ring, 74 dynamic cells, 69
# unexplained. NONE of that survives contact with the evidence in front of me:
# the dynamic set here is 97 cells in rows 30-41 x cols 11-22 plus the single
# cell (53,63); there is no colour 9 and no colour 8 anywhere in the dynamic
# set; the actions are 1,2,3,4,7 and key(5) has never been pressed. I discard
# the old manual wholesale rather than patch it. Nothing is carried over.
#
# WHAT I GOT THIS ROUND, AND IT IS THE WHOLE ROUND: frame 0 is now known
# EXACTLY, and the object inventory is forced rather than guessed.
#
#   (a) distinct_states = 5 over six states S0..S5. S3,S4,S5 are pairwise
#       distinct and all differ from S0 and S1 (the meter cell (53,63) or the
#       12 strip cells separate them); S1 cannot equal S3 without contradicting
#       the 96-cell diff at t2. The ONLY possible coincidence is S2 = S0.
#       Therefore ACTION2 exactly undid ACTION1. Deduced, not assumed.
#   (b) S2 = S0 plus the t3/t4/t5 diffs run backwards gives frame 0 cell for
#       cell: it is the frame I was shown, except rows 38-39 x cols 17-22 hold
#       2 1 1 2 1 1 / 1 1 2 1 1 2 instead of colour 4, and (53,63) is 2 not 3.
#   (c) That reconstruction was then CHECKED TWICE against numbers I did not
#       use to build it. The dynamic set it implies is exactly
#       {rows 30-35 x cols 11-16} u {rows 36-41 x cols 11-16} u
#       {rows 32-33 x cols 17-22} u {rows 38-39 x cols 17-22} u {(53,63)}
#       = 36 + 36 + 12 + 12 + 1 = 97, and the store says dynamic_cells = 97.
#       Its non-background frame-0 population is 22 (colour 6) + 12 (colour 0)
#       + 8 (colour 3) + 10 (colour 2) + 9 (colour 1) + 12 (colour 4) = 73,
#       and the store says cells_needing_an_owner = 73. Two independent
#       arithmetic closures on a reconstruction built from neither number.
#   (d) The old manual never used arc-instances: all, which is why it sat at
#       69-72 unexplained pixels and called that a ceiling. It is not a
#       ceiling. Six colour classes with arc-instances: all own all 73 cells.
#       I therefore make a hard, falsifiable prediction: the next
#       responsibility report on frame 0 reads 0 unexplained. If it does not,
#       the arm anchors instances from the union of frames rather than from
#       frame 0, and the residue will be exactly the 12 strip cells whose
#       colour differs between frame 0 and the later frames -- that is the one
#       alternative and it is pre-registered below.
#
# WHAT I STILL CANNOT WRITE: the 96-cell swap that ACTION1 and ACTION2 perform.
# It relocates a 6x6 widget by six rows and it is 96 simultaneous recolourings
# that this event vocabulary can only express one instance at a time with no
# guard that selects a row band. I refuse to fake it with 96 pixel rules that
# buy no compression. Replay will therefore fail at t1 and t2 and pass at
# t3, t4, t5 -- 3/5, up from 0/5 -- and that too is pre-registered.

semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Casing { pos: Coord, color: Int }  # arc-colour: 6  arc-instances: all
  object Cavity { pos: Coord, color: Int }  # arc-colour: 0  arc-instances: all
  object Rail { pos: Coord, color: Int }  # arc-colour: 3  arc-instances: all
  object Pip { pos: Coord, color: Int }  # arc-colour: 1  arc-instances: all
  object Stud { pos: Coord, color: Int }  # arc-colour: 2  arc-instances: all
  object Erased { pos: Coord, color: Int }  # arc-colour: 4  arc-instances: all
  landmark slot_a_head  # arc-cell: (30, 11)
  landmark slot_b_head  # arc-cell: (36, 11)
  landmark strip_a_head  # arc-cell: (32, 17)
  landmark strip_b_head  # arc-cell: (38, 17)
  landmark meter_tip  # arc-cell: (53, 63)
  landmark badge_cell  # arc-cell: (31, 42)
  Casing [segment: colour_class_6 ev: t0-t5 compress: 22]
  Cavity [segment: colour_class_0 ev: t0-t5 compress: 12]
  Rail [segment: colour_class_3 ev: t0-t5 compress: 8]
  Pip [segment: colour_class_1 ev: t0-t5 compress: 9]
  Stud [segment: colour_class_2 ev: t0-t5 compress: 10]
  Erased [segment: colour_class_4 ev: t0-t5 compress: 12]

events:
  event recolored(o, c)

rules:
  rule key3_blanks_the_strip_pips forall ?p in Pip [ev: t3 cov: 8/8]
    when act=key(3) and colored(?p, 1) and not colored(leftof(?p), 0) and not colored(leftof(?p), 5) and not colored(rightof(?p), 5) and not colored(above(?p), 5) then recolored(?p, 4)

  rule key3_blanks_the_strip_studs forall ?p in Stud [ev: t3 cov: 4/4]
    when act=key(3) and colored(?p, 2) and not colored(leftof(?p), 0) and not colored(leftof(?p), 5) and not colored(rightof(?p), 5) and not colored(above(?p), 5) then recolored(?p, 4)

  rule key7_blanks_the_strip_pips forall ?p in Pip [ev: t5 cov: 8/8]
    when act=key(7) and colored(?p, 1) and not colored(leftof(?p), 0) and not colored(leftof(?p), 5) and not colored(rightof(?p), 5) and not colored(above(?p), 5) then recolored(?p, 4)

  rule key7_blanks_the_strip_studs forall ?p in Stud [ev: t5 cov: 4/4]
    when act=key(7) and colored(?p, 2) and not colored(leftof(?p), 0) and not colored(leftof(?p), 5) and not colored(rightof(?p), 5) and not colored(above(?p), 5) then recolored(?p, 4)

  rule key4_restores_the_strip_pips forall ?p in Pip [ev: t4 cov: 8/8]
    when act=key(4) and colored(?p, 4) then recolored(?p, 1)

  rule key4_restores_the_strip_studs forall ?p in Stud [ev: t4 cov: 4/4]
    when act=key(4) and colored(?p, 4) then recolored(?p, 2)

  rule key4_advances_the_meter forall ?p in Stud [ev: t4 cov: 1/1]
    when act=key(4) and colored(?p, 2) and colored(above(?p), 5) and colored(below(?p), 4) then recolored(?p, 3)

laws:
  invariant casing_population count(Casing) = 22 [status: derived]
  invariant cavity_population count(Cavity) = 12 [status: derived]
  invariant rail_population count(Rail) = 8 [status: derived]
  invariant pip_population count(Pip) = 9 [status: derived]
  invariant stud_population count(Stud) = 10 [status: derived]
  invariant erased_population count(Erased) = 12 [status: derived]

  theorem frame_zero_is_reconstructed_exactly "frame 0 equals the frame I was shown with two edits: rows 38-39 x cols 17-22 hold 2 1 1 2 1 1 over 1 1 2 1 1 2 instead of colour 4, and (53,63) holds 2 instead of 3. The chain is forced. distinct_states = 5 over six states, and every pair except (S0,S2) is separated by the meter cell or by the 96-cell t2 diff, so S2 = S0 and ACTION2 exactly undid ACTION1. Running t3, t4, t5 backwards from the current frame then reaches S2 = S0. The reconstruction was checked against two numbers it was not built from: it implies a dynamic set of 36 + 36 + 12 + 12 + 1 = 97 cells and the store reports 97, and a non-background frame-0 population of 22 + 12 + 8 + 10 + 9 + 12 = 73 and the store reports cells_needing_an_owner = 73. Both close to the unit. This is the load-bearing entry of the manual and everything below rests on it."
    [probe: passed]

  theorem the_panel_is_two_slots_one_of_them_expanded "the moving part of this world is a panel of two stacked slots at cols 11-16, slot A at rows 30-35 and slot B at rows 36-41, each with a 2x6 strip lying to its right inside the arena at cols 17-22 on its two centre rows -- rows 32-33 for A and rows 38-39 for B. Exactly one slot is expanded at a time. The expanded slot is drawn as a 6x6 colour-6 casing with a colour-0 cavity, a 2x2 colour-6 core at its centre rows and cols 13-14, and two port cells at its right edge showing colour 1 over colour 2. The collapsed slot is drawn as a bare 2-wide stack at cols 13-14, colour 3 at its four outer rows and colour 2 at its two centre rows. In frame 0 slot B is expanded and slot A is collapsed. The arithmetic that forces this: the expanded and collapsed drawings differ in every one of the 36 positions, so a swap changes 72 casing cells, and the two strips change 12 each, giving exactly 96 -- which is exactly what t1 and t2 each reported, over exactly rows 30-41 x cols 11-22."
    [depends: frame_zero_is_reconstructed_exactly  probe: pending]

  theorem the_swap_is_inexpressible_and_i_refuse_to_fake_it "ACTION1 and ACTION2 swap which slot is expanded and are exact inverses of each other. I can state that and I cannot compile it. The event vocabulary moves one instance one cell or recolours one instance to one integer literal; the swap relocates a 6x6 widget by six rows, which is 96 simultaneous recolourings whose target colours differ per cell, and the guard language has no way to say -- the instances in rows 30-35 -- because there is no coordinate expression and no landmark comparison that grounds over a row band. I could write 96 single-instance rules. Each would explain one pixel and cost more than the pixel, which fails the gain test outright, and it would still not generalise to a third slot. So this manual predicts NO CHANGE for key(1) and key(2), which is wrong, and I say so here rather than let the reader discover it. Consequence, pre-registered: replay diverges first at t=1 with 96 cells wrong, and t3, t4, t5 replay exactly, giving 3/5."
    [depends: the_panel_is_two_slots_one_of_them_expanded  probe: pending]

  theorem the_strip_toggles_and_only_key_four_costs_anything "key(3) at t3 and key(7) at t5 each blanked all 12 cells of the expanded slot strip to the arena colour 4; key(4) at t4 restored exactly the same 1 and 2 pattern, cell for cell, and additionally advanced the meter cell (53,63) from 2 to 3. The pattern is therefore stored somewhere the frame does not show and is not destroyed by blanking. Over five commands the meter ticked once and only under key(4), so key(4) is the metered action and keys 1, 2, 3, 7 are free. One witness each: key(3) and key(7) may be a blank action and a toggle action that happened to agree because the strip was shown both times, and key(4) may be a show action or a toggle action that happened to agree because the strip was blank. Nothing in the record separates blank from toggle for any of the three. The cheapest separator is to press key(3) twice in a row from a shown strip."
    [depends: frame_zero_is_reconstructed_exactly  probe: pending]

  theorem cascade_length_carries_no_signal_here "t1, t2, t3 and t4 returned 2 frames each and t5 returned 1, yet t3 and t5 produced identical 12-cell effects. So frame count does not track the magnitude or even the presence of change, and it must not be used as a motion detector the way the discarded manual used it. What it may still carry is that ACTION7 and ACTION3 are genuinely different actions with the same visible result in this state -- one animates and one does not. That is a hint about key identity, not about the world state."
    [probe: pending]

  theorem colour_classes_are_not_the_worlds_objects_and_i_admit_the_cost "the six declared types are colour classes, not things. Stud alone spans the collapsed slot core, a port cell of the expanded slot, four strip cells and the meter tip, which are four unrelated roles; Casing and Cavity together are one widget. The world segments by widget and the arm segments by colour, and the arm wins because the arm is what draws the frame. What this buys is real and I claim it: six declarations own all 73 cells that need an owner, against 73 pixels written out, and seven rules over those classes reproduce three of the five transitions exactly. What it costs is also real: because a class is not a widget, no rule can name the strip as such, and every strip rule has to carve the strip out of its class with four negative neighbour guards -- not colour 0 to the left, not colour 5 to the left, not colour 5 to the right, not colour 5 above. Those four negations are pixel-fitting wearing a guard costume. They are correct on every instance of both classes in frame 0, which I checked one by one, and they are the price of the colour-first arm."
    [depends: the_panel_is_two_slots_one_of_them_expanded  probe: pending]

  theorem instance_anchoring_has_one_alternative_and_it_is_pre_registered "I predict the next responsibility report on frame 0 reads 0 unexplained. That holds if arc-instances: all enumerates cells of the declared colour in FRAME 0 that the board cannot explain. The alternative is that it enumerates over the union of all observed frames, in which case the 12 strip cells are claimed twice -- once by Pip or Stud from frame 0 and once by Erased from frames 3 and 5 -- and (53,63) is claimed by both Stud and Rail. Under that alternative the report will not read 0 and the residue will be drawn from exactly those 13 cells and no others. Any residue outside those 13 cells refutes frame_zero_is_reconstructed_exactly and I would rebuild the manual from the reported cells rather than defend it."
    [depends: frame_zero_is_reconstructed_exactly  probe: pending]

  theorem the_meter_is_long_so_exploration_is_cheap_now "row 53 is a colour-2 bar running at least cols 10 to 62 with the tip at col 63, and one unit has been consumed. Whether it extends left of col 10 I cannot see, because everything left of the window has held one colour throughout and is board by definition -- so at least 54 units, possibly many more, against one spent. This is the opposite of the situation the discarded manual described, where two attempts remained and every press was a bet. Here the correct posture is to spend free presses freely and metered presses deliberately. I do not know whether the bar filling to the tip is a loss, a win, or neither, and nothing in five commands speaks to it."
    [probe: pending]

  theorem two_keys_have_never_been_pressed "ARC offers ACTION1..ACTION7 and this world has seen 1, 2, 3, 4 and 7. key(5) and key(6) are unpressed and unknown. In this family key(6) is customarily a click carrying coordinates, which this guard language cannot express at all -- if that is what it is, it will need a probe reported as prose and never as a rule. Given the meter is long, I hold no fear of pressing either, and the playbook says to do it early rather than late, while a wrong outcome is still cheap to absorb."
    [depends: the_meter_is_long_so_exploration_is_cheap_now  probe: pending]

  theorem the_arena_and_its_untouched_badge "the arena is a colour-4 rectangle spanning cols 17 to 46 across rows 29 to 41 at least, bounded below by background from row 42 and by a solid colour-4 band at row 54. Inside it, rows 31-34 x cols 42-45 is a 4x4 block of colour 14, the only colour 14 in the window, and it has never changed. Colours 8 and 9 appear in the store's colour list but on no dynamic cell and nowhere in rows 29-54, so they live in the constant region above row 29 and are board. The badge is the only structure in the arena that is neither the two strips nor uniform fill, which makes it the natural candidate for whatever the strips are being compared against -- a reading with zero transitions behind it, recorded because it is the first thing to test once the strips are readable."
    [probe: pending]

  theorem no_goal_section_on_purpose "every command returned NOT_FINISHED and nothing in five transitions indicates what finishing means. The candidates are that the strips must be brought to match the badge, that the meter must be filled, or that something outside the window entirely is the objective. Writing any of them as a goal would compile to a claim refuted by the first win or, worse, would make the searcher chase a fiction. An absent goal compiles to is_goal -> False, which under-claims and costs one round; a wrong goal over-claims and costs the level. I under-claim."
    [depends: the_arena_and_its_untouched_badge  probe: pending]

  theorem what_the_engines_offered_and_why_most_of_it_was_declined "mdl_segmenter returned negative gain on both variants, -4037 bits with 4 tracks and -10409 bits with 33, and its tracks are 440-cell and 436-cell blobs of shape 13x36 with colour null -- the whole panel plus arena fused under connected_components(4). That is a fact about the operator, not about the world, and I accept the fusion while rejecting it as a segmentation. cegis_miner refused every track because its precondition is exactly one move event per transition, and this world has no mover at all; its verdict that the world does not narrate as one mover is correct and unhelpful. zero_space reports its own evidence as THIN -- 5 transitions constraining rank 3 of 679 features -- and its single global law spans nearly every dynamic cell at once, which is what a null space of dimension 676 produces and not what a conservation law looks like. I take one thing from the engine round and it is the store arithmetic: dynamic_cells 97 and cells_needing_an_owner 73, both of which closed against a reconstruction built without them."
    [probe: pending]
```

## The playbook as it stands

```
# playbook.dsl -- the compiled manual predicts three of five transitions and is
# silent on the two that matter most, so the searcher gets the strip toggle for
# free and gets nothing routable for the selector swap. Everything about the
# swap lives here. Five facts drive this playbook:
#
#   ACTION1 and ACTION2 are exact inverses and they swap which of two slots is
#     expanded -- deduced from distinct_states = 5, not guessed;
#   only ACTION4 has ever advanced the meter at (53,63); ACTION1, ACTION2,
#     ACTION3 and ACTION7 have each been pressed at least once with no tick,
#     so they are free and should be spent without hesitation;
#   the meter is at least 54 units long and one is gone, so this is an
#     exploration phase, not an endgame -- the opposite posture to a world with
#     two attempts left;
#   strip A has been visible for exactly one state in the whole record and its
#     pattern has never been read; strip B reads 2 1 1 2 1 1 over 1 1 2 1 1 2;
#   ACTION5 and ACTION6 have never been pressed, and one of them is likely the
#     coordinate click this guard language cannot express at all.

order   read_the_meter_tip_and_the_frame_count_after_every_command       [proof: lean]
order   spend_the_free_keys_before_the_metered_key                       [proof: lean]
order   expand_the_slot_whose_strip_has_never_been_read                  [proof: lean]
order   separate_blank_from_toggle_before_trusting_either_reading        [proof: lean]
order   press_the_two_never_pressed_keys_while_the_meter_is_still_long   [proof: lean]
order   compare_a_strip_against_the_badge_before_committing_the_meter    [proof: lean]

prefer  a_key_never_pressed_over_a_key_whose_effect_is_already_known     [ev: 2/7 keys unpressed]
prefer  a_key_that_has_never_ticked_the_meter_over_the_one_that_did      [ev: 1/1 meter ticks attributed]
prefer  the_selector_pair_over_the_strip_pair_while_mapping_the_panel    [ev: 96 cells vs 12 cells per press]
prefer  repeating_a_key_from_the_state_it_already_produced               [ev: 2/2 blanking presses agreed]
prefer  a_state_in_which_the_unread_strip_is_showing                     [ev: 1/6 states showed strip a]
prefer  reading_the_untouched_arena_block_before_theorising_about_it     [ev: 1/1 non_uniform arena figures]

heuristic meter_units_still_unspent_in_row_fifty_three                   [admissible: lean]
heuristic strip_patterns_still_unread_in_the_panel                       [admissible: lean]
heuristic keys_whose_effect_is_still_a_single_witness                    [admissible: lean]

prune   meter_exhausted and not goal => dead                             [proof: lean]
prune   repeat_of_a_key_that_left_this_exact_state_unchanged => dead     [proof: lean]
prune   undoing_the_selector_press_that_just_revealed_something => dead  [proof: lean]
prune   metered_press_while_a_free_press_is_still_untried => dead        [proof: lean]
prune   both_strips_read_and_no_hypothesis_about_the_badge => dead       [proof: lean]
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
  "clashes": [],
  "detail": "no (state, action) among 6 x 3 admitted two rules",
  "ok": true,
  "scope": "sampled",
  "states": 6
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
# theory.dsl -- SECOND DRAFT. The first draft was written blind against frame 0
# and came back with two hard numbers: responsibility 0/4096 unexplained, and
# replay 4/5 with first divergence at t=0. Both of those are results, not
# scores, and this round is mostly about reading them.
#
# WHAT THE CERTIFY OUTPUT ACTUALLY PROVED
#
#   (1) responsibility ok, 0 unexplained. The pre-registered question
#       instance_anchoring_has_one_alternative resolves in favour of the first
#       branch: arc-instances: all enumerates cells of the declared colour in
#       FRAME 0 that the board cannot explain. The 12 strip cells are NOT
#       double-claimed and (53,63) is NOT double-claimed. Six colour classes
#       own all 73 cells. That question is now closed and I write it as passed.
#
#   (2) replay says 4/5 and first_divergence says t=0. Those two look
#       contradictory and they are not: they can only both be true if replay is
#       OPEN LOOP -- the manual is run forward from frame 0 without being
#       resynced to the world. My manual is silent on key(1) and key(2), so its
#       state after both is still frame 0; the world went S0 -> S1 -> S2 and
#       matched again at t=1. That is a MEASUREMENT, from the harness rather
#       than from my arithmetic, that S2 = S0 exactly, cell for cell. The
#       deduction in frame_zero_is_reconstructed_exactly is no longer a
#       deduction. It is confirmed, and with it the whole reconstruction, since
#       t2..t5 then replayed exactly on top of it.
#
#   (3) 4/5 is one better than the 3/5 I pre-registered. I predicted t1 and t2
#       would both fail. t2 passed for the reason above. I record the miss.
#
# WHAT I LEARNED FROM THE FRAME THAT I HAD NOT SEEN
#
#   (4) Row 29, cols 13-14, holds colour 3 -- and row 29 is BOARD. The true
#       dynamic box is rows 30-53 x cols 11-63 (the reported [29,10,54,63] is
#       that box padded by one and clipped), so (29,13) and (29,14) have never
#       varied. Colour 3 at cols 13-14 is the signature of a COLLAPSED SLOT.
#       There is therefore at least one more slot above row 29, at rows 24-29,
#       which has never been selected and is consequently indistinguishable
#       from furniture. Rows 42 and below are uniform background, so slot B at
#       rows 36-41 is the LAST slot. The panel is a column of slots running
#       upward from row 41, key(1) moves the selection up one slot and key(2)
#       moves it down one slot. That reading, not the two-slot toggle I wrote
#       last round, is what the board itself says.
#
#   (5) The badge -- the 4x4 colour-14 block at rows 31-34 x cols 42-45 -- is
#       vertically centred on row 32.5, which is exactly the centre of SLOT A
#       (rows 30-35) and exactly the rows of STRIP A. Slot B's lane (rows
#       36-41) has no badge: cols 17-46 are uniform colour 4 there. So the
#       arena is lanes, one per slot, strip at the left end and badge at the
#       right end, and slot A has a task where slot B has none.
#
#   (6) In S1 the world drew strip A as 2 1 1 2 1 1 on row 32 -- the same six
#       colours strip B shows on row 38 in S0. Six of twelve cells agree. The
#       strip may be one display that follows the selection rather than two
#       stored patterns.
#
# WHAT I REFUSE TO DO, AND THIS TIME WITH A PROOF
#
#   The swap stays out of `rules:`. Last round I said it was inexpressible and
#   waved at "96 simultaneous recolourings". That was an assertion. This round
#   I checked it and it is a theorem with named witnesses: three pairs of cells
#   that are IDENTICAL in colour and in all four neighbour colours in frame 0
#   and that must take DIFFERENT colours under key(1). No guard in the
#   documented language separates them, and constraint 5 forbids writing two
#   rules that both fire. See the_swap_is_provably_inexpressible_here. The
#   refusal is now earned rather than pleaded.

semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Casing { pos: Coord, color: Int }  # arc-colour: 6  arc-instances: all
  object Cavity { pos: Coord, color: Int }  # arc-colour: 0  arc-instances: all
  object Rail { pos: Coord, color: Int }  # arc-colour: 3  arc-instances: all
  object Pip { pos: Coord, color: Int }  # arc-colour: 1  arc-instances: all
  object Stud { pos: Coord, color: Int }  # arc-colour: 2  arc-instances: all
  object Erased { pos: Coord, color: Int }  # arc-colour: 4  arc-instances: all
  landmark slot_a_head  # arc-cell: (30, 11)
  landmark slot_b_head  # arc-cell: (36, 11)
  landmark slot_c_head  # arc-cell: (24, 11)
  landmark strip_a_head  # arc-cell: (32, 17)
  landmark strip_b_head  # arc-cell: (38, 17)
  landmark strip_c_head  # arc-cell: (26, 17)
  landmark rail_witness  # arc-cell: (29, 13)
  landmark meter_tip  # arc-cell: (53, 63)
  landmark meter_next  # arc-cell: (53, 62)
  landmark badge_cell  # arc-cell: (31, 42)
  Casing [segment: colour_class_6 ev: t0-t5 compress: 22]
  Cavity [segment: colour_class_0 ev: t0-t5 compress: 12]
  Rail [segment: colour_class_3 ev: t0-t5 compress: 8]
  Pip [segment: colour_class_1 ev: t0-t5 compress: 9]
  Stud [segment: colour_class_2 ev: t0-t5 compress: 10]
  Erased [segment: colour_class_4 ev: t0-t5 compress: 12]

events:
  event recolored(o, c)

# The seven rules below are UNCHANGED from the draft that replayed t3, t4 and
# t5 exactly. Nothing observed this round bears on them, so nothing is touched.
# Their negative neighbour guards are ugly and I defend them, at cost, in
# colour_classes_are_not_the_worlds_objects_and_i_admit_the_cost.

rules:
  rule key3_blanks_the_strip_pips forall ?p in Pip [ev: t3 cov: 8/8]
    when act=key(3) and colored(?p, 1) and not colored(leftof(?p), 0) and not colored(leftof(?p), 5) and not colored(rightof(?p), 5) and not colored(above(?p), 5) then recolored(?p, 4)

  rule key3_blanks_the_strip_studs forall ?p in Stud [ev: t3 cov: 4/4]
    when act=key(3) and colored(?p, 2) and not colored(leftof(?p), 0) and not colored(leftof(?p), 5) and not colored(rightof(?p), 5) and not colored(above(?p), 5) then recolored(?p, 4)

  rule key7_blanks_the_strip_pips forall ?p in Pip [ev: t5 cov: 8/8]
    when act=key(7) and colored(?p, 1) and not colored(leftof(?p), 0) and not colored(leftof(?p), 5) and not colored(rightof(?p), 5) and not colored(above(?p), 5) then recolored(?p, 4)

  rule key7_blanks_the_strip_studs forall ?p in Stud [ev: t5 cov: 4/4]
    when act=key(7) and colored(?p, 2) and not colored(leftof(?p), 0) and not colored(leftof(?p), 5) and not colored(rightof(?p), 5) and not colored(above(?p), 5) then recolored(?p, 4)

  rule key4_restores_the_strip_pips forall ?p in Pip [ev: t4 cov: 8/8]
    when act=key(4) and colored(?p, 4) then recolored(?p, 1)

  rule key4_restores_the_strip_studs forall ?p in Stud [ev: t4 cov: 4/4]
    when act=key(4) and colored(?p, 4) then recolored(?p, 2)

  rule key4_advances_the_meter forall ?p in Stud [ev: t4 cov: 1/1]
    when act=key(4) and colored(?p, 2) and colored(above(?p), 5) and colored(below(?p), 4) then recolored(?p, 3)

laws:
  invariant casing_population count(Casing) = 22 [status: derived]
  invariant cavity_population count(Cavity) = 12 [status: derived]
  invariant rail_population count(Rail) = 8 [status: derived]
  invariant pip_population count(Pip) = 9 [status: derived]
  invariant stud_population count(Stud) = 10 [status: derived]
  invariant erased_population count(Erased) = 12 [status: derived]
  invariant every_dynamic_cell_has_an_owner count(Casing) + count(Cavity) + count(Rail) + count(Pip) + count(Stud) + count(Erased) = 73 [status: proven]

  theorem frame_zero_is_reconstructed_exactly "frame 0 equals the frame I was shown with two edits: rows 38-39 x cols 17-22 hold 2 1 1 2 1 1 over 1 1 2 1 1 2 instead of colour 4, and (53,63) holds 2 instead of 3. Last round this was a deduction from distinct_states = 5 plus two arithmetic closures, 97 dynamic cells and 73 owned cells, neither of which I had used to build it. This round the harness confirmed it independently: replay reports 4/5 with its first divergence at t=0, which is only consistent with open-loop replay, which in turn means the world returned to my frame 0 after key(2) and then matched me for three more transitions. Load-bearing, and now measured rather than inferred."
    [probe: passed]

  theorem replay_is_open_loop_and_that_is_what_four_of_five_means "the manual is run forward from frame 0 without resync. My manual is a no-op on key(1) and key(2), so it sat at frame 0 through both; the world left and came back; from t=2 onward the strip rules carried it. The single failing transition is t=0, the key(1) selector move, 96 cells wrong. This has a consequence I must design around: a wrong rule for key(1) would not merely fail at t=0, it would DESELECT the manual from the world for the rest of the trace and lose the three transitions I currently get for free. Silence on the selector is worth more than a guess at it, and that is a numerical argument, not a temperamental one."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem the_panel_is_a_column_of_slots_and_it_continues_above_row_29 "cells (29,13) and (29,14) hold colour 3 and have never varied, so they are board. Colour 3 at cols 13-14 is exactly the signature of a collapsed slot -- it is what slot A shows at its four outer rows. So there is a further slot at rows 24-29 that has never been selected, and probably more above it, all of them invisible to me because an unselected slot is a constant drawing and a constant drawing is board by definition. Below, rows 42 onward are uniform background, so slot B at rows 36-41 is the last slot. key(1) took the selection from B up to A and key(2) took it back down. I therefore read key(1) as move-selection-up-one-slot and key(2) as move-selection-down-one-slot, in preference to the two-slot toggle I wrote last round. The two readings differ on a probe that costs nothing: from the current state, with the bottom slot selected, a move reading predicts key(2) does nothing at all and a toggle reading predicts 96 cells change. My manual, being silent, already commits to the move reading, so the next key(2) press scores it."
    [depends: frame_zero_is_reconstructed_exactly  probe: pending]

  theorem the_arena_is_lanes_and_only_slot_a_has_a_badge "the arena is colour 4 over cols 17-46, rows 29-41 at least and probably further up where I cannot see. The 4x4 colour-14 badge at rows 31-34 x cols 42-45 is centred on row 32.5, which is the centre of slot A and the exact rows of strip A. Slot B's band, rows 36-41, is uniform colour 4 from col 17 to col 46 -- no badge. So the arena reads as one lane per slot, a 2x6 strip at the lane's left end and a badge at its right end, and slot A carries a task that slot B does not. Slots above row 29 may carry badges too and I would not know, because their badges would never have varied. This is the only structure in the arena that is neither strip nor fill and it remains the natural candidate for what the strips are compared against. Zero transitions bear on it."
    [depends: the_panel_is_a_column_of_slots_and_it_continues_above_row_29  probe: pending]

  theorem the_strip_may_be_one_display_rather_than_two "in S1 the world drew strip A row 32 as 2 1 1 2 1 1, which is exactly what strip B row 38 shows in S0. Six of the twelve cells agree; the divergence report was truncated at 24 cells and row 33 was never shown to me. Either the strip is a single display that follows the selection, or each slot has its own pattern and the two agree on their first row. The separator is free and comes with the selector probe: select slot A and read row 33. If it is 1 1 2 1 1 2 the two are the same display or the same pattern; if it differs, patterns are per-slot and the strip is slot data."
    [depends: the_panel_is_a_column_of_slots_and_it_continues_above_row_29  probe: pending]

  theorem the_swap_is_provably_inexpressible_here "the selector move relabels 96 cells and I cannot write it, and this is now a proof rather than a complaint. A guard sees a cell's own colour and the colours of its four neighbours, and nothing else -- there is no coordinate, no row band, no distance. Under key(1) the new colour of a panel cell is a function of its offset within a six-row period, and that offset is not determined by the four neighbour colours. Three witness pairs, each identical in colour and in all four neighbour colours in frame 0, each required to take different colours: (30,12) and (31,12) are colour 5 with above 5, below 5, left 5, right 3, and must become 6 and 0; (41,12) and (41,13) are colour 6 with above 0, below 5, left 6, right 6, and must become 5 and 3; (32,18) and (32,20) are colour 4 with all four neighbours colour 4, and must become 1 and 2. Stronger still, the five cells (30,16), (31,16), (32,16), (33,16), (34,16) are all colour 5 with above 5, below 5, left 5, right 4 and must become 6, 6, 1, 2, 6 -- four distinct answers to one indistinguishable question. Constraint 5 forbids two rules firing on one object in one transition, so there is no escape by writing both. The swap does not go in the manual."
    [depends: the_panel_is_a_column_of_slots_and_it_continues_above_row_29  probe: passed]

  theorem nesting_would_break_the_ties_and_would_still_fail_the_gain_test "the proof above assumes cell expressions take an instance or a landmark, as the grammar documents. If above(above(?p)) in fact compiles, the ties break: a chain of five nested neighbours can count a cell's distance from the panel edge and so recover its offset in the period. I decline that route for two reasons and I want both on the record. First, a guard form the grammar does not list is a parse risk, and a manual that fails to parse loses everything including the three transitions it currently gets right. Second, and decisively, distinguishing 96 cells by 96 distinct neighbour chains is writing the pixels out with extra syntax: it would cost more symbols than the 96 pixels it explains, which is exactly the failure constraint 3 names. The swap is inexpressible without nesting and uncompressible with it, so it stays out either way."
    [depends: the_swap_is_provably_inexpressible_here  probe: pending]

  theorem the_meter_can_tick_only_once_in_this_manual_and_the_second_tick_is_pre_registered "row 53 is a colour-2 bar running at least cols 10 to 62 with its rightmost cell at col 63, and (53,63) is the only cell of it that has ever varied. My rule key4_advances_the_meter recolours that one Stud instance from 2 to 3 and then guards itself off, because it now holds colour 3. There is no instance at (53,62): that cell is constant in frame 0 and therefore board. So this manual predicts the meter never advances again, which is almost certainly wrong. I pre-register the shape of the failure exactly: the second key(4) press diverges at ONE cell, (53,62), 2 -> 3, and nowhere else. That divergence would confirm the bar reading rather than refute the manual, and the repair is one line -- the arm will hand (53,62) an instance once it has varied, and stud_population goes from 10 to 11. A divergence anywhere other than (53,62) refutes the bar reading and I would rebuild the meter from what is reported."
    [depends: frame_zero_is_reconstructed_exactly  probe: pending]

  theorem the_strip_toggles_and_only_key_four_costs_anything "key(3) at t3 and key(7) at t5 each blanked all 12 cells of the selected slot's strip to arena colour 4; key(4) at t4 restored exactly the same 1 and 2 pattern cell for cell and additionally advanced the meter. The pattern is therefore stored somewhere the frame does not show and blanking does not destroy it. Over five commands the meter ticked once and only under key(4), so key(4) is the metered action and keys 1, 2, 3 and 7 are free. One witness each: key(3) and key(7) may be a blank and a toggle that agreed because the strip was shown both times, and key(4) may be a show or a toggle that agreed because the strip was blank. Nothing in the record separates blank from toggle for any of the three, and the cheapest separator is a second consecutive key(3) from a shown strip."
    [depends: frame_zero_is_reconstructed_exactly  probe: pending]

  theorem the_sign_of_the_meter_is_unknown_and_that_matters_more_than_its_length "I have been calling (53,63) a meter and treating its tick as a cost, and I have no evidence for the sign. Colour 2 is the bar and colour 3 is what one unit became; colour 3 is also the colour of an unselected slot's rails, and colour 2 is also the colour of half the strip. A bar consumed right to left and a score accumulated right to left look identical after one tick. If it is a cost, key(4) should be rationed; if it is a score, key(4) is the only action that has ever accomplished anything and should be repeated. This is the single largest open question about what to do next, it is worth more than any refinement of the drawing, and one further key(4) press resolves the direction while leaving at least fifty-two units of whatever it is."
    [depends: the_meter_can_tick_only_once_in_this_manual_and_the_second_tick_is_pre_registered  probe: pending]

  theorem cascade_length_carries_no_signal_here "t1, t2, t3 and t4 returned 2 frames each and t5 returned 1, yet t3 and t5 produced identical 12-cell effects. Frame count does not track the magnitude or even the presence of change and must not be used as a motion detector. What it may still carry is that ACTION7 and ACTION3 are genuinely different actions that happened to agree in this state -- one animates and one does not. That is a hint about key identity, not about world state."
    [probe: pending]

  theorem colour_classes_are_not_the_worlds_objects_and_i_admit_the_cost "the six declared types are colour classes, not things. Stud alone spans slot A's core, a port cell of the expanded slot, four strip cells and the meter tip -- four unrelated roles. Casing and Cavity together are one widget. The world segments by widget and the arm segments by colour, and the arm wins because the arm is what draws the frame. The gain is real and now measured: six declarations own all 73 cells that need an owner, against 73 pixels written out, responsibility reports 0 unexplained, and seven rules over those classes reproduce three of the five transitions exactly. The cost is real too: no rule can name the strip as such, so every strip rule carves it out of its class with four negative neighbour guards. Those guards are pixel-fitting in a costume. They are correct on every instance of both classes in frame 0, which I checked one by one, and they survived replay, and they are the price of a colour-first arm."
    [depends: the_swap_is_provably_inexpressible_here  probe: passed]

  theorem instance_anchoring_is_frame_zero_and_that_question_is_closed "I pre-registered two branches: instances anchored from frame 0, predicting 0 unexplained, or anchored from the union of frames, predicting a residue drawn from exactly 13 named cells. The report reads 0 unexplained over 4096 cells. Frame 0 it is. The consequence I now rely on: a cell that is constant in frame 0 gets no instance and can never be drawn as anything else, which is precisely why the meter cannot tick twice and why the slots above row 29 are invisible to this manual. Both of those are stated as their own entries rather than left implicit."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem two_keys_have_never_been_pressed "this world has seen ACTION1, 2, 3, 4 and 7. key(5) and key(6) are unpressed and unknown. In this family a click carrying coordinates is common and this guard language cannot express one at all -- if key(5) or key(6) is that, the finding will be recorded as prose and never as a rule. Both are worth pressing early: whatever they cost, they cost less now, while the manual is small enough that a surprise is cheap to absorb, than later when a plan depends on them."
    [depends: the_sign_of_the_meter_is_unknown_and_that_matters_more_than_its_length  probe: pending]

  theorem no_goal_section_on_purpose "every command returned NOT_FINISHED and nothing in five transitions indicates what finishing means. The live candidates are that a strip must be brought to agree with the badge in its lane, that the meter must be filled, or that the objective lies above row 29 where I have never looked. Writing any of them as a goal would compile to a claim refuted by the first win, or worse, would send the searcher after a fiction. An absent goal compiles to is_goal -> False, which under-claims and costs a round; a wrong goal over-claims and costs the level."
    [depends: the_arena_is_lanes_and_only_slot_a_has_a_badge  probe: pending]

  theorem what_the_engines_offered_and_why_none_of_it_was_taken "mdl_segmenter returned negative gain on both variants, -4037 bits at 4 tracks and -10409 at 33, with tracks that are 440-cell blobs of shape 13x36 and colour null -- the panel and the arena fused by connected_components(4). That is a fact about the operator. cegis_miner refused every track because its precondition is one move event per transition and this world has no mover; correct and unhelpful. zero_space calls its own evidence THIN, 5 transitions constraining rank 3 of 679 features, and its single global law spans nearly every dynamic cell at once, which is what a 676-dimensional null space produces rather than what a conservation law looks like. I took one thing from the engines and it was the store arithmetic, dynamic_cells 97 and cells_needing_an_owner 73, both of which closed against a reconstruction built without them and both of which the responsibility check has since ratified."
    [probe: pending]
```

=== PLAYBOOK ===
```
# playbook.dsl -- the manual is silent on the selector by proof, not by
# laziness, so every routable thing about the selector lives here. What changed
# this round:
#
#   the panel is a COLUMN of slots, not a pair -- (29,13) and (29,14) are
#     board-constant colour 3, the signature of a collapsed slot above row 29,
#     and rows 42 down are empty, so slot B is the bottom one;
#   key(1) is up-one-slot and key(2) is down-one-slot, and the manual's silence
#     already commits to that reading: from the bottom slot, key(2) is
#     predicted to do nothing, so the cheapest probe in the game also scores
#     the leading hypothesis;
#   slot A's lane carries a badge and slot B's lane carries none, so the slots
#     are not interchangeable and the one with the task is worth being in;
#   the meter's SIGN is unknown -- cost or score -- and that outranks every
#     refinement of the drawing, because it decides whether key(4) is the thing
#     to avoid or the only thing that has ever worked;
#   ACTION5 and ACTION6 have never been pressed at all.
#
# Nothing below is a stored line of play. Every entry is a ranking rule that
# still has to be evaluated against whatever state the searcher is actually in.

order   probe_the_selector_bound_before_theorising_about_the_selector    [proof: lean]
order   settle_the_sign_of_the_meter_before_rationing_the_metered_key    [proof: lean]
order   reach_a_slot_that_has_never_been_selected                        [proof: lean]
order   read_the_second_strip_row_while_the_upper_slot_is_selected       [proof: lean]
order   press_the_two_never_pressed_keys_while_the_meter_is_still_long   [proof: lean]
order   separate_blank_from_toggle_before_trusting_either_reading        [proof: lean]
order   compare_a_strip_against_the_badge_in_its_own_lane                [proof: lean]
order   read_the_meter_tip_and_the_frame_count_after_every_command       [proof: lean]

prefer  a_state_whose_lane_contains_the_badge_over_a_lane_without_one    [ev: 1/2 lanes carry a badge]
prefer  a_slot_that_has_never_been_selected_over_one_already_mapped      [ev: 2 slots seen of a column]
prefer  a_key_never_pressed_over_a_key_whose_effect_is_already_known     [ev: 2/7 keys unpressed]
prefer  an_action_whose_outcome_the_manual_already_predicts              [ev: 1/1 open_loop replay reads]
prefer  a_press_that_makes_a_board_cell_dynamic_over_one_that_repeats    [ev: 97/4096 cells ever varied]
prefer  repeating_a_key_from_the_state_it_already_produced               [ev: 2/2 blanking presses agreed]

heuristic slots_in_the_column_never_yet_selected                        [admissible: lean]
heuristic strip_rows_still_unread_in_the_panel                          [admissible: lean]
heuristic keys_whose_effect_rests_on_a_single_witness                   [admissible: lean]
heuristic lanes_whose_badge_has_never_been_addressed                    [admissible: lean]

prune   meter_exhausted and not goal => dead                            [proof: lean]
prune   repeat_of_a_key_that_left_this_exact_state_unchanged => dead     [proof: lean]
prune   metered_press_before_the_selector_bound_is_known => dead         [proof: lean]
prune   undoing_a_selector_move_that_just_revealed_something => dead     [proof: lean]
prune   selector_move_away_from_the_badge_lane_with_nothing_learned => dead [proof: lean]
```

=== LOG ===
```json
[
  {"id": "O-01", "subject": "six colour-class objects (6,0,3,1,2,4) with arc-instances: all", "verdict": "accept",
   "as": "Casing, Cavity, Rail, Pip, Stud, Erased",
   "why": "certify's responsibility check reports 0 unexplained cells of 4096, and the six declared populations 22+12+8+9+10+12 sum to exactly the 73 cells the store says need an owner, so the inventory is closed and unchanged."},

  {"id": "O-02", "subject": "mdl_segmenter obj0/obj2/obj3 (440-cell, 436-cell, shape 13x36, colour null)", "verdict": "reject",
   "why": "connected_components(4) fuses the whole panel with the whole arena because both touch through the colour-4 fill; both variants report negative gain (-4037 and -10409 bits), so the engine itself scores its segmentation as worse than writing the pixels."},

  {"id": "O-03", "subject": "a colour-5 object to own the 24 background cells of slot A", "verdict": "reject",
   "why": "it is the only way to draw slot A expanded, but the target colours of those 24 cells are not determined by their neighbour colours (witnesses (30,12) vs (31,12)), so the instances would exist and no rule could correctly recolour them; declaring an object at the declared background colour also risks the 0-unexplained result the manual currently holds."},

  {"id": "R-01", "subject": "the seven strip and meter rules from the previous draft", "verdict": "accept",
   "why": "replay reproduced t3, t4 and t5 exactly with them, and nothing observed this round bears on any of their guards, so they are carried over unmodified."},

  {"id": "R-02", "subject": "a rule set for the key(1)/key(2) selector move", "verdict": "reject",
   "why": "three witness pairs are identical in colour and in all four neighbour colours in frame 0 yet must take different colours -- (30,12)/(31,12) as 6/0, (41,12)/(41,13) as 5/3, (32,18)/(32,20) as 1/2 -- and constraint 5 forbids two rules firing on one object, so no guard set in the documented language expresses it."},

  {"id": "R-03", "subject": "cegis_miner's mined movers", "verdict": "reject",
   "why": "the engine refused all four tracks on its own precondition of exactly one move event per transition; its verdict that this world does not narrate as one mover is right, and it offered nothing to accept."},

  {"id": "L-01", "subject": "S2 = S0, i.e. key(2) exactly undid key(1)", "verdict": "accept",
   "why": "replay reports 4/5 matched with first divergence at t=0, which is only consistent with open-loop replay of a manual that is a no-op on both keys, so the world must have returned to frame 0 at t=1 -- an independent confirmation of last round's deduction."},

  {"id": "L-02", "subject": "instances are anchored from frame 0, not from the union of frames", "verdict": "accept",
   "why": "the pre-registered alternative predicted a residue drawn from 13 named cells and the report reads 0 unexplained, so the frame-0 branch is the one that holds and the question is closed."},

  {"id": "L-03", "subject": "the panel is a column of slots continuing above row 29", "verdict": "accept",
   "why": "(29,13) and (29,14) hold colour 3 and are board (the true dynamic box is rows 30-53, the reported [29,10,54,63] being that box padded by one), and colour 3 at cols 13-14 is exactly what an unselected slot draws."},

  {"id": "L-04", "subject": "key(1) moves the selection up one slot, key(2) down one slot", "verdict": "probe-pending",
   "why": "it fits both observed transitions and explains why a collapsed slot sits above row 29 and nothing sits below row 41, but a two-slot toggle fits the same two transitions; key(2) from the current bottom-selected state separates them at zero meter cost."},

  {"id": "L-05", "subject": "the arena is lanes, one per slot, and only slot A's lane carries a badge", "verdict": "accept",
   "why": "the 4x4 colour-14 block at rows 31-34 is centred on row 32.5, exactly the centre of slot A and exactly the rows of strip A, while cols 17-46 of rows 36-41 are uniform colour 4."},

  {"id": "L-06", "subject": "the strip is one display that follows the selection", "verdict": "probe-pending",
   "why": "strip A row 32 in S1 reads 2 1 1 2 1 1, identical to strip B row 38 in S0, but the divergence report was truncated before row 33, so six of twelve cells agree and six are unobserved."},

  {"id": "L-07", "subject": "the meter tick at (53,63) is a cost", "verdict": "probe-pending",
   "why": "one tick under key(4) is equally consistent with a bar being consumed and a score being accumulated, and colour 3 appears elsewhere as ordinary slot furniture, so the sign is unsupported either way."},

  {"id": "P-01", "subject": "second key(4) press diverges at exactly (53,62)", "verdict": "probe-pending",
   "why": "the manual's meter rule guards itself off once the tip holds colour 3 and (53,62) is board with no instance, so a one-cell divergence there would confirm the bar reading while any other divergence refutes it -- pre-registered before the press."},

  {"id": "P-02", "subject": "key(2) from the bottom-selected state changes nothing", "verdict": "probe-pending",
   "why": "the manual is silent on key(2) and so already predicts no change; under the move reading that prediction is correct and under the toggle reading it is 96 cells wrong, making this the cheapest scoring probe available."},

  {"id": "P-03", "subject": "two successive key(1) presses reach the never-selected slot at rows 24-29", "verdict": "probe-pending",
   "why": "it would turn board cells into dynamic ones for the first time in the record, which is the only way to see whether the column really extends and whether upper lanes carry badges of their own."},

  {"id": "E-01", "subject": "the 96-cell selector move", "verdict": "reject",
   "why": "I wanted an event that translates a 6x6 widget six rows, or a recolour whose target reads another cell's colour; the vocabulary offers one-cell moves, jumps to a named landmark, and recolours to an integer literal, so I wrote it as theorem the_swap_is_provably_inexpressible_here with three named witness pairs instead of rules."},

  {"id": "E-02", "subject": "nested cell expressions such as above(above(?p))", "verdict": "reject",
   "why": "they would break the witness ties by counting distance from the panel edge, but the grammar does not list them and a parse failure would cost the three transitions the manual currently replays; even if they compiled, one guard chain per cell over 96 cells is writing the pixels out and fails the gain test, which I recorded as theorem nesting_would_break_the_ties_and_would_still_fail_the_gain_test."},

  {"id": "E-03", "subject": "the prediction I got wrong last round", "verdict": "accept",
   "why": "I pre-registered 3/5 replay on the grounds that both key(1) and key(2) would fail; the result was 4/5 because replay is open-loop and the world came back to frame 0, and I record the miss rather than reread it as a success."}
]
```
```
