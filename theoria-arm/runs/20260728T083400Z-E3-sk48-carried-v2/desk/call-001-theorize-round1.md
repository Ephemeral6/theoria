# call-001-theorize-round1

model: `claude-opus-5` · 569232 ms · $1.493268 · usage {"cache_creation": {"ephemeral_1h_input_tokens": 29929, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 29929, "cache_read_input_tokens": 0, "inference_geo": "not_available", "input_tokens": 2, "iterations": [{"cache_creation": {"ephemeral_1h_input_tokens": 29929, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 29929, "cache_read_input_tokens": 0, "input_tokens": 2, "output_tokens": 46851, "type": "message"}], "output_tokens": 46851, "server_tool_use": {"web_fetch_requests": 0, "web_search_requests": 0}, "service_tier": "standard", "speed": "standard"}

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
# theory.dsl -- fifth draft. Seven states (t0-t6), six commands. This round
# brought NO new world observation: it brought certify's verdict on draft four.
# So this draft is judged entirely on whether draft four's predictions held,
# and on what re-reading the board and the six transitions can still buy.
#
# (1) THE SECOND POINT PREDICTION ALSO PAID, EXACTLY. Draft four wrote: "this
#     manual therefore predicts the NEXT responsibility report on frame 0 says
#     exactly 69. If it says 68, the checker's board is not 'constant over all
#     observed frames' and I have the wrong model of the checker." certify
#     returned 69, and the arithmetic closes cell by cell: the dynamic set over
#     seven states is 74 = 8 (slot-A ring) + 9 (slot-B block) + 6 (underline,
#     both positions) + 24 (ring pixels in cell (0,0)) + 24 (ring pixels in
#     cell (1,0)) + 3 (tally). Three of those -- (5,5),(5,6),(5,7) -- are
#     background in frame 0. 71 non-background, minus Marker at (1,1) and
#     Unused at (1,5), is 69. The render model is no longer a model; it is
#     arithmetic I can run in advance, and it is written as a formula below.
#
# (2) BOTH SURPRISES ARE THE LEDGER, AND I REFUSE TO CHANGE THE OBJECT SET.
#     Draft four pre-registered the test: "a replay failure whose divergence
#     set is exactly the conceded ledger is not evidence against any rule; one
#     that touches a cell OUTSIDE it is evidence and must be answered." Every
#     cell in both surprise reports -- (1,2),(1,3),(1,6),(1,7),(2,1),(2,3),
#     (2,5),(2,6),(2,7),(3,1..3),(3,5..7),(5,1..3),(8,14..18),(9,14) -- is a
#     HUD pixel or a ring pixel already conceded by name, and the two cells the
#     manual does draw, (1,1) and (1,5), are absent from the divergence list.
#     The test passed. Nothing in the object set changes.
#
# (3) DRAFT FOUR OVER-CLAIMED THE DIRECTION TABLE AND I AM RETRACTING HALF OF
#     IT. "Reading A survives every motion observation without exception" is
#     true and nearly vacuous: key(3) and key(4) were each fired exactly once,
#     both times from cell (1,0), where LEFT is off-board and RIGHT is an
#     all-void cell. Both directions are blocked there, so two 'no move'
#     results separate nothing. The honest statement is: key(2)=down is
#     witnessed positively; key(3) and key(4) are {left,right} in an order this
#     world has never revealed; key(1) is 'up' only via a bijection assumption
#     I have not tested. The route needs five steps RIGHT along the bottom
#     corridor, so this gap is on the critical path, and the playbook now says
#     where to close it for at most one wasted command.
#
# (4) I RE-READ THE STATIC BOARD PIXEL BY PIXEL THIS ROUND AND IT ALL HELD.
#     Lattice, floor map, ribbon width, gate cell, goal cup: every claim in
#     draft four survived the recount, with two refinements now written in --
#     the maze's right edge in lattice rows 0-2 is separator column 43, and the
#     colour-8 blob at cell (0,4) is exactly rows 9-11 x cols 39-41 with the
#     vertical stroke leaving it at (12,40).

semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Marker { pos: Coord, color: Int }  # arc-colour: 9
  object Unused { pos: Coord, color: Int, present: Bool }  # arc-colour: 1
  object Spent { pos: Coord, color: Int, present: Bool }  # arc-colour: 2
  landmark hud_slot_a  # arc-cell: carried, coordinates stripped -- 
  landmark hud_slot_b  # arc-cell: carried, coordinates stripped -- 
  landmark start_cell  # arc-cell: carried, coordinates stripped -- 
  landmark button_cell  # arc-cell: carried, coordinates stripped -- 
  landmark gate_cell  # arc-cell: carried, coordinates stripped -- 
  landmark corridor_cell  # arc-cell: carried, coordinates stripped -- 
  landmark goal_cell  # arc-cell: carried, coordinates stripped -- 
  Marker [segment: mdl_obj0_ring3x3_colour9 ev: t0-t6 compress: 7]
  Unused [segment: mdl_obj1_solid3x3_colour1 ev: t0-t4 compress: 5]
  Spent [segment: mdl_obj5_ring3x3_colour2 ev: t5-t6 compress: 2]

events:
  event jumped(o, dest) | vanished(o) | appeared(o)

rules:
  rule key5_advances_marker [ev: t5 cov: 1/1]
    when act=key(5) and colored(hud_slot_b, 1) then jumped(Marker, hud_slot_b)
  rule key5_marks_slot_a_spent [ev: t5 cov: 1/1]
    when act=key(5) and colored(hud_slot_a, 9) then appeared(Spent)
  rule key5_consumes_slot_b [ev: t5 cov: 1/1]
    when act=key(5) and colored(hud_slot_b, 1) then vanished(Unused)

laws:
  invariant one_marker count(Marker) = 1 [status: observed]

  theorem render_accounting_closed "DISCHARGED TWICE, and now stated as a formula rather than a number, which is the only way it can keep earning. An object is drawn as ONE pixel; its initial cell is the raster-first cell of its declared arc-colour over the frames the arm was given; two objects sharing a colour collide on that one cell (witnessed in the second draft, where Player and Marker both landed at (1,1)); an object whose colour is absent from the frames anchors nowhere and costs nothing (witnessed by Spent, which drew no stray colour-2 pixel at (0,0)). Therefore: unexplained(frame 0) = D0 - K, where D0 is the number of dynamic cells that are non-background in frame 0 and K is the number of DISTINCT colours in frame 0 for which I have declared an object. Draft three predicted 68 against 53 and got 68; draft four predicted 69 against 68 and got 69. The formula's next falsifier is mechanical: each NEW lattice cell the ring enters turns 24 previously-constant colour-5 pixels into colour-9 pixels and so adds exactly 24 to D0 and 24 to the count; each tally pixel that flips adds exactly 1; re-entering a cell the ring has already occupied adds 0. So if the next two commands walk the ring from cell (0,0) to (1,0) to (2,0) and the tally ticks once, the next responsibility report reads 69 + 24 + 1 = 94. Any deviation from D0 - 2 that is not explained by that arithmetic refutes this theorem, not the world."
    [probe: pending]

  theorem responsibility_ceiling_is_two_pixels "69 is not slack, it is the arithmetic maximum this language reaches here, and it will grow with every cell the ring visits without any of it being a missing rule. An object is located by colour and same-colour objects collide, so a colour explains at most one cell. The colours on non-background dynamic cells of frame 0 are exactly 9 and 1; colour 5 and colour 8 have raster-first cells at (7,13) and (9,39), both constant board cells, so objects in those colours would explain nothing they were not already given. Two colours, two pixels, both claimed. I could satisfy the checker by declaring seventy single-pixel objects ONLY IF same-colour objects took distinct anchors, they do not, and even if they did I would refuse: seventy noise objects buy zero compression and teach nothing. Full-frame responsibility is unreachable in this world and I say so rather than fake it."
    [depends: render_accounting_closed  probe: pending]

  theorem replay_can_never_pass_here "replay compares whole frames and frame 0 is 69 pixels wrong before any rule fires, so 0/6 is structural and stays 0/n for every n. The diagnostic pre-registered in draft four RAN THIS ROUND AND PASSED: every divergence cell reported is in the conceded ledger and the two drawn cells are not in it. That is the only signal replay can carry here, it is a real one, and it must be re-run every round -- a divergence cell outside the ledger is evidence against a rule and must be answered."
    [depends: responsibility_ceiling_is_two_pixels  probe: pending]

  theorem the_mover_is_unnameable "the thing that plays this game is a 5x5 colour-9 ring with a one-pixel hole at its centre, and it cannot be declared. Colour 9 is raster-first-claimed by the HUD at (1,1) in frames 0-4 and at (1,5) in frames 5-6, so any colour-9 object lands on the HUD. mdl_segmenter offers no track for it: under connected_components(4) with split_by_color off the ring fuses with the colour-5 floor and the colour-8 wire into obj3, 1006 cells, colour null. I ACCEPT that fusion as fact and REJECT the conclusion cegis_miner drew from it -- 'the world does not narrate as one mover'. It narrates as exactly one mover; the mover is buried in a 1006-cell blob and owns no colour. Consequence: this manual contains no movement rule and cannot, and every movement claim lives in a theorem or in the playbook."
    [probe: pending]

  theorem lattice_geometry "the maze is an 8x6 lattice of 5x5 cells at pitch 6. Cell (r,c) occupies rows 8+6r..12+6r and cols 14+6c..18+6c for r=0..7, c=0..5; separator rows are 7+6r, separator columns 13+6c; separators are colour 5 wherever both neighbours are floor, so they divide nothing. Cell centres are (10+6r, 16+6c). Witnesses: the ring occupied exactly rows 8-12 x cols 14-18, then exactly rows 14-18 x cols 14-18, a displacement of exactly 6; its hole sat at (10,16) then (16,16), each the exact centre; the goal dot is at (52,46), the centre of (7,5); the colour-8 blob is centred on (10,40), the centre of (0,4). Refinement from this round's recount: in lattice rows 0-2 the floor stops at separator column 43, so column c=5 is void above the bottom corridor."
    [probe: pending]

  theorem floor_map "the complete read of the static board by lattice cell, re-verified pixel by pixel this round. r=0: c=0..4 floor (an open five-cell corridor, separators 25,31,37,43 all floor), c=5 void. r=1: c=0 floor, c=1 void (rows 14-18 x cols 20-24 all colour 0), c=2 floor, c=3 void, c=4 the three-wide ribbon, c=5 void. r=2: c=0,1,2 floor, c=3 void, c=4 ribbon, c=5 void. r=3, r=4: c=0 floor, c=1,2,3 void, c=4 ribbon, c=5 void. r=5: c=0 is a 5x5 of colour 8 (23 pixels colour 8, colour 5 only at (39,14) and (41,14)), c=1,2,3 are the three-row stripe at rows 39-41 only, c=4 the ribbon junction, c=5 void. r=6: c=0 floor, rest void. r=7: c=0..5 all floor, the bottom corridor rows 50-54 x cols 14-48, arriving at the goal cup from the left. Consequence: the floor-only reachable set from start is exactly twelve cells -- (0,0),(0,1),(0,2),(0,3),(0,4),(1,0),(1,2),(2,0),(2,1),(2,2),(3,0),(4,0) -- and it does not contain the goal."
    [depends: lattice_geometry  probe: pending]

  theorem void_blocks_and_the_guard_language_is_inverted "colour 0 is wall, colour 5 is floor. Witness: key(4) fired from cell (1,0) at t4 faced the all-void cell (1,1) and moved nothing. Note the trap: free(x) in this DSL tests the BACKGROUND colour, which here is 0 -- exactly the cells that are NOT enterable. Any movement rule ever written here must be guarded colored(x, 5) and never free(x). Untested: whether a cell that is void at its edges but non-void at its centre blocks. No such cell is on the intended route."
    [depends: floor_map  probe: pending]

  theorem the_ribbon_is_too_narrow_for_the_ring "the sharpest deduction available without an experiment, and it kills half the search space. The colour-8 figure is one pixel wide throughout: a vertical stroke down col 40 from row 12 to row 41 with colour 5 at cols 39 and 41 and void at 38 and 42; a horizontal stroke along row 40 from col 40 back to col 14 with colour 5 at rows 39 and 41 and void at 38 and 42. Total corridor width three; the mover is five. So cells (1,4),(2,4),(3,4),(4,4),(5,1),(5,2),(5,3),(5,4) cannot hold the ring whatever colour 8 means, and no route may pass through them. Exactly one colour-8 cell has a full 5x5 of non-void pixels: (5,0), rows 38-42 x cols 14-18."
    [depends: floor_map, lattice_geometry  probe: pending]

  theorem cell_five_zero_is_the_gate "one cell decides the level. Column 0 is floor at r=0,1,2,3,4 and again at r=6,7; the bottom corridor r=7 runs unbroken to the goal; between them sits (5,0), the colour-8 filled cell, gate_cell in the word table, joined above by floor separator row 37 and below by floor separator row 43. There is no other join between the reachable twelve and the goal region. So either the ring can enter (5,0), or the goal as I read it is unreachable and the win condition is something else. No transition tests it; one command from (4,0) does, and that command is on the critical path either way, so it costs nothing if the gate is open."
    [depends: the_ribbon_is_too_narrow_for_the_ring  probe: pending]

  theorem the_eight_line_is_probably_a_wire_and_the_blob_is_its_button "the competing reading of colour 8, kept because it is cheap to keep and expensive to have missed, and strengthened this round by the recount. The figure is one connected line with two distinguished ends: a 3x3 blob at rows 9-11 x cols 39-41, dead centre of cell (0,4), which is REACHABLE floor four steps right of start; and the filled 5x5 at (5,0), which is the gate. A line joining a reachable marked cell to the one blocking cell reads as button-and-door at least as naturally as it reads as a drawn path. Two further hints: the blob is 3x3 like the HUD icons rather than 5x5 like a cell, and the ring standing on (0,4) would show colour 8 through its central hole -- the same 'dot through the hole' signature the goal cell has. If the gate refuses entry, standing on button_cell and watching gate_cell for a colour change is the next experiment, and it is eight commands out and back from (0,0)."
    [depends: cell_five_zero_is_the_gate  probe: pending]

  theorem goal_is_the_cupped_cell "rows 48-56 x cols 42-50 is a 9x9 colour-5 box drawn around cell (7,5). Inside it colour 9 paints row 49 cols 43-49, row 55 cols 43-49 and col 49 rows 50-54: a cup open to the LEFT, which is the side the bottom corridor arrives from. A lone colour-9 pixel sits at (52,46), the exact centre of (7,5), and the ring's hole is at its own exact centre, so bringing the ring here makes the dot show through the hole. It is the only cell in the frame drawn this way and it is drawn in the ring's own colour. Read off the static board; no transition witnesses it. Shortest route consistent with floor_map: seven steps down column 0, five steps right along the bottom corridor, twelve commands."
    [depends: lattice_geometry, floor_map  probe: pending]

  theorem direction_map_is_one_third_known "RETRACTION of draft four's confident table, on re-examination of what the negative results can separate. key(2) = DOWN: positively witnessed at t2, cell (0,0) to (1,0), the only motion in the record. key(1): fired at t1 and again at t6, both times from (0,0), both times nothing moved; (0,0) has floor to its right and floor below, so key(1) is NOT right and NOT down, leaving key(1) in {up, left}. key(3) at t3 and key(4) at t4 were BOTH fired from (1,0), which has floor above and floor below but off-board to the left and an all-void cell to the right; so each of them is in {left, right} and NOTHING in this record distinguishes them from each other. If keys 1-4 are a bijection onto the four directions then key(3) and key(4) exhaust {left,right}, forcing key(1) = up -- but that bijection is an assumption, not an observation, and key(1) could equally be a no-op that only ticks the clock. What matters for the route: the bottom corridor needs five steps RIGHT, so the left/right order MUST be settled, and it must be settled at a cell where a wrong guess cannot displace the ring."
    [depends: floor_map  probe: pending]

  theorem tally_is_a_two_command_clock "row 63 is a 64-pixel colour-9 bar filling with colour 1 from the right: (63,63) at t2, (63,62) at t4, (63,61) at t6, and no advance at t1, t3 or t5. A perfect alternation, 6/6, one pixel per two commands, independent of which key was pressed, independent of whether anything moved, and NOT reset by key(5) -- which is the observation that rules out reading it as a per-attempt score. Three of sixty-four consumed leaves about 122 commands against a twelve-command route: not binding, so wandering rather than walls is what would kill this level. THE HONEST CAVEAT, unchanged and unresolved: a perfect alternation over six samples is roughly a one-in-thirty accident, and zero_space's own verdict is THIN -- six transitions constrain rank 4 of 370 features, so nearly every law it can state is unfalsified rather than confirmed. I accept that verdict for this law too. Every command tests it for free and the playbook says to read it every time; the first tick on an odd command or the first pair of consecutive ticks kills it."
    [probe: pending]

  theorem hud_is_two_attempts_and_one_is_gone "two 3x3 slots at cols 1-3 and cols 5-7 with a 3-pixel underline at row 5 marking the active one. Frames 0-4: slot A a colour-9 ring, underlined; slot B a solid colour-1 block. Frames 5-6: slot A a colour-2 ring, unmarked; slot B a colour-9 RING, underlined. So the active slot shows the player's own icon in the player's own colour, an unused slot is a solid colour-1 block, a spent slot is a colour-2 ring. key(5) did all of that in one nine-frame command, moved the ring back to start, and did not reset the tally. Reading: two attempts, key(5) spends one and restarts the position. The competing reading -- 'objective cleared, next objective' -- is not dead, but a position reset with no tally reset argues against it. Either way slot B is the LAST slot, and the guards on the three rules encode that: with slot A at colour 2 and slot B at colour 9, none of them can fire again."
    [depends: key5_advances_marker, key5_marks_slot_a_spent, key5_consumes_slot_b  probe: pending]

  theorem two_action_keys_have_never_been_pressed "ARC offers ACTION1..ACTION7 and this world has seen only 1..5. Draft four never said so and that is a gap, not a fact. ACTION6 in this family is customarily a click carrying coordinates, which this guard language cannot express at all; ACTION7 is unknown. I do not press them, and the playbook says why: exactly one attempt remains, key(5) demonstrated that a single key press can cost an attempt and reset the position, and an unknown key is therefore a bet with an unbounded downside on a level whose route I believe I can already walk. They are held in reserve for the case where both the gate and the button refuse."
    [probe: pending]

  theorem spent_anchor_unresolved_and_maybe_unresolvable "Spent survives on the evidence that it cost nothing in frame 0, which is what a colour absent from the frame should cost. Its other half -- whether the arm anchors from the whole frame stack, in which case Spent sits at (1,1) and draws colour 2 there from t5 on, correctly, and before t5 incorrectly -- may never be answered, because responsibility reports frame 0 only and replay diverges at t=0 and stops. I flag this as a limit of the instrument, not a hole in the world: nothing about the route depends on it."
    [depends: render_accounting_closed  probe: pending]

  theorem vacated_cell_repaints_to_five "when the ring left cell (0,0) at t2 those 24 pixels became colour 5, not background 0, and cell (1,0) did the same at t5. A fact about the world and a defect I cannot repair: nothing in the language repaints a cell an object has left, and a colour-5 Floor object would anchor at (7,13) and paint one pixel of a 1006-cell blob. The 24 pixels of whichever start cell is currently empty are conceded in every frame."
    [probe: pending]

  theorem cascade_length_is_a_signal "t2 returned 7 frames and t5 returned 9 for a single command; t1, t3, t4, t6 returned 1 each, and t4 and t6 still changed a pixel. A multi-frame command is an animation of real motion; a single-frame command is an instant verdict. Only the last frame reaches me and cascade single_frame is the only value that compiles, so the slide itself is invisible -- but the frame COUNT is not, and it is a free channel: any command returning more than one frame moved something even if I cannot see what. This is how the left/right probe will be read, and seven frames for a six-pixel displacement is quiet support for lattice_geometry."
    [probe: pending]

  theorem no_goal_section_on_purpose "the win condition I believe is 'the ring reaches goal_cell'. Its subject is unnameable, so writing it would either fail to compile or name the HUD marker and be false. An absent goal compiles to is_goal -> False, which under-claims; a goal about the wrong object over-claims and is refuted by the first win. I under-claim and the playbook carries the direction. start_cell, button_cell, gate_cell, corridor_cell and goal_cell are declared with no rule referencing them for one reason: the DSL has nowhere else to write a coordinate and the playbook's heuristics need referents to name."
    [depends: goal_is_the_cupped_cell, the_mover_is_unnameable  probe: pending]

  theorem conceded_pixels "the ledger for frame 0 on the seven-state dynamic set of 74 cells, 3 of them background there. Drawn correctly: 2 -- Marker at (1,1), Unused at (1,5). Conceded: 7 of the slot-A ring, 8 of the slot-B block, 3 of the slot-A underline, 24 of the player ring in cell (0,0), 24 of the repainted floor in cell (1,0), 3 of the tally bar. 7+8+3+24+24+3 = 69, the number predicted and the number returned, and every cell certify listed is in this list. Every one of them fails for the same reason -- the object that owns them can be given exactly one Coord -- and not one of them is a missing rule. This violates full-frame responsibility knowingly and completely, and I would rather say so in a paragraph than declare seventy single-pixel objects that would satisfy the checker and teach nothing."
    [depends: responsibility_ceiling_is_two_pixels, vacated_cell_repaints_to_five  probe: pending]
```

## The playbook as it stands

```
# playbook.dsl -- the manual has no movement rule and cannot have one (the
# mover has no colour of its own), so the searcher gets nothing routable from
# the compiled theory and everything actionable is here. Five facts drive it,
# four of them read off the static board rather than guessed:
#
#   colour 0 is WALL and colour 5 is FLOOR, so free() must never be read as
#     walkable;
#   the colour-8 line is three pixels wide and the mover is five, so no route
#     may pass through the ribbon cells whatever colour 8 means;
#   exactly one cell joins the reachable twelve to the goal region -- the
#     colour-8 filled cell (5,0), gate_cell -- and it lies on the critical
#     path, so testing it costs nothing when the gate is open;
#   NEW THIS ROUND: the left/right binding of the two remaining direction keys
#     is completely undetermined -- both were only ever fired from a cell where
#     left and right were both blocked -- and the bottom corridor needs five
#     steps right, so this must be settled where a wrong guess cannot displace
#     the ring;
#   one HUD attempt remains. Spending it buys a position reset and nothing
#     else, so it is not an experiment, it is the end -- and the same logic
#     bars the two action keys never yet pressed.

order   read_the_tally_and_the_frame_count_after_every_command          [proof: lean]
order   settle_the_lateral_binding_where_one_side_is_off_board          [proof: lean]
order   descend_column_zero_before_exploring_the_blank_side_pockets     [proof: lean]
order   resolve_gate_cell_passability_before_any_other_experiment       [proof: lean]
order   visit_button_cell_only_if_the_gate_refuses                      [proof: lean]
order   press_a_never_pressed_key_only_if_gate_and_button_both_refuse   [proof: lean]
order   never_spend_the_last_hud_slot                                   [proof: lean]

prefer  the_direction_key_with_a_positive_motion_witness                [ev: 1/1 observed motions]
prefer  a_lateral_test_from_a_cell_whose_other_side_is_off_board        [ev: 2/2 uninformative lateral tests so far]
prefer  a_non_void_neighbour_cell_over_an_all_void_neighbour_cell       [ev: 1/1 blocked attempts]
prefer  a_full_five_by_five_non_void_target_over_a_three_wide_ribbon    [ev: 8/8 ribbon cells read]
prefer  the_only_non_void_neighbour_when_the_corridor_is_one_cell_wide  [ev: 1/1 corridors read]
prefer  the_neighbour_that_reduces_lattice_distance_to_goal_cell        [ev: 1/1 goal candidates in frame]
prefer  a_command_whose_cascade_returned_many_frames_over_one_frame     [ev: 2/2 real motions were multi_frame]
prefer  an_untried_action_from_a_cell_that_has_a_known_open_neighbour   [ev: 2/6 commands changed the board]

heuristic lattice_steps_from_ring_to_gate_cell_while_gate_is_untested   [admissible: lean]
heuristic lattice_steps_from_ring_to_corridor_cell_then_to_goal_cell    [admissible: lean]
heuristic lattice_steps_from_ring_to_button_cell_once_the_gate_refuses  [admissible: lean]

prune   target_cell_is_entirely_colour0 => dead                         [proof: lean]
prune   target_cell_is_a_three_wide_ribbon => dead                      [proof: lean]
prune   all_neighbour_cells_entirely_colour0 and not goal => dead       [proof: lean]
prune   route_that_leaves_column_zero_below_lattice_row_two => dead     [proof: lean]
prune   repeat_of_a_key_already_seen_to_do_nothing_from_this_cell => dead [proof: lean]
prune   both_hud_slots_spent and not goal => dead                       [proof: lean]
prune   tally_bar_full and not goal => dead                             [proof: lean]
```

## Why you are being called: the surprises that fired

### render_mismatch (empirical family -> theory.dsl)

72 pixels of frame 0 belong to neither the board nor any declared object

```json
{
 "cells": [
  [
   30,
   13,
   5,
   3
  ],
  [
   30,
   14,
   5,
   3
  ],
  [
   31,
   13,
   5,
   3
  ],
  [
   31,
   14,
   5,
   3
  ],
  [
   32,
   13,
   5,
   2
  ],
  [
   32,
   14,
   5,
   2
  ],
  [
   32,
   17,
   5,
   4
  ],
  [
   32,
   18,
   5,
   4
  ],
  [
   32,
   19,
   5,
   4
  ],
  [
   32,
   20,
   5,
   4
  ],
  [
   32,
   21,
   5,
   4
  ],
  [
   32,
   22,
   5,
   4
  ],
  [
   33,
   13,
   5,
   2
  ],
  [
   33,
   14,
   5,
   2
  ],
  [
   33,
   17,
   5,
   4
  ],
  [
   33,
   18,
   5,
   4
  ],
  [
   33,
   19,
   5,
   4
  ],
  [
   33,
   20,
   5,
   4
  ],
  [
   33,
   21,
   5,
   4
  ],
  [
   33,
   22,
   5,
   4
  ],
  [
   34,
   13,
   5,
   3
  ],
  [
   34,
   14,
   5,
   3
  ],
  [
   35,
   13,
   5,
   3
  ],
  [
   35,
   14,
   5,
   3
  ]
 ],
 "count": 72
}
```

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
   "manual_says": 5,
   "world_says": 6
  },
  {
   "cell": [
    30,
    14
   ],
   "manual_says": 5,
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
   "manual_says": 5,
   "world_says": 0
  },
  {
   "cell": [
    31,
    14
   ],
   "manual_says": 5,
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
   "manual_says": 5,
   "world_says": 6
  },
  {
   "cell": [
    32,
    14
   ],
   "manual_says": 5,
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
   "manual_says": 5,
   "world_says": 2
  },
  {
   "cell": [
    32,
    18
   ],
   "manual_says": 5,
   "world_says": 1
  },
  {
   "cell": [
    32,
    19
   ],
   "manual_says": 5,
   "world_says": 1
  },
  {
   "cell": [
    32,
    20
   ],
   "manual_says": 5,
   "world_says": 2
  },
  {
   "cell": [
    32,
    21
   ],
   "manual_says": 5,
   "world_says": 1
  },
  {
   "cell": [
    32,
    22
   ],
   "manual_says": 5,
   "world_says": 1
  }
 ],
 "cells_wrong": 70,
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
    "manual_says": 5,
    "world_says": 6
   },
   {
    "cell": [
     30,
     14
    ],
    "manual_says": 5,
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
    "manual_says": 5,
    "world_says": 0
   },
   {
    "cell": [
     31,
     14
    ],
    "manual_says": 5,
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
    "manual_says": 5,
    "world_says": 6
   },
   {
    "cell": [
     32,
     14
    ],
    "manual_says": 5,
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
    "manual_says": 5,
    "world_says": 2
   },
   {
    "cell": [
     32,
     18
    ],
    "manual_says": 5,
    "world_says": 1
   },
   {
    "cell": [
     32,
     19
    ],
    "manual_says": 5,
    "world_says": 1
   },
   {
    "cell": [
     32,
     20
    ],
    "manual_says": 5,
    "world_says": 2
   },
   {
    "cell": [
     32,
     21
    ],
    "manual_says": 5,
    "world_says": 1
   },
   {
    "cell": [
     32,
     22
    ],
    "manual_says": 5,
    "world_says": 1
   }
  ],
  "cells_wrong": 70,
  "kind": "frame_mismatch",
  "t": 0
 },
 "proof_layer_available": false,
 "replay": {
  "detail": "0/5 transitions replay exactly",
  "matched": 0,
  "ok": false,
  "transitions": 5
 },
 "responsibility": {
  "cells_unexplained": 72,
  "detail": "72 pixels of frame 0 belong to neither the board nor any declared object",
  "ok": false,
  "total_cells": 4096
 },
 "unambiguous": {
  "actions": 1,
  "clashes": [],
  "detail": "no (state, action) among 6 x 1 admitted two rules",
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

=== PLAYBOOK ===
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

=== LOG ===
```json
[
  {"id": "O-01", "subject": "mdl_segmenter obj0/obj2/obj3 (440, 436, 440 cells, shape 13x36, colour null)", "verdict": "reject",
   "as": "nothing", "why": "all three are connected_components(4) blobs that fuse the whole panel with the colour-4 arena; the engine's own variants report gain_bits -4037 and -10409, so by its own accounting these tracks cost more than the pixels they explain."},
  {"id": "O-02", "subject": "mdl_segmenter obj1 (108 cells, shape 2x54, present in all 6 frames)", "verdict": "reject",
   "as": "nothing", "why": "a 2x54 strip present in every frame at constant size is rows 53-54, of which exactly one cell (53,63) has ever changed; declaring 108 cells to own 1 fails the gain test outright."},
  {"id": "O-03", "subject": "colour 6 cells of the expanded slot", "verdict": "accept",
   "as": "Casing (arc-instances: all)", "why": "22 dynamic cells in frame 0, all inside rows 36-41 x cols 11-16; the count is one of six that sum to the store's cells_needing_an_owner = 73."},
  {"id": "O-04", "subject": "colour 0 cells of the expanded slot interior", "verdict": "accept",
   "as": "Cavity (arc-instances: all)", "why": "12 dynamic cells, rows 37-40, forming the hollow inside the casing; part of the 73-cell closure."},
  {"id": "O-05", "subject": "colour 3 cells at cols 13-14", "verdict": "accept",
   "as": "Rail (arc-instances: all)", "why": "8 dynamic cells at rows 30,31,34,35; (29,13) and (29,14) are the same colour but constant, so the arm leaves them to the board, which is exactly the split the reconstruction predicts."},
  {"id": "O-06", "subject": "colour 1 cells", "verdict": "accept",
   "as": "Pip (arc-instances: all)", "why": "9 dynamic cells in frame 0: the port cell (38,16) plus 8 of the 12 strip cells, matching the 8 colour-1 entries in the t3 diff."},
  {"id": "O-07", "subject": "colour 2 cells", "verdict": "accept",
   "as": "Stud (arc-instances: all)", "why": "10 dynamic cells: 4 collapsed-slot core, port cell (39,16), 4 strip cells matching the 4 colour-2 entries in the t3 diff, and the meter tip (53,63)."},
  {"id": "O-08", "subject": "colour 4 cells inside the dynamic set", "verdict": "accept",
   "as": "Erased (arc-instances: all)", "why": "12 dynamic cells at rows 32-33 x cols 17-22, the collapsed slot's strip showing arena colour; the arena proper is constant and stays with the board."},
  {"id": "O-09", "subject": "colour 14 block rows 31-34 x cols 42-45", "verdict": "reject",
   "as": "board", "why": "it appears in no diff and is outside the 97 dynamic cells, so by the manual's own definition it is board; it is named in a theorem as a target candidate, not declared."},
  {"id": "L-01", "subject": "S2 = S0, i.e. ACTION2 exactly undoes ACTION1", "verdict": "accept",
   "why": "distinct_states = 5 over six states, and every pair other than (S0,S2) is separated either by the meter cell (53,63) or by the 96-cell t2 diff that S1 cannot satisfy; one coincidence is forced and only one pair can host it."},
  {"id": "L-02", "subject": "frame 0 reconstructed cell for cell", "verdict": "accept",
   "why": "running t5, t4, t3 backwards from the shown frame onto S2 = S0 yields a dynamic set of 97 cells and a non-background population of 73, against store values 97 and 73 that were not used to build it."},
  {"id": "L-03", "subject": "zero_space global law spanning 97 cells", "verdict": "reject",
   "why": "the engine's own evidence_adequacy says 5 transitions constrain rank 3 of 679 features, so a law touching nearly every dynamic cell is a vector in a 676-dimensional null space, unfalsified rather than confirmed."},
  {"id": "L-04", "subject": "cegis_miner verdict that the world does not narrate as one mover", "verdict": "accept",
   "why": "correct and consistent with the diffs, which contain no translation of any figure; every observed change is a recolouring in place. It licenses no rule, so it is recorded and nothing is built on it."},
  {"id": "R-01", "subject": "key(3) blanks the 12 strip cells of the expanded slot", "verdict": "accept",
   "as": "key3_blanks_the_strip_pips + key3_blanks_the_strip_studs", "why": "t3 shows exactly 8 colour-1 and 4 colour-2 cells going to 4; the split by class is forced because recolored takes an integer literal and the restore direction needs to know which cell was which colour."},
  {"id": "R-02", "subject": "key(7) has the same effect as key(3)", "verdict": "accept",
   "as": "key7_blanks_the_strip_pips + key7_blanks_the_strip_studs", "why": "t5 reproduces the t3 diff cell for cell from an equivalent strip state; written as separate rules because one witness each cannot establish that the two keys are the same key."},
  {"id": "R-03", "subject": "key(4) restores the stored strip pattern", "verdict": "accept",
   "as": "key4_restores_the_strip_pips + key4_restores_the_strip_studs", "why": "t4 restored all 12 cells to the identical pattern, so the pattern is stored off-frame and instance identity carries it; guarded on colored(?p, 4), which in the blanked state selects exactly the 12 strip instances and nothing else."},
  {"id": "R-04", "subject": "key(4) advances the meter tip", "verdict": "accept",
   "as": "key4_advances_the_meter", "why": "(53,63) went 2 to 3 at t4 and at no other step; guarded by colored(above,5) and colored(below,4), which is unique to (53,63) among all ten Stud instances, and disjoint from the restore rule because that one requires colour 4."},
  {"id": "R-05", "subject": "whether key(3), key(4), key(7) blank/show or toggle", "verdict": "probe-pending",
   "why": "each fired once from a state where blank and toggle agree; pressing key(3) twice from a shown strip separates them for zero meter cost, and the playbook orders it."},
  {"id": "R-06", "subject": "the 96-cell ACTION1/ACTION2 slot swap", "verdict": "probe-pending",
   "why": "the effect is known and stated as a theorem; no rule is written because the language cannot select a row band, so the manual knowingly predicts no change for keys 1 and 2 and pre-registers replay failing at t1 and t2."},
  {"id": "E-01", "subject": "relocating a 6x6 widget by six rows in one transition", "verdict": "probe-pending",
   "why": "wanted one rule saying the expanded slot and the collapsed slot exchange drawings; moved() shifts one instance one cell, jumped() needs a landmark per instance, and no guard restricts a forall to a row band. Wrote theorem the_swap_is_inexpressible_and_i_refuse_to_fake_it instead, with the 96 = 36 + 36 + 12 + 12 arithmetic that witnesses the swap."},
  {"id": "E-02", "subject": "naming the 2x6 strip as an object", "verdict": "probe-pending",
   "why": "wanted a Strip type covering rows 38-39 x cols 17-22; the arm finds objects by colour only and the strip spans colours 1, 2 and 4 while those colours also occur outside it. Wrote four negative neighbour guards to carve it out of Pip and Stud, and admitted in theorem colour_classes_are_not_the_worlds_objects that those guards are pixel-fitting rather than concept."},
  {"id": "E-03", "subject": "a possible coordinate-click action", "verdict": "probe-pending",
   "why": "ACTION5 and ACTION6 are unpressed and one is customarily a click carrying coordinates that act=key(n) cannot express. Wrote theorem two_keys_have_never_been_pressed and an order line to press them early while the meter is long."},
  {"id": "P-01", "subject": "responsibility on frame 0", "verdict": "probe-pending",
   "why": "predicted 0 unexplained. The single alternative is pre-registered: if arc-instances: all anchors over the union of frames rather than frame 0, the residue is drawn from the 12 strip cells and (53,63) and nothing else; a residue outside those 13 cells refutes the frame-0 reconstruction."},
  {"id": "P-02", "subject": "replay", "verdict": "probe-pending",
   "why": "predicted 3/5, first divergence at t=1 with 96 cells wrong in rows 30-41 x cols 11-22. Any divergence at t3, t4 or t5 is evidence against the seven strip rules and must be answered next round."},
  {"id": "P-03", "subject": "the unread strip of slot A", "verdict": "probe-pending",
   "why": "slot A's strip has been visible in exactly one state of six and its pattern was never recorded; one free press of key(1) makes it readable, and until it is read there is no basis for any hypothesis about what the two strips encode."}
]
```
```
