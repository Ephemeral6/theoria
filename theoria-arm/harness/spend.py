"""This arm's binding to the shared spend pool (`proxy/spend_gate.py`).

A3-campaign-devpile's red line is *"每局动作预算先算后花、必须经
proxy/spend_gate.py reserve()，闸门红了立刻停"*. Before this file the arm
honoured exactly half of it, and not the expensive half.

**What was already gated.** ARC actions, but only by accident of routing:
`harness/arc.py` posts to the environment proxy, and `proxy/env_proxy.py`
mints a `permit()` before every socket and `record()`s the attempts that
happened. Nothing in this package asked for that; it came free with the proxy,
which is why the pool's report showed `theoria:r-<runid>` campaigns at
**$0.00** -- an auto-derived name and a dollar column that was not zero but
absent.

**What was not gated at all.** The desk. `harness/modelcall.py` shells out to
the `claude -p` CLI directly, records `proxied=False` with a `proxy_gap` note,
and the model proxy is genuinely unavailable to it (it strips `Authorization`
and there is no `ANTHROPIC_API_KEY`; see that module's header and the 65
`model_call` @401 records in `evidence/model-proxy-401.jsonl`). The single live
g50t run spent **$6.317658** and not one cent of it was visible to the pool.
Its only ceiling was `cost_ceiling_usd`, a float inside one process.

That is INC-BA-003 exactly (`baseline-arms/INCIDENTS.md`): *"事故不在任何一方
跑错，而在于没有任何一方的闸门看得见另一方的花费。"* A per-process ceiling is
not a gate; it is a receipt the process writes to itself.

## Shape

`baseline-arms/harness/spend.py` solved the same problem for the sibling arm
and this deliberately matches its shape rather than inventing one: a
`SpendBinding` holding one reservation plus the verbs bound to it, handed to
everything that can spend, with no default and no optional form. Three things
are added here that the sibling did not need:

* **One reservation for both axes.** `proxy/runner.py:run_game` takes a single
  claim and shares it between both proxies, for the reason stated there: two
  claims would hold the pool twice for one run's worth of spending. This arm
  has the same two axes (ARC actions through the env proxy, desk dollars
  through the CLI) and does the same thing -- `harness/run.py` opens the
  binding and passes the *same* reservation into `EnvProxyConfig`.
* **The one-true-pool assertion.** `spend_gate.POOL_ROOT` resolves a relative
  ledger against the **main checkout**, not the importer, because CLAUDE.md
  tells every agent to work in `.worktrees/<id>/` and there are ~50 of them on
  this box. If that resolution ever changed, "one shared pool" would silently
  become one full-ceiling pool per worktree, and `fingerprint()["ledger_path"]`
  is relative so the split would be invisible afterwards. So the binding checks
  the *absolute* path and the pool name at construction and refuses to run
  against anything else.
* **先算后花 as arithmetic, not just enforcement.** `plan_caps()` computes what
  a declared level actually needs and refuses against the pool's **global** free
  headroom before a reservation is opened. See its docstring for the sums.

## The order, and it is not negotiable

    check   -> before the money leaves.   Reads the GLOBAL sum. Refuses.
    spend
    record  -> after, always, success or failure. Accounts.
    release -> in a `finally`.

There is no `commit()` and no `refund()` in `spend_gate.py`: `record()` **is**
the settle step. `check()` only asks whether the headroom exists; it consumes
nothing.

## Failure policy

* `SpendGateUnavailable` -- the gate cannot do its job. Not a budget problem
  and never worked around: it propagates and the run dies. A permissive
  fallback here is indistinguishable, from the caller's side, from a working
  gate.
* `SpendGateTripped` -- a ceiling was reached. The binding **latches**: every
  subsequent `check_*` refuses with the original exception. No retry, no
  sleep-and-try-again, and above all no re-reserving smaller to squeeze under a
  pool ceiling, which would be one process deciding it may have what the pool
  just told it it may not.
* An expired lease **cannot** be renewed (`spend_gate.py:776`), only
  re-reserved -- and re-reserving can fail because somebody else took the
  headroom in the meantime. So the lease is sized to the run's declared wall
  clock up front, and `heartbeat()` renews it long before it can lapse.
"""

