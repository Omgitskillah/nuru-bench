"""run_suite's runner paths without a model: which tests a --tests spec selects, refused ID sets, a
turn that runs past its time or crashes (and is cleaned up), the batch's token summary, and --enforce's
one-batch config; and cases.load_cases refusing a malformed case before any of it starts."""
import importlib
import json
import signal
import subprocess
from pathlib import Path

import pytest

EVALS = Path(__file__).resolve().parents[1] / "decision_layer"


@pytest.fixture
def runner(monkeypatch, tmp_path):
    monkeypatch.syspath_prepend(str(EVALS))
    module = importlib.import_module("run_suite")
    monkeypatch.setattr(module, "ENV_NURU", tmp_path / "no-env-nuru")  # not the developer's model setting
    monkeypatch.delenv("NURU_MAIN_MODEL", raising=False)
    return module


@pytest.fixture
def cases_module(monkeypatch):
    monkeypatch.syspath_prepend(str(EVALS))
    return importlib.import_module("cases")


@pytest.mark.parametrize("spec, selected", [
    ("quick", [3, 4, 10, 24, 26, 28, 29, 34]),
    ("1-3,5", [1, 2, 3, 5]),
    ("38", [38]),
])
def test_a_tests_spec_selects_those_tests(runner, spec, selected):
    assert runner.parse_tests(spec) == selected


def test_quick_is_a_copy_a_caller_can_change(runner):
    runner.parse_tests("quick").append(99)
    assert 99 not in runner.parse_tests("quick")


def _cases(tmp_path, cases):
    path = tmp_path / "cases.json"
    path.write_text(json.dumps(cases))
    return path


ONE_TURN = {"name": "x", "turns": [{"prompt": "p", "checks": {}}]}


@pytest.mark.parametrize("cases, tests, message", [
    ({"3": ONE_TURN}, "3", "overlap legacy prompts"),  # 3 is one of the 34 single prompts
    ({"90": ONE_TURN}, "91", r"unknown test IDs: \[91\]"),
])
def test_the_batch_refuses_ids_it_cannot_run_before_setting_anything_up(runner, monkeypatch, tmp_path, cases, tests, message):
    monkeypatch.setattr(runner, "RUNS", tmp_path / "runs")
    monkeypatch.setattr("sys.argv", ["run_suite", "--cases", str(_cases(tmp_path, cases)), "--tests", tests])
    with pytest.raises(SystemExit, match=message):
        runner.main()
    assert not (tmp_path / "runs").exists()


@pytest.mark.parametrize("case, message", [
    ({"name": "x"}, "nonempty turns list"),
    ({"name": "x", "turns": []}, "nonempty turns list"),
    ({"name": "x", "turns": [{"prompt": "  ", "checks": {}}]}, "nonempty prompt"),
    ({"name": "x", "turns": [{"prompt": "p"}]}, "per-turn regex checks"),
    ({"name": "x", "turns": [{"prompt": "p", "checks": ["(?i)x"]}]}, "per-turn regex checks"),
])
def test_a_malformed_case_is_refused_when_the_cases_load(cases_module, tmp_path, case, message):
    with pytest.raises(ValueError, match=message):
        cases_module.load_cases(_cases(tmp_path, {"90": case}))


class _Process:
    """Stands in for drive_turn's process: `wait` either returns `returncode` or runs past its time."""
    pid = 4321

    def __init__(self, *, hangs=False, returncode=0, writes=None, log_dir=None, stderr=""):
        self.hangs, self.returncode, self.writes, self.log_dir, self.stderr = hangs, returncode, writes, log_dir, stderr
        self.waits = []

    def __call__(self, command, **kwargs):
        self.command = command
        kwargs["stderr"].write(self.stderr)
        if self.log_dir:  # the session started and logged before anything went wrong
            (self.log_dir / "20261101_abc123.jsonl").write_text("{}\n")
        if self.writes is not None:
            Path(command[command.index("--out") + 1]).write_text(json.dumps(self.writes))
        return self

    def wait(self, timeout=None):
        self.waits.append(timeout)
        if self.hangs and len(self.waits) == 1:
            raise subprocess.TimeoutExpired("drive_turn", timeout)
        return self.returncode


def _run(runner, monkeypatch, tmp_path, process, case=None):
    logs = tmp_path / "logs"
    logs.mkdir(exist_ok=True)
    monkeypatch.setattr(runner.subprocess, "Popen", process)
    killed = []
    monkeypatch.setattr(runner.os, "killpg", lambda pid, sig: killed.append((pid, sig)))
    return runner.run_turn(tmp_path, {"NURU_LOG_DIR": str(logs)}, "a prompt", "off", 60, case), killed


