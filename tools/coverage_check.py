"""Nuru's F13 coverage rule (tools/coverage_gate.py there) for the bench's own code: every gated module
above 90% of its executable lines, and all of them in a small one (at most 150). Gated are the modules
whose code changed since the bench left Nuru (2026-11-01), even by one value, and this checker itself;
add a module here when you change its code. Reads `coverage json` output whose paths start at the Nuru
checkout (nuru/evals/...).

    uv run --locked python nuru/evals/tools/coverage_check.py coverage.json
"""
import json
import sys
from pathlib import Path

GATED = ["decision_layer/cases.py", "decision_layer/common.py", "decision_layer/drive_turn.py", "decision_layer/run_suite.py",
         "decision_layer/tier_labels.py", "model_bakeoff/bakeoff.py", "obsidian_remote/live_wp01.py",
         "token_estimate/measure.py", "tools/coverage_check.py"]
SMALL = 150
FLOOR = 90.0


def failures(report: dict, gated=GATED) -> list[str]:
    files = {name.split("nuru/evals/", 1)[-1]: data["summary"] for name, data in report["files"].items()}
    problems = []
    for module in gated:
        summary = files.get(module)
        if summary is None:
            problems.append(f"{module}: not in the report (no test imported it)")
            continue
        statements, covered = summary["num_statements"], summary["covered_lines"]
        short = covered < statements if statements <= SMALL else covered * 100 / statements <= FLOOR
        if short:
            need = "100% (small)" if statements <= SMALL else f"above {FLOOR:g}%"
            problems.append(f"{module}: {covered}/{statements} lines, {covered * 100 / statements:.1f}%; needs {need}")
    return problems


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    problems = failures(json.loads(Path(argv[0]).read_text(encoding="utf-8")))
    print("\n".join(problems) or f"coverage: {len(GATED)} gated modules pass")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