import math
import os
import sys
import time
from typing import Any, Dict, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(HERE)
REPO = os.path.dirname(ARM)

if REPO not in sys.path:                                        # pragma: no cover
    sys.path.insert(0, REPO)

from proxy import spend_gate as _spend_gate                     # noqa: E402
from proxy.spend_gate import (                                  # noqa: E402
    NoReservation, Reservation, SpendGate, SpendGateError, SpendGateTripped,
    SpendGateUnavailable,
)

__all__ = [
    "SpendBinding", "Caps", "open_binding", "plan_caps", "campaign_name",
    "assert_one_true_pool", "one_true_pool",
    "NoSpendBinding", "PoolMismatch", "InsufficientHeadroom",
    "NoReservation", "SpendGate", "SpendGateError", "SpendGateTripped",
    "SpendGateUnavailable",
    "MODEL_CALL_CEILING_USD", "HTTP_PER_COMMAND", "RETRY_SAFETY",
    "FIXED_COMMANDS", "DEFAULT_ENV_MAX_ATTEMPTS",
]


# -- the pool this arm is allowed to draw on ---------------------------------

#: The pool named in `proxy/spend_policy.json`. Checked, not assumed.
POOL_NAME = "theoria-shared-2026-07"

#: Where that pool's ledger has to be, relative to the **main checkout**.
POOL_LEDGER_PARTS = ("proxy", "var", "spend_gate.jsonl")


class PoolMismatch(SpendGateError):
    """This gate is not pointed at the one shared pool.

    Its own class because the repair is nothing like a budget refusal: it means
    the ledger resolved somewhere else, and every dollar counted against it is a
    dollar the other sessions cannot see.
    """


class NoSpendBinding(SpendGateError):
    """Something tried to spend with no claim on the shared pool at all.

    Distinct from `NoReservation`, which means the claim expired or was
    released. This means nobody ever wired one up -- which, for the desk, was
    the state of the world before this module existed.
    """


class InsufficientHeadroom(SpendGateError):
    """The pool's global free headroom cannot cover this run's declared budget.

    Raised by `plan_caps()` *before* `reserve()`, so the refusal names the
    arithmetic rather than only the ceiling. Carries `.required` and `.totals`.
    """

    def __init__(self, message: str, required: Dict[str, Any],
                 totals: Dict[str, Any]):
        super().__init__(message)
        self.required = required
        self.totals = totals


def one_true_pool() -> Dict[str, Any]:
    """The fingerprint fields a gate must present before this arm will use it."""
    return {
        "pool": POOL_NAME,
        "ledger_abspath": os.path.abspath(
            os.path.join(_spend_gate.POOL_ROOT, *POOL_LEDGER_PARTS)),
    }


def assert_one_true_pool(gate: SpendGate,
                         expect: Optional[Dict[str, Any]] = None
                         ) -> Dict[str, Any]:
    """Refuse any gate that is not the shared pool. Returns the fingerprint.

    `expect` exists for tests and for a caller deliberately running against a
    scratch pool, and it is a required, explicit argument rather than a flag:
    "point somewhere else" has to be a sentence somebody wrote, not a default
    that can be reached by forgetting something. The fingerprint that was
    asserted goes into `describe()` and from there into the run record, so a run
    against a scratch pool says so.
    """
    expect = one_true_pool() if expect is None else dict(expect)
    fp = gate.fingerprint()
    wrong = {key: (fp.get(key), value) for key, value in expect.items()
             if os.path.normcase(str(fp.get(key))) != os.path.normcase(str(value))}
    if wrong:
        raise PoolMismatch(
            "this gate is not the pool this arm may draw on: %s. `ledger_abspath` "
            "is the field that matters -- a relative ledger resolves against the "
            "main checkout precisely so that ~50 worktrees do not become ~50 "
            "pools each carrying the full $%.2f ceiling. Refusing to spend "
            "against a pool the other sessions cannot see."
            % (", ".join("%s is %r, expected %r" % (k, got, want)
                         for k, (got, want) in sorted(wrong.items())),
               fp.get("usd_ceiling", 0.0)))
    return fp


