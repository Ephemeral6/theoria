"""Does the game id reach the model? Driven, not read.

Theoria.md:353 -- 硬规:游戏 ID 永不进模型上下文,全程匿名化. This script tests
that empirically instead of trusting the comments:

* the environment is `proxy/mock` (no key, no network, no quota);
* the model is a stub at `ModelDesk._invoke`, the single seam between this arm
  and money -- $0.00 is spent, no subprocess starts, nothing leaves the machine;
* the run slug is campaign-shaped (`...-g50t-leg01`), because `harness/campaign.py`
  builds it from `game_id.split("-")[0]` and the run directory is therefore
  named after the game. Anything that interpolates a path into a prompt leaks.

Every string that would have been handed to `claude -p` is captured verbatim
and grepped for the dev-pile stems and suffixes.

    python runs/20260728T233900Z-A3-campaign-devpile/probe_anon.py
"""

import json
import os
import re
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ARM)

import _bootstrap                                        # noqa: E402,F401

NEEDLES = ["g50t", "5849a774", "sk48", "d8078629", "tn36", "ef4dde99",
           "ar25", "0c556536"]

GAME = "g50t-5849a774"
#: Campaign-shaped: `harness/campaign.py:_leg_slug` -> "<utc>-g50t-leg01".
SLUG = "20260729T000000Z-g50t-leg01"

REPLY = """Here are the three blocks.

=== THEORY ===
```
semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Cart { pos: Coord, color: Int }  # arc-colour: 2
  Cart [segment: uniform_color ev: t0-t3 compress: 0]

events:
  event moved(o, dir)

rules:
  rule step_up [ev: t0 cov: 1/1]
    when act=key(1) and free(above(Cart)) then moved(Cart, up)

goal:
  goal count(Cart) = 1

laws:
  invariant cart_unique count(Cart) = 1 [status: observed]
```

=== PLAYBOOK ===
```
prefer   try_unvisited_first                  [ev: 1/1 levels]
```

=== LOG ===
```json
[{"id": "O-01", "subject": "obj0 (colour 2)", "verdict": "accept",
  "as": "Cart", "why": "the only cell that moves"}]
```
"""

ENVELOPE = {"result": REPLY, "subtype": "success", "total_cost_usd": 0.0,
            "usage": {"input_tokens": 1, "output_tokens": 1,
                      "cache_read_input_tokens": 0}}


def hits(text, where):
    out = []
    low = (text or "").lower()
    for needle in NEEDLES:
        for match in re.finditer(re.escape(needle), low):
            start = max(0, match.start() - 70)
            out.append({"where": where, "needle": needle,
                        "offset": match.start(),
                        "context": text[start:match.end() + 70].replace("\n", "\\n")})
    return out


# --------------------------------------------------------------- part 1
def drive_the_arm(tmp):
    """The real loop, the real prompt builder, a stubbed subprocess."""
    from harness import run as run_mod                   # noqa: PLC0415
    from harness import spend as spend_mod               # noqa: PLC0415
    from inner.loop import TheoriaArm                    # noqa: PLC0415
    from proxy.mock.arc_mock import DEFAULT_KEY, MockArc  # noqa: PLC0415
    from proxy.spend_gate import SpendGate               # noqa: PLC0415

    # Runs land in a temp tree, not in the repo. The slug still carries the
    # game stem, which is the property under test.
    run_mod.RUNS_DIR = os.path.join(tmp, "runs")
    os.makedirs(run_mod.RUNS_DIR, exist_ok=True)

    pool = os.path.join(tmp, "anon-probe-pool.jsonl")
    gate = SpendGate(run_mod._scratch_policy(pool))
    caps = spend_mod.plan_caps(actions=10, commands=2000,
                               cost_ceiling_usd=20.0, gate=gate)

    prompts = []
    refused_records = []

    def factory(env_base, run):
        arm = TheoriaArm(env_base=env_base, run=run, game_id=GAME,
                         budget_actions=10, offline=False,
                         model="stub-no-subprocess", cost_ceiling_usd=20.0)

        def invoke(prompt, model):                       # noqa: ANN001
            prompts.append({"model": model, "prompt": prompt})
            return dict(ENVELOPE), 1234, ""

        arm.desk._invoke = invoke        # the only seam that costs money

        # Worked around, and the workaround is itself a finding: at this commit
        # `proxy/canon.py` refuses the top-level `beat`/`label`/`transport`/
        # `proxied`/`proxy_gap` that `harness/modelcall.py` writes, so every
        # desk call raises AFTER the subprocess has been paid for and the arm
        # never gets a manual. Swallowed here so the rest of the inner loop --
        # certify, plan, probe, the second theorize with books and surprises in
        # the prompt -- is actually exercised.
        real = run.run.model_call

        def tolerant(**fields):
            try:
                return real(**fields)
            except Exception as exc:                     # noqa: BLE001
                refused_records.append({"error": "%s: %s" % (type(exc).__name__, exc),
                                        "fields": fields})
                return {}

        run.run.model_call = tolerant
        return arm

    with MockArc(api_key=DEFAULT_KEY, games=[GAME]) as mock:
        summary = run_mod.play(
            GAME, SLUG, factory, env_upstream=mock.base_url,
            env_key=DEFAULT_KEY, require_key=False, caps=caps, spend_gate=gate,
            expect_pool={"pool": gate.policy.pool,
                         "ledger_abspath": os.path.abspath(gate.ledger_path)})
    return (summary, prompts, os.path.join(run_mod.RUNS_DIR, SLUG),
            refused_records)


