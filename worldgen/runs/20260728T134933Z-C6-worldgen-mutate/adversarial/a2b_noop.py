"""Q2/operators: _apply_one claims it refuses a silent no-op mutation.  Does it?"""
from worldgen.core.world import GridWorld
from worldgen.core import truth, reversibility as rev
from worldgen import mutate
from worldgen.generate import BY_ID

# A `set_prop` whose `to` equals its `from`.  The stale-`from` guard passes.
noop = mutate.Edit(
    base="t1-tokens-lock", edit_family="change_guard",
    operators=({"op": "set_prop", "kind": "lock", "cell": (3, 4),
                "prop": "k", "from": 3, "to": 3},),
    transparent_name="typo", justification="typo", intended_solvable=True)

base_spec = BY_ID["t1-tokens-lock"]
mspec = noop.spec()
print("variant_id:", noop.variant_id)
print("spec identical to base apart from id/labels:",
      mspec.entities == base_spec.entities and mspec.flags == base_spec.flags)

b = GridWorld(base_spec); m = GridWorld(mspec)
det = mutate.earliest_detection(b, m)
print("earliest_detection:", {k: det[k] for k in ("actions", "complete")},
      det.get("note"))
bs = rev.audit(b, truth.rule_table(b)); ms = rev.audit(m, truth.rule_table(m))
print("check_family problems:", mutate.check_family(noop, b, m, bs, ms))
print("--> ships as the corpus's 'observationally equivalent' variant, "
      "passing every gate, with an empty diff.")

# same for move_entity to==from
noop2 = mutate.Edit(
    base="t2-portal-pair", edit_family="move_portal_exit",
    operators=({"op": "move_entity", "kind": "portal", "from": (4, 7), "to": (4, 7)},),
    transparent_name="typo2", justification="typo2", intended_solvable=True)
b2 = GridWorld(BY_ID["t2-portal-pair"]); m2 = GridWorld(noop2.spec())
print("\nmove_entity to==from -> entities identical:",
      noop2.spec().entities == BY_ID["t2-portal-pair"].entities)
d2 = mutate.earliest_detection(b2, m2)
print("earliest_detection:", {k: d2[k] for k in ("actions", "complete")})
bs2 = rev.audit(b2, truth.rule_table(b2)); ms2 = rev.audit(m2, truth.rule_table(m2))
print("check_family problems:", mutate.check_family(noop2, b2, m2, bs2, ms2))
