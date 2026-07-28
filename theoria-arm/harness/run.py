"""One run: one arm, one game, one scorecard, one ledger.

This is `proxy/runner.py`'s job, done here instead, for three reasons that only
show up on a live run:

* `run_game` has no `try/finally`. If `arm.play()` raises -- and a first live
  contact with an unknown game is exactly where it raises -- the run never
  reaches `run_end`, the run record is never written, and the ledger is left
  with an orphaned `run_start`. Here `run_end` is written from a `finally`.
* `run_game` does not expose the env proxy's `max_attempts`, and the split
  between the proxy's retry envelope and this arm's matters: the proxy retries
  5xx/429 short, the arm retries the 400 wave long (`harness/arc.py`).
* `run_game`'s CLI always builds the mock arm. A real custom arm has to come in
  through `arm_factory`, so the entry point has to be Python either way.

Nothing here is a copy of `proxy/`: `EnvProxy`, `Ledger`, `RunLedger` and
`SealedPileGuard` are imported and used as a library. The ledger this arm
writes is therefore produced by the frozen writer, with the frozen redaction,
and satisfies `LEDGER_FORMAT.md` by construction rather than by imitation.

## The claim on the shared pool

`Run` opens **one** reservation and hands the same one to both spenders, which
is `proxy/runner.py:run_game`'s pattern and for its stated reason: two claims
would hold the pool twice for one run's worth of spending. Here the two
spenders are the environment proxy (ARC actions) and the desk
(`harness/modelcall.py`, dollars).

Two things changed with A3-campaign-devpile:

* the campaign is **named**. Passing no campaign let `EnvProxyConfig` derive
  `theoria:r-<uuid>`, and the pool's report for this arm is a column of those:
  attributable, but silent about what the run was for.
* the desk is **inside** the claim. Before, `EnvProxyConfig` auto-reserved for
  ARC actions and the desk's dollars were accounted nowhere the pool could see.

The binding is attached to the `RunLedger` so `ModelDesk` can reach it without
`inner/loop.py` -- another agent's file -- having to change. It is released in
`__exit__`, i.e. from `play()`'s `with`, so a crash in `arm.play()` cannot
strand the shared pool's headroom for the lease's whole duration.
"""

import json
import os
import sys
import time
import uuid
from typing import Any, Callable, Dict, Optional

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap                                     # noqa: F401  (sys.path)

from proxy.env_proxy import EnvProxy, EnvProxyConfig
from proxy.guard import SealedPileGuard
from proxy.ledger import Ledger, RunLedger, canonical
from proxy.paths import UPSTREAM_ARC

from harness import spend as spend_mod

ARM = "theoria"                                       # registered in ledger.ARMS

PROMPT_ID = "A3-campaign-devpile"

RUNS_DIR = _bootstrap.path("runs")


def new_run_id() -> str:
    return "r-" + uuid.uuid4().hex[:16]


def run_dir(slug: str) -> str:
    path = os.path.join(RUNS_DIR, slug)
    os.makedirs(path, exist_ok=True)
    return path


