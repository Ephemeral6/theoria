"""Adjudication — the pre-registered rules, run over the attacks that landed.

Every field a verdict depends on is *derived*: the value comes from
`battery.metrics.evaluate`, the poverty certificate from `check.py` reading the
builder's source, the threshold from `prereg.TARGETS`.  The attacker supplies
only `claim`, `accidental` and `rationale` — and `accidental` is the one
judgement the pre-registration admits cannot be measured from a `Run`.

Three asymmetries, all fixed in `PREREG_V9.md` before any attack ran:

* **R1 — V9 demotes, V9 does not promote.**  "I could not break it" is not a
  reason to move a metric into the main table; that is process 1's job.  This
  is the rule that stops the audit from being a circle in which whatever the
  attackers happened to think of decides the table.
* **R2 — a defence that promotes costs double.**  If a V9 defence would move a
  metric back to `main`, the defence must carry more attack variants than
  tests, and the variants must reach past the tested condition.  Otherwise the
  metric stays in `reference` and the report says why.
* **R3 — a demotion names a run and a number.**  No prose-only demotions.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Dict, List, Optional

from battery.audit.v9 import prereg
from battery.audit.v9.attack import Attack
from battery.audit.v9.check import certificate
from battery.metrics import REGISTRY, evaluate


def _value(run) -> Dict[str, object]:
    """One metric on one adversarial run, as plain data."""
    return run


_ATTACKS: Optional[Dict[str, List[Attack]]] = None
_JUDGED: Dict[str, Dict[str, object]] = {}


def collect_attacks() -> Dict[str, List[Attack]]:
    """Every blind attack on disk, grouped by metric.

    Discovered by name (`attack_*`) across `battery/audit/v9/attacks/`, so an
    attack that exists but was never registered cannot exist.  Six attackers
    wrote these independently and none of them saw another's module; a metric
    therefore carries as many attacks as were found for it, and none is
    dropped.  `battery/audit/exploits/collect()` learned that lesson the hard
    way by keying a flat dict and silently keeping whichever arrived last.
    """
    global _ATTACKS
    if _ATTACKS is not None:
        return _ATTACKS

    from battery.audit.v9 import attacks as package

    found: Dict[str, List[Attack]] = {}
    for module in package.MODULES:
        for name in sorted(dir(module)):
            if not name.startswith("attack_"):
                continue
            attribute = getattr(module, name)
            if not callable(attribute):
                continue
            attack = attribute()
            if isinstance(attack, Attack):
                found.setdefault(attack.metric_id, []).append(attack)
    _ATTACKS = {k: sorted(v, key=lambda a: a.name)
                for k, v in sorted(found.items())}
    return _ATTACKS


def judge(attack: Attack) -> Dict[str, object]:
    """S1/S2/S3 for one attack.  Nothing here is taken on the author's word.

    Memoised on `(metric_id, name)`.  The attacks are deterministic by
    construction -- C1 of the poverty certificate is exactly that property --
    so a cached verdict is the same verdict, and some of these runs are very
    large on purpose.
    """
    key = "%s/%s" % (attack.metric_id, attack.name)
    if key in _JUDGED:
        return _JUDGED[key]
    card = REGISTRY.get(attack.metric_id)
    if card is None:
        return {"metric": attack.metric_id, "name": attack.name,
                "accidental": False, "succeeded": False,
                "error": "unregistered metric"}

    run = attack.build()
    value = evaluate(run)[attack.metric_id]
    cert = certificate(attack.build)

    s1 = bool(value.ok and value.value is not None)
    row: Dict[str, object] = {
        "metric": attack.metric_id,
        "name": attack.name,
        "direction": card.direction,
        "claim": attack.claim,
        "accidental": bool(attack.accidental),
        "rationale": attack.rationale,
        "status": value.status,
        "value": value.value,
        "reason": value.reason,
        "target": prereg.target_for(attack.metric_id),
        "certificate": cert,
        "S1_metric_answered": s1,
        "S3_poverty_certified": bool(cert["ok"]),
    }

    if card.direction == "neutral":
        # §1.1 — controllability, not "better".
        low_value = None
        low_cert: Optional[Dict[str, object]] = None
        if attack.build_low is not None:
            low = evaluate(attack.build_low())[attack.metric_id]
            low_value = low.value
            low_cert = certificate(attack.build_low)
            row["low_status"] = low.status
        row["low_value"] = low_value
        row["low_certificate"] = low_cert
        row["benign_window"] = attack.benign_window
        s2 = prereg.controllable(low_value, value.value)
        s1 = s1 and low_value is not None
        row["S1_metric_answered"] = s1
        row["S3_poverty_certified"] = bool(
            cert["ok"] and (low_cert or {}).get("ok", False))
    else:
        s2 = prereg.meets(attack.metric_id, card.direction, value.value)

    row["S2_reached_target"] = bool(s2)
    row["succeeded"] = bool(s1 and s2 and row["S3_poverty_certified"])
    if attack.notes:
        row["notes"] = attack.notes
    _JUDGED[key] = row
    return row


# --- defences landed by V9 -------------------------------------------------
#
# `implemented` means the code in `battery/` refuses the attack, not that a
# defence is imaginable.  `mutants` / `tests` are counted from disk by
# `battery/tests/test_v9_defences.py`, not typed here; the numbers below are
# the *claim*, and the test fails if the claim outruns the files.
#
# Three defences, each closing a *class* of blind attack rather than one
# attack.  None of the three is claimed to make its metrics safe: D1 stops a
# metric reporting a share of 7.0 and does nothing about a share of 1.0
# asserted by a producer who did no work.  That is the honest ceiling of a
# defence written inside a passive instrument, and it is why most of these
# metrics stay in the reference tier with a defence landed.
DEFENCE_OF: Dict[str, str] = {
    "K1": "D1", "K2": "D1", "K4": "D1", "K8": "D1", "K12": "D1", "M6": "D1",
    "M1": "D2", "M4": "D2",
    "E1": "D3", "E2": "D3", "E3": "D3", "E5": "D3",
}

DEFENCES: Dict[str, str] = {
    "D1": ('a value declared unit="share" may not exceed one, and a numerator '
           'may not exceed its denominator; such a record is refused as '
           'incoherent rather than reported as excellent'),
    "D2": ("a first-use or detection delay may not be negative; a mechanism "
           "used before it was visible is two counters with different "
           "origins, not a fast arm"),
    "D3": ("an unpriced model call is not a free one: the economy family "
           "refuses a partial bill instead of reading `cost_usd or 0.0`"),
}

V9_DEFENCES: Dict[str, Dict[str, object]] = {
    metric_id: {"defence_id": defence_id,
                "defence": DEFENCES[defence_id],
                "implemented": True}
    for metric_id, defence_id in DEFENCE_OF.items()
}


_DEMOTIONS: Optional[Dict[str, Dict[str, object]]] = None


def v9_demotions() -> Dict[str, Dict[str, object]]:
    """Metrics the blind round demotes, with the run and number that did it.

    Deliberately importable **without** touching `battery/audit/gaming.py`:
    `gaming.tier_of` consults this, so a cycle here would be a cycle in the
    battery's own tier decision.  `adjudicate()` is the richer view and may
    import gaming freely.

    Returning the worst landed attack per metric rather than a bare set,
    because `PREREG_V9.md` R3 says a demotion has to name a run and a value.

    A standing V9 defence buys no exemption here.  `judge` recomputes against
    the live metric, so an attack that D1/D2/D3 closes has already stopped
    landing; one that still lands is one the defence does not reach, and
    excusing it because *some* defence exists for the metric is how a defence
    turns into a promotion it did not earn.
    """
    global _DEMOTIONS
    if _DEMOTIONS is not None:
        return _DEMOTIONS
    out: Dict[str, Dict[str, object]] = {}
    for metric_id, group in collect_attacks().items():
        landed = [j for j in (judge(a) for a in group) if j.get("succeeded")]
        accidental = [j for j in landed if j["accidental"]]
        if not accidental:
            continue
        worst = sorted(accidental, key=lambda j: j["name"])[0]
        out[metric_id] = {
            "attack": worst["name"],
            "value": worst["value"],
            "target": worst["target"],
            "claim": worst["claim"],
        }
    _DEMOTIONS = out
    return out


@lru_cache(maxsize=1)
def _r2_counts_cached() -> str:
    import json
    return json.dumps(_r2_counts_uncached(), sort_keys=True)


def r2_counts() -> Dict[str, Dict[str, int]]:
    import json
    return json.loads(_r2_counts_cached())


def _r2_counts_uncached() -> Dict[str, Dict[str, int]]:
    """Mutants and tests per defence, **counted from disk**.

    Not typed into a table.  R2 is a discipline about two files, and a
    discipline that reads a number its own author wrote would be one more
    unfalsifiable boolean of the kind this package exists to remove.
    """
    import os
    import re

    from battery.audit.v9 import mutants as mutant_module

    counts = mutant_module.counts()
    tests_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))),
        "tests", "test_v9_defences.py")
    try:
        with open(tests_path, encoding="utf-8") as fh:
            names = re.findall(r"^def (test_D\d)_", fh.read(), re.MULTILINE)
    except OSError:                                   # pragma: no cover
        names = []
    return {defence_id: {"mutants": counts.get(defence_id, 0),
                         "tests": sum(1 for n in names
                                      if n == "test_%s" % defence_id)}
            for defence_id in sorted(DEFENCES)}


def _r2_satisfied(metric_id: str) -> bool:
    """§3 R2 — more attack variants than tests, or the promotion is refused."""
    defence = V9_DEFENCES.get(metric_id)
    if not defence or not defence.get("implemented"):
        return False
    counts = r2_counts().get(str(defence["defence_id"]), {})
    return counts.get("mutants", 0) > counts.get("tests", 0)


def adjudicate() -> Dict[str, object]:
    """The V9 verdict table."""
    from battery.audit.gaming import tier_before_v9 as prior_tier_of

    attacks = collect_attacks()
    rows: Dict[str, object] = {}
    demoted: List[str] = []
    held: List[str] = []
    not_gameable: List[str] = []
    unattacked = sorted(set(REGISTRY) - set(attacks))

    for metric_id in sorted(REGISTRY):
        prior = prior_tier_of(metric_id)
        judged = [judge(a) for a in attacks.get(metric_id, [])]
        landed = [j for j in judged if j.get("succeeded")]
        # The worst surviving case decides: a metric is only as safe as its
        # most dangerous live attack.
        gameable = bool(landed)
        accidental = any(j["accidental"] for j in landed)
        defence = V9_DEFENCES.get(metric_id)
        defended = bool(defence and defence.get("implemented"))

        # `NOT defended` in the pre-registered formula is not a per-metric
        # flag, and reading it as one is a live bug rather than a hypothetical:
        # it promoted K12 and E2 into the main table on the strength of a
        # defence that closes a *different* attack from the one still landing.
        #
        # An attack that still lands after the defence shipped **is** an
        # undefended attack, by construction — `judge` recomputes `succeeded`
        # against the live metric, so anything D1/D2/D3 actually closes has
        # already dropped out of `landed`. So the formula collapses: whatever
        # survives here is gameable and undefended, and the standing defence
        # only earns a metric its tier back when nothing accidental survives.
        if gameable and accidental:
            v9_tier = "reference"
        else:
            v9_tier = "main"

        # R1 — V9 never promotes on "I could not break it".
        promoted_by_silence = (v9_tier == "main" and prior == "reference"
                               and not _r2_satisfied(metric_id))
        if promoted_by_silence:
            v9_tier = "reference"

        row = {
            "prior_tier": prior,
            "v9_tier": v9_tier,
            "attacks": judged,
            "n_attacks": len(judged),
            "n_landed": len(landed),
            "gameable": gameable,
            "accidental_if_gameable": accidental,
            "defended_by_v9": defended,
            "r2_satisfied": _r2_satisfied(metric_id),
            "defence": defence,
            "R1_promotion_refused": promoted_by_silence,
        }
        if not judged:
            row["note"] = "no blind attack was written for this metric"
        elif not landed:
            row["note"] = ("attacked and not broken; see each attack's "
                           "`reason` for the guard that refused it")
        rows[metric_id] = row

        if gameable and prior == "main" and v9_tier == "reference":
            demoted.append(metric_id)
        elif gameable:
            held.append(metric_id)
        elif judged:
            not_gameable.append(metric_id)

    return {
        "rule": ("S1 metric answered AND S2 reached the pre-registered target "
                 "AND S3 poverty certificate passed -> gameable. "
                 "gameable AND accidental AND NOT defended -> reference. "
                 "R1: V9 never promotes on silence. R2: a defence that would "
                 "promote needs more attack variants than tests."),
        "prereg_targets": prereg.TARGETS,
        "n_metrics": len(REGISTRY),
        "n_attacked": len(attacks),
        "n_attacks": sum(len(v) for v in attacks.values()),
        "unattacked": unattacked,
        "gameable": sorted(m for m in rows if rows[m]["gameable"]),
        "not_gameable": sorted(not_gameable),
        "demoted_by_v9": sorted(demoted),
        "gameable_but_held": sorted(held),
        "main": sorted(m for m in rows if rows[m]["v9_tier"] == "main"),
        "reference": sorted(m for m in rows if rows[m]["v9_tier"] == "reference"),
        "metrics": rows,
    }


def disagreements_with_b14() -> List[Dict[str, object]]:
    """Where the blind round and the sighted round part company.

    Agreement is weak evidence — the same hole found twice.  A disagreement is
    the finding: either B14's sighted attackers saw something the blind ones
    could not reach, or the blind ones reached something the register never
    named.
    """
    from battery.audit.gaming import tier_before_v9 as prior_tier_of

    table = adjudicate()
    out: List[Dict[str, object]] = []
    for metric_id, row in sorted(table["metrics"].items()):
        prior = prior_tier_of(metric_id)
        if row["v9_tier"] != prior:
            out.append({
                "metric": metric_id,
                "b14_tier": prior,
                "v9_tier": row["v9_tier"],
                "v9_gameable": row["gameable"],
                "n_landed": row["n_landed"],
                "why": row.get("note", ""),
            })
    return out
