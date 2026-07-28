"""Compile `theory.dsl` into its four co-derived forms.

```
theory.dsl
 ├─ theory.py    execution — the only predictor         (gen_python_a0)
 ├─ theory.pddl  planning  — domain + problem           (gen_pddl_a0)
 ├─ theory.lean  proof     — machine reader             (gen_lean_a0)
 └─ theory.md    rendering — human reader               (theory_compiler.gen_markdown)
```

Only `theory.md` comes from the compiler track unmodified: `gen_markdown` is
genuinely AST-general, so it is reused as-is.  The other three backends are A0's
own for the reasons in DECISIONS.md D-A0-011.  The parser — the executable form
of the frozen `dsl_grammar_v0.1` contract — is upstream in all four cases.

Constraint 4: everything under `theory/generated/` is a generated form and is
never hand-edited.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap  # noqa: F401,E402

from theory_compiler.generators.gen_markdown import generate_markdown  # noqa: E402
from theory_compiler.parser.theory_parser import parse_theory  # noqa: E402

from compile import problem as problem_mod  # noqa: E402
from compile.dialect import parse_semantics  # noqa: E402
from compile.gen_lean_a0 import ArenaEscape, generate_lean  # noqa: E402
from compile.gen_pddl_a0 import generate_pddl  # noqa: E402
from compile.gen_python_a0 import generate_python  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def compile_theory(dsl_path: str, trace_path: str, problem_name: str,
                   out_dir: str, name_by_color=None) -> dict:
    text = open(dsl_path, encoding="utf-8").read()
    ast = parse_theory(text)
    semantics = parse_semantics(text)        # raises if the manual does not say
    prob = problem_mod.derive(trace_path, problem_name, name_by_color)
    os.makedirs(out_dir, exist_ok=True)

    written = {}

    py = generate_python(ast, prob, semantics)
    written["theory.py"] = _write(os.path.join(out_dir, "theory.py"), py)

    md = render_markdown(ast, semantics)
    written["theory.md"] = _write(os.path.join(out_dir, "theory.md"), md)

    domain, instance = generate_pddl(ast, prob)
    written["domain.pddl"] = _write(os.path.join(out_dir, "domain.pddl"), domain)
    written["problem.pddl"] = _write(os.path.join(out_dir, "problem.pddl"), instance)

    # The Lean form is the first thing that walks the manual's whole state space,
    # so it is the first thing that can notice `step` leaving it.  That is a real
    # certify failure and is reported, not raised past the caller.
    try:
        lean = generate_lean(ast, prob, os.path.join(out_dir, "theory.py"),
                             semantics=semantics)
        written["theory.lean"] = _write(os.path.join(out_dir, "theory.lean"), lean)
    except ArenaEscape as exc:
        written["theory.lean"] = 0
        written["theory.lean.error"] = "ArenaEscape: %s" % exc

    written["problem.json"] = _write(
        os.path.join(out_dir, "problem.json"),
        json.dumps(prob.as_json(), indent=2, sort_keys=True) + "\n",
    )
    return written


def render_markdown(ast, semantics) -> str:
    """`gen_markdown` is reused verbatim. It now renders the semantics itself.

    This used to append a second "How a Turn Works" section from
    `Semantics.rendering()`, because the shared generator had none. It has had
    one since the `semantics:` section was adopted into
    `CONTRACTS/dsl_grammar_v0.2.md`, and appending anyway put **the same three
    facts in the same document twice**, in two different wordings — "if no rule
    applies to something" and "if no rule applies to an object" — with the
    second copy stranded at the end, after the laws. Found by `cold-start-a2`,
    which runs these backends on a second world and read the output.

    `semantics` stays in the signature and `Semantics.rendering()` stays as a
    function: the A0 dialect still validates the section, and the reports still
    render it. What is gone is the duplicate.

    Still a deterministic pretty-printer with no model in the path (constraint 1
    and Theoria 1.8's "不过 LLM,不许润色").
    """
    del semantics                    # validated upstream; rendered by gen_markdown
    return generate_markdown(ast)


def _write(path: str, text: str) -> int:
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    return len(text)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dsl", default=os.path.join(ROOT, "theory", "theory.dsl"))
    parser.add_argument("--trace",
                        default=os.path.join(ROOT, "artifacts", "raw_trace.jsonl"))
    parser.add_argument("--problem", default="a0-base")
    parser.add_argument("--out", default=os.path.join(ROOT, "theory", "generated"))
    args = parser.parse_args()

    written = compile_theory(args.dsl, args.trace, args.problem, args.out)
    for name in sorted(written):
        print("%-14s %6d bytes" % (name, written[name]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