class Run:
    """The pieces one run needs, assembled and taken down in the right order."""

    def __init__(self, game_id: str, slug: str, *,
                 run_id: Optional[str] = None,
                 env_upstream: str = UPSTREAM_ARC,
                 env_key: Optional[str] = None,
                 require_key: bool = True,
                 env_max_attempts: int = 3,
                 caps: Optional[spend_mod.Caps] = None,
                 campaign: Optional[str] = None,
                 spend_gate=None,
                 expect_pool: Optional[Dict[str, Any]] = None,
                 ledger_path: Optional[str] = None):
        self.game_id = game_id
        self.slug = slug
        self.run_id = run_id or new_run_id()
        self.dir = run_dir(slug)
        self.ledger_path = ledger_path or os.path.join(self.dir, "ledger.jsonl")

        self.ledger = Ledger(self.ledger_path)
        self.run = RunLedger(self.ledger, self.run_id, ARM)
        self.guard = SealedPileGuard()

        # -- the claim, before anything that can spend exists ---------------
        # 先算后花: the caps are computed from the declared level and refused
        # against the pool's global free headroom, and only then is anything
        # reserved. A caller that passes none gets `plan_caps`' answer for this
        # module's own defaults rather than a shrug -- "no declared budget" must
        # not resolve to "whatever the policy's default is", because that
        # default exists to be inconvenient, not to be the normal case.
        self.caps = caps if caps is not None else spend_mod.plan_caps(
            actions=120, commands=2000, cost_ceiling_usd=20.0,
            env_max_attempts=env_max_attempts, gate=spend_gate)
        self.campaign = campaign or spend_mod.campaign_name(
            prompt_id=PROMPT_ID, game_id=game_id, slug=slug)
        self.spend = spend_mod.open_binding(
            self.campaign, self.caps, gate=spend_gate, expect_pool=expect_pool,
            holder={"run_id": self.run_id, "arm": ARM, "game_id": game_id,
                    "slug": slug})
        # Reached by `ModelDesk` without `inner/loop.py` having to change: the
        # RunLedger is the object that already brackets every record this run
        # writes, so it is the natural place for the claim those records are
        # written under. `ModelDesk.binding()` raises when it is absent.
        self.run.spend_binding = self.spend

        try:
            # The proxy's own envelope stays short: it covers 5xx/429/transport,
            # which are genuinely transient in seconds. The 400 wave, which is
            # transient in *minutes*, is the arm's job (harness/arc.py).
            #
            # `campaign` + `spend_reservation` are passed, so the env proxy
            # charges ARC actions against *this* claim instead of taking a
            # second, auto-named one -- and `spend_reservation_owned` stays
            # False there, so it will not release a claim the desk is still
            # spending under.
            self._cfg = EnvProxyConfig(
                run_id=self.run_id, arm=ARM, upstream=env_upstream,
                api_key=env_key, require_key=require_key,
                ledger=self.ledger, run=self.run, guard=self.guard,
                max_attempts=env_max_attempts,
                campaign=self.campaign, spend_gate=self.spend.gate,
                spend_reservation=self.spend.reservation)
        except BaseException:
            # A `Run` that never gets built must not leave a claim on the
            # shared pool for the lease's whole duration.
            self.spend.release("run construction failed")
            raise

        self.proxy: Optional[EnvProxy] = None
        self.started_at: Optional[float] = None

    # -- lifecycle ---------------------------------------------------------
    def __enter__(self) -> "Run":
        try:
            self.proxy = EnvProxy(self._cfg).start()
        except BaseException:
            self.spend.release("proxy failed to start")
            raise
        self.started_at = time.time()
        return self

    def __exit__(self, *exc) -> None:
        try:
            if self.proxy:
                self.proxy.stop()
        finally:
            # In a `finally`, and for `proxy/runner.py:run_game`'s reason: a
            # release that only runs when the run finishes is a release that
            # does not run on the paths that need it. An adversarial pass there
            # counted 43 crashed runs stranding the whole shared pool for the
            # full TTL with nothing spent -- fail-closed, but the recovery is to
            # wait an hour.
            self.spend.release("run %s ended" % self.run_id)

    @property
    def env_base(self) -> str:
        assert self.proxy is not None, "the run is not started"
        return self.proxy.base_url

    # -- the record --------------------------------------------------------
    def start_record(self, **extra: Any) -> None:
        self.run.run_start(
            game_id=self.game_id,
            env_base=self.env_base,
            model_base=None,
            env_upstream=self._cfg.upstream,
            guard=self.guard.fingerprint(),
            variant=None,
            arm_version=_bootstrap.arm_version(),
            upstream_pin=_bootstrap.upstream_pin(),
            # Which pool this run drew on, under whose claim, and the
            # arithmetic that sized the claim. A run that drew on a scratch
            # pool or a widened ceiling is identifiable after the fact.
            spend_gate=self.spend.describe(),
            **extra,
        )

    def end_record(self, **fields: Any) -> None:
        self.run.run_end(
            env_proxy=self.proxy.summary() if self.proxy else None,
            elapsed_s=round(time.time() - (self.started_at or time.time()), 1),
            **fields,
        )

    def write_run_json(self, summary: Dict[str, Any]) -> str:
        record = {
            "run_id": self.run_id,
            "arm": ARM,
            "game_id": self.game_id,
            "slug": self.slug,
            "ledger": os.path.abspath(self.ledger_path),
            "env_proxy": self.proxy.summary() if self.proxy else None,
            "arm_version": _bootstrap.arm_version(),
            "spend": self.spend.describe(),
            "summary": summary,
        }
        path = os.path.join(self.dir, "run.json")
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(record, fh, indent=2, sort_keys=True, default=str)
            fh.write("\n")
        return path


