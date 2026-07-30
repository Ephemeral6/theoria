import json

M = []


def m(name, *edits):
    M.append({"name": name, "edits": [list(e) for e in edits]})


T = "core/truth.py"
B = "build.py"
SD = "mechanisms/switch_door.py"
CL = "mechanisms/count_lock.py"
CS = "mechanisms/consumable.py"
SB = "tests/invariant_sandbox.py"

HOLDS_BRANCH = ('        if (status == INV_HOLDS and row.get("verified") is True\n'
                '                and row.get("holds") is True):\n'
                '            holds.append(name)\n')
VIOL_BRANCH = ('        elif status == INV_VIOLATED or (row.get("verified") is True\n'
               '                                        and row.get("holds") is False):\n'
               '            violated.append(name)\n')
SINK = '        else:\n            unverified.append(name)\n'
CLASSIFY_RET = ('    return {INV_HOLDS: holds, INV_VIOLATED: violated, '
                'INV_UNVERIFIED: unverified}\n')
ALLHOLD = ('    status = classify_invariants(invariants)\n'
           '    return not status[INV_VIOLATED] and not status[INV_UNVERIFIED]\n')

# --- A: classify_invariants -------------------------------------------------
m("A01-holds-key-optimistic-default", [T, HOLDS_BRANCH,
  HOLDS_BRANCH.replace('row.get("holds") is True', 'row.get("holds", True) is True')])
m("A02-holds-ignores-status", [T, HOLDS_BRANCH,
  '        if (row.get("verified") is True\n'
  '                and row.get("holds") is True):\n'
  '            holds.append(name)\n'])
m("A03-holds-ignores-verified", [T, HOLDS_BRANCH,
  '        if (status == INV_HOLDS\n'
  '                and row.get("holds") is True):\n'
  '            holds.append(name)\n'])
m("A04-truthy-not-identity", [T, HOLDS_BRANCH,
  HOLDS_BRANCH.replace('row.get("verified") is True', 'bool(row.get("verified"))')
              .replace('row.get("holds") is True', 'bool(row.get("holds"))')])
m("A05-sink-to-holds", [T, SINK,
  '        else:\n            holds.append(name)\n'])
m("A06-sink-to-violated", [T, SINK,
  '        else:\n            violated.append(name)\n'])
m("A07-drop-status-violated-clause", [T, VIOL_BRANCH,
  '        elif (row.get("verified") is True\n'
  '                                        and row.get("holds") is False):\n'
  '            violated.append(name)\n'])
m("A08-drop-verified-violated-clause", [T, VIOL_BRANCH,
  '        elif status == INV_VIOLATED:\n'
  '            violated.append(name)\n'])
m("A09-nameless-rows-vanish", [T, '        name = row.get("name", "<unnamed>")\n',
  '        if "name" not in row:\n            continue\n'
  '        name = row.get("name", "<unnamed>")\n'])
m("A10-unverified-list-emptied-at-return", [T, CLASSIFY_RET,
  '    return {INV_HOLDS: holds, INV_VIOLATED: violated, INV_UNVERIFIED: []}\n'])
m("A11-violated-list-emptied-at-return", [T, CLASSIFY_RET,
  '    return {INV_HOLDS: holds, INV_VIOLATED: [], INV_UNVERIFIED: unverified}\n'])
m("A12-violated-and-unverified-swapped", [T, CLASSIFY_RET,
  '    return {INV_HOLDS: holds, INV_VIOLATED: unverified, INV_UNVERIFIED: violated}\n'])

# --- B: all_invariants_hold -------------------------------------------------
m("B01-all-hold-ignores-unverified", [T, ALLHOLD,
  '    status = classify_invariants(invariants)\n'
  '    return not status[INV_VIOLATED]\n'])
m("B02-all-hold-ignores-violated", [T, ALLHOLD,
  '    status = classify_invariants(invariants)\n'
  '    return not status[INV_UNVERIFIED]\n'])
m("B03-all-hold-always-true", [T, ALLHOLD,
  '    classify_invariants(invariants)\n    return True\n'])

# --- C: check_invariants ----------------------------------------------------
PROSE = ('            row["verified"] = False\n'
         '            row["status"] = INV_UNVERIFIED\n'
         '            row["note"] = ("prose only — no callable check, so this claim is "\n'
         '                           "unverified, which is not the same as true")\n')
m("C01-prose-branch-reports-holds", [T, PROSE,
  '            row["verified"] = True\n'
  '            row["holds"] = True\n'
  '            row["status"] = INV_HOLDS\n'
  '            row["note"] = ("prose only")\n'])
