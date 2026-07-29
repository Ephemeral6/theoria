"""Q6: does check_family's reversible_to_irreversible test discriminate anything?

Relabel every edit in the corpus as reversible_to_irreversible and see which
ones the check would wave through.
"""
from dataclasses import replace
from worldgen.core import truth, reversibility as rev
from worldgen.core.world import GridWorld
from worldgen import mutate

print("%-12s %-28s %-28s %s" % ("id", "declared", "relabelled r2i?", "why"))
accepted = []
for eid, edit in sorted(mutate.MUTANT_BY_ID.items()):
    b = GridWorld(mutate.BY_ID[edit.base]); m = GridWorld(edit.spec())
    bs = rev.audit(b, truth.rule_table(b)); ms = rev.audit(m, truth.rule_table(m))
    fake = replace(edit, edit_family="reversible_to_irreversible")
    probs = mutate.check_family(fake, b, m, bs, ms)
    lost = sorted(n for n, r in bs["rules"].items() if r["re_witnessable"]
                  and not ms["rules"].get(n, {"re_witnessable": False})["re_witnessable"])
    gained = sorted(n for n, r in ms["rules"].items()
                    if r["single_witness"] and n not in bs["rules"])
    ok = not probs
    if ok and edit.edit_family != "reversible_to_irreversible":
        accepted.append(eid)
    print("%-12s %-28s %-28s lost=%s gained_single=%s"
          % (eid, edit.edit_family, "ACCEPTED" if ok else "rejected", lost, gained))

print("\nNon-r2i edits the r2i test would accept:", accepted)

# and the reverse: relabel the three real r2i edits as change_guard / forbid_action
print()
for eid in sorted(mutate.MUTANT_BY_ID):
    edit = mutate.MUTANT_BY_ID[eid]
    if edit.edit_family != "reversible_to_irreversible":
        continue
    b = GridWorld(mutate.BY_ID[edit.base]); m = GridWorld(edit.spec())
    bs = rev.audit(b, truth.rule_table(b)); ms = rev.audit(m, truth.rule_table(m))
    for fam in mutate.EDIT_FAMILIES:
        probs = mutate.check_family(replace(edit, edit_family=fam), b, m, bs, ms)
        print("%-12s as %-28s %s" % (eid, fam, "ACCEPTED" if not probs else "rejected"))
