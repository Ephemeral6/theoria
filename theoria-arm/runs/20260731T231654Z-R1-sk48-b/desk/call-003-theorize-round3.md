# call-003-theorize-round3

model: `claude-opus-5` · 703330 ms · $1.830049 · usage {"cache_creation": {"ephemeral_1h_input_tokens": 40090, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 40090, "cache_read_input_tokens": 0, "inference_geo": "not_available", "input_tokens": 2, "iterations": [{"cache_creation": {"ephemeral_1h_input_tokens": 40090, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 40090, "cache_read_input_tokens": 0, "input_tokens": 2, "output_tokens": 55975, "type": "message"}], "output_tokens": 55975, "server_tool_use": {"web_fetch_requests": 0, "web_search_requests": 0}, "service_tier": "standard", "speed": "standard"}

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

## The compiler refused your last manual

This is not a style complaint. The manual did not compile, so it has no executable form and nothing downstream can run. Fix the named clause; do not work around it by deleting the content unless the content really is inexpressible, in which case say so with an `E-` entry in the log.

```json
{
 "reply": "the reply carried no === THEORY === block; emit all three blocks"
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
# theory.dsl -- rebuilt from scratch this round.
#
# WHY IT IS A REBUILD AND NOT AN EDIT.
#
#   The manual I was handed narrates 34 states, a 64-cell colour-9 meter on
#   row 63, a two-slot panel at rows 1-5, and a 5x5 colour-9 body walking a
#   six-pixel lattice at rows 8-18. The evidence brief in front of me reports
#   SIX states, FIVE transitions, background 5, dynamic cells confined to
#   rows 30-41 x cols 11-22 plus the single cell (53,63), and colours 0-6
#   with 8, 9 and 14 appearing only on cells that have never changed. Not one
#   dynamic cell here has frame-0 colour 9, so every Glyph9 rule in the
#   inherited manual is unreachable text -- and worse, its Spent (colour 1)
#   and Dark (colour 0) types WOULD instantiate on my 9 colour-1 and 12
#   colour-0 cells and fire panel recolours that no frame here witnesses.
#   Carrying it forward would poison replay with rules that have zero
#   evidence in this evidence stream. I discard it wholesale. If those frames
#   return, its text is in the history; nothing is lost but a paste.
#
#   The compiler complaint that brought me here is separate and simpler: the
#   last reply carried no === THEORY === block at all, so nothing compiled and
#   nothing replayed. That is fixed by emitting the block.
#
# WHAT THIS MANUAL CLAIMS AND WHAT IT PAYS.
#
#   Cell-level diffs exist for exactly three transitions (t3 key3, t4 key4,
#   t5 key7) and they are fully explained by seven rules. t1 (key1) and t2
#   (key2) each rewrote all 96 dynamic cells of the arena and I was given
#   only their count and bounding box, never their pixels. I write NO rule
#   for key1 or key2. My manual therefore predicts identity for them and is
#   wrong by 96 pixels on t1 and 96 on t2. Expect replay 3/5. That number is
#   posted in advance so it cannot be mistaken for a surprise, and the probe
#   that fixes it is named in what_i_predict_before_i_see_it.

semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Ink0   { pos: Coord, color: Int }   # arc-colour: 0  arc-instances: all
  object Tok1   { pos: Coord, color: Int }   # arc-colour: 1  arc-instances: all
  object Tok2   { pos: Coord, color: Int }   # arc-colour: 2  arc-instances: all
  object Rail3  { pos: Coord, color: Int }   # arc-colour: 3  arc-instances: all
  object Panel4 { pos: Coord, color: Int }   # arc-colour: 4  arc-instances: all
  object Floor5 { pos: Coord, color: Int }   # arc-colour: 5  arc-instances: all
  object Case6  { pos: Coord, color: Int }   # arc-colour: 6  arc-instances: all
  Tok1   [segment: dynamic_colour_1 ev: t3,t4,t5 compress: 9]
  Tok2   [segment: dynamic_colour_2 ev: t3,t4,t5 compress: 10]
  Ink0   [segment: dynamic_colour_0 ev: t1,t2 compress: 12]
  Rail3  [segment: dynamic_colour_3 ev: t1,t2 compress: 8]
  Panel4 [segment: dynamic_colour_4 ev: t1,t2 compress: 12]
  Floor5 [segment: dynamic_colour_5 ev: t1,t2 compress: 24]
  Case6  [segment: dynamic_colour_6 ev: t1,t2 compress: 22]

rules:
  rule key3_clears_strip_tok1 forall ?p in Tok1 [ev: t3 cov: 8/8]
    when act=key(3) and colored(?p, 1) and colored(above(above(?p)), 4) then recolored(?p, 4)

  rule key3_clears_strip_tok2 forall ?p in Tok2 [ev: t3 cov: 4/4]
    when act=key(3) and colored(?p, 2) and colored(above(above(?p)), 4) then recolored(?p, 4)

  rule key7_clears_strip_tok1 forall ?p in Tok1 [ev: t5 cov: 8/8]
    when act=key(7) and colored(?p, 1) and colored(above(above(?p)), 4) then recolored(?p, 4)

  rule key7_clears_strip_tok2 forall ?p in Tok2 [ev: t5 cov: 4/4]
    when act=key(7) and colored(?p, 2) and colored(above(above(?p)), 4) then recolored(?p, 4)

  rule key4_redraws_strip_tok1 forall ?p in Tok1 [ev: t4 cov: 8/8]
    when act=key(4) and colored(?p, 4) and colored(above(above(?p)), 4) then recolored(?p, 1)

  rule key4_redraws_strip_tok2 forall ?p in Tok2 [ev: t4 cov: 4/4]
    when act=key(4) and colored(?p, 4) and colored(above(above(?p)), 4) then recolored(?p, 2)

  rule key4_burns_bar_end forall ?p in Tok2 [ev: t4 cov: 1/1]
    when act=key(4) and colored(?p, 2) and rightof(?p) = wall then recolored(?p, 3)

laws:
  invariant board_cells count(board) = 3999 [status: counted from the store]
  invariant tok1_instances count(Tok1) = 9 [status: inferred from the frame-0 census]
  invariant tok2_instances count(Tok2) = 10 [status: inferred from the frame-0 census]
  invariant ink0_instances count(Ink0) = 12 [status: inferred from the frame-0 census]
  invariant rail3_instances count(Rail3) = 8 [status: inferred from the frame-0 census]
  invariant floor5_instances count(Floor5) = 24 [status: inferred, and it equals the 24 the store withholds from cells_needing_an_owner]
  invariant case6_instances count(Case6) = 22 [status: inferred from the frame-0 census]
  invariant panel4_instances count(Panel4) = 12 [status: derived by subtraction, the weakest number in this manual]
  invariant bar_burned_cells count(Tok2, color = 3) = 1 [status: counted in the current frame, a tally and not a conservation law]

  theorem the_inherited_manual_describes_a_world_these_frames_do_not_show "I was handed a manual for 34 states, a colour-9 body on a six-pixel lattice, a two-slot panel at rows 1-5 and a 64-cell colour-9 meter on row 63. The brief in front of me reports 6 states, 5 transitions, dynamic cells only in rows 30-41 x cols 11-22 plus (53,63), and colour 9 present only on cells that have never changed. Those two descriptions cannot both be of the frames I was given, and the brief is what the responsibility check will redraw my manual onto, so the brief wins. Discarding was not a preference: the inherited Spent (arc-colour 1) and Dark (arc-colour 0) types would seat instances on my nine colour-1 and twelve colour-0 cells and fire thirteen panel recolours that no transition here witnesses, which is a direct violation of no-entry-without-evidence and would have made replay worse than an empty manual. The one thing I carry across is a method, not a fact: price the pixels you cannot draw BEFORE the world charges you for them."
    [depends: the_census_of_ninety_seven_cells  probe: passed]

  theorem the_census_of_ninety_seven_cells "Every dynamic cell is owned and the arithmetic closes three separate ways. The store says shape 64x64, constant 3999, dynamic 97, cells_needing_an_owner 73. The five diffs place 96 of those 97 inside rows 30-41 x cols 11-22 and the last at (53,63). Frame-0 colour of every cell is recoverable because t3, t4 and t5 touched only the strip and the bar, and t2 undid t1 exactly (distinct_states is 5 for 6 states, so exactly one pair coincides and s2 = s0): so frame 0 is the current frame with the strip redrawn as 2-1-1-2-1-1 over 1-1-2-1-1-2 and (53,63) back to 2. Counting the current frame cell by cell gives 12 colour-0, 9 colour-1, 10 colour-2, 8 colour-3, 24 colour-5, 22 colour-6, which is 85, leaving 12 colour-4 by subtraction, and 85 + 12 = 97 exactly. INDEPENDENT CHECK: 97 minus cells_needing_an_owner 73 is 24, which is exactly the count of dynamic cells whose colour is the background 5 -- the cells the board can already explain and which therefore need no owner. That the two numbers agree without being fitted to each other is the strongest evidence in this manual. I declare all seven colours anyway, so that if the checker does demand owners for background-coloured cells it finds twenty-four."
    [probe: passed]

  theorem the_arena_as_i_read_it_off_the_current_frame "Read pixel by pixel, and stated so a later desk can check me. A colour-4 PANEL fills rows 29-41 x cols 17-46, holding a constant 4x4 colour-14 block at rows 31-34 x cols 42-45 and a 2x6 SLOT at rows 38-39 x cols 17-22. West of it a 2-wide RAIL runs down cols 13-14 from row 29 to row 35, colour 3 except rows 32-33 which are colour 2 -- a two-row marker sitting at the middle of a seven-row track. Below the rail a 6x6 colour-6 CASE occupies rows 36-41 x cols 11-16: solid colour-6 border, an interior ring of colour 0 at rows 37-40 x cols 12-15, a 2x2 colour-6 core at rows 38-39 x cols 13-14, and TWO SOCKET PIXELS punched through its east wall at (38,16) colour 1 and (39,16) colour 2. The socket rows are exactly the slot rows and the socket colours are exactly the slot colours, which is why I read the case as the source of what the slot displays -- a reading, not a law. Far below, row 53 cols 10-63 is a 54-cell colour-2 BAR with row 54 beneath it in colour 4; the bar segmenter track obj1 is 2x54 and confirms the bar starts at col 10, not col 0. Colours 8 and 9 exist somewhere outside this window on cells that have never changed; I have never been shown them and say nothing about them."
    [depends: the_census_of_ninety_seven_cells  probe: passed]

  theorem the_slot_is_a_two_state_display_and_three_keys_drive_it "The slot at rows 38-39 x cols 17-22 holds two side-by-side copies of one 2x3 glyph, 2-1-1 over 1-1-2, and it is either FULLY DRAWN or FULLY BLANK -- twelve cells move together, three times, with no intermediate ever observed. Blank is colour 4, the panel colour, not the background 5, which is why I model the transition as recolour and not as vanished(): present=False would render the wrong colour and cost twelve pixels every time. ACTION3 blanked it (t3), ACTION7 blanked it (t5), ACTION4 redrew it (t4), each time the whole twelve. Redraw restores the exact original pattern, so the pattern is held somewhere the frame does not show or is a fixed template; I cannot tell which and do not need to, because two rules per key reproduce it from the cells themselves. THE GUARD THAT DOES THE WORK is colored(above(above(?p)), 4): among all Tok1 and Tok2 instances it is true of the twelve slot cells and false of the case sockets (their two-above is colour 6), of the rail marker (colour 3 above), and of the bar end (colour 5 above). One atom separates four groups, which is what earns it under the gain test."
    [depends: key3_clears_strip_tok1, key4_redraws_strip_tok2  probe: passed]

  theorem what_key1_and_key2_do_is_this_manual_s_largest_hole_and_i_price_it_at_ninety_six_pixels "ACTION1 changed 96 cells and ACTION2 changed 96 cells, bounding box rows 30-41 x cols 11-22, colour sets [0..6] before and after both times. 96 is EVERY dynamic cell of the arena except the bar end -- the rail, the case, the slot and the twelve dynamic panel cells all moved at once. I was given the count and the box and never the pixels, so I have no witness for a single cell of state s1 and I write no rule. Consequence, stated as a bill and not as an excuse: my compiled step returns identity for key(1) and key(2), so replay diverges by 96 cells on t1 and 96 on t2, and 3/5 is the ceiling of this manual, not a defect I can repair from what I hold. WHAT I DO KNOW ABOUT s1, all of it: s2 = s0 (distinct_states 5 of 6, and t2 restored exactly the cells t1 touched), so ACTION2 undoes ACTION1; and mdl_segmenter, which has never seen my rules, reports the arena blob at 440 non-background cells in frame 0, 436 in frame 1, and 440 again from frame 2 -- so s1 has FOUR FEWER non-background cells than s0, which rules out any reading where the twenty-four background cells at cols 11-12 and 15-16 are simply filled in. THE PROBE IS FREE AND OBVIOUS: the brief always prints the current frame, and prints cell-level diffs only for small changes, so the way to see s1 is to make s1 the state the round ENDS in. One press of ACTION1 not followed by ACTION2 buys ninety-six pixels of manual."
    [depends: the_census_of_ninety_seven_cells, what_the_engines_gave_me  probe: pending]

  theorem the_bar_burn_has_one_witness_and_the_even_index_reading_is_already_dead "(53,63), the east end of the 54-cell colour-2 bar, went 2 to 3 at t4 and at no other transition. THREE READINGS FIT ONE WITNESS. (a) ACTION4 burns: 1 positive, and 4 negatives, since keys 1, 2, 3 and 7 each ran without a burn. (b) The burn is charged for the EFFECT -- t4 is the only transition that redrew the slot rather than blanking it, so the bar may count restorations, or mistakes. (c) The burn is keyed to the command counter. READING (c) IN ITS SIMPLEST FORM IS ALREADY REFUTED: command index 2 was even and did not burn. I encode (a) because it is the only one this guard language can say, and I flag the confound loudly rather than let it rot: (a) and (b) agree on every transition observed so far and are separated by ONE press -- ACTION4 while the slot is already drawn. Under (a) the bar burns again; under (b) nothing happens. Note that my rule cannot show the second burn either way, for the reason in i_cannot_draw_a_burn_on_a_cell_that_has_never_changed, so the separator must be read off the raw diff and not off the refutation flag."
    [depends: key4_burns_bar_end  probe: pending]

  theorem i_cannot_draw_a_burn_on_a_cell_that_has_never_changed "The arm seats instances only on cells the board cannot explain, so a cell that has never varied has no instance and no rule of mine can repaint it. (53,63) is dynamic and owned; (53,62), its western neighbour and the natural next cell of a bar that burns from the east, is still constant and therefore unowned. So if the bar advances, the first pixel of the advance is undrawable BY CONSTRUCTION, exactly one wrong cell, and my manual heals only on the transition after. My burn rule is already unable to fire twice: it demands colour 2 at a cell that now reads 3. The rule that will be needed the moment the second burn makes (53,62) dynamic is written out here so it costs a paste and not a round -- rule burn_next forall ?p in Tok2 when act=key(4) and colored(?p, 2) and colored(rightof(?p), 3) then recolored(?p, 3) -- and it stays OUT of the manual until a transition witnesses it, because a rule with cov 0/0 is exactly what constraint 2 forbids."
    [depends: the_bar_burn_has_one_witness_and_the_even_index_reading_is_already_dead  probe: pending]

  theorem silence_is_a_prediction_and_four_of_my_silences_are_unwitnessed "The compiled step is total: where no rule fires the successor is the current state, so my manual never says I do not know, it says nothing happens, in the same voice it uses for things it has seen. Audit every key against the current state, where the slot is BLANK and the bar end is burned. key(3) and key(7): my clear rules demand colour 1 or 2 in the slot, which is false now, so both are predicted inert -- NO WITNESS, the slot has never been blanked twice running. key(4): the redraw rules fire, twelve cells, WITNESSED at t4; the burn rule cannot fire again. key(1) and key(2): predicted inert and KNOWN FALSE, ninety-six cells each, the hole above. key(5) and key(6): never pressed in this world, predicted inert, NO WITNESS AT ALL, and therefore the cheapest unclaimed information on the board -- two keys of a seven-key alphabet about which this manual asserts total inertness on the strength of nothing."
    [depends: key3_clears_strip_tok1, what_key1_and_key2_do_is_this_manual_s_largest_hole_and_i_price_it_at_ninety_six_pixels  probe: pending]

  theorem key3_and_key7_are_indistinguishable_so_far_and_i_refuse_to_merge_them "Each was pressed once, each from a state with the slot drawn, each blanked exactly the same twelve cells. Four of my seven rules exist only because the guard language keys on the action name: key3_clears and key7_clears are the same body twice. The gain test says merge them, and I cannot -- there is no disjunction in the guard grammar and no domain of actions to quantify over, so two identical bodies is the shortest thing sayable. I record it as a cost I pay to the DSL rather than a claim about the world, and I record the discriminator: press either key from a state the other has never acted on, or press one twice. If they ever diverge, four rules become two plus a difference; if they never do, this manual carries two redundant lines forever and says so."
    [depends: key3_clears_strip_tok1, key7_clears_strip_tok1  probe: pending]

  theorem the_goal_section_is_absent_on_purpose "Nothing in six frames has announced a win: state is NOT_FINISHED throughout, no cell has behaved like a scoreboard except the bar, and the bar moved once. The candidates all fail. count(Tok1) = 0 is never true -- the arm counts instances, not drawn cells. count(Tok1, color = 4) = 8 is true of every blanked-slot state including the current one, which is plainly not a win. The colour-14 block at rows 31-34 x cols 42-45 is the most goal-shaped thing on the board and it is CONSTANT, so it has no instance and count() has nothing to range over there. A goal true in the wrong state is worse than no goal because it halts a planner at its first step. So is_goal compiles to False, no plan terminates, and command choice falls back entirely on what the manual predicts will change -- which today is key(4) and nothing else, and that is a trap I name in the playbook."
    [depends: the_arena_as_i_read_it_off_the_current_frame  probe: passed]

  theorem what_the_engines_gave_me "mdl_segmenter reports NEGATIVE gain on both variants, -4037 bits unsplit and -10409 bits split by colour, so its own accounting says its segmentation does not beat writing the pixels out, and I owe it nothing structural. I take two facts from it anyway, both checkable. FIRST, obj1: 108 cells, shape 2x54, present in all six frames -- that is rows 53-54 x cols 10-63, and it is how I know the bar starts at col 10 rather than col 0. SECOND, obj0/obj2/obj3: one 13x36 blob at rows 29-41 x cols 11-46, 440 cells in frame 0, 436 in frame 1, 440 from frame 2 on. Since it chose connected_components(4) with split_by_color false, that blob is the whole non-background arena -- panel plus rail plus case, 468 box cells minus the 28 that are background or colour-14 -- and its four-cell dip at frame 1 is the only quantitative thing I possess about s1. I reject all four tracks AS OBJECTS: a 440-cell track cannot be one instance, and a second type over the same pixels invites the double claim constraint 5 forbids. cegis_miner refused every track and its verdict, the world does not narrate as one mover, is CORRECT here and not merely an arm limitation -- nothing in six frames translates; every event is a recolour in place. zero_space self-reports THIN in its own words, rank 3 of 679 features over 5 transitions, and its single global law is a list of my 97 dynamic cells, which is my census and not an independent law."
    [depends: the_census_of_ninety_seven_cells  probe: passed]

  theorem what_i_predict_before_i_see_it "Written so the world can charge me. The state is: slot BLANK, rail marker at rows 32-33, case unchanged, one bar cell burned. key(4): I predict exactly twelve cells, the slot redrawn to 2-1-1-2-1-1 over 1-1-2-1-1-2, and NO burn, because my burn rule needs colour 2 at (53,63) and finds 3. If a burn appears at (53,62) I am wrong by one pixel and reading (a) of the bar survives; if a burn appears anywhere else the bar is not a right-to-left counter. key(3) or key(7): I predict ZERO cells, an unwitnessed silence, and any change at all refutes the clear rules as stated. key(1): I predict ZERO cells and I EXPECT TO BE WRONG BY NINETY-SIX -- this is the press I want, because the resulting frame is printed in full and buys me the state s1 that five transitions have hidden, and because being wrong by 96 predicted pixels is the loudest signal available. key(2) from here: unknown, since ACTION2 has only ever been observed immediately after ACTION1; if it is an undo it should be inert here and if it is an independent rewrite it should move 96 cells. key(5) or key(6): I predict ZERO cells on no evidence whatsoever. The one prediction I would most like refuted is that the slot has only two states."
    [depends: silence_is_a_prediction_and_four_of_my_silences_are_unwitnessed, what_key1_and_key2_do_is_this_manual_s_largest_hole_and_i_price_it_at_ninety_six_pixels  probe: pending]

  theorem the_dsl_cannot_say_i_have_not_been_shown_this "Two holes I hit this round. FIRST and worst: there is no way to write unobserved, the manual declines to predict. Rules produce events and the absence of a rule produces identity, so my honest ignorance about ACTION1 is compiled into a confident claim that ACTION1 does nothing. The only lever the grammar offers is to write a guessed rule instead, which trades a known-wrong silence for an invented change and violates constraint 2; I take the silence and post the 96-pixel bill in the open. SECOND: the arm types instances by frame-0 colour and looks objects up by colour alone, so the twelve slot cells, which render 4 exactly when they are blank, are Tok1 and Tok2 forever and never Panel4. Every one of my seven rules depends on that, and if the arm instead retypes by current colour then all seven fire on the wrong instances and replay collapses -- so this is the single assumption whose failure would be total rather than incremental, and I name it here so the first divergence report can be read against it."
    [depends: the_slot_is_a_two_state_display_and_three_keys_drive_it  probe: pending]
```

=== PLAYBOOK ===
```
# playbook.dsl -- what to buy with the next command, not a route.
#
# ========= THE BOARD AS THE MANUAL NOW SEES IT =========
# Slot at rows 38-39 x cols 17-22 is BLANK. Rail marker at rows 32-33.
# One bar cell burned, (53,63). Five transitions observed in total.
#
#   key(3), key(7): predicted inert here, NO WITNESS for that silence.
#   key(4): predicted twelve cells, the slot redrawn. Witnessed once.
#   key(1), key(2): predicted inert and KNOWN FALSE -- 96 cells each.
#   key(5), key(6): never pressed in this world. Nothing is known.
#
# ========= THE ONE THING WORTH BUYING =========
# THE FRAME THAT SHOWS s1. ACTION1 rewrote all 96 dynamic cells and the
# brief prints cell-level diffs only for small changes, so the pixels of
# that state have never been shown and never will be shown by a diff. They
# WILL be shown by the current-frame print if the round ends in that state.
# One press of the rewrite key, not immediately undone, converts the
# manual's largest hole into transcribable pixels. Nothing else on the board
# is worth ninety-six pixels.
#
# THE TRAP TO AVOID: with the goal empty, the only thing ranking commands is
# predicted change, and the only key this manual predicts change for is the
# slot-redraw key. Ranking by predicted pixels therefore loops on the one
# thing already at full coverage. Rank by witnesses a command would CREATE.
#
# The advertised price of the probe: 96 pixels of divergence, priced in
# advance in the manual, and it must not be read as a defect.

order     buy_the_frame_that_shows_a_state_never_yet_drawn                 [proof: lean]
order     rank_by_witnesses_a_command_would_create_not_by_pixels_it_moves   [proof: lean]
order     treat_predicted_inertness_as_ignorance_unless_a_witness_backs_it  [proof: lean]
order     settle_which_key_the_bar_answers_to_before_spending_more_of_it    [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired   [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance                [proof: lean]
order     press_the_never_pressed_keys_before_re_pressing_a_solved_one      [proof: lean]
order     separate_two_rules_that_differ_only_in_their_key_literal          [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it        [proof: lean]
order     prefer_a_probe_whose_answer_is_legible_in_the_raw_diff            [proof: lean]

prune     ranked_only_because_the_manual_predicts_the_most_pixels => dead   [proof: lean]
prune     every_rule_it_would_witness_is_already_at_full_coverage => dead   [proof: lean]
prune     ranked_only_because_a_refutation_fired_on_it => dead              [proof: lean]
prune     divergence_lies_only_on_a_cell_the_board_still_owns => dead       [proof: lean]
prune     immediately_undoes_the_command_that_just_bought_a_new_state => dead [proof: lean]
prune     repeats_a_key_whose_inertness_in_this_state_is_witnessed => dead  [proof: lean]
prune     asserts_a_goal_that_is_true_of_the_current_state => dead          [proof: lean]
prune     needs_a_click_coordinate_the_guard_language_cannot_hold => dead   [proof: lean]

heuristic states_never_yet_printed_as_a_current_frame                      [admissible: lean]
heuristic keys_whose_inertness_here_rests_on_no_witness                    [admissible: lean]
heuristic keys_never_pressed_in_this_world                                 [admissible: lean]
heuristic live_readings_of_the_bar_a_command_can_eliminate                 [admissible: lean]
heuristic unowned_cells_a_command_would_make_dynamic                       [admissible: lean]
heuristic open_questions_a_command_can_close                               [admissible: lean]
heuristic remaining_bar_cells_as_a_budget_of_unknown_denomination          [admissible: lean]

prefer    a_command_that_leaves_the_world_in_an_undrawn_state              [ev: 1/6 states hidden]
prefer    a_key_never_pressed_over_one_pressed_and_understood              [ev: 2/7 keys]
prefer    a_key_whose_predicted_silence_has_never_been_witnessed           [ev: 4/7 keys]
prefer    a_press_that_splits_the_key_reading_from_the_effect_reading      [ev: 1/1 burns]
prefer    a_press_that_repeats_a_key_from_a_state_it_has_not_acted_on      [ev: 3/3 slot keys]
prefer    an_outcome_small_enough_that_the_brief_prints_it_cell_by_cell    [ev: 3/5 diffs]
prefer    learning_the_alphabet_before_theorising_about_the_goal           [ev: 0/6 frames scored]
```

=== LOG ===
```json
[
  {"id": "O-01", "subject": "colour-0 dynamic cells", "verdict": "accept", "as": "Ink0", "why": "twelve cells form the interior ring of the 6x6 case at rows 37-40 x cols 12-15 in the current frame, and they lie inside the t1/t2 change box, so they are dynamic and need an owner."},
  {"id": "O-02", "subject": "colour-1 dynamic cells", "verdict": "accept", "as": "Tok1", "why": "eight of them are named cell-by-cell in the t3/t4/t5 diffs as slot cells, and the ninth is the case socket at (38,16); all nine are inside the t1/t2 box."},
  {"id": "O-03", "subject": "colour-2 dynamic cells", "verdict": "accept", "as": "Tok2", "why": "four slot cells named in the diffs, four rail-marker cells at rows 32-33 x cols 13-14, the socket at (39,16), and the bar end (53,63) whose 2->3 burn is the only diff outside the arena box."},
  {"id": "O-04", "subject": "colour-3 dynamic cells", "verdict": "accept", "as": "Rail3", "why": "eight cells of the rail track at rows 30-31 and 34-35 x cols 13-14; row 29 of the same track is outside the dynamic rows and is board."},
  {"id": "O-05", "subject": "colour-4 dynamic cells", "verdict": "accept", "as": "Panel4", "why": "twelve of them by subtraction only -- 97 dynamic minus the 85 I can name from the frame -- so this is the weakest declaration here and it is flagged as derived in the invariant."},
  {"id": "O-06", "subject": "colour-5 dynamic cells", "verdict": "accept", "as": "Floor5", "why": "24 background-coloured cells at cols 11-12 and 15-16 x rows 30-35; the t1 diff lists 5 among the changed colours, and 97 minus cells_needing_an_owner 73 is exactly 24, which is the independent check."},
  {"id": "O-07", "subject": "colour-6 dynamic cells", "verdict": "accept", "as": "Case6", "why": "22 cells of the case border and its 2x2 core, all inside the t1/t2 change box."},
  {"id": "O-08", "subject": "mdl_segmenter obj0/obj2/obj3 (13x36, ~440 cells)", "verdict": "reject", "why": "a 440-cell track cannot be one instance and a second type over pixels my seven colours already own would double-claim them; I take only its cell counts, 440/436/440, as the sole quantitative fact I have about the hidden state s1."},
  {"id": "O-09", "subject": "mdl_segmenter obj1 (2x54, 108 cells, all frames)", "verdict": "reject", "why": "rejected as an object for the same extent reason, accepted as evidence: it fixes the bar at rows 53-54 x cols 10-63, so the bar is 54 cells wide and does not start at col 0."},
  {"id": "O-10", "subject": "the inherited Glyph9/Vacated/Spent/Dark declarations", "verdict": "reject", "why": "no dynamic cell here has frame-0 colour 9, so Glyph9 would seat nothing, while Spent and Dark would seat on my colour-1 and colour-0 cells and fire panel rules that no transition in this evidence stream witnesses."},
  {"id": "R-01", "subject": "key3_clears_strip_tok1", "verdict": "accept", "why": "t3 lists eight colour-1 slot cells going 1->4 and no others; the guard colored(above(above(?p)), 4) is true of exactly those eight among all Tok1 instances and false of the socket at (38,16), whose two-above is colour 6."},
  {"id": "R-02", "subject": "key3_clears_strip_tok2", "verdict": "accept", "why": "the same transition lists four colour-2 slot cells going 2->4; the same guard excludes the rail marker (two-above is 3) and the bar end (two-above is 5)."},
  {"id": "R-03", "subject": "key7_clears_strip_tok1 / key7_clears_strip_tok2", "verdict": "accept", "why": "t5 reproduces t3 cell for cell under a different key; the bodies are identical and I cannot merge them because the guard grammar has no disjunction and no action domain."},
  {"id": "R-04", "subject": "key4_redraws_strip_tok1 / key4_redraws_strip_tok2", "verdict": "accept", "why": "t4 restores each of the twelve slot cells to its frame-0 colour, and typing by frame-0 colour is what lets two rules with integer-literal targets reproduce a 2-1-1/1-1-2 pattern without naming a single coordinate."},
  {"id": "R-05", "subject": "key4_burns_bar_end", "verdict": "accept", "why": "(53,63) 2->3 at t4 is the only diff outside the arena; rightof(?p) = wall picks it out of the ten Tok2 instances uniquely, and its colour guard is disjoint from the redraw rule's so the pair cannot both fire."},
  {"id": "R-06", "subject": "any rule for ACTION1 or ACTION2", "verdict": "reject", "why": "96 cells changed on each and I was given only the count and bounding box, never a pixel; writing a guessed rule would trade a known-wrong silence for an invented change, and constraint 2 forbids the entry."},
  {"id": "R-07", "subject": "burn_next (the leading-edge bar rule)", "verdict": "probe-pending", "why": "text written out inside i_cannot_draw_a_burn_on_a_cell_that_has_never_changed; it stays out until a second burn makes (53,62) dynamic, because a cell the board still explains gets no instance and the rule would be cov 0/0."},
  {"id": "L-01", "subject": "s2 = s0, so ACTION2 undoes ACTION1", "verdict": "accept", "why": "distinct_states is 5 for 6 states, so exactly one pair coincides, and t2 restored exactly the 96 cells t1 changed while t3/t4/t5 each changed a strict subset -- no other pairing is consistent."},
  {"id": "L-02", "subject": "burns iff the command index is even", "verdict": "reject", "why": "command index 2 was even and did not burn; the reading that dominated the inherited manual is refuted on the first transition that could test it here."},
  {"id": "L-03", "subject": "the bar burn is keyed to ACTION4 rather than to the redraw effect", "verdict": "probe-pending", "why": "one positive and four negatives fit both readings identically because t4 is the only transition that redrew the slot; one press of ACTION4 on an already-drawn slot separates them."},
  {"id": "L-04", "subject": "cells_needing_an_owner 73 = 97 minus the 24 background-coloured dynamic cells", "verdict": "accept", "why": "the 24 was derived from the frame before the store number was consulted, so the agreement is a check and not a fit; it is the reason I trust the whole census."},
  {"id": "L-05", "subject": "zero_space global law over 97 cells", "verdict": "entailed", "why": "its cell list is my census restated; it self-reports THIN at rank 3 of 679 features over 5 transitions, so it confirms nothing beyond which cells move."},
  {"id": "L-06", "subject": "cegis_miner verdict, the world does not narrate as one mover", "verdict": "accept", "why": "correct here and not merely an arm limitation -- every observed event is a recolour in place and nothing in six frames translates."},
  {"id": "P-01", "subject": "make the ACTION1 successor the state the round ends in", "verdict": "probe-pending", "why": "diffs are printed cell by cell only for small changes, so the 96-cell state s1 can only be read off the current-frame print; it is the largest single purchase available."},
  {"id": "P-02", "subject": "press ACTION4 with the slot already drawn", "verdict": "probe-pending", "why": "separates the key-keyed bar reading from the effect-keyed one; the answer must be read off the raw diff because the next bar cell is board and undrawable either way."},
  {"id": "P-03", "subject": "press ACTION3 or ACTION7 with the slot already blank", "verdict": "probe-pending", "why": "witnesses a silence my manual asserts on no evidence, and any change at all refutes the clear rules as written."},
  {"id": "P-04", "subject": "press ACTION5 or ACTION6", "verdict": "probe-pending", "why": "two of seven keys have never been pressed in this world and my manual asserts total inertness for both on the strength of nothing."},
  {"id": "E-01", "subject": "no way to say unobserved, the manual declines to predict", "verdict": "probe-pending", "why": "I wanted a third outcome for (state, action) beyond a named successor and identity; what I wrote instead is no rule at all for keys 1 and 2 plus a theorem posting the exact 96-pixel bill, because the compiled step is total and turns my ignorance into a confident silence."},
  {"id": "E-02", "subject": "no disjunction and no action domain in the guard grammar", "verdict": "probe-pending", "why": "I wanted one clear rule guarded on key(3) or key(7); what I wrote instead is four rules with two identical bodies, declared in a theorem as a cost paid to the DSL rather than a claim about the world."},
  {"id": "E-03", "subject": "no arithmetic across types in an invariant body", "verdict": "probe-pending", "why": "I wanted one invariant asserting the seven instance counts sum to 97; what I wrote instead is eight separate count invariants plus the summation spelled out in the census theorem."}
]
```
```