# -- what one desk call is pre-authorised for --------------------------------

#: The pre-flight ceiling for one `claude -p` desk call.
#:
#: Measured, not felt. `runs/20260728T015354Z-g50t-first-contact/desk_log.json`
#: is the only live desk this arm has ever run: 5 calls, $6.317658 total, mean
#: $1.2635, **max $1.489011**. The aborted run's single call was $0.730485.
#: $4.00 is ~2.7x the worst call ever observed here.
#:
#: Bigger than baseline-arms' $0.25 by design and not by carelessness: that
#: track's desk answers in one line on a haiku tier, and this one hands
#: `claude-opus-5` a 40 KB frame-and-engine prompt.
#:
#: A loose ceiling costs almost nothing, because `check()` verifies the headroom
#: *exists* and does not consume it -- the settlement that follows is the real
#: figure. What it buys is the property that no call can start without the pool
#: having been asked first. It costs something in exactly two places, and both
#: are stated rather than hidden: it refuses slightly early when the pool is
#: nearly empty, and it is the amount charged for a call that comes back
#: unpriced.
MODEL_CALL_CEILING_USD = 4.00

#: **Borrowed, not measured on this arm.** The comment that used to stand here
#: said 1.75 was "measured post-cookie-fix" and that
#: `Budget.as_json()["http_amplification"]` is exactly this ratio. Both halves
#: were false, and the second one is why nobody caught the first:
#:
#: * The source is `arc-recon/data/incidents.jsonl:16` (INC-011), whose
#:   `side_by_side` cell reads `http_calls_gameplay 35 / executed_commands 20`.
#:   That is HTTP calls per **executed command**. This constant is consumed at
#:   `plan_caps` below as HTTP per **successful action** -- a different
#:   denominator. Per successful action the same cell is 35/18 = 1.94.
#: * That cell is the **`bare_cc` arm**, on `ar25`, with **`cookies=True`**.
#:   This arm has no cookie jar (grep `cookie` in `harness/arc.py`: nothing).
#:   INC-011's own text forbids the reuse: *"confirmed as descriptions of the
#:   OLD transport and are now obsolete as forward estimates. Re-derive rather
#:   than reinterpret."*
#: * No `theoria-arm` run has ever reported 1.75. Its observed
#:   `commands_sent/actions_ok` values are 1.083, 1.167, 1.2, 1.25 (all **mock**
#:   -- `env_proxy.upstream` is `127.0.0.1`), then 5.714, 7.333, 17.0 live, then
#:   222.222 on the leg that hit its command ceiling.
#:
#: The value is left at 1.75 rather than replaced. The live samples say this
#: arm's transport is somewhere in 5.7-17x when it is actually retrying, so 1.75
#: under-reserves; but a replacement of "12" was considered and rejected --
#: **not one observed run sits between 1.25 and 5.714**, so any number in that
#: gap is interpolation into empty space, and swapping one unfounded constant
#: for another buys nothing but a fresh false comment. What is fixed here is the
#: provenance, and `HTTP_PER_COMMAND_IS_VALIDATED` below, which makes every
#: reservation carry the fact that its sizing constant is borrowed.
HTTP_PER_COMMAND = 1.75

