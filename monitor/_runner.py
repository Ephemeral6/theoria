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


def main():
    pid_str, prompt_path, log_path, model = sys.argv[1:5]
    text = open(prompt_path, encoding="utf-8").read()
    claude = shutil.which("claude")
    t0 = time.time()
    log = open(log_path, "a", encoding="utf-8")
    err = open(log_path + ".err", "a", encoding="utf-8")
    log.write("=== runner start %s model=%s ===\n" % (pid_str, model))
    log.flush()
    try:
        proc = subprocess.run(
            [claude, "-p", text, "--model", model,
             "--dangerously-skip-permissions"],
            cwd=ROOT, stdout=log, stderr=err, stdin=subprocess.DEVNULL)
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
