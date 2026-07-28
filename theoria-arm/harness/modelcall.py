"""The theorize desk's model calls, and the account they leave behind.

Constraint 8 says the bill's shape is guaranteed by construction: a model is
called only when there is a surprise, and never during execute, certify or the
engines. That constraint is only worth anything if the bill is *measured*, so
every call made anywhere in this arm goes through `ModelDesk.call`, which is
the only place in the package that starts a model process.

## Why this is not the model proxy, and what was tried

`proxy/model_proxy.py` is the designed route and it does not work here. It was
tried, live, before this file was written:

    ANTHROPIC_BASE_URL=<model proxy>  claude -p --model claude-haiku-4-5 ...

The CLI authenticates with an OAuth bearer. The model proxy strips
`Authorization` at the boundary (it is not in `PASSTHROUGH_REQUEST_HEADERS`)
and injects `ANTHROPIC_API_KEY` instead -- and there is no `ANTHROPIC_API_KEY`
in this repo's `.env`, only `ARC_API_KEY`. Upstream answered
`401 {"message": "x-api-key header is required"}` to every request and the CLI
retried until the run timed out. Twenty-eight `model_call` records at status
401 and the matching `bypass_attempt` incidents are the evidence; they are
archived with the run.

The stripping is not a bug -- it is the sealing property, and repairing it means
editing `proxy/`, which belongs to another track. So the model side of this
run is **recorded but not proxied**, and that is a declared gap, not a silent
one. What is preserved:

* the record is written by the frozen writer, `proxy.ledger.RunLedger`, so it
  is byte-identical in shape to a proxied `model_call` and goes through
  `redact.py` on the way to disk;
* the provider's `usage` block is copied through **verbatim** from the CLI's
  own result envelope -- not reshaped, not summed (LEDGER_FORMAT.md §4);
* `http.forwarded` is `false` and `transport` names the CLI, so no reader can
  mistake this for traffic that crossed the proxy.

What is lost: the request and response bodies are the CLI's envelope rather
than the raw `/v1/messages` exchange, so the recorded prompt is what this arm
sent to the CLI, not what the CLI sent to Anthropic (it adds a system prompt
this arm never sees). Any conclusion about *input* token composition is
therefore off-limits from this ledger. Output usage and cost are not affected.

## Two independent cost figures, on purpose

The CLI reports `total_cost_usd`. `proxy/cost.py` derives a cost from the
recorded `usage` and a hashed price table that has never been checked against
a real bill. Recording both lets them be compared -- the first validation of
`pricing_v1.json` against a provider's own arithmetic. They are compared in
the run report; a disagreement is a finding about the price table.
"""

import json
import os
import shutil
import subprocess
import tempfile
import time
from typing import Any, Dict, List, Optional

#: The CLI is started here, outside the repository, for baseline-arms' D-009
#: reason: Claude Code walks parent directories looking for CLAUDE.md, and a
#: desk started inside the repo would read Theoria.md, the pile cut, the other
#: arms' traces and this arm's own source. The desk gets the candidate stream,
#: the two books and the frames -- and nothing else.
NEUTRAL_PARENT = tempfile.gettempdir()

PROVIDER = "anthropic-claude-code-cli"


class ModelError(RuntimeError):
    pass


class CostCeilingReached(RuntimeError):
    """Not an error in the run. The run's end when nothing else stopped it."""


def claude_bin() -> str:
    """On Windows the npm shim is claude.cmd; CreateProcess will not find the
    extensionless POSIX wrapper that `which claude` reports under Git Bash."""
    for name in ("claude.cmd", "claude.exe", "claude"):
        found = shutil.which(name)
        if found:
            return found
    raise ModelError("the `claude` CLI is not on PATH")


