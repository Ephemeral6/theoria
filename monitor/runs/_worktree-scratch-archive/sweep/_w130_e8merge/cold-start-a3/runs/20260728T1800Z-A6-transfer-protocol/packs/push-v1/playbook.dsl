# ============================================================================
# push 玩法书 — the second book, and it is thin on purpose.
#
# The four sentence forms are ordering, pruning, heuristics and preferences
# (constraint 10, dsl_grammar v0.2), and there is deliberately no way to write a
# solution down here.  Three of the four have very little to say about a push
# world, and saying so is more useful than padding the file:
#
# * `order` orders LANDMARKS, and this domain declares none.  A3's playbook
#   could write `order press_before_door` because A3's world has a Door whose
#   opening is a named event; a block in a corridor is not a landmark, it is an
#   obstacle whose position is problem data.  An `order` entry here would have to
#   name a cell, which is exactly what a carried book may not do.
# * `heuristic` gets one entry and it does NOT claim admissibility — see below.
# * `prefer` gets none.  Constraint 5 wants a win-rate or a node account and two
#   worlds is not a rate.  A3 wrote one at n=2 and annotated it down to
#   "indicative only"; at n=1 per direction there is nothing to annotate.
#
# So the theorem-grade content of this book is ONE pruning rule.  That is a
# smaller result than A3's and the pack reports it as such: `PACK.json` counts
# `entries_carried` and lists `entries_left_behind` by name, so a receiver can
# see what did not travel instead of having to notice its absence.
#
# ---------------------------------------------------------------------------
# WHAT "proof: domain" MEANS HERE, AND WHY IT IS NOT "proof: lean"
#
# A3's two theorem-grade entries carry `[proof: lean]` and mean it: `inv_all`
# with an empty `#print axioms`, re-discharged per level.  This pack cannot make
# that claim, and not for want of trying — D-A6-002: `gen_lean_a0.build_axes`
# admits only non-mover `_colour` and `_present` fields as state axes, so a
# Block's *position* is not in the Lean state type at all.  A Lean file for this
# manual would compile, prove `inv_closed` by `decide`, print an empty axiom
# list, and be about a world in which the Block never moves.
#
# `proof: domain` therefore means: **follows from the manual's own clauses by
# inspection of the guards, machine-checked nowhere.**  It is a weaker grade
# than `proof: lean` and it is labelled differently so the two cannot be added
# up.  The pack withholds the Lean form rather than emitting the green one.
# ============================================================================

# ---------------------------------------------------------------------------
# Pruning — the invariant, used as a search filter.
#
# `block_unique` says there is exactly one Block in every reachable state.  A
# search node that has lost one, or grown one, is not a state of this world, so
# the planner never has to expand it.  Stated over counts — inside the invariant
# language — and it names no cell, which is what lets it travel.
#
# It is also the entry that would have caught the most expensive way this domain
# could go wrong.  Read `moved(Block, dir)` as `vanished(Block)` plus
# `appeared(Block)` — which is precisely what a segmenter proposes when it loses
# a mover's track (D-A3-003, three times in this family now) — and the count
# breaks on the intermediate state.  The prune is a filter and a tripwire at the
# same time, which is Theoria 1.9's "certificate and heuristic are one object"
# at its cheapest.
prune count(Block) != 1 => dead [proof: domain]

# ---------------------------------------------------------------------------
# Heuristic — admissibility NOT claimed, and the reason is on the record.
#
# "A state whose goal is on the far side of the Block, along the line of travel,
# is at least one shove away."  True, a lower bound of 1, and nearly useless as
# a bound: it is worth something for ordering and nothing for pruning.  A0 and
# A3 both logged this same shape and both refused to overclaim.  No
# `[admissible: …]` until there is a weight function that actually dominates,
# and `lp_potential` is the engine that would have to supply it — which is A1's
# job, not this pack's.
heuristic shove_debt(Cart) [admissible: none]
