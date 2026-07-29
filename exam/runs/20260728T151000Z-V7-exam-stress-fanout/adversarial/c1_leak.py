"""Adversarial re-derivation of Claim 1: the leak gate refuses 20/20, 236/236."""
import json, collections, sys

from exam.papers import heldout_worldgen as hw, worldgen_port as port
from exam.grading.registry import digest
from exam import leakage
from exam.model import canonical, LeakageError

d = digest()
worlds_leaking = 0
worlds_total = 0
items_total = 0
probe_hit_items = 0
structural_hit_items = 0
metadata_findings = 0
per_check = collections.Counter()
probe_strings = collections.Counter()
# which probe caused the hit, and would it still hit if tags were removed?
hit_cause = collections.Counter()
no_tag_hits = 0
detail = []

for w in port.world_ids():
    worlds_total += 1
    paper = hw.build_for(w, 2)
    sheet = paper.sheet(d)
    key_doc = paper.key(d)
    try:
        leakage.check_paper(paper, sheet, key_doc=key_doc)
        leaks = False
    except LeakageError:
        leaks = True
    worlds_leaking += leaks

    sheet_text = canonical(sheet)
    w_items = 0
    w_probe = 0
    for it in paper.items:
        items_total += 1
        w_items += 1
        hits = leakage.probe_hits(sheet_text, it.leak_probes)
        if hits:
            probe_hit_items += 1
            w_probe += 1
            for h in hits:
                probe_strings[h] += 1
        if leakage.structural_hits(it):
            structural_hit_items += 1
        # counterfactual: what if 'tags' were stripped from the sheet side?
        ss = dict(it.sheet_side())
        ss.pop("tags", None)
        # rebuild a sheet-wide text without tags
    # sheet without any tags at all
    sheet2 = json.loads(canonical(sheet))
    def strip_tags(node):
        if isinstance(node, dict):
            return {k: strip_tags(v) for k, v in node.items() if k != "tags"}
        if isinstance(node, list):
            return [strip_tags(v) for v in node]
        return node
    sheet2_text = canonical(strip_tags(sheet2))
    w_notag = 0
    for it in paper.items:
        if leakage.probe_hits(sheet2_text, it.leak_probes):
            w_notag += 1
    no_tag_hits += w_notag
    detail.append({"world": w, "leaks": leaks, "items": w_items,
                   "probe_hit_items": w_probe, "probe_hits_without_tags": w_notag})

print(json.dumps({
    "worlds_total": worlds_total,
    "worlds_leaking": worlds_leaking,
    "items_total": items_total,
    "items_with_probe_hit": probe_hit_items,
    "items_with_structural_hit": structural_hit_items,
    "items_with_probe_hit_after_removing_tags": no_tag_hits,
    "probe_strings_top": probe_strings.most_common(20),
    "per_world": detail,
}, indent=2))
