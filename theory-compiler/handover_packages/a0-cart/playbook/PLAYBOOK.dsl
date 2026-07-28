# ============================================================================
# A0 玩法书 — revision 1
#
# Four sentence forms and no others (constraint 10, dsl_grammar_v0.1): ordering,
# pruning, heuristics, preferences.  There is deliberately no way to write down
# a solution here; the 12-step plan lives in artifacts/plan_generated.json,
# which is the planner's output, not the book's content.
#
# The playbook answers to theory.dsl, not to the world.  Every entry below cites
# the manual clause it depends on, so that changing that clause invalidates the
# entry — the dependency discipline of Theoria 1.9, done by hand here.
# ============================================================================

# Landmark ordering.  `door_latch` says the Door exists exactly while the Button
# is unpressed, so any plan that ends in the right room must press first.
# Relative to theory.dsl this is a theorem, and it is the one Lean proves:
# theory/generated/theory.lean, `inv_all`, 0 axioms.
order press_before_door [proof: lean]

# Dead-end pruning.  In the no-Button instance the Cart's pagoda weight can
# never rise, so any search node outside the left room is unreachable and any
# node inside it can never leave.  theory/generated_no_button/theory.lean,
# `unsolvable`, 0 axioms.
prune w_room(Cart) > 0 and no_button => dead [proof: lean]

# The same weight function as a lower bound — certificate and heuristic are one
# object (Theoria 1.9).  Admissibility is not yet proved in Lean: the weight is
# 0/1, so it certifies unreachability but bounds distance only trivially.
heuristic w_room(Cart) [admissible: none]

# The empirical tier is EMPTY, and that is a finding rather than an omission.
# A `prefer` entry must carry a win-rate or a node account (constraint 5), and
# A0 ran one instance with one exploration trace: there is no k/n to write down
# that would not be invented.  The tier stays open until a second instance
# exists to compare against.