def test_a_turn_past_its_time_is_killed_with_its_servers_and_named_by_its_session(runner, monkeypatch, tmp_path):
    process = _Process(hangs=True, log_dir=tmp_path / "logs")
    (tmp_path / "logs").mkdir()
    (tmp_path / "logs" / "20261031_older.jsonl").write_text("{}\n")  # an earlier turn's log isn't this one
    record, killed = _run(runner, monkeypatch, tmp_path, process)
    assert record == {"timed_out": True, "timeout_seconds": 60, "session_id": "abc123"}
    assert killed == [(4321, signal.SIGKILL)], "the whole process group: the MCP servers too"
    assert process.waits == [60, None], "killed, then reaped"


def test_a_sequence_gets_its_deadline_per_turn_plus_the_backstop(runner, monkeypatch, tmp_path):
    process = _Process(hangs=True)
    case = {"turns": [{"prompt": "one"}, {"prompt": "two"}]}
    record, killed = _run(runner, monkeypatch, tmp_path, process, case)
    assert record == {"timed_out": True, "timeout_seconds": 60 * 2 + 300}
    assert process.command[process.command.index("--turn-timeout") + 1] == "60"


@pytest.mark.parametrize("returncode, writes", [(1, None), (1, {"reply": "partial"}), (0, None)])
def test_a_turn_that_exits_badly_or_writes_no_result_is_a_crash_with_its_stderr(runner, monkeypatch, tmp_path, returncode, writes):
    process = _Process(returncode=returncode, writes=writes, stderr="x" * 5000 + "Traceback: boom")
    record, killed = _run(runner, monkeypatch, tmp_path, process)
    assert record["crashed"] is True and record["returncode"] == returncode
    assert record["stderr_tail"].endswith("Traceback: boom") and len(record["stderr_tail"]) == 3000
    assert killed == []


def test_the_token_summary_adds_up_each_test_and_the_round(runner, tmp_path):
    rows = [
        {"test": 3, "model_calls": [{"prompt_tokens": 100, "completion_tokens": 10, "cache_read_tokens": 40},
                                    {"prompt_tokens": 50, "completion_tokens": None}]},
        {"test": 3, "model_calls": None},  # a run that timed out has none
        {"test": 38, "model_calls": [{"prompt_tokens": 7, "completion_tokens": 2, "cache_write_tokens": 5}]},
    ]
    (tmp_path / "results.jsonl").write_text("\n".join(json.dumps(r) for r in rows))
    text = runner.token_summary(tmp_path)
    saved = json.loads((tmp_path / "tokens.json").read_text())
    assert saved["per_test"]["3"] == {"runs": 2, "calls": 2, "in": 150, "out": 10, "cached": 40, "cache_writes": 0}
    assert saved["total"] == {"runs": 3, "calls": 3, "in": 157, "out": 12, "cached": 40, "cache_writes": 5}
    assert "157 in" in text and "test 38" in text


@pytest.mark.parametrize("enforce, points", [("all", None), ("gate_write,check_claim", ["gate_write", "check_claim"])])
def test_enforce_writes_a_one_batch_config_marked_as_test_only(runner, monkeypatch, tmp_path, enforce, points):
    import yaml
    vault = tmp_path / "fixture"
    vault.mkdir()
    (vault / "note.md").write_text("fixture")
    monkeypatch.setattr(runner, "DUMMY_VAULT", vault)
    monkeypatch.setattr(runner, "RUNS", tmp_path / "runs")
    monkeypatch.setattr(runner.manifest, "build", lambda *args: {})
    monkeypatch.setattr(runner.subprocess, "run", lambda command, *, env, **kwargs: Path(env["OBSIDIAN_SEMANTIC_DB"]).write_bytes(b"i"))
    monkeypatch.setattr(runner, "run_turn", lambda *args: {"reply": "ok", "tool_calls": [], "turn_seconds": 0})
    monkeypatch.setattr("sys.argv", ["run_suite", "--tests", "3", "--enforce", enforce])
    runner.main()
    [batch] = (tmp_path / "runs").iterdir()
    text = (batch / "decision_layer.yaml").read_text()
    assert text.startswith("# TEST ONLY - written by run_suite.py --enforce for one batch.")
    config = yaml.safe_load(text)
    shipped = yaml.safe_load((runner.REPO / "config" / "decision_layer.yaml").read_text())
    chosen = points or list(shipped["decision_points"])
    assert config["decision_points"] == {p: "enforce" if p in chosen else mode for p, mode in shipped["decision_points"].items()}
    assert all(t["calibration"]["labels"] == 0 for options in config["thresholds"].values()
               for thresholds in options.values() for t in thresholds.values())
    assert config["database"] == str(batch / "decisions.sqlite3")
    assert yaml.safe_load((runner.REPO / "config" / "decision_layer.yaml").read_text()) == shipped, "the shipped config is untouched"
