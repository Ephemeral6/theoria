# 2026-07-31T170455Z-P1REPLAYLIVE · running notes

Prompt P1REPLAYLIVE · branch closeout/p1-replay-live · base d854632
Opened 2026-07-31T17:04:55Z

## 2026-07-31T17:05:13Z

Scope: Phase 1/2 closeout, item p1-replay-audit. The board's P1READJ next-step names it: spot-check the REAL online ledger since S31. Materials: ar25 (S31 probe, RESET only, proxy/var ledger) + sk48 (A3 level2-carried r1/r2/r3, committed run-dir ledgers). Excluded: 20260731T1500Z-A3-sk48-carried-l1 (in flight at ticket start, RUN_STATE finished=false, files written 2 min before ticket cut). Also to adjudicate: r3's surviving replay mismatch (commit 956ffd6f says 4->1). Recon workflow wf_349c6b91-b39 fanned out 4 read-only readers: tooling / ledger inventory / mismatch semantics / board constraints.

## 2026-07-31T17:30:15Z

CORRECTION to the opening note: the A3 level2-carried legs r1/r2/r3 are game g50t-5849a774, not sk48 (every run_start and env_step in those ledgers carries g50t; verified by the adversarial pass). sk48 is the game of the IN-FLIGHT l1 run (excluded) and of the pre-S31 E3 legs used in the sk48 supplement. The two-game live claim is therefore ar25 (S31, RESET-only) + g50t (three live legs). Adversarial verification wf_75420e77: 3 skeptics, refutations of the headline numbers: none; fixes applied to the driver: excluded-list key-space bug, derived (not hard-coded) adjudication conclusion 5-of-6, corrected canon-digest drift attribution (upgrade_ledger embeds invocation path in lifted.source -- inputs match pins 9/9; proxy-territory defect spawned as background task), adapter-honesty assertions published, archive reports/MANIFESTs and surprises.jsonl added to tracked inputs, live-depth disclosures added (ar25 live = position 0 only, 16/388 pairwise).
