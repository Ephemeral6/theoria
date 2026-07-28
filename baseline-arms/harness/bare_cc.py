"""The bare-Claude-Code arm: no theory layer, no engines, no world model.

Claude sees the frame, picks an action, sees the next frame. That is the whole
loop. This is the column `Theoria.md` 1.12 calls "裸 Claude Code / 零分工" --
everything is left to the LLM -- and this module's only job is to measure what
that costs across model tiers.

Three things are deliberate and load-bearing:

  * **The model runs in a neutral working directory outside this repository.**
    Claude Code walks parent directories looking for CLAUDE.md; started inside
    the repo it would read Theoria.md's design, the pile cut, and this very
    harness. A baseline that has read the theory is not a baseline. See
    DECISIONS.md D-009.
  * **Tools are off.** The arm gets frames and returns an action. Giving it Bash
    inside a scratch dir would measure a different thing.
  * **Failures are recorded, not smoothed.** A step whose retries run out is
    written to the ledger with frame=null and failed=true (D-006).

    python -m harness.bare_cc --game sk48-d8078629 --model claude-sonnet-5
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

from . import arc_client, ledger

PROVIDER = "anthropic-claude-code-cli"

MODEL_TIERS = {
    "cheap": "claude-haiku-4-5-20251001",
    "mid": "claude-sonnet-5",
    "expensive": "claude-opus-5",
}

# 0-15 rendered as one hex digit each: a 64x64 frame is 64 lines of 64 chars.
HEX = "0123456789abcdef"


# ---------------------------------------------------------------- rendering
def render_grid(grid: List[List[int]]) -> str:
    return "\n".join("".join(HEX[v & 0xF] for v in row) for row in grid)


def describe_change(prev: Optional[List[List[int]]], cur: List[List[int]]) -> str:
    """A one-line diff, so the model is not forced to eyeball 4096 cells."""
    if prev is None:
        return "(first frame)"
    changed = [(r, c, prev[r][c], cur[r][c])
               for r in range(len(cur)) for c in range(len(cur[0]))
               if prev[r][c] != cur[r][c]]
    if not changed:
        return "no cells changed"
    if len(changed) > 12:
        rows = sorted({r for r, _, _, _ in changed})
        cols = sorted({c for _, c, _, _ in changed})
        return ("%d cells changed, rows %d-%d, cols %d-%d"
                % (len(changed), rows[0], rows[-1], cols[0], cols[-1]))
    return "; ".join("(%d,%d) %x->%x" % (r, c, a, b) for r, c, a, b in changed)


# ------------------------------------------------------------------- prompt
PREAMBLE = """You are playing an ARC-AGI-3 game through a text interface.

The world is a 64x64 grid. Each cell is one hex digit, 0-f, standing for a
colour. You are shown the current frame, and a short history of what you did
and what changed.

You do not know the rules. Nobody will tell you them. Work them out by acting.

Reply with EXACTLY one line and nothing else:

    ACTION <n>              for a keyboard action, e.g. ACTION 3
    ACTION <n> <x> <y>      for a click action, x and y in 0..63
    GIVE UP                 if you are certain you cannot make progress