m("C02-prose-branch-drops-status-stamp", [T, PROSE,
  '            row["verified"] = False\n'
  '            row["note"] = ("prose only — no callable check, so this claim is "\n'
  '                           "unverified, which is not the same as true")\n'])
m("C03-vacuity-guard-disabled", [T,
  '        if not violations and evidence == 0:\n',
  '        if False and not violations and evidence == 0:\n'])
m("C04-vacuity-guard-states-only", [T, '            evidence += len(states)\n',
  '            evidence += 0\n'])
m("C05-vacuity-guard-edges-not-counted", [T, '            evidence += edges\n',
  '            evidence += 0\n'])
m("C06-edge-check-never-runs", [T,
  '        if edge_check is not None and len(violations) < 3:\n',
  '        if edge_check is not None and len(violations) < 3 and False:\n'])
m("C07-edge-loop-first-transition-only", [T,
  '            for prev, action, nxt, _rule in world.transitions(states):\n',
  '            for prev, action, nxt, _rule in list(world.transitions(states))[:1]:\n'])
m("C08-state-loop-first-state-only", [T, '            for state in states:\n',
  '            for state in states[:1]:\n'])
m("C09-holds-hardcoded-true", [T, '        row["holds"] = not violations\n',
  '        row["holds"] = True\n'])
m("C10-status-hardcoded-holds", [T,
  '        row["status"] = INV_VIOLATED if violations else INV_HOLDS\n',
  '        row["status"] = INV_HOLDS\n'])
m("C11-status-hardcoded-violated", [T,
  '        row["status"] = INV_VIOLATED if violations else INV_HOLDS\n',
  '        row["status"] = INV_VIOLATED\n'])
m("C12-check-exception-swallowed", [T,
  '                except Exception as exc:\n'
  '                    violations.append({"state": list(state.key()), "error": repr(exc)})\n'
  '                    break\n',
  '                except Exception:\n'
  '                    continue\n'])
m("C13-edge-exception-swallowed", [T,
  '                except Exception as exc:\n'
  '                    violations.append({"state": list(prev.key()), "action": action,\n'
  '                                       "next": list(nxt.key()), "error": repr(exc)})\n'
  '                    break\n',
  '                except Exception:\n'
  '                    continue\n'])
m("C14-states-checked-misreported", [T, '            row["states_checked"] = len(states)\n',
  '            row["states_checked"] = 0\n'])
m("C15-transitions-checked-misreported", [T, '            row["transitions_checked"] = edges\n',
  '            row["transitions_checked"] = 0\n'])
m("C16-verified-stamp-false", [T, '        row["verified"] = True\n        row["holds"]',
  '        row["verified"] = False\n        row["holds"]'])
m("C17-edge-violations-not-recorded", [T,
  '                if not ok:\n'
  '                    violations.append({"state": list(prev.key()), "action": action,\n'
  '                                       "next": list(nxt.key())})\n'
  '                    if len(violations) >= 3:\n'
  '                        break\n',
  '                if not ok:\n'
  '                    pass\n'])

# --- D: ground_truth / to_markdown -------------------------------------------
m("D01-ground-truth-all-hold-true", [T,
  '        "invariants_all_hold": all_invariants_hold(invariants),\n',
  '        "invariants_all_hold": True,\n'])
m("D02-ground-truth-status-emptied", [T,
  '        "invariant_status": classify_invariants(invariants),\n',
  '        "invariant_status": {INV_HOLDS: [], INV_VIOLATED: [], INV_UNVERIFIED: []},\n'])
m("D03-markdown-unverified-marker-removed", [T,
  '            lines.append("* **%s** — %s  _(prose only, **unverified** — no "\n',
  '            lines.append("* **%s** — %s  _(prose only, no "\n'])
m("D04-markdown-violated-marker-removed", [T,
  '                            "holds" if inv["holds"] else "**VIOLATED**"))\n',
  '                            "holds"))\n'])
m("D05-markdown-summary-always-true", [T,
  '                 "true" if truth["invariants_all_hold"] else "false"),\n',
  '                 "true"),\n'])
m("D06-markdown-rulecorr-and-not-or", [T,
  '    if "rule_correspondence" not in truth or "agrees" not in corr:\n',
  '    if "rule_correspondence" not in truth and "agrees" not in corr:\n'])
m("D07-markdown-omits-unverified-bullets", [T,
  '    for inv in truth["invariants"]:\n        if not inv.get("verified"):\n',
  '    for inv in truth["invariants"]:\n'
  '        if not inv.get("verified"):\n'
  '            continue\n'
  '        if False:\n'])