# --------------------------------------------------------------- part 2
def forced_engine_error(tmp):
    """Adversarial: an engine whose candidate write fails names the path.

    `world/adapt.py` records `{"error": ..., "traceback": ...}` for any engine
    that raises, and `inner/theorize.evidence_brief` dumps the whole engine
    report into the prompt. An OSError's message carries the path it failed on
    -- and that path is inside the run directory, which is named after the game.
    Reproduced here by making `candidates.jsonl` a directory.
    """
    from inner import theorize                           # noqa: PLC0415
    from world import adapt                              # noqa: PLC0415
    from world.frames import FrameStore, Step            # noqa: PLC0415

    run_dir = os.path.join(tmp, "runs", SLUG + "-forced")
    os.makedirs(run_dir, exist_ok=True)
    # A path no `open()` on this platform will accept, so every engine that is
    # handed it fails the way a full disk or a revoked ACL would.
    candidates = os.path.join(run_dir, 'cand"idates.jsonl')

    store = FrameStore()
    grid_a = [[0, 0, 0, 0], [0, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 3]]
    grid_b = [[0, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 3]]
    grid_c = [[0, 0, 0, 0], [0, 0, 2, 0], [0, 0, 0, 0], [0, 0, 0, 3]]
    for idx, (action, grid) in enumerate((("RESET", grid_a),
                                          ("ACTION1", grid_b),
                                          ("ACTION2", grid_c))):
        store.add(Step(idx, action, [grid], status=200, state="NOT_FINISHED"))

    engines = adapt.run_engines(store, candidates)

    class _Books:
        theory = ""
        playbook = ""

    prompt = theorize.build_prompt(store, engines, _Books(), candidates, [])
    return prompt, engines