No explanation, no code fences, no extra lines."""


def build_prompt(frame: List[List[int]], available: List[int], history: List[str],
                 levels_completed: int, win_levels: int, step_idx: int,
                 budget: int, change: str) -> str:
    hist = "\n".join(history[-12:]) if history else "(nothing yet)"
    return "\n\n".join([
        PREAMBLE,
        "Available actions this turn: %s" % ", ".join(str(a) for a in available),
        "Levels completed: %d of %d" % (levels_completed, win_levels),
        "Step %d of at most %d." % (step_idx, budget),
        "Recent history (most recent last):\n%s" % hist,
        "What changed since the previous frame: %s" % change,
        "Current frame:\n%s" % render_grid(frame),
        "Your one line:",
    ])


# -------------------------------------------------------------- model call
class ModelError(RuntimeError):
    pass


def claude_bin() -> str:
    """On Windows the npm shim is claude.cmd; CreateProcess will not find the
    extensionless POSIX wrapper that `which claude` reports under Git Bash."""
    for name in ("claude.cmd", "claude.exe", "claude"):
        found = shutil.which(name)
        if found:
            return found
    raise ModelError("the `claude` CLI is not on PATH")


def call_model(prompt: str, model: str, cwd: str, timeout: int = 300) -> Dict[str, Any]:
    """One `claude -p` invocation. Returns the parsed CLI result envelope.

    The prompt goes on **stdin**, not argv. A frame is 64 lines of hex, and a
    multi-line argv argument is mangled by the Windows `claude.cmd` shim badly
    enough that `--model` never reaches the CLI -- it then silently falls back
    to the stale `ANTHROPIC_MODEL` alias and 404s. Single-line prompts work
    either way, which is exactly why this hid until the first real frame.
    See DECISIONS.md D-010.
    """
    cmd = [claude_bin(), "-p", "--model", model, "--output-format", "json",
           "--max-turns", "1"]
    env = dict(os.environ)
    # The arm must never be able to reach the game credential.
    env.pop("ARC_API_KEY", None)
    # The stale Vendor2/* aliases are left in place on purpose. --model carries
    # the full id and overrides them, whereas *clearing* them makes the CLI fall
    # back to a different default model for its internal calls -- which is how
    # this arm first failed. See DECISIONS.md D-010.

    started = time.time()
    try:
        proc = subprocess.run(cmd, cwd=cwd, env=env, input=prompt,
                              capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise ModelError("claude -p timed out after %ds" % timeout)
    elapsed_ms = int((time.time() - started) * 1000)

    try:
        envelope = json.loads(proc.stdout)
    except json.JSONDecodeError:
        raise ModelError("unparseable CLI output: %s" % (proc.stdout or proc.stderr)[:300])
    envelope["_elapsed_ms"] = elapsed_ms
    return envelope


ACTION_RE = re.compile(r"ACTION\s*(\d+)(?:\D+(\d+)\D+(\d+))?", re.IGNORECASE)


def parse_action(text: str) -> Tuple[Optional[int], Optional[Dict[str, int]], str]:
    """(action_id, data, note). action_id None means give up / unparseable."""
    if not text:
        return None, None, "empty reply"
    if re.search(r"\bGIVE\s*UP\b", text, re.IGNORECASE):
        return None, None, "gave up"
    m = ACTION_RE.search(text)
    if not m:
        return None, None, "unparseable: %r" % text[:80]
    action_id = int(m.group(1))
    data = None
    if m.group(2) is not None and m.group(3) is not None:
        data = {"x": max(0, min(63, int(m.group(2)))),
                "y": max(0, min(63, int(m.group(3))))}
    return action_id, data, "ok"


# ---------------------------------------------------------------- the loop
# After this many consecutive failures, drop the ALB routing cookies so the next
# attempt is a fresh replica draw. See `_redraw` and arc-recon INC-007a.
REDRAW_EVERY = 5


def _redraw(client: arc_client.ArcClient, failures: int) -> None:
    """Let go of the replica pin every few failures.

    D-005 sized these envelopes against a transport that was re-routed on every
    attempt -- eight or thirty identical retries worked precisely because each
    was an independent draw at a replica that might hold the session. The cookie
    jar removes that: once pinned, every retry goes to the same replica, so if
    THAT replica is the broken one, retrying is only waiting. Dropping the pins
    restores the draw while keeping `GAMESESSION`.

    In practice this should almost never fire -- arc-recon measured 1.00 attempt
    per command after the fix -- but the envelope must not have become weaker
    than the thing it replaced.
    """
    if failures and failures % REDRAW_EVERY == 0:
        redraw = getattr(client, "clear_routing_cookies", None)
        if callable(redraw):
            redraw()


def resilient(client: arc_client.ArcClient, path: str, body: Dict[str, Any],
              note: str, tries: int = 8) -> Tuple[int, Any, int]:
    """D-005: 400 'game not found' is transient. Retry it."""
    status, parsed = -1, None
    for k in range(tries):
        status, parsed = client.request("POST", path, body=body, note=note,
                                        raise_on_error=False)
        if status == 200:
            return status, parsed, k + 1
        _redraw(client, k + 1)
        time.sleep(0.4 * (k + 1))
    return status, parsed, tries


def reset_with_retry(client: arc_client.ArcClient, game_id: str, card_id: str,
                     tries: int = 30) -> Tuple[Optional[Dict[str, Any]], int]:
    for k in range(tries):
        status, body = client.reset(game_id, card_id, raise_on_error=False)
        if status == 200 and isinstance(body, dict):
            return body, k + 1
        _redraw(client, k + 1)
        time.sleep(0.5)
    return None, tries


def play(game_id: str, model: str, budget: int, card_id: Optional[str] = None,
         client: Optional[arc_client.ArcClient] = None,
         action_retries: int = 8, model_retries: int = 3,
         cost_ceiling: Optional[float] = None, on_step=None,
         verbose: bool = True) -> Dict[str, Any]:
    """`cost_ceiling` aborts mid-episode. This matters: the full run gives one
    episode a budget of up to 1070 actions, so a ceiling checked only between
    episodes would not be checked for eleven hours. `on_step(summary)` is
    called after every step so the caller can checkpoint at the same cadence.
    """
    """One episode: one game, one model. Returns the run summary."""
    client = client or arc_client.ArcClient()
    client.assert_playable(game_id)                     # fails closed on sealed
    run_id = "bare_cc-%s-%s-%s" % (game_id.split("-")[0], model, uuid.uuid4().hex[:8])

    own_card = card_id is None
    if own_card:
        card_id = client.open_scorecard(
            tags=["baseline-arms", "bare_cc", model],
            opaque={"run_id": run_id})["card_id"]

    summary: Dict[str, Any] = {
        "run_id": run_id, "arm": "bare_cc", "game_id": game_id, "model": model,
        "budget": budget, "started": ledger.utcnow(),
        "actions_ok": 0, "actions_failed": 0, "model_calls": 0,
        "http_calls_gameplay": 0, "cost_usd": 0.0,
        "input_tokens": 0, "output_tokens": 0,
        "cache_read_tokens": 0, "cache_creation_tokens": 0,
        "levels_completed": 0, "win_levels": None, "final_state": None,
        "outcome": "unknown", "reset_attempts": 0,
    }

    body, reset_attempts = reset_with_retry(client, game_id, card_id)
    summary["reset_attempts"] = reset_attempts
    if body is None:
        summary["outcome"] = "no_reset_window"
        summary["ended"] = ledger.utcnow()
        if own_card:
            client.close_scorecard(card_id)
        return summary

    guid = body["guid"]
    frame = body["frame"][-1]
    available = body.get("available_actions") or [1]
    summary["win_levels"] = body.get("win_levels")
    summary["levels_completed"] = body.get("levels_completed") or 0

    ledger.env_step(game_id, run_id, "bare_cc", model, "RESET", body["frame"], 0,
                    state=body.get("state"),
                    levels_completed=body.get("levels_completed"),
                    win_levels=body.get("win_levels"),
                    available_actions=available)

    # A neutral cwd, outside the repo: no CLAUDE.md, no Theoria.md (D-009).
    sandbox = tempfile.mkdtemp(prefix="bare-cc-")
    history: List[str] = []
    prev_frame: Optional[List[List[int]]] = None
    change = "(first frame)"

    try:
        for step_idx in range(1, budget + 1):
            if cost_ceiling is not None and summary["cost_usd"] >= cost_ceiling:
                summary["outcome"] = "spend_ceiling_hit"
                break
            prompt = build_prompt(frame, available, history,
                                  summary["levels_completed"],
                                  summary["win_levels"] or 0,
                                  step_idx, budget, change)
            # Model calls are flaky in the same way the game API is: an
            # occasional call comes back is_error with a null result and then
            # the identical prompt succeeds. Losing a whole cell to one of
            # those wastes the money already spent on it, so retry the call and
            # only give up after `model_retries` consecutive failures.
            env = None
            last_model_error = None
            for attempt in range(model_retries):
                try:
                    env = call_model(prompt, model, sandbox)
                except ModelError as exc:
                    last_model_error, env = str(exc), None
                else:
                    usage = env.get("usage") or {}
                    summary["model_calls"] += 1
                    summary["cost_usd"] += float(env.get("total_cost_usd") or 0.0)
                    summary["input_tokens"] += int(usage.get("input_tokens") or 0)
                    summary["output_tokens"] += int(usage.get("output_tokens") or 0)
                    summary["cache_read_tokens"] += int(usage.get("cache_read_input_tokens") or 0)
                    summary["cache_creation_tokens"] += int(usage.get("cache_creation_input_tokens") or 0)
                    ledger.model_call(run_id, PROVIDER, model, usage,
                                      game_id=game_id, step_idx=step_idx,
                                      total_cost_usd=env.get("total_cost_usd"),
                                      is_error=env.get("is_error"),
                                      duration_ms=env.get("_elapsed_ms"),
                                      prompt_chars=len(prompt),
                                      attempt=attempt + 1)
                    if not env.get("is_error"):
                        break
                    last_model_error = str(env.get("result"))[:300]
                    summary["model_call_retries"] = summary.get("model_call_retries", 0) + 1
                    env = None
                time.sleep(1.5 * (attempt + 1))

            if env is None:
                summary["outcome"] = "model_error"
                summary["error"] = last_model_error
                break

            action_id, data, note = parse_action(env.get("result") or "")
            if action_id is None:
                history.append("step %d: %s -> stopping" % (step_idx, note))
                summary["outcome"] = "gave_up" if note == "gave up" else "unparseable_reply"
                summary["stop_note"] = note
                ledger.env_step(game_id, run_id, "bare_cc", model, note, None,
                                step_idx, failed=True, reason=note)
                break

            request_body: Dict[str, Any] = {"game_id": game_id, "card_id": card_id,
                                            "guid": guid}
            if data:
                request_body["data"] = data
            status, rb, tries = resilient(client, "/api/cmd/ACTION%d" % action_id,
                                          request_body,
                                          note="bare_cc %s step %d" % (model, step_idx),
                                          tries=action_retries)
            summary["http_calls_gameplay"] += tries

            if status != 200 or not isinstance(rb, dict):
                summary["actions_failed"] += 1
                msg = rb.get("message") if isinstance(rb, dict) else str(rb)[:120]
                # D-006: record the failure, do not smooth it away.
                ledger.env_step(game_id, run_id, "bare_cc", model,
                                {"id": action_id, "data": data}, None, step_idx,
                                failed=True, http_status=status, reason=msg,
                                http_tries=tries)
                history.append("step %d: ACTION %d -> refused by server (%s)"
                               % (step_idx, action_id, status))
                change = "action was refused; frame unchanged"
                if summary["actions_failed"] >= 10:
                    summary["outcome"] = "api_unusable"
                    break
                continue

            summary["actions_ok"] += 1
            guid = rb.get("guid", guid)
            new_frame = rb["frame"][-1]
            available = rb.get("available_actions") or available
            prev_levels = summary["levels_completed"]
            summary["levels_completed"] = rb.get("levels_completed") or 0
            summary["final_state"] = rb.get("state")

            ledger.env_step(game_id, run_id, "bare_cc", model,
                            {"id": action_id, "data": data}, rb["frame"], step_idx,
                            state=rb.get("state"),
                            levels_completed=rb.get("levels_completed"),
                            win_levels=rb.get("win_levels"),
                            available_actions=available,
                            frames_returned=len(rb["frame"]),
                            http_tries=tries)

            prev_frame, frame = frame, new_frame
            change = describe_change(prev_frame, frame)
            gained = " LEVEL UP" if summary["levels_completed"] > prev_levels else ""
            history.append("step %d: ACTION %d%s -> %s%s"
                           % (step_idx, action_id,
                              " (%d,%d)" % (data["x"], data["y"]) if data else "",
                              change, gained))
            if verbose:
                print("  step %-3d ACTION %-2s tries=%d lv=%d/%s %s%s"
                      % (step_idx, action_id, tries, summary["levels_completed"],
                         summary["win_levels"], change[:60], gained))

            if on_step is not None:
                on_step(summary)

            if rb.get("state") in ("WIN", "GAME_OVER"):
                summary["outcome"] = rb["state"].lower()
                break
        else:
            summary["outcome"] = "budget_exhausted"
    finally:
        if own_card:
            client.close_scorecard(card_id)

    summary["ended"] = ledger.utcnow()
    summary["card_id"] = card_id
    summary["http_amplification"] = (
        round(summary["http_calls_gameplay"] / summary["actions_ok"], 2)
        if summary["actions_ok"] else None)
    return summary


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--budget", type=int, default=20)
    ap.add_argument("--action-retries", type=int, default=8)
    args = ap.parse_args(argv)

    summary = play(args.game, args.model, args.budget,
                   action_retries=args.action_retries)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["outcome"] not in ("no_reset_window", "api_unusable") else 1


if __name__ == "__main__":
    sys.exit(main())
