"""The bench's coverage gate: Nuru's rule, on the gated modules only."""
import importlib.util
import json
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[1] / "tools" / "coverage_check.py"
spec = importlib.util.spec_from_file_location("coverage_check", PATH)
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)


def report(**modules):
    return {"files": {f"nuru/evals/{name}": {"summary": {"num_statements": n, "covered_lines": c}} for name, (n, c) in modules.items()}}


@pytest.mark.parametrize("modules, problem", [
    ({"small.py": (150, 150), "big.py": (200, 181)}, None),
    ({"small.py": (150, 149), "big.py": (200, 181)}, "small.py: 149/150 lines, 99.3%; needs 100% (small)"),
    ({"small.py": (150, 150), "big.py": (200, 180)}, "big.py: 180/200 lines, 90.0%; needs above 90%"),
    ({"small.py": (150, 150)}, "big.py: not in the report (no test imported it)"),
])
def test_a_small_module_needs_every_line_and_a_large_one_more_than_90_percent(modules, problem):
    found = check.failures(report(**modules), gated=["small.py", "big.py"])
    assert found == ([problem] if problem else [])


def test_the_command_exits_nonzero_on_a_failure_and_names_it(tmp_path, capsys):
    path = tmp_path / "coverage.json"
    path.write_text(json.dumps(report(**{name: (10, 9) for name in check.GATED})))
    assert check.main([str(path)]) == 1
    assert "decision_layer/cases.py: 9/10 lines" in capsys.readouterr().out
    path.write_text(json.dumps(report(**{name: (10, 10) for name in check.GATED})))
    assert check.main([str(path)]) == 0


def test_run_as_a_script_its_exit_status_is_the_result(tmp_path, monkeypatch):
    import runpy
    path = tmp_path / "coverage.json"
    path.write_text(json.dumps(report(**{name: (10, 10) for name in check.GATED})))
    monkeypatch.setattr("sys.argv", ["coverage_check.py", str(path)])
    with pytest.raises(SystemExit) as exit:
        runpy.run_path(str(PATH), run_name="__main__")
    assert exit.value.code == 0
