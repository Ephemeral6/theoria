import json
M=[]
def m(n,*e): M.append({"name":n,"edits":[list(x) for x in e]})
SD="mechanisms/switch_door.py"; CL="mechanisms/count_lock.py"; CS="mechanisms/consumable.py"; T="core/truth.py"; B="build.py"
m("F16-latch-edge-check-returns-false",[SD,
 '            def latch_monotone(world, prev, _action, nxt) -> bool:\n                mine_ = world.mine(self)\n',
 '            def latch_monotone(world, prev, _action, nxt) -> bool:\n                return False\n                mine_ = world.mine(self)\n'])
m("F17-collection-edge-check-returns-false",[CL,
 '        def collection_monotone(world, prev, _action, nxt) -> bool:\n            before = world.view(self, prev)\n',
 '        def collection_monotone(world, prev, _action, nxt) -> bool:\n            return False\n            before = world.view(self, prev)\n'])
m("F18-tile-edge-check-returns-false",[CS,
 '        def tile_monotone(world, prev, action, nxt) -> bool:\n',
 '        def tile_monotone(world, prev, action, nxt) -> bool:\n            return False\n'])
m("C18-transitions-checked-key-omitted",[T,'            row["transitions_checked"] = edges\n','            pass\n'])
m("C19-edge-loop-half-the-transitions",[T,
 '            for prev, action, nxt, _rule in world.transitions(states):\n',
 '            for prev, action, nxt, _rule in list(world.transitions(states))[::2]:\n'])
m("C20-state-loop-half-the-states",[T,'            for state in states:\n','            for state in states[::2]:\n'])
m("E12-gates-tuple-emptied",[B,
 'def gate_failures(manifest: Dict[str, Any]) -> List[str]:\n',
 'GATES = ()\n\n\ndef gate_failures(manifest: Dict[str, Any]) -> List[str]:\n'])
m("D08-markdown-invariant-section-dropped",[T,
 '    for inv in truth["invariants"]:\n        if not inv.get("verified"):\n',
 '    for inv in []:\n        if not inv.get("verified"):\n'])
print(json.dumps(M,indent=1))
