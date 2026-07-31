"""Variant injection: change exactly one rule, and measure the repair.

Theoria's exam has an item for this — "改一条规则,多快适应回来". The interesting
quantity is not whether the loop recovers (on a world this small it always will)
but *what it costs and what it takes down with it*:

  * **detection latency** — how many actions before the theory is caught out.
    A rule that fires often is caught immediately; a rare one can hide for
    hundreds of actions while the theory keeps replaying perfectly.
  * **repair cost** — the extra evidence needed before the re-mined theory is
    exact again on unseen states, not merely on what was replayed.
  * **collateral** — which *theorems* the change invalidates. `theorem
    unsolvable_mismatch [depends: push2]` is not decoration: if push2 changes,
    the theorem has to be re-examined, and under some variants its verdict flips
    outright. A framework that skipped that step would go on confidently
    declaring a now-solvable level impossible.

The last one is the point. Detection and repair are engineering; a theorem that
silently becomes false is the failure this whole architecture exists to prevent.
"""

import os
import re
import sys
from dataclasses import dataclass, replace
from typing import Any, Dict, List, Optional, Sequence, Tuple

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "engine-rig"))

from pipeline import cross_form, explore, gen_exec, stages     # noqa: E402
from world import levels, sokoban2                             # noqa: E402
from world.sokoban2 import Rules                               # noqa: E402


@dataclass(frozen=True)
class Variant:
    name: str
    rules: Rules
    changed_rule: str          # which rule of the manual this corresponds to
    description: str


VARIANTS: Tuple[Variant, ...] = (
    Variant(
        name="push1",
        rules=Rules(push_distance=1),
        changed_rule="push2",
        description="a push slides the box ONE cell -- the effect changes, and the "
                    "conservation law dies with it",
    ),
    Variant(
        name="push3",
        rules=Rules(push_distance=3),
        changed_rule="push2",
        description="a push slides the box THREE cells -- the effect changes and "
                    "the parity flips on every push",
    ),
    Variant(
        name="nocross",
        rules=Rules(require_crossing_free=False),
        changed_rule="push2",
        description="the box may pass through an obstructed cell -- a guard is "
                    "weakened, the effect is untouched",
    ),
    Variant(
        name="ghost",
        rules=Rules(walls_block_player=False),
        changed_rule="walk",
        description="walls no longer stop the player -- a guard on a very "
                    "frequently fired rule",
    ),
)


def variant_level(level, variant: Variant):
    return replace(level, rules=variant.rules)


# ----------------------------------------------------------- detection

def detection_latency(module: Dict[str, Any], level, max_actions: int = 4000
                      ) -> Dict[str, Any]:
    """Walk the variant world predicting with the OLD theory; when does it break?

    Uses the same deterministic exploration the loop uses, so the number is a
    property of the world and the theory rather than of a lucky action order.
    """
    State, step = module["State"], module["step"]
    episodes = explore.run_episodes(level, explore.plan_episodes(level, per_class=4))
    seen = 0
    for episode_index, episode in enumerate(episodes):
        state = sokoban2.initial_state(level)
        predicted = State(player=state.player, box=state.box)
        for action in episode["actions"]:
            if seen >= max_actions:
                break
            actual, _ = sokoban2.step(level, state, action)
            try:
                predicted_next = step(predicted, action)
            except Exception:
                return {"detected": True, "actions_until_surprise": seen + 1,
                        "episode": episode_index, "action": action,
                        "reason": "the theory could not even predict"}
            seen += 1
            if (predicted_next.player, predicted_next.box) != (actual.player, actual.box):
                return {
                    "detected": True,
                    "actions_until_surprise": seen,
                    "episode": episode_index,
                    "action": action,
                    "predicted": [list(predicted_next.player), list(predicted_next.box)],
                    "observed": [list(actual.player), list(actual.box)],
                }
            state = actual
            predicted = predicted_next
    return {"detected": False, "actions_examined": seen,
            "note": "the changed rule never fired differently in this evidence"}


# --------------------------------------------------------------- collateral