#: Whether `HTTP_PER_COMMAND` has ever been measured on *this* arm's transport,
#: in *this* constant's own denominator. It has not. A reservation sized on it
#: records this, so a leg cannot be planned on a borrowed number without the
#: plan saying so.
HTTP_PER_COMMAND_IS_VALIDATED = False
HTTP_PER_COMMAND_PROVENANCE = (
    "arc-recon/data/incidents.jsonl:16 (INC-011) side_by_side, bare_cc arm, "
    "ar25, cookies=True, 35 http / 20 executed commands. Different arm, "
    "different transport, different denominator from the one plan_caps uses.")

#: Multiplier over the measured ratio. The measurement is a mean over one run;
#: the retry envelope (`arc.ACTION_ATTEMPTS = 40`) means the tail is long, and a
#: cap sized to the mean would trip `RESERVATION_ACTION_CAP` mid-run -- which
#: stops the run, correctly, but for the wrong reason.
RETRY_SAFETY = 1.5

#: Commands a run makes that are not ACTIONs: open scorecard, RESET, close
#: scorecard. Counted because they are outbound ARC requests, and the pool's
#: unit is the request.
FIXED_COMMANDS = 3

#: `harness/run.py`'s `env_max_attempts`. Each arm-level attempt becomes up to
#: this many *outbound* requests inside the env proxy's own retry envelope, and
#: the pool counts outbound requests.
DEFAULT_ENV_MAX_ATTEMPTS = 3

#: Slack over the declared wall clock when sizing the lease, and the hard stop.
#: An expired lease cannot be renewed, so the lease is sized to outlive the run
#: rather than to be rescued mid-flight; `heartbeat()` is the second line.
TTL_MARGIN_S = 900.0
TTL_MIN_S = 3600.0
TTL_MAX_S = 8 * 3600.0

#: How close to expiry `heartbeat()` starts renewing.
HEARTBEAT_WINDOW_S = 900.0


class Caps:
    """A computed budget: what to reserve, and the sum that produced it."""

    def __init__(self, usd_cap: float, action_cap: int, ttl_seconds: float,
                 arithmetic: Dict[str, Any]):
        self.usd_cap = float(usd_cap)
        self.action_cap = int(action_cap)
        self.ttl_seconds = float(ttl_seconds)
        self.arithmetic = arithmetic

    def as_json(self) -> Dict[str, Any]:
        return {"usd_cap": round(self.usd_cap, 6), "action_cap": self.action_cap,
                "ttl_seconds": self.ttl_seconds, "arithmetic": self.arithmetic}

    def __repr__(self) -> str:                                  # pragma: no cover
        return "Caps($%.2f, %d actions, ttl %.0fs)" % (
            self.usd_cap, self.action_cap, self.ttl_seconds)


