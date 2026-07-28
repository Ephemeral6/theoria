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

ARM = "theoria"                                       # registered in ledger.ARMS

RUNS_DIR = _bootstrap.path("runs")

#: Where a test's throwaway run goes. `runs/` is the archive -- the thing Phase
#: 4 reads back to account for every action this arm ever spent -- and a fixture
#: that lands in it is indistinguishable, by directory listing, from an
#: experiment that cost money. Two of them did land there, and the archive audit
#: had to tell them apart by hand. They go somewhere else now, and
#: `armtools.verify_provenance` fails if one reappears under `runs/`.
FIXTURE_RUNS_DIR = _bootstrap.path(".pytest-runs")


def new_run_id() -> str:
    return "r-" + uuid.uuid4().hex[:16]


def run_dir(slug: str, root: Optional[str] = None) -> str:
    path = os.path.join(root or RUNS_DIR, slug)
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
                 ledger_path: Optional[str] = None,
                 runs_root: Optional[str] = None):
        self.game_id = game_id
        self.slug = slug
        self.run_id = run_id or new_run_id()
        self.dir = run_dir(slug, runs_root)
        self.ledger_path = ledger_path or os.path.join(self.dir, "ledger.jsonl")

        self.ledger = Ledger(self.ledger_path)
        self.run = RunLedger(self.ledger, self.run_id, ARM)
        self.guard = SealedPileGuard()

        # The proxy's own envelope stays short: it covers 5xx/429/transport,
        # which are genuinely transient in seconds. The 400 wave, which is
        # transient in *minutes*, is the arm's job (harness/arc.py).
        self._cfg = EnvProxyConfig(
            run_id=self.run_id, arm=ARM, upstream=env_upstream,
            api_key=env_key, require_key=require_key,
            ledger=self.ledger, run=self.run, guard=self.guard,
            max_attempts=env_max_attempts)
        self.proxy: Optional[EnvProxy] = None
        self.started_at: Optional[float] = None

    # -- lifecycle ---------------------------------------------------------
    def __enter__(self) -> "Run":
        self.proxy = EnvProxy(self._cfg).start()
        self.started_at = time.time()
        return self

    def __exit__(self, *exc) -> None:
        if self.proxy:
            self.proxy.stop()

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
         start_extra: Optional[Dict[str, Any]] = None,
         runs_root: Optional[str] = None) -> Dict[str, Any]:
    """Drive one run to completion, and write `run_end` whatever happens.

    `runs_root` defaults to the archive. A caller whose run is not archive
    material -- a test, a smoke -- passes `FIXTURE_RUNS_DIR` and keeps it out.
    """
    outcome: Dict[str, Any] = {"outcome": "not_started"}
    with Run(game_id, slug, run_id=run_id, env_upstream=env_upstream,
             env_key=env_key, require_key=require_key,
             runs_root=runs_root) as run:
        run.start_record(**(start_extra or {}))
        arm = arm_factory(run.env_base, run)
        try:
            outcome = arm.play()
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
    args = ap.parse_args(argv)

    from inner.loop import TheoriaArm                 # noqa: PLC0415

    slug = args.slug or (time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
                         + "-" + args.game.split("-")[0])

    def factory(env_base, run):
        return TheoriaArm(env_base=env_base, run=run, game_id=args.game,
                          budget_actions=args.budget,
                          budget_commands=args.commands,
                          model=args.model,
                          cost_ceiling_usd=args.cost_ceiling,
                          wall_clock_s=args.wall_clock,
                          offline=args.mock and not args.desk)

    if args.mock:
        from proxy.mock.arc_mock import DEFAULT_KEY, MockArc   # noqa: PLC0415
        with MockArc(api_key=DEFAULT_KEY, games=[args.game]) as arc:
            summary = play(args.game, slug, factory, env_upstream=arc.base_url,
                           env_key=DEFAULT_KEY, require_key=False)
    else:
        summary = play(args.game, slug, factory)

    print(canonical({k: v for k, v in summary.items() if k != "frames"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