class ModelDesk:
    """Every model call this arm makes, and the ledger records they leave.

    `beat` names which beat of the inner loop asked -- `theorize`, `probe`, or
    the two that must never appear, `certify` and `commit`. It is written into
    the record, so constraint 8 becomes checkable from the ledger rather than
    asserted in prose.
    """

    #: The beats Theoria.md 1.10(d)/(e) allows to spend a model call. Anything
    #: else raises here rather than being caught later by an auditor.
    ALLOWED_BEATS = frozenset({"theorize", "probe_design"})

    def __init__(self, run, *, model: str = "claude-opus-5",
                 pricing_ref: Optional[Dict[str, Any]] = None,
                 cost_ceiling_usd: Optional[float] = 20.0,
                 # A theorize prompt carries the frame, the diffs and the
                 # engine report; the first live call on a 64x64 world took
                 # over ten minutes on `claude-opus-5` before it returned
                 # anything. 900s was the first value here and it was too
                 # close to that. A desk that times out is not fatal any more
                 # (`inner/loop.py` records the failure and goes back for
                 # evidence), but a timeout still throws away a paid call.
                 timeout: int = 1800,
                 transcript_dir: Optional[str] = None,
                 context: Optional[Any] = None):
        self.run = run                                # proxy.ledger.RunLedger
        self.model = model
        self.pricing_ref = pricing_ref
        self.cost_ceiling_usd = cost_ceiling_usd
        self.timeout = timeout
        self.transcript_dir = transcript_dir
        #: An optional zero-argument callable returning whatever the caller
        #: wants stamped on each log entry. The bill's *shape* -- what the nth
        #: dollar bought -- needs the action count standing when the call was
        #: made, and that number lives in the loop, not here. Asking for it at
        #: call time is the only way to get it right: reconstructing it
        #: afterwards from timestamps guesses, and a guessed x-axis is not a
        #: measurement.
        self.context = context

        self.calls = 0
        self.cli_cost_usd = 0.0
        self.usage_total: Dict[str, int] = {}
        self.log: List[Dict[str, Any]] = []
        #: Ledger writes that were refused after the provider had been paid.
        #: Empty is the expected state; non-empty means the run's ledger is
        #: incomplete and says exactly where.
        self.ledger_failures: List[Dict[str, Any]] = []

    # -- the account -------------------------------------------------------
    def _absorb_usage(self, usage: Dict[str, Any]) -> None:
        for key, value in (usage or {}).items():
            if isinstance(value, int):
                self.usage_total[key] = self.usage_total.get(key, 0) + value

    def summary(self) -> Dict[str, Any]:
        return {"model": self.model, "calls": self.calls,
                "cli_cost_usd": round(self.cli_cost_usd, 6),
                "usage_total": dict(self.usage_total),
                "cost_ceiling_usd": self.cost_ceiling_usd,
                "beats": sorted({entry["beat"] for entry in self.log}),
                "ledger_failures": list(self.ledger_failures),
                "calls_missing_from_ledger": sum(
                    1 for f in self.ledger_failures
                    if f.get("stage") == "model_call")}

    # -- the call ----------------------------------------------------------
    def call(self, prompt: str, *, beat: str, step_idx: Optional[int] = None,
             model: Optional[str] = None, label: str = "",
             max_turns: int = 2) -> str:
        if beat not in self.ALLOWED_BEATS:
            raise ModelError(
                "beat %r may not spend a model call. Theoria.md constraint 8: "
                "the large model appears at theorize and at probe design, and "
                "nowhere else -- execute, certify, plan and the engines are "
                "zero-call by construction." % (beat,))
        if (self.cost_ceiling_usd is not None
                and self.cli_cost_usd >= self.cost_ceiling_usd):
            raise CostCeilingReached(
                "spent $%.4f of a $%.2f ceiling over %d calls"
                % (self.cli_cost_usd, self.cost_ceiling_usd, self.calls))

        model = model or self.model
        envelope, elapsed_ms, stderr = self._invoke(prompt, model)

        usage = envelope.get("usage") or {}
        text = envelope.get("result") or ""
        cli_cost = float(envelope.get("total_cost_usd") or 0.0)

        self.calls += 1
        self.cli_cost_usd += cli_cost
        self._absorb_usage(usage)

        # The request as *this arm* sent it. Named `prompt` rather than
        # `messages` so nobody mistakes it for the /v1/messages body: the CLI
        # wraps it in a system prompt this arm never sees.
        #
        # `proxied` and `proxy_gap` live here rather than at the top of the
        # record because `LEDGER_FORMAT.md` §4 closed the `model_call` field
        # set after P-8 landed. `request` is caller-owned and already carried
        # `beat`, `label` and `transport`, so nothing was lost by moving them
        # in beside them -- see `_record_to_ledger`.
        request = {"transport": "claude-code-cli", "model": model,
                   "max_turns": max_turns, "prompt": prompt,
                   "beat": beat, "label": label, "proxied": False,
                   "proxy_gap": "model_proxy strips Authorization and no "
                                "ANTHROPIC_API_KEY exists; see "
                                "harness/modelcall.py and DECISIONS D-P8-002"}

        # The money is already gone. Everything below is bookkeeping, and no
        # bookkeeping failure may be allowed to discard a reply that has been
        # paid for -- so the arm's own record is written FIRST and the ledger
        # write is wrapped. E3's first live desk call cost $2.695 and was thrown
        # away because the ledger raised between the payment and the append:
        # `desk.calls` said 1, `desk_log.json` was `[]`, and no transcript
        # existed. Order is the fix; see DECISIONS D-E3-010.
        entry = {"call": self.calls, "beat": beat, "label": label,
                 "model": model, "elapsed_ms": elapsed_ms,
                 "cli_cost_usd": cli_cost, "usage": usage,
                 "step_idx": step_idx, "chars_in": len(prompt),
                 "chars_out": len(text)}
        if self.context is not None:
            try:
                entry.update(self.context() or {})
            except Exception as exc:                   # noqa: BLE001
                entry["context_error"] = "%s: %s" % (type(exc).__name__, exc)
        self.log.append(entry)
        self._write_transcript(entry, prompt, text, stderr)

        self._record_to_ledger(entry, request, envelope, usage, step_idx,
                               elapsed_ms, beat, label)

        if not text.strip():
            # An empty reply is not silence: the envelope says why. Naming the
            # subtype and any permission denial turns "the desk returned
            # nothing" into a diagnosis -- `error_max_turns` with
            # `stop_reason: tool_use` means the model spent its turn on a tool.
            raise ModelError(
                "the desk returned no text (subtype=%r, stop_reason=%r, "
                "num_turns=%r, denials=%d, stderr=%r)"
                % (envelope.get("subtype"), envelope.get("stop_reason"),
                   envelope.get("num_turns"),
                   len(envelope.get("permission_denials") or []),
                   (stderr or "")[:200]))
        return text

    # -- the ledger ---------------------------------------------------------
    def _record_to_ledger(self, entry, request, envelope, usage, step_idx,
                          elapsed_ms, beat, label) -> None:
        """The canonical `model_call`, and nothing beside it.

        P-8 wrote `beat`, `label`, `transport`, `proxied` and `proxy_gap`
        straight onto the record. `LEDGER_FORMAT.md` §4 closed that field set
        after P-8 landed and `canon.py` now refuses all five, which is what
        killed E3's first live desk call.

        They are not dropped -- they are nested inside `request`, which is a
        caller-owned object on the canonical record and already carried `beat`,
        `label` and `transport` before this change. So nothing is lost and no
        new event is invented: `EVENTS` in `proxy/ledger.py` is closed to seven
        names, none of which fits a model call's metadata, and adding one would
        mean editing another track's directory. `beat` therefore remains on the
        ledger, one level deeper, and constraint 8 stays checkable from the file
        rather than from prose. `armtools/archive.py` reads both depths.

        A refusal here is recorded and survived, never raised. By the time this
        runs the provider has been paid and the reply is already in `self.log`
        and on disk as a transcript; turning a bookkeeping problem into a lost
        call is strictly worse than an incomplete ledger plus a loud entry
        saying so. `ledger_failures` rides in `summary()` so it cannot be missed.
        """
        http = {"method": "CLI", "path": "claude -p --output-format json",
                "status": 200 if envelope.get("subtype") == "success" else 500,
                "elapsed_ms": elapsed_ms, "attempts": 1,
                "forwarded": False, "stream": False}
        try:
            record = self.run.model_call(
                provider=PROVIDER, model=entry["model"], request=request,
                response=envelope, usage=usage, pricing_ref=self.pricing_ref,
                step_idx=step_idx, http=http)
        except Exception as exc:                       # noqa: BLE001
            self.ledger_failures.append(
                {"call": entry["call"], "stage": "model_call",
                 "error": "%s: %s" % (type(exc).__name__, exc)})
            entry["ledger_error"] = "%s: %s" % (type(exc).__name__, exc)
            return
        entry["call_idx"] = record.get("call_idx")

    # -- plumbing ----------------------------------------------------------
    def _invoke(self, prompt: str, model: str):
        # `--tools ""` disables every built-in tool, and it is load-bearing.
        # Without it the desk has Bash and Write available and *uses* them: the
        # first live theorize call spent $0.73 and 251 seconds, then returned
        # `subtype: "error_max_turns"`, `stop_reason: "tool_use"`, and an empty
        # result -- the model had tried to `mkdir -p .../scratchpad && cat >`
        # its answer to a file instead of printing it, the tool call consumed
        # the single turn, and no text was ever produced. The permission denial
        # is in that record's `permission_denials`.
        #
        # `bare_cc` never met this because its reply is one line; a desk asked
        # for three large blocks reaches for a file. `--max-turns 2` is the
        # belt to this brace: if a tool call still happens, the model gets a
        # turn afterwards in which to answer.
        cmd = [claude_bin(), "-p", "--model", model,
               "--output-format", "json", "--tools", "", "--max-turns", "2"]
        env = dict(os.environ)
        # The desk must not be able to reach the game credential, and must not
        # inherit a base URL that would send it somewhere unrecorded.
        env.pop("ARC_API_KEY", None)

        started = time.time()
        with tempfile.TemporaryDirectory(dir=NEUTRAL_PARENT) as cwd:
            try:
                proc = subprocess.run(cmd, cwd=cwd, env=env, input=prompt,
                                      capture_output=True, text=True,
                                      encoding="utf-8", errors="replace",
                                      timeout=self.timeout)
            except subprocess.TimeoutExpired:
                raise ModelError("claude -p timed out after %ds" % self.timeout)
        elapsed_ms = int((time.time() - started) * 1000)

        try:
            envelope = json.loads(proc.stdout)
        except json.JSONDecodeError:
            raise ModelError("unparseable CLI output: %s"
                             % (proc.stdout or proc.stderr or "")[:400])
        return envelope, elapsed_ms, proc.stderr

    def _write_transcript(self, entry: Dict[str, Any], prompt: str,
                          text: str, stderr: str) -> None:
        """The prompt and the reply, in full, on disk. The ledger has them too,
        but a human reading the concept-birth timeline should not have to grep
        a JSONL for a 40 KB prompt."""
        if not self.transcript_dir:
            return
        os.makedirs(self.transcript_dir, exist_ok=True)
        name = "call-%03d-%s%s.md" % (entry["call"], entry["beat"],
                                      ("-" + entry["label"]) if entry["label"] else "")
        path = os.path.join(self.transcript_dir, name)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("# %s\n\n" % name[:-3])
            fh.write("model: `%s` · %d ms · $%.6f · usage %s\n\n"
                     % (entry["model"], entry["elapsed_ms"],
                        entry["cli_cost_usd"], json.dumps(entry["usage"], sort_keys=True)))
            fh.write("## prompt\n\n```\n%s\n```\n\n" % prompt)
            fh.write("## reply\n\n```\n%s\n```\n" % text)
            if stderr and stderr.strip():
                fh.write("\n## stderr\n\n```\n%s\n```\n" % stderr[:4000])
