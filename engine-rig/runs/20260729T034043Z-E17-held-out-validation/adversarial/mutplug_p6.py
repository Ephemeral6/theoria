"""P6: the three E17 rate probes read `value_hit` instead of `delta_hit`.

The published provenance string is left byte-identical, so the only thing that
could catch this mutant is a digit changing.
"""
from tools import engine_table as et
SPEC = [("ho.zs_s1_global", "Z-S1/global", "100.0"),
        ("ho.zs_s2_global", "Z-S2/global", "13.1"),
        ("ho.zs_s2_local", "Z-S2/cell_local", "92.9")]
for key, bucket, expect in SPEC:
    def _mk(bucket=bucket):
        def _probe():
            d = et._load_json(f"{et.E17}/results.json")
            row = d["zero_space"]["splits"][bucket]
            return "%.1f" % (100.0 * row["value_hit"] / row["laws"])
        _probe.where = (f"{et.E17}/results.json :: "
                        f"zero_space.splits['{bucket}'] delta_hit/laws")
        return _probe
    et.FACTS[key] = (expect, _mk())
