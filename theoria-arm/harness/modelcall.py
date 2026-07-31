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

from proxy.redact import VAULT

#: The CLI is started here, outside the repository, for baseline-arms' D-009
#: reason: Claude Code walks parent directories looking for CLAUDE.md, and a
#: desk started inside the repo would read Theoria.md, the pile cut, the other
#: arms' traces and this arm's own source. The desk gets the candidate stream,
#: the two books and the frames -- and nothing else.
NEUTRAL_PARENT = tempfile.gettempdir()

PROVIDER = "anthropic-claude-code-cli"

#: Environment variables removed before the desk subprocess starts.
#:
#: `ARC_API_KEY` is the game credential: `CLAUDE.md` seals it inside the
#: environment proxy, and the desk has no business holding it.
#:
#: The three `ANTHROPIC_*` names are the redirect surface, and they are here
#: because A11 found the comment below the pop claimed to cover them and did
#: not. `ANTHROPIC_BASE_URL` is exactly how the model proxy was wired when it
#: was tried (see the module docstring), so it is a variable someone in this
#: repo has genuinely exported; `ANTHROPIC_AUTH_TOKEN` and `ANTHROPIC_API_KEY`
#: are the credentials that would make a redirected endpoint answer instead of
#: refusing. Inheriting any of them turns a desk call into a request this
#: ledger cannot see, while `total_cost_usd` still comes back in the CLI's
#: envelope and the run still looks fully accounted for.
#:
#: The CLI authenticates with its own stored OAuth bearer, so removing these
#: takes nothing away from it. If a future run genuinely needs to point the
#: desk somewhere else, that is a recorded act -- pass it explicitly and write
#: down where it went -- not something inherited from whatever shell happened
#: to launch the arm.
SCRUBBED_FROM_DESK_ENV = ("ARC_API_KEY", "ANTHROPIC_BASE_URL",
                          "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_API_KEY")


class CredentialBreach(RuntimeError):
    """A registered secret was about to be handed to the desk subprocess.

    Sibling of `AnonymityBreach`, and for its reason: this is a defect in the
    harness, not something the loop can learn from by gathering more evidence.
    `inner/loop.py` re-raises both rather than recording them as desk failures.

    It exists because the scrub above is **by name**, and a name-based scrub is
    blind to the value. `Theoria.md:305`'s Phase 1 line is a conjunction --
    *no credential inside the arm* AND *egress bypassing the two proxies must
    fail* -- and the first conjunct had no test anywhere in this arm. Measured
    rather than argued (`runs/20260730T1020Z-A3-SEAL-CONJUNCT-ONE/`): with a
    sentinel key handed to a live `Run`, the credential is resident at
    `run._cfg.api_key` and in the process-wide `VAULT`. So the first conjunct
    is false at the process boundary, and whether that reading is the binding
    one is the monitor's call, not this file's.

    What is *not* the monitor's call is the consequence. `_invoke` builds the
    desk's environment with `dict(os.environ)`, and `CLAUDE.md` documents
    `set -a; . ./.env; set +a` as the way to load the key -- so the credential
    being in this process's environment is the *documented* workflow, not a
    hypothetical. Under any other variable name (`ARC_API_KEY_BACKUP`, a CI
    runner's own convention, a `.env` copied to a second name) the four-name
    pop misses it and the value goes to a subprocess this ledger does not
    control. Whatever "inside the arm" turns out to mean, the credential
    reaching the desk is a leak under every reading of it.
    """


