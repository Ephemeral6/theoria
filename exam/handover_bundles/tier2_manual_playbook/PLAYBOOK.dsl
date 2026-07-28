# ============================================================================
# A0 玩法书 — the strategic tier of the layered handover
#
# Four sentence forms and no others (constraint 10, CONTRACTS/dsl_grammar_v0.1):
# ordering, pruning, heuristics, preferences. There is deliberately no way to
# write a solution down here. A playbook that stored answers would turn the
# handover into passing notes rather than passing understanding.
#
# Every entry cites the manual clause it rests on, so that changing that clause
# invalidates the entry.
# ============================================================================

# Check the conservation law before searching at all. The law decides some
# boards outright, and it decides them in one arithmetic step; a search that
# runs first is a search that may run forever on a board that was already
# settled. Rests on: invariant box_row_parity, invariant box_col_parity.
order parity_check_before_search [proof: lean]

# The board is decided, and impossible, when the Box's row parity or its column
# parity differs from the target's. Nothing the Player does can change either.
# Rests on: invariant box_row_parity, invariant box_col_parity, rule push2.
prune parity(Box.pos) != parity(target) => dead [proof: lean]

# A Box that cannot be pushed in any direction will never move again: every rule
# that moves the Box needs the Player standing behind it and both cells ahead of
# it free. Rests on: rule push2, rule blocked_box_crossing,
# rule blocked_box_landing.
prune no_direction_admits_a_push(Box.pos) => dead [proof: none]

# A lower bound on the number of pushes still needed: each push moves the Box
# two cells along one axis, so at best it takes half the remaining row distance
# plus half the remaining column distance. Rests on: rule push2.
heuristic pushes_remaining(Box.pos, target) [admissible: none]

# The empirical tier is EMPTY, and that is a finding rather than an omission.
# A `prefer` entry must carry a win rate or a node count (constraint 5), and no
# such measurement exists for this world yet. Writing one down without it would
# be inventing evidence. The tier stays open.
