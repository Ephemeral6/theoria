"""Did the arm receive the whole reply it paid for?

`ModelDesk._invoke` runs `claude -p --output-format json` and reads
`envelope["result"]`, which is the CLI's **last** assistant message. When the
desk's answer runs past the model's per-message output ceiling the CLI emits it
across several messages, and the arm keeps only the tail. The bill is for all of
them.

The arm has always had the evidence and never looked at it. The CLI reports
`usage.output_tokens` for the whole call and `usage.iterations[-1]` for the last
message alone; the difference is what the messages the arm never saw generated.
Across 103 archived desk calls that difference is either exactly zero or an
exact multiple of the model's own reported `maxOutputTokens` (64 000) -- 19
calls, no remainder anywhere -- so it is a count of messages, not a ratio to be
thresholded.

Why this lives in `harness/` and not in `armtools/`: it is a property of the
transport, the transport must record it as the call goes out, and the forensic
sweep must read the same definition rather than a second one that drifts.

Deliberately not here: any attempt to *recover* the missing text. It is not in
the envelope. Detecting the loss is the honest half; recovering it needs
`--output-format stream-json`, which is a live-transport change.
"""

from typing import Any, Dict, Optional, Tuple

#: Used only when the CLI envelope does not report the model's own ceiling.
#: Every archived call that reports one reports 64000. A figure derived from
#: this constant rather than from the envelope is labelled as such by the
#: caller, because an assumed ceiling turns an unexplained remainder into a
#: confident wrong count.
MAX_OUTPUT_TOKENS_FALLBACK = 64000


def ceiling_from_envelope(envelope: Dict[str, Any],
                          model: Optional[str]) -> Optional[int]:
    """The CLI's own `maxOutputTokens` for `model`, or `None` if it said none."""
    usage = (envelope or {}).get("modelUsage")
    if not isinstance(usage, dict):
        return None
    entry = usage.get(model)
    if not isinstance(entry, dict):
        return None
    cap = entry.get("maxOutputTokens")
    return cap if isinstance(cap, int) and cap > 0 else None


def messages_dropped(usage: Dict[str, Any],
                     cap: Optional[int] = None) -> Tuple[Optional[int], str]:
    """How many assistant messages the transport never handed to the arm.

    Returns `(count, why)`.

    `count` is `None` -- **not** 0 -- when the usage block carries no
    per-message `iterations`. A call whose per-message output was never recorded
    has not been shown to be whole, and reporting it as whole would let the
    detector certify exactly the calls it cannot see. Absence is recorded as
    absence.
    """
    usage = usage or {}
    iterations = usage.get("iterations")
    total = usage.get("output_tokens")
    if not isinstance(iterations, list) or not iterations or total is None:
        return None, ("usage carries no per-message `iterations`, so this call "
                      "is neither known to be whole nor known to be truncated")
    last = iterations[-1].get("output_tokens")
    if not isinstance(last, int) or not isinstance(total, int):
        return None, "the last iteration carries no integer `output_tokens`"
    gap = total - last
    ceiling = cap or MAX_OUTPUT_TOKENS_FALLBACK
    if gap <= 0:
        return 0, ("`output_tokens` equals the last message's own: the CLI "
                   "emitted one message and the arm received all of it")
    count, remainder = divmod(gap, ceiling)
    if remainder:
        return count, ("%d output tokens are unaccounted for: %d x the %d-token "
                       "ceiling plus %d. The remainder is unexplained, so the "
                       "count is a floor, not a total."
                       % (gap, count, ceiling, remainder))
    return count, ("%d output tokens were generated before the message the arm "
                   "received -- exactly %d x the model's own %d-token output "
                   "ceiling, so %d assistant message(s) were billed and never "
                   "delivered" % (gap, count, ceiling, count))
