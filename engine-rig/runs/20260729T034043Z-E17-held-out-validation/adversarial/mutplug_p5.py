"""P5: the ho.zs_s2_k3 probe averages per-setting percentages instead of pooling."""
from tools import engine_table as et
def _probe():
    d = et._load_json(f"{et.E17}/results.json")
    rows = [v for k, v in d["zero_space"]["splits"].items()
            if k.startswith("Z-S2/global/") and k.endswith("-k3")]
    rates = [100.0 * r["delta_hit"] / r["laws"] for r in rows if r["laws"]]
    return "%.1f" % (sum(rates) / len(rates))
_probe.where = "MUTANT p5"
et.FACTS["ho.zs_s2_k3"] = ("22.9", _probe)