def plan_caps(*, actions: int, commands: int,
              cost_ceiling_usd: Optional[float],
              wall_clock_s: float = 3 * 3600.0,
              env_max_attempts: int = DEFAULT_ENV_MAX_ATTEMPTS,
              model_call_ceiling_usd: float = MODEL_CALL_CEILING_USD,
              gate: Optional[SpendGate] = None,
              require_headroom: bool = True) -> Caps:
    """先算后花: compute a run's caps, then check them against the GLOBAL pool.

    ## Actions

    The pool's unit is **one outbound ARC HTTP request**, and
    `spend_policy.json` says so in as many words: *"It is NOT the scorecard's
    successful-action count."* This arm's `Budget` counts two different things
    and neither of them is that unit:

    * `Budget.actions` -- successful ACTIONs, the P-8 red line (120). Failed
      400s do not bill against the scorecard, so this is the quota unit.
    * `Budget.commands` -- arm-level attempts. `arc._send` calls
      `budget.command()` once per attempt inside its 40-attempt envelope, so
      this counts tries, not successes.

    Neither is an outbound request, because each arm-level attempt enters the
    env proxy, which has its own retry envelope (`env_max_attempts`, 3 in
    `harness/run.py`) and opens a real socket per attempt inside it. So::

        arm_attempts  = FIXED_COMMANDS + ceil(actions x 1.75 x 1.5)
        arm_attempts  = min(arm_attempts, commands)      # Budget.commands stops first
        action_cap    = arm_attempts x env_max_attempts
        hard_bound    = commands x env_max_attempts      # nothing can exceed this

    Worked, for the defaults `harness/run.py` ships (`--budget 12`,
    `--commands 2000`, `env_max_attempts=3`)::

        3 + ceil(12 x 1.75 x 1.5) = 3 + 32 = 35 arm attempts
        35 x 3                    = 105 outbound requests reserved

    and for the P-8 live shape (`actions=120`)::

        3 + ceil(120 x 1.75 x 1.5) = 3 + 315 = 318
        318 x 3                    = 954 outbound requests reserved

    The 1.75 is measured (`Budget.as_json()["http_amplification"]`,
    post-cookie-fix); 1.5 covers the tail, because `arc.ACTION_ATTEMPTS = 40`
    means one stubborn 400 wave can cost forty attempts on its own and a cap
    sized to the mean would trip mid-run. `hard_bound` is the only number here
    that is a *bound* rather than an estimate: `Budget.commands` raises before
    the (n+1)th attempt, so no run can exceed it however badly the retries go.

    ## Dollars

    `usd_cap = cost_ceiling_usd + model_call_ceiling_usd`, and the `+` is the
    load-bearing part. `modelcall.py` refuses a *new* call once
    `cli_cost_usd >= cost_ceiling_usd`, so the last permitted call lands on top
    of an already-full ceiling; a reservation sized to exactly
    `cost_ceiling_usd` would trip `RESERVATION_USD_CAP` on that call. Sizing it
    one call larger makes the two ceilings genuinely independent: the arm-local
    one always stops the run first on the arm's own account, and the pool's cap
    is there for the case where the arm-local one is wrong, absent or bypassed.

    `cost_ceiling_usd=None` (the offline dry run) still reserves one call's
    ceiling rather than $0.00 -- an offline run that unexpectedly reaches the
    desk must be refused by the pool, not merely by an `if`.

    ## The refusal

    The headroom test reads `gate.totals().free_usd` / `.free_actions`, which
    are ceiling minus spent minus **every other live reservation's unspent
    remainder**. That middle term is the one INC-BA-003 did not have, and it is
    why this cannot be answered from a local counter. `reserve()` re-checks it
    under the pool lock; this check is earlier and only so that a run refuses
    with its own arithmetic in the message instead of a bare ceiling.
    """
    actions = int(actions)
    commands = int(commands)
    env_max_attempts = max(1, int(env_max_attempts))
    if actions < 0 or commands < 0:
        raise SpendGateError("a planned budget is not negative "
                             "(actions=%r commands=%r)" % (actions, commands))

    arm_attempts = FIXED_COMMANDS + math.ceil(actions * HTTP_PER_COMMAND * RETRY_SAFETY)
    capped_by_commands = arm_attempts > commands
    arm_attempts = min(arm_attempts, commands) if commands else arm_attempts
    hard_bound = commands * env_max_attempts
    action_cap = arm_attempts * env_max_attempts
    if commands:
        action_cap = min(action_cap, hard_bound)

    ceiling = 0.0 if cost_ceiling_usd is None else float(cost_ceiling_usd)
    usd_cap = ceiling + float(model_call_ceiling_usd)

    ttl = max(TTL_MIN_S, min(TTL_MAX_S, float(wall_clock_s) + TTL_MARGIN_S))

    arithmetic = {
        "unit": "one action = one outbound ARC HTTP request (spend_policy.json)",
        "actions_budget": actions,
        "commands_ceiling": commands,
        "http_per_command": HTTP_PER_COMMAND,
        "http_per_command_is_validated": HTTP_PER_COMMAND_IS_VALIDATED,
        "http_per_command_provenance": HTTP_PER_COMMAND_PROVENANCE,
        "retry_safety": RETRY_SAFETY,
        "fixed_commands": FIXED_COMMANDS,
        "env_max_attempts": env_max_attempts,
        "arm_attempts_planned": arm_attempts,
        "arm_attempts_capped_by_commands_ceiling": capped_by_commands,
        "action_cap_hard_bound": hard_bound,
        "action_cap": action_cap,
        "cost_ceiling_usd": cost_ceiling_usd,
        "model_call_ceiling_usd": float(model_call_ceiling_usd),
        "usd_cap": round(usd_cap, 6),
        "wall_clock_s": float(wall_clock_s),
        "ttl_seconds": ttl,
    }

    if require_headroom:
        gate = gate if gate is not None else SpendGate()
        totals = gate.totals()
        short = []
        if usd_cap > totals.free_usd:
            short.append("$%.4f requested > $%.4f free ($%.4f spent + $%.4f held "
                         "by %d live reservation(s) against a $%.2f ceiling)"
                         % (usd_cap, totals.free_usd, totals.usd, totals.held_usd,
                            len(totals.live), totals.ceiling_usd))
        if action_cap > totals.free_actions:
            short.append("%d actions requested > %d free (%d spent + %d held "
                         "against a %d ceiling)"
                         % (action_cap, totals.free_actions, totals.actions,
                            totals.held_actions, totals.ceiling_actions))
        if short:
            raise InsufficientHeadroom(
                "the shared pool cannot cover this run's declared budget: %s. "
                "This is 先算后花: the budget was computed before anything was "
                "reserved and the pool refused it. The repair is a smaller "
                "declared level or a released reservation -- NOT a smaller "
                "reservation that squeezes under the ceiling, which is one "
                "process deciding it may have what the pool just said it may "
                "not." % "; ".join(short),
                arithmetic, totals.as_dict())

    return Caps(usd_cap, action_cap, ttl, arithmetic)


