"""Does the injected interleaving spare a race-FREE _emit_spec? It must, or the
strict xfail can never flip. Two candidate fixes, both run against the same
injection the pinning test uses."""
import json, os, tempfile
from exam.model import sha256_text, write_json
from exam.papers import verdict as V
from proxy.variants import Variant

spec = json.load(open(os.path.join(V.SPEC_DIR, "a2var-i1-atrium-nodown.json"),
                      encoding="utf-8"))
tmp = tempfile.mkdtemp()
V.SPEC_DIR = tmp
shared = os.path.join(tmp, spec["variant_id"] + ".json")
orig = Variant.load

def load_while_a_competitor_truncates(path):
    if os.path.exists(shared):
        open(shared, "w", encoding="utf-8").close()
    return orig(path)
Variant.load = staticmethod(load_while_a_competitor_truncates)

def fix_a_validate_in_memory(spec):
    """No read-back at all."""
    loaded = Variant(spec)
    path = os.path.join(V.SPEC_DIR, "%s.json" % spec["variant_id"])
    write_json(path, spec)
    return {"variant_id": loaded.variant_id, "operators": [o["op"] for o in loaded.operators]}

def fix_b_private_readback(spec):
    """Read back from a path no other builder knows about."""
    Variant(spec)
    path = os.path.join(V.SPEC_DIR, "%s.json" % spec["variant_id"])
    write_json(path, spec)
    private = os.path.join(tempfile.mkdtemp(), "%s.json" % spec["variant_id"])
    write_json(private, spec)
    loaded = Variant.load(private)
    return {"variant_id": loaded.variant_id, "operators": [o["op"] for o in loaded.operators]}

for name, fn in (("current _emit_spec", V._emit_spec),
                 ("fix A: validate in memory", fix_a_validate_in_memory),
                 ("fix B: private read-back", fix_b_private_readback)):
    try:
        print("%-28s -> OK  %s" % (name, fn(spec)["variant_id"]))
    except Exception as e:
        print("%-28s -> %s: %s" % (name, type(e).__name__, str(e)[:60]))