def main():
    tmp = tempfile.mkdtemp(prefix="theoria-anon-probe-")
    findings = {"needles": NEEDLES, "tmp": tmp, "hits": []}
    try:
        summary, prompts, run_dir, refused = drive_the_arm(tmp)
        print("== part 1: the real loop against the mock ==")
        print("run dir            : %s" % run_dir)
        print("outcome            : %s (%s)" % (summary.get("outcome"),
                                                summary.get("stopped_because")))
        print("model calls        : %d" % summary.get("model_calls", 0))
        print("prompts captured   : %d" % len(prompts))
        print("desk spend (usd)   : %s"
              % (summary.get("desk") or {}).get("cli_cost_usd"))
        print("canon-refused recs : %d" % len(refused))
        if refused:
            print("  first refusal    : %.150s" % refused[0]["error"])
        import json as _json
        for i, rec in enumerate(refused, 1):
            # ONLY `request` is model-bound. The rest of the record (game_id,
            # proxy_gap, the campaign name) is ledger vocabulary and is
            # SUPPOSED to name the game -- scanned separately so the two can
            # never be confused.
            findings["hits"] += hits(
                _json.dumps(rec["fields"].get("request"), sort_keys=True, default=str),
                "model_call#%d.request (model-bound)" % i)
            findings.setdefault("ledger_only_hits", []).extend(hits(
                _json.dumps({k: v for k, v in rec["fields"].items() if k != "request"},
                            sort_keys=True, default=str),
                "model_call#%d non-request fields (ledger only)" % i))

        for idx, entry in enumerate(prompts, 1):
            found = hits(entry["prompt"], "prompt#%d (%d chars)"
                         % (idx, len(entry["prompt"])))
            findings["hits"] += found
            print("  prompt %2d: %6d chars, %d hit(s)"
                  % (idx, len(entry["prompt"]), len(found)))

        # The same text again, from the two places it is persisted.
        desk_dir = os.path.join(run_dir, "desk")
        for name in sorted(os.listdir(desk_dir)) if os.path.isdir(desk_dir) else []:
            with open(os.path.join(desk_dir, name), encoding="utf-8") as fh:
                findings["hits"] += hits(fh.read(), "transcript:" + name)

        ledger = os.path.join(run_dir, "ledger.jsonl")
        n_calls = 0
        events = {}
        if os.path.exists(ledger):
            with open(ledger, encoding="utf-8") as fh:
                for line in fh:
                    record = json.loads(line)
                    kind = record.get("event")
                    events[kind] = events.get(kind, 0) + 1
                    if kind != "model_call":
                        continue
                    n_calls += 1
                    # `request.prompt` is the only string that was actually
                    # handed to the subprocess. Everything else in `request`
                    # is this arm's own bookkeeping vocabulary (`proxy_gap`
                    # names the spend-gate campaign, which contains the game
                    # id by design) and never left the machine.
                    request = record.get("request") or {}
                    findings["hits"] += hits(
                        request.get("prompt") if isinstance(request, dict)
                        else json.dumps(request),
                        "ledger model_call#%d request.prompt" % n_calls)
                    rest = {k: v for k, v in record.items() if k != "request"}
                    if isinstance(request, dict):
                        rest["request_minus_prompt"] = {
                            k: v for k, v in request.items() if k != "prompt"}
                    findings.setdefault("ledger_only_hits", []).extend(hits(
                        json.dumps(rest, sort_keys=True, default=str),
                        "ledger model_call#%d everything except the prompt" % n_calls))
        print("ledger model_call  : %d   (events: %s)"
              % (n_calls, json.dumps(events, sort_keys=True)))
        for name in ("theorize.json", "desk_failures.json"):
            path = os.path.join(run_dir, name)
            if os.path.exists(path):
                with open(path, encoding="utf-8") as fh:
                    blob = fh.read()
                print("  %-20s %d chars, compile_ok=%s"
                      % (name, len(blob), re.findall(r'"compile_ok": (\w+)', blob)))
                # On disk, not in a prompt: `theorize.json` records the
                # generated forms by absolute path. Kept in its own bucket so
                # a disk artefact can never be counted as model context.
                findings.setdefault("disk_only_hits", []).extend(
                    hits(blob, "artifact:" + name))

        # Task 3: do the books themselves carry it?
        books = os.path.join(run_dir, "books")
        for root, _dirs, names in os.walk(books):
            for name in names:
                path = os.path.join(root, name)
                try:
                    with open(path, encoding="utf-8") as fh:
                        text = fh.read()
                except (OSError, UnicodeDecodeError):
                    continue
                findings["hits"] += hits(
                    text, "books:" + os.path.relpath(path, books))

        # What certify's proof layer did -- the Lean channel is only live when
        # a Lean form was generated and `lean` is on PATH.
        certify_path = os.path.join(run_dir, "certify.json")
        if os.path.exists(certify_path):
            with open(certify_path, encoding="utf-8") as fh:
                reports = json.load(fh)
            for idx, report in enumerate(reports, 1):
                exp = report.get("expensive") or {}
                print("  certify %d: lean available=%s ok=%s detail=%.90s"
                      % (idx, exp.get("available"), exp.get("ok"),
                         str(exp.get("detail"))))
                print("             lean_file=%s" % exp.get("lean_file"))

        surprises = os.path.join(run_dir, "surprises.jsonl")
        if os.path.exists(surprises):
            with open(surprises, encoding="utf-8") as fh:
                blob = fh.read()
            print("  surprise payload hits: %d" % len(hits(blob, "surprises")))
            findings["surprises_hits"] = hits(blob, "surprises.jsonl (NOT "
                                                   "necessarily model-bound)")

        print()
        print("== part 2: forced engine I/O error ==")
        prompt, engines = forced_engine_error(tmp)
        forced = hits(prompt, "forced-error prompt")
        print("prompt chars       : %d" % len(prompt))
        print("hits in prompt     : %d" % len(forced))
        for hit in forced[:6]:
            print("  %s @%d: ...%s..." % (hit["needle"], hit["offset"],
                                          hit["context"]))
        findings["forced_error_hits"] = forced

        print()
        print("== verdict ==")
        print("model-bound hits   : %d" % len(findings["hits"]))
        for hit in findings["hits"][:20]:
            print("  %(where)s :: %(needle)s :: %(context)s" % hit)
        with open(os.path.join(HERE, "probe_anon_result.json"), "w",
                  encoding="utf-8", newline="\n") as fh:
            json.dump(findings, fh, indent=1, sort_keys=True)
            fh.write("\n")
        return 0
    finally:
        if os.environ.get("KEEP_PROBE_TMP"):
            print("\n(kept: %s)" % tmp)
        else:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