def dependent_theorems(dsl_text: str, changed_rule: str) -> List[str]:
    """Theorems whose `depends:` names the changed rule -- they must be re-examined."""
    out = []
    for match in re.finditer(r"theorem\s+(\w+)[^\[]*\[([^\]]*)\]", dsl_text, re.S):
        name, meta = match.group(1), match.group(2)
        # The bracket holds several `key: value` pairs. Splitting on commas alone
        # swallows the following key -- `depends: push2  probe: passed` parsed as
        # one dependency called "push2  probe", so nothing ever matched.
        fields = re.split(r"\s+(?=\w+:)", meta.strip())
        for field in fields:
            if not field.startswith("depends:"):
                continue
            names = re.split(r"[,\s]+", field[len("depends:"):].strip())
            if changed_rule in [n for n in names if n]:
                out.append(name)
    return out


def parity_still_holds(level) -> bool:
    """Is the conservation law still true in the variant world?"""
    cells = sokoban2.reachable_box_cells(level)
    return len({(r + c) % 2 for r, c in cells}) == 1


# ------------------------------------------------------------------ repair

def repair(variant: Variant, per_class: int = 4) -> Dict[str, Any]:
    """Re-explore and re-mine on the variant; is the new theory exact?"""
    evidence_levels = [variant_level(lv, variant) for lv in levels.EVIDENCE_LEVELS]
    transitions: List = []
    actions = 0
    for level in evidence_levels:
        evidence = explore.evidence_set(level, per_class=per_class)
        actions += evidence["action_budget_spent"]
        transitions.extend(stages.transitions_from_episodes(evidence["episodes"]))
    rules, mine_account = stages.mine_with_account(transitions)
    certificate = stages.certify(rules, transitions)

    pushes = {}
    for rule in rules:
        if rule.name.startswith("push2"):
            pushes[rule.name] = sorted(a.name for a in rule.guard)

    # E14 (adversarial review, correction 3): `replay_exact` and
    # `exactly_one_successor` are the coverage and no-violation claims of this
    # block, and they are computed by replaying the transitions through rules
    # the miner produced. If the miner crashed, those rules are whatever
    # `learn_dnf` happened to emit on the way past the exception, so the claims
    # are about that accident and not about the variant. The first version of
    # this change put the crash count *beside* them and left them true, which
    # is exactly the "adjacent but not gated" failure the ticket exists to fix.
    searched = mine_account.all_guards_searched
    return {
        "evidence_actions": actions,
        "transitions": len(transitions),
        "n_rules": len(rules),
        "synthesis_crashes": mine_account.synthesis_crashes,
        "all_guards_searched": searched,
        "replay_exact": bool(certificate["replay_exact"]) and searched,
        "exactly_one_successor": (bool(certificate["exactly_one_successor"])
                                  and searched),
        "replay_exact_before_crash_gate": bool(certificate["replay_exact"]),
        "exactly_one_successor_before_crash_gate": bool(
            certificate["exactly_one_successor"]),
        "error": (None if searched else
                  "synthesis raised %d time(s) (%s); the rules these claims "
                  "were replayed through are a crash artefact"
                  % (mine_account.synthesis_crashes,
                     ", ".join("%s x%d" % (k, v) for k, v
                               in sorted(mine_account.by_type.items())))),
        "push_guards": pushes,
        "push_effects": sorted(
            {str(r.effect[1]) for r in rules if r.name.startswith("push2")}
        ),
    }


def detection_across_levels(dsl_text: str, variant: Variant) -> Dict[str, Any]:
    """Where you look changes whether you notice at all.

    A guard weakening is invisible until you stand somewhere the old and new
    guards disagree, and the base level can make that configuration unreachable
    (the same parity argument as THEORIZE_LOG T-9). So latency is reported per
    level, not as one number.
    """
    per_level = {}
    for base_level in levels.EVIDENCE_LEVELS:
        level = variant_level(base_level, variant)
        module = gen_exec.compile_module(
            dsl_text, level.height, level.width, level.walls)
        outcome = detection_latency(module, level)
        per_level[base_level.name] = (
            outcome["actions_until_surprise"] if outcome["detected"] else None
        )
    found = [v for v in per_level.values() if v is not None]
    return {
        "per_level": per_level,
        "detected_anywhere": bool(found),
        "earliest": min(found) if found else None,
        "levels_that_never_notice": sorted(
            k for k, v in per_level.items() if v is None
        ),
    }


