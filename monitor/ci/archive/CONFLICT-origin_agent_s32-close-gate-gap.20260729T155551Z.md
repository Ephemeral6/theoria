# CONFLICT-origin_agent_s32-close-gate-gap.md
branch: origin/agent/s32-close-gate-gap
reason: verify gate red in browser-ops (verify.py)
tip: 6d2b378491c8c446ea0bc7ac153ad035068c7687
first_seen: 2026-07-29T14:49:11Z
last_seen: 2026-07-29T14:49:11Z
attempts: 1

```
[1/3] the canary parses and its checks are complete
   ok    4 check(s), each with all 6 fields
[2/3] the fingerprints could actually fail to match
   ok    every fingerprint has a hash and a non-zero length
[3/3] the history is readable, ordered, and freshness is stated
   FAIL  history entry 2 has verdict 'drift (cosmetic scope)', which is not one of ['baseline', 'changed', 'drift', 'no-drift', 'unchanged', 'unreachable'] -- an unrecognised verdict is not a pass

browser-ops: RED (1 problem(s))

```
