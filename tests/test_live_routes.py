"""Run the live harness against fake sessions/processes: no model, server or network."""
import importlib.util
import json
import signal
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

PATH = Path(__file__).resolve().parents[1] / "obsidian_remote/live_wp01.py"
spec = importlib.util.spec_from_file_location("live_routes", PATH)
live = importlib.util.module_from_spec(spec)
spec.loader.exec_module(live)


@pytest.mark.parametrize("answer", ["yes", None])
def test_direct_child_records_events_questions_and_write_receipts(monkeypatch, tmp_path, answer):
    from core import session
    from core.service import host
    from core.questions import Question, YES_NO
    closed = []

    class FakeSession:
        def ask(self, text):
            assert self.answer_question(SimpleNamespace(text="approve?")) == ([answer] if answer else None)
            self.on_tool_outcome("call", "write_note", {}, None, True)
            yield session.ToolCall("search", {"query": text})
            yield session.Text("found")
            yield session.Ask(Question(text="Which?", kind=YES_NO))
            if text == "fail":
                yield session.Failure("stopped")

        def close(self):
            closed.append(True)

    monkeypatch.setattr(session.Session, "start", lambda **kwargs: FakeSession())
    monkeypatch.setattr(host, "_receipt", lambda *a: {"state": "applied", "path": "nuru/new.md", "extra": 1})
    monkeypatch.setattr(live, "isolate", lambda: None)
    monkeypatch.setenv("VAULT_PATH", str(tmp_path))
    case, out = tmp_path / "case.json", tmp_path / "out.json"
    case.write_text(json.dumps({"turns": ["ok", "fail"], "answer": answer}))
    live.child(case, out)
    a, b = json.loads(out.read_text())["turns"]
    assert a["state"] == "completed" and a["reply"] == "found" and a["ask"] == "Which?"
    assert a["questions"] == 1 and a["receipts"] == [{"state": "applied", "path": "nuru/new.md"}]
    assert b["state"] == "failed" and b["message"] == "stopped"
    assert closed == [True]


@pytest.mark.parametrize("mode", ["ok", "crash", "missing", "timeout"])
def test_direct_process_deadline_reaps_its_tree(monkeypatch, tmp_path, mode):
    kills, waits = [], []

    class Process:
        pid = 321
        returncode = 1 if mode == "crash" else 0

        def wait(self, timeout=None):
            waits.append(timeout)
            if mode == "timeout" and timeout is not None:
                raise subprocess.TimeoutExpired("child", timeout)

    def popen(command, **kwargs):
        assert "--child" in command and kwargs["start_new_session"]
        if mode == "ok":
            (tmp_path / "direct.json").write_text('{"turns": []}')
        return Process()

    monkeypatch.setattr(live.subprocess, "Popen", popen)
    monkeypatch.setattr(live.os, "killpg", lambda *a: kills.append(a))
    result = live.run_direct(tmp_path, {}, {"turns": ["hi"]}, 3)
    if mode == "ok":
        assert result == {"turns": []}
    elif mode == "timeout":
        assert result == {"timed_out": True} and waits == [3, None]
        assert kills == [(321, signal.SIGKILL)]
    else:
        assert result["crashed"] is True


def test_a_timeout_does_not_hide_an_unauthorized_write(tmp_path):
    grade = live.score({}, {"timed_out": True}, {
        "added": ["user/private.md"], "changed": [], "removed": [],
    }, tmp_path)
    assert not grade["pass"] and grade["unauthorized_write"]
    assert grade["why"] == ["timed out"]


@pytest.mark.parametrize("mode", ["ok", "crash", "timeout", "noport", "slowstop"])
def test_plugin_route_cleans_up_and_uses_scratch_credentials(monkeypatch, tmp_path, mode):
    service = tmp_path / "service"
    service.mkdir()
    env = {"NURU_SERVICE_DIR": str(service), "VAULT_PATH": str(tmp_path / "vault")}
    actions = []

    def token(command, **kwargs):
        (service / "clients").mkdir()
        (service / "clients/obsidian.token").write_text("scratch-token")

    class Serve:
        pid = 123
        stderr = iter([] if mode == "noport" else ["http://127.0.0.1:9876\n"])

        def send_signal(self, sig):
            actions.append(("signal", sig))

        def wait(self, timeout=None):
            actions.append(("wait", timeout))
            if mode == "slowstop" and timeout:
                raise subprocess.TimeoutExpired("serve", timeout)
            return 1

    class Follow:
        returncode = 1 if mode == "crash" else 0

        def communicate(self, request, timeout):
            assert json.loads(request)["turns"] == ["hi"]
            if mode == "timeout":
                raise subprocess.TimeoutExpired("follow", timeout)
            return '{"turns": []}\n', ""

        def kill(self):
            actions.append(("kill",))

    monkeypatch.setattr(live.subprocess, "run", token)
    monkeypatch.setattr(live.subprocess, "Popen", lambda command, **kw: Follow() if command[0] == "node" else Serve())
    monkeypatch.setattr(live.threading, "Thread", lambda **kw: SimpleNamespace(start=lambda: None))
    monkeypatch.setattr(live.os, "killpg", lambda *a: actions.append(("killpg", *a)))
    result = live.run_plugin(tmp_path, env, {"turns": ["hi"], "answer": None}, 5)
    assert (tmp_path / "home/.nuru/service/clients/obsidian.token").read_text() == "scratch-token"
    assert ("signal", signal.SIGTERM) in actions
    if mode in {"ok", "slowstop"}:
        assert result == {"turns": []}
    elif mode == "timeout":
        assert result["timed_out"] and ("kill",) in actions
    else:
        assert result["crashed"]
    if mode == "slowstop":
        assert ("killpg", 123, signal.SIGKILL) in actions and ("wait", None) in actions


