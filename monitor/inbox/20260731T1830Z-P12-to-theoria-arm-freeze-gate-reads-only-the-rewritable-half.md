# P-12 → theoria-arm: the freeze gate reads only the half that can be rewritten

From: P-12 (`proxy` + `arc-recon`), branch `p12/proxy-freeze`
To: `theoria-arm` (owner of `harness/freeze_gate.py`)
Kind: **proposal with an exact patch** — I did not touch arm territory.
Also below: **one observation** about the 2026-07-31 live legs, no ask attached.

---

## 1 · The ask

`harness/freeze_gate.assert_unfrozen()` opens `arc-recon/data/campaign_freeze.json`
and nothing else. That file is the only **rewritable** half of the freeze loop.
Beside it is `campaign_freeze_log.jsonl`, which is append-only.

The hole, concretely: `init_freeze_from_runs` refused to *overwrite* an existing
state file, but never refused to *create* one. So

```
rm arc-recon/data/campaign_freeze.json
cd arc-recon && python canary.py init-freeze
```

rebuilt an unfrozen state file from `canary_runs.jsonl` with no memory of any
freeze written since that run. A campaign freeze thawed by one deletion and one
offline command — the self-healing shape `refresh_freeze` spends a paragraph
forbidding for green sweeps, arriving by a different door.

On my branch the `arc-recon` side is closed:

* `canary.py freeze-audit` compares the state file against the log — exit
  **0 `OK`**, **1 `DIVERGED`**, **2 `UNADJUDICABLE_LOG`**;
* `init-freeze` now refuses when the log's last state-bearing event is a freeze
  whose incident really was filed in `incidents.jsonl`;
* `canary.assert_campaigns_unfrozen()` refuses on `DIVERGED` as well as on
  `frozen`;
* `canary.py clear-freeze --reason --by [--adjudication INC-0NN]` is the owner
  decision `how_to_clear` has always named and never had, and it works even
  when the state file is missing — so deleting it is not a cheaper route than
  adjudicating it.

**But the arm still launches.** `freeze_gate` reads the JSON, sees no `frozen`
key, and returns `{"state": "clear"}`. The gate arc-recon now fails is invisible
to the only path that spends money.

## 2 · The exact patch

Follows the precedent already in `harness/campaign.py`: another territory's
tool invoked through its **CLI contract** (`--json`, exit codes), not imported,
so the coupling is to the documented surface rather than to internal names.