def call_field(record: Dict[str, Any], name: str) -> Any:
    """Read `beat`/`label`/`transport` off a `model_call` record, either shape.

    Defined here, beside the writer that decides the shape, because the two
    must not drift: a reader that assumes one shape is a second definition of
    the record format.

    There are two shapes on disk and both are permanent:

    * **Top-level** -- every `model_call` in the three archived P-8 runs. Those
      predate `proxy/canon.py`, which closed the field set to ten names.
    * **Inside `request`** -- everything written since. `canon.check` refuses
      the top-level form outright, so this is now the only shape that can be
      written at all.

    Preferring `request` and falling back to top-level reads both. The archived
    runs are committed artifacts that feed the figure registry, so dropping the
    fallback would silently re-zero exactly the historical curves this arm has.

    This function exists because moving the fields into `request` without it
    broke five call sites at once -- constraint 8 flipped to `holds: false` on
    every future run, and `_turn_spine` filtered on `beat == "theorize"` against
    a `None`, emptying `turn_series.json`, which is the raw material for the
    paper's bill-shape figure.
    """
    request = record.get("request")
    if isinstance(request, dict) and request.get(name) is not None:
        return request[name]
    return record.get(name)


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
                 forbid_in_prompt: Sequence[str] = (),
                 context: Optional[Any] = None):
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
        self.unpriced_calls = 0
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
        out = {"model": self.model, "calls": self.calls,
               "cli_cost_usd": round(self.cli_cost_usd, 6),
               "usage_total": dict(self.usage_total),
               "cost_ceiling_usd": self.cost_ceiling_usd,
               "unpriced_calls": self.unpriced_calls,
               "beats": sorted({entry["beat"] for entry in self.log}),
               # Ledger writes refused after the provider was paid. Empty is
               # the expected state; non-empty says the run's ledger is
               # incomplete and exactly where. See `_record_to_ledger`.
               "ledger_failures": list(self.ledger_failures),
               "calls_missing_from_ledger": sum(
                   1 for f in self.ledger_failures
                   if f.get("stage") == "model_call")}
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

    def _salvage_price(self, exc: BaseException):
        """A price out of a raised call's partial output, or None.

        Deliberately narrow. It reuses `price_of`, so a partial envelope has to
        clear exactly the same bar a complete one does -- a finite non-negative
        `total_cost_usd`, and not a bare zero with no tokens behind it. Anything
        less and this returns None and the call stays blind, which is the safe
        direction: inventing a price here would settle a call the provider may
        yet bill.

        The 2026-07-29 blind row is the case this cannot help with and should
        not pretend to: that CLI printed nothing at all, 145ms after the
        previous call settled. Nothing to salvage is still nothing to salvage.
        """
        partial = getattr(exc, "partial_stdout", "")
        if not partial or not partial.strip():
            return None
        try:
            envelope = json.loads(partial)
        except (json.JSONDecodeError, TypeError, ValueError):
            return None
        if not isinstance(envelope, dict):
            return None
        return self.price_of(envelope, envelope.get("usage") or {})

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
        binding.check_model_call(model=model)

        try:
            envelope, elapsed_ms, stderr = self._invoke(prompt, model)
        except BaseException as exc:
            # The subprocess may or may not have reached the provider -- a
            # timeout is exactly the case where it did and the answer was
            # thrown away. Charged at its ceiling and flagged unpriced when
            # nothing says otherwise, because the alternative is assuming it
            # cost nothing, which lets the provider decide whether it gets
            # billed.
            #
            # But look first. A raised call may still have printed a partial
            # envelope carrying `total_cost_usd`, and one blind row in the
            # shared pool refuses every dollar for every session until someone
            # files a correction by hand -- so a price that can be salvaged is
            # worth far more than the flag is. When one is found the call is
            # priced, not blind: the rule is that `unpriced` means the recorded
            # figure is not the measured one, and here it is.
            self.calls += 1
            salvaged = self._salvage_price(exc)
            if salvaged is None:
                self.unpriced_calls += 1
                binding.record_model_call(
                    None, detail=dict(detail, outcome="raised_before_a_price",
                                      why="the CLI raised before an envelope "
                                          "carrying a price came back"))
            else:
                self.cli_cost_usd += salvaged
                binding.record_model_call(
                    salvaged,
                    detail=dict(detail, outcome="raised_after_a_price",
                                why="the CLI raised, but its partial output "
                                    "carried a usable total_cost_usd"))
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
        #
        # E3 hit the same crash from the other side and drew the second lesson:
        # fixing the field set is necessary but not sufficient, because ANY
        # refusal from the writer lands after the money is gone. So the write
        # goes through `_record_to_ledger`, which is wrapped, and the arm's own
        # record is appended FIRST.

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
                 "gate_charged_usd": round(charged, 6),
                 "gate_unpriced": priced is None,
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
        # A writer that accepted the record but returned nothing is not a
        # failure -- the record is on the ledger, which is the property this
        # method exists to secure. Only the back-reference is unavailable, and
        # a missing back-reference must not be reported as a missing call.
        if isinstance(record, dict):
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
        #
        # The second half of that sentence was a comment and nothing else until
        # A11 read it: only `ARC_API_KEY` was popped, and `ANTHROPIC_BASE_URL`
        # was inherited from whatever launched the arm. One exported variable
        # in the operator's shell would have redirected every desk call to an
        # endpoint this ledger never sees -- and the run would still have
        # produced a full, plausible, correctly-priced transcript, because the
        # cost comes back in the CLI's own envelope. A silently redirected desk
        # is worse than a broken one: nothing goes red.
        for var in SCRUBBED_FROM_DESK_ENV:
            env.pop(var, None)
        # ... and then by value, because the four names above are a list of the
        # ways we have already been bitten. `VAULT.scrub_text` returns a
        # changed string exactly when the text contains a secret the process
        # has registered, so this asks the question the name list cannot: is
        # any value here the credential, whatever it is called? Popping first
        # and raising second means a caller that swallows the exception still
        # does not get a subprocess that can see the key.
        leaked = sorted(k for k, v in env.items()
                        if isinstance(v, str) and VAULT.scrub_text(v) != v)
        for var in leaked:
            env.pop(var, None)
        if leaked:
            raise CredentialBreach(
                "a registered secret is in the desk environment under %s; "
                "the name-based scrub does not cover it" % ", ".join(leaked))

        started = time.time()
        with tempfile.TemporaryDirectory(dir=NEUTRAL_PARENT) as cwd:
            try:
                proc = subprocess.run(cmd, cwd=cwd, env=env, input=prompt,
                                      capture_output=True, text=True,
                                      encoding="utf-8", errors="replace",
                                      timeout=self.timeout)
            except subprocess.TimeoutExpired as exc:
                # Keep whatever the CLI managed to print. The timeout is the
                # dominant producer of unpriced rows, and the CLI runs with
                # `--output-format json`, so a partial envelope carrying
                # `total_cost_usd` is exactly what may be sitting in this
                # buffer. Discarding it threw away the only evidence that
                # could price the one call that most needs pricing.
                partial = exc.stdout
                if isinstance(partial, bytes):
                    partial = partial.decode("utf-8", "replace")
                err = ModelError("claude -p timed out after %ds" % self.timeout)
                err.partial_stdout = partial or ""
                raise err
        elapsed_ms = int((time.time() - started) * 1000)

        try:
            envelope = json.loads(proc.stdout)
        except json.JSONDecodeError:
            err = ModelError("unparseable CLI output: %s"
                             % (proc.stdout or proc.stderr or "")[:400])
            err.partial_stdout = proc.stdout or ""
            raise err
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