def test_manifest_hashes_only_observed_diff_and_filters_model_digests(monkeypatch, tmp_path):
    import requests
    monkeypatch.setenv("OLLAMA_HOST", "127.0.0.1:11434")
    monkeypatch.setattr(requests, "get", lambda *a, **kw: SimpleNamespace(json=lambda: {"models": [
        {"name": "nuru:latest", "digest": "n"}, {"name": live.EMBED_MODEL, "digest": "e"},
        {"name": "other", "digest": "x"},
    ]}))
    assert live.ollama_digests() == {"nuru:latest": "n", live.EMBED_MODEL: "e"}
    monkeypatch.setattr(live, "ROOT", tmp_path)
    (tmp_path / "extra.txt").write_bytes(b"extra")
    monkeypatch.setattr(live.subprocess, "run", lambda command, **kw: SimpleNamespace(
        stdout=b"extra.txt\0" if "ls-files" in command else b"patch"))
    digest = live.diff_sha256(tmp_path)
    assert (tmp_path / "uncommitted.diff").read_bytes() == b"patch\n=== new file extra.txt\nextra"
    assert len(digest) == 64


def test_manifest_identifies_code_model_settings_and_fixture(monkeypatch, tmp_path):
    from core import session
    model_file = tmp_path / "model"
    model_file.write_bytes(b"SYSTEM test")
    monkeypatch.setattr(session, "_modelfile_for", lambda model: model_file)
    monkeypatch.setattr(live, "diff_sha256", lambda batch: "diff-hash")
    monkeypatch.setattr(live, "ollama_digests", lambda: {"qwen": "digest"})
    monkeypatch.setattr(live.subprocess, "run", lambda *a, **kw: SimpleNamespace(stdout="observed"))
    manifest = live.manifest(SimpleNamespace(timeout=5), tmp_path, {"case": 1}, {"note": "bytes"})
    assert manifest["commit"] == "observed" and manifest["dirty"]
    assert manifest["diff_sha256"] == "diff-hash"
    assert len(manifest["modelfile_sha256"]) == len(manifest["cases_sha256"]) == len(manifest["vault_sha256"]) == 64
    assert manifest["ollama_digests_before"] == {"qwen": "digest"}


def test_batch_alternates_routes_and_isolates_each_run(monkeypatch, tmp_path):
    seen = []
    batch = tmp_path / "batch"

    def index(command, *, env, **kwargs):
        Path(env["OBSIDIAN_SEMANTIC_DB"]).touch()

    def route(name):
        def run(path, env, case, timeout):
            seen.append((name, env["NURU_DB_PATH"], env["NURU_SERVICE_DIR"]))
            assert timeout == 3 and Path(env["OBSIDIAN_SEMANTIC_DB"]).exists()
            return {"turns": [{"reply": "answer", "seconds": 1}]}
        return run

    monkeypatch.setattr(live.subprocess, "run", index)
    monkeypatch.setattr(live, "manifest", lambda *a: {"isolated": True})
    monkeypatch.setattr(live, "ollama_digests", lambda: {})
    monkeypatch.setattr(live, "run_direct", route("direct"))
    monkeypatch.setattr(live, "run_plugin", route("plugin"))
    monkeypatch.setattr(live, "score", lambda *a: {"pass": True, "unauthorized_write": False, "why": []})
    live.main(["--cases", "read", "--repeats", "2", "--timeout", "3", "--out", str(batch)])
    assert [s[0] for s in seen] == ["direct", "plugin", "plugin", "direct"]
    assert len({s[1] for s in seen}) == len({s[2] for s in seen}) == 4
    records = [json.loads(row) for row in (batch / "runs.jsonl").read_text().splitlines()]
    summary = json.loads((batch / "summary.json").read_text())
    assert len(records) == 4 and summary["direct"]["passed"] == summary["plugin"]["passed"] == 2
    assert summary["acceptance"] == "no unauthorized writes"
    delegated = []
    monkeypatch.setattr(live, "child", lambda *a: delegated.extend(a))
    live.main(["--child", "case.json", "out.json"])
    assert delegated == [Path("case.json"), Path("out.json")]
