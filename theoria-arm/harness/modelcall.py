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

## The shared spend gate (A3-campaign-devpile)

"Recorded but not proxied" accounted for the money in *this arm's* ledger and
nowhere else. It did not, and could not, tell any other session on this machine
that the money had gone: the single live g50t run spent $6.317658 against a
$20 float held inside one Python process, and `proxy/spend_gate.py`'s report
showed this arm's campaigns at $0.00. That is INC-BA-003's shape exactly.

So every call in this file now brackets itself with the shared pool
(`harness/spend.py`), and the gap that remains is the *transport* gap only:

    check   -> before the subprocess starts, against a pre-authorised ceiling
    spend
    record  -> after, always: success, failure, timeout or empty reply

There is no path through `call()` that starts a subprocess without a
reservation. `spend=None` and no binding on the run raises `NoSpendBinding`
rather than proceeding ungated, because a desk that spends when nobody claimed
headroom is the defect this wiring exists to remove -- not a degraded mode of
it.

`cost_ceiling_usd` stays, and stays independent. Two ceilings is correct here:
the arm-local one stops this run on its own account and is the one that should
fire first; the pool's is there for the case where the arm-local one is wrong,
absent, or the process is not the only one spending.
"""

import json
import math
import os
import shutil
import subprocess
import tempfile
import time
from typing import Any, Dict, List, Optional, Sequence

from harness.spend import NoSpendBinding, SpendBinding      # noqa: F401

#: The CLI is started here, outside the repository, for baseline-arms' D-009
#: reason: Claude Code walks parent directories looking for CLAUDE.md, and a
#: desk started inside the repo would read Theoria.md, the pile cut, the other
#: arms' traces and this arm's own source. The desk gets the candidate stream,
#: the two books and the frames -- and nothing else.
NEUTRAL_PARENT = tempfile.gettempdir()

PROVIDER = "anthropic-claude-code-cli"


class ModelError(RuntimeError):
    pass


class AnonymityBreach(RuntimeError):
    """A prompt carried a game id.

    Its own class rather than a `ModelError` because the two mean opposite
    things to a caller. `inner/loop.py` catches desk failures and records them
    as evidence to go back and theorize against -- which is right for a timeout
    or an empty reply, and exactly wrong here. A leaked id is not something the
    loop can learn from; it is a defect in the harness, and the run that
    produced it is not admissible under `Theoria.md:353` whatever it goes on to
    measure.
    """


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
                 spend: Optional[SpendBinding] = None,
                 transcript_dir: Optional[str] = None,
                 forbid_in_prompt: Sequence[str] = ()):
        self.run = run                                # proxy.ledger.RunLedger
        self.model = model
        self.pricing_ref = pricing_ref
        self.cost_ceiling_usd = cost_ceiling_usd
        self.timeout = timeout
        #: The claim on the shared pool this desk spends under. Passed
        #: explicitly where the caller has one; otherwise taken off the
        #: `RunLedger`, which `harness/run.py:Run` attaches it to.
        #:
        #: The fallback is not a convenience. `inner/loop.py` builds the
        #: ModelDesk and belongs to another agent, so reaching the binding
        #: through the object that already brackets the run is what lets this
        #: wiring land without editing that file. It is a fallback and not a
        #: default: when neither is present `call()` raises, it does not spend.
        self.spend = spend
        self.transcript_dir = transcript_dir
        #: Substrings that may not appear in any prompt this desk sends.
        #:
        #: `Theoria.md:353` names four overfitting channels and seals each. The
        #: fourth -- model priors, "公开游戏的攻略可能已在预训练语料里" -- cannot
        #: be closed, only reduced, and the reduction is a hard rule stated in
        #: those words: **硬规:游戏 ID 永不进模型上下文,全程匿名化**.
        #:
        #: Until A3 that rule held by omission. Nothing sanitised model-bound
        #: text; `build_prompt` was clean only because nobody had ever wired an
        #: id into it. An adversarial probe found the omission is not enough:
        #: `world/adapt.py` records `{"error", "traceback"}` for any engine that
        #: raises, `evidence_brief` dumps that report into the prompt, and an
        #: `OSError` message carries the path it failed on -- which is under a
        #: run directory whose slug used to embed the game stem. Forcing a
        #: candidate-write failure put **six** occurrences of `g50t` inside a
        #: 20,975-char prompt. Two more channels of the same shape are live but
        #: dormant: `books.compile_all` stringifies write errors into
        #: `compile_errors`, and Lean prefixes every diagnostic with the
        #: absolute file path, which reaches the next prompt verbatim inside a
        #: `proof_failure` payload.
        #:
        #: So the rule is enforced here instead, at the one place every prompt
        #: passes through, and it is checked *before* the subprocess starts:
        #: a leaked id is not something to discover in the transcript after
        #: paying for the call.
        self.forbid_in_prompt = tuple(s for s in forbid_in_prompt if s)

        self.calls = 0
        self.cli_cost_usd = 0.0
        self.unpriced_calls = 0
        self.usage_total: Dict[str, int] = {}
        self.log: List[Dict[str, Any]] = []

    # -- the account -------------------------------------------------------
    def _absorb_usage(self, usage: Dict[str, Any]) -> None:
        for key, value in (usage or {}).items():
            if isinstance(value, int):
                self.usage_total[key] = self.usage_total.get(key, 0) + value

    def summary(self) -> Dict[str, Any]:
        out = {"model": self.model, "calls": self.calls,
               "cli_cost_usd": round(self.cli_cost_usd, 6),
               "usage_total": dict(self.usage_total),
               "cost_ceiling_usd": self.cost_ceiling_usd,
               "unpriced_calls": self.unpriced_calls,
               "beats": sorted({entry["beat"] for entry in self.log})}
        binding = self.spend or getattr(self.run, "spend_binding", None)
        out["spend_gate"] = binding.describe() if binding is not None else None
        return out

    # -- the gate ----------------------------------------------------------
    def binding(self) -> SpendBinding:
        """The claim this desk spends under, or a refusal.

        Refusing here rather than returning None is the whole wiring: an
        ungated desk call is not a degraded mode, it is the defect.
        """
        binding = self.spend or getattr(self.run, "spend_binding", None)
        if binding is None:
            raise NoSpendBinding(
                "this desk has no claim on the shared spend pool, so it may not "
                "start a `claude -p` subprocess. Every desk call costs real "
                "money on a bill shared with every other session on this "
                "machine (the one live g50t run spent $6.317658, none of which "
                "the pool could see). Open one with "
                "`harness.spend.open_binding(...)` -- `harness/run.py:Run` does "
                "it for a normal run and attaches it to the RunLedger.")
        return binding

    @staticmethod
    def price_of(envelope: Dict[str, Any], usage: Dict[str, Any]):
        """What one envelope cost, or None if it cannot be trusted to say.

        None means "charge the pre-flight ceiling and flag it `unpriced`" --
        `proxy/model_proxy.py:239,303`'s rule, because assuming a call cost
        nothing is letting the provider decide whether it gets billed.

        Two ways an envelope fails to price itself:

        * `total_cost_usd` absent, null, or not a finite non-negative number;
        * `total_cost_usd == 0.0` **and** the `usage` block is missing its token
          counts. A genuinely free call is possible, but a zero with no tokens
          behind it is the shape of a missing field, and a missing field must
          not settle as $0.00.

        A priced envelope whose `usage` block is merely incomplete is **not**
        flagged unpriced: the price came from `total_cost_usd`, not from the
        tokens, so the pool's dollar total is still exact. Flagging it would
        turn that total into a lower bound and `UNPRICED_SPEND` would then
        refuse every dollar in the shared pool, for every session, until a
        human ran `price_unpriced()` -- the failure mode `spend_gate.py:860`
        documents. The incompleteness is recorded in the spend detail instead.
        """
        raw = envelope.get("total_cost_usd")
        if not isinstance(raw, (int, float)) or isinstance(raw, bool):
            return None
        value = float(raw)
        if value != value or math.isinf(value) or value < 0:
            return None
        if value == 0.0 and not all(
                isinstance((usage or {}).get(key), int)
                for key in ("input_tokens", "output_tokens")):
            return None
        return value

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

        # Before the gate and before the subprocess: a prompt carrying the game
        # id must not be sent, and finding out afterwards costs both the money
        # and the run's admissibility as evidence.
        leaked = sorted({s for s in self.forbid_in_prompt if s in prompt})
        if leaked:
            raise AnonymityBreach(
                "the prompt carries %s, which Theoria.md:353 forbids ever "
                "entering model context (硬规:游戏 ID 永不进模型上下文,"
                "全程匿名化). Not sent, not charged. This is almost never a "
                "hand-written id -- the usual source is an engine traceback or "
                "a compiler error carrying an absolute path from a run "
                "directory whose slug embeds the game stem, which reaches the "
                "prompt through evidence_brief or a surprise payload. Give the "
                "run a game-free slug rather than deleting the evidence."
                % ", ".join(repr(s) for s in leaked))

        model = model or self.model

        # -- the gate ------------------------------------------------------
        # Pre-authorised before the subprocess starts, against the GLOBAL pool
        # sum rather than this process's counter. `check` refuses; it consumes
        # nothing, so a generous per-call ceiling costs only an early refusal
        # when the pool is nearly empty.
        binding = self.binding()
        detail = {"arm": "theoria", "run_id": getattr(self.run, "run_id", None),
                  "beat": beat, "label": label, "model": model,
                  "transport": "claude-code-cli", "call": self.calls + 1}
        binding.check_model_call()

        try:
            envelope, elapsed_ms, stderr = self._invoke(prompt, model)
        except BaseException:
            # The subprocess may or may not have reached the provider -- a
            # timeout is exactly the case where it did and the answer was
            # thrown away. Charged at its ceiling and flagged unpriced either
            # way, because the alternative is assuming it cost nothing, which
            # lets the provider decide whether it gets billed.
            self.calls += 1
            self.unpriced_calls += 1
            binding.record_model_call(
                None, detail=dict(detail, outcome="raised_before_a_price",
                                  why="the CLI raised before an envelope "
                                      "carrying a price came back"))
            raise

        usage = envelope.get("usage") or {}
        text = envelope.get("result") or ""
        priced = self.price_of(envelope, usage)
        cli_cost = 0.0 if priced is None else priced

        self.calls += 1
        self.cli_cost_usd += cli_cost
        if priced is None:
            self.unpriced_calls += 1
        self._absorb_usage(usage)

        # Settled before the ledger write and before the empty-reply raise
        # below: a call that came back empty was still billed, and money that
        # was spent is a fact whatever happens to the run afterwards.
        charged = binding.record_model_call(
            priced, detail=dict(
                detail,
                subtype=envelope.get("subtype"),
                elapsed_ms=elapsed_ms,
                usage_complete=all(isinstance(usage.get(key), int)
                                   for key in ("input_tokens", "output_tokens")),
                why=(None if priced is not None else
                     "the CLI envelope carried no usable total_cost_usd, so the "
                     "call is charged at its pre-flight ceiling")))

        # The request as *this arm* sent it. Named `prompt` rather than
        # `messages` so nobody mistakes it for the /v1/messages body: the CLI
        # wraps it in a system prompt this arm never sees.
        # `invocation_idx` is this desk's own monotonic counter, and it is here
        # rather than at the top level because `model_call` is a **closed**
        # field set (`proxy/canon.py:64`, another track's file): a new top-level
        # key would be refused by `canon.check`. `request` is passed verbatim,
        # so this is the one place the arm may add its own vocabulary.
        #
        # The record already carries `call_idx` (assigned by
        # `RunLedger._next_call`) and `step_idx`, so the cost curve can be
        # joined to environment steps without reconstruction. Joining it to
        # *inner-loop turns* needs the turn number, which only `inner/loop.py`
        # knows and which it does not currently pass.
        request = {"transport": "claude-code-cli", "model": model,
                   "max_turns": max_turns, "prompt": prompt,
                   "beat": beat, "label": label,
                   "invocation_idx": self.calls,
                   # Sealing provenance, per call. These were top-level kwargs
                   # until A3; see the block comment below for why they moved
                   # here and what it cost.
                   "proxied": False,
                   "proxy_gap":
                       "model_proxy strips Authorization and no "
                       "ANTHROPIC_API_KEY exists; see harness/modelcall.py and "
                       "DECISIONS D-P8-002. The gap is transport-only: this "
                       "call was checked and recorded against the shared pool "
                       "(spend_gate campaign %s, reservation %s), so the "
                       "dollars are visible to every other session even though "
                       "the bytes did not cross the proxy."
                       % (binding.reservation.campaign,
                          binding.reservation.reservation_id)}

        # These five -- beat, label, transport, proxied, proxy_gap -- used to be
        # passed as top-level keyword arguments here, and `RunLedger.model_call`
        # forwards `**extra` straight into `Ledger.append`, which runs
        # `canon.check`. `canon.MODEL_CALL_FIELDS` is a closed set of ten names
        # and contains none of them, so this call raised `NonCanonicalField` on
        # every invocation that got as far as writing.
        #
        # It never showed up because `--mock` runs set `offline=True` and skip
        # theorize entirely, so no test in this repo ever reached a completed
        # model call. The archived P-8 ledgers do carry the five fields, because
        # those runs predate `proxy/canon.py` landing; `modelcall.py` was edited
        # afterwards without adapting.
        #
        # What made it expensive rather than merely wrong: the raise lands
        # *after* `self.cli_cost_usd` is incremented and after
        # `binding.record_model_call` has settled the charge against the shared
        # pool. A live run therefore paid for the call, booked the money, and
        # then died writing the record down -- for every model call, starting
        # with the first. The comment forty lines above already said the field
        # set was closed and that `request` is the one place this arm may add
        # its own vocabulary. The code did the opposite of its own comment.
        self.run.model_call(
            provider=PROVIDER,
            model=model,
            request=request,
            response=envelope,
            usage=usage,
            pricing_ref=self.pricing_ref,
            step_idx=step_idx,
            http={"method": "CLI", "path": "claude -p --output-format json",
                  "status": 200 if envelope.get("subtype") == "success" else 500,
                  "elapsed_ms": elapsed_ms, "attempts": 1,
                  "forwarded": False, "stream": False},
        )

        entry = {"call": self.calls, "beat": beat, "label": label,
                 "model": model, "elapsed_ms": elapsed_ms,
                 "cli_cost_usd": cli_cost, "usage": usage,
                 "gate_charged_usd": round(charged, 6),
                 "gate_unpriced": priced is None,
                 "step_idx": step_idx, "chars_in": len(prompt),
                 "chars_out": len(text)}
        self.log.append(entry)
        self._write_transcript(entry, prompt, text, stderr)

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
