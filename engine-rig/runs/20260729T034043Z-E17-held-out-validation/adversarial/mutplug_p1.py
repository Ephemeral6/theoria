"""P1: the ho.zs_s1_global probe divides by the wrong denominator (laws+1)."""
from tools import engine_table as et
def _probe():
    d = et._load_json(f"{et.E17}/results.json")
    row = d["zero_space"]["splits"]["Z-S1/global"]
    return "%.1f" % (100.0 * row["delta_hit"] / (row["laws"] + 1))
_probe.where = "MUTANT p1"
et.FACTS["ho.zs_s1_global"] = ("100.0", _probe)
