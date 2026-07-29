# ============================================================================
# A3 玩法书 — revision 1.  THE SECOND BOOK, AND IT TRAVELS TOO.
#
# Four sentence forms and no others (constraint 10, dsl_grammar v0.1, unchanged
# in v0.2): ordering, pruning, heuristics, preferences.  There is deliberately
# no way to write down a solution here — the anti-cheat rule is in the contract
# and a parser that finds a literal action sequence must reject it.  Level 1's
# 15-step plan and level 2's 9-step plan live in artifacts/plan_*.json, which
# are the planner's output, not this book's content.
#
# ---------------------------------------------------------------------------
# WHY THIS FILE MATTERS TO C3
#
# C3 is stated over *two* books, not one.  A manual that travels while the
# playbook has to be rewritten every level is a much weaker result than the
# claim, so this file is held to the same standard as domain.dsl: it is
# compiled and checked against both levels, and
# tests/test_transfer.py::test_the_playbook_is_byte_identical_across_levels
# asserts the same sha256 both times.
#
# The discipline that makes that possible is the same one that makes the manual
# portable: **every entry is written in the manual's vocabulary and cites the
# manual clause it depends on** — never in coordinates.  `press_before_door`
# names the Door and the Switch, which exist in both levels; it does not name
# (6,7) or (3,1), which exist in one each.  Theoria 1.9's dependency discipline
# is doing double duty here: it was introduced so that changing a clause
# invalidates the entries that rest on it, and it turns out that an entry which
# can only be written that way is also an entry that can be carried.
# ============================================================================

# ---------------------------------------------------------------------------
# Landmark ordering — the theorem-grade entry.
#
# `switch_door_latch` says the Door exists exactly while the Switch shows 7, so
# the Door cell is free only after a press.  Any plan whose goal lies beyond the
# Door must therefore press first.  Relative to domain.dsl this is a THEOREM,
# not a heuristic, and it is the one Lean proves: the invariant is closed under
# every one of the twenty rules and the Door cell's freeness follows from it by
# `decide`.  theory/generated_l1/theory.lean and theory/generated_l2/theory.lean,
# `inv_all`, 0 axioms, in both.
#
# It is worth being exact about what the two Lean files do and do not share.
# The *statement* is the same sentence in both; the *proof* is re-run per level,
# because `decide` enumerates that level's reachable states.  So the playbook
# entry travels and its proof obligation is re-discharged — which is the honest
# shape of the claim, and cheaper than re-deriving the entry: re-checking is
# mechanical, re-deriving needs evidence.
order press_before_door [proof: lean]

# ---------------------------------------------------------------------------
# Pruning — the invariant, used as a search filter.
#
# Any state in which the latch is violated is unreachable, so the planner never
# has to expand one.  This is Theoria 1.9's "certificate and heuristic are one
# object" at its cheapest: the same sentence that discharges the proof
# obligation is the sentence that prunes.  It is stated over counts, which is
# inside the invariant language, and it names no cell.
prune count(Switch, 8) + count(Door) != 1 => dead [proof: lean]

# ---------------------------------------------------------------------------
# Heuristic — admissibility NOT claimed, and the reason is on the record.
#
# "A state from which the goal is on the far side of a present Door is at least
# one press away."  That is a true lower bound of 1 and it is nearly useless as
# a bound; what it is good for is ordering.  A0 logged the same shape and the
# same refusal to overclaim: a 0/1 quantity certifies reachability failures but
# bounds distance only trivially.  No `[admissible: lean]` until there is a
# weight function that actually dominates.
heuristic press_debt(Cart) [admissible: none]

# ---------------------------------------------------------------------------
# The empirical tier has ONE entry and it is at the bottom of the evidence
# ladder, which is exactly where the contract says it belongs.
#
# A0's playbook left this tier empty and said why: a `prefer` entry must carry
# a win-rate or a node account (constraint 5), and one instance yields no k/n.
# A3 has two instances, which is the smallest number that yields one at all —
# so the entry is written, and marked for what it is.  n=2 is not evidence of
# much and the annotation says so rather than letting the bare fraction imply
# more than it earns.  Nothing in A3's results depends on this line.
prefer portal_before_corridor [ev: 2/2 levels, n=2 — indicative only]
