"""Backend selection: Fast Downward if it is reachable, the BFS stub otherwise.

The FD path is implemented and unexercised -- no Fast Downward is installed in
this sandbox (see STATUS.md for the attempt log).  It is kept because switching
backends must not mean rewriting callers or tests: both return the same Plan.
"""

import os
import shutil
import subprocess
import tempfile
from typing import List, Optional

FD_ENV_VARS = ("FAST_DOWNWARD", "FAST_DOWNWARD_HOME", "DOWNWARD_ROOT")
FD_EXECUTABLES = ("fast-downward.py", "fast-downward", "downward")
FD_SEARCH = "astar(blind())"          # optimal for unit costs, like the stub


def find_fast_downward() -> Optional[str]:
    """Path to a runnable Fast Downward, or None."""
    for variable in FD_ENV_VARS:
        value = os.environ.get(variable)
        if not value:
            continue
        if os.path.isfile(value) and os.access(value, os.X_OK):
            return value
        for name in FD_EXECUTABLES:
            candidate = os.path.join(value, name)
            if os.path.isfile(candidate):
                return candidate
    for name in FD_EXECUTABLES:
        found = shutil.which(name)
        if found:
            return found
    return None


def parse_sas_plan(text: str) -> List[str]:
    """Fast Downward's plan file: one `(action args)` per line, then a cost comment."""
    plan = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(";"):
            continue
        plan.append(line if line.startswith("(") else "(%s)" % line)
    return plan


def run_fast_downward(executable: str, domain_path: str, problem_path: str,
                      timeout: int = 120) -> List[str]:
    """Call Fast Downward for an optimal plan and read the plan file back."""
    with tempfile.TemporaryDirectory() as workdir:
        plan_path = os.path.join(workdir, "sas_plan")
        command = [executable, "--plan-file", plan_path,
                   domain_path, problem_path, "--search", FD_SEARCH]
        if executable.endswith(".py"):
            command = ["python"] + command
        completed = subprocess.run(
            command, cwd=workdir, capture_output=True, text=True, timeout=timeout
        )
        if not os.path.exists(plan_path):
            raise RuntimeError(
                "Fast Downward produced no plan file (exit %d): %s"
                % (completed.returncode, completed.stderr[-500:])
            )
        with open(plan_path, "r", encoding="utf-8") as fh:
            return parse_sas_plan(fh.read())
