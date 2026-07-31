"""How much real traffic each of the two proxies has actually carried.

S32 asks a question the paper's "dual-agent architecture" sentence depends on:
of the two proxies `Theoria.md` Phase 1 seals the arm behind -- the
**environment** proxy and the **model** proxy -- how many real requests has
each one handled? "65 model_call records, all 401" is only a finding when it
is read against a denominator, so this module produces denominators and
nothing else. It adjudicates nothing; `VERDICT.md` beside it does that.

## What counts as "handled by a proxy"

A record written by `proxy.ledger`'s writer in `LEDGER_FORMAT v1.0` shape,
carrying an `http` leg. That is the only evidence that the bytes crossed a
proxy boundary, and it is deliberately narrower than "the arm made a request":

* `baseline-arms/ledger.jsonl` (656 records) is the baseline arms' **own**
  client format -- no `event`, no `http.forwarded`. Those requests never
  crossed the environment proxy and are not counted as its traffic.
* `arc-recon/data/recon_ledger.jsonl` (1273 records) is `arc-recon/client.py`
  talking to `BASE_URL = "https://three.arcprize.org"` **directly**, with its
  own `X-API-Key` header. Recon is shared ground, not an arm, and it predates
  the seal; its legs are not environment-proxy traffic either. Counted here as
  a named exclusion rather than left out silently, because "the environment
  proxy handled 1009 requests" and "the repo made 1009 requests" are different
  claims and the paper must not conflate them.

## Live upstream vs local fixture

`run_start.env_upstream` says where the proxy was pointed. `https://` means the
real ARC endpoint -- traffic that was authenticated, billed against the rate
budget, and could not have been faked. A `http://127.0.0.1:<port>` upstream is
a fixture server in the same test, and a proxy that forwarded to a fixture has
exercised its code path but has *not* been validated on real traffic. Both are
reported; only the first supports a "validated on real traffic" claim.

## The model proxy

Its whole recorded history is one file, `theoria-arm/evidence/model-proxy-401.jsonl`,
archived by A3 with `theoria-arm/evidence/README.md`. It is read here rather
than summarised from that README, so the counts in the paper are recomputed
from the record on every run of the gate.

Only shapes and counts are read off the model-proxy file. Header **names** are
reported (`authorization`); no header value, no credential, and no environment
variable value is read, printed or written by anything in this module -- S32's
hard red line, and the reason `_incident_headers` returns names only.
"""

import json
import os
from typing import Any, Dict, Iterable, List, Optional

#: Repository root, from this file rather than from the caller's cwd: the gate
#: is run from a worktree and from `verify-lab/` both.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

#: Every ledger the environment proxy has ever written for the theoria arm.
ARM_RUNS = os.path.join(ROOT, "theoria-arm", "runs")

#: The model proxy's entire recorded traffic against a **real** provider.
MODEL_EVIDENCE = os.path.join(ROOT, "theoria-arm", "evidence",
                              "model-proxy-401.jsonl")

#: The model proxy's traffic against a **fixture** provider. `proxy/runner.py`
#: runs the env proxy, the model proxy and a mock arm in one interpreter, and
#: this is the ledger those runs left. It matters to the verdict: without it
#: the model proxy would be code that had never carried a completed request at
#: all, and with it the gap is specifically "never on a real provider" rather
#: than "never". Read from `proxy/`, which is READ-ONLY evidence here.
MODEL_FIXTURE_LEDGER = os.path.join(ROOT, "proxy", "var", "ledger.jsonl")

#: Request ledgers that are *not* proxy traffic, and why. Named so a reader can
#: check the exclusion instead of trusting it.
NOT_PROXY_TRAFFIC = {
    os.path.join("baseline-arms", "ledger.jsonl"):
        "baseline-arms' own client format; no proxy `http` leg on any record",
    os.path.join("arc-recon", "data", "recon_ledger.jsonl"):
        "arc-recon/client.py talks to the upstream directly with its own key",
}