def run_variant(variant: Variant, base_module: Dict[str, Any],
                dsl_text: str) -> Dict[str, Any]:
    level = variant_level(levels.MATCH, variant)
    mismatch = variant_level(levels.MISMATCH, variant)

    detection = detection_latency(base_module, level)
    across = detection_across_levels(dsl_text, variant)
    theorems = dependent_theorems(dsl_text, variant.changed_rule)
    law_holds = parity_still_holds(level)
    still_unsolvable = sokoban2.solve_bfs(mismatch) is None

    return {
        "variant": variant.name,
        "description": variant.description,
        "changed_rule": variant.changed_rule,
        "detection": detection,
        "detection_across_levels": across,
        "invalidated_theorems": theorems,
        "conservation_law_still_true": law_holds,
        "mismatch_still_unsolvable": still_unsolvable,
        # The old theory's verdict was "unsolvable". Is it still right?
        "old_verdict_still_correct": still_unsolvable,
        "silently_wrong_without_dependency_tracking": (
            not still_unsolvable and bool(theorems)
        ),
        "repair": repair(variant),
    }


def main() -> int:
    import json

    result = run_all()
    path = os.path.join(HERE, "artifacts", "adaptation.json")
    with open(path, "w", encoding="utf-8", newline="") as fh:
        json.dump(result, fh, indent=2, sort_keys=True)
        fh.write("\n")

    print("A0 variant injection -- change one rule, measure the repair")
    print("-" * 78)
    print("  %-9s %-14s %-11s %-21s %s" % (
        "variant", "detect(match)", "detect(any)", "theorems hit", "verdict"))
    for entry in result["variants"]:
        detection = entry["detection"]
        across = entry["detection_across_levels"]
        print("  %-9s %-14s %-11s %-21s %s" % (
            entry["variant"],
            ("%d acts" % detection["actions_until_surprise"]) if detection["detected"]
            else "never",
            ("%d acts" % across["earliest"]) if across["detected_anywhere"] else "never",
            ",".join(entry["invalidated_theorems"]) or "none",
            "STILL CORRECT" if entry["old_verdict_still_correct"] else "** FLIPPED **"))
    print("-" * 78)
    # E14: the crash column, and the exit code that reads it. A table with no
    # crash column cannot tell a repaired theory from a miner that fell over.
    crashed = [e for e in result["variants"]
               if not e["repair"]["all_guards_searched"]]
    for entry in result["variants"]:
        r = entry["repair"]
        print("  repair %-9s synthesis_crashes=%-3d all_guards_searched=%-5s "
              "replay_exact=%-5s exactly_one_successor=%s"
              % (entry["variant"], r["synthesis_crashes"],
                 r["all_guards_searched"], r["replay_exact"],
                 r["exactly_one_successor"]))
        if r.get("error"):
            print("     !! %s" % r["error"])
    print("-" * 78)
    for entry in result["variants"]:
        if entry["silently_wrong_without_dependency_tracking"]:
            print("  %s: the old theory still calls `mismatch` unsolvable, and it is now"
                  % entry["variant"])
            print("     solvable. Caught only by [depends: %s] on theorem %s."
                  % (entry["changed_rule"], entry["invalidated_theorems"][0]))
    print("  -> %s" % path)
    if crashed:
        print("  FAILED: %d variant(s) re-mined through a crashed synthesis; "
              "their repair verdicts say nothing about the variant."
              % len(crashed))
        return 1
    return 0


def run_all(dsl_path: Optional[str] = None) -> Dict[str, Any]:
    dsl_path = dsl_path or os.path.join(HERE, "theory", "theory.dsl")
    dsl_text = open(dsl_path, encoding="utf-8").read()
    base = levels.MATCH
    base_module = gen_exec.compile_module(
        dsl_text, base.height, base.width, base.walls
    )
    return {
        "variants": [run_variant(v, base_module, dsl_text) for v in VARIANTS],
    }