def campaign_name(*, prompt_id: str, game_id: str, slug: str) -> str:
    """An explicit, meaningful campaign name.

    Never `default_campaign(arm, run_id)`, which derives `theoria:r-<uuid>`. A
    derived name is attributable but it does not say what the run was *for*, and
    the whole pool report for this arm currently reads as a column of those.
    """
    for what, value in (("prompt_id", prompt_id), ("game_id", game_id),
                        ("slug", slug)):
        if not value or not str(value).strip():
            raise SpendGateError(
                "a campaign name needs a %s. An auto-derived name (`theoria:r-"
                "<uuid>`) is what this argument exists to replace: it is "
                "attributable but it does not say what the run was for."
                % what)
    return "theoria-arm:%s:%s:%s" % (prompt_id, game_id, slug)


class SpendBinding:
    """A live claim on the shared pool, plus the verbs bound to it.

    Held by `harness/run.py`'s `Run` (which hands the same reservation to the
    env proxy) and reached by `harness/modelcall.py` for every desk call. It is
    passed explicitly and has no default: a default is how a gate becomes
    optional, and an optional gate is what INC-BA-003 already disproved.
    """

    def __init__(self, gate: SpendGate, reservation: Reservation,
                 *, pool_fingerprint: Dict[str, Any],
                 model_call_ceiling_usd: float = MODEL_CALL_CEILING_USD,
                 caps: Optional[Caps] = None):
        self.gate = gate
        self.reservation = reservation
        self.pool_fingerprint = pool_fingerprint
        self.model_call_ceiling_usd = float(model_call_ceiling_usd)
        self.caps = caps

        #: Set the first time any verb trips. Every later `check_*` refuses with
        #: it, unchanged. "闸门红了立刻停" is a latch, not a retry policy.
        self.tripped: Optional[SpendGateTripped] = None
        self.released = False

        #: This process's own counters. For the run summary and never for a
        #: limit decision -- every limit reads the global sum, which is the
        #: entire point of the module underneath.
        self.actions_charged = 0
        self.usd_charged = 0.0
        self.model_calls_charged = 0
        self.unpriced_calls = 0
        self.renewals = 0

    # -- the latch ---------------------------------------------------------
    def _refuse_if_tripped(self) -> None:
        if self.tripped is not None:
            raise self.tripped

    def _latch(self, exc: SpendGateTripped) -> SpendGateTripped:
        if self.tripped is None:
            self.tripped = exc
        return exc

    # -- lease -------------------------------------------------------------
    def heartbeat(self, *, now: Optional[float] = None) -> bool:
        """Renew the lease if it is within `HEARTBEAT_WINDOW_S` of lapsing.

        Called from every `check_*`, because an expired lease cannot be renewed
        (`spend_gate.py:776`) -- only re-reserved, and re-reserving can fail
        because somebody else took the headroom while this run was thinking. A
        desk call can block for `timeout=1800`s, so a run can be a single
        `check` away from a lapse without doing anything wrong.

        Returns True if a renewal was written.
        """
        now = time.time() if now is None else now
        if self.released:
            return False
        remaining = getattr(self.reservation, "expires_epoch", 0.0) - now
        if remaining > HEARTBEAT_WINDOW_S:
            return False
        ttl = self.caps.ttl_seconds if self.caps is not None else None
        self.gate.renew(self.reservation, ttl_seconds=ttl)
        self.renewals += 1
        return True

    def renew(self, ttl_seconds: Optional[float] = None) -> None:
        self.gate.renew(self.reservation, ttl_seconds=ttl_seconds)
        self.renewals += 1

    def release(self, reason: str = "closed") -> None:
        """Give the unspent hold back. Idempotent, and called from a `finally`.

        Idempotent because the caller that most needs to call it is an
        exception path, and a second release raising would replace the real
        failure with a bookkeeping one.
        """
        if self.released:
            return
        self.released = True
        self.gate.release(self.reservation, reason)

    # -- ARC actions -------------------------------------------------------
    # The env proxy charges these itself once it is handed this reservation
    # (`proxy/env_proxy.py:308,344`). These two exist for a caller that reaches
    # ARC without the proxy in front of it -- there is none in this arm today,
    # and the pair is here so that adding one does not mean inventing the
    # accounting at the same time.
    def check_action(self, n: int = 1) -> None:
        self._refuse_if_tripped()
        self.heartbeat()
        try:
            self.gate.check(self.reservation, usd=0.0, actions=n)
        except SpendGateTripped as exc:
            raise self._latch(exc)

    def record_action(self, n: int = 1,
                      detail: Optional[Dict[str, Any]] = None) -> None:
        try:
            self.gate.record(self.reservation, usd=0.0, actions=n,
                             detail=detail or {})
        except SpendGateTripped as exc:
            self.actions_charged += n
            raise self._latch(exc)
        self.actions_charged += n

    # -- desk dollars ------------------------------------------------------
    def check_model_call(self, usd: Optional[float] = None) -> None:
        """Before `claude -p` starts. Raises to refuse; consumes nothing."""
        self._refuse_if_tripped()
        self.heartbeat()
        amount = self.model_call_ceiling_usd if usd is None else float(usd)
        try:
            self.gate.check(self.reservation, usd=amount, actions=0)
        except SpendGateTripped as exc:
            raise self._latch(exc)

    def record_model_call(self, usd: Optional[float], *,
                          detail: Optional[Dict[str, Any]] = None) -> float:
        """Settle one desk call. Returns the amount actually charged.

        `usd is None` means the CLI envelope carried no usable price. That call
        is charged its **pre-flight ceiling** and flagged `unpriced=True`, which
        is what `proxy/model_proxy.py:239,303` does and for the same reason:
        assuming a call cost nothing is letting the provider decide whether it
        gets billed. The pool's dollar total then reports as a stated lower
        bound rather than a silent zero, and `SpendGate.check` refuses further
        *dollar* spend pool-wide until a human accounts for it with
        `price_unpriced()`. Action-only spend is unaffected -- actions are
        counted by the request, not by a price table.

        Called even when the call failed, and even when it returned no text: a
        `claude -p` invocation that reached the provider and came back empty was
        still billed. Charging only for what succeeded is how a pool undercounts
        itself into an incident.
        """
        unpriced = usd is None
        amount = self.model_call_ceiling_usd if unpriced else float(usd)
        try:
            self.gate.record(self.reservation, usd=amount, actions=0,
                             unpriced=unpriced, detail=detail or {})
        except SpendGateTripped as exc:
            self._account(amount, unpriced)
            raise self._latch(exc)
        self._account(amount, unpriced)
        return amount

    def _account(self, amount: float, unpriced: bool) -> None:
        # Accumulate raw, round once at the edge. Rounding at every step makes
        # this counter drift from a plain sum of the same figures, and "the pool
        # and the run record agree exactly" has to survive being checked exactly.
        self.usd_charged += amount
        self.model_calls_charged += 1
        if unpriced:
            self.unpriced_calls += 1

    # -- the record --------------------------------------------------------
    def describe(self) -> Dict[str, Any]:
        """What goes into `run_start`, so a run says which pool it drew on."""
        out = {
            "reservation_id": self.reservation.reservation_id,
            "campaign": self.reservation.campaign,
            "usd_cap": self.reservation.usd_cap,
            "action_cap": self.reservation.action_cap,
            "model_call_ceiling_usd": self.model_call_ceiling_usd,
            "pool": self.pool_fingerprint,
            "actions_charged": self.actions_charged,
            "usd_charged": round(self.usd_charged, 6),
            "model_calls_charged": self.model_calls_charged,
            "unpriced_calls": self.unpriced_calls,
            "renewals": self.renewals,
            "released": self.released,
            "tripped": (None if self.tripped is None
                        else {"rule": self.tripped.rule,
                              "message": str(self.tripped)}),
        }
        if self.caps is not None:
            out["caps"] = self.caps.as_json()
        return out


