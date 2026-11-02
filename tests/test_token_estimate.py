"""token_estimate/measure.py against a stand-in Ollama: what it sends, how it counts a text (its count
minus the template's), and the record it writes - every text's counts, the estimate, versions, request."""
import importlib.util
import json
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[1] / "token_estimate" / "measure.py"
spec = importlib.util.spec_from_file_location("token_measure", PATH)
measure = importlib.util.module_from_spec(spec)
spec.loader.exec_module(measure)


class FakeOllama:
    """Ollama's HTTP API as measure.py calls it: a prompt costs 10 template tokens plus one per character."""

    def __init__(self):
        self.chats, self.unloaded = [], []

    def urlopen(self, request, timeout=None):
        url = request if isinstance(request, str) else request.full_url
        if url.endswith("/api/version"):
            return _Response({"version": "0.40.11"})
        if url.endswith("/api/tags"):
            return _Response({"models": [{"name": "m1", "digest": "d1"}, {"name": "m2", "digest": "d2"}]})
        assert request.get_header("Content-type") == "application/json"
        body = json.loads(request.data)
        if url.endswith("/api/generate"):
            self.unloaded.append(body)
            return _Response({})
        self.chats.append(body)
        return _Response({"prompt_eval_count": 10 + len(body["messages"][0]["content"])})


class _Response:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self, *args):
        return self.payload


@pytest.fixture
def ollama(monkeypatch):
    fake = FakeOllama()
    monkeypatch.setattr(measure.urllib.request, "urlopen", fake.urlopen)
    return fake


def test_the_corpus_is_the_vault_the_prompt_json_results_and_the_adversarial_texts():
    corpus = measure.texts()
    assert "system.md" in corpus and "soak table" in corpus
    assert sum(1 for name in corpus if name.endswith(".md") and "/" in name) >= 40, "the sample vault's notes"
    assert json.loads(corpus["json: soak table"])["content"] == corpus["soak table"]
    assert {"adv: underscores", "adv: base64", "adv: emoji", "adv: chinese", "adv: python code"} <= set(corpus)
    assert measure.adversarial()["adv: base64"] == measure.adversarial()["adv: base64"], "seeded: the same every run"


def test_a_count_is_one_message_that_ollama_must_not_truncate(ollama):
    assert measure.count("m1", "abc") == 13
    [sent] = ollama.chats
    assert sent["model"] == "m1" and sent["messages"] == [{"role": "user", "content": "abc"}]
    assert sent["truncate"] is False and sent["think"] is False and sent["stream"] is False
    assert sent["options"] == {"num_ctx": 32768, "num_predict": 1}


def test_the_record_has_every_texts_counts_less_the_template_with_versions(ollama, monkeypatch, tmp_path):
    monkeypatch.setattr(measure, "texts", lambda: {"a": "hello", "b": "_" * 40})
    out = tmp_path / "counts.json"
    monkeypatch.setattr("sys.argv", ["measure", "--out", str(out), "m1", "m2"])
    measure.main()
    record = json.loads(out.read_text())
    assert record["ollama"] == "0.40.11" and record["models"] == {"m1": "d1", "m2": "d2"}
    assert record["request"]["truncate"] is False and "baseline" in record["request"]
    rows = {row["text"]: row for row in record["rows"]}
    # Each text is sent with a "\n<!-- i -->" tail so no two prompts are the same: 10 template tokens
    # plus the characters, minus the baseline "x" (11).
    assert rows["a"]["counts"] == {"m1": len("hello\n<!-- 0 -->") - 1, "m2": len("hello\n<!-- 0 -->") - 1}
    assert rows["a"]["estimate"] == measure.estimate_tokens("hello")
    assert rows["b"]["ratio"] == round(measure.estimate_tokens("_" * 40) / rows["b"]["counts"]["m1"], 3)
    assert record["summary"]["texts"] == 2 and record["summary"]["under"] == [r for r in rows if rows[r]["ratio"] < 1]
    assert [u["model"] for u in ollama.unloaded] == ["m1", "m2"] and all(u["keep_alive"] == 0 for u in ollama.unloaded)


def test_the_record_says_what_was_measured_so_a_rerun_on_other_code_cant_pass_for_it(ollama, monkeypatch, tmp_path):
    import hashlib
    import subprocess
    monkeypatch.setattr(measure, "texts", lambda: {"a": "hello"})
    out = tmp_path / "counts.json"
    monkeypatch.setattr("sys.argv", ["measure", "--out", str(out), "m1"])
    measure.main()
    record = json.loads(out.read_text())
    for repo, key in ((measure.NURU, "nuru"), (measure.EVALS, "bench")):
        git = lambda *args: subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout.strip()
        assert record["measured"][key] == {"commit": git("rev-parse", "HEAD"), "uncommitted_changes": bool(git("status", "--porcelain"))}
    estimator = measure.NURU / "nuru" / "src" / "core" / "context_budget.py"
    assert record["measured"]["estimator_sha256"] == hashlib.sha256(estimator.read_bytes()).hexdigest()
    assert record["rows"][0]["sha256"] == hashlib.sha256(b"hello").hexdigest()
    assert "numbered tail" in record["caveat"]


def test_uncommitted_changes_are_recorded_as_such(tmp_path):
    import subprocess
    repo = tmp_path / "repo"
    repo.mkdir()
    git = lambda *args: subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout.strip()
    git("init", "-q")
    (repo / "f").write_text("1")
    git("add", "f")
    git("-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-qm", "f")
    assert measure.revision(repo) == {"commit": git("rev-parse", "HEAD"), "uncommitted_changes": False}
    (repo / "f").write_text("2")
    assert measure.revision(repo)["uncommitted_changes"] is True


def test_run_as_a_script_it_measures_the_whole_corpus(ollama, monkeypatch, tmp_path):
    import runpy
    out = tmp_path / "counts.json"
    monkeypatch.setattr("sys.argv", ["measure.py", "--out", str(out), "m1"])
    runpy.run_path(str(PATH), run_name="__main__")
    record = json.loads(out.read_text())
    assert record["summary"]["texts"] == len(measure.texts()) == len(ollama.chats) - 1  # and the baseline