# --- E: build.py -------------------------------------------------------------
m("E01-row-violated-emptied", [B,
  '        "invariants_violated": list(truth_blob["invariant_status"]["violated"]),\n',
  '        "invariants_violated": [],\n'])
m("E02-row-unverified-emptied", [B,
  '        "invariants_unverified": list(truth_blob["invariant_status"]["unverified"]),\n',
  '        "invariants_unverified": [],\n'])
m("E03-totals-unverified-emptied", [B,
  '            "invariant_unverified": sorted(r["world_id"] for r in rows\n'
  '                                           if r["invariants_unverified"]),\n',
  '            "invariant_unverified": [],\n'])
m("E04-totals-failures-emptied", [B,
  '            "invariant_failures": sorted(r["world_id"] for r in rows\n'
  '                                         if r["invariants_violated"]),\n',
  '            "invariant_failures": [],\n'])
m("E05-totals-keys-swapped", [B,
  '            "invariant_failures": sorted(r["world_id"] for r in rows\n'
  '                                         if r["invariants_violated"]),\n'
  '            "invariant_unverified": sorted(r["world_id"] for r in rows\n'
  '                                           if r["invariants_unverified"]),\n',
  '            "invariant_failures": sorted(r["world_id"] for r in rows\n'
  '                                         if r["invariants_unverified"]),\n'
  '            "invariant_unverified": sorted(r["world_id"] for r in rows\n'
  '                                           if r["invariants_violated"]),\n'])
GATE_ENTRY = ('    ("invariant_unverified",\n'
              '     "a declared invariant ships unverified — no callable check ran, so the world "\n'
              '     "cannot claim it holds; give it a `check` or an `edge_check`, or stop "\n'
              '     "declaring it"),\n')
m("E06-unverified-gate-removed", [B, GATE_ENTRY, ''])
m("E07-violated-gate-removed", [B,
  '    ("invariant_failures", "a declared invariant is violated on a reachable state"),\n',
  ''])
m("E08-missing-key-back-to-optimistic-get", [B,
  '        if key not in totals:\n'
  '            out.append("%-24s gate could not be evaluated: the manifest carries "\n'
  '                       "no `%s` key, and an unevaluated gate is not a passed one"\n'
  '                       % ("<manifest>", key))\n'
  '            continue\n'
  '        for world_id in totals[key]:\n',
  '        for world_id in totals.get(key, ()):\n'])
m("E09-gate-failures-returns-empty", [B,
  '        for world_id in totals[key]:\n'
  '            out.append("%-24s %s (%s)" % (world_id, why, key))\n'
  '    return out\n',
  '        for world_id in totals[key]:\n'
  '            out.append("%-24s %s (%s)" % (world_id, why, key))\n'
  '    return []\n'])
m("E10-main-exits-zero-on-gate-failure", [B,
  '    if failures:\n        print()\n        print("BUILD GATE FAILED:")\n'
  '        for line in failures:\n            print("  " + line)\n        return 1\n',
  '    if failures:\n        print()\n        print("BUILD GATE FAILED:")\n'
  '        for line in failures:\n            print("  " + line)\n        return 0\n'])
m("E11-mutant-gate-results-discarded", [B,
  '        failures.extend(gate_failures(mutants))\n',
  '        gate_failures(mutants)\n'])

# --- F: the three mechanism edge_checks --------------------------------------
LATCH_HEAD = ('            def latch_monotone(world, prev, _action, nxt) -> bool:\n'
              '                mine_ = world.mine(self)\n')
m("F01-latch-edge-check-returns-true", [SD, LATCH_HEAD,
  '            def latch_monotone(world, prev, _action, nxt) -> bool:\n'
  '                return True\n'
  '                mine_ = world.mine(self)\n'])
m("F02-latch-monotone-direction-flipped", [SD,
  '                    if after.get(index) < before.get(index):\n',
  '                    if after.get(index) > before.get(index):\n'])
m("F03-latch-per-switch-clause-dropped", [SD,
  '                    if after.get(index) < before.get(index):\n                        return False\n',
  '                    if False:\n                        return False\n'])
m("F04-latch-net-clause-dropped", [SD,
  '                    if (self._net_on(mine_, before, net)\n'
  '                            and not self._net_on(mine_, after, net)):\n'
  '                        return False\n',
  '                    if False:\n'
  '                        return False\n'])