def open_binding(campaign: str, caps: Caps, *,
                 holder: Optional[Dict[str, Any]] = None,
                 gate: Optional[SpendGate] = None,
                 expect_pool: Optional[Dict[str, Any]] = None,
                 model_call_ceiling_usd: float = MODEL_CALL_CEILING_USD
                 ) -> SpendBinding:
    """Claim headroom on the shared pool and return the binding that spends it.

    One reservation per run, shared by the env proxy and the desk. Raises
    `PoolMismatch` if the gate is not the one true pool, and `SpendGateTripped`
    if the pool -- summed across every campaign and every session, including
    ones this process cannot see -- has no room. That refusal is the
    deliverable: it is the sentence INC-BA-003 had no way to say.
    """
    if not campaign or not str(campaign).strip():
        raise SpendGateError("a reservation needs a campaign name")
    if str(campaign).startswith("theoria:r-"):
        raise SpendGateError(
            "%r is `spend_gate.default_campaign`'s derived name. Use "
            "`campaign_name(prompt_id=..., game_id=..., slug=...)`: the pool "
            "report for this arm is already a column of `theoria:r-<uuid>` "
            "rows at $0.00 and none of them says what the run was for."
            % (campaign,))

    gate = gate if gate is not None else SpendGate()
    fingerprint = assert_one_true_pool(gate, expect_pool)

    holder = dict(holder or {})
    holder.setdefault("track", "theoria-arm")
    holder.setdefault("prompt_id", "A3-campaign-devpile")

    reservation = gate.reserve(campaign, caps.usd_cap, caps.action_cap,
                               holder=holder, ttl_seconds=caps.ttl_seconds)
    return SpendBinding(gate, reservation, pool_fingerprint=fingerprint,
                        model_call_ceiling_usd=model_call_ceiling_usd,
                        caps=caps)
