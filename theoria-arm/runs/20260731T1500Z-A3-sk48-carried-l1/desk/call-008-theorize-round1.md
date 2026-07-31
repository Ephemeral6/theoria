# call-008-theorize-round1

model: `claude-opus-5` · 586556 ms · $1.636750 · usage {"cache_creation": {"ephemeral_1h_input_tokens": 42254, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 42254, "cache_read_input_tokens": 0, "inference_geo": "not_available", "input_tokens": 2, "iterations": [{"cache_creation": {"ephemeral_1h_input_tokens": 42254, "ephemeral_5m_input_tokens": 0}, "cache_creation_input_tokens": 42254, "cache_read_input_tokens": 0, "input_tokens": 2, "output_tokens": 47265, "type": "message"}], "output_tokens": 47265, "server_tool_use": {"web_fetch_requests": 0, "web_search_requests": 0}, "service_tier": "standard", "speed": "standard"}

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
 "distinct_states": 12,
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
- t6   ACTION4   frames=2   state=NOT_FINISHED (38,17) 4->2; (38,18) 4->1; (38,19) 4->1; (38,20) 4->2; (38,21) 4->1; (38,22) 4->1; (39,17) 4->1; (39,18) 4->1; (39,19) 4->2; (39,20) 4->1; (39,21) 4->1; (39,22) 4->2
- t7   ACTION3   frames=2   state=NOT_FINISHED (38,17) 2->4; (38,18) 1->4; (38,19) 1->4; (38,20) 2->4; (38,21) 1->4; (38,22) 1->4; (39,17) 1->4; (39,18) 1->4; (39,19) 2->4; (39,20) 1->4; (39,21) 1->4; (39,22) 2->4
- t8   ACTION4   frames=2   state=NOT_FINISHED (38,17) 4->2; (38,18) 4->1; (38,19) 4->1; (38,20) 4->2; (38,21) 4->1; (38,22) 4->1; (39,17) 4->1; (39,18) 4->1; (39,19) 4->2; (39,20) 4->1; (39,21) 4->1; (39,22) 4->2; (53,62) 2->3
- t9   ACTION3   frames=2   state=NOT_FINISHED (38,17) 2->4; (38,18) 1->4; (38,19) 1->4; (38,20) 2->4; (38,21) 1->4; (38,22) 1->4; (39,17) 1->4; (39,18) 1->4; (39,19) 2->4; (39,20) 1->4; (39,21) 1->4; (39,22) 2->4
- t10  ACTION4   frames=2   state=NOT_FINISHED (38,17) 4->2; (38,18) 4->1; (38,19) 4->1; (38,20) 4->2; (38,21) 4->1; (38,22) 4->1; (39,17) 4->1; (39,18) 4->1; (39,19) 4->2; (39,20) 4->1; (39,21) 4->1; (39,22) 4->2
- t11  ACTION3   frames=2   state=NOT_FINISHED (38,17) 2->4; (38,18) 1->4; (38,19) 1->4; (38,20) 2->4; (38,21) 1->4; (38,22) 1->4; (39,17) 1->4; (39,18) 1->4; (39,19) 2->4; (39,20) 1->4; (39,21) 1->4; (39,22) 2->4; (53,61) 2->3
- t12  ACTION4   frames=2   state=NOT_FINISHED (38,17) 4->2; (38,18) 4->1; (38,19) 4->1; (38,20) 4->2; (38,21) 4->1; (38,22) 4->1; (39,17) 4->1; (39,18) 4->1; (39,19) 4->2; (39,20) 4->1; (39,21) 4->1; (39,22) 4->2
- t13  ACTION3   frames=2   state=NOT_FINISHED (38,17) 2->4; (38,18) 1->4; (38,19) 1->4; (38,20) 2->4; (38,21) 1->4; (38,22) 1->4; (39,17) 1->4; (39,18) 1->4; (39,19) 2->4; (39,20) 1->4; (39,21) 1->4; (39,22) 2->4
- t14  ACTION4   frames=2   state=NOT_FINISHED (38,17) 4->2; (38,18) 4->1; (38,19) 4->1; (38,20) 4->2; (38,21) 4->1; (38,22) 4->1; (39,17) 4->1; (39,18) 4->1; (39,19) 4->2; (39,20) 4->1; (39,21) 4->1; (39,22) 4->2; (53,60) 2->3
- t15  ACTION3   frames=2   state=NOT_FINISHED (38,17) 2->4; (38,18) 1->4; (38,19) 1->4; (38,20) 2->4; (38,21) 1->4; (38,22) 1->4; (39,17) 1->4; (39,18) 1->4; (39,19) 2->4; (39,20) 1->4; (39,21) 1->4; (39,22) 2->4
- t16  ACTION4   frames=2   state=NOT_FINISHED (38,17) 4->2; (38,18) 4->1; (38,19) 4->1; (38,20) 4->2; (38,21) 4->1; (38,22) 4->1; (39,17) 4->1; (39,18) 4->1; (39,19) 4->2; (39,20) 4->1; (39,21) 4->1; (39,22) 4->2
- t17  ACTION3   frames=2   state=NOT_FINISHED (38,17) 2->4; (38,18) 1->4; (38,19) 1->4; (38,20) 2->4; (38,21) 1->4; (38,22) 1->4; (39,17) 1->4; (39,18) 1->4; (39,19) 2->4; (39,20) 1->4; (39,21) 1->4; (39,22) 2->4; (53,59) 2->3

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
   "recolor": 20,
   "vanish": 2
  },
  "n_frames": 18,
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
    "frames_present": 18,
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
    "frames_present": 16,
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
    "baseline_bits": 5791,
    "compression_ratio": 1.424279,
    "events": 24,
    "gain_bits": -2457,
    "ms": 14,
    "script_bits": 8248,
    "split_by_color": false,
    "tracks": 4
   },
   {
    "baseline_bits": 5791,
    "compression_ratio": 6.883094,
    "events": 173,
    "gain_bits": -34069,
    "ms": 50,
    "script_bits": 39860,
    "split_by_color": true,
    "tracks": 89
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
   "dynamic_cells": 101,
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
  "distinct_states": 12,
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
 },
 "window": {
  "box": [
   29,
   10,
   54,
   63
  ],
  "covered": 1.0,
  "dynamic_cells": 101,
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
  "cells_dynamic": 101,
  "cells_used": 101,
  "colours": [
   "c0",
   "c1",
   "c2",
   "c3",
   "c4",
   "c5",
   "c6"
  ],
  "difference_rank": 7,
  "engine": "zero_space",
  "evidence_adequacy": {
   "constrained_fraction": 0.009901,
   "difference_rank": 7,
   "features": 707,
   "space_dimension": 700,
   "transitions": 17,
   "verdict": "THIN: 17 transitions constrain rank 7 of 707 features, so the null space has dimension 700 and nearly every vector in it is a 'law' that is true over these states and unfalsified rather than confirmed. Treat every law below as a correlation awaiting a transition that could break it, not as a conservation law."
  },
  "features": 707,
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
      59
     ],
     [
      53,
      60
     ],
     [
      53,
      61
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
  
```

The full proposal stream is 2774 rows in `candidates.jsonl`.

## The manual as it stands

```
# theory.dsl -- THIRTEENTH DRAFT.
#
# 0. THIS ROUND HAS EXACTLY ONE CAUSE AND I WILL NOT DRESS IT UP AS INSIGHT.
#    The compiler refused the twelfth draft: "Line 111: Expected 'goal'
#    statement, got: laws:". Line 111 was the bare `goal:` header I wrote with
#    nothing under it, deliberately, to make the manual's silence about winning
#    visible on its face. That device does not exist in this grammar: a `goal:`
#    header must be followed by a goal statement, and the ONLY legal way to say
#    "I do not know the goal" is to omit the section entirely, which compiles
#    to is_goal -> False. The section is now gone and the intent has moved into
#    a theorem, where prose belongs. Logged as E-01 rather than hidden, because
#    a manual that silently drops a section it once thought load-bearing is a
#    manual whose author has stopped reading his own diffs.
#
# 1. NO WORLD COMMAND WAS PRESSED THIS ROUND EITHER. The store is byte-
#    identical again: steps 14, states 14, distinct_states 9, dynamic_cells 99,
#    cells_needing_an_owner 75, constant_cells 3997. Every engine returned what
#    it returned twice before. So nothing below may be justified by new
#    observation, and nothing below claims to be. Two consecutive rounds with
#    no press is now itself a fact worth stating: the first-ranked probe has
#    been skipped FOUR times.
#
# 2. NO RULE IS EDITED AND NO EVIDENCE TAG MOVES. No transition was added, so
#    no rule gained or lost a witness. The eight rules stand at 132/132 cell
#    recolourings plus one seed plus two marches. Certify's numbers must come
#    back identical -- 9 of 13 replay, 0 unexplained of 4096, 0 clashes over 42
#    pairs -- and I pre-register that below. Removing the goal section cannot
#    move any of them, because is_goal was already False in effect; if any
#    number DOES move, the parse failure was masking something and I want to
#    know that more than I want to be right.
#
# 3. THE SURPRISE IS THE SAME SURPRISE AND THE ANSWER IS THE SAME REFUSAL.
#    Transition 0, ACTION1, 96 cells, first cell (30,11) manual 5 world 6. This
#    is the selector swap, which I have proven inexpressible twice over --
#    once by constraint 5 (five cells with one indistinguishable guard reading
#    go to three different colours) and once by constraint 3 (the shortest
#    expressible form is longer than the 96 pixels it draws). A predicted
#    surprise answered by a refusal is still an answer, and this is its fifth
#    round.
#
# 4. WHAT I DID NOT DO. I did not invent a goal to fill the hole the parser
#    made. The temptation was real: the bar is monotone and would compile.
#    I cannot tell filling from spending, so signing it would be a fiction
#    that costs the level rather than a round.

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
  Casing [segment: colour_class_6 ev: t0-t13 compress: 22]
  Cavity [segment: colour_class_0 ev: t0-t13 compress: 12]
  Rail [segment: colour_class_3 ev: t0-t13 compress: 8]
  Pip [segment: colour_class_1 ev: t0-t13 compress: 9]
  Stud [segment: colour_class_2 ev: t0-t13 compress: 12]
  Erased [segment: colour_class_4 ev: t0-t13 compress: 12]

events:
  event recolored(o, c)

# Eight rules, none edited this round because no transition was added. Six are
# the strip toggle: five ACTION3 blanks, one ACTION7 blank, five ACTION4
# restores, 132 cell-recolourings, every one correct. One is the seed. One is
# the march.
#
# READ THE MARCH'S ev TAG CAREFULLY. t8 and t11 are the transitions at which
# the WORLD converted (53,62) and (53,61). The rule fires one ACTION3 earlier,
# at t7 and t9. I cite the world's conversions because those are the events the
# rule exists to account for, and the phase error is written out in full in
# the_march_is_exactly_one_command_early_and_that_is_the_whole_of_its_error.
# Citing the firing times instead would hide the defect inside the tag.
#
# The twelve Stud instances: (32,13) (32,14) (33,13) (33,14) in the unselected
# slot bar, (38,17) (38,20) (39,19) (39,22) in the strip, (39,16) in the lower
# port, (53,61) (53,62) (53,63) in the meter.

rules:
  rule key3_blanks_the_strip_pips forall ?p in Pip [ev: t3,t7,t9,t11,t13 cov: 40/40]
    when act=key(3) and colored(?p, 1) and not colored(leftof(?p), 0) then recolored(?p, 4)

  rule key3_blanks_the_strip_studs forall ?p in Stud [ev: t3,t7,t9,t11,t13 cov: 20/20]
    when act=key(3) and colored(?p, 2) and not colored(leftof(?p), 0) and not colored(leftof(?p), 2) and not colored(rightof(?p), 2) then recolored(?p, 4)

  rule key7_blanks_the_strip_pips forall ?p in Pip [ev: t5 cov: 8/8]
    when act=key(7) and colored(?p, 1) and not colored(leftof(?p), 0) then recolored(?p, 4)

  rule key7_blanks_the_strip_studs forall ?p in Stud [ev: t5 cov: 4/4]
    when act=key(7) and colored(?p, 2) and not colored(leftof(?p), 0) and not colored(leftof(?p), 2) and not colored(rightof(?p), 2) then recolored(?p, 4)

  rule key4_restores_the_strip_pips forall ?p in Pip [ev: t4,t6,t8,t10,t12 cov: 40/40]
    when act=key(4) and colored(?p, 4) then recolored(?p, 1)

  rule key4_restores_the_strip_studs forall ?p in Stud [ev: t4,t6,t8,t10,t12 cov: 20/20]
    when act=key(4) and colored(?p, 4) then recolored(?p, 2)

  rule key4_seeds_the_meter_at_the_right_edge forall ?p in Stud [ev: t4 cov: 1/1]
    when act=key(4) and colored(?p, 2) and rightof(?p) = wall then recolored(?p, 3)

  rule key3_marches_the_meter_leftward forall ?p in Stud [ev: t8,t11 cov: 2/2]
    when act=key(3) and colored(?p, 2) and colored(rightof(?p), 3) then recolored(?p, 3)

laws:
  invariant casing_population count(Casing) = 22 [status: derived]
  invariant cavity_population count(Cavity) = 12 [status: derived]
  invariant rail_population count(Rail) = 8 [status: derived]
  invariant pip_population count(Pip) = 9 [status: derived]
  invariant stud_population count(Stud) = 12 [status: derived]
  invariant erased_population count(Erased) = 12 [status: derived]
  invariant every_dynamic_cell_has_an_owner count(Casing) + count(Cavity) + count(Rail) + count(Pip) + count(Stud) + count(Erased) = 75 [status: proven]

  theorem the_empty_goal_section_is_a_parse_error_and_silence_must_be_prose "the twelfth draft carried a bare `goal:` header with no statement under it, on purpose: I wanted the manual's ignorance about winning to be visible at the place where a goal would be, rather than inferable from an absence. The compiler refused the whole file at that line, so the device cost a full round of executable manual for zero information. The grammar's own answer is explicit and I misread it: no goal section at all is legal and compiles to is_goal -> False, so omission IS the way to say I do not know, and an empty header is a malformed goal rather than a silent one. The section is now absent and this theorem carries the intent. The general lesson is the one I keep having to relearn about this language: every place I try to make the manual EXPRESS a stance about itself, rather than state a fact about the world, the grammar has exactly one slot for it and that slot is `theorem`. Prose goes in prose. Nothing else in the file changed, so certify's numbers must be identical to last round's, and that identity is itself the check that this was a pure parse fix."
    [depends: no_goal_is_signed_and_that_is_deliberate  probe: passed]

  theorem no_goal_is_signed_and_that_is_deliberate "all fourteen states returned NOT_FINISHED and nothing in thirteen transitions indicates what finishing means. The live candidates are that a lane must be brought into some relation with the badge at its far end, that every slot in the column must be visited or solved, that the bar reaching one end ends the level, or that the objective lives in the rows I have never been shown. An absent goal compiles to is_goal implies False, which under-claims and costs a round; a wrong goal sends the searcher after a fiction and costs the level. The bar is the only monotone quantity in the record and is therefore the most tempting goal, and it is exactly the one I cannot sign because I cannot tell filling from spending: colour 3 is also what an unselected slot shows on its rails, which argues weakly for rest-or-complete over consumed, and weakly is not enough to invert every ranking in the playbook. So there is no goal section, and this theorem is where the silence is recorded."
    [depends: the_bar_runs_leftward_and_the_budget_is_measurable  probe: pending]

  theorem replay_is_open_loop_and_off_board_is_silent_and_one_number_settled_both "this was pending for three drafts and is now decided, by a measurement I wrote down before I took it. The four-way table: open-loop replay with colored(off_board, c) false scores 9 of 13; resync replay with off-board false scores 8; open-loop with off-board reading as a colour scores 8, because the march would then fire on (53,63) at transition 2 where the world did not tick; resync with off-board as a colour scores 7. The table is exhaustive over the two bits and 9 is reached by exactly one entry. Certify returned 9 of 13. So the checker does NOT hand the manual the world's state between transitions, and a guard testing a cell outside the grid is false rather than matching. Two consequences I will not forget. First, my replay errors compound rather than being wiped each step, which is why the march's one-command lead shows up as a run of divergences that closes rather than as a single wrong transition. Second, this is corroborated operationally by P-07, whose inert hash was byte-identical to the manual's own PREDICTION rather than to the world's answer -- the checker was replaying its own output, which is what open loop means. The two independent routes agree."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem the_first_divergence_is_the_selector_swap_and_i_refuse_to_change_the_manual_for_it "the surprise that called me back is the replay mismatch at transition 0: ACTION1, 96 cells, first cell (30,11) manual 5 world 6. I predicted this surprise, cell for cell, two drafts running, and I answer it with a refusal rather than an edit for the fifth round. The refusal rests on two independent grounds already proven and re-checked. Ground one, constraint 5: the divergence report itself contains five cells, (30,16) (31,16) (32,16) (33,16) (34,16), that are colour 5 in frame 0 with above 5, below 5, left 5, right 4 -- one indistinguishable guard reading -- and the world sends them to 6, 6, 1, 2, 6. No guard in this language separates them, so any rule set producing the swap contains two rules that both fire, which is forbidden. Ground two, constraint 3: the shortest expressible form is of order one landmark and one rule per repainted cell in each direction, which is longer than the 96 pixels it draws. A surprise that a manual predicted in advance, and whose cause the manual has already proven inexpressible, is not evidence that the manual is wrong; it is the price of a language, and the price is one transition in thirteen."
    [depends: the_swap_is_provably_inexpressible_here  probe: passed]

  theorem a_third_cadence_reading_fits_and_my_previous_draft_was_wrong_to_say_none_did "an earlier draft claimed exactly two readings fit the ticks at commands 4, 8 and 11 and that I had found no third. That was a claim about my own search, not about the world, and it was false. Reading F: the world returns a number of internal frames per command -- two for every command except the single ACTION7 at t5, which returned one -- and the meter ticks on the command during which the running total of internal frames crosses a multiple of seven. The running totals after each command are 2, 4, 6, 8, 9, 11, 13, 15, 17, 19, 21, 23, 25. Seven is crossed during t4, fourteen during t8, twenty-one at t11: three ticks, three crossings, and no crossing on any of the ten commands that did not tick. That is 3/3 with zero false positives, the same score as readings D and E. The lesson I take is not that F is right. It is that three ticks in thirteen commands cannot pin down a counter, that the space of counters fitting three points is large, and that I should stop presenting the cadence as a race between the fits I happen to have written down. What all three share, and what is proven independently of any of them, is that the meter advances on a schedule the visible frame does not determine."
    [depends: two_counter_readings_survive_and_they_disagree_about_which_keys_pay  probe: pending]

  theorem two_counter_readings_survive_and_they_disagree_about_which_keys_pay "ticks fell at commands 4, 8 and 11 of thirteen. Reading D counts commands that returned TWO frames and ticks on every third: the two-frame commands are t1 t2 t3 t4 t6 t7 t8 t9 t10 t11 t12 t13, ordinals 1 to 12, and the ticks fell on ordinals 4, 7 and 10. The single ACTION7 at t5 returned one frame and is skipped, which is why the raw command gaps read four then three. Reading E counts presses of ACTION3 or ACTION4 only and ticks on every third starting at the second: work presses t3 t4 t6 t7 t8 t9 t10 t11 t12 t13 are ordinals 1 to 10 and the ticks fell on 2, 5 and 8. Both need a counter modulo three; the grammar has none; neither is writable as a rule. D and E agree that the next strip key ticks. Reading F says it does not. So the disagreement is exploitable by any press at all."
    [depends: all_four_cadence_readings_are_dead_and_i_name_the_press_that_killed_each  probe: pending]

  theorem two_consecutive_non_strip_presses_separate_all_three_readings_and_end_where_they_started "pure arithmetic on data I already had. Take the current state, twenty-five internal frames spent, twelve two-frame commands, ten work presses. Press ACTION1 then ACTION2 -- a selector excursion that returns the widget to the bottom slot and returns the frame to where it started. Reading D: those are two-frame ordinals 13 and 14, and 13 is a multiple-of-three offset from 4, so D ticks on the FIRST press and not the second. Reading E: neither is a strip key, so E ticks on NEITHER. Reading F: the running total goes 25 to 27 to 29, and twenty-eight is crossed on the second press, so F ticks on the SECOND and not the first. Three readings, three distinct two-bit signatures, from two presses. If the free repeat-blank probe is spent first, the phases permute but the three signatures stay distinct, because D counts commands, E counts a subset of commands, and F counts frames, and no two of those three advance identically over a mixed sequence. The cost is honest and bounded: my manual is silent on the selector, so both transitions replay wrong at 96 cells each, taking replay from 9 of 13 to 9 of 15. I am willing to pay two transitions of a cost I have already proven irreducible in order to kill two of three readings of the only monotone quantity in the world."
    [depends: a_third_cadence_reading_fits_and_my_previous_draft_was_wrong_to_say_none_did  probe: pending]

  theorem all_four_cadence_readings_are_dead_and_i_name_the_press_that_killed_each "for three drafts I carried four readings of when the bar ticks, all 3/3 on the ticks at t4 and t8, and all four are refuted because each named a specific press. Reading A, a command counter of period four, required the next tick at command 12; it fell at 11 and 12 did nothing. Reading B, a parity on the restore key, required a tick at restore press five, t12; there was none, and the tick at t11 fell under ACTION3, a key B does not count. Reading C, the world remembers which key blanked, and C-prime, the tick rides on whatever follows an ACTION3, both required a tick at t10, which directly followed the ACTION3 at t9; t10 changed exactly twelve cells. I ranked C first because it explained why the world spends two key names on one strip function. That argument was good and the reading was still wrong: an explanation of an old puzzle is not evidence about a new fact. The ACTION3-versus-ACTION7 redundancy is unexplained and stays on the open list."
    [depends: the_world_is_not_a_function_of_the_visible_frame_and_it_is_now_witnessed_under_both_keys  probe: passed]

  theorem the_world_is_not_a_function_of_the_visible_frame_and_it_is_now_witnessed_under_both_keys "witnessed twice, once for each strip key, which removes the chance that it was an artefact of ACTION4. Witness one: s5 and s7 are the same 4096 cells, ACTION4 from s5 restored twelve cells, ACTION4 from s7 restored twelve cells and ticked (53,62). Witness two: s8 and s10 are the same 4096 cells -- strip shown, (53,63) and (53,62) colour 3, (53,61) colour 2 -- and ACTION3 from s8 blanked twelve cells while ACTION3 from s10 blanked twelve and ticked (53,61). The store corroborates the enumeration exactly: fourteen states, my reading collapses five pairs, s2=s0, s6=s4, s7=s5, s10=s8, s13=s11, and 14 minus 5 is 9 which is distinct_states. So the world carries at least one bit no guard of mine can read, constraint 5 forbids me writing both successors of an identical frame, and any planner treating a frame as a state is planning in the wrong space. This holds whichever of D, E and F is right, which is why it survives the cadence being underdetermined."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem the_march_moved_to_the_blanking_key_and_the_move_is_worth_three_transitions "the arm gave (53,61) an instance the moment it varied, and that changed what my old rule does on replay -- a rule I did not edit behaved differently because the level instance grew. With the march on key(4) it fires at t6 and t8 and the score is 7 of 13. On key(3) it fires at t7 and t9 and the score is 9 of 13, which is the number certify returned. With no march at all the score is 6 of 13 and the manual ends two cells wrong at (53,62) and (53,61) with no rule able ever to repair them. The march is therefore worth three replay transitions and two cells of present-state exactness. What I do not claim is that key(3) is the world's key for the meter: the world ticked twice under ACTION4 and once under ACTION3, so no key owns the meter, and the march is a shadow whose phase happens to align better on key(3) over this record. It is pixel-fitting with a measured price and I would trade it tomorrow for one expressible counter."
    [depends: two_counter_readings_survive_and_they_disagree_about_which_keys_pay  probe: passed]

  theorem the_march_is_exactly_one_command_early_and_that_is_the_whole_of_its_error "the world ticked (53,62) at t8 and (53,61) at t11; my march paints (53,62) at t7 and (53,61) at t9. Each firing is one ACTION3 ahead of the world's tick, and the manual then sits one cell wrong until the world catches up, at which point the frames coincide again -- at transition 7 for the first and transition 10 for the second. Now that open-loop replay is confirmed, this is exactly the shape the score should have: errors persist rather than being wiped, so a one-cell lead becomes a run of consecutive wrong transitions that closes when the world converts the same cell. The alternative phase, key(4), lags instead of leads and closes more slowly. Neither is a theory of the cadence."
    [depends: replay_is_open_loop_and_off_board_is_silent_and_one_number_settled_both  probe: passed]

  theorem the_manual_structurally_lags_the_bar_by_one_cell_forever "the arm instantiates only cells the board cannot explain, and the board is the cells that never vary. (53,60) has been colour 2 in all fourteen states, so it is board, no rule of mine can name it, and no guard changes that. My march can replay a tick already observed and can never predict a new one. From the current state I predict the next ACTION4 changes exactly twelve cells and (53,60) does not move, while D and E both say it does and F says it does not. Each cell the world converts hands me one more instance and one more cell of reach, so the lag is permanent but bounded at one cell, and the moment (53,60) varies the march inherits it."
    [depends: instance_anchoring_is_frame_zero_and_only_varying_cells_get_instances  probe: passed]

  theorem the_landmark_and_teleport_device_would_reach_the_next_bar_cell_and_i_refuse_it "the one device in the grammar that touches a cell no object occupies is the landmark, so I priced it properly rather than asserting the lag was inescapable. A landmark bar_frontier at arc-cell (53,60) is legal and can be READ by a guard. It cannot be PAINTED: the event table dispatches recolored on an object name, and the only events taking a landmark are jumped and teleported, which move an object to that cell. So the sole way to colour (53,60) is to teleport a Stud into it, and that is where the device fails on the world rather than on the grammar. Teleporting the (53,61) Stud vacates (53,61), which the world has already converted and which must stay colour 3 -- I would gain the frontier cell and destroy a cell behind it, and the bar's converted prefix would become a single travelling cell, contradicting three witnessed conversions that all persisted. Teleporting a strip Stud instead breaks the twelve-cell toggle that is 132 for 132. Beyond that, no transition in the record witnesses any position change at all: my whole event vocabulary is recolored, and cegis_miner independently refuses every track on the ground that the world does not narrate as one mover. So the device is expressible, cheap, and would buy one pre-registered cell at the cost of a rule contradicting the evidence, and I decline it."
    [depends: the_manual_structurally_lags_the_bar_by_one_cell_forever  probe: passed]

  theorem the_march_and_the_blanking_rule_cannot_both_fire_and_certify_has_now_adjudicated_every_pair "both are guarded on act=key(3) and colored(?p,2), so constraint 5 needs the remaining guards disjoint on every instance in every state. I enumerated by hand and certify then adjudicated all 42 pairs, fourteen states by the three actions my rules name, with fourteen of fourteen states reconstructed, zero clashes and zero step crashes. The hand enumeration and the machine agree. The reasons remain: meter stud (53,61) always has colour-2 (53,60) to its left so the blanking guard's not-colored-leftof-2 is false; (53,62) and (53,63) are likewise blocked by a colour-2 left neighbour in every state where they are themselves colour 2, because the bar converts strictly right to left and no state has a colour-3 cell left of a colour-2 one; strip studs have right neighbours only ever 1, 2 or 4 so the march's colored-rightof-3 is false; bar studs at rows 32-33 have right neighbours 2 or 5; port stud (39,16) has right neighbour 1 or 4. I state the scope exactly: passed over the fourteen states in the record, not over states never reached. The latent risk is a state with (53,61) colour 3 and (53,62) colour 2, which would admit both rules on (53,62); the monotone right-to-left order forbids it and that order is witnessed three times, not proven."
    [depends: the_bar_runs_leftward_and_the_budget_is_measurable  probe: passed]

  theorem frame_zero_is_reconstructed_exactly "frame 0 equals the frame I am shown with two edits: rows 38-39 by cols 17-22 hold the texture rather than colour 4, and (53,61), (53,62) and (53,63) all hold 2 rather than 3. The anatomy closes cell by cell: 22 Casing as the perimeter of rows 36-41 by cols 11-16 minus the two ports plus the 2x2 core at rows 38-39 cols 13-14; 12 Cavity as the 4x4 at rows 37-40 cols 12-15 minus that core; 8 Rail at rows 30-31 and 34-35 by cols 13-14; 4 Stud at rows 32-33 by cols 13-14; 8 Pip and 4 Stud in the lane B strip; 1 Pip at (38,16) and 1 Stud at (39,16) in the ports; 12 Erased as the lane A strip at rows 32-33 cols 17-22; 3 Stud in the meter. 22+12+8+9+12+12 = 75 = cells_needing_an_owner. The 24 remaining dynamic cells are the background of the unselected slot footprint, cols 11, 12, 15, 16 over rows 30-35, and 75+24 = 99 = dynamic_cells, and 4096-99 = 3997 = constant_cells. The dynamic set closes independently: the selector swap repaints 96 cells and the meter has ticked three times, and 96+3 = 99. Certify has returned 0 unexplained of 4096 on this reconstruction every round it has run."
    [probe: passed]

  theorem instance_anchoring_is_frame_zero_and_only_varying_cells_get_instances "instances are the cells of a declared colour that the board cannot explain, coloured as they are in frame 0; a cell constant across the whole record gets none. The arithmetic has been demonstrated repeatedly: 73 owners at 97 dynamic, 74 at 98, and 75 at 99, the difference each time exactly one bar cell and my Stud declaration moving by exactly one. Once it did something sharper than bookkeeping: the new instance at (53,61) changed the behaviour of a rule I did not edit, because the march suddenly had a twelfth Stud to land on. Level data is not inert with respect to the manual, and I will not again assume a rule's replay is stable across a store update. This round the store did not move and neither did the score, which is the same law read the other way."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem the_bar_runs_leftward_and_the_budget_is_measurable "three cells have converted, (53,63) then (53,62) then (53,61), so right-to-left is witnessed three times with no exception. Row 53 reads colour 2 from column 10 to column 60 in the window I am given and I have never been shown columns 0 to 9 of that row, so at least 51 and at most 61 cells remain. Thirteen commands have bought three ticks; all three surviving readings put the rate near one tick per three commands or per seven internal frames, so of order 150 to 190 commands of bar remain. Probing is cheap and the cheapness is a measured quantity. What I do not know is whether colour 3 means consumed or filled -- colour 3 is also what an unselected slot shows on its rails, which argues weakly for a resting or completed state -- and the two readings invert the sign of every ranking decision, so the playbook may not rank on it."
    [depends: the_manual_structurally_lags_the_bar_by_one_cell_forever  probe: pending]

  theorem a_repeat_of_a_blanking_key_has_still_never_been_tried_and_has_now_been_skipped_four_times "key(3) blanked a shown strip at t3, t7, t9, t11 and t13, key(7) blanked one at t5, key(4) restored a blanked one at t4, t6, t8, t10 and t12, twelve cells and cell for cell identical every time. Eleven presses, every blank from a shown strip and every restore from a blanked one, so hide-and-show and toggle-and-toggle remain indistinguishable. This has been my first-ranked probe for four rounds and has still not been pressed, and I record the skip rather than merely re-ranking it, because a probe that is always first and never taken is evidence about the loop I am in rather than about the world. My manual commits to complete inertness for a repeat of either blanking key from the current blanked state, since every strip cell is colour 4 and no blanking guard and no march guard can fire. If the strip returns, hide-and-show is dead. If the bar ticks with nothing else changing, the meter is a pure counter independent of the strip. And on the tick alone it separates F from D and E: D and E both say a strip press ticks now, F says the running total goes 25 to 27 and misses 28. Four answers from one press, and it is the only press in the space my manual predicts to be null, so it cannot spend the exactness the manual currently has."
    [depends: a_third_cadence_reading_fits_and_my_previous_draft_was_wrong_to_say_none_did  probe: pending]

  theorem the_extra_frame_count_is_the_only_visible_correlate_of_the_hidden_bit_and_two_readings_now_depend_on_it "every command in the record returned two frames except t5, the single ACTION7, which returned one; the store's cascade_lengths are exactly [1, 2]. Reading D uses this to skip t5 and get a clean period of three; reading F uses the totals directly. Both therefore rest on a single one-frame data point, and a second ACTION7 that returns one frame again is the cheapest way to make either sturdy, while one that returns two frames breaks both at once and leaves reading E alone. That is a two-way test on one press of a key already witnessed, which is unusually cheap for evidence that two thirds of my cadence space depends on."
    [depends: a_third_cadence_reading_fits_and_my_previous_draft_was_wrong_to_say_none_did  probe: pending]

  theorem the_cadence_is_inexpressible_and_all_three_loopholes_are_shut "a guard reads a cell colour, its four neighbour colours, off-board, and the action name. All three surviving readings need a counter -- modulo three on commands, modulo three on work presses, or modulo seven on internal frames -- and the grammar has no counter and no latch. Loophole one, an object at the background colour used as an invisible bit: unusable, because the value grammar exposes only color as a field so no guard can read present, and the 24 colour-5 cells the arm would instantiate all sit in the slot footprint. Loophole two, a second type declared at colour 2 to reach the next bar cell: unusable, because the arm finds objects by colour alone and would duplicate all twelve Studs. Loophole three, the landmark: a landmark can be read by a guard but cannot be recoloured, and the teleport that could reach it destroys the cell it leaves, as set out in the_landmark_and_teleport_device theorem. I also reconsidered using the strip as a phase register, since it is a two-cycle and the tick is a three-cycle, but blanks and restores have not alternated regularly against the counter so the two never combine into a readable six-cycle. The hidden bit stays prose."
    [depends: the_world_is_not_a_function_of_the_visible_frame_and_it_is_now_witnessed_under_both_keys  probe: passed]

  theorem the_swap_is_provably_inexpressible_here "the selector move relabels 96 cells and no set of rules in this language produces them. A guard sees a cell's own colour, its four neighbour colours, off-board, and the action name -- no coordinate, no row band, no distance. The witness is inside the divergence report certify returned again this round: (30,16), (31,16), (32,16), (33,16) and (34,16) are all colour 5 in frame 0 with above 5, below 5, left 5, right 4, one indistinguishable guard reading, and the world makes them 6, 6, 1, 2, 6. Three answers to one question. A second pair kills colour as a discriminator: (30,13) is colour 3 and becomes 6 while (32,13) is colour 2 in an equally uniform bar neighbourhood and also becomes 6. Constraint 5 forbids two rules that both fire, so the swap does not go in the manual and the transition-0 mismatch is a cost I accept."
    [depends: the_panel_is_a_column_of_slots  probe: passed]

  theorem the_swap_also_fails_the_compression_test "grant every expressibility obstacle removed and free reading of position. The swap still does not belong. It repaints 96 cells whose new colours follow no local law, because the widget is teleported six rows and no event in the vocabulary does that -- moved is one cell, jumped-over is two, jumped-to-a-landmark needs a landmark and a rule per instance. The shortest form I can construct is of order one landmark and one rule per repainted cell in both directions, longer than the 96 pixels it explains. Constraint 3 refuses it independently of constraint 5. Two independent refusals, which is why I expect never to write the swap rather than merely not to have written it yet."
    [depends: the_swap_is_provably_inexpressible_here  probe: passed]

  theorem a_background_object_would_own_exactly_the_swap_footprint_and_i_still_do_not_declare_it "an object declared at arc-colour 5 with arc-instances all would be placed on the colour-5 cells the board cannot explain, and those number exactly 99 minus 75 = 24: cols 11, 12, 15, 16 over rows 30-35, the unselected slot footprint, not one cell more. The declaration is cheap and surgical. I still do not declare it, because it would explain no pixel the board does not already draw correctly and would enable no rule I can write, which is constraint 3 refusing it on its own terms. If a device ever appears that lets a guard read position, this is the first declaration to add."
    [depends: the_swap_is_provably_inexpressible_here  probe: pending]

  theorem the_restore_and_blank_rules_are_conditioned_on_a_selection_the_manual_cannot_represent "the restore rules guard on colour 4 alone and the blanking rules on one to three neighbour tests. Both are correct on all eleven blank-or-restore presses, because every press was made with the bottom slot selected, where the only colour-4 Pip and Stud instances in existence are the twelve blanked lane B cells. They would be wrong the moment slot A is selected: lane A strip cells become texture while lane B strip cells become arena fill of colour 4, and the instances do not move with the widget because I only ever recolour. My manual never reaches that state, being silent on the selector, so this costs zero transitions and certify cannot see it. It is written here because a searcher planning through a selector move would be misled by rules that score 132 of 132 -- and because the excursion I rank second walks straight into it. The mitigation is explicit and I state it as a condition on the probe: press no strip key while the upper slot is selected. An out-and-back pair of selector presses satisfies that by construction."
    [depends: the_swap_is_provably_inexpressible_here  probe: pending]

  theorem the_strip_is_one_global_diagonal_texture "one rule covers every strip cell I have seen: a strip cell is colour 2 when (row + col) mod 3 = 1 and colour 1 otherwise. Frame 0 row 38 cols 16-22 reads 1 2 1 1 2 1 1 and row 39 reads 2 1 1 2 1 1 2, a period-3 run offset by one column; the divergence report gives lane A row 32 cols 16-22 as the world drew it at t1, 1 2 1 1 2 1 1, and rows 32 and 38 agree because 6 divides by 3. The two port cells fit the same formula, which is an unforced success. So the two strips are two windows onto one texture, which is why a restore rebuilds twelve cells exactly and why five restores rebuilt them identically. Untested prediction: select slot A and row 33 cols 17-22 reads 1 1 2 1 1 2. No rule needs this, since each instance remembers its frame 0 colour, so the concept buys understanding rather than symbols and stays out of the word table."
    [depends: frame_zero_is_reconstructed_exactly  probe: pending]

  theorem the_seed_column_is_never_erased "blanking takes cols 17-22 of the selected lane and stops there, six times now, twelve cells every time. (38,16)=1 and (39,16)=2 sit on the widget right edge, are Pip and Stud instances, and have never changed under any blank; the guards say why, since the left neighbour of each is a colour-0 cavity cell. They are the only cells of the texture that survive hiding and they are exactly the two needed to phase a period-3 run. The rival explanation is that col 16 is where the 6x6 widget ends and the survival is coincidence; six blanks do not separate them."
    [depends: the_strip_is_one_global_diagonal_texture  probe: pending]

  theorem the_panel_is_a_column_of_slots "the divergence report gives the world's t1 rows 30, 31, 32 at cols 11-16 as 6 6 6 6 6 6 / 6 0 0 0 0 6 / 6 0 6 6 0 1, and frame 0 rows 36, 37, 38 at those columns read identically -- eighteen cells, six rows apart. Rows 42 to 52 are uniform background, so rows 36-41 is the bottom slot and rows 30-35 the one above it. ACTION1 moved selection from the bottom slot to the upper one and ACTION2 moved it back, one witness each for up and down, no wrap needed. Whether a third slot exists above is untested: (29,13) and (29,14) hold colour 3 and never vary, which is what a slot at rows 24-29 would show on its bottom rail, but board cells prove nothing about slots never selected."
    [depends: frame_zero_is_reconstructed_exactly  probe: pending]

  theorem the_badge_is_lane_aligned_and_the_matching_reading_stays_downgraded "the arena is colour 4 over cols 17-46, bounded on the right by background from col 47. The only thing in it that is neither strip nor fill is a 4x4 block of colour 14 at rows 31-34 by cols 42-45. Those are exactly the rows an upper-slot cavity occupies within its six-row band, so the badge belongs to the lane of the slot at rows 30-35, and the bottom slot's lane has nothing at cols 42-45. The tempting reading is that it is a target the lane texture must be made to match, but the strip is 2 by 6 and the badge is 4 by 4 of one uniform colour, so shape refutes it. The surviving readings are that it marks which slot carries the task, that it is a destination, or that it is a picture of a completed cavity, the widget cavity being also 4x4 with a 2x2 core removed. Thirteen transitions and none of them bear on any of the three; colour 14 appears nowhere else in the frame. Note that the selector excursion I rank second is also the only probe that has ever put the badge's own lane on screen as the selected one."
    [depends: the_panel_is_a_column_of_slots  probe: pending]

  theorem colour_classes_are_not_the_worlds_objects_and_i_admit_the_cost "the six declared types are colour classes, not things. Stud alone spans the unselected slot bar, a port, four strip cells and three meter cells -- four unrelated roles in one type, and the count grows whenever the bar converts. Casing and Cavity together are one widget. The world segments by widget and the arm segments by colour, and the arm wins because the arm draws the frame. The gain is measured: six declarations own all 75 cells that need an owner against 75 pixels written out, with 0 unexplained confirmed every round it has been checked. The cost is measured too: no rule can name the strip, so every blanking rule carves it out of its colour class by neighbour tests, and the march is kept off eleven Studs by a right-neighbour test that is a fact about the bar's geometry rather than about the meter. Those guards are pixel-fitting in a costume, and the march is the worst offender because its guard is an accident of what has already ticked."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem i_have_never_been_shown_rows_0_to_28 "colours_seen lists 8 and 9 and neither appears anywhere in the window I am given, rows 29-54 by cols 10-63. They live in the 3997 constant cells I have never looked at -- above row 29, left of col 10, or below row 54. That region is board by definition and my manual draws it correctly by doing nothing, so responsibility stays at 0 unexplained; but it is where a title, target, score or instruction would live, and the likeliest home of whatever finishing means and of whether the bar is a budget or a score. Thirteen commands have not made one cell of it vary, which is mild evidence that it is decoration, but only mild, since ten of the thirteen were the same two keys."
    [depends: no_goal_is_signed_and_that_is_deliberate  probe: pending]

  theorem two_keys_have_never_been_pressed "ACTION1, 2, 3, 4 and 7 have been pressed; key(5) and key(6) have not, after fourteen commands. Of order 150 to 190 commands of bar remain, so two presses are affordable and are the cheapest untried source of a genuinely new frame. If either is a click carrying coordinates, this guard language cannot express it and the finding is recorded as prose rather than as a rule. Each press also reads its own returned frame count, which readings D and F make into a direct measurement of the counter, and each is a non-strip press so the D-E-F signature analysis applies to it exactly as it does to a selector press."
    [depends: two_consecutive_non_strip_presses_separate_all_three_readings_and_end_where_they_started  probe: pending]

  theorem what_the_engines_offered_and_why_none_of_it_was_taken "unchanged again because the engines returned unchanged output on an unchanged store, and I re-read rather than re-cited. mdl_segmenter returns negative gain on both variants, -2989 bits at 4 tracks and -25963 at 69, with tracks that are 440-cell blobs of shape 13x36 and colour null -- the panel and the arena fused by connected_components(4), a fact about the operator rather than the world. Its obj1 is 108 cells of shape 2 by 54 present in all fourteen frames, which is rows 53 and 54 clipped to the window, the meter bar and the fill row beneath it, fused because colour 2 and colour 4 touch vertically and background 5 does not separate them; it corroborates that the bar is one object continuing left of column 10 where I have never seen it. cegis_miner refuses all four tracks because its precondition is exactly one move event per transition, and its verdict that the world does not narrate as one mover agrees with my event vocabulary of recolored alone and is the outside evidence I leaned on when refusing the teleport device. zero_space calls its own evidence THIN -- 13 transitions constraining rank 5 of 693 features, null space of dimension 688 -- and its single global law spans 99 dynamic cells at once, which is what a 688-dimensional null space produces rather than what a conservation law looks like. Its cell list, ninety-six slot cells plus (53,61) (53,62) (53,63), is exactly my dynamic set and is the one thing in the stream I use."
    [probe: pending]

  theorem what_this_draft_pre_registers "certify first, and since the only edit is the removal of a malformed empty goal section, every number must be identical to the last successful compile: replay 9 of 13, first divergence at transition 0 under ACTION1, 96 cells wrong, first cell (30,11) manual 5 world 6; responsibility 0 unexplained of 4096; unambiguous 0 clashes over 14 states by 3 actions, 42 pairs, 42 nominal, 0 step crashes. If any of those moves, the empty goal header was doing something I did not know about, and I would rather learn that than be right. Now the world, and I pre-register all three readings so any continuation can be scored. Present position: 25 internal frames spent, 12 two-frame commands, 10 work presses. Probe one, repeat a blanking key from the blanked state: my manual says not one cell changes; D says the bar ticks, E says the bar ticks, F says it does not; if the strip returns, hide-and-show is dead; if the bar ticks with nothing else, the meter is a pure counter; and the returned frame count is itself a reading. Probe two, ACTION1 then ACTION2 with no strip key between: D ticks on the first press only, E ticks on neither, F ticks on the second only -- three distinct signatures, and the pair ends at the frame it started from. Probe three, ACTION4: my manual says exactly twelve cells and does not move (53,60); D and E say thirteen including (53,60); F says twelve. Probe four, key(5) or key(6): anything at all is new, and the returned frame count is read regardless."
    [depends: replay_is_open_loop_and_off_board_is_silent_and_one_number_settled_both  probe: pending]
```

## The playbook as it stands

```
# playbook.dsl -- thirteenth draft.
#
# WHAT MOVED, AND WHY.
#
# 1. NOTHING IN THIS FILE MOVED, AND THE REASON IS NOT INERTIA. This round was
#    spent on a compile failure in theory.dsl -- an empty `goal:` header, which
#    this grammar does not accept -- and no world command was pressed. No new
#    frame means no new ordering evidence, so every order, prefer, heuristic
#    and prune below is supported by exactly the evidence it was supported by
#    last round. Re-ranking on no data would be inventing a preference, and an
#    invented playbook is worse than a stale one.
#
# 2. THE FIRST ORDER HAS NOW BEEN SKIPPED FOUR ROUNDS. Repeating a blanking key
#    from the blanked state is still first and still unpressed. It is the only
#    press the manual predicts to be null, so it cannot spend the manual's
#    present exactness, and it separates reading F from D and E on the tick
#    alone on top of the four answers it already bought. Four skips of a
#    first-ranked free probe is a fact about the loop, not about the ranking,
#    and it is recorded in the manual as such.
#
# 3. THE SELECTOR EXCURSION STAYS SECOND. Two consecutive non-strip presses
#    give three DISTINCT tick signatures across D, E and F, so one out-and-back
#    pair kills two of three readings of the only monotone quantity in the
#    world. Its known danger -- the state where my blank and restore rules are
#    provably wrong -- is discharged by a condition rather than by avoidance:
#    press no strip key while the upper slot is selected. An out-and-back pair
#    satisfies that by construction, which is why the order names the pair.
#
# 4. STILL NO GOAL, AND NOW SAID PROPERLY. The manual no longer carries an
#    empty goal section; the silence lives in a theorem. Nothing here is a
#    plan. These are orders of interrogation.

order   repeat_a_blanking_key_in_the_blanked_state_for_four_answers_at_once  [proof: lean]
order   press_two_consecutive_non_strip_keys_to_separate_all_three_counter_readings  [proof: lean]
order   take_the_selector_excursion_as_a_pair_and_press_no_strip_key_inside_it  [proof: lean]
order   press_the_two_never_pressed_keys_while_the_bar_is_still_long  [proof: lean]
order   retest_the_key_that_once_returned_a_single_frame_since_two_readings_rest_on_it  [proof: lean]
order   vary_the_order_of_the_two_blanking_keys_across_a_restore  [proof: lean]
order   bound_the_selector_by_pushing_the_cursor_past_the_slots_already_drawn  [proof: lean]
order   read_the_strip_row_never_displayed_to_score_the_texture_rule  [proof: lean]
order   look_at_the_badge_lane_while_its_own_slot_is_the_selected_one  [proof: lean]
order   make_some_cell_outside_the_observed_window_vary  [proof: lean]
order   probe_the_unknown_before_planning_while_no_goal_is_known  [proof: lean]
order   read_every_bar_cell_and_the_returned_frame_count_after_every_command  [proof: lean]

prefer  an_action_the_three_counter_readings_give_different_answers_for  [ev: 3 readings, each 3/3 on 3 ticks]
prefer  a_pair_of_actions_that_separates_more_readings_than_either_alone  [ev: 2 presses, 3 signatures]
prefer  an_action_the_manual_has_pre_registered_a_null_frame_for  [ev: 0/13 transitions tested it]
prefer  an_action_that_answers_more_than_one_open_question_at_once  [ev: 1 press separates 4]
prefer  an_action_whose_returned_frame_count_the_readings_disagree_about  [ev: 1/13 commands returned one frame]
prefer  a_key_never_pressed_over_a_key_whose_effect_is_already_witnessed  [ev: 2/7 keys unpressed]
prefer  an_action_that_varies_the_order_of_two_keys_already_witnessed_singly  [ev: 11/13 presses were blank_then_restore]
prefer  a_slot_never_selected_over_one_already_drawn_twice  [ev: 2 slots seen of a column]
prefer  a_press_that_makes_a_board_cell_vary_over_one_that_repeats  [ev: 99/4096 cells ever varied]
prefer  repeating_a_key_from_the_state_that_key_itself_produced  [ev: 0/13 transitions test it]
prefer  a_probe_launched_from_a_state_the_manual_reconstructs_exactly  [ev: 4096/4096 cells right now]
prefer  an_excursion_that_returns_the_frame_to_where_it_started  [ev: 1/13 commands undid another]

heuristic bar_cells_still_unconverted  [admissible: lean]
heuristic counter_readings_still_alive  [admissible: lean]
heuristic presses_needed_to_separate_the_surviving_counter_readings  [admissible: lean]
heuristic slots_in_the_column_never_yet_selected  [admissible: lean]
heuristic rows_of_the_frame_never_yet_displayed  [admissible: lean]
heuristic keys_whose_effect_rests_on_a_single_witness  [admissible: lean]
heuristic lanes_whose_badge_has_never_been_addressed  [admissible: lean]

prune   plan_that_assumes_two_equal_frames_are_the_same_state => dead  [proof: lean]
prune   plan_that_assumes_the_checker_resyncs_the_manual_between_transitions => dead  [proof: lean]
prune   plan_that_ties_the_bar_tick_to_one_particular_key => dead  [proof: lean]
prune   plan_that_prices_a_bar_cell_at_one_per_restore_press => dead  [proof: lean]
prune   plan_that_counts_the_bar_on_raw_command_number_alone => dead  [proof: lean]
prune   plan_that_treats_the_cadence_as_a_race_between_two_named_readings => dead  [proof: lean]
prune   plan_that_asks_the_manual_to_tick_a_bar_cell_never_yet_witnessed => dead  [proof: lean]
prune   plan_that_needs_a_cell_that_has_never_varied_to_change => dead  [proof: lean]
prune   plan_that_teleports_an_object_out_of_a_cell_the_bar_has_converted => dead  [proof: lean]
prune   plan_that_rests_on_the_bar_meaning_being_known => dead  [proof: lean]
prune   plan_that_spends_the_manuals_present_exactness_and_returns_no_new_frame => dead  [proof: lean]
prune   plan_that_relies_on_the_manual_drawing_the_selector => dead  [proof: lean]
prune   plan_that_presses_a_strip_key_while_the_upper_slot_is_selected => dead  [proof: lean]
prune   plan_that_treats_the_two_blanking_keys_as_interchangeable => dead  [proof: lean]
prune   plan_whose_rules_are_longer_than_the_pixels_they_draw => dead  [proof: lean]
prune   plan_that_cites_a_transition_absent_from_the_current_record => dead  [proof: lean]
prune   plan_that_spends_a_round_on_a_manual_that_does_not_compile => dead  [proof: lean]
prune   action_whose_successor_every_live_reading_agrees_on => dead  [proof: lean]
prune   undoing_a_selector_move_that_just_revealed_something => dead  [proof: lean]
prune   bar_consumed and not goal => dead  [proof: lean]
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

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted '1317da5b367d300a', the world answered '3281b51b4c1aa929'

```json
{
 "action": 4,
 "observed": "3281b51b4c1aa929",
 "predictions": {
  "inert": "b278887e087d3593",
  "manual": "1317da5b367d300a",
  "without_key3_blanks_the_strip_pips": "1317da5b367d300a",
  "without_key3_blanks_the_strip_studs": "1317da5b367d300a",
  "without_key3_marches_the_meter_leftward": "1317da5b367d300a",
  "without_key4_restores_the_strip_pips": "b278887e087d3593",
  "without_key4_restores_the_strip_studs": "b278887e087d3593",
  "without_key4_seeds_the_meter_at_the_right_edge": "1317da5b367d300a",
  "without_key7_blanks_the_strip_pips": "1317da5b367d300a",
  "without_key7_blanks_the_strip_studs": "1317da5b367d300a"
 },
 "probe_id": "P-09"
}
```

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted 'b278887e087d3593', the world answered 'd2c8aa05e38a2da7'

```json
{
 "action": 3,
 "observed": "d2c8aa05e38a2da7",
 "predictions": {
  "inert": "1317da5b367d300a",
  "manual": "b278887e087d3593",
  "without_key3_blanks_the_strip_pips": "1317da5b367d300a",
  "without_key3_blanks_the_strip_studs": "1317da5b367d300a",
  "without_key3_marches_the_meter_leftward": "b278887e087d3593",
  "without_key4_restores_the_strip_pips": "b278887e087d3593",
  "without_key4_restores_the_strip_studs": "b278887e087d3593",
  "without_key4_seeds_the_meter_at_the_right_edge": "b278887e087d3593",
  "without_key7_blanks_the_strip_pips": "b278887e087d3593",
  "without_key7_blanks_the_strip_studs": "b278887e087d3593"
 },
 "probe_id": "P-10"
}
```

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted '1317da5b367d300a', the world answered '3281b51b4c1aa929'

```json
{
 "action": 4,
 "observed": "3281b51b4c1aa929",
 "predictions": {
  "inert": "b278887e087d3593",
  "manual": "1317da5b367d300a",
  "without_key3_blanks_the_strip_pips": "1317da5b367d300a",
  "without_key3_blanks_the_strip_studs": "1317da5b367d300a",
  "without_key3_marches_the_meter_leftward": "1317da5b367d300a",
  "without_key4_restores_the_strip_pips": "b278887e087d3593",
  "without_key4_restores_the_strip_studs": "b278887e087d3593",
  "without_key4_seeds_the_meter_at_the_right_edge": "1317da5b367d300a",
  "without_key7_blanks_the_strip_pips": "1317da5b367d300a",
  "without_key7_blanks_the_strip_studs": "1317da5b367d300a"
 },
 "probe_id": "P-11"
}
```

### probe_refutation (empirical family -> theory.dsl)

THE MANUAL WAS WRONG: it predicted 'b278887e087d3593', the world answered 'febfe034e90989ad'

```json
{
 "action": 3,
 "observed": "febfe034e90989ad",
 "predictions": {
  "inert": "1317da5b367d300a",
  "manual": "b278887e087d3593",
  "without_key3_blanks_the_strip_pips": "1317da5b367d300a",
  "without_key3_blanks_the_strip_studs": "1317da5b367d300a",
  "without_key3_marches_the_meter_leftward": "b278887e087d3593",
  "without_key4_restores_the_strip_pips": "b278887e087d3593",
  "without_key4_restores_the_strip_studs": "b278887e087d3593",
  "without_key4_seeds_the_meter_at_the_right_edge": "b278887e087d3593",
  "without_key7_blanks_the_strip_pips": "b278887e087d3593",
  "without_key7_blanks_the_strip_studs": "b278887e087d3593"
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
  "detail": "9/13 transitions replay exactly",
  "matched": 9,
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
# theory.dsl -- FOURTEENTH DRAFT.
#
# 0. FOUR COMMANDS WERE FINALLY PRESSED AND THEY PAID FOR THEMSELVES.
#    The store moved for the first time in three rounds: steps 14 -> 18,
#    states 14 -> 18, distinct_states 9 -> 12, dynamic_cells 99 -> 101,
#    cells_needing_an_owner 75 -> 77, constant_cells 3997 -> 3995. The new
#    commands are t14 ACTION4, t15 ACTION3, t16 ACTION4, t17 ACTION3, and the
#    meter converted twice more: (53,60) at t14 and (53,59) at t17.
#
# 1. ONE READING OF THE CADENCE DIED AND I NAME THE PRESS THAT KILLED IT.
#    Reading F -- internal-frame totals crossing a multiple of seven --
#    required the fourth tick at t15, because the running total goes 25 to 27
#    at t14 and only crosses 28 at t15. The world ticked at t14. F is dead.
#    Readings D and E both went 5 for 5. A fourth reading I had never written
#    down, E'' (count EVERY strip-affecting press including the ACTION7), is
#    also dead: its tick ordinals are 2, 6, 9, 12, 15 and 2 is not congruent
#    to 6 modulo three. So both survivors agree that the ACTION7 at t5 does
#    not count, and they disagree only about WHY.
#
# 2. THE FOUR PROBE REFUTATIONS ARE ONE DEFECT AND THE HASHES DECODE THE
#    WORLD. P-09 to P-12 are all the frontier blindness, and the four distinct
#    hashes they name let me read the world's state space off the record; that
#    decoding is the round's real gain and it is written out in full below.
#
# 3. WHAT I EXPECT TO LOSE. The march now has instances at (53,59) and
#    (53,60) that it did not have last round, so on replay it runs FOUR
#    commands ahead of the world instead of one, and I pre-register replay
#    falling from 9/13 to 7/17. I keep it anyway and I say exactly what for.
#
# 4. THE BAR LOOKS MORE LIKE A CLOCK THAN A SCORE NOW, AND THAT IS AN UPDATE
#    ABOUT THE PLAYBOOK RATHER THAN A GOAL. Fourteen work presses accomplished
#    nothing whatever -- the strip was toggled back to where it started every
#    time -- and the meter advanced five times regardless. Meters that advance
#    for no achievement are clocks. Still not enough to sign a goal.

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
  Casing [segment: colour_class_6 ev: t0-t17 compress: 22]
  Cavity [segment: colour_class_0 ev: t0-t17 compress: 12]
  Rail [segment: colour_class_3 ev: t0-t17 compress: 8]
  Pip [segment: colour_class_1 ev: t0-t17 compress: 9]
  Stud [segment: colour_class_2 ev: t0-t17 compress: 14]
  Erased [segment: colour_class_4 ev: t0-t17 compress: 12]

events:
  event recolored(o, c)

# Eight rules. Six are the strip toggle: seven ACTION3 blanks, one ACTION7
# blank, seven ACTION4 restores, 12 cells every time, 192 cell-recolourings,
# every one correct. One is the seed. One is the march.
#
# The Stud type now has FOURTEEN instances, two more than last round, because
# (53,59) and (53,60) varied for the first time this round and the arm gives
# an instance to every cell of a declared colour that the board cannot
# explain. They are: (32,13) (32,14) (33,13) (33,14) in the unselected slot
# bar, (38,17) (38,20) (39,19) (39,22) in the strip, (39,16) in the lower
# port, and (53,59) (53,60) (53,61) (53,62) (53,63) in the meter.
#
# THE MARCH'S ev TAG STILL CITES THE WORLD'S CONVERSIONS, NOT ITS OWN
# FIRINGS. The world converted (53,62) at t8, (53,61) at t11, (53,60) at t14
# and (53,59) at t17: four conversions, and the march is the only rule that
# accounts for any of them. It FIRES at t7, t9, t11 and t13. Citing the
# firings would hide a four-command phase error inside a tag; the error is
# written out at full length in the_march_now_leads_by_four_commands theorem.

rules:
  rule key3_blanks_the_strip_pips forall ?p in Pip [ev: t3,t7,t9,t11,t13,t15,t17 cov: 56/56]
    when act=key(3) and colored(?p, 1) and not colored(leftof(?p), 0) then recolored(?p, 4)

  rule key3_blanks_the_strip_studs forall ?p in Stud [ev: t3,t7,t9,t11,t13,t15,t17 cov: 28/28]
    when act=key(3) and colored(?p, 2) and not colored(leftof(?p), 0) and not colored(leftof(?p), 2) and not colored(rightof(?p), 2) then recolored(?p, 4)

  rule key7_blanks_the_strip_pips forall ?p in Pip [ev: t5 cov: 8/8]
    when act=key(7) and colored(?p, 1) and not colored(leftof(?p), 0) then recolored(?p, 4)

  rule key7_blanks_the_strip_studs forall ?p in Stud [ev: t5 cov: 4/4]
    when act=key(7) and colored(?p, 2) and not colored(leftof(?p), 0) and not colored(leftof(?p), 2) and not colored(rightof(?p), 2) then recolored(?p, 4)

  rule key4_restores_the_strip_pips forall ?p in Pip [ev: t4,t6,t8,t10,t12,t14,t16 cov: 56/56]
    when act=key(4) and colored(?p, 4) then recolored(?p, 1)

  rule key4_restores_the_strip_studs forall ?p in Stud [ev: t4,t6,t8,t10,t12,t14,t16 cov: 28/28]
    when act=key(4) and colored(?p, 4) then recolored(?p, 2)

  rule key4_seeds_the_meter_at_the_right_edge forall ?p in Stud [ev: t4 cov: 1/1]
    when act=key(4) and colored(?p, 2) and rightof(?p) = wall then recolored(?p, 3)

  rule key3_marches_the_meter_leftward forall ?p in Stud [ev: t8,t11,t14,t17 cov: 4/4]
    when act=key(3) and colored(?p, 2) and colored(rightof(?p), 3) then recolored(?p, 3)

laws:
  invariant casing_population count(Casing) = 22 [status: derived]
  invariant cavity_population count(Cavity) = 12 [status: derived]
  invariant rail_population count(Rail) = 8 [status: derived]
  invariant pip_population count(Pip) = 9 [status: derived]
  invariant stud_population count(Stud) = 14 [status: derived]
  invariant erased_population count(Erased) = 12 [status: derived]
  invariant every_dynamic_cell_has_an_owner count(Casing) + count(Cavity) + count(Rail) + count(Pip) + count(Stud) + count(Erased) = 77 [status: proven]

  theorem the_four_probe_hashes_decode_the_entire_state_space_and_that_is_this_rounds_real_gain "P-09 through P-12 are four refutations of the same defect, and taken together they hand me something no single frame does: the world's state lattice, read off four sixteen-hex-digit strings. Assign them by which press they follow. 1317da5b367d300a is the manual's answer to ACTION4 and the manual's starting point before ACTION3, so it is a strip-SHOWN state; b278887e087d3593 is the mirror, a strip-BLANKED state; and both of them carry the manual's bar, converted through (53,61) only. The world's answers are 3281b51b4c1aa929 after ACTION4 at BOTH t14 and t16 -- the same hash twice, which is the world telling me s14 and s16 are the identical frame -- and d2c8aa05e38a2da7 after ACTION3 at t15 against febfe034e90989ad after ACTION3 at t17, two different hashes because the world converted (53,59) in between. So a state of this world is a PRODUCT: strip in shown-or-blanked, times bar length, times which slot the selector holds. I can now check that against the store without a single new press. Enumerate: s0, s1 the swapped slot, s3 blanked with no bar, s4 shown with one, s5 blanked with one, s8 shown with two, s9 blanked with two, s11 blanked with three, s12 shown with three, s14 shown with four, s15 blanked with four, s17 blanked with five. Twelve, and distinct_states is 12. The collapses are s2=s0, s6=s4, s7=s5, s10=s8, s13=s11, s16=s14 -- six of them, and 18 minus 6 is 12. The lattice closes exactly. The consequence I care about most is in the next theorem: this product has no room in it for winning."
    [depends: the_world_is_not_a_function_of_the_visible_frame_and_it_is_now_witnessed_under_both_keys  probe: passed]

  theorem the_keys_i_have_pressed_generate_a_closed_space_that_cannot_contain_the_ending "eighteen states, every one NOT_FINISHED, and the previous theorem shows why that is not bad luck. Keys 1, 2, 3, 4 and 7 move the world only within a product of three coordinates: the strip is shown or blanked, the selector is in one of two slots, and the meter has converted k cells. The first two are involutions -- I have toggled them eleven and two times respectively and always landed back where I started -- and the third is monotone and moves on a schedule no key controls. So the only thing eighteen commands have actually ACHIEVED is spending meter. If the ending lives anywhere it lives outside this product, which means it needs either a key I have never pressed or a state of the panel I have never built. That is an argument from the shape of the reachable set rather than from any single frame, and it is the reason the playbook now ranks the two unpressed keys ahead of everything else, including the cadence question I have been chasing for five drafts. I state the weakness plainly: the argument assumes the product is complete, and it is complete only over the eighteen states I have, which is exactly the kind of assumption a new key exists to break."
    [depends: the_four_probe_hashes_decode_the_entire_state_space_and_that_is_this_rounds_real_gain  probe: pending]

  theorem reading_F_is_dead_and_the_press_that_killed_it_was_t14 "reading F said the meter ticks on the command during which the running total of internal frames crosses a multiple of seven. It was 3 of 3 when I wrote it and I gave it equal standing with D and E, deliberately, because three ticks cannot pin a counter. Four commands later it is refuted and the refutation is arithmetic I pre-registered. Totals after each command: 2, 4, 6, 8, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31, 33. Seven is crossed during t4, fourteen during t8, twenty-one is reached at t11 -- three ticks, three crossings. Twenty-eight is crossed during t15, because t14 takes the total from 25 only to 27. The world ticked at t14 and did not tick at t15. F predicted the wrong command and dies on it. I also killed a reading I had never bothered to write down, E'' -- count every press that touches the strip, INCLUDING the ACTION7 at t5. Its tick ordinals are 2, 6, 9, 12, 15, and 2 against 6 is a gap of four where every later gap is three. So the exclusion of t5 is not optional under any surviving reading: whatever the counter counts, it did not count that command."
    [depends: a_third_cadence_reading_fits_and_my_previous_draft_was_wrong_to_say_none_did  probe: passed]

  theorem readings_D_and_E_are_both_five_for_five_and_one_selector_excursion_separates_them "ticks fell at commands 4, 8, 11, 14 and 17 of seventeen. Reading D counts commands that returned TWO frames and ticks on every third: the two-frame ordinals of the ticking commands are 4, 7, 10, 13 and 16, an exact arithmetic progression of step three with no false positive among the eleven commands that did not tick. Reading E counts presses of ACTION3 or ACTION4 only and ticks on every third starting at the second: the work-press ordinals of the ticking commands are 2, 5, 8, 11 and 14, again exact, again no false positive. Five for five each. They cannot be separated by any run of ACTION3 and ACTION4, because over such a run every command is both a two-frame command and a work press and the two counters advance in lockstep -- which is precisely what the last fourteen commands were, and precisely why fourteen commands of evidence bought no discrimination. A command that is two-frame but NOT a strip key separates them in one press. Concretely, from the present position of 16 two-frame commands and 14 work presses: press ACTION1, then ACTION2, then any strip key. D counts all three, reaches two-frame ordinal 19, and ticks on the strip key; E counts only the strip key, reaches work ordinal 15, and does not tick. One bit, three presses, and the pair of selector presses returns the frame to where it started so the strip key is pressed at home."
    [depends: reading_F_is_dead_and_the_press_that_killed_it_was_t14  probe: pending]

  theorem the_meter_advances_for_no_achievement_and_that_tilts_it_toward_clock "for five drafts I have refused to say whether colour 3 on the bar means consumed or filled, on the ground that the two invert every ranking and I could not tell them apart. This round tilts it, and I want to record the tilt without overstating it. Fourteen work presses have now been spent, and what they accomplished is nothing: the strip was blanked and restored and blanked and restored, and it stands blanked now exactly as it stood at t3. Not one of the eighteen states does anything a designer would call progress. The meter advanced five times through all of it, on a schedule keyed to the number of presses rather than to their content, and it advanced under ACTION4 three times and under ACTION3 twice, so it is not paying out for a particular deed. A quantity that increases at a fixed rate regardless of what you do is a clock; a quantity that increases when you achieve something is a score, and I have achieved nothing. That is real evidence and it is still not proof: a designer may well have written a progress meter that also credits mere activity, and I have never seen the left end of row 53 nor any label for it. What changes is the playbook, not the goal section. If this is a clock then a press spent producing a state I have already seen is a press spent for nothing, and the toggle loop I have been running is the most expensive thing in the record."
    [depends: the_bar_runs_leftward_and_the_budget_is_measurable  probe: pending]

  theorem the_march_now_leads_by_four_commands_and_i_keep_it_for_the_present_state_alone "last round the march lagged the world and I priced it at three replay transitions. The arm has since given it instances at (53,59) and (53,60), and a rule I did not edit changed behaviour again -- the second time level data has moved a rule under me. Trace it exactly. The seed paints (53,63) at t4, correctly. The march then fires at t7, t9, t11 and t13, painting (53,62), (53,61), (53,60) and (53,59), while the world converts those same four cells at t8, t11, t14 and t17. The lead grows one command per conversion: one at t7, two at t9, three at t11, four at t13. Under open-loop replay errors compound, so transitions t7 and t9 through t16 all diverge and only t17 recovers, and I pre-register replay at 7 of 17 rather than the 9 of 13 certify last returned. What I get for it is the present state: the manual's bar stands at (53,63) through (53,59) converted and the world's bar stands at exactly the same five cells, so the manual reconstructs the CURRENT frame cell for cell and every probe I launch from here starts from truth. Dropping the march scores 6 of 17 and leaves the manual four cells wrong right now. I take the exactness. And I name the price honestly: the exactness is luck, not design -- the march ran out of instances at (53,58) at the same moment the world caught up -- and the very next conversion will restore the lead and destroy it."
    [depends: the_manual_cannot_predict_a_tick_into_a_cell_that_has_never_varied  probe: passed]

  theorem the_manual_cannot_predict_a_tick_into_a_cell_that_has_never_varied "this was prose last round and is now witnessed four times, by P-09 through P-12. The arm instantiates only cells the board cannot explain, and the board is the cells that never vary, so at prediction time (53,60) and (53,59) were board, no rule of mine could name them, and the manual's answer to ACTION4 at t14 and to ACTION3 at t17 was necessarily a frame with those cells unconverted. Both refutations are exactly that and nothing else: 1317da5b367d300a against 3281b51b4c1aa929 is one bar cell, b278887e087d3593 against febfe034e90989ad is one bar cell. What I got wrong last round was the SIZE of the defect, and I correct it here. I wrote that the lag was permanent but bounded at one cell. It is bounded at one cell only when the frontier converts before another conversion is due; across a stretch where the world ticks twice and the store is not refreshed in between, the manual falls two cells behind, and it will fall k behind across k ticks. The bound is on the store's staleness, not on the world. The mechanism is unchanged and is not a bug I can fix from inside the manual: each cell the world converts hands the arm one more instance and hands me one more cell of reach, always one conversion after I needed it."
    [depends: instance_anchoring_is_frame_zero_and_only_varying_cells_get_instances  probe: passed]

  theorem replay_is_open_loop_and_the_probe_stream_re_confirmed_it_this_round "settled two drafts ago by a four-way table and re-confirmed here for free, which is the kind of corroboration I trust because I did not go looking for it. Read the probe stream in sequence. P-09's inert hash is b278887e087d3593; P-10's inert hash is 1317da5b367d300a, which is exactly the hash P-09's MANUAL prediction named, not the hash the world answered. The probe harness carried my prediction forward as its own next state and never once resynced to the world. Same again at P-11 and P-12. So the checker replays the manual against itself, a guard on an off-board cell reads false rather than matching, and my errors compound rather than being wiped -- which is the whole explanation of why a four-command lead shows up as ten consecutive wrong transitions that close in one."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem the_first_divergence_is_the_selector_swap_and_i_refuse_to_change_the_manual_for_it "the surprise that called me back is the replay mismatch at transition 0: ACTION1, 96 cells, first cell (30,11) manual 5 world 6. I have predicted this surprise, cell for cell, for five drafts running, and I answer it with a refusal rather than an edit for the sixth round. The refusal rests on two independent grounds already proven and re-checked against the divergence report certify returned again this round. Ground one, constraint 5: the report contains five cells, (30,16) (31,16) (32,16) (33,16) (34,16), that are colour 5 in frame 0 with above 5, below 5, left 5, right 4 -- one indistinguishable guard reading -- and the world sends them to 6, 6, 1, 2, 6. No guard in this language separates them, so any rule set producing the swap contains two rules that both fire, which is forbidden. Ground two, constraint 3: the shortest expressible form is of order one landmark and one rule per repainted cell in each direction, longer than the 96 pixels it draws. A surprise the manual predicted in advance, whose cause the manual has proven inexpressible twice over, is the price of a language rather than a defect in the theory, and the price is one transition in seventeen."
    [depends: the_swap_is_provably_inexpressible_here  probe: passed]

  theorem no_goal_is_signed_and_that_is_deliberate "all eighteen states returned NOT_FINISHED and nothing in seventeen transitions indicates what finishing means. An absent goal compiles to is_goal implies False, which under-claims and costs a round; a wrong goal sends the searcher after a fiction and costs the level. The bar is still the only monotone quantity in the record and still the most tempting goal, and this round moved my belief about it -- the meter advanced five times while nothing whatever was achieved, which is what a clock does -- but moved it toward BUDGET, which is the reading under which making the bar full is the opposite of winning. So the tilt is an argument against signing the tempting goal, not for it. The live candidates are unchanged: that a lane must be brought into some relation with the badge at its far end, that every slot in the column must be visited or solved, or that the objective lives in the twenty-nine rows I have never been shown. There is no goal section, and this theorem is where the silence is recorded."
    [depends: the_meter_advances_for_no_achievement_and_that_tilts_it_toward_clock  probe: pending]

  theorem the_march_and_the_blanking_rule_cannot_both_fire_and_the_argument_survives_two_new_meter_studs "both are guarded on act=key(3) and colored(?p,2), so constraint 5 needs the remaining guards disjoint on every instance in every state, and the Stud type just grew from twelve instances to fourteen. I re-ran the argument on the two new ones rather than assuming it carried. The blanking guard needs the left neighbour to be neither 0 nor 2; a meter stud's left neighbour is 2 whenever the stud itself is still 2, because the bar converts strictly right to left and no state in the record has a colour-3 cell immediately left of a colour-2 one. That covers (53,59) and (53,60) exactly as it covered (53,61). The march needs the right neighbour to be 3, which fails for every strip stud (right neighbours are only ever 1, 2 or 4), for both unselected-bar studs (2 or 5), for the port stud (1 or 4), and for (53,63) whose right neighbour is off-board and therefore reads false under every guard. Certify adjudicated 42 pairs last round with zero clashes; the same enumeration now covers 18 states by 3 actions, 54 pairs, and I pre-register zero clashes again. The latent risk is unchanged and I restate it because it is the one thing that would break this: a state with a colour-3 cell immediately left of a colour-2 bar cell admits both rules on that cell. The monotone right-to-left order forbids it, and that order is now witnessed five times rather than three -- witnessed, not proven."
    [depends: the_bar_runs_leftward_and_the_budget_is_measurable  probe: passed]

  theorem the_world_is_not_a_function_of_the_visible_frame_and_it_is_now_witnessed_under_both_keys "witnessed twice, once for each strip key, which removes the chance that it was an artefact of ACTION4. Witness one: s5 and s7 are the same 4096 cells, ACTION4 from s5 restored twelve cells, ACTION4 from s7 restored twelve cells and ticked (53,62). Witness two: s8 and s10 are the same 4096 cells and ACTION3 from s8 blanked twelve cells while ACTION3 from s10 blanked twelve and ticked (53,61). This round adds a third of the same shape: s14 and s16 are the same frame -- the world said so itself by answering the identical hash 3281b51b4c1aa929 to ACTION4 at both t14 and t16 -- and ACTION3 from s15 did not tick while ACTION3 from s17's predecessor did. So the world carries at least one bit no guard of mine can read, constraint 5 forbids me writing both successors of an identical frame, and any planner treating a frame as a state is planning in the wrong space. This holds whichever of D and E is right, which is why it survived F's death untouched."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem frame_zero_is_reconstructed_exactly "frame 0 equals the frame I am shown with two edits: rows 38-39 by cols 17-22 hold the texture rather than colour 4, and (53,59) through (53,63) all hold 2 rather than 3. The anatomy closes cell by cell: 22 Casing as the perimeter of rows 36-41 by cols 11-16 minus the two ports plus the 2x2 core at rows 38-39 cols 13-14; 12 Cavity as the 4x4 at rows 37-40 cols 12-15 minus that core; 8 Rail at rows 30-31 and 34-35 by cols 13-14; 4 Stud at rows 32-33 by cols 13-14; 8 Pip and 4 Stud in the lane B strip; 1 Pip at (38,16) and 1 Stud at (39,16) in the ports; 12 Erased as the lane A strip at rows 32-33 cols 17-22; 5 Stud in the meter, two more than last round. 22+12+8+9+14+12 = 77 = cells_needing_an_owner. The 24 remaining dynamic cells are the background of the unselected slot footprint, cols 11, 12, 15, 16 over rows 30-35, and 77+24 = 101 = dynamic_cells, and 4096-101 = 3995 = constant_cells. The dynamic set closes independently: the selector swap repaints 96 cells and the meter has ticked five times, and 96+5 = 101. Certify has returned 0 unexplained of 4096 on this reconstruction every round it has run and must do so again."
    [probe: passed]

  theorem instance_anchoring_is_frame_zero_and_only_varying_cells_get_instances "instances are the cells of a declared colour that the board cannot explain, coloured as they are in frame 0; a cell constant across the whole record gets none. The arithmetic has been demonstrated five times now: 73 owners at 97 dynamic, 74 at 98, 75 at 99, and this round 77 at 101, the difference each time exactly the bar cells that converted and my Stud declaration moving by exactly the same number. Twice it has done something sharper than bookkeeping. The instance at (53,61) once changed the behaviour of a rule I did not edit; this round the instances at (53,59) and (53,60) did it again and in the same direction, turning a march that lagged into a march that leads by four. Level data is not inert with respect to the manual, and I will not again assume a rule's replay is stable across a store update -- this is the second time I have written that sentence and the first time it cost me a pre-registered number."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem the_bar_runs_leftward_and_the_budget_is_measurable "five cells have converted, (53,63) then (53,62) then (53,61) then (53,60) then (53,59), so right-to-left is witnessed five times with no exception. Row 53 reads colour 2 from column 10 to column 58 in the window I am given and I have never been shown columns 0 to 9 of that row, so at least 49 and at most 59 cells remain. Seventeen commands bought five ticks; both surviving readings put the rate at one tick per three counted commands, so of order 150 to 180 commands remain. Probing is cheap and the cheapness is a measured quantity -- but see the clock theorem, because if this is a budget then cheap is not the same as free, and the fourteen presses that produced no new state were the expensive kind."
    [depends: the_manual_cannot_predict_a_tick_into_a_cell_that_has_never_varied  probe: passed]

  theorem a_repeat_of_a_blanking_key_has_still_never_been_tried_and_no_longer_separates_the_cadence "key(3) blanked a shown strip at t3, t7, t9, t11, t13, t15 and t17, key(7) blanked one at t5, key(4) restored a blanked one at t4, t6, t8, t10, t12, t14 and t16 -- fifteen presses, every blank from a shown strip and every restore from a blanked one, twelve cells and cell for cell identical every time. Hide-and-show and toggle-and-toggle remain indistinguishable and this probe is still the only thing that separates them. What has CHANGED is its price in cadence information, and I record the loss rather than quietly leaving the old justification standing: last round I sold this press partly on separating F from D and E on the tick, and F is dead. From the present position both survivors say a single extra strip press does not tick -- D reaches two-frame ordinal 17, E reaches work ordinal 15, neither a tick point -- so the press now buys structure and inertness, not cadence. My manual commits to complete inertness: every strip cell is colour 4, no blanking guard can fire, and the march cannot fire because (53,58) has never varied and has no instance. If the strip returns, hide-and-show is dead. If anything moves at all, my inertness claim is dead. Both are worth having and neither is worth the first slot any more."
    [depends: readings_D_and_E_are_both_five_for_five_and_one_selector_excursion_separates_them  probe: pending]

  theorem the_cadence_is_inexpressible_and_the_period_three_finding_makes_that_sharper_rather_than_softer "a guard reads a cell colour, its four neighbour colours, off-board, and the action name. Both surviving readings need a counter modulo three, and the grammar has no counter and no latch. Five ticks at an exact period of three is now the best-established quantitative fact in the record and it is exactly the fact I cannot write down. I re-examined one loophole with the new data, because a three-cycle is the shape a colour cycle could carry: paint the frontier cell through two intermediate colours and let the third press finish it at 3. It fails on the frame rather than on the grammar. Every cell of this world is drawn and compared, so an intermediate colour is a visibly wrong cell for two presses out of every three, which trades the march's wrong cell for a differently wrong cell at no gain -- and there is no cell anywhere in the frame whose colour the record leaves free to use as scratch. The other three loopholes stay shut as before: an object at the background colour exposes no readable field, a second type at colour 2 duplicates all fourteen Studs because the arm finds objects by colour alone, and a landmark can be read but never painted. The hidden bit stays prose."
    [depends: readings_D_and_E_are_both_five_for_five_and_one_selector_excursion_separates_them  probe: passed]

  theorem the_landmark_and_teleport_device_would_reach_the_next_bar_cell_and_i_refuse_it "the one device in the grammar that touches a cell no object occupies is the landmark, so I priced it properly rather than asserting the frontier was unreachable. A landmark bar_frontier at arc-cell (53,58) is legal and can be READ by a guard. It cannot be PAINTED: the event table dispatches recolored on an object name, and the only events taking a landmark are jumped and teleported, which MOVE an object to that cell. So the sole way to colour (53,58) is to teleport a Stud into it, and that is where the device fails on the world rather than on the grammar. Teleporting the (53,59) Stud vacates (53,59), which the world converted at t17 and which must stay colour 3 -- I would gain the frontier and destroy the cell behind it, turning the bar's converted prefix into a single travelling cell and contradicting five witnessed conversions that all persisted. Teleporting a strip Stud instead breaks a toggle that is 192 for 192. Beyond that, no transition in seventeen witnesses any position change at all: my entire event vocabulary is recolored, and cegis_miner independently refuses every track on the ground that the world does not narrate as one mover."
    [depends: the_manual_cannot_predict_a_tick_into_a_cell_that_has_never_varied  probe: passed]

  theorem the_swap_is_provably_inexpressible_here "the selector move relabels 96 cells and no set of rules in this language produces them. A guard sees a cell's own colour, its four neighbour colours, off-board, and the action name -- no coordinate, no row band, no distance. The witness is inside the divergence report certify returned again this round: (30,16), (31,16), (32,16), (33,16) and (34,16) are all colour 5 in frame 0 with above 5, below 5, left 5, right 4, one indistinguishable guard reading, and the world makes them 6, 6, 1, 2, 6. Three answers to one question. A second pair kills colour as a discriminator: (30,13) is colour 3 and becomes 6 while (32,13) is colour 2 in an equally uniform bar neighbourhood and also becomes 6. Constraint 5 forbids two rules that both fire, so the swap does not go in the manual."
    [depends: the_panel_is_a_column_of_slots  probe: passed]

  theorem the_swap_also_fails_the_compression_test "grant every expressibility obstacle removed and free reading of position. The swap still does not belong. It repaints 96 cells whose new colours follow no local law, because the widget is teleported six rows and no event in the vocabulary does that -- moved is one cell, jumped-over is two, jumped-to-a-landmark needs a landmark and a rule per instance. The shortest form I can construct is of order one landmark and one rule per repainted cell in both directions, longer than the 96 pixels it explains. Constraint 3 refuses it independently of constraint 5. Two independent refusals, which is why I expect never to write the swap rather than merely not to have written it yet."
    [depends: the_swap_is_provably_inexpressible_here  probe: passed]

  theorem a_background_object_would_own_exactly_the_swap_footprint_and_i_still_do_not_declare_it "an object declared at arc-colour 5 with arc-instances all would be placed on the colour-5 cells the board cannot explain, and those number exactly 101 minus 77 = 24: cols 11, 12, 15, 16 over rows 30-35, the unselected slot footprint, not one cell more, and the count survived the store growing by two because both new cells were colour 2. The declaration is cheap and surgical. I still do not declare it, because it would explain no pixel the board does not already draw correctly and would enable no rule I can write, which is constraint 3 refusing it on its own terms."
    [depends: the_swap_is_provably_inexpressible_here  probe: pending]

  theorem the_restore_and_blank_rules_are_conditioned_on_a_selection_the_manual_cannot_represent "the restore rules guard on colour 4 alone and the blanking rules on one to three neighbour tests. Both are correct on all fifteen blank-or-restore presses, because every press was made with the bottom slot selected, where the only colour-4 Pip and Stud instances in existence are the twelve blanked lane B cells. They would be wrong the moment slot A is selected: lane A strip cells become texture while lane B strip cells become arena fill of colour 4, and the instances do not move with the widget because I only ever recolour. My manual never reaches that state, being silent on the selector, so this costs zero transitions and certify cannot see it. It is written here because a searcher planning through a selector move would be misled by rules scoring 192 of 192 -- and because the excursion the playbook now ranks second walks straight into it. The mitigation is a condition on the probe, not avoidance of it: press no strip key while the upper slot is selected. An out-and-back pair of selector presses satisfies that by construction, which is why the order names the pair rather than the single press."
    [depends: the_swap_is_provably_inexpressible_here  probe: pending]

  theorem the_strip_is_one_global_diagonal_texture "one rule covers every strip cell I have seen: a strip cell is colour 2 when (row + col) mod 3 = 1 and colour 1 otherwise. Frame 0 row 38 cols 16-22 reads 1 2 1 1 2 1 1 and row 39 reads 2 1 1 2 1 1 2, a period-3 run offset by one column; the divergence report gives lane A row 32 cols 16-22 as the world drew it at t1, 1 2 1 1 2 1 1, and rows 32 and 38 agree because 6 divides by 3. The two port cells fit the same formula, which is an unforced success. So the two strips are two windows onto one texture, which is why a restore rebuilds twelve cells exactly and why seven restores rebuilt them identically. Untested prediction: select slot A and row 33 cols 17-22 reads 1 1 2 1 1 2. No rule needs this, since each instance remembers its frame 0 colour, so the concept buys understanding rather than symbols and stays out of the word table."
    [depends: frame_zero_is_reconstructed_exactly  probe: pending]

  theorem the_seed_column_is_never_erased "blanking takes cols 17-22 of the selected lane and stops there, eight times now, twelve cells every time. (38,16)=1 and (39,16)=2 sit on the widget right edge, are Pip and Stud instances, and have never changed under any blank; the guards say why, since the left neighbour of each is a colour-0 cavity cell. They are the only cells of the texture that survive hiding and they are exactly the two needed to phase a period-3 run. The rival explanation is that col 16 is where the 6x6 widget ends and the survival is coincidence; eight blanks do not separate them."
    [depends: the_strip_is_one_global_diagonal_texture  probe: pending]

  theorem the_panel_is_a_column_of_slots "the divergence report gives the world's t1 rows 30, 31, 32 at cols 11-16 as 6 6 6 6 6 6 / 6 0 0 0 0 6 / 6 0 6 6 0 1, and frame 0 rows 36, 37, 38 at those columns read identically -- eighteen cells, six rows apart. Rows 42 to 52 are uniform background, so rows 36-41 is the bottom slot and rows 30-35 the one above it. ACTION1 moved selection from the bottom slot to the upper one and ACTION2 moved it back, one witness each for up and down, no wrap needed. Whether a third slot exists above is untested: (29,13) and (29,14) hold colour 3 and never vary, which is what a slot at rows 24-29 would show on its bottom rail, but board cells prove nothing about slots never selected."
    [depends: frame_zero_is_reconstructed_exactly  probe: pending]

  theorem the_badge_is_lane_aligned_and_the_matching_reading_stays_downgraded "the arena is colour 4 over cols 17-46, bounded on the right by background from col 47. The only thing in it that is neither strip nor fill is a 4x4 block of colour 14 at rows 31-34 by cols 42-45. Those are exactly the rows an upper-slot cavity occupies within its six-row band, so the badge belongs to the lane of the slot at rows 30-35, and the bottom slot's lane has nothing at cols 42-45. The tempting reading is that it is a target the lane texture must be made to match, but the strip is 2 by 6 and the badge is 4 by 4 of one uniform colour, so shape refutes it. The surviving readings are that it marks which slot carries the task, that it is a destination, or that it is a picture of a completed cavity, the widget cavity being also 4x4 with a 2x2 core removed. Seventeen transitions and none of them bear on any of the three; colour 14 appears nowhere else in the frame. This is the strongest single hint that the ending lives outside the product of states my pressed keys generate."
    [depends: the_keys_i_have_pressed_generate_a_closed_space_that_cannot_contain_the_ending  probe: pending]

  theorem colour_classes_are_not_the_worlds_objects_and_i_admit_the_cost "the six declared types are colour classes, not things. Stud alone now spans the unselected slot bar, a port, four strip cells and five meter cells -- four unrelated roles in one type, and the count grows every time the bar converts, which is the clearest possible sign that the type is an artefact of the arm rather than a thing in the world. Casing and Cavity together are one widget. The world segments by widget and the arm segments by colour, and the arm wins because the arm draws the frame. The gain is measured: six declarations own all 77 cells that need an owner against 77 pixels written out, with 0 unexplained confirmed every round it has been checked. The cost is measured too: no rule can name the strip, so every blanking rule carves it out of its colour class by neighbour tests, and the march is kept off nine other Studs by a right-neighbour test that is a fact about the bar's geometry rather than about the meter. Those guards are pixel-fitting in a costume, and the march is the worst offender because its guard is an accident of what has already ticked."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem i_have_never_been_shown_rows_0_to_28 "colours_seen lists 8 and 9 and neither appears anywhere in the window I am given, rows 29-54 by cols 10-63. They live in the 3995 constant cells I have never looked at -- above row 29, left of col 10, or below row 54. That region is board by definition and my manual draws it correctly by doing nothing, so responsibility stays at 0 unexplained; but it is where a title, target, score or instruction would live, and the likeliest home of whatever finishing means and of whether the bar is a budget or a score. Seventeen commands have not made one cell of it vary, which is mild evidence that it is decoration, but only mild, since fourteen of the seventeen were the same two keys and the two keys generate a closed space."
    [depends: the_keys_i_have_pressed_generate_a_closed_space_that_cannot_contain_the_ending  probe: pending]

  theorem two_keys_have_never_been_pressed_and_they_are_now_the_first_thing_to_press "ACTION1, 2, 3, 4 and 7 have been pressed; key(5) and key(6) have not, after eighteen commands. They have sat at rank four in the playbook for five drafts and I am moving them to rank one, and the reason is not impatience. It is the closure argument: the five pressed keys move the world only inside a product of strip state, selector slot and meter length, all eighteen states are in that product, and nothing in that product has ever returned anything but NOT_FINISHED. An unpressed key is the only cheap thing that can leave it. Of order 150 to 180 commands of bar remain so two presses are affordable, and each press also reads its own returned frame count, which reading D turns into a direct measurement of the counter -- a non-strip two-frame press is exactly the thing that separates D from E, so if either key returns two frames it does the cadence work as a side effect. If either is a click carrying coordinates, this guard language cannot express it and the finding is recorded as prose rather than as a rule."
    [depends: the_keys_i_have_pressed_generate_a_closed_space_that_cannot_contain_the_ending  probe: pending]

  theorem what_the_engines_offered_and_why_none_of_it_was_taken "the store moved so the engines moved, and they moved the way a store update moves them rather than the way a discovery does. mdl_segmenter still returns negative gain on both variants, now -2457 bits at 4 tracks and -34069 at 89, with tracks that are 440-cell blobs of shape 13x36 and colour null -- the panel and the arena fused by connected_components(4), a fact about the operator rather than the world. Its obj1 is 108 cells of shape 2 by 54 present in all eighteen frames, which is rows 53 and 54 clipped to the window, the meter bar and the fill row beneath it, fused because colour 2 and colour 4 touch vertically and background 5 does not separate them; it corroborates that the bar is one object continuing left of column 10 where I have never seen it. cegis_miner refuses all four tracks because its precondition is exactly one move event per transition, and its verdict that the world does not narrate as one mover agrees with my event vocabulary of recolored alone and is the outside evidence I leaned on when refusing the teleport device. zero_space calls its own evidence THIN in its own words -- 17 transitions constraining rank 7 of 707 features, null space of dimension 700 -- and its single global law spans 101 dynamic cells at once, which is what a 700-dimensional null space produces rather than what a conservation law looks like. Its cell list, ninety-six slot cells plus the five meter cells (53,59) through (53,63), is exactly my dynamic set and is the one thing in the stream I use. Four extra transitions moved zero_space's rank from 5 to 7 and its verdict not at all."
    [probe: pending]

  theorem what_this_draft_pre_registers "certify first, and I pre-register a WORSE number than last round on purpose, because the store grew under a rule I did not edit. Replay 7 of 17, matching at t2, t3, t4, t5, t6, t8 and t17 and diverging everywhere else; first divergence at transition 0 under ACTION1, 96 cells wrong, first cell (30,11) manual 5 world 6; responsibility 0 unexplained of 4096; unambiguous 0 clashes over 18 states by 3 actions, 54 pairs, 54 nominal, 0 step crashes. If replay comes back at 9 or 6 rather than 7 my trace of the march's lead is wrong and I want the trace corrected before anything else. Now the world. Present position: 33 internal frames spent, 16 two-frame commands, 14 work presses, bar converted through (53,59), strip blanked, selector home. Probe one, key(5) then key(6): anything at all is new, the returned frame count is read regardless, and if either returns two frames it also separates D from E on the following strip press. Probe two, ACTION1 then ACTION2 then a strip key: D ticks (53,58) on the strip key, E does not; the pair returns the frame to its start and no strip key is pressed while the upper slot is selected. Probe three, repeat ACTION3 from the blanked state: my manual says not one cell changes and both surviving readings say no tick; if the strip returns, hide-and-show is dead. Probe four, three consecutive work presses with nothing between: both D and E say the third of them converts (53,58), which my manual cannot draw and will get wrong -- that is the pre-registered cost of the frontier blindness and I state it before paying it."
    [depends: readings_D_and_E_are_both_five_for_five_and_one_selector_excursion_separates_them  probe: pending]
```

=== PLAYBOOK ===
```
# playbook.dsl -- fourteenth draft.
#
# WHAT MOVED, AND WHY.
#
# 1. THE TOP OF THE ORDER CHANGED FOR THE FIRST TIME IN FIVE DRAFTS, AND NOT
#    OUT OF BOREDOM. Four commands were finally pressed and what they taught
#    me was structural: the five keys I have pressed move the world only
#    inside a product of three coordinates -- strip shown or blanked, selector
#    in one of two slots, meter length k. All eighteen states are in that
#    product, the world's own hashes confirm it (s14 and s16 answered the
#    identical hash), and every one of them returned NOT_FINISHED. A closed
#    space that has never contained the ending cannot be explored into
#    containing it. So the two keys never pressed go first.
#
# 2. THE CADENCE QUESTION SHRANK BY ONE READING AND GOT ONE CLEAN PRESS.
#    Reading F is dead -- it required the tick at t15, the world ticked at
#    t14. D and E are both 5 for 5 and are provably inseparable by any run of
#    strip keys, because over such a run the two counters advance in lockstep.
#    That is why fourteen presses bought no discrimination and why one
#    selector excursion buys all of it. The excursion moves up to second.
#
# 3. THE REPEAT-BLANK PROBE LOST HALF ITS VALUE AND I DEMOTE IT RATHER THAN
#    RE-ARGUING FOR IT. It used to separate F from D and E on the tick; F is
#    gone, and both survivors now agree that one extra strip press does not
#    tick. It still separates hide-and-show from toggle-and-toggle, which
#    nothing else does, so it stays third rather than falling off.
#
# 4. NEW PRUNE, AND IT IS THE MOST EXPENSIVE THING I HAVE LEARNED. Fourteen
#    work presses accomplished nothing and the meter advanced five times
#    regardless. A quantity that rises at a fixed rate whatever you do is a
#    clock. That is not proof and there is still no goal section, but it flips
#    the price of a press that produces a state I have already seen from free
#    to costly, and the toggle loop I ran for four rounds was the worst
#    offender in the record.
#
# 5. STILL NO PLAN HERE. These are orders of interrogation.

order   press_the_two_never_pressed_keys_before_anything_else  [proof: lean]
order   take_the_selector_excursion_as_a_pair_then_one_strip_key_to_split_D_from_E  [proof: lean]
order   repeat_a_blanking_key_in_the_blanked_state_to_kill_hide_or_toggle  [proof: lean]
order   read_the_returned_frame_count_of_every_command_since_one_reading_counts_it  [proof: lean]
order   prefer_a_press_that_leaves_the_reachable_product_over_one_that_moves_inside_it  [proof: lean]
order   retest_the_key_that_once_returned_a_single_frame_since_a_reading_rests_on_it  [proof: lean]
order   bound_the_selector_by_pushing_the_cursor_past_the_slots_already_drawn  [proof: lean]
order   look_at_the_badge_lane_while_its_own_slot_is_the_selected_one  [proof: lean]
order   read_the_strip_row_never_displayed_to_score_the_texture_rule  [proof: lean]
order   make_some_cell_outside_the_observed_window_vary  [proof: lean]
order   vary_the_order_of_the_two_blanking_keys_across_a_restore  [proof: lean]
order   probe_the_unknown_before_planning_while_no_goal_is_known  [proof: lean]
order   read_every_bar_cell_after_every_command  [proof: lean]

prefer  a_key_never_pressed_over_a_key_whose_effect_is_already_witnessed  [ev: 2/7 keys unpressed]
prefer  an_action_that_can_leave_the_closed_product_of_states_already_enumerated  [ev: 12/12 states in the product]
prefer  an_action_the_two_surviving_counter_readings_give_different_answers_for  [ev: 2 readings, each 5/5 on 5 ticks]
prefer  a_non_strip_two_frame_press_since_only_that_advances_the_readings_differently  [ev: 14/14 work presses moved both alike]
prefer  an_action_that_answers_more_than_one_open_question_at_once  [ev: 1 press separates 3]
prefer  an_action_the_manual_has_pre_registered_a_null_frame_for  [ev: 0/17 transitions tested it]
prefer  an_action_whose_returned_frame_count_the_readings_disagree_about  [ev: 1/17 commands returned one frame]
prefer  a_slot_never_selected_over_one_already_drawn_twice  [ev: 2 slots seen of a column]
prefer  a_press_that_makes_a_board_cell_vary_over_one_that_repeats  [ev: 101/4096 cells ever varied]
prefer  a_probe_launched_from_a_state_the_manual_reconstructs_exactly  [ev: 4096/4096 cells right now]
prefer  an_excursion_that_returns_the_frame_to_where_it_started  [ev: 1/17 commands undid another]

heuristic state_classes_outside_the_enumerated_product  [admissible: lean]
heuristic keys_never_pressed  [admissible: lean]
heuristic counter_readings_still_alive  [admissible: lean]
heuristic presses_needed_to_separate_the_surviving_counter_readings  [admissible: lean]
heuristic bar_cells_still_unconverted  [admissible: lean]
heuristic slots_in_the_column_never_yet_selected  [admissible: lean]
heuristic rows_of_the_frame_never_yet_displayed  [admissible: lean]
heuristic lanes_whose_badge_has_never_been_addressed  [admissible: lean]
heuristic keys_whose_effect_rests_on_a_single_witness  [admissible: lean]

prune   plan_that_spends_a_work_press_and_returns_a_state_already_enumerated => dead  [proof: lean]
prune   plan_that_expects_a_run_of_strip_keys_to_separate_the_two_readings => dead  [proof: lean]
prune   plan_that_treats_the_internal_frame_total_reading_as_still_alive => dead  [proof: lean]
prune   plan_that_counts_the_lone_one_frame_command_toward_the_cadence => dead  [proof: lean]
prune   plan_that_assumes_two_equal_frames_are_the_same_state => dead  [proof: lean]
prune   plan_that_assumes_the_checker_resyncs_the_manual_between_transitions => dead  [proof: lean]
prune   plan_that_assumes_a_rule_replays_the_same_after_the_store_grows => dead  [proof: lean]
prune   plan_that_ties_the_bar_tick_to_one_particular_key => dead  [proof: lean]
prune   plan_that_prices_a_bar_cell_at_one_per_restore_press => dead  [proof: lean]
prune   plan_that_counts_the_bar_on_raw_command_number_alone => dead  [proof: lean]
prune   plan_that_asks_the_manual_to_tick_a_bar_cell_never_yet_witnessed => dead  [proof: lean]
prune   plan_that_needs_a_cell_that_has_never_varied_to_change => dead  [proof: lean]
prune   plan_that_teleports_an_object_out_of_a_cell_the_bar_has_converted => dead  [proof: lean]
prune   plan_that_rests_on_the_bar_meaning_being_known => dead  [proof: lean]
prune   plan_that_spends_the_manuals_present_exactness_and_returns_no_new_frame => dead  [proof: lean]
prune   plan_that_relies_on_the_manual_drawing_the_selector => dead  [proof: lean]
prune   plan_that_presses_a_strip_key_while_the_upper_slot_is_selected => dead  [proof: lean]
prune   plan_that_treats_the_two_blanking_keys_as_interchangeable => dead  [proof: lean]
prune   plan_whose_rules_are_longer_than_the_pixels_they_draw => dead  [proof: lean]
prune   plan_that_cites_a_transition_absent_from_the_current_record => dead  [proof: lean]
prune   plan_that_spends_a_round_on_a_manual_that_does_not_compile => dead  [proof: lean]
prune   action_whose_successor_every_live_reading_agrees_on => dead  [proof: lean]
prune   undoing_a_selector_move_that_just_revealed_something => dead  [proof: lean]
prune   bar_consumed and not goal => dead  [proof: lean]
```

=== LOG ===
```json
[
  {"id": "O-01", "subject": "Stud population 12 -> 14", "verdict": "accept",
   "as": "Stud", "why": "(53,59) and (53,60) varied for the first time at t17 and t14, so the arm now instantiates them; 22+12+8+9+14+12 = 77 = cells_needing_an_owner, and 77+24 background footprint cells = 101 = dynamic_cells."},
  {"id": "O-02", "subject": "mdl_segmenter obj0/obj2/obj3, 440-cell blobs of shape 13x36, colour null", "verdict": "reject",
   "why": "connected_components(4) fuses the panel with the arena because colour 6 touches colour 4; both variants report NEGATIVE gain (-2457 and -34069 bits), so the engine's own MDL score refuses its own segmentation."},
  {"id": "O-03", "subject": "mdl_segmenter obj1, 108 cells shape 2x54 present in all 18 frames", "verdict": "entailed",
   "why": "it is rows 53-54 clipped to the window -- my meter plus the fill row beneath it, fused vertically; it adds only the corroboration that the bar continues left of col 10 where I have never been shown it."},
  {"id": "O-04", "subject": "an object declared at arc-colour 5 owning the 24-cell slot footprint", "verdict": "reject",
   "why": "101 - 77 = 24 places it exactly on the unselected slot footprint, but it would explain no pixel the board does not already draw correctly and enable no writable rule; constraint 3 refuses it on its own terms."},
  {"id": "R-01", "subject": "key3_marches_the_meter_leftward, ev retagged t8,t11,t14,t17 cov 4/4", "verdict": "accept",
   "why": "it is the only rule accounting for any bar conversion, and it accounts for four; the ev tag cites the world's conversions rather than its own firings at t7,t9,t11,t13 so that the four-command phase error is stated in prose instead of hidden inside a tag."},
  {"id": "R-02", "subject": "moving the march to key(4), or dropping it", "verdict": "reject",
   "why": "traced by hand against all 17 transitions: key(4) march scores 6/17, no march scores 6/17, key(3) march scores 7/17 and additionally reconstructs the CURRENT frame cell for cell, which every probe launched from here depends on."},
  {"id": "R-03", "subject": "the six strip toggle rules, ev extended to t15 and t17 and t14 and t16", "verdict": "accept",
   "why": "four new presses, twelve cells each, cell for cell identical to the eleven before; coverage rises from 132/132 to 192/192 with no guard edited."},
  {"id": "R-04", "subject": "cegis_miner's four tracks", "verdict": "reject",
   "why": "the engine refuses them itself -- its precondition is exactly one move event per transition and it reports 'the world does not narrate as one mover', which agrees with my event vocabulary of recolored alone."},
  {"id": "L-01", "subject": "reading F, internal-frame totals crossing multiples of seven", "verdict": "reject",
   "why": "the running total goes 25 to 27 at t14 and crosses 28 only at t15; F therefore required the fourth tick at t15 and the world ticked at t14. Named press, named refutation."},
  {"id": "L-02", "subject": "reading E'', counting every strip-affecting press including the ACTION7 at t5", "verdict": "reject",
   "why": "a reading I had not previously written down; its tick ordinals are 2, 6, 9, 12, 15 and 2 against 6 is a gap of four where every later gap is three, so the ACTION7 does not count under any surviving reading."},
  {"id": "L-03", "subject": "readings D and E both at 5/5", "verdict": "probe-pending",
   "why": "D's tick ordinals are 4,7,10,13,16 and E's are 2,5,8,11,14, both exact progressions of step three with no false positives; they advance in lockstep over strip keys and are separated only by a two-frame non-strip press."},
  {"id": "L-04", "subject": "the state space is a product of strip-state, selector-slot and meter-length", "verdict": "accept",
   "why": "decoded from the four probe hashes, then checked against the store independently: enumerating the product gives 12 states with collapses s2=s0, s6=s4, s7=s5, s10=s8, s13=s11, s16=s14, and 18-6 = 12 = distinct_states."},
  {"id": "L-05", "subject": "the pressed keys generate a closed space that has never contained the ending", "verdict": "probe-pending",
   "why": "all 18 states lie in that product and all returned NOT_FINISHED; the argument assumes the product is complete over 18 states, which is exactly what an unpressed key exists to break -- hence rank one rather than a signed law."},
  {"id": "L-06", "subject": "the bar is a clock rather than a score", "verdict": "probe-pending",
   "why": "fourteen work presses achieved nothing whatever -- the strip stands blanked exactly as at t3 -- and the meter advanced five times regardless, under ACTION4 three times and ACTION3 twice; a quantity rising at a fixed rate independent of content is a clock, but a designer may credit mere activity, so it changes the playbook and not the goal section."},
  {"id": "L-07", "subject": "the manual's frontier blindness, previously claimed bounded at one cell", "verdict": "accept",
   "why": "P-09 through P-12 witness it four times; I correct my own earlier bound -- across a stretch where the world ticks twice on a stale store the manual falls two cells behind, so the bound is on store staleness, not on the world."},
  {"id": "L-08", "subject": "no clash between the march and the blanking rules, extended to two new meter Studs", "verdict": "accept",
   "why": "re-run rather than assumed: a meter stud's left neighbour is colour 2 while the stud itself is 2, because conversion is strictly right-to-left, so the blanking guard's not-colored-leftof-2 is false on (53,59) and (53,60) exactly as on (53,61)."},
  {"id": "L-09", "subject": "zero_space's single global law over 101 cells", "verdict": "reject",
   "why": "the engine's own adequacy verdict is THIN -- 17 transitions constrain rank 7 of 707 features, null space dimension 700 -- so its 'law' is what a 700-dimensional null space produces; only its cell list is used, and it reproduces my dynamic set exactly."},
  {"id": "E-01", "subject": "a counter modulo three, needed by both surviving cadence readings", "verdict": "reject",
   "why": "wanted a latch; the guard language reads only a cell's colour, its four neighbours, off-board and the action name. I reconsidered a three-colour cycle on the frontier cell and refused it too: every cell is drawn and compared, so an intermediate colour is a visibly wrong cell for two presses in three, and no cell in the frame is free to use as scratch. Written as the_cadence_is_inexpressible theorem."},
  {"id": "E-02", "subject": "painting (53,58), the meter's next frontier cell", "verdict": "reject",
   "why": "wanted recolored on a landmark; the event table dispatches recolored on object names only, and teleport -- the sole event taking a landmark -- vacates (53,59), which the world converted at t17 and which must stay colour 3. Written as the_landmark_and_teleport_device theorem."},
  {"id": "P-01", "subject": "press key(5), then key(6)", "verdict": "probe-pending",
   "why": "the only cheap thing that can leave the closed product; each press also reads its own returned frame count, and a two-frame non-strip press separates D from E as a side effect."},
  {"id": "P-02", "subject": "ACTION1 then ACTION2 then one strip key", "verdict": "probe-pending",
   "why": "D reaches two-frame ordinal 19 and ticks (53,58) on the strip key; E reaches work ordinal 15 and does not. The pair returns the frame to its start, so no strip key is pressed while the upper slot is selected."},
  {"id": "P-03", "subject": "repeat ACTION3 from the blanked state", "verdict": "probe-pending",
   "why": "demoted, and I say why: it used to separate F from D and E on the tick and F is dead, so it now buys only hide-and-show versus toggle-and-toggle -- which nothing else buys. My manual pre-registers total inertness."},
  {"id": "P-04", "subject": "pre-registered certify numbers for this draft", "verdict": "probe-pending",
   "why": "replay 7/17 matching at t2,t3,t4,t5,t6,t8,t17 -- deliberately WORSE than last round's 9/13, because two new instances turned the march's lag into a four-command lead; responsibility 0/4096; unambiguous 0 clashes over 54 pairs. A score of 9 or 6 means my trace is wrong and must be fixed before anything else."}
]
```
```
