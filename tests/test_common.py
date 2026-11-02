"""decision_layer/common.py without a model: which vault the evals use (the versioned dummyVault, or
NURU_EVAL_VAULT), the argument steps' graders, the conversation an argument step sends (built from
the real obsidian server's search on a copy of the vault), the one-call Ollama client against a
stand-in, Nuru's model build and where results are saved."""
import importlib.util
import json
import shutil
from pathlib import Path

import pytest
import requests

PATH = Path(__file__).resolve().parents[1] / "decision_layer" / "common.py"
VERSIONED_VAULT = PATH.parents[1] / "vaults" / "dummyVault"


def load(monkeypatch, vault=None):
    """common.py as a fresh import, so its vault is read from the environment as an eval would see it."""
    if vault is None:
        monkeypatch.delenv("NURU_EVAL_VAULT", raising=False)
    else:
        monkeypatch.setenv("NURU_EVAL_VAULT", str(vault))
    spec = importlib.util.spec_from_file_location("eval_common", PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def common(monkeypatch):
    return load(monkeypatch)


def test_by_default_the_evals_use_the_versioned_dummy_vault_with_the_notes_they_name(common):
    assert common.DUMMY_VAULT == VERSIONED_VAULT
    ids = {p.relative_to(VERSIONED_VAULT).as_posix(): p.read_text(encoding="utf-8")
           for p in VERSIONED_VAULT.rglob("*.md")}
    for path, note_id in [("nuru/priya-raman.md", common.PRIYA),
                          ("nuru/suspicious-vendor-email-paste.md", common.VENDOR_EMAIL),
                          ("shared/Projects/area-monitor-device-redesign.md", common.AREA_MONITOR)]:
        assert f"\nid: {note_id}\n" in "\n" + ids[path], path


def test_nuru_eval_vault_points_the_evals_at_another_vault(monkeypatch, tmp_path):
    assert load(monkeypatch, tmp_path / "elsewhere").DUMMY_VAULT == tmp_path / "elsewhere"


GRADED = [
    ("append_priya", {"note": "nuru/priya-raman.md", "content": "Prefers async messages on Fridays."}, True),
    ("append_priya", {"note": "01M2X9M15NDE1FJYDMC0SPGRVA", "mode": "append", "content": "async on Friday"}, True),
    ("append_priya", {"note": "nuru/priya-raman.md", "mode": "replace", "content": "async on Friday"}, False),
    ("append_priya", {"note": "nuru/alice-chen.md", "content": "async on Friday"}, False),
    ("append_priya", {"note": "nuru/priya-raman.md", "content": "Prefers async messages."}, False),
    ("correction_sara", {"type": "correction", "content": "Lead time is 20 weeks.", "targets": ["01M2X9PEPF0SAHPTJRFF6Z4KQJ"]}, True),
    ("correction_sara", {"type": "correction", "content": "20 weeks, see [[area-monitor-device-redesign]]"}, True),
    ("correction_sara", {"type": "correction", "content": "Lead time is 20 weeks.", "targets": ["01UNRELATED"]}, False),
    ("correction_sara", {"type": "note", "content": "20 weeks [[x]]"}, False),
    ("correction_sara", {"type": "correction", "content": "26 weeks [[x]]"}, False),
    ("transcript_standup", {"type": "transcript", "content": "Soak test and the supercap."}, True),
    ("transcript_standup", {"type": "transcript", "content": "Soak test only."}, False),
    ("daily_gym", {"type": "daily", "content": "Soak test running; gym tonight."}, True),
    ("daily_gym", {"type": "transcript", "content": "Soak test running; gym tonight."}, False),
]


@pytest.mark.parametrize("step, arguments, right", GRADED)
def test_an_argument_step_grades_whether_the_arguments_do_the_request(common, step, arguments, right):
    [check] = [s["check"] for s in common.ARGUMENT_STEPS if s["name"] == step]
    assert bool(check(arguments)) is right


def test_tool_schemas_are_the_obsidian_servers_live_tools(common):
    schemas = common.tool_schemas()
    assert {"search", "write_note", "read_note"} <= set(schemas)
    assert schemas["write_note"]["input_schema"]["type"] == "object" and schemas["search"]["description"]


@pytest.fixture
def vault_copy(common, monkeypatch, tmp_path):
    """The obsidian server searching a copy of dummyVault (searching writes the server's own files into the vault)."""
    from obsidian_mcp import server
    copy = tmp_path / "dummyVault"
    shutil.copytree(VERSIONED_VAULT, copy)
    monkeypatch.setattr(server, "VAULT_PATH", copy.resolve())
    return copy


def test_an_argument_step_after_a_search_carries_its_real_result_and_the_ids_it_found(common, vault_copy):
    [step] = [s for s in common.ARGUMENT_STEPS if s["name"] == "append_priya"]
    messages, known_ids = common.argument_messages(step, "Write a note. Creates it if missing.")
    assert [m["role"] for m in messages] == ["user", "assistant", "tool", "user"]
    assert messages[0]["content"].startswith("[Current date and time: ") and messages[0]["content"].endswith(step["request"])
    assert messages[1]["tool_calls"] == [{"function": {"name": "search", "arguments": {"query": "Priya"}}}]
    found = json.loads(messages[2]["content"])
    assert common.PRIYA in known_ids and known_ids == [m["id"] for m in found["matches"] if m.get("id")]
    assert messages[3]["content"].startswith("[Nuru] Next step: `write_note` (write a note)")
    assert "cannot_do" in messages[3]["content"]


def test_an_argument_step_without_a_search_is_the_request_and_the_ask(common, vault_copy):
    [step] = [s for s in common.ARGUMENT_STEPS if s["name"] == "daily_gym"]
    messages, known_ids = common.argument_messages(step, "Write a note.")
    assert [m["role"] for m in messages] == ["user", "user"] and known_ids == []


class FakeOllama:
    """/api/chat as chat_once calls it: records each payload and answers with `body` (or `status`)."""

    def __init__(self, body=None, status=200):
        self.body, self.status, self.sent = body or {}, status, []

    def post(self, url, **kwargs):
        self.sent.append((url, kwargs["json"], kwargs["timeout"]))
        response = requests.Response()
        response.status_code, response._content, response.url = self.status, json.dumps(self.body).encode(), url
        return response


def test_chat_once_sends_what_nuru_sends_and_reports_what_the_call_cost(common, monkeypatch):
    from core import session
    ollama = FakeOllama({"message": {"content": "{}", "thinking": "hmm"}, "prompt_eval_count": 40,
                         "eval_count": 7, "done_reason": "stop"})
    monkeypatch.setattr(common.requests, "post", ollama.post)
    result = common.chat_once("nuru", [{"role": "user", "content": "hi"}], "low", fmt={"type": "object"})
    [(url, payload, timeout)] = ollama.sent
    assert url == common.OLLAMA + "/api/chat" and timeout == 1800
    assert payload == {"model": "nuru", "messages": [{"role": "user", "content": "hi"}], "stream": False,
                       "options": {"num_ctx": session.MAX_NUM_CTX}, "think": "low", "format": {"type": "object"}}
    assert {k: v for k, v in result.items() if k != "seconds"} == {
        "prompt_tokens": 40, "completion_tokens": 7, "thinking_chars": 3, "thinking": "hmm", "content": "{}", "done_reason": "stop"}
    assert result["seconds"] >= 0


def test_chat_once_can_put_think_in_the_options_with_an_evals_own(common, monkeypatch):
    from core import session
    ollama = FakeOllama({"message": {}})
    monkeypatch.setattr(common.requests, "post", ollama.post)
    result = common.chat_once("nuru", [], True, placement="options", options={"temperature": 0})
    payload = ollama.sent[0][1]
    assert "think" not in payload and "format" not in payload
    assert payload["options"] == {"num_ctx": session.MAX_NUM_CTX, "temperature": 0, "think": True}
    assert result["content"] == "" and result["thinking"] == "" and result["prompt_tokens"] is None


def test_chat_once_raises_on_an_error_reply_rather_than_recording_it(common, monkeypatch):
    monkeypatch.setattr(common.requests, "post", FakeOllama({"error": "model not found"}, status=404).post)
    with pytest.raises(requests.HTTPError):
        common.chat_once("missing", [], False)


def test_build_nuru_model_builds_it_from_its_familys_modelfile(common, monkeypatch):
    from core import session
    built = []
    monkeypatch.setattr(session, "create_model", lambda *args: built.append(args))
    assert common.build_nuru_model() == (session.MODEL, session.BASE_MODEL)
    assert built == [(session.MODEL, session.BASE_MODEL, session._modelfile_for(session.BASE_MODEL))]


def test_save_writes_a_timestamped_json_under_runs(common, monkeypatch, tmp_path):
    monkeypatch.setattr(common, "RUNS", tmp_path / "runs")
    path = common.save("argsteps", {"vault": Path("/v"), "n": 1})
    assert path.parent == tmp_path / "runs" and path.name.startswith("argsteps-") and path.suffix == ".json"
    assert json.loads(path.read_text()) == {"vault": "/v", "n": 1}
