# P1READJ · Phase-1 board re-adjudication after 2026-07-31's material changes

No experiment ran here — this is an adjudication pass: monitor/spec.py notes
brought back in line with the tree, then `python monitor/scan.py` re-run so
state.json re-derives the counts.

## Inputs (all read, none modified)

* merge `b375a9bd` — arm-side seal by construction (EnvProxy in a child
  process; `theoria-arm/harness/proxy_process.py`,
  `theoria-arm/tests/test_seal_process.py`).
* `proxy/runs/20260731T104757Z-S31/FIRED.md` — first real-arm record in the
  shared ledger (both axes witnessed, 2 actions, $0.00, register row #9).
* `verify-lab/DUAL_PROXY.md` + inbox `20260731T1800Z-S32-to-RES-2-one-proxy-
  validated-not-two.md` — the model-proxy ruling precedent: one proxy
  validated on real traffic, one built but unvalidated (0/65 model calls
  answered; CLI-direct since 2026-07-31, `proxied: false`, D-P8-002).
* register #9–#12 complete in `p3-gate-exception` (already on master).
* A16 launch gate wired (`monitor/board/done/A16-A16-launch-gate-wired.W-1800.md`).

## Adjudications

| item | before | after | why |
|---|---|---|---|
| p1-proxy-env | green | green | note upgraded: seal-conjunct process reading now holds by construction (b375a9bd) |
| p1-proxy-model | green | **partial** | S32 precedent: built but unvalidated; green had read "instrument exists" as "instrument validated" |
| p1-seal-test | partial | partial | left conjunct now by construction; right conjunct still half (model side unproxied by design, bare_cc GAP-5) |
| p1-same-shell | partial | partial | Theoria arm now exists and flew (#10 settled $9.5569/18 actions); first real-arm ledger record; routine wiring gap of DELIVERY_RULING.md §4 still open |
| all others | — | — | unchanged |

Money-gate item (`p3-gate-exception`) stays `risk` — its adjudicated-exception
register is the record, not a pass.

## Gate outputs, verbatim

* scan: `[2026-07-31 23:54:12] monitor/index.html written — Phase 1: 8/16 green`
  (exit 0; before this pass state.json said 9/16 — the drop is the model-proxy
  downgrade)
* monitor suite: exit 0, 525 passed / 2 xfailed, 176s (< 183s gate).