m("F05-latch-reverted-to-prose", [SD, '                 "edge_check": latch_monotone})\n',
  '                 "check": None})\n'])

COLL_HEAD = ('        def collection_monotone(world, prev, _action, nxt) -> bool:\n'
             '            before = world.view(self, prev)\n')
m("F06-collection-edge-check-returns-true", [CL, COLL_HEAD,
  '        def collection_monotone(world, prev, _action, nxt) -> bool:\n'
  '            return True\n'
  '            before = world.view(self, prev)\n'])
m("F07-collection-direction-flipped", [CL,
  '            if self._collected(after) < self._collected(before):\n',
  '            if self._collected(after) > self._collected(before):\n'])
m("F08-collection-count-clause-dropped", [CL,
  '            if self._collected(after) < self._collected(before):\n                return False\n',
  '            if False:\n                return False\n'])
m("F09-collection-lock-reopen-clause-dropped", [CL,
  '            return now_closed <= was_closed\n', '            return True\n'])
m("F10-collection-reverted-to-prose", [CL,
  '             "edge_check": collection_monotone},\n', '             "check": None},\n'])

TILE_HEAD = ('        def state_is_monotone(world, prev, _action, nxt) -> bool:\n'
             '            before = world.view(self, prev)\n')
m("F11-tile-edge-check-returns-true", [CS,
  '        def tile_monotone(world, prev, action, nxt) -> bool:\n',
  '        def tile_monotone(world, prev, action, nxt) -> bool:\n            return True\n'])
m("F12-tile-monotone-direction-flipped", [CS,
  '            return all(after.get(i) >= before.get(i)\n',
  '            return all(after.get(i) <= before.get(i)\n'])
m("F13-tile-monotone-clause-dropped", [CS,
  '            return (state_is_monotone(world, prev, action, nxt)\n'
  '                    and collapsed_is_never_crossed(world, prev, action, nxt))\n',
  '            return collapsed_is_never_crossed(world, prev, action, nxt)\n'])
m("F14-tile-collapsed-crossing-clause-dropped", [CS,
  '            return (state_is_monotone(world, prev, action, nxt)\n'
  '                    and collapsed_is_never_crossed(world, prev, action, nxt))\n',
  '            return state_is_monotone(world, prev, action, nxt)\n'])
m("F15-tile-reverted-to-prose", [CS,
  '             "edge_check": tile_monotone},\n', '             "check": None},\n'])

# --- G: the sandbox itself ---------------------------------------------------
GUARD = ('            found = text.count(anchor)\n'
         '            if found != 1:\n')
m("G01-sandbox-anchor-guard-disabled", [SB, GUARD,
  '            found = text.count(anchor)\n'
  '            if False:\n'])
m("G02-sandbox-table-anchor-broken-guard-intact", [SB,
  '_TABLE_ANCHOR = (\n    "    for mechanism in world.mechanisms:\\n"\n',
  '_TABLE_ANCHOR = (\n    "    for MECHANISM in world.mechanisms:\\n"\n'])
m("G03-sandbox-anchor-broken-and-guard-disabled", [SB, GUARD,
  '            found = text.count(anchor)\n            if False:\n'],
  [SB, '_TABLE_ANCHOR = (\n    "    for mechanism in world.mechanisms:\\n"\n',
   '_TABLE_ANCHOR = (\n    "    for MECHANISM in world.mechanisms:\\n"\n'])
m("G04-sandbox-pythonpath-not-isolated", [SB, '    env["PYTHONPATH"] = root\n',
  '    env["PYTHONPATH"] = root + os.pathsep + os.path.dirname(PACKAGE)\n'])
m("G05-sandbox-gate-lines-always-empty", [SB,
  '    out = []\n    seen = False\n', '    return ()\n    out = []\n    seen = False\n'])

# --- H: mutate.py ------------------------------------------------------------
m("H01-mutate-now-false-back-to-optimistic-get", ["mutate.py",
  '    mutant_status = truth.classify_invariants(mutant_inv.values())\n'
  '    now_false = sorted(mutant_status[truth.INV_VIOLATED])\n',
  '    now_false = sorted(name for name, row in mutant_inv.items()\n'
  '                       if row.get("verified") and not row.get("holds", True))\n'])
m("H02-mutate-now-false-includes-unverified", ["mutate.py",
  '    now_false = sorted(mutant_status[truth.INV_VIOLATED])\n',
  '    now_false = sorted(mutant_status[truth.INV_VIOLATED]\n'
  '                       + mutant_status[truth.INV_UNVERIFIED])\n'])

print(json.dumps(M, indent=1))
