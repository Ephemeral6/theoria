# Requirement 2 was answered without spending, and that was a decision

The ticket's requirement 2 reads: *"跑一次最小的真臂调用（先算预算、经
`spend_gate.reserve()`），看 `proxy/var/ledger.jsonl` 有没有多出一条 `arm` 不是
`mock_arm` 的记录。有就贴出来，没有就定位写入端断在哪。"*

**No live API call was made. $0.00 spent. Zero network egress.** This is recorded
as a decision with reasons, not left as a silent omission, so the next reader can
overrule it cheaply.

## Why the question is already answered

Requirement 2 asks one thing: *is the real-arm record actually being written, and
if not, where does the write end break?* That was settled offline. The probe
(`../20260730T043824Z-S31-a10-said-done-prove-it/real_arm_probe.py`) ran
`proxy.runner.run_game(arm='bare_cc')` against the loopback mocks with the ledger
redirected to a scratch file, and wrote **61 records carrying `arm: bare_cc`**:

```
axis 1 = 61  (yes: the writer accepts a real arm and recorded one)
axis 2 = 0   (no: nothing left this machine)
```

So **the write end is not broken.** `proxy/var/ledger.jsonl` holds zero real-arm
records because no caller has ever passed a real arm to it — not because a real arm
was passed and dropped. The diagnosis requirement 2 exists to produce is complete,
and a live call cannot make it more complete.

## What a live call would and would not add

It would add **axis 2**: evidence that a run reached a non-localhost upstream. That
is a different proposition from the one requirement 2 poses, and it is the one the
arm territories own — `proxy` supplies the ledger and the gate; it does not decide
when an arm runs for real.

Three reasons not to spend it here:

1. **The ticket makes it conditional.** *"若需真跑，只准最小额并在 inbox 报数"* —
   *if a real run is needed*. It is not needed for the question asked.
2. **Spending is outward-facing and irreversible.** A billed API call cannot be
   undone, and the conditional permission in a ticket is not standing authorisation
   to spend when the finding does not require it.
3. **Zero real-arm records is A10's declared starting condition**, not a defect this
   item is chartered to clear (`proxy/DELIVERY_RULING.md` §1). Writing one live
   record would change the shared ledger's state without closing the gap that state
   represents, and would make the next auditor's job *harder*: the histogram would
   then show one real-arm record and still not mean the arms are running.

## The trap this avoids, which the probe found

The probe's own closing line is the reason to be careful here:

> And this run is exactly the forgery: had its ledger not been redirected, an audit
> asking only axis 1 would now call A10 delivered, on 61 mock records.

A run with `arm='bare_cc'` against loopback writes records that *look* like real-arm
records on the axis most audits check. **Manufacturing one real-arm record to satisfy
a requirement about real-arm records is the failure this whole item is about.** The
right output is the diagnosis plus the gap, which is what is delivered.

## If a live call is wanted anyway

It belongs to an arm territory, with its own budget line, and must go through
`proxy/spend_gate.py` (`reserve()` before the call). Whoever runs it should report
the amount in `monitor/inbox/` per the ticket, and should expect the resulting
ledger record to be **witnessed on both axes** — arm identity *and* a non-localhost
upstream — or it proves nothing that this offline probe has not already proven.