def play(game_id: str, slug: str, arm_factory: Callable[[str, "Run"], Any], *,
         env_upstream: str = UPSTREAM_ARC, env_key: Optional[str] = None,
         require_key: bool = True, run_id: Optional[str] = None,
         caps: Optional[spend_mod.Caps] = None,
         campaign: Optional[str] = None,
         spend_gate=None,
         expect_pool: Optional[Dict[str, Any]] = None,
         start_extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Drive one run to completion, and write `run_end` whatever happens.

    The `with` is what brackets the claim on the shared pool: `Run.__exit__`
    releases it in a `finally`, so the unspent hold comes back even when
    `arm.play()` raises. What was actually spent stays counted forever.
    """
    outcome: Dict[str, Any] = {"outcome": "not_started"}
    with Run(game_id, slug, run_id=run_id, env_upstream=env_upstream,
             env_key=env_key, require_key=require_key, caps=caps,
             campaign=campaign, spend_gate=spend_gate,
             expect_pool=expect_pool) as run:
        run.start_record(**(start_extra or {}))
        arm = arm_factory(run.env_base, run)
        try:
            outcome = arm.play()
        except spend_mod.SpendGateTripped as exc:     # 闸门红了立刻停
            # Not retried, not re-reserved smaller. A trip is the pool saying
            # this run may not have what it asked for, and the only correct
            # response is to stop and let the release in `__exit__` hand the
            # rest back.
            outcome = {"outcome": "spend_gate_tripped",
                       "rule": exc.rule,
                       "error": "%s: %s" % (type(exc).__name__, exc)}
            raise
        except BaseException as exc:                  # noqa: BLE001 -- recorded, then re-raised
            outcome = {"outcome": "raised",
                       "error": "%s: %s" % (type(exc).__name__, exc)}
            raise
        finally:
            try:
                partial = arm.summary() if hasattr(arm, "summary") else {}
            except Exception:                        # noqa: BLE001
                partial = {}
            merged = dict(partial)
            merged.update(outcome or {})
            run.end_record(**{k: v for k, v in merged.items()
                              if k in ("outcome", "steps", "model_calls",
                                       "score", "levels_completed", "scorecard")})
            run.write_run_json(merged)
            outcome = merged
    return outcome


def _scratch_policy(ledger_path: str):
    """A pool of one, at an explicit absolute path, for offline proofs.

    `spend_gate` deliberately has no environment variable that relocates the
    ledger -- "a pool everyone can point somewhere else is a pool of one" -- and
    this is that pool of one, reachable only by someone who typed the path. The
    caps are the tracked policy's, so a scratch run exercises the same
    arithmetic; only the file differs, and `run_start` records which file.

    It refuses to be pointed at a *run* ledger. The two files are different
    formats with different writers -- `spend_gate` records are `{"kind": ...}`
    under an OS lock, `proxy/ledger.py` records are `{"event": ...}` under an
    in-process one -- and mixing them corrupts both: the gate fails closed on a
    line it cannot total, and `read_ledger` sees spend lines it cannot place.
    Cheap to check and the same class of failure the gate exists to stop, so it
    is checked rather than assumed.
    """
    from proxy.spend_gate import SpendGateError, SpendPolicy   # noqa: PLC0415
    absolute = os.path.abspath(ledger_path)
    parts = absolute.replace("\\", "/").lower().split("/")
    if os.path.basename(absolute).lower() == "ledger.jsonl" or "runs" in parts:
        raise SpendGateError(
            "%s looks like a run ledger, not a spend pool. A spend pool holds "
            "`kind` records under a cross-process lock and a run ledger holds "
            "`event` records under an in-process one; pointing one at the other "
            "corrupts both and the gate then fails closed on a file it cannot "
            "total. Choose a path outside runs/ and not named ledger.jsonl."
            % absolute)
    tracked = SpendPolicy.load()
    return SpendPolicy({"v": "1.0",
                        "pool": "theoria-arm-scratch",
                        "usd_ceiling": tracked.usd_ceiling,
                        "action_ceiling": tracked.action_ceiling,
                        "ledger": os.path.abspath(ledger_path),
                        "default_ttl_seconds": tracked.default_ttl_seconds,
                        "lock_timeout_seconds": tracked.lock_timeout_seconds,
                        "default_run_caps": tracked.default_run_caps})


def main(argv=None) -> int:
    """Offline smoke: the whole shell against `proxy/mock`, no key, no network."""
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--mock", action="store_true",
                    help="offline environment: no key, no network, no quota")
    ap.add_argument("--desk", action="store_true",
                    help="run the real theorize desk even against the mock, so "
                         "the inner loop is exercised before a live action is spent")
    ap.add_argument("--game", default="g50t-5849a774")
    ap.add_argument("--slug", default=None)
    ap.add_argument("--budget", type=int, default=12)
    ap.add_argument("--commands", type=int, default=2000)
    ap.add_argument("--model", default="claude-opus-5")
    ap.add_argument("--cost-ceiling", type=float, default=20.0)
    ap.add_argument("--wall-clock", type=float, default=3 * 3600)
    ap.add_argument("--pool", default=None,
                    help="draw on a SCRATCH spend pool at this path instead of "
                         "the shared one. For offline proofs only: fictional "
                         "dollars must not land in proxy/var/spend_gate.jsonl. "
                         "The pool actually used is printed and recorded in "
                         "run_start, so a run against a scratch pool says so.")
    args = ap.parse_args(argv)

    from inner.loop import TheoriaArm                 # noqa: PLC0415

    slug = args.slug or (time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
                         + "-" + args.game.split("-")[0])

    # 先算后花, at the entry point: the caps are computed from the declared
    # level and refused against the pool's global free headroom before a socket
    # or a subprocess exists. An offline dry run still reserves a call's
    # ceiling rather than $0.00 -- an offline run that unexpectedly reaches the
    # desk must be refused by the pool, not merely by an `if`.
    gate = spend_mod.SpendGate() if args.pool is None else spend_mod.SpendGate(
        _scratch_policy(args.pool))
    caps = spend_mod.plan_caps(
        actions=args.budget, commands=args.commands,
        cost_ceiling_usd=None if (args.mock and not args.desk) else args.cost_ceiling,
        wall_clock_s=args.wall_clock, gate=gate)
    print(canonical({"spend_plan": caps.as_json(),
                     "pool": gate.fingerprint()}))

    def factory(env_base, run):
        return TheoriaArm(env_base=env_base, run=run, game_id=args.game,
                          budget_actions=args.budget,
                          budget_commands=args.commands,
                          model=args.model,
                          cost_ceiling_usd=args.cost_ceiling,
                          wall_clock_s=args.wall_clock,
                          offline=args.mock and not args.desk)

    expect_pool = ({"pool": gate.policy.pool,
                    "ledger_abspath": os.path.abspath(gate.ledger_path)}
                   if args.pool else None)

    if args.mock:
        from proxy.mock.arc_mock import DEFAULT_KEY, MockArc   # noqa: PLC0415
        with MockArc(api_key=DEFAULT_KEY, games=[args.game]) as arc:
            summary = play(args.game, slug, factory, env_upstream=arc.base_url,
                           env_key=DEFAULT_KEY, require_key=False,
                           caps=caps, spend_gate=gate, expect_pool=expect_pool)
    else:
        summary = play(args.game, slug, factory, caps=caps, spend_gate=gate,
                       expect_pool=expect_pool)

    print(canonical({k: v for k, v in summary.items() if k != "frames"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
