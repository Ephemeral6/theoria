"""Session wrapper: observability for headless launches (upgrade #5).

    python _runner.py <prompt_id> <prompt_path> <log_path> <model>

Runs the claude CLI with the prompt file's text, streaming stdout to the log
and stderr to <log>.err, then stamps an EXIT line with code and duration —
so a dead session always leaves a cause of death. Exit facts are mirrored to
dispatch-logs/exits.json (own file, no registry race).
"""

import json
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EXITS = os.path.join(HERE, "dispatch-logs", "exits.json")


def record_exit(pid_str, info):
    try:
        data = {}
        if os.path.exists(EXITS):
            data = json.load(open(EXITS, encoding="utf-8"))
        data.setdefault(pid_str, []).append(info)
        tmp = EXITS + ".tmp"
        json.dump(data, open(tmp, "w", encoding="utf-8"), indent=2)
        os.replace(tmp, EXITS)
    except Exception:
        pass  # observability must never take the session down with it


def resolve(pid_str):
    """One-arg form: derive prompt file, log path and model from the id, so the
    scheduled task command stays well under schtasks' 261-char /TR limit."""
    import datetime
    import re
    prompts = os.path.join(HERE, "prompts")
    if pid_str.startswith("W-"):
        return (os.path.join(prompts, "W-worker.md"),
                os.path.join(HERE, "dispatch-logs", "%s-%s.log" % (
                    pid_str,
                    __import__("datetime").datetime.now(
                        __import__("datetime").timezone.utc
                    ).strftime("%Y%m%dT%H%M%SZ"))),
                "opus")
    match = None
    for name in sorted(os.listdir(prompts)):
        if not name.endswith(".md"):
            continue
        m = re.match(r"([A-Z]\d+-[a-z0-9][a-z0-9-]*|[PRMBA]-\d+)", name)
        if m and m.group(1) == pid_str:
            match = name
            break
    if not match:
        raise SystemExit("no prompt file for %s" % pid_str)
    prompt_path = os.path.join(prompts, match)
    head = open(prompt_path, encoding="utf-8").read(600)
    mt = re.search(r"<!--\s*model:\s*(opus|sonnet|haiku)\s*-->", head)
    model = mt.group(1) if mt else "opus"
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ")
    log_path = os.path.join(HERE, "dispatch-logs",
                            "%s-%s.log" % (pid_str, stamp))
    return prompt_path, log_path, model


def main():
    if len(sys.argv) == 2:
        pid_str = sys.argv[1]
        prompt_path, log_path, model = resolve(pid_str)
    else:
        pid_str, prompt_path, log_path, model = sys.argv[1:5]
    text = open(prompt_path, encoding="utf-8").read()
    if pid_str.startswith("W-"):
        header = "你的工人号是 `%s`（board.py 的所有命令都用它）。\n\n" % pid_str
        text = header + text
    claude = shutil.which("claude")
    t0 = time.time()
    log = open(log_path, "a", encoding="utf-8")
    err = open(log_path + ".err", "a", encoding="utf-8")
    log.write("=== runner start %s model=%s ===\n" % (pid_str, model))
    log.flush()
    try:
        # The prompt goes in on STDIN, never as an argv string: under Task
        # Scheduler the `claude` .cmd shim mangles multi-line UTF-8 arguments
        # and the session receives an empty prompt (observed 2026-07-28).
        proc = subprocess.run(
            [claude, "-p", "--model", model,
             "--dangerously-skip-permissions"],
            cwd=ROOT, stdout=log, stderr=err,
            input=text.encode("utf-8"))
        code = proc.returncode
    except Exception as exc:
        err.write("runner exception: %r\n" % (exc,))
        code = -1
    dur = int(time.time() - t0)
    log.write("\n=== EXIT %s after %ds ===\n" % (code, dur))
    log.close()
    err.close()
    record_exit(pid_str, {"code": code, "seconds": dur,
                          "log": os.path.basename(log_path),
                          "ended": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                                 time.gmtime())})
    sys.exit(code if code >= 0 else 1)


if __name__ == "__main__":
    main()