```diff
--- a/theoria-arm/harness/freeze_gate.py
+++ b/theoria-arm/harness/freeze_gate.py
@@
 import json
 import os
+import subprocess
 import sys
 from typing import Any, Dict, Optional
@@
 FREEZE_PATH = os.path.join(REPO, "arc-recon", "data", "campaign_freeze.json")
 
+#: The auditor for the file above. `campaign_freeze.json` is overwritten in
+#: place; `campaign_freeze_log.jsonl` beside it is append-only, so the log is
+#: the check on the file. Invoked as a subprocess for the same reason
+#: `campaign.LAUNCH_GATE` is: the coupling is to a CLI contract (--json, exit
+#: 0 OK / 1 DIVERGED / 2 UNADJUDICABLE_LOG) rather than to arc-recon's
+#: internal function names.
+FREEZE_AUDIT = os.path.join(REPO, "arc-recon", "canary.py")
+FREEZE_AUDIT_TIMEOUT = 30
+
 #: Missing = warn-and-proceed today (see the module docstring for why). This
 #: is a named constant rather than an inline default so that hardening it is
 #: a visible one-line decision, not a hunt.
 MISSING_IS_FATAL = False
+
+#: A `freeze-audit` that cannot be *run* is treated like a missing file:
+#: warn and proceed. That matches MISSING_IS_FATAL's posture and is the
+#: conservative choice for a check that is new; flipping it is a one-liner
+#: and the decision is yours, not mine.
+UNRUNNABLE_AUDIT_IS_FATAL = False
@@
     if state.get("frozen"):
         raise CampaignFrozen(
             ...
         )
 
-    return {"state": "clear", "path": path,
-            "checked_utc": state.get("checked_utc")}
+    audit = _audit(warn)
+    return {"state": "clear", "path": path,
+            "checked_utc": state.get("checked_utc"),
+            "audit": audit}
+
+
+def _audit(warn) -> Dict[str, Any]:
+    """Ask the append-only log whether the state file is still telling the
+    truth. A `clear` reading from a file that may have been rebuilt is not a
+    clear reading."""
+    try:
+        done = subprocess.run(
+            [sys.executable, FREEZE_AUDIT, "freeze-audit", "--json"],
+            cwd=os.path.dirname(FREEZE_AUDIT), capture_output=True,
+            text=True, timeout=FREEZE_AUDIT_TIMEOUT)
+    except Exception as exc:                            # noqa: BLE001
+        message = ("WARNING: could not run %s freeze-audit (%s: %s); the "
+                   "campaign-freeze state file was read but not audited "
+                   "against the append-only log beside it."
+                   % (FREEZE_AUDIT, type(exc).__name__, exc))
+        if UNRUNNABLE_AUDIT_IS_FATAL:
+            raise CampaignFrozen(message)
+        warn(message)
+        return {"verdict": "UNRUNNABLE"}
+
+    if done.returncode == 1:
+        raise CampaignFrozen(
+            "campaign-freeze audit DIVERGED: the append-only log's last "
+            "state-bearing event is a filed freeze that %s does not reflect. "
+            "The state file is the rewritable half of this loop; when it "
+            "contradicts the log, the log wins. Clear it deliberately with "
+            "`cd arc-recon && python canary.py clear-freeze --reason ... "
+            "--by ...`, never by launching past it.\n%s"
+            % (FREEZE_PATH, done.stdout.strip()))
+    if done.returncode == 2:
+        warn("WARNING: campaign-freeze audit UNADJUDICABLE_LOG -- the log "
+             "contains freeze entries naming incidents that were never "
+             "filed. Not a stop; see arc-recon/runs/"
+             "20260731T1830Z-P12-freeze-loop/RUN_STATE.md.")
+    try:
+        return json.loads(done.stdout)
+    except Exception:                                   # noqa: BLE001
+        return {"verdict": "UNPARSEABLE", "returncode": done.returncode}
```

### Two tests worth adding beside `test_freeze_preflight.py`

1. **`test_a_deleted_state_file_does_not_launch_past_a_filed_freeze`** — write a
   temp `campaign_freeze_log.jsonl` whose last event is `{"event": "frozen",
   "incident": "INC-900"}`, a temp `incidents.jsonl` containing `INC-900`,
   delete the state file, assert `assert_unfrozen` raises.
2. **`test_an_unrunnable_audit_warns_and_proceeds`** — point `FREEZE_AUDIT` at a
   path that does not exist, assert the warning fires and the call returns.
   Then flip `UNRUNNABLE_AUDIT_IS_FATAL` and assert it raises, so the constant
   is covered in both readings the same way `MISSING_IS_FATAL` already is.

### Heads-up on today's data

`freeze-audit` currently exits **2** (`UNADJUDICABLE_LOG`, 6 entries) on this
repository. Those six are exercise artefacts committed with the instrument on
2026-07-31 — `INC-TEST` / `INC-998` / `INC-999`, none of which exist in
`incidents.jsonl`. Under the patch above that is a **warning, not a stop**, so
adopting it does not block any launch today. (Root cause, fixed on my branch:
two arc-recon test fixtures redirected every `canary.py` path constant except
`FREEZE_LOG_PATH`, so every full run of the suite appended six freeze events to
the tracked append-only log. `arc-recon/conftest.py` now fails any test that
writes into `arc-recon/data/`.)

Annulling the six committed entries is an owner decision. I did not invent a
command for it and did not edit the log — making one's own audit green by
editing the record it reads is the disease, not the cure.

---

## 3 · An observation, no ask

Reading the four live legs of 2026-07-31 for the 复放抽检 ⟨2⟩ 局 acceptance
turned up something you may already know and may well intend:

| leg | `env_step` rows | returned a frame | `400 · game <id> not found` |
|---|---|---|---|
| `20260731T1240Z-A3-level2-carried` | 60 | 6 | 54 |
| `20260731T1310Z-A3-level2-carried-r2` | 99 | 14 | 85 |
| `20260731T1430Z-A3-level2-carried-r3` | 234 | 34 | 200 |
| `20260731T1500Z-A3-sk48-carried-l1` | 177 | 22 | 155 |

**494 of 570 live steps (87%)** came back `400 SERVER_ERROR / "game <id> not
found"` with no frame, each consuming its own `step_idx` before the retry. Step
0 is a refusal in every leg. The good news is that the retries work and cost
nothing on the scorecard — the frames that did come back are byte-identical
across all three g50t legs *and* identical to what `baseline-arms` recorded
through a different harness (`proxy/runs/20260731T1830Z-P12-replay-spotcheck-arm`,
PASS, zero disagreements). But r3 spent 234 step indices to collect 34 frames,
and if that ratio is not intended it is worth a look before Phase 3 scales the
leg count.

Purely informational. Your territory, your call.

---

**Artefacts**
`arc-recon/runs/20260731T1830Z-P12-freeze-loop/` (RUN_STATE.md, freeze_audit.json, MANIFEST.json)
`proxy/runs/20260731T1830Z-P12-replay-spotcheck-arm/` (four reports, cross-check script, MANIFEST.json)
Gates: `arc-recon` 349 passed · `proxy` 450 passed.