def read_jsonl(path: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def _is_live(upstream: Optional[str]) -> bool:
    """True when the proxy was pointed at the real endpoint.

    Scheme, not hostname: every fixture in this repo is `http://127.0.0.1:<port>`
    and the real endpoint is `https://`. Matching on the scheme keeps the game
    host out of this file and still separates the two cases exactly.
    """
    return bool(upstream) and str(upstream).startswith("https://")


def env_proxy_traffic(runs_dir: str = ARM_RUNS) -> Dict[str, Any]:
    """Requests the environment proxy handled, split live / fixture.

    One entry per run directory holding a `ledger.jsonl`. `env_meta` and
    `env_step` are the two events that carry an `http` leg written by the
    proxy; `run_start`, `run_end`, `model_call` and `incident` are written by
    the arm's own process and are not requests the proxy forwarded.
    """
    runs: List[Dict[str, Any]] = []
    if os.path.isdir(runs_dir):
        for name in sorted(os.listdir(runs_dir)):
            path = os.path.join(runs_dir, name, "ledger.jsonl")
            if not os.path.exists(path):
                continue
            records = read_jsonl(path)
            upstream = None
            for record in records:
                if record.get("event") == "run_start":
                    upstream = record.get("env_upstream")
                    break
            legs = [r for r in records
                    if r.get("event") in ("env_meta", "env_step")
                    and isinstance(r.get("http"), dict)]
            statuses: Dict[str, int] = {}
            forwarded = 0
            for leg in legs:
                http = leg["http"]
                key = str(http.get("status"))
                statuses[key] = statuses.get(key, 0) + 1
                if http.get("forwarded") is True:
                    forwarded += 1
            runs.append({
                "run": name,
                "upstream_is_live": _is_live(upstream),
                "requests": len(legs),
                "env_meta": sum(1 for r in legs if r["event"] == "env_meta"),
                "env_step": sum(1 for r in legs if r["event"] == "env_step"),
                "forwarded_true": forwarded,
                "status_counts": statuses,
            })

    live = [r for r in runs if r["upstream_is_live"]]
    fixture = [r for r in runs if not r["upstream_is_live"]]

    def total(rows: Iterable[Dict[str, Any]], key: str) -> int:
        return sum(r[key] for r in rows)

    statuses: Dict[str, int] = {}
    for row in live:
        for key, count in row["status_counts"].items():
            statuses[key] = statuses.get(key, 0) + count

    return {
        "ledgers": len(runs),
        "requests_total": total(runs, "requests"),
        "requests_live_upstream": total(live, "requests"),
        "requests_fixture_upstream": total(fixture, "requests"),
        "forwarded_true_total": total(runs, "forwarded_true"),
        "live_runs": len(live),
        "fixture_runs": len(fixture),
        "live_status_counts": statuses,
        "runs": runs,
    }


def _incident_headers(records: Iterable[Dict[str, Any]]) -> List[str]:
    """Header **names** named by bypass incidents. Never a value.

    S32's red line, and the reason this is a function rather than an inline
    comprehension: the model-proxy evidence exists precisely because a client
    presented a credential of its own, so a careless reader of this file is one
    key lookup away from writing that credential into a deliverable.
    """
    return sorted({str(r.get("header")) for r in records
                   if r.get("header") is not None})


def model_proxy_traffic(path: str = MODEL_EVIDENCE) -> Dict[str, Any]:
    """Requests the model proxy handled, and how many of them were answered.

    `succeeded` is the number that matters to the claim: a request the upstream
    refused with 401 exercised the proxy's boundary but carried no model
    traffic, so it cannot validate a model-proxy leg of a "dual-agent" claim.
    """
    records = read_jsonl(path)
    calls = [r for r in records if r.get("event") == "model_call"]
    incidents = [r for r in records if r.get("event") == "incident"]
    bypass = [r for r in incidents if r.get("kind") == "bypass_attempt"]

    statuses: Dict[str, int] = {}
    for call in calls:
        key = str((call.get("http") or {}).get("status"))
        statuses[key] = statuses.get(key, 0) + 1

    return {
        "records_total": len(records),
        "model_calls": len(calls),
        "status_counts": statuses,
        "refused_401": statuses.get("401", 0),
        "succeeded": sum(count for key, count in statuses.items()
                         if key.isdigit() and 200 <= int(key) < 300),
        "incidents": len(incidents),
        "bypass_attempts": len(bypass),
        "bypass_headers": _incident_headers(bypass),
    }


def model_proxy_fixture_traffic(path: str = MODEL_FIXTURE_LEDGER) -> Dict[str, Any]:
    """Completed `model_call`s the model proxy carried against a fixture.

    Kept separate from `model_proxy_traffic` and never summed with it. A
    fixture provider answering 200 proves the proxy's forward path, its ledger
    write and its pricing hook execute; it proves nothing about whether the
    designed route works against a real provider, which is the only thing a
    "dual-agent, both validated" sentence would be claiming.

    `proxy/var/` is **gitignored** (`proxy/.gitignore:3`), so this file is
    present on the machine that ran the proxy's own end-to-end flow and absent
    from a fresh clone. `present: false` therefore means "not on this
    checkout", never "the model proxy has never completed a request" -- the
    tracked, reproducible form of the same evidence is the proxy track's suite
    (`proxy/tests/test_e2e.py`), and a run of this census that wants the fixture
    number must say which machine it was taken on. The numbers observed on the
    2026-07-31 census machine are frozen in this cell's run directory.
    """
    records = read_jsonl(path)
    calls = [r for r in records if r.get("event") == "model_call"]
    statuses: Dict[str, int] = {}
    for call in calls:
        key = str((call.get("http") or {}).get("status"))
        statuses[key] = statuses.get(key, 0) + 1
    return {
        "present": os.path.exists(path),
        "gitignored": True,
        "records_total": len(records),
        "model_calls": len(calls),
        "status_counts": statuses,
        "succeeded": sum(count for key, count in statuses.items()
                         if key.isdigit() and 200 <= int(key) < 300),
        "arms": sorted({str(r.get("arm")) for r in calls if r.get("arm")}),
        "models": sorted({str(r.get("model")) for r in calls if r.get("model")}),
    }


def excluded_ledgers(root: str = ROOT) -> List[Dict[str, Any]]:
    """The request ledgers that exist but are not proxy traffic, with counts."""
    out = []
    for rel, why in sorted(NOT_PROXY_TRAFFIC.items()):
        path = os.path.join(root, rel)
        records = read_jsonl(path)
        out.append({"path": rel.replace(os.sep, "/"),
                    "records": len(records),
                    "proxy_legs": sum(1 for r in records
                                      if isinstance(r.get("http"), dict)),
                    "why_excluded": why})
    return out


def census() -> Dict[str, Any]:
    """Both proxies, both denominators, and the named exclusions."""
    env = env_proxy_traffic()
    model = model_proxy_traffic()
    fixture = model_proxy_fixture_traffic()
    return {
        "env_proxy": env,
        "model_proxy": model,
        "model_proxy_fixture": fixture,
        "excluded": excluded_ledgers(),
        "headline": {
            "env_proxy_requests_live": env["requests_live_upstream"],
            "env_proxy_requests_total": env["requests_total"],
            "model_proxy_requests": model["records_total"],
            "model_proxy_model_calls": model["model_calls"],
            "model_proxy_succeeded": model["succeeded"],
            "model_proxy_fixture_succeeded": fixture["succeeded"],
        },
    }


if __name__ == "__main__":
    print(json.dumps(census(), indent=2, sort_keys=True))
